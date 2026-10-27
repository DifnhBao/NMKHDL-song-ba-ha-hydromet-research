#!/usr/bin/env python3
"""
01_hydrology_qa.py — GATE 1: Kiểm định 1.096 ngày dữ liệu thủy văn
=====================================================================
Đặc tả: V1.0 §IV-A, V1.1 §4–6

Đầu vào:
    data/raw/hydrology/song_ba_ha_202301_to_202512.csv

Đầu ra:
    data/processed/hydrology_clean.csv
    data/processed/hydrology_exceptions.csv
    data/processed/hydrology_qa_summary.csv
    outputs/quality/hydrology_quality_notes.md

Quy tắc:
    - Không sửa, xóa, nội suy dữ liệu gốc.
    - Cờ chất lượng riêng cho từng biến (VALID, SUSPECT, MISSING,
      INVALID_CONFIRMED, CORRECTED).
    - Danh sách đối chiếu bắt buộc: 14/01/2023, 19/02/2023, 21/01/2023,
      31/05/2023, 03/02/2024, 09/04/2024, 09/09/2024, 19–20/11/2025.
"""

import os
import sys
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
import pandas as pd
import numpy as np
from pathlib import Path

# ── Đường dẫn ─────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
RAW_CSV = ROOT / "data" / "raw" / "hydrology" / "song_ba_ha_202301_to_202512.csv"
OUT_DIR = ROOT / "data" / "processed"
QA_DIR = ROOT / "outputs" / "quality"

OUT_DIR.mkdir(parents=True, exist_ok=True)
QA_DIR.mkdir(parents=True, exist_ok=True)

# ── Thông số kỹ thuật công trình Sông Ba Hạ ────────────────────────────
MAX_POWER_MW = 220          # Công suất thiết kế (MW)
NORMAL_POOL_M = 111.5       # Mực nước dâng bình thường (m)
DEAD_POOL_M = 95.0          # Mực nước chết (m)
MIN_DOWNSTREAM_M = 30.0     # Mực nước hạ lưu hợp lý tối thiểu (m)
INFLOW_SPIKE_FACTOR = 5.0   # Hệ số phát hiện lưu lượng đột biến so với lân cận
CONSTANT_RUN_DAYS = 14      # Ngưỡng chuỗi giá trị không đổi
COVERAGE_THRESHOLD = 0.90   # Ngưỡng tỷ lệ dữ liệu hợp lệ trong tháng

# ── Danh sách ngày bắt buộc đối chiếu ──────────────────────────────────
MANDATORY_CHECK_DATES = [
    "2023-01-14",  # Mực nước thượng lưu 140,30 m
    "2023-02-19",  # Nghi đảo giá trị mực nước thượng/hạ lưu
    "2023-01-21",  # Nhiều trường thủy văn bằng 0 nhưng sản lượng điện dương
    "2023-05-31",  # Mực nước bất thường
    "2024-02-03",  # Công suất cực đại 707 MW
    "2024-04-09",  # Nghi đảo giá trị mực nước
    "2024-09-09",  # Mực nước bất thường
    "2025-11-19",  # Lưu lượng về hồ rất lớn
    "2025-11-20",  # Lưu lượng về hồ rất lớn
]


def load_data():
    """Đọc CSV gốc, kiểm tra đầu vào."""
    if not RAW_CSV.exists():
        sys.exit(f"[LỖI] Không tìm thấy tệp: {RAW_CSV}")
    df = pd.read_csv(RAW_CSV)
    df["date"] = pd.to_datetime(df["date"])
    return df


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 5.1 Kiểm tra cấu trúc
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def check_structure(df):
    """Kiểm tra cấu trúc: khoảng ngày, số ngày, trùng lặp, liên tục."""
    issues = []

    # Khoảng ngày đúng
    start, end = pd.Timestamp("2023-01-01"), pd.Timestamp("2025-12-31")
    if df["date"].min() != start or df["date"].max() != end:
        issues.append(f"Khoảng ngày: {df['date'].min()} – {df['date'].max()}, "
                       f"kỳ vọng {start.date()} – {end.date()}")

    # Đúng 1.096 ngày
    if len(df) != 1096:
        issues.append(f"Số dòng = {len(df)}, kỳ vọng 1.096")

    # Trùng ngày
    dups = df[df["date"].duplicated(keep=False)]
    if len(dups) > 0:
        issues.append(f"Ngày trùng: {sorted(dups['date'].dt.strftime('%Y-%m-%d').unique().tolist())}")

    # Liên tục
    expected = pd.date_range(start, end, freq="D")
    missing_dates = expected.difference(df["date"])
    if len(missing_dates) > 0:
        issues.append(f"Ngày thiếu: {[d.strftime('%Y-%m-%d') for d in missing_dates]}")

    return issues


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 5.2 Kiểm tra hợp lý + gắn cờ từng biến
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def qa_per_variable(df):
    """Gắn cờ chất lượng riêng cho từng biến, trả về DataFrame có cờ QA."""
    n = len(df)
    exceptions = []  # Danh sách ngoại lệ

    # Khởi tạo cờ
    for col in ["inflow", "upstream_level", "downstream_level", "release",
                "daily_energy", "max_power"]:
        df[f"{col}_quality"] = "VALID"

    # ── inflow_m3s ────────────────────────────────────────────────────
    # Giá trị thiếu (NaN)
    mask_nan = df["inflow_m3s"].isna()
    df.loc[mask_nan, "inflow_quality"] = "MISSING"
    for idx in df.index[mask_nan]:
        exceptions.append({"date": df.loc[idx, "date"], "variable": "inflow_m3s",
                           "value": np.nan, "flag": "MISSING",
                           "reason": "Giá trị NaN"})

    # Giá trị = 0
    mask_zero = (~mask_nan) & (df["inflow_m3s"] == 0)
    df.loc[mask_zero, "inflow_quality"] = "SUSPECT"
    for idx in df.index[mask_zero]:
        exceptions.append({"date": df.loc[idx, "date"], "variable": "inflow_m3s",
                           "value": 0, "flag": "SUSPECT",
                           "reason": "Lưu lượng về hồ bằng 0"})

    # Đột biến: giá trị gấp > INFLOW_SPIKE_FACTOR so với trung vị 7 ngày
    inflow = df["inflow_m3s"].copy()
    rolling_med = inflow.rolling(7, center=True, min_periods=3).median()
    spike_mask = (inflow > 0) & (rolling_med > 0) & (inflow / rolling_med > INFLOW_SPIKE_FACTOR)
    for idx in df.index[spike_mask]:
        if df.loc[idx, "inflow_quality"] == "VALID":
            df.loc[idx, "inflow_quality"] = "SUSPECT"
        exceptions.append({
            "date": df.loc[idx, "date"], "variable": "inflow_m3s",
            "value": df.loc[idx, "inflow_m3s"], "flag": "SUSPECT",
            "reason": f"Lưu lượng đột biến (>{INFLOW_SPIKE_FACTOR}× trung vị 7 ngày = "
                      f"{rolling_med.loc[idx]:.1f})"
        })

    # ── upstream_level_m ──────────────────────────────────────────────
    mask_nan = df["upstream_level_m"].isna()
    df.loc[mask_nan, "upstream_level_quality"] = "MISSING"
    for idx in df.index[mask_nan]:
        exceptions.append({"date": df.loc[idx, "date"], "variable": "upstream_level_m",
                           "value": np.nan, "flag": "MISSING",
                           "reason": "Giá trị NaN"})

    mask_zero = (~mask_nan) & (df["upstream_level_m"] == 0)
    df.loc[mask_zero, "upstream_level_quality"] = "SUSPECT"
    for idx in df.index[mask_zero]:
        exceptions.append({"date": df.loc[idx, "date"], "variable": "upstream_level_m",
                           "value": 0, "flag": "SUSPECT",
                           "reason": "Mực nước thượng lưu bằng 0"})

    # Mực nước ngoài khoảng hợp lý [DEAD_POOL_M - 5, NORMAL_POOL_M + 5]
    up_valid = (~mask_nan) & (~mask_zero)
    mask_extreme = up_valid & (
        (df["upstream_level_m"] > NORMAL_POOL_M + 5) |
        (df["upstream_level_m"] < DEAD_POOL_M - 10)
    )
    for idx in df.index[mask_extreme]:
        df.loc[idx, "upstream_level_quality"] = "SUSPECT"
        exceptions.append({
            "date": df.loc[idx, "date"], "variable": "upstream_level_m",
            "value": df.loc[idx, "upstream_level_m"], "flag": "SUSPECT",
            "reason": f"Mực nước thượng lưu ngoài khoảng [{DEAD_POOL_M-10}, {NORMAL_POOL_M+5}] m"
        })

    # Biến động đột ngột mực nước (>5 m/ngày)
    up_diff = df["upstream_level_m"].diff().abs()
    mask_jump = up_valid & (up_diff > 5.0)
    for idx in df.index[mask_jump]:
        if df.loc[idx, "upstream_level_quality"] == "VALID":
            df.loc[idx, "upstream_level_quality"] = "SUSPECT"
        exceptions.append({
            "date": df.loc[idx, "date"], "variable": "upstream_level_m",
            "value": df.loc[idx, "upstream_level_m"], "flag": "SUSPECT",
            "reason": f"Biến động mực nước đột ngột: {up_diff.loc[idx]:.2f} m/ngày"
        })

    # ── downstream_level_m ────────────────────────────────────────────
    mask_nan = df["downstream_level_m"].isna()
    df.loc[mask_nan, "downstream_level_quality"] = "MISSING"

    mask_zero = (~mask_nan) & (df["downstream_level_m"] == 0)
    df.loc[mask_zero, "downstream_level_quality"] = "SUSPECT"
    for idx in df.index[mask_zero]:
        exceptions.append({"date": df.loc[idx, "date"], "variable": "downstream_level_m",
                           "value": 0, "flag": "SUSPECT",
                           "reason": "Mực nước hạ lưu bằng 0"})

    # ── Kiểm tra đảo cột: upstream < downstream ──────────────────────
    both_valid = (
        (df["upstream_level_m"] > 0) & (df["downstream_level_m"] > 0) &
        df["upstream_level_m"].notna() & df["downstream_level_m"].notna()
    )
    mask_swap = both_valid & (df["upstream_level_m"] < df["downstream_level_m"])
    for idx in df.index[mask_swap]:
        df.loc[idx, "upstream_level_quality"] = "SUSPECT"
        df.loc[idx, "downstream_level_quality"] = "SUSPECT"
        exceptions.append({
            "date": df.loc[idx, "date"], "variable": "upstream_level_m, downstream_level_m",
            "value": f"up={df.loc[idx, 'upstream_level_m']}, down={df.loc[idx, 'downstream_level_m']}",
            "flag": "SUSPECT",
            "reason": "Mực nước thượng lưu nhỏ hơn hạ lưu — nghi đảo cột, chưa có xác minh nguồn độc lập"
        })

    # ── max_power_mw ──────────────────────────────────────────────────
    mask_power = df["max_power_mw"] > MAX_POWER_MW
    for idx in df.index[mask_power]:
        df.loc[idx, "max_power_quality"] = "INVALID_CONFIRMED"
        exceptions.append({
            "date": df.loc[idx, "date"], "variable": "max_power_mw",
            "value": df.loc[idx, "max_power_mw"], "flag": "INVALID_CONFIRMED",
            "reason": f"Công suất {df.loc[idx, 'max_power_mw']} MW vượt thiết kế {MAX_POWER_MW} MW"
        })

    mask_zero_power = df["max_power_mw"] == 0
    for idx in df.index[mask_zero_power]:
        df.loc[idx, "max_power_quality"] = "SUSPECT"
        exceptions.append({
            "date": df.loc[idx, "date"], "variable": "max_power_mw",
            "value": 0, "flag": "SUSPECT",
            "reason": "Công suất bằng 0"
        })

    # ── release_m3s ───────────────────────────────────────────────────
    mask_nan = df["release_m3s"].isna()
    df.loc[mask_nan, "release_quality"] = "MISSING"

    # ── daily_energy_kwh ──────────────────────────────────────────────
    mask_nan = df["daily_energy_kwh"].isna()
    df.loc[mask_nan, "daily_energy_quality"] = "MISSING"

    # ── Chuỗi giá trị không đổi ≥ 14 ngày ────────────────────────────
    for col in ["inflow_m3s", "upstream_level_m"]:
        vals = df[col].values
        run_start = 0
        for i in range(1, n + 1):
            if i < n and vals[i] == vals[run_start]:
                continue
            run_len = i - run_start
            if run_len >= CONSTANT_RUN_DAYS and not np.isnan(vals[run_start]):
                for j in range(run_start, i):
                    qcol = col.replace("_m3s", "").replace("_m", "") + "_quality"
                    if col == "inflow_m3s":
                        qcol = "inflow_quality"
                    elif col == "upstream_level_m":
                        qcol = "upstream_level_quality"
                    if df.loc[j, qcol] == "VALID":
                        df.loc[j, qcol] = "SUSPECT"
                exceptions.append({
                    "date": f"{df.loc[run_start, 'date'].strftime('%Y-%m-%d')} đến "
                            f"{df.loc[i-1, 'date'].strftime('%Y-%m-%d')}",
                    "variable": col, "value": vals[run_start],
                    "flag": "SUSPECT",
                    "reason": f"Chuỗi giá trị không đổi {run_len} ngày liên tiếp"
                })
            run_start = i

    # ── Kiểm tra ngày bắt buộc ────────────────────────────────────────
    for d_str in MANDATORY_CHECK_DATES:
        d = pd.Timestamp(d_str)
        row = df[df["date"] == d]
        if row.empty:
            exceptions.append({
                "date": d, "variable": "all", "value": "N/A",
                "flag": "MISSING", "reason": f"Ngày bắt buộc kiểm tra {d_str} không có trong dữ liệu"
            })
            continue
        r = row.iloc[0]

        # 2023-01-14: Mực nước thượng lưu 140,30 m
        if d_str == "2023-01-14" and r["upstream_level_m"] == 140.30:
            df.loc[row.index[0], "upstream_level_quality"] = "SUSPECT"
            exceptions.append({
                "date": d, "variable": "upstream_level_m",
                "value": 140.30, "flag": "SUSPECT",
                "reason": "Mực nước 140,30 m vượt xa mực nước dâng bình thường 111,5 m — "
                          "có thể lỗi nhập liệu hoặc đảo chữ số"
            })

        # 2023-02-19: Nghi đảo cột
        if d_str == "2023-02-19":
            if r["upstream_level_m"] < r["downstream_level_m"]:
                # Đã xử lý ở phần kiểm tra đảo cột
                pass

        # 2023-01-21: Nhiều biến bằng 0 nhưng sản lượng dương
        if d_str == "2023-01-21":
            if (r["inflow_m3s"] == 0 and r["upstream_level_m"] == 0 and
                    r["daily_energy_kwh"] > 0):
                exceptions.append({
                    "date": d, "variable": "inflow_m3s, upstream_level_m",
                    "value": f"inflow=0, up_level=0, energy={r['daily_energy_kwh']}",
                    "flag": "SUSPECT",
                    "reason": "Nhiều biến thủy văn bằng 0 nhưng sản lượng điện dương — "
                              "có thể thiếu dữ liệu"
                })

        # 2023-05-31: Mực nước bất thường
        if d_str == "2023-05-31":
            if r["downstream_level_m"] == 0:
                exceptions.append({
                    "date": d, "variable": "downstream_level_m",
                    "value": 0, "flag": "SUSPECT",
                    "reason": "Mực nước hạ lưu bằng 0 — bất thường; "
                              "mực nước thượng lưu cũng bất thường (38,4 m < mực nước chết)"
                })

        # 2024-02-03: Công suất 707 MW
        if d_str == "2024-02-03":
            # Đã xử lý ở phần max_power
            pass

        # 2024-04-09: Nghi đảo cột
        if d_str == "2024-04-09":
            # Đã xử lý ở phần kiểm tra đảo cột
            pass

        # 2024-09-09: Mực nước bất thường
        if d_str == "2024-09-09":
            if r["upstream_level_m"] < DEAD_POOL_M - 50:
                df.loc[row.index[0], "upstream_level_quality"] = "SUSPECT"
                exceptions.append({
                    "date": d, "variable": "upstream_level_m",
                    "value": r["upstream_level_m"], "flag": "SUSPECT",
                    "reason": f"Mực nước thượng lưu {r['upstream_level_m']} m — "
                              "bất thường, ngoài phạm vi vận hành"
                })

        # 2025-11-19 và 2025-11-20: Lưu lượng rất lớn
        if d_str in ["2025-11-19", "2025-11-20"]:
            # V1.1 §6: SUSPECT phải được gắn vào chính biến, không chỉ ghi vào
            # danh sách ngoại lệ — nếu không, giá trị vẫn bị coi là VALID khi
            # tổng hợp và không loại được khỏi phân tích chính/độ nhạy.
            df.loc[row.index[0], "inflow_quality"] = "SUSPECT"
            exceptions.append({
                "date": d, "variable": "inflow_m3s",
                "value": r["inflow_m3s"], "flag": "SUSPECT",
                "reason": f"Lưu lượng cực lớn {r['inflow_m3s']} m³/s — cần kiểm tra "
                          "định nghĩa và nguồn; không loại bỏ chỉ vì giá trị cao. "
                          "Có thể liên quan sự kiện lũ lớn tháng 11/2025"
            })

    return df, exceptions


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 5.3 Kiểm tra sản lượng điện ngày vs lũy kế
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def check_energy_consistency(df, exceptions):
    """Kiểm tra sự thống nhất giữa sản lượng ngày và lũy kế tháng."""
    energy_issues = []
    for ym, grp in df.groupby(df["date"].dt.to_period("M")):
        grp_sorted = grp.sort_values("date")
        daily_sum = grp_sorted["daily_energy_kwh"].sum()
        cum_max = grp_sorted["month_cumulative_kwh"].iloc[-1]
        diff = abs(daily_sum - cum_max)
        if diff > 1.0:  # Cho phép sai số làm tròn
            energy_issues.append({
                "year_month": str(ym),
                "daily_sum_kwh": daily_sum,
                "cumulative_end_kwh": cum_max,
                "diff_kwh": diff
            })
            exceptions.append({
                "date": str(ym), "variable": "daily_energy_kwh vs month_cumulative_kwh",
                "value": f"sum={daily_sum:.1f}, cum={cum_max:.1f}, diff={diff:.1f}",
                "flag": "SUSPECT",
                "reason": "Sai lệch giữa tổng sản lượng ngày và lũy kế cuối tháng"
            })
    return energy_issues


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Tổng hợp QA theo tháng
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def monthly_qa_summary(df):
    """Tạo bảng QA theo tháng với cờ LOW_COVERAGE."""
    records = []
    for ym, grp in df.groupby(df["date"].dt.to_period("M")):
        n_days = len(grp)
        expected = ym.days_in_month

        inflow_valid = (grp["inflow_quality"].isin(["VALID", "CORRECTED"])).sum()
        level_valid = (grp["upstream_level_quality"].isin(["VALID", "CORRECTED"])).sum()
        inflow_coverage = inflow_valid / n_days if n_days > 0 else 0

        flags = []
        if inflow_coverage < COVERAGE_THRESHOLD:
            flags.append("LOW_COVERAGE")

        n_suspect = (grp["inflow_quality"] == "SUSPECT").sum()
        n_invalid = (grp["inflow_quality"] == "INVALID_CONFIRMED").sum()
        n_missing = (grp["inflow_quality"] == "MISSING").sum()

        records.append({
            "year_month": str(ym),
            "n_days": n_days,
            "expected_days": expected,
            "inflow_valid_days": inflow_valid,
            "inflow_suspect_days": n_suspect,
            "inflow_invalid_days": n_invalid,
            "inflow_missing_days": n_missing,
            "inflow_coverage_pct": round(inflow_coverage * 100, 1),
            "level_valid_days": level_valid,
            "quality_status": "|".join(flags) if flags else "OK",
        })
    return pd.DataFrame(records)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Tạo ghi chú chất lượng Markdown
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def write_quality_notes(struct_issues, exceptions_df, qa_summary, energy_issues):
    """Viết hydrology_quality_notes.md."""
    lines = [
        "# Báo cáo kiểm tra chất lượng dữ liệu thủy văn",
        "",
        "**Nguồn dữ liệu:** Website Sông Ba Hạ (sbh.vn)",
        "**Giai đoạn:** 01/01/2023 – 31/12/2025 (1.096 ngày lịch)",
        "**Script:** `scripts/01_hydrology_qa.py`",
        "",
        "## 1. Kiểm tra cấu trúc",
        "",
    ]
    if struct_issues:
        for issue in struct_issues:
            lines.append(f"- ⚠️ {issue}")
    else:
        lines.append("- ✅ Đúng 1.096 ngày, 01/01/2023 – 31/12/2025, không trùng, liên tục.")
    lines.append("")

    lines += [
        "## 2. Tổng hợp ngoại lệ",
        "",
        f"- Tổng số bản ghi ngoại lệ: **{len(exceptions_df)}**",
    ]

    if len(exceptions_df) > 0:
        flag_counts = exceptions_df["flag"].value_counts()
        for flag, count in flag_counts.items():
            lines.append(f"  - {flag}: {count}")
    lines.append("")

    lines += [
        "## 3. Danh sách ngày bắt buộc đối chiếu",
        "",
        "| Ngày | Vấn đề | Cờ |",
        "|---|---|---|",
    ]
    mandatory_exc = exceptions_df[exceptions_df["date"].astype(str).isin(MANDATORY_CHECK_DATES)]
    if len(mandatory_exc) > 0:
        for _, row in mandatory_exc.iterrows():
            lines.append(f"| {row['date']} | {row['reason'][:80]} | {row['flag']} |")
    else:
        lines.append("| (Không phát hiện) | | |")
    lines.append("")

    lines += [
        "## 4. Kiểm tra sản lượng điện",
        "",
    ]
    if energy_issues:
        lines.append(f"- Có {len(energy_issues)} tháng sai lệch tổng ngày vs lũy kế.")
    else:
        lines.append("- ✅ Sản lượng ngày và lũy kế tháng nhất quán.")
    lines.append("")

    lines += [
        "## 5. Trạng thái tháng",
        "",
    ]
    low_cov = qa_summary[qa_summary["quality_status"].str.contains("LOW_COVERAGE")]
    if len(low_cov) > 0:
        lines.append(f"- {len(low_cov)} tháng có LOW_COVERAGE (< {COVERAGE_THRESHOLD*100:.0f}% "
                     "ngày lưu lượng hợp lệ):")
        for _, row in low_cov.iterrows():
            lines.append(f"  - {row['year_month']}: {row['inflow_coverage_pct']}%")
    else:
        lines.append(f"- ✅ Tất cả 36 tháng đạt ≥ {COVERAGE_THRESHOLD*100:.0f}% "
                     "ngày lưu lượng hợp lệ.")
    lines.append("")

    lines += [
        "## 6. Quy tắc xử lý đã áp dụng",
        "",
        "- Không tự động xóa, nội suy hoặc sửa bất kỳ giá trị nào.",
        "- Mỗi biến có cờ chất lượng riêng: VALID, SUSPECT, MISSING, "
        "INVALID_CONFIRMED, CORRECTED.",
        "- Lưu lượng cực lớn 19–20/11/2025 được giữ nguyên và gắn cờ SUSPECT.",
        "- Giá trị bằng 0 không tự thay bằng NaN.",
        "- Dữ liệu gốc không bị thay đổi.",
        "",
        "## 7. Giới hạn",
        "",
        "- Chưa xác minh được ý nghĩa thời gian chính xác của lưu lượng công bố "
        "(trung bình ngày hay giá trị tại thời điểm xác định).",
        "- Các ngày nghi đảo cột (19/02/2023, 09/04/2024) được đánh dấu "
        "SUSPECT vì mới có dấu hiệu up < down, chưa có xác nhận từ nguồn độc lập.",
        "- Công suất 707 MW ngày 03/02/2024 vượt thiết kế; nghi lỗi nhập liệu.",
        "",
    ]

    path = QA_DIR / "hydrology_quality_notes.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"  → {path}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Main
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def main():
    print("=" * 60)
    print("GATE 1 — Kiểm định dữ liệu thủy văn")
    print("=" * 60)

    # 1. Đọc dữ liệu
    print("\n[1/6] Đọc dữ liệu gốc...")
    df = load_data()
    print(f"  Số dòng: {len(df)}, Cột: {list(df.columns)}")

    # 2. Kiểm tra cấu trúc
    print("\n[2/6] Kiểm tra cấu trúc...")
    struct_issues = check_structure(df)
    if struct_issues:
        for iss in struct_issues:
            print(f"  ⚠️  {iss}")
    else:
        print("  ✅ Cấu trúc hợp lệ: 1.096 ngày, không trùng, liên tục.")

    # 3. Kiểm tra hợp lý và gắn cờ
    print("\n[3/6] Kiểm tra hợp lý và gắn cờ QA...")
    df, exceptions = qa_per_variable(df)

    # 4. Kiểm tra sản lượng điện (phải chạy TRƯỚC khi đóng gói exceptions_df,
    #    nếu không các ngoại lệ sản lượng bị mất khỏi hydrology_exceptions.csv)
    print("\n[4/6] Kiểm tra sản lượng điện...")
    energy_issues = check_energy_consistency(df, exceptions)

    exceptions_df = pd.DataFrame(exceptions)
    if len(exceptions_df) > 0:
        exceptions_df["date"] = exceptions_df["date"].astype(str)
    print(f"  Tổng ngoại lệ phát hiện: {len(exceptions_df)}")

    if energy_issues:
        print(f"  ⚠️  {len(energy_issues)} tháng có sai lệch sản lượng")
    else:
        print("  ✅ Sản lượng ngày và lũy kế nhất quán")

    # 5. Tổng hợp QA theo tháng
    print("\n[5/6] Tổng hợp QA theo tháng...")
    qa_summary = monthly_qa_summary(df)

    # 6. Xuất kết quả
    print("\n[6/6] Xuất kết quả...")

    # hydrology_clean.csv — dữ liệu kèm cờ chất lượng
    # V1.1 §4: Giữ cả các trường sản lượng lũy kế để kiểm tra chéo
    clean_cols = [
        "date", "upstream_level_m", "downstream_level_m",
        "inflow_m3s", "release_m3s", "daily_energy_kwh",
        "month_cumulative_kwh", "quarter_cumulative_kwh", "year_cumulative_kwh",
        "max_power_mw", "year_month",
        "inflow_quality", "upstream_level_quality",
        "downstream_level_quality", "release_quality",
        "daily_energy_quality", "max_power_quality"
    ]
    df_clean = df[clean_cols].copy()
    df_clean["date"] = df_clean["date"].dt.strftime("%Y-%m-%d")
    clean_path = OUT_DIR / "hydrology_clean.csv"
    df_clean.to_csv(clean_path, index=False, encoding="utf-8-sig")
    print(f"  → {clean_path}")

    # hydrology_exceptions.csv
    exc_path = OUT_DIR / "hydrology_exceptions.csv"
    if len(exceptions_df) > 0:
        exceptions_df.to_csv(exc_path, index=False, encoding="utf-8-sig")
    else:
        pd.DataFrame(columns=["date", "variable", "value", "flag", "reason"]).to_csv(
            exc_path, index=False, encoding="utf-8-sig")
    print(f"  → {exc_path}")

    # hydrology_qa_summary.csv
    qa_path = OUT_DIR / "hydrology_qa_summary.csv"
    qa_summary.to_csv(qa_path, index=False, encoding="utf-8-sig")
    print(f"  → {qa_path}")

    # hydrology_quality_notes.md
    write_quality_notes(struct_issues, exceptions_df, qa_summary, energy_issues)

    print("\n✅ GATE 1 hoàn thành.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
