#!/usr/bin/env python3
"""Pone b-rolls a pantalla completa sobre la base, en los tramos de palabras que diga brolls.json.

Uso: python3 nucleo/broll.py <reel> [--tiempos corte_check.json]
Lee <reel>/trabajo/brolls.json:
    {"brolls": [{"archivo": "assets/broll2.mp4", "desde": 5, "hasta": 9, "inicio_clip": 0.0}]}
"desde"/"hasta" son índices de palabra en la línea de tiempo del corte. El audio de la base no se toca.
Escribe <reel>/trabajo/base_broll.mp4.
"""
import argparse
import json
import subprocess
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("reel")
    ap.add_argument("--tiempos", default="corte_check.json")
    a = ap.parse_args()
    reel = Path(a.reel)
    trabajo = reel / "trabajo"
    w = json.loads((trabajo / a.tiempos).read_text())["palabras"]
    brolls = json.loads((trabajo / "brolls.json").read_text())["brolls"]

    entradas, filtros, previo = ["-i", str(trabajo / "base.mp4")], [], "[0:v]"
    for k, b in enumerate(brolls, start=1):
        t0 = w[b["desde"]]["inicio"] - 0.05
        t1 = w[b["hasta"]]["fin"] + 0.05
        entradas += ["-ss", str(b.get("inicio_clip", 0)), "-t", f"{t1 - t0:.3f}", "-i", str(reel / b["archivo"])]
        # Cubrir 1080x1920 sin deformar y desplazar el clip a su segundo en la línea de tiempo.
        filtros.append(f"[{k}:v]scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,"
                       f"crop=1080:1920,unsharp=5:5:0.9:5:5:0.0,setsar=1,setpts=PTS-STARTPTS+{t0:.3f}/TB[b{k}]")
        filtros.append(f"{previo}[b{k}]overlay=eof_action=pass:enable='between(t,{t0:.3f},{t1:.3f})'[v{k}]")
        previo = f"[v{k}]"
        print(f"b-roll {k}: {b['archivo']} de {t0:.2f}s a {t1:.2f}s")
    salida = trabajo / "base_broll.mp4"
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *entradas,
                    "-filter_complex", ";".join(filtros), "-map", previo, "-map", "0:a",
                    "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p",
                    "-c:a", "copy", str(salida)], check=True)
    print(f"base con b-roll -> {salida}")


if __name__ == "__main__":
    main()
