import React from "react";
import { AbsoluteFill, Easing, interpolate, useCurrentFrame } from "remotion";
import { COLORES, RESPLANDOR, Textos } from "../dynamic/Textos";
import { BLOQUES } from "../generado/andy.gen";

// Andy (VisualPRO Marketing), formato dynamic de Sebas. Fondo de estudio gris oscuro: los textos grandes van DETRÁS
// de Andy (capa "detras", debajo del recorte de nucleo/silueta.py); subtítulos y gráficos en la capa "frente".
// Zonas: la cara ocupa y≈450–700, los subtítulos el pecho (y≈1000) y los gráficos la parte de abajo (y≈1150–1580).
export const FPS = 24000 / 1001;
export const DURACION_S = 57.77;
const c = (s: number) => Math.round(s * FPS);
const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const SUAVE = Easing.bezier(0.22, 1, 0.36, 1);
const { amarillo: AMARILLO, claude: CLAUDE, rojo: ROJO } = COLORES;
const ROJO_MARCA = "#E3262E";

/** Entrada (0..1) y salida (0..1) suaves: ~0,3 s y ~0,25 s, sin rebotes (regla de Sebas). */
const vida = (f: number, desde: number, hasta: number, entra = 0.3, sale = 0.25) => ({
  p: interpolate(f, [c(desde), c(desde + entra)], [0, 1], { ...clamp, easing: SUAVE }),
  q: interpolate(f, [c(hasta - sale), c(hasta)], [0, 1], clamp),
  visible: f >= c(desde) && f < c(hasta),
});

const letra = (tam: number, color: string, peso = 700, it = false): React.CSSProperties => ({
  fontFamily: "Inter", fontSize: tam, fontWeight: peso, fontStyle: it ? "italic" : "normal", color, lineHeight: 1,
  letterSpacing: -tam * 0.03, whiteSpace: "nowrap", textShadow: RESPLANDOR,
});

// ---------- Detrás de Andy ----------

/** Texto enorme detrás de Andy (lo tapa su cabeza/hombros): sube despacio y se va borroso. */
const Detras: React.FC<{ desde: number; hasta: number; y: number; children: React.ReactNode }> = ({ desde, hasta, y, children }) => {
  const f = useCurrentFrame();
  const { p, q, visible } = vida(f, desde, hasta, 0.4, 0.3);
  if (!visible) return null;
  const sube = interpolate(f, [c(desde), c(hasta)], [0, -40], clamp); // deriva lenta: se siente vivo
  return (
    <div style={{ position: "absolute", top: y, width: 1080, display: "flex", justifyContent: "center",
      transform: `translateY(-50%) translateY(${(1 - p) * 60 + sube}px) scale(${0.94 + 0.06 * p})`,
      opacity: p * (1 - q), filter: `blur(${(1 - p) * 10 + q * 12}px)` }}>{children}</div>
  );
};

const CapaDetras: React.FC = () => (
  <AbsoluteFill>
    <Detras desde={0.38} hasta={3.2} y={470}>
      <div style={{ display: "flex", alignItems: "baseline", gap: 26 }}>
        <span style={{ ...letra(400, AMARILLO, 900, true), textShadow: "none" }}>3</span>
        <span style={{ ...letra(250, "#FFFFFF", 900, true), textShadow: "none" }}>TIPS</span>
      </div>
    </Detras>
    {[{ t: 11.22, n: "01" }, { t: 23.69, n: "02" }, { t: 30.07, n: "03" }].map(({ t, n }) => (
      <Detras key={n} desde={t} hasta={t + 2.3} y={500}>
        <span style={{ ...letra(560, CLAUDE, 900, true), textShadow: "none", opacity: 0.95 }}>{n}</span>
      </Detras>
    ))}
  </AbsoluteFill>
);

// ---------- Delante ----------

/** Píldora con el nombre del consejo, abajo, al empezar cada sección. */
const Seccion: React.FC<{ desde: number; hasta: number; texto: string }> = ({ desde, hasta, texto }) => {
  const f = useCurrentFrame();
  const { p, q, visible } = vida(f, desde, hasta);
  if (!visible) return null;
  return (
    <div style={{ position: "absolute", top: 1330, width: 1080, display: "flex", justifyContent: "center", opacity: p * (1 - q),
      transform: `translateY(${(1 - p) * 30}px)`, filter: `blur(${q * 8}px)` }}>
      <div style={{ ...letra(46, "#111", 900, true), textShadow: "none", background: CLAUDE, padding: "14px 34px 10px", borderRadius: 999,
        boxShadow: "0 12px 30px rgba(0,0,0,0.35)" }}>{texto}</div>
    </div>
  );
};

/** Lista que se va marcando con la voz (un ✓ por ítem). */
const Lista: React.FC<{ desde: number; hasta: number; items: { t: number; texto: string }[]; top?: number }> = ({ desde, hasta, items, top = 1140 }) => {
  const f = useCurrentFrame();
  const { p, q, visible } = vida(f, desde, hasta);
  if (!visible) return null;
  return (
    <div style={{ position: "absolute", top, left: 170, width: 640, display: "flex", flexDirection: "column", gap: 16,
      opacity: p * (1 - q), filter: `blur(${q * 8}px)` }}>
      {items.map((it, i) => {
        const e = interpolate(f, [c(it.t), c(it.t + 0.28)], [0, 1], { ...clamp, easing: SUAVE });
        const marca = interpolate(f, [c(it.t + 0.1), c(it.t + 0.3)], [0, 1], clamp);
        return (
          <div key={i} style={{ display: "flex", alignItems: "center", gap: 22, opacity: 0.25 + 0.75 * e, transform: `translateX(${(1 - e) * -30}px)` }}>
            <div style={{ width: 64, height: 64, borderRadius: 18, background: e > 0.5 ? AMARILLO : "rgba(255,255,255,0.12)",
              border: "3px solid rgba(255,255,255,0.6)", display: "flex", alignItems: "center", justifyContent: "center" }}>
              <svg width="40" height="40" viewBox="0 0 24 24"><path d="M4 12.5l5 5L20 6.5" fill="none" stroke="#111" strokeWidth="3.4"
                strokeLinecap="round" strokeLinejoin="round" strokeDasharray="30" strokeDashoffset={30 * (1 - marca)} /></svg>
            </div>
            <div style={letra(58, "#FFFFFF", 700)}>{it.texto}</div>
          </div>
        );
      })}
    </div>
  );
};

/** Ícono de pausa que respira en "haz pausa". */
const Pausa: React.FC<{ desde: number; hasta: number }> = ({ desde, hasta }) => {
  const f = useCurrentFrame();
  const { p, q, visible } = vida(f, desde, hasta);
  if (!visible) return null;
  const late = 1 + 0.04 * Math.sin((f - c(desde)) / 5);
  return (
    <div style={{ position: "absolute", top: 1180, width: 1080, display: "flex", justifyContent: "center", opacity: p * (1 - q) }}>
      <div style={{ width: 220, height: 220, borderRadius: 110, background: "rgba(252,243,4,0.14)", border: `6px solid ${AMARILLO}`,
        display: "flex", alignItems: "center", justifyContent: "center", gap: 30, transform: `scale(${(0.85 + 0.15 * p) * late})`,
        boxShadow: `0 0 40px rgba(252,243,4,0.35)` }}>
        {[0, 1].map((i) => <div key={i} style={{ width: 34, height: 100, borderRadius: 10, background: AMARILLO }} />)}
      </div>
    </div>
  );
};

const Persona: React.FC<{ color: string; tam: number }> = ({ color, tam }) => (
  <svg width={tam} height={tam} viewBox="0 0 24 24"><circle cx="12" cy="7.5" r="4" fill={color} /><path d="M4 21c0-4.4 3.6-8 8-8s8 3.6 8 8z" fill={color} /></svg>
);

/** "miles de personas viéndote" -> la pantalla se llena de gente; "solo eres tú y una cámara" -> queda una cámara. */
const Multitud: React.FC = () => {
  const f = useCurrentFrame();
  const { p, q, visible } = vida(f, 36.2, 39.95);
  if (!visible) return null;
  const COL = 9, FIL = 4;
  const vacia = interpolate(f, [c(38.0), c(38.5)], [0, 1], { ...clamp, easing: SUAVE });
  const camara = interpolate(f, [c(39.1), c(39.45)], [0, 1], { ...clamp, easing: SUAVE });
  return (
    <div style={{ position: "absolute", top: 1150, left: 120, width: 720, height: 420, opacity: p * (1 - q) }}>
      {Array.from({ length: COL * FIL }, (_, i) => {
        const x = i % COL, y = Math.floor(i / COL);
        const aparece = interpolate(f, [c(36.3 + (i % 13) * 0.04), c(36.5 + (i % 13) * 0.04)], [0, 1], clamp);
        return (
          <div key={i} style={{ position: "absolute", left: x * 80, top: y * 100, opacity: aparece * (1 - vacia) * (0.55 + 0.45 * ((i * 7) % 3) / 2),
            transform: `scale(${0.6 + 0.4 * aparece}) translateY(${vacia * 40}px)` }}>
            <Persona color="#FFFFFF" tam={72} />
          </div>
        );
      })}
      {f >= c(39.1) && (
        <div style={{ position: "absolute", left: 0, width: 720, top: 90, display: "flex", justifyContent: "center", alignItems: "center", gap: 40,
          opacity: camara, transform: `scale(${0.9 + 0.1 * camara})` }}>
          <Persona color={AMARILLO} tam={150} />
          <svg width="190" height="150" viewBox="0 0 32 24"><rect x="1" y="5" width="21" height="15" rx="3" fill="#FFFFFF" />
            <path d="M23 10l8-4v13l-8-4z" fill="#FFFFFF" /><circle cx="6" cy="9" r="1.6" fill={ROJO} /></svg>
        </div>
      )}
    </div>
  );
};

/** Cierre: logo de la agencia (provisional hasta tener el PNG oficial) y su Instagram. */
const Marca: React.FC<{ desde: number; hasta: number }> = ({ desde, hasta }) => {
  const f = useCurrentFrame();
  const { p, q, visible } = vida(f, desde, hasta, 0.4);
  if (!visible) return null;
  return (
    <div style={{ position: "absolute", top: 1260, width: 1080, display: "flex", flexDirection: "column", alignItems: "center", gap: 14,
      opacity: p * (1 - q), transform: `translateY(${(1 - p) * 30}px)` }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8, background: "rgba(43,43,43,0.92)", padding: "16px 30px", borderRadius: 999 }}>
        <span style={{ ...letra(60, "#FFFFFF", 900, true), textShadow: "none" }}>Visual</span>
        <span style={{ ...letra(60, "#FFFFFF", 900, true), textShadow: "none", background: ROJO_MARCA, padding: "2px 12px 0", borderRadius: 8 }}>PRO</span>
      </div>
      <div style={letra(40, "#FFFFFF", 600)}>@visualpromarketing</div>
    </div>
  );
};

/** Hueco para el video viejo de Andy ("solo mira esto"); solo se ve en el storyboard mientras no llegue el clip. */
const HuecoVideoViejo: React.FC<{ ver: boolean }> = ({ ver }) => {
  const f = useCurrentFrame();
  if (!ver || f < c(9.42) || f >= c(11.22)) return null;
  return (
    <AbsoluteFill style={{ background: "#1b1b1b", alignItems: "center", justifyContent: "center", gap: 24, display: "flex", flexDirection: "column" }}>
      <div style={{ ...letra(64, ROJO, 900, true), textShadow: "none", border: `6px solid ${ROJO}`, padding: "10px 28px 4px", transform: "rotate(-4deg)" }}>ANTES</div>
      <div style={{ ...letra(44, "#FFFFFF", 600), textAlign: "center", whiteSpace: "normal", width: 760 }}>aquí va el video viejo de Andy (pendiente)</div>
    </AbsoluteFill>
  );
};

const CapaFrente: React.FC<{ storyboard?: boolean }> = ({ storyboard }) => (
  <AbsoluteFill>
    <HuecoVideoViejo ver={!!storyboard} />
    <Seccion desde={11.3} hasta={14.2} texto="CREA COMODIDAD" />
    <Lista desde={14.3} hasta={19.75} items={[{ t: 14.36, texto: "Camina" }, { t: 15.12, texto: "Respira" },
      { t: 16.16, texto: "Habla con alguien" }, { t: 18.6, texto: "Di un chiste" }]} />
    <Seccion desde={23.75} hasta={24.3} texto="HAZ PAUSAS" />
    <Pausa desde={24.3} hasta={26.25} />
    <Seccion desde={30.15} hasta={32.0} texto="HABLA COMO CON UN AMIGO" />
    <Multitud />
    <Lista desde={50.9} hasta={54.6} top={1150} items={[{ t: 51.06, texto: "Ideas" }, { t: 52.0, texto: "Scripts" },
      { t: 53.04, texto: "Grabación" }, { t: 54.04, texto: "Edición" }]} />
    <Marca desde={55.9} hasta={57.77} />
    <Textos bloques={BLOQUES} contraste />
  </AbsoluteFill>
);

export const Andy: React.FC<{ capa?: "frente" | "detras"; storyboard?: boolean }> = ({ capa = "frente", storyboard = false }) =>
  capa === "detras" ? <CapaDetras /> : <CapaFrente storyboard={storyboard} />;
