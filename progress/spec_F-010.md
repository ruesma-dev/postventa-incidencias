<!-- progress/spec_F-010.md -->
# F-010 · Despliegue en Azure y tarjeta en el portal — spec escrita

> **Fecha**: 2026-08-20. **Autor**: `spec-author`. **Rigor**: `estandar`.
> **Worktree aislado**, posicionado sobre `feature/F-007-front` (`d786b86`),
> no sobre `main`. **No se ha tocado `progress/current.md`**, que está en uso
> por el árbol principal con la review de F-007.

## Qué se ha escrito

- `specs/F-010-despliegue/requirements.md` — **35 requisitos EARS** en siete
  bloques (scripts re-ejecutables, secretos, acceso restringido, presupuesto
  del proxy, tarjeta del portal, alcance del piloto, y T18 de F-006), con
  tabla de trazabilidad requisito → verificación → tarea.
- `specs/F-010-despliegue/design.md` — recursos, gestión de secretos, cómo se
  enlazan front y backend, ficheros a crear/modificar/no tocar, las decisiones
  **D1–D7** (D1 y D3 ya resueltas) y riesgos. **§9 bis** es el razonamiento de
  D3.
- `specs/F-010-despliegue/tasks.md` — **22 tareas**, de las cuales **diez son
  `MANUAL (humano)`**, cada una con su comando exacto de PowerShell.

Ni un valor real en los tres ficheros: verificado aplicándoles los patrones
de `test_f006_repo_sin_identificadores.py` y de
`test_f005_integracion_sin_secretos.py` (GUID, FQDN de Azure, IP, credencial
con signo igual, cadena de conexión). **Los tres salen limpios.**

## Estado de las decisiones · **queda una bloqueante**

*Actualizado el 2026-08-20 tras la respuesta del humano.*

| # | Decisión | ¿Bloquea? |
|---|---|---|
| **D1** | ✅ **RESUELTA**: el humano crea él mismo el grupo en Entra con los miembros del piloto, y da por bueno el nombre **`posventa-usuarios`**. T1 avisa de confirmarlo antes de aplicarlo, porque el nombre tiene que coincidir en tres sitios: la asignación de la aplicación empresarial, `requiredGroupName` de la tarjeta y el propio grupo | ~~Sí~~ **ya no** |
| **D2** | **ABIERTA. El proxy de la Static Web App corta a los 45 s** (documentado en `azure-apps/portal.md` §9, aprendido con la app de nóminas). Hoy `IA_TIMEOUT_S` vale 120 y el `TIMEOUT_PETICION_MS` del front vale 180000: **el circuito no cabe**. Se propone bajarlos, pero antes hay que **medir** (T2) cuánto tarda de verdad una extracción | **SÍ** |
| **D3** | ✅ **RESUELTA**: defensa en capas, no una credencial en la Function. Razonamiento completo abajo y en `design.md` §9 bis | ~~Sí~~ **ya no** |
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

Lo crea F-010 y lo cierra F-010. **Cómo** se cierra es D3, y la primera
respuesta de esta spec era equivocada: ver la sección siguiente.

## D3 · el razonamiento, no solo la conclusión

*(Encargo del humano del 2026-08-20: recomendación con argumentos, después de
mirar qué hace de verdad el ecosistema.)*

### Lo que se fue a mirar, y qué se encontró

| Servicio | Forma | Cómo protege sus endpoints |
|---|---|---|
| `partes` sv4 — front de usuario | Container App, ingress externo | Autenticación integrada de Entra + **asignación requerida** + grupo de seguridad. Su `setup_sv4_easyauth.ps1` lo hace paso a paso y deja «asignacion-requerida = ON» |
| `partes` sv5 — servicio interno | Container App | **Ingress interno**: red, no credencial |
| `sigrid-api` | **Function App** | **Clave de función** (`x-functions-key`); sin ella, `401`. La clave vive en el Key Vault del consumidor |
| `nominas-extras` | **Function App detrás de una SWA enlazada** | **Nada en la Function**: sus dos endpoints, en `ANONYMOUS` |

**Nuestro caso es el cuarto.** Y es el que menos se parecía a lo que esta spec
proponía.

### El dato que tumba la propuesta anterior

`front-nominas/js/config.js` lo documenta sin ambigüedad: con la Static Web
App enlazada, el path `/api/...` **lo proxea la SWA y reenvía el
`X-MS-CLIENT-PRINCIPAL`** del usuario autenticado, y *«no hace falta clave de
Function ni CORS»*; exponer la Function directa es *«no recomendado, requiere
CORS y clave»*. Su `function_app.py` lo confirma: los dos endpoints anónimos.

Es decir: **el backend enlazado exige nivel anónimo**, y lo que llega al
backend es una **cabecera de identidad**, no un token ni una clave que la
Function pueda exigir. Consecuencias:

- **`auth_level=FUNCTION`, lo que esta spec proponía, no vale.** La SWA no
  aporta la clave: el front habría empezado a devolver `401` en los cinco
  endpoints el día del despliegue, y el fallo habría salido en T16, con todo
  ya montado. Es exactamente el punto 2 del encargo —«si el token no viaja, la
  opción no vale por bonita que sea»— y por eso se miró antes de escribir.
- **La autenticación integrada de Entra en la Function tampoco vale**, por lo
  mismo: espera un *bearer* que el proxy no envía. Funciona en `partes` sv4
  porque allí el navegador va directo al servicio; aquí hay un proxy en medio.

### Los dos riesgos no son iguales, y por eso no se tratan igual

`/api/archivar` **escribe** en SharePoint: efecto persistente sobre un sistema
compartido. `/api/extraer` y `/api/firma` **gastan cuota de Gemini**: es
dinero, y el dinero se acota con un tope. `/api/split` y `/api/validar` solo
consumen CPU. Y `/api/health` **debe seguir anónimo**, porque es lo que
permite monitorizarlo y lo que usa el propio despliegue.

### La recomendación · defensa en capas

1. La **Static Web App autentica** y exige pertenencia al grupo, vía
   asignación requerida. Mismo mecanismo que `partes` sv4.
2. La **Function queda anónima porque la plataforma lo exige** — y por eso hay
   que **dejarlo escrito**: sin nota en la cabecera y sin test, el siguiente
   que lo lea lo «arregla» y rompe el front (R32, T8).
3. **Ventana de escritura, el candado principal**: `ARCHIVO_HABILITADO` se
   despliega **apagado** (R33); se enciende solo para T18 y las sesiones con
   negocio y se vuelve a apagar, con una App Setting y sin redesplegar (R34).
   El interruptor **ya existe** —es el de F-006, apagado por defecto— y el
   patrón también: `partes` sv4 enciende y apaga su pantalla de administración
   igual. Fuera de la ventana, `/api/archivar` responde `503` a todo el mundo.
4. **Tope de gasto y alerta en el proveedor de IA** (R35, T14 bis).
5. **Restricción de acceso público en la Function App**, *si* resulta
   compatible con el backend enlazado: se intenta, se verifica en T14 **después
   de T16**, y si el front deja de funcionar **se revierte**. Es mejora, no
   cimiento, y por eso no se da por hecha (R17).
6. El destino sigue siendo la **biblioteca de dev**, no el archivo real.

**Descartadas**: `auth_level=FUNCTION` (la plataforma lo impide); Entra en la
Function (rompe el proxy); front llamando directo con MSAL y CORS (el propio
ecosistema lo desaconseja y obligaría a cambiar el front recién cerrado en
F-007); fiarse de `x-ms-client-principal` como control (es base64 **sin
firma**: cualquiera la fabrica); y fiarse de que nadie sepa el nombre de host,
que no es seguridad.

**Coste**: bajo, y es parte del argumento — no hay código nuevo. Lo que crece
es la verificación manual: T14 gana la comprobación de la capa 5, T14 bis es
nueva, y T18 gana el encendido y apagado explícitos de la ventana.

**Riesgo residual, declarado**: mientras la capa 5 no se confirme, queda una
ventana de horas en la que `archivar` está encendido y la Function es
alcanzable. Se anota como riesgo aceptado, igual que se hizo con el riesgo 7
de F-006.

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
