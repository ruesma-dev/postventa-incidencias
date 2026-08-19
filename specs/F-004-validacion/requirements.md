<!-- specs/F-004-validacion/requirements.md -->
# F-004 · Validación del parte y clasificación de la firma — Requisitos

> Notación EARS (`specs/SPECS.md`). Cada requisito se traduce a **>= 1 test
> trazable** `test_f004_rN_...`.
>
> **Ni un dato real en este documento.** Todos los valores de ejemplo están
> inventados (el DNI `00000000T` no es válido): los partes llevan DNI de
> clientes y esto se versiona en git.

## 0 · De dónde parte esta feature

F-004 consume lo que produce **F-003** y no lo modifica: un `ExtraccionParte`
con **nueve campos**, cada uno con `valor` (texto o vacío) y `confianza_pct`
(entero 0–100):

| Campo | Origen en el papel | Vino en la remesa real de Mirasierra (22 partes) |
|---|---|---|
| `promocion` | impreso | 22/22, confianza media ~99 |
| `codigo_obra` | impreso | 22/22, confianza media ~99 |
| `unidad` | impreso | 22/22, confianza media ~99 |
| `numero_incidencia` | impreso | 22/22, confianza media ~99 |
| `descripcion` | impreso | 22/22, confianza media ~99 |
| `numero_pagina` | impreso (pie) | 22/22, confianza media ~99 |
| `fecha_servicio` | manuscrito | **0/22** (el papel está en blanco, confirmado a ojo por el humano) |
| `dni_cliente` | manuscrito | **7/22** |
| `observaciones` | manuscrito | **2/22 (~9 %)** |

Esos recuentos son medidas del barrido manual de F-003 (2026-08-19). Son
recuentos, no valores: se pueden citar, y justifican por qué esta feature
**no exige** lo que el papel deja en blanco.

Lo que F-003 **no** produce y esta feature necesita: **qué hay en la casilla
de la firma del cliente**. Eso se lee aparte (ver `design.md` §2).

## 1 · Vocabulario que fijan estos requisitos

- **Clasificación de firma**: `humana` | `marca_simple` | `casilla_vacia` |
  `ilegible`. Es una **descripción** de lo que hay en la casilla, no un juicio
  sobre el parte.
- **Campos decisivos**: `codigo_obra` y `numero_incidencia`. Son los únicos
  campos de texto que deciden (`docs/ARCHITECTURE.md`, semántica 4 bis).
- **Legible**: un campo con valor no vacío **y** confianza declarada por
  encima del umbral.
- **Veredicto**: `apto` | `no_apto`.
- **Destino**: `archivo_y_cierre` | `cola_validacion_humana` |
  `revision_manual`.
  - `cola_validacion_humana` es la cola de la decisión (3) del humano: el
    parte está completo y firmado, pero trae observaciones y **una persona
    tiene que decidir** con la transcripción delante.
  - `revision_manual` es el destino de siempre (`docs/ARCHITECTURE.md` 3 y 5):
    el parte **no reúne los mínimos** para archivarse ni cerrarse y hay que
    volver al papel.
- **Motivo**: un código más un texto en castellano llano, para Posventa.

---

## 2 · Requisitos

### Lectura de la firma

**R1.** El sistema debe clasificar la firma del cliente en **exactamente una**
de estas cuatro etiquetas: `humana`, `marca_simple`, `casilla_vacia`,
`ilegible`.
→ `test_f004_r1_las_cuatro_etiquetas_de_firma`

**R2.** SI la lectura de la firma devuelve una etiqueta que no es ninguna de
las cuatro, o no devuelve etiqueta, ENTONCES el sistema debe clasificarla como
`ilegible` y dejar un aviso; **nunca** como `humana`.
→ `test_f004_r2_una_etiqueta_desconocida_es_ilegible`
→ `test_f004_r2_sin_etiqueta_es_ilegible_nunca_humana`

**R3.** CUANDO la lectura de la firma declara una confianza que no es un
entero de 0 a 100, el sistema debe sanearla con **la misma** regla que la
extracción (fuera de rango se ajusta al extremo, no numérica se deja en 0) y
dejar aviso.
→ `test_f004_r3_la_confianza_de_la_firma_se_sanea_igual_que_la_extraccion`

**R4.** El sistema debe pedir la clasificación de la firma con un **prompt
propio** (`firma_parte_es`) de `config/prompts.yaml`, **sin modificar** el
prompt de extracción `parte_posventa_es`.
→ `test_f004_r4_el_prompt_de_firma_existe_y_es_otro`
→ `test_f004_r4_el_prompt_de_extraccion_conserva_su_huella`

**R5.** El sistema debe resolver el **schema estructurado** que se le manda al
modelo a partir del nombre que declara el prompt, y ese nombre debe estar
declarado en el dominio.
→ `test_f004_r5_cada_prompt_declara_un_schema_conocido`
→ `test_f004_r5_el_schema_de_la_firma_tiene_su_unico_campo`

### El resultado de validar

**R6.** El sistema debe emitir, por cada parte, un **veredicto**, un
**destino** y una lista de **motivos**, cada motivo con su código y un texto
entendible por Posventa (sin jerga técnica, sin nombres de campo del código).
→ `test_f004_r6_cada_parte_sale_con_veredicto_destino_y_motivos`
→ `test_f004_r6_todos_los_motivos_tienen_texto_para_posventa`

**R7.** CUANDO el parte trae `codigo_obra` y `numero_incidencia` legibles,
firma `humana` y **ninguna** observación manuscrita, el sistema debe
declararlo `apto`, con destino `archivo_y_cierre` y **sin** motivos.
→ `test_f004_r7_el_parte_completo_y_firmado_sale_apto`

### La regla que decidió el humano: firmado no es conforme

**R8.** CUANDO el parte trae `observaciones` con texto no vacío, el sistema
debe declararlo `no_apto` **aunque la firma sea `humana`**, con el motivo
`observaciones_manuscritas`, y debe incluir en el resultado la
**transcripción literal** de esas observaciones y su confianza.
→ `test_f004_r8_un_parte_firmado_con_observaciones_no_es_conforme`
→ `test_f004_r8_el_resultado_lleva_la_transcripcion_para_quien_decide`

**R9.** MIENTRAS el **único** motivo del parte sea
`observaciones_manuscritas`, el destino debe ser `cola_validacion_humana`
(nunca `revision_manual`, y nunca se descarta el parte).
→ `test_f004_r9_solo_observaciones_manda_a_la_cola_de_validacion_humana`

**R10.** El sistema no debe juzgar el **contenido** de las observaciones:
cualquier texto no vacío produce el mismo motivo y el mismo destino, diga lo
que diga.
→ `test_f004_r10_el_contenido_de_la_observacion_no_cambia_el_veredicto`

> Interpretar ese contenido —separar la observación inocua de la que impide
> dar la reparación por buena— es **F-016**. Ningún test de F-004 depende de
> ello.

### Los mínimos para poder archivar y cerrar

**R11.** SI `codigo_obra` no es legible, o `numero_incidencia` no es legible,
ENTONCES el sistema debe declarar el parte `no_apto` con destino
`revision_manual`, y **nunca** `apto`.
→ `test_f004_r11_sin_codigo_de_obra_nunca_es_apto`
→ `test_f004_r11_sin_numero_de_incidencia_nunca_es_apto`

**R12.** El sistema debe considerar **no legible** un campo decisivo vacío
(vacío incluye «solo espacios») y también uno cuya confianza esté por debajo
del umbral declarado.
→ `test_f004_r12_un_campo_decisivo_en_blanco_no_es_legible`
→ `test_f004_r12_un_campo_decisivo_con_confianza_baja_no_es_legible`
→ `test_f004_r12_justo_en_el_umbral_el_campo_es_legible`

**R13.** SI la clasificación de la firma no es `humana`, ENTONCES el sistema
debe declarar el parte `no_apto` con el motivo `firma_no_humana` y destino
`revision_manual`; el texto del motivo debe distinguir la casilla vacía, la
marca simple y la ilegible.
→ `test_f004_r13_una_marca_simple_no_es_conformidad_del_cliente`
→ `test_f004_r13_la_casilla_vacia_no_es_conformidad_del_cliente`
→ `test_f004_r13_una_firma_ilegible_va_a_revision_manual`

> **R13 depende de D1, que el humano APLAZÓ a propósito el 2026-08-19**
> (`design.md` §7). **Se implementa tal y como está escrito** —opción 1—
> porque es lo que dice `docs/ARCHITECTURE.md` (semántica 3) y lo que exige
> `CHECKPOINTS.md` C3. No bloquea a nadie: el humano confirma o cambia a la
> opción 2 **con el resultado de T14 delante**, y T14 se adelanta a cuanto el
> endpoint de firma funcione.

**R14.** MIENTRAS la clasificación sea `humana` pero su confianza esté por
debajo del umbral, el sistema debe tratarla como `ilegible` (ante la duda
nunca se da por buena la conformidad).
→ `test_f004_r14_una_firma_humana_dudosa_se_trata_como_ilegible`

**R14 bis.** CUANDO R14 degrada una firma `humana` dudosa, el sistema debe
**publicar la etiqueta degradada**: tanto `ResultadoValidacion.clasificacion_firma`
como el campo `firma.clasificacion` del JSON de `/api/validar` deben decir
`ilegible`, **nunca** `humana`. Publicar `humana` junto a un destino de
revisión manual sería incomprensible para quien lo lea en Posventa.
→ `test_f004_r14bis_la_firma_degradada_se_publica_como_ilegible`
→ `test_f004_r14bis_el_json_de_validar_publica_la_etiqueta_degradada`

> **Resuelto por el humano el 2026-08-19** (decisión D4 de `design.md` §7).
> La lectura cruda del modelo no se pierde: sigue viajando en la respuesta de
> `POST /api/firma`, que es la entrada de `/api/validar`.

### Lo que NO se exige (y es deliberado)

**R15.** El sistema **no** debe exigir `dni_cliente`: un parte sin DNI, con lo
demás en orden, sale `apto`.
→ `test_f004_r15_un_parte_sin_dni_sale_apto`

**R16.** El sistema **no** debe exigir `fecha_servicio`, ni horas, ni nombre
del cliente, ni `promocion`, ni `unidad`, ni `descripcion`, ni
`numero_pagina`: ninguno de ellos, vacío, puede cambiar el veredicto.
→ `test_f004_r16_los_campos_no_decisivos_vacios_no_cambian_el_veredicto`

**R17.** El sistema **no** debe validar el formato del `numero_incidencia`
(ni la barra, ni la serie, ni el correlativo): mientras F-008 no confirme
contra el ERP qué es cada mitad de `RS26.08 – 0123`, exigir un formato
rechazaría partes buenos.
→ `test_f004_r17_no_se_exige_formato_al_numero_de_incidencia`

### Forma del resultado

**R18.** CUANDO un parte incumple varias reglas a la vez, el sistema debe
listar **todos** los motivos —no solo el primero— en el orden declarado:
código de obra, nº de incidencia, firma, observaciones.
→ `test_f004_r18_se_listan_todos_los_motivos_en_orden`

**R19.** MIENTRAS un parte tenga algún motivo distinto de
`observaciones_manuscritas`, el destino debe ser `revision_manual`, aunque
además traiga observaciones (el parte no se puede ni nombrar ni cerrar: no hay
nada que decidir todavía). La transcripción de las observaciones debe viajar
igualmente en el resultado.
→ `test_f004_r19_un_parte_incompleto_con_observaciones_va_a_revision_manual`

### Pureza y límites

**R20.** El sistema debe aplicar las reglas de validación como **dominio
puro**: sin red, sin base de datos, sin IA y sin consultar Sigrid.
→ `test_f004_r20_las_reglas_no_importan_infraestructura`
→ `test_f004_r20_validar_no_abre_ninguna_conexion`

**R21.** SI se pide validar un parte sin extracción o sin lectura de firma,
ENTONCES el sistema debe fallar con un error de dominio explícito y **no**
inventarse un veredicto.
→ `test_f004_r21_sin_extraccion_no_hay_veredicto`
→ `test_f004_r21_sin_lectura_de_firma_no_hay_veredicto`

**R22.** El sistema **no** debe comprobar contra Sigrid que la incidencia
exista ni que esté abierta: esa comprobación necesita red y es F-008/F-009.
→ `test_f004_r22_el_modulo_de_validacion_no_conoce_sigrid`

### Interfaz HTTP

**R23.** CUANDO llega `POST /api/firma` con el PDF de **un** parte, el sistema
debe responder `200` con `hash_parte`, `firma` (clasificación y confianza),
`traza` y `avisos`, y **ninguna clave más**; sin fichero responde `400`, con
un parte que no cabe `413` y con el proveedor caído `502`.
→ `test_f004_r23_el_endpoint_de_firma_devuelve_el_contrato`
→ `test_f004_r23_sin_fichero_es_400`
→ `test_f004_r23_un_parte_demasiado_grande_es_413`
→ `test_f004_r23_un_proveedor_caido_es_502`

**R24.** CUANDO llega `POST /api/validar` con el cuerpo de `/api/extraer` y el
de `/api/firma`, el sistema debe responder `200` con el veredicto, y **sin
llamar a ningún modelo**; SI el cuerpo no trae esas dos partes bien formadas,
ENTONCES debe responder `400` diciendo qué falta.
→ `test_f004_r24_validar_devuelve_el_veredicto_sin_llamar_al_modelo`
→ `test_f004_r24_un_cuerpo_incompleto_es_400`

### Datos personales y suite

**R25.** El sistema **no** debe escribir en el log la transcripción de las
observaciones, el DNI ni ningún valor leído del parte: se registran hash,
veredicto, destino, códigos de motivo y tiempos.
→ `test_f004_r25_el_log_no_lleva_observaciones_ni_dni`

**R26.** La suite de F-004 **no** debe hacer ni una llamada real a un modelo,
ni abrir red, ni leer `muestras/` ni ningún PDF con datos personales.
→ `test_f004_r26_la_suite_no_abre_red`
→ `test_f004_r26_ningun_test_lee_muestras`

---

## 3 · Trazabilidad con los criterios `acceptance` de la ficha

| `acceptance` de F-004 | Requisitos |
|---|---|
| La clasificación de firma distingue firma de aspa en las muestras reales | R1, R2, R13 — **NO demostrado por T14**, ver nota abajo |
| Un parte con observaciones NO es conforme y va siempre a la cola, con las observaciones transcritas | R8, R9 |
| Las observaciones son el único motivo de rechazo: ninguna otra regla manda un parte **a la cola** | R9, R19 (y D1 en `design.md` §7) |
| Un parte SIN DNI sale conforme | R15 |
| Un parte sin nº de incidencia o sin código de obra nunca queda apto | R11, R12 |
| No se exigen campos que la realidad deja en blanco | R16, R17 |
| Cada parte sale con veredicto y motivo, en texto entendible por Posventa | R6 |
| Las reglas son dominio puro y se prueban sin IA | R20, R21, R26 |
| `bash harness/init.sh` en verde | T18 |

### Nota sobre el primer criterio: qué demuestra T14 y qué no

T14 se ejecutó el 2026-08-19 sobre los 22 partes reales de la remesa de
Mirasierra (detalle en `tasks.md`). Resultado: **22/22 `humana`** con confianza
media **98,2**, y cero `marca_simple`, cero `casilla_vacia` y cero `ilegible`.

Ese dato **resuelve D1** —la regla estricta no manda a revisión manual ningún
parte de una remesa real— pero **no demuestra** este criterio de aceptación. En
la remesa no había ni un aspa ni una casilla vacía que distinguir, así que un
clasificador que respondiera `humana` a todo habría producido la misma salida.
R1, R2 y R13 cubren el lado del **dominio** —las cuatro etiquetas existen, lo
desconocido cae en `ILEGIBLE` y las tres etiquetas no humanas producen
`firma_no_humana` + `revision_manual`—, que es lo que la suite puede demostrar
sin IA; lo que queda sin medir es el **acierto del modelo** distinguiendo firma
de aspa.

Lo que falta es un **control negativo**: partes sintéticos con aspa y con
casilla vacía que el clasificador no etiquete `humana`. **El humano decidió el
2026-08-19 cerrar F-004 sin él y traspasarlo a F-015** (evaluador de prompts),
donde ya consta como criterio de aceptación propio en su ficha de
`harness/features.json`.
