<!-- progress/spec_F-019.md -->
# F-019 · Informe del spec-author

**Fecha**: 2026-08-26 · **Rama**: `feature/F-019-endpoints-persistencia`
**Entregable**: `specs/F-019-endpoints-persistencia/` (requirements, design,
tasks). **Ni una línea de código**: la implementación es del implementer.

---

## 1 · Qué he leído antes de diseñar

`specs/SPECS.md`, la ficha entera de F-019 en `BACKLOG.md`,
`docs/ARCHITECTURE.md`, `docs/CONVENTIONS.md`, `docs/INTEGRACION.md` §8,
`domain/ports/persistencia.py`, `domain/models/persistencia.py`,
`application/pipelines/paso_persistencia.py` y `paso_archivo.py`,
`function_app.py` y los seis handlers de `interface_adapters/api/`,
`infrastructure/persistencia/` (fábrica, repositorio, sentencias y **el DDL de
las seis tablas**), `tests/test_f010_endpoints_protegidos.py`,
`tests/test_f010_integracion_expuesto.py`, el front (`api.js`, `pipeline.js`,
`app.js`) y `progress/review3_F-010.md`.

## 2 · Lo que cambia respecto a lo que parecía la feature

La ficha del backlog la describe como «tres endpoints». **Lo es y no lo es**:
tres endpoints sin más **no matan el defecto 15**. Si el orden depende de que
el llamante haga las cosas bien, vuelve el fallo en cuanto alguien llame a
`/api/archivar` por su cuenta — que es exactamente lo que se hizo el
2026-08-25 para verificar T18.

Por eso el diseño mete una pieza más: **`/api/archivar` escribe la traza del
archivo en estado `pendiente` ANTES de subir nada**. Como
`archivos.hash_parte` tiene clave ajena contra `partes`, esa escritura sólo
puede hacerse si el parte ya consta. **La misma restricción que hoy hace
fallar el proceso después de subir el fichero pasa a hacerlo fallar antes**,
y sin inventar una comprobación paralela que pueda divergir de la restricción
real.

Resultado: el 500 de «el fichero está arriba y falta la traza» se convierte en
un **409** de «guarda el parte primero», **sin haber subido nada**.

## 3 · Las seis decisiones que pedía el encargo, resueltas

1. **Endpoints nuevos vs. integrar en el pipeline** → **ambas cosas, pero no
   como suena**: endpoints nuevos (`POST /api/remesa`, `POST /api/parte`,
   `GET /api/cola`) que **llaman al `paso_persistencia` que ya existe** (no se
   reescribe: hasta hoy no tenía punto de entrada), más la garantía en
   `/api/archivar`. Descartado meter el guardado en `/api/extraer` o
   `/api/validar`: el primero no sabe de qué remesa viene el parte, el segundo
   no recibe el parte troceado, y el front revalida varias veces por parte.
2. **Orden y fallo del guardado** → se **aborta** el archivado. 409 si el parte
   no consta, 503 si la base no responde; en los dos casos **sin subir nada**.
   Un PDF archivado sin fila es un fichero del que el sistema no sabe nada.
3. **Idempotencia** → clave `hash_parte` para parte, validación y traza (ya lo
   garantizan los `upsert` de F-005). **La remesa es el punto flojo y lo digo
   en la spec**: `postventa.remesas` no tiene clave natural y dársela sería
   DDL, que está fuera de alcance. Mitigación: el llamante conserva y reenvía
   el `remesa_id`. No duplica partes; puede dejar una fila de remesa de más.
4. **Autenticación** → he leído `test_f010_endpoints_protegidos.py` y **lo
   respeto**: los tres nuevos van `ANONYMOUS` y el test se amplía a nueve.
   **Pero discuto una cosa distinta del `auth_level`**: `GET /api/cola` es el
   primer endpoint del servicio que devuelve **dato personal acumulado sin que
   el llamante aporte el PDF**. Eso cambia el modelo de amenaza y no lo arregla
   el `auth_level`. Va como **D1**.
5. **Ventana de escritura** → los endpoints nuevos **no** dependen de
   `ARCHIVO_HABILITADO`: escriben en el esquema propio, no en un sistema
   ajeno; atarlos dejaría sin poder guardar el trabajo justo cuando la ventana
   está cerrada, que es como se despliega. Y en `archivar` se **fija con un
   test** que la ventana corta antes de que la base se entere.
6. **Qué NO entra** → escrito en `design.md` §13: F-009 (`guardar_cierre` no se
   expone), preferencias de usuario, F-012, F-013, F-020, la pantalla de cola
   en el front, `usuario_oid`, y **rehidratar la sesión al recargar**.

## 4 · Lo que NO arregla esta feature, y conviene saberlo antes de aprobarla

La ficha atribuye a F-019 dos consecuencias. **Arregla una y media**:

- ✅ **El archivado real puede completar** (defecto 15). Ese es el bloqueo del
  piloto y se muere aquí.
- ✅ **La cola de validación humana sobrevive entre sesiones**: se escribe y se
  lee.
- ⚠️ **Recargar la pestaña sigue perdiendo el trabajo en curso.** Lo guardado
  queda guardado, pero volver a pintarlo exige **leer una remesa entera con
  sus partes**, y para eso hace falta un método de lectura nuevo en
  `RepositorioPartesPort` — que el encargo prohíbe tocar. Va como **D4**, con
  recomendación de feature nueva.

## 5 · Decisiones abiertas para el humano

| # | Qué | Recomendación |
|---|---|---|
| **D1** | `GET /api/cola` anónimo devolviendo observaciones manuscritas de clientes | **Sacarlo `ANONYMOUS`** (cualquier otra cosa rompe el front) con tope de límite, nada al log y el riesgo escrito en la cabecera; **y valorar la restricción de acceso público de la Function App**, que es la única capa real. Opcional encima: exigir `x-ms-client-principal`, que sube el listón pero **no es control de acceso** (base64 sin firma) |
| **D2** | `postventa.remesas` sin clave natural | **Aceptarlo ahora**: no duplica partes. Darle una es DDL |
| **D3** | ¿Guardar `usuario_oid`? | **No en F-019**: la cabecera no está firmada y guardarla invita a confundir traza con identidad verificada |
| **D4** | Rehidratar la sesión al recargar | **Feature nueva**, después de ver el piloto |
| **D5** | ¿Entra el cableado del front (T15–T16)? | **Sí.** Sin él, los endpoints existen y **nadie los llama**: el mismo estado que la feature viene a arreglar, un nivel más arriba. Si el humano dice que no, se caen R24–R27 y T15–T16, y hay que decir al cerrar que el archivado real sigue sin poder completar en el circuito |

## 6 · Alcance en números

- **4 ficheros de código nuevos** (tres handlers + un módulo de parsers
  compartidos) y **7 de test nuevos** (6 Python + 1 JS).
- **13 ficheros modificados**, de los cuales 3 son del front, 2 son
  documentación normativa (`INTEGRACION.md`, `ARCHITECTURE.md`) y 3 son tests
  de F-005/F-006/F-010 que **se aprietan, no se relajan**.
- **0 ficheros SQL**, **0 sentencias DDL**, **0 conexiones reales**. El puerto
  `RepositorioPartesPort` **no gana ni un método**.
- **20 tareas**, con fase RED explícita en 6 de ellas, cobertura, mutación,
  `init.sh` en verde y **una sola verificación `MANUAL (humano)`** (T20: el
  circuito del defecto 15 contra el despliegue, con parte sintético y la
  ventana de escritura abierta sólo para la prueba y cerrada al terminar).

## 7 · Riesgos que el implementer tiene que vigilar

1. **Los tests de F-006 hay que ajustarlos** (ahora `guardar_archivo` se llama
   dos veces en el camino feliz). La tentación es relajar los dobles; la spec
   manda lo contrario: exigir **dos llamadas, en orden `pendiente → archivado`**.
2. **Mover los parsers de `validar.py` a `cuerpos.py`** es mecánico pero está
   en el camino crítico: va en su propio commit (T1) y con
   `test_f004_validar_http.py` **sin tocar** como red.
3. **La garantía de orden depende de que la clave ajena siga en el DDL.** Hoy
   nadie la fija: T12 añade esa aserción al test de texto del DDL.
4. **Una llamada HTTP más por parte en el front**: milisegundos contra un
   presupuesto de 45 s con un peor caso medido de 6,5 s. No es riesgo de
   tiempo, pero conviene medirlo en T20.

## 8 · Cumplimiento de las reglas duras

- Nada contra Azure, SharePoint, PostgreSQL ni Sigrid: **ni una conexión**.
- Sin secretos, sin cadenas de conexión y sin datos personales en la spec (los
  ejemplos usan el parte sintético `0677 / RS26.08 - 0123` que ya está en las
  specs desde F-003).
- `harness/features.json` **sin tocar**: el estado lo mueve el líder.
- `bash harness/init.sh` ejecutado tal cual al terminar: **verde**.
- Commit local en la rama, sin `push` ni PR.
- `azure-apps/`: §8 de `INTEGRACION.md` cambia, así que hay que copiarla allí,
  **pero el humano decidió el 2026-08-20 que los agentes no commitean en ese
  repositorio**. Queda anotado como aviso, no como tarea de agente.
