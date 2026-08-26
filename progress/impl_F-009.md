<!-- progress/impl_F-009.md -->
# F-009 · Cierre de la incidencia en Sigrid — informe de implementación

> Rama `feature/F-009-cierre-sigrid`. Rigor `critico`.
>
> **Alcance ejecutado: bloques 1 a 7 (T1–T21).** El **bloque 8 (T22–T27) no se
> ha tocado**: es verificación contra el ERP de producción y le corresponde al
> humano, desde el entorno desplegado. Del bloque 9 se ha hecho lo que le toca
> al implementer: la campaña de mutación y `init.sh` en verde.

## 1 · Qué hace ahora el sistema, en una frase

`POST /api/cerrar` lee la reclamación en Sigrid y devuelve **qué pasaría**; y
solo si se le pide `commit` **y** alguien lo ha confirmado, mueve `con.est` al
estado de cierre y escribe la fila de auditoría en `dbo.log`, las dos en un
solo batch transaccional con tope de dos filas afectadas. Desde un puesto de
trabajo responde **503 sin tocar el ERP**, y en el entorno desplegado la
ventana de escritura se despliega **apagada**.

**Nada de esto se ha ejecutado nunca contra el ERP real.** Lo que hay es código
probado con dobles y el circuito montado; el primer cierre de verdad es T24 y
lo hace el humano.

## 2 · Ficheros tocados

### Creados — backend (`services/postventa-api/`)

| Ruta | Qué es |
|---|---|
| `domain/models/cierre.py` | El vocabulario y la única función que **decide**: `evaluar`. Dominio puro |
| `domain/ports/erp.py` | El puerto del ERP: leer la reclamación, verificar un login, cerrar |
| `domain/ports/usuarios_sigrid.py` | El puerto de las correspondencias `oid` → login |
| `infrastructure/sigrid/__init__.py` | El único paquete que conoce la pasarela |
| `infrastructure/sigrid/consultas.py` | Constructores **puros** del SQL de lectura y el mapeo de la fila |
| `infrastructure/sigrid/escrituras.py` | Constructor **puro** del batch de escritura |
| `infrastructure/sigrid/cliente.py` | `AdaptadorSigridApi`: `httpx`, `tenacity` y las dos puertas |
| `infrastructure/sigrid/fabrica.py` | `construir_erp`: entorno → interruptor → configuración → huso |
| `infrastructure/persistencia/sql/08_usuarios_sigrid.sql` | La tabla del mapeo, en el esquema propio |
| `application/pipelines/paso_cierre.py` | El paso 7 del pipeline y la resolución del login |
| `interface_adapters/api/cerrar.py` | El handler de `POST /api/cerrar` |

### Creados — front, infra y suites

| Ruta | Qué es |
|---|---|
| `infra/07_alta_usuario_sigrid.ps1` | Alta manual de una correspondencia (R34) |
| `services/postventa-front/tests_js/cierre.test.js` | `esCerrable` y `cuerpoDeCierre` |
| `services/postventa-front/tests/test_f009_front.py` | Lo que la pantalla tiene que enseñar |
| 15 ficheros `tests/test_f009_*.py` + `tests/utiles_sigrid.py` | La suite del backend |

### Modificados

| Ruta | Qué cambia |
|---|---|
| `config/settings.py` | Bloque de ocho variables de F-009, todas opcionales en el modelo |
| `function_app.py` | La ruta `cerrar` y la traducción de sus errores a 400/409/500/502/503 |
| `domain/models/errores.py` | Doce errores nuevos, repartidos por el código HTTP que les toca |
| `infrastructure/persistencia/{sentencias,mapeo,repositorio_pg}.py` | `select_login_sigrid`, `upsert_login_sigrid`, `fila_a_correspondencia` |
| `application/pipelines/contexto_parte.py` | El campo `cierre` |
| `.env.example`, `local.settings.json.example` | Las ocho variables, con placeholders |
| `services/postventa-front/js/{api,pipeline,confirmacion,app}.js`, `index.html` | El paso de cierre y la identidad |
| `docs/{ARCHITECTURE,INTEGRACION,DESPLIEGUE}.md` | T19 y T20 |
| `azure-apps/postventa_incidencias.md` | T21. **Otro repositorio**: commit local `3c1c588`, **sin push** |
| `tests/conftest.py` y varios `test_f0XX_*` previos | Guardianes que se enteraron solos (§5) |

`domain/models/persistencia.py` **no se ha tocado**: `TrazaCierre`,
`EstadoCierre` y las tablas `06_cierres.sql` / `07_preferencias.sql` ya estaban
construidas por F-005 para esta feature, tal y como anunciaba `design.md` §5.

## 3 · Las decisiones de diseño que hay que revisar

### 3.1 · Lo que se implementó tal cual dice la spec

Las dos sentencias de `design.md` §7.3 están carácter a carácter, incluida la
subconsulta escalar del `ide` con `UPDLOCK, HOLDLOCK` y el `FROM dbo.con`
filtrado por el estado destino. Ese detalle tiene test propio y su explicación:
con un `WHERE EXISTS`, el agregado sin `GROUP BY` devolvería una fila aunque no
case nada y `ISNULL(MAX(ide),0)+1` valdría **1** — colisión garantizada contra
la fila más antigua de la tabla.

### 3.2 · Desviaciones respecto a la spec, y por qué

| Qué | Spec | Qué se hizo | Por qué |
|---|---|---|---|
| `SinGraficoEnSigrid` | `design.md` §4 lo lista entre los errores nuevos | **No se ha creado** | D5 (§10) lo deja sin ningún caso que lo levante: R20 prohíbe consultar el gráfico. Un error que nadie puede levantar es código muerto en una feature `critico`, y además arrastraría la palabra a un módulo que un control negativo vigila |
| `ParteNoArchivado`, `EstadoDeCierreNoResoluble` | No están en §4 | **Añadidos** | R17 y R2 no tenían error asignado. Reusar `ParteNoApto` para R17 daría un mensaje que manda a revalidar cuando lo que falta es archivar |
| `CierreSinTraza` | No está en §4 | **Añadido** (§3.3.c) | Sin él, el borde miente sobre el estado del ERP |
| `evaluar(reclamacion)` | §6 | `evaluar(reclamacion, *, login_sigrid)` | `PlanDeCierre` lleva el login —lo dice la propia §6— y el dominio no puede resolverlo |
| `PlanDeCierre` | §6 no lista `ya_cerrada` | **Campo añadido** | §6 dice que `evaluar` decide `ya_cerrada`; sin campo no hay dónde ponerlo, y R18 exige distinguirlo de un error |
| `paso_cierre(...)` | §6: `commit, usuario_oid, correo, ahora` | + `preferencias`, `confirmado`, `numero_incidencia` | R12–R14 exigen la preferencia y la confirmación, y R6 el código de la incidencia. La firma de §6 no puede expresarlos |
| Orden de T8 y T9 | `tasks.md` los lista T8 → T9 | **Commiteados T9 → T8** | La fábrica lee `Ajustes`, así que el bloque de configuración tenía que existir antes. Es una dependencia real |

### 3.3 · Tres decisiones que la spec no cubría

**a) El huso horario de la fila de auditoría.** `design.md` §7.3 dice
«`fec`/`hor` con la fecha y la hora del cierre» y **no dice en qué huso**. F-008
midió el cierre de ejemplo a las **11:46:33 del reloj de la casa**. Escribiendo
UTC, cada fila de log nuestra aparecería con dos horas menos que todas las demás
del ERP y **nadie lo notaría hasta el día en que hiciera falta reconstruir
cuándo se cerró una incidencia**. Se convierte a la zona configurada
(`SIGRID_ZONA_HORARIA`, `Europe/Madrid` por defecto) **en el adaptador**, que es
la única pieza que conoce la configuración; `escrituras.py` sigue siendo puro. Si
el huso no se resuelve, la fábrica **falla** en vez de suponer UTC.

> No añade dependencia al manifiesto: `zoneinfo` es de la biblioteca estándar y
> `tzdata` ya está en el entorno como dependencia transitiva de `psycopg`.
> **Es lo primero que hay que mirar en T24, paso 7.**

**b) De dónde sale la identidad de quien confirma.** F-019 decidió (su D3) no
guardar el `usuario_oid` en las remesas porque `x-ms-client-principal` va sin
firmar. F-009 **sí lo necesita** (R41, R43). No es una contradicción, y está
escrito en la cabecera de `cerrar.py`: quien mintiera sobre su `oid` **no
conseguiría firmar como otro**, porque el login no sale del cuerpo — sale de la
correspondencia guardada o de un candidato **que el ERP tiene que confirmar**.
En el front, el `oid` se saca de los **claims** y no del `userId` de la Static
Web App: son cosas distintas, y confundirlas haría que una persona perdiera su
login mapeado el día que la SWA cambiara el suyo.

**c) Qué pasa si el ERP se escribe y la traza local no.** No está en la spec, y
sin nombre propio ese caso sale como el `PersistenciaNoDisponible` de la base →
**503 «no se ha cerrado nada, reintenta»**, con la incidencia **ya cerrada en
producción**. Es el **defecto 14 de F-010**, el mismo que en el archivo produjo
`ArchivoSinTraza`, aplicado donde más caro sale. Se añadió `CierreSinTraza` →
**500**, con dos tests que lo separan del caso contrario (un fallo de la base
**antes** de tocar el ERP sigue saliendo como 503).

## 4 · Fase RED (rigor `critico`)

Las trazas son reales, pegadas de la salida de `pytest`.

### T3 · el control negativo de R3, con un literal inyectado a propósito

Es la RED que de verdad importa: las demás son «el módulo no existe». Aquí el
módulo existía y estaba limpio, así que se **ensució a propósito** añadiendo a
`domain/models/cierre.py`:

```python
EST_CERRADA = 9
SQL_CIERRE = "UPDATE dbo.con SET est = 9 WHERE ide = ?"
```

Comando: `python -m pytest tests/test_f009_estado_no_hardcodeado.py -q --tb=short`

```
.FF...........                                                           [100%]
================================== FAILURES ===================================
_______ test_f009_r3_ningun_sql_de_produccion_compara_est_con_un_numero _______
tests\test_f009_estado_no_hardcodeado.py:170: in test_f009_r3_ningun_sql_de_produccion_compara_est_con_un_numero
    assert hallazgos == {}
E   AssertionError: assert {'domain/mode...: ['est = 9']} == {}
E     Left contains 1 more item:
E     {'domain/models/cierre.py': ['est = 9']}
_____ test_f009_r3_ninguna_constante_de_estado_de_produccion_es_un_numero _____
tests\test_f009_estado_no_hardcodeado.py:188: in test_f009_r3_ninguna_constante_de_estado_de_produccion_es_un_numero
    assert hallazgos == {}
E   AssertionError: assert {'domain/mode...EST_CERRADA']} == {}
E     Left contains 1 more item:
E     {'domain/models/cierre.py': ['EST_CERRADA']}
=========================== short test summary info ===========================
2 failed, 12 passed in 0.90s
```

Retirado el literal: `14 passed in 1.18s`.

### T1 · el dominio

`python -m pytest tests/test_f009_dominio_cierre.py -q --tb=short`

```
ImportError while importing test module 'tests\test_f009_dominio_cierre.py'.
tests\test_f009_dominio_cierre.py:31: in <module>
    from domain.models.cierre import (
E   ModuleNotFoundError: No module named 'domain.models.cierre'
```

**Y una segunda RED, esta no prevista**, que es la que justifica el control
negativo de R20: escrito ya el módulo, el barrido saltó **contra mi propia
prosa**, porque el docstring nombraba las dos tablas de gráficos.

```
_________ test_f009_r20_el_dominio_no_menciona_las_tablas_de_graficos _________
tests\test_f009_dominio_cierre.py:225: in test_f009_r20_el_dominio_no_menciona_las_tablas_de_graficos
    assert PATRON_TABLAS_DE_GRAFICOS.findall(texto) == []
E   AssertionError: assert ['rcg', 'gra'] == []
1 failed, 26 passed in 0.66s
```

Se arregló **el módulo**, no el test.

### T2 · los puertos

`python -m pytest tests/test_f009_arquitectura.py -q --tb=line`

```
E   AssertionError: falta el puerto erp.py
E   AssertionError: falta el puerto usuarios_sigrid.py
2 failed, 2 passed, 1 skipped in 2.10s
```

### T4, T5, T7, T8 · el SQL, el adaptador y la fábrica

```
E   ModuleNotFoundError: No module named 'infrastructure.sigrid'                (T4)
E   ModuleNotFoundError: No module named 'infrastructure.sigrid.escrituras'     (T5)
E   ModuleNotFoundError: No module named 'infrastructure.sigrid.cliente'        (T7)
E   ModuleNotFoundError: No module named 'infrastructure.sigrid.fabrica'        (T8)
```

Y en T4, una RED intermedia real: el aborto de R2 no nombraba el código que no
se había podido resolver.

```
E   AssertionError: assert 'CER' in 'el maestro de estados no resuelve el código
    de cierre para la reclamación RS26.08/0123: sin él no se cierra…'
1 failed, 24 passed in 0.33s
```

### T11, T13, T16 · el mapeo de usuarios, el paso y el borde

```
E   ModuleNotFoundError: No module named 'application.pipelines.paso_cierre'    (T11)
E   ImportError: cannot import name 'paso_cierre' from '…paso_cierre'           (T13)
E   ModuleNotFoundError: No module named 'interface_adapters.api.cerrar'        (T16)
```

En T16, además, una RED que cazó **un defecto del propio test**: el caso de R47
que manda `None` como cuerpo recibía el cuerpo válido por defecto del helper y
pasaba sin comprobar nada.

```
_________ test_f009_r47_un_cuerpo_que_no_es_un_objeto_json_se_rechaza _________
E   Failed: DID NOT RAISE CuerpoDeCierreInvalido
1 failed, 27 passed in 2.65s
```

Se arregló con un centinela `_SIN_CUERPO`, que distingue «el test no pasó
cuerpo» de «pasó `None`».

## 5 · Los guardianes previos que se enteraron solos

**Es lo mejor que ha pasado en esta feature.** Nueve tests escritos por features
anteriores fallaron **antes** de que nadie los mirase, y cada uno obligó a
justificar por escrito lo que F-009 cambiaba.

| Guardián | Qué dijo | Qué se hizo |
|---|---|---|
| `test_f005_r31_solo_el_adaptador_de_persistencia_escribe_sql` | Hay SQL fuera de `infrastructure/persistencia` | Se **amplió** a dos paquetes, uno por base de datos, con el motivo dentro del fichero. Lo que sigue prohibiendo —un `INSERT` suelto en un paso— no cambia |
| El mismo, dos veces más | La prosa del dominio nombraba verbos SQL | Se **reescribió la prosa**, no el guardián: el dominio habla de filas, no de sentencias |
| `test_f006_r22_solo_infrastructure_sharepoint_importa_graph` | Hay `httpx` en un paquete nuevo | Íd.: dos paquetes, uno por sistema externo |
| `test_f003_r7_…_no_trae_veredicto_ni_firma_ni_rutas` | `ContextoParte` tiene un campo más | Se declaró `cierre` en la lista, que es exactamente para lo que existe esa línea |
| `test_f005_r38_ningun_dni_real_…` | Mi test usaba un DNI inventado propio | Se cambió al **marcador declarado del proyecto**, en vez de ampliar su lista |
| `test_f005_r1_se_aplican_los_siete_ficheros_en_orden` | Hay un octavo `.sql` | Declarado, y renombrado el test: la lista escrita a mano es el punto |
| `test_f010_r32_…_son_nueve_endpoints` | La cuenta no cuadra | Diez, con el porqué escrito |
| `test_f019_r32_la_seccion_ocho_ya_habla_de_nueve_endpoints` | Íd. en la documentación | Íd. |
| `test_f010_r26_…_lo_que_no_esta_desplegado` | §8 dice que falta F-009 | Se reescribió la fila **sin mentir**: el cierre existe, pero su ventana se despliega apagada y no se ha ejecutado ni uno real. Y entra F-012 |
| `test_f007 R27: son nueve` (`node --test`) | Íd. en el cliente del front | Diez, y `identidad` declarada como auxiliar porque **no es un endpoint de este backend** |

**Ninguno se relajó.** Los dos que ampliaron su ámbito lo hicieron con el motivo
dentro del propio fichero, y siguen prohibiendo exactamente lo que prohibían.

## 6 · Lo que queda pendiente

### 6.1 · Bloque 8 · verificación contra el ERP de producción (T22–T27)

**MANUAL (humano). Ni una casilla marcada.** Se ejecuta desde el entorno
desplegado y con autorización expresa para la incidencia concreta. El
procedimiento está en `tasks.md`; lo que **no** está allí y hace falta saber
antes de empezar:

1. **Para el dry-run también hay que abrir la ventana.** Con
   `CIERRE_HABILITADO` apagado, la fábrica **se niega antes de leer**, así que
   ni el dry-run de T22 funciona con ella cerrada. Es consecuencia de la doble
   puerta y conviene saberlo antes de estar delante del ERP; hay que abrirla y
   **cerrarla al terminar**, igual que para el cierre.
2. **T24, paso 7: mirar la hora** de la fila de `dbo.log`. Es la decisión
   §3.3.a de este informe, y es la única que no se pudo tomar con un dato.
3. **T26** avisa de que si `SqlWriteGuard` rechazara la sugerencia de tabla
   `WITH (UPDLOCK, HOLDLOCK)`, hay que anotarlo y **no improvisar**: la feature
   se marca `blocked` y se para.

### 6.2 · Lo que este trabajo NO ha comprobado, y no puede

- Que el batch sea **de verdad** transaccional en la pasarela (R22, R26).
- Que la reserva del `ide` aguante bajo concurrencia real.
- Que el `tex` propio se pueda filtrar en el ERP (R25).
- Que los logins existan en `dbo.usu`, y la siembra de la primera
  correspondencia (R30, R31, R33).

Los cuatro los declara la propia `requirements.md` como `MANUAL (humano)`.

### 6.3 · Una propuesta para el humano, que no se ha hecho

`azure-apps/sigrid_api.md` §10 lista **quién consume la pasarela**, «para
dimensionar el impacto de cualquier cambio». `postventa-incidencias` **no está
en esa lista**, y desde F-009 no solo la consume: es **el primer escritor
genérico** por `sql/write` de todo el ecosistema. Añadir la fila sería editar el
documento de otro proyecto, y `CLAUDE.md` dice que el dueño de cada documento es
el proyecto que describe — así que **no se ha tocado**. Se propone que el humano
lo lleve al dueño de `sigrid-api`.

## 7 · Evidencias

### 7.1 · Los números

| Evidencia | Valor medido |
|---|---|
| **Tests ejecutados** — suite del backend | **1.594 pasados, 13 saltados** |
| **Tests ejecutados** — suite del front | **105 pasados** (incluye `node --test` de los 9 ficheros `tests_js/`) |
| **Tests ejecutados** — suite de la raíz (arnés) | **17 pasados** |
| De ellos, **de F-009**: backend | **348** en 16 ficheros `test_f009_*.py` |
| De ellos, **de F-009**: front | **18** (`test_f009_front.py`) + **76** en `node --test` (13 de `cierre`, 45 de `api`, 18 de `confirmacion`) |
| **Cobertura de las líneas cambiadas** | **94,1 %** (528/561), umbral 80 %, nivel `critico` |
| **Mutantes generados / evaluados** | **124 / 124**, 0 timeouts |
| **Muertos / supervivientes** | **98 / 26** |
| **Tiempo de la campaña de mutación** | **2.588 s** (6 workers, timeout 400 s/mutante) |
| **Tiempo de la suite** | backend ~85 s, front ~8 s, raíz ~2 s |

> **La cobertura es la del último `bash harness/init.sh` completo** y se midió
> antes de los últimos commits de tests, que solo pueden subirla. El número
> definitivo lo da el `init.sh` de §7.3.

### 7.2 · Los 26 supervivientes, uno a uno

**El informe está en `progress/mutacion_F-009.md`**, y la campaña se ejecutó
contra el commit **`42438f6`**. Los 26 están analizados y **25 tienen ya su
test escrito** en commits posteriores a la campaña; el 26.º es un mutante
equivalente justificado.

**Lo que falta, y lo digo yo antes de que lo pregunte nadie: la campaña de
confirmación no se ha vuelto a lanzar.** Los tests están escritos y en verde,
pero **el cero de supervivientes no está demostrado con una campaña**, solo
razonado. Volver a lanzarla son otros ~43 minutos y es lo que cierra **T28**,
que es del bloque 9 y no de este encargo.

| # | Superviviente | Por qué ningún test lo cazaba | Decisión |
|---|---|---|---|
| 1–4, 8 | `@dataclass(frozen=True)` → `False` en los cinco modelos de `cierre.py` | Nada comprobaba la inmutabilidad, y **no es decoración**: entre leer la reclamación y escribir hay varias llamadas, y si alguien pudiera reescribir el estado de origen por el camino el control optimista de R11 dejaría de proteger nada | **Test nuevo** (`3e32681`) |
| 5, 6 | `or 'desconocido'` / `or 'sin descripción'` → `and` en el motivo de R19 | El test del estado ilegible solo miraba que hubiera motivo, no **qué** decía. Con la mutación diría «el estado «»», y quien lo lea no sabría si el problema es la reclamación o la consulta | **Test nuevo** (`b85ce26`) |
| 7 | `split("@", 1)` → `split("@", 2)` en la derivación del login | **Equivalente**: `[0]` es el mismo trozo con cualquier `maxsplit ≥ 1` | **Eliminado**: se cambió a `partition("@")[0]`, que dice lo que se quiere sin un número que explicar. Un mutante equivalente menos es mejor que un mutante equivalente justificado |
| 9–17 | Los nueve códigos HTTP de la ruta `cerrar` en `function_app.py` | **El hallazgo más serio de la campaña.** Ningún test recorría la ruta: los de F-009 llamaban al handler, que levanta errores de dominio. Cambiar un 502 por un 503 no rompía nada — **y los códigos son el requisito** (R48 = 409, R49 = 503, R50 = 502): confundirlos lleva a acciones opuestas | **Fichero de tests nuevo** (`2747aa6`), con los ocho errores del 409 recorridos uno a uno |
| 18 | `trust_env=True` → `False` en el cliente HTTP | Nadie lo comprobaba. Con `False`, el servicio desplegado no sale a la pasarela por el proxy corporativo y el fallo aparece como un tiempo agotado que no dice nada | **Test nuevo** (`b85ce26`) |
| 19 | `reraise=True` → `False` en los reintentos de lectura | Nada ejercitaba el **agotamiento** de reintentos. Sin `reraise`, saldría un `RetryError` que el `except` de `function_app.py` no captura: un 500 con el cuerpo vacío, que es el defecto 14 de F-010 otra vez | **Test nuevo** (`b85ce26`) |
| 20 | `time.monotonic() - arranque` → `+` en el log de la escritura | Es el único número que quedará para saber si el ERP fue lento un día que haya que mirarlo, y nadie lo comparaba con nada | **Test nuevo** (`b85ce26`) |
| 21 | `respuesta.get("ok", False)` → `get("ok", True)` en el recuento de filas | **Equivalente en la práctica y no del todo inocuo**: cambia qué se supone cuando la pasarela **no manda** `ok`. Con `True` se daría por confirmado un batch que no lo dijo. Ningún test manda una respuesta **sin** la clave `ok` | **Hueco real, sin test**: es el único de los 26 que se queda así. Se deja dicho aquí en vez de escribir el test a última hora fuera del alcance del encargo |
| 22, 23 | `str(x or "")` → `str(x and "")` en el mapeo de `descripcion` y de `estado_destino_res` | Los tests del mapeo cubren el `NULL` del **estado de origen**, no el de estos dos. Con la mutación, una descripción presente saldría vacía — y la descripción es una de las cinco cosas que R9 obliga a enseñar antes de confirmar | **Hueco real, sin test**: mismo motivo que el 21 |
| 24 | `plan.motivo or 'sin motivo declarado'` en `escrituras.py` | Es el mensaje de una red de seguridad (R10) que el camino normal no alcanza: `paso_cierre` ya aborta antes | **Equivalente en efecto**: cambia el texto de un error que solo se ve componiendo las piezas a mano |
| 25 | `(getattr(...) or "")` → `and ""` en la fábrica | Con la mutación, **todas** las variables parecerían ausentes, así que la fábrica fallaría siempre… y los tests que comprueban que falla siguen pasando. Los que comprueban el camino bueno **no existen**, porque construir el adaptador real es justo lo que la suite tiene prohibido | **Equivalente para la suite**: no se puede cazar sin construir el adaptador de verdad, y eso lo prohíbe R39. Es el precio de la guardia de red, y se prefiere el precio |
| 26 | `confianza_observaciones=0` → `1` en el contexto que arma el handler | El campo se rellena **para no mandar nada**: `paso_cierre` no lo lee y la respuesta no lo devuelve (R51) | **Equivalente**: ningún camino lo observa |

**Resumen honesto:** de 26, **19 eran huecos reales y ya tienen test**, 1 se
eliminó cambiando el código, **3 son equivalentes justificados** (24, 25, 26) y
**3 siguen siendo huecos reales sin test** (21, 22, 23), que se dejan aquí
escritos en vez de taparlos a última hora.

### 7.3 · `bash harness/init.sh`

Ejecutado tal cual, **al cerrar el trabajo**:

```
[OK] pytest en verde (con medición de cobertura)          →  17 pasados (raíz)
[OK] servicio api (services/postventa-api): pytest en verde → 1.594 pasados, 13 saltados (77 s)
[OK] servicio front (services/postventa-front): pytest en verde → 105 pasados (3 s)
[OK] PUERTA COBERTURA: 98.8% de 572 líneas cambiadas cubiertas
     (565/572, umbral 80%, nivel critico)
[OK] Rama actual: feature/F-009-cierre-sigrid
----------------------------------------
ENTORNO LISTO. Puedes trabajar.
```

**Exit code 0.** La cobertura de las líneas cambiadas sube a **98,8 %** tras
los tests que cerraron los supervivientes; la cifra de §7.1 (94,1 %) era la
medición anterior y se deja para que se vea el efecto.

Un único aviso, **que no bloquea y no es de esta feature**: `ruff: 59 avisos
(deuda previa)`. Eran 62 antes de empezar; los ficheros nuevos de F-009 pasan
`ruff check` sin un solo aviso.

### 7.4 · Lo que NO hay en esta sección

- **La verificación contra el ERP** (bloque 8). No es que falte: es que **no
  la puede dar este trabajo**, y está detallada en §6.
- **La campaña de confirmación** con cero supervivientes, por lo dicho en §7.2.

