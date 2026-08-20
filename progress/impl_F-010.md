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

**Qué quedó fuera, y por qué**: las diez tareas `MANUAL (humano)` están
preparadas con su comando exacto, **no ejecutadas**. Nada más queda fuera:
**D2 se resolvió el 2026-08-20** (opción (a)) y con ella se desbloquearon y se
completaron T5 y T9.

**Qué falta para cerrar**: solo las verificaciones manuales del humano.

---

## Estado de las tareas

| Tarea | Estado | Nota |
|---|---|---|
| T1 · MANUAL | Preparada | El humano crea `posventa-usuarios` en Entra |
| T2 · MANUAL, alimenta **D2** | **MEDIDA** · **D2 resuelta** | La ejecutó el implementer a petición del líder |
| T3 | **Hecha** | `infra/00_vars_postventa.ps1` |
| T4 | **Hecha** | `infra/cargar_secretos_postventa.ps1` |
| T5 | **Hecha** · **FASE RED** | `infra/desplegar_backend.ps1`, con `ARCHIVO_HABILITADO` apagado |
| T6 | **Hecha** | `infra/desplegar_front.ps1` |
| T7 | **Hecha** | `infra/verificar_despliegue.ps1` |
| T8 | **Hecha** | Cabecera de `function_app.py` + test |
| T9 | **Hecha** | `TIMEOUT_PETICION_MS` a 40000 + test de JS |
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

**La decisión, tomada con estos números delante.** El implementer paró aquí y
**no fijó ningún valor**. El humano resolvió **D2 el 2026-08-20** por la
**opción (a)**, y lo que hay que conservar es el criterio, no las cifras:

> **Cada capa cede antes que la de fuera.** La IA abandona a los 35 s, el front
> a los 40, el proxy corta a los 45.

Ese orden es lo que hace que el usuario reciba **nuestro** error —explicado,
reintentable y que libera la plaza de la cola— en vez de un corte opaco de la
plataforma con una llamada zombi por detrás gastando cuota de IA.

Y el margen es deliberado: 35 s son **más de cinco veces** el peor caso medido
(6,5 s). Ese colchón es exactamente lo que cubre los tres matices de arriba —el
salto de región, el arranque en frío y un mal día del proveedor—, que son los
que **no se pueden medir en local**. No es un número redondo por casualidad: es
el peor caso más el riesgo que no se puede medir.

**`GRAPH_TIMEOUT_S` queda también en 35 s**, y no es una elección libre: es lo
que concreta `design.md` §5 («`IA_TIMEOUT_S` y `GRAPH_TIMEOUT_S` bajan a 35 s»).
Encaja además con el escalonado, y por la misma razón: `POST /api/archivar`
también viaja por el proxy, así que la llamada a Graph tiene que rendirse antes
de que el front aborte a los 40. Ponerla más alta que la de IA no compraría
nada —una subida a SharePoint que tarde más de 35 s no va a caber en 45— y
dejaría una petición viva escribiendo después de que el usuario haya visto un
error, que es justo lo que el escalonado evita.

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
| `infra/desplegar_backend.ps1` | Recursos, identidad, referencias y publicación | T5 |
| `infra/desplegar_front.ps1` | Entra, Static Web App y subida | T6 |
| `infra/verificar_despliegue.ps1` | Las tres comprobaciones, solo lecturas | T7 |
| `docs/DESPLIEGUE.md` | Runbook + bloque de la tarjeta del portal | T10 |
| `services/postventa-api/tests/test_f010_scripts_infra.py` | Contrato de los scripts | T3, T4, T6, T7 |
| `services/postventa-api/tests/test_f010_endpoints_protegidos.py` | R18, R32 | T8 |
| `services/postventa-api/tests/test_f010_tarjeta_portal.py` | R23, R24, R25, R34 | T10 |
| `services/postventa-api/tests/test_f010_integracion_expuesto.py` | R26 | T11 |
| `services/postventa-front/tests_js/test_config_timeout.test.js` | R19, R21, R22 | T9 |

### Modificados

| Ruta | Qué cambió | Tarea |
|---|---|---|
| `services/postventa-api/function_app.py` | **Solo la cabecera**: por qué los seis endpoints siguen anónimos y dónde está el control de acceso | T8 |
| `docs/INTEGRACION.md` | §8 rellenada + filas del despliegue en §9 | T11 |
| `docs/ARCHITECTURE.md` | §«Infra y despliegue»: recursos, regiones, 45 s y anonimidad | T12 |
| `services/postventa-front/js/config.js` | `TIMEOUT_PETICION_MS` 180000 → **40000**, con el escalonado explicado | T9 |
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
`ARCHIVO_HABILITADO` apagado se escribe **antes** que el script.

### Paso 1 · El test existe y el script no

```
$ ls ../../infra/desplegar_backend.ps1
ls: cannot access '../../infra/desplegar_backend.ps1': No such file or directory

$ python -m pytest tests/test_f010_scripts_infra.py -q -k "r33"
E       FileNotFoundError: [Errno 2] No such file or directory:
        'C:\Users\pgris\PycharmProjects\postventa-incidencias\infra\desplegar_backend.ps1'
ERROR tests/test_f010_scripts_infra.py::test_f010_r33_el_despliegue_deja_la_ventana_de_escritura_cerrada
ERROR tests/test_f010_scripts_infra.py::test_f010_r33_el_script_explica_por_que_la_ventana_nace_cerrada
93 deselected, 2 errors in 0.28s
```

**Pero eso es un rojo pobre**, y merece decirse: un fichero que falta hace
fallar cualquier test que lo lea. No demuestra que este test cace **el
descuido**, que es lo que R33 previene. Así que se dio un segundo paso.

### Paso 2 · El script completo, con el descuido real dentro

Se escribió `desplegar_backend.ps1` **entero** —grupo de recursos,
almacenamiento, Log Analytics, Application Insights, identidad, rol sobre el
Key Vault, Function App, App Settings y publicación— **omitiendo únicamente la
línea de `ARCHIVO_HABILITADO`**. Es exactamente el despliegue que alguien
escribiría sin haber leído `design.md` §9 bis: funciona, crea todo, y deja la
ventana de escritura a merced de lo que hubiera antes.

```
$ python -m pytest tests/test_f010_scripts_infra.py -q -k "r33"
>       assert "ARCHIVO_HABILITADO=false" in cuerpo
E       assert 'ARCHIVO_HABILITADO=false' in '  ...  exit 0
'
tests	est_f010_scripts_infra.py:444: AssertionError

>       assert "se apaga" in backend.lower() or "se vuelve a apagar" in backend.lower()
E       assert ('se apaga' in '# infra/desplegar_backend.ps1 ...' or ...)
tests	est_f010_scripts_infra.py:457: AssertionError

FAILED tests/test_f010_scripts_infra.py::test_f010_r33_el_despliegue_deja_la_ventana_de_escritura_cerrada
FAILED tests/test_f010_scripts_infra.py::test_f010_r33_el_script_explica_por_que_la_ventana_nace_cerrada
2 failed, 101 passed, 1 skipped in 0.15s
```

**Rojo por aserción, sobre un script que por lo demás está bien.** Ese es el
fallo que importa: el que no se ve revisando el diff, porque no hay nada malo
escrito —lo que hay es algo que falta—.

### Paso 3 · Verde

Se añadió la App Setting `ARCHIVO_HABILITADO=false` y el bloque de la cabecera
que explica por qué nace cerrada, cuándo se enciende y que **se vuelve a
apagar**:

```
$ python -m pytest tests/test_f010_scripts_infra.py -q
103 passed, 1 skipped in 0.23s
```

### Y la otra mitad del riesgo: que el test de R32 también tenga dientes

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
| **Tests ejecutados** (servicio `api`) | **1.063 pasados**, 1 saltado |
| **Tests ejecutados** (servicio `front`) | **74 pasados** en Python + **104** en `node --test` |
| **Tests de F-010** | **165 pasados**, 1 saltado (`-k "f010 or integracion"`) |
| **Suite raíz del arnés** | 16 pasados |
| **Cobertura de las líneas cambiadas** | **98,3 %** (114/116, umbral 80 %, nivel `estandar`) |
| **Mutantes generados / supervivientes** | **20 / 3**, 17 muertos, 0 timeouts |
| **Tiempo de la suite** | 12,7 s (`api`), 1,6 s (`front`), 0,4 s (raíz) |
| **Tiempo de la campaña de mutación** | 11,1 s |

**`bash harness/init.sh` termina en verde**, con las **dos** suites de servicio
ejecutadas de verdad (no por caché) y la puerta de cobertura pasada.

**La cobertura de las líneas cambiadas no ha bajado**: F-010 no añade ni una
línea de producción en Python. Las dos líneas no cubiertas de las 116 son
deuda previa, ajena a esta feature.

**Los tres supervivientes de mutación están analizados** en
`progress/mutacion_F-010.md`, sin ninguna sección en `PENDIENTE`. Los tres son
el mismo caso: el ancho del separador decorativo del banner de arranque de
`dev_server.py` (`"=" * 60` → `"=" * 61`). **Mutantes equivalentes**: no
alteran ningún comportamiento observable, y un test que fijara el ancho de un
adorno se rompería en cada retoque sin proteger nada.

La campaña se relanzó al terminar T5 y T9, como pedía el líder. **Y de paso
destapó un fallo del arnés que no es de esta feature**, contado abajo.

**Alcance real de la campaña, dicho por adelantado en la propia spec (T20)**:
la herramienta solo muta `.py`, y F-010 **no cambia ni una línea de
comportamiento en Python** —T8 quedó en cabecera y test—. Los dos ficheros del
alcance (`function_app.py` y `dev_server.py`) entran por el punto de partida
del diff de rama, no porque F-010 los haya reescrito. Lo que esta feature
entrega —cuatro scripts de PowerShell y documentación— **queda fuera de lo que
la campaña sabe mutar**; su disciplina la sostienen los tests de contrato de la
fase 1, que leen los scripts como texto.

---

---

## Hallazgo que hay que subir al humano · la campaña de mutación envenena `__pycache__`

**No es de F-010 y no lo arregla F-010**, pero se ha topado con él de frente y
le va a pasar a la siguiente feature igual.

**Qué pasa.** `python -m harness.mutacion` modifica el `.py` en el sitio y lo
restaura al terminar. Muchas mutaciones **conservan el tamaño exacto** del
fichero (`==` → `!=`, `60` → `61`) y la fecha queda dentro de la granularidad
con la que Python decide si un `.pyc` sigue siendo válido. Resultado: el
bytecode de `__pycache__` **conserva el mutante** y Python lo da por bueno.

**Cómo se manifestó aquí, y por qué cuesta reconocerlo.** Tras una campaña, el
portero se puso en rojo con esto, con el árbol de trabajo **limpio** según
`git status`:

```
usage: __main__.py [-h] [--port PORT] [--api API] [--root ROOT]
__main__.py: error: unrecognized arguments: tests/ -q
INTERNALERROR> ... SystemExit: 2
[KO] servicio front (services/postventa-front): pytest en rojo
[KO] PUERTA COBERTURA: 30.2% de 116 líneas cambiadas cubiertas
```

El mutante superviviente en la caché era `if __name__ != "__main__":`, así que
importar `dev_server.py` ejecutaba `main()` **durante la recolección de
pytest** y el `argparse` del servidor mataba la sesión entera. Comprobado
desensamblando el `.pyc`: `COMPARE_OP 55 (!=)` sobre `__name__`, con el fuente
diciendo `==`.

**La consecuencia silenciosa es peor que la ruidosa.** Con la caché sucia, dos
campañas seguidas dieron **0 supervivientes**; con `__pycache__` borrada, la
misma campaña da **3**, que es lo que dio la primera del día. El falso negativo
va en la dirección peligrosa: dice que todo está cazado cuando no lo está. Si
esto hubiera pasado en una feature de rigor `critico` —donde cero
supervivientes es criterio de cierre—, habría cerrado con un cero falso.

**Cómo se ha trabajado mientras tanto**: borrando la caché antes y después de
cada campaña.

```
find services -name "__pycache__" -type d -prune -exec rm -rf {} +
```

**Todos los números de este informe se han obtenido con la caché limpia**, y
`init.sh` se ha vuelto a ejecutar en verde después.

**Qué se propone, y quién decide.** El arreglo natural es que la campaña borre
el `__pycache__` del fichero mutado al restaurarlo (o que ejecute con
`PYTHONDONTWRITEBYTECODE=1`). Como vale **para cualquier proyecto**, la regla
de propagación de `CLAUDE.md` pide llevarlo a `arnes-base`. **Eso no lo decide
el implementer**: queda propuesto aquí y en `progress/mutacion_F-010.md`, y lo
resuelve el humano.

---

## Un test de F-007 que T9 tuvo que actualizar

`services/postventa-front/tests/test_f007_estaticos.py` comprobaba, leyendo
`config.js`, que `TIMEOUT_PETICION_MS` valía **180000**. Al bajarlo a 40000 se
puso en rojo, que es exactamente lo que tenía que hacer.

**No se ha relajado el test** —habría sido lo cómodo y lo equivocado—: se ha
cambiado el número esperado y se ha escrito al lado **por qué** cambia, que
180000 estaba **por encima** del corte de 45 s del proxy y por tanto el front
no llegaba nunca a abortar por su cuenta. Un test que fija un valor tiene que
seguir fijándolo; lo que cambia es el valor y la razón, no la vigilancia.

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
- **No se eligieron los tiempos de espera**: el implementer midió, paró y los
  fijó **después** de que el humano resolviera D2 con el dato delante.
- **No se arregló el fallo del arnés** que destapó la campaña de mutación: vale
  para cualquier proyecto, así que su sitio es `arnes-base` y su decisión es
  del humano.

---

# Ronda de correcciones tras la review (2026-08-20)

`progress/review_F-010.md` salió **CHANGES_REQUESTED** por cinco defectos
concretos en `infra/`, más tres encargos aceptados por el humano. Esto es lo
que se ha hecho, defecto a defecto. **Un commit por arreglo.**

Lo que el reviewer aprobó tal cual —D3/R32 y su control negativo, la ventana de
escritura que nace apagada, el escalonado 35/40/45 y el test de F-007
actualizado, el análisis del bytecode envenenado— **no se ha tocado**.

## Fase RED de esta ronda

Dos de los cinco defectos son **requisitos EARS incumplidos con su test en
verde** (R27 y R6), así que el arreglo empieza por el test que los daba por
buenos. Los tests se escribieron **antes** de tocar los scripts. Traza real:

```
$ cd services/postventa-api && ./.venv/Scripts/python.exe -m pytest \
    tests/test_f010_scripts_infra.py -k "guarda_de_la_ventana or veredicto_no_sale_en_verde \
    or valor_previo_se_lee_antes or key_vault or descripcion_no_afirma \
    or credenciales_se_acumulan or no_llama_a_archivar" -p no:randomly --no-header -q --tb=line

...FFFFFFFssF                                                            [100%]
================================== FAILURES ===================================
test_f010_scripts_infra.py:765: AssertionError: la escritura en el Key Vault de la linea 260 no comprueba su resultado
test_f010_scripts_infra.py:780: assert -1 < -1
test_f010_scripts_infra.py:796: assert True == False
test_f010_scripts_infra.py:809: AssertionError: assert 'no invalida' in '# infra/desplegar_front.ps1 ...'
test_f010_scripts_infra.py:876: assert 'if ($ventana -ne "false")' in '... exit $SALIDA_EN_ROJO'
test_f010_scripts_infra.py:896: AssertionError: comparar contra 'true' deja pasar 'desconocida': la guarda falla abierta
test_f010_scripts_infra.py:914: AssertionError: assert '$ventanaOk' in '$saludOk -and $archivarOk -and $frontOk'
test_f010_scripts_infra.py:1068: AssertionError: $env:SWA_CLI_DEPLOYMENT_TOKEN se asigna sin leer antes su valor previo
=========================== short test summary info ===========================
FAILED test_f010_t6_cada_escritura_en_el_key_vault_comprueba_su_resultado
FAILED test_f010_t6_no_escribe_en_el_key_vault_sin_comprobar_que_existe
FAILED test_f010_r32_la_descripcion_no_afirma_lecturas_que_no_hace
FAILED test_f010_t6_la_cabecera_declara_que_las_credenciales_se_acumulan
FAILED test_f010_t7_no_llama_a_archivar_si_la_ventana_esta_abierta
FAILED test_f010_t7_la_guarda_de_la_ventana_falla_cerrada
FAILED test_f010_t7_el_veredicto_no_sale_en_verde_con_la_ventana_desconocida
FAILED test_f010_r6_el_valor_previo_se_lee_antes_del_try_que_lo_restaura[desplegar_front.ps1]
8 failed, 3 passed, 2 skipped, 100 deselected in 0.07s
```

Ocho tests en rojo contra el código de la review. Uno de ellos
—`la_guarda_de_la_ventana_falla_cerrada`— se **refinó después** de esta traza:
su primera redacción prohibía el literal de la comparación en todo el fichero, y
eso también prohibía la comparación *interior*, la que solo elige el mensaje.
Ahora mira **la guarda de nivel superior**, la que decide la llamada. Contra el
código original seguía saliendo en rojo (encontraba `-eq "true"` donde exige
`-ne "false"`); es un cambio de precisión, no de veredicto.

Y el defecto del arnés, con su propia RED:

```
$ python -m pytest tests/test_mutacion_sin_bytecode.py -p no:randomly --no-header -q
F                                                                        [100%]
tests\test_mutacion_sin_bytecode.py:51: in test_la_suite_de_mutacion_se_lanza_sin_escribir_bytecode
    entorno = capturado["opciones"]["env"]
E   KeyError: 'env'
1 failed in 0.08s
```

## Los cinco defectos

### 1 · `verificar_despliegue.ps1` — la guarda fallaba abierta (commit `c800232`)

`Get-Ventana-De-Escritura` devuelve **tres** valores y la guarda comparaba
contra uno: `"desconocida"` —lo que devuelve la lectura cuando `az` falla— caía
en la rama que **sí** hace el POST. Ahora se compara contra `"false"`, el único
valor que demuestra que la ventana está cerrada; dentro se distingue `"true"`
de `"desconocida"` solo para dar un mensaje u otro, con el diagnóstico de qué
mirar (sesión, suscripción, nombre del recurso).

Y el veredicto final gana `$ventanaOk`: **no puede salir en verde con la
ventana en estado desconocido**. Antes eso ya lo tapaba de rebote
`$archivarOk = $false`, pero por accidente y no por decisión; ahora está
escrito y hay un test que lo sujeta.

El `.DESCRIPTION` se actualizó en el mismo commit: prometía una guarda que no
era la que había.

### 2 · `desplegar_front.ps1` — el Key Vault sin comprobar (commit `2818d66`)

Las dos escrituras de secreto iban sin mirar `$LASTEXITCODE`; el `if` guardaba
solo la tercera llamada. Ahora cada una mira el suyo, con un mensaje que dice
qué permiso falta, y el de `swa-client-secret` avisa además de que el secreto
**acaba de generarse y no ha quedado guardado**.

Se añade también la guarda previa de existencia del vault que ya tenía
`desplegar_backend.ps1`, con código de salida propio `$SALIDA_SIN_KEYVAULT = 9`,
y su línea en el resumen de «qué se va a hacer».

### 3 · `desplegar_front.ps1` — `-WhatIf` borraba el token (commit `823e8e3`)

`$tokenPrevio` nacía a `$null` y solo recibía valor a mitad del `try`. Como
`exit` dentro de un `try` ejecuta el `finally`, **cualquier** salida temprana
—`-WhatIf`, confirmación denegada, cualquier `Salir-Con`— restauraba `$null`,
y eso **borra** la variable de entorno. Un script que promete no tocar nada se
llevaba por delante el `SWA_CLI_DEPLOYMENT_TOKEN` del operador.

Arreglo: leer el valor previo **antes** del `try`. Así restaurar es siempre
devolver el valor de verdad, se salga por donde se salga.

El test de R6 pasaba porque comprobaba que hubiera restauración en un
`finally`, no que la restauración fuera **correcta**. El hueco lo cierra
`test_f010_r6_el_valor_previo_se_lee_antes_del_try_que_lo_restaura`, que exige
que la lectura del previo esté por delante del `try` y se aplica a **todos** los
scripts que escriben, no solo a este.

### 4 y 5 · La cabecera que mentía y el secreto que se acumula (commit `df9c9cc`)

- **4**: el `.DESCRIPTION` decía que con `-SoloFront` «se leen del Key Vault los
  que ya hay». No hay una sola lectura de secreto en el fichero. Ahora dice lo
  que pasa de verdad —el bloque se salta entero y las App Settings se quedan
  como estén— y **lo que eso implica**: `-SoloFront` **no** repara unas App
  Settings borradas a mano; para eso hay que volver en modo completo.
  `test_f010_r32_la_descripcion_no_afirma_lecturas_que_no_hace` ata las dos
  mitades: si el texto afirma que lee, el código tiene que leer.
- **5**: `--append` no revoca la credencial anterior. Se mantiene —es lo que
  evita repetir el incidente del portal—, pero ahora la cabecera lo dice, con
  el comando exacto para retirar las viejas y la advertencia de no borrar la
  última, y el resumen final imprime **cuántas credenciales `swa` vivas hay**,
  avisando en amarillo en cuanto pasan de una.

## Los tres encargos

### El arnés (commit `613e9a3`) y su porte a `arnes-base`

`harness/mutacion.py`, `EjecutorPytest.ejecutar`, ahora lanza el subproceso con
`env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}`, con el comentario que
explica por qué: el `.pyc` compilado desde el código mutado sobrevive a la
restauración del `.py` porque CPython valida la caché por (tamaño, mtime) y la
restauración deja los dos iguales.

`tests/test_mutacion_sin_bytecode.py` vigila **las dos mitades**: la variable, y
que se herede `os.environ`. Sin lo segundo el subproceso pierde `PATH` y
`VIRTUAL_ENV`, todos los mutantes «mueren» por fallo de importación y sale una
campaña que mata el 100 % sin haber comprobado nada.

**Portado a `arnes-base` en el mismo trabajo** (regla de propagación), sellado
allí como **1.6.3** sobre la 1.6.2 que ya existía: commits `c73b040` y `f1b250e`
de ese repositorio, con su sección en `GUIA_INSTALACION.md`.

> **Punto para el humano.** `harness/VERSION` de este repositorio **sigue
> diciendo `1.5.2`, y es deliberado.** Aquí se ha aplicado *el parche* de la
> 1.6.3, no la rama 1.6 entera: las **1.6.0, 1.6.1 y 1.6.2 están pendientes**, y
> la 1.6.0 no es un parche —rehace `mutacion.py` completo (línea base de la
> suite, veredicto «base rota», mutación de `is`/`is not`) y sus números **no
> son comparables** con los de antes—. Poner `1.6.3` en el sello daría a
> entender que ese trabajo está hecho. `harness/ARNES_VERSION.md` lo explica
> y deja la actualización como decisión suya. **La marca de adaptación entre
> corchetes no se ha escrito en ese fichero** (comprobado: 0 apariciones), para
> no dejar al portero un aviso falso permanente.

### La regla nueva de `CHECKPOINTS.md` (commits `613e9a3` y `054dc74`)

C4 bis gana el punto del **coste por mutante**. Y aquí hay que contar algo,
porque la primera redacción estaba mal:

Escrita como pedía el encargo —«Tiempo total» entre número de mutantes, menos
de un segundo es sospechoso—, la probé contra la campaña real que acababa de
reejecutar: **20 mutantes, 14,1 s, 0,7 s por mutante**. La marcaba como
sospechosa. Y es una campaña sana. El motivo es que **la campaña es paralela
por defecto** y su «Tiempo total» es tiempo de **reloj**, no de CPU.

La regla quedó, por tanto, así:

> coste por mutante = «Tiempo total» × nº de workers ÷ nº de mutantes

Con esta campaña: 14,1 × 16 / 20 ≈ **11 s por mutante**, coherente con lo que
tarda la suite del servicio. Y «Evidencias» pasa a exigir **el nº de workers**,
sin el cual la cuenta no se puede hacer. Corregido también en `arnes-base`.

Lo digo explícitamente porque una regla que marca en rojo el caso sano no
sobrevive: se desactiva sola a la tercera vez que salta, y así es como se
pierde un control.

### Los 16 worktrees huérfanos

Retirados los 16 de `mutacion_F-005_zllkg8wf`, y el directorio raíz con ellos.
**Comprobado antes, uno a uno**, que no llevaban trabajo sin guardar:

- 12 estaban limpios; **4** tenían modificaciones (`wk_0`, `wk_1`, `wk_6`,
  `wk_15`), y las cuatro son **mutantes abandonados**, no trabajo humano:
  `auto_cierre=False` a `True`, `group(1)` a `group(2)`, un `*` convertido en
  `//`, y un `if not filas` convertido en `if filas`.
- **0 ficheros no versionados** y **0 commits propios** por encima de `48fb104`
  en los dieciséis.

`git worktree list` queda solo con el árbol principal y los dos worktrees de
agente, que no son de esta limpieza. Se retiró también el directorio vacío
`mutacion_F-005_8q6g52nk`, que ya no estaba registrado en git.

## Un commit que no es un arreglo

`b8b3128` versiona `progress/review_F-010.md`, que estaba sin añadir. Los ocho
informes de review anteriores sí lo están, y además un árbol sucio **impide**
lanzar la campaña de mutación en paralelo, que era justo lo que había que
reejecutar.

## Verificación

`bash harness/init.sh`, tal cual, **en verde con las dos suites**:

```
[OK] Arnés v1.5.2 (2026-08-18)
[OK] features.json válido      20 features, 13 abiertas, en curso: ['F-010']
[OK] compileall: sin errores de sintaxis
[AVISO] ruff: 56 avisos (deuda previa, no bloquea)
[OK] pytest en verde (con medición de cobertura)        17 passed
[OK] servicio api (services/postventa-api): pytest en verde     1070 passed, 13 skipped in 24.82s
[OK] servicio front (services/postventa-front): pytest en verde (caché: árbol sin cambios)
[OK] PUERTA COBERTURA: 98.3% de 116 líneas cambiadas cubiertas (114/116, umbral 80%, nivel estandar)
[OK] Rama actual: feature/F-010-despliegue
ENTORNO LISTO. Puedes trabajar.
```

Campaña de mutación **relanzada con la caché limpia** (`__pycache__`,
`.pytest_cache` y `.pyc` borrados antes de arrancar), porque se tocó código
Python de producción del alcance:

```
20 mutantes evaluados, 17 muertos, 3 supervivientes, 0 timeouts en 14.1 s
```

**Mismos totales que la campaña anterior** (20 / 17 / 3). Es la confirmación
independiente de lo que el reviewer ya concluyó: aquellos números **no estaban
falseados** por el bytecode envenenado.

Los tres supervivientes son el mismo mutante repetido en tres líneas —el ancho
del separador decorativo del banner de `dev_server.py`— y los tres tienen su
análisis **completado** en `progress/mutacion_F-010.md`: **mutantes
equivalentes**, ningún comportamiento observable cambia y el fichero ni siquiera
se despliega. Ninguna sección queda en `PENDIENTE`.

`harness/mutacion.py` entra en el alcance con 10 líneas pero **genera 0
mutantes**: el cambio es un literal de diccionario y comentarios, sin ningún
operador que el mutador sepa sustituir.

## Evidencias · ronda de correcciones

| Evidencia | Valor |
|---|---|
| Tests ejecutados y resultado | **1087 pasan**, 13 saltados, 0 fallos (17 arnés + 1070 api; front por caché de árbol limpio) |
| Tests nuevos de esta ronda | **7** (6 en `test_f010_scripts_infra.py`, 1 en `tests/test_mutacion_sin_bytecode.py`), más 2 corregidos |
| Cobertura de las líneas cambiadas | **98,3 %** — 114/116, umbral 80 %, nivel `estandar` (línea `PUERTA COBERTURA`) |
| Mutantes generados / supervivientes | **20 / 3**, 17 muertos, 0 timeouts — los 3 analizados y cerrados como equivalentes |
| Workers de la campaña | **16** (paralela, por defecto) |
| Coste por mutante | 14,1 s × 16 / 20 ≈ **11 s**, coherente con la suite: la regla nueva no salta |
| Tiempo de ejecución de la suite | **24,8 s** (`api`), 0,45 s (arnés), 14,1 s la campaña de mutación |

Los cinco scripts corregidos son **PowerShell**: no entran ni en la cobertura
de líneas cambiadas ni en la campaña de mutación, que el arnés solo mide sobre
Python. Lo que los sujeta son los **113 tests** de
`services/postventa-api/tests/test_f010_scripts_infra.py`, que los leen como
texto; por eso cada defecto se arregló **empezando por su test**.

## Lo que esta ronda NO hizo

- **Ni una tarea `MANUAL (humano)`**: cero recursos en Azure, cero despliegues,
  `ARCHIVO_HABILITADO` sin tocar, nada subido a SharePoint. Las nueve siguen
  preparadas y pendientes, con el orden y las condiciones que fijó el reviewer
  (T14 bis antes de T16; T18 con autorización expresa nombrando C5; cerrar la
  ventana después de T18; T19 en `front-portal`).
- **Ningún `git push` ni PR**, ni aquí ni en `arnes-base`. Solo commits locales.
- **Ni un identificador real** entra en el repositorio.
- **No se actualizó el arnés a la 1.6.x**: decisión del humano, con el motivo
  escrito arriba.
- **No se tocó `harness/VERSION`**, por lo mismo.
- **No se tocaron los dos worktrees `.claude/worktrees/agent-*`**: no son de
  esta limpieza.

## Veredicto de la review — APROBADO el 2026-08-20

**Segunda pasada APROBADA** (`progress/review_F-010.md`); la primera fue
CHANGES_REQUESTED por cinco defectos de los scripts de `infra/`, los cinco
corregidos en esta rama.

**F-010 queda aprobada a la espera de que el humano ejecute sus nueve tareas
`MANUAL (humano)`.** No se marca `done` hasta entonces: el reviewer verificó lo
que le corresponde —que estén preparadas con su comando exacto, que ninguna se
haya ejecutado por su cuenta y que lo entregado sea correcto— y las tres cosas
se cumplen.

### Lo que la review dejó cerrado, y conviene no reabrir

- **El bytecode envenenado no invalida F-005 ni F-006.** Demostrado con
  evidencia en disco: quedaban 16 worktrees huérfanos de la campaña de F-005,
  prueba de que se ejecutó en paralelo con una caché por worker. Y el número
  que lo cierra es el **coste por mutante**: ~50 s en F-005, ≥14 s en F-006, y
  **0,55 s en F-010**, la primera campaña del repositorio que muta un fichero
  del `front`, cuya suite tarda 1,4 s. Las del `api` están dos órdenes de
  magnitud por encima del umbral donde el fallo aparece.
- **Corrección de un dato que el líder dio mal al encargar la review**: F-006
  **no** cerró con cero supervivientes, sino con **cinco justificados y
  aceptados**. El único cero era el de F-005, y para F-005 la respuesta es que
  el cero era bueno.
- **Por qué el fallo era peligroso**: con la caché envenenada, si un mutante
  rompe la recolección de pytest, **todos los siguientes ven la suite en rojo y
  se anotan como muertos**. El error va en la dirección que tranquiliza.

### El desfase del arnés: 1.5.2 aquí, 1.6.3 en `arnes-base`

El líder preguntó si eso era un defecto a corregir dentro de F-010. **El
reviewer dice que no, y con razón**: `harness/ARNES_VERSION.md` **no finge
nada**. Declara que este repositorio no lleva la 1.6.x completa, que
`harness/VERSION` sigue en `1.5.2` **a propósito**, que de la rama 1.6 se ha
traído **solo** el parche de la 1.6.3, y por qué las demás esperan: **la 1.6.0
rehace `harness/mutacion.py` entero** y sus números no son comparables con los
de antes.

Sellar `VERSION=1.6.3` sería **mentir**, que es el mismo pecado corregido en la
cabecera de `desplegar_front.ps1`. Y traerse la 1.6.x entera dentro de F-010
sería peor: metería un motor de mutación reescrito y sin revisar en mitad de
una review de despliegue, invalidando las campañas recién verificadas. Es el
LÍMITE DE SERVICIO del `CLAUDE.md`.

**Queda como trabajo aparte, y el reviewer recomienda que sea el siguiente.**
El argumento es medido y con fecha: en `arnes-base` hay un encargo del
**2026-08-19**, escrito desde `datamart-seg-anual`, que describe **este mismo
defecto del bytecode** y lo arregló allí como 1.6.0. **Hemos gastado una review
entera redescubriendo un fallo ya resuelto río arriba.** Ese es el coste real
del desfase.
