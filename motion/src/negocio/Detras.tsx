import React from "react";
import { AbsoluteFill, Easing, interpolate, useCurrentFrame } from "remotion";
import { Icono, cuadro, usePlano } from "./comunes";
import { COLORES, FPS, MOMENTOS, PLANOS, TARJETAS_A } from "./datos";

// Capa que va DETRÁS de la persona recortada (plano A): oscurece un poco la pared y pasan tarjetas.
const ANCHO_T = 270;
const ALTO_T = 340;
const SEPARACION = 30;
const VELOCIDAD = 70; // px por segundo hacia la izquierda
const Y_FILA = 470;   // a la altura de la cabeza y los hombros

type Tarjeta = { readonly icono: string; readonly texto: string };

const FilaDeTarjetas: React.FC<{ desde: number; hasta: number; tarjetas: readonly Tarjeta[] }> = ({
  desde,
  hasta,
  tarjetas,
}) => {
  const f = useCurrentFrame();
  const { visible, opacidad } = usePlano(desde, hasta);
  if (!visible) return null;
  const t = (f - cuadro(desde)) / FPS;
  // Se repiten las tarjetas para llenar el ancho mientras se desplazan.
  const lista = [...tarjetas, ...tarjetas, ...tarjetas];
  const paso = ANCHO_T + SEPARACION;
  const x0 = 120 - t * VELOCIDAD;
  return (
    <AbsoluteFill style={{ opacity: opacidad }}>
      {/* Pared un poco más oscura: la persona resalta y el texto de las tarjetas se lee */}
      <AbsoluteFill style={{ background: "radial-gradient(90% 60% at 50% 40%, rgba(0,0,0,0.18), rgba(0,0,0,0.42))" }} />
      {lista.map((tarjeta, i) => {
        const entrada = interpolate(f, [cuadro(desde) + i * 2, cuadro(desde) + i * 2 + 10], [0, 1], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
          easing: Easing.bezier(0.16, 1, 0.3, 1),
        });
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: x0 + i * paso,
              top: Y_FILA,
              width: ANCHO_T,
              height: ALTO_T,
              borderRadius: 28,
              background: `linear-gradient(160deg, rgba(40,44,54,0.92), ${COLORES.tarjeta})`,
              border: `1.5px solid ${COLORES.borde}`,
              boxShadow: "0 18px 40px rgba(0,0,0,0.45)",
              padding: 28,
              display: "flex",
              flexDirection: "column",
              justifyContent: "space-between",
              opacity: entrada,
              translate: `0px ${(1 - entrada) * 40}px`,
            }}
          >
            <div
              style={{
                width: 84,
                height: 84,
                borderRadius: 42,
                background: "rgba(255,222,68,0.12)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <Icono nombre={tarjeta.icono} tam={46} />
            </div>
            <div>
              <div style={{ width: 46, height: 4, borderRadius: 2, background: COLORES.acento, marginBottom: 16 }} />
              <div style={{ fontFamily: "Inter", fontWeight: 700, fontSize: 31, lineHeight: 1.15, color: COLORES.texto }}>
                {tarjeta.texto}
              </div>
            </div>
          </div>
        );
      })}
    </AbsoluteFill>
  );
};

/** Gancho: en "solo" la pared se oscurece y queda ella como único foco (sensación de aislamiento). */
const Foco: React.FC = () => {
  const f = useCurrentFrame();
  const { visible } = usePlano(PLANOS.foco.desde, PLANOS.foco.hasta);
  if (!visible) return null;
  const oscuro = interpolate(f, [cuadro(MOMENTOS.solo), cuadro(MOMENTOS.solo + 0.35)], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.bezier(0.16, 1, 0.3, 1),
  });
  return (
    <AbsoluteFill
      style={{ opacity: oscuro, background: "radial-gradient(70% 45% at 50% 48%, rgba(0,0,0,0.55), rgba(0,0,0,0.88))" }}
    />
  );
};

export const Detras: React.FC = () => (
  <AbsoluteFill>
    <Foco />
    <FilaDeTarjetas desde={PLANOS.a1.desde} hasta={PLANOS.a1.hasta} tarjetas={TARJETAS_A.a1} />
    <FilaDeTarjetas desde={PLANOS.a2.desde} hasta={PLANOS.a2.hasta} tarjetas={TARJETAS_A.a2} />
    <FilaDeTarjetas desde={PLANOS.a3.desde} hasta={PLANOS.a3.hasta} tarjetas={TARJETAS_A.a3} />
  </AbsoluteFill>
);
