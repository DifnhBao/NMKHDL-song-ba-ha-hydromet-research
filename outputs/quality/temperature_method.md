# Phương pháp trích xuất nhiệt độ ERA5-Land

## 1. Nguồn dữ liệu

- **Sản phẩm:** ERA5-Land (ECMWF), truy vấn qua Open-Meteo
- **Biến:** 2m temperature (t2m)
- **Loại:** Dữ liệu tái phân tích (reanalysis)
- **Độ phân giải không gian:** ~9 km (0,1°)
- **Đơn vị gốc:** Kelvin (K) khi tải qua CDS; °C khi truy vấn Open-Meteo
- **Kênh truy cập:** Open-Meteo Archive API (models=era5_land)

## 2. Phạm vi

- **Thời gian:** 01/2023 – 12/2025 (36 tháng)
- **Không gian:** Lưu vực sông Ba đến thủy điện Sông Ba Hạ
- **Ranh giới:** song_ba_ha_catchment.geojson (đã phê duyệt bởi Người giám sát dự án (xác nhận trực tiếp trong phiên làm việc))
- **Số điểm lưới dùng để lấy trung bình:** 95

## 3. Phương pháp

### Nhiệt độ tháng (P0)
- Sử dụng ERA5-Land monthly averaged reanalysis khi tải qua CDS; khi dùng
  Open-Meteo, nhiệt độ tháng là trung bình có trọng số của các ngày trong tháng.
- Chỉ dùng các ô lưới có tâm nằm trong polygon lưu vực.
- Trung bình có trọng số cos(vĩ độ) theo diện tích ô lưới.
- Chuyển đổi: T(°C) = T(K) − 273,15 (khi nguồn là Kelvin).

### Nhiệt độ ngày (P1)
- Giá trị trung bình ngày (`daily=temperature_2m_mean`) do Open-Meteo tổng hợp
  từ ERA5-Land hourly theo múi giờ UTC.
- Chỉ dùng các ô lưới trong polygon lưu vực, trọng số cos(vĩ độ).

## 4. Lưu ý

- Dữ liệu ERA5-Land theo UTC, không hoàn toàn trùng ngày quan trắc tại công trình (UTC+7).
- Không sử dụng nhiệt độ bề mặt đất (skin temperature) — chỉ dùng 2m temperature.
- Dữ liệu là tái phân tích, khác với quan trắc trực tiếp.
- Nếu kênh truy cập không phải CDS, đây là khác biệt về kênh phân phối
  (cùng sản phẩm ERA5-Land) và phải được ghi rõ trong báo cáo.

## 5. Trạng thái dữ liệu

- Nhiệt độ tháng: 36/36 tháng có dữ liệu.
- Nhiệt độ ngày: 1096/1096 ngày có dữ liệu.

## 6. Đầu ra

- `temperature_monthly.csv`: Nhiệt độ trung bình tháng (°C)
- `temperature_daily.csv`: Nhiệt độ trung bình ngày (°C) — P1
