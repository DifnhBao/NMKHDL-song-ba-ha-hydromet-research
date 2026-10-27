# 05 — Giới hạn của nghiên cứu

## 1. Giới hạn thời gian

- Chỉ có **36 tháng / 1096 ngày** (2023–2025). Không đủ để mô tả
  chu kỳ nhiều năm, ENSO hoặc xu thế khí hậu dài hạn.
- Cỡ mẫu cho tương quan tháng là 36 cặp (lag 0) và
  35 cặp (lag 1) — nhỏ, hệ số kém ổn định.

## 2. Giới hạn dữ liệu khí tượng

- CHIRPS là sản phẩm **ước lượng từ vệ tinh kết hợp trạm**, không phải đo trực tiếp
  tại lưu vực. Sai số lớn hơn ở địa hình núi và mùa khô.
- Mưa ngày CHIRPS v3 `rnl` được **phân rã từ tổng 5 ngày** bằng ERA5, nên không
  phù hợp để phân tích sự kiện trong ngày; chỉ dùng bổ trợ.
- Độ phân giải 0,05° (~5,5 km) làm trơn cực trị cục bộ.
- ERA5-Land là **tái phân tích**, không phải quan trắc; độ phân giải 0,1° (~9 km).
  Nhiệt độ đại diện ô lưới, không đại diện vi khí hậu tại công trình.
- Kênh truy cập nhiệt độ thực tế: **Open-Meteo Archive API (models=era5_land)**. Đây là cùng sản phẩm ERA5-Land
  nhưng khác kênh phân phối so với Copernicus CDS.
- Kênh tải mưa thực tế: **FTP (ftp.chc.ucsb.edu — cùng máy chủ CHC, HTTPS đang bị chặn)**.
- Dữ liệu toàn cầu theo UTC, dữ liệu công trình theo UTC+7 → có thể lệch ngày
  ở vùng biên.

## 3. Giới hạn dữ liệu thủy văn

- Lưu lượng "về hồ" là số liệu vận hành, **không phải dòng chảy tự nhiên**;
  chịu điều tiết của các hồ thượng nguồn (An Khê, Ka Nak, Sông Ba Hạ).
- Định nghĩa chính xác của trường `inflow_m3s` chưa được xác minh từ tài liệu
  công trình; có thể là lưu lượng vào hồ hoặc tổng lượng qua nhà máy.
- 32 bản ghi SUSPECT và
  3 bản ghi INVALID_CONFIRMED.
  Hai ngày 19–20/11/2025 có giá trị 12.455 m³/s chưa được xác minh độc lập.
- Mực nước thượng lưu có lỗi cảm biến/nhập liệu (0 m; 37–38 m; đảo cột) —
  đã loại khỏi phép tính nhưng làm giảm số ngày hợp lệ.
- Trường `release_m3s` (lưu lượng xả) bằng 0 trong **893/1096 ngày**
  — bất thường về mặt vận hành; biến này chỉ dùng bổ trợ và chưa được xác minh
  định nghĩa, không dùng trong phân tích chính.

## 4. Giới hạn không gian

- Polygon HydroBASINS level 12 có diện tích 11.160,6 km²,
  lệch 0,41% so với tham khảo. Ranh giới là đơn vị
  thủy văn toàn cầu, không phải khảo sát địa hình chi tiết.
- Tọa độ đập lấy từ OpenStreetMap (nguồn cộng đồng), đã đối chiếu với vị trí
  polygon nhưng chưa khảo sát thực địa.
- Trạm đo mưa/khí tượng không nằm trong lưu vực; toàn bộ là trung bình không gian.

## 5. Giới hạn phương pháp

- Tương quan Pearson/Spearman **không chứng minh nhân quả**; tính mùa chung của
  mưa và lưu lượng có thể thổi phồng hệ số. Đã bổ sung deseasonalised và phân
  nhóm mùa để kiểm tra, nhưng mỗi tháng lịch chỉ có 3 giá trị.
- Hồi quy/thời gian trễ thực không được mô hình hóa.
- **Không xây dựng Flow Duration Curve (FDC)**: chuỗi lưu lượng là số liệu vận hành
  bị điều tiết, chưa xác minh định nghĩa và còn 4 ngày SUSPECT. Theo V1.1 §13,
  FDC chỉ được xây dựng khi định nghĩa và chất lượng chuỗi cho phép diễn giải có
  cơ sở; thay vào đó dùng F10 (phân bố lưu lượng) để mô tả hình dạng phân bố.
- Phân nhóm tercile chỉ có ~12 tháng/nhóm; hệ số rất bất ổn, không dùng để khẳng
  định ngưỡng mưa – dòng chảy.

## 6. Những vấn đề chưa xác minh được

| Vấn đề | Trạng thái |
|---|---|
| Định nghĩa `inflow_m3s` của công trình | Chưa có tài liệu gốc |
| Giá trị 12.455 m³/s ngày 19–20/11/2025 | Chưa đối chiếu được nguồn độc lập |
| Ngày 21/01/2023 có lưu lượng 0 nhưng sản lượng điện dương | Đã gắn cờ SUSPECT |
| Sai lệch mưa tháng vs tổng ngày | Đã định lượng, chưa hiệu chỉnh |
| Phê duyệt GATE 2 | APPROVED (Người giám sát dự án (xác nhận trực tiếp trong phiên làm việc), 2026-10-27) |
