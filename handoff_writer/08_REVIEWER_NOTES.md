# Ghi chú nghiệm thu để viết tiểu luận

**Bắt buộc đọc trước khi sử dụng các hình/bảng.** Đây là kiểm tra độc lập hồ sơ trên GitHub, không thay thế việc xác minh dữ liệu khí tượng gốc.

- Bản chính: 36 tháng; Pearson mưa–inflow lag 0 = **0,5856** (n=36), lag 1 = **0,6147** (n=35). Đã tính lại độc lập từ `hydromet_monthly.csv`.
- Kịch bản nhạy: đưa cả bốn ngày lưu lượng gắn `SUSPECT` (01/2023: 1; 11/2025: 3) trở lại khi lấy trung bình tháng. Khi đó Pearson lag 0 = **0,5409**, lag 1 = **0,4839**. Thứ tự lag 0/1 thay đổi; **không được kết luận lag 1 mạnh hơn một cách vững chắc**. Đây chỉ là tính thử, không xác nhận số liệu ngoại lệ đúng.
- Giá trị mưa trong các CSV là **xấp xỉ trung bình không gian** dùng mask pixel nhị phân + trọng số cos(vĩ độ), chưa tính phần pixel biên cắt polygon. Cần ghi rõ giới hạn này.
- Polygon rộng **11.160,6 km²** so với tham khảo 11.115 km² (0,41%). Kết quả gần diện tích tham khảo không chứng minh ranh giới tại cửa ra hoàn toàn đúng. Tọa độ đập từ OSM; tham khảo bản đồ F01 và `basin_method.md`.
- Không coi tệp `gate2_approval.json` (được commit bởi người thực hiện kỹ thuật) là bằng chứng độc lập về quyết định phê duyệt của chủ dự án. Khi đưa vào bài, ghi “đã được đối chiếu theo phương pháp và giới hạn ghi trong biên bản” trừ khi chủ dự án xác nhận phê duyệt riêng.
- Không suy luận nhân quả, thời gian trễ thủy văn chính xác hoặc xu thế khí hậu từ ba năm số liệu. Lưu lượng công bố có thể không phải giá trị trung bình ngày thực đo.
- Các bảng F/T và CSV gốc trong `handoff_writer` là nguồn số liệu; không tự sửa bảng, hình hoặc thay số ngoài kết quả có kiểm chứng.
- Các ghi chú hiện hành có thể bị thay thế khi chạy lại script `08_write_handoff.py`. Giữ biên bản `docs/FINAL_REVIEW_AND_HANDOFF.md` và file này như nguồn kiểm soát độc lập.

**Khuyến nghị tác giả báo cáo:** Kết luận nên nói có *mối liên hệ thống kê dương theo tháng* trong cả hai cách xử lý, trong khi *so sánh lag 0/1 không ổn định*. 
