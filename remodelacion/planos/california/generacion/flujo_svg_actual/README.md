# Flujo SVG actual

Este es el punto de entrada técnico para editar y regenerar las nueve hojas coordinadas sin consultar el PDF.

## Archivos principales

- `proyecto.json` — índice de las nueve hojas y sus rutas.
- `modelos/` — un directorio por nivel y especialidad.
  - `maestro.svg` — estado aprobado que sirve de base.
  - `referencia.svg` — geometría vectorial anterior para consulta.
  - `instrucciones.json` — operaciones incrementales de la siguiente modificación.
- `herramientas/` — regeneradores SVG.
- `salidas_de_trabajo/` — borradores generados para revisión; nunca son entregables automáticos.

## Regenerar las nueve hojas

Ejecute desde esta carpeta:

```bash
python3 herramientas/renderizar_todos.py
```

El proceso verifica el hash de cada maestro, aplica las operaciones JSON y escribe solamente SVG dentro de `salidas_de_trabajo/`.

## Publicación

1. Añada operaciones a los archivos `instrucciones.json`.
2. Regenere las nueve hojas.
3. Revise continuidad constructiva entre arquitectura, acabados, electricidad e hidráulica.
4. Después de la aprobación, archive la nueva revisión y actualice las copias descriptivas de `../../planos_finales/`.
5. Actualice los enlaces del sitio únicamente si cambia un nombre de archivo.

No sobrescriba `maestro.svg` durante una prueba y no produzca PDF salvo solicitud expresa.
