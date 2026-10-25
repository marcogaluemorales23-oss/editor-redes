#!/usr/bin/env python3
"""Monta la base sin textos a partir de edl.json: 1080x1920, fps del crudo, audio a -14 LUFS.

Uso: python3 nucleo/montar.py <reel> [--zoom 1.0,1.18,...]
--zoom: acercamiento por corte (se repite en ciclo). Por defecto alterna plano normal y cerrado,
recortando hacia la parte de arriba para que la cara quede en el tercio superior.
"""
import argparse
import json
import subprocess
from pathlib import Path


def fps_de(clip):
    return subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=r_frame_rate",
         "-of", "csv=p=0", clip], capture_output=True, text=True, check=True,
    ).stdout.strip().strip(",")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("reel")
    ap.add_argument("--zoom", default="1.0,1.18")
    a = ap.parse_args()
    reel = Path(a.reel)
    trabajo = reel / "trabajo"
    tramos = trabajo / "tramos"
    tramos.mkdir(exist_ok=True)
    cortes = json.loads((trabajo / "edl.json").read_text())["cortes"]
    zooms = [float(z) for z in a.zoom.split(",")]
    fps = fps_de(str(reel / "crudos" / f'{cortes[0]["clip"]}.MP4'))

    lista = []
    for k, c in enumerate(cortes):
        z = zooms[k % len(zooms)]
        w, h = round(1080 * z / 2) * 2, round(1920 * z / 2) * 2
        # Recorte centrado en horizontal y con la cara en el tercio superior (y = 25 % del sobrante).
        vf = f"scale={w}:{h}:flags=lanczos,crop=1080:1920:(iw-1080)/2:(ih-1920)*0.25,fps={fps},format=yuv420p"
        d = c["out"] - c["in"]
        af = f"afade=t=in:d=0.01,afade=t=out:st={d - 0.012:.3f}:d=0.012"
        salida = tramos / f"{k:02d}.mp4"
        subprocess.run(
            ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", str(c["in"]), "-t", f"{d:.3f}",
             "-i", str(reel / "crudos" / f'{c["clip"]}.MP4'), "-vf", vf, "-af", af,
             "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-c:a", "pcm_s16le", "-ar", "48000",
             str(salida.with_suffix(".mov"))], check=True,
        )
        lista.append(f"file '{salida.with_suffix('.mov').name}'")
        print(f"tramo {k + 1}/{len(cortes)} listo (zoom {z})")
    (tramos / "lista.txt").write_text("\n".join(lista) + "\n")

    base = trabajo / "base.mp4"
    subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0",
         "-i", str(tramos / "lista.txt"), "-c:v", "copy",
         "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
         "-movflags", "+faststart", str(base)], check=True,
    )
    print(f"base -> {base}")


if __name__ == "__main__":
    main()
