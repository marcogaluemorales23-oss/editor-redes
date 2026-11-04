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
- **Claude**: BOF-1 ✅, MOF-3 ✅ (a Andy le gustó más que el suyo), BOF-3 ✅, BOF-2, SMS "More than one way",
  "What to expect" A (ya agendaron) y B (aún no agendan), TOF-4 (al final: faltan los videos de Izzy).
