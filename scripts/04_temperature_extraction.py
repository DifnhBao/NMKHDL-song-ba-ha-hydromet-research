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
import json
import time
import hashlib
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
    geom = catchment.geometry.union_all()
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


def _lat_weighted_mean_2d(values, latitudes):
    """Trung bình có trọng số cos(vĩ độ) cho mảng 2 chiều (lat, lon)."""
    mask = np.isfinite(values)
    if not mask.any():
        return np.nan, 0
    w = np.cos(np.radians(np.asarray(latitudes, dtype="float64")))
    ww = np.broadcast_to(w[:, None], values.shape)
    return (float(np.sum(values[mask] * ww[mask]) / np.sum(ww[mask])),
            int(mask.sum()))


def extract_temperature_from_nc(nc_path, catchment_geom, is_monthly=True):
    """Trích xuất nhiệt độ từ NetCDF, chỉ dùng pixel nằm trong lưu vực.

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
        data_vars = [v for v in ds.data_vars if v not in ["latitude", "longitude"]]
        if data_vars:
            temp_var = data_vars[0]
        else:
            ds.close()
            return []

    da = ds[temp_var]

    # Chuẩn hóa tên tọa độ/thời gian
    rename = {}
    if "latitude" in da.dims:
        rename["latitude"] = "y"
    if "longitude" in da.dims:
        rename["longitude"] = "x"
    if "valid_time" in da.dims:
        rename["valid_time"] = "time"
    if rename:
        da = da.rename(rename)

    if "y" not in da.dims or "x" not in da.dims:
        print("  ⚠️ Không nhận dạng được trục không gian của NetCDF")
        ds.close()
        return []

    # Gán CRS và CẮT THEO POLYGON — không lấy trung bình cả bounding box
    try:
        from shapely.geometry import mapping
        da = da.rio.write_crs("EPSG:4326")
        da = da.rio.clip([mapping(catchment_geom)], "EPSG:4326",
                         drop=True, all_touched=False)
    except Exception as exc:
        print(f"  ⚠️ Không cắt được NetCDF theo polygon: {exc}")
        ds.close()
        return []

    lats = da["y"].values
    results = []

    if is_monthly:
        time_dim = "time" if "time" in da.dims else None
        if time_dim:
            for t in da.time.values:
                vals = da.sel(time=t).values
                temp_k, n_pix = _lat_weighted_mean_2d(vals, lats)
                if n_pix > 0:
                    ts = pd.Timestamp(t)
                    results.append({
                        "year_month": ts.strftime("%Y-%m"),
                        "temperature_c": round(temp_k - 273.15, 2),
                        "temperature_k": round(temp_k, 2),
                        "n_pixels": n_pix,
                    })
        else:
            temp_k, n_pix = _lat_weighted_mean_2d(da.values, lats)
            if n_pix > 0:
                results.append({
                    "temperature_c": round(temp_k - 273.15, 2),
                    "temperature_k": round(temp_k, 2),
                    "n_pixels": n_pix,
                })
    else:
        if "time" in da.dims:
            daily = da.resample(time="1D").mean()
            for t in daily.time.values:
                vals = daily.sel(time=t).values
                temp_k, n_pix = _lat_weighted_mean_2d(vals, lats)
                if n_pix > 0:
                    ts = pd.Timestamp(t)
                    results.append({
                        "date": ts.strftime("%Y-%m-%d"),
                        "temperature_c": round(temp_k - 273.15, 2),
                        "temperature_k": round(temp_k, 2),
                        "n_pixels": n_pix,
                    })

    ds.close()
    return results


def _gate2_status():
    path = QA_DIR / "gate2_approval.json"
    if not path.exists():
        return "chưa có tệp phê duyệt GATE 2"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return "tệp phê duyệt GATE 2 không đọc được"
    if data.get("approved") is True:
        return f"đã phê duyệt bởi {data.get('approved_by', 'không rõ')}"
    return "chưa được phê duyệt"


def write_method(access_channel, source_label, n_points,
                 monthly_df=None, daily_df=None):
    """Viết temperature_method.md với đúng kênh truy cập thực tế."""
    n_bad_m = 0 if monthly_df is None else int(monthly_df["temperature_c"].isna().sum())
    n_bad_d = 0 if daily_df is None else int(daily_df["temperature_c"].isna().sum())

    lines = [
        "# Phương pháp trích xuất nhiệt độ ERA5-Land",
        "",
        "## 1. Nguồn dữ liệu",
        "",
        f"- **Sản phẩm:** {source_label}",
        "- **Biến:** 2m temperature (t2m)",
        "- **Loại:** Dữ liệu tái phân tích (reanalysis)",
        "- **Độ phân giải không gian:** ~9 km (0,1°)",
        "- **Đơn vị gốc:** Kelvin (K) khi tải qua CDS; °C khi truy vấn Open-Meteo",
        f"- **Kênh truy cập:** {access_channel}",
        "",
        "## 2. Phạm vi",
        "",
        "- **Thời gian:** 01/2023 – 12/2025 (36 tháng)",
        "- **Không gian:** Lưu vực sông Ba đến thủy điện Sông Ba Hạ",
        f"- **Ranh giới:** song_ba_ha_catchment.geojson ({_gate2_status()})",
        f"- **Số điểm lưới dùng để lấy trung bình:** {n_points}",
        "",
        "## 3. Phương pháp",
        "",
        "### Nhiệt độ tháng (P0)",
        "- Sử dụng ERA5-Land monthly averaged reanalysis khi tải qua CDS; khi dùng",
        "  Open-Meteo, nhiệt độ tháng là trung bình có trọng số của các ngày trong tháng.",
        "- Chỉ dùng các ô lưới có tâm nằm trong polygon lưu vực.",
        "- Trung bình có trọng số cos(vĩ độ) theo diện tích ô lưới.",
        "- Chuyển đổi: T(°C) = T(K) − 273,15 (khi nguồn là Kelvin).",
        "",
        "### Nhiệt độ ngày (P1)",
        ("- Sử dụng ERA5-Land hourly reanalysis, tổng hợp 24 giờ thành trung bình ngày (UTC)."
         if "CDS" in access_channel else
         "- Giá trị trung bình ngày (`daily=temperature_2m_mean`) do Open-Meteo tổng hợp\n  từ ERA5-Land hourly theo múi giờ UTC."),
        "- Chỉ dùng các ô lưới trong polygon lưu vực, trọng số cos(vĩ độ).",
        "",
        "## 4. Lưu ý",
        "",
        "- Dữ liệu ERA5-Land theo UTC, không hoàn toàn trùng ngày quan trắc tại công trình (UTC+7).",
        "- Không sử dụng nhiệt độ bề mặt đất (skin temperature) — chỉ dùng 2m temperature.",
        "- Dữ liệu là tái phân tích, khác với quan trắc trực tiếp.",
        "- Nếu kênh truy cập không phải CDS, đây là khác biệt về kênh phân phối",
        "  (cùng sản phẩm ERA5-Land) và phải được ghi rõ trong báo cáo.",
        "",
        "## 5. Trạng thái dữ liệu",
        "",
        f"- Nhiệt độ tháng: {0 if monthly_df is None else len(monthly_df) - n_bad_m}/"
        f"{0 if monthly_df is None else len(monthly_df)} tháng có dữ liệu.",
        f"- Nhiệt độ ngày: {0 if daily_df is None else len(daily_df) - n_bad_d}/"
        f"{0 if daily_df is None else len(daily_df)} ngày có dữ liệu.",
        "",
        "## 6. Đầu ra",
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

    has_cds = (Path.home() / ".cdsapirc").exists() or "CDSAPI_KEY" in os.environ

    if has_cds:
        # ── P0: Nhiệt độ tháng qua CDS API ────────────────────────────
        print("\n[2/4] Tải và trích xuất nhiệt độ tháng qua CDS API (P0)...")
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

        # ── P1: Nhiệt độ ngày qua CDS API ─────────────────────────────
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
                    days_in_month = calendar.monthrange(year, month)[1]
                    for d in range(1, days_in_month + 1):
                        daily_records.append({
                            "date": f"{year}-{month:02d}-{d:02d}",
                            "temperature_c": np.nan,
                            "source": "ERA5-Land",
                            "status": "DOWNLOAD_FAILED"
                        })

        daily_df = pd.DataFrame(daily_records)
        access_channel = "Copernicus CDS API (reanalysis-era5-land)"
        source_label = "ERA5-Land (Copernicus Climate Data Store)"
        n_points = int(daily_df["n_pixels"].max()) if len(daily_df) else 0
    else:
        print("\n[2/4] Không tìm thấy ~/.cdsapirc.")
        print("  → Dùng Open-Meteo Archive API để truy vấn CÙNG sản phẩm ERA5-Land.")
        print("  ⚠️ Đây là khác biệt về kênh phân phối, cần người giám sát phê duyệt (V1.1 §20).")
        import requests
        from shapely.geometry import Point

        step = 0.1
        lat0 = np.floor(bounds[1] / step) * step
        lon0 = np.floor(bounds[0] / step) * step
        lat_grid = np.arange(lat0, bounds[3] + step, step)
        lon_grid = np.arange(lon0, bounds[2] + step, step)

        points = [
            (round(float(lat), 2), round(float(lon), 2))
            for lat in lat_grid for lon in lon_grid
            if catchment_geom.contains(Point(lon, lat))
        ]
        if not points:
            sys.exit("[LỖI] Không có điểm lưới nào nằm trong lưu vực.")

        n_points = len(points)
        print(f"  Số điểm lưới 0,1° nằm trong lưu vực: {n_points}")

        raw_dir = RAW_ERA5_DIR / "openmeteo"
        raw_dir.mkdir(parents=True, exist_ok=True)

        def fetch_batch(batch, cache_path):
            if cache_path.exists():
                return json.loads(cache_path.read_text(encoding="utf-8"))

            lat_s = ",".join(str(p[0]) for p in batch)
            lon_s = ",".join(str(p[1]) for p in batch)
            url = (
                "https://archive-api.open-meteo.com/v1/archive?"
                f"latitude={lat_s}&longitude={lon_s}"
                "&start_date=2023-01-01&end_date=2025-12-31"
                "&daily=temperature_2m_mean&models=era5_land&timezone=UTC"
            )
            last_err = None
            for attempt in range(5):
                resp = requests.get(url, timeout=180)
                if resp.status_code == 429:
                    wait = 20 * (attempt + 1)
                    last_err = "HTTP 429 Too Many Requests"
                    print(f"      429 Too Many Requests — chờ {wait}s rồi thử lại "
                          f"({attempt + 1}/5)")
                    time.sleep(wait)
                    continue
                resp.raise_for_status()
                data = resp.json()
                cache_path.write_text(json.dumps(data, ensure_ascii=False),
                                      encoding="utf-8")
                return data
            raise RuntimeError(f"Open-Meteo không trả dữ liệu sau 5 lần thử: {last_err}")

        series, weights = [], []
        batch_size = 25
        for i in range(0, n_points, batch_size):
            batch = points[i:i + batch_size]
            tag = hashlib.md5(
                json.dumps(batch).encode("utf-8")).hexdigest()[:8]
            data = fetch_batch(
                batch, raw_dir / f"era5land_openmeteo_{tag}.json")

            items = data if isinstance(data, list) else [data]
            for item in items:
                d = item.get("daily", {})
                if not d or "temperature_2m_mean" not in d:
                    continue
                s = pd.Series(d["temperature_2m_mean"],
                              index=pd.to_datetime(d["time"]))
                series.append(s)
                weights.append(np.cos(np.radians(float(item["latitude"]))))
            print(f"    Batch {i // batch_size + 1}: {len(items)} điểm")
            time.sleep(3)

        if not series:
            sys.exit("[LỖI] Không truy xuất được dữ liệu ERA5-Land từ Open-Meteo.")

        df_grid = pd.concat(series, axis=1).sort_index()
        vals = df_grid.values.astype("float64")
        w = np.asarray(weights, dtype="float64")
        mask = np.isfinite(vals)
        ww = np.broadcast_to(w, vals.shape)
        num = np.where(mask, vals * ww, 0.0).sum(axis=1)
        den = np.where(mask, ww, 0.0).sum(axis=1)
        with np.errstate(invalid="ignore", divide="ignore"):
            daily_mean = np.where(den > 0, num / den, np.nan)
        n_valid = mask.sum(axis=1)

        daily_records = []
        for d_str, temp_c, n_ok in zip(df_grid.index, daily_mean, n_valid):
            daily_records.append({
                "date": d_str.strftime("%Y-%m-%d"),
                "temperature_c": round(float(temp_c), 2) if np.isfinite(temp_c) else np.nan,
                "temperature_k": (round(float(temp_c) + 273.15, 2)
                                  if np.isfinite(temp_c) else np.nan),
                "n_pixels": int(n_ok),
                "source": "ERA5-Land via Open-Meteo Archive API (ECMWF, 2m_temperature)",
                "status": "OK" if np.isfinite(temp_c) else "NO_DATA",
            })
        daily_df = pd.DataFrame(daily_records)

        # Nhiệt độ tháng = trung bình các ngày có dữ liệu trong tháng
        daily_df_copy = daily_df.copy()
        daily_df_copy["year_month"] = daily_df_copy["date"].str[:7]
        monthly_grp = (daily_df_copy.groupby("year_month")["temperature_c"]
                       .agg(["mean", "count"]))

        monthly_records = []
        for ym, row in monthly_grp.iterrows():
            t_mean = row["mean"]
            monthly_records.append({
                "year_month": ym,
                "temperature_c": round(float(t_mean), 2) if pd.notna(t_mean) else np.nan,
                "temperature_k": (round(float(t_mean) + 273.15, 2)
                                  if pd.notna(t_mean) else np.nan),
                "n_pixels": n_points,
                "n_days": int(row["count"]),
                "source": "ERA5-Land via Open-Meteo Archive API (mean of daily means)",
                "status": "OK" if pd.notna(t_mean) else "NO_DATA",
            })
        monthly_df = pd.DataFrame(monthly_records)

        access_channel = "Open-Meteo Archive API (models=era5_land)"
        source_label = "ERA5-Land (ECMWF), truy vấn qua Open-Meteo"

    monthly_path = OUT_DIR / "temperature_monthly.csv"
    monthly_df.to_csv(monthly_path, index=False, encoding="utf-8-sig")
    print(f"  → {monthly_path}")

    daily_path = OUT_DIR / "temperature_daily.csv"
    daily_df.to_csv(daily_path, index=False, encoding="utf-8-sig")
    print(f"  → {daily_path}")

    # Phương pháp
    print("\n[4/4] Viết tài liệu phương pháp...")
    write_method(access_channel, source_label, n_points, monthly_df, daily_df)

    n_bad_m = (36 - len(monthly_df)) + int(monthly_df["temperature_c"].isna().sum())
    n_bad_d = (1096 - len(daily_df)) + int(daily_df["temperature_c"].isna().sum())
    if n_bad_m or n_bad_d:
        print(f"\n❌ GATE 3b KHÔNG ĐẠT: {n_bad_m} tháng và {n_bad_d} ngày thiếu dữ liệu.")
        return 1

    print("\n✅ GATE 3b (nhiệt độ ERA5-Land) hoàn thành.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
