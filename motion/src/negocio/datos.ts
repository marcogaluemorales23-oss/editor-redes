// Tiempos del video-01 (segundos de la línea de tiempo del corte, salen de trabajo/corte_check.json).
export const FPS = 23.976;
export const DURACION_S = 26.568;

export const COLORES = {
  acento: "#FFDE44",
  texto: "#FFFFFF",
  suave: "rgba(255,255,255,0.62)",
  panel1: "#0D0F13",
  panel2: "#1B1F27",
  tarjeta: "rgba(22,25,32,0.86)",
  borde: "rgba(255,255,255,0.10)",
  rojo: "#FF5A5F",
  verde: "#3DDC84",
};

// Planos: C = animación arriba, A = completa con tarjetas detrás, B = partida con interfaz arriba.
export const PLANOS = {
  foco: { tipo: "A", desde: 0, hasta: 1.844 },
  gancho: { tipo: "C", desde: 1.844, hasta: 3.712 },
  a1: { tipo: "A", desde: 3.712, hasta: 6.298 },
  chat: { tipo: "B", desde: 6.298, hasta: 10.594 },
  a2: { tipo: "A", desde: 10.594, hasta: 11.694 },
  barras: { tipo: "C", desde: 11.694, hasta: 15.599 },
  lista: { tipo: "B", desde: 15.599, hasta: 21.73 },
  a3: { tipo: "A", desde: 21.73, hasta: 26.568 },
} as const;

// Momentos en que entran los elementos (inicio de la palabra que los nombra).
export const MOMENTOS = {
  solo: 0.984,
  transaccion: 1.844,
  sinNadie: 2.754,
  notiLlamada: 2.0,
  notiMensaje: 2.4,
  llamar: 3.294,
  disponible: 7.825,
  duda: 8.325,
  problema: 9.205,
  cierre: 10.108,
  especial: 12.374,
  comisiones: 13.814,
  beneficios: 14.394,
  mentoria: 16.498,
  training: 17.798,
  tecnologia: 18.378,
  herramientas: 19.298,
  primerDia: 21.238,
};

// Tarjetas que pasan detrás de ella en cada plano A.
export const TARJETAS_A = {
  a1: [
    { icono: "persona", texto: "Tu broker" },
    { icono: "reloj", texto: "Siempre presente" },
    { icono: "edificio", texto: "Dentro y fuera de la oficina" },
    { icono: "telefono", texto: "Disponible" },
  ],
  a2: [
    { icono: "maletin", texto: "Agentes con experiencia" },
    { icono: "estrella", texto: "Programa especial" },
    { icono: "flecha", texto: "Más crecimiento" },
  ],
  a3: [
    { icono: "semilla", texto: "Nuevo" },
    { icono: "maletin", texto: "Con experiencia" },
    { icono: "equipo", texto: "Aquí no trabajas solo" },
    { icono: "logo", texto: "Sancy Diamond Realty" },
  ],
} as const;

export const TITULOS_A = {
  a1: { linea1: "Aquí eso", clave: "no pasa" },
  a2: { linea1: "Ya tienes", clave: "experiencia" },
} as const;
