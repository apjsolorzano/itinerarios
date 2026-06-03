# Itinerary HTML Style Guide

## 1. Principios generales

- Cada itinerario debe basarse siempre en el archivo `instrucciones-ai/itinerario-plantilla.html`.
- El sitio debe ser rapido, liviano y facil de leer en movil.
- El contenido debe cargarse de arriba hacia abajo de forma progresiva.
- Priorizar claridad, utilidad practica y una experiencia visual premium.
- No generar contenido generico. Cada recomendacion debe sentirse especifica al destino, fecha, clima, horario y tipo de viaje.
- Si un dato no esta confirmado, indicarlo de forma prudente o evitar afirmarlo como definitivo.
- El archivo final debe funcionar como HTML estatico en GitHub Pages, sin backend.

## 2. Estructura obligatoria

Cada itinerario debe incluir, como minimo:

- Hero con destino, fechas, tipo de viaje y resumen.
- Resumen ejecutivo del viaje.
- Ruta general del viaje.
- Informacion de vuelos, traslados o transporte principal, si aplica.
- Itinerario dia por dia.
- Actividades organizadas por horario o bloque del dia.
- Restaurantes, cafes o experiencias gastronomicas recomendadas.
- Presupuesto estimado o rangos de gasto.
- Consejos practicos.
- Recomendaciones de vestimenta o equipaje, si aplica.
- Footer con fecha de ultima actualizacion.

## 3. Tono editorial

- Usar espanol claro, natural y directo.
- Mantener un estilo premium, practico y curado.
- Evitar sonar generico, turistico o excesivamente promocional.
- Dar recomendaciones accionables.
- Explicar por que una actividad, restaurante o ruta tiene sentido dentro del plan.
- Priorizar utilidad real sobre texto decorativo.
- Evitar frases vacias como "una experiencia inolvidable" salvo que esten acompanadas de detalles concretos.

## 4. Diseno visual

- El diseno debe ser mobile first.
- Usar CSS embebido salvo que el usuario indique lo contrario.
- No usar dependencias externas salvo que el usuario lo autorice.
- No usar JavaScript innecesario.
- Mantener jerarquia visual clara entre:
  - titulo principal
  - resumen
  - secciones
  - dias
  - actividades
  - notas secundarias
- Los botones, chips y enlaces deben verse sutiles, elegantes y no invasivos.
- Evitar saturar la pagina con demasiados elementos visuales compitiendo entre si.
- Mantener consistencia visual con `instrucciones-ai/itinerario-plantilla.html`.

## 5. Diseno movil y uso eficiente del espacio

- Maximizar el uso del espacio disponible en pantalla movil.
- Evitar bordes muertos, margenes excesivos o espacios vacios que obliguen al usuario a hacer scroll innecesario.
- Mantener una lectura limpia, comoda y rapida, sin saturar visualmente la pantalla.
- En movil, priorizar tarjetas compactas, secciones bien agrupadas y jerarquia visual clara.
- Reducir paddings laterales en pantallas pequenas, manteniendo suficiente aire visual para que el contenido no se sienta apretado.
- Las secciones deben sentirse densas en informacion util, pero no cargadas.
- Evitar bloques demasiado altos si el contenido puede resolverse con una estructura mas compacta.
- El contenido principal debe ser visible rapidamente, especialmente:
  - titulo del dia
  - zona
  - horario
  - actividad principal
  - botones de ubicacion
  - recomendaciones gastronomicas
- En movil, los botones secundarios deben ser compactos y faciles de tocar.
- Usar tamanos de fuente legibles, pero evitar titulos o espacios que ocupen demasiada altura innecesariamente.
- La experiencia movil debe priorizar consulta rapida durante el viaje.

## 6. Performance y carga

- El HTML debe ser liviano y rapido de cargar.
- El sitio debe cargar de arriba hacia abajo todo el contenido progresivamente.
- Las imagenes deben cargarse de forma progresiva y en orden logico de arriba hacia abajo.
- Usar `loading="lazy"` en imagenes que no esten en el primer viewport.
- Usar `decoding="async"` en imagenes cuando aplique.
- Definir `width` y `height` en imagenes cuando sea posible para reducir layout shifts.
- Evitar imagenes excesivamente pesadas.
- Evitar scripts externos, fuentes externas o librerias innecesarias.
- No usar videos embebidos salvo que el usuario lo pida explicitamente.
- En movil, evitar layouts que generen grandes espacios verticales vacios o cards excesivamente altas.

## 7. Imagenes

- Las imagenes deben ser realistas y coherentes con el lugar, experiencia, comida o tema especifico.
- Antes de usar una imagen, validar que corresponde al lugar o elemento al que hace referencia.
- Validar que la imagen se apegue al momento del dia o clima descrito.
- No usar una imagen de dia si la actividad ocurre de noche.
- No usar una imagen soleada si el plan describe nieve, lluvia, invierno o condiciones frias, salvo que se indique como imagen referencial.
- Cada imagen debe tener un atributo `alt` descriptivo y util.
- Las imagenes deben aportar valor real al itinerario, no ser decorativas sin proposito.
- Si no se puede validar una imagen adecuada, es preferible omitirla o usar un bloque visual sin imagen antes que usar una imagen incorrecta.

## 8. Navegacion interna y enlaces compartibles

- Cada seccion principal debe tener un `id` unico, legible y estable.
- Los IDs deben usar formato slug:
  - minusculas
  - sin espacios
  - sin tildes
  - palabras separadas con guiones
- Cada seccion importante debe poder compartirse mediante un enlace directo.
- Cuando aplique, incluir un boton sutil para copiar el enlace de la seccion.
- El boton de copiar enlace debe tener un nivel visual secundario y no distraer del contenido principal.
- Si se usa JavaScript para copiar enlaces, debe ser minimo, embebido y no depender de librerias externas.
- La pagina debe seguir siendo util aunque JavaScript no funcione.

## 9. Ubicacion, mapas y rutas

- Los lugares relevantes deben incluir botones sutiles hacia Google Maps.
- El boton de Google Maps debe estar bien ubicado, pero en un nivel visual secundario.
- Usar textos claros como:
  - Ver en Maps
  - Abrir ubicacion
  - Como llegar
- Los planes deben seguir una ruta logica para reducir fatiga por desplazamientos.
- Agrupar lugares, restaurantes y experiencias cercanas siempre que sea posible.
- Evitar rutas que obliguen a ir y regresar varias veces entre zonas lejanas.
- Preferir recorridos lineales, por zonas o por bloques geograficos.
- Indicar cuando un traslado pueda ser largo, complejo o requiera reserva previa.
- Considerar horarios, trafico, clima, energia del viajero y tiempos de descanso.

## 10. Gastronomia por dia

- Cada dia debe incluir una seccion gastronomica curada, alineada con la zona donde estara el viajero ese dia.
- La seccion gastronomica debe funcionar como una especie de carrusel horizontal o lista deslizable en movil.
- El carrusel debe mostrar entre 3 y 5 lugares recomendados por dia, salvo que el destino o la zona no lo justifique.
- Cada lugar gastronomico debe incluir:
  - nombre del lugar
  - zona o barrio
  - hora sugerida de visita
  - tipo de comida o experiencia
  - 1 a 3 platillos estrella o recomendaciones especificas
  - breve razon por la que encaja en el plan del dia
  - boton sutil hacia Google Maps
- Los platillos estrella deben ser concretos y utiles, no genericos.
- Cuando un lugar tenga varios platillos destacados, mostrarlos como chips o bullets compactos.
- Incluir indicadores textuales sutiles para:
  - zona
  - distancia o conveniencia respecto al plan del dia, si aplica
  - mejor momento para visitarlo: desayuno, almuerzo, cafe, cena, drinks o postre
- Las recomendaciones deben priorizar lugares cercanos a la ruta del dia.
- Evitar recomendar lugares que obliguen a desviarse demasiado, salvo que sean una experiencia gastronomica prioritaria.
- Si una recomendacion queda lejos de la ruta, indicarlo claramente.
- El boton de Google Maps debe tener nivel visual secundario y texto claro, por ejemplo:
  - Ver en Maps
  - Abrir ubicacion
  - Como llegar
- La seccion debe permitir comparar rapidamente varias opciones sin ocupar demasiado espacio vertical.
- En desktop puede mostrarse como grid o carrusel amplio; en movil debe priorizar carrusel horizontal o tarjetas compactas deslizadas.
- El carrusel debe funcionar sin dependencias externas.
- Si se usa JavaScript para mejorar la experiencia del carrusel, debe ser minimo y no depender de librerias.
- El carrusel debe seguir siendo usable aunque JavaScript no funcione, usando scroll horizontal nativo con CSS.
- Cada tarjeta gastronomica debe estar visualmente integrada con el diseno general del itinerario.
- No inventar horarios exactos, precios, reservas o platillos especificos si no estan verificados.
- Si los platillos estrella no estan confirmados, usar recomendaciones culinarias tipicas del lugar o indicar que son sugerencias a validar.

## 11. Presupuesto

- Incluir presupuesto estimado cuando el itinerario lo requiera o cuando agregue valor practico.
- Presentar rangos en lugar de cifras exactas cuando no haya certeza.
- Separar el presupuesto por categorias cuando sea util:
  - transporte
  - comida
  - actividades
  - entradas
  - tours
  - compras o extras
- Indicar claramente si el presupuesto excluye vuelos, hospedaje u otros gastos grandes.
- Evitar afirmar precios exactos sin verificacion actualizada.

## 12. Consejos practicos

- Incluir consejos concretos segun destino, temporada y tipo de viaje.
- Considerar:
  - clima
  - vestimenta
  - reservas
  - documentos
  - seguridad
  - conectividad
  - moneda y pagos
  - transporte local
  - horarios recomendados
  - nivel de esfuerzo fisico
- Priorizar consejos accionables sobre recomendaciones genericas.

## 13. Accesibilidad

- Usar estructura semantica correcta con `header`, `main`, `section`, `article` y `footer` cuando corresponda.
- Mantener buen contraste de texto.
- No depender unicamente del color para comunicar informacion importante.
- Usar textos descriptivos en enlaces y botones.
- Incluir atributos `aria-label` cuando un boton no sea suficientemente claro por si solo.
- Asegurar que el contenido sea legible en pantallas pequenas.

## 14. SEO basico y metadatos

- Cada HTML debe incluir un `<title>` especifico y descriptivo.
- Cada HTML debe incluir una meta description util.
- El titulo debe incluir destino, ano o duracion cuando aplique.
- Usar un solo `h1` principal.
- Mantener una jerarquia ordenada de headings: `h1`, `h2`, `h3`, `h4`.
- Evitar titulos duplicados entre paginas.
- La fecha de actualizacion debe aparecer en el footer.

## 15. URLs y nombres de archivo

- Los archivos HTML principales deben publicarse en la raiz del repositorio.
- No usar carpetas como `pages/` para los itinerarios principales.
- Los slugs deben usar:
  - minusculas
  - sin espacios
  - sin tildes
  - palabras separadas con guiones
  - extension `.html`
- Ejemplos validos:
  - `tokyo-2026.html`
  - `ushuaia-2026.html`
  - `roma-5-dias.html`
- Evitar nombres vagos como:
  - `viaje.html`
  - `itinerario.html`
  - `nuevo.html`

## 16. Consistencia con la plantilla

- Mantener la estructura visual definida en `instrucciones-ai/itinerario-plantilla.html`.
- Reutilizar clases, layout y patrones visuales existentes siempre que sea posible.
- No redisenar completamente el HTML salvo que el usuario lo pida explicitamente.
- Si se agregan nuevas secciones, deben integrarse visualmente con el estilo existente.
- Evitar duplicar estilos innecesarios si ya existen patrones en la plantilla.

## 17. Manejo de informacion incierta

- No inventar horarios, precios, direcciones, disponibilidad o politicas de reserva.
- Si un dato puede cambiar, escribirlo como recomendacion a verificar.
- Cuando sea necesario, usar frases como:
  - conviene verificar disponibilidad
  - precio estimado sujeto a cambios
  - revisar horarios antes de ir
- Priorizar precision sobre completitud artificial.

## 18. Reglas de contenido por dia

- Cada dia debe tener un tema claro.
- Cada dia debe tener una ruta logica.
- Cada actividad debe incluir:
  - horario o bloque aproximado
  - nombre de la actividad o lugar
  - descripcion breve
  - razon por la que encaja en el dia
  - enlace a ubicacion cuando aplique
- Incluir descansos o transiciones cuando el dia sea largo.
- Evitar sobrecargar el dia con demasiadas actividades.
- Considerar energia, tiempos de traslado y clima.

## 19. Footer

El footer debe incluir:

- Nombre o resumen del itinerario.
- Fecha de ultima actualizacion.
- Nota breve indicando que horarios, precios y disponibilidad pueden cambiar.
- Opcionalmente, enlace al inicio de la pagina.

## 20. Restricciones tecnicas

- No usar frameworks.
- No usar build tools.
- No usar dependencias externas salvo instruccion explicita del usuario.
- No usar tracking, analytics ni scripts de terceros salvo que el usuario lo pida.
- El archivo debe funcionar como HTML estatico en GitHub Pages.
- El HTML debe poder abrirse directamente desde la URL publica sin backend.

## 21. Prioridad de instrucciones

Cuando haya conflicto entre instrucciones, usar este orden de prioridad:

1. Instruccion especifica del usuario para ese itinerario.
2. Reglas operativas del Custom GPT.
3. `instrucciones-ai/instrucciones.md`.
4. `instrucciones-ai/itinerario-plantilla.html`.

Nunca se deben ignorar reglas de seguridad, publicacion, repositorio o manejo de secretos.
