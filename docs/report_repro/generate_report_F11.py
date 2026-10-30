"""Render the T09 pair comparison at a readable size for an A4 Word page."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
MONTHS = ROOT / "handoff_writer" / "selected_data" / "hydromet_monthly.csv"
PAIRS = ROOT / "outputs" / "tables" / "T09_selected_pairs.csv"
OUT = Path(__file__).with_name("F11_docx_vertical.png")

data = pd.read_csv(MONTHS)
selected = pd.read_csv(PAIRS)
points = data.set_index("year_month")
wet = data["year_month"].str[-2:].astype(int).between(5, 11)
fig, (top, bottom) = plt.subplots(2, 1, figsize=(6.2, 6.6), dpi=220)

for ax in (top, bottom):
    ax.grid(color="#dddddd", linewidth=0.5, zorder=0)
    ax.scatter(data.loc[wet, "rainfall_total_mm"], data.loc[wet, "inflow_mean_m3s"],
               s=23, color="#bb7130", label="Tháng 5–11", zorder=2)
    ax.scatter(data.loc[~wet, "rainfall_total_mm"], data.loc[~wet, "inflow_mean_m3s"],
               s=23, color="#3c74a8", label="Tháng 12–4", zorder=2)
    ax.set_ylabel("Lưu lượng tháng (m³/s)", fontsize=9)
    ax.tick_params(labelsize=8)

top.set_title("Toàn bộ 36 tháng", loc="left", fontweight="bold", fontsize=10)
top.set_xlim(0, 475)
top.set_ylim(0, 1300)
top.legend(loc="upper left", fontsize=7.5, frameon=True, ncol=2)
top.annotate("11/2025: 1.198 m³/s", (448, 1198), xytext=(230, 1125),
             fontsize=7.5, arrowprops={"arrowstyle": "->", "lw": 0.7})

bottom.set_title("Phóng to vùng mưa 235–322 mm", loc="left", fontweight="bold", fontsize=10)
bottom.set_xlim(235, 322)
bottom.set_ylim(0, 560)
bottom.set_xlabel("Mưa tháng (mm)", fontsize=9)

circled = {"2023-05", "2023-10", "2025-10", "2024-08", "2025-06"}
for month in sorted(circled):
    p = points.loc[month]
    bottom.scatter([p.rainfall_total_mm], [p.inflow_mean_m3s], s=115,
                   facecolors="none", edgecolors="#222222", linewidths=0.9, zorder=4)

def xy(month):
    p = points.loc[month]
    return float(p.rainfall_total_mm), float(p.inflow_mean_m3s)

for a, b, color, label, pos in [
    ("2023-05", "2023-10", "#aa3131", "5,4% mưa; 7,2× Q", (266, 405)),
    ("2023-10", "2025-10", "#287b52", "9,5% mưa; 1,0× Q", (289, 525)),
    ("2024-08", "2025-06", "#6a3d9a", "1,8% mưa; 1,0× Q", (246, 300)),
]:
    xa, ya = xy(a)
    xb, yb = xy(b)
    bottom.plot([xa, xb], [ya, yb], ls="--", lw=1.3, color=color, zorder=3)
    bottom.text(*pos, label, color=color, fontsize=7.7,
                bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.85, "pad": 1.5})

for month, offset in {
    "2023-05": (4, 5), "2023-10": (-35, -14), "2025-10": (-43, -14),
    "2024-08": (-5, 18), "2025-06": (4, -17),
}.items():
    bottom.annotate(f"{int(month[-2:])}/{month[:4]}", xy(month),
                    xytext=offset, textcoords="offset points", fontsize=7.2)

fig.tight_layout(rect=(0, 0.01, 1, 1.0), h_pad=1.5)
fig.savefig(OUT, dpi=220, facecolor="white")
print(OUT)
