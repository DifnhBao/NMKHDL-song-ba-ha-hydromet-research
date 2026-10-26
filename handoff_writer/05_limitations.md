# 05 — Giới hạn nghiên cứu

## 1. Giới hạn thời gian

- Nghiên cứu chỉ bao gồm **3 năm** (2023–2025). Đây là khoảng thời gian quá ngắn để khẳng định quy luật khí hậu hay thủy văn dài hạn.
- Không thể kết luận về xu thế biến đổi khí hậu.
- Các năm nghiên cứu có thể không đại diện cho điều kiện trung bình hoặc cực đoan.

## 2. Giới hạn dữ liệu thủy văn

- **Chưa xác minh ý nghĩa thời gian:** Lưu lượng công bố trên website Sông Ba Hạ chưa rõ là trung bình ngày hay giá trị tại thời điểm xác định. Điều này ảnh hưởng đến cách diễn giải trung bình tháng.
- **Ngày bất thường:** Một số ngày có dữ liệu nghi vấn (đảo cột, giá trị 0 bất thường, công suất vượt thiết kế). Đã gắn cờ nhưng chưa xác minh được nguyên nhân gốc.
- **Lưu lượng cực lớn 19–20/11/2025:** Giữ nguyên vì chưa có cơ sở loại bỏ, nhưng ảnh hưởng lớn đến thống kê trung bình và phương sai.

## 3. Giới hạn dữ liệu mưa

- **Mưa ngày CHIRPS v3 `rnl`:** Phân rã từ ước lượng khoảng 5 ngày bằng ERA5. Không phản ánh lượng mưa từng ngày chính xác. Phân tích tương quan ngày phải thận trọng.
- **Ưu tiên quy mô tháng** cho phân tích kết hợp.
- Mưa lưu vực là ước lượng trung bình không gian, không phải đo tại trạm.

## 4. Giới hạn không gian

- Ranh giới lưu vực từ HydroBASINS dựa trên DEM toàn cầu, có thể sai lệch cục bộ.
- Tọa độ cửa ra ước lượng, không phải tọa độ chính thức của đơn vị vận hành.
- Sai lệch diện tích so với giá trị công bố 11.115 km² đã được ghi nhận và đánh giá.

## 5. Ảnh hưởng điều tiết thượng nguồn

- Trên thượng nguồn sông Ba có các hồ chứa khác (Ayun Hạ, Ka Nak, An Khê, Sông Hinh, v.v.) điều tiết dòng chảy.
- Lưu lượng nước về hồ Sông Ba Hạ không chỉ phản ánh lượng mưa tự nhiên mà còn chịu ảnh hưởng xả nước từ các hồ thượng nguồn.
- Điều này làm phức tạp mối liên hệ mưa – lưu lượng.

## 6. Giới hạn phương pháp tương quan

- **Tương quan ≠ nhân quả.** Hệ số Pearson/Spearman chỉ đo mức độ liên hệ tuyến tính/đơn điệu.
- Tính mùa chung có thể thổi phồng hệ số tương quan.
- Phân tích deseasonalised với chỉ 3 giá trị/tháng lịch không có ý nghĩa thống kê mạnh.
- Chỉ khảo sát lag 0 và 1 tháng theo đặc tả; không tìm kiếm lag tối ưu.

## 7. Nhiệt độ ERA5-Land

- Là dữ liệu tái phân tích, không phải quan trắc trực tiếp.
- Tổng hợp ngày theo UTC, có lệch so với ngày tại địa phương (UTC+7).
- Không sử dụng nhiệt độ bề mặt đất.

## 8. Phạm vi không bao gồm

Theo đặc tả V1.0, nghiên cứu **không** thực hiện:
- Dự báo bằng machine learning
- Mô phỏng thủy văn phức tạp
- Đánh giá vận hành xả lũ chuyên sâu
- Dashboard tương tác
