# Spine Labs — estilo

Lote de 14 videos de Meta Ads + SMS/email para Andy (nov-2026). Guiones en la carpeta de Drive
"November shoot ads" (Meta Ads (11) + Non Ads deliverables). Guía de clips por guion: PDF de Sebas.

## Referencia: TOF-1 y TOF-2 editados por Sebas
1. **Ritmo**: cortes cada 1,2–2,5 s; 10–13 s en total. Planos cerrados de manos, pantalla de la máquina y caras.
2. **Textos**: Inter Bold, blanco con resplandor oscuro difuso; la palabra clave más grande sobre caja negra
   recta, o en negro sin caja. Frase partida en líneas de distinto tamaño, centrada a media pantalla.
3. **Placa final**: el último plano sigue corriendo desenfocado y aparece la frase
   THERE'S MORE THAN / ONE WAY TO CARE / FOR A SPINE.
4. **Audio**: se deja la voz real del doctor cuando explica (TOF-1: "So you see how it feels really comfortable").
5. **Pacientes**: cada anuncio sigue a UN paciente (1: camiseta de tigre / doctor; 2: gorra / doctor; 3: Izzy /
   doctora rubia). No mezclar en el mismo anuncio salvo los de marca (TOF-3, TOF-5).

## Pendientes / ojo
- Logo de Spine Labs en las placas (el guion lo pide en todas).
- Volumen de entrega a -14 LUFS (las v1 salieron a -25 y -24 LUFS).
- Duración del guion: TOF 6–10 s; MOF/BOF 15–30 s.

## Correcciones de Sebas
1. **Música** (BOF-1 v2): "advertising" (bombinsound) sonó muy chillona. Usar la de TOF-2:
   "background" (prettyjohn1, Pixabay, 99 BPM) con agudos suavizados (highshelf 5 kHz -4 dB) para los rápidos.
   Otras pistas aprobadas (Pixabay, sin Content ID): corporate_time (folk_tales, 117 BPM) y ambient (atlasaudio)
   para los de voz. Nada de música de Epidemic sin licencia comercial (son anuncios pagados).
2. **Cortes sobre el golpe** de la música (planos de 3 tiempos ≈ 1,8 s a 99 BPM; placa final 5 tiempos).
3. **Sin precios en pantalla**: la clínica tiene carteles de $29/$59 y listas de precios en la sala de espera;
   los anuncios dicen "first visit is always free". Encuadrar para que no se vean.
4. **Animación de textos "izq_der"** (MOF-3): el texto aparece revelándose de izquierda a derecha con un deslizamiento
   suave, se detiene en el centro y antes del corte sigue hacia la derecha borrándose (`"anim": "izq_der"` en el bloque).
   Cada plano con texto necesita al menos ~1,1 s para que se lea entre la entrada y la salida.
5. **Texto sobre pantallas**: no tapar lo que muestra el celular/tablet (MOF-3 toma 4: título arriba del teléfono).
6. **Sin puntos** en palabras sueltas en pantalla (BONE, MUSCLE, NERVE).
7. **Voces que no se grabaron**: van como texto en pantalla; nunca se genera la voz de la doctora con IA.
8. **La voz manda** (MOF-3 v2): cuando alguien habla, se escucha la voz primero que todo. Cada tramo de voz a -16 LUFS
   y la música 18 dB más baja mientras hay voz (rampa de 0,25 s); sube de nuevo solo donde no hay voz.
   Verificar con stems: voz vs música en cada medio segundo (diferencia ~20 dB).
9. **Cero silencio al entrar a la toma de quien habla** (MOF-3 v3): la toma entra 50 ms antes de la primera palabra
   (medir el arranque de la voz con energía, no con el tiempo de Whisper, que se adelanta ~0,5 s).

## Reparto del lote (4-nov-2026)
- **Andy**: TOF-5, MOF-1, MOF-2.  **Sebas**: TOF-1, TOF-2, TOF-3.  NO tocarlos.
- **Claude**: BOF-1 ✅, MOF-3 ✅ (a Andy le gustó más que el suyo), BOF-3 ✅, BOF-2 ✅, SMS "More than one way",
  "What to expect" A ✅ y B ✅, TOF-4 ✅. SMS "More than one way" lo hace Sebas. LOTE DE CLAUDE COMPLETO (7 videos).
10. **Textos partidos en dos** (BOF-2): la palabra de apoyo arriba SIN caja y un poco más grande cuando es la que
    atrae ("SPINAL"), la clave abajo CON caja ("DECOMPRESSION"); en la placa: "BOOK YOUR FIRST" sin caja / "VISIT NOW" con caja.
11. **Material de celular** (videos de Izzy, horizontales y de baja resolución): va como recuadro centrado sobre el
    mismo video desenfocado (`"marco": true`), con zoom en la persona para que no se vean las marcas del evento.
12. **Estabilización suave** (BOF-2): tomas a mano movidas → `"estabilizar": 20` (vid.stab, zoom mínimo automático).
    Medir el temblor en el FONDO antes/después; "fuerte" (40) casi nunca mejora y agranda el zoom, que Sebas no quiere.
    Planos seguidos del mismo clip comparten `"estab_rango"` para que no salte el zoom en el corte.
13. **Persona a cámara centrada en x** (BOF-2): la doctora alineada al centro del video; la altura se respeta.
14. **Antes de estabilizar, buscar otro tramo del mismo clip** (BOF-2, check-in): medir el temblor a lo largo del
    clip y usar el tramo más quieto que muestre la acción (C7682 18,0–19,4: la mano tocando la pantalla, 1,5 px).
    La estabilización deja un bamboleo que Sebas nota; un tramo quieto no.
15. **Animación por palabra** (TOF-4): cada segmento puede traer su `"anim"` (si no, la del bloque):
    `izq_der` (BONE/MUSCLE/NERVE), `subir` (frases que suben desde abajo con desvanecido, toma 1 y tomas 8–10),
    `bajar` (TO YOU cae desde arriba debajo de IMPORTANT que entra izq_der). Sebas mezcla animaciones según la toma.
16. **Gancho con sonido de escena** (TOF-4): aplausos + murmullo de público + brillo de coronación generados con
    `nucleo/sfx_sintetico.py` (nunca el audio del video del celular). Música 9 dB abajo en el gancho (`"bajar"`),
    y el gancho a ~3 dB del resto para que no se sienta flojo.
17. **Nada de tomas "esperando la orden"**: arrancar cuando la persona ya se mueve (medir movimiento cuadro a
    cuadro). Si camina hacia la cámara y casi no se nota, sumar un acercamiento suave.
18. **TOF-4 v3** (aprobado): a Sebas no le gustaron los aplausos/brillo generados en el gancho; quedó solo música.
    Si se quiere sonido de escena, pedir efectos reales de Pixabay ("crowd applause cheering", "magic sparkle").
19. **UN VIDEO A LA VEZ** (regla de Sebas): no mandar storyboards ni avances de otro video hasta que Sebas diga
    "listo, vamos con el siguiente". "Tofu cubano" = TOF-4 (así suena "tofu cuatro" en su dictado).
20. **Toda toma arranca en movimiento real** (TOF-4, tomas 3 y 4): medir el movimiento cuadro a cuadro y entrar
    cuando la persona ya camina con decisión, no en los pasos titubeantes de "dale, ya estoy grabando" (se ve actuado).
21. **What to expect** (A y B): visita de Izzy con sus diálogos reales; etiqueta del paso arriba ("1 · ARRIVE"…),
    tomas 4-5 a media altura (1050) y 7-10 a 700; apertura A: toma 1 a media pantalla, toma 2 debajo de "1 · ARRIVE".
    Recortar colas de otra frase ("And what…") y silencios internos de más de 0,3 s al inicio de una toma hablada.
22. **Descompresión = piernas elevadas en el cojín** (What to expect, toma 10): Sebas espera ver la camilla haciendo
    su trabajo (C7785 2,9–5,65: piernas arriba + logo SPINE LABS de la máquina), no solo a la persona acostada.

## Ronda de correcciones (5-nov-2026, clienta de Andy)
Pidió: fuente más de marca y delicada, SIN cajas negras, color cinematográfico/difuminado, música moderna (no stock),
más dinamismo con el audio. Referencia de la clínica (testimonio): Montserrat SemiBold MAYÚSCULAS blanca con sombra,
subtítulos de 2-3 palabras que aparecen en seco, color cálido suave, cierre con logo 3D cromado (no lo tienen).
Estilo aprobado para probar (estilo 5): cursiva Cormorant (con sombra fuerte) en las frases grandes; etiquetas y
subtítulos en Montserrat 600-700 blanca con sombra oscura cercana (sombra 1.0, blur 0.2) — sin píldoras (a Sebas no le
gustaron); `"grado": "cine"`. Música: Andy autoriza cualquier canción (sin licencia, riesgo asumido por él).
   **What to expect va SIN subtítulos** (Sebas). La función de subtítulos queda para otros videos (`subtitulos()` en reels/spine-labs/trabajo/estilos_wte.py).
   **Estilo "referencia"** (medido en píxeles sobre el testimonio que mandó Andy): la fuente es **Raleway** (no
   Montserrat: la W y la M lo delatan), peso ~650, MAYÚSCULAS, blanca, em 64 en 1080 (cap 45 px), tracking 0.02,
   UNA línea a y≈1097 (57 % del alto), sombra proyectada abajo-derecha `"sombra_caida": [4, 5, 2, 0.95]`, entra y
   sale en seco. Sin cursiva ni cajas. Generador: reels/spine-labs/trabajo/estilo_referencia.py.
   Correcciones de Sebas sobre el estilo referencia: apertura en DOS líneas apiladas a mitad de pantalla (y 960) en las
   tomas 1 y 2 ("THANKS FOR SCHEDULING / YOUR FIRST VISIT!", "HERE'S WHAT YOU / CAN EXPECT"); TODOS los textos entran
   con `"anim": "rebote"` (suben ~46 px y se asientan con un sobrepaso suave de ~4 %, 0,5 s; salen desvaneciéndose);
   la placa final lleva las dos líneas juntas ("WE CAN'T WAIT / TO SEE YOU!"). Pasos numerados desde el check-in (1-7).

## ESTILO APROBADO (5-nov-2026): el TOF-2 corregido de Sebas (le gustó a Andy y a la intermediaria)
Raleway: apoyo fino (300), clave en negrita (700); en el gancho la clave ~1,7x más grande ("EVER SEEN AN" /
**ADJUSTMENT** / LIKE THIS?). Sombra proyectada [4, 5, 2, 0.95]. Cada línea SUBE con desenfoque en 0,25 s
(`"anim": "sube"`), una tras otra (paso ~0,14 s). Placa: logo arriba (y≈650, ancho 470) y la frase debajo mezclando
fino/negrita ("THERE'S MORE THAN / ONE **WAY** TO CARE / FOR **YOUR SPINE**"). Música con ritmo (~140 BPM), cortes
sobre el golpe, whooshes y "text sound" en las entradas. Ayudantes: reels/spine-labs/trabajo/estilo_tofu2.py.
Orden de re-edición: BOF-1, MOF-3, BOF-2, BOF-3, TOF-4, What to expect A, What to expect B (un video a la vez).
   **Máximo 3 líneas por toma** (Sebas, BOF-1): si una frase pide más, se parte entre dos tomas para que no se vea cargado.
   **Efectos de Sebas** (TOF-2): "text sound 2" al entrar cada palabra/línea, a veces "wosh suave" o "zoom in";
   "ding" cuando aparece el logo de Spine Labs.
   **Música (ronda 2)** — Andy aprobó "Ambiental Tech" (144 BPM, 31 s; ya va en el TOF-2) pero sin repetirlo mucho.
   Plan: BOF-1 ANOTR "Talk To You" desde 19,30 s (129 BPM, tramo sin voz) · MOF-3 Be'le "algo bueno" (instrumental,
   96 BPM) desde 13,21 · BOF-2 Ambiental Tech desde 10,03 · BOF-3 Jonas Blue "Edge Of Desire" desde 21,04 (tramo sin
   voz) · TOF-4 ANOTR o Jonas Blue (drop) · What to expect A/B Be'le. Flo Rida "Right Round": NO (letra sexual).
   **Sin transiciones** (Sebas, ronda 2): solo cortes secos entre tomas; nada de barridos ni su whoosh.
   **BOF-1 ronda 2**: abre con el recorrido de arriba hacia abajo de C7732 (2,6-5,3 s, lo más estable) en vez de la
   fachada temblorosa; la toma 2 sigue de corrido. Música elegida por Sebas: Be'le "algo bueno" desde 13,21 s
   (96 BPM, 3 tiempos por toma ≈ 1,9 s). ANOTR le sonó "ranchera" en ese tramo; Jonas Blue no convenció.
   Texto que no tape letreros que se mueven en la toma (BOF-1: el bloque bajó a y 1250 para que el letrero suba libre).
   BOF-1 v3 (Sebas): la apertura son DOS tomas de C7732: acercamiento al logo (0,9 s, zoom 1,12→1,42, estabilizado) y corte al paciente entrando (6,1 s).
   BOF-1 v4: el estabilizador dejaba un salto al final de la toma del logo; se usa el tramo 100 % quieto de C7732 (2,0-3,2 s) sin estabilizar (logo 2 tiempos + entrada 4 tiempos). Antes de estabilizar, buscar SIEMPRE un tramo quieto.
   **MOF-3 ronda 2**: la clienta pidió b-rolls estables. Se midió el temblor de cada toma y se cambió por el tramo más quieto que muestra lo mismo (ajuste C7711 3,0; descompresión C7717 25,5; perilla C7757 8,47; app C7673 16,6; BONE C7667 13,9; NERVE C7667 4,4). Las tomas de la doctora a cámara no se tocan.
   Color (Sebas, MOF-3): sobre el "cine" suave, +10 % saturación y +5 % exposición (`"saturacion": 0.10, "exposicion": 0.05`). Frase secundaria de la placa en DOS líneas, em 46 (más legible).
   **Subtítulos cuando habla la doctora** (Sebas, BOF-2): UNA línea, frases completas de 3-4 palabras (nunca cortar una frase a la mitad), Raleway 600 em 70, sombra proyectada, y 1250, entran con "sube". Placa final siempre sobre una toma ESTABLE (BOF-2: sala de tratamiento C7812 6,2, prácticamente quieta; C7687 era un paneo que se sentía tambaleante).
   **Subtítulos SIEMPRE con la voz** (Sebas, BOF-2): nunca atrasarlos para evitar un corte. Si la frase cruza un corte, sus dos líneas aparecen juntas al empezar la frase y se quedan hasta que termina. Frase larga: apoyo arriba + clave abajo más grande ("YOUR FIRST VISIT / **IS ALWAYS FREE**", "THE SPINE LABS / **DIFFERENCE**"), para no ocupar todo el ancho (redes recortan los bordes).
   **Nada de miradas a cámara en los b-rolls** (Sebas, BOF-2 EXAMINATION): elegir el momento en que la persona está concentrada en el paciente, genuina (C7711 3,9: manos sobre el paciente).
   **Sin corrección de color desde BOF-3** (Sebas la hace él en Premiere): no poner "grado", "saturacion" ni "exposicion". BOF-1, MOF-3 y BOF-2 de la ronda 2 quedan como se aprobaron (con color) y NO se vuelven a renderizar salvo que pidan una corrección.
