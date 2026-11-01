#!/usr/bin/env python3
"""Busca y baja videos de stock (Pexels y Pixabay) para usarlos de b-roll.

Uso: python3 nucleo/stock.py <reel> "casa remodelación" [--fuente pexels|pixabay|todas] [--n 4] [--horizontal]
Necesita las claves en el entorno (configuración del entorno, nunca pegadas en el chat):
    PEXELS_API_KEY   (gratis en pexels.com/api)       PIXABAY_API_KEY   (gratis en pixabay.com/api/docs)
- Prefiere tomas VERTICALES (para 1080x1920) y la mejor calidad que no pase de 4K; con --horizontal no filtra.
- Baja a <reel>/crudos/stock/<fuente>_<id>.mp4, anota autor, enlace y licencia en <reel>/crudos/stock/stock.json
  y arma <reel>/trabajo/hoja_stock.jpg (un cuadro de cada toma) para elegir.
- Licencias: Pexels y Pixabay permiten uso comercial sin atribución; igual se guarda el crédito. Nunca usar tomas
  con marcas, logos o personas reconocibles en contextos que las comprometan (regla 5: material de terceros).
- Pinterest NO: no tiene una API para bajar videos y bajarlos va contra sus términos (y la red lo bloquea).
"""
import argparse
import json
import os
import subprocess
import urllib.parse
from pathlib import Path

FUENTE_TXT = Path(__file__).resolve().parents[1] / "motion/public/fuentes/Inter-Bold.ttf"


def pedir(url, cabeceras=()):
    cmd = ["curl", "-sS", "--fail", "-m", "30", url]
    for c in cabeceras:
        cmd[1:1] = ["-H", c]
    return json.loads(subprocess.run(cmd, capture_output=True, text=True, check=True).stdout)


def elegir(archivos, vertical):
    """La mejor versión: vertical si se pide, la más alta hasta 3840 px de alto."""
    buenos = [a for a in archivos if a.get("width") and a.get("height") and max(a["width"], a["height"]) <= 3840]
    if vertical:
        buenos = [a for a in buenos if a["height"] > a["width"]] or buenos
    return max(buenos, key=lambda a: a["width"] * a["height"]) if buenos else None


def pexels(q, n, vertical):
    clave = os.environ.get("PEXELS_API_KEY")
    if not clave:
        print("pexels: falta PEXELS_API_KEY en el entorno")
        return []
    params = {"query": q, "per_page": n * 2, "size": "large"}
    if vertical:
        params["orientation"] = "portrait"
    datos = pedir("https://api.pexels.com/videos/search?" + urllib.parse.urlencode(params), [f"Authorization: {clave}"])
    out = []
    for v in datos.get("videos", []):
        a = elegir([{"url": f["link"], "width": f.get("width"), "height": f.get("height")} for f in v["video_files"]], vertical)
        if a:
            out.append({"fuente": "pexels", "id": v["id"], "url": a["url"], "ancho": a["width"], "alto": a["height"],
                        "duracion": v.get("duration"), "autor": v.get("user", {}).get("name"), "pagina": v.get("url"),
                        "licencia": "Pexels License (uso comercial, sin atribución obligatoria)"})
    return out[:n]


def pixabay(q, n, vertical):
    clave = os.environ.get("PIXABAY_API_KEY")
    if not clave:
        print("pixabay: falta PIXABAY_API_KEY en el entorno")
        return []
    datos = pedir("https://pixabay.com/api/videos/?" + urllib.parse.urlencode(
        {"key": clave, "q": q, "per_page": max(3, n * 3), "safesearch": "true"}))
    out = []
    for v in datos.get("hits", []):
        a = elegir([{"url": f["url"], "width": f.get("width"), "height": f.get("height")}
                    for f in v.get("videos", {}).values() if f.get("url")], vertical)
        if a and (not vertical or a["height"] > a["width"]):
            out.append({"fuente": "pixabay", "id": v["id"], "url": a["url"], "ancho": a["width"], "alto": a["height"],
                        "duracion": v.get("duration"), "autor": v.get("user"), "pagina": v.get("pageURL"),
                        "licencia": "Pixabay Content License (uso comercial, sin atribución obligatoria)"})
    return out[:n]


def hoja(reel, bajados):
    if not bajados:
        return
    tmp = reel / "trabajo" / "hoja_stock"
    tmp.mkdir(parents=True, exist_ok=True)
    for i, b in enumerate(bajados):
        etiqueta = f"{b['fuente']} {b['id']}  {b['ancho']}x{b['alto']}".replace(":", "")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str((b.get("duracion") or 2) / 2), "-i", b["archivo"],
                        "-frames:v", "1", "-vf", "scale=360:640:force_original_aspect_ratio=decrease,pad=360:640:(ow-iw)/2:(oh-ih)/2,"
                        f"drawtext=fontfile={FUENTE_TXT}:text='{i + 1}  {etiqueta}':x=8:y=8:fontsize=18:fontcolor=white:"
                        "box=1:boxcolor=black@0.6:boxborderw=4", str(tmp / f"{i:02d}.png")], check=True)
    cols = min(6, len(bajados))
    filas = -(-len(bajados) // cols)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(tmp / "%02d.png"), "-frames:v", "1", "-vf",
                    f"tile={cols}x{filas}:padding=6:color=white", str(reel / "trabajo" / "hoja_stock.jpg")], check=True)
    print(f"hoja -> {reel / 'trabajo' / 'hoja_stock.jpg'}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("reel")
    ap.add_argument("consulta", help="en inglés da más resultados (p. ej. 'house renovation')")
    ap.add_argument("--fuente", default="todas", choices=["pexels", "pixabay", "todas"])
    ap.add_argument("--n", type=int, default=4, help="tomas por fuente")
    ap.add_argument("--horizontal", action="store_true", help="no filtrar por vertical")
    a = ap.parse_args()
    reel = Path(a.reel)
    destino = reel / "crudos" / "stock"
    destino.mkdir(parents=True, exist_ok=True)
    vertical = not a.horizontal
    encontrados = []
    if a.fuente in ("pexels", "todas"):
        encontrados += pexels(a.consulta, a.n, vertical)
    if a.fuente in ("pixabay", "todas"):
        encontrados += pixabay(a.consulta, a.n, vertical)
    registro_f = destino / "stock.json"
    registro = json.loads(registro_f.read_text()) if registro_f.exists() else []
    bajados = []
    for e in encontrados:
        archivo = destino / f"{e['fuente']}_{e['id']}.mp4"
        if not archivo.exists():
            subprocess.run(["curl", "-sSL", "--fail", "-m", "300", "-o", str(archivo), e["url"]], check=True)
        e = {**e, "consulta": a.consulta, "archivo": str(archivo)}
        bajados.append(e)
        if not any(r["archivo"] == e["archivo"] for r in registro):
            registro.append(e)
        print(f"{e['fuente']:8s} {e['id']:>10}  {e['ancho']}x{e['alto']}  {e.get('duracion')} s  {e['autor']}  -> {archivo.name}")
    registro_f.write_text(json.dumps(registro, ensure_ascii=False, indent=1))
    hoja(reel, bajados)
    if not bajados:
        print("stock: no se bajó nada (revisa las claves o prueba la búsqueda en inglés)")


if __name__ == "__main__":
    main()
