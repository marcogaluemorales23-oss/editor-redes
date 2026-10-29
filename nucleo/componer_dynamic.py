#!/usr/bin/env python3
"""Compone el formato dynamic estilo vd2/vd4: video + paneles que bajan desde arriba + pantallas completas.

Uso: python3 nucleo/componer_dynamic.py <reel> --base base_limpia.mp4 --graficos graficos.mov
Lee <reel>/trabajo/capas.json:
    {"paneles": [[desde, hasta], ...], "alto_panel": 860, "bajar": 420, "transicion": 0.3,
     "blanco_y_negro": [[desde, hasta], ...]}
Mientras hay un panel arriba el video baja `bajar` px (la cara queda en la mitad de abajo, como vd4), con la misma
curva y los mismos tiempos con que baja el panel en Remotion. Las pantallas completas no necesitan nada aquí:
la capa de gráficos ya tapa todo. Escribe <reel>/trabajo/base_compuesta.mp4 (audio de la base, sin tocar).
Regla de Sebas: nada encima de la cara. Lo que va a la altura de la cara va en panel o en pantalla completa.
"""
import argparse
import json
import subprocess
from pathlib import Path


def suave(u):
    return f"(st(0,clip({u},0,1))*ld(0)*(3-2*ld(0)))"


def bajada(paneles, d, tr):
    """Expresión de ffmpeg (en t) de cuánto baja el video: 0 sin panel, d con panel, curva suave al entrar/salir."""
    partes = [f"between(t,{a:.3f},{b:.3f})*{suave(f'(t-{a:.3f})/{tr}')}*(1-{suave(f'(t-{b - tr:.3f})/{tr}')})"
              for a, b in paneles]
    return f"{d}*({'+'.join(partes) or '0'})"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("reel")
    ap.add_argument("--base", default="base_limpia.mp4")
    ap.add_argument("--graficos", default="graficos.mov")
    a = ap.parse_args()
    t = Path(a.reel) / "trabajo"
    capas = json.loads((t / "capas.json").read_text())
    tr = capas.get("transicion", 0.3)
    y = bajada(capas["paneles"], capas.get("bajar", 420), tr)
    bn = "+".join(f"between(t,{x:.3f},{z:.3f})" for x, z in capas.get("blanco_y_negro", [])) or "0"
    filtro = ";".join([
        f"[0:v]hue=s=0:enable='{bn}',eq=contrast=1.12:enable='{bn}'[v0]",
        "color=c=0x0E0E10:s=1080x1920:r=60[fondo]",
        f"[fondo][v0]overlay=x=0:y='{y}':eval=frame:shortest=1[v1]",
        "[1:v]format=rgba[g]",
        "[v1][g]overlay=0:0,format=yuv420p[v]",
    ])
    salida = t / "base_compuesta.mp4"
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(t / a.base),
                    "-i", str(t / a.graficos), "-filter_complex", filtro, "-map", "[v]", "-map", "0:a",
                    "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-c:a", "copy", str(salida)], check=True)
    print(f"compuesto -> {salida}")


if __name__ == "__main__":
    main()
