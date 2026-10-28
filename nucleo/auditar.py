#!/usr/bin/env python3
"""Prepara un video de referencia para auditarlo: qué se dice, dónde corta y cómo se ve cada plano.

Uso: python3 nucleo/auditar.py <video.mp4> [--sin-transcribir]
Escribe en <carpeta del video>/<nombre>/:
    palabras.json   transcripción palabra por palabra (Whisper medium)
    cortes.json     segundos donde cambia el plano (detector de escena de ffmpeg)
    gancho.jpg      los primeros 4 s cada 0,25 s (el gancho se mira con lupa)
    planos_N.jpg    un cuadro por segundo y uno después de cada corte, en hojas de 32
    linea.txt       línea de tiempo: cortes y frases juntos, para leer el video de corrido
Las referencias son de otros creadores: viven en referencias/ y no van a git.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

UMBRAL_ESCENA = 0.22
GANCHO_S, GANCHO_PASO = 4.0, 0.25
POR_HOJA = 32
FUENTE = Path(__file__).parents[1] / "motion/public/fuentes/Inter-Bold.ttf"


def duracion(video):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                 video], capture_output=True, text=True, check=True).stdout.strip())


def cortes(video):
    """Cambios de plano en la mitad de arriba y en la de abajo por separado: en pantalla dividida
    suele cambiar solo una mitad y el detector sobre el cuadro entero no lo ve."""
    encontrados = []
    for zona, recorte in (("arriba", "crop=iw:ih/2:0:0"), ("abajo", "crop=iw:ih/2:0:ih/2")):
        salida = subprocess.run(["ffmpeg", "-nostdin", "-i", video, "-vf",
                                 f"{recorte},select='gt(scene,{UMBRAL_ESCENA})',showinfo", "-an", "-f", "null", "-"],
                                capture_output=True, text=True).stderr
        encontrados += [(round(float(t), 3), zona) for t in re.findall(r"pts_time:([\d.]+)", salida)]
    juntos = []
    for t, zona in sorted(encontrados):
        if juntos and t - juntos[-1]["t"] < 0.1:
            if zona not in juntos[-1]["zona"]:
                juntos[-1]["zona"] = "todo"
            continue
        juntos.append({"t": t, "zona": zona})
    return juntos


def hoja(video, tiempos, destino, columnas):
    """Un cuadro por tiempo, con el segundo escrito debajo, en una cuadrícula."""
    tmp = destino.with_suffix("")
    tmp.mkdir(exist_ok=True)
    for i, t in enumerate(tiempos):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.3f}", "-i", video, "-frames:v", "1", "-vf",
                        f"scale=240:-2,pad=iw:ih+34:0:0:white,drawtext=fontfile={FUENTE}:text='{t:.2f}'"
                        f":x=(w-tw)/2:y=h-28:fontsize=22", str(tmp / f"{i:03d}.png")], check=True)
    filas = -(-len(tiempos) // columnas)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", "1", "-i", str(tmp / "%03d.png"), "-vf",
                    f"tile={columnas}x{filas}:padding=6:margin=6:color=white", "-frames:v", "1", "-q:v", "3",
                    str(destino)], check=True)
    for f in tmp.iterdir():
        f.unlink()
    tmp.rmdir()


def frases(palabras, pausa=0.35):
    grupo = []
    for p in palabras:
        if grupo and p["inicio"] - grupo[-1]["fin"] > pausa:
            yield grupo
            grupo = []
        grupo.append(p)
    if grupo:
        yield grupo


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--sin-transcribir", action="store_true")
    a = ap.parse_args()
    video = Path(a.video)
    dest = video.with_suffix("")
    dest.mkdir(exist_ok=True)
    total = duracion(str(video))

    lista = cortes(str(video))
    (dest / "cortes.json").write_text(json.dumps({"duracion_s": round(total, 3), "cortes": lista}))

    gancho = [round(i * GANCHO_PASO, 2) for i in range(int(GANCHO_S / GANCHO_PASO))]
    hoja(str(video), gancho, dest / "gancho.jpg", 8)
    # Un cuadro por segundo más uno justo después de cada corte: muchas animaciones cambian sin corte.
    muestras = {round(float(i), 2) for i in range(int(total))} | {round(c["t"] + 0.15, 2) for c in lista}
    tomas = sorted(t for t in muestras if t < total - 0.05)
    for n in range(0, len(tomas), POR_HOJA):
        hoja(str(video), tomas[n:n + POR_HOJA], dest / f"planos_{n // POR_HOJA + 1}.jpg", 8)

    palabras = []
    if not a.sin_transcribir:
        from transcribir import transcribir
        palabras = transcribir(str(video), "medium")["palabras"]
        (dest / "palabras.json").write_text(json.dumps(palabras, ensure_ascii=False, indent=1))
    elif (dest / "palabras.json").exists():
        palabras = json.loads((dest / "palabras.json").read_text())

    eventos = [(c["t"], f"--- corte {c['zona']} (plano {i + 2})") for i, c in enumerate(lista)]
    eventos += [(g[0]["inicio"], f'{g[0]["inicio"]:6.2f}-{g[-1]["fin"]:6.2f}  ' + " ".join(p["texto"] for p in g))
                for g in frases(palabras)]
    lineas = [f"{video.name}: {total:.1f} s, {len(lista) + 1} planos, {len(lista) / total * 60:.0f} cortes por minuto"]
    lineas += [f"{t:6.2f}  {texto}" if texto.startswith("---") else texto for t, texto in sorted(eventos)]
    (dest / "linea.txt").write_text("\n".join(lineas) + "\n")
    print(f"{video.name}: {len(lista) + 1} planos, {len(palabras)} palabras -> {dest}")


if __name__ == "__main__":
    main()
