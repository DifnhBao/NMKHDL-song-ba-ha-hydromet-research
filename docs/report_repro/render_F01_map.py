"""Render Hình 1 for the report from the committed catchment polygon.

The image carries no title: Word's caption "Hình 1." is the only title.
HydroBASINS raw vectors are not part of the repository, so the map shows the
merged catchment polygon stored in the processed/handoff data.
"""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch, Polygon, Rectangle
from matplotlib.ticker import FuncFormatter
from mpl_toolkits.axes_grid1.inset_locator import inset_axes


ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).with_name("F01_basin_map_report.png")
CANDIDATES = (
    ROOT / "data" / "processed" / "song_ba_ha_catchment.geojson",
    ROOT / "handoff_writer" / "selected_data" / "song_ba_ha_catchment.geojson",
)
VALIDATION = ROOT / "data" / "processed" / "basin_validation.csv"


def vn(value: float, decimals: int) -> str:
    """Format a number with Vietnamese thousand and decimal separators."""
    text = f"{value:,.{decimals}f}"
    return text.replace(",", "_").replace(".", ",").replace("_", ".")


def read_validation() -> dict[str, str]:
    if not VALIDATION.exists():
        return {}
    with VALIDATION.open(encoding="utf-8-sig", newline="") as handle:
        return {row["parameter"]: row["value"] for row in csv.DictReader(handle)}


def load_rings(path: Path) -> list[list[list[tuple[float, float]]]]:
    """Return one list of rings per polygon."""
    data = json.loads(path.read_text(encoding="utf-8"))
    polygons: list[list[list[tuple[float, float]]]] = []
    for feature in data["features"]:
        geometry = feature["geometry"]
        if geometry["type"] == "Polygon":
            parts = [geometry["coordinates"]]
        elif geometry["type"] == "MultiPolygon":
            parts = geometry["coordinates"]
        else:
            continue
        for rings in parts:
            polygons.append([[(float(x), float(y)) for x, y in ring] for ring in rings])
    return polygons


def main() -> None:
    source = next((path for path in CANDIDATES if path.exists()), None)
    if source is None:
        raise SystemExit("Không tìm thấy song_ba_ha_catchment.geojson")

    meta = read_validation()
    area_km2 = float(meta.get("area_km2", "11160.6"))
    reference_km2 = float(meta.get("reference_area_km2", "11115"))
    deviation_pct = float(meta.get("deviation_pct", "0.41"))
    dam_lat = float(meta.get("outlet_lat", "13.0236263"))
    dam_lon = float(meta.get("outlet_lon", "108.9039118"))
    plant_lat = float(meta.get("powerhouse_lat", "13.0653214"))
    plant_lon = float(meta.get("powerhouse_lon", "108.9129319"))

    polygons = load_rings(source)
    xs = [x for rings in polygons for ring in rings for x, _ in ring]
    ys = [y for rings in polygons for ring in rings for _, y in ring]

    plt.rcParams.update({"font.size": 9, "savefig.dpi": 200})
    fig, ax = plt.subplots(figsize=(7.0, 10.6), dpi=200)

    for rings in polygons:
        outer, *holes = rings
        ax.add_patch(Polygon(outer, closed=True, facecolor="#4ECDC4",
                             edgecolor="#1A5276", linewidth=1.0,
                             alpha=0.55, zorder=2))
        for hole in holes:
            ax.add_patch(Polygon(hole, closed=True, facecolor="white",
                                 edgecolor="#1A5276", linewidth=0.6, zorder=3))

    ax.plot(dam_lon, dam_lat, "^", markersize=13, markerfacecolor="#E74C3C",
            markeredgecolor="black", markeredgewidth=0.8, zorder=7,
            label="Điểm kiểm tra = tuyến đập")
    ax.annotate(
        f"Đập Sông Ba Hạ\n{vn(dam_lat, 4)}°N – {vn(dam_lon, 4)}°E",
        xy=(dam_lon, dam_lat), xytext=(12, 18), textcoords="offset points",
        fontsize=9, fontweight="bold", zorder=8,
        bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#C0392B", alpha=0.9),
        arrowprops=dict(arrowstyle="->", color="#C0392B", lw=1.2),
    )
    ax.plot(plant_lon, plant_lat, "s", color="#8E44AD", markersize=7, zorder=7,
            label="Nhà máy (OSM way/827889670)")

    margin_y = 0.20
    ax.set_xlim(min(xs) - 0.25, max(xs) + 0.55)  # extra room for the dam label
    ax.set_ylim(min(ys) - margin_y, max(ys) + margin_y)
    lat_mid = (min(ys) + max(ys)) / 2
    ax.set_aspect(1.0 / math.cos(math.radians(lat_mid)))
    ax.set_xlabel("Kinh độ (°E)")
    ax.set_ylabel("Vĩ độ (°N)")
    comma = FuncFormatter(lambda value, _: vn(value, 1))
    ax.xaxis.set_major_formatter(comma)
    ax.yaxis.set_major_formatter(comma)
    ax.grid(True, linestyle=":", alpha=0.35, zorder=0)

    axins = inset_axes(ax, width="34%", height="30%", loc="upper right",
                       borderpad=1.0)
    for rings in polygons:
        axins.add_patch(Polygon(rings[0], closed=True, facecolor="#4ECDC4",
                                edgecolor="#1A5276", linewidth=1.0,
                                alpha=0.55, zorder=2))
    axins.plot(dam_lon, dam_lat, "^", markersize=10, markerfacecolor="#E74C3C",
               markeredgecolor="black", markeredgewidth=0.7, zorder=7)
    axins.plot(plant_lon, plant_lat, "s", color="#8E44AD", markersize=5, zorder=7)
    dlat = 0.12
    dlon = dlat / math.cos(math.radians(dam_lat))
    axins.set_xlim(dam_lon - dlon, dam_lon + dlon)
    axins.set_ylim(dam_lat - dlat, dam_lat + dlat)
    axins.set_aspect(1.0 / math.cos(math.radians(dam_lat)))
    axins.tick_params(labelsize=6)
    axins.xaxis.set_major_formatter(FuncFormatter(lambda value, _: vn(value, 2)))
    axins.yaxis.set_major_formatter(FuncFormatter(lambda value, _: vn(value, 2)))
    axins.set_title("Cận cảnh tuyến đập", fontsize=7.5, pad=3)
    for spine in axins.spines.values():
        spine.set_edgecolor("#555555")

    handles = [
        Patch(facecolor="#4ECDC4", edgecolor="#1A5276", alpha=0.55,
              label=f"Lưu vực đến tuyến đập ({vn(area_km2, 1)} km²)"),
        plt.Line2D([], [], marker="^", linestyle="", markersize=9,
                   markerfacecolor="#E74C3C", markeredgecolor="black",
                   label="Điểm kiểm tra = tuyến đập"),
        plt.Line2D([], [], marker="s", linestyle="", markersize=6,
                   color="#8E44AD", label="Nhà máy (OSM way/827889670)"),
    ]
    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.075),
              ncol=2, fontsize=8, framealpha=0.95)

    km_per_deg_lon = 111.32 * math.cos(math.radians(lat_mid))
    bar_deg = 20.0 / km_per_deg_lon
    x0 = min(xs) + 0.03
    y0 = min(ys) + 0.05
    ax.add_patch(Rectangle((x0, y0), bar_deg, 0.012, facecolor="black",
                           edgecolor="black", zorder=9))
    ax.text(x0 + bar_deg / 2, y0 + 0.018, "20 km", ha="center", va="bottom",
            fontsize=8, zorder=9)

    ax.text(
        0.99, 0.01,
        "Nguồn: HydroBASINS v1c level 12 (HydroSHEDS/WWF)\n"
        "Tuyến đập: OpenStreetMap (ODbL) · Hệ tọa độ: WGS84 (EPSG:4326)\n"
        f"Diện tích {vn(area_km2, 1)} km²; tham khảo {vn(reference_km2, 0)} km² "
        f"(lệch {vn(deviation_pct, 2)}%)",
        transform=ax.transAxes, fontsize=6.5, va="bottom", ha="right",
        bbox=dict(boxstyle="round", facecolor="white", alpha=0.85),
    )

    # tight_layout cannot account for the inset axes; set the margins directly.
    fig.subplots_adjust(left=0.13, right=0.97, top=0.99, bottom=0.12)
    fig.savefig(OUT, dpi=200)
    plt.close(fig)
    print(OUT, OUT.stat().st_size)


if __name__ == "__main__":
    main()
