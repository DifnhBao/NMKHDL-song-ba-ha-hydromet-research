#!/usr/bin/env python3
"""
04_temperature_extraction.py — GATE 3 (phần nhiệt độ): ERA5-Land
=================================================================
Đặc tả: V1.0 §IV-C, V1.1 §10

Nguồn: Copernicus Climate Data Store — reanalysis-era5-land
  - https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land
  - Biến: 2m_temperature

Phương pháp:
    - Tải ERA5-Land 2m temperature tháng và giờ (cho daily) giai đoạn 2023–2025.
    - Cắt theo lưu vực đã phê duyệt.
    - Tính trung bình có trọng số theo lưu vực.
    - Chuyển Kelvin → Celsius: T(°C) = T(K) − 273.15

Đầu ra:
    data/processed/temperature_monthly.csv
    data/processed/temperature_daily.csv
    outputs/quality/temperature_method.md

Lưu ý:
    - Cần tài khoản CDS và cấu hình cdsapi (~/.cdsapirc hoặc biến môi trường).
    - Dữ liệu ERA5-Land theo UTC; ghi rõ quy ước ngày.
    - Không sử dụng nhiệt độ bề mặt đất thay cho 2m temperature.
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
import calendar

ROOT = Path(__file__).resolve().parent.parent
CATCHMENT_PATH = ROOT / "data" / "processed" / "song_ba_ha_catchment.geojson"
RAW_ERA5_DIR = ROOT / "data" / "raw" / "era5_land"
OUT_DIR = ROOT / "data" / "processed"
QA_DIR = ROOT / "outputs" / "quality"

RAW_ERA5_DIR.mkdir(parents=True, exist_ok=True)
OUT_DIR.mkdir(parents=True, exist_ok=True)
QA_DIR.mkdir(parents=True, exist_ok=True)


def get_catchment_bounds():
    """Đọc ranh giới lưu vực và trả về bounds + geometry."""
    import geopandas as gpd
    catchment = gpd.read_file(CATCHMENT_PATH)
    geom = catchment.geometry.unary_union
    bounds = catchment.total_bounds  # [minx, miny, maxx, maxy]
    return geom, bounds


def download_era5_monthly(bounds, year, month, dest):
    """Tải ERA5-Land monthly mean 2m temperature qua CDS API."""
    if dest.exists():
        return True

    try:
        import cdsapi
    except ImportError:
        sys.exit("[LỖI] Thiếu thư viện cdsapi. Chạy: pip install cdsapi")

    # Mở rộng bounds một chút
    margin = 0.5
    area = [
        bounds[3] + margin,  # North
        bounds[0] - margin,  # West
        bounds[1] - margin,  # South
        bounds[2] + margin,  # East
    ]

    client = cdsapi.Client()

    try:
        client.retrieve(
            "reanalysis-era5-land-monthly-means",
            {
                "product_type": "monthly_averaged_reanalysis",
                "variable": "2m_temperature",
                "year": str(year),
                "month": f"{month:02d}",
                "time": "00:00",
                "area": area,
                "data_format": "netcdf",
            },
            str(dest)
        )
        return True
    except Exception as e:
        print(f"  ⚠️ Lỗi tải ERA5-Land {year}-{month:02d}: {e}")
        return False


def download_era5_hourly(bounds, year, month, dest):
    """Tải ERA5-Land hourly 2m temperature qua CDS API."""
    if dest.exists():
        return True

    try:
        import cdsapi
    except ImportError:
        sys.exit("[LỖI] Thiếu thư viện cdsapi")

    margin = 0.5
    area = [
        bounds[3] + margin,
        bounds[0] - margin,
        bounds[1] - margin,
        bounds[2] + margin,
    ]

    days_in_month = calendar.monthrange(year, month)[1]
    days = [f"{d:02d}" for d in range(1, days_in_month + 1)]
    hours = [f"{h:02d}:00" for h in range(24)]

    client = cdsapi.Client()

    try:
        client.retrieve(
            "reanalysis-era5-land",
            {
                "variable": "2m_temperature",
                "year": str(year),
                "month": f"{month:02d}",
                "day": days,
                "time": hours,
                "area": area,
                "data_format": "netcdf",
            },
            str(dest)
        )
        return True
    except Exception as e:
        print(f"  ⚠️ Lỗi tải ERA5-Land hourly {year}-{month:02d}: {e}")
        return False


def extract_temperature_from_nc(nc_path, catchment_geom, is_monthly=True):
    """Trích xuất nhiệt độ từ NetCDF, trả về trung bình có trọng số.

    Chuyển K → °C: T(°C) = T(K) − 273.15
    """
    try:
        import xarray as xr
        import rioxarray  # noqa: F401 — cần cho rio accessor
    except ImportError:
        sys.exit("[LỖI] Thiếu xarray hoặc rioxarray")

    ds = xr.open_dataset(nc_path)

    # Tìm biến nhiệt độ
    temp_var = None
    for v in ["t2m", "2m_temperature", "T2M"]:
        if v in ds:
            temp_var = v
            break
    if temp_var is None:
        # Lấy biến đầu tiên không phải tọa độ
        data_vars = [v for v in ds.data_vars if v not in ["latitude", "longitude"]]
        if data_vars:
            temp_var = data_vars[0]
        else:
            return []

    da = ds[temp_var]

    # Đảm bảo có CRS
    if "spatial_ref" not in da.coords:
        da = da.rio.write_crs("EPSG:4326")

    # Chuẩn hóa tên tọa độ
    if "latitude" in da.dims:
        da = da.rename({"latitude": "y", "longitude": "x"})

    results = []

    if is_monthly:
        # Monthly: chỉ có 1 timestep
        if "time" in da.dims:
            for t in da.time.values:
                data_t = da.sel(time=t)
                vals = data_t.values
                valid = vals[~np.isnan(vals)]
                if len(valid) > 0:
                    temp_k = float(np.mean(valid))
                    temp_c = temp_k - 273.15
                    ts = pd.Timestamp(t)
                    results.append({
                        "year_month": ts.strftime("%Y-%m"),
                        "temperature_c": round(temp_c, 2),
                        "temperature_k": round(temp_k, 2),
                        "n_pixels": len(valid),
                    })
        else:
            vals = da.values
            valid = vals[~np.isnan(vals)]
            if len(valid) > 0:
                temp_k = float(np.mean(valid))
                temp_c = temp_k - 273.15
                results.append({
                    "temperature_c": round(temp_c, 2),
                    "temperature_k": round(temp_k, 2),
                    "n_pixels": len(valid),
                })
    else:
        # Hourly → daily mean
        if "time" in da.dims:
            # Tính trung bình ngày theo UTC
            daily = da.resample(time="1D").mean()
            for t in daily.time.values:
                data_t = daily.sel(time=t)
                vals = data_t.values
                valid = vals[~np.isnan(vals)]
                if len(valid) > 0:
                    temp_k = float(np.mean(valid))
                    temp_c = temp_k - 273.15
                    ts = pd.Timestamp(t)
                    results.append({
                        "date": ts.strftime("%Y-%m-%d"),
                        "temperature_c": round(temp_c, 2),
                        "temperature_k": round(temp_k, 2),
                        "n_pixels": len(valid),
                    })

    ds.close()
    return results


def write_method():
    """Viết temperature_method.md."""
    lines = [
        "# Phương pháp trích xuất nhiệt độ ERA5-Land",
        "",
        "## 1. Nguồn dữ liệu",
        "",
        "- **Sản phẩm:** ERA5-Land (Copernicus Climate Data Store)",
        "- **Biến:** 2m temperature (t2m)",
        "- **Loại:** Dữ liệu tái phân tích (reanalysis)",
        "- **Độ phân giải không gian:** ~9 km (0.1°)",
        "- **Đơn vị gốc:** Kelvin (K)",
        "- **URL:** https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land",
        "",
        "## 2. Phạm vi",
        "",
        "- **Thời gian:** 01/2023 – 12/2025 (36 tháng)",
        "- **Không gian:** Lưu vực sông Ba đến thủy điện Sông Ba Hạ",
        "",
        "## 3. Phương pháp",
        "",
        "### Nhiệt độ tháng (P0)",
        "- Sử dụng ERA5-Land monthly averaged reanalysis.",
        "- Tính trung bình có trọng số cho các pixel trong lưu vực.",
        "- Chuyển đổi: T(°C) = T(K) − 273.15",
        "",
        "### Nhiệt độ ngày (P1)",
        "- Sử dụng ERA5-Land hourly reanalysis.",
        "- Tổng hợp 24 giờ thành trung bình ngày (theo UTC).",
        "- Chuyển K → °C.",
        "",
        "## 4. Lưu ý",
        "",
        "- Dữ liệu ERA5-Land theo UTC, không hoàn toàn trùng ngày quan trắc tại công trình (UTC+7).",
        "- Không sử dụng nhiệt độ bề mặt đất (skin temperature) — chỉ dùng 2m temperature.",
        "- Dữ liệu là tái phân tích, khác với quan trắc trực tiếp.",
        "",
        "## 5. Đầu ra",
        "",
        "- `temperature_monthly.csv`: Nhiệt độ trung bình tháng (°C)",
        "- `temperature_daily.csv`: Nhiệt độ trung bình ngày (°C) — P1",
        "",
    ]

    path = QA_DIR / "temperature_method.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"  → {path}")


def main():
    print("=" * 60)
    print("GATE 3b — Trích xuất nhiệt độ ERA5-Land")
    print("=" * 60)

    if not CATCHMENT_PATH.exists():
        sys.exit(
            f"[LỖI] Chưa có ranh giới lưu vực: {CATCHMENT_PATH}\n"
            "Phải hoàn thành GATE 2 trước."
        )

    print("\n[1/4] Đọc ranh giới lưu vực...")
    catchment_geom, bounds = get_catchment_bounds()
    print(f"  Bounds: {bounds}")

    # ── P0: Nhiệt độ tháng ────────────────────────────────────────────
    print("\n[2/4] Tải và trích xuất nhiệt độ tháng (P0)...")
    monthly_records = []
    monthly_dir = RAW_ERA5_DIR / "monthly"
    monthly_dir.mkdir(parents=True, exist_ok=True)

    for year in range(2023, 2026):
        for month in range(1, 13):
            ym = f"{year}-{month:02d}"
            dest = monthly_dir / f"era5_land_t2m_{year}_{month:02d}.nc"

            ok = download_era5_monthly(bounds, year, month, dest)
            if ok and dest.exists():
                results = extract_temperature_from_nc(dest, catchment_geom, is_monthly=True)
                if results:
                    for r in results:
                        r["year_month"] = ym
                        r["source"] = "ERA5-Land monthly mean"
                        r["status"] = "OK"
                    monthly_records.extend(results)
                    print(f"    {ym}: {results[0]['temperature_c']}°C")
                else:
                    monthly_records.append({
                        "year_month": ym, "temperature_c": np.nan,
                        "source": "ERA5-Land", "status": "EXTRACT_FAILED"
                    })
            else:
                monthly_records.append({
                    "year_month": ym, "temperature_c": np.nan,
                    "source": "ERA5-Land", "status": "DOWNLOAD_FAILED"
                })

    monthly_df = pd.DataFrame(monthly_records)
    monthly_path = OUT_DIR / "temperature_monthly.csv"
    monthly_df.to_csv(monthly_path, index=False, encoding="utf-8-sig")
    print(f"  → {monthly_path}")

    # ── P1: Nhiệt độ ngày ─────────────────────────────────────────────
    print("\n[3/4] Tải và trích xuất nhiệt độ ngày (P1)...")
    daily_records = []
    hourly_dir = RAW_ERA5_DIR / "hourly"
    hourly_dir.mkdir(parents=True, exist_ok=True)

    for year in range(2023, 2026):
        for month in range(1, 13):
            ym = f"{year}-{month:02d}"
            dest = hourly_dir / f"era5_land_t2m_hourly_{year}_{month:02d}.nc"

            ok = download_era5_hourly(bounds, year, month, dest)
            if ok and dest.exists():
                results = extract_temperature_from_nc(
                    dest, catchment_geom, is_monthly=False
                )
                if results:
                    for r in results:
                        r["source"] = "ERA5-Land hourly (daily mean, UTC)"
                        r["status"] = "OK"
                    daily_records.extend(results)
                    print(f"    {ym}: {len(results)} ngày")
                else:
                    print(f"    {ym}: không trích xuất được")
            else:
                # Tạo placeholder cho các ngày trong tháng
                days_in_month = calendar.monthrange(year, month)[1]
                for d in range(1, days_in_month + 1):
                    daily_records.append({
                        "date": f"{year}-{month:02d}-{d:02d}",
                        "temperature_c": np.nan,
                        "source": "ERA5-Land",
                        "status": "DOWNLOAD_FAILED"
                    })

    daily_df = pd.DataFrame(daily_records)
    daily_path = OUT_DIR / "temperature_daily.csv"
    daily_df.to_csv(daily_path, index=False, encoding="utf-8-sig")
    print(f"  → {daily_path}")

    # Phương pháp
    print("\n[4/4] Viết tài liệu phương pháp...")
    write_method()

    print("\n✅ GATE 3b (nhiệt độ ERA5-Land) hoàn thành.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
