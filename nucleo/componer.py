#!/usr/bin/env python3
"""Compone el formato Reel de negocio: video + capas de Remotion + persona recortada.

Uso: python3 nucleo/componer.py <reel> [--hasta SEGUNDOS]
Lee de <reel>/trabajo/:
    base.mp4         video cortado y encuadrado (sin textos)
    silueta.mkv      máscara de la persona (nucleo/silueta.py)
    detras.mov       capa transparente que va detrás de la persona (Remotion: NegocioDetras)
    delante.mov      capa transparente que va delante (Remotion: NegocioDelante)
    planos.json      {"planos": [{"tipo": "A"|"B"|"C", "desde": s, "hasta": s}, ...]}
Escribe <reel>/trabajo/base_compuesta.mp4 (con el audio de la base, sin tocar).

Orden de capas en cada cuadro:
    B y C: el video baja 480 px (la cara queda en la mitad de abajo) y el panel de "delante" tapa la de arriba.
    A:     video completo -> capa "detrás" (tarjetas en la pared) -> la persona recortada encima.
    Siempre: capa "delante" (paneles y títulos) al final.
"""
import argparse
import json
import subprocess
from pathlib import Path

BAJAR_PX = 480


def entre(tramos):
    return "+".join(f"between(t,{a:.3f},{b - 0.001:.3f})" for a, b in tramos) or "0"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("reel")
    ap.add_argument("--hasta", type=float, help="componer solo hasta este segundo (render de prueba)")
    a = ap.parse_args()
    t = Path(a.reel) / "trabajo"
    planos = json.loads((t / "planos.json").read_text())["planos"]
    partidos = [(p["desde"], p["hasta"]) for p in planos if p["tipo"] in ("B", "C")]
    completos = [(p["desde"], p["hasta"]) for p in planos if p["tipo"] == "A"]
    limite = ["-t", str(a.hasta)] if a.hasta else []
    filtro = ";".join([
        "[0:v]split=3[v][paraBajar][paraPersona]",
        f"[paraBajar]crop=1080:{1920 - BAJAR_PX}:0:0,pad=1080:1920:0:{BAJAR_PX}:0x0D0F13[bajado]",
        f"[v][bajado]overlay=0:0:enable='{entre(partidos)}'[v1]",
        "[2:v]format=rgba[detras]",
        f"[v1][detras]overlay=0:0:enable='{entre(completos)}'[v2]",
        "[1:v]format=gray[mascara]",
        "[paraPersona][mascara]alphamerge[persona]",
        f"[v2][persona]overlay=0:0:enable='{entre(completos)}'[v3]",
        "[3:v]format=rgba[delante]",
        "[v3][delante]overlay=0:0,format=yuv420p[out]",
    ])
    salida = t / "base_compuesta.mp4"
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *limite, "-i", str(t / "base.mp4"),
                    *limite, "-i", str(t / "silueta.mkv"), *limite, "-i", str(t / "detras.mov"),
                    *limite, "-i", str(t / "delante.mov"), "-filter_complex", filtro,
                    "-map", "[out]", "-map", "0:a", "-c:v", "libx264", "-preset", "medium", "-crf", "17",
                    "-c:a", "copy", *limite, str(salida)], check=True)
    print(f"compuesto -> {salida}")


if __name__ == "__main__":
    main()
