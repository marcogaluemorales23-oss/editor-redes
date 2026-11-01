#!/usr/bin/env python3
"""Transición FLASH de Sebas: destello blanco de luz en el corte (quema a blanco ~5 cuadros antes y después).

Es la transición POR DEFECTO para cambios de toma (sobre todo en videos de clientes). La de película quemada
(transiciones.py con overlay_pelicula.mp4) se usa SOLO cuando Sebas lo pide.
Va sobre la base, ANTES de la capa de textos: los textos no se queman (así lo hace él).

Uso: python3 nucleo/flash.py <reel> --base base_broll.mp4 [--salida base_flash.mp4] [--tiempos 2.2 7.84 ...]
     python3 nucleo/flash.py <reel> --base base.mp4 --cortes      # detecta solo los cambios de toma
Sin --tiempos ni --cortes lee <reel>/trabajo/flash.json: {"tiempos": [2.2, 7.84], "fuerza": 1.0, "medio_s": 0.2}
El sonido va aparte (efecto sfx_transicion.mp3, pico 0,3, ~-14,5 dB, en transiciones.json).
"""
import argparse
import json
import subprocess
from pathlib import Path


def cortes(video):
    """Cambios de toma (detector de escena de ffmpeg), sin el final del video."""
    salida = subprocess.run(["ffmpeg", "-v", "error", "-i", str(video), "-vf",
                             "scale=270:480,scdet=threshold=12,metadata=print:file=-", "-an", "-f", "null", "-"],
                            capture_output=True, text=True).stdout
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                str(video)], capture_output=True, text=True).stdout)
    ts = [float(l.split("=")[1]) for l in salida.splitlines() if "lavfi.scd.time=" in l]
    return [round(t, 3) for t in ts if t < dur - 0.3]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("reel")
    ap.add_argument("--base", default="base_broll.mp4")
    ap.add_argument("--salida", default="base_flash.mp4")
    ap.add_argument("--tiempos", type=float, nargs="*")
    ap.add_argument("--cortes", action="store_true")
    ap.add_argument("--fuerza", type=float)
    ap.add_argument("--medio-s", type=float, help="medio largo del destello (0,2 s = ~5 cuadros a cada lado)")
    a = ap.parse_args()
    t = Path(a.reel) / "trabajo"
    base = t / a.base
    conf = json.loads((t / "flash.json").read_text()) if (t / "flash.json").exists() else {}
    tiempos = a.tiempos or (cortes(base) if a.cortes else conf.get("tiempos", []))
    if not tiempos:
        raise SystemExit("flash: no hay tiempos (usa --tiempos, --cortes o trabajo/flash.json)")
    k = a.fuerza if a.fuerza is not None else conf.get("fuerza", 1.0)
    d = a.medio_s or conf.get("medio_s", 0.2)
    # F(t) = 1 justo en el corte y baja en línea recta a 0 a ±d segundos.
    f = "0"
    for x in tiempos:
        f = f"max({f}\\,max(0\\,1-abs(t-{x:.3f})/{d}))"
    # Medido contra la edición de Sebas: se ve quemado pero la toma se sigue leyendo (no blanco puro).
    filtro = (f"eq=eval=frame:brightness='{0.28 * k}*{f}':contrast='1-{0.25 * k}*{f}':"
              f"gamma='1+{0.9 * k}*{f}':saturation='1-{0.4 * k}*{f}'")
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(base), "-vf", filtro,
                    "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p", "-c:a", "copy",
                    str(t / a.salida)], check=True)
    print(f"flash en {', '.join(f'{x:.2f}s' for x in tiempos)} -> {t / a.salida}")


if __name__ == "__main__":
    main()
