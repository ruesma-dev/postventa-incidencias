<!-- progress/explore_F-006.md -->
# F-006 · Nombrado y archivo en SharePoint — spec redactada

- **Fecha**: 2026-08-19
- **Rama**: `feature/F-006-sharepoint`, sacada de `dev` (que ya trae F-002 y
  F-003 mergeadas).
- **Worktree AISLADO**: `.claude/worktrees/agent-a270937a57b6c10e2`. No se ha
  tocado el árbol principal, donde otro agente implementa F-004 sobre
  `feature/F-004-validacion`.
- **Entregado**: `specs/F-006-sharepoint/` con `requirements.md` (32
  requisitos EARS), `design.md` y `tasks.md` (21 tareas, 6 con fase RED, 3
  `MANUAL (humano)`).
- **Estado que corresponde**: `F-006` sigue `pending` hasta que el humano
  apruebe la spec. **No** se ha tocado `harness/features.json` ni
  `progress/current.md` (los usa el árbol principal).

> **No se ha escrito ni una línea de código.** Este agente redacta la
> especificación; implementarla es del `implementer`, y solo después de que el
> humano apruebe.

---

## 1 · Lo que se ha leído antes de diseñar

- `specs/SPECS.md`, `docs/ARCHITECTURE.md`, `docs/CONVENTIONS.md`,
  `CHECKPOINTS.md`, `harness/rigor.json`, `harness/servicios.json`.
- La ficha completa de F-006 en `harness/features.json` (`description` +
  cinco `acceptance`).
- El código realmente afectado: `domain/models/remesa.py`,
  `domain/models/extraccion.py`, `domain/models/errores.py`,
  `domain/ports/extractor.py`, `config/settings.py`,
  `application/pipelines/contexto_parte.py`, `interface_adapters/api/extraer.py`,
  `function_app.py`, `infrastructure/llm/gemini.py`, `tests/conftest.py`.
- **Sin cambiar de rama**: `git show feature/F-004-validacion:specs/.../design.md`
  y `git show feature/F-005-persistencia:specs/.../design.md`.
- **El ecosistema**: los ocho documentos de
  `C:\Users\pgris\PycharmProjects\azure-apps` (README, `partes.md`,
  `albaranes.md`, `remesas.md`, `portal.md`, `datamart_seg_anual.md`,
  `sigrid_api.md`, `arnes_base.md`), con barridos de `sharepoint`, `graph`,
  `SHAREPOINT_*`, `GRAPH_*`, `SITE_*`, `DRIVE_*`, `Sites.`, `Files.`.

---

## 2 · Lo decidido (resumen; el detalle está en `design.md`)

1. **El nombrado es dominio puro** (`domain/models/nombrado.py`), sin reloj,
   sin red y sin configuración. La trampa de las semánticas 2 y 5 de
   `ARCHITECTURE` está escrita en la spec **antes** que el código: obra e
   incidencia son cosas distintas, la barra `RS26.08/0123` se convierte en
   ` - ` al nombrar, los ceros de `0677` se conservan (ningún `int()` toca el
   código de obra), el sufijo ` PARTE FIRMADO` va literal, y sin nº de
   incidencia **no se nombra** ni se deduce.
2. **Un nombre imposible es un error, no un saneo silencioso**: sustituir un
   carácter raro por `_` archivaría en el archivo de Posventa un fichero con
   un nombre que nadie pidió y nadie se enteraría.
3. **Idempotencia en tres capas**, apoyadas en lo que ya existe: (L1) la traza
   de F-005, con PK por `hash_parte` —el hash del parte troceado de F-002, que
   es el criterio que ya usan `ARCHITECTURE` semántica 9 y F-005; **no se
   inventa otro**—; (L2) la subida pide **siempre reemplazar** el homónimo,
   nunca renombrar, que es lo que produce el `archivo (1).pdf` prohibido por
   el `acceptance`; (L3) la carpeta por código de obra se crea sola y tolera
   «ya existe».
4. **El test que hace verdad el `acceptance` 3 es de comportamiento, no de
   constante**: `BibliotecaFalsa` imita una biblioteca real (reemplazar pisa;
   renombrar crea `nombre (1).pdf`), y el test afirma que tras archivar dos
   veces hay **un** elemento y ningún `(1)`.
5. **La regla dura, garantizada en código y no por costumbre** (`design.md`
   §5): puerta de entorno **en el constructor del adaptador** (no solo en la
   fábrica, para que componer las piezas a mano no la salte),
   `ARCHIVO_HABILITADO` **fail-closed** (por defecto falso), la guardia de red
   de F-003 **intacta**, y tests de arquitectura que impiden que dominio y
   aplicación conozcan Graph. La única subida real permitida ocurre **desde el
   entorno desplegado**, contra el destino de dev, y es la verificación manual
   T18.
6. **Se reutiliza el patrón del ecosistema**: Graph app-only con app
   registration, como `partes` (sv3) y `albaranes`; y la traza guarda los
   mismos conceptos que ellos (`drive_id`, `item_id`, ruta, `web_url`). **No
   se reutiliza ni un identificador**, porque `azure-apps/` no los publica ni
   debe.
7. **El documento del ecosistema reusa el mecanismo de F-005**:
   `docs/INTEGRACION.md` (que crea F-005) recibe una sección de SharePoint —es
   la tarea T15, no un «luego»— y la copia a
   `azure-apps/postventa_incidencias.md` queda como `MANUAL (humano)` (T19),
   porque es otro repositorio git. **No se crea un mecanismo paralelo.**
8. **Precondición dura declarada**: F-006 se implementa **la tercera**, con
   F-004 y luego F-005 mergeadas en `dev`. Se ha descartado a propósito
   diseñar modelos gemelos (`ResultadoArchivo` propio, «apto» propio) para
   poder empezar antes.
9. **F-006 no añade DDL**: la tabla `archivos` es de F-005. Nada toca el
   servidor compartido fuera del esquema propio.
10. **Datos personales**: los ejemplos de la spec (`0677`, `RS26.08/0123`) son
    inventados y van marcados; ningún test depende de `muestras/`; ni el
    motivo de error, ni el log, ni la respuesta HTTP llevan bytes del parte,
    DNI, observaciones ni la credencial, y hay tests para eso (R26).
11. **Límite de microservicio comprobado**: F-006 vive entera en
    `services/postventa-api/`. Front es F-007, Sigrid es F-009/F-012, y el
    documento de `azure-apps/` se copia a mano.

---

## 3 · ESTADO DE LAS DECISIONES

**Seis en total: una RESUELTA (D3), una BLOQUEANTE viva (D6) y cuatro
abiertas que no bloquean (D1, D2, D4, D5).**

Actualizado el **2026-08-19**, cuando el humano resolvió D3. Las otras cinco
siguen exactamente como estaban: **nadie las ha decidido**.

### ✅ D3 — RESUELTA el 2026-08-19 · opción (a)

El rigor `critico` exige verificaciones `MANUAL (humano)` **con su resultado
real**, y la única subida real permitida es desde el entorno desplegado. Pero
el despliegue es **F-010** (prioridad 10), cuatro features más tarde que
F-006 (prioridad 6).

**Resuelto por el humano: opción (a).** F-006 se implementa y **se cierra**
con **T18 declarada y PENDIENTE**, a ejecutar cuando **F-010** despliegue el
entorno. En `tasks.md`, T18 queda como `MANUAL (humano) · DIFERIDA A F-010`,
con su comando previsto y su criterio de verificación: aplazada con fecha, no
olvidada.

**Descartadas:**

- **(b)** Adelantar un despliegue mínimo de la Function App a dev antes de
  cerrar F-006. **Descartada.**
- **(c)** Reordenar el backlog para que F-010 pase por delante de F-006.
  **Descartada.**

**Lo que NO es opción, y sigue firme**: subir desde local «solo para probar».
`CLAUDE.md` lo prohíbe sin matices y el `acceptance` lo repite.

**Consecuencia que hay que llevar al reviewer**: F-006 llegará a la revisión
con una verificación manual **sin resultado real**, y el rigor `critico` la
exige. Ese cierre necesita **autorización expresa del humano ante
`CHECKPOINTS.md` C5**; el arnés por sí solo no puede darlo por bueno. Es
exactamente el caso que motiva **F-017** (que C5 distinga la tarea de agente
pendiente de la verificación `MANUAL (humano)` pendiente).

### 🔴 D6 — BLOQUEA · El destino de dev todavía no existe

Nadie ha creado aún la **biblioteca propia dentro del sitio de IT** ni el **app
registration** con permiso de escritura sobre ella. Hace falta que el humano
(o IT) lo cree y pase los identificadores por el `.env` del despliegue,
**nunca por el repositorio**. Sin esto, T17 y T18 no se pueden ejecutar.

Sub-pregunta que conviene decidir a la vez: **qué permiso de Graph** se pide.
`Sites.Selected` acotado a esa biblioteca es lo mínimo y lo prudente;
`Files.ReadWrite.All` da acceso a todo el tenant y es lo que probablemente ya
tenga alguna aplicación del ecosistema. La spec no elige por el humano.

### 🟡 D1 — no bloquea · Qué reutilizar exactamente de `partes` / `albaranes`

`azure-apps/` dice **que** `partes` (sv3) y `albaranes` suben PDFs a SharePoint
por Graph con client/secret de un app registration, pero **no dice** qué
librería cliente de Python usan, qué permisos tienen, ni con qué nombres de
variable. Es un hueco real del ecosistema.

La spec propone `msal` + `requests` y lo aísla en `infrastructure/sharepoint/`:
si resulta que la casa usa otra cosa, **solo cambia ese paquete** (tarea T8).
Merece la pena mirarlo en el repositorio `partes` antes de implementar, para
no montar el tercer cliente distinto de Graph de la casa.

### 🟡 D2 — no bloquea · Mismo nombre, otro hash

Dos escaneos distintos de la misma incidencia producen el **mismo nombre** y
distinto `hash`, así que L1 no los ve. La spec **reemplaza y deja aviso**: el
archivo de Posventa se queda con la última versión conformada. La alternativa
sería fallar y mandarlo a revisión humana. Se implementa el reemplazo salvo
que el humano diga lo contrario.

### 🟡 D4 — no bloquea · De dónde sale el veredicto en el endpoint

`POST /api/archivar` **recibe** el veredicto en el cuerpo y el paso lo vuelve
a comprobar antes de subir nada. Leerlo de la base sería más fuerte —el
servicio no se fiaría de quien llama—, pero exige un método nuevo en
`RepositorioPartesPort` (F-005). **F-006 no cambia specs ajenas**: queda
anotado, no hecho.

### 🟡 D5 — no bloquea · `EstadoArchivo` no tiene `ya_archivado`

El enum de F-005 declara `pendiente | archivado | error`. El caso «ya estaba
archivado» sale por tanto como `archivado` + aviso. Añadir el estado sería más
limpio y más legible en el front de F-007, pero es un cambio en F-005.
**Anotado, no hecho.**

---

## 4 · Detectado en F-004 / F-005, NO cambiado

Ninguna de las dos specs necesita cambiar para que F-006 sea posible. Lo único
que se ha detectado, y va como D4 y D5, son dos mejoras opcionales de F-005
(un método de lectura de la validación y un estado más en `EstadoArchivo`) que
harían F-006 algo más robusta pero **no** la desbloquean. Ambas quedan a
criterio del humano.

---

## 5 · Qué necesita el implementer antes de empezar

1. Aprobación de la spec por el humano (PARADA 1 de `CLAUDE.md`).
2. **F-004 y F-005 mergeadas en `dev`**, en ese orden, y esta rama rebasada
   sobre `dev` (T1). Si no, `blocked`.
3. Resolución de **D1** (recomendable antes de T8) y de **D6** (antes de T17;
   el resto de la feature se puede implementar sin ella).
4. **D3 ya no hace falta esperarla**: resuelta el 2026-08-19 por la opción
   (a). **T18 no se ejecuta dentro de F-006**, se difiere a **F-010**. Al
   cerrar la feature, el `reviewer` encontrará T18 en `[ ]` y necesitará la
   autorización expresa del humano ante `CHECKPOINTS.md` **C5** (motivo de
   **F-017**).
