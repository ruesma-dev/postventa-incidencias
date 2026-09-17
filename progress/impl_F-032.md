<!-- progress/impl_F-032.md -->
# F-032 · Los códigos no admiten espacios — Informe de implementación

> Rama `feature/F-032-codigos-sin-espacios`. Rigor **`critico`**: fase RED
> obligatoria, puerta de cobertura sobre las líneas cambiadas y campaña de
> mutación con cero supervivientes (esto último, en T15, bloque 5).
>
> **Estado de este informe: bloques 0 a 3 (T1–T10) terminados.** Los bloques
> 4 y 5 no se han empezado: se encargan aparte.
>
> El informe está escrito por encargos: primero los bloques 0 y 1 (T1–T5) y
> después los bloques 2 y 3 (T6–T10). Las secciones del primer encargo se
> conservan **tal y como se escribieron**, con sus números de entonces; las
> cifras vigentes son las de la sección **«Evidencias»** del final.

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

**Dos ficheros tocados, y ninguno más:**

1. `services/postventa-api/tests/test_f006_nombrado.py` ·
   `test_f006_r8_los_espacios_interiores_se_colapsan_a_uno` pasa a llamarse
   **`test_f006_r8_los_espacios_interiores_se_eliminan`** y su segundo aserto
   cambia de expectativa:

   ```python
   # antes
   assert normalizar_codigo("RS26.08   0123") == "RS26.08 0123"
   # ahora
   assert normalizar_codigo("RS26.08   0123") == "RS26.080123"
   ```

   El primero (`"RS26.08   -    0123"` → `"RS26.08-0123"`) no se toca: sigue
   valiendo y sigue siendo el que F-028 fijó.

   Su docstring cuenta la historia **completa**, que es lo que impide que el
   siguiente que pase lea un aserto suelto: cómo nació (el colapso de F-006),
   por qué cambió el 2026-09-15 (F-028, con el literal de lo que afirmaba
   entonces) y por qué vuelve a cambiar el 2026-09-17 (F-032), con el caso real
   delante y el motivo de que el colapso no se afloje sino que **se retire**.

2. `specs/F-006-sharepoint/requirements.md` · el cuerpo de **R8** pasa a pedir
   «eliminar **todos** los blancos» y se añade la **segunda enmienda fechada**
   del 2026-09-17 con el contenido de `design.md` §9.1: qué cambia, qué la
   invalidó, quién y cuándo, y qué **no** cambia —incluida la advertencia de
   que la normalización de la **huella** es otra y no se toca (R17, D1)—.
   Se corrigen además los dos punteros que quedaban al nombre viejo del test:
   la frase de la primera enmienda y la fila de trazabilidad.

Las menciones al nombre viejo que hay en `specs/F-028-*` y en la propia spec de
F-032 **se dejan como están**: son el registro de lo que se decidió aquel día,
no punteros vivos.

### Verificación

```
cd services/postventa-api
./.venv/Scripts/python.exe -m pytest tests -q

2842 passed, 5 skipped in 49.32s
```

Verde entero. Cero fallos.

---

## Estado del arnés al cerrar el bloque 1

`bash harness/init.sh` **en verde**, sin maquillaje. Lo pertinente, literal:

```
[OK] compileall: sin errores de sintaxis
[AVISO] ruff: 61 avisos (deuda previa, no bloquea)
[OK] pytest en verde (con medición de cobertura)        ← suite del arnés, 62 passed
2842 passed, 15 skipped in 63.17s (0:01:03)
[OK] servicio api (services/postventa-api): pytest en verde
[OK] servicio front (services/postventa-front): pytest en verde (caché)
[OK] PUERTA COBERTURA: 100.0% de 1 líneas cambiadas cubiertas (1/1, umbral 80%, nivel critico)
[OK] Rama actual: feature/F-032-codigos-sin-espacios
ENTORNO LISTO. Puedes trabajar.
```

Los 61 avisos de `ruff` son **deuda previa** y no de esta rama: los ficheros que
esta feature toca pasan `ruff check` limpios.

---

## Lo que quedaba fuera del encargo de los bloques 0 y 1

Los bloques 2 a 5 **no se han empezado**, y por eso no están hechos:

- **B2/B3 · el saneo en la extracción** (R11–R16, T6–T10): `CAMPOS_DE_CODIGO` y
  `sanear_valor_leido` en el dominio, y sus dos llamantes —`paso_extraccion` y
  `cuerpos.a_extraccion`—. Hoy lo que se guarda en `postventa.partes` **sigue
  naciendo con el espacio que leyó el modelo**: lo que ya funciona es que ese
  valor sucio ya no rompe el ERP, el nombre ni la carpeta, porque los tres
  normalizan. El criterio de aceptación 3 no está cumplido todavía.
- **B4 · los controles de alcance** (T11, T12): el fichero
  `tests/test_f032_huella_intacta.py` con los tres literales de T1 **está por
  escribir**. La medición ya está hecha y es la de este informe; lo que falta
  es dejarla fijada en un test.
- **B5 · documentación, medición y cierre** (T13–T15): la precisión de F-032 en
  la semántica 5 de `docs/ARCHITECTURE.md`, el defecto **D-A1** escrito aquí
  para el humano, la **medición previa de `design.md` §6.3** y la campaña de
  mutación.

### Verificaciones MANUAL pendientes (no son de este bloque, pero se recuerdan)

- **R26 · la medición previa del §6.3, antes de desplegar.** Consulta de solo
  lectura sobre `postventa` que lista los partes archivados cuyos códigos
  guardados llevan algún blanco. **Sin ella no se despliega**, y va antes
  porque re-archivar pisa `postventa.archivos.nombre_fichero`, que es la única
  pista del nombre viejo.
- **R27** · si devuelve filas, esos partes **no se re-archivan desde el
  circuito**: lo decide una persona.
- **El caso real de punta a punta**, con escritura en el ERP de producción:
  exige autorización expresa del humano para esa incidencia concreta.

---

## Evidencias medidas al cerrar el bloque 1

Números **medidos**, no estimados, en este árbol (`c78a69b` + T5) con el
intérprete del servicio.

| Evidencia | Valor | De dónde sale |
|---|---|---|
| Tests ejecutados · servicio `api` | **2842 passed, 15 skipped, 0 failed** | `bash harness/init.sh` (suite completa del servicio) |
| Tests ejecutados · arnés | **62 passed** | `bash harness/init.sh`, sección de la raíz |
| Tests del fichero nuevo de F-032 | **108 passed** (eran **39 failed / 69 passed** en la fase RED de T2) | `pytest tests/test_f032_espacios_en_los_codigos.py` |
| Cobertura de las líneas cambiadas | **100,0 % de 1 línea (1/1)**, umbral 80 %, nivel `critico` | línea `PUERTA COBERTURA` de `init.sh` |
| Tiempo de ejecución de la suite | **63,17 s** dentro de `init.sh`; **49,32 s** lanzada a solas | la propia salida de pytest |
| Mutantes generados y supervivientes | **NO EJECUTADO todavía**, con motivo | ver abajo |

**Por qué no hay campaña de mutación en este informe**: es la tarea **T15, del
bloque 5**, y este encargo era T1–T5. La campaña es cara y se lanza **al
terminar** la feature, no a mitad: mutar ahora el dominio del saneo —que aún no
existe (bloques 2 y 3)— daría un recuento que no significa nada y habría que
repetirlo entero. Queda como lo primero que se mide al cerrar, y el nivel
`critico` exige **cero supervivientes**, cada uno con test nuevo o
justificación escrita.

**Fase RED**: hecha y con la traza real pegada (T2, arriba). 39 fallos, todos
`AssertionError` sobre el valor, ninguno por importación ni por recogida.

### Ficheros tocados en T1–T5

| Fichero | Qué |
|---|---|
| `services/postventa-api/domain/models/nombrado.py` | **producción**: `normalizar_codigo` elimina todos los blancos; se borra `_ESPACIOS_JUNTO_AL_SEPARADOR`; docstring con la enmienda fechada |
| `services/postventa-api/tests/test_f032_espacios_en_los_codigos.py` | **nuevo**: la tabla entera de casos (13 + 8 formas) |
| `services/postventa-api/tests/test_f006_nombrado.py` | el test de R8, renombrado y con la expectativa nueva |
| `specs/F-006-sharepoint/requirements.md` | R8 reescrito + segunda enmienda fechada |
| `specs/F-032-codigos-sin-espacios/tasks.md` | T1–T5 marcadas |
| `progress/impl_F-032.md`, `progress/current.md` | este informe y el rastro del arnés |

**Ni un fichero prohibido**: `domain/models/aprobacion.py`,
`tests/test_f028_*`, `tests/test_f026_*`, `domain/models/cierre.py`,
`infrastructure/sigrid/consultas.py`, `infrastructure/persistencia/**`,
`config/prompts.yaml`, `services/postventa-front/**`, `infra/` y `.env` están
**sin tocar**. Ninguna escritura contra Azure, Sigrid, SharePoint ni
PostgreSQL: todo lo de estos dos bloques es dominio puro en memoria.

---

# Bloques 2 y 3 · el saneo en la extracción (T6–T10)

> Segundo encargo. Lo que arregla: que los dos códigos **se guarden limpios**
> en `postventa.partes`, para que nadie tenga que volver a editar un parte a
> mano —que es lo que hubo que hacer el 2026-09-17 con `RS 26.09/0178`—.
>
> El bloque 1 había arreglado las tres **salidas** (ERP, nombre y carpeta).
> Esto es la otra mitad: la **entrada**.

## T6 · La red del saneo, en rojo (bloque 2)

**Fichero creado**: `services/postventa-api/tests/test_f032_saneo_en_la_extraccion.py`.
Dobles en memoria: sin red, sin BBDD y sin IA.

Cubre R11–R16 por los **dos caminos** que mide `design.md` §4 —el del pipeline
(`paso_extraccion`) y el del cuerpo HTTP (`cuerpos.a_extraccion`)— y, de borde
a borde, lo que acabaría en las columnas de la tabla.

**Lo que más ocupa del fichero es lo que NO debe cambiar**, y es deliberado:
los otros siete campos se copian tal cual, y el caso que lo demuestra es una
**observación manuscrita con espacios dobles y saltos de línea** que tiene que
salir letra por letra igual que entró. Eso es lo que separa «sanear un código»
de «tocar el texto del cliente».

### Una decisión de forma que hay que justificar

`CAMPOS_DE_CODIGO` y `sanear_valor_leido` se importan **dentro de cada test**,
no en la cabecera del fichero. En la fase RED esas dos piezas todavía no
existen (las escribe T7), y un `import` de cabecera habría tumbado el fichero
entero en la **recogida**: los tests de comportamiento —los que de verdad
reproducen el defecto— no habrían llegado a ejecutarse y el rojo no habría
dicho nada. Queda escrito en la docstring del helper `_regla_del_dominio`.

### El resultado: ROJO, y por el motivo correcto

```
cd services/postventa-api
./.venv/Scripts/python.exe -m pytest tests/test_f032_saneo_en_la_extraccion.py -q

21 failed, 8 passed in 1.03s
```

Los **8 verdes** no son relleno: son las garantías que **ya se cumplían** y que
este cambio no podía romper —los siete textos se copian tal cual por los dos
caminos, el borde no fabrica avisos, un campo ausente sigue ausente y la
confianza no se toca—. Que estuvieran verdes desde el primer momento es lo que
permite afirmar que el saneo no rompió nada, y no solo que arregló algo.

### La traza literal de los cuatro fallos que pagan la feature

```
___ test_f032_r14_la_regla_del_dominio_solo_conoce_los_dos_codigos ___
tests\test_f032_saneo_en_la_extraccion.py:298: in test_f032_r14_la_regla_del_dominio_solo_conoce_los_dos_codigos
    campos_de_codigo = _campos_de_codigo()
tests\test_f032_saneo_en_la_extraccion.py:188: in _campos_de_codigo
    from domain.models.extraccion import CAMPOS_DE_CODIGO
E   ImportError: cannot import name 'CAMPOS_DE_CODIGO' from 'domain.models.extraccion'

___ test_f032_r11_la_extraccion_sanea_los_dos_codigos ___
tests\test_f032_saneo_en_la_extraccion.py:394: in test_f032_r11_la_extraccion_sanea_los_dos_codigos
    assert contexto.extraccion.campo("codigo_obra").valor == OBRA_LIMPIA
E   AssertionError: assert '06 26' == '0626'
E     - 0626
E     + 06 26
E     ?   +

___ test_f032_r15_el_saneo_deja_aviso ___
tests\test_f032_saneo_en_la_extraccion.py:448: in test_f032_r15_el_saneo_deja_aviso
    assert len(del_codigo) == 1
E   assert 0 == 1
E    +  where 0 = len([])

___ test_f032_r13_lo_que_se_guarda_no_lleva_espacios ___
tests\test_f032_saneo_en_la_extraccion.py:679: in test_f032_r13_lo_que_se_guarda_no_lleva_espacios
    assert fila["codigo_obra"] == OBRA_LIMPIA
E   AssertionError: assert '06 26' == '0626'
E     - 0626
E     + 06 26
E     ?   +
```

El último es el importante: **el defecto del 2026-09-17 reproducido hasta los
parámetros del `INSERT`**, con el cuerpo real de `POST /api/parte` y sin base
de datos. `06 26` llegando a la columna `partes.codigo_obra`, y el número
`RS 26.09/0178` con su espacio, que es exactamente lo que hubo que borrar a
mano aquel día.

Otro fallo de la tanda, por si hiciera falta verlo entero (R16):

```
E   AssertionError: assert '  \t ' is None
     +  where '  \t ' = CampoExtraido(valor='  \t ', confianza_pct=90).valor
     +    where CampoExtraido(valor='  \t ', confianza_pct=90) = campo('numero_incidencia')
```

---

## T7 · La regla, en el dominio (bloque 2)

**Fichero tocado**: `services/postventa-api/domain/models/extraccion.py`, y solo
ese. 51 líneas añadidas, de las cuales el comportamiento son **tres**:

```python
CAMPOS_DE_CODIGO: tuple[str, ...] = ("codigo_obra", "numero_incidencia")


def sanear_valor_leido(nombre: str, valor: str | None) -> str | None:
    if valor is None or nombre not in CAMPOS_DE_CODIGO:
        return valor
    return normalizar_codigo(valor) or None
```

Va **junto a `CAMPOS_DEL_PARTE` y `CAMPOS_MANUSCRITOS`**, que es donde ya vive
el conocimiento de «qué es cada campo». El dominio dice *qué* campos son
códigos y *cómo* se sanea uno; aplicarlo sigue siendo del paso del pipeline y
del borde HTTP, así que la cabecera del módulo —«quien sanea es la
aplicación»— sigue siendo cierta. Lo que cambia es que el **criterio** deja de
estar repartido, y queda dicho en una nota fechada de esa misma cabecera.

**Se apoya en `normalizar_codigo` y nunca en una copia.** Es la misma regla que
nombra el fichero y que busca en el ERP: el día que cambie, cambia para las
tres. Dos criterios del mismo concepto divergen siempre, y a este proyecto ya
le pasó. El test lo afirma de dos formas independientes —que es **el mismo
objeto función** (`extraccion.normalizar_codigo is nombrado.normalizar_codigo`),
o sea que se importa en vez de reescribirse, y que todas las formas
equivalentes dan el mismo valor—.

**Sin ciclo de importación**: `nombrado` no importa a nadie salvo `errores`, y
la suite entera lo confirma (2866 passed en ese momento).

### Un fallo que T7 puso rojo, y que no estaba previsto

La tabla `FORMAS_EQUIVALENTES` que T6 había escrito metía `RS26.09 - 0178`
entre las formas que `sanear_valor_leido` debía dejar en `RS26.09/0178`. **Era
un error del test, no del código**: el saneo quita blancos y traduce guiones
raros al normal, pero **no unifica separadores**. Quien hace que la barra y el
guion lleguen igual al ERP es `a_codigo_de_sigrid`, que parte en tramos y los
une con `/`.

```
E   AssertionError: assert {'RS26.09-017...RS26.09/0178'} == {'RS26.09/0178'}
E     Extra items in the left set:
E     'RS26.09-0178'
```

Se corrigió la tabla **y se añadió el test que fija lo contrario**:
`sanear_valor_leido("codigo_obra", "06 - 77")` vale `"06-77"` y **no se parte
por su guion**. No es un detalle: `06-77` es **una** obra, F-028 R48 ya lo
fijó, y un saneo que tocara separadores archivaría ese parte en una carpeta que
no existe. Ese daño, además, no se ve.

Se anota aquí porque la spec no lo preveía y porque la confusión es fácil de
repetir. **No cambia el alcance ni ninguna decisión**: el código quedó como
dice `design.md` §4.1, letra por letra.

### Verificación

```
./.venv/Scripts/python.exe -m pytest tests/test_f032_saneo_en_la_extraccion.py -q

24 passed, 6 failed in 1.13s
```

Que es exactamente lo que `tasks.md` T7 pide: **los tests que solo tocan el
dominio, en verde; el resto, todavía en rojo**. Los seis rojos son los dos
llamantes, que son T8, T9 y T10.

---

## T8 · El llamante del pipeline, con su aviso (bloque 3)

**Fichero tocado**: `services/postventa-api/application/pipelines/paso_extraccion.py`.

Dentro del bucle que ya recorre `CAMPOS_DEL_PARTE`:

```python
valor = sanear_valor_leido(nombre, bruto.valor)
if valor != bruto.valor:
    avisos.append(
        f"{nombre}: el modelo leyó «{bruto.valor}» y se ha guardado "
        f"sin espacios como «{valor}»"
    )
campos[nombre] = CampoExtraido(valor=valor, confianza_pct=confianza)
```

**El aviso es R15 y no es decorativo.** Sin él, el saneo taparía una lectura
mala del modelo sin que nadie se entere: quien mire el parte vería un código
correcto y no sabría que no es letra por letra el del papel. Los avisos ya se
persisten (`partes.avisos_extraccion`) y ya se enseñan, así que no hizo falta
ningún mecanismo nuevo. Y no llevan dato personal: los dos códigos ya viven en
claro en sus propias columnas.

**Y la docstring del módulo, corregida.** Decía que este paso «no normaliza
ningún valor», y habría dejado de ser verdad —que es la peor clase de
comentario: el que parece vigente—. La enmienda va fechada, con el caso del
2026-09-17, y deja escrito lo que **no** cambia: los otros siete campos se
siguen copiando tal cual y qué campo es un código lo decide el dominio, no este
paso.

### Verificación

```
./.venv/Scripts/python.exe -m pytest tests/test_f032_saneo_en_la_extraccion.py -q
27 passed, 3 failed in 1.18s

./.venv/Scripts/python.exe -m pytest tests -q
2869 passed, 5 skipped in 33.92s
```

Los tres rojos que quedaban eran el camino del cuerpo HTTP. **Ni una
regresión** en la suite completa, pese a que el paso emite ahora un aviso más
en los casos en que sanea.

---

## T9 · El llamante del borde HTTP (bloque 3)

**Fichero tocado**: `services/postventa-api/interface_adapters/api/cuerpos.py`.

```python
campos={
    nombre: a_campo(campos[nombre], nombre) for nombre in CAMPOS_DEL_PARTE
},
```

y `a_campo` sanea el valor con la función del dominio, justo donde ya saneaba
la confianza. Es la simetría que ya existía: **lo que llega de fuera se sanea
con el criterio de dentro**.

**`nombre` es obligatorio y sin valor por defecto, a propósito.** Sin él no se
puede saber si el campo es un código o un texto, y un saneo que no sanea nada
en silencio es peor que ninguno: quien llame sin decir qué campo es, se entera
al instante. `a_campo` es pública (está en `__all__`), y el árbol entero tiene
un solo llamante, que es este.

**Por qué este sitio y no solo el pipeline.** Es la parte que más fácil sería
dar por redundante y es justo al revés: `paso_extraccion` **no persiste nada**
—su resultado viaja al front, la persona puede corregirlo y lo devuelve— y los
tres endpoints que guardan o revalidan reconstruyen la extracción **aquí**.
Sanear solo en el pipeline dejaría la base sucia en cuanto alguien corrigiera
un campo en la pantalla, que es exactamente lo que pasó el 2026-09-17.

**Sin avisos por este camino**, y es deliberado: `a_extraccion` construye la
extracción con `avisos=()` por contrato —los avisos son de la **lectura**, no
del transporte (F-019)— y fabricarlos en el borde los duplicaría en cada
revalidación del mismo parte. **Ni una clave del contrato HTTP cambia.**

### Verificación

```
./.venv/Scripts/python.exe -m pytest tests/test_f032_saneo_en_la_extraccion.py -q
30 passed in 0.98s

./.venv/Scripts/python.exe -m pytest tests -q
2872 passed, 5 skipped in 33.53s
```

---

## T10 · El borde a borde, por los dos endpoints que escriben (bloque 3)

**El test de R13 que pedía la tarea —cuerpo de `POST /api/parte` con
`codigo_obra = "06 26"` y `numero_incidencia = "RS 26.09/0178"` acabando en
`sentencias.upsert_parte` con `0626` y `RS26.09/0178`— ya se tendió en la red
de T6**, porque formaba parte de «los casos de R11–R16», y su traza RED está
arriba, en T6. Se deja dicho para que no parezca que T10 no hizo nada.

Lo que T10 **añade** es el **segundo endpoint que escribe en
`postventa.partes`**, y que además es el del caso real: `POST /api/estado`.
`/api/parte` guarda lo que leyó la máquina; `/api/estado` guarda lo que una
persona decide después de mirar la pantalla, y por ahí vuelve a pasar el cuerpo
entero, extracción incluida. El rescate del 2026-09-17 consistió exactamente en
eso: alguien corrigió el código a mano y volvió a guardar.

Son **dos handlers distintos** y lo único que comparten es
`cuerpos.a_extraccion`, que es precisamente lo que el test afirma.

### Cómo se comprueba sin base de datos

Un doble, `RepositorioQueEscribeComoLaBase`, que extiende `RepositorioEnMemoria`
y además **compone el SQL** de `sentencias.upsert_parte`. Lo que se afirma no es
un objeto en memoria —que podría estar limpio mientras la columna se ensucia—
sino los **parámetros** que viajarían a `partes.codigo_obra`. Las columnas se
emparejan con los parámetros leyendo la lista **del propio SQL**, con
`zip(..., strict=True)`, para no atarse a una constante privada de
`sentencias.py` ni a un orden que no es asunto del test.

### La comprobación en rojo del test nuevo

El test de `/api/estado` no nació con la tanda de T6, así que se comprobó
**quitando el saneo del borde** y volviéndolo a poner:

```
(con `a_campo` sin sanear el valor)
tests\test_f032_saneo_en_la_extraccion.py:757: AssertionError: assert '06 26' == '0626'
FAILED tests/test_f032_saneo_en_la_extraccion.py::test_f032_r13_la_correccion_de_una_persona_tambien_se_guarda_limpia
1 failed, 1 passed, 30 deselected
```

Con el saneo puesto, verde. `cuerpos.py` se restauró con `git checkout --` y el
árbol quedó limpio: la comprobación no dejó rastro en ningún commit.

**Honestidad sobre el segundo test nuevo**: el que vigila que
`avisos_extraccion` no gane avisos fabricados en el borde (el `1 passed` de la
línea de arriba) **pasa también sin el cambio**. No es fase RED y no se
presenta como tal: es un **guardián** contra una regresión futura —si alguien
decidiera emitir el aviso también en `a_extraccion`, el mismo parte acumularía
uno por revalidación hasta convertir la columna en ruido—.

### Verificación

```
./.venv/Scripts/python.exe -m pytest tests/test_f032_saneo_en_la_extraccion.py -q
32 passed in 0.86s

./.venv/Scripts/python.exe -m pytest tests -q
2874 passed, 5 skipped in 32.03s
```

---

## Estado del arnés al cerrar el bloque 3

`bash harness/init.sh` **en verde**, sin maquillaje. Lo pertinente, literal:

```
[OK] compileall: sin errores de sintaxis
[AVISO] ruff: 61 avisos (deuda previa, no bloquea)
62 passed in 3.85s
[OK] pytest en verde (con medición de cobertura)          ← suite del arnés
2874 passed, 15 skipped in 44.27s
[OK] servicio api (services/postventa-api): pytest en verde
[OK] servicio front (services/postventa-front): pytest en verde (caché)
[OK] PUERTA COBERTURA: 100.0% de 12 líneas cambiadas cubiertas (12/12, umbral 80%, nivel critico)
[OK] Rama actual: feature/F-032-codigos-sin-espacios
ENTORNO LISTO. Puedes trabajar.
```

Los 61 avisos de `ruff` son **los mismos de antes de esta rama**: deuda previa.
Los cuatro ficheros que estos dos bloques tocan pasan `ruff check` limpios.

---

## Ficheros tocados en T6–T10

| Fichero | Qué |
|---|---|
| `services/postventa-api/domain/models/extraccion.py` | **producción**: `CAMPOS_DE_CODIGO` y `sanear_valor_leido`; nota fechada en la cabecera |
| `services/postventa-api/application/pipelines/paso_extraccion.py` | **producción**: el saneo en `_completar_y_sanear` + el aviso de R15; docstring del módulo corregida |
| `services/postventa-api/interface_adapters/api/cuerpos.py` | **producción**: el saneo en `a_extraccion`/`a_campo`, sin avisos y sin tocar el contrato |
| `services/postventa-api/tests/test_f032_saneo_en_la_extraccion.py` | **nuevo**: 32 tests, R11–R16 por los dos caminos y de borde a borde |
| `specs/F-032-codigos-sin-espacios/tasks.md` | T6–T10 marcadas |
| `progress/impl_F-032.md`, `progress/current.md` | este informe y el rastro del arnés |

`git diff --stat f434f02 HEAD`:

```
 .../application/pipelines/paso_extraccion.py       |  38 +-
 services/postventa-api/domain/models/extraccion.py |  51 ++
 .../interface_adapters/api/cuerpos.py              |  37 +-
 .../tests/test_f032_saneo_en_la_extraccion.py      | 805 +++++++++++++++++++++
 specs/F-032-codigos-sin-espacios/tasks.md          |  10 +-
 5 files changed, 929 insertions(+), 12 deletions(-)
```

**Ni un fichero prohibido.** `git diff --stat dev` sobre
`domain/models/aprobacion.py`, `tests/test_f028_huella_intacta.py`,
`tests/test_f028_espacios_codigos.py`, `services/postventa-front/`, `infra/`,
`.env`, `infrastructure/persistencia/**`, `config/prompts.yaml`,
`domain/models/cierre.py` e `infrastructure/sigrid/consultas.py` devuelve
**vacío**. Ninguna escritura contra Azure, Sigrid, SharePoint ni PostgreSQL:
todo es memoria y dobles. La tercera construcción de `ExtraccionParte`
—`archivar.py:201`, la que `design.md` §4.3 deja fuera a propósito— **no se ha
tocado**: es alcance de F-031.

---

## Lo que queda fuera de este encargo

Los bloques 4 y 5 **no se han empezado**:

- **B4 · los controles que no pueden moverse** (T11, T12):
  `tests/test_f032_huella_intacta.py` con los tres literales medidos en T1 está
  **por escribir**, igual que los controles de alcance de R17, R22, R24, R29 y
  el de R23 (reprocesar limpia el código y, si eso mueve la huella, la decisión
  anterior deja de contar).
- **B5 · documentación, medición y cierre** (T13–T15): la precisión de F-032 en
  la semántica 5 de `docs/ARCHITECTURE.md`, el defecto **D-A1** escrito para el
  humano, la **medición previa de `design.md` §6.3** contra la base y la
  campaña de mutación.

### Verificaciones MANUAL pendientes del humano

Sin cambios respecto al encargo anterior, y siguen todas vivas:

- **R26 · la medición previa del §6.3, antes de desplegar.** Consulta de solo
  lectura sobre `postventa` que lista los partes archivados cuyos códigos
  guardados llevan algún blanco. **Sin ella no se despliega**, y va antes
  porque re-archivar pisa `postventa.archivos.nombre_fichero`, que es la única
  pista del nombre viejo.
- **R27** · si devuelve filas, esos partes **no se re-archivan desde el
  circuito**: lo decide una persona.
- **El caso real de punta a punta**, con escritura en el ERP de producción:
  exige autorización expresa del humano **para esa incidencia concreta**,
  dry-run previo y confirmación. Es el criterio de aceptación 1 y solo se puede
  dar por cumplido ahí.

---

## Evidencias

Números **medidos** —no estimados— en este árbol (`66b9152`, T10 cerrada) con
el intérprete del servicio. Sustituyen a los del bloque 1.

| Evidencia | Valor | De dónde sale |
|---|---|---|
| Tests ejecutados · servicio `api` | **2874 passed, 15 skipped, 0 failed** | `bash harness/init.sh` |
| Tests ejecutados · arnés | **62 passed** | `bash harness/init.sh`, sección de la raíz |
| Tests del fichero nuevo de los bloques 2 y 3 | **32 passed** (eran **21 failed / 8 passed** en la fase RED de T6) | `pytest tests/test_f032_saneo_en_la_extraccion.py` |
| Tests añadidos por esta feature, en total | **140** (108 de T2 + 32 de T6) | los dos ficheros `test_f032_*` |
| Cobertura de las líneas cambiadas | **100,0 % de 12 líneas (12/12)**, umbral 80 %, nivel `critico` | línea `PUERTA COBERTURA` de `init.sh` |
| Tiempo de ejecución de la suite | **44,27 s** dentro de `init.sh`; **32,03 s** lanzada a solas | la propia salida de pytest |
| Mutantes generados y supervivientes | **NO EJECUTADO todavía**, con motivo | ver abajo |

**Fase RED**: hecha, con la traza real pegada (T6, arriba: 21 fallos, todos por
valor o por `ImportError` de una pieza que aún no existía, ninguno por error de
recogida) y una comprobación en rojo adicional para el test de `/api/estado`
que T10 añadió fuera de aquella tanda.

**Por qué no hay campaña de mutación todavía**: es la tarea **T15, del bloque
5**, y este encargo era T6–T10. La campaña es cara, no corre dentro de
`init.sh` y se lanza **al terminar** la feature: mutar ahora dejaría fuera lo
que el bloque 4 va a añadir —los controles de la huella y los de alcance— y
habría que repetirla entera. Queda como lo primero que se mide al cerrar, y el
nivel `critico` exige **cero supervivientes**, cada uno con test nuevo o con
justificación escrita.
