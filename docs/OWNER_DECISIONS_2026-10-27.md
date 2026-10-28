# Quyết định nghiệm thu của trưởng nhóm — 27/10/2026

Các quyết định này do trưởng nhóm trực tiếp xác nhận trong cuộc trò chuyện; **không phải phê duyệt cuối toàn bộ dự án**.

| Hạng mục | Quyết định | Trạng thái |
|---|---|---|
| Polygon HydroBASINS 11.160,6 km² | Chấp nhận có điều kiện làm đại diện xấp xỉ; công bố sai lệch 0,41% và nguồn OSM | CONDITIONAL_ACCEPTED |
| Phương pháp mưa CHIRPS | **Chấp nhận có điều kiện** chuỗi mưa và phương pháp xấp xỉ hiện tại cho bài tiểu luận; công bố sai lệch và giới hạn tái lập 377/379 pixel, không công nhận như fractional-area chính xác | CONDITIONAL_ACCEPTED |
| Lưu lượng SUSPECT | Giữ hai kịch bản (lọc theo QA và giữ giá trị nguồn để thử độ nhạy) | APPROVED_TWO_SCENARIOS |
| main & bàn giao | Giữ nguyên main, chờ nghiệm thu cuối | HOLD_FINAL_APPROVAL |

## Đầu ra định lượng đã có
Hai hệ số chính Pearson từ `hydromet_monthly.csv`: lag0 = 0,5856 (36 cặp), lag1 = 0,6147 (35 cặp).
Kịch bản giữ cả ngày SUSPECT: lag0 = 0,5409, lag1 = 0,4839. Bảng và script: `handoff_writer/tables/T08_alternative_suspect_sensitivity.csv`, `scripts/10_suspect_sensitivity.py`.

## Kiểm tra định lượng CHIRPS sau khi trưởng nhóm chạy script 09

- Đầu vào: 36 GeoTIFF tháng giai đoạn 2023–2025 do trưởng nhóm tải lại, kiểm tra bằng script `09_rainfall_spatial_sensitivity.py`; bằng chứng CSV được lưu tại `outputs/quality/rainfall_spatial_sensitivity.csv`.
- So sánh pixel-center + cos(vĩ độ) với diện tích giao pixel–polygon: sai lệch tương đối tuyệt đối trung bình **0,4477%**, lớn nhất **1,3952%**; sai lệch tuyệt đối trung bình **0,5048 mm/tháng**, lớn nhất **1,8321 mm**.
- Tổng năm theo phương pháp diện tích giao: 2023 **1930,149 mm**, 2024 **1620,890 mm**, 2025 **2122,989 mm**. Tổng năm từ chuỗi của Huy: **1933,58**, **1625,91**, **2125,58 mm** tương ứng.
- 36 tháng tính lại từ raster chọn **379** pixel tâm ô, chuỗi mưa tháng bàn giao trước ghi **377** pixel. Sai khác lượng mưa giữa chuỗi bàn giao và kết quả tính lại theo tâm pixel: trung bình tuyệt đối **0,4232 mm/tháng**, cực đại **1,6468 mm**; chưa xác định dứt điểm nguyên nhân. Không tuyên bố tái lập hoàn toàn dữ liệu nguồn.
- Với lưu lượng `VALID_ONLY`: Pearson lag 0 từ **0,585573** (chuỗi Huy) sang **0,591432** (mưa diện tích giao), lag 1 từ **0,614721** sang **0,616264**.
- Với lưu lượng `INCLUDE_SUSPECT_AS_REPORTED`: Pearson lag 0 từ **0,540892** sang **0,547011**, lag 1 từ **0,483878** sang **0,486132**. Không kết luận lag 1 tốt hơn lag 0 một cách bền vững.

**Quyết định trưởng nhóm sau xem số liệu:** Chấp nhận **có điều kiện** cách tính mưa hiện tại của Huy là phương pháp xấp xỉ đủ dùng cho tiểu luận Nhập môn KHDL, không yêu cầu tính lại toàn bộ bộ dữ liệu. Việc này được giới hạn vào trường hợp nghiên cứu 2023–2025, không xác nhận phương pháp xấp xỉ bằng phép tính diện tích giao chính xác. Kết quả sai số phải xuất hiện trong giới hạn phương pháp và phần thảo luận. **Không phải phê duyệt nghiệm thu cuối hay cho phép merge PR #9.**

## Các vấn đề tồn tại
- `gate2_approval.json` đã sửa rõ phạm vi CHẤP NHẬN CÓ ĐIỀU KIỆN; không lấy trạng thái `approved:true` trong tệp đó làm chứng nhận nghiệm thu cuối.
- Các ngày mực nước nghi đảo cột đã được chạy lại từ raw và gắn `SUSPECT` (không phải `INVALID_CONFIRMED`); chưa xác minh nguyên nhân với nguồn độc lập.
- Dữ liệu mưa tháng đã được trưởng nhóm tải lại để chạy phép so sánh, nhưng nguyên bộ raw HTML/ERA5-Land chưa được tái lập end-to-end.
- Đã chạy lại GATE1, GATE4, GATE5a/b và GATE6 từ máy trưởng nhóm, cập nhật T01–T08, F01–F10 và `handoff_writer/` trên nhánh review; commit sản phẩm cuối của vòng chỉnh metadata là `5d10df9`. GATE3 dùng bộ khí tượng đã bàn giao, không tái lập toàn bộ từ raw trong vòng này.

**Cập nhật tiến độ 28/10/2026:** Bộ dữ liệu/kết quả có thể dùng làm **nguồn tham khảo kỹ thuật có điều kiện** cho người viết sau khi xác nhận nơi làm việc và tránh ghi đè; không gọi là nghiệm thu toàn đề tài. **Chưa merge nhánh review vào `main`** cho đến khi trưởng nhóm xác nhận người viết đã lưu an toàn các thay đổi và phê duyệt tích hợp.
