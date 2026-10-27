# 04 — Kết quả và diễn giải

> Quy ước: mỗi mục tách **Số liệu** (tính từ CSV) và **Nhận định** (diễn giải,
> có giới hạn). Không đọc phần nhận định như kết quả kiểm định thống kê.

## RQ1 — Khí tượng

### Số liệu

- Tổng mưa 3 năm: **5.685,1 mm**.
- Tổng mưa theo năm: 2023: 1.933,6 mm, 2024: 1.625,9 mm, 2025: 2.125,6 mm.
- Mưa tháng trung bình: **157,9 mm**;
  trung vị 169,0 mm;
  lớn nhất 448,0 mm;
  nhỏ nhất 4,0 mm.
- Mùa mưa (T5–T11): 21 tháng, trung bình 247,3 mm/tháng,
  chiếm **91,3%** tổng lượng mưa.
- Mùa khô (T12–T4): 15 tháng, trung bình 32,8 mm/tháng,
  chiếm 8,7%.
- Ba tháng mưa lớn nhất: 2025-11 (448,0 mm), 2023-07 (351,5 mm), 2023-09 (350,6 mm).
- Nhiệt độ trung bình 3 năm: **24,02 °C**;
  tháng lạnh nhất 18,83 °C;
  tháng nóng nhất 28,77 °C.
- Nhiệt độ trung bình theo năm: 2023: 24,02 °C, 2024: 24,55 °C, 2025: 23,48 °C.

### Bảng T03 — Thống kê khí tượng

| variable | n_months | mean | median | std | min | max | total_3yr | share_pct |
|---|---|---|---|---|---|---|---|---|
| Lượng mưa tháng (mm) | 36 | 157,90 | 169,00 | 130,30 | 4,00 | 448,00 | 5.685,10 | — |
| Tổng mưa năm 2023 (mm) | 12 | — | — | — | — | — | 1.933,60 | — |
| Tổng mưa năm 2024 (mm) | 12 | — | — | — | — | — | 1.625,90 | — |
| Tổng mưa năm 2025 (mm) | 12 | — | — | — | — | — | 2.125,60 | — |
| Nhiệt độ tháng (°C) | 36 | 24,00 | 24,40 | 2,20 | 18,80 | 28,80 | — | — |
| Lượng mưa tháng — Mùa khô (T12–T4) | 15 | 32,80 | 13,40 | 42,50 | 4,00 | 166,80 | 492,10 | 8,70 |
| Lượng mưa tháng — Mùa mưa (T5–T11) | 21 | 247,30 | 244,70 | 91,30 | 76,00 | 448,00 | 5.193,00 | 91,30 |

### Nhận định

- Lượng mưa phân hóa rất mạnh theo mùa: hơn 90% tổng mưa tập trung trong T5–T11,
  phù hợp chế độ gió mùa của miền Trung Việt Nam.
- Năm 2025 có tổng mưa cao nhất trong ba năm, chủ yếu do các tháng cuối năm;
  năm 2024 thấp nhất.
- Nhiệt độ biến động theo mùa nhưng biên độ hẹp hơn nhiều so với biên độ mưa.
- Ba năm dữ liệu **không đủ** để khẳng định xu thế biến đổi khí hậu dài hạn.

## RQ2 — Thủy văn

### Số liệu

- Lưu lượng về hồ (chỉ ngày VALID, n = 1092):
  trung bình **194,98 m³/s**, trung vị **93,53 m³/s**,
  độ lệch chuẩn 308,70 m³/s, CV 1,583,
  nhỏ nhất 7,59 m³/s, lớn nhất **4.543,28 m³/s**.
- Phân vị: P05 17,60; P25 41,55;
  P75 226,72; P90 449,17; P95 658,71 m³/s.
- Độ bất đối xứng (skewness) 6,35; kurtosis 66,16.
- Mực nước thượng lưu (n = 1084): trung bình 103,31 m,
  nhỏ nhất 101,02 m, lớn nhất 105,96 m.

### Bảng T04 — Thống kê thủy văn

| variable | n_days | mean | median | std | cv | min | p05 | p10 | p25 | p75 | p90 | p95 | max | skewness | kurtosis |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Lưu lượng về hồ (m³/s) | 1092 | 194,98 | 93,53 | 308,70 | 1,58 | 7,59 | 17,60 | 25,05 | 41,55 | 226,72 | 449,17 | 658,71 | 4.543,28 | 6,35 | 66,16 |
| Mực nước thượng lưu (m) | 1084 | 103,31 | 103,28 | 1,06 | 0,01 | 101,02 | 101,50 | 101,85 | 102,54 | 104,28 | 104,72 | 104,83 | 105,96 | -0,18 | -0,94 |
| Lưu lượng về hồ — năm 2023 (m³/s) | 364 | 198,46 | 120,57 | 233,79 | 1,18 | 7,59 | 13,18 | 38,87 | 58,75 | 246,94 | 447,74 | 542,89 | 1.819,62 | 3,18 | 14,48 |
| Lưu lượng về hồ — năm 2024 (m³/s) | 366 | 108,70 | 72,62 | 116,11 | 1,07 | 10,42 | 16,35 | 20,55 | 30,18 | 135,85 | 279,48 | 370,30 | 803,11 | 2,20 | 6,29 |
| Lưu lượng về hồ — năm 2025 (m³/s) | 362 | 278,71 | 113,58 | 452,56 | 1,62 | 11,78 | 23,96 | 32,85 | 44,46 | 332,71 | 678,28 | 1.013,05 | 4.543,28 | 5,11 | 37,41 |

### Nhận định

- Phân bố lưu lượng lệch phải mạnh (trung bình lớn hơn trung vị khoảng
  2,1 lần): đa số ngày dòng chảy thấp,
  một số ít ngày rất lớn quyết định giá trị trung bình.
- Năm 2024 có dòng chảy thấp nhất; năm 2025 cao nhất và có phương sai lớn nhất.
- Sự kiện nổi bật: **19–20/11/2025** lưu lượng về hồ 12.455 m³/s, gấp khoảng
  18,9 lần P95 của các ngày VALID
  (658,7 m³/s). Hai ngày này bị gắn cờ SUSPECT nên **không**
  nằm trong T04 (giá trị lớn nhất của chuỗi VALID là 4.543,3 m³/s).
  Cần đối chiếu với nguồn vận hành trước khi dùng làm số liệu chính thức.
- Mực nước thượng lưu có các đoạn bất thường (0 m, 37–38 m, đảo cột) đã gắn cờ;
  biểu đồ F06 chỉ vẽ các ngày VALID và ngắt đoạn tại chỗ thiếu.

## RQ3 — Liên hệ mưa – dòng chảy

### Số liệu

- Tương quan lag 0 (n = 36 tháng):
  Pearson **r = 0,586** (p < 0,001);
  Spearman **ρ = 0,544** (p < 0,001).
- Tương quan lag 1 (n = 35 tháng):
  Pearson **r = 0,615** (p < 0,001);
  Spearman **ρ = 0,793** (p < 0,001).
- Deseasonalised (loại trung bình tháng lịch): Pearson 0,657;
  Spearman 0,439.
- Loại tháng chứa ngày SUSPECT (n = 34):
  Pearson 0,483 (p = 0,0038);
  Spearman 0,498 (p = 0,0027).
- Mùa mưa (n = 21): Pearson 0,541
  (p = 0,0113); Spearman 0,339
  (p = 0,1328).
- Mùa khô (n = 15): Pearson 0,447
  (p = 0,0948); Spearman 0,232
  (p = 0,4051).
- Nhóm mưa cao (> P67, n = 12): Pearson 0,747
  (p = 0,0052).

### Bảng T05 — Tương quan mưa – dòng chảy

| analysis | subset | lag | n_pairs | pearson_r | pearson_p | spearman_r | spearman_p |
|---|---|---|---|---|---|---|---|
| B3 — Tương quan lag 0 | Tất cả tháng hợp lệ | 0 | 36 | 0,586 | < 0,001 | 0,544 | < 0,001 |
| B4 — Tương quan lag 1 tháng | Tất cả tháng hợp lệ | 1 | 35 | 0,615 | < 0,001 | 0,793 | < 0,001 |
| B6 — Deseasonalised (kiểm tra nhạy) | Tất cả tháng hợp lệ | 0 | 36 | 0,657 | < 0,001 | 0,439 | 0,0074 |
| S1 — Loại tháng có ngày SUSPECT | Không gồm tháng SUSPECT | 0 | 34 | 0,483 | 0,0038 | 0,498 | 0,0027 |
| S1 — Loại tháng có ngày SUSPECT (lag 1) | Không gồm tháng SUSPECT | 1 | 32 | 0,688 | < 0,001 | 0,754 | < 0,001 |
| D — Tương quan lag 0, Mùa mưa (T5–T11) | Mùa mưa (T5–T11) | 0 | 21 | 0,541 | 0,0113 | 0,339 | 0,1328 |
| D — Tương quan lag 0, Mùa khô (T12–T4) | Mùa khô (T12–T4) | 0 | 15 | 0,447 | 0,0948 | 0,232 | 0,4051 |
| R — Tương quan lag 0, Nhóm mưa thấp (≤ P33) | Nhóm mưa thấp (≤ P33) | 0 | 12 | 0,682 | 0,0146 | 0,077 | 0,8122 |
| R — Tương quan lag 0, Nhóm mưa trung bình (P33–P67) | Nhóm mưa trung bình (P33–P67) | 0 | 12 | -0,020 | 0,9514 | -0,105 | 0,7456 |
| R — Tương quan lag 0, Nhóm mưa cao (> P67) | Nhóm mưa cao (> P67) | 0 | 12 | 0,747 | 0,0052 | 0,469 | 0,1245 |

### Bảng T07 — Độ nhạy khi loại tháng chứa ngày SUSPECT

| metric | base_n_pairs | base_pearson_r | sens_n_pairs | sens_pearson_r | delta_pearson_r | base_spearman_r | sens_spearman_r | delta_spearman_r | base_pearson_p | sens_pearson_p |
|---|---|---|---|---|---|---|---|---|---|---|
| lag 0 | 36 | 0,586 | 34 | 0,483 | -0,103 | 0,544 | 0,498 | -0,046 | < 0,001 | 0,0038 |
| lag 1 | 35 | 0,615 | 32 | 0,688 | 0,073 | 0,793 | 0,754 | -0,039 | < 0,001 | < 0,001 |

### Nhận định

- Có liên hệ dương, mức trung bình đến khá, giữa mưa tháng và lưu lượng về hồ;
  mối liên hệ có ý nghĩa thống kê ở mức α = 0,05 cho cả lag 0 và lag 1.
- Ở kịch bản chỉ dùng ngày VALID, lag 1 có hệ số cao hơn lag 0. Nhưng khi giữ cả các ngày inflow SUSPECT làm kiểm tra độ nhạy, Pearson lag 0 = 0,541 và lag 1 = 0,484; thứ tự đảo chiều. **Không thể kết luận lag 1 mạnh hơn một cách bền vững**, càng không suy ra thời gian trễ thủy văn thực.
- Loại tháng chứa ngày SUSPECT làm Pearson lag 0 giảm
  0,103 (từ 0,586 xuống
  0,483), trong khi lag 1 tăng 0,073.
  Kết luận về chiều và độ lớn vẫn giữ nguyên, nhưng độ lớn thay đổi đáng kể.
- Khác biệt giữa Pearson và Spearman ở một số nhóm cho thấy ảnh hưởng của giá trị
  cực đoan và cỡ mẫu nhỏ; các hệ số nhóm chỉ mang tính mô tả.
- **Không** kết luận quan hệ nhân quả. Hồ chứa điều tiết làm suy yếu quan hệ
  mưa – dòng chảy tự nhiên.

## Liên kết hình

| Hình | Nội dung | Kết quả chính |
|---|---|---|
| F01 | Bản đồ lưu vực và vị trí công trình | Diện tích 11.160,6 km²; đập và nhà máy nằm trong polygon |
| F02 | Mưa tháng 2023–2025 | Đỉnh mưa T10–T11; mùa khô rất ít mưa |
| F03 | Nhiệt độ tháng | Biên độ hẹp, cao nhất vào các tháng giữa năm |
| F04 | Hydrograph lưu lượng ngày | Nhiều đỉnh ngắn, đỉnh lớn nhất 11/2025 |
| F05 | Lưu lượng tháng | Tương phản mạnh giữa mùa mưa và mùa khô |
| F06 | Mực nước thượng lưu | Dao động trong dải vận hành, có đoạn bất thường đã loại |
| F07 | Mưa và lưu lượng cùng trục thời gian | Hai chuỗi cùng pha ở quy mô tháng |
| F08 | Scatter mưa – lưu lượng | Xu hướng dương, phân tán rộng |
| F09 | So sánh tương quan lag 0 / lag 1 | Chỉ là kết quả theo bộ lọc QA; thứ tự thay đổi nếu giữ SUSPECT |
| F10 | Phân bố lưu lượng | Lệch phải mạnh, đuôi dài về phía giá trị lớn |
