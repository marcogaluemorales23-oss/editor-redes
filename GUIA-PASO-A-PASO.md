# Guía paso a paso — flujo de trabajo de Sebas

Este es EL orden de trabajo para cada video (escrito por Sebas). Debajo de cada paso van las herramientas.
El estilo (qué se ve y por qué) está en `marcas/sebastian/formato-dynamic.md`; la marca en `marcas/<marca>/`.
Referencia aprobada: prueba-02 v2 de Sunny Shore ("me gustó full").

Antes de empezar: crudos en `reels/<nombre>/crudos/`, transcripción palabra por palabra
(`python3 nucleo/transcribir.py reels/<nombre>` → `trabajo/palabras.json`, nombres y cifras corregidos) e
inventario (quién habla en cada toma, dónde están las caras, datos privados para difuminar).

## 1. Cortes
- Cortar por los huecos entre palabras, no por volumen; la mejor toma de cada frase (la última buena).
- Herramientas: `nucleo/cortar.py`, `nucleo/montar.py` (cuadros enteros, voz y labios en sincronía).
- Si el cliente ya lo entrega cortado: no se toca.

- **Corte al milisegundo** (cuando el trabajo es solo cortar, o antes de editar):
  1. Elegir la mejor toma de cada frase en `trabajo/edl.json` (`{"in", "out", "texto"}`): completa, sin trabarse,
     mirando a cámara (revisar cuadros de inicio, medio y final de cada toma).
  2. `python3 nucleo/afinar_cortes.py reels/<nombre> --crudo crudos/<crudo> [--quieto <n>]`: bordes de 50/100 ms,
     pausas internas a 0,20 s, saca arranques en falso; `--quieto n` deja hasta 5 s de imagen quieta después del
     tramo n para insertar un clip.
  3. `python3 nucleo/exportar_cortes.py reels/<nombre> --crudo crudos/<crudo> --salida salida/<nombre>.mp4` (mismo
     formato del crudo; `--crf 19` para que pese menos de 400 MB y se pueda mandar por el chat).
  4. Transcribir el corte final y medir silencios: el texto debe salir completo y sin repeticiones.

## 2. Limpiar y acomodar el audio
- `nucleo/limpiar_voz.py` (voz limpia, nada del camarógrafo).
- **Si el diálogo va muy rápido: bajar la velocidad a x0,9**:
  `python3 nucleo/velocidad.py reels/<nombre> --base base.mp4 --factor 0.9` → `base_lento.mp4` y
  `palabras_x0.9.json` (de aquí en adelante se trabaja con esos tiempos). La voz no cambia de tono.

## 3. Transiciones
- **Flash** en cada cambio de toma (la de Sebas, por defecto):
  `python3 nucleo/flash.py reels/<nombre> --base base.mp4 --cortes` (o `--tiempos ...`).
- Película quemada (`nucleo/transiciones.py` con `overlay_pelicula.mp4`) SOLO cuando Sebas lo pida.
- Entrada a una secuencia de b-rolls: la toma sube desde abajo (`"entrada": "sube"` en brolls.json).

## 4. Zoom in y zoom out en momentos importantes o para generar tensión
- En TODO el video mientras hablan: empuje lento en la frase que sube (1,00 → 1,06–1,10), golpe de zoom
  (+8–12 % en 0,15 s) en la palabra importante, y zoom out para soltar la tensión después del golpe.
- Anclado entre los ojos, desde el crudo 4K: `trabajo/zoom.json` + `python3 nucleo/zoom_crudo.py reels/<nombre>
  --crudo crudos/<crudo>.mp4`.

## 5. Subtítulos
- Composición: subtítulos chiquitos + la palabra clave en grande (1–3 pisos que se apilan con la voz).
- **Color de la palabra clave según la acción**:
  - **verde**: dinero o ganar algo;
  - **rojo**: perder dinero o un error;
  - **amarillo** o **naranja de Claude** (`"claude"`, #D97757): todo lo demás.
- Solo "?" al final de las preguntas; "$" siempre.
- `trabajo/textos.json` → `python3 nucleo/textos_dynamic.py reels/<nombre> --nombre <id>` → componente
  `Textos` (`motion/src/dynamic/Textos.tsx`). Animación suave: entra ~0,3 s, sale ~0,25 s, sin rebotes.

## 6. Música de fondo
- De la carpeta de música de Sebas (Drive, carpeta "musica"). Empieza desde el principio del video o en un
  momento perfecto (p. ej. cuando arranca la explicación).
- **Aparición progresiva**: la música NUNCA arranca de golpe (de fábrica muchas pistas empiezan durísimo). Sube desde
  silencio hasta su volumen normal en 3–4 s (por defecto 3,5 s en la primera música de `transiciones.json`;
  `"entrada"` lo cambia). Después se queda en su nivel de siempre.
- **Música de stock para tensión**: cuerdas en staccato que repiten ("ta-ta-ta-ta tan"), pulsos de cine, suspense.
  Por ahora entra por la carpeta "musica" del Drive (no hay acceso automático a bibliotecas de música).
- Debajo de la voz: ~17–18 LU bajo la voz al hablar, ~10 LU en montajes de b-roll o gráficos.

## 7. Imágenes y b-rolls
- Los que suba Sebas o el cliente, o de stock: `python3 nucleo/stock.py reels/<nombre> "house renovation"`
  (Pexels/Pixabay, vertical; elegir en `trabajo/hoja_stock.jpg`). Pinterest no (sin API, términos, licencias).
- Que cuenten la historia de lo que se dice. `trabajo/brolls.json` → `python3 nucleo/broll.py reels/<nombre>
  --tiempos palabras.json --base <base>` (difuminar datos privados con `"difuminar"`).

## 8. Animaciones o motion graphics
- Muy animados y fluidos, nunca secos: contadores que corren, curvas que suben, contornos que se dibujan, barridos
  de luz, textos que se apilan. Ejemplo aprobado: `motion/src/sunny/Prueba02v2.tsx` (Grafico).

## 9. Acomodar los subtítulos con las imágenes
- Revisar cada b-roll y gráfico con los subtítulos encima: que no se tapen, que no choquen con caras ni con el
  gráfico, dentro de las zonas seguras (245 px arriba, 330 abajo, x ≤ 950/850 a la derecha). En los gráficos, el
  texto del gráfico reemplaza al subtítulo.

## 10. Efectos de sonido
- Dinero en cada cifra, ding en la idea fuerte, whoosh al entrar un b-roll, zoom in en los golpes de zoom,
  transición en cada flash, pop en listas. Con criterio, nunca dos pegados (< 0,5 s).
- `trabajo/transiciones.json` → `python3 nucleo/transiciones.py reels/<nombre> --base <base>` y medir:
  `python3 nucleo/medir_efectos.py reels/<nombre> --base <base>` (ninguno por encima de la voz; lo aprobado:
  1,5–3 dB por debajo, el golpe parejo).

## 11. Storyboard
- 24 cuadros reales con todo aplicado (base + capa como fotos), numerados arriba a la derecha y con el segundo abajo.
- Revisarlo uno mismo antes de mandarlo, junto con el plan de sonido por escrito. Cada corrección: storyboard primero.

## 12. Confirmar y renderizar
- Solo con el "sí" de Sebas.
- Capa: `npx remotion render <Composición> ../reels/<nombre>/trabajo/capa.mov --codec=prores --prores-profile=4444
  --pixel-format=yuva444p10le --image-format=png --concurrency=4`.
- Unir: `ffmpeg -i trabajo/base_final.mp4 -i trabajo/capa.mov -filter_complex "[0:v][1:v]overlay,format=yuv420p[v]"
  -map "[v]" -map 0:a -c:v libx264 -crf 17 -r <fps del crudo> -c:a copy salida/<nombre>.mp4`.
- Prueba de 12 s antes del completo (salvo que Sebas diga que no hace falta).
- `bash nucleo/verificar.sh salida/<nombre>.mp4` (1080x1920, fps del crudo, -14 LUFS, pico ≤ -1 dBTP) y hoja de
  contactos del video final antes de decir "listo".

## Después
- Cada corrección de Sebas → regla en `estilo.md` de la marca o en `formato-dynamic.md`.
- Material de cliente: borrarlo del servidor al terminar la prueba (con confirmación).
