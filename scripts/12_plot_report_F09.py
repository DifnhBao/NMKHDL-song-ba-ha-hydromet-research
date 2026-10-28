#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Reproduce final F09 in the written report from reviewed T05, T07 and T08.

Runs after 10_suspect_sensitivity.py at GATE 6. Does NOT recompute hydrology,
alter QA classifications or change correlation estimates. The 07 script still
produces its exploratory correlation/p-value chart during GATE 5b; this script
replaces the public F09 PNG with the report's three-scenario sensitivity chart.

Output: outputs/figures/F09_correlation_comparison.png (200 dpi).
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

ROOT = Path(__file__).resolve().parent.parent
T05 = ROOT / "outputs" / "tables" / "T05_correlation_results.csv"
T07 = ROOT / "outputs" / "tables" / "T07_sensitivity.csv"
T08 = ROOT / "handoff_writer" / "tables" / "T08_alternative_suspect_sensitivity.csv"
OUTPUT = ROOT / "outputs" / "figures" / "F09_correlation_comparison.png"


def pick_unique(df: pd.DataFrame, col: str, val: str) -> pd.Series:
    matches = df.loc[df[col] == val]
    if len(matches) != 1:
        raise ValueError(f"Expected one {col}={val!r}; got {len(matches)}")
    return matches.iloc[0]


def checked_close(a: float, b: float, description: str, tol: float = 0.00015) -> None:
    if not np.isfinite(a) or not np.isfinite(b) or abs(a - b) > tol:
        raise ValueError(f"{description} mismatch: {a} != {b}")


def main() -> None:
    for path in (T05, T07, T08):
        if not path.is_file():
            raise FileNotFoundError(f"Missing QA source: {path}")

    t05 = pd.read_csv(T05)
    t07 = pd.read_csv(T07)
    t08 = pd.read_csv(T08)
    required05 = {"analysis", "n_pairs", "pearson_r"}
    required07 = {"metric", "base_n_pairs", "base_pearson_r",
                  "sens_n_pairs", "sens_pearson_r"}
    required08 = {"scenario", "n_pairs_lag0", "pearson_lag0",
                  "n_pairs_lag1", "pearson_lag1"}
    for name, frame, required in (("T05", t05, required05),
                                  ("T07", t07, required07),
                                  ("T08", t08, required08)):
        missing = required - set(frame.columns)
        if missing:
            raise ValueError(f"{name} missing columns: {sorted(missing)}")

    b3 = t05[t05["analysis"].astype(str).str.startswith("B3")]
    b4 = t05[t05["analysis"].astype(str).str.startswith("B4")]
    if len(b3) != 1 or len(b4) != 1:
        raise ValueError("T05 must contain exactly one B3 and one B4 row")
    b3, b4 = b3.iloc[0], b4.iloc[0]
    s0, s1 = (pick_unique(t07, "metric", "lag 0"),
              pick_unique(t07, "metric", "lag 1"))
    base = pick_unique(t08, "scenario", "VALID_ONLY")
    alternative = pick_unique(t08, "scenario", "INCLUDE_SUSPECT_AS_REPORTED")

    # Detect stale / inconsistent exports rather than plotting quietly.
    for k, t05row, t07row in (
        (0, b3, s0), (1, b4, s1),
    ):
        ncol = f"n_pairs_lag{k}"
        rcol = f"pearson_lag{k}"
        expected_n = int(base[ncol])
        if (int(t05row["n_pairs"]) != expected_n or
                int(t07row["base_n_pairs"]) != expected_n):
            raise ValueError(f"Lag {k}: inconsistent main-case sample sizes")
        checked_close(float(t05row["pearson_r"]),
                      float(base[rcol]), f"Lag {k}: T05/T08")
        checked_close(float(t07row["base_pearson_r"]),
                      float(base[rcol]), f"Lag {k}: T07/T08")

    scenario_specs = [
        ("Chỉ ngày VALID", base,
         (float(base["pearson_lag0"]), float(base["pearson_lag1"])),
         (int(base["n_pairs_lag0"]), int(base["n_pairs_lag1"]))),
        ("Loại tháng chứa\\nngày SUSPECT", s0,
         (float(s0["sens_pearson_r"]), float(s1["sens_pearson_r"])),
         (int(s0["sens_n_pairs"]), int(s1["sens_n_pairs"]))),
        ("Giữ SUSPECT\\nnhư nguồn công bố", alternative,
         (float(alternative["pearson_lag0"]),
          float(alternative["pearson_lag1"])),
         (int(alternative["n_pairs_lag0"]),
          int(alternative["n_pairs_lag1"]))),
    ]
    x = np.arange(len(scenario_specs))
    lag0 = np.array([r[2][0] for r in scenario_specs], dtype=float)
    lag1 = np.array([r[2][1] for r in scenario_specs], dtype=float)
    if (not np.isfinite(lag0).all() or not np.isfinite(lag1).all()
            or np.any(np.abs(lag0) > 1) or np.any(np.abs(lag1) > 1)):
        raise ValueError("Pearson coefficients must be finite and in [-1,1]")

    plt.rcParams.update({"font.size": 10, "savefig.dpi": 200})
    fig, ax = plt.subplots(figsize=(12, 5.6), dpi=200)
    ax.plot(x, lag0, marker="o", linewidth=2.0, markersize=8,
            color="#1875B5", label="Lag 0 — mưa và lưu lượng cùng tháng")
    ax.plot(x, lag1, marker="s", linewidth=2.0, markersize=8,
            color="#D08032", label="Lag 1 — mưa tháng trước")
    for i, (_, _, _, (n0, n1)) in enumerate(scenario_specs):
        ax.annotate(f"{lag0[i]:.4f} (n={n0})", (x[i], lag0[i]),
                    xytext=(0, -18), textcoords="offset points",
                    ha="center", va="top", fontsize=9, color="#15679C")
        ax.annotate(f"{lag1[i]:.4f} (n={n1})", (x[i], lag1[i]),
                    xytext=(0, 11), textcoords="offset points",
                    ha="center", va="bottom", fontsize=9, color="#9E5A21")
    ax.set_xticks(x)
    ax.set_xticklabels([row[0].replace("\\n", "\n") for row in scenario_specs])
    ax.set_ylabel("Hệ số tương quan Pearson (r)")
    ax.set_xlabel("Kịch bản xử lý dữ liệu lưu lượng")
    ax.set_ylim(max(-1, min(*lag0, *lag1) - 0.11),
                min(1, max(*lag0, *lag1) + 0.12))
    ax.set_xlim(-0.3, len(x) - 0.7)
    ax.grid(axis="y", alpha=0.28)
    ax.legend(loc="upper left", fontsize=9)
    ax.set_title("F09 — Độ nhạy của tương quan mưa–lưu lượng theo cách xử lý SUSPECT",
                 fontweight="bold", pad=16)
    fig.text(0.5, 0.012,
             "Nguồn: T05, T07, T08; lag 0/lag 1 chỉ là liên hệ thống kê, "
             "không chứng minh quan hệ nhân quả hoặc thời gian truyền nước.",
             ha="center", fontsize=8, color="#555555")
    fig.tight_layout(rect=(0, 0.05, 1, 0.99))
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"F09 report chart (3 QA scenarios) → {OUTPUT}")
    for label, _, values, ns in scenario_specs:
        print(f"  {label.replace(chr(10), ' ')}: lag0={values[0]:.6f} n={ns[0]}, "
              f"lag1={values[1]:.6f} n={ns[1]}")


if __name__ == "__main__":
    main()
