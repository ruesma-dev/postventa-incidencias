<!-- progress/review_F-019.md -->
# F-019 · Informe del reviewer

**Fecha**: 2026-08-26 · **Rama**: `feature/F-019-endpoints-persistencia`
(árbol principal, sin worktree) · **Diff**: `git diff dev...HEAD`, 27 commits
de `8024b2d` a `07dbc5a`.

## Veredicto

> ## CAMBIOS SOLICITADOS (3)

El corazón de la feature está bien hecho y **verificado por mí, no leído del
informe**: la garantía de orden es real y estructural, los tests de F-006 se
apretaron, T1 fue movimiento puro, la clave ajena queda fijada por un test con
su control negativo, las tres condiciones de D1 están cumplidas y la campaña de
mutación es auténtica (la reejecuté entera).

Lo que impide aprobar es **el otro extremo del cable**: el trozo del front que
decidió el humano en D5. **R25 no tiene ningún test, y los tres métodos nuevos
de `js/api.js` tampoco.** No es una sospecha: lo demostré rompiéndolo (§4). Con
`await this._registrarRemesa(datos)` borrado de `app.js` **y** la ruta
`/remesa` cambiada por `/remesas-typo`, los **122 tests de JavaScript siguen en
verde**. Es decir: el cableado que esta feature añade para que los endpoints
dejen de existir sin que nadie los llame **puede desaparecer sin que nada se
entere**, que es el mismo defecto que la feature viene a matar, un nivel más
arriba.

Los tres cambios son pequeños y acotados. Nada del backend hay que tocarlo.

---

## Nivel de rigor

Declarado en `harness/features.json`: **`estandar`**. Según
`harness/rigor.json` y `CHECKPOINTS.md`, exige:

| Puerta | Exigencia | Estado |
|---|---|---|
| **Fase RED** | traza real del rojo en los requisitos centrales | **[x]** siete trazas pegadas y **verificadas contra el historial** (§3.1) |
| **Cobertura** | ≥ 80 % de las líneas cambiadas | **[x]** `PUERTA COBERTURA` en `[OK]`: **100,0 % de 269 líneas** |
| **Mutación** | campaña con todos los supervivientes analizados | **[x]** 35/35 muertos, **reejecutada por mí** (§3.2) |
| Supervivientes máximos | `null` (no exige cero) | 0 supervivientes de todos modos |

`bash harness/init.sh` ejecutado por mí, tal cual: **verde, exit 0**,
`ENTORNO LISTO. Puedes trabajar.`

---

## 1 · Checkpoints

### C1 — El arnés está completo y en verde

- [x] `bash harness/init.sh` termina en exit 0. Ejecutado por mí.
- [x] Están los nueve ficheros obligatorios.

### C2 — El estado es coherente

- [x] Una sola feature `in_progress`: F-019.
- [x] Rama actual `feature/F-019-endpoints-persistencia`, nunca `main`.
- [x] `progress/current.md` encabeza con el estado activo. *Nota*: el fichero
      acumula «Estado anterior» de sesiones previas; es el estilo que este
      repositorio viene usando desde F-008 y no lo introduce F-019, así que no
      lo cuento como resto de sesión.
- [x] `features.json` no se ha tocado durante la implementación: el único
      cambio (`pending` → `in_progress`) es del líder, en `44c45fa`, anterior a
      T1. Verificado con `git log dev..HEAD -- harness/features.json`.

### C3 — El código respeta arquitectura y convenciones

- [x] **Hexagonal respetada.** `interface_adapters/api/{remesa,parte,cola}.py`
      componen el adaptador en el punto de entrada; el dominio no importa
      infraestructura; la única pieza que sabe qué es una `ForeignKeyViolation`
      es `infrastructure/persistencia/repositorio_pg.py`, que la traduce a
      `ReferenciaNoConsta`. `paso_archivo.py` deja subir los errores **sin
      traducir**: no sabe de códigos de estado.
- [x] Primera línea con la ruta en los **cuatro** módulos nuevos, los **siete**
      tests nuevos y el `.test.js`. Comprobado uno a uno.
- [x] Sin `print()`, sin `console.log`, sin TODO sin contexto, sin secretos.
      `python -m ruff check` sobre todo lo nuevo: `All checks passed!`.
      (Los 58 avisos de `init.sh` son deuda previa; ninguno cae en lo tocado.)
- [x] La unidad de trabajo sigue siendo el **parte**: `POST /api/parte` guarda
      uno, con su `hash_parte` como clave.
- [x] **Nada se archiva sin haber pasado las validaciones** — y ahora, además,
      sin constar guardado. Ni un `commit` contra Sigrid: F-019 no toca Sigrid.
- [x] Lo manuscrito no se descarta: `GET /api/cola` devuelve `observaciones` y
      `confianza_observaciones` porque quien decide las necesita delante.
- [x] «Firmado no es conforme» no cambia: `POST /api/parte` **recalcula** el
      veredicto con `domain.models.validacion.validar_parte` (R8) y nunca
      acepta uno hecho.
- [x] **Reprocesar no duplica**: `upsert` por `hash_parte`, con test
      (`test_f019_r9_guardar_dos_veces_el_mismo_hash_devuelve_actualizado`).
- [x] Ningún número de estado de Sigrid hardcodeado (no aplica aquí).
- [x] Ningún PDF ni parte escaneado ha entrado en git:
      `git log dev..HEAD --diff-filter=A` da 18 ficheros, todos `.py`, `.js` o
      `.md`.

**Lo prohibido, comprobado uno a uno:**

| Prohibición | Estado |
|---|---|
| Ni un fichero SQL ni una sentencia DDL | **cumplido**: ningún `.sql` en el diff. T15 lee el DDL como texto y el control negativo trabaja **sobre una copia en memoria** |
| Ningún método nuevo en `RepositorioPartesPort` | **cumplido**: `git diff --stat -- domain/ports/` sale vacío |
| `infra/` intacto | **cumplido**: no aparece en el diff |
| `harness/features.json` intacto | **cumplido** (ver C2) |
| Ninguna conexión real | **cumplido**: ni `psycopg.connect`, ni `requests`, ni `httpx`, ni `socket` en los tests nuevos. Suite del backend: 1233 passed, 13 skipped, **42,4 s**, sin red |

### C3 bis — Documentos de fuera

**N/A justificado**: F-019 no añade ni modifica nada en `docs/referencia/`.
Aun así ejecuté el **barrido de datos sensibles sobre el diff entero**
(§5), porque el encargo lo pedía.

### C4 — La verificación es real

- [ ] **Cada requisito EARS tiene ≥ 1 test trazable.** **NO.** R25 no lo tiene
      (§4, cambio 1). El resto sí; tabla completa en §2.
- [x] Los unit tests no tocan red ni BBDD.
- [x] La verificación `MANUAL (humano)` está listada: **T24 sigue sin marcar**
      en `tasks.md`, con su procedimiento exacto en `tasks.md` Fase 9 y
      ampliado en `progress/impl_F-019.md` §8 (consola del navegador con sesión
      iniciada —el host desnudo devuelve 400—, parte sintético, abrir y
      **volver a cerrar** `ARCHIVO_HABILITADO`). `current.md` la referencia.

### C4 bis — El rigor declarado se cumple

- [x] Declara `rigor: "estandar"`, valor válido.
- [x] **Fase RED**: siete trazas rojas reales, y **el historial las respalda**
      (§3.1).
- [x] **Cobertura**: `[OK]` 100,0 % de 269 líneas, umbral 80 %. Ningún fichero
      «no medido».
- [x] **Mutación verificada de forma independiente** (§3.2).
- [x] **Los muertos están comprobados, no solo contados**: el informe declara
      313,0 s (5,2 min), justo por encima del umbral de 5 minutos. Aun así
      **reejecuté la campaña entera** —el margen era demasiado estrecho para
      fiarse—, con la salida fuera de `progress/`. Coinciden.
- [x] **La campaña tardó lo que tenía que tardar**: 310,9 s × 8 workers ÷ 35
      mutantes = **71,1 s por mutante**, contra una suite de 42–70 s. Ni rastro
      de campaña rápida por construcción. Y **no se apoyó en bytecode viejo**:
      `harness.mutacion` evalúa cada mutante en un **git worktree recién
      creado** (los vi montarse y desmontarse), sin `__pycache__` heredado.
- [x] Cero supervivientes, luego ninguna sección en `PENDIENTE`.
- [x] Sección **«Evidencias»** completa, con los cuatro números **y los
      workers** (8), que es lo que permite calcular el coste por mutante.
- [x] Ningún punto marcado N/A sin justificación.

### C4 ter — Rutas sensibles

**N/A justificado**: este repositorio no declara `harness/rutas_sensibles.json`
(solo existe el `.ejemplo.json`), así que el bloque no aplica y no hay nada que
justificar más allá de esto.

### C5 — La sesión se cerró bien

- [x] `tasks.md` con T1–T23 en `[x]` y **T24 sin marcar a propósito** (es
      `MANUAL (humano)`).
- [x] Un commit `F-019 Tn: ...` por tarea. Los 23 están.
- [x] `git status` limpio, sin artefactos sueltos. Comprobado también
      **después** de mi campaña de mutación: los ocho worktrees temporales se
      desmontaron solos.
- [x] `features.json` refleja el estado real (`in_progress`).

---

## 2 · Trazabilidad requisito → test

| R | Test que lo cubre | ¿Cubierto? |
|---|---|---|
| R1 | `test_f019_r1_registrar_una_remesa_devuelve_200_con_su_contrato`, `…r1_la_remesa_llega_al_puerto_con_lo_que_se_mando` | sí |
| R2 | `…r2_con_remesa_id_dado_se_usa_ese_y_no_se_genera_otro`, `…r2_el_mismo_remesa_id_dos_veces_no_crea_una_segunda` | sí |
| R3 | `…r3_sin_remesa_id_se_genera_uno_y_se_devuelve`, `…r3_dos_altas_sin_remesa_id_son_dos_remesas_distintas` | sí |
| R4 | 5 tests, incluido `…r4_una_remesa_de_cero_partes_es_valida` (nacido de la mutación) | sí |
| R5 | `…r5_un_remesa_id_que_no_es_uuid_es_400_sin_llegar_a_la_base` | sí |
| R6 | `…r6_el_usuario_oid_se_guarda_en_null` | sí |
| R7 | 3 tests, incluido `…r7_el_envoltorio_delega_el_resto_del_puerto` | sí |
| R8 | `…r8_el_veredicto_se_recalcula_y_no_se_acepta_el_del_cuerpo` (+2) | sí |
| R9 | `…r9_guardar_dos_veces_el_mismo_hash_devuelve_actualizado` (+1) | sí |
| R10 | 7 tests, incluido `…r10_el_error_no_publica_lo_que_si_venia` | sí |
| R11 | `…r11_sin_remesa_registrada_responde_409_y_no_deja_fila` (+1) | sí |
| R12 | `…r12_el_parte_se_guarda_sin_contenido`, `…r12_un_contenido_b64_en_el_cuerpo_no_se_guarda` (+1) | sí |
| R13 | `…r13_si_la_base_no_esta_responde_503`, `…r13_el_503_no_se_confunde_con_el_409` (+1) | sí |
| R14 | 5 tests | sí |
| R15 | `…r15_sin_limite_se_piden_cincuenta`, `…r15_el_limite_de_la_peticion_se_respeta` | sí |
| **R16** | `…r16_ningun_limite_supera_el_tope_duro[501/1000/100000]`, `…r16_una_peticion_desmedida_se_acota_y_no_se_rechaza`, `…r16_la_respuesta_nunca_trae_mas_del_tope` | sí |
| R17 | `…r17_un_limite_que_no_es_entero_positivo_es_400`, `…r17_el_limite_uno_es_valido_y_llega_tal_cual` (de la mutación) | sí |
| R18 | 5 tests + control negativo parametrizado con los cinco valores | sí |
| **R19** | 8 tests, incluido `…r19_la_traza_previa_se_escribe_antes_de_tocar_el_archivador` y los dos del DDL | sí |
| **R20** | 7 tests, incluido `…r20_si_el_parte_no_consta_el_archivador_no_recibe_nada` | sí |
| R21 | `…r21_si_la_base_no_responde_tampoco_se_sube_nada` (+1) | sí |
| R22 | `…r22_un_fallo_del_proveedor_deja_pendiente_y_luego_error` (+2) | sí |
| R23 | `…r23_con_la_ventana_cerrada_el_repositorio_no_recibe_nada` | sí |
| R24 | `…r24_con_el_parte_ya_archivado_no_se_escribe_la_traza_previa` (+1) | sí |
| **R25** | **ninguno** | **NO** (§4, cambio 1) |
| R26 | `persistencia.test.js`: 7 tests (orden, cuerpo, sin bytes) | sí, salvo la ruta HTTP (§4, cambio 2) |
| R27 | `persistencia.test.js`: 7 tests | sí |
| R28 | `persistencia.test.js`: 4 tests | sí |
| R29 | `test_f010_r32_la_anonimidad_es_deliberada_y_esta_explicada` con `ENDPOINTS` a nueve + `test_f010_r32_el_barrido_de_niveles_ve_lo_que_hay` (`== len(ENDPOINTS) == 9`) | sí (sin `r29` en el nombre; es el mapeo que la propia spec previó) |
| R30 | `test_f019_r30_la_cabecera_dice_donde_esta_la_proteccion_de_verdad`, `…_dice_que_anade_la_cola_al_cuadro` | sí |
| R31 | — | **por inspección del reviewer** (§3.3). Es un requisito sobre la cabecera del propio fichero de test; leí el antes y el después y la afirmación falsa ha desaparecido |
| R32 | 6 tests entre `test_f019_documentacion.py` y `test_f010_integracion_expuesto.py` | sí |
| R33 | 3 tests sobre el paso 6 de `ARCHITECTURE.md` | sí |
| R34 | 4 tests, incluido `…r34_ningun_handler_nuevo_mira_la_ventana_de_escritura` | sí |

---

## 3 · Lo que comprobé mirando el código, no el informe

### 3.0 · La garantía de orden es real y no depende del llamante

Es lo primero que fui a buscar, porque es el requisito. **Lo es.**

En `application/pipelines/paso_archivo.py:136`, `_dejar_constancia_previa` va
**antes** de `_subir` y **fuera** de cualquier `try`: si levanta, el archivado
se aborta sin haber llamado al archivador. Y no hay comprobación paralela en
Python que pueda divergir —no se añadió ningún `consta_parte` al puerto—: la
que decide es la restricción real, `archivos.hash_parte → partes.hash_parte`,
traducida a `ReferenciaNoConsta` en
`infrastructure/persistencia/repositorio_pg.py:224`, donde el `except
ForeignKeyViolation` va **antes** del `except psycopg.Error` (si estuviera
después, no se alcanzaría nunca: es subclase).

Respuesta a la pregunta del encargo —«si alguien llama a `/api/archivar` por su
cuenta, sin haber guardado el parte, ¿puede subirse el fichero igual?»—: **no**.
No porque los tests lo digan, sino porque para llegar a `_subir` hay que haber
escrito antes una fila en `archivos`, y esa fila no se puede escribir sin el
parte. El único camino que la esquiva es el de la idempotencia (`_ya_archivado`),
y ese ya no sube nada por definición.

Y `ReferenciaNoConsta` **no hereda** de `PersistenciaNoDisponible`, a propósito:
si heredara, el `except` del borde se la tragaría y volvería el 503 engañoso sin
que ningún test lo notara. Está escrito en el docstring y comprobado por
`test_f019_r20_referencia_no_consta_no_es_persistencia_no_disponible`.

R23 también se sostiene por construcción, no por costumbre: en
`interface_adapters/api/archivar.py:110-112`, `construir_archivador(ajustes)`
se evalúa **antes** que `construir_repositorio(ajustes)` en la lista de
argumentos, así que con la ventana cerrada salta `ArchivoDeshabilitado` sin
haber abierto siquiera la conexión.

### 3.1 · Los tests de F-006 se apretaron, y el historial lo prueba

`test_f006_paso_archivo.py` no bajó ningún listón: **subió tres**.

- `test_f006_r23_…`: `llamadas_guardar_archivo == 2` y
  `estados == ["pendiente", "archivado"]`. No «al menos una».
- `test_f006_r24_…`: `== 2` y `["pendiente", "error"]`.
- `test_f006_r14_…`: `== 0` con el parte ya archivado (R24).

`test_f010_borde_persistencia.py` es el único que se «precisó», y lo miré con
lupa porque era el candidato natural a aflojarse: conserva **todas** sus
aserciones (`biblioteca.subidas == 1`, 500 con cuerpo legible) y **añade** el
caso nuevo. Lo que cambió es el montaje del doble —falla en la segunda llamada,
no en las dos—, porque con la garantía de orden el montaje viejo ya reproducía
**otro** escenario. Está explicado en la cabecera del fichero.

`tests_js/pipeline.test.js` solo gana `guardado: true` en el fixture común, que
es una consecuencia obligada de que `cuerpoDeArchivo` ahora exija el guardado; y
esa exigencia tiene sus dos tests propios en `persistencia.test.js`.

**La fase RED la verifiqué contra el historial, no contra el informe**:
`git show --stat` de los siete commits `RED` (`825d279`, `b44f064`, `56cc49a`,
`3d61211`, `c6791e1`, `6f52a7f`, `8f0b70a`) confirma que **ninguno toca código
de producción**: solo ficheros de `tests/` y los dos dobles. La traza roja
pegada y el historial cuentan lo mismo.

### 3.2 · La campaña de mutación es auténtica

Tres comprobaciones, en este orden:

1. **Recálculo puro.** `harness.alcance` me devuelve exactamente la misma tabla
   de alcance del informe —los nueve ficheros y **1159 líneas**— y
   `harness.mutacion.generar_mutantes` sobre ellos, **35 mutantes**
   (19 `entero`, 10 `not`, 4 `logico`, 2 `comparacion`). Cuadra al mutante.
2. **Reejecución completa.** El informe declara 313,0 s: 5,2 min, apenas por
   encima del umbral. Relancé la campaña entera con `--workers 8` y salida a mi
   scratchpad (**nunca a `progress/`**): **35 evaluados, 35 muertos, 0
   supervivientes, 0 timeouts en 310,9 s**. Idéntico. `git status` limpio
   después.
3. **Nada de bytecode viejo.** No hace falta confiar: la herramienta evalúa cada
   mutante en un **git worktree recién creado**, sin `__pycache__` heredado.
   Verifiqué los ocho worktrees vivos durante la campaña y desmontados al
   terminar.

Los dos supervivientes de fondo que el implementer cerró con tests
—`cola.py:109 pedidas < 1` y `remesa.py:129 crudo < 0`— aparecen en mi campaña
como **muertos**, junto a sus variantes `<= 1`, `< 2`, `<= 0` y `< 1`. Eran
agujeros reales, en el valor frontera que el requisito declara **válido**, y
están cerrados de verdad.

### 3.3 · Las tres condiciones de D1

1. **Tope duro en el handler, además del techo del repositorio.** **Cumplido.**
   `interface_adapters/api/cola.py:118` hace `min(pedidas, LIMITE_MAXIMO_COLA)`
   —el handler, que es quien decide qué se le pide a la base— y la línea 86
   añade el segundo cinturón sobre lo devuelto (`entradas[:LIMITE_MAXIMO_COLA]`).
   `sentencias._limite_seguro` sigue en su sitio. `LIMITE_MAXIMO_COLA == 500`, y
   el test lo fija literalmente para que no lo cambien por debajo.
2. **Ningún dato personal en el log.** **Cumplido.** Repasé los tres handlers:
   `remesa` registra `id` y `resultado` y **no** el `nombre_origen` (puede llevar
   la promoción); `parte`, hash y resultados; `cola`, **solo el recuento**. Los
   mensajes de las excepciones nombran la clave o la operación, jamás el valor
   —`_referencia_no_consta` descarta a propósito el `DETAIL` de PostgreSQL, que
   trae la clave insertada—. El guardián tiene control negativo **parametrizado
   con los cinco valores**, que es lo correcto: uno que solo probara el DNI
   dejaría los otros cuatro sin vigilar.
3. **La cabecera de `test_f010_endpoints_protegidos.py` deja de mentir, sin
   relajar el test.** **Cumplido.** Ya no dice «quedan en internet»: cuenta el
   backend enlazado con Easy Auth `azureStaticWebApps`, la regla `/*` y el grupo,
   y explica **por qué el `auth_level` sigue en `ANONYMOUS`** (porque `FUNCTION`
   rompe el front). Y sigue fallando **por las dos vías**, esta vez comprobado
   por mí sobre el código del test, no sobre el informe:
   - cambiar un `auth_level` → cae `set(declarados.values()) == {"ANONYMOUS"}`;
   - borrar la explicación → caen las aserciones de subcadena de cuatro tests
     distintos;
   - y `test_f010_r32_el_barrido_de_niveles_ve_lo_que_hay` sostiene a los demás
     con `len(niveles(codigo)) == len(ENDPOINTS) == 9`, que es lo que impide que
     un patrón que deje de casar los vuelva verdes vacíos.

### 3.4 · T1 fue movimiento puro, y lo comprobé por AST

No me fié de leer el diff. Comparé el **AST** de los cinco parsers en
`validar.py@dev` contra `cuerpos.py@HEAD`, normalizando docstrings y los
renombrados de `_bloque`→`bloque` etc.:

- `a_campo` y `a_traza`: **idénticos byte a byte**.
- `bloque`, `a_extraccion`, `a_lectura_de_firma`: la **única** diferencia son
  renombrados de variable local y de parámetro (`bloque`→`hallado`,
  `bloque`→`bloque_extraccion`, `bloque`→`bloque_firma`), forzados porque
  `bloque` pasó a ser el nombre de la función de módulo. **Ni una regla ni un
  mensaje de error cambian.**
- Las tres constantes de claves: idénticas.

Y `test_f004_validar_http.py` **no aparece en el diff**: la red aguantó sin
tocarla, que era el punto.

### 3.5 · T15, la clave ajena

`test_f019_r19_archivos_referencia_a_partes_y_es_un_requisito` afirma
`REFERENCES postventa.partes (hash_parte)` sobre el texto del `.sql`, y
`test_f019_r19_el_barrido_de_la_clave_ajena_ve_lo_que_hay` es el control
negativo que impide que la aserción esté mirando una cadena que ya no es el
`CREATE TABLE` de `archivos`. El control trabaja **sobre una copia en memoria**:
no se toca el `.sql` del repositorio ni se ejecuta DDL contra nadie.

### 3.6 · T24 sigue sin marcar

Confirmado: `- [ ] **T24**` en `tasks.md`, con el procedimiento exacto —los
cuatro pasos, la vía por consola del navegador, el parte sintético, y el
recordatorio de **volver a cerrar `ARCHIVO_HABILITADO`**—. Ningún agente la ha
tocado, que es lo que tenía que pasar.

---

## 4 · Cambios requeridos

### 1. R25 no tiene ningún test, y se puede borrar sin que nada falle

**Dónde**: `services/postventa-front/js/app.js:125`
(`await this._registrarRemesa(datos);`) y el fichero que dice cubrirlo,
`services/postventa-front/tests_js/persistencia.test.js:12`.

**Qué pasa**: R25 exige que el front registre la remesa **antes** de procesar
ningún parte y que conserve el `remesa_id` durante toda la sesión. Esa lógica
vive entera en `app.js`, y `app.js` no lo ejecuta **ningún** test: el único que
lo mira es `node --check` (sintaxis) y dos guardias textuales de F-007
(`test_f007_r36_app_js_es_solo_pegamento`, que es una lista negra de tokens como
`fetch(` o `new FormData` y no se entera de esto).

**Demostrado, no supuesto.** Sobre una copia aislada del servicio —nunca sobre
el árbol real— borré la línea 125. Resultado:

```
ℹ tests 122
ℹ pass 122
ℹ fail 0
```

Es decir: la llamada que hace que los tres endpoints nuevos se usen puede
desaparecer y **la suite no se entera**. Es literalmente el defecto que F-019
existe para matar —«el puerto existe y nadie lo llama»— reproducido un nivel más
arriba, en el cableado que el humano decidió meter aquí con D5.

Agrava el caso que la cabecera de `persistencia.test.js` afirme, en su línea 12,
que «R25 · la remesa se registra ANTES de procesar ningún parte» es lo que ese
fichero prueba. No lo prueba. Y las tablas de trazabilidad de
`requirements.md:232` y `design.md:52` mapean R25–R28 a ese fichero. Es una
cabecera que dice algo que no es cierto, que es exactamente lo que T17 arregló
en otro sitio en esta misma feature.

**Qué hacer** (cualquiera de las dos, no las dos):

- **(a)** Sacar el orden de `app.js` a un módulo probable —lo natural es
  `js/pipeline.js`, que ya es donde vive «qué se pide y en qué orden»— con una
  función tipo `procesarRemesa(datos, api)` que registre y luego procese, y
  probarla en `persistencia.test.js` contra el `api` doble que ya existe,
  afirmando `llamadas === ["registrarRemesa", …]`. Es coherente con la regla de
  oro de `app.js` («si algo merece un test, no vive aquí»), que este cambio
  incumplió.
- **(b)** Si se prefiere dejarlo en `app.js`, escribir un test que instancie
  `appPostventa()` con dobles y afirme el orden y la conservación de
  `remesaId` —incluido que `_reiniciar()` lo limpia—. Es más trabajo y rompe la
  regla de oro, pero cierra el requisito.

En ambos casos, **corregir la cabecera de `persistencia.test.js` y las tablas de
trazabilidad** para que digan la verdad sobre dónde se prueba R25.

### 2. Los tres métodos nuevos de `js/api.js` no los prueba nadie: la ruta puede estar mal y todo sigue verde

**Dónde**: `services/postventa-front/js/api.js:303` (`registrarRemesa`), `:323`
(`guardarParte`), `:340` (`cola`).

**Qué pasa**: `persistencia.test.js` prueba `pipeline.js` contra un **`api`
doble**, así que nada comprueba lo que `api.js` hace de verdad: a qué ruta
llama, con qué método, con qué `Content-Type`, ni cómo compone
`/cola?limite=…`. R25 y R26 no dicen «llama a algo», dicen «llama a
`POST /api/remesa`» y «llama a `POST /api/parte`».

**Demostrado**: en la misma copia aislada cambié
`peticion("/remesa"` por `peticion("/remesas-typo"`. Los **122 tests de
JavaScript siguen en verde**. En el entorno real eso es un 404 en cada remesa,
ningún parte guardable y ningún parte archivable —y ningún test rojo que lo
avise.

**Qué hacer**: añadir a `services/postventa-front/tests_js/api.test.js` —que es
el fichero que F-007 dejó exactamente para esto, con su doble de `fetch` ya
montado (`apiDePrueba`)— un test por método:

- `registrarRemesa` → `POST /api/remesa`, cuerpo JSON,
  `Content-Type: application/json`;
- `guardarParte` → `POST /api/parte`, con el `hash` en la traza;
- `cola` → `GET /api/cola` sin `limite`, y `GET /api/cola?limite=25` con él
  (que es lo único que ejercita el `encodeURIComponent`).

### 3. `api.test.js` sigue diciendo «los seis endpoints» cuando ya son nueve

**Dónde**: `services/postventa-front/tests_js/api.test.js:99`,
`test("f007 R27: los seis endpoints cuelgan de baseApi", …)`.

**Qué pasa**: es menor y no rompe nada, pero esta feature ha dedicado T16, T17 y
T18 a que las cabeceras y las tablas dejen de decir «seis» donde hay nueve
(`function_app.py`, `ENDPOINTS`, `INTEGRACION.md` §8). Este título se quedó
atrás. Y de paso: el test solo comprueba **dos** endpoints (`salud` y
`validar`), así que el título prometía de más ya antes.

**Qué hacer**: renombrarlo a nueve y, ya que se toca, hacer que recorra de
verdad la lista —encaja bien con el cambio 2, que va al mismo fichero.

---

## 5 · Barrido de datos sensibles y secretos

Ejecutado por mí sobre **las líneas añadidas del diff completo**
(`git diff dev...HEAD`), con estos patrones:

| Patrón | Hallazgos |
|---|---|
| GUID / UUID literal | **0** — los identificadores de los tests se generan en ejecución (lo arregló el implementer cuando `test_f006_repo_sin_identificadores.py` cazó dos) |
| `password` / `secret` / `api_key` / `token` / `connectionstring` con valor | **0** |
| `PG_PASSWORD=` con valor | **0** |
| IP privada (10/172.16-31/192.168) | **0** |
| Host de Azure (`azurewebsites.net`, `postgres.database.azure.com`, `sharepoint.com`, `blob.core.windows.net`) | **0** |
| `Bearer <token>` | **0** |
| Correo electrónico | **0** reales (solo falsos positivos de `@pytest.mark` y `@app.route`) |
| DNI español | **8**, todos `00000000T`, **número no emitido**, marcado como inventado en cada sitio donde aparece |

Los valores de negocio de los tests (`0677`, `RS26.08/0123`, promociones) están
declarados inventados en las cabeceras. **Sin secretos, sin cadenas de conexión
y sin datos personales** en código, tests, spec ni `progress/`.

---

## 6 · Observaciones para el líder (no bloquean)

1. **`traza_previa` nunca llega desde el borde.**
   `interface_adapters/api/archivar.py` llama a `paso_archivo` sin pasar
   `traza_previa`, así que en producción es siempre `None`: la capa de
   idempotencia por traza (F-006 R14) **no está cableada**, y con ella R24. No
   es regresión de F-019 —viene tal cual de F-006— y el efecto neto no empeora
   (el `upsert` y el reemplazo de SharePoint siguen evitando duplicados), pero
   conviene saber que hoy la traza previa se escribe **siempre**, y que el test
   `test_f019_r24_…` protege un camino que el borde no recorre. Candidato a
   ficha nueva, o a una línea en la de rehidratación.
2. **R31 lo doy por bueno por inspección**, no por test: es un requisito sobre
   la cabecera del propio fichero de test. Leí el antes y el después y la
   afirmación falsa —«quedan en internet»— ha desaparecido, sustituida por el
   modelo vigente. Si se quisiera blindar, sería un test que lea la cabecera de
   ese fichero; me parece desproporcionado y no lo pido.
3. **Sigue pendiente copiar `docs/INTEGRACION.md` §8 a
   `azure-apps/postventa-incidencias.md`**, como avisa el implementer en su §9.
   Cambian la tabla de endpoints (nueve filas), la nota de anonimidad y la tabla
   de ausencias. Los agentes no commitean en ese repositorio.
4. **Al cerrar hay que decir lo de D4**: lo guardado queda guardado y la cola
   sobrevive, pero **recargar el navegador sigue perdiendo el trabajo en
   curso**. Ya está bien reatribuido en `INTEGRACION.md` y con test que lo fija.
5. **`POST /api/archivar` cambia de contrato para quien ya lo llamaba**: un
   parte sin guardar recibe ahora **409** donde antes recibía un 500 o un 200 a
   medias. Es la mejora, pero es un cambio observable.

---

## 7 · Automejora del arnés (propuesta, no aplicada)

Esta review casi deja pasar el hueco de R25 porque **todas las puertas
automáticas son ciegas al front**: `harness/alcance.py` solo mide y muta `.py`,
así que las 96 líneas de `app.js`, las 60 de `api.js` y las 16 de `index.html`
no entran ni en la cobertura del 100 % ni en los 35 mutantes. Un requisito
puede quedarse sin test en JavaScript y las tres puertas del nivel `estandar`
salen en verde.

Propongo al humano añadir a `CHECKPOINTS.md`, en C4, una línea del tipo:

> En un servicio con código no medido por las puertas (JavaScript, HTML), el
> reviewer comprueba la trazabilidad de **esos** requisitos a mano, y lo dice
> por escrito: la cobertura y la mutación no los miran.

Y, en el mismo bloque, elevar a norma lo que aquí funcionó: **ante un requisito
que dice «el sistema llama a X antes que a Y», el reviewer borra la llamada en
una copia aislada y comprueba que algo se pone rojo.** Un requisito de orden que
sobrevive a que le quiten el orden no está probado.

No lo aplico: lo decide el humano. Si lo aprueba, va también a `arnes-base`.

---
---

# Re-review · segunda ronda (2026-08-26)

> **Lo de arriba no se toca**: es el rastro de la primera ronda y explica por
> qué esta feature tuvo que volver. Esto se añade debajo.

**Encargo**: verificar las tres correcciones de
`progress/impl_postreview_F-019.md`, commits `886ff31` … `0156b64`. Se eligió mi
**opción (a)** del cambio 1: el orden sale de `app.js` a
`js/pipeline.js::procesarRemesa`.

## Veredicto de la segunda ronda

> ## APROBADO

Los tres cambios están cerrados, y lo he comprobado **con el método que destapó
el problema**: romper lo que cada test dice proteger sobre una copia aislada y
mirar si la suite se pone roja. **Nueve roturas, nueve rojos.** En la primera
ronda, dos de esas mismas roturas dejaban los 122 tests en verde.

`bash harness/init.sh` ejecutado por mí: **verde, exit 0**, `PUERTA COBERTURA`
en `[OK]` con 100,0 % de 269 líneas.

---

## 1 · Las nueve roturas, y lo que pasó con cada una

Método: copia del servicio `postventa-front` en mi scratchpad —**nunca sobre el
árbol real**—, una rotura por copia, y en cada una `node --test tests_js/*.test.js`
más `pytest tests/test_f007_estaticos.py`. Copias borradas al terminar; el árbol
del repositorio quedó limpio (`git status` vacío).

**Línea base sobre copia limpia**: `140 pass, 0 fail` en JavaScript (eran 122) y
`20 passed` en `test_f007_estaticos.py` (eran 18). Las dos en exit 0, que es lo
que hace que un rojo signifique algo.

| # | Qué rompí | JS | estáticos | ¿Rojo? |
|---|---|---|---|---|
| A | `app.js` deja de delegar en `Pipeline.procesarRemesa` y monta el orden a mano | 0 | **1 failed** | **sí** |
| B | Dentro de `procesarRemesa`, procesar **antes** de registrar | **exit 1**, 4 failed | 0 | **sí** |
| C | `procesarRemesa` no llega a llamar a `api.registrarRemesa` | **exit 1** | 0 | **sí** |
| D | `reiniciar()` deja de limpiar `this.remesaId` | 0 | **1 failed** | **sí** |
| E | `api.js`: `/remesa` → `/remesas-typo` | **exit 1**, 2 failed | 0 | **sí** |
| F | `api.js`: `registrarRemesa` pasa de `POST` a `GET` | **exit 1**, 2 failed | 0 | **sí** |
| G | `api.js`: `registrarRemesa` pierde el `Content-Type: application/json` | **exit 1** | 0 | **sí** |
| H | `api.js`: `/parte` → `/partes-typo` | **exit 1** | 0 | **sí** |
| I | `api.js`: `/cola` → `/colas-typo` | **exit 1** | 0 | **sí** |

**E y A son exactamente las dos roturas de la primera ronda**, las que entonces
dejaban los 122 tests en verde. Hoy caen. El agujero está cerrado, y lo está por
construcción y no por promesa.

Qué cae en cada caso, con nombre y apellidos:

- **B (orden invertido)** → `f019 R25: la remesa se registra ANTES de procesar
  ningún parte`, `…: si el registro tarda, NO se adelanta el procesado`,
  `…: el remesa_id se devuelve y llega al procesado`, `…: si el registro falla,
  los partes se procesan IGUAL`.
- **E, F (ruta y método)** → `f007 R27 / f019: los NUEVE endpoints llaman a su
  ruta, con su metodo` **y** `f019 R25: registrarRemesa manda POST /api/remesa
  con cuerpo JSON`. Dos tests independientes, que es lo correcto: si mañana se
  reescribe uno, el otro sigue.
- **I (`/cola`)** → el de los nueve **y** `f019: cola sin limite pide GET
  /api/cola, sin cadena de consulta`.
- **A y D** → los dos guardianes textuales nuevos de `test_f007_estaticos.py`.

### El test que más me convenció

`f019 R25: si el registro tarda, NO se adelanta el procesado`. Deja el registro
**pendiente** en una promesa sin resolver, cede el turno al bucle de eventos y
afirma que el procesado **todavía no ha empezado**. Sin él, una implementación
que lanzara las dos cosas a la vez pasaría el test de orden por puro azar en el
orden de resolución. Es la diferencia entre probar el orden y probar el
resultado, y está bien vista.

## 2 · Que ningún listón bajó

Repasé **todos** los borrados de la ronda:

- `js/app.js`: pierde `_registrarRemesa` porque se **mudó**, no porque se
  quitara. `_nombreDeLaRemesa` sigue y se usa como `nombreOrigen`. El
  comportamiento ante un registro fallido se conserva entero —los partes se
  procesan igual y quedan no archivables con su motivo (R27)— y ahora **tiene
  test** (`f019 R25: si el registro falla, los partes se procesan IGUAL` y
  `…: y el motivo se cuenta, no se traga`), que antes no lo tenía.
- `tests_js/api.test.js`: las **seis** líneas borradas son el cuerpo del viejo
  «los seis endpoints cuelgan de baseApi», que comprobaba dos endpoints. Lo
  sustituyen tres tests **estrictamente más fuertes**: ruta y método exactos de
  los nueve, `baseApi` configurable en los nueve, y una cuenta que se entera si
  aparece un décimo (`Object.keys(api)` menos la maquinaria, `=== 9`, y además
  comparada con la lista).
- `tests_js/persistencia.test.js` y `tests/test_f007_estaticos.py`: **cero
  borrados**, solo añadidos.
- El backend: **ni una línea**. `git diff 99f6f47...HEAD` no toca
  `services/postventa-api/`.

## 3 · Las cabeceras y las tablas ya dicen la verdad

- **`persistencia.test.js`** ya no afirma cubrir R25 a secas: dice qué prueba
  aquí (el orden, ahora en `pipeline.js`) y **nombra las dos mitades que no
  están en este fichero y dónde están** —el guardián de `app.js` y las rutas de
  `api.test.js`—, con el motivo: aquí el `api` es un doble y un doble no puede
  decir a qué ruta se llama.
- **`requirements.md:232`** y **`design.md:52`**: la fila única pasa a tres, con
  la nota que explica por qué la que había era falsa a medias. Leí las tres
  filas contra los ficheros que citan: **coinciden**.

Es el mismo arreglo que T17 hizo en `test_f010_endpoints_protegidos.py`, ahora
aplicado a sí mismos. Es lo que había que hacer.

## 4 · Que el encargo no se desbordó

| Límite | Estado |
|---|---|
| Backend intacto | **cumplido**: el diff de la ronda solo toca `services/postventa-front/`, `specs/` y `progress/` |
| `infra/` intacto | **cumplido** |
| `harness/features.json` intacto | **cumplido** |
| Ninguna conexión real | **cumplido**: `fetch` y `api` son dobles inyectados; ni un socket |
| **T24 sin marcar** | **cumplido**: `tasks.md:241` sigue en `- [ ] **T24**` |
| Sin secretos ni datos personales | **cumplido**: barrido del diff de la ronda — 0 GUID, 0 DNI, 0 credenciales, 0 IP, 0 host de Azure, 0 `console.log`, 0 `print` |
| `ruff` | `All checks passed!` sobre lo tocado |

Suites completas, ejecutadas por mí: backend **1233 passed, 13 skipped**
(idéntico, no se tocó), front **87 passed** (eran 85), JavaScript **140 pass, 0
fail** (eran 122).

## 5 · Las puertas del rigor, revisadas

- **Fase RED**: `886ff31` («post-review 1 RED») **solo añade tests** —200 líneas
  entre `persistencia.test.js` y `test_f007_estaticos.py`, cero código de
  producción—, y el código llega en `28451df`. Verificado con `git show --stat`,
  no leído del informe. Para los cambios 2 y 3, que nacían verdes porque el
  código ya existía, el implementer hace lo que corresponde: demostrar que saben
  fallar rompiendo `api.js` de cinco formas. **Lo he reproducido yo** (casos E–I
  de §1) en vez de creérmelo.
- **Cobertura**: `[OK]`, 100,0 % de 269 líneas. El número no se mueve porque las
  puertas **no miran JavaScript**, que es justo la observación de mi §7 de la
  primera ronda; por eso esta verificación tenía que ser a mano.
- **Mutación**: el informe dice que no se relanza porque no cambió ni un `.py`
  de producción. **Lo he comprobado**, no aceptado: recalculé el alcance con
  `harness.alcance` y los mutantes con `harness.mutacion.generar_mutantes`, y
  sale **exactamente lo mismo que antes de esta ronda**: 9 ficheros, 1159
  líneas, **35 mutantes**. `progress/mutacion_F-019.md` sigue siendo válido, y
  yo ya reejecuté esa campaña entera en la primera ronda (35/35 muertos).

## 6 · Estado de los tres cambios pedidos

| # | Cambio pedido | Estado |
|---|---|---|
| 1 | R25 sin ningún test | **cerrado**. Orden mudado a `pipeline.js::procesarRemesa` (opción a), 8 tests nuevos en `persistencia.test.js` y 2 guardianes textuales en `test_f007_estaticos.py`. Cabeceras y tablas corregidas |
| 2 | Los tres métodos de `js/api.js` sin probar | **cerrado**. Ruta, método, `Content-Type`, cuerpo verbatim, `?limite=` y el escape que impide colar un segundo parámetro. Y un test de que la traza no publica nada del papel |
| 3 | «los seis endpoints» | **cerrado**. Pasa a nueve, recorre la lista de verdad y añade la cuenta que caza un décimo |

## 7 · Una cosa menor que dejo dicha, y que no bloquea

**`services/postventa-front/js/pipeline.js:241-249`: el docstring de
`procesarParte` quedó huérfano.** Al insertar `procesarRemesa` justo debajo, el
bloque `/** Procesa UN parte: extraer y firma en paralelo… */` (línea 242) quedó
**encima del docstring de `procesarRemesa`** (línea 251), así que hoy no
documenta nada, y `procesarParte` —que está en la línea 305— se quedó **sin
docstring**.

No bloquea: no afecta a ningún requisito, ni a ningún test, ni al
comportamiento. Pero en una feature que ha dedicado T16, T17, T18 y media
segunda ronda a que las cabeceras dejen de decir lo que no es, un comentario que
describe la función equivocada es de la misma familia, en pequeño. **Se arregla
moviendo esas ocho líneas justo encima de `async function procesarParte`**, y
conviene hacerlo antes del merge.

## 8 · Lo que sigue pendiente para cerrar (no es del implementer)

Sin cambios respecto a la primera ronda, y sigue siendo trabajo del líder y del
humano:

1. **T24**, la verificación `MANUAL (humano)` contra el entorno desplegado, con
   la ventana de escritura abierta a propósito **y cerrada al terminar**.
   Procedimiento en `tasks.md` Fase 9 y `progress/impl_F-019.md` §8.
2. **Copiar `docs/INTEGRACION.md` §8 a `azure-apps/postventa-incidencias.md`**.
3. **Decir lo de D4** al cerrar: recargar el navegador sigue perdiendo el
   trabajo en curso; rehidratar la sesión es feature nueva.
4. La propuesta de automejora de `CHECKPOINTS.md` de mi §7 de la primera ronda
   sigue sobre la mesa, y esta ronda la respalda: las tres puertas automáticas
   son ciegas al JavaScript, y las 18 pruebas que faltaban solo aparecieron
   rompiendo el código a mano.

---

**Veredicto final de F-019: APROBADO.**
