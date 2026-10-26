#!/usr/bin/env python3
"""Máscara de la persona (blanco = persona, negro = fondo) para poner gráficos DETRÁS de ella.

Uso: python3 nucleo/silueta.py <video> <salida.mkv> <desde-hasta[@y_escritorio]> [...] [--zona]
Ej.: python3 nucleo/silueta.py trabajo/base.mp4 trabajo/silueta.mkv 3.71-6.30@1765 10.59-12.30@1735 21.7-26.5
@y_escritorio: todo lo que está debajo de esa altura (el escritorio y lo que tiene encima) se cuenta como frente,
así persona, sillón y escritorio quedan como un solo bloque y los gráficos solo tapan la pared del fondo.
Fuera de los tramos pedidos la máscara queda negra (no se calcula, para ahorrar tiempo).
Además de la máscara escribe, junto a ella, persona.mov (ProRes 4444 con transparencia): la persona ya recortada,
lista para poner encima. Es lo que usa nucleo/componer.py.

Terminación tipo "recorte de capa" de Premiere (pedido de Sebas, el recorte de MobileNet se veía lavado):
- Modelo grande (ResNet50) y máscara a media resolución: pelo y hombros nítidos.
- Estrechar el borde (choke) con un difuminado de ~1 px: borde firme, sin zona fantasma semitransparente.
- Descontaminar el color del borde con el "frente" que estima RVM: sin halo claro de la pared alrededor del pelo.

Modelo: Robust Video Matting (ResNet50, ONNX). Es un modelo de "matting": da un alfa suave con pelo, brazos
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

MODELO = Path(__file__).with_name("modelos") / "rvm_resnet50_fp32.onnx"
CALENTAR_S = 0.6       # empieza a procesar un poco antes del tramo para que la memoria del modelo se asiente
REDUCCION = 0.5        # máscara a media resolución (0,25 dejaba el pelo borroso)
CHOKE = (0.12, 0.88)   # el alfa entre estos valores se estira a 0-1: borde firme, sin fantasma
DIFUMINADO = 0.8       # px de suavizado del borde después del choke
NUCLEO = (0.35, 0.7)   # donde el alfa es más que esto se usa el pixel original (más detalle que el de RVM)
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
    tramos = []
    for t in tramos_txt:
        rango, _, suelo = t.partition("@")
        a, b = (float(x) for x in rango.split("-"))
        tramos.append((a, b, float(suelo) if suelo else None))
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
    persona_mov = str(Path(destino).with_name("persona.mov"))
    persona = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba",
                                "-s", f"{ancho}x{alto}", "-r", fps_txt, "-i", "-", "-c:v", "prores_ks",
                                "-profile:v", "4444", "-pix_fmt", "yuva444p10le", persona_mov], stdin=subprocess.PIPE)
    filas = np.arange(alto, dtype=np.float32)[:, None]
    vacio_rgba = bytes(ancho * alto * 4)
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
        tramo = next(((a, b, y) for a, b, y in tramos if a - CALENTAR_S <= t <= b + 0.1), None)
        en_tramo = tramo is not None
        if en_tramo:
            img = np.frombuffer(crudo, np.uint8).reshape(alto, ancho, 3)
            src = (img.astype(np.float32) / 255).transpose(2, 0, 1)[None]
            r = memoria or [vacio] * 4
            frente, alfa, *memoria = sesion.run(None, {"src": src, "r1i": r[0], "r2i": r[1], "r3i": r[2],
                                                      "r4i": r[3], "downsample_ratio": reduccion})
            crudo_alfa = np.clip(alfa[0, 0], 0, 1)
            final = np.clip((crudo_alfa - CHOKE[0]) / (CHOKE[1] - CHOKE[0]), 0, 1)
            final = cv2.GaussianBlur(final, (0, 0), DIFUMINADO)
            if usar_zona:
                final = final * np.clip(zona_persona(seg, img, int(t * 1000), mp, cv2), 0, 1)
            # Color: en el borde, el frente que estima RVM (sin el color de la pared); adentro, el pixel original.
            nucleo = np.clip((crudo_alfa - NUCLEO[0]) / (NUCLEO[1] - NUCLEO[0]), 0, 1)
            if tramo[2] is not None:  # escritorio: rampa suave de 30 px hacia abajo, con su color original
                escritorio = np.clip((filas - (tramo[2] - 30)) / 30, 0, 1)
                final = np.maximum(final, escritorio)
                nucleo = np.maximum(nucleo, escritorio)
            original = img.astype(np.float32) / 255
            limpio = frente[0].transpose(1, 2, 0)
            color = original * nucleo[..., None] + limpio * (1 - nucleo[..., None])
            rgba = np.dstack([np.clip(color, 0, 1), final[..., None]])
            persona.stdin.write((rgba * 255).astype(np.uint8).tobytes())
            escritor.stdin.write((final * 255).astype(np.uint8).tobytes())
            calculados += 1
        else:
            memoria = None  # se reinicia la memoria entre tramos (otro clip, otro fondo)
            escritor.stdin.write(negro)
            persona.stdin.write(vacio_rgba)
        i += 1
    for proceso in (escritor, persona):
        proceso.stdin.close()
        proceso.wait()
    print(f"silueta: {calculados} de {i} cuadros calculados -> {destino}")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--zona"]
    main(args[0], args[1], args[2:], usar_zona="--zona" in sys.argv)
