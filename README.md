# Nghiên cứu dữ liệu khí tượng thủy văn — Lưu vực sông Ba đến Thủy điện Sông Ba Hạ (2023–2025)

![Thời gian](https://img.shields.io/badge/Thời_gian-01%2F2023_–_12%2F2025-blue)
![Số_ngày](https://img.shields.io/badge/Chuỗi_ngày-1.096_ngày-green)
![Diện_tích](https://img.shields.io/badge/Diện_tích_lưu_vực-11.160%2C6_km²-orange)
![Python](https://img.shields.io/badge/Python-3.13-3776AB)
![GATE](https://img.shields.io/badge/GATE_1–6-Hoàn_thành-success)

**Trạng thái:** GATE 1–6 hoàn thành. Polygon lưu vực đã được người giám sát phê duyệt
ngày 27/10/2026 (`outputs/quality/gate2_approval.json`).

---

## Mục lục

1. [Mục tiêu và câu hỏi nghiên cứu](#mục-tiêu-và-câu-hỏi-nghiên-cứu)
2. [Cấu trúc dự án](#cấu-trúc-dự-án)
3. [Cài đặt](#cài-đặt)
4. [Chuẩn bị dữ liệu](#chuẩn-bị-dữ-liệu)
5. [Chạy quy trình](#chạy-quy-trình)
6. [Hệ thống cổng nghiệm thu (GATE 1–6)](#hệ-thống-cổng-nghiệm-thu-gate-16)
7. [Nguồn dữ liệu và kênh truy cập](#nguồn-dữ-liệu-và-kênh-truy-cập)
8. [Kết quả chính](#kết-quả-chính)
9. [Sản phẩm bàn giao](#sản-phẩm-bàn-giao)
10. [Giới hạn và quyết định kỹ thuật](#giới-hạn-và-quyết-định-kỹ-thuật)
11. [Tái lập và kiểm chứng](#tái-lập-và-kiểm-chứng)

---

## Mục tiêu và câu hỏi nghiên cứu

Nghiên cứu theo hướng **phân tích dữ liệu khám phá (EDA)** và thống kê tương quan.
Không suy diễn quan hệ nhân quả một chiều; không dùng mô hình học máy dự báo khi
chuỗi quan trắc chỉ có ba năm.

- **RQ1 — Khí tượng:** Lượng mưa, nhiệt độ và tính mùa trên lưu vực biến động thế nào
  trong 2023–2025?
- **RQ2 — Thủy văn:** Lưu lượng nước về hồ và mực nước thay đổi thế nào theo ngày,
  tháng, năm; có sự kiện nổi bật nào?
- **RQ3 — Kết hợp:** Mưa lưu vực và lưu lượng về hồ có liên hệ thống kê thế nào?
  Liên hệ có khác theo mùa hoặc theo độ trễ 0/1 tháng không?

---

## Cấu trúc dự án

```text
doankhdl/
├── docs/                        Đặc tả V1.0, Phụ lục V1.1, WORKFLOW
├── data/
│   ├── raw/                     Dữ liệu gốc (KHÔNG đưa lên Git)
│   │   ├── hydrology/           Chuỗi vận hành Sông Ba Hạ 36 tháng
│   │   ├── chirps/              Raster CHIRPS đã cắt theo lưu vực
│   │   ├── era5_land/           JSON/NetCDF ERA5-Land
│   │   └── boundaries/          HydroBASINS, OSM reference
│   ├── interim/                 Trung gian
│   └── processed/               Bảng sạch, GeoTIFF nhỏ, polygon GeoJSON
├── scripts/
│   ├── 01_hydrology_qa.py       GATE 1 — QA thủy văn
│   ├── 02_basin_delineation.py  GATE 2 — ranh giới lưu vực
│   ├── 03_chirps_extraction.py  GATE 3a — mưa CHIRPS
│   ├── 04_temperature_extraction.py GATE 3b — nhiệt độ ERA5-Land
│   ├── 05_data_integration.py   GATE 4 — tích hợp ngày/tháng
│   ├── 06_exploratory_analysis.py   GATE 5a — RQ1, RQ2
│   ├── 07_rainfall_runoff_analysis.py GATE 5b — RQ3
│   └── 08_write_handoff.py      GATE 6 — sinh tài liệu bàn giao
├── outputs/
│   ├── figures/                 F02–F10
│   ├── maps/                    F01
│   ├── tables/                  T01–T07
│   └── quality/                 Báo cáo QA, phương pháp, phê duyệt GATE 2
├── handoff_writer/              Bộ bàn giao (hình, bảng, dữ liệu chọn lọc, 7 tài liệu)
├── run_all.py                   Điều phối pipeline + kiểm tra GATE
└── requirements.txt
```

---

## Cài đặt

```bash
# 1. Yêu cầu: Python ≥ 3.11 (đã kiểm chứng trên 3.13)
python --version

# 2. Tạo và kích hoạt môi trường ảo
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/macOS

# 3. Cài thư viện
pip install --upgrade pip
pip install -r requirements.txt
```

---

## Chuẩn bị dữ liệu

Dữ liệu thủy văn được bàn giao qua kênh nội bộ và **không nằm trong Git**
(`.gitignore` chặn `data/raw/**`, `data/processed/**`).

Giải nén gói số liệu vào `data/raw/hydrology/`:

```text
data/raw/hydrology/
├── song_ba_ha_202301_to_202512.csv   # 1.096 ngày quan trắc
├── raw_csv/                          # 36 tệp CSV theo tháng
├── raw_html/                         # 36 bản lưu HTML gốc
├── normalized/                       # 36 tệp chuẩn hóa
├── qa_monthly.csv
└── run_metadata.json
```

Mưa, nhiệt độ và ranh giới **không cần chuẩn bị thủ công**: script tự tải
CHIRPS v3.0 Final, ERA5-Land và HydroBASINS level 12.

---

## Chạy quy trình

### Chạy toàn bộ

```bash
python run_all.py
```

Pipeline **dừng ngay** khi một GATE trả mã lỗi khác 0. Trước GATE 3, pipeline kiểm tra
`outputs/quality/gate2_approval.json`; nếu chưa có `"approved": true` thì **chặn**
toàn bộ GATE 3–6.

### Chạy từ một GATE

```bash
python run_all.py --gate 3     # từ GATE 3 trở đi
python run_all.py --gate 6     # chỉ sinh tài liệu + đồng bộ bàn giao
python run_all.py --status     # xem trạng thái các GATE, không chạy
```

### Chạy từng script

```bash
python scripts/01_hydrology_qa.py
python scripts/02_basin_delineation.py
python scripts/03_chirps_extraction.py
python scripts/04_temperature_extraction.py
python scripts/05_data_integration.py
python scripts/06_exploratory_analysis.py
python scripts/07_rainfall_runoff_analysis.py
python scripts/08_write_handoff.py
```

---

## Hệ thống cổng nghiệm thu (GATE 1–6)

| GATE | Script | Đầu ra chính | Điều kiện đạt |
|---|---|---|---|
| 1 | `01_hydrology_qa.py` | `hydrology_clean.csv`, `hydrology_exceptions.csv`, T02/T02b/T06 | 1.096 ngày liên tục, không trùng; mọi ngoại lệ có cờ và quyết định |
| 2 | `02_basin_delineation.py` | `song_ba_ha_catchment.geojson`, `basin_validation.csv`, `basin_method.md`, F01 | Đập **nằm trong** polygon; hình học hợp lệ; sai lệch diện tích ≤ ngưỡng; **có phê duyệt của người giám sát** |
| 3a | `03_chirps_extraction.py` | `rainfall_monthly.csv` (36), `rainfall_daily.csv` (1.096), `rainfall_qa.csv` | Đủ tháng/ngày, không thay dữ liệu thiếu bằng 0 |
| 3b | `04_temperature_extraction.py` | `temperature_monthly.csv`, `temperature_daily.csv` | Đủ 36 tháng / 1.096 ngày, mọi điểm lưới nằm trong polygon |
| 4 | `05_data_integration.py` | `hydromet_daily.csv`, `hydromet_monthly.csv`, `integration_qa.csv`, `data_dictionary.md` | 11/11 kiểm tra đạt (khóa, độ phủ, đơn vị, cờ chất lượng) |
| 5a | `06_exploratory_analysis.py` | T01–T04, T02b, F02–F06, F10 | Đủ biến, đủ phân vị, hình có nguồn và đơn vị |
| 5b | `07_rainfall_runoff_analysis.py` | T05, T07, F07–F09 | Đủ lag 0/1, deseasonalised, phân nhóm mùa và tercile, độ nhạy |
| 6 | `08_write_handoff.py` + `run_all.py` | `handoff_writer/**` | Đủ 10 hình, 8 bảng, 7 tài liệu, dữ liệu chọn lọc; không còn NaN trong `rainfall_daily.csv` |

---

## Nguồn dữ liệu và kênh truy cập

| Dữ liệu | Sản phẩm | Kênh thực tế | Ghi chú |
|---|---|---|---|
| Thủy văn | Vận hành Sông Ba Hạ | Bàn giao nội bộ | 1.096 ngày; 5 biến |
| Mưa | CHIRPS v3.0 Final | **FTP** `ftp.chc.ucsb.edu` | `data.chc.ucsb.edu` trả HTTP 403 (CrowdSec) từ IP hiện tại; FTP cùng máy chủ, cùng sản phẩm |
| Nhiệt độ | ERA5-Land (2 m) | **Open-Meteo Archive** (`models=era5_land`) | Không có khóa CDS; cùng sản phẩm, khác kênh phân phối |
| Ranh giới | HydroBASINS v1c level 12 | hydrosheds.org | 82 tiểu lưu vực |
| Vị trí công trình | OSM `way/480785944`, `way/827889670` | OpenStreetMap | Giấy phép ODbL |

**Phương pháp tổng hợp không gian:** cắt raster theo polygon lưu vực, loại pixel
nodata (`-9999`), lấy trung bình có trọng số **cos(vĩ độ)**. Nhiệt độ dùng **95 điểm
lưới 0,1°** có tâm nằm trong polygon.

Ba quyết định kênh truy cập trên đã được người giám sát chấp thuận và được ghi rõ
trong `handoff_writer/02_data_sources_and_methods.md`,
`outputs/quality/rainfall_extraction_method.md` và `temperature_method.md`.

---

## Kết quả chính

### Ranh giới lưu vực (GATE 2)

| Chỉ tiêu | Giá trị |
|---|---|
| `HYBAS_ID` cửa ra | 4121132660 |
| Số tiểu lưu vực | 82 |
| Diện tích Albers | **11.160,6 km²** |
| Diện tích tham khảo | 11.115 km² |
| Sai lệch | **0,41%** |
| Đập trong polygon | Có (13,0236°N – 108,9039°E) |
| Nhà máy trong polygon | Có (13,0653°N – 108,9129°E) |

### RQ1 — Khí tượng

| Chỉ tiêu | Giá trị |
|---|---|
| Tổng mưa 3 năm | **5.685,1 mm** |
| 2023 / 2024 / 2025 | 1.933,6 / 1.625,9 / 2.125,6 mm |
| Mưa tháng trung bình | 157,9 mm (trung vị 169,0; lớn nhất 448,0; nhỏ nhất 4,0) |
| Mùa mưa T5–T11 | 21 tháng, 247,3 mm/tháng, **91,3%** tổng mưa |
| Mùa khô T12–T4 | 15 tháng, 32,8 mm/tháng, 8,7% |
| Nhiệt độ trung bình | **24,02 °C** (18,83–28,77 °C) |

### RQ2 — Thủy văn

| Chỉ tiêu | Giá trị |
|---|---|
| Số ngày lưu lượng hợp lệ | **1.092 / 1.096** (4 ngày SUSPECT) |
| Trung bình / trung vị | 194,98 / 93,53 m³/s |
| Độ lệch chuẩn / CV | 308,70 m³/s / 1,583 |
| P95 / lớn nhất (VALID) | 658,71 / 4.543,28 m³/s |
| Skewness / kurtosis | 6,35 / 66,16 |
| Mực nước thượng lưu hợp lệ | 1.084 ngày; 101,02–105,96 m |

### RQ3 — Liên hệ mưa – dòng chảy (n = 36 tháng)

| Kịch bản | n | Pearson | Spearman |
|---|---|---|---|
| Lag 0 | 36 | **0,586** (p < 0,001) | **0,544** (p < 0,001) |
| Lag 1 | 35 | 0,615 (p < 0,001) | **0,793** (p < 0,001) |
| Deseasonalised | 36 | 0,657 (p < 0,001) | 0,439 (p = 0,0074) |
| Loại tháng SUSPECT | 34 | 0,483 (p = 0,0038) | 0,498 (p = 0,0027) |
| Mùa mưa | 21 | 0,541 (p = 0,0113) | 0,339 (p = 0,1328) |
| Mùa khô | 15 | 0,447 (p = 0,0948) | 0,232 (p = 0,4051) |

**Đọc kết quả:** có liên hệ dương, mức trung bình đến khá, có ý nghĩa thống kê ở
lag 0 và lag 1. Loại các tháng chứa ngày SUSPECT làm Pearson lag 0 giảm 0,103
(0,586 → 0,483) — tức một phần tương quan đến từ các tháng cực đoan. Hệ số lag 1
cao hơn **không** đủ để kết luận về thời gian trễ thủy văn thực. Không kết luận
nhân quả: hồ chứa điều tiết làm suy yếu quan hệ mưa – dòng chảy tự nhiên.

### Chất lượng dữ liệu

- Tích hợp: **11/11 kiểm tra đạt** (`integration_qa.csv`).
- Mưa ngày: **1.096/1.096** ngày có dữ liệu; mưa lớn nhất **107,84 mm** ngày 19/11/2025.
- Đối chiếu mưa tháng với tổng mưa ngày: lệch tuyệt đối trung bình **0,30%**,
  lớn nhất **1,00%**, 36/36 tháng đạt ngưỡng 10%.
- Ngoại lệ thủy văn: **35 bản ghi** (32 SUSPECT, 3 INVALID_CONFIRMED), tất cả có
  quyết định xử lý trong T06.

---

## Sản phẩm bàn giao

`handoff_writer/` gồm:

| Nhóm | Số lượng | Nội dung |
|---|---|---|
| `figures/` | 10 | F01–F10 (PNG ≥ 200 dpi) |
| `tables/` | 8 | T01, T02, T02b, T03–T07 (CSV) |
| `selected_data/` | 10 | Bảng ngày/tháng, mưa, nhiệt độ, polygon, từ điển dữ liệu |
| Tài liệu | 7 | `01_project_overview.md` … `07_references.md` |

Bộ tài liệu 01–07 được **sinh tự động** từ CSV bằng `scripts/08_write_handoff.py`,
nên số liệu trong văn bản luôn khớp với bảng và hình.

---

## Giới hạn và quyết định kỹ thuật

1. **Ba năm dữ liệu** (36 tháng, 1.096 ngày) không đủ cho phân tích xu thế dài hạn;
   cỡ mẫu tương quan nhỏ (n = 35–36).
2. **Lưu lượng "về hồ" là số liệu vận hành**, chịu điều tiết của các hồ thượng nguồn;
   định nghĩa trường `inflow_m3s` chưa được xác minh từ tài liệu công trình.
3. **Hai ngày 19–20/11/2025** ghi 12.455 m³/s (gấp ~18,9 lần P95) được gắn cờ SUSPECT,
   không đưa vào T04 và được kiểm tra bằng phân tích độ nhạy T07.
4. **Mưa ngày CHIRPS v3 `rnl`** được phân rã từ tổng 5 ngày bằng ERA5 → chỉ dùng bổ trợ;
   phân tích chính dùng bảng tháng.
5. **Không xây dựng Flow Duration Curve (FDC).** Chuỗi lưu lượng là số liệu vận hành
   bị điều tiết, chưa xác minh định nghĩa và còn 4 ngày SUSPECT; theo V1.1 §13, FDC
   chỉ được lập khi định nghĩa và chất lượng chuỗi đủ căn cứ diễn giải. Thay vào đó
   dùng **F10** (phân bố lưu lượng + boxplot theo năm).
6. **Định dạng ngày:** dữ liệu công trình theo UTC+7, sản phẩm toàn cầu theo UTC;
   có thể lệch tối đa một ngày ở vùng biên.
7. **Kênh dữ liệu:** CHIRPS qua FTP và ERA5-Land qua Open-Meteo (đã được chấp thuận);
   không thay đổi sản phẩm, chỉ thay kênh phân phối.

Chi tiết: `handoff_writer/05_limitations.md`.

---

## Tái lập và kiểm chứng

```bash
# 1. Xem trạng thái các GATE
python run_all.py --status

# 2. Chạy lại từ GATE 3 (dùng cache raster/JSON đã tải)
python run_all.py --gate 3

# 3. Chạy lại riêng bước sinh tài liệu bàn giao
python run_all.py --gate 6
```

Kiểm tra nhanh tính nhất quán:

```bash
python -c "import pandas as pd; d=pd.read_csv('data/processed/rainfall_daily.csv'); print(d.rainfall_mm.isna().sum(), len(d))"
python -c "import pandas as pd; print(pd.read_csv('data/processed/integration_qa.csv')[['check','status']].to_string(index=False))"
```

---

## Tài liệu tham khảo

- Đặc tả: [docs/DAC_TA_NGHIEN_CUU_V1.0.md](docs/DAC_TA_NGHIEN_CUU_V1.0.md)
- Phụ lục triển khai: [docs/PHU_LUC_TRIEN_KHAI_V1.1.md](docs/PHU_LUC_TRIEN_KHAI_V1.1.md)
- Quy trình nghiệm thu: [docs/WORKFLOW.md](docs/WORKFLOW.md)
- Danh mục nguồn đầy đủ: `handoff_writer/07_references.md`

**Dữ liệu:** CHIRPS v3.0 Final (Funk et al., 2015); ERA5-Land (Muñoz-Sabater et al.,
2021); HydroBASINS v1c (Lehner & Grill, 2013); OpenStreetMap (ODbL).

**Miễn trừ:** Kết quả là phân tích thống kê mô tả và tương quan trên dữ liệu
2023–2025, không phải dự báo vận hành hồ chứa.
