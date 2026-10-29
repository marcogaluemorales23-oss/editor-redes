import React from "react";
import { AbsoluteFill, Easing, Img, interpolate, staticFile, useCurrentFrame } from "remotion";

// Prueba-01 al estilo dynamic vd2 (lo eligió Sebas): el video se DIFUMINA arriba (lo hace ffmpeg,
// nucleo/componer_difuminado.py) y aquí solo va lo que flota encima: título + tarjeta de vidrio, pantallas
// completas y la tarjeta de capítulo. Todo entra suave: fundido + desenfoque + 16 px de subida.
// Zona libre: título en y≈236, tarjeta entre 330 y 690 (el subtítulo va en la costura, ~730-830).
export const FPS = 60;
export const DURACION_S = 36.0;
// Tema claro (eligió Sebas, como vd2): crema, texto casi negro, clave en terracota.
const TEXTO = "#1c1a17";
const ACENTO = "#C8553D";
const CREMA = "#F4F0E8";
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

const vidrio: React.CSSProperties = {
  background: "rgba(255,255,255,0.62)",
  border: "1.5px solid rgba(255,255,255,0.9)",
  borderRadius: 34,
  boxShadow: "0 18px 44px rgba(60,40,20,0.14), inset 0 1px 0 rgba(255,255,255,0.9)",
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

const Reloj: React.FC<{ tam?: number }> = ({ tam = 170 }) => {
  const f = useCurrentFrame();
  const p = interpolate(f, [c(10.6), c(13.4)], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <svg width={tam} height={tam * 1.36} viewBox="0 0 100 136">
      <rect x="8" y="2" width="84" height="10" rx="5" fill={TEXTO} />
      <rect x="8" y="124" width="84" height="10" rx="5" fill={TEXTO} />
      <path d="M18 12 C18 48 46 58 46 68 C46 78 18 88 18 124 L82 124 C82 88 54 78 54 68 C54 58 82 48 82 12 Z" fill="rgba(255,255,255,0.75)" stroke={TEXTO} strokeWidth="3" />
      <clipPath id="arenaC"><rect x="0" y={12 + 46 * p} width="100" height={56 - 46 * p} /></clipPath>
      <path d="M22 16 C22 46 47 56 48 66 L52 66 C53 56 78 46 78 16 Z" fill={ACENTO} clipPath="url(#arenaC)" />
      <rect x="48.5" y="66" width="3" height={58 - 40 * p} fill={ACENTO} opacity={p < 0.98 ? 1 : 0} />
      <path d={`M22 121 C24 ${121 - 34 * p} 76 ${121 - 34 * p} 78 121 Z`} fill={ACENTO} />
    </svg>
  );
};

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

/** Tarjeta de capítulo amarilla (como "Paso 01 · Proyecto" de vd2): entra y sale por fundido. */
const Capitulo: React.FC<{ desde: number; hasta: number; chico: string; grande: string }> = ({ desde, hasta, chico, grande }) => {
  const f = useCurrentFrame();
  const o = interpolate(f, [c(desde), c(desde + 0.18), c(hasta - 0.18), c(hasta)], [0, 1, 1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const s = interpolate(f, [c(desde), c(hasta)], [1.04, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  if (f < c(desde) || f >= c(hasta)) return null;
  return (
    <AbsoluteFill style={{ background: ACENTO, opacity: o, alignItems: "center", justifyContent: "center", fontFamily: "Inter", color: CREMA }}>
      <div style={{ fontWeight: 700, fontSize: 30, letterSpacing: 6, opacity: 0.75 }}>{chico}</div>
      <div style={{ fontWeight: 900, fontStyle: "italic", fontSize: 190, lineHeight: 1.05, transform: `scale(${s})` }}>{grande}</div>
    </AbsoluteFill>
  );
};

const ClaseGratis: React.FC = () => {
  const f = useCurrentFrame();
  const pasos = interpolate(f, [c(20.45), c(20.9)], [0, 3], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const t = useSuave(17.2, 21.0, 0.15);
  const p = useSuave(17.2, 21.0, 0.3);
  return (
    <>
      {t.visible && (
        <div style={{ position: "absolute", top: 430, left: 160, width: 760, height: 428, ...vidrio, overflow: "hidden", display: "flex", alignItems: "center", justifyContent: "center", ...t.estilo }}>
          <Img src={staticFile("sebastian/avatar.jpg")} style={{ position: "absolute", width: 760, height: 428, objectFit: "cover", opacity: 0.5, filter: "blur(3px)" }} />
          <div style={{ position: "relative", width: 128, height: 128, borderRadius: 64, background: ACENTO, display: "flex", alignItems: "center", justifyContent: "center", boxShadow: "0 12px 30px rgba(200,85,61,0.35)" }}>
            <svg width="48" height="54" viewBox="0 0 46 52"><path d="M6 4 L42 26 L6 48 Z" fill={CREMA} /></svg>
          </div>
          <div style={{ position: "absolute", left: 26, bottom: 20, fontFamily: "Inter", fontWeight: 700, fontSize: 28, color: TEXTO }}>ya grabada</div>
        </div>
      )}
      {p.visible && (
        <div style={{ position: "absolute", top: 900, width: 1080, display: "flex", justifyContent: "center", gap: 22, fontFamily: "Inter", ...p.estilo }}>
          {[0, 1, 2].map((i) => (
            <div key={i} style={{ width: 220, height: 84, borderRadius: 42, display: "flex", alignItems: "center", justifyContent: "center", fontWeight: 900, fontStyle: "italic", fontSize: 38,
              ...(pasos > i ? { background: ACENTO, color: CREMA } : { ...vidrio, borderRadius: 42, color: TEXTO }) }}>PASO {i + 1}</div>
          ))}
        </div>
      )}
    </>
  );
};

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
      <Detras desde={10.3} hasta={13.7} x={170} y={620}><Reloj tam={250} /></Detras>
    </AbsoluteFill>
  ) : (
    <AbsoluteFill>
      {/* Arriba (video difuminado detrás). Nada que repita el subtítulo. */}
      <Titulo apoyo="día" clave="1" desde={22.62} hasta={24.3} tam={62} />
      <Perfil />
      <Comentario />
      {/* Pantallas completas (fondo difuminado) */}
      <ClaseGratis />
      <Contador />
      {/* Capítulo: el subtítulo "seguir estas" se va justo antes, así "3 COSAS" no sale dos veces */}
      <Capitulo desde={15.83} hasta={16.5} chico="" grande="3 COSAS" />
    </AbsoluteFill>
  );
