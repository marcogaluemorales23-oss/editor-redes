import React from "react";
import { interpolate, useCurrentFrame, useVideoConfig } from "remotion";

// Subtítulos del formato dynamic de Sebas (marcas/sebastian/formato-dynamic.md):
// bloques de 1 a 3 pisos que se apilan con la voz, tamaño según importancia, color según significado,
// entrada deslizando de lado con desenfoque de movimiento y salida borrosa. Sin caja; resplandor oscuro difuso.

export type Piso = {
  texto: string;
  t: number;
  tam: "s" | "m" | "l" | "xl";
  color?: "blanco" | "amarillo" | "claude" | "rojo" | "naranja" | "lima" | "verde" | "negro";
  it?: boolean;
  caja?: boolean;
  en_linea?: boolean;
  progresivo?: boolean;
  tiempos?: number[];
  tachar?: boolean;
  caja_fondo?: string;
};
export type Bloque = { zona: "arriba" | "centro" | "cta"; t0: number; t1: number; pisos: Piso[]; centro?: number };

// Color de la palabra clave según la acción (flujo de Sebas): verde = dinero o ganar algo, rojo = perder dinero o
// error, el resto amarillo o "claude" (el naranja de Claude).
export const COLORES = {
  blanco: "#FFFFFF", amarillo: "#FCF304", claude: "#D97757", rojo: "#FF4D6D", naranja: "#FFA41B", lima: "#D4F53C", verde: "#2BFF5C", negro: "#141414",
};
const TAM = { s: 50, m: 68, l: 96, xl: 140 };
const PESO = { s: 500, m: 600, l: 700, xl: 700 };
export const RESPLANDOR = "0 0 44px rgba(0,0,0,0.5), 0 0 16px rgba(0,0,0,0.32), 0 4px 12px rgba(0,0,0,0.28)";
// Para palabras de color sobre ropa o fondos del mismo tono (camisa vino tinto de Andy): halo oscuro más denso y
// pegado, que separa la letra del fondo sin llegar a ser un contorno.
export const RESPLANDOR_FUERTE = "0 0 10px rgba(0,0,0,0.85), 0 0 22px rgba(0,0,0,0.7), 0 0 48px rgba(0,0,0,0.55), 0 4px 10px rgba(0,0,0,0.5)";
// Suave y fluido (Sebas: "animado, pero no tan brusco, más suavecito"): ~0,3 s de entrada, ~0,25 s de salida.
const ENTRA = 7; // cuadros
const SALE = 6;

// Centro del bloque (zona centro): debajo de las barbillas en las tomas de Sunny Shore, sobre el pecho.
const ZONAS = { arriba: { top: 370 }, centro: { centro: 1000 }, cta: { top: 285 } };
const ANCHO_MAX = { arriba: 860, centro: 760, cta: 860 };

const ancho = (p: Piso, px: number) => {
  const mayus = p.texto === p.texto.toUpperCase() && /[A-Z]/.test(p.texto);
  const k = (p.tam === "xl" && p.it ? 0.6 : PESO[p.tam] >= 700 ? 0.57 : 0.54) * (mayus ? 1.18 : 1);
  return p.texto.length * px * k + (p.caja ? px * 0.5 : 0);
};

/** Pisos agrupados en líneas ("en_linea" se pega al anterior) con su escala para no pasarse del ancho. */
const lineas = (b: Bloque) => {
  const ls: { pisos: { p: Piso; i: number }[]; escala: number; alto: number }[] = [];
  b.pisos.forEach((p, i) => {
    if (p.en_linea && ls.length) ls[ls.length - 1].pisos.push({ p, i });
    else ls.push({ pisos: [{ p, i }], escala: 1, alto: 0 });
  });
  for (const l of ls) {
    const total = l.pisos.reduce((s, { p }) => s + ancho(p, TAM[p.tam]) + 14, -14);
    l.escala = Math.min(1, ANCHO_MAX[b.zona] / total);
    l.alto = Math.max(...l.pisos.map(({ p }) => TAM[p.tam] * (p.caja ? 1.25 : 0.98))) * l.escala;
  }
  return ls;
};

/** Palabra negada: entra entera, una línea la tacha de izquierda a derecha y la parte en dos mitades que se separan. */
const Tachada: React.FC<{ texto: string; px: number; t: number }> = ({ texto, px, t }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const c = (s: number) => Math.round(s * fps);
  const facil = (x: number) => 1 - Math.pow(1 - x, 3);
  const linea = facil(interpolate(f, [c(t + 0.18), c(t + 0.38)], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }));
  const corte = facil(interpolate(f, [c(t + 0.34), c(t + 0.58)], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }));
  const mitad = (arriba: boolean): React.CSSProperties => ({
    position: "absolute", left: 0, top: 0, clipPath: arriba ? "inset(-20% -5% 50% -5%)" : "inset(50% -5% -20% -5%)",
    transform: `translate(${(arriba ? -1 : 1) * 12 * corte}px, ${(arriba ? -1 : 1) * 9 * corte}px) rotate(${(arriba ? -1 : 1) * 1.5 * corte}deg)`,
  });
  return (
    <span style={{ position: "relative", display: "inline-block" }}>
      <span style={{ visibility: "hidden" }}>{texto}</span>
      <span style={mitad(true)}>{texto}</span>
      <span style={mitad(false)}>{texto}</span>
      <span style={{ position: "absolute", left: -px * 0.06, top: "52%", height: Math.max(6, px * 0.085), width: `${linea * 112}%`,
        background: "#FFFFFF", borderRadius: 4, transform: "translateY(-50%) rotate(-4deg)", transformOrigin: "left center",
        boxShadow: "0 0 14px rgba(0,0,0,0.6)" }} />
    </span>
  );
};

const PisoVista: React.FC<{ p: Piso; px: number; id: string; salida: number; contraste?: boolean }> = ({ p, px, id, salida, contraste }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const c = (s: number) => Math.round(s * fps);
  // Antes de su palabra el piso ya ocupa su lugar (transparente): así lo que ya está no se corre cuando entra.
  const e = interpolate(f, [c(p.t), c(p.t) + ENTRA], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const facil = 1 - Math.pow(1 - e, 3);
  const mancha = (1 - facil) * 16; // desenfoque horizontal de la entrada
  const palabras = p.texto.split(" ");
  // "progresivo": cada palabra aparece (con fundido corto) cuando se dice; las que faltan guardan su lugar.
  const alfa = (k: number) => !p.progresivo || !p.tiempos ? 1
    : interpolate(f, [c(p.tiempos[Math.min(k, p.tiempos.length - 1)]), c(p.tiempos[Math.min(k, p.tiempos.length - 1)]) + 4], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const color = COLORES[p.color ?? "blanco"];
  const oscuro = p.color === "negro";
  return (
    <>
      <svg width="0" height="0" style={{ position: "absolute" }}>
        <filter id={id} x="-30%" y="-30%" width="160%" height="160%">
          <feGaussianBlur stdDeviation={`${mancha.toFixed(2)} ${(salida * 10).toFixed(2)}`} />
        </filter>
      </svg>
      <span style={{
        display: "inline-block", fontFamily: "Inter", fontSize: px, lineHeight: 1, whiteSpace: "nowrap",
        fontWeight: p.tam === "xl" && p.it ? 900 : PESO[p.tam], fontStyle: p.it ? "italic" : "normal", color,
        letterSpacing: -px * 0.025, textShadow: p.caja ? "none" : oscuro ? "0 0 30px rgba(255,255,255,0.55)"
          : contraste && p.color && p.color !== "blanco" ? RESPLANDOR_FUERTE : RESPLANDOR,
        background: p.caja ? p.caja_fondo ?? "rgba(52,52,52,0.92)" : undefined, padding: p.caja ? `${px * 0.1}px ${px * 0.22}px ${px * 0.02}px` : undefined,
        transform: `translateX(${(1 - facil) * -45}px)`, opacity: Math.min(1, e * 1.4) * (1 - salida),
        filter: mancha > 0.05 || salida > 0 ? `url(#${id}) blur(${salida * 5}px)` : undefined,
      }}>
        {p.tachar ? <Tachada texto={p.texto} px={px} t={p.t} /> :
          palabras.map((w, k) => <span key={k} style={{ opacity: alfa(k) }}>{w}{k < palabras.length - 1 ? " " : ""}</span>)}
      </span>
    </>
  );
};

const BloqueVista: React.FC<{ b: Bloque; n: number; contraste?: boolean }> = ({ b, n, contraste }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const c = (s: number) => Math.round(s * fps);
  if (f < c(b.t0) || f >= c(b.t1)) return null;
  const salida = interpolate(f, [c(b.t1) - SALE, c(b.t1)], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const ls = lineas(b);
  const alto = ls.reduce((s, l) => s + l.alto, 0);
  const zona = ZONAS[b.zona];
  const top = b.centro !== undefined ? b.centro - alto / 2 : "centro" in zona ? zona.centro - alto / 2 : zona.top;
  return (
    <div style={{ position: "absolute", left: 0, width: 1080, top, display: "flex", flexDirection: "column", alignItems: "center" }}>
      {ls.map((l, k) => (
        <div key={k} style={{ height: l.alto, display: "flex", alignItems: "baseline", justifyContent: "center", gap: 14 * l.escala }}>
          {l.pisos.map(({ p, i }) => <PisoVista key={i} p={p} px={TAM[p.tam] * l.escala} id={`mb-${n}-${i}`} salida={salida} contraste={contraste} />)}
        </div>
      ))}
    </div>
  );
};

/** contraste: halo más fuerte en las palabras de color (cuando el fondo o la ropa es del mismo tono). */
export const Textos: React.FC<{ bloques: Bloque[]; contraste?: boolean }> = ({ bloques, contraste }) => (
  <>{bloques.map((b, n) => <BloqueVista key={n} b={b} n={n} contraste={contraste} />)}</>
);
