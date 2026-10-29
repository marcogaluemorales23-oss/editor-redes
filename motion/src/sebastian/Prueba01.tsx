import { loadFont } from "@remotion/fonts";
import React from "react";
import { AbsoluteFill, Easing, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";

// Gráficos de la prueba-01 de Sebastián (formato dynamic). Tiempos en segundos de la base cortada
// (reels/prueba-01/trabajo/corte_check.json). Todo flota ARRIBA de la cabeza (y < 700): la cara (y≈930) y
// los subtítulos (y≈1250-1360) quedan libres. Zona segura de arriba: nada antes de y=245.
export const FPS = 60;
export const DURACION_S = 36.0;
const AMARILLO = "#FCF304";

export const cargarFuentesSebastian = () =>
  Promise.all([
    loadFont({ family: "Inter", url: staticFile("fuentes/Inter-SemiBold.ttf"), weight: "600" }),
    loadFont({ family: "Inter", url: staticFile("fuentes/Inter-Bold.ttf"), weight: "700" }),
    loadFont({ family: "Inter", url: staticFile("fuentes/Inter-BlackItalic.ttf"), weight: "900", style: "italic" }),
  ]);

const c = (s: number) => Math.round(s * FPS);
const SUAVE = Easing.bezier(0.16, 1, 0.3, 1);

/** Visible entre desde y hasta; entra con resorte (escala + subida) y sale con fundido y desenfoque. */
const useFlotante = (desde: number, hasta: number) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const visible = f >= c(desde) && f < c(hasta);
  const entra = spring({ frame: f - c(desde), fps, config: { damping: 14, stiffness: 180 } });
  const sale = interpolate(f, [c(hasta) - 8, c(hasta)], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return {
    visible,
    estilo: {
      opacity: Math.min(1, entra * 1.4) * sale,
      transform: `translateY(${(1 - entra) * 60}px) scale(${0.85 + 0.15 * entra})`,
      filter: `blur(${(1 - sale) * 10}px)`,
    } as React.CSSProperties,
  };
};

const sombra = "0 24px 60px rgba(0,0,0,0.45)";

const Caja: React.FC<{ y: number; children: React.ReactNode; estilo: React.CSSProperties }> = ({ y, children, estilo }) => (
  <div style={{ position: "absolute", left: 0, width: 1080, top: y, display: "flex", justifyContent: "center", ...estilo }}>
    {children}
  </div>
);

const LogoInstagram: React.FC = () => {
  const { visible, estilo } = useFlotante(1.5, 3.8);
  if (!visible) return null;
  return (
    <Caja y={262} estilo={estilo}>
      <svg width={190} height={190} viewBox="0 0 100 100" style={{ filter: "drop-shadow(0 18px 40px rgba(0,0,0,0.45))" }}>
        <defs>
          <radialGradient id="ig" cx="30%" cy="107%" r="150%">
            <stop offset="0%" stopColor="#fdf497" />
            <stop offset="10%" stopColor="#fdf497" />
            <stop offset="50%" stopColor="#fd5949" />
            <stop offset="68%" stopColor="#d6249f" />
            <stop offset="100%" stopColor="#285AEB" />
          </radialGradient>
        </defs>
        <rect x="4" y="4" width="92" height="92" rx="26" fill="url(#ig)" />
        <rect x="24" y="24" width="52" height="52" rx="16" fill="none" stroke="#fff" strokeWidth="7" />
        <circle cx="50" cy="50" r="12" fill="none" stroke="#fff" strokeWidth="7" />
        <circle cx="68" cy="32" r="4.5" fill="#fff" />
      </svg>
    </Caja>
  );
};

/** Reloj de arena que se vacía: "quemando tu tiempo". */
const RelojDeArena: React.FC = () => {
  const f = useCurrentFrame();
  const { visible, estilo } = useFlotante(10.45, 13.7);
  if (!visible) return null;
  const p = interpolate(f, [c(10.55), c(13.4)], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const giro = interpolate(f, [c(10.45), c(10.85)], [-20, 0], { extrapolateRight: "clamp", easing: SUAVE });
  return (
    <Caja y={255} estilo={estilo}>
      <svg width={170} height={232} viewBox="0 0 100 136" style={{ transform: `rotate(${giro}deg)`, filter: "drop-shadow(0 18px 40px rgba(0,0,0,0.5))" }}>
        <rect x="8" y="2" width="84" height="10" rx="5" fill="#fff" />
        <rect x="8" y="124" width="84" height="10" rx="5" fill="#fff" />
        <path d="M18 12 C18 48 46 58 46 68 C46 78 18 88 18 124 L82 124 C82 88 54 78 54 68 C54 58 82 48 82 12 Z"
          fill="rgba(255,255,255,0.16)" stroke="#fff" strokeWidth="4" />
        {/* arena de arriba (baja) */}
        <clipPath id="arriba"><rect x="0" y={12 + 46 * p} width="100" height={56 - 46 * p} /></clipPath>
        <path d="M22 16 C22 46 47 56 48 66 L52 66 C53 56 78 46 78 16 Z" fill={AMARILLO} clipPath="url(#arriba)" />
        {/* chorro */}
        <rect x="48.5" y="66" width="3" height={58 - 40 * p} fill={AMARILLO} opacity={p < 0.98 ? 1 : 0} />
        {/* arena de abajo (sube) */}
        <path d={`M22 121 C24 ${121 - 34 * p} 76 ${121 - 34 * p} 78 121 Z`} fill={AMARILLO} />
      </svg>
    </Caja>
  );
};

/** 1 · 2 · 3 que aparecen en "estas tres cosas". */
const TresCosas: React.FC = () => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const { visible, estilo } = useFlotante(15.83, 16.45);
  if (!visible) return null;
  return (
    <Caja y={330} estilo={estilo}>
      <div style={{ display: "flex", gap: 40 }}>
        {[1, 2, 3].map((n, i) => {
          const s = spring({ frame: f - c(15.83) - i * 5, fps, config: { damping: 12, stiffness: 220 } });
          return (
            <div key={n} style={{
              width: 170, height: 170, borderRadius: 85, background: n === 3 ? AMARILLO : "rgba(20,20,20,0.82)",
              border: "4px solid rgba(255,255,255,0.9)", display: "flex", alignItems: "center", justifyContent: "center",
              fontFamily: "Inter", fontWeight: 900, fontStyle: "italic", fontSize: 110,
              color: n === 3 ? "#111" : "#fff", transform: `scale(${s})`, boxShadow: sombra,
            }}>{n}</div>
          );
        })}
      </div>
    </Caja>
  );
};

const punteado: React.CSSProperties = {
  background: "rgba(12,12,14,0.74)",
  border: "3px dashed rgba(255,255,255,0.92)",
  boxShadow: "0 0 22px rgba(255,255,255,0.35), 0 24px 60px rgba(0,0,0,0.45)",
  borderRadius: 34,
};

/** Clase gratis: miniatura de video con play + título, en tarjeta punteada (estilo dynamic vd5). */
const ClaseGratis: React.FC = () => {
  const f = useCurrentFrame();
  const { visible, estilo } = useFlotante(17.2, 22.7);
  if (!visible) return null;
  const pasos = interpolate(f, [c(20.45), c(20.9)], [0, 3], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <Caja y={258} estilo={estilo}>
      <div style={{ ...punteado, width: 600, padding: 22, display: "flex", gap: 22, alignItems: "center", fontFamily: "Inter", color: "#fff" }}>
        <div style={{ width: 150, height: 200, borderRadius: 22, background: "linear-gradient(160deg,#2a2a2e,#111)", border: "2px solid rgba(255,255,255,0.25)", display: "flex", alignItems: "center", justifyContent: "center" }}>
          <div style={{ width: 72, height: 72, borderRadius: 36, background: AMARILLO, display: "flex", alignItems: "center", justifyContent: "center" }}>
            <svg width="30" height="34" viewBox="0 0 46 52"><path d="M6 4 L42 26 L6 48 Z" fill="#111" /></svg>
          </div>
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ fontWeight: 900, fontStyle: "italic", fontSize: 54, lineHeight: 1 }}>CLASE<br />GRATIS</div>
          <div style={{ display: "flex", gap: 10, marginTop: 18 }}>
            {[0, 1, 2].map((i) => (
              <div key={i} style={{ width: 54, height: 54, borderRadius: 27, display: "flex", alignItems: "center", justifyContent: "center", fontWeight: 900, fontStyle: "italic", fontSize: 30,
                background: pasos > i ? AMARILLO : "rgba(255,255,255,0.14)", color: pasos > i ? "#111" : "#fff" }}>{i + 1}</div>
            ))}
            <div style={{ alignSelf: "center", fontWeight: 600, fontSize: 26, opacity: 0.75, marginLeft: 4 }}>pasos</div>
          </div>
        </div>
      </div>
    </Caja>
  );
};

/** Captura real del perfil con 23 seguidores, como en la v1 (borde blanco limpio, sin punteado), más chica y abajo
 * sobre el pecho: no tapa la cara. Mientras se ve, los subtítulos suben arriba de la cabeza (subtitulos.json). */
const Perfil: React.FC = () => {
  const f = useCurrentFrame();
  const { visible, estilo } = useFlotante(22.93, 26.5);
  if (!visible) return null;
  const W = 520, escala = W / 1179;
  const marca = interpolate(f, [c(23.42), c(23.77)], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: SUAVE });
  return (
    <Caja y={1240} estilo={{ ...estilo, transform: `${estilo.transform} rotate(-2deg)` }}>
      <div style={{ position: "relative", width: W, height: 780 * escala, borderRadius: 30, overflow: "hidden", boxShadow: sombra, border: "3px solid rgba(255,255,255,0.9)" }}>
        <Img src={staticFile("sebastian/perfil_23c.png")} style={{ width: W, display: "block" }} />
        <div style={{
          position: "absolute", left: 630 * escala, top: 300 * escala, width: 250 * escala, height: 130 * escala,
          border: `5px solid ${AMARILLO}`, borderRadius: 18, opacity: marca, transform: `scale(${1.4 - 0.4 * marca})`,
          boxShadow: `0 0 26px ${AMARILLO}`,
        }} />
      </div>
    </Caja>
  );
};

/** De 23 a 10K: curva que crece con brillo amarillo y número grande (como la curva de retención de vd5). */
const Contador: React.FC = () => {
  const f = useCurrentFrame();
  const { visible, estilo } = useFlotante(26.5, 29.6);
  if (!visible) return null;
  const p = interpolate(f, [c(27.8), c(29.0)], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.bezier(0.7, 0, 0.2, 1) });
  const n = Math.round(23 + (10000 - 23) * p);
  const W = 560, H = 170;
  // curva exponencial de 23 a 10K, se dibuja hasta p
  const pts = Array.from({ length: 41 }, (_, i) => i / 40).filter((x) => x <= p + 1e-6)
    .map((x) => `${(x * W).toFixed(1)},${(H - 8 - (H - 20) * Math.pow(x, 2.6)).toFixed(1)}`);
  return (
    <Caja y={262} estilo={estilo}>
      <div style={{ ...punteado, width: 600, padding: "20px 20px 16px", fontFamily: "Inter", color: "#fff" }}>
        <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between" }}>
          <div style={{ fontWeight: 900, fontStyle: "italic", fontSize: 76, lineHeight: 1, color: p >= 1 ? AMARILLO : "#fff" }}>{n.toLocaleString("es-VE")}</div>
          <div style={{ fontWeight: 600, fontSize: 26, opacity: 0.75 }}>seguidores</div>
        </div>
        <svg width={W} height={H} style={{ marginTop: 6, overflow: "visible" }}>
          <line x1="0" y1={H - 8} x2={W} y2={H - 8} stroke="rgba(255,255,255,0.25)" strokeWidth="2" strokeDasharray="6 8" />
          <line x1="0" y1="12" x2={W} y2="12" stroke="rgba(255,255,255,0.25)" strokeWidth="2" strokeDasharray="6 8" />
          <text x={W} y={H - 20} textAnchor="end" fill="rgba(255,255,255,0.7)" fontFamily="Inter" fontWeight="700" fontSize="22">meta 10K</text>
          <polyline points={pts.join(" ")} fill="none" stroke={AMARILLO} strokeWidth="7" strokeLinecap="round" strokeLinejoin="round"
            style={{ filter: `drop-shadow(0 0 10px ${AMARILLO})` }} />
        </svg>
      </div>
    </Caja>
  );
};

/** Caja de comentario que escribe RELOJ y se envía. */
const Comentario: React.FC = () => {
  const f = useCurrentFrame();
  const { visible, estilo } = useFlotante(29.85, 36.0);
  if (!visible) return null;
  const letras = Math.floor(interpolate(f, [c(30.42), c(30.9)], [0, 5], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }));
  const enviado = interpolate(f, [c(31.2), c(31.4)], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const cursor = Math.floor(f / 18) % 2 === 0 && letras < 5;
  return (
    <Caja y={330} estilo={estilo}>
      <div style={{ width: 820, display: "flex", alignItems: "center", gap: 22, padding: "22px 26px", borderRadius: 60, background: "rgba(255,255,255,0.96)", boxShadow: sombra, fontFamily: "Inter" }}>
        <Img src={staticFile("sebastian/avatar.jpg")} style={{ width: 92, height: 92, borderRadius: 46, objectFit: "cover" }} />
        <div style={{ flex: 1, fontSize: 52, fontWeight: 900, fontStyle: "italic", color: "#111", letterSpacing: 1 }}>
          {"RELOJ".slice(0, letras)}{cursor ? "|" : ""}
          {letras === 0 && <span style={{ fontStyle: "normal", fontWeight: 600, fontSize: 36, color: "#999" }}>Añade un comentario…</span>}
        </div>
        <div style={{ width: 92, height: 92, borderRadius: 46, background: enviado > 0.5 ? AMARILLO : "#3897f0", display: "flex", alignItems: "center", justifyContent: "center", transform: `scale(${1 + 0.25 * Math.sin(enviado * Math.PI)})` }}>
          <svg width="44" height="44" viewBox="0 0 24 24"><path d="M3 11l18-8-8 18-2-8z" fill={enviado > 0.5 ? "#111" : "#fff"} /></svg>
        </div>
      </div>
    </Caja>
  );
};

export const Prueba01: React.FC = () => (
  <AbsoluteFill>
    <LogoInstagram />
    <RelojDeArena />
    <TresCosas />
    <ClaseGratis />
    <Perfil />
    <Contador />
    <Comentario />
  </AbsoluteFill>
);
