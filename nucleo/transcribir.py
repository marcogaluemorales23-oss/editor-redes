#!/usr/bin/env python3
"""Transcribe un clip palabra por palabra, con inicio y fin de cada palabra.

Uso: python3 nucleo/transcribir.py <clip> <salida.json> [modelo]
Modelo por defecto: small (rápido en CPU). Para más precisión: medium o large-v3.
"""
import json
import subprocess
import sys

import numpy as np
from faster_whisper import WhisperModel


def leer_audio(clip):
    """Audio mono a 16 kHz con ffmpeg (evita depender de la versión de PyAV)."""
    crudo = subprocess.run(
        ["ffmpeg", "-nostdin", "-v", "error", "-i", clip, "-ac", "1", "-ar", "16000",
         "-f", "s16le", "-"], capture_output=True, check=True,
    ).stdout
    return np.frombuffer(crudo, np.int16).astype(np.float32) / 32768.0


def transcribir(clip, modelo="small"):
    whisper = WhisperModel(modelo, device="cpu", compute_type="int8")
    segmentos, info = whisper.transcribe(
        leer_audio(clip), language="es", word_timestamps=True, vad_filter=False, beam_size=5,
    )
    palabras = []
    for seg in segmentos:
        for p in seg.words:
            palabras.append({"texto": p.word.strip(), "inicio": round(p.start, 3),
                             "fin": round(p.end, 3), "confianza": round(p.probability, 3)})
    return {"clip": clip, "idioma": info.language, "duracion_s": round(info.duration, 2),
            "palabras": palabras}


if __name__ == "__main__":
    clip, destino = sys.argv[1], sys.argv[2]
    modelo = sys.argv[3] if len(sys.argv) > 3 else "small"
    resultado = transcribir(clip, modelo)
    with open(destino, "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=1)
    print(f'{len(resultado["palabras"])} palabras -> {destino}')
