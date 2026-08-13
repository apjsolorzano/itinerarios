#!/usr/bin/env python3
"""Construye manifiestos consistentes para las nueve hojas del PDF fuente."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

import pymupdf
from pypdf import PdfReader


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "source" / "california_planos_casa_remodelacion.pdf"

SHEETS = [
    {"page": 1, "dir": "portada", "id": "portada", "title": "PORTADA", "code": "PORTADA", "discipline": "general", "scale": "no aplica"},
    {"page": 2, "dir": "nivel_1", "id": "nivel_1_a1_4", "title": "PLANTA ARQUITECTÓNICA NIVEL 1", "code": "A1/4", "discipline": "arquitectura", "scale": "1:2500"},
    {"page": 3, "dir": "nivel_2", "id": "nivel_2_a2_4", "title": "PLANTA ARQUITECTÓNICA NIVEL 2", "code": "A2/4", "discipline": "arquitectura", "scale": "1:2500"},
    {"page": 4, "dir": "acabados_nivel_1", "id": "acabados_nivel_1_a3_4", "title": "PLANO DE ACABADOS NIVEL 1", "code": "A3/4", "discipline": "acabados", "scale": "1:2500"},
    {"page": 5, "dir": "acabados_nivel_2", "id": "acabados_nivel_2_a4_4", "title": "PLANO DE ACABADOS NIVEL 2", "code": "A4/4", "discipline": "acabados", "scale": "1:2500"},
    {"page": 6, "dir": "electrico_nivel_1", "id": "electrico_nivel_1_e1_2", "title": "PLANO DE INSTALACIÓN ELÉCTRICA NIVEL 1", "code": "E1/2", "discipline": "eléctrico", "scale": "1:2500"},
    {"page": 7, "dir": "electrico_nivel_2", "id": "electrico_nivel_2_e2_2", "title": "PLANO DE INSTALACIÓN ELÉCTRICA NIVEL 2", "code": "E2/2", "discipline": "eléctrico", "scale": "1:2500"},
    {"page": 8, "dir": "hidraulico_nivel_1", "id": "hidraulico_nivel_1_1_ih", "title": "PLANO DE INSTALACIONES HIDRÁULICAS NIVEL 1", "code": "1/I-H", "discipline": "hidráulico", "scale": "INDICADA / 1:2500"},
    {"page": 9, "dir": "hidraulico_nivel_2", "id": "hidraulico_nivel_2_2_ih", "title": "PLANO DE INSTALACIONES HIDRÁULICAS NIVEL 2", "code": "2/I-H", "discipline": "hidráulico", "scale": "INDICADA / 1:2500"}
]

CATEGORIES = {
    "0": "base_geometry",
    "100 FLECH": "symbols",
    "CORRECCIONES": "revisions",
    "Columnas nuevas": "columns_new",
    "Flecha": "circulation_arrow",
    "IE_IL_BOCAS": "electrical_lighting_points",
    "IE_IL_CAÑERÍA_LOSA": "electrical_conduits",
    "IE_TO_BOCAS": "electrical_outlet_points",
    "Muebles": "furniture_and_fixtures",
    "PAREDES ACTUALES": "walls_existing",
    "PAREDES NUEVAS": "walls_new",
    "PORTON": "gate",
    "SIMBOLOGIA": "finish_symbols",
    "TEXTO": "labels_and_schedules",
    "Vegetación-h": "landscape",
    "columnas": "columns_existing",
    "cotas": "dimensions",
    "ejes": "grid",
    "hatch": "hatch",
    "membrete": "sheet_border_and_title_block",
    "ventana": "windows",
    "wall": "wall_misc"
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def slug(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "_", normalized.lower()).strip("_") or "layer"


def aggregate_bbox_log(page) -> dict[str, dict]:
    aggregated: dict[str, dict] = {}
    for kind, bbox, layer_name in page.get_bboxlog(layers=True):
        name = layer_name or ""
        if name not in aggregated:
            aggregated[name] = {
                "object_count": 0,
                "bounds_pt": [float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3])],
                "kinds": defaultdict(int),
            }
        stats = aggregated[name]
        stats["object_count"] += 1
        stats["bounds_pt"] = [
            min(stats["bounds_pt"][0], bbox[0]),
            min(stats["bounds_pt"][1], bbox[1]),
            max(stats["bounds_pt"][2], bbox[2]),
            max(stats["bounds_pt"][3], bbox[3]),
        ]
        stats["kinds"][kind] += 1
    for stats in aggregated.values():
        stats["bounds_pt"] = [round(value, 3) for value in stats["bounds_pt"]]
        stats["kinds"] = dict(stats["kinds"])
    return aggregated


def page_ocg_layers(reader_page) -> list[tuple[int, str]]:
    properties = reader_page.get("/Resources", {}).get("/Properties", {})
    result: list[tuple[int, str]] = []
    for value in properties.values():
        xref = getattr(value, "idnum", None)
        layer = value.get_object()
        name = str(layer.get("/Name", ""))
        if xref is not None and name:
            result.append((int(xref), name))
    return result


def build() -> None:
    if not SOURCE.exists():
        raise FileNotFoundError(f"No existe el PDF fuente autónomo: {SOURCE}")

    source_hash = sha256_file(SOURCE)
    pymupdf_document = pymupdf.open(SOURCE)
    pypdf_document = PdfReader(str(SOURCE))
    if pymupdf_document.page_count != len(SHEETS):
        raise ValueError(f"Se esperaban {len(SHEETS)} páginas y se encontraron {pymupdf_document.page_count}")

    project_sheets = []
    for sheet in SHEETS:
        page_index = sheet["page"] - 1
        page = pymupdf_document[page_index]
        stats = aggregate_bbox_log(page)
        layers = []
        for xref, name in page_ocg_layers(pypdf_document.pages[page_index]):
            layer_stats = stats.get(name, {"object_count": 0, "bounds_pt": [0, 0, 0, 0], "kinds": {}})
            layers.append(
                {
                    "id": f"src.p{sheet['page']:02d}.{slug(name)}",
                    "name": name,
                    "ocg_xref": xref,
                    "visible": True,
                    "category": CATEGORIES.get(name, "source_layer"),
                    "object_count": layer_stats["object_count"],
                    "bounds_pt": layer_stats["bounds_pt"],
                    "drawing_kinds": layer_stats["kinds"],
                }
            )

        unlayered = stats.get("", {"object_count": 0, "bounds_pt": None, "kinds": {}})
        visual_profile_enabled = sheet["page"] != 1
        model = {
            "$schema": "../california_plan.schema.json",
            "format": "plan-editor/v1",
            "project_id": "casa_california_remodelacion",
            "sheet_id": sheet["id"],
            "title": sheet["title"],
            "discipline": sheet["discipline"],
            "source": {
                "pdf_path": "../source/california_planos_casa_remodelacion.pdf",
                "sha256": source_hash,
                "page_number": sheet["page"],
                "page_index": page_index,
                "sheet_code": sheet["code"],
                "printed_scale_text": sheet["scale"],
                "printed_scale_status": "preservada_del_original_no_calibrada",
                "has_ocg_layers": bool(layers),
            },
            "canvas": {
                "width_pt": float(page.rect.width),
                "height_pt": float(page.rect.height),
                "view_box": [0, 0, float(page.rect.width), float(page.rect.height)],
                "coordinate_system": "puntos_pdf_origen_superior_izquierdo",
                "metric_calibration": {
                    "status": "pending",
                    "method": "calibrar_con_cotas_impresas_antes_de_editar_geometria",
                },
            },
            "source_layers": layers,
            "unlayered_content": {
                "visible": True,
                "object_count": unlayered["object_count"],
                "bounds_pt": unlayered["bounds_pt"],
                "drawing_kinds": unlayered["kinds"],
                "note": (
                    "Esta hoja no contiene capas OCG; su contenido vectorial se conserva como base única."
                    if not layers
                    else "Contenido que el PDF no asignó a una capa OCG."
                ),
            },
            "visual_profile": {
                "enabled": visual_profile_enabled,
                "name": "architectural_validation_dense" if visual_profile_enabled else "faithful_only",
                "minimum_hairline_width_pt": 0.75,
                "force_full_stroke_opacity": True,
                "preserve_explicit_lineweights": True,
                "purpose": (
                    "reproducir la densidad visual de las hairlines del visor PDF"
                    if visual_profile_enabled
                    else "la portada no requiere refuerzo de linework"
                ),
            },
            "validation": {
                "generate_side_by_side": False,
                "keep_intermediate_images": False,
                "comparison_crop_pt": [35, 35, 1000, 757],
            },
            "semantic_entities": [],
            "operations": [],
            "output": {
                "svg_path": "california_regenerated.svg",
                "faithful_svg_path": "california_regenerated-faithful.svg",
                "preview_png_path": "california_preview.png",
                "text_as_path": True,
                "reason_for_text_as_path": "preservar apariencia exacta sin depender de fuentes instaladas",
            },
        }

        sheet_dir = ROOT / sheet["dir"]
        sheet_dir.mkdir(parents=True, exist_ok=True)
        (sheet_dir / "california_model.json").write_text(
            json.dumps(model, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        project_sheets.append(
            {
                "id": sheet["id"],
                "title": sheet["title"],
                "discipline": sheet["discipline"],
                "model": f"{sheet['dir']}/california_model.json",
                "page_number": sheet["page"],
                "sheet_code": sheet["code"],
                "status": "manifest_built",
            }
        )

    project = {
        "format": "plan-editor-project/v1",
        "project_id": "casa_california_remodelacion",
        "title": "Casa California - juego completo de planos regenerables",
        "source_pdf": "source/california_planos_casa_remodelacion.pdf",
        "source_pdf_sha256": source_hash,
        "approved_visual_profile": {
            "name": "architectural_validation_dense",
            "minimum_hairline_width_pt": 0.75,
            "force_full_stroke_opacity": True,
        },
        "sheets": project_sheets,
    }
    (ROOT / "california_project.json").write_text(
        json.dumps(project, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    pymupdf_document.close()


if __name__ == "__main__":
    build()
