# 06 — Danh sách hình và bảng

## Hình (Figures)

| Mã | Tên tệp | Nội dung | Đơn vị | Nguồn dữ liệu | Script tạo | Sử dụng cho |
|---|---|---|---|---|---|---|
| F01 | `F01_basin_map.png` | Bản đồ ranh giới lưu vực đến công trình | km² | HydroBASINS v1c | `02_basin_delineation.py` | Mô tả khu vực nghiên cứu |
| F02 | `F02_rainfall_monthly.png` | Biến động lượng mưa theo tháng 2023–2025 | mm/tháng | CHIRPS v3 Final | `06_exploratory_analysis.py` | RQ1 — Phân tích mưa |
| F03 | `F03_temperature_monthly.png` | Nhiệt độ trung bình tháng 2023–2025 | °C | ERA5-Land | `06_exploratory_analysis.py` | RQ1 — Phân tích nhiệt độ |
| F04 | `F04_inflow_daily_hydrograph.png` | Lưu lượng nước về hồ theo ngày | m³/s | Sông Ba Hạ | `06_exploratory_analysis.py` | RQ2 — Hydrograph |
| F05 | `F05_inflow_monthly.png` | Lưu lượng trung bình tháng | m³/s | Sông Ba Hạ | `06_exploratory_analysis.py` | RQ2 — Lưu lượng tháng |
| F06 | `F06_upstream_level.png` | Mực nước thượng lưu sau kiểm định | m | Sông Ba Hạ | `06_exploratory_analysis.py` | RQ2 — Mực nước |
| F07 | `F07_rainfall_inflow_comparison.png` | So sánh mưa tháng và lưu lượng | mm, m³/s | CHIRPS + SBH | `07_rainfall_runoff_analysis.py` | RQ3 — Đồng thời |
| F08 | `F08_scatter_rainfall_inflow.png` | Scatter plot mưa – lưu lượng | mm vs m³/s | CHIRPS + SBH | `07_rainfall_runoff_analysis.py` | RQ3 — Phân tán |
| F09 | `F09_correlation_comparison.png` | So sánh tương quan lag 0 và 1 | Hệ số r/ρ | Tính toán | `07_rainfall_runoff_analysis.py` | RQ3 — Tương quan |

### Quy cách hình
- Định dạng: PNG
- Độ phân giải: ≥ 200 dpi
- Mỗi hình có tiêu đề, đơn vị, chú giải, nguồn số liệu
- Thư mục: `outputs/figures/`

## Bảng (Tables)

| Mã | Tên tệp | Nội dung | Định dạng | Script tạo |
|---|---|---|---|---|
| T01 | `T01_data_sources.csv` | Danh mục nguồn dữ liệu và đặc điểm kỹ thuật | CSV | `06_exploratory_analysis.py` |
| T02 | `T02_hydrology_qa_results.csv` | Kết quả kiểm tra chất lượng thủy văn | CSV | `06_exploratory_analysis.py` |
| T03 | `T03_meteorology_stats.csv` | Thống kê khí tượng (mưa + nhiệt độ) | CSV | `06_exploratory_analysis.py` |
| T04 | `T04_hydrology_stats.csv` | Thống kê thủy văn (lưu lượng + mực nước) | CSV | `06_exploratory_analysis.py` |
| T05 | `T05_correlation_results.csv` | Kết quả tương quan mưa – dòng chảy | CSV | `07_rainfall_runoff_analysis.py` |
| T06 | `T06_exceptions_decisions.csv` | Danh sách ngoại lệ và quyết định xử lý | CSV | `07_rainfall_runoff_analysis.py` |

### Quy cách bảng
- Định dạng: CSV (UTF-8 with BOM)
- Thư mục: `outputs/tables/`
- Diễn giải kèm theo trong các file markdown tương ứng

## Ghi chú
- Nếu mực nước không đủ tin cậy, F06 được thay bằng phân bố lưu lượng kèm giải thích
- Hình và bảng cần được sao chép vào `handoff_writer/figures/` và `handoff_writer/tables/` khi bàn giao
