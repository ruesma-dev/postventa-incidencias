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
`requirements.md` (34 requisitos EARS trazados uno a uno contra los cinco
criterios `acceptance`), `design.md` y `tasks.md` (27 tareas, T1–T27).

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

## Precondición dura

**F-005 no se implementa hasta que F-004 esté mergeada en `dev`**: los puertos
hablan `ResultadoValidacion`, `Veredicto`, `Destino` y `ClasificacionFirma`,
que hoy solo existen en `feature/F-004-validacion`. Es la tarea T1. Se descartó
inventar un modelo gemelo de persistencia para poder empezar antes.

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

# DECISIONES ABIERTAS QUE NECESITA VALIDAR EL HUMANO

Son **seis**. Están desarrolladas en `design.md` §10 con su alternativa y su
coste de cambiar después. **D1 y D3 bloquean la implementación; D2 bloquea el
esquema de `partes`.**

1. **D1 · ¿Base propia `postventa`, o esquema dentro de una base existente?**
   El diseño pide base propia (es lo que hace el ecosistema). La alternativa
   —un esquema dentro de `albaranes` o `partes`— mezcla el ciclo de vida de dos
   proyectos y solo tiene sentido si crear bases en ese servidor está vetado.
   **Crear la base la crea el humano en cualquier caso.** BLOQUEA.

2. **D2 · ¿Se persiste el DNI del cliente, o solo si lo había?** El diseño lo
   persiste (la fila es la traza de lo que el modelo leyó, y el DNI ya queda
   retenido dentro del PDF archivado en SharePoint). El argumento contrario es
   minimización: nadie aguas abajo lo usa. Es una decisión de protección de
   datos, no técnica. BLOQUEA el esquema de `partes`.

3. **D3 · ¿Docker para la base efímera, o `initdb` contra un PostgreSQL local?**
   El diseño asume Docker (`postgres:16-alpine`, `--rm`). Hace falta saber con
   qué cuenta el puesto antes de escribir el script. BLOQUEA T21/T24.

4. **D4 · ¿`numero_incidencia` único?** El diseño lo deja indexado y **no**
   único: la deduplicación la hace el hash, y un único rompería el día que
   F-014 reagrupe un parte de dos hojas. Decide qué pasa si llegan dos partes
   de la misma incidencia — regla de negocio de Posventa.

5. **D5 · ¿Se declara el DDL como ruta sensible del arnés?** Hoy no existe
   `harness/rutas_sensibles.json` y C4 ter es N/A. Un DDL contra un servidor
   compartido es el candidato de manual. **No se hace sin permiso**: cambiaría
   el arnés para todas las features y habría que portarlo a `arnes-base` en el
   mismo trabajo.

6. **D6 · ¿Se guarda ya `usuario_oid` en F-005?** La columna está diseñada,
   pero quien conoce al usuario autenticado es el front (F-007/F-010): en F-005
   quedaría siempre `NULL`.

## Estado

`specs/F-005-persistencia/` escrita y commiteada en
`feature/F-005-persistencia`. **Pendiente de aprobación del humano** y de las
seis decisiones. No se ha escrito ni una línea de código, ni se ha tocado
`harness/features.json`.
