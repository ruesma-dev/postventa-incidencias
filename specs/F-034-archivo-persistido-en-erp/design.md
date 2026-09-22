<!-- specs/F-034-archivo-persistido-en-erp/design.md -->
# F-034 · Adjuntar y cerrar se fían del cuerpo — Diseño técnico

> Servicios: `services/postventa-api/` (backend) y `services/postventa-front/`
> (un solo punto, §7). Encaja en `docs/ARCHITECTURE.md` pasos **7a** (gráfico)
> y **7b** (cierre), y en la semántica 8 (el nombre del fichero). Cumple
> `docs/CONVENTIONS.md`: dominio sin dependencias, la aplicación orquesta, la
> composición vive en el borde.
>
> **Esta spec no ha escrito en ningún sistema.** Todo lo medido sale de leer el
> árbol en `dev`, commit `127e457`, y la rama `feature/F-031-nombrado-persistido`
> con `git show`. No se ha tocado Sigrid, SharePoint, Azure ni PostgreSQL.

## 0 · Dónde está el riesgo

### 0.1 · Qué se rompe si esto sale mal

| Fallo | Qué se ve | Por qué es grave |
|---|---|---|
| Se cierra **otra** reclamación | En nuestra pantalla, un cierre correcto | Irreversible desde el circuito: `cerrado` es terminal (F-028 R7). En el ERP quedan dos incidencias mal: una cerrada sin motivo y otra abierta |
| Se cuelga el parte de **otra** reclamación | Nada | El PDF lleva el DNI manuscrito de un cliente y queda en el expediente de otro |
| Se adjunta y se cierra un parte **sin archivar** | Nada | El riesgo aceptado de F-009 §2 solo es asumible porque el parte firmado existe en SharePoint. Sin él, se da por resuelta una incidencia sin dejar la prueba |
| Se rompe la puerta de aptitud al tocar `ctx.situacion` | Un parte que nadie miró llega al ERP | Es lo único que separa un parte sin validar de una reclamación cerrada en producción |

Ninguno da un error ruidoso por sí solo. Por eso el diseño elige siempre **no
escribir y decir por qué** antes que escribir con un dato dudoso.

### 0.2 · Rigor `critico`

La ficha lo declara. En la práctica: fase **RED** sobre R1, R3, R8, R9, R11 y
R13; cobertura de las líneas cambiadas sobre el umbral; campaña de mutación
**sin supervivientes sin justificar** sobre `paso_grafico.py`, `paso_cierre.py`,
`adjuntar.py`, `cerrar.py` y el módulo nuevo; y las verificaciones
`MANUAL (humano)` de §12 con su comando y su resultado real.

## 1 · Lo medido

### 1.1 · El dato correcto ya está delante, y no cuesta nada

| Pregunta | Respuesta | Fuente **[MEDIDO]** |
|---|---|---|
| ¿Qué lee hoy la puerta de archivo? | `ctx.archivo`, fabricado por el borde con el cuerpo | `paso_grafico.py:289`, `paso_cierre.py:247`; `adjuntar.py:262-265`, `cerrar.py:235-238` |
| ¿Trae la situación la traza del archivo? | **Sí**, desde F-033 | `sentencias.py:608-624`; `SituacionParte.archivo` en `domain/models/estado.py` |
| ¿Trae la situación los dos códigos guardados? | **Sí**, desde F-030 | `sentencias.py:578-582`; `ResultadoValidacion.codigo_obra` / `.numero_incidencia` (`domain/models/validacion.py:178-179`) |
| ¿Está todo eso disponible cuando se decide? | **Sí**: la puerta de aptitud es lo primero de los dos pasos | `paso_grafico.py:148`, `paso_cierre.py:152` → `puerta_de_estado.py:145` |
| ¿Cuesta alguna consulta? | **Ninguna** | Son columnas de la sentencia que ya se ejecuta |
| ¿Puede `situacion.validacion` ser `None` al llegar al cotejo? | **No** | `puerta_de_estado.py:147-148` levanta `ParteNoApto` antes |

**Esto es lo que abarata la feature**: cero columnas, cero sentencias, cero
métodos del puerto, cero DDL. Igual que F-031 y al revés que F-033.

### 1.2 · El front, medido

| Pregunta | Respuesta | Fuente **[MEDIDO]** |
|---|---|---|
| ¿De dónde salen los códigos del cuerpo? | `valorDeCampo`: la corrección si la hay, si no lo de la IA | `js/pipeline.js:386-393`, usado en `:624-627` y `:537` |
| ¿De dónde sale `estado_archivo`? | De una **constante**, no de una lectura | `js/pipeline.js:158, 540, 631` |
| ¿Quién llama a `/adjuntar` y `/cerrar`? | `ejecutarCircuito` | `js/pipeline.js:1111-…` |
| ¿Quién llama a `ejecutarCircuito`? | `_circuitoDeUno` ← `_lanzarTanda` ← **dos** sitios | `js/app.js:703-733` (`confirmarArchivo`) y `js/app.js:866-882` (`reintentarCierre`) |
| ¿Cuál de los dos pasa por el vaciado de F-031? | **Solo `confirmarArchivo`** | F-031 `design.md` §6.2: el vaciado va en `confirmarArchivo`, antes de `this.pendientes()` |

**Hallazgo propio de esta ficha (§8, H-2)**: `reintentarCierre` entra al
circuito **sin vaciar los pendientes**, y su camino llega directo a
`/api/cerrar` —y a `/api/adjuntar` si el gráfico no consta—. Es el único hueco
que F-031 no podía tapar, porque F-031 tenía prohibido tocar estos dos
endpoints. Lo tapa R29.

### 1.3 · La dependencia de F-031, medida y **bloqueante**

**[MEDIDO]** `git rev-list --left-right --count dev...feature/F-031-nombrado-persistido`
→ **`0  23`**: F-031 **no está en `dev`**. Por tanto, en la rama de F-034
—creada desde `dev`, commit `127e457`— **no existen**:

- `domain/models/nombrado.py::es_el_mismo_codigo` (el cotejo normalizado, F-031
  §3.1);
- `domain/models/errores.py::CodigosNoCoinciden` (F-031 §3.2);
- `application/pipelines/paso_archivo.py::CodigosDelParte` y
  `_codigos_guardados` (F-031 §4.1);
- `js/autoguardado.js::vaciarPendientes()` (F-031 §6.1), que es lo que R29
  necesita.

Esta feature **reutiliza las cuatro** y no las reinventa. De ahí la decisión
**D-1** de §11, que es la única que bloquea el arranque del implementer.

## 2 · Ficheros

### 2.1 · A crear

| Ruta | Capa | Qué |
|---|---|---|
| `services/postventa-api/application/pipelines/codigos_del_parte.py` | application | `CodigosDelParte`, `codigos_guardados(ctx)`, `exigir_codigos_declarados(...)` y `exigir_codigos_completos(...)`, en **un solo sitio** para los tres pasos (§3.1) |
| `services/postventa-api/tests/test_f034_archivo_persistido.py` | tests | R1–R7 sobre los dos pasos y sus dos endpoints, con dobles |
| `services/postventa-api/tests/test_f034_codigos_en_el_erp.py` | tests | R8–R19, R24, R27, R28 desde `POST /api/adjuntar` y `POST /api/cerrar` |
| `services/postventa-api/tests/test_f034_sin_consultas_de_mas.py` | tests | R38: el contador de `consultar_situacion` por paso |
| `services/postventa-api/tests/test_f034_alcance_cerrado.py` | tests | R39, con el patrón de `test_f033_alcance_cerrado.py` |
| `services/postventa-front/tests_js/reintento_vaciado.test.js` | tests | R29, R30, R32, R33 sobre `reintentarCierre` |

### 2.2 · A modificar

| Ruta | Qué cambia |
|---|---|
| `services/postventa-api/domain/models/errores.py` | **Dos** clases nuevas: `CodigoNoConsta` (R15) y —si D-1 se cierra como se recomienda— ninguna más, porque `CodigosNoCoinciden` la trae F-031 (§3.2) |
| `services/postventa-api/application/pipelines/puerta_de_estado.py` | `exigir_parte_archivado(ctx, *, y_por_eso)`, la puerta de archivo **en un solo sitio**, leyendo `ctx.situacion.archivo` (§3.3). Enmienda fechada en la cabecera |
| `services/postventa-api/application/pipelines/paso_grafico.py` | El cotejo en el punto 1 bis; los códigos guardados alimentando `_codigo_de_incidencia` y `componer_peticion`; `_exigir_archivado` sustituido por la puerta compartida; los dos parámetros pasan a ser **declarados** (§4) |
| `services/postventa-api/application/pipelines/paso_cierre.py` | Lo mismo, con **un** código (§5) |
| `services/postventa-api/interface_adapters/api/adjuntar.py` | `_como_contexto` deja de fabricar la `TrazaArchivo`; los códigos se pasan **explícitos** como declarados (§6.1) |
| `services/postventa-api/interface_adapters/api/cerrar.py` | Lo mismo (§6.1) |
| `services/postventa-api/function_app.py` | `CodigosNoCoinciden` y `CodigoNoConsta` se suman a los `except` que ya devuelven **409** en los dos endpoints, y se amplían los comentarios que documentan sus códigos (§6.2) |
| `services/postventa-api/application/pipelines/paso_archivo.py` e `interface_adapters/api/archivar.py` | **Solo el `import`**: `CodigosDelParte` y su cotejo pasan a venir del módulo compartido. Ni una regla cambia (R26, §3.1) |
| `services/postventa-front/js/app.js` | `reintentarCierre` espera el vaciado antes de lanzar el circuito (§7.1) |
| `docs/ARCHITECTURE.md` | Recuadro fechado en los pasos 7a y 7b: de dónde salen el estado del archivo y los dos códigos (§10) |
| `specs/F-033-l1-traza-archivo/design.md` §10 y `specs/F-031-nombrado-persistido/design.md` §8 | Nota de cierre de D-6 y de H-1, con la fecha y el puntero a esta carpeta (§10) |
| `CHECKPOINTS.md` | Nada. Se cita, no se toca |

### 2.3 · Lo que NO se toca (y tienta)

- **`infrastructure/persistencia/` entero** y todo `sql/`: ni una columna, ni un
  `JOIN`, ni un `NN_nombre.sql` (R23). El dato ya viaja.
- **`domain/ports/persistencia.py`** y **`domain/models/estado.py`**: ni un
  método, ni un campo. `SituacionParte` ya trae las cinco cosas.
- **`puerta_de_estado.py::exigir_parte_aprobado`**: gana una función hermana al
  lado, pero **ella no cambia** (R20).
- **`domain/models/nombrado.py`**: las cuatro reglas y `nombre_admisible` se
  quedan letra por letra (R24). Esta feature cambia de dónde salen las
  entradas, no qué se hace con ellas. `es_el_mismo_codigo` **la trae F-031**.
- **`domain/models/grafico.py` y `domain/models/cierre.py`**: dominio puro,
  intactos. `componer_peticion` sigue recibiendo dos cadenas; lo que cambia es
  **quién se las da**.
- **Las tres capas de idempotencia de F-012** y el orden de los pasos (R21).
- **`_exigir_adjuntado`** y `ctx.traza_grafico` (R22).
- **`js/pipeline.js`**: ni `cuerpoDeGrafico`, ni `cuerpoDeCierre`, ni
  `ejecutarCircuito`. El contrato no cambia (R31) y meter la espera ahí lo
  ataría a un temporizador, que es lo que F-031 §6.3 ya descartó.
- **`js/autoguardado.js`**: `vaciarPendientes()` lo escribe F-031 y aquí solo
  se llama.
- **El terreno de F-013**: no se mira la biblioteca, ni la unidad, ni la
  estructura de carpetas (D-4).

## 3 · Las piezas compartidas

### 3.1 · `application/pipelines/codigos_del_parte.py`

```python
@dataclass(frozen=True)
class CodigosDelParte:
    """Los dos códigos que deciden en qué reclamación se escribe."""
    codigo_obra: str
    numero_incidencia: str


def codigos_guardados(ctx: ContextoParte) -> CodigosDelParte: ...

def exigir_codigos_declarados(
    declarados: CodigosDelParte | None,
    guardados: CodigosDelParte,
    *,
    solo_incidencia: bool = False,
    y_por_eso: str,
) -> None: ...

def exigir_codigos_completos(
    guardados: CodigosDelParte, *, solo_incidencia: bool = False, y_por_eso: str
) -> None: ...
```

**Por qué un módulo y no una copia en cada paso.** Es literalmente el argumento
que `puerta_de_estado.py` tiene escrito en su cabecera y que F-028 pagó por
aprender: *«dos copias de una regla divergen el día que alguien la corrija en
una sola, y en una campaña de mutación cada copia se cuenta aparte, con lo que
la segunda y la tercera se quedan sin tests que las maten»*. Aquí la aplican
**tres** pasos —archivo, gráfico y cierre— y pesa más que en ningún otro sitio:
la que se aflojara sería la que dejara escribir en la reclamación equivocada.

`solo_incidencia=True` es lo que necesita el cierre, cuyo cuerpo no trae
`codigo_obra` (R16). No es un caso especial escondido: es un parámetro con
nombre, y su test dice qué pasa con cada valor.

`codigos_guardados` lee de `ctx.situacion.validacion`, que es donde F-030 los
dejó y donde F-031 decidió leerlos (su D-1). **Un único punto de lectura**, que
es lo que hace que F-013 no tenga que volver a decidirlo.

### 3.2 · Los errores, y por qué son distintos

```python
# domain/models/errores.py
class CodigoNoConsta(Exception):
    """Lo guardado no trae el código con el que habría que escribir (F-034 R15)."""
    motivo: str
```

Tres hechos, tres errores, y **no es cosmético** (R28): cada uno manda a quien
lo lee a un sitio distinto.

| Hecho | Error | Se arregla | HTTP |
|---|---|---|---|
| Lo declarado no es lo guardado | `CodigosNoCoinciden` (F-031) | Guardando la corrección (`POST /api/parte`) y reintentando | 409 |
| Lo guardado está incompleto | `CodigoNoConsta` (nuevo) | Tecleando el código en el parte y guardándolo | 409 |
| El parte no consta archivado | `ParteNoArchivado` (ya existe) | Archivando primero (`POST /api/archivar`) | 409 |
| El nombre compuesto no vale para SharePoint | `NombradoImposible` (ya existe) | Corrigiendo el carácter prohibido del código **guardado** | 409 |

**Un solo `CodigoNoConsta` para los dos endpoints** y no uno por sitio: es el
mismo hecho. Dejar que en `/adjuntar` saliera por `NombradoImposible` —que es
por donde caería solo, dentro de `componer_peticion`— y en `/cerrar` por otro
camino daría dos errores distintos para una misma cosa, que es justo lo que
F-031 §3.1 razonó que no hay que hacer. Con `exigir_codigos_completos` puesto
en el punto 1 bis, `NombradoImposible` queda reservada a su caso propio y sigue
siendo alcanzable: un código guardado con un carácter prohibido (R24).

### 3.3 · La puerta de archivo, en un solo sitio

```python
# application/pipelines/puerta_de_estado.py
def exigir_parte_archivado(ctx: ContextoParte, *, y_por_eso: str) -> None:
    """El parte tiene que constar archivado **según el almacén** (F-034 R1)."""
```

Lee `ctx.situacion.archivo` —la traza que F-033 trajo— y **nunca** `ctx.archivo`.
Vive junto a `exigir_parte_aprobado` porque son la misma clase de cosa: puertas
que los pasos del circuito abren leyendo la **misma** `SituacionParte` que la
consulta de aptitud dejó puesta, sin pagar un viaje más. La cabecera del módulo
lleva su enmienda fechada, al estilo de las de F-030 y F-033.

Hoy son **dos copias** (`paso_grafico.py:282-295` y `paso_cierre.py:240-255`)
con el mismo criterio y distinto final de frase; el parámetro `y_por_eso`
conserva esa diferencia, que es la parte del mensaje que le dice al lector qué
se ha quedado sin hacer. Mismo mecanismo que ya usa `exigir_parte_aprobado`.

`paso_archivo` **no** la usa: ahí el archivo se crea, no se exige.

## 4 · `paso_grafico`

### 4.1 · El orden, que es la mitad del requisito

Los pasos de `paso_grafico` se conservan y se intercala **uno**:

```
1.      Puerta de aptitud            (F-028/F-030; deja ctx.situacion)
1 bis.  COTEJO de los códigos        ← F-034 R11, R13, R15  (nuevo)
2.      Puerta de archivo            ← ahora desde ctx.situacion.archivo (R1)
3.      El fichero: tope y firma     (F-012 R18, R19)
4.      L1 · traza local del gráfico (F-012 R24)
5.      El login, verificado contra el ERP
6.      La reclamación               ← ahora con el código GUARDADO (R8)
7.      evaluar / dry-run / traza
8.      Solo con commit: la escritura
```

El cotejo va en **1 bis** y no más abajo, y es un requisito (R13): a partir del
punto 5 ya se ha hablado con el ERP, y a partir del 7 ya hay filas escritas en
`postventa.graficos`. Un cotejo que fallara después dejaría rastro de una
operación que nunca debió intentarse — y, peor, habría preguntado al ERP por
**la reclamación equivocada**.

Va **después** de la puerta de aptitud porque necesita la situación que esa
puerta lee: sin ella no hay con qué cotejar, y adelantarlo costaría una segunda
consulta (contra R10).

Va **antes** de la puerta de archivo a propósito: el cotejo dice *sobre qué
parte y qué reclamación* estamos operando, y todo lo que viene debajo usa esos
códigos. Resolver primero la identidad y después el estado es el mismo orden
que sigue `paso_archivo` desde F-031.

### 4.2 · Firma

```python
def paso_grafico(
    ctx, erp, graficos, repositorio, usuarios, preferencias,
    *,
    commit: bool,
    confirmado: bool,
    usuario_oid: str,
    correo: str,
    codigos_declarados: CodigosDelParte | None = None,   # ← sustituye a los dos str
    gratipide: int,
    tope_bytes: int,
    ahora: datetime,
) -> ContextoParte:
```

`numero_incidencia: str` y `codigo_obra: str` (`paso_grafico.py:116-117`)
**desaparecen** y los sustituye `codigos_declarados`, que es *lo que afirma
quien llama* y **solo** sirve para el cotejo. Dos razones para no conservarlos:

1. mientras existan dos parámetros con esos nombres, el cuerpo de la función
   puede volver a usarlos para nombrar o para buscar, y el defecto vuelve sin
   que nadie lo note. Es la misma decisión que F-031 tomó al retirar `_campo`;
2. un solo objeto con nombre hace que la firma **declare** la asimetría: lo
   declarado entra por un sitio, lo guardado sale de `ctx`.

Opcional para que los tests que no hablan de cuerpos no tengan que inventarse
uno; el borde lo pasa siempre. Cuando es `None` no hay nada que cotejar y **el
paso sigue usando lo guardado** (R19): el camino sin cotejo no puede escribir en
otra reclamación.

Dentro, `_codigo_de_incidencia(...)` y `componer_peticion(...)` pasan a recibir
`guardados.numero_incidencia` y `guardados.codigo_obra`.

`_codigo_de_incidencia` conserva su `CuerpoDeCierreInvalido` para el caso
imposible-por-construcción, pero deja de ser el camino del código vacío: ese lo
corta `exigir_codigos_completos` en 1 bis con un 409 (R15). Se documenta en su
docstring para que nadie lo tome por muerto.

## 5 · `paso_cierre`

Mismo patrón, con **un** código:

```
1.      Puerta de aptitud
1 bis.  COTEJO del número de incidencia   ← R11, R13, R15 (solo_incidencia=True)
2.      Puerta de archivo                 ← desde ctx.situacion.archivo (R1)
3.      El login, verificado contra el ERP
4.      El dry-run                        ← con el código GUARDADO (R9)
5.      evaluar / traza dry_run_ok / traza del gráfico
6.      Solo con commit: _exigir_adjuntado, autorización y escritura
```

`numero_incidencia: str` (`paso_cierre.py:117`) se sustituye por
`codigos_declarados: CodigosDelParte | None`, y la llamada de `:155` pasa a
`_codigo_de_incidencia(guardados.numero_incidencia)`.

**Esto es lo más grave que toca la feature**: la línea 155 es la que decide,
tres llamadas más abajo, qué fila de `con` recibe el `UPDATE` en producción.
Por eso su test central es el de R9: situación con
`numero_incidencia="RS26.08/0123"`, cuerpo con `"RS26.09/0999"` → **cero
llamadas al doble del ERP** y 409.

`_exigir_adjuntado` (`paso_cierre.py:279-…`) **no se toca** (R22): ya lee la
traza propia del repositorio.

## 6 · El borde

### 6.1 · `adjuntar.py` y `cerrar.py`

Dos cambios en cada uno, y el segundo es la mitad del valor:

1. el handler construye `CodigosDelParte(...)` con lo que trae el cuerpo y lo
   pasa como `codigos_declarados`;
2. `_como_contexto` **deja de fabricar la `TrazaArchivo`**: el `ContextoParte`
   sale con `archivo=None`. Con eso, ese objeto deja de ser una fuente de
   estado y pasa a ser lo que decía F-030 que era: un contexto mínimo con el
   `hash` y (en adjuntar) los bytes.

`CAMPOS_OBLIGATORIOS` **no cambia** en ninguno de los dos (R18): los siete de
`/adjuntar` y los seis de `/cerrar` siguen siendo obligatorios, y un cuerpo
incompleto o con una enumeración desconocida sigue siendo **400** (R17). Lo que
cambia es **para qué sirven** tres de ellos, y el docstring de cada módulo lo
dirá con el mismo formato de enmienda fechada que ya usan los párrafos de F-030
que hay ahí (`adjuntar.py:40-58`, `cerrar.py:45-64`).

**`estado_archivo` queda sin decidir nada, y eso se dice en voz alta.** No se
retira del contrato (§11, D-3) y **no se coteja** (R7): manda lo guardado, y un
409 porque el cliente se quede corto en su afirmación sería un error nuevo sin
ninguna escritura que evitar. Lo que impide que se convierta en un adorno
peligroso son dos tests que fijan la semántica: cuerpo `pendiente` + base
`archivado` → **pasa**; cuerpo `archivado` + base sin traza → **409 y cero
llamadas al ERP**.

### 6.2 · `function_app.py`

`CodigosNoCoinciden` y `CodigoNoConsta` se añaden a los `except` que ya
devuelven **409** en los dos endpoints (`function_app.py:885-902` para
adjuntar, `:1010-1028` para cerrar). Ni un código HTTP nuevo, ni una clave
nueva (R27, R35): `{"error": <motivo>}`, como sus hermanas. Y se amplían los
dos comentarios que documentan los códigos de cada endpoint, para que los 409
nuevos queden dentro de la familia que ya está explicada ahí.

El motivo **no se registra tal cual** en el log: se conserva la regla vigente
—al log va el tipo del error— porque estos motivos nombran los dos códigos y el
`except` es compartido con errores que nombran el correo (R36).

## 7 · El front

### 7.1 · `js/app.js::reintentarCierre`

```js
async reintentarCierre(parte) {
  const vaciado = await this._autoguardado().vaciarPendientes();   // R29
  if (!vaciado.ok) {                                               // R30
    this.avisoArchivo = AVISO_SIN_GUARDAR;
    return;                                                        // no se lanza nada
  }
  const arranque = await window.Pipeline.conGuardaDeTanda(() =>
    this._lanzarTanda([parte]),
  );
  ...
}
```

Las tres precisiones que importan:

- **es el único camino que faltaba.** El otro, `confirmarArchivo`, ya lo cubre
  F-031, y su vaciado cubre la tanda entera —archivar, adjuntar y cerrar—
  porque los tres pasos van dentro del mismo `ejecutarCircuito`;
- **no se mete en `_lanzarTanda`.** Ahí llegaría con la tanda ya calculada, y
  F-031 R19 exige lo contrario en `confirmarArchivo`: guardar revalida, y una
  tanda calculada antes del vaciado podría incluir un parte que acaba de dejar
  de ser circulable. Dos llamadas con su motivo, en vez de una que solo sirve
  para la mitad de los casos;
- **la confirmación de F-025 no se toca.** `reintentarCierre` ya se apoya en la
  confirmación dada para ese parte, y el vaciado no la consume ni la reinicia.

Si D-5 se cierra en contra, R29 se puede cubrir **solo con el backend**: el 409
de R11 aparecería en pantalla por el camino de R32 y la persona tendría que
guardar y reintentar. Funciona, pero convierte el caso normal —corregir y
reintentar— en un error que hay que entender. Es la misma alternativa que F-031
§6.3 descartó.

### 7.2 · Lo que el front **no** cambia

El cuerpo de las dos peticiones se compone exactamente igual (R31). Esta
feature **no necesita** que el front deje de mandar `estado_archivo` ni que
cambie de dónde saca los códigos: el backend deja de creerle, que es otra cosa.
Eso es lo que permite desplegar **backend primero** sin coordinar nada (§9).

## 8 · Hallazgos

**H-2 · `reintentarCierre` entra al circuito sin vaciar.** **[MEDIDO]**
`js/app.js:866-882` llama a `_lanzarTanda([parte])` directamente. Se cierra
**dentro** de esta ficha (R29), porque es exactamente el camino que llega a los
dos endpoints que F-034 revisa.

**H-3 · `_exigir_archivado` no mira la biblioteca.** La traza persistida dice
además en qué `drive_id` quedó el fichero, y ni la puerta de hoy ni la de F-034
lo miran: un parte archivado en la biblioteca de IT pasa igual que uno de
Posventa. **No se toca aquí** (D-4): es terreno de F-013, que ya tiene el asunto
de las 133 trazas de IT abierto en `progress/current.md`. Se deja anotado para
ella.

## 9 · Orden de despliegue y compatibilidad

El contrato HTTP no cambia (R18) y el front no cambia lo que manda (R31), así
que **backend y front se despliegan por separado y en cualquier orden**:

- **backend nuevo + front viejo**: funciona. El front sigue mandando los tres
  campos; el backend los coteja y los ignora. El único camino que se queda sin
  cubrir hasta que suba el front es el vaciado de `reintentarCierre` (R29), y
  su red es el 409, que se pinta igual;
- **backend viejo + front nuevo**: funciona. Un vaciado de más antes de un
  reintento no le molesta a nadie.

Es la propiedad que hace que esta feature no necesite una ventana de
despliegue, al revés que F-031, donde las dos mitades tenían que ir juntas.

## 10 · Documentación a actualizar

- `docs/ARCHITECTURE.md` · pasos **7a** y **7b**: recuadro **«Precisado por
  F-034 el 2026-09-22»** diciendo que «consta archivado» se lee de la traza
  guardada y que la reclamación —y el nombre del gráfico— salen de los dos
  códigos **guardados**; y que lo que venga en el cuerpo solo puede cerrar la
  puerta. Mismo formato que los de F-030, F-032 y F-033.
- `specs/F-033-l1-traza-archivo/design.md` §10 · nota de cierre de **D-6**, con
  la fecha y el puntero a esta carpeta.
- `specs/F-031-nombrado-persistido/design.md` §8 · nota de cierre de **H-1**,
  ídem.
- `azure-apps/postventa_incidencias.md` · **nada**, y se deja escrito por qué
  (§11.1 de `requirements.md` no aplica; ver aquí abajo).

## 11 · Encaje, límites y decisiones abiertas

### 11.1 · Límite de microservicio

Esta feature vive **entera** dentro de `postventa-incidencias`: mueve el origen
de tres datos dentro de su propio backend y añade una espera en su propio
front. **No cruza ninguna frontera del ecosistema**: no cambia lo que este
proyecto expone ni lo que consume de `sigrid-api` —mismas llamadas, mismos
endpoints de la pasarela, mismo contrato—, no toca el PostgreSQL compartido a
nivel de servidor ni fuera de su schema, y no pisa el catálogo de
`front-portal`. Por eso **`azure-apps/postventa_incidencias.md` no cambia**, y
se comprueba y se deja escrito aunque el resultado sea «no hay nada que tocar».

Que toque dos carpetas de `services/` no rompe la regla: la responsabilidad es
una sola —de dónde salen los datos con los que se escribe en el ERP— y el front
no gana lógica de dominio, gana una espera.

### 11.2 · Decisiones abiertas, con recomendación

> El implementer **no arranca** hasta que el humano cierre **D-1**. Las demás
> se pueden cerrar con la recomendación.

| Id | Pregunta | Opciones | **Recomendación** |
|---|---|---|---|
| **D-1** *(bloqueante)* | F-031 **no está en `dev`** (§1.3) y F-034 necesita cuatro piezas suyas. ¿Cómo arranca? | (a) el humano mergea `feature/F-031-nombrado-persistido` a `dev` y F-034 se rebasa encima; (b) F-034 mergea esa rama dentro de la suya y las dos llegan juntas a `dev`; (c) F-034 se escribe sus propias copias de `es_el_mismo_codigo`, `CodigosNoCoinciden`, `CodigosDelParte` y `vaciarPendientes` | **(a)**. Es el orden que el humano fijó (F-031 → F-034) y deja el historial limpio. Bloquea las dos verificaciones manuales de F-031 (T14, T15), que siguen pendientes: si el humano prefiere no esperar a ellas, **(b)** consigue lo mismo y no obliga a nada. **(c) no**: cuatro copias de reglas que ya existen es exactamente lo que `puerta_de_estado.py` tiene escrito que no se hace |
| **D-2** | ¿Dónde viven `CodigosDelParte` y su cotejo? | (a) módulo nuevo `application/pipelines/codigos_del_parte.py`, compartido por los tres pasos; (b) importarlos de `paso_archivo.py`, donde F-031 los deja; (c) una copia en cada paso | **(a)**. (b) haría que `paso_cierre` importara del paso de archivo, que no tiene nada que ver con él; (c) es la trampa de las copias. Precedente exacto: `puerta_de_estado.py` y `constancia.py` |
| **D-3** | ¿Qué se hace con `estado_archivo` en el cuerpo? | (a) sigue obligatorio y validado (400), **no decide nada** y no se coteja; (b) sigue obligatorio y se **coteja** (409 si difiere); (c) se retira del contrato | **(a)**. (b) solo podría dispararse cuando el cliente se queda **corto** en su afirmación —dice `pendiente` y la base dice `archivado`—, y ahí no hay ninguna escritura que evitar: sería un 409 nuevo sin valor. (c) cambia el contrato HTTP de dos endpoints dentro de una feature de seguridad y obliga a coordinar el despliegue del front; se puede hacer después, y se deja anotado |
| **D-4** | ¿Qué código HTTP para «lo guardado está incompleto» (R15)? | (a) **409** con error propio `CodigoNoConsta`; (b) dejar el 400 de hoy (`CuerpoDeCierreInvalido`); (c) reutilizar `NombradoImposible` | **(a)**. (b) miente: la petición está bien formada y lo que falta está en la base; además manda a quien lo lee a mirar su cuerpo. (c) da dos errores distintos para el mismo hecho según el endpoint (§3.2) |
| **D-5** | ¿Se toca el front? | (a) sí, solo `reintentarCierre` (R29); (b) no, y se fía todo al 409 | **(a)**. Es una llamada y una guarda. Con (b), corregir un número de incidencia y pulsar «reintentar» devuelve un 409 que la persona tiene que entender y repetir; y el defecto silencioso —reintentar con el código **viejo**— seguiría vivo en ese camino |
| **D-6** | ¿Se unifica la puerta de archivo? | (a) `exigir_parte_archivado` en `puerta_de_estado.py`, junto a su hermana; (b) módulo nuevo `puerta_de_archivo.py`; (c) dos copias, cada una leyendo `ctx.situacion.archivo` | **(a)**. Son dos copias de la regla **que esta feature acaba de cambiar**, y la cabecera de `puerta_de_estado.py` ya explica por qué eso no se deja así. (b) parte en dos un módulo cuyo tema es exactamente ese |
| **D-7** | ¿Se conservan `numero_incidencia` y `codigo_obra` como parámetros sueltos de los dos pasos? | (a) no: los sustituye `codigos_declarados`; (b) sí, y se cotejan sin cambiar la firma | **(a)**. Con (b) quedan en el cuerpo de la función dos cadenas con el nombre correcto y el origen equivocado, y el defecto puede volver de un solo `git revert` mal leído (§4.2) |
| **D-8** | ¿Se aprovecha para cotejar la **biblioteca** de la traza (H-3)? | (a) no, es F-013; (b) sí | **(a)**. Mezclaría dos fichas y reabriría el asunto de las 133 trazas de IT, que el humano tiene abierto para F-013 |

## 12 · Verificación manual (humano)

Ninguna parte de esta feature **necesita** BBDD ni ERP para probarse: los dos
pasos y los dos endpoints se prueban enteros con los puertos inyectados, que es
la costura de test que los dos handlers declaran en su cabecera. Lo que sí hace
falta verificar a mano, y solo eso:

- **V1** · que los dos 409 nuevos se ven en pantalla y no tumban la tanda. **No
  se puede hacer con `func start` a secas**: con `CIERRE_HABILITADO` apagado la
  respuesta es 503 antes de llegar a ninguna puerta (D-6 de `requirements.md`).
  Se hace con el front local contra un backend con los puertos dobles, o se
  acepta como cubierta por los tests de R32 y se declara;
- **V2** · en el entorno desplegado, con la ventana de escritura abierta y
  **solo con un parte que el humano autorice**: un `/api/adjuntar` y un
  `/api/cerrar` **en dry-run** (`commit` ausente) de un parte normal, y
  comprobar que la reclamación y el nombre del fichero del dry-run son los
  mismos que antes de la feature. **No escribe nada**: el dry-run es una
  lectura. Es la única comprobación contra el ERP real y va con autorización
  explícita.

Las dos están en `tasks.md` como `Verificación: MANUAL (humano)` con su comando.

## 13 · Riesgos

| # | Riesgo | Mitigación |
|---|---|---|
| 1 | Un parte `aprobado` cuyo número de incidencia guardado esté vacío deja de poder adjuntarse y cerrarse aunque el cuerpo lo traiga | Es lo correcto (R15) y coincide con la regla de F-026: un código ilegible **no se aprueba, se teclea**. El 409 dice qué falta |
| 2 | Al retirar la `TrazaArchivo` del borde, algún otro consumidor de `ctx.archivo` en esos dos pasos se queda sin dato | Medido: los únicos consumidores son `paso_grafico.py:289` y `paso_cierre.py:247`, y los dos los sustituye la puerta compartida. Lo vigila un test de alcance |
| 3 | Extraer `CodigosDelParte` de `paso_archivo` rompe F-031 | El cambio es **solo el `import`** (R26) y lo vigilan los tests de F-031 y F-006 sin tocarles el contenido. Si `test_f031_alcance_cerrado.py` se pusiera rojo por esto, se para y se consulta: sus controles son de `diff` y se auto-desactivan fuera de su rama, así que **no debería** |
| 4 | El cotejo en 1 bis rompe algún test existente de F-012 o F-009 que use un cuerpo distinto de la situación | Medido como probable: varios tests construyen `SituacionParte()` vacía o con otros códigos. Se adaptan en su tarea, **sin relajar el cotejo**, y el diff de tests se revisa a ojo |
| 5 | El 409 nuevo confunde a quien ya conocía el 409 de «no apto» o el de «no archivado» | Errores y mensajes propios (§3.2), y cada mensaje dice la acción concreta |
| 6 | Un cliente que hoy manda `estado_archivo=pendiente` por descuido y funcionaba deja de funcionar | No: R7 dice que manda lo guardado y ese caso **pasa**. Tiene test |
