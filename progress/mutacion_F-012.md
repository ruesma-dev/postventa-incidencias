<!-- progress/mutacion_F-012.md -->
# F-012 · Campaña de mutación

> **Dos pasadas, y las dos quedan aquí.** La primera dejó **35 supervivientes**.
> T33 los analizó uno a uno —**30 huecos reales de test** y **5 equivalentes**—
> y añadió los 22 tests que faltaban, **sin tocar una línea de producción**. La
> segunda se lanzó con esos tests dentro y es la que vale como evidencia de
> C4 bis: **101 mutantes, 96 muertos, 5 supervivientes, 0 timeouts**, y esos
> cinco son exactamente los cinco equivalentes justificados.
>
> Las dos se lanzaron con el mismo comando, acotando la base a la rama de F-009
> para no volver a mutar código que ya pasó su propia campaña:
>
> ```bash
> python -m harness.mutacion --feature F-012 --base feature/F-009-cierre-sigrid
> ```
>
> **Ni un `PENDIENTE`**: los 35 de la primera pasada llevan su análisis, y los 5
> de la segunda llevan el mismo, porque son los mismos.

# Segunda pasada · la que cuenta

Generado por `python -m harness.mutacion --feature F-012 --workers 8` el 2026-09-06 14:51.

## Alcance

Origen del diff: **rama** (`c93ed49e8b8653262ee62b426f61b4a1c19265fc` .. `feature/F-012-grafico-sigrid`).

| Fichero | Líneas en alcance |
|---|---|
| `services/postventa-api/application/pipelines/contexto_parte.py` | 20 |
| `services/postventa-api/application/pipelines/paso_cierre.py` | 54 |
| `services/postventa-api/application/pipelines/paso_grafico.py` | 650 |
| `services/postventa-api/config/settings.py` | 40 |
| `services/postventa-api/domain/models/cierre.py` | 18 |
| `services/postventa-api/domain/models/errores.py` | 178 |
| `services/postventa-api/domain/models/grafico.py` | 367 |
| `services/postventa-api/domain/models/persistencia.py` | 74 |
| `services/postventa-api/domain/ports/grafico.py` | 78 |
| `services/postventa-api/domain/ports/persistencia.py` | 22 |
| `services/postventa-api/function_app.py` | 206 |
| `services/postventa-api/infrastructure/persistencia/mapeo.py` | 66 |
| `services/postventa-api/infrastructure/persistencia/repositorio_pg.py` | 50 |
| `services/postventa-api/infrastructure/persistencia/sentencias.py` | 103 |
| `services/postventa-api/infrastructure/sigrid/fabrica.py` | 46 |
| `services/postventa-api/infrastructure/sigrid/graficos.py` | 338 |
| `services/postventa-api/interface_adapters/api/adjuntar.py` | 365 |
| `services/postventa-api/interface_adapters/api/cerrar.py` | 46 |
| **Total** | **2721** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 101 |
| Mutantes evaluados | 101 |
| Muertos | 96 |
| Supervivientes | 5 |
| Timeouts | 0 |
| Timeouts repasados en serie | 0: ningún mutante agotó el reloj |
| Tiempo total | 922.8 s |
| Workers | 8 |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

> **Los cinco son equivalentes**, y son los mismos cinco que la primera pasada
> ya había dejado justificados. Los números que citan los análisis de abajo
> —«el superviviente 8», «el 10»— son los de la **primera** pasada, que es
> donde están sus hermanos cazados.

### 1. `services/postventa-api/domain/models/errores.py:867` [booleano]

- Original: `def __init__(self, motivo: str, *, reintento_seguro: bool = True) -> None:`
- Mutado:   `def __init__(self, motivo: str, *, reintento_seguro: bool = False) -> None:`

#### Análisis

**EQUIVALENTE (valor por omisión que siempre se sobreescribe).** Los
**tres** únicos sitios que construyen `GraficoFallido` pasan
`reintento_seguro=True` de forma explícita, así que el valor por omisión no se
ejecuta nunca. Comprobable:

```bash
grep -rn "GraficoFallido(" --include=*.py services/postventa-api | grep -v tests
# paso_grafico.py:538, paso_grafico.py:545 y graficos.py:298; los tres pasan
# reintento_seguro=True unas líneas más abajo
```

### 2. `services/postventa-api/domain/models/grafico.py:184` [booleano]

- Original: `ya_cerrada: bool = False`
- Mutado:   `ya_cerrada: bool = True`

#### Análisis

**EQUIVALENTE (valor por omisión que siempre se sobreescribe).** El
único sitio que construye `PlanDeGrafico` es `_plan` (`paso_grafico.py:579`),
que pasa `ya_cerrada=ya_cerrada` siempre. El valor por omisión **del propio
`_plan`** sí se usa, y ese es el superviviente 8, que está cazado. Comprobable:

```bash
grep -rn "PlanDeGrafico(" --include=*.py services/postventa-api | grep -v tests
# una sola línea: application/pipelines/paso_grafico.py:579
```

### 3. `services/postventa-api/domain/models/grafico.py:187` [booleano]

- Original: `idempotente_previsto: bool = False`
- Mutado:   `idempotente_previsto: bool = True`

#### Análisis

**EQUIVALENTE**, por lo mismo que el 15: `_plan` pasa siempre
`idempotente_previsto=idempotente_previsto`. Su equivalente vivo es el
superviviente 9, cazado.

### 4. `services/postventa-api/domain/models/persistencia.py:227` [booleano]

- Original: `idempotente: bool = False`
- Mutado:   `idempotente: bool = True`

#### Análisis

**EQUIVALENTE (valor por omisión que siempre se sobreescribe).** Los dos
únicos sitios que construyen `TrazaGrafico` pasan `idempotente` explícitamente:
`paso_grafico.py:617` (`_traza`, cuya expresión es el superviviente 10, cazado)
y `mapeo.py:278`, que lo lee de la fila. Comprobable:

```bash
grep -rn "TrazaGrafico(" --include=*.py services/postventa-api | grep -v tests
```

### 5. `services/postventa-api/interface_adapters/api/adjuntar.py:251` [entero]

- Original: `confianza_observaciones=0,`
- Mutado:   `confianza_observaciones=1,`

#### Análisis

**EQUIVALENTE (inobservable).** El `confianza_observaciones=0` de
`_como_contexto` va en una `ResultadoValidacion` **reconstruida** que solo lee
`_exigir_apto`, y de ella únicamente `veredicto` y `destino`; el paso no
persiste la validación y `_serializar` devuelve ocho claves fijas que no la
incluyen. Ningún camino lee ese campo. Comprobable:

```bash
grep -n "ctx.validacion" services/postventa-api/application/pipelines/paso_grafico.py
# solo veredicto y destino
grep -rn "confianza_observaciones" --include=*.py services/postventa-api | grep -v tests
# los lectores (cola.py, validar.py) trabajan con la validación real de F-004,
# que llega de la base, no con esta
```

Es el mismo relleno que `archivar.py:197` y `cerrar.py:219`, y va con
`observaciones=None`: no hay observaciones de las que dar confianza.

---

# Primera pasada · el punto de partida y el análisis de los 35

Generado por `python -m harness.mutacion --feature F-012 --workers 8` el 2026-09-06 14:05.

## Alcance

Origen del diff: **rama** (`c93ed49e8b8653262ee62b426f61b4a1c19265fc` .. `feature/F-012-grafico-sigrid`).

| Fichero | Líneas en alcance |
|---|---|
| `services/postventa-api/application/pipelines/contexto_parte.py` | 20 |
| `services/postventa-api/application/pipelines/paso_cierre.py` | 54 |
| `services/postventa-api/application/pipelines/paso_grafico.py` | 650 |
| `services/postventa-api/config/settings.py` | 40 |
| `services/postventa-api/domain/models/cierre.py` | 18 |
| `services/postventa-api/domain/models/errores.py` | 178 |
| `services/postventa-api/domain/models/grafico.py` | 367 |
| `services/postventa-api/domain/models/persistencia.py` | 74 |
| `services/postventa-api/domain/ports/grafico.py` | 78 |
| `services/postventa-api/domain/ports/persistencia.py` | 22 |
| `services/postventa-api/function_app.py` | 206 |
| `services/postventa-api/infrastructure/persistencia/mapeo.py` | 66 |
| `services/postventa-api/infrastructure/persistencia/repositorio_pg.py` | 50 |
| `services/postventa-api/infrastructure/persistencia/sentencias.py` | 103 |
| `services/postventa-api/infrastructure/sigrid/fabrica.py` | 46 |
| `services/postventa-api/infrastructure/sigrid/graficos.py` | 338 |
| `services/postventa-api/interface_adapters/api/adjuntar.py` | 365 |
| `services/postventa-api/interface_adapters/api/cerrar.py` | 46 |
| **Total** | **2721** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 101 |
| Mutantes evaluados | 101 |
| Muertos | 66 |
| Supervivientes | 35 |
| Timeouts | 0 |
| Timeouts repasados en serie | 0: ningún mutante agotó el reloj |
| Tiempo total | 853.8 s |
| Workers | 8 |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/postventa-api/application/pipelines/paso_grafico.py:212` [booleano]

- Original: `True,`
- Mutado:   `False,`

#### Análisis

**REAL.** `plan.cerrable` es lo que el borde serializa como
`dry_run.cerrable` y lo que el front usa para ofrecer —o no— el botón de
cerrar. Ningún test lo leía en el camino bueno: los de R21 miraban el nombre,
el `sha256` y los avisos, y los de R16/R17 solo miraban el estado.

**Tests que lo matan**: `test_f012_r21_el_plan_del_dry_run_correcto_dice_cerrable_y_no_cerrada`
(`tests/test_f012_paso_grafico.py`) y `test_f012_r21_el_dry_run_normal_no_dice_que_el_parte_ya_estuviera_dentro`
(`tests/test_f012_adjuntar_http.py`).

### 2. `services/postventa-api/application/pipelines/paso_grafico.py:273` [logico]

- Original: `or ctx.validacion.destino != Destino.ARCHIVO_Y_CIERRE`
- Mutado:   `and ctx.validacion.destino != Destino.ARCHIVO_Y_CIERRE`

#### Análisis

**REAL, y era el hueco más serio de los 35.** Con `and`, un parte cuyo
veredicto no fuera `apto` pasaría la puerta siempre que el destino dijera
`archivo_y_cierre` — y ese destino llega en el formulario. Los dos tests de R14
que existían cambiaban **las dos** condiciones a la vez (`no_apto` +
`revision_manual`), así que con `and` las dos seguían siendo verdaderas y la
puerta seguía mordiendo.

**Tests que lo matan**: `test_f012_r14_un_veredicto_que_no_es_apto_no_pasa_aunque_el_destino_lo_sea`
y `test_f012_r14_un_destino_que_no_es_archivo_y_cierre_no_pasa_aunque_sea_apto`
(`tests/test_f012_paso_grafico.py`), uno por cada mitad del `or`.

### 3. `services/postventa-api/application/pipelines/paso_grafico.py:368` [booleano]

- Original: `plan = _plan(reclamacion, login, peticion, True, motivo)`
- Mutado:   `plan = _plan(reclamacion, login, peticion, False, motivo)`

#### Análisis

**REAL.** Es el plan que queda en el contexto cuando la pasarela rechaza
el **dry-run**: conserva `cerrable=True` porque la reclamación sí admitía
cierre —lo que falló fue el gráfico—. Marcarla como no cerrable mandaría a
Posventa a mirar un expediente que no tiene nada de malo. Nadie leía ese plan:
los tests de R33 solo miraban el estado de la traza.

**Test que lo mata**: `test_f012_r33_un_rechazo_del_dry_run_no_dice_que_la_reclamacion_no_valga`.

### 4. `services/postventa-api/application/pipelines/paso_grafico.py:402` [booleano]

- Original: `plan = _plan(reclamacion, login, peticion, False, motivo, ya_cerrada=True)`
- Mutado:   `plan = _plan(reclamacion, login, peticion, True, motivo, ya_cerrada=True)`

#### Análisis

**REAL.** Es el `cerrable=False` de la salida de R16. Se serializa como
`dry_run.cerrable`, y en falso es lo que impide que el front ofrezca cerrar un
expediente que ya está cerrado.

**Tests que lo matan**: `test_f012_r16_el_plan_de_una_reclamacion_ya_cerrada_lo_dice_entero`
y `test_f012_r16_una_reclamacion_ya_cerrada_se_devuelve_en_verde_y_lo_dice`.

### 5. `services/postventa-api/application/pipelines/paso_grafico.py:402` [booleano]

- Original: `plan = _plan(reclamacion, login, peticion, False, motivo, ya_cerrada=True)`
- Mutado:   `plan = _plan(reclamacion, login, peticion, False, motivo, ya_cerrada=False)`

#### Análisis

**REAL.** `ya_cerrada` es el campo que explica que no se adjunte nada, y
es propio precisamente porque **no es un error** (R16). Los tests existentes
comprobaban el estado del resultado y de la traza, nunca el plan.

**Tests que lo matan**: los dos del superviviente 4.

### 6. `services/postventa-api/application/pipelines/paso_grafico.py:542` [booleano]

- Original: `reintento_seguro=True,`
- Mutado:   `reintento_seguro=False,`

#### Análisis

**REAL, y con la línea sin ejercitar.** Es el `reintento_seguro=True` del
`GraficoFallido` de R26: la pasarela responde sin `committed` ni `idempotente`
y el parte no está dentro. `GraficoEnMemoria` no sabe fabricar esa respuesta
—no es ninguna de las cuatro formas del contrato—, así que ningún test del paso
llegaba a esa rama.

**Test que lo mata**: `test_f012_r26_r29_una_respuesta_que_no_cuelga_nada_no_se_da_por_adjuntada`,
con un doble propio (`GraficoQueNoCuelgaNada`) escrito para eso.

### 7. `services/postventa-api/application/pipelines/paso_grafico.py:551` [booleano]

- Original: `reintento_seguro=True,`
- Mutado:   `reintento_seguro=False,`

#### Análisis

**REAL.** La rama sí se ejercitaba (R27, recuento de filas distinto de
tres), pero nadie leía el booleano: el test miraba el número en el motivo y el
estado de la traza. Y ese booleano es la diferencia con F-009: dice si se puede
volver a intentar sin abrir el ERP.

**Test que lo mata**: `test_f012_r27_un_commit_con_filas_distintas_de_tres_es_un_error`,
al que se le ha añadido `assert fallo.value.reintento_seguro is True`.

### 8. `services/postventa-api/application/pipelines/paso_grafico.py:567` [booleano]

- Original: `ya_cerrada: bool = False,`
- Mutado:   `ya_cerrada: bool = True,`

#### Análisis

**REAL.** No es un valor por omisión inerte: **tres de las cuatro**
llamadas a `_plan` omiten `ya_cerrada` (las dos del dry-run y la del estado no
cerrable), así que el mutante hace que el camino bueno devuelva
`ya_cerrada=True` y el borde lo serialice.

**Test que lo mata**: `test_f012_r21_el_plan_del_dry_run_correcto_dice_cerrable_y_no_cerrada`.

### 9. `services/postventa-api/application/pipelines/paso_grafico.py:568` [booleano]

- Original: `idempotente_previsto: bool = False,`
- Mutado:   `idempotente_previsto: bool = True,`

#### Análisis

**REAL, por lo mismo.** La salida de R16 omite `idempotente_previsto`, y
ahí no se ha preguntado nada a la pasarela: afirmar que el documento ya estaba
dentro sería inventarse una lectura.

**Test que lo mata**: `test_f012_r16_el_plan_de_una_reclamacion_ya_cerrada_lo_dice_entero`,
y por el borde `test_f012_r16_una_reclamacion_ya_cerrada_se_devuelve_en_verde_y_lo_dice`.

### 10. `services/postventa-api/application/pipelines/paso_grafico.py:632` [booleano]

- Original: `idempotente=respuesta.idempotente if respuesta is not None else False,`
- Mutado:   `idempotente=respuesta.idempotente if respuesta is not None else True,`

#### Análisis

**REAL.** Es la columna `idempotente` de la traza cuando **no hay
respuesta** de la pasarela (dry-run correcto, error, ya cerrada). Esa columna es
la que responde después por R24 sin llamar a nadie: en verdadero, el endpoint
diría que el parte ya está en Sigrid sin que nadie lo haya subido.

**Test que lo mata**: `test_f012_r42_la_traza_del_dry_run_no_afirma_que_el_grafico_ya_estuviera`.

### 11. `services/postventa-api/domain/models/errores.py:867` [booleano]

- Original: `def __init__(self, motivo: str, *, reintento_seguro: bool = True) -> None:`
- Mutado:   `def __init__(self, motivo: str, *, reintento_seguro: bool = False) -> None:`

#### Análisis

**EQUIVALENTE (valor por omisión que siempre se sobreescribe).** Los
**tres** únicos sitios que construyen `GraficoFallido` pasan
`reintento_seguro=True` de forma explícita, así que el valor por omisión no se
ejecuta nunca. Comprobable:

```bash
grep -rn "GraficoFallido(" --include=*.py services/postventa-api | grep -v tests
# paso_grafico.py:538, paso_grafico.py:545 y graficos.py:298; los tres pasan
# reintento_seguro=True unas líneas más abajo
```

### 12. `services/postventa-api/domain/models/grafico.py:92` [entero]

- Original: `LONGITUD_MAXIMA_NOM = 255`
- Mutado:   `LONGITUD_MAXIMA_NOM = 256`

#### Análisis

**REAL, y el test que había se movía con la constante.**
`test_f012_r9_un_nombre_que_no_cabe_en_el_erp_se_rechaza` construye el nombre
con `LONGITUD_MAXIMA_NOM + 1`: si el tope sube a 256, el test sube con él y
sigue en verde. Y 255 no es un número redondo elegido aquí, es el ancho
**medido** de `gra.nom` (`varchar(255)`, `sigrid_tablas.md`): con 256, en el
ERP entraría un nombre truncado que dejaría de cruzar con SharePoint.

**Test que lo mata**: `test_f012_r9_un_nombre_de_256_caracteres_ya_no_cabe`, con
la frontera en números absolutos y no en la constante.

### 13. `services/postventa-api/domain/models/grafico.py:138` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis

**REAL** en sentido estricto —la asignación deja de levantar
`FrozenInstanceError` y ningún test lo veía—, aunque hoy ninguna ruta de
producción mute la petición. Lo que el test fija es la garantía sobre la que se
apoyan R20 y R21: entre el dry-run y el commit media la confirmación de una
persona, y R20 se comprueba **contando llamadas**, no comparando objetos; si la
petición se pudiera retocar por el camino, ese recuento seguiría en verde con
otro contenido dentro.

**Test que lo mata**: `test_f012_r20_r21_las_piezas_del_grafico_no_se_pueden_modificar[peticion]`.

### 14. `services/postventa-api/domain/models/grafico.py:166` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis

**REAL**, mismo razonamiento que el 13 aplicado al plan, que es
literalmente lo que se enseña para confirmar.

**Test que lo mata**: `test_f012_r20_r21_las_piezas_del_grafico_no_se_pueden_modificar[plan]`.

### 15. `services/postventa-api/domain/models/grafico.py:184` [booleano]

- Original: `ya_cerrada: bool = False`
- Mutado:   `ya_cerrada: bool = True`

#### Análisis

**EQUIVALENTE (valor por omisión que siempre se sobreescribe).** El
único sitio que construye `PlanDeGrafico` es `_plan` (`paso_grafico.py:579`),
que pasa `ya_cerrada=ya_cerrada` siempre. El valor por omisión **del propio
`_plan`** sí se usa, y ese es el superviviente 8, que está cazado. Comprobable:

```bash
grep -rn "PlanDeGrafico(" --include=*.py services/postventa-api | grep -v tests
# una sola línea: application/pipelines/paso_grafico.py:579
```

### 16. `services/postventa-api/domain/models/grafico.py:187` [booleano]

- Original: `idempotente_previsto: bool = False`
- Mutado:   `idempotente_previsto: bool = True`

#### Análisis

**EQUIVALENTE**, por lo mismo que el 15: `_plan` pasa siempre
`idempotente_previsto=idempotente_previsto`. Su equivalente vivo es el
superviviente 9, cazado.

### 17. `services/postventa-api/domain/models/grafico.py:193` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis

**REAL**, mismo razonamiento que el 13 aplicado a la respuesta de la
pasarela, que es de donde sale la decisión de R26.

**Test que lo mata**: `test_f012_r20_r21_las_piezas_del_grafico_no_se_pueden_modificar[respuesta]`.

### 18. `services/postventa-api/domain/models/grafico.py:222` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis

**REAL**, mismo razonamiento que el 13 aplicado al resultado que viaja
en el contexto del pipeline.

**Test que lo mata**: `test_f012_r20_r21_las_piezas_del_grafico_no_se_pueden_modificar[resultado]`.

### 19. `services/postventa-api/domain/models/grafico.py:310` [comparacion]

- Original: `if len(usu) > LONGITUD_MAXIMA_USU:`
- Mutado:   `if len(usu) >= LONGITUD_MAXIMA_USU:`

#### Análisis

**REAL.** Con `>=`, un login de **exactamente 24** caracteres —el ancho
justo de `usu.cod`, y los hay— se rechazaría, y a esa persona el servicio le
diría que su login no cabe en un sitio donde sí cabe. El test que había solo
probaba el lado de fuera (`LONGITUD_MAXIMA_USU + 1`).

**Test que lo mata**: `test_f012_r12_un_login_de_exactamente_24_caracteres_si_cabe`.

### 20. `services/postventa-api/domain/models/grafico.py:320` [comparacion]

- Original: `if len(nom) > LONGITUD_MAXIMA_NOM:`
- Mutado:   `if len(nom) >= LONGITUD_MAXIMA_NOM:`

#### Análisis

**REAL**, la frontera simétrica del nombre: con `>=`, un nombre de
exactamente 255 caracteres se rechazaría y el parte de esa obra no se
adjuntaría nunca.

**Test que lo mata**: `test_f012_r9_un_nombre_de_exactamente_255_caracteres_si_cabe`.

### 21. `services/postventa-api/domain/models/persistencia.py:185` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis

**REAL**, mismo razonamiento que el 13 aplicado a la traza: es lo que se
guarda de una escritura en el ERP de producción.

**Test que lo mata**: `test_f012_r20_r21_las_piezas_del_grafico_no_se_pueden_modificar[traza]`.

### 22. `services/postventa-api/domain/models/persistencia.py:227` [booleano]

- Original: `idempotente: bool = False`
- Mutado:   `idempotente: bool = True`

#### Análisis

**EQUIVALENTE (valor por omisión que siempre se sobreescribe).** Los dos
únicos sitios que construyen `TrazaGrafico` pasan `idempotente` explícitamente:
`paso_grafico.py:617` (`_traza`, cuya expresión es el superviviente 10, cazado)
y `mapeo.py:278`, que lo lee de la fila. Comprobable:

```bash
grep -rn "TrazaGrafico(" --include=*.py services/postventa-api | grep -v tests
```

### 23. `services/postventa-api/infrastructure/sigrid/graficos.py:129` [aritmetico]

- Original: `time.monotonic() - arranque,`
- Mutado:   `time.monotonic() + arranque,`

#### Análisis

**REAL, y observable.** La duración solo va al log, pero el log es lo
único con lo que se ve desde fuera que la pasarela va lenta **antes** de que
empiece a agotar el presupuesto de 45 s de la Function. Compuesta al revés sale
un número enorme y perfectamente plausible para quien no sepa que
`time.monotonic()` cuenta desde el arranque de la máquina.

**Test que lo mata**: `test_f012_el_log_registra_la_duracion_real_de_la_llamada`,
que fija el reloj del módulo en dos lecturas y exige `en 2.50 s` en el log.

### 24. `services/postventa-api/infrastructure/sigrid/graficos.py:255` [comparacion]

- Original: `if familia == "reintentable":`
- Mutado:   `if familia != "reintentable":`

#### Análisis

**REAL.** Con `!=`, un código **declarado reintentable** cae en la rama
del código desconocido y viceversa: los dos salen como 502, pero cuentan cosas
opuestas del ERP. El reintentable dice que la pasarela revirtió y nombra el
código —que es lo que permite buscarlo—; el desconocido dice justamente que no
se da por hecho que el ERP esté intacto. El test que había solo comprobaba que
en el motivo apareciera `reintent`, y eso lo dicen los dos.

**Test que lo mata**: `test_f012_r31_r34_un_codigo_reintentable_y_uno_desconocido_no_dicen_lo_mismo`.

### 25. `services/postventa-api/infrastructure/sigrid/graficos.py:325` [booleano]

- Original: `ok=bool(datos.get("ok", False)),`
- Mutado:   `ok=bool(datos.get("ok", True)),`

#### Análisis

**REAL.** Ningún test omitía la clave: todos los cuerpos de respuesta de
la suite venían completos. Un `200` con un cuerpo que no es el del contrato es
lo que devuelve un proxy o una versión de la pasarela que ya no responde lo
mismo, y con `True` por omisión `esta_colgado` daría por adjuntado un parte que
no está en ninguna parte del ERP.

**Test que lo mata**: `test_f012_r26_una_respuesta_sin_los_campos_del_contrato_no_es_un_exito`.

### 26. `services/postventa-api/infrastructure/sigrid/graficos.py:326` [booleano]

- Original: `committed=bool(datos.get("committed", False)),`
- Mutado:   `committed=bool(datos.get("committed", True)),`

#### Análisis

**REAL**, mismo caso que el 25 con `committed`. Lo mata el mismo test.

### 27. `services/postventa-api/infrastructure/sigrid/graficos.py:327` [booleano]

- Original: `idempotente=bool(datos.get("idempotente", False)),`
- Mutado:   `idempotente=bool(datos.get("idempotente", True)),`

#### Análisis

**REAL**, mismo caso que el 25 con `idempotente` — y aquí el daño es más
directo: `idempotente` en verdadero por omisión hace que `esta_colgado` diga que
sí con cualquier cuerpo vacío. Lo mata el mismo test.

### 28. `services/postventa-api/infrastructure/sigrid/graficos.py:328` [booleano]

- Original: `dry_run=bool(datos.get("dry_run", False)),`
- Mutado:   `dry_run=bool(datos.get("dry_run", True)),`

#### Análisis

**REAL**, mismo caso que el 25 con `dry_run`. Lo mata el mismo test.

### 29. `services/postventa-api/infrastructure/sigrid/graficos.py:330` [entero]

- Original: `bytes=int(grafico.get("bytes") or 0),`
- Mutado:   `bytes=int(grafico.get("bytes") or 1),`

#### Análisis

**REAL.** Un tamaño inventado (`1`) se guarda en la traza y es lo que
alguien compara, meses después, con el fichero de SharePoint. Lo mata el mismo
test que el 25.

### 30. `services/postventa-api/interface_adapters/api/adjuntar.py:96` [booleano]

- Original: `confirmado: str | bool = False,`
- Mutado:   `confirmado: str | bool = True,`

#### Análisis

**REAL.** Es el valor por omisión de `confirmado`, y a diferencia de los
supervivientes 11, 15, 16 y 22 este **sí** se ejecuta: `adjuntar_grafico` es una
función pública y su contrato, escrito en el docstring del módulo, dice que
quien llame sin haber leído el contrato no escribe nada en el ERP de
producción. Toda la suite del borde pasaba `confirmado` explícito.

**Test que lo mata**: `test_f012_r23_sin_el_campo_confirmado_no_se_escribe_nada`.

### 31. `services/postventa-api/interface_adapters/api/adjuntar.py:213` [booleano]

- Original: `return True`
- Mutado:   `return False`

#### Análisis

**REAL.** Es la rama que admite el `True` de Python además de la cadena
`true`, documentada como la forma de llamar al handler desde un test sin
fabricar cadenas. Toda la suite del borde usaba cadenas, así que la rama estaba
sin ejercitar. Si dejara de valer, un test que pidiera escribir haría un
dry-run —que también responde en verde— y nadie se enteraría.

**Test que lo mata**: `test_f012_r57_r23_las_banderas_admiten_tambien_el_booleano_de_python`.

### 32. `services/postventa-api/interface_adapters/api/adjuntar.py:251` [entero]

- Original: `confianza_observaciones=0,`
- Mutado:   `confianza_observaciones=1,`

#### Análisis

**EQUIVALENTE (inobservable).** El `confianza_observaciones=0` de
`_como_contexto` va en una `ResultadoValidacion` **reconstruida** que solo lee
`_exigir_apto`, y de ella únicamente `veredicto` y `destino`; el paso no
persiste la validación y `_serializar` devuelve ocho claves fijas que no la
incluyen. Ningún camino lee ese campo. Comprobable:

```bash
grep -n "ctx.validacion" services/postventa-api/application/pipelines/paso_grafico.py
# solo veredicto y destino
grep -rn "confianza_observaciones" --include=*.py services/postventa-api | grep -v tests
# los lectores (cola.py, validar.py) trabajan con la validación real de F-004,
# que llega de la base, no con esta
```

Es el mismo relleno que `archivar.py:197` y `cerrar.py:219`, y va con
`observaciones=None`: no hay observaciones de las que dar confianza.

### 33. `services/postventa-api/interface_adapters/api/adjuntar.py:280` [entero]

- Original: `else 0`
- Mutado:   `else 1`

#### Análisis

**REAL.** Es el `filas_afectadas` que sale por la respuesta HTTP cuando
**no hubo respuesta de la pasarela** —la salida de R16 y la de R24—. Decir `1`
sería afirmar que se escribió una fila en el ERP en un camino en el que no se ha
escrito ninguna.

**Test que lo mata**: `test_f012_r16_una_reclamacion_ya_cerrada_se_devuelve_en_verde_y_lo_dice`.

### 34. `services/postventa-api/interface_adapters/api/adjuntar.py:313` [booleano]

- Original: `return False`
- Mutado:   `return True`

#### Análisis

**REAL.** Es el `idempotente` de la respuesta cuando no hay ni respuesta
de la pasarela ni traza previa: la salida de R16. En verdadero le diría a quien
mira la pantalla que el documento ya estaba dentro de Sigrid, que es exactamente
lo contrario de lo que ha pasado.

**Test que lo mata**: el mismo del superviviente 33.

### 35. `services/postventa-api/interface_adapters/api/adjuntar.py:347` [booleano]

- Original: `"ya_estaba": False,`
- Mutado:   `"ya_estaba": True,`

#### Análisis

**REAL.** `ya_estaba` distingue las dos respuestas que existen: la del
camino normal, con su dry-run que hay que leer antes de confirmar, y la de R24,
resuelta desde la traza sin llamar a nadie. En verdadero, el front escondería el
dry-run que alguien tiene que leer. El caso contrario (`ya_estaba: True` en la
rama de R24) sí estaba cazado.

**Tests que lo matan**: `test_f012_r21_el_dry_run_normal_no_dice_que_el_parte_ya_estuviera_dentro`
y `test_f012_r16_una_reclamacion_ya_cerrada_se_devuelve_en_verde_y_lo_dice`.
