<!-- progress/impl_arnes_reintento_timeouts.md -->
# Mejora del arnés · un `timeout` deja de ser un veredicto

> Trabajo de arnés, no de feature. Rama `feature/F-009-cierre-sigrid` (el humano
> pidió no mover `dev`). **No se ha tocado nada de F-009**: ni su código, ni sus
> tests, ni `specs/F-009-cierre-sigrid/`, ni su estado en `features.json`, ni se
> ha relanzado su campaña de mutación.

Contexto: `progress/explore_F-009_timeouts.md`. Resumen de la causa: la suite del
servicio `api` tarda **38,7 s** sola y **131,6 s** con 16 workers, contra un tope
de **120 s** por mutante; tres campañas de la misma feature y el mismo commit
dieron **15, 27 y 0 timeouts** sobre mutantes distintos cada vez.

## 1. Qué cambió, pieza a pieza

### Pieza 1 · `harness/alcance.py` — el arnés fuera del alcance (`652e107`)

`DIRECTORIOS_EXCLUIDOS` pasa de `("tests", "specs", "progress", "docs")` a
incluir `"harness"`.

**Por qué va primero y en su propio commit**: sin él, los commits 2 y 3 de este
mismo trabajo habrían metido código del arnés en el alcance de F-009 —la rama en
la que estoy—, y entonces la campaña de mutación se mutaría a sí misma y la
puerta de cobertura mediría la herramienta en vez del producto. Es lo que hace
legítimas a las otras dos piezas en esta rama.

Comprobado lo que pedía el encargo:

- **La comparación es por SEGMENTO de ruta a cualquier profundidad**, tal y como
  el módulo llevaba documentado: `es_produccion` parte la ruta por `/` (tras
  normalizar `\`), descarta el último elemento (el nombre del fichero) y busca
  coincidencia exacta de segmento. Verificado con casos: `harness/mutacion.py` y
  `services/postventa-api/harness/parche.py` NO son producción; `app/harness.py`
  (el nombre no cuenta), `harnesses/util.py` y `mi_harness/util.py` (no vale
  como prefijo) SÍ lo son.
- **NO existía ningún test que fijara esa regla.** El módulo la documentaba y
  nadie la sostenía. Ahora la sostiene `tests/test_alcance_excluidos.py`
  (18 tests), que es la mitad menos vistosa y más valiosa de este commit.

### Pieza 2 · `harness/mutacion_paralela.py` — repaso en serie (`edf3dfc`)

Tras fusionar los parciales y **antes** de devolver, el coordinador vuelve a
juzgar los mutantes en `timeout` **uno a uno, sin concurrencia**, y sustituye el
no-veredicto por el real.

- **`reemplazar_timeouts(informe, reintento) -> InformeMutacion`**, pura: solo
  cambia **cómo se reparten**. `generados` y `mutantes_evaluados` no se tocan
  —nadie se evalúa dos veces ni desaparece—, las listas se reordenan con
  `clave_estable` igual que hace `fusionar`, y **los segundos se suman**.
  Esto último no estaba en el encargo y lo justifico: el repaso cuesta minutos
  reales y esconderlos falsearía la media por mutante, que es justo la señal con
  la que `CHECKPOINTS.md` (C4 bis) detecta una campaña que no midió lo que dice.
- **Dónde corre**: dentro del `with Worktrees`, sobre `rutas[0]`, reutilizando
  `ejecutar_campania` tal cual igual que hace `correr()`. El árbol principal no
  se muta nunca en modo paralelo y esa garantía no se rompe ni para esto: hay un
  test que la sostiene (`test_el_repaso_nunca_muta_el_arbol_principal`), que
  además comprueba `git status --porcelain` vacío al terminar.
- **Lo que sigue en `timeout` tras el repaso se queda en `timeout`**: eso ya sí
  es señal de un cuelgue real, y el informe lo dice con esas palabras (pieza 3).
- **Eco**: `eco_del_repaso(eco, total)` da numeración propia y antepone la marca
  `repaso`. La numeración de la campaña ya se cerró cuando el repaso empieza, así
  que seguir contando sobre ella daría un `[i/n]` fuera de rango.
- **Caso degenerado (`efectivo < 2`, campaña in situ): NO se repasa, a
  propósito**, y queda documentado en el código. Sin concurrencia, el repaso
  repetiría exactamente la misma medición que acaba de hacerse: un `timeout` en
  serie ya es el veredicto que el repaso buscaba, y repetirlo solo duplicaría el
  coste del único caso en que de verdad hay un cuelgue. Por eso
  `timeouts_repasados` se queda en cero, y el informe distingue por escrito
  «no hizo falta» de «esta campaña no repasa».

### Pieza 3 · `harness/mutacion.py` — el informe declara sus condiciones (`e48b318`)

- `InformeMutacion.workers`: los **efectivos**, no los pedidos (pedir 16 con 4
  mutantes arranca 4). Lo pone `fusionar` en modo paralelo y `main` en serie.
- **Cabecera**: `comando_de(informe)` cita el comando entero, `--workers N`
  incluido. Es lo que pedía T28 y lo que faltó el 2026-09-02 para reconstruir la
  campaña del 2026-08-27.
- **Totales**: fila `| Workers | N |`, con `n/d` cuando nadie lo dijo. Una fila
  ausente se lee como descuido; un `n/d` se lee como lo que es.
- **Totales**: fila `| Timeouts repasados en serie | ... |`, siempre presente,
  con sus tres redacciones reales (cuántos se repasaron y a cuántos les sacó
  veredicto / «no hizo falta» / «campaña en serie, no se repasa»).
- **Sección «Timeouts»**: dice si esos mutantes ya sobrevivieron al repaso, que
  es lo que decide si son ruido o un cuelgue.

### Ajuste posterior (`2c2bcf9`)

`reemplazar_timeouts` pasa a construir el informe con `dataclasses.replace` en
vez de enumerar los campos a mano. Enumerar funciona hoy y falla en silencio
mañana: el día que `InformeMutacion` gane un campo, el informe corregido lo
perdería sin que nada se pusiera rojo. Es además la forma en que se portó a
`arnes-base`, donde el dataclass tiene diez campos más.

## 2. Fase RED, con la salida pegada

### Pieza 1

```
$ python -m pytest tests/test_alcance_excluidos.py -q --tb=short
...
E   AssertionError: assert True is False
E    +  where True = es_produccion('harness/mutacion.py')
...
E   AssertionError: assert {'harness/mut...pp.py': {704}} == {'services/po...pp.py': {704}}
E     Left contains 1 more item:
E     {'harness/mutacion_paralela.py': {10, 11}}
=========================== short test summary info ===========================
FAILED tests/test_alcance_excluidos.py::test_harness_esta_entre_los_directorios_excluidos
FAILED tests/test_alcance_excluidos.py::test_ningun_fichero_del_arnes_es_produccion[harness/mutacion.py]
FAILED tests/test_alcance_excluidos.py::test_ningun_fichero_del_arnes_es_produccion[harness/mutacion_paralela.py]
FAILED tests/test_alcance_excluidos.py::test_ningun_fichero_del_arnes_es_produccion[harness/alcance.py]
FAILED tests/test_alcance_excluidos.py::test_ningun_fichero_del_arnes_es_produccion[harness\\alcance.py]
FAILED tests/test_alcance_excluidos.py::test_ningun_fichero_del_arnes_es_produccion[services/postventa-api/harness/parche.py]
FAILED tests/test_alcance_excluidos.py::test_filtrar_produccion_saca_el_arnes_del_mapa_de_lineas
7 failed, 11 passed in 0.14s
```

Tras el cambio: `35 passed in 0.52s` (los 17 de antes más los 18 nuevos).

### Pieza 2

Primer RED, al no existir la función:

```
$ python -m pytest tests/test_mutacion_repaso_timeouts.py -q --tb=line
E   ImportError: cannot import name 'reemplazar_timeouts' from 'harness.mutacion_paralela'
1 error in 0.26s
```

Ese `ImportError` tapa todo el fichero, así que **no vale como prueba de que los
tests del coordinador miden algo**. Segundo RED, con la función ya escrita y el
repaso desactivado a mano (`return informe` en vez de
`return repasar(informe, rutas[0])`), sobre worktrees de verdad:

```
$ python -m pytest tests/test_mutacion_repaso_timeouts.py -q --tb=line
........FF.F                                                             [100%]
tests\test_mutacion_repaso_timeouts.py:272: AssertionError: assert [Mutante(fich...stituto='>=')] == []
tests\test_mutacion_repaso_timeouts.py:282: AssertionError: assert [Mutante(fich...stituto='>=')] == []
tests\test_mutacion_repaso_timeouts.py:316: AssertionError: el repaso se repartió entre {'...\mutacion_F-000_twt6jyo7\wk_0', '...\mutacion_F-000_twt6jyo7\wk_1'}
FAILED tests/test_mutacion_repaso_timeouts.py::test_la_campania_paralela_repasa_los_timeouts_antes_de_dar_el_informe
FAILED tests/test_mutacion_repaso_timeouts.py::test_el_repaso_destapa_a_los_supervivientes_que_el_timeout_escondia
FAILED tests/test_mutacion_repaso_timeouts.py::test_el_repaso_se_hace_en_un_solo_worktree
3 failed, 9 passed in 2.12s
```

Restaurada la línea: `12 passed in 2.98s`.

### Pieza 3

```
$ python -m pytest tests/test_mutacion_informe_workers.py -q --tb=line
...
TypeError: InformeMutacion.__init__() got an unexpected keyword argument 'workers'
AssertionError: assert '| Workers | n/d |' in '<!-- ...mutacion_F-000.md...'
TypeError: fusionar() got an unexpected keyword argument 'workers'
AssertionError: assert 'Timeouts repasados en serie' in '<!-- ...'
StopIteration
AttributeError: 'InformeMutacion' object has no attribute 'workers'
=========================== short test summary info ===========================
FAILED ...::test_la_cabecera_cita_el_comando_con_sus_workers
FAILED ...::test_los_totales_traen_la_fila_de_workers
FAILED ...::test_sin_saber_los_workers_la_fila_lo_dice_en_vez_de_faltar
FAILED ...::test_fusionar_registra_los_workers_de_la_campania
FAILED ...::test_el_informe_dice_cuantos_timeouts_se_repasaron_y_cuantos_cambiaron
FAILED ...::test_sin_un_solo_timeout_la_fila_del_repaso_lo_dice
FAILED ...::test_una_campania_en_serie_explica_por_que_no_repasa
FAILED ...::test_la_seccion_de_timeouts_avisa_de_que_sobrevivieron_al_repaso
FAILED ...::test_la_campania_registra_los_workers_que_de_verdad_corrieron
9 failed in 0.86s
```

Un décimo fallo apareció ya en verde y merece constar, porque es el caso en que
el test estaba peor escrito que el código:
`test_la_seccion_de_timeouts_avisa_de_que_sobrevivieron_al_repaso` exigía la
palabra literal `repaso` y la prosa dice «al repasarlos en serie». Se relajó la
aserción a la raíz `repas` más `serie` —el hecho, no la redacción—, y NO se
tocó el texto del informe.

## 3. Qué se verificó, con qué resultado real

| Verificación | Resultado |
|---|---|
| `bash harness/init.sh` (final) | **verde**; cobertura 98,8 % de 572 líneas cambiadas (565/572, umbral 80 %, nivel crítico) |
| Suite raíz | **56 pasados** en 4,4 s (eran 17 antes de este trabajo) |
| Suites de servicio (`api`, `front`) | en verde, servidas desde caché: **este trabajo no toca `services/`** |
| `ruff` en el repositorio | **58 avisos, exactamente los mismos de antes** (deuda previa). Comprobado con `git stash` |
| `ruff` sobre los ficheros escritos | `All checks passed!` |
| Repaso de verdad, con worktrees | los tests del coordinador crean 2 `git worktree` reales sobre un repo de juguete en `tmp_path` |
| Árbol limpio tras la campaña de prueba | comprobado dentro del test con `git status --porcelain` |

Hubo un intento fallido intermedio que conviene anotar: la primera redacción de
la sección «Timeouts» subió ruff de 58 a **60** avisos (dos `ISC004`,
concatenación implícita de cadenas dentro de una lista, el mismo patrón que la
deuda previa de alrededor). Se parentizaron las dos cadenas y volvió a 58. No se
«heredó» el estilo malo por estar rodeado de él.

**No se relanzó la campaña de mutación de F-009** (102 minutos, y está cerrada).
La prueba del repaso se hace con dobles, como pedía el encargo.

## 4. Qué se portó a `arnes-base`, y con qué commit

Commit **`685da06`** en `C:\Users\pgris\PycharmProjects\arnes-base`, sellado como
**1.7.8 (2026-09-02)**. Local, sin `push`.

Lo primero fue mirar cómo está organizado y **si los ficheros coinciden**: no
coinciden. `arnes-base` va por la **1.7.7** y este repositorio por la **1.5.2**,
así que el cambio se portó **pieza a pieza y no fichero a fichero**. Diferencias
que obligaron a adaptar:

1. **La pieza 3 estaba a medias allí.** `InformeMutacion.workers` y la fila
   `| Workers |` existen en `arnes-base` desde la 1.7.2. Lo que faltaba —y se
   portó— es el `--workers` en la cabecera y toda la parte del repaso.
2. **`FILAS_DE_RELOJ`.** `arnes-base` tiene un test de paridad serie/paralelo que
   compara los dos informes ignorando las filas que dependen de *cómo* se corrió
   la campaña. La fila nueva `Timeouts repasados en serie` es una de ellas (en
   serie no hay repaso), así que **hubo que declararla ahí** o el test se habría
   vuelto flaky. Es literalmente el fallo que esa constante documenta.
3. **`reemplazar_timeouts` con `replace`.** Allí `InformeMutacion` tiene diez
   campos más (`sha_head`, `segundos_linea_base`, `timeout_efectivo`, `nivel`,
   `base_rota`...). Un constructor con los campos a mano los habría perdido.
   Después alineé también la versión local (commit `2c2bcf9`).
4. **Línea base y `BaseRota`.** Desde la 1.5.3, `ejecutar_campania` mide una
   línea base antes de juzgar y aborta si no está verde. El repaso la mide
   también, lo cual es bueno (sin contención, el timeout derivado sale más
   ajustado), pero un `BaseRota` ahí tiraría por la borda una campaña de horas ya
   completada. **Decisión: se captura y se devuelve la campaña tal cual**, con
   sus timeouts sin aclarar y un aviso por pantalla. Es una divergencia
   deliberada respecto a la versión local, que no tiene línea base.
5. **El eco del repaso ignora las líneas de línea base** (`MARCA_LINEA_BASE`), como
   ya hace `eco_compartido` allí: no son mutantes y numerarlas descuadra el `[i/n]`.

### La tensión que destapó el port, y cómo se resolvió

Portar la pieza 1 **puso rojos 4 tests** de `arnes-base`. La causa no es un
descuido: en `arnes-base` **todo el código de producción vive en `harness/`** —el
arnés es el producto, no el utillaje—, y su bandera `--ficheros` existe, según su
propio docstring, «para medir si la maquinaria del arnés está protegida por sus
tests». Excluir `harness` a secas dejaba al arnés incapaz de medirse a sí mismo.

Resolución, que creo que es la correcta y no un parche: **la exclusión protege el
alcance AUTOMÁTICO** —el que sale del diff, que nadie eligió y que arrastra el
arnés en cuanto una rama lo toca—, **no el que declara una persona a mano**. Se
añadió `DIRECTORIOS_EXCLUIDOS_AL_DECLARAR` (sin `harness`), que usa solo
`alcance_de_ficheros`, y `es_produccion` acepta la lista como parámetro. Sigue
rechazando `tests`, `specs`, `progress` y `docs`: mutar un test no significa
nada, lo pida quien lo pida. Cinco tests nuevos lo fijan.

Esta pieza **no aplica a este repositorio**, que va por la 1.5.2 y no tiene
`--ficheros`. Es divergencia legítima, no olvido.

### Verificación en `arnes-base`

- Suite del payload: **341 pasados, 1 saltado** en 44 s (299 antes de este
  trabajo, más 42 tests nuevos en tres ficheros).
- `ruff`: **39 avisos antes y después**, comprobado con `git stash`. Los ficheros
  escritos pasan limpios.
- **RED también allí**: desactivando `repasar(...)` caen los 3 tests del
  coordinador, con el mismo mensaje que en este repositorio.
- **Finales de línea**: `arnes-base` usa LF (`.gitattributes`: `*.py text eol=lf`).
  Los dos ficheros de test que llegaron por copia desde aquí venían en CRLF y se
  normalizaron a LF antes de commitear. El diff de los tres módulos del arnés es
  quirúrgico (252 inserciones, 16 borrados): no se reescribieron enteros.
- El instalador recorre el payload con `Get-ChildItem -Recurse`, así que los tres
  ficheros de test nuevos entran solos: no hay lista de ficheros que mantener.

### Versionado: qué se hizo y qué NO

- **Sí**: `arnes-base/harness/VERSION` → `ARNES_VERSION=1.7.8`,
  `ARNES_FECHA=2026-09-02`, y una entrada nueva en `GUIA_INSTALACION.md`
  siguiendo la plantilla de la 1.7.7 (qué pasaba, la medición, el arreglo, las
  decisiones que conviene dejar escritas, qué revisar al actualizar, ficheros y
  origen). Es la convención que el repositorio ha seguido en las 20 versiones
  anteriores.
- **`1.7.8` y no `1.8.0`** porque `ENCARGO_1.8.0_adelgazar_arnes.md` tiene ese
  número reservado para otro trabajo ya planificado.
- **NO** se ha tocado `harness/ARNES_VERSION.md` de este repositorio: lo escribe
  el instalador y no se edita a mano. Queda abierto abajo.

## 5. Ficheros tocados

**`postventa-incidencias`** (4 commits, ninguno toca `services/`):

| Fichero | Qué |
|---|---|
| `harness/alcance.py` | `harness` en `DIRECTORIOS_EXCLUIDOS` + docstring |
| `harness/mutacion_paralela.py` | `reemplazar_timeouts`, `eco_del_repaso`, `repasar`, cabecera del módulo, `workers` en `fusionar` |
| `harness/mutacion.py` | `timeouts_repasados`, `timeouts_resueltos`, `workers`, `comando_de`, `fila_del_repaso`, sección «Timeouts», `workers = 1` en la rama en serie |
| `tests/test_alcance_excluidos.py` | **nuevo**, 18 tests |
| `tests/test_mutacion_repaso_timeouts.py` | **nuevo**, 12 tests |
| `tests/test_mutacion_informe_workers.py` | **nuevo**, 9 tests |

**`arnes-base`** (1 commit): `arnes-base/harness/{alcance,mutacion,mutacion_paralela}.py`,
`arnes-base/tests/{test_alcance_excluidos,test_mutacion_repaso_timeouts,test_mutacion_informe_repaso}.py`
(nuevos), `GUIA_INSTALACION.md`, `arnes-base/harness/VERSION`.

## 6. Evidencias

| Evidencia | Valor |
|---|---|
| Tests ejecutados (raíz, `postventa`) | **56 pasados**, 0 fallos, 4,4 s |
| Tests ejecutados (payload de `arnes-base`) | **341 pasados**, 1 saltado, 44 s |
| Cobertura de las líneas cambiadas | **98,8 %** (565/572, umbral 80 %) — línea `PUERTA COBERTURA` de `init.sh` |
| Mutantes generados y supervivientes | **no medido, a propósito** (ver abajo) |
| Tiempo de ejecución de la suite | raíz: **4,4 s**; `api` y `front`: servidas desde caché, sin cambios en su árbol |

Sobre la **campaña de mutación**: no se ha lanzado, y no es un descuido.

1. El encargo prohíbe expresamente relanzar la campaña de F-009 (102 minutos, ya
   cerrada), y este trabajo no es una feature con su propia entrada en
   `features.json` contra la que calcular un alcance.
2. **Y, sobre todo, la pieza 1 de este mismo trabajo deja `harness/` fuera del
   alcance de cualquier feature**: aunque se lanzara `python -m harness.mutacion
   --feature F-009`, no generaría ni un mutante de este código. Es el
   comportamiento buscado, no una limitación.
3. La cobertura del 98,8 % que declara `init.sh` mide las 572 líneas de F-009 y
   **no incluye** las líneas escritas hoy, por lo mismo.

Lo que sí sostiene este código es su suite: **39 tests nuevos aquí** (18 + 12 + 9)
y **42 en `arnes-base`** (23 + 12 + 7), con fase RED pegada arriba y, en las dos piezas de comportamiento,
un RED *específico* obtenido desactivando la línea que hace el trabajo.

## 7. Qué queda abierto

1. **`harness/ARNES_VERSION.md` de este repositorio no se ha tocado**, siguiendo
   la instrucción de que lo escribe el instalador. Queda desactualizado en un
   punto concreto y conviene decidirlo: este repositorio lleva ahora, aplicadas a
   mano, **tres piezas de la 1.7.8** que ese fichero no menciona. Tiene
   precedente exacto (el «parche de la 1.6.3» está anotado ahí de esa forma), así
   que la opción natural es añadir un párrafo equivalente. **No lo he hecho por
   no improvisar sobre un fichero que la instrucción marca como del instalador.**
2. **`DIRECTORIOS_EXCLUIDOS_AL_DECLARAR` no existe aquí**, porque este
   repositorio no tiene `--ficheros` (llegó en la 1.7.1). Si algún día se
   actualiza el arnés de este proyecto, viene incluido.
3. **La recomendación operativa del diagnóstico sigue en pie y no la he
   aplicado**: `mutacion.workers: 8` en `harness/rigor.json`. El repaso hace que
   un timeout ya no falsee el resultado, pero **no** evita pagarlo en tiempo;
   bajar a 8 workers daba un margen del 55 % contra el tope por solo un 18 %
   menos de rendimiento. Es un cambio de configuración de una línea que no
   estaba en este encargo.
4. **La opción E del diagnóstico** (el 55 % del tiempo de la suite son 67 tests
   que barren el repositorio entero, cacheables en una fixture de sesión) sigue
   pidiendo su propia feature. Ataca la raíz y beneficia a cada `init.sh`.
5. **Ninguna verificación MANUAL pendiente.** Nada de esto toca red, ERP, BBDD,
   SharePoint ni IA.
