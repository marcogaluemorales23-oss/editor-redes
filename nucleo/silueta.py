#!/usr/bin/env python3
"""Máscara de la persona (blanco = persona, negro = fondo) para poner gráficos DETRÁS de ella.

Uso: python3 nucleo/silueta.py <video> <salida.mkv> <desde-hasta> [<desde-hasta> ...] [--zona]
Ej.: python3 nucleo/silueta.py trabajo/base.mp4 trabajo/silueta.mkv 3.71-6.30 10.59-12.30
Fuera de los tramos pedidos la máscara queda negra (no se calcula, para ahorrar tiempo).

Modelo: Robust Video Matting (MobileNetV3, ONNX). Es un modelo de "matting": da un alfa suave con pelo, brazos
y bordes bien recortados, y recuerda los cuadros anteriores, así que el borde no parpadea.
RVM a veces toma como "frente" objetos pegados a la persona (el sillón blanco de C6764). Si el objeto de verdad
está delante del fondo, se deja: los gráficos pasan detrás de los dos y se ve natural. La opción --zona multiplica
por la zona gruesa de la persona según MediaPipe, pero con objetos del mismo color que la ropa deja un borde
difuso peor que el recorte nítido de RVM (probado en C6764), así que va apagada por defecto.
"""
import subprocess
import sys
from pathlib import Path

import numpy as np

MODELO = Path(__file__).with_name("modelos") / "rvm_mobilenetv3_fp32.onnx"
CALENTAR_S = 0.6       # empieza a procesar un poco antes del tramo para que la memoria del modelo se asiente
REDUCCION = 0.25       # downsample_ratio recomendado por RVM para video HD
MODELO_ZONA = Path(__file__).with_name("modelos") / "selfie_multiclass.tflite"
MARGEN_ZONA = 22       # px que se ensancha la zona de MediaPipe (en 1080 de ancho); más, y entra el sillón


def zona_persona(seg, img, t_ms, mp, cv2):
    """Zona gruesa donde está la persona según MediaPipe, ensanchada y con borde suave."""
    alto, ancho, _ = img.shape
    chico = cv2.resize(img, (ancho // 2, alto // 2), interpolation=cv2.INTER_AREA)
    r = seg.segment_for_video(mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(chico)), t_ms)
    persona = (1.0 - r.confidence_masks[0].numpy_view().reshape(chico.shape[:2])) > 0.4
    m = MARGEN_ZONA // 2
    persona = cv2.dilate(persona.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * m + 1, 2 * m + 1)))
    persona = cv2.GaussianBlur(persona.astype(np.float32), (0, 0), m / 3)
    return cv2.resize(persona, (ancho, alto), interpolation=cv2.INTER_LINEAR)


def info(video):
    salida = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                             "stream=width,height,r_frame_rate", "-of", "csv=p=0", video],
                            capture_output=True, text=True, check=True).stdout.strip().split(",")
    ancho, alto, fps = int(salida[0]), int(salida[1]), salida[2]
    num, den = (int(x) for x in fps.split("/"))
    return ancho, alto, num / den, fps


def main(video, destino, tramos_txt, usar_zona=False):
    import cv2
    import mediapipe as mp
    import onnxruntime as ort
    from mediapipe.tasks.python import BaseOptions, vision
    tramos = [tuple(float(x) for x in t.split("-")) for t in tramos_txt]
    ancho, alto, fps, fps_txt = info(video)
    sesion = ort.InferenceSession(str(MODELO), providers=["CPUExecutionProvider"])
    seg = vision.ImageSegmenter.create_from_options(vision.ImageSegmenterOptions(
        base_options=BaseOptions(model_asset_path=str(MODELO_ZONA)), running_mode=vision.RunningMode.VIDEO,
        output_confidence_masks=True)) if usar_zona else None
    lector = subprocess.Popen(["ffmpeg", "-v", "error", "-i", video, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                              stdout=subprocess.PIPE)
    escritor = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "gray",
                                 "-s", f"{ancho}x{alto}", "-r", fps_txt, "-i", "-",
                                 "-c:v", "ffv1", "-pix_fmt", "gray", destino], stdin=subprocess.PIPE)
    vacio = np.zeros((1, 1, 1, 1), np.float32)
    memoria = None
    reduccion = np.array([REDUCCION], np.float32)
    i, calculados = 0, 0
    tam = ancho * alto * 3
    negro = bytes(ancho * alto)
    while True:
        crudo = lector.stdout.read(tam)
        if len(crudo) < tam:
            break
        t = i / fps
        en_tramo = any(a - CALENTAR_S <= t <= b + 0.1 for a, b in tramos)
        if en_tramo:
            img = np.frombuffer(crudo, np.uint8).reshape(alto, ancho, 3)
            src = (img.astype(np.float32) / 255).transpose(2, 0, 1)[None]
            r = memoria or [vacio] * 4
            _, alfa, *memoria = sesion.run(None, {"src": src, "r1i": r[0], "r2i": r[1], "r3i": r[2], "r4i": r[3],
                                                 "downsample_ratio": reduccion})
            final = np.clip(alfa[0, 0], 0, 1)
            if usar_zona:
                final = final * np.clip(zona_persona(seg, img, int(t * 1000), mp, cv2), 0, 1)
            escritor.stdin.write((final * 255).astype(np.uint8).tobytes())
            calculados += 1
        else:
            memoria = None  # se reinicia la memoria entre tramos (otro clip, otro fondo)
            escritor.stdin.write(negro)
        i += 1
    escritor.stdin.close()
    escritor.wait()
    print(f"silueta: {calculados} de {i} cuadros calculados -> {destino}")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--zona"]
    main(args[0], args[1], args[2:], usar_zona="--zona" in sys.argv)
