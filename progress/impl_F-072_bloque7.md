# F-072 · Informe del implementer · Bloque 7 (T21: documentación y alcance)

> Rama del worktree: `feature/F-072-tipo-reclamacion-sigrid-b7`, desde
> `3bb44e0` (Bloques 1–6 integrados). El líder integra en
> `feature/F-072-tipo-reclamacion-sigrid`. Solo T21 (R31, R32, R33); T22 no.
> `progress/impl_F-072.md` no se toca (está en su tope).

## Hecho

`docs/ARCHITECTURE.md` y `docs/INTEGRACION.md` describen el tipo de reclamación
de punta a punta (lectura de `auxtrcp`, columna `tipo_reclamacion`, tipo
efectivo, contrato de `listado`, volcado). Dos tests nuevos fijan la
documentación (R33) y el alcance (R31, R32), los dos en `ejecutar_siempre` de
`api`. `azure-apps/` no se toca (T25, el líder).

## Ficheros

- `docs/ARCHITECTURE.md`:
  - sección nueva **«El tipo de reclamación (F-072)»** (antes de «Acceso a
    datos…»), con siete subsecciones: la lectura, la columna y el tipo
    efectivo, plantilla e importación, el contrato de `listado`, el volcado,
    dónde vive cada pieza, lo que no hace;
  - «La plantilla» (F-071): **enmienda** fechada, el listado también sale de
    Sigrid. La frase de F-071 «todos los desplegables salen de Sigrid salvo
    urgencia y listado» se queda como historia: la fija
    `test_f071_documentacion.py` (R46) y el documento usa enmiendas para eso;
  - «La importación», paso 3: los tipos, después de las ubicaciones;
  - «La revisión es una tabla append-only»: la foto lleva también el tipo;
  - «Lo que hereda F-040» y **«El parte que se manda» (F-059)**: «tipo 0002
    siempre» pasa a «con F-059, tipo 0002 siempre (…); desde F-072, el tipo
    efectivo». Se conserva «tipo 0002», que fija `test_f059_documentacion.py`;
  - «Lo que no hace la revisión»: cuarta lectura por petición;
  - **no se duplican** lo que adelantaron el Bloque 2 (`tipo_fuera_de_sigrid`
    en la lista de motivos) y el Bloque 6 (`construir.tipos`/`tipos` en «La
    medición del listado»): la sección nueva no repite esas listas.
- `docs/INTEGRACION.md`:
  - §1: filas de PostgreSQL y de `sigrid-api` (F-072 en «Desde»); enmienda en
    «Con F-071»; sección nueva **«Con F-072 · la quinta lectura: los tipos de
    reclamación»** (SQL literal, cuándo, techo y errores, log, volumen, nada
    para el dueño de `sigrid-api`). «Quinta» porque F-065 ya es la cuarta;
  - §2: sección nueva **«Con F-072 · la columna `tipo_reclamacion`»** (primer
    `ALTER TABLE`, dueño, nulo = `0002`, `listado` heredado, aviso a F-048);
  - §3 bis: el tipo del parte (F-059 → F-072, `tipo_no_valido`);
  - §4: «Las de F-072: ninguna» y la frase de los listados en «Las de F-036»;
  - §6: dos filas (pasarela caída o al techo; tipo dado de baja, también el
    `0002`);
  - §8: filas de `GET /api/plantilla`, `POST /api/importaciones`,
    `GET /api/bandeja`, `GET /api/revision`, `POST /api/revision/acciones` y
    `POST /api/volcado/ensayo`; fila de F-072 en «Qué NO está desplegado»;
  - §9: cinco filas de F-072.
  - **La cabecera no se toca**: `test_f065_documentacion.py` la fija a
    «Fecha: 2026-10-31.» y «Última feature que lo tocó: F-065» (F-071 tampoco
    la tocó). Para el líder: si se quiere al día, hay que ampliar ese test con
    la regla de suelo de F-036/F-056/F-059 (decisión aparte).
- `services/postventa-api/tests/test_f072_documentacion.py` (nuevo, 33 tests).
- `services/postventa-api/tests/test_f072_alcance_cerrado.py` (nuevo, 77 tests).
- `harness/servicios.json`: los dos en `ejecutar_siempre` de `api`.
- `specs/F-072-tipo-reclamacion-sigrid/tasks.md`: T21 `[x]`.

## Decisiones de diseño de los tests

- **Documentación (R33)**: patrón de `test_f071_documentacion.py`; los controles
  leen el código (`SQL_TIPOS_RECLAMACION`, `TIPO_RECLAMACION_POR_DEFECTO`,
  `MotivoNoAprobable.TIPO_FUERA_DE_SIGRID`, la columna en `17_…sql`, la línea
  de log de `application/pipelines/tipos_reclamacion.py`, el YAML sin
  `listados`); barrido de secretos de F-005 y sin correos en lo nuevo.
- **Alcance (R31, R32)**: patrón de `test_f071_alcance_cerrado.py`, con base fija
  `6994cb0` y las tres guardas de F-030 (`RAMA_DE_LA_FEATURE`, rama ya en `dev`).
  - Mitad sin `git` (siempre): huella `sha256` de las **ocho** constantes `SQL_*`
    que ya existían (catálogo, ubicaciones válidas, reclamaciones de F-065,
    ubicación de F-013); huella de `13_`, `15_`, `16_*.sql` (fin de línea
    normalizado: depende de `core.autocrlf`); las 18 piezas de F-072 sin
    marcas de escritura ni ventanas ni imports de adaptadores de escritura; la
    función nueva de la fábrica; el adaptador nuevo hereda el del catálogo
    (`RUTA_LECTURA = "/api/sql/read"`) y solo define `leer`; **los tests de
    F-072** no importan `psycopg*`, `google.genai`/`generativeai` ni
    `infrastructure.llm`, ni construyen `httpx.Client`; la guardia `sin_red`
    de `conftest.py` sigue `autouse` y de sesión.
  - Mitad del diff: nada del front ni de la lista de §3.3; en
    `infrastructure/sigrid/` solo `A` de los dos módulos nuevos y `M` de la
    fábrica, que **solo gana** `construir_tipos_reclamacion` (cambia `__all__`);
    el único `.sql` es `A 17_tipo_reclamacion.sql`; las cinco `consultas*.py`
    enteras iguales a la base; `function_app.py` igual **sin docstrings** y con
    las mismas rutas.
  - `tests_bbdd/…/test_f072_bbdd_tipo.py` (R17) queda fuera del barrido de los
    tests: es la suite MANUAL contra la base efímera local.
  - Más estricto que §3.3 en un punto: toda `infrastructure/sigrid/` salvo lo
    declarado, y `consultas_ubicacion.py`/`consultas.py` (R32 dice «las
    consultas existentes de `infrastructure/sigrid/`»).

## Lo que reveló el diff (`git diff --stat 6994cb0..HEAD`)

Ningún fichero de la lista de R32 cambió: ni `services/postventa-front/**`, ni
consultas, `catalogo_obra.py`, `volcado.py`, `cliente.py`, `ddl.py`,
`excel_openpyxl.py`, lectura aislada, `application/pipelines/volcado.py`,
`guarda_sigrid.py`, equivalencias, F-065 ni `function_app.py`. En
`infrastructure/sigrid/` solo los dos módulos nuevos y `fabrica.py`. Nada que
bloquear.

## Fase RED

**Documentación.** Con `docs/` de `3bb44e0` (copias guardadas, `git checkout
HEAD -- docs/…`, test, copias restauradas):

```
$ .venv/Scripts/python.exe -m pytest tests/test_f072_documentacion.py -q -p no:cacheprovider
E       AssertionError: no se encuentra la sección «## El tipo de reclamación (F-072)»
E       AssertionError: no se encuentra la sección «### Con F-072 · la quinta lectura: los tipos de reclamación»
E       AssertionError: no se encuentra la sección «### Con F-072 · la columna `tipo_reclamacion`»
E       AssertionError: no se encuentra la sección «### Las de F-072: ninguna»
FAILED tests/test_f072_documentacion.py::test_f072_r33_la_plantilla_de_f071_lleva_la_enmienda
FAILED tests/test_f072_documentacion.py::test_f072_r33_el_parte_de_f059_ya_no_dice_solo_tipo_0002_siempre
FAILED tests/test_f072_documentacion.py::test_f072_r33_las_filas_de_la_seccion_ocho_dicen_el_contrato[| `GET /api/plantilla` |-esperados0]
32 failed, 1 passed in 1.91s
```

(El que pasa es `los_controles_leen_algo_del_codigo`, que solo lee código.)

**Alcance.** El código de F-072 ya existía (Bloques 1–6), así que la fase RED
se hizo **sembrando** las violaciones: una línea añadida a
`services/postventa-front/bandeja.html`, a `infrastructure/sigrid/consultas_catalogo.py`
y a `sql/16_volcados_sigrid.sql`, con la rama forzada a la de este worktree
(ver «Cómo se verificó la mitad del diff»):

```
E       AssertionError: assert 'b6d3b6f48175...2cb38d0496dce' == '12279ec69bf1...6e431c043f45c'
E       AssertionError: assert ['services/po...bandeja.html'] == []
E       AssertionError: assert [('M', 'servi..._sigrid.sql')] == []
E       AssertionError: assert {('A', 'servi.../fabrica.py')} <= {('A', 'servi.../fabrica.py')}
E         ('M', 'services/postventa-api/infrastructure/sigrid/consultas_catalogo.py')
E       AssertionError: assert '# services/p...valor)\n# x\n' == '# services/p... str(valor)\n'
5 failed, 72 passed in 8.97s
```

Revertido con `git checkout --` de los tres ficheros; árbol limpio de nuevo.
(La huella de la constante `SQL_*` no cae con un comentario al final del
fichero; la caza el control del fichero entero, que es el que falla arriba.)

## Cómo se verificó la mitad del diff

En el worktree la rama es `…-b7` (la de la feature está en el repositorio
principal), así que los 12 controles del diff **se saltan** por la guarda de
F-030. Para ejecutarlos se usó un ejecutor de un solo uso en el scratchpad
(fuera del repo) que pone `RAMA_DE_LA_FEATURE` a la rama del worktree antes de
recoger: **77 passed**. En la rama de la feature, tras integrar, corren solos.

## Salida de los tests

- Verificación de T21:
  `pytest tests/test_f072_documentacion.py tests/test_f072_alcance_cerrado.py tests/test_f059_documentacion.py tests/test_f071_documentacion.py`
  → **169 passed, 12 skipped in 6.37s** (los 12, la mitad del diff fuera de la
  rama de la feature).
- Todos los `*documentacion*` del servicio: 612 passed, 36 skipped.
- Suite `api` entera (`pytest -q -x`, desde el worktree): **10349 passed, 501 skipped in 1004.40s (0:16:44)**.
- `bash harness/init.sh`: **no ejecutado** (T22, por encargo).

## Evidencias

| Evidencia | Valor |
|---|---|
| Tests nuevos | 33 (documentación) + 77 (alcance; 12 de ellos solo en la rama) |
| Suite `api` | 10349 passed, 501 skipped, 0 failed; 1004,40 s |
| Cobertura de líneas cambiadas | N/A en este bloque: solo docs y tests; la mide `init.sh` en T22 |
| Mutación | No aplica a T21 (sin código de producción); la campaña de la feature es T22 |
| Capa e2e | N/A (R31–R33 son `unit`) |

## Pendiente

- T22 (init, mutación, review final) y T25 (`azure-apps/`), del líder.
- Cabecera de `INTEGRACION.md` (arriba): decisión del líder.
