#!/usr/bin/env python3
"""Regenera todas las plantas registradas en california_project.json."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from california_render_svg import render


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=Path(__file__).with_name("california_project.json"))
    parser.add_argument("--source", help="Ruta alternativa al PDF fuente")
    parser.add_argument("--validate", action="store_true", help="Regenera también los archivos de comparación")
    arguments = parser.parse_args()

    project_path = arguments.project.resolve()
    project_root = project_path.parent
    project = json.loads(project_path.read_text(encoding="utf-8"))

    for sheet in project["sheets"]:
        model_path = (project_root / sheet["model"]).resolve()
        output = render(model_path, arguments.source, None, arguments.validate)
        print(f"{sheet['id']}: {output}")
        sheet["status"] = "svg_ready"
        sheet["output_svg"] = str(output.relative_to(project_root))
        if arguments.validate:
            report_path = model_path.parent / "validation" / "california_report.json"
            report = json.loads(report_path.read_text(encoding="utf-8"))
            sheet["status"] = "validated"
            sheet["validation"] = {
                "source_and_faithful_svg_byte_identical": report[
                    "source_and_faithful_svg_byte_identical"
                ],
                "poppler_ink_ratio": report[
                    "poppler_reference_vs_profiled_svg_ink"
                ]["candidate_to_reference_ink_ratio"],
                "enhanced_hairline_count": report["enhanced_hairline_count"],
            }
    project_path.write_text(
        json.dumps(project, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
