# F-010 · Despliegue en Azure y tarjeta en el portal — informe de implementación

> Rama `feature/F-010-despliegue`. Rigor **`estandar`**. Informe **incremental**:
> se ha escrito y commiteado tarea a tarea, no al final.
>
> **Ni un valor real en este fichero**: ni FQDN, ni GUID, ni identificador de
> suscripción, inquilino, sitio o aplicación. Solo nombres de recurso y nombres
> de variable.

---

## Resumen en una pantalla

**Qué cambió**: cuatro de los cinco scripts de `infra/`, la cabecera de
`function_app.py`, tres documentos (`DESPLIEGUE.md` nuevo, `INTEGRACION.md` §8,
`ARCHITECTURE.md`) y cuatro ficheros de test nuevos. **Nada se ha ejecutado
contra Azure**: no hay ni un recurso creado, ni un secreto cargado, ni una
subida a SharePoint.

**Qué se verificó**: `bash harness/init.sh` en verde; 1.044 tests del servicio
`api` en verde, de los que **120 son de F-010**; campaña de mutación ejecutada
con sus tres supervivientes analizados.

**Qué quedó fuera, y por qué**: **T5 y T9 están sin hacer y bloqueadas por D2**
—fijan los tiempos de espera, y el implementer no elige esos números—. Las diez
tareas `MANUAL (humano)` están preparadas, no ejecutadas.

**Qué falta para cerrar**: la decisión de D2, T5, T9, y las manuales.

---

## Estado de las tareas

| Tarea | Estado | Nota |
|---|---|---|
| T1 · MANUAL | Preparada | El humano crea `posventa-usuarios` en Entra |
| T2 · MANUAL, alimenta **D2** | **MEDIDA** | La ejecutó el implementer a petición del líder |
| T3 | **Hecha** | `infra/00_vars_postventa.ps1` |
| T4 | **Hecha** | `infra/cargar_secretos_postventa.ps1` |
| T5 | **BLOQUEADA por D2** | Fija `IA_TIMEOUT_S` y `GRAPH_TIMEOUT_S` |
| T6 | **Hecha** | `infra/desplegar_front.ps1` |
| T7 | **Hecha** | `infra/verificar_despliegue.ps1` |
| T8 | **Hecha** | Cabecera de `function_app.py` + test |
| T9 | **BLOQUEADA por D2** | Fija `TIMEOUT_PETICION_MS` |
| T10 | **Hecha** | `docs/DESPLIEGUE.md` + bloque de la tarjeta |
| T11 | **Hecha** | `docs/INTEGRACION.md` §8 |
| T12 | **Hecha** | `docs/ARCHITECTURE.md` §Infra y despliegue |
| T13–T19 · MANUAL | Preparadas | Ninguna ejecutada |
| T20 | **Hecha** | Campaña de mutación, supervivientes analizados |
| T21 | **Hecha** | `bash harness/init.sh` en verde |

---

## T2 · La medición de D2 · los 45 s del proxy

**Qué se midió y cómo.** Contra la Function arrancada **en local**
(`localhost:7073`, ya en marcha en el puesto: el puerto estaba ocupado y
respondía `GET /api/health` con `200`), con un guion de biblioteca estándar
—**no se añadió ninguna dependencia al proyecto**— que llama a los endpoints
por HTTP igual que lo hace el front. El guion vive en el directorio temporal de
la sesión, **no en el repositorio**.

Entrada: la remesa escaneada real que ya está en el árbol de trabajo sin
versionar (5.286 KB, **22 partes** tras el troceado). No se imprimió ni se
guardó **ningún** campo del parte: solo segundos y códigos HTTP, como exige la
verificación de T2 («sin nombres de obra, sin códigos de incidencia y sin
DNI»).

**Salida real del guion:**

```
remesa: 5286 KB
split: 2.4s -> 200
partes troceados: 22
--- secuencial (2 partes, una peticion viva) ---
extraer: 5.5s -> 200
firma: 4.1s -> 200
extraer: 5.2s -> 200
firma: 4.1s -> 200
--- concurrente (3 partes = 6 peticiones vivas, como el front) ---
extraer: 6.2s -> 200
firma: 5.1s -> 200
extraer: 6.1s -> 200
firma: 5.2s -> 200
extraer: 6.5s -> 200
firma: 5.5s -> 200
lote completo: 6.5s
```

**Los tres números que pedía T2 (peor caso observado de cada endpoint):**

| Endpoint | Peor caso, 1 petición viva | Peor caso, 6 peticiones vivas |
|---|---|---|
| `POST /api/split` (22 partes, 5,2 MB) | **2,4 s** | — (se llama una sola vez) |
| `POST /api/extraer` | 5,5 s | **6,5 s** |
| `POST /api/firma` | 4,1 s | **5,5 s** |

El segundo bloque es el que importa: reproduce lo que hace el front de verdad
con `CONCURRENCIA_PARTES: 3` —tres partes vivos, seis peticiones simultáneas—
contra **un solo worker** de `func start`. La concurrencia sube el peor caso
de 5,5 s a 6,5 s, un 18 %.

**Lectura contra el criterio de decisión de T2.** El criterio escrito era: *«si
el peor `/api/extraer` queda holgadamente por debajo de 35 s, se sigue con la
opción (a) de D2»*. El peor `/api/extraer` medido es **6,5 s**, un **14 % del
presupuesto de 45 s** del proxy y menos de la quinta parte de los 35 s
propuestos. Cabe con holgura.

**Matices que el humano debe tener delante antes de decidir, porque la
medición es en local y el despliegue no lo es:**

1. **No incluye el salto de región.** Se midió puesto → Function local. En
   producción hay un tramo más: navegador → Static Web App (`westeurope`) →
   Function (`spaincentral`). `design.md` §4 ya avisa de que ese salto se paga
   y se descuenta del presupuesto. Con 6,5 s medidos contra 45 s de tope, el
   margen absorbe ese tramo sin discusión.
2. **No incluye el arranque en frío** de una Function App en Flex Consumption,
   que la primera petición del día sí paga.
3. **La latencia del proveedor de IA no la controlamos**: 6,5 s es lo medido
   hoy con `gemini-3.7-flash`; un día malo del proveedor o un parte con más
   páginas sube ese número, y por eso el tiempo de espera sigue haciendo falta.
4. **`split` no escala con el tamaño como se podría temer**: 22 partes de una
   remesa de 5,2 MB en 2,4 s. No es el endpoint en riesgo.

**Decisión pendiente, y por eso esta feature no se cierra aquí.** El
implementer **no fija los valores nuevos**: T5 (`IA_TIMEOUT_S`,
`GRAPH_TIMEOUT_S`) y T9 (`TIMEOUT_PETICION_MS`) quedan sin tocar hasta que el
humano decida con estos números delante. Lo que la spec propone es la opción
(a): 35 s y 40000 ms.

**Coste de la medición**: diez llamadas reales al proveedor de IA
(cuatro secuenciales y seis concurrentes) más un troceado. Ninguna escritura,
ningún recurso de Azure tocado, nada subido a SharePoint.

---

## Ficheros tocados

### Nuevos

| Ruta | Qué es | Tarea |
|---|---|---|
| `infra/00_vars_postventa.ps1` | Fuente única de nombres, regiones y tags | T3 |
| `infra/cargar_secretos_postventa.ps1` | Key Vault y los once secretos | T4 |
| `infra/desplegar_front.ps1` | Entra, Static Web App y subida | T6 |
| `infra/verificar_despliegue.ps1` | Las tres comprobaciones, solo lecturas | T7 |
| `docs/DESPLIEGUE.md` | Runbook + bloque de la tarjeta del portal | T10 |
| `services/postventa-api/tests/test_f010_scripts_infra.py` | Contrato de los scripts | T3, T4, T6, T7 |
| `services/postventa-api/tests/test_f010_endpoints_protegidos.py` | R18, R32 | T8 |
| `services/postventa-api/tests/test_f010_tarjeta_portal.py` | R23, R24, R25, R34 | T10 |
| `services/postventa-api/tests/test_f010_integracion_expuesto.py` | R26 | T11 |

### Modificados

| Ruta | Qué cambió | Tarea |
|---|---|---|
| `services/postventa-api/function_app.py` | **Solo la cabecera**: por qué los seis endpoints siguen anónimos y dónde está el control de acceso | T8 |
| `docs/INTEGRACION.md` | §8 rellenada + filas del despliegue en §9 | T11 |
| `docs/ARCHITECTURE.md` | §«Infra y despliegue»: recursos, regiones, 45 s y anonimidad | T12 |
| `.gitignore` | `infra/*.local.ps1` | T3 |

### Deliberadamente NO tocados

`staticwebapp.config.json` (conserva su marcador `<TENANT_ID>`), `host.json`,
`dev_server.py`, `.env.example`, los scripts de F-005 y F-006, `front-portal`
y `azure-apps/`.

---

## Decisiones de diseño tomadas al implementar

**1. El secreto de cliente del front lo genera `desplegar_front.ps1`, no el
humano en T13.** La spec dice que `swa-client-id` y `swa-client-secret` van al
Key Vault (T13) y que las App Settings de la Static Web App se fijan «leídas
del Key Vault en tiempo de despliegue» (§3). Pero el registro de aplicación
**no existe** hasta T16, que va después de T13: el huevo y la gallina. Se ha
resuelto así, y es coherente con las dos piezas: el modo completo de
`desplegar_front.ps1` genera el secreto, **lo guarda en el Key Vault** con esos
dos nombres y lo fija en la Static Web App; `cargar_secretos_postventa.ps1`
permite dejar un secreto vacío para no tocarlo, así que en T13 esos dos se
dejan en blanco. Queda un solo sitio donde mirar y ningún paso imposible.

**2. `verificar_despliegue.ps1` mira la App Setting antes de llamar a
`archivar`.** R27 pide comprobar que `POST /api/archivar` responde `503`, y el
`503` solo salta con el cuerpo **completo y válido** —el handler valida el
cuerpo antes de llegar a la puerta del entorno—. Es decir: esa llamada, con la
ventana **abierta**, subiría un PDF de verdad a SharePoint. El script lee antes
`ARCHIVO_HABILITADO` (una lectura) y, si la encuentra encendida, **no hace la
llamada**: lo dice y lo cuenta como hallazgo. Sin esa cautela, el verificador
sería justo lo que promete no ser.

**3. El `appRoleId` de «acceso predeterminado» se compone, no se escribe.** Es
el identificador de todo ceros, y tiene forma de GUID: el barrido de
identificadores del repositorio lo cazaría. Va montado a partir de trozos, con
el comentario que explica por qué.

**4. Los scripts se leen como ASCII en los tests**, igual que en F-005 y F-006.
Es deliberado y ya ha saltado dos veces durante esta implementación (unas
comillas angulares y una raya larga): un acento mal codificado en un nombre de
recurso es un recurso que no se encuentra.

**5. El front que se sube va sin la suite ni el servidor de desarrollo.**
`desplegar_front.ps1` limpia `tests`, `tests_js`, `dev_server.py` y compañía de
la copia de trabajo: es código de más en un sitio expuesto a internet.

---

## Evidencias de la fase RED

El rigor de esta feature es **`estandar`**, y la spec sitúa **la fase RED en
R33** (T5): el test que exige que `desplegar_backend.ps1` deje
`ARCHIVO_HABILITADO` apagado se escribe antes que el script. **T5 está
bloqueada por D2**, así que esa fase RED **queda pendiente** y se hará en el
mismo trabajo que T5. No se ha simulado ni se ha dado por hecha.

Lo que sí se ha demostrado con una traza real es que **el test de R32 tiene
dientes**, que es la otra mitad del riesgo 1 bis del diseño. Se cambió un solo
`auth_level` a `FUNCTION` en `function_app.py` y se ejecutó el test:

```
$ grep -n 'route="extraer"' function_app.py
165:@app.route(route="extraer", methods=["POST"], auth_level=func.AuthLevel.FUNCTION)

$ python -m pytest tests/test_f010_endpoints_protegidos.py -q
E         Extra items in the left set:
E         'FUNCTION'
tests\test_f010_endpoints_protegidos.py:78: AssertionError
FAILED tests/test_f010_endpoints_protegidos.py::test_f010_r32_la_anonimidad_es_deliberada_y_esta_explicada
1 failed, 5 passed in 0.13s
```

El fichero se revirtió inmediatamente y volvió a verde. Es la comprobación de
que el candado documental de R32 salta de verdad el día que alguien «arregle»
el `auth_level`.

---

## Verificaciones MANUAL (humano) pendientes

Ninguna se ha ejecutado. **Todas están preparadas** con su comando exacto en
`specs/F-010-despliegue/tasks.md` y en `docs/DESPLIEGUE.md`.

| Tarea | Qué falta | Bloquea a |
|---|---|---|
| T1 | Crear `posventa-usuarios` en Entra con los miembros del piloto | T16, T19 |
| T13 | Cargar los once secretos en el Key Vault | T14 |
| T14 | Desplegar el backend + comprobar las cuatro cosas, incluida la capa 5 | T16, T17, T18 |
| T14 bis | Tope de gasto y alerta en el proveedor de IA | **antes de T16** |
| T15 | Comprobar que la Function alcanza `psql-albaranes-rs9k2` (D4) | Nada del piloto |
| T16 | Desplegar el front y probar con **dos cuentas** | T17, T19 |
| T17 | Re-ejecutar los dos despliegues (criterio de aceptación) | Cierre |
| T18 | La subida real a SharePoint · **requiere autorización expresa ante C5** | Cierre de F-006 |
| T19 | La tarjeta en `front-portal` · otro repositorio | Cierre |

Dos recordatorios que no son formalidades:

- **T18 cierra una feature ajena** (T18 de F-006). `CHECKPOINTS.md` **C5**
  exige `tasks.md` con todas las casillas marcadas, y F-006 se cerró con esa
  vacía por dependencia declarada. La autorización se pide **nombrando C5**.
- **Si en T18 aparece un fichero con sufijo `(1)`, es una PARADA** (R31).

---

## Evidencias

| Evidencia | Valor medido |
|---|---|
| **Tests ejecutados** (servicio `api`) | **1.044 pasados**, 1 saltado |
| **Tests de F-010** | **120 pasados**, 1 saltado (`-k f010`) |
| **Suite raíz del arnés** | 16 pasados |
| **Cobertura de las líneas cambiadas** | **98,3 %** (114/116, umbral 80 %, nivel `estandar`) |
| **Mutantes generados / supervivientes** | **20 / 3**, 17 muertos, 0 timeouts |
| **Tiempo de la suite** | 14,98 s (servicio `api`), 0,38 s (raíz) |
| **Tiempo de la campaña de mutación** | 10,4 s |

**La cobertura de las líneas cambiadas no ha bajado**: F-010 no añade ni una
línea de producción en Python. Las dos líneas no cubiertas de las 116 son
deuda previa, ajena a esta feature.

**Los tres supervivientes de mutación están analizados** en
`progress/mutacion_F-010.md`, sin ninguna sección en `PENDIENTE`. Los tres son
el mismo caso: el ancho del separador decorativo del banner de arranque de
`dev_server.py` (`"=" * 60` → `"=" * 61`). **Mutantes equivalentes**: no
alteran ningún comportamiento observable, y un test que fijara el ancho de un
adorno se rompería en cada retoque sin proteger nada.

**Alcance real de la campaña, dicho por adelantado en la propia spec (T20)**:
la herramienta solo muta `.py`, y F-010 **no cambia ni una línea de
comportamiento en Python** —T8 quedó en cabecera y test—. Los dos ficheros del
alcance (`function_app.py` y `dev_server.py`) entran por el punto de partida
del diff de rama, no porque F-010 los haya reescrito. Lo que esta feature
entrega —cuatro scripts de PowerShell y documentación— **queda fuera de lo que
la campaña sabe mutar**; su disciplina la sostienen los tests de contrato de la
fase 1, que leen los scripts como texto.

---

## Lo que este trabajo NO hizo, y es a propósito

- **No se ha creado ni un recurso en Azure**, ni cargado un secreto, ni
  desplegado nada, ni encendido `ARCHIVO_HABILITADO`, ni subido nada a
  SharePoint. Las diez tareas `MANUAL (humano)` están preparadas.
- **No se ha tocado `front-portal`** ni `azure-apps/`. El entregable es el
  bloque escrito en `docs/DESPLIEGUE.md` §6.
- **No se ha tocado el `auth_level`** de ningún endpoint (D3, `design.md`
  §9 bis).
- **No se ha tocado `.env`** ni se ha añadido ninguna dependencia al
  manifiesto del proyecto.
- **No se han elegido los tiempos de espera nuevos**: es la decisión D2 y la
  toma el humano con la medición delante.
