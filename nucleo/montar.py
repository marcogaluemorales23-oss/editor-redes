#!/usr/bin/env python3
"""Monta la base sin textos a partir de edl.json: 1080x1920, fps del crudo, audio a -14 LUFS.

Uso: python3 nucleo/montar.py <reel> [--zoom 1.12,1.28] [--sin-centrar]
--zoom: acercamiento por corte (se repite en ciclo). Por defecto zoom base de 12 % (pedido de Sebas) y
alterna con un plano 15 % más cerrado.
Encuadre: detecta la cara en cada corte y la centra en horizontal, con el centro de la cara a y≈930
(como en la edición de Sebas). Si la cara está muy corrida, sube el zoom lo justo para poder centrarla.
"""
import argparse
import json
import subprocess
from pathlib import Path

CARA_Y = 930        # altura del centro de la cara en el cuadro final (Sebas: 870-1000)
TOLERANCIA_X = 25   # px que se acepta la cara fuera del centro antes de subir el zoom
ZOOM_MAX = 1.35


def zoom_para_centrar(cx):
    """Zoom mínimo que deja recorrer lo suficiente para poner la cara (cx en el crudo a 1080 de ancho) en x=540."""
    dx = abs(cx - 540)
    return 1.0 if dx <= TOLERANCIA_X else min(ZOOM_MAX, (540 - TOLERANCIA_X) / (540 - dx))


def fps_de(clip):
    return subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=r_frame_rate",
         "-of", "csv=p=0", clip], capture_output=True, text=True, check=True,
    ).stdout.strip().strip(",")


def a_cuadros(cortes, num, den):
    """Lleva cada corte a la rejilla de cuadros del crudo: el inicio cae justo en un cuadro y la duración es un
    número entero de cuadros. Así imagen y sonido arrancan en el mismo instante. Si el audio empieza en el
    instante exacto del corte y la imagen en el cuadro más cercano, quedan hasta medio cuadro (~21 ms)
    desfasados (en video-01, -24 ms en C6767). Guarda los puntos de cortar.py en in_cortar/out_cortar."""
    for c in cortes:
        c.setdefault("in_cortar", c["in"])
        c.setdefault("out_cortar", c["out"])
        cuadro_in = round(c["in_cortar"] * num / den)
        cuadros = max(1, round((c["out_cortar"] - c["in_cortar"]) * num / den))
        c["in"] = cuadro_in * den / num
        c["out"] = (cuadro_in + cuadros) * den / num
    return cortes


def cuadrar_linea_de_tiempo(trabajo, cortes):
    """Guarda edl.json ya en cuadros y mueve los tiempos de corte_check.json (subtítulos, b-roll, botón) a la
    nueva línea de tiempo, tramo por tramo, para que no quede un desfase de unos ms que se acumule."""
    viejos, nuevos, corrimiento, t0, t1 = [], [], [], 0.0, 0.0
    for c in cortes:
        d_vieja = c["out_cortar"] - c["in_cortar"]
        viejos.append((t0, t0 + d_vieja))
        nuevos.append(t1)
        corrimiento.append(c["in"] - c["in_cortar"])
        t0, t1 = t0 + d_vieja, t1 + (c["out"] - c["in"])
    edl = json.loads((trabajo / "edl.json").read_text())
    edl["cortes"], edl["duracion"] = cortes, round(t1, 6)
    (trabajo / "edl.json").write_text(json.dumps(edl, indent=1))

    check = trabajo / "corte_check.json"
    original = trabajo / "corte_check_sin_cuadrar.json"  # tiempos tal como salen de cortar.py
    if not check.exists():
        return
    if not original.exists():
        original.write_text(check.read_text())
    datos = json.loads(original.read_text())

    def mover(t):
        k = next((i for i, (a, b) in enumerate(viejos) if t < b), len(viejos) - 1)
        return round(t - viejos[k][0] + nuevos[k] - corrimiento[k], 3)

    for p in datos["palabras"]:
        p["inicio"], p["fin"] = mover(p["inicio"]), mover(p["fin"])
    check.write_text(json.dumps(datos, ensure_ascii=False, indent=1))
    print(f"línea de tiempo cuadrada a cuadros enteros: {t0:.3f}s -> {t1:.3f}s")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("reel")
    ap.add_argument("--zoom", default="1.12,1.28")
    ap.add_argument("--sin-centrar", action="store_true")
    a = ap.parse_args()
    reel = Path(a.reel)
    trabajo = reel / "trabajo"
    tramos = trabajo / "tramos"
    tramos.mkdir(exist_ok=True)
    cortes = json.loads((trabajo / "edl.json").read_text())["cortes"]
    zooms = [float(z) for z in a.zoom.split(",")]
    fps = fps_de(str(reel / "crudos" / f'{cortes[0]["clip"]}.MP4'))

    # Movimientos por tramo (opcional): {"0": {"empuje": 0.08, "golpe_en": 0.95, "golpe": 0.12, "abre": 0.3}}
    # empuje = acercamiento suave a lo largo del tramo; golpe = acercamiento rápido (150 ms) en un segundo dado.
    archivo_mov = trabajo / "movimientos.json"
    movimientos = json.loads(archivo_mov.read_text()) if archivo_mov.exists() else {}

    num, den = (int(x) for x in fps.split("/")) if "/" in fps else (float(fps), 1)
    cortes = a_cuadros(cortes, num, den)
    # encuadre.json (opcional): {"ancho_cara": 600, "cara_y": 880, "zoom_max": 2.0}. Con esto la persona queda del
    # mismo tamaño y a la misma altura en todos los planos (pedido de Sebas: el subtítulo siempre bajo la barbilla,
    # en una línea fija). Si en una toma está tan cerca que la cara ya es más grande, se deja en zoom 1 (no se puede
    # achicar) y se anota su barbilla en encuadre_tramos.json para que subtitulos.py baje el texto solo ahí.
    archivo_enc = trabajo / "encuadre.json"
    encuadre = json.loads(archivo_enc.read_text()) if archivo_enc.exists() else None
    cara_y = encuadre.get("cara_y", CARA_Y) if encuadre else CARA_Y
    tramos_enc, t_linea = [], 0.0
    archivo_sync = trabajo / "sincronia.json"
    ajustes = json.loads(archivo_sync.read_text()) if archivo_sync.exists() else {}
    lista = []
    for k, c in enumerate(cortes):
        z = zooms[k % len(zooms)]
        # movimientos.json puede fijar el zoom de un tramo ("zoom": 1.0), p. ej. para abrir el plano y dejar
        # espacio a un gráfico sin tapar la cara.
        z = movimientos.get(str(k), {}).get("zoom", z)
        # Duración exacta en cuadros enteros, igual para imagen y sonido. Si el video se redondea a cuadros y el
        # audio no, cada tramo queda unos ms más largo en imagen y al unirlos la voz se adelanta a los labios
        # (en video-01 llegó a ~200 ms a mitad del reel).
        cuadros = round((c["out"] - c["in"]) * num / den)
        d = cuadros * den / num
        crudo = reel / "crudos" / f'{c["clip"]}.MP4'
        cx, cy, fw = 540.0, cara_y * 1.0, None
        if not a.sin_centrar:
            from caras import caras
            vistas = [x for x in caras(crudo, [c["in"] + 0.2, c["in"] + d / 2, c["out"] - 0.2]) if x[1] is not None]
            if vistas:
                cx = sorted(x[1] for x in vistas)[len(vistas) // 2]
                cy = sorted(x[2] for x in vistas)[len(vistas) // 2]
                fw = sorted(x[3] for x in vistas)[len(vistas) // 2]
                if encuadre and "zoom" not in movimientos.get(str(k), {}):
                    z = min(encuadre.get("zoom_max", 2.0), max(1.0, encuadre["ancho_cara"] / fw))
                z = max(z, zoom_para_centrar(cx))
                if encuadre:  # Sebas: "estás aumentando demasiado la escala": nunca más que zoom_max, aunque
                    z = min(z, encuadre.get("zoom_max", 2.0))  # la cara quede un poco corrida
        mov = movimientos.get(str(k))
        if mov:
            # zoompan sobre el crudo 4K (2x la salida): el zoom se calcula en cada cuadro y no tiembla.
            golpe = (f"+{mov.get('golpe', 0)}*st(0,clip((it-{mov.get('golpe_en', 0)})/0.15,0,1))"
                     f"*ld(0)*(3-2*ld(0))") if "golpe_en" in mov else ""
            # "abre": arranca más cerca y se abre en 0,3 s (interrupción de patrón en el primer cuadro).
            abre = (f"+{mov['abre']}*(1-st(1,clip(it/0.3,0,1))*ld(1)*(3-2*ld(1)))") if "abre" in mov else ""
            zexpr = f"{z}*(1+{mov.get('empuje', 0)}*it/{d:.3f}{golpe}{abre})"
            vf = (f"scale=2160:3840:flags=lanczos,fps={fps},"
                  f"zoompan=z='{zexpr}':x='max(0,min(iw-iw/zoom,{cx * 2:.1f}-iw/zoom/2))'"
                  f":y='max(0,min(ih-ih/zoom,{cy * 2:.1f}-ih/zoom*{cara_y / 1920:.4f}))':d=1:s=1080x1920:fps={fps},"
                  f"format=yuv420p")
        else:
            w, h = round(1080 * z / 2) * 2, round(1920 * z / 2) * 2
            # Recorte con la cara centrada en x y a la altura CARA_Y, sin salirse del cuadro.
            x = max(0, min(w - 1080, cx * z - 540))
            y = max(0, min(h - 1920, cy * z - cara_y))
            vf = f"scale={w}:{h}:flags=lanczos,crop=1080:1920:{x:.0f}:{y:.0f},fps={fps},format=yuv420p"
        af = (f"aresample=48000,apad,atrim=0:{d:.6f},asetpts=PTS-STARTPTS,"
              f"afade=t=in:d=0.01,afade=t=out:st={d - 0.012:.6f}:d=0.012")
        salida = tramos / f"{k:02d}.mp4"
        # Ajuste fino por clip (sincronia.json, en ms): positivo = el audio suena más tarde respecto a la imagen.
        # Se usa solo si Sebas ve desfase a ojo en un clip; por defecto 0.
        ajuste = ajustes.get(c["clip"], 0) / 1000
        crudo_clip = str(reel / "crudos" / f'{c["clip"]}.MP4')
        subprocess.run(
            ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{c['in'] - 0.001:.6f}", "-t", f"{d + 0.2:.3f}",
             "-i", crudo_clip, "-ss", f"{max(0.0, c['in'] - 0.001 - ajuste):.6f}", "-t", f"{d + 0.2:.3f}",
             "-i", crudo_clip, "-map", "0:v:0", "-map", "1:a:0",
             "-vf", vf, "-af", af, "-frames:v", str(cuadros),
             "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-c:a", "pcm_s16le", "-ar", "48000",
             str(salida.with_suffix(".mov"))], check=True,
        )
        lista.append(f"file '{salida.with_suffix('.mov').name}'")
        print(f"tramo {k + 1}/{len(cortes)} listo: zoom {z:.2f}, cara en el crudo x={cx:.0f} y={cy:.0f}")
        if fw:
            # Dónde queda la cara en el cuadro final (el recorte no puede salirse del crudo) y su barbilla.
            y_cara = cy * z - max(0.0, min(1920 * z - 1920, cy * z - cara_y))
            tramos_enc.append({"desde": round(t_linea, 3), "hasta": round(t_linea + d, 3), "zoom": round(z, 3),
                               "cara_y": round(y_cara), "barbilla": round(y_cara + 0.62 * fw * z)})
        t_linea += d
    (tramos / "lista.txt").write_text("\n".join(lista) + "\n")
    (trabajo / "encuadre_tramos.json").write_text(json.dumps(tramos_enc, indent=1))
    cuadrar_linea_de_tiempo(trabajo, cortes)

    base = trabajo / "base.mp4"
    subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0",
         "-i", str(tramos / "lista.txt"), "-c:v", "copy",
         "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
         "-movflags", "+faststart", str(base)], check=True,
    )
    print(f"base -> {base}")


if __name__ == "__main__":
    main()
