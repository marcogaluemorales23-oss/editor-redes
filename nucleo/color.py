#!/usr/bin/env python3
"""Corrección de color suave, toma por toma (pedido de Sebas: "que se vea mejor pero suave, no tan exagerado").

Uso: python3 nucleo/color.py <reel> [--base base_adobe.mp4] [--salida base_color.mp4] [--fuerza 1.0] [--hoja]
Mide cada tramo de trabajo/encuadre_tramos.json (cada toma tiene su luz: cocina, cuarto, pasillo) y corrige:
1. Balance de blancos: promedio de las superficies casi grises (paredes, techo) -> la mitad del camino a neutro,
   como mucho ±6 % por canal. No se busca blanco perfecto: un poco de calidez se ve natural.
2. Niveles: negros que no llegan a negro se bajan un poco. Los blancos NO se estiran.
3. Brillo: los medios se ajustan para que el brillo medio quede igual o un poco más bajo que el original
   (--brillo 0.97). Corrección de Sebas: la primera versión subía blancos y medios y "se veía muy brillante".
4. Contraste: curva en S suave (±2 % en los cuartos).
5. Saturación: hacia ~0,34 de saturación media, entre +8 % y +18 %, pero SOLO fuera de la piel (verdes, cianes,
   azules, magentas); los rojos bajan 5 %. El balance de blancos nunca quita verde ni agrega rojo.
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


def ajustes(m, fuerza, y, brillo):
    g = np.array(m["gris"])
    ganancia = np.clip(1 + (g.mean() / g - 1) * 0.5 * fuerza, 0.94, 1.06)
    # Nunca hacia magenta/rojo: con menos verde o más rojo la piel se ve irritada ("parezco un indigente", Sebas).
    ganancia[0] = min(ganancia[0], 1.0)
    ganancia[1] = max(ganancia[1], 1.0)
    negro = min(0.06, max(0.0, (m["p1"] - 0.02) * 0.6)) * fuerza
    blanco = 1.0
    sat = float(np.clip(1 + (0.34 - m["sat"]) * 0.8, 1.08, 1.18))
    sat = 1 + (sat - 1) * fuerza
    a = {"ganancia": [round(float(v), 4) for v in ganancia], "negro": round(negro, 4), "blanco": blanco,
         "medio": 0.0, "saturacion": round(sat, 4), "contraste": round(0.02 * fuerza, 4)}
    # Medios que dejan el brillo medio en `brillo` x el original (la S y los niveles no deben aclarar la toma).
    meta = y.mean() * brillo
    a["medio"] = round(float(min(np.arange(-0.12, 0.031, 0.005), key=lambda md: abs(aplicar(y, {**a, "medio": md}).mean() - meta))), 4)
    return a


def aplicar(x, a):
    """La curva de niveles + medios + S (vale para un número o un arreglo)."""
    v = np.clip((x - a["negro"]) / (a["blanco"] - a["negro"]), 0, 1)
    v = v + a["medio"] * 4 * v * (1 - v)                    # sube/baja los medios, extremos quietos
    return np.clip(v - a["contraste"] * np.sin(2 * np.pi * v), 0, 1)  # S: baja 1/4, sube 3/4


def curva(a):
    """Niveles + medios + S suave en una sola curva (puntos para el filtro curves de ffmpeg)."""
    xs = [0, 0.1, 0.25, 0.4, 0.5, 0.6, 0.75, 0.9, 1]
    return " ".join(f"{x}/{float(aplicar(x, a)):.4f}" for x in xs)


def filtro(a):
    r, g, b = a["ganancia"]
    # La saturación sube en todo MENOS en la piel (rojos y amarillos); los rojos incluso bajan un poco para calmar
    # manchas y rojeces. Subirla pareja ponía la frente naranja y roja.
    return (f"colorchannelmixer=rr={r}:gg={g}:bb={b},curves=all='{curva(a)}',"
            f"huesaturation=saturation={a['saturacion'] - 1:.4f}:colors=g+c+b+m,"
            f"huesaturation=saturation=-0.05:colors=r")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("reel")
    ap.add_argument("--base", default="base_adobe.mp4")
    ap.add_argument("--salida", default="base_color.mp4")
    ap.add_argument("--fuerza", type=float, default=1.0)
    ap.add_argument("--hoja", action="store_true")
    ap.add_argument("--brillo", type=float, default=0.97, help="brillo medio final / original")
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
        img = cuadros(base, tr["desde"], tr["hasta"])
        m = medir(img)
        y = (0.2126 * img[..., 0] + 0.7152 * img[..., 1] + 0.0722 * img[..., 2])[:, ::4, ::4].ravel()
        aj = ajustes(m, a.fuerza, y, a.brillo)
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
