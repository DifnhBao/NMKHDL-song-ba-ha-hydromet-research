# Nghiên cứu dữ liệu khí tượng thủy văn — Lưu vực Sông Ba Hạ

**Học phần:** Nhập môn Khoa học dữ liệu  
**Đề tài:** Nghiên cứu dữ liệu lĩnh vực khí tượng thủy văn, xử lý và trực quan hóa dữ liệu và rút ra các ý nghĩa.  
**Phạm vi:** Lưu vực sông Ba đến Thủy điện Sông Ba Hạ; giai đoạn 01/01/2023 – 31/12/2025.  
**Trạng thái:** Triển khai kỹ thuật; dữ liệu gốc 36 tháng được bàn giao **ngoài Git**.

---

## Mục tiêu và câu hỏi nghiên cứu

Nghiên cứu bao quát cả khí tượng và thủy văn, mang tính phân tích dữ liệu khám phá (EDA), không nhằm chứng minh quan hệ nhân quả hoặc xây dựng mô hình dự báo.

| Mã | Câu hỏi |
|---|---|
| **RQ1** | Lượng mưa, nhiệt độ và tính mùa tại lưu vực biến động như thế nào trong 2023–2025? |
| **RQ2** | Lưu lượng nước về hồ và mực nước thay đổi ra sao? Có sự kiện nổi bật nào? |
| **RQ3** | Lượng mưa lưu vực và lưu lượng về hồ có mối liên hệ thống kê như thế nào? (Pearson/Spearman, lag 0/1 tháng; **không** kết luận nhân quả) |

## Tài liệu bắt buộc

- [Đặc tả nghiên cứu V1.0](docs/DAC_TA_NGHIEN_CUU_V1.0.md)
- [Hướng dẫn triển khai, bàn giao và nghiệm thu V1.1](docs/PHU_LUC_TRIEN_KHAI_V1.1.md)
- [Quy trình làm việc GitHub](docs/WORKFLOW.md)
- [GitHub Issues — sáu GATE](../../issues)

**Ưu tiên:** V1.1 quy định cách thực hiện cụ thể. Trong trường hợp khác biệt về trình tự hay mức độ ưu tiên, áp dụng V1.1.

---

## Cấu trúc dự án

```text
SongBaHa_Research/
│
├── data/
│   ├── raw/
│   │   ├── hydrology/          # Dữ liệu gốc SBH 36 tháng (HTML + CSV)
│   │   ├── chirps/             # Raster CHIRPS v3 (tải khi chạy script 03)
│   │   ├── era5_land/          # NetCDF ERA5-Land (tải khi chạy script 04)
│   │   └── boundaries/         # HydroBASINS shapefile (tải khi chạy script 02)
│   │
│   ├── interim/                # Dữ liệu trung gian
│   └── processed/              # Dữ liệu kết quả (CSV tích hợp, GeoJSON)
│
├── scripts/
│   ├── 01_hydrology_qa.py          # GATE 1 — Kiểm định thủy văn
│   ├── 02_basin_delineation.py     # GATE 2 — Ranh giới lưu vực
│   ├── 03_chirps_extraction.py     # GATE 3a — Mưa CHIRPS v3
│   ├── 04_temperature_extraction.py# GATE 3b — Nhiệt độ ERA5-Land
│   ├── 05_data_integration.py      # GATE 4 — Tích hợp dữ liệu
│   ├── 06_exploratory_analysis.py  # GATE 5a — Phân tích RQ1+RQ2
│   └── 07_rainfall_runoff_analysis.py # GATE 5b — Phân tích RQ3
│
├── outputs/
│   ├── figures/                # F01–F09 (PNG ≥ 200 dpi)
│   ├── tables/                 # T01–T06 (CSV)
│   ├── quality/                # Báo cáo QA, phương pháp (Markdown)
│   └── maps/                   # Bản đồ lưu vực
│
├── handoff_writer/             # Bàn giao cho người viết báo cáo (GATE 6)
│   ├── 01_project_overview.md
│   ├── 02_data_sources_and_methods.md
│   ├── 03_data_quality_summary.md
│   ├── 04_results_and_interpretation.md
│   ├── 05_limitations.md
│   ├── 06_figures_and_tables_index.md
│   ├── 07_references.md
│   ├── figures/
│   ├── tables/
│   └── selected_data/
│
├── docs/                       # Đặc tả và quy trình
├── run_all.py                  # Chạy toàn bộ pipeline
├── requirements.txt
└── README.md
```

---

## Hướng dẫn cài đặt và chạy

### 1. Yêu cầu hệ thống

- **Python:** 3.11 trở lên
- **Hệ điều hành:** Windows / Linux / macOS
- **RAM:** ≥ 8 GB (tải và xử lý raster lớn)
- **Dung lượng đĩa:** ≥ 10 GB (dữ liệu CHIRPS + ERA5 + HydroBASINS)
- **Internet:** Cần khi tải dữ liệu (GATE 2, 3)

### 2. Cài đặt

```bash
# Clone repository
git clone https://github.com/DifnhBao/NMKHDL-song-ba-ha-hydromet-research.git
cd NMKHDL-song-ba-ha-hydromet-research

# Tạo môi trường ảo (khuyến nghị)
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# Cài đặt thư viện
pip install -r requirements.txt
```

### 3. Chuẩn bị dữ liệu đầu vào

**Dữ liệu thủy văn** được bàn giao ngoài Git. Nhận ZIP 36 tháng và giải nén vào `data/raw/hydrology/`. Sau giải nén phải có:

```text
data/raw/hydrology/
├── song_ba_ha_202301_to_202512.csv   # CSV hợp nhất 1.096 ngày
├── raw_csv/                           # CSV gốc theo tháng (36 file)
├── raw_html/                          # HTML gốc (36 file)
├── normalized/                        # CSV chuẩn hóa (36 file)
├── qa_monthly.csv                     # QA sơ bộ
└── run_metadata.json                  # Metadata thu thập
```

**Tài khoản CDS (cho GATE 3b):** Để tải ERA5-Land, cần tài khoản Copernicus CDS. Sau khi đăng ký tại https://cds.climate.copernicus.eu, tạo file `~/.cdsapirc`:

```ini
url: https://cds.climate.copernicus.eu/api
key: <UID>:<API-KEY>
```

### 4. Chạy toàn bộ pipeline

```bash
python run_all.py
```

Hoặc chạy từng script riêng lẻ theo thứ tự:

```bash
# GATE 1: Kiểm định thủy văn
python scripts/01_hydrology_qa.py

# GATE 2: Xác định lưu vực (tải HydroBASINS ~500 MB)
python scripts/02_basin_delineation.py
# ⚠️ Sau bước này: trình F01_basin_map.png, basin_method.md cho người
#    thiết kế phê duyệt TRƯỚC KHI tiếp tục GATE 3

# GATE 3a: Mưa CHIRPS (tải raster ~36 file tháng + 1096 file ngày)
python scripts/03_chirps_extraction.py

# GATE 3b: Nhiệt độ ERA5-Land (yêu cầu cdsapi)
python scripts/04_temperature_extraction.py

# GATE 4: Tích hợp
python scripts/05_data_integration.py

# GATE 5a: Phân tích RQ1 + RQ2
python scripts/06_exploratory_analysis.py

# GATE 5b: Phân tích RQ3
python scripts/07_rainfall_runoff_analysis.py
```

Chạy từ GATE cụ thể (nếu các bước trước đã hoàn thành):

```bash
python run_all.py --gate 3   # Chạy từ GATE 3 trở đi
```

### 5. Thứ tự phụ thuộc

```text
GATE 1 (QA thủy văn)
   │
   ├── GATE 2 (Lưu vực) ──→ [Phê duyệt] ──→ GATE 3a (CHIRPS)
   │                                         GATE 3b (ERA5-Land)
   │                                              │
   └──────────────────────────────────────→ GATE 4 (Tích hợp)
                                                   │
                                             GATE 5a (RQ1+RQ2)
                                             GATE 5b (RQ3)
                                                   │
                                             GATE 6 (Bàn giao)
```

- **GATE 1** có thể chạy độc lập ngay.
- **GATE 2** cần chạy trước GATE 3 và phải được phê duyệt.
- **GATE 3** yêu cầu polygon lưu vực từ GATE 2.
- **GATE 4** yêu cầu đầu ra từ GATE 1 + GATE 3.
- **GATE 5** yêu cầu đầu ra từ GATE 4.
- **GATE 6** hoàn thiện thủ công sau khi GATE 5 hoàn thành.

---

## Đầu ra chính

### Dữ liệu xử lý (`data/processed/`)

| File | Mô tả |
|---|---|
| `hydrology_clean.csv` | Dữ liệu thủy văn kèm cờ QA từng biến |
| `hydrology_exceptions.csv` | Danh sách ngoại lệ |
| `hydrology_qa_summary.csv` | Tổng hợp QA theo tháng |
| `song_ba_ha_catchment.geojson` | Polygon lưu vực (WGS84) |
| `basin_validation.csv` | Kiểm tra diện tích lưu vực |
| `rainfall_monthly.csv` | Mưa tháng trung bình lưu vực (CHIRPS v3) |
| `rainfall_daily.csv` | Mưa ngày trung bình lưu vực |
| `temperature_monthly.csv` | Nhiệt độ tháng (ERA5-Land) |
| `temperature_daily.csv` | Nhiệt độ ngày |
| `hydromet_daily.csv` | Bảng ngày tích hợp (1.096 dòng) |
| `hydromet_monthly.csv` | Bảng tháng tích hợp (36 dòng) |
| `integration_qa.csv` | Kiểm tra tích hợp |

### Hình (`outputs/figures/`)

| Mã | Nội dung |
|---|---|
| F01 | Bản đồ ranh giới lưu vực |
| F02 | Biến động mưa theo tháng |
| F03 | Nhiệt độ trung bình tháng |
| F04 | Hydrograph lưu lượng theo ngày |
| F05 | Lưu lượng tháng |
| F06 | Mực nước thượng lưu sau kiểm định |
| F07 | So sánh mưa–lưu lượng đồng thời |
| F08 | Scatter plot mưa–lưu lượng |
| F09 | So sánh tương quan lag 0/1 |

### Bảng (`outputs/tables/`)

| Mã | Nội dung |
|---|---|
| T01 | Danh mục nguồn dữ liệu |
| T02 | Kết quả QA thủy văn |
| T03 | Thống kê khí tượng |
| T04 | Thống kê thủy văn |
| T05 | Kết quả tương quan mưa–dòng chảy |
| T06 | Ngoại lệ và quyết định xử lý |

---

## Nguồn dữ liệu

| Nguồn | URL | Loại |
|---|---|---|
| Sông Ba Hạ | https://sbh.vn/vi-VN/san-xuat/Tinh-hinh-san-xuat-60-1300 | Số liệu công trình |
| CHIRPS v3 | https://www.chc.ucsb.edu/data/chirps3 | Vệ tinh + quan trắc |
| ERA5-Land | https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land | Tái phân tích |
| HydroBASINS | https://www.hydrosheds.org/products/hydrobasins | Dữ liệu địa lý |

## Thư viện

Xem `requirements.txt`:
- pandas, numpy — Xử lý dữ liệu
- matplotlib — Trực quan hóa
- scipy — Phân tích tương quan
- geopandas, shapely, pyproj — Dữ liệu không gian
- rasterio, rioxarray, xarray — Raster/NetCDF
- requests — Tải dữ liệu HTTP
- cdsapi — Tải ERA5-Land
- openpyxl — Xuất Excel

---

## Quy tắc quan trọng

- **Không** đưa dữ liệu lớn, thông tin đăng nhập, API key lên repository.
- **Không** tự sửa dữ liệu gốc, bỏ cực trị, thay nguồn chính khi chưa được phê duyệt.
- **Không** kết luận nhân quả từ tương quan.
- **Không** thực hiện ML, mô hình dự báo, dashboard ngoài phạm vi.
- Dữ liệu bổ trợ (độ ẩm, lưu lượng xả) chỉ triển khai sau khi hoàn thành P0/P1.

---

## GitHub Issues

Sáu GATE nghiệm thu tương ứng Issues #1–#6 trên GitHub. Xem [Issues](../../issues) để theo dõi tiến độ.

## Liên hệ

Những quyết định ảnh hưởng đến tính đúng đắn khoa học (thay nguồn dữ liệu, thay phạm vi, sai lệch lưu vực > 5%) cần được người phụ trách thiết kế phê duyệt trước khi áp dụng.
