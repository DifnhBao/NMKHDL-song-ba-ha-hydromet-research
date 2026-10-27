# 03 — Tổng quan chất lượng dữ liệu

## 1. Dữ liệu thủy văn (GATE 1)

- Số dòng: **1096** ngày, **36** tháng; không trùng ngày.
- Bản gốc được bảo toàn; dữ liệu xử lý có cột chất lượng riêng cho từng biến.

### 1.1. Kết quả kiểm tra theo biến (T02)

| variable | label | unit | total_days | VALID | SUSPECT | MISSING | INVALID_CONFIRMED | CORRECTED | valid_pct | missing_pct | n_zero | min | max |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| inflow_m3s | Lưu lượng về hồ | m³/s | 1096 | 1092 | 4 | 0 | 0 | 0 | 99,64 | 0,00 | 1 | 0,00 | 12.455,00 |
| upstream_level_m | Mực nước thượng lưu | m | 1096 | 1084 | 10 | 0 | 2 | 0 | 98,91 | 0,00 | 1 | 0,00 | 140,30 |
| downstream_level_m | Mực nước hạ lưu | m | 1096 | 1091 | 3 | 0 | 2 | 0 | 99,54 | 0,00 | 3 | 0,00 | 103,91 |
| release_m3s | Lưu lượng xả | m³/s | 1096 | 1096 | 0 | 0 | 0 | 0 | 100,00 | 0,00 | 893 | 0,00 | 11.495,00 |
| daily_energy_kwh | Sản lượng điện ngày | kWh | 1096 | 1096 | 0 | 0 | 0 | 0 | 100,00 | 0,00 | 10 | 0,00 | 5.401.855,00 |
| max_power_mw | Công suất cực đại | MW | 1096 | 1091 | 4 | 0 | 1 | 0 | 99,54 | 0,00 | 4 | 0,00 | 707,00 |

### 1.2. Ngoại lệ theo cờ (T02b)

| variable | flag | n_records |
|---|---|---|
| downstream_level_m | SUSPECT | 4 |
| inflow_m3s | SUSPECT | 4 |
| inflow_m3s, upstream_level_m | SUSPECT | 1 |
| max_power_mw | INVALID_CONFIRMED | 1 |
| max_power_mw | SUSPECT | 4 |
| upstream_level_m | SUSPECT | 19 |
| upstream_level_m, downstream_level_m | INVALID_CONFIRMED | 2 |

Tổng số bản ghi ngoại lệ: **35**. Phân bố theo biến:
downstream_level_m (4), inflow_m3s (4), inflow_m3s, upstream_level_m (1), max_power_mw (5), upstream_level_m (19), upstream_level_m, downstream_level_m (2).

- `SUSPECT`: 32 bản ghi — giữ nguyên giá trị, đánh dấu
  để kiểm tra độ nhạy, không loại khỏi phân tích chính.
- `INVALID_CONFIRMED`: 3 bản ghi — không dùng
  trong phép tính chính, giữ nguyên bản gốc.

### 1.3. Các ngoại lệ quan trọng

| Ngày | Biến | Giá trị | Cờ | Lý do |
|---|---|---|---|---|
| 2023-02-19 | upstream_level_m, downstream_level_m | up=37.2, down=103.91 | INVALID_CONFIRMED | Mực nước thượng lưu nhỏ hơn hạ lưu — nghi đảo cột |
| 2024-04-09 | upstream_level_m, downstream_level_m | up=37.2, down=103.72 | INVALID_CONFIRMED | Mực nước thượng lưu nhỏ hơn hạ lưu — nghi đảo cột |
| 2024-02-03 | max_power_mw | 707.0 | INVALID_CONFIRMED | Công suất 707.0 MW vượt thiết kế 220 MW |
| 2025-11-19 | inflow_m3s | 12455.0 | SUSPECT | Lưu lượng cực lớn 12455.0 m³/s — cần kiểm tra định nghĩa và nguồn; không loại bỏ chỉ vì giá trị cao. Có thể liên quan sự kiện lũ lớn tháng 11/2025 |
| 2025-11-20 | inflow_m3s | 12455.0 | SUSPECT | Lưu lượng cực lớn 12455.0 m³/s — cần kiểm tra định nghĩa và nguồn; không loại bỏ chỉ vì giá trị cao. Có thể liên quan sự kiện lũ lớn tháng 11/2025 |

- Hai ngày **19–20/11/2025** có lưu lượng về hồ 12.455 m³/s — giá trị cực lớn,
  được đánh dấu SUSPECT nhưng **không loại bỏ** vì có thể liên quan đợt lũ lớn.
  Ảnh hưởng được kiểm tra bằng phân tích độ nhạy (T07).
- Mực nước thượng lưu có các ngày 37,2–38,6 m (dưới mực nước chết) và một số
  ngày đảo cột thượng/hạ lưu — đã gắn cờ, không dùng giá trị sai trong phép tính.

### 1.4. Độ phủ theo tháng

- Độ phủ lưu lượng thấp nhất: **90,0%**.
- Số tháng có độ phủ dưới 100%: **2**
  (2023-01, 2025-11).

## 2. Dữ liệu khí tượng (GATE 3)

### 2.1. Lượng mưa CHIRPS

- Mưa tháng: **36/36** tháng có dữ liệu.
- Mưa ngày: **1096/1096** ngày có dữ liệu;
  0 ngày thiếu.
- Nguồn: CHIRPS v3.0 Final daily rnl; CHIRPS v3.0 Final monthly.
- Đối chiếu mưa tháng với tổng mưa ngày (`rainfall_qa.csv`):
  - Số tháng lệch < 10%: **36**;
  - Số tháng lệch ≥ 10%: **0**;
  - Lệch tuyệt đối trung bình: **0,3%**;
  - Lệch tuyệt đối lớn nhất: **1,0%**.
- Lưu ý: mưa ngày CHIRPS v3 `rnl` được phân rã từ tổng 5 ngày, nên không kỳ vọng
  khớp tuyệt đối với sản phẩm tháng. Chênh lệch được báo cáo, không tự hiệu chỉnh.

### 2.2. Nhiệt độ ERA5-Land

- Nhiệt độ tháng: **36/36** tháng.
- Nhiệt độ ngày: **1096/1096** ngày.
- Nguồn: ERA5-Land via Open-Meteo Archive API (mean of daily means); số điểm lưới: 95.

## 3. Tích hợp dữ liệu (GATE 4)

- Bảng tháng: **36 tháng**, khóa `year_month` không trùng.
- Bảng ngày: **1096 dòng** ngày lịch, khóa `date` không trùng.
- Kết quả kiểm tra: **11/11 đạt**, 0 lỗi.

| check | expected | actual | status |
|---|---|---|---|
| total_daily_rows | 1096 | 1096 | OK |
| total_monthly_rows | 36 | 36 | OK |
| duplicate_dates | 0 | 0 | OK |
| duplicate_months | 0 | 0 | OK |
| zero_as_missing_inflow | 0 | 0 | OK |
| rainfall_daily_valid_days | 1096 | 1096 | OK |
| temperature_daily_valid_days | 1096 | 1096 | OK |
| rainfall_valid_days_consistency | 1096 | 1096 | OK |
| temperature_valid_days_consistency | 1096 | 1096 | OK |
| monthly_vs_daily_rainfall_mismatch_gt10pct | 0 | 0 | OK |
| months_without_quality_status | 0 | 0 | OK |

## 4. Ranh giới lưu vực (GATE 2)

| Kiểm tra | Kết quả |
|---|---|
| Diện tích Albers | 11.160,6 km² |
| Diện tích tham khảo | 11.115 km² |
| Sai lệch | 0,41% |
| Đập trong polygon | True |
| Nhà máy trong polygon | True |
| Hình học hợp lệ | True |
| Trạng thái | APPROVED (Người giám sát dự án (xác nhận trực tiếp trong phiên làm việc), 2026-10-27) |

## 5. Ảnh hưởng đến độ tin cậy

- Các ngày SUSPECT tập trung ở tháng cực đoan (01/2023, 11/2025) nên ảnh hưởng
  trực tiếp đến tương quan RQ3 — đã định lượng bằng T07.
- Sai lệch diện tích lưu vực 0,41% làm sai lệch
  nhỏ lượng mưa trung bình lưu vực; không làm thay đổi kết luận định tính.
- Chuỗi mưa ngày là sản phẩm phân rã, chỉ dùng bổ trợ; phân tích chính dùng
  bảng tháng.
