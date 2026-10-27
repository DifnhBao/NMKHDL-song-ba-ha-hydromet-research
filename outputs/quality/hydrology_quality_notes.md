# Báo cáo kiểm tra chất lượng dữ liệu thủy văn

**Nguồn dữ liệu:** Website Sông Ba Hạ (sbh.vn)
**Giai đoạn:** 01/01/2023 – 31/12/2025 (1.096 ngày lịch)
**Script:** `scripts/01_hydrology_qa.py`

## 1. Kiểm tra cấu trúc

- ✅ Đúng 1.096 ngày, 01/01/2023 – 31/12/2025, không trùng, liên tục.

## 2. Tổng hợp ngoại lệ

- Tổng số bản ghi ngoại lệ: **35**
  - SUSPECT: 32
  - INVALID_CONFIRMED: 3

## 3. Danh sách ngày bắt buộc đối chiếu

| Ngày | Vấn đề | Cờ |
|---|---|---|
| 2023-01-21 | Lưu lượng về hồ bằng 0 | SUSPECT |
| 2023-01-21 | Mực nước thượng lưu bằng 0 | SUSPECT |
| 2023-01-14 | Mực nước thượng lưu ngoài khoảng [85.0, 116.5] m | SUSPECT |
| 2023-02-19 | Mực nước thượng lưu ngoài khoảng [85.0, 116.5] m | SUSPECT |
| 2023-05-31 | Mực nước thượng lưu ngoài khoảng [85.0, 116.5] m | SUSPECT |
| 2024-04-09 | Mực nước thượng lưu ngoài khoảng [85.0, 116.5] m | SUSPECT |
| 2024-09-09 | Mực nước thượng lưu ngoài khoảng [85.0, 116.5] m | SUSPECT |
| 2023-01-14 | Biến động mực nước đột ngột: 35.97 m/ngày | SUSPECT |
| 2023-02-19 | Biến động mực nước đột ngột: 66.70 m/ngày | SUSPECT |
| 2023-05-31 | Biến động mực nước đột ngột: 65.08 m/ngày | SUSPECT |
| 2024-04-09 | Biến động mực nước đột ngột: 66.53 m/ngày | SUSPECT |
| 2024-09-09 | Biến động mực nước đột ngột: 64.39 m/ngày | SUSPECT |
| 2023-01-21 | Mực nước hạ lưu bằng 0 | SUSPECT |
| 2023-05-31 | Mực nước hạ lưu bằng 0 | SUSPECT |
| 2024-09-09 | Mực nước hạ lưu bằng 0 | SUSPECT |
| 2023-02-19 | Mực nước thượng lưu nhỏ hơn hạ lưu — nghi đảo cột | INVALID_CONFIRMED |
| 2024-04-09 | Mực nước thượng lưu nhỏ hơn hạ lưu — nghi đảo cột | INVALID_CONFIRMED |
| 2024-02-03 | Công suất 707.0 MW vượt thiết kế 220 MW | INVALID_CONFIRMED |
| 2023-01-21 | Công suất bằng 0 | SUSPECT |
| 2023-01-14 | Mực nước 140,30 m vượt xa mực nước dâng bình thường 111,5 m — có thể lỗi nhập li | SUSPECT |
| 2023-01-21 | Nhiều biến thủy văn bằng 0 nhưng sản lượng điện dương — có thể thiếu dữ liệu | SUSPECT |
| 2023-05-31 | Mực nước hạ lưu bằng 0 — bất thường; mực nước thượng lưu cũng bất thường (38,4 m | SUSPECT |
| 2024-09-09 | Mực nước thượng lưu 38.6 m — bất thường, ngoài phạm vi vận hành | SUSPECT |
| 2025-11-19 | Lưu lượng cực lớn 12455.0 m³/s — cần kiểm tra định nghĩa và nguồn; không loại bỏ | SUSPECT |
| 2025-11-20 | Lưu lượng cực lớn 12455.0 m³/s — cần kiểm tra định nghĩa và nguồn; không loại bỏ | SUSPECT |

## 4. Kiểm tra sản lượng điện

- ✅ Sản lượng ngày và lũy kế tháng nhất quán.

## 5. Trạng thái tháng

- ✅ Tất cả 36 tháng đạt ≥ 90% ngày lưu lượng hợp lệ.

## 6. Quy tắc xử lý đã áp dụng

- Không tự động xóa, nội suy hoặc sửa bất kỳ giá trị nào.
- Mỗi biến có cờ chất lượng riêng: VALID, SUSPECT, MISSING, INVALID_CONFIRMED, CORRECTED.
- Lưu lượng cực lớn 19–20/11/2025 được giữ nguyên và gắn cờ SUSPECT.
- Giá trị bằng 0 không tự thay bằng NaN.
- Dữ liệu gốc không bị thay đổi.

## 7. Giới hạn

- Chưa xác minh được ý nghĩa thời gian chính xác của lưu lượng công bố (trung bình ngày hay giá trị tại thời điểm xác định).
- Các ngày nghi đảo cột (19/02/2023, 09/04/2024) được đánh dấu INVALID_CONFIRMED dựa trên bằng chứng up < down.
- Công suất 707 MW ngày 03/02/2024 vượt thiết kế; nghi lỗi nhập liệu.
