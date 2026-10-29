import React from "react";
import { AbsoluteFill, Easing, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";

// Prueba-01, versión "dynamic vd2/vd4" (pedido de Sebas: nada encima de la cara). Dos recursos:
//  - PANEL: baja desde arriba y cubre la mitad superior; el video baja y la cara queda en la mitad de abajo
//    (el corrimiento del video lo hace ffmpeg con los mismos tiempos: trabajo/capas.json).
//  - PANTALLA: cubre todo con fondo sólido; entra subiendo desde abajo y sale hacia arriba, como vd2.
// Tiempos en segundos de la base cortada (reels/prueba-01/trabajo/base_palabras.json).
export const FPS = 60;
export const DURACION_S = 36.0;
export const ALTO_PANEL = 860;
export const TRANSICION = 0.3;
const AMARILLO = "#FCF304";
const FONDO = "#0E0E10";

export const PANELES = [
  { id: "ig", desde: 1.2, hasta: 3.8 },
  { id: "reloj", desde: 10.45, hasta: 13.7 },
  { id: "perfil", desde: 22.62, hasta: 24.3 },
  { id: "comentario", desde: 29.85, hasta: 32.6 },
];
export const PANTALLAS = [
  { id: "tres", desde: 15.83, hasta: 16.5 },
  { id: "clase", desde: 17.2, hasta: 21.0 },
  { id: "contador", desde: 27.75, hasta: 29.75 },
];

const c = (s: number) => Math.round(s * FPS);
const SUAVE = Easing.bezier(0.65, 0, 0.35, 1);
const SALIDA = Easing.bezier(0.16, 1, 0.3, 1);

/** 0→1 al entrar y 1→0 al salir, con la curva de las cortinas. */
const useCortina = (desde: number, hasta: number) => {
  const f = useCurrentFrame();
  const entra = interpolate(f, [c(desde), c(desde + TRANSICION)], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: SUAVE });
  const sale = interpolate(f, [c(hasta - TRANSICION), c(hasta)], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: SUAVE });
  return { visible: f >= c(desde) && f < c(hasta), entra, sale };
};

/** Contenido que aparece con un resorte un poco después de que entra la cortina. */
const useAparece = (t: number) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  return spring({ frame: f - c(t), fps, config: { damping: 15, stiffness: 170 } });
};

const Panel: React.FC<{ desde: number; hasta: number; children: React.ReactNode }> = ({ desde, hasta, children }) => {
  const { visible, entra, sale } = useCortina(desde, hasta);
  if (!visible) return null;
  const y = -ALTO_PANEL * (1 - entra) - ALTO_PANEL * sale;
  return (
    <div style={{ position: "absolute", left: 0, top: y, width: 1080, height: ALTO_PANEL, background: `radial-gradient(120% 90% at 50% 30%, #1d1d21, ${FONDO})`, boxShadow: "0 18px 50px rgba(0,0,0,0.55)", overflow: "hidden" }}>
      {children}
    </div>
  );
};

const Pantalla: React.FC<{ desde: number; hasta: number; fondo?: string; children: React.ReactNode }> = ({ desde, hasta, fondo, children }) => {
  const { visible, entra, sale } = useCortina(desde, hasta);
  if (!visible) return null;
  const y = 1920 * (1 - entra) - 1920 * sale;
  return (
    <AbsoluteFill style={{ top: y, background: fondo ?? `radial-gradient(120% 70% at 50% 35%, #1d1d21, ${FONDO})` }}>{children}</AbsoluteFill>
  );
};

/** Título de pantalla: apoyo en Inter Bold blanca + clave en Inter Black Italic amarilla, en una línea. */
const Titulo: React.FC<{ apoyo: string; clave: string; y: number; t: number }> = ({ apoyo, clave, y, t }) => {
  const s = useAparece(t);
  return (
    <div style={{ position: "absolute", top: y, width: 1080, textAlign: "center", fontFamily: "Inter", opacity: s, transform: `translateY(${(1 - s) * 30}px)` }}>
      <span style={{ fontWeight: 700, fontSize: 64, color: "#fff" }}>{apoyo} </span>
      <span style={{ fontWeight: 900, fontStyle: "italic", fontSize: 80, color: AMARILLO }}>{clave}</span>
    </div>
  );
};

const LogoInstagram: React.FC = () => {
  const s = useAparece(1.45);
  return (
    <div style={{ position: "absolute", top: 250, width: 1080, display: "flex", justifyContent: "center", transform: `scale(${0.6 + 0.4 * s}) rotate(${(1 - s) * -12}deg)`, opacity: s }}>
      <svg width={360} height={360} viewBox="0 0 100 100" style={{ filter: "drop-shadow(0 20px 50px rgba(214,36,159,0.45))" }}>
        <defs>
          <radialGradient id="ig2" cx="30%" cy="107%" r="150%">
            <stop offset="0%" stopColor="#fdf497" /><stop offset="10%" stopColor="#fdf497" /><stop offset="50%" stopColor="#fd5949" />
            <stop offset="68%" stopColor="#d6249f" /><stop offset="100%" stopColor="#285AEB" />
          </radialGradient>
        </defs>
        <rect x="4" y="4" width="92" height="92" rx="26" fill="url(#ig2)" />
        <rect x="24" y="24" width="52" height="52" rx="16" fill="none" stroke="#fff" strokeWidth="7" />
        <circle cx="50" cy="50" r="12" fill="none" stroke="#fff" strokeWidth="7" />
        <circle cx="68" cy="32" r="4.5" fill="#fff" />
      </svg>
    </div>
  );
};

const RelojDeArena: React.FC = () => {
  const f = useCurrentFrame();
  const s = useAparece(10.6);
  const p = interpolate(f, [c(10.7), c(13.4)], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <div style={{ position: "absolute", top: 240, width: 1080, display: "flex", justifyContent: "center", opacity: s, transform: `scale(${0.7 + 0.3 * s})` }}>
      <svg width={300} height={410} viewBox="0 0 100 136" style={{ filter: "drop-shadow(0 0 30px rgba(252,243,4,0.25))" }}>
        <rect x="8" y="2" width="84" height="10" rx="5" fill="#fff" />
        <rect x="8" y="124" width="84" height="10" rx="5" fill="#fff" />
        <path d="M18 12 C18 48 46 58 46 68 C46 78 18 88 18 124 L82 124 C82 88 54 78 54 68 C54 58 82 48 82 12 Z" fill="rgba(255,255,255,0.08)" stroke="#fff" strokeWidth="3.5" />
        <clipPath id="arriba2"><rect x="0" y={12 + 46 * p} width="100" height={56 - 46 * p} /></clipPath>
        <path d="M22 16 C22 46 47 56 48 66 L52 66 C53 56 78 46 78 16 Z" fill={AMARILLO} clipPath="url(#arriba2)" />
        <rect x="48.5" y="66" width="3" height={58 - 40 * p} fill={AMARILLO} opacity={p < 0.98 ? 1 : 0} />
        <path d={`M22 121 C24 ${121 - 34 * p} 76 ${121 - 34 * p} 78 121 Z`} fill={AMARILLO} />
      </svg>
    </div>
  );
};

/** Tarjeta de capítulo amarilla a pantalla completa, como "Paso 1 · Proyecto" de vd2. */
const TresCosas: React.FC = () => {
  const s = useAparece(15.88);
  return (
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", fontFamily: "Inter", color: "#111" }}>
      <div style={{ fontWeight: 700, fontSize: 52, opacity: 0.75 * s }}>solo tienes que seguir</div>
      <div style={{ fontWeight: 900, fontStyle: "italic", fontSize: 230, lineHeight: 1, transform: `scale(${0.85 + 0.15 * s})`, opacity: s }}>3 COSAS</div>
    </AbsoluteFill>
  );
};

const ClaseGratis: React.FC = () => {
  const f = useCurrentFrame();
  const s = useAparece(17.4);
  const pasos = interpolate(f, [c(20.45), c(20.9)], [0, 3], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <AbsoluteFill style={{ fontFamily: "Inter", color: "#fff" }}>
      <Titulo apoyo="una" clave="CLASE GRATIS" y={360} t={17.3} />
      <div style={{ position: "absolute", top: 520, left: 140, width: 800, height: 450, borderRadius: 36, overflow: "hidden", opacity: s, transform: `translateY(${(1 - s) * 60}px)`,
        background: "linear-gradient(150deg,#2a2a30,#111114)", border: "2px solid rgba(255,255,255,0.14)", boxShadow: "0 30px 70px rgba(0,0,0,0.6)", display: "flex", alignItems: "center", justifyContent: "center" }}>
        <Img src={staticFile("sebastian/avatar.jpg")} style={{ position: "absolute", width: 800, height: 450, objectFit: "cover", opacity: 0.35, filter: "blur(2px)" }} />
        <div style={{ position: "relative", width: 150, height: 150, borderRadius: 75, background: AMARILLO, display: "flex", alignItems: "center", justifyContent: "center", boxShadow: `0 0 50px ${AMARILLO}66` }}>
          <svg width="56" height="64" viewBox="0 0 46 52"><path d="M6 4 L42 26 L6 48 Z" fill="#111" /></svg>
        </div>
        <div style={{ position: "absolute", left: 28, bottom: 22, fontWeight: 700, fontSize: 30, opacity: 0.85 }}>ya grabada</div>
      </div>
      <div style={{ position: "absolute", top: 1030, width: 1080, display: "flex", justifyContent: "center", gap: 26 }}>
        {[0, 1, 2].map((i) => (
          <div key={i} style={{ width: 230, height: 96, borderRadius: 48, display: "flex", alignItems: "center", justifyContent: "center", fontWeight: 900, fontStyle: "italic", fontSize: 44,
            background: pasos > i ? AMARILLO : "rgba(255,255,255,0.10)", color: pasos > i ? "#111" : "rgba(255,255,255,0.75)", transform: `scale(${pasos > i ? 1.04 : 1})` }}>PASO {i + 1}</div>
        ))}
      </div>
    </AbsoluteFill>
  );
};

/** La captura real (23 seguidores), limpia como en la v1, dentro del panel de arriba. */
const Perfil: React.FC = () => {
  const f = useCurrentFrame();
  const s = useAparece(22.8);
  const W = 860, escala = W / 1179;
  const marca = interpolate(f, [c(23.42), c(23.77)], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: SALIDA });
  return (
    <div style={{ position: "absolute", top: 250, left: (1080 - W) / 2, opacity: s, transform: `translateY(${(1 - s) * 40}px)` }}>
      <div style={{ position: "relative", width: W, height: 780 * escala, borderRadius: 34, overflow: "hidden", border: "3px solid rgba(255,255,255,0.9)", boxShadow: "0 24px 60px rgba(0,0,0,0.5)" }}>
        <Img src={staticFile("sebastian/perfil_23c.png")} style={{ width: W, display: "block" }} />
        <div style={{ position: "absolute", left: 630 * escala, top: 300 * escala, width: 250 * escala, height: 130 * escala, border: `6px solid ${AMARILLO}`, borderRadius: 22,
          opacity: marca, transform: `scale(${1.4 - 0.4 * marca})`, boxShadow: `0 0 30px ${AMARILLO}` }} />
      </div>
    </div>
  );
};

const Contador: React.FC = () => {
  const f = useCurrentFrame();
  const s = useAparece(27.9);
  const p = interpolate(f, [c(28.05), c(29.25)], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.bezier(0.7, 0, 0.2, 1) });
  const n = Math.round(23 + (10000 - 23) * p);
  const W = 860, H = 420;
  const pts = Array.from({ length: 61 }, (_, i) => i / 60).filter((x) => x <= p + 1e-6)
    .map((x) => `${(x * W).toFixed(1)},${(H - 10 - (H - 30) * Math.pow(x, 2.6)).toFixed(1)}`);
  return (
    <AbsoluteFill style={{ fontFamily: "Inter", color: "#fff", opacity: s }}>
      <div style={{ position: "absolute", top: 330, width: 1080, textAlign: "center", fontWeight: 700, fontSize: 52, opacity: 0.8 }}>seguidores</div>
      <div style={{ position: "absolute", top: 400, width: 1080, textAlign: "center", fontWeight: 900, fontStyle: "italic", fontSize: 220, lineHeight: 1, color: p >= 1 ? AMARILLO : "#fff" }}>
        {n.toLocaleString("es-VE")}
      </div>
      <svg width={W} height={H} style={{ position: "absolute", top: 690, left: (1080 - W) / 2, overflow: "visible" }}>
        <line x1="0" y1={H - 10} x2={W} y2={H - 10} stroke="rgba(255,255,255,0.22)" strokeWidth="3" strokeDasharray="8 10" />
        <line x1="0" y1="20" x2={W} y2="20" stroke="rgba(255,255,255,0.22)" strokeWidth="3" strokeDasharray="8 10" />
        <text x="0" y={H + 44} fill="rgba(255,255,255,0.7)" fontFamily="Inter" fontWeight="700" fontSize="34">hoy: 23</text>
        <text x={W} y="0" textAnchor="end" fill={AMARILLO} fontFamily="Inter" fontWeight="900" fontStyle="italic" fontSize="40">META 10K</text>
        <polyline points={pts.join(" ")} fill="none" stroke={AMARILLO} strokeWidth="10" strokeLinecap="round" strokeLinejoin="round" style={{ filter: `drop-shadow(0 0 14px ${AMARILLO})` }} />
      </svg>
    </AbsoluteFill>
  );
};

const Comentario: React.FC = () => {
  const f = useCurrentFrame();
  const s = useAparece(30.0);
  const letras = Math.floor(interpolate(f, [c(30.55), c(31.0)], [0, 5], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }));
  const enviado = interpolate(f, [c(31.2), c(31.4)], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const cursor = Math.floor(f / 18) % 2 === 0 && letras < 5;
  return (
    <div style={{ position: "absolute", top: 300, left: 90, width: 900, opacity: s, transform: `translateY(${(1 - s) * 40}px)`, fontFamily: "Inter" }}>
      <div style={{ color: "#fff", fontWeight: 700, fontSize: 46, marginBottom: 26, textAlign: "center" }}>comenta la palabra</div>
      <div style={{ display: "flex", alignItems: "center", gap: 24, padding: "26px 30px", borderRadius: 70, background: "rgba(255,255,255,0.97)", boxShadow: "0 24px 60px rgba(0,0,0,0.5)" }}>
        <Img src={staticFile("sebastian/avatar.jpg")} style={{ width: 100, height: 100, borderRadius: 50, objectFit: "cover" }} />
        <div style={{ flex: 1, fontSize: 64, fontWeight: 900, fontStyle: "italic", color: "#111" }}>
          {"RELOJ".slice(0, letras)}{cursor ? "|" : ""}
          {letras === 0 && <span style={{ fontStyle: "normal", fontWeight: 600, fontSize: 40, color: "#999" }}>Añade un comentario…</span>}
        </div>
        <div style={{ width: 100, height: 100, borderRadius: 50, background: enviado > 0.5 ? AMARILLO : "#3897f0", display: "flex", alignItems: "center", justifyContent: "center", transform: `scale(${1 + 0.25 * Math.sin(enviado * Math.PI)})` }}>
          <svg width="48" height="48" viewBox="0 0 24 24"><path d="M3 11l18-8-8 18-2-8z" fill={enviado > 0.5 ? "#111" : "#fff"} /></svg>
        </div>
      </div>
    </div>
  );
};

const CONTENIDO: Record<string, React.FC> = {
  ig: LogoInstagram, reloj: RelojDeArena, perfil: Perfil, comentario: Comentario,
  tres: TresCosas, clase: ClaseGratis, contador: Contador,
};

export const Prueba01b: React.FC = () => (
  <AbsoluteFill>
    {PANELES.map((p) => {
      const C = CONTENIDO[p.id];
      return <Panel key={p.id} desde={p.desde} hasta={p.hasta}><C /></Panel>;
    })}
    {PANTALLAS.map((p) => {
      const C = CONTENIDO[p.id];
      return <Pantalla key={p.id} desde={p.desde} hasta={p.hasta} fondo={p.id === "tres" ? AMARILLO : undefined}><C /></Pantalla>;
    })}
  </AbsoluteFill>
);
