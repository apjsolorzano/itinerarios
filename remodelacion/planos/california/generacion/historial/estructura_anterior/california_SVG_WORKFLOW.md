# Flujo SVG-first de Casa California

## Objetivo

Editar, regenerar y revisar los planos sin volver a extraer páginas del PDF. El PDF queda fuera del ciclo normal y solo se conserva como archivo histórico.

## Archivos canónicos por hoja

- `california_reference.svg`: referencia vectorial preservada de la regeneración anterior a REV-04.
- `california_master.svg`: estado vigente aprobado, actualmente REV-04.
- `california_svg_model.json`: instrucciones incrementales para la siguiente revisión.
- `california_model.json`: historial técnico del flujo anterior; ya no es la entrada predeterminada.

El proyecto coordinador es `california_svg_project.json`.

## Regeneración habitual

```bash
python california_render_all_fast.py
```

El regenerador:

1. Verifica el SHA-256 del SVG maestro.
2. Aplica únicamente las operaciones nuevas del JSON.
3. Escribe `california_working.svg`.
4. No importa librerías PDF, no abre el PDF y no genera archivos PDF.

Para una prueba fuera de las carpetas de publicación:

```bash
python california_render_all_fast.py --output-root /ruta/temporal
```

## Operaciones disponibles

- `whiteout`: vacía una región rectangular o poligonal.
- `draw_path`, `draw_rect`, `draw_line`, `draw_polyline`: construyen muros, cierres y geometría nueva.
- `append_svg`: incorpora un detalle vectorial externo.
- `hide_ids`: oculta elementos que ya tengan identificadores semánticos.
- `set_attributes`: cambia atributos de elementos identificados.
- `replace_color`: actualiza un color de trazo o relleno.

Cada retiro debe incluir, cuando corresponda, las operaciones de cierre que hagan que el plano siga siendo constructivamente coherente.

## Nueva revisión

1. Copiar los manifiestos SVG-first a la nueva revisión o añadir sus operaciones incrementales.
2. Regenerar las nueve hojas con `california_render_all_fast.py`.
3. Revisar visualmente arquitectura, acabados, electricidad e hidráulica.
4. Publicar archivos `california_revNN.svg` nuevos.
5. Después de la aprobación, promover esa revisión a `california_master.svg` y actualizar los hashes con `california_prepare_svg_workflow.py --refresh`.

No se debe consultar el PDF para comparar geometría ya disponible en `california_reference.svg` o `california_master.svg`.
