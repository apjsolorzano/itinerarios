#!/usr/bin/env python3
"""Renderiza recortes de capas OCG para localizar elementos del cambio REV-02."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pymupdf


ROOT = Path("/Users/felix/Desktop/AI/personal/output/pdf/plano_california_revision_sin_escalera")
OUT = Path(__file__).resolve().parent / "layers"
OUT.mkdir(parents=True, exist_ok=True)


for folder in ("nivel_1", "nivel_2"):
    model = json.loads((ROOT / folder / "model.json").read_text(encoding="utf-8"))
    source = (ROOT / folder / model["source"]["pdf_path"]).resolve()
    for layer in model["source_layers"]:
        xref = layer.get("ocg_xref")
        if not xref:
            continue
        document = pymupdf.open(source)
        document.set_layer(-1, basestate="OFF", on=[xref])
        with tempfile.NamedTemporaryFile(suffix=".pdf") as temporary:
            document.save(temporary.name)
            document.close()
            isolated = pymupdf.open(temporary.name)
            page = isolated[model["source"]["page_index"]]
            clip = pymupdf.Rect(200, 140, 600, 680)
            pixmap = page.get_pixmap(matrix=pymupdf.Matrix(3, 3), clip=clip, alpha=False)
            safe_name = "".join(character if character.isalnum() else "_" for character in layer["name"])
            pixmap.save(OUT / f"{folder}-{xref}-{safe_name}.png")
            isolated.close()
