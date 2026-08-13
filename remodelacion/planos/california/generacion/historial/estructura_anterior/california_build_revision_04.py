#!/usr/bin/env python3
"""Aplica REV-04: reemplaza cortes de borrado por cierres constructivos coordinados."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent

DISCIPLINE = {
    "portada": ("architecture", "#263238"),
    "nivel_1": ("architecture", "#263238"),
    "nivel_2": ("architecture", "#263238"),
    "acabados_nivel_1": ("finishes", "#737b80"),
    "acabados_nivel_2": ("finishes", "#737b80"),
    "electrico_nivel_1": ("electrical", "#737b80"),
    "electrico_nivel_2": ("electrical", "#737b80"),
    "hidraulico_nivel_1": ("hydraulic", "#636465"),
    "hidraulico_nivel_2": ("hydraulic", "#636465"),
}

# El borrado empieza después del espesor completo del muro que pasa a ser fachada.
LEVEL_2_ROOM_WHITEOUTS = {
    "nivel_2": [500.0, 478.2, 297.0, 163.8],
    "acabados_nivel_2": [474.612, 471.4, 288.803, 159.274],
    "electrico_nivel_2": [506.389, 465.3, 297.775, 164.372],
    "hidraulico_nivel_2": [500.0, 466.2, 292.0, 165.8],
}

# Franjas angostas del dibujo original usadas para recuperar el muro exacto,
# sus columnas y el encuentro con los cerramientos laterales.
CLOSURE_STRIPS = {
    "nivel_1": [533.0, 459.2, 252.0, 10.2],
    "nivel_2": [529.0, 469.0, 250.0, 10.2],
    "acabados_nivel_1": [498.0, 456.8, 250.0, 10.5],
    "acabados_nivel_2": [502.0, 462.6, 242.0, 10.2],
    "electrico_nivel_1": [525.0, 460.8, 251.0, 10.5],
    "electrico_nivel_2": [535.0, 455.5, 251.0, 10.8],
}

STAIR_MASK_PREFIXES = (
    "edit.rev02-remove-stair-corridor-",
    "edit.rev03-remove-level-2-stair-corridor-",
)


def load_model(folder: str) -> tuple[Path, dict]:
    path = ROOT / folder / "california_model.json"
    return path, json.loads(path.read_text(encoding="utf-8"))


def layer_xrefs(model: dict, names: set[str]) -> list[int]:
    wanted = {name.casefold() for name in names}
    return [
        int(layer["ocg_xref"])
        for layer in model.get("source_layers", [])
        if layer["name"].casefold() in wanted
    ]


def stair_regions(model: dict) -> list[list[float]]:
    return [
        operation["rect_pt"]
        for operation in model.get("operations", [])
        if operation.get("id", "").startswith(STAIR_MASK_PREFIXES)
        and "rect_pt" in operation
    ]


def recolored_source_operation(
    operation_id: str,
    xrefs: list[int],
    regions: list[list[float]],
    color: str,
    description: str,
) -> dict:
    return {
        "id": operation_id,
        "type": "append_source_layers_recolored",
        "ocg_xrefs": xrefs,
        "regions_pt": regions,
        "source_colors": ["#000000", "#bababa"],
        "color": color,
        "visible": True,
        "description": description,
    }


def configure_layered_sheet(folder: str) -> None:
    path, model = load_model(folder)
    discipline, _ = DISCIPLINE[folder]
    model["operations"] = [
        operation
        for operation in model.get("operations", [])
        if not operation.get("id", "").startswith("edit.rev04-")
    ]

    if folder in LEVEL_2_ROOM_WHITEOUTS:
        for operation in model["operations"]:
            if operation.get("id") == "edit.rev03-remove-level-2-rooms-5-6":
                operation["rect_pt"] = LEVEL_2_ROOM_WHITEOUTS[folder]
                operation["description"] = (
                    "Retira Habitaciones V y VI desde la cara exterior del nuevo muro de cierre; "
                    "conserva íntegro el cerramiento inferior de Habitación VII."
                )

    model["semantic_entities"] = [
        entity
        for entity in model.get("semantic_entities", [])
        if not entity.get("id", "").startswith("REV04-")
    ]
    level = "Nivel 1" if folder.endswith("nivel_1") or folder == "nivel_1" else "Nivel 2"
    model["semantic_entities"].append(
        {
            "id": f"REV04-EXTERIOR-CLOSURE-{folder.upper().replace('_', '-')}",
            "type": "wall",
            "label": "Muro exterior reconstruido después del retiro de habitaciones",
            "level": level,
            "visible": True,
            "properties": {
                "revision": "REV-04",
                "discipline": discipline,
                "continuous": True,
            },
        }
    )
    model["project_id"] = "casa_california_remodelacion_revision_04"
    model["sheet_id"] = (
        model["sheet_id"]
        .split("_revision_04", 1)[0]
        .split("_revision_03", 1)[0]
        + "_revision_04"
    )
    model["output"]["svg_path"] = "california_rev04.svg"
    model["output"]["faithful_svg_path"] = None
    model["output"]["preview_png_path"] = None
    model["edit_revision"] = {
        "id": "REV-04",
        "base_revision": "REV-03",
        "non_destructive": True,
        "svg_only": True,
        "summary": [
            "Muro de cierre completo conservado en el límite de las habitaciones retiradas.",
            "Los recortes empiezan después del espesor del muro para preservar columnas y encuentros.",
            "Escalera, pasillo y habitaciones descartadas permanecen retirados.",
        ],
    }
    path.write_text(json.dumps(model, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def configure_hydraulic(folder: str) -> None:
    path, model = load_model(folder)
    _, base_color = DISCIPLINE[folder]
    model["operations"] = [
        operation
        for operation in model.get("operations", [])
        if not operation.get("id", "").startswith("edit.rev04-")
    ]
    if folder == "hidraulico_nivel_2":
        for operation in model["operations"]:
            if operation.get("id") == "edit.rev03-remove-level-2-rooms-5-6":
                operation["rect_pt"] = LEVEL_2_ROOM_WHITEOUTS[folder]
                operation["description"] = (
                    "Retira Habitaciones V y VI y sus ramales desde la cara exterior del nuevo cierre."
                )
            elif operation.get("id") == "edit.remove-pool":
                operation["polygon_pt"] = [
                    [125.0, 274.0],
                    [244.0, 274.0],
                    [244.0, 382.0],
                    [125.0, 382.0],
                ]
                operation["description"] = (
                    "Elimina por completo la piscina y su contorno, conservando el lindero exterior."
                )
        closure_paths = [
            ("M511.7 459.3 H792", 0.75),
            ("M511.7 464.4 H792", 0.75),
        ]
        level = "Nivel 2"
    else:
        closure_paths = [
            ("M510.1 461 H679.5", 0.75),
            ("M510.1 465.9 H679.2", 0.75),
        ]
        level = "Nivel 1"
    for index, (path_data, width) in enumerate(closure_paths, start=1):
        model["operations"].append(
            {
                "id": f"edit.rev04-reconstruct-exterior-closure-{index:02d}",
                "type": "draw_path",
                "d": path_data,
                "fill": "none",
                "stroke": base_color,
                "stroke_width_pt": width,
                "stroke_linecap": "square",
                "stroke_linejoin": "miter",
                "visible": True,
                "description": "Línea del muro exterior reconstruido y coordinado con arquitectura.",
            }
        )
    model["semantic_entities"] = [
        entity
        for entity in model.get("semantic_entities", [])
        if not entity.get("id", "").startswith("REV04-")
    ]
    model["semantic_entities"].append(
        {
            "id": f"REV04-EXTERIOR-CLOSURE-{level.upper().replace(' ', '-')}-HYDRAULIC",
            "type": "wall",
            "label": "Muro exterior reconstruido y coordinado con instalaciones hidráulicas",
            "level": level,
            "visible": True,
            "properties": {"revision": "REV-04", "continuous": True},
        }
    )
    model["project_id"] = "casa_california_remodelacion_revision_04"
    model["sheet_id"] = (
        model["sheet_id"]
        .split("_revision_04", 1)[0]
        .split("_revision_03", 1)[0]
        + "_revision_04"
    )
    model["output"]["svg_path"] = "california_rev04.svg"
    model["output"]["faithful_svg_path"] = None
    model["output"]["preview_png_path"] = None
    model["edit_revision"] = {
        "id": "REV-04",
        "base_revision": "REV-03",
        "non_destructive": True,
        "svg_only": True,
        "summary": [
            "Muro exterior reconstruido en doble línea.",
            "Ramales de habitaciones descartadas retirados.",
            "Red hidráulica de los ambientes conservados mantenida.",
        ],
    }
    path.write_text(json.dumps(model, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def configure_cover() -> None:
    path, model = load_model("portada")
    model["project_id"] = "casa_california_remodelacion_revision_04"
    model["sheet_id"] = (
        model["sheet_id"]
        .split("_revision_04", 1)[0]
        .split("_revision_03", 1)[0]
        + "_revision_04"
    )
    model["output"]["svg_path"] = "california_rev04.svg"
    model["output"]["faithful_svg_path"] = None
    model["output"]["preview_png_path"] = None
    model["edit_revision"] = {
        "id": "REV-04",
        "base_revision": "REV-03",
        "non_destructive": True,
        "svg_only": True,
        "summary": ["Portada coordinada con la revisión constructiva vigente."],
    }
    path.write_text(json.dumps(model, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def configure_project() -> None:
    path = ROOT / "california_project.json"
    project = json.loads(path.read_text(encoding="utf-8"))
    project["project_id"] = "casa_california_remodelacion_revision_04"
    project["title"] = "Casa California - REV-04 constructiva, salida SVG"
    project["base_project"] = "REV-03"
    project["revision"] = {
        "id": "REV-04",
        "preserves_base_files": True,
        "output_format": "SVG solamente",
        "changes": [
            "Cierres exteriores completos conservados en vez de dejar cortes de borrado.",
            "Habitación III de Nivel 1 y Habitación VII de Nivel 2 quedan cerradas por muros continuos.",
            "Todas las disciplinas coordinadas con el nuevo perímetro.",
        ],
    }
    for sheet in project["sheets"]:
        sheet["status"] = "pending_rev04_svg"
        sheet.pop("validation", None)
        sheet.pop("output_svg", None)
    path.write_text(json.dumps(project, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    for folder in (
        "nivel_1",
        "nivel_2",
        "acabados_nivel_1",
        "acabados_nivel_2",
        "electrico_nivel_1",
        "electrico_nivel_2",
    ):
        configure_layered_sheet(folder)
    configure_hydraulic("hidraulico_nivel_1")
    configure_hydraulic("hidraulico_nivel_2")
    configure_cover()
    configure_project()


if __name__ == "__main__":
    main()
