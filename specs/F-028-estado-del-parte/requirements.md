<!-- specs/F-028-estado-del-parte/requirements.md -->
# F-028 · Estado del parte —pendiente, aprobado, rechazado, cerrado— con histórico y transición manual — Requisitos

> Notación EARS (`specs/SPECS.md`). Cada requisito se traduce a **al menos un
> test trazable** `test_f028_rN_*`. Rigor **`estandar`** (`harness/rigor.json`):
> fase RED obligatoria, puerta de cobertura sobre las líneas cambiadas (80 %) y
> **campaña de mutación** con los supervivientes documentados y juzgados por el
> reviewer. Ni una puerta más: el nivel `estandar` no exige cero supervivientes
> —eso es `critico`— ni verificación en real como condición de cierre.

## Alcance

**Dos asuntos en una feature**, por petición expresa del humano
(`harness/features.json`, replanteada el 2026-09-15):

- **Asunto 1 · el estado del parte.** Sus palabras: *«los partes pueden estar
  pendientes, rechazados, aprobados o cerrados; lo que quiero es poder cambiar
  el estado desde donde esté a aprobado o rechazado, y que se guarde un
  histórico del estado»*. Eso es **un modelo de estado explícito**, que hoy no
  existe: el estado está repartido entre cuatro sitios y hay que reconstruirlo
  cruzándolos (§0).
- **Asunto 2 · los espacios de los códigos.** `normalizar_codigo` no quita los
  espacios que rodean a un separador y eso **rompe el cierre** en el ERP.
  Reproducido el 2026-09-15 (§0.9). Es un defecto **independiente** del asunto
  1 y va aquí porque el humano lo pidió así.

**No entra**: ninguna escritura nueva en Sigrid ni en SharePoint —cambiar de
estado no borra, no mueve y no renombra nada de lo ya escrito—; las reglas de
reparto de F-004, que no se tocan; deshacer un cierre ya escrito en el ERP, que
no se hace desde aquí (R7); el contrato de `/api/archivar`, `/api/adjuntar` y
`/api/cerrar`, que no cambia ni una clave; y el **valor** de la huella de F-026,
que no cambia (§9).

---

## 0 · Lo que hay hoy, medido

Todo **[MEDIDO]** contra `dev` el **2026-09-15**, con su fuente al lado.

1. **No existe ningún estado del parte.** No hay columna, ni enumerado, ni
   función que responda «¿en qué estado está este parte?». Lo que hay son
   **cuatro hechos en cuatro sitios**: el veredicto en `postventa.validaciones`
   (F-004), la aprobación humana en `postventa.aprobaciones` (F-026),
   `postventa.archivos.estado` (F-006) y `postventa.cierres.estado` (F-009).
   **[MEDIDO]** — es el problema que abre la feature.

2. **La mitad del asunto 1 ya está modelada.** `domain/models/aprobacion.py`
   declara `Aprobacion` con `revocada_at_utc` y `revocada_motivo`,
   `esta_vigente()` devuelve falso en cuanto hay fecha de revocación, y
   `admite_circuito()` —lo que la ficha llama «`puede_archivarse`»— se apoya en
   ella. **[MEDIDO]**

3. **La única revocación que existe es automática y tiene un solo motivo.**
   `MotivoRevocacion` tiene un único valor, `VEREDICTO_CAMBIADO`, y lo escribe
   `sentencias.revocar_aprobacion_si_cambio` dentro de `guardar_validacion`
   (F-026 R30, «la revocación ocurre en la escritura»). No hay endpoint, ni
   botón, ni columna de autor de la revocación. **[MEDIDO]**

4. **Volver a aprobar borra el rechazo anterior.** `upsert_aprobacion` hace
   `ON CONFLICT (hash_parte) DO UPDATE` y pone `revocada_at_utc` y
   `revocada_motivo` a `NULL` literal —está escrito en su docstring—. Con
   `hash_parte` como clave primaria (F-026 R17), **un ciclo aprobar → rechazar
   → aprobar deja UNA fila y ni rastro del rechazo**. **[MEDIDO]** — es el
   argumento que obliga al histórico (§4).

5. **Un parte verde nunca paga la consulta de la aprobación, y ese atajo es
   justo lo que impide rechazarlo.** `paso_archivo.py::_exigir_admitido`
   pregunta primero `admite_circuito(ctx.validacion, None)` y **vuelve sin
   consultar nada** si el parte es apto: «el parte apto no paga una consulta
   que no puede cambiar la decisión, que en una remesa real de 22 partes son 22
   consultas por paso» (su docstring). `paso_grafico` y `paso_cierre` hacen lo
   mismo. **[MEDIDO]** — mientras ese atajo exista, **rechazar un parte apto no
   puede funcionar**, y por eso R33 lo retira a propósito.

6. **La pantalla ya sabe volver al color de antes.**
   `js/pipeline.js::aprobacionVale` exige `aprobacion.estado === "aprobado"` y
   `interface_adapters/api/aprobacion_serializada.py` emite `"revocado"`. Un
   bloque que diga otra cosa devuelve el parte a su ámbar o su rojo, en el
   semáforo y en el selector de la tanda. **[MEDIDO]**

7. **Los dos estados que ya viven en la base y que esta feature no reinventa.**
   `postventa.cierres.estado` admite
   `pendiente|dry_run_ok|cerrado|error|ya_cerrada` y
   `postventa.archivos.estado` admite `pendiente|archivado|error`
   (`sql/06_cierres.sql`, `sql/05_archivos.sql`). **[MEDIDO]**

8. **Y de esos dos, el puerto no sabe leer ninguno.**
   `RepositorioPartesPort` tiene `guardar_archivo` y `guardar_cierre`, pero la
   **única** lectura de traza que existe es `consultar_grafico`. **[MEDIDO]** —
   decide el diseño de `cerrado`.

9. **El defecto de los espacios, reproducido.** Con el código de `dev`, el
   2026-09-15:

   | Entrada | `normalizar_codigo` | `a_codigo_de_sigrid` | `nombre_de_archivo(obra='0626')` |
   |---|---|---|---|
   | `RS26.09 / 0149` | `RS26.09 / 0149` | **`RS26.09 / 0149`** ✗ | `0626 - RS26.09 - 0149 PARTE FIRMADO.pdf` ✓ |
   | `RS26.09 /0149` | `RS26.09 /0149` | **`RS26.09 /0149`** ✗ | `0626 - RS26.09 - 0149 PARTE FIRMADO.pdf` ✓ |
   | `RS26.09- 0149` | `RS26.09- 0149` | **`RS26.09- 0149`** ✗ | **`0626 - RS26.09- 0149 PARTE FIRMADO.pdf`** ✗ |
   | `RS26.09 - 0149` | `RS26.09 - 0149` | `RS26.09/0149` ✓ | `0626 - RS26.09 - 0149 PARTE FIRMADO.pdf` ✓ |
   | `RS26.09/0149` | `RS26.09/0149` | `RS26.09/0149` ✓ | `0626 - RS26.09 - 0149 PARTE FIRMADO.pdf` ✓ |

   **[MEDIDO]**, ejecutado sobre el dominio, sin red. La causa:
   `normalizar_codigo` traduce los guiones raros, **colapsa** los espacios
   repetidos y recorta los extremos, pero **no quita los que flanquean a un
   separador**.

10. **Por qué solo falla el cierre, y por eso costó verlo.** Hacia el ERP la
    búsqueda es por igualdad exacta —`WHERE c.tip = ? AND c.cod = ?`,
    `infrastructure/sigrid/consultas.py`— y un código con espacios no encuentra
    nada. Hacia el nombre del fichero, la barra pasa a ` - ` y el colapso
    posterior **se come el sobrante por casualidad**. La forma con guion y
    espacio detrás sí produce un nombre distinto del canónico. **[MEDIDO]**

11. **Las dos conversiones ya comparten normalización, y está escrito por qué.**
    `a_codigo_de_sigrid` se apoya en `normalizar_codigo` «no en una copia […]
    dos criterios del mismo concepto divergen siempre» (su docstring). Por eso
    el arreglo va **en el dominio**. **[MEDIDO]**

12. **La huella de F-026 NO usa `normalizar_codigo`.** `huella_de_veredicto`
    normaliza con `aprobacion.py::_normalizar` —recorta, colapsa y baja a
    minúsculas—, que **no** traduce guiones raros y **no** toca separadores; y
    `aprobacion.py` **no importa nada de `nombrado.py`**. Además, lo que entra
    en la huella son los valores **crudos** de la extracción: `validar_parte`
    copia `extraccion.campo(...).valor` tal cual. **[MEDIDO]** — es lo que
    despeja el riesgo que planteaba la ficha, y va entero en §9.

---

## 1 · El modelo de estado

> Las reglas de esta sección las decidió el humano el **2026-09-15**. No son
> preguntas abiertas: son el encargo.

**R1.** El sistema debe reconocer **exactamente cuatro estados** de un parte, y
ninguno más: `pendiente`, `aprobado`, `rechazado` y `cerrado`.

**R2.** El sistema debe poder responder **en qué estado está un parte** sin que
quien pregunta tenga que cruzar cuatro tablas ni conocer el veredicto, la
aprobación, el archivo y el cierre por separado.

**R3.** CUANDO la validación automática declara un parte **apto** con destino
`archivo_y_cierre`, el parte debe **nacer `aprobado`**.

> Es deliberado y es lo que hace que el trabajo diario de Posventa no cambie:
> los verdes se siguen archivando en bloque, sin que nadie tenga que aprobar 22
> partes a mano. Lo que la feature añade no es un permiso más: es poder
> **rechazar** uno antes de que se archive.

**R4.** CUANDO la validación automática **no** declara apto un parte, el parte
debe nacer **`pendiente`**.

**R5.** MIENTRAS un parte esté `rechazado`, el sistema **no debe** archivarlo,
adjuntarlo ni cerrarlo.

**R6.** CUANDO la incidencia de un parte queda **cerrada en el ERP**, el estado
del parte debe ser `cerrado`.

**R7.** MIENTRAS un parte esté `cerrado`, el sistema **no debe** admitir ningún
cambio de estado: `cerrado` es **terminal** y de ahí no sale ninguna flecha.

> Lo escrito en SharePoint y en el ERP no se deshace desde aquí, y cambiar el
> estado solo conseguiría que nuestra base dijera algo distinto del ERP. La web
> lo **explica** en vez de fallar (R41).

**R8.** El estado **no debe** sustituir al veredicto de la máquina: el
veredicto, el destino y los motivos de F-004 siguen intactos y consultables
después de cualquier cambio de estado. La decisión humana se registra **al
lado**, nunca encima (F-026 R11).

---

## 2 · Quién mueve el estado, y cómo

**R9.** El sistema debe permitir que **una persona** mueva un parte a
`aprobado` o a `rechazado` desde **cualquiera** de los otros tres estados
—`pendiente`, `aprobado` o `rechazado`—, incluido deshacer su propia decisión y
la de la máquina.

**R10.** El sistema **no debe** ofrecer ningún otro destino manual: a
`pendiente` no se vuelve a mano, y a `cerrado` solo se llega cerrando la
incidencia.

**R11.** SI el cambio de estado es a **`rechazado`**, ENTONCES el motivo es
**obligatorio**: sin él no se registra nada y se dice por qué.

**R12.** CUANDO el cambio de estado es a **`aprobado`**, el motivo debe ser
**opcional**.

**R13.** El motivo debe ser **texto libre acotado** en longitud y recortado por
los extremos. Es texto de quien revisa, **no** del papel: no debe contener
datos del cliente.

**R14.** SI llega un cambio de estado **sin** el identificador de quien lo
hace, ENTONCES el sistema **no debe** registrar nada y debe decir que sin saber
quién decide no se puede registrar la decisión.

**R15.** El sistema debe permitir el cambio de estado a **cualquiera que pueda
entrar**: no hay roles en el servicio y el acceso ya lo acota el grupo de
Posventa (F-010). De quien decide se guarda el **`oid` opaco** de Entra ID y
nada más: nunca su correo, nunca su nombre y **nunca su login del ERP**.

---

## 3 · Dónde vive el estado

> Es **la** decisión de diseño de la feature y `design.md` §3 la razona con su
> alternativa y su coste. Aquí van los requisitos que la fijan.

**R16.** El sistema **no debe** guardar el estado como un dato más: el estado
debe **derivarse** de los hechos que ya tienen dueño —el veredicto, la última
decisión humana y la traza de cierre—, de modo que **no pueda contradecir** a
ninguno de ellos.

**R17.** La derivación debe ser **una sola función de dominio puro**, sin red,
sin SQL y sin reloj, y debe ser la **única** forma de responder a R2 en todo el
servicio: ni el borde, ni el front, ni una vista SQL pueden tener su propia
copia del criterio.

**R18.** El estado `cerrado` debe salir **de la traza de cierre** y de ningún
otro sitio, y debe **ganar** a cualquier decisión humana registrada.

**R19.** Una decisión humana `aprobado` debe valer **para el veredicto sobre el
que se tomó**: SI el veredicto guardado deja de ser aquel, ENTONCES el parte
**no debe** contar como aprobado por esa decisión (F-026 R30, conservada).

**R20.** CUANDO se vuelve a guardar **el mismo** veredicto, el sistema **no
debe** invalidar la decisión humana que lo aprobó (F-026 R32, conservada: al
recargar hay que volver a subir la remesa, y eso reprocesa cada parte).

> Y su simétrica, que es lo que hace segura la asimetría: una decisión humana
> **`rechazado` nunca caduca** por un cambio de veredicto. Lo automático puede
> **retirar** un permiso; no puede concederlo.

---

## 4 · El histórico

**R21.** El sistema debe guardar un **histórico append-only** de los cambios de
estado: **ninguna fila se pisa, ninguna se borra**.

**R22.** Cada fila del histórico debe decir **de qué estado a cuál**, **quién**
lo decidió, **cuándo** y **por qué**.

**R23.** CUANDO un parte nace `aprobado` porque la máquina lo declaró apto, el
histórico debe registrarlo, diciendo que **lo decidió la máquina** y no una
persona.

**R24.** El sistema **no debe** inventar un autor para lo que decidió la
máquina: donde va el `oid` de una persona, una decisión automática no debe
dejar un identificador falso.

**R25.** El histórico debe conservar, **en orden**, todas las decisiones sobre
un parte: un ciclo aprobar → rechazar → aprobar debe dejar las tres, y ninguna
puede quedar tapada por la siguiente (§0.4).

**R26.** El histórico debe ser **constancia, nunca criterio**: ninguna puerta
del backend ni de la pantalla puede decidir nada leyendo una fila de máquina.

> Es lo que impide que el histórico se convierta en la segunda fuente de verdad
> que R16 evita. Se apunta lo que pasó; lo que vale se deriva.

---

## 5 · El borde HTTP

**R27.** El sistema debe exponer un endpoint **propio** para cambiar el estado
de **un** parte, y **no debe** hacer del cambio de estado un efecto lateral de
ningún endpoint existente.

**R28.** El sistema **no debe** aceptar que el veredicto llegue hecho en esa
petición: el veredicto sobre el que se decide se **recalcula** con las reglas
de F-004 al recibirla (F-026 R5, conservada).

**R29.** El cambio de estado debe ser un **acto explícito** confirmado con el
booleano de JSON, y el sistema **no debe** pedir una segunda pantalla de
confirmación (F-026 R29 y la confirmación única de F-025, intactas).

**R30.** El cuerpo de la petición **no debe** llevar ningún byte del PDF ni un
veredicto ya hecho.

**R31.** El endpoint debe responder **400** si el cuerpo está mal formado, si
falta quién decide, si falta el motivo de un rechazo o si el estado pedido no
es uno de los dos manuales; **409** si el parte no consta guardado o si está
`cerrado` (R7); y **503** si aquí y ahora no hay base de datos. En los tres
casos **sin haber escrito nada**.

**R32.** El endpoint **no debe** depender de `ARCHIVO_HABILITADO` ni de
`CIERRE_HABILITADO`: decidir escribe en el esquema propio, y atarlo dejaría sin
poder registrar el trabajo de revisión justo cuando las ventanas de escritura
están cerradas, que es como se despliega el entorno (F-026 R21).

---

## 6 · Qué abre y qué cierra el estado

**R33.** Las tres puertas del backend —archivar, adjuntar y cerrar— deben
admitir **exactamente** los partes en estado `aprobado`, y deben resolverlo
**leyendo el almacén**, nunca el cuerpo de la petición (F-026 R24).

> Esto retira el atajo de §0.5: hoy el parte apto pasa sin consultar nada, y
> mientras eso siga así **un parte apto rechazado seguiría archivándose**. El
> coste —una consulta por parte y paso— se declara en `design.md` §6.

**R34.** El estado **no debe** relajar ninguna otra puerta: el parte sigue
teniendo que constar guardado (F-019), constar archivado antes del gráfico y
del cierre (F-006, F-012), constar adjuntado antes del cierre (F-012 R2), y el
cierre sigue exigiendo su dry-run dentro de la misma llamada, el login
verificado contra el ERP y el estado de origen en el `WHERE` (F-009, F-025).

**R35.** El estado **no debe** saltarse la **confirmación única** de F-025: un
parte aprobado entra en la tanda y se escribe cuando alguien confirma la tanda,
no antes.

**R36.** El sistema **no debe** permitir cambiar el estado **por lotes** ni
«aprobar toda la cola»: la decisión es de **un** parte, con ese parte delante.

**R37.** El cambio de estado **no debe** escribir nada en Sigrid ni en
SharePoint, ni borrar, mover o renombrar nada de lo ya escrito.

---

## 7 · Qué ve quien revisa

**R38.** El sistema debe enseñar el **estado** de cada parte en la lista y en
el detalle, y debe distinguir los cuatro.

**R39.** El sistema debe distinguir un parte **aprobado por una persona** de uno
aprobado por la máquina, con una marca propia y un texto que lo diga (F-026
R36, conservada).

**R40.** MIENTRAS un parte no esté `cerrado`, el detalle debe ofrecer **los dos
gestos** —aprobar y rechazar—, con el PDF delante y no en una lista, y el de
rechazar debe **exigir el motivo** antes de dejar enviarlo (R11).

**R41.** SI un parte está `cerrado`, ENTONCES la web **no debe** ofrecer ningún
gesto y debe **explicar por qué** en vez de fallar (R7).

**R42.** El sistema **no debe** pintar en pantalla el identificador de quien
decidió, ni su correo, ni su nombre (F-026 R38).

**R43.** La pantalla debe distinguir «lo decidió una persona» de «el veredicto
cambió y la aprobación dejó de contar»: son dos hechos distintos y el segundo
no acusa a nadie.

---

## 8 · Los espacios de los códigos (asunto 2)

**R44.** El sistema debe **eliminar los espacios que rodean a un separador**
—la barra `/` y el guion `-`— al normalizar un código, además de colapsar los
interiores y recortar los de los extremos.

**R45.** CUANDO el número de incidencia se lee con espacios alrededor del
separador, el código que se manda al ERP debe ser **idéntico** al que se
mandaría sin ellos, de modo que la reclamación se localice igual.

**R46.** CUANDO el número de incidencia llega en cualquiera de sus formas
equivalentes —con barra o con guion, con espacios o sin ellos, con guiones
raros—, el nombre del fichero debe ser **el mismo nombre canónico**.

**R47.** La conversión al formato de Sigrid debe seguir siendo la **inversa
exacta** del nombrado (F-009 R6) y las dos deben seguir apoyándose en **la
misma** normalización del dominio: ni una copia, ni un saneo local en una punta.

**R48.** El arreglo **no debe** tocar ninguna otra garantía de F-006: los ceros
a la izquierda se conservan (R4), el sufijo y la extensión van literales (R5) y
un nombre imposible sigue siendo un error ruidoso y nunca un saneo silencioso
(R7).

**R49.** SI un código queda vacío después de normalizar, ENTONCES sigue siendo
`NombradoImposible` y no se archiva nada (F-006 R6, sin cambios).

---

## 9 · El riesgo que la ficha manda tratar: la huella de F-026

> La ficha lo pide con todas las letras: si cambia lo que significa
> «normalizado», la huella podría **invalidar decisiones vigentes por nada**,
> que es justo lo que F-026 se esforzó en evitar (su R32).

**Respuesta, medida (§0.12): no comparten criterio y no comparten código.**
`huella_de_veredicto` normaliza con `aprobacion.py::_normalizar`, que no toca
separadores ni guiones raros; `normalizar_codigo` vive en `nombrado.py` y el
módulo de la aprobación **no lo importa**; y lo que entra en la huella son los
valores **crudos** de la extracción. **Cambiar `normalizar_codigo` no cambia ni
una huella.**

**R50.** El cambio de normalización **no debe** invalidar ninguna decisión
humana vigente: para toda entrada, la huella del veredicto debe seguir valiendo
exactamente lo que valía antes del cambio.

**R51.** El sistema debe dejar escrito, **con un test**, que las dos
normalizaciones son distintas **a propósito** y que el módulo de la decisión no
importa el del nombrado, para que nadie las unifique por descuido.

> **Y no se alinean** (decisión del humano, 2026-09-15). Alinearlas sería
> defendible —hoy una relectura que solo cambie los espacios alrededor de la
> barra **sí** invalida la aprobación, y eso es invalidar por nada—, pero
> cambiaría el valor de las huellas ya escritas, y con F-026 desplegada y
> verificada en real ya hay decisiones en la base. Queda **declarado como
> defecto latente conocido**, no arreglado aquí.

---

## 10 · Datos personales, logs y secretos

**R52.** Los textos de pantalla y de log que añada F-028 **no deben** contener
el DNI, las observaciones manuscritas, la descripción, el correo, el nombre, el
`oid` de nadie **ni el motivo** que escriba quien decide.

**R53.** El log del endpoint de estado debe llevar el `hash_parte`, el estado
de origen, el de destino y el resultado, y **nada más**.

**R54.** F-028 **no debe** añadir ninguna variable de entorno, ningún secreto y
ninguna dependencia nueva.

---

## 11 · Las enmiendas

> **No se borra ningún requisito.** Se enmienda con un recuadro fechado que
> cita la premisa original **literal**, dice qué la invalidó y quién lo
> decidió. Es el patrón de R28 de F-010, de §7 de F-025 y de H-1 de F-026.

**R55.** **R8 de F-006** queda **enmendado** y debe recibir su recuadro
fechado, sin que se borre su texto.

> R8 dice hoy, literal: *«El sistema debe colapsar los espacios redundantes de
> los códigos (`0677  -  RS26.08` → `0677 - RS26.08`) y recortar los de los
> extremos, de forma que dos lecturas del mismo parte que solo difieran en
> espacios produzcan **el mismo** nombre.»*
>
> Lo que cambia: los espacios que **flanquean a un separador** ya no se
> colapsan, se **eliminan**. La garantía que R8 enunciaba **no se recorta: se
> cumple por primera vez**, porque hasta hoy `RS26.09- 0149` producía un nombre
> distinto del canónico (§0.9). Lo que cambia es el valor intermedio de
> `normalizar_codigo`, y con él el test
> `test_f006_r8_los_espacios_interiores_se_colapsan_a_uno`, que lo fija.

**R56.** **R12, R17 y R22 de F-026** quedan **enmendados**: la decisión humana
deja de vivir en una fila que se sustituye y pasa a vivir en el histórico
append-only, cuya **última fila humana manda**. Su recuadro debe citar el texto
original y decir qué lo invalidó: **§0.4**, que el `ON CONFLICT DO UPDATE`
borra el rechazo anterior y hace imposible el criterio de aceptación «el
histórico conserva las decisiones en orden».

**R57.** **R30 y R31 de F-026** quedan **precisados, no derogados**: la
aprobación sigue dejando de valer cuando el veredicto cambia, pero eso se
resuelve **al derivar el estado** y no con una escritura que marca la fila. El
recuadro debe decir por qué: con el estado derivado no hay dato guardado que
pueda quedarse viejo, y resolverlo al leer elimina la ventana entre las dos
escrituras.

**R58.** **R36 de F-025** y los tres puntos de `docs/ARCHITECTURE.md` que F-026
ya enmendó deben quedar al día con el vocabulario del estado —«solo se archiva
lo que está `aprobado`»—, **sin borrar** lo anterior.

**R59.** `docs/INTEGRACION.md` —la fuente de verdad— y
`azure-apps/postventa_incidencias.md` deben actualizarse **en esta misma
feature**: endpoint nuevo, tabla nueva y qué deja de escribirse. La regla de
`CLAUDE.md` no admite hacerlo después, y son **dos repositorios**, con commit
aparte y **sin `push`**.

---

## Decisiones ya tomadas · no se vuelven a abrir

> El humano las decidió el **2026-09-15** al replantear la feature. Se listan
> aquí para que el implementer y el reviewer no las reabran.

| # | Decisión |
|---|---|
| D1 | Cuatro estados: `pendiente`, `aprobado`, `rechazado`, `cerrado` |
| D2 | El apto **nace aprobado**, y el histórico dice que lo decidió la máquina |
| D3 | El no apto nace `pendiente` |
| D4 | Una persona mueve a `aprobado` o `rechazado` desde los otros tres |
| D5 | `cerrado` es **terminal**; la web lo explica en vez de fallar |
| D6 | Motivo **obligatorio** al rechazar, **opcional** al aprobar |
| D7 | Puede cambiarlo **cualquiera** que entre; se guarda su `oid` opaco |
| D8 | Histórico **append-only**: de qué estado a cuál, quién, cuándo y por qué |
| D9 | Las dos normalizaciones **no se alinean** (§9) |

---

## Trazabilidad de los requisitos que no llevan test unitario

| Requisito | Por qué no hay test unitario | Cómo se verifica |
|---|---|---|
| R21, R25 en su ejecución real sobre PostgreSQL | Crear la tabla y acumular filas exige la base compartida | `MANUAL (humano)`, bloque 8 de `tasks.md`. El **texto** del DDL sí tiene test sin BBDD, con el patrón de `test_f005_ddl_idempotente_texto.py` y `test_f026_ddl_aprobaciones.py` |
| R6, R18 extremo a extremo | Exigen una traza de cierre real | `MANUAL (humano)`; el **camino** tiene test unitario entero con dobles en memoria |
| R37 | Es una **prohibición de cambio** sobre otros sistemas | Control negativo: ni `infrastructure/sharepoint/` ni `infrastructure/sigrid/` aparecen en el diff, y sus suites siguen en verde |
| R45 contra el ERP | Exige el ERP de producción | `MANUAL (humano)`: con un parte cuyo número se lea con espacios. El **dominio** sí tiene test: la tabla de §0.9 entera, fila a fila |
| R58, R59 | Son documentos, y uno está en **otro repositorio** | Repaso declarado en `tasks.md`; para `ARCHITECTURE.md`, test de documentación con el patrón de `test_f026_documentacion.py` |

Todo lo demás tiene test unitario **sin red, sin BBDD y sin IA**.
