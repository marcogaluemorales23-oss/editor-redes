#!/usr/bin/env python3
"""Subtítulos en dos líneas (frase en blanco + frase clave en color) y badge final, quemados sobre la base.

Uso: python3 nucleo/subtitulos.py <reel> <marca> [--tiempos corte_check.json] [--y 1150]
Lee <reel>/trabajo/subtitulos.json:
    {"bloques": [{"l1": [desde, hasta, "texto"], "l2": [desde, hasta, "texto"]}, ...],
     "badge": {"desde_palabra": 74, "handle": "...", "logo": "ruta"}}
Los índices son de palabra en la transcripción del corte (tiempos ya en la línea de tiempo del corte).
El texto de cada línea lo escribe Claude ya corregido (tildes, nombres propios).
"""
import argparse
import json
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

RAIZ = Path(__file__).resolve().parent.parent


def ass_tiempo(t):
    h, r = divmod(max(t, 0), 3600)
    m, s = divmod(r, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def ass_color(hex6):
    r, g, b = hex6[1:3], hex6[3:5], hex6[5:7]
    return f"&H00{b}{g}{r}".upper()


# Subtítulos centrados en el cuadro (x=540), como pidió Sebas. Abajo la zona segura termina en x≈850 (likes,
# comentarios, compartir): se acepta pasarse un poco; si la línea amarilla se pasa mucho, se achica solo ella.
# Arriba (llamada a la acción) no hay iconos y cabe más ancho.
ZONA_ABAJO = {"x": 540, "ancho": 780, "ancho_l2": 720}
ZONA_ARRIBA = {"x": 540, "ancho": 860, "ancho_l2": 860}
BOTON_X = 480  # el botón sí va corrido a la izquierda para no meterse bajo los iconos

# Medidas de Sebastián en Premiere (secuencia 1440x2560), pasadas a 1080x1920 (x 0,75). Se pueden cambiar
# por marca en marca.json -> "subtitulos".
ESTILO = {
    "l1_px": 83,             # Regular 111
    "l2_px": 106,            # Bold 142
    "tracking": -0.049,      # tracking -49 (milésimas de em)
    "interlineado": 87,      # de línea base a línea base
    # Sombra: en su edición es un resplandor oscuro muy difuso que casi no se ve, sin contorno pegado a la letra.
    "sombra_opacidad": 0.45,
    "sombra_distancia": 2.2,  # 3 a 135° -> abajo a la derecha
    "sombra_tamano": 0,
    "sombra_desenfoque": 22,
    # Animación: entra deslizando con desenfoque de movimiento y sale borrosa.
    "entrada_ms": 180,
    "salida_ms": 140,
    "deslizar_px": 60,
}


def metricas(fuente):
    """(alto de celda ASS por px de em, descendente por px de em). En ASS el tamaño es ascendente+descendente,
    no el em: con Playfair, 'Fontsize 83' en ASS da una letra de 61 px. Hay que convertir."""
    f = ImageFont.truetype(str(fuente), 1000)
    asc, desc = f.getmetrics()
    return (asc + desc) / 1000, desc / 1000


def ancho(texto, fuente, px, tracking):
    return ImageFont.truetype(str(fuente), round(px)).getlength(texto) + tracking * px * (len(texto) - 1)


def tamano_que_cabe(texto, fuente, px, tracking, limite):
    """Baja el tamaño de letra hasta que la línea quepa en la zona segura (ASS no corta líneas con WrapStyle 2)."""
    while px > 40 and ancho(texto, fuente, px, tracking) > limite:
        px -= 1
    return px


def linea(t0, t1, estilo, x, y, px, celda, est, texto, sombra, alinear=2):
    fs = round(px * celda, 1)
    fsp = round(est["tracking"] * px, 2)
    dur = round((t1 - t0) * 1000)
    e, sal, dx = est["entrada_ms"], min(est["salida_ms"], dur // 3), est["deslizar_px"]
    if sombra:
        d = est["sombra_distancia"]
        alfa = f"&H{round(255 * (1 - est['sombra_opacidad'])):02X}&"
        x, y = x + d, y + d
        estilo_txt = (f"\\1c&H000000&\\3c&H000000&\\1a{alfa}\\3a{alfa}\\bord{est['sombra_tamano']}"
                      f"\\blur{est['sombra_desenfoque']}")
        anim = f"\\fad({e},{sal})"
    else:
        estilo_txt = "\\bord0\\shad0\\blur14"
        anim = f"\\fad({e},{sal})\\t(0,{e},\\blur0)\\t({dur - sal},{dur},\\blur10)"
    return (f"Dialogue: {0 if sombra else 1},{ass_tiempo(t0)},{ass_tiempo(t1)},{estilo},,0,0,0,,"
            f"{{\\an{alinear}\\move({x - dx:.1f},{y:.1f},{x:.1f},{y:.1f},0,{e})\\fs{fs}\\fsp{fsp}{estilo_txt}{anim}}}{texto}")


def caja_redonda(x0, y0, w, h, r):
    """Rectángulo de esquinas redondeadas en dibujo ASS (\\p1), con origen arriba a la izquierda."""
    k = 0.55 * r
    return (f"m {r} 0 l {w - r} 0 b {w - r + k} 0 {w} {r - k} {w} {r} l {w} {h - r} "
            f"b {w} {h - r + k} {w - r + k} {h} {w - r} {h} l {r} {h} b {r - k} {h} 0 {h - r + k} 0 {h - r} "
            f"l 0 {r} b 0 {r - k} {r - k} 0 {r} 0")


def fondo_claro(base, t, x0, y0, w, h):
    """¿Lo que hay detrás de la frase clave es claro o muy cargado? (luminancia media o contraste alto)."""
    import numpy as np
    if base is None:
        return False
    x0, y0, w, h = (max(0, int(v)) for v in (x0, y0, w, h))
    crudo = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", str(base), "-frames:v", "1", "-vf",
                            f"crop={min(w, 1080 - x0)}:{min(h, 1920 - y0)}:{x0}:{y0},format=gray", "-f", "rawvideo",
                            "-"], capture_output=True).stdout
    if not crudo:
        return False
    px = np.frombuffer(crudo, np.uint8) / 255.0
    return px.mean() > 0.55 or px.std() > 0.24


def bloque_compuesto(b, w, fin, base, est, f_l1, f_l2, celda1, desc1, celda2, desc2, video=None):
    """Modo "compuesto" (Sebas, prueba-01). La frase clave manda: ENORME, en UNA sola línea (si no cabe se achica,
    nunca se parte). El apoyo (máx. 3 palabras) se acomoda ALREDEDOR de la clave, como un título de portada:
      - en línea, a la izquierda de la clave, si los dos caben juntos ("hoy tengo 23 SEGUIDORES");
      - si no, arriba y pegado al borde izquierdo de la clave (o centrado si es más ancho que ella).
    Si detrás de la clave el fondo es claro o cargado, la clave va en una caja negra (letra amarilla), como el
    "seguidores" resaltado de los videos de Sebas. `base` = línea base de la clave."""
    out = []
    claves = b.get("l2", [])
    if claves and not isinstance(claves[0], list):
        claves = [claves]
    a1, _, texto1 = b["l1"]
    t1 = w[a1]["inicio"]
    if not claves:
        px = tamano_que_cabe(texto1, f_l1, est["solo_px"], est["tracking"], est["ancho_apoyo"])
        for sombra in (True, False):
            out.append(linea(t1, fin, "L1", 540, base - est["solo_sube"] + desc1 * px, px, celda1, est, texto1, sombra))
        return out
    for j, (a2, _, texto2) in enumerate(claves):
        t2 = w[a2]["inicio"]
        fin2 = w[claves[j + 1][0]]["inicio"] - 0.02 if j + 1 < len(claves) else fin
        px2 = tamano_que_cabe(texto2, f_l2, est["l2_px"], est["tracking"], est["ancho_clave"])
        ancho2 = ancho(texto2, f_l2, px2, est["tracking"])
        px1 = est["l1_px"]
        ancho1 = ancho(texto1, f_l1, px1, est["tracking"])
        hueco = px1 * 0.35
        en_linea = j == 0 and ancho1 + hueco + ancho2 <= est["ancho_total"]
        if en_linea:
            x0 = 540 - (ancho1 + hueco + ancho2) / 2
            x_clave = x0 + ancho1 + hueco
        else:
            x0 = x_clave = 540 - ancho2 / 2
        # Caja negra detrás de la clave si el fondo no deja leer (o si el bloque la pide con "caja").
        alto_mayus = px2 * 0.73
        caja = b.get("caja")
        if caja is None and est.get("caja_auto"):
            caja = fondo_claro(video, t2 + 0.2, x_clave - 20, base - alto_mayus - 20, ancho2 + 40, alto_mayus + 40)
        if caja:
            pad_x, pad_y = px2 * 0.14, px2 * 0.12
            bw, bh = ancho2 + 2 * pad_x, alto_mayus + 2 * pad_y
            bx, by = x_clave - pad_x, base - alto_mayus - pad_y
            dur = round((fin2 - t2) * 1000)
            out.append(f"Dialogue: 0,{ass_tiempo(t2)},{ass_tiempo(fin2)},L2,,0,0,0,,"
                       f"{{\\an7\\pos({bx:.1f},{by:.1f})\\p1\\1c&H000000&\\1a&H1A&\\bord0\\shad0"
                       f"\\fad({est['entrada_ms']},{min(est['salida_ms'], dur // 3)})}}"
                       f"{caja_redonda(0, 0, round(bw), round(bh), round(bh * 0.22))}{{\\p0}}")
        for sombra in ((False,) if caja else (True, False)):  # con caja la sombra sobra
            out.append(linea(t2, fin2, "L2", x_clave, base + desc2 * px2, px2, celda2, est, texto2, sombra, alinear=1))
        if j == 0:
            if en_linea:
                # Apoyo centrado en la altura de las mayúsculas de la clave.
                y1 = base - (alto_mayus - px1 * 0.73) / 2 + desc1 * px1
                for sombra in (True, False):
                    out.append(linea(t1, fin, "L1", x0, y1, px1, celda1, est, texto1, sombra, alinear=1))
            else:
                y1 = base - alto_mayus - est["aire_apoyo"] - (px2 * 0.12 if caja else 0) + desc1 * px1
                if ancho1 <= ancho2:
                    for sombra in (True, False):
                        out.append(linea(t1, fin, "L1", x_clave, y1, px1, celda1, est, texto1, sombra, alinear=1))
                else:
                    px1 = tamano_que_cabe(texto1, f_l1, px1, est["tracking"], est["ancho_apoyo"])
                    for sombra in (True, False):
                        out.append(linea(t1, fin, "L1", 540, y1, px1, celda1, est, texto1, sombra))
    return out


def escribir_ass(bloques, w, marca, destino, y, fin_video, marca_dir, y_arriba=None, desde_arriba=None,
                 y_por_tramo=(), encuadre=(), video=None):
    """y = línea base de la frase blanca. Los bloques desde la palabra `desde_arriba` (la llamada a la acción)
    suben a y_arriba para dejar la banda de abajo libre para el botón.
    "l2" puede ser una lista de frases clave: la blanca se queda fija y la amarilla va cambiando (listas como
    "para cada duda / cada problema / cada cierre")."""
    est = {**ESTILO, **marca.get("subtitulos", {})}
    fam = marca["fuentes"]["subtitulos"]["familia"]
    clave = marca["fuentes"]["palabras_clave"]
    fam2 = clave.get("familia", fam)
    # Peso e itálica de la frase clave por marca (Sebas: Inter Black Italic). Con "peso" el estilo L2 usa \\b<peso>.
    negrita2 = clave.get("peso", 1)
    italica2 = 1 if clave.get("italica") else 0
    negrita1 = marca["fuentes"]["subtitulos"].get("peso", 0)  # Sebas: apoyo en Inter Bold (700)
    blanco = ass_color(marca["colores"]["texto"])
    acento = ass_color(marca["colores"]["acento"])
    f_l1 = marca_dir / marca["fuentes"]["subtitulos"]["archivo"]
    f_l2 = marca_dir / marca["fuentes"]["palabras_clave"]["archivo"]
    celda1, desc1 = metricas(f_l1)
    celda2, desc2 = metricas(f_l2)
    cab = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: L1,{fam},80,{blanco},{blanco},&H00000000,&H00000000,{negrita1},0,0,0,100,100,0,0,1,0,0,2,0,0,0,1
Style: L2,{fam2},100,{acento},{acento},&H00000000,&H00000000,{negrita2},{italica2},0,0,100,100,0,0,1,0,0,2,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lineas = []
    for k, b in enumerate(bloques):
        siguiente = bloques[k + 1]["l1"][0] if k + 1 < len(bloques) else None
        fin = w[siguiente]["inicio"] - 0.02 if siguiente is not None else fin_video
        if est.get("modo") == "compuesto":
            t_b = w[b["l1"][0]]["inicio"]
            tramo = next((tr for tr in y_por_tramo if tr["desde"] - 0.05 <= t_b < tr["hasta"]), None)
            y_b = tramo["y"] if tramo and "y" in tramo else y
            enc = next((tr for tr in encuadre if tr["desde"] - 0.05 <= t_b < tr["hasta"]), None)
            if enc and not tramo:
                # Bajo la barbilla: apoyo arriba + clave. Nunca más arriba que la línea fija `y`.
                y_b = min(est.get("y_max", 1585), max(y, enc["barbilla"] + est["bajo_barbilla"]))
            nuevas = bloque_compuesto(b, w, fin, y_b, est, f_l1, f_l2, celda1, desc1, celda2, desc2, video)
            if tramo and tramo.get("colores"):
                # Sobre fondo claro (pantallas crema): apoyo oscuro y clave en el acento del tramo, sin sombra.
                l1c, l2c = (ass_color(x) + "&" for x in tramo["colores"])
                nuevas = [x.replace(",L1,,", ",L1,,").replace("{\\an", "{\\1c" + l1c + "\\an", 1)
                          if ",L1,," in x else x.replace("{\\an", "{\\1c" + l2c + "\\an", 1) if ",L2,," in x and "\\p1" not in x else x
                          for x in nuevas if not (x.startswith("Dialogue: 0,") and "\\blur" in x and "\\1a" in x)]
            lineas += nuevas
            continue
        arriba = desde_arriba is not None and b["l1"][0] >= desde_arriba
        base, zona = (y_arriba, ZONA_ARRIBA) if arriba else (y, {**ZONA_ABAJO, **marca.get("zona_abajo", {})})
        # Formatos con pantalla partida: en esos tramos el subtítulo va en la línea que divide la pantalla.
        t_bloque = w[b["l1"][0]]["inicio"]
        tramo = next((tr for tr in y_por_tramo if tr["desde"] - 0.05 <= t_bloque < tr["hasta"]), None)
        if tramo and not arriba:
            base = tramo["y"]
        a, _, texto = b["l1"]
        px1 = tamano_que_cabe(texto, f_l1, est["l1_px"], est["tracking"], zona["ancho"])
        y1 = base + desc1 * px1  # \an2 ancla el borde de abajo de la celda: línea base + descendente
        for sombra in (True, False):
            lineas.append(linea(w[a]["inicio"], fin, "L1", zona["x"], y1, px1, celda1, est, texto, sombra))
        claves = b.get("l2", [])
        if claves and not isinstance(claves[0], list):
            claves = [claves]
        for j, (a2, _, texto2) in enumerate(claves):
            fin2 = w[claves[j + 1][0]]["inicio"] - 0.02 if j + 1 < len(claves) else fin
            px2 = tamano_que_cabe(texto2, f_l2, est["l2_px"], est["tracking"], zona["ancho_l2"])
            y2 = base + est["interlineado"] + desc2 * px2
            for sombra in (True, False):
                lineas.append(linea(w[a2]["inicio"], fin2, "L2", zona["x"], y2, px2, celda2, est, texto2, sombra))
    destino.write_text(cab + "\n".join(lineas) + "\n", encoding="utf-8")


def emblema(marca):
    """Recorta el símbolo del logo: el primer bloque de columnas con tinta, antes del primer hueco vacío."""
    alfa = marca.getchannel("A").point(lambda v: 255 if v > 40 else 0)
    caja = alfa.getbbox()
    ancho, alto = marca.size
    columnas = [alfa.crop((x, 0, x + 1, alto)).getbbox() is not None for x in range(caja[0], caja[2])]
    fin = caja[0] + next((i for i, c in enumerate(columnas) if not c), len(columnas))
    simbolo = alfa.crop((caja[0], 0, fin, alto)).getbbox()
    return marca.crop((caja[0], simbolo[1], fin, simbolo[3]))


def crear_badge(logo, handle, destino):
    """Badge tipo Instagram: logo en círculo, usuario y botón Seguir."""
    W, H = 640, 120
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, W - 1, H - 1), radius=H // 2, fill=(255, 255, 255, 240))
    marca = Image.open(logo).convert("RGBA")
    icono = emblema(marca)
    icono.thumbnail((80, 80))
    circulo = Image.new("RGBA", (96, 96), (0, 0, 0, 0))
    ImageDraw.Draw(circulo).ellipse((0, 0, 95, 95), fill=(255, 255, 255, 255), outline=(210, 205, 195, 255), width=3)
    circulo.alpha_composite(icono, ((96 - icono.width) // 2, (96 - icono.height) // 2))
    img.alpha_composite(circulo, (12, 12))
    inter = RAIZ / "marcas" / "sebastian" / "fuentes"
    f_user = ImageFont.truetype(str(inter / "Inter-SemiBold.ttf"), 34)
    f_btn = ImageFont.truetype(str(inter / "Inter-SemiBold.ttf"), 30)
    d.text((124, H // 2), handle, font=f_user, fill=(20, 20, 20, 255), anchor="lm")
    # Sin check de verificado: ponerlo en una cuenta que no lo tiene sería engañoso.
    btn_x = 124 + int(d.textlength(handle, font=f_user)) + 24
    d.rounded_rectangle((btn_x, 26, W - 18, H - 26), radius=16, fill=(0, 149, 246, 255))
    d.text(((btn_x + W - 18) // 2, H // 2), "Seguir", font=f_btn, fill="white", anchor="mm")
    img.save(destino)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("reel")
    ap.add_argument("marca")
    ap.add_argument("--tiempos", default="corte_check.json")
    ap.add_argument("--y", type=int, default=1243, help="línea base de la frase blanca (banda 1210-1550)")
    ap.add_argument("--y-arriba", type=int, default=345, help="línea base en la llamada a la acción")
    ap.add_argument("--base", default="base.mp4", help="base.mp4 o base_broll.mp4")
    a = ap.parse_args()
    trabajo = Path(a.reel) / "trabajo"
    marca_dir = RAIZ / "marcas" / a.marca
    marca = json.loads((marca_dir / "marca.json").read_text())
    conf = json.loads((trabajo / "subtitulos.json").read_text())
    w = json.loads((trabajo / a.tiempos).read_text())["palabras"]
    base = trabajo / a.base
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                str(base)], capture_output=True, text=True, check=True).stdout)
    ass = trabajo / "subtitulos.ass"
    arch_enc = trabajo / "encuadre_tramos.json"
    encuadre = json.loads(arch_enc.read_text()) if arch_enc.exists() else []
    escribir_ass(conf["bloques"], w, marca, ass, a.y, dur, marca_dir, a.y_arriba,
                 conf.get("arriba_desde_palabra", conf.get("badge", {}).get("desde_palabra")),
                 conf.get("y_por_tramo", []), encuadre, base)

    salida = Path(a.reel) / "salida"
    salida.mkdir(exist_ok=True)
    final = salida / "final.mp4"
    filtro = f"[0:v]subtitles={ass}:fontsdir={marca_dir / 'fuentes'}[v]"
    entradas = ["-i", str(base)]
    audio = ["-map", "0:a", "-c:a", "copy"]
    if "animacion" in conf.get("badge", {}):
        # Animación con transparencia hecha por Sebas (ProRes 4444 / QuickTime Animation), con su sonido.
        b = conf["badge"]
        t0 = w[b["desde_palabra"]]["inicio"] + b.get("ajuste_s", 0)
        entradas += ["-i", str(Path(a.reel) / b["animacion"])]
        # Efectos de sonido a -4,4 dB, como los baja Sebas en Premiere.
        vol = b.get("volumen_db", -4.4)
        esc = b.get("escala", 1.0)
        ms = round(t0 * 1000)
        # El retraso se aplica a imagen (setpts) y sonido (adelay) por separado: con -itsoffset el sonido
        # del botón no llegaba a la mezcla.
        filtro = (f"[0:v]subtitles={ass}:fontsdir={marca_dir / 'fuentes'}[s];"
                  f"[1:v]format=rgba,scale=iw*{esc}:-1,setpts=PTS-STARTPTS+{t0:.3f}/TB[b];"
                  f"[s][b]overlay={BOTON_X}-w/2:{b.get('mover_y', 0)}:eof_action=pass[v];"
                  f"[1:a]aresample=48000,adelay={ms}|{ms},volume={vol}dB[ba];"
                  f"[0:a][ba]amix=inputs=2:duration=first:normalize=0[a]")
        audio = ["-map", "[a]", "-c:a", "aac", "-b:a", "192k"]
    elif "badge" in conf:
        badge = trabajo / "badge.png"
        crear_badge(RAIZ / conf["badge"]["logo"], conf["badge"]["handle"], badge)
        t0 = w[conf["badge"]["desde_palabra"]]["inicio"]
        entradas += ["-loop", "1", "-i", str(badge)]
        filtro = (f"[0:v]subtitles={ass}:fontsdir={marca_dir / 'fuentes'}[s];"
                  f"[1:v]format=rgba,fade=t=in:st={t0:.2f}:d=0.25:alpha=1[b];"
                  f"[s][b]overlay=(W-w)/2:1480:enable='gte(t,{t0:.2f})':shortest=1[v]")
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *entradas, "-filter_complex", filtro,
                    "-map", "[v]", *audio, "-c:v", "libx264", "-preset", "slow", "-crf", "18",
                    "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(final)], check=True)
    print(f"final -> {final}")


if __name__ == "__main__":
    main()
