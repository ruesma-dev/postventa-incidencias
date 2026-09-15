<!-- progress/explore_F-009_timeouts.md -->
# F-009 · Diagnóstico de los 15 timeouts de la campaña de mutación (T28)

> Subagente de investigación, 2026-09-02. **Diagnóstico, no arreglo**: no se ha
> tocado ni una línea de producción ni de tests. El árbol queda limpio.

## 1. La causa, en una frase

**No hay ningún cuelgue.** La suite del servicio `api` tarda **38,7 s** en
verde ella sola, y la campaña la ejecuta con **16 workers simultáneos**, cada
uno en su `git worktree`. Con esa concurrencia la misma suite pasa a tardar
**125–135 s**, es decir, **por encima del límite de 120 s por mutante** de
`harness/rigor.json`. Todo mutante cuya muerte no llegue hasta bien entrada la
suite agota el límite y se anota como `timeout` sin haber fallado nada.

El veredicto `timeout` de esta campaña **no dice nada del mutante**: dice que
en ese instante había 16 suites peleándose por la máquina. Es **no
determinista**: los mismos mutantes salen `muerto`, `superviviente` o
`timeout` según la carga del momento (§4, prueba decisiva).

## 2. Qué se midió, con qué comando y qué salió

Todo con el intérprete real del servicio
(`services/postventa-api/.venv/Scripts/python.exe`) y **el mismo comando que
lanza el arnés** (`harness/mutacion.py`, clase `EjecutorPytest`):

```
python -m pytest -x -q --tb=no -p no:cacheprovider      # cwd: services/postventa-api
                                                        # env: PYTHONDONTWRITEBYTECODE=1
```

| # | Medición | Comando / condición | Resultado |
|---|---|---|---|
| 1 | Baseline de la suite | 1 proceso, árbol principal | **38,7 s** · 1594 pasados, 13 saltados |
| 2 | Mutante `function_app.py:704` 400→401 | 1 proceso, árbol principal | **37,0 s** → **FALLA** `test_f009_ruta_http.py::test_f009_r47_un_cuerpo_que_no_es_json_es_400` (76 % de la suite) |
| 3 | Mutante `cierre.py:320` `==`→`!=` | 1 proceso, árbol principal | **22,6 s** → **FALLA** `test_f009_cerrar_http.py::test_f009_r48_una_reclamacion_que_no_admite_cierre_tambien` (62 % de la suite) |
| 4 | Contención 16× (árbol principal) | 16 suites limpias a la vez | 85–97 s, media **92,9 s** (factor 2,4×) |
| 5 | **Contención 16× en worktrees** (condiciones reales de la campaña) | 16 worktrees, suite limpia | 125–135 s, media **131,6 s** (factor **3,4×**) → **16 de 16 por encima de 120 s** |
| 6 | Contención 16× en worktrees, mutante `fa:704` aplicado | 16 worktrees | 99–104 s, media **102,5 s** (factor 2,8×) |
| 7 | Contención **8×** en worktrees, suite limpia | 8 worktrees | 77,0–77,9 s, media **77,4 s** (factor 2,0×) → 0 de 8 por encima |
| 8 | ¿El límite corta de verdad? | `EjecutorPytest.ejecutar(5/10/20)` | corta en 5,0 / 10,0 / 20,0 s exactos. **El timeout funciona bien** |
| 9 | Coste de los worktrees | crear y retirar 16 | **9,7 s** crear, **2,4 s** retirar |
| 10 | Peso de los tests de barrido | suite sin los 5 ficheros `*_arquitectura.py` / `*_repo_sin_identificadores.py` | **17,3 s** (frente a 38,7 s): **el 55 % del tiempo de la suite son 67 tests que recorren el repositorio entero** |

Scripts usados (en el scratchpad de la sesión, fuera del repositorio):
`contencion.py` y `contencion_worktrees.py`.

## 3. Hipótesis descartadas, con la evidencia

- **«Reintentos de `tenacity` al desviar el código de estado»** (la hipótesis
  anotada en `current.md`): **falsa**. Medición 2 y 3: los dos mutantes
  reproducidos mueren limpiamente en 37,0 s y 22,6 s, y el test que los mata es
  exactamente el que comprueba el código HTTP. No hay reintento, ni espera, ni
  bucle: fallan en el `assert` del código de estado.
- **«Un `sleep` real o un test mal aislado»**: no hay ni un `subprocess`, ni un
  `sleep(`, ni un `Popen` en `services/postventa-api/tests/` (grep). La suite de
  base de datos (`tests_bbdd/`) se salta entera sin `POSTVENTA_PG_TEST_DSN`.
- **«El límite de 120 s no se aplica bien»**: falso, medición 8. Corta al
  segundo exacto y el `kill` no se va de tiempo ni con 16 muertes simultáneas
  (medición de §4: 2 rondas = 12 s + 118 s + 120 s = 250 s reales).
- **«Coste de arranque de los worktrees»**: 12,1 s en total para los 16
  (medición 9). Irrelevante.

## 4. La prueba decisiva: el veredicto `timeout` es una lotería

Se lanzó una campaña **parcial** con el comando real del arnés y su
configuración real (16 workers, 120 s), muestreando 32 mutantes:

```
python -m harness.mutacion --feature F-009 --max-mutantes 32 --semilla 11 --salida <scratchpad>
```

Resultado: **16 muertos y 16 timeouts en 249,8 s**. Y el reparto no es
aleatorio: **los 16 primeros en terminar murieron; los 16 de la segunda ronda
—arrancados todos a la vez, con la máquina saturada— agotaron los 120 s sin
excepción**.

Lo importante es **quiénes** son esos 16 timeouts, comparados con el veredicto
que les dio la campaña de T28:

| Mutante | Veredicto en T28 (2026-08-27) | Veredicto ahora |
|---|---|---|
| `escrituras.py:206` (×3), `escrituras.py:207` (×2), `escrituras.py:213`, `:240` | **muerto** | **timeout** |
| `consultas.py:143`, `:146`, `:161` | **muerto** | **timeout** |
| `cerrar.py:147`, `:156`, `:186` | **muerto** | **timeout** |
| `cliente.py:359` | **muerto** | **timeout** |
| `fabrica.py:130`, `cerrar.py:219` | **superviviente** (equivalente justificado) | **timeout** |
| `cierre.py:321` [comparación] | **timeout** | **muerto** |

Un mutante que la campaña anterior dio por muerto sale ahora `timeout`, y uno
de los quince timeouts sale ahora muerto. **El veredicto depende de la carga,
no del mutante.** Con esto, la hipótesis del cuelgue queda cerrada.

## 5. Por qué cayeron justo esos 15, y no otros

Dos hechos que se multiplican:

1. **`pytest -x` para en el primer fallo**, así que lo que cuesta un mutante es
   *cuánta suite hay que recorrer hasta el test que lo mata*, no la suite
   entera.
2. **El orden de recolección es alfabético por fichero.** Los tests de F-009
   están en la cola: de los 82 ficheros de `tests/`, `test_f009_cerrar_http.py`
   es el **56** y `test_f009_ruta_http.py` el **66**. Son los dos ficheros que
   matan, respectivamente, a los mutantes de `domain/models/cierre.py` y a los
   de `function_app.py`.

Es decir: los 15 mutantes que agotaron el límite son **los que necesitan
recorrer más suite antes de morir** (62 % y 76 %), y con el factor 3,4× de la
concurrencia se plantan en 110–130 s contra un tope de 120 s. Los mutantes que
mueren en tests anteriores (F-001 a F-006) terminan mucho antes y sobreviven al
tope. Los 6 supervivientes recorren el 100 % de la suite y deberían haber caído
también: se salvaron por milímetros, porque la contención no es constante a lo
largo de la campaña (al final quedan menos workers activos).

**Conclusión operativa: la campaña de T28 está funcionando al filo del
límite.** No hay 15 casos raros; hay 123 mutantes que tardan entre 100 y 135 s
contra un tope de 120 s, y quince cayeron del lado malo.

## 6. Una anomalía que conviene anotar (no cambia el diagnóstico)

`current.md` y el informe dicen **3.623,4 s** de tiempo total. Ese número **no
cuadra con una campaña de 16 workers**: con 123 mutantes repartidos en
round-robin, ningún worker evalúa más de 8, y ningún mutante puede pasar de
120 s porque el tope corta (medición 8). El techo teórico es
`8 × 120 s + 12 s de worktrees ≈ 972 s`, y la campaña parcial de §4 lo confirma
(2 rondas = 249,8 s ≈ 2 × 120 + 12). Los 3.623 s son **3,7 veces ese techo**.

Lecturas posibles: que la campaña se lanzara con `--workers` reducido (en serie,
123 mutantes a ~29,5 s de media dan 3.630 s, que cuadra al 0,4 %), o que la
máquina estuviera haciendo otra cosa. **No se ha podido determinar cuál**: no
queda registro de la línea `Campaña paralela: hasta N workers` de aquella
ejecución. Recomendación barata: en la próxima campaña, **guardar esa línea**
junto al informe.

## 7. Opciones de arreglo, con su coste (ninguna implementada)

Ordenadas por relación coste/beneficio.

### A · Bajar los workers de 16 a 8 — *recomendada como arreglo inmediato*

`harness/rigor.json` → `mutacion.workers: 8` (la clave existe y tiene
precedencia sobre el default), o `--workers 8` en la línea de comandos.

- **Efecto medido**: la suite baja de 131,6 s a **77,4 s** (medición 7), un
  margen del 55 % contra el tope. Los 15 timeouts desaparecen.
- **Coste en tiempo de campaña**: **casi nulo**. Rendimiento con 16 workers:
  16/131,6 = 0,122 suites/s; con 8: 8/77,4 = 0,103 suites/s. Se pierde un
  **18 %** de rendimiento, no la mitad: a 16 workers la máquina ya está saturada
  y el paralelismo extra solo alarga cada suite.
- **Riesgo**: ninguno sobre el código. Es configuración del arnés.
- **Ojo**: es específico de esta máquina (22 CPUs) y de lo grande que se ha
  hecho esta suite; ver la opción D para el arreglo genérico.

### B · Subir el timeout por mutante

`harness/rigor.json` → `mutacion.timeout_por_mutante_s: 300`.

- **Efecto**: 300 s da 2,3× de margen sobre el peor caso medido (135 s).
- **Coste**: solo se paga cuando se agota. Un cuelgue de verdad costaría 300 s
  en vez de 120 s (con 15 casos, +45 min en el peor escenario imaginable).
- **Contra**: tapa el síntoma sin arreglar la saturación, y **alarga el lazo de
  seguridad que existe justamente para detectar un cuelgue real**. Si se elige,
  mejor combinada con A.

### C · Relanzar solo esos 15 mutantes, para cerrar T28 ya

`python -m harness.mutacion --feature F-009 --workers 4` (o `--workers 1`),
que con 123 mutantes tarda más, o esperar a A/B y repetir la campaña completa.

- **Coste**: con `--workers 8` la campaña completa se estima en **~18–20 min**
  (123 mutantes × ~77 s ÷ 8), frente a los 60 min declarados en T28.
- **Aviso**: la CLI **no sabe acotar por fichero**; `--max-mutantes` muestrea al
  azar, no filtra. Para reevaluar exactamente esos 15 hace falta o la campaña
  completa o una opción nueva (ver D).

### D · Arreglo genérico del arnés, para portar a `arnes-base`

Tres ideas, de menor a mayor esfuerzo:

1. **Reevaluar los timeouts en serie antes de dar el informe.** Al terminar la
   campaña, volver a pasar los mutantes `timeout` de uno en uno (sin
   concurrencia). Es el arreglo correcto: un `timeout` deja de ser un veredicto
   y pasa a ser un reintento. Coste: ~30 líneas en
   `harness/mutacion_paralela.py`; en tiempo, 15 mutantes × ~35 s ≈ 9 min.
2. **Calibrar los workers midiendo la suite una vez** al arrancar la campaña
   (baseline solo) y elegir `workers` tal que `baseline × factor < timeout`.
   Coste: un pase de suite (~40 s) más lógica de decisión.
3. **Filtro `--ficheros`** en la CLI, para reevaluar un subconjunto sin repetir
   la campaña entera. Coste: pequeño; utilidad, alta y recurrente.

### E · Acelerar la suite (ataca la raíz, y sirve a todo el proyecto)

Medición 10: **el 55 % de los 38,7 s son 67 tests de 5 ficheros** que recorren
el repositorio entero fichero a fichero:

- `tests/test_f003_arquitectura.py::test_f003_r8_ningun_modulo_incrusta_el_texto_del_prompt` — **12,7 s él solo, un tercio de la suite**
- `tests/test_f006_repo_sin_identificadores.py` (3 tests, ~4 s)
- `tests/test_f006_arquitectura.py`, `tests/test_f009_arquitectura.py`,
  `tests/test_f005_arquitectura.py` (~4 s entre los tres)

Todos hacen el mismo barrido del árbol y lo repiten en cada test. Cachear el
recorrido en una fixture de sesión (leer el árbol UNA vez y que cada test
consulte el resultado) dejaría la suite en torno a **20 s**, y con ello la
campaña a 16 workers volvería a caber de sobra en 120 s.

- **Coste**: tocar tests de F-003, F-005, F-006 y F-009 (features cerradas), con
  el riesgo de aflojar sin querer una comprobación de arquitectura. **Requiere
  su propia feature y su review**; no es un cambio para meter dentro de T28.
- **Beneficio**: no es solo la mutación; es cada `init.sh` de cada sesión.

## 8. Recomendación para cerrar T28

**A + C**: declarar `mutacion.workers: 8` en `harness/rigor.json` y repetir la
campaña completa (~20 min estimados). Si aun así apareciera algún timeout, es
que hay algo más y entonces sí toca mirar ese mutante concreto. Anotar en el
informe la línea de workers que imprime el comando.

D.1 (reevaluar timeouts en serie) es la mejora que **de verdad** cierra el
agujero —hoy un `timeout` es un veredicto sin valor— y, por la regla de
propagación, va a `arnes-base`. E queda como feature aparte.

## 9. Estado del árbol al terminar

- Las dos mutaciones aplicadas a mano (`function_app.py:704` y
  `domain/models/cierre.py:320`) se revirtieron con `git checkout --` justo
  después de cada medición; se comprobó `git status --porcelain` vacío en las
  dos ocasiones.
- Los worktrees creados para las mediciones se retiraron con el propio
  `Worktrees` del arnés; `git worktree list` muestra solo el árbol principal.
- Los informes de las campañas de prueba se escribieron **en el scratchpad**,
  no en `progress/`: `progress/mutacion_F-009.md` sigue intacto.
- Único fichero añadido: este informe.
