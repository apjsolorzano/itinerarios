#!/usr/bin/env python3
"""Fija referencias SVG, maestros REV-04 y manifiestos SVG-first para futuras revisiones."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parent
FOLDERS = (
    "portada",
    "nivel_1",
    "nivel_2",
    "acabados_nivel_1",
    "acabados_nivel_2",
    "electrico_nivel_1",
    "electrico_nivel_2",
    "hidraulico_nivel_1",
    "hidraulico_nivel_2",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def copy_once(source: Path, target: Path, refresh: bool) -> None:
    if refresh or not target.exists():
        shutil.copy2(source, target)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Actualiza las copias canónicas a partir de los SVG vigentes",
    )
    arguments = parser.parse_args()
    legacy_project = json.loads((ROOT / "california_project.json").read_text(encoding="utf-8"))
    project_sheets: list[dict] = []

    for folder in FOLDERS:
        directory = ROOT / folder
        reference = directory / "california_reference.svg"
        master = directory / "california_master.svg"
        copy_once(directory / "california_regenerated-faithful.svg", reference, arguments.refresh)
        copy_once(directory / "california_rev04.svg", master, arguments.refresh)

        legacy_model_path = directory / "california_model.json"
        legacy_model = json.loads(legacy_model_path.read_text(encoding="utf-8"))
        model = {
            "$schema": "../california_svg_plan.schema.json",
            "format": "plan-editor/svg-v1",
            "project_id": "casa_california_svg_first",
            "sheet_id": legacy_model["sheet_id"],
            "title": legacy_model.get("title", folder.replace("_", " ").title()),
            "discipline": legacy_model.get("discipline", "general"),
            "source": {
                "kind": "svg",
                "master_svg_path": "california_master.svg",
                "master_svg_sha256": sha256(master),
                "reference_svg_path": "california_reference.svg",
                "reference_svg_sha256": sha256(reference),
                "baseline_revision": "REV-04",
                "reference_policy": "svg_only",
                "normal_workflow_uses_pdf": False,
            },
            "canvas": legacy_model["canvas"],
            "semantic_entities": legacy_model.get("semantic_entities", []),
            "operations": [],
            "baked_history": {
                "legacy_model": "california_model.json",
                "revision": legacy_model.get("edit_revision", {}).get("id", "REV-04"),
                "operation_index": [
                    {
                        "id": operation.get("id"),
                        "type": operation.get("type"),
                        "description": operation.get("description"),
                    }
                    for operation in legacy_model.get("operations", [])
                ],
            },
            "workflow": {
                "editing_rule": "Añadir únicamente operaciones incrementales sobre california_master.svg.",
                "publication_rule": "Publicar una nueva revisión SVG y promoverla a maestro solo después de validarla.",
                "forbidden_normal_inputs": ["PDF"],
                "allowed_outputs": ["SVG"],
            },
            "output": {"svg_path": "california_working.svg"},
        }
        (directory / "california_svg_model.json").write_text(
            json.dumps(model, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        legacy_sheet = next(
            sheet for sheet in legacy_project["sheets"] if Path(sheet["model"]).parts[0] == folder
        )
        project_sheets.append(
            {
                "id": legacy_sheet["id"],
                "folder": folder,
                "title": legacy_sheet["title"],
                "discipline": legacy_sheet["discipline"],
                "sheet_code": legacy_sheet["sheet_code"],
                "model": f"{folder}/california_svg_model.json",
                "reference_svg": f"{folder}/california_reference.svg",
                "master_svg": f"{folder}/california_master.svg",
                "published_svg": f"{folder}/california_rev04.svg",
            }
        )

    svg_project = {
        "format": "plan-editor-svg-project/v1",
        "project_id": "casa_california_svg_first",
        "title": "Casa California - flujo SVG-first",
        "baseline_revision": "REV-04",
        "reference_policy": "svg_only",
        "normal_workflow_uses_pdf": False,
        "default_output_format": "SVG",
        "sheets": project_sheets,
    }
    (ROOT / "california_svg_project.json").write_text(
        json.dumps(svg_project, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Flujo SVG-first preparado para {len(project_sheets)} hojas")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
