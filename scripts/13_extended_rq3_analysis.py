#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Reproduce the extended RQ3 analysis added to the final report.

Input: handoff_writer/selected_data/hydromet_monthly.csv.
Outputs:
  outputs/tables/T09_all_month_pairs.csv
  outputs/tables/T09_same_rain_pairs.csv
  outputs/tables/T09_threshold_summary.csv
  outputs/tables/T09_prior_rain_stats.csv
  outputs/figures/F11_same_rain_pairs.png
"""
from __future__ import annotations

import sys
from itertools import combinations
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from scipy import stats

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

ROOT = Path(__file__).resolve().parent.parent
INPUT = ROOT / "handoff_writer" / "selected_data" / "hydromet_monthly.csv"
OUT_TABLES = ROOT / "outputs" / "tables"
OUT_FIGURES = ROOT / "outputs" / "figures"
PAIRS_ALL = OUT_TABLES / "T09_all_month_pairs.csv"
PAIRS_SAME = OUT_TABLES / "T09_same_rain_pairs.csv"
SUMMARY = OUT_TABLES / "T09_threshold_summary.csv"
STATS = OUT_TABLES / "T09_prior_rain_stats.csv"
FIG = OUT_FIGURES / "F11_same_rain_pairs.png"

THRESHOLDS = (5.0, 10.0, 15.0)
WET_MONTHS = set(range(5, 12))
SELECTED = {
    ("2023-05", "2023-10"),
    ("2023-10", "2025-10"),
    ("2023-10", "2025-05"),
    ("2023-11", "2024-06"),
    ("2024-08", "2025-06"),
}


def month_label(value: str) -> str:
    year, month = value.split("-")
    return f"{int(month)}/{year}"


def season_name(value: str) -> str:
    month = int(value.split("-")[1])
    return "Mưa" if month in WET_MONTHS else "Khô"


def partial_p(r: float, n: int, controls: int) -> float:
    df = n - controls - 2
    t_stat = abs(r) * np.sqrt(df / (1.0 - r * r))
    return float(2.0 * stats.t.sf(t_stat, df))


def load_monthly() -> pd.DataFrame:
    if not INPUT.is_file():
        raise FileNotFoundError(f"Missing input: {INPUT}")
    data = pd.read_csv(INPUT)
    required = {
        "year_month",
        "rainfall_total_mm",
        "inflow_mean_m3s",
    }
    missing = required - set(data.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")
    data = data.copy()
    data["year_month"] = data["year_month"].astype(str)
    data["month"] = pd.to_datetime(data["year_month"] + "-01")
    data = data.sort_values("month").reset_index(drop=True)
    data["rain_prev_mm"] = data["rainfall_total_mm"].shift(1)
    if len(data) != 36:
        raise ValueError(f"Expected 36 months, got {len(data)}")
    if data["rainfall_total_mm"].isna().any() or data["inflow_mean_m3s"].isna().any():
        raise ValueError("Monthly rainfall/inflow contains missing values")
    if (data["inflow_mean_m3s"] <= 0).any():
        raise ValueError("Monthly inflow must be positive for ratios")
    return data


def build_pairs(data: pd.DataFrame) -> pd.DataFrame:
    antecedent = dict(zip(data["year_month"], data["rain_prev_mm"]))
    rows = []
    for i, j in combinations(range(len(data)), 2):
        a = data.iloc[i]
        b = data.iloc[j]
        rain_a = float(a["rainfall_total_mm"])
        rain_b = float(b["rainfall_total_mm"])
        flow_a = float(a["inflow_mean_m3s"])
        flow_b = float(b["inflow_mean_m3s"])
        rain_diff = abs(rain_a - rain_b) / ((rain_a + rain_b) / 2.0) * 100.0
        flow_ratio = max(flow_a, flow_b) / min(flow_a, flow_b)
        rows.append({
            "month_a": a["year_month"],
            "month_b": b["year_month"],
            "month_a_label": month_label(a["year_month"]),
            "month_b_label": month_label(b["year_month"]),
            "rain_a_mm": rain_a,
            "rain_b_mm": rain_b,
            "rain_diff_pct": rain_diff,
            "flow_a_m3s": flow_a,
            "flow_b_m3s": flow_b,
            "flow_ratio": flow_ratio,
            "antecedent_a_mm": antecedent[a["year_month"]],
            "antecedent_b_mm": antecedent[b["year_month"]],
            "season_a": season_name(a["year_month"]),
            "season_b": season_name(b["year_month"]),
        })
    pairs = pd.DataFrame(rows)
    if len(pairs) != 630:
        raise ValueError(f"Expected 630 pairs, got {len(pairs)}")
    pairs["selected_for_report"] = [
        (row.month_a, row.month_b) in SELECTED
        for row in pairs.itertuples(index=False)
    ]
    return pairs


def build_summary(pairs: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for threshold in THRESHOLDS:
        subset = pairs[pairs["rain_diff_pct"] <= threshold]
        ge_two = int((subset["flow_ratio"] >= 2.0).sum())
        rows.append({
            "threshold_pct": threshold,
            "n_pairs": int(len(subset)),
            "share_of_all_pairs_pct": len(subset) / len(pairs) * 100.0,
            "n_flow_ratio_ge_2": ge_two,
            "share_flow_ratio_ge_2_pct": ge_two / len(subset) * 100.0,
            "median_flow_ratio": float(subset["flow_ratio"].median()),
            "min_flow_ratio": float(subset["flow_ratio"].min()),
            "max_flow_ratio": float(subset["flow_ratio"].max()),
        })
    return pd.DataFrame(rows)


def build_stats(data: pd.DataFrame) -> pd.DataFrame:
    rain = data["rainfall_total_mm"].to_numpy(dtype=float)
    flow = data["inflow_mean_m3s"].to_numpy(dtype=float)
    months = data["month"].dt.month.to_numpy(dtype=int)
    rows = []

    r, p = stats.pearsonr(rain, flow)
    rows.append({"metric": "Pearson lag 0, toàn bộ 36 tháng", "n": len(rain),
                 "r": float(r), "p_value": float(p),
                 "note": "Mưa tháng hiện tại và lưu lượng cùng tháng"})

    r, p = stats.pearsonr(rain[1:], flow[1:])
    rows.append({"metric": "Pearson lag 0, mẫu 35 tháng", "n": len(rain) - 1,
                 "r": float(r), "p_value": float(p),
                 "note": "Mẫu dùng được cho trễ 1"})

    r, p = stats.pearsonr(rain[:-1], flow[1:])
    rows.append({"metric": "Pearson lag 1, mưa tháng trước", "n": len(rain) - 1,
                 "r": float(r), "p_value": float(p),
                 "note": "Mưa tháng t-1 và lưu lượng tháng t"})

    p2m = rain[1:] + rain[:-1]
    r, p = stats.pearsonr(p2m, flow[1:])
    rows.append({"metric": "Pearson P2m, 35 tháng", "n": len(p2m),
                 "r": float(r), "p_value": float(p),
                 "note": "P2m = P_t + P_(t-1)"})

    prior2 = rain[:-2] + rain[1:-1]
    r, p = stats.pearsonr(prior2, flow[2:])
    rows.append({"metric": "Pearson hai tháng trước, 34 tháng", "n": len(prior2),
                 "r": float(r), "p_value": float(p),
                 "note": "P_(t-1) + P_(t-2), không gồm P_t"})

    prev = rain[:-1]
    current = rain[1:]
    target = flow[1:]
    r_prev_target = stats.pearsonr(prev, target)[0]
    r_prev_current = stats.pearsonr(prev, current)[0]
    r_current_target = stats.pearsonr(current, target)[0]
    r_partial = (r_prev_target - r_prev_current * r_current_target) / np.sqrt(
        (1.0 - r_prev_current ** 2) * (1.0 - r_current_target ** 2)
    )
    rows.append({"metric": "Tương quan riêng mưa trước | mưa hiện tại", "n": len(target),
                 "r": float(r_partial), "p_value": partial_p(r_partial, len(target), 1),
                 "note": "Kiểm soát mưa cùng tháng, chưa kiểm soát mùa"})

    month_angle = 2.0 * np.pi * months[1:] / 12.0
    design = np.column_stack([
        np.ones(len(target)),
        np.sin(month_angle),
        np.cos(month_angle),
    ])

    def residual(values: np.ndarray) -> np.ndarray:
        beta = np.linalg.lstsq(design, values, rcond=None)[0]
        return values - design @ beta

    r_season, p_season = stats.pearsonr(residual(prev), residual(target))
    rows.append({"metric": "Tương quan riêng mưa trước, đã khử mùa sin/cos", "n": len(target),
                 "r": float(r_season), "p_value": float(p_season),
                 "note": "Khử mùa bằng sin/cos; p chưa hiệu chỉnh bậc tự do, chỉ tham khảo"})

    return pd.DataFrame(rows)


def make_figure(data: pd.DataFrame, pairs: pd.DataFrame, same: pd.DataFrame) -> None:
    plt.rcParams.update({
        "font.size": 10,
        "axes.titlesize": 10,
        "axes.labelsize": 9,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "savefig.dpi": 200,
    })
    fig, (left, right) = plt.subplots(
        1, 2, figsize=(12.4, 5.5), dpi=200,
        gridspec_kw={"width_ratios": [1.12, 1.0]},
    )

    rain = data["rainfall_total_mm"].to_numpy(dtype=float)
    flow = data["inflow_mean_m3s"].to_numpy(dtype=float)
    wet = data["month"].dt.month.isin(WET_MONTHS).to_numpy()
    colors = np.where(wet, "#D08032", "#1875B5")

    for ax in (left, right):
        ax.grid(alpha=0.24)
        ax.set_facecolor("#FCFCFC")
        ax.axvspan(260, 315, color="#8C8C8C", alpha=0.10, linewidth=0)

    left.scatter(rain, flow, c=colors, s=42, alpha=0.82, edgecolors="white", linewidths=0.6)

    selected = same[same["selected_for_report"]].copy()
    selected_months = set(selected["month_a"]) | set(selected["month_b"])
    selected_rows = data[data["year_month"].isin(selected_months)]
    left.scatter(
        selected_rows["rainfall_total_mm"], selected_rows["inflow_mean_m3s"],
        s=120, facecolors="none", edgecolors="#222222", linewidths=0.9, zorder=4,
    )

    left.set_xlim(0, 480)
    left.set_ylim(0, 1270)
    left.set_xlabel("Mưa tháng (mm)")
    left.set_ylabel("Lưu lượng trung bình tháng (m³/s)")
    left.set_title("Toàn bộ 36 tháng", loc="left", fontweight="bold")
    left.text(287.5, 1225, "Vùng mưa\n260–315 mm", ha="center", va="top",
              fontsize=8, color="#555555")
    left.annotate(
        "11/2025\n1.198 m³/s",
        xy=(float(data.loc[data["year_month"] == "2025-11", "rainfall_total_mm"].iloc[0]),
            float(data.loc[data["year_month"] == "2025-11", "inflow_mean_m3s"].iloc[0])),
        xytext=(360, 1090), textcoords="data", fontsize=8, color="#444444",
        arrowprops={"arrowstyle": "-", "color": "#777777", "lw": 0.8},
    )
    left.annotate("5/2023", xy=(270.89, 69.75), xytext=(-7, -12),
                  textcoords="offset points", ha="right", va="top", fontsize=8)
    left.annotate("10/2023", xy=(285.92, 502.54), xytext=(-8, 8),
                  textcoords="offset points", ha="right", va="bottom", fontsize=8)
    left.annotate("10/2025", xy=(314.46, 501.48), xytext=(8, 8),
                  textcoords="offset points", ha="left", va="bottom", fontsize=8)

    zoom = data[(data["rainfall_total_mm"] >= 235) & (data["rainfall_total_mm"] <= 322)]
    zoom_wet = zoom["month"].dt.month.isin(WET_MONTHS).to_numpy()
    right.scatter(
        zoom["rainfall_total_mm"], zoom["inflow_mean_m3s"],
        c=np.where(zoom_wet, "#D08032", "#1875B5"), s=58, alpha=0.9,
        edgecolors="white", linewidths=0.6, zorder=3,
    )
    zoom_selected = zoom[zoom["year_month"].isin(selected_months)]
    right.scatter(
        zoom_selected["rainfall_total_mm"], zoom_selected["inflow_mean_m3s"],
        s=140, facecolors="none", edgecolors="#222222", linewidths=0.9, zorder=4,
    )

    by_label = {row.month_a_label: row for row in pairs.itertuples(index=False)}
    by_label.update({row.month_b_label: row for row in pairs.itertuples(index=False)})
    lookup = {}
    for row in data.itertuples(index=False):
        lookup[month_label(row.year_month)] = (row.rainfall_total_mm, row.inflow_mean_m3s)

    pair_specs = [
        ("5/2023", "10/2023", "#B23A48", "5,4% mưa\n7,2× Q", (276.5, 300)),
        ("10/2023", "10/2025", "#2E7D5B", "9,5% mưa\n1,0× Q", (300, 535)),
    ]
    for a, b, color, text, text_xy in pair_specs:
        xa, ya = lookup[a]
        xb, yb = lookup[b]
        right.plot([xa, xb], [ya, yb], color=color, lw=1.4, ls="--", zorder=2)
        right.text(text_xy[0], text_xy[1], text, ha="center", va="center",
                   fontsize=8, color=color,
                   bbox={"boxstyle": "round,pad=0.22", "fc": "white",
                         "ec": "none", "alpha": 0.82})

    labels = [
        ("5/2023", 270.89, 69.75, -6, 8, "right", "bottom"),
        ("10/2023", 285.92, 502.54, -8, 8, "right", "bottom"),
        ("10/2025", 314.46, 501.48, 8, 8, "left", "bottom"),
        ("5/2025", 262.05, 42.10, -6, -10, "right", "top"),
        ("8/2024", 240.29, 112.82, -6, 8, "right", "bottom"),
        ("6/2025", 244.71, 111.94, 6, -8, "left", "top"),
    ]
    for label, x, y, dx, dy, ha, va in labels:
        right.annotate(label, xy=(x, y), xytext=(dx, dy), textcoords="offset points",
                       ha=ha, va=va, fontsize=8)

    right.set_xlim(235, 322)
    right.set_ylim(0, 560)
    right.set_xlabel("Mưa tháng (mm)")
    right.set_ylabel("Lưu lượng trung bình tháng (m³/s)")
    right.set_title("Phóng to vùng mưa 235–322 mm", loc="left", fontweight="bold")

    handles = [
        Line2D([], [], marker="o", color="none", markerfacecolor="#D08032",
               markeredgecolor="white", markersize=7, label="Mùa mưa (T5–T11)"),
        Line2D([], [], marker="o", color="none", markerfacecolor="#1875B5",
               markeredgecolor="white", markersize=7, label="Mùa khô (T12–T4)"),
        Line2D([], [], marker="o", color="none", markerfacecolor="none",
               markeredgecolor="#222222", markersize=9, label="Cặp tiêu biểu"),
    ]
    left.legend(handles=handles, loc="upper right", fontsize=7.5, frameon=False)

    fig.suptitle("F11 — Quan hệ mưa tháng và lưu lượng: cùng mưa, khác dòng chảy",
                 fontsize=12.5, fontweight="bold")
    fig.text(
        0.5, 0.012,
        "Nguồn: hydromet_monthly.csv; 36 tháng. Các cặp tháng không độc lập; "
        "hình chỉ mô tả phân tán, không suy ra quan hệ nhân quả.",
        ha="center", fontsize=8, color="#555555",
    )
    fig.tight_layout(rect=(0, 0.04, 1, 0.94))
    OUT_FIGURES.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG, dpi=200, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    OUT_TABLES.mkdir(parents=True, exist_ok=True)
    data = load_monthly()
    pairs = build_pairs(data)
    summary = build_summary(pairs)
    stats_table = build_stats(data)

    same = pairs[pairs["rain_diff_pct"] <= 10.0].copy()
    selected = same[same["selected_for_report"]].copy()
    selected_order = [
        ("2023-05", "2023-10"),
        ("2023-10", "2025-10"),
        ("2023-10", "2025-05"),
        ("2023-11", "2024-06"),
        ("2024-08", "2025-06"),
    ]
    selected["order"] = selected.apply(
        lambda row: selected_order.index((row["month_a"], row["month_b"])), axis=1
    )
    selected = selected.sort_values("order").drop(columns="order")

    if len(same) != 36:
        raise ValueError(f"Expected 36 same-rain pairs, got {len(same)}")
    if int((same["flow_ratio"] >= 2.0).sum()) != 27:
        raise ValueError("Expected 27 pairs with flow ratio >= 2")
    if len(selected) != 5:
        raise ValueError(f"Expected 5 selected pairs, got {len(selected)}")
    if abs(float(pairs.loc[pairs["selected_for_report"], "rain_diff_pct"].max()) - 9.5) > 0.1:
        raise ValueError("Selected pair rain difference does not match report")

    pairs.to_csv(PAIRS_ALL, index=False, encoding="utf-8-sig", float_format="%.6f")
    same.to_csv(PAIRS_SAME, index=False, encoding="utf-8-sig", float_format="%.6f")
    selected.to_csv(OUT_TABLES / "T09_selected_pairs.csv", index=False,
                    encoding="utf-8-sig", float_format="%.6f")
    summary.to_csv(SUMMARY, index=False, encoding="utf-8-sig", float_format="%.6f")
    stats_table.to_csv(STATS, index=False, encoding="utf-8-sig", float_format="%.6f")
    make_figure(data, pairs, same)

    print(f"All month pairs: {len(pairs)} -> {PAIRS_ALL}")
    print(f"Same-rain pairs (<=10%): {len(same)} -> {PAIRS_SAME}")
    print(f"Threshold summary -> {SUMMARY}")
    print(f"Prior-rain statistics -> {STATS}")
    print(f"Figure F11 -> {FIG}")
    print(summary.to_string(index=False))
    print(stats_table.to_string(index=False))


if __name__ == "__main__":
    main()
