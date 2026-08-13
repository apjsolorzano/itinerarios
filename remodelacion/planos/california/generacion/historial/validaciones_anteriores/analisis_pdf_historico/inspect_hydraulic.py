#!/usr/bin/env python3
"""Inspecciona geometría de la hoja hidráulica alrededor de la escalera."""

from __future__ import annotations

import json
from pathlib import Path

import pymupdf


ROOT = Path("/Users/felix/Desktop/AI/personal/output/pdf/plano_california_revision_sin_escalera")
model = json.loads((ROOT / "hidraulico_nivel_1/model.json").read_text(encoding="utf-8"))
source = (ROOT / "hidraulico_nivel_1" / model["source"]["pdf_path"]).resolve()
page = pymupdf.open(source)[model["source"]["page_index"]]
regions = [
    pymupdf.Rect(250, 278, 515, 332),
    pymupdf.Rect(395, 318, 497, 407),
    pymupdf.Rect(498, 420, 516, 630),
]

for index, drawing in enumerate(page.get_drawings()):
    rect = drawing["rect"]
    if not any(rect.intersects(region) for region in regions):
        continue
    if rect.width > 300 or rect.height > 350:
        continue
    print(
        f"{index:04d} type={drawing.get('type')} "
        f"rect=({rect.x0:.1f},{rect.y0:.1f},{rect.x1:.1f},{rect.y1:.1f}) "
        f"items={len(drawing.get('items', []))} width={drawing.get('width')} "
        f"fill={drawing.get('fill')} color={drawing.get('color')} dashes={drawing.get('dashes')}"
    )

print("\nBLACK SQUARES")
for index, drawing in enumerate(page.get_drawings()):
    rect = drawing["rect"]
    if not (150 <= rect.x0 <= 600 and 250 <= rect.y0 <= 680):
        continue
    if rect.width > 15 or rect.height > 15:
        continue
    fill = drawing.get("fill")
    if fill and max(fill) < 0.05:
        print(index, tuple(round(value, 1) for value in (rect.x0, rect.y0, rect.x1, rect.y1)))
