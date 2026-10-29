import { loadFont } from "@remotion/fonts";
import React from "react";
import { Easing, interpolate, staticFile, useCurrentFrame } from "remotion";
import { COLORES, FPS } from "./datos";

export const cargarFuentes = () =>
  Promise.all([
    loadFont({ family: "Playfair Display", url: staticFile("fuentes/PlayfairDisplay-Regular.ttf"), weight: "400" }),
    loadFont({ family: "Playfair Display", url: staticFile("fuentes/PlayfairDisplay-Bold.ttf"), weight: "700" }),
    loadFont({ family: "Inter", url: staticFile("fuentes/Inter-SemiBold.ttf"), weight: "600" }),
    loadFont({ family: "Inter", url: staticFile("fuentes/Inter-Bold.ttf"), weight: "700" }),
  ]);

export const cuadro = (segundos: number) => Math.round(segundos * FPS);

const SALIDA_SUAVE = Easing.bezier(0.16, 1, 0.3, 1);

/** 0→1 con la curva de entrada de la casa (rápida al principio, frena al final). */
export const useEntrada = (segundos: number, duracion = 0.35) => {
  const f = useCurrentFrame();
  return interpolate(f, [cuadro(segundos), cuadro(segundos + duracion)], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: SALIDA_SUAVE,
  });
};

/** Visible solo dentro del plano, con fundido corto al entrar y al salir. */
export const usePlano = (desde: number, hasta: number) => {
  const f = useCurrentFrame();
  const visible = f >= cuadro(desde) && f < cuadro(hasta);
  const opacidad = interpolate(
    f,
    [cuadro(desde), cuadro(desde) + 3, cuadro(hasta) - 3, cuadro(hasta)],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );
  return { visible, opacidad };
};

type IconoProps = { nombre: string; tam?: number; color?: string };

/** Íconos de trazo simple, dibujados en SVG (sin dependencias). */
export const Icono: React.FC<IconoProps> = ({ nombre, tam = 56, color = COLORES.acento }) => {
  const p = { fill: "none", stroke: color, strokeWidth: 2.2, strokeLinecap: "round" as const, strokeLinejoin: "round" as const };
  if (nombre === "logo") nombre = "estrella"; // el logo del cliente se borró al terminar la prueba
  const trazos: Record<string, React.ReactNode> = {
    persona: <><circle cx="12" cy="8" r="4" {...p} /><path d="M4 21c0-4.4 3.6-7 8-7s8 2.6 8 7" {...p} /></>,
    reloj: <><circle cx="12" cy="12" r="9" {...p} /><path d="M12 7v5l3 2" {...p} /></>,
    edificio: <><path d="M4 21V5l8-3v19M12 9l8 3v9M2 21h20M8 8h0M8 12h0M8 16h0M16 15h0M16 18h0" {...p} /></>,
    telefono: <path d="M5 3h4l2 5-2.5 1.5a11 11 0 0 0 6 6L16 13l5 2v4a2 2 0 0 1-2 2A17 17 0 0 1 3 5a2 2 0 0 1 2-2z" {...p} />,
    maletin: <><rect x="3" y="7" width="18" height="13" rx="2" {...p} /><path d="M9 7V5a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v2M3 13h18" {...p} /></>,
    estrella: <path d="M12 3l2.8 5.7 6.2.9-4.5 4.4 1 6.2L12 17.3 6.5 20.2l1-6.2L3 9.6l6.2-.9z" {...p} />,
    flecha: <><path d="M4 18l6-6 4 4 6-8" {...p} /><path d="M15 8h5v5" {...p} /></>,
    semilla: <><path d="M12 21v-8M12 13c0-4 3-7 8-7 0 5-3 7-8 7zM12 15c0-3-2-5-6-5 0 3 2 5 6 5z" {...p} /></>,
    equipo: <><circle cx="8" cy="9" r="3" {...p} /><circle cx="16" cy="9" r="3" {...p} /><path d="M2 20c0-3 3-5 6-5s6 2 6 5M14 15c3 0 8 1 8 5" {...p} /></>,
    mentoria: <><path d="M3 9l9-5 9 5-9 5z" {...p} /><path d="M7 11v5c3 2 7 2 10 0v-5" {...p} /></>,
    training: <><rect x="3" y="4" width="18" height="12" rx="2" {...p} /><path d="M10 8l4 2-4 2zM8 20h8" {...p} /></>,
    tecnologia: <><rect x="6" y="6" width="12" height="12" rx="2" {...p} /><path d="M9 2v4M15 2v4M9 18v4M15 18v4M2 9h4M2 15h4M18 9h4M18 15h4" {...p} /></>,
    herramientas: <path d="M14 7a4 4 0 0 1 5-4l-3 3 1 3 3 1 3-3a4 4 0 0 1-4 5L9 22l-3-3z" {...p} />,
    check: <path d="M4 12l5 5L20 6" {...p} />,
  };
  return (
    <svg width={tam} height={tam} viewBox="0 0 24 24">
      {trazos[nombre]}
    </svg>
  );
};

/** Fondo de panel de la mitad de arriba (planos B y C). */
// El fondo aparece de golpe con el corte (si se funde, asoma el relleno del video bajado); el contenido sí se funde.
export const PanelArriba: React.FC<{ opacidad: number; children: React.ReactNode }> = ({ opacidad, children }) => (
  <div
    style={{
      position: "absolute",
      left: 0,
      top: 0,
      width: 1080,
      height: 960,
      background: `radial-gradient(120% 90% at 50% 0%, ${COLORES.panel2} 0%, ${COLORES.panel1} 70%)`,
      boxShadow: "0 30px 60px rgba(0,0,0,0.45)",
      overflow: "hidden",
    }}
  >
    <div style={{ position: "absolute", inset: 0, opacity: opacidad }}>{children}</div>
  </div>
);
