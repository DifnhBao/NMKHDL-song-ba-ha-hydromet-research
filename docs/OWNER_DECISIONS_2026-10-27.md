# Quyết định nghiệm thu của trưởng nhóm — 27/10/2026

Các quyết định này do trưởng nhóm trực tiếp xác nhận trong cuộc trò chuyện; **không phải phê duyệt cuối toàn bộ dự án**.

| Hạng mục | Quyết định | Trạng thái |
|---|---|---|
| Polygon HydroBASINS 11.160,6 km² | Chấp nhận có điều kiện làm đại diện xấp xỉ; công bố sai lệch 0,41% và nguồn OSM | CONDITIONAL_ACCEPTED |
| Phương pháp mưa CHIRPS | Kiểm tra sai số với trọng số diện tích giao rồi trưởng nhóm mới quyết định | PENDING_QUANTIFICATION |
| Lưu lượng SUSPECT | Giữ hai kịch bản (lọc theo QA và giữ giá trị nguồn để thử độ nhạy) | APPROVED_TWO_SCENARIOS |
| main & bàn giao | Giữ nguyên main, chờ nghiệm thu cuối | HOLD_FINAL_APPROVAL |

## Đầu ra định lượng đã có
Hai hệ số chính Pearson từ `hydromet_monthly.csv`: lag0 = 0,5856 (36 cặp), lag1 = 0,6147 (35 cặp).
Kịch bản giữ cả ngày SUSPECT: lag0 = 0,5409, lag1 = 0,4839. Bảng và script: `handoff_writer/tables/T08_alternative_suspect_sensitivity.csv`, `scripts/10_suspect_sensitivity.py`.

## Sai số CHIRPS: chưa có con số
- Hiện trạng: raster được trích xuất theo pixel có tâm trong polygon và trọng số cos(lat).
- Phương pháp đối chiếu: `scripts/09_rainfall_spatial_sensitivity.py` tính lại theo diện tích giao pixel–polygon trong hệ tọa độ bằng diện tích; xuất `outputs/quality/rainfall_spatial_sensitivity.csv`.
- Chỉ chạy được khi nhận đủ **36 GeoTIFF CHIRPS tháng nguyên gốc**, không phải CSV trung bình hay raster đã bị cắt mất các pixel biên. Chưa có đủ raster đó trong repository.
- Khi có kết quả so sánh: báo cáo chênh tuyệt đối/tương đối theo tháng, trung bình và cực đại; đánh giá ảnh hưởng lên RQ1/RQ3, rồi trình trưởng nhóm lựa chọn.
- **Không được tự đặt ngưỡng sai số rồi tuyên bố phương pháp đạt.**

## Các vấn đề tồn tại
- `gate2_approval.json` đã sửa rõ phạm vi CHẤP NHẬN CÓ ĐIỀU KIỆN; không lấy trạng thái `approved:true` trong tệp đó làm chứng nhận nghiệm thu cuối.
- Mực nước `INVALID_CONFIRMED` còn thiếu chứng cứ độc lập. Chưa tự sửa giá trị hoặc thống kê khi người giám sát chưa có cơ sở xác nhận.
- Raw HTML/CHIRPS/ERA5-Land ngoài GitHub, chưa chạy lại end-to-end.
- `scripts/08_write_handoff.py` đã bổ sung quy tắc ghi lại cảnh báo nghiệm thu trong các tài liệu sinh ra, nhưng cần chạy thử tại môi trường có các bảng dữ liệu gốc.

**Không merge nhánh nghiệm thu vào main và chưa chuyển giao bản kết quả cuối cho người viết khi chưa có quyết định tiếp theo.**
