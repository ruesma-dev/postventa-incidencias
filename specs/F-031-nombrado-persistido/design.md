<!-- specs/F-031-nombrado-persistido/design.md -->
# F-031 · El nombrado del fichero archivado sale del cuerpo, no de lo persistido — Diseño técnico

> Servicios: `services/postventa-api/` (backend) y `services/postventa-front/`
> (front). Encaja en `docs/ARCHITECTURE.md` paso 5 (nombrado) y paso 6
> (archivo), y en la semántica 8 («el nombre del fichero es
> `<cod obra> - <cod incidencia> PARTE FIRMADO.pdf`»). Cumple
> `docs/CONVENTIONS.md`: dominio sin dependencias, la aplicación orquesta, la
> composición vive en el borde.
>
> **Esta spec no ha escrito en ningún sistema.** Todo lo que declara como
> medido sale de leer el árbol del repositorio en `dev`, commit `7b013ff`. No
> se ha tocado SharePoint, Sigrid, Azure ni PostgreSQL.
>
> **Orden decidido por el humano el 2026-09-18**: F-033 → **F-031** → F-034 →
> F-013. F-033 está cerrada y desplegada; F-013 está aprobada y espera a esta.

## 0 · Dónde está el riesgo

### 0.1 · Qué se rompe si esto sale mal

| Fallo | Qué se ve | Por qué es grave |
|---|---|---|
| El PDF acaba en la carpeta de **otra obra** | Nada, hasta que alguien lo busque | Lleva el DNI manuscrito de un cliente, y nuestra traza dirá `archivado` |
| Se nombra con el código **viejo** una corrección recién hecha | La persona cree que su corrección se aplicó | Silencioso. Es el fallo que introduciría esta feature si se hiciera solo el backend (§1.3) |
| L1 de F-033 corta para siempre lo mal archivado | Reintentar no arregla nada | Una traza `archivado` no se pisa (F-033 R17) y no hay forma de forzar el re-archivo (F-033 R21) |
| Se rompe la puerta de estado al tocar `ctx.situacion` | Un parte no aprobado se archiva | Es lo único que separa un parte que nadie ha mirado de un PDF subido a SharePoint |

Ninguno produce un error ruidoso por sí solo. Por eso el diseño elige siempre
**no archivar y decir por qué** antes que archivar con un dato dudoso.

### 0.2 · Rigor `critico`

La ficha lo declara. En la práctica: cobertura de las líneas cambiadas sobre el
umbral, fase RED sobre R1, R3, R5 y R18, campaña de mutación **sin
supervivientes sin justificar** sobre `paso_archivo.py`, `nombrado.py`,
`archivar.py` y el módulo nuevo, y las verificaciones `MANUAL (humano)` de §12
con su comando y su resultado real.

## 1 · Lo medido

### 1.1 · El dato correcto ya está delante del nombrado

| Pregunta | Respuesta | Fuente **[MEDIDO]** |
|---|---|---|
| ¿Qué usa hoy el nombrado? | Los códigos del cuerpo, metidos en una `ExtraccionParte` de pega | `interface_adapters/api/archivar.py:196-200`; `application/pipelines/paso_archivo.py:199-203, 460-470` |
| ¿Están los códigos guardados en la consulta de situación? | **Sí**, desde F-030 | `infrastructure/persistencia/sentencias.py:635` (`p.codigo_obra, p.numero_incidencia`) |
| ¿Dónde acaban? | En `ResultadoValidacion.codigo_obra` / `.numero_incidencia` | `infrastructure/persistencia/mapeo.py:432-433`; el modelo, en `domain/models/validacion.py:178-179` |
| ¿Están disponibles cuando se nombra? | **Sí**: la puerta corre antes y deja la situación en `ctx.situacion` | `puerta_de_estado.py:145`; `paso_archivo.py:197` va antes de `:199` |
| ¿De qué tabla salen? | `postventa.partes`, no `validaciones`: ahí no hay copia | `sql/03_partes.sql` (columnas `codigo_obra`, `numero_incidencia`) |
| ¿Vienen saneados? | **Sí**, F-032 los sanea al leerlos, antes de guardarlos | `domain/models/extraccion.py:76-107` (`sanear_valor_leido`) |
| ¿Cuesta alguna consulta traerlos? | **Ninguna** | Son dos columnas de la sentencia que ya se ejecuta |

**Esto es lo que abarata la feature**: no hay columna nueva, ni sentencia
nueva, ni método nuevo en `RepositorioPartesPort`, ni DDL. Al revés que F-033.

### 1.2 · El front, medido

| Pregunta | Respuesta | Fuente **[MEDIDO]** |
|---|---|---|
| ¿Dónde se corrige un campo? | `editarCampo` → `parte.ediciones` + autoguardado | `js/app.js:428-435` |
| ¿Cuándo se guarda? | Rebote de **1.500 ms** desde la última pulsación | `js/autoguardado.js:99-291`; `js/config.js:64` |
| ¿Qué manda el cuerpo de `/api/archivar`? | La edición si la hay, si no lo que leyó la IA | `js/pipeline.js:386-393, 469-470` |
| ¿Espera el archivado a que se guarde? | **No.** `confirmarArchivo` calcula la tanda y la lanza | `js/app.js:703-746` |
| ¿Hay algo que sepa si queda pendiente? | Sí, `hayPendiente`, y **no lo llama nadie** | `js/autoguardado.js:283`; `grep hayPendiente js/app.js` → 0 líneas |
| ¿Basta `parte.guardado`? | **No**: es verdad desde el primer guardado y no caduca al escribir encima | `js/pipeline.js:450-457` |

### 1.3 · Por qué las dos mitades van juntas

Sin tocar el front, mover el nombrado a lo persistido **empeoraría** el caso de
la corrección reciente: hoy archiva con el valor corregido y deja la base con
el viejo (ruidoso el día que alguien compare); con solo el backend archivaría
con el **viejo** sin que nadie se entere. La combinación que sí es una mejora
en los dos escenarios es: **nombrar con lo guardado + cotejar lo declarado +
forzar el guardado antes de la tanda**. Las tres piezas, o ninguna.

## 2 · Ficheros

### 2.1 · A crear

| Ruta | Capa | Qué |
|---|---|---|
| `services/postventa-api/tests/test_f031_nombrado_persistido.py` | tests | R1, R2, R7, R8, R12 sobre `paso_archivo` con dobles |
| `services/postventa-api/tests/test_f031_cotejo_de_codigos.py` | tests | R3, R4, R5, R6, R10, R11 desde `POST /api/archivar` |
| `services/postventa-api/tests/test_f031_alcance_cerrado.py` | tests | R29: `adjuntar.py`, `cerrar.py`, `paso_grafico.py`, `paso_cierre.py` y el SQL sin tocar |
| `services/postventa-front/tests_js/autoguardado_vaciado.test.js` | tests | R18, R20, R21, R22 sobre el método nuevo del autoguardado |

Los tests del front nuevos podrían ir dentro de `tests_js/autoguardado.test.js`;
van en fichero propio para que el diff de la feature se lea de un vistazo y
para no engordar un fichero que ya cubre F-026.

### 2.2 · A modificar

| Ruta | Qué cambia |
|---|---|
| `services/postventa-api/domain/models/nombrado.py` | **Una función nueva**, pura: `es_el_mismo_codigo(uno, otro) -> bool`, que normaliza los dos con `normalizar_codigo` y compara. Nada más se toca (§3.1) |
| `services/postventa-api/domain/models/errores.py` | `CodigosNoCoinciden(Exception)` con `.motivo`, hermana de `ParteNoApto` y `NombradoImposible` (§3.2) |
| `services/postventa-api/application/pipelines/paso_archivo.py` | El nombrado toma los códigos de `ctx.situacion`; el cotejo contra lo declarado; `_campo` desaparece (§4) |
| `services/postventa-api/interface_adapters/api/archivar.py` | Deja de meter los códigos en la `ExtraccionParte` de pega y los pasa **explícitos** al paso (§5) |
| `services/postventa-api/function_app.py` | `CodigosNoCoinciden` se suma al `except` que ya traduce a **409** (§5.2) |
| `services/postventa-front/js/autoguardado.js` | Método `vaciarPendientes()` (§6.1) |
| `services/postventa-front/js/app.js` | `confirmarArchivo` lo espera antes de calcular y lanzar la tanda (§6.2) |
| `services/postventa-api/tests/test_f006_archivar_http.py` | El caso del cuerpo con `06\|77` cambia de motivo: hoy es nombrado imposible, mañana es cotejo. Se conserva **además** un caso de nombrado imposible con el código **guardado** corrupto (§9) |
| `docs/ARCHITECTURE.md` | Recuadro fechado en el paso 6 y en la semántica 8: de dónde salen los dos códigos (§10) |
| `specs/F-006-sharepoint/design.md` y `specs/F-030-veredicto-persistido/design.md` §10.7 | Nota de cierre del hallazgo, con la fecha (§10) |
| `CHECKPOINTS.md` | Nada. Se cita, no se toca |

### 2.3 · Lo que NO se toca (y tienta)

- **`domain/models/nombrado.py` salvo la función de §3.1.** Las cuatro reglas,
  el sufijo, los separadores y `nombre_admisible` se quedan letra por letra
  (R12). Esta feature cambia de dónde salen las entradas, no qué se hace con
  ellas.
- **`domain/models/estado.py` y `SituacionParte`.** No gana campos: los dos
  códigos ya viajan dentro de `validacion` (§3.3, D-1).
- **`domain/ports/persistencia.py`.** Ni un método más.
- **`infrastructure/persistencia/` entero**: sentencias, mapeo, repositorio y
  todo el SQL. Ni una columna, ni un `JOIN`, ni un `NN_nombre.sql` nuevo (R17).
- **`application/pipelines/puerta_de_estado.py`.** La puerta sigue exactamente
  igual; esta feature **usa** lo que deja en `ctx.situacion` y no cambia cómo lo
  deja.
- **Las tres capas de F-006 y la enmienda de F-033** (L1, reemplazo, carpeta) y
  la garantía de orden de F-019. El orden de los ocho pasos de `paso_archivo`
  no se altera: solo cambia de dónde salen dos cadenas en el paso 2, y se
  intercala el cotejo **antes** (§4.2).
- **`domain/models/aprobacion.py`** y la huella del veredicto (R16).
- **`/api/adjuntar`, `/api/cerrar`, `paso_grafico.py`, `paso_cierre.py`.**
  Tienen el mismo defecto de familia (§8, H-1) y no son de esta ficha.
- **`js/pipeline.js`.** Es lógica pura y no conoce el autoguardado; meter ahí la
  espera lo ataría a un temporizador (§6.3, alternativa descartada).
- **`js/confirmacion.js`.** La confirmación única de F-025 no se toca: el
  vaciado va después de resolverla y antes de la tanda (§6.2).
- **El terreno de F-013.** Ver §7.2: esta feature deja los dos códigos resueltos
  **en un solo sitio dentro del paso**, que es de donde F-013 los tomará.

## 3 · Dominio

### 3.1 · `es_el_mismo_codigo` (dominio puro)

```python
# domain/models/nombrado.py
def es_el_mismo_codigo(uno: str | None, otro: str | None) -> bool:
    """¿Son dos formas de escribir el mismo código? (F-031 R4)."""
    return normalizar_codigo(uno) == normalizar_codigo(otro)
```

Vive aquí y no en el paso por el motivo que este módulo ya tiene escrito: **el
dueño de «qué es el mismo código» es quien lo normaliza**, y dos criterios del
mismo concepto divergen siempre (F-028 R47, F-032). Con esto, el día que
`normalizar_codigo` cambie —ya cambió una vez, el 2026-09-17— el cotejo se
mueve con él y no hay que acordarse de nada.

Dos códigos vacíos dan `True`. No es un descuido: el caso «los dos vacíos» lo
decide R7 un paso más adelante (`NombradoImposible` diciendo cuál falta), y
hacer que el cotejo también opine sobre él produciría dos errores distintos
para el mismo hecho.

### 3.2 · `CodigosNoCoinciden`

```python
# domain/models/errores.py
class CodigosNoCoinciden(Exception):
    """Lo declarado en la petición no es lo que consta guardado (F-031 R3)."""
    def __init__(self, motivo: str) -> None: ...
    motivo: str
```

Excepción propia y no `ParteNoApto` reutilizada: los dos son 409, pero llevan a
acciones **opuestas**. `ParteNoApto` se arregla decidiendo sobre el parte;
esto se arregla **guardando la corrección** y volviendo a intentarlo. Es la
misma razón por la que existen `ParteNoArchivado`, `ArchivoSinTraza` y
`ReferenciaNoConsta`, cada una con su docstring diciéndolo.

El `motivo` nombra **qué campo** no coincide y con qué valores, y nada más
(R25): un 409 que no lo dice obliga a mirar la base a mano.

### 3.3 · Por qué los códigos se leen de `situacion.validacion`

`ResultadoValidacion` ya declara, en su propio docstring, que sus dos campos de
código son «los dos campos decisivos, tal y como se leyeron» y que «entran en
la huella del veredicto». Leer el nombre de **ese mismo objeto** da una
propiedad que ningún otro camino da gratis: **el fichero se nombra, byte por
byte, con los valores que la puerta acaba de aprobar**. Es exactamente lo que
la ficha pide cerrar.

Que ese objeto se llame «validación» y traiga dos columnas de `partes` es una
rareza heredada de F-030 y está declarada como decisión abierta **D-1** (§11).

## 4 · El paso de archivo

### 4.1 · Los códigos, resueltos una vez

```python
# application/pipelines/paso_archivo.py
@dataclass(frozen=True)
class CodigosDelParte:
    """Los dos códigos que deciden carpeta y nombre. **Los guardados** (R1)."""
    codigo_obra: str
    numero_incidencia: str


def _codigos_guardados(ctx: ContextoParte) -> CodigosDelParte: ...
```

`_codigos_guardados` lee de `ctx.situacion.validacion`, que la puerta acaba de
dejar puesta. Si `validacion` fuera `None` devuelve dos cadenas vacías y el
nombrado se niega diciendo cuál falta (R7): **no se añade una guardia
inalcanzable**, que es lo que `nombre_admisible` ya razona en su docstring —la
puerta levanta `ParteNoApto` antes de llegar aquí—.

Un único punto de lectura, con nombre, es lo que hace que F-013 no tenga que
volver a decidir de dónde salen (§7.2).

### 4.2 · El orden, que es la mitad del requisito

Los ocho pasos de `paso_archivo` se conservan y se intercala **uno**:

```
1. Puerta de aptitud            (F-028; deja ctx.situacion)
1 bis. COTEJO de los códigos    ← F-031 R3, R5  (nuevo)
2. Nombrado                     ← ahora con los códigos GUARDADOS (R1)
3. L1 · idempotencia por traza  (F-033)
4. Traza previa en `pendiente`  (F-019)
5. asegurar_carpeta
6. buscar el homónimo
7. subir
8. Traza final
```

El cotejo va en **1 bis** y no más abajo, y es un requisito (R5): a partir del
paso 4 ya hay una fila escrita en `postventa.archivos`, y a partir del 5 ya se
ha hablado con SharePoint. Un cotejo que fallara después dejaría rastro de un
archivado que nunca debió intentarse.

Va **después** de la puerta y no antes porque necesita la situación que la
puerta lee: sin ella no hay con qué cotejar, y adelantarlo obligaría a una
segunda consulta (contra R2).

### 4.3 · Firma

```python
def paso_archivo(
    ctx: ContextoParte,
    archivador: ArchivoPort,
    repositorio: RepositorioPartesPort,
    *,
    carpeta_base: str,
    ahora: datetime,
    drive_id_vigente: str | None = None,
    codigos_declarados: CodigosDelParte | None = None,   # ← nuevo
) -> ContextoParte:
```

`codigos_declarados` es **lo que afirma quien llama**, y solo sirve para el
cotejo de R3. Opcional para que los tests que no hablan de cuerpos no tengan
que inventarse uno; el borde lo pasa siempre. Cuando es `None`, no hay nada que
cotejar y el nombrado usa lo guardado igual: **el camino sin cotejo no puede
archivar con otros códigos** (R11).

`_campo(ctx, nombre)` **desaparece**: era el único consumidor de
`ctx.extraccion` en este paso, y dejarlo sería dejar viva la segunda fuente que
la feature viene a cerrar. Es la misma decisión que F-033 tomó con
`traza_previa` (su D-2).

### 4.4 · El cotejo

```python
def _exigir_codigos_declarados(
    declarados: CodigosDelParte | None, guardados: CodigosDelParte
) -> None:
    """R3, R4 · lo declarado tiene que ser lo guardado, o no se archiva."""
```

Compara campo a campo con `es_el_mismo_codigo`. Levanta `CodigosNoCoinciden`
nombrando el primero que falla, con los dos valores y con la acción concreta:
guardar el parte (`POST /api/parte`) y volver a intentarlo.

## 5 · El borde

### 5.1 · `interface_adapters/api/archivar.py`

Dos cambios, y el segundo es la mitad del valor:

1. `archivar_parte` construye `CodigosDelParte(codigo_obra=…,
   numero_incidencia=…)` con lo que trae el cuerpo y lo pasa como
   `codigos_declarados`.
2. `_como_contexto` **deja de rellenar** `codigo_obra` y `numero_incidencia` en
   la `ExtraccionParte` de pega: los nueve campos van vacíos. Con eso, ese
   objeto deja de ser una fuente de datos y pasa a ser lo que decía F-030 que
   era: un contexto mínimo con el `hash` y los bytes.

`CAMPOS_OBLIGATORIOS` no cambia (R10): los cinco siguen siendo obligatorios y
un cuerpo incompleto sigue siendo 400 (R6). Lo que cambia es **para qué
sirven** dos de ellos, y el docstring del módulo lo dirá con el mismo formato
de enmienda fechada que ya usan F-030 y F-033.

### 5.2 · `function_app.py`

`CodigosNoCoinciden` se añade al `except (ParteNoApto, NombradoImposible)` que
ya devuelve **409**. Ni un código HTTP nuevo, ni una clave nueva en el cuerpo
de la respuesta (R26): `{"error": <motivo>}`, como sus dos hermanas.

Y se amplía el comentario que documenta los códigos del endpoint —**400** mal
formada, **409** no se puede archivar tal y como está, **503** aquí y ahora no,
**502** el proveedor, **500** se subió y no hay traza— para que el 409 nuevo
quede dentro de la familia que ya está explicada ahí.

## 6 · El front

### 6.1 · `js/autoguardado.js` · `vaciarPendientes()`

```js
/**
 * F-031 R18 · fuerza lo que esté escrito y sin guardar, y espera.
 * @returns {Promise<{ok: boolean, motivo: string}>}
 */
vaciarPendientes()
```

Qué hace, en este orden:

1. **espera al guardado en vuelo**, si lo hay. El módulo ya tiene la bandera
   `enVuelo`; hace falta además **guardar la promesa** para poder esperarla, que
   hoy no se conserva;
2. **cancela el temporizador** en espera y **dispara** el guardado de lo que
   quede pendiente, y lo espera;
3. repite como mucho **dos rondas más**. Hay tope a propósito: `disparar` se
   reprograma cuando encuentra un guardado en vuelo, y un bucle sin tope podría
   no terminar nunca con alguien tecleando delante;
4. devuelve `{ok: false, motivo}` si al acabar **sigue quedando** algo distinto
   de lo guardado, y `{ok: true}` si no.

Tres cosas que **no** hace:

- **no toca `parte.ediciones`** (R21): lo escrito se queda donde está pase lo
  que pase, exactamente como ya promete F-026 R52 y R53;
- **no dispara nada si no hay cambios** (R22): reutiliza el `hayCambios` que ya
  existe, así que pulsar «archivar y cerrar» sin haber corregido nada no cuesta
  ni una petición contra el PostgreSQL compartido;
- **no mira el veredicto ni el estado** de ningún parte: el módulo sigue sin
  saber qué es eso (F-026 R55).

Vive aquí y no en `app.js` por lo que ya dice la cabecera del módulo: lo que se
puede probar con `node --test` no se deja en el fichero de Alpine.

### 6.2 · `js/app.js` · `confirmarArchivo`

```js
this.avisoArchivo = "";

const vaciado = await this._autoguardado().vaciarPendientes();   // R18
if (!vaciado.ok) {                                               // R20
  this.avisoArchivo = AVISO_SIN_GUARDAR;
  return;                                                        // la tanda NO se lanza
}

const tanda = this.pendientes();                                 // R19: DESPUÉS
```

Las dos precisiones que importan:

- **el vaciado va antes de `this.pendientes()`** (R19). Guardar revalida
  (`revalidarYGuardar`, F-026 R50), y una corrección puede tumbar un veredicto:
  una tanda calculada antes archivaría un parte que acaba de dejar de ser
  archivable;
- **va después de `Confirmacion.resolver`**, así que ni alarga ni reinicia la
  ventana de la confirmación única de F-025. Si el vaciado falla, la
  confirmación ya está consumida y hay que volver a confirmar: correcto, porque
  lo que se va a archivar ha cambiado.

`AVISO_SIN_GUARDAR` dice las dos cosas que hacen falta: que **no** se ha
archivado nada y que lo escrito sigue en pantalla. Se apoya en el mensaje que
F-026 ya tiene para el fallo de autoguardado, para no dar dos explicaciones del
mismo hecho.

### 6.3 · Alternativas descartadas en el front

| Alternativa | Por qué no |
|---|---|
| Bloquear el botón mientras `hayPendiente` | El rebote es de 1,5 s: el botón parpadearía mientras alguien escribe, y no resuelve la corrección hecha justo antes de pulsar |
| Guardar en cada pulsación (rebote a 0) | Una escritura por tecla contra un PostgreSQL compartido con albaranes. Es justo lo que F-026 evitó |
| Meter la espera en `js/pipeline.js` | Es lógica pura y no conoce el autoguardado; atarlo a un temporizador le quitaría sus tests |
| No tocar el front y fiarlo todo al 409 | Convierte el caso normal —corregir y archivar— en un error que la persona tiene que entender y repetir |

## 7 · Encaje y límites

### 7.1 · Límite de microservicio

Esta feature vive **entera** dentro de `postventa-incidencias`: mueve el origen
de un dato dentro de su propio backend y ajusta su propio front. No cruza
ninguna frontera del ecosistema: no llama a `sigrid-api`, no toca el catálogo
de `front-portal`, no cambia nada del PostgreSQL compartido y no cambia lo que
este proyecto expone ni consume, así que **no hay que actualizar
`azure-apps/postventa_incidencias.md`** (se comprueba en T11 y se deja dicho
aunque el resultado sea «no hay nada que tocar»).

Que toque dos carpetas de `services/` **no** rompe la regla de «una feature no
mezcla responsabilidades de dos servicios»: la responsabilidad es una sola —de
dónde salen los dos códigos que deciden dónde acaba un PDF— y el front no gana
ninguna lógica de dominio; gana una espera. Partirla en dos fichas dejaría
desplegada durante un tiempo la mitad que **empeora** el caso de la corrección
reciente (§1.3), que es precisamente lo que no puede pasar.

### 7.2 · Terreno preparado para F-013, sin duplicar nada

F-013 §2.3 declara, literal, que **no** toca «el origen de los códigos de
F-031», y su §8.2 (D-3) dice que F-013 «usa `codigo_obra` y `numero_incidencia`
tal y como llegan al paso» y que **F-031 decide de dónde salen**. El orden que
el humano fijó —F-031 antes que F-013— es para que F-013 herede la fuente
correcta sin volver a decidirla.

Lo que esta feature deja preparado, y es todo lo que F-013 necesita:

- **un solo punto de lectura**, `_codigos_guardados(ctx)`, dentro de
  `paso_archivo`. El `resolver_destino` de F-013 se llama **desde este paso**
  (su §2.2: «parámetro opcional `resolver_destino`; si llega, sustituye a
  `componer_destino` + `asegurar_carpeta`»), así que recibirá esos dos códigos
  y no tendrá que buscarlos;
- **la pieza que F-013 llama `codigo_obra` en su R8** —«la obra que dice Sigrid
  para ese número tiene que ser la del parte»— pasa a contrastarse contra el
  código **guardado**, que es lo que F-013 esperaba y lo que cierra el hueco que
  su §8.2 dejaba escrito («lo que **no** cubre es un cuerpo que mienta en los
  dos de forma coherente»);
- **nada que F-013 tenga que deshacer**: no se crea ningún módulo nuevo de
  aplicación que compita con su `destino_archivo.py`, no se toca
  `nombre_de_archivo` ni `carpeta_de_archivo`, y no se añade nada a
  `postventa.archivos`.

Y lo que esta feature **no** hace, para no pisar F-013: no mira la estructura de
la biblioteca, no consulta la unidad ni la obra en Sigrid, no crea carpetas y no
distingue `por_obra` de `posventa`.

### 7.3 · Encaje con F-032

F-032 sanea los dos códigos **al leerlos**, así que lo guardado en
`postventa.partes` nace sin espacios (`domain/models/extraccion.py:76-107`).
Dos consecuencias directas:

1. **el nombrado desde lo persistido hereda el saneo gratis**: la fuente ya está
   limpia, y `normalizar_codigo` dentro de `nombre_de_archivo` deja de ser la
   última red y pasa a ser una confirmación;
2. **el cotejo tiene que normalizar los dos lados** (R4). El front manda lo que
   `valorDeCampo` devuelve, que solo hace `trim()`
   (`js/pipeline.js:386-393`): un cuerpo con `RS 26.09/0178` contra una base con
   `RS26.09/0178` es el **mismo** código y no puede ser un 409. Ese es
   exactamente el caso que costó un cierre a mano el 2026-09-17.

### 7.4 · Encaje con F-033

F-033 es la razón por la que este diseño aborta **antes** de la traza previa
(R5). Con L1 cortando por `hash` + estado y sin forma de forzar el re-archivo
(su D-1 y su R21), un parte archivado en la carpeta equivocada **no se puede
arreglar desde el circuito**. El coste de equivocarse aquí es permanente, y eso
manda sobre todas las decisiones de §11.

## 8 · Hallazgo, fuera de alcance

**H-1 · `/api/adjuntar` y `/api/cerrar` nombran y eligen con el cuerpo.**
**[MEDIDO]**:

- `interface_adapters/api/adjuntar.py:94-95, 107-108, 148-149, 172-173` pasa
  `codigo_obra` y `numero_incidencia` **del cuerpo** al paso del gráfico;
- `application/pipelines/paso_grafico.py:116-117, 157, 175-176` los usa para
  **nombrar el fichero** que se adjunta y para **localizar la reclamación**;
- `interface_adapters/api/cerrar.py:100, 149` toma `numero_incidencia` del
  cuerpo y `application/pipelines/paso_cierre.py:117, 155` lo convierte en el
  código con el que se busca la reclamación **que se va a cerrar en el ERP de
  producción**;
- el front los manda con el mismo `valorDeCampo` (`js/pipeline.js:624-627`,
  `:537`).

Es la misma familia que F-030 y que esta ficha, y es **más grave**: aquí lo que
está en juego no es en qué carpeta acaba un PDF, sino **qué incidencia se
cierra**. No entra en F-031 por decisión del humano (el alcance de esta ficha es
el nombrado del fichero archivado) y **no lo cubre F-034**, cuyo `acceptance`
habla solo del `estado_archivo` del cuerpo.

**Recomendación**: ampliarlo al `acceptance` de **F-034**, que ya va a tocar
esos dos endpoints y ya va a leer la situación persistida, en vez de abrir una
ficha más. Se anota en `progress/current.md` para que lo decida el humano.

## 9 · Tests: qué cambia de lo que ya hay

| Test existente | Qué le pasa |
|---|---|
| `tests/test_f006_archivar_http.py:341` (cuerpo con `06\|77`) | Hoy espera 409 por nombrado imposible. Con F-031 el 409 será **por cotejo**: el cuerpo dice `06\|77` y la base dice `0677`. Se adapta el motivo esperado |
| Nombrado imposible por carácter prohibido | **Se conserva y se refuerza**: caso nuevo con el código **guardado** corrupto (`06\|77` en la situación) y el mismo en el cuerpo. Así el camino de R8 sigue siendo alcanzable y sigue teniendo test |
| `tests/test_f033_archivar_http.py`, `tests/test_f030_circuito_borde_a_borde.py`, `tests/test_f019_orden_archivado.py`, `tests/test_f006_paso_archivo.py` | El cuerpo y la situación ya usan los mismos valores (`0677` / `RS26.08/0123`, o `0626` / `RS26.09/0178`), así que **pasan sin cambios**. Los que construyan `SituacionParte()` vacía y esperen archivar tendrán que traer veredicto, que es lo que `utiles_validacion.veredicto_apto` ya da |
| `tests/utiles_validacion.py::veredicto_apto` | **No se toca**: ya sale de `validar_parte` sobre `CAMPOS_DE_EJEMPLO`, que trae `codigo_obra="0677"` y `numero_incidencia="RS26.08/0123"` (`tests/utiles_ia.py:46,48`) |
| `tests_js/pipeline.test.js` | `cuerpoDeArchivo` no cambia: los dos campos siguen viajando |

Ningún test toca red, BBDD ni IA (R28). La guardia de red de la suite sigue en
pie y ningún test construye un adaptador capaz de llegar a Graph.

## 10 · Documentación a actualizar

- `docs/ARCHITECTURE.md` · paso 6 y semántica 8: recuadro **«Precisado por
  F-031 el 2026-09-22»** diciendo que la carpeta y el nombre salen del
  `codigo_obra` y el `numero_incidencia` **guardados**, y que lo que venga en el
  cuerpo solo puede cerrar la puerta. Mismo formato que los de F-030, F-032 y
  F-033.
- `specs/F-030-veredicto-persistido/design.md` §10.7 · nota de cierre del
  hallazgo, con la fecha y el puntero a esta carpeta.
- `specs/F-006-sharepoint/design.md` · nota al margen del nombrado.
- `azure-apps/postventa_incidencias.md` · **nada**, y se deja escrito por qué
  (§7.1).

## 11 · Decisiones abiertas, con recomendación

> Todas tienen recomendación y ninguna bloquea la escritura de la spec. El
> implementer **no arranca** hasta que el humano cierre D-1, D-3 y D-5.

| Id | Pregunta | Opciones | **Recomendación** |
|---|---|---|---|
| **D-1** | ¿De dónde lee el paso los códigos guardados? | (a) de `ctx.situacion.validacion`, que ya los trae; (b) dos campos nuevos en `SituacionParte`, leídos de las **mismas** dos columnas | **(a)**. Cuesta cero, y da la propiedad que la ficha pide: el fichero se nombra con lo que la puerta acaba de aprobar, sin un segundo camino que pueda divergir. (b) es más bonito de leer —«el código del parte no es del veredicto»— pero mete **dos representaciones del mismo dato en el mismo objeto**, que es justo lo que este repositorio evita en todas partes |
| **D-2** | ¿Cómo llega al paso lo declarado en el cuerpo? | (a) parámetro explícito `codigos_declarados`; (b) seguir metiéndolo en la `ExtraccionParte` de pega | **(a)**. (b) conserva una `ExtraccionParte` que dice «esto leyó la IA» conteniendo lo que escribió un formulario, que es la confusión que dejó el defecto |
| **D-3** | ¿Qué se hace si el cuerpo difiere de la base? | (a) **409** y no se archiva; (b) se archiva con lo guardado y se añade un aviso; (c) se ignora en silencio | **(a)**. (b) archivaría con el código viejo una corrección recién hecha, y el aviso llega **después** de que el PDF esté subido y con L1 cortando el arreglo (§7.4). (c) es el fallo silencioso que la ficha viene a cerrar |
| **D-4** | ¿Siguen siendo obligatorios los dos campos del cuerpo? | (a) sí, pasan a cotejar; (b) se retiran del contrato | **(a)**. Retirarlos cambiaría el contrato HTTP, obligaría a tocar el front por otro motivo y **perdería la detección** de R3: sin lo declarado no hay con qué cotejar |
| **D-5** | ¿Qué hace el front antes de archivar? | (a) forzar el guardado y esperar; (b) bloquear el botón mientras haya pendiente; (c) no tocarlo y fiarlo al 409 | **(a)**, con (c) debajo como red. §6.3 razona (b) |
| **D-6** | H-1 (`/api/adjuntar` y `/api/cerrar` con los códigos del cuerpo) | (a) ampliar el `acceptance` de F-034; (b) ficha nueva; (c) dejarlo escrito y no hacer nada | **(a)**. F-034 ya toca esos dos endpoints y ya lee la situación persistida |
| **D-7** | ¿El cotejo compara literal o normalizado? | (a) normalizado con `normalizar_codigo`; (b) literal | **(a)**. Con (b), `RS 26.09/0178` contra `RS26.09/0178` daría 409 y convertiría en error el caso que F-032 declaró explícitamente que es **el mismo código** |

## 12 · Verificación manual (humano)

Ninguna parte de esta feature **necesita** BBDD para probarse: el paso, el
borde y el front se prueban enteros con dobles. Lo que sí hace falta verificar a
mano, y solo eso:

- **V1** · que el 409 nuevo se ve tal cual en la pantalla, con el front y el
  backend locales (`func start` + `dev_server.py`), corrigiendo un código y
  pulsando archivar sin esperar. **No sube nada**: `ARCHIVO_HABILITADO` está
  apagado en local y el endpoint responde 503 antes de tocar Graph;
- **V2** · en el entorno desplegado y con un parte autorizado por el humano:
  que un archivado normal sigue produciendo el mismo nombre y la misma carpeta
  que antes de la feature. Es la única comprobación que toca la biblioteca real,
  y va con dry-run previo y confirmación explícita.

Las dos están en `tasks.md` como `Verificación: MANUAL (humano)` con su comando.

## 13 · Riesgos

| # | Riesgo | Mitigación |
|---|---|---|
| 1 | Un parte `aprobado` cuyo código guardado esté vacío deja de poder archivarse aunque el cuerpo lo traiga | Es lo correcto (R7) y coincide con la regla de F-026: un código ilegible **no se aprueba, se teclea**. El 409 dice qué falta y tecleando + guardando se arregla |
| 2 | Al retirar `_campo`, algún otro consumidor de `ctx.extraccion` en el paso se queda sin dato | Medido: `_campo` es el **único** consumidor en `paso_archivo.py` (líneas 460-470, usado en 200-202) |
| 3 | El vaciado del front alarga el tiempo hasta la primera petición | Como mucho un rebote (1,5 s) más un guardado. Frente a una tanda de 22 partes con tres escrituras cada uno, es ruido |
| 4 | `vaciarPendientes` se queda en bucle con alguien tecleando | Tope de rondas (§6.1) y `{ok:false}` que **no lanza la tanda** |
| 5 | Tocar `confirmarArchivo` rompe la confirmación única de F-025 | El vaciado va después de `Confirmacion.resolver` y no toca su estado; `tests_js/confirmacion.test.js` y `circuito.test.js` siguen en verde |
| 6 | El 409 nuevo confunde a quien ya conocía el 409 de «no apto» | Excepción y mensaje propios (§3.2), y el mensaje dice la acción: guardar y reintentar |
