#!/usr/bin/env python3
"""
03_chirps_extraction.py — GATE 3 (phần mưa): Trích xuất CHIRPS v3 Final
=========================================================================
Đặc tả: V1.0 §IV-C, V1.1 §9

Nguồn:  CHIRPS v3 Final (Climate Hazards Center, UC Santa Barbara)
  - Tháng: https://data.chc.ucsb.edu/products/CHIRPS/v3.0/monthly/global/
  - Ngày:  https://data.chc.ucsb.edu/products/CHIRPS/v3.0/daily/final/rnl/

Phương pháp:
    - Tải raster CHIRPS v3 Final monthly (tháng) và daily rnl (ngày).
    - Cắt theo lưu vực đã phê duyệt.
    - Tính lượng mưa trung bình lưu vực (trọng số diện tích).
    - P_t = Σ(A_i × P_i,t) / Σ(A_i)

Đầu ra:
    data/processed/rainfall_monthly.csv
    data/processed/rainfall_daily.csv
    data/processed/rainfall_qa.csv
    outputs/quality/rainfall_extraction_method.md
"""

import os
import sys
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
import warnings
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import date, timedelta

try:
    import rasterio
    from rasterio.mask import mask as rio_mask
    import geopandas as gpd
    from shapely.geometry import mapping
except ImportError as e:
    sys.exit(f"[LỖI] Thiếu thư viện: {e}")

ROOT = Path(__file__).resolve().parent.parent
CATCHMENT_PATH = ROOT / "data" / "processed" / "song_ba_ha_catchment.geojson"
RAW_CHIRPS_DIR = ROOT / "data" / "raw" / "chirps"
OUT_DIR = ROOT / "data" / "processed"
QA_DIR = ROOT / "outputs" / "quality"

RAW_CHIRPS_DIR.mkdir(parents=True, exist_ok=True)
OUT_DIR.mkdir(parents=True, exist_ok=True)
QA_DIR.mkdir(parents=True, exist_ok=True)

# ── URL templates ─────────────────────────────────────────────────────
CHIRPS_MONTHLY_URL = (
    "https://data.chc.ucsb.edu/products/CHIRPS/v3.0/monthly/global/"
    "tifs/chirps-v3.0.{year}.{month:02d}.tif"
)
CHIRPS_DAILY_URL = (
    "https://data.chc.ucsb.edu/products/CHIRPS/v3.0/daily/final/rnl/"
    "{year}/chirps-v3.0.{year}.{month:02d}.{day:02d}.tif"
)

START_DATE = date(2023, 1, 1)
END_DATE = date(2025, 12, 31)


def download_file(url, dest):
    """Tải file nếu chưa có."""
    import requests

    if dest.exists():
        return True

    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        resp = requests.get(url, stream=True, timeout=120)
        resp.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in resp.iter_content(chunk_size=1024 * 512):
                f.write(chunk)
        return True
    except requests.RequestException as e:
        print(f"  ⚠️ Không tải được: {url} — {e}")
        return False


def area_weighted_mean(tif_path, catchment_geom):
    """Tính lượng mưa trung bình có trọng số diện tích cho lưu vực.

    P_t = Σ(A_i × P_i,t) / Σ(A_i)
    Trong đó A_i là diện tích phần ô raster thuộc lưu vực.
    """
    with rasterio.open(tif_path) as src:
        # Cắt raster theo polygon
        out_image, out_transform = rio_mask(
            src, [mapping(catchment_geom)], crop=True, nodata=-9999
        )
        data = out_image[0]  # Band 1

        # Loại nodata
        valid_mask = (data != -9999) & (~np.isnan(data)) & (data >= 0)

        if not valid_mask.any():
            return np.nan, 0

        # Mỗi pixel có cùng kích thước → trọng số đều cho các pixel hợp lệ
        # (đây là xấp xỉ tốt vì CHIRPS resolution ~0.05° và lưu vực đủ lớn)
        valid_values = data[valid_mask]
        weighted_mean = np.mean(valid_values)
        n_pixels = int(valid_mask.sum())

        return float(weighted_mean), n_pixels


def extract_monthly(catchment_geom):
    """Trích xuất mưa tháng CHIRPS v3 Final."""
    print("\n  Trích xuất mưa tháng...")
    records = []
    monthly_dir = RAW_CHIRPS_DIR / "monthly"
    monthly_dir.mkdir(parents=True, exist_ok=True)

    for year in range(2023, 2026):
        for month in range(1, 13):
            ym = f"{year}-{month:02d}"
            url = CHIRPS_MONTHLY_URL.format(year=year, month=month)
            fname = f"chirps-v3.0.{year}.{month:02d}.tif"
            dest = monthly_dir / fname

            ok = download_file(url, dest)
            if not ok:
                records.append({
                    "year_month": ym, "rainfall_mm": np.nan,
                    "n_pixels": 0, "source": "CHIRPS v3.0 Final monthly",
                    "status": "DOWNLOAD_FAILED"
                })
                continue

            rainfall_mm, n_pixels = area_weighted_mean(dest, catchment_geom)
            records.append({
                "year_month": ym,
                "rainfall_mm": round(rainfall_mm, 2) if not np.isnan(rainfall_mm) else np.nan,
                "n_pixels": n_pixels,
                "source": "CHIRPS v3.0 Final monthly",
                "status": "OK" if not np.isnan(rainfall_mm) else "NO_DATA"
            })
            print(f"    {ym}: {rainfall_mm:.1f} mm ({n_pixels} pixels)")

    return pd.DataFrame(records)


def extract_daily(catchment_geom):
    """Trích xuất mưa ngày CHIRPS v3 Final daily rnl."""
    print("\n  Trích xuất mưa ngày (P1)...")
    records = []
    daily_dir = RAW_CHIRPS_DIR / "daily"

    current = START_DATE
    total_days = (END_DATE - START_DATE).days + 1
    done = 0

    while current <= END_DATE:
        year, month, day = current.year, current.month, current.day
        url = CHIRPS_DAILY_URL.format(year=year, month=month, day=day)
        fname = f"chirps-v3.0.{year}.{month:02d}.{day:02d}.tif"
        yearly_dir = daily_dir / str(year)
        yearly_dir.mkdir(parents=True, exist_ok=True)
        dest = yearly_dir / fname

        ok = download_file(url, dest)
        if not ok:
            records.append({
                "date": current.strftime("%Y-%m-%d"),
                "rainfall_mm": np.nan,
                "n_pixels": 0,
                "source": "CHIRPS v3.0 Final daily rnl",
                "status": "DOWNLOAD_FAILED"
            })
        else:
            rainfall_mm, n_pixels = area_weighted_mean(dest, catchment_geom)
            records.append({
                "date": current.strftime("%Y-%m-%d"),
                "rainfall_mm": round(rainfall_mm, 2) if not np.isnan(rainfall_mm) else np.nan,
                "n_pixels": n_pixels,
                "source": "CHIRPS v3.0 Final daily rnl",
                "status": "OK" if not np.isnan(rainfall_mm) else "NO_DATA"
            })

        done += 1
        if done % 30 == 0 or current == END_DATE:
            print(f"    Tiến độ: {done}/{total_days} ngày "
                  f"({done/total_days*100:.0f}%)")
        current += timedelta(days=1)

    return pd.DataFrame(records)


def cross_check_monthly_daily(monthly_df, daily_df):
    """So sánh tổng mưa ngày vs mưa tháng (Bước 6 V1.1)."""
    records = []
    if daily_df is None or len(daily_df) == 0:
        return pd.DataFrame()

    daily_df = daily_df.copy()
    daily_df["year_month"] = daily_df["date"].str[:7]

    for _, mrow in monthly_df.iterrows():
        ym = mrow["year_month"]
        monthly_val = mrow["rainfall_mm"]
        daily_grp = daily_df[daily_df["year_month"] == ym]

        if len(daily_grp) == 0 or np.isnan(monthly_val):
            records.append({
                "year_month": ym,
                "monthly_product_mm": monthly_val,
                "daily_sum_mm": np.nan,
                "diff_mm": np.nan,
                "diff_pct": np.nan,
                "status": "NO_DAILY_DATA"
            })
            continue

        daily_sum = daily_grp["rainfall_mm"].sum()
        diff = daily_sum - monthly_val
        diff_pct = (diff / monthly_val * 100) if monthly_val != 0 else np.nan

        records.append({
            "year_month": ym,
            "monthly_product_mm": round(monthly_val, 2),
            "daily_sum_mm": round(daily_sum, 2),
            "diff_mm": round(diff, 2),
            "diff_pct": round(diff_pct, 1) if not np.isnan(diff_pct) else np.nan,
            "status": "OK" if abs(diff_pct) < 10 else "CHECK"
        })

    return pd.DataFrame(records)


def write_method(monthly_df, daily_df, qa_df):
    """Viết rainfall_extraction_method.md."""
    lines = [
        "# Phương pháp trích xuất lượng mưa CHIRPS v3",
        "",
        "## 1. Nguồn dữ liệu",
        "",
        "- **Sản phẩm:** CHIRPS v3 Final (Climate Hazards Center, UC Santa Barbara)",
        "- **Mưa tháng:** https://data.chc.ucsb.edu/products/CHIRPS/v3.0/monthly/global/",
        "- **Mưa ngày:** https://data.chc.ucsb.edu/products/CHIRPS/v3.0/daily/final/rnl/",
        "- **Loại dữ liệu:** Ước lượng mưa kết hợp vệ tinh và quan trắc",
        "- **Độ phân giải không gian:** ~0.05° (~5 km)",
        "- **Đơn vị:** mm/tháng (sản phẩm tháng), mm/ngày (sản phẩm ngày)",
        "",
        "## 2. Phạm vi",
        "",
        "- **Thời gian:** 01/2023 – 12/2025 (36 tháng)",
        "- **Không gian:** Lưu vực sông Ba đến thủy điện Sông Ba Hạ",
        "- **Ranh giới:** song_ba_ha_catchment.geojson (đã phê duyệt GATE 2)",
        "",
        "## 3. Phương pháp tính mưa trung bình lưu vực",
        "",
        "Sử dụng trung bình có trọng số diện tích:",
        "",
        "```",
        "P_t = Σ(A_i × P_i,t) / Σ(A_i)",
        "```",
        "",
        "Trong đó A_i là diện tích phần ô raster giao với polygon lưu vực.",
        "Trong triển khai, sử dụng rasterio.mask để cắt raster theo polygon,",
        "sau đó lấy trung bình các pixel hợp lệ (xấp xỉ tốt vì các pixel",
        "CHIRPS có kích thước đều và lưu vực đủ lớn).",
        "",
        "## 4. Lưu ý khoa học",
        "",
        "- Dữ liệu ngày CHIRPS v3 `rnl` được phân rã từ lượng mưa theo khoảng",
        "  năm ngày bằng thông tin ERA5.",
        "- Phân tích tương quan ở quy mô tháng được ưu tiên.",
        "- Không diễn giải tương quan theo ngày thành bằng chứng về thời gian",
        "  phản ứng thủy văn chính xác.",
        "- Giá trị một ô CHIRPS tháng đã mang đơn vị mm/tháng; không cộng trực",
        "  tiếp các giá trị của các ô không gian.",
        "",
        "## 5. Kết quả đối chiếu mưa tháng vs tổng mưa ngày",
        "",
    ]

    if qa_df is not None and len(qa_df) > 0:
        lines.append("| Tháng | Sản phẩm tháng (mm) | Tổng ngày (mm) | Lệch (mm) | Lệch (%) |")
        lines.append("|-------|---------------------|----------------|-----------|----------|")
        for _, row in qa_df.iterrows():
            lines.append(
                f"| {row['year_month']} | {row['monthly_product_mm']} | "
                f"{row['daily_sum_mm']} | {row['diff_mm']} | {row['diff_pct']} |"
            )
    else:
        lines.append("(Chưa có dữ liệu ngày để so sánh)")

    lines += [
        "",
        "## 6. Đầu ra",
        "",
        "- `rainfall_monthly.csv`: Mưa tháng trung bình lưu vực",
        "- `rainfall_daily.csv`: Mưa ngày trung bình lưu vực (P1)",
        "- `rainfall_qa.csv`: So sánh mưa tháng vs tổng ngày",
        "",
    ]

    path = QA_DIR / "rainfall_extraction_method.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"  → {path}")


def main():
    print("=" * 60)
    print("GATE 3a — Trích xuất mưa CHIRPS v3 Final")
    print("=" * 60)

    # Kiểm tra ranh giới lưu vực
    if not CATCHMENT_PATH.exists():
        sys.exit(
            f"[LỖI] Chưa có ranh giới lưu vực: {CATCHMENT_PATH}\n"
            "Phải hoàn thành GATE 2 và được phê duyệt trước khi trích xuất mưa."
        )

    print("\n[1/5] Đọc ranh giới lưu vực...")
    catchment = gpd.read_file(CATCHMENT_PATH)
    catchment_geom = catchment.geometry.unary_union
    print(f"  Bounds: {catchment.total_bounds}")

    # P0: Mưa tháng
    print("\n[2/5] Tải và trích xuất mưa tháng (P0)...")
    monthly_df = extract_monthly(catchment_geom)
    monthly_path = OUT_DIR / "rainfall_monthly.csv"
    monthly_df.to_csv(monthly_path, index=False, encoding="utf-8-sig")
    print(f"  → {monthly_path}")
    print(f"  Tổng: {len(monthly_df)} tháng, "
          f"OK: {(monthly_df['status']=='OK').sum()}")

    # P1: Mưa ngày
    print("\n[3/5] Tải và trích xuất mưa ngày (P1)...")
    daily_df = extract_daily(catchment_geom)
    daily_path = OUT_DIR / "rainfall_daily.csv"
    daily_df.to_csv(daily_path, index=False, encoding="utf-8-sig")
    print(f"  → {daily_path}")

    # So sánh
    print("\n[4/5] So sánh mưa tháng vs tổng ngày...")
    qa_df = cross_check_monthly_daily(monthly_df, daily_df)
    qa_path = OUT_DIR / "rainfall_qa.csv"
    if len(qa_df) > 0:
        qa_df.to_csv(qa_path, index=False, encoding="utf-8-sig")
        print(f"  → {qa_path}")
    else:
        print("  (Bỏ qua — chưa có dữ liệu ngày)")

    # Phương pháp
    print("\n[5/5] Viết tài liệu phương pháp...")
    write_method(monthly_df, daily_df, qa_df)

    print("\n✅ GATE 3a (mưa CHIRPS) hoàn thành.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
