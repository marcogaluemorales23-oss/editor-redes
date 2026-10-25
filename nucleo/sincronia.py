#!/usr/bin/env python3
"""Mide el desfase entre labios y voz de cada clip crudo.

Con los puntos faciales de MediaPipe mide cuánto abre la boca en cada cuadro (distancia entre labio de arriba y
labio de abajo, relativa al alto de la cara) y lo compara con el volumen de la voz, probando retrasos de -300 a
+300 ms. El retraso con mejor correlación es el desfase del clip.
Positivo = la voz llega DESPUÉS que la boca (hay que adelantar el audio); negativo = la voz se adelanta.

Uso: python3 nucleo/sincronia.py <reel> [segundos_por_clip]
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

MODELO = Path(__file__).with_name("modelos") / "face_landmarker.task"
SR = 16000


def apertura_boca(crudo, t0, d, fps_txt):
    import mediapipe as mp
    from mediapipe.tasks.python import BaseOptions, vision
    num, den = (int(v) for v in fps_txt.split("/"))
    det = vision.FaceLandmarker.create_from_options(vision.FaceLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=str(MODELO)), running_mode=vision.RunningMode.VIDEO,
        num_faces=1))
    crudo_px = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t0), "-t", str(d), "-i", str(crudo),
                               "-vf", "scale=540:960", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                              capture_output=True, check=True).stdout
    cuadros = np.frombuffer(crudo_px, np.uint8).reshape(-1, 960, 540, 3)
    salida = []
    for i, c in enumerate(cuadros):
        r = det.detect_for_video(mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(c)),
                                 int(i * 1000 * den / num))
        if not r.face_landmarks:
            salida.append(np.nan)
            continue
        p = r.face_landmarks[0]
        alto_cara = abs(p[152].y - p[10].y) or 1
        salida.append(abs(p[14].y - p[13].y) / alto_cara)  # 13/14: labio interior de arriba/abajo
    return np.array(salida), num / den


def volumen(crudo, t0, d):
    x = np.frombuffer(subprocess.run(
        ["ffmpeg", "-v", "error", "-ss", str(t0), "-t", str(d), "-i", str(crudo), "-ac", "1", "-ar", str(SR),
         "-f", "s16le", "-"], capture_output=True, check=True).stdout, np.int16).astype(np.float32) / 32768
    v = int(SR * 0.005)
    env = np.sqrt((x[: len(x) // v * v].reshape(-1, v) ** 2).mean(axis=1))
    env = np.convolve(env, np.ones(8) / 8, "same")  # ~40 ms, como un cuadro
    return np.log(env + 1e-4)


def desfase(boca, fps, env):
    ok_b = ~np.isnan(boca)
    resultados = []
    for lag_ms in range(-300, 301, 5):
        idx = (np.arange(len(boca)) / fps * 1000 + lag_ms) / 5
        ok = ok_b & (idx >= 0) & (idx < len(env))
        if ok.sum() < 48:
            continue
        r = np.corrcoef(boca[ok], env[idx[ok].astype(int)])[0, 1]
        resultados.append((r, lag_ms))
    return max(resultados)


def main(reel, segundos=40.0):
    reel = Path(reel)
    cortes = json.loads((reel / "trabajo" / "edl.json").read_text())["cortes"]
    for clip in dict.fromkeys(c["clip"] for c in cortes):
        crudo = reel / "crudos" / f"{clip}.MP4"
        fps_txt = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                                  "stream=r_frame_rate", "-of", "csv=p=0", str(crudo)],
                                 capture_output=True, text=True).stdout.strip().strip(",")
        dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
                                    "csv=p=0", str(crudo)], capture_output=True, text=True).stdout)
        usados = [c for c in cortes if c["clip"] == clip]
        centro = (min(c["in"] for c in usados) + max(c["out"] for c in usados)) / 2
        t0 = max(0.0, min(centro - segundos / 2, dur - segundos))
        d = min(segundos, dur)
        boca, fps = apertura_boca(crudo, t0, d, fps_txt)
        r, lag = desfase(boca, fps, volumen(crudo, t0, d))
        print(f"{clip}: desfase {lag:+4d} ms  (correlación {r:.2f}, {d:.0f} s analizados)", flush=True)


if __name__ == "__main__":
    main(sys.argv[1], float(sys.argv[2]) if len(sys.argv) > 2 else 40.0)
