<!-- specs/F-060-normalizar-ubicaciones/requirements.md -->
# F-060 · Normalizar las ubicaciones de la bandeja al texto exacto de Sigrid — Requisitos

> **Estado: pendiente de aprobación del humano** (PARADA 1). Escrita el
> 2026-10-09 sobre `feature/F-060-normalizar-ubicaciones` (`dev` en `704cfca`
> más `33d8938`). Las decisiones (D-n) y las preguntas (Q-n) están en
> `design.md` §15, con recomendación. Rigor **`critico`**.

## Contexto

F-056 (cerrada y desplegada el 2026-10-09) compara la ubicación de cada
incidencia **exacta** contra la lista de la tipología de su unidad en Sigrid
(`prmtpl.ubica`, design de F-056 §16). La plantilla de F-036 ofrece las
ubicaciones de `config/plantilla_incidencias.yaml`, con otras mayúsculas. En la
0677 (158 incidencias), 148 salen con `ubicacion_fuera_de_lista`: **110 solo
por mayúsculas**, 0 por tildes o blancos, y 38 (8 textos) porque de verdad no
están en la lista de su unidad.

**Decisión del humano (2026-10-09): normalizar, no comparar sin mayúsculas.**
Una ubicación que coincide salvo mayúsculas con una de la lista de su unidad
**pasa a ser el texto exacto de Sigrid**, con constancia, para que en la
bandeja, en lo aprobado y en lo que llegue al volcado (F-059) solo haya textos
de Sigrid. Vale para lo ya importado y para lo que se importe. La comparación
de F-056 **sigue exacta**.

Segundo objetivo: `GET /api/revision` tardó p50 7,1 s y máx. 12,7 s en la T19
de F-056 (9 peticiones), con las tres lecturas de Sigrid en 0,1–0,3 s cada
una. El código no basta para saber dónde se va el resto (`design.md` §11):
**primero se mide** en producción, luego se optimiza.

Ejemplos de esta spec: ficticios (obras `99NN`, ubicaciones «Sala Ejemplo»,
«Patio Ficticio»; correos `@ejemplo.invalid`).

## Definiciones

- **Lista de una unidad**: las ubicaciones válidas de F-056 para esa unidad
  (`ubicaciones_de_tipologia`, R47–R48 de F-056), leídas de Sigrid en esa
  petición. Una unidad fuera del catálogo de hoy tiene la lista vacía.
- **Clave de una ubicación**: el texto en forma Unicode NFC, recortado por los
  extremos y con `casefold()` (D-3).
- **Editable por la normalización**: una incidencia en estado `nueva` o
  `editada` (D-6).
- **Identidad del sistema**: `QUIEN_SISTEMA`, con `oid` y correo iguales al
  literal `sistema:normalizar_ubicacion` (D-4, Q-2).

## Requisitos

### La regla (dominio puro)

- **R1.** El sistema debe calcular la clave de una ubicación como
  `unicodedata.normalize("NFC", texto).strip().casefold()`: sin colapsar los
  blancos interiores, sin quitar tildes ni diéresis y sin quitar puntuación.
- **R2.** Dada una ubicación y la lista de su unidad, el sistema debe
  clasificarla así, en este orden:
  1. `exacta` si el texto, tal cual, es un valor de la lista;
  2. `normalizable` hacia el valor de la lista igual al texto recortado por
     los extremos, si lo hay;
  3. `normalizable` hacia el **único** valor de la lista cuya clave es la del
     texto;
  4. `ambigua` si dos o más valores de la lista tienen esa clave;
  5. `sin_coincidencia` si ninguno.
- **R3.** SI la lista de la unidad está vacía, ENTONCES el sistema debe
  clasificar cualquier ubicación como `sin_coincidencia`.
- **R4.** El sistema debe clasificar como `sin_coincidencia` una ubicación que
  solo difiere de las de la lista en una tilde, una letra, un blanco interior
  de más o de menos, o un signo de puntuación («Sala Ejemplo» frente a «Sála
  Ejemplo», «Sala  Ejemplo» o «Sala Ejemplo.»).
- **R5.** CUANDO la clasificación es `normalizable`, el texto resultante debe
  ser **exactamente** el valor de la lista (sus mayúsculas, sus tildes y sus
  blancos interiores), nunca una transformación del texto de partida.

### Qué se normaliza

- **R6.** El sistema debe planificar la normalización de una obra mirando, de
  cada incidencia, su ubicación **vigente** contra la lista de su unidad
  **vigente**, y omitir las que no tienen ubicación o la tienen `exacta`.
- **R7.** El sistema debe proponer una revisión de normalización **solo** para
  las incidencias editables por la normalización (`nueva`, `editada`) cuya
  ubicación es `normalizable`. Una `aprobada` o una `descartada` (y, cuando
  exista F-059, una `volcada` o `en_duda`) no recibe nunca una revisión de
  normalización, aunque su ubicación sea `normalizable`: se cuenta en
  `no_editables`.
- **R8.** La revisión de normalización debe ser una fila de
  `postventa.revisiones_bandeja` con `accion = editar`; sus valores, los
  vigentes con **solo** la ubicación cambiada (los otros doce, idénticos); su
  huella, `huella_de_valores` de esos valores; sin motivo; `QUIEN_SISTEMA`
  como quién; y el instante de la petición.
- **R9.** El plan debe llevar, por incidencia, la `revision_id` de su última
  revisión leída (o `null` si no tiene) como la esperada para la escritura.
- **R10.** El sistema debe dar un recuento de la obra: `examinadas` (todas las
  leídas), `no_exactas` (con ubicación y no `exacta`), `normalizables`,
  `ambiguas`, `sin_coincidencia` y `no_editables`, de modo que
  `no_exactas = normalizables + ambiguas + sin_coincidencia + no_editables`.
- **R11.** `validar_quien` (F-056 R9) debe seguir rechazando el correo de
  `QUIEN_SISTEMA`: ninguna persona puede actuar como el sistema por
  `POST /api/revision/acciones`.

### La escritura

- **R12.** El sistema debe registrar las revisiones de normalización de una
  obra en **una** transacción: bloquear con `SELECT … FOR UPDATE`, en orden
  fijo de `incidencia_id`, las filas de la bandeja de todas; leer la última
  `revision_id` de cada una; insertar **solo** las que coinciden con su
  esperada, en orden de `incidencia_id`; y devolver las registradas (con su
  `revision_id`) y las desactualizadas.
- **R13.** SI la última revisión de una incidencia no es la esperada (alguien
  actuó entre la lectura y la escritura), ENTONCES el sistema no debe escribir
  la suya y debe contarla en `conflictos`, **sin** abortar las demás.
- **R14.** SI la base falla durante el lote, ENTONCES el sistema debe deshacer
  la transacción entera y levantar `PersistenciaNoDisponible` (→ 503) con la
  operación y el tipo del fallo, nunca los parámetros.
- **R15.** El sistema no debe actualizar ni borrar ninguna fila: ni de
  `revisiones_bandeja` (append-only) ni de `bandeja_incidencias` (lo
  importado queda como llegó).
- **R16.** CUANDO el lote está vacío, el sistema no debe abrir transacción ni
  escribir nada.

### La normalización de una obra (aplicación)

- **R17.** `normalizar_ubicaciones` debe leer las incidencias de la obra con
  el tope de F-056 (10.000) y, si se pasa, levantar `BandejaDemasiadoGrande`
  **sin** leer las ubicaciones ni escribir.
- **R18.** Debe leer las ubicaciones válidas de Sigrid **una** vez por
  ejecución, con el catálogo que recibe, y aplicar R6–R10.
- **R19.** DONDE `ensayo` es `true`, el sistema no debe escribir nada (el lote
  no se llama) y debe devolver el recuento con `normalizadas = 0` y
  `conflictos = 0`.
- **R20.** DONDE `ensayo` es `false`, el sistema debe registrar el lote y
  devolver el recuento con `normalizadas` (las registradas) y `conflictos`
  (las desactualizadas), con `normalizadas + conflictos = normalizables`.
- **R21.** CUANDO se ejecuta dos veces seguidas sin cambios entre medias, la
  segunda debe dar `normalizables = 0` y no escribir nada (idempotencia).
- **R22.** CUANDO una incidencia se ha normalizado, `GET /api/revision` debe
  enseñarla con la ubicación de Sigrid en `vigentes`, la de la propiedad en
  `importados`, `"ubicacion"` en `cambios`, estado `editada` (Q-1), el correo
  de `QUIEN_SISTEMA` en `revisado_por` y **sin** `ubicacion_fuera_de_lista`;
  y su historial, una revisión `editar` con ese correo y
  `campos_cambiados = ["ubicacion"]`.
- **R23.** Una ubicación `ambigua` o `sin_coincidencia` debe seguir saliendo
  con `ubicacion_fuera_de_lista` y sin revisión nueva.

### Lo aprobado y lo que llega al volcado

- **R24.** CUANDO se aprueba una incidencia normalizada, la revisión `aprobar`
  y su `CandidataAlVolcado` deben llevar la ubicación exacta de Sigrid.
- **R25.** Aprobar una incidencia cuya ubicación solo difiere en mayúsculas y
  **no** se ha normalizado debe seguir dando 409 `incidencia_no_aprobable`
  con `ubicacion_fuera_de_lista`, y editar con una ubicación así debe seguir
  dando 400 `valores_no_validos` en `ubicacion` (D-5): la comparación de F-056
  no cambia.

### El endpoint `POST /api/revision/normalizar`

- **R26.** El sistema debe aceptar un cuerpo JSON con **exactamente** `obra`,
  `confirmado` y `ensayo`: `confirmado` el booleano `true` de JSON, `ensayo`
  un booleano de JSON (sin valor por defecto) y `obra` un código válido para
  `normalizar_codigo_obra`. SI no, ENTONCES 400 (`peticion_invalida`, o el
  código de obra inválido de F-036) **antes** de construir ningún adaptador y
  sin repetir lo recibido.
- **R27.** CUANDO el cuerpo vale, el sistema debe leer el catálogo de la obra
  (`leer_catalogo`, las dos lecturas de F-036) y ejecutar
  `normalizar_ubicaciones`, y responder 200 con `obra`, `ensayo` y el
  recuento de R10, `normalizadas` y `conflictos`: solo números, sin textos,
  sin `incidencia_id`, sin correo.
- **R28.** SI la obra no tiene unidades, es ambigua, la lectura llega al
  techo, la bandeja pasa del tope, o Sigrid, la base o su configuración no
  están, ENTONCES el sistema debe responder lo mismo que `GET /api/revision`
  (404 `obra_sin_unidades`; 409 `obra_ambigua`, `catalogo_sin_verificar`,
  `bandeja_demasiado_grande`; 503) sin haber escrito nada.
- **R29.** El endpoint debe construir los adaptadores de Sigrid **antes** que
  los de la base (como F-056) y hacer, como mucho, tres lecturas de Sigrid
  por `POST /api/sql/read`.
- **R30.** El endpoint debe registrar una línea con la obra, `ensayo`, el
  recuento, `normalizadas`, `conflictos` y los segundos; nunca textos,
  `oid` ni correo.

### Tras cada importación

- **R31.** CUANDO una importación registra al menos una fila en la bandeja
  (`nuevas + duplicadas_en_fichero > 0`), el sistema debe ejecutar
  `normalizar_ubicaciones` de esa obra con `ensayo = false` y con el catálogo
  que la importación ya leyó, **después** del Excel de errores (D-2).
- **R32.** CUANDO la importación es `ya_importado` o no registra ninguna fila,
  el sistema no debe ejecutar la normalización ni leer las ubicaciones.
- **R33.** La respuesta de `POST /api/importaciones` debe ser la misma, clave
  a clave y valor a valor, con normalización y sin ella.
- **R34.** SI la normalización tras importar falla por un error de
  disponibilidad o configuración (de Sigrid, de la base o el tope de la
  bandeja), ENTONCES la importación debe responder igual que si no hubiera
  normalización y registrar un aviso con la obra y el **tipo** del error;
  ningún otro efecto. **Decisión del humano 2026-10-12: mejor esfuerzo =
  cualquier excepción de la normalización se registra por su tipo y no afecta
  a la importación.** Vale para **cualquier** excepción al componer o ejecutar
  la normalización tras importar (también un `AttributeError` por una
  configuración incompleta o un error de programación): el aviso lleva solo el
  tipo, sin mensaje, textos de ubicación, correo ni `oid`. Nada más de la
  importación se captura de forma amplia (`design.md` §5.1).
- **R35.** La importación debe registrar, cuando normaliza, una línea con la
  obra, `normalizadas`, `conflictos`, `ambiguas`, `sin_coincidencia` y los
  segundos; nunca textos, `oid` ni correo.

### Contratos que no cambian

- **R36.** `GET /api/revision`, `GET /api/revision/historial`,
  `POST /api/revision/acciones` y `POST /api/importaciones` deben responder
  con las mismas claves que hoy: F-060 no añade ni quita ninguna (F-038, el
  front de F-036).
- **R37.** F-060 no debe crear ni modificar ningún `.sql`
  (`15_revisiones_bandeja.sql` intacto): sin DDL (D-4).
- **R38.** Ningún módulo de F-060 debe escribir en Sigrid, nombrar una ruta de
  escritura de la pasarela ni mirar una ventana de escritura
  (`CIERRE_HABILITADO`, `ARCHIVO_HABILITADO`, `VOLCADO_HABILITADO`).
- **R39.** Los tests de F-036 y de F-056 deben seguir en verde **sin
  tocarse**, salvo los que enumeran rutas o cuentan endpoints, que se
  **amplían** sin quitar nada (`test_f010_endpoints_protegidos.py`,
  `test_f053_documentacion.py`) y se citan en el informe. **Excepción
  (decisión del humano 2026-10-10):**
  `test_f056_repositorio_revision.py::test_f056_r34_el_puerto_tiene_las_seis_operaciones_de_5`
  se amplía, sin relajarlo, para exigir el conjunto exacto de **siete**
  operaciones de `RevisionPort` (las seis de F-056 más `registrar_lote`);
  ninguna otra aserción de F-056 cambia.
  **Excepción del Bloque 5 (T20; decisión del líder 2026-10-13 con el criterio que el humano aprobó en F-056: un test de documentación que fija una frase que cambia se amplía sin relajar y se declara)**: `test_f056_documentacion.py::test_f056_r44_la_seccion_ocho_dice_la_cuenta_y_las_ventanas` («Los veintiuno», y «Los veinte» en `not in`) y `…::test_f056_r44_la_cabecera_dice_que_f056_lo_toco` (deja de exigir que F-056 sea la **última** feature de la cabecera de `INTEGRACION.md` y exige una cabecera bien formada que no retroceda, con F-056 y su despliegue constando, como hizo F-056 con el de F-036); fuera de F-036 y F-056, `test_f053_documentacion.py` (`CUENTA_VIGENTE`), `test_f012_documentacion.py` (`NUMERALES` hasta 21) y `test_f019_documentacion.py::test_f019_r32_…`. Ninguna otra aserción cambia; `tests/test_f060_alcance_cerrado.py` lo vigila función a función.

### Medir el listado

- **R40.** CUANDO `GET /api/revision` termina, con 200 o con un error, el
  borde debe registrar **una** línea `F-060 tiempos del listado` con la obra,
  el resultado (`200` o el tipo del error), el total, `proceso_nuevo` (si es
  la primera petición de ese proceso), los segundos desde que arrancó el
  proceso y los segundos de cada tramo: la construcción de cada adaptador,
  cada método de puerto llamado, la aplicación entera, el cálculo (la
  aplicación menos los puertos) y la serialización.
- **R41.** La medición no debe cambiar nada de lo que hace el listado: los
  mismos valores devueltos, las mismas excepciones, las mismas llamadas a los
  puertos y el mismo orden de construcción.
- **R42.** La línea de tiempos debe llevar solo la obra, nombres de tramo y
  números; ni correo, ni `oid`, ni textos. La línea de F-056 del listado no
  cambia.

### Documentos

- **R43.** `docs/ARCHITECTURE.md` (sección de F-060 y enmienda del «no
  revisa» de F-036), `docs/INTEGRACION.md` (§2 la ruta nueva, §7 la identidad
  del sistema, §8 la cuenta de anónimos a veintiuno) y
  `azure-apps/postventa_incidencias.md` deben quedar al día.

## Verificación en producción (MANUAL, humano; `tasks.md` Bloques 6 y 7)

- **V1.** En la 0677, el ensayo da `normalizables` igual a las de solo
  mayúsculas que haya ese día (110 el 2026-10-09) y la normalización real las
  escribe (`normalizadas + conflictos = normalizables`). Después,
  `resumen.por_motivo.ubicacion_fuera_de_lista` de `GET /api/revision` pasa de
  su valor de antes a **antes − `normalizadas`** (de 148 a **38** si nada ha
  cambiado desde la T19 y no hay `ambiguas` ni `no_editables`). Un segundo
  ensayo da `normalizables = 0`.
- **V2.** Nada se ha escrito en Sigrid: la lectura de
  `infra\24_ubicacion_sigrid.ps1 -CodigoObra 0677` antes y después es la
  misma.
- **V3.** El tiempo del listado se mide con la línea de R40 y la duración de
  la petición en Application Insights (consultas de `tasks.md`), en caliente y
  en frío por separado. Objetivo (D-10, Q-3): en caliente, **máximo < 10 s**
  (obligatorio) y **p50 < 3 s** (deseable). Si la medición ya lo cumple, el
  Bloque 7 no se hace y consta por escrito.
