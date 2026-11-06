"""Embed the report figure renders into BAO_CAO.docx, keyed by figure caption.

The existing drawing is kept (same width); only the image bytes and the height
are updated so the picture is not stretched.
"""
from __future__ import annotations

import os
from pathlib import Path
from zipfile import ZipFile

from docx import Document
from docx.oxml.ns import qn
from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "docs" / "BAO_CAO.docx"
HERE = Path(__file__).resolve().parent
CHARTS = HERE / "final_numbered_charts"

SOURCES = {
    1: HERE / "F01_basin_map_report.png",
    3: CHARTS / "F02_rainfall_monthly.png",
    4: CHARTS / "F03_temperature_monthly.png",
    5: CHARTS / "F04_inflow_daily_hydrograph.png",
    6: CHARTS / "F05_inflow_monthly.png",
    7: CHARTS / "F06_upstream_level.png",
    8: CHARTS / "F07_rainfall_inflow_comparison.png",
    9: CHARTS / "F08_scatter_rainfall_inflow.png",
    10: HERE / "H10_same_rain_pairs.png",
    12: CHARTS / "F10_inflow_distribution.png",
}

document = Document(REPORT)
replacement: dict[str, bytes] = {}

for number, source in SOURCES.items():
    captions = [p for p in document.paragraphs
                if p.style.name == "Caption" and p.text.startswith(f"Hình {number}. ")]
    if len(captions) != 1:
        raise ValueError((number, len(captions)))
    caption = captions[0]
    picture = caption._p.getprevious()
    while picture is not None and picture.tag != qn("w:p"):
        picture = picture.getprevious()
    blips = list(picture.iter(qn("a:blip")))
    if len(blips) != 1:
        raise ValueError((number, "expected exactly one image before the caption"))

    rid = blips[0].get(qn("r:embed"))
    part = document.part.related_parts[rid]
    media_name = str(part.partname).lstrip("/")

    with Image.open(source) as image:
        aspect = image.height / image.width
    for extent in picture.iter(qn("wp:extent")):
        width = int(extent.get("cx"))
        extent.set("cy", str(round(width * aspect)))
    for extent in picture.iter(qn("a:ext")):
        width = int(extent.get("cx"))
        extent.set("cy", str(round(width * aspect)))

    replacement[media_name] = source.read_bytes()
    print(f"Hình {number}: {media_name} <- {source.name}")

document.save(REPORT)

tmp = REPORT.with_suffix(".figtmp.docx")
with ZipFile(REPORT, "r") as original, ZipFile(tmp, "w") as updated:
    for item in original.infolist():
        updated.writestr(item, replacement.get(item.filename, original.read(item.filename)))
os.replace(tmp, REPORT)
print("Replaced", len(replacement), "embedded images")
