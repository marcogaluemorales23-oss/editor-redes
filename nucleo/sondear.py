#!/usr/bin/env python3
"""Revisa cada clip: duración, fps, resolución, rotación y si es HDR.

Uso: python3 nucleo/sondear.py reels/<nombre>/crudos/*
"""
import json
import subprocess
import sys

HDR_TRANSFERS = {"smpte2084", "arib-std-b67"}


def sondear(ruta):
    salida = subprocess.run(
        ["ffprobe", "-v", "error", "-print_format", "json", "-show_streams", "-show_format", ruta],
        capture_output=True, text=True, check=True,
    ).stdout
    datos = json.loads(salida)
    video = next(s for s in datos["streams"] if s["codec_type"] == "video")
    num, den = video["r_frame_rate"].split("/")
    rotacion = 0
    for side in video.get("side_data_list", []):
        if "rotation" in side:
            rotacion = int(side["rotation"])
    rotacion = int(video.get("tags", {}).get("rotate", rotacion))
    return {
        "archivo": ruta,
        "duracion_s": round(float(datos["format"]["duration"]), 2),
        "fps": round(int(num) / int(den), 2),
        "resolucion": f'{video["width"]}x{video["height"]}',
        "rotacion": rotacion,
        "hdr": video.get("color_transfer") in HDR_TRANSFERS,
        "tiene_audio": any(s["codec_type"] == "audio" for s in datos["streams"]),
    }


if __name__ == "__main__":
    print(json.dumps([sondear(r) for r in sys.argv[1:]], indent=2, ensure_ascii=False))
