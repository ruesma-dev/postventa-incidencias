<!-- progress/review_F-030.md -->
# F-030 · Review — **APROBADO**

> Revisado el 2026-09-16 sobre `feature/F-030-veredicto-persistido`, HEAD
> `9e30f57`, árbol limpio, base `dev` (`55721f3`).
>
> **Ni una llamada real**: ni Azure, ni Sigrid, ni SharePoint, ni el
> PostgreSQL compartido. Todo contra el código, los documentos y dobles en
> memoria. Las dos ventanas de escritura siguen abiertas en `dev` y esta
> review no ha tocado ninguna.

---

## Veredicto

**APROBADO.** El arreglo arregla, está probado por una red que caza el defecto
—lo he reproducido yo—, y **ninguna puerta se ha aflojado**: en los 14 ficheros
de tests tocados solo desaparecen **tres asertos**, y los tres se sustituyen por
otros más fuertes.

Quedan dos observaciones de mejora al final, **ninguna bloqueante**, y las dos
verificaciones `MANUAL (humano)` V1 y V2, que exigen el entorno desplegado y no
las puede ejecutar un agente.

## Nivel de rigor

`harness/features.json` declara **`rigor: "critico"`** para F-030. Exige, según
`harness/rigor.json` y la tabla de `CHECKPOINTS.md`: **fase RED**, **cobertura**
de las líneas cambiadas ≥ 80 %, **campaña de mutación** con **cero
supervivientes** sin justificación escrita, y las verificaciones
`MANUAL (humano)` listadas con su comando y su resultado. Las cuatro puertas se
han comprobado, y tres de ellas **reejecutándolas yo**.

---

## Lo que he verificado por mi cuenta (no leyendo el informe)

### 1 · El arreglo arregla, y la red lo prueba

**El centinela estructural de T12 (R3) caza el stub.** Reintroducido el
`ResultadoValidacion` de pega en `archivar.py`, en un **worktree aislado**:

```
E  AssertionError: estos módulos del borde fabrican un ResultadoValidacion, y eso es
   exactamente lo que rompió el circuito en F-030: el veredicto lo emite F-004 con la
   extracción, o se lee de la base. {'archivar.py': [213]}
E  assert {'archivar.py': [213]} == {}
FAILED tests/test_f030_veredicto_persistido.py::test_f030_r3_ningun_modulo_del_borde_construye_un_veredicto
```

(La línea es 213 y no 208 porque mi parche añade una línea de import; es el
mismo punto.) Comprobado además que **recorre la carpeta entera**: metiendo el
stub en `cerrar.py` lo caza igual → `{'cerrar.py': [234]}`.

**El test de borde a borde de T14 caza el defecto, pero solo con el defecto
entero.** Dos experimentos:

| Experimento | Resultado |
|---|---|
| Stub devuelto **solo** a `archivar.py`, puerta como en HEAD | `10 passed` — **no se pone rojo** |
| Stub **+** `puerta_de_estado.py` revertida a `dev` (el defecto completo) | **`6 failed, 4 passed`** |

El rojo del caso central es **literalmente el error de producción**:

```
E  domain.models.errores.ParteNoApto: este parte está pendiente: la validación lo manda
   a «cola_validacion_humana» y no consta que nadie lo haya aprobado, así que no se archiva
application/pipelines/puerta_de_estado.py:119: ParteNoApto
FAILED tests/test_f030_circuito_borde_a_borde.py::test_f030_r4_el_parte_que_una_persona_aprobo_se_archiva
```

Es el mensaje exacto que vio el humano en RS26.09/0178. **La red caza el
defecto que vino a cazar.**

Que con el stub a solas no se ponga rojo **no es un agujero, y el implementer lo
declara** (desviación 4 de su informe): T8 dejó la puerta ciega a
`ctx.validacion`, así que el stub por sí solo ya no puede hacer daño —lo que lo
vigila es el centinela de T12, y lo hace—. La cadena que `tasks.md` T14 daba por
hecha la rompió el propio arreglo, **a mejor**. Declarado por escrito: correcto.

**Es de verdad borde a borde.** `test_f030_circuito_borde_a_borde.py` llama a
`cambiar_estado_http`, `archivar_parte`, `adjuntar_grafico` y
`cerrar_incidencia` con los cuerpos reales del front, contra
`RepositorioComoLaBase`, que **guarda columnas** (`mapeo.valores_de_campos`,
`mapeo.valores_de_validacion`) y **recompone con la misma
`mapeo.fila_a_validacion_y_cierre` de producción**. Los controles negativos
existen para los tres pasos, y con **dos mundos** (base vacía y parte guardado
sin aprobar), que es más de lo que pedía `design.md` §7.2.

### 2 · Ninguna puerta se aflojó

Barrido sobre el diff completo de los 14 ficheros de tests. **Asertos
eliminados: tres.** Ni uno más.

| Aserto retirado | Sustituto | Juicio |
|---|---|---|
| `assert contexto.validacion.observaciones is None` | `assert contexto.validacion is None` | **más fuerte**: antes se afirmaba que el stub no llevaba datos del papel; ahora, que **no hay stub** |
| `assert contexto.validacion.confianza_observaciones == 0` | (el mismo de arriba) | **más fuerte**, por lo mismo |
| `assert conexion.veces_con("FROM {esquema}.cierres") == 1` | `... veces_con("LEFT JOIN …cierres") == 1` **y** `... veces_con("LEFT JOIN …validaciones") == 1` | **más fuerte**: dos asertos donde había uno. El literal cambió porque `cierres` entra ahora por `LEFT JOIN`; el `len(conexion.ejecutadas) == 2` que vigila el coste **no se toca** |

Los tres tests que «pasaban por el motivo equivocado» **ahora prueban lo que
dicen**, con el veredicto que rechaza puesto en el doble:

- `test_f006_r31_parte_no_apto_responde_409` → `_repositorio(veredicto_no_apto(...))`;
- `test_f019_r19_un_parte_no_apto_no_escribe_ni_la_traza_previa` → `SituacionParte(validacion=ctx.validacion)` del contexto **no apto**;
- `test_f009_r48_un_parte_no_apto_sube_como_error_de_dominio` → `SituacionParte(validacion=veredicto_no_apto(...))`.

Sin ese cambio los tres habrían seguido en verde **por «no consta validación»**,
que es otro motivo. Corregirlos es lo contrario de relajar.

**Los ayudantes compartidos emiten veredictos de verdad.** `veredicto_apto` y
`veredicto_no_apto` (`tests/utiles_validacion.py`) llaman a **`validar_parte`**,
la función real de F-004, y **afirman el resultado** (`assert validacion.veredicto
is Veredicto.APTO` / `NO_APTO` y su destino): si mañana F-004 cambiara sus
reglas, estos tests se enteran. `contexto_apto`/`contexto_no_apto` de
`utiles_sharepoint.py` hacen lo mismo. **Ni un `ResultadoValidacion` a mano.**

`con_el_veredicto_guardado` (`tests/utiles_pg.py`) tiene las dos salvaguardas
que impiden que sea una puerta trasera, y las he comprobado en el código:
**no inventa** veredicto si el contexto no trae ninguno (el caso R8 sigue siendo
el caso R8) y **no pisa** la situación que el test haya preparado a propósito. Y
**no se usa** en los dos ficheros que vigilan la puerta.

**Los 48 casos de `test_f028_puertas.py`: ni un aserto cambiado.** El diff toca
solo las tres funciones ayudantes y añade un comentario de enmienda fechado.

### 3 · Las tres desviaciones declaradas

| # | Desviación | Juicio |
|---|---|---|
| (a) | T11 previó 5 ficheros y tocó **14 / 232 casos** | **Bien resuelta.** Es la consecuencia mecánica de mudar la fuente del veredicto, no un desbordamiento de alcance: los 14 son ficheros de test, **cero líneas de producción** fuera de lo previsto. Cada uno con su nota fechada explicando por qué el doble tiene que contestar el veredicto |
| (b) | T9 tocó **tres** ayudantes y no dos | **Bien resuelta.** `design.md` §5.5 nombraba `_dobles()` / `_con()`, que no existen en ese fichero; los reales son `_archivar`, `_adjuntar` y `_cerrar`. Uno por paso, tres pasos. Declarado con nota fechada en el propio fichero |
| (c) | El centinela de F-028 pasa de tres campos a cuatro | **Bien resuelta y no es una relajación.** Sigue siendo **igualdad exacta de conjunto**: un quinto campo lo pone rojo igual que antes lo ponía el cuarto. La enmienda está escrita y fechada en la docstring del test y en la de `SituacionParte` |

Ninguna esconde un problema.

### 4 · R18 · el coste no sube

En el código: `consultar_situacion` sigue ejecutando **dos** sentencias
—`select_situacion_estado` y la nueva `select_veredicto_y_cierre`, que
**sustituye** a la llamada a `self.consultar_estado_cierre(...)`—. No hay método
nuevo en el puerto.

En el test (`test_f030_r18_traer_el_veredicto_no_cuesta_ninguna_consulta_mas`):

```python
assert len(conexion.ejecutadas) == 2
assert conexion.veces_con(f"FROM {ESQUEMA}.cierres") == 0      # la vieja ya no corre aquí
assert conexion.veces_con(f"FROM {ESQUEMA}.partes AS p") == 1
```

Más `test_f005_sentencias.py`: el `FROM` es `partes`, los dos `JOIN` son `LEFT`
(`sql.count("LEFT JOIN") == sql.count("JOIN") == 2`), hay **un solo `%s`** y el
`hash` **no aparece interpolado en el texto**. Cumple.

### 5 · R21 · dato personal

`repositorio_pg.py`: la línea de log gana **`destino=%s`** con
`validacion.destino.value` —un literal de `Enum`— **y nada más**. Ni
observaciones, ni `codigo_obra`, ni `numero_incidencia`, que sí se leen de la
base y se quedan en memoria.

`test_f030_r21_leer_la_situacion_no_publica_nada_del_papel` lo vigila con
constantes **reconocibles** y, lo importante, con **control positivo**:

```python
assert OBRA_INVENTADA not in caplog.text
assert INCIDENCIA_INVENTADA not in caplog.text
assert "texto inventado" not in caplog.text
assert "cola_validacion_humana" in caplog.text   # si no registrara nada, pasaría igual
assert "hash-inventado-0001" in caplog.text
```

Sin el control positivo el test pasaría con un logger mudo. Está. Cumple.

### 6 · C4 bis · mutación, verificada de forma independiente

**Recálculo puro** (`harness.alcance` + `harness.mutacion.generar_mutantes`, sin
ejecutar la suite y sin escribir en disco): **419 líneas en 9 ficheros y 3
mutantes**, con el reparto por fichero **idéntico** al del informe.

Los tres mutantes coinciden uno a uno con los declarados:

| Fichero:línea | Original → mutado |
|---|---|
| `mapeo.py:426` | `codigo_obra=codigo_obra or ""` → `... and ""` |
| `mapeo.py:427` | `numero_incidencia=numero_incidencia or ""` → `... and ""` |
| `repositorio_pg.py:307` | `fila_a_validacion_y_cierre(filas[0], …)` → `filas[1]` |

**Por qué solo 3 sobre 419 líneas, y por qué es legítimo.** El mutador del arnés
tiene **cinco operadores**: comparaciones (`==`, `!=`, `<`, `<=`, `>`, `>=`),
aritméticos (`+`, `-`, `*`, `//`) y lógicos (`and`/`or`). **No muta `is` / `is
not`**, ni constantes, ni borra sentencias. Las 419 líneas de F-030 son casi
todas docstrings, notas de enmienda, un campo de dataclass, la construcción de
un `SQL` por concatenación, un desempaquetado de tupla y comprobaciones
`is None`: nada de eso es mutable con esos operadores.

**Prueba de control** exigida por el protocolo, para distinguir «no había nada
que mutar» de «el generador está roto»: sobre **los 9 ficheros enteros**,
ignorando la exclusión de alcance, el generador produce **66 mutantes**. Funciona.
El 3 es una propiedad del diff, no un fallo de la herramienta.

**Campaña reejecutada** (el informe declara 21,1 s, por debajo de los 5 minutos,
así que el protocolo la exige), con la salida **fuera de `progress/`**, en el
scratchpad:

```
python -m harness.mutacion --feature F-030 --workers 3 --salida <scratchpad>/mutacion_F-030_reviewer.md
3 mutantes evaluados, 3 muertos, 0 supervivientes, 0 timeouts en 36.1 s
```

| Métrica | Informe | Mi reejecución |
|---|---|---|
| Mutantes | 3 | **3** |
| Muertos | 3 | **3** |
| **Supervivientes** | **0** | **0** |
| Timeouts | 0 | **0** |
| Tiempo total | 21,1 s | 36,1 s (misma máquina, con carga) |

**Árbol limpio después** (`git status --short` vacío, rama
`feature/F-030-veredicto-persistido`, HEAD `9e30f57`), y el worktree de la
reproducción del rojo restaurado y vacío.

**Coste por mutante.** El nº de workers **consta**: `progress/mutacion_F-030.md`
dice `Workers | 3`, y la tabla de Evidencias lo repite («3; se pidieron 8, el
arnés los resuelve a uno por mutante»). Con la fórmula de `CHECKPOINTS.md`:

> 21,1 s × 3 workers ÷ 3 mutantes = **21,1 s por mutante**

contra los **21,22 s** que el propio informe declara para la suite del servicio.
Prácticamente idénticos: la suite **se estaba ejecutando entera** por cada
mutante. Con mis números, 36,1 × 3 ÷ 3 = 36,1 s, también por encima del tiempo
de la suite. **No es una campaña sospechosa por construcción.**

> Nota menor: la tabla de Evidencias escribe el comando como `--workers 8`
> mientras la cabecera del informe de mutación dice `--workers 3`. El valor
> **efectivo** (3) está declarado en los dos sitios y es el que he usado; la
> discrepancia es del texto del comando, no del dato.

**Los tres mutantes a mano de T18** están documentados con el nº de casos que
los mata (M1 → 84 en rojo, M2 → 19, M3 → 18) y con **quién** los mata, no solo
cuántos. He verificado el equivalente de **M1** por mi cuenta: revertir la
puerta a `ctx.validacion` pone en rojo 6 de los 10 casos del circuito de borde a
borde con el error exacto de producción. El implementer además **declara por
escrito** que «la campaña automática, sola, no acredita nada en esta feature» y
que lo que la acredita son esos tres. Es la lectura correcta y es de agradecer
que esté escrita.

### 7 · R20 · sin DDL

`git diff --name-only dev...HEAD` → **0 ficheros** bajo
`infrastructure/persistencia/sql/`. Lo vigilan además tres tests
(`test_f030_r20_*`), uno de ellos **control negativo** de que la lista del diff
no viene vacía, que es el fallo clásico de este tipo de control. Cumple.

### 8 · T16 · la compatibilidad hacia atrás (la promesa de mañana)

Los **dos** casos existen, parametrizados por las **tres** puertas:

- `test_f030_r11_una_decision_ya_guardada_sigue_aprobando_sin_volver_a_decidir`:
  la base con la ficha, el veredicto y la aprobación ya escritas; la puerta
  **pasa**. Y afirma `base.decisiones == [aprobacion]`, es decir, **la puerta no
  apunta nada nuevo**: se archiva **sin volver a decidir**. Es exactamente la
  promesa de V1 sobre `b7e9b037`.
- `test_f030_r12_si_el_veredicto_guardado_cambia_la_aprobacion_deja_de_contar`:
  el parte se revalida a `revision_manual` después de la aprobación → la puerta
  levanta `ParteNoApto`, el mensaje nombra **el destino nuevo** y **nada ha
  salido** a ningún sistema externo.

El segundo es lo que impide que el primero sea un agujero: sin él, R11 podría
estar pasando porque la huella no se compara en absoluto. Los dos están.

### 9 · `bash harness/init.sh`

Ejecutado **tal cual, sin pipes ni tail**:

```
[OK] pytest en verde (con medición de cobertura)      62 passed
[OK] servicio api (services/postventa-api): pytest en verde
[OK] servicio front (services/postventa-front): pytest en verde
[OK] PUERTA COBERTURA: 100.0% de 30 líneas cambiadas cubiertas (30/30, umbral 80%, nivel critico)
[OK] Rama actual: feature/F-030-veredicto-persistido
ENTORNO LISTO. Puedes trabajar.
EXIT_CODE=0
```

**Exit code 0.** El único aviso es `ruff: 61` avisos, deuda previa declarada que
no bloquea y que **no crece** con esta feature.

---

## Recorrido de CHECKPOINTS.md

### C1 — El arnés está completo y en verde

- [x] `bash harness/init.sh` termina con **exit code 0**.
- [x] Existen los siete ficheros obligatorios.

### C2 — El estado es coherente

- [x] Una sola feature `in_progress`: F-030.
- [x] Rama `feature/F-030-veredicto-persistido`, nunca `main`.
- [x] `progress/current.md` describe **solo** la sesión activa de F-030.
- [x] No hay feature `done` nueva pendiente de resumen en `history.md`.

### C3 — El código respeta arquitectura y convenciones

- [x] **Hexagonal respetada.** `domain/` no importa `infrastructure` ni
      `interface_adapters` (comprobado con grep sobre todo `domain/`). El mapeo
      de columnas vive en `infrastructure/persistencia/mapeo.py`, el `SQL` en
      `sentencias.py`, la regla en `domain/models/estado.py` y la orquestación
      en `application/pipelines/`. Cada artefacto en su capa.
- [x] Primera línea con la ruta relativa en **los 12 ficheros** creados o
      tocados (comprobado uno a uno).
- [x] Sin `print()` de debug, sin `TODO`/`FIXME`, sin secretos, sin
      dependencias nuevas.
- [x] La unidad de trabajo sigue siendo **el parte**: todo va por `hash_parte`.
- [x] **Nada se archiva ni se cierra sin pasar las validaciones** — es
      literalmente lo que esta feature restaura, y ahora con la fuente correcta.
      Dry-run intacto: los casos de T15 van con `commit=False`.
- [x] Lo manuscrito no se descarta: las observaciones se leen de `partes` y
      entran en la huella, que es el motivo de todo el `JOIN`.
- [x] Firmado no es conforme: el material de `veredicto_no_apto` es un parte
      **firmado con observaciones** y F-004 lo manda a la cola.
- [x] Reprocesar no duplica: sin cambios en ese camino.
- [x] Nada hardcodea un número de estado de Sigrid: esta feature no toca Sigrid.
- [x] Ningún PDF ni escaneo ha entrado en git
      (`git log --diff-filter=A` sobre `dev..HEAD`: vacío).

### C3 bis — Documentos de fuera

**N/A, justificado:** el diff **no toca ni un fichero de `docs/referencia/`**
(`git diff --name-only dev...HEAD` → 0 coincidencias). No hay documento externo
que cabecear ni que barrer.

### C4 — La verificación es real

- [x] Cada requisito tiene ≥ 1 test que lo cubre y **todos pasan** (tabla
      abajo). Ver la observación 1 sobre el **nombrado** de tres de ellos.
- [x] Los unit tests **no tocan red, ni BBDD, ni IA**: dobles en memoria
      (`RepositorioComoLaBase`, `RepositorioEnMemoria`, `RepositorioFalso`,
      `ConexionDoble`, `ErpEnMemoria`, `GraficoEnMemoria`, `ArchivoPortFalso`).
- [x] V1 y V2 listadas en `progress/current.md` y en el informe, con su comando
      y su aviso, **pendientes del humano**.

### C4 bis — El rigor declarado se cumple

- [x] Declara `rigor: "critico"`, valor válido.
- [x] **Fase RED**: el informe trae **trazas reales**, no afirmaciones — el
      `ParteNoApto` de producción, los `DID NOT RAISE ParteNoApto` de la segunda
      cara del defecto, los `AttributeError: module … has no attribute
      'fila_a_validacion_y_cierre'`, el `ImportError: cannot import name
      'select_veredicto_y_cierre'`, el `assert 1 == 0` del coste. Y la he
      **reproducido yo** para T12 y T14.
- [x] **Cobertura**: `[OK] PUERTA COBERTURA: 100.0% de 30 líneas cambiadas
      cubiertas (30/30, umbral 80%, nivel critico)`.
- [x] **Mutación**: `progress/mutacion_F-030.md` existe, generado por la
      herramienta, y sus totales están **verificados de forma independiente**
      (recálculo puro de alcance y mutantes: coinciden uno a uno).
- [x] **Los muertos están comprobados**: el «Tiempo total» declarado (21,1 s) es
      inferior a 5 minutos, así que **he reejecutado la campaña entera** a una
      ruta del scratchpad, fuera de `progress/`. Totales idénticos: 3/3/0/0.
      Árbol limpio después.
- [x] **La campaña tardó lo que tenía que tardar**: 21,1 s × 3 workers ÷ 3
      mutantes = **21,1 s por mutante**, contra 21,22 s de suite. Coherente.
      Prueba de control hecha además sobre el cero aparente de siete ficheros:
      con los ficheros enteros salen 66 mutantes, o sea que el generador
      funciona y el alcance estrecho es real.
- [x] **Cero supervivientes**, que es lo que exige `critico`. No hay ninguna
      sección de análisis en `PENDIENTE` porque no hay ningún superviviente.
- [x] **«Evidencias»** con los cuatro números y **el nº de workers** (3).
- [x] Ningún punto de este bloque marcado N/A.

### C4 ter — Rutas sensibles

**N/A, justificado:** este repositorio **no declara** `harness/rutas_sensibles.json`
(solo existe el `.ejemplo.json`). Sin declaración el bloque es N/A por diseño y
no hay nada que justificar más allá de constatarlo.

### C5 — La sesión se cerró bien

- [x] `tasks.md` con **T1–T20 todas `[x]`** y un commit `F-030 Tn: ...` por
      tarea (verificado en `git log dev..HEAD`: los 20 están). Las dos casillas
      abiertas son **V1 y V2**, que la propia `tasks.md` declara «no son
      condición de cierre de la feature».
- [x] Sin ficheros temporales ni artefactos sin trackear: `git status --short`
      vacío.
- [x] `features.json` refleja el estado real: `in_progress`, a la espera de este
      APROBADO. El implementer **no** la marcó `done`, que es lo correcto.

---

## Cobertura requisito → test

| Req | Test que lo cubre | Estado |
|---|---|---|
| R1 | `test_f030_r1_un_stub_apto_en_el_contexto_no_abre_ninguna_puerta`, `…_no_apto_no_cierra_una_puerta_abierta`, `…_la_huella_del_stub_no_depende_del_parte` (×3 puertas) | verde |
| R2 | `test_f030_r2_la_situacion_reune_las_cuatro_cosas_y_ninguna_mas`, `…_una_situacion_vacia_sigue_siendo_valida`, `test_f030_r2_la_situacion_trae_el_veredicto_guardado` | verde |
| R3 | `test_f030_r3_ningun_modulo_del_borde_construye_un_veredicto` + `…_el_centinela_sabe_ver_una_construccion` | verde · **rojo reproducido** |
| R4 | `test_f030_r4_el_parte_que_una_persona_aprobo_se_archiva`, `…_la_huella_apuntada_es_la_del_veredicto_que_vuelve_de_la_base` | verde · **rojo reproducido** |
| R5 | `test_f030_r5_el_parte_aprobado_se_adjunta_a_su_reclamacion_en_dry_run` | verde |
| R6 | `test_f030_r6_el_parte_aprobado_llega_al_dry_run_del_cierre` | verde |
| R7 | `test_f030_r7_un_cuerpo_que_miente_no_pasa_ninguna_de_las_tres_puertas` (×3) | verde |
| R8 | `test_f030_r8_sin_veredicto_guardado_cada_puerta_dice_lo_suyo` (×3), `test_f030_r8_con_ficha_pero_sin_validacion_el_veredicto_es_none` | verde |
| R9 | `test_f030_r9_sin_ficha_del_parte_no_hay_veredicto_ni_cierre`, `test_f030_r9_sin_fila_de_validacion_…`, `…_sin_ninguna_fila_…` | verde |
| R10 | `test_f030_r10_el_veredicto_recompuesto_da_la_misma_huella` (7 casos borde) + los 4 de `test_f005_mapeo.py` + `…_el_orden_de_las_columnas_es_el_que_lee_el_mapeo` | verde |
| R11 | `test_f030_r11_un_parte_no_apto_aprobado_a_mano_pasa_las_tres_puertas` (6), `…_una_decision_ya_guardada_sigue_aprobando_sin_volver_a_decidir` (3) | verde |
| R12 | `test_f030_r12_si_el_veredicto_guardado_cambia_la_aprobacion_deja_de_contar` (3), `…_la_huella_apuntada_deja_de_coincidir` | verde |
| R13 | `test_f028_huella_intacta.py` — **intacto**, como manda la spec | verde |
| R14 | `test_f030_r1_un_stub_no_apto_en_el_contexto_no_cierra_una_puerta_abierta` (su docstring lo nombra: «el camino normal de R14»), los control-negativo de `test_f028_puertas.py` y los de endpoint con `veredicto_apto` guardado | verde · **ver observación 1** |
| R15 | `test_f028_r5_un_parte_apto_rechazado_a_mano_no_pasa_ninguna_puerta`, `test_f028_r5_el_rechazo_tampoco_caduca_cuando_trae_otra_huella` — intactos y ahora ejercitados por la fuente nueva | verde · **ver observación 1** |
| R16 | `test_f030_r16_un_parte_cerrado_sin_validacion_sigue_dando_cerrado`, `…_la_consulta_se_ancla_en_partes_y_los_dos_join_son_left` | verde |
| R17 | `test_f030_r17_el_mensaje_de_pendiente_nombra_el_destino_guardado` (×3 puertas × destinos) | verde |
| R18 | `test_f030_r18_traer_el_veredicto_no_cuesta_ninguna_consulta_mas`, `test_f028_la_situacion_se_resuelve_con_dos_consultas`, + 3 de `test_f005_sentencias.py` | verde |
| R19 | `test_f006_archivar_http.py`, `test_f012_adjuntar_http.py`, `test_f009_cerrar_http.py` — los 400 intactos; `_exigir_valor_conocido(Veredicto/Destino, …)` sigue en los tres endpoints; `services/postventa-front/` **no aparece en el diff** | verde |
| R20 | `test_f030_r20_el_diff_de_la_rama_no_toca_ni_un_fichero_de_ddl`, `…_no_esta_mirando_una_lista_vacia`, `…_no_hay_ni_un_fichero_de_ddl_nuevo` | verde |
| R21 | `test_f030_r21_leer_la_situacion_no_publica_nada_del_papel` + los `test_*_logs_sin_datos_personales.py` existentes | verde |
| R22 | Cubierto por los recuentos de sentencias: `consultar_situacion` ejecuta **2 sentencias y las dos son `SELECT`**, y `test_f030_r23_el_doble_de_la_base_no_guarda_ni_un_veredicto_dentro` fija que lo leído no se queda en ninguna fila | verde · **ver observación 1** |
| R23, R24 | `test_f030_circuito_borde_a_borde.py` entero (10 casos) + los 3 del doble | verde · **rojo reproducido** |

---

## Observaciones (NO bloqueantes)

**1 · Tres requisitos se verifican, pero sin el test que lleva su número.**
La tabla §4 de `requirements.md` prometía `test_f030_r14_*`,
`test_f030_r15_*` y `test_f030_r22_*`, y **no existen**. Los tres están
cubiertos de verdad —R14 por el caso `r1` cuyo docstring lo nombra y por los
endpoints con veredicto apto guardado, R15 por los dos `test_f028_r5_*`
intactos que la propia tabla ya designaba, R22 por los recuentos de sentencias—,
así que **no hay requisito sin verificar** y por eso no bloquea. Lo que falta es
el nombre trazable y, sobre todo, que el implementer **no lo declaró** entre sus
cuatro desviaciones, cuando las otras cuatro sí. Recomendación: o se añaden los
tres alias con su nombre, o se enmienda la tabla §4 con nota fechada apuntando
al test real. Es trabajo de minutos y deja la trazabilidad automática limpia.

**2 · El centinela de T12 tiene un hueco que su propia docstring niega.**
`_construcciones_de` detecta `ResultadoValidacion(...)` y
`modulo.ResultadoValidacion(...)`, y su docstring afirma: *«cambiar la forma del
import no puede ser la manera de esquivar esto»*. **Sí puede**: lo he
comprobado metiendo en `cerrar.py`
`from domain.models.validacion import ResultadoValidacion as RV` y construyendo
`RV(...)` — el centinela pasa en verde. Con el nombre llano lo caza
(`{'cerrar.py': [234]}`), y una reintroducción realista del defecto sería una
copia del código viejo, que usa el nombre llano; por eso no bloquea. Pero la
frase de la docstring promete más de lo que el código da. Recomendación: o
resolver los alias del `ImportFrom` en el AST, o rebajar la frase.

**3 · Discrepancia menor de texto** entre `--workers 8` (tabla de Evidencias) y
`--workers 3` (cabecera de `mutacion_F-030.md`). El valor efectivo, 3, consta en
los dos sitios. Solo hay que corregir el comando escrito.

**4 · `R25` no existe en `requirements.md`.** Los dos tests de T19 se llaman
`test_f030_r25_*`. El implementer declara los dos casos como desviación 3 y su
motivo es bueno (sin ellos la precisión de F-030 en `ARCHITECTURE.md` quedaría
sin vigilancia mientras las de F-026 y F-028 la tienen), pero el número de
requisito está inventado. Recomendación: renombrarlos o dar de alta R25 en la
spec con nota fechada.

---

## Verificaciones MANUAL (humano) — **PENDIENTES, y no son motivo de rechazo**

Ninguna se ha ejecutado, y ninguna la puede ejecutar un agente.

- [ ] **V1 · el parte que está esperando.** Con F-030 desplegado en `dev`,
      archivar `b7e9b037` de **RS26.09/0178** y comprobar que se archiva **sin
      volver a decidir nada**. ⚠️ **Escribe en SharePoint**: exige autorización
      expresa del humano para esa incidencia y **no se hace desde local**.
      Comprobar antes la ventana: `infra/22_ventana_archivo.ps1 -Estado`.
- [ ] **V2 · el coste, medido.** Contar las consultas de una tanda real de 22
      partes contra `psql-albaranes-rs9k2` y comprobar que **no ha subido**
      respecto a F-028 (R18). Continúa la verificación abierta de F-028 §11.1.

> **Aviso de entorno, vigente:** `ARCHIVO_HABILITADO` y `CIERRE_HABILITADO`
> están **las dos abiertas** en `dev`. Decisión del humano si se cierran.

---

## Automejora del arnés (propuesta, no aplicada)

**`CHECKPOINTS.md` C4 bis debería exigir la prueba de control del alcance
estrecho, no solo la del cero.** Hoy el protocolo manda hacer la prueba de
control únicamente **«si la campaña declara cero mutantes»**. F-030 declara
**3 sobre 419 líneas**, que no es cero pero es igual de poco informativo, y la
única forma de saber si eso era legítimo fue generar mutantes sobre los ficheros
enteros (66) y leer los operadores del mutador. Propongo cambiar el disparador
de «cero mutantes» a **«cero mutantes, o menos de uno por cada 50 líneas de
alcance»**, con la misma prueba de control. Sin eso, una campaña que roce el cero
por un alcance mal calculado pasa el recálculo puro sin que nadie se entere.

**Segunda propuesta, menor:** que la plantilla del informe de mutación imprima
también **el coste por mutante ya calculado** y el tiempo de la suite del
servicio, que son los dos números que `CHECKPOINTS.md` obliga a cruzar a mano.
Calcularlo la herramienta evita que cada reviewer lo haga distinto.

Las dos valen para cualquier proyecto: si el humano las aprueba, van a
`arnes-base` en el mismo trabajo, según la regla de propagación de `CLAUDE.md`.
