<!-- specs/F-028-rechazo-manual/requirements.md -->
# F-028 · Rechazar un parte aprobado a mano, y quitar los espacios de los códigos de incidencia — Requisitos

> Notación EARS (`specs/SPECS.md`). Cada requisito se traduce a **al menos un
> test trazable** `test_f028_rN_*`. Rigor **`estandar`** (`harness/rigor.json`):
> fase RED obligatoria, puerta de cobertura sobre las líneas cambiadas (80 %) y
> **campaña de mutación** con los supervivientes documentados y juzgados por el
> reviewer. No hay más puertas: el nivel `estandar` no exige cero
> supervivientes —eso es `critico`— ni verificación en real como condición de
> cierre.

## Alcance

**La feature son dos asuntos**, y el humano quiere los dos aquí (ficha de
`harness/features.json`, 2026-09-15):

- **Asunto 1 · el gesto de rechazar.** Retirar a mano una aprobación humana de
  F-026: un motivo de revocación nuevo, el endpoint que la registra con el
  `oid` de quien la retira, el botón en la web, y la traza que conserva las dos
  decisiones en orden.
- **Asunto 2 · los espacios de los códigos.** `normalizar_codigo` no quita los
  espacios que rodean a un separador, y eso rompe el cierre en el ERP.
  Reproducido el 2026-09-15 (§0.7). Es un defecto **independiente** del rechazo
  manual y va aquí por petición expresa del humano.

**No entra**: ninguna escritura nueva en Sigrid ni en SharePoint —rechazar no
borra, no mueve y no renombra nada de lo ya escrito—; las reglas de reparto de
F-004, que no se tocan; la lista `MOTIVOS_APROBABLES` de F-026, que no se
amplía ni se recorta; la huella de F-026, cuyo **valor** no cambia (§8); el
contrato de `/api/archivar`, `/api/adjuntar` y `/api/cerrar`, que no cambia ni
una clave; y deshacer un cierre ya escrito en el ERP, que no se hace desde aquí
(R9).

---

## 0 · Lo que hay hoy, medido

Todo **[MEDIDO]** contra `dev` el **2026-09-15**, con su fuente al lado.

1. **La mitad del asunto 1 ya está hecha.** `domain/models/aprobacion.py`
   declara `Aprobacion` con `revocada_at_utc` y `revocada_motivo`,
   `esta_vigente()` devuelve falso en cuanto hay fecha de revocación, y
   `admite_circuito()` se apoya en ella. **[MEDIDO]**

2. **Y la revocación que existe es automática y solo una.**
   `MotivoRevocacion` tiene **un único valor**, `VEREDICTO_CAMBIADO`, y lo
   escribe `sentencias.revocar_aprobacion_si_cambio`, que `guardar_validacion`
   ejecuta **siempre** en la misma operación (F-026 R30). No hay ninguna otra
   forma de revocar: ni endpoint, ni botón, ni columna de autor. **[MEDIDO]**

3. **Una aprobación revocada no se borra** (F-026 R33): la fila sigue, con su
   `aprobado_por` y su `aprobado_at_utc`, y `select_aprobacion` **no filtra**
   por `revocada_at_utc IS NULL` a propósito, para que quien lee pueda
   distinguir «no la aprobó nadie» de «se aprobó y dejó de valer».
   **[MEDIDO]**

4. **Volver a aprobar borra la revocación anterior.** `upsert_aprobacion` hace
   `ON CONFLICT (hash_parte) DO UPDATE` y pone `revocada_at_utc` y
   `revocada_motivo` a `NULL` literal —está escrito en su docstring: «es el
   camino normal después de una revocación»—. Con `hash_parte` como clave
   primaria (F-026 R17, una sola fila por parte), **un ciclo aprobar → rechazar
   → aprobar deja en la base una sola fila y ni rastro del rechazo**.
   **[MEDIDO]** — es el argumento que decide §3.

5. **La pantalla ya sabe volver al color de antes.**
   `js/pipeline.js::aprobacionVale` exige `aprobacion.estado === "aprobado"`, y
   `interface_adapters/api/aprobacion_serializada.py` emite `"revocado"` para
   una aprobación con fecha de revocación. Un bloque que diga «revocado» ya
   devuelve el parte a su ámbar o su rojo, en el semáforo y en el selector de
   la tanda. **[MEDIDO]**

6. **Del cierre y del archivo se guarda estado, pero el puerto no los sabe
   leer.** `postventa.cierres.estado` admite
   `pendiente|dry_run_ok|cerrado|error|ya_cerrada` y
   `postventa.archivos.estado` admite `pendiente|archivado|error`
   (`sql/06_cierres.sql`, `sql/05_archivos.sql`). `RepositorioPartesPort` tiene
   `guardar_cierre` y `guardar_archivo`, pero **la única lectura de traza que
   existe es `consultar_grafico`**. **[MEDIDO]** — es lo que decide el diseño
   de R9.

7. **El defecto de los espacios, reproducido.** Con el código de `dev`, a
   fecha 2026-09-15:

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

8. **Por qué solo falla el cierre, y por eso costó verlo.** Hacia el ERP, la
   búsqueda de la reclamación es por igualdad exacta —`WHERE c.tip = ? AND
   c.cod = ?`, `infrastructure/sigrid/consultas.py`— y un código con espacios
   no encuentra nada. Hacia el nombre del fichero, la barra pasa a ` - ` y el
   colapso posterior **se come el sobrante por casualidad**: el parte se
   archiva bien y solo falla el cierre. La forma con guion y espacio detrás
   (`RS26.09- 0149`) sí produce un nombre distinto del canónico. **[MEDIDO]**

9. **Las dos conversiones ya comparten normalización, y está escrito por qué.**
   `a_codigo_de_sigrid` se apoya en `normalizar_codigo` «no en una copia […]
   dos criterios del mismo concepto divergen siempre» (su docstring). Por eso
   el arreglo va **en el dominio**, en `normalizar_codigo`, y no en una de las
   dos puntas. **[MEDIDO]**

10. **La huella de F-026 NO usa `normalizar_codigo`.**
    `huella_de_veredicto` normaliza el destino, los motivos, la firma, las
    observaciones, el código de obra y el número de incidencia con
    `aprobacion.py::_normalizar`, que es **otra función**: recorta, colapsa y
    pasa a minúsculas, y **no** traduce guiones raros ni toca los separadores.
    `domain/models/aprobacion.py` **no importa nada de `nombrado.py`**.
    **[MEDIDO]** — es lo que contesta al riesgo que plantea la ficha, y va
    entero en §8.

11. **Y lo que alimenta la huella son los valores crudos.**
    `validar_parte` copia `extraccion.campo("codigo_obra").valor` y
    `…("numero_incidencia").valor` tal cual a `ResultadoValidacion`, y
    `mapeo.valores_de_campos` guarda en `postventa.partes` lo que extrajo la
    IA sin normalizar. Ningún camino mete la salida de `normalizar_codigo`
    dentro de una huella. **[MEDIDO]**

---

## 1 · El gesto: rechazar es un acto explícito de una persona

**R1.** El sistema debe ofrecer un **acto explícito y propio** de retirada de
una aprobación humana, distinto de corregir un campo, de revalidar y de la
revocación automática que ya existe.

**R2.** CUANDO una persona rechaza un parte aprobado, el sistema debe registrar
la revocación con **quién** la hizo —su identificador opaco—, **cuándo**, el
**motivo cerrado** que dice que la retiró una persona y, si la escribió, su
**nota**.

**R3.** El sistema **no debe** borrar la aprobación al rechazarla: se marca
revocada y la fila conserva quién aprobó y cuándo (F-026 R33, sin cambios).

**R4.** SI llega una petición de rechazo **sin** el identificador de quien lo
hace, ENTONCES el sistema **no debe** registrar nada y debe decir que sin saber
quién decide no se puede registrar la decisión (simétrico a F-026 R4).

**R5.** El rechazo debe confirmarse con el **booleano de JSON** en el cuerpo, y
el sistema **no debe** pedir una segunda pantalla de confirmación: F-026 R29
sigue intacto y la confirmación única de F-025 sigue siendo la única que
precede a una escritura externa.

**R6.** El sistema debe permitir rechazar a **cualquiera que pueda aprobar**, no
solo a quien aprobó, y debe registrar el `oid` de quien lo hace (**P3**).

---

## 2 · Qué se puede rechazar, y qué no

**R7.** El sistema debe permitir el rechazo **solo** de un parte cuya
aprobación conste **vigente** en el almacén, leída de ahí y nunca del cuerpo de
la petición (F-026 R24).

**R8.** SI el parte **no consta aprobado**, o su aprobación **ya está
revocada**, ENTONCES el sistema **no debe** escribir nada nuevo y debe
responder diciendo el estado en que está, sin fingir un error de sistema: pulsar
dos veces el botón no puede producir dos revocaciones ni un fallo.

**R9.** SI el parte consta **cerrado en el ERP** —su traza de cierre está en
`cerrado` o en `ya_cerrada`—, ENTONCES el sistema **no debe** revocar la
aprobación y debe decir que lo escrito en Sigrid no se deshace desde aquí
(**P1**).

> Fingir que sí se deshace es peor que no ofrecerlo: la reclamación seguiría
> cerrada en producción con el parte colgado, y la pantalla diría lo contrario.

**R10.** MIENTRAS el parte conste **archivado pero no cerrado**, el sistema debe
permitir el rechazo, y debe **advertir** de que el PDF ya subido a SharePoint
sigue ahí: el rechazo no lo borra.

**R11.** El sistema **no debe** borrar, mover ni renombrar nada en SharePoint, y
**no debe** escribir nada en Sigrid al rechazar. Rechazar ocurre entero en el
esquema propio (límite de servicio, `CLAUDE.md`).

---

## 3 · Dónde se guarda

**R12.** La revocación debe guardarse en la **fila de la aprobación** del
esquema propio, con quién la retiró, cuándo, el motivo cerrado y la nota.

**R13.** El catálogo de motivos de revocación debe ganar el valor que dice que
**la retiró una persona**, y debe seguir siendo una **etiqueta corta y
cerrada** (F-026 R34): el texto libre va en una columna aparte, nunca dentro
del motivo.

**R14.** La nota debe ser **texto libre y opcional**, acotada en longitud y
recortada por los extremos; el sistema **no debe** exigirla para rechazar
(**P2**). Es texto de quien revisa, **no** del papel: no debe contener datos
del cliente.

**R15.** El sistema debe conservar, **en orden**, las decisiones humanas sobre
un parte —cada aprobación y cada retirada—, de modo que volver a aprobar **no
borre** el rechazo anterior (§0.4).

**R16.** El DDL nuevo debe ser **idempotente**, vivir **solo** en el esquema
propio y seguir la convención `NN_nombre.sql`; las columnas nuevas de una tabla
que ya existe se añaden con `ADD COLUMN IF NOT EXISTS`. El sistema **no debe**
ejecutar ninguna sentencia fuera de ese esquema ni de ámbito de servidor
(`CLAUDE.md`, regla dura del PostgreSQL compartido).

**R17.** La regla de **una sola aprobación viva por parte** (F-026 R17) sigue
intacta: lo que R15 añade es **histórico**, no estado.

---

## 4 · El borde HTTP

**R18.** El sistema debe exponer un endpoint **propio** para rechazar, y **no
debe** hacer del rechazo un efecto lateral de ningún endpoint existente (mismo
argumento que F-026 R18: una petición, una decisión, una fila de auditoría).

**R19.** El cuerpo de esa petición **no debe** llevar el DNI, ni las
observaciones, ni ningún byte del PDF, ni un veredicto ya hecho.

**R20.** El endpoint debe responder **400** si el cuerpo está mal formado o
falta quién decide, **409** si el parte no consta guardado o si su cierre ya
está escrito (R9), y **503** si aquí y ahora no hay base de datos. En los tres
casos **sin haber escrito nada**.

**R21.** El endpoint **no debe** depender de `ARCHIVO_HABILITADO` ni de
`CIERRE_HABILITADO`: rechazar escribe en el esquema propio (misma razón que
F-026 R21).

**R22.** La respuesta debe devolver el estado en que queda la aprobación, con
la **misma** serialización que ya usan `/api/parte` y `/api/aprobar`, y **sin**
el `oid` de quien aprobó ni el de quien rechazó.

---

## 5 · Qué cierra el rechazo

**R23.** CUANDO una aprobación queda revocada, el parte debe dejar de ser
admitido en el circuito **en el acto**: ni el front lo mete en la tanda, ni las
tres puertas del backend lo dejan archivar, adjuntar ni cerrar (F-026 R31, sin
cambios).

**R24.** El rechazo **no debe** cambiar el veredicto de la máquina, su destino
ni sus motivos: se registra al lado, nunca encima (F-026 R11).

**R25.** Un parte rechazado debe poder **volver a aprobarse** por el camino que
ya existe (F-026), sin ningún gesto nuevo, y las dos decisiones deben quedar
conservadas en orden (R15).

---

## 6 · Qué ve quien revisa

**R26.** MIENTRAS un parte conste aprobado y vigente, el sistema debe ofrecer
el gesto de rechazarlo **en el detalle del parte**, con el PDF delante, y no en
una lista (simétrico a F-026 R35).

**R27.** CUANDO el rechazo queda registrado, la pantalla debe volver a pintar
el parte con **el color que tenía antes de aprobarse** y decir que lo retiró
una persona y cuándo.

**R28.** El sistema **no debe** pintar en pantalla el identificador de quien
aprobó ni el de quien rechazó, ni su correo, ni su nombre (F-026 R38).

**R29.** SI el parte ya consta cerrado, ENTONCES la web **no debe** ofrecer el
gesto, y si aun así se intenta, debe decirlo con un texto entendible en vez de
fallar (R9).

**R30.** La pantalla debe **distinguir** una aprobación retirada por una persona
de una revocada porque el veredicto cambió: son dos hechos distintos y el
segundo no acusa a nadie.

---

## 7 · Los espacios de los códigos

**R31.** El sistema debe **eliminar los espacios que rodean a un separador**
—la barra `/` y el guion `-`— al normalizar un código, además de colapsar los
interiores y recortar los de los extremos.

**R32.** CUANDO el número de incidencia se lee con espacios alrededor del
separador, el código que se manda al ERP debe ser **idéntico** al que se
mandaría sin ellos, de modo que la reclamación se localice igual.

**R33.** CUANDO el número de incidencia llega en cualquiera de sus formas
equivalentes —con barra o con guion, con espacios o sin ellos, con guiones
raros—, el nombre del fichero debe ser **el mismo nombre canónico**.

**R34.** La conversión al formato de Sigrid debe seguir siendo la **inversa
exacta** del nombrado (F-009 R6) y las dos deben seguir apoyándose en **la
misma** normalización del dominio: ni una copia, ni un saneo local en una de
las dos puntas.

**R35.** El arreglo **no debe** tocar ninguna otra garantía de F-006: los ceros
a la izquierda se conservan (R4), el sufijo y la extensión van literales (R5) y
un nombre imposible sigue siendo un error ruidoso y nunca un saneo silencioso
(R7).

**R36.** SI un código queda vacío después de normalizar, ENTONCES sigue siendo
`NombradoImposible` y no se archiva nada (F-006 R6, sin cambios).

---

## 8 · El riesgo que la ficha manda tratar: la huella de F-026

> La ficha lo pide con todas las letras: si cambia lo que significa
> «normalizado», la huella puede **revocar aprobaciones vigentes por nada**,
> que es justo lo que F-026 se esforzó en evitar (su R32).

**Respuesta, medida (§0.10 y §0.11): no comparten criterio y no comparten
código.** `huella_de_veredicto` normaliza con `aprobacion.py::_normalizar`
—recorta, colapsa y baja a minúsculas—, que **no** traduce guiones raros y
**no** toca los separadores; `normalizar_codigo` vive en `nombrado.py` y el
módulo de aprobación **no lo importa**. Y lo que entra en la huella son los
valores **crudos** de la extracción, no la salida de ninguna normalización de
nombrado. Por tanto **cambiar `normalizar_codigo` no cambia ni una huella**.

**R37.** El cambio de normalización **no debe** revocar ninguna aprobación que
estuviera vigente: para toda entrada, la huella del veredicto debe seguir
valiendo exactamente lo que valía antes del cambio.

**R38.** El sistema debe dejar escrito, **con un test**, que las dos
normalizaciones son distintas **a propósito** y que el módulo de la aprobación
no importa el del nombrado, para que nadie las unifique por descuido.

> **Y por qué no se unifican ahora, que es la otra mitad de la pregunta.**
> Alinearlas sería defendible —hoy una relectura que solo cambie los espacios
> alrededor de la barra **sí** revoca, y eso es «revocar por nada»—, pero
> alinearlas **cambia el valor de las huellas ya escritas**, y con F-026
> desplegada y verificada en real el 2026-09-15 ya hay aprobaciones en la base.
> La enmienda H-1 de F-026 pudo tocar la huella porque no había ninguna; ahora
> hacerlo la revocaría. Se propone **no tocarla** y dejarlo como decisión
> aparte y consciente (**P5**).

---

## 9 · Datos personales, logs y secretos

**R39.** Los textos de pantalla y de log que añada F-028 **no deben** contener
el DNI, las observaciones manuscritas, la descripción, el correo, el nombre, el
`oid` de nadie **ni la nota** del rechazo.

**R40.** El log del endpoint de rechazo debe llevar el `hash_parte` y el
resultado, y **nada más** (simétrico a F-026 R44).

**R41.** F-028 **no debe** añadir ninguna variable de entorno, ningún secreto y
ninguna dependencia nueva.

---

## 10 · Las enmiendas

> **No se borra ningún requisito.** Se enmienda con un recuadro fechado que
> cita la premisa original **literal**, dice qué la invalidó y quién lo
> decidió. Es el patrón de R28 de F-010, de §7 de F-025 y de H-1 de F-026.

**R42.** **R8 de F-006** queda **enmendado** y debe recibir su recuadro
fechado, sin que se borre su texto.

> R8 dice hoy, literal: *«El sistema debe colapsar los espacios redundantes de
> los códigos (`0677  -  RS26.08` → `0677 - RS26.08`) y recortar los de los
> extremos, de forma que dos lecturas del mismo parte que solo difieran en
> espacios produzcan **el mismo** nombre.»*
>
> Lo que cambia: los espacios que **flanquean a un separador** ya no se
> colapsan, se **eliminan**. La garantía que R8 enunciaba —«dos lecturas que
> solo difieran en espacios producen el mismo nombre»— **no se recorta: se
> cumple por primera vez**, porque hasta hoy `RS26.09- 0149` producía un nombre
> distinto del canónico (§0.7). Lo que cambia es el valor intermedio de
> `normalizar_codigo`, y con él el test
> `test_f006_r8_los_espacios_interiores_se_colapsan_a_uno`, que fija ese valor.

**R43.** **R34 de F-026** queda **precisado**, no derogado: los motivos de
revocación siguen siendo etiqueta corta y cerrada, y ahora son **dos**. Su
recuadro debe decir que el texto libre del rechazo vive en columna propia y
nunca dentro del motivo.

**R44.** `docs/INTEGRACION.md` —que es la fuente de verdad— y
`azure-apps/postventa_incidencias.md` deben actualizarse **en esta misma
feature**: endpoint nuevo, columnas nuevas y tabla nueva. La regla de
`CLAUDE.md` no admite hacerlo después, y son **dos repositorios**, con commit
aparte y **sin `push`**.

**R45.** `docs/ARCHITECTURE.md` debe recoger, en la semántica 5 —«el número de
incidencia lo emite Sigrid y se escribe `RS26.08/0123`»—, que **los espacios
alrededor del separador no forman parte del código**, y en lo que dice de la
aprobación humana, que una aprobación puede retirarla una persona.

---

## Preguntas abiertas · las decide el humano al aprobar la spec

> Las **tres primeras** vienen en la ficha con su valor por defecto. Las dos
> últimas las abre esta spec al diseñar. En todas se propone el valor por
> defecto **razonado**; ninguna se da por decidida.

| # | Pregunta | Propuesta (por defecto) | Si el humano dice que no |
|---|---|---|---|
| **P1** | ¿Se puede rechazar un parte ya archivado **y cerrado**? | **No** (R9). La puerta se pone en el **cierre**, no en el archivo: lo escrito en el ERP es lo que no se deshace desde aquí. Archivado-sin-cerrar **sí** se puede rechazar, con aviso (R10) | Bloquear también el archivado es una condición más en la misma comprobación; permitirlo siempre tumba R9 y deja a la web sin nada que decir |
| **P2** | ¿El rechazo exige motivo en texto? | **Texto libre y opcional** (R14), acotado, guardado junto a la revocación y **fuera** del motivo cerrado | Obligatorio es una guardia más en el borde; sin nota se cae una columna y un campo de la pantalla |
| **P3** | ¿Quién puede rechazar? | **Cualquiera que pueda aprobar**, con su `oid` registrado (R6). No hay roles en el servicio: el acceso ya lo acota el grupo de Posventa (F-010) | Restringirlo a quien aprobó es comparar `oid` en el backend —una línea—, pero deja el parte bloqueado si esa persona no está |
| **P4** | ¿Se guarda el **histórico** de decisiones? | **Sí**, una bitácora append-only (R15). Es lo único que hace verdad el criterio de aceptación «la traza conserva las dos decisiones en orden»: hoy volver a aprobar borra el rechazo (§0.4) | Sin ella ese criterio no se puede cumplir y habría que retirarlo de la ficha. Alternativa intermedia: registrar solo las **retiradas**, con lo que se pierde la fecha de la aprobación anterior |
| **P5** | ¿Se alinea `_normalizar` (huella de F-026) con `normalizar_codigo`? | **No** (§8). Cambiaría el valor de huellas ya escritas y revocaría aprobaciones vigentes, que es lo que la propia ficha prohíbe | Alinearlas es una decisión aparte, consciente y fechada, sabiendo que invalida las aprobaciones que haya en la base |

---

## Trazabilidad de los requisitos que no llevan test unitario

| Requisito | Por qué no hay test unitario | Cómo se verifica |
|---|---|---|
| R12, R16 en su ejecución real sobre PostgreSQL | Crear columnas y tabla exige la base compartida | `MANUAL (humano)`, bloque 6 de `tasks.md`. El **texto** del DDL sí tiene test sin BBDD, con el patrón de `tests/test_f005_ddl_idempotente_texto.py` y de `tests/test_f026_ddl_aprobaciones.py`: idempotencia, esquema propio y `CHECK` comparados contra el `Enum` del dominio |
| R9, R10 extremo a extremo | Exigen una traza de cierre real y las ventanas de escritura | `MANUAL (humano)`; el **camino** tiene test unitario entero con dobles en memoria |
| R11 | Es una **prohibición de cambio** sobre otros sistemas | Control negativo: ni `infrastructure/sharepoint/` ni `infrastructure/sigrid/` aparecen en el diff, y sus suites siguen en verde |
| R32 contra el ERP | Exige el ERP de producción | `MANUAL (humano)`: el humano comprueba con un parte cuyo número se lea con espacios. El **dominio** sí tiene test: la tabla de §0.7 entera, fila a fila |
| R44, R45 | Son documentos, y uno está en **otro repositorio** | Repaso declarado en `tasks.md`; para `ARCHITECTURE.md`, test de documentación con el patrón de `tests/test_f026_documentacion.py` |

Todo lo demás tiene test unitario **sin red, sin BBDD y sin IA**.
