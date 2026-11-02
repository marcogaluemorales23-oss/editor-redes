#!/usr/bin/env python3
"""Corte multicámara: los MISMOS cortes de trabajo/edl.json (cámara A) aplicados a una segunda cámara sincronizada.

Uso: python3 nucleo/multicam.py <reel> --a crudos/C5510.MP4 --b crudos/C5323.MP4 --desfase 45.5044 [--girar-b 1]
                                [--plan AABAB...] [--crf 19] [--solo-pedazos]
- --desfase: segundo de A = segundo de B + desfase (se mide correlacionando el audio de las dos cámaras).
- --girar-b: transpose de ffmpeg para la cámara B (1 = 90° a la derecha) si grabó acostada sin marca de rotación.
- Si B es una copia rala de Drive (nucleo/drive_ralo.py, crudos/<B>.rangos.json), baja solo los bytes de
  cada corte (desde 0,6 s antes: un I cada 0,5 s) y los libera después (fallocate --punch-hole).
- Cada corte se codifica una sola vez (A y B por separado, mismos ajustes de x264) en trabajo/multicam/; las versiones
  se arman uniendo pedazos SIN recomprimir. El audio es siempre el de A (mismo largo exacto de cada corte).
Salidas: salida/<nombre>_camB.mp4 (todo B; donde B no grabó, A con un acercamiento de 1,3x)
         salida/<nombre>_intercalado.mp4 (cambia de cámara en cada corte, según --plan o alternando).
"""
import argparse
import csv
import json
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

X264 = ["-c:v", "libx264", "-preset", "medium", "-pix_fmt", "yuv420p", "-profile:v", "high", "-level", "5.2",
        "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-an"]
W, H = 2160, 3840


def correr(cmd):
    subprocess.run(cmd, check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("reel")
    ap.add_argument("--a", required=True)
    ap.add_argument("--b", required=True)
    ap.add_argument("--desfase", type=float, required=True)
    ap.add_argument("--girar-b", type=int)
    ap.add_argument("--plan", help="cámara por corte, p. ej. ABAB... (Z = A con acercamiento)")
    ap.add_argument("--crf", type=int, default=19)
    ap.add_argument("--nombre", default="corte")
    a = ap.parse_args()
    reel = Path(a.reel)
    t = reel / "trabajo"
    pdir = t / "multicam"
    pdir.mkdir(exist_ok=True)
    A, B = reel / a.a, reel / a.b
    fps = Fraction(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=r_frame_rate",
                                   "-of", "csv=p=0", str(A)], capture_output=True, text=True).stdout.strip().strip(","))
    durB = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(B)],
                                capture_output=True, text=True).stdout)
    cortes = json.loads((t / "edl.json").read_text())["cortes"]
    ralo = Path(str(B) + ".rangos.json").exists()
    if ralo:
        # Copia rala (nucleo/drive_ralo.py): tabla de paquetes (tiempo, byte, tamaño) para bajar solo cada corte.
        sys.path.insert(0, str(Path(__file__).parent))
        import drive_ralo
        tabla = t / f"paquetes_{B.stem}.csv"
        if not tabla.exists():
            tabla.write_text(subprocess.run(["ffprobe", "-v", "quiet", "-show_entries", "packet=stream_index,pts_time,size,pos",
                                             "-of", "csv=p=0", str(B)], capture_output=True, text=True).stdout)
        paquetes = [r for r in csv.reader(open(tabla)) if len(r) >= 4 and r[0] in "01" and r[1] not in ("", "N/A")]

    pedazos = []
    for k, c in enumerate(cortes):
        f0, f1 = round(c["in"] * fps), round(c["out"] * fps)
        n = f1 - f0
        tA = float(f0 / fps)
        pa = pdir / f"A_{k:02d}.mp4"
        pz = pdir / f"Z_{k:02d}.mp4"
        pb = pdir / f"B_{k:02d}.mp4"
        if not pa.exists():
            correr(["ffmpeg", "-v", "error", "-y", "-ss", f"{tA:.6f}", "-t", f"{n / float(fps) + 0.5:.6f}", "-i", str(A),
                    "-vf", f"trim=end_frame={n},setpts=PTS-STARTPTS,scale={W}:{H}", "-r", str(fps), "-crf", str(a.crf), *X264, str(pa)])
        tB = tA - a.desfase
        hay_b = tB - 0.6 >= 0 and tB + n / float(fps) <= durB - 0.1
        if not hay_b and not pz.exists():
            # "Cámara" Z: la misma A con un acercamiento de 1,3x anclado arriba (cara), para alternar donde B no existe.
            correr(["ffmpeg", "-v", "error", "-y", "-i", str(pa), "-vf",
                    f"crop=iw/1.3:ih/1.3:(iw-iw/1.3)/2:ih*0.08,scale={W}:{H}:flags=lanczos", "-r", str(fps),
                    "-crf", str(a.crf), *X264, str(pz)])
        if hay_b and not pb.exists():
            fB0 = round(tB * fps)
            ini = float(fB0 / fps)
            rango = None
            if ralo:
                sel = [(int(r[3]), int(r[2])) for r in paquetes if ini - 0.6 <= float(r[1]) <= ini + n / float(fps) + 0.3]
                rango = (min(p for p, s in sel), max(p + s for p, s in sel) - 1)
                drive_ralo.traer(B, *rango)
            giro = f",transpose={a.girar_b}" if a.girar_b is not None else ""
            # -v fatal: en la copia rala ffmpeg se queja de los bytes vacíos que ve al abrir el archivo (no se usan).
            correr(["ffmpeg", "-v", "fatal", "-y", "-seek2any", "1", "-ss", f"{ini - 0.6:.6f}", "-copyts", "-i", str(B),
                    "-vf", f"trim=start={ini - 0.5 / float(fps):.6f},trim=end_frame={n},setpts=PTS-STARTPTS{giro},"
                           f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}",
                    "-r", str(fps), "-crf", str(a.crf), *X264, str(pb)])
            if rango:
                drive_ralo.liberar(B, *rango)
        pedazos.append({"k": k, "n": n, "f0": f0, "A": pa, "Z": pz, "B": pb if hay_b else None})
        print(f"corte {k + 1}/{len(cortes)}: {n} cuadros, B {'sí' if hay_b else 'no grabó'}", flush=True)

    # Audio de A con el largo exacto de cada corte (como exportar_cortes.py).
    audio = pdir / "audio_A.wav"
    entradas, filtros = [], []
    for i, p in enumerate(pedazos):
        dur = p["n"] / float(fps)
        entradas += ["-ss", f"{float(p['f0'] / fps):.6f}", "-t", f"{dur + 0.5:.6f}", "-i", str(A)]
        filtros.append(f"[{i}:a]atrim=end={dur:.6f},asetpts=PTS-STARTPTS,afade=t=in:d=0.01,afade=t=out:st={max(0, dur - 0.01):.6f}:d=0.01[a{i}]")
    filtros.append("".join(f"[a{i}]" for i in range(len(pedazos))) + f"concat=n={len(pedazos)}:v=0:a=1[a]")
    correr(["ffmpeg", "-v", "error", "-y", *entradas, "-filter_complex", ";".join(filtros), "-map", "[a]", "-ac", "2", "-ar", "48000", str(audio)])

    def armar(nombre, eleccion):
        lista = pdir / f"{nombre}.txt"
        lista.write_text("".join(f"file '{p}'\n" for p in eleccion))
        salida = reel / "salida" / f"{a.nombre}_{nombre}.mp4"
        correr(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lista), "-i", str(audio),
                "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "320k", "-movflags", "+faststart", str(salida)])
        print(f"{nombre} -> {salida}")

    for p in pedazos:   # donde B no grabó y el plan pide B, va A con acercamiento (Z)
        if p["B"] is None and not p["Z"].exists():
            correr(["ffmpeg", "-v", "error", "-y", "-i", str(p["A"]), "-vf",
                    f"crop=iw/1.3:ih/1.3:(iw-iw/1.3)/2:ih*0.08,scale={W}:{H}:flags=lanczos", "-r", str(fps),
                    "-crf", str(a.crf), *X264, str(p["Z"])])
    armar("camB", [p["B"] or p["Z"] for p in pedazos])
    plan = a.plan or "".join("AB"[i % 2] for i in range(len(pedazos)))
    eleccion = []
    for p, cam in zip(pedazos, plan):
        if cam == "B" and p["B"] is None:
            cam = "Z" if (eleccion and eleccion[-1].name.startswith("A")) else "A"
        eleccion.append(p[cam])
    armar("intercalado", eleccion)
    print("plan usado:", "".join(e.name[0] for e in eleccion))


if __name__ == "__main__":
    main()
