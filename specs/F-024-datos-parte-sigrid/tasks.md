<!-- specs/F-024-datos-parte-sigrid/tasks.md -->
# F-024 · Datos del parte enlazados a Sigrid, para el datamart — Tareas

> Una tarea = un commit `F-024 Tn: ...`. Ordenadas por dependencia; los tests
> van antes o junto a la implementación (fase RED en los requisitos centrales:
> R1, R3, R9, R13, R16–R20, R27). Rigor `estandar`.
>
> **Ninguna pregunta abierta bloquea el arranque**: P1 y P3 de `design.md` §13
> son una columna al final o un atributo del front y se aplican en T7/T9 según
> lo que el humano decida al aprobar; P4 es del arnés (T13 la da por resuelta
> en (a) salvo que el humano diga otra cosa); P2, P5 y P6 son «no hacer» o
> calendario.
>
> **La rama**: `feature/F-024-datos-parte-sigrid`, creada desde
> `feature/F-012-grafico-sigrid` (F-024 necesita `postventa.graficos` y
> `reclamacion_ide`, que nacen en F-012). Lo confirma el líder al arrancar.
>
> **PROHIBIDO** ejecutar nada contra Azure, Sigrid, `sigrid-api`, el
> PostgreSQL compartido ni SharePoint desde el implementer; lo que exige base
> real es `MANUAL (humano)` y va en el bloque 6.
>
> **Ni un dato personal**: los ejemplos de tests y fixtures son inventados
> (`00000000T`, `INDUSTRIAL DE PRUEBA S.L.`, `Fontanería`, `baño`); nada de
> `muestras/` entra en el repositorio (T14 lo lee, no lo copia).

## Bloque 1 · El contrato de extracción (dominio, sin red, sin BBDD, sin IA)

- [ ] **T1**: Ampliar `domain/models/extraccion.py`: `CAMPOS_DEL_PARTE` con
      `oficio`, `empresa`, `estancia`, `hora_inicio`, `hora_fin` **al final**
      y en ese orden; `CAMPOS_MANUSCRITOS` con `hora_inicio` y `hora_fin`;
      docstrings sin «nueve». Ampliar `tests/utiles_ia.py::CAMPOS_DE_EJEMPLO`
      con los cinco (valores inventados; las horas a `None`). Adaptar los
      censos a mano citando F-024: `test_f003_extraccion_dominio.py`
      (`CAMPOS_MANUSCRITOS ==`), `test_f003_paso_extraccion.py`
      (`len(CAMPOS_DEL_PARTE) == 14`), `test_f004_prompts_firma.py`
      (`CAMPOS_DEL_PARTE_A_MANO`). | Verificación: `test_f024_extraccion_campos.py`
      —R1 (la tupla, a mano, catorce en ese orden; los ocho de contenido siguen
      siendo prefijo), R2 (un valor y una confianza `"85"` en `oficio` salen
      saneados por el mismo camino), R3 (**RED primero**: con `validar_parte`
      real, un parte apto sigue apto con los cinco a `None`/`0` **y** con los
      cinco rellenos; uno de la cola sigue en la cola; uno de revisión manual
      sigue igual), R6 (`schema_para("parte_posventa")` trae los catorce como
      `required` y `properties` en orden), R8 (el censo de `ContextoParte` de
      `test_f003_r7_*` **no se toca** y sigue en verde)—, y la suite de F-003 y
      F-004 en verde.

- [ ] **T2**: `config/prompts.yaml`: `parte_posventa_es` pasa a `version: "2"`
      y su `task` describe los cinco campos (`design.md` §7.1); el `system`
      solo si hace falta nombrar «estancia» junto a «oficio, empresa».
      `firma_parte_es` **intacto**. Actualizar `HUELLA_DEL_PROMPT_MEDIDO` en
      `test_f004_prompts_firma.py` con la huella nueva, con comentario que cite
      F-024 y la verificación M1 (T14) que vuelve a medir; `version == "2"`. |
      Verificación: `test_f024_prompt.py`: R4 (el YAML real nombra los cinco
      campos en `task`, `version == "2"`, y ni un patrón de DNI ni un nombre
      real —reutilizar el barrido de `test_f005_repo_sin_datos_personales`—),
      R5 (la huella de `firma_parte_es`, **escrita a mano** con el valor que
      tiene hoy, no cambia). `test_f003_prompts_yaml.py` y
      `test_f004_prompts_firma.py` en verde.

- [ ] **T3**: Comprobar el borde sin tocarlo: `POST /api/extraer` serializa
      catorce, `POST /api/validar` y `POST /api/parte` exigen catorce. |
      Verificación: en `test_f024_extraccion_campos.py`, R7: `extraer_parte`
      con `ExtractorFalso` devuelve las catorce claves; `cuerpos.a_extraccion`
      con un cuerpo de nueve responde `CuerpoDeValidacionInvalido` nombrando
      los cinco que faltan. `test_f003_extraer_http.py`, `test_f004_validar_http.py`
      y `test_f019_parte_http.py` en verde (sus fixtures usan `utiles_ia`/
      `utiles_validacion`, que ya traen catorce desde T1).

## Bloque 2 · Las columnas nuevas y la clave del ERP

- [ ] **T4**: Crear `infrastructure/persistencia/sql/10_partes_campos_datamart.sql`
      (`design.md` §8.1: diez `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`, una
      columna por sentencia, en el orden de la tupla) y añadirlo a la lista de
      `test_f005_ddl_idempotente_texto.py::test_f005_r1_se_aplican_todos_los_ficheros_en_orden`.
      | Verificación: `test_f024_ddl_columnas.py` (**RED primero** sobre R9):
      el fichero real pasa `validar` sentencia a sentencia con
      `ESQUEMA_LITERAL`; son exactamente diez sentencias; cada una es un
      `ALTER TABLE postventa.partes ADD COLUMN IF NOT EXISTS <col> <tipo>` con
      `<col>` en el orden de `columnas_de_campos()[18:]` (derivado, no a mano)
      y `integer NOT NULL DEFAULT 0` en las confianzas; `cargar_ddl` del
      directorio completo carga sin `DdlInseguro` (R14, R28); `ficheros_ddl`
      lo devuelve detrás de `09_graficos.sql`. **Los tests que busquen verbos
      prohibidos miran las sentencias (`cargar_ddl`), no el texto crudo**: la
      cabecera del `.sql` puede nombrar `GRANT` al explicar por qué no se usa.

- [ ] **T5**: Comprobar el mapeo y la sentencia del parte **sin tocar código**
      (`mapeo.py` y `upsert_parte` derivan de la tupla) y actualizar
      `test_f005_mapeo.py::COLUMNAS_ESPERADAS` a veintiocho, a mano. |
      Verificación: `test_f024_persistencia.py`: R10 (`columnas_de_campos()`
      son 28, las últimas diez con los nombres nuevos; `upsert_parte` tiene un
      marcador por columna y el único `::jsonb` sigue en `avisos_extraccion`),
      R11 (un `ExtraccionParte` con los cinco campos a `None`/`0` se guarda con
      el doble de PG sin error y con los 28 valores en su posición; reprocesar
      el mismo `hash` produce `ACTUALIZADO`). `test_f005_mapeo.py`,
      `test_f005_sentencias.py`, `test_f005_repositorio.py` en verde.

- [ ] **T6**: `reclamacion_ide` en el cierre: `TrazaCierre.reclamacion_ide`
      (`domain/models/persistencia.py`), `paso_cierre._traza` lo rellena con
      `plan.reclamacion.ide`, `upsert_cierre` lo escribe (columna detrás de
      `numero_incidencia`, parámetro en la misma posición), y el fichero
      `11_cierres_reclamacion_ide.sql` (`design.md` §8.2) en la lista de
      ficheros del test de F-005. | Verificación: **RED primero** sobre R13 en
      `test_f024_persistencia.py`: con `ErpEnMemoria` y el doble de PG, las
      trazas `dry_run_ok`, `cerrado`, `error` (fallo de `erp.cerrar`) y
      `ya_cerrada` llevan `reclamacion_ide == reclamacion.ide`; `upsert_cierre`
      lo lleva como **parámetro** y no pegado; el `WHERE estado <> 'cerrado'`
      sigue (R25 de F-005: un `cerrado` no se pisa). En
      `test_f024_ddl_columnas.py`, R12: el fichero real es **una** sentencia
      `ALTER TABLE postventa.cierres ADD COLUMN IF NOT EXISTS reclamacion_ide
      integer`, sin `NOT NULL`. `test_f009_paso_cierre.py`,
      `test_f012_cerrar_exige_grafico.py` y `test_f005_sentencias.py` en verde
      (si alguna aserción cuenta parámetros de `upsert_cierre`, se ajusta
      citando R13; **no** se retira ninguna otra aserción de F-009).

## Bloque 3 · La vista

- [ ] **T7**: Crear `infrastructure/persistencia/sql/12_v_partes_sigrid.sql`
      (`design.md` §8.3, con `observaciones` como última columna **solo si**
      el humano eligió (b) en P1) y añadirlo a la lista de ficheros del test de
      F-005. | Verificación: `test_f024_vista.py` sobre el **texto real**
      (**RED primero** sobre R16–R20 y R27): la lista ordenada de columnas,
      **escrita a mano** (59, o 60 con (b)), coincide con la que se extrae del
      `SELECT` (R27); para cada campo de `CAMPOS_DEL_PARTE` salvo `dni_cliente`
      y `observaciones` aparecen `p.<campo>` y `p.<campo>_confianza_pct`
      (derivado de la tupla: un campo futuro sin columna en la vista rompe la
      suite) (R18); `tiene_observaciones` con `btrim` y
      `observaciones_confianza_pct` (R19); la sentencia (sin comentarios) **no
      contiene** `dni`, `usuario_oid`, `confirmado_por`, `motivo`, `avisos`,
      `paginas_origen` (R20); exactamente cuatro `LEFT JOIN`, cada uno
      `ON x.hash_parte = p.hash_parte`, ningún `WHERE`, `DISTINCT`, `GROUP BY`
      ni `UNION` (R16, R26); `COALESCE(g.reclamacion_ide, c.reclamacion_ide)`
      y `COALESCE(c.numero_incidencia, g.numero_incidencia)` (R17); las
      columnas de R21–R25 con esos nombres exactos; `validar` acepta la
      sentencia con `ESQUEMA_LITERAL` y con `otro_inventado` (la sustitución
      de esquema alcanza a las cinco tablas y a la vista); `ficheros_ddl` la
      deja la última (R15, R28); `public.` ausente del texto crudo.

## Bloque 4 · El front

- [ ] **T8**: `services/postventa-front/js/pipeline.js::CAMPOS_DEL_PARTE` a
      catorce en el orden del dominio; adaptar `tests_js/pipeline.test.js`
      (censo a mano) y las fixtures con nueve campos de `tests_js/*.test.js`
      (`persistencia.test.js` y las que `grep -l numero_pagina` encuentre). |
      Verificación: `node --test tests_js` (por el puente
      `tests/test_f007_js.py`): R29 (el cuerpo de validar y el de parte llevan
      las catorce claves; la lista a mano es la del dominio), R30 (los cuerpos
      de archivar, adjuntar y cerrar **no** llevan ninguno de los cinco nombres
      nuevos: aserción nueva sobre `cuerpoDeArchivo`, `cuerpoDeGrafico` y el
      cuerpo de `cerrar`).

- [ ] **T9**: La tarjeta del parte: **nada que tocar** si P3 es (a) —la
      plantilla itera `CAMPOS`—; si es (b), `:readonly` condicionado por una
      lista `CAMPOS_SOLO_LECTURA` en `pipeline.js` con su test. |
      Verificación: `tests/test_f007_estaticos.py` y `test_f012_front.py` en
      verde; con (b), un test JS de que `esSoloLectura` responde a los cinco y
      solo a ellos.

## Bloque 5 · Infra y documentación

- [ ] **T10**: `infra/18_vista_partes_sigrid.ps1` (`design.md` D-K): psycopg
      desde el `.venv`, contraseña por `SecureString`, **solo `SELECT`** sobre
      `information_schema.columns` y `postventa.v_partes_sigrid`; empaqueta
      Q2–Q5 de §14; compara las columnas con la lista del contrato; parámetro
      `-HashParte` para Q5, que **no selecciona texto del parte**; veredicto
      `PASA`/`NO PASA`. | Verificación: `test_f024_scripts_infra.py`, al modo de
      `test_f012_scripts_infra.py`: existe, cabecera con ruta, solo `SELECT`,
      solo el esquema propio e `information_schema`, sin `psql`, sin valores
      (host, usuario, contraseña), y la consulta de la fila de muestra no
      nombra `oficio`, `empresa`, `estancia`, `descripcion`, `promocion`,
      `unidad` ni `observaciones` como columna seleccionada.

- [ ] **T11**: `docs/ARCHITECTURE.md` (paso 3 y fila de PostgreSQL) y
      `docs/INTEGRACION.md` (§2 con las nueve tablas y la vista; §7; §8
      subsección «Lo que exponemos al datamart» con el contrato, la tabla de
      `NULL` y la petición de `design.md` §12; §9; cabecera con fecha y
      feature). | Verificación: `test_f024_documentacion.py` (R33, R34):
      `INTEGRACION.md` contiene `postventa.v_partes_sigrid`, «una fila por
      parte», «sin `dni_cliente`», `tiene_observaciones`, «solo se añaden
      columnas al final», `datamart-seg-anual`, «rol de solo lectura» y «fuera
      de nuestro alcance»; su árbol de §2 nombra `usuarios_sigrid`, `graficos`
      y `v_partes_sigrid`; `ARCHITECTURE.md` nombra `oficio`, `empresa`,
      `estancia`, `hora_inicio`, `hora_fin` en el paso 3 y `v_partes_sigrid`
      en la tabla; ningún host ni valor de secreto (reutilizar los patrones de
      `test_f012_documentacion.py`). `test_f005_integracion_sin_secretos.py`,
      `test_f009_documentacion.py`, `test_f012_documentacion.py`,
      `test_f019_documentacion.py` en verde.

- [ ] **T12**: `tests/test_f005_repo_sin_datos_personales.py::DIRECTORIOS_BARRIDOS`
      gana `specs/F-024-datos-parte-sigrid` (R32). | Verificación: ese test en
      verde sobre los tres ficheros de la spec y sobre el nuevo `.sql`, `.ps1`
      y tests.

## Bloque 6 · Verificación `MANUAL (humano)` — pequeña, y toda de solo lectura

- [ ] **T13**: Campaña de mutación (`python -m harness.mutacion --feature
      F-024`, con los 8 workers de `harness/rigor.json`, **anotando el nº de
      workers**) y análisis de cada superviviente. | Verificación: rigor
      `estandar` → informe en `progress/mutacion_F-024.md` sin ningún
      `PENDIENTE`; los supervivientes se documentan y los juzga el reviewer (no
      se exige cero). Alcance esperado: pocas líneas de `.py` (la tupla, un
      campo, una línea de `paso_cierre`, dos de `sentencias.py`); si la
      herramienta declara la puerta N/A por alcance, se anota el motivo que
      imprime.

- [ ] **T14 · M1**: Barrido de extracción con el prompt v2 sobre los partes
      reales de `muestras/` (los 22 de Mirasierra, si están en el puesto), con
      la credencial de IA del `.env` local, como T18 de F-003. | Verificación:
      **MANUAL (humano)**. Comando: desde `services/postventa-api`, el mismo
      guion que usó T18 de F-003 (o `func start` + `POST /api/extraer` parte a
      parte). Se anota en `progress/current.md`, **sin copiar ningún valor**:
      en cuántos partes salen `oficio`, `empresa` y `estancia` (esperado:
      22/22 con confianza alta **[MEDIDO en el papel: impresos siempre]**),
      cuántos traen `hora_inicio`/`hora_fin` (esperado: 0/22
      **[MEDIDO: vacías en toda la remesa]**) y, para los nueve de siempre,
      que los aciertos de código de obra, nº de incidencia, DNI y observaciones
      **no bajan** respecto al resultado anotado de T18 de F-003. Si baja
      alguno, **es una parada**: se revisa la redacción y se repite antes de
      T15.

- [ ] **T15 · M2**: Tras desplegar el backend (`infra/desplegar_backend.ps1`,
      lo hace el humano; el DDL se aplica solo al arrancar), comprobar la vista
      en la base desplegada y un parte nuevo que traiga los campos. |
      Verificación: **MANUAL (humano)**. (1) Antes del despliegue, Q1 de
      `design.md` §14 (cuántos partes quedan con `prompt_version = "1"`), y se
      anota el número. (2) `powershell -ExecutionPolicy Bypass -File
      infra\18_vista_partes_sigrid.ps1` → `PASA`: las columnas de Q2 son las
      del contrato en su orden, Q3 da `partes == filas_vista`, Q4 devuelve las
      once columnas nuevas con sus tipos, y `dni_cliente` no está entre las
      columnas de la vista. (3) Subir por el front **un** parte (el de la obra
      de prueba 404 si sigue disponible del bloque 9 de F-012, o uno de
      Mirasierra), guardarlo (`POST /api/parte`) y lanzar el script con
      `-HashParte <hash>`: Q5 devuelve `prompt_version = "2"`, `trae_oficio`,
      `trae_empresa` y `trae_estancia` a `true`, `trae_hora_inicio` a `false`,
      y los estados de archivo/gráfico/cierre coherentes con lo que se hizo.
      (4) Si además se ejecuta un dry-run de cierre sobre ese parte (solo si la
      ventana está abierta por otro motivo; **no se abre para esto**),
      `reclamacion_ide` en Q5 deja de ser `NULL`. Resultado anotado en
      `progress/current.md`, con los números y sin ningún dato del parte.

- [ ] **T16 · M3**: Refrescar `azure-apps/postventa_incidencias.md` como copia
      de `docs/INTEGRACION.md` (R35), y con ello la petición al datamart
      (`design.md` §12). | Verificación: **MANUAL (humano)** — es **otro
      repositorio**: commit local allí, sin push. **No se toca
      `azure-apps/datamart_seg_anual.md`**.

## Bloque 7 · Cierre

- [ ] **T17**: Ejecutar `bash harness/init.sh` en verde. | Verificación:
      `bash harness/init.sh` termina con exit code 0, tests incluidos —los de
      `api` y los de `front`, con el puente a `node --test`— y con la puerta
      de cobertura de las líneas cambiadas en `[OK]` (≥ 80 %).
