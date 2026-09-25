# F-049 · Las villas que crea el archivo, siempre con tres cifras — Review

- **Veredicto:** CHANGES_REQUESTED (RECHAZADO)
- **Rama:** `feature/F-049-villa-tres-cifras`, `993dcbe` (base `884a0ee` de `dev`)
- **Fecha:** 2026-09-25 · reviewer

El código y los tests están bien: el cambio es una sola línea (`:02d` →
`:03d`), el casado no se toca, la cascada de F-013 se limita al ancho del
nombre que se crea y las enmiendas citan la premisa sin borrarla. Se rechaza
por dos cambios pequeños y concretos del rastro documental (§6): la
verificación MANUAL de F-049 no está en `progress/current.md` con su comando
exacto, y el bloque de F-013 de ese mismo fichero sigue diciendo la salida
esperada antigua del paso 2 del corte; además, la justificación de M8 en el
informe de mutación da un motivo que no es cierto, justo en el texto que el
humano tiene que aceptar por escrito. Aparte queda la aceptación escrita de
los equivalentes M7 y M8, que no depende del implementer (§4).

## 1 · Nivel de rigor

`critico`, declarado en `harness/features.json`, y válido según
`bash harness/init.sh`. Exige: fase RED con traza real, cobertura de las líneas
cambiadas ≥ 80 %, campaña de mutación con los totales comprobados por mí,
cero supervivientes salvo equivalentes aceptados **por escrito por el humano**
(incluidos los de mutación a mano, C4 bis aclarado el 2026-09-25) y las
verificaciones MANUAL listadas con su comando exacto.

## 2 · Verificaciones que he hecho yo

| Qué | Resultado |
|---|---|
| `bash harness/init.sh` (tal cual) | **ENTORNO LISTO**. api: 4356 passed, 52 skipped (81,85 s); raíz: 62 passed; front en verde (caché); `PUERTA COBERTURA: 100.0% de 1 líneas cambiadas cubiertas (1/1, umbral 80%, nivel critico)`; ruff con 61 avisos, la misma deuda previa |
| Diff de producción (`git diff 884a0ee...HEAD`) | solo `domain/models/destino_posventa.py`: la línea `return f"VILLA {int(encaje['n']):03d}"` y los docstrings. Ni un import nuevo. `_casa_con_la_unidad`, `clave_de_unidad`, `parecidas_de_unidad`, `PATRON_CODIGO_UNIDAD`, `application/`, `infrastructure/` e `infra/`: **sin tocar** |
| Fase RED reproducida | `git archive 684021d` a una copia en mi scratchpad y ahí `pytest tests/test_f049_villa_tres_cifras.py`: **42 failed, 47 passed**, igual que el informe. Ese commit solo añade el fichero de test (388 líneas) |
| Alcance recalculado (`harness.alcance.alcance_de_feature("F-049")`) | 1 fichero, **10 líneas** (29, 30, 475, 478–483, 493), igual que el informe |
| Número de mutantes recalculado (`generar_mutantes`, cálculo puro) | **0**, igual que el informe |
| Prueba de control del cero | `generar_mutantes` sobre el mismo fichero **sin el filtro de alcance**: **39** mutantes, 3 de ellos dentro de `nombre_derivado_de_unidad` (líneas 487 y 491, fuera del diff). El generador funciona, así que el cero es legítimo: la línea 493 solo tiene una especificación de formato dentro de una f-string, y la herramienta no tiene operador para eso |
| Campaña reejecutada («Tiempo total» 0,0 s < 5 min) | `python -m harness.mutacion --feature F-049 --salida <scratchpad>`: 0 generados, 0 muertos, 0 supervivientes, 0 timeouts. Coincide. `git status` limpio después |
| Mutación a mano, reejecutada por mí | en una copia desechable (`git archive HEAD`), los 9 mutantes del informe contra `test_f049_*` + `test_f013_*` con `-x`: **M1–M6 y M9 muertos, M7 y M8 sobreviven**. Coincide fila a fila, también en el test que caza cada uno (M4, por `…VILLA 0013.-VILLA 013`). Base sin mutar: 1098 passed, 17 skipped |
| Mutantes a mano propios (5 más) | `encaje['n'].zfill(3)` sin `int()` y `:03x`: **muertos**. `str(int(n)).zfill(3)`, `n.lstrip('0').zfill(3)` y `:03n`: sobreviven, y los tres son equivalentes (para `[0-9]+`; `:03n` solo cambiaría con un `setlocale` que nadie hace). No descubren ningún hueco en los tests |
| Equivalencia de M7 y M8, numérica | `format(n,'03') == format(n,'03d') == format(n,'0=3d')` para `n` en −200000…200000: **True**. Ojo, `format(-5,'03d') == format(-5,'0=3d') == '-05'`: ver §6, cambio 2 |
| Gemelo `azure-apps` `556e1b2` | 1 fichero (`postventa_incidencias.md`), +16 líneas, **el mismo recuadro** que `docs/INTEGRACION.md` §3. Sin GUID, IP, host, correo, cadena de conexión ni clave. Commit local en `master`, sin push |
| Enmiendas sin borrar | `git diff --numstat`: `specs/F-013-*/{requirements,design,tasks}.md`, `docs/INTEGRACION.md` y `docs/DESPLIEGUE.md` tienen **0 líneas borradas**. Solo se añaden recuadros |
| PDF o datos personales en git | `git log --diff-filter=A 884a0ee..HEAD`: solo la spec, el test y los dos informes |
| Árbol limpio al terminar | `git status --short` vacío; copias del scratchpad borradas |

## 3 · Checkpoints

### C1 — El arnés está completo y en verde
- [x] `bash harness/init.sh` exit 0 (ENTORNO LISTO).
- [x] Existen los ficheros base (los comprueba `init.sh`).

### C2 — El estado es coherente
- [x] Una sola `in_progress` (F-049).
- [x] Rama `feature/F-049-villa-tres-cifras`.
- [x] `progress/current.md`: arriba la sesión activa (F-049); siguen los
      bloques de F-013 porque su merge y su corte están pendientes y ahí
      viven sus MANUAL. Lo que esté desfasado va en C4 (cambio 1).
- [x] Toda feature `done` con resumen en `history.md` (F-049 no es `done`).

### C3 — Arquitectura y convenciones
- [x] Hexagonal: el cambio vive en `domain/models/`, sin imports nuevos (los
      del módulo son `re`, `unicodedata`, stdlib y `domain.models.nombrado`).
- [x] Primera línea con la ruta en `destino_posventa.py` y en el test nuevo.
- [x] Sin `print()`, sin TODOs, sin secretos y sin dependencias nuevas.
- N/A · La unidad de trabajo es el parte: F-049 no toca troceado, remesas ni
  partes, solo el nombre de una carpeta.
- N/A · Nada se archiva sin validaciones / dry-run contra Sigrid: el orden
  del paso de archivo (F-013) no se toca, y el resolutor sigue sin crear nada
  (lo comprueba el `finally` de `_resolver` en el test nuevo). Sin escritura
  en Sigrid.
- N/A · Lo manuscrito, firma y conformidad: F-049 no los toca.
- N/A · Reprocesar no duplica: F-049 no toca hash ni trazas; R3 comprueba
  además que la segunda resolución no crea nada.
- N/A · Estados de Sigrid: F-049 no los toca.
- [x] Ningún parte escaneado ni PDF en git (`git log --diff-filter=A`).

### C3 bis — Documentos que entran de fuera
- N/A · F-049 no añade ni modifica nada en `docs/referencia/`.

### C4 — La verificación es real
- [x] Cada requisito tiene tests `test_f049_rN_*` y pasan (tabla §5).
- [x] Sin red ni BBDD: dobles de `tests/utiles_destino.py` y ficheros del
      repositorio o de `tmp_path`.
- [ ] **MANUAL listadas en `progress/current.md` con su comando exacto.** El
      bloque de F-049 dice «relanzar el paso 2 del corte (R31) desde una copia
      con F-049», sin comando y sin la salida que tiene que dar. El comando
      solo está en el bloque de F-013, **que sigue esperando la salida
      antigua**: «VILLA 01–03 y 05–07 «resolvería», VILLA 04 «crearía
      `PARTES FIRMADOS`», 08–15 «crearía `VILLA NN`» … Cualquier diferencia:
      no se despliega». Con la biblioteca reorganizada y F-049, el 23 va a
      decir otra cosa (12 y 13 «resolvería», «crearía `VILLA 008`»). Es la
      única lista de trabajo del humano para el corte. Cambio 1.

### C4 bis — El rigor declarado se cumple
- [x] `rigor: critico` declarado y válido.
- [x] **Fase RED**: el informe §6 trae el comando, `42 failed, 47 passed` y
      tres trazas reales (ancho en R1, creación en R2, recuadro en R4). La he
      reproducido (§2).
- [x] **Cobertura**: `[OK]` 100,0 % (1/1).
- [x] **Mutación**: `progress/mutacion_F-049.md` lo generó la herramienta.
      Alcance (10 líneas) y mutantes (0) recalculados por mí; el cero pasa la
      prueba de control (39 sin filtro de alcance). Como la herramienta no
      muta la línea, hay mutación a mano, también reejecutada por mí (§2).
- [x] **Muertos comprobados**: campaña del arnés reejecutada (0,0 s < 5 min),
      mismos totales; y los 9 mutantes a mano, uno a uno, mismo resultado.
- N/A · **Coste por mutante**: con 0 mutantes la fórmula divide por cero.
  Justificación: no hay ningún veredicto del arnés que pueda estar
  envenenado. Los muertos a mano los he reejecutado yo en una copia limpia
  (entre 1,9 y 2,4 s por mutante con `-x`, que es lo que tarda en caer el
  primer test; la base sin mutar tarda 8,4 s).
- [ ] **Supervivientes con análisis y aceptación del humano**: M7 (`:03`) y
      M8 (`:0=3d`) tienen su análisis y **los dos son equivalentes de
      verdad**: lo he comprobado numéricamente y sobreviven también en mi
      copia. Pero en `critico` necesitan la **aceptación escrita del
      humano**, que está **pendiente** (la gestiona el líder). Además, el
      motivo que se da para M8 no es cierto (cambio 2). Mi juicio: **la
      equivalencia se sostiene y recomiendo aceptar los dos**, pero sobre el
      texto corregido.
- [x] **Evidencias**: están los cuatro números y los workers de la campaña
      (6).
- [x] Ningún N/A de este bloque sin justificar.
- N/A · **Punto 7 del protocolo (orden)**: el requisito central de F-049 es un
  **valor**, el ancho del nombre, no un orden entre colaboradores. F-049 no
  mueve ninguna llamada ni ninguna puerta; las de F-013 (traza previa antes
  de crear, resolver antes de subir) siguen fijadas por sus tests, que corren
  en verde sin cambios de orden.

### C4 ter — Rutas sensibles
- N/A · No existe `harness/rutas_sensibles.json` (solo el `.ejemplo.json`),
  y la puerta de `init.sh` no señala nada.

### C5 — Cierre de sesión
- [x] `tasks.md` T1–T7 marcadas `[x]`; un commit `F-049 Tn:` por tarea
      (`e90f47a` T1 … `993dcbe` T7) y el alta `1d574bf`.
- [x] Sin ficheros sin trackear. `.claude/worktrees/agent-a6e2f9bed1d46cdbc`
      (`9e30f57`) es de otro agente, no de esta rama ni de esta campaña.
- [x] `features.json`: `in_progress`, que es el estado real hasta la review.

## 4 · Lo que el líder me pidió comprobar en especial

1. **El casado no cambia.** Confirmado en el diff: ni una línea de las
   reglas estricta ni amplia. En los tests: `VILLA 001`, `VILLA 01`,
   `VILLA 1` y `Villa 001` casan con la villa 1 y solo con ella; `VILLA 001`
   no casa con la 10 ni con la 100, ni se parece a ellas; y con la
   biblioteca reorganizada, el resolutor real da 1–7, 12 y 13 sin crear nada.
   `test_f013_r20_tras_crear_la_carpeta_a_mano_el_reintento_archiva`
   (Posventa crea `VILLA 08` a mano) sigue intacto y en verde. `VILLA 01`
   junto a `VILLA 001` da `unidad_ambigua`, y está documentado.
2. **Los tests de F-013, tocados solo donde fijaban el ancho del nombre
   creado.** He revisado el diff línea a línea en los cinco ficheros: todos
   los cambios son `VILLA NN` → `VILLA 0NN` en lo que **crea** el sistema.
   Los datos medidos del 2026-09-24 (`VILLA 01…07`, la columna «carpeta hoy»
   de `TABLA_4_6`, `arbol_0677`, `_villa(n)`) están intactos. Un matiz, que
   no bloquea: en `test_f013_r21_en_la_carrera_de_f033_no_se_crea_ni_se_sube`
   el cambio a `_hoja_creada(8)` **no hacía falta**, porque el test solo
   compara la traza consigo misma y pasaría con `_hoja(8)`. Es coherente (la
   otra petición habría creado `VILLA 008`) y no debilita nada.
3. **Las enmiendas citan la premisa sin borrarla.** 0 líneas borradas en los
   cinco documentos. Además, `test_f049_r4_*` comprueba que cada premisa
   aparece literal dentro de un recuadro y también fuera, en su sitio, y
   tiene cinco controles negativos y uno positivo del propio control. R42 se
   enmendó sin estar en el encargo, y está bien hecho: si no, contradiría a
   R31.
4. **El gemelo de `azure-apps`** (`556e1b2`) es el mismo recuadro que
   INTEGRACION §3, sin identificadores y sin push.

## 5 · Cobertura: requisito → test

| Requisito | Tests (`tests/test_f049_villa_tres_cifras.py`) |
|---|---|
| R1 · el nombre creado tiene al menos tres cifras; los ceros del `con.cod` no cuentan; fuera del patrón, `None` | `test_f049_r1_la_villa_se_crea_con_tres_cifras` (13 casos, del 0 al 12345, `008`, `0013`, dos blancos, extremos), `test_f049_r1_lo_que_no_cumple_el_patron_sigue_sin_nombre` (6), `test_f049_r1_las_15_villas_de_la_0677` (15); además `test_f013_r37_*` y `TABLA_4_6` actualizados |
| R2 · el casado no cambia; la biblioteca reorganizada; `VILLA 01` + `VILLA 001` → `unidad_ambigua` | `test_f049_r2_tres_dos_o_una_cifra_son_la_misma_villa_1` (4), `test_f049_r2_villa_001_no_es_la_10_ni_la_100` (2), `test_f049_r2_la_biblioteca_reorganizada_casa_sin_crear` (9), `test_f049_r2_las_que_faltan_se_crean_con_tres_cifras` (6), `test_f049_r2_villa_01_y_villa_001_juntas_son_ambiguas` |
| R3 · lo creado casa consigo mismo y solo con su unidad (R38, R39, R46, R50) | `test_f049_r3_cada_villa_creada_casa_con_su_unidad_y_con_ninguna_otra` (15), `test_f049_r3_la_segunda_resolucion_la_encuentra` (6); además `test_f013_r39_en_conjunto_*` |
| R4 · recuadros fechados que citan la premisa sin borrarla | `test_f049_r4_la_documentacion_lleva_su_recuadro_fechado` (5 documentos), `test_f049_r4_el_runbook_de_r31_dice_crearia_villa_008`, `test_f049_r4_el_control_caza_lo_que_no_es_enmendar` (5), `test_f049_r4_el_control_acepta_una_enmienda_bien_hecha` |
| acceptance 1–2 de `features.json` | R1 y R2 |
| acceptance 3 | R4 |
| acceptance 4 | `bash harness/init.sh` en verde (§2) |

89 casos en total, los mismos que declara el informe.

## 6 · Cambios requeridos

1. **`progress/current.md`, bloque de F-049 (líneas 23–25), y bloque de F-013
   (líneas 37–40).** En el bloque de F-049, sustituir «relanzar el paso 2 del
   corte (R31) desde una copia **con F-049**» por los **dos comandos
   exactos** (el `24_ubicacion_sigrid.ps1` y el `23_destino_posventa.ps1`,
   tal y como están en el bloque de F-013), lanzados desde una copia que ya
   lleve F-049, y **la salida esperada nueva**: obra y `PARTES INCIDENCIAS`
   «resolvería»; 1–7, 12 y 13 «resolvería» (o «crearía `PARTES FIRMADOS`»
   donde no haya hoja); 8–11, 14 y 15 «crearía `VILLA 008`» … `VILLA 015`
   con su hoja; ninguna «bloquearía». Y en el bloque de F-013, junto a
   «Tiene que salir exactamente lo de R31 (VILLA 01–03 … 08–15 «crearía
   `VILLA NN`» …)», una línea fechada que diga que esa salida la sustituyó
   F-049 el 2026-09-25 y remita al bloque de arriba (sin borrar la antigua,
   como en el resto de enmiendas). Motivo: con «Cualquier diferencia: no se
   despliega», el humano pararía el corte al comparar con la salida vieja.
2. **`progress/mutacion_F-049.md`, viñeta de M8.** Dice: «Solo se
   distinguiría con un negativo, y `<n>` … nunca lo es». **No es cierto**:
   `format(-5, "03d") == format(-5, "0=3d") == "-05"`. El `0` delante del
   ancho ya pone relleno `0` y alineación `=`, así que `:0=3d` es igual que
   `:03d` **para todo entero**, también los negativos. Hay que corregir el
   motivo (y la frase «Comprobado numéricamente … `0 … 199999`» si se quiere
   ampliar el rango a los negativos). La conclusión, que es equivalente, se
   mantiene y queda más fuerte. Tiene que corregirse **antes** de que el
   humano lo acepte, porque lo que acepta es ese texto.

Aparte, y **no es un cambio del implementer**: antes de cerrar hace falta la
aceptación escrita del humano de M7 y M8 (C4 bis, nivel `critico`). Mi
recomendación es aceptar los dos.

## 7 · Observaciones (no bloquean)

- `test_f013_r21_en_la_carrera_de_f033_no_se_crea_ni_se_sube`: el cambio
  no hacía falta (§4.2). Se puede dejar.
- Rótulos genéricos «`VILLA NN`» sin recuadro: el mensaje de
  `unidad_sin_nombre_derivable` en
  `application/pipelines/destino_archivo.py:184`, el comentario de
  `config/settings.py:285` y `docs/ARCHITECTURE.md:153`. Los dos primeros
  quedan cubiertos por el «léase tres cifras» de las cabeceras de la spec de
  F-013; `ARCHITECTURE.md` **no**, porque no tiene ningún recuadro de F-049.
  Como el texto es genérico, no lo exijo. El líder decide si vale un recuadro
  de una línea.
- `progress/cierre_F-013.md` y `progress/review_F-013.md` siguen hablando de
  `VILLA NN` / `VILLA 08`: son actas fechadas de F-013 y está bien que no se
  toquen.

## 8 · Automejora (propuestas, no aplicadas)

1. **`CHECKPOINTS.md` C4, tercera casilla**: añadir «Si la feature cambia la
   **salida esperada** de una verificación MANUAL que ya está listada en
   `progress/current.md` (de esta feature o de otra), esa entrada lleva
   también su nota fechada. Una MANUAL con la salida esperada desfasada
   cuenta como no listada». Motivo: el R4 de F-049 enumeraba bien los
   documentos, pero se olvidó de la lista de trabajo del humano. Vale para
   cualquier proyecto: a `arnes-base`.
2. **`harness/mutacion.py`** (a `arnes-base`): un operador para los **anchos
   numéricos de la especificación de formato** de las f-strings
   (`ast.FormattedValue.format_spec`, p. ej. `03d` → `04d`). Hoy una línea
   así da 0 mutantes, y la mutación la tiene que suplir alguien a mano. Es
   el segundo caso en este repositorio en que la herramienta no ve la línea
   que importa (después de `unidades_que_casan` en F-013 T20).
3. **Protocolo del reviewer, punto 4**: cuando un informe declare
   equivalente un mutante a mano, el reviewer comprueba **numéricamente el
   motivo** que se da, no solo la conclusión. Aquí la conclusión era buena y
   el motivo, falso, y lo que el humano acepta por escrito es el motivo.
