#!/usr/bin/env python3
"""Transiciones (overlay en modo Trama + su sonido) y música de fondo con ducking sobre la base.

Uso: python3 nucleo/transiciones.py <reel> [--base base_broll.mp4]
Lee <reel>/trabajo/transiciones.json:
    {"transiciones": [{"t": 10.59, "overlay": "assets/overlay.mp4", "desde": 7.0, "pico": 0.4, "dur": 1.2}],
     "sonido": {"archivo": "assets/sfx.mp3", "pico": 1.7, "db": -4.4},
     "musica": {"archivo": "assets/musica.m4a", "inicio": 0, "db": -20}}
"t" es el segundo del corte en la línea de tiempo del video; "pico" es dónde cae el destello dentro del tramo
del overlay, para que el destello coincida con el corte. Escribe <reel>/trabajo/base_final.mp4 a -14 LUFS.
"""
import argparse
import json
import subprocess
from pathlib import Path


def duracion(ruta):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                 str(ruta)], capture_output=True, text=True, check=True).stdout)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("reel")
    ap.add_argument("--base", default="base_broll.mp4")
    a = ap.parse_args()
    reel = Path(a.reel)
    trabajo = reel / "trabajo"
    conf = json.loads((trabajo / "transiciones.json").read_text())
    base = trabajo / a.base
    total = duracion(base)

    entradas = ["-i", str(base)]
    filtros, video, audios = [], "[0:v]", []
    n = 1
    for k, tr in enumerate(conf.get("transiciones", [])):
        inicio = tr["t"] - tr["pico"]
        entradas += ["-ss", str(tr["desde"]), "-t", str(tr["dur"]), "-i", str(reel / tr["overlay"])]
        filtros.append(f"[{n}:v]scale=1080:1920,fps=24000/1001,format=gbrp,"
                       f"setpts=PTS-STARTPTS+{inicio:.3f}/TB[ov{k}]")
        # Trama (screen): lo negro del overlay desaparece y solo suma la luz del destello. La mezcla va en RGB:
        # en YUV la trama también aclara los canales de color y todo sale magenta.
        filtros.append(f"{video}format=gbrp[bg{k}];[bg{k}][ov{k}]blend=all_mode=screen:eof_action=pass[v{k}]")
        video = f"[v{k}]"
        n += 1
        if "sonido" in conf:
            s = conf["sonido"]
            ms = max(0, round((tr["t"] - s["pico"]) * 1000))
            entradas += ["-i", str(reel / s["archivo"])]
            filtros.append(f"[{n}:a]aresample=48000,adelay={ms}|{ms},volume={s.get('db', -4.4)}dB[sx{k}]")
            audios.append(f"[sx{k}]")
            n += 1

    voz = "[0:a]"
    if "musica" in conf:
        m = conf["musica"]
        entradas += ["-ss", str(m.get("inicio", 0)), "-t", f"{total:.3f}", "-i", str(reel / m["archivo"])]
        filtros.append(f"[0:a]asplit=2[voz][clave]")
        filtros.append(f"[{n}:a]aresample=48000,volume={m.get('db', -20)}dB,afade=t=in:d=0.6,"
                       f"afade=t=out:st={total - 1.5:.3f}:d=1.5[mus]")
        # Ducking: la música baja cuando ella habla y sube en las pausas.
        filtros.append("[mus][clave]sidechaincompress=threshold=0.03:ratio=6:attack=20:release=300[musd]")
        voz = "[voz]"
        audios.append("[musd]")
        n += 1
    mezcla = f"{voz}{''.join(audios)}amix=inputs={1 + len(audios)}:duration=first:normalize=0,"
    filtros.append(mezcla + "loudnorm=I=-14:TP=-1.5:LRA=11[a]")

    salida = trabajo / "base_final.mp4"
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *entradas,
                    "-filter_complex", ";".join(filtros), "-map", video, "-map", "[a]",
                    "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "192k", "-ar", "48000", str(salida)], check=True)
    print(f"base con transiciones y música -> {salida}")


if __name__ == "__main__":
    main()
