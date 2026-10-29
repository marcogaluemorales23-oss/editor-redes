#!/usr/bin/env python3
"""Limpia la voz de la base (como el "Enhance" de Adobe Podcast, pero en el servidor): quita el ruido del cuarto sin
cambiar el tono.

Uso: python3 nucleo/limpiar_voz.py <reel> [--base base.mp4] [--salida base_limpia.mp4]
1. Demucs (htdemucs) separa la voz de todo lo demás (ruido del cuarto, ventilador, eco lejano).
2. Pasa-altos a 75 Hz (golpes y zumbido grave), reductor de ruido FFT suave y una compuerta con rango limitado:
   en las pausas el ruido baja, pero no se va a silencio absoluto (sonaría a corte).
No toca la ecualización de la voz: el tono queda igual. Prueba-01: piso de ruido -26,7 -> -34 dB, voz igual.
Va después de montar.py y antes de componer/transiciones.py. La imagen se copia sin recodificar.
"""
import argparse
import shutil
import subprocess
import sys
from pathlib import Path

FILTRO = ("highpass=f=75,afftdn=nr=12:nf=-42:tn=1,"
          "agate=threshold=0.012:ratio=2.5:attack=5:release=180:range=0.3")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("reel")
    ap.add_argument("--base", default="base.mp4")
    ap.add_argument("--salida", default="base_limpia.mp4")
    a = ap.parse_args()
    trabajo = Path(a.reel) / "trabajo"
    base = trabajo / a.base
    tmp = trabajo / "limpieza"
    tmp.mkdir(exist_ok=True)
    wav = tmp / "voz.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(base), "-vn", "-ac", "2", "-ar", "44100", str(wav)],
                   check=True)
    subprocess.run([sys.executable, "-m", "demucs", "--two-stems", "vocals", "-n", "htdemucs", "-o", str(tmp),
                    str(wav)], check=True, capture_output=True)
    voz = tmp / "htdemucs" / "voz" / "vocals.wav"
    salida = trabajo / a.salida
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(base), "-i", str(voz), "-map", "0:v", "-map", "1:a",
                    "-af", FILTRO + ",loudnorm=I=-14:TP=-1.5:LRA=11", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                    "-ar", "48000", "-shortest", str(salida)], check=True)
    shutil.rmtree(tmp)
    print(f"voz limpia -> {salida}")


if __name__ == "__main__":
    main()
