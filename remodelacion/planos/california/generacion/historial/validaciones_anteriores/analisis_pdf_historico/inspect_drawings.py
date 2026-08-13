#!/usr/bin/env python3
"""Lista geometría OCG que intersecta el área de la escalera y pasillo."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pymupdf


ROOT = Path("/Users/felix/Desktop/AI/personal/output/pdf/plano_california_revision_sin_escalera")
TARGET = pymupdf.Rect(180, 260, 570, 680)


for folder, xrefs in {
    "nivel_1": [75],
    "acabados_nivel_1": [110],
    "electrico_nivel_1": [307],
}.items():
    model = json.loads((ROOT / folder / "model.json").read_text(encoding="utf-8"))
    source = (ROOT / folder / model["source"]["pdf_path"]).resolve()
    print(f"\n{folder}")
    for xref in xrefs:
        document = pymupdf.open(source)
        document.set_layer(-1, basestate="OFF", on=[xref])
        with tempfile.NamedTemporaryFile(suffix=".pdf") as temporary:
            document.save(temporary.name)
            document.close()
            isolated = pymupdf.open(temporary.name)
            drawings = isolated[model["source"]["page_index"]].get_drawings()
            print(f"  xref {xref}: {len(drawings)} drawings")
            for index, drawing in enumerate(drawings):
                rect = drawing["rect"]
                if rect.intersects(TARGET):
                    print(
                        f"    {index:03d} type={drawing.get('type')} "
                        f"rect=({rect.x0:.1f},{rect.y0:.1f},{rect.x1:.1f},{rect.y1:.1f}) "
                        f"items={len(drawing.get('items', []))} "
                        f"width={drawing.get('width')} fill={drawing.get('fill')} color={drawing.get('color')}"
                    )
                    if xref in {75, 110, 307}:
                        print(f"      items={drawing.get('items')}")
            isolated.close()
