# ĐẶC TẢ NGHIÊN CỨU VÀ TRIỂN KHAI KỸ THUẬT — V1.0

**Học phần:** Nhập môn Khoa học dữ liệu  
**Đề tài đăng ký:** Nghiên cứu dữ liệu lĩnh vực khí tượng thủy văn, xử lý và trực quan hóa dữ liệu và rút ra các ý nghĩa.  
**Trường hợp nghiên cứu:** Lưu vực sông Ba đến công trình thủy điện Sông Ba Hạ.  
**Thời gian nghiên cứu:** 01/01/2023–31/12/2025.  
**Trạng thái:** Chốt phạm vi và phương pháp triển khai; các kết quả dữ liệu phải được nghiệm thu.

## I. Mục tiêu nghiên cứu

Nghiên cứu phải bao quát cả hai lĩnh vực khí tượng và thủy văn, không chỉ thực hiện phân tích lượng mưa hoặc lưu lượng sông đơn lẻ.

Có ba mục tiêu:

1. Hệ thống hóa các loại dữ liệu khí tượng, thủy văn, phương pháp thu thập, đặc điểm và hạn chế của chúng.
2. Thu thập, kiểm tra chất lượng, xử lý và trực quan hóa dữ liệu khí tượng và thủy văn thực tế trên lưu vực Sông Ba Hạ giai đoạn 2023–2025.
3. Khảo sát mối liên hệ thống kê giữa lượng mưa trên lưu vực và lưu lượng nước về hồ; giải thích kết quả trong bối cảnh đặc điểm lưu vực và tác động điều tiết thượng nguồn.

Đề tài mang tính **phân tích dữ liệu khám phá (Exploratory Data Analysis)** và nghiên cứu mối liên hệ, không nhằm chứng minh quan hệ nhân quả hoặc xây dựng mô hình dự báo vận hành hồ.

## II. Câu hỏi nghiên cứu

**RQ1 — Khí tượng:** Lượng mưa, nhiệt độ và tính mùa của chúng tại lưu vực nghiên cứu biến động như thế nào trong giai đoạn 2023–2025?

**RQ2 — Thủy văn:** Lưu lượng nước về hồ và mực nước thay đổi như thế nào theo ngày, tháng, năm; có những thời kỳ hoặc sự kiện nổi bật nào?

**RQ3 — Kết hợp:** Lượng mưa trên lưu vực và lưu lượng nước về hồ có mối liên hệ thống kê như thế nào? Mối liên hệ có khác nhau theo mùa hoặc khi xét độ trễ thời gian hay không?

## III. Phạm vi dữ liệu

| Nhóm       | Biến dữ liệu                      | Nguồn                                       | Mức ưu tiên                     |
| ---------- | --------------------------------- | ------------------------------------------- | ------------------------------- |
| Khí tượng  | Lượng mưa trung bình lưu vực (mm) | CHIRPS v3 Final                             | Bắt buộc                        |
| Khí tượng  | Nhiệt độ không khí (°C)           | ERA5-Land                                   | Bắt buộc                        |
| Khí tượng  | Độ ẩm tương đối (%)               | ERA5 hoặc nguồn phù hợp                     | Bổ trợ                          |
| Thủy văn   | Lưu lượng nước về hồ (m³/s)       | Website Sông Ba Hạ                          | Bắt buộc                        |
| Thủy văn   | Mực nước thượng lưu (m)           | Website Sông Ba Hạ                          | Bắt buộc, sau kiểm định         |
| Thủy văn   | Mực nước hạ lưu (m)               | Website Sông Ba Hạ                          | Bổ trợ                          |
| Vận hành   | Lưu lượng xả (m³/s)               | Website Sông Ba Hạ                          | Bổ trợ, cần xác minh định nghĩa |
| Không gian | Ranh giới lưu vực đến công trình  | HydroBASINS/HydroSHEDS, tài liệu công trình | Bắt buộc                        |

Các biến bổ trợ không được làm chậm những hạng mục bắt buộc.

## IV. Yêu cầu xử lý dữ liệu

### A. Dữ liệu thủy văn

Sử dụng bộ dữ liệu 36 tháng đã thu thập, giữ nguyên HTML và CSV gốc.

Thực hiện kiểm định toàn bộ 1.096 ngày, xác định dữ liệu thiếu, trùng ngày, giá trị bằng 0, giá trị cực đoan và những giá trị trái với thông số kỹ thuật của công trình.

Đặc biệt kiểm tra các trường hợp đã phát hiện: mực nước bị nghi đảo cột, công suất 707 MW, các ngày nhiều biến bằng 0 và lưu lượng cực lớn tháng 11/2025.

Không tự động xóa, nội suy hoặc sửa các ngoại lệ. Mỗi quyết định xử lý phải có cờ chất lượng, lý do và được lưu lại. Xác minh định nghĩa dữ liệu công bố theo ngày, nhất là liệu lưu lượng là giá trị trung bình ngày hay giá trị tại thời điểm xác định.

### B. Ranh giới lưu vực

Xác định lưu vực thượng nguồn đóng góp nước đến công trình Sông Ba Hạ, không dùng toàn bộ lưu vực sông Ba.

Đối chiếu diện tích với giá trị tham khảo 11.115 km². Ngoài diện tích, cần kiểm tra vị trí cửa ra, tính liên thông thượng nguồn và tính phù hợp với hệ thống sông.

Lưu polygon thành GeoJSON hoặc Shapefile, kèm hệ tọa độ, nguồn và phương pháp xác định.

Không sử dụng polygon chỉ vì diện tích gần đúng nếu chưa chứng minh tính phù hợp thủy văn.

### C. Dữ liệu khí tượng

Sử dụng cùng khoảng thời gian 2023–2025.

Trích xuất CHIRPS v3 Final và tính lượng mưa trung bình có trọng số diện tích cho lưu vực. Nhiệt độ ERA5-Land nên được tổng hợp theo cùng phạm vi không gian khi khả thi.

Phân biệt dữ liệu vệ tinh kết hợp quan trắc, dữ liệu tái phân tích và số liệu công trình. Ghi rõ độ phân giải, đơn vị và giới hạn của từng nguồn.

### D. Dữ liệu kết hợp

Tạo bảng theo ngày gồm tối thiểu:

`date`, `rainfall_mm`, `temperature_c`, `inflow_m3s`, `upstream_level_m`, `quality_flag`.

Từ bảng ngày, xây dựng bảng tháng:

- Tổng lượng mưa tháng (mm).
- Nhiệt độ trung bình tháng (°C).
- Giá trị lưu lượng trung bình của các bản ghi ngày trong tháng (m³/s), với điều kiện nêu rõ bản chất số liệu nguồn.
- Số ngày hợp lệ và tỷ lệ dữ liệu thiếu của từng biến.

Không tự động tính thể tích dòng chảy từ số liệu lưu lượng nếu chưa xác minh tính đại diện theo thời gian của chúng.

## V. Phương pháp phân tích

### Phần A — Phân tích độc lập

**Khí tượng:** Thống kê mô tả, phân bố lượng mưa, tổng lượng mưa tháng/năm, nhiệt độ, diễn biến theo thời gian, tính mùa và các giai đoạn mưa đáng chú ý.

**Thủy văn:** Thống kê lưu lượng, biểu đồ dòng chảy theo thời gian (hydrograph), phân bố lưu lượng, biến động mực nước, Flow Duration Curve nếu dữ liệu phù hợp, và các sự kiện cực đoan cần kiểm chứng.

### Phần B — Phân tích kết hợp

- Biểu đồ đồng thời lượng mưa và lưu lượng nước về hồ.
- Đồ thị phân tán lượng mưa – lưu lượng.
- Tương quan Pearson và/hoặc Spearman, lựa chọn theo đặc điểm phân bố.
- Khảo sát độ trễ tại quy mô tháng, ưu tiên độ trễ 0 và 1 tháng.
- So sánh đặc điểm mối liên hệ giữa các giai đoạn có điều kiện mưa khác nhau.
- Kiểm tra độ nhạy của nhận xét khi bao gồm hoặc loại trừ các bản ghi chưa xác minh.

Ưu tiên phân tích theo tháng trong phần đánh giá quan hệ mưa – dòng chảy. Phân tích ngày chỉ là bổ trợ và phải thận trọng vì dữ liệu mưa ngày CHIRPS v3 được phân rã từ ước lượng theo khoảng năm ngày.

Không kết luận quan hệ nhân quả từ hệ số tương quan. Phải thảo luận ảnh hưởng tính mùa, tự tương quan, thời gian truyền nước, hồ chứa thượng nguồn và thời gian nghiên cứu chỉ gồm ba năm.

## VI. Sản phẩm kỹ thuật bắt buộc bàn giao

| Sản phẩm                        | Yêu cầu                                               |
| ------------------------------- | ----------------------------------------------------- |
| Dữ liệu thủy văn gốc            | Bảo toàn 36 tháng, HTML/CSV và metadata               |
| Báo cáo QA                      | Danh sách ngoại lệ và quyết định xử lý                |
| Dữ liệu thủy văn dùng phân tích | CSV sạch kèm cờ chất lượng                            |
| Ranh giới lưu vực               | GeoJSON/SHP và bản đồ kiểm chứng                      |
| Dữ liệu khí tượng               | Chuỗi mưa, nhiệt độ cùng giai đoạn                    |
| Dữ liệu kết hợp                 | Bảng ngày và bảng tháng                               |
| Mã nguồn                        | Python/Notebook chạy lại được                         |
| Biểu đồ                         | Có tiêu đề, đơn vị, chú giải, nguồn và diễn giải      |
| Kết quả phân tích               | Bảng thống kê, kết quả tương quan, nhận xét có căn cứ |
| Hướng dẫn                       | README và danh sách thư viện, phương pháp tái lập     |

## VII. Tiêu chí nghiệm thu

**Dữ liệu:** Không thiếu hoặc trùng ngày trong chuỗi thời gian nền; các giá trị nguồn không bị thay đổi âm thầm; toàn bộ ngoại lệ có trạng thái và cách xử lý rõ ràng.

**Không gian:** Ranh giới đúng lưu vực nghiên cứu và có căn cứ xác minh; không dùng dữ liệu mưa tại một điểm thay cho lượng mưa toàn lưu vực mà không giải thích.

**Phân tích:** Hoàn thành RQ1, RQ2 và RQ3; kết quả số học kiểm tra lại được; đồ thị không đánh tráo đơn vị hoặc kiểu đại lượng.

**Khoa học:** Nhận xét không vượt quá bằng chứng dữ liệu; phân biệt quan trắc, tái phân tích và ước lượng; công khai giới hạn nghiên cứu.

**Tái lập:** Có thể chạy lại quy trình từ nguồn dữ liệu đã lưu để tái tạo các bảng và hình chính.

## VIII. Quy tắc xử lý trở ngại

Nếu một biến bổ trợ không lấy được dữ liệu đáng tin cậy, bỏ biến đó và ghi rõ giới hạn; không trì hoãn toàn bộ dự án.

Nếu không xác định được ranh giới lưu vực đủ tin cậy, phải báo cáo ngay vấn đề cùng các phương án và sai số không gian. Không tự dựng ranh giới thiếu cơ sở. Phân tích tương quan mưa – dòng chảy chỉ được thực hiện với phạm vi mưa có thể bảo vệ về mặt khoa học.

Nếu có ngoại lệ thủy văn chưa giải quyết được, giữ bản gốc, gắn cờ và kiểm tra độ nhạy của kết quả; không tự ý hiệu chỉnh.

Không bổ sung dự báo bằng machine learning, mô phỏng thủy văn phức tạp hay đánh giá vận hành xả lũ ngoài phạm vi khi chưa hoàn thành ba câu hỏi nghiên cứu.

**Bản V1.0 là cơ sở triển khai chính thức. Những thay đổi về câu hỏi nghiên cứu, phạm vi lưu vực, biến trọng tâm hoặc phương pháp kết hợp phải được phê duyệt trước khi áp dụng.**