<!-- specs/F-030-veredicto-persistido/design.md -->
# F-030 · La aprobación humana no sobrevive a la puerta de F-028 — Diseño

> Requisitos en `requirements.md`. Rigor **`critico`**.
> Rama: `feature/F-030-veredicto-persistido`, ya creada desde `dev`.

---

## 1 · La idea, en una frase

**Quien trae la extracción emite el veredicto; quien no la trae, lo lee.**

`POST /api/parte` y `POST /api/estado` reciben el parte entero —extracción y
lectura de firma— y emiten el veredicto con las reglas de F-004 en la propia
llamada: son **productores**, y por eso pueden apuntar la huella de lo que
acaban de emitir. `POST /api/archivar`, `POST /api/adjuntar` y
`POST /api/cerrar` **no reciben la extracción y no la van a recibir nunca**
—pedirla obligaría al front a reenviar el DNI y las observaciones manuscritas
del cliente en cada llamada—, así que no pueden emitir el veredicto. Hasta hoy
lo fabricaban de todas formas, con lo poco que tenían y rellenando el resto con
valores fijos. F-030 les quita esa fabricación y les da lo que sí pueden tener:
**el veredicto que está guardado**.

---

## 2 · La huella se recompone con lo que ya hay guardado (§ D3)

La cadena canónica de `huella_de_veredicto`
(`domain/models/aprobacion.py:151-160`) tiene seis campos. **Los seis están
persistidos**:

| # | Campo de la cadena canónica | De dónde sale | Nota |
|---|---|---|---|
| 1 | `destino` | `validaciones.destino` | literal del `Enum`, con `CHECK` |
| 2 | códigos de los motivos, **ordenados** | `validaciones.motivos` (jsonb) | la huella los ordena, así que el orden guardado da igual |
| 3 | `clasificacion_firma` | `validaciones.clasificacion_firma` | literal del `Enum`, con `CHECK` |
| 4 | `observaciones` **normalizadas** | `partes.observaciones` | el DDL de `validaciones` manda traerlas con `JOIN` (R21, R39) |
| 5 | `codigo_obra` normalizado | `partes.codigo_obra` | |
| 6 | `numero_incidencia` normalizado | `partes.numero_incidencia` | |

Y los dos campos de `ResultadoValidacion` que no entran en la huella pero
completan el objeto también están: `veredicto` en `validaciones.veredicto`,
`confianza_observaciones` en `partes.observaciones_confianza_pct` y `avisos` en
`validaciones.avisos`.

**Las tres equivalencias que hacen que esto funcione**, y que son el motivo por
el que la recomposición no puede desviarse, cada una comprobada hoy
**[MEDIDO]**:

1. **`None` y «solo espacios» dan la misma huella.** `validar_parte` pone
   `observaciones=None` cuando el campo está vacío, mientras `partes.observaciones`
   guarda el literal que leyó el modelo, que puede ser `"   "`. `_normalizar`
   los colapsa a la cadena vacía: **misma huella**. Lo mismo vale para
   `codigo_obra` y `numero_incidencia`, que el veredicto normaliza a `""` y la
   base puede guardar como `NULL`.
2. **El orden de los motivos da igual**: `huella_de_veredicto` los ordena por
   código antes de unirlos, y el jsonb los guarda en el orden de emisión.
3. **El recorte de `avisos` a 240 caracteres no afecta**: los avisos **no
   entran** en la cadena canónica.

**Comprobación [MEDIDA] el 2026-09-16** sobre un veredicto con observaciones
con saltos de línea y mayúsculas, código de obra con espacio final, número de
incidencia con espacios alrededor del separador, un motivo y un aviso de 300
caracteres: la huella del objeto original y la del objeto recompuesto a partir
de las columnas (`mapeo.valores_de_validacion` + las tres de `partes`)
coinciden — `db5a879e…` en los dos casos. Y la del stub de `archivar.py` sobre
ese mismo parte sale `9d8596a0…`, que es exactamente la que midió el humano
sobre RS26.09/0178. El guion está en `progress/` como evidencia de la fase RED
(T1); **no se versiona en el repo**.

**Conclusión: no hace falta ninguna columna nueva** y no hay DDL en esta
feature (R20).

---

## 3 · Dónde va la lectura: dentro de la consulta que ya se hace (§ D4)

`SituacionParte` ya es «lo que hace falta saber de un parte para derivar su
estado». Le faltaba **el primer argumento de `estado_del_parte`**. Con F-030
lleva las cuatro cosas, y así el que deriva el estado no puede mezclar una
fuente con otra (R2).

El coste importa porque el PostgreSQL es **compartido** con albaranes y
compañía, y F-028 §11.1 ya se preocupaba de esto: la puerta hace un viaje por
parte y por paso, o sea tres por parte. Un método nuevo `consultar_validacion`
llamado aparte sumaría **tres viajes más por parte**, seis en total.

Se evita así: hoy `consultar_situacion` ejecuta **dos** sentencias —el
`UNION ALL` del histórico y la del estado de cierre—. F-030 **sustituye la
segunda** por una que trae el veredicto y el estado de cierre a la vez,
anclada en `partes`:

```sql
SELECT v.veredicto, v.destino, v.clasificacion_firma, v.motivos, v.avisos,
       p.observaciones, p.observaciones_confianza_pct,
       p.codigo_obra, p.numero_incidencia,
       c.estado
FROM postventa.partes AS p
LEFT JOIN postventa.validaciones AS v ON v.hash_parte = p.hash_parte
LEFT JOIN postventa.cierres     AS c ON c.hash_parte = p.hash_parte
WHERE p.hash_parte = %s
```

**Siguen siendo dos sentencias por llamada: ni un viaje más** (R18).

Tres detalles del `SQL`, y ninguno es de estilo:

- **Se ancla en `partes` y los dos `JOIN` son `LEFT`.** `validaciones` y
  `cierres` tienen `hash_parte` como clave primaria **y** como
  `REFERENCES postventa.partes`, así que ninguna puede tener fila donde no la
  haya en `partes`: anclar ahí no pierde nada. Si se anclara en `validaciones`,
  un parte sin veredicto se llevaría por delante el estado de cierre, y
  entonces un parte **cerrado** sin fila de validación dejaría de dar `cerrado`
  — que es el hecho que gana a todo (R16, R18 de F-028).
- **Sin fila de `partes` no vuelve ninguna fila**, y eso se traduce a veredicto
  `None` y cierre `None`: es exactamente lo que devuelve hoy
  `select_estado_cierre` en ese caso, y de ahí sale el error propio de «no
  consta que este parte haya pasado la validación» (R8, R9).
- **`validaciones` se distingue por `v.veredicto IS NULL`**, no por el
  `hash_parte`: el `hash` de la fila de `partes` siempre viene.

`select_estado_cierre` y el método de puerto `consultar_estado_cierre`
**se quedan como están**: los usan `interface_adapters/api/estado.py:349`
—la puerta del parte cerrado, que va antes de escribir nada— y
`interface_adapters/api/parte.py:234`.

---

## 4 · Ficheros a crear

| Ruta | Qué es |
|---|---|
| `services/postventa-api/tests/test_f030_veredicto_persistido.py` | Las tres puertas contra el veredicto guardado (R1, R2, R7, R8, R9, R11, R12, R14–R17), la ida y vuelta de la huella (R10) y el centinela estructural (R3). |
| `services/postventa-api/tests/test_f030_circuito_borde_a_borde.py` | El test que faltó: decidir → archivar / adjuntar / cerrar con el cuerpo real de los endpoints (R4, R5, R6, R23, R24). |

No se crea ningún `.sql`, ningún módulo de producción y ningún endpoint.

---

## 5 · Ficheros a modificar

### 5.1 · Dominio

**`services/postventa-api/domain/models/estado.py`**

- `SituacionParte` gana un cuarto campo:

  ```python
  validacion: ResultadoValidacion | None = None
  ```

  **Va el último de los cuatro** aunque conceptualmente sea el primero: los
  tests y el código existentes construyen `SituacionParte` por palabra clave,
  pero ponerlo delante rompería cualquier construcción posicional que aparezca
  por el camino, y esta feature no está para eso.
- Se **enmienda** el párrafo de su docstring que dice *«Una cuarta cosa aquí
  sería una invitación a decidir con ella, y lo que se decide se decide en
  `estado_del_parte`»*, con una nota fechada al estilo de las de
  `aprobacion.py`: la cuarta cosa **es** el primer argumento de
  `estado_del_parte`, y tenerla aquí es justo lo que impide decidir con otra.
- `estado_del_parte`, `estado_de_la_maquina`, `_aprueba_lo_que_hay`,
  `decision_en_firme` y `DecisionEstado` **no se tocan**. Siguen siendo puras y
  con la misma firma: lo que cambia es de dónde sale su primer argumento.

**`services/postventa-api/domain/ports/persistencia.py`**

- `consultar_situacion`: la docstring pasa de «tres cosas» a **cuatro**, y dice
  que el veredicto viene del almacén y nunca del cuerpo, igual que la situación.
- `guardar_validacion`: **se enmienda su docstring**, que hoy es la
  descripción literal del defecto. Dice todavía que revoca la aprobación (lo
  retiró F-028 T15; el adaptador ya lleva su enmienda, el puerto no) y, sobre
  todo, sostiene esta premisa: *«los tres pasos del circuito, cuyo cuerpo de
  petición no trae ni los motivos ni las observaciones y por tanto **no
  puede** recomputar la huella»*. Era cierta y dejó de serlo hoy: no la
  recomputan **del cuerpo**, la **leen de la base**. Dejarla ahí es dejar
  escrito el razonamiento que llevó a fabricar el stub.

### 5.2 · Infraestructura de persistencia

**`infrastructure/persistencia/sentencias.py`**

```python
def select_veredicto_y_cierre(*, esquema: str, hash_parte: str) -> tuple[str, tuple]:
```

El `SQL` de §3. Sustituye a `select_estado_cierre` **dentro de
`consultar_situacion`** y solo ahí. Su docstring explica el anclaje en `partes`
y por qué los dos `JOIN` son `LEFT`.

**`infrastructure/persistencia/mapeo.py`** (módulo puro, sin `psycopg`)

```python
def fila_a_validacion_y_cierre(
    fila: Sequence[Any], *, hash_parte: str
) -> tuple[ResultadoValidacion | None, str | None]:
```

- Devuelve las dos cosas juntas **porque vienen de la misma fila**, que es la
  misma regla que ya siguen `fila_a_traza_grafico` y `fila_a_decision_estado`:
  una fila leída por posición se rompe en silencio el día que alguien añade una
  columna al `SELECT`, así que el orden y quien lo lee viven pegados.
- El `hash_parte` entra por palabra clave y no de la fila: es el que se pidió,
  y `ResultadoValidacion.hash_parte` es identificador, no dato leído.
- `Veredicto(...)`, `Destino(...)`, `ClasificacionFirma(...)` y
  `CodigoMotivo(...)` **revientan** si la base trae un valor que el dominio no
  conoce, igual que `EstadoGrafico` y `EstadoParte`: traducir «como si fuera»
  otro abriría la puerta que escribe en el ERP de producción.
- `observaciones` se pasa **tal cual viene** (puede ser `None`): normalizarla
  aquí sería una segunda copia del criterio de `_normalizar`.
- Reutiliza `_motivos_desde_json`, que ya admite `jsonb` deserializado o texto,
  y se le añade el gemelo `_avisos_desde_json` con la misma tolerancia.

**`infrastructure/persistencia/repositorio_pg.py`**

- `consultar_situacion` usa la sentencia nueva en lugar de
  `self.consultar_estado_cierre(...)` y devuelve `SituacionParte` con las
  cuatro cosas.
- La línea de log gana **el destino guardado** —un literal de `Enum`— y **nada
  más**: ni observaciones, ni código de obra, ni número de incidencia (R21).
  Es el camino más transitado del servicio; si filtrara, filtraría en bucle.
- `consultar_estado_cierre` **no se toca**.

### 5.3 · Aplicación

**`application/pipelines/puerta_de_estado.py`** — el cambio que arregla la
regresión:

```python
ctx.situacion = repositorio.consultar_situacion(hash_parte=ctx.parte.hash)
validacion = ctx.situacion.validacion          # ← del almacén, nunca del cuerpo
if validacion is None:
    raise ParteNoApto(sin_veredicto)
estado = estado_del_parte(
    validacion, ctx.situacion.decision_humana, ctx.situacion.estado_cierre
)
if estado is EstadoParte.APROBADO:
    return estado
motivo = MOTIVOS[estado].format(destino=validacion.destino.value)
raise ParteNoApto(f"{motivo}, así que {y_por_eso}")
```

Tres consecuencias que se declaran:

1. **`ctx.validacion` deja de leerse aquí.** La puerta no vuelve a mirar el
   contexto para nada que decida, y ese es el blindaje: aunque alguien vuelva a
   meter un veredicto en el contexto desde el borde, la puerta no se entera.
   Hay un test que lo fija (R1): contexto con un stub apto, almacén con un
   veredicto a `revision_manual` → **no pasa**.
2. **Un parte sin veredicto ahora paga la consulta** antes de que le digan que
   no. Es inevitable —no se puede saber si hay veredicto guardado sin
   preguntar— y es el mismo precio que F-028 aceptó al retirar el atajo del
   apto (§11.1). El mensaje y el orden de precedencia no cambian: «no hay
   veredicto» sigue siendo el primer motivo y sigue siendo el suyo (R8, R17).
3. **`situacion_leida` no cambia**: sigue devolviendo lo que la puerta dejó en
   `ctx.situacion`, ahora con el veredicto dentro.

**`application/pipelines/paso_persistencia.py`** — **no se toca.** Su constancia
sigue derivando el estado de `ctx.validacion`, que es el veredicto que esa misma
llamada **acaba de guardar** dos líneas más arriba. Cambiarlo a
`ctx.situacion.validacion` no aportaría nada y tocaría el camino de escritura
del que depende `POST /api/estado`, que hoy funciona.

### 5.4 · Borde HTTP — los tres que fabricaban el veredicto

En `interface_adapters/api/archivar.py`, `adjuntar.py` y `cerrar.py`:

- `_como_contexto` **deja de construir el `ResultadoValidacion`** y devuelve el
  `ContextoParte` con `validacion=None`. Desaparecen `motivos=()`,
  `clasificacion_firma=ClasificacionFirma.HUMANA` y `observaciones=None`: los
  tres eran valores inventados sobre un parte que nadie había mirado desde ese
  endpoint.
- Se retiran los imports que quedan huérfanos (`ResultadoValidacion`,
  `ClasificacionFirma` donde solo servía para el stub). **`Veredicto` y
  `Destino` se quedan**: los sigue usando `_exigir_valor_conocido`.
- **El contrato no cambia** (R19, D6): `veredicto` y `destino` siguen siendo
  obligatorios y siguen validándose contra las enumeraciones de F-004, con su
  400 si traen algo desconocido. Lo que cambia es que **ya no deciden nada**, y
  eso se dice en el código, en la cabecera de cada fichero, sustituyendo al
  párrafo «El veredicto llega en el cuerpo, y se vuelve a comprobar» de
  `archivar.py:23-29` —que es donde F-006 dejó anotada la deuda que esta
  feature paga—.
- `_serializar` **no se toca** en ninguno de los tres: siguen sin llevar ni una
  clave del papel (R21).

### 5.5 · Tests existentes que hay que tocar, y por qué

- **`tests/utiles_pg.py`**: se añade el doble `RepositorioComoLaBase` (§7). El
  `RepositorioEnMemoria` de hoy **se conserva intacto** —lo usan decenas de
  tests— y gana la posibilidad de que la `SituacionParte` preparada traiga
  veredicto, que ya sale gratis del campo nuevo.
- **`tests/test_f028_puertas.py`**: sus 48 casos preparan la situación con
  `SituacionParte(decision_humana=…, estado_cierre=…)` y el veredicto lo ponen
  en el contexto. Al mudarse la fuente, **hay que pasar el veredicto a la
  situación** en el ayudante `_dobles()` / `_con()`. Es un cambio mecánico en
  **dos ayudantes**, no en los casos. Ese fichero es la red de seguridad de
  F-028 y ninguno de sus asertos cambia: si alguno tuviera que cambiar, es que
  se está aflojando una puerta y hay que **parar**.
- **`tests/test_f006_archivar_http.py`, `test_f012_adjuntar_http.py`,
  `test_f009_cerrar_http.py`**: los que hoy pasan la puerta gracias al
  `veredicto=apto` del formulario tendrán que preparar el veredicto en el
  doble de repositorio. Es el cambio que **demuestra** la feature: si un test
  de endpoint sigue pasando sin veredicto guardado, la puerta no está leyendo
  de donde dice.
- **`tests/test_f028_persistencia.py`**: los casos de `consultar_situacion`
  ganan la cuarta cosa y la sentencia nueva.
- **`tests/test_f028_huella_intacta.py`, `tests/test_f026_*`**: **no se tocan**
  (R13).

---

## 6 · Ficheros que NO se tocan (los colindantes que tientan)

- `domain/models/aprobacion.py` — `huella_de_veredicto` y `_normalizar` (R13,
  D9 de F-026 y de F-028).
- `domain/models/validacion.py` y `infrastructure/persistencia/sql/04_validaciones.sql`
  — tocar cualquiera de los dos es reescribir el veredicto (regla dura 1 de
  F-028, que aquí se hereda).
- Todo `infrastructure/persistencia/sql/` — no hay DDL (R20).
- `interface_adapters/api/estado.py` — el escritor de la huella (D5).
- `interface_adapters/api/parte.py`, `validar.py`, `cola.py`.
- `application/pipelines/paso_validacion.py`, `paso_persistencia.py`,
  `constancia.py`.
- `infrastructure/sharepoint/`, `infrastructure/sigrid/`, `infrastructure/llm/`.
- `services/postventa-front/` — el front no cambia ni una línea (R19).
- `infra/` — no hay despliegue nuevo ni variable de entorno nueva.

---

## 7 · El test que faltó (R23, R24)

El de F-028 no podía cazar el defecto porque la decisión y la puerta salían del
**mismo objeto**. Los dos de F-030 se construyen para que eso sea imposible.

### 7.1 · El doble que se comporta como la base

`tests/utiles_pg.py::RepositorioComoLaBase`, con una regla: **guarda columnas,
no objetos**.

- `guardar_parte(...)` guarda las 18 columnas de `mapeo.valores_de_campos(...)`.
- `guardar_validacion(...)` guarda las 7 columnas de
  `mapeo.valores_de_validacion(...)`.
- `registrar_decision(...)` **acumula**, como la tabla append-only.
- `consultar_situacion(...)` **reconstruye** el veredicto con la misma
  `mapeo.fila_a_validacion_y_cierre` que usa producción, y devuelve la última
  decisión **humana**.

Que el objeto que entró no se pueda devolver es todo el valor del doble: si la
recomposición pierde las observaciones, o el código de obra, o el orden de los
motivos, **la huella deja de coincidir y el test se pone rojo**. Es la
propiedad que el `RepositorioEnMemoria` no tiene y por la que el defecto pasó.

### 7.2 · El recorrido, con los cuerpos de verdad

`tests/test_f030_circuito_borde_a_borde.py`, tres casos con la misma forma:

1. `cambiar_estado_http(cuerpo_de_estado, repositorio=base, ahora=…)` con el
   cuerpo real —`remesa_id`, `parte`, `extraccion`, `firma`, `estado`,
   `usuario_oid`, `confirmado`— sobre un parte **no apto** con observaciones
   manuscritas: es el caso de RS26.09/0178. Se comprueba que responde
   `cambiado` y que el estado devuelto es `aprobado`.
2. `archivar_parte(contenido, hash=…, codigo_obra=…, numero_incidencia=…,
   veredicto=…, destino=…, archivador=doble, repositorio=base)` con el cuerpo
   real del formulario. **Tiene que archivar.**
3. Lo mismo con `adjuntar_grafico(...)` y con `cerrar_incidencia(...)` en
   dry-run (`commit=False`): de la puerta del estado se pasa, y lo que venga
   después son las otras puertas, que no cambian.

Y el **control negativo** que hace que el test sirva de algo: el mismo
recorrido **sin el paso 1** —nadie ha aprobado nada— tiene que levantar
`ParteNoApto` en los tres. Si alguien vuelve a fabricar el veredicto desde el
cuerpo, ese control se pone verde por el camino equivocado y el caso 2 sigue
pasando: por eso van los dos juntos, y por eso el caso 1 usa un parte **no
apto**, que sin aprobación no tiene forma de pasar.

### 7.3 · El centinela estructural (R3)

Un test que recorre con `ast` los módulos de `interface_adapters/api/` y falla
si alguno **construye** un `ResultadoValidacion`. Es barato, no se puede
esquivar sin verlo y ataca la causa —una construcción a mano— y no el síntoma.
Mismo patrón que
`test_f028_t15_ningun_modulo_de_produccion_escribe_en_la_tabla_de_f026`.

---

## 8 · Compatibilidad hacia atrás: qué pasa con lo ya decidido

**Respuesta corta: las decisiones ya guardadas siguen valiendo, no hay que
volver a decidir nada, y no hay migración.**

El motivo es que **la huella no cambia** (R13). La que apuntó `POST /api/estado`
salió del veredicto que esa misma llamada guardó en `postventa.validaciones` y
`postventa.partes` unas líneas antes (`estado.py:180` → `:198`), así que la
huella recomputada desde esas dos filas es la misma. §2 lo demuestra
**[MEDIDO]** campo por campo.

**El parte `b7e9b037`, incidencia RS26.09/0178**, aprobado el 2026-09-16 a las
18:09:33 y todavía sin archivar: en cuanto se despliegue F-030, **se archiva
sin que nadie vuelva a decidir**. La aprobación está en
`postventa.historico_estado` con su huella real (`44aeec3e…`), el veredicto
está en `postventa.validaciones`, y la puerta va a comparar por fin las dos
cosas que hay que comparar. Es la **verificación manual V1** de `tasks.md`.

Las **dos únicas formas** de que una decisión ya guardada deje de contar son las
que R12 quiere, y ninguna es culpa de esta feature:

- que el parte se haya **revalidado con otra lectura** desde que se aprobó —el
  modelo lee distinto, o alguien corrigió un campo decisivo—: entonces el
  veredicto guardado es otro y la aprobación no cuenta, que es exactamente lo
  que R19 de F-028 protege;
- que la fila de `postventa.partes` se haya **actualizado** por un reproceso
  que leyó otra cosa. Mismo caso: se resuelve volviendo a mirar el parte y
  decidiendo, no tocando la huella.

**Los rechazos** ya guardados no dependen de la huella (`estado.py:323-324`):
siguen rechazando, con veredicto o sin él.

**La tabla `postventa.aprobaciones`**, congelada y sembrada por F-028, no se
toca.

---

## 9 · Dato personal

La recomposición trae a memoria `partes.observaciones`, que es **texto
manuscrito del cliente** y está declarado como dato personal directo en
`sql/03_partes.sql`. Se asume, con estas condiciones:

- **No viaja por HTTP.** El argumento de `archivar.py`, `adjuntar.py` y
  `cerrar.py` —*«pedirlas obligaría al front a reenviar el DNI y las
  observaciones manuscritas del cliente en cada llamada»*— es sobre **el
  cable**, no sobre la memoria del servidor. Aquí el texto sale de nuestra
  propia base, en la misma conexión que ya está abierta, y **no entra ni sale
  del servicio**. El front sigue sin mandarlo y las tres respuestas siguen sin
  llevarlo (R21).
- **No se registra.** Ni `mapeo.py` (que no tiene logger, a propósito) ni la
  línea de `consultar_situacion` nombran el texto. Lo vigilan los
  `test_*_logs_sin_datos_personales.py` que ya existen más el caso nuevo de R21.
- **No se copia.** El veredicto recompuesto vive en `ctx.situacion` durante la
  pasada y muere ahí: no se escribe en ninguna tabla, no se serializa y no crea
  una segunda copia del texto (R22, y es la misma regla que impide copiarlo a
  `validaciones`).
- **No entra en la huella en claro**: lo que sale de `huella_de_veredicto` es
  un `sha256` y no lleva dentro ni una letra del papel (R15 de F-026).

---

## 10 · Riesgos, y alternativas descartadas

### 10.1 · El parche por destino — **descartado por el humano, 2026-09-16**

Que la puerta comparase solo el destino aprobado, como hacía
`admite_circuito` en F-026. Arregla el síntoma en una línea y **reabre lo que
R19 cerró**: la aprobación volvería a sobrevivir a que alguien cambie el número
de incidencia —también legible, así que ningún motivo cambia—, y acabaría
cerrando **otra** reclamación del ERP de producción. Es literalmente el camino
que describe la enmienda H-1 de `aprobacion.py` (2026-09-12). Descartado por
escrito, con su motivo.

### 10.2 · Guardar la huella en `postventa.validaciones` — descartada

Una columna `huella_veredicto` escrita por `guardar_validacion` con la misma
función que usa el escritor. Tiene dos ventajas reales —la deriva de la
recomposición sería **imposible por construcción**, y el circuito no tocaría ni
una letra de texto manuscrito— y tres motivos para no hacerla hoy:

1. **Las filas ya escritas tendrían la huella a `NULL`**, y `_aprueba_lo_que_hay`
   trata la ausencia de huella como «no cuenta». La aprobación de RS26.09/0178
   dejaría de valer hasta revalidar el parte: el arreglo de la regresión
   empezaría **rompiendo el caso que la motiva**.
2. **El backfill no se puede escribir en SQL** sin traducir `_normalizar` y el
   orden de los motivos a otro lenguaje, que es justo el segundo criterio que
   F-028 §3 se negó a tener. Escrito en Python es esta misma recomposición,
   ejecutada una vez y con un `UPDATE` masivo sobre el PostgreSQL compartido.
3. Toca `sql/04_validaciones.sql` y `guardar_validacion`, o sea el camino de
   escritura del veredicto, en la sesión que arregla una regresión de
   producción.

**Queda anotada como endurecimiento posterior**: si el humano quiere eliminar la
clase entera de «deriva de la recomposición», ese es el camino, y su momento es
una feature propia con su backfill, no esta.

### 10.3 · Que `POST /api/estado` también leyera el veredicto de vuelta — descartada

Haría que el escritor y el lector calculasen la huella **del mismo byte**, y la
regresión sería estructuralmente imposible en vez de estar sostenida por tests.
Se descarta porque introduce un camino de fallo nuevo justo en el endpoint que
hoy funciona: si `situacion.validacion` volviera vacía por cualquier motivo, la
aprobación no se podría apuntar y estaríamos en la misma pantalla de error, con
otro origen. La garantía se consigue igual con el test de ida y vuelta (R10) y
con el de borde a borde (R23), que es lo que la spec exige.

### 10.4 · Un método de puerto `consultar_validacion` aparte — descartada

Es la propuesta de partida del encargo. Se descarta por §3: **tres viajes más
por parte** a un PostgreSQL compartido, seis en total, cuando la consulta que
hace falta cabe en la que ya se hace. Si algún día hiciera falta el veredicto
suelto en otro sitio, se añade entonces y con su motivo.

### 10.5 · Riesgo: los tests de endpoint que hoy pasan gracias al cuerpo

Varios tests de `/api/archivar`, `/api/adjuntar` y `/api/cerrar` pasan la puerta
porque el formulario dice `veredicto=apto`. Al leerse de la base, **se pondrán
rojos**. Es el efecto buscado y no un daño colateral: cada uno se arregla
preparando el veredicto en el doble. Lo que **no** vale es relajar la puerta
para que sigan verdes; si aparece la tentación, hay que **parar** y avisar.

### 10.6 · Riesgo: dos ventanas de escritura abiertas en `dev`

`ARCHIVO_HABILITADO` y `CIERRE_HABILITADO` están **abiertas** en `dev` ahora
mismo. Esta spec **no autoriza ninguna escritura**: los tests no tocan ni red ni
base ni IA, desde local no se escribe nunca, y cualquier comprobación contra
SharePoint o el ERP exige autorización expresa del humano **por incidencia**
(§12).

### 10.7 · Riesgo declarado y fuera de alcance: el nombrado sigue saliendo del cuerpo

`/api/archivar` decide la carpeta y el nombre del fichero con el `codigo_obra` y
el `numero_incidencia` **del formulario**, no con los guardados. Como esos dos
campos entran en la huella, la puerta aprueba los de la base y el fichero se
nombra con los del cuerpo: si no coincidieran, el PDF con el DNI de un cliente
acabaría en la carpeta de otra obra. Hoy no pasa porque el front manda lo que
leyó, y **cerrarlo no es F-030**: obliga a mover el nombrado a lo persistido y
a mirar qué hace el front cuando una persona corrige un campo. **Se propone
darlo de alta como feature propia** y se deja anotado en
`progress/current.md` para que lo decida el humano.

> **CERRADO por F-031 el 2026-09-22.** El humano lo dio de alta como ficha
> propia y ya está implementada: la carpeta y el nombre salen del `codigo_obra`
> y el `numero_incidencia` **guardados**, leídos de la misma situación que la
> puerta de estado acaba de aprobar; los dos campos del cuerpo siguen siendo
> obligatorios pero pasan a **cotejarse**, y un cuerpo que no cuadre da **409**
> sin archivar nada, antes de dejar rastro; y el front fuerza el guardado de lo
> escrito y lo espera antes de lanzar la tanda, que es la mitad sin la cual
> esto habría **empeorado** el caso de la corrección reciente. La asimetría que
> esta sección describe ya no existe. El detalle, en
> `specs/F-031-nombrado-persistido/`.
>
> Lo que F-031 **no** cerró, y sigue abierto: `/api/adjuntar` y `/api/cerrar`
> tienen el mismo defecto de familia y es **peor** —ahí lo que está en juego es
> qué reclamación se cierra en el ERP de producción—. Es el hallazgo **H-1** de
> `specs/F-031-nombrado-persistido/design.md` §8, y por decisión del humano del
> 2026-09-22 va en el `acceptance` ampliado de **F-034**.

---

## 11 · Encaje en la arquitectura y límite de microservicio

**Encaja sin mover ninguna frontera**, y de hecho endereza una que estaba
torcida:

- **Dominio**: `SituacionParte` gana un campo y sigue sin dependencias.
  `estado_del_parte` sigue siendo pura, con la misma firma.
- **Puertos**: `RepositorioPartesPort` no gana ningún método; cambia lo que
  promete `consultar_situacion`, que es donde tiene que estar.
- **Infraestructura**: el `SQL` y el mapeo viven donde vive el `SQL` y el
  mapeo. Ni una sentencia fuera de `sentencias.py`, ni un `psycopg` en
  `mapeo.py`.
- **Aplicación**: la puerta sigue siendo **un solo módulo**
  (`puerta_de_estado.py`) para los tres pasos, por el motivo de su cabecera:
  tres copias de la decisión son tres sitios donde puede aflojarse, y solo uno
  tendría que aflojarse para que ocurriera.
- **Borde**: los tres endpoints dejan de tener lógica de dominio inventada —un
  `ResultadoValidacion` a mano es exactamente eso— y se quedan componiendo y
  serializando, que es lo que manda `docs/CONVENTIONS.md`.

**Límite de microservicio: F-030 se queda entera en `services/postventa-api`.**
No toca `services/postventa-front/`, no cruza a `sigrid-api`, no toca el
catálogo del portal y no necesita nada de otro proyecto. **Tampoco procede
actualizar `azure-apps/`**: no cambia lo que este servicio expone —mismas rutas,
mismas claves, mismos códigos— ni lo que consume —mismas tablas del schema
`postventa`, mismas variables de entorno, misma pasarela—. Lo único que cambia
es de qué fila sale una decisión interna.

---

## 12 · Verificación manual (humano)

Ninguna condición de cierre de la feature depende de estas dos, que exigen base
de datos o el entorno desplegado. Se listan en `tasks.md` y se anotan en
`progress/current.md`.

- **V1 · el parte que está esperando.** Con F-030 desplegado en `dev`, llamar a
  `POST /api/archivar` para el parte `b7e9b037` de **RS26.09/0178** y comprobar
  que se archiva sin volver a decidir nada. Es la prueba de que la
  compatibilidad de §8 es cierta contra datos reales. **Escritura en SharePoint:
  requiere autorización expresa del humano para esa incidencia.**
- **V2 · el coste, medido.** Contar las consultas de una tanda real de 22 partes
  contra el PostgreSQL compartido y comprobar que **no ha subido** respecto a
  F-028 (§3, R18). Es la continuación de la verificación manual que dejó abierta
  F-028 §11.1.
