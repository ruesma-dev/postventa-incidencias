<!-- specs/F-009-cierre-sigrid/requirements.md -->
# F-009 · Cierre de la incidencia en Sigrid (solo estado) — Requisitos

> Notación EARS (`specs/SPECS.md`). Cada requisito se traduce a **al menos un
> test trazable** `test_f009_rN_*`. Rigor `critico`.
>
> Lo que esta feature escribe va al **ERP de producción**. Los requisitos que
> parecen paranoicos —dry-run obligatorio, doble puerta, verificación del
> login contra el ERP, tope de filas afectadas— no lo son: son la diferencia
> entre cerrar una incidencia y dar por resuelta una reparación que sigue
> viva.

## Alcance

F-009 mueve `con.est` de la reclamación al estado de cierre y **escribe la fila
de auditoría en `dbo.log` que el ERP escribiría**. Nada más.

**Fuera de alcance, y por decisión del humano del 2026-08-26**: subir el parte a
Sigrid como gráfico (es **F-012**) y confirmar el gráfico-URL (es **F-013**;
F-008 demostró que no hay ni un precedente en 282.599 filas).

## Vocabulario

| Término | Qué es |
|---|---|
| **Reclamación** | El concepto `dbo.con` con `tip = 708`, extensión 1:1 en `rcp`. Es «la incidencia». |
| **Código de incidencia** | `con.cod`, formato `RS{AA}.{MM}/{NNNN}`. Único dentro del tipo 708. En el nombre del fichero va con guion; en Sigrid, con barra. |
| **Estado de cierre** | El `conest.est` cuyo `conest.cod` es `CER`, resuelto en ejecución. **Nunca el número.** |
| **Dry-run** | Consulta de solo lectura que devuelve qué se escribiría, sin escribir. |
| **Login de Sigrid** | `dbo.usu.cod`. Lo que va en `dbo.log.usu`. |

---

## 1 · Resolución del estado, nunca cableado

**R1.** El sistema debe resolver el estado de cierre consultando `dbo.conest`
por `tip` de la reclamación y `cod = 'CER'`, y usar el `est` que devuelva.

**R2.** SI la consulta de `dbo.conest` no devuelve **exactamente una** fila para
ese `tip` y `cod`, ENTONCES el sistema debe abortar el cierre sin escribir nada
y registrar el motivo.

**R3.** El sistema **no debe** contener ningún número de estado de Sigrid
literal en el código de producción, ni como valor por defecto, ni como
configuración, ni como constante.

> R3 se verifica con un **control negativo** sobre el árbol de producción, al
> modo de `test_f005_logs_sin_datos_personales.py`: es la traducción directa
> del checkpoint C3 «nada contra Sigrid hardcodea un número de estado».

**R4.** El sistema debe tomar el `tip` de la reclamación **de la propia
reclamación leída**, y no de una constante.

## 2 · Localización de la reclamación

**R5.** CUANDO se pide cerrar una incidencia, el sistema debe localizar la
reclamación por `con.cod` acotando **siempre** con el `tip` de reclamación de
posventa.

**R6.** El sistema debe convertir el código que trae el parte al formato de
Sigrid **con barra** antes de consultar, y esa conversión debe ser la inversa
exacta de la que aplica el nombrado de F-006.

**R7.** SI la búsqueda no devuelve exactamente una reclamación, ENTONCES el
sistema debe abortar sin escribir nada y decir cuántas encontró.

## 3 · El dry-run es obligatorio y va primero

**R8.** CUANDO se solicita un cierre, el sistema debe ejecutar **primero** un
dry-run que consulte el estado actual de la reclamación **sin escribir nada**.

**R9.** El dry-run debe devolver: el código de la incidencia, la descripción de
la reclamación, el **código y la descripción legibles** del estado de origen, los
del estado de destino, el login de Sigrid con el que se firmaría el cierre, y el
**aviso de que la reclamación quedará cerrada sin el parte dentro de Sigrid**.

**R10.** MIENTRAS no exista un dry-run correcto y reciente para esa incidencia,
el sistema **no debe** ejecutar ninguna escritura contra Sigrid.

**R11.** SI el estado de origen leído en el dry-run difiere del estado que la
reclamación tiene en el momento de escribir, ENTONCES el sistema debe abortar la
escritura sin aplicarla.

> R11 es la respuesta al hallazgo de F-008 §2.4: **los cierres se deshacen**
> (81 filas `DESHACER proceso`). No se puede asumir que lo leído siga ahí.

## 4 · La confirmación, y la única forma de saltársela

**R12.** El sistema **no debe** ejecutar el cierre con `commit` sin una de estas
dos cosas: la confirmación explícita del usuario en el front, o su preferencia
de auto-cierre guardada y activa.

**R13.** DONDE el usuario tenga `auto_cierre` activo en
`postventa.preferencias_usuario`, el sistema debe poder encadenar el dry-run y
el commit sin pedir confirmación, **sin saltarse el dry-run** (R8) ni ninguna
de las validaciones.

**R14.** El valor por omisión de `auto_cierre` debe ser **falso**: quien no ha
decidido nada no tiene auto-cierre.

**R15.** CUANDO el usuario confirma en el front, la confirmación debe caducar y
un segundo clic fuera de la ventana **no debe** disparar el cierre.

## 5 · Nada se cierra si no ha pasado todas las validaciones

**R16.** El sistema **no debe** cerrar una incidencia cuyo parte no haya sido
declarado apto por la validación de F-004.

**R17.** El sistema **no debe** cerrar una incidencia cuyo parte no conste
**archivado** en `postventa.archivos`.

> R17 es el orden del procedimiento de Posventa, datado en F-008 §4.2: primero
> el documento, después el cierre. Si el PDF no está guardado en ninguna parte,
> cerrar la incidencia la da por resuelta sin dejar la prueba en ningún sitio.

**R18.** SI la reclamación ya está en el estado de cierre, ENTONCES el sistema
debe registrar el resultado como `ya_cerrada` **sin escribir nada en Sigrid**, y
eso **no** debe tratarse como un error.

**R19.** SI la reclamación está en un estado que no admite cierre automático,
ENTONCES el sistema debe abortar sin escribir y nombrar el estado en el motivo.

**R20.** El sistema **no debe** consultar las tablas de gráficos de Sigrid
(`rcg`, `gra`) para decidir si cierra: la precondición del cierre es **propia**
—parte apto (R16) y archivado (R17)— y ninguna otra.

> **R20 es el orden que decidió el humano el 2026-08-26**: validar → cerrar →
> subir el PDF. Lo que el usuario sube y la aplicación valida y archiva es la
> prueba; el PDF entra en Sigrid después, en **F-012**. Se verifica con un
> **control negativo**: ni el SQL de lectura ni el dominio mencionan `rcg` ni
> `gra`.

**R21.** CUANDO se presenta el dry-run, el sistema debe advertir explícitamente
de que el cierre dejará la reclamación **cerrada sin gráfico en el ERP**, para
que quien confirma lo sepa antes de confirmar.

## 6 · La escritura: las dos filas, o ninguna

**R22.** CUANDO se ejecuta el cierre con `commit`, el sistema debe enviar el
`UPDATE` de `con.est` y el `INSERT` en `dbo.log` **en un solo batch
transaccional** de `POST /api/sql/write`.

**R23.** El `UPDATE` debe llevar `WHERE` sobre el `ide` de la reclamación **y**
sobre el estado de origen leído, y el batch debe declarar un tope de filas
afectadas que no pueda pasar de las dos filas esperadas.

**R24.** La fila de `dbo.log` debe escribirse con `tab = 'con'`, el `tip` de la
reclamación, `cod` y `res` copiados de la reclamación, `ope` de «proceso
ejecutado», `est` y `ori` con los valores que el ERP escribe, `emp` **tomado de
la reclamación**, y `fec`/`hor` con la fecha y la hora del cierre en los
formatos enteros de Sigrid.

**R25.** El `tex` de esa fila debe ser un texto **propio y rastreable** que
empiece por el texto del proceso del ERP, de modo que un cierre hecho por este
servicio se distinga de uno hecho a mano con un solo filtro por prefijo.

**R26.** El `ide` de la fila de `dbo.log` debe reservarse **dentro de la misma
sentencia** que la inserta, y el sistema debe tratar la colisión de clave como un
fallo recuperable que deja el ERP **sin ningún cambio**.

**R27.** SI la escritura falla por cualquier motivo, ENTONCES el sistema debe
registrar el cierre como `error` con su motivo y **no** debe reintentar la
escritura por su cuenta.

## 7 · El `usu`: quién firma el cierre

**R28.** El sistema debe escribir en `dbo.log.usu` el **login de Sigrid de la
persona que confirma el cierre**, nunca un usuario técnico ni un valor
constante.

**R29.** MIENTRAS exista una correspondencia **confirmada** para ese usuario en
`postventa.usuarios_sigrid`, el sistema debe usarla **sin derivar nada**.

**R30.** CUANDO no exista correspondencia confirmada, el sistema debe **derivar
un login candidato** de la parte local del correo del usuario autenticado, y
**verificarlo contra `dbo.usu`** por lectura antes de cualquier escritura.

> La derivación es la **siembra**, no el mecanismo de cada cierre. El supuesto
> —«el correo de la app y el de Sigrid son el mismo»— **la base no lo confirma**
> (`usu.ele` está vacío en los 228 usuarios), así que se trata como supuesto: se
> propone, se comprueba contra el ERP, y solo lo comprobado se guarda.

**R31.** SI el login candidato no existe **exactamente una vez** en `dbo.usu`,
o hay cualquier ambigüedad, ENTONCES el sistema debe abortar el cierre **sin
escribir nada en Sigrid** y devolver un error que nombre el correo del usuario y
el login que se intentó, pidiendo dar de alta la correspondencia a mano.

**R32.** El sistema **no debe jamás** escribir en `dbo.log.usu` un login que no
haya sido verificado contra `dbo.usu` en esa misma ejecución o en una anterior
cuyo resultado esté guardado como confirmado.

**R33.** CUANDO un login candidato se verifica con éxito, el sistema debe
**guardar la correspondencia como confirmada** en `postventa.usuarios_sigrid`,
con su marca de tiempo de verificación.

**R34.** El sistema debe admitir el **alta manual** de una correspondencia que no
siga la convención, y una correspondencia dada de alta a mano debe tener
**precedencia** sobre cualquier derivación.

> R34 es la salida para los casos medidos que no cumplen la convención: de los 8
> usuarios con correo registrado en el ERP, **2 no la cumplen**.

**R35.** El login usado **no debe** exceder la longitud del campo `usu` de
`dbo.log`.

## 8 · Puertas de entorno

**R36.** El sistema **no debe** poder escribir en Sigrid desde el entorno local:
la escritura debe estar permitida únicamente en los entornos desplegados.

**R37.** El sistema debe exigir además un **interruptor de cierre**, apagado por
defecto, y ese interruptor debe comprobarse **en la fábrica y en el propio
adaptador**, de modo que componer las piezas a mano tampoco permita escribir.

> R36 y R37 replican exactamente el patrón que F-006 aplicó a SharePoint
> (`ENTORNOS_CON_ARCHIVO` + `ARCHIVO_HABILITADO`), por el mismo motivo y con la
> misma doble comprobación.

**R38.** SI falta configuración para hablar con `sigrid-api`, ENTONCES el
sistema debe nombrar **todas** las variables que faltan de una vez y **jamás**
sus valores.

**R39.** Ningún test de la suite debe abrir una conexión de red hacia
`sigrid-api`, y ninguna prueba debe poder ejecutar una escritura contra Sigrid.

## 9 · La traza local

**R40.** CUANDO termina un dry-run correcto, el sistema debe registrar la traza
en `postventa.cierres` con estado `dry_run_ok` y su marca de tiempo.

**R41.** CUANDO termina un cierre con éxito, el sistema debe registrar la traza
con estado `cerrado`, el `oid` de quien lo confirmó, los códigos de estado de
origen y destino, y la marca de tiempo del cierre.

**R42.** El estado `cerrado` es **terminal**: un intento posterior de registrar
un cierre para ese mismo parte **no debe** pisar la traza existente.

**R43.** La traza debe guardar el **`oid` opaco de Entra** de quien confirma, y
**nunca** su correo, su nombre ni su login de Sigrid.

> R43 no es una duplicación de R28 ni choca con R33, y las tres cosas conviven
> porque son tres sitios distintos: en el **log de Sigrid** va el login, porque
> es el ERP quien necesita saber quién ejecutó el proceso; en la **traza del
> cierre** (`postventa.cierres`) va solo el `oid`, porque para reconstruir qué
> hicimos no hace falta saber quién es; y en la **tabla de correspondencias**
> (`postventa.usuarios_sigrid`) va el par `oid` → login, que es exactamente su
> razón de existir. Lo que R43 prohíbe es meter el login en la traza del cierre.

## 10 · Datos personales y logs

**R44.** El sistema **no debe** escribir en sus logs el DNI, el nombre, las
observaciones manuscritas ni ningún dato de propietario.

**R45.** El sistema **no debe** escribir en sus logs el correo, el nombre ni el
login de Sigrid de quien confirma el cierre.

> R45 no impide el mensaje de error de R31. Son dos destinos distintos: el
> **mensaje** va al usuario autenticado y le nombra **su propio** correo, que ya
> es suyo y lo tiene delante; el **log** lo lee cualquiera que abra Application
> Insights. Lo que no puede pasar es que ese mensaje se registre tal cual.

> R44 y R45 se verifican con **control negativo**, como en F-005 y F-019: un
> test que hace pasar datos personales por el camino real y comprueba que no
> aparecen en la salida. Sin control negativo, un logger que no registrase nada
> pasaría igual.

**R46.** El sistema **no debe** escribir ningún secreto —claves de función,
credenciales— en logs ni en mensajes de error.

## 11 · El borde HTTP

**R47.** CUANDO se llama al endpoint de cierre sin los campos obligatorios, el
sistema debe responder **400** diciendo **qué** falta.

**R48.** CUANDO el cierre no puede ejecutarse porque el parte no es apto, no
consta archivado, la reclamación no admite cierre o falta el mapeo del usuario,
el sistema debe responder **409** con el motivo.

**R49.** CUANDO la escritura está deshabilitada por entorno, por interruptor o
por configuración incompleta, el sistema debe responder **503** sin haber
tocado Sigrid.

**R50.** CUANDO `sigrid-api` falla o no responde, el sistema debe responder
**502** con el motivo, sin filtrar el cuerpo crudo del error ni ninguna
credencial.

**R51.** La respuesta del endpoint **no debe** contener ningún campo manuscrito
del parte, ni el contenido del PDF, ni la configuración del destino.

## 12 · Documentación que la feature deja al día

**R52.** CUANDO F-009 cambie lo que este proyecto escribe en un sistema ajeno,
`docs/INTEGRACION.md` debe reflejarlo en el mismo trabajo, con los nombres de
las variables nuevas y **nunca** sus valores.

**R53.** El documento del proyecto en `azure-apps/` debe reflejar que este
servicio **escribe** en Sigrid, qué escribe y qué se rompe si alguien cambia la
configuración de escritura de la pasarela.

---

## Trazabilidad de los requisitos que no llevan test unitario

Los siguientes **solo** se pueden verificar contra el ERP de producción y son
por tanto `MANUAL (humano)`, con su procedimiento en `tasks.md`:

| Requisito | Por qué no hay test unitario |
|---|---|
| R22, R26 | Que el batch sea de verdad transaccional y que la reserva de `ide` aguante lo prueba el ERP, no un mock. |
| R25 | Que el `tex` propio quede escrito y sea localizable se comprueba leyendo `dbo.log` después. |
| R30, R31, R33 | La existencia del login en `dbo.usu` y la siembra de la primera correspondencia son lecturas del ERP. |

Todo lo demás tiene test unitario **sin red, sin BBDD y sin IA**.
