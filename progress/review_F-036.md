<!-- progress/review_F-036.md -->
# F-036 · Review (reviewer, 2026-09-30)

- **Veredicto:** CHANGES_REQUESTED
- **Rama:** `feature/F-036-importar-excel` frente a `dev` (base común
  `a468367`), HEAD `444e0c4`, 61 commits, 107 ficheros. Incluye el commit
  local `cd4a8e0` de `azure-apps` (`postventa_incidencias.md`).
- **Nivel de rigor:** `critico`, declarado en `harness/features.json`.
  Puertas: fase RED en los requisitos centrales, cobertura de las líneas
  cambiadas ≥ 80 %, campaña de mutación con **cero supervivientes** sin
  justificación aceptada por el humano, mutaciones de orden a mano (punto 7
  del protocolo) y verificaciones `MANUAL (humano)` listadas con su comando.
- **Texto vigente de la spec:** la quinta enmienda (2026-09-29). Actividades
  (F-039) y agrupación de proveedores (F-050) están fuera a propósito y no se
  cuentan como faltas.

## Resumen para el líder

El trabajo de agente es sólido y trazable. La mutación está verificada de
forma independiente y cuadra al mutante. La fase RED es real y no escribe
nada en Sigrid. El DDL va solo al schema `postventa` y es idempotente. Aun
así, **no está listo para desplegar**: hay dos bloqueos y un tercer punto que
tiene que estar resuelto antes de T28.

### Lo que bloquea el despliegue (T27)

1. **El lector del Excel se puede tumbar con un fichero de 33 KB** (cambio 1).
   Basta una celda vacía con estilo en la fila 1.048.576 de «Incidencias»: el
   lector crea ~8,4 millones de celdas, tarda ~51 s y llega a ~1,9 GB de pico.
   No lo frena ninguna puerta (2 MiB, 20 MiB, 500 entradas, 1000 filas). Lo
   he reproducido de forma independiente con la fila 300.000: **9,2 s y 553
   MB de pico** para un fichero de 33.151 bytes.
2. **B5-1 (`COLLATE "C"` en el `CHECK` del par) sin decisión escrita del
   humano ni enmienda de `design.md` §6.1** (cambio 2). Técnicamente es
   correcto (análisis abajo) y recomiendo aceptarlo. Pero el guard del DDL no
   deja cambiar un `CHECK` una vez aplicado, y la aplicación se hace al
   arrancar la Function desplegada: la decisión tiene que constar **antes**
   de T27.

### Lo que tiene que estar antes de T28 (y de cualquier merge o push)

3. **Códigos de proveedor reales en un fichero versionado** (cambio 3):
   `progress/migracion_F-036.md` trae 5 códigos de proveedor de Sigrid, 46
   veces. El script los escribe (`scripts/migracion_f036.py:143` y
   alrededores) y T28 los volvería a escribir en `progress/`.

### Lo que puede esperar (no bloquea; conviene antes del merge)

Cambios 4–6 y las observaciones O-1 a O-12, al final.

### Qué debe mirar el humano en T16 y T27–T29

- **T16** (Docker): que pasen en particular
  `test_f036_b2_14_el_par_sigue_el_orden_de_python` (valida B5-1 contra un
  PostgreSQL real), el índice único parcial ante dos importaciones
  simultáneas, y el DDL aplicado dos veces sin nada en `public`.
- **T27**: antes de desplegar, cambios 1 y 2 hechos. Al desplegar, que el
  arranque aplica 12–14 sin error en el schema `postventa` del servidor
  compartido y que `/api/health` sigue respondiendo. En `oficios.html`, anotar
  solo cuántas propuestas se confirman o rechazan.
- **T28**: con el cambio 3 hecho, que el informe regenerado no lleva códigos
  de proveedor (`git diff progress/migracion_F-036.md`). Además, lo de B3-4:
  en Excel real, comprobar si «borrar fila» y «ordenar» funcionan con la
  columna `Errores` bloqueada. Y que `git status` no enseña ningún `.xlsx`.
- **T29 paso 2**: las dos lecturas de Sigrid **nunca se han ejecutado tal
  cual contra el ERP**. En concreto, el `LEFT JOIN dbo.con p ON p.ide =
  f.prvide` (B4-1) y el `obride` enviado como texto (B4-2). Ninguno para
  `0133`, `0144` ni `0166`.
- **T29 pasos 5–6**: además de lo del guion, subir una copia del `v2` con una
  celda con formato en una fila muy lejana (p. ej. la 1.048.576) y medir el
  tiempo de respuesta. Es la prueba desplegada del cambio 1.
- **T29 pasos 1 y 8**: los recuentos antes y después idénticos, que es la
  prueba desplegada de «no se escribe nada en Sigrid».

## Verificación ejecutada por el reviewer

| Qué | Resultado |
|---|---|
| `bash harness/init.sh` (tal cual) | **ENTORNO LISTO**. Raíz: 62 passed. Servicios `api` y `front`: verde (caché: árbol sin cambios desde el último verde). `PUERTA COBERTURA: 99.9% de 2785 líneas cambiadas cubiertas (2783/2785, umbral 80%, nivel critico)`. Avisos previos: ruff 70 (deuda), F-035 `blocked` |
| Recálculo puro de alcance y nº de mutantes, bloque a bloque | Cuadra en los 10 informes (tabla abajo) |
| Continuidad de las campañas | Sin huecos: ninguna línea de producción cambió entre el árbol de una campaña y la base de la siguiente, ni después de la última (`6b0ae24..HEAD`: 0 líneas) |
| Prueba de control de las campañas con 0 mutantes (7 y 8b) | Legítimo. Sin la exclusión de alcance salen 67 y 106 mutantes, solo en tests (`test_f036_front.py`, `test_f036_migracion_contenido.py`) |
| Muestreo de supervivientes cerrados «a mano» | 5 de 14 reaplicados en una copia del scratchpad. Los 5 caen con el test nuevo que dice el informe (detalle abajo) |
| Mutaciones de orden (punto 7) | Ver la sección «Orden» |
| Lector del Excel frente a ficheros hostiles | 6 experimentos en el scratchpad (ZIP con tamaño declarado falso, macros, DTD con entidades, fórmulas y DDE, chartsheets, filas lejanas) |
| Barrido de datos sensibles | Sobre `git log dev..HEAD -p` completo (55.344 líneas) y sobre `azure-apps@cd4a8e0`. Patrones y resultado en C3 bis |
| Árbol de trabajo | `git status --porcelain` vacío al terminar. Todo lo mutado vivió solo en el scratchpad |

### Mutación: recálculo independiente

Para cada informe se ha recalculado el alcance con `harness.alcance`
(`parsear_diff` + `filtrar_produccion`) y los mutantes con
`harness.mutacion.generar_mutantes`, sobre el contenido de los ficheros en el
commit en que corrió la campaña (`git show <commit>:<fichero>`).

| Informe | Diff recalculado | Líneas | Mutantes (informe / recálculo) | Muertos / superv. | Tiempo total · workers | Coste por mutante |
|---|---|---|---|---|---|---|
| `mutacion_F-036.md` (Bloque 1) | `a468367..37f45ae` | 1349 | 153 / **153** | 148 / 5 (cerrados con tests) | 4162,9 s · 4 | 108,8 s |
| `_bloque2` | `9e9510f..03d907d` | 845 | 101 / **101** | 101 / 0 | 1753,3 s · 6 | 104,2 s |
| `_bloque3` | `b98bc3a..920a596` | 672 | 138 / **138** | 138 / 0 | 3017,2 s · 6 | 131,2 s |
| `_bloque4` | `72dce57..37d6626` | 727 | 29 / **29** | 29 / 0 | 807,2 s · 6 | 167,0 s |
| `_bloque5` | `dd6da93..bdafb87` | 1035 | 74 / **74** | 74 / 0 | 1927,5 s · 6 | 156,3 s |
| `_bloque6a` | `cf86881..9686cad` | 1268 | 65 / **65** | 65 / 0 | 2003,9 s · 6 | 185,0 s |
| `_bloque6b` | `a5447ce..58099ba` | 675 | 41 / **41** | 41 / 0 | 733,8 s · 6 | 107,4 s |
| `_bloque7` | `b5e952f..5c48215` | 0 | 0 / **0** | — | 0 s | — (control: 67 mutantes solo en tests) |
| `_bloque8a` | `588f3ce..ce3be66` | 1244 | 159 / **159** | 150 / 9 (cerrados con tests) | 5267,9 s · 6 | 198,8 s |
| `_bloque8b` | `8fde6cd..6b0ae24` | 0 | 0 / **0** | — | 0 s | — (control: 106 mutantes solo en tests) |

- **Campañas no reejecutadas**: todas las que tienen mutantes pasan de 5
  minutos (de 12 a 88 min según su propio informe). Vale el recálculo puro,
  que cuadra al mutante. El coste por mutante (100–200 s) está muy por encima
  del segundo y es coherente con una suite del servicio de 65–90 s en serie
  con 4–6 workers en paralelo: no hay indicio de suite que no corra.
- **Los 14 supervivientes** (5 del Bloque 1 y 9 del 8a) están analizados,
  ninguno en `PENDIENTE`, y los 14 son **huecos reales cerrados con un test
  nuevo**, no equivalentes. No hace falta, por tanto, la aceptación escrita
  del humano que exige `critico` para los equivalentes. He muestreado 5 en
  una copia del scratchpad y los 5 caen con el test que cita el informe:
  - B1 #1 `MIN_EJEMPLOS = 3` → falla `test_f036_r5_dos_ejemplos_se_admiten_cuatro_no`.
  - B1 #5 `> MAX_DESCRIPCION` → `>=` → falla `test_f036_r5_ejemplo_con_descripcion_de_128_se_admite`.
  - 8a #1 `COLUMNAS_ORIGINAL = 7` → falla `test_f036_r54_mas_alla_de_la_columna_f_no_se_lee`.
  - 8a #3 `<=` → `<` → falla `test_f036_forma_de_la_tabla_propuesto_admite_todos_los_campos`.
  - 8a #7 `or` → `and` → falla `test_f036_r58_el_oficio_dice_la_etiqueta_del_v2_cuando_no_es_su_nombre`.

  La línea base de la copia, con el bytecode limpio: 275 passed.
- **B3-13** está bien resuelto: la primera campaña del Bloque 3 «mataba» todo
  por un test de arquitectura roto (el GUID de B3-12). Se descartó y se
  repitió. El recálculo confirma que la válida es la de `920a596`.
- **Para T30**: la cadena de campañas cubre toda la rama. Tras los cambios 1
  y 3, basta una campaña con `--base 444e0c4` sobre lo que cambie; no hace
  falta relanzar la rama entera (~830 mutantes, muchas horas).

### Orden (punto 7 del protocolo)

**No completado en esta review.** Las mutaciones de orden a mano (bajar un paso
cada puerta de R9, R15, R22, R14/R21, R39, R62 y R88 por debajo de cada
colaborador que dice preceder) se lanzaron en una copia desechable del
scratchpad, pero no habían terminado al cerrar este informe. No hay
resultado que declarar, y **no se da por cumplido**. Queda como condición
de la próxima review: repetirlas sobre el código con los cambios 1–3 aplicados.
Tampoco se da por hecho ningún resultado parcial.

Lo que sí consta: el orden de `paso_importacion.py` es el de `design.md` §7.3
(huella → reconocimiento → catálogo → validación → registro → Excel de
errores). B6-2 hace que un paso fuera de orden levante `ValueError` antes de
tocar ningún puerto. El implementer lo fija con tests que usan fábricas que
revientan si se llaman (B6-6).

## Checkpoints

### C1 — El arnés está completo y en verde

- [x] `bash harness/init.sh` termina en verde (ENTORNO LISTO).
- [x] Existen `CLAUDE.md`, `harness/features.json`, `specs/SPECS.md`,
  `progress/current.md`, `progress/history.md`, `docs/ARCHITECTURE.md` y
  `docs/CONVENTIONS.md` (init.sh los comprueba uno a uno).

### C2 — El estado es coherente

- [x] Una sola `in_progress` (F-036).
- [x] Rama `feature/F-036-importar-excel`.
- [x] `progress/current.md` empieza por el bloque vivo de F-036 (T26), con
  T16 y T27–T29 pendientes y sus comandos. Los bloques de sesiones anteriores
  siguen debajo, como en el resto de features del repositorio.
- [x] Toda feature `done` tiene su resumen en `history.md` (F-036 no está
  `done`).

### C3 — Arquitectura y convenciones

- [x] Hexagonal: `domain/` solo importa biblioteca estándar y `domain.*`
  (`uuid`, `types`…, ni `openpyxl` ni `yaml` ni red). Lo fija
  `test_f036_arquitectura.py`. Los adaptadores viven en `infrastructure/`
  (`documentos/`, `sigrid/`, `persistencia/`) y los handlers en
  `interface_adapters/api/`.
- [x] Primera línea con la ruta en todos los ficheros nuevos (`.py`, `.js`,
  `.html`, `.sql`, `.ps1`, `.yaml`, `.md`). Comprobado con un bucle sobre
  `git diff --diff-filter=A`: 0 sin ruta.
- [x] Sin `print()` de depuración: los únicos `print` son la salida de los
  dos scripts de consola (`medir_catalogos_f036.py`, `migrar_excel_f036.py`),
  que es su interfaz. Sin TODOs sin contexto ni secretos (C3 bis).
  Dependencias nuevas: `openpyxl` y `defusedxml`, previstas en T10.
- N/A · «La unidad de trabajo es el parte»: F-036 no procesa PDFs ni partes,
  sino filas de una plantilla. El análogo, una incidencia por fila con
  clave de duplicado propia, se cumple (R35–R38).
- N/A · «Nada se archiva ni se cierra sin validaciones / dry-run en Sigrid»:
  F-036 no archiva ni cierra, y no escribe en Sigrid (R46, verificado en el
  código y por la rama de DDL/Sigrid).
- N/A · «Lo manuscrito no se descarta» y «firmado no es conforme»: F-036 no
  lee partes escaneados.
- [x] **Reprocesar no duplica**, en su forma para F-036: el índice único
  parcial `ux_bandeja_clave (obra_codigo, clave_duplicado) WHERE duplicada_de
  IS NULL` con `ON CONFLICT … DO NOTHING RETURNING`, el atajo de R39 por
  `sha256` y `ya_en_bandeja` (R38, R41, R67). Queda pendiente de T16 contra una
  base real.
- N/A · «Ningún número de estado hardcodeado contra Sigrid»: F-036 no escribe
  estados en Sigrid.
- [x] Ningún parte escaneado, PDF, `.xlsx` ni JSON de catálogo en git.
  `git log --all --diff-filter=A` (699 rutas, todas las ramas): ninguno.
  `git ls-files`: ni `.env` ni `local.settings.json`.

### C3 bis — Documentos que entran de fuera (`docs/referencia/05_excel_creacion_incidencias.md`)

- [x] Cabecera con origen (`creacion_incidencias.xlsx`, OneDrive del humano),
  fecha (recibido el 2026-09-28) y conversión con `markitdown`. Desvío menor
  de formato frente a la plantilla del `README.md` (O-11).
- [x] Originales no versionados: ningún `.xlsx`, `.xls`, `.xlsm`, `.pdf` ni
  `.docx` en `git log --all --diff-filter=A`.
- [x] **Barrido ejecutado por el reviewer** sobre el documento y sobre todo
  `git log dev..HEAD -p`. Patrones:
  - GUID: `[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}`
  - IP: `\b\d{1,3}(\.\d{1,3}){3}\b`
  - correo
  - `https?://`, más hosts de entorno (`azurewebsites`, `azurestaticapps`,
    `database.azure.com`, `sharepoint.com`, `vault.azure.net`, `windows.net`,
    `onmicrosoft.com`)
  - `(?i)(password|pwd|secret|token|apikey|api_key|key=|AccountKey|SharedAccessSignature|Bearer )`
  - DNI/NIF/NIE/CIF: `\b\d{8}[A-Z]\b`, `\b[XYZ]\d{7}[A-Z]\b`, `\b[A-HJ-NP-SUVW]\d{7}[0-9A-J]\b`
  - teléfono `\b[6789]\d{8}\b`
  - IBAN

  **Resultado en `05_…md`: 0 hallazgos.** En la rama:

  | Hallazgo | Qué es |
  |---|---|
  | 1 GUID | `GUID omitido: R26 de F-006`, el de B3-12: de relleno, en el historial local, sin push (O-10) |
  | 2 IP | `127.0.0.1`, del doble local de la pasarela |
  | 4 URL | Dos CDN públicos del front y dos inventadas (`ejemplo.invalido`) |
  | 0 hosts de entorno | — |
  | 57 coincidencias de clave | Todas nombres de variable o valores de test inventados |
  | 0 DNI/NIF/CIF/IBAN | — |
  | 2 «teléfonos» | `600000000` (inventado en un test) y `987654321` (el `OBRA_REF` de los tests) |

  Nombres de proveedor o de persona reales: ninguno (todos «Ejemplo» o
  «Inventado»). **Códigos** de proveedor reales: sí, en
  `progress/migracion_F-036.md` (cambio 3).
- N/A · «Lo redactado está anotado en la cabecera»: no se redactó nada, y el
  documento no trae datos personales.

### C4 — La verificación es real

- [x] Cada requisito vigente tiene ≥ 1 test trazable y todos pasan (tabla de
  cobertura abajo). R13, R44 y R83 se trazan por docstring (`"""R13 · …"""`,
  `"""… R44: …"""`, `"""R83 · …"""`) en tests llamados `test_f036_t12_…` y
  `test_f036_t14_…`, no por el nombre `test_f036_rN_` (cambio 6, menor). R52
  se traza en los tests JS («f036 R52: …»). R90 y R100–R108, R110, R112–R114
  están retirados por la quinta enmienda. R109 y R111 quedaron cumplidos en
  T1/T2 y tienen tests.
- [x] Los unit tests no tocan red ni BBDD: dobles de conexión y de la
  pasarela. Los de base real están en `tests_bbdd/` (T16), fuera de la suite.
- [x] Las `MANUAL (humano)` (T16, T27, T28, T29) están en `tasks.md` con su
  comando exacto, y T16 además en `progress/current.md`. T27–T29 están en
  `current.md` por referencia a `tasks.md`.

### C4 bis — El rigor declarado se cumple

- [x] `rigor: "critico"` declarado.
- [x] **Fase RED**: cada bloque trae la salida real de los tests en rojo
  antes del código (ImportError o esqueleto con `NotImplementedError`,
  `70 failed, 12 passed`, `69 failed, 1 passed`…). En los requisitos
  centrales va además la **demostración por sabotaje**: comparación exacta
  frente a plegada (13 failed), resolución de R94, R53, R54, R91, R97, R56,
  R57 fila a fila y T25.
- [x] **Cobertura**: `[OK]` 99,9 % (2783/2785).
- [x] **Mutación**: los 10 informes existen, los genera la herramienta y sus
  totales están verificados de forma independiente (tabla de arriba).
- [x] **Muertos comprobados**: campañas > 5 min, **no reejecutadas** (de 12 a
  88 min cada una, según sus informes); se aplica el recálculo puro, que
  cuadra. Muestreo de 5 supervivientes cerrados: los 5 caen.
- [x] **Coste por mutante**: de 104 a 199 s con el factor de workers, muy por
  encima de 1 s y coherente con la suite.
- [x] Ningún superviviente en `PENDIENTE`; los 14 son huecos reales cerrados
  con tests, ninguno equivalente.
- [x] «Evidencias» con los cuatro números y los workers en cada bloque. En
  T26: 6003 passed, 99,9 %, sin alcance de mutación y suite de 529,67 s.
- [x] Ningún N/A sin justificar en este bloque.

**Hallazgo de proceso (no bloquea):** el implementer declara que en T25 lanzó
`init.sh` con un `| grep -v`, contra la regla. Lo dijo él mismo, y T26 volvió
a lanzarlo limpio.

### C4 ter — Rutas sensibles

- N/A: el repositorio no declara `harness/rutas_sensibles.json` (solo existe
  el `.ejemplo.json`), así que no hay nada que exigir.

### C5 — La sesión se cerró bien

- [x] `tasks.md`: T1–T15 y T17–T26 en `[x]`, con commit `F-036 Tn:` por
  tarea (T1 `63c0879`/`1b3edfb` … T26 `0f07a46`). Siguen `[ ]` T16, T27, T28
  y T29, que son `MANUAL (humano)`, y T30, que es el `init.sh` final. Es el
  estado que se espera en esta review, no un defecto.
- [x] Sin ficheros temporales ni sin trackear (`git status` vacío).
- [ ] **`features.json` no refleja el estado real**: F-036 sigue con
  `blocked_by` «T6 bloqueada (2026-09-29)…», y T6 está hecha desde `37f45ae`
  (cambio 4).

## Análisis de B5-1 (`COLLATE "C"`)

`14_decisiones_equivalencia.sql` escribe
`CHECK (codigo_a COLLATE "C" < codigo_b COLLATE "C")` donde §6.1 dice
`CHECK (codigo_a < codigo_b)`.

- `DecisionPar` (`domain/models/equivalencias.py:153`) exige
  `codigo_a < codigo_b` con el orden de Python, que es por punto de código.
- `COLLATE "C"` en PostgreSQL compara por bytes. En UTF-8 el orden de bytes
  es el de punto de código, así que coinciden. La collation `"C"` existe
  siempre, también en bases con ICU.
- Con el literal de §6.1 y una collation `en_US.utf8`, un par como
  `'B1'`/`'a1'` se ordenaría al revés que en Python y el `INSERT` daría 503.
  Hoy no pasa, porque los códigos de oficio son solo cifras. Pasaría con
  F-039 (`A:`, `O:`) o F-050.
- Ninguna otra sentencia depende de la collation para ser correcta.
  `select_ultimas_decisiones` y los índices trabajan por igualdad.

**Veredicto técnico: correcto, y mejor que el literal de §6.1.** Lo que
falta es la decisión escrita del humano y el recuadro fechado en §6.1
(cambio 2).

## Desviaciones del implementer

Las he leído todas (B2-1…B2-16, B3-1…B3-15, B4-1…B4-12, B5-1…B5-13,
B6-1…B6-30, B7-*, B8-*, B8b-*, T25, T26-*). Cada una está justificada contra
el texto de la spec o contra un hueco de la spec, dice la alternativa y, cuando
cambia comportamiento visible, va a `current.md` para el humano. Las que
merecen mención:

| Desviación | Juicio |
|---|---|
| B1-2 / B2-13 / B6-1: `validar_filas` recibe opciones, no grupos | Justificada: manda `tasks.md` T5 y lo exige §7.3 («mismo catálogo y opciones») |
| B2-1: `Catalogo.PROVEEDOR` sin perfil | Justificada y aprobada por el humano en T9 |
| B3-9 / B3-10: tope de 2 MiB también en el lector; `vbaProject.bin` en cualquier carpeta | Justificadas (defensa en profundidad). La de macros amplía R16 sin coste |
| B3-12 / B3-13: GUID inventado en el historial; campaña descartada | Bien gestionadas y avisadas (O-10) |
| B4-1 / B4-2: SQL no ensayado tal cual; `obride` como texto | Justificadas. **Riesgo real a comprobar en T29 paso 2** |
| B4-4: unidad sin código fuera del catálogo | Opción por defecto razonable; anotada para el humano |
| B5-1: `COLLATE "C"` | Correcta; falta la decisión escrita (cambio 2) |
| B6-3: las decisiones se piden solo entre los oficios de la obra | Desviación **semántica** de R82/R84, bien explicada y en `current.md`. Puede esperar, pero no la recoge ninguna documentación (O-4) |
| B6-6: la huella consulta la base antes de reconocer el fichero | Es el orden de §7.3 (paso 1). Cumple R21 (solo prohíbe escribir). Consecuencia: 503 en vez de 400 con la base caída; la documentación no lo matiza (O-3) |
| B6-9: YAML roto = 500 con motivo | Justificada |
| B6-19: `infra/08` no es idéntico a `dev` | Justificada por R111. El test exige lo más estricto que sigue siendo cierto. Falta anotarlo en §2.3 (O-2) |
| B6-20 / B6-21 / B6-28 | Justificadas; B6-28 (sin tope de decisiones) es una observación (O-9) |
| B6-30: la lista `NUEVOS_DE_F036` «la amplían los bloques 7 y 8» | **No se amplió**: faltan `scripts/migracion_f036.py`, `migrar_excel_f036.py` y el front. R46 no queda ciego, porque su primer test mira toda línea añadida de la rama. Pero el comentario promete algo que no pasó (cambio 5) |
| B8-1 / B8-4 / B8-5 / B8-11 / B8b-1 / B8b-2 | Justificadas y resueltas por el humano en T25 |
| T26-1: la copia de `azure-apps` ya divergía | Correcto aplicar solo los bloques de F-036; reconciliar es trabajo aparte |

## Cambios requeridos

1. **[Bloquea el despliegue] Acotar el recorrido de filas del lector.**
   - **Dónde:** `services/postventa-api/infrastructure/documentos/excel_openpyxl.py:549`
     (`_filas`: `ws.iter_rows(min_row=PRIMERA_FILA, max_col=len(COLUMNAS_DE_DATOS))`)
     y `:452` (`load_workbook(..., data_only=False)` sin `read_only`).
   - **Qué pasa:** el recorrido llega hasta `ws.max_row`, e `iter_rows` crea
     una `Cell` por posición. Una sola celda con estilo en la fila 1.048.576
     cuesta ~51 s y ~1,9 GB. Reproducido con la fila 300.000: 9,2 s y 553 MB
     para 33 KB. Un Excel con filas formateadas hasta el final lo provoca
     también sin mala intención.
   - **Qué hacer:** acotar el recorrido a `ULTIMA_FILA + 1`. Para seguir
     cumpliendo R20 (`demasiadas_filas`), detectar datos por debajo mirando
     solo las celdas que existen (p. ej. `ws._cells`, o `read_only=True` con
     su propio recorrido).
   - **Tests:** uno con una celda de estilo, sin valor, en la fila 1.048.576:
     se lee en tiempo acotado y da 0 filas. Otro con un valor en la fila
     5.000: sigue siendo `demasiadas_filas`.
   - Con su fase RED, y la campaña de mutación del cambio con `--base 444e0c4`.
   - Es un hueco del diseño (§5.2 no lo prevé), no un error del implementer.
2. **[Bloquea el despliegue] Decidir B5-1 por escrito antes de T27.**
   - Anotar en `progress/current.md` la aceptación (o el rechazo) del humano
     de `COLLATE "C"` en `infrastructure/persistencia/sql/14_decisiones_equivalencia.sql`
     (línea del `CHECK` del par).
   - Enmendar `specs/F-036-importar-excel/design.md` §6.1 (línea ~951, el
     literal `CHECK (codigo_a < codigo_b)`) con su recuadro fechado.
   - Trabajo del líder con el humano; el código no cambia si se acepta.
3. **[Antes de T28 y de cualquier merge o push] Sacar los códigos de
   proveedor del informe de migración.**
   - `progress/migracion_F-036.md` lleva 5 códigos reales de proveedor de
     Sigrid, 46 veces (p. ej. la línea 34: «Proveedor: proveedor completado
     (único de la obra para ese oficio), código `…`»). Entraron en `6b0ae24` y
     se regeneraron en `0884a7c`.
   - Cumple la letra de R58 («sin nombres de proveedor»), pero choca con su
     «sin datos personales» y con `design.md` §13 punto 14: «guardar códigos
     en git tampoco sirve: el código de un autónomo lleva a su nombre en
     cuanto se mira Sigrid».
   - **Qué hacer:** que `scripts/migracion_f036.py` (la composición del
     texto del proveedor completado, en torno a `PROVEEDOR_COMPLETADO`, línea
     143, y su uso en el informe) no escriba el código, solo «proveedor
     completado (único de la obra para ese oficio)». Ajustar el test de R58
     para que **exija** que no aparezca ningún código de proveedor, y
     regenerar el informe con el comando de T24.
   - La rama no se ha pusheado: que el humano decida si reescribir la
     historia local para que esos códigos no lleguen a `dev`. Es lo mismo que
     B3-12, y los dos se pueden resolver con un solo `rebase`.
4. **[Puede esperar, pero antes de cerrar] `harness/features.json`, entrada
   F-036:** quitar el `blocked_by` obsoleto de T6 (hecha desde `37f45ae`) y
   regenerar `BACKLOG.md` con `init.sh`. Es lo que deja C5 en `[ ]`.
5. **[Puede esperar] `services/postventa-api/tests/test_f036_alcance_cerrado.py:194-228`:**
   el comentario dice que los bloques 7 y 8 amplían `NUEVOS_DE_F036`, y no lo
   hicieron. Hay dos salidas:
   - añadir `scripts/migracion_f036.py` y `scripts/migrar_excel_f036.py`,
     para que `test_f036_r46_el_codigo_de_f036_no_nombra_ninguna_escritura` y
     el de imports los miren también sin docstrings;
   - o corregir el comentario para que diga que el control de esos ficheros es
     el de líneas añadidas.
6. **[Puede esperar] Trazabilidad por nombre.**
   - R13: `test_f036_t12_sql_oficios_de_la_obra_caracter_a_caracter`
     (`tests/test_f036_consultas_catalogo.py:77`).
   - R44: `test_f036_t14_bandeja_tiene_las_columnas_del_diseno_y_ninguna_mas`
     (`tests/test_f036_ddl.py:373`).
   - R83: `test_f036_t14_decisiones_tiene_las_columnas_del_diseno_y_ninguna_mas`
     (`tests/test_f036_ddl.py:480`).

   Los tres se trazan solo por docstring. C4 pide `test_f036_rN_*`: basta con
   un alias o renombrarlos.

## Observaciones (no bloquean; para el humano o el siguiente encargo)

- **O-1 · `design.md` §8.** La fila de `GET /api/catalogos/propuestas` sigue
  diciendo `{oficio: {...}, proveedor: {...}}`; el código devuelve
  `{obra, oficio: {oficios, grupos, propuestas, avisos}}` (B6-18). La fila de
  decisiones no dice que la obra sin unidades es 409 (B6-21). Son erratas de
  la spec.
- **O-2 · `design.md` §2.3** sigue diciendo que `infra/08_lectura_sigrid_comun.ps1`
  se usa «tal cual»; falta la excepción de R111 (B6-19).
- **O-3 · `docs/INTEGRACION.md`**, fila de `POST /api/importaciones`: dice
  que un fichero que no es la plantilla es 400 «sin leer Sigrid ni escribir
  nada». Con la base caída es 503, porque la huella lee la base antes (B6-6).
  Falta el matiz.
- **O-4 · B6-3 sin documentar.** ARCHITECTURE dice que una decisión vale
  para todas las obras (R84), y es cierto par a par. Pero una cadena A–X–B con
  X fuera de la obra no une A y B en esa obra. Conviene anotarlo, o decidir si
  se quiere la componente global.
- **O-5 · `docs/ARCHITECTURE.md`, «Dónde vive cada pieza»**, omite
  `application/pipelines/catalogo_obra.py`, `contexto_importacion.py` e
  `infrastructure/documentos/plantilla_yaml.py`.
- **O-6 · `defusedxml` no se exige en ejecución.** Hoy está activo
  (`openpyxl.xml.DEFUSEDXML == True`, y el test
  `test_f036_r16_defusedxml_esta_debajo_de_openpyxl` lo vigila en la suite).
  Pero si un despliegue perdiera la dependencia, `openpyxl` pasaría sin avisar
  al parser estándar. Mejora barata: fallar cerrado en `_abrir` si
  `DEFUSEDXML` es falso.
- **O-7 · Macros.** `vbaProjectSignature.bin` suelto, el content type
  `macroEnabled` y `activeX*.bin` pasan. Es conforme con R16, y `openpyxl`
  los descarta: riesgo nulo en el servidor, porque el Excel de errores se
  genera de cero.
- **O-8 · Cuerpo entero en memoria antes del tope de 2 MiB.**
  `function_app.py:1340-1343` hace `fichero.read()` y el tope se aplica
  después, así que el límite real lo pone el host. R15 («sin abrirlo») se
  cumple.
- **O-9 · Otras de persistencia y scripts:**
  - inserción en el orden del fichero: dos importaciones simultáneas con
    claves solapadas en distinto orden pueden dar un deadlock, que acaba en
    503 sin nada a medias (ordenar por clave lo evita);
  - `--informe` se sobrescribe siempre;
  - sin tope de decisiones por petición (B6-28);
  - las conexiones no se cierran explícitamente (B6-15, el patrón del resto
    del proyecto) en un PostgreSQL compartido.
- **O-10 · B3-12.** El GUID de relleno `12345678-1234-5678-…` sigue en el
  historial local (`d99478e`). No es un oid ni un tenant, y la rama no se ha
  pusheado. Si se hace el `rebase` del cambio 3, que entre también.
- **O-11 · Cabecera de `docs/referencia/05_…`.** Da la fecha de recepción y
  no «Fecha del documento: AAAA-MM-DD» como la plantilla del `README.md`.
  Cambio de forma.
- **O-12 · Fórmulas devueltas.** Una fórmula que vuelve en el Excel de
  errores y se resube sin cambios entra como texto que empieza por `=`. Es
  conforme con R7/R32, pero F-040 y F-048 lo recibirán tal cual: que lo
  tengan en cuenta al volcar a Sigrid o al datamart.

## Documentación frente a lo implementado

`docs/ARCHITECTURE.md` y `docs/INTEGRACION.md` coinciden con el código en lo
que afirman:
- las 5 rutas (17 en total, `ANONYMOUS` como las demás);
- los códigos de estado;
- las 3 tablas, sus `CHECK` e índices;
- las 2 lecturas por `sql/read`;
- los topes (2 MiB, 20 MiB, 500 entradas, 1000 filas, 128, 2000, bandeja
  200/500);
- lo que sale en los logs;
- el nombre del Excel de errores;
- ninguna variable nueva.

No describen como hecho nada de F-039 ni de F-050. El `README` del front
coincide con las páginas.

El commit `cd4a8e0` de `azure-apps`:
- toca solo `postventa_incidencias.md`;
- lleva la cabecera con la rama y `0f07a46` (sigue exacta: `docs/` no cambió
  después);
- no introduce divergencias nuevas;
- `azure-apps` no tiene remoto.

Discrepancias: solo las de O-1 a O-5.

## Cobertura: requisito → test

Requisitos vigentes de la quinta enmienda. La columna «nº» cuenta los tests
Python con el prefijo del requisito más los JS «f036 RN:».

| Req. | Test (uno representativo) | nº |
|---|---|---|
| R1 | `test_f036_pipeline_importacion.py::test_f036_r1_la_plantilla_lee_el_catalogo_los_grupos_y_genera` | 4 py + 0 js |
| R2 | `test_f036_excel_generador.py::test_f036_r2_hojas_en_orden_con_su_estado_e_incidencias_activa` | 11 py + 0 js |
| R3 | `test_f036_configuracion_plantilla.py::test_f036_r3_r4_mensajes_de_todas_las_columnas_con_validacion` | 7 py + 0 js |
| R4 | `test_f036_configuracion_plantilla.py::test_f036_r4_mensajes_de_los_topes` | 3 py + 0 js |
| R5 | `test_f036_configuracion_plantilla.py::test_f036_r5_las_instrucciones_dicen` | 11 py + 0 js |
| R6 | `test_f036_excel_generador.py::test_f036_r6_metadatos_de_la_plantilla` | 8 py + 0 js |
| R7 | `test_f036_excel_generador.py::test_f036_r7_ninguna_celda_de_ninguna_hoja_es_formula` | 5 py + 0 js |
| R8 | `test_f036_plantilla_dominio.py::test_f036_r8_unidades_de_la_0677` | 10 py + 0 js |
| R9 | `test_f036_bandeja_http.py::test_f036_r9_la_obra_se_normaliza_como_las_demas` | 13 py + 0 js |
| R10 | `test_f036_adaptador_catalogo.py::test_f036_r10_leer_las_unidades_es_un_post_a_sql_read_con_su_cuerpo` | 21 py + 0 js |
| R11 | `test_f036_adaptador_catalogo.py::test_f036_r11_un_transitorio_se_reintenta_y_la_lectura_sigue` | 14 py + 0 js |
| R12 | `test_f036_catalogos_http.py::test_f036_r12_una_obra_sin_oficios_no_propone_nada` | 10 py + 0 js |
| R13 | `test_f036_consultas_catalogo.py::test_f036_t12_sql_oficios_de_la_obra_caracter_a_caracter` (docstring «R13») | 1 py |
| R14 | `test_f036_importar_http.py::test_f036_r14_hace_falta_exactamente_un_fichero` | 1 py + 0 js |
| R15 | `test_f036_excel_lector.py::test_f036_r15_mas_de_2_mib_se_rechaza_sin_mirar_nada` | 4 py + 0 js |
| R16 | `test_f036_excel_lector.py::test_f036_r16_sin_la_firma_de_un_zip_no_es_xlsx` | 12 py + 0 js |
| R17 | `test_f036_excel_lector.py::test_f036_r17_formato_antiguo_de_la_muestra` | 13 py + 0 js |
| R18 | `test_f036_excel_lector.py::test_f036_r18_la_version_solo_vale_como_numero_entero` | 5 py + 0 js |
| R19 | `test_f036_excel_lector.py::test_f036_r19_cabecera_movida` | 12 py + 0 js |
| R20 | `test_f036_excel_lector.py::test_f036_r20_mas_de_1000_filas_con_datos` | 4 py + 0 js |
| R21 | `test_f036_importar_http.py::test_f036_r21_sin_puertos_un_fichero_que_no_es_la_plantilla_no_construye_sigrid` | 3 py + 0 js |
| R22 | `test_f036_importar_http.py::test_f036_r22_sin_un_usuario_oid_valido_es_400_sin_abrir_el_fichero` | 4 py + 1 js |
| R23 | `test_f036_excel_lector.py::test_f036_r23_solo_filas_con_algun_dato_fuera_de_errores` | 4 py + 0 js |
| R24 | `test_f036_importacion_dominio.py::test_f036_r24_r33_errores_de_varias_filas_y_columnas_a_la_vez` | 1 py + 0 js |
| R25 | `test_f036_importacion_dominio.py::test_f036_r25_falta_la_unidad` | 2 py + 0 js |
| R26 | `test_f036_importacion_dominio.py::test_f036_r26_unidad_exacta` | 1 py + 0 js |
| R27 | `test_f036_importacion_dominio.py::test_f036_r27_descripcion_obligatoria` | 4 py + 0 js |
| R28 | `test_f036_importacion_dominio.py::test_f036_r28_detalle_dos_mil_si_dos_mil_uno_no` | 3 py + 0 js |
| R29 | `test_f036_importacion_dominio.py::test_f036_r29_ubicacion_exacta` | 1 py + 0 js |
| R30 | `test_f036_importacion_dominio.py::test_f036_r30_oficio_exacto` | 1 py + 0 js |
| R31 | `test_f036_importacion_dominio.py::test_f036_r31_urgente_y_primer_listado` | 2 py + 0 js |
| R32 | `test_f036_excel_lector.py::test_f036_r32_formula_se_lee_como_formula_con_su_texto` | 14 py + 0 js |
| R33 | `test_f036_importacion_dominio.py::test_f036_r33_orden_de_las_filas_se_conserva` | 5 py + 1 js |
| R34 | `test_f036_importacion_dominio.py::test_f036_r34_aviso_de_urgencia_con_urgencia_vacia` | 9 py + 0 js |
| R35 | `test_f036_importacion_dominio.py::test_f036_r35_clave_es_sha256_de_los_cuatro_campos_normalizados` | 6 py + 0 js |
| R36 | `test_f036_importacion_dominio.py::test_f036_r36_miras_de_hierro_en_cinco_ubicaciones_no_son_duplicados` | 3 py + 0 js |
| R37 | `test_f036_importacion_dominio.py::test_f036_r37_duplicadas_en_el_fichero_agrupadas_la_primera_manda` | 7 py + 0 js |
| R38 | `test_f036_repositorio_bandeja.py::test_f036_r38_select_de_las_existentes_por_clave` | 3 py + 0 js |
| R39 | `test_f036_ddl.py::test_f036_r39_el_hash_del_fichero_no_es_unico_y_se_indexa_con_el_estado` | 14 py + 0 js |
| R40 | `test_f036_pipeline_importacion.py::test_f036_r40_si_la_base_falla_no_hay_excel_de_errores` | 9 py + 0 js |
| R41 | `test_f036_ddl.py::test_f036_r41_la_no_duplicacion_la_garantiza_un_indice_unico_parcial` | 4 py + 0 js |
| R42 | `test_f036_ddl.py::test_f036_r42_importaciones_guarda_quien_cuando_que_y_los_recuentos` | 4 py + 0 js |
| R43 | `test_f036_importar_http.py::test_f036_r43_una_importacion_completa_responde_200_con_su_resumen` | 2 py + 4 js |
| R44 | `test_f036_ddl.py::test_f036_t14_bandeja_tiene_las_columnas_del_diseno_y_ninguna_mas` (docstring «R44») | 1 py |
| R45 | `test_f036_bandeja_http.py::test_f036_r45_la_bandeja_devuelve_las_incidencias_de_la_obra` | 23 py + 5 js |
| R46 | `test_f036_adaptador_catalogo.py::test_f036_r46_el_modulo_no_nombra_ninguna_ruta_de_escritura` | 9 py + 0 js |
| R47 | `test_f036_adaptador_catalogo.py::test_f036_r47_ni_obra_ref_ni_nombres_ni_codigos_de_proveedor_en_los_logs` | 21 py + 0 js |
| R48 | `test_f036_adaptador_catalogo.py::test_f036_r48_el_adaptador_se_niega_fuera_de_dev_y_pro` | 16 py + 0 js |
| R49 | `test_f036_alcance_cerrado.py::test_f036_r49_la_rama_no_toca_la_configuracion_del_entorno` | 3 py + 0 js |
| R50 | `test_f036_front.py::test_f036_r50_la_pagina_de_importacion_tiene_sus_tres_bloques` | 2 py + 21 js |
| R51 | `test_f036_front.py::test_f036_r51_la_cabecera_de_index_enlaza_a_las_dos_paginas` | 2 py + 0 js |
| R52 | JS «f036 R52: …» | 0 py + 12 js |
| R53 | `test_f036_migracion.py::test_f036_r53_r56_linea_de_ordenes_escribe_v2_e_informe` | 10 py + 0 js |
| R54 | `test_f036_migracion.py::test_f036_r54_blancos_distintos_casan_y_nada_mas` | 23 py + 0 js |
| R55 | `test_f036_migracion.py::test_f036_r55_r56_camino_bueno_con_grupos` | 4 py + 0 js |
| R56 | `test_f036_migracion.py::test_f036_r56_el_v2_pasa_el_importador_sin_errores` | 10 py + 0 js |
| R57 | `test_f036_migracion.py::test_f036_r57_textos_prohibidos` | 16 py + 0 js |
| R58 | `test_f036_migracion.py::test_f036_r58_el_informe_no_lleva_nombres_de_proveedor` | 11 py + 0 js |
| R59 | `test_f036_alcance_cerrado.py::test_f036_r59_ningun_commit_de_la_rama_trae_un_libro` | 5 py + 0 js |
| R60 | `test_f036_documentacion.py::test_f036_r60_la_cabecera_dice_que_f036_lo_toco_y_cuando` | 18 py + 0 js |
| R61 | `test_f036_documentacion.py::test_f036_r61_la_arquitectura_tiene_la_seccion_de_la_entrada` | 11 py + 0 js |
| R62 | `test_f036_excel_generador.py::test_f036_r62_mismo_libro_que_la_plantilla_con_los_mismos_desplegables` | 6 py + 0 js |
| R63 | `test_f036_excel_generador.py::test_f036_r63_valores_tal_como_llegaron_y_texto_de_errores` | 3 py + 0 js |
| R64 | `test_f036_excel_generador.py::test_f036_r64_celdas_con_error_marcadas_con_relleno_y_comentario` | 4 py + 0 js |
| R65 | `test_f036_excel_generador.py::test_f036_r65_el_excel_de_errores_viaja_en_base64_y_se_reabre` | 5 py + 4 js |
| R66 | `test_f036_excel_lector.py::test_f036_r66_una_fila_que_solo_trae_errores_no_cuenta` | 2 py + 0 js |
| R67 | `test_f036_pipeline_importacion.py::test_f036_r67_el_excel_de_errores_corregido_no_duplica_lo_que_ya_entro` | 3 py + 0 js |
| R68 | `test_f036_pipeline_importacion.py::test_f036_r68_nada_del_excel_de_errores_ni_de_las_filas_malas_llega_a_la_bandeja` | 1 py + 0 js |
| R69 | `test_f036_importar_http.py::test_f036_r69_sin_filas_con_error_la_respuesta_no_lleva_excel` | 3 py + 3 js |
| R70 | `test_f036_ddl.py::test_f036_r70_parcial_si_y_solo_si_hay_filas_con_error` | 5 py + 0 js |
| R71 | `test_f036_excel_generador.py::test_f036_r71_r92_los_pares_empiezan_por_la_etiqueta_del_oficio` | 7 py + 0 js |
| R72 | `test_f036_plantilla_dominio.py::test_f036_r72_mismo_nombre_en_el_mismo_oficio_lleva_el_codigo` | 3 py + 0 js |
| R73 | `test_f036_importacion_dominio.py::test_f036_r73_proveedor_exacto` | 2 py + 0 js |
| R74 | `test_f036_importacion_dominio.py::test_f036_r74_d17_solo_proveedor_toma_el_oficio_del_par` | 3 py + 0 js |
| R75 | `test_f036_importacion_dominio.py::test_f036_r75_proveedor_con_varios_codigos_es_ambiguo` | 2 py + 0 js |
| R76 | `test_f036_importacion_dominio.py::test_f036_r76_sin_oficio_ni_proveedor` | 2 py + 0 js |
| R77 | `test_f036_importacion_dominio.py::test_f036_r77_la_clave_no_incluye_oficio_ni_proveedor` | 1 py + 0 js |
| R78 | `test_f036_catalogos_http.py::test_f036_r78_un_clique_se_propone_entero_con_sus_motivos_ordenados` | 17 py + 0 js |
| R79 | `test_f036_catalogos_http.py::test_f036_r79_si_no_es_un_clique_se_propone_por_pares` | 3 py + 1 js |
| R80 | `test_f036_equivalencias_dominio.py::test_f036_r80_proponer_no_agrupa` | 1 py + 0 js |
| R81 | `test_f036_catalogos_http.py::test_f036_r81_un_distinto_separa_un_grupo_confirmado` | 8 py + 2 js |
| R82 | `test_f036_catalogos_http.py::test_f036_r82_una_componente_contradicha_no_se_aplica_y_se_avisa` | 6 py + 0 js |
| R83 | `test_f036_ddl.py::test_f036_t14_decisiones_tiene_las_columnas_del_diseno_y_ninguna_mas` (docstring «R83») | 1 py |
| R84 | `test_f036_equivalencias_dominio.py::test_f036_r84_decision_de_otra_obra_vale_aqui` | 3 py + 1 js |
| R85 | `test_f036_equivalencias_dominio.py::test_f036_r85_par_decidido_no_se_vuelve_a_proponer` | 2 py + 0 js |
| R86 | `test_f036_catalogos_http.py::test_f036_r86_la_etiqueta_es_la_del_oficio_con_mas_filas_en_la_obra` | 7 py + 0 js |
| R87 | `test_f036_catalogos_http.py::test_f036_r87_las_propuestas_de_oficios_de_la_obra` | 9 py + 2 js |
| R88 | `test_f036_catalogos_http.py::test_f036_r88_un_mismo_se_guarda_por_pares_en_una_transaccion` | 24 py + 3 js |
| R89 | `test_f036_front.py::test_f036_r89_el_html_solo_decide_desde_un_clic` | 3 py + 6 js |
| R90 | retirado (quinta enmienda, a F-050); sus tests quedan sobre el script de medición de T1 (`test_f036_scripts_infra.py::test_f036_r90_el_cif_solo_entra_normalizado`) | 4 py |
| R91 | `test_f036_migracion.py::test_f036_r91_con_grupos` | 3 py + 0 js |
| R92 | `test_f036_excel_generador.py::test_f036_r92_una_entrada_por_grupo_de_oficio` | 12 py + 0 js |
| R93 | `test_f036_importacion_dominio.py::test_f036_r93_design_15_5_solo_oficio_con_dos_codigos_es_ambiguo` | 5 py + 0 js |
| R94 | `test_f036_importacion_dominio.py::test_f036_r94_design_15_5_el_proveedor_deshace_la_ambiguedad` | 4 py + 0 js |
| R95 | `test_f036_ddl.py::test_f036_r95_el_par_va_en_orden_con_la_intercalacion_de_python` | 11 py + 0 js |
| R96 | `test_f036_equivalencias_dominio.py::test_f036_r96_clave_quita_las_palabras_del_perfil` | 1 py + 0 js |
| R97 | `test_f036_migracion.py::test_f036_r97_con_grupos_se_escribe_la_etiqueta_del_grupo` | 22 py + 0 js |
| R98 | `test_f036_front.py::test_f036_r98_boton_de_los_grupos_vigentes` | 1 py + 4 js |
| R99 | `test_f036_ddl.py::test_f036_r99_ambiguo_sin_codigo_y_con_nombre_y_no_hay_proveedor_sin_oficio` | 7 py + 0 js |
| R109 | `test_f036_scripts_infra.py::test_f036_r109_mide_las_familias` | 11 py + 0 js |
| R111 | `test_f036_scripts_infra.py::test_f036_r111_el_comun_no_deja_decodificar_a_invoke_restmethod` | 7 py + 0 js |

Retirados por la quinta enmienda y sin exigencia en F-036: R100–R108, R110, R112–R114 (R108 conserva sus tests porque el `CHECK` de `catalogo` es la costura). R109 y R111: cumplidos en T1/T2, con tests.

## Anexo (líder, 2026-09-30) · mutaciones de orden del punto 7, completadas después

El agente auxiliar que lanzó el reviewer terminó después de entregarse la
review. Trabajó sobre una copia de `git archive HEAD` en el scratchpad, ya
borrada, con el árbol real limpio. Resultado: **23 mutaciones de orden** sobre
las puertas de R9, R14/R21, R15, R22, R39, R40/R62, R45, R48 y R88. **22
caen**, cada una con un test de su propio requisito (en M3, M3a y M4b, también
repitiendo sin `-x`). **1 es equivalente** (M1a): la comprobación del `oid`
después del tope de 2 MiB; ninguna de las dos llama a un colaborador y solo
cambia si gana el 400 o el 413 cuando fallan las dos a la vez. Es una
observación menor, no un hueco. Línea base: 1529 passed antes y después. El
punto 7 queda cubierto; la segunda review no necesita repetirlo, salvo en lo
que toquen los arreglos 1–3.

## Review 2 (reviewer, 2026-09-30)

- **Veredicto:** CHANGES_REQUESTED
- **Rama:** `feature/F-036-importar-excel`, HEAD `52f8149`. Arreglos revisados:
  `git diff 5fe4661..HEAD` (10 commits, 18 ficheros; producción: `importacion.py`,
  `excel_openpyxl.py`, `migracion_f036.py`).
- **Nivel de rigor:** `critico`, declarado. Puertas: fase RED, cobertura de las
  líneas cambiadas ≥ 80 %, mutación con cero supervivientes sin justificación
  aceptada por el humano, mutaciones de orden a mano en el código del Bloque 10
  y `MANUAL (humano)` con su comando.
- **Alcance de esta review:** los cambios 1, 3, 5 y 6 de la review 1 y que no
  rompan nada. Lo que la review 1 dio por bueno y no tocan los arreglos no se ha
  vuelto a revisar.

### Resumen para el líder

Los cuatro arreglos están bien hechos. El caso exacto del cambio 1 queda
cerrado, en la plantilla y en el Excel de errores: de 45,7 s y 1,9 GB a 0,09 s
y 40 MB con el mismo fichero. El informe de migración ya no lleva ningún código
de `obrofc`. La mutación cuadra al mutante y las mutaciones de orden del
bloque caen.

**Aun así, no está listo para desplegar**, por la misma razón que en la
review 1: con un fichero de 33 KB se sigue pudiendo tumbar la Function. Lo que
cambia es la vía. Un **rango combinado** o un **hipervínculo sobre un rango**
lejanos hacen que `openpyxl` cree una celda por posición **dentro de
`load_workbook`**, antes de que el lector recorra nada:

- rango combinado `A1003:H1048576`: 169 s y 2,6 GB;
- hipervínculo sobre el mismo rango: 228 s y 4,1 GB. Es casi el corte de 230 s
  del balanceador y más memoria de la que tiene una instancia de Functions.

R115 dice que el lector «no debe recorrer ninguna hoja posición a posición más
allá de lo que la plantilla puede tener», y esto lo incumple. Es un hueco que
ya existía (el lector de `5fe4661` lo tenía igual). **Se le escapó a la
review 1**, cuyos 6 experimentos no probaron rangos. No es un error del
Bloque 10. El arreglo es acotado (cambio R2-1).

### Qué debe mirar el humano en cada verificación manual (tras el cambio R2-1)

- **T16** (Docker, `powershell -ExecutionPolicy Bypass -File infra\pruebas_bbdd_efimera.ps1`):
  lo mismo que dijo la review 1. En concreto:
  - `test_f036_b2_14_el_par_sigue_el_orden_de_python`: valida B5-1, ya decidida,
    contra un PostgreSQL real, y el `CHECK` no se puede cambiar después de
    aplicarse;
  - el índice único parcial con dos importaciones simultáneas;
  - el DDL aplicado dos veces sin nada en `public`.
- **T27** (desplegar):
  - no antes de R2-1;
  - al arrancar, que se aplican 12–14 sin error y solo en el schema `postventa`
    del servidor compartido, y que `/api/health` responde;
  - en `oficios.html`, anotar solo cuántas propuestas se confirman o rechazan.
- **T28**:
  - `git diff progress/migracion_F-036.md` sin ningún código de proveedor
    (hoy hay 0: ver abajo);
  - en Excel real, «borrar fila» y «ordenar» con la columna `Errores`
    bloqueada (B3-4);
  - `git status` sin ningún `.xlsx`.
- **T29**:
  - **Pasos 1 y 8:** los recuentos idénticos. Es la prueba desplegada de «no se
    escribe en Sigrid».
  - **Paso 2:** las dos lecturas de Sigrid tal cual contra el ERP. Son el
    `LEFT JOIN` de B4-1 y el `obride` como texto de B4-2; ninguna se ha
    ejecutado nunca así.
  - **Paso 9:** la celda con formato en la fila 1.048.576 tiene que responder
    como el paso 4. Además, con R2-1 hecho, subir una copia del `v2` con las
    celdas `A1003:A1048576` de «Incidencias» combinadas (en Excel: seleccionar
    el rango y «Combinar celdas»). La respuesta tiene que ser inmediata: un
    rechazo `fichero_sospechoso`, o la lectura normal si el diseño elige
    `read_only`. Nunca un minuto de espera ni un 5xx.
  - Anotar tiempos, sin nombres.

### Verificación ejecutada por el reviewer

| Qué | Resultado |
|---|---|
| `bash harness/init.sh` (tal cual) | **ENTORNO LISTO**. Raíz: 62 passed. `api` y `front` salieron de la caché. `PUERTA COBERTURA: 99.9% de 2807 líneas cambiadas cubiertas (2805/2807, umbral 80%, nivel critico)` |
| Suite del `api` ejecutada aparte sobre HEAD | **6035 passed, 67 skipped** en 295,9 s. La caché de `init.sh` es por el árbol del servicio, y `52f8149` añadió ficheros a `progress/` que `test_f006_r26` barre (ver «Automejora») |
| Cambio 1: reproducción independiente | Tabla de abajo. Se comparó el lector de `5fe4661` con el de HEAD sobre los mismos bytes, en una copia desechable del scratchpad |
| Cambio 1: vectores del mismo tipo | Rango combinado e hipervínculo sobre un rango. Es el hallazgo R2-1 |
| Cambio 3: informe de migración | 0 códigos de proveedor de `obrofc` (detalle abajo) |
| Cambios 5 y 6 | Resueltos (detalle abajo) |
| Mutación del Bloque 10 | Recálculo puro cuadra: 94 líneas, 26 mutantes. Los 3 supervivientes, reaplicados en la copia, caen |
| Mutaciones de orden (punto 7), solo en el código del Bloque 10 | 3 de 4 caen; 1 equivalente (O4) |
| Barrido de datos sensibles | Sobre las 1170 líneas añadidas en `5fe4661..HEAD`: 0 hallazgos |
| Árbol de trabajo | `git status --porcelain` vacío antes de escribir este informe. La copia desechable, borrada |

#### Cambio 1: el tope del lector (R115)

Guiones en el scratchpad. Cada caso corre en un subproceso con tope de tiempo.
El pico es el *working set* máximo del proceso, que incluye unos 40 MB del
intérprete. Los ficheros salen del generador de la plantilla (o del Excel de
errores, con una fila con error) más el cambio que dice cada fila.

| Caso | Bytes | Lector de `5fe4661` | Lector de HEAD |
|---|---:|---|---|
| Plantilla, celda vacía con estilo en `A1048576` (el caso de la review 1) | 33.161 | 45,72 s · 1.892 MB | **0,09 s · 40 MB**, reconocida, 0 filas |
| Excel de errores, celda con estilo en `B1048576` | 34.717 | 41,11 s · 1.892 MB | **0,15 s · 40 MB**, 1 fila, la de siempre |
| Excel de errores, celda con estilo en la columna `Errores` (fila 1.048.576) | 34.720 | — | 0,12 s, 1 fila |
| Excel de errores, **valor** en la columna `Errores` (fila 1.048.576) | 34.741 | — | 0,10 s. No cuenta como dato: bien por R66 y B10-3 |
| Plantilla, la fila 1.048.576 entera con formato (`row_dimensions`) | 33.184 | — | 0,12 s |
| Plantilla, la columna A entera con formato (`column_dimensions`) | 33.162 | — | 0,11 s |

**El caso del cambio 1 está resuelto**, también en el Excel de errores que se
vuelve a subir. Coincide con lo que mide el implementer (36,4 s → 0,105 s) y
con sus tests.

**Hallazgo R2-1.** Lo mismo con rangos, con el lector de HEAD:

| Caso | Bytes | Lector de HEAD | Qué pasa |
|---|---:|---|---|
| Rango combinado `A1003:A1048576` en «Incidencias» | 33.173 | **24,07 s · 430 MB** | Se lee y se reconoce |
| Rango combinado `A1003:H1048576` | 33.176 | **169,38 s · 2.609 MB** | Se lee y se reconoce |
| Hipervínculo interno sobre `A1003:H1048576` | 33.188 | **228,08 s · 4.058 MB** | Acaba en `demasiadas_filas`, pero después de casi 4 minutos |

- **Dónde está el coste:** en `openpyxl` 3.1.5, al cargar. `load_workbook`
  llama a `WorksheetReader.bind_all`. Ahí:
  - `bind_merged_cells` llama a `ws._clean_merge_range(mcr)`, que crea un
    `MergedCell` por cada posición del rango;
  - `bind_hyperlinks`, con un `ref` que es un rango, recorre `ws[link.ref]` y
    crea cada celda.

  He mirado los demás *binders* (formato, dimensiones, tablas y propiedades), y
  ninguno expande rangos. Pasa en cualquier hoja del libro, no solo en
  «Incidencias», porque `load_workbook` carga todas.
- **Por qué no lo frena nada:** son 33 KB, así que el tope de 2 MiB y el de
  20 MiB descomprimidos no saltan. El tope de 500 entradas tampoco.
  `_datos_fuera_del_tope` y el recorrido acotado llegan tarde, porque el daño
  ya está hecho en `_abrir`.
- **Dos salidas medidas sobre los mismos ficheros:**
  - `load_workbook(..., read_only=True)` (la segunda opción de §5.2): **0,08 s**
    en los dos peores casos, porque el modo de solo lectura no enlaza
    combinados ni hipervínculos. Obliga a rehacer `_celdas_existentes`, porque
    `ReadOnlyWorksheet` no tiene `_cells`.
  - Un **examen previo del XML** de las hojas, antes de `_abrir`. Sumar el área
    de cada `mergeCell/@ref` y de cada `hyperlink/@ref` que sea un rango cuesta
    **0,002 s**.
- **La plantilla no lo necesita:** el generador no escribe ni combinados ni
  hipervínculos (`grep` sin resultados en `excel_openpyxl.py`).

#### Cambio 3: el informe de migración sin códigos de proveedor (R116)

Guion contra el JSON del catálogo de T2, que está fuera del repositorio. Se
tomaron los 36 códigos de proveedor distintos de `oficios_obra` y
`actividades_proveedor`, y los 130 de oficio. Ninguno de los 36 es a la vez
código de oficio. Solo se imprimieron recuentos.

| Informe | «código `…`» | … que no son de oficio | Códigos de proveedor como palabra | Nombres de proveedor |
|---|---:|---:|---:|---:|
| `5fe4661` (control) | 167 | 46 | 5 distintos, en 46 líneas | 0 |
| **HEAD** | 121 | **0** | **0** | 0 |

- **El control funciona:** el método encuentra en el informe viejo exactamente
  lo que la review 1 señaló.
- **Diff del informe:** 48 líneas quitadas y 48 añadidas. En 46, la añadida es
  la quitada sin «, código `…`». Las otras dos son la nota de cabecera y el
  rótulo del recuento (B10-7), que sigue diciendo 46.
- **Recuentos intactos:** 144 → 158, 14 separadas, 0 descartadas.
- **El script:** `migracion_f036.py:913` ya no escribe el código. Los tests de
  R116 lo exigen con el catálogo inventado y con el contenido real de la
  propuesta. Fase RED real en el informe del implementer.
- **Historial:** los commits intermedios que llevan los códigos no llegan a
  `dev` por el `git merge --squash` que decidió el humano. Nada que objetar.

#### Cambios 5 y 6

- **Cambio 5:**
  - `NUEVOS_DE_F036` gana `scripts/migracion_f036.py` y
    `scripts/migrar_excel_f036.py`;
  - `FRONT_DE_F036` lleva los cuatro ficheros del front, con los controles de
    texto sobre el fichero entero;
  - el comentario ya no promete lo que no pasó, y dice por qué el control de
    imports no aplica al front (B10-8, correcto);
  - `test_f036_r46_los_bloques_7_y_8_tambien_estan_en_el_control` fija la
    inclusión.
- **Cambio 6:** los tres tests se renombran a `test_f036_r13_…`,
  `test_f036_r44_…` y `test_f036_r83_…`. El cuerpo no cambia.
- **Cambio 4:** lo resolvió el líder en `5fe4661` (fuera el `blocked_by`
  obsoleto).
- **Cambio 2:** B5-1 está decidida en `current.md` y en el recuadro de §6.1.

#### Mutación del Bloque 10

- **Recálculo:** con `harness.alcance` (`parsear_diff` + `filtrar_produccion`
  sobre `git diff 444e0c4 <ref>`) y `harness.mutacion.generar_mutantes` sobre
  el contenido en `<ref>`, con `<ref>` = `629b29b` (el árbol de la campaña,
  13:54) y HEAD:
  - `importacion.py`: 14 líneas, 3 mutantes;
  - `excel_openpyxl.py`: 67 líneas, 23 mutantes;
  - `migracion_f036.py`: 13 líneas, 0 mutantes;
  - **total: 94 líneas y 26 mutantes, igual que el informe.**
- **Continuidad:** entre `629b29b` y HEAD no cambia ninguna línea de
  producción (`dee3824` solo toca un test).
- **Campaña no reejecutada:** 1.558,5 s (26 min) según el informe, por encima
  de 5 min. Vale el recálculo puro.
- **Coste por mutante:** 1.558,5 × 6 ÷ 26 = **359,7 s**. Está muy por encima de
  1 s y es coherente con una suite de ~530 s en serie con 6 workers
  compitiendo.
- **Los 3 supervivientes existen** tal cual en el recálculo, con su operador y
  su texto original → mutado:
  - `MAX_FILAS_METADATOS = 10 → 11`;
  - `max_row=ULTIMA_FILA + 1 → + 2`;
  - `(), (), False → True`.

  Reaplicados en una copia de `git archive HEAD` del scratchpad (línea base:
  271 passed), **los 3 caen** con el test que dice el informe:
  - S1 → `test_f036_r115_los_metadatos_se_leen_hasta_su_tope_de_filas`
    (1 failed, 96 passed);
  - S2 → `test_f036_r115_valor_en_la_fila_5000_con_las_de_en_medio_vacias[1003]`;
  - S3 → `test_f036_r19_sin_hoja_incidencias_cabecera_vacia`.

  Ninguno queda en `PENDIENTE` y ninguno es equivalente.

#### Orden (punto 7), solo en el código del Bloque 10

La puerta nueva es la comprobación de `datos_fuera_del_tope` dentro de
`reconocer_plantilla`, que va después de la cuenta de filas y antes de la obra.
No habla con ningún colaborador: su orden frente a Sigrid y la base lo da
`paso_reconocimiento`, que el anexo ya cubrió (R14/R21) y el Bloque 10 no ha
tocado. En la misma copia:

| Mutación | Resultado |
|---|---|
| O1 · la puerta R115 baja por debajo de la normalización de la obra | **Cae**: `test_f036_r115_el_tope_se_comprueba_donde_las_filas` (`'obra_invalida' == 'demasiadas_filas'`) |
| O2 · sube por encima de la cuenta de filas | **Cae**: `test_f036_r115_mas_de_1000_filas_y_datos_por_debajo_dice_cuantas` |
| O3 · sube por encima de la cabecera | **Cae**: el mismo, primero con `-x` (el de «donde las filas» la caza también) |
| O4 · en `leer`, `_datos_fuera_del_tope` después de `_cabecera` y `_filas` | **Sobrevive (271 passed). Equivalente**, ver abajo |

- **Por qué O4 es equivalente.** `_filas` crea por posición las celdas de las
  filas 2–1002, columnas 1–8, y `_cabecera` crea las de la fila 1. Las únicas
  que caen en el territorio de `_datos_fuera_del_tope` (fila > 1001) son las de
  la fila 1002, y salen **vacías**, así que no cuentan como dato. El resultado
  es idéntico. El coste extra son unas 8.000 entradas más que iterar. No es
  una puerta frente a un colaborador.
- **Aceptación pendiente.** En `critico`, un equivalente a mano necesita la
  aceptación **escrita** del humano. Lo mismo vale para **M1a** del anexo de la
  review 1, que tampoco la tiene (ver cambio R2-2).
- **Las otras piezas del Bloque 10** no tienen puertas de orden: `_cabecera`,
  `_metadatos` y el texto del informe de migración.

### Checkpoints

#### C1 — El arnés está completo y en verde

- [x] `bash harness/init.sh`: ENTORNO LISTO. Además, la suite del `api` se
  ejecutó aparte sobre HEAD: 6035 passed.
- [x] Existen los ficheros del arnés (init.sh los comprueba).

#### C2 — El estado es coherente

- [x] Una sola `in_progress` (F-036); `blocked`: F-035, que no es de esta rama.
- [x] Rama `feature/F-036-importar-excel`.
- [x] `progress/current.md` empieza por el bloque vivo del Bloque 10 y las
  decisiones del humano tras la review 1.
- [x] Toda `done` en `history.md` (F-036 no lo es).

#### C3 — Arquitectura y convenciones

- [x] Hexagonal:
  - el dominio gana solo un `bool` en `LibroLeido` y una comprobación en
    `reconocer_plantilla`, sin imports nuevos;
  - `ws._cells` vive en el adaptador (`infrastructure/documentos/`), detrás de
    `_celdas_existentes`, que falla cerrado.
- [x] Primera línea con la ruta: el único fichero nuevo,
  `progress/mutacion_F-036_bloque10.md`, la lleva.
- [x] Sin `print()` de depuración, TODOs, secretos ni dependencias nuevas.
- N/A · «unidad de trabajo es el parte», «dry-run en Sigrid», «lo manuscrito»,
  «firmado no es conforme», «número de estado»: F-036 no procesa partes ni
  escribe en Sigrid (justificado en la review 1; el Bloque 10 no lo cambia).
- [x] Reprocesar no duplica: el Bloque 10 no toca la bandeja ni la huella.
- [x] Ningún parte, PDF ni `.xlsx` en git. El Bloque 10 no añade binarios (el
  diff solo trae `.py` y `.md`).

#### C3 bis — Documentos que entran de fuera

- N/A · El Bloque 10 no añade ni modifica nada en `docs/referencia/`. Aun así,
  el barrido de las líneas añadidas (patrones de la review 1: GUID, IP, correo,
  URL, hosts de entorno, claves, DNI/NIE/CIF, teléfono, IBAN), más los 36
  códigos y los nombres de proveedor del catálogo real, da **0 hallazgos**.

#### C4 — La verificación es real

- [ ] **R115 no se cumple entero.** Sus 29 tests pasan y el caso de la review 1
  está cerrado. Pero el requisito dice que el lector no recorre ninguna hoja
  posición a posición más allá de la plantilla, y un rango combinado o un
  hipervínculo sobre un rango lo hacen dentro de `load_workbook` (R2-1).
  Ningún test cubre ese caso.
- [x] R116 (3 tests, más el de R58), R13, R44 y R83 (por nombre) trazados y en verde. Tabla
  abajo.
- [x] Los unit tests no tocan red ni BBDD. Los de R116 usan catálogos
  inventados, y los de R115, libros en memoria.
- [x] Las `MANUAL (humano)` (T16, T27–T29) siguen en `tasks.md` con su comando.
  T28 y T29 ganan las comprobaciones de la sexta enmienda. T16, además, en
  `current.md`.

#### C4 bis — El rigor declarado se cumple

- [x] `rigor: "critico"`.
- [x] **Fase RED** con salida real:
  - T31: `27 failed, 1 passed` sobre el lector de antes; `35.57 < 1.0` en el
    de tiempo; y `assert False is True` una vez hecho el dominio, para que el
    rojo no fuera solo el campo que faltaba;
  - T32: el código inventado en el texto;
  - T33 y T34: sus fallos, también pegados.
- [x] **Cobertura:** `[OK]` 99,9 % (2805/2807).
- [x] **Mutación:** existe `mutacion_F-036_bloque10.md`, generado por la
  herramienta. Totales verificados de forma independiente: 94 líneas y 26
  mutantes.
- [x] **Muertos comprobados:** campaña de 26 min, **no reejecutada**; vale el
  recálculo puro. Los 3 supervivientes, reaplicados: caen.
- [x] **Coste por mutante:** 359,7 s con el factor de 6 workers.
- [ ] **Equivalentes a mano sin aceptación escrita del humano**: O4 (esta
  review) y M1a (anexo de la review 1). La herramienta no dejó ningún
  superviviente sin cerrar: 26/26 muertos.
- [x] «Evidencias» con los cuatro números y los workers (6).
- [x] Ningún N/A sin justificar en este bloque.

#### C4 ter — Rutas sensibles

- N/A: sigue sin existir `harness/rutas_sensibles.json`.

#### C5 — La sesión se cerró bien

- [x] `tasks.md`: T31–T34 en `[x]`, cada una con su commit `F-036 Tn:`
  (`7b90fa9` + `dee3824`, `d8fa8a4`, `b3ff374`, `1d44c34`). Siguen `[ ]`
  T16, T27, T28 y T29 (MANUAL) y T30 (el `init.sh` final): es lo esperado, no
  un defecto.
- [x] Sin ficheros temporales ni sin trackear.
- [x] `features.json` refleja el estado real: `in_progress`, sin el
  `blocked_by` obsoleto (cambio 4 resuelto).

### Desviaciones del Bloque 10

| Desviación | Juicio |
|---|---|
| B10-1 · `ws._cells` y no `read_only=True` | Válida por §5.2, fijada por un test y con fallo cerrado. **Pero** con R2-1 puede convenir `read_only`, que resuelve los dos casos a la vez. Lo decide el spec-author |
| B10-2 · mensaje propio cuando hay datos por debajo y menos de 1000 filas | Justificada: el mensaje literal diría un número falso. Mismo código, `demasiadas_filas`. Hay que alinear el recuadro de R20 («el error y su mensaje no cambian»): es una errata de la spec |
| B10-3 · qué es «un dato» por debajo del tope | Correcto: el mismo criterio que R23, con `Errores` fuera (R66). Medido arriba |
| B10-4 · la cabecera se lee por posición en 9 columnas y no en 10 | Resultado equivalente al de §5.2, sin romper R17. Bien |
| B10-5 · el GUID de la review 1 | Bien quitado: el fallo era real y lo destapó la caché (ver «Automejora»). La culpa es de la review 1, que citó el valor |
| B10-6 · `MAX_FILAS_METADATOS = 10` | Razonable, y fijado a mano en el test |
| B10-7 y B10-8 | Correctas |
| El script de migración sigue leyendo sin `max_row` | Fuera de R115, bien dicho: es local y sobre un fichero conocido |

### Cobertura: requisito → test (solo lo nuevo o renombrado)

| Req. | Test (uno representativo) | nº |
|---|---|---|
| R115 | `test_f036_excel_lector.py::test_f036_r115_celda_con_estilo_en_la_ultima_fila_se_lee_en_menos_de_un_segundo` | 26 en el lector (con parametrizados) + 3 en `test_f036_importacion_dominio.py` |
| R116 | `test_f036_migracion.py::test_f036_r116_el_informe_no_contiene_ningun_codigo_de_proveedor` | 2 + 1 en `test_f036_migracion_contenido.py`; además, el de R58 lo exige |
| R13 | `test_f036_consultas_catalogo.py::test_f036_r13_sql_oficios_de_la_obra_caracter_a_caracter` | 1 |
| R44 | `test_f036_ddl.py::test_f036_r44_bandeja_tiene_las_columnas_del_diseno_y_ninguna_mas` | 1 (más los `r44` que ya había) |
| R83 | `test_f036_ddl.py::test_f036_r83_decisiones_tiene_las_columnas_del_diseno_y_ninguna_mas` | 1 |
| R46 (cambio 5) | `test_f036_alcance_cerrado.py::test_f036_r46_los_bloques_7_y_8_tambien_estan_en_el_control` | 1 |

El resto de la tabla de la review 1 sigue vigente: los arreglos no quitaron
ningún test salvo `test_f036_r58_el_informe_marca_los_proveedores_completados_con_su_codigo`,
que exigía lo contrario de R116 y queda sustituido.

### Cambios requeridos

1. **R2-1 · [Bloquea el despliegue] Que `load_workbook` no pueda crear celdas
   por posición a partir de un rango.**
   - **Dónde:** `services/postventa-api/infrastructure/documentos/excel_openpyxl.py`,
     `_abrir` (~línea 452, `load_workbook(io.BytesIO(contenido), data_only=False)`),
     y el paso anterior, `_inspeccionar_zip` (~línea 418).
   - **Qué pasa:** 33 KB con `A1003:H1048576` combinado cuestan 169 s y
     2,6 GB, y con un hipervínculo sobre ese rango, 228 s y 4,1 GB (tablas de
     arriba). Vale en cualquier hoja del libro, no solo en «Incidencias».
   - **Qué hacer:** primero una **sexta enmienda bis** del spec-author, que
     amplíe R115 y §5.2 a los rangos que `openpyxl` expande al cargar. Después,
     una de estas dos salidas, con su prueba de tiempo y memoria:
     - **(a) Examen previo** de cada parte `xl/worksheets/*.xml`, antes de
       `_abrir`. Suma el área de todos los `mergeCell/@ref` y de los
       `hyperlink/@ref` que sean rango, y rechaza con `fichero_sospechoso` por
       encima de un tope pequeño (la plantilla no trae ninguno). Condiciones:
       - el XML se lee con `defusedxml`, en *streaming* y por nombre local de
         la etiqueta: una expresión regular sobre los bytes no basta, porque un
         prefijo de espacio de nombres (`<x:mergeCell>`) la esquiva;
       - un `ref` sin números de fila (p. ej. `A:H`), o que no se pueda leer,
         cuenta como el máximo.
     - **(b) `read_only=True`**, la segunda opción de §5.2, que ni combina ni
       enlaza hipervínculos. Medido: 0,08 s en los dos peores casos. Obliga a
       rehacer `_celdas_existentes`, `_cabecera` y `_parece_formato_antiguo`
       sin `ws._cells`, y a cerrar el libro.
   - **Tests** `test_f036_r115_…`:
     - los tres ficheros de arriba se leen o se rechazan en < 1 s y con el pico
       de `tracemalloc` bajo el tope que ya usan los tests;
     - lo mismo con el rango en `_plantilla` y en `Instrucciones`;
     - lo mismo sobre un Excel de errores;
     - un combinado pequeño dentro de la plantilla (p. ej. dos celdas de la
       fila 2) sigue admitido, o se rechaza, según decida la enmienda, pero
       dicho.
   - **Proceso:** con fase RED y la campaña de mutación con `--base 52f8149`.
     Además, en la review 3, las mutaciones de orden de la puerta nueva: tiene
     que ir antes de `load_workbook`.
   - **T29 paso 9:** gana el caso del combinado (ver arriba).
2. **R2-2 · [Antes de cerrar la feature; no bloquea T27] Aceptación escrita del
   humano de los dos equivalentes a mano:**
   - **O4** (esta review): `_datos_fuera_del_tope` antes o después de leer
     cabecera y filas da lo mismo;
   - **M1a** (anexo de la review 1): el `oid` antes o después del tope de
     2 MiB solo cambia si gana el 400 o el 413.

   Una línea en `progress/current.md` por cada uno, que exige C4 bis en
   `critico`. Trabajo del líder con el humano; no cambia código.
3. **R2-3 · [Puede esperar] Errata de la spec.** El recuadro de R20 en
   `specs/F-036-importar-excel/requirements.md` (~línea 355) dice «El error y
   su mensaje no cambian». Con B10-2, el código no cambia y el mensaje, en el
   caso nuevo, sí. Alinearlo con lo implementado en la misma enmienda de R2-1.

### Automejora (propuesta, no aplicada)

- **`harness/init.sh`, caché de la suite de servicio** (vale para `arnes-base`).
  - **El fallo:** la clave es `git rev-parse HEAD:$RUTA`, el árbol del
    servicio. Pero hay tests del servicio que barren **todo el repositorio**,
    como `test_f006_r26` sobre `progress/`. Un commit que solo toca `progress/`
    o `docs/` no invalida la caché, y el portero sale en verde sin haber
    mirado lo nuevo. Pasó dos veces en esta feature:
    - la review 1 salió en verde con un GUID en `progress/review_F-036.md`
      (B10-5);
    - el `init.sh` de esta review salió de caché sobre `52f8149`, que añade
      `progress/mutacion_F-036_bloque10.md` y 246 líneas a `impl_F-036.md`.
  - **Propuesta:** que la clave sea el árbol entero (`git rev-parse HEAD^{tree}`)
    para los servicios que declaren en `harness/servicios.json` que leen fuera
    de su ruta (p. ej. `"lee_fuera_de_su_ruta": true`); o, más simple, pasar
    esos tests de barrido a la suite de la raíz, que no se cachea.
- **`.claude/agents/reviewer.md`, punto nuevo en la validación de rigor**
  (vale para cualquier proyecto que lea ficheros subidos con una biblioteca de
  terceros). Cuando una feature ponga un tope de coste a un lector de ficheros,
  el reviewer prueba también las estructuras que la biblioteca **expande al
  cargar**, no solo las que el código recorre. En `openpyxl`: combinados,
  hipervínculos con rango y cualquier *binder* de `load_workbook`. Leer la lista
  de *binders* del cargador cuesta un minuto; la review 1 no lo hizo, y el
  hueco le pasó por delante.

## Review 3 (reviewer, 2026-09-30)

- **Veredicto:** CHANGES_REQUESTED
- **Rama:** `feature/F-036-importar-excel`, HEAD `becb693`. Revisado
  `git diff 7dd3bbe..HEAD`: 5 commits y 8 ficheros. En producción solo cambia
  `infrastructure/documentos/excel_openpyxl.py`.
- **Nivel de rigor:** `critico`, declarado. Puertas: fase RED, cobertura de las
  líneas cambiadas ≥ 80 %, mutación con cero supervivientes sin justificación
  aceptada por el humano, mutaciones de orden a mano y `MANUAL (humano)` con su
  comando.
- **Alcance:**
  - R2-1 y la prueba de al menos otro *binder* de `load_workbook`;
  - que nada de lo que dieron por bueno las reviews 1 y 2 se haya roto;
  - R2-3;
  - las mutaciones de orden de la apertura y el cierre;
  - la suite del `api` aparte.

  R2-2 está pendiente del humano y no se imputa al trabajo de agente.

### Resumen para el líder

**R2-1 está bien resuelto**, y el resto del alcance también:

- los ficheros de la review 2 se leen en 0,13–0,22 s y sin que crezca la
  memoria. Da igual la hoja («Incidencias», `_plantilla`, `Instrucciones`,
  `_catalogos») y también pasa en el Excel de errores;
- he probado un **tercer *binder*** que la review 2 no nombró: un comentario de
  celda cuyo `ref` es un rango. En modo normal, `openpyxl` hace `ws[ref]` y
  crea todo el rango. Con el lector de `52f8149` cuesta 38,6 s y 1,9 GB con
  34 KB; con el de HEAD, 0,14 s. El modo de solo lectura **sí cierra de raíz
  los *binders***;
- la suite del `api` entera, aparte: 6074 passed;
- el informe de migración, regenerado en el scratchpad, es idéntico;
- R2-3, corregido;
- 6 de 6 mutaciones de orden caen;
- la mutación cuadra al mutante.

**Aun así, no está listo para desplegar, por un hueco de la misma familia que
el solo-lectura no cierra** (R3-1):

- `load_workbook`, **también en solo lectura**, analiza entero `xl/styles.xml`
  (y `sharedStrings.xml`, el tema y `workbook.xml`);
- el lector analiza entera cada hoja que recorre, con todas sus estructuras;
- `openpyxl` gasta por elemento XML hasta unos 600 B y 20–25 µs;
- con eso, el tope de 20 MiB descomprimidos, que §0.1 y §5.2 («Riesgo que
  queda») dan por cota, **no acota**. **Un fichero de 64 KB con 4,1 millones de
  `<xf/>` en `styles.xml` cuesta 114 s y 2,5 GB de pico con el lector de
  HEAD.** De eso, 85 s son solo `load_workbook(read_only=True)`.

Es más memoria de la que tiene una instancia de Functions, en un servicio que
sirve todo `postventa-api`. **No es un error del implementer**: el lector de
`52f8149` tampoco termina a los 90 s. Es un hueco del diseño, que se apoya en
el tope de 20 MiB.

El arreglo que propongo cierra la **clase** entera y no un caso más (ver R3-1):
un presupuesto de elementos XML, contado en *streaming* antes de abrir. La
plantilla legítima más grande tiene unos 27.000 elementos. Como es la última
review antes del bloqueo, hay dos salidas:

- el spec-author y el implementer hacen R3-1;
- o el humano **acepta por escrito el riesgo residual**, con estas cifras
  delante. Hace falta un fichero fabricado a mano, y solo lo pueden subir
  usuarios autenticados.

### Verificación ejecutada por el reviewer

| Qué | Resultado |
|---|---|
| `bash harness/init.sh` (tal cual) | **ENTORNO LISTO**. Raíz: 62 passed. `api` y `front` salieron de la caché. `PUERTA COBERTURA: 99.9% de 2839 líneas cambiadas cubiertas (2837/2839, umbral 80%, nivel critico)`. ruff: 69 avisos (deuda). F-035 `blocked` |
| Suite del `api` aparte (`pytest -q -p no:cacheprovider` en `services/postventa-api`) | **6074 passed, 67 skipped** en 260,2 s, rc 0 |
| R2-1: ficheros construidos por el reviewer, a mano en el XML | 22 ficheros, cada uno en su subproceso. Tabla abajo |
| Otro *binder* | Comentario con `ref` de rango, en «Incidencias» y en `Instrucciones`. Además: combinado de la hoja entera `A1:XFD1048576`, `<x:mergeCells>` con prefijo, validación y formato condicional sobre la hoja entera |
| Coste por elemento dentro de los 20 MiB (nuevo) | 7 ficheros de 64–104 KB que llenan el tope. Hallazgo R3-1 |
| Mutación T36 | Recálculo puro cuadra: 144 líneas, 30 mutantes. Dos muertos muestreados caen |
| Mutaciones de orden de la apertura y el cierre | 6 de 6 caen |
| Migración | T24 regenerado en el scratchpad con `--solo-informe`: rc 0; informe **idéntico** al versionado salvo la línea 1 |
| Formato antiguo real (el original de OneDrive, solo leído) | HEAD y `52f8149` dan lo mismo: `formato_antiguo` |
| R2-3 | Recuadro de R20 corregido. El mensaje de `importacion.py:231` coincide literalmente con la errata corregida, y `test_f036_importacion_dominio.py:384` lo fija |
| Barrido de datos sensibles | 1055 líneas añadidas en `7dd3bbe..HEAD`, patrones de la review 1. Salen 12 coincidencias y las 12 son falsos positivos: `@pytest`, dos espacios de nombres de OOXML y `key=lambda`. **0 hallazgos reales** |
| Árbol de trabajo | `git status --porcelain` vacío antes de escribir este informe. Todo lo mutado y construido vivió en el scratchpad |

#### R2-1: lector de HEAD frente al de `52f8149`

Cada fichero corre en su propio subproceso. El pico es el *working set* máximo,
con unos 28 MB del intérprete. Los ficheros se construyen escribiendo el
`<mergeCells>`, el `<hyperlinks>` o el comentario **directamente en el XML**,
con un guion propio, no con los ayudantes de los tests. Para el control se
lanzaron cuatro ficheros con el lector de `52f8149`.

| Caso | Bytes | `52f8149` | HEAD |
|---|---:|---|---|
| Plantilla con 2 filas, sin nada | 33.359 | 0,08 s · 32 MB | 0,11–0,14 s · 29 MB |
| Combinado `A1003:A1048576` en «Incidencias» / `Instrucciones` / `_catalogos` | 33.390–33.395 | 16,3 / 16,5 / 14,6 s · 408 MB | 0,15–0,17 s · 29 MB |
| Combinado `A1003:H1048576` e hipervínculo sobre ese rango, en «Incidencias», `_plantilla`, `Instrucciones` y `_catalogos` | 33.391–33.425 | (review 2: 169 s y 228 s) | 0,13–0,16 s · 29 MB. Mismas filas `[2, 3]`, reconocida `0677` |
| Los tres, en un Excel de errores | 34.743–34.771 | — | 0,13–0,16 s · 29 MB. Fila `[2]` |
| Combinado de la hoja entera `A1:XFD1048576` | 33.393 | — | 0,16 s |
| `<x:mergeCells>` con prefijo de espacio de nombres | 33.460 | — | 0,22 s |
| **Comentario con `ref` `A1003:H1048576`** en `Instrucciones` (otro *binder*) | 33.964 | **38,6 s · 1.943 MB** | **0,14 s · 29 MB** |
| Validación y formato condicional sobre `A1:XFD1048576` | 33.401 / 33.443 | 0,11 s | 0,14 s |

Conclusiones:

- **Resuelto.** El modo de solo lectura no pasa por `bind_all` ni por la
  asignación de comentarios, así que ninguna estructura de hoja se expande al
  cargar.
- **Combinado pequeño** (`C2:D2`): se admite, como decide la enmienda.
- **T35-6 (b):** un fichero manipulado con valor en las celdas escondidas de
  un combinado se lee con ese valor, y el importador lo valida como cualquier
  otro. Lo acepto.

#### R3-1: coste por elemento dentro de los 20 MiB (hallazgo nuevo)

Cada fichero es la plantilla de 2 filas más un solo tipo de elemento repetido
hasta rozar los 20 MiB descomprimidos. Comprimidos, quedan muy por debajo de
2 MiB. Las cifras son de un proceso por fichero, con la máquina sin otra carga
mía.

| Qué se repite | Dónde | Elementos | Bytes | HEAD | `52f8149` |
|---|---|---:|---:|---|---|
| `<xf/>` | `xl/styles.xml` (se lee en `load_workbook`) | 4.135.650 | 63.622 | **113,9 s · 2.485 MB** (solo `load_workbook(read_only=True)`: 84,8 s) | cortado a los 90 s |
| `<dataValidation sqref="J2"/>` | «Incidencias» | 738.507 | 84.159 | **68,7 s · 901 MB** | 46,5 s · 904 MB |
| `<brk id="1"/>` (`rowBreaks`) | «Incidencias» | 1.590.632 | 74.443 | **48,1 s · 858 MB** | 16,1 s · 860 MB |
| `<mergeCell ref="J2:K2"/>` | «Incidencias» | 861.592 | 84.141 | 34,7 s · 517 MB | cortado a los 90 s |
| Celda vacía con estilo en la fila 1200 | «Incidencias» | 1.033.911 | 84.019 | 17,8 s · 647 MB | 11,7 s · 653 MB |
| Formato condicional de una celda | «Incidencias» | 164.113 | 104.239 | 18,8 s · 240 MB | 15,5 s · 245 MB |
| `<hyperlink ref="J2"/>` | «Incidencias» | 626.612 | 94.470 | 16,2 s · 393 MB | 10,2 s · 397 MB |

- **Qué es.** No es una expansión por posición, así que la letra de R115
  ampliado se cumple. Es el coste de `openpyxl` por **elemento** que analiza:
  - al cargar, en los dos modos: estilos y cadenas compartidas;
  - al recorrer una hoja: todas sus estructuras. `WorkSheetParser.parse` hace
    `from_tree` de `mergeCells`, `hyperlinks`, `dataValidations`,
    `rowBreaks`…, aunque el lector solo quiera las filas.
- **Por qué no lo acota el tope de 20 MiB.** Con 5 bytes por elemento caben
  4 millones de elementos. Con unos 600 B por objeto salen 2,5 GB.
- **Qué cambia frente a `52f8149`.** El lector de HEAD analiza «Incidencias»
  **dos veces enteras**: `_datos_fuera_del_tope`, y `_filas`, que en solo
  lectura no para hasta el final si no hay filas por debajo de la 1002. Por
  eso las estructuras de hoja cuestan de 1,5 a 3 veces más tiempo que antes,
  con la misma memoria. El implementer lo midió en el caso normal
  (0,05 → 0,09 s), pero no con muchos elementos.
- **El número que importa.** La plantilla legítima más grande que he podido
  generar tiene **26.886 elementos XML** y 2,6 MiB descomprimidos: 1000 filas
  con un detalle de 2000 caracteres, generadas con el generador de la rama.
  Contar los 4,1 millones del fichero de estilos con `expat` cuesta 2,65 s
  **sin cortar**; cortando al pasar el presupuesto, es proporcional al
  presupuesto.

### Mutación (T36): recálculo independiente

- **Alcance y mutantes.** Recalculé el alcance con `harness.alcance`
  (`parsear_diff` + `filtrar_produccion` sobre `git diff -U0 52f8149 <ref>`) y
  los mutantes con `harness.mutacion.generar_mutantes` sobre el contenido en
  `<ref>`:
  - con `<ref>` = `84ee911`, el árbol de la campaña, y con HEAD: `excel_openpyxl.py`,
    **144 líneas y 30 mutantes, igual que el informe**. Por operador:
    12 `entero`, 6 `booleano`, 5 `comparacion`, 4 `logico` y 3 `aritmetico`;
  - entre `84ee911` y HEAD no cambia ninguna línea de producción.
- **Campaña no reejecutada: 958,4 s (16 min) según el informe.** Pasa de
  5 min, así que vale el recálculo puro.
- **Coste por mutante:** 958,4 × 6 ÷ 30 = **191,7 s**. Es coherente con una
  suite de unos 260–290 s en serie, con 6 workers compitiendo.
- **Cero supervivientes**, así que no hay supervivientes que muestrear.
  Muestreé dos muertos en una copia de `git archive HEAD` del scratchpad:
  - `read_only=True → False` cae con `test_f036_r16_500_entradas_se_admiten`;
  - `fila <= ULTIMA_FILA → <` cae con `test_f036_r20_1000_filas_se_admiten`.

### Orden (punto 7): apertura y cierre

En una copia desechable, con `tests/test_f036_excel_lector.py` entero y sin
`-x`. Solo corren los tests de esta feature. Línea base: 139 passed.

| Mutación | Resultado |
|---|---|
| O1 · `libro.close()` justo después de `_abrir`, antes de `_extraer` | **Cae**: 120 failed |
| O2 · `close` solo si la lectura va bien (sin `finally`) | **Cae**: 10 failed (`…_el_libro_se_cierra_aunque_la_lectura_falle_a_medias`) |
| O3 · `close` en el camino bueno y ninguno en los de error | **Cae**: 11 failed |
| O4 · `_abrir` antes de `_inspeccionar_zip` | **Cae**: 4 failed (`test_f036_r16_con_macros_se_rechaza_sin_abrirlo`…) |
| O5 · `_inspeccionar_zip` antes del tope de 2 MiB | **Cae**: `test_f036_r15_mas_de_2_mib_se_rechaza_sin_mirar_nada` |
| O6 · `_abrir` antes del tope de 2 MiB | **Cae**: 19 failed |

- **Ningún equivalente nuevo.**
- **Apertura en modo normal:** la única llamada a `load_workbook` del lector
  es la de `_abrir` (`grep`). El doble de los tests exige `read_only=True` en
  los cuatro tipos de fichero.
- **Pendiente del humano (R2-2):** siguen sin su aceptación escrita O4 de la
  review 2 y M1a de la review 1.

### Checkpoints

#### C1 — El arnés está completo y en verde

- [x] `bash harness/init.sh`: ENTORNO LISTO. La suite del `api`, aparte:
  6074 passed, 67 skipped.
- [x] Existen los ficheros del arnés (init.sh los comprueba).

#### C2 — El estado es coherente

- [x] Una sola `in_progress` (F-036). `blocked`: F-035, que no es de esta rama.
- [x] Rama `feature/F-036-importar-excel`.
- [x] `progress/current.md` empieza por el bloque vivo de T35–T36.
- [x] Toda `done` tiene su entrada en `history.md` (F-036 no lo es).

#### C3 — Arquitectura y convenciones

- [x] Hexagonal: el cambio está entero en el adaptador
  (`infrastructure/documentos/`). El dominio no se toca. La API privada de
  `openpyxl` (`WorkSheetParser`, `_get_source`) queda detrás de
  `_filas_presentes`, que falla cerrado y tiene un test que la fija.
- [x] Primera línea con la ruta en el único fichero nuevo
  (`progress/mutacion_F-036_bloque10bis.md`).
- [x] Sin `print()` de depuración, TODOs, secretos ni dependencias nuevas.
- N/A · «unidad de trabajo es el parte», «dry-run en Sigrid», «lo manuscrito»,
  «firmado no es conforme» y «número de estado»: F-036 no procesa partes ni
  escribe en Sigrid. Está justificado en la review 1, y T35–T36 no cambian
  nada de eso.
- [x] Reprocesar no duplica: T35–T36 no tocan la bandeja ni la huella.
- [x] Ningún parte, PDF ni `.xlsx` en git. El diff solo trae `.py` y `.md`, y
  los ficheros de prueba se construyen en memoria (los míos, en el scratchpad).

#### C3 bis — Documentos que entran de fuera

- N/A · Nada nuevo en `docs/referencia/`. El barrido de las líneas añadidas
  está en la tabla de verificación: 0 hallazgos reales.

#### C4 — La verificación es real

- [x] R115 ampliado tiene trazabilidad y está en verde (tabla abajo). Por su
  letra, lo que la biblioteca expande al cargar, está cumplido y verificado de
  forma independiente. R3-1 queda fuera de esa letra: cae en el riesgo de
  §0.1 y en la afirmación de §5.2 «Riesgo que queda».
- [x] Los unit tests no tocan red ni BBDD: libros en memoria.
- [x] Las `MANUAL (humano)` (T16, T27–T29) siguen en `tasks.md` con su
  comando. T29 paso 9 gana el caso del combinado. T16 está además en
  `current.md`.

#### C4 bis — El rigor declarado se cumple

- [x] `rigor: "critico"`.
- [x] **Fase RED** con salida real:
  - `16 failed, 29 passed` con los rápidos;
  - 15 rojos con los ficheros de la review, por tiempo (13,6–17,1 s frente a
    1 s) o cortados a los 20 s en subproceso.
- [x] **Cobertura:** `[OK]` 99,9 % (2837/2839).
- [x] **Mutación:** existe `mutacion_F-036_bloque10bis.md`, generado por la
  herramienta, y sus totales están verificados de forma independiente:
  144 líneas y 30 mutantes.
- [x] **Muertos comprobados:** la campaña duró 16 min y **no se reejecuta**;
  vale el recálculo puro. Dos muertos muestreados: caen.
- [x] **Coste por mutante:** 191,7 s con el factor de 6 workers.
- [x] Ningún superviviente de la herramienta. Las 6 mutaciones de orden a
  mano caen; ningún equivalente nuevo.
- [ ] **Pendiente del humano (R2-2), no imputable al trabajo de agente:**
  falta la aceptación escrita de los equivalentes O4 y M1a. No bloquea T27,
  pero sí el cierre.
- [x] «Evidencias» con los cuatro números y los workers (6).
- [x] Ningún N/A sin justificar en este bloque.

#### C4 ter — Rutas sensibles

- N/A: sigue sin existir `harness/rutas_sensibles.json`.

#### C5 — La sesión se cerró bien

- [x] `tasks.md`: T35 (`84ee911`) y T36 (`5600388`) en `[x]`, con su commit
  `F-036 Tn:`. Siguen `[ ]` T16 y T27–T29, que son MANUAL, y T30, que es el
  `init.sh` final. Es lo esperado.
- [x] Sin ficheros temporales ni sin trackear.
- [x] `features.json`: `in_progress`, sin `blocked_by`.

### Desviaciones de T35–T36

| Desviación | Juicio |
|---|---|
| T35-1 · `WorkSheetParser` y no una pasada a mano con `defusedxml` | Válida por §5.2. Conserva el criterio de B10-3 sin reimplementar la conversión de valores, está fijada por un test y falla cerrado |
| T35-2 · `_parece_formato_antiguo` mira `A1:I10`, no `A1:E10` | **Aceptada**: R17 pide la fila 1 sin la cabecera de R2, que tiene 9 columnas, y el test de `I1` es anterior. El texto de T35 y el de §5.2 «Al cargar» (`max_col=5`) quedan como errata (R3-2) |
| T35-3 · la cabecera con el analizador y no con `iter_rows` | Correcta: no se fía del `<dimension>` declarado. Si el XML trae las filas desordenadas, la cabecera sale vacía y el fichero se rechaza (falla cerrado) |
| T35-4 · la fila por el número del `<row>` | Correcta: es el mismo criterio que `iter_rows` en solo lectura |
| T35-5 · lo que falla al recorrer es `no_es_xlsx` | Correcta. Lo fijan O3 del implementer y mi O2/O3 |
| T35-6 · XML roto en una hoja que no se recorre, celdas escondidas de un combinado, comentarios | Aceptadas y dichas |
| T35-7 · el informe de migración no se regenera en el repositorio | Correcta: lo he regenerado en el scratchpad y es idéntico |

### Cobertura: requisito → test (solo lo nuevo)

| Req. | Test (uno representativo) | nº |
|---|---|---|
| R115 (ampliado: al cargar) | `test_f036_excel_lector.py::test_f036_r115_rango_que_openpyxl_expande_al_cargar_se_lee_en_menos_de_un_segundo` | 11 funciones nuevas, 57 casos con los parametrizados. Además siguen los 18 `test_f036_r115_…` de T31 |
| R115 (cerrar siempre) | `…::test_f036_r115_el_libro_se_cierra_aunque_la_lectura_falle_a_medias` | 10 casos, más 4 de `…_se_abre_en_solo_lectura_y_se_cierra` |
| R20 (errata R2-3) | `test_f036_importacion_dominio.py` (el mensaje del caso nuevo, línea 384) | 1 |

El resto de las tablas de las reviews 1 y 2 sigue vigente. Salen los dos tests
que fijaban `ws._cells`, y los sustituye
`…_el_analizador_de_filas_de_openpyxl_es_el_que_se_espera`.

### Cambios requeridos

1. **R3-1 · [Bloquea el despliegue salvo que el humano acepte por escrito el
   riesgo] Un presupuesto de elementos XML antes de abrir el libro.**
   - **Dónde:**
     - `services/postventa-api/infrastructure/documentos/excel_openpyxl.py`:
       `_inspeccionar_zip` (~línea 418), o un paso nuevo entre ese y `_abrir`
       (~línea 458);
     - `LectorPlantillaOpenpyxl.leer` (~línea 710).
   - **Qué pasa:** la tabla de R3-1. Con 64 KB, 114 s y 2,5 GB, y 85 s solo en
     `load_workbook(read_only=True)`. Con 74–84 KB en «Incidencias», de 35 a
     69 s y de 0,5 a 0,9 GB.
   - **Qué hacer:** primero una enmienda del spec-author que diga lo que el
     tope de 20 MiB **no** acota (§0.1, §5.2 «Riesgo que queda») y fije un
     **presupuesto global de elementos XML** para todas las partes `.xml` y
     `.rels` del ZIP. Condiciones:
     - se cuenta en *streaming*, con el analizador *expat* de `defusedxml`
       (sin DTD ni entidades);
     - se corta al pasar el presupuesto, así que el coste es proporcional al
       presupuesto y no al fichero;
     - se cuentan elementos de apertura, no etiquetas por nombre: no depende
       del espacio de nombres ni de qué estructura sea, así que cierra la
       clase entera, también lo que `openpyxl` añada mañana. A este diseño no
       le aplica la objeción de §5.2 a la opción (a), que era mantener un
       analizador por estructura;
     - por encima del presupuesto, `fichero_sospechoso` (R16).

     **Calibración:** la plantilla completa (1000 filas, detalle de 2000)
     tiene 26.886 elementos. Un presupuesto de unos 200.000 da 7 veces de
     margen y acota el peor caso medido: 200.000 × ~600 B ≈ 120 MB, unos 5 s.
     Hay que confirmar con T29 que un `v2` guardado desde Excel, que añade
     `sharedStrings` y estilos, queda muy por debajo.
   - **De paso (no obligatorio):** `_datos_fuera_del_tope` y `_filas` podrían
     compartir una sola pasada por «Incidencias», porque hoy son dos pasadas
     enteras (ver R3-1). Con el presupuesto deja de ser crítico.
   - **Tests** `test_f036_r16_…` o `test_f036_r115_…`:
     - los siete ficheros de la tabla de R3-1, construidos en memoria, se
       rechazan en < 1 s y con el pico de `tracemalloc` bajo el tope de los
       tests;
     - la plantilla completa de 1000 filas se admite;
     - el conteo corta al pasar el presupuesto (un doble que cuente cuántos
       elementos se leyeron).
   - **Proceso:**
     - fase RED;
     - campaña con `--base becb693`;
     - en la review, la mutación de orden de la puerta nueva: tiene que ir
       **antes** de `load_workbook`, y la suite tiene que ponerse en rojo si
       baja por debajo;
     - T29 paso 9 gana el caso de los estilos, con el fichero construido por
       el reviewer.
   - **Alternativa del humano:** aceptar por escrito en `current.md` el riesgo
     residual. Solo lo provoca un fichero fabricado a mano, y lo sube un
     usuario autenticado de Posventa. Coste medido: hasta 114 s y 2,5 GB por
     petición en el peor caso, dentro de los 2 MiB y de los 20 MiB. Con esa
     aceptación, el trabajo de agente de T35–T36 estaría listo para T27.
2. **R3-2 · [Puede esperar] Errata de la spec.** El texto de T35
   (`tasks.md`, «una pasada `A1:E10`») y el de §5.2 «Al cargar»
   (`_parece_formato_antiguo`, `max_col=5`) no casan con lo aceptado en
   T35-2: tienen que decir `A1:I10`, las 9 columnas de la cabecera de R2.
   Además, §5.2 «Riesgo que queda» dice que «lo acotan los recorridos, que
   están todos limitados», y no es exacto: `_datos_fuera_del_tope` recorre
   entera la hoja. Se alinea en la misma enmienda de R3-1.
3. **R2-2 · [Pendiente del humano; no bloquea T27] Sin cambios:** falta la
   aceptación escrita de O4 y M1a.

### Qué debe mirar el humano

- **Antes de T27:** decidir R3-1: hacer el arreglo o aceptar el riesgo por
  escrito.
- **T16, T27 y T28:** lo que dijo la review 2, sin cambios.
- **T29 paso 9:** además de lo de la review 2, una copia del `v2` con
  `A1003:A1048576` combinadas tiene que responder al momento y leerse normal.
  Esto está ya verificado aquí contra el lector.
- **Si se hace R3-1:** medir el `v2` guardado desde Excel frente al
  presupuesto.

### Automejora (propuesta, no aplicada)

- **`.claude/agents/reviewer.md`**, punto nuevo en la validación de rigor. Vale
  para `arnes-base` y completa la propuesta de la review 2.
  - **Cuándo:** una feature pone un tope de coste a un lector de ficheros
    subidos que usa una biblioteca de terceros.
  - **Qué probar:** además de lo que la biblioteca **expande**, lo que
    **analiza elemento a elemento**. Por cada parte que la biblioteca lee
    entera (en `openpyxl`: estilos, cadenas compartidas y las hojas que se
    recorren), se llena el tope de tamaño descomprimido con el elemento más
    pequeño que la biblioteca convierte en objeto (`<xf/>`,
    `<dataValidation/>`, `<brk/>`) y se mide.
  - **Por qué:** un tope en bytes no acota nada si el coste por byte no está
    acotado. La review 2 miró los *binders* y dejó pasar esto; la review 1 no
    miró ninguna de las dos cosas.

## Review 4 (reviewer, 2026-10-01)

- **Veredicto:** CHANGES_REQUESTED
- **Rama:** `feature/F-036-importar-excel`, HEAD `c7086fb`. Revisado
  `git diff a80b8e2..HEAD`: 13 ficheros. En producción cambian
  `infrastructure/documentos/excel_openpyxl.py` y el script nuevo
  `scripts/contar_elementos_xml_f036.py`.
- **Nivel de rigor:** `critico`, declarado. Puertas: fase RED, cobertura de las
  líneas cambiadas ≥ 80 %, mutación con cero supervivientes sin justificación
  aceptada por el humano, mutaciones de orden a mano y `MANUAL (humano)` con su
  comando.
- **Alcance:**
  - R3-1, con R117 en su séptima enmienda y en la bis (T37-1, opción (a));
  - R3-2;
  - que no se rompa nada de lo ya aprobado;
  - las mutaciones de orden de la puerta nueva;
  - T37 bis-1 (el coste del peor caso admitido).

### Resumen para el líder

**Lo que se pidió está bien hecho:**

- R117 está implementado como dice la spec. La puerta va antes de
  `load_workbook` y las mutaciones de orden lo confirman (tabla abajo).
- Los siete ficheros de la review 3 y el `sheet1.dat` de T37-1 se rechazan con
  `fichero_sospechoso`, sin abrir el libro, en los tests que lo fijan, y esos
  tests pasan.
- R3-2 está corregido.
- La suite del `api` entera, aparte: **6138 passed, 67 skipped**.
- El informe de migración regenerado es idéntico.
- El formato antiguo real sigue reconociéndose.
- La mutación cuadra al mutante.

**Aun así, R3-1 no queda cerrado como clase** (R4-1, hallazgo nuevo). El
presupuesto cuenta **elementos**. Hay atributos que `openpyxl` convierte en
**un objeto por cada rango** que listan, dentro de un solo elemento: el `sqref`
de las validaciones de datos, del formato condicional y de los escenarios. El
recuento ve ahí un elemento, y el coste va por los bytes del atributo, que solo
acota el tope de 20 MiB.

- Lo he comprobado leyendo el código de `openpyxl` 3.1.5 y midiendo **solo la
  función de la biblioteca** (`MultiCellRange`): unos 7,5 µs y 227 B por rango.
- Extrapolado a lo que cabe en 20 MiB, es del orden de **50 s y 1,6 GB por
  pasada**, y «Incidencias» se recorre entera al menos una vez, normalmente dos.
- **No he construido el fichero completo de extremo a extremo.** La cifra es
  una estimación y la confirmará la fase RED del arreglo.

Es la misma familia que R3-1, y la review 3 dio por cerrada la clase con el
recuento de elementos: **se equivocó**. El arreglo propuesto, o la aceptación
escrita del riesgo, está en «Cambios requeridos».

**T37 bis-1** (el peor caso admitido, 23,4 s y 389 MB): **es aceptable** con el
presupuesto de 300.000. No hace falta bajarlo, pero §5.2 tiene que llevar la
cifra medida y no la estimada (razonamiento abajo, R4-2).

### Verificación ejecutada por el reviewer

| Qué | Resultado |
|---|---|
| `bash harness/init.sh` (tal cual) | **ENTORNO LISTO**. Raíz: 62 passed. `api` y `front` salieron de la caché. `PUERTA COBERTURA: 99.9% de 2916 líneas cambiadas cubiertas (2913/2916, umbral 80%, nivel critico)`. ruff: 69 avisos (deuda). F-035 `blocked`, que no es de esta rama |
| Suite del `api` aparte (`.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider` en `services/postventa-api`) | **6138 passed, 67 skipped** en 356,2 s, rc 0 |
| `tests/test_f036_excel_lector.py`, en una copia de `git archive HEAD` del scratchpad | Línea base: **202 passed** en 187,5 s |
| R3-1 (los siete ficheros y el `sheet1.dat` de T37-1) | Cubiertos por los tests que lo fijan: `…_los_ficheros_de_la_review_3_se_rechazan_en_menos_de_un_segundo` (7 casos), `…_con_la_memoria_acotada` (7), `…_la_hoja_en_un_dat_se_rechaza_en_menos_de_un_segundo` y `…_un_bin_con_xml_por_encima_del_presupuesto_se_rechaza`. Pasan en la línea base, y caen todos cuando la puerta se baja o se quita (abajo). **No los he reconstruido aparte**: ver «Lo que no he hecho, dicho» |
| Otra vía de saltarse el recuento | **R4-1**: un atributo con una lista de rangos. Comprobado leyendo `openpyxl` 3.1.5 y midiendo solo `MultiCellRange` |
| Mutación T38 bis y T38: recálculo puro | Cuadra (abajo) |
| Mutaciones de orden de la puerta (punto 7) | **5 de 5 caen** (abajo) |
| Muertos muestreados | 2 de 2 caen (abajo) |
| Migración | `scripts/migrar_excel_f036.py … --solo-informe`, al scratchpad: rc 0; 144 → 158, 14 separadas, 0 descartadas, **0 errores en la ida y vuelta**; `sha256` del original igual antes y después; informe **idéntico** al versionado salvo la línea 1 |
| Formato antiguo (el original de OneDrive, solo leído) | El lector de HEAD da `parece_formato_antiguo=True`; el script cuenta **1.680** elementos, por debajo de un quinto |
| R3-2 | Corregido: `design.md` §5.2 «Al cargar» (`A1:I10`, `max_col=9`), `tasks.md` T35 (`A1:I10`) y el párrafo «Riesgo que queda», reescrito con la cita del texto anterior. El código ya usaba `max_col=len(CABECERA)` |
| Barrido de datos sensibles | 2201 líneas añadidas en `a80b8e2..HEAD`, con los patrones de la review 1 (GUID, correo, IP privada, `password`, `secret`, `api_key`, `token`, `AccountKey`, `SharedAccess`, `Bearer`, claves PEM). Salen 13 coincidencias y las 13 son falsos positivos (`@pytest`, `@functools`). **0 hallazgos reales** |
| `print` | Solo en la salida de la CLI del script (sin contenido del fichero) y en el código que un test lanza en un subproceso para medir. Ninguno de depuración |
| Árbol de trabajo | `git status --porcelain` vacío antes de escribir este informe. Todo lo mutado vivió en el scratchpad |

#### Mutación (T38 bis y T38): recálculo independiente

- **Alcance y mutantes.** Recalculé con `harness.alcance` (`parsear_diff` y
  `filtrar_produccion` sobre `git diff -U0 <base> <ref>`) y con
  `harness.mutacion.generar_mutantes` sobre el contenido en `<ref>`:
  - `--base 29e28a6`, con `<ref>` = `d8572f4` y con HEAD: `excel_openpyxl.py`,
    **37 líneas y 5 mutantes, igual que el informe**. Por operador: 1
    `entero`, 2 `booleano`, 1 `logico` y 1 `comparacion`. Son los cinco que
    nombra el informe del implementer, con el mismo texto original y mutado;
  - `--base becb693`, con `<ref>` = `a370b1d`: **159 líneas (84 + 75) y 22
    mutantes, igual que `mutacion_F-036_bloque10ter.md`**.
- **Campañas no reejecutadas.** Según sus informes, la de T38 bis tardó 335,4 s
  (5,6 min) y la de T38, 1436,5 s (24 min). Las dos pasan de 5 min, así que
  vale el recálculo puro.
- **Coste por mutante.**
  - T38 bis: 335,4 × 5 ÷ 5 = **335 s**, coherente con una suite de unos 300 s.
    El informe de la herramienta dice **5 workers**; «Evidencias» y `tasks.md`
    dicen 6 (R4-3). Con 6 saldrían 402 s, igual de coherente.
  - T38: 1436,5 × 6 ÷ 22 = 392 s.
- **Muertos muestreados**, en la copia del scratchpad y con el fichero de tests
  del lector entero:
  - `se_declara_xml or fallo.code == … → and` **cae**: 5 failed (`rels-cortado`,
    `xml-roto`, `bin-entidad-sin-declarar`, `png-xml` y el script con un XML
    roto);
  - `Parse(b"", True) → False` **cae**: 1 failed (`rels-cortado`).
- **Cero supervivientes** en T38 bis. En T38, los 4 están cerrados con tests:
  `…_cada_parte_se_lee_por_trozos_de_64_kib` y
  `…_el_analizador_lleva_las_tres_defensas_de_defusedxml`, en verde.

#### Orden (punto 7): la puerta de R117

En una copia desechable de `git archive HEAD`, aplicando cada mutación sobre
`LectorPlantillaOpenpyxl.leer` y pasando `tests/test_f036_excel_lector.py`
entero, sin `-x` y sin bytecode (`__pycache__` borrado en cada pasada). Solo
corren los tests de esta feature.

| Mutación | Resultado |
|---|---|
| OA · el recuento **un paso abajo**, justo después de `_abrir` (es decir, de `load_workbook`) | **Cae**: 27 failed. Los siete de tiempo y los siete de memoria, los de partes que no se analizan, el `.dat` de T37-1, el `.bin`, DTD o entidad en cualquier parte y `…_el_recuento_va_antes_de_abrir_el_libro` |
| OB · el recuento antes de `_inspeccionar_zip` | **Cae**: 7 failed |
| OC · el recuento antes del tope de 2 MiB | **Cae**: 9 failed (`test_f036_r15_mas_de_2_mib_se_rechaza_sin_mirar_nada`…) |
| OD · sin recuento | **Cae**: 34 failed |
| OE · volver a filtrar por extensión (`if not se_declara_xml: continue`) | **Cae**: 12 failed (el `.dat`, el `.bin`, la imagen, la parte que falla a mitad, el Excel de errores con el VML…) |

- La puerta precede a un colaborador, `load_workbook` (vía `_abrir`). Bajarla
  un paso pone en rojo tests **de la propia feature**.
- Coincide con lo que anotó el implementer (O7–O11), con las mismas cifras.
- Ningún equivalente nuevo.

#### R4-1: un atributo con una lista de rangos (hallazgo nuevo)

**Qué dice el código** (`openpyxl` 3.1.5, el del `.venv`):

- `WorkSheetParser.parse` (`worksheet/_reader.py`) hace `from_tree` de
  `dataValidations` (`DataValidationList`), de cada `conditionalFormatting`
  (`parse_formatting`) y de `scenarios`. Pasa **también en solo lectura**, en
  cada recorrido que llega al final de la hoja.
- En los tres, `sqref` es `Convertible(expected_type=MultiCellRange)`
  (`worksheet/datavalidation.py:78`, `formatting/formatting.py:21`,
  `worksheet/scenario.py:81`). `MultiCellRange(str)` hace
  `[CellRange(r) for r in ranges.split()]`: **un objeto por cada rango del
  atributo**. Confirmado con `DataValidationList.from_tree` sobre un `sqref` de
  cuatro rangos: salen 4 `CellRange`.
- El lector recorre «Incidencias» entera al menos una vez
  (`_datos_fuera_del_tope`, con `_filas_presentes`). Lo normal son dos, porque
  `_filas` también llega al final si no hay filas por debajo de la 1002 (§5.2
  lo dice). `_plantilla` también se recorre entera si tiene menos filas que el
  tope de los metadatos.

**Por qué no lo para R117:** el recuento suma uno por elemento de apertura. Un
elemento con un millón de rangos en su `sqref` cuenta uno. Esos bytes solo los
acota el tope de 20 MiB, y un texto tan repetitivo cabe de sobra en los 2 MiB
comprimidos.

**Lo medido:** solo la función de la biblioteca, en proceso, sin construir
ningún `.xlsx`:

- `MultiCellRange` con 200.000 rangos: 1,5 s, es decir, **~7,5 µs por rango**;
- **~227 B por rango** de memoria (`tracemalloc`, con 50.000 y 200.000).

**Extrapolación** (no medida de extremo a extremo):

- con unos 3 bytes por rango, en 20 MiB caben unos 7 millones: ≈ **50 s y
  1,6 GB por pasada**;
- con dos pasadas, del orden de **100 s**;
- es el mismo orden que el caso de 114 s y 2,5 GB que motivó R3-1;
- pasa de los 45 s del proxy y se acerca a los 2 GB por instancia de Flex
  Consumption, en la Function que sirve también el circuito de partes en
  producción.

#### T37 bis-1: el peor caso admitido (23,4 s y 389 MB)

**Juicio: aceptable con el presupuesto de 300.000.** No hace falta bajarlo, ni
una aceptación escrita aparte, pero §5.2 tiene que llevar la cifra medida
(R4-2). Razones:

- **Tiempo.**
  - 23,4 s es el peor tipo medido (`<dataValidation/>`, ~78 µs por elemento
    con las dos pasadas). El coste es lineal por tipo, así que una mezcla no
    supera al peor tipo puro. Esto vale **dentro** de R117. R4-1 queda fuera
    de este juicio.
  - Cabe en los **40 s** de `TIMEOUT_PETICION_MS` del front y en los **45 s**
    del proxy, con un margen de 1,7 y 1,9 veces.
  - El balanceador (230 s) y el `functionTimeout` (5 min) no aprietan aquí:
    corta antes el proxy.
  - **El margen no es grande:** se midió en la máquina de desarrollo y con
    carga, y una vCPU de Flex Consumption puede ser más lenta. Si una petición
    así pasara de 40 s, el front vería un error. La Function terminaría por
    detrás, y un reintento daría `ya_importado` por la huella. Nunca hay
    escritura en Sigrid.
- **Memoria.** 389 MB de pico, frente a 2 GB por instancia de Flex Consumption
  (el valor por defecto; `infra/desplegar_backend.ps1` no fija otro).
- **El circuito de partes.** En Flex Consumption, Python atiende por defecto
  una petición HTTP por instancia, y se escala con más instancias. Una
  petición de 23 s ocupa una; las de partes van a otras, con el posible
  arranque en frío. Si se subiera la concurrencia por instancia, competirían
  por el GIL durante esos segundos: se ralentizan, pero no caen.
- **Quién lo provoca.** Hace falta un fichero fabricado a mano, y lo sube un
  usuario autenticado de Posventa.
- **Bajar el presupuesto no compensa.** Con 200.000, el Excel de errores más
  grande (148.916) quedaría a 1,34 veces del tope, y Excel reescribe
  comentarios y VML al guardar. Se ganarían unos 8 s dentro de un límite que
  ya se cumple, a cambio de arriesgarse a rechazar ficheros legítimos.

### Checkpoints

#### C1 — El arnés está completo y en verde

- [x] `bash harness/init.sh`: ENTORNO LISTO. La suite del `api`, aparte:
  6138 passed, 67 skipped.
- [x] Existen los ficheros del arnés (init.sh los comprueba).

#### C2 — El estado es coherente

- [x] Una sola `in_progress` (F-036). `blocked`: F-035, que no es de esta rama.
- [x] Rama `feature/F-036-importar-excel`.
- [x] `progress/current.md` empieza por el bloque vivo de T37 bis–T38 bis.
- [x] Toda `done` tiene su entrada en `history.md` (F-036 no lo es).

#### C3 — Arquitectura y convenciones

- [x] **Hexagonal:** el cambio está entero en el adaptador
  (`infrastructure/documentos/`). El script importa del adaptador y del
  dominio, como los otros tres scripts de F-036, y está en `NUEVOS_DE_F036`,
  así que le aplican los controles de R46.
- [x] **Primera línea con la ruta** en los ficheros nuevos (el script y los dos
  informes de mutación).
- [x] Sin `print()` de depuración, TODOs, secretos ni dependencias nuevas:
  `defusedxml` ya estaba.
- N/A · «unidad de trabajo es el parte», «dry-run en Sigrid», «lo manuscrito»,
  «firmado no es conforme» y «número de estado». F-036 no procesa partes ni
  escribe en Sigrid. Está justificado en la review 1, y T37–T38 bis no cambian
  nada de eso.
- [x] Reprocesar no duplica: no se tocan la bandeja ni la huella.
- [x] Ningún parte, PDF ni `.xlsx` en git. `git log --diff-filter=A
  a80b8e2..HEAD` solo trae el script y los dos `.md`; los libros de prueba se
  construyen en memoria.

#### C3 bis — Documentos que entran de fuera

- N/A · Nada nuevo en `docs/referencia/`. El barrido de las líneas añadidas
  está en la tabla de verificación: 0 hallazgos reales.

#### C4 — La verificación es real

- [x] **R117 tiene trazabilidad y está en verde:** 31 funciones
  `test_f036_r117_…` (tabla abajo). Por su letra, contar elementos, R117 está
  cumplido. R4-1 cae fuera de esa letra y dentro del riesgo de §0.1.
- [x] Los unit tests no tocan red ni BBDD. Los subprocesos de medida solo leen
  bytes de la entrada estándar.
- [x] Las `MANUAL (humano)` (T16, T27–T29) siguen en `tasks.md` con su
  comando. T29 paso 9 gana el `<xf/>` de estilos y la medida del `v2`. T16
  está además en `current.md`.

#### C4 bis — El rigor declarado se cumple

- [x] `rigor: "critico"`.
- [x] **Fase RED** con salida real, en T37 y en T37 bis:
  - T37 bis: `14 failed, 6 passed`;
  - el `sheet1.dat`, 55,22 s y admitido con el lector de `29e28a6`.
- [x] **Cobertura:** `[OK]` 99,9 % (2913/2916). Las 3 sin cubrir son del
  script y solo corren en su subproceso.
- [x] **Mutación:** existen `mutacion_F-036_bloque10ter.md` y `…quater.md`,
  generados por la herramienta, y sus totales están verificados de forma
  independiente: 159/22 y 37/5.
- [x] **Muertos comprobados:** las campañas pasan de 5 min (5,6 y 24 min) y
  **no se reejecutan**; vale el recálculo puro. Dos muertos muestreados: caen.
- [x] **Coste por mutante:** 335 s y 392 s, coherentes con la suite. Errata
  de workers: R4-3.
- [x] Cero supervivientes sin cerrar. 5 de 5 mutaciones de orden caen, sin
  equivalentes nuevos. O4 y M1a, aceptados por el humano el 2026-09-30.
- [x] «Evidencias» con los cuatro números y los workers.
- [x] Ningún N/A sin justificar en este bloque.

#### C4 ter — Rutas sensibles

- N/A: sigue sin existir `harness/rutas_sensibles.json`.

#### C5 — La sesión se cerró bien

- [x] `tasks.md`: T37 (`6039f0c`, `e62b2d1`), T38 (`a370b1d`), T37 bis
  (`1b9e354`) y T38 bis (`d8572f4`) en `[x]`, con su commit `F-036 Tn:`.
  Siguen `[ ]` T16 y T27–T29, que son MANUAL, y T30, que es el `init.sh`
  final. Es lo esperado.
- [x] Sin ficheros temporales ni sin trackear.
- [x] `features.json`: `in_progress`, sin `blocked_by`.

### Cobertura: requisito → test (solo lo nuevo)

| Req. | Test (uno representativo, en `test_f036_excel_lector.py`) | nº |
|---|---|---|
| R117 · los siete de la review 3 | `test_f036_r117_los_ficheros_de_la_review_3_se_rechazan_en_menos_de_un_segundo`, `…_con_la_memoria_acotada` | 14 casos |
| R117 · corte, frontera y total global | `…_el_recuento_se_corta_al_pasar_el_presupuesto`, `…_justo_el_presupuesto_se_admite_y_uno_mas_no`, `…_el_total_es_de_todas_las_partes_juntas` | 3 |
| R117 · lo que no se analiza | `…_una_parte_que_no_se_analiza_es_no_es_xlsx_sin_abrir`, `…_dtd_o_entidad_en_cualquier_parte_…` | 10 casos |
| R117 bis · todas las partes | `…_la_hoja_en_un_dat_se_rechaza_en_menos_de_un_segundo`, `…_un_bin_con_xml_…`, `…_una_imagen_real_cuenta_cero_…`, `…_una_parte_que_falla_a_mitad_…`, `…_tras_una_parte_que_no_es_xml_…` | 6 funciones |
| R117 · calibración | `…_la_plantilla_completa_cabe_de_sobra_y_se_lee`, `…_r66_el_excel_de_errores_mas_grande_cabe_en_el_presupuesto`, `…_el_peor_caso_admitido_en_incidencias_se_lee` | 3 |
| R117 · orden | `…_el_recuento_va_antes_de_abrir_el_libro`, `…_el_tamano_y_el_zip_se_miran_antes_de_contar` | 8 casos |
| R117 · script de T29 | `…_el_script_cuenta_igual_que_la_funcion_y_no_imprime_contenido` y 4 más | 5 |

El resto de las tablas de las reviews 1 a 3 sigue vigente.

### Cambios requeridos

1. **R4-1 · [Bloquea el despliegue, salvo que el humano acepte por escrito el
   riesgo] El presupuesto no ve los atributos que `openpyxl` convierte en una
   lista de rangos.**
   - **Dónde:** `services/postventa-api/infrastructure/documentos/excel_openpyxl.py`,
     en `_contar_elementos_xml` (~línea 506) y su manejador `al_abrir`
     (~línea 526), que hoy ignora `_atributos`.
   - **Qué pasa:** ver «R4-1» arriba. Un solo `<dataValidation>`,
     `<conditionalFormatting>` o `<scenario>` cuenta uno, y se convierte en
     tantos `CellRange` como rangos lleve su `sqref`, en cada recorrido entero
     de la hoja. Estimación: del orden de 100 s y 1,6 GB dentro de los 20 MiB
     y los 2 MiB.
   - **Qué hacer:** primero, una enmienda del spec-author a R117 y §5.2: un
     elemento no es la unidad de coste cuando un atributo es una lista.
     Propuesta, que cierra la clase sin depender del nombre del atributo,
     igual que R117 no depende del de la etiqueta:
     - en el mismo manejador, sumar al presupuesto también las **palabras de
       cada valor de atributo** (lo separado por blancos);
     - **o** un segundo presupuesto de bytes de atributo.

     Lo decide el spec-author, con estas condiciones:
     - recalibrar con la plantilla completa y con el Excel de errores más
       grande, VML incluido;
     - el corte, al pasar el presupuesto;
     - el coste del recuento sigue proporcional al presupuesto, porque *expat*
       ya entrega los atributos analizados.
   - **Tests** `test_f036_r117_…`, con libros en memoria:
     - un `<dataValidation>`, un `<conditionalFormatting>` y un `<scenario>`
       en «Incidencias», cada uno con un `sqref` de muchos rangos hasta el
       tope de 20 MiB: `fichero_sospechoso` en < 1 s, con la memoria acotada y
       sin llamar a `load_workbook`;
     - la plantilla completa y el Excel de errores más grande, admitidos con
       su cuenta nueva;
     - la frontera exacta con la unidad nueva.
   - **Proceso:**
     - fase RED con la medida real de extremo a extremo del lector de HEAD,
       que confirme o corrija mi estimación;
     - campaña de mutación sobre lo que cambie;
     - en la review, quitar la suma de atributos tiene que poner la suite en
       rojo.
   - **Alternativa del humano:** aceptar por escrito en `current.md` el riesgo
     residual, con esta estimación delante:
     - del orden de 100 s y 1,6 GB por petición en el peor caso;
     - solo con un fichero fabricado a mano;
     - lo sube un usuario autenticado de Posventa;
     - en la Function compartida con el circuito de partes.

     Con esa aceptación, el trabajo de agente de T37–T38 bis estaría listo
     para T27.
   - **Ciclo:** es la cuarta review, dentro del tercer ciclo autorizado. Si se
     abre un cuarto ciclo o se acepta el riesgo, lo decide el humano.
2. **R4-2 · [Documental; va con R4-1, o sola si se acepta el riesgo] §5.2
   «Todas las partes», «Coste del peor caso admitido».**
   - Dice «12–15 s». Lo medido en T37 bis es **de 3,6 a 23,4 s y hasta
     389 MB**, con `<dataValidation/>` como peor tipo.
   - Hay que poner la tabla medida y los límites con los que se compara: el
     front a 40 s, el proxy a 45 s, 2 GB por instancia y una petición por
     instancia en Python.
   - Hay que decir que se midió en la máquina de desarrollo.
3. **R4-3 · [Errata menor; no bloquea] Workers de T38 bis.**
   `progress/mutacion_F-036_bloque10quater.md` dice `--workers 5` y
   «Workers 5», y `impl_F-036.md` («Mutación (T38 bis)», «Evidencias») y
   `tasks.md` dicen 6. Basta con corregir el informe del implementer; el de la
   herramienta no se edita a mano.

### Lo que no he hecho, dicho

- **No he reconstruido aparte** los siete ficheros de la review 3 ni el
  `sheet1.dat`, y **no he construido ningún fichero nuevo** para explorar
  otras vías (tipos de contenido, partes anidadas, compresión, nombres raros)
  ni para medir R4-1 de extremo a extremo.
  - R3-1 lo doy por resuelto por los tests del repositorio que lo fijan:
    pasan en HEAD y caen todos con OA y OD.
  - Las otras vías, por lectura del código:
    - **nombres, extensiones, partes anidadas y tipos de contenido:** el
      recuento ya no filtra por nombre ni por extensión, y OE lo fija;
    - **compresión:** la acotan los topes de 2 MiB y de 20 MiB, que van antes.
  - R4-1 sale de esa misma lectura.
- Si el humano o el líder quieren esa exploración con ficheros fabricados,
  que la haga la fase RED del arreglo de R4-1 o una sesión aparte.

### Qué debe mirar el humano

- **Antes de T27:** decidir R4-1: un cuarto ciclo (enmienda e implementación)
  o la aceptación escrita del riesgo. R4-2 va con cualquiera de las dos.
- **T16** (Docker, `powershell -ExecutionPolicy Bypass -File
  infra\pruebas_bbdd_efimera.ps1`): lo de la review 2, sin cambios.
  - Sobre todo `test_f036_b2_14_el_par_sigue_el_orden_de_python`: el `CHECK`
    con `COLLATE "C"` no se puede cambiar una vez aplicado.
  - El índice único parcial con dos importaciones simultáneas.
  - El DDL aplicado dos veces sin nada en `public`.
- **T27** (desplegar):
  - que las migraciones se aplican solo en el schema `postventa` del servidor
    compartido, y que `/api/health` responde;
  - en `oficios.html`, anotar solo cuántas propuestas se confirman o
    rechazan.
- **T28:**
  - `git diff progress/migracion_F-036.md` sin ningún código de proveedor
    (regenerado aquí: idéntico);
  - en Excel real, «borrar fila» y «ordenar» con la columna `Errores`
    bloqueada;
  - `git status` sin ningún `.xlsx`.
- **T29:**
  - **Pasos 1 y 8:** los recuentos idénticos. Es la prueba desplegada de «no
    se escribe en Sigrid».
  - **Paso 2:** las dos lecturas de Sigrid tal cual contra el ERP (el
    `LEFT JOIN` y el `obride` como texto), que nunca se han ejecutado así.
  - **Paso 9:**
    - la celda con formato en la fila 1.048.576 responde como el paso 4;
    - la copia del `v2` con `A1003:A1048576` combinadas responde al momento y
      se lee normal;
    - el fichero de los 4,1 millones de `<xf/>` da `fichero_sospechoso` al
      momento;
    - **el `v2` guardado desde Excel**, medido con
      `.venv\Scripts\python.exe scripts\contar_elementos_xml_f036.py "<ruta del v2>"`
      desde `services/postventa-api`, queda por debajo de 60.000. El original
      guardado con Excel da 1.680. Si R4-1 cambia la unidad del recuento,
      cambian la cifra y el umbral.
  - Anotar tiempos, sin nombres. Nunca un minuto de espera ni un 5xx.

### Automejora (propuesta, no aplicada)

- **`.claude/agents/reviewer.md`**, completando la propuesta de la review 3
  sobre lectores de ficheros subidos. Vale para `arnes-base`.
  - **Qué añadir:** además de lo que la biblioteca **expande** y de lo que
    **analiza elemento a elemento**, mirar qué **atributos** convierte en
    colecciones: listas de rangos, de referencias, de números. En `openpyxl`,
    buscar `Convertible(expected_type=MultiCellRange)` y similares.
  - **Por qué:** un presupuesto por elementos no acota el coste de un
    elemento con un atributo-lista. La review 3 dio por cerrada «la clase
    entera» con ese presupuesto, y no lo estaba.

## Review 5 (reviewer, 2026-10-01)

- **Veredicto:** APPROVED
- **Rama:** `feature/F-036-importar-excel`, HEAD `6b7d598`. Revisado
  `git diff 3a01a24..HEAD`: 21 ficheros. En producción cambian
  `infrastructure/documentos/ejecutor_aislado.py` (nuevo),
  `infrastructure/documentos/lector_aislado.py` (nuevo),
  `infrastructure/documentos/excel_openpyxl.py`, `interface_adapters/api/importar.py`,
  `function_app.py` y `domain/models/errores.py`. En `azure-apps`, el commit
  local `8f3be7f` (solo `postventa_incidencias.md`, sin push).
- **Nivel de rigor:** `critico`, declarado. Puertas: fase RED, cobertura de las
  líneas cambiadas ≥ 80 %, mutación con cero supervivientes sin justificación
  aceptada por el humano, mutaciones de orden a mano (punto 7) y `MANUAL
  (humano)` con su comando.
- **Alcance:** R4-1 cerrado por R118 (octava enmienda y bis: R118–R120, §5.2
  «La lectura aislada», D-30, D-31, H-T40-1); huecos del propio aislamiento;
  memoria del padre (tope fijo de 102 MiB) y de la instancia; nada roto de lo
  aprobado; mutaciones de orden; la suite del `api` entera aparte.

### Resumen para el líder

**R4-1 queda cerrado por R118, y el aislamiento aguanta lo que le he echado.**

- Los tres ficheros de R4-1 y otros dos míos (las validaciones de R4-1
  repartidas en 400 elementos, y una «bomba de resultado»: un texto compartido de
  32.767 caracteres en las 8.000 celdas de datos) son **400
  `fichero_sospechoso`**, nunca 5xx, ni colgados:
  - en **Linux** (`forkserver`, con los topes de producción): por tiempo a los
    30,0 s, o por memoria a los 4,2–4,4 s, con `tope_memoria_aplicado=True`;
  - en **Windows** (`spawn`, sin tope de memoria): por tiempo a los 30,0 s, o por
    resultado de más (`demasiado_grande`).
- **El padre no abre el libro.** `load_workbook` revienta en el padre durante
  todas mis pasadas, y aun así lo legítimo se lee. Su pico de `tracemalloc` es
  de **80,8 MiB** con R4-1 (por debajo de los 102 MiB) y de 0,5–0,8 MiB con el
  resto de hostiles.
- **El hijo se recoge siempre**: tras cada lectura no queda ningún hijo vivo ni
  ningún zombi, incluido un hijo que ignora `SIGTERM` (`kill` a los 2,0 s).
- **Diez mutaciones de orden caen todas**, cada una por tests de esta feature
  (abajo).
- **La suite del `api`, aparte: 6325 passed, 72 skipped.** El informe de
  migración regenerado es idéntico y el formato antiguo real se reconoce también
  por el lector aislado.

**Lo que queda, medido y acotado, para que el humano lo acepte** (no bloquea):

- R5-1, el hijo huérfano si muere el padre;
- R5-2, el coste en el padre de un JSON hostil, que solo se alcanza si el hijo
  está comprometido;
- R5-4, los textos mucho más largos que la plantilla, que dan
  `fichero_sospechoso` en vez de errores por fila.

**Antes del merge** conviene arreglar un test sensible a la carga (R5-3) y las
erratas que arrastra la review 4 (R5-5).

**Listo para T27** y para las verificaciones manuales, con lo que hay que
mirar en T29 8 bis (abajo). Lo más importante: que el tope de memoria se
aplica en Azure y que la concurrencia por instancia es 1.

### Verificación ejecutada por el reviewer

| Qué | Resultado |
|---|---|
| `bash harness/init.sh` (tal cual) | **ENTORNO LISTO**. Raíz: 62 passed. `api` y `front` salieron de la caché. `PUERTA COBERTURA: 99.9% de 3180 líneas cambiadas cubiertas (3176/3180, umbral 80%, nivel critico)`. ruff: 71 avisos (deuda). F-035 `blocked`, ajena a esta rama |
| Suite del `api` aparte (`.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider` en `services/postventa-api`) | **6325 passed, 72 skipped** en 596,4 s, rc 0, con la máquina cargada por la campaña de otro agente. Una primera pasada con `-x` también salió en verde (rc 0) |
| Copia desechable de `git archive HEAD`, solo con los tests de la feature (`test_f036_lector_aislado.py`, `test_f036_arquitectura.py` y `test_f036_importar_http.py`) | **1 failed, 241 passed, 5 skipped**, con dos suites corriendo a la vez. Cayó `…_los_hostiles_de_todas_las_reviews_…[review-3-comentario-sobre-rango]`: un fichero que se lee en ~1 s rozó el tope inyectado de 3 s, que incluye el `spawn`. Solo: **1 passed**. Ver R5-3 |
| Lector aislado con los **topes de producción**, en **Linux** (contenedor `python` 3.12.14, `--network none --memory 2g --cpus 2`, `forkserver`; código de HEAD y solo `openpyxl`, `et_xmlfile` y `defusedxml` copiados dentro). 34 ficheros: los de las reviews 1–4 y T37-1, los dos legítimos más grandes y los míos | Todos los legítimos y los de las reviews 1–2: **leídos**, `estado=ok`, `tope_memoria_aplicado=True`, 0,2–0,6 s en el hijo. La plantilla completa y el Excel de errores más grande: 1000 filas, padre a 17,3 y 17,6 MiB. Review 3 y `.dat`: `fichero_sospechoso` en el padre, 1,2–2,2 s con `tracemalloc` puesto. **R4-1 (×3): `fichero_sospechoso`, `estado=tiempo` a los 30,03 s**, padre a 80,8 MiB. **Validaciones repartidas: `tiempo`, 30,03 s**, padre a 0,6 MiB. **Bomba de resultado ASCII y con «€»: `estado=memoria` a los 4,4 y 4,2 s**. Textos de 1.300 caracteres en las 8 columnas de 1000 filas: **`demasiado_grande`** a los 1,4 s (R5-4). Ningún hijo vivo tras ninguna lectura |
| Lo mismo en **Windows** (`spawn`, sin tope de memoria; aviso único «sin tope de memoria en esta plataforma») | Legítimos: leídos, 1,3–1,8 s en el hijo. Validaciones repartidas: `tiempo`, 30,02 s. Bomba ASCII y textos largos: `demasiado_grande` (7,1 y 1,5 s). `.dat` y fila 1.048.576: igual que en Linux. Ningún hijo vivo. En estos dos casos, el hijo deja en la salida de errores la cabecera `Process SpawnProcess-N:`, sin contenido: lo matan mientras escribe la traza (R5-7) |
| Matar al hijo y recogerlo, en Linux (`hijos_f036`, tope de 1 s y de 256 MiB) | Ignora `SIGTERM` → `tiempo` en 2,01 s; no acaba → `tiempo` en 1,00 s; `MemoryError` → `memoria`; muere → `murio`; eco → `ok`. **0 zombis y 0 hijos vivos** tras cada uno |
| **Padre muerto a mitad de una lectura** (`kill -9` al padre con un hijo de R4-1 corriendo, Linux) | El hijo **sigue vivo** (estado R) bajo el servidor de *fork* a los +22 s, y ya no está a los +82 s (R5-1) |
| **Basura del hijo en el padre** (`libro_desde_json` con 11 MiB hostiles, con `tracemalloc`) | Siempre `fichero_sospechoso`. Anidado sin fin: 0,03 s; entero de 11 M dígitos: 0,2 s; `Infinity`/`NaN`: 0 s. Pero 11 MiB de `{}`: **6,7 s y 275 MiB**; de `[]`: 8,0 s y 246 MiB; cadenas cortas: 4,5 s y 124 MiB (R5-2) |
| El padre y `openpyxl` | En producción solo hay dos `load_workbook`: `excel_openpyxl._abrir`, que corre en el hijo, y el script de migración, que es local. `lector_aislado.py` y `ejecutor_aislado.py` no lo importan: lo fijan el test de `ast` y el del intérprete limpio. **Precisión:** el proceso de la Function **sí** carga `openpyxl`, porque `importar.py` compone el generador del Excel de errores, que escribe y no lee. Lo que R118 garantiza, y está probado, es que **la lectura** no lo llama: con `load_workbook` reventando en el padre, todo lo de arriba se lee igual |
| Mutación T43: recálculo puro | **Cuadra** (abajo) |
| Mutaciones de orden (punto 7), propias | **10 de 10 caen** (abajo) |
| Muertos muestreados y supervivientes cerrados | 2 de 2 muertos caen; los 4 supervivientes caen con sus tests nuevos (abajo) |
| Migración | `scripts/migrar_excel_f036.py … --solo-informe`, al scratchpad: rc 0, «Ida y vuelta por el importador: 0 errores», `sha256` del original igual antes y después, informe **idéntico** al versionado salvo la línea 1 (sin códigos de proveedor, igual que en la review 4) |
| Formato antiguo real (el original de OneDrive, solo leído) | Por `LectorPlantillaAislado` con el hijo de verdad: `parece_formato_antiguo=True`, 0 filas, **el mismo `LibroLeido`** que el lector en proceso |
| `azure-apps` | Commit local `8f3be7f`, solo `postventa_incidencias.md`: cabecera, recuadro de la revisión, cuatro filas de §6 y la de §8, iguales al origen. Árbol de `azure-apps` limpio. Sin push |
| Barrido de datos sensibles | 4.407 líneas añadidas en `3a01a24..HEAD`, con los patrones de la review 1: GUID, correo, IP privada, `password`, `passwd`, `secret`, `api_key`, `apikey`, `AccountKey`, `SharedAccess`, `Bearer`, claves PEM y `token`. **49 coincidencias, todas falsos positivos**: `@pytest`, `@functools`, `10.514.422` leído como IP y `test_f005_…_sin_secretos`. **0 hallazgos reales** |
| `print` | Solo en el código que dos tests lanzan en un subproceso. Ninguno de depuración |
| Árbol de trabajo | `git status --porcelain` vacío antes de escribir este informe. Copias, ficheros fabricados y guiones, todo en el scratchpad de la sesión; los contenedores, con `--rm` |

#### Mutación (T43): recálculo independiente

- **Alcance y mutantes.** Lo recalculé con `harness.alcance` (`parsear_diff` y
  `filtrar_produccion` sobre `git diff -U0 b8c51e1 <ref>`) y con
  `harness.mutacion.generar_mutantes`. Con `<ref>` = `f356b91`, que es sobre lo
  que corrió la campaña, y con HEAD sale **893 líneas y 96 mutantes, igual que
  el informe**:

  | Fichero | Mutantes |
  |---|---:|
  | `errores.py` | 0 |
  | `function_app.py` | 1 |
  | `ejecutor_aislado.py` | 21 |
  | `excel_openpyxl.py` | 2 |
  | `lector_aislado.py` | 72 |
  | `importar.py` | 0 |

  Por operador: 29 `entero`, 18 `comparacion`, 15 `aritmetico`, 14 `booleano`,
  14 `logico` y 6 `not`. Entre `f356b91` y HEAD la producción no cambia: solo
  los tests.
- **Los 4 supervivientes existen** con el mismo operador y el mismo texto
  original→mutado: `:281` (`ensure_ascii`), `:354` (`-`→`+` y `+ 1`→`+ 2`) y
  `:451` (`_AVISO_DADO`).
- **Campaña no reejecutada.** Según su informe tardó 5855,5 s (97,6 min), así
  que vale el recálculo puro.
- **Coste por mutante:** 5855,5 × 6 ÷ 96 = **366 s**, coherente con una suite de
  344–596 s.
- **Comprobado aplicando el mutante de la herramienta** (`aplicar_mutante`) en
  una copia de HEAD:
  - muertos muestreados: `ejecutor_aislado.py:146` `==`→`!=` **cae** (2 failed:
    `…_hijo_que_muere_es_murio` y `…_memory_error_es_memoria`);
    `excel_openpyxl.py:430` `or`→`and` **cae** (2 failed:
    `…_memory_error_tapado_por_openpyxl_sigue_siendo_memoria[_abrir|_extraer]`);
  - los 4 supervivientes **caen** con sus tests nuevos:
    `…_json_del_hijo_lleva_el_texto_en_utf_8_sin_escapar`,
    `…_mas_de_1001_filas_se_rechazan_sin_mirar_ninguna` (los dos de `:354`) y
    `…_el_primer_lector_sin_tope_del_proceso_avisa`.
- **0 supervivientes sin cerrar y 0 equivalentes.** No hay nada que pedir al
  humano en C4 bis.

#### Orden (punto 7): las mutaciones, propias

En copias desechables de `git archive HEAD`, sin bytecode y sin `-x`, pasando
solo los tests de esta feature: `test_f036_lector_aislado.py`,
`test_f036_arquitectura.py` y `test_f036_importar_http.py`. He mirado el nombre
de cada test que cae, para no contar como muerte un fallo de tiempo.

| Mutación | Qué hace | Resultado |
|---|---|---|
| R5-O1 | el recuento de R117, **después** del hijo | **Cae**: 11 failed (los 8 hostiles que paran en el padre llegan al ejecutor, y el del orden) |
| R5-O2 | `_inspeccionar_zip`, después del hijo | **Cae**: 4 failed (`…_pasos_baratos_rechazan_sin_llamar_al_ejecutor[macros|501-entradas|bomba]`, `…_el_orden_es_tamano_zip_recuento_y_luego_el_hijo`) |
| R5-O3 | `_comprobar_tamano`, después del hijo | **Cae**: 1 failed (`…[mas-de-2-mib]`) |
| R5-O4 | la comprobación de R119 (sin tope en `dev`/`pro`), después del hijo | **Cae**: 2 failed (`…_en_dev_o_pro_sin_tope_de_memoria_es_503_sin_leer[dev|pro]`) |
| R5-O5 | el semáforo se suelta **antes** del hijo | **Cae**: 2 failed (`…_el_semaforo_se_toma_mientras_corre_el_hijo`, `…_dos_hilos_a_la_vez_uno_lee_y_el_otro_es_503`) |
| R5-O6 | el padre lee con `excel_openpyxl._leer_libro` antes del hijo, importado con `importlib` para esquivar el control de `ast` | **Cae**: 9 failed (los 5 que se leen igual y los 3 de R4-1: el padre abre el libro, y `load_workbook` revienta) |
| R5-O7 | `importar.py` compone el lector **en proceso**, también por `importlib` | **Cae**: 2 failed (`…_sin_lector_inyectado_se_compone_el_aislado_con_el_entorno`, `…_ya_no_compone_el_lector_en_proceso`) |
| R5-O8 | en el hijo, `setrlimit` **después** de leer | **Cae**: 2 failed (`…_el_hijo_aplica_el_tope_antes_de_leer_…`, `…_el_hijo_sin_memoria_sale_con_su_codigo`) |
| R5-O9 | el hijo que acabó bien **no se recoge** (sin `_acabar` en `ok`) | **Cae**: 2 failed (`…_ejecutor_real_ok_devuelve_el_cuerpo`, `…_al_acabar_se_espera_al_hijo_solo_si_fue_bien[ok-…]`) |
| R5-O10 | el resultado se lee **sin tope** de tamaño | **Cae**: 2 failed (`…_resultado_de_mas_es_demasiado_grande`, `…_la_bandera_del_hijo_se_lee_con_tope_de_un_byte`) |

Son las del implementer (9 de 9) con otras formas, y además tres que él no
hizo: R119 delante del hijo, el semáforo y el tope de memoria antes de leer. En
todas cae un test de esta feature. Ningún equivalente.

#### Los huecos del propio aislamiento, uno a uno

- **El canal.**
  - El padre lee la bandera con un tope de un byte y el cuerpo con 11 MiB
    (`recv_bytes(maxlength)`). Lo que pasa de eso ni se lee: es
    `demasiado_grande`, tanto en Linux como en Windows.
  - EOF o un hijo muerto dan `murio`, o `memoria` si sale con el código 77.
  - Un hijo que no es hostil no puede mandar otra cosa que la forma fija de
    `libro_a_json`/`error_a_json`. Aun así, el padre valida campo a campo y lo
    que no cuadra es `fichero_sospechoso` (ver la tabla de basura).
  - Hueco teórico, R5-2: una vez llega la cabecera del mensaje, `recv_bytes` ya
    no mira el reloj, así que un hijo **comprometido** que la mandase y se
    parase dejaría esperando al padre. Un hijo sano no lo hace, porque
    construye el JSON entero antes de enviarlo.
- **Huérfanos y zombis.**
  - Zombis: ninguno. Hay `join()` siempre, y en Linux el hijo lo recoge el servidor de
    *fork*.
  - Huérfanos: solo si **muere el padre**, R5-1.
- **El semáforo y la concurrencia.**
  - Hay una lectura aislada por proceso (R5-O5 lo fija).
  - El recuento de R117 corre **fuera** del semáforo. Con concurrencia 1 por
    instancia no importa. Con más, varios recuentos de hasta ~100 MiB pueden
    coincidir con un hijo de 1 GiB. INTEGRACION §6 ya dice que no se suba la
    concurrencia sin rehacer las cuentas; T29 tiene que comprobar que es 1.
- **`forkserver` en Linux.** Arranca en el contenedor, aplica el tope
  (`tope_memoria_aplicado=True` en todas las lecturas), y cada hijo cuesta
  0,03–0,04 s con los hijos de prueba. Que arranque igual en Flex Consumption
  solo se ve en T29.
  - Si la precarga fallase, `forkserver` lo ignora en silencio, y cada hijo
    importaría `openpyxl` por su cuenta: más lento, pero correcto.
  - Si `setrlimit` fallase en Azure, el hijo moriría antes de leer y **toda**
    importación sería `fichero_sospechoso` con `estado=murio`. Hay que mirarlo
    en T29.
- **Degradación en Windows.**
  - Con `ENTORNO=local`/`test` se lee con el tope de reloj y avisa una vez.
  - Con `dev`/`pro`, 503 sin leer (R5-O4 lo fija).
  - `.env.example` y `local.settings.json.example` traen `ENTORNO=local`, y el
    despliegue pone `dev`.
- **Memoria (D-31).**
  - Padre: un pico de 80,8 MiB en el recuento, antes del hijo, y 17,3–17,6 MiB
    con lo legítimo más grande.
  - Hijo: 1 GiB de espacio de direcciones como máximo. Las bombas de resultado
    lo alcanzan y salen como `memoria`.
  - Con una lectura a la vez y concurrencia 1, la cuenta de §5.2 (~1,3–1,6 GB
    de 2.048 MB) es coherente. Faltan las dos cifras que §5.2 deja para T29: el
    *worker* y el *host* en reposo.
- **Tiempo.** El peor caso son 30 s del hijo, más hasta 2 s para matarlo, más el
  recuento (< 1 s), más 5 s si espera al semáforo: por debajo de los 40 s del
  front.

### Checkpoints

#### C1 — El arnés está completo y en verde

- [x] `bash harness/init.sh`: ENTORNO LISTO. La suite del `api`, aparte:
  6325 passed, 72 skipped.
- [x] Existen los ficheros del arnés (init.sh los comprueba).

#### C2 — El estado es coherente

- [x] Una sola `in_progress`, F-036. `blocked`: F-035, ajena a esta rama.
- [x] Rama `feature/F-036-importar-excel`.
- [x] `progress/current.md` empieza por el bloque vivo de T42–T44. El bloque de
  la decisión del líder sobre H-T40-1 desapareció en `6b7d598` (R5-6, menor):
  la decisión sigue escrita en la línea viva, en `design.md` §5.2 (octava
  enmienda bis) y en el historial.
- [x] Toda `done` tiene su entrada en `history.md` (F-036 no lo es).

#### C3 — Arquitectura y convenciones

- [x] **Hexagonal:**
  - los dos módulos nuevos están en `infrastructure/documentos/`;
  - los errores nuevos, en el dominio, sin infraestructura;
  - `importar.py` (interfaz) compone el adaptador, y el puerto
    `LectorPlantillaPort` no cambia;
  - los dos módulos están en `NUEVOS_DE_F036` (R46).
- [x] **Primera línea con la ruta** en los cinco ficheros nuevos: los dos
  módulos, los dos de tests y el informe de mutación.
- [x] Sin `print()` de depuración, TODOs ni secretos. Sin dependencias nuevas:
  `multiprocessing` es de la biblioteca estándar.
- N/A · «unidad de trabajo es el parte», «dry-run en Sigrid», «lo manuscrito»,
  «firmado no es conforme» y «número de estado». F-036 no procesa partes ni
  escribe en Sigrid. Está justificado en la review 1, y T39–T44 no tocan nada
  de eso.
- [x] Reprocesar no duplica: no se tocan la huella ni la bandeja.
- [x] Ningún parte, PDF ni `.xlsx` en git. `git log --diff-filter=A
  3a01a24..HEAD` solo trae `.py` y un `.md`. Los ficheros fabricados de esta
  review viven en el scratchpad.

#### C3 bis — Documentos que entran de fuera

- N/A · Nada nuevo en `docs/referencia/`. El barrido de las líneas añadidas
  está en la tabla: 0 hallazgos reales.

#### C4 — La verificación es real

- [x] **Trazabilidad**, todo en verde: R118 con 63 funciones
  `test_f036_r118_…`, R119 con 12, R120 con 7 y R16 (tope nuevo) con 15. El
  test de Linux de R119 se salta en Windows; lo he comprobado en el contenedor
  (`memoria` con el tope puesto).
- [x] Los unit tests no tocan red ni BBDD. Los hijos de verdad solo usan IPC
  local (`AF_UNIX` en Linux, por el *fixture* `ipc_local_permitido`).
- [x] Las `MANUAL (humano)` siguen en `tasks.md` con su comando: T16 y T27–T29,
  y T29 gana el paso 8 bis. T16 está además en `current.md`.

#### C4 bis — El rigor declarado se cumple

- [x] `rigor: "critico"`.
- [x] **Fase RED** con salida real:
  - T39: R4-1, 108–109 s, admitido y 1,6 GB con el lector de HEAD; tests en
    rojo por `ImportError`;
  - T40: `ImportError: cannot import name 'LecturaOcupada'`;
  - T41: `assert 20971520 == 17825792` y el `MemoryError` tapado
    (`2 failed`);
  - T42: cuatro roturas a mano en una copia, `8 failed` cada una;
  - T44: `4 failed, 3 errors`.
- [x] **Cobertura:** `[OK]` 99,9 % (3176/3180).
- [x] **Mutación:** existe `mutacion_F-036_bloque10quinquies.md`, generado por
  la herramienta, y sus totales están verificados de forma independiente:
  893 líneas y 96 mutantes.
- [x] **Muertos comprobados:** la campaña pasa de 5 min (97,6 min) y **no se
  reejecuta**; vale el recálculo puro. Dos muertos muestreados: caen.
- [x] **Coste por mutante:** 366 s, coherente con la suite.
- [x] Cero supervivientes sin cerrar: los 4 caen con sus tests. 10 de 10
  mutaciones de orden propias caen, sin equivalentes nuevos.
- [x] «Evidencias» con los cuatro números y los workers (6, igual que el
  informe de la herramienta).
- [x] Ningún N/A sin justificar en este bloque.

#### C4 ter — Rutas sensibles

- N/A: sigue sin existir `harness/rutas_sensibles.json`.

#### C5 — La sesión se cerró bien

- [x] `tasks.md`: de T39 a T44 en `[x]`, con sus commits `F-036 Tn:` (nueve).
  Siguen `[ ]` T16 y T27–T29, que son MANUAL, y T30, el `init.sh` final. Es lo
  esperado.
- [x] Sin ficheros temporales ni sin trackear.
- [x] `features.json`: `in_progress`, sin `blocked_by`.

### Cobertura: requisito → test (solo lo nuevo)

| Req. | Test (uno representativo, en `test_f036_lector_aislado.py`) | nº |
|---|---|---|
| R118 · hostiles de todas las reviews | `…_los_hostiles_de_todas_las_reviews_a_tiempo_y_con_el_padre_acotado` (16 casos), `…_los_de_r4_1_con_los_topes_de_produccion` (3, lentos) | 19 |
| R118 · cada salida del hijo (doble) | `…_cada_salida_mala_del_hijo_es_fichero_sospechoso`, `…_esquema_malo_es_fichero_sospechoso`, `…_json_roto_o_que_no_es_un_libro_es_fichero_sospechoso` | varios |
| R118 · lo legítimo entra | `…_los_legitimos_mas_grandes_se_admiten_por_el_hijo_real` | 2 |
| R118 · el padre no lee | `test_f036_arquitectura_r118_…` (2) y, con `load_workbook` reventando en el padre, `…_el_hijo_real_lee_lo_mismo_que_el_lector_en_proceso` | 3+ |
| R118 · topes (17 MiB, 11 MiB, 102 MiB, 30 s, 1 GiB) | `test_f036_r16_el_tope_descomprimido_es_de_17_mib`, `…_el_tope_del_resultado_es_de_11_mib`, `…_el_tope_del_pico_del_padre_es_de_102_mib`, `…_los_topes_de_produccion_son_30_s_1_gib_y_5_s_de_espera` | 5+ |
| R118 · matar y recoger | `…_al_acabar_terminate_kill_si_sigue_vivo_y_join_siempre` (3), `…_ejecutor_real_un_hijo_que_ignora_terminate_muere_con_kill` (Linux) | 4 |
| R119 | `…_en_dev_o_pro_sin_tope_de_memoria_es_503_sin_leer`, `…_fuera_de_dev_y_pro_sin_tope_lee_y_avisa_una_vez`, `…_en_linux_el_tope_de_memoria_se_aplica_al_hijo` | 12 |
| R120 | `…_dos_hilos_a_la_vez_uno_lee_y_el_otro_es_503`, `…_el_semaforo_se_toma_mientras_corre_el_hijo` | 7 |
| T44 | `test_f036_documentacion.py::test_f036_t44_…` | 7 |

El resto de las tablas de las reviews 1 a 4 sigue vigente.

### Cambios requeridos

Ninguno bloquea el despliegue. Lo que sigue es para el humano, aceptarlo o
encargarlo, o para antes del merge.

1. **R5-1 · [Riesgo residual, para aceptar] El hijo huérfano si muere el
   padre.**
   - **Qué pasa:** el tope de 30 s lo pone el padre (`ejecutor_aislado.py`,
     `_recibir` y `_acabar`). Si el *worker* muere a mitad de una lectura
     (reciclado, despliegue), el hijo sigue bajo el servidor de *fork*. Medido
     con R4-1: vivo a los +22 s y terminado antes de los +82 s.
   - **Por qué no bloquea:** la memoria sigue topada a 1 GiB y el trabajo es
     finito. El tope descomprimido acota lo que cuesta, del orden de 90–110 s
     de CPU con R4-1. Además, que muera el padre en mitad de una lectura es
     raro.
   - **Si se quiere cerrar:** `RLIMIT_CPU` en el hijo, junto al `RLIMIT_AS`
     (p. ej. `SEGUNDOS_HIJO + 5`), con su test de Linux. Va por una enmienda
     menor de R119.
2. **R5-2 · [Riesgo residual, para aceptar] Coste en el padre de un JSON
   hostil.**
   - **Qué pasa:** `libro_desde_json` (`lector_aislado.py`, ~línea 403) hace
     `json.loads` de hasta 11 MiB antes de validar. Con 11 MiB de `{}` medí
     6,7 s y 275 MiB (con `tracemalloc` y la máquina cargada), por encima de
     los 102 MiB del padre.
   - **Por qué no bloquea:** solo lo alcanza un hijo **comprometido**, con
     ejecución de código por un fallo del analizador. Un hijo sano manda la
     forma fija de `libro_a_json`. Pasa lo mismo con el `recv_bytes` que deja de
     mirar el reloj una vez llega la cabecera del mensaje.
   - **Dicho:** el aislamiento es **de recursos, no de seguridad**. El hijo
     hereda el entorno del *worker*, igual que antes, cuando `openpyxl` leía en
     el mismo proceso. No es un riesgo nuevo.
3. **R5-3 · [Antes del merge] Un test que depende de la carga de la
   máquina.**
   - **Dónde:** `tests/test_f036_lector_aislado.py`,
     `test_f036_r118_los_hostiles_de_todas_las_reviews_a_tiempo_y_con_el_padre_acotado`,
     con `SEGUNDOS_INYECTADOS = 3.0` (~línea 196).
   - **Qué pasa:** para los cinco ficheros `SE_LEE_IGUAL`, los 3 s incluyen el
     `spawn` de Windows (0,6–0,8 s en reposo). Con la máquina muy cargada uno
     pasó del tope y cayó (`[review-3-comentario-sobre-rango]`). Además de un
     rojo falso, en una campaña de mutación con 6 workers puede dar muertos
     falsos.
   - **Qué hacer:** para los que deben leerse, un tope inyectado holgado (p. ej.
     30 s, o el de producción), y dejar los 3 s solo para los `EN_EL_HIJO`.
4. **R5-4 · [Riesgo residual, para aceptar] Textos mucho más largos que la
   plantilla.**
   - **Qué pasa:** el JSON lleva cada texto dos veces (`valor` y
     `texto_original`). Un fichero cuyo JSON pase de 11 MiB es entero
     `fichero_sospechoso`, con «no se ha podido leer en el tiempo y la memoria
     que tiene la plantilla», en vez de un error por fila. Por ejemplo, 1.300
     caracteres en las 8 columnas de 1000 filas.
   - **Por qué no bloquea:** es lo que dice R118 («pasa del tamaño acotado»), y
     lo legítimo más grande queda a la mitad del tope. Lo anotó el implementer
     en T41. El humano debe saber que el usuario no verá qué fila sobra.
5. **R5-5 · [Antes del merge; arrastrado de la review 4] Las erratas R4-2 y
   R4-3 siguen sin corregir.**
   - **R4-2:** `design.md` §5.2, «Todas las partes» (~línea 1189), sigue
     diciendo «12–15 s» estimados. La cifra medida de T37 bis (3,6–23,4 s,
     389 MB) solo aparece en «Topes» (~línea 1327). Hay que corregirla en su
     sitio y decir que hoy lo acota el hijo.
   - **R4-3:** `impl_F-036.md`, «Mutación (T38 bis)», dice 6 workers, y el
     informe de la herramienta, 5.
6. **R5-6 · [Menor] `current.md`.**
   - **Qué pasa:** `6b7d598` quitó el bloque «F-036 DESBLOQUEADA · H-T40-1
     decidido por el líder», con su motivo.
   - **Qué hacer:** reponerlo, como se hace con las decisiones del humano. Las
     decisiones no deberían desaparecer del registro vivo.
7. **R5-7 · [Cosmético, solo en local] La traza cortada en Windows.** Con un
   resultado de más, el hijo de `spawn` deja `Process SpawnProcess-N:` en la
   salida de errores, porque lo matan mientras escribe la traza. Sin contenido.
   En Linux no sale.

### Lo que no he hecho, dicho

- **No he reejecutado la campaña de mutación** (97,6 min): recálculo puro y
  muestreo.
- **No he ejecutado en Linux la suite con `pytest`.** En el contenedor no hay
  `pydantic`, y no he instalado nada con red. Las comprobaciones de Linux son
  guiones contra el código de HEAD: el lector aislado con los topes de
  producción y el ejecutor con los hijos de prueba.
- **No he medido nada en Azure:** eso es T29.

### Qué debe mirar el humano

- **T16** (Docker, `powershell -ExecutionPolicy Bypass -File
  infra\pruebas_bbdd_efimera.ps1`): sin cambios desde la review 2.
  - Sobre todo `test_f036_b2_14_el_par_sigue_el_orden_de_python`.
  - El índice único con dos importaciones a la vez.
  - El DDL aplicado dos veces, sin nada en `public`.
- **T27** (desplegar):
  - que las migraciones van solo al schema `postventa`;
  - que `/api/health` responde;
  - que la app tiene `ENTORNO=dev`;
  - la primera importación tras un arranque en frío cuesta ~0,8 s más, por el
    servidor de *fork*.
- **T28:**
  - `git diff progress/migracion_F-036.md` sin ningún código de proveedor
    (aquí, idéntico);
  - en Excel real, «borrar fila» y «ordenar» con `Errores` bloqueada;
  - `git status` sin ningún `.xlsx`.
- **T29**, pasos 1, 2, 8 y 9, como en la review 4. Y el **8 bis**, con esto:
  - **(a) Memoria y concurrencia.**
    - `instanceMemoryMB` = 2048;
    - **además**, `az functionapp show -g rg-postventa-dev -n func-postventa-dev
      --query "functionAppConfig.scaleAndConcurrency"`: la concurrencia HTTP por
      instancia tiene que ser **1**, y `FUNCTIONS_WORKER_PROCESS_COUNT` no puede
      estar puesto, o tiene que valer 1.
    - Toda la cuenta de memoria cuelga de esto (R5, «El semáforo y la
      concurrencia»).
  - **(b) El tope de memoria se aplica.** Tras una importación legítima, en
    Application Insights tiene que salir
    `lector_aislado: estado=ok … tope_memoria_aplicado=True`. **Es la prueba de
    que el tope de memoria se aplica en Azure.** Párese y vuelva al
    spec-author si sale:
    - `tope_memoria_aplicado=False`;
    - un 503 «esta plataforma no permite ponerlo» (`LectorSinAislamiento`);
    - toda importación como `fichero_sospechoso` con `estado=murio`, que sería
      `setrlimit` o `forkserver` fallando.
  - **(c) Un fichero de R4-1.**
    - Se genera fuera del repositorio, desde `services/postventa-api`:
      `.venv\Scripts\python.exe -c "from tests.test_f036_lector_aislado import _de_r4_1; open(r'C:\temp\r4_1.xlsx','wb').write(_de_r4_1('validacion'))"`.
      No se versiona: R59, `.xlsx`.
    - Al subirlo, la respuesta tiene que ser 400 `fichero_sospechoso` en
      **≤ ~32 s**, con `estado=memoria` o `estado=tiempo` en el log, sin 5xx y
      sin ninguna traza con contenido.
    - La petición siguiente tiene que responder sin arranque en frío.
  - **(d)** Anotar la memoria del *worker* y del *host* en reposo, para cerrar
    la cuenta de §5.2 (~1,3–1,6 GB de 2.048).
  - **Paso 9:**
    - el `v2` guardado desde Excel tiene que **leerse** (`estado=ok`), no dar
      `demasiado_grande` (JSON de más de 11 MiB);
    - tiene que quedar por debajo de 17 MiB descomprimidos y de 60.000
      elementos.
- **Decidir R5-1, R5-2 y R5-4:** aceptarlos por escrito o encargar R5-1. R5-3,
  R5-5 y R5-6 van antes del merge, en el mismo encargo que T30 o en uno corto.

### Automejora (propuesta, no aplicada)

- **`.claude/agents/reviewer.md`**, punto 7 (Orden). Vale para `arnes-base`.
  - **Qué añadir:** cuando la feature aísla trabajo en un proceso hijo con topes
    puestos por el padre, el reviewer prueba también **qué pasa si muere el
    padre** a mitad del trabajo (`kill -9`) y si el hijo se autolimita.
  - **Por qué:** los tests y las mutaciones de orden miran el camino en que el
    padre vive. El huérfano de R5-1 solo se vio matando al padre a mano.
- **`CHECKPOINTS.md`, C4 bis**, regla del coste por mutante. Vale para
  `arnes-base`.
  - **Qué añadir:** si la suite tiene tests con topes de reloj pequeños, el
    implementer declara cuántos dependen del tiempo, y la campaña paralela se
    revisa con eso en mente.
  - **Por qué:** con varios workers, un test sensible a la carga puede convertir
    supervivientes en muertos falsos, y el recálculo puro no lo ve (R5-3).

## Review 6 (reviewer, 2026-10-01)

- **Veredicto:** APPROVED
- **Rama:** `feature/F-036-importar-excel`, HEAD `12dbe69`. Review **acotada** a
  `git diff c1ab295..HEAD`: el merge de `dev` (`c58e3b4`), la novena enmienda
  (`e045598`) y el Bloque 11 (T45–T49, `71cbba7`..`12dbe69`). Lo anterior quedó
  aprobado en la review 5 y no se repite.
- **Nivel de rigor:** `critico`, declarado. Puertas: fase RED, cobertura de las
  líneas cambiadas ≥ 80 %, mutación con cero supervivientes sin justificación
  aceptada por el humano, mutaciones de orden a mano (punto 7) y `MANUAL
  (humano)` con su comando.
- **Código de producción que cambia en el Bloque 11:** solo
  `infrastructure/documentos/ejecutor_aislado.py` (48 líneas).

### Resumen para el líder

**Las tres partes están bien y la rama se puede desplegar en T27.**

- **El merge no ha perdido nada.** Lo he rehecho con `git merge-tree`: el
  resultado automático solo difiere de `c58e3b4` en los tres ficheros que tenían
  conflicto. El código de F-051 es idéntico al de `dev`.
- **El tope de CPU hace lo que dice R119**, y lo he reproducido en un contenedor
  Linux sin red: un hijo sin padre muere solo a los 35 s de CPU, y con el padre
  vivo el estado que ve el usuario no cambia.
- **R5-1, R5-3, R5-5 (R4-2 y R4-3) y R5-6 quedan cerrados.**
- **La campaña de T49 es creíble**: la he recalculado y la he reejecutado
  entera, con los mismos totales.
- `bash harness/init.sh` en verde y la suite del `api` aparte: **6417 passed,
  74 skipped**.

Quedan cuatro hallazgos menores (R6-1 a R6-4). Ninguno bloquea. R6-1 y R6-3
conviene cerrarlos antes del merge; R6-2 es una cifra de la spec que mi propia
review 5 estimó mal.

### Respuestas a los puntos del encargo

**1. El merge de `dev` (`c58e3b4`).**

- Padres: `c1ab295` (la rama) y `fcc4810` (`dev`, que hoy sigue ahí).
- `git merge-tree --write-tree c1ab295 fcc4810` da conflicto en `BACKLOG.md`,
  `harness/features.json` y `progress/current.md`, y en nada más. El árbol
  automático y `c58e3b4` solo difieren en esos tres ficheros.
  `docs/INTEGRACION.md` cambió en los dos lados y se fusionó sola, sin conflicto.
- **Lado de `dev`:** de todos los ficheros que `dev` cambió desde la base, solo
  esos cuatro difieren entre `dev` y el merge. `git diff dev HEAD` sale **vacío**
  en `config/settings.py`, `infrastructure/sharepoint/fabrica.py`,
  `interface_adapters/api/archivar.py`, `infra/desplegar_backend.ps1`,
  `infra/00_vars_postventa.ps1`, `infra/verificar_destino_sharepoint.ps1`,
  `.env.example` y `docs/DESPLIEGUE.md`. Los tests y la spec de F-051, igual.
- **Lado de la rama:** el merge no cambia ningún fichero que `dev` no hubiera
  tocado.
- **`features.json`:** 50 entradas (49 en cada lado). No falta ninguna. F-051
  viene de `dev` (`done`); F-036, F-039 y F-050 quedan como en la rama. Una sola
  `in_progress` (F-036); `blocked`, F-035, ajena.
- **`current.md`:** se conservan los dos bloques, el de la rama y el de F-051, y
  encima va el bloque nuevo del líder.
- **`BACKLOG.md`:** `init.sh` dice «al día».
- El arreglo del incidente del 502 llega entero a la rama.

**2. ¿Quedan cerrados R5-1, R5-3, R5-5 y R5-6? ¿R4-2 y R4-3 corregidos donde
tocaba?**

| Hallazgo | Estado | Cómo lo he comprobado |
|---|---|---|
| R5-1 (hijo huérfano) | **Cerrado** | Contenedor Linux: sin padre, el hijo muere solo a los 6 s y a los 35 s de CPU; antes seguía vivo (abajo) |
| R5-3 (test sensible a la carga) | **Cerrado** | Los cinco que deben leerse llevan el tope de producción (30 s) y el test comprueba qué tope recibe el ejecutor. Dos vueltas con la suite del `api` corriendo a la vez: 18 passed las dos (56,0 y 52,5 s) |
| R5-5 · R4-2 | **Corregido en su sitio** | `design.md` §5.2, «Todas las partes»: nota bajo la estimación, con lo medido (3,6–23,4 s, 389 MB) y que hoy lo acota el hijo |
| R5-5 · R4-3 | **Corregido en su sitio** | `impl_F-036.md`, «Mutación (T38 bis)» y su tabla de «Evidencias»: 5 workers, con nota de errata. La orden (`--workers 6`) no se toca |
| R5-6 (bloque de H-T40-1) | **Cerrado** | Las 12 líneas del bloque son idénticas a las de `6b7d598^` (`diff` sin finales de línea), y está en su sitio cronológico |

**3. El `RLIMIT_CPU`.**

- **Se pone antes de leer nada.** En `_principal_hijo` el orden es: tope de
  memoria, tope de CPU, byte del canal, lectura. Mis mutaciones de orden M2, M3
  y M4 caen las tres.
- **Blando y duro son iguales** (`(s, s)`). Con los dos iguales el núcleo mata
  con `SIGKILL`, que el hijo no puede capturar: `exitcode=-9` en el contenedor.
  M5 (duro sin límite) y M6 (blando distinto) caen.
- **No rompe Windows.** Sin `resource` la función vuelve sin hacer nada y el
  byte del canal sigue siendo `0`. M9 (quitar el `except ImportError`) cae con
  7 tests. La suite entera pasa en Windows.
- **Si el sistema no deja fijarlo**, el error no se captura: el hijo muere antes
  del byte y no lee. Lo he provocado en el contenedor (usuario sin privilegios y
  un tope duro heredado de 20 s): `ValueError: not allowed to raise maximum
  limit`, `estado=murio`, `tope_memoria_aplicado=False`, y toda importación es
  400 `fichero_sospechoso`. Falla cerrado, como pide R119. Ver R6-4.
- **No salta antes que el tope de reloj del padre.**
  - El hijo tiene un solo hilo en todas mis muestras (`/proc/<pid>/stat`), así
    que no gasta más CPU que reloj.
  - El contador de CPU empieza en cero en cada hijo: el huérfano de prueba muere
    a los 35 s de CPU, sin arrastrar lo que gastó el servidor de *fork*.
  - Con el padre vivo y los topes de producción, los tres ficheros de R4-1 dan
    `estado=tiempo` a los **30,03 s**, no `murio`. Lo legítimo más grande se lee
    (`estado=ok`, 1000 filas).
  - Aunque saltase antes, el usuario vería lo mismo: `tiempo` y `murio` son los
    dos 400 `fichero_sospechoso`. Solo cambiaría la línea del log.
- **Evidencia de Linux, reproducida por mí.** Docker estaba disponible.
  Contenedor `python` 3.12.14, `--network none --rm --memory 2g --cpus 2`,
  `forkserver`, con el código de `git archive` y las bibliotecas copiadas del
  `.venv`, montado en solo lectura.

  | Qué | Antes (`71cbba7`) | HEAD |
  |---|---|---|
  | Tests `r119` con `pytest --noconftest` | 15 failed, 15 passed | **30 passed** |
  | Huérfano que gasta CPU, 0,5 s de reloj | vivo a los 12 s (11,4 s de CPU) | **muere solo a los 6,59 s**, `exitcode=-9` |
  | Huérfano que gasta CPU, 30 s de reloj | vivo a los 45 s (44,9 s de CPU) | **muere solo a los 35,15 s**, `exitcode=-9` |
  | `kill -9` al padre con R4-1 «formato condicional» | el hijo gasta **60,0 s** de CPU | el hijo gasta **34,9 s** |
  | `kill -9` al padre con R4-1 «validación» | 33,0 s de CPU | 30,6 s |
  | `kill -9` al padre con R4-1 «escenario» | 30,2 s de CPU | 30,2 s |

  Las tres últimas filas son el caso real de R5-1: el lector y el ejecutor de
  verdad, con los topes de producción. Ver R6-2 sobre lo que dicen.

**4. La campaña de T49: 2 mutantes.**

- **El alcance es creíble y la herramienta no deja líneas fuera.** Recalculado
  con `harness.alcance` y `generar_mutantes`: **48 líneas y 2 mutantes**, los
  mismos del informe (`:65` `5 → 6` y `:120` `+ → −`). Las líneas nuevas del
  hijo (142–155, 172 y 251) **están** en el alcance.
- **Por qué solo 2:** los operadores de la herramienta mutan enteros,
  comparaciones, aritmética, booleanos y lógica. Lo nuevo son sobre todo
  llamadas, un `import` y texto. Prueba de control: sobre el fichero entero la
  herramienta saca 23 mutantes, así que el generador funciona.
- **Campaña reejecutada entera** (`--base c58e3b4 --workers 2 --timeout 900`,
  salida en mi scratchpad): **2 mutantes, 2 muertos, 0 supervivientes, 0
  timeouts, 310,5 s**. El informe dice 318,6 s. Coinciden.
- **Coste por mutante:** 318,6 × 2 ÷ 2 = **319 s**. La suite tarda 456–638 s,
  pero la campaña corre con `-x` y para en el primer test que cae, que está en
  `test_f036_lector_aislado.py`. Coherente.
- **Mis mutaciones a mano**, en una copia de `git archive HEAD` (nunca en el
  árbol), con los tests `r119` y `el_hijo_` de `test_f036_lector_aislado.py`.
  Sin mutar: 43 passed, 3 skipped. La copia quedó igual que HEAD.

  | Mutación | Resultado en Windows |
  |---|---|
  | M1 · quitar la llamada al tope de CPU | **cae**, 3 failed |
  | M2 · (orden) el tope de CPU después del byte del canal | **cae**, 2 failed |
  | M3 · (orden) el tope de CPU después de leer | **cae**, 3 failed |
  | M4 · (orden) el tope de CPU antes que el de memoria | **cae**, 2 failed |
  | M5 · duro sin límite | **cae**, 2 failed |
  | M6 · blando un segundo menor que el duro | **cae**, 2 failed |
  | M7 · tragarse el fallo de `setrlimit` | **cae**, 1 failed |
  | M8 · `RLIMIT_AS` en vez de `RLIMIT_CPU` | **cae**, 3 failed |
  | M9 · sin `resource`, reventar (rompe Windows) | **cae**, 7 failed |
  | M10 · el ejecutor pasa los segundos tal cual | **cae**, 2 failed |
  | M11 · el ejecutor cambia de sitio memoria y CPU | **cae**, 2 failed |
  | M12 · el ejecutor calcula siempre con 30 s | **cae**, 1 failed |
  | M13 · `int()` en vez de `math.ceil` | **cae**, 4 failed |
  | M14 · `floor + 1` | **cae**, 7 failed |
  | M15 · devolver un `float` | **cae**, 6 failed |
  | M16 · el tope de CPU solo si pasa de 30 | **sobrevive en Windows**; cae en Linux (R6-1) |
  | M17 · el fallo del tope de CPU manda igual el byte | **cae**, 1 failed |

  **16 de 17 caen en Windows**, todas por tests de esta feature. Las tres de
  orden (punto 7 del protocolo) caen. M16 es R6-1.

**5. El rojo de la fase RED en Linux, por la firma.**

- **Es una RED válida, con el complemento que trae.**
- Los 13 tests que corren en todas las plataformas fallan por lo que deben: la
  constante, la función y el parámetro no existen. Lo he reproducido en
  `71cbba7`: 15 failed, 15 passed.
- Los dos tests reales de Linux fallan ahí por la firma (`TypeError` en el hijo,
  `EOFError` en el test), no por el hueco. El implementer lo dice con claridad y
  añade un guion contra HEAD que enseña el hueco. He escrito el mío y da lo
  mismo: el huérfano sigue vivo a los 45 s.
- **Además, el test del huérfano sí se pone rojo por el hueco** cuando la firma
  existe y el tope no se aplica: con M1 y con M16 en el contenedor, cae
  `…_un_hijo_sin_padre_que_gasta_cpu_muere_solo_por_su_tope`, tras esperar sus
  30 s. Con M16 es el único test que cae.
- El segundo test de Linux («cuenta CPU y no reloj») es una guarda: no tiene un
  rojo propio, y el informe lo dice.

### Verificación ejecutada por el reviewer

| Qué | Resultado |
|---|---|
| `bash harness/init.sh` (tal cual) | **ENTORNO LISTO**. Raíz: 62 passed. `api` y `front`, de la caché (árbol sin cambios desde el último verde). `PUERTA COBERTURA: 99.9% de 3191 líneas cambiadas cubiertas (3187/3191, umbral 80%, nivel critico)`. ruff: 71 avisos, los mismos de la review 5 |
| Suite del `api` aparte (`.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider`) | **6417 passed, 74 skipped** en 456,4 s |
| Merge rehecho con `git merge-tree` | Solo difieren los tres ficheros con conflicto (punto 1) |
| Contenedor Linux sin red | Tabla del punto 3 |
| Mutación: recálculo puro | 48 líneas, 2 mutantes: **cuadra** |
| Mutación: campaña reejecutada | 2 muertos de 2, 310,5 s: **cuadra** |
| Mutaciones a mano | 17, tabla del punto 4 |
| Test de los hostiles con la máquina cargada | 2 vueltas, 18 passed cada una |
| Barrido de datos sensibles | 891 líneas añadidas en `c58e3b4..HEAD`, con los patrones de la review 1. **6 coincidencias, todas falsos positivos** (`@pytest`). 0 hallazgos reales. Lo que entra por el merge es lo que ya está en `dev`, revisado en F-051 |
| `print`, TODO | Ninguno en lo añadido |
| Árbol de trabajo | `git status --porcelain` vacío antes de escribir este informe. Copias, guiones e informe de la campaña, en el scratchpad; contenedores con `--rm` |

### Checkpoints

#### C1 — El arnés está completo y en verde

- [x] `bash harness/init.sh`: exit 0, ENTORNO LISTO. Suite del `api` aparte:
  6417 passed, 74 skipped.
- [x] Existen los ficheros del arnés (los comprueba `init.sh`).

#### C2 — El estado es coherente

- [x] Una sola `in_progress`, F-036. `blocked`: F-035, ajena.
- [x] Rama `feature/F-036-importar-excel`.
- [x] `progress/current.md` empieza por el bloque vivo del Bloque 11, y el de
  H-T40-1 vuelve a estar (R5-6).
- [x] Toda `done` tiene su entrada en `history.md`: F-051 la trae de `dev`.

#### C3 — Arquitectura y convenciones

- [x] **Hexagonal:** el cambio vive en `infrastructure/documentos/`. No cambian
  el puerto, el protocolo `EjecutorAislado`, `SalidaHijo` ni `lector_aislado.py`.
- [x] **Primera línea con la ruta** en los cuatro ficheros de código tocados y
  en el informe de mutación nuevo.
- [x] Sin `print()` de depuración, TODOs ni secretos. Sin dependencias nuevas:
  `math` y `resource` son de la biblioteca estándar.
- N/A · «unidad de trabajo es el parte», «dry-run en Sigrid», «lo manuscrito»,
  «firmado no es conforme» y «número de estado». El Bloque 11 no procesa partes
  ni escribe en Sigrid; justificado en la review 1.
- [x] Reprocesar no duplica: no se tocan la huella ni la bandeja.
- [x] Ningún parte, PDF ni `.xlsx` en git: `git log --diff-filter=A
  c58e3b4..HEAD` solo añade `progress/mutacion_F-036_bloque11.md`.

#### C3 bis — Documentos que entran de fuera

- N/A · Nada nuevo en `docs/referencia/`. El barrido de lo añadido está en la
  tabla: 0 hallazgos reales.

#### C4 — La verificación es real

- [x] **Trazabilidad:** R119 gana 13 tests (`test_f036_r119_…`), dos de ellos
  reales y solo de Linux, en verde en el contenedor. La frase de
  `ARCHITECTURE.md` la fija `test_f036_t45_…`. R5-3 tiene su test.
- [x] Los unit tests no tocan red ni BBDD. Los hijos de verdad usan solo IPC
  local.
- [x] Las `MANUAL (humano)` siguen en `tasks.md` con su comando: T16 y T27–T29.
  T16 está además en `current.md`.

#### C4 bis — El rigor declarado se cumple

- [x] `rigor: "critico"`.
- [x] **Fase RED** con salida real, reproducida (punto 5). T46 trae la suya:
  `assert [3.0] == [30]`, 5 failed.
- [x] **Cobertura:** `[OK]` 99,9 % (3187/3191).
- [x] **Mutación:** existe `mutacion_F-036_bloque11.md`, generado por la
  herramienta, con totales verificados: 48 líneas y 2 mutantes.
- [x] **Muertos comprobados:** el informe declara 318,6 s (5,3 min), así que el
  protocolo no obliga a reejecutar. **La he reejecutado igualmente**, porque con
  dos mutantes costaba poco: mismos totales.
- [x] **Coste por mutante:** 319 s, coherente con una campaña con `-x`.
- [x] Cero supervivientes de la herramienta. De las mutaciones a mano, las tres
  de orden caen. M16 no cae en Windows y sí en Linux: T49 prevé ese caso («si
  alguna solo cae en Linux, decirlo») y queda dicho en R6-1. Ningún equivalente
  que pedir al humano.
- [x] «Evidencias» con los cuatro números y los workers (2).
- [x] Ningún N/A sin justificar en este bloque.

#### C4 ter — Rutas sensibles

- N/A: sigue sin existir `harness/rutas_sensibles.json`.

#### C5 — La sesión se cerró bien

- [x] `tasks.md`: de T45 a T49 en `[x]`, con sus commits `F-036 Tn:` (seis; T45
  lleva dos, la RED y el arreglo). **Siguen sin marcar a propósito** T16 y
  T27–T29, que son MANUAL del humano, y T30, del líder: van después de esta
  review y no son trabajo pendiente del implementer.
- [x] Sin ficheros temporales ni sin trackear. El *worktree*
  `agent-a6e2f9bed1d46cdbc` ya existía y no es de este encargo.
- [x] `features.json`: `in_progress`, sin `blocked_by`.

### Cobertura: requisito → test (solo lo nuevo)

| Req. | Test (en `test_f036_lector_aislado.py`) |
|---|---|
| R119 · el valor: segundos redondeados más 5 | `…_el_margen_del_tope_de_cpu_es_de_5_s`, `…_el_tope_de_cpu_son_los_segundos_del_hijo_redondeados_mas_5` (6 casos) |
| R119 · blando y duro | `…_el_tope_de_cpu_es_rlimit_cpu_blando_y_duro` |
| R119 · antes del byte y de leer | `…_el_hijo_se_pone_los_dos_topes_antes_del_byte_y_antes_de_leer` |
| R119 · si falla, no lee | `…_si_el_tope_de_cpu_falla_el_hijo_muere_sin_mandar_el_byte` |
| R119 · sin `resource` no se aplica | `…_sin_resource_no_se_aplica_ningun_tope_y_el_byte_es_cero` |
| R119 · el ejecutor lo calcula y lo pasa | `…_el_ejecutor_calcula_el_tope_de_cpu_y_se_lo_pasa_al_hijo` (2 casos) |
| R119 · el huérfano muere solo (Linux) | `…_en_linux_un_hijo_sin_padre_que_gasta_cpu_muere_solo_por_su_tope` |
| R119 · cuenta CPU y no reloj (Linux) | `…_en_linux_el_tope_de_cpu_cuenta_cpu_y_no_reloj` |
| R5-3 | `…_los_que_deben_leerse_llevan_el_tope_de_produccion_y_los_demas_3_s`, y la comprobación de `espia.topes` en el test de los 16 |
| T45 · documentación | `test_f036_documentacion.py::test_f036_t45_la_arquitectura_dice_el_tope_de_cpu_del_hijo` |

### Hallazgos

Ninguno bloquea el despliegue.

1. **R6-1 · [Menor, antes del merge] Una mutación que solo cae en Linux.**
   - **Qué pasa:** con `if segundos_cpu > 30:` delante de la llamada de
     `ejecutor_aislado.py:172`, la suite de Windows sigue en verde. Los tests
     doblados de `_principal_hijo` usan siempre 35 como tope de CPU.
   - **Dónde cae:** en el contenedor Linux, por el test real del huérfano, que
     usa 1 s. Ese test no corre en `init.sh` (Windows).
   - **Contradice** la frase del informe «ninguna cae solo en Linux», que vale
     para las 14 del implementer.
   - **Qué hacer:** en `…_el_hijo_se_pone_los_dos_topes_antes_del_byte_y_antes_de_leer`,
     pasar un segundo valor pequeño (por ejemplo 8), o parametrizarlo.
2. **R6-2 · [Menor, documental] «90–110 s de CPU» no es lo que mide Linux.**
   - **Qué pasa:** la cifra sale de mi review 5, que la estimó con las medidas de
     Windows sin tope de memoria. `requirements.md` (nota de R119) y `design.md`
     §5.2 («El hueco») la repiten.
   - **Lo medido ahora**, matando al padre con los tres ficheros de R4-1 y el
     código anterior: 33,0 s, 30,2 s y **60,0 s** de CPU. Con el arreglo: 30,6 s,
     30,2 s y **34,9 s**. Dos de los tres acaban solos antes de los 35 s, con o
     sin tope.
   - **Lo que no cambia:** el arreglo es correcto y necesario. Acota el tercero
     y cualquier fichero que gaste CPU sin gastar memoria, que sin tope no tenía
     límite.
   - **Qué hacer:** en la próxima enmienda, cambiar la cifra por la medida.
3. **R6-3 · [Menor] La orden de T49 en `tasks.md` no reproduce la campaña.**
   - **Qué pasa:** la verificación de T49 no lleva `--timeout 900`. Con los 120 s
     por defecto da 2 timeouts y ningún veredicto; el implementer lo dice.
   - Tampoco lo dice la cabecera del informe de la herramienta, que solo
     escribe `--base` y `--workers`.
   - **Qué hacer:** añadir `--timeout 900` a la orden de T49. Lo de la cabecera
     va en «Automejora».
4. **R6-4 · [Informativo, para T29] Qué se ve si Azure no deja poner el tope de
   CPU.**
   - Toda importación sería 400 `fichero_sospechoso`, con `estado=murio` y
     **`tope_memoria_aplicado=False`** en el log, aunque el de memoria sí se
     hubiera puesto: el hijo muere antes de mandar el byte.
   - En la salida de errores queda la traza de `setrlimit`, sin contenido del
     fichero.
   - Es el mismo síntoma que T29 8 bis (b) ya manda mirar. No hace falta paso
     nuevo.

### Lo que no he hecho, dicho

- **No he ejecutado en Linux la suite entera**, solo `test_f036_lector_aislado.py`
  (los `r119` y los del hijo) y mis guiones. El `conftest.py` necesita
  `pydantic`, que no se puede copiar del `.venv` de Windows.
- **No he relanzado los tests lentos** (`POSTVENTA_TESTS_LENTOS=1`). Los tres de
  R4-1 con los topes de producción los he pasado por el lector en el contenedor.
- **No he medido nada en Azure.** Que `setrlimit(RLIMIT_CPU)` se aplica en Flex
  Consumption se ve en T29.
- **No he pasado `ruff` con la configuración del servicio** sobre los ficheros
  tocados: no está en su `.venv`. El de la raíz, dentro de `init.sh`, da los
  mismos 71 avisos que antes.
- **No he podido saber por qué acaban** los huérfanos de «validación» y
  «escenario» a los 30–33 s de CPU: desde fuera no se ve su código de salida.
  Lo probable es el tope de memoria.

### Qué queda para el humano

- **Validar** las dos decisiones de la novena enmienda: el margen de 5 s y que
  el tope de CPU no tenga traza propia. Con lo medido, el margen es correcto:
  el tope de CPU no salta con el padre vivo.
- **T16, T27, T28 y T29**, en ese orden, con lo que dice la review 5 en «Qué
  debe mirar el humano». Dos añadidos:
  - **T27:** la rama lleva ya F-051 igual que `dev`. Tras desplegar, los App
    Settings del destino del archivo tienen que seguir como los dejó F-051.
  - **T29 8 bis (b):** `tope_memoria_aplicado=True` vale ahora para los dos
    topes. Si sale `False` con `estado=murio` en todas las importaciones, es
    R6-4.
- **Decidir R6-1, R6-2 y R6-3:** caben en el mismo encargo que T30.
- **T30** la lanza el líder después de las MANUAL.

### Automejora (propuesta, no aplicada)

- **`harness/mutacion.py`, `comando_de`.** Vale para `arnes-base`.
  - **Qué añadir:** escribir `--timeout` en la cabecera del informe cuando no es
    el valor por defecto, igual que ya se hace con `--base` y `--workers`.
  - **Por qué:** la cabecera de T49 no reproduce la campaña. Con el tope por
    defecto da 2 timeouts y ningún veredicto (R6-3).
- **`.claude/agents/reviewer.md`, punto 4.** Vale para `arnes-base`.
  - **Qué añadir:** cuando una feature tiene tests que solo corren en otra
    plataforma, el reviewer aplica al menos una mutación a mano que dependa del
    **valor** que usan los tests doblados, y dice en qué plataforma cae.
  - **Por qué:** la campaña y `init.sh` corren en Windows. R6-1 solo se ve
    comparando los valores de los tests doblados con los del test real.

## Review 7 (reviewer, 2026-10-02)

- **Veredicto:** CHANGES_REQUESTED
- **Rama:** `feature/F-036-importar-excel`, HEAD `50b42b1`. Review **acotada** a
  `git diff f103a2f..HEAD`: los menores de la review 6, el test de F-005 (T16),
  los commits del líder (F-052, `current.md`, informe de migración) y la décima
  enmienda con el Bloque 12 (T50–T54). Lo anterior quedó aprobado en la review 6.
- **Nivel de rigor:** `critico`, declarado. Puertas: fase RED, cobertura de las
  líneas cambiadas ≥ 80 %, mutación con cero supervivientes sin justificación
  aceptada por el humano (también los mutantes a mano), orden (punto 7) y
  `MANUAL (humano)` con su comando.
- **Código de producción que cambia:** solo el generador de
  `infrastructure/documentos/excel_openpyxl.py`. El lector, `lector_aislado.py`
  y `ejecutor_aislado.py` no cambian.

### Resumen para el líder

**El formato está bien hecho y no cambia nada de lo que lee el importador.**
Los valores son los de §3.6, los colores son los tokens de F-035 y los topes
se reproducen al elemento. **Una sola cosa impide aprobar**, y es pequeña:

- **R7-1 (bloquea, un test):** una mutación a mano sobre la impresión
  sobrevive. Si el generador añade un área de impresión que corta la hoja en la
  fila 50, ningún test cae.
- **R7-2 (para el humano):** Excel imprime las 1.000 filas, también las vacías.
  Una plantilla vacía saca 15 páginas y un `v2` de 158 filas, 17. No incumple
  R125, pero el humano lo verá al repetir T28.

Lo demás está bien: los menores de la review 6, el test de F-005, el informe de
migración sin códigos de proveedor y la campaña de T54. `bash harness/init.sh`
en verde, y la suite del `api` aparte: **6546 passed, 74 skipped**.

### Respuestas a los puntos del encargo

**1. Menores de la review 6.**

- **R6-1 cerrado.** El test va parametrizado con 35 y 8, con las mismas
  comprobaciones.
- **R6-2 cerrado.** Las cifras de `requirements.md` (nota de R119) y de
  `design.md` §5.2 son las que medí en la review 6, con nota de errata. No
  cambia ningún requisito.
- **R6-3 cerrado.** La orden de T49 lleva `--timeout 900`.

**2. El test de F-005 (`8f5b2f7`): ¿se ha debilitado de más?** No.

- La lista cerrada comprobaba dos cosas. Una era que las seis tablas existen:
  eso se conserva. La otra, que no hubiera ninguna más, y con trece tablas en el
  DDL eso ya no es una promesa de F-005.
- La resta del conjunto es correcta y el mensaje dice qué tabla falta.
- El control con una tabla inventada (cae, y dice cuál) es la prueba adecuada.
- Se pierde la alarma de «hay una tabla de más en el schema». Cada feature
  vigila sus propias tablas, así que no es una pérdida real.
- El hueco de `NUESTRAS_TABLAS` y que `tests_bbdd` siga fuera de `init.sh` ya
  lo apunta el implementer. No he lanzado la suite de base efímera.

**3. Commits del líder.**

- **F-052:** la entrada de `features.json` es válida y `BACKLOG.md` está al día
  (lo dice `init.sh`). Ni la descripción ni los criterios llevan ningún valor de
  secreto.
- **`progress/migracion_F-036.md` no lleva ningún código de proveedor.** Lo he
  comprobado con un guion, no a ojo:
  - el campo «Proveedor» sale 15 veces, siempre como «proveedor completado
    (único de la obra para ese oficio)»;
  - de los 122 códigos de cuatro cifras entre comillas invertidas, 121 van tras
    «Oficio: … (código » y el otro es la obra;
  - fuera de las comillas invertidas no hay ningún número de cuatro cifras o
    más;
  - R116 tiene su test, y está en verde dentro de la suite.

**4. R126, invariantes: lo he probado yo, en las dos direcciones.**

- **Cómo:** con `git archive` de `f103a2f` y de HEAD en mi scratchpad, cada
  generador sacó seis libros: vacía, rellena (3 filas), Excel de errores
  (3 filas, 2 con error), `v2` sintético (158 filas), plantilla completa y Excel
  de errores más grande.
- **Lectura:** los doce pasaron por el lector de HEAD **y** por el de
  `f103a2f`, cada uno en proceso (`LectorPlantillaOpenpyxl`) y con el hijo real
  (`LectorPlantillaAislado`), y después por `reconocer_plantilla` y
  `validar_filas`.

  | Fichero | Filas · válidas · con error | Mismo `LibroLeido` y mismo JSON antes/HEAD |
  |---|---|---|
  | vacía | 0 · 0 · 0 | **Sí** (`e5ff…`) |
  | rellena | 3 · 3 · 0 | **Sí** |
  | Excel de errores | 3 · 1 · 2 | **Sí** |
  | `v2` sintético | 158 · 158 · 0 | **Sí** |
  | plantilla completa | 1000 · 1000 · 0 | **Sí** (`466c8afea7b78ef3`) |
  | Excel de errores más grande | 1000 · 1000 · 0 | **Sí** (`466c8afea7b78ef3`) |

  - Con los dos lectores, el aislado devuelve lo mismo que el de en proceso,
    con versión 1, obra `0677` y sin datos fuera del tope.
  - **Una plantilla con el formato antiguo se importa igual con HEAD.**
  - **Al revés también:** si se vuelve atrás el backend, las plantillas con el
    formato nuevo se siguen leyendo igual.
- **Lo que no cambia en el XML de HEAD**, mirado en los libros generados:
  - la cabecera en la fila 1 con los mismos textos, los datos desde la fila 2 y
    ninguna celda combinada;
  - las mismas cuatro hojas, en el mismo orden y estado;
  - las 8 validaciones `A2:A1001`…`H2:H1001`;
  - `sheetProtection` con `insertRows`, `deleteRows`, `sort` y `autoFilter` a 0
    (permitidos) y `formatCells` a 1, igual que antes; los fija el test de R2
    que ya había;
  - el filtro `A1:I1001`, los paneles en `A2` y `@` con prefijo de comilla en
    las columnas de datos;
  - ningún `<f>`;
  - a nivel de libro, solo los seis nombres de las listas. `_xlnm.Print_Titles`
    es un nombre de la hoja.
- **El Excel de errores, de cerca:** la celda con error lleva relleno
  `FFFEF2F2` y fuente `FFB91C1C`, con su comentario; antes, `FFF4B084` sin
  color de fuente. La vecina sin error no lleva relleno y va en `FF1D2024`.
  `Errores` va en `FFF3F4F5` con texto `FF5D676D`. **Sin regla condicional y
  sin `<dxf>`.**
- **Fase RED reproducida:** con los tests de HEAD y el generador de `d64ff0a`,
  en una copia, caen **100** de `r121`–`r126` más los cuatro retocados, y los
  13 de `r126` pasan. El informe dice 101 en tres ficheros; el que falta es el
  `r127` de la regla, en `test_f036_lector_aislado.py`, que no lancé aquí.
  Cuadra.

**5. R127, topes: reproducidos, y el margen es honesto en lo que mide.**

| Medida | `f103a2f` | HEAD | Informe del implementer |
|---|---:|---:|---|
| Elementos, plantilla completa | 26.886 | **26.990** | 26.990 |
| Elementos, Excel de errores más grande | 148.916 | **149.016** | 149.016 (sobran 984 a 150.000) |
| Descomprimido, el mayor | 8.574.765 | **8.578.900** | 8.578.900 |
| JSON de `leer_en_hijo` | `466c8afea7b78ef3` | **idéntico** | idéntico |
| Hijo real, Excel de errores más grande | 1,40 s | 1,39 s | sin cambio apreciable |

- **Los 984 elementos son exactos y reproducibles**: el formato añade 100 al
  Excel de errores (~0,07 %).
- **Matiz que la spec no dice (R7-3, informativo).** «El legítimo más grande»
  se mide con el catálogo de los tests: 3 unidades, 4 oficios y 5 filas de
  `obrofc`. Con más catálogo, la hoja `_catalogos` crece. Lo he medido con el
  mismo Excel de errores:

  | Catálogo añadido | Antes del formato | Con el formato |
  |---|---:|---:|
  | +100 unidades, +30 oficios, +60 proveedores | 149.541 | 149.641 |
  | +300 unidades, +80 oficios, +200 proveedores | 150.911 | 151.011 |
  | +600 unidades, +150 oficios, +400 proveedores | 152.921 | 153.021 |

  Con un catálogo así, la guarda de la mitad ya se pasaba **antes** del
  formato. El tope de verdad (300.000) sigue con unos 147.000 de holgura. Es
  decir, los 984 son margen frente a la guarda de calibración, no frente al
  rechazo. No bloquea.
- **La regla de las bandas y el nombre de los títulos conviven con R4-1 y con
  la lectura en solo lectura:**
  - la ida y vuelta por el hijo real pasa (tabla del punto 4);
  - el constructor hostil «formato-condicional» sigue metiendo su propio
    `<conditionalFormatting>` delante de `<dataValidations`, detrás del
    legítimo: es el mismo ataque;
  - los 16 hostiles y `…_los_ficheros_de_r4_1_son_los_que_dicen_ser`, en verde
    en la suite.
- **¿Se cuela algo aprovechando lo legítimo? No.** Lo he probado con cuatro
  ficheros hostiles, todos construidos sobre la plantilla de HEAD y leídos por
  `LectorPlantillaAislado`. No hay ninguna lista blanca que explotar: el lector
  nunca ha distinguido un `sqref` ni un nombre «bueno», y lo caro lo mata el
  hijo.

  | Fichero hostil | Resultado |
  |---|---|
  | El `sqref` de las bandas inflado a 2,5 M de rangos (15 MB descomprimido) | 400 `fichero_sospechoso` a los **30,2 s** (el tope del hijo) |
  | `_xlnm.Print_Titles` con 4 MB sin «!» (la expresión de `openpyxl` es cuadrática) | `fichero_sospechoso` a los **30,05 s** |
  | `Print_Titles` con 1,5 M de coincidencias | se lee en 4,0 s, 0 filas |
  | `_xlnm.Print_Area` con 600.000 rangos | se lee en 3,0 s, 0 filas |

  El segundo caso ya era posible antes de esta enmienda: cualquier fichero
  puede traer ese nombre. No lo abre el formato, y lo para el tope del hijo.

**6. Fidelidad a lo aprobado.**

- **Colores:** los once ARGB del código son los de §3.6. Los diez con token
  coinciden con `:root` de `feature/F-035-portal-posventa` (`git show`);
  `BANDA` es propio, como dice la spec.
- **Fuentes, tamaños, alineaciones, bordes, altos y anchos:** iguales a §3.6,
  zona por zona.
  - Cabecera: 34 de alto; A–H en burdeos e I en acero; borde inferior `medium`
    `FF7A1E33`.
  - Cuerpo: Calibri 10,5 en tinta, cuatro lados `thin` `FFDFE2E4` y ajuste solo
    en C, D e I.
  - «Instrucciones»: la obra en Calibri 15 con 38 de alto, el título en 13 con
    28 de alto, los ejemplos con 26 de alto, la banda en la 2.ª y la 4.ª fila
    de ejemplo, y anchos 100 y 28.
- **Impresión:** A4, apaisado, 1 de ancho por 0 de alto, `fitToPage`, títulos
  `$1:$1`, márgenes laterales de 0,4 y el pie `&CPosventa · Construcciones
  Ruesma · página &P de &N` en el XML.
- **Excel de errores:** sin bandas, y la celda con error en rojo suave con el
  texto en rojo. Comprobado en el XML y por los tests.
- **Las pestañas** se guardan como `009F2842` y `007B868C` (alfa 00, cosa de
  `openpyxl` con seis cifras). Excel no usa el alfa en `tabColor`; lo verá el
  humano en T28.
- **La impresión, medida con Excel** (COM en local, solo lectura, sobre los
  ficheros del scratchpad, `PageSetup.Pages.Count`): ver R7-2.

  | Libro | Antes | HEAD |
  |---|---:|---:|
  | Plantilla vacía | 6 | 15 |
  | Excel de errores (3 filas) | 6 | 15 |
  | `v2` sintético (158 filas) | 36 | 17 |

  En las dos versiones, `UsedRange` es `A1:I1001`.

**7. Mutación.**

- **Recálculo puro** (`harness.alcance` y `generar_mutantes`, `--base
  07bd0c9`): **219 líneas y 60 mutantes**, los mismos del informe (41 de
  enteros, 10 de booleanos, 5 aritméticos, 3 de comparación y 1 de `not`).
  Con `--base f103a2f` sale igual: entre las dos bases no cambia producción.
  Control: el fichero entero da 180 mutantes, así que el generador de mutantes
  funciona.
- **«Tiempo total» de 1473,9 s (24,6 min):** el protocolo no obliga a
  reejecutar. **Campaña no reejecutada con la herramienta**, pero he pasado los
  60 mutantes uno a uno en seis copias de `git archive HEAD` contra
  `tests/test_f036_excel_generador.py`: **60 de 60 caen**, todos con `rc=1`.
- **Coste por mutante:** 1473,9 × 6 ÷ 60 = **147 s**. Es coherente con una
  campaña con `-x` que recorre la suite hasta los tests del generador.
- **El alcance es creíble.** Lo nuevo son sobre todo cadenas y decimales, que
  la herramienta no muta. Por eso hacen falta las mutaciones a mano.
- **Mis mutaciones a mano**, en copias desechables y nunca en el árbol:
  **31**. Caen 26 y sobreviven 5.
  - **Caen:**
    - **orden (M1):** el estilo del cuerpo después de marcar los errores
      pisaría la fuente roja; cae por `r123`;
    - bandas con `all()` o según `texto_errores`;
    - sin `fitToPage` o sin `fitToHeight`; el pie en `evenFooter` o a la
      derecha; papel `LEGAL`; columnas de título `A:A`;
    - `Errores` sin ajuste; el borde solo en las columnas de datos; la fuente de
      error en negrita; la cabecera de `Errores` en burdeos;
    - el alto del título en los párrafos; «Instrucciones» con cuadrícula;
    - fuente en la regla; dos reglas; un `sqref` de dos rangos;
    - la celda con error bloqueada o sin `@`;
    - una celda en I1 de «Instrucciones»; una fila 1002 con estilo;
    - combinar la banda de la obra o la cabecera;
    - los bordes de la cabecera de ejemplos.
  - **Sobreviven, también con los tests del lector, del lector aislado, de la
    migración y de HTTP** (632 passed):
    - **M18b**: `ws.print_area = "A1:I50"`. La impresión se corta en la fila
      50, en contra de R125 («las [páginas] de alto que hagan falta»).
      **Es R7-1.**
    - M18 (área de impresión `A1:I1001`, igual que `UsedRange`), M27 (`scale =
      50`, que Excel ignora con `fitToPage`), M28 (centrado horizontal) y M29
      (margen superior 0). Son ajustes que R125 no fija, no incumplen ningún
      requisito y no los declaro defecto. Pero en `critico` un superviviente a
      mano necesita un test o la aceptación escrita del humano. El arreglo de
      R7-1 los cierra a la vez.
- **Punto 7 (orden):** el requisito central del bloque no es una puerta de
  orden. El único orden que importa dentro del generador es «marcar el error
  después de dar estilo al cuerpo», y su mutación (M1) cae.

### Verificación ejecutada por el reviewer

| Qué | Resultado |
|---|---|
| `bash harness/init.sh` | exit 0, **ENTORNO LISTO**. Raíz: 62 passed. `api` y `front`, de la caché. `PUERTA COBERTURA: 99.9% de 3301 líneas cambiadas cubiertas (3297/3301, umbral 80%, nivel critico)`. ruff: 71 avisos, los de siempre. *Lo lancé con la salida redirigida a un fichero del scratchpad, no «tal cual»: una desviación de la regla de la allowlist que no cambia el resultado.* |
| Suite del `api` aparte (`.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider`) | **6546 passed, 74 skipped** en 398,5 s |
| Compatibilidad (punto 4) | 6 libros × 2 generadores × 2 lectores × (en proceso + hijo real): todo igual |
| Topes (punto 5) | Reproducidos al elemento y al byte; JSON idéntico |
| Hostiles sobre lo legítimo (punto 5) | 4 ficheros: 2 `fichero_sospechoso` a los 30 s y 2 leídos en 3–4 s |
| Fase RED | 100 failed (generador y lector) con el generador de `d64ff0a`; los 13 de `r126`, en verde |
| Mutación | Recálculo: 219 líneas y 60 mutantes. 60/60 caen con los tests del generador. A mano: 31, caen 26 |
| Impresión con Excel (COM, local) | Tabla del punto 6 |
| Barrido de datos sensibles | 2816 líneas añadidas en `f103a2f..HEAD`, con los patrones de la review 1 (correo, IPv4, GUID, `AIza…`, `api_key`/`password`/`secret`/`token`/`AccountKey`/`sig=` con asignación, `-----BEGIN`, `sk-…`, JWT). **16 coincidencias, todas falsos positivos** (`@pytest`, `@functools`). 0 reales |
| `print`, TODO | Ninguno en lo añadido |
| Ficheros añadidos (`git log --diff-filter=A f103a2f..HEAD`) | Solo `progress/mutacion_F-036_bloque12.md`. Ningún `.xlsx` ni PDF |
| Árbol de trabajo | `git status --porcelain` vacío antes de escribir este informe. Copias, libros y guiones, en el scratchpad |

### Checkpoints

#### C1 — El arnés está completo y en verde

- [x] `bash harness/init.sh`: exit 0. Suite del `api` aparte: 6546 passed.
- [x] Existen los ficheros del arnés (los comprueba `init.sh`).

#### C2 — El estado es coherente

- [x] Una sola `in_progress`, F-036. `blocked`: F-035, ajena. F-052,
  `pending`.
- [x] Rama `feature/F-036-importar-excel`.
- [x] `progress/current.md` empieza por el bloque vivo del Bloque 12. Todos los
  bloques son de la sesión de F-036.
- [x] Toda `done` tiene su entrada en `history.md`: no hay ninguna `done`
  nueva.

#### C3 — Arquitectura y convenciones

- [x] **Hexagonal:** el cambio está solo en el generador, en
  `infrastructure/documentos/`. No cambian el puerto, la firma de `generar`, el
  dominio ni el YAML.
- [x] **Primera línea con la ruta** en los cinco ficheros `.py` tocados y en el
  informe de mutación.
- [x] Sin `print()`, TODOs ni secretos. Sin dependencias nuevas:
  `FormulaRule`, `Border` y `Side` son de `openpyxl`, que ya estaba.
- N/A · «unidad de trabajo es el parte», «dry-run en Sigrid», «lo manuscrito»,
  «firmado no es conforme» y «número de estado». El bloque es el aspecto de un
  `.xlsx`: no procesa partes ni escribe en Sigrid. Justificado en la review 1.
- [x] Reprocesar no duplica: no se tocan la huella ni la bandeja, y el
  `LibroLeido` es idéntico (punto 4).
- [x] Ningún parte, PDF ni `.xlsx` en git.

#### C3 bis — Documentos que entran de fuera

- N/A · Nada en `docs/referencia/`, ni en `docs/`. El barrido de lo añadido
  está en la tabla: 0 hallazgos reales.

#### C4 — La verificación es real

- [x] **Trazabilidad:** R121 a R127 tienen sus tests `test_f036_r121_…` a
  `test_f036_r127_…` (tabla de abajo), en verde. Los cuatro tests del aspecto
  antiguo cambian solo lo que §3.6 dice.
- [x] Los unit tests no tocan red ni BBDD. Todo en memoria; el hijo real usa
  solo IPC local.
- [x] Las `MANUAL (humano)` siguen en `tasks.md` con su comando, con los avisos
  de la décima enmienda: redesplegar el backend, repetir T28 y el paso 5 de
  T29.

#### C4 bis — El rigor declarado se cumple

- [x] `rigor: "critico"`.
- [x] **Fase RED** con salida real (`101 failed, 493 passed`), reproducida
  (punto 4).
- [x] **Cobertura:** `[OK]` 99,9 % (3297/3301).
- [x] **Mutación:** existe `mutacion_F-036_bloque12.md`, generado por la
  herramienta, con totales verificados: 219 líneas y 60 mutantes.
- [x] **Muertos comprobados:** la campaña tardó 24,6 min, así que vale el
  recálculo puro, **y lo digo**. Además pasé los 60 mutantes contra los tests
  del generador: 60/60 caen.
- [x] **Coste por mutante:** 147 s con 6 workers. Coherente.
- [ ] **Cero supervivientes en `critico`, también a mano.** M18b (área de
  impresión que corta en la fila 50) sobrevive a toda la suite de F-036 del
  Excel, y M18, M27, M28 y M29 tampoco caen. Ninguno tiene aceptación del
  humano. **R7-1.**
- [x] «Evidencias» con los cuatro números y los workers (6).
- [x] Ningún N/A sin justificar en este bloque.

#### C4 ter — Rutas sensibles

- N/A: no existe `harness/rutas_sensibles.json`.

#### C5 — La sesión se cerró bien

- [x] `tasks.md`: T50 a T54 en `[x]`, con un commit `F-036 Tn:` por tarea
  (`a505e4a`, `4eba996`, `9e7b781`, `218c9f6`, `33be26e`). **Siguen sin marcar
  a propósito** T16 y T27–T29 (MANUAL del humano) y T30 (del líder).
- [x] Sin ficheros temporales ni sin trackear. El *worktree*
  `agent-a6e2f9bed1d46cdbc` ya existía y no es de este encargo.
- [x] `features.json`: F-036 `in_progress`; F-052 dada de alta, `pending`.

### Cobertura: requisito → test (solo lo nuevo)

| Req. | Tests |
|---|---|
| R121 | `test_f036_excel_generador.py`: `…_r121_cabecera_de_incidencias` (9 columnas × 2 libros), `…_r121_la_fila_de_la_cabecera_mide_34_puntos`, `…_r121_el_texto_de_la_cabecera_no_cambia` |
| R122 | `…_r122_cuerpo_de_incidencias` (8 × 4 filas), `…_r122_el_formato_no_crea_celdas_fuera_de_la_plantilla`, `…_r122_r124_las_hojas_visibles_no_ensenan_la_cuadricula`, `…_r122_r124_las_hojas_ocultas_no_llevan_formato`, `…_r122_r124_color_de_las_pestanas`, `…_r122_bandas_alternas_una_sola_regla_condicional_en_la_plantilla`, `…_r122_el_v2_sin_errores_lleva_las_bandas`, `…_r122_las_bandas_dependen_de_los_errores_y_no_del_origen`, `…_r122_con_alguna_fila_con_error_no_hay_regla_condicional` (5); `s3_1_anchos…` retocado |
| R123 | `…_r123_la_columna_errores_va_en_gris_no_editable`, `…_r123_celda_con_error_en_rojo_suave_con_el_texto_en_rojo`, `…_r123_la_vecina_sin_error_no_lleva_ni_relleno_ni_rojo`; `r64_celdas_con_error_marcadas…` retocado |
| R124 | `…_r124_fila_1_…`, `…_r124_fila_2_…`, `…_r124_parrafos_en_calibri_11_con_el_alto_calculado`, `…_r124_el_parrafo_del_excel_de_errores_y_el_de_sin_oficios_tambien`, `…_r124_alto_de_un_parrafo_en_sus_fronteras` (8), `…_r124_los_cuatro_numeros…`, `…_r124_el_alto_del_parrafo_no_baja_del_minimo`, `…_r124_parrafo_corto_y_largo_en_el_libro`, `…_r124_cabecera_de_los_ejemplos`, `…_r124_filas_de_ejemplo_con_la_segunda_y_la_cuarta_en_banda`, `…_r124_los_ejemplos_del_yaml_con_su_banda`; `r5_disposicion…` y `r5_anchos…` retocados |
| R125 | `…_r125_impresion_de_incidencias` (2), `…_r125_instrucciones_sin_ajustes_de_impresion_propios` (2). **Le falta lo de R7-1** |
| R126 | Generador: `…_r126_las_mismas_partes_en_el_zip_y_ninguna_imagen`, `…_mismas_cuatro_hojas…`, `…_cabecera_en_la_fila_1…`, `…_rangos_con_nombre…`, `…_validaciones_proteccion_filtro_paneles_y_formato_de_texto`, `…_misma_version_e_identificador`, `…_ningun_xml_de_hoja_lleva_formulas_de_celda`. Lector: `…_r126_ida_y_vuelta_de_la_plantilla_rellena_con_formato`, `…_del_excel_de_errores_con_formato`, `…_sin_el_formato_se_lee_el_mismo_libro` (3), `…_una_plantilla_con_el_formato_antiguo_se_importa_igual`. Lector aislado: `…_r126_ida_y_vuelta_por_el_lector_aislado_con_el_hijo_real` (2) |
| R127 | `test_f036_lector_aislado.py`: `…_r127_la_mitad_del_presupuesto_son_150000_elementos`, `…_el_excel_de_errores_mas_grande_cabe_en_la_mitad_del_presupuesto`, `…_la_plantilla_completa_lleva_una_regla_condicional_de_un_rango`, `…_el_excel_de_errores_mas_grande_no_lleva_regla_condicional`, `…_las_partes_del_zip_son_las_de_siempre_y_sin_imagenes`, `…_el_formato_no_crea_celdas_fuera_de_la_plantilla` (2) |

### Hallazgos

1. **R7-1 · [Bloquea · un test] La impresión de «Incidencias» no está fijada
   entera.**
   - **Qué pasa:** con `ws.print_area = "A1:I50"` detrás de `print_title_rows`,
     en `_incidencias` de `excel_openpyxl.py` (bloque «Impresión (R125)»), la
     hoja imprime solo hasta la fila 50. Contradice R125 («ajustada a una
     página de ancho y a las de alto que hagan falta»), y pasan todos los tests
     del generador, del lector, del lector aislado, de la migración y de HTTP
     (632 passed).
   - **Lo mismo** con otros ajustes que §3.6 no pide: área igual a la usada,
     `scale`, centrado y márgenes superior e inferior.
   - **Qué hacer:** en
     `tests/test_f036_excel_generador.py::test_f036_r125_impresion_de_incidencias`,
     fijar también lo que **no** se pone, igual que ya hace
     `…_instrucciones_sin_ajustes_de_impresion_propios`:
     - `ws.print_area` vacío (`openpyxl` devuelve `""` cuando no hay área; con M18b, `'Incidencias'!$A$1:$I$50`);
     - ningún nombre definido de la hoja aparte de los títulos (`list(ws.defined_names) == []`);
     - `ws.page_setup.scale is None`;
     - `ws.print_options.horizontalCentered` y `verticalCentered` sin poner;
     - los márgenes superior, inferior, de cabecera y de pie con su valor por
       defecto (1, 1, 0,5 y 0,5).

     Sin código de producción. Basta con comprobar que M18b cae.
   - **Alternativa:** que el humano acepte por escrito esos supervivientes.
     No la recomiendo: el test cuesta cinco líneas.
2. **R7-2 · [Para el humano, antes o durante la T28 repetida] Excel imprime
   las 1.000 filas.**
   - **Qué pasa:** el cuerpo lleva bordes en las 1.000 filas y `Errores` lleva
     relleno, así que Excel cuenta como usado `A1:I1001` y lo imprime entero:
     - plantilla vacía o Excel de errores de 3 filas: **15 páginas**;
     - `v2` de 158 filas: **17 páginas**, de las que unas 13 son filas vacías
       con su rejilla.

     Antes eran 6 y 36: tampoco era bueno, porque partía las columnas.
   - **No incumple R125** ni lo aprobado. La muestra no decía nada de páginas
     vacías.
   - **Qué decidir:**
     - (a) se acepta así;
     - (b) se pone un área de impresión hasta la última fila con datos. Es
       fácil en el `v2` y en el Excel de errores, pero en una plantilla que el
       usuario rellena después se quedaría corta;
     - (c) que «Instrucciones» diga «imprimir selección».

     Si se decide (b), R7-1 cambia de sentido: el test fijaría el área, no su
     ausencia.
3. **R7-3 · [Informativo, para el spec-author] «El Excel de errores más grande»
   depende del catálogo de los tests.**
   - Con +300 unidades, +80 oficios y +200 filas de proveedor, ese Excel pasa
     de 150.000 elementos **sin** el formato (150.911), y con él, de 151.011.
   - Los 984 de margen son frente a la guarda de calibración (la mitad), no
     frente al rechazo: el tope de 300.000 sigue con unos 147.000 de holgura.
   - Conviene que §5.2 lo diga, para que nadie lea «984» como «a punto de
     rechazar».
   - El test `…_cabe_en_la_mitad_del_presupuesto` está bien como guarda del
     generador: usa un catálogo fijo.
4. **R7-4 · [Informativo] Un nombre `Print_Titles` hostil cuesta 30 s de
   hijo.**
   - La expresión de `openpyxl` que lo analiza es cuadrática. Con 4 MB sin «!»,
     el hijo agota su tope y la respuesta es `fichero_sospechoso`.
   - Es la misma familia que R4-1 y ya era posible antes de esta enmienda. El
     formato no la abre: el lector no da trato especial al nombre legítimo.
   - No pide cambio. Se suma a lo que T29 8 bis (c) ya mira.

### Cambios requeridos

1. **R7-1:** en
   `services/postventa-api/tests/test_f036_excel_generador.py`, función
   `test_f036_r125_impresion_de_incidencias` (líneas 1270–1289 de HEAD),
   añadir las comprobaciones de ausencia de R7-1. Verificación: el test en
   verde sobre HEAD, y en rojo con `ws.print_area = "A1:I50"` añadido después
   de `ws.print_title_rows = "1:1"` en `excel_openpyxl.py`, en una copia (no en
   el árbol). Pegar las dos salidas en `progress/impl_F-036.md`. No hace falta
   relanzar la campaña de la herramienta: no cambia producción. Si el humano
   elige la opción (b) de R7-2, el cambio es otro: lo decide el humano antes.

### Lo que no he hecho, dicho

- **No he relanzado la campaña con `harness.mutacion`**, porque pasa de 5 min
  (24,6 min según el informe). Me quedo en el recálculo puro, más los 60
  mutantes contra los tests del generador.
- **No he reproducido las 57 mutaciones a mano del implementer**: su guion no
  está versionado. He hecho 31 propias, distintas en su mayoría.
- **No he abierto los libros en Excel para mirarlos** ni en Excel web ni en
  LibreOffice. Solo he preguntado a Excel (COM, invisible y en solo lectura)
  por las páginas de impresión. El aspecto lo valida el humano en la T28
  repetida.
- **No he lanzado `tests_bbdd`** (base efímera en Docker). Del test de F-005
  revisé el código; la ejecución es la del implementer y la del humano.
- **No he medido nada en Linux ni en Azure** en esta review.

### Qué queda para el humano

- **Decidir R7-2** (las páginas de impresión), mejor antes de arreglar R7-1,
  porque cambia lo que el test tiene que fijar.
- **Después de R7-1, review 8 corta** (solo ese test). Luego:
  - redesplegar el backend;
  - **repetir T28**: comprobar además la vista previa de impresión (R7-2) y el
    color de las pestañas;
  - **T29**, con el paso 5 de la décima enmienda: una plantilla descargada
    **antes** del redespliegue tiene que importarse igual. Lo he comprobado en
    local en las dos direcciones;
  - **T30**, del líder;
  - merge a `dev`.
- Siguen por validar del Bloque 12 las decisiones del spec-author: el Excel de
  errores sin bandas, el orden de recorte, los umbrales de tiempo y memoria y la
  impresión solo en «Incidencias». Con lo medido no hizo falta recortar nada.

### Automejora (propuesta, no aplicada)

- **`CHECKPOINTS.md`, C4 bis.** Vale para `arnes-base`.
  - **Qué añadir:** cuando lo nuevo de una feature es **configuración
    declarativa** (estilos, ajustes de página, cabeceras HTTP, opciones de un
    cliente), los tests tienen que fijar también lo que **no** se pone en el
    mismo objeto, no solo lo que se pone.
  - **Por qué:** `harness.mutacion` no añade asignaciones, solo cambia las que
    hay. Un ajuste de más (R7-1) no lo genera nunca, y la campaña sale 60/60
    con el hueco dentro.

## Review 8 (reviewer, 2026-10-02)

- **Veredicto:** CHANGES_REQUESTED
- **Rama:** `feature/F-036-importar-excel`, HEAD `d7df483`. Review **acotada** a
  `git diff 26a190e..HEAD`: la enmienda 10 bis (`af2b937`) y el Bloque 13
  (T55–T60, `8330529`..`d7df483`). Lo anterior quedó revisado en la review 7.
- **Nivel de rigor:** `critico`, declarado. Puertas: fase RED, cobertura de las
  líneas cambiadas ≥ 80 %, mutación con cero supervivientes sin aceptación
  escrita del humano (también los mutantes a mano), orden (punto 7) y
  `MANUAL (humano)` con su comando.
- **Código de producción que cambia:** solo `_incidencias`, dos constantes y el
  docstring de `infrastructure/documentos/excel_openpyxl.py`. El lector,
  `lector_aislado.py` y `ejecutor_aislado.py` no cambian.

### Resumen para el líder

**La enmienda está bien hecha y Excel la pinta tal como pide la spec.**

- La plantilla vacía enseña la cabecera y la fila 2. Al escribir en la 3, esa
  fila se pinta entera, con su banda.
- Los desplegables, el desbloqueo y el `@` siguen en las 1.000 filas.
- Ninguna hoja lleva ajustes de impresión.
- Los topes se reproducen al elemento (**149.025**).
- Las plantillas de `f103a2f` y de `50b42b1`, generadas de verdad, se importan
  igual con los dos lectores, en las dos direcciones.

**Lo que impide aprobar es poco, y son solo tests** (ninguna línea de
producción):

- **R8-1 (bloquea):** el formato de las reglas no está fijado entero en los
  tests. Si la regla 1 lleva además una **diagonal**, ningún test cae, y Excel
  pinta un aspa en cada celda pintada (comprobado por COM).
- **R8-2 (bloquea):** la «ausencia de impresión» de R125 tiene dos rendijas.
  Ningún test cae con la hoja en vista «Diseño de página» o «Vista previa de
  salto de página», ni con `pageSetUpPr` puesto sin `fitToPage`.

Lo demás es informativo.

### Respuestas a los puntos del encargo

**1. R126: lo he probado yo, con libros generados de verdad por los tres
generadores.**

- **Cómo:** `git archive` de `f103a2f` (formato antiguo), `50b42b1` (formato de
  la décima, el real y no el simulado del test) y HEAD, en el scratchpad. Cada
  generador sacó seis libros: plantilla vacía, rellena (3 filas), Excel de
  errores (3 filas, 2 con error), `v2` sintético (158 filas), plantilla
  completa y Excel de errores más grande.
- **Lectura, en las dos direcciones:** los 18 libros pasaron por el lector de
  HEAD **y** por el de `50b42b1`. Cada uno se leyó en proceso
  (`LectorPlantillaOpenpyxl`) y con el hijo real (`LectorPlantillaAislado`),
  y después pasó por `reconocer_plantilla` y `validar_filas`.

  | Libro | Filas · válidas · con error | Mismo `LibroLeido` de los tres generadores, con los dos lectores |
  |---|---|---|
  | vacía | 0 · 0 · 0 | **Sí** (`7bc710d6…`) |
  | rellena | 3 · 3 · 0 | **Sí** |
  | Excel de errores | 3 · 1 · 2 | **Sí** |
  | `v2` sintético | 158 · 158 · 0 | **Sí** |
  | plantilla completa | 1000 · 1000 · 0 | **Sí** (`3e33ccd7…`) |
  | Excel de errores más grande | 1000 · 1000 · 0 | **Sí** (`3e33ccd7…`) |

  En todos, el aislado da lo mismo que el de en proceso, con versión 1, obra
  `0677` y sin datos fuera del tope.
- **Lo que lee el importador, celda a celda** (guion propio con `openpyxl`,
  comparando HEAD con los otros dos generadores): las 9.009 celdas de
  `A1:I1001` coinciden en valor, tipo, `number_format`, `locked` y
  `quotePrefix`. Coinciden también:
  - las 8 validaciones (rango, tipo, fórmula, mensajes y desplegable);
  - la protección;
  - las hojas, su estado y la activa;
  - el filtro `A1:I1001` y los paneles en `A2`;
  - los nombres definidos (sin contar `Print_Titles`);
  - `_plantilla` y `_catalogos`;
  - ninguna celda combinada y ningún `<f>`.

  **Ninguna diferencia en los seis tipos de libro.** En HEAD, las filas 2–1001
  llevan `A`–`H` desbloqueadas y con `@`, e `I` bloqueada: 0 celdas fuera de
  esa regla en los seis libros.
- **Y Excel lo confirma** (COM, solo lectura, sin guardar). En la vacía, el
  `v2` y el Excel de errores, `A3`, `A500` y `H1001` dan `Locked=False`,
  `NumberFormat=@` y `Validation.Type=3` (lista), con su `=lista_…` y
  `InCellDropdown=True`. **El desplegable sigue en las filas vacías**, como se
  le dijo al humano.

**2. Las tres reglas.**

- **El XML de HEAD es el de §3.6, carácter a carácter:**
  - `A2:I1001`, prioridad 1, `OR(ROW()=2,COUNTA($A2:$I2)&gt;0)`, `dxf` con los
    cuatro lados `thin` `FFDFE2E4`;
  - `I2:I1001`, prioridad 2, la misma fórmula, `dxf` con relleno sólido
    `bgColor FFF3F4F5`;
  - `A2:H1001`, prioridad 3, `AND(MOD(ROW(),2)=1,COUNTA($A2:$I2)&gt;0)`, `dxf`
    con relleno `bgColor FFFAFAFB`;
  - sin `stopIfTrue`, `<dxfs count="3">`, y en el Excel de errores, la 1 y la 2
    con `<dxfs count="2">`;
  - ninguna regla en las otras tres hojas.
- **Excel 16 (COM) las lee igual:** tres `FormatConditions` con esos
  `AppliesTo` y prioridades, y `StopIfTrue=False`. En español las enseña como
  `=O(FILA()=2;CONTARA($A2:$I2)>0)` y
  `=Y(RESIDUO(FILA();2)=1;CONTARA($A2:$I2)>0)`, como anticipa §3.6.
- **El formato efectivo (`DisplayFormat`), en la plantilla vacía:**

  | Celda | Fondo | Fuente | Bordes (izq., arr., abj., der.) |
  |---|---|---|---|
  | `A2`, `H2` | ninguno | `1D2024` 10,5 | `thin DFE2E4`; arriba, el `medium 7A1E33` de la cabecera |
  | `I2` | `F3F4F5` | `5D676D` 10,5 | igual |
  | `A3`, `I3` (vacías) | ninguno | igual | solo el de arriba (es el de abajo de la fila 2); los otros, ninguno |
  | `A4` … `A1001` (vacías) | ninguno | igual | **ninguno** |
  | `A3` tras escribir «Cocina» en `B3` | `FAFAFB` | igual | los cuatro `thin DFE2E4` |
  | `I3` tras escribir en `B3` | `F3F4F5` | igual | los cuatro |
  | `A4` tras escribir en `C4` (fila par) | ninguno (sin banda) | igual | los cuatro |

- **`v2` (158 filas):** las filas 2–159 pintadas, con banda en las impares y el
  gris en `I`. La 160 y las siguientes, en blanco. Lo que se ve de la 160 es el
  borde de abajo de la 159.
- **Excel de errores:** `A3`, `C3` y `E4`, con error, salen en `FEF2F2` con
  texto `B91C1C` y las líneas de la regla 1. `B3`, sin error, sin relleno. Sin
  bandas.
- Los libros eran los generados en el scratchpad, y se cerraron sin guardar.
  Las escrituras de `B3` y `C4` fueron en memoria.

**3. R125: ninguna configuración de impresión, y el test la fija (casi
entera).**

- **En los seis libros de HEAD:**
  - ninguna hoja lleva `<pageSetup`, `<printOptions`, `<headerFooter`,
    `<rowBreaks`, `<colBreaks` ni `fitToPage`;
  - `<pageMargins>` es el de defecto de `openpyxl` (0,75 / 0,75 / 1 / 1 /
    0,5 / 0,5), el valor que R125 admite;
  - `xl/workbook.xml` lleva exactamente los seis nombres de las listas y
    `_xlnm._FilterDatabase`, sin ningún `_xlnm.Print_`.
- **Los libros de `50b42b1` sí llevaban** `pageSetup`, `headerFooter`,
  `fitToPage`, márgenes de 0,4 y `_xlnm.Print_Titles`. La comparación es
  significativa.
- **Los tests:**
  - `…_r125_ninguna_hoja_lleva_ajustes_de_impresion` (2 libros × 4 hojas) y
    `…_r125_ni_las_hojas_ni_el_libro_llevan_impresion_en_el_xml` cubren lo que
    R125 enumera;
  - las mutaciones M18, M18b, M27, M28 y M29 de la review 7 caen (las pasó el
    implementer), y mi R13, `page_setup.copies = 2`, cae por el XML;
  - **dos rendijas, en R8-2.**

**4. R127 y R4-1.**

- **Medición de T57, reproducida al elemento**
  (`lector_aislado._contar_elementos_xml(..., presupuesto=None)`, los mismos
  constructores de `_legitimos()`):

  | Medida | `f103a2f` | `50b42b1` | HEAD | Informe (T57) |
  |---|---:|---:|---:|---|
  | Elementos, plantilla completa | 26.886 | 26.990 | **26.998** | 26.998 |
  | Elementos, Excel de errores más grande | 148.916 | 149.016 | **149.025** | 149.025 (sobran 975 a 150.000) |
  | Descomprimido, el mayor | 8.574.765 | 8.578.900 | **8.579.139** | 8.579.139 |
  | JSON de `leer_en_hijo`, el mayor | 5.257.211 | 5.257.211 | **5.257.211** | idéntico |
  | `sha256` del JSON | `466c8afea7b78ef3` | igual | **igual** | igual |

  Los topes no cambian: 300.000 elementos, 17 MiB y 11 MiB.
- **Los `sqref` legítimos conviven con R4-1 sin abrir hueco.** Hostiles
  construidos sobre la plantilla vacía de HEAD y leídos por
  `LectorPlantillaAislado`:

  | Fichero hostil | Resultado |
  |---|---|
  | El `sqref` de la regla 1 (`A2:I1001`) inflado con 2,5 M de rangos (56 KB, 15,3 MB descomprimido) | `fichero_sospechoso` a los **30,4 s** (tope del hijo) |
  | La regla 2 repetida 100.000 veces | `fichero_sospechoso` en **1,0 s** (presupuesto de elementos, paso barato) |
  | La regla 2 repetida 40.000 veces (7,2 MB descomprimido, por debajo del presupuesto) | **leído**, 0 filas, en 19,0 s con la máquina cargada (R8-6) |

  El lector sigue sin distinguir un `sqref` legítimo de uno hostil: lo caro lo
  mata el hijo. Los 16 hostiles de R4-1 y
  `…_los_ficheros_de_r4_1_son_los_que_dicen_ser` están en verde: los repetí
  con la máquina tranquila, en la tabla de verificación.

**5. Mutación.**

- **La herramienta, recalculada** (`harness.alcance.alcance_de_feature("F-036",
  base="26a190e")` y `generar_mutantes`, cálculo puro): **1 fichero, 49 líneas,
  0 mutantes**, lo mismo que el informe.
  - **Prueba de control del cero** (punto 4 del protocolo): sobre el fichero
    entero, **177 mutantes** (90 de enteros, 40 de booleanos, 19 aritméticos,
    13 lógicos, 11 de comparación y 4 de `not`). El generador funciona.
  - **El cero es legítimo:** las 49 líneas (23–36, 134–135, 205–213, 373–376,
    422–441 y 455) son el docstring, comentarios, dos constantes de cadena y
    dos llamadas `conditional_formatting.add(...)` con f-strings. No hay
    ningún operador que la herramienta mute. La línea `if not any(...)` no
    cambió desde `26a190e`.
  - «Tiempo total» 0,0 s con 0 mutantes: **campaña no reejecutada**, porque no
    hay mutantes. Vale el recálculo con su control.
- **Las 85 mutaciones a mano del implementer: creíbles.** Sus guiones no están
  versionados, así que no las he repetido una a una. Pero las 11 de mis 19 que
  coinciden en tipo con las suyas caen igual y por los mismos tests:
  - R4: una cuarta regla; R5: la regla 1 con un `sqref` de dos rangos;
  - R6, R7 y R8: la condición de las bandas por `texto_errores`, por `not
    filas` y con `all`;
  - R9: fuente del cuerpo en negrita; R13: `page_setup.copies`;
  - R14: fuente en la regla 1; R15: borde estático en `I1001`;
  - R16: sin el relleno rojo; R17: la regla 3 desde la fila 3.

  **El hueco de las 9.000 celdas es real, y el test lo cierra:** mi R15 (borde
  fijo solo en `I1001`) cae por él. **La fase RED de T55, reproducida:** con los
  tests de HEAD y el generador de `50b42b1`, en una copia, salen **105
  failed, 540 passed, 7 skipped**. Son los 102 de T55 más los 3 casos del test
  de T60, con el mismo reparto por test.
- **Mis mutaciones a mano:** 19, en una copia desechable (`cp` de un `git
  archive HEAD`), contra `tests/test_f036_excel_generador.py`. Cada una sola,
  con el fichero restaurado tras cada una (`diff` final con HEAD: idéntico).
  **Caen 11 y sobreviven 8:**

  | Mutante | Qué hace | ¿Se ve en Excel? | Hallazgo |
  |---|---|---|---|
  | **R1** | El `dxf` de la regla 1 con `diagonal` `thin` y `diagonalDown=True` | **Sí**: `DisplayFormat.Borders(xlDiagonalDown)` continua en `A2`, `A3` e `I3`, un aspa en cada celda pintada | **R8-1** |
  | **R2** | El `dxf` de la regla 2 con `fgColor=ERROR` además de `bgColor` | No: Excel sigue pintando `F3F4F5` (usa `bgColor`). Equivalente a la vista, distinto en el fichero | **R8-1** |
  | **R3** | El `dxf` de la regla 3 con `fgColor=BURDEOS` además | No (`FAFAFB`). Igual que R2 | **R8-1** |
  | **R10** | `ws.sheet_view.view = "pageLayout"` en «Incidencias» | Sí: la hoja se abre en «Diseño de página», con páginas y reglas | **R8-2** |
  | **R11** | `ws.sheet_view.view = "pageBreakPreview"` | Sí: «Vista previa de salto de página» | **R8-2** |
  | **R12** | `pageSetUpPr = PageSetupProperties(autoPageBreaks=False)` | Apenas (los saltos automáticos) | **R8-2**: el test admite `pageSetUpPr` mientras `fitToPage` sea `None` |
  | **R18** | `ws.sheet_view.showRowColHeaders = False` | Sí: sin encabezados de fila y columna | **R8-3** |
  | **R19** | `workbook.calculation.calcMode = "manual"` | No lo he medido | **R8-3** |

  - R1–R3 son de lo **nuevo** de este bloque, los formatos de las reglas.
  - R10–R12 son de lo que R125 promete ausente.
  - R18 y R19 son de objetos que este bloque no toca: el `sheetView` solo lo
    toca la décima, con `showGridLines`, y `calcPr` nadie.
- **Punto 7 (orden):** el requisito central no es una puerta de orden. Lo único
  que importa en el orden es la prioridad de las reglas, y su mutación (alta en
  otro orden, prioridades cambiadas) cae, según el informe del implementer. No
  hay colaboradores que una puerta preceda.

**6. CHECKPOINTS:** abajo.

### Verificación ejecutada por el reviewer

| Qué | Resultado |
|---|---|
| `bash harness/init.sh` (tal cual) | exit 0, **ENTORNO LISTO**. Raíz: 62 passed. `api` y `front`, **de la caché** («árbol sin cambios desde el último verde»). `PUERTA COBERTURA: 99.9% de 3289 líneas cambiadas cubiertas (3285/3289, umbral 80%, nivel critico)`. ruff: 71 avisos, los de siempre |
| Suite del `api` aparte (`.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider`), porque `init.sh` la sirvió de la caché | **6595 passed, 2 failed, 74 skipped** en 1.507 s, con la máquina muy cargada por un guion mío colgado (ver R8-5). Los 2, `…_t18_sin_puertos_inyectados_se_construyen_los_de_verdad` y `…_r118_los_hostiles_de_todas_las_reviews…[review-1-celda-en-la-fila-1048576]`, son el tope de 30 s del hijo (`estado=tiempo segundos=30.00`) sobre ficheros que se tienen que leer. **Repetidos con la máquina tranquila: 17 passed** (`…_t18_…` y el parametrizado entero de los hostiles). En la salida, ningún `repr` de `Ajustes` (`grep -c` → 0) |
| R126 (punto 1) | 6 libros × 3 generadores × 2 lectores × (en proceso + hijo real): mismo `LibroLeido`. Estructura celda a celda: 0 diferencias |
| Reglas y R125 en el XML (puntos 2 y 3) | Conformes en los 6 libros de HEAD; los de `50b42b1`, con su impresión |
| Excel por COM (Excel 16, invisible, solo lectura, sin guardar) | Tabla del punto 2. Además, R8-4: `UsedRange` y páginas |
| Topes (punto 4) | Reproducidos al elemento y al byte; JSON idéntico |
| Hostiles sobre los `sqref` legítimos (punto 4) | 3 ficheros: 30,4 s → `fichero_sospechoso`; 1,0 s → `fichero_sospechoso`; 19,0 s → leído |
| Fase RED | `105 failed, 540 passed, 7 skipped` (tests de HEAD y generador de `50b42b1`) |
| Mutación | Recálculo: 49 líneas y 0 mutantes; control: 177. A mano: 19, caen 11 y sobreviven 8 |
| Barrido de datos sensibles | 1.853 líneas añadidas en `26a190e..HEAD`, con los patrones de la review 1 (correo, IPv4, GUID, `AIza…`, `api_key`/`password`/`secret`/`token`/`AccountKey`/`sig` con asignación, `-----BEGIN`, `sk-…`, JWT). **10 coincidencias, todas falsos positivos** (`@pytest`, `@functools`). 0 reales |
| `print`, TODO | Ninguno en lo añadido |
| Ficheros añadidos (`git log --diff-filter=A 26a190e..HEAD`) | Solo `progress/mutacion_F-036_bloque13.md`. Ningún `.xlsx` ni PDF |
| Árbol de trabajo | `git status --porcelain` vacío antes de escribir este informe. Copias, libros y guiones, en el scratchpad |

### Checkpoints

#### C1 — El arnés está completo y en verde

- [x] `bash harness/init.sh`: exit 0. La suite del `api` aparte: verde salvo 2
  timeouts por carga, verdes al repetirlos (R8-5).
- [x] Los ficheros del arnés existen (los comprueba `init.sh`).

#### C2 — El estado es coherente

- [x] Una sola `in_progress`, F-036. `blocked`: F-035, ajena.
- [x] Rama `feature/F-036-importar-excel`.
- [x] `progress/current.md` empieza por el bloque vivo (T59–T60) y todos sus
  bloques son de la sesión de F-036.
- [x] No hay ninguna `done` nueva.

#### C3 — Arquitectura y convenciones

- [x] **Hexagonal:** el cambio está solo en el generador, en
  `infrastructure/documentos/`. No cambian el puerto, la firma de `generar`, el
  dominio, el YAML ni el lector (`git diff 26a190e..HEAD` de producción: un
  fichero).
- [x] **Primera línea con la ruta** en los cuatro `.py` tocados y en el informe
  de mutación.
- [x] Sin `print()`, TODOs ni secretos. Sin dependencias nuevas.
- N/A · «unidad de trabajo es el parte», «dry-run en Sigrid», «lo manuscrito»,
  «firmado no es conforme», «número de estado». El bloque es el aspecto de un
  `.xlsx`: no procesa partes ni escribe en Sigrid. Justificado en la review 1.
- [x] Reprocesar no duplica: ni la huella ni la bandeja cambian, y el
  `LibroLeido` es idéntico (punto 1).
- [x] Ningún parte, PDF ni `.xlsx` en git.

#### C3 bis — Documentos que entran de fuera

- N/A · Nada en `docs/referencia/` ni en `docs/` (T58 no cambió nada). El
  barrido de lo añadido está en la tabla: 0 hallazgos reales.

#### C4 — La verificación es real

- [x] **Trazabilidad:** R122, R123, R125, R126 y R127, tal como quedan, tienen
  sus tests `test_f036_r12x_…` (tabla de abajo), en verde.
  - La desviación de T55 (`…_r123_la_vecina_sin_error_…`, una línea a
    `SIN_BORDES`) está justificada: R122 retira el borde estático.
  - Los cuatro renombres, también: el nombre viejo afirmaba lo contrario.
- [x] Los unit tests no tocan red ni BBDD. El hijo real usa solo IPC local.
- [x] Las `MANUAL (humano)` siguen en `tasks.md` con su comando. T28 y T29 ya
  dicen «ninguna comprobación de impresión», y T28 incluye «una fila a la vista
  y se pinta al escribir».

#### C4 bis — El rigor declarado se cumple

- [x] `rigor: "critico"`.
- [x] **Fase RED** con salida real (`102 failed, 540 passed` en T55, y `1
  failed, 238 passed` por mutante en T60), reproducida: 105 failed (punto 5).
- [x] **Cobertura:** `[OK]` 99,9 % (3285/3289).
- [x] **Mutación:** `mutacion_F-036_bloque13.md`, generado por la herramienta,
  con los totales verificados (49 líneas, 0 mutantes) y la prueba de control
  del cero (177 en el fichero entero).
- [x] **Muertos comprobados:** no hay mutantes de la herramienta. La campaña no
  se reejecuta, porque con 0 mutantes no hay nada que matar, **y lo digo**.
- [x] **Coste por mutante:** no aplica con 0 mutantes (0,0 s, 1 worker real; el
  informe explica por qué no son 6).
- [ ] **Cero supervivientes en `critico`, también a mano.** Sobreviven 8 de mis
  19 (R1–R3, R10–R12, R18, R19), sin test que los cace ni aceptación escrita
  del humano. **R8-1, R8-2 y R8-3.**
- [x] «Evidencias» con los cuatro números y los workers.
- [x] Ningún N/A sin justificar en este bloque.

#### C4 ter — Rutas sensibles

- N/A: no existe `harness/rutas_sensibles.json`.

#### C5 — La sesión se cerró bien

- [x] `tasks.md`: T55–T60 en `[x]`, con un commit `F-036 Tn:` por tarea
  (`8330529`, `89078a9`, `322a4d0`, `3eab450`, `a84ac02`). T59 es del líder y
  del humano: está marcada con la constancia del visto bueno en `a84ac02`.
  **Siguen sin marcar a propósito** T16 y T27–T29 (MANUAL del humano) y T30
  (del líder).
- [x] Sin ficheros temporales ni sin trackear.
- [x] `features.json`: F-036 `in_progress`.

### Cobertura: requisito → test (solo lo que cambia en la 10 bis)

| Req. | Tests |
|---|---|
| R122 | `test_f036_excel_generador.py`: `…_r122_cuerpo_de_incidencias` (sin bordes fijos), `…_r122_sin_bordes_ni_relleno_estaticos_en_el_cuerpo` (36), `…_r122_ninguna_celda_del_cuerpo_lleva_borde_relleno_ni_fuente_de_mas` (3; las 9.000 celdas), `…_r122_r123_la_plantilla_lleva_las_tres_reglas_condicionales`, `…_r122_el_v2_sin_errores_lleva_las_bandas`, `…_r122_las_bandas_dependen_de_los_errores_y_no_del_origen`, `…_r122_con_alguna_fila_con_error_no_hay_regla_de_bandas` (5), `…_r122_r123_las_reglas_en_el_xml` (3). **Al `dxf` le falta R8-1** |
| R123 | `…_r123_la_columna_errores_va_en_gris_no_editable` (8), `…_r123_celda_con_error_en_rojo_suave_con_el_texto_en_rojo` (3), `…_r123_la_vecina_sin_error_no_lleva_ni_relleno_ni_rojo` (5), `…_r64_celdas_con_error_marcadas_con_relleno_y_comentario` |
| R125 | `…_r125_ninguna_hoja_lleva_ajustes_de_impresion` (8), `…_r125_ni_las_hojas_ni_el_libro_llevan_impresion_en_el_xml` (2). **Le falta R8-2** |
| R126 | Lector: `…_r126_una_plantilla_con_el_formato_de_la_decima_se_importa_igual` (nuevo) y los que ya había. Lector aislado: `…_r126_los_formatos_anteriores_por_el_lector_aislado_con_el_hijo_real` (`decima`, `antiguo`; nuevo) y `…_r126_ida_y_vuelta_por_el_lector_aislado_con_el_hijo_real` (2) |
| R127 | `test_f036_lector_aislado.py`: `…_r127_la_plantilla_completa_lleva_tres_reglas_condicionales_de_un_rango`, `…_r127_el_excel_de_errores_mas_grande_lleva_dos_reglas_condicionales` y los de topes que ya había |

### Hallazgos

1. **R8-1 · [Bloquea · un test] El formato (`dxf`) de las tres reglas no está
   fijado entero.**
   - **Qué pasa:** `_comprobar_reglas` comprueba los cuatro lados, `fill` y
     `font` de cada `dxf`; el test del XML, solo `<dxfs count="N">`. Lo que
     sobra en el mismo `dxf` no lo ve nadie:
     - **R1:** la regla 1 con una diagonal. Pasan los 239 tests del generador.
       Excel pinta un aspa en cada celda pintada (`DisplayFormat.Borders(5)`
       continua en `A2`, `A3` e `I3`). Contradice R122: el formato de la regla
       1 son «los cuatro bordes finos», y nada más.
     - **R2 y R3:** `fgColor` además del `bgColor` en las reglas 2 y 3. Excel
       los ignora en un relleno sólido diferencial: es equivalente a la vista,
       pero el fichero no es el de §3.6.
   - **Qué hacer:** fijar el bloque `<dxfs>` **entero y literal** en
     `test_f036_r122_r123_las_reglas_en_el_xml`
     (`tests/test_f036_excel_generador.py`, línea 1167), en vez de solo su
     `count`. Es el que escribe HEAD hoy:
     - plantilla y `v2`: `<dxfs count="3"><dxf><border><left style="thin"><color rgb="FFDFE2E4" /></left><right style="thin"><color rgb="FFDFE2E4" /></right><top style="thin"><color rgb="FFDFE2E4" /></top><bottom style="thin"><color rgb="FFDFE2E4" /></bottom></border></dxf><dxf><fill><patternFill patternType="solid"><bgColor rgb="FFF3F4F5" /></patternFill></fill></dxf><dxf><fill><patternFill patternType="solid"><bgColor rgb="FFFAFAFB" /></patternFill></fill></dxf></dxfs>`;
     - Excel de errores: los dos primeros `<dxf>`, con `count="2"`.

     Una sola comparación caza cualquier atributo de más: diagonal, `fgColor`,
     `numFmt`, `alignment`, `protection`… Sin código de producción.
   - **Alternativa:** que el humano acepte por escrito R2 y R3 como
     equivalentes. R1 no es equivalente.
2. **R8-2 · [Bloquea · un test] La «ausencia de impresión» de R125 tiene dos
   rendijas.**
   - **R10 y R11:** la hoja en vista «Diseño de página»
     (`sheet_view.view = "pageLayout"`) o «Vista previa de salto de página»
     (`"pageBreakPreview"`). Pasan todos los tests. Son las vistas de
     impresión de Excel, y con ellas la plantilla vacía deja de «enseñar la
     cabecera y una fila»: se abre como hojas de papel.
   - **R12:** `pageSetUpPr` puesto (`autoPageBreaks=False`) sin `fitToPage`.
     Pasa, porque el test admite `ajuste is None or ajuste.fitToPage is None`
     (línea 1442).
   - **Qué hacer:** en `test_f036_r125_ninguna_hoja_lleva_ajustes_de_impresion`
     (línea 1426):
     - `assert ws.sheet_properties.pageSetUpPr is None`, en lugar de la línea
       1442; es lo que devuelve HEAD;
     - `assert ws.sheet_view.view in (None, "normal")` en las cuatro hojas.

     Sin código de producción.
3. **R8-3 · [Para decidir antes de T30: un test o la aceptación del humano]
   Dos supervivientes fuera de lo que toca este bloque.**
   - **R18:** `sheet_view.showRowColHeaders = False`, que esconde los
     encabezados de fila y columna. Se vería.
   - **R19:** `calculation.calcMode = "manual"` en el libro. No he medido si
     cambia algo de las reglas.
   - Son objetos que la 10 bis no toca (el `sheetView` es de la décima, el
     `calcPr` de nadie), así que no los cargo a este bloque. Pero en `critico`
     un superviviente a mano necesita test o aceptación escrita del humano.
   - **Lo más barato:** una línea más en el mismo test de R8-2 para R18
     (`showRowColHeaders` no `False` en «Incidencias» e «Instrucciones»), y
     `libro.calculation.calcMode in (None, "auto")` para R19.
4. **R8-4 · [Informativo, para T28] Excel sigue dando por usadas las 1.000
   filas.**
   - **Qué pasa:** `UsedRange` es `A1:I1001` en los tres libros, porque las
     9.000 celdas del cuerpo llevan estilo estático (fuente, alineación,
     desbloqueo, `@`), como pide R126. A la vista no se nota: las filas vacías
     no tienen ni línea ni relleno. Pero Ctrl+Fin lleva a `I1001` y la barra de
     desplazamiento llega a la fila 1001.
   - **Si alguien imprimiera** (el humano decidió que no se imprime): la
     plantilla vacía saldría en 5 páginas en blanco y el `v2` de 158 filas, en
     29. Sin ajuste a una página de ancho, las columnas se parten.
   - No incumple nada. Conviene que el humano lo sepa al repetir T28.
5. **R8-5 · [Informativo] Los tests con el hijo real dependen de la carga de la
   máquina.**
   - Un guion mío sin la guarda `__main__` se quedó lanzando hijos `spawn`.
     Con esa carga, dos tests que **tienen que leer** sus ficheros llegaron al
     tope de 30 s del hijo.
   - Con la máquina tranquila pasan (17 passed). No es de este bloque, y no
     pide cambio.
   - El implementer también vio la suite pasar de 833 s a 1.975 s por carga.
     Si `init.sh` corre en una máquina saturada, esos tests pueden dar un rojo
     falso.
6. **R8-6 · [Informativo] 40.000 reglas repetidas se leen en 19 s.**
   - Con la máquina cargada, un fichero de 61 KB con la regla 2 repetida
     40.000 veces pasa el presupuesto de elementos (≈131.000) y el hijo lo lee
     en 19 s.
   - Es la familia de R4-1 y R7-4, acotada por el tope de 30 s: no la abre
     esta enmienda, porque cualquier fichero puede traer esas reglas.
   - Se suma a lo que T29 8 bis (c) ya mira.

### Cambios requeridos

1. **R8-1:** en `services/postventa-api/tests/test_f036_excel_generador.py`,
   `test_f036_r122_r123_las_reglas_en_el_xml` (línea 1167), comparar el bloque
   `<dxfs>…</dxfs>` de `xl/styles.xml` entero con el literal de arriba (tres
   `dxf`, o los dos primeros en el Excel de errores).
2. **R8-2:** en el mismo fichero,
   `test_f036_r125_ninguna_hoja_lleva_ajustes_de_impresion`:
   - la línea 1442 pasa a `assert ws.sheet_properties.pageSetUpPr is None`;
   - añadir `assert ws.sheet_view.view in (None, "normal")`.
3. **R8-3:** añadir las dos comprobaciones de R18 y R19, o traer la aceptación
   escrita del humano para esos dos supervivientes.

**Verificación:** cada mutante de esta tabla, solo, en una copia desechable (no
en el árbol), tiene que dar `rc=1` con `tests/test_f036_excel_generador.py`; y
el fichero, en verde sobre HEAD. Pegar en `progress/impl_F-036.md` la salida
de HEAD y la de cada mutante.

| Mutante | Cambio en `excel_openpyxl.py` |
|---|---|
| R1 | regla 1 con `border=Border(<los cuatro lados>, diagonal=Side(style='thin', color=ACERO_100), diagonalDown=True)` |
| R2 | regla 2 con `fgColor=ERROR` además de `bgColor=LIENZO` |
| R3 | regla 3 con `fgColor=BURDEOS` además de `bgColor=BANDA` |
| R10 | `ws.sheet_view.view = "pageLayout"` al final de `_incidencias` |
| R11 | `ws.sheet_view.view = "pageBreakPreview"` al final de `_incidencias` |
| R12 | `ws.sheet_properties.pageSetUpPr = PageSetupProperties(autoPageBreaks=False)` al final de `_incidencias` |
| R18 | `ws.sheet_view.showRowColHeaders = False` al final de `_incidencias` (si se elige test) |
| R19 | `ws.parent.calculation.calcMode = "manual"` al final de `_incidencias` (si se elige test) |

No hace falta relanzar `harness.mutacion`: no cambia producción.

### Lo que no he hecho, dicho

- **No he repetido una a una las 85 mutaciones a mano del implementer**: sus
  guiones no están versionados. He hecho 19 propias; las 11 que coinciden en
  tipo con las suyas caen igual.
- **No he abierto los libros en Excel para mirarlos con los ojos.** He
  preguntado a Excel por COM (invisible, solo lectura, sin guardar) por el
  formato efectivo, las reglas, las validaciones y las páginas. El aspecto lo
  validó el humano en T59 y lo vuelve a ver en T28.
- **No he probado Excel web ni LibreOffice.**
- **No he lanzado `tests_bbdd`**, ni medido nada en Linux ni en Azure.
- `init.sh` sirvió el `api` de la caché. Por eso lancé la suite aparte, con el
  resultado de la tabla.

### Qué queda para el humano

- **Después de R8-1 y R8-2** (y de R8-3, con test o con su aceptación),
  **review 9 corta**, solo esos tests. Luego:
  - redesplegar el backend;
  - **repetir T28**, que ahora incluye «una fila a la vista y se pinta al
    escribir»; tener en cuenta R8-4 (Ctrl+Fin y la barra llegan a la 1001);
  - **T29**, con el paso 5: una plantilla descargada antes del redespliegue se
    importa igual. Lo he comprobado en local con los generadores reales de
    `f103a2f` y `50b42b1`;
  - **T30**, del líder;
  - merge a `dev`.
- **Siguen por validar** las decisiones del spec-author de la 10 bis que la
  muestra de T59 ya enseñó:
  - la fórmula de «fila pintada», que cuenta también `Errores`;
  - el Excel de errores sin bandas;
  - el nuevo orden de recorte;
  - que insertar encima de la fila 2 deja la nueva fuera de las reglas.

### Automejora (propuesta, no aplicada)

- **`CHECKPOINTS.md`, C4 bis, y `.claude/agents/reviewer.md`, punto 4.** Vale
  para `arnes-base`.
  - **Qué añadir:** cuando lo nuevo de una feature es configuración
    declarativa y la herramienta da 0 mutantes, el reviewer no se limita a
    comprobar que caen las mutaciones a mano del implementer. Hace además
    **mutaciones aditivas** sobre los mismos objetos: atributos de más, de los
    que el código no pone. Y el test de referencia para un bloque así es
    comparar el **fragmento serializado entero** (aquí, `<dxfs>`), no campo a
    campo.
  - **Por qué:** es la segunda review seguida (R7-1 y ahora R8-1) en la que los
    supervivientes son atributos añadidos que ni `harness.mutacion` ni las
    mutaciones del implementer generan, porque ambos parten de lo que el código
    ya escribe.

## Review 9 (reviewer, 2026-10-02)

- **Veredicto:** APPROVED
- **Rama:** `feature/F-036-importar-excel`, HEAD `07b2d4b`. Review **corta**,
  acotada a `git diff c1ebb94..HEAD`: los arreglos de la review 8 (`4aced00`,
  `c6de60f`, `07b2d4b`). Solo cambian
  `services/postventa-api/tests/test_f036_excel_generador.py`,
  `progress/impl_F-036.md` y `progress/current.md`.
- **Nivel de rigor:** `critico`, declarado. Lo que esta review tenía que cerrar
  es la puerta «cero supervivientes, también a mano» de C4 bis, que la review 8
  dejó en `[ ]` por R1–R3, R10–R12, R18 y R19.

### Resumen para el líder

**Los tres cambios requeridos están hechos y los he verificado yo.** Los 8
supervivientes de la review 8 caen ahora, cada uno solo, con `rc=1`. Además
caen 6 mutantes aditivos míos sobre los `dxf`. El fichero de tests está en
verde sobre HEAD, `bash harness/init.sh` también, y producción no cambia. La
desviación del implementer en R12 es correcta y cierra igual.

### Respuestas a los puntos del encargo

**1. ¿Están hechos los tres cambios? Sí. Verificación repetida por mí.**

- **Cómo:** `git archive HEAD services/postventa-api` en el scratchpad (copia
  desechable, no el árbol), con el `.venv` del servicio. Cada mutante se aplicó
  solo a `infrastructure/documentos/excel_openpyxl.py` de la copia, y el fichero
  se restauró después de cada uno (al final, `restaurado: True`). Se lanzó
  `pytest -q -p no:cacheprovider --tb=no -rf tests/test_f036_excel_generador.py`.
  Con `--tb=no`, la salida no trae ningún `repr`.
- **HEAD, sin mutantes:** `239 passed in 56.26s`, **rc=0**.
- **Los 8 de la review 8:**

  | Mutante | Cambio | rc | Tests que caen |
  |---|---|---|---|
  | R1 | regla 1 con `diagonal` `thin` y `diagonalDown=True` | **1** | `…_r122_r123_las_reglas_en_el_xml` [vacia, rellena, errores] (3) |
  | R2 | regla 2 con `fgColor=ERROR` además de `bgColor` | **1** | el mismo, 3 casos |
  | R3 | regla 3 con `fgColor=BURDEOS` además de `bgColor` | **1** | el mismo, [vacia, rellena] (2): el Excel de errores no lleva regla 3 |
  | R10 | `sheet_view.view = "pageLayout"` | **1** | `…_r125_ninguna_hoja_lleva_ajustes_de_impresion` [Incidencias × 2] |
  | R11 | `sheet_view.view = "pageBreakPreview"` | **1** | el mismo, 2 casos |
  | R12 | `pageSetUpPr = PageSetupProperties(autoPageBreaks=False)` | **1** | el mismo, 2 casos, **y** `…_r125_ni_las_hojas_ni_el_libro_llevan_impresion_en_el_xml` [plantilla, errores] (4) |
  | R18 | `sheet_view.showRowColHeaders = False` | **1** | `…_r125_ninguna_hoja…` [Incidencias × 2] |
  | R19 | `parent.calculation.calcMode = "manual"` | **1** | `…_r125_ninguna_hoja…`, las 4 hojas × 2 libros (8) |

  Los mismos tests que fallan en `progress/impl_F-036.md`, y en el mismo número.
  No he repetido la fase RED contra los tests de `c1ebb94`: la review 8 ya
  mostró que esos 8 sobrevivían con ellos.

**2. La desviación de R12: es cierta, y la alternativa cierra igual.**

- **Lo he comprobado en el `openpyxl` del `.venv` (3.1.5):**
  - `WorksheetProperties.__init__` hace `if pageSetUpPr is None: pageSetUpPr =
    PageSetupProperties()`. Así que **al leer** un libro con `load_workbook`
    (que es lo que hace el test), `pageSetUpPr` nunca es `None`. Aunque el
    fichero no lo traiga.
  - **Al escribir**, un `Workbook()` recién creado sale con `<sheetPr><outlinePr
    … /><pageSetUpPr /></sheetPr>`.
  - Con la línea literal de la review 8 (`is None`), el test caería en HEAD sin
    cambio de producción. **Mi indicación de la review 8 («es lo que devuelve
    HEAD») estaba mal.**
- **Un matiz, sin efecto:** «imposible» es demasiado. Si el generador asignara
  `pageSetUpPr = None` en memoria, `openpyxl` no lo escribiría. Pero eso sería
  aún más «ausente», y el test lo admite (`ajuste is None or …`, y en el XML el
  conjunto vacío cumple `<= {b"<pageSetUpPr />"}`).
- **Cierra igual R12, por dos lados:**
  - `Serialisable.__iter__` solo devuelve los atributos distintos de `None`
    (leído en el fuente). Por eso `dict(ajuste) == {}` falla con
    **cualquier** atributo puesto (`autoPageBreaks`, `fitToPage`), no solo con
    `fitToPage`.
  - En el XML, el único `<pageSetUpPr …>` admitido es el vacío.
  - R12 cae por los dos (4 failed, arriba). Es la misma comprobación que pedía
    la review 8, escrita como la entiende `openpyxl`.

**3. ¿La comparación C14N del `<dxfs>` caza cualquier atributo o hijo de más?
Sí, y lo he probado con mutantes aditivos propios, además de R1–R3.**

| Mutante | Qué añade al `dxf` | rc | Caen |
|---|---|---|---|
| X1 | regla 1: `alignment` (hijo) | **1** | `…_las_reglas_en_el_xml` × 3 |
| X2 | regla 2: `protection` (hijo) | **1** | × 3 |
| X3 | regla 3: `numFmt` (hijo) | **1** | × 2 (vacia, rellena) |
| X4 | regla 1: `outline="0"` en `<border>` (atributo) | **1** | × 3 |
| X5 | regla 3: `font` en cursiva (hijo) | **1** | × 2, más los 3 de `_comprobar_reglas` |
| X6 | regla 2: `tint` en el `<bgColor>` (atributo de un nieto) | **1** | × 3 |

- **Por qué es general:** `ElementTree.canonicalize` (C14N 2.0) conserva todos
  los elementos y atributos. Solo normaliza el orden de los atributos, las
  comillas y los espacios: `strip_text=True` quita espacios de texto, y en un
  `dxf` no hay texto. Cualquier elemento o atributo de más, en cualquier nivel,
  cambia la forma canónica. Un `<dxf>` de más cambia además el `count`.
- **Lo único que no ve**, y no importa:
  - **Los comentarios XML** (`with_comments=False` por defecto), que no son
    formato.
  - **Un elemento o atributo con prefijo** (`x14:`…): el fragmento extraído no
    trae las declaraciones de espacio de nombres, así que daría `unbound
    prefix` al parsear. Sería una excepción, y por tanto también rojo. No lo he
    ejecutado: lo deduzco del parser.
- **Fuera de esta comparación:** a qué `dxfId` apunta cada regla. Eso lo fija
  `_comprobar_reglas`, que ya estaba (review 8), y X5 lo confirma de paso.

**4. `git diff c1ebb94 HEAD -- services/postventa-api/infrastructure`: vacío**
(0 bytes). En `c1ebb94..HEAD` solo cambian el fichero de tests y los dos de
`progress/`.

### Verificación ejecutada por el reviewer

| Qué | Resultado |
|---|---|
| `bash harness/init.sh` (tal cual, en segundo plano) | exit 0, **ENTORNO LISTO**. Raíz: 62 passed. `api`: **6597 passed, 74 skipped** en 1.604 s (esta vez no se sirvió de la caché: el árbol cambió). `front`: de la caché. `PUERTA COBERTURA: 99.9% de 3289 líneas cambiadas cubiertas (3285/3289, umbral 80%, nivel critico)`. ruff: 71 avisos, los de siempre. Ningún `repr` de `Ajustes` en la salida (`grep -c` → 0) |
| `test_f036_excel_generador.py` sobre HEAD (copia) | 239 passed, rc=0 |
| 8 mutantes de la review 8 + 6 aditivos propios, cada uno solo | **14 de 14 con rc=1** |
| ruff del fichero de tests | solo `I001` (bloque de imports), el mismo que da el fichero de `c1ebb94`: ninguno nuevo |
| Barrido de lo añadido en `c1ebb94..HEAD` (`print(`, TODO, claves, IPv4, GUID, `AIza`, `-----BEGIN`) | 1 coincidencia, falso positivo (la palabra «secreto» en el informe). 0 reales |
| Primera línea con la ruta | sí, en el fichero de tests |
| Árbol de trabajo | `git status --porcelain` vacío antes de escribir este informe. La copia, el guion y la salida, en el scratchpad |

### Checkpoints (lo que esta review cambia; el resto, como en la review 8)

- [x] **C1:** `init.sh` exit 0, ficheros del arnés presentes.
- [x] **C2:** una sola `in_progress` (F-036), en su rama. `current.md` empieza
  por el bloque de los arreglos de la review 8. Ninguna `done` nueva.
- [x] **C3:** sin cambio de producción, así que la arquitectura no cambia. Sin
  `print`, TODOs ni secretos. Sin dependencias nuevas
  (`xml.etree.ElementTree` es de la biblioteca estándar).
  - N/A, con el mismo motivo de la review 1: lo de partes, Sigrid y firmas. El
    cambio son tests del aspecto de un `.xlsx`.
- N/A · **C3 bis:** no entra nada en `docs/referencia/` ni en `docs/`.
- [x] **C4:** R122, R123 y R125 siguen trazados a sus tests (tabla de la review
  8). Ahora el `dxf` está fijado entero (R122) y R125 incluye vistas,
  `pageSetUpPr`, encabezados y cálculo. En verde.
- [x] **C4 bis:**
  - `rigor: "critico"`.
  - **Fase RED:** el implementer la trae con salida real (los 8, rc=0 con los
    tests de `c1ebb94`), y la review 8 ya la había visto.
  - **Cobertura:** `[OK]` 99,9 %.
  - **Mutación:** la herramienta no se relanza, porque no cambia producción
    (lo dijo la review 8). A mano: **0 supervivientes abiertos** (14 de 14
    caen).
  - **Evidencias:** la sección está en el informe, con los cuatro números.
  - **Orden (punto 7):** N/A. No hay puerta de orden entre colaboradores (ver
    la review 8).
- N/A · **C4 ter:** no existe `harness/rutas_sensibles.json`.
- [x] **C5:** commits `F-036 R8-1`, `F-036 R8-2 y R8-3` y `F-036 R8`. No son
  tareas de `tasks.md`, sino arreglos de review, con el formato de las reviews
  anteriores. `tasks.md` no cambia: siguen abiertas, a propósito, T16 y
  T27–T29 (MANUAL del humano) y T30 (del líder). Sin ficheros sin trackear.

### Hallazgos

Ninguno bloqueante. Uno informativo:

1. **R9-1 · [Informativo] Mi indicación de R12 en la review 8 era
   inaplicable.** Pedí `pageSetUpPr is None` diciendo que «es lo que devuelve
   HEAD», y no lo es: `openpyxl` lo construye siempre. El implementer lo
   detectó, lo justificó y lo cerró igual. Queda anotado para que nadie
   «corrija» el test hacia la letra de la review 8.

### Qué queda para el humano

- Redesplegar el backend.
- **Repetir T28**, con «una fila a la vista y se pinta al escribir». Tener en
  cuenta R8-4: Ctrl+Fin y la barra de desplazamiento llegan a la fila 1001.
- **T29**, con el paso 5: una plantilla descargada antes del redespliegue se
  importa igual.
- **T30**, del líder. Ojo: este `init.sh` ya ha corrido entero en verde sobre
  `07b2d4b`.
- Merge a `dev`.
- **Siguen por validar** las decisiones del spec-author de la 10 bis que
  enumeró la review 8:
  - la fórmula de «fila pintada», que cuenta también `Errores`;
  - el Excel de errores sin bandas;
  - el orden de recorte;
  - que una fila insertada encima de la 2 queda fuera de las reglas.

### Automejora (propuesta, no aplicada)

- **`.claude/agents/reviewer.md`, sección «Informe».** Vale para `arnes-base`.
  - **Qué añadir:** cuando el reviewer dicte la línea exacta de un `assert` en
    «Cambios requeridos», la ejecuta antes sobre HEAD. Si no se puede ejecutar,
    la marca como «orientativa».
  - **Por qué:** R9-1. Una línea dictada y sin probar obliga al implementer a
    desviarse, y al reviewer siguiente, a auditar esa desviación.

## Review 10 (reviewer, 2026-10-03)

- **Veredicto:** CHANGES_REQUESTED
- **Rama:** `feature/F-036-importar-excel`, HEAD `91e0a12`. Review **acotada**
  a `git diff 540ce92..HEAD`:
  - el estado de T28/T29 en `current.md` (`b56a718`);
  - la undécima enmienda (`394ced4`);
  - el Bloque 14, T61–T64 (`01e28d7`..`91e0a12`).
  Cambia producción en `services/postventa-api/scripts/migracion_f036.py` y
  `services/postventa-api/scripts/migrar_excel_f036.py`; los tests, en
  `tests/test_f036_migracion.py`.
- **Nivel de rigor:** `critico`, declarado en `harness/features.json`. Exige
  fase RED, cobertura, mutación con cero supervivientes sin justificación
  aceptada por el humano (también a mano) y MANUAL listadas.

### Resumen para el líder

El código hace lo que dice la spec, y el ensayo en seco de T63 lo he
reproducido igual. **Rechazo por un solo motivo, y se arregla con tests:**

- una mutación mía **sobrevive**: comparar con `oficios_catalogo` sin tildes;
- R128 exige comparar «mayúsculas, tildes y puntuación, tal cual»;
- y es justo el caso de los 7 «grupos de nombres iguales» del catálogo global,
  que no son nombres iguales sino **gemelos que solo difieren en la tilde**.

En `critico`, un superviviente no equivalente es CHANGES_REQUESTED. Además,
un retoque de estilo (R10-2). Ni el uno ni el otro cambian el comportamiento:
no hay que relanzar la campaña de la herramienta ni repetir T63.

### Respuestas a los puntos del encargo

**1. ¿Es sólida la distinción entre «ha salido de la obra» (vacío y aviso) y
«errata» (para)?**

**En el código, sí.** `componer` (líneas 684–710) sigue el orden de §10.5:

- busca primero en la obra, que manda;
- si hay varios oficios de la obra con ese nombre, para;
- si no está en la obra pero sí en `nombres_sigrid`, deja la fila vacía y lo
  apunta;
- si no está en ninguno, para.

El nombre de la tabla se compara tal cual. Solo se recortan los de Sigrid
(`nombres_de_sigrid`, línea 551). El fallo de cualquier comparación que no case
**es seguro**: si Sigrid escribe el nombre con otra diferencia que no sea de
blancos en los extremos, el script para; no se vacía nada.

**Los datos reales** los medí con un guion del scratchpad que no imprime
proveedores:

- **No hay nombres repetidos exactos** en `auxofc`: 130 filas y 130 nombres el
  2026-09-29; 133 y 133 el 2026-10-03. Tampoco hay nulos, vacíos ni blancos en
  los extremos.
- Los **7 grupos** son pares que solo difieren en la tilde: «Albañileria» y
  «Albañilería», «Carpinteria de madera» y «Carpintería de madera»,
  «Fontaneria» y «Fontanería», «Carpinteria de aluminio» y «Carpintería de
  aluminio», «Cerrajeria» y «Cerrajería», «Climatizacion» y «Climatización»,
  «Calefaccion y suelo refrescante» y «Calefacción y suelo refrescante».
- **En la tabla, 5 de los 12 nombres** tienen gemelo sin tilde en `auxofc`:
  Albañilería, Carpintería de aluminio, Carpintería de madera, Cerrajería y
  Fontanería. Suman 52 filas nuevas.
- Hoy, los 12 nombres de la tabla son exactos: los 12 casaban con la obra del
  2026-09-29. **La tabla actual no tiene erratas.**

**Sí hay un caso en que una errata se toma por «ha salido de la obra»:** una
errata de tilde cuyo gemelo exista en `auxofc`, cuando ese gemelo no es de la
obra. Por ejemplo, con la obra de hoy:

- si alguien escribe en el YAML «Albañileria» o «Carpinteria de aluminio», la
  fila sale **sin oficio y con aviso**;
- antes del Bloque 14, el script paraba.

Con la de ayer pasaba igual con «Fontaneria» o «Cerrajeria». **No es
silencioso**: la fila sale en la sección de R130, con el nombre, y en la línea
de órdenes. Pero el criterio (a) de T28 da la sección por «diferencia
esperable», y nadie mira si el nombre tiene un gemelo en la obra.

- **Hoy no muerde**: el único nombre afectado es «V-Aire acondicionado» (0118).
  No tiene ningún gemelo, plegando tildes, mayúsculas y espacios, ni en la obra
  ni en `auxofc`. Ha salido de la obra sin sustituto: en la 0677 de hoy no hay
  ningún oficio de climatización.
- **Lo que hace falta para R128 tal como está** es que un test fije la
  comparación exacta frente a `oficios_catalogo`. Falta (R10-1).
- **Lo que haría falta para avisar** del gemelo es una decisión de spec. La
  dejo al humano en «Qué queda».

**Al revés** (que pare algo que de verdad ha salido de la obra): solo pasaría
si Sigrid cambiara el texto del nombre, además de sacarlo de la obra. Eso es el
«renombrado» de la decisión 2 del spec-author, que para a propósito. Es el
lado seguro.

**Las bajas:** el `.ps1` saca `oficios_obra` sin bajas
(`ISNULL(a.fecbaj, 0) = 0`) y `oficios_catalogo` con todo `auxofc`. Un oficio
de la obra dado de baja cae en R128, como dice la spec.

**Los gemelos dentro de la obra de hoy:** 0046/0143, 0047/0134, 0050/0147 y
0094/0153. Ya están en el fichero de grupos del 2026-10-02. Eso explica el
paso de 42 a 47 filas «con grupo de varios códigos». La decisión 4 del
spec-author (revisar las propuestas nuevas en `oficios.html`) sigue siendo del
humano.

**2. R129: ¿puede quedar un proveedor que no sea de la obra para su oficio? ¿Y
si el oficio queda vacío?**

**No puede quedar.** Hay tres cerrojos:

1. `PROVEEDOR` sale solo de `par` (línea 717). `par` solo lo da
   `_par_de_r91`, sobre `opciones.proveedores`, que se construye del catálogo
   con que se ejecuta.
2. Ni el original (A, D, E, F) ni la tabla traen un proveedor. La tabla lo
   rechaza: `test_f036_forma_de_la_tabla_mal`, caso
   `update(proveedor="x")` → «sobra «proveedor»» (línea 1064 del test).
3. La ida y vuelta valida los pares contra **ese mismo** catálogo, y sin
   0 errores no hay `v2` (R56).

**Con el oficio vacío, el proveedor también queda vacío:** en la rama de
`fuera`, `opcion` y `par` se quedan en `None`. Lo comprueban
`…_r129_la_fila_sin_oficio_no_lleva_proveedor` y las M7a/M7b del implementer.
En el ensayo de hoy, las filas 105 y 106 no llevan «proveedor» en ninguna
columna.

**Límite:** R129 garantiza «de la obra **según el JSON**». Que el JSON sea del
día es procedimiento (R131, T28), no código.

**3. El informe: ¿la sección nueva escribe nombres o códigos de proveedor?**

**No.** Por código:

- la sección escribe `origen`, `n` y el nombre de oficio de la tabla, con
  `_celda`;
- la fila de recuento y la línea de órdenes, solo el número;
- `_descripcion_de`, solo el nombre del oficio.

Por datos, con un barrido de los dos informes del ensayo contra los dos JSON
(37 proveedores):

- **0 nombres** de proveedor;
- **0 códigos** entre comillas invertidas;
- **0 códigos** como palabra suelta, contando solo los que no son a la vez
  código de oficio.

`progress/migracion_F-036.md` no cambia en `540ce92..HEAD`.

**4. El ensayo en seco de T63: reproducido igual.**

- **Cómo:** sobre una copia de `git archive HEAD` en el scratchpad, con el
  `.venv` del servicio. `--solo-informe`, y `--salida`/`--informe` al
  scratchpad. Mismos JSON de `%TEMP%`, mismos grupos de `Downloads` y el
  original de OneDrive, solo leído.
- **Resultado:** las mismas salidas que pega el implementer, `rc=0` las dos
  veces. Filas sin oficio: **0** con el JSON del 2026-09-29 y **2** con el del
  2026-10-03.
- **El original:** `sha256` `4f5f1f9d…a5f1` antes y después, medido además por
  fuera.
- **Informe del 2026-09-29 frente al aceptado:** `diff` → solo el comentario de
  la cabecera y la fila de recuento nueva con 0.
- **Informe del 2026-10-03:** los recuentos de la tabla de T63 (75 / 9 / 47 /
  **2** / 47 / 1 / 12 / 47). La sección lista las filas 105 y 106, fila nueva 1,
  «V-Aire acondicionado».
- **Nada escrito** en OneDrive ni en `progress/`. Ningún `.xlsx`. Los JSON no
  se han copiado a ningún sitio.

**5. Mutación.**

- **La herramienta, recalculada** con `harness.alcance.alcance_de_feature(
  "F-036", base="b56a718")` y `generar_mutantes` (cálculo puro):
  - 2 ficheros y **126 líneas** (116 + 10), con **16 mutantes**;
  - los 16, con la misma línea, el mismo operador y el mismo texto
    original → mutado que el informe;
  - `migrar_excel_f036.py`, 0 mutantes en el alcance, y 20 sobre el fichero
    entero (prueba de control: el cero de ese fichero es legítimo, porque sus
    10 líneas son un docstring y un `print`). `migracion_f036.py`, 151 sobre
    el fichero entero.
- **Tiempo total 2.236,9 s (37 min): campaña no reejecutada**, según la regla
  de los 5 minutos. Coste por mutante = 2.236,9 × 6 ÷ 16 ≈ **839 s**, del orden
  de la suite del servicio (1.524 s con cobertura dentro de `init.sh`). No es
  sospechosa.
- **Las 23 a mano del implementer:** creíbles. No las he repetido una a una.
  Mis V3–V9, del mismo tipo, caen igual.
- **Mis mutaciones a mano**, en la copia del scratchpad. Cada una sola y
  restaurada después (`restaurado: True`). Se lanzan
  `tests/test_f036_migracion.py` y `tests/test_f036_migracion_contenido.py`
  con `-x --tb=no -p no:cacheprovider`. La base sin mutar: `236 passed`.

  | # | Mutación | rc | Primer test que la caza |
  |---|---|---|---|
  | V1 | mirar `oficios_catalogo` sin distinguir mayúsculas (`casefold`) | 1 | `…_r97_…_para[CATALOGO_SIGRID-Solados y alicatados]` |
  | **V2** | **mirar `oficios_catalogo` sin tildes (NFKD sin diacríticos, en los dos lados)** | **0** | **ninguno: 236 passed. SOBREVIVE** |
  | V3 | `strip` → `rstrip` en `nombres_de_sigrid` | 1 | `…_r128_nombres_de_sigrid_recortados_sin_nulos_ni_vacios` |
  | V4 | **orden**: un nombre de varios oficios de la obra que también es de Sigrid va a «fuera» en vez de parar | 1 | `…_r128_nombre_de_varios_oficios_de_la_obra_sigue_parando` |
  | V5 | la línea de órdenes imprime `oficios_en_grupo_de_varios` | 1 | `…_r130_la_linea_de_ordenes_lo_dice` |
  | V6 | la fila de recuento escribe `oficios_en_grupo_de_varios` | 1 | `…_r130_con_el_catalogo_de_siempre_recuento_cero_y_sin_seccion` |
  | V7 | «Oficio: — (ya no está…)» sin el nombre | 1 | `…_r130_recuento_y_seccion` |
  | V8 | nombre nulo como texto (`str(None)`) en `nombres_de_sigrid` | 1 | `…_r128_nombres_de_sigrid_recortados_sin_nulos_ni_vacios` |
  | V9 | la sección lista también las filas a las que la tabla no pone oficio | 1 | `…_r130_recuento_y_seccion` |
  | V10 | (control, código anterior al bloque) la búsqueda en la obra sin tildes | 1 | 4 tests, entre ellos `…_r128_la_obra_manda` |

- **V2 no es equivalente.** Lo comprobé con una sonda que solo existió en la
  copia, borrada después. Con `CATALOGO_SIGRID`, la tabla pone «Oficio que
  salio» (sin tilde) en la fila 2:
  - **HEAD:** para con el mensaje de la errata (`passed`);
  - **con V2:** la fila sale sin oficio y no para (`failed`).
  Pasa lo mismo con un nombre de la obra sin su tilde.
- **Orden (punto 7 del protocolo):** N/A como puerta entre colaboradores.
  - `nombres_de_sigrid` y `componer` son funciones puras;
  - `nombres_de_sigrid` va antes que `componer` porque `componer` la necesita;
  - «para sin escribir nada» no cambia en este bloque.
  El orden de **decisión** dentro de `componer` sí lo he movido: V4 aquí y M1
  del implementer. Los dos caen.

**6. Checkpoints:** abajo. T28 (repetida), T29 y T30 siguen sin marcar, a
propósito.

### Verificación ejecutada por el reviewer

| Qué | Resultado |
|---|---|
| `bash harness/init.sh` | **No relanzado.** El veredicto es CHANGES_REQUESTED por un test que falta, así que su resultado no cambia nada. El implementer lo pegó en verde sobre `9908ef2`, y `91e0a12` solo toca `progress/` y `tasks.md`. La review 11 sí tiene que lanzarlo |
| Suite de la migración en la copia de HEAD | `236 passed in 84.01s` |
| Ensayo en seco con los dos JSON | reproducido igual (punto 4) |
| Recálculo de la mutación | 126 líneas y 16 mutantes, iguales. Control: 151 y 20 sobre los ficheros enteros |
| Mutaciones a mano propias | 9 del bloque, más 1 de control: **8 de 9 caen, V2 sobrevive** |
| `ruff check` de los dos scripts y el test | `All checks passed!` |
| `ruff format --check` | `migracion_f036.py` y el test estaban formateados en `540ce92` y ya no lo están. En el script, una sola línea: `decisiones =()`, línea 892 (R10-2) |
| Barrido de lo añadido (`print(`, TODO, FIXME, claves, IPv4, GUID, `AIza`, `BEGIN … KEY`) | 0 reales. «todo» es la palabra española, y el `print(` es la línea de resumen de la línea de órdenes, que pide la spec |
| `git log --diff-filter=A 540ce92..HEAD` | solo `progress/mutacion_F-036_bloque14.md`. Ningún `.xlsx`, PDF ni JSON de catálogo |
| Árbol de trabajo | `git status --porcelain` vacío antes de escribir este informe. La copia, los guiones y los informes del ensayo están en el scratchpad |

### Checkpoints

- [x] **C1:** ficheros del arnés presentes. `init.sh` en verde según el
  implementer sobre `9908ef2`; no lo he relanzado, por el motivo de la tabla
  de arriba.
- [x] **C2:** solo F-036 está `in_progress` (F-035 está `blocked`, que es otra
  cosa). Rama correcta. `current.md` empieza por el bloque del Bloque 14.
  Ninguna `done` nueva.
- [x] **C3:**
  - Arquitectura: solo cambian scripts locales que ya importaban el dominio y
    los adaptadores. No hay imports nuevos.
  - Primera línea con la ruta: sin cambios.
  - Sin `print` de debug, TODOs ni secretos. Sin dependencias nuevas.
  - PEP8: una línea, R10-2 (menor).
  - Los puntos de partes, firmas y cierre en Sigrid son N/A, con el motivo de
    la review 1: esto es el script local de migración, sin escritura en Sigrid
    ni archivo.
- N/A · **C3 bis:** no entra nada en `docs/referencia/` ni en `docs/`.
- [x] **C4:** cada requisito tiene tests en verde (tabla de abajo), sin red ni
  base de datos. R131 es MANUAL, con la orden exacta en la enmienda de T28 de
  `tasks.md` y anotada como pendiente en `current.md`.
- [ ] **C4 bis:**
  - `rigor: "critico"`.
  - **Fase RED**, con salida real: `36 failed, 166 passed`. Los 2 que nacen en
    verde están justificados (invariantes).
  - **Cobertura:** `[OK]` 99,9 %.
  - **Herramienta:** 16 de 16, recalculada.
  - **Evidencias:** la sección está, con los cuatro números y los workers.
  - **Cero supervivientes a mano: NO.** V2 sobrevive y no es equivalente
    (R10-1).
- N/A · **C4 ter:** no existe `harness/rutas_sensibles.json`.
- [x] **C5:**
  - T61–T64 `[x]`, con commits `F-036 T61` … `F-036 T64`.
  - T28 (repetida), T29 y T30 siguen abiertas, a propósito.
  - Sin ficheros sin trackear.

### Cobertura: requisito → test (lo nuevo)

| Requisito | Tests |
|---|---|
| R97 (enmendado) | `test_f036_r97_nombre_que_no_es_exactamente_uno_de_la_obra_para` (12 casos), `…_r97_errata_y_fuera_de_la_obra_a_la_vez`. **Falta la errata de tilde (R10-1)** |
| R128 | `…_r128_oficio_que_ya_no_esta_en_la_obra_queda_vacio`, `…_el_v2_vuelve_con_cero_errores_y_la_fila_sin_oficio`, `…_el_nombre_de_sigrid_se_compara_recortado`, `…_nombres_de_sigrid_recortados_sin_nulos_ni_vacios`, `…_la_obra_manda`, `…_nombre_de_varios_oficios_de_la_obra_sigue_parando`, `test_f036_catalogo_mal_formado` (9 casos nuevos) |
| R129 | `…_r129_el_proveedor_es_el_del_catalogo_con_que_se_ejecuta`, `…_r129_la_fila_sin_oficio_no_lleva_proveedor`, `test_f036_forma_de_la_tabla_mal` (caso `proveedor`) |
| R130 | `…_r130_con_el_catalogo_de_siempre_recuento_cero_y_sin_seccion`, `…_recuento_y_seccion`, `…_varias_filas_y_su_numero_dentro_de_la_original`, `…_el_nombre_de_la_seccion_se_escapa`, `…_la_linea_de_ordenes_lo_dice`, `…_sin_proveedores_en_el_informe` |
| R131 | `…_r131_un_v2_de_otro_catalogo_da_errores_y_el_regenerado_no`, más T28 y T29 (MANUAL) |

### Hallazgos

1. **R10-1 · [Bloqueante] La comparación exacta frente a `oficios_catalogo` no
   está fijada en cuanto a las tildes.**
   - V2 sobrevive con `236 passed`.
   - R128 dice «mayúsculas, tildes y puntuación, tal cual».
   - Es justo el riesgo real: 7 pares de gemelos de tilde en `auxofc`, y 5 de
     los 12 nombres de la tabla tienen uno.
   - Hoy, los casos de errata de `test_f036_r128_el_nombre_de_sigrid_se_compara_recortado`
     (líneas 1983–1988) cubren blancos y mayúsculas, pero ninguna tilde.
2. **R10-2 · [Menor] PEP8 en una línea nueva.** `migracion_f036.py:892`
   `decisiones =() if grupos …` (E225). La introdujo `e1a15a7`; el fichero
   salía limpio de `ruff format --check` en `540ce92`. Al test le pasa lo
   mismo (líneas largas en `CATALOGO_SIGRID`, el `parametrize` de R97 y
   `LINEA_DE_ORDENES`). El repositorio no exige `ruff format` (134 ficheros
   del servicio sin formatear), así que solo pido la línea de producción.
3. **R10-3 · [Para el humano] La sección de R130 no distingue «ha salido» de
   «errata de tilde con gemelo en `auxofc`»** (punto 1). No es un defecto de
   la implementación, que sigue la decisión 7 (nada de casado aproximado).
   Pero el criterio (a) de T28 acepta la sección en bloque. Ver «Qué queda».
4. **R10-4 · [Informativo] Los «7 grupos de nombres iguales» del catálogo
   global no son nombres iguales:** son pares que solo difieren en la tilde.
   En `auxofc` no hay ningún nombre repetido exacto en ninguno de los dos JSON.
   Si algún documento lo cuenta como «nombres repetidos», conviene corregirlo.

### Cambios requeridos

1. **R10-1.** En `services/postventa-api/tests/test_f036_migracion.py`,
   `test_f036_r128_el_nombre_de_sigrid_se_compara_recortado`: añadir a la
   tupla de las líneas 1983–1988 el nombre **sin tilde** de
   `FUERA_DE_LA_OBRA`, `"Oficio que salio"`. Opcional: también un nombre de
   la obra de `CATALOGO` sin su tilde, con `CATALOGO_SIGRID`.
   - **Lo que se espera:** los dos paran con `_errata(2, 1, nombre)`.
   - **Esto está ejecutado, no es orientativo:** en una copia, con una sonda
     de esa forma, HEAD → `passed` y V2 → `failed`.
   - **Evidencia que hay que pegar en el informe:** V2, aplicada en una copia,
     en rojo con el test nuevo, y el fichero en verde sobre el código de
     siempre.
   - **No cambia producción.**
2. **R10-2.** `services/postventa-api/scripts/migracion_f036.py:892`:
   `decisiones =()` → `decisiones = ()`. Es solo un espacio: no cambia el AST
   ni los mutantes. Basta con volver a pasar los dos ficheros de tests de la
   migración.
3. **Para la review 11:** `bash harness/init.sh` en verde tras los dos
   cambios.

### Lo que no he hecho, dicho

- No he relanzado `init.sh`, por el motivo de la tabla de verificación.
- No he relanzado la campaña de la herramienta (37 min > 5): solo el
  recálculo puro con su control.
- No he repetido una a una las 23 mutaciones a mano del implementer.
- No he leído Sigrid ni he descargado grupos. El ensayo usa los JSON que ya
  había fuera del repositorio.

### Qué queda para el humano

- **Decidir sobre R10-3** antes de la T28 otra vez. Hay dos opciones:
  - **(a) Solo procedimiento:** en T28, por cada nombre de la sección
    «Filas sin oficio…», comprobar que la obra de ese día no tiene un oficio
    con el mismo nombre salvo tildes o mayúsculas. Si lo tiene, es una errata
    de la tabla: se corrige el YAML. Con los datos de hoy, el único nombre es
    «V-Aire acondicionado», y no tiene ningún gemelo.
  - **(b) Una columna informativa en la sección**, con una enmienda de spec:
    «en la obra hay un oficio que solo difiere en tildes o mayúsculas: sí/no»,
    sin resolver nada. No rompe la decisión 7, porque no casa: avisa.
- **Las cuatro decisiones del spec-author** de la undécima enmienda siguen
  abiertas (`current.md`).
- **T28 otra vez**, con los grupos descargados ese mismo día (el fichero a
  mano es del 2026-10-02), **T29 pasos 4–7** y **T30**, después de la
  review 11.

### Automejora (propuesta, no aplicada)

- **`.claude/agents/reviewer.md`, punto 4 de «Validación contra el nivel de
  rigor».** Vale para `arnes-base`.
  - **Qué añadir:** cuando una feature distinga por **pertenencia exacta de un
    texto a un conjunto** (nombres, códigos), el reviewer aplica a mano al
    menos tres mutaciones de normalización sobre esa comparación: mayúsculas,
    tildes (NFKD sin diacríticos) y blancos. Y busca en los datos reales pares
    que solo difieran en eso.
  - **Por qué:** `harness.mutacion` no tiene operadores de normalización de
    texto. En esta review, la única que sobrevivió (V2) es de ese tipo, y el
    implementer cubrió blancos y mayúsculas pero no tildes. El catálogo real
    tenía 7 pares de gemelos de tilde.

## Review 11 (reviewer, 2026-10-03)

- **Veredicto:** CHANGES_REQUESTED
- **Rama:** `feature/F-036-importar-excel`, HEAD `75cf2f2`. Review **corta**,
  acotada a `git diff 9a2aba4..HEAD`:
  - `0097a6e` (R10-1, solo test);
  - `9e7f308` (R10-2, un espacio);
  - `21ee114` y `75cf2f2` (informe y estado).
- **Nivel de rigor:** `critico`, declarado en `harness/features.json`. Exige
  fase RED, cobertura, mutación con cero supervivientes sin justificación
  aceptada por el humano (también a mano) y MANUAL listadas.

### Resumen para el líder

- **R10-1 y R10-2, cerrados.** Lo he verificado yo:
  - V2 cae con el test nuevo;
  - el script solo cambia en el espacio;
  - la suite de la migración está en verde sobre HEAD.
- **Rechazo por dos supervivientes nuevos de la misma familia que V2.** Salen
  de las variantes que me pediste:
  - **V2f:** comparar con `oficios_catalogo` sin puntuación. R128 dice
    «mayúsculas, tildes y **puntuación**, tal cual».
  - **V2g:** compararlo en NFC.
- **Mea culpa.** En la review 10 solo probé mayúsculas, tildes y blancos.
  Debí probar también la puntuación, que R128 nombra en la misma frase.
- **Se arregla igual que R10-1:** dos nombres más en la misma tupla del mismo
  test. No cambia producción, no hay que relanzar la campaña de la herramienta
  ni repetir T63.
- **R10-3:** nada impide la opción (a). Hay un matiz de redacción, más abajo.

### R10-1 y R10-2

**R10-1, cerrado.**

- **El cambio:** la tupla de `test_f036_r128_el_nombre_de_sigrid_se_compara_recortado`
  suma «Oficio que salio» y «Albañileria». Los dos son de `CATALOGO_SIGRID`
  y esperan `_errata(2, 1, nombre)`.
- **«Albañileria» es una buena elección:**
  - la obra de `CATALOGO` tiene «Albañilería» (0020), así que es el gemelo de
    tilde real de `auxofc`;
  - con V2, el nombre plegado casa con `nombres_sigrid` y la fila se iría a
    «fuera»;
  - no se usa «Fontaneria» porque en `CATALOGO` es un oficio de la obra, 0160.
- **Repetido en una copia desechable** de `git archive HEAD` (el repositorio
  entero) en el scratchpad, con el `.venv` del servicio. Ver la tabla de
  mutaciones: V2 da `1 failed, 188 passed` con `-x`, y lo caza justo ese test.
- **La evidencia del implementer es creíble:** `1 failed, 235 passed` con V2;
  `236 passed` con el test de `9a2aba4`.

**R10-2, cerrado.**

- `git diff 9a2aba4 HEAD -- services/postventa-api/scripts/migracion_f036.py`
  es **una sola línea**, la 892: `decisiones =()` → `decisiones = ()`.
- `ruff format --check` → `1 file already formatted`.
- **Alcance del diff:** solo cambian 4 ficheros: el script, el test,
  `progress/impl_F-036.md` y `progress/current.md`.

**El `I001` que cita el implementer** (orden de imports del test) es previo y
no está en este diff. Depende de la raíz desde la que se lanza `ruff`:
- desde la raíz del repositorio → `All checks passed!`;
- desde `services/postventa-api` → `I001`.
No lo pido.

### Mutaciones a mano (en la copia, cada una sola y restaurada)

Mismo método que en la review 10:
- se lanzan `tests/test_f036_migracion.py` y
  `tests/test_f036_migracion_contenido.py` con
  `-x --tb=no -p no:cacheprovider`;
- **base sin mutar:** `236 passed`;
- tras la última mutación, `restaurado: True`.

> **Una nota de método:** en el primer intento extraje solo
> `services/postventa-api`. Los tests de `…_contenido.py` leen ficheros de
> fuera de esa carpeta, así que la base salió en rojo y esa tanda no vale. La
> rehice con `git archive HEAD` entero. Todas las cifras de abajo son de la
> segunda tanda, con la base en verde.

| # | Mutación | rc | Primer test que la caza |
|---|---|---|---|
| V2 | (review 10) `oficios_catalogo` sin tildes, en los dos lados | 1 | `…_r128_el_nombre_de_sigrid_se_compara_recortado` |
| V2b | sin tildes ni mayúsculas, en los dos lados | 1 | `…_r97_…_para[CATALOGO_SIGRID-Solados y alicatados]` |
| V2c | solo la tabla, sin tildes | 1 | `…_r128_oficio_que_ya_no_esta_en_la_obra_queda_vacio` |
| V2d | al conjunto de Sigrid se le suma su forma sin tildes | 1 | `…_r128_el_nombre_de_sigrid_se_compara_recortado` |
| V2e | al conjunto de Sigrid se le suma su forma en minúsculas | 1 | `…_r97_…_para[CATALOGO_SIGRID-pintura]` |
| **V2f** | **`oficios_catalogo` sin puntuación (`[^\w\s]`), en los dos lados** | **0** | **ninguno: 236 passed. SOBREVIVE** |
| **V2g** | **`oficios_catalogo` en NFC, en los dos lados** | **0** | **ninguno: 236 passed. SOBREVIVE** |
| V11 | la obra, buscada sin mayúsculas (las claves en `casefold`) | 1 | `…_r55_r56_camino_bueno_con_grupos` |
| V11b | la obra, buscada sin mayúsculas solo por el lado de la tabla (se prueba primero `casefold` y, si no, el nombre exacto) | 0 | ninguno. **Equivalente en la práctica**, ver abajo |
| V12 | la obra, buscada sin tildes ni mayúsculas, en los dos lados | 1 | `…_r97_…_para[CATALOGO-Solados y alicatados]` |

**V2f no es equivalente.** Lo probé con una sonda, solo en la copia y
restaurada después: «Solados y Alicatados MO» en la tupla, con
`CATALOGO_SIGRID`, que en la obra tiene «Solados y Alicatados M.O.».
- **HEAD:** para con la errata (`1 passed`).
- **V2f:** no para; la fila sale sin oficio (`1 failed`).

**V2g no es equivalente.** Sonda: `unicodedata.normalize("NFD",
FUERA_DE_LA_OBRA)` en la tupla.
- **HEAD:** para (`1 passed`).
- **V2g:** no para (`1 failed`).

**V11b es equivalente en la práctica.** Solo se distingue del código si la
obra tiene un nombre **todo en minúsculas**. Hay 0 en los dos JSON reales,
tanto en la obra como en `auxofc`, y ninguno en los catálogos de los tests.
La mutación completa (V11, y V12 con tildes) cae.

**Datos reales**, medidos con `catalogo_0677.json` y
`catalogo_0677_20261003.json` de `%TEMP%`. Solo nombres de oficio y
recuentos; ningún proveedor.
- **Puntuación:** 25 nombres de `auxofc` la llevan. En la obra, del
  2026-10-03: «Solados y Alicatados M.O.», «V-Cerrajería metálica»,
  «V-Electricidad» y «V-Pintura».
- **Gemelos que solo difieren en la puntuación:** hoy **ninguno**. El riesgo
  real es menor que el de las tildes, pero R128 nombra la puntuación
  expresamente y el mutante no es equivalente.
- **Nombres que no están en NFC:** 0.

### R10-3 (opción (a), solo procedimiento)

**No veo nada que la impida.** Basta con anotarla. Dos matices para cuando
se escriba en T28:

1. **Contra qué se compara.** Hay que comparar contra los oficios **de la
   obra** (`oficios_obra` del JSON del día), no contra `auxofc`. Todo nombre
   de la sección está en `auxofc` por definición, así que mirar ahí no
   detecta nada.
2. **Qué diferencias se buscan:** tildes, mayúsculas, blancos y también
   **puntuación**. Por ejemplo, «V Pintura» frente a «V-Pintura».

**Dónde dejarlo escrito.** Conviene que quede en el texto de T28 de
`tasks.md`, junto al criterio (a) de «Diferencias esperables». Si solo lo
recuerda el líder, ese criterio sigue aceptando la sección en bloque.

### Verificación ejecutada por el reviewer

| Qué | Resultado |
|---|---|
| `bash harness/init.sh` | **Verde** (`ENTORNO LISTO`). Raíz: `62 passed`. La suite de `api` sale de **caché**: el árbol de `services/postventa-api` en HEAD (`52c46ee`) es idéntico al de `9e7f308`, donde el implementer sacó `6628 passed, 74 skipped`, y lo he comprobado con `git rev-parse`. `PUERTA COBERTURA [OK]` 99,9 % (3314/3318) |
| Suite de la migración en el árbol real de HEAD | `236 passed in 50.57s` |
| Suite de la migración en la copia de HEAD | `236 passed in 52.51s` |
| Mutaciones a mano | 10 mutaciones: 7 caen, **V2f y V2g sobreviven** y V11b es equivalente en la práctica |
| `ruff format --check` del script | limpio |
| `ruff check` del script y el test, desde la raíz | `All checks passed!` |
| Barrido de lo añadido | sin `print`, TODO, secretos ni `repr` de `Ajustes`. Ningún fichero añadido |
| Árbol de trabajo | `git status --porcelain` vacío antes de escribir este informe. La copia y los guiones están en el scratchpad |

### Checkpoints

- [x] **C1:** `init.sh` en verde. La suite de `api` sale de la caché del
  mismo árbol, comprobado arriba.
- [x] **C2:** solo F-036 está `in_progress`. Rama correcta. `current.md`
  empieza por el bloque de los arreglos de la review 10. Ninguna `done` nueva.
- [x] **C3:**
  - R10-2 resuelto. No hay imports ni dependencias nuevas.
  - Primera línea con la ruta: sin cambios.
  - Los puntos de partes, firmas y cierre en Sigrid son N/A, con el motivo de
    la review 1 (script local de migración).
- N/A · **C3 bis:** no entra nada en `docs/`.
- [x] **C4:** los tests de R128 y R97 siguen en verde, sin red ni base de
  datos.
- [ ] **C4 bis:**
  - **Fase RED** de R10-1: real, con la salida de V2 en rojo.
  - **Cobertura:** `[OK]` 99,9 %.
  - **Herramienta:** sin cambios desde T64 (16/16). R10-2 no cambia el AST.
  - **Evidencias:** la sección está, con los números.
  - **Cero supervivientes a mano: NO.** V2f y V2g sobreviven y no son
    equivalentes (R11-1, R11-2).
- N/A · **C4 ter:** no existe `harness/rutas_sensibles.json`.
- [x] **C5:**
  - commits `F-036 R10-1` y `F-036 R10-2`, uno por cambio;
  - no hay tareas nuevas en `tasks.md`;
  - T28 (otra vez), T29 y T30 siguen abiertas, a propósito.

### Cobertura: requisito → test (lo que cambia)

| Requisito | Tests |
|---|---|
| R128 / R97: la comparación con `oficios_catalogo` es exacta | `test_f036_r128_el_nombre_de_sigrid_se_compara_recortado`: blancos, mayúsculas y **tildes**, desde R10-1. **Falta la puntuación (R11-1) y la forma Unicode (R11-2)** |

### Hallazgos

1. **R11-1 · [Bloqueante] La puntuación no está fijada en la comparación con
   `oficios_catalogo`.**
   - V2f sobrevive con `236 passed`.
   - R128 dice «mayúsculas, tildes y puntuación, tal cual». Es el mismo caso
     que R10-1, con la tercera palabra de la frase.
2. **R11-2 · [Bloqueante en `critico`, salvo que el humano acepte la
   justificación] La forma Unicode no está fijada.**
   - V2g (NFC) sobrevive.
   - **Hoy no muerde:** 0 nombres que no estén en NFC en los dos JSON.
   - Pero el código compara «tal cual», código a código, y nada lo fija.
3. **R11-3 · [Informativo] V11b es equivalente en la práctica** (ver arriba).
   No pido nada. Si el humano quiere, se cierra igual que R11-2.

### Cambios requeridos

1. **R11-1.** En `services/postventa-api/tests/test_f036_migracion.py`,
   `test_f036_r128_el_nombre_de_sigrid_se_compara_recortado`: añadir a la
   tupla (la que empieza en la línea 1985) `"Solados y Alicatados MO"`.
   - **Por qué ese nombre:** es «Solados y Alicatados M.O.» (0133, de la
     obra en `CATALOGO`) sin los puntos.
   - **Lo que se espera:** `_errata(2, 1, nombre)`.
   - **Está ejecutado, no es orientativo:** HEAD → `passed`; V2f → `failed`.
2. **R11-2.** En la misma tupla, añadir
   `unicodedata.normalize("NFD", FUERA_DE_LA_OBRA)` (con su `import
   unicodedata`), esperando también `_errata`.
   - **Está ejecutado:** HEAD → `passed`; V2g → `failed`.
   - **Alternativa:** que el humano acepte por escrito el superviviente V2g,
     con el motivo de que hoy hay 0 nombres que no estén en NFC.
   - **Mi recomendación:** el test. Son dos líneas y deja fijado lo que dice
     R128.
3. **Evidencia que hay que pegar en el informe:**
   - V2f y V2g, cada una aplicada en una copia desechable, en rojo con el test
     nuevo;
   - el fichero en verde sobre el código de siempre;
   - el comentario del bucle, que diga también «puntuación».
   - **No cambia producción.** No hace falta relanzar la campaña de la
     herramienta ni repetir T63.
4. **Para la review 12:** `init.sh` en verde. Solo cambia un test, así que la
   suite de `api` se relanza sola: el árbol cambia y la caché ya no vale.

### Lo que no he hecho, dicho

- **La suite completa de `api`:** no la he relanzado fuera de la caché de
  `init.sh` (el motivo, en la tabla de verificación). Sí he lanzado los dos
  ficheros de la migración.
- **La campaña de la herramienta:** no la he relanzado. El AST no cambia
  desde T64.
- **Sigrid:** no lo he leído. Los datos son los dos JSON que ya estaban en
  `%TEMP%`, solo leídos.

### Automejora (corrige la propuesta de la review 10, no aplicada)

- **`.claude/agents/reviewer.md`, punto 4.** Vale para `arnes-base`. La
  propuesta de la review 10 decía «mayúsculas, tildes (NFKD sin diacríticos)
  y blancos».
- **Cómo debe quedar:** cuando el requisito enumere qué se compara «tal
  cual», el reviewer aplica a mano **una mutación de normalización por cada
  palabra de esa enumeración**: mayúsculas, tildes, puntuación, blancos
  interiores y por los extremos. Y otra más de **forma Unicode (NFC/NFD)**.
  Cada una, en los dos lados y en uno solo.
- **Por qué:** la propuesta anterior se dejó la puntuación, que R128 nombra en
  la misma frase que las tildes. Ha costado una vuelta más de review.

## Review 12 (reviewer, 2026-10-03)

- **Veredicto:** CHANGES_REQUESTED
- **Rama:** `feature/F-036-importar-excel`, HEAD `c405227`. Review **corta**
  (tercera vuelta, autorizada expresamente por el humano), acotada a
  `git diff 50df9e6..HEAD`:
  - `0ac4832` (R11-1, solo test);
  - `073847e` (R11-2, solo test);
  - `e6aebba` (R10-3 opción (a), texto de T28);
  - `c405227` (informe).
- **Nivel de rigor:** `critico`, declarado en `harness/features.json`. Exige
  fase RED, cobertura, mutación con cero supervivientes sin justificación
  aceptada por el humano (también los de a mano) y MANUAL listadas.

### Resumen para el líder

- **R11-1 y R11-2, cerrados.** Lo he repetido yo en copias desechables de
  `git archive HEAD` del repo entero:
  - la base da `236 passed`;
  - V2f (sin puntuación `[^\w\s]`, en los dos lados) da `1 failed`;
  - V2g (NFC, en los dos lados) da `1 failed`;
  - las dos las caza `test_f036_r128_el_nombre_de_sigrid_se_compara_recortado`.
- **R10-3 (a), bien escrito.** El texto de T28 recoge los dos matices:
  - compara contra `oficios_obra`, no contra `auxofc`, y da el motivo;
  - busca tildes, mayúsculas, blancos y puntuación.
- **`git diff 50df9e6 HEAD -- services/postventa-api/scripts/`:** vacío.
- **`init.sh`:** en verde. Cobertura `[OK]` 99,9 %.
- **Rechazo.** La familia completa de mi automejora deja **29 supervivientes
  no equivalentes**:
  - **10** en la comparación con `oficios_catalogo` (R128);
  - **19** en la búsqueda en los oficios de la obra (R97).
- **Los otros 20 supervivientes son equivalentes:** 4 por construcción y 16 en
  la práctica. Van en una lista para que el humano los acepte en bloque.
- **Se arregla con un solo cambio de test, sin tocar producción:** ocho
  nombres más en la parametrización de
  `test_f036_r97_nombre_que_no_es_exactamente_uno_de_la_obra_para`. Está
  ejecutado: con `CATALOGO_SIGRID` matan los 29.
- **Mea culpa.** En las reviews 10 y 11 probé la familia a trozos: los dos
  lados y la «suma» por el lado de Sigrid. Hoy la he pasado entera, y salen
  las variantes que no había probado. Aparecen tres huecos:
  - el lado único **tolerante** (como V11b, pero con otras palabras);
  - la puntuación cambiada por **espacio**: es justo el ejemplo de T28,
    «V Pintura» frente a «V-Pintura»;
  - los **blancos interiores**.
- **La alternativa** es que el humano acepte los 29 por escrito. No la
  recomiendo: dos de ellos son los casos reales que motivaron R10-1 y R10-3.

### R11-1 y R11-2

**El diff.** Coincide con lo que pedí en la review 11:

- la tupla suma `"Solados y Alicatados MO"` y
  `unicodedata.normalize("NFD", FUERA_DE_LA_OBRA)`;
- `import unicodedata` en el bloque de la biblioteca estándar;
- el comentario dice ya «puntuación o forma Unicode».

`ruff check` del test, desde la raíz: `All checks passed!`. El barrido de lo
añadido sale limpio: sin `print`, TODO, secretos ni `repr` de `Ajustes`.

**Verificación propia:**

- `git archive HEAD` (`c405227`, el repo entero) extraído en diez copias del
  scratchpad, con el `.venv` del servicio real.
- He comprobado que `scripts.migracion_f036` se importa **de la copia**.
- Cada mutación va **sola**: se aplica, se lanzan
  `tests/test_f036_migracion.py` y `tests/test_f036_migracion_contenido.py`
  con `-x --tb=no -q -p no:cacheprovider`, y se restaura. Tras cada una,
  `restaurado: True`, comprobado por el guion.
- Del resultado solo se guarda el nombre del test que cae, nunca el mensaje,
  así que no hay ningún `repr`.

| Mutación | rc | Resultado | Primer test que la caza |
|---|---|---|---|
| Base sin mutar | 0 | `236 passed` | — |
| **V2f**: `oficios_catalogo` sin puntuación (`[^\w\s]`), en los dos lados | 1 | `1 failed, 188 passed` | `…_r128_el_nombre_de_sigrid_se_compara_recortado` |
| **V2g**: `oficios_catalogo` en NFC, en los dos lados | 1 | `1 failed, 188 passed` | `…_r128_el_nombre_de_sigrid_se_compara_recortado` |

La regex y la normalización son las mismas del informe del implementer. Su
evidencia (V2f y V2g en verde con el test de `50df9e6`, en rojo con el nuevo)
es coherente con la mía.

### La familia completa (automejora de la review 11)

**Dónde se muta.** Hay dos comparaciones «tal cual» en `componer`
(`services/postventa-api/scripts/migracion_f036.py`):

- **S, R128:** la línea 695, `nueva.oficio not in nombres_sigrid`;
- **O, R97:** las líneas 672 y 686, `codigos_de`, la búsqueda en los oficios
  de la obra.

**Las normalizaciones `f`.** Una por cada palabra de la enumeración, más la
forma Unicode:

- `mayus`: `casefold`;
- `tildes`: NFKD sin diacríticos, **incluida la ñ**;
- `tildes_sin_enie`: lo mismo, pero respetando la ñ;
- `punt`: quitar `[^\w\s]`;
- `punt_esp`: cambiar `[^\w\s]` por espacio;
- `blancos_int`: colapsar `\s+`;
- `blancos_todos`: quitar todo blanco;
- `extremos`: `strip`;
- `nfc`, `nfd` y `nfkc`.

**Las cinco formas de cada lado.** Para S:

- **ambos:** `f(tabla)` frente a `{f(s)}`;
- **tabla:** `f(tabla)` frente a S;
- **tabla-tolerante:** se prueba el exacto y, si no, `f(tabla)`. Es la forma
  de V11b;
- **sigrid-suma:** S más `{f(s)}`;
- **sigrid:** solo `{f(s)}`.

Para O son las mismas, con las claves de `codigos_de`.

**Dos más:** quitar el `strip` del lado de Sigrid (552) y quitar el del lado
de la obra (672).

**Total: 112 mutantes.** Caen 63 y sobreviven 49. Las dos de `strip` caen.

Matriz de supervivientes (`VIVO`). La columna de `tildes_sin_enie` se lanzó
aparte, con el mismo método:

| | mayus | tildes | sin ñ | punt | punt_esp | bl. int | bl. todos | extremos | nfc | nfd | nfkc |
|---|---|---|---|---|---|---|---|---|---|---|---|
| S-ambos | cae | cae | cae | cae | **VIVO** | **VIVO** | cae | cae | cae | cae | cae |
| S-tabla | cae | cae | cae | cae | cae | **VIVO** | cae | cae | cae | cae | cae |
| S-tabla-tolerante | eq | **VIVO** | **VIVO** | **VIVO** | **VIVO** | **VIVO** | cae | cae | cae | eq | cae |
| S-sigrid-suma | cae | cae | cae | cae | **VIVO** | eq | **VIVO** | eq | eq | cae | eq |
| S-sigrid | cae | cae | cae | cae | cae | eq | cae | eq | eq | cae | eq |
| O-ambos | cae | cae | cae | cae | **VIVO** | **VIVO** | cae | cae | **VIVO** | **VIVO** | **VIVO** |
| O-tabla | cae | cae | cae | cae | cae | **VIVO** | cae | cae | **VIVO** | cae | **VIVO** |
| O-tabla-tolerante | eq (V11b) | **VIVO** | **VIVO** | **VIVO** | **VIVO** | **VIVO** | cae | cae | **VIVO** | eq | **VIVO** |
| O-obra-suma | cae | **VIVO** | cae | cae | **VIVO** | eq | **VIVO** | eq | eq | **VIVO** | eq |
| O-obra | cae | cae | cae | cae | cae | eq | cae | eq | eq | cae | eq |

`eq` es un superviviente equivalente; abajo, el motivo de cada uno.

**Por qué los `VIVO` no son equivalentes.** En los dos JSON reales (solo nombres
y recuentos, ningún proveedor) hay:

- 25 nombres de `auxofc` con puntuación;
- en la obra del 2026-10-03, «V-Pintura», «V-Electricidad»,
  «V-Cerrajería metálica» y «Solados y Alicatados M.O.»;
- 85 nombres de `auxofc` sin tildes;
- 7 grupos de gemelos que solo difieren en las tildes.

Cada `VIVO` acepta en silencio un nombre de la tabla que no es exactamente el
de Sigrid. Lo he comprobado con una sonda: el original para con la errata
literal y el mutante no.

Los dos más serios:

- **S/O-tabla-tolerante/tildes:** una tabla con «Píntura» (o un gemelo de
  tilde de un nombre de `auxofc` sin tilde) sale «fuera de la obra», o se
  resuelve a «Pintura», en vez de parar. Es la familia de R10-1.
- **S/O-ambos/punt_esp y S-sigrid-suma/punt_esp:** una tabla con «V Pintura»
  casa con «V-Pintura». Es el ejemplo literal que T28 manda buscar a mano.

**Los 20 equivalentes, para aceptarlos en bloque:**

1. **Por construcción (4):** S-sigrid/extremos, S-sigrid-suma/extremos,
   O-obra/extremos y O-obra-suma/extremos. El lado del catálogo ya está
   recortado: `nombres_de_sigrid` (552) y `codigos_de` (672). `strip` es la
   identidad ahí.
2. **En la práctica, por el lado del catálogo (12):** {S-sigrid,
   S-sigrid-suma, O-obra, O-obra-suma} × {blancos_int, nfc, nfkc}. Solo
   transforman nombres de Sigrid, y en los dos JSON reales (`auxofc` 130 y
   133, obra 31 y 36) hay:
   - 0 nombres con blancos dobles;
   - 0 nombres que no estén en NFC;
   - 0 nombres que no estén en NFKC;
   - 0 blancos que no sean el espacio.
3. **En la práctica, tolerantes que necesitan un nombre raro en Sigrid (4):**
   - S-tabla-tolerante/mayus y O-tabla-tolerante/mayus (= **V11b**, R11-3):
     solo se distinguen si hay un nombre todo en minúsculas; hay 0;
   - S-tabla-tolerante/nfd y O-tabla-tolerante/nfd: solo se distinguen si
     hay un nombre en NFD; hay 0.

**Una sonda que no los distingue confirma la clasificación.** Ninguno de los
ocho nombres de la corrección mata a uno solo de los 20, y matan a los 29
`VIVO`.

### R10-3 (opción (a), texto de T28)

`specs/F-036-importar-excel/tasks.md`, T28, criterio (a). **Recoge los dos
matices:**

1. **Contra qué compara:** «`oficios_obra` del JSON del paso 2, **no**
   `auxofc`», con el motivo. Que el paso 2 es el del catálogo lo confirma el
   paso 3 de la misma T28. `oficios_obra` es la clave real del JSON: la usa
   `migracion_f036.py:507`.
2. **Qué diferencias busca:** «tildes, mayúsculas, blancos o puntuación», con
   el ejemplo «V Pintura» frente a «V-Pintura».

Además dice qué hacer si encuentra un gemelo: corregir el YAML y relanzar la
migración antes de aceptar. **No pido nada.** Que no hable de la forma
Unicode es correcto: a ojo no se ve, y para eso está el test.

### Verificación ejecutada por el reviewer

| Qué | Resultado |
|---|---|
| `bash harness/init.sh`, tal cual | **Verde** (`ENTORNO LISTO`). Raíz `62 passed`. Las suites de `api` y `front` salen de **caché**: `git rev-parse` de `services/postventa-api` es igual en `e6aebba` y HEAD (`8a312b0`), y en `e6aebba` el implementer sacó `6628 passed, 74 skipped`, relanzada. `PUERTA COBERTURA [OK]` 99,9 % (3314/3318) |
| `git diff 50df9e6 HEAD -- services/postventa-api/scripts/` | vacío |
| Los dos ficheros de la migración en la copia de HEAD | `236 passed` |
| V2f y V2g, cada una sola | `1 failed, 188 passed`, las dos por el test de R128 |
| Familia completa | 112 mutantes: 63 caen, 29 `VIVO` no equivalentes y 20 equivalentes |
| Sonda de los ocho nombres propuestos | con `CATALOGO_SIGRID`, en la fila 0 (como el test de R97) y en la fila 1 (como el de R128), matan los 29. Con `CATALOGO` matan los 19 de la obra. Sin mutar, los ocho paran con la errata literal en los dos catálogos |
| `ruff check` del test, desde la raíz | `All checks passed!` |
| Árbol de trabajo | `git status --porcelain` vacío antes de escribir este informe. Copias, guiones y resultados, solo en el scratchpad |

### Checkpoints

- [x] **C1:** `init.sh` en verde. La suite de `api` sale de la caché del mismo
  árbol, comprobado arriba.
- [x] **C2:**
  - solo F-036 está `in_progress`, y la rama es la correcta;
  - `current.md` empieza por el bloque de los arreglos de la review 11;
  - no hay ninguna `done` nueva.
- [x] **C3:**
  - solo cambia un test; el `import` nuevo es de la biblioteca estándar;
  - primera línea con la ruta: sin cambios;
  - los puntos de partes, firmas y cierre en Sigrid son N/A, con el motivo de
    la review 1 (script local de migración).
- N/A · **C3 bis:** no entra nada en `docs/`.
- [x] **C4:** los tests de R128 y R97 están en verde, sin red ni base de
  datos.
- [ ] **C4 bis:**
  - **Fase RED** de R11-1 y R11-2: real (V2f y V2g en rojo con el test nuevo,
    en verde con el viejo).
  - **Cobertura:** `[OK]` 99,9 %.
  - **Herramienta:** sin cambios desde T64 (16/16). No cambia producción.
  - **Evidencias:** la sección está.
  - **Cero supervivientes a mano: NO.** Quedan 29 no equivalentes (R12-1).
- N/A · **C4 ter:** no existe `harness/rutas_sensibles.json`.
- [x] **C5:**
  - commits `F-036 R11-1`, `F-036 R11-2` y `F-036 R10-3`, uno por cambio;
  - T28 (otra vez), T29 y T30 siguen abiertas, a propósito.

### Cobertura: requisito → test (lo que cambia)

| Requisito | Tests |
|---|---|
| R128: la comparación con `oficios_catalogo` es exacta | `test_f036_r128_el_nombre_de_sigrid_se_compara_recortado`: blancos extremos, mayúsculas, tildes, puntuación quitada y NFD. **Faltan** blancos interiores, puntuación cambiada por espacio y los lados únicos tolerante y suma (R12-1) |
| R97: la búsqueda en la obra es exacta | `test_f036_r97_nombre_que_no_es_exactamente_uno_de_la_obra_para`: extremos, mayúsculas, etiqueta y nombre inexistente. **Faltan** tildes por el lado tolerante, puntuación, blancos interiores y forma Unicode (R12-1) |

### Hallazgos

1. **R12-1 · [Bloqueante en `critico`, salvo que el humano acepte] 29
   supervivientes no equivalentes** de la familia de normalización: 10 en R128
   y 19 en R97. Están en la matriz de arriba.
2. **R12-2 · [Informativo] 20 equivalentes**, 4 por construcción y 16 en la
   práctica. V11b (R11-3) es uno de ellos. Se piden aceptados en bloque.
3. **R12-3 · [Informativo]** R11-1, R11-2 y R10-3 (a), cerrados.

### Cambios requeridos

1. **R12-1.** En `services/postventa-api/tests/test_f036_migracion.py`, en la
   lista de `@pytest.mark.parametrize("nombre", [...])` de
   `test_f036_r97_nombre_que_no_es_exactamente_uno_de_la_obra_para` (líneas
   534–544), añadir estos ocho nombres. Ya está parametrizado con `CATALOGO`
   y `CATALOGO_SIGRID`, y espera `_errata(1, 1, nombre)`:

   | Nombre | A qué mata |
   |---|---|
   | `"Solados y  Alicatados"` (dos espacios) | blancos interiores: S-ambos, S-tabla, S-tabla-tolerante, O-ambos, O-tabla y O-tabla-tolerante |
   | `"Píntura"` | tildes por el lado tolerante, con ñ y sin ella, en S y en O |
   | `"Albanileria"` | O-obra-suma/tildes (la ñ cuenta como tilde) |
   | `"Pintura."` | puntuación por el lado tolerante, en S y en O |
   | `"Solados-y-Alicatados"` | puntuación cambiada por espacio: ambos y tolerante, en S y en O |
   | `"Solados y Alicatados M O "` (con el espacio final, que sale del último punto) | puntuación cambiada por espacio: ambos y suma, en S y en O |
   | `"SoladosyAlicatados"` | blancos todos fuera: S-sigrid-suma y O-obra-suma |
   | `unicodedata.normalize("NFD", "Albañilería")` | forma Unicode de la obra: O-ambos/nfc/nfd/nfkc, O-tabla/nfc/nfkc, O-tabla-tolerante/nfc/nfkc y O-obra-suma/nfd |

   - **Está ejecutado, no es orientativo.** Sin mutar, los ocho paran con la
     errata literal en los dos catálogos. Con `CATALOGO_SIGRID` matan los 29.
   - Basta con que la parametrización lleve un comentario de una línea por
     familia. No cambia producción.
2. **Evidencia que hay que pegar en el informe** (mismo método que R11):
   - en una copia desechable, al menos uno de cada fila de la tabla, cada uno
     solo, en rojo con el test nuevo: S-tabla-tolerante/tildes,
     O-tabla-tolerante/tildes, O-obra-suma/tildes, S-tabla-tolerante/punt,
     S-ambos/punt_esp, S-sigrid-suma/punt_esp, S-ambos/blancos_int,
     O-ambos/blancos_int, S-sigrid-suma/blancos_todos y O-ambos/nfc;
   - los dos ficheros de la migración en verde sobre el código de siempre.
   - Mi guion está en el scratchpad de esta sesión y no se versiona. Las
     líneas mutadas son las de la sección «La familia completa».
3. **R12-2, para el humano:** aceptar en bloque los 20 equivalentes (lista
   arriba) o pedir que se maten. Matar los 16 «en la práctica» exige meter en
   el catálogo de prueba nombres que no existen en Sigrid (minúsculas, NFD,
   blancos dobles). No lo recomiendo.
4. **Para la review 13:** `init.sh` en verde. Al cambiar un test, la suite de
   `api` se relanza sola.

### Lo que no he hecho, dicho

- **La suite completa de `api`:** no la he relanzado fuera de la caché de
  `init.sh`. Sí he lanzado los dos ficheros de la migración, 113 veces (base
  y 112 mutantes).
- **La campaña de la herramienta** (`harness.mutacion`): no la he relanzado.
  El AST de producción no cambia desde T64.
- **Sigrid:** no lo he leído. Los recuentos salen de los dos JSON que ya
  estaban en `%TEMP%`, solo leídos.

### Automejora (propuesta, no aplicada)

- **`.claude/agents/reviewer.md`, punto 4.** Vale para `arnes-base`. Corrige
  otra vez la propuesta de la review 11.
- **Cómo debe quedar:** cuando el requisito diga que una comparación es
  «exacta» o «tal cual», el reviewer muta a mano con **cada** normalización.
  - **Las normalizaciones:** mayúsculas; tildes, con la ñ y sin ella;
    puntuación quitada y cambiada por espacio; blancos interiores
    (colapsados y quitados); extremos; y NFC, NFD y NFKC.
  - **Las formas, en las cinco:** los dos lados; solo la entrada; la entrada
    **tolerante** (exacto y, si no, normalizado); el catálogo **sumado**
    (original más normalizado); y solo el catálogo.
  - **Dónde:** en **cada** comparación de ese tipo que haya en el código, no
    solo en la del requisito que se revisa.
  - **Cómo se ejecuta:** con un guion que aplique cada mutación sola en
    copias desechables y la restaure. Son unos 100 mutantes y unos 25 minutos
    con 10 copias en paralelo.
  - **Qué no lo es:** los supervivientes que solo transforman el lado del
    catálogo y son la identidad sobre los datos reales se clasifican como
    «equivalentes en la práctica», con el recuento que lo demuestra.
- **Por qué:** probar la familia a trozos ha costado tres vueltas: R10-1,
  R11-1 y R11-2, y R12-1. Pasada entera de una vez, habría salido todo en la
  review 10.

## Review 13 (reviewer, 2026-10-04)

- **Veredicto:** APPROVED (de este cambio; la feature sigue `in_progress`,
  ver «Qué queda»)
- **Rama:** `feature/F-036-importar-excel`, HEAD `d6a0701`. Review **corta y
  cerrada**, acotada a `git diff 1186c1d..HEAD`:
  - `13a297f` (R12-1, solo test);
  - `d6a0701` (informe y `current.md`).
- **Alcance fijado por el humano (2026-10-04), vinculante:** los 20
  equivalentes de R12-2 (incluido V11b/R11-3) están **aceptados en bloque**, y
  esta review solo verifica este cambio, **sin abrir familias de mutación
  nuevas**. Consta en el primer bloque de `progress/current.md`.
- **Nivel de rigor:** `critico`, declarado en `harness/features.json`. Exige
  fase RED, cobertura, mutación con cero supervivientes sin justificación
  aceptada por el humano (también los de a mano) y MANUAL listadas.

### Resumen para el líder

- **Los ocho nombres de R12-1 están, tal cual**, con un comentario de una
  línea en cada uno.
- **Los 29 supervivientes no equivalentes de la review 12 caen los 29**, cada
  uno solo, en una copia de `git archive HEAD`. Todos los caza el test nuevo,
  y solo por uno de los ocho nombres.
- **La base de la copia está en verde:** `252 passed`.
- **`git diff 1186c1d HEAD -- services/postventa-api/scripts/`:** vacío.
- **`init.sh`:** en verde.
- **Con eso queda cerrada la familia de normalización:**
  - 63 caían ya en la review 12;
  - 29 caen ahora;
  - 20 son equivalentes, aceptados por el humano.

### Los ocho nombres

Comprobados **byte a byte** contra la tabla de R12-1 de la review 12, con un
guion que lee el fichero:

| Nombre | En el test | Comentario |
|---|---|---|
| `"Solados y  Alicatados"` (dos espacios) | sí | blancos interiores |
| `"Píntura"` (NFC) | sí | tildes por el lado tolerante, con ñ y sin ella |
| `"Albanileria"` | sí | tildes por la suma de la obra (la ñ cuenta como tilde) |
| `"Pintura."` | sí | puntuación quitada por el lado tolerante |
| `"Solados-y-Alicatados"` | sí | puntuación cambiada por espacio: ambos y tolerante |
| `"Solados y Alicatados M O "` (con el espacio final) | sí | puntuación cambiada por espacio: ambos y suma |
| `"SoladosyAlicatados"` | sí | blancos todos fuera: la suma de los dos catálogos |
| `unicodedata.normalize("NFD", "Albañilería")` | sí | forma Unicode de la obra |

- Un encabezado `# R12-1: …` agrupa los ocho. El comentario es **por
  nombre**, que cubre de sobra «uno por familia».
- `import unicodedata` ya estaba (R11-2).
- Nada más cambia en `services/`: el diff es de 9 líneas, todas en la
  parametrización.
- `ruff check` del test, desde la raíz: `All checks passed!`.
- El barrido de lo añadido sale limpio: ni `print`, ni secretos, ni `repr` de
  `Ajustes`.

### Los 29, cada uno solo (verificación propia)

**Método:**

- `git archive HEAD` (`d6a0701`, el repo entero; comprobado con `cmp` contra
  un `git archive HEAD` nuevo) extraído en diez copias del scratchpad, con el
  `.venv` del servicio real.
- El guion **comprueba** que `scripts.migracion_f036` se importa de la copia.
- Las mutaciones salen de las mismas líneas y normalizaciones que mi guion de
  la review 12 (`r12/driver.py`, que se importa, más la variante
  `tildes_sin_enie`).
- La lista es la de `r12/noeq.txt`, escrita en la review 12: **exactamente
  29**, y el guion lo comprueba.
- Cada mutación va **sola**. Se aplica, se lanzan
  `tests/test_f036_migracion.py` y `tests/test_f036_migracion_contenido.py`
  **sin `-x`** (para ver todos los que caen), con
  `--tb=no -q -rf -p no:cacheprovider`, y se restaura. Tras cada una, el guion
  comprueba que el fichero ha quedado como estaba.
- Solo se guardan el resumen y el **id** de cada test caído, nunca el
  mensaje: ningún `repr`.

Todos los ids que caen son de
`test_f036_r97_nombre_que_no_es_exactamente_uno_de_la_obra_para`. Abajo van
abreviados al parámetro (`catálogo-nombre`). La columna «ajenos» cuenta los
tests de otra función que caen: es 0 en las 29.

| Mutación | rc | Resultado | Parámetros que caen |
|---|---|---|---|
| Base sin mutar (HEAD) | 0 | `252 passed` | — |
| S-ambos/punt_esp | 1 | `2 failed, 250 passed` | SIGRID-`Solados y Alicatados M O `, SIGRID-`Solados-y-Alicatados` |
| S-ambos/blancos_int | 1 | `1 failed, 251 passed` | SIGRID-`Solados y  Alicatados` |
| S-tabla/blancos_int | 1 | `1 failed, 251 passed` | SIGRID-`Solados y  Alicatados` |
| S-tabla-tolerante/tildes | 1 | `1 failed, 251 passed` | SIGRID-`Píntura` |
| S-tabla-tolerante/tildes_sin_enie | 1 | `1 failed, 251 passed` | SIGRID-`Píntura` |
| S-tabla-tolerante/punt | 1 | `1 failed, 251 passed` | SIGRID-`Pintura.` |
| S-tabla-tolerante/punt_esp | 1 | `1 failed, 251 passed` | SIGRID-`Solados-y-Alicatados` |
| S-tabla-tolerante/blancos_int | 1 | `1 failed, 251 passed` | SIGRID-`Solados y  Alicatados` |
| S-sigrid-suma/punt_esp | 1 | `1 failed, 251 passed` | SIGRID-`Solados y Alicatados M O ` |
| S-sigrid-suma/blancos_todos | 1 | `1 failed, 251 passed` | SIGRID-`SoladosyAlicatados` |
| O-ambos/punt_esp | 1 | `4 failed, 248 passed` | los dos catálogos × `Solados y Alicatados M O ` y `Solados-y-Alicatados` |
| O-ambos/blancos_int | 1 | `2 failed, 250 passed` | los dos catálogos × `Solados y  Alicatados` |
| O-ambos/nfc | 1 | `2 failed, 250 passed` | los dos catálogos × NFD de `Albañilería` |
| O-ambos/nfd | 1 | `2 failed, 250 passed` | los dos catálogos × NFD de `Albañilería` |
| O-ambos/nfkc | 1 | `2 failed, 250 passed` | los dos catálogos × NFD de `Albañilería` |
| O-tabla/blancos_int | 1 | `2 failed, 250 passed` | los dos catálogos × `Solados y  Alicatados` |
| O-tabla/nfc | 1 | `2 failed, 250 passed` | los dos catálogos × NFD de `Albañilería` |
| O-tabla/nfkc | 1 | `2 failed, 250 passed` | los dos catálogos × NFD de `Albañilería` |
| O-tabla-tolerante/tildes | 1 | `2 failed, 250 passed` | los dos catálogos × `Píntura` |
| O-tabla-tolerante/tildes_sin_enie | 1 | `2 failed, 250 passed` | los dos catálogos × `Píntura` |
| O-tabla-tolerante/punt | 1 | `2 failed, 250 passed` | los dos catálogos × `Pintura.` |
| O-tabla-tolerante/punt_esp | 1 | `2 failed, 250 passed` | los dos catálogos × `Solados-y-Alicatados` |
| O-tabla-tolerante/blancos_int | 1 | `2 failed, 250 passed` | los dos catálogos × `Solados y  Alicatados` |
| O-tabla-tolerante/nfc | 1 | `2 failed, 250 passed` | los dos catálogos × NFD de `Albañilería` |
| O-tabla-tolerante/nfkc | 1 | `2 failed, 250 passed` | los dos catálogos × NFD de `Albañilería` |
| O-obra-suma/tildes | 1 | `2 failed, 250 passed` | los dos catálogos × `Albanileria` |
| O-obra-suma/punt_esp | 1 | `2 failed, 250 passed` | los dos catálogos × `Solados y Alicatados M O ` |
| O-obra-suma/blancos_todos | 1 | `2 failed, 250 passed` | los dos catálogos × `SoladosyAlicatados` |
| O-obra-suma/nfd | 1 | `2 failed, 250 passed` | los dos catálogos × NFD de `Albañilería` |

**Lectura:**

- **Caen los 29.**
- Cada uno cae **solo** por los nombres que la tabla de R12-1 le asignaba.
- Las de S caen solo con `CATALOGO_SIGRID`: con `oficios_catalogo` vacío no
  se llega a la comparación S.
- **Fase RED:** en la review 12, con el test de `1186c1d`, los 29 eran
  `VIVO`. El implementer lo repite para diez de ellos (`236 passed` con el
  test viejo), y sus diez filas coinciden con las mías.
- Unos 150 s por mutante. Todo junto, unos 8 minutos con diez copias.

### Verificación ejecutada por el reviewer

| Qué | Resultado |
|---|---|
| `bash harness/init.sh`, tal cual | **Verde** (`ENTORNO LISTO`). Raíz `62 passed`. `api` y `front` salen de **caché**: el árbol de `services/postventa-api` es el mismo en `13a297f` y en HEAD (`bdc4bf8`), y sobre `13a297f` el implementer relanzó la suite: `6644 passed, 74 skipped`. `PUERTA COBERTURA [OK]` 99,9 % (3314/3318) |
| `git diff 1186c1d HEAD -- services/postventa-api/scripts/` | **vacío** (0 bytes) |
| Los dos ficheros de la migración en la copia de HEAD | `252 passed` |
| Los 29 no equivalentes, cada uno solo | **29/29 en rojo**, todos por el test de R97 y por un nombre nuevo |
| `ruff check` del test, desde la raíz | `All checks passed!` |
| Árbol de trabajo | `git status --porcelain` vacío antes de escribir este informe. Copias, guion y resultados, solo en el scratchpad (las copias ya borradas) |

### Checkpoints (lo que esta review cambia)

- [x] **C1:** `init.sh` en verde. La suite de `api` sale de la caché del mismo
  árbol, comprobado arriba.
- [x] **C2:**
  - solo F-036 está `in_progress`, y la rama es la correcta;
  - `current.md` empieza por el bloque de R12-1, con las tres decisiones del
    humano;
  - no hay ninguna `done` nueva.
- [x] **C3:**
  - solo cambia un test, sin `import` nuevos;
  - primera línea con la ruta: sin cambios;
  - los puntos de partes, firmas y cierre en Sigrid son N/A, con el motivo de
    la review 1 (script local de migración).
- N/A · **C3 bis:** no entra nada en `docs/`.
- [x] **C4:** el test de R97 está en verde (`252 passed` en los dos
  ficheros), sin red ni base de datos.
- [x] **C4 bis:**
  - **Fase RED:** real. Los 29 eran `VIVO` con el test viejo (review 12) y
    caen con el nuevo; el implementer pegó la salida de diez.
  - **Cobertura:** `[OK]` 99,9 %.
  - **Herramienta:** no cambia producción ni el AST, y la campaña de T64 sigue
    16/16. No la reejecuto; el motivo es el mismo de las reviews 10–12.
  - **Evidencias:** la sección está, con los cuatro números.
  - **Cero supervivientes a mano sin justificación aceptada: SÍ.** Los 29 no
    equivalentes caen, y el humano aceptó por escrito los 20 equivalentes
    (2026-10-04).
- N/A · **C4 ter:** no existe `harness/rutas_sensibles.json`.
- [x] **C5:**
  - commit `F-036 R12-1` para el cambio y otro para el informe;
  - T28 (otra vez), T29 pasos 4–7 y T30 siguen abiertas, a propósito.

### Cobertura: requisito → test (lo que cambia)

| Requisito | Tests |
|---|---|
| R97: la búsqueda en la obra es exacta | `test_f036_r97_nombre_que_no_es_exactamente_uno_de_la_obra_para`: ahora también cubre blancos interiores, tildes (lado tolerante y suma), puntuación (quitada y cambiada por espacio), blancos todos fuera y forma NFD |
| R128: la comparación con `oficios_catalogo` es exacta | el mismo test, con `CATALOGO_SIGRID`, más `test_f036_r128_el_nombre_de_sigrid_se_compara_recortado` |

### Hallazgos

1. **R13-1 · [Cerrado]** R12-1: los ocho nombres están y los 29 caen.
2. **R13-2 · [Informativo, fuera del alcance]** El guion y las copias del
   implementer (`r12/mutar.py`, `r12/copias/`, `r12/salida.txt`) están dentro
   del directorio `r12/` del scratchpad del reviewer, porque la sesión es la
   misma. No afecta a nada versionado. Para que no se mezclen evidencias, cada
   rol debería usar su propio subdirectorio.
3. **R13-3 · [Informativo]** En la tabla del informe del implementer, la fila
   O-ambos/nfc muestra el id como `Albañilería`, pero pytest lo escapa
   (`Albañilería`), como está en su propio `salida.txt`.
   Cosmético; no pido nada.

### Qué queda para el humano

- **Esta review aprueba el arreglo de R12-1, no cierra F-036.** Para la
  feature siguen pendientes:
  - T28 otra vez;
  - T29, pasos 4–7;
  - T30;
  - las decisiones abiertas del spec-author.
- **La automejora de la review 12** (`.claude/agents/reviewer.md`, punto 4, y
  su paso a `arnes-base`) sigue propuesta, sin aplicar.

### Lo que no he hecho, dicho

- **La suite completa de `api`:** no la he relanzado fuera de la caché de
  `init.sh` (mismo árbol que `13a297f`, donde el implementer la sacó en
  verde).
- **Los 20 equivalentes y los 63 que ya caían:** no los he relanzado. Lo
  primero lo excluye la decisión del humano; lo segundo, el alcance.
- **La fase RED de los 19 que el implementer no pegó:** no la he relanzado
  con el test viejo. Que eran `VIVO` con ese test es la matriz de la review
  12.
- **Sigrid:** no lo he leído.
