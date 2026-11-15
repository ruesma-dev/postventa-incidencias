<!-- specs/F-072-tipo-reclamacion-sigrid/design.md -->
# F-072 · El tipo de reclamación sale de Sigrid (auxtrcp) de punta a punta — Diseño

> **Rigor: `critico`.** Disparadores de «Niveles de rigor» (`CHECKPOINTS.md`):
> **2** — escribe en producción y en lo compartido: el volcado manda a Sigrid
> (`POST /api/sigrid/partes-reclamacion`, ERP de producción) un `tipo` que deja
> de ser constante, y añade columnas en `psql-albaranes-rs9k2` (esquema
> `postventa`); **4** — cambia contratos: el esquema de dos tablas propias (las
> leerá el datamart, F-048) y los valores de `listado` en `/api/revision`.
> **Pendiente de aprobación** (§14). Base fija propuesta: `dev` `6994cb0`.

## 1 · Qué cambia, en una frase por punta

- **Plantilla**: `Listado` ofrece los tipos vigentes de `auxtrcp` leídos al
  descargar; el YAML pierde `listados`; misma hoja y versión 2. **Importación**:
  lee los tipos tras catálogo y ubicaciones, casa la celda y guarda el **código**
  (en blanco, `0002`).
- **Bandeja**: columna nueva `tipo_reclamacion` en `bandeja_incidencias` y en
  `revisiones_bandeja` (`17_tipo_reclamacion.sql`, `ALTER TABLE … ADD COLUMN IF
  NOT EXISTS`). `listado` se queda como dato heredado y deja de escribirse.
- **Revisión**: la lista y editar/aprobar leen los tipos; `catalogo.listados`
  los ofrece; `valores.listado` lleva el **tipo efectivo**; motivo nuevo
  `tipo_fuera_de_sigrid`.
- **Volcado**: `parte_de` manda el tipo efectivo; `TIPO_RECLAMACION` es el defecto.

Encaje (`docs/ARCHITECTURE.md`): la hexagonal de F-036/F-056. Un puerto de una
lectura como `UbicacionesValidasPort`, adaptador hijo de `AdaptadorCatalogoSigridApi`
y una **fuente** (callable) para la aplicación, como `FuenteUbicacionesValidas`.

## 2 · Límite de servicio (Q-4)

Todo cae en `services/postventa-api`. **El front no cambia**: `bandeja.html`
ya tiene un `<select>` «Listado» que se rellena con `catalogo.listados` y manda
`valores.listado` (`js/revision.js`, líneas ~486, 891, 1305). Si el backend
mantiene **la forma** del contrato —la clave `listado`, ahora con el código de
`auxtrcp`, y `catalogo.listados` con `{codigo, etiqueta}` de los tipos—, la
página publicada enseña los tipos y deja cambiarlos sin tocar una línea. No hay
que partir la ficha. Los retoques de texto del front (Q-11) van con F-040, que
ya toca `bandeja.html` y `js/volcado.js` al retomarse. Nada es de otro
microservicio: `sigrid-api` ya admite `tipo` y valida `fecbaj` (§8.9).

## 3 · Ficheros

### 3.1 · A crear (rutas bajo `services/postventa-api/`)

| Ruta | Qué |
|---|---|
| `domain/ports/tipos_reclamacion.py` | `FilaTipoReclamacion(codigo: str\|None, nombre: str\|None, posicion: int\|None)`; `TiposReclamacionPort.leer() -> LecturaCatalogo[FilaTipoReclamacion]` (reutiliza `LecturaCatalogo` de `catalogo_obra.py`) |
| `infrastructure/sigrid/consultas_tipos_reclamacion.py` | `SQL_TIPOS_RECLAMACION` (R2), `select_tipos_reclamacion()`, `fila_a_tipo_reclamacion(fila)` (3 columnas o `ValueError` sin la fila) |
| `infrastructure/sigrid/tipos_reclamacion.py` | `AdaptadorTiposReclamacionSigridApi(AdaptadorCatalogoSigridApi)`: `leer()` y el log de R30 |
| `application/pipelines/tipos_reclamacion.py` | `leer_tipos_reclamacion(puerto) -> tuple[TipoReclamacion, ...]` (R4, R5), `FuenteTiposReclamacion = Callable[[], tuple[TipoReclamacion, ...]]`, `fuente_de_tipos(puerto)` |
| `infrastructure/persistencia/sql/17_tipo_reclamacion.sql` | §7 |
| `tests/test_f072_dominio_tipos.py` | R6, R7, R14, R19, R26, R28 |
| `tests/test_f072_revision_dominio.py` | R21–R25, R27 |
| `tests/test_f072_lectura_sigrid.py` | R1–R5, R30 (consulta, mapeo, adaptador con `httpx` simulado, aplicación) |
| `tests/test_f072_ddl.py` | R16, R18 (con los `.sql` reales y la guarda) |
| `tests/test_f072_persistencia.py` | R15 y lectura/escritura de la columna en las sentencias (sin base) |
| `tests/test_f072_plantilla.py` | R6–R10 (generador real abierto con `openpyxl`, YAML real y rotos en `tmp_path`) |
| `tests/test_f072_importacion.py` | R11–R15 (dominio y pasos con dobles) |
| `tests/test_f072_revision_http.py` | R20–R24, R27 por los handlers con puertos inyectados |
| `tests/test_f072_volcado.py` | R28, R29 (cuerpo del lote; ensayo con un `tipo_no_valido` simulado) |
| `tests/test_f072_documentacion.py`, `tests/test_f072_alcance_cerrado.py` | R33; R31, R32 (patrón de `test_f071_alcance_cerrado.py`, base fija) |
| `tests_bbdd/tests/test_f072_bbdd_tipo.py` | R17 (MANUAL, base efímera) |

### 3.2 · A modificar

| Ruta | Qué cambia |
|---|---|
| `domain/models/plantilla_incidencias.py` | `TipoReclamacion(codigo, nombre)`; `TIPO_RECLAMACION_POR_DEFECTO = "0002"`; `MAX_TIPO_RECLAMACION = 24`; `tipos_del_desplegable(tipos) -> tuple[Opcion, ...]` (R6); `listas_con_tipos(listas, tipos) -> ListasCerradas` (`replace` de `listados`); `tipo_efectivo(codigo: str\|None) -> str` (R19). Docstring de `ListasCerradas`: `listados` llega vacío del YAML y lo rellena la aplicación con Sigrid |
| `domain/models/importacion.py` | `IncidenciaValida` e `IncidenciaEnBandeja` ganan `tipo_reclamacion: str\|None = None` (último campo); `validar_filas` guarda el código (R12) o el defecto (R14); `listado` se queda y vale `None` en lo nuevo (R15) |
| `domain/models/revision.py` | §4.2 |
| `domain/models/volcado.py` | `TIPO_RECLAMACION = TIPO_RECLAMACION_POR_DEFECTO` (alias, mismo nombre que usan los tests de F-059); `parte_de` con `tipo_efectivo(v.tipo_reclamacion)` (R28); docstrings («siempre 0002» fuera) |
| `application/pipelines/plantilla.py` | `generar_plantilla(..., tipos: FuenteTiposReclamacion)`: catálogo → ubicaciones → **tipos** → `listas_con_tipos` → `generador.generar` (sin cambiar su firma) |
| `application/pipelines/contexto_importacion.py`, `paso_importacion.py` | `paso_catalogo(contexto, catalogo_obra, ubicaciones, tipos)` guarda `contexto.tipos` (fuera del `repr`); `paso_validacion` y `paso_excel_errores` usan `listas_con_tipos` (R11, R13) |
| `application/pipelines/revision.py` | `listar_para_revisar(..., tipos)` y `aplicar_accion(..., tipos)` (solo en `_LEEN_SIGRID`): una lectura, tras catálogo y ubicaciones; `PaginaDeRevision.listas` ya con los tipos |
| `infrastructure/sigrid/fabrica.py` | `construir_tipos_reclamacion(ajustes) -> TiposReclamacionPort` (misma puerta de entorno que `construir_ubicaciones_validas`) |
| `infrastructure/documentos/plantilla_yaml.py` | sin `listados`; la clave en la raíz → error (R9); `_ejemplos` deja de validar `Listado` (R10) |
| `config/plantilla_incidencias.yaml` | §6.3 |
| `infrastructure/persistencia/sentencias_bandeja.py`, `sentencias_revision.py` | escriben y leen `tipo_reclamacion` (columnas, `INSERT`, mapeo); `listado` se sigue **leyendo** y se escribe `NULL` en la bandeja y la copia heredada en la revisión |
| `interface_adapters/api/plantilla.py`, `importar.py`, `revision.py` | componen `tipos=` (por defecto `fuente_de_tipos(construir_tipos_reclamacion(obtener_ajustes()))`); en `importar.py`, solo si el fichero se reconoció y no estaba importado (R11); `revision.py` serializa `listado` = tipo efectivo (R20) y lee `valores.listado` como código (§8) |
| `interface_adapters/api/bandeja.py` | `listado` = tipo efectivo (§8) |
| `domain/models/errores.py` | solo si hace falta el texto del error de R9 |
| `harness/servicios.json` | `tests/test_f072_documentacion.py` y `tests/test_f072_alcance_cerrado.py` en `ejecutar_siempre` de `api` (leen `docs/` y git; regla del propio fichero) |
| `docs/ARCHITECTURE.md`, `docs/INTEGRACION.md` | R33: sección «El tipo de reclamación (F-072)» y las frases «tipo 0002 siempre» de F-059 |
| Tests de F-036, F-056, F-059, F-060, F-071 que fijen `listados` del YAML, `Listado` al importar, la huella o «siempre 0002» | cada aserción que cambie se **cita** en `progress/impl_F-072.md` con el R que la sustituye; ninguna se borra sin sustituta |

### 3.3 · Que NO se tocan (R32)

`services/postventa-front/**` (Q-4); `infrastructure/sigrid/consultas_catalogo.py`,
`consultas_ubicaciones_validas.py`, `consultas_reclamaciones_obra.py`,
`catalogo_obra.py` (solo se hereda), `volcado.py` y `cliente.py`;
`application/pipelines/volcado.py` y `guarda_sigrid.py` (el tipo lo pone el
dominio); `infrastructure/persistencia/ddl.py` y `sql/13_`, `15_`, `16_*.sql`;
`infrastructure/documentos/excel_openpyxl.py` (recibe `Listado` como una lista
más, D-21 de F-071), `lector_aislado.py`, `ejecutor_aislado.py`; equivalencias;
F-065 (`sigrid_bandeja.*`); `function_app.py` salvo docstrings.

## 4 · Dominio

### 4.1 · Tipos y desplegable (`plantilla_incidencias.py`)

`tipos_del_desplegable`: etiqueta `"<nombre> (<codigo>)"` o `"<codigo>"`, en el
orden leído; recibe `TipoReclamacion` ya limpios (R5 es de `leer_tipos_reclamacion`).
`tipo_efectivo(None) == "0002"`; cualquier otro valor, tal cual.

### 4.2 · Revisión (`revision.py`)

- `ValoresIncidencia` gana `tipo_reclamacion: str | None = None` como **último**
  campo; `listado: Listado | None` se queda (heredado, ya no editable).
- `ValoresPedidos.listado` **conserva el nombre** (es la clave del JSON) y
  ahora es un código. `validar_valores`: `None` → `0002` (R22); el código
  exacto de `listas.listados`, o igual a `tipo_efectivo(vigentes.tipo_reclamacion)`
  → se guarda (R21); otro → `("listado", TIPO_NO_VALIDO)` con
  `TIPO_NO_VALIDO = "no es un tipo de reclamación vigente en Sigrid"`. Copia
  `listado` de los vigentes (R23); `_tasado` queda para urgencia.
- `MotivoNoAprobable.TIPO_FUERA_DE_SIGRID = "tipo_fuera_de_sigrid"`, entre
  `PROVEEDOR_AMBIGUO` y `DUPLICADA` (R24): `motivos_no_aprobable` recibe los
  códigos vigentes; con `None` (descartar, recuperar) no se calcula, como hoy.
- El campo lógico `listado` de `cambios` deja de salir de `_ATRIBUTOS_DE_CAMPO`:
  se compara `tipo_efectivo(v.tipo_reclamacion)` de las dos fotos (R25).
- `huella_de_valores` (R26): la lista de los 13 primeros campos como hoy y,
  **solo si** `tipo_reclamacion` no es `None`, el código al final. Un test fija
  la huella de una foto de ejemplo con el valor que da el código de `dev`
  `6994cb0` (literal en el test).

### 4.3 · Volcado (`volcado.py`)

Solo `parte_de` (R28) y el alias. `huella_intacta` no cambia: con R26, una
candidata anterior a F-072 sigue intacta y va con `0002`. Ni lectura nueva ni
motivo nuevo en el ensayo (R29): `tipo_no_valido` de `sigrid-api` ya es un
`rechazado` con su motivo, y el ensayo no escribe nada.

## 5 · Aplicación

`leer_tipos_reclamacion(puerto)`: al techo, `CatalogoSinVerificar` (R4);
`CatalogoNoDisponible` sube tal cual (R3); filtra y deduplica (R5). Orden en cada
petición: catálogo → ubicaciones → tipos (la más barata, al final). Plantilla,
importación con fichero nuevo, listado, editar y aprobar: 3 lecturas; descartar y
recuperar: 0 (R27). `normalizar_ubicaciones` (F-060) no lee tipos: copia con `replace`.

## 6 · Infraestructura

### 6.1 · La lectura

Adaptador delgado (compone, manda, mapea; **no decide**), con el techo de las
otras lecturas del catálogo. Log de R30 en la aplicación: `F-072 tipos de
reclamación leídos en Sigrid: tipos=%d sin_codigo=%d repetidos=%d al_techo=%s segundos=%.2f`.

### 6.2 · Persistencia

`sentencias_bandeja.py`: `tipo_reclamacion` en el `INSERT` y en `_COLUMNAS_LISTADO`;
`listado` a `NULL`. `sentencias_revision.py`: la columna en la foto y en los importados.

### 6.3 · YAML y textos (R9, R10)

- Fuera `listados` y su comentario; cabecera: «Las ubicaciones, los oficios, los
  proveedores y los tipos de reclamación (columna Listado) salen de Sigrid al
  descargar (F-071, F-072). La urgencia sí, porque Sigrid no tiene catálogo.»
- Instrucción: «Los desplegables de unidad, ubicación, oficio, proveedor y
  listado salen de Sigrid el día que descargas la plantilla.»
- `mensajes.Listado`: `titulo_entrada: Listado (tipo de reclamación)`;
  `entrada`: «Opcional: el tipo de reclamación de Sigrid, por ejemplo el primer o
  el segundo listado de repasos. Si lo dejas en blanco, entra como tipo 0002.»;
  `error`: «Ese valor no está en la lista. Elige el tipo del desplegable o déjalo
  en blanco.»
- Ejemplo 3: `Listado: "Tipo de reclamación (elígelo de la lista)"`, sin validar.

## 7 · SQL

`17_tipo_reclamacion.sql`, capa de persistencia, esquema `postventa`, lee de
`13_` y `15_`. Cabecera explicando: columna nueva y no un `CHECK` nuevo sobre
`listado` (la guarda no deja cambiar un `CHECK`); nulo = anterior a F-072
(tipo efectivo `0002`); sin `UPDATE` (la guarda tampoco lo admite: lo heredado
no se migra en la base, se interpreta en el dominio). Dos sentencias:

```sql
ALTER TABLE postventa.bandeja_incidencias ADD COLUMN IF NOT EXISTS tipo_reclamacion text CHECK (char_length(tipo_reclamacion) BETWEEN 1 AND 24);
ALTER TABLE postventa.revisiones_bandeja ADD COLUMN IF NOT EXISTS tipo_reclamacion text CHECK (char_length(tipo_reclamacion) BETWEEN 1 AND 24);
```

Columna nula sin defecto: solo catálogo, sin reescribir la tabla, pero con
bloqueo exclusivo breve y siendo **dueño**: primer `ALTER TABLE` en producción (Q-3).

## 8 · Contrato HTTP (sin cambio de forma)

| Dónde | Antes | Con F-072 |
|---|---|---|
| `GET /api/revision` `catalogo.listados` | 2 opciones del YAML (`primero`, `segundo`) | los tipos vigentes `{codigo, etiqueta}` (R20) |
| `valores.listado`, `importados.listado` | `primero`/`segundo`/`null` | el tipo efectivo, nunca `null` |
| `POST /api/revision/acciones` `valores.listado` | código del YAML o `null` | código de `auxtrcp` o `null` (= `0002`) (R21, R22) |
| motivos | 9 | 10: `tipo_fuera_de_sigrid` (R24) |
| `GET /api/bandeja` `listado` | `primero`/`segundo`/`null` | el tipo efectivo |
| cuerpo a `sigrid-api` §8.9 `tipo` | `0002` | el tipo efectivo (R28) |

## 9 · Compatibilidad

- **Front publicado**: sigue funcionando (§2); hasta Q-11 enseña «Sin listado»
  (al guardar, `0002`) y el motivo nuevo en crudo.
- **Aprobadas antes de F-072**: huella intacta (R26), van con `0002`, como hoy.
- **`listado` heredado** (`primero`/`segundo`): no se traduce (Q-2); se lee y
  se copia, no se enseña. Si hay alguna `segundo` sin volcar, Posventa la cambia
  en la revisión antes de aprobar.
- **Plantillas v2 ya repartidas** (Q-5): se aceptan; una celda «Primer listado»
  o «Segundo listado» vuelve en el Excel de errores, que ya trae la lista nueva;
  en blanco entra con `0002`.

## 10 · Riesgos (logs: solo recuentos y códigos de obra, R30)

- **Dueño de las tablas** (Q-3): si no lo es, el `ALTER` tumba el arranque de
  la Function → se mide en T0 y, si no es dueño, se para (nada a nivel de servidor).
- **Latencia** del listado de revisión (M2 de F-056: p50 5 s): una lectura más,
  de una tabla pequeña; se mide en T26 y se anota.
- **`0002` de baja en Sigrid** (Q-1): el blanco iría a `tipo_no_valido`. Si T0 lo
  ve de baja, se para y se vuelve al humano.
- **Tipos internos** que no deban verlos la propiedad (Q-1): se ofrecen todos los
  vigentes; filtrar sería otra ficha.
- **Tests que caducan** («tipo 0002 siempre» de F-059, `listados` del YAML): §3.2.

## 11 · Frontera

**¿Cruza la frontera del proyecto? Sí.**
- `sigrid-api`: una lectura nueva por `sql/read` (`dbo.auxtrcp`, que ya leía
  F-065 por `JOIN`) en plantilla, importación y revisión; y el `tipo` que
  mandamos a §8.9 deja de ser siempre `0002`. `sigrid-api` **no cambia**.
- `psql-albaranes-rs9k2`: dos columnas en el esquema propio (primer `ALTER
  TABLE`). Nada a nivel de servidor.
- Documentos (el **líder al desplegar**, con `git pull` antes): 
  `azure-apps/postventa_incidencias.md` (tablas, lecturas, «mandamos tipo
  `0002`») y la fila de consumidores de §8.9 en `azure-apps/sigrid_api.md`
  (como Q-6 de F-059); y su copia `docs/INTEGRACION.md` (implementer, R33).

## 12 · Decisiones

Trazabilidad: cada R tiene su `test_f072_rN_*` en el fichero de §3.1; R17 y R34
son MANUAL (`tasks.md` T13 y T26).

| Decisión | Opciones | Recomendado | Decidido |
|---|---|---|---|
| Q-1 · Los valores de `auxtrcp` (medición del líder: `SELECT cod, res, pos, fecbaj FROM dbo.auxtrcp ORDER BY pos, cod` por `sql/read`) | (a) ofrecer todos los vigentes; (b) una lista blanca de códigos | (a), y parar si `0002` no está vigente || (a), humano 2026-11-15. T0: 4 tipos, todos vigentes, `0002` entre ellos |
| Q-2 · `listado` heredado en la base (medición del líder: recuento por `listado` en `bandeja_incidencias` y en la última revisión de cada incidencia no volcada) | (a) no traducir: nulo = `0002`; (b) traducir `primero` → `0002` y `segundo` → el código que diga el humano | (a); si hay `segundo` sin volcar, se cambian a mano || (a), humano 2026-11-15. T0: 285 `primero`, 4 nulos, ningún `segundo` |
| Q-3 · Dueño de las tablas para el primer `ALTER TABLE` (medición del líder: `tableowner` de las dos tablas en `pg_tables` frente al rol de la Function) | (a) seguir si es dueño; (b) si no lo es, parar y proponer | (a)/(b) según la medición || (a), humano 2026-11-15. T0: `postventa_app` es dueño de las dos tablas y es el rol de la Function |
| Q-4 · Límite de servicio y contrato | (a) solo backend: `listado` lleva el código y `catalogo.listados` los tipos, el front no cambia; (b) clave nueva `tipo_reclamacion` y ficha de front aparte | (a) || (a), humano 2026-11-15 |
| Q-5 · Plantillas v2 ya repartidas | (a) seguir en v2; las etiquetas viejas fallan por fila; (b) v3 y rechazar las v2 enteras; (c) alias «Primer listado» → `0002` | (a) || (a), humano 2026-11-15 |
| Q-6 · Etiqueta del desplegable | (a) `<res> (<cod>)`, como el oficio de F-071; (b) solo `res`; (c) `<cod> <res>` | (a) || (a), humano 2026-11-15 |
| Q-7 · En blanco | (a) guardar `0002` al importar y al editar; nulo solo en lo anterior a F-072; (b) guardar nulo y resolver al volcar | (a) (literal del `acceptance`) || (a), humano 2026-11-15 |
| Q-8 · Validar el tipo al aprobar | (a) motivo `tipo_fuera_de_sigrid`; (b) no, lo para `sigrid-api` en el ensayo | (a) || (a), humano 2026-11-15 |
| Q-9 · Qué se guarda | (a) solo el código; (b) código y nombre | (a): el nombre se pinta con la lista vigente || (a), humano 2026-11-15 |
| Q-10 · Verificación en producción (T26) | (a) autorizar filas «PRUEBA F-072 - DESCARTAR» en la bandeja de la 0677 y un **ensayo** (dry-run, ventana cerrada) de una aprobada con tipo ≠ `0002`, y descartarlas; (b) solo lecturas | (a) || (a), humano 2026-11-15 |
| Q-11 · Textos del front («Listado», «Sin listado», el motivo nuevo, `TEXTO_TIPO` de `js/volcado.js`) | (a) en F-040 al retomarla; (b) ficha de front aparte | (a) || (a), humano 2026-11-15 |
