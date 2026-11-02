#!/usr/bin/env python3
"""Exporta un corte (lista de tramos del crudo) en el MISMO formato del crudo, para que Sebas lo siga editando.

Uso: python3 nucleo/exportar_cortes.py <reel> --crudo crudos/C5510.MP4 [--salida salida/corte.mp4] [--sin <n> ...]
Lee <reel>/trabajo/edl.json: {"cortes": [{"in": 204.40, "out": 207.62, "texto": "..."}, ...]} (segundos del crudo).
- Cada tramo se ajusta a cuadros enteros del crudo y el audio se corta al mismo largo exacto (voz y labios en
  sincronía, regla 12). Fundido de 10 ms en cada borde del audio para que no haya "clic" en los cortes.
- Mantiene resolución, fps y color del crudo (H.264 alta calidad + AAC 320k). No toca la voz ni el color.
- --sin 3 deja afuera el tramo 3 (numerados desde 1), para probar versiones sin rehacer la lista.
"""
import argparse
import json
import subprocess
from fractions import Fraction
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("reel")
    ap.add_argument("--crudo", required=True)
    ap.add_argument("--salida", default="salida/corte.mp4")
    ap.add_argument("--sin", type=int, nargs="*", default=[])
    ap.add_argument("--crf", type=int, default=15)
    a = ap.parse_args()
    reel = Path(a.reel)
    crudo = reel / a.crudo
    info = json.loads(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                                      "stream=r_frame_rate,width,height", "-of", "json", str(crudo)],
                                     capture_output=True, text=True, check=True).stdout)["streams"][0]
    fps = Fraction(info["r_frame_rate"])
    cortes = [c for k, c in enumerate(json.loads((reel / "trabajo" / "edl.json").read_text())["cortes"], start=1)
              if k not in a.sin]
    entradas, filtros, total = [], [], 0
    for i, c in enumerate(cortes):
        f0, f1 = round(c["in"] * fps), round(c["out"] * fps)
        n = f1 - f0
        t0, dur = float(f0 / fps), float(n / fps)
        entradas += ["-ss", f"{t0:.6f}", "-t", f"{dur + 0.5:.6f}", "-i", str(crudo)]
        filtros.append(f"[{i}:v]trim=end_frame={n},setpts=PTS-STARTPTS[v{i}]")
        filtros.append(f"[{i}:a]atrim=end={dur:.6f},asetpts=PTS-STARTPTS,afade=t=in:d=0.01,"
                       f"afade=t=out:st={max(0, dur - 0.01):.6f}:d=0.01[a{i}]")
        total += dur
    k = len(cortes)
    filtros.append("".join(f"[v{i}][a{i}]" for i in range(k)) + f"concat=n={k}:v=1:a=1[v][a]")
    salida = reel / a.salida
    salida.parent.mkdir(exist_ok=True)
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *entradas, "-filter_complex", ";".join(filtros),
                    "-map", "[v]", "-map", "[a]", "-r", info["r_frame_rate"], "-c:v", "libx264", "-preset", "medium",
                    "-crf", str(a.crf), "-pix_fmt", "yuv420p", "-color_primaries", "bt709", "-color_trc", "bt709",
                    "-colorspace", "bt709", "-c:a", "aac", "-b:a", "320k", "-ar", "48000",
                    "-movflags", "+faststart", str(salida)], check=True)
    print(f"{k} tramos, {total:.2f} s -> {salida} ({info['width']}x{info['height']}, {float(fps):.3f} fps)")


if __name__ == "__main__":
    main()
