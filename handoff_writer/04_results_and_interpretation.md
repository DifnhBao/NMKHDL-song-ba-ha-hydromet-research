# 04 — Kết quả và diễn giải

> **Lưu ý cho người viết:** Phần "Số liệu" dưới đây là kết quả tính toán. Phần "Diễn giải" là nhận định kỹ thuật. Người viết có thể sử dụng làm cơ sở nhưng không thêm kết luận khoa học chưa được kiểm tra.

## RQ1 — Khí tượng

### Lượng mưa (F02, T03)

**Số liệu:**
- Xem bảng `T03_meteorology_stats.csv` cho thống kê mô tả
- Tổng mưa từng năm 2023, 2024, 2025 có trong T03
- Phân bố theo tháng: xem F02

**Diễn giải:**
- Lưu vực sông Ba có tính mùa rõ: mùa mưa tập trung tháng 5–11 (ảnh hưởng gió mùa), mùa ít mưa tháng 12–4
- Những tháng mưa cao nhất cần được xác định từ dữ liệu thực tế trong T03 và F02
- **Không** kết luận xu thế biến đổi khí hậu dài hạn từ 3 năm dữ liệu

### Nhiệt độ (F03, T03)

**Số liệu:**
- Nhiệt độ trung bình tháng (°C): xem T03 và F03
- Biên độ nhiệt theo mùa

**Diễn giải:**
- Nhiệt độ ổn định hơn lượng mưa, dao động theo mùa với biên độ hẹp hơn
- Nhiệt độ từ ERA5-Land là tái phân tích, không phải quan trắc trực tiếp

## RQ2 — Thủy văn

### Lưu lượng (F04, F05, T04)

**Số liệu:**
- Thống kê lưu lượng: xem T04 (trung bình, trung vị, min, max, độ lệch chuẩn)
- Biểu đồ ngày (hydrograph): F04
- Trung bình theo tháng: F05

**Diễn giải:**
- Lưu lượng có biến động mùa tương ứng với mùa mưa
- Phân bố lưu lượng lệch phải (right-skewed): trung vị < trung bình, có các giá trị cực lớn
- Sự kiện 19–20/11/2025: lưu lượng 12.455 m³/s — cần đối chiếu với thông tin lũ lớn; không loại bỏ chỉ vì giá trị cao

### Mực nước (F06, T04)

**Số liệu:**
- Thống kê mực nước thượng lưu (chỉ VALID): xem T04
- Biến động theo thời gian: F06
- Tham khảo: mực nước dâng bình thường 111,5 m, mực nước chết 95,0 m

**Diễn giải:**
- Mực nước phản ánh chế độ vận hành hồ (tích/xả)
- Một số ngày mực nước bất thường đã được gắn cờ (xem T06)

## RQ3 — Liên hệ mưa – dòng chảy

### Tương quan (F07, F08, F09, T05)

**Số liệu:**
- Biểu đồ đồng thời: F07
- Scatter plot: F08
- So sánh hệ số: F09
- Bảng chi tiết: T05
- Pearson và Spearman tại lag 0 và lag 1 tháng
- Kiểm tra deseasonalised (B6): phép kiểm tra độ nhạy

**Diễn giải:**
- Mưa lưu vực và lưu lượng về hồ có thể có mối liên hệ thống kê do cùng chịu ảnh hưởng mùa
- Tương quan **không** chứng minh quan hệ nhân quả
- Hệ số tương quan có thể bị thổi phồng bởi tính mùa chung
- Deseasonalised cho thấy mức độ liên hệ sau khi loại ảnh hưởng mùa (nhưng mẫu nhỏ: 3 giá trị/tháng lịch)
- Lag 1 tháng có thể phản ánh thời gian truyền nước, nhưng cũng có thể do overlap mùa
- Kết quả bị ảnh hưởng bởi: tính mùa, tự tương quan, hồ chứa thượng nguồn điều tiết, và thời gian nghiên cứu chỉ 3 năm

### Ngoại lệ và quyết định (T06)
- Xem `T06_exceptions_decisions.csv` cho danh sách đầy đủ
