import React from "react";
import { AbsoluteFill, Easing, Img, interpolate, interpolateColors, spring, staticFile, useCurrentFrame } from "remotion";
import { COLORES, RESPLANDOR, Textos } from "../dynamic/Textos";
import { BLOQUES } from "../generado/p02v2.gen";

// Prueba-02 v2 (Sunny Shore) con el estilo dynamic de Sebas (marcas/sebastian/formato-dynamic.md).
// Una sola capa transparente encima del video: subtítulos por pisos, el motion graphic del tramo sin color
// (renta vs fix & flip sobre la toma aérea) y el logo. Los destellos blancos de transición van en ffmpeg (debajo).
export const FPS = 24000 / 1001;
export const DURACION_S = 48.38;
const c = (s: number) => Math.round(s * FPS);
const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const SALE = Easing.bezier(0.22, 1, 0.36, 1);
const { amarillo: AMARILLO, rojo: ROJO, naranja: NARANJA, lima: LIMA, verde: VERDE } = COLORES;

/** 0..1 de entrada y salida (borrosa), para piezas del gráfico. */
const vida = (f: number, desde: number, hasta: number, entra = 0.18, sale = 0.18) => ({
  p: interpolate(f, [c(desde), c(desde + entra)], [0, 1], { ...clamp, easing: SALE }),
  q: interpolate(f, [c(hasta - sale), c(hasta)], [0, 1], clamp),
  visible: f >= c(desde) && f < c(hasta),
});

/** Texto del gráfico que entra deslizando con desenfoque (mismo lenguaje que los subtítulos). */
const Entra: React.FC<{ f: number; desde: number; hasta: number; children: React.ReactNode; style?: React.CSSProperties }> = ({ f, desde, hasta, children, style }) => {
  const { p, q, visible } = vida(f, desde, hasta);
  if (!visible) return null;
  return (
    <div style={{ transform: `translateX(${(1 - p) * -80}px) translateY(${-q * 30}px)`, opacity: Math.min(1, p * 1.6) * (1 - q),
      filter: `blur(${(1 - p) * 8 + q * 10}px)`, ...style }}>{children}</div>
  );
};

const texto = (tam: number, color: string, peso = 700, it = false): React.CSSProperties => ({
  fontFamily: "Inter", fontSize: tam, fontWeight: peso, fontStyle: it ? "italic" : "normal", color, lineHeight: 1,
  letterSpacing: -tam * 0.025, whiteSpace: "nowrap", textShadow: RESPLANDOR, textAlign: "center",
});

// La casa en la toma aérea (dron_cielo desde el segundo 8): el techo deriva un poco a la derecha mientras orbita.
const casa = (f: number) => {
  const u = interpolate(f, [c(23.24), c(31.38)], [0, 1], clamp);
  return { x: 430 + 80 * u, y: 1090 - 22 * u, w: 700, h: 560, giro: -18 };
};

/** Contorno que se dibuja alrededor de la casa + brillo que la barre. */
const ContornoCasa: React.FC<{ f: number; color: string }> = ({ f, color }) => {
  const k = casa(f);
  const dibujo = interpolate(f, [c(23.7), c(24.3)], [0, 1], { ...clamp, easing: Easing.inOut(Easing.cubic) });
  const barrido = interpolate(f, [c(24.2), c(24.9)], [-0.3, 1.3], clamp);
  const largo = 2 * (k.w + k.h);
  const vendida = spring({ frame: f - c(30.62), fps: FPS, config: { damping: 9, stiffness: 220 } });
  const latido = f >= c(30.62) ? 1 + 0.04 * Math.sin((f - c(30.62)) / 3) * Math.exp(-(f - c(30.62)) / 14) : 1;
  return (
    <div style={{ position: "absolute", left: k.x - k.w / 2, top: k.y - k.h / 2, width: k.w, height: k.h, transform: `rotate(${k.giro}deg) scale(${latido})` }}>
      <svg width={k.w} height={k.h} style={{ overflow: "visible" }}>
        <rect x="0" y="0" width={k.w} height={k.h} rx="60" fill="none" stroke={color} strokeWidth="10"
          strokeDasharray={largo} strokeDashoffset={largo * (1 - dibujo)} style={{ filter: `drop-shadow(0 0 14px ${color})` }} />
      </svg>
      {/* Brillo diagonal que barre la casa una vez dibujado el contorno */}
      <div style={{ position: "absolute", inset: 0, borderRadius: 60, overflow: "hidden", opacity: barrido > -0.3 && barrido < 1.3 ? 1 : 0 }}>
        <div style={{ position: "absolute", top: -k.h, height: k.h * 3, width: 140, left: `${barrido * 100}%`, transform: "rotate(20deg)",
          background: "linear-gradient(90deg, transparent, rgba(255,255,255,0.45), transparent)" }} />
      </div>
      {/* Etiqueta pegada al contorno */}
      <div style={{ position: "absolute", left: 40, top: -38, ...texto(44, "#111", 900, true), textShadow: "none", background: color,
        padding: "8px 22px 4px", transform: `scale(${interpolate(f, [c(23.9), c(24.15)], [0, 1], { ...clamp, easing: Easing.back(2) })})`, transformOrigin: "left center" }}>
        {f < c(26.64) ? "RENTA" : "FIX & FLIP"}
      </div>
      {f >= c(30.62) && (
        <div style={{ position: "absolute", left: "50%", top: "50%", transform: `translate(-50%,-50%) rotate(-8deg) scale(${vendida * 1.0})`,
          ...texto(110, VERDE, 900, true), textShadow: "none", border: `10px solid ${VERDE}`, padding: "10px 34px 0", background: "rgba(0,0,0,0.55)" }}>VENDIDA</div>
      )}
    </div>
  );
};

/** La curva que sube (como el 0 → 10.000 de prueba-01): de la renta (1.000 $/mes) a 100.000 $ en una venta. */
const Curva: React.FC<{ f: number; avance: number }> = ({ f, avance }) => {
  const { p, q, visible } = vida(f, 27.6, 30.1, 0.3, 0.25);
  if (!visible) return null;
  const W = 800, H = 520, x0 = 140, y0 = 1500;
  const pts = Array.from({ length: 81 }, (_, i) => i / 80).filter((x) => x <= avance + 1e-6)
    .map((x) => [x * W, H - 20 - (H - 60) * Math.pow(x, 2.4)] as const);
  const ultimo = pts[pts.length - 1];
  const color = interpolateColors(avance, [0, 0.6, 1], [NARANJA, LIMA, VERDE]);
  return (
    <div style={{ position: "absolute", left: x0, top: y0 - H, width: W, height: H, opacity: p * (1 - q), filter: `blur(${q * 10}px)` }}>
      <svg width={W} height={H} style={{ overflow: "visible" }}>
        {[0.25, 0.5, 0.75].map((g) => <line key={g} x1="0" x2={W} y1={H * g} y2={H * g} stroke="rgba(255,255,255,0.15)" strokeWidth="2" strokeDasharray="6 12" />)}
        <line x1="0" y1={H - 20} x2={W} y2={H - 20} stroke="rgba(255,255,255,0.45)" strokeWidth="3" />
        <polyline points={pts.map(([x, y]) => `${x.toFixed(1)},${y.toFixed(1)}`).join(" ")} fill="none" stroke={color} strokeWidth="12"
          strokeLinecap="round" strokeLinejoin="round" style={{ filter: `drop-shadow(0 0 16px ${color})` }} />
        <circle cx="0" cy={H - 20} r="16" fill={NARANJA} />
        {ultimo && <circle cx={ultimo[0]} cy={ultimo[1]} r={18 + 4 * Math.sin(f / 3)} fill={color} style={{ filter: `drop-shadow(0 0 18px ${color})` }} />}
      </svg>
      <div style={{ position: "absolute", left: -10, top: H + 8, ...texto(34, NARANJA, 700) }}>renta: 1.000 $/mes</div>
    </div>
  );
};

/** Motion graphic del tramo sin color (23,24–31,38): renta vs fix & flip sobre la toma aérea. */
const Grafico: React.FC = () => {
  const f = useCurrentFrame();
  if (f < c(23.24) || f >= c(31.38)) return null;
  const velo = interpolate(f, [c(23.24), c(23.6), c(27.4), c(27.9), c(30.0), c(30.4)], [0, 0.32, 0.32, 0.58, 0.58, 0.35], clamp);
  const sale = interpolate(f, [c(31.1), c(31.38)], [0, 1], clamp);
  // Renta: 500 $ (rojo) -> 1.000 $ (naranja), como lo dicen ("500, mil dólares de cash flow al mes").
  const renta = interpolate(f, [c(24.62), c(24.8), c(24.94), c(25.3)], [0, 500, 500, 1000], { ...clamp, easing: SALE });
  const colorRenta = interpolateColors(renta, [500, 1000], [ROJO, NARANJA]);
  // Fix & flip: 60K -> 70K -> 100.000 $ con la voz; la curva sube con el número.
  const k = f < c(27.92) ? 0 : f < c(28.6) ? interpolate(f, [c(27.92), c(28.22)], [0, 60], { ...clamp, easing: SALE })
    : f < c(29.34) ? interpolate(f, [c(28.6), c(28.82)], [60, 70], { ...clamp, easing: SALE })
    : interpolate(f, [c(29.34), c(29.75)], [70, 100], { ...clamp, easing: SALE });
  const colorFlip = interpolateColors(k, [0, 60, 100], [LIMA, LIMA, VERDE]);
  const golpe = (t: number) => (f >= c(t) ? 1 + 0.12 * Math.exp(-(f - c(t)) / 3) : 1);
  const colorContorno = f < c(26.64) ? (renta > 0 ? colorRenta : AMARILLO) : f < c(30.62) ? colorFlip : VERDE;
  return (
    <AbsoluteFill style={{ opacity: 1 - sale, filter: `blur(${sale * 12}px)` }}>
      <AbsoluteFill style={{ background: "linear-gradient(180deg, rgba(0,0,0,0.85) 0%, rgba(0,0,0,0.25) 40%, rgba(0,0,0,0.6) 100%)", opacity: velo * 1.4 }} />
      {/* Mientras sube la curva, el contorno de la casa queda atenuado para no cruzarse con ella */}
      <div style={{ opacity: interpolate(f, [c(27.5), c(27.8), c(30.0), c(30.3)], [1, 0.22, 0.22, 1], clamp) }}>
        <ContornoCasa f={f} color={colorContorno} />
      </div>
      <Curva f={f} avance={k / 100} />
      {/* Zona de textos de arriba (y 330–760) */}
      <div style={{ position: "absolute", top: 330, width: 1080, display: "flex", flexDirection: "column", alignItems: "center", gap: 6 }}>
        <Entra f={f} desde={23.24} hasta={24.6}><div style={texto(54, "#fff", 500)}>Qué te va a dejar</div></Entra>
        <Entra f={f} desde={24.0} hasta={24.6}><div style={texto(104, AMARILLO, 700)}>una renta?</div></Entra>
        <Entra f={f} desde={24.62} hasta={26.64}>
          <div style={{ ...texto(170, colorRenta, 900, true), transform: `scale(${golpe(24.62) * golpe(24.94)})` }}>{Math.round(renta).toLocaleString("es-VE")} $</div>
        </Entra>
        <Entra f={f} desde={25.88} hasta={26.64}><div style={texto(54, "#fff", 600, true)}>de cash flow <span style={{ fontSize: 38 }}>/mes</span></div></Entra>
        <Entra f={f} desde={26.64} hasta={30.04}><div style={texto(72, AMARILLO, 600)}>Nosotros</div></Entra>
        <Entra f={f} desde={27.34} hasta={30.04}><div style={texto(50, "#fff", 900, true)}>PODEMOS HACER</div></Entra>
        <Entra f={f} desde={29.16} hasta={30.04}><div style={texto(64, "#fff", 900, true)}>y hasta</div></Entra>
        <Entra f={f} desde={27.92} hasta={30.04}>
          <div style={{ ...texto(k >= 100 ? 150 : 140, colorFlip, 900, true), transform: `scale(${golpe(27.92) * golpe(28.6) * golpe(29.34)})` }}>
            {k >= 99.5 ? "100.000 $" : `${Math.round(k)}K USD`}
          </div>
        </Entra>
        <Entra f={f} desde={30.04} hasta={31.38}><div style={texto(54, "#fff", 500)}>en una sola</div></Entra>
        <Entra f={f} desde={30.62} hasta={31.38}>
          <div style={{ position: "relative" }}>
            <div style={texto(112, AMARILLO, 700)}>transacción</div>
            {/* Subrayado que se dibuja de izquierda a derecha */}
            <div style={{ position: "absolute", left: 0, bottom: -18, height: 12, background: AMARILLO, boxShadow: `0 0 16px ${AMARILLO}`,
              width: `${interpolate(f, [c(30.7), c(30.95)], [0, 100], { ...clamp, easing: SALE })}%` }} />
          </div>
        </Entra>
      </div>
    </AbsoluteFill>
  );
};

/** Logo de Sunny Shore sobre el pecho cuando lo nombran; cruza el corte hacia la toma del dron y se va borroso. */
const Logo: React.FC = () => {
  const f = useCurrentFrame();
  const { p, q, visible } = vida(f, 35.62, 37.45, 0.3, 0.3);
  if (!visible) return null;
  return (
    <div style={{ position: "absolute", top: 1000, width: 1080, display: "flex", justifyContent: "center",
      transform: `translateY(-50%) scale(${0.92 + 0.08 * p + 0.04 * q})`, opacity: p * (1 - q), filter: `blur(${(1 - p) * 10 + q * 12}px) drop-shadow(0 6px 26px rgba(0,0,0,0.5))` }}>
      <Img src={staticFile("sunny/logo-blanco.png")} style={{ width: 600 }} />
    </div>
  );
};

export const Prueba02v2: React.FC = () => (
  <AbsoluteFill>
    <Grafico />
    <Logo />
    <Textos bloques={BLOQUES} />
  </AbsoluteFill>
);
