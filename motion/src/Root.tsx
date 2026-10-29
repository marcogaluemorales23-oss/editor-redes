import React from "react";
import { CalculateMetadataFunction, Composition } from "remotion";
import { cargarFuentes } from "./negocio/comunes";
import { DURACION_S, FPS } from "./negocio/datos";
import { Delante } from "./negocio/Delante";
import { Detras } from "./negocio/Detras";
import { cargarFuentesSebastian, DURACION_S as DUR_P01, FPS as FPS_P01, Prueba01 } from "./sebastian/Prueba01";
import { DURACION_S as DUR_P01B, Prueba01b } from "./sebastian/Prueba01b";
import { DURACION_S as DUR_P01C, Prueba01c } from "./sebastian/Prueba01c";

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
    <Composition
      id="SebastianPrueba01c"
      component={Prueba01c}
      fps={FPS_P01}
      width={1080}
      height={1920}
      durationInFrames={Math.round(DUR_P01C * FPS_P01)}
      calculateMetadata={async () => {
        await cargarFuentesSebastian();
        return { defaultCodec: "prores", defaultVideoImageFormat: "png", defaultPixelFormat: "yuva444p10le", defaultProResProfile: "4444" };
      }}
    />
    <Composition
      id="SebastianPrueba01b"
      component={Prueba01b}
      fps={FPS_P01}
      width={1080}
      height={1920}
      durationInFrames={Math.round(DUR_P01B * FPS_P01)}
      calculateMetadata={async () => {
        await cargarFuentesSebastian();
        return { defaultCodec: "prores", defaultVideoImageFormat: "png", defaultPixelFormat: "yuva444p10le", defaultProResProfile: "4444" };
      }}
    />
    <Composition
      id="SebastianPrueba01"
      component={Prueba01}
      fps={FPS_P01}
      width={1080}
      height={1920}
      durationInFrames={Math.round(DUR_P01 * FPS_P01)}
      calculateMetadata={async () => {
        await cargarFuentesSebastian();
        return { defaultCodec: "prores", defaultVideoImageFormat: "png", defaultPixelFormat: "yuva444p10le", defaultProResProfile: "4444" };
      }}
    />
  </>
);
