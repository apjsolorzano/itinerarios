#!/usr/bin/env python3
"""Construye el PDF consolidado y la vista resumen de la edición limpia."""

from __future__ import annotations

import json
from pathlib import Path

import pymupdf
from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parent


def build_pdf(project: dict) -> Path:
    output = pymupdf.open()
    for sheet in project["sheets"]:
        model_path = ROOT / sheet["model"]
        model = json.loads(model_path.read_text(encoding="utf-8"))
        svg_path = model_path.parent / model["output"]["svg_path"]
        svg_document = pymupdf.open("svg", svg_path.read_bytes())
        page_pdf = pymupdf.open("pdf", svg_document.convert_to_pdf())
        output.insert_pdf(page_pdf)
        page_pdf.close()
        svg_document.close()
    output_path = ROOT / "california_planos_revision_sin_escalera.pdf"
    output.save(output_path, garbage=4, deflate=True)
    output.close()
    return output_path


def build_contact_sheet(project: dict) -> Path:
    columns = 3
    thumb_width = 612
    thumb_height = 396
    header_height = 34
    gutter = 18
    rows = (len(project["sheets"]) + columns - 1) // columns
    canvas = Image.new(
        "RGB",
        (
            columns * thumb_width + (columns + 1) * gutter,
            rows * (thumb_height + header_height) + (rows + 1) * gutter,
        ),
        "white",
    )
    draw = ImageDraw.Draw(canvas)
    for index, sheet in enumerate(project["sheets"]):
        model_path = ROOT / sheet["model"]
        model = json.loads(model_path.read_text(encoding="utf-8"))
        preview_path = model_path.parent / model["output"]["preview_png_path"]
        preview = Image.open(preview_path).convert("RGB")
        preview.thumbnail((thumb_width, thumb_height))
        column = index % columns
        row = index // columns
        x = gutter + column * (thumb_width + gutter)
        y = gutter + row * (thumb_height + header_height + gutter)
        draw.text((x, y + 8), f"{index + 1}. {sheet['title']}", fill="black")
        image_x = x + (thumb_width - preview.width) // 2
        image_y = y + header_height + (thumb_height - preview.height) // 2
        canvas.paste(preview, (image_x, image_y))
    output_path = ROOT / "california_resumen_revision_9_hojas.png"
    canvas.save(output_path)
    return output_path


def main() -> None:
    project = json.loads((ROOT / "california_project.json").read_text(encoding="utf-8"))
    print(build_pdf(project))
    print(build_contact_sheet(project))


if __name__ == "__main__":
    main()
