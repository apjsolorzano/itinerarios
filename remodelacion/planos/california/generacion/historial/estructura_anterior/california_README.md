# Casa California - REV-04 constructiva en SVG

Esta carpeta contiene `REV-04`, una revisión independiente y regenerable. Los SVG de las revisiones anteriores permanecen intactos.

## Flujo vigente: SVG-first

- La entrada predeterminada es `california_svg_project.json`.
- Cada hoja usa `california_master.svg` como estado vigente y `california_reference.svg` como referencia vectorial.
- Los cambios nuevos se guardan en `california_svg_model.json`.
- El flujo normal no abre ni procesa el PDF.
- El regenerador predeterminado es `california_render_all_fast.py`, construido únicamente sobre SVG y JSON.

Consulte `california_SVG_WORKFLOW.md` para el procedimiento completo.

## Política de salida

- El formato de trabajo y entrega predeterminado es SVG.
- No se genera un PDF salvo que el usuario lo solicite expresamente.
- El archivo actual de cada hoja es `california_rev04.svg`.

## Cambios acumulados

- Se retiraron camas, cocinas, vehículos, mesas, sillas y demás mobiliario principal.
- Se conservaron los baños completos, incluidos lavamanos e inodoros.
- Se eliminó la piscina.
- En Nivel 1 se eliminaron Habitaciones I y II, conservando el portón, el perímetro y el cierre de Habitación III.
- En `REV-02` se retiraron la escalera del estacionamiento, el pasillo aplazado, sus líneas de cierre y las columnas asociadas.
- En `REV-03` se retiraron también Habitaciones V y VI de Nivel 2, porque su huella quedó sin soporte en Nivel 1.
- Escalera, pasillo y columnas aplazadas quedaron retiradas de arquitectura, acabados, electricidad e hidráulica de ambos niveles.
- En `REV-04` los vacíos empiezan después del espesor de los muros conservados, de modo que Habitación III en Nivel 1 y Habitación VII en Nivel 2 terminan en cerramientos continuos.
- La piscina y su contorno quedaron completamente retirados también en la hoja hidráulica del Nivel 2.
- Se aplicó una paleta diferenciada: arquitectura en grafito, acabados en terracota, electricidad en violeta e hidráulica en azul/naranja.

En la hoja hidráulica se recuperan las redes azules y los símbolos naranjas después de aplicar la limpieza arquitectónica, para conservar la información de instalaciones visible.

## Archivos por hoja

- `california_model.json`: instrucciones, operaciones y entidades semánticas.
- `california_regenerated.svg`: SVG final editable.
- `california_rev04.svg`: SVG coordinado vigente.
- `california_regenerated-faithful.svg`: extracción vectorial previa a las operaciones.
- `california_preview.png`: vista de control.
- `validation/california_report.json`: procedencia, hashes y métricas de regeneración.

El juego contiene nueve hojas: portada, arquitectura de niveles 1 y 2, acabados de niveles 1 y 2, electricidad de niveles 1 y 2 e hidráulica de niveles 1 y 2.

## Regeneración

Desde esta carpeta:

Flujo vigente, rápido y sin PDF:

```bash
python california_render_all_fast.py
```

Flujo histórico anterior:

```bash
python -m pip install -r california_requirements.txt
python california_build_clean_edition.py
python california_build_revision_02.py
python california_build_revision_03.py
python california_build_revision_04.py
python california_render_all.py
```

El flujo histórico anterior permanece solo para trazabilidad. No debe usarse en cambios nuevos salvo autorización expresa.

El regenerador verifica el SHA-256 del PDF fuente antes de producir resultados. Las operaciones de `REV-02` usan identificadores `edit.rev02-*` y se pueden ajustar o desactivar sin modificar el PDF fuente.

## Entidades para edición futura

- `REV02-STAIR-N1-REMOVE`
- `REV02-CORRIDOR-N1-REMOVE`
- `EDIT-BATHROOM-FIXTURES-KEEP`
- `EDIT-POOL-REMOVE`
- `N1-ROOMS-01-02-REMOVE`
