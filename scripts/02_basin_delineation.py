#!/usr/bin/env python3
"""
02_basin_delineation.py — GATE 2: Xác định ranh giới lưu vực đến đập
=====================================================================
Đặc tả: V1.0 §IV-B, V1.1 §7–8

Phương pháp:
    - Tải HydroBASINS cấp 12 khu vực Đông Nam Á.
    - Xác định vị trí cửa ra tại thủy điện Sông Ba Hạ.
    - Truy vết thượng nguồn bằng trường NEXT_DOWN.
    - Hợp nhất polygon, tính diện tích (phép chiếu phù hợp).
    - Đối chiếu 11.115 km².

Đầu ra:
    data/processed/song_ba_ha_catchment.geojson
    data/processed/basin_validation.csv
    outputs/quality/basin_method.md
    outputs/maps/F01_basin_map.png
"""

import os
import sys
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
import warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

try:
    import geopandas as gpd
    from shapely.geometry import Point
    from shapely.ops import unary_union
    import pyproj
except ImportError as e:
    sys.exit(f"[LỖI] Thiếu thư viện: {e}. Chạy pip install geopandas shapely pyproj")

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "data" / "processed"
MAP_DIR = ROOT / "outputs" / "maps"
QA_DIR = ROOT / "outputs" / "quality"
RAW_BOUNDARIES = ROOT / "data" / "raw" / "boundaries"

OUT_DIR.mkdir(parents=True, exist_ok=True)
MAP_DIR.mkdir(parents=True, exist_ok=True)
QA_DIR.mkdir(parents=True, exist_ok=True)
RAW_BOUNDARIES.mkdir(parents=True, exist_ok=True)

# ── Thông số ──────────────────────────────────────────────────────────
# Tọa độ thủy điện Sông Ba Hạ (WGS84)
DAM_LAT = 12.935
DAM_LON = 108.940
REFERENCE_AREA_KM2 = 11115  # Diện tích công bố
TOLERANCE_PCT = 5.0          # Sai lệch cho phép (%)

# URL HydroBASINS
HYDROBASINS_URL = (
    "https://data.hydrosheds.org/file/HydroBASINS/standard/"
    "hybas_as_lev12_v1c.zip"
)


def download_hydrobasins():
    """Tải HydroBASINS nếu chưa có."""
    import requests
    import zipfile
    import io

    shp_candidates = list(RAW_BOUNDARIES.glob("hybas_as_lev12*.shp"))
    if shp_candidates:
        print(f"  Đã có: {shp_candidates[0].name}")
        return shp_candidates[0]

    print(f"  Tải HydroBASINS level 12 châu Á...")
    print(f"  URL: {HYDROBASINS_URL}")

    try:
        resp = requests.get(HYDROBASINS_URL, stream=True, timeout=300)
        resp.raise_for_status()
    except requests.RequestException as e:
        sys.exit(
            f"[LỖI] Không tải được HydroBASINS: {e}\n"
            f"Vui lòng tải thủ công từ:\n"
            f"  https://www.hydrosheds.org/products/hydrobasins\n"
            f"Giải nén vào: {RAW_BOUNDARIES}"
        )

    total = int(resp.headers.get("content-length", 0))
    print(f"  Kích thước: {total / 1024 / 1024:.0f} MB")

    data = io.BytesIO()
    downloaded = 0
    for chunk in resp.iter_content(chunk_size=1024 * 1024):
        data.write(chunk)
        downloaded += len(chunk)
        if total > 0:
            pct = downloaded / total * 100
            print(f"\r  Tải: {pct:.0f}%", end="", flush=True)
    print()

    with zipfile.ZipFile(data) as zf:
        zf.extractall(RAW_BOUNDARIES)

    shp_candidates = list(RAW_BOUNDARIES.glob("hybas_as_lev12*.shp"))
    if not shp_candidates:
        sys.exit("[LỖI] Không tìm thấy shapefile sau giải nén")
    return shp_candidates[0]


def find_outlet_basin(gdf, dam_point):
    """Tìm tiểu lưu vực chứa vị trí đập."""
    # Tìm tiểu lưu vực gần nhất chứa điểm đập
    contains = gdf[gdf.contains(dam_point)]
    if len(contains) > 0:
        # Lọc theo dòng sông Ba (MAIN_BAS hoặc tên)
        return contains.iloc[0]["HYBAS_ID"]

    # Nếu không chứa, tìm gần nhất
    gdf["dist"] = gdf.geometry.distance(dam_point)
    nearest = gdf.nsmallest(5, "dist")
    print(f"  Điểm đập không nằm trong polygon nào. 5 gần nhất:")
    for _, row in nearest.iterrows():
        print(f"    HYBAS_ID={row['HYBAS_ID']}, dist={row['dist']:.4f}°, "
              f"NEXT_DOWN={row['NEXT_DOWN']}, SUB_AREA={row['SUB_AREA']} km²")
    return nearest.iloc[0]["HYBAS_ID"]


def trace_upstream(gdf, outlet_id):
    """Truy vết tất cả tiểu lưu vực thượng nguồn bằng NEXT_DOWN."""
    # Xây dựng dict: NEXT_DOWN → list of HYBAS_ID
    next_down_map = {}
    for _, row in gdf.iterrows():
        nd = row["NEXT_DOWN"]
        if nd not in next_down_map:
            next_down_map[nd] = []
        next_down_map[nd].append(row["HYBAS_ID"])

    # BFS từ outlet
    upstream_ids = {outlet_id}
    queue = [outlet_id]
    while queue:
        current = queue.pop(0)
        children = next_down_map.get(current, [])
        for child in children:
            if child not in upstream_ids:
                upstream_ids.add(child)
                queue.append(child)

    return upstream_ids


def compute_area(catchment_gdf):
    """Tính diện tích bằng phép chiếu diện tích bằng nhau (Albers)."""
    centroid = catchment_gdf.dissolve().geometry.centroid.iloc[0]

    # Sử dụng phép chiếu Albers Equal Area phù hợp cho Việt Nam
    proj_string = (
        f"+proj=aea +lat_1={centroid.y - 2} +lat_2={centroid.y + 2} "
        f"+lat_0={centroid.y} +lon_0={centroid.x} +datum=WGS84 +units=m"
    )

    catchment_proj = catchment_gdf.to_crs(proj_string)
    dissolved = catchment_proj.dissolve()
    area_m2 = dissolved.geometry.area.iloc[0]
    area_km2 = area_m2 / 1e6
    return area_km2


def create_basin_map(catchment_gdf, dam_point, area_km2, deviation_pct):
    """Tạo bản đồ F01."""
    fig, ax = plt.subplots(1, 1, figsize=(12, 10), dpi=200)

    dissolved = catchment_gdf.dissolve()
    dissolved.plot(ax=ax, color="#4ECDC4", edgecolor="#2C3E50",
                   linewidth=0.5, alpha=0.6, label="Lưu vực")

    ax.plot(dam_point.x, dam_point.y, "r^", markersize=12, label="TĐ Sông Ba Hạ",
            zorder=5)

    bounds = dissolved.total_bounds
    margin = 0.2
    ax.set_xlim(bounds[0] - margin, bounds[2] + margin)
    ax.set_ylim(bounds[1] - margin, bounds[3] + margin)

    ax.set_title(
        f"F01 — Ranh giới lưu vực sông Ba đến thủy điện Sông Ba Hạ\n"
        f"Diện tích: {area_km2:,.0f} km² | Tham khảo: {REFERENCE_AREA_KM2:,} km² | "
        f"Sai lệch: {deviation_pct:.1f}%",
        fontsize=12, fontweight="bold", pad=15
    )
    ax.set_xlabel("Kinh độ (°E)")
    ax.set_ylabel("Vĩ độ (°N)")
    ax.legend(loc="upper left")
    ax.grid(True, alpha=0.3)

    # Thông tin nguồn
    ax.text(0.01, 0.01,
            "Nguồn: HydroBASINS v1c (HydroSHEDS/WWF)\nHệ tọa độ: WGS84 (EPSG:4326)",
            transform=ax.transAxes, fontsize=8, va="bottom",
            bbox=dict(boxstyle="round", facecolor="white", alpha=0.8))

    path = MAP_DIR / "F01_basin_map.png"
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"  → {path}")
    return path


def write_basin_method(area_km2, deviation_pct, n_subbasins, outlet_id):
    """Viết basin_method.md."""
    lines = [
        "# Phương pháp xác định ranh giới lưu vực",
        "",
        "## 1. Vị trí cửa ra",
        "",
        f"- **Công trình:** Thủy điện Sông Ba Hạ",
        f"- **Tọa độ (WGS84):** {DAM_LAT}°N, {DAM_LON}°E",
        f"- **HYBAS_ID cửa ra:** {outlet_id}",
        "",
        "## 2. Dữ liệu nền",
        "",
        "- **Nguồn:** HydroBASINS v1c (HydroSHEDS, WWF)",
        "- **Cấp:** Level 12 (chi tiết nhất)",
        "- **Khu vực:** Châu Á (hybas_as_lev12_v1c)",
        "- **Hệ tọa độ:** WGS84 (EPSG:4326)",
        "",
        "## 3. Phương pháp",
        "",
        "1. Xác định tiểu lưu vực chứa vị trí đập.",
        "2. Truy vết ngược thượng nguồn bằng trường `NEXT_DOWN` (topology HydroBASINS).",
        "3. Hợp nhất tất cả tiểu lưu vực thượng nguồn thành polygon lưu vực.",
        "4. Tính diện tích bằng phép chiếu Albers Equal Area.",
        "",
        "## 4. Kết quả",
        "",
        f"- **Số tiểu lưu vực:** {n_subbasins}",
        f"- **Diện tích tính toán:** {area_km2:,.1f} km²",
        f"- **Diện tích tham khảo:** {REFERENCE_AREA_KM2:,} km²",
        f"- **Sai lệch:** {deviation_pct:.1f}%",
        "",
        "## 5. Đánh giá",
        "",
    ]
    if deviation_pct <= TOLERANCE_PCT:
        lines.append(
            f"Sai lệch {deviation_pct:.1f}% nằm trong ngưỡng {TOLERANCE_PCT}%. "
            "Tuy nhiên, cần kiểm tra hình học, vị trí cửa ra và tính liên thông "
            "trên bản đồ trước khi kết luận polygon đúng."
        )
    else:
        lines.append(
            f"⚠️ Sai lệch {deviation_pct:.1f}% vượt ngưỡng {TOLERANCE_PCT}%. "
            "Cần báo cáo nguyên nhân và trình người giám sát phê duyệt."
        )
    lines += [
        "",
        "## 6. Giới hạn",
        "",
        "- HydroBASINS dựa trên DEM toàn cầu, ranh giới có thể sai lệch cục bộ.",
        "- Vị trí cửa ra sử dụng tọa độ ước lượng, không phải tọa độ chính thức.",
        "- Ranh giới cần được đối chiếu với tài liệu công trình và nghiệm thu.",
        "",
        "## 7. Định dạng đầu ra",
        "",
        "- `song_ba_ha_catchment.geojson`: Polygon lưu vực (WGS84)",
        "- `basin_validation.csv`: Thông tin diện tích và kiểm tra",
        "- `F01_basin_map.png`: Bản đồ kiểm chứng",
        "",
    ]

    path = QA_DIR / "basin_method.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"  → {path}")


def main():
    print("=" * 60)
    print("GATE 2 — Xác định ranh giới lưu vực")
    print("=" * 60)

    # 1. Tải HydroBASINS
    print("\n[1/6] Kiểm tra/Tải HydroBASINS level 12...")
    shp_path = download_hydrobasins()

    # 2. Đọc và lọc sơ bộ
    print("\n[2/6] Đọc HydroBASINS...")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        gdf = gpd.read_file(shp_path)
    print(f"  Tổng số tiểu lưu vực châu Á: {len(gdf)}")

    # Lọc bounding box khu vực sông Ba
    bbox_filter = (
        (gdf.geometry.centroid.x > 107.5) & (gdf.geometry.centroid.x < 110.5) &
        (gdf.geometry.centroid.y > 12.0) & (gdf.geometry.centroid.y < 15.0)
    )
    gdf_region = gdf[bbox_filter].copy()
    print(f"  Tiểu lưu vực trong vùng lọc: {len(gdf_region)}")

    # 3. Tìm cửa ra
    print("\n[3/6] Tìm tiểu lưu vực cửa ra...")
    dam_point = Point(DAM_LON, DAM_LAT)
    outlet_id = find_outlet_basin(gdf_region, dam_point)
    print(f"  Cửa ra HYBAS_ID: {outlet_id}")

    # 4. Truy vết thượng nguồn (sử dụng toàn bộ dữ liệu châu Á)
    print("\n[4/6] Truy vết thượng nguồn...")
    upstream_ids = trace_upstream(gdf, outlet_id)
    print(f"  Số tiểu lưu vực thượng nguồn: {len(upstream_ids)}")

    catchment = gdf[gdf["HYBAS_ID"].isin(upstream_ids)].copy()

    # 5. Tính diện tích
    print("\n[5/6] Tính diện tích...")
    area_km2 = compute_area(catchment)
    deviation_pct = abs(area_km2 - REFERENCE_AREA_KM2) / REFERENCE_AREA_KM2 * 100
    print(f"  Diện tích: {area_km2:,.1f} km²")
    print(f"  Tham khảo: {REFERENCE_AREA_KM2:,} km²")
    print(f"  Sai lệch: {deviation_pct:.1f}%")

    if deviation_pct > TOLERANCE_PCT:
        print(f"  ⚠️ Sai lệch > {TOLERANCE_PCT}%! Cần trình người giám sát phê duyệt.")
    else:
        print(f"  ✅ Sai lệch trong ngưỡng {TOLERANCE_PCT}%")

    # Xuất GeoJSON
    dissolved = catchment.dissolve()
    geojson_path = OUT_DIR / "song_ba_ha_catchment.geojson"
    dissolved.to_file(geojson_path, driver="GeoJSON")
    print(f"  → {geojson_path}")

    # Xuất basin_validation.csv
    validation = pd.DataFrame([{
        "parameter": "outlet_lat", "value": DAM_LAT,
    }, {
        "parameter": "outlet_lon", "value": DAM_LON,
    }, {
        "parameter": "outlet_hybas_id", "value": outlet_id,
    }, {
        "parameter": "n_subbasins", "value": len(upstream_ids),
    }, {
        "parameter": "area_km2", "value": round(area_km2, 1),
    }, {
        "parameter": "reference_area_km2", "value": REFERENCE_AREA_KM2,
    }, {
        "parameter": "deviation_pct", "value": round(deviation_pct, 1),
    }, {
        "parameter": "crs", "value": "EPSG:4326",
    }, {
        "parameter": "source", "value": "HydroBASINS v1c level 12",
    }])
    val_path = OUT_DIR / "basin_validation.csv"
    validation.to_csv(val_path, index=False, encoding="utf-8-sig")
    print(f"  → {val_path}")

    # 6. Tạo bản đồ và tài liệu
    print("\n[6/6] Tạo bản đồ F01 và tài liệu...")
    create_basin_map(catchment, dam_point, area_km2, deviation_pct)
    write_basin_method(area_km2, deviation_pct, len(upstream_ids), outlet_id)

    print("\n✅ GATE 2 hoàn thành.")
    print("⚠️ Cần trình F01_basin_map.png, basin_method.md và basin_validation.csv")
    print("   cho người thiết kế phê duyệt trước khi tiếp tục GATE 3.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
