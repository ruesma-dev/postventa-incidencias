<!-- progress/explore_F-003.md -->
# F-003 · Explicación para decidir si arranca

**Fecha**: 2026-08-18 · **Rol**: explorer (solo lectura) · **Fuentes**:
`specs/F-003-extraccion/{requirements,design,tasks}.md`,
`progress/spec_F-003.md`, `harness/features.json`,
`docs/referencia/02_parte_de_trabajo.md`, `docs/ARCHITECTURE.md`,
`specs/F-002-ingesta-troceado/design.md` y el código ya escrito de F-002.

---

## 1 · Qué hace F-003, en una frase

**Coge un parte troceado (el PDF de un solo parte que produce F-002), se lo
enseña a un modelo multimodal, y devuelve nueve datos del papel con un número
de confianza para cada uno.** Nada más.

Qué **no** hace, y de quién es cada cosa:

| No hace | Es de |
|---|---|
| Decidir si el parte es apto; clasificar la firma | **F-004** |
| Guardar nada en PostgreSQL | F-005 |
| Nombrar el fichero y subirlo a SharePoint | F-006 |
| Tocar Sigrid | F-008 / F-009 |
| **Reagrupar** el parte de dos hojas usando el «Página N» | **F-014** |
| Medir si el modelo acierta de verdad, de forma repetible | **F-015** |

La frontera fina, porque es la que se puede malinterpretar: F-003 **lee** el
número de página del pie y lo devuelve; **no une páginas, no toca
`paginas_origen`, no cambia `modo_deteccion`, no reordena nada**. Leer es de
esta feature, reagrupar es de F-014. La spec lo repite en tres sitios y le pone
un test específico (`test_f003_r2bis_la_extraccion_no_reagrupa_paginas`) para
que no se cuele.

Frontera con F-002: F-003 **consume** `ParteTroceado` y no lo modifica. El
diseño lista explícitamente los ficheros de F-002 que no se tocan
(`design.md` §12); si al implementar pareciera necesario cambiarlos, es una
**parada**, no un ajuste.

---

## 2 · Qué campos se extraen

Nueve. Ocho de contenido más el número de página:

| Campo | Etiqueta en el papel | Impreso / manuscrito |
|---|---|---|
| `promocion` | Promoción | impreso |
| `codigo_obra` | Código Obra (`0677`) | impreso |
| `unidad` | Vivienda (`Viviendas Bloque Villa 5`) | impreso |
| `numero_incidencia` | Nº Incidencia (`RS26.08/0123`) | impreso |
| `descripcion` | Descripción | impreso |
| `numero_pagina` | pie: «… Página 1» | impreso |
| `fecha_servicio` | Fecha servicio | **manuscrito** |
| `dni_cliente` | Fdo. / DNI (columna izquierda) | **manuscrito** |
| `observaciones` | Observaciones de reparación | **manuscrito** |

Los tres manuscritos son los que importan de verdad: según
`docs/referencia/02_parte_de_trabajo.md`, la observación manuscrita es lo que
distingue «firmado» de «conforme» (el parte de la piscina: firmado y con «se
aprecia que se han hecho parcheados»). Por eso extraerlos no es un extra.

**Ojo con lo que la realidad deja en blanco**: fecha de servicio, horas, nombre
y DNI están vacíos en casi toda la remesa de Mirasierra. La spec lo asume: el
resultado trae **siempre las nueve claves**, y las que el parte no tiene salen
con `valor = null`, `confianza_pct = 0` y un aviso. Eso es normal, no un fallo.

**Qué es la «confianza por campo».** Un entero 0–100 que el propio modelo
declara para cada dato: su certeza de haber *leído bien ese campo* (no de que
el parte esté bien). Para qué sirve en la práctica, tres cosas:

1. **F-004** podrá mandar a revisión manual lo que venga con confianza baja en
   los campos que deciden (código de obra, nº de incidencia).
2. **El front (F-007)** puede pintar en amarillo lo dudoso y en verde lo claro,
   para que Posventa mire solo lo que hay que mirar.
3. **La revisión posterior** sabe si un dato malo vino del modelo dudando o del
   modelo equivocándose con seguridad, que es peor.

El nombre y la escala (`confianza_pct`, 0–100) son los que ya usan `partes` y
`albaranes` en el ecosistema. No se inventa nada.

Detalle que agradecerá F-006: los valores salen **tal cual se leen**, sin
normalizar. `RS26.08/0123` conserva la barra, `0677` conserva los ceros, la
fecha manuscrita conserva su formato. Convertir a guion para el nombre de
fichero es trabajo de F-006, no de aquí.

---

## 3 · Cómo funciona por dentro

Sin abrir el código, la cadena es esta:

1. **Entra** el PDF de un parte (1–2 páginas) y su `hash`.
2. **Corta si es enorme**: si pasa de 15 MB, se rechaza **sin llamar al
   modelo** (llamar costaría dinero para nada).
3. **Se carga el prompt** de `services/postventa-api/config/prompts.yaml`, por
   una clave (`parte_posventa_es`). Si el fichero no existe o la clave no está,
   revienta ahí, **antes** de llamar a nadie.
4. **Se llama al modelo** (Gemini 2.5 Flash por defecto) mandándole el PDF
   entero — el proveedor ya sabe rasterizarlo, no rasterizamos nosotros — con
   un *schema* que le obliga a devolver JSON con esos nueve campos y sus nueve
   confianzas. Si falla por algo transitorio (timeout, 429, 5xx) se reintenta
   con espera creciente, hasta 3 veces; si el error es de credencial o petición
   mal formada, **no se reintenta**.
5. **Se sanea el resultado**: se recorre *la lista de campos declarada en el
   código*, no lo que devolvió el modelo. Así, lo que falte sale vacío con
   aviso, y lo que el modelo se invente se descarta con aviso. Una confianza
   de 120 pasa a 100, una de −5 a 0, un `"no sé"` a 0, cada una con su aviso.
6. **Sale** un objeto con el `hash`, los nueve campos, la **traza** (proveedor,
   modelo, clave de prompt, versión y huella del prompt) y los avisos.

**Por qué el prompt vive fuera del código.** Porque es lo que más se va a
tocar y lo que menos tiene que ver con la lógica: cambiar una frase del prompt
no debería ser un cambio de código. Va en un YAML con `version` declarada
(la sube quien lo cambia a conciencia) **y** una huella calculada del texto
(sha256, 12 caracteres) que viaja en la traza. La versión dice *qué querías*;
la huella dice *qué había de verdad* el día que se extrajo ese dato, aunque
nadie se acordara de subir la versión.

**Por qué la traza importa**: dentro de seis meses, ante un dato raro guardado
en base de datos (F-005), sabrás con qué modelo y con qué redacción exacta del
prompt se leyó. Sin eso, un cambio de prompt hace irreproducible todo el
histórico.

**Cambiar de proveedor** es configuración: `IA_PROVIDER` y `GEMINI_MODEL`.
Todo lo que sabe de Gemini cabe en **un fichero**
(`infrastructure/llm/gemini.py`), detrás de un puerto. El pipeline no se entera.

---

## 4 · Qué se ve desde fuera cuando esté hecho

Un endpoint nuevo: **`POST /api/extraer`**, con el PDF de **un** parte en
`multipart/form-data`. Devuelve `200` con:

```json
{
  "hash_parte": "9f2b…",
  "campos": { "codigo_obra": {"valor": "0677", "confianza_pct": 99}, … },
  "traza": {"proveedor": "gemini", "modelo": "gemini-2.5-flash",
            "prompt_key": "parte_posventa_es", "version_prompt": "1",
            "huella_prompt": "3f9a1c2b7d04"},
  "avisos": ["fecha_servicio: el modelo no devolvió el campo"]
}
```

Sin fichero → `400`. Extracción fallida → `502`. Parte demasiado grande →
`413`. Ni una clave más en el JSON: hay un test que comprueba el conjunto exacto
de claves, precisamente para que no se cuelen por la puerta de atrás campos de
F-004 o F-006.

Qué puede hacer un humano con eso, ya:

- Trocear una remesa con `POST /split` (F-002, ya hecho) y luego pedir la
  extracción parte a parte, viendo qué lee el modelo del papel real.
- Comprobar si Gemini lee los manuscritos de esta letra y estos escaneos,
  que es **la incógnita grande de todo el proyecto**.
- Comprobar si lee el «Página N» del pie, que es lo que hace viable F-014.

Encaja con la decisión de arquitectura ya tomada: `/split` rápido y **una
llamada por parte**, porque la Function App corta a los 230 s y una remesa de
22 partes a una llamada de IA cada uno no cabe en una sola petición.

---

## 5 · Las cuatro decisiones que ya tomaste, y qué implican

| Decisión | Consecuencia práctica |
|---|---|
| **D1 · `numero_pagina` entra ya** | Un noveno campo, sin código propio (viaja igual que los otros ocho). Coste: casi cero. Beneficio: F-014 deja de estar bloqueada por falta de dato. **F-003 sigue sin reagrupar nada**, con un test que lo vigila |
| **D2 · el endpoint entra ya** | Dos requisitos y dos tareas más (T15/T16), pero sin él la extracción no la puede ejercitar nadie: ni el front (F-007) ni tú en las verificaciones manuales. Sin endpoint, F-003 sería código que nadie puede tocar hasta F-007 |
| **D3 · la ruta sensible del prompt se aplaza a F-015** | Hoy **ningún test detecta que cambiar la redacción del prompt empeore la extracción** (el modelo está simulado: la suite seguiría verde con el prompt roto). Declarar la ruta sensible ahora sería protección falsa, porque el comando que la validaría no existe. El hueco lo tapa la verificación manual T20 hasta que exista F-015, que ya está dada de alta en el backlog con prioridad 15 |
| **D4 · el campo se llama `unidad`** | Ni `chalet` (backlog) ni `vivienda` (papel): `unidad`, el término del archivo de Posventa (`PARTES INCIDENCIAS / <UNIDAD> / PARTES FIRMADOS`). El mismo concepto se llama igual en código y en archivo. Los tres nombres quedan escritos en la spec para que nadie lo lea como un descuido |

Sobre D3, un apunte que la spec deja escrito y conviene que tengas presente:
el evaluador de F-015 **sería genérico** (le vale igual a `partes` y a
`albaranes`), así que por la regla de propagación su sitio es `arnes-base`, no
este repositorio. Aquí se quedarían solo los partes de prueba y el umbral.

---

## 6 · Lo que puede salir mal

1. **El acierto real del modelo no lo mide ningún test, y no lo va a medir.**
   La suite demuestra el *contrato* (que no falta ninguna clave, que la
   confianza se sanea, que los errores se manejan), **no la calidad de
   lectura**. Con manuscritos de mala letra y escaneos flojos, la única medida
   hoy es que tú ejecutes T20 contra un parte real y mires. Esto es lo más
   importante de esta lista.
2. **Coste y tiempo**: una llamada multimodal **por parte**, 22 partes por
   remesa de Mirasierra. La spec no da una cifra de coste ni de latencia
   esperada — **no está en la spec**. Si el modelo tarda más de lo previsto, lo
   absorbe la concurrencia limitada del front (F-007), no un lote más grande.
3. **`google-genai` es un SDK joven y cambia.** Mitigado: todo lo que sabe de
   él está en un fichero, detrás del puerto, con su propio test.
4. **Datos personales en logs.** El parte lleva DNI. Está prohibido volcar el
   contenido, la respuesta cruda o los valores extraídos en logs o mensajes de
   error; se registran tamaño, tiempo, modelo y nombres de campo. Es el error
   fácil de cometer «para depurar», y por eso está escrito como requisito
   (R15) *y* como riesgo.
5. **El parte de dos hojas sigue sin reagruparse.** Si llegó partido en dos por
   F-002, F-003 devolverá dos extracciones incompletas. Aceptado por ti el
   2026-08-18 para F-002; F-014 lo arregla.

---

## 7 · Qué te van a pedir a ti

**Dependencias nuevas que aprobar** (a `services/postventa-api/requirements.txt`,
mismas horquillas que ya corren en `partes`):

- `google-genai>=0.3` — el SDK nuevo de Gemini, no el deprecado
  `google-generativeai`.
- `pyyaml>=6.0` — para leer `config/prompts.yaml`.
- `tenacity>=8.2,<10.0` — reintentos con backoff, como manda
  `docs/CONVENTIONS.md`.

Ninguna más: sin OCR, sin Pillow, sin cliente HTTP propio.

**Credencial y coste**: hace falta `GEMINI_API_KEY` en el `.env` local del
servicio **solo para las dos verificaciones manuales**. Los tests no la
necesitan (la credencial es opcional en la configuración a propósito, para que
`/health` y la suite arranquen sin ella). La clave no se pega en ningún informe
ni en ningún commit. El coste es el de ~23 llamadas a `gemini-2.5-flash`:
1 de humo (T19) y 1 por parte real que quieras probar (T20).

**Verificaciones `MANUAL (humano)` que ejecutarás tú**, con el comando exacto
ya escrito en `tasks.md`:

- **T19** — humo contra el modelo real con un parte **sintético** (sin ningún
  dato personal). Se espera: nueve claves, traza con `gemini` /
  `gemini-2.5-flash`, `codigo_obra = 0677`, `numero_incidencia = RS26.08/0123`
  y `numero_pagina = "1"`. Aquí sí se pueden imprimir valores: son inventados.
  *(Comprobado: el generador sintético de F-002 imprime esos valores.)*
- **T20** — acierto sobre **un parte real** de Mirasierra
  (`docs/referencia/doc02871320260817093833.pdf`, que **no está versionado**:
  tiene que existir en tu árbol). El comando imprime, de cada campo, **solo el
  nombre, un booleano «vino o no vino» y la confianza**; el único valor que sale
  por pantalla es `numero_pagina`, porque un número de página no es dato
  personal y es justo el dato que hace viable F-014. Lo que se anota en
  `progress/current.md` son booleanos y confianzas, **nunca valores**.

Nada más: no hay que crear recursos en Azure, ni tocar SharePoint, ni tocar el
PostgreSQL compartido, ni ejecutar SQL. F-003 cae entera dentro de
`services/postventa-api/`.

---

## 8 · Cuánto trabajo es

**21 tareas**, todas obligatorias (no queda ninguna condicional tras tus cuatro
decisiones). De ellas:

- **8 son fase RED** (test primero, con la traza real en rojo pegada en
  `progress/impl_F-003.md`): T2, T4, T6, T7, T9, T11, T13, T15.
- **8 son implementación** de lo que esos tests piden: T3, T5, T8, T10, T12,
  T14, T16.
- **5 son de cierre**: documentación (T17), campaña de mutación con cero
  supervivientes (T18), las dos manuales (T19, T20) y `init.sh` en verde (T21).

Ocho ficheros de test nuevos y unos quince ficheros de producción, todos bajo
`services/postventa-api/`. Volumen comparable a F-002.

Las partes delicadas, por orden:

1. **T3, la guardia de red** en `conftest.py`: bloquear `socket.connect` en
   toda la suite para que «ni una llamada real» sea imposible, no una promesa.
   Puede chocar con algún plugin de pytest o con la cobertura; la spec deja
   **una variante B ya aprobada por escrito** para que el implementer no
   improvise. Cualquier tercera vía es `blocked`.
2. **T8, el prompt** (`config/prompts.yaml`): es lo único que ningún test
   valida de verdad. Si está mal redactado, la suite sigue verde y la
   extracción es basura. Aquí es donde miran T19/T20.
3. **T12, el adaptador de Gemini**: reintentos, parseo y logging sin datos
   personales, contra un SDK joven.
4. **T18, la mutación con cero supervivientes** (rigor `critico`): el saneo de
   confianzas y el completado de campos son código con muchas ramas pequeñas,
   justo lo que la mutación castiga.

---

## 9 · Lo que yo miraría antes de aprobar

Cuatro cosas concretas. Ninguna es un bloqueo, pero las cuatro son más baratas
de decidir ahora que a mitad de la implementación.

1. **Contradicción real entre `requirements.md` y `design.md` en el código HTTP
   del parte demasiado grande.** R18 dice «SI la extracción falla (R15/**R16**)
   → **502**»; `design.md` §4.5 y T16 dicen `ParteDemasiadoGrande` → **413**.
   Son dos respuestas distintas para el mismo caso. Hay que fijar una: 413 es
   la correcta semánticamente (*Payload Too Large*), así que lo que sobra es la
   mención de R16 en R18. Es una línea de la spec, pero si no se corrige, el
   reviewer tiene una excusa legítima para rechazar el trabajo.

2. **El camino 413 no tiene test.** T15 solo describe los tests de 200, 400 y
   502. Con rigor `critico` y campaña de mutación de cero supervivientes, el
   mapeo a 413 en `function_app.py` es superficie de mutantes sin cubrir: o se
   añade su test a T15, o T18 va a sacar supervivientes que habrá que
   justificar a mano.

3. **Un test declarado que ninguna tarea escribe.** La tabla de trazabilidad de
   `requirements.md` incluye
   `test_f003_r8_ningun_modulo_incrusta_el_texto_del_prompt` (segunda mitad de
   R8) y `design.md` §2 lo asigna a `test_f003_arquitectura.py`, pero **ninguna
   tarea lo manda escribir**: T2 escribe el de red (R19) y T13 añade el de R13.
   Es el test que garantiza que nadie vuelva a incrustar el prompt en el
   código, o sea, justo el requisito que más se degrada solo. Una línea en T13.

4. **Discrepancia menor de recuento en el informe del spec-author.**
   `progress/spec_F-003.md` dice «21 tareas, **9** con fase RED»; en `tasks.md`
   hay **8**. No cambia nada del trabajo, pero conviene cuadrarlo para que el
   reviewer no persiga una tarea fantasma.

Y una observación que **no** es un defecto de la spec, sino la pregunta que de
verdad decide si este proyecto sale: **T20 es el momento de la verdad del
proyecto entero**. Si Gemini no lee los manuscritos de estos escaneos, no
falla F-003 (su contrato se cumpliría igual), falla la premisa. Yo ejecutaría
T20 en cuanto T16 esté hecho, **antes** de invertir en T17–T18, y no al final
de la lista donde está ahora. Es un cambio de orden, no de alcance, y ahorra la
campaña de mutación entera si la respuesta es mala.

Lo que **no está en la spec** y he buscado: ninguna estimación de coste por
llamada ni de latencia esperada por parte, ningún umbral de confianza a partir
del cual un campo se considere dudoso (eso será F-004), y ningún criterio de
«qué porcentaje de acierto sería aceptable» en T20 — el resultado se anota,
pero no hay listón declarado. Ese listón es, literalmente, lo que viene a
poner F-015.
