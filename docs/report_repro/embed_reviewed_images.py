"""Embed Hình 2 and Hình 11 renders without changing Word's layout XML."""
from pathlib import Path
from zipfile import ZipFile
import os

from docx import Document
from docx.oxml.ns import qn


ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "docs/BAO_CAO_final.docx"
ASSETS = Path(__file__).resolve().parent
SOURCES = {2: ASSETS / "H02_workflow.png", 11: ASSETS / "H11_suspect_sensitivity.png"}

document = Document(REPORT)
replacement = {}
for number, source in SOURCES.items():
    captions = [i for i, p in enumerate(document.paragraphs)
                if p.style.name == "Caption" and p.text.startswith(f"Hình {number}. ")]
    if len(captions) != 1:
        raise ValueError((number, captions))
    picture = document.paragraphs[captions[0] - 1]
    blips = list(picture._p.iter(qn("a:blip")))
    if len(blips) != 1:
        raise ValueError((number, "expected exactly one image before the caption"))
    rid = blips[0].get(qn("r:embed"))
    media_name = str(document.part.related_parts[rid].partname).lstrip("/")
    replacement[media_name] = source.read_bytes()

tmp = REPORT.with_suffix(".imagetmp.docx")
with ZipFile(REPORT, "r") as original, ZipFile(tmp, "w") as updated:
    for item in original.infolist():
        updated.writestr(item, replacement.get(item.filename, original.read(item.filename)))
os.replace(tmp, REPORT)
print("Replaced", len(replacement), "embedded images")
