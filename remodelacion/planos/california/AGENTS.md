# Flujo obligatorio para los planos de Casa California

- Use `generacion/flujo_svg_actual/proyecto.json` y los archivos `modelos/*/instrucciones.json` como punto de entrada.
- Use `maestro.svg` como fuente del estado vigente y `referencia.svg` para consultar geometría anterior.
- No abra, lea, renderice ni convierta los PDF del historial durante el flujo normal de edición.
- Genere y entregue únicamente SVG salvo que el usuario solicite expresamente otro formato.
- Registre cada cambio como una operación incremental dentro de `instrucciones.json`.
- No sobrescriba `maestro.svg`. Regenere primero en `salidas_de_trabajo/`, valide y promueva el resultado solo después de la aprobación del usuario.
- Mantenga coordinadas las nueve hojas y verifique continuidad constructiva entre arquitectura, acabados, electricidad e hidráulica.
- Los entregables visibles y los enlaces del sitio deben apuntar exclusivamente a `planos_finales/`.
- El contenido de `generacion/historial/` es solo trazabilidad y no debe usarse como fuente vigente.

Comando normal, desde `generacion/flujo_svg_actual/`:

```bash
python3 herramientas/renderizar_todos.py
```
