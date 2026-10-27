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
import json
import time
import tempfile
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import date, timedelta

# Giới hạn thời gian cho các yêu cầu HTTP của GDAL (/vsicurl/)
os.environ.setdefault("GDAL_HTTP_TIMEOUT", "20")
os.environ.setdefault("GDAL_HTTP_MAX_RETRY", "1")

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
# HTTPS (data.chc.ucsb.edu) là kênh chính; FTP (ftp.chc.ucsb.edu) là kênh
# dự phòng của CÙNG máy chủ CHC, dùng khi HTTPS bị chặn (403 CrowdSec).
CHIRPS_MONTHLY_URL = (
    "https://data.chc.ucsb.edu/products/CHIRPS/v3.0/monthly/global/"
    "tifs/chirps-v3.0.{year}.{month:02d}.tif"
)
CHIRPS_DAILY_URL = (
    "https://data.chc.ucsb.edu/products/CHIRPS/v3.0/daily/final/rnl/"
    "{year}/chirps-v3.0.rnl.{year}.{month:02d}.{day:02d}.tif"
)
CHIRPS_MONTHLY_FTP = (
    "/vsicurl/ftp://ftp.chc.ucsb.edu/pub/org/chc/products/CHIRPS/v3.0/"
    "monthly/global/tifs/chirps-v3.0.{year}.{month:02d}.tif"
)
CHIRPS_DAILY_FTP = (
    "/vsicurl/ftp://ftp.chc.ucsb.edu/pub/org/chc/products/CHIRPS/v3.0/"
    "daily/final/rnl/{year}/chirps-v3.0.rnl.{year}.{month:02d}.{day:02d}.tif"
)


def _monthly_sources(year, month):
    return [
        f"/vsicurl/{CHIRPS_MONTHLY_URL.format(year=year, month=month)}",
        CHIRPS_MONTHLY_FTP.format(year=year, month=month),
    ]


def _daily_sources(year, month, day):
    return [
        f"/vsicurl/{CHIRPS_DAILY_URL.format(year=year, month=month, day=day)}",
        CHIRPS_DAILY_FTP.format(year=year, month=month, day=day),
    ]

START_DATE = date(2023, 1, 1)
END_DATE = date(2025, 12, 31)


def _gate2_status():
    """Đọc trạng thái phê duyệt GATE 2 từ tệp phê duyệt (nếu có)."""
    path = ROOT / "outputs" / "quality" / "gate2_approval.json"
    if not path.exists():
        return "chưa có tệp phê duyệt GATE 2"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return "tệp phê duyệt GATE 2 không đọc được"
    if data.get("approved") is True:
        return f"đã phê duyệt bởi {data.get('approved_by', 'không rõ')}"
    return "chưa được phê duyệt"


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


CHIRPS_NODATA = -9999

# Máy chủ FTP của CHC (cùng nguồn dữ liệu với data.chc.ucsb.edu)
FTP_HOST = "ftp.chc.ucsb.edu"
FTP_ROOT = "/pub/org/chc/products/CHIRPS/v3.0"

# Kênh tải thực tế trong lần chạy (được ghi vào tài liệu phương pháp)
USED_CHANNEL = "HTTPS (data.chc.ucsb.edu)"


def _weighted_mean_by_latitude(data, transform):
    """Xấp xỉ trung bình diện tích theo pixel được chọn và cos(lat).

    Pixel biên sử dụng mặt nạ nhị phân, chưa tính diện tích phần giao pixel.
    """
    valid = (data != CHIRPS_NODATA) & np.isfinite(data) & (data >= 0)
    if not valid.any():
        return np.nan, 0

    rows, cols = np.where(valid)
    # Vĩ độ tâm ô của từng hàng
    lats = transform.f + (rows + 0.5) * transform.e
    weights = np.cos(np.radians(lats))
    values = data[rows, cols].astype("float64")
    return float(np.sum(values * weights) / np.sum(weights)), int(valid.sum())


def area_weighted_mean(tif_path, catchment_geom):
    """Tính trung bình xấp xỉ theo tâm pixel và cos(vĩ độ)."""
    with rasterio.open(tif_path) as src:
        out_image, out_transform = rio_mask(
            src, [mapping(catchment_geom)], crop=True, nodata=CHIRPS_NODATA
        )
        return _weighted_mean_by_latitude(out_image[0], out_transform)


from concurrent.futures import ThreadPoolExecutor


def extract_single_month(args):
    year, month, catchment_geom, monthly_dir = args
    ym = f"{year}-{month:02d}"
    fname = f"chirps-v3.0.{year}.{month:02d}.tif"
    local_crop = monthly_dir / fname

    if local_crop.exists():
        val, n_pix = area_weighted_mean(local_crop, catchment_geom)
        return {
            "year_month": ym, "rainfall_mm": round(val, 2), "n_pixels": n_pix,
            "source": "CHIRPS v3.0 Final monthly", "status": "OK"
        }

    errors = []
    for url in _monthly_sources(year, month):
        try:
            with rasterio.open(url) as src:
                out_img, out_transform = rio_mask(src, [mapping(catchment_geom)],
                                                  crop=True, nodata=CHIRPS_NODATA)
                val, n_pix = _weighted_mean_by_latitude(out_img[0], out_transform)
                if not np.isnan(val):
                    meta = src.meta.copy()
                    meta.update({
                        "driver": "GTiff",
                        "height": out_img.shape[1],
                        "width": out_img.shape[2],
                        "transform": out_transform,
                        "nodata": CHIRPS_NODATA,
                    })
                    with rasterio.open(local_crop, "w", **meta) as dst:
                        dst.write(out_img)
                    return {
                        "year_month": ym, "rainfall_mm": round(val, 2), "n_pixels": n_pix,
                        "source": "CHIRPS v3.0 Final monthly", "status": "OK",
                        "error": "",
                    }
                return {
                    "year_month": ym, "rainfall_mm": np.nan, "n_pixels": 0,
                    "source": "CHIRPS v3.0 Final monthly", "status": "NO_DATA",
                    "error": "",
                }
        except Exception as e:
            errors.append(str(e)[:120])
    return {
        "year_month": ym, "rainfall_mm": np.nan, "n_pixels": 0,
        "source": "CHIRPS v3.0 Final monthly", "status": "DOWNLOAD_FAILED",
        "error": " | ".join(errors)[:240],
    }


def extract_monthly(catchment_geom):
    """Trích xuất mưa tháng CHIRPS v3 Final."""
    print("\n  Trích xuất mưa tháng (P0)...")
    monthly_dir = RAW_CHIRPS_DIR / "monthly"
    monthly_dir.mkdir(parents=True, exist_ok=True)

    tasks = [
        (year, month, catchment_geom, monthly_dir)
        for year in range(2023, 2026)
        for month in range(1, 13)
    ]

    with ThreadPoolExecutor(max_workers=6) as executor:
        records = list(executor.map(extract_single_month, tasks))

    # Sắp xếp lại theo thời gian
    records.sort(key=lambda x: x["year_month"])
    for r in records:
        print(f"    {r['year_month']}: {r['rainfall_mm']} mm ({r['n_pixels']} pixels)")

    return pd.DataFrame(records)


def _crop_and_save(src, catchment_geom, local_crop):
    """Cắt raster theo polygon, lưu bản cắt cục bộ, trả về (giá trị, số pixel)."""
    out_img, out_transform = rio_mask(
        src, [mapping(catchment_geom)], crop=True, nodata=CHIRPS_NODATA
    )
    val, n_pix = _weighted_mean_by_latitude(out_img[0], out_transform)
    if np.isnan(val):
        return np.nan, 0
    local_crop.parent.mkdir(parents=True, exist_ok=True)
    meta = src.meta.copy()
    meta.update({
        "driver": "GTiff",
        "height": out_img.shape[1],
        "width": out_img.shape[2],
        "transform": out_transform,
        "nodata": CHIRPS_NODATA,
    })
    with rasterio.open(local_crop, "w", **meta) as dst:
        dst.write(out_img)
    return val, n_pix


def _download_via_ftp(remote_path, dest, attempts=3):
    """Tải một tệp CHIRPS qua FTP (cùng máy chủ CHC, dùng khi HTTPS bị chặn)."""
    from ftplib import FTP

    last_err = None
    for attempt in range(attempts):
        try:
            ftp = FTP(FTP_HOST, timeout=120)
            ftp.login()
            try:
                with open(dest, "wb") as fh:
                    ftp.retrbinary("RETR " + remote_path, fh.write,
                                   blocksize=1 << 20)
            finally:
                try:
                    ftp.quit()
                except Exception:
                    ftp.close()
            return
        except Exception as exc:
            last_err = exc
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"FTP thất bại sau {attempts} lần: {last_err}")


def extract_single_day(args):
    cur_date, catchment_geom, daily_dir, channel = args
    d_str = cur_date.strftime("%Y-%m-%d")
    year, month, day = cur_date.year, cur_date.month, cur_date.day
    fname = f"chirps-v3.0.rnl.{year}.{month:02d}.{day:02d}.tif"
    local_crop = daily_dir / str(year) / fname

    if local_crop.exists():
        val, n_pix = area_weighted_mean(local_crop, catchment_geom)
        return {
            "date": d_str, "rainfall_mm": round(val, 2) if not np.isnan(val) else np.nan,
            "n_pixels": n_pix, "source": "CHIRPS v3.0 Final daily rnl",
            "status": "OK" if not np.isnan(val) else "NO_DATA", "error": "",
        }

    if channel == "ftp":
        # Tải cả tệp toàn cầu rồi cắt: với FTP, 1 lần RETR nhanh hơn nhiều
        # so với hàng chục lần đọc ranged.
        tmp = Path(tempfile.gettempdir()) / f"chirps_{d_str}.tif"
        remote = (f"{FTP_ROOT}/daily/final/rnl/{year}/{fname}")
        try:
            _download_via_ftp(remote, tmp)
            with rasterio.open(tmp) as src:
                val, n_pix = _crop_and_save(src, catchment_geom, local_crop)
        except Exception as exc:
            return {
                "date": d_str, "rainfall_mm": np.nan, "n_pixels": 0,
                "source": "CHIRPS v3.0 Final daily rnl",
                "status": "DOWNLOAD_FAILED", "error": str(exc)[:200],
            }
        finally:
            try:
                os.remove(tmp)
            except OSError:
                pass
        if np.isnan(val):
            return {
                "date": d_str, "rainfall_mm": np.nan, "n_pixels": 0,
                "source": "CHIRPS v3.0 Final daily rnl",
                "status": "NO_DATA", "error": "",
            }
        return {
            "date": d_str, "rainfall_mm": round(val, 2), "n_pixels": n_pix,
            "source": "CHIRPS v3.0 Final daily rnl", "status": "OK", "error": "",
        }

    # Kênh HTTPS: đọc trực tiếp bằng /vsicurl
    url = f"/vsicurl/{CHIRPS_DAILY_URL.format(year=year, month=month, day=day)}"
    try:
        with rasterio.open(url) as src:
            val, n_pix = _crop_and_save(src, catchment_geom, local_crop)
    except Exception as exc:
        return {
            "date": d_str, "rainfall_mm": np.nan, "n_pixels": 0,
            "source": "CHIRPS v3.0 Final daily rnl",
            "status": "DOWNLOAD_FAILED", "error": str(exc)[:200],
        }
    if np.isnan(val):
        return {
            "date": d_str, "rainfall_mm": np.nan, "n_pixels": 0,
            "source": "CHIRPS v3.0 Final daily rnl",
            "status": "NO_DATA", "error": "",
        }
    return {
        "date": d_str, "rainfall_mm": round(val, 2), "n_pixels": n_pix,
        "source": "CHIRPS v3.0 Final daily rnl", "status": "OK", "error": "",
    }


def _detect_channel():
    """Chọn kênh tải: HTTPS nếu truy cập được, ngược lại FTP (cùng máy chủ CHC)."""
    import requests

    url = CHIRPS_MONTHLY_URL.format(year=2023, month=1)
    try:
        resp = requests.head(url, timeout=20, allow_redirects=True)
        if resp.status_code == 200:
            return "https", "HTTPS (data.chc.ucsb.edu)"
    except Exception:
        pass
    return "ftp", "FTP (ftp.chc.ucsb.edu — cùng máy chủ CHC, HTTPS đang bị chặn)"


def extract_daily(catchment_geom):
    """Trích xuất mưa ngày CHIRPS v3 Final daily rnl."""
    print("\n  Trích xuất mưa ngày (P1)...")
    daily_dir = RAW_CHIRPS_DIR / "daily"
    daily_dir.mkdir(parents=True, exist_ok=True)

    total_days = (END_DATE - START_DATE).days + 1
    dates = [START_DATE + timedelta(days=i) for i in range(total_days)]

    channel, channel_label = _detect_channel()
    print(f"  Kênh tải: {channel_label}")
    global USED_CHANNEL
    USED_CHANNEL = channel_label

    tasks = [(d, catchment_geom, daily_dir, channel) for d in dates]
    records = []
    done = 0
    with ThreadPoolExecutor(max_workers=8) as executor:
        for r in executor.map(extract_single_day, tasks):
            records.append(r)
            done += 1
            if done % 100 == 0 or done == total_days:
                n_ok = sum(1 for x in records if x["status"] == "OK")
                print(f"    Tiến độ: {done}/{total_days} ngày "
                      f"({done/total_days*100:.0f}%), OK: {n_ok}")

    records.sort(key=lambda x: x["date"])
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
                "n_missing_days": np.nan,
                "diff_mm": np.nan,
                "diff_pct": np.nan,
                "status": "NO_MONTHLY_DATA" if np.isnan(monthly_val) else "NO_DAILY_DATA"
            })
            continue

        daily_sum = daily_grp["rainfall_mm"].sum(min_count=1)  # NaN nếu toàn thiếu
        n_missing = int(daily_grp["rainfall_mm"].isna().sum())
        diff = daily_sum - monthly_val
        diff_pct = (diff / monthly_val * 100) if monthly_val != 0 else np.nan

        records.append({
            "year_month": ym,
            "monthly_product_mm": round(monthly_val, 2),
            "daily_sum_mm": round(daily_sum, 2) if pd.notna(daily_sum) else np.nan,
            "n_missing_days": n_missing,
            "diff_mm": round(diff, 2) if pd.notna(diff) else np.nan,
            "diff_pct": round(diff_pct, 1) if pd.notna(diff_pct) else np.nan,
            "status": ("NO_DAILY_DATA" if pd.isna(daily_sum)
                       else "CHECK" if abs(diff_pct) >= 10 else "OK")
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
        f"- **Kênh tải thực tế:** {USED_CHANNEL}",
        "- **Loại dữ liệu:** Ước lượng mưa kết hợp vệ tinh và quan trắc",
        "- **Độ phân giải không gian:** ~0.05° (~5 km)",
        "- **Đơn vị:** mm/tháng (sản phẩm tháng), mm/ngày (sản phẩm ngày)",
        "",
        "## 2. Phạm vi",
        "",
        "- **Thời gian:** 01/2023 – 12/2025 (36 tháng)",
        "- **Không gian:** Lưu vực sông Ba đến thủy điện Sông Ba Hạ",
        f"- **Ranh giới:** song_ba_ha_catchment.geojson "
        f"({_gate2_status()})",
        "",
        "## 3. Phương pháp tính mưa trung bình lưu vực",
        "",
        "Sử dụng trung bình xấp xỉ theo các pixel mask chọn:",
        "",
        "```",
        "P_t ≈ Σ(cos(lat_i) × P_i,t) / Σ(cos(lat_i))",
        "```",
        "",
        "Mask nhị phân lấy pixel được chọn; chưa tính phần diện tích giao polygon tại pixel biên.",
        "Trọng số theo vĩ độ được áp dụng vì diện tích ô 0,05° tỷ lệ với cos(vĩ độ).",
        "Pixel ngoài polygon hoặc có giá trị nodata (-9999) bị loại, không thay bằng 0.",
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
        lines.append("| Tháng | Sản phẩm tháng (mm) | Tổng ngày (mm) | Số ngày thiếu | Lệch (mm) | Lệch (%) | Trạng thái |")
        lines.append("|-------|---------------------|----------------|---------------|-----------|----------|------------|")
        for _, row in qa_df.iterrows():
            lines.append(
                f"| {row['year_month']} | {row['monthly_product_mm']} | "
                f"{row['daily_sum_mm']} | {row.get('n_missing_days', '')} | "
                f"{row['diff_mm']} | {row['diff_pct']} | {row['status']} |"
            )
    else:
        lines.append("(Chưa có dữ liệu ngày để so sánh)")

    lines += [
        "",
        "## 6. Trạng thái dữ liệu",
        "",
        f"- Mưa tháng: {int((monthly_df['status'] == 'OK').sum())}/{len(monthly_df)} tháng OK.",
        f"- Mưa ngày: {int((daily_df['status'] == 'OK').sum())}/{len(daily_df)} ngày OK; "
        f"{int(daily_df['rainfall_mm'].isna().sum())} ngày thiếu (giữ NaN, không thay bằng 0).",
        "",
        "Ghi chú: mưa ngày CHIRPS v3 `rnl` được phân rã từ tổng 5 ngày bằng ERA5,",
        "nên tổng ngày có thể lệch nhỏ so với sản phẩm tháng. Chênh lệch được báo cáo",
        "trong `rainfall_qa.csv`, không tự động hiệu chỉnh.",
        "",
        "## 7. Đầu ra",
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
    catchment_geom = catchment.geometry.union_all()
    print(f"  Bounds: {catchment.total_bounds}")

    # P0: Mưa tháng
    print("\n[2/5] Tải và trích xuất mưa tháng (P0)...")
    monthly_df = extract_monthly(catchment_geom)
    monthly_path = OUT_DIR / "rainfall_monthly.csv"
    monthly_df.to_csv(monthly_path, index=False, encoding="utf-8-sig")
    print(f"  → {monthly_path}")
    n_ok_m = int((monthly_df["status"] == "OK").sum())
    print(f"  Tổng: {len(monthly_df)} tháng, OK: {n_ok_m}")

    # P1: Mưa ngày
    print("\n[3/5] Tải và trích xuất mưa ngày (P1)...")
    daily_df = extract_daily(catchment_geom)
    daily_path = OUT_DIR / "rainfall_daily.csv"
    daily_df.to_csv(daily_path, index=False, encoding="utf-8-sig")
    print(f"  → {daily_path}")
    n_ok_d = int((daily_df["status"] == "OK").sum())
    n_nan_d = int(daily_df["rainfall_mm"].isna().sum())
    print(f"  Tổng: {len(daily_df)} ngày, OK: {n_ok_d}, thiếu: {n_nan_d}")

    # So sánh
    print("\n[4/5] So sánh mưa tháng vs tổng ngày...")
    qa_df = cross_check_monthly_daily(monthly_df, daily_df)
    qa_path = OUT_DIR / "rainfall_qa.csv"
    if len(qa_df) > 0:
        qa_df.to_csv(qa_path, index=False, encoding="utf-8-sig")
        print(f"  → {qa_path}")

    # Phương pháp
    print("\n[5/5] Viết tài liệu phương pháp...")
    write_method(monthly_df, daily_df, qa_df)

    n_bad_m = len(monthly_df) - n_ok_m
    n_bad_d = len(daily_df) - n_ok_d
    if n_bad_m or n_bad_d:
        print(f"\n❌ GATE 3a KHÔNG ĐẠT: {n_bad_m} tháng và {n_bad_d} ngày "
              "không có dữ liệu hợp lệ.")
        print("  → Không dùng giá trị 0 thay cho dữ liệu thiếu.")
        print("  → Xem cột `status`/`error` trong rainfall_monthly.csv và "
              "rainfall_daily.csv.")
        return 1

    print("\n✅ GATE 3a (mưa CHIRPS) hoàn thành.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
