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

Lưu ý:
    - GATE 2 yêu cầu tải HydroBASINS (~500 MB) và cần phê duyệt polygon
      trước khi tiếp tục GATE 3.
    - GATE 3 yêu cầu tải CHIRPS (~36 tháng × ~50 MB) và ERA5-Land (cdsapi).
    - Có thể chạy từng script riêng lẻ nếu cần.
    - Thêm --skip-download để bỏ qua các bước tải nếu đã có dữ liệu.
    - Thêm --gate N để chạy từ GATE N trở đi.
"""

import sys
import os
import subprocess
import argparse
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

    print("\n" + "=" * 60)
    if errors:
        print(f"  Pipeline kết thúc với {len(errors)} lỗi:")
        for e in errors:
            print(f"    ❌ {e}")
        return 1
    else:
        print("  ✅ Toàn bộ pipeline hoàn thành thành công!")
        print("\n  Bước tiếp theo:")
        print("  1. Kiểm tra outputs/ (hình, bảng, chất lượng)")
        print("  2. Hoàn thiện handoff_writer/ cho người viết báo cáo")
        print("  3. Đối chiếu với các GATE issues trên GitHub")
        return 0


if __name__ == "__main__":
    sys.exit(main())
