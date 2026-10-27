# Trạng thái thực thi vòng QA sau quyết định của trưởng nhóm — 27/10/2026

**Trạng thái:** CHƯA NGHIỆM THU CUỐI — nhánh `review/conditional-qa-20261027`, PR #9 Draft; `main` giữ nguyên.

## Đã thay đổi trên nhánh review
1. README và `basin_method.md`: bỏ thông tin "100% passed / end-to-end verified / polygon được duyệt hoàn toàn", thay bằng trạng thái chấp nhận có điều kiện.
2. `gate2_approval.json`: ghi điều kiện theo quyết định trưởng nhóm. `run_all.py` / `03_chirps_extraction.py` phân biệt quyền tiếp tục xử lý polygon với phê duyệt kết quả cuối.
3. `01_hydrology_qa.py`: mực nước thượng lưu thấp hơn hạ lưu chỉ `SUSPECT` (nghi đảo cột), chưa dùng `INVALID_CONFIRMED` nếu thiếu bằng chứng độc lập. **Đã chạy lại GATE1 từ raw 1.096 ngày và tái xuất T02/T02b/T06, hình F02–F10 trên nhánh review; main vẫn thuộc lần chạy cũ.**
4. `10_suspect_sensitivity.py`: kịch bản VALID và kịch bản giữ SUSPECT, lấy đầu vào `data/processed` khi có; nếu không thì từ `handoff_writer/selected_data`. `run_all.py` gọi script này trước khi tạo tài liệu GATE6.
5. `08_write_handoff.py`: tự đọc bảng T08 để bổ sung kết quả độ nhạy; không khóa cứng giá trị hệ số vào phần phụ lục. Sửa định dạng xuống dòng và mô tả phương pháp mưa.
6. `09_rainfall_spatial_sensitivity.py`: phương pháp đo sai số pixel-center/cos(lat) so với fractional area trên 36 CHIRPS GeoTIFF tháng **nguyên bản**; đã được trưởng nhóm chạy đủ 36 raster tháng; bảng kiểm tra đã đưa lên `outputs/quality/rainfall_spatial_sensitivity.csv`.

## Quy trình nghiệm thu kỹ thuật tiếp theo (theo thứ tự)
- [x] Trưởng nhóm đã tải đủ 36 GeoTIFF CHIRPS tháng và chạy script 09; kết quả CSV đã được lưu vào nhánh review. Việc đối chiếu metadata/raw đầy đủ vẫn là giới hạn của kiểm tra.
- [ ] Kiểm tra script 09 trên raster nhỏ tổng hợp có lời giải dự kiến, rồi chạy 36 tháng. Kiểm tra đầu ra sai số mm/% từng tháng, tổng năm và ảnh hưởng tới RQ1, RQ3.
- [x] Trưởng nhóm chấp nhận **có điều kiện** phương pháp mưa xấp xỉ, sau khi xem sai số tương đối tuyệt đối trung bình 0,4477%, tối đa 1,3952%; kết luận Pearson không thay đổi đáng kể. Số pixel 377/379 chưa giải thích hoàn toàn.
- [x] Đã chạy GATE1 với raw 1.096 ngày; các ngày nghi đảo cột giữ SUSPECT, tổng 35 lượt ngoại lệ; chạy lại GATE4, GATE5a/b.
- [x] Đã chạy script 10, bảng T08 có hệ số VALID_ONLY 0,585573/0,614721 và INCLUDE_SUSPECT 0,540892/0,483878.
- [ ] Chạy GATE6, kiểm tra toàn bộ các hình F01–F10, bảng T01–T08, bảy tài liệu chính và các ghi chú reviewer; không xuất hiện \n nguyên văn trong Markdown.
- [ ] Sửa mọi số liệu/nhận xét cũ sau tái tính, kiểm tra metadata nguồn; ghi rõ giới hạn dữ liệu khí tượng và thủy văn.
- [ ] Trưởng nhóm xác nhận nghiệm thu cuối; khi đó mới chuyển PR #9 khỏi Draft, merge vào `main`, chốt bộ `handoff_writer/` cho người viết.

## Không được ghi thành đã đạt
- Chưa xác minh đúng toàn bộ dữ liệu CHIRPS/ERA5-Land từ raw.
- Đã có trị số sai lệch mưa từ phép chạy độc lập, nhưng còn khác biệt 377/379 pixel với chuỗi Huy và chưa xác minh đầy đủ raw CHIRPS/ERA5-Land end-to-end.
- GATE1/GATE6 đã được chạy từ máy trưởng nhóm; sau vòng kiểm tra tài liệu cuối có sửa script 06/08 nên **cần chạy lại GATE5a/GATE6 và xác minh output cập nhật**.
- Phương pháp mưa được chấp nhận có điều kiện, nhưng **chưa có nghiệm thu cuối**.

**Tài liệu có hiệu lực quản lý:** `docs/OWNER_DECISIONS_2026-10-27.md` và PR #9. Đây là hồ sơ công việc đang tiến hành, không phải giấy chứng nhận hoàn tất.
