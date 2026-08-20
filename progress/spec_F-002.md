<!-- progress/spec_F-002.md -->
# F-002 · Spec redactada — decisiones y dudas abiertas

**Entregable**: `specs/F-002-ingesta-troceado/` con `requirements.md`
(19 requisitos EARS, cada uno con su test trazable), `design.md` y
`tasks.md` (16 tareas, RED antes que implementación). Ni una línea de código
de producción.

## El hallazgo que ha condicionado el diseño

Al diseñar se comprobó, con `pymupdf` y en solo lectura, la remesa real
`docs/referencia/doc02871320260817093833.pdf` (no versionada):

```
paginas: 22 · TOTAL chars capa texto: 0 · 1 imagen por pagina
```

**El escaneo no tiene capa de texto.** Es decir: la regla del pie —«el parte
de dos hojas se delata por el "Página 2"»— **no se puede disparar hoy sobre
las remesas reales**. Solo funcionará con PDFs que traigan texto (los que
genera Sigrid directamente, o un escaneo con OCR).

Esto **no invalida los criterios `acceptance`**: Mirasierra son 22 partes de
una hoja, y la regla por defecto —una página, un parte— acierta las 22. Pero
obliga a que el resultado declare **en qué modo se troceó**.

## Decisiones tomadas

1. **Una sola regla, sin bifurcación.** Continuación ⟺ la página tiene el
   marcador de plantilla `RCP_Parte_de_Trabajos` **y** un `Página N` con
   N ≥ 2. Sin texto no hay pie reconocido, así que la degradación a «una
   página, un parte» sale sola, sin un `if` alternativo que nadie ejercite.
   El campo `modo_deteccion` (`por_pie_de_pagina` / `una_pagina_por_parte`)
   es **informativo**: dice si se pudo mirar el pie.
2. **Regla conservadora**: ante la duda, se abre parte. Trocear de más manda
   un parte a revisión manual; fundir dos partes pierde una incidencia.
3. **Hash**: SHA-256 sobre el **texto normalizado y las imágenes incrustadas
   de las páginas de origen**, con longitudes delimitadas — **no** sobre los
   bytes del PDF troceado, que dependen de la versión de PyMuPDF, del `/ID` y
   de la compresión. Es lo único que hace cierto el criterio «un ZIP y un PDF
   multi-parte producen la misma lista» y la promesa de F-005 de no duplicar.
4. **Capas**: la regla del pie es dominio puro (`PieDePagina`), los pasos van
   en `application/pipelines/`, PDF y ZIP son adaptadores en una carpeta nueva
   `infrastructure/documentos/`, y el endpoint en `interface_adapters/api/`.
   El dominio no importa `pymupdf` ni `zipfile` (R19 lo vigila con un test).
5. **`pymupdf` se declara en `services/postventa-api/requirements.txt`** (es
   código de producción del servicio), no solo en el `requirements-dev.txt` de
   la raíz, que es el del arnés.
6. **Generador de PDFs sintéticos con PyMuPDF**, no con ReportLab: es material
   de test y ReportLab sería una dependencia solo para fixtures. Anotado en el
   diseño para que el reviewer no lo lea como incumplimiento de
   `docs/CONVENTIONS.md`.
7. **Límites del ZIP como constantes del adaptador** (500 entradas, 200 MB
   descomprimidos), comprobados sobre el índice: una bomba nunca se expande.
   No se añaden variables nuevas a `Ajustes`.
8. **Alcance cerrado**: ni extracción, ni validación, ni persistencia, ni SQL,
   ni SharePoint, ni Sigrid, ni front. R18 fija con un test que la respuesta
   de `/split` no lleva **ningún** campo de negocio.

## Dudas abiertas — necesitan al humano

1. **[Decisión de producto] El parte de dos hojas no se detectará en
   producción mientras las remesas lleguen sin OCR.** Opciones:
   - **(a) Aceptar la degradación en v1** y dejarla declarada en
     `modo_deteccion`. Mirasierra sale 22/22. *Es lo que la spec asume.*
   - (b) Añadir OCR del pie: dependencia nueva (tesseract), tests offline
     complicados. No recomendado ahora.
   - (c) Cuando exista **F-003**, aprovechar que ya pasa cada página por un
     modelo multimodal para que devuelva el «Página N» del pie y reagrupar
     después. *Es la continuación natural; no se implementa en F-002.*
2. **Redacción del criterio `acceptance` 2.** Dice «22 páginas = 22 partes,
   con su parte de dos hojas». Según `docs/referencia/02_parte_de_trabajo.md`
   la remesa de Mirasierra **no tiene** ningún parte de dos hojas (las 22
   páginas numeran «Página 1»); el de dos hojas es el caso general que hay que
   soportar. La spec lo resuelve así: recuento sobre Mirasierra como
   verificación **`MANUAL (humano)`** (T15), y parte de dos hojas cubierto por
   los **tests sintéticos** de T9. Si la intención era otra, hay que decirlo
   antes de implementar.
3. **`/split` devuelve el PDF de cada parte en base64**, porque no hay
   persistencia hasta F-005. Para 22 partes escaneados eso infla la respuesta
   un 33 %. Aceptable para el piloto; conviene confirmarlo.
4. **Riesgo técnico a vigilar en la fase RED** (T6): si PyMuPDF no conservase
   el contenido de la página al extraerla, el criterio «ZIP y PDF multi-parte
   dan la misma lista» no se cumpliría. La spec ordena **parar y reportar**,
   no improvisar.

## Estado

`F-002` sigue en `pending`: la spec necesita **aprobación del humano** antes
de pasar a `spec_ready` y de que entre el implementer.
