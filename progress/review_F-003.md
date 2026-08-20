<!-- progress/review_F-003.md -->
# F-003 · Extracción multimodal del parte — Informe de review

**Veredicto: APPROVED**

Rama `feature/F-003-extraccion`, base real `chore/postreview-F-002`
(merge-base `05146ef`). Arnés **1.5.2**. Revisión hecha contra
`specs/F-003-extraccion/{requirements,design,tasks}.md` (spec aprobada por el
humano, con las seis correcciones), `CHECKPOINTS.md`, `docs/CONVENTIONS.md` y
`docs/ARCHITECTURE.md`.

**El veredicto aprueba el trabajo del implementer, no el cierre de la
feature.** F-003 no puede pasar a `done` hasta que el humano ejecute **T17** y
**T18** (ver §7). Eso es diseño de la spec, no un defecto: se listan como
pendiente, no como cambio requerido.

**Cambios requeridos: ninguno.** Tres observaciones menores en §6, todas
documentales y ninguna bloqueante.

---

## 1 · Nivel de rigor y puertas que exige

`harness/features.json` declara `"rigor": "critico"` para F-003. Es el nivel
más exigente de `harness/rigor.json`, así que se le exige **todo**:

| Puerta | Exigida | Resultado |
|---|---|---|
| Fase RED en los requisitos centrales | sí | **[x]** verificada contra el historial de git, no solo contra el informe |
| Cobertura de las líneas cambiadas ≥ 80 % | sí | **[x]** 100,0 % (631/631), **recalculada por el reviewer** |
| Campaña de mutación | sí | **[x]** 127 mutantes, **campaña reejecutada entera** |
| Cero supervivientes | sí (`critico`) | **[x]** 0 supervivientes en la campaña del implementer **y** en la del reviewer |
| Verificaciones `MANUAL (humano)` con comando exacto | sí (`critico`) | **[x]** T17 y T18 documentadas, **sin ejecutar y sin marcar** (correcto) |
| Sección «Evidencias» con los cuatro números | sí | **[x]** `progress/impl_F-003.md`, §Evidencias |

## 2 · Verificación independiente de las puertas

### 2.1 · `bash harness/init.sh` — ejecutado tal cual, sin pipes ni tail

Primera línea: `[OK] Arnés v1.5.2 (2026-08-18)`. Exit code 0. Todo en `[OK]`:
compileall, ruff sin avisos, 16 tests de la raíz, 207 del servicio `api`,
`PUERTA COBERTURA: 100.0% de 631 líneas cambiadas cubiertas (631/631, umbral
80%, nivel critico)`, rama correcta, una sola feature `in_progress`.

### 2.2 · Cobertura — recalculada, y sin ficheros «no medidos»

No me he fiado del número del informe. He cruzado a mano el `coverage.json` de
la raíz y el del servicio (fusionados con `harness.cobertura.fusionar_coberturas`)
contra `harness.alcance.alcance_de_feature('F-003', base='dev')`:

```
base dev -> 27 ficheros, 1912 líneas de diff
TOTAL 631 / 631 = 100.0 %
```

**Los 27 ficheros del alcance aparecen en el informe de cobertura: ninguno sale
«no medido»**, que es exactamente por donde se colaría un 100 % falso (un
módulo nuevo que ningún test importa no aparece en `coverage.json` y el
mecanismo de `lineas_ejecutables` lo contaría como no cubierto). Desglose por
fichero: todos a `n/n`, ninguna línea en `SIN CUBRIR`. Los tres `__init__.py`
de paquetes nuevos aportan 0 líneas ejecutables, que es lo correcto.

### 2.3 · Mutación — recálculo puro **y** campaña reejecutada

**Recálculo puro** (sin ejecutar la suite):

- `harness.alcance.alcance_de_feature('F-003')` → **27 ficheros, 1912 líneas**.
  Coincide con la tabla de `progress/mutacion_F-003.md`.
- `harness.mutacion.generar_mutantes` sobre esos ficheros → **127 mutantes**.
  Coincide con «Mutantes generados: 127».

**Reejecución completa de la campaña** (exigencia estrenada del arnés 1.5.2).
El informe declara «Tiempo total 103,7 s», por debajo del umbral de 5 minutos,
así que la campaña se ha vuelto a lanzar entera:

```
python -m harness.mutacion --feature F-003 \
  --salida C:/Users/pgris/AppData/Local/Temp/review-f003/mutacion_F-003_reviewer.md
```

| Métrica | Informe del implementer | Campaña del reviewer |
|---|---|---|
| Mutantes generados | 127 | **127** |
| Mutantes evaluados | 127 | **127** |
| Muertos | 127 | **127** |
| Supervivientes | 0 | **0** |
| Timeouts | 0 | **0** |
| Tiempo total | 103,7 s | 101,0 s |

Los cuatro totales cuadran. **Los muertos están comprobados, no solo
contados.** La salida se escribió **fuera de `progress/`** (directorio temporal
del sistema), así que no se ha pisado el informe del implementer, y
**`git status` queda vacío** después de la campaña: el árbol está limpio.

Comprobación de control del «cero supervivientes»: la campaña no declara cero
mutantes, así que no aplica la prueba de exclusión por alcance. He muestreado
mutantes reales de la traza (`gemini.py:45` sobre `CODIGOS_TRANSITORIOS`,
`gemini.py:156` sobre el timeout en milisegundos, `fabrica.py:33`
`or` → `and`, `prompts_yaml.py:20` `parents[2]` → `parents[3]`): existen, con
su operador y su texto original→mutado, y todos mueren.

### 2.4 · Fase RED — contrastada contra el historial, no contra el informe

Las ocho tareas RED (T2, T4, T6, T7, T9, T11, T13, T15) traen su **salida
literal** en `progress/impl_F-003.md`. He verificado commit a commit que en el
commit RED **está el test y no está el módulo de producción**:

| Tarea | Commit RED | Ficheros del commit | Módulo de producción |
|---|---|---|---|
| T2 | `b21f7fc` | solo `tests/test_f003_arquitectura.py` | `conftest.py` existía de F-001, **sin** la guardia `sin_red` (0 coincidencias) |
| T4 | `0ee8866` | solo `tests/utiles_ia.py` + test | `domain/models/extraccion.py` **no existía** |
| T6 | `6a78ea1` | test + la entrada nueva de la tupla | `numero_pagina` **no estaba** en `extraccion.py` del commit anterior |
| T7 | `10ec228` | solo el test | `infrastructure/prompts/prompts_yaml.py` **no existía** |
| T9 | `1cfa1da` | solo el test | `application/pipelines/paso_extraccion.py` **no existía** |
| T11 | `8969779` | solo el test | `infrastructure/llm/gemini.py` **no existía** |
| T13 | `2d07d51` | solo tests | `infrastructure/llm/fabrica.py` **no existía** |
| T15 | `4df3f69` | solo el test | `interface_adapters/api/extraer.py` **no existía** |

T6 es «RED + verde» en un commit **porque así lo manda la propia tarea**, y su
traza en rojo está pegada. Los dos guardianes de T13 (`r13` de imports y `r8`
del prompt incrustado) no tienen código de producción cuyo fallo enseñar: el
implementer aplicó el mecanismo que `CHECKPOINTS.md` C4 bis contempla —romper
lo vigilado en una **copia aislada** (`%TEMP%`, nunca el árbol real) y pegar la
traza—, con dos violaciones inyectadas y sus dos `AssertionError`. Correcto.

**Tests añadidos en T20 (los que nacen de la mutación).** Por naturaleza no
tienen fase RED previa. El implementer **lo dice explícitamente** en
`progress/impl_F-003.md` («Nota sobre la fase RED de los tests añadidos en
T20»), y lo justifica bien: son endurecimiento, no funcionalidad, y su prueba
de que muerden es que la campaña pasó de 23 supervivientes a 0. He verificado
además lo que hace falsa esa justificación si no se cumple: **los cuatro
commits de T20 (`7c1201d`, `9b0b956`, `b2366e1`, `f7cc39d`) tocan solo ficheros
de test y `progress/`, ni una línea de producción**. Los supervivientes se
mataron con tests, no ablandando el código.

Merece quedar escrito el análisis del vigesimocuarto superviviente: un test
parametrizado con `sorted(CODIGOS_TRANSITORIOS)`, es decir, alimentado por la
constante que vigilaba. Al borrar el `502` de la constante desaparecía el caso
de prueba y la campaña aplaudía la mutación. Está corregido (los seis códigos
escritos a mano, más un test que comprueba que constante y lista coinciden) y
la lección vale para cualquier feature.

### 2.5 · Trazabilidad requisito → test

Los **35** tests nombrados en la tabla de trazabilidad de `requirements.md`
existen y se recogen: crucé la tabla contra `pytest --collect-only`.
**Faltan: ninguno.** 207 tests pasan (72 de ellos `f003_*`; el informe habla de
112 contando parametrizaciones).

| Req | Test que lo cubre (existe y pasa) |
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
| R15 | `test_f003_r15_reintentos_agotados_levantan_extraccion_fallida`, `test_f003_r15_json_invalido_levanta_extraccion_fallida`, `test_f003_r15_error_no_transitorio_no_se_reintenta`, `test_f003_r15_el_mensaje_de_error_no_lleva_el_contenido_del_parte`, `test_f003_r15_el_log_no_lleva_ni_el_parte_ni_lo_extraido` |
| R16 | `test_f003_r16_parte_demasiado_grande_no_llama_al_modelo` |
| R17 | `test_f003_r17_extraer_devuelve_200_con_el_contrato` |
| R18 | `test_f003_r18_extraer_sin_fichero_responde_400`, `test_f003_r18_extraccion_fallida_responde_502`, `test_f003_r18_parte_demasiado_grande_responde_413` |
| R19 | `test_f003_r19_la_suite_no_puede_abrir_conexiones_de_red` |

## 3 · Los siete puntos donde esta feature se podía haber roto en silencio

### 3.1 · Ni una llamada real a la IA en la suite — **correcto**

`services/postventa-api/tests/conftest.py:29-56`: fixture `sin_red`,
`autouse=True`, `scope="session"`, que sustituye `socket.socket.connect` por
un `RuntimeError` explícito y lo restaura al final. Está en el `conftest.py`
raíz de `tests/`, así que **cubre la suite entera del servicio**; no hay marca,
variable de entorno ni flag que lo desactive. `ssl.SSLSocket` hereda de
`socket.socket` y su `connect` acaba llamando al parcheado, así que HTTPS
tampoco escapa. `test_f003_r19_la_suite_no_puede_abrir_conexiones_de_red`
(`tests/test_f003_arquitectura.py:78`) comprueba que muerde, y usa
TEST-NET-1 (`192.0.2.1`, RFC 5737) para no depender de la red de quien ejecuta.

**Es la variante principal de `design.md` §6.3, no la B ni una tercera vía.**
El implementer lo declara en su decisión 5 («No hizo falta la variante B: la
guardia no rompió ni pytest ni la cobertura») y se comprueba en el código: no
hay parcheo de `genai.Client` en el `conftest`. El único módulo que importa
`google` fuera de producción es `tests/utiles_ia.py`, que es lo que la propia
variante B habría exigido.

### 3.2 · Datos personales — **ninguno, buscado activamente**

Barrido sobre el diff completo de la rama (`git diff chore/postreview-F-002...HEAD`),
sobre `progress/*.md` y sobre el historial (`git log --all --diff-filter=A`),
con estos patrones:

| Patrón | Resultado |
|---|---|
| `[0-9]{8}[- ]?[A-Za-z]` (DNI/NIE) | solo `00000000T`, DNI inválido y declarado inventado |
| `[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}` (correos) | ninguno (solo decoradores `@app.route`, `@pytest.mark`) |
| `\b[6-9][0-9]{8}\b` (teléfonos) | ninguno |
| `\.pdf$` en ficheros añadidos al historial | **ninguno**: ni un parte escaneado ha entrado en git, en ninguna rama |
| `MIRASIERRA` | solo el nombre comercial de la promoción, dato de negocio ya presente en la spec aprobada; no hay valores extraídos del parte real |

En el código, la prohibición está **probada**, no solo escrita:
`infrastructure/llm/gemini.py:160-168` registra modelo, clave y huella del
prompt, bytes y segundos —nunca el contenido ni la respuesta cruda—;
`gemini.py:137-141` construye el motivo de `ExtraccionFallida` con el **tipo**
del error y su código, nunca con el `str(error)` del SDK (que arrastra el
cuerpo del proveedor). Lo vigilan
`test_f003_r15_el_mensaje_de_error_no_lleva_el_contenido_del_parte` y
`test_f003_r15_el_log_no_lleva_ni_el_parte_ni_lo_extraido`, este último con
`caplog` a nivel DEBUG: un `log.debug("respuesta: %s", texto)` puesto «para
depurar» rompe la suite.

Ningún fixture lee `muestras/` ni `docs/referencia/*.pdf`: todas las respuestas
se construyen en el test con `tests/utiles_ia.py`.

### 3.3 · Credenciales — **ninguna**

Ni en código, ni en tests, ni en informes, ni en `progress/`. Los tests usan
`api_key="no-es-una-credencial"`. `git ls-files` no devuelve ningún `.env`
(solo `.env.example`, con placeholders) y el historial completo tampoco.
`infrastructure/llm/fabrica.py:33-39` exige la credencial **recortada** y su
mensaje nombra la variable `GEMINI_API_KEY`, jamás su valor;
`test_f003_r12_sin_credencial_falla_sin_revelarla` lo fija. La credencial es
`None` por defecto en `Ajustes` a propósito, para que `/health` y la suite
arranquen sin ella.

### 3.4 · F-003 lee `numero_pagina` pero NO reagrupa — **correcto**

`numero_pagina` aparece en producción en exactamente tres sitios: la entrada de
`CAMPOS_DEL_PARTE` (`domain/models/extraccion.py:40`), su comentario y la línea
del prompt (`config/prompts.yaml:62`). **No hay reagrupación, ni ganchos, ni
banderas, ni código muerto preparando F-014.** El campo viaja por el mismo
camino que los otros ocho, sin ninguna rama propia. `paginas_origen` solo se
toca en `interface_adapters/api/extraer.py:70` para declararlo **vacío** (no se
deduce), y `test_f003_r2bis_la_extraccion_no_reagrupa_paginas` comprueba que
leer `numero_pagina = "2"` no altera `paginas_origen` ni `modo_deteccion`. Las
funciones `_agrupar_en_partes` / `es_continuacion` que aparecen al buscar son
de F-002 y **no las toca el diff**.

### 3.5 · Límite de alcance de la respuesta — **fijado por test**

`test_f003_r7_el_resultado_no_trae_veredicto_ni_firma_ni_rutas`
(`tests/test_f003_paso_extraccion.py:189`) hace lo que hay que hacer: mete en
la respuesta simulada tres claves de otras features (`veredicto`,
`firma_valida`, `nombre_fichero`) y comprueba que **el conjunto exacto** de
claves sigue siendo `CAMPOS_DEL_PARTE`, y que los campos del dataclass
`ExtraccionParte` son exactamente `{hash_parte, campos, traza, avisos}`.
`tests/test_f003_extraer_http.py:34` fija además el conjunto de claves del JSON
del endpoint. No hay ni un campo de negocio de F-004, F-005 ni F-006.

### 3.6 · Modelo por defecto y afirmaciones sobre el ecosistema — **correcto**

`config/settings.py`: `gemini_model` por defecto **`gemini-3.7-flash`**
(`GEMINI_MODEL`), y `ia_proveedor` por defecto `gemini` (`IA_PROVIDER`). Lo
fijan `test_f003_r11_la_fabrica_devuelve_gemini_por_defecto` y
`test_f003_r11_los_valores_por_defecto_de_los_ajustes_de_ia`.

**Y la afirmación vieja se ha borrado donde estaba**: la tabla de sistemas
externos de `docs/ARCHITECTURE.md` decía `Gemini (gemini-2.5-flash)` y ahora
dice solo `Gemini`, remitiendo a `IA_PROVIDER` / `GEMINI_MODEL`. No queda en el
repositorio ninguna afirmación sobre qué versión de modelo corre en otro
proyecto del ecosistema, que es lo que `azure-apps` no fija.

### 3.7 · «chalet» → `unidad` — **alineado**

`docs/ARCHITECTURE.md`, paso 3 del pipeline: el campo se nombra **`unidad`** y
se explica que el papel lo imprime «Vivienda» y el backlog lo llamaba «chalet»
—tres nombres del mismo dato, uno solo en el código—. `CAMPOS_DEL_PARTE` usa
`unidad`, y `test_f003_r1_...` afirma `"chalet" not in CAMPOS_DEL_PARTE`. La
mención restante en `docs/ARCHITECTURE.md:24` (`CHALET XX - Nº INCIDENCIA`)
describe **el proceso manual de hoy**, no el modelo de datos: es correcta y no
debe tocarse.

## 4 · Arquitectura, convenciones y alcance de ficheros

- **Hexagonal respetada.** `domain/` y `application/` no importan `google`,
  `yaml`, `tenacity`, `azure` ni `infrastructure`; lo comprueba con `ast`
  `test_f003_r13_dominio_y_aplicacion_no_importan_proveedores`, que además
  falla si el recorrido no encuentra ningún módulo (no puede aprobar en vacío).
  El SDK vive en **un solo fichero**, `infrastructure/llm/gemini.py`. La
  composición está en el punto de entrada (`interface_adapters/api/extraer.py`),
  no dentro del paso.
- **El prompt vive solo en el YAML.** `test_f003_r8_ningun_modulo_incrusta_el_texto_del_prompt`
  saca las frases del propio `config/prompts.yaml` en tiempo de ejecución —el
  test no las lleva escritas— y comprueba que ningún `.py` del servicio las
  contiene. Sigue valiendo cuando se reescriba el prompt.
- **Ficheros tocados = los previstos.** Los 23 ficheros añadidos y los 9
  modificados coinciden con `design.md` §2 y §3. Ni uno más. Nada de F-002
  (`remesa.py`, `paso_troceado.py`, `split.py`…) se ha modificado, como manda
  §12.
- **Convenciones.** Los 24 ficheros nuevos/modificados llevan su ruta relativa
  en la primera línea. Sin `print()` de depuración, sin TODO/FIXME, sin
  secretos. `ruff` sin avisos. Todo en español.
- **Dependencias.** `google-genai>=0.3`, `pyyaml>=6.0`, `tenacity>=8.2,<10.0`:
  exactamente las tres previstas en `design.md` §7, ni una más. Quedan
  pendientes de aprobación del humano, ya anotadas en `progress/current.md`.
- **Sin SQL, sin red, sin SharePoint, sin Sigrid.** Confirmado.
- **Códigos HTTP.** `function_app.py`: 400 sin fichero (sin llamar al modelo),
  **413** para `ParteDemasiadoGrande` y 502 para `ExtraccionFallida`. Los tres
  con test. R18, `design.md` §4.5 y T16 dicen lo mismo, y el código también.

## 5 · Recorrido de CHECKPOINTS.md

### C1 — El arnés está completo y en verde

- [x] `bash harness/init.sh` termina con exit code 0 (`Arnés v1.5.2`).
- [x] Existen los siete documentos obligatorios.

### C2 — El estado es coherente

- [x] Una sola feature `in_progress` (F-003).
- [x] Rama `feature/F-003-extraccion`, la de la feature en curso.
- [x] `progress/current.md` describe solo la sesión activa (con la observación
      O2 de §6: una línea suya se ha quedado obsoleta).
- [x] Ninguna feature ha pasado a `done` en esta rama, así que no hay resumen
      que exigir en `history.md`.

### C3 — El código respeta arquitectura y convenciones

- [x] Hexagonal respetada, adaptadores solo en `infrastructure/`.
- [x] Primera línea de cada fichero con su ruta relativa.
- [x] Sin `print()`, sin TODOs, sin secretos, sin dependencias no previstas.
- [x] La unidad de trabajo es el **parte**: `POST /api/extraer` procesa **un**
      parte por llamada, como decidió `docs/ARCHITECTURE.md`.
- N/A · Nada se archiva ni se cierra: F-003 no archiva ni cierra nada
  (SharePoint es F-006, Sigrid F-008/F-009). **Justificación**: fuera del
  alcance declarado en `requirements.md` y vigilado por R7.
- [x] Lo manuscrito no se descarta: `CAMPOS_MANUSCRITOS` es conocimiento del
      dominio, y el prompt manda extraer DNI y observaciones como «dato de
      primera».
- N/A · «Firmado no es conforme»: la regla es de **F-004**. **Justificación**:
  F-003 no juzga la firma (R7), y el prompt lo prohíbe explícitamente. Lo que
  F-003 sí hace es dejar `CAMPOS_MANUSCRITOS` en el dominio para que F-004
  aplique la regla sin preguntarle a la IA.
- N/A · «Reprocesar no duplica»: el hash lo produce **F-002** y F-003 lo
  transporta sin tocarlo (`ExtraccionParte.hash_parte`). **Justificación**:
  esta feature no persiste nada (F-005).
- N/A · Estados de Sigrid: F-003 no habla con Sigrid. **Justificación**: fuera
  de alcance (F-008/F-009); el diff no contiene ni una referencia.
- [x] Ningún parte escaneado ni PDF con datos personales ha entrado en git:
      comprobado con `git log --all --diff-filter=A`, no solo con el árbol.

### C3 bis — Documentos que entran de fuera

**N/A justificado**: el diff de F-003 **no añade ni modifica ningún fichero de
`docs/referencia/`** (`git diff --name-only ... -- docs/referencia/` sale
vacío). El barrido de datos sensibles se ha hecho igualmente sobre todo el
diff y sobre `progress/`, con los patrones de §3.2.

### C4 — La verificación es real

- [x] Cada requisito EARS tiene ≥ 1 test trazable y todos pasan (§2.5).
- [x] Los unit tests no tocan red ni BBDD: la guardia lo hace **imposible**,
      no improbable (§3.1).
- [x] Las `MANUAL (humano)` están en `progress/current.md` con su comando
      exacto, pendientes de que las ejecute el humano.

### C4 bis — El rigor declarado se cumple

- [x] La feature declara `rigor: "critico"`, valor válido.
- [x] **Fase RED**: traza real pegada para las ocho tareas RED, verificada
      contra el historial de git (§2.4). El caso «el entregable es el propio
      test» se resolvió rompiendo lo vigilado en copia aislada, como manda el
      checkpoint.
- [x] **Cobertura**: `[OK]` 100,0 % (631/631), recalculada por el reviewer y
      sin ficheros «no medidos» (§2.2).
- [x] **Mutación**: `progress/mutacion_F-003.md` existe, generado por la
      herramienta, con totales **verificados de forma independiente**: alcance
      (27 ficheros / 1912 líneas) y 127 mutantes recalculados con
      `harness.alcance` y `harness.mutacion.generar_mutantes` (§2.3).
- [x] **Los muertos están comprobados, no solo contados**: campaña
      **reejecutada entera** (103,7 s declarados < 5 min), salida fuera de
      `progress/`, cuatro totales coincidentes, árbol limpio después (§2.3).
- [x] Cero supervivientes, ninguna sección de análisis en `PENDIENTE`.
- [x] Sección «Evidencias» con los cuatro números en `progress/impl_F-003.md`.
- [x] Ningún punto marcado N/A.

### C4 ter — Verificaciones extra por rutas sensibles

**N/A**: este repositorio **no tiene `harness/rutas_sensibles.json`**, que es
el caso mayoritario y no exige justificación. Consta que es deliberado: la
decisión D3 del humano manda declarar la ruta sensible de `config/prompts.yaml`
**cuando exista el evaluador** (F-015), no antes, porque una verificación
declarada cuyo comando nadie puede ejecutar es protección falsa. Mientras
tanto el hueco lo tapa T18.

### C5 — La sesión se cerró bien

- [ ] **`tasks.md` con todas las tareas `[x]`**: 19 de 21 lo están. **T17 y
      T18 siguen `[ ]` a propósito**, marcadas `PENDIENTE DEL HUMANO`. Este
      checkbox **no se puede marcar hasta que el humano las ejecute**, y por
      eso F-003 no puede pasar a `done` todavía. **No es un defecto del
      implementer**: marcarlas habría sido declarar hecho lo que no se ha
      hecho, y eso sí sería motivo de rechazo. Ver §7.
- [x] Un commit `F-003 Tn: ...` por tarea (24 commits en la rama, incluidos los
      cuatro de T20 y dos de ajuste de imports, todos con el prefijo correcto).
- [x] Sin ficheros temporales ni artefactos sin trackear: `git status` vacío,
      también tras mi reejecución de la campaña.
- [x] `features.json` refleja el estado real: F-003 sigue `in_progress`, que es
      la verdad mientras T17 y T18 no estén hechas.

## 6 · Observaciones menores (ninguna bloquea)

**O1 · Una afirmación inexacta sobre cuándo se instala la guardia de red.**
`services/postventa-api/tests/conftest.py:38-40` y la decisión 5 de
`progress/impl_F-003.md` dicen que se instala a mano en vez de con
`monkeypatch` porque la guardia «tiene que estar puesta también durante la
**recogida** de tests». Una fixture `autouse` de alcance sesión tampoco se
ejecuta durante la recogida: pytest la monta en el *setup* del primer test, ya
recogida la suite. El motivo de fondo sigue siendo bueno y suficiente
(`monkeypatch` es de alcance función y no cubriría fixtures de sesión ni la
sesión entera), y **la protección funciona**: solo sobra media frase. Si
alguien quisiera cubrir de verdad la importación de módulos haría falta un
hook (`pytest_collection`) o un `sitecustomize`, y eso es más de lo que R19
pide.

**O2 · Una línea obsoleta en `progress/current.md`.** Las líneas 26-27 siguen
diciendo «**Pendiente**: `docs/ARCHITECTURE.md` todavía dice "chalet"», cuando
T19 (commit `81a1a90`) ya lo arregló. Es memoria externa del arnés que ahora
dice que queda pendiente algo que está hecho. Lo arregla el líder al cerrar la
sesión; lo dejo escrito para que no se pierda.

**O3 · El alcance de la campaña de mutación es más ancho que F-003.**
`progress/mutacion_F-003.md` declara como origen del diff la ref `f5328f2`
(el merge del arnés 1.5.0), no la base real de la rama (`chore/postreview-F-002`,
`05146ef`). Por eso el alcance arrastra 27 ficheros —incluidos código de F-002
y **`harness/mutacion.py`, que aporta 32 de los 127 mutantes**—. **No es un
defecto**: el alcance es más amplio, nunca más estrecho, y aun así mueren los
127. Pero conviene saber que los 127 mutantes no son todos de F-003 (unos 56 lo
son) y que el número no es comparable feature a feature. Ver la propuesta P1.

## 7 · Lo que falta para cerrar F-003 (pendiente del humano, no cambio requerido)

**T17 y T18 son verificaciones `MANUAL (humano)` y están sin ejecutar a
propósito.** No las he ejecutado ni las doy por hechas: piden `GEMINI_API_KEY`
y el parte real de Mirasierra, que no se versiona. Lo que sí he comprobado:

- **Están documentadas con su comando exacto**, tanto en
  `specs/F-003-extraccion/tasks.md` (T17, T18) como en `progress/current.md`,
  con el resultado esperado y el criterio de parada.
- **No están marcadas como hechas**: siguen `[ ]` con la etiqueta
  `PENDIENTE DEL HUMANO`.
- **El paso 0 de T17 —confirmar contra la API que el identificador del modelo
  existe— está delante de todo**, antes de gastar una llamada de extracción, y
  con su instrucción de parada («si sale `reconocido: False` se le pregunta al
  humano; no se sustituye el modelo por iniciativa propia»). Es la protección
  correcta: un ID mal escrito no lo caza ningún test porque el modelo está
  simulado.
- **El comando de T18 no imprime valores extraídos.** Verificado línea a línea:
  imprime `nombre: <booleano> confianza=<n>` para los ocho campos y **solo para
  `numero_pagina` imprime el valor**, que es un número de página y no un dato
  personal. No escribe nada en disco. Lo que se anota en `progress/current.md`
  son booleanos y confianzas, nunca valores.

Además queda, ya anotado por el implementer: **aprobar las tres dependencias
nuevas** y **crear el `.env` local** con la credencial (ningún agente lo toca).

Y una advertencia que la spec deja escrita y conviene repetir: si T18 sale mal,
**no falla F-003** —su contrato se cumple igual— sino la premisa del proyecto,
y se arregla tocando el prompt o el modelo, no añadiendo tests.

## 8 · Automejora (propuestas, no aplicadas)

**P1 · Que la campaña de mutación use la base real de la rama.**
`harness/alcance.py` resuelve el origen «rama» con una ref que en cadenas de
ramas (`dev` → F-002 → `chore/postreview-F-002` → F-003) no es la base de la
feature, y el alcance acaba arrastrando ficheros de features anteriores y del
propio arnés (§O3). La cobertura, que usa `--base dev` explícito, da 631
líneas; la mutación, 1912. Propongo que `harness/features.json` pueda declarar
la rama base de cada feature (campo `base`, con `dev` por defecto) y que tanto
`harness.cobertura` como `harness.mutacion` la usen, de forma que los dos
números hablen del mismo «qué cambió» —que es justo lo que promete el docstring
de `harness/cobertura.py`—.

**P2 · Que `CHECKPOINTS.md` C5 contemple las tareas `MANUAL (humano)`.** Hoy
C5 exige «`tasks.md` con todas las tareas `[x]`», sin excepción, y una feature
de nivel `critico` **está obligada** a tener verificaciones manuales que un
agente no puede ejecutar. El reviewer se queda entre aprobar con un checkbox
vacío o rechazar por algo que no es un defecto. Propongo añadir a C5: *«Una
tarea marcada `MANUAL (humano)` y pendiente no vacía este checkbox, pero
impide el paso a `done`: el reviewer la lista en su informe como pendiente del
humano, con su comando.»* Es exactamente lo que he hecho en §7, y ahora mismo
lo he tenido que improvisar.

**P3 · Que C4 bis nombre la comprobación de «no medido» en la cobertura.** El
bloque exige que la puerta salga en `[OK]` con su porcentaje, pero un 100 %
sobre ficheros que no aparecen en el informe de `coverage` sería un 100 %
falso. El mecanismo existe en `harness/cobertura.py` (los cuenta como no
cubiertos), pero el checkpoint no le pide al reviewer que lo verifique.
Propongo añadir: *«y ningún fichero del alcance sale "no medido"»*, que es
barato de comprobar y cierra la vía más fácil de inflar el número.

---

**Veredicto final: APPROVED.** El trabajo del implementer cumple la spec, las
convenciones, la arquitectura y las cuatro puertas del nivel `critico`, con
todas ellas verificadas de forma independiente. F-003 **no pasa a `done`**
hasta que el humano ejecute T17 y T18.
