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


ANCHO_SEGURO = 820  # zona segura de Instagram: x de ~110 a ~950 px, con algo de aire


def tamano_que_cabe(texto, fuente, px):
    """Baja el tamaño de letra hasta que la línea quepa en la zona segura (ASS no corta líneas con WrapStyle 2)."""
    while px > 40 and ImageFont.truetype(str(fuente), px).getlength(texto) > ANCHO_SEGURO:
        px -= 2
    return px


def escribir_ass(bloques, w, marca, destino, y, fin_video, marca_dir, l1_px=74, l2_px=118):
    fam = marca["fuentes"]["subtitulos"]["familia"]
    blanco = ass_color(marca["colores"]["texto"])
    acento = ass_color(marca["colores"]["acento"])
    f_l1 = marca_dir / marca["fuentes"]["subtitulos"]["archivo"]
    f_l2 = marca_dir / marca["fuentes"]["palabras_clave"]["archivo"]
    cab = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: L1,{fam},{l1_px},{blanco},{blanco},&H00000000,&H78000000,0,0,0,0,100,100,0,0,1,0,4,2,60,60,0,1
Style: L2,{fam},{l2_px},{acento},{acento},&H00000000,&H78000000,1,0,0,0,100,100,0,0,1,0,4,8,60,60,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    pop = r"{\fad(70,50)\fscx88\fscy88\t(0,140,\fscx100\fscy100)}"
    lineas = []
    for k, b in enumerate(bloques):
        siguiente = bloques[k + 1]["l1"][0] if k + 1 < len(bloques) else None
        fin = w[siguiente]["inicio"] - 0.02 if siguiente is not None else fin_video
        a, _, texto = b["l1"]
        fs1 = tamano_que_cabe(texto, f_l1, l1_px)
        lineas.append(f"Dialogue: 0,{ass_tiempo(w[a]['inicio'])},{ass_tiempo(fin)},L1,,0,0,0,,"
                      f"{{\\pos(540,{y})\\fs{fs1}}}{pop}{texto}")
        if "l2" in b:
            a2, _, texto2 = b["l2"]
            fs2 = tamano_que_cabe(texto2, f_l2, l2_px)
            lineas.append(f"Dialogue: 0,{ass_tiempo(w[a2]['inicio'])},{ass_tiempo(fin)},L2,,0,0,0,,"
                          f"{{\\pos(540,{y + 4})\\fs{fs2}}}{pop}{texto2}")
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
    ap.add_argument("--y", type=int, default=1330, help="línea entre L1 y L2 (banda segura 1210-1550)")
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
    escribir_ass(conf["bloques"], w, marca, ass, a.y, dur, marca_dir)

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
        entradas += ["-itsoffset", f"{t0:.3f}", "-i", str(Path(a.reel) / b["animacion"])]
        vol = b.get("volumen", 0.6)
        esc = b.get("escala", 1.0)
        filtro = (f"[0:v]subtitles={ass}:fontsdir={marca_dir / 'fuentes'}[s];"
                  f"[1:v]format=rgba,scale=iw*{esc}:-1[b];[s][b]overlay=(W-w)/2:{b.get('mover_y', 0)}:eof_action=pass[v];"
                  f"[1:a]volume={vol}[ba];[0:a][ba]amix=inputs=2:duration=first:normalize=0[a]")
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
