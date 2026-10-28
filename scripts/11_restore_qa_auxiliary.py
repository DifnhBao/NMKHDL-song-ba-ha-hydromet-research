#!/usr/bin/env python3
"""Restore ONLY missing auxiliary QA inputs from verified handoff evidence.

This is NOT a fresh run of HydroBASINS/GATE 2 or CHIRPS extraction.
- rainfall_qa.csv is recalculated from the handed-off CHIRPS daily/monthly CSVs
  with the exact comparison rule in scripts/03_chirps_extraction.py.
- basin_validation.csv is reconstructed from the retained polygon and the
  already conditionally approved GATE 2 record, with independent geometry checks.
- Never alters source observations or the owner's scientific decisions.
"""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

import pandas as pd
from pyproj import Transformer
from shapely.geometry import Point, shape
from shapely.ops import transform as transform_geom

ROOT = Path(__file__).resolve().parent.parent
PROC = ROOT / "data" / "processed"
HANDOFF = ROOT / "handoff_writer" / "selected_data"
QUALITY = ROOT / "outputs" / "quality"


def check(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError("KHÔNG ĐẠT: " + message)


def restore_rainfall_qa() -> None:
    monthly = pd.read_csv(PROC / "rainfall_monthly.csv")
    daily = pd.read_csv(PROC / "rainfall_daily.csv")
    expected = pd.period_range("2023-01", "2025-12", freq="M").astype(str).tolist()
    check(len(monthly) == 36 and monthly["year_month"].tolist() == expected,
          "rainfall_monthly.csv không đủ 36 tháng liên tục 2023-2025")
    dates = pd.to_datetime(daily["date"], errors="raise")
    check(len(daily) == 1096 and not dates.duplicated().any() and
          dates.min() == pd.Timestamp("2023-01-01") and
          dates.max() == pd.Timestamp("2025-12-31"),
          "rainfall_daily.csv phải có 1.096 ngày liên tục")
    check(dates.dt.strftime("%Y-%m").nunique() == 36,
          "Không đủ 36 tháng mưa ngày")
    check(daily["rainfall_mm"].notna().all() and
          monthly["rainfall_mm"].notna().all(),
          "Nguồn CHIRPS có giá trị trống; không tự thay bằng 0")
    check(daily["rainfall_mm"].ge(0).all() and monthly["rainfall_mm"].ge(0).all(),
          "Nguồn CHIRPS có giá trị mưa âm")
    daily["year_month"] = dates.dt.strftime("%Y-%m")
    rows = []
    for _, mrow in monthly.iterrows():
        month = mrow["year_month"]
        mval = float(mrow["rainfall_mm"])
        grp = daily.loc[daily["year_month"] == month, "rainfall_mm"]
        check(len(grp) == pd.Period(month).days_in_month,
              f"Tháng {month} thiếu ngày")
        dsum = float(grp.sum(min_count=1))
        difference = dsum - mval
        percentage = difference / mval * 100 if mval != 0 else float("nan")
        status = "CHECK" if abs(percentage) >= 10 else "OK"
        rows.append({
            "year_month": month,
            "monthly_product_mm": round(mval, 2),
            "daily_sum_mm": round(dsum, 2),
            "n_missing_days": 0,
            "diff_mm": round(difference, 2),
            "diff_pct": round(percentage, 1),
            "status": status,
        })
    qa = pd.DataFrame(rows)
    check(len(qa) == 36 and (qa["status"] == "OK").all(),
          "Có tháng có chênh lệch CHIRPS >=10%, cần xem xét")
    PROC.mkdir(parents=True, exist_ok=True)
    qa.to_csv(PROC / "rainfall_qa.csv", index=False, encoding="utf-8-sig")
    print(f"  rainfall_qa.csv: {len(qa)} tháng, {sum(qa.status == 'OK')} OK")


def capture_number(pattern: str, text: str, description: str) -> float:
    match = re.search(pattern, text, flags=re.MULTILINE)
    check(match is not None, f"Không tìm thấy {description} trong biên bản GATE 2")
    return float(match.group(1).replace(",", ""))


def restore_basin_validation() -> None:
    approval = json.loads((QUALITY / "gate2_approval.json").read_text(encoding="utf-8"))
    approved = approval.get("approved_parameters", {})
    check(approval.get("approval_status") == "CONDITIONAL" and approval.get("approved") is True,
          "Polygon chưa có quyết định chấp thuận có điều kiện")
    method = (QUALITY / "basin_method.md").read_text(encoding="utf-8")
    polygon_source = HANDOFF / "song_ba_ha_catchment.geojson"
    geo = json.loads(polygon_source.read_text(encoding="utf-8"))
    check(geo.get("type") == "FeatureCollection" and len(geo.get("features", [])) == 1,
          "GeoJSON không phải một polygon lưu vực duy nhất")
    feature = geo["features"][0]
    geom = shape(feature["geometry"])
    check(geom.is_valid and geom.geom_type in {"Polygon", "MultiPolygon"},
          "Hình học polygon không hợp lệ")
    check(int(feature["properties"]["HYBAS_ID"]) == int(approved["outlet_hybas_id"]),
          "HYBAS_ID khác quyết định nghiệm thu")
    dlat = capture_number(r"Tuyến đập \(WGS84\):\*\*\s*([0-9.]+)°N", method, "vĩ độ đập")
    dlon = capture_number(r"Tuyến đập \(WGS84\):\*\*\s*[0-9.]+°N,\s*([0-9.]+)°E", method, "kinh độ đập")
    plat = capture_number(r"Nhà máy \(WGS84\):\*\*\s*([0-9.]+)°N", method, "vĩ độ nhà máy")
    plon = capture_number(r"Nhà máy \(WGS84\):\*\*\s*[0-9.]+°N,\s*([0-9.]+)°E", method, "kinh độ nhà máy")
    dam_inside = geom.contains(Point(dlon, dlat))
    plant_inside = geom.contains(Point(plon, plat))
    check(dam_inside and plant_inside, "Đập hoặc nhà máy không nằm trong polygon")
    centroid = geom.centroid
    crs = (
        f"+proj=aea +lat_1={centroid.y - 2} +lat_2={centroid.y + 2} "
        f"+lat_0={centroid.y} +lon_0={centroid.x} +datum=WGS84 +units=m"
    )
    trans = Transformer.from_crs("EPSG:4326", crs, always_xy=True)
    area_km2 = transform_geom(trans.transform, geom).area / 1_000_000
    recorded_area = float(approved["area_km2_albers"])
    check(abs(area_km2 - recorded_area) < 0.5,
          f"Diện tích GeoJSON ({area_km2:.2f}) không khớp hồ sơ ({recorded_area})")
    reference_area = float(approved["reference_area_km2"])
    deviation_pct = abs(area_km2 - reference_area) / reference_area * 100
    check(abs(deviation_pct - float(approved["deviation_pct"])) < 0.02,
          "Sai lệch diện tích không khớp hồ sơ nghiệm thu")
    area_sum = capture_number(
        r"Tổng SUB_AREA của các tiểu lưu vực:\*\*\s*([0-9,.]+)",
        method, "tổng SUB_AREA tiểu lưu vực"
    )
    rows = [
        ("outlet_lat", dlat),
        ("outlet_lon", dlon),
        ("powerhouse_lat", plat),
        ("powerhouse_lon", plon),
        ("coord_source", "OpenStreetMap way/480785944 (biên bản GATE 2)"),
        ("outlet_hybas_id", approved["outlet_hybas_id"]),
        ("outlet_match_method", "contains (đã kiểm tra hình học polygon)"),
        ("outlet_up_area_km2", feature["properties"].get("UP_AREA")),
        ("n_subbasins", approved["n_subbasins"]),
        ("area_km2", round(area_km2, 1)),
        ("area_sum_subarea_km2", area_sum),
        ("reference_area_km2", reference_area),
        ("deviation_pct", round(deviation_pct, 2)),
        ("dam_inside_polygon", dam_inside),
        ("powerhouse_inside_polygon", plant_inside),
        ("outlet_in_upstream_set", "True (theo biên bản GATE 2; không tính lại HydroBASINS)"),
        ("geometry_valid", geom.is_valid),
        ("crs", "EPSG:4326"),
        ("area_method", "Albers Equal Area (local, lat_1/lat_2 = centroid ± 2°)"),
        ("source", "TÁI DỰNG từ polygon + hồ sơ GATE 2 đã phê duyệt có điều kiện; KHÔNG chạy lại HydroBASINS"),
        ("gate2_status", "CONDITIONAL_ACCEPTED — không phải nghiệm thu cuối"),
    ]
    pd.DataFrame(rows, columns=["parameter", "value"]).to_csv(
        PROC / "basin_validation.csv", index=False, encoding="utf-8-sig"
    )
    shutil.copy2(polygon_source, PROC / "song_ba_ha_catchment.geojson")
    print(f"  basin_validation.csv: {len(rows)} thông số; diện tích tính lại {area_km2:.1f} km²")
    print("  Ranh giới polygon: kiểm tra đập, nhà máy, diện tích/hình học đạt.")
    print("  LƯU Ý: không chạy lại truy vết mạng HydroBASINS level 12.")


def main() -> None:
    print("Khôi phục 2 bảng QA phụ từ dữ liệu và chứng cứ đã lưu")
    restore_rainfall_qa()
    restore_basin_validation()
    print("Hoàn thành. Có thể chạy GATE 6 sau khi cập nhật bản review.")


if __name__ == "__main__":
    main()
