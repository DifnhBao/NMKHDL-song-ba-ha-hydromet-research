# 01 — Tổng quan dự án

## 1. Thông tin chung

| Hạng mục | Nội dung |
|---|---|
| Đề tài | Nghiên cứu dữ liệu khí tượng thủy văn, xử lý và trực quan hóa dữ liệu, rút ra ý nghĩa |
| Trường hợp nghiên cứu | Lưu vực sông Ba đến công trình thủy điện Sông Ba Hạ |
| Thời gian | 01/01/2023 – 31/12/2025 (1096 ngày, 36 tháng) |
| Vị trí công trình | Đập: 13,0236°N, 108,9039°E; nhà máy: 13,0653°N, 108,9129°E |
| Diện tích lưu vực | 11.160,6 km² (Albers), lệch 0,41% so với 11.115 km² tham khảo |
| Tính chất | Phân tích dữ liệu khám phá (EDA); không chứng minh nhân quả, không xây dựng mô hình dự báo vận hành hồ |

## 2. Mục tiêu nghiên cứu

1. Hệ thống hóa các loại dữ liệu khí tượng, thủy văn cùng phương pháp thu thập, đặc điểm và hạn chế.
2. Thu thập, kiểm tra chất lượng, xử lý và trực quan hóa dữ liệu thực tế trên lưu vực giai đoạn 2023–2025.
3. Khảo sát mối liên hệ thống kê giữa lượng mưa trên lưu vực và lưu lượng nước về hồ, đặt trong bối cảnh đặc điểm lưu vực và điều tiết thượng nguồn.

## 3. Câu hỏi nghiên cứu

**RQ1 — Khí tượng:** Lượng mưa, nhiệt độ và tính mùa của chúng tại lưu vực nghiên cứu biến động như thế nào trong giai đoạn 2023–2025?

**RQ2 — Thủy văn:** Lưu lượng nước về hồ và mực nước thay đổi như thế nào theo ngày, tháng, năm; có những thời kỳ hoặc sự kiện nổi bật nào?

**RQ3 — Kết hợp:** Lượng mưa trên lưu vực và lưu lượng nước về hồ có mối liên hệ thống kê như thế nào? Mối liên hệ có khác nhau theo mùa hoặc khi xét độ trễ thời gian hay không?

## 4. Phạm vi và đơn vị

| Nhóm | Biến | Đơn vị | Vai trò |
|---|---|---|---|
| Khí tượng | Lượng mưa trung bình lưu vực | mm/tháng, mm/ngày | Bắt buộc |
| Khí tượng | Nhiệt độ không khí 2 m | °C | Bắt buộc |
| Thủy văn | Lưu lượng nước về hồ | m³/s | Bắt buộc |
| Thủy văn | Mực nước thượng lưu | m | Bắt buộc, sau kiểm định |
| Thủy văn | Mực nước hạ lưu | m | Bổ trợ |
| Không gian | Ranh giới lưu vực | — | Bắt buộc |

## 5. Sản phẩm bàn giao

- Dữ liệu đã xử lý: `handoff_writer/selected_data/`
- Hình: F01–F10 (`handoff_writer/figures/`)
- Bảng: T01–T07 (`handoff_writer/tables/`)
- Thuyết minh: 01–07 (thư mục này)
- Mã nguồn tái lập: `scripts/01`–`08`, `run_all.py`

> Lưu ý: Mọi số liệu trong bộ tài liệu này được sinh tự động từ CSV đầu ra
> bằng `scripts/08_write_handoff.py`. Không sửa tay số liệu khi viết báo cáo.
