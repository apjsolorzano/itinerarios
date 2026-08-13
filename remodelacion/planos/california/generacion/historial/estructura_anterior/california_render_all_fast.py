#!/usr/bin/env python3
"""Regenera todas las hojas desde SVG maestros, sin dependencias ni acceso a PDF."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from california_render_svg_fast import render


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--project",
        type=Path,
        default=Path(__file__).with_name("california_svg_project.json"),
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        help="Directorio alternativo para una regeneración de prueba",
    )
    arguments = parser.parse_args()
    project_path = arguments.project.resolve()
    project_root = project_path.parent
    project = json.loads(project_path.read_text(encoding="utf-8"))
    if project.get("reference_policy") != "svg_only":
        raise ValueError("El proyecto no exige referencia exclusiva SVG")
    for sheet in project["sheets"]:
        model_path = (project_root / sheet["model"]).resolve()
        output_override = None
        if arguments.output_root:
            output_override = str(
                (arguments.output_root.resolve() / sheet["folder"] / "california_working.svg")
            )
        output = render(model_path, output_override)
        print(f"{sheet['id']}: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
