<!-- progress/impl_F-032.md -->
# F-032 · Los códigos no admiten espacios — Informe de implementación

> Rama `feature/F-032-codigos-sin-espacios`. Rigor **`critico`**: fase RED
> obligatoria, puerta de cobertura sobre las líneas cambiadas y campaña de
> mutación con cero supervivientes (esto último, en T15, bloque 5).
>
> **Estado de este informe: bloques 0 y 1 (T1–T5) terminados.** Los bloques
> 2 a 5 no se han empezado: se encargan aparte.

---

## T1 · La medición previa de la huella (bloque 0)

**Lo que se mide y por qué.** `design.md` §7.3 exige medir las huellas de los
tres veredictos del control **antes** de tocar `normalizar_codigo`. Medirlas
después sería una foto, no una medición: una huella comparada consigo misma no
prueba nada. Estos tres hexadecimales son el control que T11 escribirá literal
en `tests/test_f032_huella_intacta.py` y que tiene que seguir valiendo lo mismo
con el cambio ya aplicado.

**Dónde se midió, exactamente:**

| Dato | Valor |
|---|---|
| Commit | `fd4fc700b7692e74018546565833396759137626` (`fd4fc70`, *F-033: alta del defecto D-A1…*) |
| Rama | `feature/F-032-codigos-sin-espacios` |
| Árbol | **limpio** (`git status --porcelain` vacío en el momento de medir) |
| Intérprete | `services/postventa-api/.venv/Scripts/python.exe` (Python 3.12.7) |
| Código de producción tocado en T1 | **ninguno** |

No hizo falta el `git worktree` de la receta de §7.3 porque la medición se hizo
**antes de editar una sola línea**, sobre el árbol de trabajo limpio en ese
mismo commit: es el mismo árbol que tendría el worktree.

### Los tres veredictos, escritos enteros

Los seis campos que entran en la cadena canónica van explícitos; el resto es
relleno (`hash_parte="9f2b0011aabb"`). Los literales de observaciones son los
**inventados** que ya usa `test_f028_huella_intacta.py`: ni un dato personal.

| # | Veredicto | Campos que entran en la huella |
|---|---|---|
| a | apto con el número leído con espacio | `destino=archivo_y_cierre`, `motivos=()`, `clasificacion_firma=humana`, `observaciones=None`, `codigo_obra="0626"`, `numero_incidencia="RS 26.09/0178"` |
| b | apto con la obra leída con espacio | `destino=archivo_y_cierre`, `motivos=()`, `clasificacion_firma=humana`, `observaciones=None`, `codigo_obra="06 26"`, `numero_incidencia="RS26.09/0178"` |
| c | no apto, en cola por observaciones, con el número leído con espacio | `destino=cola_validacion_humana`, `motivos=(observaciones_manuscritas,)`, `clasificacion_firma=humana`, `observaciones="Se aprecian parcheados. No se reparo la totalidad."`, `codigo_obra="0626"`, `numero_incidencia="RS 26.09/0178"` |

### La traza de la ejecución

Comando:

```
cd services/postventa-api
PYTHONPATH=. ENTORNO=test ./.venv/Scripts/python.exe <scratchpad>/medir_huellas_f032.py
```

Salida, literal:

```
commit medido : fd4fc700b7692e74018546565833396759137626
arbol sucio   : (limpio)

a) apto con numero_incidencia='RS 26.09/0178'
  huella = 49ab7cc6aae5026b98a27208c78c5199a6c962b57d4006c150752121fb7c508a
b) apto con codigo_obra='06 26'
  huella = 3aa32ce8733a127291fb9c7d9b09854f893dfaeec5bb927d3020536af3e0b626
c) no apto con observaciones y numero_incidencia='RS 26.09/0178'
  huella = 4fb437b10fd5635172f29bb1127aa5f23859fc492b68397d46c6eba819b66652

Comprobaciones de contexto (estado ANTES del cambio):
  normalizar_codigo('RS 26.09/0178') = 'RS 26.09/0178'
  normalizar_codigo('06 26')         = '06 26'
  _normalizar('RS 26.09/0178')       = 'rs 26.09/0178'
  _normalizar('06 26')               = '06 26'
```

Las dos últimas parejas son el defecto medido en vivo: **antes del cambio**,
`normalizar_codigo` dejaba el espacio interior intacto —de ahí el
`ReclamacionNoLocalizada` del 2026-09-17— y `_normalizar`, la de la huella,
también lo conserva (baja a minúsculas y nada más). Que la segunda lo conserve
es lo **correcto** y es justo lo que no se toca (R17).

### El segundo camino, ya comprobado en T1

Las mismas tres huellas recalculadas a mano con `hashlib` sobre la cadena
canónica escrita a pelo —seis campos separados por `\n`, en minúsculas, sin
importar ni una constante de `aprobacion.py`— dan **exactamente lo mismo**:

```
a 49ab7cc6aae5026b98a27208c78c5199a6c962b57d4006c150752121fb7c508a
b 3aa32ce8733a127291fb9c7d9b09854f893dfaeec5bb927d3020536af3e0b626
c 4fb437b10fd5635172f29bb1127aa5f23859fc492b68397d46c6eba819b66652
```

Cadenas canónicas usadas (las que T11 tiene que escribir en el test):

| # | Cadena canónica (campos separados por salto de línea) |
|---|---|
| a | `archivo_y_cierre` · `` · `humana` · `` · `0626` · `rs 26.09/0178` |
| b | `archivo_y_cierre` · `` · `humana` · `` · `06 26` · `rs26.09/0178` |
| c | `cola_validacion_humana` · `observaciones_manuscritas` · `humana` · `se aprecian parcheados. no se reparo la totalidad.` · `0626` · `rs 26.09/0178` |

O sea: el literal no es la foto de un código que ya estuviera mal, y lo es por
dos caminos independientes desde antes de tocar nada.

---

## T2 · La fase RED (bloque 0)

**Fichero creado**: `services/postventa-api/tests/test_f032_espacios_en_los_codigos.py`
(dominio puro: sin red, sin BBDD, sin IA y sin reloj).

Lleva **la tabla entera** de `design.md` §5 —las 13 formas del número, con el
caso real **`RS 26.09/0178` escrito literal**, y las 8 del código de obra—,
parametrizada sobre las tres salidas: `normalizar_codigo`,
`a_codigo_de_sigrid` y `nombre_de_archivo`/`carpeta_de_archivo`.

**Un detalle que no es cosmético**: los blancos invisibles van escritos con su
secuencia de escape (`"RS\u00a026.09/0149"`, `"06\u00a026"`, `"\u202f"`,
`"\u200b"`) y **no** con el carácter pegado. Pegados en el fichero son
indistinguibles de un espacio normal, y un día alguien los «arreglaría» sin
saber que acaba de borrar el caso que el test prueba. `ruff` avisa de ello
(`PLE2515`) y tiene razón.

### El resultado: ROJO, y por el motivo correcto

```
cd services/postventa-api
./.venv/Scripts/python.exe -m pytest tests/test_f032_espacios_en_los_codigos.py -q

39 failed, 69 passed in 0.43s
```

**Ni un `ImportError` ni un error de recogida**: los 108 tests se recogen y
ejecutan, 69 pasan —las seis formas que F-028 ya arregló y las garantías que
esta feature no toca— y 39 fallan con un `AssertionError` que dice exactamente
lo que la spec predice. Un rojo por importación no sería fase RED.

Reparto de los 39 fallos, que coincide con lo que `tasks.md` T2 anticipaba
(«filas 7–13 y B–D»):

| Test | Fallos | Filas |
|---|---|---|
| `test_f032_r1_normalizar_elimina_todos_los_espacios` | 1 | el caso real y `06 26` |
| `test_f032_r2_los_blancos_raros_tambien` | 6 | espacio, doble, tabulador, salto, `U+00A0`, `U+202F` |
| `test_f032_r3_los_ceros_a_la_izquierda_siguen_intactos` | 2 | `06 26`, `00 07` |
| `test_f032_r6_el_saneo_vive_en_normalizar_codigo` | 10 | 7–13 y B–D |
| `test_f032_r7_todas_las_formas_dan_el_mismo_codigo_para_el_erp` | 7 | 7–13 |
| `test_f032_r8_todas_las_formas_dan_el_mismo_nombre_de_fichero` | 7 | 7–13 |
| `test_f032_r9_el_codigo_de_obra_con_espacios_no_cambia_la_carpeta` | 3 | B–D |
| `test_f032_r28_*` (las tres agregadas) | 3 | la propiedad entera |

Verdes ya antes del cambio: las filas **1–6** (las de F-028), la **A** y las
**E–H** de la obra —incluida la que impide pasarse de listo, `06-77`, que no se
parte por su guion—, R4 (código vacío), R10 (idempotencia) y el defecto
declarado D3 (el `U+200B` sigue pasando, y está escrito para que se vea).

### La traza, literal, de las cuatro filas que pagan la feature

```
_____________ test_f032_r1_normalizar_elimina_todos_los_espacios ______________
tests\test_f032_espacios_en_los_codigos.py:142: in test_f032_r1_normalizar_elimina_todos_los_espacios
    assert normalizar_codigo(LEIDO_EL_17) == "RS26.09/0178"
E   AssertionError: assert 'RS 26.09/0178' == 'RS26.09/0178'
E     - RS26.09/0178
E     + RS 26.09/0178
E     ?   +
_ test_f032_r6_el_saneo_vive_en_normalizar_codigo[7 · espacio dentro del primer tramo (EL CASO REAL)] _
tests\test_f032_espacios_en_los_codigos.py:264: in test_f032_r6_el_saneo_vive_en_normalizar_codigo
    assert not any(caracter.isspace() for caracter in normalizado), (
E   AssertionError: la forma «7 · espacio dentro del primer tramo (EL CASO REAL)» conserva un blanco: «RS 26.09/0178»
_ test_f032_r7_todas_las_formas_dan_el_mismo_codigo_para_el_erp[7 · espacio dentro del primer tramo (EL CASO REAL)] _
tests\test_f032_espacios_en_los_codigos.py:292: in test_f032_r7_todas_las_formas_dan_el_mismo_codigo_para_el_erp
    assert a_codigo_de_sigrid(entrada) == esperado, (
E   AssertionError: la forma «7 · espacio dentro del primer tramo (EL CASO REAL)» no llega al ERP como la canónica
E   assert 'RS 26.09/0178' == 'RS26.09/0178'
_ test_f032_r8_todas_las_formas_dan_el_mismo_nombre_de_fichero[7 · espacio dentro del primer tramo (EL CASO REAL)] _
tests\test_f032_espacios_en_los_codigos.py:330: in test_f032_r8_todas_las_formas_dan_el_mismo_nombre_de_fichero
E   AssertionError: la forma «7 · espacio dentro del primer tramo (EL CASO REAL)» se archivaría con otro nombre
E     - 0626 - RS26.09 - 0178 PARTE FIRMADO.pdf
E     + 0626 - RS 26.09 - 0178 PARTE FIRMADO.pdf
E     ?          +
_______ test_f032_r28_las_formas_de_la_misma_obra_dan_una_unica_carpeta _______
tests\test_f032_espacios_en_los_codigos.py:406: in test_f032_r28_las_formas_de_la_misma_obra_dan_una_unica_carpeta
    assert carpetas == {"Postventa/0626"}
E   AssertionError: assert {'Postventa/0...stventa/0626'} == {'Postventa/0626'}
E     Extra items in the left set:
E     'Postventa/06 26'
```

Eso es el defecto del 2026-09-17 reproducido en memoria, en 0,4 segundos y sin
tocar ni el ERP ni SharePoint: el mismo número que costó un rescate a mano.
`'Postventa/06 26'` es además el daño **que no se ve**: para Graph es otra
carpeta, y ahí nadie echa en falta el PDF.

---

## T3 · El cambio en `normalizar_codigo` (bloque 1)

**Fichero tocado**: `services/postventa-api/domain/models/nombrado.py`, y
**solo ese**. 42 líneas añadidas y 26 borradas, de las cuales el cambio de
comportamiento son **dos**:

```python
# antes
colapsado = " ".join(bruto.translate(_A_GUION_NORMAL).split())
return _ESPACIOS_JUNTO_AL_SEPARADOR.sub(r"\1", colapsado)

# ahora
return "".join(bruto.translate(_A_GUION_NORMAL).split())
```

Lo demás es la docstring reescrita y el borrado de
`_ESPACIOS_JUNTO_AL_SEPARADOR`, que **queda sin trabajo**: después de quitar
todos los blancos no puede quedar ninguno flanqueando a un separador, y un
regex que ya no puede casar nada es un regex que dentro de seis meses alguien
lee como si significara algo. `import re` sigue haciendo falta para
`_CUALQUIER_SEPARADOR`, que parte el código en tramos.

La docstring lleva la **enmienda fechada del 2026-09-17** con las cuatro cosas
que pide la tarea: qué decía antes (literal), qué la invalidó (la premisa de
F-028 de que el espacio siempre tocaba al separador, y el cierre que costó),
quién y cuándo, y **qué no cambia** —ceros a la izquierda, sufijo y extensión
literales, error ruidoso ante un nombre imposible y el código de obra sin
partir por sus guiones—. También queda escrito ahí que `str.split()` cubre
cualquier blanco Unicode sin lista que mantener, y que el `U+200B` **no** entra
(defecto D3, declarado).

### Verificación

```
cd services/postventa-api
./.venv/Scripts/python.exe -m pytest tests/test_f032_espacios_en_los_codigos.py -q

108 passed in 0.27s
```

Verde entero: los 39 que fallaban en T2 pasan, y los 69 que ya pasaban siguen
pasando. `ruff` limpio sobre el fichero.

---

## T4 · La suite completa, y la única consecuencia admitida (bloque 1)

```
cd services/postventa-api
./.venv/Scripts/python.exe -m pytest tests -q --tb=short

1 failed, 2841 passed, 5 skipped in 44.72s
```

Se lanzó **sin `-x`** a propósito: con `-x` la suite para en el primer fallo y
no se puede afirmar que sea el único. El recuento de arriba es el de la suite
entera recorrida.

**El único fallo es el previsto**, y es el test que codifica la regla que esta
feature sustituye:

```
___________ test_f006_r8_los_espacios_interiores_se_colapsan_a_uno ____________
tests\test_f006_nombrado.py:456: in test_f006_r8_los_espacios_interiores_se_colapsan_a_uno
    assert normalizar_codigo("RS26.08   0123") == "RS26.08 0123"
E   AssertionError: assert 'RS26.080123' == 'RS26.08 0123'
E     - RS26.08 0123
E     ?        -
E     + RS26.080123
```

Nada más se movió: **ni una consecuencia que la spec no hubiera previsto**.

### Los centinelas que tenían que seguir verdes sin tocarlos

Ejecutados aparte, además de dentro de la suite, porque son el control que esta
feature tiene que **pasar**, no ajustar:

| Suite | Resultado |
|---|---|
| `test_f028_espacios_codigos.py` + `test_f028_huella_intacta.py` + `test_f026_aprobacion_dominio.py` | **88 passed** |
| `test_f026_*` (los cuatro ficheros) | **76 passed** |
| `test_f009_*` (los quince ficheros) | **355 passed** |

Y el control de que no se han «ajustado»: `git diff dev --stat` sobre
`domain/models/aprobacion.py`, `tests/test_f028_huella_intacta.py`,
`tests/test_f028_espacios_codigos.py` y `services/postventa-front/` devuelve
**vacío**. Las siete huellas literales de F-028 siguen valiendo lo que valían
con el cambio ya aplicado, que es R18 cumplido por ejecución y no por
razonamiento.

---

## T5 · El test de F-006 R8, enmendado (bloque 1)

PENDIENTE

---

## Evidencias

PENDIENTE
