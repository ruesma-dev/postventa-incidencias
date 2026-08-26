<!-- progress/review_F-008.md -->
# Review de F-008 · Modelo de posventa en Sigrid: confirmar contra el ERP

> `reviewer` · 2026-08-26 · rama `feature/F-008-modelo-sigrid`
> (worktree `agent-a31450ce7b55c4c8d`, HEAD `e12cbce`)
> Diff revisado: `git diff dev...HEAD` — 7 ficheros, 697 inserciones.

## Veredicto

**CAMBIOS SOLICITADOS (2)**

Dos correcciones, las dos en el entregable, las dos de un párrafo. **Nada de
lo revisado está mal hecho**: el trabajo es sólido, la separación entre
verificado y deducido es ejemplar y el arreglo del guardián cierra un hueco
real. Se rechaza porque el entregable es *la* feature, y contiene (1) una cifra
que su propia tabla contradice dos secciones después y (2) un hallazgo
verificado que se quedó en `progress/` en vez de en `docs/referencia/`, que es
justo lo que pide el `acceptance` nº 5. Ver §4.

---

## 1 · Nivel de rigor y puertas que exige

Declarado en `harness/features.json`: **`rigor: "documental"`**, `sdd: false`.
Valor válido de `harness/rigor.json`. No se aplica el `critico` por omisión
porque **sí** está declarado.

Lo que `documental` exige, según la tabla de `CHECKPOINTS.md` y los valores de
`harness/rigor.json` (`fase_red: false`, `cobertura: false`, `mutacion: false`,
`supervivientes_maximos: null`):

| Puerta | ¿Exigida? | Justificación del N/A |
|---|---|---|
| C1, C2, C3, C3 bis, C5 | **Sí** | — |
| C4 (tests trazables por requisito) | **N/A** | La tabla de niveles de `CHECKPOINTS.md` deja C4 fuera de `documental`: el entregable es un documento, no hay código de producción al que trazar un `test_f008_rN_*`. |
| **Fase RED** | **N/A** | `fase_red: false` en el nivel `documental`. Aun así, el único cambio de código de la rama **sí llegó con su fallo delante** (§3.3). |
| **Cobertura** | **N/A** | `cobertura: false`. Y lo imprime el propio portero: `PUERTA COBERTURA: N/A (F-008 es de nivel documental: no exige cobertura)`. N/A con motivo impreso, que es lo que pide C4 bis. |
| **Mutación** | **N/A** | `mutacion: false`. No existe `progress/mutacion_F-008.md` **y no debe existir**: mutar el único fichero de código tocado —un test— no mide nada, porque los mutantes de un test no los mata nadie. No procede recálculo de alcance ni prueba de control de «cero mutantes». |
| C4 ter (rutas sensibles) | **N/A** | No existe `harness/rutas_sensibles.json`. El propio checkpoint dice que sin declaración el bloque es N/A y **no hay nada que justificar**. |

`sdd: false`: no hay `specs/F-008-*/`. El contrato son los seis `acceptance` de
la ficha, y todo lo que dependa de `tasks.md` es N/A por la nota de cabecera de
`CHECKPOINTS.md`.

---

## 2 · Los seis `acceptance`, uno a uno

Verificados contra el documento entregado, no contra el informe.

| # | Criterio | Estado | Dónde queda y qué comprobé |
|---|---|---|---|
| 1 | `con.tip` de la reclamación y estados de `conest`, con el de cierre identificado | **CUMPLE** | §1 del entregable: `con.tip = 708`, extensión `rcp`, y el catálogo `1/SAT`, `3/PTE`, `5/TER`, `7/NPR`, **`9/CER` CERRADA**. Además avisa de que el 9 es configurable y hay que resolverlo por `cod`. **Comprobación de coherencia interna que hice yo**: los cinco recuentos de la tabla (1.989+1.011+3.757+656+14.141) suman **exactamente 21.554**, el total de `rcp` que declara la línea anterior. Cuadra. |
| 2 | Qué filas toca «Cerrar parte» comparando cerrada y pendiente, y en qué se diferencia de RPV | **CUMPLE** | §2.1 (pareja de la misma obra, columna a columna) y §2.2 (el mismo resultado sobre las 4.761 creadas desde 2025: 85+839+1.474+258+2.105 = **4.761**, cuadra). §3 para RPV. La respuesta —`con.est` y una fila en `dbo.log`, nada más— está sostenida por dos poblaciones distintas, no por un caso. Y §2.4 añade lo que no se pedía y es lo que más vale: la fila de auditoría que un `UPDATE` directo se dejaría. |
| 3 | Si un gráfico puede ser una URL a SharePoint | **CUMPLE** | §4.3. Es una respuesta **negativa y honesta**: 0 en `cod`, 0 en `tex`, 0 menciones a `sharepoint`, y la única coincidencia en `nom` desmontada como falso positivo. Marca lo que sigue siendo deducción con un **«Deducido, no verificado»** literal y con un «No se debe diseñar F-009 sobre esta suposición». Un «no se puede afirmar, y aquí está la evidencia de por qué» **es** una respuesta escrita, y es la única que se podía dar sin escribir en el ERP. |
| 4 | Ni una escritura contra Sigrid | **CUMPLE** | Ver §3.1, con la cadena de evidencia que comprobé. |
| 5 | `docs/referencia/` recoge lo nuevo; lo de `azure-apps` se enlaza, no se copia | **CUMPLE A MEDIAS** | La segunda mitad, **impecable**: la tabla «Qué no está aquí» manda a `sigrid_tablas.md`, `sigrid_api.md` y §9.1–9.3, y **comprobé que las secciones citadas existen y dicen lo que se les atribuye** (`sigrid_api.md` §2.1 «`ruesma_rep` **nunca** se escribe», §7.2 «la escritura está apagada por defecto», §9.3 el join de `conest`). Comprobé también que **no hay copia**: `sigrid_api.md` §9.2 **no** lista el tipo 708, así que documentarlo aquí es aportar, no duplicar. La primera mitad falla en un punto: el hallazgo del `con.cod` no llegó al documento → **cambio requerido nº 2**. |
| 6 | `bash harness/init.sh` en verde | **CUMPLE** | Ejecutado por mí, tal cual, en el worktree. Exit 0, `ENTORNO LISTO`. 17 tests del arnés, servicio `api` y servicio `front` en verde. Único aviso: `ruff: 58` marcado como deuda previa, que no bloquea y no es de esta rama. |

---

## 3 · Verificaciones que hice yo, no leyendo el informe

### 3.1 · «Ni una escritura»: la cadena de evidencia

No se puede auditar a posteriori un `SELECT` que ya ocurrió, así que en vez de
creerme la frase busqué evidencia estructural. Cuatro eslabones, y los cuatro
aguantan:

1. **En el diff no hay ni una escritura.** Barrí `git diff dev...HEAD` con
   `INSERT INTO|UPDATE .* SET|DELETE FROM|/api/sql/write|documents/write`.
   Único acierto: `impl_F-008.md:633`, y es la **recomendación** de lo que
   escribiría F-009, no algo ejecutado.
2. **No hay artefacto ejecutable en la rama.** Los dos ficheros añadidos son
   `docs/referencia/03_modelo_posventa_sigrid.md` y `progress/impl_F-008.md`.
   Ningún script, ninguna consulta versionada. El script de trabajo se quedó en
   el *scratchpad*, que es donde debía quedarse.
3. **El camino usado no puede escribir.** `sigrid_api.md:114` y `:323-324`
   confirman lo que declara el documento: la lectura va con `ro_user`, que
   **no tiene permisos de escritura en el propio SQL Server**. No es una
   promesa del implementer, es una propiedad del usuario SQL.
4. **La escritura de la pasarela va apagada por defecto** (`sigrid_api.md`
   §7.2), y el propio documento lo lista en §5.6 como algo *no comprobado*
   porque comprobarlo sería escribir. Esa autolimitación es coherente con el
   resto.

**No ejecuté ninguna consulta contra el ERP para verificarlo**: sería
exactamente la escritura de riesgo que el criterio prohíbe, en el sentido de
tocar producción sin necesidad. La cadena estructural es suficiente.

### 3.2 · Barrido de datos sensibles (obligatorio de C3 bis, lo ejecuta el reviewer)

Ejecutado por mí sobre los cuatro ficheros de texto tocados
—`docs/referencia/03_modelo_posventa_sigrid.md`, `docs/referencia/README.md`,
`progress/impl_F-008.md`, `progress/current.md`—. **Patrones usados, literales**:

| Qué busqué | Patrón | Resultado |
|---|---|---|
| Correos | `[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}` | **0** |
| IPs | `\b([0-9]{1,3}\.){3}[0-9]{1,3}\b` | **0** |
| GUID (tenant, suscripción, sitio, app) | `\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b` (sin distinguir caja) | **0** |
| URLs | `https?://` seguido de cualquier cosa que no sea espacio, paréntesis ni acento grave | **0** |
| Recursos y hosts | `azurewebsites\|blob\.core\|\.database\.windows\|vault\.azure\|onmicrosoft\|sharepoint\.com\|ruesma\.es\|subscription\|tenant` | **0** |
| Credenciales | `password\|passwd\|contrase\|secret\|api[_-]?key\|token\|bearer\|pwd=\|Server=\|Data Source=\|connectionstring` | 6 aciertos, **todos la palabra en prosa**, ningún valor: «guardián de secretos», «los once secretos del script», «`Key Vault Secrets Officer`». Ninguno en el entregable. |
| DNI | `\b[0-9]{8}[- ]?[A-Za-z]\b` | **0** |

**El login redactado, comprobado en el documento y no en el informe.** El
informe declara que `gra.cod` llevaba un login y va como `<usuario>`. Está así
en el entregable, §4.2: ``gra.cod`` → `202608181140392614.<usuario>`, y la
cabecera lo anota («**Redactado**: los logins de usuario de Sigrid aparecen
como `<usuario>`»). Es la única aparición: no hay ningún otro login en el
documento. La fila de `dbo.log` de §2.4 usa el mismo marcador.

**Datos personales**: cero. El documento no trae ni un nombre de cliente, ni un
DNI, ni un propietario. Las columnas que apuntan a personas (`rcp.cliide`,
`rcp.recide`, `rcp.cntide`) se consultaron **solo por si están rellenas**, que
es la forma correcta de hacerlo. `RS26.08/0123` y la obra `0677, Mirasierra`
son códigos internos, no datos de persona, y `RS26.08/0123` **ya estaba** en
`docs/referencia/01_cierre_incidencia_sigrid.md` (líneas 19, 41, 53, 58) desde
antes de esta rama: no lo introduce F-008.

**Originales sin versionar**: `git log --all --diff-filter=A` no devuelve ni un
`.pdf`, `.docx`, `.xlsx`, `.pptx` ni imagen en **ningún** commit de **ninguna**
rama. Y `git log --diff-filter=A dev..HEAD` confirma que esta rama solo añade
los dos `.md` citados.

### 3.3 · El arreglo del guardián: ¿cierra el hueco o baja el listón?

**Cierra el hueco, y no baja ningún listón.** Lo comprobé ejecutando, no
leyendo.

Reproduje el filtro **viejo** (comparar los excluidos contra las `parts`
**absolutas**) sobre la raíz de este worktree:

```
RAIZ = ...\.claude\worktrees\agent-a31450ce7b55c4c8d
con el filtro viejo, barridos = 0
```

**Cero ficheros.** El guardián de secretos estaba apagado del todo al ejecutarse
desde un worktree, exactamente como dice el informe. Con el filtro nuevo, sobre
la misma raíz:

```
barridos = 275
  cubre: docs/referencia/03_modelo_posventa_sigrid.md
  cubre: progress/impl_F-008.md
  ficheros bajo worktrees dentro del barrido: []
```

Es decir: **el guardián ahora sí mira los dos ficheros que esta misma feature
añade**. Y desde el árbol principal la exclusión que se puso originalmente
sigue viva:

```
RAIZ principal = C:\Users\pgris\PycharmProjects\postventa-incidencias
barridos = 273
alguno en worktrees? []
```

Ninguna copia de subagente se barre dos veces. El arreglo hace lo que promete
en las dos direcciones.

**Y no se ha relajado nada para que pase.** Comprobado línea a línea:

- El umbral de `test_..._mira_ficheros_de_verdad` sigue en `>= 60` (con 275
  reales, sobradísimo). No se tocó.
- `GUID_TOLERADO_POR_FICHERO` sigue con **3** entradas y un GUID cada una, y su
  test `..._la_tolerancia_del_barrido_no_crece_sin_que_se_vea` sigue fijando
  `len(...) == 3`. No se tocó.
- `PATRON_GUID` se sigue **importando** de la otra mitad, no copiando. No se
  tocó.
- `DIRECTORIOS_NO_VERSIONADOS`, `EXTENSIONES` y `FICHEROS_NO_VERSIONADOS`:
  idénticos. **No se quitó `worktrees` de la lista**, que era la salida fácil y
  habría desprotegido el árbol principal.

El cambio es el mínimo posible: `fichero.parts` → `fichero.relative_to(raiz).parts`,
más pasar `raiz` desde `_ficheros_barridos`. Los 29 tests del fichero, en verde
(`29 passed in 2.83s`). El docstring nuevo explica el porqué y deja constancia
de que fue el propio control positivo quien lo cazó, que es la parte que vale
para el siguiente.

**Una observación de diseño, no bloqueante**: `_es_barrido` llama a
`relative_to(raiz)`, que lanza `ValueError` si el fichero no cuelga de `raiz`.
Hoy es imposible porque el único llamante los saca de `raiz.rglob("*")`, pero
la firma pública ya no tolera cualquier `Path`. No pido cambiarlo; lo dejo
anotado por si algún día se llama desde otro sitio.

### 3.4 · Coherencia entre el informe y el entregable

Comprobé los números del informe contra el documento y contra sí mismos:

- Los 21 hallazgos de la tabla del informe están sostenidos por el documento,
  **salvo el nº 21** (ver cambio requerido nº 2).
- `23.063 - 21.554 = 1.509`, el hueco de conceptos sin fila en `rcp` que declara
  §1. Cuadra.
- §3: «Cerrar parte» de 2023 a 2026 → `241+18+1.968+138 = 2.365`, y con gráfico
  lo mismo. La afirmación «2.365 cierres, 2.365 con gráfico, cero excepciones»
  cuadra con su propia tabla.
- §4.1: el reparto de `vin` (282.405+154+38+1+1) suma **282.599**, el total de
  `ruesma.gra`. Cuadra.
- §4.2: 13.399 de 13.450 = **99,62 %**. El «99,6 %» está bien redondeado.
- Las 6.843 filas de log de «Cerrar parte» (§2.4) frente a las 6.590 que suma
  §3 **no** es una contradicción: §3 cuenta reclamaciones «que **hoy** están en
  `CER`» y el log cuenta ejecuciones, que incluyen las 81 deshechas y las que
  cambiaron de estado después. La diferencia está explicada por el propio
  encabezado de la tabla.
- **La que no cuadra** es §2.5 → cambio requerido nº 1.

La distinción verificado / deducido está bien hecha y es el mayor mérito del
documento: §4.3 marca su deducción como tal y §5 lista seis cosas no
confirmadas, incluida la más incómoda («qué hace el proceso **por dentro**: se
ha medido su efecto observable, no leído su código»). Eso es exactamente lo que
necesita quien vaya a especificar F-009.

---

## 4 · Cambios requeridos

Los dos en `docs/referencia/03_modelo_posventa_sigrid.md`. Ninguno pide volver
al ERP: se resuelven con lo que ya está medido.

### 1. §2.5, línea 154: la cifra «2.105» no cuadra con la tabla de §3

Dice, literal:

> `De los **2.105** cierres con «Cerrar parte» desde 2025, **29 se hicieron
> directamente desde PENDIENTE**`

Pero la tabla de §3 (líneas 179–180) da, para «Cerrar parte», **1.968 en 2025 y
138 en 2026: 2.106**, no 2.105. Y 2.105 es exactamente el número que la tabla
de §2.2 (línea 97) da para otra población distinta: las reclamaciones
**creadas** desde 2025 que hoy están en `CER` — que no son todas «Cerrar
parte», porque §3 muestra 32 cierres por RPV en 2025.

O sea: o el número está tomado de la población equivocada, o la etiqueta
describe una población que no es la suya. Con un documento cuyo valor entero es
«esto se midió», un lector que sume dos filas de la tabla siguiente y le salga
otra cosa deja de fiarse del resto.

**Qué hacer**: fijar la población del 2.105 (¿creadas desde 2025 y hoy en
`CER`, o cerradas con «Cerrar parte» en 2025–2026?) y escribirla explícita en
la frase. Si son dos poblaciones distintas, decirlo. El hallazgo —29 cierres
directos desde PENDIENTE— no está en cuestión; lo que hay que arreglar es el
denominador al que se atribuye.

**De paso, la misma corrección en dos sitios más**, porque es el mismo
descuido:

- Líneas 201–203, «Cerrar Preventas»: dice **4.899 ejecuciones** y acto seguido
  **«3 de 4.892»**. Siete de diferencia sin explicar. Cuadrarlo o declarar que
  son dos poblaciones (ejecuciones frente a reclamaciones distintas).
- `progress/impl_F-008.md`, hallazgos **#10** y **#12**, que repiten el «2.105
  cierres desde 2025». Si se corrige el documento y no el informe, quedan
  contándose cosas distintas.

### 2. El hallazgo del `con.cod` se quedó en `progress/`, y `acceptance` nº 5 lo pide en `docs/referencia/`

`progress/impl_F-008.md:82` recoge, como hallazgo **verificado con datos**:

> `con.cod` identifica la reclamación de forma única y global: 23.063 conceptos
> `tip=708`, 23.063 códigos distintos. El formato es `RS{AA}.{MM}/{NNNN}` y
> **no codifica la obra**.

**No está en el documento entregado.** Lo comprobé buscando `con.cod`,
`23.063`, `RS{AA}` y «única» en los 329 renglones: el documento solo menciona
el código de pasada, como ejemplo dentro de la fila de `dbo.log` (§2.4).

Importa por dos razones concretas:

1. **Es el criterio nº 5 del contrato.** «`docs/referencia/` recoge lo nuevo».
   Esto es nuevo, está verificado contra el ERP y no está recogido.
2. **Es la clave de localización de F-009**, que es de rigor `critico` y
   escribe en producción. El propio informe lo usa así en §6.4.5. Quien
   redacte esa spec leerá `docs/referencia/03`, no un informe de sesión ajeno:
   el `README.md` de `docs/referencia/` dice en su tabla «Qué va aquí y qué no»
   que `progress/` es para **notas de trabajo de una sesión**, no para
   conocimiento de referencia. Un dato de referencia que solo vive en
   `progress/` está, a efectos prácticos, perdido.

**Qué hacer**: un párrafo en §1 (o una subsección §1.1) con la unicidad, el
recuento que la sostiene, el formato y el «no codifica la obra». Y conviene
enlazar desde ahí la trampa barra/guion, que **ya está documentada** en
`docs/referencia/01_cierre_incidencia_sigrid.md:58` — no hay que reescribirla,
solo que se encuentre desde aquí.

---

## 5 · CHECKPOINTS.md, recorrido completo

### C1 — El arnés está completo y en verde

- **[x]** `bash harness/init.sh` termina con exit 0. Ejecutado por mí en el
  worktree, sin pipes ni decoración: `ENTORNO LISTO. Puedes trabajar.`
- **[x]** Existen los nueve ficheros obligatorios. El propio portero los lista
  uno a uno en `[OK]`.

### C2 — El estado es coherente

- **[x]** Una sola feature `in_progress`: F-008. Lo valida `init.sh`
  (`en curso: ['F-008']`).
- **[x]** Rama actual `feature/F-008-modelo-sigrid`, nunca `main`.
- **[x]** `progress/current.md` lleva al frente el bloque de F-008, fechado.
  Sigue siendo memoria apilada y declarada como tal, que es como este
  repositorio la viene usando y como la aceptó `review4_F-010.md` §C2. No
  introduce residuo nuevo: los bloques anteriores vinieron heredados de `dev`
  por el merge `6963a79`.
- **[x]** Las ocho features `done` tienen resumen en `history.md`; comprobé la
  última, F-010, en `progress/history.md:466`.

### C3 — El código respeta arquitectura y convenciones

- **[x]** **Hexagonal**: N/A material, y por eso no lo marco N/A a secas — la
  rama **no toca producción**. Los únicos ficheros de código son un test del
  servicio `api`; no hay dominio, ni puertos, ni adaptadores implicados, así
  que no hay frontera que cruzar ni que pueda haberse cruzado mal.
- **[x]** Primera línea con la ruta relativa: `# services/postventa-api/tests/test_f006_repo_sin_identificadores.py`
  en el test, `<!-- docs/referencia/03_modelo_posventa_sigrid.md -->` en el
  entregable y `<!-- progress/impl_F-008.md -->` en el informe. Los tres.
- **[x]** Sin `print()` de debug, sin TODO huérfanos, **sin secretos
  hardcodeados** (§3.2), sin dependencias nuevas.
- **[x]** La unidad de trabajo es el **parte**: el documento razona por
  reclamación (`con.ide`, `con.cod`), nunca por PDF.
- **[x]** **Nada se cierra sin validar**, y aquí es más fuerte que un checkbox:
  la feature entera fue de solo lectura (§3.1), y su recomendación para F-009
  (§6.2 del informe) es **negarse a cerrar sin gráfico**, replicando por
  nuestro lado el control del ERP en vez de esquivarlo. Es la lectura correcta
  del checkpoint.
- **[x]** Lo manuscrito y la firma: N/A **por materia** — esta feature no toca
  extracción ni firma, no hay código de validación en el diff. Nada en el
  documento contradice esas reglas.
- **[x]** «Firmado no es conforme»: N/A por lo mismo, y el documento lo
  respeta al remitir a `02_parte_de_trabajo.md` desde el índice.
- **[x]** Reprocesar no duplica: N/A por materia, no hay ingesta en el diff.
- **[x]** **Nada hardcodea un número de estado.** Este sí aplica de lleno, y es
  donde el documento se luce: §1 escribe el `9` pero **avisa en negrita** de
  que es configurable por instalación y de que se resuelve por `conest.cod`; y
  §6.4.1 del informe lo eleva a requisito de F-009, incluido el `tip`. El
  checkpoint sale reforzado de esta feature, no solo cumplido.
- **[x]** Ningún parte escaneado ni PDF con datos personales ha entrado en git.
  Comprobado con `git log --all --diff-filter=A`, no solo con el árbol: cero
  ficheros de ofimática o imagen en el historial de ninguna rama.

### C3 bis — Los documentos que entran de fuera son seguros

Aplica: la rama añade `docs/referencia/03_modelo_posventa_sigrid.md`.

- **[x]** Cabecera con **origen y fecha**: «Origen: consultas de solo lectura
  contra el ERP de producción, a través de `sigrid-api` (`POST /api/sql/read`),
  bases `ruesma` y `ruesma_rep`. Fecha de las consultas: 2026-08-25 (F-008)».
  Y algo que agradezco: declara explícitamente **por qué no hubo `markitdown`**
  —no hay original que convertir— en vez de dejar el hueco callado.
- **[x]** Los originales en PDF u ofimática **no están en git**, ni en el índice
  ni en el historial de ninguna rama. Comprobado a mano además del test
  automático.
- **[x]** **Barrido de datos sensibles ejecutado por mí**, con los patrones
  literales y el resultado en §3.2 de este informe. Cero hallazgos con valor.
- **[x]** Lo redactado está anotado en la cabecera («Redactado: los logins de
  usuario de Sigrid aparecen como `<usuario>`») **y** en la fila del índice de
  `docs/referencia/README.md`.

### C4 — La verificación es real

- **N/A justificado por el nivel.** La tabla de niveles de `CHECKPOINTS.md`
  deja C4 fuera de `documental`: exige «C1–C3, C3 bis y C5». No es una omisión
  ni una comodidad — el entregable es un documento de referencia, y no existe
  código de producción cuyo comportamiento pudiera trazar un `test_f008_rN_*`.
  El único fichero de código de la rama es un test, y ese test **sí** tiene su
  verificación: 29 casos en verde, comprobados por mí, más la comprobación
  empírica de §3.3.
- **[x]** Los unit tests no tocan red ni BBDD. Aplica al fichero modificado y
  se cumple: `_ficheros_barridos` recorre el sistema de ficheros local, y los
  controles negativos y positivos montan su árbol en `tmp_path`.
- **[x]** Las verificaciones `MANUAL (humano)` están listadas: cuatro, en §7
  del informe y resumidas en `progress/current.md` — el `tex` y el `usu` de la
  fila de log, si la escritura de `sigrid-api` está habilitada, y si merece la
  pena confirmar el gráfico-URL. Las cuatro son **decisiones**, correctamente
  identificadas como del humano y no del implementer.

### C4 bis — El rigor declarado se cumple

- **[x]** La feature declara `rigor: "documental"`, valor válido de
  `harness/rigor.json`. No hay omisión que castigar con el `critico` por
  defecto.
- **N/A justificado** · **Fase RED**: `fase_red: false` en `documental`. Y aun
  no siendo exigible, el único cambio de código **llegó con su fallo delante**,
  pegado literal en §5 del informe (`assert 0 >= 60`), con diagnóstico y
  arreglo. Es más de lo que el nivel pide.
- **N/A justificado** · **Cobertura**: `cobertura: false`, y el portero lo
  imprime con su motivo — `PUERTA COBERTURA: N/A (F-008 es de nivel
  documental: no exige cobertura)`. Que el motivo salga **impreso por
  `init.sh`** es justo la forma que C4 bis exige para este N/A.
- **N/A justificado** · **Mutación**: `mutacion: false`. No existe
  `progress/mutacion_F-008.md` y **es correcto que no exista**: el único
  fichero de código tocado es un test, y mutar un test no mide nada porque no
  hay nada que mate a sus mutantes. Por lo mismo **no procede** el recálculo
  independiente de alcance y mutantes, ni la regla de los 5 minutos, ni el
  coste por mutante, ni la prueba de control de «cero mutantes»: no hay campaña
  que verificar, y montar una sería teatro.
- **N/A justificado** · **Supervivientes**: sin campaña no hay supervivientes.
  `supervivientes_maximos: null` en este nivel.
- **[x]** El informe trae la sección **«Evidencias»** (§7), y la trae bien: en
  vez de omitirla por no aplicar tres de los cuatro números, **declara qué se
  midió y por qué el resto no aplica**. Tests: `api` 1.078 pasan / 13 saltados
  / 0 fallan, `front` 74 pasan. Tiempo de suite: 47,18 s y 3,16 s. Cobertura y
  mutación: N/A con motivo. Sin campaña, el nº de workers no procede. Añade
  además dos números propios de esta feature —~25 consultas, todas `SELECT`; la
  mayor devuelve 36 filas—, que es la evidencia que de verdad importa aquí.
- **[x]** Ningún punto de este bloque marcado N/A sin justificación escrita:
  los cinco de arriba la llevan.

### C4 ter — Verificaciones extra por rutas sensibles

- **N/A sin nada que justificar.** No existe `harness/rutas_sensibles.json`
  (solo el `.ejemplo.json`), y el propio checkpoint dice que sin esa
  declaración el bloque es N/A. `init.sh` no señaló ninguna ruta tocada.

### C5 — La sesión se cerró bien

- **N/A justificado** · `tasks.md`: F-008 es `sdd: false`, no hay
  `specs/F-008-*/`. Lo aplica la nota de cabecera de `CHECKPOINTS.md`. En su
  lugar rige el formato mínimo de commit `F-XXX: <descripción>`, y los dos
  commits de la rama lo cumplen: `F-008: el modelo de posventa en Sigrid,
  confirmado contra el ERP` (`2f44e37`) y `F-008: el barrido de identificadores
  filtra por ruta relativa, no absoluta` (`337701c`).
- **[x]** Sin ficheros temporales ni artefactos sin trackear. `git status`
  sale **limpio**. La unión de directorio al `.venv` que el implementer montó
  para poder ejecutar la suite no toca ningún fichero versionado, como declara.
- **[x]** `features.json` refleja el estado real: F-008 `in_progress`, movida
  por el líder en `e12cbce` junto con el `BACKLOG.md` regenerado. Coherente con
  lo que valida `init.sh`.

---

## 6 · Observaciones no bloqueantes

No hace falta actuar sobre ellas para aprobar. Van por si el líder o el humano
quieren recogerlas.

1. **El bloque de F-008 en `current.md` se quedó desfasado.** Dice «`F-008`
   sigue **`pending`** a propósito», y el líder ya la movió a `in_progress` en
   `e12cbce`. Era cierto cuando se escribió; hoy contradice a `features.json`.
   Es del líder, no del implementer.
2. **Dos hallazgos son conocimiento del sistema origen, no de este proyecto.**
   La forma de la fila de `dbo.log` con sus códigos de `ope` (§2.4) y el
   emparejamiento `ruesma.gra` ↔ `ruesma_rep.gra` **por `cod`, no por `ide`**
   (§4.1) le sirven a cualquiera que consuma Sigrid, no solo a posventa. Según
   `CLAUDE.md`, «cuando necesites saber qué es una tabla o un campo de Sigrid,
   ve a `azure-apps/sigrid_tablas.md`». No lo pido como cambio —el `acceptance`
   nº 5 manda el entregable a `docs/referencia/`, y F-008 no altera lo que este
   proyecto expone ni consume, así que la regla de propiedad de `azure-apps` no
   se dispara—, pero **valdría la pena proponerle al dueño de `sigrid-api`**
   llevarse esos dos a `sigrid_tablas.md`. El de `gra` sobre todo: descubrir a
   base de tropiezos que los `ide` de las dos bases son espacios independientes
   es caro, y ya lo pagó esta feature.
3. **`_es_barrido` puede lanzar `ValueError`** si algún día se le pasa un
   fichero fuera de `raiz` (§3.3). Hoy es inalcanzable.
4. **La lección del worktree merece salir de aquí.** «Un guardián que filtra
   por ruta absoluta se apaga solo dentro de un worktree» no es específico de
   este repositorio: le pasará a cualquier proyecto que instale el arnés, tenga
   subagentes en worktrees y escriba un test que barra el árbol. El implementer
   decidió no portar el **fichero** a `arnes-base`, y hace bien —nació del
   hallazgo H1 de F-006—, pero la **lección** sí es transversal. Sugiero al
   humano valorar una nota en `arnes-base`.
5. **Lo mejor de esta feature no estaba en la ficha**, y conviene que no se
   pierda en la lectura rápida: que «Cerrar parte» **no toca `con.tiemod`** y
   que por tanto el log es el único rastro temporal de un cierre. Si F-009 hace
   solo el `UPDATE`, deja incidencias que para un auditor **nadie cerró nunca**.
   Está bien argumentado en §6.1 del informe y es la decisión de diseño más
   importante que hereda F-009.

---

## 7 · Automejora del protocolo (propuesta, no aplicada)

Dos huecos que este review ha destapado. **No los aplico**: los propongo para
que los apruebe el humano, y si se aceptan valen para cualquier proyecto, así
que tocaría portarlos a `arnes-base`.

1. **`CHECKPOINTS.md` no dice qué evidencia se le exige a una feature
   `documental`.** El protocolo del `reviewer` está afiladísimo para verificar
   campañas de mutación —recálculo independiente, regla de los 5 minutos,
   coste por mutante, prueba de control del cero— y **no dice ni una palabra**
   de cómo se verifica un entregable que es un documento. He tenido que
   inventarme el criterio sobre la marcha: cuadrar los totales de las tablas
   entre sí, comprobar que las secciones citadas de otro repositorio existen y
   dicen lo que se les atribuye, y contrastar cada hallazgo del informe contra
   el documento. Los tres controles han encontrado algo (§3.4 y los dos cambios
   requeridos). Propongo un bloque **C4 quater — El entregable documental es
   verificable**, con esos tres puntos y un cuarto: **ningún hallazgo verificado
   puede quedarse solo en `progress/`**, porque `progress/` es memoria de
   sesión y no documentación de referencia. Sin él, el `acceptance` «recoge lo
   nuevo» se comprueba a ojo.

2. **Nada obliga a ejecutar la suite desde fuera del árbol principal.** El
   guardián de R26 llevaba apagado dentro de los worktrees quien sabe cuánto, y
   lo cazó la casualidad de que esta feature se trabajara en uno. Cualquier test
   que compare rutas absolutas tiene el mismo defecto latente, y el arnés
   **trabaja en worktrees por diseño**. Propongo añadir a C1 una línea: cuando
   la feature se haya desarrollado en un worktree, el reviewer comprueba que
   los barridos del repositorio **encuentran ficheros** ahí, no solo que los
   tests pasan. Un `[OK]` que se obtiene por no mirar nada es la peor clase de
   verde, y es la que este arnés dice combatir en la nota de cabecera de
   `CHECKPOINTS.md`.

---

## 8 · Resumen para el líder

**CAMBIOS SOLICITADOS (2)**, los dos pequeños y los dos en el entregable:

1. `docs/referencia/03_modelo_posventa_sigrid.md:154` — la cifra «2.105 cierres
   con «Cerrar parte» desde 2025» no cuadra con la tabla de §3 (1.968+138 =
   2.106) y coincide con otra población distinta. Fijar y escribir la
   población. Arrastra las líneas 201–203 («4.899» frente a «4.892») y los
   hallazgos #10 y #12 de `progress/impl_F-008.md`.
2. `docs/referencia/03_modelo_posventa_sigrid.md` — falta el hallazgo del
   `con.cod` (único y global, `RS{AA}.{MM}/{NNNN}`, no codifica la obra), hoy
   solo en `progress/impl_F-008.md:82`. Es `acceptance` nº 5 y es la clave de
   localización de F-009, que es `critico`.

Ni una escritura contra Sigrid: **confirmado** por cuatro vías independientes.
Sin secretos ni datos personales: **confirmado** con barrido propio. El arreglo
del guardián: **cierra el hueco de verdad** (0 → 275 ficheros barridos) y **no
baja ningún listón**. El resto del trabajo, aprobado sin reservas.
