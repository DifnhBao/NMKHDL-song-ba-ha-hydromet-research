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
    8. 08_write_handoff.py      (GATE 6 — sinh 7 tài liệu bàn giao)
    9. Bàn giao (GATE 6): sao chép kết quả vào handoff_writer/ và kiểm tra đủ bộ

Quy tắc cứng (V1.1 §17, §20):
    - GATE 2 phải được người giám sát phê duyệt trước khi dùng polygon cho
      GATE 3+. Phê duyệt đọc từ outputs/quality/gate2_approval.json.
    - Bất kỳ GATE nào lỗi (exit code ≠ 0) đều dừng pipeline: các bước sau phụ
      thuộc trực tiếp vào bước trước.
    - GATE 6 chỉ chạy khi đủ 9 hình, 6 bảng, 7 tài liệu handoff và dữ liệu chính.

Ví dụ:
    python run_all.py                 # chạy từ GATE 1
    python run_all.py --gate 3        # chạy từ GATE 3 (vẫn kiểm tra phê duyệt GATE 2)
    python run_all.py --status        # chỉ kiểm tra trạng thái các GATE
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

# Đảm bảo in tiếng Việt trên Windows
os.environ["PYTHONIOENCODING"] = "utf-8"
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


ROOT = Path(__file__).resolve().parent
SCRIPTS_DIR = ROOT / "scripts"
PROC_DIR = ROOT / "data" / "processed"
QA_DIR = ROOT / "outputs" / "quality"
APPROVAL_FILE = QA_DIR / "gate2_approval.json"

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
    {"gate": 6, "script": "08_write_handoff.py",
     "desc": "GATE 6 — Sinh tài liệu bàn giao"},
]

REQUIRED_FIGURES = [f"F{i:02d}" for i in range(1, 10)]
REQUIRED_TABLES = [f"T{i:02d}" for i in range(1, 7)]
REQUIRED_DOCS = [
    "01_project_overview.md",
    "02_data_sources_and_methods.md",
    "03_data_quality_summary.md",
    "04_results_and_interpretation.md",
    "05_limitations.md",
    "06_figures_and_tables_index.md",
    "07_references.md",
]
REQUIRED_DATA = [
    "hydromet_daily.csv",
    "hydromet_monthly.csv",
    "hydrology_clean.csv",
    "hydrology_qa_summary.csv",
    "rainfall_monthly.csv",
    "rainfall_daily.csv",
    "temperature_monthly.csv",
    "temperature_daily.csv",
    "song_ba_ha_catchment.geojson",
]


def check_gate2_approval():
    """Đọc và xác thực phê duyệt GATE 2 (V1.1 §17 GATE 2, §20)."""
    if not APPROVAL_FILE.exists():
        return False, (
            f"Thiếu tệp phê duyệt: {APPROVAL_FILE}\n"
            "  → Trình outputs/maps/F01_basin_map.png, outputs/quality/basin_method.md\n"
            "    và data/processed/basin_validation.csv cho người giám sát.\n"
            "  → Sau khi được duyệt, tạo gate2_approval.json với "
            '{"approved": true, "approved_by": "...", "approved_at": "...", '
            '"note": "..."}'
        )
    try:
        data = json.loads(APPROVAL_FILE.read_text(encoding="utf-8"))
    except Exception as exc:
        return False, f"Không đọc được {APPROVAL_FILE}: {exc}"

    if data.get("approved") is not True:
        return False, f"{APPROVAL_FILE} chưa có \"approved\": true"
    if not data.get("approved_by") or not data.get("approved_at"):
        return False, f"{APPROVAL_FILE} thiếu approved_by/approved_at"
    return True, f"Đã phê duyệt bởi {data['approved_by']} lúc {data['approved_at']}"


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


def verify_handoff(handoff):
    """Kiểm tra GATE 6: đủ hình, bảng, tài liệu, dữ liệu (V1.1 §17–18)."""
    problems = []

    fig_dir = handoff / "figures"
    for code in REQUIRED_FIGURES:
        matches = list(fig_dir.glob(f"{code}_*.png"))
        if not matches:
            problems.append(f"thiếu hình {code}")

    tab_dir = handoff / "tables"
    for code in REQUIRED_TABLES:
        matches = list(tab_dir.glob(f"{code}_*.csv"))
        if not matches:
            problems.append(f"thiếu bảng {code}")

    for doc in REQUIRED_DOCS:
        if not (handoff / doc).exists():
            problems.append(f"thiếu tài liệu {doc}")

    data_dir = handoff / "selected_data"
    for name in REQUIRED_DATA:
        if not (data_dir / name).exists():
            problems.append(f"thiếu dữ liệu {name}")

    # Chất lượng tối thiểu: không được bàn giao chuỗi mưa ngày rỗng
    rain = PROC_DIR / "rainfall_daily.csv"
    if rain.exists():
        try:
            import pandas as pd
            df = pd.read_csv(rain)
            n_nan = int(df["rainfall_mm"].isna().sum())
            if n_nan > 0:
                problems.append(
                    f"rainfall_daily.csv còn {n_nan}/{len(df)} dòng NaN")
        except Exception as exc:
            problems.append(f"không đọc được rainfall_daily.csv: {exc}")

    return problems


def gate6_handoff():
    """GATE 6 — Bàn giao: sao chép kết quả vào handoff_writer/ và kiểm tra."""
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
    missing = []

    for src_dir, dest_dir, pattern in [
        (ROOT / "outputs" / "figures", hw_figures, "*.png"),
        (ROOT / "outputs" / "maps", hw_figures, "*.png"),
        (ROOT / "outputs" / "tables", hw_tables, "*.csv"),
    ]:
        if not src_dir.exists():
            continue
        for f in src_dir.glob(pattern):
            shutil.copy2(f, dest_dir / f.name)
            print(f"  → {dest_dir.name}/{f.name}")
            copied += 1

    for fname in REQUIRED_DATA:
        src = PROC_DIR / fname
        if src.exists():
            shutil.copy2(src, hw_data / fname)
            print(f"  → selected_data/{fname}")
            copied += 1
        else:
            missing.append(fname)
            print(f"  ⚠️  Chưa có: {fname}")

    print(f"\n  Sao chép: {copied} tệp, thiếu: {len(missing)} tệp")

    problems = verify_handoff(handoff)
    if problems:
        print("\n  ❌ GATE 6 KHÔNG ĐẠT:")
        for p in problems:
            print(f"     - {p}")
        return 1

    print("\n  ✅ GATE 6 ĐẠT: đủ hình, bảng, tài liệu và dữ liệu.")
    return 0


def print_status():
    """In trạng thái các GATE dựa trên artifact hiện có."""
    print("=" * 60)
    print("  TRẠNG THÁI PIPELINE")
    print("=" * 60)

    checks = [
        ("GATE 1", (PROC_DIR / "hydrology_clean.csv").exists()),
        ("GATE 2 (kỹ thuật)", (PROC_DIR / "basin_validation.csv").exists()),
        ("GATE 3a — mưa ngày",
         (PROC_DIR / "rainfall_daily.csv").exists() and not
         _has_nan(PROC_DIR / "rainfall_daily.csv")),
        ("GATE 3b — nhiệt độ",
         (PROC_DIR / "temperature_daily.csv").exists()),
        ("GATE 4", (PROC_DIR / "hydromet_monthly.csv").exists()),
        ("GATE 5", list((ROOT / "outputs" / "tables").glob("T06_*.csv")) != []),
        ("GATE 6", not verify_handoff(ROOT / "handoff_writer")),
    ]
    for name, ok in checks:
        print(f"  {'✅' if ok else '❌'} {name}")

    ok, msg = check_gate2_approval()
    print(f"\n  Phê duyệt GATE 2: {'✅' if ok else '❌'} {msg}")


def _has_nan(path):
    try:
        import pandas as pd
        df = pd.read_csv(path, usecols=["rainfall_mm"])
        return bool(df["rainfall_mm"].isna().any())
    except Exception:
        return True


def main():
    parser = argparse.ArgumentParser(
        description="Chạy toàn bộ quy trình phân tích khí tượng thủy văn Sông Ba Hạ"
    )
    parser.add_argument(
        "--gate", type=int, default=1,
        help="Chạy từ GATE N trở đi (mặc định: 1)"
    )
    parser.add_argument(
        "--status", action="store_true",
        help="Chỉ in trạng thái các GATE rồi thoát"
    )
    args = parser.parse_args()

    if args.status:
        print_status()
        return 0

    print("=" * 60)
    print("  QUY TRÌNH PHÂN TÍCH KHÍ TƯỢNG THỦY VĂN SÔNG BA HẠ")
    print("  Đặc tả V1.0 + Phụ lục V1.1")
    print("=" * 60)

    # GATE 2 là điều kiện tiên quyết cho mọi bước dùng polygon
    if args.gate >= 3:
        ok, msg = check_gate2_approval()
        if not ok:
            print("\n❌ DỪNG: chưa có phê duyệt GATE 2.")
            print(f"  {msg}")
            return 1
        print(f"\n✅ Phê duyệt GATE 2: {msg}")

    errors = []
    for step in PIPELINE:
        if step["gate"] < args.gate:
            print(f"\n⏭️  Bỏ qua: {step['desc']}")
            continue

        if step["gate"] >= 3:
            approved, approval_msg = check_gate2_approval()
            if not approved:
                errors.append("GATE 2 approval required")
                print("DUNG truoc GATE 3: " + approval_msg)
                break
        # Generate the two reviewed inflow scenarios immediately before the writer handoff.
        if step["gate"] == 6:
            sens_code = run_script("10_suspect_sensitivity.py", "QA — hai kịch bản SUSPECT")
            if sens_code != 0:
                errors.append("10_suspect_sensitivity.py")
                break
        code = run_script(step["script"], step["desc"])
        if code != 0:
            errors.append(step["script"])
            print(f"\n❌ {step['script']} thất bại (exit code {code})")
            print("  → Dừng pipeline: các GATE sau phụ thuộc trực tiếp.")
            break
        else:
            print(f"\n✅ {step['desc']} — hoàn thành")

    # Sau GATE 2 phải xác nhận phê duyệt trước khi sang GATE 3
    if not errors and args.gate <= 3:
        ok, msg = check_gate2_approval()
        if not ok:
            print("\n❌ DỪNG sau GATE 2: chưa có phê duyệt của người giám sát.")
            print(f"  {msg}")
            errors.append("GATE 2 — chưa được phê duyệt")

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

    print("  ✅ Toàn bộ pipeline hoàn thành thành công!")
    print("\n  GATE 6 — Bàn giao hoàn tất:")
    print("  1. handoff_writer/figures/ — hình F01–F10")
    print("  2. handoff_writer/tables/  — bảng T01–T07")
    print("  3. handoff_writer/selected_data/ — dữ liệu chính")
    print("  4. handoff_writer/*.md — tài liệu cho người viết báo cáo")
    return 0


if __name__ == "__main__":
    sys.exit(main())
