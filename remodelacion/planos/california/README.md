# Planos de Casa California

Esta carpeta separa los planos listos para consultar en obra de los archivos técnicos usados para regenerarlos y mantener su historial.

## Acceso rápido

- **Para ver o entregar planos:** abra [`planos_finales/`](planos_finales/).
- **Para editar o regenerar:** abra [`generacion/`](generacion/).
- **Para verlos en el sitio:** abra [`california.html`](../../california.html#planos).

## Estructura

```text
california/
├── README.md                 ← esta guía
├── planos_finales/           ← los nueve SVG vigentes para consulta y obra
│   ├── nivel_1/
│   ├── nivel_2/
│   └── informacion_general/
└── generacion/               ← modelos, herramientas e historial técnico
    ├── flujo_svg_actual/
    └── historial/
```

## Regla principal

Los archivos de `planos_finales/` son los únicos entregables vigentes. Sus nombres describen el nivel y la especialidad y no incluyen números de revisión.

El contenido de `generacion/` no debe entregarse a la cuadrilla ni utilizarse como plano de obra. Allí se conservan los SVG maestros, las instrucciones JSON, las herramientas y las revisiones anteriores.

El flujo normal usa SVG y JSON. Los PDF antiguos permanecen únicamente como archivo histórico y no se consultan ni se regeneran salvo solicitud expresa.

