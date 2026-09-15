<!-- specs/F-024-datos-parte-sigrid/requirements.md -->
# F-024 · Datos del parte enlazados a Sigrid, para el datamart — Requisitos

> Notación EARS (`specs/SPECS.md`). Cada requisito se traduce a **al menos un
> test trazable** `test_f024_rN_*`. Rigor **`estandar`**: fase RED en los
> requisitos centrales, cobertura ≥ 80 % de las líneas cambiadas, campaña de
> mutación con los supervivientes documentados (lo que exige
> `harness/rigor.json` para este nivel; ver P4 de `design.md` §13), y tests
> **sin red, sin BBDD y sin IA**.
>
> Contrato de partida: la entrada `F-024` de `harness/features.json`, aprobada
> por el humano el 2026-09-06, con sus tres piezas, su pregunta abierta y lo
> que deja fuera. Estos requisitos la desarrollan; no la amplían.

## Por qué existe

En palabras del humano: *«Los datos que hoy se pierden se pueden guardar en
nuestra base como información adicional, siempre relacionándola con la de
Sigrid, de forma que al reconstruir podamos recabar esa información; por
ejemplo cuando el datamart incluya los partes de postventa, se pueden
enriquecer con esta información adicional.»*

El cierre en Sigrid registra **solo el gráfico y el estado**
(`docs/referencia/01_cierre_incidencia_sigrid.md`, revisado el 2026-09-06
contra el correo original de Posventa). Todo lo demás del parte —quién reparó,
en qué estancia, a qué hora, con qué firma, qué decidió la revisión— quedaría
únicamente dentro del PDF. Esta feature lo conserva en el schema propio,
**enlazado con las claves del ERP**, y lo expone en una vista de lectura.

## Alcance

Tres piezas, y solo esas:

1. **Extracción**: cinco campos nuevos —`oficio`, `empresa`, `estancia`
   (impresos) y `hora_inicio`, `hora_fin` (manuscritos)—, con su confianza,
   **sin exigirlos**, y sus columnas en `postventa.partes`.
2. **Claves del ERP**: `reclamacion_ide` (`con.ide`) también en
   `postventa.cierres`; `postventa.graficos` ya nació con ella (F-012).
3. **La vista** `postventa.v_partes_sigrid`: una fila por parte con las claves
   de Sigrid, los campos extraídos y sus confianzas, la firma, el veredicto y
   los estados de archivo, gráfico y cierre. **Sin `dni_cliente`.**

**Fuera de alcance, por decisión del humano del 2026-09-06**: el acceso desde
el datamart (rol de solo lectura, `GRANT`, la conexión de su ETL). Se deja
escrita la **petición** al proyecto `datamart-seg-anual` (`design.md` §12) y la
vista se documenta como **contrato** en `docs/INTEGRACION.md` §8 y en
`azure-apps/postventa_incidencias.md`. Tampoco entran: reextraer los partes ya
guardados, interpretar las observaciones (F-016), reagrupar páginas (F-014) ni
un endpoint HTTP nuevo.

## Vocabulario

| Término | Qué es |
|---|---|
| **Campos del parte** | `CAMPOS_DEL_PARTE` de `domain/models/extraccion.py`: hoy nueve; con esta feature, **catorce**. Es la fuente única del schema que rellena el modelo, de las columnas de `partes` y del cuerpo de `/api/validar` y `/api/parte`. |
| **Campo impreso / manuscrito** | Lo que imprime Sigrid en el parte frente a lo que escribe a mano quien estuvo allí (`docs/referencia/02_parte_de_trabajo.md`). |
| **`reclamacion_ide`** | El `con.ide` de la reclamación en Sigrid: la clave estable del ERP. `numero_incidencia` (`con.cod`, `RS26.08/0123`) es legible y única dentro del tipo 708 **[MEDIDO, `03_modelo_posventa_sigrid.md` §1.1]**, pero no es la clave. |
| **La vista** | `postventa.v_partes_sigrid`, `CREATE OR REPLACE VIEW` en el schema propio. Contrato de lectura: sus columnas y su orden son estables. |
| **El datamart** | `datamart-seg-anual`, base `sigrid_dm` en el **mismo** Flexible Server `psql-albaranes-rs9k2`, otra base. Consumidor futuro de la vista. |
| **`tiene_observaciones`** | Booleano derivado: hay texto manuscrito en `observaciones`. Es lo que la vista expone **por defecto** en vez del texto (P1 de `design.md` §13). |

---

## 1 · Los cinco campos nuevos de la extracción

**R1.** El sistema debe declarar en `CAMPOS_DEL_PARTE` **catorce** campos: los
nueve de F-003, en su orden, seguidos de `oficio`, `empresa`, `estancia`,
`hora_inicio` y `hora_fin`, **en ese orden y al final**. `CAMPOS_MANUSCRITOS`
debe incluir además `hora_inicio` y `hora_fin`.

> Al final y no intercalados: los nueve primeros son el prefijo que fijan
> `test_f003_extraccion_dominio.py` y el orden de las columnas ya creadas en
> `03_partes.sql`. Un campo nuevo en medio desplazaría ese orden sin ganar
> nada.

**R2.** CUANDO el modelo devuelve alguno de los cinco campos nuevos, el sistema
debe dejarlo en `ExtraccionParte.campos` con su valor **literal** y su
`confianza_pct` saneada a `0–100`, **por el mismo camino** que los otros nueve
(sin ninguna rama de código propia).

**R3.** SI el modelo omite un campo nuevo, o lo devuelve vacío, ENTONCES el
sistema debe incluirlo con `valor = None` y `confianza_pct = 0` (con aviso si
faltó la clave), y **el veredicto de F-004 no debe cambiar**: un parte apto
sigue apto, uno de la cola sigue en la cola y uno de revisión manual sigue en
revisión manual. Los cinco campos **no deciden nada**.

> Es la regla de F-003 y la semántica 4 bis de `docs/ARCHITECTURE.md`: no se
> exige lo que la realidad deja en blanco. Las horas están vacías en toda la
> remesa de Mirasierra **[MEDIDO, `02_parte_de_trabajo.md`]**.

**R4.** El prompt `parte_posventa_es` de `config/prompts.yaml` debe describir
los cinco campos nuevos —con su etiqueta del papel y si son impresos o
manuscritos— sin ningún dato personal ni real de ejemplo, y debe subir su
`version` declarada a `"2"`.

**R5.** CUANDO cambia el texto del prompt, la huella clavada en
`test_f004_prompts_firma.py::HUELLA_DEL_PROMPT_MEDIDO` debe actualizarse **a
conciencia** con la huella nueva, citando F-024 y la verificación manual que
vuelve a medir la lectura (M1 de `tasks.md`). El prompt de la firma,
`firma_parte_es`, **no debe cambiar** ni una coma.

**R6.** El schema estructurado que viaja al modelo (`schema_para("parte_posventa")`)
debe llevar los catorce campos como `required`, **generado del dominio** y sin
ninguna lista escrita a mano en infraestructura.

**R7.** `POST /api/extraer` debe devolver los catorce campos con su valor y su
confianza; `POST /api/validar` y `POST /api/parte` deben exigir los catorce y
responder `400` nombrando los que falten (mismo mecanismo que hoy, por
construcción).

**R8.** `ContextoParte` **no debe ganar ningún campo**: los cinco nuevos viajan
dentro de `extraccion.campos`. El censo de campos del contexto que vigila
`test_f003_paso_extraccion.py::test_f003_r7_*` se conserva tal cual.

## 2 · Las columnas nuevas y la compatibilidad hacia atrás

**R9.** El sistema debe añadir a `postventa.partes` diez columnas —cinco
`text` anulables y sus cinco `<campo>_confianza_pct integer NOT NULL DEFAULT 0`—
mediante sentencias `ALTER TABLE postventa.partes ADD COLUMN IF NOT EXISTS`,
**una columna por sentencia**, en un fichero `NN_nombre.sql` nuevo que pasa la
guarda de `ddl.py` sin cambiarla.

**R10.** `columnas_de_campos()` debe devolver **veintiocho** columnas en el
orden del contrato, y `upsert_parte` debe escribirlas todas con un marcador
por columna y **sin lista escrita a mano** (se derivan de `CAMPOS_DEL_PARTE`).

**R11.** MIENTRAS existan partes guardados antes de esta feature, el sistema
debe conservarlos **sin reextraer**: sus columnas nuevas quedan `NULL` (valor)
y `0` (confianza), y su `prompt_version` sigue diciendo `"1"`, que es lo que
permite distinguir «no se pidió» de «se pidió y estaba en blanco». Reprocesar
la misma remesa actualiza esa fila por `hash_parte` y la rellena, sin duplicar.

**R12.** El sistema debe añadir a `postventa.cierres` la columna
`reclamacion_ide integer` (anulable) con `ALTER TABLE ... ADD COLUMN IF NOT
EXISTS`, en su propio fichero `NN_nombre.sql`, sin tocar `06_cierres.sql`.

**R13.** CUANDO `paso_cierre` deja una traza que nace de un plan —`dry_run_ok`,
`cerrado`, `error` tras el dry-run o `ya_cerrada`—, el sistema debe rellenar
`TrazaCierre.reclamacion_ide` con `plan.reclamacion.ide`, y `upsert_cierre`
debe escribirlo. La regla de R25 de F-005 se mantiene: una fila en `cerrado`
**no se pisa**.

**R14.** El DDL completo debe seguir siendo **idempotente y del schema propio**:
cada sentencia lleva `IF NOT EXISTS` u `OR REPLACE`, todas van cualificadas con
`postventa.`, ninguna nombra `public.`, ninguna declara un tipo binario y
ninguna usa `GRANT`, `CREATE ROLE` ni ningún verbo de la lista negra.

## 3 · La vista `postventa.v_partes_sigrid`

**R15.** El sistema debe crear la vista con `CREATE OR REPLACE VIEW
postventa.v_partes_sigrid`, en su propio fichero `NN_nombre.sql` numerado
**después** de todas las tablas y de los `ALTER` de esta feature.

**R16.** La vista debe devolver **exactamente una fila por fila de
`postventa.partes`**: parte de `partes` y une `validaciones`, `archivos`,
`graficos` y `cierres` por `hash_parte` con **`LEFT JOIN`** y sin `WHERE`. Las
cuatro tablas tienen `hash_parte` como clave primaria, así que ningún `JOIN`
multiplica filas.

**R17.** La vista debe exponer las claves de Sigrid: `codigo_obra` (leído del
papel; es el `con.cod` de la obra), `numero_incidencia` (leído del papel, con
barra), `numero_incidencia_sigrid` (el `con.cod` **confirmado por el ERP** en
el dry-run, de `cierres` o `graficos`; `NULL` si nunca hubo dry-run),
`reclamacion_ide` (`COALESCE` de `graficos` y `cierres`), `gra_cod`,
`gra_ide_negocio` y `rcg_ide`.

**R18.** La vista debe exponer los **doce** campos extraídos que no son
personales directos —los catorce menos `dni_cliente` y `observaciones`—, cada
uno con su `<campo>_confianza_pct`, con los mismos nombres que en `partes`.

**R19.** La vista debe exponer `tiene_observaciones` (booleano: hay texto
manuscrito, no solo espacios) y `observaciones_confianza_pct`, y **no** el
texto de `observaciones`, salvo que el humano elija la opción (b) de P1 al
aprobar (`design.md` §13), en cuyo caso `observaciones` se añade **como última
columna**.

**R20.** La vista **no debe contener** `dni_cliente` ni
`dni_cliente_confianza_pct` —ni una columna derivada de ellos—, ni ningún
`oid` de empleado (`remesas.usuario_oid`, `cierres.confirmado_por`,
`graficos.confirmado_por`), ni las columnas `motivo` de texto libre de
`archivos`, `cierres` y `graficos`, ni ninguna columna binaria.

**R21.** La vista debe exponer, de la validación: `veredicto`, `destino`,
`clasificacion_firma` y `validado_at_utc`.

**R22.** La vista debe exponer, del archivo: `archivo_estado`,
`archivo_nombre_fichero`, `archivo_carpeta`, `archivo_web_url` y
`archivado_at_utc`.

**R23.** La vista debe exponer, del gráfico: `grafico_estado`,
`grafico_sha256`, `grafico_bytes`, `grafico_idempotente` y `adjuntado_at_utc`.

**R24.** La vista debe exponer, del cierre: `cierre_estado`,
`cierre_estado_origen_sigrid`, `cierre_estado_destino_sigrid`,
`cierre_dry_run_at_utc` y `cerrado_at_utc`.

**R25.** La vista debe exponer, de la traza del parte: `remesa_id`,
`modo_deteccion`, `primera_vez_at_utc`, `actualizado_at_utc`, `reprocesos`,
`ia_modelo`, `prompt_version` y `prompt_huella`.

**R26.** CUANDO un parte no tiene validación, archivo, gráfico o cierre, la
vista debe devolverlo igualmente, con las columnas de ese bloque a `NULL`. El
significado de cada `NULL` está en `design.md` §8.3 y en `INTEGRACION.md` §8.

**R27.** La lista de columnas de la vista, **en su orden**, es un contrato: el
test la fija escrita a mano, y cualquier cambio futuro solo puede **añadir
columnas al final** (`CREATE OR REPLACE VIEW` en PostgreSQL rechaza quitar,
renombrar o reordenar columnas de una vista existente).

**R28.** La guarda de `ddl.py` debe aceptar los ficheros nuevos **tal y como
están** (sin modificar la guarda), y `ficheros_ddl` debe recogerlos en orden:
`10_*` < `11_*` < `12_*`, todos detrás de `09_graficos.sql`.

## 4 · El front

**R29.** La tarjeta del parte del front debe mostrar los catorce campos con su
confianza: `js/pipeline.js::CAMPOS_DEL_PARTE` pasa a catorce, en el orden del
dominio, y `cuerpoDeValidacion` / `cuerpoDeParte` llevan las catorce claves.

**R30.** Los cuerpos de `/api/archivar`, `/api/adjuntar` y `/api/cerrar` **no
deben ganar ningún campo**: nada de lo nuevo viaja a SharePoint ni al ERP.

## 5 · Datos personales y logs

**R31.** Ningún log nuevo debe registrar el valor de un campo del parte: los
cinco campos nuevos pasan por `repositorio_pg.py` y `mapeo.py` como los demás,
que no registran valores, y el control negativo de
`test_f005_logs_sin_datos_personales.py` sigue en verde.

**R32.** Ningún fichero de esta feature —spec, `.sql`, tests, prompt— debe
llevar un DNI, un nombre de cliente ni un dato real de un parte: los ejemplos
son inventados y `test_f005_repo_sin_datos_personales.py` barre también
`specs/F-024-datos-parte-sigrid`.

## 6 · Documentación que la feature deja al día

**R33.** `docs/INTEGRACION.md` debe declarar la vista como **contrato de
lectura** en §8: nombre, grano, claves de Sigrid, lista de columnas con su
significado, qué **no** lleva (DNI, observaciones, `oid`), la regla de
compatibilidad (solo se añade al final) y la **petición** al proyecto
`datamart-seg-anual` con lo que queda fuera de nuestro alcance (rol de solo
lectura, `GRANT`, conexión de su ETL). §2 debe listar las nueve tablas y la
vista; §7 debe decir que la vista no expone el DNI ni el texto manuscrito.
**Nunca** un valor de conexión.

**R34.** `docs/ARCHITECTURE.md` debe nombrar los cinco campos nuevos en el paso
3 del pipeline —como campos que **no deciden**— y mencionar la vista en la fila
de PostgreSQL de la tabla de sistemas externos.

**R35.** `azure-apps/postventa_incidencias.md` debe refrescarse como copia de
`INTEGRACION.md` en el mismo trabajo (otro repositorio: commit local, sin
push).

---

## Trazabilidad de los requisitos que no llevan test unitario

| Requisito | Por qué no hay test unitario | Cómo se verifica |
|---|---|---|
| R5 (segunda mitad: la calidad de lectura con el prompt v2) | El modelo está simulado en la suite; ningún test detecta que una redacción lea peor | **M1**, `MANUAL (humano)`: barrido sobre los partes reales de `muestras/`, como T18 de F-003 |
| R11 (los partes ya guardados en la base desplegada) | Exige la base real; la suite no abre conexiones | **M2**, `MANUAL (humano)`: consulta preparada de solo lectura, `design.md` §14 |
| R16, R26 (que la vista devuelva una fila por parte con `NULL` donde toca, **sobre PostgreSQL de verdad**) | El texto SQL se comprueba en la suite; que PostgreSQL lo acepte y lo ejecute así, no | **M2**, `MANUAL (humano)`: `infra/18_vista_partes_sigrid.ps1` contra la base desplegada, solo lectura; y opcionalmente la suite `tests_bbdd/` contra base efímera |
| R35 | Es otro repositorio | **M3**, `MANUAL (humano)` |

Todo lo demás tiene test unitario **sin red, sin BBDD y sin IA**, sobre el
texto real de los `.sql`, los dobles de `tests/utiles_*.py` y el doble de
conexión de `tests/utiles_pg.py`.
