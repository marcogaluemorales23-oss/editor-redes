#!/usr/bin/env python3
"""Baja (o sube) la velocidad de reproducción de un video cuando el diálogo va muy rápido (flujo de Sebas: x0,9).

Uso: python3 nucleo/velocidad.py <reel> --base base.mp4 [--factor 0.9] [--salida base_lento.mp4]
- Imagen y voz juntas (setpts + atempo): la voz NO cambia de tono y los labios siguen sincronizados.
- Reescala trabajo/palabras.json -> trabajo/palabras_x<factor>.json (todos los tiempos / factor), para que los
  subtítulos, zooms y efectos se planeen sobre el video ya lento.
- Va DESPUÉS de los cortes y la limpieza de la voz, y ANTES de todo lo demás (transiciones, zooms, textos...).
- Ojo: se mantienen los fps del crudo (regla 6). A x0,9 sobre 23,976 fps se repite ~1 cuadro de cada 10; en tomas
  con mucho movimiento puede notarse un leve tirón. Si el crudo es de 50/60 fps no pasa: se usan los cuadros reales.
"""
import argparse
import json
import subprocess
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("reel")
    ap.add_argument("--base", default="base.mp4")
    ap.add_argument("--factor", type=float, default=0.9)
    ap.add_argument("--salida", default="base_lento.mp4")
    ap.add_argument("--fps", help="fps de salida (por defecto los del video)")
    a = ap.parse_args()
    if not 0.5 <= a.factor <= 2.0:
        raise SystemExit("velocidad: el factor va entre 0,5 y 2,0 (atempo)")
    t = Path(a.reel) / "trabajo"
    base = t / a.base
    fps = a.fps or subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                                   "stream=r_frame_rate", "-of", "csv=p=0", str(base)],
                                  capture_output=True, text=True, check=True).stdout.strip()
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(base),
                    "-filter_complex", f"[0:v]setpts=PTS/{a.factor}[v];[0:a]atempo={a.factor}[a]",
                    "-map", "[v]", "-map", "[a]", "-r", fps, "-c:v", "libx264", "-preset", "medium", "-crf", "16",
                    "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "256k", str(t / a.salida)], check=True)
    print(f"x{a.factor} -> {t / a.salida}")
    palabras = t / "palabras.json"
    if palabras.exists():
        datos = json.loads(palabras.read_text())
        for w in datos["palabras"]:
            w["inicio"] = round(w["inicio"] / a.factor, 3)
            w["fin"] = round(w["fin"] / a.factor, 3)
        destino = t / f"palabras_x{a.factor}.json"
        destino.write_text(json.dumps(datos, ensure_ascii=False, indent=1))
        print(f"tiempos reescalados -> {destino}")


if __name__ == "__main__":
    main()
