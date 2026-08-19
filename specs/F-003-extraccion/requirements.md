<!-- specs/F-003-extraccion/requirements.md -->
# F-003 · Extracción multimodal del parte, manuscritos incluidos — Requisitos (EARS)

> Contrato de partida: la entrada `F-003` de `harness/features.json` (cinco
> criterios `acceptance`). Estos requisitos los desarrollan; no los amplían.
> Rigor declarado: **`critico`** (fase RED, cobertura, campaña de mutación con
> cero supervivientes, y verificaciones `MANUAL (humano)` con su comando
> exacto y su resultado real).
>
> **Decisiones del humano del 2026-08-18, ya incorporadas** (detalle en
> `progress/spec_F-003.md`): entra `numero_pagina` en el contrato (R2 bis),
> entra el endpoint `POST /api/extraer` (R17–R18), el campo de la unidad de
> posventa se llama **`unidad`**, y la ruta sensible del prompt **no** se
> declara aquí (es F-015).

## Alcance

F-003 hace **una cosa**: coger un **parte troceado** (lo que produce F-002) y
devolver **los campos del parte con una confianza por campo**, leídos por un
modelo multimodal que se elige por configuración.

Fuera de alcance, explícitamente (y vigilado por R7):

| Qué | De quién es |
|---|---|
| Decidir si el parte es apto, y clasificar la firma | **F-004** |
| Guardar nada en PostgreSQL | **F-005** |
| Nombrar el fichero y subirlo a SharePoint | **F-006** |
| Tocar Sigrid (leer o cerrar) | **F-008 / F-009** |
| **Reagrupar** el parte de dos hojas con el «Página N» | **F-014** |
| Evaluar el acierto del prompt contra partes reales | **F-015** |

> **Matiz importante sobre F-014.** F-003 **lee** el número de página del pie y
> lo devuelve (R2 bis), porque el modelo lo ve aunque el escaneo no tenga capa
> de texto. Pero **F-003 no reagrupa nada**: no une páginas, no altera
> `paginas_origen` y no toca el troceado de F-002. Leer es de esta feature;
> reagrupar es de F-014.

## Vocabulario

- **Parte troceado**: el `ParteTroceado` de F-002 (`domain/models/remesa.py`) —
  `hash`, `origen`, `paginas_origen`, `modo_deteccion`, `contenido` (PDF de una
  o dos páginas) y `avisos`. Es **la entrada** de esta feature y no se modifica
  aquí.
- **Campo del parte**: cada uno de los datos declarados en R1 y R2 bis.
- **Confianza**: entero `0–100` que el modelo declara para **cada** campo
  (`confianza_pct`, el mismo nombre que ya usan `partes` y `albaranes` en el
  ecosistema).
- **Bloque impreso / bloque manuscrito**: los dos bloques del papel, descritos
  en `docs/referencia/02_parte_de_trabajo.md`. Lo manuscrito es **dato de
  primera**: DNI y observaciones.
- **Traza de extracción**: proveedor, modelo, clave de prompt, versión del
  prompt y huella del prompt con los que se obtuvo un resultado.
- **Doble de prueba**: objeto de test que cumple un puerto (`ExtractorPort`,
  cliente del SDK) y devuelve respuestas simuladas. **Nunca** hay red.

---

## 1 · El contrato de la extracción

**R1.** El sistema debe extraer de un parte troceado **exactamente estos ocho
campos de contenido**, y ninguno más:

| Campo | Etiqueta en el papel | Bloque | Ejemplo (inventado) |
|---|---|---|---|
| `promocion` | Promoción | impreso | `15 VIVIENDAS UNIFAMILIARES EN MIRASIERRA(MADRID)` |
| `codigo_obra` | Código Obra | impreso | `0677` |
| `unidad` | Vivienda | impreso | `Viviendas Bloque Villa 5` |
| `numero_incidencia` | Nº Incidencia | impreso | `RS26.08/0123` |
| `fecha_servicio` | Fecha servicio | **manuscrito** | `05/08/26` |
| `descripcion` | Descripción | impreso | `Sellado de encuentro de falsos techos` |
| `dni_cliente` | Fdo. / DNI (columna izquierda) | **manuscrito** | `00000000T` |
| `observaciones` | Observaciones de reparación | **manuscrito** | `Se aprecia que se han hecho parcheados` |

> **`unidad` es la unidad de posventa.** El papel la imprime con la etiqueta
> «Vivienda» (`docs/referencia/02_parte_de_trabajo.md`) y el backlog la llamaba
> «chalet» (descripción de F-003 y `docs/ARCHITECTURE.md`). Se nombra `unidad`
> por decisión del humano del 2026-08-18: es el término que ya usa la estructura
> de archivo de Posventa (`PARTES INCIDENCIAS / <UNIDAD> / PARTES FIRMADOS`,
> F-013), así que el mismo concepto se llama igual en el código y en el archivo.
> No es un descuido: son tres nombres del mismo dato.
>
> `fecha_servicio` es la fecha **manuscrita** del bloque «SERVICIO REALIZADO Y
> CONFORME», no la fecha de impresión del pie.

**R2 bis.** El sistema debe extraer además el **número de página que el pie
impreso declara** (`numero_pagina`: `"1"`, `"2"`, … o `None` si el pie no se
lee), con su confianza como cualquier otro campo. El modelo multimodal **sí ve
ese pie** aunque el escaneo no tenga capa de texto, que es exactamente lo que
F-002 no pudo leer. **F-003 solo lo lee y lo devuelve**: quien lo use para
reagrupar el parte de dos hojas es **F-014**, y esta feature no une páginas ni
toca `paginas_origen`.

**R2.** El resultado debe contener **todos los campos declarados siempre** —los
ocho de R1 más el `numero_pagina` de R2 bis: **nueve claves**—, también los que
el parte deja en blanco. SI la respuesta del modelo omite un campo, ENTONCES el
sistema debe incluirlo con `valor = None` y `confianza_pct = 0`, y dejar un
aviso que lo nombre. Un campo que falta como clave rompería a F-004, y el papel
real deja en blanco fecha, horas, nombre y DNI en casi toda la remesa.

**R3.** El sistema debe acompañar **cada** campo de su `confianza_pct` entero
`0–100`, **incluidos los manuscritos** `dni_cliente` y `observaciones`.

**R4.** SI el modelo devuelve una confianza fuera de `0–100`, o no numérica,
ENTONCES el sistema debe ajustarla al rango (`< 0` → `0`, `> 100` → `100`, no
numérica → `0`) y dejar un aviso que nombre el campo. No se descarta el valor
por eso: una confianza mal formada no invalida lo leído, lo hace sospechoso.

**R5.** El sistema debe devolver los valores **tal y como los lee del parte**,
sin normalizar, reformatear ni deducir: `RS26.08/0123` conserva la barra y
`fecha_servicio` conserva el formato escrito a mano. La normalización a guion
para el nombre del fichero es F-006, y deducir un dato que no está en el papel
es inventarlo.

**R6.** El resultado debe traer la **traza** de cómo se obtuvo —`proveedor`,
`modelo`, `prompt_key`, `version_prompt` y `huella_prompt`— y el `hash` del
parte troceado al que corresponde, para que cualquier revisión posterior sepa
qué modelo y qué prompt produjeron ese dato.

**R7.** El resultado de F-003 **no** debe contener veredicto de validación,
clasificación de firma, nombre de fichero, ruta de SharePoint, identificador de
base de datos ni estado de Sigrid: el conjunto de claves del resultado es
exactamente el declarado en R1 + R2 bis + R6 + avisos.

## 2 · Los prompts viven fuera del código

**R8.** El sistema debe cargar el prompt —`system`, `task`, nombre del
`schema` y `version`— de `services/postventa-api/config/prompts.yaml`.
Ningún módulo de código debe contener el texto del prompt.

**R9.** SI el fichero de prompts no existe, no es un mapping en la raíz, o no
declara la clave pedida, ENTONCES el sistema debe fallar al construir el
repositorio de prompts con un error que nombre el fichero y las claves
disponibles, **antes** de llamar a ningún modelo. Llamar con un prompt vacío
produciría basura cara y silenciosa.

**R10.** El sistema debe calcular una **huella** del texto del prompt cargado
(`system` + `task`) y publicarla en la traza (R6), para que un cambio de
redacción sea detectable aunque nadie suba la `version` declarada.

## 3 · El proveedor se cambia por configuración

**R11.** El sistema debe elegir el adaptador de IA por configuración
—`IA_PROVIDER`, con `gemini` por defecto— y el modelo por `GEMINI_MODEL`, con
`gemini-3.7-flash` por defecto. Cambiar de proveedor o de modelo **no debe
tocar** el paso del pipeline, el dominio ni los puertos.

**R12.** SI `IA_PROVIDER` nombra un proveedor no soportado, o falta la
credencial del proveedor elegido, ENTONCES el sistema debe fallar al construir
el extractor con un mensaje que diga qué falta y qué proveedores hay, y **nunca
debe registrar ni devolver el valor de la credencial**.

**R13.** El paso de extracción debe funcionar con **cualquier** objeto que
cumpla `ExtractorPort` —se demuestra ejecutándolo con un doble—, y ningún
módulo de `services/postventa-api/domain/` ni de
`services/postventa-api/application/` debe importar `google`, `google.genai`,
`yaml`, `tenacity` ni nada de `infrastructure/`.

## 4 · La llamada al modelo, cuando el mundo falla

**R14.** CUANDO la llamada al modelo falla con un error transitorio, el sistema
debe reintentarla con espera exponencial hasta el número de intentos
configurado, y devolver el resultado si un reintento tiene éxito.

**R15.** SI se agotan los reintentos, o la respuesta no es JSON válido, o no
encaja con el schema declarado, ENTONCES el sistema debe levantar
`ExtraccionFallida` con el motivo y **sin volcar el contenido del parte en el
mensaje ni en el log** (lleva datos personales). Los errores **no** transitorios
—credencial inválida, petición mal formada— no se reintentan.

**R16.** SI el parte supera el tamaño máximo admitido para enviarlo en línea al
modelo, ENTONCES el sistema debe rechazarlo con motivo **sin llamar al
modelo**.

## 5 · Endpoint `POST /api/extraer`

**R17.** CUANDO se hace `POST /api/extraer` con el PDF de **un** parte en
`multipart/form-data`, el sistema debe responder `200` con un JSON que
contenga: el `hash` del parte, los **nueve** `campos` con su `valor` y su
`confianza_pct`, la `traza` (R6) y la lista de `avisos`.

**R18.** SI la petición no trae ningún fichero, ENTONCES el sistema debe
responder `400` con el motivo **sin llamar al modelo**; SI la extracción falla
(R15), ENTONCES debe responder `502` con el motivo, sin devolver el contenido
del parte; y SI el parte supera el tamaño máximo (R16), ENTONCES debe responder
`413`, **no** `502`.

> El `413` (*Payload Too Large*) es deliberado y es el único código correcto
> para R16: nadie ha fallado río arriba, la petición es demasiado grande y quien
> puede arreglarlo es el cliente. Un `502` diría lo contrario —que el proveedor
> de IA se rompió— cuando al modelo **ni se le ha llamado**. Este requisito,
> `design.md` §4.5 y la tarea T16 dicen los tres lo mismo: `400` / `413` / `502`.

## 6 · Ni una llamada real a la IA en la suite

**R19.** La suite del servicio **no debe poder** abrir una conexión de red:
cualquier intento durante un test falla de forma explícita. Los tests usan
dobles y respuestas simuladas construidas en el propio test, con **datos
inventados**, y ninguno lee `muestras/` ni `docs/referencia/*.pdf`, que no se
versionan.

---

## Trazabilidad requisito → test

| Req | Test (nombre trazable) |
|---|---|
| R1 | `test_f003_r1_los_ocho_campos_de_contenido_estan_declarados` |
| R2 bis | `test_f003_r2bis_el_numero_de_pagina_se_lee_del_pie`, `test_f003_r2bis_la_extraccion_no_reagrupa_paginas` |
| R2 | `test_f003_r2_un_campo_ausente_sale_vacio_con_confianza_cero_y_aviso`, `test_f003_r2_el_resultado_siempre_trae_las_nueve_claves` |
| R3 | `test_f003_r3_cada_campo_trae_su_confianza`, `test_f003_r3_los_manuscritos_tambien_traen_confianza` |
| R4 | `test_f003_r4_confianza_fuera_de_rango_se_ajusta_con_aviso`, `test_f003_r4_confianza_no_numerica_pasa_a_cero_con_aviso` |
| R5 | `test_f003_r5_el_numero_de_incidencia_conserva_la_barra`, `test_f003_r5_la_fecha_manuscrita_no_se_reformatea` |
| R6 | `test_f003_r6_el_resultado_trae_traza_y_hash_del_parte` |
| R7 | `test_f003_r7_el_resultado_no_trae_veredicto_ni_firma_ni_rutas` |
| R8 | `test_f003_r8_el_prompt_se_carga_del_yaml`, `test_f003_r8_ningun_modulo_incrusta_el_texto_del_prompt` |
| R9 | `test_f003_r9_yaml_inexistente_falla_nombrando_el_fichero`, `test_f003_r9_clave_desconocida_falla_listando_las_disponibles` |
| R10 | `test_f003_r10_la_huella_del_prompt_cambia_si_cambia_el_texto` |
| R11 | `test_f003_r11_la_fabrica_devuelve_gemini_por_defecto`, `test_f003_r11_el_modelo_sale_de_gemini_model` |
| R12 | `test_f003_r12_proveedor_no_soportado_falla_listando_los_validos`, `test_f003_r12_sin_credencial_falla_sin_revelarla` |
| R13 | `test_f003_r13_el_paso_funciona_con_un_doble_del_puerto`, `test_f003_r13_dominio_y_aplicacion_no_importan_proveedores` |
| R14 | `test_f003_r14_un_error_transitorio_se_reintenta_y_acaba_bien` |
| R15 | `test_f003_r15_reintentos_agotados_levantan_extraccion_fallida`, `test_f003_r15_json_invalido_levanta_extraccion_fallida`, `test_f003_r15_error_no_transitorio_no_se_reintenta`, `test_f003_r15_el_mensaje_de_error_no_lleva_el_contenido_del_parte` |
| R16 | `test_f003_r16_parte_demasiado_grande_no_llama_al_modelo` |
| R17 | `test_f003_r17_extraer_devuelve_200_con_el_contrato` |
| R18 | `test_f003_r18_extraer_sin_fichero_responde_400`, `test_f003_r18_extraccion_fallida_responde_502`, `test_f003_r18_parte_demasiado_grande_responde_413` |
| R19 | `test_f003_r19_la_suite_no_puede_abrir_conexiones_de_red` |

Todos los tests usan **respuestas de IA simuladas construidas en el propio
test** (criterio `acceptance` 4). Ninguno depende de `muestras/` ni de
`docs/referencia/*.pdf`, y ninguna respuesta de ejemplo —ni en los tests ni en
esta spec— lleva datos personales reales: todos los DNI, nombres y textos son
inventados.

**Verificación `MANUAL (humano)`**: que el modelo real acierte de verdad sobre
partes reales **no lo puede demostrar la suite**. Va como tarea manual con su
comando exacto en `tasks.md` (**T17** y **T18**), y su resultado real se anota
en `progress/current.md`. Medir ese acierto de forma sistemática y repetible es
**F-015**, no esta feature.
