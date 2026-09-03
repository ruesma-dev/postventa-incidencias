<!-- progress/impl_spec_escritura_documental.md -->
# Spec del endpoint de escritura documental en `sigrid-api` (para desbloquear F-012)

> ## ⚠ CORRECCIÓN · 2026-09-03 · la §3 de la spec quedó DESMENTIDA
>
> Este informe entregó una especificación cuya **§3 (permisos)** afirma que el
> usuario de escritura «casi con seguridad no tiene ningún permiso» sobre la
> base documental, y presenta una acción de administrador de base de datos como
> la pieza que falta para poder implementar.
>
> **Es falso.** El humano lo confirmó el 2026-09-03 y lo respalda el spike
> **F-002 de `sigrid-api`, ya cerrado**: el usuario de escritura **ya tiene
> permiso** sobre esa base. Con ello la **§2** deja de ser una inferencia y pasa
> a estar cerrada, la consulta de `DATABASEPROPERTYEX` de §2.5 deja de ser
> necesaria para sostener la premisa, y el escenario de §2.6 («y si la premisa
> fuera falsa») deja de ser un riesgo abierto.
>
> **La spec NO se ha corregido, y es deliberado.** La corrige **el humano al
> implementar su F-004**, que es el endpoint que esto especifica: lo decidió así
> porque tiene `sigrid-api` en otra rama (`chore/instalar-arnes`, donde acaba de
> instalar el arnés v1.7.8) y no tiene sentido que un agente le cambie de rama
> un repositorio en el que está trabajando.
>
> Todo lo demás de la spec —contrato, transaccionalidad, reserva de `ide`,
> correspondencia por `cod`, idempotencia, límites y seguridad— **sigue en pie**.


> Trabajo **documental y de solo lectura**, 2026-09-03, rama
> `feature/F-009-cierre-sigrid`.
> **No se ha ejecutado ni una llamada ni una consulta** contra Sigrid,
> `sigrid-api`, ninguna Function desplegada, el PostgreSQL compartido ni
> SharePoint. Ni de lectura.
> **No se ha implementado nada**: es una especificación.
> **No se ha cambiado el estado de ninguna feature**, ni aquí ni en ningún otro
> repositorio. F-012 sigue `blocked` y F-023 sigue `blocked`.

---

## 1 · Dónde quedó la especificación

**Fichero:**
`C:\Users\pgris\PycharmProjects\sigrid-api\docs\propuestas\2026-09-03_endpoint_adjuntar_documento.md`

- **Repositorio:** `sigrid-api` (la v1, la desplegada). El dueño del documento
  es el proyecto que describe.
- **Rama:** `docs/propuesta-escritura-documental`, creada desde `albaranes`
  (la rama en la que estaba el repositorio). **No se ha hecho `push`.**
- **Commit:** `8df3ba3` — *«Propuesta: endpoint de dominio para adjuntar un
  documento a un concepto»*, **un solo fichero, 1.152 líneas**.
- **El repositorio queda en esa rama nueva.** El trabajo sin confirmar que ya
  había allí (cuatro scripts en el índice y varios CSV sin seguir) está
  **intacto y en el mismo estado** en que se encontró. Para volver a lo de
  antes: `git checkout albaranes`.

**Por qué `docs/propuestas/` y no otro sitio:** `sigrid-api` **no tiene arnés**
—ni `CLAUDE.md`, ni `harness/`, ni `specs/`, ni `.claude/`—; su único documento
propio es `docs/DEPLOYMENT_TERRAFORM_AND_CODE.md`, que es operación. Se creó una
carpeta para diseño previo a código, con nombre `AAAA-MM-DD_asunto.md`. Si algún
día se le instala `arnes-base`, el documento se mueve a `specs/` sin pérdida.

**No se ha tocado `azure-apps/sigrid_api.md`**, que describe lo que la pasarela
hace hoy y no lo que se propone. La spec lleva escrito qué secciones suyas hay
que actualizar el día que el endpoint exista (§13).

**No se ha duplicado la spec aquí.** En este repositorio solo queda el puntero
de `docs/INTEGRACION.md` §3 bis y este informe.

---

## 2 · Los tres puntos previos, resueltos

### 2.1 · Contra qué repositorio se especifica — **RESUELTO, sin ambigüedad**

**La v1 (`C:\Users\pgris\PycharmProjects\sigrid-api`).** Cinco evidencias:

1. `azure-apps/sigrid_api.md` §11 manda desplegar desde esa ruta a
   `func-sigridapi-dev-huyke`.
2. Ese documento se actualizó el **2026-08-18** (§4.1, App Settings efectivas
   medidas) y sigue describiendo **una sola** Function App.
3. `remesas.md` —consumidor vivo— tiene su `SIGRID_API_BASE_URL` apuntando a
   esa Function App; `partes.md` y `dedicacion.md` la nombran igual.
4. **`func-sigridapi2-dev` no aparece en ningún documento del ecosistema**,
   solo en el `README.md` de la propia v2: el cutover no ha ocurrido.
5. **`sigrid-api-v2` ni siquiera es un repositorio git.** La v1 tiene
   historial, ramas y remoto.

La v2 no se ignora: la spec anota (§13) que sus capas `domain/`, `application/`,
`infrastructure/` y `config/` son copia 1:1 de las de la v1, así que el endpoint
se porta añadiendo **un router** — y que si el cutover ocurre después de
implementarlo, hay que rehacer esa copia o se pierde.

### 2.2 · Si la instancia es la misma — **RESUELTO en código; la premisa era falsa al revés**

**Veredicto: la base documental NO es una réplica de solo lectura. Es una base
documental normal, en la MISMA instancia, y el propio ERP le escribe.**

Tres hechos:

1. **Misma instancia [MEDIDO, en código].**
   `sigrid-api/infrastructure/repositories/sql_server_repository.py`, método
   `_connect()`, construye **una sola** cadena
   `SERVER=tcp:{host},{port};DATABASE={database};`, y `config/settings.py`
   declara **un único** `SQL_SERVER_HOST` y un único `SQL_SERVER_PORT`. **No hay
   una segunda pareja host/puerto para la documental.** Lo único que cambia es
   `DATABASE=`. Un puerto TCP responde a una instancia.
   → **Una transacción entre las dos bases es LOCAL. No hace falta MSDTC**, que
   es una suerte porque `pyodbc` no lo soporta.
2. **El ERP le escribe todos los días [MEDIDO].** Nuestro propio
   `docs/referencia/03_modelo_posventa_sigrid.md` §4.1–§4.2: la documental tiene
   357.901 filas y **ninguna con `ima` vacío**; el parte de ejemplo pesa 242.534
   bytes ahí y su fila nació el 2026-08-18 a las 11:40:39, cuando Posventa
   importó el PDF desde la UI; y `ruesma.gra.ima` está vacío para los 13.450
   gráficos de posventa, o sea que **el binario no existe en ninguna otra
   parte**. Una réplica de solo lectura no puede recibir esa escritura.
3. **La exclusión es una App Setting [MEDIDO].** `write-lists.json` e
   `infra/scripts/setup-deploy-write.ps1` de `sigrid-api` fijan la lista de
   bases escribibles a la de negocio. Se cambia editando una lista.

**De dónde venía el error.** `azure-apps/sigrid_api.md` §2 —el documento del
**dueño** de la pasarela— dice literalmente «**no son una base y su réplica**:
son dos bases con **propósitos distintos**», y que la documental está fuera de
la lista blanca «**precisamente para impedirlo**»: una política. Son
`dedicacion.md`, `partes.md` y `remesas.md` —documentos de proyectos
**consumidores**— los que la llaman «réplica». **Se equivocan los tres**, y ese
error ha costado tener F-012 bloqueada por un motivo que no era el real.

> Corregir esa palabra en los tres documentos es trabajo de sus dueños, no
> nuestro. Queda anotado en la spec (§13) para el día del despliegue.

**Sigue siendo [INFERIDO], y la spec lo marca así.** Lo convierte en dato una
consulta de lectura de una línea (§2.5 de la spec):
`SELECT DATABASEPROPERTYEX('<documental>','Updateability')` — esperado
`READ_WRITE` — más `SELECT @@SERVERNAME` ejecutado contra las dos bases para ver
que devuelven el mismo servidor. **Es la primera tarea de cualquier
implementación y es gratis.**

### 2.3 · Permisos del login de escritura sobre la documental — **NO SE PUEDE SABER LEYENDO**

Lo que sí se sabe: hay dos logins separados; el de lectura **sí** puede leer la
documental (`documents/read` abre la conexión con credenciales de lectura y
funciona en producción) y **no** tiene permisos de escritura en el motor; el de
escritura puede `INSERT`/`UPDATE` en la base de negocio y **no** tiene `DELETE`
general (`sigrid_api.md` §7.7).

Lo que **no** se sabe: si el login de escritura tiene siquiera usuario en la
base documental. **No hay ni un script de `GRANT` en el repositorio**: se buscó
en `infra/` y en `docs/` y los scripts solo crean recursos de Azure y fijan App
Settings. Los permisos se concedieron a mano en el motor y no están versionados.

**Lo más probable [INFERIDO]:** no lo tiene, y un `INSERT` cruzado fallaría con
un error limpio (SQL 916), no con una escritura a medias. La spec §3 lleva las
consultas exactas —de solo lectura, con `EXECUTE AS USER` y `fn_my_permissions`—
que lo responden, y **no puede hacerlas la pasarela**, porque `sql/read` usa
siempre las credenciales de lectura: las tiene que ejecutar un administrador del
SQL Server.

El `GRANT` mínimo que haría falta está en §12.2 de la spec: `CREATE USER` +
`GRANT SELECT, INSERT ON OBJECT::dbo.gra`, **y nada más** — ni `UPDATE`, ni
`DELETE`, ni `db_datawriter`, ni ninguna otra tabla.

---

## 3 · Qué contiene la spec, en una pantalla

Diseñada como **endpoint de dominio acotado**, no como apertura de `sql/write`
a la base documental. Ese matiz es el corazón: **la lista blanca de escritura
sigue teniendo solo la base de negocio después del cambio**, y lo que se abre es
un `INSERT` sobre **una** tabla, alcanzable **solo** por la ruta nueva.

- **Contrato** — `POST /api/sigrid/concepto-grafico`. Binario en **base64
  dentro del JSON**, con las tres razones (coherencia con el embudo
  Pydantic+guard de la pasarela, simetría con `documents/read`, y que el coste
  del 33 % de inflado es irrelevante frente a un parte de 242 KB) y lo que se
  pierde dicho en voz alta. Respuesta igual en dry-run y en commit. **Errores
  en la convención de la casa** (400 + código de máquina en el cuerpo), con el
  argumento de por qué no se inventan 409 ni 413.
- **Transaccionalidad** — una conexión contra la base de negocio, nombres de
  tres partes para llegar a la documental, `run_in_write_transaction()` que ya
  existe. Y el **orden documental → metadatos → enlace**, elegido para que cada
  prefijo interrumpido sea un estado invisible en vez de un gráfico roto —que es
  justamente la anomalía de los 51 gráficos sin pareja. Con plan B por escrito
  si las bases no fueran de la misma instancia.
- **Reserva de `ide`** — se **reutiliza y se cita** la técnica de F-009
  (`design.md` §7.3 y `escrituras.py`): `UPDLOCK, HOLDLOCK` sobre el agregado,
  fallo en seguro por clave única, rollback total, y el filtro en el `FROM` y
  nunca en un `WHERE EXISTS`. Con una mejora que aquí sí cabe: un endpoint de
  dominio mantiene el cursor abierto, así que el `ide` reservado se reutiliza en
  Python y `rcg.gra` no hay que rederivarlo por `cod`.
- **Correspondencia por `cod`** — el formato medido, la regla de que la misma
  cadena va en las dos filas, y la guarda previa de duplicados porque **`gra.cod`
  no tiene índice único declarado**.
- **Idempotencia** — clave determinista `UUIDv5(conide + sha256)` en `gra.guid`,
  comprobada dentro de la transacción y serializada por el applock; con plan B
  **por contenido** (`HASHBYTES` sobre el binario ya guardado) si resultara que
  Sigrid usa esa columna.
- **Límites** — 10 MB de binario, timeout **120 s deliberadamente por debajo de
  los 230 s del balanceador** (para que falle la aplicación y responda, en vez
  de que corte el LB y el cliente no sepa si se escribió), y tope de **3 filas
  exactas**, constante y no configurable.
- **Seguridad** — lo que se abre y lo que no, en dos tablas. Lo más importante:
  lista blanca de **tipo de concepto destino**, así que el endpoint no es
  «adjunta lo que sea a lo que sea»; validación por **firma binaria**, no por
  extensión ni `content_type`; y que **el endpoint no construye ni un
  identificador SQL a partir de la entrada**.
- **Configuración y permisos** — siete App Settings nuevas, **todas con defecto
  y con listas vacías**, de modo que desplegar el código no habilita nada. Con
  el aviso de que un campo sin defecto tumbaría toda la Function App, `sql/read`
  incluido, por el `@lru_cache` de `build_dependencies()`.
- **Impacto en consumidores** — ninguno, con la razón de cada uno.
- **Verificación** — cuatro niveles, y el bonito es el 3: la prueba de punta a
  punta **se hace con `documents/read`, que ya existe**, descargando el binario
  de vuelta por `cod` y comparando su `sha256`. La limpieza la hace Posventa
  desde la UI de Sigrid, que es la vía soportada; nosotros no borramos y no
  debemos poder.
- **Qué queda fuera** — borrado, versionado, ficheros grandes, el módulo
  `dog`/`condog`, la vía URL (F-023), y **abrir `sql/write` a la documental**,
  que se rechaza con argumento.

---

## 4 · Preguntas abiertas

Las diez van en §17 de la spec, cada una con la consulta de lectura que la
responde. Las **tres bloqueantes**:

| # | Pregunta | Cómo se responde |
|---|---|---|
| **Q1** | ¿Es la documental `READ_WRITE`, y en la misma instancia? | Dos llamadas a `sql/read`. Convierte la premisa de inferencia en dato |
| **Q2** | ¿Tiene el login de escritura usuario y permisos en la documental? | Un administrador del motor, con `EXECUTE AS USER` + `fn_my_permissions`. **La pasarela no puede**: `sql/read` usa siempre credenciales de lectura |
| **Q3** | ¿Qué columnas rellena Sigrid en la fila de la base **documental**? Está medido que `cod` e `ima` sí; del resto no hay medida | Un `SELECT` sobre el `cod` del parte de ejemplo, con `database` = la documental. **Si el ERP rellena más columnas, hay que replicarlas o el documento podría no abrirse desde la ficha** |

Las otras siete (no bloqueantes): qué significan los 4 dígitos de `gra.cod`; si
Sigrid usa `gra.guid`; la versión del motor (por `HASHBYTES`); si el ERP escribe
en `dbo.log` al importar un gráfico; si hay `cod` duplicados; el tamaño real de
los partes firmados; y si existe un entorno de pruebas de Sigrid.

---

## 5 · Qué significa esto para F-012 y F-023

**No se ha cambiado ningún estado**, y la decisión es del humano. Lo que la
investigación aporta:

- **El primer bloqueo de F-012 sigue en pie y ahora tiene solución escrita**:
  hacía falta un endpoint de dominio en `sigrid-api`, y aquí está especificado.
- **El segundo bloqueo de F-012 estaba mal enunciado.** Decía que la documental
  «no admite escritura». **Sí la admite**: el ERP le escribe a diario. Lo que
  hay es una **política** de la pasarela más, casi con seguridad, **un permiso
  que falta en el motor**. Sigue siendo decisión del dueño de `sigrid-api`,
  pero es una decisión distinta —y mucho más pequeña— de la que se creía:
  no es «abrir la base documental al ecosistema», es «conceder `INSERT` sobre
  una tabla a un login, y solo por una ruta».
- **F-023 (la vía URL) no queda invalidada.** Sigue bloqueada por una medida
  que solo Posventa puede dar, y sigue teniendo la ventaja de no tocar la
  documental. Si esta spec se implementa, F-023 deja de ser necesaria — pero eso
  lo decide el humano, no este informe.
- **Nada de esto afecta a F-009**, que solo escribe en la base de negocio.

---

## 6 · Qué se tocó en este repositorio

Un solo fichero, y es una línea:

- `docs/INTEGRACION.md` §3 bis — puntero corto a la spec al final del bloque
  que advertía a quien cogiera F-012. **La spec no se duplica aquí.**

`bash harness/init.sh` en verde tras el cambio.
