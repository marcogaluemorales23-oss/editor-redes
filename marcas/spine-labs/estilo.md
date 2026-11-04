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
  "What to expect" A (ya agendaron) y B (aún no agendan), TOF-4 ✅.
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
