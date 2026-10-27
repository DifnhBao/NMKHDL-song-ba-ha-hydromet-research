# 02 — Nguồn dữ liệu và phương pháp

## 1. Danh mục nguồn dữ liệu (T01)

| variable | source | type | spatial_resolution | temporal_resolution | period | notes |
|---|---|---|---|---|---|---|
| Lưu lượng nước về hồ (m³/s) | Website Sông Ba Hạ (sbh.vn) | Số liệu công trình | Điểm (tại đập) | Ngày | 2023-01 – 2025-12 | Chưa xác minh ý nghĩa thời gian (trung bình ngày vs tức thời) |
| Mực nước thượng/hạ lưu (m) | Website Sông Ba Hạ (sbh.vn) | Số liệu công trình | Điểm | Ngày | 2023-01 – 2025-12 | Một số ngày nghi đảo cột; đã gắn cờ INVALID_CONFIRMED |
| Lượng mưa lưu vực (mm) | CHIRPS v3.0 Final monthly | Vệ tinh kết hợp quan trắc | ~0.05° (~5 km) | Tháng (P0), Ngày rnl (P1) | 2023-01 – 2025-12 | Mưa ngày phân rã từ tổng 5 ngày bằng ERA5; trung bình có trọng số diện tích trên polygon lưu vực |
| Nhiệt độ không khí 2m (°C) | ERA5-Land via Open-Meteo Archive API (mean of daily means) | Tái phân tích | ~0.1° (~9 km) | Tháng (P0), Ngày (P1) | 2023-01 – 2025-12 | Trạng thái dữ liệu: OK |
| Ranh giới lưu vực | HydroBASINS v1c (HydroSHEDS/WWF) | Dữ liệu địa lý toàn cầu | ~15 arc-second | Tĩnh | — | Diện tích tham khảo 11.115 km²; cửa ra theo OSM way/480785944 |

## 2. Dữ liệu thủy văn — Sông Ba Hạ

- Nguồn: trang thông tin vận hành của công trình Thủy điện Sông Ba Hạ.
- Giai đoạn: 01/01/2023 – 31/12/2025, 1096 dòng ngày, không trùng ngày.
- Bản gốc được giữ nguyên tại `data/raw/hydrology/`; dữ liệu xử lý ở
  `data/processed/hydrology_clean.csv` kèm cột chất lượng cho từng biến.
- Quy ước: mỗi dòng là một ngày dương lịch; giá trị 0 không tự động được coi
  là giá trị thật — xem mục ngoại lệ.

## 3. Ranh giới lưu vực — HydroBASINS v1c level 12

- Nguồn: HydroBASINS v1c (Lehner & Grill, 2013), cấp 12, hệ tọa độ EPSG:4326.
- Xác định cửa ra: chọn đơn vị thủy văn **chứa** tọa độ đập
  (13,0236°N, 108,9039°E) —
  phương pháp `contains`, không chọn theo chênh lệch diện tích.
- Tọa độ đập lấy từ OpenStreetMap `way/480785944` (Đập thủy điện Sông Ba Hạ);
  nhà máy `way/827889670` — cả hai đều nằm trong polygon.
- Kết quả: `HYBAS_ID = 4121132660`, 82 tiểu lưu vực,
  diện tích Albers **11.160,6 km²**, lệch
  **0,41%** so với diện tích tham khảo
  11.115 km².
- Kiểm tra: `dam_inside_polygon = True`,
  `powerhouse_inside_polygon = True`,
  `geometry_valid = True`.
- Trạng thái phê duyệt: **CONDITIONAL** — chấp nhận polygon có điều kiện, không phải nghiệm thu toàn bộ đề tài.

Chi tiết quy trình: `outputs/quality/basin_method.md`; bằng chứng số:
`data/processed/basin_validation.csv`.

## 4. Lượng mưa — CHIRPS v3.0 Final

- Sản phẩm: CHIRPS v3.0 Final (Climate Hazards Center, UC Santa Barbara).
- Kênh tải thực tế: **FTP (ftp.chc.ucsb.edu — cùng máy chủ CHC, HTTPS đang bị chặn)**.
  Máy chủ `data.chc.ucsb.edu` trả HTTP 403 cho dải IP sử dụng; FTP là cùng máy
  chủ CHC, cùng sản phẩm và cùng phiên bản.
- Độ phân giải: 0,05° (~5,5 km); tháng: sản phẩm monthly; ngày: sản phẩm `rnl`.
- Phương pháp tổng hợp không gian: cắt raster theo polygon lưu vực, loại pixel
  nodata (-9999), trung bình **xấp xỉ** theo pixel được mask chọn,
  có trọng số cos(vĩ độ): `P_t ≈ Σ(cos(lat_i)P_i,t)/Σ(cos(lat_i))`.
  **Không** tính phần diện tích giao raster–polygon ở các pixel biên.
- Số pixel dùng cho mưa tháng: 377; mưa ngày:
  379.
- Không thay dữ liệu thiếu bằng 0.
- Chi tiết: `outputs/quality/rainfall_extraction_method.md`.

## 5. Nhiệt độ — ERA5-Land

- Sản phẩm: ERA5-Land 2 m temperature (ECMWF/Copernicus).
- Kênh truy cập thực tế: **Open-Meteo Archive API (models=era5_land)**.
- Số điểm lưới 0,1° nằm trong lưu vực: **95** (chỉ dùng điểm có tâm
  nằm trong polygon, trọng số cos(vĩ độ)).
- Nhiệt độ tháng = trung bình các ngày có dữ liệu trong tháng (khi kênh truy
  cập không cung cấp sản phẩm monthly).
- Đơn vị: °C; dữ liệu theo UTC.
- Chi tiết: `outputs/quality/temperature_method.md`.

## 6. Quy tắc tích hợp (V1.1 §11)

| Quy tắc | Thực hiện |
|---|---|
| Khóa thời gian | `date` (YYYY-MM-DD) cho bảng ngày, `year_month` (YYYY-MM) cho bảng tháng |
| Không trùng khóa | Đã kiểm tra, 0 bản ghi trùng |
| Số ngày hợp lệ | `rainfall_valid_days`, `temperature_valid_days`, `inflow_valid_days` tính từ dữ liệu ngày thực tế |
| Độ phủ | `*_coverage_pct` = số ngày hợp lệ / số ngày trong tháng |
| Cờ chất lượng | `rainfall_quality`, `temperature_quality`, `inflow_quality`, `level_quality` |
| Tổng hợp tháng | Mưa: tổng; nhiệt độ, lưu lượng, mực nước: trung bình các ngày VALID |
| Phân tích chính | Dùng bảng tháng; bảng ngày chỉ bổ trợ |

## 7. Quy ước thời gian và đơn vị

- Ngày dương lịch theo giờ Việt Nam (UTC+7) cho dữ liệu công trình.
- ERA5-Land và CHIRPS là sản phẩm toàn cầu theo UTC; khi ghép với dữ liệu
  công trình có thể lệch tối đa một ngày ở vùng biên.
- Đơn vị: mưa mm, nhiệt độ °C, lưu lượng m³/s, mực nước m, điện năng kWh.

## 8. Mã nguồn tái lập

| Script | Nội dung |
|---|---|
| `scripts/01_hydrology_qa.py` | GATE 1 — QA thủy văn, ngoại lệ |
| `scripts/02_basin_delineation.py` | GATE 2 — ranh giới lưu vực, F01 |
| `scripts/03_chirps_extraction.py` | GATE 3a — mưa CHIRPS |
| `scripts/04_temperature_extraction.py` | GATE 3b — nhiệt độ ERA5-Land |
| `scripts/05_data_integration.py` | GATE 4 — bảng ngày/tháng |
| `scripts/06_exploratory_analysis.py` | GATE 5a — RQ1, RQ2 |
| `scripts/07_rainfall_runoff_analysis.py` | GATE 5b — RQ3 |
| `scripts/08_write_handoff.py` | GATE 6 — sinh tài liệu bàn giao |
| `run_all.py` | Điều phối toàn bộ pipeline |


## Lưu ý nghiệm thu không gian
Polygon CHẤP NHẬN CÓ ĐIỀU KIỆN. Trưởng nhóm đã CHẤP NHẬN CÓ ĐIỀU KIỆN phương pháp tính mưa xấp xỉ mask pixel nhị phân và cos(vĩ độ) cho bài tiểu luận. Phương pháp này không tính phần giao các ô biên. Kiểm tra 36 tháng với trọng số diện tích giao: trung bình |Δ%|=0.4477%, lớn nhất |Δ%|=1.3952%. Chuỗi cũ dùng [377] pixel, tái tính dùng [379]; chưa xác định dứt điểm nguyên nhân. Xem outputs/quality/rainfall_spatial_sensitivity.csv.
