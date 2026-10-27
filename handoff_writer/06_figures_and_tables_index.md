# 06 — Danh mục hình và bảng

## 1. Hình

| Mã | Tệp | Nội dung | Đơn vị | Nguồn | Script | Dùng cho |
|---|---|---|---|---|---|---|
| F01 | `figures/F01_basin_map.png` | Bản đồ vị trí, ranh giới lưu vực, đập và nhà máy | — | HydroBASINS v1c L12; OSM | 02 | RQ1–RQ3 (bối cảnh) |
| F02 | `figures/F02_rainfall_monthly.png` | Biến động lượng mưa theo tháng 2023–2025 | mm/tháng | CHIRPS v3.0 Final | 06 | RQ1 |
| F03 | `figures/F03_temperature_monthly.png` | Nhiệt độ trung bình tháng | °C | ERA5-Land | 06 | RQ1 |
| F04 | `figures/F04_inflow_daily_hydrograph.png` | Lưu lượng nước về hồ theo ngày | m³/s | Sông Ba Hạ | 06 | RQ2 |
| F05 | `figures/F05_inflow_monthly.png` | Lưu lượng nước về hồ theo tháng | m³/s | Sông Ba Hạ | 06 | RQ2 |
| F06 | `figures/F06_upstream_level.png` | Mực nước thượng lưu sau kiểm định | m | Sông Ba Hạ | 06 | RQ2 |
| F07 | `figures/F07_rainfall_inflow_comparison.png` | So sánh mưa tháng và lưu lượng về hồ | mm, m³/s | CHIRPS; Sông Ba Hạ | 07 | RQ3 |
| F08 | `figures/F08_scatter_rainfall_inflow.png` | Scatter mưa – lưu lượng theo tháng | mm, m³/s | CHIRPS; Sông Ba Hạ | 07 | RQ3 |
| F09 | `figures/F09_correlation_comparison.png` | So sánh tương quan lag 0 và lag 1 (kèm p-value) | — | Tính từ bảng tháng | 07 | RQ3 |
| F10 | `figures/F10_inflow_distribution.png` | Phân bố lưu lượng (histogram log + boxplot theo năm) | m³/s | Sông Ba Hạ | 06 | RQ2 (bổ sung) |

Ghi chú:

- F06 chỉ vẽ các ngày VALID và ngắt đoạn tại chỗ thiếu; dữ liệu mực nước có
  lỗi cảm biến đã được gắn cờ.
- **Không có FDC.** Lý do: xem `05_limitations.md` mục 5 (V1.1 §13).
- Mỗi hình PNG ≥ 200 dpi, có tên, đơn vị, chú giải, nguồn số liệu.

## 2. Bảng

| Mã | Tệp | Nội dung | Đơn vị | Nguồn | Script |
|---|---|---|---|---|---|
| T01 | `tables/T01_data_sources.csv` | Danh mục nguồn dữ liệu và đặc điểm kỹ thuật | — | Tổng hợp | 06 |
| T02 | `tables/T02_hydrology_qa_results.csv` | Kết quả kiểm tra chất lượng thủy văn | — | Sông Ba Hạ | 06 |
| T02b | `tables/T02b_exception_counts.csv` | Số bản ghi ngoại lệ theo biến và cờ | — | Sông Ba Hạ | 06 |
| T03 | `tables/T03_meteorology_stats.csv` | Thống kê khí tượng (mưa, nhiệt độ, mùa) | mm, °C | CHIRPS; ERA5-Land | 06 |
| T04 | `tables/T04_hydrology_stats.csv` | Thống kê thủy văn (phân vị, CV, skewness) | m³/s, m | Sông Ba Hạ | 06 |
| T05 | `tables/T05_correlation_results.csv` | Tương quan mưa – dòng chảy (lag, mùa, tercile) | — | Tính từ bảng tháng | 07 |
| T06 | `tables/T06_exceptions_decisions.csv` | Danh sách ngoại lệ và quyết định xử lý | — | Sông Ba Hạ | 06 |
| T07 | `tables/T07_sensitivity.csv` | Độ nhạy khi loại tháng chứa ngày SUSPECT | — | Tính từ bảng tháng | 07 |

## 3. Dữ liệu chọn lọc

| Tệp | Nội dung |
|---|---|
| `selected_data/hydrology_clean.csv` | Thủy văn ngày đã QA, kèm cờ chất lượng |
| `selected_data/hydrology_qa_summary.csv` | Độ phủ theo tháng |
| `selected_data/hydromet_daily.csv` | Bảng tích hợp ngày |
| `selected_data/hydromet_monthly.csv` | Bảng tích hợp tháng (dùng cho phân tích chính) |
| `selected_data/rainfall_monthly.csv` | Mưa tháng CHIRPS |
| `selected_data/rainfall_daily.csv` | Mưa ngày CHIRPS |
| `selected_data/temperature_monthly.csv` | Nhiệt độ tháng ERA5-Land |
| `selected_data/temperature_daily.csv` | Nhiệt độ ngày ERA5-Land |
| `selected_data/song_ba_ha_catchment.geojson` | Polygon lưu vực (EPSG:4326) |
| `selected_data/data_dictionary.md` | Từ điển dữ liệu |

## 4. Cách trích dẫn trong báo cáo

- Hình: "Nguồn: CHIRPS v3.0 Final, tính toán bởi nhóm kỹ thuật (F02)."
- Bảng: "Nguồn: dữ liệu vận hành Sông Ba Hạ, xử lý theo V1.1 (T04)."
- Không sửa số liệu trong CSV; nếu cần làm tròn, ghi rõ quy tắc làm tròn.
