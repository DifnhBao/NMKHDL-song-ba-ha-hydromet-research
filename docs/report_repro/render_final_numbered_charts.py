"""Render report-only plots without in-image titles.

Word supplies "Hình N." captions, so the image itself must not repeat the title.
Panel labels such as "(a) Phân bố toàn giai đoạn" are kept.
"""
from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
import importlib.util

from matplotlib.axes import Axes
from matplotlib.figure import Figure


ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).with_name("final_numbered_charts")
OUT.mkdir(exist_ok=True)

FIGURE_TITLE_PREFIXES = ("Hình ", "F0", "F1")


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.FIG_DIR = OUT
    return module


@contextmanager
def drop_figure_titles():
    original_set_title = Axes.set_title
    original_suptitle = Figure.suptitle

    def set_title(self, label, *args, **kwargs):
        if isinstance(label, str) and label.startswith(FIGURE_TITLE_PREFIXES):
            return None
        return original_set_title(self, label, *args, **kwargs)

    def suptitle(self, t, *args, **kwargs):
        return None

    Axes.set_title = set_title
    Figure.suptitle = suptitle
    try:
        yield
    finally:
        Axes.set_title = original_set_title
        Figure.suptitle = original_suptitle


SNAPSHOT = Path(__file__).with_name("engine")
eda = load_module("eda_report_figures", SNAPSHOT / "06_exploratory_analysis.py")
runoff = load_module("runoff_report_figures", SNAPSHOT / "07_rainfall_runoff_analysis.py")

with drop_figure_titles():
    daily, monthly, hydro_qa, _ = eda.load_data()
    eda.create_F02(monthly)
    eda.create_F03(monthly)
    eda.create_F04(daily, hydro_qa)
    eda.create_F05(monthly)
    eda.create_F06(daily, hydro_qa)
    eda.create_F10(daily, hydro_qa)

    rain_monthly = runoff.load_monthly()
    valid = runoff.filter_valid_months(rain_monthly)
    suspect_months = runoff.load_suspect_months()
    correlations = runoff.compute_all_correlations(valid, rain_monthly, suspect_months)
    runoff.create_F07(valid)
    runoff.create_F08(valid, correlations)

for path in sorted(OUT.glob("*.png")):
    print(path.name, path.stat().st_size)
