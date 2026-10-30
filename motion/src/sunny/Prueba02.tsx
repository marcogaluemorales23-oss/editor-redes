import React from "react";
import { AbsoluteFill, Easing, Img, interpolate, spring, staticFile, useCurrentFrame } from "remotion";

// Prueba-02 (Sunny Shore, cliente de Sebas): mismo estilo que Sebas (Inter, amarillo #FCF304 en caja negra recta).
// Dos capas:
//  - "detras": títulos GRANDES arriba, DETRÁS de las personas (debajo del recorte persona.mov de nucleo/silueta.py).
//    Son la palabra fuerte de la frase; el resto de la frase va en los subtítulos fijos del pecho (subtitulos.py).
//  - "frente": el motion graphic del tramo sin color (renta vs fix & flip) y la llamada a la acción (comentario FLIP).
export const FPS = 24000 / 1001;
export const DURACION_S = 48.38;
const AMARILLO = "#FCF304";
const NEGRO = "#111111";
const TEXTO = "#1c1a17";
const c = (s: number) => Math.round(s * FPS);
const CURVA = Easing.bezier(0.22, 1, 0.36, 1);
const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

/** 0..1 de entrada (con rebote suave) y de salida (borrosa). */
const useVida = (desde: number, hasta: number, entra = 0.28, sale = 0.2) => {
  const f = useCurrentFrame();
  const p = interpolate(f, [c(desde), c(desde + entra)], [0, 1], { ...clamp, easing: Easing.bezier(0.34, 1.35, 0.64, 1) });
  const q = interpolate(f, [c(hasta - sale), c(hasta)], [0, 1], { ...clamp, easing: CURVA });
  return { f, p, q, visible: f >= c(desde) && f < c(hasta) };
};

/** Palabra fuerte arriba, detrás de las personas: amarilla Inter Black Italic en caja negra recta (regla de Sebas). */
const Arriba: React.FC<{ desde: number; hasta: number; texto: string; y?: number; max?: number }> = ({ desde, hasta, texto, y = 470, max = 230 }) => {
  const { p, q, visible } = useVida(desde, hasta);
  if (!visible) return null;
  // Ancho máximo 820 (centrado en 540, el borde seguro derecho está en x=950).
  const tam = Math.min(max, 820 / (texto.length * 0.64 + 0.5));
  return (
    <div style={{ position: "absolute", left: 0, width: 1080, top: y, display: "flex", justifyContent: "center",
      transform: `translateY(-50%) translateY(${(1 - p) * 40 - q * 20}px) scale(${0.9 + 0.1 * p})`,
      opacity: Math.min(1, p * 1.5) * (1 - q), filter: `blur(${(1 - Math.min(1, p)) * 10 + q * 12}px)` }}>
      <div style={{ background: NEGRO, padding: `${tam * 0.06}px ${tam * 0.16}px ${tam * 0.02}px`, fontFamily: "Inter", fontWeight: 900,
        fontStyle: "italic", fontSize: tam, lineHeight: 1, color: AMARILLO, letterSpacing: -tam * 0.03, whiteSpace: "nowrap" }}>{texto}</div>
    </div>
  );
};

/** "NO NO NO": cada NO entra con su palabra. */
const NoNoNo: React.FC = () => {
  const f = useCurrentFrame();
  const tiempos = [4.12, 4.5, 4.62];
  const fin = 4.8;
  if (f < c(tiempos[0]) || f >= c(fin)) return null;
  return (
    <div style={{ position: "absolute", top: 470, width: 1080, display: "flex", justifyContent: "center", gap: 22, transform: "translateY(-50%)" }}>
      {tiempos.map((t, i) => {
        const s = spring({ frame: f - c(t), fps: FPS, config: { damping: 10, stiffness: 260 } });
        return f >= c(t) ? (
          <div key={i} style={{ background: NEGRO, padding: "10px 26px 2px", fontFamily: "Inter", fontWeight: 900, fontStyle: "italic", fontSize: 200,
            lineHeight: 1, color: AMARILLO, transform: `scale(${s}) rotate(${(i - 1) * 4}deg)` }}>NO</div>
        ) : null;
      })}
    </div>
  );
};

/** Logo de Sunny Shore (blanco) en caja negra recta, detrás de las personas. */
const LogoArriba: React.FC<{ desde: number; hasta: number }> = ({ desde, hasta }) => {
  const { p, q, visible } = useVida(desde, hasta);
  if (!visible) return null;
  return (
    <div style={{ position: "absolute", top: 450, width: 1080, display: "flex", justifyContent: "center",
      transform: `translateY(-50%) scale(${0.9 + 0.1 * p})`, opacity: Math.min(1, p * 1.5) * (1 - q), filter: `blur(${q * 12}px)` }}>
      <div style={{ background: NEGRO, padding: "34px 48px" }}>
        <Img src={staticFile("sunny/logo-blanco.png")} style={{ width: 640, display: "block" }} />
      </div>
    </div>
  );
};

// ---------- Motion graphic del tramo sin color: renta vs fix & flip ----------

const Casa: React.FC<{ tam: number; color: string; detalle: "llave" | "dolar" }> = ({ tam, color, detalle }) => (
  <svg width={tam} height={tam} viewBox="0 0 100 100">
    <path d="M12 46 L50 14 L88 46 L88 90 L12 90 Z" fill="none" stroke={color} strokeWidth="7" strokeLinejoin="round" />
    <rect x="40" y="62" width="20" height="28" fill={color} />
    {detalle === "llave" ? (
      <g transform="translate(66 56)"><circle cx="0" cy="0" r="9" fill="none" stroke={color} strokeWidth="5" /><path d="M8 4 L22 18 M16 12 L12 16 M20 16 L16 20" stroke={color} strokeWidth="5" strokeLinecap="round" /></g>
    ) : (
      <text x="70" y="72" fontFamily="Inter" fontWeight="900" fontStyle="italic" fontSize="36" fill={color}>$</text>
    )}
  </svg>
);

const Contador: React.FC<{ valor: number; sufijo: string; tam: number; color: string }> = ({ valor, sufijo, tam, color }) => (
  <div style={{ fontFamily: "Inter", fontWeight: 900, fontStyle: "italic", fontSize: tam, lineHeight: 1, color, letterSpacing: -tam * 0.03 }}>
    ${Math.round(valor).toLocaleString("en-US")}{sufijo}
  </div>
);

const Comparativa: React.FC<{ desde: number; hasta: number }> = ({ desde, hasta }) => {
  const f = useCurrentFrame();
  if (f < c(desde) || f >= c(hasta)) return null;
  const sale = interpolate(f, [c(hasta - 0.25), c(hasta)], [0, 1], { ...clamp, easing: CURVA });
  const entra = (t: number) => interpolate(f, [c(t), c(t + 0.35)], [0, 1], { ...clamp, easing: Easing.bezier(0.34, 1.3, 0.64, 1) });
  // Renta: aparece en "renta" y su número en "500 ... al mes".
  const renta = entra(desde);
  const quinientos = interpolate(f, [c(24.62), c(25.3)], [0, 500], { ...clamp, easing: CURVA });
  // Fix & flip: aparece en "nosotros podemos hacer"; el contador salta 60K -> 70K -> 100K con la voz.
  const flip = entra(26.64);
  const k = f < c(27.92) ? 0 : f < c(28.6) ? interpolate(f, [c(27.92), c(28.25)], [0, 60000], { ...clamp, easing: CURVA })
    : f < c(29.34) ? interpolate(f, [c(28.6), c(28.85)], [60000, 70000], { ...clamp, easing: CURVA })
    : interpolate(f, [c(29.34), c(29.9)], [70000, 100000], { ...clamp, easing: CURVA });
  const barraFlip = 560 * (k / 100000);
  const sello = spring({ frame: f - c(30.3), fps: FPS, config: { damping: 9, stiffness: 240 } });
  const BASE = 1420;
  return (
    <AbsoluteFill style={{ opacity: 1 - sale, filter: `blur(${sale * 14}px)`, fontFamily: "Inter" }}>
      {/* Columna renta */}
      <div style={{ position: "absolute", left: 120, width: 400, top: 330, display: "flex", flexDirection: "column", alignItems: "center", gap: 18,
        opacity: renta, transform: `translateY(${(1 - renta) * 40}px)` }}>
        <Casa tam={150} color={TEXTO} detalle="llave" />
        <div style={{ fontWeight: 900, fontStyle: "italic", fontSize: 66, color: TEXTO }}>RENTA</div>
        <Contador valor={quinientos} sufijo="" tam={92} color={TEXTO} />
        <div style={{ fontWeight: 700, fontSize: 34, color: "rgba(28,26,23,0.65)" }}>al mes</div>
      </div>
      {/* Columna fix & flip */}
      <div style={{ position: "absolute", left: 560, width: 400, top: 330, display: "flex", flexDirection: "column", alignItems: "center", gap: 18,
        opacity: flip, transform: `translateY(${(1 - flip) * 40}px)` }}>
        <Casa tam={150} color={TEXTO} detalle="dolar" />
        <div style={{ background: NEGRO, color: AMARILLO, fontWeight: 900, fontStyle: "italic", fontSize: 58, padding: "4px 16px 0" }}>FIX & FLIP</div>
        <Contador valor={k} sufijo="" tam={92} color={TEXTO} />
        <div style={{ fontWeight: 700, fontSize: 34, color: "rgba(28,26,23,0.65)" }}>por casa</div>
      </div>
      {/* Barras: la renta casi no se ve al lado del flip */}
      <div style={{ position: "absolute", left: 120, width: 840, top: BASE, height: 4, background: "rgba(28,26,23,0.25)" }} />
      <div style={{ position: "absolute", left: 250, width: 140, top: BASE - 10 * Math.min(1, quinientos / 500), height: 10 * Math.min(1, quinientos / 500), background: TEXTO, opacity: renta }} />
      <div style={{ position: "absolute", left: 690, width: 140, top: BASE - barraFlip, height: barraFlip, background: NEGRO, opacity: flip }}>
        <div style={{ position: "absolute", left: 0, right: 0, top: 0, height: 14, background: AMARILLO }} />
      </div>
      {/* Sello en "una sola transacción" */}
      {f >= c(30.3) && (
        <div style={{ position: "absolute", top: 1480, width: 1080, display: "flex", justifyContent: "center" }}>
          <div style={{ background: AMARILLO, color: NEGRO, fontWeight: 900, fontStyle: "italic", fontSize: 54, padding: "8px 22px 2px",
            transform: `scale(${sello}) rotate(-4deg)`, boxShadow: "0 14px 30px rgba(0,0,0,0.25)" }}>EN UNA SOLA VENTA</div>
        </div>
      )}
    </AbsoluteFill>
  );
};

// ---------- Llamada a la acción: comentario FLIP + flecha hacia abajo ----------

const Comentario: React.FC<{ desde: number; hasta: number }> = ({ desde, hasta }) => {
  const { f, p, q, visible } = useVida(desde, hasta, 0.35, 0.25);
  if (!visible) return null;
  const letras = Math.floor(interpolate(f, [c(45.84), c(46.2)], [0, 4], clamp));
  const enviado = interpolate(f, [c(46.4), c(46.6)], [0, 1], clamp);
  const cursor = Math.floor(f / 12) % 2 === 0 && letras < 4;
  return (
    <div style={{ position: "absolute", top: 300, left: 110, width: 860, display: "flex", alignItems: "center", gap: 22, padding: "20px 24px",
      borderRadius: 60, background: "rgba(255,255,255,0.97)", boxShadow: "0 18px 44px rgba(0,0,0,0.25)", fontFamily: "Inter",
      opacity: Math.min(1, p * 1.5) * (1 - q), transform: `translateY(${(1 - p) * 30}px)`, filter: `blur(${q * 10}px)` }}>
      <div style={{ width: 88, height: 88, borderRadius: 44, overflow: "hidden", background: "#e9e9e9", display: "flex", alignItems: "center", justifyContent: "center" }}>
        <Img src={staticFile("sunny/logo_color.png")} style={{ height: 88, objectFit: "cover", objectPosition: "32% 50%", width: 88, transform: "scale(3.2) translateX(10%)" }} />
      </div>
      <div style={{ flex: 1, fontSize: 56, fontWeight: 900, fontStyle: "italic", color: "#111" }}>
        {"FLIP".slice(0, letras)}{cursor ? "|" : ""}
        {letras === 0 && <span style={{ fontStyle: "normal", fontWeight: 600, fontSize: 36, color: "#999" }}>Añade un comentario…</span>}
      </div>
      <div style={{ width: 88, height: 88, borderRadius: 44, background: enviado > 0.5 ? NEGRO : "#3897f0", display: "flex", alignItems: "center", justifyContent: "center",
        transform: `scale(${1 + 0.2 * Math.sin(enviado * Math.PI)})` }}>
        <svg width="42" height="42" viewBox="0 0 24 24"><path d="M3 11l18-8-8 18-2-8z" fill={enviado > 0.5 ? AMARILLO : "#fff"} /></svg>
      </div>
    </div>
  );
};

const Flecha: React.FC<{ desde: number; hasta: number }> = ({ desde, hasta }) => {
  const { f, p, q, visible } = useVida(desde, hasta);
  if (!visible) return null;
  const rebote = Math.abs(Math.sin((f - c(desde)) / FPS * 6)) * 24;
  return (
    <div style={{ position: "absolute", top: 1330 + rebote, width: 1080, display: "flex", justifyContent: "center", opacity: Math.min(1, p) * (1 - q) }}>
      <svg width="110" height="130" viewBox="0 0 110 130" style={{ filter: "drop-shadow(0 8px 18px rgba(0,0,0,0.45))" }}>
        <path d="M55 6 L55 104 M16 68 L55 112 L94 68" fill="none" stroke={AMARILLO} strokeWidth="16" strokeLinecap="square" />
      </svg>
    </div>
  );
};

export const Prueba02: React.FC<{ capa?: "frente" | "detras" }> = ({ capa = "frente" }) =>
  capa === "detras" ? (
    <AbsoluteFill>
      {/* Gancho: la palabra fuerte arriba, detrás de ellos; el resto de la frase en el pecho */}
      <Arriba desde={0.68} hasta={1.94} texto="DINERO" />
      <Arriba desde={3.4} hasta={4.08} texto="RENTAR" />
      <NoNoNo />
      <Arriba desde={5.58} hasta={6.18} texto="REMODELAR" />
      <Arriba desde={6.18} hasta={6.76} texto="Y VENDER" />
      <Arriba desde={9.46} hasta={11.0} texto="NI UN DÓLAR" />
      <Arriba desde={22.5} hasta={23.24} texto="FIX & FLIP" y={450} />
      {/* Sunny Shore y lo que hacen, en lista: la blanca fija en el pecho, la amarilla cambia arriba */}
      <LogoArriba desde={35.6} hasta={36.78} />
      <Arriba desde={36.84} hasta={37.86} texto="ADQUISICIÓN" y={430} />
      <Arriba desde={37.88} hasta={39.18} texto="REMODELACIÓN" y={430} />
      <Arriba desde={39.2} hasta={39.74} texto="SALIDA" y={430} />
    </AbsoluteFill>
  ) : (
    <AbsoluteFill>
      <Comparativa desde={23.24} hasta={31.36} />
      <Comentario desde={44.84} hasta={48.38} />
      <Flecha desde={46.36} hasta={48.38} />
    </AbsoluteFill>
  );

