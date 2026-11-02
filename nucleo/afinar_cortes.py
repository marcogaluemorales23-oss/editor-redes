#!/usr/bin/env python3
"""Afina un corte al milisegundo (pedido de Sebas: "muy detallista y preciso", sin silencios de más).

Uso: python3 nucleo/afinar_cortes.py <reel> --crudo crudos/C5510.MP4 [--quieto 3]
Lee <reel>/trabajo/edl.json con los tramos elegidos a grandes rasgos ({"in", "out", "texto"}, segundos del crudo),
guarda una copia en edl_bruto.json y reescribe edl.json afinado. Después: nucleo/exportar_cortes.py.
Por cada tramo:
1. Busca los pedazos de voz reales (energía en ventanas de 10 ms, umbral -40 dB) y TRANSCRIBE CADA PEDAZO por
   separado. Así aparecen los arranques en falso ("Lo-… Lo importante") que en la transcripción completa se pierden.
   Los pedazos muy cortos (< 0,35 s) aislados al principio o al final del tramo se sacan solos (arranque en falso);
   igual revisar la lista que imprime: si algo más no es parte de la frase, se corrige el "in"/"out" del tramo.
2. Bordes: entra 50 ms antes de la voz y sale 100 ms después (entre frases quedan ~0,15 s).
3. Pausas dentro de la frase de más de 0,30 s quedan en 0,20 s.
4. --quieto N (número de tramo, desde 1): después de ese tramo deja la imagen corriendo mientras la persona siga
   quieta, como mucho 5 s (espacio para insertar un clip, p. ej. después de "solo mira esto").
Todo cae en cuadros enteros del crudo.
"""
import argparse
import json
import math
import subprocess
from fractions import Fraction
from pathlib import Path

import numpy as np

UMBRAL_DB, PASO, UNIR_S = -40.0, 0.01, 0.25
ANTES, DESPUES, PAUSA_MAX, PAUSA = 0.05, 0.10, 0.30, 0.20
QUIETO_MAX_S = 5.0


def audio(crudo, sr):
    return np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", str(crudo), "-vn", "-ac", "1", "-ar", str(sr),
                                         "-f", "f32le", "-"], capture_output=True, check=True).stdout, np.float32)


def pedazos(a, sr, t0, t1):
    ts = np.arange(max(0, t0), t1, PASO)
    v = np.array([20 * np.log10(np.sqrt((a[int(t * sr):int((t + PASO) * sr)] ** 2).mean()) + 1e-9) for t in ts])
    r, i = [], 0
    while i < len(v):
        if v[i] > UMBRAL_DB:
            j = i
            while j < len(v) and v[j] > UMBRAL_DB:
                j += 1
            if r and ts[i] - r[-1][1] < UNIR_S:
                r[-1][1] = ts[j - 1] + PASO
            else:
                r.append([ts[i], ts[j - 1] + PASO])
            i = j
        else:
            i += 1
    return [x for x in r if x[1] - x[0] >= 0.05]


def quieto_hasta(crudo, desde):
    """Segundo en que la persona empieza a moverse (diferencia entre cuadros), como mucho desde + 5 s."""
    W, H = 108, 192
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{desde:.3f}", "-i", str(crudo), "-t", f"{QUIETO_MAX_S:.1f}",
                          "-vf", f"scale={W}:{H},format=gray", "-f", "rawvideo", "-"], capture_output=True).stdout
    f = np.frombuffer(raw, np.uint8).reshape(-1, H, W).astype(float)
    d = np.abs(np.diff(f, axis=0)).mean((1, 2))
    base = np.median(d[:12]) if len(d) > 12 else 0.25
    fps = len(f) / QUIETO_MAX_S
    for i in range(len(d)):
        if d[i] > max(0.45, base * 1.8):
            return desde + (i + 1) / fps - 0.05
    return desde + QUIETO_MAX_S


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("reel")
    ap.add_argument("--crudo", required=True)
    ap.add_argument("--quieto", type=int, nargs="*", default=[])
    a = ap.parse_args()
    t = Path(a.reel) / "trabajo"
    crudo = Path(a.reel) / a.crudo
    bruto = json.loads((t / "edl.json").read_text())
    (t / "edl_bruto.json").write_text(json.dumps(bruto, ensure_ascii=False, indent=1))
    fps = Fraction(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                                   "stream=r_frame_rate", "-of", "csv=p=0", str(crudo)],
                                  capture_output=True, text=True, check=True).stdout.strip().strip(","))
    a48, a16 = audio(crudo, 48000), audio(crudo, 16000)
    from faster_whisper import WhisperModel
    modelo = WhisperModel("large-v3", device="cpu", compute_type="int8")
    cortes = []
    for k, c in enumerate(bruto["cortes"], start=1):
        ps = pedazos(a48, 48000, c["in"] - 0.1, c["out"] + 0.1)
        print(f"#{k} {c.get('texto', '')[:60]}")
        for s, e in ps:
            seg, _ = modelo.transcribe(a16[int((s - 0.05) * 16000):int((e + 0.08) * 16000)], language="es",
                                       beam_size=5, condition_on_previous_text=False)
            print(f"   {s:8.2f}-{e:8.2f}  {' '.join(z.text.strip() for z in seg)}")
        # Arranque en falso: un pedazo muy corto (< 0,35 s) al principio o al final del tramo, separado por una pausa
        # (> 0,30 s) del resto, es casi siempre una sílaba que se cortó y se repitió ("Lo-… Lo importante").
        while len(ps) > 1 and ps[0][1] - ps[0][0] < 0.35 and ps[1][0] - ps[0][1] > PAUSA_MAX:
            print(f"   fuera (arranque en falso): {ps[0][0]:.2f}-{ps[0][1]:.2f}")
            ps = ps[1:]
        while len(ps) > 1 and ps[-1][1] - ps[-1][0] < 0.35 and ps[-1][0] - ps[-2][1] > PAUSA_MAX:
            print(f"   fuera (sílaba suelta al final): {ps[-1][0]:.2f}-{ps[-1][1]:.2f}")
            ps = ps[:-1]
        grupos = [list(ps[0])]
        for s, e in ps[1:]:
            if s - grupos[-1][1] <= PAUSA_MAX:
                grupos[-1][1] = e
            else:
                grupos.append([s, e])
        for g, (s, e) in enumerate(grupos):
            ultimo = g == len(grupos) - 1
            ini = s - ANTES if g == 0 else s - PAUSA / 2
            fin = e + DESPUES if ultimo else e + PAUSA / 2
            if ultimo and k in a.quieto:
                fin = quieto_hasta(crudo, e)
                print(f"   quieto hasta {fin:.2f} ({fin - e:.2f} s después de hablar)")
            cortes.append({"in": round(float(math.floor(ini * fps) / fps), 4), "out": round(float(math.ceil(fin * fps) / fps), 4),
                           "tramo": k, "texto": c.get("texto", "")})
    (t / "edl.json").write_text(json.dumps({"fps": str(fps), "cortes": cortes}, ensure_ascii=False, indent=1))
    print(f"{len(cortes)} cortes, {sum(x['out'] - x['in'] for x in cortes):.2f} s -> {t / 'edl.json'}")


if __name__ == "__main__":
    main()
