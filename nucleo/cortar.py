#!/usr/bin/env python3
"""Corte seco: de las tomas elegidas a una lista de cortes (edl.json).

Uso: python3 nucleo/cortar.py <reel>
Lee <reel>/trabajo/tomas.json:
    {"tomas": [{"clip": "C6762", "desde": 17, "hasta": 31}, ...]}
"desde"/"hasta" son índices de palabra de <reel>/trabajo/<clip>.json, en el orden en que deben sonar.

Dentro de cada toma, toda pausa más larga de lo que pide su puntuación se recorta a esa medida.
Las pausas se miden con la energía del audio, no con los tiempos de Whisper, que estira las palabras
sobre los silencios.
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

PAUSAS = {"nada": 0.06, "coma": 0.14, "punto": 0.28, "fin": 0.35}
COLA = 0.12  # aire que queda después de la última palabra de una toma
# Formatos con más ritmo (dynamic) piden pausas más cortas: tomas.json puede traer "pausas" y "cola".
PASO = 0.01  # resolución de la energía: 10 ms


def energia_db(clip):
    crudo = subprocess.run(
        ["ffmpeg", "-nostdin", "-v", "error", "-i", clip, "-ac", "1", "-ar", "16000", "-f", "s16le", "-"],
        capture_output=True, check=True,
    ).stdout
    x = np.frombuffer(crudo, np.int16).astype(np.float32) / 32768.0
    n = int(16000 * PASO)
    x = x[: len(x) // n * n].reshape(-1, n)
    return 20 * np.log10(np.sqrt((x ** 2).mean(axis=1)) + 1e-9)


def umbral(env):
    piso, voz = np.percentile(env, 10), np.percentile(env, 90)
    return max(piso + 8, voz - 28)


def umbral_fuerte(env):
    """Nivel de la voz principal (la de cámara). Los bordes de toma se buscan con este umbral: el camarógrafo
    ("ya", "acción") y las respiraciones suenan más bajo y superan el umbral normal, pero no este."""
    # En un cuarto con ruido (prueba-01: piso ~-37 dB) p90-16 cae dentro del ruido y el corte deja hasta 0,6 s
    # muertos al inicio de la toma: nunca por debajo del umbral normal (piso + 8 dB).
    return max(np.percentile(env, 90) - 16, umbral(env))


def tipo_pausa(palabra):
    if palabra.endswith((".", "?", "!")):
        return "punto"
    if palabra.endswith((",", ";", ":")):
        return "coma"
    return "nada"


def silencio(env, th, t0, t1):
    """Tramo sin voz más largo entre t0 y t1: (inicio, fin) o None."""
    a, b = max(0, int(t0 / PASO)), min(len(env), int(t1 / PASO))
    mejor, ini = None, None
    for k in range(a, b + 1):
        callado = k < b and env[k] <= th
        if callado and ini is None:
            ini = k
        elif not callado and ini is not None:
            if mejor is None or k - ini > mejor[1] - mejor[0]:
                mejor = (ini, k)
            ini = None
    return (mejor[0] * PASO, mejor[1] * PASO) if mejor else None


def arranque(env, th, t, antes=0.15, despues=0.3, sostenida=3):
    """Primer instante con voz sostenida (`sostenida` x 10 ms) cerca del inicio que dio Whisper.
    La ventana mira poco hacia atrás: más allá suele estar la respiración previa, que supera el umbral."""
    for k in range(max(0, int((t - antes) / PASO)), min(len(env) - sostenida, int((t + despues) / PASO))):
        if (env[k:k + sostenida] > th).all():
            return k * PASO
    return t


def caida(env, th, t, desde, despues=0.15):
    """Última voz de la palabra, buscando hacia atrás desde poco después del final que dio Whisper
    hasta el inicio de la palabra (`desde`): Whisper a veces estira la última palabra casi un segundo."""
    for k in range(min(len(env) - 1, int((t + despues) / PASO)), max(1, int(desde / PASO)), -1):
        if env[k] > th and env[k - 1] > th:
            return (k + 1) * PASO
    return t


def cortar_toma(env, th, w, d, h):
    tramos = []
    # Whisper puede adelantar el inicio de la primera palabra hasta medio segundo (C6766: dijo 3,24 s y la voz
    # empieza en 3,74 s), así que la ventana mira bastante hacia delante y con el umbral de la voz principal.
    fuerte = umbral_fuerte(env)
    # 80 ms sostenidos: un "ya" del camarógrafo dura ~60 ms por encima del umbral, la voz de cámara no.
    t_in = max(0.0, arranque(env, fuerte, w[d]["inicio"], antes=0.15, despues=0.7, sostenida=8) - 0.08)
    for i in range(d, h):
        meta = PAUSAS[tipo_pausa(w[i]["texto"])]
        s = silencio(env, th, w[i]["fin"] - 0.15, w[i + 1]["inicio"] + 0.15)
        if s and s[1] - s[0] > max(meta + 0.05, 0.12):
            tramos.append((t_in, s[0] + meta * 0.55))
            t_in = s[1] - meta * 0.45
    fin = caida(env, fuerte, w[h]["fin"], w[h]["inicio"]) + COLA
    tramos.append((t_in, min(fin, len(env) * PASO)))
    return [(round(a, 3), round(b, 3)) for a, b in tramos if b - a > 0.05]


def main(reel):
    trabajo = Path(reel) / "trabajo"
    global COLA
    conf = json.loads((trabajo / "tomas.json").read_text())
    tomas = conf["tomas"]
    PAUSAS.update(conf.get("pausas", {}))
    COLA = conf.get("cola", COLA)
    cortes, energias = [], {}
    for n, tm in enumerate(tomas):
        clip = tm["clip"]
        w = json.loads((trabajo / f"{clip}.json").read_text())["palabras"]
        if clip not in energias:
            env = energia_db(str(Path(reel) / "crudos" / f"{clip}.MP4"))
            energias[clip] = (env, umbral(env))
        env, th = energias[clip]
        for a, b in cortar_toma(env, th, w, tm["desde"], tm["hasta"]):
            cortes.append({"toma": n, "clip": clip, "in": a, "out": b})
    total = sum(c["out"] - c["in"] for c in cortes)
    (trabajo / "edl.json").write_text(json.dumps({"cortes": cortes, "duracion": round(total, 3)}, indent=1))
    for c in cortes:
        print(f'toma {c["toma"] + 1}  {c["clip"]}  {c["in"]:7.2f} -> {c["out"]:7.2f}  ({c["out"] - c["in"]:.2f}s)')
    print(f"\n{len(tomas)} tomas -> {len(cortes)} cortes, {total:.1f}s")


if __name__ == "__main__":
    main(sys.argv[1])
