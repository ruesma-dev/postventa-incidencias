<!-- progress/impl_F-049.md -->
# F-049 · Las villas que crea el archivo, siempre con tres cifras — Informe del implementer

Rama `feature/F-049-villa-tres-cifras` (desde `dev`, alta en `1d574bf`). Rigor
`critico`. Sin push. `harness/features.json` e `infra/00_vars_postventa.ps1`
sin tocar.

## 0 · Qué cambió, en una frase

`nombre_derivado_de_unidad` crea la villa con **al menos tres cifras**
(`VILLA 008`, `VILLA 013`, `VILLA 1000`) en vez de dos; **cómo se casa no
cambia** (`VILLA 001`, `VILLA 01` y `VILLA 1` siguen siendo la villa 1); y la
spec de F-013 y los documentos lo dicen con recuadros fechados el 2026-09-25.

## 1 · Commits

| Commit | Tarea | Qué |
|---|---|---|
| `e90f47a` | T1 | spec breve `specs/F-049-villa-tres-cifras/` (requirements R1–R4, design, tasks) |
| `684021d` | T2 | **RED**: `tests/test_f049_villa_tres_cifras.py` (42 rojos, 47 verdes) |
| `6f16b4a` | T3 | `:02d` → `:03d` + docstrings, y la cascada de tests de F-013 (§3) |
| `161cf7c` | T4 | recuadros en `specs/F-013-archivo-posventa/` |
| `8a8b11c` | T5 | recuadros en `docs/INTEGRACION.md` §3 y `docs/DESPLIEGUE.md` §9 |
| `46a6692` | T6 | `progress/mutacion_F-049.md` (campaña del arnés + mutación a mano) |
| (T7) | T7 | este informe, `progress/current.md`, tareas marcadas, orden de imports del test |
| `556e1b2` en **`azure-apps`** | T5 | el gemelo `postventa_incidencias.md`, mismo recuadro que INTEGRACION (commit local, sin push) |

## 2 · Ficheros tocados

**Código de producción** (una línea de código y docstrings):

- `services/postventa-api/domain/models/destino_posventa.py`:
  `return f"VILLA {int(encaje['n']):03d}"`; docstring de la función (`VILLA
  NNN`, al menos tres cifras, el ancho es solo del nombre que se crea) y una
  mención en el docstring del módulo.

**Tests nuevos**: `services/postventa-api/tests/test_f049_villa_tres_cifras.py`
(89 casos):

- R1: 13 anchos (`1`→`001`, `8`, `13`, `99`, `100`, `999`, `1000`, `12345`,
  ceros del `con.cod` que no cuentan —`008`, `0013`—, `0`, dos blancos,
  extremos); lo que no cumple el patrón sigue siendo `None`; las 15 de la 0677.
- R2: `VILLA 001`/`VILLA 01`/`VILLA 1`/`Villa 001` casan con la villa 1 y solo
  con ella; `VILLA 001` no casa ni se parece a la 10 ni a la 100; **la
  biblioteca reorganizada** (`VILLA 001` … `007`, `012`, `013`, árbol nuevo en
  el test) resuelta con el resolutor real: 1–7, 12 y 13 sin crear nada; 8–11,
  14 y 15 crean `VILLA 0NN` + hoja; `VILLA 01` junto a `VILLA 001` →
  `unidad_ambigua`.
- R3: para las 15, lo creado es admisible (R38), casa con su unidad y solo con
  ella (R46, R50); y la segunda resolución tras crear en el doble no crea nada
  (R39).
- R4: cada documento enmendado tiene un recuadro con cabecera «Enmienda del
  2026-09-25 (F-049)» que cita literal cada premisa, la premisa sigue fuera
  del recuadro, el recuadro dice lo nuevo y quién lo decidió; el runbook §9
  dice «crearía `VILLA 008`». Con 5 controles negativos y 1 positivo del
  propio control.

**Documentación**:

- `specs/F-013-archivo-posventa/requirements.md`: recuadros en la cabecera,
  §0 ter (T4-1 y T4-5), vocabulario («Nombre derivado de la unidad»), **R37**,
  **R31** (el resultado esperado con la biblioteca reorganizada) y **R42** (el
  aviso: qué villas se crearán). R42 no estaba en el encargo: lo añadí porque
  nombra `VILLA 08` … `VILLA 15` como lo que se crearía, y dejarlo así
  contradiría R31 enmendado.
- `specs/F-013-archivo-posventa/design.md`: recuadros en la cabecera
  (incluye «donde diga `VILLA NN` sin más —§7.1, §9 ter, §10—, léase tres
  cifras»), **§1** (la medición del 2026-09-25), **§4.5**, **§4.6** (cita
  `NN = f"{int(n):02d}"`, nueva `:03d`) y **§7.3** (pasos 2 y 3).
- `specs/F-013-archivo-posventa/tasks.md`: «Después del merge», paso 2
  (con la nota de que el 23 ejecuta el dominio **de la copia local**: hay que
  lanzarlo desde una copia que ya lleve F-049).
- `docs/INTEGRACION.md` §3, `docs/DESPLIEGUE.md` §9 (la salida esperada de
  R31: «crearía `VILLA 008` + `PARTES FIRMADOS`» … y el aviso del paso 3).
- `C:\Users\pgris\PycharmProjects\azure-apps\postventa_incidencias.md`: el
  mismo recuadro que INTEGRACION §3 (es su gemelo; no menciona el runbook).
- Nada de identificadores (el barrido de `test_f006_repo_sin_identificadores.py`
  y `test_f005_integracion_sin_secretos.py`, en verde).

## 3 · Tests de F-013 tocados (solo donde fijaban el ancho del nombre creado)

Todos los cambios son de `VILLA NN` → `VILLA 0NN` **en el nombre que crea el
sistema**. Los **datos medidos** de T2 (`VILLA 01` … `VILLA 07`,
`UNIDADES_EN_POSVENTA`, `HOJAS_EN_POSVENTA`, `arbol_0677`, los `_villa(n)` de
carpetas existentes) no se han tocado: son la foto del 2026-09-24.

| Fichero | Test / dato | Cambio |
|---|---|---|
| `test_f013_destino_dominio.py` | `TABLA_4_6` | columna «nombre derivado» `VILLA 01…15` → `VILLA 001…015`; última columna de 8–15 `crea VILLA 0NN y su PARTES FIRMADOS`. La columna «carpeta en Posventa hoy» (medida) sigue `VILLA 01…07` |
| ídem | `test_f013_r37_fuera_del_patron_no_se_inventa` | 4 filas: `VILLA 13`→`VILLA 013`, `VILLA 05`→`VILLA 005` (×3) |
| ídem | `test_f013_r46_un_con_res_que_no_acaba_en_su_villa_no_casaria` | `derivado == "VILLA 013"` (y su docstring) |
| `test_f013_resolver_destino.py` | `test_f013_r35_villa_07_no_impide_crear_la_unidad_5` | creaciones `VILLA 005` |
| ídem | `CREACIONES` (usada por `test_f013_r34_se_anota_…` y `test_f013_r39_lo_creado_casa_…`) | `toda-la-ruta` y `desde-incidencias`: `VILLA 005`; `la-villa-13`: `VILLA 013` |
| ídem | `test_f013_r37_la_unidad_nueva_se_llama_villa_nn` | `(INC, "VILLA 008")` (nombre del test sin cambiar) |
| ídem | `test_f013_r46_una_villa_cuyo_con_res_no_acaba_en_su_numero_es_nombre_no_casaria` | candidatas `("VILLA 013",)` (y docstring) |
| ídem | `test_f013_r50_una_carpeta_que_se_crearia_para_dos_unidades_es_compartida` | candidatas `("VILLA 013",)` |
| ídem | `test_f013_r17_con_base_todo_cuelga_de_ella` | creaciones y destino con `VILLA 013` |
| ídem | `test_f013_r39_en_conjunto_tras_crear_lo_anotado_las_15_resuelven_sin_crear` | el listado final: `VILLA 01…07` (medidas) + `VILLA 008…015` (creadas) |
| ídem | `test_f013_r31_*` (tabla y en conjunto) | sin cambio propio: leen `TABLA_4_6` |
| `test_f013_paso_archivo_posventa.py` | helpers **nuevos** `_villa_creada(n)` / `_hoja_creada(n)` (tres cifras); `_villa`/`_hoja` siguen para las existentes | — |
| ídem | `test_f013_r15_la_unidad_que_falta_se_crea_tras_la_traza_previa_y_en_orden` | `VILLA 008` y rutas creadas |
| ídem | `test_f013_r15_sin_ninguna_carpeta_se_crean_los_cuatro_niveles_uno_a_uno` | `VILLA 005` |
| ídem | `test_f013_r40_el_log_de_carpeta_creada_es_un_aviso_del_logger_del_paso` | rutas creadas |
| ídem | `test_f013_r21_si_falla_una_creacion_no_se_sube_y_el_reintento_sigue_donde_quedo` | rutas creadas |
| ídem | `test_f013_r21_en_la_carrera_de_f033_no_se_crea_ni_se_sube` | la traza de «la otra petición» en la hoja **creada** (`VILLA 008`): la otra petición habría resuelto lo mismo |
| `test_f013_archivar_http.py` | `test_f013_t13_posventa_crea_lo_que_falta_con_el_mismo_archivador` | `VILLA 013` (y docstring) |
| `test_f013_scripts_infra.py` | `R31_0677` (el ensayo del script 23, `test_f013_t14_la_regla_da_lo_de_r31_para_la_0677`) | `f"VILLA {n:03d}"` para 8–15 (y docstring) |
| ídem | `test_f013_t14_sin_ninguna_obra_crearia_con_el_nombre_de_r36` | `VILLA 005` |

**No tocado a propósito**: `test_f013_r20_tras_crear_la_carpeta_a_mano_el_reintento_archiva`
(Posventa crea **a mano** `VILLA 08`: sigue casando con la villa 8, que es
justo lo que F-049 promete no romper); `test_f013_documentacion.py` (exige
«`VILLA NN`» en INTEGRACION §3, que sigue ahí: los recuadros no borran);
`test_f013_fabricas.py` (un docstring genérico). Ningún test de F-006, F-019,
F-031, F-032, F-033 ni F-034; los controles de alcance de F-031…F-034 y el de
F-013 solo corren en sus ramas y se saltan en esta.

**Tampoco tocado** (código de producción con «`VILLA NN`» como rótulo
genérico, sin ancho): el mensaje de `unidad_sin_nombre_derivable` en
`application/pipelines/destino_archivo.py` («se deriva «VILLA NN»») y un
comentario de `config/settings.py`; y `docs/ARCHITECTURE.md` («la unidad, como
`VILLA NN`»). Cubiertos por el «léase tres cifras» de los recuadros de
cabecera. Si el líder prefiere cambiarlos, es un cambio de texto aparte.

## 4 · Decisiones

1. **Los datos medidos no se reescriben.** La biblioteca reorganizada entra
   como árbol **nuevo** en los tests de F-049; la de T2 sigue siendo la de los
   tests de F-013. Así la tabla de §4.6 sigue siendo «lo que se midió el
   2026-09-24», y lo del 2026-09-25 tiene sus propios tests.
2. **Hojas de la biblioteca reorganizada [NO MEDIDO].** El encargo no trae
   qué hojas tienen `VILLA 001` … `VILLA 013`. No lo invento: el R31
   enmendado dice «resolvería, o crearía `PARTES FIRMADOS` si no tiene hoja;
   lo dice el 23». En el test, todas con `PARTES FIRMADOS` (neutro para el
   nivel de unidad).
3. **`VILLA 01` + `VILLA 001` juntas → `unidad_ambigua`.** Consecuencia del
   casado por número, que no se toca; la documento en R31, §4.5, DESPLIEGUE e
   INTEGRACION y la fijo con un test.
4. **El 23 corre el dominio de la copia local**: lo dejo escrito en tasks.md
   y DESPLIEGUE §9 (hay que relanzarlo desde una copia con F-049, o dirá
   «crearía `VILLA 08`»).

## 5 · Verificación

- `bash harness/init.sh`: **ENTORNO LISTO**. Suite del servicio api:
  **4.356 passed, 52 skipped en 144,18 s**; front y raíz en verde (62 passed).
- `PUERTA COBERTURA: 100.0% de 1 líneas cambiadas cubiertas (1/1, umbral 80%,
  nivel critico)`.
- ruff: el test nuevo tenía un aviso de orden de imports, corregido con
  `ruff --fix` en T7; tras él, `init.sh` vuelve a los 61 avisos de deuda
  previa (los mismos que al empezar). Última ejecución de `init.sh`, tras T7:
  4.356 passed, 52 skipped en 85,93 s; cobertura 100 % (1/1).

## 6 · Fase RED

Comando (desde `services/postventa-api`, commit `684021d`, antes de tocar el
código):

```
.venv/Scripts/python.exe -m pytest tests/test_f049_villa_tres_cifras.py -q -p no:cacheprovider
```

Resultado: `42 failed, 47 passed in 3.54s`. Rojos: los 13 anchos de R1 salvo
`100`, `999`, `1000`, `12345` (que ya salían bien con `:02d`), las 15 de la
0677, las 6 creaciones de R2, las 6 segundas resoluciones de R3 y los 6 de R4.
Verdes: el casado (R2), R3 de propiedad (con `VILLA 08` también casaba) y los
controles del control de R4. Trazas reales:

```
__ test_f049_r1_la_villa_se_crea_con_tres_cifras[0677.03VILLA 8.-VILLA 008] ___
    def test_f049_r1_la_villa_se_crea_con_tres_cifras(cod, nombre):
        """R1 · `VILLA 008`, `VILLA 013`; de tres cifras en adelante, tal cual."""
>       assert nombre_derivado_de_unidad(cod, codigo_obra="0677") == nombre
E       AssertionError: assert 'VILLA 08' == 'VILLA 008'
E         
E         - VILLA 008
E         ?       -
E         + VILLA 08
```

```
___________ test_f049_r2_las_que_faltan_se_crean_con_tres_cifras[8] ___________
        villa = f"VILLA {n:03d}"
>       assert resuelto.carpetas_por_crear == ((INC, villa), (f"{INC}/{villa}", FIRMADOS))
E       AssertionError: assert (('677  MIRAS...ES FIRMADOS')) == (('677  MIRAS...ES FIRMADOS'))
E         
E         At index 0 diff: ('677  MIRASIERRA/PARTES INCIDENCIAS', 'VILLA 08') != ('677  MIRASIERRA/PARTES INCIDENCIAS', 'VILLA 008')
```

```
    def _comprobar(documento: Path, premisas: tuple[str, ...], nuevo: tuple[str, ...]) -> None:
        recuadros, resto = _partes(documento)
>       assert recuadros, f"{documento.name}: ningún recuadro fechado de F-049"
E       AssertionError: DESPLIEGUE.md: ningún recuadro fechado de F-049
E       assert []
```

Tras `:03d` (T3): los 83 de R1–R3 en verde y los 6 de R4 en rojo hasta T4/T5;
tras T5, `89 passed`.

## 7 · Qué queda fuera y qué falta

- **Fuera**: `infra/00_vars_postventa.ps1` (el corte, del líder); renombrar o
  mover carpetas existentes (F-013 R43); cualquier cambio del casado.
- **MANUAL pendiente (humano)**: relanzar el paso 2 del corte (R31) **desde una
  copia con F-049** y comprobar que sale lo del R31 enmendado: 1–7, 12 y 13
  «resolvería» (o «crearía `PARTES FIRMADOS`» donde no haya hoja), 8–11, 14
  y 15 «crearía `VILLA 008`» …, ninguna «bloquearía». Y, tras el
  despliegue, R42 con el aviso a Posventa enmendado.
- **Para el líder**: `azure-apps` tiene el commit local `556e1b2` sin push;
  R42 se enmendó sin estar en el encargo (§2); los rótulos genéricos
  «`VILLA NN`» de producción no se cambiaron (§3).

## Evidencias

| Evidencia | Valor medido |
|---|---|
| Tests ejecutados | servicio api **4.356 passed, 52 skipped**; raíz 62 passed; front en verde (caché); F-049: **89 passed** |
| Cobertura de las líneas cambiadas | **100,0 %** (1/1 línea de producción, `PUERTA COBERTURA` de `init.sh`) |
| Mutantes (arnés) | `python -m harness.mutacion --feature F-049 --timeout 900 --workers 6`: **0 generados** (10 líneas en alcance, 9 de docstring; la de código solo tiene un formato de f-string, que la herramienta no muta) |
| Mutantes (a mano) | **9 generados, 7 muertos, 2 supervivientes equivalentes** (`:03` y `:0=3d`, iguales a `:03d` para todo entero no negativo, y `<n>` es `[0-9]+`). Análisis en `progress/mutacion_F-049.md` |
| Tiempo de la suite | **85,93 s** (servicio api, última `init.sh`, tras T7; la anterior, 144,18 s) |

## Correcciones tras la review (RECHAZADA, `progress/review_F-049.md` §6)

Solo documentación; código y tests sin tocar.

1. `progress/current.md`: el bloque de F-049 lleva los dos comandos exactos
   del paso 2 y la salida esperada nueva, y anota como **hecho** (2026-09-25,
   humano) que el paso 2 contra la red real, desde la copia con `:03d`, dio
   `DESTINO DE POSVENTA : PASA` con «crearía `VILLA 008` … `VILLA 015`», 012 y
   013 «crearía `PARTES FIRMADOS`», 001–007 «resolvería» y ninguna
   «bloquearía». El bloque de F-013 conserva su salida antigua con una línea
   fechada que remite a la nueva.
2. `progress/mutacion_F-049.md`, M8: el motivo era falso. `:0=3d` es igual que
   `:03d` para **todo** entero, negativos incluidos (`-05` en los dos);
   recuadro de corrección que cita la frase antigua, y la comprobación
   numérica ampliada a `-200000 … 199999` (`True`).
