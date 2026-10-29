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
