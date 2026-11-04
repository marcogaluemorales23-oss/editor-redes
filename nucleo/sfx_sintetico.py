#!/usr/bin/env python3
"""Efectos de sonido generados (sin librerías externas: la red del servidor bloquea Pixabay).

Uso: python3 nucleo/sfx_sintetico.py <tipo> <salida.wav> [duración_s]
Tipos:
  aplausos   público aplaudiendo en un auditorio: cientos de palmadas (ráfagas de ruido de 4-14 ms filtradas
             entre 700 y 3500 Hz), paneo al azar, entra subiendo, pico a 55 % y se apaga; reverb de sala.
  brillo     destello de "coronación": campanitas en arpegio ascendente (parciales inarmónicos tipo glockenspiel)
             con cola de reverb. Para el momento de la corona o una revelación.
  murmullo   público de fondo (ruido rosa filtrado 150-900 Hz con vaivén lento), para pegar debajo de aplausos.
Salida: WAV 48 kHz estéreo, picos a -3 dBFS. El nivel final se pone en la mezcla ("sfx" de anuncio.py).
"""
import sys
import wave

import numpy as np

SR = 48000
rng = np.random.default_rng(7)


def pasabanda(x, f1, f2):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    m = np.clip((f - f1 * 0.7) / (f1 * 0.3), 0, 1) * np.clip((f2 * 1.3 - f) / (f2 * 0.3), 0, 1)
    return np.fft.irfft(X * m, len(x))


def reverb(st, seg=1.6, mezcla=0.28):
    """Cola de sala: respuesta al impulso de ruido con caída exponencial, convolución por FFT."""
    n = int(seg * SR)
    t = np.arange(n) / SR
    out = []
    for c in range(2):
        ir = rng.standard_normal(n) * np.exp(-t * 6.9 / seg)
        ir = pasabanda(ir, 300, 6000)
        ir /= np.sqrt((ir ** 2).sum())
        L = len(st) + n
        mojado = np.fft.irfft(np.fft.rfft(st[:, c], L) * np.fft.rfft(ir, L), L)[:len(st)]
        out.append(st[:, c] * (1 - mezcla) + mojado * mezcla * 3)
    return np.stack(out, 1)


def aplausos(dur):
    n = int(dur * SR)
    st = np.zeros((n, 2))
    t_pico = dur * 0.55
    env_t = lambda t: np.clip(t / (t_pico * 0.6), 0, 1) ** 1.5 * np.where(t > t_pico, np.exp(-(t - t_pico) * 1.6), 1)
    densidad = 260                                   # palmadas por segundo en el pico (un auditorio lleno)
    k = int(densidad * dur)
    tiempos = np.sort(rng.uniform(0, dur, k))
    for t0 in tiempos:
        e = env_t(t0)
        if rng.random() > e:
            continue
        largo = int(rng.uniform(0.004, 0.014) * SR)
        r = rng.standard_normal(largo) * np.exp(-np.arange(largo) / (largo / 4))
        centro = rng.uniform(900, 2600)
        r = pasabanda(np.pad(r, (0, 256)), centro * 0.6, centro * 1.5)[:largo]
        g = rng.uniform(0.3, 1.0)
        pan = rng.uniform(0.15, 0.85)
        i = int(t0 * SR)
        j = min(i + largo, n)
        st[i:j, 0] += r[:j - i] * g * (1 - pan)
        st[i:j, 1] += r[:j - i] * g * pan
    return reverb(st, 1.4, 0.3)


def murmullo(dur):
    n = int(dur * SR)
    blanco = rng.standard_normal((n, 2))
    X = np.fft.rfft(blanco, axis=0)
    f = np.fft.rfftfreq(n, 1 / SR)[:, None]
    rosa = np.fft.irfft(X / np.sqrt(np.maximum(f, 20)), n, axis=0)
    st = np.stack([pasabanda(rosa[:, c], 150, 900) for c in range(2)], 1)
    t = np.arange(n) / SR
    st *= (0.7 + 0.3 * np.sin(2 * np.pi * 0.6 * t + rng.uniform(0, 6)))[:, None]
    return st * np.clip(t / 0.5, 0, 1)[:, None] * np.clip((dur - t) / 0.8, 0, 1)[:, None]


def brillo(dur):
    n = int(dur * SR)
    st = np.zeros((n, 2))
    notas = [1046.5, 1318.5, 1568.0, 2093.0, 2637.0, 3136.0]   # do-mi-sol en dos octavas, ascendente
    for k, f0 in enumerate(notas):
        i = int(k * 0.055 * SR)
        m = n - i
        t = np.arange(m) / SR
        tono = sum(a * np.sin(2 * np.pi * f0 * p * t) * np.exp(-t * d)
                   for p, a, d in [(1, 1.0, 3.2), (2.76, 0.45, 6.0), (5.4, 0.2, 11.0)])
        tono *= np.clip(t / 0.003, 0, 1) * (0.8 ** k + 0.25)
        pan = 0.3 + 0.4 * k / (len(notas) - 1)
        st[i:, 0] += tono * (1 - pan)
        st[i:, 1] += tono * pan
    return reverb(st, 2.2, 0.35)


def guardar(st, ruta):
    st = st / (np.abs(st).max() + 1e-9) * 10 ** (-3 / 20)
    with wave.open(ruta, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((st * 32767).astype(np.int16).tobytes())


if __name__ == "__main__":
    tipo, ruta = sys.argv[1], sys.argv[2]
    dur = float(sys.argv[3]) if len(sys.argv) > 3 else {"aplausos": 5.0, "brillo": 2.5, "murmullo": 5.0}[tipo]
    guardar({"aplausos": aplausos, "brillo": brillo, "murmullo": murmullo}[tipo](dur), ruta)
    print(ruta)
