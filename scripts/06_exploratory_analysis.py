#!/usr/bin/env python3
"""
06_exploratory_analysis.py — GATE 5 (phần A): Phân tích RQ1 + RQ2
==================================================================
Đặc tả: V1.0 §V-A, V1.1 §12–13

Phần A1 — Khí tượng (RQ1):
    - Thống kê mô tả mưa + nhiệt độ
    - Tổng mưa năm, phân bố tháng, tính mùa
    - Biểu đồ F02, F03

Phần A2 — Thủy văn (RQ2):
    - Thống kê lưu lượng
    - Hydrograph ngày (F04), lưu lượng tháng (F05)
    - Biến động mực nước (F06)
    - Sự kiện nổi bật

Đầu ra:
    outputs/figures/F02_rainfall_monthly.png
    outputs/figures/F03_temperature_monthly.png
    outputs/figures/F04_inflow_daily_hydrograph.png
    outputs/figures/F05_inflow_monthly.png
    outputs/figures/F06_upstream_level.png
    outputs/tables/T01_data_sources.csv
    outputs/tables/T02_hydrology_qa_results.csv
    outputs/tables/T03_meteorology_stats.csv
    outputs/tables/T04_hydrology_stats.csv
"""

import sys
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROC_DIR = ROOT / "data" / "processed"
FIG_DIR = ROOT / "outputs" / "figures"
TAB_DIR = ROOT / "outputs" / "tables"
FIG_DIR.mkdir(parents=True, exist_ok=True)
TAB_DIR.mkdir(parents=True, exist_ok=True)

# Cấu hình matplotlib cho tiếng Việt
plt.rcParams.update({
    "figure.dpi": 200,
    "savefig.dpi": 200,
    "font.size": 10,
    "axes.titlesize": 12,
    "axes.labelsize": 10,
})

COVERAGE_THRESHOLD = 0.90


def load_data():
    """Đọc dữ liệu tích hợp."""
    daily_path = PROC_DIR / "hydromet_daily.csv"
    monthly_path = PROC_DIR / "hydromet_monthly.csv"
    hydro_clean = PROC_DIR / "hydrology_clean.csv"
    hydro_exc = PROC_DIR / "hydrology_exceptions.csv"

    if not daily_path.exists() or not monthly_path.exists():
        sys.exit(f"[LỖI] Chưa có dữ liệu tích hợp. Chạy GATE 4 trước.")

    daily = pd.read_csv(daily_path)
    daily["date"] = pd.to_datetime(daily["date"])
    monthly = pd.read_csv(monthly_path)

    hydro_qa = None
    if hydro_clean.exists():
        hydro_qa = pd.read_csv(hydro_clean)
        hydro_qa["date"] = pd.to_datetime(hydro_qa["date"])

    exceptions = None
    if hydro_exc.exists():
        exceptions = pd.read_csv(hydro_exc)

    return daily, monthly, hydro_qa, exceptions


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# T01: Danh mục nguồn dữ liệu
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def _first_meta(path, column):
    """Lấy giá trị metadata (source/status) thực tế từ CSV đầu ra."""
    try:
        s = pd.read_csv(path, usecols=[column])[column].dropna()
        return str(s.iloc[0]) if len(s) else "không rõ"
    except Exception:
        return "không rõ"


def create_T01():
    """T01 — Danh mục nguồn dữ liệu.

    Nguồn của mưa/nhiệt độ được đọc từ chính CSV đầu ra để T01 không thể
    mâu thuẫn với dữ liệu thực tế đã dùng.
    """
    rain_src = _first_meta(PROC_DIR / "rainfall_monthly.csv", "source")
    temp_src = _first_meta(PROC_DIR / "temperature_monthly.csv", "source")
    temp_note = _first_meta(PROC_DIR / "temperature_monthly.csv", "status")

    records = [
        {
            "variable": "Lưu lượng nước về hồ (m³/s)",
            "source": "Website Sông Ba Hạ (sbh.vn)",
            "type": "Số liệu công trình",
            "spatial_resolution": "Điểm (tại đập)",
            "temporal_resolution": "Ngày",
            "period": "2023-01 – 2025-12",
            "notes": "Chưa xác minh ý nghĩa thời gian (trung bình ngày vs tức thời)"
        },
        {
            "variable": "Mực nước thượng/hạ lưu (m)",
            "source": "Website Sông Ba Hạ (sbh.vn)",
            "type": "Số liệu công trình",
            "spatial_resolution": "Điểm",
            "temporal_resolution": "Ngày",
            "period": "2023-01 – 2025-12",
            "notes": "Một số ngày nghi đảo cột; đánh dấu SUSPECT, chưa xác minh độc lập"
        },
        {
            "variable": "Lượng mưa lưu vực (mm)",
            "source": rain_src,
            "type": "Vệ tinh kết hợp quan trắc",
            "spatial_resolution": "~0.05° (~5 km)",
            "temporal_resolution": "Tháng (P0), Ngày rnl (P1)",
            "period": "2023-01 – 2025-12",
            "notes": ("Mưa ngày phân rã từ tổng 5 ngày bằng ERA5; "
                      "trung bình xấp xỉ pixel-mask + cos(vĩ độ); chưa tính diện tích giao pixel biên, đã kiểm tra độ nhạy 36 tháng")
        },
        {
            "variable": "Nhiệt độ không khí 2m (°C)",
            "source": temp_src,
            "type": "Tái phân tích",
            "spatial_resolution": "~0.1° (~9 km)" if "ERA5" in temp_src else "Điểm lưới",
            "temporal_resolution": "Tháng (P0), Ngày (P1)",
            "period": "2023-01 – 2025-12",
            "notes": f"Trạng thái dữ liệu: {temp_note}"
        },
        {
            "variable": "Ranh giới lưu vực",
            "source": "HydroBASINS v1c (HydroSHEDS/WWF)",
            "type": "Dữ liệu địa lý toàn cầu",
            "spatial_resolution": "~15 arc-second",
            "temporal_resolution": "Tĩnh",
            "period": "—",
            "notes": "Diện tích tham khảo 11.115 km²; cửa ra theo OSM way/480785944"
        },
    ]
    df = pd.DataFrame(records)
    path = TAB_DIR / "T01_data_sources.csv"
    df.to_csv(path, index=False, encoding="utf-8-sig")
    print(f"  → {path}")
    return df


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# T02: Kết quả kiểm tra chất lượng thủy văn
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def create_T02(hydro_qa, exceptions):
    """T02 — Kết quả kiểm tra chất lượng thủy văn (đủ 6 biến, V1.1 §5–6)."""
    if hydro_qa is None:
        print("  ⚠️ Không có hydrology_clean.csv")
        return

    var_map = [
        ("inflow_m3s", "inflow_quality", "Lưu lượng về hồ"),
        ("upstream_level_m", "upstream_level_quality", "Mực nước thượng lưu"),
        ("downstream_level_m", "downstream_level_quality", "Mực nước hạ lưu"),
        ("release_m3s", "release_quality", "Lưu lượng xả"),
        ("daily_energy_kwh", "daily_energy_quality", "Sản lượng điện ngày"),
        ("max_power_mw", "max_power_quality", "Công suất cực đại"),
    ]

    records = []
    total = len(hydro_qa)
    for col, qcol, label in var_map:
        if col not in hydro_qa.columns or qcol not in hydro_qa.columns:
            continue
        s = hydro_qa[col]
        q = hydro_qa[qcol]
        valid = (q == "VALID").sum()
        records.append({
            "variable": col,
            "label": label,
            "unit": ("m³/s" if "m3s" in col else
                     "m" if col.endswith("_m") else
                     "kWh" if "energy" in col else "MW"),
            "total_days": total,
            "VALID": int(valid),
            "SUSPECT": int((q == "SUSPECT").sum()),
            "MISSING": int((q == "MISSING").sum()),
            "INVALID_CONFIRMED": int((q == "INVALID_CONFIRMED").sum()),
            "CORRECTED": int((q == "CORRECTED").sum()),
            "valid_pct": round(valid / total * 100, 2),
            "missing_pct": round((q == "MISSING").sum() / total * 100, 2),
            "n_zero": int((s == 0).sum()),
            "min": round(s.min(), 2) if s.notna().any() else np.nan,
            "max": round(s.max(), 2) if s.notna().any() else np.nan,
        })

    df = pd.DataFrame(records)

    # Dòng tổng hợp số ngoại lệ theo cờ (để T02 khớp T06)
    if exceptions is not None and len(exceptions) > 0:
        exc_summary = (exceptions.groupby(["variable", "flag"]).size()
                       .reset_index(name="n_records"))
        exc_path = TAB_DIR / "T02b_exception_counts.csv"
        exc_summary.to_csv(exc_path, index=False, encoding="utf-8-sig")
        print(f"  → {exc_path}")

    path = TAB_DIR / "T02_hydrology_qa_results.csv"
    df.to_csv(path, index=False, encoding="utf-8-sig")
    print(f"  → {path}")
    return df


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# T03: Thống kê khí tượng
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def create_T03(monthly):
    """T03 — Thống kê khí tượng."""
    records = []

    # Mưa tháng
    rain = monthly["rainfall_total_mm"].dropna()
    if len(rain) > 0:
        records.append({
            "variable": "Lượng mưa tháng (mm)",
            "n_months": len(rain),
            "mean": round(rain.mean(), 1),
            "median": round(rain.median(), 1),
            "std": round(rain.std(), 1),
            "min": round(rain.min(), 1),
            "max": round(rain.max(), 1),
            "total_3yr": round(rain.sum(), 1),
        })

    # Mưa năm
    monthly_copy = monthly.copy()
    monthly_copy["year"] = monthly_copy["year_month"].str[:4].astype(int)
    for year in [2023, 2024, 2025]:
        yr_rain = monthly_copy[monthly_copy["year"] == year]["rainfall_total_mm"].dropna()
        if len(yr_rain) > 0:
            records.append({
                "variable": f"Tổng mưa năm {year} (mm)",
                "n_months": len(yr_rain),
                "mean": np.nan,
                "median": np.nan,
                "std": np.nan,
                "min": np.nan,
                "max": np.nan,
                "total_3yr": round(yr_rain.sum(), 1),
            })

    # Nhiệt độ
    temp = monthly["temperature_mean_c"].dropna()
    if len(temp) > 0:
        records.append({
            "variable": "Nhiệt độ tháng (°C)",
            "n_months": len(temp),
            "mean": round(temp.mean(), 1),
            "median": round(temp.median(), 1),
            "std": round(temp.std(), 1),
            "min": round(temp.min(), 1),
            "max": round(temp.max(), 1),
            "total_3yr": np.nan,
        })

    # Đặc trưng mùa mưa / mùa khô (V1.1 §12.5)
    if len(rain) > 0:
        r = monthly.dropna(subset=["rainfall_total_mm"]).copy()
        r["month_num"] = r["year_month"].str[5:7].astype(int)
        r["season"] = np.where(r["month_num"].isin([5, 6, 7, 8, 9, 10, 11]),
                               "Mùa mưa (T5–T11)", "Mùa khô (T12–T4)")
        total_all = r["rainfall_total_mm"].sum()
        for season, grp in r.groupby("season"):
            records.append({
                "variable": f"Lượng mưa tháng — {season}",
                "n_months": len(grp),
                "mean": round(grp["rainfall_total_mm"].mean(), 1),
                "median": round(grp["rainfall_total_mm"].median(), 1),
                "std": round(grp["rainfall_total_mm"].std(), 1),
                "min": round(grp["rainfall_total_mm"].min(), 1),
                "max": round(grp["rainfall_total_mm"].max(), 1),
                "total_3yr": round(grp["rainfall_total_mm"].sum(), 1),
                "share_pct": round(grp["rainfall_total_mm"].sum() / total_all * 100, 1),
            })

    df = pd.DataFrame(records)
    path = TAB_DIR / "T03_meteorology_stats.csv"
    df.to_csv(path, index=False, encoding="utf-8-sig")
    print(f"  → {path}")
    return df


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# T04: Thống kê thủy văn
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def create_T04(daily, hydro_qa):
    """T04 — Thống kê thủy văn (phân bố, phân vị, theo năm — V1.1 §13)."""
    records = []

    if hydro_qa is not None:
        valid_mask = hydro_qa["inflow_quality"].isin(["VALID", "CORRECTED"])
        inflow_df = hydro_qa.loc[valid_mask, ["date", "inflow_m3s"]].dropna()
    else:
        inflow_df = daily[["date", "inflow_m3s"]].dropna()

    inflow = inflow_df["inflow_m3s"]

    def quant(v, q):
        return round(v.quantile(q), 3) if len(v) else np.nan

    if len(inflow) > 0:
        records.append({
            "variable": "Lưu lượng về hồ (m³/s)",
            "n_days": len(inflow),
            "mean": round(inflow.mean(), 3),
            "median": round(inflow.median(), 3),
            "std": round(inflow.std(), 3),
            "cv": round(inflow.std() / inflow.mean(), 3) if inflow.mean() else np.nan,
            "min": round(inflow.min(), 3),
            "p05": quant(inflow, 0.05),
            "p10": quant(inflow, 0.10),
            "p25": quant(inflow, 0.25),
            "p75": quant(inflow, 0.75),
            "p90": quant(inflow, 0.90),
            "p95": quant(inflow, 0.95),
            "max": round(inflow.max(), 3),
            "skewness": round(inflow.skew(), 3),
            "kurtosis": round(inflow.kurtosis(), 3),
        })

    # Mực nước thượng lưu (VALID + CORRECTED)
    if hydro_qa is not None:
        valid_mask = hydro_qa["upstream_level_quality"].isin(["VALID", "CORRECTED"])
        level = hydro_qa.loc[valid_mask, "upstream_level_m"].dropna()
    else:
        level = daily["upstream_level_m"].dropna()

    if len(level) > 0:
        records.append({
            "variable": "Mực nước thượng lưu (m)",
            "n_days": len(level),
            "mean": round(level.mean(), 3),
            "median": round(level.median(), 3),
            "std": round(level.std(), 3),
            "cv": round(level.std() / level.mean(), 3),
            "min": round(level.min(), 3),
            "p05": quant(level, 0.05),
            "p10": quant(level, 0.10),
            "p25": quant(level, 0.25),
            "p75": quant(level, 0.75),
            "p90": quant(level, 0.90),
            "p95": quant(level, 0.95),
            "max": round(level.max(), 3),
            "skewness": round(level.skew(), 3),
            "kurtosis": round(level.kurtosis(), 3),
        })

    # Theo năm — nhận diện thời kỳ dòng chảy cao/thấp (V1.1 §13.4)
    inflow_df = inflow_df.copy()
    inflow_df["date"] = pd.to_datetime(inflow_df["date"])
    inflow_df["year"] = inflow_df["date"].dt.year
    for year, grp in inflow_df.groupby("year"):
        v = grp["inflow_m3s"]
        records.append({
            "variable": f"Lưu lượng về hồ — năm {year} (m³/s)",
            "n_days": len(v),
            "mean": round(v.mean(), 3),
            "median": round(v.median(), 3),
            "std": round(v.std(), 3),
            "cv": round(v.std() / v.mean(), 3) if v.mean() else np.nan,
            "min": round(v.min(), 3),
            "p05": quant(v, 0.05),
            "p10": quant(v, 0.10),
            "p25": quant(v, 0.25),
            "p75": quant(v, 0.75),
            "p90": quant(v, 0.90),
            "p95": quant(v, 0.95),
            "max": round(v.max(), 3),
            "skewness": round(v.skew(), 3),
            "kurtosis": round(v.kurtosis(), 3),
        })

    df = pd.DataFrame(records)
    path = TAB_DIR / "T04_hydrology_stats.csv"
    df.to_csv(path, index=False, encoding="utf-8-sig")
    print(f"  → {path}")
    return df


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# F02: Biến động lượng mưa theo tháng
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def create_F02(monthly):
    """F02 — Biến động lượng mưa theo tháng 2023–2025."""
    rain = monthly[["year_month", "rainfall_total_mm"]].dropna(subset=["rainfall_total_mm"])
    if len(rain) == 0:
        print("  ⚠️ Không có dữ liệu mưa để vẽ F02")
        return

    fig, ax = plt.subplots(figsize=(14, 5))
    x = range(len(rain))
    colors = []
    for ym in rain["year_month"]:
        m = int(ym.split("-")[1])
        if m in [5, 6, 7, 8, 9, 10, 11]:  # Mùa mưa
            colors.append("#2196F3")
        else:
            colors.append("#FF9800")

    ax.bar(x, rain["rainfall_total_mm"], color=colors, edgecolor="white", linewidth=0.5)
    ax.set_xticks(range(0, len(rain), 3))
    ax.set_xticklabels(rain["year_month"].iloc[::3], rotation=45, ha="right")
    ax.set_xlabel("Tháng")
    ax.set_ylabel("Lượng mưa (mm)")
    ax.set_title("F02 — Biến động lượng mưa theo tháng 2023–2025\n"
                 "(Nguồn: CHIRPS v3 Final — trung bình lưu vực sông Ba đến TĐ Sông Ba Hạ)",
                 fontweight="bold")

    # Legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor="#2196F3", label="Mùa mưa (T5–T11)"),
        Patch(facecolor="#FF9800", label="Mùa ít mưa (T12–T4)")
    ]
    ax.legend(handles=legend_elements, loc="upper left")
    ax.grid(axis="y", alpha=0.3)

    path = FIG_DIR / "F02_rainfall_monthly.png"
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"  → {path}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# F03: Nhiệt độ trung bình tháng
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def create_F03(monthly):
    """F03 — Nhiệt độ trung bình tháng."""
    temp = monthly[["year_month", "temperature_mean_c"]].dropna(subset=["temperature_mean_c"])
    if len(temp) == 0:
        print("  ⚠️ Không có dữ liệu nhiệt độ để vẽ F03")
        return

    fig, ax = plt.subplots(figsize=(14, 5))
    x = range(len(temp))
    ax.plot(x, temp["temperature_mean_c"], "o-", color="#E53935",
            markersize=5, linewidth=1.5, label="Nhiệt độ trung bình")
    ymin = float(temp["temperature_mean_c"].min())
    ymax = float(temp["temperature_mean_c"].max())
    ax.set_ylim(max(0.0, ymin - 2.0), ymax + 1.5)
    ax.fill_between(x, temp["temperature_mean_c"], ax.get_ylim()[0],
                    alpha=0.15, color="#E53935")
    ax.set_xticks(range(0, len(temp), 3))
    ax.set_xticklabels(temp["year_month"].iloc[::3], rotation=45, ha="right")
    ax.set_xlabel("Tháng")
    ax.set_ylabel("Nhiệt độ (°C)")
    ax.set_title("F03 — Nhiệt độ trung bình tháng 2023–2025\n"
                 "(Nguồn: ERA5-Land 2 m — trung bình có trọng số cos(vĩ độ) "
                 "trên lưu vực)",
                 fontweight="bold")
    ax.legend()
    ax.grid(alpha=0.3)

    path = FIG_DIR / "F03_temperature_monthly.png"
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"  → {path}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# F04: Hydrograph lưu lượng theo ngày
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def create_F04(daily, hydro_qa):
    """F04 — Biểu đồ lưu lượng nước về hồ theo ngày."""
    fig, ax = plt.subplots(figsize=(16, 6))

    dates = daily["date"]
    inflow = daily["inflow_m3s"]

    # Vẽ tất cả giá trị
    ax.plot(dates, inflow, linewidth=0.6, color="#1565C0", alpha=0.8,
            label="Lưu lượng về hồ")

    # Đánh dấu SUSPECT
    if hydro_qa is not None:
        suspect_mask = hydro_qa["inflow_quality"] == "SUSPECT"
        suspect_dates = hydro_qa.loc[suspect_mask, "date"]
        suspect_vals = hydro_qa.loc[suspect_mask, "inflow_m3s"]
        ax.scatter(suspect_dates, suspect_vals, c="orange", s=15, zorder=4,
                   label="Nghi vấn (SUSPECT)", alpha=0.7)

        invalid_mask = hydro_qa["inflow_quality"] == "INVALID_CONFIRMED"
        if invalid_mask.any():
            inv_dates = hydro_qa.loc[invalid_mask, "date"]
            inv_vals = hydro_qa.loc[invalid_mask, "inflow_m3s"]
            ax.scatter(inv_dates, inv_vals, c="red", s=20, zorder=5,
                       label="Xác nhận sai (INVALID)", marker="x")

    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    plt.xticks(rotation=45, ha="right")

    ax.set_xlabel("Ngày")
    ax.set_ylabel("Lưu lượng (m³/s)")
    ax.set_title("F04 — Lưu lượng nước về hồ theo ngày 2023–2025\n"
                 "(Nguồn: Website Sông Ba Hạ — sbh.vn)",
                 fontweight="bold")
    ax.legend(loc="upper left")
    ax.grid(alpha=0.3)

    path = FIG_DIR / "F04_inflow_daily_hydrograph.png"
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"  → {path}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# F05: Lưu lượng tháng
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def create_F05(monthly):
    """F05 — Lưu lượng nước về hồ theo tháng."""
    flow = monthly[["year_month", "inflow_mean_m3s", "quality_status"]].copy()

    fig, ax = plt.subplots(figsize=(14, 5))
    x = range(len(flow))
    colors = ["#EF5350" if "LOW_COVERAGE" in str(qs) else "#1E88E5"
              for qs in flow["quality_status"]]
    ax.bar(x, flow["inflow_mean_m3s"], color=colors, edgecolor="white", linewidth=0.5)
    ax.set_xticks(range(0, len(flow), 3))
    ax.set_xticklabels(flow["year_month"].iloc[::3], rotation=45, ha="right")
    ax.set_xlabel("Tháng")
    ax.set_ylabel("Lưu lượng trung bình (m³/s)")
    ax.set_title(
        "F05 — Lưu lượng nước về hồ trung bình theo tháng 2023–2025\n"
        "(Trung bình các giá trị ngày đủ ĐK; nguồn: Website Sông Ba Hạ)",
        fontweight="bold")

    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor="#1E88E5", label="Đủ dữ liệu"),
        Patch(facecolor="#EF5350", label="LOW_COVERAGE (< 90%)")
    ]
    ax.legend(handles=legend_elements)
    ax.grid(axis="y", alpha=0.3)

    path = FIG_DIR / "F05_inflow_monthly.png"
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"  → {path}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# F06: Biến động mực nước thượng lưu
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def create_F06(daily, hydro_qa):
    """F06 — Biến động mực nước thượng lưu sau kiểm định.

    Nếu mực nước không đủ tin cậy → vẽ phân bố lưu lượng thay thế.
    """
    # Kiểm tra mực nước có đủ tin cậy
    if hydro_qa is not None:
        valid_level = hydro_qa["upstream_level_quality"].isin(["VALID", "CORRECTED"])
        valid_pct = valid_level.sum() / len(hydro_qa) * 100
    else:
        valid_pct = 100

    fig, ax = plt.subplots(figsize=(16, 6))

    if valid_pct >= 80:
        # Vẽ mực nước
        if hydro_qa is not None:
            valid_mask = hydro_qa["upstream_level_quality"].isin(["VALID", "CORRECTED"])
            dates = hydro_qa.loc[valid_mask, "date"]
            levels = hydro_qa.loc[valid_mask, "upstream_level_m"]
        else:
            dates = daily["date"]
            levels = daily["upstream_level_m"]

        ax.plot(dates, levels, linewidth=0.6, color="#7B1FA2")
        ax.axhline(y=111.5, color="red", linestyle="--", alpha=0.5,
                   label="Mực nước dâng bình thường (111.5 m)")
        ax.axhline(y=95.0, color="orange", linestyle="--", alpha=0.5,
                   label="Mực nước chết (95.0 m)")
        ax.set_ylabel("Mực nước (m)")
        ax.set_title(
            f"F06 — Biến động mực nước thượng lưu sau kiểm định 2023–2025\n"
            f"({valid_pct:.0f}% dữ liệu hợp lệ; nguồn: Website Sông Ba Hạ)",
            fontweight="bold")
        ax.legend(loc="upper right")
    else:
        # Thay thế: phân bố lưu lượng
        if hydro_qa is not None:
            valid_mask = hydro_qa["inflow_quality"].isin(["VALID", "CORRECTED"])
            inflow = hydro_qa.loc[valid_mask, "inflow_m3s"].dropna()
        else:
            inflow = daily["inflow_m3s"].dropna()

        ax.hist(inflow, bins=50, color="#7B1FA2", edgecolor="white",
                alpha=0.8)
        ax.set_xlabel("Lưu lượng (m³/s)")
        ax.set_ylabel("Số ngày")
        ax.set_title(
            "F06 (thay thế) — Phân bố lưu lượng nước về hồ 2023–2025\n"
            f"(Mực nước không đủ tin cậy: {valid_pct:.0f}% hợp lệ; "
            "nguồn: Website Sông Ba Hạ)",
            fontweight="bold")

    if isinstance(ax.xaxis.get_major_formatter(), mdates.DateFormatter) or valid_pct >= 80:
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        plt.xticks(rotation=45, ha="right")

    ax.grid(alpha=0.3)

    path = FIG_DIR / "F06_upstream_level.png"
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"  → {path}")


def create_F10(daily, hydro_qa):
    """F10 — Phân bố lưu lượng về hồ (V1.1 §13.4).

    Bổ sung ngoài danh mục tối thiểu F01–F09 để đáp ứng yêu cầu phân tích
    phân bố; không thay thế hình nào trong danh mục bắt buộc.
    """
    if hydro_qa is not None:
        valid_mask = hydro_qa["inflow_quality"].isin(["VALID", "CORRECTED"])
        d = hydro_qa.loc[valid_mask, ["date", "inflow_m3s"]].dropna().copy()
    else:
        d = daily[["date", "inflow_m3s"]].dropna().copy()

    if len(d) == 0:
        print("  ⚠️ Không có dữ liệu lưu lượng để vẽ F10")
        return

    d["date"] = pd.to_datetime(d["date"])
    d["year"] = d["date"].dt.year
    d["season"] = np.where(d["date"].dt.month.isin([5, 6, 7, 8, 9, 10, 11]),
                           "Mùa mưa (T5–T11)", "Mùa khô (T12–T4)")

    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))

    ax = axes[0]
    bins = np.logspace(np.log10(max(d["inflow_m3s"].min(), 0.1)),
                       np.log10(d["inflow_m3s"].max()), 45)
    ax.hist(d["inflow_m3s"], bins=bins, color="#1E88E5",
            edgecolor="white", linewidth=0.4)
    ax.set_xscale("log")
    ax.axvline(d["inflow_m3s"].median(), color="#E53935", linestyle="--",
               label=f"Trung vị = {d['inflow_m3s'].median():,.0f} m³/s")
    ax.axvline(d["inflow_m3s"].quantile(0.95), color="#FB8C00", linestyle=":",
               label=f"P95 = {d['inflow_m3s'].quantile(0.95):,.0f} m³/s")
    ax.set_xlabel("Lưu lượng về hồ (m³/s, thang log)")
    ax.set_ylabel("Số ngày")
    ax.set_title("(a) Phân bố toàn giai đoạn", fontweight="bold")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)

    ax = axes[1]
    groups = [d.loc[d["year"] == y, "inflow_m3s"].values for y in [2023, 2024, 2025]]
    bp = ax.boxplot(groups, tick_labels=["2023", "2024", "2025"], patch_artist=True,
                    showfliers=True, flierprops=dict(marker=".", markersize=3,
                                                     alpha=0.5))
    for patch, color in zip(bp["boxes"], ["#90CAF9", "#A5D6A7", "#FFCC80"]):
        patch.set_facecolor(color)
    ax.set_yscale("log")
    ax.set_xlabel("Năm")
    ax.set_ylabel("Lưu lượng về hồ (m³/s, thang log)")
    ax.set_title("(b) Phân bố theo năm", fontweight="bold")
    ax.grid(alpha=0.3)

    fig.suptitle(
        "F10 — Phân bố lưu lượng nước về hồ 2023–2025 "
        "(chỉ ngày VALID/CORRECTED)\nNguồn: Website Sông Ba Hạ — sbh.vn",
        fontweight="bold", fontsize=11)
    fig.tight_layout()

    path = FIG_DIR / "F10_inflow_distribution.png"
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"  → {path}")


def main():
    print("=" * 60)
    print("GATE 5a — Phân tích khám phá (RQ1 + RQ2)")
    print("=" * 60)

    print("\n[1/9] Đọc dữ liệu...")
    daily, monthly, hydro_qa, exceptions = load_data()

    print("\n[2/9] T01 — Danh mục nguồn dữ liệu...")
    create_T01()

    print("\n[3/9] T02 — Kết quả QA thủy văn...")
    create_T02(hydro_qa, exceptions)

    print("\n[4/9] T03 — Thống kê khí tượng...")
    create_T03(monthly)

    print("\n[5/9] T04 — Thống kê thủy văn...")
    create_T04(daily, hydro_qa)

    print("\n[6/9] Biểu đồ khí tượng (F02, F03)...")
    create_F02(monthly)
    create_F03(monthly)

    print("\n[7/9] Biểu đồ thủy văn (F04, F05)...")
    create_F04(daily, hydro_qa)
    create_F05(monthly)

    print("\n[8/9] F06 — Mực nước / phân bố lưu lượng...")
    create_F06(daily, hydro_qa)

    print("\n[9/9] F10 — Phân bố lưu lượng...")
    create_F10(daily, hydro_qa)

    print("\n✅ GATE 5a (phân tích A — RQ1, RQ2) hoàn thành.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
