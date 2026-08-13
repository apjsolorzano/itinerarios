# Registro de revisiones

## FLUJO-SVG-01

Estado: adoptado como flujo predeterminado para cambios posteriores a REV-04.

- Nueve referencias vectoriales y nueve maestros REV-04 fijados por SHA-256.
- Nuevos manifiestos `california_svg_model.json` sin rutas ni dependencias PDF.
- Regenerador puro SVG/JSON comprobado con igualdad byte por byte en las nueve hojas.
- PDF relegado a archivo histórico y excluido del flujo normal.

## REV-04

Estado: SVG coordinados, cerrados constructivamente y revisados visualmente.

Cambios:

- Los vacíos de Habitaciones I y II en Nivel 1 y V y VI en Nivel 2 empiezan después del espesor completo del muro que ahora funciona como fachada.
- Habitación III en Nivel 1 y Habitación VII en Nivel 2 conservan cerramientos continuos y encuentros laterales completos.
- Se coordinó el mismo perímetro en arquitectura, acabados, electricidad e hidráulica.
- Se eliminó el contorno residual de piscina y los ramales/aparatos de los cuartos retirados en la hoja hidráulica del Nivel 2.
- La salida continúa limitada a SVG; no se genera PDF salvo solicitud expresa.

## REV-03

Estado: SVG coordinados y revisados visualmente.

Cambios:

- Retiro de Habitaciones V y VI del Nivel 2 por falta de soporte en Nivel 1.
- Retiro de escalera, pasillo y columnas asociadas en ambos niveles y todas las disciplinas.
- Arquitectura en grafito, acabados en terracota, electricidad en violeta e hidráulica en azul/naranja.
- Salida de trabajo limitada a SVG; no se genera PDF salvo solicitud expresa.

## REV-02

Estado: validación visual final.

Cambios:

- Retiro temporal de la escalera del estacionamiento en Nivel 1.
- Retiro del pasillo aplazado, sus líneas de cierre y columnas asociadas.
- Vehículos permanecen retirados conforme a `REV-LIMPIEZA-01`.
- Coordinación del cambio en arquitectura, acabados, electricidad e hidráulica de Nivel 1.

## REV-LIMPIEZA-01

- Limpieza general de mobiliario y equipamiento no sanitario.
- Conservación de baños completos, incluidos lavamanos e inodoros.
- Eliminación de piscina.
- Eliminación de Habitaciones I y II de Nivel 1.
- Conservación del muro de Habitación III, perímetro exterior y portón.

Procedencia:

- PDF fuente: `source/california_planos_casa_remodelacion.pdf`
- SHA-256: `e4f69232fb5bfaa51469b0355bb3247e479c4645e26ec3dfeb039616d24bf6f4`

Los cambios permanecen definidos como operaciones no destructivas dentro de los modelos JSON.
