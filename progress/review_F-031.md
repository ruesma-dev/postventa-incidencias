<!-- progress/review_F-031.md -->
# F-031 · Review · El nombrado del fichero archivado sale de lo persistido

> Revisado el **2026-09-22** sobre `feature/F-031-nombrado-persistido`
> (`958c084` .. `01c9370`, base de integración `dev` = `127e457`), contra
> `specs/F-031-nombrado-persistido/` (spec aprobada por el humano el
> 2026-09-22, D-1 a D-7), `docs/CONVENTIONS.md`, `docs/ARCHITECTURE.md` y
> `CHECKPOINTS.md`.
>
> **Nada se ha implementado ni corregido en esta revisión.** No se ha escrito
> en SharePoint, ni en Sigrid, ni en PostgreSQL, ni se ha tocado el código del
> implementer. Lo único que se ha escrito en el árbol es este fichero; la
> campaña de mutación de verificación se lanzó **fuera** de `progress/`, al
> scratchpad de la sesión, y `git status` quedó limpio.

## Veredicto

**APROBADO**, con **una condición de cierre** (no es una corrección de código):

> **La feature NO puede marcarse `done` ni mergearse a `dev` hasta que el
> humano recorra V1 (T14) y V2 (T15) y su resultado real conste por escrito.**
> El nivel `critico` exige las verificaciones `MANUAL (humano)` «con su comando
> exacto **y su resultado real**», y hoy solo está lo primero. Esto es trabajo
> del humano, no del implementer: por eso no es CHANGES_REQUESTED. Es el mismo
> patrón que cerró F-032 y F-033 (`acta de cierre de las verificaciones
> manuales`).

Los cuatro puntos que el encargo pedía mirar con lupa **están bien resueltos**:
las cinco adaptaciones de tests son ajustes al mundo real y no aflojamientos;
el 409 sale antes de tocar nada; el cotejo es normalizado; y el front tiene
tests de verdad, sobre el módulo real y con reloj inyectado.

## Nivel de rigor y puertas que exige

| | |
|---|---|
| **Declarado** en `harness/features.json` | **`critico`** (explícito, no por omisión) |
| **Exige** (`CHECKPOINTS.md` + `harness/rigor.json`) | C1–C5 + C3 bis + C4 bis · tests trazables · **fase RED** en los requisitos centrales · **cobertura** de las líneas cambiadas ≥ 80 % · **campaña de mutación** con **cero supervivientes** salvo justificación escrita · verificaciones `MANUAL (humano)` con comando exacto y resultado real |

### Lo que ha comprobado el reviewer, por su cuenta

| Puerta | Cómo se verificó | Resultado |
|---|---|---|
| Arnés | `bash harness/init.sh`, ejecutado por el reviewer | **VERDE**, exit 0. 62 passed, `PUERTA COBERTURA [OK] 100.0 % de 28 líneas cambiadas (28/28, umbral 80 %, nivel critico)`, rama correcta |
| Suites, **sin fiarse de la caché** del arnés | `pytest -q` en los dos servicios, ejecutado por el reviewer | `api`: **3.066 passed, 24 skipped**. `front`: **256 passed** (incluye el puente `node --test tests_js/*.test.js`) |
| Mutación · recálculo puro | `harness.alcance.alcance_de_feature` + `harness.mutacion.generar_mutantes`, sin ejecutar la suite | **Coincide con el informe línea por línea**: 5 ficheros, **305 líneas**, **3 mutantes**, con el mismo operador y el mismo `original -> mutado` en los tres |
| Mutación · **reejecución de la campaña** (obligatoria: el informe declara 78,6 s < 5 min) | `python -m harness.mutacion --feature F-031 --workers 3 --salida <scratchpad>` | **3 mutantes, 3 muertos, 0 supervivientes, 0 timeouts** en **66,8 s**. **Coincide con el informe.** Árbol limpio después (`git status` vacío) |
| Coste por mutante (C4 bis) | 78,6 s × 3 workers ÷ 3 mutantes = **78,6 s/mutante** (reejecución: 66,8 s) | Por encima del tiempo de la suite del servicio (65,6 s). **No es sospechosa**: la suite se ejecutó de verdad |
| Alcance H-1 | `git diff --name-only 958c084...HEAD` filtrado | `adjuntar.py`, `cerrar.py`, `paso_grafico.py`, `paso_cierre.py`: **cero líneas**. Ni la persistencia, ni el puerto, ni el DDL |
| Secretos y datos personales | Barrido sobre el diff (`AccountKey`, `subscription`, `tenant`, IPs, `Bearer`, `password`, `api_key`) y `git log --diff-filter=A` | **Cero coincidencias.** Ningún PDF ni fichero de `muestras/` entró en git |
| Lint | `ruff check` sobre los 8 ficheros tocados | `All checks passed!` (los 61 avisos del repo son deuda previa) |

## Checkpoints

### C1 — El arnés está completo y en verde
- [x] `bash harness/init.sh` termina en verde, ejecutado por el reviewer.
- [x] Existen los ocho ficheros obligatorios.

### C2 — El estado es coherente
- [x] Una sola feature `in_progress`: `F-031`.
- [x] Rama `feature/F-031-nombrado-persistido`, nunca `main` ni `dev`.
- [x] `progress/current.md` describe la sesión activa **arriba del todo**, con
      el bloque de F-031 y lo que queda. *(Observación 3: el fichero conserva
      el histórico de sesiones anteriores debajo. Es deuda previa del
      repositorio, no de esta feature, y no se le imputa.)*
- [x] Ninguna feature pasa a `done` en esta rama: `features.json` sigue
      diciendo `in_progress`, que es lo correcto hasta el cierre del líder.

### C3 — El código respeta arquitectura y convenciones
- [x] **Hexagonal respetada.** `es_el_mismo_codigo` vive en
      `domain/models/nombrado.py` y solo se apoya en `normalizar_codigo`: cero
      imports nuevos, sin reloj, sin red, sin configuración (R13).
      `CodigosNoCoinciden` va en `domain/models/errores.py` y **no sabe de
      HTTP**: quien traduce a 409 es `function_app.py`. `CodigosDelParte` y el
      cotejo viven en la capa de aplicación; el borde compone y pasa. Ningún
      import de infraestructura ha entrado en el dominio.
- [x] Primera línea con la ruta relativa en los **cinco** ficheros nuevos
      (comprobado uno a uno, incluido el `.js`).
- [x] Sin `print()` de debug, sin TODO sin contexto, sin secretos, sin
      dependencias nuevas.
- [x] La unidad sigue siendo **el parte**: el cotejo y el vaciado razonan por
      `hash` de parte, y el vaciado del front recorre **todos** los partes con
      algo escrito, no solo el abierto.
- [x] **Nada se archiva sin pasar las validaciones**: el cotejo va *después* de
      la puerta de aptitud y *antes* de todo lo demás. Ningún `commit` contra
      Sigrid: esta feature no toca el ERP.
- [x] Lo manuscrito no se descarta y el 409 **no lo nombra**: el mensaje lleva
      los dos códigos y nada más (verificado con
      `test_f031_r25_el_409_no_lleva_ningun_dato_del_papel`).
- [x] Reprocesar no duplica: L1 y las tres capas de F-006/F-033 intactas (R14),
      con sus tests en verde.
- [x] Ningún número de estado de Sigrid hardcodeado: no se toca Sigrid.
- [x] Ningún PDF ni dato personal en git (`git log --diff-filter=A`).

### C3 bis — Documentos que entran de fuera
**N/A, justificado:** la feature **no añade ni modifica ningún fichero en
`docs/referencia/`** (verificado sobre el diff completo). No hay documento
externo que fechar, ni original que mantener fuera de git. El barrido de datos
sensibles se ha ejecutado igualmente sobre el diff entero, con los patrones
listados arriba, y salió limpio.

### C4 — La verificación es real
- [x] **Cada requisito EARS de §1.1 y §1.3 tiene test trazable** y todos pasan.
      Tabla completa abajo. *(Excepción declarada: R23 y R24 — observación 4.)*
- [x] Los tests **no tocan red, ni BBDD, ni IA**: dobles en todos los casos
      (`RepositorioFalso`, `ArchivoPortFalso`, `BibliotecaFalsa`, reloj
      inyectado en los `node --test`). La guardia de red de la suite sigue en
      pie.
- [x] Las verificaciones `MANUAL (humano)` están listadas y **pendientes del
      humano**, con su comando. *(Observación 2: el comando exacto vive en
      `progress/impl_F-031.md` §8 ter y en `tasks.md` T14/T15;
      `progress/current.md` las nombra y apunta allí en vez de repetirlas.)*

### C4 bis — El rigor declarado se cumple
- [x] `rigor` declarado y válido: **`critico`**.
- [x] **Fase RED, con salida real.** Es el punto más sólido del informe.
      `impl_F-031.md` §4.3 trae el rojo que importa —no un `ImportError`, sino
      **el comportamiento viejo funcionando**—: `assert 200 == 409` con el log
      del defecto a la vista, `fichero=677 - RS26.08 - 0123 PARTE FIRMADO.pdf
      carpeta=Postventa/677` cuando la base guardaba `0677`. Nueve casos en
      rojo antes del código (R3, R5, R11). §4.1 y §4.2 traen el rojo de R4 y
      del error nuevo; §4 bis.1 y §4 bis.2, el de R18/R19/R20 en el front.
- [x] **Cobertura**: `[OK] 100.0 % de 28 líneas cambiadas (28/28, umbral 80 %)`,
      línea impresa por `init.sh` en la ejecución del reviewer.
- [x] **Mutación**: existe `progress/mutacion_F-031.md`, generado por la
      herramienta, con totales reales **verificados de forma independiente**
      (recálculo puro de alcance y mutantes: coincide exactamente).
- [x] **Los muertos están comprobados, no solo contados**: el informe declara
      78,6 s (< 5 min), así que se **reejecutó la campaña entera** al
      scratchpad. 3/3/0/0, igual que el informe. Árbol limpio después.
- [x] **La campaña tardó lo que tenía que tardar**: 78,6 s × 3 ÷ 3 = 78,6 s por
      mutante, por encima de los 65,6 s que tarda la suite del servicio. Nada
      que oliera a caché envenenada.
- [x] **Cero supervivientes**, y ninguna sección en `PENDIENTE`. El único que
      sobrevivió en la primera vuelta (`@dataclass(frozen=True)` →
      `frozen=False`) **se mató con un test nuevo** en vez de justificarse como
      equivalente — que es exactamente lo que el nivel `critico` quiere ver.
- [x] **«Evidencias»** con los cuatro números **y el nº de workers** (§9 ter):
      tests, cobertura, mutantes/supervivientes, tiempo de la suite, 3 workers.
- [x] Ningún punto marcado N/A sin justificación escrita.

**Nota exigida por el encargo — el JavaScript queda fuera de la puerta de
cobertura y de la de mutación.** Medido, no supuesto: `harness/alcance.py:134`
filtra el alcance con `if not normalizada.endswith(".py")`, de modo que
`js/autoguardado.js` y `js/app.js` **no entran** ni en el 100 % de cobertura ni
en los 3 mutantes. El implementer lo declara así (desviación nº 11) en vez de
omitirlo, que es lo correcto. **Juicio del reviewer: la mitad del front está
respaldada de verdad, no por la métrica sino por sus tests.** Ver el bloque
«Lo que se miró con lupa», punto 4.

### C4 ter — Rutas sensibles
**N/A, y no hay nada que justificar**: este repositorio no declara
`harness/rutas_sensibles.json` (solo existe el `.ejemplo.json`), que es el caso
mayoritario previsto por `CHECKPOINTS.md`.

### C5 — La sesión se cerró bien
- [x] Un commit `F-031 Tn: ...` por tarea, con la atribución correcta y sin
      ningún `git push` ni PR.
- [ ] **`tasks.md` con todas las tareas `[x]`: NO.** Quedan **T14 y T15**,
      abiertas **a propósito**: son `Verificación: MANUAL (humano)` y no las
      ejecuta ningún agente. **Este es el único checkbox vacío del review, y
      es la condición de cierre del veredicto**, no un defecto del trabajo
      entregado. Las 15 tareas que ejecuta un agente están hechas.
- [x] Sin ficheros temporales ni artefactos sin trackear (`git status` limpio,
      antes y después de la campaña de verificación).
- [x] `features.json` refleja el estado real: `in_progress`.

## Lo que el encargo pedía mirar con lupa

### 1 · Las cinco adaptaciones de tests existentes · **ajuste legítimo, no aflojamiento**

Tres ficheros, cinco casos, todos con enmienda fechada en su propio docstring.
Los he leído uno a uno y comparado con su versión en `dev`:

| Caso | Juicio |
|---|---|
| `test_f033_archivar_http.py` · circuito F-032 (**el que señala el encargo**) | **Legítimo.** El caso mandaba `FORMULARIO_F032` (`0626`/`RS26.09/0178`) contra una base que, por el `contexto_apto()` por defecto, guardaba `0677`/`RS26.08/0123`. Esa combinación **no existe en el mundo real**: cuando una petición llega a `/api/archivar`, esos códigos ya están en `postventa.partes` porque es el front quien los leyó de ahí. El arreglo es un parámetro en el *fixture* para que la base diga lo mismo que el formulario. **Las seis aserciones del caso no se han tocado ni una**: sigue exigiendo `200`, cero llamadas al archivador, cero subidas, el **nombre viejo** y la **carpeta vieja** en la respuesta, los dos avisos (`YA_ARCHIVADO` + `ARCHIVADO_EN_OTRO_DESTINO`) y la traza sin pisar. Lo que el caso vigila —que el nombre viejo de F-032 se queda y se avisa— está intacto. **No se ha aflojado nada**; y la divergencia que ese 409 destapaba tiene su propio test, `test_f031_r3_*`, que no existía antes |
| `test_f006_archivar_http.py` · cuerpo con `06\|77` | **Legítimo y reforzado.** El caso ya no puede probar «nombre imposible» porque el nombrado dejó de mirar el cuerpo. Sigue exigiendo 409 y cero subidas, y **ahora afirma además sobre el motivo**, que antes no se miraba: el test es más estricto que el original, no menos |
| `test_f006_archivar_http.py` · **caso nuevo** de nombre imposible desde lo guardado | **Es la contrapartida correcta**, y la spec la pedía (§9). Mete `06\|77` **en la base** y el mismo valor en el cuerpo: el cotejo pasa y lo que falla es el nombrado. Añade dos aserciones que el original no tenía (`"no vale para SharePoint"` y `carpetas == set()`). **El camino de R8 sigue vivo y sigue con test** |
| `test_f006_archivar_http.py` · los dos de `_como_contexto` | **Legítimo.** Pasan a exigir los **nueve** campos vacíos y a cero. Es más exigente que antes, no menos: el `if/else` que permitía confianza 100 en dos campos desaparece |
| `test_f033_l1_desde_el_almacen.py` · `r9_el_nombrado_va_antes_que_l1` | **Legítimo.** R9 no cambia («el nombrado va antes que L1»); cambia de dónde se le quita la entrada, porque el contexto ya no nombra. Sigue exigiendo `NombradoImposible` y `registro == []` |
| `test_f033_l1_desde_el_almacen.py` · `r21_la_firma_no_ofrece_forma_de_forzar` | **Legítimo, y es el que más me importaba.** Podía haberse relajado a un `not in` y **no se hizo**: sigue comparando el **conjunto exacto** de parámetros de `paso_archivo`, de modo que cualquier parámetro nuevo obliga a mirar si abre una puerta. Es lo contrario de aflojar |

### 2 · El 409 ocurre **antes** de subir nada y antes de dejar rastro (D-3, R5)

**Verificado en el código, no en el informe.** El orden de `paso_archivo` es:
`_exigir_admitido` (la puerta, que deja `ctx.situacion`) → `_codigos_guardados`
→ `_exigir_codigos_declarados` → `componer_destino` → L1 → traza previa →
`asegurar_carpeta` → subir. El cotejo está en el punto **1 bis**, antes del
nombrado, antes de la fila en `postventa.archivos` y antes de la primera
palabra con SharePoint. El test que lo fija
(`test_f031_r5_ante_una_divergencia_no_se_escribe_ni_se_llama_a_nadie`) no se
conforma con el 409: exige `llamadas_guardar_archivo == 0`, `archivos == []`,
`registro == []`, `archivador.llamadas == []`, `carpetas == set()`,
`elementos == {}` y `creaciones_de_carpeta == 0`. **Siete aserciones sobre las
dos fronteras.** Es exactamente lo que §7.4 razona que hace falta: con L1 de
F-033 cortando para siempre, un rastro de más no se arregla desde el circuito.

### 3 · El cotejo es **normalizado** (D-7, R4)

**Verificado.** `_exigir_codigos_declarados` compara con `es_el_mismo_codigo`,
que es `normalizar_codigo(uno) == normalizar_codigo(otro)` — la misma función
de F-032, no una copia. `test_f031_r4_el_mismo_codigo_escrito_de_dos_maneras_archiva`
cubre cuatro formas, **incluido el caso literal del encargo**
(`RS 26.09/0178` contra `RS26.09/0178`, el que costó un cierre a mano el
2026-09-17), el espacio dentro del código de obra (`06 26` / `0626`), el guion
largo del escaneo y **el sentido inverso** (la base con el espacio y el cuerpo
limpio). Los cuatro terminan en **200** y con el fichero en
`Postventa/0626`. Y hay control negativo: `0677` y `677` **no** son el mismo
código, con test propio. Además, `test_f031_r4_el_cotejo_se_apoya_en_normalizar_codigo_y_no_en_una_copia`
impide que alguien duplique el criterio el día que cambie.

### 4 · El front (Bloque 3) · **la mitad imprescindible está, y con tests de verdad**

Este es el punto donde la métrica no ayuda —la puerta de cobertura solo mide
Python— así que lo he juzgado leyendo el código y los tests:

- **El vaciado se espera antes de calcular la tanda.** En `app.js`,
  `const vaciado = await this._autoguardado().vaciarPendientes();` va **después**
  de `Confirmacion.resolver` (no alarga la ventana de F-025) y **antes** de
  `const tanda = this.pendientes();`. El orden es el que pide R19.
- **Un vaciado fallido impide lanzarla.** `if (!vaciado.ok) { this.avisoArchivo
  = window.Autoguardado.AVISO_SIN_GUARDAR; return; }` — `return` antes de
  cualquier cosa: no se calcula tanda, no se entra en `conGuardaDeTanda`, no se
  cambia de fase. R20 cumplido.
- **Los tests de JS lo respaldan: sí.** `tests_js/autoguardado_vaciado.test.js`
  son **12 casos sobre el módulo real** (`require("../js/autoguardado.js")`,
  no un doble), con temporizador inyectado y sin DOM ni red. No son tests de
  texto: reproducen el defecto medido —corregir y pulsar **sin correr el
  reloj**, de modo que si el guardado ocurre es porque lo forzó el vaciado—,
  el guardado **en vuelo** (con una promesa diferida, comprobando que el
  vaciado **no se da por bueno** hasta que resuelve y que **no se guarda dos
  veces**), el parte **que no está abierto**, el fallo del guardado, el tope
  de rondas, el aviso, y tres controles negativos de R22 (sin cambios no sale
  ni una petición contra el PostgreSQL compartido). Corren dentro del arnés
  por el puente `tests/test_f007_js.py`, que **falla si falta `node`** en vez
  de saltarse: 310 tests JS en verde en mi ejecución.
- **Y lo que solo se puede fijar sobre el texto fuente** —el orden de las tres
  líneas de `app.js`, que es la única habitación sin tests— lo fija
  `tests/test_f031_front.py`, **seis casos**, buscando sobre el fuente **sin
  comentarios** (nombrar una cosa en un comentario no es hacerla). Ese fichero
  no estaba en `tasks.md`: el implementer lo añadió porque si no **R19 se
  quedaba sin ningún test**. Es una desviación al alza y la apruebo.

**Conclusión del punto 4**: la ausencia de cobertura y de mutación sobre el
JavaScript es una limitación **de la herramienta**, está declarada con su
causa medida, y **no deja el front sin respaldo**. No la trato como N/A
injustificado.

### 5 · No se ha entrado en F-034 · **confirmado**

`git diff --name-only 958c084...HEAD` no contiene `adjuntar.py`, `cerrar.py`,
`paso_grafico.py` ni `paso_cierre.py`. **Cero líneas.** Y no es una foto: hay
guardia automática, `test_f031_r29_la_rama_no_toca_adjuntar_ni_cerrar_ni_sus_pasos`,
con **control de los controles** (`test_f031_el_control_del_diff_no_esta_mirando_una_lista_vacia`)
que exige que el diff no esté vacío y que contenga las dos mitades de la
feature — sin él, un `git diff` que no devolviera nada pondría verdes todos los
demás sin haber comprobado nada. Los 10 controles pasan **sin ningún skip** en
esta rama (verificado con `pytest -rs`). La tentación era grande y está
razonada en el propio test: copiar tres líneas arreglaría `/api/cerrar`, y
cambiar de dónde sale su `numero_incidencia` cambia **qué reclamación se cierra
en producción**. Bien que no se haya hecho.

## Trazabilidad · requisito → test que lo cubre

| Req | Test |
|---|---|
| R1 | `test_f031_r1_el_nombre_y_la_carpeta_salen_de_lo_guardado_y_no_del_cuerpo`, `test_f031_r1_el_paso_ya_no_lee_la_extraccion_del_contexto` |
| R2 | `test_f031_r2_los_codigos_guardados_no_cuestan_ninguna_consulta`, `test_f031_r2_los_codigos_salen_del_mismo_objeto_que_aprobo_la_puerta` |
| R3 | `test_f031_r3_un_cuerpo_que_dice_otra_obra_no_sube_nada`, `test_f031_r3_un_cuerpo_que_miente_responde_409_diciendo_cual` (4 casos), `test_f031_r3_el_409_nombra_tambien_el_valor_guardado` |
| R4 | `test_f031_r4_dos_formas_de_escribir_el_mismo_codigo_son_el_mismo`, `…_dos_codigos_distintos_no_son_el_mismo`, `…_el_cotejo_se_apoya_en_normalizar_codigo_y_no_en_una_copia`, `test_f031_r4_el_mismo_codigo_escrito_de_dos_maneras_archiva` (4 casos) |
| R5 | `test_f031_r5_ante_una_divergencia_no_se_escribe_ni_se_llama_a_nadie` |
| R6 | `test_f031_r6_una_peticion_mal_formada_es_400_y_no_el_409_nuevo` |
| R7 | `test_f031_r7_sin_veredicto_guardado_los_codigos_son_dos_vacios`, `test_f031_r7_lo_guardado_vacio_no_se_sustituye_por_lo_del_cuerpo` (4 variantes) |
| R8 | `test_f031_r8_un_nombre_imposible_desde_lo_guardado_no_se_sanea`, `test_f006_r31_un_nombre_imposible_desde_lo_guardado_responde_409` |
| R9 | `test_f031_r9_un_parte_que_no_consta_validado_responde_409_de_la_puerta` |
| R10 | `test_f031_r10_el_camino_bueno_sigue_devolviendo_las_seis_claves`, `test_f031_r6_…` (los cinco campos siguen obligatorios) |
| R11 | `test_f031_r11_sin_cotejo_lo_declarado_tampoco_mueve_el_pdf`, `test_f031_r11_los_codigos_resueltos_no_se_pueden_reescribir`, `test_f031_r11_nada_del_cuerpo_abre_ni_mueve_la_puerta` (3 casos) |
| R12 | `test_f031_r12_las_reglas_del_nombrado_no_cambian_al_cambiar_la_fuente` |
| R13 | Verificado por lectura: `nombrado.py` no gana ni un import y `es_el_mismo_codigo` solo llama a `normalizar_codigo`. Lo vigila además `test_f031_r29_lo_nuevo_solo_vive_en_los_cinco_ficheros_de_la_feature` |
| R14, R15 | Los tests de F-033 (`test_f033_l1_desde_el_almacen.py`, `test_f033_archivar_http.py`) y de F-019 (`test_f019_orden_archivado.py`), en verde y sin relajar |
| R16 | Los tests de F-026/F-030 sobre la huella, en verde; `test_f026_puertas.py` (la guarda de «aprob») intacta |
| R17 | `test_f031_r17_la_rama_no_toca_la_persistencia_ni_el_puerto`, `…_no_toca_el_ddl`, `…_no_hay_ni_un_fichero_de_ddl_nuevo`, `…_el_puerto_de_persistencia_no_gana_ni_un_metodo`, `test_f031_d1_situacion_parte_no_gana_campos_para_los_codigos` |
| R18 | JS: `f031 R18` × 4 (fuerza y espera; retira el rebote; espera al guardado en vuelo; vacía **cualquier** parte). Python: `test_f031_r18_confirmar_archivo_espera_el_vaciado` |
| R19 | `test_f031_r19_la_tanda_se_calcula_despues_del_vaciado`, `test_f031_r19_el_vaciado_va_despues_de_resolver_la_confirmacion` |
| R20 | JS: `f031 R20` × 3 (devuelve `ok:false`; tope de rondas; el aviso). Python: `test_f031_r20_si_el_vaciado_falla_no_se_lanza_la_tanda`, `…_el_aviso_es_el_del_modulo_y_no_uno_inventado_aqui`, `…_el_aviso_existe_de_verdad_en_el_modulo` |
| R21 | JS: `f031 R21` × 2 (con el vaciado fallido y con el correcto, `ediciones` intacto) |
| R22 | JS: `f031 R22` × 3 (sin nada escrito; escribir y deshacer; dos vaciados seguidos) |
| R23, R24 | **Sin test con nombre `f031`** — ver observación 4. Cubiertos por los de F-019/F-025/F-028 ya existentes (`tests_js/circuito.test.js`, el selector `pendientesDeCircuito`), que siguen en verde |
| R25 | `test_f031_r25_el_409_no_lleva_ningun_dato_del_papel` |
| R26 | `test_f031_r10_el_camino_bueno_sigue_devolviendo_las_seis_claves` |
| R27 | Los de F-033 R20/R24 sobre `drive_id` en logs y avisos, intactos y en verde |
| R28 | Los 94 tests nuevos llevan nombre trazable (`test_f031_rN_…` / `f031 RN: …`); ninguno toca red, BBDD ni IA |
| R29 | `test_f031_r29_la_rama_no_toca_adjuntar_ni_cerrar_ni_sus_pasos`, `…_lo_nuevo_solo_vive_en_los_cinco_ficheros_de_la_feature`, `…_el_paso_de_archivo_ya_no_lee_la_extraccion`, con el control del control |

## Las 11 desviaciones del implementer, juzgadas una a una

| # | Juicio |
|---|---|
| **1** · `test_f033_archivar_http.py` no pasaba sin cambios | **ACEPTADA.** Legítima y bien declarada. Es un error de la spec (§9 lo daba por intacto), no del implementer, y el arreglo pone el *fixture* en el mundo real sin tocar ni una aserción. Detallada arriba |
| **2** · Precedencia R7/R3 con lo guardado vacío | **ACEPTADA, con observación 1.** La spec se contradice consigo misma (R5 fija el cotejo antes del nombrado; R7 pide que hable `NombradoImposible`) y el implementer lo dice en voz alta en vez de esconderlo. Resolvió por el lado seguro y **más accionable**: el 409 que sale dice «guarda la corrección», que es lo que de verdad falta. Lo que R7 exige en sustancia —409, nada archivado, se nombra cuál, el cuerpo no sustituye a lo guardado— se conserva entero, y el camino de `NombradoImposible` sigue vivo con cuatro variantes de test sobre el paso y una por HTTP. **Recomendación al humano**, no al implementer: enmendar la letra de R7 en `requirements.md` para que la spec deje de contradecirse |
| **3** · Reparto del caso central de R1 entre los dos ficheros | **ACEPTADA.** Cosmética y bien razonada: el caso afirma R3+R5, y ponerlo en el fichero de nombrado habría hecho imposible la verificación de T5 |
| **4** · Dos frases reescritas por la guarda de F-026 R24 | **ACEPTADA, y es lo correcto.** La guarda comprueba sobre el texto fuente que no aparece la raíz «aprob» en los handlers, y un comentario la disparó. **Se reescribió el comentario y no se tocó la guarda.** Es la puerta más importante del proyecto; aflojarla porque un comentario se cruza con ella habría sido motivo de rechazo por sí solo |
| **5** · Un fichero de test de más (`tests/test_f031_front.py`) | **ACEPTADA, al alza.** Sin él, R19 —un requisito EARS— se quedaba sin ningún test, contra R28 y contra el nivel `critico`. Mismo planteamiento que `test_f025_front.py` y `test_f026_front.py`. Un implementer que añade un test que nadie le pidió para tapar un hueco de la spec está haciendo bien su trabajo |
| **6** · `node --test tests_js` no arranca con Node 24 | **ACEPTADA.** Cambio de comando, no de alcance: se usa el patrón `tests_js/*.test.js` que el puente de F-007 lleva usando desde entonces. Verificado: 310 tests JS en verde |
| **7** · R23 y R24 no necesitaron ni una línea | **ACEPTADA, con observación 4.** Son requisitos «conservados» y el implementer los declara en vez de dejarlos parecer olvidados. La letra de R28 pediría un test `f031` para cada uno; la sustancia está cubierta por los de F-025 |
| **8** · El fichero de T11 lleva más controles de los que `tasks.md` enumera | **ACEPTADA, al alza.** La mitad «que no depende de `git`» es lo que impide que el fichero **se apague solo** el día que la rama entre en `dev` — que es justo cuando el alcance empieza a necesitar guardia. Verificado: 10 controles, 0 skips en esta rama |
| **9** · T13 se cumplió verificando, no escribiendo | **ACEPTADA, y verificada por el reviewer.** He comprobado en `harness/features.json` que la ficha de F-034 lleva de verdad la ampliación: su `acceptance` tiene el punto de los dos códigos persistidos citando H-1 y las mismas líneas, y su `description` la enmienda «AMPLIADA el 2026-09-22 por decisión del humano». La decisión **está ejecutada**, no solo tomada. La verificación línea a línea de las ocho referencias (§6 ter.2) es correcta |
| **10** · T14 y T15 no ejecutadas | **ACEPTADA como hecho, y es la condición de cierre del veredicto.** Son del humano; ningún agente puede recorrerlas. Están escritas con su comando y con qué anotar en cada paso |
| **11** · La campaña de mutación tiene el mismo alcance que la del Bloque 2 | **ACEPTADA y verificada.** El recálculo independiente confirma 305 líneas y 3 mutantes: el mutador solo muerde `.py` (`harness/alcance.py:134`) y lo que añadieron los bloques 3 y 4 es JavaScript y tests. Declararlo con la causa medida, en vez de omitir el dato, es lo que hay que hacer |

## Hallazgos y observaciones (ninguno bloquea)

> Ninguno es un cambio requerido. Se numeran con su gravedad para que el humano
> decida; **no hay lista de «cambios requeridos» porque no hay ninguno**.

**1 · BAJA · La letra de R7 ya no describe lo que pasa desde el endpoint.**
`requirements.md` R7 dice que con el código guardado vacío sale «el error de
nombrado imposible». Desde el endpoint sale `CodigosNoCoinciden`, porque R5
manda el cotejo antes del nombrado y R10 mantiene el cuerpo obligatorio y no
vacío. Los dos son 409, los dos dejan el parte sin archivar y los dos dicen
cuál de los dos códigos falla. **Es una contradicción de la spec, no del
código**, y el implementer eligió la lectura correcta. *Propuesta al humano:
una nota fechada bajo R7 diciendo cuál gana. No requiere tocar código.*

**2 · BAJA · Las verificaciones `MANUAL (humano)` no traen el comando dentro de
`progress/current.md`.** C4 pide que estén «listadas en `progress/current.md`
con su comando exacto». `current.md` las nombra, dice que son del humano y
apunta a `progress/impl_F-031.md` §8 ter, que es donde está el guion completo
(y `tasks.md` T14/T15 también lo trae). El dato está en `progress/` y es
localizable en un salto; lo doy por cumplido en sustancia. *Propuesta: pegar
las cuatro líneas de comando en `current.md` al cerrar la feature.*

**3 · BAJA · `progress/current.md` arrastra el histórico de sesiones
anteriores** (3.900+ líneas), mientras que C2 pide que describa **solo** la
sesión activa. **Es deuda previa del repositorio, no de F-031**: la feature
añade su bloque arriba del todo, que es el patrón vigente. Se anota para que
no se pierda, no para imputársela a este trabajo.

**4 · BAJA · R23 y R24 no tienen test con nombre `f031`.** R28 pide «para cada
requisito de §1.1 y §1.3, al menos un test con nombre trazable». Los dos son
requisitos de **conservación** que no costaron ni una línea, y su sustancia la
vigilan tests que ya existen (`tests_js/circuito.test.js` para el pintado del
error sin tumbar la tanda; el selector `pendientesDeCircuito` para R23). El
implementer lo declara. *Propuesta: dos casos de una línea en
`tests_js/circuito.test.js` citando F-031 R24, o una nota en R28 aceptando que
un requisito conservado se traza con el test que ya lo cubre.*

**5 · INFORMATIVO · El cotejo corre antes de L1, así que un parte que ya consta
archivado y venga con un cuerpo divergente recibe 409 en vez del 200
idempotente de F-033.** Es lo que el diseño ordena (1 bis antes del 3) y es el
lado seguro —quien llama con códigos que no cuadran tiene que enterarse—, pero
no está escrito como requisito en ninguna parte. Merece una línea en la
documentación de F-033 o de F-031 el día que alguien se pregunte por qué.

**6 · INFORMATIVO · `vaciarPendientes` cancela el rebote en espera y, si el
guardado falla, no lo reprograma.** Lo escrito **no se pierde** (sigue en
`parte.ediciones` y en `pendientes`, con test de R21) y la pantalla lo dice con
`MENSAJE_FALLO`, que además explica cómo reintentar («vuelve a escribir algo o
pulsa Revalidar»). No incumple ningún requisito —cancelar es deliberado, para
que el temporizador no salte después de la tanda— pero conviene saberlo: tras
un vaciado fallido, el autoguardado no volverá solo hasta la siguiente
pulsación.

## Automejora del arnés (propuesta, no aplicada)

**`.claude/agents/reviewer.md` · la prueba de control del «cero mutantes» tiene
un hermano que falta: el «poquísimos mutantes».** El protocolo me hace probar
el caso de 0 mutantes, pero no el de **3 mutantes sobre 305 líneas**, que es lo
que ha salido aquí. El recálculo puro coincidía, así que el número es cierto;
pero un alcance enorme con un puñado de mutantes es igual de informativo y el
protocolo no me pide mirarlo. En este caso la explicación es correcta y la
verifiqué (casi todo lo cambiado son docstrings y enmiendas fechadas, y el
mutador solo muerde operadores y constantes), pero lo hice por instinto, no
porque el protocolo lo pidiera. *Propuesta: añadir al punto 4 de «Validación
contra el nivel de rigor» que, cuando la razón mutantes/líneas baje de ~1 por
cada 50 líneas, el reviewer deje escrito **por qué** — normalmente
documentación — en vez de darlo por bueno.* Vale para cualquier proyecto, así
que si el humano la aprueba, va también a `arnes-base`.

---

## Resumen

Trabajo sólido y honesto. La fase RED es de las buenas —el rojo con el log del
defecto archivando en `Postventa/677` vale más que cualquier párrafo—, la
campaña de mutación aguanta la verificación independiente **y la reejecución**,
las cinco adaptaciones de tests existentes son ajustes al mundo real que en dos
casos dejan el test **más** estricto que antes, y las dos mitades de la feature
—backend y front— están, que es lo que la spec declaraba imprescindible. El
alcance se respetó donde más tentaba: `/api/cerrar` sigue sin tocar, con
guardia automática que lo vigila.

**APROBADO.** Con una sola casilla pendiente, que no es del implementer: **V1 y
V2, del humano, antes de `done` y antes de mergear**.
