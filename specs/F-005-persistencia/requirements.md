<!-- specs/F-005-persistencia/requirements.md -->
# F-005 · Persistencia en el PostgreSQL compartido — Requisitos (EARS)

> Contrato: `description` y `acceptance` de `harness/features.json`.
> Normativo por encima de esta spec: `docs/ARCHITECTURE.md`,
> `docs/CONVENTIONS.md`, `CHECKPOINTS.md` y las reglas duras de `CLAUDE.md`.
>
> **Ni un dato real.** Todos los ejemplos de esta spec están inventados y
> marcados como tales. Los partes llevan DNI y observaciones manuscritas de
> clientes: eso se guarda en base de datos, nunca en el repositorio.

## Trazabilidad con `acceptance`

| Criterio `acceptance` | Requisitos |
|---|---|
| El DDL es idempotente: dos arranques seguidos no fallan ni duplican | R3, R4, R10 |
| Todo el DDL vive en el schema propio; ni una sentencia a nivel de servidor | R1, R5, R6, R7, R8, R11 |
| Reprocesar la misma remesa actualiza, no duplica (clave por hash del parte) | R13–R17 |
| Tests contra base efímera, nunca contra el servidor compartido | R32, R33, R34, R35, R36 |
| `bash harness/init.sh` en verde | R30, R31 y toda la suite |

Fuera de los cinco criterios, y por la decisión **D2** del humano del
2026-08-19 (se persiste el DNI): las salvaguardas del dato personal son
**R12, R21, R27, R29 y R37–R40**, desarrolladas en `design.md` §6.

---

## 1 · El esquema y su DDL

**R1.** El sistema debe mantener todo su DDL en ficheros `NN_nombre.sql`
dentro de `services/postventa-api/infrastructure/persistencia/sql/`, y
aplicarlos en orden lexicográfico ascendente de nombre de fichero.

**R2.** CUANDO el servicio necesita la base de datos por primera vez en un
proceso, el sistema debe aplicar el DDL completo una sola vez y reutilizar esa
garantía durante el resto de la vida del proceso.

**R3.** El sistema debe declarar cada sentencia del DDL de forma idempotente
(`CREATE ... IF NOT EXISTS`, `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`,
`CREATE INDEX IF NOT EXISTS`, `CREATE OR REPLACE VIEW`).

**R4.** CUANDO el DDL se aplica dos veces seguidas sobre la misma base, el
sistema debe terminar sin error las dos veces y dejar exactamente el mismo
conjunto de tablas, columnas, índices y restricciones.

**R5.** SI alguna sentencia del DDL no está cualificada con el esquema
configurado, ENTONCES el sistema debe fallar antes de abrir ninguna conexión,
con un error que nombre el fichero y la sentencia culpable.

**R6.** SI el DDL contiene una sentencia de ámbito de servidor o de base de
datos —`CREATE DATABASE`, `CREATE ROLE`, `CREATE USER`, `CREATE EXTENSION`,
`CREATE TABLESPACE`, `ALTER SYSTEM`, `ALTER DATABASE`, `ALTER ROLE`, `GRANT`,
`REVOKE`, `DROP DATABASE`, `DROP SCHEMA`, `DROP ROLE`, `CREATE PUBLICATION`,
`CREATE SUBSCRIPTION`— ENTONCES el sistema debe fallar antes de abrir ninguna
conexión, nombrando la sentencia.

**R7.** El sistema no debe crear nunca la base de datos ni el rol de acceso:
ambos son tarea de infraestructura, ejecutada una sola vez por el humano.

**R8.** CUANDO abre una conexión, el sistema debe fijar el `search_path` de la
sesión únicamente a su propio esquema, sin `public`.

**R9.** CUANDO abre una conexión, el sistema debe fijar de sesión
`application_name`, `statement_timeout`, `lock_timeout` e
`idle_in_transaction_session_timeout`, con los valores que declara la
configuración.

**R10.** MIENTRAS dos o más procesos arrancan a la vez contra la misma base,
el sistema debe serializar la aplicación del DDL con un bloqueo consultivo de
sesión (`pg_advisory_lock`), y liberarlo pase lo que pase.

**R11.** SI el entorno es `local` y el host configurado no es un host local
(`localhost`, `127.0.0.1`, `::1`), ENTONCES el sistema debe negarse a aplicar
el DDL y decir por qué, sin abrir la conexión.

**R12.** El sistema no debe declarar en su DDL ninguna columna binaria
(`bytea`, large objects): los PDF viven en SharePoint y el almacenamiento de
este servidor es compartido y solo crece.

---

## 2 · Reprocesar actualiza, no duplica

**R13.** El sistema debe identificar cada parte por su `hash_parte`, el que
produce F-002, y usarlo como clave primaria de la fila del parte.

**R14.** CUANDO se guarda un parte cuyo `hash_parte` ya existe, el sistema
debe actualizar la fila existente y no crear ninguna nueva.

**R15.** CUANDO actualiza un parte que ya existía, el sistema debe conservar
intacta su fecha de primera vez, refrescar su fecha de actualización e
incrementar en uno su contador de reprocesos.

**R16.** CUANDO la misma remesa se procesa dos veces seguidas, el sistema debe
dejar en la tabla de partes el mismo número de filas que tras la primera vez.

**R17.** CUANDO se guarda la validación de un parte que ya tenía una, el
sistema debe sustituirla, nunca acumular una segunda fila para ese parte.

---

## 3 · Qué se guarda

**R18.** CUANDO se guarda un parte, el sistema debe persistir los nueve campos
de `CAMPOS_DEL_PARTE` (F-003), cada uno con su valor literal y su
`confianza_pct`.

**R19.** CUANDO se guarda un parte, el sistema debe persistir su traza de
extracción: proveedor, modelo, clave del prompt, versión y huella.

**R20.** CUANDO se guarda una validación, el sistema debe persistir veredicto,
destino, clasificación de la firma y la lista completa de motivos, en el orden
en que los emitió F-004.

**R21.** El sistema no debe duplicar la transcripción de las observaciones
manuscritas: vive en la fila del parte y solo ahí.

**R22.** CUANDO se pide la cola de validación humana, el sistema debe devolver
únicamente los partes cuyo destino es `cola_validacion_humana`, cada uno con
su transcripción de observaciones y la confianza de esa transcripción.

**R23.** CUANDO se registra el archivo de un parte, el sistema debe dejar una
única fila por `hash_parte`, con su estado y —si la subida salió bien— sus
identificadores de SharePoint.

**R24.** CUANDO se registra un cierre correcto, el sistema debe dejar el parte
marcado como cerrado, con el estado de Sigrid de origen y de destino tal y
como se resolvieron en ejecución.

**R25.** SI se intenta registrar un cierre sobre un parte ya marcado como
cerrado, ENTONCES el sistema debe dejar la fila intacta y devolver que no
había nada que hacer.

**R26.** CUANDO un cierre falla, el sistema debe dejar el parte marcado con el
motivo del fallo y el número de intentos acumulados.

**R27.** CUANDO se guarda la preferencia de auto-cierre de un usuario, el
sistema debe dejar una única fila por usuario, identificado por el `oid`
opaco de Entra ID y nunca por su correo ni por su nombre.

**R28.** CUANDO un usuario revoca su auto-cierre, el sistema debe dejar la
preferencia en falso y anotar el instante de la revocación.

**R29.** El sistema no debe escribir en el log el DNI, las observaciones ni el
valor de ningún campo manuscrito; de un campo manuscrito solo puede registrar
si venía vacío y su confianza.

---

## 4 · Arquitectura

**R30.** El dominio y la aplicación no deben importar el driver de PostgreSQL
ni ningún módulo de `infrastructure`.

**R31.** El acceso a la persistencia debe pasar por puertos declarados en
`domain/ports/`, y el adaptador de PostgreSQL debe ser la única pieza que
conozca SQL.

---

## 5 · Cómo se prueba

**R32.** La suite que ejecuta `bash harness/init.sh` no debe abrir ninguna
conexión de red ni de base de datos.

**R33.** DONDE está definida la variable de entorno que apunta a una base
efímera, el sistema debe ejecutar además la suite de base de datos; en su
ausencia esa suite debe saltarse por completo.

**R34.** SI la variable de la base efímera apunta a un host que no es local,
ENTONCES la suite de base de datos debe abortar sin abrir la conexión: nunca
se prueba contra el servidor compartido.

**R35.** SI el demonio de Docker no responde, ENTONCES el script de la suite
efímera debe abortar con un mensaje accionable que diga que hay que arrancar
Docker Desktop, en vez de dejar caer un error de conexión a la base.

**R36.** El script de la suite efímera y la suite de base de datos no deben
depender de que exista `psql` en el `PATH`.

---

## 6 · Salvaguardas del dato personal

> El humano resolvió el **2026-08-19** (decisión D2 de `design.md` §10) que
> **el DNI del cliente SÍ se persiste** en `partes.dni_cliente`. Estos cuatro
> requisitos son la contrapartida: hay dato personal directo en una base
> compartida, así que las salvaguardas dejan de ser una intención y pasan a
> ser verificables. `design.md` §6 dice cómo se comprueba cada una.

**R37.** El sistema no debe escribir nunca el DNI del cliente en el log, ni
completo ni parcial: de ese campo solo puede registrar si venía vacío y su
`confianza_pct`.

**R38.** El repositorio no debe contener ningún DNI real: los DNI que aparezcan
en tests, fixtures, specs o documentación deben ser inventados y estar marcados
como tales en el propio fichero.

**R39.** El sistema debe guardar el DNI del cliente en una sola columna,
`partes.dni_cliente`, y ninguna otra tabla debe copiarlo; quien lo necesite lo
recupera con un `JOIN` a `partes`.

**R40.** El sistema no debe guardar en la base los bytes del PDF del parte, que
contienen el DNI manuscrito: el documento vive en SharePoint y de él solo se
persisten metadatos, hash e identificadores.
