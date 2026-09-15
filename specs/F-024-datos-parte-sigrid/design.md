<!-- specs/F-024-datos-parte-sigrid/design.md -->
# F-024 · Datos del parte enlazados a Sigrid, para el datamart — Diseño

> Rigor `estandar`. Esta feature **no escribe en ningún sistema ajeno**: ni en
> Sigrid, ni en SharePoint. Toca el schema propio `postventa` del servidor
> compartido `psql-albaranes-rs9k2` —columnas nuevas y una vista—, el prompt
> de extracción y el front. Encaja en `docs/ARCHITECTURE.md` (paso 3 del
> pipeline y almacén de estado) y en `docs/CONVENTIONS.md` (SQL numerado e
> idempotente). Servicios: `services/postventa-api/` y `services/postventa-front/`.
>
> Convención: cada afirmación sobre datos reales va marcada **[MEDIDO]** (con
> su fuente) o **[INFERIDO]**. Lo que no se sabe va a §13 con opciones y una
> recomendación; no se inventa. **Ni un dato personal** en esta spec: los
> ejemplos son inventados.

## 0 · Lo que ya está resuelto y no hay que volver a preguntar

| Pregunta | Respuesta | Dónde |
|---|---|---|
| Qué guarda hoy `postventa.partes` | Los nueve campos de F-003 con sus confianzas, la traza de IA (`prompt_version`, `prompt_huella`, modelo) y los avisos. `hash_parte` es la clave | `03_partes.sql` **[MEDIDO en el DDL]** |
| Qué imprime el parte que hoy no se extrae | Oficio, Nº referencia externo (vacío en toda la remesa), Empresa (el industrial), Cliente/Teléfono (vacíos), Dirección, Estancia | `docs/referencia/02_parte_de_trabajo.md` **[MEDIDO sobre 22 partes]** |
| Qué se escribe a mano y hoy no se extrae | Hora inicio y hora finalización, **vacías en toda la remesa**; ficha y DNI del técnico, vacíos | íd. **[MEDIDO]** |
| Qué registra el cierre en Sigrid | El gráfico (`gra`, `rcg`) y el estado (`con.est` + fila de `dbo.log`). **Nada más** | `01_cierre_incidencia_sigrid.md`, `03_modelo_posventa_sigrid.md` §2 **[MEDIDO]** |
| Cuál es la clave estable de la reclamación | `con.ide`. `con.cod` (`RS26.08/0123`) es único dentro del tipo 708 (23.063/23.063) pero es legible, no clave, y **no codifica la obra** | `03_modelo_posventa_sigrid.md` §1.1 **[MEDIDO]** |
| Cómo se llega de la reclamación a la obra | `rcp.upvide` → `upv.obride` → `obr` (= `con`, cuyo `con.cod` es el código de obra) | `azure-apps/sigrid_tablas.md` **[MEDIDO en el diccionario]**; `specs/F-012-grafico-sigrid/design.md` §15 |
| De dónde sale `reclamacion_ide` en nuestras trazas | Del dry-run de F-009 (`ErpPort.leer_reclamacion` → `Reclamacion.ide`). `postventa.graficos` ya lo guarda desde el primer dry-run | `09_graficos.sql`, `paso_grafico._traza` **[MEDIDO en código]** |
| Cómo se versiona el prompt | `version` declarada + huella sha256 calculada al cargar, las dos en la traza del parte. La huella de `parte_posventa_es` está **clavada a mano** en `test_f004_prompts_firma.py` para forzar una nueva medición si cambia | F-003 R10, F-004 D3 **[MEDIDO en código]** |
| Qué admite la guarda de DDL | `CREATE SCHEMA/TABLE/INDEX IF NOT EXISTS`, `CREATE OR REPLACE VIEW`, `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` (una columna por sentencia); lista negra con `GRANT`, `CREATE ROLE`, `CREATE EXTENSION` | `ddl.py` **[MEDIDO en código]** |
| Dónde vive el datamart | Base `sigrid_dm` en el **mismo** servidor; rol de solo lectura `mcp_sigrid_dm_ro`; publica su semántica en `_meta`; sus vistas de contrato solo añaden columnas al final; un `DROP` se lleva los `GRANT` | `azure-apps/datamart_seg_anual.md` **[MEDIDO en el documento]** |
| Si el datamart ingiere ya `rcp`/`upv` | No consta entre los grupos que entraron en su F-066 (personal, contabilidad, compras); la ficha de F-024 dice «cuando el datamart incluya los partes de postventa» | **[INFERIDO]** |
| Cuántos partes hay en la base desplegada con `prompt_version = "1"` | No se sabe desde aquí: consulta preparada Q1 (§14), solo lectura, la lanza el humano | **[NO MEDIDO]** |

## 1 · Las decisiones del humano (2026-09-06), y cómo se traducen

| # | Decisión | Qué hace este diseño con ella |
|---|---|---|
| **H1** | Extraer `oficio`, `empresa`, `estancia`, `hora_inicio`, `hora_fin` con confianza, **sin exigirlos**; columnas con `ADD COLUMN IF NOT EXISTS` en un DDL nuevo | D-A, D-B, D-C; `10_partes_campos_datamart.sql` (§8.1) |
| **H2** | `reclamacion_ide` en `postventa.cierres`, relleno en el dry-run; `graficos` ya la tiene | D-D; `11_cierres_reclamacion_ide.sql` (§8.2); un campo en `TrazaCierre` y una línea en `paso_cierre._traza` |
| **H3** | Vista `postventa.v_partes_sigrid`, una fila por parte, claves de Sigrid, campos con confianzas, firma y veredicto, archivo con URL, gráfico y cierre con fechas, **sin `dni_cliente`**. Pregunta abierta: `observaciones` | D-E, D-F, D-G, D-H; `12_v_partes_sigrid.sql` (§8.3); P1 en §13 |
| **H4** | Fuera de alcance el acceso desde el datamart; petición escrita y contrato documentado en `azure-apps` | D-J; §12 (la petición) y §15 (la documentación) |
| **H5** | Rigor `estandar`; verificación manual pequeña | §11 y `tasks.md`: M1 (un barrido de extracción) y M2 (la vista en la base desplegada, solo lectura) |

## 2 · Las decisiones de este diseño

### D-A · Los cinco campos entran **al final** del contrato y sin rama propia

**Decidido:** `CAMPOS_DEL_PARTE` pasa de nueve a catorce **añadiendo al final**
`oficio`, `empresa`, `estancia`, `hora_inicio`, `hora_fin`, en ese orden; y
`CAMPOS_MANUSCRITOS` gana `hora_inicio` y `hora_fin`.

Es lo que hace que la feature sea pequeña: `schema_para` (el JSON schema que
viaja al modelo), `_completar_y_sanear` (el paso de extracción),
`columnas_de_campos` / `valores_de_campos` (las columnas de `partes`),
`cuerpos.a_extraccion` (`/api/validar` y `/api/parte`) y `archivar._contexto`
**recorren la tupla**; ninguno lleva lista a mano. Añadir cinco campos es
tocar la tupla y la línea del prompt que los describe —exactamente lo que
F-003 §5.2 diseñó para este caso— y actualizar los censos escritos a mano en
los tests, que existen para que este cambio **no pase desapercibido**.

Al final y no intercalados por dos motivos: `test_f003_extraccion_dominio.py`
fija los ocho de contenido como **prefijo** de la tupla, y el orden de la tupla
es el orden de las columnas de `03_partes.sql`. Las diez columnas nuevas se
añaden con `ALTER TABLE` en el mismo orden, así que `columnas_de_campos()` y
el DDL siguen contando la misma historia.

**Ni una rama de código para los campos nuevos** (misma decisión que F-003 tomó
con `numero_pagina`): un camino especial sería superficie de mutantes gratis y
una forma de que el campo nuevo se comportara distinto sin que nadie lo
pidiera.

**Descartado:** un `jsonb` de «campos adicionales» en `partes`. F-005 ya lo
descartó para los nueve —un `jsonb` esconde del `information_schema` qué
columnas guardan qué— y la vista necesita columnas con nombre para ser un
contrato.

### D-B · El prompt sube a `version: "2"`; los partes antiguos **no se reextraen**

**Decidido:** `parte_posventa_es` describe los cinco campos, sube `version` a
`"2"` y su huella cambia; la constante `HUELLA_DEL_PROMPT_MEDIDO` de
`test_f004_prompts_firma.py` se actualiza con la huella nueva citando F-024 y
la verificación M1 que vuelve a medir la lectura.

Por qué la versión declarada **tiene** que subir: es un cambio de contrato del
prompt (pide cinco cosas más), no una coma. La huella cambiaría igual, pero la
versión es lo que una persona lee en `partes.prompt_version` sin calcular
nada.

Qué implica para los partes ya guardados —los del piloto de Mirasierra que
hayan pasado por el circuito desplegado— y **qué se decide**:

- Sus filas quedan con las diez columnas nuevas a `NULL` (valor) y `0`
  (confianza), y `prompt_version = "1"`. Es **indistinguible por las columnas**
  de un parte leído con v2 en el que el campo estaba en blanco (que también
  sale `NULL` / `0`, regla 1 del prompt). **Lo que los distingue es
  `prompt_version`**, y por eso la vista la expone (R25).
- **No se reextraen.** Reextraer exige el PDF, que **no está en la base** (R12
  de F-005): habría que descargarlo de SharePoint o volver a subir la remesa.
  Y gasta una llamada de IA por parte. El dato que se pierde en esas filas es
  oficio/empresa/estancia de un puñado de partes del piloto.
- **Si el humano quiere rellenarlos**, la vía ya existe: volver a subir la
  remesa de Mirasierra por el front. `upsert_parte` actualiza por `hash_parte`
  —conserva `primera_vez_at_utc`, sube `reprocesos`— y la fila queda con v2.
  Sin duplicar (R13–R16 de F-005). Es P5 de §13, y no bloquea nada.

**Descartado:** un prompt aparte para los cinco campos (segunda llamada de
IA). Doblaría el coste por parte y la latencia dentro del presupuesto de 45 s
sin ganar nada: los campos están en el mismo papel que los otros nueve.

**Descartado:** mantener `version: "1"` y dejar que solo la huella cambie.
Sería justo el caso que F-003 R10 describe como error: la declaración diría
«qué querías» y ya no sería verdad.

### D-C · Tres ficheros de DDL, no uno

**Decidido:** `10_partes_campos_datamart.sql`, `11_cierres_reclamacion_ide.sql`
y `12_v_partes_sigrid.sql`.

`docs/CONVENTIONS.md` pide «un fichero por unidad lógica». Son tres unidades
—las columnas del parte, la clave del ERP en el cierre, la vista— con tres
ciclos de vida distintos: el día que un campo nuevo entre en el contrato se
tocará el 10 (o uno nuevo) y el 12, y el 11 no; el día que el humano decida
exponer `observaciones` se tocará solo el 12. La numeración garantiza el orden
que la vista necesita (después de todas las tablas y de todos los `ALTER`).

`03_partes.sql` y `06_cierres.sql` **no se tocan**: el patrón del ecosistema
(`albaranes.md` §5.3) es `CREATE ... IF NOT EXISTS` para lo que nace y `ALTER
TABLE ... ADD COLUMN IF NOT EXISTS` para lo que crece, y es el único `ALTER`
que la guarda admite. Editar el `CREATE TABLE` sería invisible para una base
que ya tiene la tabla.

### D-D · `reclamacion_ide` en `cierres`; **ni `obra_ide` ni `upv_ide`**

**Decidido:** `postventa.cierres` gana `reclamacion_ide integer` anulable,
`TrazaCierre` gana el campo, `paso_cierre._traza` lo rellena con
`plan.reclamacion.ide` y `upsert_cierre` lo escribe. Como en `graficos`: desde
el primer dry-run, porque toda traza que nace de un plan ya tiene la
reclamación leída.

**Recomendación: no guardar `obra_ide` ni `upv_ide`.** Cuatro motivos, y el
primero basta:

1. **Desde `reclamacion_ide` se llega a todo, y se llega mejor desde el
   datamart que desde aquí.** La cadena `rcp.upvide → upv.obride → obr` es
   determinista **[MEDIDO en el diccionario]**, y el datamart la resolverá
   sobre **su copia** de Sigrid, que es la que está al día. Si Posventa
   moviera una reclamación de unidad (improbable pero posible), un `upv_ide`
   guardado aquí el día del cierre sería un dato viejo con aspecto de clave.
2. **Costaría tocar F-009.** `Reclamacion` tiene once campos «y ninguno es de
   gráficos», y `SQL_RECLAMACION` lee solo `con` y `conest`; añadir `upvide` y
   `obride` exige extender la consulta del dry-run, el dataclass, `fila_a_reclamacion`,
   `ErpEnMemoria` y los tests de una feature `critico` cerrada con cero
   supervivientes. Para una redundancia.
3. **La obra ya está.** `codigo_obra` es el `con.cod` de la obra leído del
   papel (`0677`), con su confianza; es la clave legible de la obra en todo el
   ecosistema (el datamart la usa en `_meta.v_frescura_obra.codigo_obra`) y la
   vista la expone. `numero_incidencia_sigrid` (`con.cod` confirmado por el
   ERP) cubre además a los partes cuyo dry-run nunca llegó a guardar un `ide`.
4. **Un dato no verificado.** `codigo_obra` sale del papel con confianza; un
   `obra_ide` saldría del ERP como consecuencia de la reclamación. Guardar los
   dos invita a cruzarlos, y el día que no cuadren nadie sabrá cuál manda.

Si el datamart llegara a pedir `upv_ide` explícitamente, es una columna más al
final de la vista y una extensión de la consulta de F-009: se decide entonces,
con la petición delante.

### D-E · La vista: `partes` a la izquierda, cuatro `LEFT JOIN`, una fila por parte

**Decidido:** `FROM postventa.partes p LEFT JOIN validaciones v ... LEFT JOIN
archivos a ... LEFT JOIN graficos g ... LEFT JOIN cierres c ...` por
`hash_parte`, sin `WHERE`. Las cuatro tablas tienen `hash_parte` como **clave
primaria**, así que la vista no puede multiplicar filas: es una fila por parte
por construcción, no por un `DISTINCT`.

Dos números de incidencia, a propósito:

- `numero_incidencia`: el que leyó el modelo del papel (`partes`), con su
  confianza; puede ser `NULL` (revisión manual) o venir con un guion raro.
- `numero_incidencia_sigrid`: el `con.cod` **que devolvió el ERP** en el
  dry-run, `COALESCE(c.numero_incidencia, g.numero_incidencia)`. En `cierres`
  y `graficos` esa columna se rellena siempre con `plan.reclamacion.codigo`
  **[MEDIDO en `paso_cierre._traza` y `paso_grafico._traza`]**, así que es
  canónico; `NULL` significa «nunca hubo dry-run».

Y `reclamacion_ide = COALESCE(g.reclamacion_ide, c.reclamacion_ide)`: la
misma reclamación, leída por el mismo `select_reclamacion`, en dos trazas;
`graficos` va primero porque es el paso anterior y porque desde F-012 es quien
la tiene siempre que hay cierre.

### D-F · Sin `dni_cliente`, y `tiene_observaciones` en vez del texto (por defecto)

**Decidido:** la vista no nombra `dni_cliente` ni su confianza, ni siquiera un
booleano derivado. Y expone `tiene_observaciones` (`observaciones IS NOT NULL
AND btrim(observaciones) <> ''`, el mismo criterio que `CampoExtraido.esta_vacio`)
más `observaciones_confianza_pct`, **no el texto**, salvo que el humano elija
lo contrario en P1 (§13).

La razón es la de F-005 §6: el DNI y la transcripción son **dato personal
directo** y viven en una sola columna de una sola tabla; la vista es una
segunda superficie, pensada para que la lea **otro rol** desde **otro
proyecto**. Lo que el datamart necesita para enriquecer un parte —si hubo
observaciones, con qué confianza, y a dónde fue el parte por ello (`destino`)—
lo da el booleano. Lo que **no** le da es la voz del cliente, que es
exactamente lo que puede llevar un nombre.

Por qué el booleano se calcula con `btrim` y no con `IS NOT NULL`: el modelo
puede devolver `""` o espacios, y `esta_vacio` los trata como vacío. Una vista
que dijera `tiene_observaciones = true` por una cadena de espacios
contradiría al dominio.

### D-G · Lo demás que la vista **no** expone, y por qué `gra_cod` sí

No se exponen:

- **`usuario_oid` y `confirmado_por`** (de `remesas`, `cierres`, `graficos`):
  dato personal seudónimo de empleados; el datamart no lo necesita para nada
  que esta vista responda.
- **`motivo`** de `archivos`, `cierres` y `graficos`: texto libre que compone
  el pipeline con lo que devuelvan Graph, la pasarela o el ERP. Hoy no lleva
  datos personales **[MEDIDO en `paso_cierre`, `paso_grafico`, `paso_archivo`]**,
  pero es la clase de columna cuyo contenido cambia con cada feature, y un
  contrato no puede prometer lo que no controla. Los **estados** sí van.
- **`motivos` y `avisos`** (`jsonb`) de `validaciones` y `partes`: los textos
  son constantes del dominio (`TEXTO_OBSERVACIONES_MANUSCRITAS`, etc.)
  **[MEDIDO en `validacion.py`]**, pero son `jsonb` con estructura propia; el
  datamart quiere columnas planas. Si algún día se piden, se añaden al final
  como texto (`codigo`s separados por coma) o como columnas booleanas.
- **`paginas_origen`, `origen`**: internos del troceado.
- **`dry_run_at_utc` de `graficos`**: se expone `adjuntado_at_utc`; el dry-run
  del gráfico es un detalle del mecanismo. El del cierre sí se expone
  (`cierre_dry_run_at_utc`) porque marca «alguien miró esta incidencia» aunque
  no llegara a cerrarla.

**`gra_cod` sí se expone**, porque el humano lo listó entre las claves y porque
es el identificador con el que se localiza el gráfico en Sigrid (la pareja
negocio/documental se casa por `cod`, no por `ide` **[MEDIDO,
`03_modelo_posventa_sigrid.md` §4.1]**). Consta que **lleva dentro el login
del ERP** de quien confirmó (`AAAAMMDDHHMMSS` + 4 dígitos + `.login`); se dice
en el `.sql`, en `INTEGRACION.md` y en la petición al datamart. `gra_ide_negocio`
va al lado como la clave numérica sin login, por si el consumidor prefiere no
tocar la otra.

### D-H · El orden de las columnas es el contrato

**Decidido:** la lista de columnas de la vista, en su orden, se escribe **a
mano** en `test_f024_vista.py` y se compara con la lista que sale del `.sql`.
Y la regla, tomada de cómo el datamart trata `_meta.v_diccionario`: **solo se
añaden columnas al final; nunca se quita, renombra ni reordena una**.

No es estética. `CREATE OR REPLACE VIEW` en PostgreSQL acepta añadir columnas
al final y **rechaza** quitar, renombrar o cambiar el tipo de las existentes
(`cannot drop columns from view`) **[INFERIDO de la documentación de
PostgreSQL 16; no se ha probado contra el servidor]**. Cambiarlas exigiría un
`DROP VIEW`, que la guarda no admite (`DROP` no está en las cinco formas) y que
además se llevaría por delante los `GRANT` del rol de lectura del datamart. La
regla convierte esa limitación en promesa: el consumidor puede leer por
posición o por nombre y ninguna de las dos se mueve.

Por eso, si P1 acaba en (b), `observaciones` va **la última**, y si mañana
F-016 quiere exponer su clasificación, va detrás.

### D-I · El front pinta los catorce con la misma plantilla

**Decidido (recomendación; P3 de §13):** `js/pipeline.js::CAMPOS_DEL_PARTE`
pasa a catorce en el orden del dominio, y la tarjeta del parte de
`index.html` —que ya itera `CAMPOS` y pinta valor, confianza y el aviso de
«dudoso»— muestra los cinco nuevos **sin tocar la plantilla**. Quedan
**editables como los otros nueve**, con la regla D3 de F-007: lo que corrige
una persona viaja con confianza 100 y marcado como `editado`.

El líder sugería «solo lectura». Se propone editable, y se explica: (1) no
exige ninguna rama en la plantilla ni en `editarCampo`; (2) `hora_inicio` y
`hora_fin` son manuscritos y son justo los que el modelo leerá peor —una
persona que ve `18:30` donde el modelo puso `10:30` debería poder corregirlo
antes de guardar, porque es el dato que el datamart va a consumir—; (3) editar
un campo que no decide nada no cambia el veredicto (R3), así que no hay riesgo
de que una edición «arregle» un parte no apto. Si el humano prefiere solo
lectura, es un `:readonly` condicionado por una lista de cinco nombres en
`pipeline.js`, con su test.

Lo que **no** cambia en el front: `cuerpoDeArchivo`, `cuerpoDeGrafico` y el
cuerpo de `cerrar` (R30). Nada de lo nuevo sale hacia SharePoint ni hacia el
ERP.

### D-J · El acceso del datamart queda fuera, y se dice cómo sería

PostgreSQL **no consulta entre bases**: `sigrid_dm` no puede hacer `SELECT`
sobre `postventa.v_partes_sigrid` sin una segunda conexión o una extensión.
Las dos vías, para que la petición (§12) las lleve escritas:

- **(a) Una conexión más del ETL del datamart a la base `postventa`**, con un
  rol de solo lectura propio —por ejemplo `postventa_datamart_ro`— que tenga
  `CONNECT` a la base, `USAGE` en el schema y **`SELECT` únicamente sobre la
  vista**, nunca sobre las tablas. Con la vista en su modo por defecto
  (`security_invoker = false`), quien la consulta lee con los privilegios del
  **dueño** de la vista (`postventa_app`, que es quien aplica el DDL), así que
  ese rol **no podría** leer `partes.dni_cliente` ni `partes.observaciones` ni
  aunque lo intentara **[INFERIDO de la documentación de PostgreSQL 16, no
  probado contra el servidor]**. Su nocturna la ingiere como una tabla más de
  `raw` (`raw.postventa_partes`, o el nombre que ellos elijan).
- **(b) `postgres_fdw`** desde `sigrid_dm`: exige `CREATE EXTENSION` **en su
  base** y una tabla foránea; es una decisión suya y de plataforma.

**Recomendación: (a).** Es lo que ya hace el propio datamart con `mcp-bbdd`
(un rol de lectura por consumidor) y lo que `red_postgresql_compartido.md` §5
señala como mejora pendiente («rol propio por consumidor y `REVOKE` de lo que
no le toca»).

**Y lo que este repositorio no puede hacer, con todas las letras:** crear ese
rol y darle permisos son `CREATE ROLE` y `GRANT`, sentencias de ámbito de
servidor que `CLAUDE.md` prohíbe a la aplicación y que `ddl.py` rechaza antes
de abrir la conexión. Solo puede hacerlo **el humano, a mano, una vez**, como
hizo con `infra/crear_base_postventa.ps1`. Se propone que eso sea una feature
propia —«rol de lectura del datamart sobre `v_partes_sigrid`», un script
`infra/` con confirmación escrita que crea el rol y los tres `GRANT` y que
**no toca nada más**— que el líder da de alta si el humano acepta la petición.
`CREATE OR REPLACE VIEW` **conserva los `GRANT`** existentes (a diferencia del
`DROP` + `CREATE` del datamart) **[INFERIDO de la documentación]**, así que
una vez concedido el permiso, las ampliaciones de la vista no lo pierden.

### D-K · Cómo se comprueba la vista contra la base real: un script de solo lectura

**Decidido:** `infra/18_vista_partes_sigrid.ps1`, al modo de
`17_traza_grafico_local.ps1`: `psycopg` desde el `.venv`, contraseña por
`SecureString`, **solo `SELECT`** sobre `information_schema.columns` y sobre
la vista, solo del schema propio. Imprime la lista ordenada de columnas y la
compara con la del contrato; cuenta filas; enseña, de un `hash` dado, **solo
claves y estados** (nunca campos de texto del parte, para que la salida de
consola no sea un fichero con datos de una vivienda); y comprueba que
`dni_cliente` no aparece entre las columnas. Es M2 de `tasks.md`.

## 3 · Ficheros a crear

Todos bajo `services/postventa-api/`, salvo donde se indique.

| Ruta | Capa | Qué contiene |
|---|---|---|
| `infrastructure/persistencia/sql/10_partes_campos_datamart.sql` | infra/SQL | Diez `ALTER TABLE postventa.partes ADD COLUMN IF NOT EXISTS ...` (§8.1) |
| `infrastructure/persistencia/sql/11_cierres_reclamacion_ide.sql` | infra/SQL | Un `ALTER TABLE postventa.cierres ADD COLUMN IF NOT EXISTS reclamacion_ide integer` (§8.2) |
| `infrastructure/persistencia/sql/12_v_partes_sigrid.sql` | infra/SQL | `CREATE OR REPLACE VIEW postventa.v_partes_sigrid AS ...` (§8.3) |
| `infra/18_vista_partes_sigrid.ps1` | infra | Solo lectura contra la base desplegada (D-K) |

### Tests a crear (`services/postventa-api/tests/`)

| Fichero | Requisitos |
|---|---|
| `test_f024_extraccion_campos.py` | R1, R2, R3 (con `validar_parte` real sobre extracciones inventadas: los cinco campos vacíos o llenos no mueven el veredicto), R6, R8 |
| `test_f024_prompt.py` | R4 (el YAML real describe los cinco nombres; `version == "2"`; sin patrón de DNI ni nombre real), R5 (la huella de `firma_parte_es` **no** cambia: se escribe a mano su huella actual, medida al arrancar la tarea) |
| `test_f024_ddl_columnas.py` | R9, R12, R14, R28: los tres ficheros reales pasan la guarda; diez `ALTER` sobre `partes` con el tipo esperado; el orden de ficheros; `cargar_ddl` del conjunto |
| `test_f024_persistencia.py` | R10 (28 columnas, un marcador por columna en `upsert_parte`), R11 (la fila antigua «cabe»: un `ExtraccionParte` con los cinco campos `None`/`0` se guarda sin error), R13 (`_traza` de `paso_cierre` lleva `reclamacion_ide` en los cuatro estados; `upsert_cierre` lo escribe como parámetro) |
| `test_f024_vista.py` | R15–R27 sobre el **texto real** del `.sql`: lista ordenada de columnas escrita a mano; los doce campos con confianza derivados de `CAMPOS_DEL_PARTE` menos `dni_cliente`/`observaciones`; `dni` ausente de la sentencia; `oid`, `motivo`, `usuario_oid`, `confirmado_por` ausentes; cuatro `LEFT JOIN` por `hash_parte`, ningún `WHERE`, ningún `DISTINCT`; `COALESCE` de las dos claves; `btrim` en `tiene_observaciones` |
| `test_f024_documentacion.py` | R33, R34: `INTEGRACION.md` nombra la vista, «una fila por parte», «sin `dni_cliente`», `tiene_observaciones`, «solo se añaden columnas al final», `datamart-seg-anual` y el rol de lectura como fuera de alcance; `ARCHITECTURE.md` nombra los cinco campos en el paso 3 y la vista; ningún host ni valor de secreto |
| `test_f024_scripts_infra.py` | El script 18 existe, solo `SELECT`, solo `information_schema` y `postventa.v_partes_sigrid`, sin valores, y **no selecciona** ninguna columna de texto del parte en la fila de muestra |

En `services/postventa-front/`: los tests existentes de `tests_js/pipeline.test.js`
y `tests_js/persistencia.test.js` se adaptan a catorce (censo a mano y
fixtures), y `tests_js/grafico.test.js` / `api.test.js` fijan que los cuerpos de
archivar, adjuntar y cerrar **no** llevan ninguno de los cinco nombres nuevos
(R30).

## 4 · Ficheros a modificar

| Ruta | Qué cambia |
|---|---|
| `domain/models/extraccion.py` | `CAMPOS_DEL_PARTE`: cinco nombres al final; `CAMPOS_MANUSCRITOS`: `hora_inicio`, `hora_fin`; los docstrings dejan de decir «nueve» y explican que los cinco **no deciden** |
| `domain/models/persistencia.py` | `TrazaCierre.reclamacion_ide: int \| None = None`, con el mismo comentario que en `TrazaGrafico` |
| `application/pipelines/paso_cierre.py` | `_traza(...)`: `reclamacion_ide=plan.reclamacion.ide`. **Una línea.** Nada más del módulo se toca (sigue sin nombrar `rcg` ni `gra`) |
| `infrastructure/persistencia/sentencias.py` | `upsert_cierre`: `reclamacion_ide` en `columnas` (detrás de `numero_incidencia`) y `traza.reclamacion_ide` en `parametros`, en la misma posición |
| `config/prompts.yaml` | `parte_posventa_es`: `version: "2"`; en `task`, la lista pasa a «catorce campos» con cinco líneas nuevas (§7.1); la regla 1 ya nombra las horas como vacías normales y se mantiene. `firma_parte_es` **intacto** |
| `tests/utiles_ia.py` | `CAMPOS_DE_EJEMPLO` gana los cinco con valores inventados (`Fontanería`, `INDUSTRIAL DE PRUEBA S.L.`, `baño`, `None`, `None`) |
| `tests/test_f003_extraccion_dominio.py` | El `CAMPOS_MANUSCRITOS ==` escrito a mano; el test de R1 sigue comprobando el prefijo de ocho |
| `tests/test_f003_paso_extraccion.py` | `len(CAMPOS_DEL_PARTE) == 14` y los «nueve» de los docstrings. El censo de `ContextoParte` **no cambia** (R8) |
| `tests/test_f004_prompts_firma.py` | `HUELLA_DEL_PROMPT_MEDIDO` (nueva, con comentario que cite F-024 y M1) y `CAMPOS_DEL_PARTE_A_MANO` a catorce; `version == "2"` |
| `tests/test_f005_mapeo.py` | `COLUMNAS_ESPERADAS` a veintiocho, escritas a mano |
| `tests/test_f005_ddl_idempotente_texto.py` | La lista de ficheros de `test_f005_r1_se_aplican_todos_los_ficheros_en_orden` gana los tres; el docstring lo cuenta |
| `tests/test_f005_sentencias.py`, `tests/test_f009_paso_cierre.py`, `tests/test_f005_repositorio.py` | Solo si alguna aserción cuenta parámetros de `upsert_cierre` o compara `TrazaCierre` campo a campo; se ajusta citando R13 |
| `tests/test_f005_repo_sin_datos_personales.py` | `DIRECTORIOS_BARRIDOS` gana `specs/F-024-datos-parte-sigrid` (R32) |
| `services/postventa-front/js/pipeline.js` | `CAMPOS_DEL_PARTE` a catorce, en el orden del dominio; comentario «nueve» → «catorce» |
| `services/postventa-front/tests_js/pipeline.test.js`, `persistencia.test.js` (y cualquier fixture con los nueve campos) | Censo a mano a catorce; fixtures con los cinco campos nuevos |
| `docs/ARCHITECTURE.md` | Paso 3: los catorce campos, y que los cinco nuevos existen para el datamart y no deciden; fila de PostgreSQL: «y la vista `postventa.v_partes_sigrid`, contrato de lectura para el datamart» |
| `docs/INTEGRACION.md` | §2 (árbol: las nueve tablas —hoy faltan `usuarios_sigrid` y `graficos`— y la vista), §7 (la vista no expone DNI ni texto manuscrito), **§8 nueva subsección** «Lo que exponemos al datamart» (§15), §9 (dónde está la vista y el script 18). Cabecera: fecha y «última feature que lo tocó» |
| `azure-apps/postventa_incidencias.md` | Copia refrescada. **Otro repositorio**: commit local allí, sin push (M3) |

## 5 · Ficheros que NO se tocan

- **`infrastructure/persistencia/sql/01_*.sql` … `09_*.sql`** — lo que crece,
  crece con `ALTER` en ficheros nuevos (D-C).
- **`infrastructure/persistencia/ddl.py`, `arranque.py`, `mapeo.py`,
  `repositorio_pg.py`** — la guarda ya admite las tres formas; el mapeo se
  deriva de la tupla; el repositorio no lee la vista. Si al implementar
  pareciera necesario tocar `ddl.py`, **es una parada**: significaría que el
  DDL propuesto no tiene una de las cinco formas.
- **`application/pipelines/paso_extraccion.py`, `paso_validacion.py`,
  `paso_persistencia.py`, `paso_grafico.py`, `contexto_parte.py`** — recorren
  la tupla o no tocan campos (R8).
- **`domain/models/validacion.py`** — los cinco campos no deciden (R3); ni una
  regla nueva.
- **`domain/models/cierre.py`, `domain/ports/erp.py`,
  `infrastructure/sigrid/consultas.py`** — no se lee nada más del ERP (D-D).
- **`domain/models/schemas.py`, `infrastructure/llm/gemini.py`,
  `interface_adapters/api/cuerpos.py`, `extraer.py`, `parte.py`, `archivar.py`,
  `cerrar.py`, `adjuntar.py`, `function_app.py`** — derivan de la tupla o no
  la usan; ningún endpoint nuevo.
- **`config/prompts.yaml :: firma_parte_es`** — ni una coma (R5).
- **`services/postventa-front/index.html`, `css/styles.css`** — la tarjeta
  itera `CAMPOS` (D-I). Solo si P3 acaba en «solo lectura».
- **`infra/crear_base_postventa.ps1`** — el rol de lectura es otra feature (D-J).
- **`harness/*`, `CHECKPOINTS.md`, `progress/`, `harness/features.json`** —
  lo lleva el líder.
- **`muestras/`** — se lee en M1; no entra nada de ahí en el repositorio.

## 6 · Las firmas que importan

### Dominio (`domain/models/extraccion.py`)

```python
CAMPOS_DEL_PARTE: tuple[str, ...] = (
    "promocion", "codigo_obra", "unidad", "numero_incidencia",
    "fecha_servicio", "descripcion", "dni_cliente", "observaciones",
    "numero_pagina",
    # F-024 · para el datamart; ninguno decide el veredicto (F-004 no los mira)
    "oficio", "empresa", "estancia",          # impresos
    "hora_inicio", "hora_fin",                # manuscritos, casi siempre vacíos
)

CAMPOS_MANUSCRITOS: frozenset[str] = frozenset(
    {"fecha_servicio", "dni_cliente", "observaciones", "hora_inicio", "hora_fin"}
)
```

Nada más cambia en el dominio de la extracción: `CampoExtraido`,
`ExtraccionParte` y `campo()` valen igual para catorce.

### Dominio (`domain/models/persistencia.py`)

```python
@dataclass(frozen=True)
class TrazaCierre:
    hash_parte: str
    numero_incidencia: str
    estado: EstadoCierre
    #: El `con.ide` de la reclamación en el ERP (F-024). Se rellena ya en el
    #: dry-run; anulable por las filas anteriores a esta feature.
    reclamacion_ide: int | None = None
    estado_origen_sigrid: str | None = None
    ...  # el resto, sin cambios
```

Va con valor por defecto y **después** de `estado` para no romper ninguna
construcción posicional existente (todas son por nombre, pero el default lo
garantiza).

### Aplicación (`application/pipelines/paso_cierre.py`)

```python
def _traza(ctx, plan, *, estado, usuario_oid, motivo=None,
           dry_run_at_utc=None, cerrado_at_utc=None) -> TrazaCierre:
    return TrazaCierre(
        hash_parte=ctx.parte.hash,
        numero_incidencia=plan.reclamacion.codigo,
        estado=estado,
        reclamacion_ide=plan.reclamacion.ide,          # F-024, R13
        ...
    )
```

Las cuatro salidas del paso (`dry_run_ok`, `error`, `ya_cerrada`, `cerrado`)
pasan por `_traza` con un plan **[MEDIDO en código]**, así que todas llevan el
`ide`.

### Infraestructura (`infrastructure/persistencia/sentencias.py`)

`upsert_cierre`: `columnas = ("hash_parte", "numero_incidencia",
"reclamacion_ide", "estado", ...)` y `traza.reclamacion_ide` en la misma
posición de `parametros`. El `WHERE {tabla}.estado <> %s` sigue igual (R25 de
F-005).

`upsert_parte`, `columnas_de_campos`, `valores_de_campos`: **sin cambios de
código**; producen veintiocho por recorrer la tupla.

### Front (`js/pipeline.js`)

`CAMPOS_DEL_PARTE`: los catorce, en el orden del dominio. Todo lo demás
(`cuerpoDeValidacion`, `cuerpoDeParte`, `aplicarEdiciones`, `esDudoso`) itera
esa lista y no cambia.

## 7 · Dónde entra cada campo en el pipeline

```
papel ──▶ Gemini (schema de 14 `required`, generado de CAMPOS_DEL_PARTE)
      ──▶ paso_extraccion._completar_y_sanear  (recorre CAMPOS_DEL_PARTE: 14)
      ──▶ ContextoParte.extraccion.campos      (14 claves; el contexto NO gana campos)
      ──▶ /api/extraer  ──▶ front: tarjeta (14) ──▶ /api/validar (exige 14; F-004 mira 2 + firma + observaciones)
      ──▶ /api/parte    ──▶ paso_persistencia ──▶ upsert_parte (28 columnas de campos)
                                                     └─▶ postventa.partes  ──▶ v_partes_sigrid
/api/cerrar (dry-run) ──▶ paso_cierre._traza(reclamacion_ide) ──▶ upsert_cierre ──▶ postventa.cierres ─┘
```

### 7.1 · Lo que dice el prompt de los cinco campos (contenido normativo)

Escrito contra `docs/referencia/02_parte_de_trabajo.md`, sin datos reales.
En `task`, la lista pasa a «catorce campos, y solo estos catorce», con:

- `oficio`: el oficio impreso del bloque «PROFESIONAL Y SERVICIOS ASIGNADOS»
  (por ejemplo `Albañilería`, `Fontanería`), literal.
- `empresa`: la empresa impresa, el industrial asignado a la reparación,
  literal y con su forma jurídica si la imprime.
- `estancia`: la estancia impresa (por ejemplo `jardín`, `baño`), literal.
- `hora_inicio`, `hora_fin`: las horas **MANUSCRITAS** («Hora inicio», «Hora
  finalización») del bloque «SERVICIO REALIZADO Y CONFORME», tal y como estén
  escritas, sin normalizar a `HH:MM`. Casi siempre vacías: `null` y `0`.

Las reglas 1–5 del prompt se mantienen; la regla 1 ya dice que «las horas» en
blanco son normal. La regla 5 («no devuelvas ningún campo que no esté en la
lista») sigue valiendo con la lista ampliada.

**No se toca el `system`** salvo la enumeración del bloque impreso, que ya
nombra «oficio, empresa». Cuanto menos cambie la redacción medida, menos
riesgo de que los nueve de siempre se lean peor; M1 es quien lo comprueba.

## 8 · El SQL

Los tres ficheros, en el schema `postventa`, con cabecera según
`docs/CONVENTIONS.md`, idempotentes, y **todos pasan la guarda de `ddl.py` sin
cambiarla**: `_validar_alter_table` exige `ALTER TABLE <esquema>.<tabla> ADD
COLUMN IF NOT EXISTS <col> ...` (una columna por sentencia) y
`_validar_create_view` exige `CREATE OR REPLACE VIEW <esquema>.<vista>`.

Dos cuidados de redacción que impone la guarda: ningún alias ni literal puede
ser la palabra `lo` ni `oid` (`TIPOS_PROHIBIDOS` busca `\bLO\b` y `\bOID\b`
sobre el texto en mayúsculas), y ninguna sentencia puede nombrar `public.`.
Los comentarios `--` se eliminan antes de validar, así que la cabecera puede
explicar libremente.

### 8.1 · `10_partes_campos_datamart.sql`

```sql
-- services/postventa-api/infrastructure/persistencia/sql/10_partes_campos_datamart.sql
-- Construye: las diez columnas de los cinco campos que F-024 añade al
-- contrato de extracción (oficio, empresa, estancia, hora_inicio, hora_fin),
-- con su confianza. Lee de: 03_partes.sql.
--
-- ALTER TABLE ... ADD COLUMN IF NOT EXISTS y no un CREATE TABLE editado: la
-- tabla ya existe en la base desplegada y un CREATE ... IF NOT EXISTS no la
-- tocaria. Es el patron del ecosistema para lo que crece, y la unica forma de
-- ALTER que admite ddl.py. Una columna por sentencia, en el orden de
-- CAMPOS_DEL_PARTE, que es el orden de columnas_de_campos().
--
-- Ninguno de los cinco decide nada (F-004 no los mira): existen para que el
-- datamart pueda enriquecer el parte con lo que el cierre en Sigrid no
-- registra. Las horas son MANUSCRITAS y vienen vacias en toda la remesa real;
-- se guardan como text, literal, igual que fecha_servicio.
--
-- Las filas anteriores a esta feature quedan con NULL y 0: no se reextraen.
-- Lo que las distingue de un parte leido con el prompt v2 y el campo en
-- blanco es prompt_version ("1" frente a "2").
--
-- DATO PERSONAL: ninguna de estas columnas lo es. empresa es una razon
-- social; oficio y estancia son catalogo; las horas no identifican a nadie.

ALTER TABLE postventa.partes ADD COLUMN IF NOT EXISTS oficio                    text;
ALTER TABLE postventa.partes ADD COLUMN IF NOT EXISTS oficio_confianza_pct      integer NOT NULL DEFAULT 0;
ALTER TABLE postventa.partes ADD COLUMN IF NOT EXISTS empresa                   text;
ALTER TABLE postventa.partes ADD COLUMN IF NOT EXISTS empresa_confianza_pct     integer NOT NULL DEFAULT 0;
ALTER TABLE postventa.partes ADD COLUMN IF NOT EXISTS estancia                  text;
ALTER TABLE postventa.partes ADD COLUMN IF NOT EXISTS estancia_confianza_pct    integer NOT NULL DEFAULT 0;
ALTER TABLE postventa.partes ADD COLUMN IF NOT EXISTS hora_inicio               text;
ALTER TABLE postventa.partes ADD COLUMN IF NOT EXISTS hora_inicio_confianza_pct integer NOT NULL DEFAULT 0;
ALTER TABLE postventa.partes ADD COLUMN IF NOT EXISTS hora_fin                  text;
ALTER TABLE postventa.partes ADD COLUMN IF NOT EXISTS hora_fin_confianza_pct    integer NOT NULL DEFAULT 0;
```

`NOT NULL DEFAULT 0` en las confianzas, como las nueve de `03_partes.sql`:
`upsert_parte` las escribe siempre, y las filas existentes reciben el `0` sin
reescritura de la tabla **[INFERIDO: PostgreSQL ≥ 11 guarda el default en el
catálogo; en cualquier caso el volumen es de decenas de filas]**.

### 8.2 · `11_cierres_reclamacion_ide.sql`

```sql
-- services/postventa-api/infrastructure/persistencia/sql/11_cierres_reclamacion_ide.sql
-- Construye: la clave estable del ERP en la traza del cierre (F-024).
-- Lee de: 06_cierres.sql.
--
-- reclamacion_ide es el con.ide de la reclamacion, el mismo que
-- postventa.graficos guarda desde F-012 y por el mismo motivo: es la clave
-- con la que el datamart cruzara nuestras filas, mientras que
-- numero_incidencia (con.cod) es legible pero no es clave. Se rellena desde el
-- primer dry-run (paso_cierre lo lee de la reclamacion). Anulable: las filas
-- anteriores a esta feature no lo tienen, y no se inventa.

ALTER TABLE postventa.cierres ADD COLUMN IF NOT EXISTS reclamacion_ide integer;
```

### 8.3 · `12_v_partes_sigrid.sql`

```sql
-- services/postventa-api/infrastructure/persistencia/sql/12_v_partes_sigrid.sql
-- Construye: la vista de lectura postventa.v_partes_sigrid, UNA FILA POR
-- PARTE, para que el datamart (sigrid_dm, mismo servidor, otra base) enriquezca
-- los partes de posventa con lo que el cierre en Sigrid no registra (F-024).
-- Lee de: 03_partes.sql, 04_validaciones.sql, 05_archivos.sql, 06_cierres.sql,
-- 09_graficos.sql, 10_partes_campos_datamart.sql, 11_cierres_reclamacion_ide.sql.
--
-- ES UN CONTRATO. El orden de las columnas es fijo y solo se anaden columnas
-- AL FINAL: CREATE OR REPLACE VIEW rechaza quitar, renombrar o reordenar, y un
-- DROP VIEW (que la guarda no admite) se llevaria los GRANT del rol de lectura.
--
-- LEFT JOIN a las cuatro trazas por hash_parte, que es clave primaria en
-- todas: la vista no puede multiplicar filas, y un parte sin validacion, sin
-- archivo, sin grafico o sin cierre sale igualmente con ese bloque a NULL.
--
-- LO QUE NO LLEVA, a proposito: el DNI del cliente (ni su confianza, ni un
-- booleano), el texto de las observaciones manuscritas (solo si las hay y con
-- que confianza), el oid de ningun empleado, los motivos de texto libre y
-- ningun byte. El dato personal directo vive en postventa.partes y en ningun
-- otro sitio (F-005, R39); esta vista es una segunda superficie para otro rol
-- y otro proyecto, y no lo copia.
--
-- gra_cod LLEVA DENTRO EL LOGIN DEL ERP de quien confirmo (sello + 4 digitos +
-- '.login'): es el identificador del grafico tal y como Sigrid lo genera y con
-- el que se casa la pareja negocio/documental. gra_ide_negocio va al lado como
-- clave numerica sin login.
--
-- numero_incidencia es lo que leyo el modelo del papel (puede faltar o traer
-- un guion raro); numero_incidencia_sigrid es el con.cod que devolvio el ERP
-- en el dry-run, y NULL significa "nunca hubo dry-run".

CREATE OR REPLACE VIEW postventa.v_partes_sigrid AS
SELECT
    -- identidad y claves de Sigrid
    p.hash_parte,
    COALESCE(g.reclamacion_ide, c.reclamacion_ide)     AS reclamacion_ide,
    COALESCE(c.numero_incidencia, g.numero_incidencia) AS numero_incidencia_sigrid,
    g.gra_cod,
    g.gra_ide_negocio,
    g.rcg_ide,
    -- los campos leidos del parte, en el orden del contrato, con su confianza
    p.promocion,                       p.promocion_confianza_pct,
    p.codigo_obra,                     p.codigo_obra_confianza_pct,
    p.unidad,                          p.unidad_confianza_pct,
    p.numero_incidencia,               p.numero_incidencia_confianza_pct,
    p.fecha_servicio,                  p.fecha_servicio_confianza_pct,
    p.descripcion,                     p.descripcion_confianza_pct,
    (p.observaciones IS NOT NULL AND btrim(p.observaciones) <> '') AS tiene_observaciones,
                                       p.observaciones_confianza_pct,
    p.numero_pagina,                   p.numero_pagina_confianza_pct,
    p.oficio,                          p.oficio_confianza_pct,
    p.empresa,                         p.empresa_confianza_pct,
    p.estancia,                        p.estancia_confianza_pct,
    p.hora_inicio,                     p.hora_inicio_confianza_pct,
    p.hora_fin,                        p.hora_fin_confianza_pct,
    -- la validacion (F-004)
    v.veredicto,
    v.destino,
    v.clasificacion_firma,
    v.validado_at_utc,
    -- el archivo en SharePoint (F-006)
    a.estado                                           AS archivo_estado,
    a.nombre_fichero                                   AS archivo_nombre_fichero,
    a.carpeta                                          AS archivo_carpeta,
    a.web_url                                          AS archivo_web_url,
    a.archivado_at_utc,
    -- el grafico en Sigrid (F-012)
    g.estado                                           AS grafico_estado,
    g.sha256                                           AS grafico_sha256,
    g.bytes                                            AS grafico_bytes,
    g.idempotente                                      AS grafico_idempotente,
    g.adjuntado_at_utc,
    -- el cierre en Sigrid (F-009)
    c.estado                                           AS cierre_estado,
    c.estado_origen_sigrid                             AS cierre_estado_origen_sigrid,
    c.estado_destino_sigrid                            AS cierre_estado_destino_sigrid,
    c.dry_run_at_utc                                   AS cierre_dry_run_at_utc,
    c.cerrado_at_utc,
    -- la traza del parte (F-002, F-003, F-005)
    p.remesa_id,
    p.modo_deteccion,
    p.primera_vez_at_utc,
    p.actualizado_at_utc,
    p.reprocesos,
    p.ia_modelo,
    p.prompt_version,
    p.prompt_huella
FROM postventa.partes p
LEFT JOIN postventa.validaciones v ON v.hash_parte = p.hash_parte
LEFT JOIN postventa.archivos     a ON a.hash_parte = p.hash_parte
LEFT JOIN postventa.graficos     g ON g.hash_parte = p.hash_parte
LEFT JOIN postventa.cierres      c ON c.hash_parte = p.hash_parte;
```

Cincuenta y nueve columnas. Si P1 acaba en (b), se añade **la última**:
`p.observaciones`.

#### Qué significa cada `NULL` (también va a `INTEGRACION.md` §8)

| Columna(s) | `NULL` significa |
|---|---|
| `reclamacion_ide`, `numero_incidencia_sigrid` | Nunca hubo dry-run de gráfico ni de cierre para este parte (o lo hubo antes de F-012/F-024 en el caso del `ide`). El parte se cruza con Sigrid por `numero_incidencia` (leído) + tipo 708, con la confianza que traiga |
| `gra_cod`, `gra_ide_negocio`, `rcg_ide` | El gráfico no llegó a `adjuntado` (o el `ide` no vino en la respuesta idempotente **[MEDIDO, F-012]**). Mirar `grafico_estado` |
| `veredicto`, `destino`, `clasificacion_firma`, `validado_at_utc` | El parte se guardó sin validación: hoy no ocurre por el front (guarda extracción y veredicto a la vez), pero la vista no lo supone |
| `archivo_*`, `archivado_at_utc` | No se ha intentado archivar (parte no apto, o pendiente de la ventana de escritura). `archivo_estado = 'error'` con `archivado_at_utc NULL` es un intento fallido |
| `grafico_*`, `adjuntado_at_utc` | No se ha intentado adjuntar. `grafico_estado` en `dry_run_ok` con `adjuntado_at_utc NULL` es un dry-run sin commit |
| `cierre_*`, `cerrado_at_utc` | No se ha intentado cerrar. `cierre_estado = 'ya_cerrada'` con `cerrado_at_utc NULL` es una reclamación que ya estaba cerrada antes de llegar nosotros |
| Un campo leído (`oficio`, `hora_inicio`, …) | El papel lo dejaba en blanco **o** el parte se leyó con `prompt_version = "1"`, que no lo pedía. Se distingue por esa columna |
| `numero_incidencia`, `codigo_obra` | El modelo no lo leyó: el parte está en revisión manual (`destino`) y no se cruza con Sigrid hasta que alguien lo corrija |

### 8.4 · Contra Sigrid, esta feature **no escribe ni lee nada nuevo**

`reclamacion_ide` sale de la misma `select_reclamacion` de F-009 que ya se
ejecuta en cada dry-run. Ni una consulta más al ERP, ni una fila más en
`dbo.log`.

## 9 · Compatibilidad hacia atrás

| Qué | Antes | Después | Cómo se garantiza |
|---|---|---|---|
| Filas de `partes` anteriores | 9 campos | 9 con valor + 5 a `NULL`/`0`, `prompt_version = "1"` | `ADD COLUMN IF NOT EXISTS` con `DEFAULT 0`; no se reextrae (D-B) |
| Filas de `cierres` anteriores | sin `reclamacion_ide` | `NULL` | Columna anulable; la vista usa `COALESCE` con `graficos` |
| `upsert_parte` sobre una fila antigua | — | Reprocesar rellena los 28 y sube `reprocesos` | R14–R16 de F-005, sin cambios |
| `POST /api/validar` y `/api/parte` | exigen 9 | exigen 14 | `cuerpos.a_extraccion` recorre la tupla. **El front y el backend se despliegan juntos**: un front viejo contra un backend nuevo recibiría `400` nombrando los cinco que faltan |
| `ContextoParte` | 9 campos del contexto | los mismos | R8; el censo de `test_f003_paso_extraccion` no se toca |
| El schema que ve el modelo | 9 `required` | 14 `required` | `schema_para` del dominio |
| Tests de F-003/F-004/F-005 con censos a mano | 9 / 18 | 14 / 28 | Se actualizan citando F-024; **esa es su función** |
| La huella medida del prompt | `2306ac1d07f1` | la nueva | Se actualiza tras M1 |
| Reintentos del bloque 8 de F-009 y del bloque 9 de F-012 contra el ERP | — | igual: `cierres` gana una columna anulable y las trazas la rellenan | Los guiones no cambian; `infra/12_traza_cierre_local.ps1` sigue valiendo (no selecciona columnas que desaparezcan) |

## 10 · Encaje en la arquitectura, y límite de microservicio

- **`domain/`** cambia dos tuplas y un campo de dataclass. Sigue sin importar
  nada de infraestructura (`test_f003_arquitectura`, `test_f005_arquitectura`
  intactos).
- **`application/`** cambia una línea (`paso_cierre._traza`). Ningún paso
  nuevo: la vista no la lee nadie del servicio.
- **`infrastructure/persistencia/`** gana tres `.sql` y una columna en una
  sentencia. La guarda no cambia.
- **`interface_adapters/`** no cambia: ningún endpoint nuevo. La vista **no
  se expone por HTTP** —el consumidor es otra base del mismo servidor, no el
  front—, y eso es deliberado: exponerla por `/api/` convertiría a este
  servicio en una API para terceros, que `INTEGRACION.md` §8 dice que no es.
- **El front** cambia una lista.

**Límite de microservicio.** Todo lo de arriba es de este servicio. Lo que
**no** lo es, y se entrega como petición y no como código (D-J, §12): el rol
de lectura y los `GRANT` (son del humano, a nivel de servidor), la conexión y
la ingesta del ETL del datamart (son de `datamart-seg-anual`), y cualquier
vista o semántica en `sigrid_dm` (`_meta`, `raw`) que ellos quieran publicar
sobre nuestros datos. No se diseña nada de eso aquí.

## 11 · Riesgos, y alternativas descartadas

| Riesgo | Qué lo contiene |
|---|---|
| Que el prompt v2 lea **peor** los nueve de siempre | El `system` casi no cambia; la huella clavada obliga a M1 (barrido sobre los 22 partes reales, comparado con T18 de F-003); si empeora, se revisa la redacción antes de cerrar |
| Que el DDL nuevo no pase la guarda en producción | Los tests cargan los ficheros **reales** con `cargar_ddl` (R28); `arranque.py` los valida antes de bloquear nada |
| Que la vista multiplique filas | `LEFT JOIN` por claves primarias; test sobre el texto; M2 cuenta filas de la vista frente a `partes` |
| Que la vista exponga dato personal | Lista de columnas a mano en el test; `dni` ausente de la sentencia; sin `oid`, sin `motivo`; M2 comprueba `information_schema` |
| Que alguien reordene o quite una columna «para limpiar» | R27 y el test a mano; el `.sql` lo dice en su cabecera; `INTEGRACION.md` lo declara contrato |
| Que un consumidor lea `NULL` como «vacío en el papel» | `prompt_version` en la vista y la tabla de §8.3 en `INTEGRACION.md` |
| Que el datamart no pueda leer la vista | Fuera de alcance por decisión del humano; la petición (§12) lleva las dos vías y la recomendación |
| Que los censos a mano de los tests se «arreglen» sin pensar | Cada actualización cita F-024 en el commit y en el comentario; el reviewer lo mira |
| Que el front y el backend se desplieguen por separado | Se despliegan juntos (`docs/DESPLIEGUE.md`); si no, `400` explícito nombrando los campos |

**Alternativas descartadas:**

- Un `jsonb` para los campos nuevos (D-A).
- Un segundo prompt / segunda llamada de IA (D-B).
- Reextraer los partes antiguos automáticamente (D-B).
- Un solo fichero `.sql` para las tres piezas (D-C).
- `obra_ide` y `upv_ide` en las trazas (D-D).
- Exponer `observaciones` por defecto (D-F; P1).
- Exponer `motivo`, `motivos`, `avisos`, `oid` (D-G).
- Una vista materializada: no hay volumen que lo justifique (decenas de
  filas) y exigiría `REFRESH`, que la guarda no admite.
- Un endpoint HTTP que sirva la vista (§10).
- Crear el rol de lectura desde este repositorio (D-J: `CREATE ROLE` y
  `GRANT` son del humano).
- `security_invoker = true` en la vista: obligaría a dar `SELECT` sobre las
  tablas al rol del datamart, que es justo lo que se quiere evitar.

## 12 · La petición al proyecto `datamart-seg-anual` (texto listo para enviar)

> **De** `postventa-incidencias` **a** `datamart-seg-anual`. Fecha: la de la
> aprobación de esta spec. Se copia a `azure-apps/postventa_incidencias.md` §8
> (M3) y de ahí la lee su dueño.
>
> **Qué os ofrecemos.** Una vista de lectura, `postventa.v_partes_sigrid`, en
> la base `postventa` del mismo servidor `psql-albaranes-rs9k2`. **Una fila
> por parte de posventa** procesado por nuestro servicio (grano `hash_parte`),
> con lo que el cierre en Sigrid no registra: quién reparó (`empresa`), qué
> oficio, en qué estancia, a qué hora (si el técnico lo anotó), cómo se
> clasificó la firma del cliente, si hubo observaciones manuscritas, a dónde
> mandó el parte la validación, y el estado y las fechas de su archivo en
> SharePoint (con la URL), de su gráfico y de su cierre en Sigrid.
>
> **Con qué claves se cruza con vuestra copia de Sigrid.**
> `reclamacion_ide` = `con.ide` de la reclamación (`tip = 708`). Cuando es
> `NULL` (el parte nunca pasó por un dry-run), `numero_incidencia_sigrid` o
> `numero_incidencia` = `con.cod`, único dentro del tipo 708. `codigo_obra` =
> `con.cod` de la obra, el mismo de vuestra `_meta.v_frescura_obra`. De la
> reclamación llegáis a la unidad y a la obra con `rcp.upvide → upv.obride`.
> Del gráfico, `gra_ide_negocio` = `ruesma.gra.ide` y `gra_cod` = `gra.cod`
> (que lleva dentro el login del ERP de quien confirmó).
>
> **Lo que NO lleva, y no llevará sin una decisión escrita**: el DNI del
> cliente, el texto de las observaciones manuscritas (solo
> `tiene_observaciones` y su confianza), ningún identificador de empleado, y
> ningún binario. Es dato personal y vive en una sola tabla de nuestra base.
>
> **Reglas de compatibilidad**: el orden de las columnas es fijo; solo
> añadimos columnas al final; no renombramos ni quitamos; cualquier cambio se
> anuncia en `azure-apps/postventa_incidencias.md` antes de desplegarse.
> `prompt_version` distingue los partes leídos con el contrato de catorce
> campos (`"2"`) de los anteriores (`"1"`, con los cinco nuevos a `NULL`).
> `actualizado_at_utc` es la frescura por fila.
>
> **Volumen**: decenas de filas hoy, cientos al año. Una remesa son ~22 partes.
>
> **Lo que os toca a vosotros, y no podemos hacer desde aquí**: PostgreSQL no
> cruza bases. La vía que recomendamos es la que ya usáis con `mcp-bbdd`: un
> rol de solo lectura propio (`postventa_datamart_ro`, o el nombre que
> prefiráis) con `CONNECT` a `postventa`, `USAGE` sobre el schema y `SELECT`
> **solo sobre la vista** —con eso no puede leer las tablas—, y una segunda
> conexión de vuestro ETL que la ingiera como una tabla más de `raw`. El rol y
> los `GRANT` los crea el humano a mano (son de ámbito de servidor y nuestra
> aplicación tiene prohibido ejecutarlos); pedidlo cuando queráis empezar y se
> abre la feature que lo hace. La alternativa `postgres_fdw` desde `sigrid_dm`
> es decisión vuestra y de plataforma.
>
> **Qué necesitamos saber de vosotros**: si `rcp` y `upv` van a entrar en
> vuestra ingesta (hoy no constan), qué nombre queréis para la tabla `raw`, y
> si queréis que expongamos algo más (por ejemplo los códigos de motivo de la
> validación, o la clasificación de las observaciones cuando exista F-016).
> Todo eso serían columnas al final.

## 13 · Preguntas abiertas (con recomendación)

| # | Pregunta | Opciones | Recomendación |
|---|---|---|---|
| **P1** | ¿La vista expone el **texto** de `observaciones`? Es el dato más valioso para el datamart y puede llevar nombres | (a) **No**: `tiene_observaciones` + `observaciones_confianza_pct` (el diseño de §8.3); (b) **Sí**: además, `observaciones` como **última** columna | **(a)**. Es dato personal directo (F-005 §6, decisión D2 del humano) y la vista la leerá otro rol de otro proyecto; el datamart ya arrastra un aviso propio por `raw.emp`/`raw.res`. Lo que de verdad enriquece un parte —si hubo objeción y a dónde fue— lo da el booleano y `destino`. Y cuando F-016 clasifique las observaciones, **esa** clasificación es lo que conviene exponer, no el texto. Si el humano elige (b), es una columna al final y una fila más en la tabla de datos personales de `INTEGRACION.md` §7 |
| **P2** | ¿Se guardan también `obra_ide` y `upv_ide`? | (a) No; (b) Sí, extendiendo la consulta de F-009 | **(a)**, por D-D. Reversible mañana con una columna al final |
| **P3** | ¿Los cinco campos nuevos en la tarjeta del front son editables o solo lectura? | (a) Editables, misma plantilla; (b) Solo lectura (`:readonly` por lista) | **(a)**, por D-I: cero código nuevo, y las horas manuscritas son las que más corrección necesitan. El líder sugería (b); no cambia nada del backend |
| **P4** | El encuadre del líder dice «sin campaña de mutación» para `estandar`, pero `harness/rigor.json` declara `mutacion: true` para ese nivel (con `supervivientes_maximos: null`) y `CHECKPOINTS.md` la exige | (a) Seguir `rigor.json`: campaña, supervivientes documentados, sin exigir cero; (b) Cambiar `rigor.json` (vale para todas las features y viaja a `arnes-base`) | **(a)**. La herramienta es la que valida el nivel y un N/A sin motivo es checkbox vacío. `tasks.md` la incluye como T13 |
| **P5** | ¿Se rellenan los partes del piloto ya guardados con `prompt_version = "1"`? | (a) No, quedan `NULL`; (b) Reprocesar la remesa de Mirasierra por el front (22 llamadas de IA; sin duplicar) | **(a)** para cerrar la feature; (b) queda disponible y es decisión de Posventa/humano según cuántos partes diga Q1 (§14). No bloquea |
| **P6** | Nombre del rol de lectura y de la feature que lo crea | `postventa_datamart_ro`; «F-0XX · Rol de lectura del datamart sobre `v_partes_sigrid`» | Lo da de alta el líder si el humano acepta la petición de §12 |

Ninguna cambia la estructura del diseño: P1 y P3 son una columna o un
atributo; P2 y P5 son «no hacer»; P4 es del arnés; P6 es calendario.

## 14 · Consultas preparadas (solo lectura; **no se han ejecutado**)

Para la base `postventa` del servidor compartido, desde el entorno que el
humano decida (`infra/18_vista_partes_sigrid.ps1` las empaqueta, salvo Q1 que
va antes de desplegar). Ninguna escribe.

```sql
-- Q1 · cuántos partes quedarán con los campos nuevos a NULL (antes de desplegar)
SELECT prompt_version, COUNT(*) AS partes
FROM postventa.partes
GROUP BY prompt_version
ORDER BY prompt_version;
```

```sql
-- Q2 · la vista existe y sus columnas son las del contrato, en su orden
SELECT ordinal_position, column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'postventa' AND table_name = 'v_partes_sigrid'
ORDER BY ordinal_position;
```

```sql
-- Q3 · una fila por parte, de verdad
SELECT (SELECT COUNT(*) FROM postventa.partes)          AS partes,
       (SELECT COUNT(*) FROM postventa.v_partes_sigrid) AS filas_vista;
```

```sql
-- Q4 · las diez columnas nuevas existen en partes y la de cierres también
SELECT table_name, column_name, data_type, column_default
FROM information_schema.columns
WHERE table_schema = 'postventa'
  AND (
        (table_name = 'partes'  AND column_name IN ('oficio', 'oficio_confianza_pct',
                                                     'empresa', 'empresa_confianza_pct',
                                                     'estancia', 'estancia_confianza_pct',
                                                     'hora_inicio', 'hora_inicio_confianza_pct',
                                                     'hora_fin', 'hora_fin_confianza_pct'))
     OR (table_name = 'cierres' AND column_name = 'reclamacion_ide')
      )
ORDER BY table_name, column_name;
```

```sql
-- Q5 · un parte nuevo procesado tras el despliegue: claves y estados, sin texto del parte
SELECT hash_parte, codigo_obra, numero_incidencia_sigrid, reclamacion_ide,
       prompt_version,
       oficio IS NOT NULL      AS trae_oficio,
       empresa IS NOT NULL     AS trae_empresa,
       estancia IS NOT NULL    AS trae_estancia,
       hora_inicio IS NOT NULL AS trae_hora_inicio,
       tiene_observaciones, clasificacion_firma, destino,
       archivo_estado, grafico_estado, cierre_estado
FROM postventa.v_partes_sigrid
WHERE hash_parte = %s;
```

Q5 **no selecciona** `oficio`, `empresa` ni ningún texto del parte a
propósito: la salida de consola de un script no debe ser un fichero con datos
de una vivienda concreta.

## 15 · Qué cambia en la documentación

| Documento | Qué |
|---|---|
| `docs/ARCHITECTURE.md`, paso 3 | La lista de campos pasa a nombrar también oficio, empresa, estancia y las dos horas, con una frase: existen para el datamart (F-024) y **no deciden**; F-004 sigue mirando código de obra, nº de incidencia, firma y observaciones |
| `docs/ARCHITECTURE.md`, tabla de sistemas externos, fila PostgreSQL | «… y la vista `postventa.v_partes_sigrid`, contrato de lectura para `datamart-seg-anual` (F-024). La ve otro rol, nunca el front» |
| `docs/INTEGRACION.md` §2 | El árbol lista las **nueve** tablas (añade `usuarios_sigrid` y `graficos`, que faltan desde F-009/F-012) y la vista |
| `docs/INTEGRACION.md` §7 | Una línea: la vista no expone el DNI ni el texto manuscrito; solo `tiene_observaciones` |
| `docs/INTEGRACION.md` §8, subsección nueva **«Lo que exponemos al datamart: `postventa.v_partes_sigrid`»** | Grano, claves, lista de columnas por bloque, la tabla de `NULL` de §8.3, la regla «solo al final», la aclaración de `gra_cod`, y la petición de §12 con lo que queda fuera de nuestro alcance |
| `docs/INTEGRACION.md` §9 | Dónde está la vista (`12_v_partes_sigrid.sql`) y el script 18 |
| `azure-apps/postventa_incidencias.md` | Copia refrescada (M3, otro repositorio, commit local sin push). **No se toca `azure-apps/datamart_seg_anual.md`**: es de su dueño; que ellos anoten que nos consumen cuando lo hagan |
| `docs/referencia/` | Nada: ningún documento nuevo entra de fuera |
