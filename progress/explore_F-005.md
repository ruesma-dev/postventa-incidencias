<!-- progress/explore_F-005.md -->
# F-005 · Persistencia en el PostgreSQL compartido — spec redactada

> Escrito por el `spec-author` el 2026-08-19, en un **worktree aislado**
> (`.claude/worktrees/agent-a5e9b8fd6b01155a7`), rama
> `feature/F-005-persistencia` salida de `dev`.
>
> **No se ha tocado `progress/current.md` a propósito**: lo está escribiendo
> otro agente en el árbol principal, sobre `feature/F-004-validacion`.

## Qué se entrega

`specs/F-005-persistencia/` con los tres ficheros de `specs/SPECS.md`:
`requirements.md` (40 requisitos EARS trazados uno a uno contra los cinco
criterios `acceptance`), `design.md` y `tasks.md` (28 tareas, T1–T27 más
T19 bis).

**Actualizada el 2026-08-19** con las seis decisiones del humano (ver abajo).

## Lo que se leyó antes de diseñar

- `azure-apps/`: `README.md`, `albaranes.md` entero, y las secciones de
  `partes.md` y `datamart_seg_anual.md` que hablan del servidor compartido.
- `harness/features.json` (F-005 y las fichas vecinas F-002/006/007/009/016),
  `harness/rigor.json`, `harness/servicios.json`, `CHECKPOINTS.md`.
- `docs/ARCHITECTURE.md`, `docs/CONVENTIONS.md`, `specs/SPECS.md`.
- El contrato real en código: `domain/models/extraccion.py`,
  `config/settings.py`, `tests/conftest.py`, `requirements*.txt`.
- F-004 sin cambiar de rama, con
  `git show feature/F-004-validacion:specs/F-004-validacion/design.md`.

## Los cinco hallazgos que gobiernan el diseño

1. **El ecosistema aísla por BASE DE DATOS, no por esquema.** `albaranes`,
   `partes` y la diseñada `sigrid_dm` son tres bases del mismo servidor, cada
   una trabajando contra su `public`. `docs/ARCHITECTURE.md` dice «schema
   propio». El diseño cumple las dos cosas: base `postventa` **y** esquema
   nominado `postventa` dentro, con `search_path` sin `public`. → **D1**.

2. **El servidor es un `Standard_B1ms` con 32 GB compartidos, el disco solo
   crece y el PITR restaura el servidor entero.** El 2026-08-09 otro proyecto
   lo dejó al 93,4 % y en solo-lectura diez minutos. De ahí tres reglas duras
   del diseño: **ni un BLOB en la base** (los PDF van a SharePoint), **sin
   `raw_extraccion_json`**, y **techo bajo de conexiones** con
   `idle_in_transaction_session_timeout`.

3. **Qué es «como hace sv3»**: el servicio dueño del esquema aplica al
   arrancar `CREATE/ALTER/CREATE INDEX ... IF NOT EXISTS`, sin herramienta de
   migraciones. Se copia **el patrón**; **no** el mecanismo (sv3 y `partes`
   generan el DDL de su ORM de SQLAlchemy), porque `docs/CONVENTIONS.md` manda
   ficheros `NN_nombre.sql`, porque el problema que forzó el ORM allí lo
   causaban **dos** servicios escribiendo el mismo esquema y aquí solo hay
   uno, y porque en un servidor ajeno el DDL tiene que poder leerse antes de
   aplicarlo.

4. **Las prohibiciones duras se convierten en código, no en buenas
   intenciones.** `ddl.py` valida cada sentencia **antes de abrir ninguna
   conexión** y falla el arranque si se sale del esquema o usa un verbo de
   servidor (`CREATE DATABASE/ROLE/EXTENSION/TABLESPACE`, `ALTER SYSTEM`,
   `GRANT`…). Por eso los UUID se generan en Python: `CREATE EXTENSION` está
   prohibido. Y **la aplicación nunca crea la base** —a diferencia de sv3—:
   eso es un script que ejecuta el humano una vez.

5. **La suite tiene una guarda de red que muerde.** F-003 dejó en
   `tests/conftest.py` un parcheo de sesión de `socket.socket.connect`, con un
   test que comprueba que está puesta. **No se afloja.** La suite de base
   efímera vive en otro directorio (`tests_bbdd/`), donde ese `conftest.py` no
   aplica, y se salta sola si no está definida `POSTVENTA_PG_TEST_DSN`.

## Cómo se resuelve la tensión de los tests (design §7)

- **Sin base de datos** (suite por defecto, la que corre `init.sh`): validación
  del DDL real y de ejemplos hostiles inventados, construcción del SQL, mapeo
  ida y vuelta, y el **adaptador entero contra un doble de conexión** que imita
  la DBAPI. Ahí se ganan la cobertura y la mutación.
- **Con base efímera** (opt-in por variable de entorno): lo único que un doble
  no puede demostrar — que el SQL es PostgreSQL válido, que aplicarlo dos veces
  no falla, y que `public` queda sin ninguna tabla nuestra.
- **MANUAL (humano)**: M1 la suite efímera vía script PowerShell (una línea,
  sin `&&`), M2 la primera aplicación del DDL contra la base real de dev, M3 la
  copia del documento a `azure-apps/`.

Un detalle que condiciona el rigor: `harness/alcance.py` **solo muta y mide
ficheros `.py`**, así que un `.sql` escaparía a las puertas. Se tapa dejando el
DDL en `.sql` (convención) y **todo lo que lo interpreta en `.py`**, cuyos
tests leen los `.sql` reales.

## PRECONDICIÓN DURA — sigue vigente tras resolverse las seis decisiones

**F-005 NO se implementa hasta que F-004 esté mergeada en `dev`.** Los puertos
de F-005 hablan `ResultadoValidacion`, `Veredicto`, `Destino` y
`ClasificacionFirma`, que hoy **solo existen en `feature/F-004-validacion`**.
Es la tarea **T1**, y es una parada, no un aviso: si F-004 no está mergeada, se
para. Se descartó inventar un modelo gemelo de persistencia para poder empezar
antes.

Que las seis decisiones estén resueltas **no levanta esta precondición**: eran
dos bloqueos distintos. Las decisiones bloqueaban el *qué*; F-004 bloquea el
*cuándo*.

No se ha pedido ningún cambio a F-004. Único apunte, sin tocarla: su
`ResultadoValidacion` transporta `observaciones` y `confianza_observaciones`,
que **ya vienen de la extracción**; F-005 **no las duplica** en la tabla de
validaciones y las recupera de `partes` con un `JOIN`, por minimización de dato
personal. El invariante «la transcripción del resultado es la del parte» queda
vigilado por un test.

## Cruce de frontera del ecosistema

F-005 hace que este proyecto **consuma un recurso compartido que hoy no
consume**. Por la regla de `CLAUDE.md` y el `README.md` de `azure-apps/`, eso
se documenta en el mismo trabajo: T22 crea `docs/INTEGRACION.md` (fuente de
verdad, en este repositorio) y T26 deja como MANUAL la copia a
`azure-apps/postventa_incidencias.md` — es otro repositorio git y ningún
agente commitea ahí sin que se le pida.

## Datos personales

`design.md` §6 lista **qué columna guarda qué**: `partes.dni_cliente` y
`partes.observaciones` son dato personal directo; `descripcion` posible;
`promocion` y `unidad` indirecto (localizan la vivienda); los `usuario_oid` y
`confirmado_por` son seudónimos de empleado (se guarda el `oid` de Entra,
nunca el correo ni el nombre). Reglas aplicadas: nunca en el repositorio,
nunca en el log (R29, con test), nunca duplicadas, y el PDF no entra en la
base. Todos los ejemplos de la spec están inventados y marcados como tales.

---

# LAS SEIS DECISIONES, RESUELTAS POR EL HUMANO EL 2026-08-19

**Ya no son decisiones abiertas y ninguna bloquea.** Están registradas con su
fecha en `design.md` §10, que conserva el planteamiento original de cada una
para que se entienda qué se sopesó. Cinco **confirman** lo que el diseño ya
proponía; **D2** y **D5** añadieron trabajo concreto a la spec.

1. **D1 · CONFIRMADA: base propia `postventa`**, con esquema nominado dentro y
   `search_path` sin `public`, tal y como se diseñó. Motivo: el ecosistema
   aísla por base, y meter un esquema en `albaranes` ataría el ciclo de vida de
   dos proyectos. La base **la crea el humano a mano; la aplicación nunca**.

2. **D2 · RESUELTA: SÍ se persiste el DNI del cliente.** Decisión expresa del
   humano: *«si guarda el DNI es importante»*. Descartada la alternativa del
   booleano «traía DNI». Como ahora hay **dato personal directo confirmado en
   una base compartida**, las salvaguardas pasan de insinuadas a explícitas y
   verificables: `design.md` §6 es ahora una tabla regla → requisito →
   verificación, y `requirements.md` gana **R37–R40** (nunca en el log, nunca
   en el repositorio ni en fixtures, nunca duplicado en otra tabla, y el PDF
   fuera de la base). `tasks.md` gana **T19 bis**, el barrido del repositorio.
   El esquema de `partes` no cambia.

3. **D3 · CONFIRMADA: Docker** (`postgres:16-alpine`, `--rm`). Dos datos
   verificados ese día en el puesto del humano, ya escritos en **T21**:
   **Docker 29.5.3 está instalado** pero el **demonio estaba parado** (Docker
   Desktop cerrado), y **no hay `psql` en el `PATH`**. El script comprueba lo
   primero que el demonio responde y aborta con un mensaje accionable
   —«arranca Docker Desktop»— en vez de un error opaco de conexión (**R35**), y
   no depende de `psql` en ningún punto (**R36**).

4. **D4 · CONFIRMADA: `numero_incidencia` indexado pero NO único.** La
   deduplicación la hace el hash del parte. Motivos aceptados: una misma
   incidencia puede tener más de un parte (más de una visita), y un índice
   único rompería el día que F-014 reagrupe un parte de dos hojas.

5. **D5 · RESUELTA: NO se declara ahora el DDL como ruta sensible.** F-005 no
   crea `harness/rutas_sensibles.json` y C4 ter sigue **N/A**. Motivo:
   cambiaría el arnés para todas las features y obligaría a portarlo a
   `arnes-base` en el mismo trabajo. **Su sitio es F-017**, ya dada de alta,
   que va a tocar `CHECKPOINTS.md` y a viajar a `arnes-base`. Queda escrito en
   `design.md` §10 que el DDL es **candidato reconocido** a ruta sensible y que
   la decisión vive en F-017, para que nadie lo lea como un olvido.

6. **D6 · CONFIRMADA: la columna `usuario_oid` se crea ya y queda `NULL`**
   hasta F-007/F-010. Cuesta cero ahora y ahorra un `ALTER TABLE` contra una
   base compartida después.

## Estado

`specs/F-005-persistencia/` escrita, con las seis decisiones registradas, y
commiteada en `feature/F-005-persistencia` (worktree aislado). **No se ha
escrito ni una línea de código.** No se ha tocado `harness/features.json`: lo
lleva el líder.

Lo único que sigue en pie antes de implementar es la **precondición dura de más
arriba**: F-004 mergeada en `dev`.
