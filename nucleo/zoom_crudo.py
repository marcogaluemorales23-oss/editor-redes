#!/usr/bin/env python3
"""Zooms suaves y golpes de zoom sacados directo del crudo en alta (4K -> 1080x1920): el acercamiento no pierde nitidez.

Uso: python3 nucleo/zoom_crudo.py <reel> --crudo crudos/raw.mp4 [--salida base.mp4]
Lee <reel>/trabajo/zoom.json: lista de tramos (tiempo del video):
    [{"desde": 0, "hasta": 7.84, "ancla": [0.5, 0.36], "empuje": [1.0, 1.08],
      "golpes": [{"t": 4.14, "z": 0.05, "hasta": 4.8}]}, ...]
- "ancla": punto que queda quieto en pantalla (fracción del cuadro, x y), normalmente entre los ojos.
- "empuje": zoom al inicio y al final del tramo (curva suave). Fuera de los tramos, zoom 1.0.
- "golpes": zoom rápido (0,15 s) que se suma en "t" y se suelta suave en 0,35 s desde "hasta".
Mantiene los fps del crudo y copia su audio.
"""
import argparse
import json
import subprocess
from pathlib import Path

import cv2
import numpy as np

W, H = 1080, 1920


def suave(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)


def zoom_en(t, tramos):
    for tr in tramos:
        if tr["desde"] <= t < tr["hasta"]:
            z0, z1 = tr.get("empuje", [1.0, 1.0])
            z = z0 + (z1 - z0) * suave((t - tr["desde"]) / (tr["hasta"] - tr["desde"]))
            for g in tr.get("golpes", []):
                fin = g.get("hasta", tr["hasta"])
                z += g["z"] * suave((t - g["t"]) / 0.15) * (1 - suave((t - fin) / 0.35))
            return z, tr.get("ancla", [0.5, 0.5])
    return 1.0, [0.5, 0.5]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("reel")
    ap.add_argument("--crudo", required=True)
    ap.add_argument("--salida", default="base.mp4")
    a = ap.parse_args()
    reel = Path(a.reel)
    tramos = json.loads((reel / "trabajo" / "zoom.json").read_text())
    crudo = reel / a.crudo
    info = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                           "stream=width,height,r_frame_rate", "-of", "csv=p=0", str(crudo)],
                          capture_output=True, text=True, check=True).stdout.strip().split(",")
    ancho, alto, fps_txt = int(info[0]), int(info[1]), info[2]
    n, d = (int(v) for v in fps_txt.split("/"))
    fps = n / d
    lector = subprocess.Popen(["ffmpeg", "-v", "error", "-i", str(crudo), "-f", "rawvideo", "-pix_fmt", "bgr24", "-"],
                              stdout=subprocess.PIPE)
    salida = reel / "trabajo" / a.salida
    escritor = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}",
                                 "-r", fps_txt, "-i", "-", "-i", str(crudo), "-map", "0:v", "-map", "1:a",
                                 "-c:v", "libx264", "-preset", "medium", "-crf", "15", "-pix_fmt", "yuv420p",
                                 "-c:a", "copy", "-shortest", str(salida)], stdin=subprocess.PIPE)
    tam, i = ancho * alto * 3, 0
    while True:
        crudo_b = lector.stdout.read(tam)
        if len(crudo_b) < tam:
            break
        img = np.frombuffer(crudo_b, np.uint8).reshape(alto, ancho, 3)
        z, (ax, ay) = zoom_en(i / fps, tramos)
        cw, ch = ancho / z, alto / z
        # El ancla queda en el mismo lugar de la pantalla: x0 = ancla * (1 - 1/z), sin salirse del cuadro.
        x0 = min(max(ax * ancho * (1 - 1 / z), 0), ancho - cw)
        y0 = min(max(ay * alto * (1 - 1 / z), 0), alto - ch)
        # Primero se achica con INTER_AREA (sin aliasing al bajar de 4K) y después se corre con precisión de subpíxel.
        s = W / cw
        chico = cv2.resize(img, (round(ancho * s), round(alto * s)), interpolation=cv2.INTER_AREA)
        m = np.float32([[1, 0, -x0 * s], [0, 1, -y0 * s]])
        escritor.stdin.write(cv2.warpAffine(chico, m, (W, H), flags=cv2.INTER_LINEAR,
                                            borderMode=cv2.BORDER_REPLICATE).tobytes())
        i += 1
    escritor.stdin.close()
    escritor.wait()
    print(f"zoom: {i} cuadros -> {salida}")


if __name__ == "__main__":
    main()
