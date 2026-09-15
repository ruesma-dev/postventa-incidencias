<!-- progress/review_F-026.md -->
# F-026 · Aprobación humana de los partes que van a revisión — Review

**VEREDICTO: APROBADO**

> Revisión del 2026-09-12 sobre la rama `feature/F-026-aprobacion-humana`.
> Diff revisado: `git diff feature/F-025-confirmacion-unica...HEAD`
> (53 ficheros, +10 248 / −247). No se ha cambiado de rama, no se ha tocado
> ningún fichero del implementer y no se ha ejecutado nada contra Azure,
> Sigrid, `sigrid-api`, el PostgreSQL compartido ni SharePoint.
>
> **El bloque 6 (verificación contra la base real, del responsable) y el
> bloque 7 (cierre, del líder) quedan pendientes por encargo y no cuentan
> como reparos.** Lo que falta de cada uno está en §5.

---

## 1 · Nivel de rigor y puertas que exige

| Concepto | Valor |
|---|---|
| `rigor` declarado en `harness/features.json` | **`estandar`** (declarado, no por omisión) |
| Qué exige (`harness/rigor.json`) | C1–C3, C3 bis, C5 + tests trazables (C4) + **fase RED** + **cobertura ≥ 80 %** de las líneas cambiadas + **campaña de mutación** con supervivientes analizados |
| Supervivientes máximos | `null` — se documentan y el reviewer juzga (no es `critico`, que exige cero) |

Verificado a mano: `harness/features.json` declara `"rigor": "estandar"` para
F-026, y `harness/rigor.json` lo reconoce como nivel válido.

---

## 2 · Lo que se ha comprobado a fondo (los ocho puntos del encargo)

### 2.1 · La aprobación se registra **al lado** del veredicto, nunca encima — ✅

Sostenido en los tres sitios donde se podía romper:

- **En la base**: `postventa.aprobaciones` es **tabla propia**
  (`sql/10_aprobaciones.sql`), con `hash_parte` como PK y FK contra
  `postventa.partes`. **Ni una columna de `postventa.validaciones` cambia**:
  el diff no toca `sql/04_validaciones.sql` ni `upsert_validacion`. Verificado
  que ningún camino escribe `apto` sobre un `no_apto`: `grep` de
  `upsert_validacion` devuelve un único llamante (`guardar_validacion`), y ahí
  el `ResultadoValidacion` viaja tal cual lo emitió `validar_parte`.
- **En el dominio**: `admite_circuito()` es una función **pura** que devuelve
  verdadero por dos caminos disjuntos y no modifica el `ResultadoValidacion`.
  `domain/models/validacion.py` no aparece en el diff.
- **En la pantalla**: `semaforoDe(validacion, aprobacion)` gana un **cuarto**
  estado `"aprobado"` —verde **con anillo**, `ring-2 ring-sky-600`— y no un
  verde más, más el texto «Aprobado por revisión humana · venía de … · …».
  `esArchivable` **conserva** su significado original («lo que la máquina dio
  por bueno») y lo nuevo vive en `esCirculable`, que es exactamente lo que
  mantiene la distinción viva en el código y no solo en el CSS.

### 2.2 · La revocación ocurre **en la escritura**, no al leer — ✅

- `RepositorioPostgres.guardar_validacion` compone `upsert_validacion` **y**
  `revocar_aprobacion_si_cambio`, y las pasa a `_escribir(..., ademas=(...))`,
  que las ejecuta **en el mismo cursor y con un solo `commit`**. Leído el
  cuerpo de `_escribir`: no hay `commit` intermedio ni segunda transacción.
- El `UPDATE` lleva las dos condiciones que hacen falta:
  `revocada_at_utc IS NULL` (no machaca la fecha de la primera revocación) y
  `huella_aprobada <> %s` (distingue «cambió el veredicto» de «se volvió a
  subir la misma remesa», que es R32 y el criterio de aceptación «sobrevive a
  recargar»). **No borra** (R33) y el motivo es la etiqueta cerrada
  `veredicto_cambiado` (R34).
- **Búsqueda de caminos que se salten la revocación**: `guardar_validacion` es
  el **único** llamante de `upsert_validacion` en todo el servicio, y
  `paso_persistencia` es el único llamante de `guardar_validacion`. Los dos
  endpoints que llegan ahí —`/api/parte` y `/api/aprobar`— **recalculan
  siempre** el veredicto con `validar_parte` antes de guardar, así que
  `ctx.validacion` nunca llega `None` por esa vía y la revocación se evalúa en
  todos los guardados. `/api/validar` no persiste nada, luego no puede dejar
  una aprobación desacompasada de lo guardado.
- **El orden dentro de `/api/aprobar` es el correcto y está razonado**:
  `paso_persistencia` (parte → validación, que revoca) y **después**
  `guardar_aprobacion` (que resucita la fila poniendo las dos columnas de
  revocación a `NULL` **en el SQL**, no confiándolo al objeto). Al revés, la
  aprobación nacería revocada. Lo vigila
  `test_f026_r22_la_aprobacion_se_lee_despues_de_guardar`, cuya aserción es
  una **igualdad de lista completa**: `orden == ["parte", "validacion",
  "consulta_aprobacion"]`.

### 2.3 · El autoguardado mantiene el acoplamiento guardar↔revalidar — ✅

- `app.js::_guardarCorreccion` llama a `window.Pipeline.revalidarYGuardar`, la
  **misma** función del botón, no una ruta paralela.
- **Control negativo verificado**: `test_f026_r50_el_autoguardado_no_llama_a_guardar_por_su_cuenta`
  comprueba que la cadena `Pipeline.guardarParte` **no aparece** en `app.js`.
  Confirmado a mano con `grep` sobre `services/postventa-front/js/`: las
  únicas llamadas a `guardarParte` están dentro de `pipeline.js`, en
  `procesarParte` (que va inmediatamente después de `api.validar`) y en
  `revalidarYGuardar`. **No hay ningún camino que guarde sin revalidar.**
- `test_f026_r50_no_se_ha_inventado_ningun_estado_de_veredicto_obsoleto`
  cierra además la alternativa que `design.md` §15.1 descartó.
- R52 se sostiene: el aviso de fallo se pinta en recuadro rojo aparte, sin
  temporizador que lo borre, y `pendientes` no se tira en el `catch`, así que
  la siguiente pausa reintenta y lo escrito sigue en pantalla.

### 2.4 · Las correcciones no pisan el valor ni la confianza de la máquina — ✅ (con matiz, ver H-2)

`aplicarEdiciones` construye un objeto **nuevo** (`Object.assign({}, extraccion,
{campos})`) y no muta `parte.extraccion`, así que lo que leyó el modelo sigue
íntegro en memoria del front. Lo vigila
`test_f026_r53_el_front_no_escribe_nunca_sobre_la_extraccion`. El matiz —qué
pasa en la base— va en H-2, y no es un incumplimiento: es lo que `design.md`
§15.2 decidió.

### 2.5 · El identificador de quien aprueba es opaco — ✅

- **En la base**: `aprobado_por text NOT NULL` recibe `usuario_oid` tal cual,
  el `oid` opaco de Entra ID. La cabecera del `.sql` lo declara dato personal
  seudónimo, con el mismo tratamiento que `cierres.confirmado_por`.
- **En los logs**: barrido propio con `grep` sobre todo `services/postventa-api`
  buscando `usuario_oid|aprobado_por` dentro de llamadas `log.` →
  **cero coincidencias**. Los tres logs nuevos llevan `hash`, `destino`,
  `resultado` y `vigente`, nada más. `repositorio_pg::guardar_aprobacion` ni
  siquiera registra la huella.
- **En la respuesta HTTP**: `bloque_de_aprobacion` publica **cuatro** claves y
  ninguna es el `oid`.
- **En la pantalla**: `usuario.usuarioOid` aparece en `index.html` solo como
  condición (`:disabled`, `x-show`); nunca dentro de un `x-text`. Verificado a
  mano, y lo vigilan `test_f026_r38_la_pantalla_no_pinta_quien_aprobo` y
  `test_f026_r38_el_bloque_de_aprobacion_solo_usa_las_cuatro_claves_publicadas`.

### 2.6 · Qué se puede aprobar y qué no — ✅

La línea está donde dice la spec, **en el dominio y por motivo**:
`MOTIVOS_APROBABLES = (OBSERVACIONES_MANUSCRITAS, FIRMA_NO_HUMANA)` y
`es_aprobable` exige las tres condiciones (hay veredicto, no es apto, y
**todos** los motivos están en la lista).

Comprobado que la línea no se puede rodear: en `domain/models/validacion.py`,
`CAMPOS_DECISIVOS = ("codigo_obra", "numero_incidencia")` y `es_legible` exige
valor no vacío **y** confianza ≥ umbral, así que un parte sin número de
incidencia **siempre** emite `numero_incidencia_no_legible` y `es_aprobable`
devuelve falso. No es una política que se pueda ablandar desde el cuerpo de la
petición: R5 se cumple —`aprobar.py` recalcula el veredicto con `validar_parte`
y no mira ningún veredicto del cuerpo—, así que quien llame no puede
declararse aprobable.

El `CHECK (destino_aprobado IN ('cola_validacion_humana','revision_manual'))`
del DDL impide además registrar la aprobación de un `archivo_y_cierre` (R10).

### 2.7 · Las enmiendas — ✅

- **R36 de F-025**: el texto original **no se ha borrado** (sigue en su sitio,
  líneas 250-254 de `specs/F-025-confirmacion-unica/requirements.md`) y debajo
  entra un recuadro fechado **2026-09-12** que lo **cita literal**, dice qué
  cae (solo la última frase), qué sigue entero, y **quién lo decidió**: el
  responsable, el 2026-09-11, con sus palabras entrecomilladas.
- **La interpretación consta como tal**: el recuadro dice, con negrita,
  *«Que aprobar sea un acto explícito, con su botón, es interpretación del
  líder y no un pronunciamiento del responsable»*, y explica por qué lo que el
  responsable pidió («sin botón») era para otra cosa. Lo mismo en la tabla de
  P1 de `specs/F-026-aprobacion-humana/requirements.md`. **No hay ningún sitio
  donde el botón se atribuya al responsable.**
- **`docs/ARCHITECTURE.md`**: los **tres** puntos (paso 6, semántica 3,
  semántica 7) llevan su recuadro «Precisado por F-026 el 2026-09-12», los
  tres dicen que la puerta nueva es **más estrecha**, y **ninguno borra** el
  texto anterior.
- Lo vigilan los 21 tests de `tests/test_f026_documentacion.py`, escritos
  antes que los documentos (fase RED en §40 del informe).

### 2.8 · La campaña de mutación — ✅ verificada de forma independiente

**Recálculo puro, hecho por mí, no leído del informe:**

```
harness.alcance.alcance_de_feature("F-026", base="feature/F-025-confirmacion-unica")
  → ref_diff = (bb84d860…, feature/F-026-aprobacion-humana)   [coincide con el informe]
  → 16 ficheros, 1 315 líneas en alcance                      [coincide, fichero a fichero]
harness.mutacion.generar_mutantes sobre esos 16 ficheros
  → 35 mutantes                                               [coincide]
```

Los 16 recuentos por fichero coinciden uno a uno con la tabla de
`progress/mutacion_F-026.md` (285 en `aprobacion.py`, 231 en `aprobar.py`,
164 en `sentencias.py`, 117 en `cuerpos.py`…).

**El superviviente, comprobado a mano y no creído.** Es real: `generar_mutantes`
sobre `mapeo.py` produce exactamente un mutante, y es el que el informe
declara —misma línea (182), mismo operador (`booleano`), mismo texto
`ensure_ascii=False` → `ensure_ascii=True`—. Y la justificación de
equivalencia la he verificado **ejecutando el enum**, no leyéndola:

```
codigo_obra_no_legible True | numero_incidencia_no_legible True
firma_no_humana        True | observaciones_manuscritas    True   (isascii)
```

Los cuatro valores de `CodigoMotivo` son ASCII puro y
`json_de_codigos_de_motivo` no recibe otra cosa (`Aprobacion.motivos_aprobados`
está tipada `tuple[CodigoMotivo, ...]`), así que las dos formas producen el
mismo texto y **ningún test puede distinguirlas**. **Equivalencia aceptada.**
Ninguna sección queda en `PENDIENTE`.

**Campaña no reejecutada, y se dice por qué**: el «Tiempo total» que declara el
informe es **401,5 s (6 min 42 s)**, por encima del umbral de 5 minutos de
C4 bis, así que se aplica el recálculo puro y se declara explícitamente el
nivel de verificación aplicado. El árbol queda limpio (`git status` vacío).

**Coste por mutante** (C4 bis): 401,5 s × 8 workers ÷ 35 mutantes ≈ **91,8 s
por mutante**. La suite del servicio `api` tarda **65,3 s** en solitario
(medida por mí) y ~95 s dentro de `init.sh` con cobertura. El coste está **por
encima** del tiempo de la suite, no por debajo: la campaña tardó lo que tenía
que tardar y no hay indicio de caché envenenada. No procede el relanzamiento
con caché limpia.

---

## 3 · Hallazgos, por severidad

**Ninguno bloquea el cierre.** No hay hallazgos de severidad ALTA.

### H-1 · MEDIA · La huella no incluye el número de incidencia, y eso decide **qué reclamación se cierra**

`huella_de_veredicto` se calcula sobre destino + códigos de motivo + firma +
observaciones normalizadas. **Los valores de los campos no entran**, y
`design.md` §3 lo justifica así: *«el nombrado cambia si cambia el código de
obra, pero eso no es lo que se aprobó»*.

El razonamiento cubre `codigo_obra` —que decide la carpeta— pero **no examina
`numero_incidencia`**, que decide **sobre qué reclamación del ERP de
producción se escribe el cierre**. Camino concreto, que existe hoy:

1. un parte va a la cola por observaciones manuscritas, con
   `numero_incidencia = A`, legible y por encima del umbral;
2. una persona lo aprueba mirando el papel: se registra la huella H;
3. alguien corrige `numero_incidencia` a **B** (también legible) y revalida;
4. destino, motivos, firma y observaciones **no cambian** → la huella sigue
   siendo H → `revocar_aprobacion_si_cambio` **no revoca**;
5. `admite_circuito` solo compara el `destino`, que coincide → el parte
   circula y **cierra la reclamación B** con una aprobación dada sobre A.

Es coherente con la spec aprobada (R30 habla del **veredicto**, y el número de
incidencia no forma parte del veredicto), así que **no es un incumplimiento y
por eso no rechazo**. Pero sí contradice el espíritu de §12.1 («la aprobación
nunca inventa un dato») y merece decisión escrita.

**Acción propuesta (del líder, con el responsable):** o se añade
`numero_incidencia` —y, si se quiere, `codigo_obra`— a la cadena canónica de
`huella_de_veredicto` (cambio de una línea en
`services/postventa-api/domain/models/aprobacion.py`, más su test), o se
declara el riesgo por escrito en §12.1 de `design.md` con su razón. **No lo
arregle nadie sin decidirlo**: tocar la huella invalida las aprobaciones
existentes, y hoy no hay ninguna en producción, que es el mejor momento para
decidirlo.

### H-2 · BAJA · R53 solo se cumple en el front; en la base, la corrección **sí** pisa lo que leyó la IA

R53 dice que las correcciones no pisan el valor ni la confianza de la IA
porque *«F-015 los va a necesitar»*. En el front se cumple (§2.4). En la base
**no**: `upsert_parte` escribe todas las columnas de campos con
`_NO_SE_PISA_AL_REPROCESAR = {"hash_parte", "primera_vez_at_utc"}`, así que el
valor corregido y su `confianza_pct = 100` sustituyen lo que extrajo el modelo
en `postventa.partes`.

Es **deuda heredada de F-019**, no de F-026, y `design.md` §15.2 sitúa
deliberadamente la garantía en el front. Lo que F-026 cambia es la
**frecuencia**: hasta ahora ese pisado ocurría cuando alguien pulsaba
«Revalidar»; con el autoguardado ocurre cada 1 500 ms de pausa mientras se
escribe.

**Acción propuesta:** anotarlo como precondición de **F-015** —si el prompt se
va a evaluar contra lo que dijo el modelo, la lectura original tendrá que
guardarse en algún sitio, y hoy no está en la base—. No se arregla en F-026.

### H-3 · BAJA · R3 está cubierto, pero por un test que no lleva su nombre

R3 («corregir o revalidar no aprueba») no tiene ningún `test_f026_r3_*`, y
`grep` de `R3` en los tests de F-026 no devuelve nada. **Materialmente sí está
cubierto**, y de la forma más fuerte posible: la aserción
`assert repositorio.orden == ["parte", "validacion", "consulta_aprobacion"]`
de `test_f026_r22_la_aprobacion_se_lee_despues_de_guardar` es una igualdad de
lista completa, así que el día que `/api/parte` llamara a `guardar_aprobacion`
el test caería. Lo mismo en el front con
`test_f026_la_aprobacion_nace_vacia_y_no_se_inventa_ninguna`.

**Acción propuesta:** una línea en la docstring de ese test citando **R3**, o
renombrarlo. Es trazabilidad documental, no un hueco de verificación.

### H-4 · BAJA · Dos requisitos sin test que tampoco están en la tabla de excepciones

`requirements.md` cierra con *«Todo lo demás tiene test unitario»*, y hay dos
que no lo tienen y no figuran en la tabla:

- **R40** (el resumen final de la tanda sigue igual): es un «sin cambios» de
  F-025 y lo sostienen los tests de F-025, que están en verde. Aceptable.
- **R45** (ni variable de entorno, ni secreto, ni dependencia nueva):
  **verificado por mí en el diff** — `git diff` filtrado por
  `*requirements*.txt`, `*settings.py`, `*.env*` e `infra/` devuelve
  **vacío**. Cumplido, pero sin test que lo vigile.

**Acción propuesta:** añadir las dos filas a la tabla de trazabilidad de
`requirements.md` al cerrar, para que la frase «todo lo demás tiene test» siga
siendo verdad.

### H-5 · BAJA · Dos restos de estado en `progress/` y `tasks.md`

- `progress/current.md` sigue diciendo, en «Lo que falta para cerrar F-026»,
  que falta *«Bloque 7 (T24) · la campaña de mutación»*. La campaña **ya se
  lanzó** (commit `389edef`) y su informe está completo.
- En `specs/F-026-aprobacion-humana/tasks.md`, **T24 y T25 siguen sin marcar**
  aunque los dos están materialmente hechos: la campaña existe y
  `bash harness/init.sh` termina en verde (comprobado por mí, exit 0).

Son tareas del bloque 7, que es del líder. **Se marcan al cerrar**, no antes.

### H-6 · BAJA · Un aviso de `ruff` más (60 frente a 59)

El nuevo es un `I001` en `interface_adapters/api/aprobar.py`, del **mismo
tipo** que los otros 20 del servicio: el repositorio separa con línea en
blanco el grupo `interface_adapters`/`application` y `ruff`, sin
`known-first-party` configurado, lo considera desordenado. El implementer
siguió la convención del servicio en vez de dejar el fichero nuevo como
excepción, y lo declaró. `init.sh` lo trata como deuda previa y no bloquea.
Arreglarlo de verdad es una línea de configuración que afecta a los 21 a la
vez: decisión del líder, no de esta feature.

---

## 4 · Recorrido de `CHECKPOINTS.md`

### C1 — El arnés está completo y en verde

- [x] `bash harness/init.sh` termina con exit 0 — **ejecutado por mí**:
      `ENTORNO LISTO`, 62 tests en la raíz, `api` y `front` en verde,
      `PUERTA COBERTURA [OK]`.
- [x] Existen los siete ficheros obligatorios (los verifica el propio
      `init.sh`, todos en `[OK]`).

### C2 — El estado es coherente

- [x] Una sola feature `in_progress`: `['F-026']`. (`F-009` está `blocked`,
      que es un estado distinto y no lo impide; el aviso de `init.sh` es de
      antes de esta feature.)
- [x] Rama actual `feature/F-026-aprobacion-humana`, la de la feature en
      curso. No es `main` ni `dev`.
- [x] `progress/current.md` abre con el bloque de la sesión activa de F-026.
      **Observación escrita**: el fichero acumula 2 093 líneas con material
      operativo de F-005, F-009 y F-012 (guiones de verificación manual que
      siguen sirviendo). No es resto de una sesión a medias, es memoria
      declarada del proyecto, así que no lo cuento como checkbox vacío; sí
      arrastra el desfase de H-5.
- [x] Toda feature `done` tiene su resumen en `progress/history.md` (sin
      cambios en esta feature: F-026 no pasa a `done` aquí).

### C3 — El código respeta arquitectura y convenciones

- [x] **Hexagonal respetada.** `domain/models/aprobacion.py` importa
      `hashlib`, `dataclasses`, `datetime`, `enum` y `domain.models.validacion`
      — **nada de infraestructura, ni `psycopg`, ni HTTP**. El SQL vive en
      `infrastructure/persistencia/`, la traducción HTTP en
      `interface_adapters/api/`, la orquestación en
      `application/pipelines/`, y la ruta en `function_app.py`. Cada artefacto
      nuevo está en su capa.
- [x] Primera línea con la ruta relativa en los cinco ficheros nuevos
      (`aprobacion.py`, `aprobar.py`, `aprobacion_serializada.py`,
      `autoguardado.js`, `10_aprobaciones.sql`) — comprobado con `head -1`.
- [x] Sin `print()` de debug, sin `console.log`, sin TODO/FIXME, sin secretos
      ni correos hardcodeados. Barrido propio sobre las líneas `+` del diff de
      `services/`: cero coincidencias reales (las que salen son la palabra
      «todo» y «método» en castellano).
- [x] La unidad de trabajo es el **parte**: la aprobación se clava por
      `hash_parte`, PK y FK. Nada razona por PDF.
- [x] **Nada se archiva ni se cierra sin pasar las validaciones**: las tres
      puertas siguen ahí, ahora mirando dos cosas en vez de una, y la segunda
      es una decisión humana registrada. El `commit` contra Sigrid sigue
      exigiendo su dry-run: `paso_cierre` no cambia por debajo de
      `_exigir_admitido`.
- [x] **Lo manuscrito no se descarta**: R15 se cumple —la tabla de
      aprobaciones no copia ni una letra de la transcripción, solo un
      `sha256`—, y las observaciones siguen viviendo en `postventa.partes`.
      Ninguna marca simple pasa a contar como firma: `validacion.py` no se
      toca.
- [x] **Firmado no es conforme**: intacto, F-004 sin cambios.
- [x] **Reprocesar no duplica**: `upsert_aprobacion` es
      `INSERT … ON CONFLICT (hash_parte) DO UPDATE`, una fila por parte (R17).
- [x] Nada hardcodea un número de estado de Sigrid: F-026 no toca
      `domain/models/cierre.py` ni `infrastructure/sigrid/` (R42, control
      negativo verificado en el diff).
- [x] Ningún PDF ni parte escaneado ha entrado en git:
      `git log --diff-filter=A` sobre el rango de la rama → **cero** ficheros
      `.pdf` y cero rutas de `muestras/`.

### C3 bis — Documentos que entran de fuera

**N/A, justificado:** F-026 **no añade ni modifica ningún fichero de
`docs/referencia/`**. Comprobado en el diff completo: los únicos documentos
tocados son `docs/ARCHITECTURE.md` y `docs/INTEGRACION.md`, que son documentos
propios del proyecto y no material convertido de un original externo. No hay
PDF ni ofimática que barrer.

### C4 — La verificación es real

- [x] **Requisitos con test trazable.** Recorridos los 55 requisitos: hay
      tests `test_f026_rN_*` para R2, R4–R18, R20–R25, R29–R39, R44, R46, R47
      y R50–R55, más los de JS (`R4, R5, R6, R8, R9, R10, R13, R19, R22, R23,
      R25, R26, R27, R29, R31, R36, R50–R55`). R1, R28, R43 y R48 están
      cubiertos por tests cuya docstring los cita. R3 está cubierto
      materialmente (ver **H-3**). R12/R16/R17 en ejecución real, R23/R26
      extremo a extremo, R41, R42, R47 y R49 tienen su justificación en la
      tabla de trazabilidad de la spec. Quedan R40 y R45 como **H-4**, los dos
      verificados por otra vía. **Todos los tests pasan**: 2 338 pasan y 13 se
      saltan en `api` (ejecución fresca por mí, 65,3 s), 62 en la raíz, 224 en
      `front` y **292 en JavaScript** (`node --test "tests_js/*.test.js"`,
      ejecutado por mí).
- [x] **Los unit tests no tocan red ni BBDD.** Los 13 `skipped` son todos
      ajenos a F-026 (suite de BBDD sin `POSTVENTA_PG_TEST_DSN` y dos de
      F-010). Los tests de F-026 usan dobles en memoria (`utiles_pg.py`,
      `RepositorioEnMemoria`) y el DDL se comprueba **por su texto**, no
      aplicándolo.
- [x] **Verificaciones `MANUAL (humano)` listadas con su comando exacto.**
      T20–T23 están en `specs/F-026-aprobacion-humana/tasks.md` con su
      `SELECT` literal y sus pasos, y `progress/current.md` las declara
      pendientes remitiendo al bloque 6. **Matiz escrito**: el precedente de
      F-009 en este repositorio es copiar el comando exacto **dentro de**
      `current.md`; aquí vive en `tasks.md`. Lo cuento cumplido porque el
      comando exacto existe, está versionado y está enlazado, pero el líder
      debería trasladarlo a `current.md` al cerrar (§5).

### C4 bis — El rigor declarado se cumple

- [x] `rigor` declarado y válido: **`estandar`**.
- [x] **Fase RED** con **salida real pegada**, no con una frase. Verificadas
      las trazas de §5.1, §5.2, §5.3, §11, §12, §13, §14, §24 y §40 del
      informe: llevan `FAILED …`, `AssertionError`, `AttributeError` y el
      recuento (`10 failed, 24 passed in 1.50s`). La más elocuente es la de
      T8, donde el rojo que importa no es el `AttributeError` sino
      `assert 0 == 1` sobre `veces_con('UPDATE postventa.aprobaciones')`: eso
      demuestra que **antes del cambio la revocación no ocurría**. El informe
      **declara además dónde no hubo RED** (TA2, TA4, TA5, por ser controles
      negativos) en vez de inventarse un rojo, y cuenta un test que pasaba sin
      comprobar nada por un `\b` mal escapado. Eso es honestidad de informe,
      no un hueco.
- [x] **Cobertura**: `PUERTA COBERTURA [OK]` — **99,0 %** de 1 338 líneas
      cambiadas (1 325/1 338), umbral 80 %, nivel `estandar`.
- [x] **Mutación**: existe `progress/mutacion_F-026.md`, generado por la
      herramienta, con totales **verificados de forma independiente** por mí
      (alcance y nº de mutantes recalculados: 1 315 líneas y 35 mutantes,
      coincidencia exacta fichero a fichero). Ver §2.8.
- [x] **Los muertos, comprobados**: «Tiempo total» **401,5 s > 5 min**, así
      que se aplica el recálculo puro y **se declara explícitamente**
      (campaña **no** reejecutada: 6 min 42 s según el informe). Árbol limpio.
- [x] **La campaña tardó lo que tenía que tardar**: 401,5 × 8 ÷ 35 ≈ **91,8 s
      por mutante**, por encima de los 65,3 s que tarda la suite del servicio
      en solitario. No es sospechosa por construcción; no procede relanzar con
      caché limpia.
- [x] **El único superviviente tiene su análisis completado** (ninguno en
      `PENDIENTE`) y la equivalencia la he **verificado yo** ejecutando el
      enum. Nivel `estandar` → no exige cero supervivientes.
- [x] **Sección «Evidencias»** con los cuatro números: está, y **cinco veces**
      —§8, §17, §27, §34 y §43—, una por bloque, con tests, cobertura,
      mutantes y tiempo de suite. **El nº de workers** consta en
      `progress/mutacion_F-026.md` (cabecera con el comando `--workers 8` y
      fila «Workers | 8» en Totales), que es donde vive la campaña real; las
      tandas intermedias declaran expresamente que no lanzaron ninguna. Es
      suficiente para calcular el coste por mutante, que es para lo que
      C4 bis lo pide.
- [x] Ningún punto de este bloque marcado N/A.

### C4 ter — Verificaciones extra por rutas sensibles

**N/A, y no hay nada que justificar**: `harness/rutas_sensibles.json` **no
existe** en este repositorio, que es el caso mayoritario que el propio
checkpoint declara N/A por configuración. `init.sh` no señaló ninguna ruta
sensible tocada.

### C5 — La sesión se cerró bien

- [x] **Un commit `F-026 Tn: …` por tarea.** Verificados en `git log`: T1,
      T2–T4, T5, T6, T7, T8, T9, T10, T11, T12, T13, T14, T15, T16, T17, T18,
      T19 y TA1–TA5, más los informes. 24 de 30 tareas marcadas `[x]`.
- [x] **Sin ficheros temporales ni artefactos sin trackear**: `git status`
      **vacío** en `postventa-incidencias` y **vacío** en `azure-apps`. La
      verificación de mutación que hice es cálculo puro y no escribió nada.
- [x] `features.json` refleja el estado real: `in_progress`. **No lo he
      tocado**: el veredicto lo aplica el líder.
- [ ] **Las seis tareas sin marcar.** T20–T23 son del **bloque 6 (responsable)**
      y T24–T25 del **bloque 7 (líder)**: por encargo explícito quedan
      pendientes y **no son reparos**. De ellas, T24 y T25 están materialmente
      hechas y solo falta marcarlas (**H-5**).

Sin el descuento del encargo, ese último checkbox estaría vacío y el veredicto
sería CHANGES_REQUESTED. Con él —y está por escrito en el encargo de esta
review— **C5 queda pendiente de cierre, no incumplido**.

---

## 5 · Lo que queda para el responsable y para el líder

### Para el responsable · bloque 6, `MANUAL (humano)`, contra la base de desarrollo

Los comandos exactos están en `specs/F-026-aprobacion-humana/tasks.md`,
T20–T23. En resumen:

1. **T20** · aplicar el DDL **dos veces seguidas** y comprobar que la segunda
   no falla, y que `information_schema.columns` devuelve las nueve columnas de
   `postventa.aprobaciones`.
2. **T21** · el circuito completo de un parte aprobado, **con autorización
   expresa para esa incidencia** y una sola confirmación de tanda.
3. **T22** · la consulta de auditoría de R41 (**solo lectura**), cruzando
   `aprobaciones` con `cierres` y `graficos` por `hash_parte`. El `oid` **no
   se copia a `progress/`**: se anota que existe, no su valor.
4. **T23** · la revocación sobre datos reales: corregir, revalidar, y
   comprobar `revocada_at_utc` relleno y `revocada_motivo = veredicto_cambiado`.

Y además, **nadie ha visto todavía esta pantalla en un navegador**: el botón,
la marca con anillo, el texto de origen y fecha, y los tres estados del
autoguardado están probados por texto y por lógica, no a ojo.

### Decisión que le corresponde al responsable

**H-1**: ¿una aprobación debe sobrevivir a que se cambie el **número de
incidencia** del parte aprobado? Hoy sobrevive. Es el momento barato de
decidirlo, porque todavía no hay ninguna aprobación en producción.

### Para el líder · bloque 7

1. Marcar **T24** y **T25** en `tasks.md` (los dos están hechos: la campaña
   existe y `init.sh` está en verde).
2. Corregir en `progress/current.md` la línea que aún dice que falta la
   campaña de mutación (**H-5**).
3. Trasladar los comandos de T20–T23 a `progress/current.md` con el formato de
   F-009 (**C4**, matiz).
4. Añadir R40 y R45 a la tabla de trazabilidad de `requirements.md` (**H-4**)
   y citar R3 en la docstring del test que lo cubre (**H-3**).
5. Decidir qué hacer con el `I001` de `ruff` (**H-6**): o se configura
   `known-first-party` para los 21 avisos a la vez, o se deja como deuda
   declarada.
6. `harness/features.json` a `done` **solo** después del bloque 6.

---

## 6 · Propuesta de mejora del arnés (no aplicada)

Para `.claude/agents/reviewer.md` y `CHECKPOINTS.md`, a valorar por el humano:

**C4 bis pide el nº de workers «en Evidencias» del informe del implementer.**
En esta feature la campaña la lanzó el **líder** (bloque 7), no el implementer,
y el dato vive donde tiene que vivir: en la cabecera y en la tabla de Totales
de `progress/mutacion_F-XXX.md`, que es el fichero que la herramienta genera.
Exigirlo en «Evidencias» del implementer obliga a duplicarlo o a declararlo
ausente cuando la campaña no es suya.

**Redacción propuesta**: *«el nº de workers consta en `progress/mutacion_F-XXX.md`
(cabecera del comando y fila de Totales) o, si la campaña la lanzó el
implementer, en su sección «Evidencias». Basta con uno de los dos.»*
