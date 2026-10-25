import React from "react";
import { CalculateMetadataFunction, Composition } from "remotion";
import { cargarFuentes } from "./negocio/comunes";
import { DURACION_S, FPS } from "./negocio/datos";
import { Delante } from "./negocio/Delante";
import { Detras } from "./negocio/Detras";

// Capas transparentes (ProRes 4444) que después se componen con ffmpeg sobre el video.
const transparente: CalculateMetadataFunction<Record<string, unknown>> = async () => {
  await cargarFuentes();
  return {
    defaultCodec: "prores",
    defaultVideoImageFormat: "png",
    defaultPixelFormat: "yuva444p10le",
    defaultProResProfile: "4444",
  };
};

const comun = {
  fps: FPS,
  width: 1080,
  height: 1920,
  durationInFrames: Math.round(DURACION_S * FPS),
  calculateMetadata: transparente,
};

export const RemotionRoot: React.FC = () => (
  <>
    <Composition id="NegocioDetras" component={Detras} {...comun} />
    <Composition id="NegocioDelante" component={Delante} {...comun} />
  </>
);
