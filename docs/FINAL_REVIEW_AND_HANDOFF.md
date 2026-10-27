# Biên bản rà soát trước bàn giao — 27/10/2026

## Phạm vi kiểm tra
Nhánh Huy tại commit 24c653f: đối chiếu với đặc tả V1.0/V1.1; kiểm tra cấu trúc 1.096 ngày / 36 tháng, kiểm tra độc lập Pearson và tình huống giữ hoặc bỏ giá trị lưu lượng được gắn cờ. **Không chạy lại việc tải khí tượng gốc** do bản raw raster, dữ liệu API và raw HTML không lưu trong repository.

## Kết quả đã xác minh
- 36 tháng và 1.096 ngày trong bảng tích hợp; hệ số Pearson lag 0 = 0.5856, lag 1 = 0.6147 từ CSV khớp T05.
- Đã có F01–F10, T01–T07, polygon, tài liệu và dữ liệu trong handoff_writer.
- 2025-11 có ba ngày lưu lượng SUSPECT (07, 19, 20), 2023-01 có một ngày SUSPECT (21).

## Những giới hạn không được nói quá
1. Dữ liệu mưa trích xuất theo mask pixel nhị phân + trọng số cos(vĩ độ), **không** phải trọng số diện tích phần giao của mỗi pixel biên với polygon; số mưa là xấp xỉ không gian. Không viết là phép tính fractional area chính xác.
2. Polygon 11.160,6 km² (82 tiểu lưu vực; chênh 0,41%) là hợp lý theo kiểm tra hình học/diện tích, **không đủ bằng chứng kiểm chứng chính xác ranh giới thủy văn tới tuyến đập**; bản đồ dùng nguồn tọa độ cộng đồng OSM. Chủ dự án phải ghi nhận phê duyệt chính thức dựa trên việc xem F01 và basin_method; bản JSON do người triển khai tạo không chứng minh phê duyệt.
3. Các bản ghi SUSPECT có thể là sự kiện lũ thực; việc loại khỏi phép tính chính chỉ là một lựa chọn QA, cần minh bạch và chạy kiểm tra độ nhạy.
4. Kết quả tương quan có thể chịu ảnh hưởng mùa, hồ thượng nguồn và chỉ ba năm số liệu; không chứng minh nhân quả hay thời gian đáp ứng chính xác.
5. Đây là nghiệm thu hồ sơ dựa vào artifact đã commit, không phải xác thực end-to-end từ raw CHIRPS, ERA5-Land và vận hành website.

## Phân tích độ nhạy kiểm tra độc lập

| Cách tính | Số cặp lag 0 | Pearson lag 0 | Số cặp lag 1 | Pearson lag 1 |
|---|---:|---:|---:|---:|
| Chỉ tính ngày inflow VALID (cách hiện tại) | 36 | 0.5856 | 35 | 0.6147 |
| Giữ cả inflow SUSPECT (chỉ là kịch bản giả định) | 36 | 0.5409 | 35 | 0.4839 |

Trong kịch bản thứ hai, lưu lượng tháng 11/2025 từ trung bình 27 ngày VALID = 1.198,01 m³/s thành trung bình 30 bản ghi nguồn = 2.127,05 m³/s. **Thứ tự tương quan lag 0 và lag 1 đảo chiều**; không nên kết luận lag 1 mạnh hơn một cách bền vững.

## Quy tắc cho người viết báo cáo
- Trình bày kết quả r = 0,586 (lag 0) và r = 0,615 (lag 1) là **trường hợp sàng lọc theo QA**, ghi rõ n và phương pháp.
- Trình bày cả kịch bản giữ SUSPECT nêu trên; không dùng để khẳng định giá trị cực trị là đúng.
- Chỉ viết polygon theo tính đại diện xấp xỉ; luôn nêu giới hạn chưa phân định chính xác cửa ra.
- Không diễn giải p-value như bằng chứng nhân quả hoặc xu thế dài hạn.
- Tất cả số liệu từ CSV, bảng F/T tương ứng; không lấy lời nhận xét cũ về lag 1 làm kết luận độc lập.

## Trạng thái phê duyệt khoa học
**Cần xác nhận trực tiếp từ chủ dự án:** chấp thuận sử dụng polygon hiện tại ở vai trò đại diện xấp xỉ và phương pháp trọng số cos(lat) thay vì diện tích pixel giao chính xác. Nếu chưa phê duyệt, tài liệu này không được coi là biên bản nghiệm thu GATE 2.

## Lưu ý về tài liệu tạo tự động
`scripts/08_write_handoff.py` có thể ghi đè `handoff_writer/*.md` khi chạy lại pipeline. Vì vậy các phát hiện và giới hạn quan trọng trong biên bản này phải được giữ và chuyển sang báo cáo dù tài liệu tự động được sinh lại.
