<!-- specs/F-002-ingesta-troceado/requirements.md -->
# F-002 · Ingesta y troceado de la remesa en partes — Requisitos (EARS)

> Contrato de partida: la entrada `F-002` de `harness/features.json` (cinco
> criterios `acceptance`). Estos requisitos los desarrollan; no los amplían.
> Rigor declarado: **`critico`** (fase RED, cobertura, mutación con cero
> supervivientes y verificaciones `MANUAL (humano)` con su comando exacto).

## Alcance

F-002 hace **tres cosas y ninguna más**:

1. **Ingesta** — normalizar la entrada (PDF suelto, ZIP, varios ficheros) a
   una lista de PDFs.
2. **Troceado** — partir cada PDF de remesa en documentos de **un parte**,
   detectando el comienzo por la plantilla impresa.
3. **Hash** — dar a cada parte troceado una huella estable para que
   reprocesar la misma remesa no duplique.

**Fuera de alcance, explícitamente**: leer el contenido del parte (nº de
incidencia, código de obra, firma, manuscritos). Eso es F-003. Ver R18.

## Vocabulario

- **Remesa**: lo que sube el usuario de una vez. Puede ser un PDF con N
  partes, un ZIP, o varios ficheros.
- **Documento de entrada**: un fichero de la remesa (nombre + bytes).
- **Parte troceado**: PDF de una o dos páginas que contiene **un solo parte**
  de trabajo, con su huella.
- **Pie reconocido**: el pie que imprime Sigrid en cada página del parte,
  `(RCP_Parte_de_Trabajos.xjs) Parte de Trabajo` … `Página N`
  (`docs/referencia/02_parte_de_trabajo.md`).
- **Capa de texto útil**: texto extraíble de la página por encima del umbral
  declarado. Un escaneo sin OCR no la tiene: **la remesa real de Mirasierra
  tiene 0 caracteres de texto en sus 22 páginas** (comprobado al diseñar).

---

## 1 · Ingesta: normalizar la entrada

**R1.** El sistema debe aceptar una lista de documentos de entrada (nombre y
contenido) y normalizarla a una lista de PDFs, conservando **el orden en que
llegan** y **el nombre del fichero de origen** de cada uno.

**R2.** CUANDO un documento de entrada es un ZIP, el sistema debe añadir a la
lista normalizada todos los PDF que contenga, recorriendo sus entradas en
**orden alfabético de ruta interna**, y descartar el resto de entradas
—directorios, ZIP anidados y ficheros que no sean PDF— dejando un aviso que
nombre cada una.

**R3.** SI un documento de entrada no es ni un PDF ni un ZIP, ENTONCES el
sistema debe descartarlo con un aviso que lo nombre y **seguir procesando el
resto de la remesa**.

**R4.** SI un PDF está cifrado o corrupto y no se puede abrir, ENTONCES el
sistema debe descartarlo con un aviso que lo nombre y **seguir procesando el
resto de la remesa**: un fichero roto no puede tumbar una remesa de 22
partes.

**R5.** SI la entrada no produce ni un solo PDF utilizable, ENTONCES el
sistema debe responder `400` con el motivo y la lista de avisos, sin trocear
nada.

**R6.** SI la entrada supera los límites declarados de la ingesta —número de
entradas del ZIP o tamaño total descomprimido—, ENTONCES el sistema debe
rechazarla con `413` y motivo, **sin descomprimir ni una entrada** (la
comprobación se hace sobre los tamaños declarados en el índice del ZIP).

## 2 · Troceado: dónde empieza un parte

**R7.** El sistema debe trocear cada PDF de remesa en documentos de **un
parte**; por defecto, **cada página es un parte**.

**R8.** CUANDO una página tiene pie reconocido y ese pie numera `Página N`
con **N ≥ 2**, el sistema debe tratarla como **continuación** del parte
anterior —añadirla a ese parte— y no abrir uno nuevo.

**R9.** CUANDO una página no tiene pie reconocido, o lo tiene con `N = 1`, o
no se le puede leer el número, el sistema debe **abrir un parte nuevo**. Es
la regla conservadora deliberada: trocear de más produce un parte a revisión
manual; fundir dos partes en un documento **pierde una incidencia**.

**R10.** SI la **primera** página de un PDF de remesa es una continuación
(`Página 2` sin `Página 1` delante), ENTONCES el sistema debe abrir un parte
con ella igualmente y marcar ese parte con un aviso de troceado: no hay parte
anterior al que engancharla y descartarla perdería un parte.

**R11.** MIENTRAS ninguna página de un PDF de remesa tenga capa de texto
útil, el sistema debe declarar para sus partes el modo de detección
`una_pagina_por_parte` —en vez de `por_pie_de_pagina`—, de forma que quien
lea el resultado sepa que en ese documento **el parte de dos hojas no se ha
podido detectar** y el troceado es «una página, un parte».

## 3 · Hash: reprocesar no duplica

**R12.** El sistema debe dar a cada parte troceado un hash **SHA-256 en
hexadecimal minúsculo**, calculado sobre el **contenido de sus páginas de
origen** (texto normalizado e imágenes incrustadas, en orden, con longitudes
delimitadas) y **no** sobre los bytes del PDF resultante.

**R13.** CUANDO la misma remesa se procesa dos veces, el sistema debe
producir exactamente los mismos hashes, en el mismo orden.

**R14.** CUANDO la misma remesa se entrega de dos formas —un PDF multi-parte,
y un ZIP con esos mismos partes como ficheros sueltos—, el sistema debe
producir **la misma lista de hashes en el mismo orden**.

**R15.** SI una página no tiene ni texto ni imágenes de las que calcular
huella (página en blanco), ENTONCES el sistema debe marcar ese parte con un
aviso que lo diga, porque su hash no distingue una página en blanco de otra.

## 4 · Endpoint `POST /api/split`

**R16.** CUANDO se hace `POST /api/split` con uno o más ficheros en
`multipart/form-data`, el sistema debe responder `200` con un JSON que
contenga, por cada parte y en orden: su `hash`, su fichero de `origen`, sus
`paginas_origen` (numeradas desde 1), su `modo_deteccion`, sus `avisos` y su
PDF en `contenido_b64`; más la lista de `avisos` de la remesa y el
`total_partes`.

**R17.** SI la petición no trae ningún fichero, ENTONCES el sistema debe
responder `400` con el motivo, sin procesar nada.

## 5 · Arquitectura y límite de alcance

**R18.** El sistema **no** debe interpretar el contenido del parte en esta
feature: la respuesta de `/api/split` no contiene ningún campo de negocio
—ni nº de incidencia, ni código de obra, ni firma, ni manuscritos—. Esos
campos los produce F-003.

**R19.** El sistema debe mantener el dominio puro: ningún módulo de
`services/postventa-api/domain/` importa `pymupdf`, `fitz`, `zipfile`,
`azure` ni ningún otro módulo de `infrastructure/`.

---

## Trazabilidad requisito → test

| Req | Test (nombre trazable) |
|---|---|
| R1 | `test_f002_r1_conserva_orden_y_nombre_de_origen` |
| R2 | `test_f002_r2_zip_aporta_sus_pdf_en_orden_alfabetico`, `test_f002_r2_zip_descarta_lo_que_no_es_pdf_con_aviso` |
| R3 | `test_f002_r3_entrada_que_no_es_pdf_ni_zip_se_descarta_con_aviso` |
| R4 | `test_f002_r4_pdf_corrupto_no_tumba_la_remesa` |
| R5 | `test_f002_r5_sin_pdf_utilizable_responde_400` |
| R6 | `test_f002_r6_zip_que_supera_el_limite_se_rechaza_sin_descomprimir` |
| R7 | `test_f002_r7_una_pagina_un_parte` |
| R8 | `test_f002_r8_pagina_2_es_continuacion_del_parte_anterior` |
| R9 | `test_f002_r9_sin_pie_reconocido_abre_parte_nuevo`, `test_f002_r9_pagina_1_abre_parte_nuevo` |
| R10 | `test_f002_r10_primera_pagina_continuacion_abre_parte_con_aviso` |
| R11 | `test_f002_r11_sin_capa_de_texto_el_modo_es_una_pagina_por_parte` |
| R12 | `test_f002_r12_el_hash_es_sha256_del_contenido_de_las_paginas`, `test_f002_r12_el_hash_no_depende_de_los_bytes_del_pdf_resultante` |
| R13 | `test_f002_r13_reprocesar_la_misma_remesa_da_los_mismos_hashes` |
| R14 | `test_f002_r14_zip_y_pdf_multiparte_dan_la_misma_lista_de_hashes` |
| R15 | `test_f002_r15_pagina_en_blanco_deja_aviso` |
| R16 | `test_f002_r16_split_devuelve_200_con_el_contrato` |
| R17 | `test_f002_r17_split_sin_ficheros_responde_400` |
| R18 | `test_f002_r18_la_respuesta_no_trae_campos_de_negocio` |
| R19 | `test_f002_r19_el_dominio_no_importa_infraestructura` |

Todos los tests usan **PDFs sintéticos generados en el propio test** (criterio
`acceptance` 4). Ninguno depende de `muestras/` ni de `docs/referencia/*.pdf`,
que no se versionan.

El criterio `acceptance` 2 —acertar el número de partes de la **remesa real de
Mirasierra**— es **verificación `MANUAL (humano)`**: ver `tasks.md`, T15.
