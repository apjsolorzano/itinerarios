#!/usr/bin/env python3
"""Regenera una hoja desde un SVG maestro y operaciones JSON, sin abrir PDFs."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
from pathlib import Path


GRAPHIC_TAGS = "g|path|rect|line|polyline|polygon|circle|ellipse|text|use"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def resolve(path_value: str, base: Path) -> Path:
    path = Path(path_value)
    return path if path.is_absolute() else (base / path).resolve()


def svg_inner_markup(svg_text: str) -> str:
    start = svg_text.find(">")
    end = svg_text.rfind("</svg>")
    if start < 0 or end < 0:
        raise ValueError("El recurso indicado no contiene un SVG válido")
    return svg_text[start + 1 : end]


def append_before_closing_svg(svg_text: str, fragments: list[str]) -> str:
    if not fragments:
        return svg_text
    closing = svg_text.rfind("</svg>")
    if closing < 0:
        raise ValueError("El SVG maestro no contiene una etiqueta de cierre")
    return svg_text[:closing] + "\n" + "\n".join(fragments) + "\n" + svg_text[closing:]


def inject_attributes(svg_text: str, ids: list[str], attributes: dict[str, object]) -> str:
    for svg_id in ids:
        id_pattern = re.escape(svg_id)
        element_pattern = re.compile(
            rf'<(?P<tag>{GRAPHIC_TAGS})\b(?P<attrs>[^>]*\bid="{id_pattern}"[^>]*)(?P<slash>/?)>'
        )

        def update(match: re.Match[str]) -> str:
            attrs = match.group("attrs")
            for name, raw_value in attributes.items():
                value = html.escape(str(raw_value), quote=True)
                attribute_pattern = re.compile(rf'\s+{re.escape(name)}="[^"]*"')
                if attribute_pattern.search(attrs):
                    attrs = attribute_pattern.sub(f' {name}="{value}"', attrs)
                else:
                    attrs += f' {name}="{value}"'
            return f'<{match.group("tag")}{attrs}{match.group("slash")}>'

        svg_text, count = element_pattern.subn(update, svg_text, count=1)
        if count == 0:
            raise ValueError(f"No existe el elemento SVG con id {svg_id!r}")
    return svg_text


def operation_fragment(operation: dict, model_dir: Path) -> str:
    operation_id = html.escape(operation.get("id", "svg-edit"), quote=True)
    operation_type = operation["type"]
    common = f'id="{operation_id}" data-plan-operation="{operation_type}"'
    if operation_type == "whiteout":
        fill = html.escape(operation.get("fill", "#ffffff"), quote=True)
        if "rect_pt" in operation:
            x, y, width, height = operation["rect_pt"]
            geometry = f'<rect x="{x}" y="{y}" width="{width}" height="{height}" fill="{fill}" stroke="none"/>'
        else:
            points = " ".join(f"{x},{y}" for x, y in operation["polygon_pt"])
            geometry = f'<polygon points="{points}" fill="{fill}" stroke="none"/>'
        return f"<g {common}>{geometry}</g>"
    if operation_type == "draw_path":
        return (
            f'<path {common} d="{html.escape(operation["d"], quote=True)}" '
            f'fill="{html.escape(operation.get("fill", "none"), quote=True)}" '
            f'stroke="{html.escape(operation.get("stroke", "#263238"), quote=True)}" '
            f'stroke-width="{operation.get("stroke_width_pt", 0.75)}" '
            f'stroke-linecap="{operation.get("stroke_linecap", "square")}" '
            f'stroke-linejoin="{operation.get("stroke_linejoin", "miter")}"/>'
        )
    if operation_type == "draw_rect":
        x, y, width, height = operation["rect_pt"]
        return (
            f'<rect {common} x="{x}" y="{y}" width="{width}" height="{height}" '
            f'fill="{html.escape(operation.get("fill", "none"), quote=True)}" '
            f'stroke="{html.escape(operation.get("stroke", "#263238"), quote=True)}" '
            f'stroke-width="{operation.get("stroke_width_pt", 0.75)}"/>'
        )
    if operation_type == "draw_line":
        return (
            f'<line {common} x1="{operation["x1"]}" y1="{operation["y1"]}" '
            f'x2="{operation["x2"]}" y2="{operation["y2"]}" '
            f'stroke="{html.escape(operation.get("stroke", "#263238"), quote=True)}" '
            f'stroke-width="{operation.get("stroke_width_pt", 0.75)}"/>'
        )
    if operation_type == "draw_polyline":
        points = " ".join(f"{x},{y}" for x, y in operation["points_pt"])
        return (
            f'<polyline {common} points="{points}" '
            f'fill="{html.escape(operation.get("fill", "none"), quote=True)}" '
            f'stroke="{html.escape(operation.get("stroke", "#263238"), quote=True)}" '
            f'stroke-width="{operation.get("stroke_width_pt", 0.75)}"/>'
        )
    if operation_type == "append_svg":
        overlay_path = resolve(operation["path"], model_dir)
        overlay = svg_inner_markup(overlay_path.read_text(encoding="utf-8"))
        return f"<g {common}>{overlay}</g>"
    raise ValueError(f"Operación gráfica no soportada: {operation_type}")


def apply_operations(svg_text: str, model: dict, model_dir: Path) -> str:
    fragments: list[str] = []
    for operation in model.get("operations", []):
        if operation.get("visible", True) is False:
            continue
        operation_type = operation["type"]
        if operation_type == "hide_ids":
            svg_text = inject_attributes(svg_text, operation["ids"], {"display": "none"})
        elif operation_type == "set_attributes":
            svg_text = inject_attributes(svg_text, operation["ids"], operation["attributes"])
        elif operation_type == "replace_color":
            source = re.escape(operation["source_color"])
            target = operation["target_color"]
            svg_text = re.sub(
                rf'(?P<attribute>stroke|fill)="{source}"',
                lambda match: f'{match.group("attribute")}="{target}"',
                svg_text,
                flags=re.IGNORECASE,
            )
        else:
            fragments.append(operation_fragment(operation, model_dir))
    return append_before_closing_svg(svg_text, fragments)


def render(model_path: Path, output_override: str | None = None) -> Path:
    model_path = model_path.resolve()
    model_dir = model_path.parent
    model = json.loads(model_path.read_text(encoding="utf-8"))
    if model.get("format") != "plan-editor/svg-v1":
        raise ValueError("El modelo no usa el formato plan-editor/svg-v1")
    source = model["source"]
    if source.get("kind") != "svg" or source.get("reference_policy") != "svg_only":
        raise ValueError("El modelo no está configurado para referencia exclusiva SVG")
    master_path = resolve(source["master_svg_path"], model_dir)
    expected_hash = source["master_svg_sha256"]
    actual_hash = sha256(master_path)
    if actual_hash != expected_hash:
        raise ValueError(
            f"El SVG maestro cambió: se esperaba {expected_hash} y se obtuvo {actual_hash}"
        )
    output_path = resolve(output_override or model["output"]["svg_path"], model_dir)
    if output_path == master_path:
        raise ValueError("La salida no puede sobrescribir el SVG maestro")
    result = apply_operations(master_path.read_text(encoding="utf-8"), model, model_dir)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(result, encoding="utf-8")
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model", type=Path)
    parser.add_argument("--output", help="Ruta alternativa de salida SVG")
    arguments = parser.parse_args()
    output = render(arguments.model, arguments.output)
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
