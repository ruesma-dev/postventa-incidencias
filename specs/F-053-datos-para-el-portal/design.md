<!-- specs/F-053-datos-para-el-portal/design.md -->
# F-053 · Dos datos que pide el portal — Diseño

## 1 · Encaje y límite de servicio

Todo vive en **`services/postventa-api`**, en las tres capas que ya usa F-036
para estos dos endpoints, y nada sale del servicio:

| Capa | Qué hace aquí |
|---|---|
| `domain/models/equivalencias.py` | Una función pura nueva: los pares cuya última decisión es «distinto» entre unos códigos |
| `application/pipelines/equivalencias.py` | `propuestas_de_oficios` la llama con las decisiones **que ya lee** y la devuelve en `PropuestasDeOficios` |
| `interface_adapters/api/importar.py` y `equivalencias.py` | Serializan los dos campos |
| `infrastructure/` | **Nada.** El dato de los dos campos ya se lee hoy |

El front (`services/postventa-front`, F-035) **ya** consume los dos campos de
forma tolerante; no se toca. Ninguna responsabilidad de otro servicio entra
aquí: no hace falta extraer nada.

## 2 · De dónde sale cada dato (sin columnas nuevas)

**`importado_at_utc`.** La columna existe:
`postventa.importaciones.importado_at_utc timestamptz NOT NULL`
(`infrastructure/persistencia/sql/12_importaciones.sql`).

- **Importación nueva**: `paso_registro` construye `RegistroImportacion(...,
  importado_at_utc=contexto.ahora)`; `ContextoImportacion.__post_init__` ya
  exige que `ahora` lleve zona, y el borde lo crea con `datetime.now(UTC)`. Se
  guarda tal cual con `insert_importacion`, y `RepositorioBandejaPostgres.
  _registrar` devuelve ese mismo `RegistroImportacion` dentro de
  `ResultadoImportacion.importacion`. PostgreSQL guarda microsegundos, así que
  el valor de la respuesta es el guardado.
- **`ya_importado`**: `paso_huella` pone en `contexto.resultado` lo que devuelve
  `importacion_completa_por_hash`; `select_importacion_completa_por_hash` lee
  `importado_at_utc` (columna 6 de `_COLUMNAS_LECTURA_IMPORTACION`, ordenado
  por `importado_at_utc, importacion_id`, `LIMIT 1`: la **original**) y
  `fila_a_resultado_ya_importado` lo deja en `importacion.importado_at_utc`.
  psycopg lo devuelve *aware*, en la zona de la sesión.

En las dos rutas el dato es **`contexto.resultado.importacion.
importado_at_utc`**. Nunca `contexto.ahora`: en `ya_importado` es el instante
de la petición repetida, y daría la fecha de hoy (R2).

**`oficio.distintos`.** `_vigentes` ya llama a `equivalencias.
ultimas_decisiones(catalogo=OFICIO, codigos=<los de la obra>)`, que por
contrato del puerto devuelve solo pares con **los dos** códigos de la obra
(`DISTINCT ON` en PostgreSQL; el doble de los tests filtra igual). De esas
mismas decisiones se sacan los pares cuya última decisión es `distinto`.
**Ni una lectura nueva** (R16).

## 3 · Ficheros

**A crear**

| Ruta | Qué es |
|---|---|
| `services/postventa-api/tests/test_f053_importado_at_utc.py` | R1–R7 (serializador y ruta HTTP con dobles; sin red ni base) |
| `services/postventa-api/tests/test_f053_distintos_dominio.py` | R9–R13 sobre la función pura |
| `services/postventa-api/tests/test_f053_propuestas_distintos.py` | R8–R16 por la ruta HTTP con los dobles de F-036, y R17 para `POST /api/catalogos/decisiones` |
| `services/postventa-api/tests/test_f053_documentacion.py` | R20 sobre `docs/INTEGRACION.md` |

**A modificar**

| Ruta | Qué cambia |
|---|---|
| `services/postventa-api/interface_adapters/api/importar.py` | `serializar_importacion` añade `"importado_at_utc"`; función privada `_instante_utc`; el docstring del módulo («La respuesta (R43)») lo nombra |
| `services/postventa-api/domain/models/equivalencias.py` | Función pura `pares_distintos` (§4) |
| `services/postventa-api/application/pipelines/equivalencias.py` | `PropuestasDeOficios` gana `distintos`; `propuestas_de_oficios` lo calcula con las decisiones de `_vigentes` |
| `services/postventa-api/interface_adapters/api/equivalencias.py` | `leer_propuestas` añade `"distintos"` dentro de `oficio`; el docstring del módulo lo nombra |
| `services/postventa-api/tests/test_f036_importar_http.py` | **Una línea añadida**: `"importado_at_utc",` en `CLAVES` (D-3) |
| `services/postventa-api/tests/test_f036_catalogos_http.py` | **Dos líneas añadidas**: `"distintos": [],` en la igualdad de `test_f036_r87_las_propuestas_de_oficios_de_la_obra` y en la de `test_f036_r12_una_obra_sin_oficios_no_propone_nada` (D-3) |
| `docs/INTEGRACION.md` | §8, subapartado «Los endpoints, y qué hace cada uno»: **un párrafo nuevo, sin encabezado**, justo antes de «Los diecisiete quedan en nivel **anónimo**» (§6) |
| `C:\Users\pgris\PycharmProjects\azure-apps\postventa_incidencias.md` | El mismo párrafo en su §8 y una línea en «LO QUE CAMBIA EN ESTA REVISIÓN»; commit local en ese repositorio |

**No se tocan** (y tientan):

- `infrastructure/persistencia/` entero: `sentencias_bandeja.py`,
  `repositorio_bandeja_pg.py`, `sql/*.sql` (ni DDL ni consultas nuevas: el dato
  ya se lee), `ddl.py`, `arranque.py`.
- `domain/ports/bandeja.py` y `domain/ports/equivalencias.py`: los contratos de
  los puertos no cambian.
- `application/pipelines/paso_importacion.py` y `contexto_importacion.py`: el
  instante ya se fija y se guarda bien.
- `GruposVigentes` y `_grupos()` del adaptador: los comparten la respuesta de
  `POST /api/catalogos/decisiones` (`grupos_vigentes`) y la plantilla; meter ahí
  `distintos` cambiaría esas respuestas (R17).
- `application/pipelines/plantilla.py`, `interface_adapters/api/bandeja.py`
  (su `creada_at_utc.isoformat()` se queda como está: es otro contrato).
- `function_app.py`: las rutas, los códigos HTTP y los envoltorios no cambian.
- `services/postventa-front/` entero, `infra/`, `harness/*` (salvo lo que el
  líder haga con `features.json`), `CHECKPOINTS.md`.
- El log de `propuestas_de_oficios`: no gana `distintos=%d` (no lo pide nadie y
  sería un mutante de log más).
- El resto de tests de F-036 (R18): solo las tres líneas de arriba.

## 4 · Funciones y firmas

| Firma | Capa | Responsabilidad |
|---|---|---|
| `pares_distintos(codigos: Iterable[str], decisiones: Iterable[DecisionPar], catalogo: Catalogo) -> tuple[tuple[str, str], ...]` | domain | Reutiliza `_ultimas(decisiones, catalogo)` (la regla de F-036: manda la fecha; a igual fecha, la que llega después; las de otro catálogo no cuentan). Devuelve los pares `(codigo_a, codigo_b)` cuya última decisión es `DISTINTO` y cuyos **dos** códigos están en `codigos`, ordenados con `sorted`. Filtra por la obra aunque el puerto ya lo haga: la función no se fía de quien la llame (R9) |
| `PropuestasDeOficios.distintos: tuple[tuple[str, str], ...]` | application | Campo nuevo, **al final** y **sin valor por defecto** (el único constructor es `propuestas_de_oficios`; sin defecto, olvidarlo es un error y no un `()` silencioso) |
| `propuestas_de_oficios(...)` | application | `distintos=pares_distintos((o.codigo for o in catalogo.oficios), decisiones, Catalogo.OFICIO)`, con las `decisiones` que ya devuelve `_vigentes` |
| `leer_propuestas(...)` | interface_adapters | En `oficio`, después de `"propuestas"`: `"distintos": [{"codigo_a": a, "codigo_b": b} for a, b in resultado.distintos]` |
| `_instante_utc(valor: datetime) -> str \| None` | interface_adapters (`importar.py`) | `None` si `valor.utcoffset() is None` (R5); si no, `valor.astimezone(UTC).isoformat(timespec="microseconds")` (R3, R4) |
| `serializar_importacion(contexto)` | interface_adapters | `cuerpo["importado_at_utc"] = _instante_utc(resultado.importacion.importado_at_utc)`, en las dos rutas (R1, R2, R6, R7) |

## 5 · SQL

**Ninguno.** Ni DDL ni consultas nuevas. La columna `importado_at_utc` existe y
se lee; las decisiones ya se leen con `select_ultimas_decisiones`.

## 6 · `docs/INTEGRACION.md`: dónde y por qué ahí

El párrafo va **sin encabezado** dentro de «### Los endpoints, y qué hace cada
uno», antes de «Los diecisiete quedan en nivel **anónimo**». Un `###` nuevo
partiría ese subapartado: los tests de documentación de F-019 y F-036 cortan
las secciones por encabezado (`_seccion`) y buscan textos que van detrás de la
tabla; con un encabezado en medio dejarían de encontrarlos. Las dos filas de
la tabla no se reescriben (las fija `test_f036_documentacion.py`).

Lo que dice el párrafo (R20): `POST /api/importaciones` devuelve, desde F-053,
`importado_at_utc` (instante en UTC, `AAAA-MM-DDTHH:MM:SS.ffffff+00:00`;
`null` si no se sabe la zona; con `ya_importado: true`, el de la importación
**original**); `GET /api/catalogos/propuestas` devuelve `oficio.distintos`
(`[{codigo_a, codigo_b}]`, códigos como texto con sus ceros, `codigo_a <
codigo_b`, ordenados, solo pares de oficios de la obra cuya **última** decisión
es `distinto`; los códigos de oficio de Sigrid son dígitos, y el front
identifica el par con `a-b`, así que un código con guion podría chocar). Los
dos son **aditivos** y los consume el portal (F-035) de forma tolerante.

## 7 · Tests: cómo se prueba cada cosa sin red ni base

Todo con los dobles que ya existen (`tests/utiles_importacion.py`:
`BandejaEnMemoria`, `EquivalenciasEnMemoria`; `EquivalenciasQueGuardan` en
`test_f036_catalogos_http.py`) y `datetime` fijos. Las zonas, con
`timezone(timedelta(hours=2))` y no con `ZoneInfo`, para no depender de
`tzdata` en Windows.

Casos que matan los mutantes previsibles:

| Mutante | Lo mata |
|---|---|
| Serializar `contexto.ahora` en vez del resultado | R2: primera subida con `ahora=T1`, segunda con `ahora=T2`; la segunda devuelve T1 |
| Quitar `timespec="microseconds"` | R3 con `AHORA` (microsegundo 0): igualdad exacta con `…T08:15:00.000000+00:00` |
| Quitar `astimezone(UTC)` | R4: `01:30+02:00` del 15/07 sale `2026-07-14T23:30:00.000000+00:00` |
| Quitar la rama sin zona | R5: un resultado con instante *naive* da `null` y 200 |
| `DISTINTO` → `MISMO`, `==` → `!=` | R9/R10 |
| `and` → `or` en el filtro de la obra | R9 en el dominio: un par con un código de fuera de `codigos` no sale |
| Quitar el `sorted` | R12: decisiones dadas en orden inverso |
| Quitar el filtro de catálogo | R13: una decisión `proveedor` «distinto» con los mismos códigos |
| Meter `distintos` en `_grupos()` | R17: la igualdad completa de `test_f036_r88_la_respuesta_lleva_los_pares_y_los_grupos_resultantes` (sin tocar) |

R10 y R15 van **por la ruta HTTP** con `EquivalenciasQueGuardan`: `GET`, `POST`
«distinto» con un `ahora`, `POST` «mismo» con otro posterior, `GET`. R11, con
el catálogo de la 0677 en el doble (`0033` y `0133` como textos) y
`isinstance(..., str)` además de la igualdad.

## 8 · Riesgos y decisiones

- **D-1 · La forma de la fecha: siempre con microsegundos y `+00:00`.**
  `isoformat()` a secas omite los microsegundos cuando valen 0, así que la
  forma variaría de una respuesta a otra. Con `timespec="microseconds"` es
  **una sola**, y es exactamente la del caso de Node que ya existe en el front
  («con +00:00 y microsegundos»), así que no hay que tocar el front (O12-2 de la
  review del bloque 12). Descartadas: `timespec="seconds"` (no hay caso de Node
  con `+00:00` sin microsegundos: habría que añadirlo en otro servicio) y `Z`
  (Python no lo emite; habría que construirlo a mano).
- **D-2 · Sin zona, `null`.** No debería pasar (`ContextoImportacion` exige
  zona y psycopg devuelve `timestamptz` con zona), pero si pasa, una fecha sin
  rótulo es segura y una supuesta UTC puede ser la de Madrid (contrato, punto
  2). Descartadas: tratarla como UTC (puede mentir) y lanzar (convertiría en
  500 una importación ya registrada).
- **D-3 · Tres líneas añadidas en tests de F-036 (requiere visto bueno).** Tres
  aserciones de F-036 comparan la respuesta **entera** (`set(cuerpo) ==
  CLAVES` y dos igualdades de `oficio`), así que cualquier campo nuevo las
  rompe. «Los tests de F-036 siguen en verde» se cumple ampliándolas con la
  clave nueva: **solo líneas añadidas**, ninguna quitada ni cambiada. La
  review lo comprueba con `git diff 349ba06 -- services/postventa-api/tests/test_f036_*.py`.
  Descartada: dejarlas como están (imposible: o fallan, o el campo no sale).
- **D-4 · `distintos` en el dominio y no en SQL.** Reutiliza `_ultimas` (la
  regla de «manda la última» se dice una vez) y las decisiones que ya se leen
  (R16). Descartada: una consulta `WHERE decision = 'distinto'` tras el
  `DISTINCT ON` (otra lectura, y la regla dicha dos veces).
- **D-5 · Solo en `GET /api/catalogos/propuestas`.** La respuesta de `POST
  /api/catalogos/decisiones` no gana `distintos`: el front recarga las
  propuestas después de decidir (contrato, punto 8) y `grupos_vigentes` lo
  comparten otras respuestas (R17).
- **D-6 · Los guiones no se garantizan con un test.** Los códigos de oficio de
  Sigrid son dígitos; filtrar códigos con guion escondería datos en silencio.
  Consta en `docs/INTEGRACION.md` (contrato, punto 6: «si no, basta con que
  conste»).
- **Riesgo · el orden de despliegue.** Ninguno: el front ya tolera la ausencia
  de los dos campos. El despliegue se hace **desde una copia limpia de `dev`**
  (worktree), no desde la carpeta de trabajo, para publicar exactamente lo
  mergeado.
- **Riesgo · V1 escribe si el `v2` no era completo.** Si la importación del
  `v2` hubiera sido **parcial**, reimportarlo no sería `ya_importado`: se
  procesaría otra vez y dejaría una fila más en `postventa.importaciones` (las
  incidencias saldrían `ya_en_bandeja`). Por eso V1 empieza mirando el estado
  (`tasks.md`, T11).
