#!/usr/bin/env python3
"""Aplica REV-02: retiro temporal de escalera, pasillo y sus columnas en Nivel 1."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


REFERENCE_BOUNDS = [149.34, 124.185, 793.005, 629.256]
REFERENCE_MASKS = [
    # Línea que cerraba el pasillo y las dos columnas que la acompañaban.
    [258.0, 317.0, 255.0, 14.0],
    # Retorno lateral del pasillo hacia el muro de los apartamentos.
    [258.0, 280.0, 11.0, 52.0],
    # Escalera y rótulo de estacionamiento de motos.
    [397.0, 319.0, 118.0, 89.0],
    # Línea lateral y columnas alineadas al costado derecho del antiguo pasillo.
    [501.0, 319.0, 14.0, 307.0],
]


SHEETS = {
    "nivel_1": [149.34, 124.185, 793.005, 629.256],
    "acabados_nivel_1": [100.47, 114.675, 758.955, 630.217],
    "electrico_nivel_1": [127.65, 118.905, 784.695, 636.465],
}

HYDRAULIC_MASKS = [
    [248.0, 317.0, 270.0, 14.0],
    [248.0, 280.0, 18.0, 52.0],
    [390.0, 315.0, 128.0, 115.0],
    [490.0, 319.0, 28.0, 307.0],
]

REV02_SUMMARY = [
    "Retiro temporal de escalera y pasillo del estacionamiento en Nivel 1.",
    "Retiro de las columnas y líneas asociadas al pasillo aplazado.",
    "Vehículos permanecen retirados conforme a REV-LIMPIEZA-01.",
]


def revision_sheet_id(value: str) -> str:
    base = value.split("_revision_sin_escalera", 1)[0]
    base = base.split("_edicion_limpia", 1)[0]
    return base + "_revision_sin_escalera"


def transform_regions(
    regions: list[list[float]],
    source_bounds: list[float],
    target_bounds: list[float],
) -> list[list[float]]:
    source_x0, source_y0, source_x1, source_y1 = source_bounds
    target_x0, target_y0, target_x1, target_y1 = target_bounds
    scale_x = (target_x1 - target_x0) / (source_x1 - source_x0)
    scale_y = (target_y1 - target_y0) / (source_y1 - source_y0)
    return [
        [
            target_x0 + (x - source_x0) * scale_x,
            target_y0 + (y - source_y0) * scale_y,
            width * scale_x,
            height * scale_y,
        ]
        for x, y, width, height in regions
    ]


def whiteout(operation_id: str, rectangle: list[float], description: str) -> dict:
    return {
        "id": operation_id,
        "type": "whiteout",
        "rect_pt": [round(value, 3) for value in rectangle],
        "fill": "#ffffff",
        "visible": True,
        "description": description,
    }


def configure_sheet(folder: str, bounds: list[float]) -> None:
    model_path = ROOT / folder / "california_model.json"
    model = json.loads(model_path.read_text(encoding="utf-8"))
    model["project_id"] = "casa_california_remodelacion_revision_sin_escalera"
    model["sheet_id"] = revision_sheet_id(model["sheet_id"])

    masks = transform_regions(REFERENCE_MASKS, REFERENCE_BOUNDS, bounds)
    descriptions = [
        "Retira la línea de cierre y las columnas superiores del pasillo aplazado.",
        "Retira el retorno lateral del pasillo aplazado.",
        "Retira la escalera y su rótulo asociado.",
        "Retira la línea lateral y las columnas del pasillo aplazado.",
    ]
    model["operations"] = [
        operation
        for operation in model.get("operations", [])
        if not operation.get("id", "").startswith("edit.rev02-")
    ]
    model["operations"].extend(
        whiteout(f"edit.rev02-remove-stair-corridor-{index:02d}", mask, description)
        for index, (mask, description) in enumerate(zip(masks, descriptions), start=1)
    )
    entities = [
        entity
        for entity in model.get("semantic_entities", [])
        if not entity.get("id", "").startswith("REV02-")
    ]
    entities.extend(
        [
            {
                "id": "REV02-STAIR-N1-REMOVE",
                "type": "area",
                "label": "Escalera de estacionamiento retirada temporalmente",
                "level": "Nivel 1",
                "visible": False,
                "properties": {"revision": "REV-02", "phase": "aplazada"},
            },
            {
                "id": "REV02-CORRIDOR-N1-REMOVE",
                "type": "area",
                "label": "Pasillo y columnas asociadas retirados temporalmente",
                "level": "Nivel 1",
                "visible": False,
                "properties": {"revision": "REV-02", "phase": "aplazada"},
            },
        ]
    )
    model["semantic_entities"] = entities
    previous_summary = [
        item
        for item in model.get("edit_revision", {}).get("summary", [])
        if item not in REV02_SUMMARY
    ]
    model["edit_revision"] = {
        "id": "REV-02",
        "base_revision": "REV-LIMPIEZA-01",
        "non_destructive": True,
        "summary": previous_summary + REV02_SUMMARY,
    }
    model_path.write_text(json.dumps(model, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def configure_hydraulic_sheet() -> None:
    model_path = ROOT / "hidraulico_nivel_1" / "california_model.json"
    model = json.loads(model_path.read_text(encoding="utf-8"))
    model["project_id"] = "casa_california_remodelacion_revision_sin_escalera"
    model["sheet_id"] = revision_sheet_id(model["sheet_id"])
    model["operations"] = [
        operation
        for operation in model.get("operations", [])
        if not operation.get("id", "").startswith("edit.rev02-")
    ]
    model["operations"].extend(
        whiteout(
            f"edit.rev02-remove-stair-corridor-{index:02d}",
            mask,
            "Retira geometría arquitectónica de escalera, pasillo y columnas aplazadas.",
        )
        for index, mask in enumerate(HYDRAULIC_MASKS, start=1)
    )
    model["operations"].append(
        {
            "id": "edit.rev02-restore-hydraulic-linework",
            "type": "append_source_colors",
            "stroke_colors": ["#0000ff", "#f8991e"],
            "fill_colors": ["#0000ff", "#f8991e"],
            "visible": True,
            "description": "Recupera redes hidráulicas azules y símbolos naranjas después del retiro arquitectónico.",
        }
    )
    entities = [
        entity
        for entity in model.get("semantic_entities", [])
        if not entity.get("id", "").startswith("REV02-")
    ]
    entities.extend(
        [
            {
                "id": "REV02-STAIR-N1-REMOVE",
                "type": "area",
                "label": "Escalera de estacionamiento retirada temporalmente",
                "level": "Nivel 1",
                "visible": False,
                "properties": {"revision": "REV-02", "phase": "aplazada"},
            },
            {
                "id": "REV02-CORRIDOR-N1-REMOVE",
                "type": "area",
                "label": "Pasillo y columnas asociadas retirados temporalmente",
                "level": "Nivel 1",
                "visible": False,
                "properties": {"revision": "REV-02", "phase": "aplazada"},
            },
        ]
    )
    model["semantic_entities"] = entities
    hydraulic_summary = REV02_SUMMARY + [
        "Conservación de redes hidráulicas coloreadas sobre el área revisada."
    ]
    previous_summary = [
        item
        for item in model.get("edit_revision", {}).get("summary", [])
        if item not in hydraulic_summary
    ]
    model["edit_revision"] = {
        "id": "REV-02",
        "base_revision": "REV-LIMPIEZA-01",
        "non_destructive": True,
        "summary": previous_summary + hydraulic_summary,
    }
    model_path.write_text(json.dumps(model, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def configure_unchanged_sheets() -> None:
    for folder in (
        "portada",
        "nivel_2",
        "acabados_nivel_2",
        "electrico_nivel_2",
        "hidraulico_nivel_2",
    ):
        model_path = ROOT / folder / "california_model.json"
        model = json.loads(model_path.read_text(encoding="utf-8"))
        model["project_id"] = "casa_california_remodelacion_revision_sin_escalera"
        model["sheet_id"] = revision_sheet_id(model["sheet_id"])
        previous_summary = [
            item
            for item in model.get("edit_revision", {}).get("summary", [])
            if item != "Hoja conservada sin cambios adicionales en REV-02."
        ]
        model["edit_revision"] = {
            "id": "REV-02",
            "base_revision": "REV-LIMPIEZA-01",
            "non_destructive": True,
            "summary": previous_summary + ["Hoja conservada sin cambios adicionales en REV-02."],
        }
        model_path.write_text(json.dumps(model, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def configure_project() -> None:
    project_path = ROOT / "california_project.json"
    project = json.loads(project_path.read_text(encoding="utf-8"))
    project["project_id"] = "casa_california_remodelacion_revision_sin_escalera"
    project["title"] = "Casa California - revisión sin escalera ni pasillo de estacionamiento"
    project["base_project"] = "REV-LIMPIEZA-01"
    project["revision"] = {
        "id": "REV-02",
        "preserves_base_files": True,
        "scope": "Hojas de Nivel 1; las demás hojas se conservan como referencia",
        "changes": [
            "Escalera del estacionamiento retirada.",
            "Pasillo y columnas asociadas retirados.",
            "Vehículos retirados.",
        ],
    }
    for sheet in project["sheets"]:
        sheet["status"] = "pending_rev02_validation"
        sheet.pop("validation", None)
    project_path.write_text(json.dumps(project, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    for folder, bounds in SHEETS.items():
        configure_sheet(folder, bounds)
    configure_hydraulic_sheet()
    configure_unchanged_sheets()
    configure_project()


if __name__ == "__main__":
    main()
