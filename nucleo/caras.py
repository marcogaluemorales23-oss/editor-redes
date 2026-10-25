#!/usr/bin/env python3
"""Detecta la cara en cuadros de un video: centro y ancho, normalizados a un cuadro de 1080x1920.

Uso como módulo: caras(video, tiempos) -> [(t, cx, cy, ancho) | (t, None, None, None)]
Uso por consola: python3 nucleo/caras.py <video> <paso_s>
"""
import subprocess
import sys
from pathlib import Path

import numpy as np

MODELO = Path(__file__).with_name("modelos") / "blaze_face_short_range.tflite"
_detector = None


def detector():
    global _detector
    if _detector is None:
        from mediapipe.tasks.python import BaseOptions, vision
        _detector = vision.FaceDetector.create_from_options(
            vision.FaceDetectorOptions(base_options=BaseOptions(model_asset_path=str(MODELO)),
                                       min_detection_confidence=0.5))
    return _detector


def cuadro(video, t, ancho=540):
    """Un cuadro a ancho fijo (con la rotación del clip ya aplicada) como arreglo RGB."""
    alto = ancho * 16 // 9
    crudo = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", str(video), "-frames:v", "1",
                            "-vf", f"scale={ancho}:{alto}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                           capture_output=True, check=True).stdout
    return np.frombuffer(crudo, np.uint8).reshape(alto, ancho, 3)


def caras(video, tiempos):
    import mediapipe as mp
    salida = []
    for t in tiempos:
        img = cuadro(video, t)
        h, w, _ = img.shape
        r = detector().detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(img)))
        if not r.detections:
            salida.append((t, None, None, None))
            continue
        b = max(r.detections, key=lambda d: d.bounding_box.width).bounding_box
        k = 1080 / w
        salida.append((t, (b.origin_x + b.width / 2) * k, (b.origin_y + b.height / 2) * k, b.width * k))
    return salida


if __name__ == "__main__":
    video, paso = sys.argv[1], float(sys.argv[2])
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                video], capture_output=True, text=True).stdout)
    for t, cx, cy, a in caras(video, np.arange(0, dur, paso)):
        print(f"{t:6.2f}  " + ("sin cara" if cx is None else f"x={cx:5.0f} y={cy:5.0f} ancho={a:4.0f}"))
