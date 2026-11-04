#!/usr/bin/env python3
"""Arma un anuncio corto de b-roll (Meta Ads) desde crudos horizontales 4K: planos verticales, textos animados,
placa final desenfocada y audio mezclado a -14 LUFS. Pensado para lotes como Spine Labs (marcas/spine-labs).

Uso:
  python3 nucleo/anuncio.py <reel> <guion.json> --storyboard     # hoja de cuadros (uno por plano) ANTES de renderizar
  python3 nucleo/anuncio.py <reel> <guion.json> [--prueba 12]    # render (completo o solo los primeros N s)

<guion.json> (en <reel>/trabajo/):
{
  "nombre": "bof1",
  "planos": [
    {"clip": "C7731", "desde": 2.0, "dur": 1.8,            # segundos dentro del crudo
     "x": 0.5, "y": 0.5,                                   # centro del recorte vertical (fracción del cuadro 16:9)
     "zoom": [1.0, 1.06],                                  # zoom al inicio y al final del plano (1.0 = 9:16 completo)
     "filtro": "eq=contrast=1.12:saturation=1.2",          # opcional: ffmpeg sobre el crudo (perfil plano)
     "entrada": "barrido",                                 # opcional: barrido con desenfoque de movimiento (0,17 s)
     "desenfoque": [0.2, 0.6]}                             # opcional: se desenfoca de 0,2 s a 0,6 s (placa final)
  ],
  "textos": [
    {"t": 0.15, "hasta": 3.3, "y": 820,                    # tiempo del video; y = centro del bloque (en 1080x1920)
     "lineas": [
       {"segs": [{"txt": "Ever seen an", "tam": 62}]},
       {"segs": [{"txt": "adjustment", "tam": 118, "caja": true}]},
       {"segs": [{"txt": "like", "tam": 80}, {"txt": "this?", "tam": 46, "arriba": true}]}],
     "paso": 0.22}                                         # retraso entre segmentos (si no traen "t" propio)
  ],
  "logo": {"archivo": "marca/logo.png", "t": 9.0, "y": 1350, "ancho": 300},
  "audio": {
    "voz": [{"clip": "C7800", "desde": 1.2, "hasta": 4.6, "en": 0.0, "db": 0}],
    "musica": {"archivo": "musica/pista.mp3", "desde": 0, "db": -18, "duck": true},
    "sfx": [{"archivo": "sfx/whoosh.wav", "en": 2.0, "db": -4.4}]
  }
}
Segmentos de texto: tam (px de em en 1080), color blanco|negro, caja (blanco sobre caja negra), arriba (alineado
arriba, como "this?"), peso Bold|ExtraBold|Black, t (segundos absolutos de entrada).
Salida: <reel>/salida/<nombre>.mp4 (1080x1920, fps del crudo, H.264 + AAC, -14 LUFS, pico -1 dBTP).
"""
import argparse
import json
import subprocess
from functools import lru_cache
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1080, 1920
FUENTES = {p: f"/usr/share/fonts/opentype/inter/Inter-{p}.otf" for p in ("Bold", "ExtraBold", "Black", "SemiBold")}
ENTRA_S, SALE_S, BARRIDO_S = 0.2, 0.16, 0.17
TRACKING = -0.035      # fracción del em, letras apretadas como en las ediciones de Sebas


def suave(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)


def sale(u):
    u = min(max(u, 0.0), 1.0)
    return 1 - (1 - u) ** 3


# ---------- textos ----------

@lru_cache(None)
def fuente(peso, tam):
    return ImageFont.truetype(FUENTES[peso], tam)


def sprite_seg(seg):
    """RGBA del segmento con su sombra difusa y su caja; devuelve (imagen, ascenso hasta la línea base)."""
    tam, peso = seg["tam"], seg.get("peso", "Bold")
    f = fuente(peso, tam)
    txt = seg["txt"]
    track = TRACKING * tam
    xs = [f.getlength(txt[:i]) + i * track for i in range(len(txt))]
    ancho = int(xs[-1] + f.getlength(txt[-1])) if txt else 0
    asc, desc = f.getmetrics()
    cap = f.getbbox("H")[1]                       # espacio vacío sobre las mayúsculas
    alto_txt = asc + desc
    caja = seg.get("caja", False)
    px, py = (int(tam * 0.13), int(tam * 0.02)) if caja else (0, 0)
    m = int(tam * 0.45)                           # margen para la sombra
    iw, ih = ancho + 2 * px + 2 * m, alto_txt - cap + 2 * py + 2 * m
    capa_txt = Image.new("L", (iw, ih), 0)
    d = ImageDraw.Draw(capa_txt)
    for ch, x in zip(txt, xs):
        d.text((m + px + x, m + py - cap), ch, font=f, fill=255)
    color = (0, 0, 0) if seg.get("color") == "negro" and not caja else (255, 255, 255)
    img = Image.new("RGBA", (iw, ih), (0, 0, 0, 0))
    if caja:
        caja_img = Image.new("RGBA", (iw, ih), (0, 0, 0, 0))
        ImageDraw.Draw(caja_img).rectangle([m, m, iw - m, ih - m - int(desc * 0.35)], fill=(0, 0, 0, 255))
        img = Image.alpha_composite(img, caja_img)
    else:
        # resplandor: oscuro detrás del blanco, claro detrás del negro (nunca contorno pegado)
        sombra = capa_txt.filter(ImageFilter.GaussianBlur(tam * 0.16))
        tono, op = ((0, 0, 0), 0.5) if color == (255, 255, 255) else ((255, 255, 255), 0.35)
        s = Image.new("RGBA", (iw, ih), tono + (0,))
        s.putalpha(sombra.point(lambda v: int(v * op)))
        img = Image.alpha_composite(img, s)
    letras = Image.new("RGBA", (iw, ih), color + (0,))
    letras.putalpha(capa_txt)
    img = Image.alpha_composite(img, letras)
    linea_base = m + py - cap + asc
    return np.array(img), {"m": m, "py": py, "w": ancho + 2 * px, "h": alto_txt - cap + 2 * py,
                           "base": linea_base - m, "cap_h": asc - cap}


def maquetar(bloque):
    """Posición de cada segmento (centrado en x=540, bloque centrado en y)."""
    lineas, filas, y = [], [], 0.0
    for li in bloque["lineas"]:
        segs = [(s, *sprite_seg(s)) for s in li["segs"]]
        esp = [int(s["tam"] * 0.22) for s, _, _ in segs]
        ancho = sum(g["w"] for _, _, g in segs) + sum(esp[:-1])
        cap_max = max(g["cap_h"] for _, _, g in segs)
        filas.append((segs, esp, ancho, cap_max, y))
        y += cap_max + max(s["tam"] for s, _, _ in segs) * li.get("aire", 0.2)
    alto = y - max(s["tam"] for s, _, _ in filas[-1][0]) * bloque["lineas"][-1].get("aire", 0.2)
    y0 = bloque.get("y", 960) - alto / 2
    k = 0
    for segs, esp, ancho, cap_max, yl in filas:
        x = W / 2 - ancho / 2 + bloque.get("dx", 0)
        for (s, img, g), e in zip(segs, esp):
            base = y0 + yl + cap_max                       # línea base de la fila
            arriba_cap = y0 + yl + cap_max * 0.22 if s.get("arriba") else base - g["cap_h"]   # borde superior de las mayúsculas
            t = s.get("t", bloque["t"] + k * bloque.get("paso", 0.2))
            lineas.append({"img": img, "x": x - g["m"], "y": arriba_cap - g["m"] - g["py"], "t": t})
            x += g["w"] + e
            k += 1
    return lineas


def pegar(fr, img, x, y, alfa=1.0):
    """Mezcla un RGBA sobre el cuadro BGR (float) en (x, y)."""
    h, w = img.shape[:2]
    x, y = int(round(x)), int(round(y))
    x0, y0, x1, y1 = max(x, 0), max(y, 0), min(x + w, W), min(y + h, H)
    if x0 >= x1 or y0 >= y1:
        return
    sub = img[y0 - y:y1 - y, x0 - x:x1 - x].astype(np.float32)
    a = sub[..., 3:4] / 255.0 * alfa
    fr[y0:y1, x0:x1] = fr[y0:y1, x0:x1] * (1 - a) + sub[..., 2::-1] * a


def barrer(img, largo):
    """Desenfoque de movimiento horizontal sobre un RGBA (premultiplicado para no ensuciar bordes)."""
    largo = int(largo)
    if largo < 2:
        return img
    k = np.ones((1, largo), np.float32) / largo
    f = img.astype(np.float32)
    a = f[..., 3:4] / 255.0
    pre = np.concatenate([f[..., :3] * a, f[..., 3:4]], axis=2)
    pre = cv2.filter2D(pre, -1, k, borderType=cv2.BORDER_CONSTANT)
    a2 = np.maximum(pre[..., 3:4] / 255.0, 1e-4)
    return np.concatenate([pre[..., :3] / a2, pre[..., 3:4]], axis=2).clip(0, 255).astype(np.uint8)


def dibujar_textos(fr, t, bloques):
    for b in bloques:
        if t < b["t"] - 0.01 or t >= b.get("hasta", 1e9):
            continue
        u_sal = (t - (b.get("hasta", 1e9) - SALE_S)) / SALE_S
        for s in b["_segs"]:
            u = (t - s["t"]) / ENTRA_S
            if u < 0:
                continue
            ue = sale(u)
            img = s["img"]
            dx = -46 * (1 - ue)
            borr = 48 * (1 - ue)
            alfa = min(1.0, u * 1.6)
            if u_sal > 0:                                  # salida borrosa
                borr = max(borr, 40 * suave(u_sal))
                alfa *= 1 - suave(u_sal)
            pegar(fr, barrer(img, borr), s["x"] + dx, s["y"], alfa)


# ---------- imagen ----------

def leer_plano(crudo, p, fps):
    """Cuadros del plano ya recortados a la franja vertical (alto completo, ancho 9:16)."""
    info = sonda(crudo)
    cw, ch = info["w"], info["h"]
    fw = int(round(ch * 9 / 16 / 2) * 2)
    cx = int(np.clip(p.get("x", 0.5) * cw - fw / 2, 0, cw - fw))
    filtro = f"crop={fw}:{ch}:{cx}:0"
    if p.get("filtro"):
        filtro = p["filtro"] + "," + filtro
    n = int(round(p["dur"] * fps))
    cmd = ["ffmpeg", "-nostdin", "-v", "error", "-ss", f'{p["desde"]:.3f}', "-i", str(crudo), "-frames:v", str(n),
           "-vf", filtro, "-pix_fmt", "bgr24", "-f", "rawvideo", "-"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    tam = fw * ch * 3
    for _ in range(n):
        buf = proc.stdout.read(tam)
        if len(buf) < tam:
            break
        yield np.frombuffer(buf, np.uint8).reshape(ch, fw, 3)
    proc.stdout.close()
    proc.wait()


def encuadrar(fr, z, ay):
    """Zoom z (>=1) dentro de la franja vertical, anclado en ay (fracción vertical), a 1080x1920."""
    h, w = fr.shape[:2]
    cw, ch = w / z, h / z
    x0 = (w - cw) / 2
    y0 = np.clip(ay * h - ch / 2, 0, h - ch)
    m = np.array([[W / cw, 0, -x0 * W / cw], [0, H / ch, -y0 * H / ch]], np.float32)
    return cv2.warpAffine(fr, m, (W, H), flags=cv2.INTER_AREA if z < 1.6 else cv2.INTER_CUBIC)


@lru_cache(None)
def sonda(crudo):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "stream=width,height,r_frame_rate", "-of", "json", str(crudo)],
                         capture_output=True, text=True, check=True).stdout
    s = json.loads(out)["streams"][0]
    a, b = s["r_frame_rate"].split("/")
    return {"w": s["width"], "h": s["height"], "fps": int(a) / int(b), "fps_txt": s["r_frame_rate"]}


def cuadros(reel, g, fps, limite=None, solo=None):
    """Genera (t, cuadro BGR float) del anuncio completo, o solo los tiempos de `solo`."""
    t0 = 0.0
    bloques = g.get("textos", [])
    for b in bloques:
        b["_segs"] = maquetar(b)
    logo = None
    if g.get("logo"):
        L = g["logo"]
        im = Image.open(Path(reel) / "trabajo" / L["archivo"]).convert("RGBA")
        im = im.resize((L["ancho"], int(im.height * L["ancho"] / im.width)), Image.LANCZOS)
        logo = (np.array(im), L)
    k_global = 0
    for i, p in enumerate(g["planos"]):
        crudo = Path(reel) / "crudos" / f'{p["clip"]}.MP4'
        n = int(round(p["dur"] * fps))
        tiempos = [t0 + k / fps for k in range(n)]
        if solo is not None and not any(t0 <= s < t0 + p["dur"] for s in solo):
            t0 += n / fps
            k_global += n
            continue
        z0, z1 = p.get("zoom", [1.0, 1.0])
        for k, fr in enumerate(leer_plano(crudo, p, fps)):
            t = tiempos[k]
            if limite and t >= limite:
                return
            if solo is not None and not any(abs(t - s) < 0.5 / fps for s in solo):
                continue
            u = k / max(n - 1, 1)
            img = encuadrar(fr, z0 + (z1 - z0) * suave(u), p.get("y", 0.5)).astype(np.float32)
            if p.get("desenfoque"):
                a, b = p["desenfoque"]
                sig = 16 * suave((k / fps - a) / (b - a))
                if sig > 0.3:
                    img = cv2.GaussianBlur(img, (0, 0), sig)
            if p.get("entrada") == "barrido" and k / fps < BARRIDO_S:
                v = 1 - sale(k / fps / BARRIDO_S)
                largo = int(140 * v)
                if largo > 2:
                    img = cv2.filter2D(img, -1, np.ones((1, largo), np.float32) / largo)
                img = np.roll(img, int(-120 * v), axis=1)
            sig_p = g["planos"][i + 1] if i + 1 < len(g["planos"]) else None
            if sig_p and sig_p.get("entrada") == "barrido" and (n - k) / fps <= BARRIDO_S * 0.6:
                v = 1 - (n - k) / fps / (BARRIDO_S * 0.6)
                largo = int(140 * v)
                if largo > 2:
                    img = cv2.filter2D(img, -1, np.ones((1, largo), np.float32) / largo)
                img = np.roll(img, int(120 * v), axis=1)
            dibujar_textos(img, t, bloques)
            if logo is not None and t >= logo[1]["t"]:
                L = logo[1]
                a = sale((t - L["t"]) / ENTRA_S)
                pegar(img, logo[0], W / 2 - logo[0].shape[1] / 2, L["y"] - logo[0].shape[0] / 2 + 30 * (1 - a), a)
            yield t, img
        t0 += n / fps
        k_global += n


# ---------- audio ----------

def mezclar_audio(reel, g, dur, destino):
    """Voz (de los crudos), música con ducking y efectos -> wav a -14 LUFS / -1 dBTP."""
    A = g.get("audio", {})
    entradas, cadenas, voces = [], [], []
    for j, v in enumerate(A.get("voz", [])):
        entradas += ["-i", str(Path(reel) / "crudos" / f'{v["clip"]}.MP4')]
        largo = v["hasta"] - v["desde"]
        cadenas.append(
            f'[{len(entradas)//2 - 1}:a]atrim={v["desde"]}:{v["hasta"]},asetpts=PTS-STARTPTS,aformat=channel_layouts=mono,'
            f'highpass=f=80,afftdn=nf=-30,acompressor=threshold=-20dB:ratio=3:attack=8:release=120,'
            f'volume={v.get("db", 0)}dB,afade=t=in:d=0.04,afade=t=out:st={max(largo - 0.06, 0)}:d=0.06,'
            f'adelay={int(v["en"] * 1000)}:all=1,apad=whole_dur={dur}[v{j}]')
        voces.append(f"[v{j}]")
    pistas = []
    if voces:
        cadenas.append(f'{"".join(voces)}amix=inputs={len(voces)}:normalize=0,atrim=0:{dur}[voz]')
    M = A.get("musica")
    if M:
        entradas += ["-i", str(Path(reel) / "trabajo" / M["archivo"])]
        idx = len(entradas) // 2 - 1
        cadenas.append(f'[{idx}:a]atrim={M.get("desde", 0)}:{M.get("desde", 0) + dur},asetpts=PTS-STARTPTS,'
                       f'aformat=channel_layouts=stereo,volume={M.get("db", -18)}dB,'
                       f'afade=t=out:st={max(dur - M.get("fade", 0.8), 0)}:d={M.get("fade", 0.8)}[mus0]')
        if voces and M.get("duck", True):
            cadenas.append("[voz]asplit[voz][vsc]")
            cadenas.append("[mus0][vsc]sidechaincompress=threshold=0.03:ratio=6:attack=20:release=300[mus]")
        else:
            cadenas.append("[mus0]anull[mus]")
        pistas.append("[mus]")
    if voces:
        pistas.append("[voz]")
    for j, s in enumerate(A.get("sfx", [])):
        entradas += ["-i", str(Path(reel) / "trabajo" / s["archivo"])]
        idx = len(entradas) // 2 - 1
        cadenas.append(f'[{idx}:a]aformat=channel_layouts=stereo,volume={s.get("db", -4.4)}dB,'
                       f'adelay={int(s["en"] * 1000)}:all=1[s{j}]')
        pistas.append(f"[s{j}]")
    if not pistas:
        subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-f", "lavfi", "-i",
                        f"anullsrc=r=48000:cl=stereo", "-t", f"{dur}", str(destino)], check=True)
        return
    cadenas.append(f'{"".join(pistas)}amix=inputs={len(pistas)}:normalize=0,aformat=channel_layouts=stereo,'
                   f'apad=whole_dur={dur},atrim=0:{dur}[mez]')
    crudo = str(destino).replace(".wav", "_mez.wav")
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", *entradas, "-filter_complex", ";".join(cadenas),
                    "-map", "[mez]", "-ar", "48000", crudo], check=True)
    # loudnorm en dos pasadas
    med = subprocess.run(["ffmpeg", "-nostdin", "-hide_banner", "-i", crudo, "-af",
                          "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    j = json.loads(med[med.rindex("{"):med.rindex("}") + 1])
    ln = (f'loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={j["input_i"]}:measured_TP={j["input_tp"]}:'
          f'measured_LRA={j["input_lra"]}:measured_thresh={j["input_thresh"]}:offset={j["target_offset"]}:linear=true')
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", crudo, "-af", ln + ",alimiter=limit=0.89",
                    "-ar", "48000", str(destino)], check=True)


# ---------- principal ----------

def duracion(g, fps):
    return sum(int(round(p["dur"] * fps)) for p in g["planos"]) / fps


def storyboard(reel, g, fps):
    """Hoja con un cuadro por plano (a 60 % del plano, o en "muestra"), numerado y con el segundo."""
    tiempos, t0 = [], 0.0
    for p in g["planos"]:
        n = int(round(p["dur"] * fps))
        tiempos.append(t0 + p.get("muestra", 0.6) * n / fps)
        t0 += n / fps
    tiempos = [round(t * fps) / fps for t in tiempos]
    hechos = {round(t, 3): img for t, img in cuadros(reel, g, fps, solo=tiempos)}
    mini = []
    for i, t in enumerate(tiempos):
        img = hechos.get(round(t, 3))
        if img is None:
            img = min(hechos.items(), key=lambda kv: abs(kv[0] - t))[1]
        im = cv2.resize(img.clip(0, 255).astype(np.uint8), (360, 640), interpolation=cv2.INTER_AREA)
        cv2.rectangle(im, (300, 0), (360, 44), (0, 0, 0), -1)
        cv2.putText(im, str(i + 1), (310, 33), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.rectangle(im, (0, 600), (120, 640), (0, 0, 0), -1)
        cv2.putText(im, f"{t:.1f}s", (8, 630), cv2.FONT_HERSHEY_SIMPLEX, 0.85, (255, 255, 255), 2, cv2.LINE_AA)
        mini.append(im)
    cols = min(len(mini), 6)
    while len(mini) % cols:
        mini.append(np.zeros_like(mini[0]))
    filas = [np.hstack(mini[r:r + cols]) for r in range(0, len(mini), cols)]
    destino = Path(reel) / "salida" / f'{g["nombre"]}_storyboard.jpg'
    cv2.imwrite(str(destino), np.vstack(filas), [cv2.IMWRITE_JPEG_QUALITY, 88])
    print(destino)


def render(reel, g, fps, fps_txt, limite=None):
    dur = duracion(g, fps) if not limite else min(limite, duracion(g, fps))
    sal = Path(reel) / "salida"
    sal.mkdir(exist_ok=True)
    nombre = g["nombre"] + ("_prueba" if limite else "")
    wav = Path(reel) / "trabajo" / f"{nombre}_audio.wav"
    mezclar_audio(reel, g, dur, wav)
    destino = sal / f"{nombre}.mp4"
    enc = subprocess.Popen(["ffmpeg", "-nostdin", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24",
                            "-s", f"{W}x{H}", "-r", fps_txt, "-i", "-", "-i", str(wav), "-map", "0:v", "-map", "1:a",
                            "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p",
                            "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
                            "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart", "-shortest", str(destino)],
                           stdin=subprocess.PIPE)
    for _, img in cuadros(reel, g, fps, limite=limite):
        enc.stdin.write(img.clip(0, 255).astype(np.uint8).tobytes())
    enc.stdin.close()
    enc.wait()
    print(destino, f"{dur:.2f}s")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("reel")
    ap.add_argument("guion")
    ap.add_argument("--storyboard", action="store_true")
    ap.add_argument("--prueba", type=float)
    a = ap.parse_args()
    g = json.loads((Path(a.reel) / "trabajo" / a.guion).read_text())
    info = sonda(Path(a.reel) / "crudos" / f'{g["planos"][0]["clip"]}.MP4')
    if a.storyboard:
        storyboard(a.reel, g, info["fps"])
    else:
        render(a.reel, g, info["fps"], info["fps_txt"], a.prueba)


if __name__ == "__main__":
    main()
