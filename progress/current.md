<!-- progress/current.md -->
# Sesión activa

> ## ✅ AL DÍA · 2026-09-16 · **T23 y T24 de F-028 terminadas** · el control de la huella PASA
>
> Rama `feature/F-028-estado-del-parte`, árbol limpio, commits `6256762` (T23)
> y `0417104` (T24), locales, sin `push`.
>
> `bash harness/init.sh` → **ENTORNO LISTO**: **2.650 pasados**, 13 saltados,
> **0 fallos** en `api`; front en verde (caché); **PUERTA COBERTURA 100,0 % de
> 297 líneas cambiadas (297/297)**.
>
> ### Lo primero, porque es lo que el encargo pedía saber
>
> **Los tres controles de T23 pasan. Ninguna decisión humana vigente se ha
> invalidado, así que no había que parar.** El riesgo que la ficha mandaba
> tratar —que cambiar la normalización revocara aprobaciones que tomaron
> personas— queda **medido con el bloque 7 ya aplicado**, que era lo único que
> lo demostraba de verdad:
>
> - **el valor**: las **siete** huellas medidas en el árbol anterior al bloque
>   7 (`git worktree` sobre `71a5e00`) y en el de ahora son **idénticas**, y
>   van escritas **literales** en el test. Cuatro de las siete llevan el número
>   o la obra con espacios alrededor del separador;
> - **el acoplamiento**: `domain/models/aprobacion.py` importa exactamente
>   `__future__`, `hashlib` y `domain.models.validacion`. Ni `nombrado`, ni
>   `normalizar_codigo`, ni `tramos_de_codigo`;
> - **el efecto**: un parte aprobado por una persona sigue `aprobado` —incluido
>   el que tiene el número leído `RS26.09 /0149`, el caso exacto del riesgo— y
>   la pantalla sigue diciendo **«aprobado por una persona»**.
>
> ### Qué se ha cerrado
>
> - **T23** (`6256762`) · `tests/test_f028_huella_intacta.py`, **15 casos**.
>   **Ni una línea de código de producción.**
> - **T24** (`0417104`) · **siete recuadros fechados**: R12, R17 y R22 de F-026
>   enmendados (R56); R30 y R31 **precisados, no derogados** (R57); R36 de
>   F-025 con un segundo recuadro debajo del de F-026; los tres puntos de
>   `docs/ARCHITECTURE.md` que F-026 precisó, al día; y la **semántica 5**, que
>   pasa a decir que **los espacios alrededor del separador no forman parte del
>   código**. **42 casos nuevos**, ocho de ellos control negativo.
>   **Ningún texto original borrado**, y los tests de documentación de F-025 y
>   F-026 siguen en verde **sin tocarlos**.
>
> ### Tres cosas que el reviewer tiene que mirar con nombre propio
>
> 1. **§111.1** — el caso que recalcula la huella a mano **duplica a propósito**
>    el algoritmo dentro del test. Es una segunda opinión y por eso no importa
>    ninguna constante de `aprobacion.py`; el precio es que un cambio legítimo
>    del formato pondrá dos tests en rojo.
> 2. **§115.1** — la campaña automática da **32/32 sin supervivientes**, y
>    **no mide nada de este encargo**: T23 y T24 no añaden código de
>    producción. Lo que sí lo mide son los **13 mutantes a mano** de §115.2,
>    **13 muertos y ningún superviviente** (la primera campaña de la feature
>    sin ninguno).
> 3. **§117** — el **defecto latente D9** sigue sin arreglar, ahora **con
>    test**: una relectura que solo cambie los espacios alrededor de la barra
>    hace que una aprobación humana deje de contar. Arreglarlo cambiaría las
>    huellas ya escritas en `postventa.aprobaciones`, y el humano decidió el
>    2026-09-15 no alinear las dos normalizaciones aquí.
>
> ### Por dónde sigue
>
> **T25**, en su propio encargo: `docs/INTEGRACION.md` y
> `azure-apps/postventa_incidencias.md` —**dos repositorios, dos commits, sin
> `push`**—. Aviso vigente: `INTEGRACION.md` tiene un test que exige frases
> concretas (R26 de F-010, `tests/test_f010_integracion_expuesto.py`), y ya se
> rompió una vez esta semana por reescribirlo sin mirarlo. Después, el bloque
> 10: T26, T27 (las seis verificaciones MANUAL del humano tras desplegar) y
> T28.
>
> El informe completo, en `progress/impl_F-028.md` §109–§118.

---

> ## SUPERADO por el bloque de arriba · 2026-09-16 · **T21 y T22 de F-028** · la rama vuelve a estar EN VERDE
>
> Rama `feature/F-028-estado-del-parte`, árbol limpio, commits `30cf674` (T21)
> y `2482607` (T22), locales, sin `push`.
>
> `bash harness/init.sh` → **ENTORNO LISTO**: **2.593 pasados**, 13 saltados,
> **0 fallos** en `api`; front en verde (caché, árbol sin cambios); **PUERTA
> COBERTURA 100,0 % de 297 líneas cambiadas (297/297)**.
>
> **Los 25 rojos que declaraba §94 están los 25 en verde.** Y lo que más
> importaba de ellos: **los 4 de `tests/test_f028_puertas.py` —la red de
> seguridad del bloque 0— volvieron a verde SOLOS**, sin tocar ni una línea de
> ese fichero ni de las tres puertas. Fallaban por el código convertido, no por
> el control. El control nunca se aflojó.
>
> **Qué se ha cerrado: el bloque 7 entero, y con él el asunto 2 en el dominio.**
>
> - **T21** · `test_f006_r8_los_espacios_interiores_se_colapsan_a_uno` pasa a
>   esperar `"RS26.08-0123"`; R8 de F-006 recibe su **recuadro fechado** con el
>   patrón de R28 de F-010 —premisa citada literal, qué la invalidó, y **el
>   responsable, el 2026-09-15**, al ver fallar el circuito en real—; y
>   `tests/test_f028_documentacion.py` (nuevo, 6 casos) **fija ese recuadro**.
> - **T22** · `a_codigo_de_sigrid` compone por tramos:
>   `return "/".join(tramos_de_codigo(codigo))`. **Una línea** y su
>   importación. `cierre.py` no cambia en nada más: control negativo verificado
>   sobre el diff — ni `TEXTO_LOG_CIERRE`, ni `batch_de_cierre`, ni
>   `infrastructure/sigrid/escrituras.py`.
>
> ### Tres cosas que el reviewer tiene que mirar con nombre propio
>
> 1. **UN test existente cambió de expectativa** (§100), que es lo que la spec
>    manda declarar: `test_f006_r8_los_espacios_interiores_se_colapsan_a_uno`.
>    No es aflojarlo: R8 pedía que dos lecturas del mismo parte produjeran el
>    mismo nombre y **eso no se cumplía**; la garantía no se recorta, se cumple
>    por primera vez. Conserva su nombre, cita la expectativa vieja en su
>    docstring y **gana una segunda aserción** para no dejar de probar el
>    colapso que sí sigue vigente.
> 2. **La campaña automática da 32/32 y esta vez la línea base SÍ estaba verde,
>    pero no mide T22** (§105.1): el generador no produce ningún mutante sobre
>    `"/".join(...)`. Lo que respalda el bloque son los **15 mutantes a mano**:
>    14 muertos y 1 superviviente **equivalente**.
> 3. **El superviviente M8** (§105.3): la guarda `if not codigo: return ""` de
>    `a_codigo_de_sigrid` quedó **redundante** con el cambio de T22 —
>    `"/".join(())` ya es `""`—. Demostrado equivalente con ocho entradas. **No
>    se ha quitado**, y el porqué está escrito para que la decisión se tome
>    mirándola.
>
> **Decisión que `tasks.md` no enumera**: `tests/test_f028_documentacion.py` se
> crea en T21 con **solo los casos de R55**, para que «el recuadro presente»
> tenga verificación automática. **T24 lo extiende** con R56, R57 y R58.
>
> **Lo siguiente es el bloque 8 (T23)**: los tres controles negativos de que la
> huella de F-026 **no se ha movido**. No se ha entrado en él. Informe:
> `progress/impl_F-028.md`, secciones **99 a 108**.

> ## SUPERADO por el bloque de arriba · 2026-09-16 · T19 y T20 de F-028 · la rama estuvo en rojo (**resuelto por T22**)
>
> Rama `feature/F-028-estado-del-parte`, árbol limpio, commits `98968c8` (T19) y
> `c12d826` (T20), locales, sin `push`.
>
> **`bash harness/init.sh` sale EN ROJO, y es lo primero que hay que leer.**
> Hay **25 tests en rojo** con **dos** causas:
>
> - **1** es `test_f006_r8_los_espacios_interiores_se_colapsan_a_uno`, que es el
>   que **T21** tiene que actualizar. El encargo prohibía tocarlo y no se ha
>   tocado.
> - **24** son **una sola causa**: `a_codigo_de_sigrid` sigue convirtiendo con
>   `replace(" - ", "/")`, y el arreglo de R44 deja esa sustitución sin efecto.
>   Componer por tramos es **T22**, y el encargo prohibía entrar en ella.
>
> **T20 y T22 no se pueden separar**, y no es un descuido del implementer: es
> una consecuencia inevitable de R44. La línea de verificación de T20 en
> `tasks.md` —«T19 en verde»— **no es alcanzable** sin T22, y la propia T22 lo
> delata al pedir «T19 **entero** en verde». Entero en
> `progress/impl_F-028.md` **§94**.
>
> **Qué se ha cerrado: el arreglo de los espacios, en el sitio correcto.**
>
> - **T19** · `tests/test_f028_espacios_codigos.py`, **59 casos**, escrito
>   **antes** que el código: la tabla de `design.md` §9.3 fila a fila para las
>   dos conversiones. Falló en las **tres filas rotas**, y la quinta
>   (`RS26.09- 0149`) rompía además el nombre del fichero. Trazas pegadas en
>   **§92**.
> - **T20** · `normalizar_codigo` quita los espacios que flanquean a un
>   separador (R44); `SEPARADORES_DE_CODIGO` y `tramos_de_codigo` nuevas;
>   `nombre_de_archivo` compone uniendo tramos. **Un solo fichero de
>   producción**: `domain/models/nombrado.py`.
>
> `tests/test_f006_nombrado.py` queda **entero en verde salvo el único test de
> T21**, que era la condición que ponía el encargo.
>
> ### Tres cosas que el reviewer tiene que mirar con nombre propio
>
> 1. **La campaña automática de mutación da 32/32 y NO VALE** (§95.1): con la
>    línea base en rojo, el ejecutor da por muerto cualquier mutante. Lo que
>    respalda T20 son los **16 mutantes a mano** de §95.2, evaluados contra una
>    línea base construida verde a propósito: **15 muertos y 1 superviviente
>    equivalente**, demostrado con 55.987 cadenas (§95.3).
> 2. **Una decisión que `tasks.md` no enumera** (§93.2): un nº de incidencia de
>    solo separadores (`"/"`) ya no se archiva. No normaliza a vacío, así que la
>    guardia de F-006 R6 lo dejaba pasar, y al componer por tramos habría dado
>    `0626 -  PARTE FIRMADO.pdf` — un nombre que `nombre_admisible` **acepta**.
> 3. **El riesgo de la huella de F-026 sigue descartado y no se ha rediseñado
>    nada por él** (§93.4). El control explícito es el bloque 8 y **no** se ha
>    adelantado.
>
> **Propagación pendiente a `arnes-base`** (la tercera que anota esta feature):
> `harness.mutacion` **no comprueba que la línea base esté verde** antes de
> empezar, y publica un 100 % que solo dice que la suite ya fallaba.
>
> **Lo siguiente son T21 y T22, y hay que hacerlas juntas**: las dos devuelven
> la rama a verde; por separado la dejan rota entre medias sin ganar nada.
> Informe: `progress/impl_F-028.md`, secciones **90 a 98**.

> ## SUPERADO por el bloque de arriba · 2026-09-16 · T18 de F-028
>
> Rama `feature/F-028-estado-del-parte`, árbol limpio, `bash harness/init.sh` →
> **ENTORNO LISTO**: 2.528 pasados en `api`, **250 en `front`**, **298 casos de
> JavaScript** y cobertura **100,0 % de 283 líneas cambiadas**. Commit
> `4b85e6b`, local, sin `push`.
>
> **Qué se ha cerrado: la pantalla, y con ella el bloque 6 entero.**
>
> - **los dos gestos en el detalle** (R40), con el PDF delante y el campo de
>   motivo delante de los dos. El botón de **rechazar está deshabilitado
>   mientras no haya motivo** (R11), y un motivo de solo espacios no cuenta;
> - **las cuatro marcas** en la lista y en el detalle (R38): el rechazado gris
>   apagado y **tachado** —que no se confunda con «pendiente de mirar»—, el
>   cerrado azul y con candado, y el aprobado **por una persona** con anillo,
>   separado del que dio por bueno la máquina (R39);
> - **la frase del parte `cerrado`** (R41): la pantalla **explica** por qué no
>   se puede cambiar, en vez de fallar, y no ofrece ningún gesto;
> - **los textos de R43**, que son dos hechos distintos: «lo decidió una
>   persona · fecha» y «la decisión dejó de contar porque el veredicto cambió»;
> - **ningún `oid` en la sección del estado**, ni siquiera dentro de una
>   condición: lo pregunta `hayIdentidad()` (R42).
>
> Informe: `progress/impl_F-028.md`, secciones **80 a 89**.
>
> ### ✅ La rama vuelve a poder desplegarse
>
> Las tres líneas que T16/T17 dejaron rotas a propósito están arregladas y cada
> una tiene su control negativo: `api.aprobar` (ya no existe),
> `cuerpoDeAprobacion` (retirada) y `semaforoDe(validacion, parte.aprobacion)`
> (ahora recibe el bloque nuevo). El detalle, con su tabla, en la sección **89**.
>
> ### Tres cosas que el reviewer tiene que mirar con nombre propio
>
> 1. **R43 no se puede leer de una sola respuesta** y por eso hay una función
>    nueva, `js/pipeline.js::avisoDeEstado`, que compara dos bloques
>    consecutivos. El porqué —y la alternativa descartada, que sería tocar el
>    backend— están en **§83.1**. Es la única desviación respecto a `design.md`
>    §8.2, que no nombraba `pipeline.js` en T18.
> 2. **La campaña a mano tuvo DOS supervivientes en la primera pasada**, y los
>    dos tapaban un agujero real de mis propios tests: un test de texto que daba
>    por comprobada una estructura sin mirarla. Están contados enteros en
>    **§86.3**, con el arreglo. Después: **21 de 21 muertos**.
> 3. **20 tests retirados** —`tests_js/aprobacion.test.js` entero y 7 de
>    `tests/test_f026_front.py`—, todos con su recuadro fechado y su sustituto o
>    su derogación nombrada (§84). **Tres de los siete seguían en verde**, dos de
>    ellos iterando sobre listas vacías, y eran los que sostenían el requisito de
>    privacidad.
>
> Y el aviso de siempre, que ya lleva tres bloques: **ni la puerta de cobertura
> ni `harness.mutacion` miden una sola línea de esto**, porque el arnés solo
> mide y muta Python (§86.1). Lo que respalda la tarea son los 21 mutantes a
> mano y la ejecución real de `app.js` bajo Node (§85.1).
>
> **No se ha entrado en el bloque 7.** La siguiente es **T19**.

> ## SUPERADO por el bloque de arriba · 2026-09-16 · T16 y T17 de F-028
>
> Rama `feature/F-028-estado-del-parte`, árbol limpio, `bash harness/init.sh` →
> **ENTORNO LISTO**: 2.528 pasados en `api`, 223 en `front`, **305 casos de
> JavaScript** y cobertura **100,0 % de 283 líneas cambiadas**. Commits
> `9d379f3` (T16) y `efaaea4` (T17), locales, sin `push`.
>
> **Qué se ha cerrado:** la capa JS del front.
>
> - **T16** · `js/api.js::cambiarEstado` → `POST /api/estado` con su paso propio
>   de traza, y se retira `aprobar`, que llamaba a un endpoint que T15 borró.
>   `js/pipeline.js::cuerpoDeCambioDeEstado` compone el cuerpo y **se niega** sin
>   destino manual (R10), sin quien decide (R14), con un rechazo sin motivo
>   (R11), con un motivo pasado del límite del dominio (R13) o sin remesa.
>   `confirmado` viaja como el **booleano** de JSON. Ni un byte del PDF ni un
>   veredicto hecho (R28, R30).
> - **T17** · `semaforoDe(validacion, estado)` pinta las cuatro marcas y
>   distingue el aprobado **por una persona** del de la máquina (R39);
>   `esCirculable` y `pendientesDeCircuito` filtran por `estado === "aprobado"`.
>   **Un parte `rechazado` sale de la tanda aunque su veredicto sea apto** —el
>   caso que el responsable pidió— y un `cerrado` también.
>
> Informe: `progress/impl_F-028.md`, secciones **70 a 79**.
>
> ### ⚠️ Sigue sin poder desplegarse: falta T18
>
> `js/app.js` e `index.html` **no se han tocado** (son T18, y el encargo era
> pararse antes). Hoy `app.js` llama a `api.aprobar` —que ya no existe— y a
> `cuerpoDeAprobacion`, y le pasa a `semaforoDe` el bloque viejo. **El front y
> la Function se despliegan juntos**, así que hasta que T18 esté, nada de esto
> sale a Azure. Lo que T18 se encuentra hecho y los cinco apuntes para cogerla
> están en la sección **78** del informe.
>
> ### Dos cosas que el reviewer tiene que mirar con nombre propio
>
> 1. **Ni la puerta de cobertura ni la campaña de mutación miden este bloque**
>    (informe §76.1). El arnés mide y muta **Python**, y T16 y T17 son 307
>    líneas de **JavaScript**. Los 31 mutantes de la campaña son de los bloques
>    1 a 5 y siguen muriendo, pero no dicen nada de este. Lo que respalda el
>    bloque es la fase RED (§72) y **15 mutantes aplicados a mano, 15 muertos**
>    (§76.2). Queda anotado para el líder como posible mejora del arnés
>    genérico: un servicio con dos lenguajes mide uno solo y no lo dice.
> 2. **29 tests retirados y 8 reescritos**, todos con su recuadro fechado y su
>    sustituto nombrado (§74). Cuatro de los retirados **seguían en verde** y se
>    van por eso mismo: su montaje se había quedado inerte.
>
> La fase RED destapó un defecto real que no estaba en la spec: un
> `usuario_oid` de solo espacios es `truthy` en JavaScript y se colaba en la
> petición (§72.2). Arreglado y con test.

> ## SUPERADO por el bloque de arriba · 2026-09-16 · T13 de F-028, y el arnés está ROJO por otra cosa
>
> Rama `feature/F-028-estado-del-parte`. Lo de abajo («PARA RETOMAR · al
> 2026-09-15») es de la rama de F-026 y **se conserva entero**: sigue valiendo
> para el plan de merge y despliegue.
>
> **Qué se ha cerrado:** **T13** —`POST /api/estado`, su ruta en
> `function_app.py` y la traducción de `ParteCerrado` a **409**, que no
> existía—. El commit `822100e` había dejado la tarea a medias y en rojo a
> propósito (el vigilante mató al implementer a los 600 s): 57 casos en verde y
> 12 en rojo. **Los 12 eran de los tests, no del handler**, y el handler entra
> sin tocar ni un byte. Informe: `progress/impl_F-028.md`, secciones **36 a
> 47**.
>
> **No se ha entrado en T14 ni en T15.** La siguiente es **T14**.
>
> ### ⚠️ `bash harness/init.sh` sale ROJO, y **no es de F-028**
>
> ```
> FAILED tests/test_f010_integracion_expuesto.py::test_f010_r26_dice_la_consecuencia_visible_de_cada_ausencia
> E   AssertionError: assert 'Sigrid no se toca' in '...'
> ```
>
> **Ya estaba rojo en `HEAD` antes de empezar** —comprobado con `git stash`—: lo
> rompió el commit `6eb6d33` («INTEGRACION: los dos cierres reales...») al
> reescribir `docs/INTEGRACION.md` y sacar de su tabla la fila que contenía esa
> frase. Es documentación de F-010 y **decidir qué debe decir ahora ese
> documento no es del implementer de T13**. Queda para el humano o para quien
> retome F-010.
>
> Tiene **tres consecuencias** que no hay que confundir con un problema de
> F-028:
>
> 1. `[KO] servicio api: pytest en rojo` — ese caso y ningún otro;
> 2. `[KO] PUERTA COBERTURA: 58,3 %` es **falso**: `init.sh` lanza la suite con
>    `-x`, se para ahí y mide media suite. Entera, la puerta da **100,0 % de 276
>    líneas cambiadas**;
> 3. **la campaña de mutación sale falsa**, y esta es la grave. El evaluador da
>    un mutante por muerto cuando la suite falla; con un caso rojo antes de
>    mutar nada, **todos** salen «muertos» sin que ningún test los cace. La
>    campaña que consta en `progress/mutacion_F-028.md` se lanzó con ese único
>    caso deselecionado y `--workers 1`, con la línea base **verde**. Mientras
>    ese test siga rojo, **ninguna campaña lanzada a secas sobre el servicio
>    `api` vale nada**.
>
> **T12 sigue sin marcar en `tasks.md`** aunque el commit `0af9830` la hizo. No
> se marcó porque el encargo era «T13 y nada más». Es para el líder.

> ## PARA RETOMAR · al 2026-09-15, tras la sesión de solo lectura de F-009
>
> **Dónde está todo:** rama `feature/F-026-aprobacion-humana`, árbol limpio,
> arnés en verde (`62 passed in 4.22s`, cobertura de líneas cambiadas 99,0 %).
> **195 commits sin mergear a `dev`** (medido con `git rev-list --count
> dev..HEAD`; el «185» del bloque anterior estaba corto) y **nada con `push`**
> en ninguno de los
> tres repositorios (este, `azure-apps` y `arnes-base`).
>
> ### El estado, en una tabla
>
> | Feature | Estado | Qué falta |
> |---|---|---|
> | **F-012** parte adjunto a la incidencia | `done` | nada |
> | **F-025** una sola confirmación | `done` | nada |
> | **F-026** aprobación humana y autoguardado | **`in_progress`** | **solo la verificación real**, que la hace el humano |
> | **F-009** cierre en Sigrid | `blocked` | decisión del humano: ver abajo |
> | **F-024** datos del parte para el datamart | `spec_ready` | cuatro decisiones del humano |
>
> ### El plan acordado, y por dónde va
>
> Por orden: **(1)** cerrar F-009, **(2)** merge de la cadena a `dev`, **(3)**
> desplegar backend y front, **(4)** el humano revisa F-026 en real y se cierra.
> **Los pasos 2, 3 y 4 siguen intactos.**
>
> ### Paso 1 · F-009: ya casi está, y la decisión sigue siendo del humano
>
> El **2026-09-15** se hizo la **sesión de solo lectura** que se había propuesto:
> cuatro scripts de `infra/` contra el ERP de producción, **sin abrir la ventana
> de escritura** —solo `POST /api/sql/read`, `CIERRE_HABILITADO` cerrado todo el
> tiempo— y solo lectura del esquema propio en PostgreSQL. **Los cuatro dan
> `PASA`.** Acta en `progress/guion_bloque8_F-009.md` **§10**; informe del
> encargo en `progress/impl_lectura_F-009.md`.
>
> **Lo que se ha ganado:**
>
> - **El huso de la fila de auditoría es HORA LOCAL**, con **0,0 min** de
>   diferencia. **El defecto que el diseño daba por probable no existía**: no
>   escribimos en UTC. Era *la única decisión de la feature que no se pudo tomar
>   con un dato*; ahora lo tiene.
> - **T25 queda marcada entera** (las dos condiciones de D1: seguimos saliendo en
>   los informes de Posventa, y el filtro exacto devuelve **solo lo nuestro**,
>   ninguno de los 6.843 cierres manuales).
> - **De T24 quedan acreditados los pasos 6, 7 y 9**, y con ellos **R24, R25, R41
>   y R43**. El paso 6 ya no depende de lo que viera una persona en la ficha.
>
> **Lo que NO se ha ganado, y por qué T24 sigue sin marcar**: su contrato son
> nueve pasos y faltan cinco —el 2, el 3, el 4 (el `estado` de la respuesta), el
> 5 y el 8—, y el **`filas_afectadas: 2` (R22) no es recuperable hacia atrás**:
> solo lo dará el siguiente cierre real. **T22, T23 y T27 tampoco se marcan.**
>
> **De ocho huecos quedan cinco** (`guion_bloque8_F-009.md` §9.4, actualización):
>
> | # | Hueco | Coste |
> |---|---|---|
> | 4 | **T23** · siembra del login, **reducido** a R33, R31 y la unicidad del candidato. Hoy se vio que el `usu` del ERP es `pgris`, luego el login se derivó, se resolvió y se usó para firmar — pero eso no prueba R33 | casi todo solo lectura |
> | 5 | **T22 pasos 2 y 5** · el `503` con el interruptor apagado, y que el dry-run no escribe | el `503` sale gratis; lo otro exige ventana |
> | 6 | **T22 paso 4** · las seis cosas de R9 y el bloque `grafico` | ventana abierta, pero **no escribe** |
> | 7 | **T27** · reintento sobre lo ya cerrado | **el único que exige abrir la ventana de escritura**, y **sale gratis cuando el humano revise F-026**: basta volver a subir un parte ya cerrado |
> | 8 | **`filas_afectadas: 2`** y el `tiemod` de partida | **no recuperable**: solo el siguiente cierre real |
>
> **La decisión que sigue encima de la mesa es la misma, con menos peso encima**:
> cerrar F-009 con los cinco huecos escritos y fechados —como se cerró F-012—, o
> recorrer antes alguno más. Lo que ya no puede decirse es que *nadie ha mirado
> la fila de auditoría*: está mirada, campo a campo, y pasa.
>
> ### Cabos abiertos, con dueño
>
> - **`azure-apps/postventa_incidencias.md` sigue diciendo que «todavía no se ha
>   ejecutado ni un cierre real»**, y desde el 2026-09-11 es falso. La regla de
>   propiedad de `CLAUDE.md` obliga a corregirlo, y ahora hay con qué hacerlo
>   bien: fecha, incidencia, `ide` de la fila de log y veredicto del huso.
> - **`infra/07_alta_usuario_sigrid.ps1`** (líneas 161 y 248) y
>   **`infra/17_traza_grafico_local.ps1`** (línea 196) arrastran el defecto de
>   comillas de PowerShell 5.1 que el 2026-09-15 tumbó al `12`, y **nunca se han
>   ejecutado**: se estrellarán en la primera línea de quien recorra T23 o la
>   precondición de T24. El arreglo ya está escrito
>   (`Invoke-PythonDelServicio`, en `infra/08_lectura_sigrid_comun.ps1`).
> - `progress/peticion_posventa_prueba_F-012.md` está **escrita y sin enviar**.
>   Su nota interna dice qué hacía falta antes; ya se cumple.
> - Dos avisos nuevos de `ruff` (58 → 60) que **no son de ninguna feature**:
>   salen de `harness/`.
> - `arnes-base` tiene el **encargo 1.7.12** sin implementar (la caché de
>   `init.sh` puede tapar un rojo — y en esta sesión las suites de `api` y
>   `front` volvieron a salir de caché) y el 1.7.11 sin confirmar siquiera.

> ## Estado al 2026-09-14 · **F-009: levantada el acta de su bloque 8; solo T26 queda acreditada**
>
> Encargo **documental** y acotado: F-009 sigue `blocked` desde el 2026-09-06
> esperando a F-012, pero **el cierre real ya se ejecutó** —dentro de la
> verificación de F-012, el 2026-09-11— así que buena parte del bloque 8 de
> F-009 **ya ocurrió**. Había que averiguar **qué exactamente**, y dejarlo
> escrito. **No se ejecutó nada** contra Azure, Sigrid, `sigrid-api`, el
> PostgreSQL compartido ni SharePoint: toda la evidencia estaba escrita.
> Informe: `progress/impl_cierre_F-009.md`.
>
> ### Lo hecho, en dos commits
>
> - **`092bf8d`** — `progress/guion_bloque8_F-009.md`: casillas de **T22–T27**
>   rellenas citando dónde consta cada cosa; **enmienda fechada de la obra**
>   (nombraba la obra de prueba **404**; fue **`RS26.09/0150` de la `0626`**,
>   una obra **en uso**, por decisión del responsable del 2026-09-10) **sin
>   borrar la premisa original**; y un **§9** nuevo con la evidencia medida, los
>   **ocho huecos con su coste** y el **veredicto**. Era el resto abierto de
>   **H10** de `guion_bloque9_F-012.md`.
> - **`ff5fb6a`** — `specs/F-009-cierre-sigrid/tasks.md`: **solo T26** del
>   bloque 8 marcada, más **T29**, cada una diciendo de dónde sale. Nota
>   fechada bajo el bloque 8 que enmienda además dos cosas que el texto de T22
>   dice mal: **Mirasierra** y el **aviso de R21**, derogado por R48 de F-012.
>
> ### El veredicto, para la decisión del líder
>
> **El cierre real está acreditado; sus comprobaciones, casi ninguna.** Una
> reclamación pasó a `CER` en producción, con autorización y **con su parte
> dentro**, y el responsable lo vio en la ficha de Sigrid. Pero **ninguno de
> los cinco scripts de lectura de `infra/` se ha ejecutado jamás**: de los nueve
> pasos de T24 constan **uno y medio**, y **la fila de auditoría del primer
> cierre real está escrita en producción y nadie la ha mirado** —su **huso**
> incluido, que §0.2 del guion daba por defecto probable—.
>
> **Marcar el bloque 8 como superado sería falso.** De los ocho huecos de §9.4,
> **siete no exigen escribir en el ERP y tres no exigen ni abrir la ventana**
> (la fila de `dbo.log` y su huso, T25 entera, la traza local). **El único que
> exige ventana de escritura es T27**, el reintento sobre lo ya cerrado — el
> escenario más probable en uso normal, y el que **las tres features dejaron
> sin marcar** (T27 de F-009, T30 de F-012, T22 de F-025).
>
> ### Tres cosas que el reviewer tiene que mirar
>
> 1. **La única marca del bloque 8 es T26, y se apoya en una inferencia**: `200`
>    + la reclamación en `CER` ⇒ el guard aceptó el batch, porque un rechazo lo
>    habría revertido entero. La cadena está escrita entera en su casilla y en
>    `tasks.md` **para que se pueda romper**; `filas_afectadas` no se anotó y
>    eso consta como salvedad, no se esconde.
> 2. **La prueba de F-025 se descartó a propósito como evidencia de T27** (§9.6
>    del guion): sus registros no muestran **ninguna** llamada a `cerrar`, y una
>    llamada que no consta no verifica un reintento.
> 3. **`T29` se marcó desde la rama `feature/F-026-aprobacion-humana`**, no
>    desde la de F-009, y la salvedad va escrita: el código de F-009 está en el
>    historial de HEAD, así que el verde cubre más, no menos.
>
> ### Lo que NO se tocó
>
> **El `status` de ninguna feature** —F-009 sigue `blocked`, lo lleva el líder—,
> ni código, ni tests, ni `azure-apps/`. Ese último es el pendiente con dueño:
> `azure-apps/postventa_incidencias.md` **sigue diciendo que «todavía no se ha
> ejecutado ni un cierre real»**, y desde el 2026-09-11 es falso.

> ## Estado al 2026-09-12 · **F-026: hecho el bloque 5, las enmiendas y la documentación**
>
> Entrega **parcial y pedida así**: el encargo acotaba el trabajo al **bloque
> 5** de `specs/F-026-aprobacion-humana/tasks.md` (T17–T19) y mandaba parar
> ahí. **El bloque 6 (verificación contra la base real, del responsable), el 7
> (cierre, del líder) y la campaña de mutación no se han tocado.** Informe
> completo, con la traza de la fase RED y las evidencias, en la **parte V** de
> `progress/impl_F-026.md` (§35 en adelante).
>
> ### Lo que hay hecho en esta tanda
>
> - **T17** (`b7ac982`) — el recuadro de enmienda bajo **R36 de F-025**, sin
>   borrar su texto, y `tests/test_f026_documentacion.py` (21 tests) escrito
>   **antes** que los documentos.
> - **T18** (`c9258f0`) — los **tres** puntos de `docs/ARCHITECTURE.md` que
>   decían que solo se archiva lo apto: paso 6, semántica 3 y semántica 7.
>   **Precisados, no borrados.**
> - **T19** (`02cb101` aquí, `0d7c843` en `azure-apps`) — `docs/INTEGRACION.md`
>   y su copia del ecosistema: la tabla `postventa.aprobaciones`, el endpoint
>   `POST /api/aprobar`, las ventanas de escritura y el `oid` de quien aprueba.
> - **Ajuste** (`212ba40`) — la cuenta de endpoints, de once a doce, en los dos
>   tests ajenos que la vigilan.
>
> ### Lo que cambia de verdad
>
> Hasta hoy el código abría una puerta que **tres documentos aprobados
> declaraban cerrada**. Quien leyera `ARCHITECTURE.md` encontraría
> `_exigir_admitido` y lo tomaría por un agujero; quien leyera R36 de F-025
> «arreglaría» el backend para volver a dejar fuera los partes aprobados. Eso
> ya no puede pasar, y **no porque alguien se acuerde: porque hay un test**.
>
> Y el documento del ecosistema ya dice lo único que el resto de proyectos
> necesita saber de F-026: que **no empezamos a consumir nada nuevo**, y que
> desde ahora una reclamación puede acabar cerrada aunque su parte no fuera
> apto —si una persona lo aprobó—, **sin que en el ERP quede constancia** de esa
> aprobación (decisión expresa del responsable).
>
> ### Tres cosas que el reviewer tiene que mirar
>
> 1. **El botón de aprobar consta como interpretación del líder**, no como
>    pronunciamiento del responsable, y así está escrito en el recuadro con su
>    test (§36.1 del informe). Lo que el responsable pidió fue lo contrario
>    —«según escribe guarda, sin botón»— pero para las correcciones, que es
>    otro juicio.
> 2. **Se tocaron dos documentos y no uno** (§38): `azure-apps/` declara ser
>    una copia de `docs/INTEGRACION.md`, así que tocar solo la copia habría
>    creado justo la divergencia que la regla quiere evitar. Dos repositorios,
>    dos commits, **sin `push`** en ninguno, `git -C ../azure-apps status`
>    limpio.
> 3. **Dos tests ajenos saltaron en rojo y ninguno se aflojó** (§39). El de
>    F-019 mantiene su cuenta a mano —es lo que ese test declara querer— y el de
>    F-012 pasa a **contar** las filas de la tabla en vez de fijar un literal,
>    porque así comprueba lo que afirma en lugar de avisar de una cifra vieja.
>    De paso, el árbol de tablas de §2 listaba seis de las nueve que crea el
>    DDL: se añaden `usuarios_sigrid` (F-009) y `graficos` (F-012), y queda
>    declarado como deuda ajena corregida al pasar (§38.1).
>
> ### Lo que falta para cerrar F-026
>
> - **Bloque 6 (T20–T23)** · **MANUAL (humano)**, contra la base de desarrollo:
>   el DDL aplicado dos veces, el circuito completo de un parte aprobado, la
>   traza reconstruible hasta el ERP y la revocación sobre datos reales. A esa
>   lista siguen sumadas las comprobaciones de pantalla de §26 y §33, que nadie
>   ha visto todavía en un navegador.
> - **Bloque 7 (T24)** · la campaña de mutación.
>
> `bash harness/init.sh` en **verde** al cerrar (exit 0): 62 tests en la raíz,
> **2 338** en el servicio `api` —**21 nuevos**—, `front` servido de caché, y
> la puerta de cobertura en **99,0 %** de 1 338 líneas cambiadas.


> ## Estado al 2026-09-12 · **F-026: hecho el bloque 4 bis, el autoguardado**
>
> Entrega **parcial y pedida así**: el encargo acotaba el trabajo al **bloque
> 4 bis** de `specs/F-026-aprobacion-humana/tasks.md` (TA1–TA5) y mandaba parar
> ahí. **El bloque 5 y el 7 (la campaña de mutación) no se han empezado.**
> Informe completo, con las trazas de la fase RED y las evidencias, en la
> **parte IV** de `progress/impl_F-026.md` (§28 en adelante).
>
> ### Lo que hay hecho en esta tanda
>
> - **TA1** (`428842c`) — `RETARDO_AUTOGUARDADO_MS: 1500` en `js/config.js`,
>   con la razón del número escrita al lado; `js/autoguardado.js` (el rebote y
>   la comparación con lo último guardado, lógica pura y con el temporizador
>   inyectado); `valoresDeCampos` en `js/pipeline.js`; y el disparador en
>   `app.js::editarCampo`.
> - **TA2** (`7beaa0b`) — lo que se dispara es `revalidarYGuardar`, la misma
>   función que el botón, con su control negativo.
> - **TA3** (`ebfb2ae`) — los tres estados en `index.html`.
> - **TA4 + TA5** (`1259c39`) — la corrección no pisa lo que leyó la IA (R53,
>   por F-015), una revocación como mucho por pausa (R54) y todos los partes
>   (R55).
>
> ### Lo que cambia de verdad en la pantalla
>
> Escribir en un campo **guarda lo que escribes**, tras una pausa de 1,5 s y
> **sin botón**. Hasta hoy la corrección vivía **solo en memoria** y quien
> escribía y se iba la perdía. Y hay un efecto de segundo orden que importa:
> como la **revocación de una aprobación ocurre en la escritura**, corregir un
> campo de un parte aprobado ahora lo revoca **solo**, sin que nadie tenga que
> acordarse de pulsar «Revalidar».
>
> Y si el guardado falla, se dice: **recuadro rojo que no se va solo**, con lo
> escrito intacto en el campo. Quien escribe y no ve nada supone que se guardó.
>
> ### Tres cosas que el reviewer tiene que mirar
>
> 1. **TA2, TA4 y TA5 no tuvieron fase RED, y está escrito por qué** (§31 del
>    informe): TA2 fija un acoplamiento que TA1 ya dejó cableado —y que existe
>    desde F-019 R28—, y TA4/TA5 son **control-negativo**, que por definición
>    no pueden fallar antes de existir el código. El rojo real de este bloque
>    está en TA1 y TA3, con la traza pegada.
> 2. **`guardarParte` no lanza cuando el backend rechaza** —devuelve
>    `{ok: false, motivo}`—, así que `_guardarCorreccion` convierte ese caso en
>    error a propósito. Sin eso, la pantalla diría «Guardado.» con la base sin
>    tocar.
> 3. **Un test que pasaba sin comprobar nada** (§31, último apartado): un `\b`
>    mal escapado acabó siendo un carácter de retroceso literal dentro del
>    patrón. Se detectó porque pasaba cuando tenía que fallar. Corregido en
>    `428842c`, pero conviene saber que el fichero se ve idéntico a uno bueno.
>
> ### Lo que falta para cerrar F-026
>
> - **Bloque 5 (T17–T19)** · la enmienda a R36 de F-025, los tres puntos de
>   `docs/ARCHITECTURE.md` y `azure-apps/postventa_incidencias.md`. El endpoint
>   nuevo y la tabla nueva **siguen sin documentar fuera de la spec**.
> - **Bloque 6 (T20–T23)** · **MANUAL (humano)**, contra la base de desarrollo.
>   A esa lista se le añaden las cuatro comprobaciones de pantalla del
>   autoguardado que enumera §33 del informe: nada de esto se ha visto en un
>   navegador.
> - **Bloque 7 (T24)** · la campaña de mutación.
>
> `bash harness/init.sh` en **verde** al cerrar: 62 tests en la raíz, 224 en el
> servicio `front` (que incluyen los 292 de JavaScript por el puente de
> `node --test`), `api` servido de caché, y la puerta de cobertura en
> **99,0 %** de 1 338 líneas cambiadas.


> ## Estado al 2026-09-12 · **F-026: hecho el bloque 4, la pantalla**
>
> Entrega **parcial y pedida así**: el encargo acotaba el trabajo al **bloque
> 4** de `specs/F-026-aprobacion-humana/tasks.md` (T13–T16) y mandaba parar
> ahí. **El bloque 4 bis (el autoguardado), el 5 y el 7 no se han empezado.**
> Informe completo, con las cuatro trazas de la fase RED y las evidencias, en
> la **parte III** de `progress/impl_F-026.md` (§18 en adelante).
>
> ### Lo que hay hecho hoy
>
> - **T13** (`3fbfbd2`) — `js/pipeline.js` gana `MOTIVOS_APROBABLES`,
>   `esAprobable`, `esCirculable`, `cuerpoDeAprobacion` y un `semaforoDe` que
>   acepta la aprobación y devuelve un **cuarto estado**, `"aprobado"` (R36).
> - **T14** (`bf2fdc0`) — `pendientesDeCircuito`, `cuerpoDeArchivo`,
>   `esCerrable` y, por su puerta, `cuerpoDeGrafico` y `cuerpoDeCierre` pasan
>   por `esCirculable` (R23). `esArchivable` **conserva su significado**: lo que
>   dio por bueno la máquina.
> - **T15** (`48e2799`) — `api.aprobar()`, `app.aprobarParte()`, `esAprobable()`
>   y `aprobacion` declarada en `_parteInicial` para que Alpine la repinte.
> - **T16** (`5270f8d`) — `index.html`: el botón en el **detalle**, la marca del
>   semáforo con anillo, el texto de R36/R37 y la frase de R39.
>
> ### Lo que cambia de verdad en la pantalla
>
> Hasta hoy el backend admitía en el circuito un parte aprobado y **no había
> forma de aprobarlo** desde la interfaz. Ahora quien revisa aprueba con el PDF
> delante, **sin una segunda confirmación** (R29, P7: sigue armándose **una**
> en todo el front), y **un parte aprobado no se lee igual que uno que siempre
> fue verde**: mismo punto verde **con anillo**, más el texto de quién lo
> aprobó —una persona, sin `oid`, sin correo y sin nombre—, de qué destino se
> rescató y cuándo.
>
> ### Dos decisiones que el reviewer tiene que mirar
>
> 1. **El cuerpo de `/api/aprobar` es el de `/api/parte` más `usuario_oid` y
>    `confirmado`**, tal y como manda `design.md` §6, y **no** una versión
>    recortada como podría leerse en la letra de T13. El motivo está en §23.1
>    del informe y es de fondo: el backend **recalcula** el veredicto sobre esa
>    extracción, así que sin el texto de las observaciones el parte dejaría de
>    ser aprobable y aprobar contestaría 409 a toda la cola ámbar. Lo que sí se
>    fija por test es que F-026 **no añade** ninguna clave personal propia.
>    Punto a confirmar por el líder.
> 2. **`guardarParte` propaga la `aprobacion` que devuelve el backend**, y eso
>    no estaba en la letra de las cuatro tareas (§23.2). Sin ello, una
>    revalidación que **revoca** la aprobación (R31) dejaría la pantalla
>    diciendo «aprobado» hasta la siguiente recarga, y al resubir la remesa los
>    partes aprobados volverían a parecer rechazados (R22).
>
> ### Tres avisos para quien siga
>
> 1. **Nada de esto se ha visto en un navegador.** Los tests de pantalla son de
>    texto, que es lo que esta suite sabe hacer. Que la marca con anillo se
>    distinga del verde liso **de un vistazo** es literalmente R36 y solo lo
>    puede decir una persona: va al bloque 6, con T20–T23.
> 2. **`esCirculable` es la puerta de la tanda en el front.** Un selector nuevo
>    que vuelva a preguntar por `esArchivable` para decidir si algo se archiva,
>    se adjunta o se cierra deshace F-026 **sin romper ningún test de F-007**.
> 3. **El bloque 4 no está mutado, y no puede estarlo con este utillaje**:
>    `harness/mutacion` muta Python, y aquí todo lo escrito es JavaScript y
>    HTML. T24 sigue siendo obligatoria sobre el Python de la feature, y para el
>    front lo que sostiene la calidad son los control-negativo.

> ## Estado al 2026-09-12 · **F-026: hecho el bloque 3, las puertas y el borde HTTP**
>
> Entrega **parcial y pedida así**: el encargo acotaba el trabajo al **bloque
> 3** de `specs/F-026-aprobacion-humana/tasks.md` (T9–T12) y mandaba parar ahí.
> **Los bloques 4, 4 bis, 5 y 7 no se han empezado.** Informe completo, con las
> cuatro trazas de la fase RED y las evidencias, en la **parte II** de
> `progress/impl_F-026.md` (§10 en adelante).
>
> ### Lo que hay hecho hoy
>
> - **T9** (`6b51d60`) — `interface_adapters/api/aprobar.py`. Aprobar guarda el
>   parte, su veredicto **recalculado** y la aprobación **en una sola llamada**,
>   en ese orden. Dos puertas antes de tocar el puerto: `usuario_oid` (R4) y
>   `confirmado: true` como booleano de JSON, y `es_aprobable` sobre el
>   veredicto recalculado (R5, R9, R10).
> - **T10** (`9760019`) — la ruta en `function_app.py`, su traducción de
>   errores (400 / 409 / 503) y un log con `hash_parte`, destino y resultado y
>   **nada más** (R44).
> - **T11** (`851f0d2`) — los tres `_exigir_apto` pasan a `_exigir_admitido`:
>   el apto de siempre **o** una aprobación viva del mismo destino (R23).
> - **T12** (`44c306c`) — `POST /api/parte` devuelve el bloque `aprobacion`
>   (R22), leído **después** de guardar.
>
> ### Lo que cambia de verdad en el servicio
>
> Hasta hoy, F-026 no cambiaba ningún comportamiento: la tabla existía y nadie
> la llamaba. **A partir de este commit, un parte que la validación mandó a
> revisión puede archivar, adjuntar y cerrar si consta aprobado y vigente.** Lo
> que sigue siendo imposible, y lo vigilan los trece casos de control negativo
> de T1: hacerlo **sin** aprobación, o con una **revocada**, o con una de otro
> destino. Y ninguno de los tres endpoints del circuito gana una clave en su
> cuerpo: la aprobación se lee del repositorio y nunca de la petición (R24).
>
> ### Tres puntos de diseño que no se pueden perder
>
> 1. **El orden de las tres escrituras de `/api/aprobar`** —parte, validación,
>    aprobación— es requisito: guardar la validación **revoca** la aprobación
>    cuyo veredicto ya no coincide (R30, bloque 2), así que escribir la
>    aprobación antes la dejaría revocada en el acto de nacer. Lo mismo, al
>    revés, en `/api/parte`: la aprobación se **lee después** de guardar, o se
>    devolvería como viva una que esa misma llamada acaba de tumbar.
> 2. **Las puertas solo consultan cuando el veredicto no basta.** El parte apto
>    circula sin pagar una lectura por paso —66 consultas inútiles en una remesa
>    de 22—, y hay un test que lo fija para que no se pierda en la primera
>    refactorización.
> 3. **Los parsers del cuerpo bajaron a `cuerpos.py`** (`CLAVES_DEL_PARTE`,
>    `a_remesa_id`, `a_parte_troceado`), sin cambiar ni una regla ni un mensaje.
>    El motivo no es estético: si aprobar y guardar describieran el parte de dos
>    formas distintas, **se aprobaría un veredicto y se guardaría otro**.
>
> ### Tres avisos para quien siga
>
> 1. **No hay forma de aprobar desde la pantalla.** El bloque 4 (T13–T16) no se
>    ha tocado: el endpoint existe y funciona, pero hoy solo se puede llamar a
>    mano. Es lo siguiente.
> 2. **El endpoint estará vivo en cuanto se despliegue**, y **no depende** de
>    `ARCHIVO_HABILITADO` ni de `CIERRE_HABILITADO` (R21, deliberado). Escribe
>    solo en el esquema propio; lo que habilita es que un parte no apto entre en
>    el circuito cuando alguien lo apruebe. La confirmación única de F-025 sigue
>    intacta delante de toda escritura externa (R27).
> 3. **El bloque 3 no está mutado.** Esta tanda no lanzó ninguna campaña, por
>    encargo. La que sí corrió —en paralelo, del implementer del bloque 2:
>    `3e1b63e`, 242 mutantes y 14 supervivientes analizados en
>    `progress/mutacion_F-026.md`— se generó sobre un árbol **sin** `aprobar.py`,
>    sin `aprobacion_serializada.py` y sin las tres puertas nuevas. **T24 sigue
>    siendo obligatoria** al cerrar (C4 bis), sobre la feature entera.
>
>    Dos agentes escribieron en esta rama a la vez, y conviene saberlo al leer el
>    historial: el commit `3e1b63e` arrastró la parte II de
>    `progress/impl_F-026.md` —escrita por esta tanda y todavía sin commitear—
>    porque no se podía separar del mismo fichero. El código del bloque 3 va
>    entero en `6b51d60`, `9760019`, `851f0d2` y `44c306c`.
>
>    Sigue en pie, además, lo que anotó la tanda anterior: **la traza de la fase
>    RED de los bloques 0 y 1 se perdió** con el agente que se interrumpió, y
>    **el `.sql` solo está verificado en su texto** — T20 y T23 son `MANUAL
>    (humano)` y ningún doble de conexión puede sustituirlos.
>
> ### Estado del arnés al cerrar
>
> `bash harness/init.sh` → **ENTORNO LISTO**. Cobertura de líneas cambiadas
> **99,0 %** (1 325/1 338, umbral 80 %). **2 317** tests del servicio `api` en
> verde —61 nuevos en esta tanda—, 62 en la raíz, el front en verde. **60**
> avisos de `ruff`: uno más que los 59 de partida, un `I001` en `aprobar.py`
> del mismo tipo que los otros 20 del servicio (el repositorio no configura
> `known-first-party` y separa con línea en blanco el grupo
> `interface_adapters`). Se ha seguido la convención del servicio en vez de
> dejar el fichero nuevo como excepción; arreglarlo de verdad es una línea de
> configuración que toca a los 21 a la vez, y esa decisión es del líder.

---

> ## Estado al 2026-09-12 · **F-026: hecho el bloque 2, la persistencia de la aprobación**
>
> Entrega **parcial y pedida así**: el encargo acotaba el trabajo al **bloque
> 2** de `specs/F-026-aprobacion-humana/tasks.md` (T6–T8) y mandaba parar ahí.
> **Los bloques 3, 4, 4 bis y 5 no se han empezado.** Informe completo, con la
> fase RED y las evidencias: **`progress/impl_F-026.md`**, que además recoge lo
> que hicieron los bloques 0 y 1 leyendo sus commits — los agentes que los
> escribieron se interrumpieron antes de redactarlo.
>
> ### Lo que hay hecho hoy
>
> - **T6** (`1ece459`) — el DDL `10_aprobaciones.sql` existía desde `f1e5718`
>   pero **no estaba declarado**. Y el sitio donde se declara no es `ddl.py`
>   —que descubre los `.sql` por `glob`— sino la lista escrita **a mano y a
>   propósito** de `tests/test_f005_ddl_idempotente_texto.py`. El arnés estaba
>   en rojo por eso.
> - **T7** (`4d80aaa`) — `sentencias.py` gana `upsert_aprobacion`,
>   `select_aprobacion` y `revocar_aprobacion_si_cambio`; `mapeo.py` gana
>   `json_de_codigos_de_motivo` y `fila_a_aprobacion`.
> - **T8** (`fc5a37a`) — el puerto gana `guardar_aprobacion` y
>   `consultar_aprobacion`, y `guardar_validacion` ejecuta además la
>   **revocación**. `RepositorioEnMemoria` crece para seguir cumpliendo el
>   puerto.
> - **`tests/test_f026_persistencia.py`** nuevo: **34 tests**, sin BBDD y sin
>   red, con el doble de `tests/utiles_pg.py`.
>
> ### El punto de diseño que no se puede perder (D-F)
>
> **La revocación ocurre en la escritura, no en la lectura**, y «en la misma
> operación» es literal: `guardar_validacion` ejecuta el `upsert` de la
> validación y el `UPDATE` de la revocación **en el mismo cursor y con un solo
> `commit`**. Con dos transacciones habría una ventana en la que el veredicto
> nuevo ya está guardado y la aprobación del viejo sigue viva, y un paso que
> leyera justo ahí admitiría en el circuito un parte que nadie ha aprobado. Un
> test lo fija: `len(ejecutadas) == 2` y `commits == 1`.
>
> ### Tres avisos para quien siga
>
> 1. **Nada de esto cambia todavía el comportamiento del servicio.** La tabla
>    existe y el repositorio sabe escribirla y leerla, pero **nadie llama a
>    esas operaciones**: el endpoint `POST /api/aprobar` (T9) y las tres
>    puertas que leen la aprobación (T11) son el bloque 3. Un parte no apto
>    sigue sin archivarse, sin adjuntarse y sin cerrarse, y eso lo vigilan los
>    trece casos de control negativo de T1.
> 2. **La traza de la fase RED de los bloques 0 y 1 se perdió** con el agente
>    que se interrumpió. No se ha reconstruido: una traza de hoy no es la de
>    entonces. La del bloque 2 está pegada entera en el informe. El reviewer
>    tiene que saberlo antes de mirar C4 bis.
> 3. **El `.sql` solo está verificado en su texto.** Que sea PostgreSQL válido
>    y que aplicarlo dos veces no falle es **T20, MANUAL (humano)**, y la
>    revocación sobre datos reales es **T23**. Un doble de conexión no puede
>    demostrar ninguna de las dos.
>
> ### Estado del arnés al cerrar
>
> `bash harness/init.sh` → **ENTORNO LISTO**. Cobertura de líneas cambiadas
> **98,7 %** (1 171/1 186, umbral 80 %), frente al **47,6 %** en `[KO]` con el
> que empezó la sesión. 2 253 tests del servicio `api` en verde; **59** avisos
> de `ruff`, los mismos que antes de esta tanda.

---

> ## Estado al 2026-09-11 · **F-025: hecho el bloque 4; los requisitos derogados ya llevan su constancia fechada**
>
> Entrega **parcial y pedida asi**: el encargo acotaba el trabajo al **bloque
> 4** de `specs/F-025-confirmacion-unica/tasks.md` (T14-T18) y mandaba parar
> ahi. **Los bloques 5 y 6 no se han empezado.** Informe completo, con la fase
> RED y las evidencias: **`progress/impl_F-025.md`**, de la §20 en adelante.
>
> ### Lo que hay hecho
>
> - **T14** - `specs/F-012-grafico-sigrid/requirements.md`: los **cinco**
>   recuadros de enmienda, uno bajo cada requisito (R63 **DEROGADO**, R22, R21,
>   R49, R50). Cada uno con fecha `2026-09-11`, la premisa original **citada
>   literal**, que la invalido y **quien lo decidio, con sus palabras**:
>   *«quiero que al darle a archivar los partes aptos me pida confirmacion como
>   ahora, y al confirmar ya haga el proceso de cierre»* y, ante la objecion de
>   que esa pantalla protege de cerrar la incidencia equivocada, *«no hace
>   falta ensenar nada»*. **+77 lineas, CERO suprimidas.**
> - **T15** - `specs/F-009-cierre-sigrid/requirements.md`: la nota bajo
>   R8/R10. Siguen vigentes y **se cumplen mejor**; R12-R15 igual; hay **UNA
>   sola** confirmacion, **no ninguna**; y R21 **no se vuelve a derogar**, que
>   ya lo estaba desde el 2026-09-06. **+21 lineas, CERO suprimidas.**
> - **T16** - el repaso formal de las retiradas en `test_f009_front.py` y
>   `test_f012_front.py`: cotejo nombre a nombre contra `e250775`. **Ningun
>   test desaparecido sin sustituto**; las bajas netas son fusiones. Tapado un
>   hueco: el control negativo de R9 vigilaba cinco de los siete campos de la
>   tarjeta retirada.
> - **T17** - `docs/ARCHITECTURE.md`, paso 7b y punto 6 de «Semantica de
>   dominio»: la confirmacion es **una sola** y el calculo previo ocurre **en
>   la misma llamada** que escribe.
> - **T18** - la constancia de que `azure-apps/postventa_incidencias.md` **no
>   se toca**, con el repaso hecho punto por punto (endpoints, cuerpos,
>   variables, tablas y las cinco puertas) en la §26 del informe. Ese
>   repositorio queda **limpio**.
> - **`services/postventa-api/tests/test_f025_documentacion.py`** nuevo:
>   **21 tests** que vigilan los recuadros, la nota y las dos precisiones de
>   arquitectura. Fase RED con **17 rojos de 21**, pegada en la §23 del
>   informe.
>
> ### Lo que cambia para quien lo lea dentro de seis meses
>
> Antes, quien abriera R63 de F-012 leia que el front tiene que ensenar dos
> dry-run antes de confirmar, y «arreglaria» el front para cumplir un requisito
> que ya no rige. Ahora lee el requisito **entero, sin una palabra borrada**, y
> debajo por que cayo y quien lo decidio. **Ningun fichero de produccion se ha
> tocado en esta tanda**: lo unico que cambia en codigo son dos aserciones de
> test.
>
> ### Tres avisos que siguen en pie
>
> 1. **La pantalla no se ejecuta en ninguna suite.** Sigue igual que tras el
>    bloque 3: son aserciones sobre el TEXTO de `index.html` y `app.js`. Nadie
>    ha abierto la pantalla. Es lo primero del bloque 5.
> 2. **`AVISO_CADUCADA_CIERRE` de `js/confirmacion.js` se queda sin llamante**
>    en produccion, y **no se retira a proposito**: `design.md` §9.3 deja ese
>    fichero fuera del alcance. Deuda menor declarada, con su motivo, en la
>    §24.5 del informe.
> 3. **La constancia de T18 es un repaso, no un test**: `azure-apps/` vive en
>    otro repositorio y ninguna suite lo lee. Si una feature futura cambia un
>    cuerpo o una variable, ese documento se quedara desactualizado sin que
>    nada se ponga rojo.
>
> ### Por donde sigue
>
> **Bloque 5 (T19-T23)**, `MANUAL (humano)`: escribe en el historico de una
> **obra en uso**. Empieza por **T19**, el guion
> `progress/guion_bloque5_F-025.md`, que todavia **no existe**. Reglas que no
> se negocian y que vienen de F-012: autorizacion expresa del responsable para
> la incidencia concreta, `CIERRE_HABILITADO` abierto **solo** durante la
> prueba y releido al cerrarlo, y **ninguna escritura desde un puesto de
> trabajo**. Despues, el **bloque 6** (mutacion y cierre), que lleva el lider.
>
> ### Estado del entorno
>
> `bash harness/init.sh` en **verde**: 62 + 2.144 (13 skipped) + 185 tests,
> cobertura de lineas cambiadas **99,0 %** (umbral 80, nivel critico). **13**
> commits locales en `feature/F-025-confirmacion-unica` desde el cierre de F-012
> (`e250775`), **cinco** de esta tanda, sin `push`.
> `features.json` **sin tocar**.

> ## Estado al 2026-09-11 (tanda 2) · **F-025: hechos los bloques 2 y 3; la pantalla YA pide UNA sola confirmacion** _(superado por el bloque de arriba)_
>
> Entrega **parcial y pedida asi**: el encargo acotaba el trabajo a los
> **bloques 2 y 3** de `specs/F-025-confirmacion-unica/tasks.md` (T7-T13) y
> mandaba parar ahi. **T14 en adelante no se ha empezado.** Informe completo,
> con la fase RED y las evidencias: **`progress/impl_F-025.md`**, de la §11 en
> adelante.
>
> ### Lo que hay hecho
>
> - **Bloque 2 (T7-T9)** - `js/app.js`: `confirmarArchivo` recorre
>   `pendientesDeCircuito` llamando a `ejecutarCircuito` por la MISMA cola,
>   envuelto en `conGuardaDeTanda`. Desaparecen `_archivarUno`,
>   `_adjuntarYCerrarUno`, `_cerrarUno`, `_dryRunUno`, `pedirDryRunCierre`,
>   `hayDryRun`, `dryRunDe` y `dryRunGraficoDe`. Entran `totalTanda`,
>   `parte.paso`, la fase `archivando_y_cerrando` y las dos banderas de las
>   puertas de entorno.
> - **Bloque 3 (T10-T13)** - `index.html`: las secciones «Archivar» y «Cerrar
>   en Sigrid» fundidas en UNA, con **un** boton, **una** confirmacion con el
>   texto aprobado en P3, el paso por parte y el **numero de incidencia** en el
>   resumen (R37). Sin identidad el boton se deshabilita (P2). Los dos
>   recuadros de F-012 R65 **siguen intactos**.
> - **`tests/test_f025_front.py`** nuevo: **57 tests**, casi todos control
>   negativo. Fase RED con 44 rojos sobre codigo real, pegada en el informe.
>
> ### Lo que cambia para quien lo pruebe
>
> El front pasa de **cinco** llamadas por parte a **tres**, y de **dos**
> confirmaciones a **una**. El backend **no cambia ni una linea**: lo que
> desaparece es la pantalla, no la verificacion — la comprobacion previa se
> sigue haciendo dentro de la misma llamada que escribe.
>
> ### Tres avisos que hay que tener a la vista
>
> 1. **La pantalla no se ejecuta en ninguna suite.** Los 57 tests son
>    aserciones sobre el TEXTO de `index.html` y `app.js`. Se ha cotejado a
>    mano que los 35 identificadores que invoca el HTML existen en `app.js`, y
>    `node --check` pasa, pero **nadie ha abierto la pantalla**. Es lo primero
>    que hay que hacer en el bloque 5.
> 2. **La bandera de «el ERP esta cerrado»** la ven los partes que aun no han
>    arrancado, no los que ya estan en vuelo en la cola: como mucho dos `503`
>    de mas. Aceptado, y **escrito en el codigo**, no descubierto en la review.
> 3. **T16 (bloque 4) esta medio consumida**: 28 tests de F-009 y F-012
>    apuntaban a la pantalla retirada y habia que adaptarlos para no dejar la
>    suite en rojo. Cada retirada deja su control negativo y cita R38/R39; la
>    tabla con las quince entradas esta en la §16 del informe. **El bloque 4
>    tiene que revisarla, no repetirla.**
>
> ### Por donde sigue
>
> **Bloque 4 (T14-T18)**: los cinco recuadros de enmienda en
> `specs/F-012-grafico-sigrid/requirements.md`, la nota en
> `specs/F-009-cierre-sigrid/requirements.md`, el repaso de T16,
> `docs/ARCHITECTURE.md` (R47) y la constancia de R48. Despues, el **bloque 5**
> contra el ERP, que ahora **si tiene algo que probar**.
>
> ### Estado del entorno
>
> `bash harness/init.sh` en **verde**: 62 + 2.123 (13 skipped) + 183 tests,
> cobertura de lineas cambiadas **99,0 %** (umbral 80, nivel critico). **Tres**
> commits locales en `feature/F-025-confirmacion-unica`, sin `push`.
> `features.json` **sin tocar**.

> ## Estado al 2026-09-11 (tanda 1) · **F-025: hechos los bloques 0 y 1; el front todavia pedia DOS confirmaciones** _(superado por el bloque de arriba)_
>
> Entrega **parcial y pedida asi**: el encargo acotaba el trabajo a los **dos
> primeros bloques** de `specs/F-025-confirmacion-unica/tasks.md` (T1-T6).
> **T7 en adelante no se ha empezado.** Informe completo, con la fase RED y las
> evidencias: **`progress/impl_F-025.md`**.
>
> ### Lo que hay hecho
>
> - **Bloque 0 (T1, T2)** - `services/postventa-api/tests/test_f025_sin_dry_run_previo.py`,
>   27 tests. Fija con una **bitacora ordenada compartida por los dos dobles**
>   el hallazgo del que depende la feature entera: un `commit` **sin ninguna
>   llamada previa** hace su comprobacion contra el ERP y la pasarela **dentro
>   de la misma invocacion** y solo entonces escribe. Mas los **siete
>   control-negativo** de `requirements.md` 6 (R29-R35).
> - **Bloque 1 (T3-T6)** - `js/pipeline.js` gana `pendientesDeCircuito`,
>   `porcentajeDeTanda`, `ejecutarCircuito`, `conGuardaDeTanda` y
>   `hayTandaEnCurso`; `tests_js/circuito.test.js` los cubre con **37 tests**.
>   El orden de las tres escrituras deja de vivir en `app.js`, que no tiene
>   tests.
>
> ### Lo que NO hay, y conviene no confundirlo
>
> **El comportamiento de la pantalla no ha cambiado ni un poco.** `js/app.js` e
> `index.html` estan intactos: el front sigue pidiendo **dos** confirmaciones y
> **cinco** llamadas por parte. `ejecutarCircuito` esta escrito y **no lo llama
> nadie** todavia.
>
> Tampoco se ha tocado: ni `paso_grafico.py` ni `paso_cierre.py` (regla dura de
> la feature), ni las enmiendas a F-009 y F-012 (bloque 4), ni la verificacion
> contra el ERP (bloque 5, MANUAL), ni la campana de mutacion (T24).
>
> ### Por donde sigue
>
> **Bloque 2 (T7-T9)**, en `js/app.js`, con `tests/test_f025_front.py` nuevo.
> El informe trae en su 7.2 el esqueleto de `confirmarArchivo` y **dos avisos
> que conviene leer antes de escribir codigo**: que la bandera `erpCerrado` no
> la veran los partes que ya esten en vuelo en la cola, y que
> `reintentarCierre` se queda sin funcion si T7 borra `_cerrarUno` (la salida
> limpia es reintentar por `ejecutarCircuito`, que ya se salta lo que consta
> hecho).
>
> ### Estado del entorno
>
> `bash harness/init.sh` en **verde**: 62 + 2.123 + 130 tests, cobertura de
> lineas cambiadas **99,0 %** (umbral 80, nivel critico). Dos commits locales
> en `feature/F-025-confirmacion-unica`, sin `push`. `features.json` **sin
> tocar**.

> ## Estado al 2026-09-11 · **el bloque 9 de F-012 se ejecutó contra el ERP y FUNCIONÓ; se cierra con cinco escenarios sin verificar**
>
> **Lo primero, porque es el hito que esta feature perseguía**: el
> responsable del proyecto recorrió el **circuito completo** contra el ERP de
> producción sobre la incidencia **`RS26.09/0150`** de la obra **`0626`**. Un
> parte subido por la web quedó **archivado**, **adjunto a su reclamación** y
> la **reclamación cerrada**. Sus palabras: ***«ha funcionado perfectamente»***
> y ***«cerró una y lo hizo bien»***. Es el **primer cierre real** de este
> servicio, y fue **con su parte dentro**: la anomalía que F-009 aceptaba como
> riesgo no llegó a producirse ni una vez.
>
> ### La evidencia objetiva, medida en `appi-postventa-dev`
>
> `az monitor app-insights query`, 2026-09-11. **Las cinco respuestas, `200`**:
>
> | Hora (UTC) | Ruta | Código | Duración |
> |---|---|---|---|
> | `08:27:15` | `archivar` | 200 | 1.756 ms |
> | `08:27:29` | `adjuntar` | 200 | **13.134 ms** |
> | `08:27:42` | `cerrar` | 200 | 4.424 ms |
> | `08:28:03` | `adjuntar` | 200 | **8.471 ms** |
> | `08:28:12` | `cerrar` | 200 | 472 ms |
>
> Los dos pares son **la comprobación previa y la escritura**: dry-run antes de
> cada `commit`, como manda el guion.
>
> **El número que R37 pedía anotar**: `adjuntar` tarda **13,1 s** en la primera
> llamada, frente a los **35 s** de `SIGRID_TIMEOUT_S`. Hay margen —21,9 s—,
> pero es **con diferencia el paso más lento**: el **37,5 %** del tope, **28
> veces** lo que tarda el cierre. **Con un parte más pesado se acerca**, y
> pasarse no da un error claro: da un `502` con el ERP en estado desconocido.
> **Lo que no se midió y hacía falta**: el **tamaño en bytes** del parte usado,
> así que los 13,1 s no se pueden extrapolar.
>
> ### El hallazgo de procedimiento: **el front desplegado no llevaba F-012**
>
> Durante la prueba el circuito **se paró después de archivar**, sin llamar a
> `adjuntar` ni a `cerrar` y **sin error visible**. Se diagnosticó con los
> registros —ni una llamada a esas dos rutas, luego no era el backend— y
> descargando el **JavaScript servido**, que no contenía el paso de adjuntar.
> Se resolvió con `infra/desplegar_front.ps1 -SoloFront`. **El guion daba por
> hecho que basta con desplegar el backend, y no basta**: queda como **H11** y
> el **Paso 0 (2) y la P2 están corregidos** para desplegar **las dos partes**
> y comprobar el JS servido. La lección vale para cualquier feature con front y
> backend: **un front al que le falta un paso no falla, no hace nada**.
>
> ### Qué se marcó, y qué queda SIN verificar
>
> Se ejecutó **el camino feliz y poco más**. Marcadas **T25, T27 y T32** —y aun
> esas, con pasos sin recorrer, anotados uno a uno en sus casillas— más **T34**.
> **Sin marcar, con el motivo y qué se pierde en cada casilla**:
>
> | Tarea | Escenario sin verificar |
> |---|---|
> | **T26** | el `commit` del cierre **rechazado** por no constar adjuntado (**R2**, la razón de ser de la feature). Su dry-run sí se ejecutó |
> | **T28** | **idempotencia** de extremo a extremo: nada se repitió |
> | **T29** | **«adjuntado pero no cerrado»** y el botón que saca de ahí: adjuntar y cerrar fueron seguidos (9 s) y ese estado no llegó a existir |
> | **T30** | **reintento sobre lo ya cerrado** — el más probable en uso normal y **el más barato de cerrar**: basta repetir el circuito |
> | **T31** | **rechazo de la pasarela** sin escritura; ya el guion lo daba por prescindible |
>
> Y transversal: **no se ejecutó ni uno de los scripts de lectura de `infra/`**.
> No está comprobado el `filas_afectadas: 3` de R27, ni que el binario dentro
> del ERP coincida **byte a byte**, ni que `dbo.log` no haya crecido por el
> gráfico (R36), ni el **huso** de la fila de auditoría del cierre, ni las dos
> trazas locales. **Todo eso es solo lectura y sigue disponible**: la
> incidencia, el gráfico y la fila están en el ERP.
>
> ### La decisión del responsable, fechada
>
> **El 2026-09-11 decidió cerrar F-012 así**, con esos cinco escenarios sin
> ejecutar: la feature se da por buena **con el camino principal verificado en
> producción**. Está escrito en `progress/guion_bloque9_F-012.md` §9.5 y en
> `progress/impl_F-012.md` §13.5 para que **las casillas vacías no se lean como
> un olvido**.
>
> ### Estado del entorno y qué queda pendiente
>
> - **`CIERRE_HABILITADO` = `false`**: la ventana se leyó (seguía `true`), se
>   cerró y **se releyó** para confirmarlo. **Falta** el paso 3 de T32:
>   comprobar en el borde que responde `503`.
> - **`SIGRID_GRATIPIDE_PARTE` sigue en 35** (nunca se cambió: T31 no se hizo).
> - **Pendiente**: `azure-apps/postventa_incidencias.md` —ya no es verdad que
>   «no se ha ejecutado ni un cierre real»— y `progress/guion_bloque8_F-009.md`,
>   que sigue nombrando la obra genérica.
> - **El `status` de F-012 no lo toca este encargo**: lo lleva el líder.
>
> **Encargo documental**: ningún código, ningún test, ninguna llamada a Azure,
> Sigrid, SharePoint ni PostgreSQL —toda la evidencia venía medida—.
> `bash harness/init.sh` **en verde**: 62 tests del arnés en 14,97 s y la
> puerta de cobertura en **99,0 % de 1.079 líneas**. Ficheros tocados:
> `progress/guion_bloque9_F-012.md`, `specs/F-012-grafico-sigrid/tasks.md`,
> `progress/impl_F-012.md` y este.

> ## Estado al 2026-09-11 · **la documentación de la verificación de F-012 ya nombra el caso concreto, con constancia fechada de quién cambió la premisa**
>
> Encargo **documental**: ningún código, ningún test, ninguna llamada a Azure,
> Sigrid, SharePoint ni PostgreSQL. `bash harness/init.sh` **en verde**
> (62 tests del arnés en 5,51 s; puerta de cobertura 99,0 % de 1.079 líneas; las
> suites de `api` y `front` **de caché**, legítimo porque no se tocó un solo
> `.py`).
>
> **Qué cambió.** Donde se decía «obra de prueba **404**, nunca una obra real»
> ahora se dice **incidencia `RS26.09/0150` (tipo 708) de la obra `0626`**, que
> **no es una obra de pruebas: está en uso**. La advertencia anterior **no se
> ha borrado**: en cada documento queda un recuadro fechado —calcado del de la
> enmienda del 2026-09-03 bajo el R28 de `specs/F-010-despliegue/requirements.md`—
> con la premisa original **literal**, quién la levantó (**el responsable del
> proyecto, el 2026-09-10**, tras planteárselo de forma explícita) y qué implica:
> la incidencia de la comprobación y su cierre quedan **en el histórico de una
> obra en uso**, con el documento adjunto colgado de ella.
>
> | Fichero | Qué se tocó |
> |---|---|
> | `progress/guion_bloque9_F-012.md` | Nota fechada arriba; regla del encabezado; P5 y **P6**; §3; casilla de T25; T25, T31 y T32; §7 (datos); H7 y H10 |
> | `specs/F-012-grafico-sigrid/requirements.md` | Término del glosario + recuadro de enmienda; trazabilidad de los `MANUAL` |
> | `specs/F-012-grafico-sigrid/design.md` | H5, D-B, mapa de ficheros, orden (b), P5 del §14 y **§15 con su propia enmienda** |
> | `specs/F-012-grafico-sigrid/tasks.md` | T22, encabezado y regla dura del bloque 9, P5, P6, T31 |
> | `harness/features.json` | **Solo** la descripción de F-012 (`status` intacto: `in_progress`); `BACKLOG.md` regenerado |
> | `progress/peticion_posventa_prueba_F-012.md` | Nota interna fechada, y el correo reenviable dice **a Ana y Alicia** que la 0626 está en uso y dónde queda lo que confirmen |
>
> **La consulta del §15 no se ha reinventado**: Q1 y Q2 se quedan como estaban
> —siguen dando estado y nº de gráficos de la incidencia— y solo se ajusta el
> parámetro de Q0 a `['0626', '626']`.
>
> **Lo que NO cambia, y se comprobó que sigue escrito en los seis ficheros**:
> comprobación previa (dry-run) antes de cada escritura; **autorización expresa
> del responsable por incidencia concreta —que aquí se dice explícitamente que
> gana peso, no lo pierde—**; `CIERRE_HABILITADO` como **interruptor único**
> del documento adjunto y del cambio de estado; y ninguna escritura desde un
> puesto de trabajo.
>
> **Queda fuera de este encargo y sigue nombrando la obra genérica** (no se
> tocó): `infra/15_reclamaciones_obra_prueba.ps1` —su `-CodigoObra` sigue con
> `404` por defecto, así que **hay que pasarle `0626` a mano**, y así está
> avisado en el guion y en la spec—, `progress/guion_bloque8_F-009.md`,
> el `blocked_by` de **F-009** en `features.json`, `docs/INTEGRACION.md` §520 y
> `specs/F-024-datos-parte-sigrid/tasks.md`. Los informes ya cerrados
> (`impl_F-012.md`, `review_F-012.md`) no se tocan: son histórico.
>
> **Qué falta para el bloque 9**: que el responsable dé de alta `RS26.09/0150`
> en el ERP, y que el parte `muestras/parte_prueba_RS26.09-0150.pdf` se
> imprima, se firme a mano y se escanee. T25–T32 siguen sin ejecutar.

> ## Estado al 2026-09-11 · **El entorno desplegado ya puede escribir: Paso 0 hecho, F-012 desplegada y la ventana de archivo abierta**
>
> **Decisión del humano, y cambia una premisa**: la verificación de F-012 se
> hace sobre la **obra 0626, que es una obra REAL**, y no sobre una obra de
> pruebas. Se le planteó explícitamente y lo reafirmó. La incidencia del caso
> es **`RS26.09/0150`**, que el humano crea en Sigrid; su parte de trabajo
> está preparado en `muestras/parte_prueba_RS26.09-0150.pdf` (no versionado,
> datos inventados salvo el código de obra y el de incidencia), **pendiente
> del nombre de la promoción**, de imprimir, firmar a mano y escanear.
>
> ### Lo que ya está hecho contra el entorno desplegado
>
> | Paso | Estado |
> |---|---|
> | Secretos de Sigrid en el Key Vault | hecho, desde el `.env` del puesto |
> | Referencias a Key Vault | **11 de 11 resueltas** |
> | Backend desplegado **con el código de F-012** | hecho: `adjuntar` está en el aire |
> | Configuración de la pasarela (tipo 708, clase 35, escritura documental) | ya estaba desde el 2026-09-06 |
> | Ventana de **archivo** | **abierta** |
> | Ventana del **ERP** (`CIERRE_HABILITADO`) | **cerrada**, y así sigue |
>
> Para subir los dos secretos desde el `.env` se escribió un script **fuera del
> repositorio**, en el home del humano: lee los dos nombres del mapa de
> `00_vars_postventa.ps1`, no imprime ningún valor y no toca el `.env`.
>
> ### Dos correcciones de la sesión
>
> 1. **Seis ayudantes de la suite leían el `.env` del puesto** pese a prometer
>    lo contrario, y el `.env` de hoy los puso en rojo. Arreglados con
>    `_env_file=None`. La suite del api: **2.096 pasan, 13 saltados**.
> 2. **La caché de `init.sh` tapó ese rojo** durante toda una sesión, porque
>    mira al árbol commiteado y no a los ficheros ignorados. Es del arnés y se
>    llevó a `arnes-base` como **encargo 1.7.12** (commit `9ff2224` allí).
>
> ### Lo que queda pendiente y no se ha hecho
>
> - **Cambiar la obra 404 por la 0626** en `progress/guion_bloque9_F-012.md`,
>   en la spec de F-012 y en `progress/peticion_posventa_prueba_F-012.md`, con
>   constancia fechada de que la premisa «nunca una obra real» la levantó el
>   humano el 2026-09-10. **Sin hacer**: el subagente que iba a hacerlo lo
>   bloqueó el clasificador de permisos de la sesión.
> - Comprobar el login del ERP de quien vaya a operar (`infra/20_login_sigrid.ps1`).
> - El bloque 9 entero: T25–T32 siguen sin ejecutar y sin marcar.
>
> **F-012 sigue `in_progress`**, F-009 `blocked` y F-024 `spec_ready`.

> ## Estado al 2026-09-11 · **utillaje de puesta en marcha del bloque 9 (F-012): entregado; `init.sh` en ROJO por un defecto ajeno**
>
> **`infra/19_ventana_escritura.ps1`** y **`infra/20_login_sigrid.ps1`**
> (nuevos): las dos operaciones que hasta hoy vivían como fragmentos sueltos
> dentro de `progress/guion_bloque9_F-012.md`. El 19 consulta, abre y cierra
> `CIERRE_HABILITADO` —por omisión **solo lee**; `-Abrir` avisa de que la
> ventana es **una sola** para el gráfico y para el cierre (D-B, §0.2) y exige
> teclear `ABRIR`; `-Cerrar` no pregunta, porque cerrar siempre es seguro; y
> tras escribir **relee** y dice el estado real—. El 20 deriva el login
> candidato como `derivar_login_candidato` y lo comprueba contra `dbo.usu` con
> la consulta del servicio (`SQL_USUARIO`, importada por el test), con veredicto
> de tres casos. **Ninguno de los dos se ha ejecutado**: nada contra Azure,
> Sigrid, el PostgreSQL compartido ni SharePoint, ni lecturas.
>
> **31 tests nuevos** en `test_f012_scripts_infra.py`, escritos **antes** que
> los scripts (traza RED pegada en el informe), y los dos entran en el censo
> `scripts_entregados()` de `test_f010_scripts_infra.py`. `ParseFile`: 0 errores
> de sintaxis en ambos. `ruff`: 58 avisos, la deuda previa exacta.
>
> **BLOQUEO, y no es de este trabajo.** `bash harness/init.sh` termina en rojo
> por **un** test, `test_f012_fabrica_grafico.py::test_f012_r40_la_tercera_puerta_nombra_todas_las_variables_que_faltan`.
> Su ayudante `_ajustes()` promete «sin tocar el `.env` de nadie» y no lo
> cumple: `Ajustes(**entorno)` es `pydantic-settings` y lee del `.env` todo lo
> que no se le pase. El `.env` de este puesto ya define `SIGRID_API_BASE_URL` y
> `SIGRID_API_KEY` (nombres; los valores no se han mirado), así que la fábrica
> solo echa en falta `SIGRID_BASE_DATOS` y el test, que exige las tres, falla.
> Con ese test deseleccionado, **2 095 pasan, 13 saltados, en 88 s**. Falla
> también ejecutando **solo su fichero**, que no importa nada de lo tocado aquí.
>
> Dos remedios, y los dos son decisión del humano: **(a)** una línea,
> `return Ajustes(_env_file=None, **entorno)` —comprobado que restituye los tres
> nombres—, que es lo que ya declara el propio `conftest.py`; o **(b)** quitar
> esas variables del `.env`, que este agente tiene **prohibido** tocar. No se ha
> aplicado ninguno: es la suite de una feature ya revisada, con la mutación
> cerrada y sus 5 supervivientes aceptados.
>
> **Hallazgo que conviene no perder:** el primer `init.sh` de la sesión salió en
> verde porque sirvió la suite del api **de la caché** («árbol sin cambios desde
> el último verde»). La caché puede tapar un rojo que depende del entorno, y
> este llevaba tapado desde que cambió el `.env`.
>
> Detalle completo: **`progress/impl_utillaje_puesta_en_marcha.md`**.
> No se tocó `features.json`, ni `tasks.md`, ni se relanzó la mutación (lo
> entregado es PowerShell y tests: `harness/alcance.py` solo mide `.py`).

> ## Estado al 2026-09-07 · **petición a Posventa para probar el circuito completo (F-012), escrita**
>
> **`progress/peticion_posventa_prueba_F-012.md`** (nuevo): la petición a Ana
> Bello y Alicia Echevarría, redactada para **reenviarse tal cual** por correo,
> calcada de `progress/peticion_posventa_prueba_url_F-023.md`. Sin jerga
> técnica: solo términos del ERP («gráficos», «Importa», «Procesos → 3. Cerrar
> parte», «reclamación», «unidad»).
>
> Lleva lo que hay que preparar **antes** (dos o tres reclamaciones en la obra
> **404**, sus partes impresos, firmados a mano y escaneados, **uno con una
> observación manuscrita** para ver que la aplicación lo aparta en vez de
> cerrarlo), los pasos del front tal y como están hoy en `index.html` y
> `js/app.js` —trocear, revisar, «Archivar los partes aptos», «Ver qué pasaría
> (no cierra nada)», «Cerrar las incidencias»—, los dos avisos que no pueden
> ser sorpresa (el botón cierra **todos** los partes en pantalla; lo confirmado
> se escribe de verdad), las preguntas de vuelta, la **P1/D2** sobre `PV002`
> marcada aparte, lo que no deben hacer y a quién avisar.
>
> **No se envía todavía**: la nota para el humano de la cabecera exige el
> bloque 9 en verde, el alta de los logins de Sigrid de las dos con
> `infra/07_alta_usuario_sigrid.ps1` —el de Alicia es **`aechevarria`**, que no
> coincide con el prefijo de su correo— y las dos dentro de
> `posventa-usuarios`. La dirección del portal va como marcador
> `<la dirección del portal>`: no está en ningún documento versionado.
>
> `bash harness/init.sh` **en verde**. Este encargo solo escribe Markdown en
> `progress/`: no se relanzó la mutación, no se tocó `features.json` ni se marcó
> ninguna tarea de `tasks.md`. **Nada ejecutado** contra Azure, Sigrid,
> `sigrid-api`, el PostgreSQL compartido ni SharePoint —ni lecturas—, y **no se
> ha enviado ningún correo**.

> ## Estado al 2026-09-06 (noche, 6) · **F-024 con spec: `spec_ready`, a la espera de la aprobación del humano**
>
> `specs/F-024-datos-parte-sigrid/` (commit `2ce37d6`, escrita por el
> spec-author sobre la rama de F-012 porque depende de `postventa.graficos`).
> Tres piezas: cinco campos nuevos de extracción con prompt `version: "2"` y
> sin reextraer lo antiguo; `reclamacion_ide` en `cierres`; y la vista
> `postventa.v_partes_sigrid` como contrato de lectura para el datamart, con
> la petición a `datamart-seg-anual` redactada en design §12.
>
> **Seis preguntas para el humano** (design §13), con recomendación: P1
> `observaciones` en la vista (no; `tiene_observaciones`); P2 `obra_ide`/
> `upv_ide` (no); P3 campos nuevos editables en la tarjeta (sí); P4 el
> encuadre del líder decía «sin mutación» pero `harness/rigor.json` la exige
> en `estandar` sin tope de supervivientes: manda `rigor.json`; P5 no
> reextraer partes antiguos; P6 el rol de lectura del datamart como feature
> aparte, porque `CREATE ROLE`/`GRANT` son del humano y fuera del schema.
>
> **F-012 sigue `in_progress`** con el bloque 9 pendiente del humano; F-024 no
> se implementa hasta que F-012 cierre. Nada ejecutado contra Azure ni el ERP.

> ## Estado al 2026-09-06 (noche, 5) · **los 5 supervivientes de mutación de F-012, aceptados por el humano**
>
> «Acepto los 5 supervivientes de mutación». Consta en la cabecera de
> `progress/mutacion_F-012.md` y la precondición documental **D1** del guion
> del bloque 9 queda marcada. Con ello **C4 bis está cerrado para F-012**.
> Queda abierta **D2** (confirmar `PV002` con Posventa) y todo lo técnico del
> bloque 9, que es del humano. F-012 sigue `in_progress`.

> ## Estado al 2026-09-06 (noche, 4) · **guion del bloque 9 de F-012 escrito, y el del bloque 8 de F-009 corregido**
>
> - **`progress/guion_bloque9_F-012.md`** (nuevo): el procedimiento que sigue el
>   humano para T25–T32, calcado del de F-009. Toda escritura sobre
>   **reclamaciones de la obra de prueba 404**, dry-run antes de cada commit y
>   **autorización expresa por incidencia**. Ni un valor sensible: marcadores
>   `<...>`, y la lectura de las App Settings de `sigrid-api` va filtrada con
>   `--query` para no volcar sus credenciales a ninguna consola.
> - **`progress/guion_bloque8_F-009.md`** (corregido, cambios quirúrgicos con
>   fecha): nota arriba explicando que el bloque 9 de F-012 ejecuta de hecho un
>   cierre completo sobre la 404; **P5** pasa de Mirasierra a la obra 404 con el
>   gráfico ya adjuntado; **T22** espera el bloque `grafico` (R49) y no
>   `aviso_sin_grafico` (R48 lo derogó); **T24** exige que el parte conste
>   `adjuntado` (R2) o pasa antes por `/api/adjuntar`.
> - **Diez hallazgos** en §8 del guion nuevo. Los que no estaban escritos:
>   `/api/adjuntar` es `multipart` y **poner `Content-Type` la rompe en
>   silencio**; `filas_afectadas: 0` significa **cosas opuestas** en `adjuntar`
>   y en `cerrar`; el reintento tras un `502` es **seguro en uno y prohibido en
>   el otro**; T28 capa 2 necesita borrar una fila de `postventa.graficos` y no
>   había forma escrita; y **T31 no puede usar la reclamación de T27** porque la
>   idempotencia de capa 1 cortaría antes de llegar a la pasarela.
>
> `bash harness/init.sh` **en verde**, con la puerta de cobertura en las mismas
> **1.079 líneas cambiadas al 99,0 %**: este encargo solo escribe Markdown en
> `progress/`, así que **no se relanzó la mutación** ni cambió el alcance.
>
> **No se ejecutó nada** contra Azure, Sigrid, `sigrid-api`, el PostgreSQL
> compartido ni SharePoint —ni lecturas—: lo que el guion afirma sale del código
> y de los scripts leídos. **No se marcó ninguna tarea** de `tasks.md` ni se
> tocó `harness/features.json`. Detalle en `progress/impl_F-012.md` §12.
>
> **Pendiente para el humano**: **D1** de §2 del guion nuevo, aceptar los 5
> supervivientes de mutación declarados equivalentes; y **D2**, confirmar con
> Posventa que `PV002` (`gratipide` 35) es la clase correcta para un parte
> firmado. Ninguna bloquea T25; las dos se cierran antes de dar el bloque 9 por
> bueno.

> ## Estado al 2026-09-06 (noche, 3) · **post-review de F-012: D1, D2 y S9 hechas**
>
> Las **dos correcciones «debe corregirse»** de `progress/review_F-012.md` §6 y
> la sugerencia **S9**, que además era una mejora genérica del arnés.
>
> - **D1** · `infra/16_grafico_sigrid.ps1`: la casilla «bytes descargados»
>   imprimía `$huella.Length` —la cadena hexadecimal del sha256, siempre 64—.
>   Ahora mide `$respuesta.Content.Length`, **capturado antes** de que el script
>   suelte la respuesta a `$null`. Con test de texto que fija además ese orden.
> - **D2** · los comentarios de `js/api.js` y `js/app.js` dejaban de describir
>   el sistema real: contaban el aviso «quedará cerrada sin el parte» que **R48
>   derogó**. Reescritos con el bloque `grafico` (R49) y con la derogación
>   nombrada. **Sin cambios funcionales.**
> - **S9** · `comando_de()` de `harness/mutacion.py` no emitía `--base`, así que
>   la línea «Generado por» de un informe de mutación no reproducía nada cuando
>   la rama nace de otra feature —el caso de F-012—. Corregido, con seis tests
>   nuevos, y corregidas las dos líneas de `progress/mutacion_F-012.md`.
> - **Propagado a `arnes-base`** por la regla obligatoria: estaba en `main` y
>   limpio, así que se portó pieza a pieza (allí va por la 1.7.9 y aquí por la
>   1.5.2), con **`VERSION` a 1.7.10** y entrada en `GUIA_INSTALACION.md`.
>   Commit local `6aa4335`, sin `push`. Su suite: **347 passed, 1 skipped**.
>
> `bash harness/init.sh` **en verde**: 62 tests del arnés, **2.055** en `api`
> (13 saltados), 130 en `front`, puerta de cobertura **99,0 % de 1.079 líneas
> cambiadas** (idéntica) y `ruff` en **58 avisos, la deuda previa exacta**. El
> analizador de PowerShell da el script 16 **sin errores de sintaxis**.
>
> **No se relanzó la campaña de mutación**: ninguna línea de producción del
> alcance de F-012 cambió (un `.ps1`, comentarios de `.js` y `harness/`, que no
> entra en el alcance). **No se tocó `features.json`**: el estado de F-012 lo
> decide el líder. Detalle en `progress/impl_F-012.md` §11.
>
> **Pendiente**: las ocho sugerencias restantes de la review (S1–S8), que el
> encargo no pedía.

> ## Estado al 2026-09-06 (noche, 2) · **T33 hecha: los 35 supervivientes de la mutación, cazados o justificados**
>
> Se han analizado **uno a uno** los 35 supervivientes de la primera pasada de
> la campaña de mutación de F-012: **30 eran huecos reales de test** y **5 son
> equivalentes** (cuatro valores por omisión que ningún sitio de producción
> llega a usar y un campo que nadie lee aguas abajo), con la justificación
> escrita y comprobable con un `grep`. **Aceptarlas es del humano**: es lo
> que pide, literalmente, la verificación de T33.
>
> **22 tests nuevos y dos ampliados**, sin tocar ni una línea de producción:
> los 30 eran huecos de test, no defectos. Antes de relanzar la campaña se
> comprobó cada mutante por separado, a mano: **los 30 mueren**.
>
> **Segunda pasada**: **101 mutantes, 96 muertos, 5 supervivientes, 0 timeouts** en 922,8 s con 8 workers, y los cinco son exactamente los cinco equivalentes. Informe con las dos pasadas y el análisis
> completo en `progress/mutacion_F-012.md` —**sin ningún `PENDIENTE`**— y la
> tabla resumen en `progress/impl_F-012.md` §7.2.
>
> Los dos hallazgos que valía la pena tener: el `or` de la puerta de R14 en
> `paso_grafico.py:273` (con `and`, un parte **no apto** pasaba si el destino
> decía `archivo_y_cierre`, y el destino llega del formulario) y los cuatro
> `bool(datos.get(..., False))` de `graficos.py` (con `True` por omisión, un
> `200` con un cuerpo que no es el del contrato se leía como gráfico
> adjuntado).
>
> `bash harness/init.sh` **en verde**: 2.054 tests en `api` (13 saltados),
> puerta de cobertura **99,0 % de 1.079 líneas cambiadas**, `ruff` en **58
> avisos, la deuda previa exacta**. **T33 marcada** en `tasks.md`.
>
> **NO se ha ejecutado nada** contra Azure, Sigrid, `sigrid-api`, el PostgreSQL
> compartido ni SharePoint.
>
> Sigue pendiente lo mismo de antes: **T34** (`init.sh`, que el encargo reserva
> al líder) y el **bloque 9** contra el ERP, con su guion sin escribir.

> ## Estado al 2026-09-06 (noche) · **F-012 implementada: T1–T24 hechas, `init.sh` en verde, bloque 9 y mutación sin ejecutar**
>
> El implementer ha ejecutado **T1 a T24** de `specs/F-012-grafico-sigrid/tasks.md`
> en `feature/F-012-grafico-sigrid`, 22 commits locales, sin push.
> **Informe completo: `progress/impl_F-012.md`.**
>
> Lo que hace el código ahora: el PDF del parte se adjunta a la reclamación
> como **gráfico** de Sigrid (`POST /api/sigrid/concepto-grafico`) **antes** del
> cambio de estado, y **el cierre se niega a ejecutarse si el gráfico no consta
> adjuntado** en `postventa.graficos`. Con eso el **riesgo aceptado de
> `docs/ARCHITECTURE.md` queda cerrado por diseño y sin haberse producido ni
> una vez**, porque F-012 se implementa antes del primer cierre real (orden (b)
> que eligió el humano).
>
> **Números medidos, no estimados:** 2.032 tests en verde en `api` (32,9 s) y
> 130 en `front` (con 187 de JavaScript dentro); **464 de ellos son propios de
> F-012**. Puerta de cobertura: **98,7 % de 1.079 líneas cambiadas** (umbral 80,
> nivel `critico`). `ruff` se queda en **58 avisos, exactamente la deuda
> previa**: la feature no añade ni uno.
>
> **NO se ha ejecutado nada** contra Azure, Sigrid, `sigrid-api`, el PostgreSQL
> compartido ni SharePoint. Ni una lectura. Los tres scripts nuevos de `infra/`
> están escritos y validados sintácticamente, pero **sin lanzar**.
>
> **Lo que queda, y es del líder o del humano** (el encargo lo reservó
> explícitamente, por eso no está marcado en `tasks.md`):
>
> - **T33 · la campaña de mutación.** Sin ejecutar. El informe trae ya el
>   **alcance calculado**: 24 ficheros y **224 mutantes**, de los que ~102 son
>   de F-009 —esta rama nace de la suya y el alcance se mide contra `dev`—.
>   Comando y coste estimado (~15 min con 8 workers, ~8 min acotando la base) en
>   `progress/impl_F-012.md` §7.1.
> - **T34 · `bash harness/init.sh`.** Se ha ejecutado y está **en verde**, pero
>   la tarea no se marca.
> - **Bloque 9 (T25–T32) · la verificación contra el ERP**, sobre la **obra de
>   prueba 404**, con dry-run y autorización expresa por incidencia. Su guion
>   (`progress/guion_bloque9_F-012.md`) **todavía no existe**: escribirlo es lo
>   primero.
>
> **AVISO para cuando se abra la ventana**: `CIERRE_HABILITADO` es **una sola**
> para el gráfico y el cierre (decisión D-B). Abrirla para probar el gráfico
> **abre también el cierre**. Y la P0 del bloque 9 —las cinco App Settings
> `SIGRID_DOCUMENT_*` de `sigrid-api`— es **del dueño de la pasarela**: se
> releen antes de abrir nada, no se dan por buenas.
>
> **Fuera de este repositorio**: `azure-apps/postventa_incidencias.md`
> refrescado, commit local `72b8fa3`, **sin push**.
>
> **Sigue abierta la P1** de `design.md` §14: confirmar con Posventa que
> `PV002` (`gratipide` 35) es la clase correcta para un parte firmado. Cambiarla
> exige tocar además la lista blanca de la pasarela: es una decisión de dos
> dueños.

> ## Estado al 2026-09-06 (tarde) · **«Ok a todo»: F-012 va primero, F-023 cancelada, F-009 espera**
>
> El humano aprobó las cuatro recomendaciones de la spec de F-012 (§14):
> **P1** `gratipide` 35 se mantiene (confirmar con Posventa); **P3** orden
> **(b)**, F-012 antes que el bloque 8 de F-009; **P4** F-023 **cancelada**
> (ficha retirada de `features.json`, conservada en `progress/history.md`);
> **P5** hay que preparar un parte de la obra 404 antes de abrir la ventana.
>
> - **F-009 pasa a `blocked`** con motivo explícito en su ficha: no le falta
>   código, le falta ejecutar el bloque 8, y eso va después de desplegar
>   F-012. Al reanudarla: Paso 0 y corregir el guion según design §13(b).
> - **F-012 sigue `spec_ready`**. Se pone `in_progress` al lanzar el
>   implementer, en la rama `feature/F-012-grafico-sigrid` creada **desde
>   `feature/F-009-cierre-sigrid`** (necesita el código del cierre, que no
>   está en `dev`).
> - **Pendiente de aclarar con el humano antes de implementar**: pidió revisar
>   el correo de Alicia del 2026-08-18 con la guía de cierre por si el
>   cierre debe registrar «toda la información pertinente» y no solo el
>   gráfico. Revisado el correo, la guía reconvertida con `markitdown` y sus
>   seis capturas: la guía solo prescribe renombrar, importar el gráfico
>   (Descripción `PARTE FIRMADO`, Tipo `PV002`) y `Procesos → 3. Cerrar
>   parte`; no rellena ningún otro campo de la reclamación. No hay otro
>   correo ni mensaje de Teams con instrucciones. `docs/referencia/01_cierre_incidencia_sigrid.md`
>   es fiel al original. Si hay más información que registrar, no está
>   escrita en ningún sitio: hay que preguntársela al humano.

> ## Estado al 2026-09-06 · **F-012 desbloqueada y con spec: `spec_ready`, a la espera de la aprobación del humano**
>
> El endpoint `POST /api/sigrid/concepto-grafico` existe (`sigrid-api` F-004,
> mergeada en `dev` el 2026-09-06; contrato en `azure-apps/sigrid_api.md`
> §8.8), así que el bloqueo de F-012 cae. El humano lo confirmó hoy y fijó el
> encuadre: **el gráfico se adjunta antes del cambio de estado**, orden más
> idempotencia en vez de atomicidad entre dos llamadas, y **toda escritura de
> prueba contra el ERP va a reclamaciones de la obra de prueba 404**.
>
> - Commit `33fd684`: F-012 `blocked` → `pending`, ficha reescrita.
> - Commit `fe76639`: **`specs/F-012-grafico-sigrid/`** (requirements 70
>   requisitos, design con 12 decisiones D-A…D-L, tasks en 10 bloques). Lo
>   escribió el spec-author sin ejecutar nada contra el ERP; la consulta que
>   localiza las reclamaciones de la obra 404 queda **preparada y sin lanzar**
>   (design §15).
> - Este commit: F-012 → **`spec_ready`**, y los scripts de utillaje de la
>   spec pasan de `14/15/16` a **`15/16/17`** porque `infra/14_paso0_sigrid.ps1`
>   ya existe desde `1223bde`.
>
> **Decisiones que la spec deja al humano** (design §14): P1 la clase
> `gratipide 35` para un parte firmado (recomendación: sí, confirmar con
> Posventa); P3 el **orden** entre el bloque 8 de F-009 y F-012 —el humano
> eligió F-009 primero; la spec recomienda F-012 primero para que el primer
> cierre real lleve ya el gráfico—; P4 si se cancela F-023; P5 preparar un
> parte de la obra 404 que haya pasado el circuito antes de abrir la ventana.
> En cualquier orden, la P5 del guion del bloque 8 debe pasar de Mirasierra a
> la **obra 404**: pendiente de corregir cuando se decida el orden.
>
> **F-009 sigue `in_progress`** con el bloque 8 sin ejecutar; solo cabe una
> `in_progress`, así que F-012 no se implementa hasta que F-009 cierre o el
> humano decida lo contrario. **No se ha ejecutado nada** contra Azure, Sigrid,
> `sigrid-api`, el PostgreSQL compartido ni SharePoint.

> ## Estado al 2026-09-06 · **Dos correcciones más, fuera de feature, aprobadas por el humano**
>
> Detalle completo: **`progress/impl_paso0_sigrid.md`**. Commits `32d40f5`
> (corrección 1), `1223bde` (corrección 2) y este mismo (el rastro). **Sin
> `push`.** **Ningún estado de feature cambia**: F-009 sigue `in_progress`,
> F-023 sigue `blocked`.
>
> **NO se ha ejecutado nada contra Azure, Sigrid, `sigrid-api`, el PostgreSQL
> compartido ni SharePoint. Ni lecturas.** Ninguna casilla del bloque 8 se ha
> marcado.
>
> 1. **La raíz de la pasarela y `PG_HOST` se teclean, no se leen con `az`.** Era
>    la observación que `c3fa55d` dejó anotada y sin corregir, y eran **dos**
>    líneas del Paso 0 de aquí abajo, no una: `SIGRID_API_BASE_URL` y `PG_HOST`
>    son **referencias a Key Vault**, así que `appsettings list` devolvía la
>    cadena `@Microsoft.KeyVault(SecretUri=...)` sin resolver. Las dos pasan a
>    `Read-Host`. `SIGRID_BASE_DATOS` se queda: desde `bed95ea` es plana. El
>    porqué queda escrito en el §3 del guion del bloque 8.
> 2. **`infra/14_paso0_sigrid.ps1`**: el Paso 0 del bloque 8 —dos secretos, ocho
>    App Settings con `-SinPublicar`, y la comprobación de que las **once**
>    referencias a Key Vault se resuelven— en un solo script, con tabla,
>    veredicto (`Paso 0 COMPLETO: 11/11`) y código de salida. Con `-WhatIf` solo
>    lee, y así se comprueba la precondición **P3** sin tocar nada. 18 tests. La
>    vía manual del guion **se conserva** como camino alternativo.
>
> **Lo primero que hace falta del humano** es ejecutarlo, empezando por
> `powershell -ExecutionPolicy Bypass -File .\infra\14_paso0_sigrid.ps1 -WhatIf`.

> ## Estado al 2026-09-03 · **Dos correcciones sobre el trabajo de H1/H2, aprobadas por el humano**
>
> Detalle completo: **sección «Correcciones del 2026-09-03» de
> `progress/impl_H1_H2_despliegue.md`** (§11 a §15). Commits `bed95ea`
> (scripts y test), `a6669c3` (documentación) y `2855955` (spec de F-010);
> en `azure-apps`, `0b31237`. **Sin `push` en ninguno de los dos.**
>
> 1. **`SIGRID_BASE_DATOS` baja de secreto de Key Vault a App Setting plana.**
>    Los tres secretos de `82fbfb8` eran exceso de celo en uno: el nombre de la
>    base de producción del ERP **ya está escrito en el repositorio**
>    (`docs/referencia/03_modelo_posventa_sigrid.md` y
>    `specs/F-009-cierre-sigrid/design.md`), así que el vault no lo protegía de
>    nada y a cambio obligaba a un aprovisionamiento manual más por entorno.
>    **Quedan dos secretos** —`sigrid-api-key`, que es una credencial, y
>    `sigrid-api-base-url`, que es un host interno— y el vault pasa de 12+2 a
>    **11+2**. El test de R28 **no se ha relajado**: que esas dos no aparezcan
>    escritas en `desplegar_backend.ps1` sigue siendo la comprobación, y hay
>    una aserción **nueva** que impide que `sigrid-base-datos` vuelva al vault
>    por inercia y acabe fijado por partida doble.
> 2. **R28 de F-010 ya no miente.** Decía que **ninguna** variable de Sigrid
>    entra en el despliegue, premisa que cayó con la aprobación de hoy. Se
>    corrige el texto en `requirements.md` (requisito y tabla de trazabilidad)
>    y en `tasks.md` (verificación de T5), con un **recuadro fechado** debajo
>    del requisito que cita la premisa original literal, dice qué la invalidó y
>    apunta al hallazgo H1 del §8 del guion. **F-010 sigue `done`**: no se
>    reabre ni se reinterpreta. No aparecía en su `design.md` ni en
>    `CHECKPOINTS.md`; se buscó.
>
> **Una precisión honesta**: el encargo daba seis documentos donde el nombre de
> la base ya estaba escrito, y son **dos**. En los otros cuatro la palabra
> aparece como parte de `swa-postventa-ruesma`, que es la Static Web App. La
> decisión no cambia —dos documentos versionados bastan, y uno es la
> documentación de referencia del sistema origen—, pero el número sí.
>
> **A mano antes de T22 quedan dos valores, no tres.** Lo demás del §6 del
> informe sigue abierto y sin tocar.
>
> **No se ha ejecutado nada** contra Azure, Sigrid, `sigrid-api`, el PostgreSQL
> compartido ni SharePoint —ni lecturas—; no se ha tocado el repositorio
> `sigrid-api`; no se ha marcado ninguna tarea del bloque 8 ni T29, y no se ha
> cambiado el estado de ninguna feature.

> ## Estado al 2026-09-03 · **H1 y H2 arreglados: el despliegue ya aprovisiona Sigrid y rearma el candado del cierre**
>
> Los dos hallazgos de despliegue del §8 de `progress/guion_bloque8_F-009.md`,
> aprobados por el humano hoy. Informe completo, con el cotejo variable a
> variable: **`progress/impl_H1_H2_despliegue.md`**. Commit `82fbfb8` aquí y
> `9bc0518` en `azure-apps`. **Sin `push` en ninguno de los dos.**
>
> - **H1** · El despliegue no traía **ninguna** de las ocho variables de F-009.
>   Ya las trae. **Corregido después** (ver el bloque de arriba): son **dos**
>   por referencia a Key Vault (`sigrid-api-base-url`, `sigrid-api-key`) y
>   **seis** en `$ajustes`. Son dos secretos y no uno porque la raíz de la
>   pasarela es un host interno, igual que `pg-host`.
> - **H2** · `CIERRE_HABILITADO=false` está en `$ajustes`, junto a
>   `ARCHIVO_HABILITADO`. Era el único candado del despliegue que no se rearmaba
>   solo. `docs/DESPLIEGUE.md` §4 bis decía que sí; ahora describe el mecanismo
>   real y deja escrito que antes no lo era.
> - **El cotejo destapó dos variables más** de las tres previstas:
>   `SIGRID_ZONA_HORARIA` —la que decide el huso de `fec`/`hor` en `dbo.log`, y
>   la única que **no da error al faltar**— y `SIGRID_TIP_RECLAMACION`.
>
> ### Dos cosas que el humano tiene que decidir o hacer
>
> 1. **Queda a mano subir los valores al Key Vault** —**dos**, no tres, tras la
>    corrección de arriba—: los da el dueño de
>    `sigrid-api` y no pueden entrar al repositorio. El **Paso 0** del §1 del
>    guion sigue ahí, con los dos caminos (redesplegar, o poner las App Settings
>    sueltas si no se quiere redesplegar el entorno actual).
> 2. **Se tocó un test de F-010**, contra la instrucción de no tocar
>    `services/`, porque era imposible no hacerlo: `test_f010_r28` exigía
>    literalmente que **no** hubiera ninguna variable `SIGRID_*` en el
>    despliegue. Su premisa —«el ERP está fuera del piloto»— cae con la
>    aprobación de hoy; lo que protegía, no, y es lo que comprueba ahora.
>    **RESUELTO** en `2855955`: R28 está enmendado en la spec, con constancia
>    fechada. Detalle en el §5 y el §12 del informe.
>
> **No se ha ejecutado nada** contra Azure, Sigrid, `sigrid-api`, el PostgreSQL
> compartido ni SharePoint —ni lecturas—, no se ha marcado ninguna tarea del
> bloque 8 ni T29, y no se ha cambiado el estado de ninguna feature.

> ## Estado al 2026-09-03 · **Cae la premisa que bloqueaba F-012: la base documental SÍ es escribible**
>
> **El dato lo dio el humano hoy**, y lo respalda el spike **F-002 de
> `sigrid-api`, ya cerrado**: **el usuario de escritura tiene permiso sobre la
> base documental**. Con eso cae el bloqueo que arrastrábamos desde el
> 2026-08-26.
>
> Lo que creíamos —«la documental está cerrada y abrirla es decisión del dueño
> de `sigrid-api`, que afecta a todo el ecosistema»— era **media verdad**. La
> otra media: la base **no es una réplica de solo lectura** (el sufijo es
> «repositorio», no «réplica»), está en la **misma instancia** que la de
> negocio, y **el propio ERP le escribe** cada vez que alguien importa un
> documento desde la UI de Sigrid. Que esté fuera de
> `ALLOWED_WRITE_DATABASES` es una **política de la pasarela**, no un
> impedimento del motor.
>
> Consecuencia técnica, y es la que importa para el diseño: **una transacción
> puede abarcar las dos bases sin MSDTC**, porque entre bases de la misma
> instancia es local. Eso es lo que hace viable adjuntar el parte de forma
> atómica: metadatos y enlace en la de negocio, binario en la documental, las
> tres escrituras o ninguna.
>
> ### Quién hace qué
>
> **El endpoint lo está implementando el humano**, en `sigrid-api` (su backlog:
> **F-004**, «Endpoint de dominio para adjuntar un documento a un concepto de
> Sigrid»). La **especificación de referencia** se escribió ayer y vive en
> `sigrid-api/docs/propuestas/2026-09-03_endpoint_adjuntar_documento.md`, rama
> `docs/propuesta-escritura-documental`.
>
> **Esa spec tiene una sección desmentida y NO se ha corregido, a propósito**:
> su §3 dice que el usuario de escritura «casi con seguridad no tiene ningún
> permiso» sobre la documental y describe una acción de administrador de base de
> datos como pieza que falta. Ya no falta. **La corrige el humano al implementar
> F-004**: lo decidió así porque tiene ese repositorio en otra rama
> (`chore/instalar-arnes`, donde acaba de instalar el arnés v1.7.8) y no tiene
> sentido que un agente le cambie de rama un repositorio en el que está
> trabajando. Queda anotado aquí para que nadie lea esa §3 como vigente.
>
> ### La orden operativa, que es corta
>
> **No se escribe NI SE LEE nada contra el ERP desde este proyecto hasta que el
> humano nos pase el endpoint.** Lo pidió expresamente el 2026-09-03. Eso
> incluye las lecturas de caracterización que había preparadas
> (`infra/13_caracterizacion_grafico_url.ps1`): están listas y **no se lanzan**.
>
> ### Lo que esto NO cambia
>
> - **F-012 sigue `blocked`**, porque el endpoint todavía no existe. Lo que
>   cambia es el motivo: ya no es una decisión pendiente de un tercero, es
>   trabajo en curso del propio humano.
> - **F-023 (el gráfico por URL) sigue `blocked`**, esperando la prueba manual
>   de Posventa. **Con el endpoint del binario en camino, conviene que el humano
>   decida si esa vía sigue interesándole**: evitaría duplicar el PDF dentro del
>   ERP, pero deja de ser la única salida. **Esa decisión no la toma un agente.**
> - **F-009 sigue `in_progress`** y su **bloque 8 sigue entero sin ejecutar**.
>   Antes de T22 hace falta su Paso 0: el entorno desplegado no tiene
>   aprovisionada ninguna configuración de Sigrid.


> ## Estado al 2026-09-02 · **F-012 bloqueada, nace F-023, y falta UNA medida**
>
> ### F-012 pasa a `blocked`, con dos bloqueos y ninguno se resuelve aquí
>
> Subir el PDF del parte a Sigrid como gráfico —incrustar el binario— **no
> tiene hoy por dónde hacerse**:
>
> 1. **`sigrid-api` no sabe escribir documentos.** Haría falta un endpoint de
>    dominio nuevo **en ese repositorio**, porque `sql/write` ni reserva `ide`
>    con applock ni está pensado para BLOBs.
> 2. **El binario vive en la base DOCUMENTAL**, y la configuración desplegada
>    tiene la de negocio como **única escribible** (`ALLOWED_WRITE_DATABASES`).
>    La documental queda fuera **a propósito**: abrirla es decisión del dueño de
>    `sigrid-api` y afecta al ecosistema entero.
>
> El humano lo confirmó el 2026-09-02: **el binario se queda en F-012** hasta
> que su dueño abra esa base.
>
> ### Nace F-023 · el gráfico por URL, la vía que no depende de nadie
>
> Asociar el parte a la reclamación **como referencia** al PDF que ya
> archivamos en SharePoint, en vez de incrustarlo: escribe **solo en la base de
> negocio** (metadatos en `gra` + el enlace `rcg`), así que **el bloqueo de
> F-012 no le aplica**.
>
> **Por qué importa, y no es cosmético.** F-009 cierra con un `UPDATE con.est`
> directo y **sin ningún `COUNT` sobre `rcg`** (R20, deliberado): el proceso
> nativo «Cerrar parte» no nos frena. Pero deja **reclamaciones en `CER` sin
> ninguna fila en `rcg`**, anomalía firmada como **RIESGO ACEPTADO** en
> `design.md` §2 y que **no ha ocurrido ni una vez en los 2.365 cierres desde
> 2023**. F-023 la hace desaparecer.
>
> La investigación que la fundamenta es `progress/explore_grafico_url.md`, y
> trae un **resultado negativo que vale**: los 13.450 gráficos de posventa **NO
> son de tipo URL**. `vin = 3` con `ima` vacío significa «el binario está en la
> otra base», no «esto es un enlace». **No hay ni un precedente en 282.599
> filas**, y en el diccionario de Sigrid la tabla `gra` ni siquiera tiene
> columna `url`.
>
> ### Lo que mide el script nuevo
>
> `infra/13_caracterizacion_grafico_url.ps1` empaqueta **Q1, Q3, Q4, Q5, Q8 y
> Q9** del §5 del informe, en el orden de su §6. **Todas son `SELECT`** por
> `POST /api/sql/read`; **no se ha ejecutado ninguna**.
>
> | | Qué mide | Por qué |
> |---|---|---|
> | **Q1** | Las columnas que tiene **de verdad** la `gra` desplegada, y si ya hay una `url` | El diccionario es de v.20240618 y **ya se sabe que le faltan columnas** de `rcg`. Si `gra` tuviera `url`, cambia el diseño entero |
> | **Q3** | Las **dos** filas huérfanas `vin = 1` y `vin = 4` | Dos filas en 282.599 que nadie ha mirado. La pista más barata que existe |
> | **Q4** | El perfil de cada modo de `vin` | Nadie ha caracterizado `vin = 2` (154) ni `vin = 0` (38) |
> | **Q5** | En qué estado están las reclamaciones cuyos gráficos **no tienen fichero detrás** (los 51) | **El proxy empírico**: si alguno cuelga de una reclamación cerrada, «Cerrar parte» mira **el enlace**, no el contenido |
> | **Q8** | Si `gra.cod` es **único** | El `INSERT` en `rcg` deriva el `ide` por `cod`; con `cod` repetidos crearía enlaces de más |
> | **Q9** | Si esta instalación usa `dog`/`condog`, que **sí** tiene `url` nativa | Es el segundo camino, y el mensaje del ERP dice «gráfico **o Doc. multimedia**» |
>
> Reutiliza `infra/08_lectura_sigrid_comun.ps1`, al que se le añadió el switch
> **`-Tolerante`** (apagado por defecto: los `09`–`12` no cambian de
> comportamiento).
>
> ### Qué falta EXACTAMENTE para desbloquear F-023
>
> **Una sola medida, y ningún documento puede darla**: qué escribe Sigrid al
> usar *Importa → Asociar URL de Internet…*. Es la **Q10** del informe, y no
> hay consulta que la responda **porque esa opción no se ha usado nunca aquí**.
>
> La resuelve **Posventa (Alicia Echevarría) en cinco minutos**, haciéndolo una
> vez a mano sobre una reclamación de prueba y ejecutando después
> *Procesos → 3. Cerrar parte*. Nosotros **solo leemos** la fila resultante.
> La petición, **redactada para reenviarla tal cual**, está en
> **`progress/peticion_posventa_prueba_url_F-023.md`**.
>
> **Hasta entonces F-023 no se diseña ni se escribe su spec**: F-008 ya advirtió
> que la combinación de `vin`/`tex`/`nom` **no se debe diseñar sobre
> suposiciones**.
>
> ### Y F-009 sigue igual: `in_progress`, con el bloque 8 SIN EJECUTAR
>
> Nada de lo anterior lo mueve. **T22–T27 y T29 siguen sin marcar**, el guion
> de `progress/guion_bloque8_F-009.md` sigue escrito y sin ejecutar, y siguen en
> pie sus dos hallazgos: el entorno desplegado **no tiene configuración de
> Sigrid** (H1) y **`CIERRE_HABILITADO` no se rearma solo** (H2).
>
> Se corrigió además una **referencia rota** en su spec: `design.md` §1 (D4),
> §10 y §11, y `requirements.md`, mandaban el gráfico-URL a **F-013**, que es
> «mudar el archivo a la biblioteca de Posventa». Ahora apuntan a **F-023**.
> Solo se cambió el identificador.

> ## Estado al 2026-09-02 · **guion del bloque 8 escrito, sin ejecutar nada**
>
> `progress/guion_bloque8_F-009.md` + cinco scripts en `infra/`
> (`08_lectura_sigrid_comun.ps1`, `09_estado_reclamacion_sigrid.ps1`,
> `10_log_cierre_sigrid.ps1`, `11_trazabilidad_tex_sigrid.ps1`,
> `12_traza_cierre_local.ps1`). **Los cinco son de LECTURA**; la única
> escritura del bloque la hace el servicio desplegado.
>
> **No se ha ejecutado ni una llamada** a Sigrid, `sigrid-api`, la Function
> desplegada, el PostgreSQL compartido ni SharePoint. T22–T27 y T29 siguen sin
> marcar y F-009 sigue `in_progress`: las marca el humano.
>
> **El bloque 8 NO puede arrancar tal cual (hallazgo H1).** El entorno
> desplegado **no tiene ninguna configuración de Sigrid**: `infra/00_vars_postventa.ps1`
> no lista `sigrid-api-key` entre los secretos ni `SIGRID_API_KEY` entre las
> referencias, y `infra/desplegar_backend.ps1` no fija ninguna `SIGRID_*`.
> T22 respondería `503 ConfiguracionSigridIncompleta`. El «Paso 0» del §1 del
> guion lo aprovisiona a mano; arreglarlo en los scripts está **propuesto y no
> hecho**.
>
> **Y `CIERRE_HABILITADO` no se rearma solo (hallazgo H2)**, al contrario que
> `ARCHIVO_HABILITADO=false`: no está en `$ajustes`, así que se apoya en el
> valor por defecto del código, que solo aplica **mientras la App Setting no
> exista**. Encendida una vez, un redespliegue **no** la apaga —y
> `docs/DESPLIEGUE.md` §4 bis dice que sí—. Cerrar la ventana a mano al
> terminar, y comprobarlo.
>
> Los seis hallazgos, con su propuesta, en §8 del guion.

> ## Estado al 2026-09-02 · **T28 CERRADA: 117 muertos, 6 supervivientes, 0 timeouts**
>
> ```
> python -m harness.mutacion --feature F-009 --workers 1
> ```
>
> **123 mutantes evaluados, 117 muertos, 6 supervivientes, 0 timeouts, en
> 6.124,7 s** (102 min). Informe regenerado en `progress/mutacion_F-009.md`,
> con los 26 análisis y **cero `PENDIENTE`**. Con esto el «cero supervivientes
> con veredicto» que exige el rigor `critico` **queda demostrado**, no razonado:
> T28 se marca `[x]` en `specs/F-009-cierre-sigrid/tasks.md`.
>
> **Los 6 supervivientes son exactamente los seis previstos, ni uno más:**
>
> - Los **tres aceptados por escrito como riesgo por el humano** el 2026-08-26:
>   `infrastructure/sigrid/cliente.py:347` (respuesta de escritura sin la clave
>   `ok`), `infrastructure/sigrid/consultas.py:202` y `:207` (los `NULL` de
>   `descripcion` y `estado_destino_res`).
> - Los **tres equivalentes ya justificados**:
>   `infrastructure/sigrid/escrituras.py:217` (texto de un error inalcanzable),
>   `infrastructure/sigrid/fabrica.py:130` (no se caza sin construir el
>   adaptador real, y eso lo prohíbe la guardia de red R39) e
>   `interface_adapters/api/cerrar.py:219` (`confianza_observaciones`, que se
>   rellena para no mandar nada).
>
> ### Por qué en serie: la hipótesis de los reintentos de `tenacity` era FALSA
>
> Lo anotado el 2026-08-27 («al mutar un código de estado la ejecución se desvía
> a un camino con reintentos de `tenacity`») **no se sostiene**. El diagnóstico
> completo está en `progress/explore_F-009_timeouts.md`: los dos mutantes
> sospechosos, reproducidos a mano y en solitario, **mueren limpiamente** en
> 37,0 s y 22,6 s, en el `assert` del código de estado. No hay cuelgue, ni
> reintento, ni espera.
>
> **La causa real es saturación de la máquina.** La suite del servicio `api`
> tarda **38,7 s** ella sola y **131,6 s** ejecutada con los 16 workers que
> usaba la campaña, es decir **por encima del tope de 120 s por mutante**. El
> veredicto `timeout` dependía de la carga del momento, no del mutante: mutantes
> que una campaña daba por muertos salían `timeout` en la siguiente, y al revés.
>
> Se confirmó tres veces. **Con `--workers 8`** (hoy): 123 evaluados, 95
> muertos, 1 superviviente, **27 timeouts**, 1.553,6 s — peor que con 16, y
> sobre **mutantes distintos**. Por eso la campaña buena se lanzó **en serie**
> (`--workers 1`): tarda 102 min, pero **cada veredicto es del mutante y no de
> la máquina**. Su informe no se conserva en `progress/` (quedó en el scratchpad
> de la sesión); `progress/mutacion_F-009.md` se restauró desde git para no
> dejar la feature peor documentada, y luego lo regeneró la campaña en serie.
>
> ### El informe generado NO registra el nº de workers
>
> Carencia del arnés: `progress/mutacion_F-009.md` dice «Generado por `python -m
> harness.mutacion --feature F-009`» **sin el `--workers`**, y sin ese dato el
> tiempo total de una campaña no se puede interpretar (fue justo lo que impidió
> reconstruir a posteriori cómo se lanzó la del 2026-08-27). Por eso **el número
> queda escrito aquí y en la línea de verificación de T28**: la campaña que
> cierra T28 se ejecutó con **1 worker, en serie**.
>
> Hay un arreglo del arnés ya aprobado que va en **un trabajo aparte**, no en
> este: excluir `harness/` del alcance de la mutación y **reevaluar en serie los
> mutantes en `timeout` al final de una campaña paralela**, para que un
> `timeout` deje de ser un veredicto y pase a ser un reintento. Ahí es donde
> toca añadir también la línea de workers al informe. Regla de propagación: va a
> `arnes-base`.
>
> ### Lo que esto NO cierra
>
> - **F-009 sigue `in_progress`.** A `done` la mueve el humano, no un agente.
> - **El bloque 8 (T22–T27) sigue entero sin ejecutar**: es el que toca el ERP
>   de producción, se hace desde el entorno desplegado con dry-run previo y
>   confirmación explícita, y ninguna de sus tareas se ha ejecutado. **T29
>   tampoco se marca.**
> - Lo único que cambia con T28 es que la puerta de mutación del rigor
>   `critico` está satisfecha.


> ## Estado al 2026-08-27 · **T28 ejecutada: cero supervivientes nuevos, 15 timeouts sin veredicto** — SUPERADO por el bloque del 2026-09-02

>
> `python -m harness.mutacion --feature F-009`, campaña completa, **3.623 s**.
> Informe regenerado en `progress/mutacion_F-009.md`, con los análisis de los
> seis conservados (cero `PENDIENTE`). Salida del comando: **123 evaluados,
> 102 muertos, 6 supervivientes, 15 timeouts**; exit code 1.
>
> **Los 6 supervivientes son exactamente los previstos, ni uno más:**
>
> - Los **tres aceptados como riesgo por el humano** el 2026-08-26:
>   `cliente.py:347` (respuesta sin clave `ok`), `consultas.py:202` y `:207`
>   (los `NULL` de `descripcion` y `estado_destino_res`).
> - Los **tres equivalentes ya justificados**: `escrituras.py:217` (texto de un
>   error inalcanzable), `fabrica.py:130` (no se caza sin construir el adaptador
>   real, y eso lo prohíbe la guardia de red R39) y `cerrar.py:219`
>   (`confianza_observaciones`, que se rellena para no mandar nada).
>
> **Los ~19 supervivientes que destapó la primera campaña están muertos**: los
> tests que se escribieron después funcionan.
>
> ### PENDIENTE · los 15 timeouts, que no los había antes
>
> Quince mutantes quedaron **sin veredicto** —ni muertos ni vivos—, y no al
> azar: **7 en `domain/models/cierre.py` y 8 en `function_app.py`**. Los ocho de
> `function_app.py` son **los códigos HTTP** que la primera campaña destapó como
> supervivientes y para los que se escribió el fichero de tests de la ruta.
> La campaña anterior tuvo **0 timeouts** con el mismo límite.
>
> **Hipótesis sin comprobar**: al mutar un código de estado, la ejecución se
> desvía a un camino con reintentos de `tenacity` y el test agota el límite.
>
> **Cómo se cierra cuando se retome**: relanzar acotado a esos dos ficheros con
> `--timeout` más alto (son 15 mutantes, no 123). **T28 no se marca**: la
> campaña se ejecutó, pero el «cero supervivientes con veredicto» que pide
> `critico` no está demostrado mientras haya quince sin evaluar.
>
> **El humano decidió seguir con el bloque 8 y dejar esto anotado.**


> ## Estado al 2026-08-27 · **F-009 APROBADA en segunda review · el ERP sigue sin tocarse**
>
> `progress/review2_F-009.md`: **APROBADO**, con tres condiciones para el humano
> (§7). Los cinco cambios de la primera review están atendidos; el único cambio
> de código de esa tanda fue un reorden de imports, y `ruff` baja de 59 a 58
> avisos, exactamente el efecto esperado. El reviewer añadió una comprobación
> que la primera pasada no hizo: **muestrear que los tests nuevos matan de
> verdad a sus mutantes**, 4 de 4.
>
> `bash harness/init.sh` en verde: cobertura **98,8 %** (565/572), umbral 80 %.
>
> **Las tres condiciones, que no las cierra ningún agente:**
>
> 1. **T28 sin ejecutar**: el cero de supervivientes de `critico` está razonado
>    y muestreado, **no demostrado**. Son ~43 min: `python -m harness.mutacion
>    --feature F-009`.
> 2. **El bloque 8 entero sin ejecutar, y F-009 no está terminada hasta que se
>    ejecute.** Lo aprobado es que el código está listo **para** ese día, no que
>    ese día haya llegado. En T24 el paso 7 incluye mirar la hora de la fila de
>    `dbo.log` (el huso `Europe/Madrid` es la única decisión sin dato). En T26,
>    si `SqlWriteGuard` rechaza el `WITH (UPDLOCK, HOLDLOCK)`: **`blocked` y
>    parar**, no improvisar.
> 3. **Marcar T22–T28 solo según se ejecuten de verdad.**
>
> **El estado de la feature no lo he tocado**: F-009 sigue `in_progress` y a
> `done` la mueve el humano. Sigue anotado, sin hacer y sin bloquear, todo lo
> de la primera review §6.3, incluido llevar al dueño de `sigrid-api` que
> **este servicio es ya el primer escritor genérico por `sql/write`** del
> ecosistema y no figura en su tabla de consumidores.


> ## Estado al 2026-08-26 (review) · **F-009 rechazada y corregida; decisión del humano sobre los tres huecos**
>
> `progress/review_F-009.md` devolvió **CHANGES_REQUESTED** con cinco cambios
> (§7). No discutía la ingeniería —verificó la campaña de mutación por su
> cuenta y le salieron los mismos 3.021 líneas y 124 mutantes en el commit de
> la campaña—: rechazó por **cuatro casillas vacías de `CHECKPOINTS.md`**, y en
> rigor `critico` una casilla vacía es rechazo.
>
> **Hechos por el implementer** (commits `a335706`, `43c822c`, `dee5495`,
> `b831da1`): §7.1 los 26 análisis de supervivientes trasladados a
> `progress/mutacion_F-009.md` —**cero `PENDIENTE` ya**—, §7.3 las
> verificaciones `MANUAL (humano)` de T22–T27 escritas aquí abajo **con el
> comando exacto**, y §7.5 el `I001` de `paso_cierre.py` arreglado y el dato de
> `ruff` corregido.
>
> **Hecho por el líder**: §7.4, la poda de este fichero (lo movido está en
> `progress/history.md`, bloque del 2026-08-26).
>
> ### DECISIÓN DEL HUMANO (2026-08-26) · los tres huecos se aceptan como riesgo
>
> El §7.2 del review pedía un test para cada uno de los tres supervivientes que
> el implementer declaró sin cubrir, **o** que el humano los aceptara por
> escrito. **El humano eligió lo segundo, explícitamente: «salta el 2».** Queda
> escrito aquí porque en rigor `critico` esa decisión no la puede tomar ni el
> implementer ni el reviewer, y es la que cierra esa casilla:
>
> 1. **Superviviente 21** · `infrastructure/sigrid/cliente.py:347` —
>    `respuesta.get("ok", False)`. Ningún test manda una respuesta de la
>    pasarela **sin la clave `ok`**. Riesgo: si `sigrid-api` dejara de mandarla,
>    nada fija por test qué se supone entonces.
> 2. **Supervivientes 22 y 23** · `infrastructure/sigrid/consultas.py:202` y
>    `:207` — el `NULL` de `descripcion` y de `estado_destino_res` en el mapeo
>    del dry-run. La descripción es una de las cinco cosas que **R9** obliga a
>    enseñar antes de confirmar, y su caso `NULL` no está fijado.
>
> **Ninguno de los tres afecta a la escritura en el ERP**: el batch de §7.3 del
> diseño está cubierto y verificado. Si el reviewer quiere reabrirlo en la
> segunda pasada, tiene esta decisión fechada y con nombre.
>
> **Siguiente paso**: segunda review contra `CHECKPOINTS.md`. F-009 sigue
> `in_progress`; a `done` solo la mueve el humano, y el **bloque 8 (T22–T27),
> el que toca el ERP de producción, está entero sin ejecutar**.


> ## Estado al 2026-08-26 (implementación) · **F-009: bloques 1-7 hechos, el ERP sin tocar**
>
> **Ejecutado T1–T21.** El servicio ya sabe cerrar una incidencia en Sigrid:
> `POST /api/cerrar` hace el dry-run, y solo con `commit` **y** confirmación
> mueve `con.est` y escribe la fila de `dbo.log`, las dos en un batch
> transaccional con tope de dos filas. El informe completo, con la fase RED
> pegada y las evidencias, está en **`progress/impl_F-009.md`**.
>
> **Nada se ha ejecutado contra el ERP.** El bloque 8 (T22–T27) queda entero
> para el humano, desde el entorno desplegado y con autorización expresa para
> la incidencia concreta. Ni una casilla suya marcada.
>
> ### Lo que el humano tiene que saber antes de T22
>
> 1. **Para el dry-run también hay que abrir la ventana.** `CIERRE_HABILITADO`
>    apagado hace que la **fábrica se niegue antes de leer**, así que ni el
>    dry-run funciona con ella cerrada. Es consecuencia de la doble puerta;
>    conviene saberlo antes de estar delante del ERP.
> 2. **Mirar la hora de la fila de `dbo.log` en T24, paso 7.** La spec no decía
>    en qué huso se escriben `fec`/`hor`; se decidió **hora local**
>    (`SIGRID_ZONA_HORARIA`, `Europe/Madrid`), porque escribir UTC dejaría
>    nuestras filas con dos horas menos que todas las del ERP. Está razonado en
>    el informe §3.3.a.
> 3. **Hay una propuesta sin hacer**, y es de otro repositorio:
>    `azure-apps/sigrid_api.md` §10 lista quién consume la pasarela y
>    `postventa-incidencias` no está — y desde F-009 es su **primer escritor
>    genérico**. No se ha tocado ese documento porque su dueño es `sigrid-api`.
>
> **T21 hecho en `azure-apps`**: commit local `3c1c588`, **sin push**.


> ## Estado al 2026-08-26 (cierre de jornada) · **el Word leído; §7 en pie**
>
> **El pendiente del Word queda CERRADO, y con una sorpresa: ya estaba dentro.**
> `markitdown` respondió, se convirtió `PASOS CERRAR INCIDENCIA.docx` y su texto
> coincide **1:1** con `docs/referencia/01_cierre_incidencia_sigrid.md`, que se
> incorporó en el commit `8cb6c66` —convertido con `markitdown`, con las
> capturas leídas una a una y volcadas, y el propietario y el servidor
> redactados—. La sesión anterior lo anotó como pendiente sin ver que el
> documento que pedía leer era justo ese. El `.docx` sigue **fuera de git**
> (`.gitignore`, comprobado con `git status --ignored`); **no se ha extraído ni
> versionado ninguna captura**, y no hace falta: su contenido ya está en texto.
>
> **Del Word solo faltaban dos detalles, ninguno de F-009**, y se han añadido al
> `01`: la ruta de origen de los partes (`677 MIRASIERRA\PARTES
> INCIDENCIAS\VILLA 05\PARTES FIRMADOS`, o sea obra → unidad → firmados) y el
> **anexo** en el que la autora duda de cómo nombrar el fichero —solo incidencia
> con carpeta por vivienda, o vivienda + incidencia—. Eso es **pregunta abierta
> del negocio para la feature de archivo en SharePoint**, no para el cierre.
> De paso, el `01` ya remite al `03` para la duda que dejaba abierta sobre qué
> filas toca el proceso.
>
> ### El veredicto que pedía el punto 4: `design.md` §7 NO cambia
>
> El Word describe **el proceso** (renombrar, subir el gráfico, Procesos → 3);
> lo que F-009 replica es **el registro**, y el registro son dos cosas medidas
> por F-008 sobre 6.843 filas: `con.est = 9` y **una fila en `dbo.log`** con
> `tab='con'`, `tip=708`, `cod`/`res` copiados de la reclamación, `ope=5`,
> `est=1`, `ori=0`, `emp` de `con.emp`, `usu` el login y `fec`/`hor`. El §7.3
> escribe exactamente eso, en una transacción, con **una sola desviación
> deliberada**: el `tex` de D1. Ni una sentencia que tocar.
>
> **Siguiente paso**: pasar F-009 a `in_progress` (lo mueve el humano) y lanzar
> al `implementer` contra `specs/F-009-cierre-sigrid/tasks.md`.



## F-009 · Verificaciones `MANUAL (humano)` de T22–T27, con el comando exacto

Checkpoint C4: aquí están **tecleables**, no en prosa. El procedimiento
razonado sigue en `specs/F-009-cierre-sigrid/tasks.md` (bloque 8); lo de aquí
es lo que se copia y se pega, con los `?` del SQL resueltos en su lista de
parámetros. **Ninguna de estas casillas está marcada: nada se ha ejecutado
todavía contra el ERP.**

> **AVISO, y hay que saberlo antes de estar delante del ERP: con
> `CIERRE_HABILITADO` apagado ni siquiera el dry-run de T22 funciona.** La
> fábrica **se niega antes de leer** —la puerta se comprueba al construir el
> adaptador, no al escribir—, así que `/api/cerrar` responde `503` también sin
> `commit`. Hay que **abrir la ventana también para el dry-run** y **cerrarla al
> terminar, salga bien o mal**. Está en `progress/impl_F-009.md` §6.1.

> **REGLA DURA**: todo el bloque se ejecuta **desde el entorno desplegado**, con
> el humano delante y con autorización expresa para esa incidencia concreta.
> Nunca desde local, y nunca «de paso».

### Paso 0 · preparar la consola (una vez; el resto reutiliza estas variables)

```powershell
$grupo   = "rg-postventa-dev"
$funcion = "func-postventa-dev"
$base    = "https://" + (az functionapp show -g $grupo -n $funcion --query defaultHostName -o tsv)

# Los datos de ESTA ejecución. El código sale del parte; el hash, del front.
$incidencia = "PON-AQUI-EL-CODIGO-DE-LA-RECLAMACION"
$hash       = "PON-AQUI-EL-HASH-DEL-PARTE"
$oid        = az ad signed-in-user show --query id -o tsv
$correo     = az ad signed-in-user show --query mail -o tsv

# La pasarela, para las lecturas de comprobación (T22, T24, T25, T27).
# La raíz se TECLEA. NO se lee con `az functionapp config appsettings list`:
# SIGRID_API_BASE_URL es una referencia a Key Vault y ese comando devuelve el
# valor crudo, es decir la cadena @Microsoft.KeyVault(SecretUri=...) sin
# resolver. Azure solo la resuelve al arrancar la Function, no en la API de
# gestión. Es un host interno: se teclea, no se escribe en ningún fichero.
$sigridUrl  = Read-Host "Raiz de la pasarela sigrid-api (sin barra final)"
# Esta SÍ se lee: desde `bed95ea` SIGRID_BASE_DATOS es App Setting plana.
$sigridBase = az functionapp config appsettings list -g $grupo -n $funcion --query "[?name=='SIGRID_BASE_DATOS'].value" -o tsv
$sigridKey  = Read-Host "Clave de funcion de sigrid-api"   # NO se escribe en ningun fichero
$cabSigrid  = @{ "x-functions-key" = $sigridKey }

function Leer-Sigrid($sql, $parametros) {
    $cuerpo = @{ database = $sigridBase; sql = $sql; parameters = $parametros; max_rows = 50 } |
        ConvertTo-Json -Depth 5 -Compress
    (Invoke-RestMethod -Method Post -Uri "$sigridUrl/api/sql/read" -Headers $cabSigrid `
        -ContentType "application/json" -Body ([Text.Encoding]::UTF8.GetBytes($cuerpo))).rows
}

function Llamar-Cerrar($extra) {
    $cuerpo = @{
        hash              = $hash
        numero_incidencia = $incidencia
        veredicto         = "apto"
        destino           = "archivo_y_cierre"
        estado_archivo    = "archivado"
        usuario_oid       = $oid
        correo            = $correo
    }
    foreach ($k in $extra.Keys) { $cuerpo[$k] = $extra[$k] }
    $json = $cuerpo | ConvertTo-Json -Depth 5 -Compress
    try {
        Invoke-RestMethod -Method Post -Uri "$base/api/cerrar" -ContentType "application/json" `
            -Body ([Text.Encoding]::UTF8.GetBytes($json))
    } catch {
        # Sin esto, un 409 o un 503 salen como una excepcion muda (defecto 14 de F-010).
        $r = $_.Exception.Response
        $texto = (New-Object IO.StreamReader($r.GetResponseStream())).ReadToEnd()
        Write-Host ("HTTP {0} -> {1}" -f [int]$r.StatusCode, $texto) -ForegroundColor Yellow
    }
}
```

### Abrir la ventana · **también para el dry-run**

```powershell
az functionapp config appsettings set -g rg-postventa-dev -n func-postventa-dev --settings CIERRE_HABILITADO=true
```

Reinicia la Function: esperar ~30 s antes de la primera llamada.

### Cerrar la ventana · **SIEMPRE al terminar, salga bien o mal**

```powershell
az functionapp config appsettings set -g rg-postventa-dev -n func-postventa-dev --settings CIERRE_HABILITADO=false
az functionapp config appsettings list -g rg-postventa-dev -n func-postventa-dev --query "[?name=='CIERRE_HABILITADO'].value" -o tsv
```

La segunda línea es la comprobación: tiene que imprimir `false`.

### T22 · dry-run real contra Mirasierra, sin escribir

```powershell
Llamar-Cerrar @{} | ConvertTo-Json -Depth 6
```

Se espera, en el `dry_run`: `incidencia`, `descripcion`, el estado de origen
**legible** (código y descripción), el destino con código `CER`, el
`login_sigrid` con el que se firmaría, y en `avisos` **el de que la incidencia
quedará cerrada sin el parte dentro de Sigrid** (R21). `estado` debe ser
`dry_run_ok` y `filas_afectadas` **0**.

Y que **nada ha cambiado en el ERP** — el `est` tiene que seguir siendo el de
antes:

```powershell
Leer-Sigrid "SELECT c.ide, c.est, c.tiemod, e.cod FROM dbo.con c LEFT JOIN dbo.conest e ON e.tip = c.tip AND e.est = c.est WHERE c.tip = ? AND c.cod = ?" @(708, $incidencia)
```

### T23 · la siembra del login contra `dbo.usu` (R30–R33), en tres pasos

**Paso 1** — **con la correspondencia vacía**, el dry-run de T22 deriva el
candidato del correo y lo verifica. Comprobar que ese login existe
**exactamente una vez** (tiene que devolver `1`, ni `0` ni `2`):

```powershell
$login = ($correo -split "@")[0]
Leer-Sigrid "SELECT COUNT(*) FROM dbo.usu WHERE cod = ?" @($login)
```

**Paso 2** — que quedó **guardada y confirmada** en
`postventa.usuarios_sigrid` (R33), y que un segundo dry-run ya no deriva nada.
La lectura de PostgreSQL, con el intérprete del servicio (no hay `psql` en el
PATH) y la contraseña **aparte del DSN**, como avisa el defecto 16. El `'@` de
cierre va **pegado al margen izquierdo**, o PowerShell no parsea el bloque:

```powershell
# PG_HOST también se teclea, y por el mismo motivo que la raíz de la pasarela:
# `pg-host` es un secreto del vault y la App Setting es una referencia, así que
# `appsettings list` devolvería @Microsoft.KeyVault(SecretUri=...) sin resolver.
$env:PG_HOST     = Read-Host "Host de PostgreSQL"
$env:PG_DB       = "postventa"
$env:PG_USER     = "postventa_app"
$env:PG_PASSWORD = Read-Host "Contrasena de postventa_app"
$env:SQL_TEMP    = "SELECT usuario_oid, login_sigrid, alta_at_utc, verificado_at_utc FROM postventa.usuarios_sigrid WHERE usuario_oid = %s"
$env:CLAVE_TEMP  = $oid
$leerPg = @'
import os, psycopg
from config.settings import obtener_ajustes
from infrastructure.persistencia.conexion import dsn_desde_ajustes
ajustes = obtener_ajustes()
with psycopg.connect(dsn_desde_ajustes(ajustes), password=ajustes.pg_password) as cn:
    with cn.cursor() as cur:
        cur.execute(os.environ["SQL_TEMP"], (os.environ["CLAVE_TEMP"],))
        for fila in cur.fetchall():
            print(fila)
'@
Push-Location services\postventa-api
& .\.venv\Scripts\python.exe -c $leerPg
Pop-Location
Remove-Item Env:\PG_PASSWORD, Env:\SQL_TEMP, Env:\CLAVE_TEMP -ErrorAction SilentlyContinue
```

`verificado_at_utc` **no** puede quedarse a `NULL`: eso es lo que R33 exige.

**Paso 3** — con un usuario cuyo candidato **no exista** en `dbo.usu` (uno de
los 2 de 8 que no siguen la convención), la misma llamada de T22 tiene que
responder **409** nombrando el correo y el login intentado, **sin tocar
Sigrid** (R31). `Llamar-Cerrar` ya imprime el código y el cuerpo. Se resuelve
con el alta manual de T12 (R34):

```powershell
powershell -ExecutionPolicy Bypass -File infra\07_alta_usuario_sigrid.ps1 -UsuarioOid $oid -LoginSigrid "EL-LOGIN-REAL-DEL-ERP" -VerificarAhora -SigridBaseUrl $sigridUrl -SigridBaseDatos $sigridBase
```

### T24 · el primer cierre real · los nueve pasos, en este orden

**Paso 1** — anotar el estado de partida (y `tiemod`, que hace falta en el
paso 8):

```powershell
$antes = Leer-Sigrid "SELECT ide, est, tiemod FROM dbo.con WHERE tip = ? AND cod = ?" @(708, $incidencia)
$antes
```

**Paso 2** — anotar el último `ide` del log:

```powershell
$logAntes = (Leer-Sigrid "SELECT MAX(ide) FROM dbo.log" @())[0][0]
$logAntes
```

**Paso 3** — ejecutar el dry-run **y leerlo** (es el comando de T22):

```powershell
Llamar-Cerrar @{} | ConvertTo-Json -Depth 6
```

**Paso 4** — confirmar en el front y ejecutar con `commit`. **Esto escribe en
el ERP de producción**:

```powershell
Llamar-Cerrar @{ commit = $true; confirmado = $true } | ConvertTo-Json -Depth 6
```

**Paso 5** — la respuesta tiene que declarar **`"filas_afectadas": 2`** y
`"estado": "cerrado"` (R22). Ni 1 ni 3: 2.

**Paso 6** — releer `con.est`: tiene que ser el `est` que `conest` da para
`cod = 'CER'`, y las dos lecturas tienen que coincidir:

```powershell
Leer-Sigrid "SELECT c.est, e.cod, e.res FROM dbo.con c LEFT JOIN dbo.conest e ON e.tip = c.tip AND e.est = c.est WHERE c.tip = ? AND c.cod = ?" @(708, $incidencia)
Leer-Sigrid "SELECT est, cod, res FROM dbo.conest WHERE tip = ? AND cod = ?" @(708, "CER")
```

**Paso 7** — la fila nueva de `dbo.log`, **campo a campo** contra `design.md`
§7.3 (R24, R25):

```powershell
Leer-Sigrid "SELECT ide, emp, ori, ope, fec, hor, usu, tab, tip, cod, res, tex, est FROM dbo.log WHERE ide > ? AND tab = ? AND tip = ? AND cod = ?" @($logAntes, "con", 708, $incidencia)
```

Valores esperados, **todos con su número real y ninguno con `?`**:

| Campo | Valor que tiene que salir |
|---|---|
| `ide` | `$logAntes + 1` |
| `emp` | el `emp` **de la reclamación**, no una constante |
| `ori` | `0` |
| `ope` | `5` (proceso ejecutado) |
| `fec` | `AAAAMMDD` como **entero**, hoy, en hora **local** `Europe/Madrid` |
| `hor` | `HHMMSS` como **entero** — **mirar la hora**: es la decisión §3.3.a del informe, la única que no se pudo tomar con un dato. Si sale con dos horas de menos, es que se escribió UTC y hay que arreglarlo |
| `usu` | el login del ERP, sin truncar (máx. 48) |
| `tab` | `con` |
| `tip` | `708` |
| `cod` | el código de la reclamación |
| `res` | el `res` de la reclamación |
| `tex` | exactamente `Cerrar parte (postventa-incidencias)` |
| `est` | `1` |

**Paso 8** — que **`con.tiemod` no se ha movido** (F-008 §2.3): comparar con el
`tiemod` anotado en el paso 1.

```powershell
Leer-Sigrid "SELECT ide, est, tiemod FROM dbo.con WHERE tip = ? AND cod = ?" @(708, $incidencia)
```

**Paso 9** — la traza local: `estado = 'cerrado'`, con sus dos códigos de
estado y su `confirmado_por`, y **sin el login** (R41, R43). Mismo bloque de
PostgreSQL del T23.2, cambiando la consulta:

```powershell
$env:SQL_TEMP   = "SELECT hash_parte, numero_incidencia, estado, estado_origen_sigrid, estado_destino_sigrid, dry_run_at_utc, cerrado_at_utc, confirmado_por, motivo, intentos FROM postventa.cierres WHERE hash_parte = %s"
$env:CLAVE_TEMP = $hash
```

La tabla **no tiene columna de login** a propósito; si apareciera un login en
`motivo`, es un defecto de R43.

### T25 · que el `tex` propio hace lo que se diseñó (R25)

Dos lecturas. La primera tiene que **encontrar** el cierre nuevo (seguimos
apareciendo en los informes de Posventa, que filtran por `Cerrar parte%`); la
segunda tiene que devolver **exactamente los cierres de este servicio** y
ninguno manual:

```powershell
Leer-Sigrid "SELECT COUNT(*) FROM dbo.log WHERE tab = ? AND cod = ? AND tex LIKE ?" @("con", $incidencia, "Cerrar parte%")
Leer-Sigrid "SELECT ide, cod, usu, fec, tex FROM dbo.log WHERE tab = ? AND tex = ? ORDER BY ide DESC" @("con", "Cerrar parte (postventa-incidencias)")
```

### T26 · que el guard de escritura acepta el batch tal cual

**Se comprueba dentro de T24, en el paso 4**: si `SqlWriteGuard` rechazara la
sugerencia de tabla `WITH (UPDLOCK, HOLDLOCK)`, el `commit` devolverá un `502`
con el motivo, y `Llamar-Cerrar` lo imprime. **No se improvisa otra vía**: se
anota el motivo, se marca la feature `blocked` y se para.

### T27 · reintento sobre lo ya cerrado (R18, R42)

Repetir T24 sobre **la misma** incidencia. Tiene que salir `ya_cerrada`, **sin
escribir nada** y sin pisar la traza local:

```powershell
Llamar-Cerrar @{ commit = $true; confirmado = $true } | ConvertTo-Json -Depth 6
(Leer-Sigrid "SELECT MAX(ide) FROM dbo.log" @())[0][0]
```

El segundo comando tiene que devolver **el mismo `ide`** que dejó T24: si ha
subido, se ha escrito una fila que no debía escribirse.

### Al terminar

Cerrar la ventana (comando de arriba), comprobar que imprime `false`, y marcar
T22–T27 en `specs/F-009-cierre-sigrid/tasks.md` **solo lo que se haya
ejecutado de verdad**.

---

## Cómo se mergeó F-005, y por qué importa para la próxima

Se mergeó **con squash** por indicación del reviewer. El árbol de la rama
estaba limpio, pero su historial no: el arreglo del FQDN del servidor
compartido cambió el fichero en `HEAD`, y los 24 commits anteriores seguían
conteniendo el valor. Con squash ese valor **no entró nunca en `dev`**.

Es la lección a repetir cuando una rama corrija un dato que no debió entrar:
el historial de git no suelta lo que entra, y el squash es la salida barata.

- **Con squash, el valor no entra nunca en `dev`.** Es lo que dictó el
  reviewer y lo que hay que hacer.
- Con un merge normal entraría. El reviewer valoró esa gravedad como **baja**
  y por eso no lo convirtió en bloqueo, pero la recomendación es clara.
- **No se reescribe** la historia de una rama de 31 commits: el coste y el
  riesgo superan al beneficio.

## Pendiente del humano (cola de decisiones)

1. ~~El commit en `azure-apps`~~ — **CERRADO el 2026-08-20: el humano no hace
   commits en `azure-apps`.** Es una decisión permanente, no una tarea
   pendiente: **no se vuelve a proponer**. Los dos ficheros
   (`postventa_incidencias.md` y la fila del `README.md`) quedan escritos en
   el árbol de ese repositorio y ahí se quedan. Consecuencia asumida: ese
   documento no tiene fecha comprobable ni historial.
2. ~~D6 de F-006~~ — **RESUELTA el 2026-08-20. F-006 ya NO está bloqueada.**
   La biblioteca, el app registration y los permisos **ya existen**, según el
   humano, y así lo confirmé en Azure: el registro `postventa-incidencias`
   está dado de alta y su service principal tiene consentimiento de
   administrador. **Su D3 sigue resuelta**: F-006 se cierra con la
   verificación de subida real diferida a F-010, lo que exigirá autorización
   expresa ante `CHECKPOINTS.md` C5. Ver «Lo que hay que saber de Graph»,
   abajo.
3. **P1 y P2 del reviewer de F-004** (propuestas de arnés, genéricas): afinar
   `CHECKPOINTS.md` C4 para las verificaciones manuales ya ejecutadas, y
   añadir a C5 el checkpoint de la deuda con dueño citado por identificador.
   Si se aceptan, viajan a `arnes-base` en el mismo trabajo. Texto literal en
   `progress/review_F-004.md`. **El reviewer de F-005 añadió una tercera**,
   sin aplicar, en la sección «Propuesta de mejora del protocolo» de
   `progress/review_F-005.md`.
4. **P4 · la campaña de mutación deja bytecode envenenado** (reviewer de
   F-007, 2026-08-20): con `--workers 1`, la mutación deja `__pycache__`
   alterado que **`git status` no enseña**, así que un árbol aparentemente
   limpio puede tener bytecode que no corresponde al fuente. Es genérica: si
   se acepta el arreglo, viaja a `arnes-base`.
5. **Campo `base` en `harness/features.json`** para que cobertura y mutación
   usen la base real de la rama. Aplazada; robustez para cuando se vuelvan a
   encadenar ramas.
6. **Decisión suelta**: si la regla de `docs/CONVENTIONS.md` sobre ReportLab
   frente a PyMuPDF sube a `arnes-base`. Recomendación del líder: dejarla
   aquí, porque solo sirve a proyectos que manipulen PDF.

## Estado del backlog

**No se duplica aquí.** `BACKLOG.md` se genera desde `harness/features.json` y
lo regenera `bash harness/init.sh`: está siempre al día, y esta sección no.
Copiar el estado a mano ya produjo un defecto —la review de F-007 lo cazó—, así
que la regla es mirar `BACKLOG.md` y no fiarse de ningún resumen escrito aquí.

Lo único que conviene tener a mano, porque no se lee del JSON: **F-010 ·
Despliegue subió de prioridad el 2026-08-20**, por delante de las dos features
de Sigrid, para que negocio pruebe el circuito desplegado sin tocar el ERP.
Además **F-010 desbloquea T18 de F-006**, la subida real a SharePoint.

## ⚠️ Los permisos de Graph son más amplios de lo necesario

Sigue vivo aunque F-006 esté cerrada. El service principal
`postventa-incidencias` tiene **tres** permisos de aplicación consentidos:
`Sites.Selected` (el que pedía la spec), **`Sites.ReadWrite.All`** y
**`Sites.FullControl.All`**. Los dos últimos alcanzan a **todos** los sitios de
SharePoint del inquilino y vuelven irrelevante al primero: nada impide
técnicamente que la aplicación escriba en el sitio de RRHH o de dirección.

**El humano decidió el 2026-08-20** cerrar F-006 con los permisos actuales y
recortarlos después, en **F-018 · Mínimo privilegio en Graph**, para no mezclar
un cambio de configuración del inquilino con una implementación. El riesgo
queda documentado en el `design.md` de F-006 citando a F-018. **La deuda tiene
dueño; no se pierde.**

**Su appId no se escribe en el repositorio**: se consulta con `az ad app list`.
Estuvo escrito aquí un rato y la review de F-006 lo cazó (H1).

**Dato reutilizable**: `partes` ya tiene cliente de SharePoint y proveedor de
token (`services/partes-persistencia/infrastructure/`), sobre **`httpx`**. De
ahí salió el patrón que usa F-006.

## Deuda declarada, con dueño

- **F-015 · control negativo de la firma** (heredado de F-004): la
  clasificación acertó sobre 22 firmas reales, pero **en la remesa no había ni
  un aspa ni una casilla vacía**, así que falta demostrar que no etiqueta
  `humana` lo que no lo es. Ya es criterio de aceptación de su ficha.
- **F-018 · mínimo privilegio en Graph** (nacida el 2026-08-20): recortar los
  permisos del app registration a solo `Sites.Selected`. Ver arriba.

## Observación abierta

**El SDK de Gemini avisa en cada llamada real**: «Direct use of automatic
function calling (AFC) in `Models.generate_content` is not recommended». No
rompe nada, pero sugiere que el schema se pasa de una forma que activa la
llamada automática de funciones. Merece una revisión de
`services/postventa-api/infrastructure/llm/gemini.py`. **No bloquea.**

## Apuntes para features futuras

- **F-014 · Reagrupar el parte de dos hojas.** La remesa de Mirasierra **no
  sirve** para verificarla: sus 22 partes dieron `numero_pagina` «1». Hará
  falta **otro escaneo**, pedido al humano antes de empezar.
- **F-015 · Evaluación del prompt de extracción.** Línea base medida sobre 22
  partes reales: impresos ~99 de confianza media, manuscritos 82-90
  (`dni_cliente` 89,3; `observaciones` 82,5). Sospecha a medir: la **regla 1
  de `config/prompts.yaml`** nombra la fecha de servicio como «casi siempre en
  blanco» y podría estar induciendo falsos negativos. Ojo: el test R4 clava la
  huella `2306ac1d07f1` del prompt, así que quien lo cambie actualiza la
  constante a conciencia y vuelve a medir.
- **F-016 · Interpretación automática de las observaciones manuscritas.**
  Dato de dimensionado: **2 de 22 partes (~9 %)** traen observaciones.

**Hallazgo de dominio que sigue vigente**: «cerrar parte» en Sigrid **exige
documento adjunto**. Está en `docs/ARCHITECTURE.md` y en `docs/referencia/`.

## La base de datos, ya creada

`postventa` existe en `psql-albaranes-rs9k2` desde el 2026-08-19, con su rol
propio `postventa_app`, su esquema `postventa`, seis tablas vacías y 13
índices. **Nada nuestro en `public`.** El DDL se demostró idempotente contra
el motor real, no solo contra un doble.

Somos el **cuarto inquilino** de ese servidor, junto a `albaranes`, `partes` y
`datamart-seg-anual`. Las reglas duras sobre él siguen vigentes: ningún DDL
fuera del esquema propio y nada a nivel de servidor.

**El `.env`** de `services/postventa-api/` ya tiene las variables `PG_*` con la
credencial real. No se versiona y ningún agente lo toca. Los campos de
`config/settings.py` van **en español** (`pg_base`, `pg_usuario`,
`pg_esquema`) y exponen su `validation_alias` **en inglés** (`PG_DB`,
`PG_USER`, `PG_SCHEMA`): eso es deliberado, y es lo que lee el `.env`.

## Los scripts de las verificaciones manuales

Viven **fuera del repositorio**, en el home del humano, porque PowerShell
parte los comandos largos al pegarlos:

- `f3_modelo.py`, `f3_humo.py`, `f3_real.py` — F-003.
- `f4_firma.py` — F-004.
- `f5_ddl_dryrun.py` — el dry-run del DDL de F-005: imprime las 14 sentencias
  sin abrir conexión.
- `f5_comprobar_base.py` — comprobación **de solo lectura** del catálogo de la
  base real: tablas, índices, nada en `public`, recuento de filas.
- `t18_sembrar_parte.py` — F-010, T18: siembra el **parte sintético**,
  comprueba su traza y **la borra** al terminar. Es lo que desatasca el
  `ForeignKeyViolation` del defecto 15 mientras F-019 no exista.
- `t18_consola.js` — el fragmento para la **consola del navegador en el
  front**, que es la vía que sí funciona desde el defecto 13. Su copia
  versionada está en `docs/DESPLIEGUE.md` §5 bis.
- `t18_logs.ps1` y `t18_diagnostico.ps1` — lectura de Application Insights y
  del **cuerpo** de los errores, que es lo que faltaba para leer el 500 mudo.

Ninguno imprime ni escribe valores extraídos de un parte real.

### ⚠️ Defecto 16 · el DSN se compone SIN contraseña, a propósito

Para quien repita esta verificación: `dsn_desde_ajustes` **no** mete la
contraseña en la cadena de conexión, y es **deliberado** —así no acaba en un
log—. Hay que pasarla **aparte** en `psycopg.connect`, exactamente como hace
`services/postventa-api/infrastructure/persistencia/fabrica.py`:

```
conexion = psycopg.connect(dsn, password=ajustes.pg_password)
```

Un script de verificación que use `dsn_desde_ajustes` y no lo sepa **muere con
`fe_sendauth: no password supplied`**, y el mensaje no dice nada de esto.

## Contexto del arnés

- **Arnés 1.5.2**, verificado contra el payload de `arnes-base`. La campaña de
  mutación conserva el análisis de supervivientes al repetirse, **pero no el
  de los timeouts**, que hay que copiar a mano al informe de implementación.
- **`harness/rutas_sensibles.json` no existe**, así que `CHECKPOINTS.md`
  C4 ter sale N/A. Su declaración completa es **F-015**.
- Los agentes del arnés están cargados: **se delega**, el líder orquesta.

## Cinco lecciones operativas vigentes

1. **Dos agentes a la vez en la misma rama se pisan en el índice de git.** Un
   `git add -A` de uno arrastró al commit el trabajo del otro. Si se
   paraleliza: cada agente en su worktree, o `git add` con rutas concretas.
2. **Los subagentes SÍ pueden trabajar en paralelo sin pisarse si cada uno va
   en su propio worktree** (`.claude/worktrees/`, ya ignorado).
3. **El humano trabaja en PowerShell.** No admite `&&`, y al pegar comandos
   multilínea con Python en `-c` los indenta y revientan con
   `IndentationError`. Para cualquier verificación manual: **un script y una
   línea corta para invocarlo**.
4. **Un subagente puede colgarse dejando el trabajo casi hecho.** Pasó tres
   veces con F-005, siempre al escribir el informe final. Antes de relanzar
   nada, **mirar `git log` y `git status`**: la respuesta suele ser un cierre
   de diez minutos, no rehacer la tarea. Y a un agente caído se le puede
   **reanudar con su contexto intacto** en vez de empezar de cero.
5. **Un informe se escribe incremental, no al final.** Es la contrapartida de
   la lección 4: lo que ya está en disco sobrevive a la caída.

---

## 2026-09-15 · Spec de F-028 escrita (spec-author)

Escrita `specs/F-028-rechazo-manual/` con sus tres ficheros: `requirements.md`
(45 requisitos EARS, 5 preguntas abiertas), `design.md` y `tasks.md` (25 tareas
en 9 bloques pequeños, porque los encargos al implementer se dan de uno en uno).
**No se ha tocado ni una línea de código.**

### Lo que la spec propone, en corto

- **Asunto 1 · rechazo manual.** No inventa mecanismo: reutiliza la revocación
  que F-026 ya modeló. Motivo nuevo `MotivoRevocacion.RETIRADA_HUMANA`, dos
  columnas más en `postventa.aprobaciones` (`revocada_por`, `revocada_nota`),
  endpoint propio `POST /api/rechazar` con cuerpo mínimo —`hash_parte`,
  `usuario_oid`, `confirmado: true`, `nota` opcional—, y botón en el detalle
  del parte. El front no necesita tocar `aprobacionVale`: en cuanto el bloque
  dice «revocado», el parte vuelve solo a su color y sale de la tanda.
- **Asunto 2 · espacios.** El arreglo va en `normalizar_codigo`
  (`domain/models/nombrado.py`): elimina los espacios que flanquean a un
  separador, y las dos conversiones pasan a componerse por **tramos**, con lo
  que quedan inversas exactas. `a_codigo_de_sigrid` gana además el caso
  `RS26.09-0149` (guion pegado), que hoy tampoco encontraba la reclamación.

### El riesgo de la huella: contestado, y la respuesta es que no hay riesgo

`huella_de_veredicto` normaliza con `aprobacion.py::_normalizar`, que es **otra
función** —recorta, colapsa y baja a minúsculas, sin tocar separadores— y
`aprobacion.py` **no importa nada de `nombrado.py`**. Además, lo que entra en
la huella son los valores **crudos** de la extracción. Conclusión medida:
**cambiar `normalizar_codigo` no cambia ni una huella**, y no revoca ninguna
aprobación vigente. El bloque 7 de `tasks.md` lo fija con tres controles
negativos, uno de ellos con las huellas escritas literales.

Queda declarado, eso sí, un **defecto latente de F-026 que esta spec NO
arregla**: hoy una relectura que solo cambie los espacios alrededor de la barra
**sí** revoca la aprobación («revocar por nada», contra su R32). Alinear las
dos normalizaciones lo arreglaría, pero cambiaría las huellas ya escritas y
revocaría las aprobaciones que ya hay en la base desde el despliegue. Va como
pregunta abierta **P5**.

### Lo que necesita decidir el humano antes de implementar

| # | Pregunta | Propuesta por defecto |
|---|---|---|
| P1 | ¿Rechazar un parte ya archivado y cerrado? | **No**, y la puerta se pone en el **cierre** (`cierres.estado` en `cerrado`/`ya_cerrada`), no en el archivo: archivado-sin-cerrar sí se puede rechazar, con aviso de que el PDF sigue en SharePoint |
| P2 | ¿Motivo en texto? | Texto libre **opcional**, 500 caracteres, en columna propia y nunca dentro del motivo cerrado |
| P3 | ¿Quién puede rechazar? | Cualquiera que pueda aprobar, con su `oid` registrado |
| P4 | **Nueva** · ¿histórico de decisiones? | **Sí**: tabla append-only `postventa.decisiones_aprobacion`. Sin ella el criterio «la traza conserva las dos decisiones en orden» **no se puede cumplir**: hoy volver a aprobar pone la revocación a `NULL` y borra el rechazo |
| P5 | **Nueva** · ¿alinear `_normalizar` con `normalizar_codigo`? | **No**, por lo dicho arriba |

P1, P2 y P4 **bloquean** el arranque del asunto 1 (cambian el diseño). P3 no
bloquea. El asunto 2 (bloques 6 y 7) se puede arrancar sin ninguna de las
cinco, y es el que desbloquea un cierre que hoy falla en real.

### Un aviso para el implementer que el humano debe conocer

El arreglo de los espacios cambia la expectativa de **un** test ya existente:
`test_f006_r8_los_espacios_interiores_se_colapsan_a_uno`. Va con su enmienda
fechada a R8 de F-006 (T19) y el implementer tiene obligación de decirlo en su
informe. Ningún otro test de F-006 ni de F-009 cambia.

---

## 2026-09-15 · F-028 REPLANTEADA: la spec anterior queda anulada y rehecha

**El bloque anterior de este fichero —«Spec de F-028 escrita»— describe una
feature que ya no es la que se va a hacer.** El humano replanteó F-028 ese
mismo día: no es «rechazar un parte aprobado», es **un modelo de estado
explícito del parte**. La ficha de `harness/features.json` está reescrita con
todo, la rama pasa a `feature/F-028-estado-del-parte` y la carpeta
`specs/F-028-rechazo-manual/` se ha **borrado** y sustituida por
`specs/F-028-estado-del-parte/`. Lo que sigue valiendo del bloque anterior: las
mediciones, el apartado de los espacios y la respuesta sobre la huella.

### Qué pide ahora, en sus palabras

*«los partes pueden estar pendientes, rechazados, aprobados o cerrados; lo que
quiero es poder cambiar el estado desde donde esté a aprobado o rechazado, y
que se guarde un histórico del estado».*

Nueve decisiones **ya tomadas** por él (D1–D9 en `requirements.md`): cuatro
estados; el apto **nace aprobado** y el histórico dice que lo decidió la
máquina; el no apto nace `pendiente`; una persona mueve a `aprobado` o
`rechazado` desde los otros tres; `cerrado` es **terminal** y la web lo explica;
motivo **obligatorio** al rechazar y opcional al aprobar; puede cambiarlo
cualquiera que entre, con su `oid` opaco; histórico **append-only**; y las dos
normalizaciones **no se alinean**. **No hay preguntas abiertas.**

### La decisión de diseño, que es la que el humano debe mirar

**El estado se DERIVA, no se guarda.** No hay columna `estado` en ninguna
tabla. Sale de una sola función de dominio puro sobre tres hechos que ya tienen
dueño: el veredicto (`validaciones`), la última decisión humana (el histórico
nuevo) y la traza de cierre (`cierres`). El argumento decisivo: `cerrado`
**pertenece al ERP**, y guardar una copia nuestra es la forma de acabar diciendo
que un parte está cerrado cuando no lo está. La comparación completa, con lo que
cuesta cada opción, está en `design.md` §3.

Consecuencias que conviene que vea antes de aprobar:

1. **Se retira el atajo del parte apto** en las tres puertas del backend. Hoy un
   parte verde no consulta nada antes de archivar («22 consultas por paso» dice
   su propia docstring), y **mientras eso siga así, rechazar un parte verde es
   un botón que no hace nada**. Coste declarado: 66 consultas por tanda de 22
   partes contra el PostgreSQL compartido.
2. **`POST /api/aprobar` se retira** y lo sustituye `POST /api/estado`. Dos
   endpoints que escriben la misma decisión divergen. Es la parte que más código
   de F-026 toca, y F-026 se cerró ayer.
3. **`postventa.aprobaciones` se congela y se siembra**: no se borra —tiene la
   aprobación real del despliegue— y sus filas vigentes pasan al histórico con
   un `INSERT … SELECT … WHERE NOT EXISTS` idempotente dentro del DDL.
4. **La aprobación puede revivir**: si el veredicto cambia y luego vuelve a ser
   el que se aprobó, la aprobación vuelve a contar. Es coherente con F-026 R32
   —se aprobó *ese* veredicto— y sale gratis al derivar. Declarado en
   `design.md` §11.3 por si prefiere lo contrario.

### Lo que no cambia respecto a la versión anterior

El asunto 2 (los espacios de los códigos) va tal cual: arreglo en
`normalizar_codigo`, las dos conversiones por **tramos**, tabla de
equivalencias, y **un solo test existente cambia de expectativa**
(`test_f006_r8_los_espacios_interiores_se_colapsan_a_uno`), con su enmienda
fechada a R8 de F-006. Y la respuesta sobre la huella sigue siendo que **no hay
riesgo**: `huella_de_veredicto` normaliza con otra función y el módulo no
importa `nombrado`; el bloque 8 de `tasks.md` lo fija con tres controles
negativos.

### Cómo queda la spec

`specs/F-028-estado-del-parte/` con `requirements.md` (59 requisitos EARS y las
nueve decisiones listadas para que nadie las reabra), `design.md` y `tasks.md`
(28 tareas en 11 bloques pequeños, uno por encargo). **Ni una línea de código
tocada.**

---

## F-028 · bloques 0 y 1 hechos (2026-09-15, implementer)

Rama `feature/F-028-estado-del-parte`, 5 commits locales sobre `ed46181`,
arnés en verde. **T1, T2, T3 y T4 cerradas**; el bloque 2 (persistencia, T5–T7)
es el siguiente encargo.

Lo entregado es **dominio puro**: `domain/models/estado.py` con los cuatro
estados, `DecisionEstado`, `SituacionParte` y la derivación
`estado_del_parte`; dos errores nuevos en `errores.py`; y el bloque 0, la red
de seguridad de las tres puertas, que salió **verde antes de tocar nada**
—ninguna puerta está floja hoy—.

Ni una línea fuera de `domain/`: `application/`, `infrastructure/`,
`interface_adapters/` y el front siguen exactamente como los dejó F-026.

Cobertura de líneas cambiadas 100,0 % (59/59); mutación 11/11 muertos, 0
supervivientes (los 2 de la primera campaña eran huecos reales y se cerraron
con un test cada uno). **Sin desviaciones respecto a la spec.**

Detalle completo, trazas de la fase RED y evidencias: `progress/impl_F-028.md`.

---

## F-028 · bloque 3 hecho (2026-09-15, implementer)

Rama `feature/F-028-estado-del-parte`, **2 commits locales** sobre `7cab1cb`
(`4c0934a` T8, `117421e` T9), arnés en verde. **T8 y T9 cerradas**; el bloque 4
—las tres puertas, T10 y T11— es el siguiente encargo, y es el primero que
**afloja** algo que hoy funciona.

Lo entregado es la **regla de constancia** de `design.md` §4: si el estado
derivado no es el de la última fila, se añade una fila. `paso_persistencia` la
aplica tras guardar el veredicto y `paso_cierre` tras el cierre. La regla vive
en `application/pipelines/constancia.py` —fichero nuevo, y la **única
desviación** de la spec, que no lo listaba— por lo mismo que `confianza.py` en
F-004: dos copias divergen, y en una campaña de mutación cada copia se cuenta
aparte.

**Las tres puertas no se han tocado** y `tests/test_f028_puertas.py` sigue en
verde sin editarlo (16 pasados). Tampoco se ha retirado nada de F-026: eso es
T15.

**El caso que hay que conocer**: si la base falla al apuntar la fila
`→ cerrado`, el error **se traga**. La incidencia ya está cerrada en el ERP de
producción y su traza —de donde se deriva el estado— ya está guardada; dejarlo
salir convertiría un cierre que ocurrió en un 503 «vuelve a intentarlo». La
fila la recupera el siguiente reproceso.

Cobertura de líneas cambiadas 100,0 % (158/158). Mutación: 18/18 muertos, 0
supervivientes, **pero ni un mutante del código de este bloque** —la
herramienta no muta comparaciones de identidad y aquí no hay otra cosa—, así
que se mutaron **a mano los nueve puntos** del bloque: **9 de 9 muertos**.
Queda anotado para el líder que `harness/mutacion.py` debería avisar de los
ficheros en alcance que no producen ningún mutante (propagable a `arnes-base`).

Detalle completo, trazas de la fase RED, los nueve mutantes a mano y las
decisiones: `progress/impl_F-028.md` §19 a §26.

---

## F-028 · bloque 4 hecho (2026-09-15, implementer)

Rama `feature/F-028-estado-del-parte`, **2 commits locales** sobre `2393fa2`
(`4130495` T10, `51fbe77` T11), arnés en verde. **T10 y T11 cerradas**; el
bloque 5 —el borde HTTP, T12 a T15— es el siguiente encargo.

**Lo que este bloque hace posible, que era medio encargo de la feature: un
parte apto que una persona rechaza ya no se archiva, ni se adjunta, ni cierra
su incidencia.** Hasta `51fbe77` eso era imposible por construcción —la puerta
devolvía «pasa» en cuanto el veredicto era apto, sin consultar nada—, y la
traza del test en rojo que lo demuestra («DID NOT RAISE ParteNoApto», tres
veces, una por puerta) está pegada en el informe.

Las tres puertas exigen ahora `estado_del_parte(...) is EstadoParte.APROBADO`
con la situación leída **del repositorio y nunca del cuerpo**, y **se retira el
atajo del apto**: todos los partes pagan una consulta por paso. El coste está
declarado en `design.md` §6 (66 consultas por tanda de 22) y **se añade una
verificación MANUAL** para medirlo en la primera tanda real contra el
PostgreSQL compartido.

La puerta vive en `application/pipelines/puerta_de_estado.py` —fichero nuevo, y
la **única desviación** de la spec, que listaba los tres pasos— por lo mismo
que `constancia.py` en el bloque 3: es la única decisión que separa un parte
sin revisar de un cierre en el ERP, y tres copias son tres sitios donde puede
aflojarse.

**`tests/test_f028_puertas.py` pasa de 16 a 48 casos y los 16 de T1 siguen
intactos** (el diff solo borra imports y dos firmas de ayudante). Siete tests
de antes cambian, todos justificados uno a uno en el informe: **cinco
retirados de F-026** —su mecanismo desaparece y su sustituto de F-028 está
escrito y verde, incluido el que fijaba el atajo del apto—, uno de F-028 que
ahora falla antes y mejor, y el control de campos del contexto de F-003.

**Para el bloque 5**: el único sitio de producción que todavía lee
`consultar_aprobacion` es `interface_adapters/api/parte.py:131`, que es justo
lo que T14 sustituye. Y quedan **dos casos inertes** en
`tests/test_f026_puertas.py` que T15 debería retirar con `Aprobacion`.

Cobertura de líneas cambiadas 100,0 % (183/183). Mutación: 19/19 muertos en la
campaña automática —que **solo genera un mutante de este bloque**, porque la
herramienta no muta comparaciones de identidad— más **13 mutados a mano, 13
muertos**, entre ellos los tres que reabren la puerta al `rechazado`, al
`cerrado` y al que no consulta el almacén.

Detalle completo, trazas de la fase RED, los tests cambiados y las decisiones:
`progress/impl_F-028.md` §27 a §35.
