# 02 — Nguồn dữ liệu và phương pháp

## 1. Dữ liệu thủy văn — Website Sông Ba Hạ

- **Nguồn:** https://www.sbh.vn/vi-VN/san-xuat/Tinh-hinh-san-xuat-60-1300
- **Loại:** Số liệu vận hành công trình, công bố hàng ngày
- **Biến chính:** Lưu lượng nước về hồ (m³/s), mực nước thượng lưu (m), mực nước hạ lưu (m), lưu lượng xả (m³/s), sản lượng điện (kWh), công suất cực đại (MW)
- **Độ phân giải:** Ngày
- **Thu thập:** Bằng script `song_ba_ha_collector.py`, tải HTML rồi trích xuất bảng
- **Lưu ý:** Chưa xác minh liệu lưu lượng công bố là trung bình ngày hay giá trị tại thời điểm xác định. Dữ liệu gốc (HTML + CSV) được bảo toàn nguyên trạng trong `data/raw/hydrology/`

## 2. Lượng mưa — CHIRPS v3 Final

- **Nguồn:** Climate Hazards Center, University of California, Santa Barbara
- **URL:** https://data.chc.ucsb.edu/products/CHIRPS/v3.0/
- **Loại:** Ước lượng mưa kết hợp vệ tinh và quan trắc mặt đất
- **Sản phẩm tháng:** `monthly/global/` — đơn vị mm/tháng
- **Sản phẩm ngày:** `daily/final/rnl/` — đơn vị mm/ngày, phân rã từ khoảng 5 ngày bằng ERA5
- **Độ phân giải:** ~0.05° (~5 km)
- **Phương pháp tổng hợp:** Trung bình có trọng số diện tích cho lưu vực
  - `P_t = Σ(A_i × P_i,t) / Σ(A_i)` trong đó A_i là diện tích ô raster thuộc lưu vực
  - Cắt raster bằng rasterio.mask theo polygon lưu vực
- **Đơn vị đầu ra:** mm/tháng (sản phẩm tháng), mm/ngày (sản phẩm ngày)
- **Lưu ý:** Không cộng giá trị các ô raster để tạo tổng mưa lưu vực

## 3. Nhiệt độ — ERA5-Land

- **Nguồn:** Copernicus Climate Data Store (ECMWF)
- **URL:** https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land
- **Biến:** 2m temperature (t2m) — nhiệt độ không khí 2 m
- **Loại:** Dữ liệu tái phân tích (reanalysis), không phải quan trắc trực tiếp
- **Đơn vị gốc:** Kelvin → chuyển sang °C: `T(°C) = T(K) − 273.15`
- **Độ phân giải:** ~0.1° (~9 km)
- **Tổng hợp tháng:** ERA5-Land monthly averaged reanalysis
- **Tổng hợp ngày:** ERA5-Land hourly → trung bình 24 giờ theo UTC
- **Lưu ý:** Dữ liệu theo UTC, không hoàn toàn trùng ngày quan trắc tại công trình (UTC+7). Không sử dụng nhiệt độ bề mặt đất (skin temperature).

## 4. Ranh giới lưu vực — HydroBASINS

- **Nguồn:** HydroBASINS v1c (HydroSHEDS, WWF)
- **URL:** https://www.hydrosheds.org/products/hydrobasins
- **Dữ liệu:** Level 12 châu Á (chi tiết nhất)
- **Phương pháp:** Xác định tiểu lưu vực cửa ra → truy vết ngược bằng NEXT_DOWN → hợp nhất polygon
- **Tính diện tích:** Phép chiếu Albers Equal Area
- **Đối chiếu:** Diện tích công bố 11.115 km²

## 5. Quy ước thời gian và đơn vị

| Biến | Đơn vị | Quy ước thời gian |
|------|--------|-------------------|
| Lưu lượng | m³/s | Giá trị công bố theo ngày (SBH) |
| Mực nước | m | Giá trị công bố theo ngày (SBH) |
| Mưa tháng | mm/tháng | CHIRPS v3 monthly product |
| Mưa ngày | mm/ngày | CHIRPS v3 daily rnl |
| Nhiệt độ tháng | °C | ERA5-Land monthly mean |
| Nhiệt độ ngày | °C | ERA5-Land hourly → daily mean (UTC) |

## 6. Phân biệt loại dữ liệu

- **Số liệu công trình (SBH):** Giá trị vận hành, không phải quan trắc khí tượng chuẩn
- **Vệ tinh kết hợp quan trắc (CHIRPS):** Kết hợp dữ liệu vệ tinh, trạm quan trắc và tái phân tích
- **Tái phân tích (ERA5-Land):** Sản phẩm mô hình đồng hóa dữ liệu, không phải đo trực tiếp
