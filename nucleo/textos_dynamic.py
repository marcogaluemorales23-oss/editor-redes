#!/usr/bin/env python3
"""Subtítulos del formato dynamic de Sebas (marcas/sebastian/formato-dynamic.md) -> datos para Remotion.

Uso: python3 nucleo/textos_dynamic.py <reel> --nombre p02v2 [--tiempos palabras.json]
Lee <reel>/trabajo/textos.json:
    {"bloques": [
      {"zona": "arriba"|"centro"|"cta", "hasta": 1.44,           # "hasta" opcional (segundos)
       "pisos": [{"p": [0, 1], "texto": "Si sabes", "tam": "xl", "color": "blanco", "it": true},
                 {"p": [36, 37], "texto": "ni un", "tam": "s"},
                 {"p": [38, 39], "texto": "$1", "tam": "xl", "color": "amarillo", "en_linea": true},
                 {"p": [160, 162], "texto": "COMENTA LA PALABRA", "progresivo": true}]}]}
- "p": índices de palabra (primera y última). El piso aparece cuando se dice la primera palabra.
- "texto": lo que se escribe (corregido: "$1", "deja dinero?"). Con "progresivo" aparece palabra por palabra
  (una palabra del texto por cada palabra dicha del rango).
- "en_linea": va en la misma línea que el piso anterior (p. ej. "ni un" chico + "$1" gigante).
- tam: s / m / l / xl. color: blanco, amarillo, claude (naranja de Claude), rojo, naranja, lima, verde, negro.
  Palabra clave según la acción: verde = dinero o ganar, rojo = perder dinero o error, el resto amarillo o claude.
  "it": itálica. "caja": caja gris.
El bloque se va cuando empieza el siguiente de la misma zona, o como mucho 0,8 s después de su última palabra.
Escribe motion/src/generado/<nombre>.gen.ts (no va a git: es el texto del cliente).
"""
import argparse
import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
QUEDA_S = 0.8


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("reel")
    ap.add_argument("--nombre", required=True)
    ap.add_argument("--tiempos", default="palabras.json")
    a = ap.parse_args()
    trabajo = Path(a.reel) / "trabajo"
    w = json.loads((trabajo / a.tiempos).read_text())["palabras"]
    bloques = json.loads((trabajo / "textos.json").read_text())["bloques"]

    salida = []
    for b in bloques:
        pisos = []
        for p in b["pisos"]:
            i, j = p["p"]
            piso = {k: v for k, v in p.items() if k != "p"}
            piso["t"] = round(p.get("t", w[i]["inicio"]), 3)
            if p.get("progresivo"):
                piso["tiempos"] = [round(w[k]["inicio"], 3) for k in range(i, j + 1)]
            piso["fin_voz"] = w[j]["fin"]
            pisos.append(piso)
        salida.append({"zona": b.get("zona", "centro"), "t0": pisos[0]["t"], "hasta": b.get("hasta"), "pisos": pisos})

    for k, b in enumerate(salida):
        siguiente = next((x["t0"] for x in salida[k + 1:] if x["zona"] == b["zona"]), None)
        fin = b["hasta"] if b["hasta"] is not None else max(p["fin_voz"] for p in b["pisos"]) + QUEDA_S
        if siguiente is not None and b["hasta"] is None:
            fin = min(fin, siguiente)
        b["t1"] = round(fin, 3)
        del b["hasta"]
        for p in b["pisos"]:
            del p["fin_voz"]

    destino = RAIZ / "motion/src/generado" / f"{a.nombre}.gen.ts"
    destino.parent.mkdir(exist_ok=True)
    destino.write_text("// Generado por nucleo/textos_dynamic.py. No editar a mano.\n"
                       "import type { Bloque } from \"../dynamic/Textos\";\n\n"
                       f"export const BLOQUES: Bloque[] = {json.dumps(salida, ensure_ascii=False, indent=1)};\n")
    print(f"{len(salida)} bloques -> {destino}")


if __name__ == "__main__":
    main()
