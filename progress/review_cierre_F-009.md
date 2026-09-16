<!-- progress/review_cierre_F-009.md -->
# Review · CIERRE DOCUMENTAL de F-009 (2026-09-16)

- **Veredicto: APROBADO**
- **Rama revisada**: `feature/F-009-cierre-sigrid`, seis commits sobre `dev`
  (`83f66a6`), árbol limpio, sin `push` ni merge.
- **Qué se revisa**: un **cierre documental**, no una implementación. El diff
  **no toca `services/`** — comprobado, y era una prohibición del encargo.
- **Informe revisado**: `progress/impl_cierre_F-009_20260916.md`.
- **Nivel de rigor**: **`critico`**, declarado en `harness/features.json`.
  Exige C1–C5, C3 bis, C4 bis (fase RED, cobertura, mutación con cero
  supervivientes salvo justificación aceptada) y las verificaciones
  `MANUAL (humano)` listadas con su comando exacto y su resultado real.

> **Lo que este veredicto NO dice.** No dice que F-009 esté verificada de
> extremo a extremo: **no lo está**, y quedan **cinco huecos vivos**. Dice que
> el cierre con esos huecos está **escrito, completo, fechado y sin maquillar**,
> que es exactamente lo que el responsable ordenó el 2026-09-16 y lo único que
> aquí se juzga.

---

## 1 · Lo más importante: ¿es honesto el cierre?

**Sí.** Recorrido uno a uno, contra los cinco sitios donde tenía que constar
(`progress/cierre_F-009.md` §3, `specs/F-009-cierre-sigrid/tasks.md`,
`harness/features.json`, `progress/current.md` y `progress/history.md`).

| Hueco | Requisito | ¿Escrito, con motivo, sin suavizar? |
|---|---|---|
| 1 · **T22 pasos 2 y 5** — el `503` con la ventana cerrada; que el dry-run no escribe | R37, R49 / R8, R10 | **[x]** En los cinco sitios. El motivo distingue las dos mitades: el `503` «sale gratis pero nadie lo ha pedido»; «no escribe» **exige foto antes/después con la ventana abierta** |
| 2 · **T22 paso 4** — las seis comprobaciones de R9 + el bloque `grafico` | R9, R49 | **[x]** Y con la consecuencia que lo hace difícil: desde F-025 **la única vía es la consola**, porque el front ya no pide dry-run por sí solo |
| 3 · **T23** — `COUNT` en `dbo.usu` (R34), R33, login inexistente → `409` sin tocar Sigrid (R31) | R34, R33, R31 | **[x]** Y **no se maquilla lo acreditado**: dice que el `usu` `pgris` prueba R30–R32 «en lo sustantivo» y que **eso no prueba R33, ni el `409`, ni la unicidad**. Añade el bloqueo por script roto |
| 4 · **T27** — reintento → `ya_cerrada` | R18, R42 | **[x]** Consta **literalmente** como «el ÚNICO criterio de aceptación de la ficha que ningún cierre real ha ejercido», en el acta §3, en `tasks.md`, en la ficha, en `current.md` y en `history.md`. Y va más lejos: «acreditado solo por tests», «el escenario más probable en uso normal», y que **las cuatro features que pasaron por delante lo dejaron sin marcar** |
| 5 · **R22** — `filas_afectadas: 2`, `MAX(ide)`/`tiemod` de partida | R22, T24 pasos 2/5/8 | **[x]** Consta **NO RECUPERABLE HACIA ATRÁS** en los cinco sitios, con el porqué exacto —«la foto que faltaba era la de **antes**»— y el dato que lo remata: `con.tiemod` vale hoy `46275.647118` y «ese número no compara con nada» |

**T24, paso a paso.** El contrato son nueve pasos. `tasks.md` dice
«**Lo que falta**: los pasos **2, 3, 4, 5 y 8**» — coincide con el encargo. Y lo
acreditado lo está **con fecha y fuente**, sin redondear al alza:

- paso **4 en parte** — «solo el `HTTP 200` del `commit` de `08:28:12` UTC del
  2026-09-11, **no el estado "cerrado" del cuerpo**». Esa distinción es la
  prueba de que aquí no se está inflando nada.
- pasos **6, 7 y 9** — sesión de solo lectura del **2026-09-15**, scripts `09_`,
  `10_`, `11_` y `12_`, los cuatro `PASA`; R1, R24, R25, R41, R43.
- **T25** (2026-09-15, `11_trazabilidad_tex_sigrid.ps1` → `PASA`) y **T26**
  (2026-09-11, acreditada el 14): marcadas con su fecha y su fuente.

**Nada marcado como hecho sin estarlo.** `specs/F-009-cierre-sigrid/tasks.md`:
**25 casillas `[x]`, 4 `[ ]`**, y las cuatro vacías son **exactamente T22, T23,
T24 y T27** (líneas 301, 336, 364, 446), cada una con su bloque «NO RECORRIDA
(constancia del 2026-09-16)». **Ninguna casilla se marcó en este trabajo.**

---

## 2 · Nada derogado se ha borrado: se ha enmendado

Las tres derogaciones que el encargo señalaba, comprobadas en el diff:

1. **Criterio de aceptación 3 de F-009** (`harness/features.json`). Conserva la
   premisa **literal** entrecomillada —«El dry-run se muestra al usuario antes
   de cerrar: qué incidencia y de qué estado a cuál pasaría»—, con **fecha**
   (2026-09-11), **quién** (decisión del humano, vía F-025, R38–R41) y la
   precisión que importa y que el encargo exigía: **«LO QUE DESAPARECE ES LA
   PANTALLA, NO LA VERIFICACIÓN PREVIA DEL BACKEND»**. **[x]**
2. **R21 derogado por R48 de F-012** (2026-09-06). En la enmienda (b) de T22 de
   `tasks.md`, con el texto original intacto encima y el remate útil: «un
   dry-run que aún trajera aquel aviso significaría que el despliegue no lleva
   F-012». **[x]**
3. **La obra 404 / Mirasierra**, derogada el **2026-09-10** en favor de la
   **`0626`**. Enmienda (a) de T22, citando la premisa anterior literal («toda
   escritura de prueba cae en la obra de prueba 404», 2026-09-06), quién la
   levantó y dónde consta (`progress/guion_bloque9_F-012.md`). Y añade lo que
   evita un accidente: **«Mirasierra sigue fuera: nadie ha autorizado cerrar una
   incidencia del piloto»**. **[x]**

Además, **el `blocked_by` retirado se cita literal** en la `description` antes
de darlo por desfasado, con las **cuatro** razones por las que ya no vale. Eso
es enmendar, no borrar. **[x]**

Mismo criterio en el guion: §4(a) y la tabla de ocho huecos de §9.4 **se
conservan enteros** con un aviso delante, en vez de reescribirse.

---

## 3 · Las dos afirmaciones del implementer, contrastadas

### 3.1 · El cabo del «ni un cierre real» estaba en dos ficheros — CIERTO

- `docs/INTEGRACION.md` línea 644 y `azure-apps/postventa_incidencias.md` línea
  737: los dos llevan la sección **«Lo que YA se ha ejecutado contra el ERP»**,
  los dos corrigen expresamente el «todavía no se ha ejecutado ni un cierre
  real» y el «obra de prueba 404», y los dos listan **los dos cierres** con
  `ide` 8457839 / 8467000 y el veredicto del huso. **Coherentes entre sí.**

**Sobre `azure-apps`, que es repositorio AJENO: este encargo NO lo tocó, y está
bien que no lo tocara.**

- `git -C ../azure-apps status --short` → **limpio**.
- Sus tres commits de hoy son **anteriores a este encargo** (`d2292df` 00:33,
  `cc28c24` 01:13, `6bb162c` 04:46) y pertenecen al trabajo de F-028 y a la
  corrección previa. **Ninguno sale de esta rama.**
- **Estaba justificado** que se corrigiera entonces: la regla de `CLAUDE.md`
  obliga a actualizar el documento cuando cambia lo que el proyecto expone o
  consume, y el documento **afirmaba algo falso** desde el 2026-09-11.
- **Y quedó coherente**: `cc28c24` repuso la frase «Sigrid no se toca» que se
  había caído al reescribir el apartado, **porque un test de este repositorio la
  exige** (R26 de F-010, `tests/test_f010_integracion_expuesto.py`) y se puso en
  rojo. Se repuso la frase en vez de aflojar el test. Correcto.
- Este cierre **no cambia nada de lo que el proyecto expone o consume**, así que
  **no tocar `azure-apps` es la conducta debida**, no una omisión.

> **Matiz de redacción, no defecto.** El §5.1 del informe dice «**Los dos están
> corregidos**», que puede leerse como acción propia. No lo fue: ya lo estaban.
> El §10 lo aclara sin ambigüedad («No se tocó `azure-apps/`»). Se deja anotado
> para quien lea solo el §5.1.

### 3.2 · La verificación 6 de F-028 no acredita T27 — CIERTO

Verificado en `specs/F-028-estado-del-parte/tasks.md`, en la nota de resultado
de T27, que dice literalmente que la 6 «se probó sobre `RS26.09/0150`, que **ya
estaba cerrada** desde el 2026-09-11, y **las dos ventanas de escritura estaban
cerradas**», y que «el cierre real con espacios **sigue sin ejecutarse**».

El §11.2 del guion lo recoge correctamente y **añade el dato que la fuente no
deletrea**: con `CIERRE_HABILITADO` en `false` la respuesta es **`503` antes de
tocar el ERP** (§0.1), **no `ya_cerrada`** — luego R18 y R42 siguen sin
ejercerse y **el hueco 4 queda intacto**. El §11.2 también distingue, como la
fuente, que las verificaciones **3, 4, 5 y 6 están declaradas, no medidas**.
**El implementer corrigió bien el encargo.**

---

## 4 · La ficha, el backlog y F-029

- **`status: "done"`** en F-009. **[x]**
- **Dónde va la constancia.** Leído `harness/backlog.py`: `construir()` proyecta
  **`id`, `title`, `priority`, `status`, `rigor`, `sdd`, `branch` y
  `description`** — y nada más. **`blocked_by` y `acceptance` no llegan nunca a
  `BACKLOG.md`.** La decisión de meter la constancia en `description` **está
  bien fundada y confirmada leyendo el generador**: en `blocked_by` los cinco
  huecos habrían quedado invisibles en el fichero que `CLAUDE.md` manda leer en
  vez del JSON. **[x]**
- **`BACKLOG.md` regenerado, no editado a mano**: `bash harness/init.sh` da
  `[OK] BACKLOG.md al día`, que es `backlog.py --comprobar` en verde — la prueba
  automática de que el Markdown es función pura del JSON. **[x]**
- **F-029, el id**: el máximo en el JSON es F-028 → **F-029 libre**. Comprobado
  que **F-023 está usada aunque no esté en el JSON** (cancelada el 2026-09-06,
  entrada en `progress/history.md` línea 701 con su JSON completo) y que **F-022
  existe**. **No se reutilizó ninguna**, que era la trampa de la colisión del
  2026-09-15. **[x]**
- **F-029, la descripción**: dice **qué** está roto (la invocación
  `& $python -c ...` y el entrecomillado que PowerShell 5.1 destroza), **dónde**
  (`07_alta_usuario_sigrid.ps1` líneas **161** y **248**;
  `17_traza_grafico_local.ps1` línea **196**) y **cuál es el arreglo conocido**
  (`Invoke-PythonDelServicio`, en `infra/08_lectura_sigrid_comun.ps1`, el mismo
  que arregló al `12_`). Los tres datos que pedía el encargo. **[x]**
  Añade dos aciertos: exige **ejecutar** los scripts («arreglarlos sin lanzarlos
  no cierra esta feature»), que es la lección del §10.2 del guion; y avisa de
  que cobertura y mutación **solo miden Python**, así que aquí no valen como
  evidencia. `rigor: estandar` es el correcto — `documental` está definido como
  «ni código ni SQL» y esto cambia código.

---

## 5 · Coherencia documental

| Dónde | Qué pedía el encargo | Resultado |
|---|---|---|
| `progress/current.md` | sin cabos falsos | **[x]** Bloque nuevo al frente; el «PARA RETOMAR» del 15 marcado **SUPERADO** con **las tres cosas suyas que ya no son verdad** enumeradas. Los cabos que quedan son los de verdad: la petición a Posventa sin enviar, F-029 y los 61 avisos de `ruff` |
| `progress/history.md` | entrada fechada | **[x]** Entrada de F-009 al final (append-only), con la decisión literal, los dos cierres, los cinco huecos, las dos derogaciones y la deuda |
| Guion §4(a) | el dry-run de tanda que F-025 eliminó | **[x]** Marcado **DESFASADO** sin borrar, con la consecuencia operativa: «la única vía que queda para leer un dry-run es la consola» |
| Guion §9.4 | cinco huecos, no ocho | **[x]** Aviso delante de la tabla del 14, que se conserva |
| Guion §0.2 | el huso, descartado con dato | **[x]** `HORA LOCAL (correcto)`, **0,0 min**, y **dos** observaciones independientes |
| Guion §11.1 | acta del segundo cierre real | **[x]** `RS26.09/0149`, `ide` 8467000, `14:30:05` hora local, con **lo que aporta y lo que no** |
| Guion §11.3 | precondición que aporta F-028 | **[x]** El front solo compone el cierre si el parte consta `aprobado`; la P5 decía solo «archivado» y **ya no basta** |
| Guion §11.4 | el histórico no es la fuente | **[x]** «Las fuentes son `postventa.cierres` y la fila de `dbo.log`», con el caso real que lo destapó |

**Contrastado contra el código** (solo lectura): `pedirDryRunCierre` **no existe
ya** en `services/postventa-front/js/` —solo sobrevive en
`tests/test_f025_front.py` como vigilancia de que no vuelva—, y
`pipeline.js::esCirculable` (381) es `estadoDe(parte) === ESTADO_APROBADO`,
exigido por `esCerrable` (489) y por `cuerpoDeCierre` (519), que **lanza** si no
se cumple. Las dos afirmaciones del guion son ciertas.

> **Precisión menor, para el acta.** `esCerrable` exige **además**
> `parte.validacion.veredicto`, que ni el §4 del informe ni el §11.3 del guion
> mencionan. No falsea nada —la afirmación sustantiva («exige `aprobado`») es
> correcta—, pero quien use el §11.3 como lista de precondiciones se dejaría
> una.

---

## 6 · `bash harness/init.sh`

Ejecutado **tal cual, sin pipes ni `tail`**. **Verde**, exit 0:

```
[OK] Arnés v1.5.2 (2026-08-18)
     28 features, 13 abiertas, en curso: ninguna, bloqueadas: ninguna
[OK] features.json válido
[OK] BACKLOG.md al día
[AVISO] ruff: 61 avisos (deuda previa, no bloquea)
62 passed in 4.50s
[OK] pytest en verde (con medición de cobertura)
[OK] servicio api / servicio front: pytest en verde (caché: árbol sin cambios)
[OK] PUERTA COBERTURA: N/A (F-009 no cambia líneas Python de producción frente a dev)
[OK] Rama actual: feature/F-009-cierre-sigrid
ENTORNO LISTO. Puedes trabajar.
```

`git status` **limpio** después de ejecutarlo.

---

## 7 · Recorrido de `CHECKPOINTS.md` (rigor `critico`)

### C1 — El arnés está completo y en verde

- [x] `init.sh` termina con exit code 0.
- [x] Existen los nueve ficheros exigidos (los verifica el propio portero).

### C2 — El estado es coherente

- [x] **Cero** features en `in_progress`.
- [x] Rama `feature/F-009-cierre-sigrid`, la de la feature. No es `main`.
- [~] **`current.md` describe solo la sesión activa** — literalmente **no**:
      conserva bloques de sesiones anteriores. **No lo cuento como vacío**
      porque (a) es una desviación **preexistente y deliberada** de este
      repositorio, no introducida aquí, y (b) este trabajo **la mejora**: marcó
      el bloque del 15 como SUPERADO enumerando qué dejó de ser verdad, en vez
      de dejarlo como cabo falso. **Queda anotado para el humano**, no como
      defecto de este encargo.
- [x] F-009 `done` **tiene** su resumen en `history.md`, fechado.

### C3 — El código respeta arquitectura y convenciones

- [x] **No se tocó `services/`** — confirmado en el diff: los ocho ficheros son
      `BACKLOG.md`, `harness/features.json`, cuatro de `progress/` y `tasks.md`.
      Los puntos de arquitectura hexagonal, dry-run, manuscrito, reproceso y
      `conest` son **N/A por ausencia de cambio de código**, y lo que ya estaba
      lo aprobó `review2_F-009.md`.
- [x] Primera línea con la ruta en los **dos** ficheros nuevos
      (`progress/cierre_F-009.md`, `progress/impl_cierre_F-009_20260916.md`).
- [x] Todo en español. Sin secretos, sin prints de debug, sin dependencias
      nuevas.
- [x] **Ningún PDF ni parte escaneado ha entrado**:
      `git log --diff-filter=A dev..HEAD` da **exactamente esos dos `.md`**.

### C3 bis — Los documentos que entran de fuera son seguros

**N/A justificado**: el diff **no añade ni modifica nada en `docs/referencia/`**.

Aun así se ejecutó el **barrido de datos sensibles** sobre el diff completo, que
es lo que este bloque protege. Patrones usados: correos
`[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}`; IPv4; GUID de suscripción o tenant
`[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}`;
`password|passwd|contrasen|secret|api[_-]?key`; `BEGIN ... PRIVATE KEY`;
`Bearer `; `AccountKey=`; `DefaultEndpointsProtocol`. **Cero coincidencias.**

Lo que sí aparece —`pgris` como login del ERP, los códigos `RS26.09/0149` y
`/0150`, los `ide` 8457839 y 8467000— es dato de negocio ya versionado y
necesario para la trazabilidad; no es secreto ni dato personal de cliente.

### C4 — La verificación es real

- [x] **R1–R52 tienen test trazable** (`test_f009_rN_*`) y **62 tests pasan**.
      Comprobado por barrido de nombres, no fiándome del informe.
- [ ] **R53 no tiene test trazable ni fila en la tabla de trazabilidad** de
      `requirements.md`. **Es la deuda ya conocida de `review2_F-009.md` §7**,
      que el encargo excluye expresamente como motivo de rechazo. **Sigue
      viva** — ver §8.
- [x] Los unit tests no tocan red ni BBDD (lo vigila
      `test_f009_arquitectura.py`, ya aprobado).
- [x] **Las verificaciones `MANUAL (humano)` están listadas** en `current.md`
      con su comando y su estado, y en `tasks.md` con su motivo. Es justamente
      el contenido de este cierre.

### C4 bis — El rigor declarado se cumple

- [x] La feature declara `rigor: "critico"`, valor válido.
- [x] **Fase RED — N/A, justificado por escrito**: este encargo **no escribe ni
      una línea de código de producción ni de test**. No hay código cuyo fallo
      previo enseñar, y tampoco es el caso del «entregable es el propio test».
      **La justificación es la naturaleza del cambio, no la omisión de la
      herramienta.** La fase RED del código de F-009 la revisó y aprobó
      `review2_F-009.md`.
- [x] **Cobertura — N/A con el motivo impreso por el portero**, que es
      exactamente la vía que `CHECKPOINTS.md` admite:
      `PUERTA COBERTURA: N/A (F-009 no cambia líneas Python de producción frente a dev)`.
- [x] **Mutación — existe `progress/mutacion_F-009.md`, y lo he verificado de
      forma independiente, no me he creído el informe.** Recálculo puro, sin
      ejecutar la suite y sin tocar el árbol:
      - **Alcance**: `harness.alcance.parsear_diff` + `filtrar_produccion` sobre
        `6cabd39..457b68b` → **17 ficheros, 3.024 líneas**. El informe declara
        **17 ficheros y 3.024**. **Coincide exacto.**
      - **Nº de mutantes**: `harness.mutacion.generar_mutantes` sobre el
        contenido de cada fichero **en ese commit** (vía `git show`) → **123**.
        El informe declara **123 generados / 123 evaluados**. **Coincide
        exacto.**
      - **Muestreo de supervivientes**: cuatro de los seis
        (`cliente.py:347`, `escrituras.py:217`, `fabrica.py:130`,
        `cerrar.py:219`) **existen como mutantes reales**, con el **mismo
        operador** (`booleano`, `logico`, `logico`, `entero`) y el **mismo texto
        original→mutado** que declara el informe. No es un informe escrito a
        mano.
- [x] **Los muertos: campaña NO reejecutada, y lo digo explícitamente.** El
      «Tiempo total» declarado es **6.124,7 s (102 min)**, muy por encima del
      umbral de 5 minutos, así que `CHECKPOINTS.md` admite quedarse en el
      recálculo puro. **No hay cero mutantes**, luego la prueba de control del
      cero no aplica.
- [x] **La campaña tardó lo que tenía que tardar.** `tasks.md` T28 declara
      **workers 1 (campaña en serie)**, con su motivo (con 8 y con 16 la máquina
      satura y el veredicto `timeout` sale por carga). Coste por mutante =
      6.124,7 × 1 ÷ 123 = **49,8 s**, **por encima** de los ~38,7 s que tarda la
      suite del servicio `api`. **Sano**: no es una campaña que no estuviera
      ejecutando los tests.
      > El informe generado **no trae la línea de workers** porque es del
      > 2026-09-02 14:05 y la mejora del arnés que la añade (`e48b318`) es de
      > las 14:23 del mismo día. El dato **consta por escrito en T28 y en el
      > mensaje del commit `457b68b`**. Queda cubierto.
- [x] **Cero análisis en `PENDIENTE`** (verificado: 0 ocurrencias). Los **6
      supervivientes** están **justificados por escrito y aceptados por el
      humano**: tres aceptados como riesgo el **2026-08-26** (`cliente.py:347`,
      `consultas.py:202` y `:207`) y tres equivalentes. Es la vía que el nivel
      `critico` admite.
- [x] El informe del implementer trae la sección **«Evidencias»** (§8) con los
      cuatro números: **62 pasados / 0 fallos**, cobertura **N/A con motivo**,
      mutación **123 / 117 / 6 / 0 timeouts**, suite **4,80 s**.
- [x] Ningún punto de este bloque marcado N/A sin justificación escrita.

### C4 ter — Las verificaciones extra por rutas sensibles

**N/A sin justificación necesaria**: `harness/rutas_sensibles.json` **no existe**
en este repositorio (solo el `.ejemplo.json`), que es el caso mayoritario que el
propio bloque declara N/A. `init.sh` no señaló ninguna ruta tocada.

### C5 — La sesión se cerró bien

- [~] **`tasks.md` con todas las tareas `[x]`** — **no se cumple, y es por
      diseño**: **T22, T23, T24 y T27 quedan `[ ]`** deliberadamente. **No lo
      cuento como checkbox vacío** porque el encargo lo excluye expresamente y
      porque la decisión del responsable del 2026-09-16 está **escrita, fechada
      y firmada** en cinco sitios. **Marcarlas habría sido el motivo de rechazo;
      dejarlas vacías con constancia es el acierto de este trabajo.** Ver §9.
- [~] **Un commit `F-009 Tn: ...` por tarea** — los seis commits son
      `F-009 cierre: ...`. **Justificado**: no se ejecutó ninguna tarea, se
      cerró la feature; no hay `Tn` que citar. Los mensajes son descriptivos y
      en español.
- [x] Sin ficheros temporales ni artefactos sin trackear: `git status` limpio.
- [x] **`features.json` refleja el estado real**: `done`, con los cinco huecos
      dentro y el `blocked_by` derogado con su cita literal.

---

## 8 · Deuda anotada, que NO se usa para rechazar

Verificada una a una, como pedía el encargo:

1. **R53 sigue sin fila en la tabla de trazabilidad de `requirements.md` y sin
   test trazable** (`requirements.md` línea 317; barrido de `test_f009_r53`
   vacío). **Sigue viva.**
2. **`Reclamacion.estado_destino_est`** — hoy es `estado_destino_est: int` en
   `services/postventa-api/domain/models/cierre.py:147`, **no `int | None`**.
   Este punto de la deuda **parece resuelto o superado**; conviene que el humano
   lo confirme y lo tache de la lista, porque arrastrar como abierto algo que ya
   no lo está hace el mismo daño que este cierre viene a evitar.
3. **`azure-apps/sigrid_api.md`**: la tabla de consumidores y los tres detalles
   de la primera review (enlaces cruzados, `REQUIRE_WHERE_ON_UPDATE_DELETE`).
   **No se comprobó en este encargo** y **no se tocó `azure-apps`**: queda como
   estaba.
4. **61 avisos de `ruff`**, deuda previa que sale de `harness/`, ajena a F-009.
5. **`progress/peticion_posventa_prueba_F-012.md` sigue escrita y sin enviar.**
   Es **la llave del hueco 5** y también la del cierre real con espacios que
   dejó pendiente F-028. Es lo único que hoy desbloquea de verdad a F-009.

---

## 9 · Automejora (propuesta, NO aplicada — la decide el humano)

**El caso «feature cerrada con huecos documentados» ya ha ocurrido dos veces**
—F-012 el 2026-09-11 y F-009 hoy— y `CHECKPOINTS.md` **no lo contempla**: su C5
exige «todas las tareas `[x]`», así que un cierre honesto con huecos escritos
**parece un checkbox vacío** y obliga al reviewer a razonar la excepción a mano
cada vez. Dos reviewers distintos podrían resolverlo distinto, y uno de los dos
resolvería mal.

Propuesta para `CHECKPOINTS.md`, C5, primer punto — añadir:

> **Cierre con verificaciones abiertas.** Una tarea puede quedar `[ ]` al cerrar
> si, y solo si: (a) hay **decisión escrita y fechada** de quien puede tomarla,
> citada literal; (b) cada hueco consta **uno a uno con su requisito y su
> motivo** en un acta bajo `progress/`; y (c) la ficha de `features.json` remite
> a esa acta. El reviewer **comprueba las tres** y las enumera en su informe.
> Sin las tres, un `[ ]` sigue siendo CHANGES_REQUESTED.

Y un apunte para **C4 bis**: el informe que genera `harness.mutacion` **no
registra el nº de workers** en campañas anteriores a la 1.7.8, y el checkpoint lo
exige. Convendría que el checkpoint admita explícitamente que el dato conste **en
`tasks.md` o en el mensaje del commit** cuando el informe sea anterior a esa
versión — es lo que ha salvado aquí el cálculo del coste por mutante.

**Si el humano las acepta, van también a `arnes-base`**: valen para cualquier
proyecto (regla de propagación de `CLAUDE.md`).

---

## 10 · Veredicto

**APROBADO.**

El cierre hace lo difícil: **deja peor parada a la feature de lo que un cierre
complaciente la habría dejado**, y esa es la prueba de que es honesto. Los cinco
huecos están escritos con su requisito, su motivo y su coste; T27 consta como el
único criterio de la ficha sin ejecución real; R22 consta como no recuperable
hacia atrás; lo derogado se enmienda citando la premisa literal con fecha y
autor; y las dos correcciones que el implementer hizo al encargo —los dos
ficheros del cabo, y que la verificación 6 de F-028 no acredita T27— **son
ciertas las dos**, comprobadas contra las fuentes.

No se tocó `services/`, no se tocó `azure-apps`, no se ejecutó nada contra
producción, `init.sh` está en verde y el árbol queda limpio.
