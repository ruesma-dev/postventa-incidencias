<!-- specs/F-033-l1-traza-archivo/tasks.md -->
# F-033 · La primera capa contra el duplicado en SharePoint, conectada — Tareas

> Una tarea = un commit `F-033 Tn: ...`. Ordenadas por dependencia; los tests
> van **antes o junto** a la implementación (**fase RED obligatoria**, rigor
> `critico`, cero supervivientes de mutación).
>
> Rama: `feature/F-033-l1-traza-archivo`, creada desde `dev` (`11dda9d`).
>
> **Los encargos al implementer se dan por bloques**, y el implementer **para**
> al terminar cada bloque.
>
> **Antes de empezar, el humano tiene que haber respondido D-1…D-7**
> (`requirements.md` §8, `design.md` §10). Las tareas están escritas con las
> recomendaciones; si alguna decisión cambia, se enmienda la spec **antes** de
> implementar. Si al implementar aparece una duda que no resuelvan la spec,
> `docs/ARCHITECTURE.md` o `docs/CONVENTIONS.md`, se **para** y se marca
> `blocked`; no se improvisa.

## Reglas duras de esta feature

1. **Sin DDL**: ni un fichero nuevo ni una línea cambiada en
   `infrastructure/persistencia/sql/`. Ni un `UPDATE` sobre filas existentes.
2. **Ni un aserto existente cambia de expectativa.** Cambian de **forma** los
   que fijan la sentencia de la situación (número de `JOIN`, tupla de columnas,
   filas de diez) y los atajos que pasaban `traza_previa`; la lista cerrada
   está en `design.md` §7. Los asertos de **dos sentencias** por
   `consultar_situacion` **no se tocan**. Cualquier otro cambio de expectativa:
   **parar**.
3. **No se tocan** `paso_grafico.py`, `paso_cierre.py`, `adjuntar.py`,
   `cerrar.py` (eso es D-6), `domain/models/nombrado.py` (F-031),
   `infrastructure/sharepoint/**`, `puerta_de_estado.py`, el front ni
   `azure-apps/`.
4. **Ninguna escritura contra SharePoint, Sigrid ni PostgreSQL desde local**,
   ni en tests ni a mano. Contra la base `postventa`, **solo lecturas** y solo
   las de T13, que ejecuta el humano.
5. **Ni un dato personal en los tests** ni un identificador real de biblioteca:
   `drive_id` inventados y reconocibles (`drive-inventado-it`,
   `drive-inventado-posventa`).
6. **Nada de `git push` ni de PRs.** Commits locales, en español.

---

## Bloque 1 · La traza en la situación (persistencia)

- [x] **T1**: RED. Crear `tests/test_f033_situacion_con_archivo.py` con los
      tests de R1–R6 y R17 (`design.md` §6, primera fila). Ejecutarlos y pegar
      la **salida real del fallo** en `progress/impl_F-033.md`. |
      Verificación: `python -m pytest services/postventa-api/tests/test_f033_situacion_con_archivo.py -q`
      falla por `SituacionParte` sin `archivo`, sentencia sin tercer `JOIN` y
      `upsert_archivo` sin `WHERE`; traza pegada en el informe.

- [x] **T2**: `SituacionParte.archivo` (R1), con la enmienda fechada del
      docstring («cuatro cosas» → cinco, citando la frase vieja), y los
      docstrings del puerto (`consultar_situacion`, `guardar_archivo`). |
      Verificación: los tests de R1 de T1 en verde; `python -m pytest services/postventa-api/tests -q -k "f028 or f030"` en verde.

- [x] **T3**: `sentencias.py`: `_COLUMNAS_ARCHIVO`, `upsert_archivo` con
      `WHERE … estado <> %s` y `_ESTADO_ARCHIVO_TERMINAL` como parámetro (R17),
      y el tercer `LEFT JOIN` con las ocho columnas al final en
      `select_veredicto_y_cierre` (R2, R3), con enmienda fechada en su
      docstring. En el mismo commit, **solo los cambios de forma** de
      `design.md` §7 en `test_f005_sentencias.py`. | Verificación: tests de R2,
      R3 (forma) y R17 (sentencia) de T1 en verde;
      `python -m pytest services/postventa-api/tests/test_f005_sentencias.py -q` en verde.

- [x] **T4**: `mapeo.py`: `fila_a_traza_archivo` y `fila_a_situacion_guardada`
      con el corte con nombre (R4, R5; `design.md` §3.3). `repositorio_pg.py`:
      `consultar_situacion` rellena `archivo` y registra su estado (R6). En el
      mismo commit, las filas de diez → dieciocho en
      `test_f028_persistencia.py`, `test_f030_veredicto_persistido.py` y
      `tests/utiles_pg.py::RepositorioComoLaBase` (que además pasa a la
      semántica terminal de R17 en `guardar_archivo`). | Verificación: todo
      `test_f033_situacion_con_archivo.py` en verde, incluido R3 contado
      (`len(conexion.ejecutadas) == 2`); `python -m pytest services/postventa-api/tests -q -k "f005 or f028 or f030"` en verde.

**Parada del bloque 1.** Informe en `progress/impl_F-033.md` y respuesta de una
línea.

## Bloque 2 · L1 en el paso y en el endpoint

- [x] **T5**: RED. Crear `tests/test_f033_l1_desde_el_almacen.py` (R7–R11,
      R13–R16, R18–R21) y `tests/test_f033_archivar_http.py` (R12, R14, R23 y
      los tres recorridos de circuito de `design.md` §6). Pegar la salida real
      del fallo. En particular, **el circuito de doble archivado con
      `RepositorioComoLaBase` tiene que fallar hoy por haber subido dos
      veces**: es la prueba de que el defecto D-A1 existe y de que el test lo
      caza. | Verificación: `python -m pytest services/postventa-api/tests/test_f033_l1_desde_el_almacen.py services/postventa-api/tests/test_f033_archivar_http.py -q`
      en rojo; traza en el informe.

- [x] **T6**: `RepositorioFalso` (`tests/utiles_sharepoint.py`) con resultados
      programables de `guardar_archivo` (R18); los atajos `archivar(...)` de
      `test_f006_paso_archivo.py` y `_archivar(...)` de
      `test_f019_orden_archivado.py` siembran `traza_previa` en
      `repositorio.situacion` en vez de pasarla (`design.md` §7). **Sin tocar
      ningún cuerpo de test ni ningún aserto.** | Verificación: `git diff` de
      esos dos ficheros limitado a los atajos; los dos ficheros siguen en
      verde **con el paso todavía sin cambiar** (el atajo pasa la traza por
      los dos caminos durante esta tarea, y el siguiente commit quita uno).

- [x] **T7**: `paso_archivo.py`: fuera `traza_previa`, dentro
      `drive_id_vigente`; L1 desde `situacion_leida(ctx, repositorio).archivo`;
      `_en_otro_destino`; los dos avisos nuevos; R18, R19 y R20 (`design.md`
      §4). Docstring del módulo y de la función actualizados (la tabla de las
      tres capas dice ya de dónde sale L1). Quitar del atajo de T6 el camino
      viejo. | Verificación: `test_f033_l1_desde_el_almacen.py` en verde;
      `python -m pytest services/postventa-api/tests -q -k "f006 or f019"` en verde.

- [x] **T8**: `archivar.py` pasa `drive_id_vigente=ajustes.sharepoint_drive_id`
      (R15). Docstring: una línea que diga que L1 sale de la situación que lee
      la puerta. | Verificación: `test_f033_archivar_http.py` en verde,
      incluidos los tres recorridos de circuito.

**Parada del bloque 2.**

## Bloque 3 · Documentación y cierre

- [x] **T9**: `docs/ARCHITECTURE.md`, paso 6, bajo «tres capas»: precisión
      fechada **F-033, 2026-09-xx** (R25): L1 lee la traza de la situación, en
      la misma consulta; `archivado` no se pisa; una traza en otro destino
      corta y avisa; el re-archivo del mismo parte no existe desde el
      circuito. **Sin borrar** nada. | Verificación: `git diff docs/ARCHITECTURE.md`
      solo añade líneas.

- [x] **T10**: Control de alcance en `tests/test_f033_l1_desde_el_almacen.py`
      (o fichero propio si crece): ni un fichero cambiado bajo
      `infrastructure/persistencia/sql/`, ni en `services/postventa-front/`,
      ni en los cuatro ficheros de D-6, ni en `nombrado.py`; con las **dos
      mitades** que usó F-032 (diff contra `dev` y comprobación que no depende
      de `git`) y sus tres guardas para no dejar `dev` en rojo al mergear. |
      Verificación: el test en verde en la rama.

- [x] **T11**: Campaña de mutación. | Verificación:
      `python -m harness.mutacion --feature F-033` con **cero supervivientes**
      (cada uno, si lo hubiera, con test nuevo o justificación escrita para el
      humano); informe en `progress/mutacion_F-033.md` con el nº de workers.

- [x] **T12**: Ejecutar `bash harness/init.sh` en verde. | Verificación: el
      comando termina en verde, con la puerta de cobertura de las líneas
      cambiadas en `[OK]` por encima del umbral de `critico`; números en la
      sección «Evidencias» de `progress/impl_F-033.md`.

---

## Verificación manual pendiente del humano (fuera de la rama)

- [x] **T13 · MANUAL (humano) · antes de desplegar** (R26). **EJECUTADA el
      2026-09-18** con `infra/25_mediciones_despliegue.ps1`: 133 trazas, las 133
      `archivado` y con biblioteca, **0 `pendiente`**. R26 cumplido. Resultado en
      `progress/current.md` y en `progress/cierre_verificaciones_F-033.md`. Solo lectura,
      dentro del schema `postventa`, con las credenciales que el humano tiene
      y ningún agente:

      ```sql
      SET search_path TO postventa;

      -- 1. Cuántas trazas hay en cada estado, y cuántas con biblioteca.
      SELECT estado, count(*) AS trazas, count(drive_id) AS con_biblioteca
      FROM postventa.archivos
      GROUP BY estado
      ORDER BY estado;

      -- 2. Las que se quedaron en 'pendiente': posibles ficheros subidos
      --    sin traza final (ArchivoSinTraza). Sin drive_id ni web_url.
      SELECT hash_parte, carpeta, nombre_fichero, intentos
      FROM postventa.archivos
      WHERE estado = 'pendiente'
      ORDER BY hash_parte;
      ```

      Anotar el resultado en `progress/` **sin identificadores de biblioteca**.
      Lo esperable es cero filas en la segunda. Si hay alguna, una persona
      mira esa carpeta en SharePoint antes de desplegar: desde F-033 el
      siguiente archivado de ese parte avisará (R20), pero la traza se pisará.

- [x] **T14 · MANUAL (humano) · después de desplegar** (R27). **NO RECORRIDA
      COMO ESTÁ ESCRITA.** El 2026-09-22 el responsable dio la feature por
      cerrada porque **Posventa la está probando en real**; no hay foto
      antes/después de un re-archivado ni constancia de `AVISO_YA_ARCHIVADO`
      observado. Qué la respalda y qué no, en
      `progress/cierre_verificaciones_F-033.md`. Con
      **autorización expresa** para un parte concreto que ya conste
      `archivado`, y la ventana `ARCHIVO_HABILITADO` abierta solo para ello:

      1. Anotar de ese parte, con la consulta de solo lectura
         `SELECT estado, intentos, archivado_at_utc FROM postventa.archivos WHERE hash_parte = '<hash>';`,
         los tres valores.
      2. Volver a archivarlo desde el front (o `POST /api/archivar` con el
         mismo cuerpo).
      3. Comprobar: la respuesta trae `AVISO_YA_ARCHIVADO`; en SharePoint el
         fichero conserva su fecha de modificación y no hay otro; y la misma
         consulta del paso 1 devuelve **los mismos tres valores** (con
         `intentos` igual: no hubo ninguna escritura).
      4. Cerrar la ventana.

      Resultado real anotado en `progress/`.
