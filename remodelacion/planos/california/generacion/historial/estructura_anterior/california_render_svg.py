#!/usr/bin/env python3
"""Regenera una hoja SVG desde el PDF fuente y un manifiesto plan-editor/v1."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path


def load_runtime():
    try:
        import pymupdf
        from PIL import Image, ImageChops, ImageStat
    except ImportError as exc:
        raise SystemExit(
            "Faltan dependencias. Ejecute: python -m pip install -r california_requirements.txt"
        ) from exc
    return pymupdf, Image, ImageChops, ImageStat


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_path(value: str, base: Path) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else (base / path).resolve()


def svg_inner_markup(svg_text: str) -> str:
    start = svg_text.find(">")
    end = svg_text.rfind("</svg>")
    if start < 0 or end < 0:
        raise ValueError("El archivo de superposición no contiene un SVG válido")
    return svg_text[start + 1 : end]


GRAPHIC_ELEMENT_PATTERN = re.compile(
    r"<(?P<tag>path|line|polyline|polygon|circle|ellipse|rect)\b(?P<attrs>[^>]*?)(?P<slash>/?)>"
)


def prefix_svg_ids(svg_text: str, prefix: str) -> str:
    """Evita colisiones entre identificadores de la base y las capas recuperadas."""
    safe_prefix = re.sub(r"[^A-Za-z0-9_-]+", "-", prefix).strip("-") or "operation"
    identifiers = set(re.findall(r'\bid="([^"]+)"', svg_text))
    for identifier in sorted(identifiers, key=len, reverse=True):
        replacement = f"{safe_prefix}-{identifier}"
        svg_text = svg_text.replace(f'id="{identifier}"', f'id="{replacement}"')
        svg_text = svg_text.replace(f"#{identifier}", f"#{replacement}")
    return svg_text


def extract_layer_svg(
    pymupdf,
    source_pdf: Path,
    page_index: int,
    visible_xrefs: list[int],
    text_as_path: bool,
    regions: list[list[float]] | None = None,
    exclude_regions: list[list[float]] | None = None,
    canvas: dict | None = None,
) -> str:
    """Extrae una página con una selección OCG concreta, sin alterar el PDF fuente."""
    document = pymupdf.open(source_pdf)
    temporary_pdf: Path | None = None
    configured_document = None
    clipped_document = None
    try:
        if visible_xrefs:
            document.set_layer(-1, basestate="OFF", on=visible_xrefs)
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as handle:
            temporary_pdf = Path(handle.name)
        document.save(temporary_pdf)
        document.close()
        configured_document = pymupdf.open(temporary_pdf)
        configured_page = configured_document[page_index]
        if exclude_regions:
            if canvas is None:
                raise ValueError("Una extracción con exclusiones requiere el tamaño de la hoja")
            regions = complement_rectangles(
                float(canvas["width_pt"]),
                float(canvas["height_pt"]),
                exclude_regions,
            )
        if regions:
            clipped_document = pymupdf.open()
            clipped_page = clipped_document.new_page(
                width=configured_page.rect.width,
                height=configured_page.rect.height,
            )
            for x, y, width, height in regions:
                rectangle = pymupdf.Rect(
                    float(x),
                    float(y),
                    float(x) + float(width),
                    float(y) + float(height),
                )
                if rectangle.is_empty:
                    continue
                clipped_page.show_pdf_page(
                    rectangle,
                    configured_document,
                    page_index,
                    clip=rectangle,
                    keep_proportion=False,
                    overlay=True,
                )
            configured_page = clipped_page
        return configured_page.get_svg_image(
            text_as_path=1 if text_as_path else 0
        )
    finally:
        if not document.is_closed:
            document.close()
        if configured_document is not None and not configured_document.is_closed:
            configured_document.close()
        if clipped_document is not None and not clipped_document.is_closed:
            clipped_document.close()
        if temporary_pdf is not None and temporary_pdf.exists():
            temporary_pdf.unlink()


def extract_layer_drawings(
    pymupdf,
    source_pdf: Path,
    page_index: int,
    visible_xrefs: list[int],
) -> list[dict]:
    document = pymupdf.open(source_pdf)
    temporary_pdf: Path | None = None
    configured_document = None
    try:
        document.set_layer(-1, basestate="OFF", on=visible_xrefs)
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as handle:
            temporary_pdf = Path(handle.name)
        document.save(temporary_pdf)
        document.close()
        configured_document = pymupdf.open(temporary_pdf)
        return configured_document[page_index].get_drawings()
    finally:
        if not document.is_closed:
            document.close()
        if configured_document is not None and not configured_document.is_closed:
            configured_document.close()
        if temporary_pdf is not None and temporary_pdf.exists():
            temporary_pdf.unlink()


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def visible_svg_graphics(svg_text: str) -> list[ET.Element]:
    root = ET.fromstring(svg_text)
    output: list[ET.Element] = []
    graphic_tags = {"path", "line", "polyline", "polygon", "circle", "ellipse", "rect"}

    def walk(element: ET.Element, inside_defs: bool = False) -> None:
        name = local_name(element.tag)
        next_inside_defs = inside_defs or name in {"defs", "clipPath", "mask"}
        if name in graphic_tags and not next_inside_defs:
            output.append(element)
        for child in element:
            walk(child, next_inside_defs)

    walk(root)
    return output


def rect_intersects_regions(rect, regions: list[list[float]]) -> bool:
    for x, y, width, height in regions:
        if (
            rect.x0 < float(x) + float(width)
            and rect.x1 > float(x)
            and rect.y0 < float(y) + float(height)
            and rect.y1 > float(y)
        ):
            return True
    return False


def selective_layer_fragment(
    svg_text: str,
    drawings: list[dict],
    preserve_regions: list[list[float]],
    target_regions: list[list[float]] | None = None,
    as_eraser: bool = False,
    eraser_stroke_width_source: float = 60.0,
) -> str:
    """Selecciona objetos de una capa según sus límites geométricos."""
    elements = visible_svg_graphics(svg_text)
    expected_count = sum(
        2 if drawing.get("type") in {"fs", "sf"} else 1 for drawing in drawings
    )
    if len(elements) != expected_count:
        raise ValueError(
            "No se pudo correlacionar la geometría de la capa: "
            f"{len(elements)} elementos SVG y {expected_count} elementos esperados."
        )

    selected: list[str] = []
    element_index = 0
    for drawing in drawings:
        count = 2 if drawing.get("type") in {"fs", "sf"} else 1
        drawing_elements = elements[element_index : element_index + count]
        element_index += count
        if target_regions and not rect_intersects_regions(drawing["rect"], target_regions):
            continue
        if rect_intersects_regions(drawing["rect"], preserve_regions):
            continue
        for element in drawing_elements:
            serialized = ET.tostring(element, encoding="unicode")
            serialized = re.sub(r'\s+xmlns:ns\d+="[^"]+"', "", serialized)
            serialized = re.sub(r'(<\/?)ns\d+:', r"\1", serialized)
            selected.append(serialized)
    fragment = "".join(selected)
    return (
        recolor_as_white_eraser(fragment, eraser_stroke_width_source)
        if as_eraser
        else fragment
    )


def clip_definition(
    operation_id: str,
    canvas: dict,
    regions: list[list[float]] | None = None,
    exclude_regions: list[list[float]] | None = None,
) -> tuple[str, str]:
    if not regions and not exclude_regions:
        return "", ""
    # El SVG extraído del PDF suele traer sus propios clipPath. Use un sufijo
    # que no pueda coincidir con los identificadores prefijados del contenido.
    clip_id = f"{operation_id}-edit-region-clip"
    if regions:
        shapes = "".join(
            f'<rect x="{x}" y="{y}" width="{width}" height="{height}"/>'
            for x, y, width, height in regions
        )
    else:
        width = float(canvas["width_pt"])
        height = float(canvas["height_pt"])
        path_parts = [f"M0 0H{width}V{height}H0Z"]
        for x, y, region_width, region_height in exclude_regions or []:
            path_parts.append(
                f"M{x} {y}H{x + region_width}V{y + region_height}H{x}Z"
            )
        shapes = (
            f'<path d="{" ".join(path_parts)}" clip-rule="evenodd" '
            'fill-rule="evenodd"/>'
        )
    definition = f'<defs><clipPath id="{clip_id}">{shapes}</clipPath></defs>'
    return definition, f' clip-path="url(#{clip_id})"'


def complement_rectangles(
    width: float,
    height: float,
    excluded: list[list[float]],
) -> list[list[float]]:
    """Descompone el complemento de rectángulos en bandas sin superposición."""
    clipped: list[tuple[float, float, float, float]] = []
    for x, y, region_width, region_height in excluded:
        left = max(0.0, float(x))
        top = max(0.0, float(y))
        right = min(width, left + float(region_width))
        bottom = min(height, top + float(region_height))
        if right > left and bottom > top:
            clipped.append((left, top, right, bottom))

    y_edges = sorted({0.0, height, *(value for item in clipped for value in (item[1], item[3]))})
    rectangles: list[list[float]] = []
    for top, bottom in zip(y_edges, y_edges[1:]):
        if bottom <= top:
            continue
        intervals = sorted(
            (left, right)
            for left, region_top, right, region_bottom in clipped
            if region_top < bottom and region_bottom > top
        )
        merged: list[tuple[float, float]] = []
        for left, right in intervals:
            if merged and left <= merged[-1][1]:
                merged[-1] = (merged[-1][0], max(merged[-1][1], right))
            else:
                merged.append((left, right))
        cursor = 0.0
        for left, right in merged:
            if left > cursor:
                rectangles.append([cursor, top, left - cursor, bottom - top])
            cursor = max(cursor, right)
        if cursor < width:
            rectangles.append([cursor, top, width - cursor, bottom - top])
    return rectangles


def region_limited_overlay(
    operation_id: str,
    overlay: str,
    canvas: dict,
    regions: list[list[float]] | None,
    excluded: list[list[float]] | None,
) -> str:
    """Recorta con viewports SVG anidados, compatibles con visores PDF y SVG."""
    if excluded:
        regions = complement_rectangles(
            float(canvas["width_pt"]),
            float(canvas["height_pt"]),
            excluded,
        )
    if not regions:
        return overlay

    safe_operation_id = (
        re.sub(r"[^A-Za-z0-9_-]+", "-", operation_id).strip("-")
        or "operation"
    )
    content_id = f"{safe_operation_id}-edit-region-content"
    definition = f'<defs><g id="{content_id}">{overlay}</g></defs>'
    viewports = []
    for x, y, width, height in regions:
        if float(width) <= 0 or float(height) <= 0:
            continue
        viewports.append(
            f'<svg x="{x}" y="{y}" width="{width}" height="{height}" '
            f'viewBox="{x} {y} {width} {height}" preserveAspectRatio="none" '
            f'overflow="hidden"><use xlink:href="#{content_id}"/></svg>'
        )
    return definition + "".join(viewports)


def recolor_as_white_eraser(svg_text: str, stroke_width_source: float = 60.0) -> str:
    """Convierte geometría vectorial de referencia en una máscara blanca de borrado."""
    def recolor(match: re.Match[str]) -> str:
        tag = match.group("tag")
        attributes = match.group("attrs")
        closing_slash = match.group("slash")
        if 'fill="none"' not in attributes and "fill=" in attributes:
            attributes = re.sub(r'fill="[^"]*"', 'fill="#ffffff"', attributes)
        if "stroke=" in attributes and 'stroke="none"' not in attributes:
            attributes = re.sub(r'stroke="[^"]*"', 'stroke="#ffffff"', attributes)
            attributes = re.sub(r'\s+stroke-opacity="[^"]*"', "", attributes)
            if "stroke-width=" in attributes:
                attributes = re.sub(
                    r'stroke-width="[^"]*"',
                    f'stroke-width="{stroke_width_source:g}"',
                    attributes,
                )
            else:
                attributes += f' stroke-width="{stroke_width_source:g}"'
        return f"<{tag}{attributes}{closing_slash}>"

    return GRAPHIC_ELEMENT_PATTERN.sub(recolor, svg_text)


def filter_svg_colors(svg_text: str, colors: set[str]) -> str:
    normalized = {color.lower() for color in colors}

    def keep(match: re.Match[str]) -> str:
        attributes = match.group("attrs").lower()
        element_colors = re.findall(r'(?:stroke|fill)="(#[0-9a-f]{6})"', attributes)
        return match.group(0) if any(color in normalized for color in element_colors) else ""

    return GRAPHIC_ELEMENT_PATTERN.sub(keep, svg_text)


def replace_graphic_colors(svg_text: str, replacements: dict[str, str]) -> str:
    """Sustituye colores exactos en trazos y rellenos sin alterar fondos blancos."""
    normalized = {source.lower(): target for source, target in replacements.items()}
    color_pattern = re.compile(r'(?P<attribute>stroke|fill)="(?P<color>#[0-9a-fA-F]{6})"')

    def replace(match: re.Match[str]) -> str:
        color = match.group("color")
        replacement = normalized.get(color.lower())
        if replacement is None:
            return match.group(0)
        return f'{match.group("attribute")}="{replacement}"'

    return color_pattern.sub(replace, svg_text)


def apply_color_profile(svg_text: str, model: dict) -> str:
    """Aplica la paleta base de una disciplina antes de añadir sus capas de énfasis."""
    profile = model.get("color_profile", {})
    if not profile.get("enabled", False):
        return svg_text
    return replace_graphic_colors(svg_text, profile.get("replacements", {}))


def color_svg_fragment(
    svg_text: str,
    stroke_colors: set[str],
    fill_colors: set[str],
) -> str:
    """Extrae directamente trazos por color, sin conservar grupos transformados ajenos."""
    normalized_strokes = {color.lower() for color in stroke_colors}
    normalized_fills = {color.lower() for color in fill_colors}
    selected: list[str] = []
    for element in visible_svg_graphics(svg_text):
        attributes = {local_name(key): value for key, value in element.attrib.items()}
        stroke = attributes.get("stroke", "").lower()
        fill = attributes.get("fill", "").lower()
        if stroke not in normalized_strokes and fill not in normalized_fills:
            continue
        serialized = ET.tostring(element, encoding="unicode")
        serialized = re.sub(r'\s+xmlns:ns\d+="[^"]+"', "", serialized)
        serialized = re.sub(r'(<\/?)ns\d+:', r"\1", serialized)
        selected.append(serialized)
    return "".join(selected)


def whiteout_fragment(operation: dict) -> str:
    fill = operation.get("fill", "#ffffff")
    if "rect_pt" in operation:
        x, y, width, height = operation["rect_pt"]
        return (
            f'<rect x="{x}" y="{y}" width="{width}" height="{height}" '
            f'fill="{fill}" stroke="none"/>'
        )
    points = operation["polygon_pt"]
    point_text = " ".join(f"{x},{y}" for x, y in points)
    return f'<polygon points="{point_text}" fill="{fill}" stroke="none"/>'


def apply_operations(
    svg_text: str,
    model: dict,
    model_dir: Path,
    pymupdf,
    source_pdf: Path,
    page_index: int,
) -> str:
    operations = model.get("operations", [])
    if not operations:
        return svg_text

    fragments: list[str] = []
    for index, operation in enumerate(operations, start=1):
        if operation.get("visible", True) is False:
            continue
        operation_id = operation.get("id", f"operation-{index}")
        operation_type = operation.get("type")

        if operation_type == "append_svg":
            overlay_path = resolve_path(operation["path"], model_dir)
            overlay = svg_inner_markup(overlay_path.read_text(encoding="utf-8"))
            fragments.append(
                f'<g id="{operation_id}" data-plan-operation="append_svg">{overlay}</g>'
            )
            continue

        if operation_type in {
            "append_source_layers_clipped",
            "append_source_layers_recolored",
            "append_source_layer_elements",
            "erase_source_layers",
            "erase_source_layer_elements",
        }:
            operation_page_index = int(operation.get("source_page_index", page_index))
            use_physical_regions = operation_type not in {
                "erase_source_layer_elements",
                "append_source_layer_elements",
            }
            physical_regions = operation.get("regions_pt") if use_physical_regions else None
            if use_physical_regions and operation.get("exclude_regions_pt"):
                physical_regions = complement_rectangles(
                    float(model["canvas"]["width_pt"]),
                    float(model["canvas"]["height_pt"]),
                    operation["exclude_regions_pt"],
                )
            layer_svg = extract_layer_svg(
                pymupdf,
                source_pdf,
                operation_page_index,
                [int(xref) for xref in operation["ocg_xrefs"]],
                bool(model["output"].get("text_as_path", True)),
                operation.get("regions_pt") if use_physical_regions else None,
                operation.get("exclude_regions_pt") if use_physical_regions else None,
                model["canvas"],
            )
            if operation_type in {
                "erase_source_layer_elements",
                "append_source_layer_elements",
            }:
                drawings = extract_layer_drawings(
                    pymupdf,
                    source_pdf,
                    operation_page_index,
                    [int(xref) for xref in operation["ocg_xrefs"]],
                )
                layer_svg = selective_layer_fragment(
                    layer_svg,
                    drawings,
                    operation.get("preserve_regions_pt", []),
                    operation.get("target_regions_pt"),
                    as_eraser=operation_type == "erase_source_layer_elements",
                    eraser_stroke_width_source=float(
                        operation.get("eraser_stroke_width_source", 60.0)
                    ),
                )
            elif operation_type == "erase_source_layers":
                layer_svg = recolor_as_white_eraser(layer_svg)
            if operation_type in {
                "append_source_layers_clipped",
                "append_source_layers_recolored",
                "append_source_layer_elements",
            }:
                layer_svg, _ = apply_visual_profile(layer_svg, model)
            if operation_type == "append_source_layers_recolored":
                source_colors = operation.get("source_colors", ["#000000"])
                target_color = operation["color"]
                layer_svg = replace_graphic_colors(
                    layer_svg,
                    {source_color: target_color for source_color in source_colors},
                )
            layer_svg = prefix_svg_ids(layer_svg, operation_id)
            layer_markup = (
                layer_svg
                if operation_type in {
                    "erase_source_layer_elements",
                    "append_source_layer_elements",
                }
                else svg_inner_markup(layer_svg)
            )
            # PyMuPDF conserva recursos de página completos en algunas extracciones
            # recortadas. Los viewports anidados aseguran que la recuperación se
            # limite físicamente a la zona indicada en todos los visores SVG.
            if physical_regions:
                layer_markup = region_limited_overlay(
                    operation_id,
                    layer_markup,
                    model["canvas"],
                    physical_regions,
                    None,
                )
            fragments.append(
                f'<g id="{operation_id}" data-plan-operation="{operation_type}">'
                f"{layer_markup}</g>"
            )
            continue

        if operation_type == "append_source_colors":
            legacy_colors = set(operation.get("colors", []))
            filtered = color_svg_fragment(
                svg_text,
                set(operation.get("stroke_colors", legacy_colors)),
                set(operation.get("fill_colors", legacy_colors)),
            )
            filtered = prefix_svg_ids(filtered, operation_id)
            fragments.append(
                f'<g id="{operation_id}" data-plan-operation="append_source_colors">'
                f"{filtered}</g>"
            )
            continue

        if operation_type == "whiteout":
            fragments.append(
                f'<g id="{operation_id}" data-plan-operation="whiteout">'
                f"{whiteout_fragment(operation)}</g>"
            )
            continue

        if operation_type == "draw_path":
            fragments.append(
                f'<path id="{operation_id}" data-plan-operation="draw_path" '
                f'd="{operation["d"]}" fill="{operation.get("fill", "none")}" '
                f'stroke="{operation.get("stroke", "#000000")}" '
                f'stroke-width="{operation.get("stroke_width_pt", 0.75)}" '
                f'stroke-linecap="{operation.get("stroke_linecap", "square")}" '
                f'stroke-linejoin="{operation.get("stroke_linejoin", "miter")}"/>'
            )
            continue

        raise ValueError(f"Operación no soportada: {operation_type}")

    if not fragments:
        return svg_text
    closing = svg_text.rfind("</svg>")
    return svg_text[:closing] + "\n" + "\n".join(fragments) + "\n" + svg_text[closing:]


def apply_visual_profile(svg_text: str, model: dict) -> tuple[str, int]:
    """Aplica un grosor mínimo visible a trazos PDF de tipo hairline.

    AutoCAD exporta muchas líneas sin ancho explícito. El PDF las muestra como
    un píxel de dispositivo, pero un visor SVG puede rasterizarlas a una
    fracción casi invisible. El ancho se compensa contra la matriz de cada
    elemento para obtener un mínimo estable en puntos de la hoja.
    """
    profile = model.get("visual_profile", {})
    if not profile.get("enabled", False):
        return svg_text, 0

    minimum = float(profile.get("minimum_hairline_width_pt", 0.65))
    force_opacity = bool(profile.get("force_full_stroke_opacity", True))
    element_pattern = re.compile(
        r"<(?P<tag>path|line|polyline|polygon|circle|ellipse|rect)\b(?P<attrs>[^>]*?)(?P<slash>/?)>"
    )
    changed = 0

    def enhance(match: re.Match[str]) -> str:
        nonlocal changed
        tag = match.group("tag")
        attributes = match.group("attrs")
        closing_slash = match.group("slash")
        if "stroke=" not in attributes or 'stroke="none"' in attributes:
            return match.group(0)
        if "stroke-width=" in attributes:
            return match.group(0)

        scale = 1.0
        transform_match = re.search(r'transform="matrix\(([^)]*)\)"', attributes)
        if transform_match:
            matrix_values = [
                float(value)
                for value in re.split(r"[ ,]+", transform_match.group(1).strip())
                if value
            ]
            if len(matrix_values) >= 4:
                a, b, c, d = matrix_values[:4]
                determinant = abs(a * d - b * c)
                if determinant > 0:
                    scale = math.sqrt(determinant)
        source_width = minimum / scale

        if force_opacity:
            attributes = re.sub(r'\s+stroke-opacity="[^"]*"', "", attributes)
            opacity = ' stroke-opacity="1"'
        else:
            opacity = ""
        changed += 1
        return (
            f"<{tag}{attributes} stroke-width=\"{source_width:.6g}\""
            f"{opacity}{closing_slash}>"
        )

    return element_pattern.sub(enhance, svg_text), changed


def image_metrics(reference, candidate, ImageChops, ImageStat) -> tuple[dict, object]:
    if reference.size != candidate.size:
        raise ValueError(f"Tamaños distintos: {reference.size} y {candidate.size}")
    diff = ImageChops.difference(reference.convert("RGB"), candidate.convert("RGB"))
    stat = ImageStat.Stat(diff)
    channels = diff.tobytes()
    changed = sum(
        1
        for offset in range(0, len(channels), 3)
        if channels[offset] or channels[offset + 1] or channels[offset + 2]
    )
    total = reference.width * reference.height
    metrics = {
        "width_px": reference.width,
        "height_px": reference.height,
        "changed_pixels": changed,
        "changed_pixel_ratio": changed / total,
        "mean_absolute_channel_difference": stat.mean,
        "rms_channel_difference": stat.rms,
        "max_channel_difference": [maximum for _, maximum in diff.getextrema()],
    }
    return metrics, diff


def ink_metrics(reference, candidate) -> dict:
    reference_gray = reference.convert("L")
    candidate_gray = candidate.convert("L")
    if reference_gray.size != candidate_gray.size:
        raise ValueError(f"Tamaños distintos: {reference_gray.size} y {candidate_gray.size}")
    reference_bytes = reference_gray.tobytes()
    candidate_bytes = candidate_gray.tobytes()
    mask = [
        index
        for index, (reference_value, candidate_value) in enumerate(
            zip(reference_bytes, candidate_bytes)
        )
        if reference_value < 250 or candidate_value < 250
    ]
    reference_ink = sum(255 - reference_bytes[index] for index in mask)
    candidate_ink = sum(255 - candidate_bytes[index] for index in mask)
    return {
        "masked_pixel_count": len(mask),
        "masked_mean_absolute_difference": (
            sum(
                abs(reference_bytes[index] - candidate_bytes[index])
                for index in mask
            )
            / len(mask)
            if mask
            else 0
        ),
        "candidate_to_reference_ink_ratio": (
            candidate_ink / reference_ink if reference_ink else 1
        ),
    }


def render_poppler_reference(source_pdf: Path, page_number: int, output_prefix: Path) -> Path | None:
    executable = os.environ.get("PDFTOPPM_BIN") or shutil.which("pdftoppm")
    if not executable:
        return None
    output_path = output_prefix.with_suffix(".png")
    subprocess.run(
        [
            executable,
            "-f",
            str(page_number),
            "-l",
            str(page_number),
            "-singlefile",
            "-png",
            "-r",
            "90",
            str(source_pdf),
            str(output_prefix),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return output_path


def render(model_path: Path, source_override: str | None, output_override: str | None, validate: bool) -> Path:
    pymupdf, Image, ImageChops, ImageStat = load_runtime()
    model_path = model_path.resolve()
    model_dir = model_path.parent
    model = json.loads(model_path.read_text(encoding="utf-8"))

    if model.get("format") != "plan-editor/v1":
        raise ValueError("Formato de modelo no reconocido")

    source_value = source_override or model["source"]["pdf_path"]
    source_pdf = resolve_path(source_value, model_dir)
    if not source_pdf.exists():
        raise FileNotFoundError(
            f"No se encontró el PDF fuente: {source_pdf}. Use --source para indicar su ubicación."
        )

    actual_source_hash = sha256_file(source_pdf)
    expected_source_hash = model["source"]["sha256"]
    if actual_source_hash != expected_source_hash:
        raise ValueError(
            "El PDF fuente no coincide con el usado para construir el modelo. "
            f"Esperado {expected_source_hash}; recibido {actual_source_hash}."
        )

    page_index = int(model["source"]["page_index"])
    visible_xrefs = [
        int(layer["ocg_xref"])
        for layer in model["source_layers"]
        if layer.get("visible", True)
    ]

    source_document = pymupdf.open(source_pdf)
    if page_index >= source_document.page_count:
        source_document.close()
        raise IndexError(f"La página {page_index + 1} no existe en el PDF")

    available_xrefs = set(source_document.get_ocgs().keys())
    unknown = set(visible_xrefs) - available_xrefs
    if unknown:
        source_document.close()
        raise ValueError(f"Capas OCG desconocidas en el modelo: {sorted(unknown)}")

    source_page_svg = source_document[page_index].get_svg_image(
        text_as_path=1 if model["output"].get("text_as_path", True) else 0
    )

    temporary_pdf: Path | None = None
    configured_document = None
    try:
        source_document.set_layer(-1, basestate="OFF", on=visible_xrefs)
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as handle:
            temporary_pdf = Path(handle.name)
        source_document.save(temporary_pdf)
        source_document.close()

        configured_document = pymupdf.open(temporary_pdf)
        configured_page = configured_document[page_index]
        extracted_svg = configured_page.get_svg_image(
            text_as_path=1 if model["output"].get("text_as_path", True) else 0
        )
        faithful_value = model["output"].get("faithful_svg_path")
        if faithful_value:
            faithful_path = resolve_path(faithful_value, model_dir)
            faithful_path.parent.mkdir(parents=True, exist_ok=True)
            faithful_path.write_text(extracted_svg, encoding="utf-8")

        profiled_svg, enhanced_stroke_count = apply_visual_profile(extracted_svg, model)
        profiled_svg = apply_color_profile(profiled_svg, model)
        regenerated_svg = apply_operations(
            profiled_svg,
            model,
            model_dir,
            pymupdf,
            source_pdf,
            page_index,
        )

        output_value = output_override or model["output"]["svg_path"]
        output_path = resolve_path(output_value, model_dir)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(regenerated_svg, encoding="utf-8")

        if validate:
            validation_dir = model_dir / "validation"
            validation_dir.mkdir(parents=True, exist_ok=True)
            validation_settings = model.get("validation", {})
            generate_side_by_side = validation_settings.get("generate_side_by_side", True)
            keep_intermediate_images = validation_settings.get("keep_intermediate_images", True)
            matrix = pymupdf.Matrix(2, 2)

            configured_pixmap = configured_page.get_pixmap(matrix=matrix, alpha=False, annots=False)
            configured_png = validation_dir / "configured-pdf.png"
            configured_pixmap.save(configured_png)

            faithful_document = pymupdf.open("svg", extracted_svg.encode("utf-8"))
            faithful_pixmap = faithful_document[0].get_pixmap(matrix=matrix, alpha=False)
            faithful_png = validation_dir / "faithful-svg.png"
            faithful_pixmap.save(faithful_png)
            faithful_document.close()

            svg_document = pymupdf.open("svg", regenerated_svg.encode("utf-8"))
            svg_pixmap = svg_document[0].get_pixmap(matrix=matrix, alpha=False)
            preview_value = model["output"].get("preview_png_path")
            svg_png = (
                resolve_path(preview_value, model_dir)
                if preview_value
                else validation_dir / "regenerated-svg.png"
            )
            svg_png.parent.mkdir(parents=True, exist_ok=True)
            svg_pixmap.save(svg_png)
            svg_document.close()

            reference_image = Image.open(configured_png).convert("RGB")
            faithful_image = Image.open(faithful_png).convert("RGB")
            regenerated_image = Image.open(svg_png).convert("RGB")
            faithful_metrics, _ = image_metrics(
                reference_image, faithful_image, ImageChops, ImageStat
            )
            metrics, diff_image = image_metrics(
                reference_image, regenerated_image, ImageChops, ImageStat
            )
            diff_path = validation_dir / "diff-amplified.png"
            diff_image.point(lambda value: min(255, value * 6)).save(diff_path)

            comparison_scale = 1.25
            comparison_matrix = pymupdf.Matrix(comparison_scale, comparison_scale)
            poppler_reference_path = render_poppler_reference(
                source_pdf,
                page_index + 1,
                validation_dir / "pdf-original-poppler-90dpi",
            )
            if poppler_reference_path:
                reference_preview = Image.open(poppler_reference_path).convert("RGB")
                comparison_reference_renderer = "Poppler 90 dpi"
            else:
                reference_preview_pixmap = configured_page.get_pixmap(
                    matrix=comparison_matrix, alpha=False, annots=False
                )
                reference_preview = Image.frombytes(
                    "RGB",
                    (reference_preview_pixmap.width, reference_preview_pixmap.height),
                    reference_preview_pixmap.samples,
                )
                comparison_reference_renderer = "PyMuPDF 90 dpi equivalente"
            comparison_svg_document = pymupdf.open("svg", regenerated_svg.encode("utf-8"))
            regenerated_preview_pixmap = comparison_svg_document[0].get_pixmap(
                matrix=comparison_matrix, alpha=False
            )
            regenerated_preview = Image.frombytes(
                "RGB",
                (regenerated_preview_pixmap.width, regenerated_preview_pixmap.height),
                regenerated_preview_pixmap.samples,
            )
            comparison_svg_document.close()
            comparison_ink_metrics = ink_metrics(reference_preview, regenerated_preview)

            comparison_crop_pt = validation_settings.get(
                "comparison_crop_pt", [35, 35, 1000, 757]
            )
            crop_box = tuple(
                round(float(coordinate) * comparison_scale)
                for coordinate in comparison_crop_pt
            )
            reference_preview = reference_preview.crop(crop_box)
            regenerated_preview = regenerated_preview.crop(crop_box)

            comparison_path = validation_dir / "comparison-side-by-side.png"
            if generate_side_by_side:
                from PIL import ImageDraw

                gutter = 24
                header = 44
                comparison = Image.new(
                    "RGB",
                    (
                        reference_preview.width + regenerated_preview.width + gutter,
                        max(reference_preview.height, regenerated_preview.height) + header,
                    ),
                    "white",
                )
                comparison.paste(reference_preview, (0, header))
                comparison.paste(regenerated_preview, (reference_preview.width + gutter, header))
                draw = ImageDraw.Draw(comparison)
                draw.text(
                    (16, 14),
                    f"PDF ORIGINAL - {comparison_reference_renderer.upper()}",
                    fill="black",
                )
                draw.text(
                    (reference_preview.width + gutter + 16, 14),
                    "SVG REGENERADO - PERFIL LEGIBLE",
                    fill="black",
                )
                draw.line(
                    (reference_preview.width + gutter // 2, 0, reference_preview.width + gutter // 2, comparison.height),
                    fill="#888888",
                    width=1,
                )
                comparison.save(comparison_path)
            elif comparison_path.exists():
                comparison_path.unlink()

            report = {
                "generated_at_utc": datetime.now(timezone.utc).isoformat(),
                "model": str(model_path),
                "source_pdf": str(source_pdf),
                "source_pdf_sha256": actual_source_hash,
                "page_number": page_index + 1,
                "source_page_svg_sha256": sha256_bytes(source_page_svg.encode("utf-8")),
                "configured_page_svg_sha256": sha256_bytes(extracted_svg.encode("utf-8")),
                "regenerated_svg_sha256": sha256_bytes(regenerated_svg.encode("utf-8")),
                "source_and_regenerated_svg_byte_identical": source_page_svg == regenerated_svg,
                "source_and_faithful_svg_byte_identical": source_page_svg == extracted_svg,
                "visible_ocg_xrefs": visible_xrefs,
                "visual_profile": model.get("visual_profile", {}),
                "enhanced_hairline_count": enhanced_stroke_count,
                "operation_count": len(model.get("operations", [])),
                "configured_pdf_vs_faithful_svg_pixels": faithful_metrics,
                "configured_pdf_vs_profiled_svg_pixels": metrics,
                "poppler_reference_vs_profiled_svg_ink": comparison_ink_metrics,
                "side_by_side_reference_renderer": comparison_reference_renderer,
                "side_by_side_crop_pt": comparison_crop_pt,
                "side_by_side_generated": generate_side_by_side,
                "note": (
                    "El SVG faithful conserva igualdad canónica con la fuente. El SVG principal aplica un "
                    "grosor mínimo a hairlines para reproducir la densidad visual que los visores PDF asignan "
                    "a esas líneas dependientes del dispositivo."
                ),
            }
            (validation_dir / "california_report.json").write_text(
                json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )

            if not keep_intermediate_images:
                for intermediate in (
                    configured_png,
                    faithful_png,
                    diff_path,
                    poppler_reference_path,
                    validation_dir / "regenerated-svg.png",
                ):
                    if intermediate and intermediate != svg_png and intermediate.exists():
                        intermediate.unlink()

        return output_path
    finally:
        if not source_document.is_closed:
            source_document.close()
        if configured_document is not None and not configured_document.is_closed:
            configured_document.close()
        if temporary_pdf is not None and temporary_pdf.exists():
            temporary_pdf.unlink()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model", type=Path, help="Ruta al archivo california_model.json")
    parser.add_argument("--source", help="Ruta alternativa al PDF fuente")
    parser.add_argument("--output", help="Ruta alternativa para el SVG de salida")
    parser.add_argument("--validate", action="store_true", help="Renderiza y compara el resultado")
    arguments = parser.parse_args()
    output_path = render(arguments.model, arguments.source, arguments.output, arguments.validate)
    print(output_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
