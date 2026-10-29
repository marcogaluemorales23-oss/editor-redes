import React from "react";
import { AbsoluteFill, Easing, Img, interpolate, spring, staticFile, useCurrentFrame } from "remotion";

// Prueba-01 al estilo dynamic vd2 (lo eligió Sebas): el video se DIFUMINA arriba (lo hace ffmpeg,
// nucleo/componer_difuminado.py) y aquí solo va lo que flota encima: título + tarjeta, pantallas
// completas y la tarjeta de capítulo. Todo entra suave: fundido + desenfoque + 16 px de subida.
// Zona libre: título en y≈236, tarjeta entre 330 y 690 (el subtítulo va en la costura, ~730-830).
export const FPS = 60;
export const DURACION_S = 36.0;
// Tema claro (eligió Sebas, como vd2): crema, texto casi negro, clave en terracota.
const TEXTO = "#1c1a17";
const ACENTO = "#C8553D";
const CREMA = "#F4F0E8";
const AMARILLO = "#FCF304";
const ENTRA = 0.45;
const SALE = 0.35;
const c = (s: number) => Math.round(s * FPS);
const CURVA = Easing.bezier(0.22, 1, 0.36, 1);

/** Opacidad, desenfoque y subida de un elemento que vive entre desde y hasta. */
const useSuave = (desde: number, hasta: number, retraso = 0) => {
  const f = useCurrentFrame();
  const a = desde + retraso;
  const p = interpolate(f, [c(a), c(a + ENTRA)], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: CURVA });
  const q = interpolate(f, [c(hasta - SALE), c(hasta)], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: CURVA });
  const v = p * (1 - q);
  return {
    visible: f >= c(a) && f < c(hasta),
    estilo: { opacity: v, filter: `blur(${(1 - v) * 10}px)`, transform: `translateY(${(1 - p) * 16 - q * 10}px)` } as React.CSSProperties,
  };
};

/** Título: apoyo en Inter Bold blanca + clave en Inter Black Italic amarilla, en una línea, centrado. */
const Titulo: React.FC<{ apoyo: string; clave: string; desde: number; hasta: number; y?: number; tam?: number }> = ({ apoyo, clave, desde, hasta, y = 236, tam = 60 }) => {
  const { visible, estilo } = useSuave(desde, hasta);
  if (!visible) return null;
  return (
    <div style={{ position: "absolute", top: y, width: 1080, textAlign: "center", fontFamily: "Inter", whiteSpace: "nowrap", ...estilo }}>
      <span style={{ fontWeight: 700, fontSize: tam, color: TEXTO }}>{apoyo} </span>
      <span style={{ fontWeight: 900, fontStyle: "italic", fontSize: tam * 1.14, color: ACENTO }}>{clave}</span>
    </div>
  );
};

const LogoIG: React.FC<{ tam: number }> = ({ tam }) => (
  <svg width={tam} height={tam} viewBox="0 0 100 100">
    <defs>
      <radialGradient id="igc" cx="30%" cy="107%" r="150%">
        <stop offset="0%" stopColor="#fdf497" /><stop offset="10%" stopColor="#fdf497" /><stop offset="50%" stopColor="#fd5949" />
        <stop offset="68%" stopColor="#d6249f" /><stop offset="100%" stopColor="#285AEB" />
      </radialGradient>
    </defs>
    <rect x="4" y="4" width="92" height="92" rx="26" fill="url(#igc)" />
    <rect x="24" y="24" width="52" height="52" rx="16" fill="none" stroke="#fff" strokeWidth="7" />
    <circle cx="50" cy="50" r="12" fill="none" stroke="#fff" strokeWidth="7" />
    <circle cx="68" cy="32" r="4.5" fill="#fff" />
  </svg>
);

/** Ícono suelto DETRÁS de Sebas (regla de Sebas: nada de "ícono con título encima"; el ícono va a un lado,
 * detrás de él). Esta capa se pone debajo del recorte de la persona (nucleo/silueta.py -> persona.mov).
 * Entra creciendo desde atrás con desenfoque, flota suave y sale borroso. */
const Detras: React.FC<{ desde: number; hasta: number; x: number; y: number; children: React.ReactNode }> = ({ desde, hasta, x, y, children }) => {
  const f = useCurrentFrame();
  const p = interpolate(f, [c(desde), c(desde + 0.5)], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.bezier(0.34, 1.4, 0.64, 1) });
  const q = interpolate(f, [c(hasta - SALE), c(hasta)], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: CURVA });
  if (f < c(desde) || f >= c(hasta)) return null;
  const o = Math.min(1, p * 1.6) * (1 - q);
  const flota = Math.sin((f - c(desde)) / FPS * 2.2) * 8;
  return (
    <div style={{ position: "absolute", left: x, top: y, transform: `translate(-50%, -50%) translateY(${flota + (1 - p) * 40}px) scale(${0.7 + 0.3 * p - 0.08 * q})`,
      opacity: o, filter: `blur(${(1 - Math.min(1, p)) * 12 + q * 14}px) drop-shadow(0 20px 30px rgba(0,0,0,0.28))` }}>
      {children}
    </div>
  );
};

/** 1 · 2 · 3 en "seguir estas tres cosas" (el de las primeras versiones, el que le gustó a Sebas): círculos oscuros
 * con borde blanco y resplandor, el 3 en amarillo; entran uno tras otro con rebote, arriba de la cabeza. */
const TresCirculos: React.FC<{ desde: number; hasta: number }> = ({ desde, hasta }) => {
  const f = useCurrentFrame();
  if (f < c(desde) || f >= c(hasta)) return null;
  const sale = interpolate(f, [c(hasta - 0.15), c(hasta)], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: CURVA });
  return (
    <div style={{ position: "absolute", top: 255, width: 1080, display: "flex", justifyContent: "center", gap: 36, opacity: 1 - sale, filter: `blur(${sale * 10}px)` }}>
      {[1, 2, 3].map((n, i) => {
        const s0 = spring({ frame: f - c(desde) - i * 5, fps: FPS, config: { damping: 11, stiffness: 230 } });
        return (
          <div key={n} style={{ width: 150, height: 150, borderRadius: 75, background: n === 3 ? AMARILLO : "rgba(20,20,20,0.82)",
            border: "4px solid rgba(255,255,255,0.92)", display: "flex", alignItems: "center", justifyContent: "center",
            fontFamily: "Inter", fontWeight: 900, fontStyle: "italic", fontSize: 96, color: n === 3 ? "#111" : "#fff",
            transform: `scale(${s0})`, opacity: Math.min(1, s0 * 2),
            boxShadow: "0 0 22px rgba(255,255,255,0.35), 0 18px 40px rgba(0,0,0,0.35)" }}>{n}</div>
        );
      })}
    </div>
  );
};

/** Iris: círculo que se abre desde (x, y) y se cierra al final. La crema va un poco adelantada al abrir y atrasada
 * al cerrar, así queda un aro crema en el borde del naranja (la transición que pidió Sebas para la clase). */
const iris = (f: number, desde: number, hasta: number, adelanto: number) => {
  const abre = interpolate(f, [c(desde - adelanto), c(desde - adelanto + 0.45)], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.bezier(0.65, 0, 0.35, 1) });
  const cierra = interpolate(f, [c(hasta - 0.3 + adelanto), c(hasta + adelanto)], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.bezier(0.65, 0, 0.35, 1) });
  return 2300 * abre * (1 - cierra);
};

/** Miniatura propia de la clase (no la foto de perfil): video EN PAUSA, título simple y barra de reproducción. */
const Miniatura: React.FC = () => (
  <div style={{ position: "relative", width: 840, height: 472, borderRadius: 28, overflow: "hidden", fontFamily: "Inter",
    background: "linear-gradient(135deg, #24201b 0%, #15120f 100%)", boxShadow: "0 30px 70px rgba(60,20,10,0.45)", border: "2px solid rgba(255,255,255,0.18)" }}>
    <div style={{ position: "absolute", left: 48, top: 52, background: AMARILLO, color: "#111", fontWeight: 900, fontStyle: "italic", fontSize: 30, padding: "6px 16px" }}>CLASE 01</div>
    <div style={{ position: "absolute", left: 48, top: 120, color: CREMA, fontWeight: 900, fontStyle: "italic", fontSize: 76, lineHeight: 0.98, letterSpacing: -2 }}>VENDER CON<br />CONTENIDO</div>
    <div style={{ position: "absolute", left: 50, top: 290, color: "rgba(244,240,232,0.7)", fontWeight: 700, fontSize: 32 }}>sin pagar anuncios</div>
    {/* En pausa: velo, botón de play y barra al inicio */}
    <div style={{ position: "absolute", inset: 0, background: "rgba(0,0,0,0.18)" }} />
    <div style={{ position: "absolute", right: 70, top: 130, width: 140, height: 140, borderRadius: 70, background: "rgba(255,255,255,0.95)",
      display: "flex", alignItems: "center", justifyContent: "center", boxShadow: "0 12px 30px rgba(0,0,0,0.35)" }}>
      <svg width="52" height="58" viewBox="0 0 46 52"><path d="M8 4 L42 26 L8 48 Z" fill={ACENTO} /></svg>
    </div>
    <div style={{ position: "absolute", left: 40, right: 40, bottom: 34, display: "flex", alignItems: "center", gap: 18, color: CREMA, fontWeight: 700, fontSize: 24 }}>
      <svg width="22" height="24" viewBox="0 0 46 52"><path d="M6 4 L42 26 L6 48 Z" fill={CREMA} /></svg>
      <div style={{ position: "relative", flex: 1, height: 6, borderRadius: 3, background: "rgba(255,255,255,0.28)" }}>
        <div style={{ position: "absolute", left: 0, top: 0, width: "4%", height: 6, borderRadius: 3, background: ACENTO }} />
        <div style={{ position: "absolute", left: "4%", top: -7, width: 20, height: 20, borderRadius: 10, background: CREMA, transform: "translateX(-50%)" }} />
      </div>
      <span>0:00 / 18:24</span>
    </div>
  </div>
);

/** Clase gratis en pantalla completa NARANJA (el fondo de la tarjeta "3 COSAS"), entra y sale por iris. */
const ClaseGratis: React.FC<{ desde: number; hasta: number }> = ({ desde, hasta }) => {
  const f = useCurrentFrame();
  if (f < c(desde - 0.07) || f >= c(hasta + 0.07)) return null;
  const pasos = [20.5, 20.63, 20.76].filter((t) => f >= c(t)).length;
  const contenido = suaveValor(f, desde + 0.2, hasta - 0.3);
  const centro = "540px 660px";
  return (
    <>
      <AbsoluteFill style={{ background: CREMA, clipPath: `circle(${iris(f, desde, hasta, 0.07)}px at ${centro})` }} />
      <AbsoluteFill style={{ background: ACENTO, clipPath: `circle(${iris(f, desde, hasta, 0)}px at ${centro})` }}>
        <div style={{ position: "absolute", top: 424, left: 120, opacity: contenido, transform: `translateY(${(1 - contenido) * 24}px) scale(${0.96 + 0.04 * contenido})` }}>
          <Miniatura />
        </div>
        <div style={{ position: "absolute", top: 950, width: 1080, display: "flex", justifyContent: "center", gap: 22, fontFamily: "Inter", opacity: contenido }}>
          {[0, 1, 2].map((i) => {
            const on = pasos > i;
            return (
              <div key={i} style={{ width: 220, height: 84, borderRadius: 42, display: "flex", alignItems: "center", justifyContent: "center", fontWeight: 900, fontStyle: "italic", fontSize: 38,
                border: `3px solid ${CREMA}`, background: on ? CREMA : "transparent", color: on ? ACENTO : CREMA, transform: `scale(${on && f < c([20.5, 20.63, 20.76][i] + 0.12) ? 1.08 : 1})` }}>PASO {i + 1}</div>
            );
          })}
        </div>
      </AbsoluteFill>
    </>
  );
};

/** Entrada/salida suave (0..1) sin hooks, para usar dentro de un componente que ya decide si se ve. */
const suaveValor = (f: number, desde: number, hasta: number) =>
  interpolate(f, [c(desde), c(desde + 0.35), c(hasta), c(hasta + 0.25)], [0, 1, 1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: CURVA });

const Perfil: React.FC = () => {
  const f = useCurrentFrame();
  const W = 540, escala = W / 1179;
  const marca = interpolate(f, [c(23.42), c(23.77)], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: CURVA });
  const { visible, estilo } = useSuave(22.62, 24.3, 0.12);
  if (!visible) return null;
  return (
    <div style={{ position: "absolute", top: 335, left: (1080 - W) / 2, width: W, height: 780 * escala, borderRadius: 28, overflow: "hidden", border: "1.5px solid rgba(255,255,255,0.95)", boxShadow: "0 18px 44px rgba(60,40,20,0.18)", ...estilo }}>
      <Img src={staticFile("sebastian/perfil_23c.png")} style={{ width: W, display: "block" }} />
      <div style={{ position: "absolute", left: 630 * escala, top: 300 * escala, width: 250 * escala, height: 130 * escala, border: `4px solid ${ACENTO}`, borderRadius: 16,
        opacity: marca, transform: `scale(${1.3 - 0.3 * marca})`, boxShadow: `0 0 18px ${ACENTO}88` }} />
    </div>
  );
};

const Contador: React.FC = () => {
  const f = useCurrentFrame();
  const p = interpolate(f, [c(28.05), c(29.25)], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.bezier(0.7, 0, 0.2, 1) });
  const n = Math.round(23 + (10000 - 23) * p);
  const W = 760, H = 330;
  const pts = Array.from({ length: 61 }, (_, i) => i / 60).filter((x) => x <= p + 1e-6).map((x) => `${(x * W).toFixed(1)},${(H - 10 - (H - 30) * Math.pow(x, 2.6)).toFixed(1)}`);
  const { visible, estilo } = useSuave(27.75, 29.75, 0.15);
  if (!visible) return null;
  return (
    <div style={{ position: "absolute", top: 300, width: 1080, fontFamily: "Inter", color: TEXTO, ...estilo }}>
      <div style={{ textAlign: "center", fontWeight: 700, fontSize: 44, opacity: 0.75 }}>seguidores</div>
      <div style={{ textAlign: "center", fontWeight: 900, fontStyle: "italic", fontSize: 180, lineHeight: 1.05, color: p >= 1 ? ACENTO : TEXTO }}>{n.toLocaleString("es-VE")}</div>
      <svg width={W} height={H} style={{ marginLeft: (1080 - W) / 2, marginTop: 30, overflow: "visible" }}>
        <line x1="0" y1={H - 10} x2={W} y2={H - 10} stroke="rgba(28,26,23,0.18)" strokeWidth="2" strokeDasharray="8 10" />
        <text x={W} y="4" textAnchor="end" fill={ACENTO} fontFamily="Inter" fontWeight="900" fontStyle="italic" fontSize="34">META 10K</text>
        <text x="0" y={H + 40} fill="rgba(28,26,23,0.6)" fontFamily="Inter" fontWeight="700" fontSize="30">hoy: 23</text>
        <polyline points={pts.join(" ")} fill="none" stroke={ACENTO} strokeWidth="8" strokeLinecap="round" strokeLinejoin="round" style={{ filter: `drop-shadow(0 6px 10px ${ACENTO}55)` }} />
      </svg>
    </div>
  );
};

const Comentario: React.FC = () => {
  const f = useCurrentFrame();
  const letras = Math.floor(interpolate(f, [c(30.5), c(30.95)], [0, 5], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }));
  const enviado = interpolate(f, [c(31.2), c(31.4)], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const cursor = Math.floor(f / 18) % 2 === 0 && letras < 5;
  const { visible, estilo } = useSuave(29.85, 32.6, 0.12);
  if (!visible) return null;
  return (
    <div style={{ position: "absolute", top: 330, left: 120, width: 840, display: "flex", alignItems: "center", gap: 22, padding: "22px 26px", borderRadius: 60, background: "rgba(255,255,255,0.97)", border: "1.5px solid rgba(255,255,255,1)", boxShadow: "0 18px 44px rgba(60,40,20,0.16)", fontFamily: "Inter", ...estilo }}>
      <Img src={staticFile("sebastian/avatar.jpg")} style={{ width: 88, height: 88, borderRadius: 44, objectFit: "cover" }} />
      <div style={{ flex: 1, fontSize: 56, fontWeight: 900, fontStyle: "italic", color: "#111" }}>
        {"RELOJ".slice(0, letras)}{cursor ? "|" : ""}
        {letras === 0 && <span style={{ fontStyle: "normal", fontWeight: 600, fontSize: 36, color: "#999" }}>Añade un comentario…</span>}
      </div>
      <div style={{ width: 88, height: 88, borderRadius: 44, background: enviado > 0.5 ? ACENTO : "#3897f0", display: "flex", alignItems: "center", justifyContent: "center", transform: `scale(${1 + 0.2 * Math.sin(enviado * Math.PI)})` }}>
        <svg width="42" height="42" viewBox="0 0 24 24"><path d="M3 11l18-8-8 18-2-8z" fill="#fff" /></svg>
      </div>
    </div>
  );
};

export const Prueba01c: React.FC<{ capa?: "frente" | "detras" }> = ({ capa = "frente" }) =>
  capa === "detras" ? (
    <AbsoluteFill>
      {/* Detrás de Sebas (debajo de su recorte) */}
      <Detras desde={1.2} hasta={3.8} x={770} y={430}><LogoIG tam={300} /></Detras>
    </AbsoluteFill>
  ) : (
    <AbsoluteFill>
      {/* Arriba (video difuminado detrás). Nada que repita el subtítulo. */}
      <Titulo apoyo="día" clave="1" desde={22.62} hasta={24.3} tam={62} />
      <Perfil />
      <Comentario />
      {/* Pantallas completas (fondo difuminado) */}
      <ClaseGratis desde={17.2} hasta={21.3} />
      <Contador />
      {/* 1 · 2 · 3 arriba de la cabeza en "seguir estas tres cosas" */}
      <TresCirculos desde={15.82} hasta={16.55} />
    </AbsoluteFill>
  );
