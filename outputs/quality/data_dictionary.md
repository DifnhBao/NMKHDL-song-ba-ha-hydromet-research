# Từ điển dữ liệu (Data Dictionary)

## hydromet_daily.csv

| Cột | Kiểu | Đơn vị | Mô tả |
|-----|------|--------|-------|
| date | YYYY-MM-DD | — | Ngày lịch |
| rainfall_mm | float | mm | Lượng mưa trung bình lưu vực (CHIRPS v3.0 Final daily rnl) |
| temperature_c | float | °C | Nhiệt độ 2 m trung bình lưu vực. Nguồn: ERA5-Land via Open-Meteo Archive API (mean of daily means) |
| inflow_m3s | float | m³/s | Lưu lượng nước về hồ (dữ liệu vận hành Sông Ba Hạ) |
| upstream_level_m | float | m | Mực nước thượng lưu |
| inflow_quality | str | — | Cờ QA: VALID/SUSPECT/MISSING/INVALID_CONFIRMED/CORRECTED |
| level_quality | str | — | Cờ QA mực nước |
| rainfall_quality | str | — | Cờ QA mưa |
| temperature_quality | str | — | Cờ QA nhiệt độ |

## hydromet_monthly.csv

| Cột | Kiểu | Đơn vị | Mô tả |
|-----|------|--------|-------|
| year_month | YYYY-MM | — | Tháng lịch |
| rainfall_total_mm | float | mm | Tổng lượng mưa tháng (sản phẩm mưa tháng) |
| rainfall_daily_sum_mm | float | mm | Tổng mưa ngày trong tháng (để đối chiếu, không dùng thay) |
| temperature_mean_c | float | °C | Nhiệt độ trung bình tháng |
| inflow_mean_m3s | float | m³/s | Trung bình các giá trị lưu lượng ngày đủ ĐK |
| upstream_level_mean_m | float | m | Trung bình mực nước thượng lưu |
| rainfall_valid_days | int | ngày | Số ngày có giá trị mưa ngày hợp lệ |
| rainfall_coverage_pct | float | % | Tỷ lệ ngày có mưa ngày hợp lệ |
| temperature_valid_days | int | ngày | Số ngày có giá trị nhiệt độ hợp lệ |
| temperature_coverage_pct | float | % | Tỷ lệ ngày có nhiệt độ hợp lệ |
| inflow_valid_days | int | ngày | Số ngày lưu lượng đủ ĐK (VALID/CORRECTED) |
| inflow_coverage_pct | float | % | Tỷ lệ ngày lưu lượng hợp lệ |
| rainfall_source | str | — | Nguồn mưa tháng thực tế đã dùng |
| temperature_source | str | — | Nguồn nhiệt độ tháng thực tế đã dùng |
| quality_status | str | — | Cờ: OK / LOW_COVERAGE / NO_RAINFALL / RAINFALL_MONTHLY_ONLY / RAINFALL_DAILY_MISMATCH / NO_TEMPERATURE |

## Quy ước

- **Mưa tháng:** Sử dụng sản phẩm mưa tháng; tổng mưa ngày chỉ dùng để đối chiếu.
- **Nhiệt độ tháng:** Trung bình tháng từ nguồn ghi ở cột `temperature_source`.
- **Lưu lượng tháng:** Trung bình các bản ghi ngày có trạng thái VALID hoặc CORRECTED.
  Đây là trung bình các giá trị công bố, không phải lưu lượng trung bình thực đo
  vì chưa xác minh ý nghĩa thời gian của bản ghi.
- **Không sử dụng 0 thay cho giá trị thiếu.**
- **Không dịch thời gian khi ghép dữ liệu.**
- **Không cộng m³/s để tạo tổng lượng nước.**

## Tháng LOW_COVERAGE

- Tháng có < 90% ngày lưu lượng đủ ĐK được gắn cờ LOW_COVERAGE.
- Không tự động đưa vào phân tích tương quan chính.
