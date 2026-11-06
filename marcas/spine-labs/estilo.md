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
   **TOF-4 ronda 2** (correcciones del cliente): sin las tomas del escenario (celular de Izzy, "se ve horrible"); abre con Izzy caminando hacia la cámara (C7762 24,9); escaneo 3D en tramo estable (C7745 18,6); después del escaneo, paneo por los 3 carteles (C7667 5,6, acelerado x3,2: NERVE→MUSCLE→BONE; perfil plano, Sebas lo colorea). Música Ambiental Tech.
   TOF-4 v3 (Sebas): Izzy caminando 1,2 s (no más); IMPORTANT/TO YOU a la cintura (y 1060); carteles en 3 cortes como MOF-3 (BONE 13,9 · MUSCLE 8,2 · NERVE 4,4), el paneo acelerado no le gustó; YOUR SPINE IS PART una sola vez desde la correa de la cabeza; música Jonas Blue (drop 1:46,9).
   **Estabilizador: medir SIEMPRE antes y después** (What to expect): en tomas donde las personas llenan el cuadro (evaluación C7775) vid.stab sigue a la gente y EMPEORA el temblor (5,5 → 6,4); ahí se deja como viene. En "face down" (C7776) sí mejoró (5,1 → 2,6).
   **What to expect B ronda 2** (Sebas: sin estabilizador, tramo más quieto de cada clip): evaluación desde 1,0 s (temblor 6,5 → 2,8) con la voz entrando 0,66 s antes sobre el saludo (sincronía intacta); saludo +0,5 s y voz del saludo cortada antes de "here". "Face down": no hay tramo quieto mientras habla de frente → va como viene.
   **AUTORREVISIÓN antes de mandar** (Sebas): `anuncio.py` achica sola cualquier línea de más de 900 px y avisa si un
   texto sale del alto seguro (250-1590) o toca la columna de botones (x > 850 con y > 1000). Storyboard con
   `--guias` para revisarlo yo. Verificar también la sincronía voz-imagen con números (desfase 0 ms en cada toma donde
   se ve hablar a alguien). NADA de voz adelantada ni cortada para ganar estabilidad: la sincronía manda.
   **Siempre storyboard antes de renderizar**, también en las versiones B.
   **Respuestas del paciente** (Sebas, What to expect B): si el paciente habla lejos del micrófono ("It does" de Izzy), va en su propio tramo de voz (se normaliza aparte y queda al nivel de la doctora). Revisar que la frase siguiente no arranque con la cola cortada de otra ("...there"): empezar en la primera palabra limpia.
   What to expect B: el audio de C7782 sigue hasta 10,46 s (Izzy "It does" + doctora "And what happens is you end up just..."), toma de la máquina +1,3 s (misma toma, sincronía 0 ms) y piernas +1,1 s; video 39,5 s. Nunca cortar el audio justo después de la respuesta de alguien: dejar respirar la frase.
   **Si piden arreglar el AUDIO, no tocar las tomas** (Sebas): la corrección de "It does" se hizo solo con audio (la frase de la doctora sigue sobre la toma de las piernas, donde no se ven labios; luego "You can just relax..." antes de la risa). **Placa con la persona en movimiento**, nunca parada: B cierra con Izzy y la doctora caminando (C7776 0,21 → placa de corrido).
   B final: CHECK OUT = C7776 2,6 (ya caminando); placa en la RECEPCIÓN desde que Izzy camina por el mostrador (C7764 14,2) con cámara lenta x0,68 para llenar 3,4 s. ANTES DE MANDAR: revisar cada toma nueva contra la regla de "arranca en movimiento, sin mirar a cámara".
   **Fragmento enviado por Sebas** (placa de WTE B): si Sebas manda el clip ya recortado, se usa TAL CUAL anclado en el cuadro 0 (sin cámara lenta, sin zoom, sin buscar otro tramo); si sobra, se corta el final. Para pedirle un fragmento: decirle clip, segundos usados y cuánto dura la toma. WTE B final: placa = `crudos/PLACA_SEBAS.MP4` 0,0–3,4 s.
   **Estado ronda 2 (Sebas)**: BOF-1, MOF-3, BOF-2, BOF-3, TOF-4, WTE A y WTE B TERMINADOS. WTE A queda como está (no se le pasan los cambios de B). Pendiente: correcciones de Andy al BOF-1 (las va a mandar Sebas).
   **BOF-1 ronda 3 (Andy + Sebas)**: sin el acercamiento al logo (abre con C7732 5,5, la cámara bajando y el chamo entrando); perilla C7757 en su tramo más quieto (13,89; el peor salto pasó de 16 a 1,3). **Márgenes sin achicar textos**: si un texto toca la columna de botones, se sube a la parte de arriba o se corre a la izquierda (`"dx": -70`, centrado en x = 470 entre el margen y los botones); el CTA largo se parte en dos ("BOOK YOUR" / "FIRST VISIT" clave). Texto sobre una toma con paneo vertical: que entre cuando el elemento de fondo (letrero) ya pasó, para que no se monten.
   **LEER los AVISOS de anuncio.py antes de decir "zona segura OK"** (me pasó en BOF-1: el aviso salió y no lo leí).
   **Testimonios (3 extra, documentos de Andy)**: estructura del documento + estilo aprobado del TOF-2 (Sebas). Orden: Sam → paciente de la gorra → Izzy. Subtítulos del diálogo: Raleway 600 62 px, frase completa, dos líneas si es larga, centrados en y 1250 y ≤ 620 px de ancho (columna de botones). Etiquetas de cada paso arriba (y 330) y título "<NOMBRE>'S / FIRST VISIT" en la llegada. Placa: voz real C7801 2,15–5,05 ("At Spine Labs, your first visit is always free") y la frase entra cuando ella la dice.
   **El final de cada tramo de voz se mide con la energía del audio, no con el fin de palabra de Whisper** (en Sam se comió el "free" de la doctora por cortar en 4,75). Revisar transcribiendo el render final.
   Sebas (Sam): propone abrir con Sam entrando a la clínica en vez del doctor escuchando; se renderizó la versión del doctor para comparar.
   **Sam v2 (Sebas)**: abre con Sam entrando y su voz encima (C7690); el título nunca encima de una cara (va solo en la toma de espaldas, y 400). Recepcionista en plano abierto (C7683, otra toma del saludo) en vez del primer plano C7684. Consulta en UNA toma corrida (C7689 5,5–20,75): nada de cortar al detalle del uniforme y volver. Zoom de las tomas con diálogo fijo en 1,0 y empujes de máx. 1,03: los clips ya vienen cerrados de cámara.
   **Voz limpia por Sebas**: `anuncio.py --voz` exporta salida/<nombre>_VOZ.wav (pista de voz sola, del largo del video, nivelada y sin procesar). Él la limpia (volumen, eco) y la devuelve; se usa con `"audio": {"voz_archivo": "<archivo en trabajo/>"}` (la lista "voz" queda solo para el ducking de la música). Si el montaje cambia después, hay que volver a exportarla.
   **NINGÚN texto encima de una cara** (Sebas lo pidió varias veces): `--guias` ahora corre `revisar_caras()` (MediaPipe sobre los cuadros sin textos, al entrar, a la mitad y al salir de cada bloque) y avisa "tapa una cara". Si avisa: bajar los subtítulos (y 1480 sobre la ropa) o subir/acortar el texto. Etiquetas de paso: solo 1,6 s al empezar el paso. Revisar los avisos uno por uno (la nuca de alguien de espaldas puede dar falso aviso: comprobar con la imagen).
   **La música tiene que durar todo el video** (Sam: ANOTR desde 2:23,85 se acababa a los 45 s). `anuncio.py` ahora avisa "AVISO música: se acaba en el segundo X". Si se acaba: alargarla repitiendo un tramo en el compás exacto (16 compases atrás, buscando el punto más parecido con librosa) y con el salto escondido debajo de un diálogo. Sam: musica/anotr_sam_extendida.wav (143,85→180,225 + 151,115→178,5).
