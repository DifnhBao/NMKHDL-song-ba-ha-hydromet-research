# PHỤ LỤC V1.1 — HƯỚNG DẪN TRIỂN KHAI, BÀN GIAO VÀ NGHIỆM THU KỸ THUẬT

**Dự án:** Nghiên cứu dữ liệu khí tượng thủy văn — trường hợp lưu vực Sông Ba Hạ  
**Tài liệu áp dụng cùng:** Đặc tả nghiên cứu và triển khai kỹ thuật V1.0  
**Giai đoạn nghiên cứu:** 01/01/2023–31/12/2025  
**Trạng thái:** Phạm vi nghiên cứu đã chốt, chuyển sang triển khai kỹ thuật.

---

## 1. Quy định thực hiện

Người phụ trách kỹ thuật thực hiện toàn bộ quy trình thu thập bổ sung, kiểm định chất lượng, xử lý dữ liệu, phân tích, trực quan hóa và bàn giao kết quả theo tài liệu V1.0 và phụ lục này.

Không tự thay đổi địa điểm nghiên cứu, nguồn dữ liệu chủ đạo, thời gian nghiên cứu, câu hỏi nghiên cứu hoặc thêm các mục tiêu ngoài phạm vi.

**Phụ lục V1.1 quy định cách thực hiện cụ thể. Trong trường hợp khác biệt về trình tự hay mức độ ưu tiên, áp dụng V1.1. Mọi thay đổi về mục tiêu hoặc yêu cầu học thuật phải được người phụ trách thiết kế phê duyệt.**

Các quyết định đã chốt:

| Nội dung | Quy định |
|---|---|
| Lưu vực nghiên cứu | Sông Ba, giới hạn đến công trình Sông Ba Hạ |
| Thời gian | 2023–2025 |
| Phương pháp tổng thể | EDA, thống kê mô tả, trực quan hóa, phân tích mối liên hệ |
| Khí tượng chủ đạo | CHIRPS v3 Final và ERA5-Land |
| Thủy văn chủ đạo | Lưu lượng nước về hồ từ website Sông Ba Hạ |
| Đơn vị thời gian phân tích kết hợp | Tháng |
| Đơn vị thời gian phân tích thủy văn chi tiết | Ngày |
| Phân tích kết hợp | Lượng mưa lưu vực so với lưu lượng về hồ |
| Độ trễ nghiên cứu | 0 tháng và 1 tháng |
| Dự báo bằng ML | Không thực hiện |
| Dashboard tương tác | Không thực hiện |
| Lưu lượng xả | Chỉ dùng bổ trợ sau khi xác minh định nghĩa |

## 2. Đầu vào được bàn giao

Người triển khai phải nhận đủ:

1. File đặc tả nghiên cứu V1.0.
2. Phụ lục triển khai V1.1 này.
3. ZIP dữ liệu Sông Ba Hạ đã thu thập cho 36 tháng, bao gồm dữ liệu gốc, dữ liệu chuẩn hóa, HTML và báo cáo QA.
4. Mã nguồn `song_ba_ha_collector.py` và hướng dẫn chạy.
5. Danh sách các bản ghi nghi vấn cần đối chiếu.
6. Đường dẫn các nguồn dữ liệu khí tượng, địa lý và tài liệu về công trình.

Trước khi xử lý, kiểm kê các tệp đầu vào, ghi phiên bản và kiểm tra bản dữ liệu thủy văn có đủ 36 tháng, tương ứng 1.096 ngày lịch.

Không ghi đè hoặc thay đổi dữ liệu đầu vào.

## 3. Công nghệ và cấu trúc dự án

**Ngôn ngữ:** Python 3.11 trở lên.

**Thư viện chính:**
- pandas, numpy: Xử lý và kiểm tra dữ liệu.
- matplotlib: Trực quan hóa.
- scipy: Phân tích tương quan.
- geopandas, shapely, pyproj: Dữ liệu không gian.
- rasterio, rioxarray hoặc xarray: Dữ liệu khí tượng dạng raster.
- requests: Truy xuất dữ liệu.
- cdsapi: Tải dữ liệu Copernicus khi sử dụng API.

Có thể sử dụng QGIS để kiểm tra trực quan ranh giới lưu vực.

Cấu trúc thư mục:

```text
SongBaHa_Research/
│
├── data/
│   ├── raw/
│   │   ├── hydrology/
│   │   ├── chirps/
│   │   ├── era5_land/
│   │   └── boundaries/
│   │
│   ├── interim/
│   └── processed/
│
├── scripts/
│   ├── 01_hydrology_qa.py
│   ├── 02_basin_delineation.py
│   ├── 03_chirps_extraction.py
│   ├── 04_temperature_extraction.py
│   ├── 05_data_integration.py
│   ├── 06_exploratory_analysis.py
│   └── 07_rainfall_runoff_analysis.py
│
├── outputs/
│   ├── tables/
│   ├── figures/
│   ├── quality/
│   └── maps/
│
├── handoff_writer/
├── docs/
├── requirements.txt
├── README.md
└── run_all.py
```

Các tên script là giao diện bàn giao thống nhất. Có thể tổ chức mã nguồn nội bộ thành module bổ sung, nhưng phải giữ được khả năng chạy lại toàn bộ quy trình.

Mỗi bước xử lý cần có thông báo lỗi rõ ràng. Nếu đầu vào không đạt điều kiện, chương trình phải báo lỗi hoặc tạo trạng thái cần kiểm tra, không tự động sinh dữ liệu thay thế.

---

# GIAI ĐOẠN A — KIỂM ĐỊNH DỮ LIỆU THỦY VĂN

## 4. Đầu vào

Sử dụng CSV hợp nhất của 36 tháng đã thu thập.

Các trường quan trọng:

- `date`
- `inflow_m3s`
- `upstream_level_m`
- `downstream_level_m`
- `release_m3s`
- `max_power_mw`
- `daily_energy_kwh`

Giữ cả các trường sản lượng lũy kế để kiểm tra chéo, không sử dụng lũy kế như một giá trị phát sinh mới mỗi ngày.

## 5. Kiểm tra bắt buộc

**5.1. Kiểm tra cấu trúc**

- Đúng khoảng ngày 01/01/2023–31/12/2025.
- Có 1.096 ngày lịch.
- Không có ngày trùng.
- Ngày được chuẩn hóa thành `YYYY-MM-DD`.
- Các cột số được nhận dạng và lưu chính xác.
- Kiểm tra tính liên tục qua cuối tháng và cuối năm.

**5.2. Kiểm tra hợp lý**

- Phát hiện dữ liệu trống và dữ liệu bằng 0.
- Phát hiện các biến động mực nước đột ngột.
- Cảnh báo nếu mực nước thượng lưu nhỏ hơn mực nước hạ lưu.
- Cảnh báo công suất cực đại vượt 220 MW.
- Cảnh báo các chuỗi giá trị không thay đổi từ 14 ngày liên tiếp trở lên.
- Phát hiện các giá trị lưu lượng quá khác biệt với lân cận để kiểm tra.
- Kiểm tra sự thống nhất của sản lượng điện ngày và lũy kế tháng.

Những điều kiện này là **quy tắc phát hiện ngoại lệ**, không phải cơ sở tự động kết luận dữ liệu sai.

**5.3. Danh sách cần đối chiếu bắt buộc**

| Ngày | Vấn đề |
|---|---|
| 14/01/2023 | Mực nước thượng lưu 140,30 m |
| 19/02/2023 | Nghi đảo giá trị mực nước thượng/hạ lưu |
| 21/01/2023 | Nhiều trường thủy văn bằng 0 nhưng sản lượng điện dương |
| 31/05/2023 | Mực nước bất thường |
| 03/02/2024 | Công suất cực đại 707 MW |
| 09/04/2024 | Nghi đảo giá trị mực nước |
| 09/09/2024 | Mực nước bất thường |
| 19–20/11/2025 | Lưu lượng về hồ rất lớn; cần kiểm tra định nghĩa và nguồn |

Các ngày trên là danh sách kiểm tra ban đầu, không phải danh sách đầy đủ mọi ngoại lệ.

## 6. Quy tắc xử lý thống nhất

Áp dụng trạng thái riêng cho từng biến, không chỉ một cờ duy nhất cho cả dòng.

| Trạng thái | Định nghĩa | Xử lý |
|---|---|---|
| `VALID` | Giá trị hợp lệ theo các kiểm tra hiện có | Đưa vào phân tích |
| `SUSPECT` | Giá trị nghi vấn, chưa xác minh | Giữ nguyên nguồn, đánh dấu |
| `MISSING` | Không có dữ liệu thực | Không thay bằng 0 |
| `INVALID_CONFIRMED` | Có bằng chứng xác nhận sai | Không dùng giá trị sai trong phép tính chính |
| `CORRECTED` | Đã hiệu chỉnh dựa trên bằng chứng xác thực | Giữ cả giá trị gốc và giá trị hiệu chỉnh |

Không tự động nội suy, thay thế bằng trung bình hoặc xóa dữ liệu.

Lưu lượng cực lớn không bị loại chỉ vì có giá trị cao.

Trong phân tích chính, chỉ sử dụng các giá trị hợp lệ hoặc được hiệu chỉnh có căn cứ. Với dữ liệu `SUSPECT` chưa giải quyết, tạo phân tích độ nhạy khi việc bao gồm hoặc loại trừ chúng có thể ảnh hưởng đến nhận xét.

Nếu một tháng có dưới 90% số ngày lưu lượng đủ điều kiện phân tích, gắn cờ `LOW_COVERAGE`, không tự động đưa tháng đó vào phân tích tương quan chính. Ngưỡng 90% là tiêu chí kiểm soát chất lượng nội bộ của dự án, không phải chuẩn phổ quát của ngành.

**Đầu ra:**

```text
hydrology_clean.csv
hydrology_exceptions.csv
hydrology_qa_summary.csv
hydrology_quality_notes.md
```

---

# GIAI ĐOẠN B — XÁC ĐỊNH RANH GIỚI LƯU VỰC

## 7. Mục tiêu

Xác định khu vực thượng nguồn đóng góp nước đến tuyến công trình thủy điện Sông Ba Hạ.

Diện tích tham khảo do đơn vị vận hành công bố: **11.115 km²**.

Không dùng diện tích toàn bộ lưu vực sông Ba thay thế.

## 8. Trình tự kỹ thuật

**Bước 1:** Xác định vị trí tuyến đập/cửa ra bằng tài liệu công trình hoặc nguồn địa lý có thể kiểm chứng.

**Bước 2:** Tải dữ liệu HydroBASINS khu vực châu Á, sử dụng dữ liệu cấp tiểu lưu vực đủ chi tiết để định vị mạng sông liên quan.

**Bước 3:** Kiểm tra kết nối thượng nguồn–hạ nguồn bằng thông tin topology của HydroBASINS. Nếu ranh giới polygon tổng hợp chưa bám chính xác tuyến đập, sử dụng dữ liệu hướng dòng chảy HydroSHEDS để phân định lưu vực đến cửa ra thích hợp.

**Bước 4:** Tạo polygon lưu vực tổng hợp và lưu dưới định dạng GeoJSON.

**Bước 5:** Tính diện tích bằng phương pháp địa lý phù hợp, không dùng phép tính diện tích phẳng trực tiếp trên kinh độ–vĩ độ.

**Bước 6:** Kiểm tra hình học, tính liên thông sông và vị trí cửa ra trên bản đồ. Đối chiếu với tài liệu diện tích 11.115 km².

Công thức sai lệch:

\[
\text{Sai lệch diện tích (\%)} =
\frac{|A_{\text{tính}}-11115|}{11115}\times100
\]

Quy tắc báo cáo:

- Sai lệch không quá 5%: tiếp tục kiểm tra hình học và mạng sông; không tự động coi là đúng.
- Sai lệch trên 5%: phải báo cáo nguyên nhân và trình người giám sát phê duyệt trước khi sử dụng.
- Không xác định được cửa ra hoặc hướng dòng chảy một cách có căn cứ: dừng bước ghép mưa với lưu lượng và báo cáo ngay.

**Đầu ra:**

```text
song_ba_ha_catchment.geojson
basin_validation.csv
basin_method.md
F01_basin_map.png
```

Trong `basin_method.md` phải có tọa độ cửa ra đã kiểm chứng, dữ liệu nền sử dụng, cách xác định polygon, diện tích và giới hạn độ chính xác.

---

# GIAI ĐOẠN C — THU THẬP VÀ XỬ LÝ KHÍ TƯỢNG

## 9. Lượng mưa CHIRPS v3

**Nguồn:** Climate Hazards Center, University of California, Santa Barbara.

Sử dụng CHIRPS v3 Final, không trộn lẫn các phiên bản dữ liệu khác nhau.

Nguồn dữ liệu:

- https://www.chc.ucsb.edu/data/chirps3
- https://data.chc.ucsb.edu/products/CHIRPS/v3.0/monthly/global/
- https://data.chc.ucsb.edu/products/CHIRPS/v3.0/daily/final/rnl/

### Trình tự

**Bước 1:** Tải sản phẩm mưa tháng giai đoạn 2023–2025 trước, gồm 36 tháng.

**Bước 2:** Cắt dữ liệu raster theo vùng lưu vực đã được phê duyệt.

**Bước 3:** Tính lượng mưa trung bình lưu vực bằng trọng số diện tích, tính đến phần ô raster giao với polygon.

\[
P_t=\frac{\sum A_iP_{i,t}}{\sum A_i}
\]

Trong đó \(A_i\) là diện tích thực tế phần ô raster thuộc lưu vực.

**Bước 4:** Xuất chuỗi tổng lượng mưa tháng. Giá trị một ô CHIRPS tháng đã mang đơn vị mm/tháng; không cộng trực tiếp các giá trị của các ô không gian để tạo tổng mưa lưu vực.

**Bước 5:** Tải và trích xuất CHIRPS v3 Final daily `rnl` để hoàn thiện chuỗi mưa ngày theo yêu cầu dữ liệu V1.0.

**Bước 6:** So sánh tổng mưa ngày trong từng tháng với sản phẩm mưa tháng, ghi nhận sai lệch do dữ liệu và phương pháp xử lý. Không ép hai chuỗi khớp bằng cách sửa dữ liệu nguồn.

**Lưu ý khoa học:** Dữ liệu ngày CHIRPS v3 `rnl` được phân rã từ lượng mưa theo khoảng năm ngày bằng thông tin ERA5. Phân tích tương quan ở quy mô tháng được ưu tiên; không diễn giải tương quan theo ngày thành bằng chứng về thời gian phản ứng thủy văn chính xác.

**Đầu ra:**

```text
rainfall_monthly.csv
rainfall_daily.csv
rainfall_extraction_method.md
rainfall_qa.csv
```

Các bảng phải có `date` hoặc `year_month`, giá trị mưa mm, thông tin nguồn và trạng thái dữ liệu.

## 10. Nhiệt độ ERA5-Land

**Nguồn:** Copernicus Climate Data Store.

https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land

Sử dụng biến `2m_temperature`.

**Bước 1:** Lấy dữ liệu nhiệt độ tháng 2023–2025 cho khu vực nghiên cứu.

**Bước 2:** Tính trung bình có trọng số theo lưu vực đã xác định.

**Bước 3:** Chuyển Kelvin sang Celsius:

\[
T(°C)=T(K)-273.15
\]

**Bước 4:** Tạo chuỗi nhiệt độ tháng. Sau khi hoàn thành dữ liệu tháng, bổ sung chuỗi nhiệt độ ngày từ dữ liệu theo giờ nếu đáp ứng được yêu cầu nguồn và phạm vi thời gian.

Đối với nguồn thời gian theo UTC, phải ghi rõ quy ước ngày và cách tổng hợp; không tự coi ngày UTC trùng hoàn toàn với ngày quan trắc tại công trình.

**Đầu ra:**

```text
temperature_monthly.csv
temperature_daily.csv
temperature_method.md
```

Không sử dụng nhiệt độ bề mặt đất thay cho nhiệt độ không khí 2 m.

**Độ ẩm tương đối:** Không thuộc sản phẩm bắt buộc. Không triển khai trước khi hoàn thành toàn bộ sản phẩm chính.

---

# GIAI ĐOẠN D — TÍCH HỢP DỮ LIỆU

## 11. Quy tắc tạo bộ dữ liệu kết hợp

Tạo hai bảng chính.

### Bảng ngày

```text
hydromet_daily.csv
```

Các cột tối thiểu:

```text
date
rainfall_mm
temperature_c
inflow_m3s
upstream_level_m
inflow_quality
level_quality
rainfall_quality
temperature_quality
```

### Bảng tháng

```text
hydromet_monthly.csv
```

Các cột tối thiểu:

```text
year_month
rainfall_total_mm
temperature_mean_c
inflow_mean_m3s
upstream_level_mean_m
rainfall_valid_days
temperature_valid_days
inflow_valid_days
inflow_coverage_pct
quality_status
```

Quy tắc:

- Mưa tháng: dùng lượng mưa tích lũy trong tháng (mm).
- Nhiệt độ tháng: trung bình nhiệt độ theo thời gian (°C).
- Lưu lượng tháng: trung bình các giá trị lưu lượng ngày đủ điều kiện (m³/s).
- Không cộng các giá trị m³/s để gọi là tổng lượng nước.
- Không gọi trung bình của các bản ghi công bố theo ngày là “lưu lượng trung bình ngày/tháng thực đo” nếu chưa xác minh ý nghĩa thời gian của bản ghi.
- Không dùng giá trị 0 thay cho giá trị thiếu.
- Không tự dịch thời gian một ngày khi ghép dữ liệu, trừ khi đã có căn cứ về quy ước thời gian.

**Kiểm tra đầu ra:**

- Bảng nền ngày có đủ 1.096 ngày lịch.
- Bảng tháng có đủ 36 tháng lịch.
- Những ô không có dữ liệu phải được gắn cờ.
- Có số ngày hợp lệ của từng biến.
- Không trùng khóa `date` hoặc `year_month`.
- Có bảng đối chiếu dữ liệu trước và sau tích hợp.

**Đầu ra bổ sung:**

```text
integration_qa.csv
data_dictionary.md
```

---

# GIAI ĐOẠN E — THỐNG KÊ VÀ TRỰC QUAN HÓA

## 12. Phần A1 — Khí tượng

Thực hiện:

1. Thống kê mô tả lượng mưa và nhiệt độ.
2. Tổng lượng mưa các năm 2023, 2024 và 2025.
3. Phân bố và diễn biến lượng mưa theo tháng.
4. Nhiệt độ trung bình theo tháng.
5. So sánh đặc trưng mùa mưa, mùa ít mưa dựa trên chính số liệu thu được.
6. Xác định những tháng có lượng mưa nổi bật.

Không khẳng định xu thế biến đổi khí hậu dài hạn từ ba năm dữ liệu.

## 13. Phần A2 — Thủy văn

Thực hiện:

1. Thống kê lưu lượng nước về hồ: giá trị trung bình, trung vị, nhỏ nhất, lớn nhất và độ lệch chuẩn.
2. Hydrograph lưu lượng theo ngày.
3. Lưu lượng trung bình theo tháng.
4. Phân bố lưu lượng và nhận diện các thời kỳ dòng chảy cao/thấp.
5. Phân tích mực nước thượng lưu sau kiểm định.
6. Mô tả các sự kiện đáng chú ý, đặc biệt tháng 11/2025, với nguồn đối chiếu phù hợp.

Chỉ xây dựng Flow Duration Curve nếu định nghĩa và chất lượng chuỗi lưu lượng cho phép diễn giải một cách có cơ sở. Nếu không đủ căn cứ, bỏ biểu đồ này và ghi rõ lý do; không bắt buộc xin phê duyệt vì điều kiện đã được xác định trước.

## 14. Phần B — Liên hệ lượng mưa và dòng chảy

**Dữ liệu chính:** 36 tháng, sau khi loại các tháng không đủ điều kiện chất lượng theo quy tắc đã đặt.

Thực hiện:

**B1.** Biểu đồ đồng thời mưa tháng và lưu lượng về hồ tháng, sử dụng hai biểu đồ cùng trục thời gian hoặc hai trục tung có đơn vị rõ ràng.

**B2.** Scatter plot lượng mưa tháng và lưu lượng về hồ tháng.

**B3.** Tính Pearson và Spearman tại độ trễ 0 tháng.

**B4.** Tính tương quan giữa lưu lượng tháng hiện tại với lượng mưa tháng trước đó (độ trễ 1 tháng).

**B5.** So sánh hệ số, số cặp dữ liệu hợp lệ và tính ổn định của nhận xét.

**B6.** Kiểm tra ảnh hưởng của tính mùa: trừ trung bình của từng tháng trong năm để tạo chuỗi sai lệch theo tháng lịch, sau đó khảo sát tương quan như một phép kiểm tra độ nhạy. Phải nêu rõ mỗi tháng lịch chỉ có ba giá trị theo năm, nên kết quả không mang ý nghĩa khẳng định mạnh.

Với mỗi phép tính phải ghi:

- Số cặp dữ liệu hợp lệ.
- Biến và đơn vị.
- Độ trễ được sử dụng.
- Hệ số tương quan.
- Những bản ghi bị loại và lý do.
- Giới hạn diễn giải.

Nếu số tháng hợp lệ nhỏ hơn 24, không đưa ra kết luận tổng quát về mối liên hệ trong toàn giai đoạn; báo cáo cho người giám sát để quyết định hướng trình bày.

Không khảo sát hàng chục độ trễ để lựa chọn tùy ý hệ số cao nhất. Không kết luận mưa trực tiếp gây ra một thay đổi lưu lượng chỉ từ tương quan.

---

# GIAI ĐOẠN F — DANH MỤC HÌNH VÀ BẢNG PHẢI BÀN GIAO

## 15. Danh mục hình tối thiểu

| Mã | Nội dung |
|---|---|
| F01 | Bản đồ vị trí và ranh giới lưu vực đến công trình |
| F02 | Biến động lượng mưa theo tháng 2023–2025 |
| F03 | Nhiệt độ trung bình tháng |
| F04 | Biểu đồ lưu lượng nước về hồ theo ngày |
| F05 | Lưu lượng nước về hồ theo tháng |
| F06 | Biến động mực nước thượng lưu sau kiểm định |
| F07 | So sánh mưa tháng và lưu lượng về hồ tháng |
| F08 | Scatter plot mưa – lưu lượng |
| F09 | So sánh kết quả tương quan độ trễ 0 và 1 tháng |

Nếu dữ liệu mực nước không đủ tin cậy, F06 được thay bằng biểu đồ phân bố lưu lượng, kèm giải thích chất lượng dữ liệu mực nước.

Mỗi hình phải có tên, đơn vị, chú giải, nguồn số liệu và một đoạn giải thích nội dung.

Lưu hình ở định dạng PNG, độ phân giải tối thiểu 200 dpi. Đồng thời lưu mã nguồn tạo biểu đồ.

## 16. Danh mục bảng tối thiểu

| Mã | Nội dung |
|---|---|
| T01 | Danh mục nguồn dữ liệu và đặc điểm kỹ thuật |
| T02 | Kết quả kiểm tra chất lượng thủy văn |
| T03 | Thống kê khí tượng |
| T04 | Thống kê thủy văn |
| T05 | Kết quả tương quan mưa – dòng chảy |
| T06 | Danh sách ngoại lệ và quyết định xử lý quan trọng |

Đầu ra phải ở định dạng CSV hoặc Excel, kèm phần diễn giải dạng Markdown.

---

# GIAI ĐOẠN G — KIỂM TRA VÀ NGHIỆM THU

## 17. Các cổng nghiệm thu

### GATE 1 — Dữ liệu thủy văn

Điều kiện:

- Đủ 36 tháng và 1.096 ngày lịch.
- Không trùng ngày.
- Ngoại lệ được ghi nhận.
- Bản gốc được bảo toàn.
- Các phép thống kê được tính từ dữ liệu có trạng thái chất lượng rõ ràng.

### GATE 2 — Không gian

Điều kiện:

- Xác định được cửa ra tương ứng công trình.
- Polygon có nguồn và quy trình tạo.
- Diện tích và tính liên thông đã kiểm tra.
- Được người giám sát phê duyệt trước khi dùng cho bước kết hợp.

### GATE 3 — Khí tượng

Điều kiện:

- Có dữ liệu lượng mưa và nhiệt độ giai đoạn 2023–2025.
- Có phương pháp tổng hợp không gian.
- Đơn vị và quy ước thời gian đúng.
- Không thiếu tháng chưa được giải thích.
- Có bản dữ liệu ngày để hoàn thiện thiết kế đầy đủ V1.0.

### GATE 4 — Tích hợp

Điều kiện:

- Không trùng khóa thời gian.
- Đúng đơn vị và phương pháp tổng hợp.
- Có số ngày hợp lệ và cờ chất lượng.
- Phân tích chính sử dụng được bảng tháng.

### GATE 5 — Kết quả phân tích

Điều kiện:

- Trả lời đủ RQ1, RQ2, RQ3 hoặc nêu rõ trở ngại đã được người giám sát phê duyệt.
- Các biểu đồ, bảng và kết luận nhất quán.
- Không trình bày suy đoán như kết quả kiểm chứng.
- Có mã nguồn chạy lại được.

### GATE 6 — Bàn giao cuối

Điều kiện:

- Đủ bộ dữ liệu.
- Đủ script và hướng dẫn.
- Đủ hình, bảng, thuyết minh.
- Có báo cáo giới hạn và những vấn đề chưa thể xác minh.
- Có bộ tài liệu riêng cho người viết báo cáo.

---

# GIAI ĐOẠN H — BÀN GIAO CHO NGƯỜI VIẾT TIỂU LUẬN

## 18. Tạo thư mục `handoff_writer`

Bắt buộc có:

```text
handoff_writer/
│
├── 01_project_overview.md
├── 02_data_sources_and_methods.md
├── 03_data_quality_summary.md
├── 04_results_and_interpretation.md
├── 05_limitations.md
├── 06_figures_and_tables_index.md
├── 07_references.md
│
├── figures/
├── tables/
└── selected_data/
```

### Nội dung yêu cầu

**01_project_overview.md:** Tóm tắt mục tiêu, câu hỏi nghiên cứu, địa điểm và thời gian.

**02_data_sources_and_methods.md:** Giải thích nguồn Sông Ba Hạ, CHIRPS, ERA5-Land, HydroBASINS; cách xử lý và tính toán; quy ước thời gian và đơn vị.

**03_data_quality_summary.md:** Số ngày, tháng, giá trị thiếu, bất thường, quyết định xử lý và ảnh hưởng đến độ tin cậy.

**04_results_and_interpretation.md:** Giải thích kết quả của từng bảng và biểu đồ, liên hệ với RQ1–RQ3. Tách riêng số liệu tính toán và nhận định diễn giải.

**05_limitations.md:** Giới hạn dữ liệu, thời gian ba năm, ảnh hưởng hồ chứa, tính đại diện không gian, vấn đề dữ liệu ngày, và giới hạn của tương quan.

**06_figures_and_tables_index.md:** Danh sách hình/bảng với tên tệp, chú thích, đơn vị, nguồn, script tạo và phần nội dung có thể sử dụng trong báo cáo.

**07_references.md:** Đường dẫn chính thức, thông tin tác giả, năm công bố và ngày truy cập. Không tự tạo tài liệu tham khảo hoặc DOI.

Người viết có thể dùng kết quả và diễn giải kỹ thuật làm cơ sở, nhưng không thay đổi số liệu hoặc đưa thêm các kết luận khoa học chưa được kiểm tra.

---

# GIAI ĐOẠN I — QUY ĐỊNH XỬ LÝ TRỞ NGẠI VÀ BÁO CÁO

## 19. Các vấn đề được tự xử lý

Người kỹ thuật được chủ động:

- Sửa lỗi chương trình.
- Tối ưu thời gian tải dữ liệu.
- Thay đổi cấu trúc module nội bộ mà không thay đổi đầu ra.
- Sửa biểu đồ cho rõ ràng.
- Khắc phục lỗi định dạng và đơn vị có căn cứ.
- Bổ sung kiểm tra dữ liệu.
- Ghi nhận ngoại lệ và thực hiện phân tích độ nhạy theo quy định.

## 20. Các vấn đề bắt buộc trình người giám sát

- Không xác định được ranh giới lưu vực đúng.
- Không lấy được dữ liệu CHIRPS hoặc ERA5-Land từ nguồn đã chọn.
- Muốn thay nguồn dữ liệu chủ đạo.
- Muốn thay đổi giai đoạn nghiên cứu hoặc địa điểm.
- Muốn loại bỏ một biến bắt buộc.
- Muốn thay đổi phương pháp phân tích mưa – dòng chảy.
- Số tháng đủ điều kiện phân tích kết hợp dưới 24.
- Gặp sai lệch lớn làm thay đổi nhận xét chính.
- Không xác minh được ý nghĩa thời gian của dữ liệu thủy văn và cần giảm mức độ khẳng định trong kết quả.

Khi phát sinh vấn đề, gửi một báo cáo ngắn theo mẫu:

```text
MÃ VẤN ĐỀ:
CÔNG ĐOẠN:
HIỆN TƯỢNG:
BẰNG CHỨNG / TỆP LIÊN QUAN:
ẢNH HƯỞNG ĐẾN RQ1 / RQ2 / RQ3:
PHƯƠNG ÁN ĐỀ XUẤT:
QUYẾT ĐỊNH CẦN PHÊ DUYỆT:
```

Không dừng toàn bộ công việc nếu các phần khác vẫn có thể thực hiện độc lập.

## 21. Thứ tự ưu tiên khi thực hiện

**P0 — Hoàn thành trước:**

1. QA thủy văn và báo cáo ngoại lệ.
2. Xác định ranh giới lưu vực.
3. Trích xuất 36 tháng lượng mưa CHIRPS.
4. Trích xuất 36 tháng nhiệt độ ERA5-Land.
5. Tạo bộ dữ liệu tháng.
6. Thống kê, biểu đồ và phân tích A+B theo tháng.

**P1 — Hoàn thiện thiết kế đầy đủ:**

1. Dữ liệu khí tượng ngày.
2. Bảng tích hợp ngày.
3. Biểu đồ thủy văn chi tiết.
4. Phân tích độ nhạy và kiểm tra tính mùa.
5. Hoàn thiện mã nguồn và tài liệu tái lập.

**P2 — Không thực hiện nếu làm chậm P0/P1:**

- Độ ẩm tương đối và biến khí tượng bổ trợ.
- Dashboard.
- Machine learning.
- Mô hình thủy văn dự báo.
- Phân tích vận hành xả lũ chuyên sâu.

P0 là mốc để nghiệm thu kết quả phân tích cốt lõi, chưa phải hoàn thành toàn bộ đặc tả V1.0. Những hạng mục P1 có liên quan đến đầu ra bắt buộc của V1.0 vẫn phải hoàn thiện để nghiệm thu toàn bộ, trừ khi người phụ trách thiết kế phê duyệt điều chỉnh phạm vi.

---

## 22. Quy định hoàn thành

Công việc kỹ thuật chỉ được coi là hoàn thành khi có đầy đủ:

- Dữ liệu nguồn, dữ liệu xử lý và metadata.
- Kết quả kiểm tra chất lượng.
- Ranh giới lưu vực đã được phê duyệt.
- Dữ liệu khí tượng và thủy văn tích hợp.
- Hình và bảng phân tích.
- Kết quả trả lời RQ1, RQ2 và RQ3.
- Phần giải thích ý nghĩa và giới hạn nghiên cứu.
- Mã nguồn và hướng dẫn tái lập.
- Thư mục bàn giao hoàn chỉnh cho người viết báo cáo.

**Nguyên tắc cuối cùng: Người triển khai chịu trách nhiệm thực hiện kỹ thuật và bảo đảm sản phẩm đúng yêu cầu. Người phụ trách thiết kế giữ quyền phê duyệt các thay đổi ảnh hưởng đến phạm vi hoặc giá trị khoa học của nghiên cứu.**

*Hết phụ lục triển khai V1.1.*