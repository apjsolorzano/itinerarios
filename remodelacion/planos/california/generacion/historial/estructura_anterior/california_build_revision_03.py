#!/usr/bin/env python3
"""Aplica REV-03: coherencia estructural entre niveles y paleta por disciplina."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent

LEVEL_2_REFERENCE_BOUNDS = [132.33, 127.305, 787.755, 641.497]
LEVEL_2_ROOM_REGION = [500.0, 470.0, 297.0, 172.0]
LEVEL_2_STAIR_CORRIDOR_MASKS = [
    [241.0, 315.0, 274.0, 18.0],
    [241.0, 278.0, 16.0, 56.0],
    [392.0, 315.0, 123.0, 108.0],
    [486.0, 315.0, 29.0, 326.0],
]

SHEET_BOUNDS = {
    "nivel_2": [132.33, 127.305, 787.755, 641.497],
    "acabados_nivel_2": [117.09, 131.205, 754.425, 630.186],
    "electrico_nivel_2": [137.76, 113.595, 794.895, 629.167],
}

ARCHITECTURE_SHEETS = ("nivel_1", "nivel_2")
FINISH_SHEETS = ("acabados_nivel_1", "acabados_nivel_2")
ELECTRICAL_SHEETS = ("electrico_nivel_1", "electrico_nivel_2")
HYDRAULIC_SHEETS = ("hidraulico_nivel_1", "hidraulico_nivel_2")

PALETTES = {
    "architecture": {"base": "#263238", "label": "grafito azulado"},
    "finishes": {"base": "#737b80", "accent": "#c2410c", "label": "terracota"},
    "electrical": {"base": "#737b80", "accent": "#7c3aed", "label": "violeta"},
    "hydraulic": {"accent": "#0000ff", "secondary": "#f8991e", "label": "azul y naranja"},
}


def transform_region(
    rectangle: list[float],
    source_bounds: list[float],
    target_bounds: list[float],
) -> list[float]:
    source_x0, source_y0, source_x1, source_y1 = source_bounds
    target_x0, target_y0, target_x1, target_y1 = target_bounds
    scale_x = (target_x1 - target_x0) / (source_x1 - source_x0)
    scale_y = (target_y1 - target_y0) / (source_y1 - source_y0)
    x, y, width, height = rectangle
    return [
        round(target_x0 + (x - source_x0) * scale_x, 3),
        round(target_y0 + (y - source_y0) * scale_y, 3),
        round(width * scale_x, 3),
        round(height * scale_y, 3),
    ]


def whiteout(operation_id: str, rectangle: list[float], description: str) -> dict:
    return {
        "id": operation_id,
        "type": "whiteout",
        "rect_pt": rectangle,
        "fill": "#ffffff",
        "visible": True,
        "description": description,
    }


def load_model(folder: str) -> tuple[Path, dict]:
    path = ROOT / folder / "california_model.json"
    return path, json.loads(path.read_text(encoding="utf-8"))


def prepare_model(folder: str, discipline: str) -> tuple[Path, dict]:
    path, model = load_model(folder)
    model["project_id"] = "casa_california_remodelacion_revision_03"
    model["sheet_id"] = model["sheet_id"].split("_revision_03", 1)[0] + "_revision_03"
    model["operations"] = [
        operation
        for operation in model.get("operations", [])
        if not operation.get("id", "").startswith("edit.rev03-")
    ]
    model["semantic_entities"] = [
        entity
        for entity in model.get("semantic_entities", [])
        if not entity.get("id", "").startswith("REV03-")
    ]
    model["output"]["svg_path"] = "california_rev03.svg"
    model["output"]["faithful_svg_path"] = None
    model["output"]["preview_png_path"] = None
    model["discipline_palette"] = PALETTES[discipline]
    return path, model


def add_level_2_consistency(model: dict, bounds: list[float]) -> None:
    room_region = transform_region(LEVEL_2_ROOM_REGION, LEVEL_2_REFERENCE_BOUNDS, bounds)
    model["operations"].append(
        whiteout(
            "edit.rev03-remove-level-2-rooms-5-6",
            room_region,
            "Retira Habitaciones V y VI de Nivel 2 porque no existe soporte construido bajo su huella.",
        )
    )
    for index, reference_mask in enumerate(LEVEL_2_STAIR_CORRIDOR_MASKS, start=1):
        mask = transform_region(reference_mask, LEVEL_2_REFERENCE_BOUNDS, bounds)
        model["operations"].append(
            whiteout(
                f"edit.rev03-remove-level-2-stair-corridor-{index:02d}",
                mask,
                "Retira escalera, pasillo y columnas aplazadas en Nivel 2.",
            )
        )
    model["semantic_entities"].extend(
        [
            {
                "id": "REV03-ROOMS-N2-05-06-REMOVE",
                "type": "area",
                "label": "Habitaciones V y VI de Nivel 2 eliminadas",
                "level": "Nivel 2",
                "visible": False,
                "properties": {"revision": "REV-03", "reason": "sin soporte en Nivel 1"},
            },
            {
                "id": "REV03-STAIR-CORRIDOR-N2-REMOVE",
                "type": "area",
                "label": "Escalera y pasillo de Nivel 2 eliminados",
                "level": "Nivel 2",
                "visible": False,
                "properties": {"revision": "REV-03", "phase": "aplazada"},
            },
        ]
    )


def add_revision_metadata(model: dict, discipline: str) -> None:
    model["edit_revision"] = {
        "id": "REV-03",
        "base_revision": "REV-02",
        "non_destructive": True,
        "svg_only": True,
        "summary": [
            "Habitaciones V y VI eliminadas en Nivel 2 para corresponder con los vacíos de Nivel 1.",
            "Escalera, pasillo y columnas aplazadas eliminadas en ambos niveles y disciplinas.",
            f"Paleta de {discipline} aplicada para distinguir la disciplina.",
            "Salida limitada a SVG; no se genera PDF.",
        ],
    }


def configure_architecture() -> None:
    for folder in ARCHITECTURE_SHEETS:
        path, model = prepare_model(folder, "architecture")
        model["color_profile"] = {
            "enabled": True,
            "replacements": {"#000000": PALETTES["architecture"]["base"]},
        }
        if folder == "nivel_2":
            add_level_2_consistency(model, SHEET_BOUNDS[folder])
        add_revision_metadata(model, "arquitectura")
        path.write_text(json.dumps(model, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def configure_finishes() -> None:
    for folder in FINISH_SHEETS:
        path, model = prepare_model(folder, "finishes")
        model["color_profile"] = {
            "enabled": True,
            "replacements": {"#000000": PALETTES["finishes"]["base"]},
        }
        symbol_layers = []
        for layer in model["source_layers"]:
            if layer["name"].casefold() == "simbologia":
                layer["visible"] = False
                symbol_layers.append(int(layer["ocg_xref"]))
        if symbol_layers:
            model["operations"].insert(
                0,
                {
                    "id": "edit.rev03-highlight-finishes",
                    "type": "append_source_layers_recolored",
                    "ocg_xrefs": symbol_layers,
                    "source_colors": ["#000000"],
                    "color": PALETTES["finishes"]["accent"],
                    "visible": True,
                    "description": "Destaca símbolos y especificaciones de acabados en terracota.",
                },
            )
        if folder == "acabados_nivel_2":
            add_level_2_consistency(model, SHEET_BOUNDS[folder])
        add_revision_metadata(model, "acabados")
        path.write_text(json.dumps(model, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def configure_electrical() -> None:
    electrical_layer_names = {"ie_il_bocas", "ie_to_bocas", "ie_il_cañería_losa"}
    for folder in ELECTRICAL_SHEETS:
        path, model = prepare_model(folder, "electrical")
        model["color_profile"] = {
            "enabled": True,
            "replacements": {"#000000": PALETTES["electrical"]["base"]},
        }
        electrical_layers = []
        for layer in model["source_layers"]:
            if layer["name"].casefold() in electrical_layer_names:
                layer["visible"] = False
                electrical_layers.append(int(layer["ocg_xref"]))
        if electrical_layers:
            model["operations"].insert(
                0,
                {
                    "id": "edit.rev03-highlight-electrical",
                    "type": "append_source_layers_recolored",
                    "ocg_xrefs": electrical_layers,
                    "source_colors": ["#000000"],
                    "color": PALETTES["electrical"]["accent"],
                    "visible": True,
                    "description": "Destaca luminarias, tomas y canalizaciones eléctricas en violeta.",
                },
            )
        if folder == "electrico_nivel_2":
            add_level_2_consistency(model, SHEET_BOUNDS[folder])
        add_revision_metadata(model, "electricidad")
        path.write_text(json.dumps(model, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def configure_hydraulic() -> None:
    for folder in HYDRAULIC_SHEETS:
        path, model = prepare_model(folder, "hydraulic")
        model["color_profile"] = {"enabled": False, "replacements": {}}
        if folder == "hidraulico_nivel_2":
            model["operations"].append(
                whiteout(
                    "edit.rev03-remove-level-2-rooms-5-6",
                    [500.0, 454.0, 295.0, 178.0],
                    "Retira Habitaciones V y VI y sus ramales hidráulicos en Nivel 2.",
                )
            )
            for index, mask in enumerate(
                [
                    [240.0, 312.0, 282.0, 20.0],
                    [240.0, 274.0, 20.0, 59.0],
                    [388.0, 312.0, 134.0, 116.0],
                    [486.0, 312.0, 36.0, 320.0],
                ],
                start=1,
            ):
                model["operations"].append(
                    whiteout(
                        f"edit.rev03-remove-level-2-stair-corridor-{index:02d}",
                        mask,
                        "Retira escalera, pasillo y columnas aplazadas en el plano hidráulico de Nivel 2.",
                    )
                )
            model["semantic_entities"].extend(
                [
                    {
                        "id": "REV03-ROOMS-N2-05-06-REMOVE",
                        "type": "area",
                        "label": "Habitaciones V y VI de Nivel 2 eliminadas",
                        "level": "Nivel 2",
                        "visible": False,
                    },
                    {
                        "id": "REV03-STAIR-CORRIDOR-N2-REMOVE",
                        "type": "area",
                        "label": "Escalera y pasillo de Nivel 2 eliminados",
                        "level": "Nivel 2",
                        "visible": False,
                    },
                ]
            )
        add_revision_metadata(model, "hidráulica")
        path.write_text(json.dumps(model, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def configure_cover() -> None:
    path, model = prepare_model("portada", "architecture")
    model["color_profile"] = {
        "enabled": True,
        "replacements": {"#000000": PALETTES["architecture"]["base"]},
    }
    model["edit_revision"] = {
        "id": "REV-03",
        "base_revision": "REV-02",
        "non_destructive": True,
        "svg_only": True,
        "summary": ["Portada SVG coordinada con la revisión actual."],
    }
    path.write_text(json.dumps(model, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def configure_project() -> None:
    path = ROOT / "california_project.json"
    project = json.loads(path.read_text(encoding="utf-8"))
    project["project_id"] = "casa_california_remodelacion_revision_03"
    project["title"] = "Casa California - REV-03 coordinada, salida SVG"
    project["base_project"] = "REV-02"
    project["revision"] = {
        "id": "REV-03",
        "preserves_base_files": True,
        "output_format": "SVG solamente",
        "changes": [
            "Habitaciones V y VI retiradas de Nivel 2.",
            "Escalera y pasillo retirados de todas las hojas de ambos niveles.",
            "Arquitectura en grafito, acabados en terracota, electricidad en violeta e hidráulica en azul/naranja.",
        ],
    }
    for sheet in project["sheets"]:
        sheet["status"] = "pending_rev03_svg"
        sheet.pop("validation", None)
        sheet.pop("output_svg", None)
    path.write_text(json.dumps(project, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    configure_architecture()
    configure_finishes()
    configure_electrical()
    configure_hydraulic()
    configure_cover()
    configure_project()


if __name__ == "__main__":
    main()
