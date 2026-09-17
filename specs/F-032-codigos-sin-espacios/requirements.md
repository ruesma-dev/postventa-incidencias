<!-- specs/F-032-codigos-sin-espacios/requirements.md -->
# F-032 · Los códigos no admiten espacios — Requisitos

> Notación EARS (`specs/SPECS.md`). Cada requisito se traduce a **al menos un
> test trazable** `test_f032_rN_*`. Rigor **`critico`** (`harness/rigor.json`):
> fase RED obligatoria, puerta de cobertura sobre las líneas cambiadas (80 %) y
> campaña de mutación con **cero supervivientes** —cada uno exige un test nuevo
> o una justificación escrita aceptada por el humano—.
>
> Es `critico` por lo que hay al otro lado: el código de obra decide **la
> carpeta de SharePoint** donde acaba un PDF con el DNI manuscrito de un
> cliente, y el número de incidencia decide **qué reclamación se cierra** en el
> ERP de producción. Un espacio de más no da un resultado aproximado: da la
> carpeta de otra promoción o ninguna reclamación.

## Alcance

**Un defecto de lectura, y nada más.** F-032 no añade ninguna capacidad: hace
que un código leído con un espacio de más valga lo mismo que el mismo código
leído sin él, que es lo que F-006 R8 lleva prometiendo desde el primer día y
lo que F-028 dejó cumplido solo a medias.

**Entra**, y son los **dos sitios que no tocan la huella**, tal y como los fijó
el humano el 2026-09-17:

1. **`domain/models/nombrado.py::normalizar_codigo`**: eliminar **todos** los
   espacios de un código en vez de colapsarlos a uno. De ahí heredan las dos
   conversiones —el nombre del fichero (F-006) y el código del ERP (F-009
   `a_codigo_de_sigrid`)— y la carpeta de archivo, así que una línea cubre el
   ERP, la carpeta y el nombre.
2. **El saneo en la extracción**: `codigo_obra` y `numero_incidencia` se sanean
   con esa misma función **antes** de viajar y antes de guardarse, de modo que
   lo que se escriba en `postventa.partes` **nazca sin espacios** y nadie tenga
   que editar un parte a mano nunca más.

**No entra**, y cada una de estas cosas se ha considerado y se ha dejado fuera
a propósito:

- **`huella_de_veredicto` y `_normalizar` no se tocan**
  (`domain/models/aprobacion.py:165-178`). Es la decisión expresa del humano
  del 2026-09-17 y no se reabre: la huella guardada se calculó con la regla
  vieja y la recompuesta usaría la nueva, así que **todo parte aprobado cuyo
  código u observaciones lleven un espacio volvería a `pendiente`** y habría
  que volver a decidirlo. Rompería además R50 y R51 de F-028 —con centinela en
  `tests/test_f028_huella_intacta.py`— y el §8 de `design.md` de F-030. Si
  algún día se quieren alinear las dos normalizaciones, es **feature propia con
  migración** (§3, D1);
- **ninguna migración de datos**: ni `UPDATE`, ni script de limpieza sobre las
  filas ya escritas en `postventa.partes`. No es pereza: los dos códigos que
  entran en la huella **se leen de esa tabla** (§0.7), así que limpiarlas por
  fuera haría exactamente el daño que el punto anterior evita (§3, D2);
- **ningún DDL**: ni tabla, ni columna, ni índice, ni fichero nuevo en
  `infrastructure/persistencia/sql/`;
- **ni una clave del contrato HTTP**: `/api/extraer`, `/api/parte`,
  `/api/validar`, `/api/estado`, `/api/archivar`, `/api/adjuntar` y
  `/api/cerrar` siguen aceptando y devolviendo exactamente lo mismo.
  **`services/postventa-front/` no se toca**;
- **ninguna operación nueva sobre SharePoint**: `ArchivoPort` no gana borrado
  ni renombrado. Darle a este servicio la capacidad de borrar en el archivo de
  Posventa no lo paga esta feature (§3, D4);
- **el prompt no es el arreglo.** Pedirle al modelo que no escriba espacios
  (`config/prompts.yaml`) no garantiza nada —la lectura no es determinista— y
  dejaría el defecto vivo para el texto que teclea una persona. Puede añadirse
  algún día como **ayuda**, nunca como garantía (§3, D5);
- **F-031 no se invade** (§4): de dónde saca `/api/archivar` los códigos con
  los que nombra el fichero sigue siendo su asunto.

---

## 0 · Lo que pasa hoy, medido

Todo **[MEDIDO]** por lectura del código de la rama `dev` a **2026-09-17**, con
su fuente al lado. Los ejemplos de código y de incidencia que aparecen aquí son
los del caso real de ayer; no hay ningún dato personal en esta spec.

### 0.1 · `normalizar_codigo` colapsa, no elimina

`domain/models/nombrado.py:145-146`:

```python
colapsado = " ".join(bruto.translate(_A_GUION_NORMAL).split())
return _ESPACIOS_JUNTO_AL_SEPARADOR.sub(r"\1", colapsado)
```

La primera línea **colapsa** todos los espacios interiores a uno; la segunda
**elimina** solo los que flanquean a un separador (`/` o `-`). Un espacio que
no toca un separador sobrevive al colapso: `RS 26.09/0178` normaliza a
`RS 26.09/0178`, con el espacio intacto.

Eso es exactamente lo que F-028 arregló **a medias**: sus R44–R47 cazaron
`RS26.09 / 0149` —la forma que se vio fallar el 2026-09-15— y dejaron viva la
forma en la que el espacio cae **dentro de un tramo**.

### 0.2 · El ERP busca por igualdad exacta, así que no encuentra nada

`infrastructure/sigrid/consultas.py:78-84`, cláusula final de
`SQL_RECLAMACION`:

```sql
WHERE c.tip = ? AND c.cod = ?
```

Sin `LIKE`, sin `REPLACE`, sin `TRIM`. Un código con un espacio de más no
devuelve «casi» la reclamación: devuelve **cero filas**, y el dominio lo
traduce a `ReclamacionNoLocalizada` (`application/pipelines/paso_cierre.py:308-312`).
El gráfico muere por lo mismo, un paso antes
(`application/pipelines/paso_grafico.py:304`, `_codigo_de_incidencia`).

### 0.3 · Nadie más normaliza por el camino

- **La extracción guarda el valor crudo.** `paso_extraccion.py:106` construye
  `CampoExtraido(valor=bruto.valor, confianza_pct=confianza)`: lo único que se
  sanea es la confianza. La docstring del módulo lo dice con todas las letras:
  *«no normaliza ningún valor (F-006 nombrará el fichero)»*.
- **El cuerpo HTTP también lo copia crudo.** `interface_adapters/api/cuerpos.py:126`
  (`a_extraccion` → `a_campo`) sanea la confianza **con la función del
  dominio** y copia el valor tal cual.
- **El front solo recorta los extremos.** `services/postventa-front/js/pipeline.js:186`
  (`normalizarValor`) hace `String(valor).trim()`; un espacio interior no lo
  toca nadie.
- **Y la base se queda el literal sucio.** `sentencias.upsert_parte` escribe
  `valores_de_campos(extraccion)` tal cual en `postventa.partes`.

### 0.4 · El daño silencioso: dos nombres para el mismo parte

`nombre_de_archivo` compone `0626 - RS 26.09 - 0178 PARTE FIRMADO.pdf` y
`nombre_admisible` (`nombrado.py`) lo **acepta**: el espacio interior no es un
carácter prohibido, el nombre no empieza ni acaba en espacio y no acaba en
punto. Así que el mismo parte puede acabar en SharePoint con dos nombres
distintos —uno por cada lectura— y a ojo son el mismo fichero.

### 0.5 · Y el código de obra decide **la carpeta**

`carpeta_de_archivo(carpeta_base=..., codigo_obra=...)` compone
`<base>/<obra>` con el código **normalizado por la misma función**. Un
`06 26` produce hoy la carpeta `Postventa/06 26`, que no es
`Postventa/0626`: un PDF con el DNI manuscrito de un cliente archivado en una
carpeta que no es la de su promoción, y que nadie mira. No es el mismo daño
que un cierre fallido —ese se ve—: este no se ve.

### 0.6 · La huella **no** pasa por `normalizar_codigo`

`domain/models/aprobacion.py:165-178` tiene su propia `_normalizar`, que
recorta, colapsa y baja a minúsculas. F-028 lo midió, lo razonó y lo dejó
vigilado con tres controles en `tests/test_f028_huella_intacta.py`: el valor
(siete huellas escritas literales, medidas en el árbol anterior al cambio), el
acoplamiento (`aprobacion.py` no importa `nombrado` ni nombra sus piezas) y el
efecto (un parte aprobado sigue aprobado). **Su conclusión, literal: «cambiar
`normalizar_codigo` no cambia ni una huella».**

### 0.7 · Pero los códigos de la huella **se leen de `postventa.partes`**

Esto no estaba escrito en ninguna spec y es lo que decide el §4 de esta:

`sentencias.py:589` (consulta de situación, la que alimenta a las tres puertas
del circuito) selecciona `p.codigo_obra, p.numero_incidencia` **de la tabla
`partes`**, no de `validaciones`; y `mapeo.py:406-426`
(`fila_a_validacion_y_cierre`) los mete en el `ResultadoValidacion` sobre el
que la puerta **recompone la huella**.

Consecuencia directa, y es la que hay que tener delante: **un `UPDATE` que
limpiara `postventa.partes` cambiaría el valor de huellas ya guardadas y
revocaría decisiones humanas vivas**, que es justo lo que el alcance prohíbe.
La migración de datos no está fuera por comodidad: está fuera porque hace el
daño que la feature evita.

### 0.8 · La capa de idempotencia del archivo está **inerte** desde el endpoint

`paso_archivo.py:96` declara `traza_previa: TrazaArchivo | None = None` y
`:131` la usa para cortar sin llamar a nadie (F-006 R14, la capa **L1** que
`docs/ARCHITECTURE.md` describe en el paso 6). Pero
`interface_adapters/api/archivar.py:118-128` llama a `paso_archivo` **sin
pasarla**, y el único sitio del árbol donde se pasa es
`tests/test_f019_orden_archivado.py`. `SituacionParte` —lo que la puerta ya
consulta— **no trae la traza del archivo** (`domain/models/estado.py:189-208`:
son cuatro cosas y ninguna es esa), y el puerto de persistencia no tiene
`consultar_archivo` (`domain/ports/persistencia.py`: hay `consultar_grafico`,
`consultar_situacion` y `consultar_estado_cierre`).

O sea: **hoy `/api/archivar` vuelve a subir siempre**, confiando en el
reemplazo del homónimo (capa L2). Mientras el nombre no cambiaba, eso era
inofensivo. Con el nombre nuevo deja de serlo: el reemplazo no encuentra
homónimo y sube un **segundo** fichero. Es el riesgo que resuelve el §5.

### 0.9 · El caso real, literal

**2026-09-17.** El humano verifica F-030 contra producción (V1). El circuito
funciona, pero antes tiene que **editar a mano el código del parte**: la IA
había leído `RS 26.09/0178` —espacio dentro del primer tramo— y con ese valor
el cierre moría en `ReclamacionNoLocalizada`. La incidencia es la misma que
protagonizó F-030: **RS26.09/0178**.

Ese literal, `RS 26.09/0178`, es un requisito de esta spec: tiene que estar en
la tabla de casos, escrito tal cual (R27).

---

## 1 · El saneo del código (dominio puro)

**R1.** El sistema debe **eliminar todos los espacios** de un código
normalizado, estén donde estén: en los extremos, dentro de un tramo o
flanqueando a un separador. `RS 26.09/0178` normaliza a `RS26.09/0178` y
`06 26` a `0626`.

> **Enmienda a F-006 R8 (ver `specs/F-006-sharepoint/requirements.md`).** R8
> pedía «colapsar a uno los espacios redundantes que no tocan un separador».
> Eso deja de ser cierto: ya no se colapsan, se eliminan. La garantía que R8
> promete —que dos lecturas del mismo parte que solo difieran en espacios
> produzcan el mismo nombre y el mismo código para el ERP— es la que **por fin
> se cumple entera**; lo que se cae es el ejemplo, que describía el defecto.

**R2.** El sistema debe tratar como espacio **cualquier blanco Unicode**:
espacio normal, tabulador, salto de línea, espacio no separable (`U+00A0`) y
espacio fino no separable (`U+202F`). Los tres últimos salen de los escaneos y
de Word, y a ojo son indistinguibles de un espacio normal.

**R3.** El sistema debe seguir conservando **los ceros a la izquierda** y
trabajando con `str`: `0626` nunca es `626`, y quitar espacios no puede ser la
puerta trasera por la que un código se convierta en número.

**R4.** SI el código es `None`, vacío o solo blancos, ENTONCES el sistema debe
seguir devolviendo la cadena vacía, sin levantar nada: quien decide que eso es
un error es quien nombra el fichero (F-006 R6, F-028 R49, sin cambios).

**R5.** El sistema debe seguir sin partir el **código de obra** por sus
guiones: `06-77` es una obra, no dos tramos (F-028 R48, sin cambios).

**R6.** El saneo debe vivir **en `normalizar_codigo` y en ningún otro sitio**:
las dos conversiones del código —`nombre_de_archivo` y `a_codigo_de_sigrid`—
siguen heredando de ella y no añaden un saneo propio (F-028 R47, sin cambios).

**R7.** CUANDO el número de incidencia se haya leído con un espacio dentro de
un tramo (`RS 26.09/0178`), el sistema debe mandar al ERP **`RS26.09/0178`**,
que es el literal por el que Sigrid busca la reclamación.

**R8.** CUANDO el número de incidencia se haya leído con un espacio dentro de
un tramo, el sistema debe nombrar el fichero
**`0626 - RS26.09 - 0178 PARTE FIRMADO.pdf`**: un solo nombre canónico para
todas las formas de leer el mismo número.

**R9.** CUANDO el código de obra se haya leído con un espacio (`06 26`), el
sistema debe archivar en la carpeta **`<base>/0626`** y no en una carpeta
nueva.

**R10.** El sistema debe mantener **idempotentes** las dos conversiones:
aplicarlas dos veces sobre su propio resultado da el mismo valor (F-009 R6,
sin cambios).

---

## 2 · El saneo en la extracción (lo que se persiste)

**R11.** CUANDO el pipeline complete los campos de una extracción
(`paso_extraccion`), el sistema debe sanear `codigo_obra` y
`numero_incidencia` con **la misma función del dominio** que usan el nombrado
y el ERP.

**R12.** CUANDO una petición HTTP reconstruya una extracción desde su cuerpo
(`cuerpos.a_extraccion`), el sistema debe aplicar **ese mismo saneo**. Es la
puerta por la que pasan `/api/parte`, `/api/validar` y `/api/estado`, y por
tanto la única por la que el valor llega a la base: sin esto, R13 no se cumple
(`design.md` §4.2).

**R13.** El sistema debe guardar en `postventa.partes` los dos códigos **ya sin
espacios**, sin que nadie tenga que editar el parte a mano.

**R14.** El sistema debe sanear **solo esos dos campos**. Los otros siete
—`promocion`, `unidad`, `fecha_servicio`, `descripcion`, `dni_cliente`,
`observaciones`, `numero_pagina`— llevan texto con espacios legítimos y se
copian tal cual: quitarle los espacios a una observación manuscrita la
convertiría en otra cosa, y las observaciones son lo que lee una persona para
decidir.

**R15.** SI el saneo cambia el valor que leyó el modelo, ENTONCES el sistema
debe dejar un **aviso** de extracción diciendo qué se leyó y qué se guardó. El
saneo no puede ser silencioso: quien mire el parte tiene que poder ver que el
valor que hay guardado no es letra por letra el que salió del papel.

**R16.** El sistema no debe convertir un campo ausente en uno leído ni al
revés: `None` sigue siendo `None`, y un valor que se quede vacío tras el saneo
se guarda como **no leído**. Es la misma equivalencia que ya aplican F-004 («solo
espacios» es vacío) y la huella (`_normalizar(None) == _normalizar("   ")`), así
que esto **no mueve ninguna huella**.

---

## 3 · La huella no se mueve (la garantía que paga la feature)

**R17.** El sistema debe dejar `huella_de_veredicto` y `_normalizar`
(`domain/models/aprobacion.py`) **exactamente como están**: ni una línea.

**R18.** Las **siete huellas** que F-028 midió en el árbol anterior a su
bloque 7 y dejó escritas literales en `tests/test_f028_huella_intacta.py` deben
seguir valiendo **lo mismo** después de este cambio.

**R19.** Además, el sistema debe fijar **dos casos nuevos propios de este
cambio** —un veredicto cuyo `numero_incidencia` sea `RS 26.09/0178` y otro cuyo
`codigo_obra` sea `06 26`, que son las formas que F-028 **no** tocaba y esta sí—
con su huella **medida antes del cambio** y escrita literal, y esa huella debe
seguir valiendo lo mismo después. No basta con apoyarse en el centinela
existente: el centinela de F-028 mide las formas de F-028.

**R20.** MIENTRAS exista una decisión humana guardada sobre un veredicto
anterior al cambio, el sistema debe seguir dando ese parte por **`aprobado`** y
seguir diciendo que lo decidió **una persona** (F-028 R43, `decision_en_firme`).

**R21.** El sistema debe mantener separadas las dos normalizaciones:
`aprobacion.py` sigue sin importar `domain.models.nombrado` y sin nombrar
`normalizar_codigo`, `tramos_de_codigo` ni `SEPARADORES_DE_CODIGO` (F-028 R51,
sin cambios).

---

## 4 · Las filas que ya están guardadas sucias

**R22.** El sistema **no debe modificar ninguna fila ya escrita** en
`postventa.partes` ni en `postventa.validaciones`: sin `UPDATE`, sin script de
limpieza y sin DDL. Los códigos que entran en la huella se leen de
`postventa.partes` (§0.7), así que limpiarlas por fuera revocaría decisiones
humanas vivas —el daño exacto que el alcance de esta feature prohíbe—.

**R23.** CUANDO un parte se reprocese —se vuelva a extraer y a guardar—, el
sistema debe escribir sus códigos **ya saneados**; y si eso cambia la huella de
su veredicto, la decisión humana anterior **deja de contar** y el parte vuelve
a `pendiente`. Es el comportamiento correcto y ya especificado (F-028 R19): se
decidió sobre un veredicto que ya no es el que hay. Queda escrito aquí para que
nadie lo lea como un efecto no deseado de F-032.

---

## 5 · El archivo, y el riesgo del renombrado

**R24.** El sistema **no debe borrar ni renombrar nada** en SharePoint:
`ArchivoPort` no gana ninguna operación y el circuito sigue pudiendo solo crear
carpeta, buscar homónimo y subir reemplazando.

**R25.** SI un parte ya archivado con el nombre viejo —el que lleva el espacio
dentro del código— se volviera a archivar después del cambio, ENTONCES el
sistema subiría un fichero con el nombre nuevo y el viejo quedaría **huérfano
en la biblioteca**, porque el reemplazo solo alcanza al homónimo y la capa de
idempotencia por traza está inerte desde el endpoint (§0.8). Es un **riesgo
asumido y medido**, no un descuido: `design.md` §6 explica por qué no se
arregla aquí.

**R26.** MIENTRAS no se haya ejecutado la **medición previa** —la consulta de
solo lectura de `design.md` §6.3, que lista los partes archivados cuyos códigos
guardados llevan algún blanco— con resultado conocido y anotado, el cambio
**no se despliega**. La medición va **antes** del despliegue porque nuestra
traza es el único sitio donde está escrito el nombre viejo: re-archivar lo
pisa (`postventa.archivos.nombre_fichero`). Verificación **MANUAL (humano)**.

**R27.** SI la medición devuelve alguna fila, ENTONCES ese parte **no se
re-archiva desde el circuito**: se anota y lo decide una persona, que es quien
puede mirar la biblioteca y quitar el fichero viejo a mano.

---

## 6 · La tabla de casos, y el alcance cerrado

**R28.** El sistema debe tratar como **el mismo código** todas las formas de la
tabla de `design.md` §5, que amplía la de F-028 con: espacio dentro de un tramo
(`RS 26.09/0178`, **el caso real del 2026-09-17**), varios espacios seguidos
dentro del tramo, espacio en el código de obra (`06 26`), tabulador, espacio no
separable y las seis formas que F-028 ya fijaba. Todas tienen que dar el mismo
código para el ERP y el mismo nombre de fichero.

**R29.** El sistema no debe cambiar **ninguna clave del contrato HTTP** ni un
fichero de `services/postventa-front/`: el front sigue mandando lo que manda y
recibiendo lo que recibe. Lo único que cambia para quien mire la pantalla es
que el código que se le enseña ya viene limpio.

---

## 7 · Trazabilidad requisito → test

| Requisito | Test |
|---|---|
| R1, R2 | `test_f032_r1_normalizar_elimina_todos_los_espacios`, `test_f032_r2_los_blancos_raros_tambien` |
| R3 | `test_f032_r3_los_ceros_a_la_izquierda_siguen_intactos` |
| R4 | `test_f032_r4_un_codigo_vacio_sigue_dando_cadena_vacia` |
| R5 | `test_f032_r5_el_codigo_de_obra_no_se_parte_por_sus_guiones` |
| R6 | `test_f032_r6_el_saneo_vive_en_normalizar_codigo` |
| R7 | `test_f032_r7_todas_las_formas_dan_el_mismo_codigo_para_el_erp` |
| R8 | `test_f032_r8_todas_las_formas_dan_el_mismo_nombre_de_fichero` |
| R9 | `test_f032_r9_el_codigo_de_obra_con_espacios_no_cambia_la_carpeta` |
| R10 | `test_f032_r10_las_dos_conversiones_siguen_siendo_idempotentes` |
| R11 | `test_f032_r11_la_extraccion_sanea_los_dos_codigos` |
| R12 | `test_f032_r12_el_cuerpo_http_sanea_los_dos_codigos` |
| R13 | `test_f032_r13_lo_que_se_guarda_no_lleva_espacios` (sobre `sentencias.upsert_parte`, con dobles) |
| R14 | `test_f032_r14_los_otros_siete_campos_no_se_tocan` |
| R15 | `test_f032_r15_el_saneo_deja_aviso` |
| R16 | `test_f032_r16_ausente_sigue_ausente` |
| R17, R21 | `test_f032_r17_la_huella_no_se_toca` (AST sobre `aprobacion.py`) + los de F-028 que siguen verdes |
| R18 | `test_f028_r50_la_huella_sigue_valiendo_lo_que_valia` (sin cambios, se ejecuta) |
| R19 | `test_f032_r19_la_huella_de_los_codigos_con_espacio_interior_no_se_mueve` |
| R20 | `test_f032_r20_un_parte_aprobado_antes_del_cambio_sigue_aprobado` |
| R22 | `test_f032_r22_no_hay_sql_de_migracion` (el árbol no gana ningún `UPDATE`) |
| R23 | `test_f032_r23_reprocesar_limpia_y_caduca_la_aprobacion` |
| R24 | `test_f032_r24_el_puerto_de_archivo_no_gana_borrado_ni_renombrado` |
| R25, R26, R27 | **MANUAL (humano)**: `design.md` §6.3, consulta de solo lectura |
| R28 | `test_f032_r28_*`, la tabla entera parametrizada |
| R29 | `test_f032_r29_el_contrato_http_no_cambia` + `services/postventa-front/` sin diff |

---

## 8 · Decisiones y alternativas descartadas

**D1 · Alinear `_normalizar` (la huella) con `normalizar_codigo`. DESCARTADA
por el humano el 2026-09-17.** Sería «lo coherente» y es exactamente lo que no
se puede hacer: las huellas guardadas se calcularon con la regla vieja y las
recompuestas usarían la nueva, así que **todo parte aprobado cuyo código u
observaciones lleven un espacio volvería a `pendiente`**, y el trabajo de
revisión de una persona se perdería sin que nadie lo decidiera. Rompe R50 y R51
de F-028 —con centinela— y el §8 de `design.md` de F-030. Si algún día se
quieren alinear: **feature propia, con migración** que recalcule y reescriba las
huellas del histórico en la misma transacción, y con el humano delante.

**D2 · Limpiar con un `UPDATE` las filas ya guardadas. DESCARTADA.** Suena
inofensivo y no lo es: los dos códigos que entran en la huella se leen de
`postventa.partes` (§0.7), así que un `UPDATE` es D1 por la puerta de atrás.
Lo que sí limpia una fila es reprocesar el parte, y eso caduca su aprobación
**a la vista** (R23).

**D3 · Tratar como espacio todo lo invisible (incluido el `U+200B`, espacio de
ancho cero). DESCARTADA en esta feature, y declarada.** `str.split()` no lo
considera blanco —**[MEDIDO]**: `'06​26'.split()` devuelve `['06​26']`—
así que un código con un `U+200B` sobreviviría al saneo y produciría un nombre
de fichero con un carácter invisible que `nombre_admisible` acepta. No se ha
visto nunca, y ampliar el criterio a «todo lo que no se ve» es otra discusión
—hay caracteres invisibles que sí significan algo—. Queda escrito para que la
decisión se tome mirándola, no por olvido.

**D4 · Que el circuito borre o renombre el fichero viejo en SharePoint.
DESCARTADA.** Exigiría darle al servicio la capacidad de **borrar** en el
archivo de Posventa. Un fichero de más lo ve una persona; un borrado
equivocado no lo ve nadie, y el archivo de Posventa se consulta a mano. El
fichero huérfano se reconcilia con la medición del §6.3 y con la mano de quien
lo archivó.

**D5 · Arreglarlo en el prompt.** Pedirle al modelo que no meta espacios no es
una garantía: la lectura no es determinista y el mismo papel se lee distinto
dos veces. Además dejaría vivo el caso de la persona que teclea un espacio en
el front. Se puede añadir al prompt como **ayuda** en otra feature; no sustituye
a R1 ni a R11.

**D6 · Cablear la traza previa del archivo para que la capa L1 corte de verdad
(§0.8). DESCARTADA aquí, propuesta fuera.** Es lo único que haría **imposible**
el duplicado, y es más feature de lo que parece: tocar `SituacionParte`, el
puerto de persistencia, su adaptador, una sentencia y su mapeo. Ampliar F-032
hasta ahí reabre el alcance que fijó el humano y mete esta feature en el
terreno de F-019/F-031. Se declara como **defecto D-A1** en `design.md` §6.2 y
se propone al humano como feature propia.

---

## 9 · Relación con otras features

- **F-028** deja aquí sus R44–R51 intactos: esta feature **extiende** R44
  (eliminar también el espacio que no toca al separador) y **no toca** R50 ni
  R51, que son los que protegen la huella. Sus tests siguen verdes sin cambiar
  ni un aserto; el único test del árbol que cambia de expectativa es
  `test_f006_r8_los_espacios_interiores_se_colapsan_a_uno`, y es el que
  codifica la regla que esta feature sustituye.
- **F-030** dejó escrito que las puertas juzgan **el veredicto guardado**. F-032
  no lo toca: se limita a que lo guardado esté limpio desde que nace.
- **F-031** (*el nombrado del fichero archivado sale del cuerpo, no de lo
  persistido*) **no se sustituye ni se invade**. Lo que F-032 hace es allanarle
  el terreno: cuando los dos códigos nacen saneados y las dos puntas comparten
  la misma normalización, «el del cuerpo» y «el de la base» dejan de poder
  divergir **por espacios**, que era una de las formas en que podían diferir.
  Las otras —que alguien corrija el código a mano y esa corrección no se
  guarde antes de archivar— siguen enteras y son suyas.
