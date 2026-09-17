<!-- specs/F-032-codigos-sin-espacios/design.md -->
# F-032 · Los códigos no admiten espacios — Diseño

> Diseño contra `docs/ARCHITECTURE.md` (semánticas 2, 5 y 8; pasos 5, 6, 7a y
> 7b del pipeline) y `docs/CONVENTIONS.md`. Lo marcado **[MEDIDO]** se ha
> comprobado leyendo el código de `dev` a 2026-09-17; lo demás es diseño.

## 1 · El mapa del cambio

### 1.1 · Ficheros a crear

| Fichero | Qué es |
|---|---|
| `services/postventa-api/tests/test_f032_espacios_en_los_codigos.py` | La tabla de casos ampliada (§5) sobre las tres salidas: normalización, código del ERP y nombre/carpeta. Dominio puro, sin red, sin BBDD y sin IA |
| `services/postventa-api/tests/test_f032_saneo_en_la_extraccion.py` | Que los dos códigos nacen limpios por los **dos** caminos —pipeline y cuerpo HTTP—, que los otros siete campos no se tocan y que el saneo deja aviso |
| `services/postventa-api/tests/test_f032_huella_intacta.py` | El control propio de **este** cambio: las huellas de los veredictos cuyo código lleva un espacio **dentro del tramo** no se mueven (§7) |

### 1.2 · Ficheros a modificar

| Fichero | Qué cambia |
|---|---|
| `services/postventa-api/domain/models/nombrado.py` | `normalizar_codigo` elimina todos los blancos en vez de colapsarlos; desaparece `_ESPACIOS_JUNTO_AL_SEPARADOR`, que queda sin trabajo; docstring reescrita con la enmienda fechada |
| `services/postventa-api/domain/models/extraccion.py` | Nueva constante `CAMPOS_DE_CODIGO` y nueva función pura `sanear_valor_leido` (§4.1) |
| `services/postventa-api/application/pipelines/paso_extraccion.py` | `_completar_y_sanear` aplica `sanear_valor_leido` y emite el aviso de R15; docstring del módulo corregida (hoy dice que no normaliza nada) |
| `services/postventa-api/interface_adapters/api/cuerpos.py` | `a_extraccion` aplica el mismo saneo, campo a campo (§4.2) |
| `services/postventa-api/tests/test_f006_nombrado.py` | `test_f006_r8_los_espacios_interiores_se_colapsan_a_uno` cambia de expectativa y de nombre: es **el** test que codifica la regla que esta feature sustituye |
| `specs/F-006-sharepoint/requirements.md` | Segunda enmienda fechada de R8 (§9.1) |
| `docs/ARCHITECTURE.md` | Precisión fechada en la semántica 5 (§9.2) |
| `progress/current.md`, `BACKLOG.md`/`harness/features.json` | Rastro del arnés (lo regenera `init.sh`) |

### 1.3 · Ficheros que NO se tocan (los colindantes que tientan)

| Fichero | Por qué no |
|---|---|
| `domain/models/aprobacion.py` | **La regla dura de la feature.** Tocar `_normalizar` revoca decisiones humanas vivas (R17, D1) |
| `tests/test_f028_huella_intacta.py`, `tests/test_f028_espacios_codigos.py`, `tests/test_f026_*` | Ni un aserto. Sus siete huellas literales son el control que esta feature tiene que pasar, no ajustar |
| `domain/models/cierre.py` (`a_codigo_de_sigrid`) | Hereda de `normalizar_codigo` a propósito (F-028 R47). Un saneo propio aquí es el bug que R6 prohíbe |
| `infrastructure/sigrid/consultas.py` | La búsqueda por igualdad exacta **es correcta**: lo que estaba mal es el código que le llegaba |
| `application/pipelines/paso_archivo.py`, `paso_grafico.py`, `paso_cierre.py` | No hay ninguna línea que cambiar: reciben el código ya saneado |
| `interface_adapters/api/archivar.py`, `adjuntar.py`, `cerrar.py` | Su `codigo_obra` del cuerpo pasa por `componer_destino` / `a_codigo_de_sigrid`, que ya sanean. De dónde deberían sacarlo es **F-031** |
| `infrastructure/persistencia/**` | Ni DDL, ni sentencia, ni mapeo, ni migración (R22) |
| `services/postventa-front/**` | El front sigue igual; lo que cambia es que ve el código limpio (R29) |
| `config/prompts.yaml` | El prompt no es el arreglo (D5) |

---

## 2 · El cambio 1 · `normalizar_codigo`

**Capa: dominio puro.** Sin reloj, sin red y sin configuración, como exige
F-006 R9.

Hoy (`domain/models/nombrado.py:145-146`):

```python
colapsado = " ".join(bruto.translate(_A_GUION_NORMAL).split())
return _ESPACIOS_JUNTO_AL_SEPARADOR.sub(r"\1", colapsado)
```

Después:

```python
return "".join(bruto.translate(_A_GUION_NORMAL).split())
```

Tres cosas que hay que ver en esas dos líneas de diferencia:

1. **`str.split()` sin argumentos ya parte por cualquier blanco Unicode**, así
   que R2 sale gratis y sin una lista de caracteres que mantener: tabulador,
   salto de línea, `U+00A0` (espacio no separable) y `U+202F` (espacio fino no
   separable) se van igual que el espacio normal. **[MEDIDO]**:
   `'a b'.split()` → `['a', 'b']`; `'06 26'.split()` → `['06', '26']`.
   Lo que **no** se va es el `U+200B` (ancho cero), que Python no considera
   blanco: es el defecto declarado D3 de `requirements.md` §8.
2. **`_ESPACIOS_JUNTO_AL_SEPARADOR` se queda sin trabajo y se borra.** Después
   de quitar todos los blancos no queda ninguno flanqueando a un separador. Un
   regex que ya no puede casar nada es un regex que el día de mañana alguien
   lee como si significara algo.
3. **Los guiones raros se siguen traduciendo antes** (`_A_GUION_NORMAL`), y el
   orden importa: es lo que hace que `RS26.09 – 0178` y `RS26.09-0178` acaben
   en el mismo sitio.

### 2.1 · Por qué una línea cubre el ERP, la carpeta y el nombre

Porque las tres salidas cuelgan de esta función y **ninguna tiene saneo
propio** (F-028 R47, verificado):

| Salida | Quién la compone | Cómo llega aquí |
|---|---|---|
| Código para el ERP | `domain/models/cierre.py::a_codigo_de_sigrid` | `normalizar_codigo` → `tramos_de_codigo` → `"/".join(...)` |
| Nombre del fichero | `nombrado.py::nombre_de_archivo` | `normalizar_codigo` de los dos códigos → tramos → `" - ".join(...)` |
| Carpeta de archivo | `nombrado.py::carpeta_de_archivo` | `normalizar_codigo` del código de obra |

Y por eso el arreglo va **aquí** y no en las puntas: dos criterios del mismo
concepto divergen siempre, que es literalmente lo que le pasó a este proyecto
el 2026-09-15 (F-028 §9.1).

---

## 3 · Qué deja de estar roto, caso por caso

| Hoy | Después |
|---|---|
| `a_codigo_de_sigrid("RS 26.09/0178")` → `"RS 26.09/0178"` → `WHERE c.cod = 'RS 26.09/0178'` → 0 filas → `ReclamacionNoLocalizada` | → `"RS26.09/0178"` → la reclamación de siempre |
| `nombre_de_archivo(obra="0626", nº="RS 26.09/0178")` → `0626 - RS 26.09 - 0178 PARTE FIRMADO.pdf` | → `0626 - RS26.09 - 0178 PARTE FIRMADO.pdf` |
| `carpeta_de_archivo(base="Postventa", obra="06 26")` → `Postventa/06 26` | → `Postventa/0626` |
| `postventa.partes.numero_incidencia` = `'RS 26.09/0178'` | = `'RS26.09/0178'` (§4) |

---

## 4 · El cambio 2 · el saneo en la extracción

El objetivo es el criterio de aceptación 3: **lo que se guarda nace limpio**.
Hay que entender antes por dónde llega el valor a la base, porque no es por
donde parece.

**[MEDIDO] · el camino real del dato:**

```
/api/extraer  →  paso_extraccion  →  ExtraccionParte  →  JSON al front
                                                            |
   (el front lo enseña, la persona puede corregirlo, y lo devuelve)
                                                            v
/api/parte  ·  /api/validar  ·  /api/estado  →  cuerpos.a_extraccion
                                                            |
                                       paso_persistencia → upsert_parte
                                                            v
                                                   postventa.partes
```

`paso_extraccion` **nunca persiste nada**: su resultado viaja al front y vuelve
en el cuerpo. Quien construye el `ExtraccionParte` que acaba en la base es
`cuerpos.a_extraccion` (`interface_adapters/api/cuerpos.py:109-133`), usado por
los tres endpoints que guardan o revalidan (`parte.py:117`, `estado.py:157`,
`validar.py:57`). **Por eso hacen falta los dos sitios**: sanear solo en el
pipeline dejaría la base sucia en cuanto una persona corrigiera un campo, y
sanear solo en el cuerpo dejaría al front enseñando un código que no es el que
se va a usar.

### 4.1 · La regla, en el dominio

En `domain/models/extraccion.py`, junto a `CAMPOS_DEL_PARTE` y
`CAMPOS_MANUSCRITOS`, que es donde vive el conocimiento de «qué es cada campo»:

```python
#: Los dos campos que son un **código** y no un texto (F-032 R14).
CAMPOS_DE_CODIGO: tuple[str, ...] = ("codigo_obra", "numero_incidencia")


def sanear_valor_leido(nombre: str, valor: str | None) -> str | None:
    """El valor de un campo listo para viajar y para guardarse.

    Un **código** sale sin blancos: es lo que identifica una reclamación en el
    ERP (por igualdad exacta) y la carpeta del archivo. Cualquier otro campo
    sale **tal cual**: quitarle los espacios a una observación manuscrita la
    convertiría en otra cosa.
    """
    if valor is None or nombre not in CAMPOS_DE_CODIGO:
        return valor
    return normalizar_codigo(valor) or None
```

Cuatro decisiones metidas en seis líneas:

- **La regla es de dominio, aplicarla es de quien construye la extracción.** El
  dominio dice *qué* campos son códigos y *cómo* se sanea un código; el paso del
  pipeline y el borde HTTP lo aplican. Eso conserva lo que dice la cabecera de
  `extraccion.py` —«quien sanea es la aplicación»— sin repartir el criterio.
- **Se apoya en `normalizar_codigo`**, no en una copia. Es la misma regla que
  nombra el fichero y que busca en el ERP: si un día cambia, cambia para los
  tres. `domain/models/extraccion.py` importando `domain/models/nombrado.py` es
  una dependencia **dentro del dominio**, y `nombrado.py` no importa a nadie
  salvo `errores`, así que no hay ciclo. **[MEDIDO]**.
- **`None` se devuelve sin tocar** (R16): un campo que el modelo no leyó no se
  convierte en uno leído.
- **Un código que se queda vacío sale `None`** y no `""`: un valor de solo
  blancos no dice nada que un `NULL` no diga, y F-004 ya trata «solo espacios»
  como vacío. **No mueve ninguna huella**, porque `_normalizar(None)` y
  `_normalizar("   ")` valen los dos la cadena vacía (§7.3).

### 4.2 · Los dos llamantes

**`application/pipelines/paso_extraccion.py::_completar_y_sanear`** — una línea
dentro del bucle que ya recorre `CAMPOS_DEL_PARTE`:

```python
valor = sanear_valor_leido(nombre, bruto.valor)
if valor != bruto.valor:
    avisos.append(
        f"{nombre}: el modelo leyó «{bruto.valor}» y se ha guardado sin "
        f"espacios como «{valor}»"
    )
campos[nombre] = CampoExtraido(valor=valor, confianza_pct=confianza)
```

El aviso es R15: el saneo **no es silencioso**, y quien mire el parte en el
front ve que el valor guardado no es letra por letra el del papel. Los avisos
ya se persisten (`partes.avisos_extraccion`) y ya se enseñan, así que no hace
falta ningún mecanismo nuevo. No llevan dato personal: un código de obra y un
número de incidencia ya viven en claro en sus propias columnas.

**`interface_adapters/api/cuerpos.py::a_extraccion`** — el mismo saneo, en el
bucle que ya monta los nueve campos:

```python
campos={
    nombre: a_campo(campos[nombre], nombre) for nombre in CAMPOS_DEL_PARTE
},
```

con `a_campo` recibiendo el nombre del campo y llamando a `sanear_valor_leido`
justo donde hoy ya sanea la confianza con la función del dominio. Es la misma
simetría que ya existía: **lo que llega de fuera se sanea con el criterio de
dentro**.

Aquí **no se emite aviso** y es deliberado: `a_extraccion` construye la
extracción con `avisos=()` por contrato (los avisos son de la lectura, no del
transporte, F-019), y fabricar avisos en el borde los acabaría duplicando en
cada revalidación del mismo parte.

### 4.3 · La tercera construcción de `ExtraccionParte`, y por qué se deja

**[MEDIDO]**: en todo el árbol hay tres, y la tercera es
`interface_adapters/api/archivar.py:201`, el contexto mínimo que F-030 dejó
para nombrar el fichero. Esa no pasa por `a_extraccion` y **no se toca**:

- no persiste nada —`/api/archivar` no escribe en `partes`—;
- su valor va derecho a `componer_destino`, que lo normaliza igual;
- y **de dónde debería salir ese código es exactamente el alcance de F-031**.

Se declara aquí para que el implementer no la «arregle» de paso y para que el
reviewer sepa que está vista.

---

## 5 · La tabla de casos

Amplía la de F-028 (`tests/test_f028_espacios_codigos.py:67-74`, seis formas).
Obra `0626` y número `RS26.09/0149` son los **inventados** de aquella tabla;
`RS 26.09/0178` es **el caso real del 2026-09-17**, y va escrito literal porque
un caso real que nadie escribe se vuelve a perder. Ni un dato personal: un
código de incidencia no identifica a nadie.

Todas las filas tienen que dar **el mismo código para el ERP** (`RS26.09/0149`
o `RS26.09/0178`) y **el mismo nombre de fichero**
(`0626 - RS26.09 - 0149 PARTE FIRMADO.pdf` o `... - 0178 ...`).

| # | Forma | Entrada | Quién la arregla |
|---|---|---|---|
| 1 | barra pegada (la canónica) | `RS26.09/0149` | ya estaba |
| 2 | barra con espacio a los dos lados | `RS26.09 / 0149` | F-028 R44 |
| 3 | barra con espacio solo delante | `RS26.09 /0149` | F-028 R44 |
| 4 | guion normal con espacio a los dos lados | `RS26.09 - 0149` | F-028 R44 |
| 5 | guion pegado delante, espacio detrás | `RS26.09- 0149` | F-028 R44 |
| 6 | guion largo con espacio a los dos lados | `RS26.09 – 0149` | F-028 R44 |
| **7** | **espacio dentro del primer tramo (el caso real)** | **`RS 26.09/0178`** | **F-032 R1** |
| 8 | espacio dentro del segundo tramo | `RS26.09/01 49` | F-032 R1 |
| 9 | varios espacios dentro del tramo | `RS  26.09/0149` | F-032 R1 |
| 10 | espacio interior **y** alrededor del separador | `RS 26.09 / 0149` | F-032 R1 |
| 11 | tabulador dentro del tramo | `RS\t26.09/0149` | F-032 R2 |
| 12 | espacio no separable dentro del tramo | `RS 26.09/0149` | F-032 R2 |
| 13 | extremos con blancos y espacio interior | `  RS 26.09/0149  ` | F-032 R1 |

Y la tabla del **código de obra**, que decide la carpeta:

| # | Entrada | `normalizar_codigo` | Carpeta |
|---|---|---|---|
| A | `0626` | `0626` | `Postventa/0626` |
| B | `06 26` | `0626` | `Postventa/0626` |
| C | `06  26` | `0626` | `Postventa/0626` |
| D | `06 26` | `0626` | `Postventa/0626` |
| E | `06-77` | `06-77` | `Postventa/06-77` (**no se parte**, F-028 R48) |
| F | `06 - 77` | `06-77` | `Postventa/06-77` |
| G | `06–77` (guion largo) | `06-77` | `Postventa/06-77` |
| H | `0000626` | `0000626` | `Postventa/0000626` (los ceros, intactos) |

La fila **E** es la que impide que este arreglo se pase de listo: el código de
obra **no se parte por sus guiones** y el guion no se toca; lo único que
desaparece son los blancos.

---

## 6 · El riesgo del renombrado en SharePoint

Es el punto que no se puede esquivar, y se resuelve en tres partes: qué pasa
exactamente, por qué no se arregla en el código, y qué se hace en su lugar.

### 6.1 · Qué pasa exactamente

Un parte archivado **antes** del cambio con el nombre sucio
—`0626 - RS 26.09 - 0178 PARTE FIRMADO.pdf`— y archivado **otra vez** después,
se subiría como `0626 - RS26.09 - 0178 PARTE FIRMADO.pdf`. El viejo **no se
sobrescribe**: el reemplazo de la capa L2 solo alcanza al **homónimo**
(`paso_archivo.py::_subir` busca por nombre), y el nombre ha cambiado. Quedan
dos ficheros del mismo parte en la carpeta de Posventa, los dos con el DNI
manuscrito del cliente dentro.

Y hay algo peor que el duplicado: **re-archivar borra la única pista del
nombre viejo**. `postventa.archivos` tiene el `hash_parte` como clave primaria,
así que la traza nueva pisa `nombre_fichero` y `carpeta` de la vieja. Después
de re-archivar, el fichero huérfano ya no se puede localizar desde nuestra
base. De ahí que la medición del §6.3 vaya **antes del despliegue** y no
después.

### 6.2 · Por qué no se arregla en el código · defecto D-A1

La arquitectura dice que esto no debería poder pasar: el paso 6 declara tres
capas contra el duplicado, y la primera —**L1, la traza**— corta sin llamar a
nadie cuando el parte ya consta archivado (F-006 R14).

**[MEDIDO]: L1 está inerte desde el endpoint.** `paso_archivo` la espera como
argumento opcional (`paso_archivo.py:96`, `traza_previa=None`) y
`archivar.py:118-128` no se la pasa; el único sitio del árbol que la pasa es
`tests/test_f019_orden_archivado.py`. `SituacionParte` —lo que la puerta ya
consulta en la misma llamada— no trae la traza del archivo
(`domain/models/estado.py:189-208`), y `RepositorioPartesPort` no tiene
`consultar_archivo` (`domain/ports/persistencia.py`: `consultar_grafico`,
`consultar_situacion`, `consultar_estado_cierre`). Así que hoy
`/api/archivar` **vuelve a subir siempre** y se apoya en el reemplazo del
homónimo, que funcionaba porque el nombre no cambiaba nunca.

Cablearlo es lo único que haría **imposible** el duplicado, y es más feature de
lo que parece: un campo nuevo en `SituacionParte`, un método nuevo en el
puerto, su adaptador, una sentencia, su mapeo y los tests de los tres. Eso
reabre el alcance que fijó el humano el 2026-09-17 y pisa el terreno de
F-019/F-031. **Se declara como D-A1 y se propone al humano como feature
propia** (o como parte de F-031, que ya va a mirar de dónde salen los códigos
del archivado).

### 6.3 · Lo que se hace en su lugar: medir antes de desplegar

Consulta de **solo lectura**, sobre nuestro propio schema, que lista los partes
archivados cuyos códigos guardados llevan algún blanco: son exactamente
aquellos cuyo nombre de fichero cambiaría.

```sql
SET search_path TO postventa;

SELECT a.hash_parte,
       a.estado,
       a.carpeta,
       a.nombre_fichero,
       p.codigo_obra,
       p.numero_incidencia,
       a.archivado_at_utc
FROM postventa.archivos a
JOIN postventa.partes  p ON p.hash_parte = a.hash_parte
WHERE a.estado = 'archivado'
  AND translate(
        coalesce(p.codigo_obra, '') || '|' || coalesce(p.numero_incidencia, ''),
        E' \t\n\r' || chr(160) || chr(8239), ''
      )
      <> coalesce(p.codigo_obra, '') || '|' || coalesce(p.numero_incidencia, '')
ORDER BY a.archivado_at_utc;
```

`translate` con el tercer argumento vacío **borra** esos caracteres, así que la
comparación detecta cualquier blanco —incluidos el no separable (`chr(160)`) y
el fino (`chr(8239)`)— sin depender de cómo trate `\s` la configuración
regional.

**Lo esperable es cero filas** y hay motivo para creerlo: el único parte que se
sabe leído con un espacio interior —el de ayer— se **editó a mano antes** de
archivarlo, y las formas que F-028 arregló producían ya el nombre canónico *por
casualidad* (la barra pasaba a ` - ` y el colapso se comía el sobrante). Pero
«lo esperable» no es una medición: por eso R26 la exige con resultado anotado.

**Si devuelve filas** (R27): ese parte **no se re-archiva desde el circuito**.
Se anota `hash_parte`, `carpeta` y `nombre_fichero` en `progress/`, y decide el
humano —él es quien puede abrir la biblioteca y quitar el fichero viejo—. El
sistema no borra ni renombra nada (R24, D4).

---

## 7 · La huella: el control propio de este cambio

### 7.1 · Por qué no se mueve (el razonamiento)

Son dos funciones distintas, en dos módulos distintos, y **la huella no pasa
por el nombrado**: `huella_de_veredicto` normaliza con `_normalizar`
(`aprobacion.py:165-178`), que recorta, colapsa y baja a minúsculas. Cambiar
`normalizar_codigo` no puede cambiar el valor de una huella porque ninguna
huella lo llama. F-028 lo dejó medido y vigilado con tres controles.

Pero eso es un razonamiento sobre el código, y el encargo pide la medición
**para este cambio concreto**. F-028 midió las formas de F-028 —espacios
**alrededor** del separador—; las que F-032 toca son otras.

### 7.2 · El control nuevo: `tests/test_f032_huella_intacta.py`

Tres controles, con la misma estructura que el de F-028 para que se lean
juntos:

1. **El valor, con casos propios.** Dos veredictos nuevos —uno con
   `numero_incidencia="RS 26.09/0178"` y otro con `codigo_obra="06 26"`, más
   una variante no apta con observaciones— con su huella **escrita literal**,
   medida **antes** del cambio. Una huella comparada consigo misma no prueba
   nada.
2. **El segundo camino independiente.** La misma huella recalculada a mano con
   `hashlib` sobre la cadena canónica escrita en el test —seis campos separados
   por saltos de línea, en minúsculas—, sin importar ni una constante de
   `aprobacion.py`. Es lo que demuestra que el literal no es la foto de un
   código que ya estuviera mal. Aquí se ve además lo que hay que ver:
   `_normalizar("RS 26.09/0178")` vale **`rs 26.09/0178`**, con el espacio
   dentro, y eso es lo correcto: la huella compara **dos lecturas del mismo
   papel**, no identifica nada fuera.
3. **El efecto.** Un parte no apto que una persona aprobó antes del cambio,
   con la huella de aquel veredicto y el código leído con espacio interior,
   sigue `aprobado` (`estado_del_parte`) y sigue constando decidido **por una
   persona** (`decision_en_firme`, F-028 R43).

Y se conserva el control de acoplamiento de F-028 (R51) ejecutándolo: `aprobacion.py`
sigue sin importar `nombrado` y sin nombrar sus piezas.

### 7.3 · Cómo se mide el literal (receta exacta para el implementer)

Igual que hizo F-028 en su T23, y por partida doble:

```bash
git worktree add ../postventa-f032-antes HEAD     # árbol anterior al bloque 1
```

y en ese árbol, con el entorno del servicio, calcular
`huella_de_veredicto(...)` de los tres veredictos del control y pegar la traza
en `progress/impl_F-032.md`. Después del bloque 1, los mismos tres valores
tienen que salir **idénticos**. El segundo camino —`hashlib` a mano— no depende
del worktree y tiene que coincidir con el primero.

La medición se hace **antes de tocar `normalizar_codigo`**, que es lo que la
convierte en una medición y no en una foto.

### 7.4 · Lo que sí caduca, y está bien que caduque

Un parte **reprocesado** después del cambio guarda sus códigos limpios, y si su
huella cambia, la aprobación humana anterior deja de contar y el parte vuelve a
`pendiente` (F-028 R19). No es un efecto de F-032: es la regla de F-028
funcionando. Se decidió sobre un veredicto que ya no es el que hay, y quien
decidió tiene que volver a mirar. Las filas **que nadie reprocesa no se tocan**
(R22), así que ninguna decisión vigente se pierde por desplegar esto.

---

## 8 · Encaje en la arquitectura

| Pieza | Capa | Nota |
|---|---|---|
| `normalizar_codigo` | dominio | Sigue pura: dos cadenas entran, una sale. Paso 5 del pipeline |
| `CAMPOS_DE_CODIGO`, `sanear_valor_leido` | dominio | Conocimiento de qué campo es un código; sin reloj, sin red, sin configuración |
| `_completar_y_sanear` | aplicación | Aplica la regla del dominio; sigue sin saber quién leyó el parte (F-003 R13) |
| `a_extraccion` | interface adapters | Lo que llega de fuera se sanea con el criterio de dentro, como ya hace con la confianza |
| Persistencia, SharePoint, Sigrid | infraestructura | **Sin cambios**: reciben el mismo contrato, con el valor limpio |

**Límite de microservicio.** Todo lo que toca esta feature es de
`services/postventa-api` y de su propio dominio. No cruza ninguna frontera: no
cambia lo que consumimos de `sigrid-api` (la consulta es la misma, con el
parámetro bien escrito), ni lo que escribimos en SharePoint, ni ninguna
variable de entorno. Por eso **no procede tocar `azure-apps/postventa_incidencias.md`**:
no cambia nada de lo que ese documento describe —endpoints, tablas, variables—.
Queda dicho para que el reviewer no lo eche en falta.

---

## 9 · Documentación a enmendar

### 9.1 · `specs/F-006-sharepoint/requirements.md` · R8, segunda enmienda

R8 quedó redactado por F-028 como: *«eliminar los espacios que flanquean a un
separador, **colapsar a uno los espacios redundantes que no tocan un
separador** y recortar los de los extremos…»*. La parte en negrita es la que
cae. La enmienda, fechada **2026-09-17**, dice:

- **qué cambia**: los espacios que no tocan un separador ya no se colapsan, se
  **eliminan**. `RS 26.09/0178` normaliza a `RS26.09/0178`;
- **qué la invalidó**: la premisa de F-028 era que el espacio problemático
  siempre estaba pegado al separador. No era cierto, y se vio en real el
  2026-09-17: la IA leyó `RS 26.09/0178` y el cierre murió en
  `ReclamacionNoLocalizada` hasta que una persona editó el código a mano;
- **quién y cuándo**: el responsable del proyecto, el 2026-09-17, al verificar
  F-030 contra producción;
- **qué no cambia**: los ceros a la izquierda (R4), el sufijo y la extensión
  literales (R5), el error ruidoso ante un nombre imposible (R7) y que el
  código de obra no se parte por sus guiones (F-028 R48).

### 9.2 · `docs/ARCHITECTURE.md` · semántica 5

Añadir, con el formato de las precisiones anteriores:

> **Precisado por F-032 el 2026-09-17**: **ningún espacio forma parte del
> código**, ni junto al separador ni dentro de un tramo. `RS 26.09/0178` es el
> mismo número que `RS26.09/0178`, y `06 26` la misma obra que `0626`. F-028
> había dejado fuera el espacio que no toca al separador, y el 2026-09-17 eso
> costó un cierre que hubo que rescatar editando el código a mano. Los códigos
> se sanean **al leerlos**, así que lo que se guarda en `postventa.partes` nace
> sin espacios. Lo que sigue sin cambiar: el código de obra **no se parte por
> sus guiones** (`06-77` es una obra), y la normalización de la **huella** del
> veredicto es **otra** y no se toca.

---

## 10 · Riesgos

| # | Riesgo | Mitigación |
|---|---|---|
| **1** | Un parte ya archivado con el nombre sucio se re-archiva y deja un huérfano en SharePoint | §6: medición previa obligatoria (R26), no re-archivar los que salgan (R27), defecto D-A1 declarado y propuesto aparte |
| **2** | Se toca la huella «de paso» y se revocan decisiones humanas | Regla dura de la feature (R17), centinela de F-028 sin tocar + control propio (§7) |
| **3** | Alguien «limpia» las filas viejas con un `UPDATE` | R22 y D2: los códigos de la huella se leen de `partes`; un `UPDATE` es tocar la huella por la puerta de atrás |
| **4** | El saneo se le aplica a un campo de texto y se estropea una observación manuscrita | R14 y su test: solo `CAMPOS_DE_CODIGO`; los otros siete se copian tal cual |
| **5** | Un código con `U+200B` sigue pasando | Declarado (D3) y no arreglado: no se ha visto nunca y ampliar el criterio a «todo lo invisible» es otra discusión |
| **6** | El saneo tapa una lectura mala del modelo sin que nadie se entere | R15: aviso cuando el valor cambia, persistido y visible |

---

## 11 · Trazabilidad requisito → fichero → tarea

| Requisito | Fichero | Bloque/tarea |
|---|---|---|
| R1–R10, R28 | `domain/models/nombrado.py`, `tests/test_f032_espacios_en_los_codigos.py` | B0–B1 |
| R11–R16 | `domain/models/extraccion.py`, `paso_extraccion.py`, `cuerpos.py`, `tests/test_f032_saneo_en_la_extraccion.py` | B2–B3 |
| R17–R21 | `tests/test_f032_huella_intacta.py` (+ los de F-028, ejecutados) | B0 (medición) y B4 |
| R22, R23 | Ausencia de SQL nuevo + `tests/test_f032_saneo_en_la_extraccion.py` | B3, B4 |
| R24–R27 | §6.3 y `progress/impl_F-032.md` | B5 (MANUAL) |
| R29 | `services/postventa-front/` sin diff; tests de contrato | B4 |
| Documentación | `specs/F-006-sharepoint/requirements.md`, `docs/ARCHITECTURE.md` | B5 |
