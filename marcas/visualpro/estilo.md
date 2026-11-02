# VisualPRO Marketing — estilo

Cliente de Sebastián (agencia de Andy, @visualpromarketing). Formato dynamic de Sebas: `marcas/sebastian/formato-dynamic.md`.

1. **Grabación**: estudio con fondo gris oscuro, dos cámaras Sony (A: plano abierto, Andy sentado en silla de
   director, 4K vertical con marca de rotación; B: plano cerrado de lado, grabó acostada SIN marca de rotación,
   va con transpose=1). Cortes exactos e intercalado A/B: `nucleo/afinar_cortes.py` + `nucleo/multicam.py`.
2. **Fondo oscuro = textos grandes DETRÁS de Andy** (recorte con `nucleo/silueta.py`): "3 TIPS", "01/02/03".
3. **Colores de las palabras clave**: regla de Sebas (verde dinero/ganar, rojo error o lo malo, el resto amarillo o
   naranja de Claude). El rojo de la marca solo en el logo y en la caja del CTA (pendiente confirmar con Sebas).
4. **CTA**: escribir por DM a @visualpromarketing.
5. **Correcciones de Sebas al storyboard**:
   - En la toma donde Andy se inclina (cámara B cerrada, 3,2–8 s) el texto quedaba a la altura de la cara: esos
     bloques van más abajo (`"centro": 1230` en textos.json). Revisar cada toma cerrada: el texto nunca a la altura
     de la cara.
   - Los íconos solo cuando la frase habla de eso: el de pausa va en "haz pausa", no en "no tienes que ir corriendo".
   - Palabra negada ("no tienes que ir corriendo"): se anima la misma palabra, sin b-roll encima: una línea la tacha
     y la parte en dos mitades (`"tachar": true`).
   - Camisa vino tinto: palabras rojas y naranjas con halo fuerte (`<Textos contraste />`).
