# Formato dynamic — estilo de Sebas (referencia principal)

Sacado cuadro por cuadro de su edición final de Sunny Shore (`sunny-shore_vd1.mp4`, 48,2 s, 23,976 fps, aprobada por el
cliente sin una sola corrección). Es EL estilo base del formato dynamic; puede tener variaciones, pero se parte de aquí.
La fuente sale de la marca (Sunny Shore: Inter). Medidas en 1080x1920.

## 1. Textos: cómo, dónde y por qué

**Posición.** Un solo lugar fijo para casi todo: el centro del cuadro, sobre el pecho (bloque centrado en x=540,
y≈900–1150). No sigue a la persona ni se mueve con la toma. Excepciones:
- el gancho: la primera frase va ARRIBA y grande (y≈420–540), encima del cielo/árbol;
- la llamada a la acción: sube arriba (y≈250–480);
- sobre los b-rolls el texto sigue en el mismo lugar, encima de la toma.

**Ritmo.** El texto va palabra por palabra con la voz. Cada bloque tiene 1 a 3 pisos que se van APILANDO a medida
que habla ("Nosotros" → "PODEMOS HACER" → "y hasta" → "100.000 $"). Cuando termina la idea, el bloque se va entero
y empieza el siguiente. Bloques de 0,3–1,5 s.

**Tamaño = importancia.** Cada bloque tiene jerarquía propia:
- conectores ("La compramos", "ni un", "de cash flow", "aquí abajo y me"): pequeños, Regular, ~40–65 px;
- la idea de la frase ("La compraron", "para remodelar", "Sin gastar", "y hasta"): Bold, ~75–90 px;
- el golpe (cifra o palabra fuerte: "$1", "100.000 $", "una casa", "dinero"): Bold/Black, ~110–150 px;
- el título del gancho ("Si sabes / cuánto dinero"): Bold Italic, ~110–120 px, el más grande de los textos de voz.

**Color = significado.**
- Blanco: lo que conecta.
- Amarillo: la palabra que lleva el sentido (lo que se gana, la acción, el centro de la pregunta: "deja dinero?",
  "una casa", "capitalizarte", "rápido", "más fácil", "para trabajar", "dinero", "Fix and Flip", "la remodelación").
- La primera pregunta del vecino va TODA en amarillo y en MAYÚSCULAS ("COMO ASÍ VECINO?"): marca la reacción.
- **Plata en escala de color según el monto**: 500 $ rojo/rosado (poco), 1.000 $ naranja, 60K/70K USD amarillo
  verdoso, 100.000 $ verde fuerte (mucho). El color cuenta si la cifra es buena o mala.
- Las cifras se escriben como número aunque se digan en palabras: "ni un solo dólar" → "ni un **$1**".

**Itálica** para lo que tiene velocidad o énfasis: "rápido", "dinero", "y hasta", "PODEMOS HACER", "la remodelación".
**Sin caja** en ningún texto de voz; solo resplandor oscuro difuso.
**Signos** (Sebas): las preguntas llevan SOLO el "?" del final, nunca el "¿" de apertura; el "$" va SIEMPRE.
Ningún otro signo (ni puntos, ni comas, ni ¡!). Esto reemplaza la regla 8 de CLAUDE.md en el formato dynamic.

**Animación de los textos.** Entran deslizando de lado con mucho desenfoque de movimiento (~4 cuadros, se ve como
una mancha de color que se asienta) y salen con desenfoque. Nada de escalar ni rebotar.

## 2. Imagen y cortes

- 18 planos, ~21 cortes por minuto. Se respeta el montaje del crudo y se le suman b-rolls.
- **Transición en cada cambio de toma de cámara** (2,2 / 7,7 / 11,0 / 31,2 s): destello blanco de luz
  (quema a blanco ~4 cuadros antes y después del corte) + sonido "transicion".
- **Entrada a la secuencia de b-rolls**: la toma nueva sube desde abajo empujando a la anterior (~7 cuadros), y el
  texto ("Fix and Flip") queda quieto encima.
- **Zoom suave** que se va cerrando en las frases fuertes ("Sin gastar ni un $1").
- **B-rolls que cuentan una historia, no que tapan**: palabra "propiedad" → la casa desde el piso; renta y cash flow →
  obra en demolición; "nosotros podemos hacer… 100.000 $" → baño terminado (el después); "en una sola transacción" →
  cartel FOR SALE; lista "adquisición / remodelación / salida" → dron, obra, FOR SALE (una toma por palabra).
- **Logo** (versión a color, sin caja) aparece sobre el pecho cuando lo nombran y CRUZA el corte hacia la toma aérea
  del dron; se va con desenfoque.
- No hay tarjetas, barras, íconos, comentarios falsos ni flechas: las cifras grandes de colores hacen ese trabajo.
- **Motion graphics (pedido de Sebas)**: si no hay b-rolls que cuenten la historia, se puede usar un gráfico,
  pero MUY animado, nunca seco: cámara que se mueve, contador que corre (como el 0 → 10.000 de prueba-01, que le
  gustó), subrayado/barrido que dibuja la casa en la toma de dron, textos que se reubican y se apilan con ritmo.
  Las tarjetas quietas con barras de la v1 de prueba-02 se veían "tan secas".

## 3. Sonido

- **Gancho sin música** (0–13,4 s): solo efectos sobre silencio. Eso es lo que da tensión. Riser que lleva a la
  primera transición, ding en "para rentar?", dinero en "vender", golpe fuerte (impacto2) en "$1",
  transición en cada cambio de toma.
- **La música entra cuando empieza la explicación** (~13,4 s, después de "complicado"): Central Cee – Doja
  (instrumental), hasta el final.
- **Música muy baja mientras hablan**: ~24 dB bajo la voz. Sube en el montaje de b-rolls (~12 dB bajo la voz) y
  ~5 dB en las pausas.
- **Los efectos mandan, no la música**: suenan fuertes (el fondo con efectos queda solo 4–8 LU bajo la voz).
- Efectos encontrados (librería de Sebas, coincidencia exacta): transicion ×4, dinero ×5 (vender, "deja dinero?",
  60K, 70K, 100K: uno por cifra), ding ×2 ("para rentar?", "más fácil"), impacto2 ×1 ("$1"), pop ×1 (cifra),
  whoosh ×1 (logo), riser ×1 (gancho); probables: zoom in en cada b-roll de la lista y en "FLIP".
- Referencia de estilo sonoro: Víctor Era (pendiente: analizar videos suyos con nucleo/escuchar.py).

## 3b. Correcciones de Sebas en prueba-02 v2 (aprobado el storyboard)

- **Animación suave y fluida, nunca brusca**: textos entran en ~0,3 s (7 cuadros a 24 fps) con frenado suave,
  desplazamiento corto (~45 px) y desenfoque moderado; salen en ~0,25 s. En los gráficos, nada de rebotes ni
  sacudones: pulsos de escala ≤ 5 %, resortes amortiguados. Lo que ya está en pantalla no se corre cuando entra
  un piso nuevo (cada piso reserva su lugar desde el principio).
- **Efectos de sonido suaves**: la voz siempre manda; nadie debe tener que bajar el volumen para oírla. Cada efecto
  queda al menos ~5 dB bajo la voz hablando (se mide, no se adivina). Golpes (impacto) mucho más abajo
  (~-21 dB), dinero y whoosh ~-16 dB, transición ~-14,5 dB, ding/pop/zoom ~-12/-14 dB.
- **Música**: ~17–18 LU bajo la voz mientras hablan y ~10 LU en el montaje del gráfico.

## 4. Llamada a la acción

"COMENTA" → "COMENTA LA PALABRA" (palabra por palabra, negro, mayúsculas, Bold, arriba) y debajo **"FLIP"** entre
comillas, amarillo, Black, ~150 px, en caja gris oscuro. Los subtítulos de la voz siguen en el pecho.

## 5. Lo que hice mal en la prueba-02 (no repetir)

- Títulos grandes arriba en todo el gancho: él usa arriba SOLO la primera frase; el resto, en el centro.
- Subtítulos de dos niveles fijos (blanco + clave amarilla) en y=1110: él usa 1–3 pisos con tamaños variables según
  la importancia, en y≈900–1150.
- Gráfico de tarjetas y barras para la plata: él usa la cifra gigante con color según el monto, sobre b-roll.
- Música en todo el video (Vivaldi + Runaway) a 15 dB bajo la voz: él deja el gancho sin música y la música mucho
  más baja; los efectos suenan más.
- Demasiados elementos de interfaz (comentario falso, flecha): él lo resuelve solo con texto.
