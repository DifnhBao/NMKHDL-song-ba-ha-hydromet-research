# Nguồn hình của `docs/BAO_CAO.docx`

Thư mục này giữ **đúng PNG nhúng trong bản Word** và mã tạo các bố cục riêng của báo cáo. Đường dẫn bên dưới tính từ gốc repository. Nguồn bảng/CSV dùng để đối chiếu là phiên bản kỹ thuật tại commit `a9d3544b242d5554755c78939884f1113188e755`; báo cáo được thêm sau đó. Các hình này không xác thực lại dữ liệu nguồn thô.

| Hình Word | Ảnh sử dụng | Mã / dữ liệu đầu vào |
|---|---|---|
| 1 | `docs/report_repro/F01_basin_map_report.png` | `docs/report_repro/render_F01_map.py`; polygon `handoff_writer/selected_data/song_ba_ha_catchment.geojson` và `data/processed/basin_validation.csv`. Bản đồ chỉ vẽ polygon đã hợp nhất (không có đường tiểu lưu vực) vì raw HydroBASINS không nằm trong repository. Không có tiêu đề trong ảnh. |
| 2 | `docs/report_repro/H02_workflow.png` | `docs/report_repro/render_report_specific.py`; sơ đồ nhóm dựng từ `run_all.py` và các script 01–07 |
| 3 | `docs/report_repro/final_numbered_charts/F02_rainfall_monthly.png` | `render_final_numbered_charts.py` → `scripts/06_exploratory_analysis.py`; `hydromet_monthly.csv` |
| 4 | `docs/report_repro/final_numbered_charts/F03_temperature_monthly.png` | Như Hình 3; `hydromet_monthly.csv` |
| 5 | `docs/report_repro/final_numbered_charts/F04_inflow_daily_hydrograph.png` | Như Hình 3; `hydromet_daily.csv`, `hydrology_qa_summary.csv` |
| 6 | `docs/report_repro/final_numbered_charts/F05_inflow_monthly.png` | Như Hình 3; `hydromet_monthly.csv` |
| 7 | `docs/report_repro/final_numbered_charts/F06_upstream_level.png` | Như Hình 5; chỉ nối ngày mực nước `VALID` |
| 8 | `docs/report_repro/final_numbered_charts/F07_rainfall_inflow_comparison.png` | `render_final_numbered_charts.py` → `scripts/07_rainfall_runoff_analysis.py`; `hydromet_monthly.csv` |
| 9 | `docs/report_repro/final_numbered_charts/F08_scatter_rainfall_inflow.png` | Như Hình 8; `T05_correlation_results.csv` |
| 10 | `docs/report_repro/H10_same_rain_pairs.png` | `docs/report_repro/render_H10_same_rain_pairs.py` → `scripts/13_extended_rq3_analysis.py`; `hydromet_monthly.csv`. Bố cục hai panel, không có tiêu đề trong ảnh; ảnh cũ `F11_docx_vertical.png` giữ lại để đối chiếu. |
| 11 | `docs/report_repro/H11_suspect_sensitivity.png` | `docs/report_repro/render_report_specific.py`; `T05_correlation_results.csv`, `T07_sensitivity.csv`, `T08_alternative_suspect_sensitivity.csv`. Bố cục riêng từ các hệ số đã rà soát. |
| 12 | `docs/report_repro/final_numbered_charts/F10_inflow_distribution.png` | `render_final_numbered_charts.py` → `scripts/06_exploratory_analysis.py`; ngày lưu lượng `VALID` |

Mọi PNG nhúng trong Word đều **không có tiêu đề "Hình N —"** bên trong ảnh: tiêu đề duy nhất là caption của Word. Các đường dẫn CSV ngắn trong bảng ở `handoff_writer/selected_data/` hoặc `handoff_writer/tables/`. Bảng độ nhạy mưa bổ sung ở `outputs/quality/rainfall_spatial_sensitivity.csv`. Các PNG trong thư mục này được giữ lại để nhận diện chính xác hình đã nhúng dù môi trường Matplotlib sau này thay đổi. `engine/06_exploratory_analysis.py` và `engine/07_rainfall_runoff_analysis.py` là bản chụp mã vẽ đúng thời điểm tạo hình; chỉ đổi biến `ROOT` để chạy từ vị trí này. Các script phân tích chính của nhóm vẫn ở `scripts/`.

Từ gốc repository, có thể tạo lại những hình riêng của báo cáo bằng:

```powershell
python docs/report_repro/render_report_specific.py
python docs/report_repro/render_F01_map.py
python docs/report_repro/render_H10_same_rain_pairs.py
python docs/report_repro/render_final_numbered_charts.py
```

`render_final_numbered_charts.py` dùng bản chụp mã vẽ trong `engine/` và bỏ mọi tiêu đề cấp hình; các phép thống kê vẫn lấy từ CSV của đề tài. Chèn lại ảnh vào Word bằng `python docs/report_repro/embed_report_figures.py` (khớp theo caption, giữ nguyên tỉ lệ khung hình). Để tái lập **toàn bộ pipeline từ nguồn thô**, cần thêm raster CHIRPS, phản hồi API Open-Meteo, và raw HTML/CSV thủy văn cùng metadata; các tệp raw này chưa được bàn giao đầy đủ trong repository.
