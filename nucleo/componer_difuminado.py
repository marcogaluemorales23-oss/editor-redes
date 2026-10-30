#!/usr/bin/env python3
"""Compone el formato dynamic estilo vd2 (el que eligió Sebas): el video no se tapa, se DIFUMINA.

Uso: python3 nucleo/componer_difuminado.py <reel> --base base_adobe.mp4 [--graficos graficos_c.mov] [--sin-graficos]
       [--detras detras.mov --detras-desde 1.0 --persona persona.mov]
Lee <reel>/trabajo/capas.json:
    {"tema": "claro"|"oscuro", "bajar": 300, "arriba": [[desde, hasta], ...], "pantallas": [[desde, hasta], ...],
     "blanco_y_negro": [[desde, hasta], ...], "fundido": 0.45}
- "arriba": la parte de arriba del video se desenfoca y oscurece con un degradado que termina sobre la cabeza; ahí
  flotan el título y la tarjeta (capa de Remotion). Como Sebas graba con la cabeza muy arriba, mientras dura el
  tramo el video baja `bajar` px y el hueco de arriba se rellena con el mismo video ampliado y muy desenfocado
  (parece la pared). Todo entra y sale por fundido.
- "pantallas": todo el cuadro pasa a desenfocado oscuro por fundido (la capa de Remotion pone el contenido).
- "detras" (--detras): íconos sueltos a un lado de Sebas y DETRÁS de él (regla de Sebas: nada de ícono con título
  encima). Va la capa de Remotion (renderizada desde --detras-desde) y encima el recorte de la persona
  (persona.mov de nucleo/silueta.py), así el ícono queda entre la pared y Sebas.
Escribe <reel>/trabajo/base_compuesta.mp4 (con --sin-graficos, base_difuminada.mp4 para el storyboard).
"""
import argparse
import json
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw

ZONA_ARRIBA, ZONA_FIN = 560, 920   # opaco hasta 560, se desvanece hasta 920 (sobre la cabeza)
BORDE = 140                        # borde suave del video cuando baja


def mascaras(trabajo):
    zona, borde = trabajo / "mascara_zona.png", trabajo / "mascara_borde.png"
    m = Image.new("L", (1080, 1920), 0)
    d = ImageDraw.Draw(m)
    for y in range(ZONA_FIN):
        v = 255 if y < ZONA_ARRIBA else int(255 * max(0.0, 1 - (y - ZONA_ARRIBA) / (ZONA_FIN - ZONA_ARRIBA)) ** 1.6)
        d.line([(0, y), (1079, y)], fill=v)
    m.save(zona)
    b = Image.new("L", (1080, 1920), 255)
    d = ImageDraw.Draw(b)
    for y in range(BORDE):
        d.line([(0, y), (1079, y)], fill=int(255 * y / BORDE))
    b.save(borde)
    return zona, borde


def suave(u):
    return f"(st(0,clip({u},0,1))*ld(0)*(3-2*ld(0)))"


def envolvente(tramos, f):
    return "+".join(f"between(t,{a:.3f},{b:.3f})*{suave(f'(t-{a:.3f})/{f}')}*(1-{suave(f'(t-{b - f:.3f})/{f}')})"
                    for a, b in tramos) or "0"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("reel")
    ap.add_argument("--base", default="base_adobe.mp4")
    ap.add_argument("--graficos", default="graficos_c.mov")
    ap.add_argument("--sin-graficos", action="store_true")
    ap.add_argument("--detras")
    ap.add_argument("--detras-desde", type=float, default=0.0)
    ap.add_argument("--persona", default="persona.mov")
    a = ap.parse_args()
    t = Path(a.reel) / "trabajo"
    c = json.loads((t / "capas.json").read_text())
    f = c.get("fundido", 0.45)
    arriba, pantallas = c.get("arriba", []), c.get("pantallas", [])
    zona, borde = mascaras(t)
    bn = "+".join(f"between(t,{x:.3f},{z:.3f})" for x, z in c.get("blanco_y_negro", [])) or "0"
    en_arriba = "+".join(f"between(t,{x:.3f},{z:.3f})" for x, z in arriba) or "0"
    y = f"{c.get('bajar', 300)}*({envolvente(arriba, 0.5)})"
    n = len(arriba) + len(pantallas)
    g = [
        f"[0:v]hue=s=0:enable='{bn}',eq=contrast=1.12:enable='{bn}',split=3[v][vplano][rel]",
        # Relleno: el mismo video ampliado y muy desenfocado (como la pared desenfocada de vd2).
        "[rel]scale=1350:2400,crop=1080:1920:135:0,gblur=sigma=40[relleno]",
        "[v]format=rgba[va]", "[2:v]format=gray,scale=1080:1920[mb]", "[va][mb]alphamerge[vb]",
        f"[relleno][vb]overlay=x=0:y='{y}':eval=frame:shortest=1[bajado]",
        # Fuera de los tramos "arriba" el video va limpio (sin borde suave ni relleno).
        f"[bajado][vplano]overlay=0:0:enable='not({en_arriba})'" + ("[comp0]" if a.detras else "[comp]"),
        f"[comp]split={n + 1}[c0]" + "".join(f"[c{i + 1}]" for i in range(n)),
        "[1:v]format=gray,scale=1080:1920,split=" + str(max(1, len(arriba))) + "".join(f"[mz{i}]" for i in range(max(1, len(arriba)))),
    ]
    actual, k = "[c0]", 1
    claro = c.get("tema", "oscuro") == "claro"
    # El tinte se genera a los mismos fps de la base (60 en prueba-01, 23,976 en prueba-02).
    fps = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=r_frame_rate",
                          "-of", "csv=p=0", str(t / a.base)], capture_output=True, text=True, check=True).stdout.strip()
    # Tema claro (el que eligió Sebas, como vd2): el desenfoque se lava hacia crema. Oscuro: vidrio ahumado.
    # En blend la opacidad es de la PRIMERA entrada (la de arriba): la crema va primero, si no se lava al revés.
    tinte_arriba = ("[{e}]gblur=sigma=26[{e}b];color=c=0xF4F0E8:s=1080x1920:r={fps}[{e}c];"
                    "[{e}c][{e}b]blend=all_mode=normal:all_opacity=0.70:shortest=1,format=rgba") if claro else \
                   "[{e}]gblur=sigma=26,colorchannelmixer=rr=0.42:gg=0.42:bb=0.45,format=rgba"
    tinte_pantalla = ("[{e}]gblur=sigma=40[{e}b];color=c=0xF4F0E8:s=1080x1920:r={fps}[{e}c];"
                      "[{e}c][{e}b]blend=all_mode=normal:all_opacity=0.88:shortest=1,format=rgba") if claro else \
                     "[{e}]gblur=sigma=40,colorchannelmixer=rr=0.22:gg=0.22:bb=0.24,format=rgba"
    for i, (a0, b0) in enumerate(arriba):
        g += [tinte_arriba.format(e=f"c{k}", fps=fps) + f"[bz{i}]",
              f"[bz{i}][mz{i}]alphamerge,fade=t=in:st={a0:.3f}:d={f}:alpha=1,"
              f"fade=t=out:st={b0 - f:.3f}:d={f}:alpha=1[za{i}]",
              f"{actual}[za{i}]overlay=0:0[ca{i}]"]
        actual, k = f"[ca{i}]", k + 1
    for j, (a0, b0) in enumerate(pantallas):
        g += [tinte_pantalla.format(e=f"c{k}", fps=fps) + f",fade=t=in:st={a0:.3f}:d={f}:alpha=1,"
              f"fade=t=out:st={b0 - f:.3f}:d={f}:alpha=1[zp{j}]",
              f"{actual}[zp{j}]overlay=0:0[cp{j}]"]
        actual, k = f"[cp{j}]", k + 1
    if not arriba:
        g.append("[mz0]nullsink")
    # Las máscaras fijas se repiten solo lo que dura la base: con "-loop 1" sin límite, una máscara que no se usa
    # (va a nullsink) corre para siempre y el archivo nunca se cierra (sin moov).
    dur = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                          str(t / a.base)], capture_output=True, text=True, check=True).stdout.strip()
    entradas = ["-i", str(t / a.base), "-loop", "1", "-t", dur, "-i", str(zona), "-loop", "1", "-t", dur, "-i", str(borde)]
    # "sin_persona": tramos con b-roll encima, donde el recorte de la persona no debe pegarse.
    sin_persona = "+".join(f"between(t,{x:.3f},{z:.3f})" for x, z in c.get("sin_persona", [])) or "0"
    if a.detras:
        entradas += ["-i", str(t / a.detras), "-i", str(t / a.persona)]
        g[1:1] = [f"[3:v]format=rgba,setpts=PTS-STARTPTS+{a.detras_desde:.3f}/TB[dt]", "[4:v]format=rgba[pe]",
                  "[comp0][dt]overlay=0:0:eof_action=pass[comp1]",
                  f"[comp1][pe]overlay=0:0:eof_action=pass:enable='not({sin_persona})'[comp]"]
    if a.sin_graficos:
        g.append(f"{actual}format=yuv420p[out]")
        salida = t / "base_difuminada.mp4"
    else:
        entradas += ["-i", str(t / a.graficos)]
        g += [f"[{5 if a.detras else 3}:v]format=rgba[gr]", f"{actual}[gr]overlay=0:0,format=yuv420p[out]"]
        salida = t / "base_compuesta.mp4"
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *entradas, "-filter_complex", ";".join(g),
                    "-map", "[out]", "-map", "0:a", "-c:v", "libx264", "-preset", "medium", "-crf", "16",
                    "-c:a", "copy", "-shortest", str(salida)], check=True)
    print(f"compuesto -> {salida}")


if __name__ == "__main__":
    main()
