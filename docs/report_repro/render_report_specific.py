"""Render the report-only workflow (Hình 2) and QA sensitivity (Hình 11).

Run from any directory: python docs/report_repro/render_report_specific.py
The other report figures are covered by the adjacent render scripts.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Rectangle
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent


def flow_diagram() -> None:
    fig, ax = plt.subplots(figsize=(11, 5.2), dpi=220)
    fig.patch.set_facecolor("white")
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 5.2)
    ax.axis("off")

    def box(x, y, w, h, label, fill="#ffffff", size=10):
        ax.add_patch(Rectangle((x, y), w, h, facecolor=fill,
                               edgecolor="#222222", linewidth=1.15))
        ax.text(x + w / 2, y + h / 2, label, ha="center", va="center",
                fontsize=size, family="DejaVu Sans", color="#111111")

    def arrow(a, b):
        ax.add_patch(FancyArrowPatch(a, b, arrowstyle="-|>",
                                    mutation_scale=12, linewidth=1.25,
                                    color="#222222", shrinkA=2, shrinkB=2))

    box(0.15, 3.65, 1.8, 0.9, "Số liệu công trình\nSông Ba Hạ")
    box(2.3, 3.65, 1.8, 0.9, "Thu thập chuỗi\nthủy văn", "#f2f2f2")
    box(4.45, 3.4, 2.1, 1.4,
        "QA từng biến\nVALID / SUSPECT /\nINVALID_CONFIRMED", "#f2f2f2", 8.2)

    box(0.15, 1.55, 1.8, 1.5,
        "CHIRPS3\nERA5-Land\nqua Open-Meteo\nHydroBASINS", size=8.2)
    box(2.3, 1.55, 1.8, 1.5,
        "Polygon lưu vực;\ntrung bình mưa\nvà nhiệt độ", "#f2f2f2", 8.8)
    box(6.95, 2.1, 1.7, 1.3,
        "Tích hợp\nngày: 1.096\ntháng: 36", "#f2f2f2", 9.0)
    box(9.0, 2.1, 1.8, 1.3,
        "Trực quan hóa\nthống kê\ntương quan, độ nhạy", "#f2f2f2", 8.1)
    box(9.0, 0.35, 1.8, 0.9,
        "Trả lời RQ1–RQ3\nvà nêu giới hạn", "#f2f2f2", 9.5)

    arrow((1.95, 4.1), (2.3, 4.1))
    arrow((4.1, 4.1), (4.45, 4.1))
    arrow((6.55, 4.1), (7.1, 3.4))
    arrow((1.95, 2.3), (2.3, 2.3))
    arrow((4.1, 2.3), (6.95, 2.65))
    arrow((8.65, 2.75), (9.0, 2.75))
    arrow((9.9, 2.1), (9.9, 1.25))
    ax.text(0.15, 0.55, "Ô trắng: nguồn dữ liệu    Ô xám: bước nhóm thực hiện",
            fontsize=8.5, color="#333333", family="DejaVu Sans")
    fig.savefig(OUT / "H02_workflow.png", dpi=220,
                facecolor="white", bbox_inches="tight", pad_inches=0.08)
    plt.close(fig)


def row(df: pd.DataFrame, column: str, value: str) -> pd.Series:
    selected = df.loc[df[column].astype(str) == value]
    if len(selected) != 1:
        raise ValueError(f"Expected one {column}={value!r}; found {len(selected)}")
    return selected.iloc[0]


def sensitivity_chart() -> None:
    t05 = pd.read_csv(ROOT / "handoff_writer/tables/T05_correlation_results.csv")
    t07 = pd.read_csv(ROOT / "handoff_writer/tables/T07_sensitivity.csv")
    t08 = pd.read_csv(ROOT / "handoff_writer/tables/T08_alternative_suspect_sensitivity.csv")
    baseline = row(t08, "scenario", "VALID_ONLY")
    included = row(t08, "scenario", "INCLUDE_SUSPECT_AS_REPORTED")
    drop0 = row(t07, "metric", "lag 0")
    drop1 = row(t07, "metric", "lag 1")
    scenarios = [
        ("Chỉ ngày VALID", float(baseline.pearson_lag0),
         float(baseline.pearson_lag1), int(baseline.n_pairs_lag0), int(baseline.n_pairs_lag1)),
        ("Loại tháng chứa\nSUSPECT", float(drop0.sens_pearson_r),
         float(drop1.sens_pearson_r), int(drop0.sens_n_pairs), int(drop1.sens_n_pairs)),
        ("Giữ SUSPECT\nnhư nguồn", float(included.pearson_lag0),
         float(included.pearson_lag1), int(included.n_pairs_lag0), int(included.n_pairs_lag1)),
    ]
    # Check source consistency before drawing a chart used as report evidence.
    b3 = t05[t05.analysis.astype(str).str.startswith("B3")]
    b4 = t05[t05.analysis.astype(str).str.startswith("B4")]
    if len(b3) != 1 or len(b4) != 1:
        raise ValueError("Missing reviewed baseline rows B3/B4")
    if not np.isclose(float(b3.iloc[0].pearson_r), scenarios[0][1], atol=0.00015):
        raise ValueError("Lag 0 mismatch")
    if not np.isclose(float(b4.iloc[0].pearson_r), scenarios[0][2], atol=0.00015):
        raise ValueError("Lag 1 mismatch")

    fig, ax = plt.subplots(figsize=(11.25, 5), dpi=240)
    x = np.arange(3)
    lag0 = [s[1] for s in scenarios]
    lag1 = [s[2] for s in scenarios]
    ax.plot(x, lag0, color="#286087", marker="o", linewidth=2,
            markersize=8, label="Trễ 0: mưa cùng tháng")
    ax.plot(x, lag1, color="#a2642c", marker="s", linewidth=2,
            markersize=8, label="Trễ 1: mưa tháng trước")
    for i, (_, a, b, na, nb) in enumerate(scenarios):
        ax.annotate(f"{a:.4f} (n={na})", (i, a), xytext=(0, 10 if i == 2 else -22),
                    textcoords="offset points", ha="center", fontsize=9)
        ax.annotate(f"{b:.4f} (n={nb})", (i, b), xytext=(0, -22 if i == 2 else 10),
                    textcoords="offset points", ha="center", fontsize=9)
    ax.set_xticks(x, [s[0] for s in scenarios])
    ax.set_ylim(0.38, 0.75)
    ax.set_xlim(-0.25, 2.25)
    ax.set_ylabel("Hệ số Pearson (r)")
    ax.grid(axis="y", color="#dddddd", linewidth=0.7)
    ax.legend(loc="upper right", frameon=False)
    fig.tight_layout()
    fig.savefig(OUT / "H11_suspect_sensitivity.png", dpi=240,
                facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    flow_diagram()
    sensitivity_chart()
    print(OUT / "H02_workflow.png")
    print(OUT / "H11_suspect_sensitivity.png")
