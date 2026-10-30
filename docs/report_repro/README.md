# Nguồn hình của `docs/BAO_CAO_final.docx`

Thư mục này giữ **đúng PNG nhúng trong bản Word** và mã tạo các bố cục riêng của báo cáo. Đường dẫn bên dưới tính từ gốc repository. Nguồn bảng/CSV dùng để đối chiếu là phiên bản kỹ thuật tại commit `a9d3544b242d5554755c78939884f1113188e755`; báo cáo được thêm sau đó. Các hình này không xác thực lại dữ liệu nguồn thô.

| Hình Word | Ảnh sử dụng | Mã / dữ liệu đầu vào |
|---|---|---|
| 1 | `docs/report_repro/F01_basin_map_report.png` | Bản sao đúng ảnh nhúng từ `handoff_writer/figures/F01_basin_map.png`; `scripts/02_basin_delineation.py`; HydroBASINS, OSM và polygon `handoff_writer/selected_data/song_ba_ha_catchment.geojson` |
| 2 | `docs/report_repro/H02_workflow.png` | `docs/report_repro/render_report_specific.py`; sơ đồ nhóm dựng từ `run_all.py` và các script 01–07 |
| 3 | `docs/report_repro/final_numbered_charts/F02_rainfall_monthly.png` | `render_final_numbered_charts.py` → `scripts/06_exploratory_analysis.py`; `hydromet_monthly.csv` |
| 4 | `docs/report_repro/final_numbered_charts/F03_temperature_monthly.png` | Như Hình 3; `hydromet_monthly.csv` |
| 5 | `docs/report_repro/final_numbered_charts/F04_inflow_daily_hydrograph.png` | Như Hình 3; `hydromet_daily.csv`, `hydrology_qa_summary.csv` |
| 6 | `docs/report_repro/final_numbered_charts/F05_inflow_monthly.png` | Như Hình 3; `hydromet_monthly.csv` |
| 7 | `docs/report_repro/final_numbered_charts/F06_upstream_level.png` | Như Hình 5; chỉ nối ngày mực nước `VALID` |
| 8 | `docs/report_repro/final_numbered_charts/F07_rainfall_inflow_comparison.png` | `render_final_numbered_charts.py` → `scripts/07_rainfall_runoff_analysis.py`; `hydromet_monthly.csv` |
| 9 | `docs/report_repro/final_numbered_charts/F08_scatter_rainfall_inflow.png` | Như Hình 8; `T05_correlation_results.csv` |
| 10 | `docs/report_repro/F11_docx_vertical.png` | `docs/report_repro/generate_report_F11.py`; `hydromet_monthly.csv`, `outputs/tables/T09_selected_pairs.csv`. Bố cục dọc cho trang A4, khác F11 nằm ngang do `scripts/13_extended_rq3_analysis.py` tạo; cặp tháng và giá trị lấy cùng bảng. |
| 11 | `docs/report_repro/H11_suspect_sensitivity.png` | `docs/report_repro/render_report_specific.py`; `T05_correlation_results.csv`, `T07_sensitivity.csv`, `T08_alternative_suspect_sensitivity.csv`. Bố cục riêng từ các hệ số đã rà soát. |
| 12 | `docs/report_repro/final_numbered_charts/F10_inflow_distribution.png` | `render_final_numbered_charts.py` → `scripts/06_exploratory_analysis.py`; ngày lưu lượng `VALID` |

Các đường dẫn CSV ngắn trong bảng ở `handoff_writer/selected_data/` hoặc `handoff_writer/tables/`. Bảng độ nhạy mưa bổ sung ở `outputs/quality/rainfall_spatial_sensitivity.csv`. Các PNG trong thư mục này được giữ lại để nhận diện chính xác hình đã nhúng dù môi trường Matplotlib sau này thay đổi. `engine/06_exploratory_analysis.py` và `engine/07_rainfall_runoff_analysis.py` là bản chụp mã vẽ đúng thời điểm tạo hình; chỉ đổi biến `ROOT` để chạy từ vị trí này. Các script phân tích chính của nhóm vẫn ở `scripts/`.

Từ gốc repository, có thể tạo lại những hình riêng của báo cáo bằng:

```powershell
python docs/report_repro/render_report_specific.py
python docs/report_repro/generate_report_F11.py
python docs/report_repro/render_final_numbered_charts.py
```

`render_final_numbered_charts.py` dùng bản chụp mã vẽ trong `engine/` và chỉ sửa số hình hiển thị để khớp chú thích Word; các phép thống kê vẫn lấy từ CSV của đề tài. Để tái lập **toàn bộ pipeline từ nguồn thô**, cần thêm raster CHIRPS, phản hồi API Open-Meteo, và raw HTML/CSV thủy văn cùng metadata; các tệp raw này chưa được bàn giao đầy đủ trong repository.
