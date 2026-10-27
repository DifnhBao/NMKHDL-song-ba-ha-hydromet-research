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
import json
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
# Tuyến đập thủy điện Sông Ba Hạ (WGS84).
# Nguồn: OpenStreetMap way/480785944 "Đập thủy điện Sông Ba Hạ",
#        truy vấn qua OSM API 0.6, lưu tại data/raw/boundaries/osm_reference.geojson.
# Nhà máy (way/827889670) nằm cách tuyến đập ~4,9 km về hạ lưu, cùng tiểu lưu vực.
DAM_LAT = 13.0236263
DAM_LON = 108.9039118
POWERHOUSE_LAT = 13.0653214
POWERHOUSE_LON = 108.9129319
DAM_COORD_SOURCE = (
    "OpenStreetMap way/480785944 (Đập thủy điện Sông Ba Hạ), OSM API 0.6"
)
REFERENCE_AREA_KM2 = 11115  # Diện tích công bố
TOLERANCE_PCT = 5.0          # Sai lệch cho phép (%)
OSM_REFERENCE = ROOT / "data" / "raw" / "boundaries" / "osm_reference.geojson"


# URL HydroBASINS
HYDROBASINS_URL = (
    "https://data.hydrosheds.org/file/HydroBASINS/standard/"
    "hybas_as_lev12_v1c.zip"
)


def read_gate2_status():
    """Đọc trạng thái phê duyệt GATE 2 từ tệp phê duyệt của người giám sát."""
    path = QA_DIR / "gate2_approval.json"
    if not path.exists():
        return "PENDING_SUPERVISOR_APPROVAL"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return "PENDING_SUPERVISOR_APPROVAL"
    if data.get("approved") is True:
        return (f"APPROVED ({data.get('approved_by', 'không rõ')}, "
                f"{data.get('approved_at', 'không rõ')})")
    return "PENDING_SUPERVISOR_APPROVAL"


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
    """Tìm tiểu lưu vực chứa tuyến đập Sông Ba Hạ.

    V1.1 §8 Bước 1–3: cửa ra phải được xác định từ vị trí tuyến đập có thể
    kiểm chứng, không chọn theo diện tích gần đúng. Do đó dùng phép chứa
    không gian (contains), rồi mới kiểm tra chéo diện tích thượng nguồn.
    """
    containing = gdf[gdf.geometry.contains(dam_point)]
    if len(containing) == 1:
        best = containing.iloc[0]
        print(f"  Điểm đập nằm trong HYBAS_ID={best['HYBAS_ID']}, "
              f"UP_AREA={best['UP_AREA']:.1f} km²")
        return best["HYBAS_ID"], "contains"

    if len(containing) > 1:
        # Điểm nằm trên biên chung: chọn tiểu lưu vực có UP_AREA lớn nhất
        # (dòng chính) và ghi nhận trường hợp biên.
        containing = containing.sort_values("UP_AREA", ascending=False)
        best = containing.iloc[0]
        print(f"  ⚠️ Điểm đập nằm trên biên {len(containing)} tiểu lưu vực; "
              f"chọn HYBAS_ID={best['HYBAS_ID']} (UP_AREA lớn nhất)")
        return best["HYBAS_ID"], "boundary"

    # Không có polygon nào chứa điểm → không được tự suy diễn cửa ra
    gdf = gdf.copy()
    gdf["dist"] = gdf.geometry.distance(dam_point)
    nearest = gdf.nsmallest(1, "dist").iloc[0]
    raise RuntimeError(
        f"Không tiểu lưu vực HydroBASINS nào chứa điểm đập "
        f"({DAM_LAT}, {DAM_LON}). Gần nhất: HYBAS_ID={nearest['HYBAS_ID']} "
        f"cách {nearest['dist']:.4f}° (~{nearest['dist']*111:.1f} km). "
        "Phải báo cáo người giám sát, không tự dựng ranh giới."
    )


def trace_upstream(gdf, outlet_id):
    """Truy vết tất cả tiểu lưu vực thượng nguồn bằng NEXT_DOWN."""
    # Xây dựng dict nhanh bằng zip: NEXT_DOWN → list of HYBAS_ID
    next_down_map = {}
    for nd, hid in zip(gdf["NEXT_DOWN"], gdf["HYBAS_ID"]):
        if nd not in next_down_map:
            next_down_map[nd] = []
        next_down_map[nd].append(hid)

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


def create_basin_map(catchment_gdf, dam_point, area_km2, deviation_pct,
                     region_gdf=None):
    """Tạo bản đồ kiểm chứng F01 (V1.1 §8 Bước 6, §15)."""
    import numpy as np
    from matplotlib.patches import Rectangle

    fig, ax = plt.subplots(1, 1, figsize=(11, 10), dpi=200)

    # Nền: toàn bộ tiểu lưu vực lân cận (ngữ cảnh mạng sông)
    if region_gdf is not None:
        region_gdf.boundary.plot(ax=ax, color="#B0BEC5", linewidth=0.35,
                                 zorder=1)
        region_gdf.plot(ax=ax, facecolor="#FAFAFA", edgecolor="none",
                        zorder=0)

    dissolved = catchment_gdf.dissolve()
    dissolved.plot(ax=ax, color="#4ECDC4", edgecolor="#1A5276",
                   linewidth=1.0, alpha=0.55, zorder=2,
                   label=f"Lưu vực đến tuyến đập ({area_km2:,.0f} km²)")

    # Hồ chứa / tuyến đập tham chiếu OSM (nếu có)
    if OSM_REFERENCE.exists():
        try:
            ref = gpd.read_file(OSM_REFERENCE)
            res = ref[ref.geometry.geom_type.isin(["Polygon", "MultiPolygon"])]
            dam_line = ref[ref.geometry.geom_type.isin(["LineString", "MultiLineString"])]
            if len(res) > 0:
                res.plot(ax=ax, color="#5DADE2", edgecolor="#1B4F72",
                         linewidth=0.6, alpha=0.75, zorder=3,
                         label="Hồ Sông Ba Hạ (OSM)")
            if len(dam_line) > 0:
                dam_line.plot(ax=ax, color="#C0392B", linewidth=2.4, zorder=6,
                              label="Tuyến đập (OSM way/480785944)")
        except Exception as exc:  # pragma: no cover - chỉ cảnh báo
            print(f"  ⚠️ Không vẽ được tham chiếu OSM: {exc}")

    ax.plot(dam_point.x, dam_point.y, "r^", markersize=13,
            markerfacecolor="#E74C3C", markeredgecolor="black",
            markeredgewidth=0.8, zorder=7, label="Điểm kiểm tra = tuyến đập")
    ax.annotate("Đập Sông Ba Hạ\n13,0236°N – 108,9039°E",
                xy=(dam_point.x, dam_point.y),
                xytext=(12, 18), textcoords="offset points",
                fontsize=9, fontweight="bold", zorder=8,
                bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#C0392B", alpha=0.9),
                arrowprops=dict(arrowstyle="->", color="#C0392B", lw=1.2))
    ax.plot(POWERHOUSE_LON, POWERHOUSE_LAT, "s", color="#8E44AD",
            markersize=7, zorder=7, label="Nhà máy (OSM way/827889670)")

    bounds = dissolved.total_bounds
    margin_x, margin_y = 0.25, 0.20
    ax.set_xlim(bounds[0] - margin_x, bounds[2] + margin_x)
    ax.set_ylim(bounds[1] - margin_y, bounds[3] + margin_y)

    # Tỷ lệ trục đúng cho lat/lon
    lat_mid = (bounds[1] + bounds[3]) / 2
    ax.set_aspect(1.0 / np.cos(np.radians(lat_mid)))

    # Inset: vùng tuyến đập để thấy rõ điểm nằm trong polygon
    from mpl_toolkits.axes_grid1.inset_locator import inset_axes
    axins = inset_axes(ax, width="34%", height="30%", loc="upper right",
                       borderpad=1.0)
    dissolved.plot(ax=axins, color="#4ECDC4", edgecolor="#1A5276",
                   linewidth=1.0, alpha=0.55, zorder=2)
    if OSM_REFERENCE.exists():
        try:
            ref2 = gpd.read_file(OSM_REFERENCE)
            ref2[ref2.geometry.geom_type.isin(["Polygon", "MultiPolygon"])].plot(
                ax=axins, color="#5DADE2", edgecolor="#1B4F72",
                linewidth=0.6, alpha=0.8, zorder=3)
            ref2[ref2.geometry.geom_type.isin(["LineString", "MultiLineString"])].plot(
                ax=axins, color="#C0392B", linewidth=2.2, zorder=6)
        except Exception:
            pass
    axins.plot(dam_point.x, dam_point.y, "r^", markersize=10,
               markerfacecolor="#E74C3C", markeredgecolor="black",
               markeredgewidth=0.7, zorder=7)
    axins.plot(POWERHOUSE_LON, POWERHOUSE_LAT, "s", color="#8E44AD",
               markersize=5, zorder=7)
    dlat = 0.12
    dlon = dlat / np.cos(np.radians(DAM_LAT))
    axins.set_xlim(DAM_LON - dlon, DAM_LON + dlon)
    axins.set_ylim(DAM_LAT - dlat, DAM_LAT + dlat)
    axins.set_aspect(1.0 / np.cos(np.radians(DAM_LAT)))
    axins.tick_params(labelsize=6)
    axins.set_title("Cận cảnh tuyến đập", fontsize=7.5, pad=3)
    for spine in axins.spines.values():
        spine.set_edgecolor("#555555")

    ax.set_title(
        f"F01 — Ranh giới lưu vực sông Ba đến tuyến đập Sông Ba Hạ\n"
        f"Diện tích: {area_km2:,.0f} km² | Tham khảo: {REFERENCE_AREA_KM2:,} km² | "
        f"Sai lệch: {deviation_pct:.2f}%",
        fontsize=12, fontweight="bold", pad=14
    )
    ax.set_xlabel("Kinh độ (°E)")
    ax.set_ylabel("Vĩ độ (°N)")
    ax.grid(True, linestyle=":", alpha=0.35, zorder=0)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.08), ncol=2,
              fontsize=8, framealpha=0.95)

    # Thước tỷ lệ xấp xỉ 20 km
    km_per_deg_lon = 111.32 * np.cos(np.radians(lat_mid))
    bar_deg = 20.0 / km_per_deg_lon
    x0 = bounds[0] + 0.03
    y0 = bounds[1] + 0.05
    ax.add_patch(Rectangle((x0, y0), bar_deg, 0.012, facecolor="black",
                           edgecolor="black", zorder=9))
    ax.text(x0 + bar_deg / 2, y0 + 0.018, "20 km", ha="center", va="bottom",
            fontsize=8, zorder=9)

    ax.text(0.99, 0.01,
            "Nguồn: HydroBASINS v1c level 12 (HydroSHEDS/WWF)\n"
            "Tuyến đập & hồ: OpenStreetMap (ODbL)\n"
            "Hệ tọa độ: WGS84 (EPSG:4326)",
            transform=ax.transAxes, fontsize=7, va="bottom", ha="right",
            bbox=dict(boxstyle="round", facecolor="white", alpha=0.85))

    path = MAP_DIR / "F01_basin_map.png"
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"  → {path}")
    return path


def write_basin_method(area_km2, deviation_pct, n_subbasins, outlet_id,
                       area_sum_sub, checks):
    """Viết basin_method.md (V1.1 §8: tọa độ, dữ liệu nền, cách xác định,
    diện tích và giới hạn độ chính xác)."""
    lines = [
        "# Phương pháp xác định ranh giới lưu vực",
        "",
        "## 1. Vị trí cửa ra",
        "",
        "- **Công trình:** Thủy điện Sông Ba Hạ (220 MW), sông Ba",
        f"- **Tuyến đập (WGS84):** {DAM_LAT:.7f}°N, {DAM_LON:.7f}°E",
        f"- **Nhà máy (WGS84):** {POWERHOUSE_LAT:.7f}°N, {POWERHOUSE_LON:.7f}°E",
        f"- **Nguồn tọa độ:** {DAM_COORD_SOURCE}",
        "- **Đối tượng OSM:** way/480785944 (tuyến đập), way/827889670 (nhà máy),",
        "  relation/7077710 (hồ chứa); lưu tại `data/raw/boundaries/osm_reference.geojson`",
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
        "1. Xác định tuyến đập từ nguồn địa lý kiểm chứng được (OSM API 0.6).",
        "2. Tìm tiểu lưu vực HydroBASINS **chứa** điểm tuyến đập (`contains`),",
        "   không chọn theo diện tích gần đúng.",
        "3. Truy vết ngược thượng nguồn bằng trường `NEXT_DOWN` (topology HydroBASINS).",
        "4. Hợp nhất tất cả tiểu lưu vực thượng nguồn thành polygon lưu vực.",
        "5. Tính diện tích bằng phép chiếu Albers Equal Area (không tính phẳng trên độ).",
        "6. Kiểm tra chéo: polygon chứa điểm đập, cửa ra nằm trong tập thượng nguồn,",
        "   tổng `SUB_AREA` khớp diện tích hình học.",
        "",
        "## 4. Kết quả",
        "",
        f"- **Số tiểu lưu vực:** {n_subbasins}",
        f"- **Diện tích tính toán (Albers):** {area_km2:,.1f} km²",
        f"- **Tổng SUB_AREA của các tiểu lưu vực:** {area_sum_sub:,.1f} km²",
        f"- **Diện tích tham khảo:** {REFERENCE_AREA_KM2:,} km²",
        f"- **Sai lệch:** {deviation_pct:.2f}%",
        f"- **UP_AREA của tiểu lưu vực cửa ra:** theo HydroBASINS (xem "
        "`basin_validation.csv`)",
        "",
        "## 5. Kiểm tra nghiệm thu (GATE 2)",
        "",
        "| Kiểm tra | Kết quả |",
        "|---|---|",
    ]
    for name, ok, detail in checks:
        lines.append(f"| {name} | {'✅ ĐẠT' if ok else '❌ KHÔNG ĐẠT'} — {detail} |")

    lines += ["", "## 6. Đánh giá sai lệch diện tích", ""]
    if deviation_pct <= TOLERANCE_PCT:
        lines.append(
            f"Sai lệch {deviation_pct:.2f}% nằm trong ngưỡng {TOLERANCE_PCT}%. "
            "Theo V1.1 §8, vẫn phải kiểm tra hình học và mạng sông (đã thực hiện ở mục 5) "
            "trước khi sử dụng."
        )
    else:
        lines.append(
            f"⚠️ Sai lệch {deviation_pct:.2f}% vượt ngưỡng {TOLERANCE_PCT}%. "
            "Phải báo cáo nguyên nhân và trình người giám sát phê duyệt trước khi sử dụng."
        )

    lines += [
        "",
        "## 7. Giới hạn độ chính xác",
        "",
        "- HydroBASINS dựa trên DEM toàn cầu; đường phân thủy có thể lệch cục bộ",
        "  vài km, đặc biệt ở địa hình karst hoặc nơi sông đổi dòng.",
        "- Tuyến đập lấy theo OSM (cộng đồng), chưa đối chiếu với hồ sơ thiết kế",
        "  của chủ đầu tư; sai số vị trí ước tính < 500 m.",
        "- Tiểu lưu vực chứa tuyến đập có diện tích cục bộ ~85 km²; phần diện tích",
        "  nằm giữa tuyến đập và cửa ra của tiểu lưu vực được tính vào lưu vực,",
        "  tạo sai lệch dương nhỏ (đã phản ánh trong sai lệch tổng).",
        "- Ranh giới phải được người giám sát phê duyệt (GATE 2) trước khi dùng",
        "  để tính mưa lưu vực.",
        "",
        "## 8. Diễn giải bản đồ F01",
        "",
        "F01 hiển thị polygon lưu vực đến tuyến đập (màu xanh ngọc), mạng tiểu lưu vực",
        "HydroBASINS level 12 làm nền định vị (đường xám), hồ Sông Ba Hạ và tuyến đập",
        "theo OSM. Điểm kiểm tra (tam giác đỏ) trùng tuyến đập và **nằm trong** polygon;",
        "nhà máy (vuông tím) nằm hạ lưu ~4,9 km nhưng vẫn trong cùng tiểu lưu vực.",
        "Bản đồ dùng để nghiệm thu GATE 2, không dùng để đọc giá trị mưa.",
        "",
        "## 9. Trạng thái phê duyệt",
        "",
        f"- `gate2_status` = {read_gate2_status()}",
        "- Người giám sát phê duyệt bằng `outputs/quality/gate2_approval.json`.",
        "",
        "## 10. Định dạng đầu ra",
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
    print("\n[3/6] Tìm tiểu lưu vực chứa tuyến đập...")
    dam_point = Point(DAM_LON, DAM_LAT)
    outlet_id, match_method = find_outlet_basin(gdf_region, dam_point)
    print(f"  Cửa ra HYBAS_ID: {outlet_id} ({match_method})")

    # 4. Truy vết thượng nguồn (sử dụng toàn bộ dữ liệu châu Á)
    print("\n[4/6] Truy vết thượng nguồn...")
    upstream_ids = trace_upstream(gdf, outlet_id)
    print(f"  Số tiểu lưu vực thượng nguồn: {len(upstream_ids)}")

    catchment = gdf[gdf["HYBAS_ID"].isin(upstream_ids)].copy()

    # 5. Tính diện tích và kiểm tra
    print("\n[5/6] Tính diện tích và kiểm tra...")
    area_km2 = compute_area(catchment)
    area_sum_sub = float(catchment["SUB_AREA"].sum())
    deviation_pct = abs(area_km2 - REFERENCE_AREA_KM2) / REFERENCE_AREA_KM2 * 100
    print(f"  Diện tích (Albers): {area_km2:,.1f} km²")
    print(f"  Tổng SUB_AREA: {area_sum_sub:,.1f} km²")
    print(f"  Tham khảo: {REFERENCE_AREA_KM2:,} km²")
    print(f"  Sai lệch: {deviation_pct:.2f}%")

    dissolved = catchment.dissolve()
    dam_inside = bool(dissolved.geometry.iloc[0].contains(dam_point))
    powerhouse_inside = bool(
        dissolved.geometry.iloc[0].contains(Point(POWERHOUSE_LON, POWERHOUSE_LAT))
    )
    outlet_upstream = bool(outlet_id in upstream_ids)
    geom_valid = bool(dissolved.geometry.is_valid.all())
    area_diff_sub_pct = abs(area_km2 - area_sum_sub) / area_sum_sub * 100

    checks = [
        ("Điểm đập nằm trong polygon", dam_inside,
         f"contains = {dam_inside}"),
        ("Nhà máy nằm trong polygon", powerhouse_inside,
         f"contains = {powerhouse_inside}"),
        ("Cửa ra thuộc tập thượng nguồn", outlet_upstream,
         f"HYBAS_ID {outlet_id} ∈ {len(upstream_ids)} tiểu lưu vực"),
        ("Hình học hợp lệ", geom_valid, f"is_valid = {geom_valid}"),
        ("Sai lệch diện tích ≤ 5%", deviation_pct <= TOLERANCE_PCT,
         f"{deviation_pct:.2f}%"),
        ("Diện tích hình học khớp tổng SUB_AREA (< 2%)",
         area_diff_sub_pct < 2.0, f"{area_diff_sub_pct:.2f}%"),
    ]
    print("\n  Kiểm tra GATE 2:")
    for name, ok, detail in checks:
        print(f"    {'✅' if ok else '❌'} {name}: {detail}")

    if not (dam_inside and outlet_upstream and geom_valid):
        raise RuntimeError(
            "GATE 2 KHÔNG ĐẠT: polygon/cửa ra không thỏa điều kiện hình học. "
            "Dừng pipeline và báo cáo người giám sát (V1.1 §8, §20)."
        )

    # Xuất GeoJSON
    geojson_path = OUT_DIR / "song_ba_ha_catchment.geojson"
    dissolved.to_file(geojson_path, driver="GeoJSON")
    print(f"\n  → {geojson_path}")

    # Xuất basin_validation.csv (gồm cả ứng viên đã cân nhắc)
    gdf_region = gdf_region.copy()
    gdf_region["dist_deg"] = gdf_region.geometry.distance(dam_point)
    candidates = gdf_region.nsmallest(5, "dist_deg")[
        ["HYBAS_ID", "NEXT_DOWN", "SUB_AREA", "UP_AREA", "dist_deg"]
    ]
    rows = [
        ("outlet_lat", DAM_LAT),
        ("outlet_lon", DAM_LON),
        ("powerhouse_lat", POWERHOUSE_LAT),
        ("powerhouse_lon", POWERHOUSE_LON),
        ("coord_source", DAM_COORD_SOURCE),
        ("outlet_hybas_id", outlet_id),
        ("outlet_match_method", match_method),
        ("outlet_up_area_km2", float(catchment.loc[
            catchment["HYBAS_ID"] == outlet_id, "UP_AREA"].iloc[0])),
        ("n_subbasins", len(upstream_ids)),
        ("area_km2", round(area_km2, 1)),
        ("area_sum_subarea_km2", round(area_sum_sub, 1)),
        ("reference_area_km2", REFERENCE_AREA_KM2),
        ("deviation_pct", round(deviation_pct, 2)),
        ("dam_inside_polygon", dam_inside),
        ("powerhouse_inside_polygon", powerhouse_inside),
        ("outlet_in_upstream_set", outlet_upstream),
        ("geometry_valid", geom_valid),
        ("crs", "EPSG:4326"),
        ("area_method", "Albers Equal Area (local, lat_1/lat_2 = centroid ± 2°)"),
        ("source", "HydroBASINS v1c level 12"),
        ("gate2_status", read_gate2_status()),
    ]
    validation = pd.DataFrame(rows, columns=["parameter", "value"])
    val_path = OUT_DIR / "basin_validation.csv"
    validation.to_csv(val_path, index=False, encoding="utf-8-sig")
    print(f"  → {val_path}")

    cand_path = OUT_DIR / "basin_outlet_candidates.csv"
    candidates.to_csv(cand_path, index=False, encoding="utf-8-sig")
    print(f"  → {cand_path}")

    # 6. Tạo bản đồ và tài liệu
    print("\n[6/6] Tạo bản đồ F01 và tài liệu...")
    create_basin_map(catchment, dam_point, area_km2, deviation_pct,
                     region_gdf=gdf_region)
    write_basin_method(area_km2, deviation_pct, len(upstream_ids), outlet_id,
                       area_sum_sub, checks)

    status = read_gate2_status()
    print("\n✅ GATE 2 hoàn thành phần kỹ thuật.")
    if status.startswith("APPROVED"):
        print(f"✅ Đã được phê duyệt: {status}")
    else:
        print("⚠️ BẮT BUỘC: trình F01_basin_map.png, basin_method.md và")
        print("   basin_validation.csv cho người thiết kế phê duyệt trước khi chạy GATE 3.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
