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
     "desenfoque": [0.2, 0.6],                             # opcional: se desenfoca de 0,2 s a 0,6 s (placa final)
     "sigma": 16, "oscurecer": 0.3}                        # fuerza del desenfoque y cuánto se oscurece (0-1)
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
    "musica": {"archivo": "musica/pista.mp3", "desde": 0, "db": -18, "duck": true,
               "eq": "highshelf=f=5000:g=-4"},                 # opcional: ecualizador ffmpeg (suavizar agudos)
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
# fuentes variables (Google Fonts, licencia OFL) en nucleo/fuentes: "peso": "Montserrat:300", "Jost:500", "Cormorant:500"
VARIABLES = {"Raleway": "Raleway-VF.ttf", "Montserrat": "Montserrat-VF.ttf", "Jost": "Jost-VF.ttf", "Cormorant": "CormorantGaramond-Italic-VF.ttf"}
COLORES = {"blanco": (255, 255, 255), "negro": (0, 0, 0), "verde": (138, 168, 136)}   # verde salvia del logo "SL"
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
    if ":" in peso:                                # fuente variable con su peso: "Montserrat:300"
        fam, w = peso.split(":")
        f = ImageFont.truetype(str(Path(__file__).parent / "fuentes" / VARIABLES[fam]), tam)
        f.set_variation_by_axes([int(w)])
        return f
    return ImageFont.truetype(FUENTES[peso], tam)


def sprite_seg(seg):
    """RGBA del segmento con su sombra difusa y su caja; devuelve (imagen, ascenso hasta la línea base)."""
    tam, peso = seg["tam"], seg.get("peso", "Bold")
    f = fuente(peso, tam)
    txt = seg["txt"]
    track = seg.get("tracking", TRACKING) * tam
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
    color = (255, 255, 255) if caja else COLORES.get(seg.get("color", "blanco"), (255, 255, 255))
    img = Image.new("RGBA", (iw, ih), (0, 0, 0, 0))
    if caja:
        caja_img = Image.new("RGBA", (iw, ih), (0, 0, 0, 0))
        ImageDraw.Draw(caja_img).rectangle([m, m, iw - m, ih - m - int(desc * 0.35)], fill=(0, 0, 0, 255))
        img = Image.alpha_composite(img, caja_img)
    else:
        # resplandor: oscuro detrás del blanco, claro detrás del negro (nunca contorno pegado)
        sombra = capa_txt.filter(ImageFilter.GaussianBlur(tam * seg.get("sombra_blur", 0.16)))
        tono, op = ((255, 255, 255), 0.35) if color == (0, 0, 0) else ((0, 0, 0), seg.get("sombra", 0.5))
        s = Image.new("RGBA", (iw, ih), tono + (0,))
        s.putalpha(sombra.point(lambda v: int(v * op)))
        img = Image.alpha_composite(img, s)
    if seg.get("sombra_caida") and not caja:      # sombra proyectada como la referencia de la clínica: [dx, dy, blur, opacidad]
        dx, dy, bl, op = seg["sombra_caida"]
        caida = Image.new("L", (iw, ih), 0)
        caida.paste(capa_txt, (int(dx), int(dy)))
        caida = caida.filter(ImageFilter.GaussianBlur(bl))
        sc = Image.new("RGBA", (iw, ih), (0, 0, 0, 0))
        sc.putalpha(caida.point(lambda v: int(v * op)))
        img = Image.alpha_composite(img, sc)
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
            lineas.append({"img": img, "x": x - g["m"], "y": arriba_cap - g["m"] - g["py"], "t": t,
                           "anim": s.get("anim"), "caja": (x, arriba_cap - g["py"], g["w"], g["h"])})
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


def barrer(img, largo, vertical=False):
    """Desenfoque de movimiento (horizontal o vertical) sobre un RGBA, premultiplicado para no ensuciar bordes."""
    largo = int(largo)
    if largo < 2:
        return img
    k = np.ones((largo, 1) if vertical else (1, largo), np.float32) / largo
    f = img.astype(np.float32)
    a = f[..., 3:4] / 255.0
    pre = np.concatenate([f[..., :3] * a, f[..., 3:4]], axis=2)
    pre = cv2.filter2D(pre, -1, k, borderType=cv2.BORDER_CONSTANT)
    a2 = np.maximum(pre[..., 3:4] / 255.0, 1e-4)
    return np.concatenate([pre[..., :3] / a2, pre[..., 3:4]], axis=2).clip(0, 255).astype(np.uint8)


IZQ_ENTRA_S, IZQ_SALE_S, IZQ_DX = 0.38, 0.3, 90       # "izq_der" (MOF-3)
VERT_ENTRA_S, VERT_SALE_S, VERT_DY = 0.4, 0.28, 70    # "subir" / "bajar" (TOF-4)


def revelar(img, desde, hasta, borde=28):
    """Deja visible solo la franja horizontal [desde, hasta] (fracciones del ancho), con borde suave."""
    w = img.shape[1]
    x = np.arange(w, dtype=np.float32)
    m = np.clip((x - desde * w) / borde + 0.5, 0, 1) * np.clip((hasta * w - x) / borde + 0.5, 0, 1)
    out = img.copy()
    out[..., 3] = (out[..., 3].astype(np.float32) * m[None, :]).astype(np.uint8)
    return out


def dibujar_seg(fr, t, s, anim, hasta):
    """Un segmento de texto con su animación:
    None      entra deslizando desde la izquierda con desenfoque y sale borroso (BOF-1)
    "izq_der" se revela de izquierda a derecha, se detiene en el centro y sigue a la derecha al salir (MOF-3)
    "subir"   sube desde abajo apareciendo (desvanecido + desenfoque vertical) y al salir se desvanece subiendo
    "bajar"   cae desde arriba apareciendo y al salir se desvanece bajando"""
    img = s["img"]
    if anim == "izq_der":
        u = (t - s["t"]) / IZQ_ENTRA_S
        if u < 0:
            return
        ue = sale(u)
        v = suave((t - (hasta - IZQ_SALE_S)) / IZQ_SALE_S) if hasta < 1e8 else 0.0
        dx = -IZQ_DX * (1 - ue) + IZQ_DX * v
        pegar(fr, barrer(revelar(img, v, ue * 1.08), 22 * (1 - ue) + 22 * v), s["x"] + dx, s["y"])
    elif anim == "rebote":                              # sube desde abajo y se asienta con un rebote suave (Sebas)
        u = (t - s["t"]) / 0.5
        if u < 0:
            return
        u = min(u, 1.0)
        c1 = 1.25                                       # sobrepaso pequeño (easeOutBack suave: ~4 % de la subida)
        e = 1 + (c1 + 1) * (u - 1) ** 3 + c1 * (u - 1) ** 2
        v = suave((t - (hasta - 0.22)) / 0.22) if hasta < 1e8 else 0.0
        dy = 46 * (1 - e) - 18 * v
        alfa = min(1.0, u * 2.2) * (1 - v)
        pegar(fr, img, s["x"], s["y"] + dy, alfa)
    elif anim == "corte":                               # subtítulo tipo referencia: aparece y se va en seco
        if t < s["t"]:
            return
        alfa = min(1.0, (t - s["t"]) / 0.05) * min(1.0, max(0.0, (hasta - t) / 0.05))
        pegar(fr, img, s["x"], s["y"], alfa)
    elif anim in ("subir", "bajar"):
        u = (t - s["t"]) / VERT_ENTRA_S
        if u < 0:
            return
        ue = sale(u)
        v = suave((t - (hasta - VERT_SALE_S)) / VERT_SALE_S) if hasta < 1e8 else 0.0
        signo = 1 if anim == "subir" else -1               # subir: viene de abajo (+y) y se va hacia arriba
        dy = signo * VERT_DY * (1 - ue) - signo * 0.6 * VERT_DY * v
        alfa = min(1.0, u * 1.4) * (1 - v)
        pegar(fr, barrer(img, 30 * (1 - ue) + 26 * v, vertical=True), s["x"], s["y"] + dy, alfa)
    else:
        u = (t - s["t"]) / ENTRA_S
        if u < 0:
            return
        ue = sale(u)
        borr, alfa = 48 * (1 - ue), min(1.0, u * 1.6)
        u_sal = (t - (hasta - SALE_S)) / SALE_S
        if u_sal > 0:                                      # salida borrosa
            borr = max(borr, 40 * suave(u_sal))
            alfa *= 1 - suave(u_sal)
        pegar(fr, barrer(img, borr), s["x"] - 46 * (1 - ue), s["y"], alfa)


def _alfa_fondo(t, b, hasta):
    u = sale((t - min(s["t"] for s in b["_segs"])) / 0.35)
    v = suave((t - (hasta - 0.3)) / 0.3) if hasta < 1e8 else 0.0
    return u * (1 - v)


def dibujar_fondo(fr, t, b, hasta):
    """Fondo detrás del bloque, en vez de la caja negra (pedido de la clienta de Andy: más delicado):
    "degradado" sombra oscura muy difusa que solo oscurece la zona del texto (no se ve la forma);
    "vidrio"    píldora de vidrio ahumado por línea: el video desenfocado y algo oscurecido, borde blanco fino."""
    a = _alfa_fondo(t, b, hasta)
    if a <= 0.01:
        return
    cajas = [s["caja"] for s in b["_segs"]]
    if b["fondo"] == "degradado":
        if "_mascara" not in b:
            x0 = min(c[0] for c in cajas) - 150; x1 = max(c[0] + c[2] for c in cajas) + 150
            y0 = min(c[1] for c in cajas) - 110; y1 = max(c[1] + c[3] for c in cajas) + 110
            m = np.zeros((H, W), np.float32)
            cv2.ellipse(m, ((int((x0 + x1) / 2), int((y0 + y1) / 2)), (int(x1 - x0), int(y1 - y0)), 0), 1.0, -1)
            m = cv2.GaussianBlur(m, (0, 0), 70)
            b["_mascara"] = (m / max(m.max(), 1e-6))[..., None]
        fr *= 1 - b.get("fuerza", 0.5) * a * b["_mascara"]
    elif b["fondo"] == "vidrio":
        filas = {}
        for c in cajas:                                   # una píldora por línea
            k = round(c[1] / 10)
            x0, y0, x1, y1 = c[0], c[1], c[0] + c[2], c[1] + c[3]
            f = filas.get(k)
            filas[k] = (min(f[0], x0), min(f[1], y0), max(f[2], x1), max(f[3], y1)) if f else (x0, y0, x1, y1)
        for x0, y0, x1, y1 in filas.values():
            px, py = 34, 20
            X0, Y0 = int(max(x0 - px, 0)), int(max(y0 - py, 0))
            X1, Y1 = int(min(x1 + px, W)), int(min(y1 + py, H))
            hh, ww = Y1 - Y0, X1 - X0
            m = np.zeros((hh, ww), np.float32)
            r = hh // 2
            cv2.rectangle(m, (r, 0), (ww - r, hh), 1.0, -1)
            cv2.circle(m, (r, r), r, 1.0, -1); cv2.circle(m, (ww - r, r), r, 1.0, -1)
            borde = cv2.GaussianBlur(m, (0, 0), 1.2) - cv2.GaussianBlur(cv2.erode(m, np.ones((5, 5))), (0, 0), 1.2)
            m = cv2.GaussianBlur(m, (0, 0), 1.2)[..., None]
            zona = fr[Y0:Y1, X0:X1]
            vidrio = cv2.GaussianBlur(zona, (0, 0), 24) * b.get("oscuro", 0.62)
            mezcla = zona * (1 - m * a) + vidrio * m * a
            mezcla += (255 - mezcla) * (np.clip(borde, 0, 1)[..., None] * 0.35 * a)
            fr[Y0:Y1, X0:X1] = mezcla


def dibujar_textos(fr, t, bloques):
    for b in bloques:
        hasta = b.get("hasta", 1e9)
        if t < b["t"] - 0.01 or t >= hasta:
            continue
        if b.get("fondo"):
            dibujar_fondo(fr, t, b, hasta)
        for s in b["_segs"]:                               # cada palabra puede traer su propia "anim"
            dibujar_seg(fr, t, s, s.get("anim") or b.get("anim"), hasta)


# ---------- imagen ----------

def leer_plano(crudo, p, fps):
    """Cuadros del plano ya recortados a la franja vertical (alto completo, ancho 9:16)."""
    info = sonda(crudo)
    cw, ch = info["w"], info["h"]
    fw = cw if p.get("marco") else min(int(round(ch * 9 / 16 / 2) * 2), cw)
    cx = int(np.clip(p.get("x", 0.5) * cw - fw / 2, 0, cw - fw))
    filtro = f"crop={fw}:{ch}:{cx}:0" if fw < cw else "null"   # crudo vertical u horizontal en marco: entero
    if p.get("filtro"):
        filtro = p["filtro"] + "," + filtro
    if abs(info["fps"] - fps) > 0.01:          # material de otra cámara (celular): llevarlo a los fps del lote
        filtro += f",fps={fps:.6f}"
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


def encuadrar(fr, z, ay, ax=0.5):
    """Zoom z (>=1) dentro de la franja vertical, anclado en (ax, ay) (fracción del cuadro), a 1080x1920."""
    h, w = fr.shape[:2]
    cw, ch = w / z, h / z
    x0 = np.clip(ax * w - cw / 2, 0, w - cw)
    y0 = np.clip(ay * h - ch / 2, 0, h - ch)
    m = np.array([[W / cw, 0, -x0 * W / cw], [0, H / ch, -y0 * H / ch]], np.float32)
    return cv2.warpAffine(fr, m, (W, H), flags=cv2.INTER_AREA if z < 1.6 else cv2.INTER_CUBIC)


def enmarcar(fr, z, ancho=1000, cy=960, ax=0.5, ay=0.5):
    """Video horizontal (p. ej. de celular) como recuadro centrado sobre el mismo video ampliado y desenfocado."""
    h, w = fr.shape[:2]
    peq = cv2.resize(fr, (w // 4, h // 4), interpolation=cv2.INTER_AREA)
    sw = int(peq.shape[0] * 9 / 16)                     # recorte 9:16 del centro para llenar la pantalla
    peq = peq[:, (peq.shape[1] - sw) // 2:(peq.shape[1] + sw) // 2]
    fondo = cv2.resize(peq, (W, H), interpolation=cv2.INTER_LINEAR).astype(np.float32)
    fondo = cv2.GaussianBlur(fondo, (0, 0), 18) * 0.55
    cw, ch = w / z, h / z                      # zoom dentro del recuadro, anclado en (ax, ay)
    x0, y0 = np.clip(ax * w - cw / 2, 0, w - cw), np.clip(ay * h - ch / 2, 0, h - ch)
    alto = int(round(ancho * h / w))
    m = np.array([[ancho / cw, 0, -x0 * ancho / cw], [0, alto / ch, -y0 * alto / ch]], np.float32)
    cuadro = cv2.warpAffine(fr, m, (ancho, alto), flags=cv2.INTER_CUBIC).astype(np.float32)
    cuadro = cv2.filter2D(cuadro, -1, np.array([[0, -0.25, 0], [-0.25, 2, -0.25], [0, -0.25, 0]], np.float32))
    x, y = (W - ancho) // 2, int(cy - alto / 2)
    sombra = np.zeros((H, W), np.float32)
    sombra[y + 12:y + alto + 12, x:x + ancho] = 1
    sombra = cv2.GaussianBlur(sombra, (0, 0), 22)[..., None]
    fondo = fondo * (1 - 0.6 * sombra)
    fondo[y:y + alto, x:x + ancho] = cuadro
    return fondo


@lru_cache(None)
def sonda(crudo):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "stream=width,height,r_frame_rate:stream_side_data=rotation", "-of", "json", str(crudo)],
                         capture_output=True, text=True, check=True).stdout
    s = json.loads(out)["streams"][0]
    a, b = s["r_frame_rate"].split("/")
    w, h = s["width"], s["height"]
    rot = next((abs(int(d.get("rotation", 0))) for d in s.get("side_data_list", [])), 0)
    if rot in (90, 270):          # cámara girada (Sony en vertical): ffmpeg la endereza al decodificar
        w, h = h, w
    return {"w": w, "h": h, "fps": int(a) / int(b), "fps_txt": s["r_frame_rate"]}


def graduar(img, k=1.0, rng=np.random.default_rng(3)):
    """Color "cine" (pedido de la clienta: más cinematográfico y difuminado): negros levantados, contraste suave,
    algo cálido y menos saturado, brillo difuso en las luces (tipo filtro Pro-Mist) y un grano fino. k = intensidad."""
    x = img / 255.0
    x = x * (1 - 0.06 * k) + 0.035 * k                                   # negros levantados, blancos sin quemar
    x = 0.5 + (x - 0.5) * (1 - 0.08 * k)                                 # contraste más suave
    gris = x.mean(2, keepdims=True)
    x = gris + (x - gris) * (1 - 0.12 * k)                               # un poco menos saturado
    x = x * np.array([1 - 0.035 * k, 1.0, 1 + 0.03 * k], np.float32)     # BGR: más cálido
    luz = np.clip((x.mean(2, keepdims=True) - 0.62) / 0.38, 0, 1) * x
    x = x + cv2.GaussianBlur(luz, (0, 0), 28) * 0.32 * k                 # difusión en las luces
    x = x + rng.normal(0, 0.012 * k, (img.shape[0] // 2, img.shape[1] // 2, 1)).astype(np.float32).repeat(2, 0).repeat(2, 1)
    return np.clip(x, 0, 1) * 255


def estabilizar(reel, crudo, p):
    """Estabilización suave con vid.stab (2 pasadas) del tramo del plano + 1 s a cada lado (pedido de Sebas, BOF-2:
    tomas a mano movidas). "estabilizar": N = cuadros de suavizado (15 suave … 30 fuerte). optzoom=1 aplica el zoom
    mínimo fijo para que no aparezcan bordes. Se guarda en trabajo/estab/ y se reutiliza."""
    suave = int(p["estabilizar"]) if p["estabilizar"] is not True else 20
    if p.get("estab_rango"):                          # planos seguidos del mismo clip: misma estabilización
        ini, fin = p["estab_rango"]
        largo = fin - ini
    else:
        ini = max(p["desde"] - 1.0, 0.0)
        largo = p["dur"] + (p["desde"] - ini) + 1.0
    carpeta = Path(reel) / "trabajo" / "estab"
    carpeta.mkdir(exist_ok=True)
    nombre = f'{p["clip"]}_{ini:.2f}_{largo:.2f}_{suave}'
    destino, trf = carpeta / f"{nombre}.MP4", carpeta / f"{nombre}.trf"
    if not destino.exists():
        base = ["ffmpeg", "-nostdin", "-v", "error", "-y", "-ss", f"{ini:.3f}", "-t", f"{largo:.3f}", "-i", str(crudo)]
        escala = "scale=1440:-2:flags=lanczos"         # 1440 de ancho: sobra para entregar en 1080 y es 2x más rápido
        subprocess.run(base + ["-vf", f"{escala},vidstabdetect=shakiness=6:accuracy=15:result={trf}",
                               "-f", "null", "-"], check=True)
        subprocess.run(base + ["-vf", f"{escala},vidstabtransform=input={trf}:smoothing={suave}:optzoom=1:"
                               f"interpol=bicubic,unsharp=5:5:0.4", "-an", "-c:v", "libx264", "-preset", "fast",
                               "-crf", "14", "-pix_fmt", "yuv420p", str(destino)], check=True)
    return destino, dict(p, desde=round(p["desde"] - ini, 3))


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
        if p.get("estabilizar"):
            crudo, p = estabilizar(reel, crudo, p)
        for k, fr in enumerate(leer_plano(crudo, p, fps)):
            t = tiempos[k]
            if limite and t >= limite:
                return
            if solo is not None and not any(abs(t - s) < 0.5 / fps for s in solo):
                continue
            u = k / max(n - 1, 1)
            vertical = sonda(crudo)["w"] < sonda(crudo)["h"]
            if p.get("marco"):
                img = enmarcar(fr, z0 + (z1 - z0) * suave(u), p.get("ancho_marco", 1000), p.get("y_marco", 960),
                               p.get("x", 0.5), p.get("y", 0.5))
            else:
                img = encuadrar(fr, z0 + (z1 - z0) * suave(u), p.get("y", 0.5),
                                p.get("x", 0.5) if vertical else 0.5).astype(np.float32)
            if g.get("grado") == "cine":
                img = graduar(img, g.get("grado_k", 1.0)).astype(np.float32)
            if p.get("desenfoque"):
                a, b = p["desenfoque"]
                r = suave((k / fps - a) / (b - a))
                sig = p.get("sigma", 16) * r
                if sig > 0.3:
                    img = cv2.GaussianBlur(img, (0, 0), sig)
                img *= 1 - p.get("oscurecer", 0) * r          # fondo más oscuro para que el blanco resalte
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

VOZ_LUFS = -16          # nivel de cada tramo de voz antes de la mezcla
BAJO_VOZ_DB = 18        # cuánto baja la música mientras alguien habla (pedido de Sebas: la voz manda)


def retrasar(seg):
    """Mueve el audio a `seg` segundos con silencio REAL delante. Solo adelay deja un hueco de tiempo que amix
    borra después (la voz de MOF-3 sonaba en el segundo 0, encima del gancho, y faltaba en el clip 8)."""
    return f"aresample=48000,adelay={int(round(seg * 1000))}:all=1,aresample=async=1:first_pts=0"


def lufs(cmd_in, filtro):
    """Sonoridad integrada de una entrada de ffmpeg pasada por `filtro`."""
    e = subprocess.run(["ffmpeg", "-nostdin", "-hide_banner", *cmd_in, "-af", f"{filtro},loudnorm=print_format=json",
                        "-f", "null", "-"], capture_output=True, text=True).stderr
    return float(json.loads(e[e.rindex("{"):e.rindex("}") + 1])["input_i"])


def mezclar_audio(reel, g, dur, destino):
    """Voz (de los crudos) a nivel fijo, música que baja BAJO_VOZ_DB mientras hay voz, efectos -> -14 LUFS."""
    A = g.get("audio", {})
    entradas, cadenas, voces, ventanas = [], [], [], []
    for j, v in enumerate(A.get("voz", [])):
        crudo = str(Path(reel) / "crudos" / f'{v["clip"]}.MP4')
        entradas += ["-i", crudo]
        largo = v["hasta"] - v["desde"]
        limpia = (f'aformat=channel_layouts=mono,highpass=f=80,afftdn=nf=-30,'
                  f'acompressor=threshold=-24dB:ratio=3:attack=8:release=120')
        nivel = lufs(["-ss", str(v["desde"]), "-t", str(largo), "-i", crudo], limpia)
        gan = VOZ_LUFS - nivel + v.get("db", 0)
        cadenas.append(
            f'[{len(entradas)//2 - 1}:a]atrim={v["desde"]}:{v["hasta"]},asetpts=PTS-STARTPTS,{limpia},'
            f'volume={gan:.2f}dB,alimiter=limit=0.9:level=disabled,'
            f'afade=t=in:d=0.04,afade=t=out:st={max(largo - 0.06, 0)}:d=0.06,'
            f'{retrasar(v["en"])},apad=whole_dur={dur}[v{j}]')
        voces.append(f"[v{j}]")
        ventanas.append((v["en"], v["en"] + largo))
    pistas = []
    if voces:
        cadenas.append(f'{"".join(voces)}amix=inputs={len(voces)}:normalize=0,atrim=0:{dur}[voz]')
    M = A.get("musica")
    if M:
        musica = str(Path(reel) / "trabajo" / M["archivo"])
        entradas += ["-i", musica]
        idx = len(entradas) // 2 - 1
        eq = M.get("eq", "anull")
        nivel = lufs(["-ss", str(M.get("desde", 0)), "-t", str(dur), "-i", musica], eq)
        base = VOZ_LUFS - nivel + M.get("db_libre", 0)      # sin voz: la música suena al nivel de la voz
        env = "0"
        for a, b in ventanas:                                # rampa de 0,25 s al entrar y 0,35 s al salir
            e = f"clip((t-({a:.3f}-0.25))/0.25,0,1)*clip((({b:.3f}+0.35)-t)/0.35,0,1)"
            env = f"max({env},{e})"
        baja = M.get("bajo_voz", BAJO_VOZ_DB) if M.get("duck", True) else 0
        db_expr = f"-{baja}*{env}"
        for a, b, d in M.get("bajar", []):                  # tramos con la música más baja (p. ej. aplausos del gancho)
            db_expr += f"-{abs(d)}*clip((t-({a:.3f}-0.2))/0.2,0,1)*clip((({b:.3f}+0.4)-t)/0.4,0,1)"
        cadenas.append(f'[{idx}:a]atrim={M.get("desde", 0)}:{M.get("desde", 0) + dur},asetpts=PTS-STARTPTS,'
                       f'aformat=channel_layouts=stereo,{eq},volume={base:.2f}dB,'
                       f"volume=eval=frame:volume='pow(10,({db_expr})/20)',"
                       f'afade=t=out:st={max(dur - M.get("fade", 0.8), 0)}:d={M.get("fade", 0.8)}[mus]')
        pistas.append("[mus]")
    if voces:
        pistas.append("[voz]")
    for j, s in enumerate(A.get("sfx", [])):
        entradas += ["-i", str(Path(reel) / "trabajo" / s["archivo"])]
        idx = len(entradas) // 2 - 1
        cadenas.append(f'[{idx}:a]aformat=channel_layouts=stereo,volume={s.get("db", -4.4)}dB,'
                       f'{retrasar(s["en"])}[s{j}]')
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
    # sonoridad: ganancia fija hasta -14 LUFS y limitador con margen para el AAC (pico final <= -1 dBTP)
    def medir(f):
        e = subprocess.run(["ffmpeg", "-nostdin", "-hide_banner", "-i", f, "-af",
                            "loudnorm=print_format=json", "-f", "null", "-"], capture_output=True, text=True).stderr
        j = json.loads(e[e.rindex("{"):e.rindex("}") + 1])
        return float(j["input_i"]), float(j["input_tp"])
    ganancia, limite = -14 - medir(crudo)[0], 0.7
    for _ in range(6):
        subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", crudo, "-af",
                        f"volume={ganancia:.2f}dB,alimiter=limit={limite:.3f}:attack=1:release=60:level=disabled",
                        "-ar", "48000", str(destino)], check=True)
        i, tp = medir(str(destino))
        ok_i, ok_tp = abs(i + 14) < 0.3, tp <= -2.5        # margen: el AAC sube el pico ~1 dB (BOF-2 salió a -0,6)
        if ok_i and ok_tp:
            break
        if not ok_tp:
            limite *= 10 ** ((-2.5 - tp - 0.3) / 20)
        ganancia += -14 - i


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
    # fps del lote = los que más se repiten entre los planos (no los del primero: un clip de celular trae 600/1)
    from collections import Counter
    info = Counter((sonda(Path(a.reel) / "crudos" / f'{p["clip"]}.MP4')["fps_txt"],
                    sonda(Path(a.reel) / "crudos" / f'{p["clip"]}.MP4')["fps"]) for p in g["planos"]).most_common(1)[0][0]
    info = {"fps_txt": info[0], "fps": info[1]}
    if a.storyboard:
        storyboard(a.reel, g, info["fps"])
    else:
        render(a.reel, g, info["fps"], info["fps_txt"], a.prueba)


if __name__ == "__main__":
    main()
