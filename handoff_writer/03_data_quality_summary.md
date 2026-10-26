# 03 — Tóm tắt chất lượng dữ liệu

## 1. Dữ liệu thủy văn

### Cấu trúc
- **Số ngày:** 1.096 ngày lịch (01/01/2023 – 31/12/2025)
- **Trùng ngày:** Không
- **Tính liên tục:** Đầy đủ, không thiếu ngày

### Trạng thái QA cho từng biến

Mỗi biến có cờ chất lượng riêng theo quy tắc V1.1 §6:

| Trạng thái | Định nghĩa |
|---|---|
| VALID | Hợp lệ theo các kiểm tra |
| SUSPECT | Nghi vấn, chưa xác minh |
| MISSING | Không có dữ liệu thực |
| INVALID_CONFIRMED | Xác nhận sai bằng bằng chứng |
| CORRECTED | Hiệu chỉnh có căn cứ (giữ cả gốc) |

Kết quả chi tiết: xem `outputs/tables/T02_hydrology_qa_results.csv`

### Các ngày ngoại lệ bắt buộc đối chiếu

| Ngày | Vấn đề |
|---|---|
| 14/01/2023 | Mực nước thượng lưu 140,30 m (vượt xa bình thường) |
| 19/02/2023 | Nghi đảo cột: upstream 37.2 < downstream 103.91 |
| 21/01/2023 | Tất cả biến thủy văn = 0 nhưng sản lượng điện dương |
| 31/05/2023 | Mực nước hạ lưu = 0, thượng lưu bất thường |
| 03/02/2024 | Công suất 707 MW (thiết kế: 220 MW) |
| 09/04/2024 | Nghi đảo cột: upstream 37.2 < downstream 103.72 |
| 09/09/2024 | Mực nước thượng lưu 38.6 m (ngoài phạm vi vận hành) |
| 19–20/11/2025 | Lưu lượng 12.455 m³/s (cực lớn, giữ nguyên + gắn cờ) |

### Quyết định xử lý
- **Không** tự động xóa, nội suy hoặc sửa bất kỳ giá trị nào
- Ngày đảo cột: INVALID_CONFIRMED (không dùng trong tính toán chính)
- Công suất 707 MW: INVALID_CONFIRMED
- Lưu lượng 19–20/11/2025: SUSPECT (giữ nguyên, có thể là sự kiện lũ thực)
- Ngày 21/01/2023 (tất cả = 0): SUSPECT
- Giá trị bằng 0 không tự động thay bằng NaN

### Ảnh hưởng đến độ tin cậy
- Các tháng có < 90% ngày lưu lượng hợp lệ → gắn LOW_COVERAGE, không đưa vào tương quan chính
- Kết quả thống kê chỉ tính từ dữ liệu VALID hoặc CORRECTED

## 2. Dữ liệu khí tượng

### Lượng mưa CHIRPS
- 36 tháng (01/2023 – 12/2025)
- Trung bình có trọng số diện tích cho toàn lưu vực
- Kiểm tra: so sánh tổng mưa ngày vs sản phẩm mưa tháng

### Nhiệt độ ERA5-Land
- 36 tháng nhiệt độ trung bình tháng
- Chuyển đổi K → °C
- Dữ liệu theo UTC (ghi rõ trong metadata)

## 3. Dữ liệu tích hợp

- Bảng ngày: 1.096 dòng, cờ QA riêng từng biến
- Bảng tháng: 36 dòng, có số ngày hợp lệ và tỷ lệ phủ
- Không sử dụng 0 thay cho giá trị thiếu
- Không dịch thời gian khi ghép dữ liệu

Chi tiết: xem `outputs/quality/data_dictionary.md`
