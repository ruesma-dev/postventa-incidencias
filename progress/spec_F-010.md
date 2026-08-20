<!-- progress/spec_F-010.md -->
# F-010 · Despliegue en Azure y tarjeta en el portal — spec escrita

> **Fecha**: 2026-08-20. **Autor**: `spec-author`. **Rigor**: `estandar`.
> **Worktree aislado**, posicionado sobre `feature/F-007-front` (`d786b86`),
> no sobre `main`. **No se ha tocado `progress/current.md`**, que está en uso
> por el árbol principal con la review de F-007.

## Qué se ha escrito

- `specs/F-010-despliegue/requirements.md` — **31 requisitos EARS** en siete
  bloques (scripts re-ejecutables, secretos, acceso restringido, presupuesto
  del proxy, tarjeta del portal, alcance del piloto, y T18 de F-006), con
  tabla de trazabilidad requisito → verificación → tarea.
- `specs/F-010-despliegue/design.md` — recursos, gestión de secretos, cómo se
  enlazan front y backend, ficheros a crear/modificar/no tocar, **siete
  decisiones abiertas D1–D7** y riesgos.
- `specs/F-010-despliegue/tasks.md` — **21 tareas**, de las cuales **nueve son
  `MANUAL (humano)`**, cada una con su comando exacto de PowerShell.

Ni un valor real en los tres ficheros: verificado aplicándoles los patrones
de `test_f006_repo_sin_identificadores.py` y de
`test_f005_integracion_sin_secretos.py` (GUID, FQDN de Azure, IP, credencial
con signo igual, cadena de conexión). **Los tres salen limpios.**

## Lo que el humano tiene que decidir · **tres decisiones bloquean**

| # | Decisión | ¿Bloquea? |
|---|---|---|
| **D1** | **El grupo de seguridad de Posventa no existe.** Falta decidir nombre (se propone `posventa-usuarios`), propietario y miembros del piloto. Lo crea el humano o IT: un agente no toca el inquilino | **SÍ** |
| **D2** | **El proxy de la Static Web App corta a los 45 s** (documentado en `azure-apps/portal.md` §9, aprendido con la app de nóminas). Hoy `IA_TIMEOUT_S` vale 120 y el `TIMEOUT_PETICION_MS` del front vale 180000: **el circuito no cabe**. Se propone bajarlos, pero antes hay que **medir** (T2) cuánto tarda de verdad una extracción | **SÍ** |
| **D3** | **Cómo se cierra la Function App.** Ver el hallazgo de abajo | **SÍ** |
| D4 | El cortafuegos de `psql-albaranes-rs9k2`: si hiciera falta una regla nueva, es un cambio **a nivel de servidor compartido** y lo decide el humano con albaranes | Solo para la traza del archivo |
| D5 | Nombre de host del front: se propone el que asigna Azure, sin dominio propio | No |
| D6 | ¿Esperar a F-018? Se propone **no esperar** y subir F-018 justo detrás | No |
| D7 | Quién aplica y despliega la tarjeta en `front-portal` | No |

## El hallazgo que más importa

**El despliegue, tal y como está el código hoy, abriría a internet un endpoint
que escribe en SharePoint.** Los seis endpoints de `function_app.py` están en
`auth_level=ANONYMOUS`, lo cual es correcto mientras solo escuchen en
`localhost:7073`. Pero en el entorno desplegado `ENTORNO` vale `dev` y
`ARCHIVO_HABILITADO` está encendido, así que **las dos puertas que impiden
subir desde local están abiertas por diseño**, y `POST /api/archivar` quedaría
al alcance de cualquiera que supiera el nombre de host — igual que
`/api/extraer`, con la cuota de Gemini detrás.

Lo crea F-010 y lo cierra F-010: es **R17**, la tarea **T8** con fase RED, y
la verificación manual **T14**, que exige comprobar que una llamada al host
desnudo devuelve `401` antes de seguir.

## Sobre T18 de F-006, que es lo que esta feature desbloquea

Recogido como bloque G de los requisitos (**R29–R31**) y como tarea **T18**,
con el comando exacto (`verificar_archivo_dev.ps1 -BaseUrl`), el criterio de
los tres puntos, y la parada si aparece un fichero con sufijo `(1)`.

Queda escrito que **requiere autorización expresa del humano ante
`CHECKPOINTS.md` C5**, y por qué no es una formalidad: F-006 se cerró con esa
casilla vacía por una dependencia declarada, y quien la marque está cerrando
una feature ajena.

## Sobre la tarjeta del portal, sin suponer nada

`front-portal` **no** está en el mismo caso que `azure-apps`: es un
repositorio con historial y commits del humano, mientras que en `azure-apps`
él mismo declaró el 2026-08-20 que no commitea (por eso T19 de F-006 quedó
`N/A`). Pero tampoco se da por hecho lo contrario: la última actividad es de
julio de 2026 y dar de alta una tarjeta exige además **desplegar** el portal,
que es un acto sobre Azure y no un commit.

Por eso el entregable de F-010 es **el bloque escrito** en
`docs/DESPLIEGUE.md`, y T19 queda `MANUAL (humano) · OTRO REPOSITORIO` con
las dos vías abiertas. El criterio de aceptación —«queda escrito qué hay que
cambiar en `catalog.js`»— se cumple sin depender de quién lo aplique.

## Qué verá negocio en el piloto, y qué no

Verá el circuito de la entrada al archivo: soltar la remesa, troceado,
extracción, firma, semáforo, corrección manual y archivo en SharePoint.

**No verá** el cierre en Sigrid (F-008, F-009, deliberadamente fuera) ni la
cola persistida: F-005 creó las tablas, pero los endpoints que guardan la
remesa y leen la cola son **F-019**, todavía pendiente. Consecuencia visible y
que hay que avisar antes de la demostración: **si el usuario recarga la
página, pierde el trabajo en curso**.

## Nota para quien implemente

`services/postventa-front/js/config.js` es de F-007, que estaba **en revisión**
mientras se escribía esta spec. La fase 2 de `tasks.md` no empieza hasta que
`feature/F-007-front` esté cerrada y mergeada (riesgo 4 de `design.md` §10).
