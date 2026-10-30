#!/usr/bin/env python3
"""
07_rainfall_runoff_analysis.py — GATE 5 (phần B): Phân tích RQ3
=================================================================
Đặc tả: V1.0 §V-B, V1.1 §14

Phần B — Liên hệ lượng mưa và dòng chảy:
    B1. Biểu đồ đồng thời mưa tháng + lưu lượng tháng (F07)
    B2. Scatter plot mưa – lưu lượng (F08)
    B3. Pearson và Spearman tại lag 0
    B4. Tương quan lag 1 tháng
    B5. So sánh hệ số, số cặp, ổn định nhận xét (F09)
    B6. Kiểm tra tính mùa (deseasonalise → tương quan)

    T05: Kết quả tương quan mưa – dòng chảy
    T06: Danh sách ngoại lệ và quyết định xử lý quan trọng

Quy tắc:
    - Chỉ dùng tháng đủ điều kiện (không LOW_COVERAGE, có mưa + lưu lượng)
    - Nếu < 24 tháng hợp lệ → không kết luận tổng quát
    - Không kết luận nhân quả từ tương quan
    - Không khảo sát hàng chục lag
    - Ghi đủ: n cặp, biến, đơn vị, lag, hệ số, bản ghi bị loại, giới hạn
"""

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
from scipy import stats

ROOT = Path(__file__).resolve().parents[3]
PROC_DIR = ROOT / "data" / "processed"
FIG_DIR = ROOT / "outputs" / "figures"
TAB_DIR = ROOT / "outputs" / "tables"
FIG_DIR.mkdir(parents=True, exist_ok=True)
TAB_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    "figure.dpi": 200,
    "savefig.dpi": 200,
    "font.size": 10,
    "axes.titlesize": 12,
    "axes.labelsize": 10,
})


def load_monthly():
    """Đọc bảng tháng tích hợp."""
    path = PROC_DIR / "hydromet_monthly.csv"
    if not path.exists():
        sys.exit(f"[LỖI] Chưa có: {path}. Chạy GATE 4 trước.")
    df = pd.read_csv(path)
    return df


def filter_valid_months(monthly):
    """Lọc các tháng đủ điều kiện cho phân tích tương quan.

    Điều kiện: không LOW_COVERAGE, có cả mưa lẫn lưu lượng.
    """
    valid = monthly.copy()

    # Loại LOW_COVERAGE
    valid = valid[~valid["quality_status"].str.contains("LOW_COVERAGE", na=False)]

    # Phải có cả mưa lẫn lưu lượng
    valid = valid.dropna(subset=["rainfall_total_mm", "inflow_mean_m3s"])

    # Loại tháng mưa hoặc lưu lượng NaN
    valid = valid[
        (valid["rainfall_total_mm"].notna()) &
        (valid["inflow_mean_m3s"].notna())
    ]

    return valid


def compute_correlation(x, y, method="pearson"):
    """Tính tương quan Pearson hoặc Spearman, trả về r, p-value."""
    if len(x) < 3:
        return np.nan, np.nan
    if method == "pearson":
        r, p = stats.pearsonr(x, y)
    else:
        r, p = stats.spearmanr(x, y)
    return round(r, 4), round(p, 6)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# B1 + F07: Biểu đồ đồng thời mưa và lưu lượng
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def create_F07(valid):
    """F07 — So sánh mưa tháng và lưu lượng về hồ tháng."""
    fig, ax1 = plt.subplots(figsize=(14, 6))

    x = range(len(valid))
    labels = valid["year_month"].tolist()

    # Mưa (trục trái)
    color_rain = "#2196F3"
    ax1.bar(x, valid["rainfall_total_mm"].values, color=color_rain, alpha=0.6,
            label="Lượng mưa (mm)")
    ax1.set_ylabel("Lượng mưa (mm)", color=color_rain)
    ax1.tick_params(axis="y", labelcolor=color_rain)
    ax1.set_ylim(0, valid["rainfall_total_mm"].max() * 1.25)

    # Lưu lượng (trục phải)
    ax2 = ax1.twinx()
    color_flow = "#E53935"
    ax2.plot(x, valid["inflow_mean_m3s"].values, "o-", color=color_flow,
             linewidth=1.5, markersize=4, label="Lưu lượng TB (m³/s)")
    ax2.set_ylabel("Lưu lượng trung bình (m³/s)", color=color_flow)
    ax2.tick_params(axis="y", labelcolor=color_flow)

    ax1.set_xticks(range(0, len(valid), 3))
    ax1.set_xticklabels([labels[i] for i in range(0, len(labels), 3)],
                        rotation=45, ha="right")
    ax1.set_xlabel("Tháng")

    ax1.set_title(
        "Hình 7 — So sánh lượng mưa lưu vực và lưu lượng về hồ theo tháng 2023–2025\n"
        f"(n = {len(valid)} tháng hợp lệ; mưa: CHIRPS v3; lưu lượng: Sông Ba Hạ)",
        fontweight="bold"
    )

    # Gộp legend
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left")
    ax1.grid(alpha=0.2)

    path = FIG_DIR / "F07_rainfall_inflow_comparison.png"
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"  → {path}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# B2 + F08: Scatter plot
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def create_F08(valid, corr_results):
    """F08 — Scatter plot mưa – lưu lượng."""
    fig, ax = plt.subplots(figsize=(8, 7))

    rain = valid["rainfall_total_mm"].values
    flow = valid["inflow_mean_m3s"].values

    ax.scatter(rain, flow, c="#1565C0", s=40, alpha=0.7, edgecolors="white",
               linewidths=0.5)

    # Đường hồi quy tuyến tính (chỉ minh họa, không kết luận)
    if len(rain) >= 3:
        z = np.polyfit(rain, flow, 1)
        p = np.poly1d(z)
        x_line = np.linspace(rain.min(), rain.max(), 100)
        ax.plot(x_line, p(x_line), "--", color="gray", alpha=0.5,
                label="Tuyến tính (minh họa)")

    # Ghi tương quan lên đồ thị (p rất nhỏ hiển thị dạng ngưỡng)
    def _p_txt(p):
        return "p < 0,001" if p < 0.001 else f"p = {p:.4f}".replace(".", ",")

    def _num(v):
        return f"{v:.3f}".replace(".", ",")

    lag0 = [r for r in corr_results if r["lag"] == 0]
    if lag0:
        info = lag0[0]
        ax.text(0.04, 0.96,
                f"Pearson r = {_num(info['pearson_r'])}, {_p_txt(info['pearson_p'])}\n"
                f"Spearman ρ = {_num(info['spearman_r'])}, {_p_txt(info['spearman_p'])}\n"
                f"n = {info['n_pairs']} tháng",
                transform=ax.transAxes, fontsize=9, va="top",
                bbox=dict(boxstyle="round", facecolor="lightyellow", alpha=0.9))

    ax.set_xlabel("Lượng mưa lưu vực (mm/tháng)")
    ax.set_ylabel("Lưu lượng trung bình về hồ (m³/s)")
    ax.set_title(
        "Hình 8 — Scatter plot mưa tháng – lưu lượng tháng\n"
        "(CHIRPS v3 Final × dữ liệu vận hành Sông Ba Hạ; "
        "tương quan ≠ nhân quả)",
        fontweight="bold"
    )
    ax.legend()
    ax.grid(alpha=0.3)

    path = FIG_DIR / "F08_scatter_rainfall_inflow.png"
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"  → {path}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# B3–B5: Tương quan lag 0, lag 1, so sánh
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def load_suspect_months():
    """Các tháng có ít nhất một ngày inflow bị gắn cờ SUSPECT."""
    path = PROC_DIR / "hydrology_clean.csv"
    if not path.exists():
        return []
    df = pd.read_csv(path, usecols=["date", "inflow_quality"])
    mask = df["inflow_quality"] == "SUSPECT"
    return sorted(df.loc[mask, "date"].str[:7].unique().tolist())


def _row(analysis, subset, lag, x, y, vx, vy, excluded, reason, limit):
    pr, pp = compute_correlation(x, y, "pearson")
    sr, sp = compute_correlation(x, y, "spearman")
    return {
        "analysis": analysis,
        "subset": subset,
        "lag": lag,
        "variable_x": vx,
        "variable_y": vy,
        "n_pairs": len(x),
        "pearson_r": pr, "pearson_p": pp,
        "spearman_r": sr, "spearman_p": sp,
        "excluded_months": "; ".join(sorted(excluded)),
        "exclusion_reason": reason,
        "interpretation_limit": limit,
    }


def build_lag1_pairs(valid):
    """Cặp (mưa tháng trước, lưu lượng tháng hiện tại) cho các tháng liên tiếp."""
    v = valid.sort_values("year_month").reset_index(drop=True)
    pairs = []
    for i in range(1, len(v)):
        curr = pd.Timestamp(v.iloc[i]["year_month"] + "-01")
        prev = pd.Timestamp(v.iloc[i - 1]["year_month"] + "-01")
        if (curr - prev).days <= 35:
            pairs.append({
                "year_month": v.iloc[i]["year_month"],
                "rain_prev": v.iloc[i - 1]["rainfall_total_mm"],
                "flow_curr": v.iloc[i]["inflow_mean_m3s"],
            })
    return pd.DataFrame(pairs)


def compute_all_correlations(valid, monthly, suspect_months=None):
    """Tính tương quan lag 0/1, deseasonalised, độ nhạy và phân nhóm."""
    suspect_months = suspect_months or []
    results = []
    excluded_months = list(set(monthly["year_month"]) - set(valid["year_month"]))
    limit_base = (
        "Tương quan không chứng minh quan hệ nhân quả. Cả mưa và lưu lượng đều "
        "có tính mùa → có thể thổi phồng hệ số. Ba năm dữ liệu không đại diện "
        "cho quy luật lâu dài."
    )

    rain = valid["rainfall_total_mm"].values
    flow = valid["inflow_mean_m3s"].values

    # ── B3: Lag 0 ─────────────────────────────────────────────────────
    results.append(_row(
        "B3 — Tương quan lag 0", "Tất cả tháng hợp lệ", 0, rain, flow,
        "rainfall_total_mm (mm/tháng)", "inflow_mean_m3s (m³/s)",
        excluded_months, "LOW_COVERAGE hoặc thiếu dữ liệu mưa/lưu lượng",
        limit_base))

    # ── B4: Lag 1 ─────────────────────────────────────────────────────
    lag1 = build_lag1_pairs(valid)
    results.append(_row(
        "B4 — Tương quan lag 1 tháng", "Tất cả tháng hợp lệ", 1,
        lag1["rain_prev"].values if len(lag1) else np.array([]),
        lag1["flow_curr"].values if len(lag1) else np.array([]),
        "rainfall_total_mm tháng trước (mm)",
        "inflow_mean_m3s tháng hiện tại (m³/s)",
        excluded_months, "LOW_COVERAGE, thiếu dữ liệu, hoặc tháng không liên tiếp",
        "Lag 1 tháng có thể phản ánh thời gian truyền nước trong lưu vực lớn, "
        "nhưng cũng có thể do trùng lặp tính mùa. Không kết luận đây là thời "
        "gian trễ thủy văn chính xác."))

    # ── B6: Deseasonalised ────────────────────────────────────────────
    vc = valid.copy()
    vc["month_num"] = vc["year_month"].str[5:7].astype(int)
    rain_mean = vc.groupby("month_num")["rainfall_total_mm"].mean()
    flow_mean = vc.groupby("month_num")["inflow_mean_m3s"].mean()
    vc["rain_anomaly"] = vc["rainfall_total_mm"] - vc["month_num"].map(rain_mean)
    vc["flow_anomaly"] = vc["inflow_mean_m3s"] - vc["month_num"].map(flow_mean)
    des = vc.dropna(subset=["rain_anomaly", "flow_anomaly"])

    results.append(_row(
        "B6 — Deseasonalised (kiểm tra nhạy)", "Tất cả tháng hợp lệ", 0,
        des["rain_anomaly"].values, des["flow_anomaly"].values,
        "Sai lệch mưa tháng so với TB tháng lịch (mm)",
        "Sai lệch lưu lượng tháng so với TB tháng lịch (m³/s)",
        [], "",
        "Mỗi tháng lịch chỉ có 3 giá trị theo năm → trung bình mùa không chính "
        "xác. Kết quả deseasonalised chỉ là phép kiểm tra độ nhạy."))

    # ── S1: Loại tháng chứa ngày SUSPECT (V1.1 §6, §14 B5) ────────────
    if suspect_months:
        cleaned = valid[~valid["year_month"].isin(suspect_months)]
        results.append(_row(
            "S1 — Loại tháng có ngày SUSPECT", "Không gồm tháng SUSPECT", 0,
            cleaned["rainfall_total_mm"].values,
            cleaned["inflow_mean_m3s"].values,
            "rainfall_total_mm (mm/tháng)", "inflow_mean_m3s (m³/s)",
            list(set(excluded_months) | set(suspect_months)),
            "Loại toàn bộ tháng chứa ít nhất một ngày inflow SUSPECT",
            "Đây là phép kiểm tra độ nhạy, không phải kết quả chính."))

        lag1c = build_lag1_pairs(cleaned)
        results.append(_row(
            "S1 — Loại tháng có ngày SUSPECT (lag 1)",
            "Không gồm tháng SUSPECT", 1,
            lag1c["rain_prev"].values if len(lag1c) else np.array([]),
            lag1c["flow_curr"].values if len(lag1c) else np.array([]),
            "rainfall_total_mm tháng trước (mm)",
            "inflow_mean_m3s tháng hiện tại (m³/s)",
            sorted(set(excluded_months) | set(suspect_months)),
            "Loại tháng chứa ngày SUSPECT và tháng không liên tiếp",
            "Phép kiểm tra độ nhạy của B4."))

    # ── D1/D2: Theo mùa (V1.0 §V-B, RQ3) ──────────────────────────────
    wet_months = [5, 6, 7, 8, 9, 10, 11]
    mnum = valid["year_month"].str[5:7].astype(int)
    for name, mask in [("Mùa mưa (T5–T11)", mnum.isin(wet_months)),
                       ("Mùa khô (T12–T4)", ~mnum.isin(wet_months))]:
        sub = valid[mask]
        results.append(_row(
            f"D — Tương quan lag 0, {name}", name, 0,
            sub["rainfall_total_mm"].values, sub["inflow_mean_m3s"].values,
            "rainfall_total_mm (mm/tháng)", "inflow_mean_m3s (m³/s)",
            sorted(set(excluded_months) | set(valid.loc[~mask, "year_month"])),
            "Chỉ dùng các tháng thuộc mùa đang xét",
            "Cỡ mẫu nhỏ (khoảng 12 tháng/nhóm); hệ số kém ổn định, "
            "chỉ mô tả khác biệt mùa, không suy rộng."))

    # ── R1–R3: Theo nhóm điều kiện mưa (tercile) ─────────────────────
    if len(valid) >= 9:
        q1, q2 = valid["rainfall_total_mm"].quantile([1 / 3, 2 / 3])
        groups = [
            ("Nhóm mưa thấp (≤ P33)", valid["rainfall_total_mm"] <= q1),
            ("Nhóm mưa trung bình (P33–P67)",
             (valid["rainfall_total_mm"] > q1) & (valid["rainfall_total_mm"] <= q2)),
            ("Nhóm mưa cao (> P67)", valid["rainfall_total_mm"] > q2),
        ]
        for name, mask in groups:
            sub = valid[mask]
            results.append(_row(
                f"R — Tương quan lag 0, {name}", name, 0,
                sub["rainfall_total_mm"].values, sub["inflow_mean_m3s"].values,
                "rainfall_total_mm (mm/tháng)", "inflow_mean_m3s (m³/s)",
                sorted(set(excluded_months) | set(valid.loc[~mask, "year_month"])),
                f"Chia theo tercile mưa tháng (P33={q1:.0f} mm, P67={q2:.0f} mm)",
                "Mỗi nhóm chỉ ~12 tháng; n nhỏ nên hệ số có thể rất bất ổn. "
                "Không dùng để khẳng định ngưỡng mưa – dòng chảy."))

    return results


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# F09: So sánh kết quả tương quan
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def _short_label(r):
    a = r["analysis"]
    if a.startswith("B3"):
        return "Lag 0"
    if a.startswith("B4"):
        return "Lag 1"
    if a.startswith("B6"):
        return "Deseason."
    if a.startswith("S1") and "lag 1" in a:
        return "Lag 1\n(loại SUSPECT)"
    if a.startswith("S1"):
        return "Lag 0\n(loại SUSPECT)"
    if a.startswith("D"):
        return r["subset"].replace("Mùa ", "").replace(" (", "\n(")
    return r["subset"]


def create_F09(corr_results):
    """F09 — So sánh kết quả tương quan lag 0 và lag 1 (kèm độ nhạy)."""
    focus = [r for r in corr_results
             if r["analysis"].startswith(("B3", "B4", "B6", "S1"))]

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    analyses = [_short_label(r) for r in focus]
    pearson_r = [r["pearson_r"] if not np.isnan(r["pearson_r"]) else 0 for r in focus]
    spearman_r = [r["spearman_r"] if not np.isnan(r["spearman_r"]) else 0 for r in focus]
    n_pairs = [r["n_pairs"] for r in focus]

    x = range(len(analyses))
    width = 0.35

    ax = axes[0]
    bars1 = ax.bar([i - width / 2 for i in x], pearson_r, width,
                   label="Pearson r", color="#1565C0", alpha=0.8)
    ax.bar([i + width / 2 for i in x], spearman_r, width,
           label="Spearman ρ", color="#E53935", alpha=0.8)

    ax.set_xticks(list(x))
    ax.set_xticklabels(analyses, rotation=0, ha="center", fontsize=8)
    ax.set_ylabel("Hệ số tương quan")
    ax.set_title("Hệ số tương quan", fontweight="bold")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    ax.set_ylim(-0.2, 1.1)

    for bar, n in zip(bars1, n_pairs):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.02,
                f"n={n}", ha="center", fontsize=7)

    ax2 = axes[1]
    eps = 1e-12
    pearson_p = [-np.log10(max(r["pearson_p"], eps)) if not np.isnan(r["pearson_p"]) else 0
                 for r in focus]
    spearman_p = [-np.log10(max(r["spearman_p"], eps)) if not np.isnan(r["spearman_p"]) else 0
                  for r in focus]

    ax2.bar([i - width / 2 for i in x], pearson_p, width,
            label="Pearson", color="#1565C0", alpha=0.5)
    ax2.bar([i + width / 2 for i in x], spearman_p, width,
            label="Spearman", color="#E53935", alpha=0.5)
    ax2.axhline(y=-np.log10(0.05), color="green", linestyle="--", alpha=0.8,
                label="α = 0.05")

    ax2.set_xticks(list(x))
    ax2.set_xticklabels(analyses, rotation=0, ha="center", fontsize=8)
    ax2.set_ylabel("−log10(p)  (cao hơn = ý nghĩa hơn)")
    ax2.set_title("Ý nghĩa thống kê", fontweight="bold")
    ax2.legend(fontsize=8)
    ax2.grid(axis="y", alpha=0.3)

    fig.suptitle(
        "F09 — So sánh tương quan mưa – lưu lượng: lag 0, lag 1 và độ nhạy\n"
        "(Lưu ý: tương quan ≠ nhân quả; bị ảnh hưởng bởi tính mùa và mẫu nhỏ)",
        fontweight="bold", fontsize=12, y=1.02
    )
    fig.tight_layout()

    path = FIG_DIR / "F09_correlation_comparison.png"
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"  → {path}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# T05: Bảng tương quan
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def create_T05(corr_results):
    """T05 — Kết quả tương quan mưa – dòng chảy."""
    df = pd.DataFrame(corr_results)
    path = TAB_DIR / "T05_correlation_results.csv"
    df.to_csv(path, index=False, encoding="utf-8-sig")
    print(f"  → {path}")
    return df


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# T06: Danh sách ngoại lệ và quyết định xử lý quan trọng
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def create_T06():
    """T06 — Danh sách ngoại lệ và quyết định xử lý."""
    exc_path = PROC_DIR / "hydrology_exceptions.csv"
    if not exc_path.exists():
        print("  ⚠️ Không có hydrology_exceptions.csv")
        return

    exc = pd.read_csv(exc_path)

    # Chọn các ngoại lệ quan trọng
    important = exc[
        (exc["flag"].isin(["INVALID_CONFIRMED", "SUSPECT"])) &
        (exc["variable"].isin([
            "inflow_m3s", "upstream_level_m", "downstream_level_m",
            "upstream_level_m, downstream_level_m", "inflow_m3s, upstream_level_m",
            "max_power_mw"
        ]))
    ].copy()

    # Thêm cột quyết định xử lý
    decisions = []
    for _, row in important.iterrows():
        flag = row["flag"]
        if flag == "INVALID_CONFIRMED":
            decisions.append("Không sử dụng giá trị sai trong phép tính chính; giữ nguyên gốc")
        elif flag == "SUSPECT":
            decisions.append("Giữ nguyên; đánh dấu để kiểm tra độ nhạy")
        else:
            decisions.append("Ghi nhận")
    important["decision"] = decisions

    path = TAB_DIR / "T06_exceptions_decisions.csv"
    important.to_csv(path, index=False, encoding="utf-8-sig")
    print(f"  → {path}")


def create_T07(corr_results):
    """T07 — Bảng độ nhạy: so sánh kết quả chính và khi loại tháng SUSPECT."""
    df = pd.DataFrame(corr_results)
    base = df[df["analysis"].str.startswith(("B3", "B4"))]
    sens = df[df["analysis"].str.startswith("S1")]

    def _match(prefix, lag):
        m = sens[(sens["analysis"].str.startswith(prefix)) & (sens["lag"] == lag)]
        return m.iloc[0] if len(m) else None

    rows = []
    for _, b in base.iterrows():
        lag = int(b["lag"])
        s = _match("S1", lag)
        if s is None:
            continue
        rows.append({
            "metric": f"lag {lag}",
            "base_n_pairs": int(b["n_pairs"]),
            "base_pearson_r": b["pearson_r"],
            "sens_n_pairs": int(s["n_pairs"]),
            "sens_pearson_r": s["pearson_r"],
            "delta_pearson_r": round(s["pearson_r"] - b["pearson_r"], 4),
            "base_spearman_r": b["spearman_r"],
            "sens_spearman_r": s["spearman_r"],
            "delta_spearman_r": round(s["spearman_r"] - b["spearman_r"], 4),
            "base_pearson_p": b["pearson_p"],
            "sens_pearson_p": s["pearson_p"],
        })

    out = pd.DataFrame(rows)
    path = TAB_DIR / "T07_sensitivity.csv"
    out.to_csv(path, index=False, encoding="utf-8-sig")
    print(f"  → {path}")

    for r in rows:
        print(f"    {r['metric']}: Pearson {r['base_pearson_r']} → "
              f"{r['sens_pearson_r']} (Δ={r['delta_pearson_r']}); "
              f"Spearman {r['base_spearman_r']} → {r['sens_spearman_r']}")
    return out


def main():
    print("=" * 60)
    print("GATE 5b — Phân tích mưa–dòng chảy (RQ3)")
    print("=" * 60)

    # Đọc dữ liệu
    print("\n[1/8] Đọc dữ liệu tháng...")
    monthly = load_monthly()
    print(f"  Tổng: {len(monthly)} tháng")

    # Lọc tháng hợp lệ
    print("\n[2/8] Lọc tháng đủ điều kiện...")
    valid = filter_valid_months(monthly)
    n_valid = len(valid)
    n_excluded = len(monthly) - n_valid
    print(f"  Hợp lệ: {n_valid} tháng, Loại: {n_excluded} tháng")

    suspect_months = load_suspect_months()
    print(f"  Tháng chứa ngày inflow SUSPECT: {suspect_months}")

    if n_valid < 24:
        print(f"  ⚠️ Số tháng hợp lệ ({n_valid}) < 24.")
        print("  → Không đưa ra kết luận tổng quát về mối liên hệ.")
        print("  → Báo cáo cho người giám sát để quyết định hướng trình bày.")

    # Tính tương quan
    print("\n[3/8] Tính tương quan (B3–B6, S1, D, R)...")
    corr_results = compute_all_correlations(valid, monthly, suspect_months)
    for r in corr_results:
        print(f"  {r['analysis']} [{r['subset']}]: "
              f"n={r['n_pairs']}, Pearson={r['pearson_r']}, "
              f"Spearman={r['spearman_r']}")

    # Biểu đồ
    print("\n[4/8] F07 — Biểu đồ đồng thời...")
    create_F07(valid)

    print("\n[5/8] F08 — Scatter plot...")
    create_F08(valid, corr_results)

    print("\n[6/8] F09 — So sánh tương quan...")
    create_F09(corr_results)

    # Bảng
    print("\n[7/8] T05, T06, T07...")
    create_T05(corr_results)
    create_T06()
    create_T07(corr_results)

    print("\n[8/8] Kiểm tra điều kiện kết luận...")
    print(f"  n hợp lệ = {n_valid} (ngưỡng 24)")
    if n_valid < 24:
        print("⚠️ LƯU Ý: < 24 tháng hợp lệ — cần trình người giám sát.")
        return 2

    print("\n✅ GATE 5b (phân tích B — RQ3) hoàn thành.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
