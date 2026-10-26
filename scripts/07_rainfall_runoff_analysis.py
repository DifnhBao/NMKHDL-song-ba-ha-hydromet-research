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

ROOT = Path(__file__).resolve().parent.parent
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

    # Mưa (trục trái, đảo ngược — mưa từ trên xuống)
    color_rain = "#2196F3"
    ax1.bar(x, valid["rainfall_total_mm"].values, color=color_rain, alpha=0.6,
            label="Lượng mưa (mm)")
    ax1.set_ylabel("Lượng mưa (mm)", color=color_rain)
    ax1.tick_params(axis="y", labelcolor=color_rain)
    ax1.invert_yaxis()

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
        "F07 — So sánh lượng mưa lưu vực và lưu lượng về hồ theo tháng 2023–2025\n"
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

    # Ghi tương quan lên đồ thị
    lag0 = [r for r in corr_results if r["lag"] == 0]
    if lag0:
        info = lag0[0]
        ax.text(0.05, 0.95,
                f"Pearson r = {info['pearson_r']}, p = {info['pearson_p']}\n"
                f"Spearman ρ = {info['spearman_r']}, p = {info['spearman_p']}\n"
                f"n = {info['n_pairs']} tháng",
                transform=ax.transAxes, fontsize=9, va="top",
                bbox=dict(boxstyle="round", facecolor="lightyellow", alpha=0.9))

    ax.set_xlabel("Lượng mưa lưu vực (mm/tháng)")
    ax.set_ylabel("Lưu lượng trung bình về hồ (m³/s)")
    ax.set_title(
        "F08 — Scatter plot mưa tháng – lưu lượng tháng\n"
        "(CHIRPS v3 Final × Website Sông Ba Hạ; "
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
def compute_all_correlations(valid, monthly):
    """Tính tương quan lag 0 và lag 1, kèm deseasonalised."""
    results = []
    excluded_months = list(set(monthly["year_month"]) - set(valid["year_month"]))

    rain = valid["rainfall_total_mm"].values
    flow = valid["inflow_mean_m3s"].values

    # ── B3: Lag 0 ─────────────────────────────────────────────────────
    pr, pp = compute_correlation(rain, flow, "pearson")
    sr, sp = compute_correlation(rain, flow, "spearman")
    results.append({
        "analysis": "B3 — Tương quan lag 0",
        "lag": 0,
        "variable_x": "rainfall_total_mm (mm/tháng)",
        "variable_y": "inflow_mean_m3s (m³/s)",
        "n_pairs": len(rain),
        "pearson_r": pr, "pearson_p": pp,
        "spearman_r": sr, "spearman_p": sp,
        "excluded_months": "; ".join(sorted(excluded_months)),
        "exclusion_reason": "LOW_COVERAGE hoặc thiếu dữ liệu mưa/lưu lượng",
        "interpretation_limit": (
            "Tương quan không chứng minh quan hệ nhân quả. "
            "Cả mưa và lưu lượng đều có tính mùa → có thể thổi phồng hệ số. "
            "Ba năm dữ liệu không đại diện cho quy luật lâu dài."
        )
    })

    # ── B4: Lag 1 ─────────────────────────────────────────────────────
    # Lưu lượng tháng hiện tại ~ mưa tháng trước
    valid_sorted = valid.sort_values("year_month").reset_index(drop=True)
    pairs_lag1 = []
    for i in range(1, len(valid_sorted)):
        ym_curr = valid_sorted.iloc[i]["year_month"]
        ym_prev = valid_sorted.iloc[i - 1]["year_month"]

        # Kiểm tra tháng liên tiếp
        curr_dt = pd.Timestamp(ym_curr + "-01")
        prev_dt = pd.Timestamp(ym_prev + "-01")
        if (curr_dt - prev_dt).days <= 35:  # ~1 tháng
            pairs_lag1.append({
                "rain_prev": valid_sorted.iloc[i - 1]["rainfall_total_mm"],
                "flow_curr": valid_sorted.iloc[i]["inflow_mean_m3s"],
            })

    if pairs_lag1:
        lag1_df = pd.DataFrame(pairs_lag1)
        rain_l1 = lag1_df["rain_prev"].values
        flow_l1 = lag1_df["flow_curr"].values
        pr1, pp1 = compute_correlation(rain_l1, flow_l1, "pearson")
        sr1, sp1 = compute_correlation(rain_l1, flow_l1, "spearman")
    else:
        pr1, pp1, sr1, sp1 = np.nan, np.nan, np.nan, np.nan
        rain_l1, flow_l1 = np.array([]), np.array([])

    results.append({
        "analysis": "B4 — Tương quan lag 1 tháng",
        "lag": 1,
        "variable_x": "rainfall_total_mm tháng trước (mm)",
        "variable_y": "inflow_mean_m3s tháng hiện tại (m³/s)",
        "n_pairs": len(pairs_lag1),
        "pearson_r": pr1, "pearson_p": pp1,
        "spearman_r": sr1, "spearman_p": sp1,
        "excluded_months": "; ".join(sorted(excluded_months)),
        "exclusion_reason": "LOW_COVERAGE, thiếu dữ liệu, hoặc tháng không liên tiếp",
        "interpretation_limit": (
            "Lag 1 tháng có thể phản ánh thời gian truyền nước trong lưu vực lớn, "
            "nhưng cũng có thể do trùng lặp tính mùa. "
            "Không kết luận đây là thời gian trễ thủy văn chính xác."
        )
    })

    # ── B6: Deseasonalised ────────────────────────────────────────────
    valid_copy = valid_sorted.copy()
    valid_copy["month_num"] = valid_copy["year_month"].str[5:7].astype(int)

    # Trung bình từng tháng lịch (chỉ 3 giá trị/tháng lịch)
    rain_monthly_mean = valid_copy.groupby("month_num")["rainfall_total_mm"].mean()
    flow_monthly_mean = valid_copy.groupby("month_num")["inflow_mean_m3s"].mean()

    valid_copy["rain_anomaly"] = valid_copy.apply(
        lambda row: row["rainfall_total_mm"] - rain_monthly_mean.get(row["month_num"], 0),
        axis=1
    )
    valid_copy["flow_anomaly"] = valid_copy.apply(
        lambda row: row["inflow_mean_m3s"] - flow_monthly_mean.get(row["month_num"], 0),
        axis=1
    )

    deseason = valid_copy.dropna(subset=["rain_anomaly", "flow_anomaly"])
    if len(deseason) >= 3:
        dpr, dpp = compute_correlation(
            deseason["rain_anomaly"].values,
            deseason["flow_anomaly"].values,
            "pearson"
        )
        dsr, dsp = compute_correlation(
            deseason["rain_anomaly"].values,
            deseason["flow_anomaly"].values,
            "spearman"
        )
    else:
        dpr, dpp, dsr, dsp = np.nan, np.nan, np.nan, np.nan

    results.append({
        "analysis": "B6 — Deseasonalised (kiểm tra nhạy)",
        "lag": 0,
        "variable_x": "Sai lệch mưa tháng so với TB tháng lịch (mm)",
        "variable_y": "Sai lệch lưu lượng tháng so với TB tháng lịch (m³/s)",
        "n_pairs": len(deseason),
        "pearson_r": dpr, "pearson_p": dpp,
        "spearman_r": dsr, "spearman_p": dsp,
        "excluded_months": "",
        "exclusion_reason": "",
        "interpretation_limit": (
            "Mỗi tháng lịch chỉ có 3 giá trị theo năm → trung bình mùa không chính xác. "
            "Kết quả deseasonalised không mang ý nghĩa khẳng định mạnh, "
            "chỉ là phép kiểm tra độ nhạy."
        )
    })

    return results


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# F09: So sánh kết quả tương quan
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def create_F09(corr_results):
    """F09 — So sánh kết quả tương quan lag 0 và lag 1."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Panel trái: Pearson
    analyses = [r["analysis"].split(" — ")[1] for r in corr_results]
    pearson_r = [r["pearson_r"] if not np.isnan(r["pearson_r"]) else 0 for r in corr_results]
    spearman_r = [r["spearman_r"] if not np.isnan(r["spearman_r"]) else 0 for r in corr_results]
    n_pairs = [r["n_pairs"] for r in corr_results]

    x = range(len(analyses))
    width = 0.35

    ax = axes[0]
    bars1 = ax.bar([i - width / 2 for i in x], pearson_r, width,
                   label="Pearson r", color="#1565C0", alpha=0.8)
    bars2 = ax.bar([i + width / 2 for i in x], spearman_r, width,
                   label="Spearman ρ", color="#E53935", alpha=0.8)

    ax.set_xticks(x)
    ax.set_xticklabels(analyses, rotation=30, ha="right", fontsize=8)
    ax.set_ylabel("Hệ số tương quan")
    ax.set_title("Hệ số tương quan", fontweight="bold")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    ax.set_ylim(-0.2, 1.1)

    # Ghi n trên thanh
    for bar, n in zip(bars1, n_pairs):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.02,
                f"n={n}", ha="center", fontsize=7)

    # Panel phải: p-value
    ax2 = axes[1]
    pearson_p = [r["pearson_p"] if not np.isnan(r["pearson_p"]) else 1 for r in corr_results]
    spearman_p = [r["spearman_p"] if not np.isnan(r["spearman_p"]) else 1 for r in corr_results]

    ax2.bar([i - width / 2 for i in x], pearson_p, width,
            label="Pearson p", color="#1565C0", alpha=0.5)
    ax2.bar([i + width / 2 for i in x], spearman_p, width,
            label="Spearman p", color="#E53935", alpha=0.5)
    ax2.axhline(y=0.05, color="green", linestyle="--", alpha=0.7, label="α = 0.05")

    ax2.set_xticks(x)
    ax2.set_xticklabels(analyses, rotation=30, ha="right", fontsize=8)
    ax2.set_ylabel("p-value")
    ax2.set_title("Ý nghĩa thống kê (p-value)", fontweight="bold")
    ax2.legend()
    ax2.grid(axis="y", alpha=0.3)

    fig.suptitle(
        "F09 — So sánh kết quả tương quan mưa – lưu lượng\n"
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


def main():
    print("=" * 60)
    print("GATE 5b — Phân tích mưa–dòng chảy (RQ3)")
    print("=" * 60)

    # Đọc dữ liệu
    print("\n[1/7] Đọc dữ liệu tháng...")
    monthly = load_monthly()
    print(f"  Tổng: {len(monthly)} tháng")

    # Lọc tháng hợp lệ
    print("\n[2/7] Lọc tháng đủ điều kiện...")
    valid = filter_valid_months(monthly)
    n_valid = len(valid)
    n_excluded = len(monthly) - n_valid
    print(f"  Hợp lệ: {n_valid} tháng, Loại: {n_excluded} tháng")

    if n_valid < 24:
        print(f"  ⚠️ Số tháng hợp lệ ({n_valid}) < 24.")
        print("  → Không đưa ra kết luận tổng quát về mối liên hệ.")
        print("  → Báo cáo cho người giám sát để quyết định hướng trình bày.")

    # Tính tương quan
    print("\n[3/7] Tính tương quan (B3–B6)...")
    corr_results = compute_all_correlations(valid, monthly)
    for r in corr_results:
        print(f"  {r['analysis']}:")
        print(f"    n={r['n_pairs']}, Pearson r={r['pearson_r']}, Spearman ρ={r['spearman_r']}")

    # Biểu đồ
    print("\n[4/7] F07 — Biểu đồ đồng thời...")
    create_F07(valid)

    print("\n[5/7] F08 — Scatter plot...")
    create_F08(valid, corr_results)

    print("\n[6/7] F09 — So sánh tương quan...")
    create_F09(corr_results)

    # Bảng
    print("\n[7/7] T05, T06...")
    create_T05(corr_results)
    create_T06()

    print("\n✅ GATE 5b (phân tích B — RQ3) hoàn thành.")
    if n_valid < 24:
        print("⚠️ LƯU Ý: < 24 tháng hợp lệ — cần trình người giám sát.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
