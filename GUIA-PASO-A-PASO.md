# Guía paso a paso — formato dynamic

Cómo se armó la prueba-02 v2 de Sunny Shore (aprobada por Sebas: "me gustó full"). Seguirla en cada video dynamic.
El estilo (qué se ve y por qué) está en `marcas/sebastian/formato-dynamic.md`; aquí va el CÓMO, en orden.
Pendiente: sumar el flujo de trabajo que Sebas va a mandar por escrito.

## 0. Recibir el material
- Crudos en `reels/<nombre>/crudos/` (cámara, drones, stock). Material de cliente: nunca sale del servidor.
- Marca: `marcas/<marca>/marca.json` + `estilo.md` (fuente, colores, Instagram).
- Música: la elige o la pasa Sebas. No elegir a ciegas.

## 1. Escuchar y leer el crudo
```
python3 nucleo/transcribir.py reels/<nombre>            # palabras.json (Whisper large-v3, palabra por palabra)
python3 nucleo/flash.py reels/<nombre> --base base.mp4 --cortes   # (o scdet) para saber dónde cambia la toma
```
- Corregir nombres y cifras contra lo que se oye (y preguntar si una cifra no tiene sentido).
- Inventario: quién habla en cada toma, dónde están las caras (para que el texto del centro no las tape),
  datos privados (números de casa, placas) para difuminar.

## 2. Planear (antes de tocar nada)
1. **Textos** → `trabajo/textos.json`: bloques de 1–3 pisos; tamaño según importancia (s/m/l/xl), amarillo solo
   en la palabra que importa, plata con color según el monto, "?" solo al final, "$" siempre.
2. **Zooms de tensión** → `trabajo/zoom.json`: en TODO el video, mientras hablan. Empuje lento en las frases que
   suben (1,00 → 1,06–1,10) y un golpe (+8–12 %) en la palabra importante de cada toma, anclado en los ojos.
3. **B-rolls** → `trabajo/brolls.json`: que cuenten la historia de lo que se dice. Si faltan tomas:
   `python3 nucleo/stock.py reels/<nombre> "house renovation"` (Pexels/Pixabay, vertical) y elegir en
   `trabajo/hoja_stock.jpg`. Si no hay b-roll que sirva: motion graphic MUY animado (contador que corre, curva que
   sube, contorno que se dibuja), nunca tarjetas quietas.
4. **Transiciones**: FLASH en cada cambio de toma (por defecto). Película quemada solo si Sebas lo pide.
5. **Sonido** → `trabajo/transiciones.json`: gancho sin música (solo efectos); la música entra cuando empieza la
   explicación; efectos con criterio (dinero por cifra, ding en la idea fuerte, whoosh en b-roll, zoom in en golpes).

## 3. Base de video
```
python3 nucleo/zoom_crudo.py reels/<nombre> --crudo crudos/<crudo>.mp4     # zooms desde el 4K -> base.mp4
python3 nucleo/broll.py reels/<nombre> --tiempos palabras.json --base base.mp4   # -> base_broll.mp4
python3 nucleo/flash.py reels/<nombre> --base base_broll.mp4 --tiempos <cortes>  # -> base_flash.mp4
```
("entrada": "sube" en brolls.json = la toma entra subiendo desde abajo, como Sebas al entrar a la secuencia.)

## 4. Capa de textos y gráficos (Remotion, transparente)
```
python3 nucleo/textos_dynamic.py reels/<nombre> --nombre <id>   # -> motion/src/generado/<id>.gen.ts
```
- Composición en `motion/src/<marca>/` que use `Textos` (`motion/src/dynamic/Textos.tsx`) + gráficos + logo.
- Animación suave: entradas ~0,3 s, salidas ~0,25 s, sin rebotes; nada se corre cuando entra un piso nuevo.

## 5. Storyboard (OBLIGATORIO antes de renderizar)
- 24 cuadros reales: base + capa como fotos (`npx remotion still`), numerados arriba a la derecha y con el segundo
  abajo. Revisarlo uno mismo primero (caras tapadas, zonas seguras, ortografía, choques entre elementos).
- Mandarlo con el plan de sonido escrito. No renderizar hasta que Sebas diga que sí. Cada corrección: storyboard.

## 6. Sonido
```
python3 nucleo/transiciones.py reels/<nombre> --base base_flash.mp4     # efectos + música + -14 LUFS
python3 nucleo/medir_efectos.py reels/<nombre> --base base_flash.mp4    # ningún efecto por encima de la voz
```
- Efectos 1,5–3 dB bajo la voz; golpes parejos con ella, nunca encima.
- Música: ~17–18 LU bajo la voz mientras hablan, ~10 LU en el montaje de gráficos o b-rolls.

## 7. Render y entrega
```
npx remotion render <Composición> ../reels/<nombre>/trabajo/capa.mov --codec=prores --prores-profile=4444 \
    --pixel-format=yuva444p10le --image-format=png --concurrency=4
ffmpeg -i trabajo/base_final.mp4 -i trabajo/capa.mov -filter_complex "[0:v][1:v]overlay,format=yuv420p[v]" \
    -map "[v]" -map 0:a -c:v libx264 -crf 17 -r <fps del crudo> -c:a copy salida/<nombre>.mp4
bash nucleo/verificar.sh salida/<nombre>.mp4      # 1080x1920, fps del crudo, -14 LUFS, pico ≤ -1 dBTP
```
- Prueba de 12 s antes del completo, salvo que Sebas diga que no hace falta.
- Hoja de contactos del video final antes de decir "listo".

## 8. Aprender y cerrar
- Cada corrección de Sebas → regla en `estilo.md` de la marca o en `formato-dynamic.md`.
- Al terminar la prueba con un cliente: borrar su material del servidor (pedir confirmación antes).
