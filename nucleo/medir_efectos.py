#!/usr/bin/env python3
"""Mide cada efecto de sonido contra la voz que suena alrededor (regla de Sebas: la voz siempre manda).

Uso: python3 nucleo/medir_efectos.py <reel> --base base_v2.mp4
Lee <reel>/trabajo/transiciones.json ("efectos"), arma la pista de efectos con sus tiempos y volúmenes, y compara
el volumen máximo de cada efecto (ventana de 400 ms) con el nivel NORMAL de la voz hablando en todo el video (los
efectos suelen caer en pausas o cortes, así que la voz de ese instante no sirve de referencia).
Referencia aprobada por Sebas (prueba-02 v2): efectos entre 1,5 y 3 dB bajo la voz, golpes (impacto) parejos con ella.
Marca "ALTO" lo que pase la voz (hay que bajarle el "db" en transiciones.json) y "justo" lo que quede a menos de 1,5 dB.
"""
import argparse
import json
import subprocess
from pathlib import Path

import numpy as np

SR = 48000
ALTO_DB = 0.5    # más fuerte que la voz (con 0,5 dB de tolerancia): hay que bajarlo
JUSTO_DB = -1.5  # entre esto y la voz: se puede dejar, pero revisar


def leer(ruta, t=None):
    cmd = ["ffmpeg", "-v", "error", "-i", str(ruta)] + (["-t", str(t)] if t else []) + \
          ["-ac", "1", "-ar", str(SR), "-f", "f32le", "-"]
    return np.frombuffer(subprocess.run(cmd, capture_output=True).stdout, np.float32).astype(np.float64)


def db(x):
    return 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-9)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("reel")
    ap.add_argument("--base", default="base_broll.mp4")
    a = ap.parse_args()
    reel = Path(a.reel)
    conf = json.loads((reel / "trabajo" / "transiciones.json").read_text())
    voz = leer(reel / "trabajo" / a.base)
    efectos, eventos = np.zeros_like(voz), []
    for e in conf.get("efectos", []):
        s = leer(reel / e["archivo"], e.get("dur")) * 10 ** (e.get("db", -4.4) / 20)
        for t in e.get("tiempos", []):
            i = int(max(0.0, t - e["pico"]) * SR)
            trozo = s[:max(0, len(efectos) - i)]
            efectos[i:i + len(trozo)] += trozo
            eventos.append((t, Path(e["archivo"]).name))
    W, paso = int(0.4 * SR), int(0.05 * SR)
    ventanas = np.array([db(voz[k:k + W]) for k in range(0, len(voz) - W, paso)])
    habla = float(np.median(ventanas[ventanas > -40]))
    print(f"voz hablando (mediana): {habla:.1f} dB")
    altos = 0
    for t, nombre in sorted(eventos):
        i = int(t * SR)
        pico = max(db(efectos[k:k + W]) for k in range(max(0, i - int(0.6 * SR)), i + int(0.8 * SR), paso))
        dif = pico - habla
        aviso = "  ALTO" if dif > ALTO_DB else "  justo" if dif > JUSTO_DB else ""
        altos += aviso == "  ALTO"
        print(f"{t:6.2f}s  {nombre:22s} efecto {pico:6.1f} dB | {dif:+5.1f} dB vs voz{aviso}")
    print(f"{altos} efecto(s) más fuertes que la voz: bajarlos" if altos else "ningún efecto pasa la voz")


if __name__ == "__main__":
    main()
