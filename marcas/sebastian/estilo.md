# Estilo de edición: marca personal de Sebastián

Reglas aprendidas de sus correcciones. Base: `CRITERIO.md`, `estilos/heras.md`, `estilos/dynamic.md`.

## Prueba-01 (dynamic, 29-10-2026): lo que aprobó
- **Edición sonora "de tráiler"**: le encantó. Golpe en el primer cuadro, música de tensión en el gancho, blanco y negro
  + suspenso en la pregunta, golpe y música con ritmo en la respuesta, riser con el contador, medio segundo de silencio
  antes de la llamada a la acción y música nueva. Efectos que copian lo que pasa en pantalla (pop, ding, whoosh, mensaje).
- La captura real del perfil (23 seguidores) con el número marcado en amarillo: le gustó el recorte y la animación.

## Correcciones (reglas)
1. **Sin huecos al empezar una toma.** Nada de aire muerto antes de que hable; si no es una pausa de tensión buscada, se
   corta. En cuartos con ruido el detector de voz no puede bajar del umbral normal (`cortar.py`). En dynamic: pausas
   cortas (`tomas.json` → "pausas" / "cola"), pero sin cortar sílabas: huecos menores a ~0,17 s dentro de la frase se dejan.
2. **Subtítulos compuestos** (`marca.json` → `"modo": "compuesto"`): la palabra clave manda, ENORME (hasta 158 px),
   MAYÚSCULA itálica amarilla #FCF304, partida en dos líneas si hace falta ("QUEMANDO|TU TIEMPO"). El apoyo va chico
   y blanco encima: pegado al borde izquierdo de la clave si es corto, centrado si es largo. Sin signos.
3. **Tarjetas como las de dynamic vd5**: vidrio oscuro con borde punteado blanco que brilla, compactas (~600 px de ancho)
   y ARRIBA de la cabeza. **Nunca tapar la cara**: como mucho el pelo o la frente, los ojos siempre libres.
   No le gustaron las tarjetas grandes y planas (clase gratis y contador de la primera versión).
4. **Voz limpia siempre** (antes usaba Adobe Podcast): `nucleo/limpiar_voz.py` separa la voz con Demucs y quita el
   ruido del cuarto sin cambiar el tono. Va después de montar la base.
5. **Máximo 3 palabras por línea de subtítulo** (se lee de un vistazo). Una sola palabra si es larga o se entiende sola.
   Texto de apoyo más grande (64 px con clave, 78 px solo). **La palabra clave siempre en UNA línea**: en dos líneas
   "se ve raro y feo". Si no cabe, se achica; nunca se parte.
6. **El corte mide sobre la voz aislada** (`tomas.json` → `"voz_separada": true`, `"unir": 0.17`): en tomas grabadas
   lejos del celular la voz queda al nivel del ruido y quedaba medio segundo muerto al empezar ("y te preguntarás").
   Whisper también inventa palabras sobre una respiración: el inicio se busca donde hay voz de verdad.
7. **Captura del perfil**: como en la v1 (borde blanco limpio, sin punteado), más chica y **abajo, sobre el pecho**;
   mientras se ve, los subtítulos suben arriba de la cabeza (`y_por_tramo`). Ese plano se abre (`"zoom": 1.0`) para
   que la cara no quede tapada.
8. **Tipografía de subtítulos**: clave en **Inter Black Italic** amarilla; apoyo en **Inter Bold** blanca (no Regular).
   **Interlineado apretado**: el apoyo casi pegado a la clave.
9. **Posición fija bajo la barbilla** (`trabajo/encuadre.json`): la persona del mismo tamaño y a la misma altura en
   todos los planos y el subtítulo justo debajo de la barbilla. Títulos compuestos: el apoyo se acomoda alrededor de
   la clave (en línea si cabe, si no arriba); si el fondo no deja leer, la clave va en caja negra con letra amarilla.
10. **Nunca escalar de más ni tapar la cara** (corrección v6): zoom máximo 15 % (`encuadre.json` → `zoom_max: 1.15`,
    aunque la cara quede algo corrida). Lo que va a la altura de la cara se resuelve como dynamic vd2/vd4
    (`nucleo/componer_dynamic.py` + `motion/src/sebastian/Prueba01b.tsx`):
    - **Panel** que baja desde arriba (860 px, fondo oscuro) y el video baja 420 px: la cara queda abajo y el
      subtítulo va en la costura.
    - **Pantalla completa** de fondo sólido que sube desde abajo y sale hacia arriba, con la voz sonando.
    - **Tarjeta de capítulo amarilla** (como "Paso 1 · Proyecto" de vd2) para un número o idea corta.
    - Whoosh en cada entrada y salida.
11. **Voz**: si Sebas la pasa por Adobe Podcast, se le manda la voz cortada en WAV (mismo largo que el video) y la
    devuelve igual de larga: se reemplaza sin tocar la sincronía.
12. **Estilo dynamic = vd2** (lo eligió Sebas, 29-10): el video NO se tapa, se **difumina** arriba (desenfoque +
    tinte ahumado con degradado que termina sobre la cabeza) y ahí flotan título y tarjeta de vidrio. Entradas
    suaves (fundido + desenfoque + 16 px de subida), pantallas completas por **fundido** (no cortinas), tarjeta de
    capítulo amarilla. Versión oscura: vidrio ahumado, blanco y amarillo #FCF304. Grabar con **un tercio de pantalla
    libre sobre la cabeza**; si no hay aire, el video baja y se rellena arriba con el mismo fondo desenfocado.
13. **Storyboard visual antes de cada render** (cuadros reales con el estilo aplicado). El render sale aprobado.
14. **Sin escalar la toma** (corrección v8): Sebas no graba tan cerca como para necesitar zoom. Base a `zoom_max: 1.0`
    (la toma tal cual) y golpes de zoom muy suaves (≤ 5 %). Escalar de más lo deja apretado y sin aire.
15. **Nada repetido**: un título o gráfico no dice lo mismo que el subtítulo que está en pantalla. Si un gráfico ya
    lo dice, el subtítulo se va antes (`"hasta_s"` en el bloque) o el título se quita.
16. **Toda clave amarilla lleva su caja negra**, en TODO el video, **recta, sin esquinas redondeadas**
    (`marca.json` → `caja_siempre: true`, `caja_radio: 0`). En pantallas claras la clave sigue amarilla en su caja.
17. **Nada de "ícono suelto con título encima"**: un ícono o emoji solo va **a un lado de Sebas y detrás de él**
    (capa `detras` de Remotion + recorte `persona.mov` de `nucleo/silueta.py`, en `componer_difuminado.py --detras`).
    Un motion graphic de verdad (algo que pasa, p. ej. el logo de Instagram cortándose) sí puede ir en grande.
    El difuminado arriba con título queda para gráficos con contenido (perfil, comentario, contador).
18. **Un ícono solo vale si se ve.** Si a un lado de Sebas no hay espacio (la cara llena el ancho), el ícono no va
    (el reloj de prueba-01 se quitó: se tapaba casi entero).
19. **Listas cortas ("3 cosas")**: círculos 1 · 2 · 3 oscuros con borde blanco y resplandor, el último en amarillo,
    entrando uno tras otro con rebote y un pop cada uno (le gustan más que una tarjeta de capítulo a pantalla completa).
20. **Pantalla completa de una oferta (clase gratis)**: fondo naranja de marca que entra y sale por **iris** (círculo
    con aro crema) y whoosh. La miniatura de la clase es propia y **en pausa** (título simple, botón de play, barra al
    inicio), nunca la foto de perfil.
21. **Corrección de color suave, toma por toma** (`nucleo/color.py`): balance de blancos a medio camino de neutro,
    negros un poco más firmes, S de contraste ±3 % y saturación +8..18 %. Que se note (la primera prueba con +4..14 %
    casi no se veía) pero sin exagerar. **Nunca más brillante que el original** ("se ve muy brillante"): no se estiran
    los blancos y los medios bajan hasta que el brillo medio quede en ~97 % del original. Va antes de silueta.py.
    **La piel no se toca** ("parezco un indigente"): la saturación sube solo fuera de la piel (verdes, cianes, azules),
    los rojos bajan 5 % y el balance de blancos nunca quita verde ni agrega rojo (eso ponía la frente roja y naranja).
