<!-- specs/F-025-confirmacion-unica/requirements.md -->
# F-025 · Archivar y cerrar en una sola confirmación — Requisitos

> Notación EARS (`specs/SPECS.md`). Cada requisito se traduce a **al menos un
> test trazable** `test_f025_rN_*`. Rigor `critico`.
>
> Esta feature **no añade ninguna escritura nueva** al ERP ni a SharePoint:
> quita un paso de pantalla y junta en un gesto los tres que ya existían. Pero
> el gesto que junta **escribe en un ERP de producción**, así que el rigor es
> el mismo que el de F-009 y F-012.

## Alcance

**Entra**: el circuito del front desde que el usuario decide archivar hasta
que la incidencia queda cerrada en Sigrid; el número y el orden de las
llamadas; qué ve mientras tanto; qué pasa si falla a mitad; y las **enmiendas
fechadas** a los requisitos aprobados de F-009 y F-012 que esta decisión
deroga.

**No entra**: el contrato HTTP de `/api/archivar`, `/api/adjuntar` y
`/api/cerrar`, que **no cambia ni una clave**; las comprobaciones que el
backend hace antes de escribir, que **no se tocan**; los partes que la
validación mandó a revisión o a la cola humana, que siguen sin archivarse
(poder aprobarlos es **F-026**, otra feature); y el auto-cierre guardado
(R13/R14 de F-009), que sigue como está.

---

## 0 · La decisión que manda sobre todo este documento

**Decisión del responsable del proyecto, del 2026-09-11**, tomada después de
verificar el circuito completo contra el ERP real. Literal:

> «Quiero que al darle a archivar los partes aptos me pida confirmación como
> ahora, y al confirmar ya haga el proceso de cierre.»

Se le planteó **de forma explícita** que la pantalla previa es justamente lo
que protege de cerrar la incidencia equivocada si la extracción leyó mal el
número del papel. Respondió, literal:

> «no hace falta enseñar nada»

**Es su decisión, está tomada y este diseño la respeta. No se reabre.**

> ### Lo que se pierde, por escrito
>
> Hasta hoy, entre el cálculo y la escritura había una persona leyendo el
> número de incidencia, la descripción de la reclamación y el estado del que
> salía. Esa lectura era la última oportunidad de parar un error de
> extracción.
>
> **Lo que pasa a partir de F-025**: si la IA leyó mal el número de incidencia
> del papel, y el número mal leído **existe en el ERP y está en un estado que
> admite cierre**, el sistema adjuntará el parte a **esa otra reclamación** y
> **la cerrará**, sin que nadie lo haya visto antes. Las comprobaciones del
> backend no lo impiden: comprueban que la reclamación existe y que se puede
> cerrar, no que sea **la que toca**.
>
> Qué lo hace acotado, y no es lo mismo que decir que no pasa:
> - El número de incidencia es uno de los **dos campos que deciden** la
>   aptitud (F-004): un parte cuyo número no se leyó, o se leyó por debajo del
>   umbral de confianza, **no llega a ser apto** y no entra en la tanda.
> - Un número mal leído tiene que **existir** en el tipo de posventa del ERP
>   para que pase de `ReclamacionNoLocalizada`; y tiene que estar abierto para
>   pasar de `EstadoNoCerrable`.
> - Los cierres **se deshacen** en el ERP: 81 precedentes medidos por F-008.
>   El gráfico adjunto, en cambio, se borra desde la UI de Sigrid a mano.
> - **R30** obliga a enseñar, al terminar, el número de incidencia sobre el
>   que se escribió: es la primera ocasión en que quien pulsó puede darse
>   cuenta, y por eso deja de ser opcional.

---

## 1 · Una sola confirmación, y sin ella no se escribe nada

**R1.** CUANDO el usuario pulsa el botón de archivar los partes aptos, el
sistema debe pedir **una** confirmación explícita y, al recibirla, ejecutar
para cada parte de la tanda los **tres pasos** —archivar en SharePoint,
adjuntar el parte a su reclamación y cerrarla— sin volver a pedir nada.

**R2.** El sistema **no debe** pedir ninguna segunda confirmación entre el
archivo y la escritura en el ERP: en todo el circuito hay **exactamente una**.

**R3.** SIN esa confirmación, el sistema **no debe** ejecutar ninguna
escritura: ni la subida a SharePoint, ni el gráfico, ni el cambio de estado.

**R4.** La confirmación debe **caducar**, y un segundo clic fuera de la
ventana **no debe** disparar nada (mismo mecanismo y mismo módulo que R19 de
F-007, R15 de F-009 y R66 de F-012: `js/confirmacion.js`, sin cambios de
lógica).

**R5.** El sistema **no debe** ofrecer, antes de esa confirmación, ninguna
pantalla que muestre el cálculo previo del gráfico ni el del cierre.

> R5 es lo que deroga R63 de F-012. Ver §7.

**R6.** El texto de la confirmación debe nombrar **las tres cosas que van a
pasar** —el archivo en SharePoint, el documento adjunto a la reclamación y el
cierre de la incidencia— y el **número de partes** afectados. Quien confirma
no ve el detalle, así que el aviso tiene que ser exacto sobre el alcance.

---

## 2 · El circuito: tres llamadas por parte, y en este orden

**R7.** CUANDO se confirma la tanda, el sistema debe ejecutar para cada parte,
**en este orden**: `POST /api/archivar`, después `POST /api/adjuntar` con
`commit` y `confirmado`, y después `POST /api/cerrar` con `commit` y
`confirmado`.

**R8.** El front **no debe** emitir ninguna llamada a `/api/adjuntar` ni a
`/api/cerrar` con `commit` ausente o falso: el cálculo previo ya no se pide
por separado.

**R9.** El sistema **no debe** ejecutar más de **tres** llamadas HTTP por
parte en el circuito de archivo y cierre.

**R10.** CUANDO se llama a `/api/adjuntar` o a `/api/cerrar` con `commit`, el
backend debe seguir ejecutando **dentro de la misma llamada y antes de
escribir** su comprobación previa contra el ERP (R20 de F-012 y R8 de F-009
siguen vigentes **sin cambios**), y **no debe** existir ningún camino que
escriba sin ella.

**R11.** Los tres pasos deben pasar por **la misma cola de concurrencia** y
con el mismo límite que el resto del proceso (R7 de F-007): la tanda no abre
más peticiones simultáneas de las que ya abría.

---

## 3 · Lo que ve el usuario mientras tanto

> Con un solo parte, el circuito medido tarda **~20 s** (§0 de `design.md`).
> Con veinte partes, se multiplica. Un botón que se queda quieto veinte
> segundos invita a pulsarlo otra vez, y esta vez lo que hay detrás escribe en
> un ERP de producción.

**R12.** MIENTRAS la tanda esté en curso, el sistema debe mostrar cuántos
partes van terminados **de cuántos partes tiene la tanda** (no del total de la
remesa).

**R13.** MIENTRAS un parte esté en curso, el sistema debe mostrar **en cuál de
los tres pasos está**: archivando, adjuntando o cerrando.

**R14.** MIENTRAS la tanda esté en curso, el sistema **no debe** permitir
lanzar una segunda tanda: ni desde el botón, ni por un segundo clic sobre la
confirmación.

**R15.** Un segundo clic sobre el botón de confirmar **no debe** disparar una
segunda tanda **aunque llegue dentro de la ventana**: la confirmación se
consume al primer clic.

**R16.** CUANDO termina la tanda, el sistema debe enseñar, **por parte**,
hasta dónde llegó: archivado, adjuntado, cerrado, ya cerrada, o el error que
lo paró.

---

## 4 · Qué pasa si falla a mitad

**R17.** SI el archivo de un parte falla, ENTONCES el sistema **no debe**
adjuntar ni cerrar ese parte.

**R18.** SI el adjuntado de un parte falla, ENTONCES el sistema **no debe**
cerrar esa incidencia.

**R19.** SI el cierre de un parte falla después de que su gráfico quedara
adjunto, ENTONCES el sistema debe dejar ese parte en el estado **«adjuntado
pero no cerrado»**, distinguible en pantalla y con salida propia (R65 de
F-012, sin cambios).

**R20.** SI un parte de la tanda falla en cualquiera de los tres pasos,
ENTONCES el sistema debe **seguir con los partes que quedan**: un parte roto
no tumba la tanda (R10 de F-007).

**R21.** SI una llamada del **ERP** —`/api/adjuntar` o `/api/cerrar`—
responde con la puerta de entorno (`503`, ventana de escritura cerrada o
configuración ausente), ENTONCES el sistema debe **dejar de pedir la mitad del
ERP** para los partes que queden, **seguir archivando** los que falten, y
decirlo **una sola vez** en su pantalla propia.

**R22.** SI la llamada de **archivo** responde con su puerta de entorno,
ENTONCES el sistema debe **detener la tanda**: sin archivo no hay nada que
adjuntar ni que cerrar.

**R23.** El sistema **no debe** reintentar por su cuenta ninguna escritura
fallida contra el ERP: el reintento lo pide una persona (R27 de F-009 y R28 de
F-012, sin cambios).

---

## 5 · El reintento no puede duplicar nada

**R24.** La tanda debe incluir **todos** los partes aptos y guardados que no
estén cerrados, **incluidos los que quedaron a medias** en una tanda anterior
—archivados sin adjuntar, o adjuntados sin cerrar—, y no solo los que aún no
se han archivado.

**R25.** CUANDO un parte de la tanda ya consta archivado, el sistema **no
debe** volver a subirlo a SharePoint: se salta ese paso y sigue por el
siguiente.

**R26.** CUANDO un parte de la tanda ya consta adjuntado, el sistema **no
debe** volver a mandar los bytes a la pasarela: responde desde la traza local
(capa 1 de R24 de F-012) y sigue por el cierre.

**R27.** CUANDO la reclamación ya está en el estado de cierre, el sistema debe
tratarlo como **éxito** y no como error (R18 de F-009 y R16 de F-012, sin
cambios), y decirlo en el resumen.

**R28.** El sistema **no debe** producir un segundo gráfico ni una segunda
fila de `dbo.log` por volver a lanzar la tanda sobre partes ya procesados. Las
**tres capas de idempotencia** de F-012 —traza local, pasarela por tamaño y
`sha256`, y `evaluar`— más la traza de archivo de F-006 siguen siendo el único
mecanismo: F-025 **no añade ninguna capa nueva** y **no puede saltarse
ninguna**.

---

## 6 · Lo que desaparece es la pantalla, no la verificación

> Esta sección es la diferencia entre **quitar un paso** y **escribir a
> ciegas**. Todos sus requisitos son **control negativo**: se verifican
> comprobando que el camino sigue ahí después del cambio.

**R29.** El backend debe seguir comprobando, antes de escribir, que la
**reclamación existe** en el tipo de posventa del ERP, y **no debe** escribir
nada si no la localiza.

**R30.** El backend debe seguir comprobando **en qué estado está** la
reclamación y **no debe** adjuntar ni cerrar una que no admita cierre; una ya
cerrada no recibe gráfico.

**R31.** El backend debe seguir comprobando si **el documento ya cuelga** de
la reclamación —traza local, y en la pasarela por tamaño y `sha256`— y **no
debe** duplicarlo.

**R32.** Las **puertas de aptitud y de archivo** de los dos pasos de escritura
(R14/R15 de F-012 y R16/R17 de F-009) deben seguir comprobándose **dentro del
paso**, aunque el veredicto llegue en el cuerpo de la petición.

**R33.** El **login de Sigrid** de quien confirma debe seguir resolviéndose y
**verificándose contra el ERP** antes de escribir nada (R29–R32 de F-009).

**R34.** El cierre debe seguir exigiendo que el parte **conste adjuntado**
(R2 de F-012) y llevando en el `WHERE` del `UPDATE` el estado de origen leído
en la comprobación previa (R11 y R23 de F-009).

**R35.** Las **puertas de entorno** —`ENTORNO`, `ARCHIVO_HABILITADO`,
`CIERRE_HABILITADO`— y la guardia de red de la suite **no se tocan**: F-025
**no debe** modificar ninguna de ellas para que el circuito nuevo funcione.

**R36.** El sistema **no debe** archivar, adjuntar ni cerrar un parte que no
sea `apto` con destino `archivo_y_cierre`, ni siquiera dentro de la tanda y ni
siquiera si el usuario pulsa dos veces. Los partes en revisión y los de la
cola humana **siguen fuera** (aprobarlos es **F-026**).

**R37.** CUANDO termina el circuito de un parte, el sistema debe enseñar el
**número de incidencia** de la reclamación sobre la que escribió.

> R37 no es cosmético y por eso está aquí y no en §3: al no haber pantalla
> previa, el resumen es **la primera y única ocasión** en que quien pulsó
> puede detectar que se escribió sobre la incidencia equivocada. Ver el
> recuadro «Lo que se pierde» de §0.

---

## 7 · Las enmiendas a F-009 y F-012

> **No se borra ningún requisito.** Se enmienda con un recuadro fechado que
> cita la premisa original **literal**, dice qué la invalidó y quién lo
> decidió. El patrón exacto es el de R28 de `specs/F-010-despliegue/requirements.md`,
> del 2026-09-03.

**R38.** El requisito **R63 de F-012** queda **derogado** y debe recibir su
recuadro de enmienda fechado el 2026-09-11, sin que se borre su texto.

> R63 dice hoy, literal: *«CUANDO el usuario pide «ver qué pasaría», el front
> debe pedir para cada parte cerrable **los dos dry-run** —gráfico y cierre, en
> ese orden— y enseñarlos juntos antes de ofrecer la confirmación.»*
>
> Lo invalidó la decisión del responsable del 2026-09-11 (§0): ya no hay un
> gesto «ver qué pasaría», así que no hay momento en el que enseñarlos.

**R39.** El requisito **R22 de F-012** queda **enmendado** en su momento, no
en su contenido: el caso idempotente se sigue detectando y se sigue diciendo,
pero **al terminar** y no «antes de confirmar».

> R22 dice hoy, literal: *«SI el dry-run responde `idempotente: true`,
> ENTONCES el sistema debe decirlo al usuario **antes** de confirmar: ese parte
> ya está dentro de Sigrid y el commit no escribirá nada.»*

**R40.** El requisito **R21 de F-012** y el **R49 de F-012** quedan
**enmendados en su justificación**: el endpoint sigue devolviendo el bloque
completo del cálculo previo y el estado del gráfico —el contrato de respuesta
**no cambia**— pero lo que se lee no es una pantalla anterior a la
confirmación, sino el resumen de lo que se hizo.

**R41.** El requisito **R50 de F-012** se **mantiene como regla** —el cálculo
previo del cierre no exige que el gráfico conste adjuntado— y se **enmienda su
justificación**: ya no es «para que los dos dry-run se puedan enseñar juntos
antes de confirmar», sino para que el contrato del endpoint siga siendo
consultable sin escribir.

**R42.** El requisito **R21 de F-009** **no recibe enmienda nueva**: ya fue
derogado por R48 de F-012 el 2026-09-06. Esta feature debe **comprobarlo y
decirlo**, no volver a derogarlo.

**R43.** Los requisitos **R8, R10, R11, R12, R13, R14 y R15 de F-009** y
**R20, R23, R64, R65, R66 y R67 de F-012** quedan **vigentes sin cambios**, y
la spec debe dejarlo escrito: lo que cae es la pantalla intermedia, no el
cálculo previo, ni la confirmación, ni el orden, ni la caducidad.

> R10 de F-009 —*«MIENTRAS no exista un dry-run correcto y reciente para esa
> incidencia, el sistema no debe ejecutar ninguna escritura contra Sigrid»*—
> **se sigue cumpliendo**, y ese es el hallazgo que sostiene todo el diseño: el
> cálculo previo se ejecuta **dentro de la misma llamada** que escribe. Ver
> `design.md` §2.

**R44.** Los requisitos **R19, R20, R21 y R22 de F-007** quedan **vigentes**;
R19 pasa a ser **la única** confirmación del circuito y su texto en pantalla se
amplía según R6.

---

## 8 · Datos personales, logs y secretos

**R45.** F-025 **no debe** hacer viajar ningún campo manuscrito ni ningún byte
de más: los cuerpos de las tres peticiones son **exactamente** los que ya
definen R20 de F-007, R57 de F-012 y R51 de F-009.

**R46.** Los textos nuevos de pantalla y de log **no deben** contener el DNI,
las observaciones manuscritas, el correo, el nombre ni el `oid` de quien
confirma (R44/R45 de F-009, R53/R54 de F-012).

---

## 9 · Documentación que la feature deja al día

**R47.** `docs/ARCHITECTURE.md` debe precisar, en el paso 7b del pipeline y en
el punto 6 de «Semántica de dominio», que la confirmación explícita es **una
sola** y cubre el archivo, el gráfico y el cierre, y que el cálculo previo
ocurre **dentro de la llamada que escribe**.

**R48.** El documento del proyecto en `azure-apps/` **no debe** tocarse por
esta feature, y la spec debe decir por qué: no cambia ningún endpoint, ningún
campo de sus cuerpos, ninguna variable de entorno, ninguna tabla ni ninguna de
las cinco puertas que ese documento describe. Lo que cambia es **quién llama y
cuántas veces**, que es interno.

> Comprobado el 2026-09-11 contra `azure-apps/postventa_incidencias.md`: sus
> puntos 1–5 de «las puertas» y las fichas de `/api/adjuntar` y `/api/cerrar`
> siguen siendo ciertos palabra por palabra después de F-025. **Lo que sí
> sigue pendiente allí es deuda de F-012** (su T32, paso 8), no de esta
> feature.

---

## Preguntas abiertas · las decide el humano al aprobar la spec

| # | Pregunta | Opciones | Recomendación |
|---|---|---|---|
| **P1** | ¿Se **retira del todo** el botón «Ver qué pasaría (no cierra nada)», o se conserva como consulta de solo lectura? | (a) retirarlo, y con él la fase `dry_run` y R63; (b) conservarlo como botón secundario que solo lee | **(a) retirarlo.** La ficha dice «quitar el paso de vista previa del circuito», y dejar dos caminos obliga a mantener vivos los dos y a probar los dos. El backend **conserva** su comportamiento de solo lectura por omisión, así que la consulta se puede recuperar en una feature futura sin tocar el contrato |
| **P2** | Sin identidad (`usuario_oid` vacío), ¿el botón único se deshabilita, o archiva y se para antes del ERP? | (a) deshabilitar el botón y decir por qué; (b) archivar igual y parar en `adjuntar` | **(a).** Hoy archivar no exigía identidad y cerrar sí; al fundirlos, archivar sin poder cerrar deja justo el estado a medias que la feature quiere evitar. El texto que ya existe («No se ha podido saber quién eres…») se reutiliza |
| **P3** | Texto del botón y de la confirmación | «Archivar y cerrar los partes aptos» / «¿Seguro? Se subirán a SharePoint, se adjuntarán a su reclamación y se cerrarán en Sigrid. N parte(s).» | El de la izquierda. Lo decide quien lo va a leer (Posventa) |
| **P4** | El riesgo del **tiempo de espera** en la llamada fusionada de `adjuntar` (ver `design.md` §12) | (a) aceptarlo y medirlo en la verificación manual; (b) bajar `GRAFICO_MAX_BYTES`; (c) subir `SIGRID_TIMEOUT_S` | **(a)**, y anotar el **tamaño en bytes** del parte, que es el número que F-012 se dejó sin medir. (c) no cabe: el escalonado de tiempos lo fija el proxy de 45 s |

---

## Trazabilidad de los requisitos que no llevan test unitario

| Requisito | Por qué no hay test unitario | Cómo se verifica |
|---|---|---|
| R7 (extremo a extremo), R29–R34 en su ejecución real | Exigen el ERP de producción con la ventana abierta | `MANUAL (humano)`, bloque 5 de `tasks.md`, sobre una incidencia **autorizada expresamente** por el responsable, con el procedimiento de F-012 |
| R21, R22 | La puerta de entorno real solo la produce el entorno desplegado | `MANUAL (humano)`; el **camino** sí tiene test unitario con un doble que levanta el error de entorno |
| R37 en su valor real | El número que se enseña sale del ERP | `MANUAL (humano)`; el test unitario fija que la clave viaja y se pinta |

Todo lo demás tiene test unitario **sin red, sin BBDD y sin IA**.
