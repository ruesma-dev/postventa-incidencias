<!-- progress/review_F-034.md -->
# F-034 · Review · Adjuntar y cerrar leen de lo persistido el estado de archivo y los dos códigos

> Revisado el **2026-09-23** sobre `feature/F-034-archivo-persistido-en-erp`
> (`33010e3` .. `8cdf958`, base de integración `dev`; base del diff de la
> herramienta de alcance: `e2e5d7a`), contra `specs/F-034-archivo-persistido-en-erp/`
> (aprobada por el humano el 2026-09-22 con D-1 (a) y D-2 a D-8 según la
> recomendación), `docs/CONVENTIONS.md`, `docs/ARCHITECTURE.md` y `CHECKPOINTS.md`.
>
> **En esta revisión no se ha implementado ni corregido nada.** No se ha
> escrito en Sigrid, SharePoint, Azure ni PostgreSQL. Las sondas de mutación
> se ejecutaron en un `git worktree` desechable dentro del scratchpad de la
> sesión, ya retirado; `git status` queda limpio. El único fichero que se
> escribe en el árbol es este.

## Veredicto

**RECHAZADO** (CHANGES_REQUESTED), por **un solo hallazgo bloqueante de
gravedad MEDIA** (H-R1) más uno BAJO que conviene resolver en la misma vuelta
(H-R2). **El código de producción está bien**: lo he leído línea a línea y
hace lo que la spec pide. Lo que falla es que **los tests de `/api/cerrar` no
pueden ver el login**, así que la mitad de R13 («antes de resolver el login
contra el ERP») y el punto 2 del encargo («las puertas cortan antes de hablar
con Sigrid») **no están demostrados** en el endpoint que decide qué reclamación
se cierra. Dos regresiones que mueven una puerta por debajo del login pasan la
suite **entera** en verde (3.229 passed). En una feature `critico` que el
encargo pide revisar «con ese peso», eso no se deja para después.

La corrección es de tests y es pequeña (una tarea): ver «Cambios requeridos».

Además, **condición de cierre** que no es trabajo del implementer: T16 (V1) y
T17 (V2) son `MANUAL (humano)` y están sin ejecutar. Aunque el hallazgo se
corrija, la feature no puede pasar a `done` ni mergearse a `dev` hasta que su
resultado real conste en `progress/impl_F-034.md` (mismo patrón que F-031,
F-032 y F-033).

## Nivel de rigor y puertas que exige

| | |
|---|---|
| **Declarado** en `harness/features.json` | **`critico`** (explícito) |
| **Exige** | C1–C5 + C3 bis + C4 bis · tests trazables · **fase RED** en los requisitos centrales · **cobertura** de líneas cambiadas ≥ 80 % · **mutación** con **cero supervivientes** salvo justificación aceptada por el humano · verificaciones `MANUAL (humano)` con comando exacto **y resultado real** |

### Lo que ha comprobado el reviewer por su cuenta

| Puerta | Cómo | Resultado |
|---|---|---|
| Arnés | `bash harness/init.sh`, tal cual | **VERDE**. Raíz 62 passed; api y front en verde (de caché); `PUERTA COBERTURA [OK] 100.0 % de 88 líneas cambiadas (88/88, umbral 80 %, nivel critico)`; rama correcta |
| Suites **sin caché** | `pytest tests -q -p no:cacheprovider` en los dos servicios; `node --test "tests_js/*.test.js"` | api **3.236 passed, 18 skipped** (98 s); front **256 passed**; JS **322 pass, 0 fail** (Node v24.14.1) |
| Mutación · recálculo puro | `harness.alcance.alcance_de_feature("F-034")` + `harness.mutacion.generar_mutantes` | **Idéntico al informe**: 10 ficheros, **738 líneas**, **12 mutantes**, mismos operador, línea y texto original→mutado en los doce (`codigos_del_parte.py` 71/140/185/187/205/206/207/211, `paso_cierre.py` 328/333, `puerta_de_estado.py` 210 ×2) |
| Mutación · ¿están muertos de verdad? | **Campaña no reejecutada: 359,8 s (≈ 6 min) según el informe**, por encima del umbral de 5 min, así que por protocolo basta el recálculo. **Además**, por el peso de la feature: cada uno de los 12 mutantes aplicado en un worktree aislado de `HEAD` contra **solo** los 4 ficheros de tests de F-034 (control sin mutar: 163 passed, 7 skipped —los controles de `diff` se saltan en `HEAD` separado, como deben—) | **12/12 muertos**, y el test que cae primero coincide con la tabla «quién mata» del informe en los doce |
| Coste por mutante | 359,8 s × 8 workers ÷ 12 = **239,9 s/mutante** | Por encima del tiempo de la suite (127 s). **No es sospechosa** |
| Mutantes **a mano** (lo que los operadores de la herramienta no alcanzan) | 11 mutaciones semánticas sobre el orden y el origen de los datos, mismo worktree | 7 muertos; 2 **equivalentes por construcción** (O-1); **2 supervivientes con la suite entera** → H-R1 |
| Alcance | `git diff --stat dev...HEAD` y `test_f034_alcance_cerrado.py` (25, ninguno saltado en la rama) | Producción tocada = la lista de `design.md` §2. `infra/desplegar_backend.ps1`: **solo comentarios** (nota del líder, T14) |
| Secretos, datos personales, PDFs | Barrido del diff (`print(`, `console.log`, `TODO`, `AccountKey`, `password`, `api_key=`, `Bearer`, `subscription`, `tenant`, IPv4) y `git log --diff-filter=A dev..HEAD` | **Limpio.** Ningún PDF ni fichero de `muestras/` |
| Lint | `ruff check` sobre los `.py` tocados | 2 avisos `PYI034` en `tests/utiles_pg.py:82,157`, **anteriores** (`7c57e523`, 2026-08-20). Nada nuevo |

## Hallazgos (numerados, con gravedad)

### H-R1 · MEDIA · **bloqueante** · En `/api/cerrar` ningún test ve el login: dos puertas pueden bajar por debajo de él sin que nada se ponga rojo

**Qué pasa.** Los mundos de test (`tests/utiles_circuito.py:93-105`) usan un
doble `Usuarios` con la correspondencia **ya confirmada**, que **no apunta sus
llamadas**. Con eso `resolver_login_de_sigrid` (`paso_cierre.py:704-707`)
devuelve el login sin tocar el ERP, y `MundoDelCierre.nada_ha_tocado_el_erp()`
(`utiles_circuito.py:392-401`) no tiene forma de saber si el login se resolvió
antes o después de las puertas.

**Medido** (worktree aislado, suite `api` **entera**):

| Mutación a mano en `paso_cierre.py` | Resultado |
|---|---|
| El cotejo de 1 bis (`_codigos_con_los_que_se_cierra` + puerta de archivo) movido **después** de `resolver_login_de_sigrid` | **VIVO** · `3229 passed, 25 skipped` |
| La puerta de archivo (`exigir_parte_archivado`) movida **después** de `resolver_login_de_sigrid` | **VIVO** · `3229 passed, 25 skipped` |
| La misma del cotejo en `paso_grafico.py` | Muerto (14 fallos), pero **por la consulta de la traza local** del gráfico (`graficos_consultados`), que va antes del login; tampoco allí se observa el login |

Y `test_f034_r15_paso_cierre_sin_incidencia_guardada_no_llega_al_login`
(`test_f034_codigos_en_el_erp.py:1029`) **promete en el nombre lo que no puede
ver**: pasa igual con el login delante.

**Por qué importa aquí.** R13 dice literalmente «antes de resolver el login
contra el ERP»; el encargo pide que las puertas corten «antes de hablar con
Sigrid». Con cualquiera de esas dos regresiones, para un usuario **sin
correspondencia confirmada** el 409 llegaría **después** de una lectura a
Sigrid por `sigrid-api` (`_exigir_que_el_erp_lo_confirme`) y de una
**escritura** en la tabla de correspondencias del PostgreSQL compartido
(`usuarios.guardar_login`, `paso_cierre.py:712`). No cierra otra reclamación
—la lectura de la reclamación sigue detrás—, por eso es MEDIA y no ALTA; pero
es exactamente la propiedad que la feature afirma y sus tests no la fijan. El
código de hoy **sí** la cumple (verificado leyendo `paso_cierre.py:214-222`).

### H-R2 · BAJA · R37: R14 no tiene ningún test con nombre `test_f034_r14_…`

R37 exige, para **cada** requisito de §1.1, §1.2 y §1.5, un test con nombre
trazable. R14 (el cotejo también en dry-run) **está cubierto** —los casos
`[dry_run]` de `test_f034_r11_adjuntar_otra_incidencia_en_el_cuerpo_no_toca_el_erp`,
`test_f034_r9_cerrar_otra_incidencia_en_el_cuerpo_no_toca_el_erp` y
`test_f034_r3_*_no_toca_el_erp`, cuyo docstring cita R14—, pero ninguno lo
lleva en el nombre (`grep "def test_f034_r14_"` → 0). Es lo único de R37 que no
cuadra; R21, R22, R25, R36 son de §1.3/§1.6 y R37 no les exige nombre.

## Cambios requeridos

1. **(H-R1)** `services/postventa-api/tests/utiles_circuito.py:93-105` · que
   `Usuarios` apunte cada llamada (`resolver_login`, `guardar_login`) en una
   lista, y que `nada_ha_tocado_el_erp()` de **los dos** mundos
   (`:256-266` y `:392-401`) exija además esa lista vacía. Si se prefiere no
   tocar el doble compartido, alternativa equivalente: una variante del mundo
   con la correspondencia **sin confirmar**, de modo que un login resuelto
   deje rastro en `erp.verificaciones`, usada al menos en los casos centrales
   de R9/R11/R13/R15 y de R3 por `/api/cerrar`.
   **Verificación exigible**: fase RED de las dos mutaciones de la tabla de
   H-R1 (aplicadas a mano en una copia, nunca en el árbol real) con su traza
   pegada en `progress/impl_F-034.md`, y verde con el código real. Revisar de
   paso que `test_f034_r15_paso_cierre_sin_incidencia_guardada_no_llega_al_login`
   y `test_f034_r15_grafico_sin_incidencia_guardada_no_llega_al_login` pasen a
   demostrar lo que dicen sus nombres.
2. **(H-R2)** Renombrar (o parametrizar con un alias) los casos `[dry_run]`
   centrales para que R14 tenga al menos un `test_f034_r14_…` en cada endpoint.
   Sin cambiar ni una aserción.
3. Tras 1 y 2: `bash harness/init.sh` en verde y la **campaña de mutación
   relanzada** (el cambio es solo de tests, pero la puerta de cobertura y el
   informe deben corresponder al `HEAD` que se revise).

## Lo que el encargo pedía juzgar expresamente

### 1a · La decisión del humano del 2026-09-23 (enmienda de dos tests de F-031) · **ACEPTADA, y se cumplió al pie de la letra**

`git diff dev...HEAD` sobre los tests de F-031, F-006 y F-033: **solo** cambian
`test_f031_alcance_cerrado.py` (la tabla `NOMBRES_NUEVOS_Y_DONDE_VIVEN` y su
comentario de enmienda fechada, +40/−5) y `test_f031_nombrado_persistido.py`
(un `import`, con alias `codigos_guardados as _codigos_guardados` para que el
cuerpo del test no cambie, +8/−1). **Ninguna función de test** de F-031 cambia,
ni una aserción; `test_f006_*` y `test_f033_*` sin tocar. Las dos claves
privadas de la tabla pasan a sus nombres públicos: sigue siendo «solo la
tabla». Ninguna regla de F-031 cambia: el mensaje de archivar lo fija byte a
byte `test_f034_r26_codigos_el_mensaje_de_archivar_es_byte_a_byte_el_de_f031`,
y `test_f034_r26_de_paso_archivo_solo_cambia_la_mudanza` /
`…de_archivar_solo_cambia_el_import` comparan el árbol sintáctico con la base.
El control «dónde vive lo nuevo» lo hereda y amplía
`test_f034_lo_nuevo_solo_vive_en_los_ficheros_previstos`.

### 1b · H-4 (decisión del líder dentro de D-4) · **ACEPTADA; hay tests que lo demuestran**

Un nº guardado sin tramos da 409 `CodigoNoConsta` por la **ruta HTTP de
verdad** en gráfico (`test_f034_h4_adjuntar_incidencia_guardada_sin_tramos_es_409_codigo_no_consta`)
y en cierre (`test_f034_h4_cerrar_…`), con el cuerpo diciendo lo mismo o un
número bueno, y `nada_ha_tocado_el_erp()`. La pieza, con y sin
`solo_incidencia` y cuatro formas de separador. `/api/archivar` idéntico:
`test_f034_h4_r26_archivar_no_cambia_con_una_incidencia_sin_tramos` exige el
`NombradoImposible` **con el mensaje literal medido antes de H-4** y cero
llamadas, y `…_archivar_no_llama_a_la_exigencia_de_completos` cierra el camino.
La obra de solo separadores sigue en `NombradoImposible` (R24, test propio).
Es coherente con D-4 —lo incompleto es lo guardado y el 400 mentía— y, en
`/cerrar`, tapa un caso en que antes se **cerraba la reclamación del cuerpo**.
Sin interruptor, con razón escrita. Bien decidida.

### 2 · Las puertas cortan antes de Sigrid y de dejar traza, también en dry-run · **el código sí; los tests, a medias → H-R1**

Todos los tests centrales van con los cinco puertos **inyectados**, así que
`construir_erp`/`construir_graficos` —y su `exigir_interruptor_de_cierre`—
**no se evalúan**: ningún 409 puede salir tapado por el 503 de la ventana. Y
no lo hacen: los del handler exigen **la clase** de error
(`CodigosNoCoinciden`, `CodigoNoConsta`, `ParteNoArchivado`), y los de la ruta
exigen `status_code == 409`, `{"error"}` como única clave y el **tipo** del
error en el log (`test_f034_r27_*`). Los casos centrales están parametrizados
`[dry_run]`/`[commit]` (R14). `nada_ha_tocado_el_erp()` cubre lecturas y
cierres del ERP, llamadas a la pasarela, trazas de gráfico y de cierre,
histórico y hasta la consulta de la traza local. Lo que **no** cubre es el
login → H-R1. `construir_erp` no abre red al construirse (`fabrica.py:78-100`).

### 3 · La reclamación que se cierra sale del número guardado · **SÍ, línea a línea**

- `paso_cierre.py:214` aptitud → `:215` `guardados = codigos_guardados(ctx)`
  (lee `ctx.situacion.validacion`, `codigos_del_parte.py:113-119`), completos
  (`solo_incidencia=True`) **antes** del cotejo → `:216` puerta de archivo
  desde `ctx.situacion.archivo` → `:218` `_codigo_de_incidencia(guardados.numero_incidencia)`
  → `:223` `_dry_run(erp, codigo=codigo)` → `erp.leer_reclamacion(codigo=…)`
  (`:398`) → el `plan` es el único que llega a `_escribir` → `erp.cerrar(plan=plan)`
  (`:463`). **Ninguna** otra vía: el parámetro `numero_incidencia` desapareció
  de la firma (D-7, con test `test_f034_r19_paso_cierre_ya_no_acepta_el_numero_suelto`).
- `paso_grafico.py:208` aptitud → `:209` códigos guardados completos y
  cotejados → `:210` archivo → `:218` `_codigo_de_incidencia(guardados…)` →
  `:223` `leer_reclamacion` → `:233-237` `componer_peticion` con
  `guardados.codigo_obra` y `guardados.numero_incidencia`.
- Los bordes (`cerrar.py:180-182`, `adjuntar.py:195-197`) pasan lo del cuerpo
  **solo** como `codigos_declarados`; `_como_contexto` ya no fabrica
  `TrazaArchivo` en ninguno de los dos (R4, con espía en los dos endpoints).
- Mutantes a mano muertos: quitar el cotejo (en cierre y en gráfico), que
  `cerrar.py` no declare, invertir los códigos en `adjuntar.py`, que la puerta
  lea `ctx.archivo` o que `ctx.archivo` la abra, el archivo antes que el
  cotejo, y quitar la exigencia de completos en el cierre.

### 4 · H-5 (`RS26.08 - 0123` ≠ `RS26.08/0123` en el cotejo) · **lado seguro, y no produce 409 falsos con los datos reales del circuito**

El razonamiento, con el código delante:

- **Lo guardado** pasa siempre por `sanear_valor_leido` → `normalizar_codigo`:
  al extraer (`paso_extraccion.py:128`) y al guardar una corrección con
  `POST /api/parte` (`cuerpos.py:170`). `normalizar_codigo` solo traduce
  guiones raros y quita blancos (`nombrado.py:160-162`); **no** toca `/` ni `-`.
- **El cuerpo** sale de `valorDeCampo` (`pipeline.js:386-393`): la edición de
  la persona si la hay, si no el valor de la extracción, que **ya viene
  saneado** del backend. Solo recorta extremos.
- El cotejo compara `normalizar(cuerpo)` con `normalizar(guardado)`, y
  `normalizar_codigo` es **idempotente**. Así que cuerpo y guardado difieren
  en el estilo de separador **solo si el valor del front no es el guardado**:
  una corrección sin guardar. Ahí el 409 es **correcto**, y desde T11 el
  reintento vacía antes (R29).
- Las filas anteriores a F-032 solo pueden diferir en **blancos**, que el
  cotejo iguala; F-032 no cambió separadores.
- Y en el circuito real **archivar va antes** con el **mismo** cotejo (F-031,
  desplegado y en uso): una divergencia de separador ya se pararía allí, así
  que F-034 no añade ninguna clase nueva de 409 en la práctica.

Recomendación: **no tocarlo** (sería cambiar R12 de F-031 y el comportamiento
de archivar). Relajarlo a igualdad por tramos también sería seguro —los dos
estilos apuntan a la misma reclamación de Sigrid—, pero no hace falta.
Si V2 lo viera, que se anote tal como dice el guion.

### 5 · Los guiones de T16 y T17 · **recorribles**; la propuesta de V1 (a) · **de acuerdo**

He contrastado cada supuesto del guion con el código:

- **No usa `func start`**: se hace en el entorno desplegado. Evita el primer
  fallo de V1 de F-031 (el 503 antes de las puertas).
- **`api` no es global**, en efecto: es una `const` dentro de la clausura de
  `appPostventa()` (`app.js:23`). El guion usa lo que sí es global:
  `window.CONFIG_POSTVENTA.baseApi` (`config.js:5-6`, `"/api"`),
  `Alpine.$data(document.querySelector('[x-data]'))` (el único `x-data` raíz,
  `index.html:16`) y `app.usuario`, que tiene la forma `{usuarioOid, correo}`
  (`api.js:106-125`). Evita el segundo fallo.
- `fetch` al mismo origen lleva la cookie de sesión de la Static Web App; el
  front de verdad no añade ninguna cabecera de autenticación
  (`api.js:202-207`), así que la consola llega igual que la pantalla.
- Los cuerpos llevan las claves de `CAMPOS_OBLIGATORIOS`, `destino` es un valor
  de `Destino`, el campo del fichero se llama `fichero`, y las claves que se
  mandan mirar existen: `estado`, `numero_incidencia`, `filas_afectadas`,
  `dry_run.incidencia` (`cerrar.py:287-291, 313`; `adjuntar.py:301-304, 375`)
  y `dry_run.nombre_fichero` / `ya_estaba` (`adjuntar.py:363-382`).
- Declara lo que escribe: nada en Sigrid ni en SharePoint, **sí** la traza
  `dry_run_ok` en la base propia, y V2-4 una sola lectura de situación
  (medido por T12).

**V1 · (a) declarar R32 cubierta por tests + (b) V2-4 como complemento: de
acuerdo.** Los dos 409 nuevos viajan por el camino genérico de cualquier 409
(`clasificar` → `ErrorApi("no_apto")`, `api.js:77-79`, con sus tests;
`anotarFallo`), y `reintento_vaciado.test.js` ejecuta `app.js` de verdad en
`node:vm` con un error de la misma forma que produce `clasificar`: el 409 se
pinta en el parte y no tumba ni el reintento ni una tanda de dos. Provocarlo
desde la pantalla con las ventanas abiertas sería escribir en Sigrid si
fallara el intento. Lo que falta es que el humano **escriba su decisión** en
`progress/impl_F-034.md` §10.2.

### 6 · Mutación y JavaScript · **correctas**

Mutación: ver la tabla de comprobaciones. La vuelta 1 dejó un superviviente
(`strict=True` del `zip`), equivalente con el código de hoy, y el implementer
eligió **matarlo con un test de «fallar cerrado»** con su RED contra el
mutante en vez de pedir al humano que aceptara la equivalencia: bien. 738
líneas y 12 mutantes se explica por los operadores de la herramienta (el grueso
son docstrings, mensajes, firmas y llamadas); por eso hice además los mutantes
a mano de H-R1 y O-1.

JavaScript: la herramienta solo muta Python, así que la mutación y la
cobertura del cambio de `app.js` son **N/A justificado por el lenguaje**. Lo
respaldan los 12 tests de `reintento_vaciado.test.js` (RED real de 5 fallos en
§8.2), que cubren las dos ramas de `if (!vaciado.ok)`, la **espera** (el cierre
no sale con el guardado en vuelo), el aviso, que el aviso anterior se retire,
R31 (mismas claves del cuerpo), R32 y R33. Ningún otro fichero de `tests_js/`
tocado. 322/322 en verde con mi ejecución.

## Las desviaciones del resumen del implementer (§11.2), una a una

| # | Juicio |
|---|---|
| 1 · R26 y T3 enmendadas | **Aceptada** (decisión del humano; ver 1a) |
| 2 · Mensajes con parte fija + `y_por_eso`; `CodigoNoConsta` lleva la acción en la parte fija | **Aceptada.** La asimetría es deliberada y tiene sentido: la acción de `CodigoNoConsta` es la misma en cualquier endpoint |
| 3 · `tests/utiles_circuito.py` fuera de la lista de `design.md` §2.1 | **Aceptada**: utillería de tests. Es donde hay que arreglar H-R1 |
| 4 · Commits intermedios de T6 y T9 con el borde en rojo | **Aceptada** por el orden de `tasks.md` (firma del paso en una tarea, borde en la siguiente). Anotado para quien haga `git bisect` |
| 5 · H-4 | **Aceptada** (ver 1b) |
| 6 · `test_f009_r47` pasa de 400 a 409 `CodigoNoConsta`; `_ha_pasado` de F-028 | **Aceptada.** Es R15/D-4 y el test conserva lo que vigila (`assert erp.lecturas == []`, `test_f009_paso_cierre.py:388`). En F-028 la lectura exigida pasa a ser la del código **guardado**: más estricta, no menos. He barrido el diff de los tests adaptados de F-009, F-012, F-025, F-026, F-028 y F-030: **ninguna aserción retirada** fuera de las dos fundidas de `_ha_pasado` |
| 7 · Una línea más en `reintentarCierre` (retirar el aviso); tests por ejecución; `node --test` con patrón | **Aceptada**, con test cada cosa |
| 8 · T12 cuenta todas las llamadas; T13 lista cerrada | **Aceptada, al alza** |
| 9 · Recuadros fechados el 23; notas «desde el despliegue de F-034» | **Aceptada.** En `infra/desplegar_backend.ps1` solo cambian comentarios |
| 10 · `--timeout 600`; test para el superviviente; T13 marcada | **Aceptada** |
| 11 · T16 y T17 sin ejecutar | **Condición de cierre**, trabajo del humano (ver 5) |

## Checkpoints

### C1 — El arnés está completo y en verde
- [x] `bash harness/init.sh` en verde, ejecutado por el reviewer.
- [x] Existen los ficheros obligatorios.

### C2 — El estado es coherente
- [x] Una sola feature `in_progress`: F-034.
- [x] Rama `feature/F-034-archivo-persistido-en-erp`.
- [x] `progress/current.md` describe la sesión activa arriba del todo. *(Conserva debajo el histórico de sesiones anteriores: deuda previa del repositorio, no imputable a F-034, igual que en la review de F-031.)*
- [x] Ninguna feature pasa a `done` en esta rama.

### C3 — Arquitectura y convenciones
- [x] Hexagonal: `CodigoNoConsta` en `domain/models/errores.py` sin saber de HTTP; `codigos_del_parte.py` y `exigir_parte_archivado` en la capa de aplicación, dependiendo solo del dominio; el borde compone y traduce a 409.
- [x] Primera línea con la ruta en los 9 ficheros nuevos (comprobado uno a uno, `.js` incluido).
- [x] Sin `print()`, sin TODO sin contexto, sin secretos, sin dependencias nuevas.
- [x] La unidad es el parte (todo por `hash`; el vaciado del front recorre todos los partes).
- [x] Nada se adjunta ni se cierra sin las validaciones, y ahora **con lo guardado**; ningún `commit` sin confirmación; dry-run primero (la tanda de F-025 no cambia).
- [x] Lo manuscrito no se descarta y los 409 no lo nombran (`test_f034_r34_*` en los dos endpoints).
- [x] Reprocesar no duplica: las tres capas de F-012 intactas (`test_f034_r38_adjuntar_ya_adjuntado_…`).
- [x] Ningún número de estado de Sigrid hardcodeado.
- [x] Ningún PDF ni dato personal en git (`git log --diff-filter=A`).

### C3 bis — Documentos que entran de fuera
**N/A, justificado**: la feature no añade ni modifica nada en `docs/referencia/`. El barrido de datos sensibles se ejecutó igualmente sobre el diff entero (patrones arriba) y salió limpio.

### C4 — La verificación es real
- [ ] **Cada requisito tiene ≥ 1 test trazable y todos pasan: NO del todo.** Todos pasan, y la tabla de abajo cubre R1–R39; pero la cláusula de R13 «antes de resolver el login» **no está demostrada en `/api/cerrar`** (H-R1), y R14 no tiene test con su nombre (H-R2).
- [x] Los tests no tocan red, ni BBDD, ni IA, ni el ERP: puertos dobles en todos los casos.
- [x] Las `MANUAL (humano)` están listadas y pendientes: `progress/current.md` las anuncia y apunta al guion completo con sus comandos en `progress/impl_F-034.md` §10.2 y §10.3.

### C4 bis — El rigor declarado se cumple
- [x] `rigor: "critico"` declarado.
- [x] Fase RED con traza real en los centrales: T2, T3, T4 (39 fallos), T8 (37, incluido el cierre de la reclamación del cuerpo visto de frente), T11 (5), T12 medido en `dev`, T13 con sondas y el test de T15 contra su mutante.
- [x] Cobertura: `[OK] 100.0 % de 88 líneas cambiadas`. JS: N/A justificado por el lenguaje (el arnés no mide JS), con las dos ramas del `if` con test.
- [x] Mutación: informe generado por la herramienta, totales **recalculados e idénticos**.
- [x] Muertos comprobados: campaña de 359,8 s (> 5 min), **no reejecutada entera**, y así lo digo; en su lugar, los 12 mutantes aplicados uno a uno contra los tests de F-034 en un worktree aislado: **12/12 muertos**.
- [x] Coste por mutante 239,9 s > suite 127 s: no sospechosa.
- [x] Cero supervivientes; el de la vuelta 1, matado con test.
- [x] «Evidencias» con los cuatro números y los workers (8).
- [x] Ningún N/A sin justificar.

### C4 ter — Rutas sensibles
**N/A, y no hay nada que justificar**: el repositorio no declara `harness/rutas_sensibles.json`.

### C5 — La sesión se cerró bien
- [ ] **`tasks.md` con todas las tareas `[x]`: NO.** Quedan **T16 y T17**, `MANUAL (humano)`: condición de cierre, no defecto del implementer. Las 16 tareas de agente, hechas, con su commit `F-034 Tn: …`.
- [x] Sin temporales ni artefactos sin trackear (`git status` limpio antes y después de las sondas; el worktree de la sonda, retirado).
- [x] `features.json` dice `in_progress`, que es el estado real.

## Cobertura · requisito → test

| Req. | Test(s) representativo(s) |
|---|---|
| R1 | `test_f034_r1_puerta_pasa_con_la_traza_guardada_en_archivado`, `…_el_grafico_usa_la_compartida_y_no_su_copia`, `…_el_cierre_usa_la_compartida…` |
| R2 | `test_f034_r2_adjuntar_…_no_cuesta_ninguna_consulta_mas`, `test_f034_r2_cerrar_…`; `test_f034_r38_*` |
| R3 | `test_f034_r3_adjuntar_cuerpo_archivado_sin_archivo_guardado_no_toca_el_erp[×dry_run/commit]`, `test_f034_r3_cerrar_…`, `…_por_la_ruta_es_409_…` |
| R4 | `test_f034_r4_adjuntar_el_borde_ya_no_fabrica_la_traza_de_archivo`, `test_f034_r4_cerrar_…`, `test_f034_r4_el_borde_no_fabrica…` |
| R5 | `test_f034_r5_puerta_lo_que_diga_el_cuerpo_no_la_abre` |
| R6 | `test_f034_r6_{adjuntar,cerrar}_estado_archivo_sigue_siendo_obligatorio_y_validado`, `…_el_modulo_dice_que_estado_archivo_ya_no_decide` |
| R7 | `test_f034_r7_{adjuntar,cerrar}_cuerpo_corto_con_archivo_guardado_pasa`, `test_f034_r7_puerta_…` |
| R8 | `test_f034_r8_adjuntar_el_handler_pasa_lo_declarado_solo_para_cotejar`; control positivo `lecturas == [guardada]` |
| R9 | `test_f034_r9_cerrar_otra_incidencia_en_el_cuerpo_no_toca_el_erp[×2]`, `…_control_positivo_mismo_numero_si_cierra` |
| R10 | `test_f034_r10_codigos_guardados_salen_de_la_situacion_ya_leida`; `test_f034_r38_*` |
| R11 | `test_f034_r11_adjuntar_otra_incidencia…`, `…_codigos_divergentes_dicen_cual…`, `…_si_las_dos_listas_no_casan…` |
| R12 | `test_f034_r12_codigos_el_cotejo_normaliza_los_dos_lados`, `…_{adjuntar,cerrar}_el_cotejo_normaliza…` |
| R13 | `test_f034_r13_{adjuntar,cerrar}_el_cotejo_va_antes_que_la_puerta_de_archivo`, `…_antes_que_mirar_el_fichero`; **login en `/cerrar`: sin demostrar (H-R1)** |
| R14 | Casos `[dry_run]` de R3, R9 y R11 (**sin nombre propio: H-R2**) |
| R15 | `test_f034_r15_{adjuntar,cerrar}_sin_…_guardad…_es_409_y_no_usa…`, `…_incompletos_dicen_cual_falta` |
| R16 | `test_f034_r16_cerrar_no_coteja_ni_exige_la_obra`, `…_adjuntar_otra_obra…`, `…_solo_incidencia_*` |
| R17 | `test_f034_r17_{adjuntar,cerrar}_un_cuerpo_sin_…_sigue_siendo_400` |
| R18 | `test_f034_r18_los_dos_cuerpos_piden_lo_mismo_de_siempre` |
| R19 | `test_f034_r19_paso_{grafico,cierre}_ya_no_acepta…`, `…_sin_declarados_…_con_lo_guardado` |
| R20 | `test_f034_r20_{adjuntar,cerrar}_la_puerta_de_aptitud_sigue_yendo_la_primera` |
| R21 | `test_f034_r38_adjuntar_ya_adjuntado_…`; suites de F-012 |
| R22 | Suites de F-012 (`test_f012_cerrar_exige_grafico.py`), en verde |
| R23 | `test_f034_r23_*` (5) |
| R24 | `test_f034_r24_adjuntar_un_codigo_guardado_imposible_es_nombrado_imposible`, `…_el_dominio_del_nombrado…`, `test_f034_h4_codigos_una_obra_sin_tramos…` |
| R25 | Lista cerrada de `test_f034_r39_la_rama_solo_toca_el_codigo_de_produccion_del_diseno` |
| R26 | `test_f034_r26_*` (6), `test_f034_h4_r26_*` |
| R27 | `test_f034_r27_{adjuntar,cerrar}_por_la_ruta_los_dos_errores_nuevos_son_409` |
| R28 | `test_f034_r28_*` (3) |
| R29–R33 | `reintento_vaciado.test.js` (`f034 R29`×3, `R30`×2, `R31`, `R32`×2, `R33`×3); R31 además `test_f034_r31_…` |
| R34 | `test_f034_r34_{adjuntar,cerrar}_el_motivo_no_lleva_nada_del_papel…` |
| R35 | `test_f034_r35_{adjuntar,cerrar}_la_respuesta_sigue_teniendo…` |
| R36 | `test_f034_r27_*` (exigen el tipo en el log y no el motivo) |
| R37 | Estructural (esta tabla); falta R14 con nombre (H-R2) |
| R38 | `test_f034_sin_consultas_de_mas.py` (10) |
| R39 | `test_f034_r39_*`, `test_f034_r23_*` |

## Observaciones (no bloquean)

- **O-1 · Dos mutantes a mano equivalentes, y es buena señal.** Que el cierre
  busque con el número **declarado** si lo hay, o que el gráfico **nombre** con
  los declarados, pasa la suite: tras el cotejo, `normalizar(declarado) ==
  normalizar(guardado)`, y tanto `a_codigo_de_sigrid` como `nombre_de_archivo`
  dependen **solo** de `normalizar_codigo`. Es decir: con el cotejo delante,
  **da igual de cuál de los dos se tome**; y sin cotejo, los tests caen. El
  diseño es robusto por construcción.
- **O-2 · H-6** (corregir un parte `adjuntado` lo pone en `listo` y esconde
  «Reintentar el cierre») es anterior a F-034 y no se pierde el parte. Merece
  su propia ficha; no es de aquí.
- **O-3 · Para el líder**: `rigor.json` fija 120 s por mutante y la suite `api`
  ya tarda 100–130 s; la nota de `azure-apps/postventa_incidencias.md:406-409`
  al desplegar; la frase de F-030 `design.md` §10.7 sobre H-1.

## Propuesta de automejora del protocolo (para que el humano la apruebe)

El recálculo puro y los operadores de `harness.mutacion` no ven **el orden
entre llamadas a puertos distintos**, que es justo lo que protege esta familia
de features (F-030, F-031, F-033, F-034: «la puerta va antes de X»). Propuesta
para `.claude/agents/reviewer.md` (y, si se acepta, para `arnes-base`): en
features `critico` cuyo requisito central sea un **orden** («antes de hablar
con…», «antes de escribir…»), el reviewer aplica al menos una mutación a mano
que **mueva la puerta un paso más abajo** por cada colaborador que la puerta
dice preceder, y exige que muera. Aquí fue lo que encontró H-R1.
