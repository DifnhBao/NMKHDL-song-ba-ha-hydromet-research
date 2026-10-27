# Phương pháp trích xuất lượng mưa CHIRPS v3

## 1. Nguồn dữ liệu

- **Sản phẩm:** CHIRPS v3 Final (Climate Hazards Center, UC Santa Barbara)
- **Mưa tháng:** https://data.chc.ucsb.edu/products/CHIRPS/v3.0/monthly/global/
- **Mưa ngày:** https://data.chc.ucsb.edu/products/CHIRPS/v3.0/daily/final/rnl/
- **Kênh tải thực tế:** FTP (ftp.chc.ucsb.edu — cùng máy chủ CHC, HTTPS đang bị chặn)
- **Loại dữ liệu:** Ước lượng mưa kết hợp vệ tinh và quan trắc
- **Độ phân giải không gian:** ~0.05° (~5 km)
- **Đơn vị:** mm/tháng (sản phẩm tháng), mm/ngày (sản phẩm ngày)

## 2. Phạm vi

- **Thời gian:** 01/2023 – 12/2025 (36 tháng)
- **Không gian:** Lưu vực sông Ba đến thủy điện Sông Ba Hạ
- **Ranh giới:** song_ba_ha_catchment.geojson (đã phê duyệt bởi Người giám sát dự án (xác nhận trực tiếp trong phiên làm việc))

## 3. Phương pháp tính mưa trung bình lưu vực

Sử dụng trung bình có trọng số diện tích:

```
P_t = Σ(A_i × P_i,t) / Σ(A_i)
```

Trong đó A_i là diện tích phần ô raster giao với polygon lưu vực.
Trọng số theo vĩ độ được áp dụng vì diện tích ô 0,05° tỷ lệ với cos(vĩ độ).
Pixel ngoài polygon hoặc có giá trị nodata (-9999) bị loại, không thay bằng 0.

## 4. Lưu ý khoa học

- Dữ liệu ngày CHIRPS v3 `rnl` được phân rã từ lượng mưa theo khoảng
  năm ngày bằng thông tin ERA5.
- Phân tích tương quan ở quy mô tháng được ưu tiên.
- Không diễn giải tương quan theo ngày thành bằng chứng về thời gian
  phản ứng thủy văn chính xác.
- Giá trị một ô CHIRPS tháng đã mang đơn vị mm/tháng; không cộng trực
  tiếp các giá trị của các ô không gian.

## 5. Kết quả đối chiếu mưa tháng vs tổng mưa ngày

| Tháng | Sản phẩm tháng (mm) | Tổng ngày (mm) | Số ngày thiếu | Lệch (mm) | Lệch (%) | Trạng thái |
|-------|---------------------|----------------|---------------|-----------|----------|------------|
| 2023-01 | 79.05 | 79.42 | 0 | 0.37 | 0.5 | OK |
| 2023-02 | 7.47 | 7.45 | 0 | -0.02 | -0.3 | OK |
| 2023-03 | 11.3 | 11.28 | 0 | -0.02 | -0.2 | OK |
| 2023-04 | 49.46 | 49.31 | 0 | -0.15 | -0.3 | OK |
| 2023-05 | 270.89 | 270.55 | 0 | -0.34 | -0.1 | OK |
| 2023-06 | 212.03 | 211.53 | 0 | -0.5 | -0.2 | OK |
| 2023-07 | 351.46 | 350.24 | 0 | -1.22 | -0.3 | OK |
| 2023-08 | 99.15 | 98.77 | 0 | -0.38 | -0.4 | OK |
| 2023-09 | 350.64 | 350.16 | 0 | -0.48 | -0.1 | OK |
| 2023-10 | 285.92 | 286.15 | 0 | 0.23 | 0.1 | OK |
| 2023-11 | 171.12 | 172.51 | 0 | 1.39 | 0.8 | OK |
| 2023-12 | 45.09 | 45.38 | 0 | 0.29 | 0.6 | OK |
| 2024-01 | 3.99 | 4.0 | 0 | 0.01 | 0.3 | OK |
| 2024-02 | 5.5 | 5.51 | 0 | 0.01 | 0.2 | OK |
| 2024-03 | 21.84 | 21.88 | 0 | 0.04 | 0.2 | OK |
| 2024-04 | 11.69 | 11.71 | 0 | 0.02 | 0.2 | OK |
| 2024-05 | 181.81 | 181.64 | 0 | -0.17 | -0.1 | OK |
| 2024-06 | 180.37 | 180.16 | 0 | -0.21 | -0.1 | OK |
| 2024-07 | 304.84 | 303.75 | 0 | -1.09 | -0.4 | OK |
| 2024-08 | 240.29 | 239.35 | 0 | -0.94 | -0.4 | OK |
| 2024-09 | 242.65 | 242.38 | 0 | -0.27 | -0.1 | OK |
| 2024-10 | 190.08 | 190.59 | 0 | 0.51 | 0.3 | OK |
| 2024-11 | 76.04 | 76.1 | 0 | 0.06 | 0.1 | OK |
| 2024-12 | 166.81 | 167.39 | 0 | 0.58 | 0.3 | OK |
| 2025-01 | 7.61 | 7.62 | 0 | 0.01 | 0.1 | OK |
| 2025-02 | 11.97 | 12.03 | 0 | 0.06 | 0.5 | OK |
| 2025-03 | 13.42 | 13.38 | 0 | -0.04 | -0.3 | OK |
| 2025-04 | 24.06 | 23.98 | 0 | -0.08 | -0.3 | OK |
| 2025-05 | 262.05 | 261.5 | 0 | -0.55 | -0.2 | OK |
| 2025-06 | 244.71 | 244.11 | 0 | -0.6 | -0.2 | OK |
| 2025-07 | 129.79 | 129.4 | 0 | -0.39 | -0.3 | OK |
| 2025-08 | 304.7 | 303.85 | 0 | -0.85 | -0.3 | OK |
| 2025-09 | 331.96 | 331.46 | 0 | -0.5 | -0.2 | OK |
| 2025-10 | 314.46 | 315.4 | 0 | 0.94 | 0.3 | OK |
| 2025-11 | 448.02 | 449.64 | 0 | 1.62 | 0.4 | OK |
| 2025-12 | 32.83 | 33.15 | 0 | 0.32 | 1.0 | OK |

## 6. Trạng thái dữ liệu

- Mưa tháng: 36/36 tháng OK.
- Mưa ngày: 1096/1096 ngày OK; 0 ngày thiếu (giữ NaN, không thay bằng 0).

Ghi chú: mưa ngày CHIRPS v3 `rnl` được phân rã từ tổng 5 ngày bằng ERA5,
nên tổng ngày có thể lệch nhỏ so với sản phẩm tháng. Chênh lệch được báo cáo
trong `rainfall_qa.csv`, không tự động hiệu chỉnh.

## 7. Đầu ra

- `rainfall_monthly.csv`: Mưa tháng trung bình lưu vực
- `rainfall_daily.csv`: Mưa ngày trung bình lưu vực (P1)
- `rainfall_qa.csv`: So sánh mưa tháng vs tổng ngày
