#!/usr/bin/env python3
"""Corrección de color suave, toma por toma (pedido de Sebas: "que se vea mejor pero suave, no tan exagerado").

Uso: python3 nucleo/color.py <reel> [--base base_adobe.mp4] [--salida base_color.mp4] [--fuerza 1.0] [--hoja]
Mide cada tramo de trabajo/encuadre_tramos.json (cada toma tiene su luz: cocina, cuarto, pasillo) y corrige:
1. Balance de blancos: promedio de las superficies casi grises (paredes, techo) -> la mitad del camino a neutro,
   como mucho ±6 % por canal. No se busca blanco perfecto: un poco de calidez se ve natural.
2. Niveles: negros que no llegan a negro se bajan un poco y blancos apagados se suben un poco (nunca se queman).
3. Medios: si la toma quedó oscura, la curva sube un poco los medios (piel más viva).
4. Contraste: curva en S suave (±3 % en los cuartos).
5. Saturación: hacia ~0,34 de saturación media, entre +8 % y +18 % (la primera prueba, +4..14 %, casi no se notaba).
Todo con fuerza ajustable (--fuerza 0.5 = la mitad). Corta por cuadros exactos (trim + concat), el audio se copia.
Escribe trabajo/<salida>, trabajo/color.json (medidas y ajustes) y con --hoja trabajo/color_antes_despues.jpg.
Va después de montar.py / la voz limpia, y ANTES de silueta.py y componer (el recorte debe salir ya corregido).
"""
import argparse
import json
import subprocess
from pathlib import Path

import numpy as np

W, H = 270, 480


def cuadros(video, desde, hasta, paso=0.2):
    """Cuadros chicos (RGB 0..1) cada `paso` segundos dentro del tramo."""
    out = []
    t = desde + 0.05
    while t < hasta - 0.03:
        crudo = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", str(video), "-frames:v", "1",
                                "-vf", f"scale={W}:{H}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                               capture_output=True).stdout
        if len(crudo) == W * H * 3:
            out.append(np.frombuffer(crudo, np.uint8).reshape(H, W, 3) / 255.0)
        t += paso
    return np.stack(out)


def medir(img):
    r, g, b = img[..., 0], img[..., 1], img[..., 2]
    y = 0.2126 * r + 0.7152 * g + 0.0722 * b
    mx, mn = img.max(-1), img.min(-1)
    sat = np.where(mx > 0.02, (mx - mn) / np.maximum(mx, 1e-6), 0)
    gris = (y > 0.25) & (y < 0.85) & (sat < 0.25)
    rgb_gris = img[gris].mean(0) if gris.sum() > 500 else np.array([0.5, 0.5, 0.5])
    return {"p1": float(np.percentile(y, 1)), "p50": float(np.percentile(y, 50)), "p99": float(np.percentile(y, 99)),
            "sat": float(sat.mean()), "gris": [float(v) for v in rgb_gris]}


def ajustes(m, fuerza):
    g = np.array(m["gris"])
    ganancia = np.clip(1 + (g.mean() / g - 1) * 0.5 * fuerza, 0.94, 1.06)
    negro = min(0.06, max(0.0, (m["p1"] - 0.02) * 0.6)) * fuerza
    blanco = 1.0 if m["p99"] >= 0.97 else max(0.88, 1 - (1 - m["p99"]) * 0.6 * fuerza)
    medio = float(np.clip((0.45 - m["p50"]) * 0.3, -0.03, 0.05)) * fuerza
    sat = float(np.clip(1 + (0.34 - m["sat"]) * 0.8, 1.08, 1.18))
    sat = 1 + (sat - 1) * fuerza
    return {"ganancia": [round(float(v), 4) for v in ganancia], "negro": round(negro, 4), "blanco": round(blanco, 4),
            "medio": round(medio, 4), "saturacion": round(sat, 4), "contraste": round(0.03 * fuerza, 4)}


def curva(a):
    """Niveles + medios + S suave en una sola curva (puntos para el filtro curves de ffmpeg)."""
    def f(x):
        v = np.clip((x - a["negro"]) / (a["blanco"] - a["negro"]), 0, 1)
        v = v + a["medio"] * 4 * v * (1 - v)                    # sube/baja los medios, extremos quietos
        return float(np.clip(v - a["contraste"] * np.sin(2 * np.pi * v), 0, 1))  # S: baja 1/4, sube 3/4
    xs = [0, 0.1, 0.25, 0.4, 0.5, 0.6, 0.75, 0.9, 1]
    return " ".join(f"{x}/{f(x):.4f}" for x in xs)


def filtro(a):
    r, g, b = a["ganancia"]
    return (f"colorchannelmixer=rr={r}:gg={g}:bb={b},curves=all='{curva(a)}',"
            f"eq=saturation={a['saturacion']}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("reel")
    ap.add_argument("--base", default="base_adobe.mp4")
    ap.add_argument("--salida", default="base_color.mp4")
    ap.add_argument("--fuerza", type=float, default=1.0)
    ap.add_argument("--hoja", action="store_true")
    a = ap.parse_args()
    t = Path(a.reel) / "trabajo"
    base = t / a.base
    fps_txt = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                              "stream=r_frame_rate", "-of", "csv=p=0", str(base)], capture_output=True,
                             text=True).stdout.strip()
    n, d = (int(v) for v in fps_txt.split("/"))
    fps = n / d
    tramos = json.loads((t / "encuadre_tramos.json").read_text())
    registro, partes = [], []
    for i, tr in enumerate(tramos):
        m = medir(cuadros(base, tr["desde"], tr["hasta"]))
        aj = ajustes(m, a.fuerza)
        registro.append({"desde": tr["desde"], "hasta": tr["hasta"], "medida": m, "ajuste": aj})
        f0, f1 = round(tr["desde"] * fps), round(tr["hasta"] * fps)
        partes.append(f"[s{i}]trim=start_frame={f0}:end_frame={f1},setpts=PTS-STARTPTS,{filtro(aj)}[c{i}]")
        print(f"tramo {i + 1}/{len(tramos)}: medios {m['p50']:.2f}, sat {m['sat']:.2f} -> "
              f"sat x{aj['saturacion']}, negro {aj['negro']}, blanco {aj['blanco']}, medios {aj['medio']:+}, "
              f"rgb {aj['ganancia']}")
    k = len(tramos)
    grafo = ";".join([f"[0:v]split={k}" + "".join(f"[s{i}]" for i in range(k))] + partes +
                     ["".join(f"[c{i}]" for i in range(k)) + f"concat=n={k}:v=1:a=0,format=yuv420p[v]"])
    salida = t / a.salida
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(base), "-filter_complex", grafo,
                    "-map", "[v]", "-map", "0:a", "-c:v", "libx264", "-preset", "medium", "-crf", "16",
                    "-r", fps_txt, "-c:a", "copy", str(salida)], check=True)
    (t / "color.json").write_text(json.dumps(registro, indent=1))
    print(f"color -> {salida}")
    if a.hoja:
        hoja(t, base, salida, tramos)


def hoja(t, antes, despues, tramos):
    """Antes (arriba) / después (abajo), un cuadro por toma."""
    tmp = t / "color_hoja"
    tmp.mkdir(exist_ok=True)
    fuente = Path(__file__).resolve().parent.parent / "motion/public/fuentes/Inter-Bold.ttf"
    lista = []
    for i, tr in enumerate(x for x in tramos if x["hasta"] - x["desde"] > 1.0):
        s = (tr["desde"] + tr["hasta"]) / 2
        for nombre, v in (("antes", antes), ("despues", despues)):
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{s:.3f}", "-i", str(v), "-frames:v", "1", "-vf",
                            f"scale=300:533,drawtext=fontfile={fuente}:text='{nombre}':x=12:y=12:fontsize=26:"
                            f"fontcolor=white:box=1:boxcolor=black@0.6:boxborderw=6",
                            str(tmp / f"{nombre}_{i:02d}.png")], check=True)
        lista.append(i)
    entradas, cols = [], []
    for i in lista:
        entradas += ["-i", str(tmp / f"antes_{i:02d}.png"), "-i", str(tmp / f"despues_{i:02d}.png")]
    k = len(lista)
    g = ";".join(f"[{2 * j}:v][{2 * j + 1}:v]vstack[col{j}]" for j in range(k))
    g += ";" + "".join(f"[col{j}]" for j in range(k)) + f"hstack={k}"
    subprocess.run(["ffmpeg", "-v", "error", "-y", *entradas, "-filter_complex", g, "-frames:v", "1",
                    str(t / "color_antes_despues.jpg")], check=True)
    print(f"hoja -> {t / 'color_antes_despues.jpg'}")


if __name__ == "__main__":
    main()
