#!/usr/bin/env python3
"""Separa la voz de la música y los efectos de un video de referencia y lo dibuja para poder "verlo".

Uso: python3 nucleo/escuchar.py <video.mp4>
Necesita <carpeta del video>/<nombre>/palabras.json (nucleo/auditar.py). Escribe ahí mismo:
    voz.wav, fondo.wav   pistas separadas con Demucs (fondo = música + efectos de sonido)
    sonido_N.png         tiras de 10 s: espectrograma del fondo, nivel de voz y de fondo, y las palabras encima.
                         Un whoosh se ve como un barrido de ruido que sube; un golpe, una raya vertical
                         fuerte con graves; un ding, una línea horizontal aguda que se apaga.
    sonido.json         nivel de fondo cada 0,1 s (dB) y los golpes (picos bruscos del fondo) con su palabra
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

SR = 22050
TIRA_S = 10
PASO_S = 0.1


def leer(wav):
    crudo = subprocess.run(["ffmpeg", "-v", "error", "-i", str(wav), "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                           capture_output=True, check=True).stdout
    return np.frombuffer(crudo, np.float32)


def separar(video, dest):
    if (dest / "fondo.wav").exists():
        return
    tmp = dest / "demucs"
    subprocess.run([sys.executable, "-m", "demucs", "--two-stems", "vocals", "-n", "htdemucs", "-o", str(tmp),
                    str(video)], check=True, capture_output=True)
    carpeta = next(tmp.glob("htdemucs/*"))
    (carpeta / "vocals.wav").rename(dest / "voz.wav")
    (carpeta / "no_vocals.wav").rename(dest / "fondo.wav")
    subprocess.run(["rm", "-rf", str(tmp)], check=True)


def nivel_db(x):
    n = int(PASO_S * SR)
    bloques = x[: len(x) // n * n].reshape(-1, n)
    return 20 * np.log10(np.sqrt((bloques ** 2).mean(1)) + 1e-6)


def golpes(fondo, palabras):
    """Picos bruscos del fondo: subida de más de 8 dB en 50 ms por encima de su propio nivel reciente."""
    n = int(0.05 * SR)
    env = 20 * np.log10(np.sqrt((fondo[: len(fondo) // n * n].reshape(-1, n) ** 2).mean(1)) + 1e-6)
    eventos, ultimo = [], -1.0
    for i in range(4, len(env)):
        base = np.median(env[max(0, i - 20):i])
        t = i * 0.05
        if env[i] - base > 8 and env[i] > -40 and t - ultimo > 0.3:
            cerca = min(palabras, key=lambda p: abs(p["inicio"] - t), default=None)
            eventos.append({"t": round(t, 2), "sube_db": round(float(env[i] - base), 1),
                            "palabra": cerca["texto"] if cerca else "", "palabra_t": cerca["inicio"] if cerca else None})
            ultimo = t
    return eventos


def dibujar(fondo, voz, palabras, eventos, dest):
    total = len(fondo) / SR
    nv, nf = nivel_db(voz), nivel_db(fondo)
    tiempos = np.arange(len(nf)) * PASO_S
    for k in range(int(np.ceil(total / TIRA_S))):
        a, b = k * TIRA_S, min((k + 1) * TIRA_S, total)
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 6), sharex=True, gridspec_kw={"height_ratios": [3, 1]})
        trozo = fondo[int(a * SR):int(b * SR)]
        ax1.specgram(trozo, NFFT=1024, Fs=SR, noverlap=768, cmap="magma", vmin=-110, xextent=(a, b))
        ax1.set_ylim(0, 11000)
        ax1.set_ylabel("Hz (fondo)")
        for p in palabras:
            if a <= p["inicio"] < b:
                ax1.text(p["inicio"], 10500, p["texto"], color="white", fontsize=9, rotation=90, va="top")
                ax1.axvline(p["inicio"], color="white", alpha=0.15, lw=0.5)
        for e in eventos:
            if a <= e["t"] < b:
                ax1.axvline(e["t"], color="cyan", lw=1.2)
        m = (tiempos >= a) & (tiempos < b)
        ax2.plot(tiempos[m], nv[m], color="tab:blue", label="voz")
        ax2.plot(tiempos[m], nf[m], color="tab:orange", label="fondo")
        ax2.set_ylim(-70, 0)
        ax2.set_ylabel("dB")
        ax2.legend(loc="upper right", fontsize=8)
        ax2.set_xlabel("segundos")
        ax2.set_xticks(np.arange(a, b + 0.01, 0.5), minor=True)
        ax2.grid(True, which="both", alpha=0.3)
        fig.tight_layout()
        fig.savefig(dest / f"sonido_{k + 1}.png", dpi=80)
        plt.close(fig)


def main():
    video = Path(sys.argv[1])
    dest = video.with_suffix("")
    palabras = json.loads((dest / "palabras.json").read_text())
    separar(video, dest)
    fondo, voz = leer(dest / "fondo.wav"), leer(dest / "voz.wav")
    eventos = golpes(fondo, palabras)
    (dest / "sonido.json").write_text(json.dumps({
        "paso_s": PASO_S, "fondo_db": [round(float(v), 1) for v in nivel_db(fondo)],
        "voz_db": [round(float(v), 1) for v in nivel_db(voz)], "golpes": eventos}, ensure_ascii=False))
    dibujar(fondo, voz, palabras, eventos, dest)
    print(f"{video.name}: {len(eventos)} golpes en el fondo -> {dest}")


if __name__ == "__main__":
    main()
