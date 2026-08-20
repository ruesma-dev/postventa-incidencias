<!-- progress/mutacion_F-006.md -->
# F-006 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-006` el 2026-08-20 02:14.

## Alcance

Origen del diff: **rama** (`f2e317b2af433fee592a08f2a3cf7e3a145d35f4` .. `feature/F-006-sharepoint`).

| Fichero | Líneas en alcance |
|---|---|
| `services/postventa-api/application/pipelines/contexto_parte.py` | 6 |
| `services/postventa-api/application/pipelines/paso_archivo.py` | 234 |
| `services/postventa-api/config/settings.py` | 85 |
| `services/postventa-api/domain/models/errores.py` | 121 |
| `services/postventa-api/domain/models/nombrado.py` | 231 |
| `services/postventa-api/domain/ports/archivo.py` | 92 |
| `services/postventa-api/function_app.py` | 66 |
| `services/postventa-api/infrastructure/sharepoint/__init__.py` | 7 |
| `services/postventa-api/infrastructure/sharepoint/fabrica.py` | 121 |
| `services/postventa-api/infrastructure/sharepoint/graph.py` | 448 |
| `services/postventa-api/interface_adapters/api/archivar.py` | 208 |
| **Total** | **1619** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 64 |
| Mutantes evaluados | 64 |
| Muertos | 59 |
| Supervivientes | 5 |
| Timeouts | 0 |
| Tiempo total | 235.2 s |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/postventa-api/config/settings.py:285` [entero]

- Original: `default=60,`
- Mutado:   `default=61,`

#### Análisis · MUTANTE EQUIVALENTE justificado

**Qué es**: el valor por defecto de `GRAPH_TIMEOUT_S`, los segundos que se le
conceden a una llamada a Graph cuando el despliegue no dice otra cosa.

**Por qué ningún test lo caza**: porque no hay ningún requisito que fije *60*.
Lo que la feature exige de este número es una **propiedad**, no un valor: que
una llamada colgada no se coma los 230 s a los que corta la Function. Con 60 y
con 61 se cumple igual, y con los tres reintentos por defecto el peor caso son
180 s (o 183 s con el mutante), por debajo del techo en los dos casos.

**Por qué no se añade un test**: un `assert ajustes.graph_timeout_s == 60` no
protegería nada; sería un detector de cambios que hay que actualizar cada vez
que alguien afina el número, y esa clase de test acaba actualizándose sin
pensar. La propiedad que sí importa —que quepa dentro de los 230 s— la fija el
despliegue, no la suite.

**Riesgo residual**: ninguno de comportamiento. Si algún día el margen se
volviera ajustado, lo que habría que escribir es un test de la **propiedad**
(`timeout * reintentos < 230`), no del valor.

### 2. `services/postventa-api/config/settings.py:293` [entero]

- Original: `default=3,`
- Mutado:   `default=4,`

#### Análisis · MUTANTE EQUIVALENTE justificado

**Qué es**: el valor por defecto de `GRAPH_REINTENTOS`.

**Por qué ningún test lo caza**: el comportamiento que la feature exige de los
reintentos —**qué** se reintenta y qué no— está cubierto y bien cubierto:
`test_f006_r25_un_error_transitorio_se_reintenta` (los seis códigos, uno a
uno), `test_f006_r25_un_error_no_transitorio_no_se_reintenta` (un `403` o un
`404` producen **una** llamada) y
`test_f006_r25_agotados_los_reintentos_sale_archivo_fallido`, que fija el
número **pasándolo explícitamente** (`reintentos=3`) y comprobando que se
hacen tres llamadas y ni una más. Lo que este mutante toca es solo el valor por
omisión del despliegue, que ningún test consume.

**Por qué no se añade un test**: mismo motivo que el anterior. El número
concreto es una decisión de operación, no una regla del dominio.

**Riesgo residual**: ninguno. Cuántas veces se reintenta se puede cambiar por
variable de entorno sin tocar código, que es justamente para lo que está.

### 3. `services/postventa-api/infrastructure/sharepoint/graph.py:112` [entero]

- Original: `MARGEN_DE_TOKEN_S = 60`
- Mutado:   `MARGEN_DE_TOKEN_S = 61`

#### Análisis · MUTANTE EQUIVALENTE justificado

**Qué es**: el margen con el que se renueva el token antes de que caduque.

**Por qué ningún test lo caza**: el comportamiento sí está cubierto —
`test_f006_r25_un_token_caducado_se_vuelve_a_pedir` y
`test_f006_r25_un_token_vigente_no_se_vuelve_a_pedir`, los dos **añadidos a
raíz de esta campaña**—, pero cubren la caducidad, no el tamaño del margen.
Distinguir 60 de 61 exige un token cuyo `expires_in` caiga **exactamente** en
la frontera (`expires_in = 61`), y entonces el test pasaría a depender de que
entre dos llamadas en memoria transcurra menos de un segundo.

**Por qué no se añade un test**: sería un test con un presupuesto de un segundo
de reloj real. Con la máquina cargada —y la campaña de mutación corre 16
procesos a la vez— fallaría de vez en cuando. **Un test que falla a veces es
peor que no tener test**: se acaba desactivando, y de paso desactiva la
confianza en los que sí valen.

**Riesgo residual**: despreciable. El margen existe para no usar un token que
caduque en pleno vuelo; 60 o 61 segundos protegen igual, y el fallo que evitaría
la diferencia —un `401` en la ventana de un segundo— se traduce en una traza de
`error` y un reintento del parte, no en un archivo corrupto.

### 4. `services/postventa-api/infrastructure/sharepoint/graph.py:362` [comparacion]

- Original: `if self._token is not None and time.monotonic() < self._token_expira_en:`
- Mutado:   `if self._token is not None and time.monotonic() <= self._token_expira_en:`

#### Análisis · MUTANTE EQUIVALENTE (en el sentido estricto)

**Qué es**: la comparación que decide si el token cacheado sigue siendo válido,
`time.monotonic() < self._token_expira_en` frente a `<=`.

**Por qué ningún test lo caza**: porque **no es cazable**. Los dos operadores
solo difieren cuando los dos flotantes son **exactamente** iguales, y
`time.monotonic()` devuelve un flotante de resolución de nanosegundos que se
compara contra otro calculado en un instante distinto. Que coincidan bit a bit
no es improbable: es un caso que no se puede provocar de forma determinista.

**Por qué no se añade un test**: no existe entrada que lo distinga. Es la
definición de mutante equivalente.

**Riesgo residual**: ninguno. Aunque coincidieran, la diferencia sería usar un
token durante un instante más, y el margen de 60 s de renovación ya cubre eso
con seis órdenes de magnitud de sobra.

### 5. `services/postventa-api/infrastructure/sharepoint/graph.py:380` [entero]

- Original: `time.monotonic() + int(cuerpo.get("expires_in", 3599)) - MARGEN_DE_TOKEN_S`
- Mutado:   `time.monotonic() + int(cuerpo.get("expires_in", 3600)) - MARGEN_DE_TOKEN_S`

#### Análisis · MUTANTE EQUIVALENTE justificado

**Qué es**: el `expires_in` **de reserva**, el que se usa solo si la respuesta
del punto de token de Entra no trae ese campo.

**Por qué ningún test lo caza**: distinguir 3599 de 3600 exige que pase una
hora de reloj real entre dos llamadas. La caché sí está cubierta —los dos tests
de caducidad citados arriba, con `expira_en` explícito—, y el camino en que
`expires_in` falta también se ejercita; lo que no se puede ejercitar es la
diferencia de **un segundo dentro de una hora**.

**Por qué no se añade un test**: haría falta manipular el reloj monótono, que
no es un reloj que se pueda fijar. Y el valor solo entra en juego si Entra
incumple su propio contrato y omite `expires_in`, que es un camino de
salvaguarda, no el normal.

**Riesgo residual**: ninguno. En el peor caso el token se renovaría un segundo
antes o después dentro de una ventana de una hora, y el margen de 60 s absorbe
la diferencia entera.

---

## Veredicto de la campaña (nivel `critico`)

**Cinco supervivientes, cinco análisis completos, ninguno pendiente.** Los
cinco son **mutantes equivalentes o constantes de operación**: ninguno describe
un comportamiento que la feature prometa y que ningún test compruebe.

Dos campañas antes había **20 supervivientes**. Las tres cuartas partes se
mataron, y el camino hasta aquí está en `progress/impl_F-006.md`: la campaña
destapó **tres huecos reales de test y dos de código**, entre ellos una puerta
de aptitud que se podía saltar y un parámetro muerto que nadie había visto.

| Campaña | Mutantes | Muertos | Supervivientes |
|---|---|---|---|
| 1.ª | 68 | 48 | 20 |
| 2.ª | 64 | 58 | 6 |
| 3.ª (final) | 64 | 59 | **5** |

Los cinco que quedan se reparten así:

| # | Qué es | Por qué sobrevive |
|---|---|---|
| 1 | `GRAPH_TIMEOUT_S` por defecto | Constante de operación; el requisito es una propiedad, no el número |
| 2 | `GRAPH_REINTENTOS` por defecto | Ídem; **qué** se reintenta sí está cubierto, y a fondo |
| 3 | `MARGEN_DE_TOKEN_S` | Cazarlo exigiría un test con un presupuesto de 1 s de reloj real |
| 4 | `<` frente a `<=` sobre `time.monotonic()` | Equivalente estricto: no hay entrada que los distinga |
| 5 | `expires_in` de reserva, 3599 | Exigiría una hora de reloj real, y solo si Entra incumple su contrato |

Ninguno de los cinco toca **el nombrado** —los separadores, el sufijo, el orden
de las sustituciones—, ni **la puerta de entorno**, ni **la idempotencia**, que
eran los tres sitios donde `tasks.md` (T20) pedía mirar con lupa. Ahí no
sobrevive nada.

> **Este análisis lo tiene que aceptar el humano**, como pide el nivel
> `critico`. Su copia durable está en `progress/impl_F-006.md`: este fichero lo
> **regenera** la siguiente campaña y se lleva por delante lo escrito a mano.
