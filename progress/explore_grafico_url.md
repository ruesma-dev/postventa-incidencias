<!-- progress/explore_grafico_url.md -->
# La vía del gráfico por URL: ¿se puede asociar el parte a la reclamación sin tocar la base documental?

> Investigación **documental y de solo lectura**, 2026-09-02, rama
> `feature/F-009-cierre-sigrid`.
> **No se ha ejecutado ni una llamada** a Sigrid, `sigrid-api`, la Function
> desplegada, el PostgreSQL compartido ni SharePoint. Todo lo que hay aquí
> sale de leer ficheros: `azure-apps/sigrid_tablas.md`,
> `azure-apps/sigrid_api.md`, `azure-apps/postventa_incidencias.md`,
> `docs/referencia/01_cierre_incidencia_sigrid.md`,
> `docs/referencia/03_modelo_posventa_sigrid.md`,
> `specs/F-009-cierre-sigrid/design.md` y el código de
> `services/postventa-api/infrastructure/`.
> Sin secretos y sin datos personales.

---

## VEREDICTO

**DEPENDE — y depende de UNA cosa que no puede responder ningún documento: qué
escribe Sigrid cuando alguien usa «Asociar URL de Internet…».**

Tres frases que resumen todo lo demás:

1. **La premisa de la pregunta es FALSA.** Los 13.450 gráficos de posventa
   **no son de tipo URL**. `vin = 3` con `ima` vacío **no** significa «esto es
   un enlace»: significa «el binario está en la otra base». El 99,6 % de esos
   gráficos tiene su PDF real en `ruesma_rep.gra.ima`. Son binarios normales,
   almacenados fuera de la base de negocio. (§1)
2. **Lo demás de la vía URL sí encaja, y encaja bien.** El enlace `rcg` es
   idéntico venga el binario de donde venga (§2), y `sigrid-api` **sí**
   permitiría los dos `INSERT` sobre la base de negocio, con la misma técnica
   de reserva de `ide` que ya usa F-009 (§3). No hace falta el dueño de
   `sigrid-api` para nada.
3. **Pero no hay ni una fila en 282.599 de la que copiar el formato**, y en la
   documentación de Sigrid la tabla `gra` **ni siquiera tiene columna `url`**
   (§1.2). Inventarnos `vin` y el campo destino es adivinar cómo funciona por
   dentro un ERP de producción, y eso es exactamente lo que este proyecto
   lleva nueve features sin hacer.

**Quién lo resuelve, y es barato:** **Posventa** (Alicia Echevarría), en cinco
minutos, haciendo **una vez a mano** en la UI de Sigrid lo que ya sabe hacer:
sobre una reclamación de prueba, *Importa → **Asociar URL de Internet…*** con
una dirección cualquiera, y después *Procesos → 3. Cerrar parte*. Nosotros
solo leemos la fila resultante (§5, consulta Q10). Eso convierte las dos
incógnitas —cómo se guarda, y si «Cerrar parte» lo acepta— **de inferencia en
medida**, sin que escribamos nada.

Si esa prueba sale bien, la vía URL es viable y no depende de nadie fuera de
este proyecto. Si sale mal, F-012 (el binario) sigue siendo el único camino y
sigue bloqueada por el dueño de `sigrid-api`.

---

## 1 · Cómo se registra un gráfico por URL

### 1.1 · La pregunta más importante: ¿los 13.450 gráficos de posventa son de tipo URL?

**No. Son binarios corrientes, y el binario está en la base documental.**

Esto está **medido**, no inferido, y sale de
`docs/referencia/03_modelo_posventa_sigrid.md` §4.1 y §4.3 (F-008, consultas de
solo lectura contra el ERP el 2026-08-25):

| Evidencia | Dato | Qué prueba |
|---|---|---|
| De los **13.450** gráficos de reclamaciones, **13.399 (99,6 %)** tienen su binario en `ruesma_rep.gra` con el **mismo `cod`** | §4.1 | El fichero existe de verdad. Un gráfico-URL no tendría binario en ninguna parte |
| `ruesma_rep.gra`: **357.901 filas, ninguna con `ima` vacío** | §4.1 | La base documental es donde vive el byte, siempre |
| El gráfico de ejemplo: `ruesma_rep.gra.ima` = **242.534 bytes** | §4.2 | El PDF del parte firmado está ahí, con su tamaño real |
| `cod` que empiece por `http`: **0** sobre 282.599 filas | §4.3 | — |
| `tex` («Camino») que empiece por `http`: **0** | §4.3 | — |
| `nom` que empiece por `http`: **1**, y **no es un enlace** (es el nombre de una captura derivado de una dirección web, `.png`, con `vin = 3`) | §4.3 | — |
| Cualquier campo que mencione `sharepoint`: **0** | §4.3 | — |

La pantalla llama a `vin = 3` **`[INCRUSTADO EXTERNO]`**
(`docs/referencia/01_cierre_incidencia_sigrid.md`, «Lo que se rellena al
importar el gráfico»). «Externo» ahí no quiere decir «en Internet»: quiere
decir **fuera de la base de negocio**. Que `ruesma.gra.ima` esté vacío es la
consecuencia mecánica del diseño de dos bases que describe
`azure-apps/sigrid_api.md` §2, no la señal de un enlace.

> **Conclusión, y es un resultado negativo que vale:** el hecho que animaba la
> hipótesis —`ima` vacío con `vin = 3`— **no apunta a la vía URL**. Se explica
> entero por otra causa ya conocida. La vía URL sigue sin un solo precedente en
> esta instalación.

### 1.2 · Qué campos de `ruesma.gra` intervienen, y dónde iría la URL

Definición de la tabla en `azure-apps/sigrid_tablas.md`, página 247
(`grep -n "^| gra " sigrid_tablas.md` → línea 14408). Campos relevantes:

| Campo | Tipo | Descripción del diccionario | Qué lleva hoy en un parte firmado (§4.2 de `03_modelo_posventa_sigrid.md`) |
|---|---|---|---|
| `ide` | Entero | Identificador — **índice primario, único** | el del gráfico |
| `cod` | Texto 128 | Código | `202608181140392614.<usuario>` (sello `AAAAMMDDHHMMSS` + 4 dígitos + `.` + login) |
| `emp` | Entero | Empresa | la de la reclamación |
| `res` | Texto 48 | Resumen | `PARTE FIRMADO` ← **lo teclea Posventa** |
| `tex` | **Texto ilimitado** | **Camino** | **vacío** con `vin = 3` |
| `nom` | Texto **255** | Nombre | `RS26.08 - 0123 PARTE FIRMADO.pdf` |
| `nomori` | Texto 255 | Nombre original | — |
| `ima` | Binario ilimitado | Imagen | **vacío** con `vin = 3` |
| `gratipide` | Índice a `auxgra` | Clase de gráfico | `35` → `PV002` «POSTVENTA:Fotos Reparaciones» ← **lo elige Posventa** |
| **`vin`** | **Entero** | **«Vinculado»** | **`3`** |
| `usu` | Texto 128 | Usuario | el login |
| `fec` | Entero tipo fecha | Fecha | `20260818` |
| `cla`, `guid`, `texrev`, `numrev`, `estcon`, `ori`, `anx`, `mntide` | varios | Clave, id único, revisión, estado, procedencia, anexo, id en MNet | vacíos / sin medir |

**Dato duro y decisivo: `ruesma.gra` NO tiene columna `url` en el diccionario.**
Lo comprobé buscando `url` e `internet` en las 2 MB de `sigrid_tablas.md`
(`grep -n -i "internet\|\bURL\b"`): aparece en once tablas, y **`gra` no es
ninguna de ellas**. Los únicos campos de texto donde cabría una dirección son
`tex` («Camino», ilimitado), `nom` (255) y `cod` (128).

**Y aquí está el hallazgo que no estaba en ningún informe previo.** Tres tablas
de Sigrid son el mismo concepto que `gra` en otros módulos, y **las tres tienen
a la vez `gravin` («Vinculado») Y una columna `url` propia**:

| Tabla | Qué es | Línea | Campos gemelos | Su `url` |
|---|---|---|---|---|
| `catgra` | Catálogos: Gráficos | 4431 | `cod`, `res`, `granom`, `graima`, **`gravin`**, `gratam`, `tex`, `gratipide` | `url` — Texto de **255** |
| `ppogra` | Presupuestos: Gráficos | 18367 | idénticos | `url` — Texto de **255** |
| `dog` | Documento (gestión documental) | 9379 | `granom`, `graima`, **`gravin`**, `gratam`, `tex`, `gratipide`, **`codrep`** («Código repositorio externo») | `url` — **Texto ilimitado** («Url externo») |

Lectura de esto, y va marcada como **inferencia**:

- Que en tres tablas hermanas `gravin` y `url` **convivan** dice que en Sigrid
  «Vinculado» y «URL» son **dos cosas distintas**: `vin` describe *cómo se
  almacena el fichero*, y `url` es *un campo aparte*. Refuerza que `vin` no es
  el interruptor «esto es un enlace».
- `gra` es la tabla **más antigua** de la familia: le faltan `gratam` (Tamaño)
  y `url`, que las otras tres sí tienen. Es plausible que en `gra` la dirección
  no tenga campo propio y se guarde en `tex` o en `nom`.

**Dónde iría la URL, si es en `gra`.** Dos candidatos, y la evidencia se
reparte:

| Candidato | A favor | En contra |
|---|---|---|
| **`gra.nom`** | La ventana de gráficos llama a ese campo, literalmente, **«Archivo / Ubicación / URL»** (`01_cierre_incidencia_sigrid.md`), y `03_modelo_posventa_sigrid.md` §4.2 lo mapea a `gra.nom`. Es el único campo de la pantalla que menciona la palabra URL | **255 caracteres**. Una URL de SharePoint con la estructura de Posventa (`…/PARTES INCIDENCIAS/VILLA 05/PARTES FIRMADOS/…`) y `%20` por cada espacio se acerca peligrosamente a ese tope |
| **`gra.tex`** | «Camino», **texto ilimitado**, y está vacío justo en el modo `vin = 3`. Es lo que dedujo F-008 | Ningún campo de la pantalla se llama «Camino»; nadie ha visto nunca ese campo relleno |

> F-008 se inclinó por `tex`; la etiqueta de la pantalla apunta a `nom`.
> **Ninguna de las dos es un dato.** Las dos son inferencias, y la prueba
> manual de §5 las resuelve de golpe.

### 1.3 · Qué valor toma `vin`, y qué significan los otros

**No se sabe, y no está documentado en ninguna parte.** El diccionario declara
`vin` como «Vinculado, Entero» y **no enumera sus valores**; tampoco los
enumeran `sigrid_api.md` ni ningún documento de `azure-apps/`.

Lo único que hay es el **reparto medido** por F-008 sobre las 282.599 filas de
`ruesma.gra` (`03_modelo_posventa_sigrid.md` §4.1):

| `vin` | Filas | Qué se sabe | Cómo se sabe |
|---:|---:|---|---|
| `3` | 282.405 | «Incrustado externo»: `ima` y `tex` vacíos, binario en `ruesma_rep` | **Medido** + etiqueta de la pantalla |
| `2` | 154 | **Nada** | — |
| `0` | 38 | **Los únicos con binario dentro de `ruesma`** | **Medido** |
| `1` | **1** | **Nada. No inspeccionada** | — |
| `4` | **1** | **Nada. No inspeccionada** | — |

Suma 282.599 ✓ (verificado por el reviewer de F-008, `review_F-008.md` §205).

**Las dos filas de `vin = 1` y `vin = 4` son la pista más barata que existe**:
son dos filas, se leen con un `SELECT`, y si alguna resultara ser un enlace, la
pregunta estaría contestada sin molestar a nadie. Nadie las ha mirado. Consulta
Q3 preparada en §5.

**Pista adicional del diccionario, no explotada.** La tabla de configuración
`DB` (línea 60 de `sigrid_tablas.md`) tiene tres campos globales de gráficos:
`grapath` («Camino imágenes»), `gracopy` («**Camino copia/vincula**») y
`gramodo` («**Modo gráficos**»). Que exista un «camino copia/vincula» a nivel
de instalación sugiere que **`vin` distingue *copiar el fichero* de *vincularlo
por ruta*** — es decir, un eje de almacenamiento local, no de Internet.
**Inferencia, no dato.**

### 1.4 · Qué otros campos serían obligatorios

Nada en el diccionario marca campos `NOT NULL` (el autodocumentador no expone
esa propiedad), así que **«obligatorio» aquí significa «lo que Sigrid rellena
siempre», no una restricción comprobada**. Por comparación con la fila medida
(§4.2) haría falta, como mínimo: `ide`, `cod`, `emp`, `res`, `nom` (o `tex`),
`gratipide`, `vin`, `usu`, `fec`. Y en `rcg`: `ide`, `con`, `gra`, `pos`.

`auxgra` autoriza el destino: el tipo `PV002` (`ide = 35`) tiene
`tipaso = 'UPV,RCP,TAR'`, y **`RCP` es lo que permite colgar el documento de una
reclamación**; `tammax = 0` (sin límite) y `fecbaj = 0` (activo).

---

## 2 · ¿Se rellena `rcg` igual?

**Sí, y esto es lo más sólido del informe.** El vínculo gráfico↔reclamación es
**estructuralmente independiente** de dónde esté el binario.

`rcg` («Gráficos en conceptos», `sigrid_tablas.md` línea 19529) son cinco
columnas y ninguna dice nada del contenido:

| Campo | Tipo | Valor medido en los 13.450 enlaces (§4.2) |
|---|---|---|
| `ide` | Entero, índice primario único | el del enlace |
| `con` | Índice a `con` | la reclamación |
| `gra` | Índice a `gra` | el gráfico |
| `pos` | Entero | `64` en el ejemplo; **múltiplos de 64**, 52 posiciones distintas en uso |
| `cla` | Entero, «Clase de relación» | `0` en los 13.450 |

`rcg.gra` es un `ide` de `ruesma.gra`, y `ruesma.gra` es la tabla de
**metadatos**. La base documental **no aparece en el enlace**: la pareja
metadatos↔binario se localiza por `gra.cod`, no por el enlace
(`03_modelo_posventa_sigrid.md` §4.1). Un gráfico sin binario en `ruesma_rep`
se enlaza exactamente igual.

**Y ya existen 51 casos así.** 13.450 − 13.399 = **51 gráficos de posventa cuyo
`cod` no tiene pareja en la base documental**. Están enlazados en `rcg` y no
tienen fichero localizable. Nadie ha mirado en qué estado están sus
reclamaciones — y esa es la mejor evidencia empírica disponible para la
pregunta 4 (consulta Q5 en §5).

**Dos avisos sobre `rcg`, los dos verificables:**

1. **El diccionario está incompleto para esta instalación.**
   `03_modelo_posventa_sigrid.md` §4.2 midió `rcg.cla`, **`rcg.fecalt`** y
   **`rcg.feclee`**, y el bloque `rcg` de `sigrid_tablas.md` **solo declara
   cinco columnas: `ide`, `con`, `gra`, `pos`, `cla`**. `feclee` no aparece ni
   una vez en las 2 MB del diccionario. El PDF es de **v.20240618** y la
   instalación va por delante.
   > **Consecuencia directa y no menor: no se puede descartar que la `gra`
   > desplegada tenga hoy una columna `url` que el diccionario no recoge.** Es
   > una consulta de una línea (Q1) y cambiaría el diseño entero.
2. **`rcg.pos` no es siempre 64.** Son múltiplos de 64 y hay 52 valores
   distintos en uso: si la reclamación ya tuviera un gráfico, insertar otro con
   `pos = 64` podría chocar en el orden de la pantalla. Consulta Q6.

---

## 3 · ¿Permitiría `sigrid-api` esas escrituras?

**Sí, con la configuración desplegada de hoy, y sin tocar el otro repositorio.**

### 3.1 · Las listas blancas

Comprobado el 2026-08-26 al resolver D3 de F-009 (`design.md` §1, D3), leyendo
las *App Settings* de la Function App con `az functionapp config appsettings
list`, **solo lectura y sin ver ningún valor secreto**:

| Qué se preguntó | Respuesta |
|---|---|
| ¿`INSERT` permitido? | **Sí** |
| ¿`UPDATE` permitido? | **Sí** |
| ¿La base de negocio en `ALLOWED_WRITE_DATABASES`? | **Sí, y es la única** |
| ¿Credencial de escritura configurada? | Sí, por referencia a Key Vault |
| `REQUIRE_WHERE_ON_UPDATE_DELETE` | `true` (irrelevante aquí: son `INSERT`) |
| Tope de filas afectadas / sentencias por batch | **1.000 / 50** |

**`ALLOWED_WRITE_PREFIXES` son verbos SQL, no tablas.** `sigrid_api.md` §5.1
describe el `SqlWriteGuard` como «lista blanca estricta (`ALLOWED_WRITE_PREFIXES`);
prohíbe DDL/administración (`DROP/ALTER/CREATE/GRANT/EXEC/MERGE/…`); una
sentencia por elemento; `WHERE` obligatorio en UPDATE/DELETE», y describe el
guardián de lectura como «solo `SELECT` (según `ALLOWED_QUERY_PREFIXES`)». **No
hay ninguna lista blanca de tablas.** Por tanto `INSERT INTO dbo.gra` e
`INSERT INTO dbo.rcg` sobre la base de negocio **pasan el guardián igual que el
`INSERT INTO dbo.log` de F-009**.

**Y esto es lo que hace atractiva la vía URL:** los dos `INSERT` van **solo a
la base de negocio**. `ruesma_rep` no se toca. **El bloqueo de F-012 —que la
base documental esté fuera de `ALLOWED_WRITE_DATABASES` a propósito, y que
abrirla sea decisión del dueño de `sigrid-api` que afecta al ecosistema
entero— NO aplica aquí.** No hay que pedirle nada a nadie.

### 3.2 · Cómo se reservaría el `ide`: sí, la técnica de F-009 vale

`sigrid_api.md` §7.5 es tajante: **en Sigrid `ide` no es IDENTITY ni hay
SEQUENCE**; se calcula `MAX(ide)+1`, y **`sql/write` no protege esa reserva con
applock** (solo lo hacen los endpoints de dominio). F-009 lo resolvió
metiendo la reserva **dentro de la propia sentencia**, y el código está en
`services/postventa-api/infrastructure/sigrid/escrituras.py`
(`SQL_INSERT_LOG`, y `design.md` §7.3):

```sql
INSERT INTO dbo.log (ide, emp, ori, ope, fec, hor, usu, tab, tip, cod, res, tex, est)
SELECT (SELECT ISNULL(MAX(l.ide), 0) + 1 FROM dbo.log l WITH (UPDLOCK, HOLDLOCK)),
       c.emp, ?, ?, ?, ?, ?, 'con', c.tip, c.cod, c.res, ?, ?
FROM dbo.con c
WHERE c.ide = ? AND c.tip = ? AND c.est = ?
```

**La misma técnica vale para `gra` y para `rcg`**, y por los mismos motivos:
`UPDLOCK, HOLDLOCK` serializa la reserva; si aun así colisiona, la clave
primaria única rechaza el `INSERT`, `sql/write` **revierte todo el batch**
(§7.3) y el ERP queda sin ningún cambio. Y el mismo detalle fino se aplica: **el
filtro va en el `FROM`, nunca en un `WHERE EXISTS`**, porque un agregado sin
`GROUP BY` devuelve una fila aunque no case nada y `ISNULL(MAX(ide),0)+1`
valdría `1`, colisión garantizada contra la fila más antigua.

**Hay UNA diferencia, y es real:** `rcg.gra` necesita el `ide` que acaba de
tomar `gra`. `sql/write` manda las sentencias del batch como elementos
independientes —una sentencia por elemento (§5.1)—, así que **no se puede pasar
un valor de la sentencia 1 a la 2 con una variable T-SQL**. La salida limpia es
**volver a derivarlo por `gra.cod`**, que nosotros mismos generamos y que es
único por construcción (sello de tiempo + login):

```sql
-- sentencia 2, esquemática: el enlace deriva el ide del gráfico por su cod
INSERT INTO dbo.rcg (ide, con, gra, pos, cla)
SELECT (SELECT ISNULL(MAX(r.ide), 0) + 1 FROM dbo.rcg r WITH (UPDLOCK, HOLDLOCK)),
       ?, g.ide, ?, 0
FROM dbo.gra g
WHERE g.cod = ?
```

Con esto el batch entero (gráfico + enlace, o incluso gráfico + enlace + estado
+ log) va en **una transacción**, con `max_affected_rows` ajustado. Caben de
sobra en los topes: 50 sentencias y 1.000 filas.

**Dos cosas que NO están verificadas y que hay que decir:**

- **`gra.cod` no tiene índice único declarado** en el diccionario (solo `ide`
  es índice primario). Si hubiera `cod` repetidos, el `SELECT` de la sentencia
  2 devolvería más de una fila y crearía enlaces de más. Consulta Q8.
- **Que el `SqlWriteGuard` acepte un `INSERT … SELECT … WITH (UPDLOCK,
  HOLDLOCK)` sigue sin comprobarse contra la pasarela real.** F-009 lo dio por
  bueno leyendo la *configuración*, no probando el *comportamiento*, y a fecha
  de hoy **F-009 no ha ejecutado ni una escritura** (`progress/current.md`, el
  bloque 8 está escrito y sin ejecutar). Es un riesgo que la vía URL
  **hereda**, no uno nuevo: lo despeja la primera ejecución del bloque 8 de
  F-009.

---

## 4 · ¿Hay evidencia de que el ERP lo acepta como cierre válido?

**No hay evidencia ni a favor ni en contra. Y hay que separar dos preguntas que
se confunden.**

### 4.1 · Lo que dice el ERP

El mensaje de confirmación de *Procesos → 3. Cerrar parte* dice, literalmente
(`01_cierre_incidencia_sigrid.md`, «Lo más importante de todo»):

> **Comprobando:**
> - Que la Reclamación tenga asociado **algún gráfico o Doc. multimedia**.

Y los datos son consistentes con que **bloquea**: desde 2023, **2.365 cierres
con «Cerrar parte» y 2.365 con gráfico, cero excepciones**
(`03_modelo_posventa_sigrid.md` §3). La opción **6, «Cerrar parte sin archivo
(RPV)», existe justo para saltársela**, y es la prueba empírica: RPV sí deja
reclamaciones cerradas sin ningún gráfico, todos los años en que se usó.

**Lo que NO se sabe** (`§5.2` de ese mismo documento): **si la comprobación
bloquea o solo avisa**. No se ha provocado, porque provocarla es escribir.

### 4.2 · Búsqueda de reclamaciones cerradas con un gráfico de ese tipo

**Buscado y no encontrado, porque no existe la población.** F-008 barrió las
282.599 filas de `ruesma.gra` (§4.3) y **no hay ni un gráfico-URL en toda la
instalación**, ni cerrado ni abierto. La opción «Asociar URL de Internet…»
**nunca se ha usado aquí**. No hay precedente que consultar.

### 4.3 · El proxy que sí existe, y que nadie ha mirado

Lo más parecido a un gráfico-URL que hay en la base es **un gráfico sin
fichero real detrás**, y de esos hay **51**: los `13.450 − 13.399` gráficos de
posventa cuyo `cod` no tiene pareja en `ruesma_rep`. Si alguno de esos 51
cuelga de una reclamación en `CER` cerrada con «Cerrar parte», sabríamos que la
comprobación **mira el enlace `rcg`, no el contenido**. Es la consulta Q5, y es
de lectura.

### 4.4 · Y la pregunta que en realidad importa para nosotros

**Nuestro cierre no ejecuta «Cerrar parte».** F-009 hace un `UPDATE dbo.con SET
est` más la fila de `dbo.log`, y `design.md` §7.1 lo dice sin rodeos: **no hay
ningún `COUNT` sobre `rcg`, y es deliberado (R20)**; un control negativo
comprueba que ni la consulta ni el dominio mencionan `rcg` o `gra`. Así que
**la comprobación del ERP no nos afecta técnicamente**: nuestros cierres se
saltan el proceso nativo por completo — riesgo ya asumido y firmado en
`design.md` §2, «RIESGO ACEPTADO».

Lo que la vía URL arregla es **otra cosa, y es la que pidió el humano**: que la
reclamación **quede con su parte asociado**, de modo que la anomalía descrita en
ese riesgo aceptado —«reclamaciones en `CER` sin ninguna fila en `rcg`, algo que
no ha ocurrido ni una vez en los 2.365 cierres desde 2023»— **desaparezca**. Ese
es el valor real de esta vía, y es grande.

> Segundo camino, no explorado por nadie y que dejo apuntado porque el mensaje
> del ERP lo nombra: **«o Doc. multimedia»**. Sigrid tiene un módulo documental
> aparte —`dog` («Documento»), enlazado a conceptos por **`condog`** (`conide`
> → `con`, `dogide` → `dog`), exactamente el mismo patrón que `rcg`— y **`dog`
> sí tiene columna `url` nativa** («Url externo», texto ilimitado) **y `codrep`
> («Código repositorio externo»)**. Es decir: Sigrid **sí sabe** guardar
> documentos que viven en un repositorio externo por URL; lo que no está claro
> es si sabe hacerlo en la tabla `gra` antigua. Contra: `dog` es «Propiedades de
> con», o sea que **un documento es en sí mismo un concepto** y darlo de alta
> obliga a crear también su fila en `con`. Más escrituras y más riesgo, pero
> puede ser el camino que el ERP tiene pensado para justo esto. Consulta Q9.

---

## 5 · Lo que NO se puede responder sin consultar el ERP

Ocho preguntas abiertas. Para cada una, la consulta de **lectura** preparada,
lista para `POST /api/sql/read` (parámetros siempre con marcadores `?`, como
exige `sigrid_api.md` §5.2) o para
`infra/09_estado_reclamacion_sigrid.ps1` / `Invoke-SigridLectura` de
`infra/08_lectura_sigrid_comun.ps1`.

> Todas son `SELECT`. Ninguna trae datos personales. **Ninguna se ha
> ejecutado.**
> Cuidado con `gra.ima` y `gra.pul`: son binarios ilimitados. **Nunca se
> seleccionan directamente**; se mide su tamaño con `DATALENGTH`.

### Q1 · ¿Qué columnas tiene DE VERDAD la `gra` desplegada? ¿Existe ya una `url`?

*Por qué:* el diccionario es de **v.20240618** y ya sabemos que **le faltan
columnas de `rcg`** (`fecalt`, `feclee`, medidas por F-008 y ausentes del PDF).
Si la `gra` desplegada tuviera `url`, la respuesta a todo el informe cambia.
**Esta es la primera consulta que hay que lanzar.**

```sql
SELECT TABLE_NAME, ORDINAL_POSITION, COLUMN_NAME, DATA_TYPE,
       CHARACTER_MAXIMUM_LENGTH, IS_NULLABLE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME IN ('gra', 'rcg', 'auxgra')
ORDER BY TABLE_NAME, ORDINAL_POSITION
```
Base: negocio. Sin parámetros.

### Q2 · ¿`gra.ide` y `rcg.ide` son IDENTITY? ¿Qué índices tienen?

*Por qué:* de ello depende que la técnica de reserva de F-009 (§3.2) sea
aplicable tal cual. `sigrid_api.md` §7.5 lo afirma **en general**; F-009 lo
verificó **para `log`** en `sys.columns`. Para `gra`/`rcg`, no.

```sql
SELECT t.name AS tabla, c.name AS columna, c.is_identity, c.is_nullable,
       ty.name AS tipo, c.max_length
FROM sys.columns c
JOIN sys.tables t ON t.object_id = c.object_id
JOIN sys.types ty ON ty.user_type_id = c.user_type_id
WHERE t.name IN ('gra', 'rcg')
ORDER BY t.name, c.column_id
```

```sql
SELECT t.name AS tabla, i.name AS indice, i.is_unique, i.is_primary_key,
       col.name AS columna, ic.key_ordinal
FROM sys.indexes i
JOIN sys.index_columns ic ON ic.object_id = i.object_id AND ic.index_id = i.index_id
JOIN sys.columns col ON col.object_id = ic.object_id AND col.column_id = ic.column_id
JOIN sys.tables t ON t.object_id = i.object_id
WHERE t.name IN ('gra', 'rcg')
ORDER BY t.name, i.name, ic.key_ordinal
```

### Q3 · Las dos filas huérfanas: `vin = 1` y `vin = 4`

*Por qué:* **son dos filas** y son la pista más barata que existe. Si alguna
fuera un enlace, media investigación estaría hecha.

```sql
SELECT ide, vin, cod, res, nom, nomori,
       CAST(tex AS varchar(2000)) AS camino,
       gratipide, fec, usu, estcon, ori, guid, anx,
       DATALENGTH(ima) AS bytes_ima
FROM dbo.gra
WHERE vin IN (?, ?)
```
Parámetros: `[1, 4]`.

### Q4 · ¿Qué es cada valor de `vin`? El perfil de cada modo

*Por qué:* nadie ha caracterizado `vin = 2` (154 filas) ni `vin = 0` (38).
Saber qué modo es cada uno acota dónde encajaría el modo URL.

```sql
SELECT vin,
       COUNT(*)                                                      AS filas,
       SUM(CASE WHEN DATALENGTH(ima) > 0 THEN 1 ELSE 0 END)          AS con_binario_local,
       SUM(CASE WHEN DATALENGTH(tex) > 0 THEN 1 ELSE 0 END)          AS con_camino,
       SUM(CASE WHEN nom LIKE 'http%' THEN 1 ELSE 0 END)             AS nom_url,
       SUM(CASE WHEN CAST(tex AS varchar(max)) LIKE 'http%' THEN 1 ELSE 0 END) AS tex_url,
       MAX(LEN(nom))                                                 AS nom_mas_largo,
       MAX(DATALENGTH(tex))                                          AS tex_mas_largo,
       MIN(fec) AS fec_min, MAX(fec) AS fec_max
FROM dbo.gra
GROUP BY vin
ORDER BY vin
```

Y una muestra del modo desconocido:

```sql
SELECT TOP 20 ide, vin, cod, res, nom,
       CAST(tex AS varchar(1000)) AS camino,
       gratipide, fec, DATALENGTH(ima) AS bytes_ima
FROM dbo.gra
WHERE vin = ?
ORDER BY fec DESC
```
Parámetros: `[2]`.

### Q5 · ¿Se ha cerrado alguna reclamación con un gráfico SIN fichero detrás?

*Por qué:* es **el proxy empírico** de la pregunta 4 (§4.3). Los 51 gráficos de
posventa sin pareja en la documental son lo más parecido a un gráfico-URL que
existe hoy.

Intento en una sola llamada (contra la base de negocio; `ALLOWED_DATABASES`
incluye las dos, pero **si la pasarela rechaza el nombre de la otra base en el
`FROM`, usar la variante en dos pasos**):

```sql
SELECT c.est,
       COUNT(*)                                             AS graficos,
       SUM(CASE WHEN rep.cod IS NULL THEN 1 ELSE 0 END)     AS sin_binario_en_documental
FROM dbo.rcg r
JOIN dbo.gra g ON g.ide = r.gra
JOIN dbo.con c ON c.ide = r.con AND c.tip = ?
LEFT JOIN ruesma_rep.dbo.gra rep ON rep.cod = g.cod
GROUP BY c.est
ORDER BY c.est
```
Parámetros: `[708]`.

**Variante en dos pasos** (si la anterior no pasa el guardián):

```sql
-- paso A · contra la base de NEGOCIO: los cod de los gráficos de posventa y el estado
SELECT g.cod, g.vin, c.est
FROM dbo.rcg r
JOIN dbo.gra g ON g.ide = r.gra
JOIN dbo.con c ON c.ide = r.con AND c.tip = ?
```
```sql
-- paso B · contra la base DOCUMENTAL: qué cod tienen binario
SELECT cod FROM dbo.gra WHERE cod IN (?, ?, ?, ...)   -- por lotes
```
Y el cruce se hace en local. (Ojo con la paginación: `sigrid_api.md` §6.4.
13.450 filas caben en el `MAX_ALLOWED_ROWS` de la instancia `dev`, pero manda
el corte de 230 s.)

Complemento: **cómo se cerraron esas reclamaciones**, para saber si fue «Cerrar
parte» o RPV:

```sql
SELECT l.tex, COUNT(*) AS veces
FROM dbo.log l
WHERE l.tab = 'con' AND l.tip = ? AND l.ope = ? AND l.cod = ?
GROUP BY l.tex
```
Parámetros: `[708, 5, '<codigo de una de esas reclamaciones>']`.

### Q6 · ¿Cómo se numera `rcg.pos` cuando la reclamación ya tiene gráficos?

*Por qué:* insertar siempre `pos = 64` puede chocar. Hay 52 posiciones
distintas en uso.

```sql
SELECT n_graficos, COUNT(*) AS reclamaciones,
       MIN(pos_min) AS pos_min, MAX(pos_max) AS pos_max
FROM (
    SELECT r.con, COUNT(*) AS n_graficos, MIN(r.pos) AS pos_min, MAX(r.pos) AS pos_max
    FROM dbo.rcg r
    JOIN dbo.con c ON c.ide = r.con AND c.tip = ?
    GROUP BY r.con
) t
GROUP BY n_graficos
ORDER BY n_graficos
```
Parámetros: `[708]`.

### Q7 · ¿Cabe una URL de SharePoint en el campo? Y ¿cómo es el `cod` de verdad?

*Por qué:* `gra.nom` son **255 caracteres**. Y los dos documentos de referencia
dan el `cod` con longitudes distintas (17 dígitos en
`01_cierre_incidencia_sigrid.md`, 18 en `03_modelo_posventa_sigrid.md` §4.2):
hay que reproducir el formato **medido**, no el transcrito.

```sql
SELECT MAX(LEN(nom)) AS nom_mas_largo,
       MAX(LEN(cod)) AS cod_mas_largo,
       MIN(LEN(cod)) AS cod_mas_corto,
       MAX(DATALENGTH(tex)) AS tex_mas_largo
FROM dbo.gra
```

```sql
SELECT TOP 20 cod, LEN(cod) AS largo, res, nom, fec, usu
FROM dbo.gra g
JOIN dbo.rcg r ON r.gra = g.ide
JOIN dbo.con c ON c.ide = r.con AND c.tip = ?
ORDER BY g.fec DESC, g.ide DESC
```
Parámetros: `[708]`.

> El otro lado de esta pregunta **no es del ERP y no requiere consulta a
> Sigrid**: cuánto miden nuestras URLs. Está en
> `postventa.archivos.web_url` (`services/postventa-api/infrastructure/persistencia/sql/05_archivos.sql`),
> que ya guarda el `webUrl` que devuelve Graph. Un `SELECT max(length(web_url))
> FROM postventa.archivos` lo contesta — **y todavía no incluye la mudanza de
> F-013 a la biblioteca de Posventa**, con su estructura profunda
> `obra / PARTES INCIDENCIAS / <unidad> / PARTES FIRMADOS`, que la alargará.

### Q8 · ¿Es `gra.cod` único? (de ello depende la sentencia 2 del §3.2)

```sql
SELECT COUNT(*) AS filas, COUNT(DISTINCT cod) AS codigos_distintos
FROM dbo.gra
```

### Q9 · El otro camino: ¿usa esta instalación el módulo `dog` / `condog`?

*Por qué:* `dog` **sí tiene `url` nativa**, y el mensaje del ERP dice «algún
gráfico **o Doc. multimedia**».

```sql
SELECT COUNT(*) AS documentos_colgados_de_reclamaciones
FROM dbo.condog cd
JOIN dbo.con c ON c.ide = cd.conide AND c.tip = ?
```
Parámetros: `[708]`.

```sql
SELECT COUNT(*) AS dog_total,
       SUM(CASE WHEN DATALENGTH(url) > 0 THEN 1 ELSE 0 END)     AS con_url,
       SUM(CASE WHEN LEN(codrep) > 0 THEN 1 ELSE 0 END)         AS con_repositorio_externo,
       SUM(CASE WHEN DATALENGTH(graima) > 0 THEN 1 ELSE 0 END)  AS con_binario
FROM dbo.dog
```

Y el catálogo de tipos, por si alguno está marcado como enlace
(`auxgra.tipfic`, «Tipo de ficha multimedia», nunca inspeccionado):

```sql
SELECT ide, cod, res, tipfic, tipver, tiplec, tipaso, tammax, fecbaj, pos
FROM dbo.auxgra
ORDER BY ide
```

### Q10 · LA DECISIVA · Qué escribe Sigrid al asociar una URL

**No hay ninguna consulta que responda esto sobre los datos de hoy: la opción
nunca se ha usado.** Sólo se responde **después** de que una persona la use una
vez a mano. El protocolo, entero:

1. **Posventa** elige una reclamación de prueba (o crea una), y hace
   *Importa → **Asociar URL de Internet…*** con una dirección cualquiera —vale
   la de un parte ya archivado en SharePoint, y así se comprueba de paso si el
   visor de Sigrid la abre y si pide autenticación—, rellenando **Descripción**
   y **Tipo gráfico `PV002`** como en el flujo normal.
2. **Anota el código de la reclamación y el día**. Nada más.
3. Después, y **solo lecturas nuestras**:

```sql
-- la fila del gráfico recién creada: aquí está vin, y aquí está dónde fue la URL
SELECT TOP 20 ide, vin, cod, res, nom, nomori,
       CAST(tex AS varchar(4000)) AS camino,
       gratipide, fec, usu, cla, guid, estcon, ori, anx, numrev, texrev,
       DATALENGTH(ima) AS bytes_ima
FROM dbo.gra
WHERE fec >= ?
ORDER BY ide DESC
```
Parámetros: `[<AAAAMMDD del día de la prueba>]`.

```sql
-- el enlace: confirma que rcg se rellena igual, y con qué pos y qué cla
SELECT r.ide, r.con, r.gra, r.pos, r.cla, c.cod AS reclamacion, c.est
FROM dbo.rcg r
JOIN dbo.con c ON c.ide = r.con
WHERE c.tip = ? AND c.cod = ?
```
Parámetros: `[708, '<codigo de la reclamacion de prueba>']`.

4. **Y si además ejecuta *Procesos → 3. Cerrar parte* sobre esa reclamación**,
   queda contestada de una vez la pregunta 4 —si un gráfico-URL satisface la
   comprobación—, y se lee así:

```sql
SELECT l.ide, l.fec, l.hor, l.ope, l.tex, l.est, l.cod
FROM dbo.log l
WHERE l.tab = 'con' AND l.tip = ? AND l.cod = ?
ORDER BY l.ide DESC
```
Parámetros: `[708, '<codigo de la reclamacion de prueba>']`.
Si aparece una fila `ope = 5` con `tex = 'Cerrar parte'` y `con.est` quedó en el
estado `CER`, **la vía URL es válida de punta a punta**.

### Q11 · Lo que NINGUNA consulta de lectura puede responder

Por honestidad, y para que nadie lo busque:

| Pregunta | Por qué no se puede leer | Quién lo resuelve |
|---|---|---|
| ¿El `SqlWriteGuard` acepta `INSERT … SELECT … WITH (UPDLOCK, HOLDLOCK)`? | Es comportamiento de la pasarela ante una **escritura**, no un dato de la base | La primera ejecución del **bloque 8 de F-009**, que ya lleva esa misma sentencia |
| ¿La comprobación del gráfico **bloquea** o solo avisa? | Habría que **intentar** cerrar sin gráfico | La prueba manual de Q10, o el proveedor del ERP |
| ¿«Cerrar parte» dispara correos o avisos fuera de la base? | No hay señal en la base ni a favor ni en contra (`03_modelo_posventa_sigrid.md` §5.4) | El proveedor del ERP |
| ¿Sigrid **valida** la URL al asociarla (que responda, que sea accesible)? | Es lógica del cliente del ERP | La prueba manual de Q10 |
| ¿El visor de Sigrid abre una URL de SharePoint, y con qué identidad? | Es comportamiento de la aplicación de escritorio | La prueba manual de Q10, y es **la que decide si Posventa lo acepta como útil** |
| ¿Qué pasa si el fichero se mueve en SharePoint y la URL muere? | Es una decisión de negocio, no un dato | El humano, y F-013 al mudar la biblioteca |

---

## 6 · Recomendación, en cuatro líneas

1. **Lanzar Q1 antes que nada.** Si la `gra` desplegada ya tiene columna `url`,
   todo lo demás se simplifica. Cuesta una consulta.
2. **Lanzar Q3, Q4, Q5 y Q8** en el mismo bloque de lecturas: son baratas,
   caracterizan `vin` y cierran la pregunta 4 por la vía del proxy.
3. **Pedir a Posventa la prueba manual (Q10).** Es lo único que convierte la
   inferencia en dato, cuesta cinco minutos de una persona y **no nos obliga a
   escribir nada en producción**.
4. **No diseñar ninguna feature todavía.** F-008 ya escribió, y con razón, que
   la combinación de `vin`/`tex`/`nom` **«no se debe diseñar sobre esta
   suposición»** (`03_modelo_posventa_sigrid.md` §4.3). Sigue valiendo.

> **Aviso de mantenimiento para el líder:** `specs/F-009-cierre-sigrid/design.md`
> §1 (D4) dice que el gráfico-URL «lo necesita **F-013**», pero **F-013 en
> `harness/features.json` es hoy «mudar el archivo a la biblioteca de
> Posventa»**. El gráfico-URL **no tiene feature asignada**. Dar de alta la
> feature es cosa del líder, no mía; solo señalo la referencia rota.
