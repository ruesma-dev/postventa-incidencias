<!-- progress/review_F-004.md -->
# F-004 · Validación del parte y clasificación de la firma — informe de review

> Revisión de la rama `feature/F-004-validacion` contra `CHECKPOINTS.md`,
> `specs/F-004-validacion/`, `docs/ARCHITECTURE.md` y `docs/CONVENTIONS.md`.
> Ni un dato real en este informe: los únicos valores citados son recuentos y
> constantes inventadas del propio repositorio.

## Veredicto

**APROBADO.**

Los tres puntos que esta revisión tenía que mirar con lupa salen bien: la
deuda del control negativo está escrita con honestidad y en los tres sitios
que importan; la decisión D1 está implementada tal y como la resolvió el
humano y es coherente con los documentos normativos; y no hay ni un dato
personal, ni una credencial, ni una invasión de otras features.

**Dos acciones de cierre, ninguna de código**, listadas al final: refrescar
`progress/current.md` (lo lleva el líder) y una nota de una línea en
`progress/impl_F-004.md`, que se quedó diciendo que T14 está pendiente cuando
ya se ejecutó.

## Nivel de rigor y puertas que exige

**`rigor: critico`**, declarado en la ficha de `harness/features.json`. Exige,
sobre lo de `estandar`: fase RED en los requisitos centrales, cobertura de las
líneas cambiadas ≥ 80 %, campaña de mutación con **cero supervivientes** salvo
justificación escrita, y las verificaciones `MANUAL (humano)` listadas con su
**comando exacto y su resultado real**.

| Puerta | Resultado | Cómo se comprobó |
|---|---|---|
| `init.sh` | `ENTORNO LISTO`, exit 0 | ejecutado por el reviewer, sin pipes |
| Suite | **400 passed in 14,09 s** | `.venv/Scripts/python.exe -m pytest -q` lanzado por el reviewer, no la caché de `init.sh` |
| Cobertura | **`[OK]` 100,0 % de 305 líneas cambiadas** (305/305, umbral 80 %) | línea `PUERTA COBERTURA` de `init.sh` |
| Mutación | **43/43/0/0 · campaña REEJECUTADA por el reviewer** | ver §«Verificación independiente» |
| Fase RED | 5 bloques con traza real + la rotura deliberada de R25 | `progress/impl_F-004.md` |
| MANUAL (humano) | T14, con comando y resultado real | `tasks.md` T14, `design.md` §7 |

## Verificación independiente de la campaña de mutación

El informe declara **127,0 s**, por debajo de los 5 minutos, así que
`CHECKPOINTS.md` C4 bis obliga a **reejecutar la campaña entera**. Hecho:

```
.venv/Scripts/python.exe -m harness.mutacion --feature F-004 \
    --salida <scratchpad>/mutacion_F-004_reejecutada.md
```

Salida fuera de `progress/` (en el scratchpad de la sesión, nunca en el
repositorio) y **`git status` limpio antes y después**.

| Métrica | Informe del implementer | Reejecución del reviewer | Recálculo puro |
|---|---|---|---|
| Ficheros en alcance | 15 | 15 | **15** |
| Líneas en alcance | 1198 | 1198 | **1198** |
| Mutantes generados | 43 | 43 | **43** |
| Muertos | 43 | 43 | — |
| Supervivientes | **0** | **0** | — |
| Timeouts | 0 | 0 | — |
| Tiempo | 127,0 s | 169,7 s | — |

El recálculo puro se hizo aparte con `harness.alcance.alcance_de_feature` y
`harness.mutacion.generar_mutantes` (sin ejecutar la suite ni escribir en
disco) y coincide fichero a fichero: `validacion.py` 12, `paso_firma.py` 8,
`firma.py` 8, `function_app.py` 7, `confianza.py` 5, `validar.py` 3, el resto
0. No es una campaña de cero mutantes, así que no hace falta la prueba de
control por exclusión de alcance.

**Los muertos están comprobados, no contados**: los 43 volvieron a morir en la
reejecución del reviewer, con la misma cuenta final.

### La lección de F-003 sobre las constantes: comprobada, y aquí no se repite

F-004 tiene dos constantes de dominio que un test parametrizado con la propia
constante dejaría sin vigilar: `UMBRAL_CONFIANZA` y el conjunto de etiquetas
de firma. Los tests las escriben **a mano**, no las importan para generar sus
casos:

- `test_f004_r12_el_umbral_de_confianza_es_50_y_los_decisivos_son_dos` clava
  `UMBRAL_CONFIANZA == 50` y `CAMPOS_DECISIVOS == ("codigo_obra",
  "numero_incidencia")` con literales.
- Los casos del borde están escritos con números literales a los dos lados
  (`[0, 1, 30, 48, 49]` y `[50, 51, 93, 100]`), así que mover el umbral rompe
  tests en vez de arrastrarlos.
- Las cuatro etiquetas se comprueban por su `value` literal
  (`test_f004_r1_las_cuatro_etiquetas_de_firma`), no por iteración del `Enum`.

Es exactamente lo contrario del hueco de F-003. Los cuatro supervivientes de
la primera pasada (el borde `>=` del tope de tamaño y tres `frozen=True`) se
mataron con tests de comportamiento, no aflojando el mutador.

## Los tres puntos que se miraron con lupa

### 1 · La deuda del control negativo: escrita con honestidad

El criterio `acceptance` «La clasificación de firma distingue firma de aspa en
las muestras reales» **figura como NO demostrado** en los tres sitios, y
ninguno lo presenta como cubierto:

- **`requirements.md` §3**, tabla de trazabilidad: la fila dice literalmente
  «R1, R2, R13 — **NO demostrado por T14**», con una nota debajo que explica
  que un 22/22 `humana` lo habría producido igual un clasificador que
  respondiera `humana` a todo.
- **`tasks.md` T14**: sección «Lo que este resultado NO demuestra», con la
  frase clave —en la remesa no había ni un aspa que distinguir— y el traspaso
  a F-015 con su commit (`89e0a30`).
- **`design.md` §7, D1**: separa lo que el dato cierra (D1) de lo que no
  cierra (el acierto del modelo distinguiendo firma de aspa).
- El **mensaje del commit `ab9b677`** lo dice también, sin adornos.

Verificado además que la ficha de **F-015** en `harness/features.json` recoge
el encargo como criterio de aceptación propio, nombrando el control negativo
con partes sintéticos y `tests/utiles_pdf.py`. La deuda no se pierde.

**No se re-litiga la decisión del humano.** Lo que se comprueba —y se
cumple— es que la documentación no vende como demostrado lo que no lo está.

### 2 · D1 y la coherencia con los documentos normativos

El código hace lo que dice la spec, y son **dos destinos para dos trabajos**:

- `domain/models/validacion.py::_destino` manda a `COLA_VALIDACION_HUMANA`
  **solo** si el conjunto de códigos es exactamente
  `{OBSERVACIONES_MANUSCRITAS}`; cualquier otro caso con motivos va a
  `REVISION_MANUAL`.
- `LecturaFirma.es_conformidad_del_cliente` exige `HUMANA` **y** confianza en
  el umbral; cualquier otra etiqueta produce `firma_no_humana` y, por tanto,
  `revision_manual`. Un parte sin firma humana **nunca** entra en la cola.

Contra los documentos normativos:

- **`docs/ARCHITECTURE.md` semántica 3** (sin firma válida no se archiva ni se
  cierra): respetada. El paso 4 y la semántica 3 se reescribieron en esta rama
  y explican por escrito **cómo conviven** con el «único motivo de rechazo»:
  el criterio `acceptance` está redactado sobre **la cola**, y leerlo como «lo
  único que impide ser apto» chocaría con otro criterio de la misma lista
  (sin nº de incidencia nunca queda apto). El argumento es correcto y está en
  el sitio que manda, no solo en la spec.
- **`CHECKPOINTS.md` C3** («una marca simple —aspa, trazo geométrico, casilla
  vacía— nunca cuenta como firma del cliente»): cumplido, con tres textos de
  motivo distintos y un test que comprueba que son tres
  (`test_f004_r13_los_tres_textos_de_firma_no_humana_son_distintos`).
- **C3 «firmado no es conforme»**: cumplido por R8/R9.

Las tres decisiones de dominio del humano, comprobadas en el código y no en el
informe:

| Decisión | Dónde vive | Test |
|---|---|---|
| Sin DNI **SÍ** es conforme | `dni_cliente` no está en `CAMPOS_DECISIVOS` | `test_f004_r15_un_parte_sin_dni_sale_apto` |
| Con observaciones **NO** es conforme, aunque esté firmado | `_motivos` añade `OBSERVACIONES_MANUSCRITAS` con cualquier texto no vacío | `test_f004_r8_un_parte_firmado_con_observaciones_no_es_conforme` (comprueba que la firma sigue siendo `humana`) |
| Va a la cola **con el texto transcrito delante** | `ResultadoValidacion.observaciones` + bloque `observaciones` del JSON de `/api/validar` | `test_f004_r8_el_resultado_lleva_la_transcripcion_para_quien_decide` |

Detalle acertado y verificado: el umbral de confianza **no** se aplica a las
observaciones (`test_f004_r8_una_observacion_de_confianza_baja_viaja_igual`).
Descartar por poca confianza lo único que escribió el cliente habría sido el
fallo caro por el otro lado.

### 3 · Datos personales y límites de la feature

**Barrido ejecutado por el reviewer sobre el diff completo `dev...HEAD`**, no
leído del informe del implementer. Patrones usados:

| Patrón | Resultado |
|---|---|
| DNI `\b[0-9]{8}[- ]?[A-Za-z]\b` | 10 coincidencias, **todas** `00000000T`, el marcador inventado |
| Correos `[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}` | ninguno real (solo `@app.route` y `@pytest.mark.parametrize`) |
| IPs `([0-9]{1,3}\.){3}[0-9]{1,3}` | una: `192.0.2.1`, rango **TEST-NET-1 de la RFC 5737**, reservado para documentación |
| GUID de suscripción/tenant | ninguno |
| Claves `AIza…`, `sk-…`, `password=`, `api_key=`, `secret=`, `Bearer …` | solo `api_key="no-es-una-credencial"` en dos dobles de prueba |
| Teléfonos `\b[67][0-9]{8}\b`, direcciones `calle/avda` | ninguno |
| Binarios en git `git log --all --diff-filter=A` (pdf/jpg/png/tif/docx/xlsx) | **ninguno en toda la historia, en ninguna rama** |

Las observaciones de los tests son inventadas y distintas de la real que ya
citaba `ARCHITECTURE.md` desde antes de esta rama: `"Falta rematar el rodapié
del salón"` y `"Todo correcto, gracias"`. El prompt `firma_parte_es` prohíbe
expresamente transcribir nada (regla 2: «NI EL NOMBRE, NI EL DNI»), y solo
pide un campo.

Red, BBDD e IA en los tests: la guardia autouse de `tests/conftest.py`
sustituye `socket.socket.connect` durante **toda la sesión**, no por fichero.
Ningún test lee `muestras/` ni `docs/referencia/`, y hay un guardia con `ast`
que lo vigila sobre las cadenas de código (`test_f004_r26_ningun_test_lee_muestras`).

Límites de feature, comprobados sobre el diff y no sobre la palabra del
informe: **ni una línea** de SQL, persistencia, SharePoint, Sigrid o front.
Ningún fichero de `services/postventa-front/`, ningún `psycopg`, ningún
`sharepoint`. F-004 detecta y transcribe las observaciones; **no las
interpreta** (F-016), y hay un test que lo clava
(`test_f004_r10_el_contenido_de_la_observacion_no_cambia_el_veredicto`, con
cinco textos de sentido opuesto y el mismo veredicto). Ningún puerto de
`domain/ports/` se tocó, que era la condición de parada del diseño. Ninguna
dependencia nueva en el manifiesto.

## Checkpoints

### C1 — El arnés está completo y en verde

- [x] `bash harness/init.sh` termina con exit code 0 (`ENTORNO LISTO`).
- [x] Existen los ocho ficheros obligatorios.

### C2 — El estado es coherente

- [x] Una sola feature `in_progress` (F-004); lo valida `init.sh`.
- [x] Rama actual `feature/F-004-validacion`, la de la feature en curso.
- [x] `progress/current.md` describe la sesión del 2026-08-19, que es la
      activa, y no arrastra restos de features anteriores (el detalle de F-003
      está en `history.md`). **Con salvedad, y es la acción de cierre 1**: se
      quedó en la foto de antes de implementar —dice «ninguna feature
      `in_progress`», la spec «espera aprobación», T14 pendiente y «16
      features» cuando ya son 17—. No afecta al código ni a la verificación, y
      lo refresca el líder al cerrar la sesión, que es el paso siguiente a
      este veredicto.
- [x] Toda feature `done` tiene su resumen en `history.md` (F-001 a F-003).

### C3 — El código respeta arquitectura y convenciones

- [x] Hexagonal respetada. El dominio no importa `google`, `yaml`, `tenacity`,
      `infrastructure` ni `azure`; comprobado a mano y además por un test que
      recorre `domain/` y `application/` **enteros** con `ast`, no por texto,
      contando también los imports dentro de funciones.
- [x] Primera línea con la ruta relativa en los 17 ficheros nuevos.
- [x] Sin `print()` de debug (el único `print` del diff está dentro de un
      comando de ejemplo de `tasks.md`), sin TODOs sueltos, sin secretos, sin
      dependencias nuevas. `ruff` pasa **limpio** sobre los ficheros de F-004
      (los 33 avisos del repositorio son deuda previa de orden de imports y no
      crecen con esta rama).
- [x] La unidad de trabajo es el **parte**: `/api/firma` recibe un parte, no
      una remesa, y el hash del parte viaja en todo.
- [x] Nada se archiva ni se cierra sin validar: F-004 **es** la puerta, y
      declara por escrito que la comprobación contra Sigrid es una segunda
      puerta posterior (F-008/F-009). Ningún `commit` contra Sigrid aquí.
- [x] Lo manuscrito no se descarta (la transcripción viaja aunque el parte
      vaya a `revision_manual`, R19) y una marca simple nunca cuenta como
      firma.
- [x] Firmado no es conforme: R8 y R9, con la cola como destino propio.
- [ ] → **N/A justificado**: «reprocesar no duplica» es persistencia, y F-004
      no persiste nada (es F-005). El hash del parte, que es la clave que lo
      hará posible, ya viaja en `ResultadoValidacion`.
- [ ] → **N/A justificado**: «nada hardcodea un estado de Sigrid» — F-004 no
      habla con Sigrid, y un test de arquitectura lo vigila (R22).
- [x] Ningún parte escaneado ni PDF ha entrado en git: comprobado con
      `git log --all --diff-filter=A`, no solo con el árbol.

### C3 bis — Documentos que entran de fuera

**N/A justificado**: la rama no añade ni modifica ningún fichero de
`docs/referencia/`. El barrido de datos sensibles se ha hecho igualmente sobre
el diff completo (§3 de arriba), con los patrones listados.

### C4 — La verificación es real

- [x] Los 26 requisitos EARS tienen ≥ 1 test trazable y todos pasan. Los 45
      nombres de test citados en `requirements.md` existen en el código
      (comprobado por diferencia de conjuntos, no a ojo). Reparto por
      requisito en la tabla de trazabilidad de más abajo.
- [x] Los tests no tocan red ni BBDD ni IA: guardia de `socket` autouse de
      sesión, dobles de prueba para el extractor y el repositorio de prompts.
- [x] La única verificación `MANUAL (humano)` de la feature, **T14**, está
      listada con su **comando exacto** (`python C:\Users\pgris\f4_firma.py
      todos`) y con su **resultado real** en `tasks.md` T14 y en `design.md`
      §7. Ya no está «pendiente de que el humano la ejecute»: la ejecutó el
      2026-08-19 y el resultado está registrado, que es más de lo que pide el
      checkbox. **Salvedad**: el comando no figura en `progress/current.md`,
      donde sí están los de F-003; entra en la acción de cierre 1.

### C4 bis — El rigor declarado se cumple

- [x] La feature declara `rigor: critico` con valor válido.
- [x] **Fase RED**: el informe trae la salida real del fallo previo para T1,
      T3, T6, T8 y T11 —los cinco bloques centrales—, con `ModuleNotFoundError`
      sobre el módulo que aún no existía. Para R25, cuyo test nació en verde,
      se rompió a propósito la línea de log y se pegó la traza del fallo, que
      es exactamente lo que pide el checkpoint cuando el entregable es el
      propio guardia.
- [x] **Cobertura**: `[OK]` 100,0 % de 305 líneas cambiadas, umbral 80 %.
- [x] **Mutación**: `progress/mutacion_F-004.md` existe, generado por la
      herramienta, con totales reales **verificados de forma independiente**
      (alcance y nº de mutantes recalculados; coinciden fichero a fichero).
- [x] **Los muertos están comprobados**: campaña **reejecutada entera** por el
      reviewer (127,0 s declarados < 5 min), salida fuera de `progress/`,
      árbol limpio, mismos totales.
- [x] Cero supervivientes; ninguna sección en `PENDIENTE`. Los cuatro de la
      primera pasada están analizados uno a uno, con el test que los mata.
- [x] Sección **«Evidencias»** con los cuatro números: tests (400 passed),
      cobertura (100 % de 305), mutantes/supervivientes (43/0) y tiempo de la
      suite (26,0 s en `init.sh`, 13,0 s sola).
- [x] Ningún punto de este bloque marcado N/A.

### C4 ter — Verificaciones extra por rutas sensibles

**N/A sin nada que justificar**: `harness/rutas_sensibles.json` no existe en
este repositorio; es el caso mayoritario que el propio checkpoint declara N/A.
Merece decirse que el hueco es real y conocido —`config/prompts.yaml` gana en
esta rama un prompt que ningún test unitario puede medir— y que **ya está
mitigado en parte**: R4 clava la huella del prompt de extracción, así que
nadie lo roza sin enterarse. La declaración completa es F-015.

### C5 — La sesión se cerró bien

- [x] `tasks.md` con las **18 tareas `[x]`** y cero checkboxes vacíos, y un
      commit `F-004 Tn: ...` por tarea (T1 a T18, más el commit de resultado de
      T14). Comprobado contra `git log dev..HEAD`.
- [x] Árbol limpio: `git status` sin ficheros temporales ni artefactos sueltos,
      antes y después de la campaña de mutación del reviewer.
- [x] `features.json` refleja el estado real: F-004 sigue `in_progress`, que es
      lo correcto hasta que el líder cierre con este veredicto delante.

## Trazabilidad requisito → test

| Req | Qué exige | Tests (nº) |
|---|---|---|
| R1 | Las cuatro etiquetas, una y solo una | `test_f004_r1_*` (4) |
| R2 | Etiqueta desconocida o ausente → `ilegible`, nunca `humana` | `test_f004_r2_*` (7) |
| R3 | Confianza saneada con la misma regla que la extracción | `test_f004_r3_*` (4) |
| R4 | Prompt propio `firma_parte_es`; el de extracción, intacto | `test_f004_r4_*` (2, uno clava la huella) |
| R5 | El schema se resuelve por el nombre que declara el prompt | `test_f004_r5_*` (6) |
| R6 | Veredicto, destino y motivos con texto para Posventa | `test_f004_r6_*` (5) |
| R7 | Parte completo y firmado → `apto`, sin motivos | `test_f004_r7_*` (2) |
| R8 | Observaciones → `no_apto` aunque la firma sea humana, con transcripción | `test_f004_r8_*` (3) |
| R9 | Solo observaciones → `cola_validacion_humana` | `test_f004_r9_*` (1) |
| R10 | El contenido de la observación no cambia el veredicto | `test_f004_r10_*` (1, parametrizado con 5 textos) |
| R11 | Sin código de obra o sin nº de incidencia, nunca apto | `test_f004_r11_*` (2) |
| R12 | Vacío y confianza bajo umbral no son legibles; el umbral incluye | `test_f004_r12_*` (4) |
| R13 | Firma no humana → `firma_no_humana` + `revision_manual`, tres textos | `test_f004_r13_*` (4) |
| R14 | `humana` dudosa se trata como `ilegible` | `test_f004_r14_*` (3) |
| R14 bis | Y se **publica** degradada, en el dominio y en el JSON | `test_f004_r14bis_*` (6) |
| R15 | Sin DNI sale apto | `test_f004_r15_*` (1) |
| R16 | Los campos no decisivos vacíos no cambian el veredicto | `test_f004_r16_*` (2) |
| R17 | No se exige formato al nº de incidencia | `test_f004_r17_*` (1) |
| R18 | Todos los motivos, en el orden declarado | `test_f004_r18_*` (2) |
| R19 | Con algún motivo más, `revision_manual`, y la transcripción viaja | `test_f004_r19_*` (3) |
| R20 | Las reglas son dominio puro | `test_f004_r20_*` (2, con `ast`) |
| R21 | Sin extracción o sin firma, error de dominio; no se inventa veredicto | `test_f004_r21_*` (5) |
| R22 | La validación no conoce Sigrid | `test_f004_r22_*` (1) |
| R23 | Contrato de `POST /api/firma` + 400/413/502 | `test_f004_r23_*` (11) |
| R24 | Contrato de `POST /api/validar`, sin modelo, 400 diciendo qué falta | `test_f004_r24_*` (10) |
| R25 | El log no lleva observaciones ni DNI | `test_f004_r25_*` (1, con fase RED pegada) |
| R26 | La suite no abre red ni lee partes reales | `test_f004_r26_*` (2) |

### Contra los `acceptance` de la ficha

| `acceptance` | Estado |
|---|---|
| Distingue firma de aspa en las muestras reales | **NO demostrado**, y así consta. Deuda traspasada a F-015 por decisión del humano del 2026-08-19 |
| Observaciones → no conforme, siempre a la cola, con transcripción | Cubierto (R8, R9) |
| Las observaciones son el único motivo que manda **a la cola** | Cubierto (R9, R19), con el razonamiento en `ARCHITECTURE.md` semántica 3 |
| Sin DNI sale conforme | Cubierto (R15) |
| Sin nº de incidencia o sin código de obra, nunca apto | Cubierto (R11, R12) |
| No se exigen campos que la realidad deja en blanco | Cubierto (R16, R17) |
| Veredicto y motivo en texto entendible por Posventa | Cubierto (R6) |
| Reglas de dominio puro, probadas sin IA | Cubierto (R20, R21, R26) |
| `bash harness/init.sh` en verde | Cubierto (T18, reejecutado por el reviewer) |

## Acciones de cierre (del líder, no del implementer)

1. **Refrescar `progress/current.md`** antes de marcar F-004 `done`: sigue
   diciendo que no hay feature `in_progress`, que la spec espera aprobación y
   que T14 está pendiente, y cuenta 16 features cuando ya son 17. Debe recoger
   además el comando y el resultado de **T14**, como se hizo con los `f3_*.py`
   de F-003, y la deuda del control negativo heredada por F-015.
2. **Una nota en `progress/impl_F-004.md`**: sus secciones «Estado» y
   «Verificaciones MANUAL pendientes» se quedaron diciendo que T14 la ejecuta
   el humano. Ya se ejecutó. Basta una línea que apunte al resultado en
   `tasks.md` T14; el registro autoritativo está bien y es honesto, pero quien
   lea solo el informe se lleva una foto vieja. No cambia ningún número de la
   sección «Evidencias».

Ninguna de las dos toca código, tests ni la spec, y ninguna cambia el
veredicto.

## Observaciones que no bloquean

**O1 · El aviso de etiqueta desconocida publica el valor crudo del modelo.**
`application/pipelines/paso_firma.py:116` mete `bruto.valor` en el texto del
aviso, y los avisos acaban en el cuerpo de `/api/validar`. Hoy es inocuo: el
prompt pide un solo campo y prohíbe transcribir, y el aviso **no** entra en
ningún log (R25 lo comprueba). Pero cuando **F-005** persista los avisos,
conviene decidir si ese valor crudo se guarda o se recorta: es la única vía
por la que un texto no previsto del modelo podría viajar más allá de la
respuesta.

**O2 · `.gitignore` se tocó pese a estar en la lista de «no se tocan»** de
`design.md` §3.3. Es una línea (`.claude/worktrees/`), la metió el **líder** en
el commit `c83ed8b` —no el implementer— y está explicada en el cuerpo de ese
commit. No es una desviación del implementer ni afecta a nada.

**O3 · Precisión menor.** `requirements.md` y varios docstrings afirman que el
DNI `00000000T` «no es válido». La letra de control de `00000000` es
efectivamente `T`, así que el formato sí valida; lo que ocurre es que es un
número **no emitido** y de uso convencional como marcador. La afirmación no
tiene consecuencias —no hay ningún dato real— pero conviene no repetirla como
si fuera una garantía técnica.

**O4 · El alcance de la mutación (1198 líneas) y el de la cobertura (305) no
son comparables.** No es un defecto: la cobertura mide sentencias ejecutables
y la mutación cuenta líneas de fichero en alcance. Se anota porque en el
informe conviven los dos números y se leen como si midieran lo mismo.

## Automejora del arnés (propuesta, no aplicada)

**P1 · `CHECKPOINTS.md` C4, tercer punto, se queda corto cuando la
verificación manual YA se ejecutó.** Dice: «Las verificaciones `MANUAL
(humano)` están listadas en `progress/current.md` con su comando exacto,
**pendientes de que el humano las ejecute**». En F-004 la verificación se
ejecutó **durante** la implementación —a propósito, porque decidía D1— y el
checkbox se queda sin caso: no hay nada pendiente, y su resultado vive en
`tasks.md`, no en `current.md`. Propuesta de redacción:

> - [ ] Las verificaciones `MANUAL (humano)` constan con su **comando exacto**
>       y, si ya se ejecutaron, con su **resultado real** y la fecha. Mientras
>       estén pendientes viven en `progress/current.md`; una vez ejecutadas,
>       el registro que manda es `tasks.md` (o el informe de la feature), y
>       `current.md` deja de tener que listarlas.

**P2 · Falta un checkpoint para la deuda traspasada.** F-004 cierra con un
criterio `acceptance` no demostrado, por decisión explícita del humano, y lo
que impide que eso se pierda es que alguien se acordó de anotarlo en la ficha
de F-015. Convendría que fuera obligatorio, no memorístico. Propuesta, en C5:

> - [ ] Si la feature se cierra con algún criterio `acceptance` **no
>       demostrado**, consta por escrito en su `requirements.md` (o en la
>       ficha, si `sdd=false`) **y** está dado de alta como criterio propio de
>       otra feature de `harness/features.json`, citada por su identificador.
>       Cerrar con una deuda es legítimo; cerrarla sin dueño, no.

En F-004 ambas cosas se cumplen —y por eso el veredicto es APROBADO—, pero se
cumplen por diligencia del equipo, no porque el arnés lo exija. Las dos
propuestas son genéricas: si el humano las acepta, van también a `arnes-base`.
