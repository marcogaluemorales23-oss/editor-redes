#!/usr/bin/env python3
"""Copia "rala" de un video de Drive: el archivo local tiene el tamaño completo pero solo los bytes que se piden
(el resto no ocupa disco). Sirve cuando el crudo no entra en el disco del servidor o Drive limita las descargas
completas ("Quota exceeded"): se baja el índice y después solo los pedazos que hacen falta, en pocas peticiones.

Uso: python3 nucleo/drive_ralo.py <id_de_drive> <destino.MP4>          # crea la copia con cabecera e índice
     python3 nucleo/drive_ralo.py <id_de_drive> <destino.MP4> a-b ...   # además baja esos rangos de bytes
Lleva la cuenta en <destino>.rangos.json. Para leerlo con ffmpeg/ffprobe en un punto sin fotograma clave en el
índice: -seek2any 1 y empezar ~0,6 s antes (los Sony graban un fotograma I cada 0,5 s).
Libera un rango con liberar() (fallocate --punch-hole) cuando ya se usó.
"""
import json
import subprocess
import sys
from pathlib import Path


def _url(fid):
    return f"https://drive.usercontent.google.com/download?id={fid}&export=download&confirm=t"


def _estado(dest):
    f = Path(str(dest) + ".rangos.json")
    return json.loads(f.read_text()) if f.exists() else None


def _guardar(dest, e):
    Path(str(dest) + ".rangos.json").write_text(json.dumps(e))


def crear(fid, dest):
    cab = subprocess.run(["curl", "-sS", "-D", "-", "-o", "/dev/null", "-r", "0-0", _url(fid)], capture_output=True, text=True).stdout
    total = int([l for l in cab.splitlines() if l.lower().startswith("content-range")][0].split("/")[-1])
    with open(dest, "wb") as f:
        f.truncate(total)
    _guardar(dest, {"id": fid, "total": total, "rangos": []})
    traer(dest, 0, min(total - 1, 524287))                 # cabecera
    traer(dest, max(0, total - 600000), total - 1)          # índice (moov) al final, como graban las Sony
    return total


def traer(dest, a, b):
    """Baja los bytes a..b (inclusive) a su lugar; no repite lo que ya está."""
    e = _estado(dest)
    if any(x <= a and b <= y for x, y in e["rangos"]):
        return 0
    r = subprocess.run(["curl", "-sS", "--fail", "-r", f"{a}-{b}", _url(e["id"])], capture_output=True, check=True).stdout
    if len(r) != b - a + 1 or r[:15] == b"<!DOCTYPE html>":
        raise SystemExit(f"Drive no entregó {a}-{b} ({len(r)} bytes): posible cupo de descargas excedido")
    with open(dest, "r+b") as f:
        f.seek(a)
        f.write(r)
    e["rangos"].append([a, b])
    _guardar(dest, e)
    return len(r)


def liberar(dest, a, b):
    subprocess.run(["fallocate", "--punch-hole", "--keep-size", "--offset", str(a), "--length", str(b - a + 1), str(dest)],
                   check=True)
    e = _estado(dest)
    e["rangos"] = [r for r in e["rangos"] if r != [a, b]]
    _guardar(dest, e)


if __name__ == "__main__":
    fid, dest = sys.argv[1], sys.argv[2]
    if _estado(dest) is None:
        print("tamaño", crear(fid, dest))
    for rango in sys.argv[3:]:
        x, y = map(int, rango.split("-"))
        print(rango, traer(dest, x, y))
