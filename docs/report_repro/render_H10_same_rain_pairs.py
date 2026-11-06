"""Render Hình 10 (same-rain, different-flow pairs) without an in-image title."""
from __future__ import annotations

import importlib.util
from pathlib import Path

from matplotlib.figure import Figure


ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUT = HERE / "H10_same_rain_pairs.png"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


extended = load_module("extended_rq3_report", ROOT / "scripts" / "13_extended_rq3_analysis.py")
extended.FIG = OUT

original_suptitle = Figure.suptitle
Figure.suptitle = lambda self, *args, **kwargs: None
try:
    data = extended.load_monthly()
    pairs = extended.build_pairs(data)
    same = pairs[pairs["rain_diff_pct"] <= 10.0].copy()
    extended.make_figure(data, pairs, same)
finally:
    Figure.suptitle = original_suptitle

print(OUT, OUT.stat().st_size)
