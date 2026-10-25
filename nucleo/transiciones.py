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

    transiciones = conf.get("transiciones", [])
    if "en_cada_clip" in conf:
        # Regla de Sebas: la transición va en cada cambio de clip bruto. Se calcula sola desde edl.json.
        molde = conf["en_cada_clip"]
        cortes = json.loads((trabajo / "edl.json").read_text())["cortes"]
        t, transiciones = 0.0, []
        for previo, c in zip(cortes, cortes[1:]):
            t += previo["out"] - previo["in"]
            if c["clip"] != previo["clip"]:
                transiciones.append({**molde, "t": round(t, 3)})
        print("transiciones en:", ", ".join(f'{x["t"]:.2f}s' for x in transiciones))

    entradas = ["-i", str(base)]
    filtros, video, audios = [], "[0:v]", []
    n = 1
    for k, tr in enumerate(transiciones):
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

    # Efectos sueltos (whoosh en cambios de encuadre, "zoom in" en acercamientos rápidos...). Cada uno dice dónde va:
    # "cortes_mismo_clip" = cortes que no cambian de clip, "brolls" = entrada de cada b-roll, "golpes" = los golpes
    # de zoom de movimientos.json. El "pico" del sonido cae justo en ese segundo.
    cortes = json.loads((trabajo / "edl.json").read_text())["cortes"]
    inicios, t = [], 0.0
    for c in cortes:
        inicios.append(t)
        t += c["out"] - c["in"]
    for ef in conf.get("efectos", []):
        if ef["en"] == "cortes_mismo_clip":
            tiempos = [inicios[k] for k in range(1, len(cortes)) if cortes[k]["clip"] == cortes[k - 1]["clip"]]
        elif ef["en"] == "golpes":
            mov_f = trabajo / "movimientos.json"
            movs = json.loads(mov_f.read_text()) if mov_f.exists() else {}
            tiempos = [inicios[int(k)] + m["golpe_en"] for k, m in movs.items() if "golpe_en" in m]
        elif ef["en"] == "palabras":
            # Palabras clave: el golpe del sonido cae al empezar la palabra (índices de corte_check.json).
            palabras = json.loads((trabajo / "corte_check.json").read_text())["palabras"]
            tiempos = [palabras[i]["inicio"] for i in ef["palabras"]]
        elif ef["en"] == "brolls":
            palabras = json.loads((trabajo / "corte_check.json").read_text())["palabras"]
            brolls = json.loads((trabajo / "brolls.json").read_text())["brolls"]
            tiempos = [palabras[b["desde"]]["inicio"] - 0.05 for b in brolls]
        else:
            tiempos = ef.get("tiempos", [])
        for t in tiempos:
            ms = max(0, round((t - ef["pico"]) * 1000))
            entradas += ["-t", str(ef.get("dur", 10)), "-i", str(reel / ef["archivo"])]
            filtros.append(f"[{n}:a]aresample=48000,afade=t=out:st={max(0, ef.get('dur', 10) - 0.2)}:d=0.2,"
                           f"adelay={ms}|{ms},volume={ef.get('db', -4.4)}dB[ef{n}]")
            audios.append(f"[ef{n}]")
            n += 1
        print(f"{Path(ef['archivo']).name} en: " + ", ".join(f"{x:.2f}s" for x in tiempos))

    voz = "[0:a]"
    # Música: una pista ("musica") o varias por tramos ("musicas"), p. ej. tensión en el gancho y ritmo después.
    # Cada tramo: {"archivo", "inicio" (segundo de la pista), "desde"/"hasta" (segundos del video), "db",
    # "entrada"/"salida" (fundidos en s)}. "golpe_en_pista"+"golpe_en_video" alinean un golpe de compás de la
    # pista con un segundo del video (p. ej. la primera transición).
    musicas = conf.get("musicas") or ([{**conf["musica"], "desde": 0, "hasta": total}] if "musica" in conf else [])
    if musicas:
        partes = []
        for m in musicas:
            desde, hasta = m.get("desde", 0), min(m.get("hasta", total), total)
            inicio = m.get("inicio", 0)
            if "golpe_en_pista" in m:
                inicio = m["golpe_en_pista"] - (m["golpe_en_video"] - desde)
            ent, sal = m.get("entrada", 0.6), m.get("salida", 1.5)
            entradas += ["-ss", f"{inicio:.3f}", "-t", f"{hasta - desde:.3f}", "-i", str(reel / m["archivo"])]
            ms = round(desde * 1000)
            filtros.append(f"[{n}:a]aresample=48000,volume={m.get('db', -20)}dB,afade=t=in:d={ent},"
                           f"afade=t=out:st={max(0, hasta - desde - sal):.3f}:d={sal},adelay={ms}|{ms}[mus{n}]")
            partes.append(f"[mus{n}]")
            n += 1
        filtros.append(f"{''.join(partes)}amix=inputs={len(partes)}:duration=longest:normalize=0[mus]")
        filtros.append(f"[0:a]asplit=2[voz][clave]")
        # Ducking: la música baja cuando ella habla y sube en las pausas.
        filtros.append("[mus][clave]sidechaincompress=threshold=0.03:ratio=6:attack=20:release=300[musd]")
        voz = "[voz]"
        audios.append("[musd]")
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
