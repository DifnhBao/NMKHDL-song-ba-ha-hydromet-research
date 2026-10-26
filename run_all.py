#!/usr/bin/env python3
"""
run_all.py — Chạy toàn bộ quy trình phân tích
================================================
Thực thi tuần tự các script theo thứ tự phụ thuộc V1.1.

Thứ tự:
    1. 01_hydrology_qa.py       (GATE 1 — P0)
    2. 02_basin_delineation.py  (GATE 2 — P0, cần phê duyệt)
    3. 03_chirps_extraction.py  (GATE 3a — P0, sau GATE 2)
    4. 04_temperature_extraction.py (GATE 3b — P0)
    5. 05_data_integration.py   (GATE 4 — P0)
    6. 06_exploratory_analysis.py   (GATE 5a — P0)
    7. 07_rainfall_runoff_analysis.py (GATE 5b — P0)
    8. Bàn giao (GATE 6): sao chép kết quả vào handoff_writer/

Lưu ý:
    - GATE 2 yêu cầu tải HydroBASINS (~500 MB) và cần phê duyệt polygon
      trước khi tiếp tục GATE 3.
    - GATE 3 yêu cầu tải CHIRPS (~36 tháng × ~50 MB) và ERA5-Land (cdsapi).
    - Có thể chạy từng script riêng lẻ nếu cần.
    - Thêm --gate N để chạy từ GATE N trở đi.
"""

import sys
import os
import subprocess
import argparse
import shutil
from pathlib import Path

# Đảm bảo in tiếng Việt trên Windows
os.environ["PYTHONIOENCODING"] = "utf-8"


ROOT = Path(__file__).resolve().parent
SCRIPTS_DIR = ROOT / "scripts"

PIPELINE = [
    {"gate": 1, "script": "01_hydrology_qa.py",
     "desc": "GATE 1 — Kiểm định dữ liệu thủy văn"},
    {"gate": 2, "script": "02_basin_delineation.py",
     "desc": "GATE 2 — Xác định ranh giới lưu vực"},
    {"gate": 3, "script": "03_chirps_extraction.py",
     "desc": "GATE 3a — Trích xuất mưa CHIRPS v3"},
    {"gate": 3, "script": "04_temperature_extraction.py",
     "desc": "GATE 3b — Trích xuất nhiệt độ ERA5-Land"},
    {"gate": 4, "script": "05_data_integration.py",
     "desc": "GATE 4 — Tích hợp dữ liệu"},
    {"gate": 5, "script": "06_exploratory_analysis.py",
     "desc": "GATE 5a — Phân tích khám phá (RQ1 + RQ2)"},
    {"gate": 5, "script": "07_rainfall_runoff_analysis.py",
     "desc": "GATE 5b — Phân tích mưa–dòng chảy (RQ3)"},
]


def run_script(script_name, desc):
    """Chạy một script, trả về exit code."""
    script_path = SCRIPTS_DIR / script_name
    if not script_path.exists():
        print(f"  [LỖI] Không tìm thấy: {script_path}")
        return 1

    print(f"\n{'─' * 60}")
    print(f"  {desc}")
    print(f"  Script: {script_name}")
    print(f"{'─' * 60}")

    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=str(ROOT),
    )
    return result.returncode


def gate6_handoff():
    """GATE 6 — Bàn giao: sao chép kết quả vào handoff_writer/.

    Theo V1.1 §18:
      - handoff_writer/figures/  ← outputs/figures/ + outputs/maps/
      - handoff_writer/tables/   ← outputs/tables/
      - handoff_writer/selected_data/ ← dữ liệu tích hợp chính
    """
    print(f"\n{'─' * 60}")
    print("  GATE 6 — Bàn giao: sao chép kết quả vào handoff_writer/")
    print(f"{'─' * 60}")

    handoff = ROOT / "handoff_writer"
    hw_figures = handoff / "figures"
    hw_tables = handoff / "tables"
    hw_data = handoff / "selected_data"

    hw_figures.mkdir(parents=True, exist_ok=True)
    hw_tables.mkdir(parents=True, exist_ok=True)
    hw_data.mkdir(parents=True, exist_ok=True)

    copied = 0
    skipped = 0

    # ── Sao chép hình từ outputs/figures/ ─────────────────────────────
    src_figures = ROOT / "outputs" / "figures"
    if src_figures.exists():
        for f in src_figures.glob("*.png"):
            dest = hw_figures / f.name
            shutil.copy2(f, dest)
            print(f"  → figures/{f.name}")
            copied += 1

    # ── Sao chép bản đồ từ outputs/maps/ ─────────────────────────────
    src_maps = ROOT / "outputs" / "maps"
    if src_maps.exists():
        for f in src_maps.glob("*.png"):
            dest = hw_figures / f.name
            shutil.copy2(f, dest)
            print(f"  → figures/{f.name} (từ maps/)")
            copied += 1

    # ── Sao chép bảng từ outputs/tables/ ──────────────────────────────
    src_tables = ROOT / "outputs" / "tables"
    if src_tables.exists():
        for f in src_tables.glob("*.csv"):
            dest = hw_tables / f.name
            shutil.copy2(f, dest)
            print(f"  → tables/{f.name}")
            copied += 1

    # ── Sao chép dữ liệu chính vào selected_data/ ────────────────────
    selected_files = [
        "hydromet_daily.csv",
        "hydromet_monthly.csv",
        "hydrology_clean.csv",
        "hydrology_qa_summary.csv",
        "rainfall_monthly.csv",
        "temperature_monthly.csv",
    ]
    proc_dir = ROOT / "data" / "processed"
    for fname in selected_files:
        src = proc_dir / fname
        if src.exists():
            dest = hw_data / fname
            shutil.copy2(src, dest)
            print(f"  → selected_data/{fname}")
            copied += 1
        else:
            print(f"  ⚠️ Chưa có: {fname}")
            skipped += 1

    # ── Sao chép GeoJSON lưu vực ──────────────────────────────────────
    geojson = proc_dir / "song_ba_ha_catchment.geojson"
    if geojson.exists():
        dest = hw_data / geojson.name
        shutil.copy2(geojson, dest)
        print(f"  → selected_data/{geojson.name}")
        copied += 1

    print(f"\n  Sao chép: {copied} tệp, bỏ qua: {skipped} tệp")

    if copied == 0:
        print("  ⚠️ Không có tệp nào được sao chép. Kiểm tra các GATE trước.")
        return 1

    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Chạy toàn bộ quy trình phân tích khí tượng thủy văn Sông Ba Hạ"
    )
    parser.add_argument(
        "--gate", type=int, default=1,
        help="Chạy từ GATE N trở đi (mặc định: 1)"
    )
    args = parser.parse_args()

    print("=" * 60)
    print("  QUY TRÌNH PHÂN TÍCH KHÍ TƯỢNG THỦY VĂN SÔNG BA HẠ")
    print("  Đặc tả V1.0 + Phụ lục V1.1")
    print("=" * 60)

    errors = []
    for step in PIPELINE:
        if step["gate"] < args.gate:
            print(f"\n⏭️  Bỏ qua: {step['desc']}")
            continue

        code = run_script(step["script"], step["desc"])
        if code != 0:
            errors.append(step["script"])
            print(f"\n❌ {step['script']} thất bại (exit code {code})")

            # GATE 2 thất bại → không thể tiếp tục GATE 3+
            if step["gate"] == 2:
                print("  → Dừng pipeline: GATE 2 là điều kiện tiên quyết cho GATE 3+")
                break
        else:
            print(f"\n✅ {step['desc']} — hoàn thành")

    # ── GATE 6: Bàn giao ─────────────────────────────────────────────
    if not errors and args.gate <= 6:
        code = gate6_handoff()
        if code != 0:
            errors.append("GATE 6 — Bàn giao")

    print("\n" + "=" * 60)
    if errors:
        print(f"  Pipeline kết thúc với {len(errors)} lỗi:")
        for e in errors:
            print(f"    ❌ {e}")
        return 1
    else:
        print("  ✅ Toàn bộ pipeline hoàn thành thành công!")
        print("\n  GATE 6 — Bàn giao hoàn tất:")
        print("  1. handoff_writer/figures/ — hình F01–F09")
        print("  2. handoff_writer/tables/  — bảng T01–T06")
        print("  3. handoff_writer/selected_data/ — dữ liệu chính")
        print("  4. handoff_writer/*.md — tài liệu cho người viết báo cáo")
        return 0


if __name__ == "__main__":
    sys.exit(main())
