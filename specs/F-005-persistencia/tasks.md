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

- [x] **T1**: Comprobar que **F-004 está mergeada en `dev`** y rebasar esta
      rama sobre `dev`. Si F-004 no está mergeada, **PARAR**: los puertos de
      F-005 hablan `ResultadoValidacion`, `Veredicto`, `Destino` y
      `ClasificacionFirma` (design §1).
      **Verificación**: `git log dev --oneline --grep F-004` muestra el merge,
      y `git show dev:services/postventa-api/domain/models/validacion.py`
      existe.

- [x] **T2**: Copiar a `progress/impl_F-005.md` las **seis decisiones D1–D6, ya
      resueltas por el humano el 2026-08-19** y registradas en `design.md` §10.
      Ninguna bloquea: D1, D3, D4 y D6 confirman el diseño; **D2** obliga a las
      salvaguardas de `design.md` §6 y R37–R40 (T19 y T19 bis); **D3** fija cómo
      se comporta el script de Docker (T21); **D5** deja el DDL como candidato
      reconocido a ruta sensible, con la decisión en **F-017**.
      **Verificación**: la sección «Decisiones D1–D6» del informe está completa,
      sin ningún `PENDIENTE`, y cita la fecha 2026-08-19.

## Fase 1 · Configuración y dependencia

- [x] **T3**: Añadir `psycopg[binary]>=3.1,<4.0` a
      `services/postventa-api/requirements.txt` e instalarlo en el `.venv` del
      servicio.
      **Verificación**: `bash harness/init.sh` en verde (la suite existente no
      se mueve).

- [x] **T4**: Añadir a `config/settings.py` los diez campos `pg_*` de
      `design.md` §5, y reflejar sus **nombres** (nunca valores) en
      `.env.example` y `local.settings.json.example`.
      **Verificación**: `tests/test_f005_ajustes.py` comprueba los valores por
      defecto, que `pg_password` es opcional y que `/health` sigue arrancando
      sin ninguna variable `PG_*` definida.

## Fase 2 · Dominio (RED primero)

- [x] **T5**: **RED** — escribir `tests/test_f005_arquitectura.py`: dominio y
      aplicación no importan `psycopg` ni `infrastructure`; los puertos de
      persistencia existen en `domain/ports/`.
      **Verificación**: el test **falla** por `ModuleNotFoundError` del puerto
      inexistente. Traza pegada en `progress/impl_F-005.md`.

- [x] **T6**: Crear `domain/models/persistencia.py` (registros y enums de
      `design.md` §4.1) y añadir los cinco errores nuevos a
      `domain/models/errores.py`.
      **Verificación**: `tests/test_f005_modelos.py` comprueba que cada error
      hereda de `ErrorDePersistencia` y expone `.motivo`, y que los enums
      declaran exactamente los valores del diseño.

- [x] **T7**: Crear `domain/ports/persistencia.py` con `RepositorioPartesPort`
      y `RepositorioPreferenciasPort`.
      **Verificación**: `tests/test_f005_arquitectura.py` pasa (T5 en VERDE).

## Fase 3 · El DDL y su guarda (el corazón de la feature)

- [x] **T8**: **RED** — escribir `tests/test_f005_ddl_seguro.py` con los
      ejemplos hostiles **inventados** que deben ser rechazados:
      `CREATE DATABASE`, `CREATE ROLE`, `CREATE EXTENSION`, `ALTER SYSTEM`,
      `GRANT`, `DROP SCHEMA`, una tabla sin cualificar, una tabla en
      `public.`, y una columna `bytea`.
      **Verificación**: el test **falla** porque no existe
      `infrastructure/persistencia/ddl.py`. Traza pegada en el informe.

- [x] **T9**: Crear `infrastructure/persistencia/ddl.py`: `ficheros_ddl`,
      `sentencias`, `validar`, `cargar_ddl`, `valores_check`.
      **Verificación**: `tests/test_f005_ddl_seguro.py` en verde (R5, R6, R12)
      y `tests/test_f005_ddl_orden.py` comprueba el orden lexicográfico (R1).

- [x] **T10**: Escribir los siete `.sql` de `design.md` §4.1
      (`01_esquema.sql` … `07_preferencias.sql`), cada uno con su cabecera,
      todas las sentencias idempotentes y cualificadas.
      **Verificación**: `tests/test_f005_ddl_idempotente_texto.py` valida los
      `.sql` **reales** con `ddl.cargar_ddl` (R3) y comprueba que los `CHECK`
      de `validaciones` cubren exactamente los `Enum` de F-004 (R20).

- [x] **T11**: Crear `infrastructure/persistencia/conexion.py`
      (`es_host_local`, `dsn_desde_ajustes`, `sentencias_de_sesion`).
      **Verificación**: `tests/test_f005_conexion.py` comprueba que el
      `search_path` es solo el esquema y **no** incluye `public` (R8), que se
      fijan los tres timeouts y el `application_name` (R9), y que la
      contraseña no aparece nunca en el DSN construido.

- [x] **T12**: Crear `infrastructure/persistencia/arranque.py`
      (`puede_aplicar_ddl`, `asegurar_esquema`).
      **Verificación**: `tests/test_f005_arranque.py`, con el doble de
      conexión: se niega a aplicar DDL desde `entorno=local` contra un host
      remoto (R11); toma y **libera** el `pg_advisory_lock` incluso si el DDL
      revienta (R10); no reejecuta el DDL en la segunda llamada del mismo
      proceso (R2).

## Fase 4 · SQL, mapeo y adaptador

- [x] **T13**: Crear `tests/utiles_pg.py` con el **doble de conexión** (imita
      la DBAPI, graba lo ejecutado, devuelve filas preparadas). Sin `test_` en
      el nombre, como `utiles_ia.py` y `utiles_pdf.py`.
      **Verificación**: se usa desde T12 y T14–T17; no aporta test propio.

- [x] **T14**: Crear `infrastructure/persistencia/sentencias.py`: los
      `INSERT ... ON CONFLICT (hash_parte) DO UPDATE`, el `SELECT` de la cola
      con su `JOIN` a `partes`, y el `UPDATE` de cierre con
      `WHERE estado <> 'cerrado'`.
      **Verificación**: `tests/test_f005_sentencias.py` — R14, R17, R22, R25;
      y que ningún valor se interpola en el texto del SQL.

- [x] **T15**: Crear `infrastructure/persistencia/mapeo.py`, iterando
      `CAMPOS_DEL_PARTE` para las 18 columnas de valor y confianza.
      **Verificación**: `tests/test_f005_mapeo.py` hace ida y vuelta con una
      `ExtraccionParte` y un `ResultadoValidacion` **inventados** (R18, R19,
      R20) y comprueba que añadir un campo al contrato rompe el test, no la
      producción.

- [x] **T16**: Crear `infrastructure/persistencia/repositorio_pg.py` con los
      dos puertos implementados.
      **Verificación**: `tests/test_f005_repositorio.py` contra el doble:
      conserva `primera_vez_at_utc` e incrementa `reprocesos` (R15);
      sustituye la validación en vez de acumularla (R17); deja una sola fila
      de archivo por parte (R23); no pisa un cierre terminal y devuelve
      `SIN_CAMBIOS` (R25); registra motivo e intentos de un cierre fallido
      (R26).

- [x] **T17**: Implementar preferencias por usuario en el mismo adaptador.
      **Verificación**: `tests/test_f005_preferencias.py` — una sola fila por
      `usuario_oid` (R27), revocar deja `auto_cierre=false` con su marca de
      tiempo (R28), y no se guarda ni correo ni nombre.

- [x] **T18**: Crear `infrastructure/persistencia/fabrica.py` y
      `application/pipelines/paso_persistencia.py`.
      **Verificación**: `tests/test_f005_fabrica.py` levanta
      `ConfiguracionPgIncompleta` si falta host, base, usuario o contraseña;
      `tests/test_f005_paso_persistencia.py` comprueba que el paso habla con
      el **puerto** (doble en memoria) y no con el adaptador (R30, R31).

- [x] **T19**: Añadir `tests/test_f005_logs_sin_datos_personales.py`: capturar
      el logger mientras se guarda un parte con DNI y observaciones
      **inventados** y comprobar que ninguno de los dos valores aparece en la
      salida (R29, R37).
      **Verificación**: el test pasa, y falla si se quita el saneado.

- [x] **T19 bis**: Añadir `tests/test_f005_repo_sin_datos_personales.py`: barrer
      los ficheros de la feature —`specs/F-005-persistencia/`, `tests/`,
      `tests_bbdd/`, `infrastructure/persistencia/`— buscando un patrón de DNI
      español y fallar si aparece alguno (R38). Es la salvaguarda que exige D2:
      el DNI se guarda en base, **nunca en el repositorio**.
      **Verificación**: el test pasa sobre el árbol real, y falla si se le
      inyecta un DNI de prueba en un fichero temporal.

## Fase 5 · Base efímera

- [x] **T20**: Crear `services/postventa-api/tests_bbdd/` con su `conftest.py`
      (aborta si `POSTVENTA_PG_TEST_DSN` no apunta a host local, R34) y los
      tres tests de `design.md` §7.2, todos con `skipif` sobre esa variable
      (R33).
      **Verificación**: `bash harness/init.sh` en verde **con la variable sin
      definir** — los tres salen `skipped` y la suite por defecto sigue sin
      abrir ni una conexión (R32).

- [x] **T21**: Crear `infra/pruebas_bbdd_efimera.ps1` (levanta, ejecuta y tira
      la base desechable, con `try/finally`) y `infra/crear_base_postventa.ps1`
      (una sola vez, con confirmación escrita). Ningún secreto versionado.

      **Lo que fija la decisión D3 del humano (2026-08-19), verificado en su
      puesto**: hay **Docker 29.5.3 instalado**, el **demonio puede estar
      parado** (Docker Desktop cerrado) y **no hay `psql` en el `PATH`**. Por
      tanto:

      1. El script comprueba **lo primero** que el demonio responde
         (`docker info`) y, si no, **aborta con un mensaje accionable** —del
         tipo «Docker está instalado pero el demonio no responde: arranca
         Docker Desktop y vuelve a lanzar»— en vez de seguir y morir con un
         error opaco de conexión a la base (R35). Distinguir los dos casos:
         Docker no instalado, y Docker instalado con el demonio parado.
      2. **No se usa `psql` en ningún punto** (R36): la espera a que la base
         acepte conexiones y cualquier comprobación se hacen con `psycopg`
         desde el `.venv` del servicio, o con `docker exec` dentro del
         contenedor.

      **Verificación**: revisión del script; con Docker Desktop cerrado el
      script sale con el mensaje accionable y **código de salida distinto de
      cero**, sin dejar contenedores vivos; con Docker arrancado, M1 más abajo.

      **Hecho, y con la revisión convertida en test.** Una revisión no
      sobrevive a la siguiente edición del script, así que el contrato de los
      dos `.ps1` lo comprueba `tests/test_f005_scripts_infra.py` (17 tests):
      R7, R35, R36, el `finally` que destruye el contenedor, que ninguna
      credencial viaje por la línea de comandos y que el Python incrustado
      compile. Es el mismo patrón con el que el DDL en `.sql` se comprueba
      desde `test_f005_ddl_seguro.py`, y hace falta por lo mismo:
      `harness/alcance.py` solo mide y muta `.py`.

      Ejecutado de verdad con el demonio parado: **código de salida 3** y el
      mensaje accionable, sin contenedores vivos (traza en
      `progress/impl_F-005.md`).

## Fase 6 · Documentación del ecosistema

- [x] **T22**: Crear `docs/INTEGRACION.md` (qué base, qué esquema, qué
      variables, qué volumen esperamos, qué rompe a otros) y actualizar la
      fila de PostgreSQL de `docs/ARCHITECTURE.md`. **Solo nombres, ningún
      valor**: ni host, ni usuario, ni contraseña, ni IDs.
      **Verificación**: `tests/test_f005_integracion_sin_secretos.py` barre el
      documento buscando patrones de host, GUID y credencial, y falla si
      encuentra alguno.

      **Hecho, con fase RED** (traza en `progress/impl_F-005.md`): el test se
      escribió antes que el documento y falló por `FileNotFoundError`. Son 22
      tests: seis familias de patrones prohibidos (FQDN de Azure, GUID,
      `VARIABLE=valor`, `password=`, URI con credencial incrustada e IPv4 que
      no sea el bucle local), cada una con su control negativo inyectado y con
      su control positivo de texto legítimo, más la comprobación de que el
      documento existe, nombra las once variables y no queda huérfano en
      `docs/ARCHITECTURE.md`.

## Fase 7 · Puertas de rigor

- [x] **T23**: Ejecutar la campaña de mutación y dejar el informe.
      **Verificación**: `python -m harness.mutacion --feature F-005` genera
      `progress/mutacion_F-005.md` con **cero supervivientes**; cada
      superviviente que aparezca se mata con un test nuevo y se vuelve a
      lanzar.
      **Hecho el 2026-08-19, en dos vueltas.** Campaña completa (sin muestreo)
      sobre 2.206 líneas cambiadas en 14 ficheros. Primera vuelta (15:33):
      104 mutantes, 71 muertos, **31 supervivientes**, 2 timeouts, 250,2 s.
      Los 31 se mataron con test (19 de ellos en el troceador de `ddl.py`) en
      dos tandas, `0b13e3b` y `84736ea`. Campaña final (16:13): **104
      mutantes, 101 muertos, 0 supervivientes, 3 timeouts, 395,0 s**. Los tres
      timeouts son el mismo defecto —la mutación rompe el avance del escáner y
      el bucle no termina—, no se pueden matar con un test y se verifican bajo
      `timeout 15`: exit 124 los tres. Análisis completo en
      `progress/mutacion_F-005.md` y copia durable en
      `progress/impl_F-005.md`.

- [x] **T24**: **MANUAL (humano) · M1 — suite contra base efímera.**
      **Requisito previo**: Docker Desktop **abierto** (el 2026-08-19 estaba
      instalado —29.5.3— pero con el demonio parado; si sigue parado, el script
      lo dirá y saldrá, T21).
      Comando exacto, una línea, sin `&&` ni pipes, desde la raíz del
      repositorio en PowerShell:

      powershell -ExecutionPolicy Bypass -File infra\pruebas_bbdd_efimera.ps1

      **Verificación**: los tres tests de `tests_bbdd/` pasan (DDL idempotente
      dos veces, reproceso sin duplicar, `public` sin ninguna tabla nuestra) y
      el contenedor queda destruido. El resultado real se pega en
      `progress/impl_F-005.md`; «debería funcionar» no vale.

      **EJECUTADA POR EL HUMANO el 2026-08-19. Resultado real: en verde** —
      `10 passed in 2.40s` contra `postgres:16-alpine` en `127.0.0.1:55432`,
      y el contenedor destruido (comprobado después con `docker ps -a`, que no
      lista ninguno). Son **10** tests, no tres: la verificación se escribió
      contando los tres criterios, y cada uno se cubre con varios casos; son
      exactamente los 10 que la suite normal declara `skipped`. El primer
      intento, con el demonio de Docker parado, abortó en el primer paso con
      su mensaje accionable, que es la otra mitad de T21. Detalle en
      `progress/impl_F-005.md`.

- [x] **T25**: **MANUAL (humano) · M2 — primera aplicación del DDL contra la
      base real de dev.** Escritura en un servidor compartido: la ejecuta el
      humano, nunca un agente, y **solo después** de M1 en verde.
      Primero el dry-run, que no abre conexión:

      python -c "from infrastructure.persistencia.ddl import cargar_ddl; from pathlib import Path; print(chr(10).join(cargar_ddl(Path('infrastructure/persistencia/sql'), esquema='postventa')))"

      y luego, con las sentencias revisadas delante:

      powershell -ExecutionPolicy Bypass -File infra\crear_base_postventa.ps1

      **Verificación**: la base `postventa` existe con el esquema `postventa`,
      el `information_schema` lista las seis tablas, y una segunda ejecución
      no falla ni cambia nada. Resultado real en `progress/impl_F-005.md`.

      **EJECUTADA POR EL HUMANO el 2026-08-19. Resultado real: `VEREDICTO M2:
      OK` en las dos pasadas.** La base `postventa` existe con su esquema
      `postventa`, el catálogo lista **las seis tablas** y 13 índices (los 7
      nuestros más los 6 de clave primaria), **ninguna tabla nuestra en
      `public`** y 0 filas en todas. La segunda ejecución dijo «el rol ya
      existia: no se toca» y «la base ya existia: no se toca», reaplicó el DDL
      sin error y dejó el catálogo idéntico. El dry-run previo enseñó las 14
      sentencias, todas `IF NOT EXISTS` y todas cualificadas con `postventa.`.
      **Dos correcciones a esta tarea, comprobadas al ejecutarla**: el comando
      necesita el conmutador **`-AplicarDdl`** —sin él el script solo crea rol
      y base, y no habría ninguna tabla que verificar—, y el dry-run se entregó
      como script en el home del humano, porque PowerShell parte el `python -c`
      de una línea al pegarlo.

- [~] **T26**: **MANUAL (humano) · M3 — copiar `docs/INTEGRACION.md` a
      `azure-apps/postventa_incidencias.md`** y dar de alta la fila en su
      `README.md`. Es **otro repositorio git**: lo commitea el humano, no un
      agente (design §11). Cabecera obligatoria con origen y fecha, y ni un
      valor de conexión.
      **Verificación**: el fichero existe en `azure-apps/` y su commit consta
      en `progress/impl_F-005.md`.

      **HECHA A MEDIAS el 2026-08-19, por decisión del humano.** El fichero
      `postventa_incidencias.md` (172 líneas, cabecera correcta, barrido de
      secretos limpio) y la fila del `README.md` **están escritos** en el árbol
      de `azure-apps`. **El commit NO se ha hecho**: el humano decidió dejarlo
      así. Por eso la casilla queda `[~]` y no `[x]` — el contenido está, el
      registro no. Sin commit, el documento no tiene fecha comprobable ni
      historial y una limpieza del árbol se lo lleva. Detalle en
      `progress/impl_F-005.md`.

- [x] **T27**: Ejecutar `bash harness/init.sh` en verde.
      **Verificación**: exit code 0, con la puerta de cobertura de las líneas
      cambiadas en `[OK]` y por encima del umbral de
      `harness/rigor.json` (80 %).
      **Hecho el 2026-08-19**: exit code 0 y `ENTORNO LISTO`. `16 passed` en
      la suite del arnés y `678 passed, 10 skipped in 20.22s` en la del
      servicio `api` (los 10 saltados son los `tests_bbdd/`, apagados sin su
      variable de entorno: son M1/T24, del humano).
      `[OK] PUERTA COBERTURA: 97.0% de 591 líneas cambiadas cubiertas
      (573/591, umbral 80%, nivel critico)`. Salida íntegra pegada en
      `progress/impl_F-005.md`.
