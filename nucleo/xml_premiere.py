#!/usr/bin/env python3
"""Arma un XML de Premiere (FCP7 xmeml) con el corte de trabajo/edl.json, apuntando a los crudos ORIGINALES de Sebas.

Uso: python3 nucleo/xml_premiere.py <reel> --camara A=crudos/C5510.MP4 [--camara B=crudos/C5323.MP4 --desfase B=-123.456]
                                     [--nombre andy_corte] [--ancho 2160 --alto 3840]
- Cada corte usa la cámara de su campo "cam" (por defecto A). --desfase B=x: segundo de B = segundo de A + x
  (sale de sincronizar el audio de las dos cámaras).
- El audio va siempre de la cámara A (la del micrófono bueno), en dos pistas (estéreo).
- En Premiere: Archivo > Importar el XML y, si pide los medios, "Vincular" al archivo original en tu disco.
Escribe <reel>/salida/<nombre>.xml.
"""
import argparse
import json
import subprocess
from fractions import Fraction
from pathlib import Path
from xml.sax.saxutils import escape


def info(ruta):
    d = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,width,height,"
                                   "r_frame_rate:format=duration", "-of", "json", str(ruta)],
                                  capture_output=True, text=True, check=True).stdout)
    v = next(s for s in d["streams"] if s["codec_type"] == "video")
    return {"w": v["width"], "h": v["height"], "fps": Fraction(v["r_frame_rate"]), "dur": float(d["format"]["duration"])}


def rate(fps):
    ntsc = fps.denominator == 1001
    return f"<rate><timebase>{round(float(fps))}</timebase><ntsc>{'TRUE' if ntsc else 'FALSE'}</ntsc></rate>"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("reel")
    ap.add_argument("--camara", action="append", required=True, help="A=crudos/archivo.MP4")
    ap.add_argument("--desfase", action="append", default=[], help="B=segundos (B = A + desfase)")
    ap.add_argument("--nombre", default="corte")
    ap.add_argument("--ancho", type=int, default=2160)
    ap.add_argument("--alto", type=int, default=3840)
    a = ap.parse_args()
    reel = Path(a.reel)
    camaras = dict(x.split("=", 1) for x in a.camara)
    desfases = {k: float(v) for k, v in (x.split("=", 1) for x in a.desfase)}
    medios = {k: {**info(reel / v), "nombre": Path(v).name} for k, v in camaras.items()}
    fps = medios["A"]["fps"]
    cortes = json.loads((reel / "trabajo" / "edl.json").read_text())["cortes"]

    def archivo(cam, primero):
        m = medios[cam]
        if not primero:
            return f'<file id="file-{cam}"/>'
        return (f'<file id="file-{cam}"><name>{escape(m["nombre"])}</name><pathurl>file://localhost/{escape(m["nombre"])}</pathurl>'
                f'{rate(m["fps"])}<duration>{round(m["dur"] * float(m["fps"]))}</duration><media>'
                f'<video><samplecharacteristics><width>{m["w"]}</width><height>{m["h"]}</height></samplecharacteristics></video>'
                f'<audio><samplecharacteristics><depth>16</depth><samplerate>48000</samplerate></samplecharacteristics>'
                f'<channelcount>2</channelcount></audio></media></file>')

    vid, aud1, aud2, t, usados = [], [], [], 0, set()
    for k, c in enumerate(cortes):
        cam = c.get("cam", "A")
        f0, f1 = round(c["in"] * fps), round(c["out"] * fps)
        n = f1 - f0
        v0 = round((c["in"] + desfases.get(cam, 0.0)) * fps)
        vid.append(f'<clipitem id="v{k}"><name>{escape(medios[cam]["nombre"])}</name>{rate(fps)}<start>{t}</start>'
                   f'<end>{t + n}</end><in>{v0}</in><out>{v0 + n}</out>{archivo(cam, cam not in usados)}</clipitem>')
        usados.add(cam)
        for pista, lista in ((1, aud1), (2, aud2)):
            # El archivo A ya queda definido en la pista de video (va antes en el XML); si el video nunca usa A,
            # se define en el primer clip de audio.
            primero = k == 0 and pista == 1 and all(x.get("cam", "A") != "A" for x in cortes)
            lista.append(f'<clipitem id="a{pista}_{k}"><name>{escape(medios["A"]["nombre"])}</name>{rate(fps)}<start>{t}</start>'
                         f'<end>{t + n}</end><in>{f0}</in><out>{f1}</out>{archivo("A", primero)}'
                         f'<sourcetrack><mediatype>audio</mediatype><trackindex>{pista}</trackindex></sourcetrack></clipitem>')
        t += n
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE xmeml>\n<xmeml version="4"><sequence id="seq">'
           f'<name>{escape(a.nombre)}</name><duration>{t}</duration>{rate(fps)}<media><video><format><samplecharacteristics>'
           f'{rate(fps)}<width>{a.ancho}</width><height>{a.alto}</height><pixelaspectratio>square</pixelaspectratio>'
           f'</samplecharacteristics></format><track>{"".join(vid)}</track></video><audio>'
           f'<track>{"".join(aud1)}</track><track>{"".join(aud2)}</track></audio></media></sequence></xmeml>\n')
    destino = reel / "salida" / f"{a.nombre}.xml"
    destino.write_text(xml)
    print(f"{len(cortes)} cortes, {t} cuadros ({float(t / fps):.2f} s) -> {destino}")


if __name__ == "__main__":
    main()
