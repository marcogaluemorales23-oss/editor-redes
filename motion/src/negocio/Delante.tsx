import React from "react";
import { AbsoluteFill, Easing, interpolate, useCurrentFrame } from "remotion";
import { Icono, PanelArriba, cuadro, usePlano } from "./comunes";
import { COLORES, MOMENTOS, PLANOS, TITULOS_A } from "./datos";

// Capa que va DELANTE de todo (menos los subtítulos): títulos del plano A y paneles de los planos B y C.
// Todo dentro de la zona segura: x 110-950, y desde 245.

const CURVA = Easing.bezier(0.16, 1, 0.3, 1);
/** 0→1 desde el segundo `s`, en `d` segundos. */
const ent = (f: number, s: number, d = 0.35) =>
  interpolate(f, [cuadro(s), cuadro(s + d)], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: CURVA });

const tarjeta: React.CSSProperties = {
  background: "rgba(255,255,255,0.06)",
  border: `1.5px solid ${COLORES.borde}`,
  borderRadius: 26,
};

const Titulo: React.FC<{ desde: number; hasta: number; linea1: string; clave: string }> = ({ desde, hasta, linea1, clave }) => {
  const f = useCurrentFrame();
  const { visible, opacidad } = usePlano(desde, hasta);
  if (!visible) return null;
  const caja = (texto: string, color: string, retraso: number) => {
    const e = ent(f, desde + retraso, 0.3);
    return (
      <div style={{ display: "inline-block", background: "#000", padding: "6px 22px 12px", opacity: e, translate: `${(1 - e) * -40}px 0px` }}>
        <span style={{ fontFamily: "Playfair Display", fontWeight: 700, fontSize: 76, color, letterSpacing: -2 }}>{texto}</span>
      </div>
    );
  };
  return (
    <div style={{ position: "absolute", top: 270, left: 0, width: 1080, textAlign: "center", opacity: opacidad, lineHeight: 1.05 }}>
      {caja(linea1, COLORES.texto, 0)}
      <br />
      {caja(clave, COLORES.acento, 0.12)}
    </div>
  );
};

/** Gancho: llamas a tu broker y no contesta; se apilan notificaciones. */
const Gancho: React.FC = () => {
  const f = useCurrentFrame();
  const { desde, hasta } = PLANOS.gancho;
  const { visible, opacidad } = usePlano(desde, hasta);
  if (!visible) return null;
  const sinRespuesta = f >= cuadro(MOMENTOS.llamar);
  const pulso = 1 + 0.08 * Math.sin((f / 24) * Math.PI * 2 * 1.4);
  const notis = [
    { s: MOMENTOS.notiLlamada, color: COLORES.rojo, icono: "telefono", titulo: "Llamada perdida", texto: "Tu broker no contestó" },
    { s: MOMENTOS.notiMensaje, color: "#25D366", icono: "persona", titulo: "Mensaje sin leer", texto: "¿Me ayudas con el cierre?" },
    { s: MOMENTOS.sinNadie, color: "#F5A623", icono: "reloj", titulo: "Cliente esperando", texto: "La firma sigue pendiente" },
  ];
  return (
    <PanelArriba opacidad={opacidad}>
      <div style={{ position: "absolute", top: 275, left: 130, width: 820, display: "flex", alignItems: "center", gap: 32 }}>
        <div style={{ width: 148, height: 148, borderRadius: 74, background: "rgba(255,255,255,0.08)", display: "flex", alignItems: "center", justifyContent: "center", scale: sinRespuesta ? "1" : String(pulso), border: `3px solid ${sinRespuesta ? COLORES.rojo : COLORES.verde}` }}>
          <Icono nombre="persona" tam={80} color={COLORES.texto} />
        </div>
        <div>
          <div style={{ fontFamily: "Inter", fontWeight: 700, fontSize: 56, color: COLORES.texto }}>Tu broker</div>
          <div style={{ fontFamily: "Inter", fontWeight: 600, fontSize: 38, color: sinRespuesta ? COLORES.rojo : COLORES.suave }}>
            {sinRespuesta ? "Sin respuesta" : "Llamando…"}
          </div>
        </div>
      </div>
      {notis.map((n, i) => {
        const e = ent(f, n.s, 0.4);
        return (
          <div key={i} style={{ ...tarjeta, position: "absolute", left: 130, width: 820, top: 480 + i * 158, height: 142, display: "flex", alignItems: "center", gap: 26, padding: "0 30px", opacity: e, translate: `0px ${(1 - e) * -60}px`, scale: String(0.94 + 0.06 * e) }}>
            <div style={{ width: 86, height: 86, borderRadius: 22, background: n.color, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
              <Icono nombre={n.icono} tam={48} color="#fff" />
            </div>
            <div style={{ flex: 1 }}>
              <div style={{ display: "flex", justifyContent: "space-between", fontFamily: "Inter", fontWeight: 700, fontSize: 38, color: COLORES.texto }}>
                <span>{n.titulo}</span>
                <span style={{ fontWeight: 600, fontSize: 26, color: COLORES.suave }}>ahora</span>
              </div>
              <div style={{ fontFamily: "Inter", fontWeight: 600, fontSize: 32, color: COLORES.suave }}>{n.texto}</div>
            </div>
          </div>
        );
      })}
    </PanelArriba>
  );
};

/** Chat con el broker: disponible y resolviendo duda, problema y cierre. */
const Chat: React.FC = () => {
  const f = useCurrentFrame();
  const { desde, hasta } = PLANOS.chat;
  const { visible, opacidad } = usePlano(desde, hasta);
  if (!visible) return null;
  const enLinea = f >= cuadro(MOMENTOS.disponible);
  const burbujas = [
    { s: desde + 0.2, mio: true, texto: "¿Estás disponible?" },
    { s: MOMENTOS.disponible, mio: false, texto: "Siempre. Cuéntame" },
    { s: MOMENTOS.duda, mio: false, texto: "Tu duda: resuelta", check: true },
    { s: MOMENTOS.problema, mio: false, texto: "Tu problema: resuelto", check: true },
    { s: MOMENTOS.cierre, mio: false, texto: "Tu cierre: listo", check: true },
  ];
  return (
    <PanelArriba opacidad={opacidad}>
      <div style={{ position: "absolute", top: 262, left: 120, width: 840, height: 116, display: "flex", alignItems: "center", gap: 22, borderBottom: `1.5px solid ${COLORES.borde}` }}>
        <div style={{ width: 88, height: 88, borderRadius: 44, background: "rgba(255,222,68,0.15)", display: "flex", alignItems: "center", justifyContent: "center" }}>
          <Icono nombre="persona" tam={52} />
        </div>
        <div>
          <div style={{ fontFamily: "Inter", fontWeight: 700, fontSize: 44, color: COLORES.texto }}>Tu broker</div>
          <div style={{ fontFamily: "Inter", fontWeight: 600, fontSize: 30, color: enLinea ? COLORES.verde : COLORES.suave }}>
            {enLinea ? "● en línea" : "escribiendo…"}
          </div>
        </div>
      </div>
      {burbujas.map((b, i) => {
        const e = ent(f, b.s, 0.3);
        if (e <= 0) return null;
        return (
          <div key={i} style={{ position: "absolute", top: 410 + i * 104, left: b.mio ? undefined : 120, right: b.mio ? 130 : undefined, opacity: e, scale: String(0.9 + 0.1 * e), translate: `${(1 - e) * (b.mio ? 30 : -30)}px 0px` }}>
            <div style={{ display: "flex", alignItems: "center", gap: 16, padding: "18px 30px", borderRadius: 30, background: b.mio ? COLORES.acento : "rgba(255,255,255,0.1)", color: b.mio ? "#111" : COLORES.texto, fontFamily: "Inter", fontWeight: 600, fontSize: 40 }}>
              {b.check ? (
                <div style={{ width: 50, height: 50, borderRadius: 25, background: COLORES.acento, display: "flex", alignItems: "center", justifyContent: "center" }}>
                  <Icono nombre="check" tam={30} color="#111" />
                </div>
              ) : null}
              {b.texto}
            </div>
          </div>
        );
      })}
    </PanelArriba>
  );
};

/** Programa especial: tarjeta y dos barras que suben (sin cifras inventadas). */
const Barras: React.FC = () => {
  const f = useCurrentFrame();
  const { desde, hasta } = PLANOS.barras;
  const { visible, opacidad } = usePlano(desde, hasta);
  if (!visible) return null;
  const eTitulo = ent(f, desde + 0.1, 0.4);
  const brillo = ent(f, MOMENTOS.especial, 0.3);
  const filas = [
    { s: MOMENTOS.comisiones, texto: "Comisiones", hasta: 0.88 },
    { s: MOMENTOS.beneficios, texto: "Beneficios preferenciales", hasta: 0.78 },
  ];
  return (
    <PanelArriba opacidad={opacidad}>
      <div style={{ position: "absolute", top: 285, left: 140, width: 800, opacity: eTitulo, translate: `0px ${(1 - eTitulo) * 30}px` }}>
        <div style={{ fontFamily: "Inter", fontWeight: 700, fontSize: 28, letterSpacing: 4, color: COLORES.suave }}>PARA AGENTES CON EXPERIENCIA</div>
        <div style={{ fontFamily: "Playfair Display", fontWeight: 700, fontSize: 68, lineHeight: 1.05, color: COLORES.texto, marginTop: 10 }}>
          Programa <span style={{ color: COLORES.acento, textShadow: `0 0 ${24 * brillo}px rgba(255,222,68,${0.6 * brillo})` }}>especial</span> para ti
        </div>
      </div>
      {filas.map((fila, i) => {
        const e = ent(f, fila.s, 0.9);
        // La barra vacía ya está desde que entra el panel; se llena cuando ella nombra cada cosa.
        const aparece = ent(f, desde + 0.35 + i * 0.12, 0.35);
        return (
          <div key={i} style={{ position: "absolute", top: 600 + i * 150, left: 140, width: 800, opacity: aparece }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", fontFamily: "Inter", fontWeight: 700, fontSize: 34, color: COLORES.texto, marginBottom: 16 }}>
              <span>{fila.texto}</span>
              <span style={{ opacity: e }}><Icono nombre="flecha" tam={44} /></span>
            </div>
            <div style={{ height: 26, borderRadius: 13, background: "rgba(255,255,255,0.1)", overflow: "hidden" }}>
              <div style={{ width: `${fila.hasta * 100 * e}%`, height: "100%", borderRadius: 13, background: `linear-gradient(90deg, #E8C22E, ${COLORES.acento})`, boxShadow: "0 0 24px rgba(255,222,68,0.45)" }} />
            </div>
          </div>
        );
      })}
    </PanelArriba>
  );
};

/** Vas empezando: mentoría, training, tecnología, herramientas; y "Día 1". */
const Lista: React.FC = () => {
  const f = useCurrentFrame();
  const { desde, hasta } = PLANOS.lista;
  const { visible, opacidad } = usePlano(desde, hasta);
  if (!visible) return null;
  const items = [
    { s: MOMENTOS.mentoria, icono: "mentoria", texto: "Mentoría" },
    { s: MOMENTOS.training, icono: "training", texto: "Training" },
    { s: MOMENTOS.tecnologia, icono: "tecnologia", texto: "Tecnología" },
    { s: MOMENTOS.herramientas, icono: "herramientas", texto: "Herramientas" },
  ];
  const eTitulo = ent(f, desde + 0.1, 0.35);
  const dia = ent(f, MOMENTOS.primerDia - 0.25, 0.35);
  return (
    <PanelArriba opacidad={opacidad}>
      <div style={{ position: "absolute", top: 285, left: 140, fontFamily: "Inter", fontWeight: 700, fontSize: 28, letterSpacing: 4, color: COLORES.suave, opacity: eTitulo }}>
        SI VAS EMPEZANDO, TE DAMOS
      </div>
      {items.map((it, i) => {
        const e = ent(f, it.s, 0.35);
        const col = i % 2;
        const fila = Math.floor(i / 2);
        return (
          <div key={i} style={{ ...tarjeta, position: "absolute", left: 140 + col * 412, top: 355 + fila * 250, width: 388, height: 226, padding: 30, display: "flex", flexDirection: "column", justifyContent: "space-between", opacity: e * (1 - dia * 0.75), scale: String(0.85 + 0.15 * e) }}>
            <Icono nombre={it.icono} tam={64} />
            <div style={{ fontFamily: "Inter", fontWeight: 700, fontSize: 40, color: COLORES.texto }}>{it.texto}</div>
          </div>
        );
      })}
      {dia > 0 ? (
        <div style={{ position: "absolute", left: 540 - 170, top: 430, width: 340, height: 360, borderRadius: 34, overflow: "hidden", background: "#fff", boxShadow: "0 30px 60px rgba(0,0,0,0.5)", opacity: dia, scale: String(0.7 + 0.3 * dia) }}>
          <div style={{ height: 96, background: COLORES.acento, display: "flex", alignItems: "center", justifyContent: "center", fontFamily: "Inter", fontWeight: 700, fontSize: 34, letterSpacing: 3, color: "#111" }}>DESDE EL</div>
          <div style={{ height: 264, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", fontFamily: "Playfair Display", fontWeight: 700, color: "#111" }}>
            <div style={{ fontSize: 56 }}>Día</div>
            <div style={{ fontSize: 150, lineHeight: 0.9 }}>1</div>
          </div>
        </div>
      ) : null}
    </PanelArriba>
  );
};

export const Delante: React.FC = () => (
  <AbsoluteFill>
    <Titulo desde={PLANOS.a1.desde} hasta={PLANOS.a1.hasta} {...TITULOS_A.a1} />
    <Titulo desde={PLANOS.a2.desde} hasta={PLANOS.a2.hasta} {...TITULOS_A.a2} />
    <Gancho />
    <Chat />
    <Barras />
    <Lista />
  </AbsoluteFill>
);
