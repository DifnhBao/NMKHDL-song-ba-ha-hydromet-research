# Trạng thái thực thi vòng QA sau quyết định của trưởng nhóm — 27/10/2026

**Trạng thái:** CHƯA NGHIỆM THU CUỐI — nhánh `review/conditional-qa-20261027`, PR #9 Draft; `main` giữ nguyên.

## Đã thay đổi trên nhánh review
1. README và `basin_method.md`: bỏ thông tin "100% passed / end-to-end verified / polygon được duyệt hoàn toàn", thay bằng trạng thái chấp nhận có điều kiện.
2. `gate2_approval.json`: ghi điều kiện theo quyết định trưởng nhóm. `run_all.py` / `03_chirps_extraction.py` phân biệt quyền tiếp tục xử lý polygon với phê duyệt kết quả cuối.
3. `01_hydrology_qa.py`: mực nước thượng lưu thấp hơn hạ lưu chỉ `SUSPECT` (nghi đảo cột), chưa dùng `INVALID_CONFIRMED` nếu thiếu bằng chứng độc lập. **Cần chạy lại GATE1 và các bảng mực nước/T02/T02b/T06 trước khi phát hành; CSV trên main vẫn thuộc lần chạy cũ.**
4. `10_suspect_sensitivity.py`: kịch bản VALID và kịch bản giữ SUSPECT, lấy đầu vào `data/processed` khi có; nếu không thì từ `handoff_writer/selected_data`. `run_all.py` gọi script này trước khi tạo tài liệu GATE6.
5. `08_write_handoff.py`: tự đọc bảng T08 để bổ sung kết quả độ nhạy; không khóa cứng giá trị hệ số vào phần phụ lục. Sửa định dạng xuống dòng và mô tả phương pháp mưa.
6. `09_rainfall_spatial_sensitivity.py`: phương pháp đo sai số pixel-center/cos(lat) so với fractional area trên 36 CHIRPS GeoTIFF tháng **nguyên bản**; chưa chạy, chưa có bảng `rainfall_spatial_sensitivity.csv`.

## Quy trình nghiệm thu kỹ thuật tiếp theo (theo thứ tự)
- [ ] Thu thập đủ 36 tệp CHIRPS monthly nguyên bản, kiểm tra năm/tháng, CRS, nodata và nguồn; không dùng ảnh raster đã mask/crop mất giá trị ở pixel biên.
- [ ] Kiểm tra script 09 trên raster nhỏ tổng hợp có lời giải dự kiến, rồi chạy 36 tháng. Kiểm tra đầu ra sai số mm/% từng tháng, tổng năm và ảnh hưởng tới RQ1, RQ3.
- [ ] Trưởng nhóm ra quyết định về phương pháp mưa sau khi xem số liệu định lượng. **Chưa được tự chấp nhận kết quả xấp xỉ.**
- [ ] Chuẩn bị bộ raw thủy văn 36 tháng; chạy GATE1 theo code mới, xác minh ngày nghi đảo cột giữ SUSPECT; chạy lại các GATE phụ thuộc.
- [ ] Chạy script 10; tính lại Pearson độc lập; xác nhận hai kịch bản trùng dữ liệu thực, bảng T08 và văn bản diễn giải.
- [ ] Chạy GATE6, kiểm tra toàn bộ các hình F01–F10, bảng T01–T08, bảy tài liệu chính và các ghi chú reviewer; không xuất hiện \n nguyên văn trong Markdown.
- [ ] Sửa mọi số liệu/nhận xét cũ sau tái tính, kiểm tra metadata nguồn; ghi rõ giới hạn dữ liệu khí tượng và thủy văn.
- [ ] Trưởng nhóm xác nhận nghiệm thu cuối; khi đó mới chuyển PR #9 khỏi Draft, merge vào `main`, chốt bộ `handoff_writer/` cho người viết.

## Không được ghi thành đã đạt
- Chưa xác minh đúng toàn bộ dữ liệu CHIRPS/ERA5-Land từ raw.
- Chưa có trị số sai lệch mưa pixel-center so với fractional-area.
- Chưa chạy lại mã nguồn GATE1 và GATE6 sau các sửa đổi.
- Chưa có kết quả nghiệm thu cuối hoặc quyết định thay phương pháp mưa.

**Tài liệu có hiệu lực quản lý:** `docs/OWNER_DECISIONS_2026-10-27.md` và PR #9. Đây là hồ sơ công việc đang tiến hành, không phải giấy chứng nhận hoàn tất.
