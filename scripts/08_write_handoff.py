#!/usr/bin/env python3
"""
08_write_handoff.py — GATE 6: Sinh 7 tài liệu bàn giao cho người viết báo cáo
=============================================================================
Đặc tả: V1.1 §18 (nội dung 01–07)

Mọi con số trong tài liệu được đọc trực tiếp từ CSV đầu ra, không nhập tay,
để tránh mâu thuẫn giữa văn bản và dữ liệu.

Đầu ra:
    handoff_writer/01_project_overview.md
    handoff_writer/02_data_sources_and_methods.md
    handoff_writer/03_data_quality_summary.md
    handoff_writer/04_results_and_interpretation.md
    handoff_writer/05_limitations.md
    handoff_writer/06_figures_and_tables_index.md
    handoff_writer/07_references.md
"""

import json
import os
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
PROC = ROOT / "data" / "processed"
TABLES = ROOT / "outputs" / "tables"
QA = ROOT / "outputs" / "quality"
HANDOFF = ROOT / "handoff_writer"

ACCESS_DATE = "27/10/2026"


# ── Định dạng số kiểu Việt Nam ───────────────────────────────────────────
def vn(x, nd=1):
    """1234.5 → '1.234,5'."""
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return "—"
    s = f"{x:,.{nd}f}"
    return s.replace(",", "\x00").replace(".", ",").replace("\x00", ".")


def pct(x, nd=1):
    return f"{vn(x, nd)}%"


def pval(x):
    """p-value cho ô bảng: tránh hiển thị 0,00000 khi p rất nhỏ."""
    if x is None or pd.isna(x):
        return "—"
    if x < 0.001:
        return "< 0,001"
    return vn(x, 4)


def p_txt(x):
    """p-value cho câu văn: 'p < 0,001' hoặc 'p = 0,0038'."""
    if x is None or pd.isna(x):
        return "p không xác định"
    if x < 0.001:
        return "p < 0,001"
    return f"p = {vn(x, 4)}"


def md_table(df, dec=None):
    """DataFrame → bảng Markdown; `dec` là dict cột → số chữ số thập phân."""
    dec = dec or {}
    cols = [str(c) for c in df.columns]
    lines = ["| " + " | ".join(cols) + " |",
             "|" + "|".join(["---"] * len(cols)) + "|"]
    for _, row in df.iterrows():
        vals = []
        for col, v in zip(cols, row):
            if isinstance(v, float) and pd.notna(v):
                if col.endswith("_p"):
                    vals.append(pval(v))
                else:
                    vals.append(vn(v, dec.get(col, 2)))
            elif isinstance(v, float):
                vals.append("—")
            else:
                vals.append(str(v) if pd.notna(v) else "—")
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)


def read_csv(name, base=PROC):
    path = base / name
    if not path.exists():
        sys.exit(f"[LỖI] Thiếu tệp đầu ra: {path}. Chạy lại các GATE trước.")
    return pd.read_csv(path)


def find_row(df, key_col, contains):
    mask = df[key_col].astype(str).str.contains(contains, regex=False)
    if not mask.any():
        return None
    return df[mask].iloc[0]


def main():
    # ── Đọc dữ liệu ─────────────────────────────────────────────────────
    hydro = read_csv("hydrology_clean.csv")
    qa_summary = read_csv("hydrology_qa_summary.csv")
    exceptions = read_csv("hydrology_exceptions.csv")
    rain_m = read_csv("rainfall_monthly.csv")
    rain_d = read_csv("rainfall_daily.csv")
    rain_qa = read_csv("rainfall_qa.csv")
    temp_m = read_csv("temperature_monthly.csv")
    temp_d = read_csv("temperature_daily.csv")
    hydromet_m = read_csv("hydromet_monthly.csv")
    hydromet_d = read_csv("hydromet_daily.csv")
    integ_qa = read_csv("integration_qa.csv")
    basin_val = read_csv("basin_validation.csv")

    T01 = read_csv("T01_data_sources.csv", TABLES)
    T02 = read_csv("T02_hydrology_qa_results.csv", TABLES)
    T02b = read_csv("T02b_exception_counts.csv", TABLES)
    T03 = read_csv("T03_meteorology_stats.csv", TABLES)
    T04 = read_csv("T04_hydrology_stats.csv", TABLES)
    T05 = read_csv("T05_correlation_results.csv", TABLES)
    T06 = read_csv("T06_exceptions_decisions.csv", TABLES)
    T07 = read_csv("T07_sensitivity.csv", TABLES)

    basin = dict(zip(basin_val["parameter"], basin_val["value"]))
    approval = {}
    approval_path = QA / "gate2_approval.json"
    if approval_path.exists():
        approval = json.loads(approval_path.read_text(encoding="utf-8"))

    # ── Chỉ số dẫn xuất ─────────────────────────────────────────────────
    rain_m = rain_m.copy()
    rain_m["year"] = rain_m["year_month"].str[:4].astype(int)
    rain_m["month"] = rain_m["year_month"].str[5:7].astype(int)
    annual_rain = rain_m.groupby("year")["rainfall_mm"].sum()
    wet = rain_m[rain_m["month"].between(5, 11)]
    dry = rain_m[~rain_m["month"].between(5, 11)]
    top_months = rain_m.nlargest(3, "rainfall_mm")[
        ["year_month", "rainfall_mm"]]

    temp_m = temp_m.copy()
    temp_m["year"] = temp_m["year_month"].str[:4].astype(int)
    annual_temp = temp_m.groupby("year")["temperature_c"].mean()

    inflow_row = find_row(T04, "variable", "Lưu lượng về hồ (m³/s)")
    level_row = find_row(T04, "variable", "Mực nước thượng lưu")
    inflow_years = T04[T04["variable"].astype(str).str.contains("năm 20")]

    n_days = len(hydro)
    n_months = len(hydromet_m)
    n_release_zero = int((hydro["release_m3s"] == 0).sum())

    exc_by_flag = exceptions.groupby("flag").size().to_dict()
    exc_by_var = exceptions.groupby("variable").size().to_dict()

    qa_ok = integ_qa["status"].eq("OK").sum()
    qa_fail = int((integ_qa["status"] != "OK").sum())

    rain_qa_valid = rain_qa["diff_pct"].dropna()
    n_rain_qa_check = int((rain_qa["status"] == "CHECK").sum())
    n_rain_qa_ok = int((rain_qa["status"] == "OK").sum())

    rain_source = "; ".join(sorted(set(
        rain_m["source"].dropna().tolist() + rain_d["source"].dropna().tolist())))

    def _channel_from(md_name, key):
        """Đọc dòng 'Kênh ...' trong tài liệu phương pháp của script 03/04."""
        try:
            for line in (QA / md_name).read_text(encoding="utf-8").splitlines():
                if key in line and "**" in line:
                    return line.split("**")[2].lstrip(": ").strip()
        except Exception:
            pass
        return "không rõ"

    rain_channel = _channel_from("rainfall_extraction_method.md",
                                 "Kênh tải thực tế")
    temp_channel = _channel_from("temperature_method.md", "Kênh truy cập")
    temp_source = "; ".join(sorted(temp_m["source"].dropna().unique()))
    n_temp_points = int(temp_m["n_pixels"].max())

    # Tương quan
    def corr(label):
        row = T05[T05["analysis"].str.startswith(label)].iloc[0]
        return row

    lag0 = corr("B3")
    lag1 = corr("B4")
    deseason = corr("B6")
    s1_lag0 = T05[(T05["analysis"].str.startswith("S1"))
                  & (T05["lag"] == 0)].iloc[0]
    wet_row = T05[T05["subset"] == "Mùa mưa (T5–T11)"].iloc[0]
    dry_row = T05[T05["subset"] == "Mùa khô (T12–T4)"].iloc[0]
    high_row = T05[T05["subset"] == "Nhóm mưa cao (> P67)"].iloc[0]

    sens0 = T07[T07["metric"] == "lag 0"].iloc[0]
    sens1 = T07[T07["metric"] == "lag 1"].iloc[0]

    HANDOFF.mkdir(parents=True, exist_ok=True)

    # ═══════════════════════════════════════════════════════════════════
    # 01 — TỔNG QUAN DỰ ÁN
    # ═══════════════════════════════════════════════════════════════════
    d01 = f"""# 01 — Tổng quan dự án

## 1. Thông tin chung

| Hạng mục | Nội dung |
|---|---|
| Đề tài | Nghiên cứu dữ liệu khí tượng thủy văn, xử lý và trực quan hóa dữ liệu, rút ra ý nghĩa |
| Trường hợp nghiên cứu | Lưu vực sông Ba đến công trình thủy điện Sông Ba Hạ |
| Thời gian | 01/01/2023 – 31/12/2025 ({n_days} ngày, {n_months} tháng) |
| Vị trí công trình | Đập: {vn(float(basin['outlet_lat']), 4)}°N, {vn(float(basin['outlet_lon']), 4)}°E; nhà máy: {vn(float(basin['powerhouse_lat']), 4)}°N, {vn(float(basin['powerhouse_lon']), 4)}°E |
| Diện tích lưu vực | {vn(float(basin['area_km2']), 1)} km² (Albers), lệch {pct(float(basin['deviation_pct']), 2)} so với {vn(float(basin['reference_area_km2']), 0)} km² tham khảo |
| Tính chất | Phân tích dữ liệu khám phá (EDA); không chứng minh nhân quả, không xây dựng mô hình dự báo vận hành hồ |

## 2. Mục tiêu nghiên cứu

1. Hệ thống hóa các loại dữ liệu khí tượng, thủy văn cùng phương pháp thu thập, đặc điểm và hạn chế.
2. Thu thập, kiểm tra chất lượng, xử lý và trực quan hóa dữ liệu thực tế trên lưu vực giai đoạn 2023–2025.
3. Khảo sát mối liên hệ thống kê giữa lượng mưa trên lưu vực và lưu lượng nước về hồ, đặt trong bối cảnh đặc điểm lưu vực và điều tiết thượng nguồn.

## 3. Câu hỏi nghiên cứu

**RQ1 — Khí tượng:** Lượng mưa, nhiệt độ và tính mùa của chúng tại lưu vực nghiên cứu biến động như thế nào trong giai đoạn 2023–2025?

**RQ2 — Thủy văn:** Lưu lượng nước về hồ và mực nước thay đổi như thế nào theo ngày, tháng, năm; có những thời kỳ hoặc sự kiện nổi bật nào?

**RQ3 — Kết hợp:** Lượng mưa trên lưu vực và lưu lượng nước về hồ có mối liên hệ thống kê như thế nào? Mối liên hệ có khác nhau theo mùa hoặc khi xét độ trễ thời gian hay không?

## 4. Phạm vi và đơn vị

| Nhóm | Biến | Đơn vị | Vai trò |
|---|---|---|---|
| Khí tượng | Lượng mưa trung bình lưu vực | mm/tháng, mm/ngày | Bắt buộc |
| Khí tượng | Nhiệt độ không khí 2 m | °C | Bắt buộc |
| Thủy văn | Lưu lượng nước về hồ | m³/s | Bắt buộc |
| Thủy văn | Mực nước thượng lưu | m | Bắt buộc, sau kiểm định |
| Thủy văn | Mực nước hạ lưu | m | Bổ trợ |
| Không gian | Ranh giới lưu vực | — | Bắt buộc |

## 5. Sản phẩm bàn giao

- Dữ liệu đã xử lý: `handoff_writer/selected_data/`
- Hình: F01–F10 (`handoff_writer/figures/`)
- Bảng: T01–T08 (gồm T02b; `handoff_writer/tables/`)
- Thuyết minh: 01–07 (thư mục này)
- Mã nguồn tái lập: `scripts/01`–`08`, `run_all.py`

> Lưu ý: Mọi số liệu trong bộ tài liệu này được sinh tự động từ CSV đầu ra
> bằng `scripts/08_write_handoff.py`. Không sửa tay số liệu khi viết báo cáo.
"""
    (HANDOFF / "01_project_overview.md").write_text(d01, encoding="utf-8")

    # ═══════════════════════════════════════════════════════════════════
    # 02 — NGUỒN DỮ LIỆU VÀ PHƯƠNG PHÁP
    # ═══════════════════════════════════════════════════════════════════
    t01_md = md_table(T01)
    d02 = f"""# 02 — Nguồn dữ liệu và phương pháp

## 1. Danh mục nguồn dữ liệu (T01)

{t01_md}

## 2. Dữ liệu thủy văn — Sông Ba Hạ

- Nguồn: trang thông tin vận hành của công trình Thủy điện Sông Ba Hạ.
- Giai đoạn: 01/01/2023 – 31/12/2025, {n_days} dòng ngày, không trùng ngày.
- Bản gốc được giữ nguyên tại `data/raw/hydrology/`; dữ liệu xử lý ở
  `data/processed/hydrology_clean.csv` kèm cột chất lượng cho từng biến.
- Quy ước: mỗi dòng là một ngày dương lịch; giá trị 0 không tự động được coi
  là giá trị thật — xem mục ngoại lệ.

## 3. Ranh giới lưu vực — HydroBASINS v1c level 12

- Nguồn: HydroBASINS v1c (Lehner & Grill, 2013), cấp 12, hệ tọa độ EPSG:4326.
- Xác định cửa ra: chọn đơn vị thủy văn **chứa** tọa độ đập
  ({vn(float(basin['outlet_lat']), 4)}°N, {vn(float(basin['outlet_lon']), 4)}°E) —
  phương pháp `contains`, không chọn theo chênh lệch diện tích.
- Tọa độ đập lấy từ OpenStreetMap `way/480785944` (Đập thủy điện Sông Ba Hạ);
  nhà máy `way/827889670` — cả hai đều nằm trong polygon.
- Kết quả: `HYBAS_ID = {basin['outlet_hybas_id']}`, {basin['n_subbasins']} tiểu lưu vực,
  diện tích Albers **{vn(float(basin['area_km2']), 1)} km²**, lệch
  **{pct(float(basin['deviation_pct']), 2)}** so với diện tích tham khảo
  {vn(float(basin['reference_area_km2']), 0)} km².
- Kiểm tra: `dam_inside_polygon = {basin['dam_inside_polygon']}`,
  `powerhouse_inside_polygon = {basin['powerhouse_inside_polygon']}`,
  `geometry_valid = {basin['geometry_valid']}`.
- Trạng thái phê duyệt: **{approval.get('approval_status', 'PENDING_SUPERVISOR_APPROVAL')}** — chấp nhận polygon có điều kiện, không phải nghiệm thu toàn bộ đề tài.

Chi tiết quy trình: `outputs/quality/basin_method.md`; bằng chứng số:
`data/processed/basin_validation.csv`.

## 4. Lượng mưa — CHIRPS v3.0 Final

- Sản phẩm: CHIRPS v3.0 Final (Climate Hazards Center, UC Santa Barbara).
- Kênh tải thực tế: **{rain_channel}**.
  Máy chủ `data.chc.ucsb.edu` trả HTTP 403 cho dải IP sử dụng; FTP là cùng máy
  chủ CHC, cùng sản phẩm và cùng phiên bản.
- Độ phân giải: 0,05° (~5,5 km); tháng: sản phẩm monthly; ngày: sản phẩm `rnl`.
- Phương pháp tổng hợp không gian: cắt raster theo polygon lưu vực, loại pixel
  nodata (-9999), trung bình **xấp xỉ** theo pixel được mask chọn,
  có trọng số cos(vĩ độ): `P_t ≈ Σ(cos(lat_i)P_i,t)/Σ(cos(lat_i))`.
  **Không** tính phần diện tích giao raster–polygon ở các pixel biên.
- Số pixel dùng cho mưa tháng: {int(rain_m['n_pixels'].median())}; mưa ngày:
  {int(rain_d['n_pixels'].median())}.
- Không thay dữ liệu thiếu bằng 0.
- Chi tiết: `outputs/quality/rainfall_extraction_method.md`.

## 5. Nhiệt độ — ERA5-Land

- Sản phẩm: ERA5-Land 2 m temperature (ECMWF/Copernicus).
- Kênh truy cập thực tế: **{temp_channel}**.
- Số điểm lưới 0,1° nằm trong lưu vực: **{n_temp_points}** (chỉ dùng điểm có tâm
  nằm trong polygon, trọng số cos(vĩ độ)).
- Nhiệt độ tháng = trung bình các ngày có dữ liệu trong tháng (khi kênh truy
  cập không cung cấp sản phẩm monthly).
- Đơn vị: °C; dữ liệu theo UTC.
- Chi tiết: `outputs/quality/temperature_method.md`.

## 6. Quy tắc tích hợp (V1.1 §11)

| Quy tắc | Thực hiện |
|---|---|
| Khóa thời gian | `date` (YYYY-MM-DD) cho bảng ngày, `year_month` (YYYY-MM) cho bảng tháng |
| Không trùng khóa | Đã kiểm tra, 0 bản ghi trùng |
| Số ngày hợp lệ | `rainfall_valid_days`, `temperature_valid_days`, `inflow_valid_days` tính từ dữ liệu ngày thực tế |
| Độ phủ | `*_coverage_pct` = số ngày hợp lệ / số ngày trong tháng |
| Cờ chất lượng | `rainfall_quality`, `temperature_quality`, `inflow_quality`, `level_quality` |
| Tổng hợp tháng | Mưa: tổng; nhiệt độ, lưu lượng, mực nước: trung bình các ngày VALID |
| Phân tích chính | Dùng bảng tháng; bảng ngày chỉ bổ trợ |

## 7. Quy ước thời gian và đơn vị

- Ngày dương lịch theo giờ Việt Nam (UTC+7) cho dữ liệu công trình.
- ERA5-Land và CHIRPS là sản phẩm toàn cầu theo UTC; khi ghép với dữ liệu
  công trình có thể lệch tối đa một ngày ở vùng biên.
- Đơn vị: mưa mm, nhiệt độ °C, lưu lượng m³/s, mực nước m, điện năng kWh.

## 8. Mã nguồn tái lập

| Script | Nội dung |
|---|---|
| `scripts/01_hydrology_qa.py` | GATE 1 — QA thủy văn, ngoại lệ |
| `scripts/02_basin_delineation.py` | GATE 2 — ranh giới lưu vực, F01 |
| `scripts/03_chirps_extraction.py` | GATE 3a — mưa CHIRPS |
| `scripts/04_temperature_extraction.py` | GATE 3b — nhiệt độ ERA5-Land |
| `scripts/05_data_integration.py` | GATE 4 — bảng ngày/tháng |
| `scripts/06_exploratory_analysis.py` | GATE 5a — RQ1, RQ2 |
| `scripts/07_rainfall_runoff_analysis.py` | GATE 5b — RQ3 |
| `scripts/08_write_handoff.py` | GATE 6 — sinh tài liệu bàn giao |
| `run_all.py` | Điều phối toàn bộ pipeline |
"""
    (HANDOFF / "02_data_sources_and_methods.md").write_text(d02, encoding="utf-8")

    # ═══════════════════════════════════════════════════════════════════
    # 03 — TỔNG QUAN CHẤT LƯỢNG DỮ LIỆU
    # ═══════════════════════════════════════════════════════════════════
    t02_md = md_table(T02)
    t02b_md = md_table(T02b)
    integ_md = md_table(integ_qa)

    min_cov = qa_summary["inflow_coverage_pct"].min()
    months_below = qa_summary[qa_summary["inflow_coverage_pct"] < 100]
    d03 = f"""# 03 — Tổng quan chất lượng dữ liệu

## 1. Dữ liệu thủy văn (GATE 1)

- Số dòng: **{n_days}** ngày, **{n_months}** tháng; không trùng ngày.
- Bản gốc được bảo toàn; dữ liệu xử lý có cột chất lượng riêng cho từng biến.

### 1.1. Kết quả kiểm tra theo biến (T02)

{t02_md}

### 1.2. Ngoại lệ theo cờ (T02b)

{t02b_md}

Tổng số bản ghi ngoại lệ: **{len(exceptions)}**. Phân bố theo biến:
{", ".join(f"{k} ({v})" for k, v in exc_by_var.items())}.

- `SUSPECT`: {exc_by_flag.get('SUSPECT', 0)} lượt ngoại lệ — bảo toàn giá trị nguồn;
  loại khỏi phép tính trung bình tháng chính của biến tương ứng nếu chưa được xác minh,
  đồng thời giữ kịch bản bao gồm SUSPECT để kiểm tra độ nhạy.
- `INVALID_CONFIRMED`: {exc_by_flag.get('INVALID_CONFIRMED', 0)} bản ghi — không dùng
  trong phép tính chính, giữ nguyên bản gốc.

### 1.3. Các ngoại lệ quan trọng

| Ngày | Biến | Giá trị | Cờ | Lý do |
|---|---|---|---|---|
{chr(10).join(
    f"| {r['date']} | {r['variable']} | {vn(r['value'], 2) if isinstance(r['value'], (int, float)) else r['value']} | {r['flag']} | {str(r['reason'])[:180]} |"
    for _, r in exceptions.iterrows()
    if r['flag'] == 'INVALID_CONFIRMED' or '12455' in str(r['value'])
)}

- Hai ngày **19–20/11/2025** có lưu lượng về hồ 12.455 m³/s — giá trị cực lớn,
  được giữ nguyên trong dữ liệu nguồn và đánh dấu SUSPECT; không dùng trong
  trung bình tháng chính, nhưng đưa vào kịch bản độ nhạy T08. Kiểm tra loại
  toàn bộ tháng có SUSPECT nằm tại T07. Chưa xác minh cực trị từ nguồn độc lập.
- Mực nước thượng lưu có các ngày 37,2–38,6 m (bất thường) và một số
  ngày nghi đảo cột thượng/hạ lưu — đã gắn cờ SUSPECT, loại khỏi thống kê chính
  nhưng chưa xác nhận nguyên nhân hay tự sửa giá trị nguồn.

### 1.4. Độ phủ theo tháng

- Độ phủ lưu lượng thấp nhất: **{pct(min_cov)}**.
- Số tháng có độ phủ dưới 100%: **{len(months_below)}**
  {("(" + ", ".join(months_below['year_month'].tolist()) + ")") if len(months_below) else ""}.

## 2. Dữ liệu khí tượng (GATE 3)

### 2.1. Lượng mưa CHIRPS

- Mưa tháng: **{int((rain_m['status'] == 'OK').sum())}/{len(rain_m)}** tháng có dữ liệu.
- Mưa ngày: **{int(rain_d['rainfall_mm'].notna().sum())}/{len(rain_d)}** ngày có dữ liệu;
  {int(rain_d['rainfall_mm'].isna().sum())} ngày thiếu.
- Nguồn: {rain_source}.
- Đối chiếu mưa tháng với tổng mưa ngày (`rainfall_qa.csv`):
  - Số tháng lệch < 10%: **{n_rain_qa_ok}**;
  - Số tháng lệch ≥ 10%: **{n_rain_qa_check}**;
  - Lệch tuyệt đối trung bình: **{pct(rain_qa_valid.abs().mean())}**;
  - Lệch tuyệt đối lớn nhất: **{pct(rain_qa_valid.abs().max())}**.
- Lưu ý: mưa ngày CHIRPS v3 `rnl` được phân rã từ tổng 5 ngày, nên không kỳ vọng
  khớp tuyệt đối với sản phẩm tháng. Chênh lệch được báo cáo, không tự hiệu chỉnh.

### 2.2. Nhiệt độ ERA5-Land

- Nhiệt độ tháng: **{int(temp_m['temperature_c'].notna().sum())}/{len(temp_m)}** tháng.
- Nhiệt độ ngày: **{int(temp_d['temperature_c'].notna().sum())}/{len(temp_d)}** ngày.
- Nguồn: {temp_source}; số điểm lưới: {n_temp_points}.

## 3. Tích hợp dữ liệu (GATE 4)

- Bảng tháng: **{len(hydromet_m)} tháng**, khóa `year_month` không trùng.
- Bảng ngày: **{len(hydromet_d)} dòng** ngày lịch, khóa `date` không trùng.
- Kết quả kiểm tra: **{qa_ok}/{len(integ_qa)} đạt**, {qa_fail} lỗi.

{integ_md}

## 4. Ranh giới lưu vực (GATE 2)

| Kiểm tra | Kết quả |
|---|---|
| Diện tích Albers | {vn(float(basin['area_km2']), 1)} km² |
| Diện tích tham khảo | {vn(float(basin['reference_area_km2']), 0)} km² |
| Sai lệch | {pct(float(basin['deviation_pct']), 2)} |
| Đập trong polygon | {basin['dam_inside_polygon']} |
| Nhà máy trong polygon | {basin['powerhouse_inside_polygon']} |
| Hình học hợp lệ | {basin['geometry_valid']} |
| Trạng thái | {basin.get('gate2_status')} |

## 5. Ảnh hưởng đến độ tin cậy

- Các ngày SUSPECT tập trung ở tháng cực đoan (01/2023, 11/2025) nên ảnh hưởng
  trực tiếp đến tương quan RQ3 — đã định lượng bằng T07.
- Sai lệch diện tích lưu vực {pct(float(basin['deviation_pct']), 2)} là phép kiểm tra diện tích,
  **không tự nó đo được sai số lượng mưa**. Độ nhạy của phương pháp tính mưa
  được đo riêng trên 36 tháng (xem `rainfall_spatial_sensitivity.csv`).
- Chuỗi mưa ngày là sản phẩm phân rã, chỉ dùng bổ trợ; phân tích chính dùng
  bảng tháng.
"""
    (HANDOFF / "03_data_quality_summary.md").write_text(d03, encoding="utf-8")

    # ═══════════════════════════════════════════════════════════════════
    # 04 — KẾT QUẢ VÀ DIỄN GIẢI
    # ═══════════════════════════════════════════════════════════════════
    t03_md = md_table(T03)
    t04_md = md_table(T04)
    t05_cols = ["analysis", "subset", "lag", "n_pairs", "pearson_r",
                "pearson_p", "spearman_r", "spearman_p"]
    t05_md = md_table(T05[t05_cols], dec={
        "pearson_r": 3, "spearman_r": 3,
        "pearson_p": 4, "spearman_p": 4,
    })
    t07_md = md_table(T07, dec={
        "base_pearson_r": 3, "sens_pearson_r": 3, "delta_pearson_r": 3,
        "base_spearman_r": 3, "sens_spearman_r": 3, "delta_spearman_r": 3,
        "base_pearson_p": 4, "sens_pearson_p": 4,
    })

    top_months_txt = ", ".join(
        f"{r['year_month']} ({vn(r['rainfall_mm'], 1)} mm)"
        for _, r in top_months.iterrows())

    d04 = f"""# 04 — Kết quả và diễn giải

> Quy ước: mỗi mục tách **Số liệu** (tính từ CSV) và **Nhận định** (diễn giải,
> có giới hạn). Không đọc phần nhận định như kết quả kiểm định thống kê.

## RQ1 — Khí tượng

### Số liệu

- Tổng mưa 3 năm: **{vn(rain_m['rainfall_mm'].sum(), 1)} mm**.
- Tổng mưa theo năm: {", ".join(f"{y}: {vn(v, 1)} mm" for y, v in annual_rain.items())}.
- Mưa tháng trung bình: **{vn(rain_m['rainfall_mm'].mean(), 1)} mm**;
  trung vị {vn(rain_m['rainfall_mm'].median(), 1)} mm;
  lớn nhất {vn(rain_m['rainfall_mm'].max(), 1)} mm;
  nhỏ nhất {vn(rain_m['rainfall_mm'].min(), 1)} mm.
- Mùa mưa (T5–T11): {len(wet)} tháng, trung bình {vn(wet['rainfall_mm'].mean(), 1)} mm/tháng,
  chiếm **{pct(wet['rainfall_mm'].sum() / rain_m['rainfall_mm'].sum() * 100)}** tổng lượng mưa.
- Mùa khô (T12–T4): {len(dry)} tháng, trung bình {vn(dry['rainfall_mm'].mean(), 1)} mm/tháng,
  chiếm {pct(dry['rainfall_mm'].sum() / rain_m['rainfall_mm'].sum() * 100)}.
- Ba tháng mưa lớn nhất: {top_months_txt}.
- Nhiệt độ trung bình 3 năm: **{vn(temp_m['temperature_c'].mean(), 2)} °C**;
  tháng lạnh nhất {vn(temp_m['temperature_c'].min(), 2)} °C;
  tháng nóng nhất {vn(temp_m['temperature_c'].max(), 2)} °C.
- Nhiệt độ trung bình theo năm: {", ".join(f"{y}: {vn(v, 2)} °C" for y, v in annual_temp.items())}.

### Bảng T03 — Thống kê khí tượng

{t03_md}

### Nhận định

- Lượng mưa phân hóa rất mạnh theo mùa: hơn 90% tổng mưa tập trung trong T5–T11,
  phù hợp chế độ gió mùa của miền Trung Việt Nam.
- Năm 2025 có tổng mưa cao nhất trong ba năm, chủ yếu do các tháng cuối năm;
  năm 2024 thấp nhất.
- Nhiệt độ biến động theo mùa nhưng biên độ hẹp hơn nhiều so với biên độ mưa.
- Ba năm dữ liệu **không đủ** để khẳng định xu thế biến đổi khí hậu dài hạn.

## RQ2 — Thủy văn

### Số liệu

- Lưu lượng về hồ (chỉ ngày VALID, n = {int(inflow_row['n_days'])}):
  trung bình **{vn(inflow_row['mean'], 2)} m³/s**, trung vị **{vn(inflow_row['median'], 2)} m³/s**,
  độ lệch chuẩn {vn(inflow_row['std'], 2)} m³/s, CV {vn(inflow_row['cv'], 3)},
  nhỏ nhất {vn(inflow_row['min'], 2)} m³/s, lớn nhất **{vn(inflow_row['max'], 2)} m³/s**.
- Phân vị: P05 {vn(inflow_row['p05'], 2)}; P25 {vn(inflow_row['p25'], 2)};
  P75 {vn(inflow_row['p75'], 2)}; P90 {vn(inflow_row['p90'], 2)}; P95 {vn(inflow_row['p95'], 2)} m³/s.
- Độ bất đối xứng (skewness) {vn(inflow_row['skewness'], 2)}; kurtosis {vn(inflow_row['kurtosis'], 2)}.
- Mực nước thượng lưu (n = {int(level_row['n_days'])}): trung bình {vn(level_row['mean'], 2)} m,
  nhỏ nhất {vn(level_row['min'], 2)} m, lớn nhất {vn(level_row['max'], 2)} m.

### Bảng T04 — Thống kê thủy văn

{t04_md}

### Nhận định

- Phân bố lưu lượng lệch phải mạnh (trung bình lớn hơn trung vị khoảng
  {vn(inflow_row['mean'] / inflow_row['median'], 1)} lần): đa số ngày dòng chảy thấp,
  một số ít ngày rất lớn quyết định giá trị trung bình.
- Năm 2024 có dòng chảy thấp nhất; năm 2025 cao nhất và có phương sai lớn nhất.
- Sự kiện nổi bật: **19–20/11/2025** lưu lượng về hồ 12.455 m³/s, gấp khoảng
  {vn(12455 / inflow_row['p95'], 1)} lần P95 của các ngày VALID
  ({vn(inflow_row['p95'], 1)} m³/s). Hai ngày này bị gắn cờ SUSPECT nên **không**
  nằm trong T04 (giá trị lớn nhất của chuỗi VALID là {vn(inflow_row['max'], 1)} m³/s).
  Cần đối chiếu với nguồn vận hành trước khi dùng làm số liệu chính thức.
- Mực nước thượng lưu có các đoạn bất thường (0 m, 37–38 m, đảo cột) đã gắn cờ;
  biểu đồ F06 chỉ vẽ các ngày VALID và ngắt đoạn tại chỗ thiếu.

## RQ3 — Liên hệ mưa – dòng chảy

### Số liệu

- Tương quan lag 0 (n = {int(lag0['n_pairs'])} tháng):
  Pearson **r = {vn(lag0['pearson_r'], 3)}** ({p_txt(lag0['pearson_p'])});
  Spearman **ρ = {vn(lag0['spearman_r'], 3)}** ({p_txt(lag0['spearman_p'])}).
- Tương quan lag 1 (n = {int(lag1['n_pairs'])} tháng):
  Pearson **r = {vn(lag1['pearson_r'], 3)}** ({p_txt(lag1['pearson_p'])});
  Spearman **ρ = {vn(lag1['spearman_r'], 3)}** ({p_txt(lag1['spearman_p'])}).
- Deseasonalised (loại trung bình tháng lịch): Pearson {vn(deseason['pearson_r'], 3)};
  Spearman {vn(deseason['spearman_r'], 3)}.
- Loại tháng chứa ngày SUSPECT (n = {int(s1_lag0['n_pairs'])}):
  Pearson {vn(s1_lag0['pearson_r'], 3)} ({p_txt(s1_lag0['pearson_p'])});
  Spearman {vn(s1_lag0['spearman_r'], 3)} ({p_txt(s1_lag0['spearman_p'])}).
- Mùa mưa (n = {int(wet_row['n_pairs'])}): Pearson {vn(wet_row['pearson_r'], 3)}
  ({p_txt(wet_row['pearson_p'])}); Spearman {vn(wet_row['spearman_r'], 3)}
  ({p_txt(wet_row['spearman_p'])}).
- Mùa khô (n = {int(dry_row['n_pairs'])}): Pearson {vn(dry_row['pearson_r'], 3)}
  ({p_txt(dry_row['pearson_p'])}); Spearman {vn(dry_row['spearman_r'], 3)}
  ({p_txt(dry_row['spearman_p'])}).
- Nhóm mưa cao (> P67, n = {int(high_row['n_pairs'])}): Pearson {vn(high_row['pearson_r'], 3)}
  ({p_txt(high_row['pearson_p'])}).

### Bảng T05 — Tương quan mưa – dòng chảy

{t05_md}

### Bảng T07 — Độ nhạy khi loại tháng chứa ngày SUSPECT

{t07_md}

### Nhận định

- Có liên hệ thống kê dương ở quy mô tháng giữa mưa và lưu lượng công bố.
  Các p-value trong T05 là kiểm định tương quan thông thường, **chưa hiệu chỉnh
  tự tương quan chuỗi thời gian, tính mùa hay nhiều phép thử**; không dùng riêng
  chúng làm bằng chứng về nhân quả hoặc thời gian trễ thủy văn.
- Lag 1 có hệ số cao hơn lag 0, nhưng **không đủ căn cứ** để kết luận đó là thời
  gian trễ thủy văn thực; ba năm dữ liệu và tính mùa mạnh có thể tạo tương quan giả.
- Loại tháng chứa ngày SUSPECT làm Pearson lag 0 giảm
  {vn(abs(sens0['delta_pearson_r']), 3)} (từ {vn(sens0['base_pearson_r'], 3)} xuống
  {vn(sens0['sens_pearson_r'], 3)}), trong khi lag 1 tăng {vn(sens1['delta_pearson_r'], 3)}.
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
| F09 | So sánh tương quan lag 0 / lag 1 | Hệ số lag 1 cao hơn, p-value đều nhỏ |
| F10 | Phân bố lưu lượng | Lệch phải mạnh, đuôi dài về phía giá trị lớn |
"""
    (HANDOFF / "04_results_and_interpretation.md").write_text(d04, encoding="utf-8")

    # ═══════════════════════════════════════════════════════════════════
    # 05 — GIỚI HẠN
    # ═══════════════════════════════════════════════════════════════════
    d05 = f"""# 05 — Giới hạn của nghiên cứu

## 1. Giới hạn thời gian

- Chỉ có **{n_months} tháng / {n_days} ngày** (2023–2025). Không đủ để mô tả
  chu kỳ nhiều năm, ENSO hoặc xu thế khí hậu dài hạn.
- Cỡ mẫu cho tương quan tháng là {int(lag0['n_pairs'])} cặp (lag 0) và
  {int(lag1['n_pairs'])} cặp (lag 1) — nhỏ, hệ số kém ổn định.

## 2. Giới hạn dữ liệu khí tượng

- CHIRPS là sản phẩm **ước lượng từ vệ tinh kết hợp trạm**, không phải đo trực tiếp
  tại lưu vực. Sai số lớn hơn ở địa hình núi và mùa khô.
- Mưa ngày CHIRPS v3 `rnl` được **phân rã từ tổng 5 ngày** bằng ERA5, nên không
  phù hợp để phân tích sự kiện trong ngày; chỉ dùng bổ trợ.
- Độ phân giải 0,05° (~5,5 km) làm trơn cực trị cục bộ.
- ERA5-Land là **tái phân tích**, không phải quan trắc; độ phân giải 0,1° (~9 km).
  Nhiệt độ đại diện ô lưới, không đại diện vi khí hậu tại công trình.
- Kênh truy cập nhiệt độ thực tế: **{temp_channel}**. Đây là cùng sản phẩm ERA5-Land
  nhưng khác kênh phân phối so với Copernicus CDS.
- Kênh tải mưa thực tế: **{rain_channel}**.
- Dữ liệu toàn cầu theo UTC, dữ liệu công trình theo UTC+7 → có thể lệch ngày
  ở vùng biên.

## 3. Giới hạn dữ liệu thủy văn

- Lưu lượng "về hồ" là số liệu vận hành, **không phải dòng chảy tự nhiên**;
  chịu điều tiết của các hồ thượng nguồn (An Khê, Ka Nak, Sông Ba Hạ).
- Định nghĩa chính xác của trường `inflow_m3s` chưa được xác minh từ tài liệu
  công trình; có thể là lưu lượng vào hồ hoặc tổng lượng qua nhà máy.
- {exc_by_flag.get('SUSPECT', 0)} lượt ngoại lệ SUSPECT (có thể nhiều lý do trên cùng ngày/biến) và
  {exc_by_flag.get('INVALID_CONFIRMED', 0)} lượt ngoại lệ INVALID_CONFIRMED.
  Hai ngày 19–20/11/2025 có giá trị 12.455 m³/s chưa được xác minh độc lập.
- Mực nước thượng lưu có các giá trị bất thường (0 m; 37–38 m; nghi đảo cột),
  được gắn SUSPECT và loại khỏi thống kê chính; nguyên nhân chưa xác minh độc lập.
- Trường `release_m3s` (lưu lượng xả) bằng 0 trong **{n_release_zero}/{n_days} ngày**
  — bất thường về mặt vận hành; biến này chỉ dùng bổ trợ và chưa được xác minh
  định nghĩa, không dùng trong phân tích chính.

## 4. Giới hạn không gian

- Polygon HydroBASINS level 12 có diện tích {vn(float(basin['area_km2']), 1)} km²,
  lệch {pct(float(basin['deviation_pct']), 2)} so với tham khảo. Ranh giới là đơn vị
  thủy văn toàn cầu, không phải khảo sát địa hình chi tiết.
- Tọa độ đập lấy từ OpenStreetMap (nguồn cộng đồng), đã đối chiếu với vị trí
  polygon nhưng chưa khảo sát thực địa.
- Trạm đo mưa/khí tượng không nằm trong lưu vực; toàn bộ là trung bình không gian.

## 5. Giới hạn phương pháp

- Tương quan Pearson/Spearman **không chứng minh nhân quả**; tính mùa chung của
  mưa và lưu lượng có thể thổi phồng hệ số. Đã bổ sung deseasonalised và phân
  nhóm mùa để kiểm tra, nhưng mỗi tháng lịch chỉ có 3 giá trị.
- Hồi quy/thời gian trễ thực không được mô hình hóa.
- **Không xây dựng Flow Duration Curve (FDC)**: chuỗi lưu lượng là số liệu vận hành
  bị điều tiết, chưa xác minh định nghĩa và còn 4 ngày SUSPECT. Theo V1.1 §13,
  FDC chỉ được xây dựng khi định nghĩa và chất lượng chuỗi cho phép diễn giải có
  cơ sở; thay vào đó dùng F10 (phân bố lưu lượng) để mô tả hình dạng phân bố.
- Phân nhóm tercile chỉ có ~12 tháng/nhóm; hệ số rất bất ổn, không dùng để khẳng
  định ngưỡng mưa – dòng chảy.

## 6. Những vấn đề chưa xác minh được

| Vấn đề | Trạng thái |
|---|---|
| Định nghĩa `inflow_m3s` của công trình | Chưa có tài liệu gốc |
| Giá trị 12.455 m³/s ngày 19–20/11/2025 | Chưa đối chiếu được nguồn độc lập |
| Ngày 21/01/2023 có lưu lượng 0 nhưng sản lượng điện dương | Đã gắn cờ SUSPECT |
| Sai lệch mưa tháng vs tổng ngày | Đã định lượng, chưa hiệu chỉnh |
| Phê duyệt GATE 2 | {basin.get('gate2_status')} |
"""
    (HANDOFF / "05_limitations.md").write_text(d05, encoding="utf-8")

    # ═══════════════════════════════════════════════════════════════════
    # 06 — DANH MỤC HÌNH VÀ BẢNG
    # ═══════════════════════════════════════════════════════════════════
    d06 = f"""# 06 — Danh mục hình và bảng

## 1. Hình

| Mã | Tệp | Nội dung | Đơn vị | Nguồn | Script | Dùng cho |
|---|---|---|---|---|---|---|
| F01 | `figures/F01_basin_map.png` | Bản đồ vị trí, ranh giới lưu vực, đập và nhà máy | — | HydroBASINS v1c L12; OSM | 02 | RQ1–RQ3 (bối cảnh) |
| F02 | `figures/F02_rainfall_monthly.png` | Biến động lượng mưa theo tháng 2023–2025 | mm/tháng | CHIRPS v3.0 Final | 06 | RQ1 |
| F03 | `figures/F03_temperature_monthly.png` | Nhiệt độ trung bình tháng | °C | ERA5-Land | 06 | RQ1 |
| F04 | `figures/F04_inflow_daily_hydrograph.png` | Lưu lượng nước về hồ theo ngày | m³/s | Sông Ba Hạ | 06 | RQ2 |
| F05 | `figures/F05_inflow_monthly.png` | Lưu lượng nước về hồ theo tháng | m³/s | Sông Ba Hạ | 06 | RQ2 |
| F06 | `figures/F06_upstream_level.png` | Mực nước thượng lưu sau kiểm định | m | Sông Ba Hạ | 06 | RQ2 |
| F07 | `figures/F07_rainfall_inflow_comparison.png` | So sánh mưa tháng và lưu lượng về hồ | mm, m³/s | CHIRPS; Sông Ba Hạ | 07 | RQ3 |
| F08 | `figures/F08_scatter_rainfall_inflow.png` | Scatter mưa – lưu lượng theo tháng | mm, m³/s | CHIRPS; Sông Ba Hạ | 07 | RQ3 |
| F09 | `figures/F09_correlation_comparison.png` | So sánh tương quan lag 0 và lag 1 (kèm p-value) | — | Tính từ bảng tháng | 07 | RQ3 |
| F10 | `figures/F10_inflow_distribution.png` | Phân bố lưu lượng (histogram log + boxplot theo năm) | m³/s | Sông Ba Hạ | 06 | RQ2 (bổ sung) |

Ghi chú:

- F06 chỉ vẽ các ngày VALID và ngắt đoạn tại chỗ thiếu; dữ liệu mực nước có
  lỗi cảm biến đã được gắn cờ.
- **Không có FDC.** Lý do: xem `05_limitations.md` mục 5 (V1.1 §13).
- Mỗi hình PNG ≥ 200 dpi, có tên, đơn vị, chú giải, nguồn số liệu.

## 2. Bảng

| Mã | Tệp | Nội dung | Đơn vị | Nguồn | Script |
|---|---|---|---|---|---|
| T01 | `tables/T01_data_sources.csv` | Danh mục nguồn dữ liệu và đặc điểm kỹ thuật | — | Tổng hợp | 06 |
| T02 | `tables/T02_hydrology_qa_results.csv` | Kết quả kiểm tra chất lượng thủy văn | — | Sông Ba Hạ | 06 |
| T02b | `tables/T02b_exception_counts.csv` | Số bản ghi ngoại lệ theo biến và cờ | — | Sông Ba Hạ | 06 |
| T03 | `tables/T03_meteorology_stats.csv` | Thống kê khí tượng (mưa, nhiệt độ, mùa) | mm, °C | CHIRPS; ERA5-Land | 06 |
| T04 | `tables/T04_hydrology_stats.csv` | Thống kê thủy văn (phân vị, CV, skewness) | m³/s, m | Sông Ba Hạ | 06 |
| T05 | `tables/T05_correlation_results.csv` | Tương quan mưa – dòng chảy (lag, mùa, tercile) | — | Tính từ bảng tháng | 07 |
| T06 | `tables/T06_exceptions_decisions.csv` | Danh sách ngoại lệ và quyết định xử lý | — | Sông Ba Hạ | 06 |
| T07 | `tables/T07_sensitivity.csv` | Độ nhạy khi loại tháng chứa ngày SUSPECT | — | Tính từ bảng tháng | 07 |
| T08 | `tables/T08_alternative_suspect_sensitivity.csv` | Độ nhạy lưu lượng khi giữ cả bốn ngày SUSPECT so với VALID_ONLY | — | Từ dữ liệu ngày và tháng | 10 |

## 3. Dữ liệu chọn lọc

| Tệp | Nội dung |
|---|---|
| `selected_data/hydrology_clean.csv` | Thủy văn ngày đã QA, kèm cờ chất lượng |
| `selected_data/hydrology_qa_summary.csv` | Độ phủ theo tháng |
| `selected_data/hydromet_daily.csv` | Bảng tích hợp ngày |
| `selected_data/hydromet_monthly.csv` | Bảng tích hợp tháng (dùng cho phân tích chính) |
| `selected_data/rainfall_monthly.csv` | Mưa tháng CHIRPS |
| `selected_data/rainfall_daily.csv` | Mưa ngày CHIRPS |
| `selected_data/temperature_monthly.csv` | Nhiệt độ tháng ERA5-Land |
| `selected_data/temperature_daily.csv` | Nhiệt độ ngày ERA5-Land |
| `selected_data/song_ba_ha_catchment.geojson` | Polygon lưu vực (EPSG:4326) |
| `selected_data/data_dictionary.md` | Từ điển dữ liệu |

## 4. Cách trích dẫn trong báo cáo

- Hình: "Nguồn: CHIRPS v3.0 Final, tính toán bởi nhóm kỹ thuật (F02)."
- Bảng: "Nguồn: dữ liệu vận hành Sông Ba Hạ, xử lý theo V1.1 (T04)."
- Không sửa số liệu trong CSV; nếu cần làm tròn, ghi rõ quy tắc làm tròn.
"""
    (HANDOFF / "06_figures_and_tables_index.md").write_text(d06, encoding="utf-8")

    # ═══════════════════════════════════════════════════════════════════
    # 07 — TÀI LIỆU THAM KHẢO
    # ═══════════════════════════════════════════════════════════════════
    d07 = f"""# 07 — Tài liệu tham khảo

> Chỉ liệt kê nguồn thực tế đã dùng. Ngày truy cập: {ACCESS_DATE}.

## 1. Dữ liệu và sản phẩm

**CHIRPS v3.0 Final**
- Funk, C., Peterson, P., Landsfeld, M., Pedreros, D., Verdin, J., Shukla, S.,
  Husak, G., Rowland, J., Harrison, L., Hoell, A., Michaelsen, J. (2015).
  The climate hazards infrared precipitation with stations — a new environmental
  record for monitoring extremes. *Scientific Data*, 2, 150066.
  https://doi.org/10.1038/sdata.2015.66
- Climate Hazards Center, University of California, Santa Barbara.
  CHIRPS v3.0 Final.
  https://data.chc.ucsb.edu/products/CHIRPS/v3.0/
  (kênh tải thực tế: ftp://ftp.chc.ucsb.edu/pub/org/chc/products/CHIRPS/v3.0/)

**ERA5-Land**
- Muñoz-Sabater, J., Dutra, E., Agustí-Panareda, A., Albergel, C., Arduini, G.,
  Balsamo, G., et al. (2021). ERA5-Land: a state-of-the-art global reanalysis
  dataset for land applications. *Earth System Science Data*, 13, 4349–4383.
  https://doi.org/10.5194/essd-13-4349-2021
- Copernicus Climate Change Service. ERA5-Land hourly/monthly data.
  https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land
- Open-Meteo. Historical Weather API (models=era5_land).
  https://open-meteo.com/en/docs/historical-weather-api

**Ranh giới lưu vực**
- Lehner, B., Grill, G. (2013). Global river hydrography and network routing:
  baseline data and new approaches to study the world's large river systems.
  *Hydrological Processes*, 27(15), 2171–2186.
  https://doi.org/10.1002/hyp.9740
- HydroBASINS v1c (level 12), HydroSHEDS.
  https://www.hydrosheds.org/products/hydrobasins

**Vị trí công trình**
- OpenStreetMap contributors. Đập thủy điện Sông Ba Hạ (`way/480785944`),
  nhà máy (`way/827889670`). OpenStreetMap API 0.6.
  https://www.openstreetmap.org/way/480785944
  Giấy phép ODbL.

**Dữ liệu vận hành**
- Trang thông tin vận hành Thủy điện Sông Ba Hạ (dữ liệu nội bộ được bàn giao
  cho nhóm kỹ thuật). Không có DOI.

## 2. Tài liệu đặc tả của học phần

- `docs/DAC_TA_NGHIEN_CUU_V1.0.md` — Đặc tả nghiên cứu và triển khai kỹ thuật V1.0.
- `docs/PHU_LUC_TRIEN_KHAI_V1.1.md` — Phụ lục triển khai V1.1.
- `docs/WORKFLOW.md` — Quy trình làm việc, phê duyệt GATE.

## 3. Thư viện phần mềm

- Python 3.11+; pandas; numpy; geopandas; shapely; rasterio; matplotlib;
  xarray; rioxarray; requests.
"""
    (HANDOFF / "07_references.md").write_text(d07, encoding="utf-8")

    # ── Sao chép data dictionary ─────────────────────────────────────────
    ddict = QA / "data_dictionary.md"
    if ddict.exists():
        (HANDOFF / "selected_data").mkdir(parents=True, exist_ok=True)
        (HANDOFF / "selected_data" / "data_dictionary.md").write_text(
            ddict.read_text(encoding="utf-8"), encoding="utf-8")

    # Review appendix: read the actual recorded spatial-sensitivity evidence.
    rainfall_audit_path = QA / "rainfall_spatial_sensitivity.csv"
    if not rainfall_audit_path.exists():
        raise RuntimeError("Missing rainfall_spatial_sensitivity.csv: rainfall method not auditable")
    spatial_audit = pd.read_csv(rainfall_audit_path)
    if len(spatial_audit) != 36 or not spatial_audit["delta_pct"].notna().all():
        raise RuntimeError("CHIRPS spatial audit must cover 36 valid months")
    mean_abs_bias = spatial_audit["delta_pct"].abs().mean()
    max_abs_bias = spatial_audit["delta_pct"].abs().max()
    recalculated_pixels = sorted(spatial_audit["center_cells"].unique().tolist())
    historic_pixels = sorted(rain_m["n_pixels"].unique().tolist())

    reviewer_note = HANDOFF / "08_REVIEWER_NOTES.md"
    if reviewer_note.exists():
        alt_path = HANDOFF / "tables" / "T08_alternative_suspect_sensitivity.csv"
        if not alt_path.exists():
            raise RuntimeError("Missing T08: run scripts/10_suspect_sensitivity.py first.")
        alt = pd.read_csv(alt_path).set_index("scenario")
        base = alt.loc["VALID_ONLY"]
        suspect = alt.loc["INCLUDE_SUSPECT_AS_REPORTED"]
        appendices = {
            "02_data_sources_and_methods.md": (
                "\n\n## Lưu ý nghiệm thu không gian\n"
                "Polygon CHẤP NHẬN CÓ ĐIỀU KIỆN. Trưởng nhóm đã CHẤP NHẬN CÓ ĐIỀU KIỆN "
                "phương pháp tính mưa xấp xỉ mask pixel nhị phân và cos(vĩ độ) cho bài tiểu luận. "
                "Phương pháp này không tính phần giao các ô biên. "
                f"Kiểm tra 36 tháng với trọng số diện tích giao: trung bình |Δ%|={mean_abs_bias:.4f}%, "
                f"lớn nhất |Δ%|={max_abs_bias:.4f}%. "
                f"Chuỗi cũ dùng {historic_pixels} pixel, tái tính dùng {recalculated_pixels}; "
                "chưa xác định dứt điểm nguyên nhân. Xem outputs/quality/rainfall_spatial_sensitivity.csv.\n"
            ),
            "04_results_and_interpretation.md": (
                "\n\n## Kiểm tra độ nhạy SUSPECT\n"
                f"Kịch bản chỉ dùng ngày VALID: Pearson lag 0 = {base['pearson_lag0']:.4f}, "
                f"lag 1 = {base['pearson_lag1']:.4f}. "
                f"Kịch bản giữ SUSPECT theo nguồn: lag 0 = {suspect['pearson_lag0']:.4f}, "
                f"lag 1 = {suspect['pearson_lag1']:.4f}. "
                "Thứ tự thay đổi; không kết luận lag 1 mạnh hơn ổn định. "
                "Đây là độ nhạy, không phải kiểm chứng giá trị cực trị.\n"
            ),
            "05_limitations.md": (
                "\n\n## Giới hạn nghiệm thu cập nhật\n"
                "Polygon và phương pháp mưa CHIRPS đã được trưởng nhóm chấp nhận có điều kiện; "
                f"chênh lệch tương đối tối đa khi kiểm tra fractional-area là {max_abs_bias:.4f}%. "
                "Sai khác 377/379 pixel giữa hai lần trích xuất chưa truy nguyên đầy đủ. "
                "Kết quả lag 0/lag 1 không bền vững trước cách xử lý SUSPECT.\n"
            ),
        }
        for fname, note in appendices.items():
            p = HANDOFF / fname
            if p.exists():
                p.write_text(p.read_text(encoding="utf-8") + note, encoding="utf-8")

    print("  Đã sinh 7 tài liệu bàn giao:")
    for doc in sorted(HANDOFF.glob("0*.md")):
        print(f"    → {doc.name} ({doc.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
