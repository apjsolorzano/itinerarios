#!/usr/bin/env python3
"""Configura la edición limpia sin alterar el proyecto de reproducción original."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


LEVEL_1_BATHROOM_FIXTURES = [
    [188, 118, 42, 42],
    [490, 118, 78, 43],
    [600, 118, 48, 43],
    [754, 318, 44, 54],
    [752, 390, 46, 58],
]

LEVEL_2_BATHROOM_FIXTURES = [
    [174, 118, 45, 42],
    [480, 118, 82, 43],
    [594, 118, 52, 43],
    [752, 303, 44, 58],
    [750, 394, 46, 58],
    [748, 486, 48, 60],
    [746, 572, 50, 60],
]

LEVEL_1_FURNITURE_BOUNDS = [149.34, 124.185, 793.005, 629.256]
LEVEL_2_FURNITURE_BOUNDS = [132.33, 127.305, 787.755, 641.497]


SHEETS = {
    "nivel_1": {
        "base_xref": 74,
        "furniture_bounds": [149.34, 124.185, 793.005, 629.256],
        "furniture_xref": 82,
        "bathrooms": LEVEL_1_BATHROOM_FIXTURES,
        "pool": [[149, 283.5], [245, 283.5], [245, 373], [177, 373]],
        "remove_rooms_1_2": True,
    },
    "nivel_2": {
        "base_xref": 91,
        "furniture_bounds": [132.33, 127.305, 787.755, 641.497],
        "furniture_xref": 99,
        "bathrooms": LEVEL_2_BATHROOM_FIXTURES,
        "pool": [[131, 289], [229, 289], [229, 376], [160, 376]],
        "remove_rooms_1_2": False,
    },
    "acabados_nivel_1": {
        "base_xref": 109,
        "furniture_bounds": [100.47, 114.675, 758.955, 630.217],
        "furniture_xref": 116,
        "bathrooms": LEVEL_1_BATHROOM_FIXTURES,
        "pool": [[99, 284], [201, 284], [201, 374], [127, 374]],
        "remove_rooms_1_2": True,
    },
    "acabados_nivel_2": {
        "base_xref": 127,
        "furniture_bounds": [117.09, 131.205, 754.425, 630.186],
        "furniture_xref": 134,
        "bathrooms": LEVEL_2_BATHROOM_FIXTURES,
        "pool": [[99, 289], [201, 289], [201, 376], [127, 376]],
        "remove_rooms_1_2": False,
    },
    "electrico_nivel_1": {
        "base_xref": 312,
        "furniture_bounds": [127.65, 118.905, 784.695, 636.465],
        "furniture_xref": 315,
        "bathrooms": LEVEL_1_BATHROOM_FIXTURES,
        "pool": [[130, 284], [230, 284], [230, 374], [158, 374]],
        "remove_rooms_1_2": True,
    },
    "electrico_nivel_2": {
        "base_xref": 312,
        "furniture_bounds": [137.76, 113.595, 794.895, 629.167],
        "furniture_xref": 315,
        "bathrooms": LEVEL_2_BATHROOM_FIXTURES,
        "pool": [[130, 289], [230, 289], [230, 376], [158, 376]],
        "remove_rooms_1_2": False,
    },
}


def erase_furniture_except_bathrooms(xref: int, regions: list[list[float]]) -> dict:
    return {
        "id": "edit.erase-furniture-except-bathrooms",
        "type": "erase_source_layer_elements",
        "ocg_xrefs": [xref],
        "preserve_regions_pt": regions,
        "visible": True,
        "description": "Borra mobiliario por objeto y conserva lavamanos, inodoros y aparatos de baños.",
    }


def restore_bathroom_fixtures(xref: int, regions: list[list[float]]) -> dict:
    return {
        "id": "edit.restore-bathroom-fixtures",
        "type": "append_source_layer_elements",
        "ocg_xrefs": [xref],
        "target_regions_pt": regions,
        "preserve_regions_pt": [],
        "visible": True,
        "description": "Recupera únicamente lavamanos, inodoros y demás aparatos dentro de baños.",
    }


def pool_whiteout(points: list[list[float]]) -> dict:
    return {
        "id": "edit.remove-pool",
        "type": "whiteout",
        "polygon_pt": points,
        "fill": "#ffffff",
        "visible": True,
        "description": "Elimina la piscina y deja libre el patio, conservando sus límites exteriores.",
    }


def erase_patio_furniture(xref: int, pool: list[list[float]]) -> dict:
    left = min(point[0] for point in pool)
    top = min(point[1] for point in pool)
    return {
        "id": "edit.erase-patio-furniture",
        "type": "erase_source_layer_elements",
        "ocg_xrefs": [xref],
        "target_regions_pt": [[left + 48, top + 84, 92, 184]],
        "preserve_regions_pt": [],
        "visible": True,
        "description": "Retira mesas y sillas exteriores sin borrar la vegetación.",
    }


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


def rooms_whiteout(rectangle: list[float] | None = None) -> dict:
    return {
        "id": "edit.remove-level-1-rooms-1-2",
        "type": "whiteout",
        "rect_pt": rectangle or [533, 474, 246, 152],
        "fill": "#ffffff",
        "visible": True,
        "description": (
            "Vacía Habitaciones I y II; el rectángulo se mantiene dentro del perímetro para conservar "
            "el muro inferior de Habitación III, el muro exterior derecho y el cerramiento del portón."
        ),
    }


def configure_ocg_sheet(folder: str, settings: dict) -> None:
    model_path = ROOT / folder / "california_model.json"
    model = json.loads(model_path.read_text(encoding="utf-8"))
    model["project_id"] = "casa_california_remodelacion_edicion_limpia"
    model["sheet_id"] = model["sheet_id"].split("_edicion_limpia", 1)[0] + "_edicion_limpia"
    for layer in model["source_layers"]:
        if layer["name"].casefold() == "muebles":
            layer["visible"] = False
            layer["edit_reason"] = "Capa global oculta; se recuperan por objeto únicamente los aparatos de baños."

    reference_bounds = (
        LEVEL_1_FURNITURE_BOUNDS
        if settings["remove_rooms_1_2"]
        else LEVEL_2_FURNITURE_BOUNDS
    )
    bathroom_regions = transform_regions(
        settings["bathrooms"],
        reference_bounds,
        settings["furniture_bounds"],
    )
    operations = [
        restore_bathroom_fixtures(settings["furniture_xref"], bathroom_regions),
        erase_patio_furniture(settings["base_xref"], settings["pool"]),
        pool_whiteout(settings["pool"]),
    ]
    if settings["remove_rooms_1_2"]:
        room_region = transform_regions(
            [[533, 474, 246, 152]],
            LEVEL_1_FURNITURE_BOUNDS,
            settings["furniture_bounds"],
        )[0]
        operations.append(rooms_whiteout(room_region))
    model["operations"] = operations
    model["semantic_entities"] = [
        {
            "id": "EDIT-BATHROOM-FIXTURES-KEEP",
            "type": "fixture",
            "label": "Aparatos sanitarios de baños conservados",
            "visible": True,
            "properties": {"includes_washbasins": True, "includes_toilets": True},
        },
        {
            "id": "EDIT-POOL-REMOVE",
            "type": "area",
            "label": "Piscina eliminada",
            "visible": False,
            "properties": {"operation_id": "edit.remove-pool"},
        },
    ]
    if settings["remove_rooms_1_2"]:
        model["semantic_entities"].append(
            {
                "id": "N1-ROOMS-01-02-REMOVE",
                "type": "area",
                "label": "Habitaciones I y II eliminadas",
                "level": "Nivel 1",
                "visible": False,
                "properties": {"operation_id": "edit.remove-level-1-rooms-1-2"},
            }
        )
    model["edit_revision"] = {
        "id": "REV-LIMPIEZA-01",
        "base_project": "../plano_california",
        "non_destructive": True,
        "summary": [
            "Retiro de mobiliario, camas y cocinas.",
            "Conservación de aparatos sanitarios dentro de baños, incluidos lavamanos.",
            "Retiro de piscina.",
        ]
        + (
            ["Retiro de Habitaciones I y II en Nivel 1, conservando cerramientos solicitados."]
            if settings["remove_rooms_1_2"]
            else []
        ),
    }
    model_path.write_text(json.dumps(model, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def configure_hydraulic_sheet(folder: str, level: int) -> None:
    model_path = ROOT / folder / "california_model.json"
    model = json.loads(model_path.read_text(encoding="utf-8"))
    model["project_id"] = "casa_california_remodelacion_edicion_limpia"
    model["sheet_id"] = model["sheet_id"].split("_edicion_limpia", 1)[0] + "_edicion_limpia"
    furniture_page_index = 1 if level == 1 else 2
    furniture_xref = 82 if level == 1 else 99
    bathrooms = LEVEL_1_BATHROOM_FIXTURES if level == 1 else LEVEL_2_BATHROOM_FIXTURES
    pool = (
        [[140, 284], [242, 284], [242, 374], [169, 374]]
        if level == 1
        else [[130, 289], [230, 289], [230, 376], [158, 376]]
    )
    common_furniture_masks = [
        [225, 125, 78, 40],
        [340, 125, 78, 40],
        [225, 235, 78, 40],
        [340, 235, 78, 40],
        [710, 182, 82, 42],
        [705, 238, 87, 42],
        [245, 255, 62, 26],
        [548, 257, 78, 35],
        [625, 280, 48, 42],
        [668, 280, 86, 48],
        [548, 367, 78, 32],
        [625, 368, 48, 46],
        [666, 367, 88, 56],
    ]
    level_2_extra_masks = [
        [548, 457, 78, 32],
        [625, 458, 48, 46],
        [666, 457, 88, 56],
        [548, 542, 78, 32],
        [625, 543, 48, 46],
        [666, 542, 88, 56],
        [548, 608, 82, 24],
    ]
    furniture_masks = common_furniture_masks + (level_2_extra_masks if level == 2 else [])
    operations = [
        {
            "id": "edit.restore-hydraulic-linework",
            "type": "append_source_colors",
            "stroke_colors": ["#0000ff", "#f8991e"],
            "fill_colors": ["#0000ff", "#f8991e"],
            "visible": True,
            "description": "Restaura redes hidráulicas, drenajes, símbolos y notas sobre el borrado.",
        },
        pool_whiteout(pool),
    ]
    operations[0:0] = [
        {
            "id": f"edit.remove-hydraulic-furniture-{index:02d}",
            "type": "whiteout",
            "rect_pt": rectangle,
            "fill": "#ffffff",
            "visible": True,
            "description": "Máscara localizada de mobiliario en la base hidráulica sin capas.",
        }
        for index, rectangle in enumerate(furniture_masks, start=1)
    ]
    if level == 1:
        operations.append(rooms_whiteout([533, 466, 246, 160]))
    model["operations"] = operations
    model["semantic_entities"] = [
        {
            "id": "EDIT-BATHROOM-FIXTURES-KEEP",
            "type": "fixture",
            "label": "Aparatos sanitarios de baños conservados",
            "level": f"Nivel {level}",
            "visible": True,
            "properties": {"includes_washbasins": True, "includes_toilets": True},
        },
        {
            "id": "EDIT-POOL-REMOVE",
            "type": "area",
            "label": "Piscina eliminada",
            "visible": False,
            "properties": {"operation_id": "edit.remove-pool"},
        },
    ]
    if level == 1:
        model["semantic_entities"].append(
            {
                "id": "N1-ROOMS-01-02-REMOVE",
                "type": "area",
                "label": "Habitaciones I y II eliminadas",
                "level": "Nivel 1",
                "visible": False,
                "properties": {"operation_id": "edit.remove-level-1-rooms-1-2"},
            }
        )
    model["edit_revision"] = {
        "id": "REV-LIMPIEZA-01",
        "base_project": "../plano_california",
        "non_destructive": True,
        "summary": [
            "Retiro vectorial de mobiliario, camas y cocinas.",
            "Conservación de baños completos, incluidos lavamanos.",
            "Retiro de piscina.",
        ]
        + (
            ["Retiro de Habitaciones I y II en Nivel 1, conservando cerramientos solicitados."]
            if level == 1
            else []
        ),
    }
    model_path.write_text(json.dumps(model, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def configure_project() -> None:
    project_path = ROOT / "california_project.json"
    project = json.loads(project_path.read_text(encoding="utf-8"))
    project["project_id"] = "casa_california_remodelacion_edicion_limpia"
    project["title"] = "Casa California - edición limpia independiente"
    project["base_project"] = "../plano_california"
    project["revision"] = {
        "id": "REV-LIMPIEZA-01",
        "preserves_base_files": True,
        "bathroom_washbasins_preserved": True,
        "scope": "Todas las hojas del juego de planos",
    }
    for sheet in project["sheets"]:
        sheet["status"] = "pending_clean_validation"
        sheet.pop("validation", None)
    project_path.write_text(json.dumps(project, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def configure_cover() -> None:
    model_path = ROOT / "portada" / "california_model.json"
    model = json.loads(model_path.read_text(encoding="utf-8"))
    model["project_id"] = "casa_california_remodelacion_edicion_limpia"
    model["edit_revision"] = {
        "id": "REV-LIMPIEZA-01",
        "base_project": "../plano_california",
        "non_destructive": True,
        "summary": ["Portada copiada sin cambios para conservar el juego completo."],
    }
    model_path.write_text(json.dumps(model, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    for folder, settings in SHEETS.items():
        configure_ocg_sheet(folder, settings)
    configure_hydraulic_sheet("hidraulico_nivel_1", 1)
    configure_hydraulic_sheet("hidraulico_nivel_2", 2)
    configure_cover()
    configure_project()


if __name__ == "__main__":
    main()
