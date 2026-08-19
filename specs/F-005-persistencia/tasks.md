<!-- specs/F-005-persistencia/tasks.md -->
# F-005 · Persistencia en el PostgreSQL compartido — Tareas

> Un commit por tarea, mensaje `F-005 Tn: descripción`. Rama
> `feature/F-005-persistencia`. Rigor **`critico`**: fase RED con la traza
> real pegada en `progress/impl_F-005.md`, cobertura de las líneas cambiadas,
> campaña de mutación con **cero supervivientes**, y las verificaciones
> `MANUAL (humano)` con su comando exacto y su resultado real.
>
> **Ni un dato real** en ningún fichero de esta feature: los ejemplos de los
> tests son inventados y se marcan como tales en el propio fichero.

## Fase 0 · Precondición

- [ ] **T1**: Comprobar que **F-004 está mergeada en `dev`** y rebasar esta
      rama sobre `dev`. Si F-004 no está mergeada, **PARAR**: los puertos de
      F-005 hablan `ResultadoValidacion`, `Veredicto`, `Destino` y
      `ClasificacionFirma` (design §1).
      **Verificación**: `git log dev --oneline --grep F-004` muestra el merge,
      y `git show dev:services/postventa-api/domain/models/validacion.py`
      existe.

- [ ] **T2**: Registrar en `progress/impl_F-005.md` la respuesta del humano a
      las **seis decisiones abiertas** D1–D6 de `design.md`. Si alguna sigue
      sin respuesta y bloquea (D1 y D3 bloquean; D2 bloquea el esquema de
      `partes`), marcar la feature `blocked` y parar.
      **Verificación**: la sección «Decisiones D1–D6» del informe está
      completa, sin ningún `PENDIENTE`.

## Fase 1 · Configuración y dependencia

- [ ] **T3**: Añadir `psycopg[binary]>=3.1,<4.0` a
      `services/postventa-api/requirements.txt` e instalarlo en el `.venv` del
      servicio.
      **Verificación**: `bash harness/init.sh` en verde (la suite existente no
      se mueve).

- [ ] **T4**: Añadir a `config/settings.py` los diez campos `pg_*` de
      `design.md` §5, y reflejar sus **nombres** (nunca valores) en
      `.env.example` y `local.settings.json.example`.
      **Verificación**: `tests/test_f005_ajustes.py` comprueba los valores por
      defecto, que `pg_password` es opcional y que `/health` sigue arrancando
      sin ninguna variable `PG_*` definida.

## Fase 2 · Dominio (RED primero)

- [ ] **T5**: **RED** — escribir `tests/test_f005_arquitectura.py`: dominio y
      aplicación no importan `psycopg` ni `infrastructure`; los puertos de
      persistencia existen en `domain/ports/`.
      **Verificación**: el test **falla** por `ModuleNotFoundError` del puerto
      inexistente. Traza pegada en `progress/impl_F-005.md`.

- [ ] **T6**: Crear `domain/models/persistencia.py` (registros y enums de
      `design.md` §4.1) y añadir los cinco errores nuevos a
      `domain/models/errores.py`.
      **Verificación**: `tests/test_f005_modelos.py` comprueba que cada error
      hereda de `ErrorDePersistencia` y expone `.motivo`, y que los enums
      declaran exactamente los valores del diseño.

- [ ] **T7**: Crear `domain/ports/persistencia.py` con `RepositorioPartesPort`
      y `RepositorioPreferenciasPort`.
      **Verificación**: `tests/test_f005_arquitectura.py` pasa (T5 en VERDE).

## Fase 3 · El DDL y su guarda (el corazón de la feature)

- [ ] **T8**: **RED** — escribir `tests/test_f005_ddl_seguro.py` con los
      ejemplos hostiles **inventados** que deben ser rechazados:
      `CREATE DATABASE`, `CREATE ROLE`, `CREATE EXTENSION`, `ALTER SYSTEM`,
      `GRANT`, `DROP SCHEMA`, una tabla sin cualificar, una tabla en
      `public.`, y una columna `bytea`.
      **Verificación**: el test **falla** porque no existe
      `infrastructure/persistencia/ddl.py`. Traza pegada en el informe.

- [ ] **T9**: Crear `infrastructure/persistencia/ddl.py`: `ficheros_ddl`,
      `sentencias`, `validar`, `cargar_ddl`, `valores_check`.
      **Verificación**: `tests/test_f005_ddl_seguro.py` en verde (R5, R6, R12)
      y `tests/test_f005_ddl_orden.py` comprueba el orden lexicográfico (R1).

- [ ] **T10**: Escribir los siete `.sql` de `design.md` §4.1
      (`01_esquema.sql` … `07_preferencias.sql`), cada uno con su cabecera,
      todas las sentencias idempotentes y cualificadas.
      **Verificación**: `tests/test_f005_ddl_idempotente_texto.py` valida los
      `.sql` **reales** con `ddl.cargar_ddl` (R3) y comprueba que los `CHECK`
      de `validaciones` cubren exactamente los `Enum` de F-004 (R20).

- [ ] **T11**: Crear `infrastructure/persistencia/conexion.py`
      (`es_host_local`, `dsn_desde_ajustes`, `sentencias_de_sesion`).
      **Verificación**: `tests/test_f005_conexion.py` comprueba que el
      `search_path` es solo el esquema y **no** incluye `public` (R8), que se
      fijan los tres timeouts y el `application_name` (R9), y que la
      contraseña no aparece nunca en el DSN construido.

- [ ] **T12**: Crear `infrastructure/persistencia/arranque.py`
      (`puede_aplicar_ddl`, `asegurar_esquema`).
      **Verificación**: `tests/test_f005_arranque.py`, con el doble de
      conexión: se niega a aplicar DDL desde `entorno=local` contra un host
      remoto (R11); toma y **libera** el `pg_advisory_lock` incluso si el DDL
      revienta (R10); no reejecuta el DDL en la segunda llamada del mismo
      proceso (R2).

## Fase 4 · SQL, mapeo y adaptador

- [ ] **T13**: Crear `tests/utiles_pg.py` con el **doble de conexión** (imita
      la DBAPI, graba lo ejecutado, devuelve filas preparadas). Sin `test_` en
      el nombre, como `utiles_ia.py` y `utiles_pdf.py`.
      **Verificación**: se usa desde T12 y T14–T17; no aporta test propio.

- [ ] **T14**: Crear `infrastructure/persistencia/sentencias.py`: los
      `INSERT ... ON CONFLICT (hash_parte) DO UPDATE`, el `SELECT` de la cola
      con su `JOIN` a `partes`, y el `UPDATE` de cierre con
      `WHERE estado <> 'cerrado'`.
      **Verificación**: `tests/test_f005_sentencias.py` — R14, R17, R22, R25;
      y que ningún valor se interpola en el texto del SQL.

- [ ] **T15**: Crear `infrastructure/persistencia/mapeo.py`, iterando
      `CAMPOS_DEL_PARTE` para las 18 columnas de valor y confianza.
      **Verificación**: `tests/test_f005_mapeo.py` hace ida y vuelta con una
      `ExtraccionParte` y un `ResultadoValidacion` **inventados** (R18, R19,
      R20) y comprueba que añadir un campo al contrato rompe el test, no la
      producción.

- [ ] **T16**: Crear `infrastructure/persistencia/repositorio_pg.py` con los
      dos puertos implementados.
      **Verificación**: `tests/test_f005_repositorio.py` contra el doble:
      conserva `primera_vez_at_utc` e incrementa `reprocesos` (R15);
      sustituye la validación en vez de acumularla (R17); deja una sola fila
      de archivo por parte (R23); no pisa un cierre terminal y devuelve
      `SIN_CAMBIOS` (R25); registra motivo e intentos de un cierre fallido
      (R26).

- [ ] **T17**: Implementar preferencias por usuario en el mismo adaptador.
      **Verificación**: `tests/test_f005_preferencias.py` — una sola fila por
      `usuario_oid` (R27), revocar deja `auto_cierre=false` con su marca de
      tiempo (R28), y no se guarda ni correo ni nombre.

- [ ] **T18**: Crear `infrastructure/persistencia/fabrica.py` y
      `application/pipelines/paso_persistencia.py`.
      **Verificación**: `tests/test_f005_fabrica.py` levanta
      `ConfiguracionPgIncompleta` si falta host, base, usuario o contraseña;
      `tests/test_f005_paso_persistencia.py` comprueba que el paso habla con
      el **puerto** (doble en memoria) y no con el adaptador (R30, R31).

- [ ] **T19**: Añadir `tests/test_f005_logs_sin_datos_personales.py`: capturar
      el logger mientras se guarda un parte con DNI y observaciones
      **inventados** y comprobar que ninguno de los dos valores aparece en la
      salida (R29).
      **Verificación**: el test pasa, y falla si se quita el saneado.

## Fase 5 · Base efímera

- [ ] **T20**: Crear `services/postventa-api/tests_bbdd/` con su `conftest.py`
      (aborta si `POSTVENTA_PG_TEST_DSN` no apunta a host local, R34) y los
      tres tests de `design.md` §7.2, todos con `skipif` sobre esa variable
      (R33).
      **Verificación**: `bash harness/init.sh` en verde **con la variable sin
      definir** — los tres salen `skipped` y la suite por defecto sigue sin
      abrir ni una conexión (R32).

- [ ] **T21**: Crear `infra/pruebas_bbdd_efimera.ps1` (levanta, ejecuta y tira
      la base desechable, con `try/finally`) y `infra/crear_base_postventa.ps1`
      (una sola vez, con confirmación escrita). Ningún secreto versionado.
      **Verificación**: revisión del script + M1 más abajo.

## Fase 6 · Documentación del ecosistema

- [ ] **T22**: Crear `docs/INTEGRACION.md` (qué base, qué esquema, qué
      variables, qué volumen esperamos, qué rompe a otros) y actualizar la
      fila de PostgreSQL de `docs/ARCHITECTURE.md`. **Solo nombres, ningún
      valor**: ni host, ni usuario, ni contraseña, ni IDs.
      **Verificación**: `tests/test_f005_integracion_sin_secretos.py` barre el
      documento buscando patrones de host, GUID y credencial, y falla si
      encuentra alguno.

## Fase 7 · Puertas de rigor

- [ ] **T23**: Ejecutar la campaña de mutación y dejar el informe.
      **Verificación**: `python -m harness.mutacion --feature F-005` genera
      `progress/mutacion_F-005.md` con **cero supervivientes**; cada
      superviviente que aparezca se mata con un test nuevo y se vuelve a
      lanzar.

- [ ] **T24**: **MANUAL (humano) · M1 — suite contra base efímera.**
      Comando exacto, una línea, sin `&&` ni pipes, desde la raíz del
      repositorio en PowerShell:

      powershell -ExecutionPolicy Bypass -File infra\pruebas_bbdd_efimera.ps1

      **Verificación**: los tres tests de `tests_bbdd/` pasan (DDL idempotente
      dos veces, reproceso sin duplicar, `public` sin ninguna tabla nuestra) y
      el contenedor queda destruido. El resultado real se pega en
      `progress/impl_F-005.md`; «debería funcionar» no vale.

- [ ] **T25**: **MANUAL (humano) · M2 — primera aplicación del DDL contra la
      base real de dev.** Escritura en un servidor compartido: la ejecuta el
      humano, nunca un agente, y **solo después** de M1 en verde.
      Primero el dry-run, que no abre conexión:

      python -c "from infrastructure.persistencia.ddl import cargar_ddl; from pathlib import Path; print(chr(10).join(cargar_ddl(Path('infrastructure/persistencia/sql'), esquema='postventa')))"

      y luego, con las sentencias revisadas delante:

      powershell -ExecutionPolicy Bypass -File infra\crear_base_postventa.ps1

      **Verificación**: la base `postventa` existe con el esquema `postventa`,
      el `information_schema` lista las seis tablas, y una segunda ejecución
      no falla ni cambia nada. Resultado real en `progress/impl_F-005.md`.

- [ ] **T26**: **MANUAL (humano) · M3 — copiar `docs/INTEGRACION.md` a
      `azure-apps/postventa_incidencias.md`** y dar de alta la fila en su
      `README.md`. Es **otro repositorio git**: lo commitea el humano, no un
      agente (design §11). Cabecera obligatoria con origen y fecha, y ni un
      valor de conexión.
      **Verificación**: el fichero existe en `azure-apps/` y su commit consta
      en `progress/impl_F-005.md`.

- [ ] **T27**: Ejecutar `bash harness/init.sh` en verde.
      **Verificación**: exit code 0, con la puerta de cobertura de las líneas
      cambiadas en `[OK]` y por encima del umbral de
      `harness/rigor.json` (80 %).
