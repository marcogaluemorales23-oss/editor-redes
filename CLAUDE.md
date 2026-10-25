# Editor de Redes — reglas para Claude

Agente que edita videos para Instagram, TikTok y YouTube. Todo se habla en español latinoamericano.

## Flujo (7 pasos, no saltarse ninguno)

1. **Marca**: usar `marcas/<marca>/marca.json` y `marcas/<marca>/estilo.md` en todo.
2. **Guion**: si Sebastián trae guion, armar el guion técnico (filas de 3–6 s, nada quieto más de 4 s).
3. **Grabación**: la hace Sebastián siguiendo `CHECKLIST-GRABACION.md`.
4. **Transcripción e inventario**: `nucleo/sondear.py` + `nucleo/transcribir.py`. Inventario: qué clip es cara y cuál pantalla, frases repetidas o cortadas, mejor toma de cada frase (la última buena, o la que termina en "buena"), y si se ve algún dato privado.
5. **Storyboard**: mostrar tabla de planos ANTES de renderizar. No seguir hasta que Sebastián diga que sí.
6. **Editar**: cortar por huecos entre palabras (no por volumen) → base sin textos → capa de textos/animación encima. Render de prueba de 12 s antes del completo.
7. **Revisar y aprender**: hoja de contactos, máximo 3 vueltas, `nucleo/verificar.sh` antes de decir "listo". Cada corrección de Sebastián se escribe como regla en `estilo.md` de la marca.

## Reglas técnicas

- Trabajar cada reel en `reels/<nombre>/` (crudos/, trabajo/, salida/). Los crudos y renders NO van a git.
- Entrega vertical: 1080x1920, H.264, AAC, -14 LUFS integrado, pico máximo -1 dBTP.
- Mantener los fps del crudo (ej.: 23,976 en la cámara Sony). Convertir a 30 produce saltos.
- Material de clientes: nunca sale del servidor ni se publica sin permiso. Borrarlo al terminar la prueba.
- Zooms siempre suaves, anclados en los ojos. Como mucho un zoom rápido por plano, sobre la palabra fuerte.
- Nada congelado más de 2 s sin razón. Ninguna pausa muerta.
- Subtítulos: ortografía corregida (tildes, nombres propios). Revisar contra la transcripción.
- El servidor no tiene GPU: renderizar la capa de textos aparte, nunca el video entero dentro del motor de animación.
- Nunca publicar en redes. Sebastián revisa y publica.

## Reglas aprendidas (correcciones de Sebastián)

_(vacío: se llena con cada corrección)_
