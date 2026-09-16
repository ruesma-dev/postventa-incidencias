<!-- specs/F-026-aprobacion-humana/requirements.md -->
# F-026 · Aprobación humana de los partes que van a revisión — Requisitos

> Notación EARS (`specs/SPECS.md`). Cada requisito se traduce a **al menos un
> test trazable** `test_f026_rN_*`. Rigor `estandar`.
>
> Esta feature **no añade ninguna escritura nueva** al ERP ni a SharePoint, y
> **no afloja ninguna de las puertas** que los protegen. Lo que hace es abrir
> una puerta que hoy no existe: la de una persona que decide, sobre un parte
> concreto, que se archiva y se cierra **a pesar** de lo que dijo la máquina. Y
> deja esa decisión registrada.

## Alcance

**Entra**: el acto de aprobar un parte no apto, dónde se guarda esa decisión,
qué motivos son aprobables y cuáles no, cómo entra un parte aprobado en el
circuito de F-025, cuándo deja de valer una aprobación, cómo se distingue en
pantalla de un parte que siempre fue verde, y la **enmienda fechada** a R36 de
F-025 y a los puntos de `docs/ARCHITECTURE.md` que hoy dicen que solo se
archiva lo que declaró apto la validación automática.

**No entra**: las reglas de F-004, que **no se tocan** —quién va a cada destino
se sigue decidiendo igual—; el contrato de `/api/archivar`, `/api/adjuntar` y
`/api/cerrar`, que no cambia ni una clave de su cuerpo; las comprobaciones que
el backend hace contra el ERP antes de escribir; la interpretación automática
del contenido de una observación (eso es **F-016**); la pantalla de la cola de
validación humana (`GET /api/cola` sigue como está); y cualquier escritura
nueva dentro de Sigrid, incluido el texto de `dbo.log.tex` (ver §8 y **P6**).

---

## 0 · Lo que hay hoy, medido

Todo lo de esta sección está **[MEDIDO]** contra el código de la rama
`feature/F-025-confirmacion-unica` el 2026-09-11, con su fuente al lado. Lo que
no se pudo medir va marcado **[INFERIDO]** y se dice por qué.

1. **La validación reparte en tres destinos** y no hay más.
   `domain/models/validacion.py::Destino` declara `archivo_y_cierre`,
   `cola_validacion_humana` y `revision_manual`; `_destino()` manda a la cola
   **solo** al parte cuyo único motivo es `observaciones_manuscritas`, y todo
   lo demás a revisión manual. **[MEDIDO]**

2. **Solo el verde se archiva.** `services/postventa-front/js/pipeline.js::esArchivable`
   devuelve verdadero si y solo si `veredicto === "apto"` **y**
   `destino === "archivo_y_cierre"`, y los dos valores los pone la validación
   automática. `cuerpoDeArchivo`, `esCerrable` y `cuerpoDeGrafico` se apoyan en
   ella, y `pendientesDeCircuito` la usa como filtro de la tanda. **[MEDIDO]**

3. **El backend lo vuelve a comprobar tres veces**, y lo hace **dentro del
   paso**: `application/pipelines/paso_archivo.py::_exigir_apto`,
   `paso_grafico.py::_exigir_apto` y `paso_cierre.py::_exigir_apto` levantan
   `ParteNoApto` con la misma condición —`veredicto != APTO or destino !=
   ARCHIVO_Y_CIERRE`—. **[MEDIDO]**

4. **No existe ninguna forma de aprobar.** `grep -rn -i "aprobac|aprobad|aprobar"`
   sobre `services/` devuelve **siete** coincidencias y **ninguna es código**:
   seis son comentarios o docstrings de tests, y una es el comentario de
   `pipeline.js::pendientesDeCircuito` que dice, literal: *«Aprobarlos es F-026,
   otra feature»*. Ni endpoint, ni botón, ni columna, ni campo en ningún cuerpo.
   **[MEDIDO]**

5. **Un parte ámbar o rojo se queda parado para siempre.** Se puede ver
   (`abrirParte`), se pueden corregir sus nueve campos (`editarCampo`), se
   puede revalidar sin gastar IA (`revalidarYGuardar`) y la cola se puede leer
   (`GET /api/cola`), pero ninguna de esas acciones cambia su destino salvo que
   el dato corregido haga desaparecer el motivo. **[MEDIDO]**

6. **Corregir un campo decisivo ya «aprueba» hoy, y lo hace el dominio.** Si el
   único motivo era `codigo_obra_no_legible` o `numero_incidencia_no_legible` y
   la persona escribe el valor, `validar_parte` vuelve a emitir `apto` /
   `archivo_y_cierre` y el parte pasa a verde sin que nadie apruebe nada. Eso
   **ya funciona** y esta feature no lo toca. **[MEDIDO]**

7. **Y ahí hay un agujero, que esta feature declara.** `observaciones` es uno de
   los nueve campos editables del detalle (`index.html`, `x-for="nombre in
   CAMPOS"`), `aplicarEdiciones` admite el valor vacío y `normalizarValor("")`
   devuelve `null`. Así que **vaciar a mano la transcripción de la observación
   del cliente y pulsar «Revalidar» convierte hoy un parte ámbar en verde**, sin
   dejar traza de que lo decidió una persona; y como `upsert_parte` reescribe
   todas las columnas de campos, además **pisa la transcripción original** en
   `postventa.partes.observaciones`. **[MEDIDO]** sobre el código; **[INFERIDO]**
   que nadie lo ha hecho: no hay forma de saberlo, precisamente porque no hay
   traza. Ver **R31** y **P3**.

8. **Lo que sí se guarda ya de quién decide**: `postventa.cierres.confirmado_por`
   y `postventa.graficos.confirmado_por` llevan el `oid` opaco de Entra ID de
   quien confirmó la tanda, nunca su correo ni su nombre
   (`sql/06_cierres.sql`, `sql/09_graficos.sql`). `postventa.archivos` **no
   guarda a nadie**. **[MEDIDO]**

9. **Dentro de Sigrid no queda constancia de quién decidió nada más que el
   login**: el cierre escribe `dbo.con.est` y una fila de `dbo.log` con
   `tex = "Cerrar parte (postventa-incidencias)"` (constante
   `domain/models/cierre.py::TEXTO_LOG_CIERRE`) y `usu` = el login de Sigrid de
   quien confirmó. Ese texto es **constante y homogéneo** a propósito: es lo que
   hace el conjunto localizable con un solo `LIKE` y reversible. **[MEDIDO]**

10. **La validación se sustituye entera en cada guardado.**
    `infrastructure/persistencia/sentencias.py::upsert_validacion` hace
    `ON CONFLICT (hash_parte) DO UPDATE SET` sobre **todas** las columnas menos
    la clave. Una columna «aprobado por» añadida a `postventa.validaciones` se
    borraría en el siguiente `POST /api/parte`. **[MEDIDO]** — es el argumento
    que decide §3.

11. **El DDL admite `ALTER TABLE … ADD COLUMN`**, pero no hace falta:
    `infrastructure/persistencia/ddl.py::_validar_forma` reconoce cinco formas
    y `ficheros_ddl()` aplica los `NN_nombre.sql` en orden lexicográfico, así
    que una tabla nueva entra sola con un fichero `10_`. **[MEDIDO]**

---

## 1 · Qué es aprobar: un acto explícito, y no un efecto lateral

> El responsable dijo «cuando se modifiquen los campos o se revise». Eso admite
> dos lecturas y son cosas distintas. La recomendación razonada y la alternativa
> están en **P1**; esta sección especifica la recomendada.

**R1.** El sistema debe ofrecer un **acto explícito y propio** de aprobación de
un parte, distinto de corregir un campo y distinto de revalidar.

**R2.** CUANDO una persona aprueba un parte, el sistema debe registrar la
aprobación con **quién** la hizo —su identificador opaco— y **cuándo**, y debe
guardarla fuera del navegador.

**R3.** El sistema **no debe** dar por aprobado un parte por el solo hecho de
que se haya corregido uno de sus campos o de que se haya revalidado.

**R4.** SI llega una petición de aprobación **sin** el identificador de quien
aprueba, ENTONCES el sistema **no debe** registrar nada y debe decir que sin
saber quién decide no se puede registrar la decisión.

**R5.** El sistema **no debe** aceptar que el veredicto llegue hecho en la
petición de aprobación: el veredicto sobre el que se aprueba se **recalcula**
con las reglas de F-004 al recibirla (misma regla que R8 de F-019).

---

## 2 · Qué se puede aprobar, y qué no

> Los dos destinos no aptos llegan ahí por motivos distintos, y F-004 lo dice
> con todas las letras: `cola_validacion_humana` es «hay algo que **decidir**»,
> `revision_manual` es «hay algo que **arreglar**»
> (`domain/models/validacion.py`, cabecera). La línea que separa lo aprobable de
> lo no aprobable no es el destino: es **el motivo**.

**R6.** El sistema debe considerar **aprobables** exactamente estos dos motivos
de F-004: `observaciones_manuscritas` y `firma_no_humana`.

**R7.** El sistema **no debe** considerar aprobables los motivos
`codigo_obra_no_legible` ni `numero_incidencia_no_legible`.

> No es una política, es una imposibilidad: sin nº de incidencia no hay
> reclamación que cerrar ni fichero que nombrar (`ARCHITECTURE.md`, semántica 5
> y 8), y sin código de obra no hay carpeta. Ahí no hay nada que decidir: hay
> algo que teclear, y teclearlo **ya funciona** (§0.6).

**R8.** CUANDO **todos** los motivos de un parte están en la lista de
aprobables, el sistema debe permitir aprobarlo, **venga del destino que venga**
—de la cola ámbar o de la revisión manual—.

**R9.** SI alguno de los motivos de un parte **no** está en la lista de
aprobables, ENTONCES el sistema **no debe** permitir aprobarlo, y debe decir
cuál lo impide y que se arregla corrigiendo ese campo.

**R10.** El sistema **no debe** ofrecer aprobar un parte que ya es apto con
destino `archivo_y_cierre`: no hay nada que aprobar.

**R11.** El sistema **no debe** cambiar ninguna regla de F-004: el veredicto, el
destino y los motivos de un parte aprobado siguen siendo **los que emitió la
validación**, y la aprobación se registra **al lado**, nunca encima.

---

## 3 · Dónde se guarda, y con qué forma

**R12.** La aprobación debe guardarse en una **tabla propia** del esquema
propio del proyecto, con `hash_parte` como clave primaria y clave ajena contra
`postventa.partes`.

> Tabla propia y no una columna en `postventa.validaciones` por §0.10: ese
> `upsert` reescribe todas sus columnas en cada guardado, así que la decisión de
> una persona se perdería en el siguiente reproceso. Es además el patrón que ya
> siguen `archivos` (F-006), `cierres` (F-009) y `graficos` (F-012): **una tabla
> por hecho con ciclo de vida propio**.

> **Enmienda del 2026-09-16 · F-028 (R56).** La decisión humana deja de vivir
> en una fila que se sustituye y pasa a vivir en el **histórico append-only**
> `postventa.historico_estado`, donde manda la **última fila humana**.
>
> **R12 decía**, literal: *«La aprobación debe guardarse en una tabla propia
> del esquema propio del proyecto, con `hash_parte` como clave primaria y clave
> ajena contra `postventa.partes`.»*
>
> **Qué la invalidó**: `hash_parte` como **clave primaria** obliga a una fila
> por parte, y con ella al `ON CONFLICT DO UPDATE` que borra la decisión
> anterior (**§0.4** de `specs/F-028-estado-del-parte/requirements.md`). Con
> eso, el criterio de aceptación de F-028 —«el histórico conserva las
> decisiones en orden», y un ciclo aprobar → rechazar → aprobar deja **tres**
> filas— es imposible de cumplir, no difícil.
>
> **Lo que no cambia**: sigue siendo una **tabla propia** del esquema propio,
> con su clave ajena contra `postventa.partes`, y la decisión se sigue
> registrando **al lado del veredicto, nunca encima** (R11). Lo que cambia es
> la forma de la tabla, no de quién es el dato.
>
> **`postventa.aprobaciones` no se borra**: guarda decisiones que tomaron
> personas de verdad, y el DDL del histórico la **siembra** para que sigan
> contando. Se congela: ni se lee ni se escribe más.
>
> **Quién y cuándo**: el **responsable del proyecto**, el **2026-09-15**, al
> replantear la feature después de ver F-026 funcionando.

**R13.** De quien aprueba, el sistema debe guardar **el identificador opaco de
Entra ID y nada más**: nunca su correo, nunca su nombre, nunca su login de
Sigrid.

**R14.** La aprobación debe guardar, además de quién y cuándo: **de qué destino
se rescató el parte**, **qué motivos se aprobaron** (sus códigos) y **sobre qué
veredicto exacto se decidió**.

**R15.** El sistema **no debe** copiar en la tabla de aprobaciones la
transcripción de las observaciones del cliente, ni ningún otro campo manuscrito.

> Misma regla que la cabecera de `sql/04_validaciones.sql` (R21 y R39 de F-005):
> las observaciones ya están en `postventa.partes`, y una segunda copia de texto
> manuscrito de un cliente dobla la exposición y diverge. «Sobre qué veredicto se
> decidió» se guarda como **huella**, no como texto (ver §6).

**R16.** El DDL de la tabla debe ser **idempotente** y vivir **solo** en el
esquema propio, siguiendo la convención `NN_nombre.sql`. El sistema **no debe**
ejecutar ninguna sentencia fuera de ese esquema ni de ámbito de servidor.

**R17.** El sistema debe dejar **una sola fila por parte**: volver a aprobar el
mismo parte sustituye su aprobación, nunca acumula una segunda.

> **Enmienda del 2026-09-16 · F-028 (R56).** Ya no hay una sola fila por
> parte: hay **una fila por decisión**, y manda la **última fila humana**.
>
> **R17 decía**, literal: *«El sistema debe dejar una sola fila por parte:
> volver a aprobar el mismo parte sustituye su aprobación, nunca acumula una
> segunda.»*
>
> **Qué la invalidó**: sustituir **borra el rechazo anterior**. Con el
> `ON CONFLICT DO UPDATE` que impone una fila por parte (**§0.4** de
> `specs/F-028-estado-del-parte/requirements.md`), un ciclo aprobar → rechazar
> → aprobar no deja ni rastro del rechazo, y quien audite el parte no verá que
> alguien lo miró y dijo que no. El histórico de F-028 es **append-only** y
> deja las tres filas, en orden.
>
> **Lo que no cambia**: sigue habiendo **una sola respuesta** a «¿en qué estado
> está este parte?» (R2 y R17 de F-028). Lo que se acumula son los hechos, no
> los criterios: el estado se **deriva**, y el histórico es constancia y nunca
> criterio (R26 de F-028). Si mañana faltara una fila, el estado seguiría
> siendo el correcto.
>
> **Quién y cuándo**: el **responsable del proyecto**, el **2026-09-15**.

---

## 4 · El borde HTTP

**R18.** El sistema debe exponer un endpoint **propio** para aprobar un parte, y
**no debe** hacer de la aprobación un efecto lateral de ningún endpoint
existente.

> Un endpoint por escritura con consecuencias es el patrón del servicio
> (`/api/archivar`, `/api/adjuntar`, `/api/cerrar`). Y sobre todo: una petición
> = una decisión de una persona, que es justo la unidad que hay que poder
> auditar. La alternativa —extender `POST /api/parte`— convertiría aprobar en un
> efecto de guardar, y guardar ocurre en cada revalidación. Ver `design.md` §5.

**R19.** El cuerpo de esa petición **no debe** llevar ni el DNI, ni el veredicto
ya hecho, ni ningún byte del PDF.

**R20.** El endpoint debe responder **400** si el cuerpo está mal formado,
**409** si el parte no consta guardado o si su veredicto no es aprobable (R9), y
**503** si aquí y ahora no hay base de datos. En los tres casos **sin haber
escrito nada**.

**R21.** El endpoint **no debe** depender de `ARCHIVO_HABILITADO` ni de
`CIERRE_HABILITADO`: aprobar escribe en el esquema propio, no en un sistema
ajeno, y atarlo dejaría sin poder registrar el trabajo de revisión justo cuando
las ventanas de escritura están cerradas, que es como se despliega el entorno
(misma razón que R34 de F-019).

**R22.** CUANDO el sistema devuelve el resultado de guardar un parte, debe decir
**si ese parte consta aprobado** y si su aprobación **sigue vigente**, para que
la pantalla lo sepa sin una petición más por parte.

> **Enmienda del 2026-09-16 · F-028 (R56).** Lo que se devuelve al guardar un
> parte ya no es «consta aprobado» más «sigue vigente»: es **el estado del
> parte**, uno de cuatro —`pendiente`, `aprobado`, `rechazado`, `cerrado`—, y
> quién lo sostiene.
>
> **R22 decía**, literal: *«CUANDO el sistema devuelve el resultado de guardar
> un parte, debe decir si ese parte consta aprobado y si su aprobación sigue
> vigente, para que la pantalla lo sepa sin una petición más por parte.»*
>
> **Qué la invalidó**: las dos banderas solo saben decir sí o no, y eso se
> quedó corto en cuanto una persona pudo **rechazar** un parte que la máquina
> había dado por bueno: «no aprobado» y «rechazado» no son lo mismo —del
> segundo no se sale reprocesando—, y un parte `cerrado` no admite ningún
> cambio. Con dos banderas, la pantalla tendría que reconstruir el estado por
> su cuenta, que es la segunda copia del criterio que R17 de F-028 prohíbe. Y
> la decisión ya no vive donde vivía: está en el **histórico append-only**
> `postventa.historico_estado`, donde manda la **última fila humana**
> (**§0.4** de `specs/F-028-estado-del-parte/requirements.md`, el
> `ON CONFLICT DO UPDATE` que borraba el rechazo anterior).
>
> **Lo que no cambia**: el motivo por el que esto existe. Sigue viajando **en
> la respuesta de guardar**, sin una petición más por parte, y la vigencia de
> una decisión humana se sigue resolviendo por **huella del veredicto** (R30,
> precisada más abajo).
>
> **Quién y cuándo**: el **responsable del proyecto**, el **2026-09-15**.

---

## 5 · Qué abre la aprobación, y qué no

**R23.** CUANDO un parte consta aprobado y vigente, el sistema debe **admitirlo
en el circuito de F-025** —archivar, adjuntar y cerrar— igual que a un parte
apto.

**R24.** El sistema debe leer la aprobación **del almacén** y **nunca** del
cuerpo de la petición.

> Misma razón que `ContextoParte.traza_grafico` (F-012, R49): si viniera del
> cuerpo, quien llama podría afirmar que alguien aprobó lo que nadie aprobó, y
> con eso se cierra una reclamación que la validación había rechazado.

**R25.** El sistema **no debe** archivar, adjuntar ni cerrar un parte no apto
que **no** conste aprobado, ni siquiera dentro de una tanda y ni siquiera si el
usuario pulsa dos veces.

**R26.** La aprobación **no debe** relajar ninguna otra puerta: el parte
aprobado sigue teniendo que **constar guardado** (F-019), **constar archivado**
antes del gráfico y del cierre (F-006, F-012), **constar adjuntado** antes del
cierre (F-012 R2), y el cierre sigue exigiendo su dry-run dentro de la misma
llamada, el login verificado contra el ERP y el estado de origen en el `WHERE`
(F-009, F-025 §6).

**R27.** La aprobación **no debe** saltarse la **confirmación única** de F-025:
un parte aprobado entra en la tanda y se escribe cuando alguien confirma la
tanda, no antes.

**R28.** El sistema **no debe** aprobar un parte por lotes ni «aprobar toda la
cola»: la aprobación es de **un** parte, con ese parte delante.

**R29.** El sistema **no debe** pedir una segunda confirmación para aprobar.

> Y esto no es un descuido: aprobar **no escribe en ningún sistema ajeno** —ni
> SharePoint, ni el ERP—, escribe en el esquema propio y se deshace revalidando.
> La confirmación única de F-025 sigue siendo la única que precede a una
> escritura externa, y **R2 de F-025 sigue intacto** (lo vigila
> `test_f025_r2_solo_se_arma_una_confirmacion_en_todo_el_front`). Ver **P7**.

---

## 6 · Cuándo deja de valer una aprobación

> La pregunta del encargo: ¿caduca si el parte se vuelve a procesar, o si se
> corrige un campo después de aprobar? La respuesta de esta spec es que **la
> aprobación vale para el veredicto que se aprobó, no para el parte en
> abstracto**. Una persona que mira una firma dudosa y dice «vale» está diciendo
> «vale **esta** firma»; si el sistema vuelve a leer el papel y sale otra cosa,
> esa persona no ha opinado sobre lo nuevo.

> **ENMIENDA DEL 2026-09-12 · hallazgo H-1 de `progress/review_F-026.md`.**
> La huella pasa a incluir también el **código de obra** y el **número de
> incidencia**, los dos normalizados.
>
> **La premisa original decía**, literal: *«Por qué no entran los valores de
> los campos: el nombrado cambia si cambia el código de obra, pero eso no es
> lo que se aprobó; y los campos decisivos ilegibles no son aprobables, así
> que su cambio ya sale reflejado en los motivos.»*
>
> **Qué la invalidó**: ese razonamiento examinaba el código de obra y **no
> llegó a examinar el número de incidencia**, que decide **sobre qué
> reclamación del ERP de producción se escribe el cierre**. El camino que
> dejaba abierto: un parte va a la cola por observaciones, alguien lo aprueba
> mirando el papel, otra persona corrige el número a uno distinto —también
> legible, así que ningún motivo cambia—, revalida, y la aprobación sobrevive
> y acaba cerrando **otra** reclamación. El código de obra entra por su propio
> motivo: decide en qué carpeta acaba un PDF con el DNI manuscrito de un
> cliente.
>
> **Quién y cuándo**: lo decidió el responsable del proyecto el **2026-09-12**,
> tras leer el hallazgo. Se hizo entonces porque tocar la huella invalida las
> aprobaciones existentes, y no había ninguna: la feature no se había
> desplegado.
>
> **Lo que no cambia**: que un campo decisivo ilegible sigue sin ser
> aprobable. Lo que estos dos añaden no es la legibilidad, que ya sale en los
> motivos, sino **la identidad de lo que se aprobó**.

**R30.** CUANDO se guarda una validación cuyo veredicto **difiere** del que se
aprobó, el sistema debe **revocar** la aprobación de ese parte, en la misma
operación y sin que nadie tenga que acordarse de pedirlo.

> **Precisión del 2026-09-16 · F-028 (R57). No se deroga: se precisa.** La
> aprobación **sigue dejando de valer** cuando cambia el veredicto sobre el que
> se decidió. Lo que cambia es **cuándo y cómo se resuelve**.
>
> **R30 decía**, literal: *«CUANDO se guarda una validación cuyo veredicto
> difiere del que se aprobó, el sistema debe revocar la aprobación de ese
> parte, en la misma operación y sin que nadie tenga que acordarse de
> pedirlo.»*
>
> **Qué se precisa**: ya no hay ninguna escritura que revoque. Se resuelve al
> **derivar** el estado, comparando la **huella** apuntada en el histórico con
> la del veredicto guardado ahora (`domain/models/estado.py`,
> `_aprueba_lo_que_hay`). Con el estado derivado no hay dato guardado que pueda
> quedarse viejo, así que no hay nada que revocar.
>
> **Y cierra un hueco, no solo mueve el sitio**: revocar era una **segunda**
> escritura detrás de la del veredicto, y entre las dos había una **ventana**.
> Si la segunda fallaba —la base tose, el proceso se cae—, el parte se quedaba
> aprobado sobre un veredicto que ya no existía, y nadie se enteraba.
> Resolviéndolo al leer, esa ventana no existe.
>
> **Lo que no cambia**: el criterio, que es el de siempre —se aprobó *ese*
> veredicto—, ni R32: volver a guardar el mismo veredicto **no** caduca nada, y
> eso sigue siendo lo que hace que recargar la pantalla no tire por la ventana
> el trabajo de revisión.
>
> **Quién y cuándo**: el **responsable del proyecto**, el **2026-09-15**.

**R31.** MIENTRAS una aprobación esté revocada, el sistema **no debe** admitir
ese parte en el circuito: vuelve a hacer falta que una persona lo apruebe.

> Esto cierra, de paso, la mitad del agujero de §0.7: vaciar la observación y
> revalidar cambia el veredicto, así que **revoca** cualquier aprobación previa.
> La otra mitad —que ese vaciado siga convirtiendo un ámbar en verde sin traza—
> está fuera del alcance de F-026 y va como **P3**.

> **Precisión del 2026-09-16 · F-028 (R57). No se deroga: se precisa.**
>
> **R31 decía**, literal: *«MIENTRAS una aprobación esté revocada, el sistema
> no debe admitir ese parte en el circuito: vuelve a hacer falta que una
> persona lo apruebe.»*
>
> **Qué se precisa**: ya no existe «revocada» como dato guardado. Una
> aprobación tomada sobre otro veredicto simplemente **no cuenta** al
> **derivar** el estado —su **huella** no es la del veredicto de ahora—, y el
> parte se queda donde lo deje la máquina, que en la práctica es `pendiente`.
> La consecuencia es **exactamente la misma** que enunciaba R31: no entra en el
> circuito, y vuelve a hacer falta que una persona lo apruebe.
>
> **Y una diferencia que sí importa, declarada**: como no hay marca que borrar,
> si el veredicto vuelve a ser el que se aprobó —alguien corrige un campo y
> deshace la corrección—, la aprobación **vuelve a contar**. Es lo que ya decía
> R32 y lo que hace que recargar la pantalla no invalide el trabajo hecho, pero
> visto desde aquí parece otra cosa: encontrárselo en producción sin haberlo
> leído antes es como se abren los partes de incidencia.
>
> **Lo que no cambia**: que lo automático puede **retirar** un permiso y nunca
> concederlo. Por eso el `rechazado` de una persona **no caduca jamás**, ni
> aunque el veredicto pase a apto (R5 de F-028): si caducara, bastaría con
> reprocesar la remesa para que un parte que alguien miró y rechazó volviera a
> entrar en la tanda.
>
> **Quién y cuándo**: el **responsable del proyecto**, el **2026-09-15**.

**R32.** CUANDO se vuelve a guardar una validación cuyo veredicto es **el
mismo** que se aprobó, el sistema **no debe** revocar la aprobación.

> Es lo que hace verdad el criterio de aceptación «sobrevive a recargar la
> página»: al recargar hay que volver a subir la remesa (así está declarado en
> el pie de `index.html`, F-019), y eso reprocesa cada parte y vuelve a guardar
> su validación. Si cualquier reproceso revocara, la aprobación no sobreviviría
> a nada.

**R33.** El sistema **no debe** borrar la fila de una aprobación revocada: la
decisión se tomó, y quién la tomó y cuándo sigue siendo información. Se marca
revocada, con su instante y su motivo.

**R34.** El sistema debe registrar la revocación **sin** guardar el texto que la
provocó: el motivo es una etiqueta corta, nunca la observación del cliente.

---

## 7 · Qué ve quien revisa

**R35.** MIENTRAS un parte sea aprobable (R8), el sistema debe ofrecer su
aprobación **en el detalle del parte**, con el PDF delante, y no en una lista.

**R36.** CUANDO un parte queda aprobado, el sistema debe distinguirlo en
pantalla **de un parte que siempre fue verde**, con una marca propia y un texto
que diga que lo aprobó una persona.

> No es cosmética: uno lo dio por bueno la máquina y el otro lo dio por bueno
> una persona **a pesar** de la máquina. Pintarlos igual borra exactamente el
> dato que esta feature existe para registrar.

**R37.** El sistema debe enseñar, junto a esa marca, **de qué destino se
rescató** el parte y **cuándo** se aprobó.

**R38.** El sistema **no debe** pintar en pantalla el identificador de quien
aprobó, ni su correo, ni su nombre.

> Que la decisión quede registrada no exige publicarla en la pantalla de todo
> el que mire la remesa. Quien necesite auditarla la lee en la base.

**R39.** SI un parte no es aprobable por R9, ENTONCES el sistema **no debe**
ofrecer el gesto de aprobar, y debe decir qué hay que corregir.

**R40.** CUANDO un parte aprobado entra en la tanda, el resumen del final debe
seguir diciendo, por parte, hasta dónde llegó y sobre qué número de incidencia
se escribió (R16 y R37 de F-025, sin cambios).

---

## 8 · La traza hasta el ERP

> Antes de proponer nada se miró qué se guarda hoy (§0.8 y §0.9).

**R41.** El sistema debe permitir responder, **con lo que guarda en su propio
esquema**, a la pregunta «¿esta reclamación se cerró a partir de un parte que
aprobó una persona, y quién?»: la aprobación se cruza por `hash_parte` con
`postventa.cierres` y `postventa.graficos`, que ya llevan el número de
incidencia, el `ide` de la reclamación y el `oid` de quien confirmó.

**R42.** F-026 **no debe** cambiar lo que se escribe dentro de Sigrid: ni el
estado, ni el `tex` de `dbo.log`, ni ninguna columna más.

> El `tex` es constante y homogéneo a propósito (§0.9): es lo que identifica
> nuestros cierres con un solo `LIKE` y lo que hace el conjunto reversible.
> Meterle un sufijo por parte lo convertiría en un texto variable y es una
> escritura distinta en el ERP de producción, que decide el dueño del proceso,
> no esta spec. Ver **P6**.

---

## 9 · Datos personales, logs y secretos

**R43.** Los textos de pantalla y de log que añada F-026 **no deben** contener
el DNI, las observaciones manuscritas, la descripción, el correo, el nombre ni
el `oid` de quien aprueba.

**R44.** El log del endpoint de aprobación debe llevar el `hash_parte`, el
destino del que se rescató y el resultado, y **nada más**.

**R45.** F-026 **no debe** añadir ninguna variable de entorno, ningún secreto y
ninguna dependencia nueva.

---

## 10 · Las enmiendas

> **No se borra ningún requisito.** Se enmienda con un recuadro fechado que cita
> la premisa original **literal**, dice qué la invalidó y quién lo decidió. Es
> el patrón de R28 de F-010 y de §7 de F-025.

**R46.** El requisito **R36 de F-025** queda **enmendado** y debe recibir su
recuadro fechado, sin que se borre su texto.

> R36 dice hoy, literal: *«El sistema **no debe** archivar, adjuntar ni cerrar
> un parte que no sea `apto` con destino `archivo_y_cierre`, ni siquiera dentro
> de la tanda y ni siquiera si el usuario pulsa dos veces. Los partes en
> revisión y los de la cola humana **siguen fuera** (aprobarlos es **F-026**).»*
>
> Lo que cambia es **solo** su última frase, y la propia frase lo anunciaba:
> desde F-026, un parte no apto entra en la tanda **si y solo si consta aprobado
> y vigente**. La prohibición **sigue entera** para todo lo demás, y su
> comprobación sigue estando en los tres pasos del backend.

**R47.** `docs/ARCHITECTURE.md` debe quedar al día en los **tres** puntos que
hoy afirman lo contrario, y con la precisión —no con un borrado—:

> - paso 6 del pipeline: *«**Solo se archiva lo que el paso 4 declaró apto**»*;
> - semántica 3: *«Un parte sin firma válida no se archiva ni se cierra: va a
>   revisión manual»*;
> - semántica 7: *«**Nada se archiva ni se cierra si no ha pasado todas las
>   validaciones.**»*
>
> Los tres siguen siendo ciertos **salvo aprobación humana registrada**, que es
> una puerta más estrecha que la que abrían: exige una persona, un parte
> concreto, un motivo aprobable y un registro.

**R48.** Los requisitos de F-004 quedan **vigentes sin ningún cambio**, y la
spec debe decirlo: F-026 no toca ni una regla de reparto. Lo mismo para R14–R17
de F-012 y R16–R17 de F-009, cuyo enunciado —«solo se adjunta/cierra lo apto»—
pasa a leerse «lo apto **o lo aprobado**», sin que se afloje ninguna de sus
otras comprobaciones.

**R49.** El documento del proyecto en `azure-apps/` **debe** actualizarse en
esta misma feature: F-026 añade un endpoint y una tabla, que es exactamente lo
que ese documento describe. La regla de `CLAUDE.md` no admite hacerlo después.

> Hecho el **2026-09-12**, en T19 y en dos commits, porque son dos
> repositorios: `docs/INTEGRACION.md` —que es la **fuente de verdad**, y sin
> tocarla la copia habría quedado diciendo algo que aquí no está escrito— y
> `azure-apps/postventa_incidencias.md`, refrescado desde ella. **Sin `push`**
> en ninguno de los dos, y `git -C ../azure-apps status` limpio al terminar.
>
> Lo que se escribió allí: la tabla `postventa.aprobaciones` en el árbol del
> esquema propio, la fila de `POST /api/aprobar` en la tabla de endpoints —los
> once pasan a doce—, que aprobar **no mira ninguna de las dos ventanas de
> escritura**, y el `oid` de quien aprueba en el apartado de datos personales,
> con el motivo por el que se guarda. En la cabecera de la copia consta lo
> único que el ecosistema necesita saber: que **no empezamos a consumir nada
> nuevo**, y que desde F-026 una reclamación puede acabar cerrada aunque su
> parte no fuera apto —si una persona lo aprobó—, **sin que en el ERP quede
> constancia de la aprobación** (P6, decisión del responsable).
>
> De paso se corrigió **deuda ajena** en ese mismo árbol: faltaban
> `usuarios_sigrid` (F-009) y `graficos` (F-012), que existen desde sus
> features. Se añaden porque el bloque que había que tocar era ese, y un
> inventario de tablas al que le faltan dos es peor que no tenerlo.

---

## Preguntas abiertas · RESUELTAS el 2026-09-11

> **Las siete quedan cerradas.** El responsable respondió con estas palabras:
> *«EN F26. ESCRIBIR EN UN CAMPO, DEBE GUARDAR LO QUE ESCRIBES (SEGÚN ESCRIBE
> GUARDA, SIN BOTÓN). OK A 2.3, NO HACE FALTA QUE CONSTE EN SIGRID SI EN
> NUESTRA BBDD.»*
>
> | # | Cómo queda | Quién lo decidió |
> |---|---|---|
> | **P1** | **Acto explícito**, con su botón y su registro. **Y ADEMÁS** entra el autoguardado como requisito nuevo (§11) | **Interpretación del líder, no pronunciamiento del responsable.** Ver abajo |
> | **P2** | Por **motivo**, no por destino | Responsable |
> | **P3** | **Fuera de alcance**, declarado como riesgo con su fecha | Responsable |
> | **P4** | Con el texto de las observaciones en la huella | Recomendación, **por omisión** |
> | **P5** | Por huella del veredicto | Recomendación, **por omisión** |
> | **P6** | **No consta en Sigrid.** Sí en el esquema propio | Responsable, explícito |
> | **P7** | Aprobar **no** pide confirmación aparte | Recomendación, **por omisión** |
>
> **Por qué P1 es una interpretación y no una respuesta.** Lo que el
> responsable describe —«escribir en un campo debe guardar lo que escribes»—
> **no responde a lo que P1 preguntaba**, que era si corregir un campo
> *aprueba* por sí solo. Pide **autoguardado**, que es otra cosa. El líder
> decidió mantener el acto explícito y añadir el autoguardado, con este
> argumento: guardar lo que alguien escribe y declarar que una firma dudosa
> vale son juicios distintos, y **solo el segundo necesita saber quién lo
> hizo**. Se le dijo al responsable que si quería decir que tampoco hubiera
> botón de aprobar, lo dijera; mientras no lo diga, manda esta interpretación.
>
> **Lo que sigue vivo de P6**: preguntar a Posventa si quieren **distinguir en
> sus informes** los cierres que vinieron de una aprobación humana. No es una
> decisión técnica y no la toma este proyecto.

---

## 11 · El autoguardado de las correcciones · requisito nuevo del 2026-09-11

### 11.0 · Lo que hay hoy [MEDIDO]

- `js/app.js::editarCampo(nombre, valor)` guarda la corrección **solo en
  memoria** (`this.parteAbierto.ediciones[nombre] = valor`) y pone el mensaje
  «Hay correcciones sin revalidar». **Si la persona escribe y se va, se
  pierde.**
- Persistir existe, pero **solo por acción explícita**:
  `js/pipeline.js::revalidarYGuardar(parte, api, remesaId)`.
- **Y las dos van juntas a propósito.** El comentario de esa función lo
  explica: si se revalidara sin guardar, en la base quedaría el veredicto que
  la IA emitió **sobre el dato sin corregir**.
- `revalidar` por separado **no guarda**, y **no gasta IA**: es el contrato de
  F-007 R17, una sola petición.

### 11.1 · El choque, y cómo se resuelve

Guardar «según se escribe» rompe ese acoplamiento: la base quedaría con el
dato nuevo y el veredicto viejo, que es justo lo que `revalidarYGuardar`
evita.

**R50.** CUANDO una persona corrige un campo y deja de escribir, el sistema
debe **revalidar y guardar juntos**, reutilizando `revalidarYGuardar`, de modo
que el veredicto guardado corresponda **siempre** al dato guardado.

> **Por qué juntos y no solo el campo.** Revalidar **no gasta IA** y es una
> sola petición, así que el coste de mantener el acoplamiento es bajo. La
> alternativa —guardar solo el campo y marcar el veredicto como obsoleto—
> obliga a inventar un estado nuevo que todas las puertas tendrían que mirar,
> y a que alguien recuerde revalidar después. **Mantener invariante «el
> veredicto corresponde al dato» sale más barato que gestionarla rota.**
>
> **Efecto secundario que se acepta y se declara**: el color del parte puede
> cambiar mientras se escribe, porque cada revalidación lo recalcula. Se
> considera **deseable**: quien corrige ve al momento el efecto de su
> corrección.

**R51.** El guardado debe dispararse **tras una pausa al escribir**, no en
cada pulsación, y **solo si el valor cambió** respecto a lo último guardado.
El retardo se fija en el diseño; la razón del retardo es que el PostgreSQL es
**compartido con otros dos proyectos en producción**.

**R52.** CUANDO el guardado automático falle, el sistema debe **decírselo a la
persona** y conservar lo escrito en pantalla. Quien escribe y no ve nada
supone que se guardó, y esa suposición no puede quedar sin desmentir.

**R53.** Las correcciones **no pisan** el valor ni la confianza que extrajo la
IA: esos dos son la evidencia de cómo se comportó el modelo y **F-015 los va a
necesitar** para evaluar el prompt. Dónde vive cada uno lo fija el diseño.

**R54.** El autoguardado **no debe revocar una aprobación a mitad de una
palabra**: la revocación se evalúa sobre lo guardado, con la huella de R15, y
por tanto ocurre como mucho una vez por pausa.

**R55.** El autoguardado aplica a **todos** los partes, no solo a los que van
a revisión. Perder lo escrito es igual de malo en un parte verde, y la
revalidación mantiene su veredicto al día en los dos casos.

---

## Trazabilidad de los requisitos que no llevan test unitario

| Requisito | Por qué no hay test unitario | Cómo se verifica |
|---|---|---|
| R12, R16, R17 en su ejecución real sobre PostgreSQL | Crear la tabla exige la base compartida | `MANUAL (humano)`, bloque 5 de `tasks.md`. El **texto** del DDL sí tiene test sin BBDD, con el patrón de `tests/test_f005_ddl_idempotente_texto.py`: idempotencia, esquema propio, y los `CHECK` comparados contra los `Enum` del dominio |
| R23, R26 extremo a extremo | Exigen SharePoint y el ERP con sus ventanas abiertas | `MANUAL (humano)`; el **camino** tiene test unitario entero con dobles en memoria, que es como lo prueban hoy F-006, F-012 y F-025 |
| R41 | Es una consulta de auditoría sobre datos reales | `MANUAL (humano)`: la consulta exacta va escrita en `tasks.md`, contra el esquema propio y **solo lectura** |
| R42 | Es una **prohibición de cambio** sobre otro sistema | Control negativo: `TEXTO_LOG_CIERRE` y `batch_de_cierre` intactos en el diff, con sus tests de F-009 en verde |
| R47, R49 | Son documentos, y uno está en **otro repositorio** | Repaso declarado en `tasks.md`; para `ARCHITECTURE.md`, un test de documentación con el patrón de `tests/test_f025_documentacion.py` |

Todo lo demás tiene test unitario **sin red, sin BBDD y sin IA**.
