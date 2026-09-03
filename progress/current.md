<!-- progress/current.md -->
# Sesión activa

> ## Estado al 2026-09-03 · **H1 y H2 arreglados: el despliegue ya aprovisiona Sigrid y rearma el candado del cierre**
>
> Los dos hallazgos de despliegue del §8 de `progress/guion_bloque8_F-009.md`,
> aprobados por el humano hoy. Informe completo, con el cotejo variable a
> variable: **`progress/impl_H1_H2_despliegue.md`**. Commit `82fbfb8` aquí y
> `9bc0518` en `azure-apps`. **Sin `push` en ninguno de los dos.**
>
> - **H1** · El despliegue no traía **ninguna** de las ocho variables de F-009.
>   Ya las trae: tres por referencia a Key Vault (`sigrid-api-base-url`,
>   `sigrid-api-key`, `sigrid-base-datos`) y cinco en `$ajustes`. Son **tres**
>   secretos y no uno porque la raíz de la pasarela es un host interno y
>   `SIGRID_BASE_DATOS` es el nombre de la base de producción del ERP: ninguno
>   de los dos puede quedar escrito en el repositorio, igual que `pg-host`.
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
> 1. **Queda a mano subir los tres valores al Key Vault**: los da el dueño de
>    `sigrid-api` y no pueden entrar al repositorio. El **Paso 0** del §1 del
>    guion sigue ahí, con los dos caminos (redesplegar, o poner las App Settings
>    sueltas si no se quiere redesplegar el entorno actual).
> 2. **Se tocó un test de F-010**, contra la instrucción de no tocar
>    `services/`, porque era imposible no hacerlo: `test_f010_r28` exigía
>    literalmente que **no** hubiera ninguna variable `SIGRID_*` en el
>    despliegue. Su premisa —«el ERP está fuera del piloto»— cae con la
>    aprobación de hoy; lo que protegía, no, y es lo que comprueba ahora.
>    **R28 sigue escrito en `specs/F-010-despliegue/requirements.md` con su
>    texto original y ya no describe el sistema**: enmendarlo o no es decisión
>    del humano. Detalle en el §5 del informe.
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
$sigridUrl  = az functionapp config appsettings list -g $grupo -n $funcion --query "[?name=='SIGRID_API_BASE_URL'].value" -o tsv
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
$env:PG_HOST     = az functionapp config appsettings list -g $grupo -n $funcion --query "[?name=='PG_HOST'].value" -o tsv
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
