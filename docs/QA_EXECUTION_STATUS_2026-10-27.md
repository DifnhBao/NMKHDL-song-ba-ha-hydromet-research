# Trạng thái thực thi vòng QA sau quyết định của trưởng nhóm — 27/10/2026

*Cập nhật tiến độ kỹ thuật: 28/10/2026. Giữ nguyên tên file làm đầu mối hồ sơ.*

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
- [ ] Kiểm tra độc lập script 09 bằng raster tổng hợp có đáp số biết trước (chưa có bằng chứng chạy test này); phép đối chiếu trên 36 raster CHIRPS thật đã hoàn thành và được trưởng nhóm chấp nhận có điều kiện, không tuyên bố thuật toán đã được xác minh tuyệt đối.
- [x] Trưởng nhóm chấp nhận **có điều kiện** phương pháp mưa xấp xỉ, sau khi xem sai số tương đối tuyệt đối trung bình 0,4477%, tối đa 1,3952%; kết luận Pearson không thay đổi đáng kể. Số pixel 377/379 chưa giải thích hoàn toàn.
- [x] Đã chạy GATE1 với raw 1.096 ngày; các ngày nghi đảo cột giữ SUSPECT, tổng 35 lượt ngoại lệ; chạy lại GATE4, GATE5a/b.
- [x] Đã chạy script 10, bảng T08 có hệ số VALID_ONLY 0,585573/0,614721 và INCLUDE_SUSPECT 0,540892/0,483878.
- [x] Trưởng nhóm chạy GATE6: 27 thao tác sao chép, không thiếu; 10 hình F01–F10, T01–T08 (bao gồm T02b), bảy tài liệu chính và reviewer notes đều có mặt. Rà soát văn bản/CSV trên GitHub: không còn nhầm SUSPECT/INVALID_CONFIRMED trong T01, không thấy chuỗi xuống dòng `\\n` nguyên văn trong các tài liệu chính. Chưa đánh dấu là đã kiểm tra trực quan từng PNG.
- [x] Đã sửa các mâu thuẫn phát hiện trong T01, Markdown, diễn giải SUSPECT, trạng thái CHIRPS và danh mục T08; Pearson được tính độc lập từ 36 tháng và khớp T05/T08. Vẫn công bố các giới hạn nguồn raw, 377/379 pixel và kiểm định tương quan thông thường.
- [ ] Trưởng nhóm xác nhận nghiệm thu cuối; khi đó mới chuyển PR #9 khỏi Draft, merge vào `main`, chốt bộ `handoff_writer/` cho người viết.

## Không được ghi thành đã đạt
- Chưa xác minh đúng toàn bộ dữ liệu CHIRPS/ERA5-Land từ raw.
- Đã có trị số sai lệch mưa từ phép chạy độc lập, nhưng còn khác biệt 377/379 pixel với chuỗi Huy và chưa xác minh đầy đủ raw CHIRPS/ERA5-Land end-to-end.
- GATE1, GATE4, GATE5a/b, GATE6 đã chạy thành công tại máy trưởng nhóm; sau chỉnh sửa script 06/08 đã chạy lại GATE5a và GATE6 và push kết quả trong commit `5d10df9`. GATE3 tận dụng dữ liệu khí tượng đã bàn giao, không chạy lại quá trình tải raw.
- Polygon và phương pháp mưa được chấp nhận có điều kiện; vòng rà soát số liệu và diễn giải kỹ thuật đạt trong phạm vi đã kiểm. **Chưa nghiệm thu toàn đề tài**, chưa xác nhận người viết đã cập nhật nội dung, chưa rà soát trực quan từng PNG và chưa tái lập đủ raw.

**Tài liệu có hiệu lực quản lý:** `docs/OWNER_DECISIONS_2026-10-27.md` và PR #9. Đây là hồ sơ công việc đang tiến hành, không phải giấy chứng nhận hoàn tất.
