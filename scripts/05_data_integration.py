#!/usr/bin/env python3
"""
05_data_integration.py — GATE 4: Tích hợp dữ liệu khí tượng–thủy văn
======================================================================
Đặc tả: V1.0 §IV-D, V1.1 §11

Tạo hai bảng chính:
    - hydromet_daily.csv  (1.096 ngày, cờ QA riêng từng biến)
    - hydromet_monthly.csv (36 tháng, tổng hợp có kiểm soát)

Quy tắc:
    - Mưa tháng = tổng lượng mưa tích lũy (mm)
    - Nhiệt độ tháng = trung bình (°C)
    - Lưu lượng tháng = trung bình các giá trị ngày đủ điều kiện (m³/s)
    - Không cộng m³/s → "tổng lượng nước"
    - Không dùng 0 thay missing
    - Không tự dịch thời gian

Đầu ra:
    data/processed/hydromet_daily.csv
    data/processed/hydromet_monthly.csv
    data/processed/integration_qa.csv
    outputs/quality/data_dictionary.md
"""

import sys
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
import numpy as np
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROC_DIR = ROOT / "data" / "processed"
QA_DIR = ROOT / "outputs" / "quality"
QA_DIR.mkdir(parents=True, exist_ok=True)

# Đầu vào
HYDRO_CLEAN = PROC_DIR / "hydrology_clean.csv"
RAIN_MONTHLY = PROC_DIR / "rainfall_monthly.csv"
RAIN_DAILY = PROC_DIR / "rainfall_daily.csv"
TEMP_MONTHLY = PROC_DIR / "temperature_monthly.csv"
TEMP_DAILY = PROC_DIR / "temperature_daily.csv"

COVERAGE_THRESHOLD = 0.90  # 90% ngày hợp lệ


def load_hydrology():
    """Đọc hydrology_clean.csv."""
    if not HYDRO_CLEAN.exists():
        sys.exit(f"[LỖI] Chưa có: {HYDRO_CLEAN}. Chạy GATE 1 trước.")
    df = pd.read_csv(HYDRO_CLEAN)
    df["date"] = pd.to_datetime(df["date"])
    return df


def load_rainfall_monthly():
    if not RAIN_MONTHLY.exists():
        print(f"  ⚠️ Chưa có {RAIN_MONTHLY}")
        return None
    return pd.read_csv(RAIN_MONTHLY)


def load_rainfall_daily():
    if not RAIN_DAILY.exists():
        print(f"  ⚠️ Chưa có {RAIN_DAILY}")
        return None
    df = pd.read_csv(RAIN_DAILY)
    df["date"] = pd.to_datetime(df["date"])
    return df


def load_temperature_monthly():
    if not TEMP_MONTHLY.exists():
        print(f"  ⚠️ Chưa có {TEMP_MONTHLY}")
        return None
    return pd.read_csv(TEMP_MONTHLY)


def load_temperature_daily():
    if not TEMP_DAILY.exists():
        print(f"  ⚠️ Chưa có {TEMP_DAILY}")
        return None
    df = pd.read_csv(TEMP_DAILY)
    df["date"] = pd.to_datetime(df["date"])
    return df


def build_daily_table(hydro, rain_daily, temp_daily):
    """Xây dựng bảng ngày tích hợp theo V1.1 §11."""
    # Nền: 1.096 ngày từ thủy văn
    daily = hydro[["date", "inflow_m3s", "upstream_level_m",
                    "inflow_quality", "upstream_level_quality"]].copy()

    # Mưa ngày
    if rain_daily is not None:
        rain = rain_daily[["date", "rainfall_mm"]].copy()
        rain["rainfall_quality"] = rain["rainfall_mm"].apply(
            lambda v: "VALID" if pd.notna(v) and v >= 0 else "MISSING"
        )
        daily = daily.merge(rain[["date", "rainfall_mm", "rainfall_quality"]],
                           on="date", how="left")
    else:
        daily["rainfall_mm"] = np.nan
        daily["rainfall_quality"] = "MISSING"

    # Nhiệt độ ngày
    if temp_daily is not None:
        temp = temp_daily[["date", "temperature_c"]].copy()
        temp["temperature_quality"] = temp["temperature_c"].apply(
            lambda v: "VALID" if pd.notna(v) else "MISSING"
        )
        daily = daily.merge(temp[["date", "temperature_c", "temperature_quality"]],
                           on="date", how="left")
    else:
        daily["temperature_c"] = np.nan
        daily["temperature_quality"] = "MISSING"

    # Điền cờ cho những dòng chưa ghép được
    daily["rainfall_quality"] = daily["rainfall_quality"].fillna("MISSING")
    daily["temperature_quality"] = daily["temperature_quality"].fillna("MISSING")

    # Rename cho đồng nhất
    daily = daily.rename(columns={
        "inflow_quality": "inflow_quality",
        "upstream_level_quality": "level_quality",
    })

    # Sắp xếp cột theo V1.1
    col_order = [
        "date", "rainfall_mm", "temperature_c",
        "inflow_m3s", "upstream_level_m",
        "inflow_quality", "level_quality",
        "rainfall_quality", "temperature_quality"
    ]
    daily = daily[[c for c in col_order if c in daily.columns]]
    daily["date"] = daily["date"].dt.strftime("%Y-%m-%d")
    return daily


def build_monthly_table(daily_df, rain_monthly, temp_monthly, hydro):
    """Xây dựng bảng tháng tích hợp theo V1.1 §11."""
    # Khung nền 36 tháng
    months = pd.date_range("2023-01", "2025-12", freq="MS")
    records = []

    # Chuyển daily_df thành datetime nếu cần
    df_d = daily_df.copy()
    df_d["date"] = pd.to_datetime(df_d["date"])

    for m in months:
        ym = m.strftime("%Y-%m")
        year, month = m.year, m.month

        # Lưu lượng
        grp = df_d[(df_d["date"].dt.year == year) & (df_d["date"].dt.month == month)]
        inflow_valid_mask = grp["inflow_quality"].isin(["VALID", "CORRECTED"])
        inflow_valid_days = int(inflow_valid_mask.sum())
        n_days = len(grp)
        inflow_coverage = inflow_valid_days / n_days if n_days > 0 else 0

        if inflow_valid_days > 0:
            inflow_mean = grp.loc[inflow_valid_mask, "inflow_m3s"].mean()
        else:
            inflow_mean = np.nan

        # Mực nước thượng lưu
        level_valid_mask = grp["level_quality"].isin(["VALID", "CORRECTED"])
        if level_valid_mask.sum() > 0:
            level_mean = grp.loc[level_valid_mask, "upstream_level_m"].mean()
        else:
            level_mean = np.nan

        # Mưa tháng — ưu tiên sản phẩm mưa tháng CHIRPS
        rainfall_total = np.nan
        rainfall_valid_days = int(grp["rainfall_mm"].notna().sum())
        rainfall_daily_sum = grp["rainfall_mm"].sum(min_count=1)
        rainfall_source = "không có"
        if rain_monthly is not None:
            rrow = rain_monthly[rain_monthly["year_month"] == ym]
            if len(rrow) > 0 and pd.notna(rrow.iloc[0]["rainfall_mm"]):
                rainfall_total = rrow.iloc[0]["rainfall_mm"]
                rainfall_source = str(rrow.iloc[0].get("source", "CHIRPS monthly"))

        # Nhiệt độ tháng — ưu tiên sản phẩm tháng ERA5-Land
        temp_mean = np.nan
        temp_valid_days = int(grp["temperature_c"].notna().sum())
        temp_source = "không có"
        if temp_monthly is not None:
            trow = temp_monthly[temp_monthly["year_month"] == ym]
            if len(trow) > 0 and pd.notna(trow.iloc[0]["temperature_c"]):
                temp_mean = trow.iloc[0]["temperature_c"]
                temp_source = str(trow.iloc[0].get("source", "ERA5-Land monthly"))

        # Quality status
        flags = []
        if inflow_coverage < COVERAGE_THRESHOLD:
            flags.append("LOW_COVERAGE")
        if np.isnan(rainfall_total):
            flags.append("NO_RAINFALL")
        elif rainfall_valid_days < n_days:
            flags.append("RAINFALL_MONTHLY_ONLY")
        if (pd.notna(rainfall_total) and pd.notna(rainfall_daily_sum)
                and rainfall_total > 0
                and abs(rainfall_daily_sum - rainfall_total) / rainfall_total > 0.10):
            flags.append("RAINFALL_DAILY_MISMATCH")
        if np.isnan(temp_mean):
            flags.append("NO_TEMPERATURE")

        records.append({
            "year_month": ym,
            "rainfall_total_mm": round(rainfall_total, 2) if pd.notna(rainfall_total) else np.nan,
            "rainfall_daily_sum_mm": (round(rainfall_daily_sum, 2)
                                      if pd.notna(rainfall_daily_sum) else np.nan),
            "temperature_mean_c": round(temp_mean, 2) if pd.notna(temp_mean) else np.nan,
            "inflow_mean_m3s": round(inflow_mean, 2) if pd.notna(inflow_mean) else np.nan,
            "upstream_level_mean_m": round(level_mean, 2) if pd.notna(level_mean) else np.nan,
            "rainfall_valid_days": rainfall_valid_days,
            "rainfall_coverage_pct": round(rainfall_valid_days / n_days * 100, 1) if n_days else np.nan,
            "temperature_valid_days": temp_valid_days,
            "temperature_coverage_pct": round(temp_valid_days / n_days * 100, 1) if n_days else np.nan,
            "inflow_valid_days": inflow_valid_days,
            "inflow_coverage_pct": round(inflow_coverage * 100, 1),
            "rainfall_source": rainfall_source,
            "temperature_source": temp_source,
            "quality_status": "|".join(flags) if flags else "OK",
        })

    return pd.DataFrame(records)


def build_integration_qa(daily_df, monthly_df):
    """Tạo integration_qa.csv — bảng đối chiếu trước/sau tích hợp."""
    records = []

    df_d = daily_df.copy()
    df_d["date"] = pd.to_datetime(df_d["date"])

    # Kiểm tra số ngày
    records.append({
        "check": "total_daily_rows",
        "expected": 1096,
        "actual": len(df_d),
        "status": "OK" if len(df_d) == 1096 else "FAIL"
    })

    # Kiểm tra số tháng
    records.append({
        "check": "total_monthly_rows",
        "expected": 36,
        "actual": len(monthly_df),
        "status": "OK" if len(monthly_df) == 36 else "FAIL"
    })

    # Kiểm tra không trùng ngày
    dups = df_d["date"].duplicated().sum()
    records.append({
        "check": "duplicate_dates",
        "expected": 0,
        "actual": dups,
        "status": "OK" if dups == 0 else "FAIL"
    })

    # Kiểm tra không trùng tháng
    dups_m = monthly_df["year_month"].duplicated().sum()
    records.append({
        "check": "duplicate_months",
        "expected": 0,
        "actual": dups_m,
        "status": "OK" if dups_m == 0 else "FAIL"
    })

    # Kiểm tra zero-as-missing
    inflow_zero_missing = (
        (df_d["inflow_m3s"] == 0) & (df_d["inflow_quality"] == "MISSING")
    ).sum()
    records.append({
        "check": "zero_as_missing_inflow",
        "expected": 0,
        "actual": int(inflow_zero_missing),
        "status": "OK" if inflow_zero_missing == 0 else "CHECK"
    })

    # Số ngày có dữ liệu mưa / nhiệt độ thực tế
    rain_valid = int(df_d["rainfall_mm"].notna().sum())
    temp_valid = int(df_d["temperature_c"].notna().sum())
    records.append({
        "check": "rainfall_daily_valid_days",
        "expected": 1096,
        "actual": rain_valid,
        "status": "OK" if rain_valid == 1096 else "FAIL"
    })
    records.append({
        "check": "temperature_daily_valid_days",
        "expected": 1096,
        "actual": temp_valid,
        "status": "OK" if temp_valid == 1096 else "FAIL"
    })

    # rainfall_valid_days ở bảng tháng phải khớp số ngày mưa thực tế
    if "rainfall_valid_days" in monthly_df.columns:
        recorded = int(monthly_df["rainfall_valid_days"].sum())
        records.append({
            "check": "rainfall_valid_days_consistency",
            "expected": rain_valid,
            "actual": recorded,
            "status": "OK" if recorded == rain_valid else "FAIL"
        })

    if "temperature_valid_days" in monthly_df.columns:
        recorded = int(monthly_df["temperature_valid_days"].sum())
        records.append({
            "check": "temperature_valid_days_consistency",
            "expected": temp_valid,
            "actual": recorded,
            "status": "OK" if recorded == temp_valid else "FAIL"
        })

    # Tổng mưa ngày trong tháng vs sản phẩm mưa tháng (V1.1 §9 Bước 6)
    if "rainfall_daily_sum_mm" in monthly_df.columns:
        both = monthly_df.dropna(subset=["rainfall_total_mm", "rainfall_daily_sum_mm"])
        n_mismatch = int((
            (both["rainfall_total_mm"] - both["rainfall_daily_sum_mm"]).abs()
            / both["rainfall_total_mm"].replace(0, np.nan) > 0.10
        ).sum()) if len(both) else 0
        records.append({
            "check": "monthly_vs_daily_rainfall_mismatch_gt10pct",
            "expected": 0,
            "actual": n_mismatch,
            "status": "OK" if n_mismatch == 0 else "CHECK"
        })

    # Không được có tháng thiếu cờ chất lượng
    empty_flag = int((monthly_df["quality_status"].astype(str).str.strip() == "").sum())
    records.append({
        "check": "months_without_quality_status",
        "expected": 0,
        "actual": empty_flag,
        "status": "OK" if empty_flag == 0 else "FAIL"
    })

    return pd.DataFrame(records)


def write_data_dictionary():
    """Viết data_dictionary.md."""
    rain_src = "không rõ"
    rain_daily_src = "không rõ"
    temp_src = "không rõ"
    try:
        r = pd.read_csv(PROC_DIR / "rainfall_monthly.csv", usecols=["source"])
        rain_src = str(r["source"].dropna().iloc[0])
    except Exception:
        pass
    try:
        rd = pd.read_csv(PROC_DIR / "rainfall_daily.csv", usecols=["source"])
        rain_daily_src = str(rd["source"].dropna().iloc[0])
    except Exception:
        rain_daily_src = rain_src
    try:
        t = pd.read_csv(PROC_DIR / "temperature_monthly.csv", usecols=["source"])
        temp_src = str(t["source"].dropna().iloc[0])
    except Exception:
        pass

    lines = [
        "# Từ điển dữ liệu (Data Dictionary)",
        "",
        "## hydromet_daily.csv",
        "",
        "| Cột | Kiểu | Đơn vị | Mô tả |",
        "|-----|------|--------|-------|",
        "| date | YYYY-MM-DD | — | Ngày lịch |",
        f"| rainfall_mm | float | mm | Lượng mưa trung bình lưu vực ({rain_daily_src}) |",
        f"| temperature_c | float | °C | Nhiệt độ 2 m trung bình lưu vực. Nguồn: {temp_src} |",
        "| inflow_m3s | float | m³/s | Lưu lượng nước về hồ (dữ liệu vận hành Sông Ba Hạ) |",
        "| upstream_level_m | float | m | Mực nước thượng lưu |",
        "| inflow_quality | str | — | Cờ QA: VALID/SUSPECT/MISSING/INVALID_CONFIRMED/CORRECTED |",
        "| level_quality | str | — | Cờ QA mực nước |",
        "| rainfall_quality | str | — | Cờ QA mưa |",
        "| temperature_quality | str | — | Cờ QA nhiệt độ |",
        "",
        "## hydromet_monthly.csv",
        "",
        "| Cột | Kiểu | Đơn vị | Mô tả |",
        "|-----|------|--------|-------|",
        "| year_month | YYYY-MM | — | Tháng lịch |",
        "| rainfall_total_mm | float | mm | Tổng lượng mưa tháng (sản phẩm mưa tháng) |",
        "| rainfall_daily_sum_mm | float | mm | Tổng mưa ngày trong tháng (để đối chiếu, không dùng thay) |",
        "| temperature_mean_c | float | °C | Nhiệt độ trung bình tháng |",
        "| inflow_mean_m3s | float | m³/s | Trung bình các giá trị lưu lượng ngày đủ ĐK |",
        "| upstream_level_mean_m | float | m | Trung bình mực nước thượng lưu |",
        "| rainfall_valid_days | int | ngày | Số ngày có giá trị mưa ngày hợp lệ |",
        "| rainfall_coverage_pct | float | % | Tỷ lệ ngày có mưa ngày hợp lệ |",
        "| temperature_valid_days | int | ngày | Số ngày có giá trị nhiệt độ hợp lệ |",
        "| temperature_coverage_pct | float | % | Tỷ lệ ngày có nhiệt độ hợp lệ |",
        "| inflow_valid_days | int | ngày | Số ngày lưu lượng đủ ĐK (VALID/CORRECTED) |",
        "| inflow_coverage_pct | float | % | Tỷ lệ ngày lưu lượng hợp lệ |",
        "| rainfall_source | str | — | Nguồn mưa tháng thực tế đã dùng |",
        "| temperature_source | str | — | Nguồn nhiệt độ tháng thực tế đã dùng |",
        "| quality_status | str | — | Cờ: OK / LOW_COVERAGE / NO_RAINFALL / RAINFALL_MONTHLY_ONLY / RAINFALL_DAILY_MISMATCH / NO_TEMPERATURE |",
        "",
        "## Quy ước",
        "",
        "- **Mưa tháng:** Sử dụng sản phẩm mưa tháng; tổng mưa ngày chỉ dùng để đối chiếu.",
        "- **Nhiệt độ tháng:** Trung bình tháng từ nguồn ghi ở cột `temperature_source`.",
        "- **Lưu lượng tháng:** Trung bình các bản ghi ngày có trạng thái VALID hoặc CORRECTED.",
        "  Đây là trung bình các giá trị công bố, không phải lưu lượng trung bình thực đo",
        "  vì chưa xác minh ý nghĩa thời gian của bản ghi.",
        "- **Không sử dụng 0 thay cho giá trị thiếu.**",
        "- **Không dịch thời gian khi ghép dữ liệu.**",
        "- **Không cộng m³/s để tạo tổng lượng nước.**",
        "",
        "## Tháng LOW_COVERAGE",
        "",
        f"- Tháng có < {COVERAGE_THRESHOLD*100:.0f}% ngày lưu lượng đủ ĐK được gắn cờ LOW_COVERAGE.",
        "- Không tự động đưa vào phân tích tương quan chính.",
        "",
    ]

    path = QA_DIR / "data_dictionary.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"  → {path}")


def main():
    print("=" * 60)
    print("GATE 4 — Tích hợp dữ liệu khí tượng–thủy văn")
    print("=" * 60)

    # Đọc dữ liệu
    print("\n[1/5] Đọc dữ liệu đầu vào...")
    hydro = load_hydrology()
    print(f"  Thủy văn: {len(hydro)} dòng")

    rain_monthly = load_rainfall_monthly()
    rain_daily = load_rainfall_daily()
    temp_monthly = load_temperature_monthly()
    temp_daily = load_temperature_daily()

    # Bảng ngày
    print("\n[2/5] Xây dựng bảng ngày...")
    daily_df = build_daily_table(hydro, rain_daily, temp_daily)
    daily_path = PROC_DIR / "hydromet_daily.csv"
    daily_df.to_csv(daily_path, index=False, encoding="utf-8-sig")
    print(f"  → {daily_path} ({len(daily_df)} dòng)")

    # Bảng tháng
    print("\n[3/5] Xây dựng bảng tháng...")
    monthly_df = build_monthly_table(daily_df, rain_monthly, temp_monthly, hydro)
    monthly_path = PROC_DIR / "hydromet_monthly.csv"
    monthly_df.to_csv(monthly_path, index=False, encoding="utf-8-sig")
    print(f"  → {monthly_path} ({len(monthly_df)} dòng)")

    # Kiểm tra
    print("\n[4/5] Kiểm tra tích hợp...")
    qa_df = build_integration_qa(daily_df, monthly_df)
    qa_path = PROC_DIR / "integration_qa.csv"
    qa_df.to_csv(qa_path, index=False, encoding="utf-8-sig")
    print(f"  → {qa_path}")
    for _, row in qa_df.iterrows():
        status_icon = "✅" if row["status"] == "OK" else "⚠️"
        print(f"  {status_icon} {row['check']}: {row['actual']} "
              f"(kỳ vọng {row['expected']})")

    # Từ điển dữ liệu
    print("\n[5/5] Viết từ điển dữ liệu...")
    write_data_dictionary()

    n_fail = int((qa_df["status"] == "FAIL").sum())
    if n_fail > 0:
        print(f"\n❌ GATE 4 KHÔNG ĐẠT: {n_fail} kiểm tra FAIL.")
        print("  → Xem data/processed/integration_qa.csv")
        return 1

    print("\n✅ GATE 4 hoàn thành.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
