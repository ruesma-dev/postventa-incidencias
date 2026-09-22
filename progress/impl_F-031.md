<!-- progress/impl_F-031.md -->
# F-031 · Bloque 2 (backend) · informe de implementación

> Rama `feature/F-031-nombrado-persistido`. Rigor **`critico`**.
> Encargo: **solo el Bloque 2 de `tasks.md`** (T1–T7). El Bloque 3 (front),
> el 4 (alcance y documentación) y el 5 (manuales y mutación de la feature
> entera) **no se han tocado** — ver §7.
>
> **No se ha escrito en ningún sistema externo.** Ni SharePoint, ni Sigrid, ni
> Azure, ni PostgreSQL. No hay DDL. Todos los tests corren sin red, sin BBDD y
> sin IA, con la guarda de socket de `tests/conftest.py` puesta.

## 1 · Qué cambió, en una frase

La carpeta y el nombre del fichero que se archiva salen ahora del
`codigo_obra` y el `numero_incidencia` **que constan guardados** para el
parte, y los dos que vienen en el cuerpo de `POST /api/archivar` dejan de
nombrar y pasan a **cotejar**: si no cuadran, **409 y no se archiva nada**.

El defecto que cierra estaba medido en `requirements.md` §0.1 y era una
asimetría: desde F-030 la puerta de estado dejaba pasar mirando los códigos
guardados y el PDF se nombraba con los declarados. Coincidían porque el front
manda lo que leyó — una costumbre, no una garantía.

## 2 · Ficheros tocados

### 2.1 · Producción (5)

| Fichero | Qué |
|---|---|
| `services/postventa-api/domain/models/nombrado.py` | `es_el_mismo_codigo(uno, otro)`, dominio puro sobre `normalizar_codigo`, y su entrada en `__all__`. Nada más del módulo se toca |
| `services/postventa-api/domain/models/errores.py` | `CodigosNoCoinciden` con `.motivo`, más la línea de la cabecera que enumera las familias por feature |
| `services/postventa-api/application/pipelines/paso_archivo.py` | `CodigosDelParte`, `_codigos_guardados(ctx)`, `_exigir_codigos_declarados(...)` en el punto **1 bis**, el nombrado desde lo guardado, `_campo` **retirado**, `codigos_declarados` en la firma y la enmienda fechada del módulo |
| `services/postventa-api/interface_adapters/api/archivar.py` | Pasa `codigos_declarados`; `_como_contexto` deja de rellenar los dos campos (y pierde sus dos parámetros); cabecera con la enmienda fechada |
| `services/postventa-api/function_app.py` | `CodigosNoCoinciden` al `except` que ya daba **409**, y el comentario del endpoint explicando los tres motivos que hoy caben dentro de ese 409 |

### 2.2 · Tests nuevos (2)

- `services/postventa-api/tests/test_f031_nombrado_persistido.py` — 39 casos:
  R1, R2, R4 (la función pura), R7, R8, R11 y R12.
- `services/postventa-api/tests/test_f031_cotejo_de_codigos.py` — 27 casos:
  el error de dominio, R3, R4 (desde el borde), R5, R6, R9, R10, R11 y R25.

### 2.3 · Tests ya existentes, adaptados (3 ficheros, 5 casos)

Todos con su **enmienda fechada** dentro del propio docstring, al estilo de
las de F-030 y F-033, y todos conservando la intención del caso original:

| Caso | Qué le pasó |
|---|---|
| `test_f006_archivar_http.py` · cuerpo con `06\|77` | Seguía siendo 409 y seguía sin subir nada, pero **por otro motivo**: el nombrado ya no mira el cuerpo, así que lo que dispara ese `06\|77` es el cotejo. Ahora se afirma sobre el motivo, que antes no se miraba |
| `test_f006_archivar_http.py` · **caso nuevo** | Nombre imposible **desde el código guardado** (R8), que es donde el camino de F-006 R7 sigue siendo alcanzable |
| `test_f006_archivar_http.py` · los dos de `_como_contexto` | Pasan a exigir los **nueve** campos vacíos y a cero |
| `test_f033_l1_desde_el_almacen.py` · `r9_el_nombrado_va_antes_que_l1` | Vacía el código **guardado** en vez del del contexto, que ya no nombra. R9 no cambia; cambia de dónde se le quita la entrada |
| `test_f033_l1_desde_el_almacen.py` · `r21_la_firma_no_ofrece_ninguna_forma_de_forzar` | Recoge `codigos_declarados` en el conjunto exacto de parámetros, **en vez de relajarse a un `not in`**: lo que R21 exige es que la firma entera esté a la vista |
| `test_f033_archivar_http.py` · circuito F-032 | Ver §6: la spec lo daba por intacto y no lo era |

### 2.4 · Documentación de la feature

- `specs/F-031-nombrado-persistido/tasks.md`: T1–T7 marcadas, con la
  constancia de la aprobación del humano en T1.
- `progress/current.md`: bloque nuevo arriba con lo que falta.

**No se ha tocado** `docs/ARCHITECTURE.md`, `specs/F-006-sharepoint/`,
`specs/F-030-veredicto-persistido/` ni `azure-apps/`: son T12, del Bloque 4.

## 3 · Decisiones de diseño y por qué

1. **Los códigos se leen de `ctx.situacion.validacion`** (D-1, aprobada). Da
   una propiedad que ningún otro camino da gratis: el fichero se nombra, byte
   por byte, con los dos valores que la puerta acaba de dar por buenos. La
   alternativa —dos campos nuevos en `SituacionParte`— metía dos
   representaciones del mismo dato en el mismo objeto.
2. **El cotejo va en el punto 1 bis**, después de la puerta y antes del
   nombrado, de la traza previa y de cualquier llamada al puerto (R5). A
   partir del paso 4 ya hay fila en `postventa.archivos` y a partir del 5 ya
   se habló con SharePoint; con L1 de F-033 —que corta por `hash` + estado y
   no admite forzar el re-archivo— un parte archivado en la carpeta
   equivocada **no se arregla desde el circuito**. Y después de la puerta, no
   antes, porque el cotejo necesita la situación que la puerta lee:
   adelantarlo costaría una segunda consulta (contra R2).
3. **`es_el_mismo_codigo` vive en el dominio**, no en el paso. El dueño de
   «qué es el mismo código» es quien lo normaliza (F-028 R47, F-032):
   `normalizar_codigo` ya cambió una vez, el 2026-09-17, y el cotejo tiene que
   moverse con ella sin que nadie se acuerde.
4. **Dos vacíos dan `True`** en `es_el_mismo_codigo`. De ese caso opina R7 un
   paso más adelante, con `NombradoImposible` diciendo cuál falta; que el
   cotejo también opinara produciría dos errores distintos para el mismo hecho.
5. **`_campo` se retira entero**, no se deja «por si acaso». Era el único
   consumidor de `ctx.extraccion` en el paso y dejarlo vivo habría dejado viva
   la segunda fuente que la feature viene a cerrar. Es la misma decisión que
   tomó F-033 con `traza_previa` (su D-2), y tiene test: el parte se archiva
   **sin extracción ninguna**.
6. **`codigos_declarados` es opcional y, cuando falta, no abre nada.** El
   camino sin cotejo sigue nombrando con lo guardado (R11), y eso tiene su
   propio test parametrizado: es la mitad silenciosa del requisito.
7. **`CodigosNoCoinciden` es excepción propia** y no `ParteNoApto` reutilizada
   (D-2, §3.2 del diseño). Los tres son 409 y llevan a acciones opuestas; éste
   es el único en el que reintentar, **después de guardar**, funciona. Si
   heredara de cualquiera de las otras dos, el `except` del borde se la
   tragaría sin que ningún test lo notara.

## 4 · Fase RED · las trazas reales

### 4.1 · T2 · `es_el_mismo_codigo`

Comando: `./.venv/Scripts/python.exe -m pytest tests/test_f031_nombrado_persistido.py -k r4 -q`

```
=================================== ERRORS ====================================
___________ ERROR collecting tests/test_f031_nombrado_persistido.py ___________
ImportError while importing test module 'C:\...\tests\test_f031_nombrado_persistido.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
..\..\..\..\AppData\Local\Programs\Python\Python312\Lib\importlib\__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests\test_f031_nombrado_persistido.py:31: in <module>
    from domain.models.nombrado import es_el_mismo_codigo
E   ImportError: cannot import name 'es_el_mismo_codigo' from 'domain.models.nombrado' (C:\...\domain\models\nombrado.py)
=========================== short test summary info ===========================
ERROR tests/test_f031_nombrado_persistido.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.66s
```

Después de implementarla: `17 passed in 0.23s`.

### 4.2 · T3 · `CodigosNoCoinciden`

Comando: `./.venv/Scripts/python.exe -m pytest tests/test_f031_cotejo_de_codigos.py -k errores -q`

```
=================================== ERRORS ====================================
____________ ERROR collecting tests/test_f031_cotejo_de_codigos.py ____________
ImportError while importing test module 'C:\...\tests\test_f031_cotejo_de_codigos.py'.
Traceback:
tests\test_f031_cotejo_de_codigos.py:27: in <module>
    from domain.models.errores import (
E   ImportError: cannot import name 'CodigosNoCoinciden' from 'domain.models.errores' (C:\...\domain\models\errores.py)
=========================== short test summary info ===========================
ERROR tests/test_f031_cotejo_de_codigos.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.66s
```

Después: `3 passed in 0.12s`.

### 4.3 · T4 · el rojo de verdad, con el defecto a la vista

Éste es el que importa, porque no es un `ImportError`: es el **comportamiento
viejo funcionando**. Comando:
`./.venv/Scripts/python.exe -m pytest tests/test_f031_cotejo_de_codigos.py -q`

```
>       assert respuesta.status_code == 409, caso
E       AssertionError: la obra sin ceros
E       assert 200 == 409
E        +  where 200 = <azure.functions._http.HttpResponse object at 0x...>.status_code

tests\test_f031_cotejo_de_codigos.py:525: AssertionError
------------------------------ Captured log call ------------------------------
INFO     function_app:function_app.py:796 archivar: parte=9f2b0011aabb fichero=677 - RS26.08 - 0123 PARTE FIRMADO.pdf carpeta=Postventa/677 estado=archivado avisos=0
=========================== short test summary info ===========================
FAILED ...::test_f031_r3_un_cuerpo_que_miente_responde_409_diciendo_cual[otra obra-campos0-código de obra-0999]
FAILED ...::test_f031_r3_un_cuerpo_que_miente_responde_409_diciendo_cual[otra incidencia-campos1-nº de incidencia-RS26.09/0999]
FAILED ...::test_f031_r3_un_cuerpo_que_miente_responde_409_diciendo_cual[la obra sin sus ceros-campos2-código de obra-677]
FAILED ...::test_f031_r3_un_cuerpo_que_miente_responde_409_diciendo_cual[las dos: manda la primera que falla-campos3-código de obra-0999]
FAILED ...::test_f031_r3_el_409_nombra_tambien_el_valor_guardado
FAILED ...::test_f031_r5_ante_una_divergencia_no_se_escribe_ni_se_llama_a_nadie
FAILED ...::test_f031_r11_nada_del_cuerpo_abre_ni_mueve_la_puerta[otra obra entera-campos0]
FAILED ...::test_f031_r11_nada_del_cuerpo_abre_ni_mueve_la_puerta[una obra que existe de verdad-campos1]
FAILED ...::test_f031_r11_nada_del_cuerpo_abre_ni_mueve_la_puerta[la obra sin ceros-campos2]
9 failed, 17 passed in 2.71s
```

**Lo que dice esa línea de log es el defecto entero**: el cuerpo mandó `677`,
la base guardaba `0677`, y el sistema respondió **200** archivando en
`carpeta=Postventa/677` — otra carpeta, con el PDF que lleva el DNI
manuscrito de un cliente dentro.

Y el conjunto ni siquiera arrancaba:
`./.venv/Scripts/python.exe -m pytest tests/test_f031_*.py -q` →
`ImportError: cannot import name 'CodigosDelParte' from 'application.pipelines.paso_archivo'`.

### 4.4 · Rojo intermedio de T5/T6

Antes de que el borde pasara los códigos (T7), los 10 casos de
`test_f031_cotejo_de_codigos.py` que van por HTTP seguían rojos, con el mismo
`200 == 409`. Es lo esperado: T6 deja el cotejo puesto y T7 es quien le da de
comer desde el borde.

## 5 · Verificaciones de cada tarea, con su resultado real

| Tarea | Comando | Resultado |
|---|---|---|
| T1 | — | **CUMPLIDA**: aprobación del humano del 2026-09-22 («si», D-1 a D-7), transcrita y fechada en `progress/current.md`, commit `35ad69d` |
| T2 | `pytest tests/test_f031_nombrado_persistido.py -k r4` | **17 passed** |
| T3 | `pytest tests/test_f031_cotejo_de_codigos.py -k errores` | **3 passed** |
| T4 | `pytest tests/test_f031_*.py -q` | **rojo**, §4.3 |
| T5 | `pytest tests/test_f031_nombrado_persistido.py -q` | **38 passed** |
| T5 | `pytest tests/test_f006_paso_archivo.py tests/test_f033_*.py tests/test_f019_orden_archivado.py -q` | **182 passed, 4 skipped** |
| T6 | el caso de R5 + el fichero de nombrado | **39 passed** (cero escrituras en el repositorio, cero llamadas al archivador ante divergencia) |
| T7 | `pytest tests/test_f006_archivar_http.py tests/test_f030_circuito_borde_a_borde.py tests/test_f031_*.py -q` | **90 passed** |
| Cierre | `bash harness/init.sh` | **VERDE** |

Salida del arnés al cerrar el bloque:

```
62 passed in 6.51s
[OK] pytest en verde (con medición de cobertura)
3056 passed, 24 skipped in 94.81s (0:01:34)
[OK] servicio api (services/postventa-api): pytest en verde
[OK] servicio front (services/postventa-front): pytest en verde (caché: árbol sin cambios desde el último verde)
[OK] PUERTA COBERTURA: 100.0% de 28 líneas cambiadas cubiertas (28/28, umbral 80%, nivel critico)
ENTORNO LISTO. Puedes trabajar.
```

## 6 · Desviaciones respecto a la spec, declaradas

### 6.1 · `test_f033_archivar_http.py` NO pasaba sin cambios

`design.md` §9 dice, literal, que ese fichero «pasa sin cambios» porque «el
cuerpo y la situación ya usan los mismos valores (`0677` / `RS26.08/0123`, o
`0626` / `RS26.09/0178`)». **Medido: no era cierto.** Su caso
`test_f033_circuito_f032_el_nombre_viejo_se_queda_y_se_avisa` manda
`FORMULARIO_F032` (`0626` / `RS26.09/0178`) contra un repositorio construido
por `_base_con_el_parte_apto()`, que guardaba el veredicto del
`contexto_apto()` **por defecto**, es decir `0677` / `RS26.08/0123`. Con el
cotejo nuevo eso es un 409:

```
E       assert 409 == 200
INFO  function_app: archivar no procede: el código de obra de la petición
      («0626») no es el que consta guardado para este parte («0677») ...
```

**Arreglo**: `_base_con_el_parte_apto` acepta ahora los códigos que constan
guardados, y ese caso le pasa `0626` / `RS26.09/0178`. Es poner el mundo en su
sitio, no aflojar nada: cuando una petición llega de verdad a
`/api/archivar`, esos códigos ya están en `postventa.partes`. Lo que sigue
siendo viejo es **el nombre de la traza**, que es de lo que va el caso, y el
test sigue afirmando lo mismo que afirmaba (cero subidas, los dos avisos, la
respuesta con el nombre viejo).

### 6.2 · Precedencia entre R7 y R3 cuando lo guardado está vacío

La spec no lo resuelve y conviene que el reviewer lo mire.

R7 dice que si el código guardado está vacío, la respuesta es el **409 de
nombrado imposible** diciendo cuál falta. Pero el diseño fija el cotejo
**antes** del nombrado (§4.2, y es R5), y R10 mantiene los dos campos del
cuerpo **obligatorios y no vacíos**. Conclusión: desde el endpoint, con lo
guardado vacío y el cuerpo lleno, el que habla es el **cotejo**
(`CodigosNoCoinciden`), no `NombradoImposible`.

**Se ha implementado lo que dice el diseño**, sin caso especial (§4.4 dice
«compara campo a campo… levanta `CodigosNoCoinciden` nombrando el primero que
falla»). Lo que R7 exige en sustancia se conserva entero: **409**, **no se
archiva nada**, el mensaje **nombra cuál** de los dos no cuadra, y el valor
del cuerpo **no sustituye** al guardado. Y de los dos 409 posibles, el que
sale es el más accionable: dice que hay que guardar la corrección, que es
exactamente lo que falta.

El camino de `NombradoImposible` por R7 **sigue vivo y con test** sobre el
paso, llamándolo sin `codigos_declarados` — que es el caso que `design.md`
§4.1 describe — con cuatro variantes (obra vacía, obra de solo blancos,
incidencia vacía, incidencia de solo blancos), y comprobando además que el
contexto llega con los dos códigos llenos y aun así no se archiva nada.

### 6.3 · El reparto de un caso entre los dos ficheros de test

`tasks.md` T4 pone el «caso central de R1» (situación `0677`, cuerpo `0999` →
no se sube nada) sin decir en qué fichero. Vive en
`test_f031_cotejo_de_codigos.py`, porque lo que afirma es R3 + R5 —cero
llamadas a los dos puertos— y porque, si viviera en el fichero de nombrado,
la verificación de T5 («ese fichero en verde») no se habría podido cumplir
hasta T6. El fichero de cotejo dice en su cabecera que ese caso es la
excepción que se ejercita sobre el paso y no por HTTP.

### 6.4 · Dos frases reescritas por la guarda de F-026 R24

`test_f026_puertas.py` comprueba sobre el **texto fuente** de los tres
handlers que no aparece la raíz «aprob»: es la guarda contra leer la
aprobación del cuerpo. Dos frases de mi enmienda en `archivar.py` decían «la
puerta aprobaba los códigos guardados» y la disparaban. **Se reescribió el
comentario; no se tocó la guarda.** Es la puerta más importante del proyecto
y no se afloja porque un comentario se cruce con ella.

## 7 · Lo que queda fuera de este encargo (y sigue pendiente)

- **Bloque 3 · el front (T8–T10).** `vaciarPendientes()` en
  `js/autoguardado.js` y la espera en `confirmarArchivo`. **Sin empezar.**
- **Bloque 4 (T11–T13)**: `test_f031_alcance_cerrado.py`, la documentación
  (`docs/ARCHITECTURE.md`, las notas en las specs de F-006 y F-030, y dejar
  escrito que `azure-apps/postventa_incidencias.md` no cambia) y la anotación
  de H-1. **Sin empezar.** H-1 ya está recogido en la ficha ampliada de F-034,
  por decisión del humano del 2026-09-22.
- **Bloque 5 (T14–T16)**: V1 y V2 manuales y la campaña de mutación de la
  feature completa. **Sin empezar.**

**No se ha tocado nada de lo que el encargo declaró fuera**: `adjuntar.py`,
`cerrar.py`, `paso_grafico.py`, `paso_cierre.py` (hallazgo H-1, que es F-034),
ni `harness/features.json`, ni una línea de SQL, ni el puerto de persistencia.

### ⚠️ Esto no se despliega solo

`design.md` §1.3 es explícito y conviene repetirlo aquí: desplegar **solo** el
backend **empeora** el caso de la corrección reciente. Quien corrija un código
y pulse «archivar y cerrar» antes de los 1.500 ms de rebote se llevará hoy un
**409** que no entiende, porque su corrección todavía no está guardada. Las
dos mitades van juntas: **no se despliega F-031 hasta tener el Bloque 3**.

## 8 · Verificaciones `MANUAL (humano)` pendientes

Las dos son del Bloque 5 y **no se han recorrido**:

- **T14 / V1** · con `func start` y `dev_server.py` en local: corregir el
  código de obra y pulsar «archivar y cerrar» antes de 1,5 s. **Requiere el
  Bloque 3**, porque lo que se espera comprobar es que el vaciado evita el
  409. La segunda mitad —forzar el 409 desde la consola— sí sería ejercitable
  ya, y pintaría el mensaje nuevo tal cual. No sube nada:
  `ARCHIVO_HABILITADO` está apagado en local.
- **T15 / V2** · en el entorno desplegado y solo con un parte que el humano
  autorice: que el nombre y la carpeta siguen siendo los mismos que antes de
  la feature. Única comprobación contra la biblioteca real, y no procede hasta
  que la feature esté completa.

## 9 · Evidencias

Números **medidos**, no estimados. Salidas de esta misma sesión.

| Evidencia | Medida |
|---|---|
| **Tests ejecutados** y resultado | Servicio `api`: **3.056 passed, 24 skipped**, 0 failed. Arnés: **62 passed**. Servicio `front`: verde (caché, árbol sin cambios) |
| **Tests nuevos** de la feature | **66** (39 en `test_f031_nombrado_persistido.py` + 27 en `test_f031_cotejo_de_codigos.py`), todos con nombre trazable `test_f031_rN_…` |
| **Cobertura de las líneas cambiadas** | **100,0 %** — 28/28 líneas, umbral 80 %, nivel `critico`. Línea `PUERTA COBERTURA` de `bash harness/init.sh` |
| **Tiempo de ejecución de la suite** | **94,81 s** el servicio `api`; 6,51 s el arnés |
| **Mutantes generados y supervivientes** | **3 generados, 3 evaluados, 3 muertos, 0 supervivientes, 0 timeouts**, en 82,7 s con 3 workers. Informe: `progress/mutacion_F-031.md`. Ninguna sección queda en `PENDIENTE` |
| **Lint** | `python -m ruff check .`: **61 avisos, los mismos que antes de la feature** (deuda previa). El único aviso nuevo que introduje —un `I001`— se corrigió en el commit `2077f39` |

### 9.1 · La campaña de mutación, con nombre y apellidos

`python -m harness.mutacion --feature F-031`. El alcance son **305 líneas de
producción en 5 ficheros**; de ahí salen solo **3 mutantes** porque casi todo
lo cambiado es docstring y enmiendas fechadas, y el mutador solo muerde
operadores y constantes reales.

| Mutante | Veredicto |
|---|---|
| `nombrado.py:188` · `normalizar_codigo(uno) == normalizar_codigo(otro)` → `!=` | **muerto** |
| `paso_archivo.py:579` · `if not es_el_mismo_codigo(...)` → `if es_el_mismo_codigo(...)` | **muerto** |
| `paso_archivo.py:142` · `@dataclass(frozen=True)` → `frozen=False` | **muerto en la segunda vuelta** |

El tercero **sobrevivió en la primera campaña** (3 mutantes, 2 muertos, 1
superviviente, 86,9 s). No se justificó como equivalente: se **mató**, con un
test que ejercita la inmutabilidad de `CodigosDelParte`
(`test_f031_r11_los_codigos_resueltos_no_se_pueden_reescribir`, commit
`55db9c8`). La inmutabilidad ahí no es decoración —es la misma razón que
`DestinoArchivo` tiene escrita— y una guardia que nadie ejercita es una
guardia que nadie sabe si funciona.

Segunda campaña, tras el test: **3 de 3 muertos, 0 supervivientes**.

> Esta campaña es la del **Bloque 2**. La T16 de `tasks.md` es la de la
> **feature entera** y sigue pendiente: se lanzará cuando el front esté hecho,
> porque el alcance del diff cambiará.

## 10 · Commits del bloque

```
55db9c8 F-031: mata el superviviente de la campana de mutacion (frozen de CodigosDelParte)
2077f39 F-031: imports del test de cotejo al inicio del modulo (ruff I001)
db9703d F-031 T7: el borde pasa los codigos declarados y el 409 nuevo sale por HTTP
cf17133 F-031 T6: el cotejo en el punto 1 bis, antes de dejar cualquier rastro
ac4d353 F-031 T5: el nombrado sale de los codigos guardados y _campo desaparece
de86aad F-031 T4 (RED): los tests de R1-R12, antes de tocar el paso
e9cb2dc F-031 T3: CodigosNoCoinciden, con su docstring diciendo por que es propio
d08de87 F-031 T2: es_el_mismo_codigo, dominio puro sobre normalizar_codigo
```

Ningún `git push`, ningún PR, ningún commit fuera de la rama de la feature.

---

# F-031 · Bloque 3 (front) · informe de implementación

> Rama `feature/F-031-nombrado-persistido`. Rigor **`critico`**.
> Encargo: **solo el Bloque 3 de `tasks.md`** (T8–T10). El Bloque 4 (alcance y
> documentación) y el 5 (manuales y mutación de la feature entera) **no se han
> tocado** — ver §7 bis.
>
> **No se ha escrito en ningún sistema externo.** Ni SharePoint, ni Sigrid, ni
> Azure, ni PostgreSQL. No hay DDL. Todos los tests corren sin red, sin BBDD y
> sin IA: el temporizador del front entra **inyectado**, como ya hacía F-026.
>
> **No se ha tocado nada de lo que el encargo declaró fuera**: `adjuntar.py`,
> `cerrar.py`, `paso_grafico.py`, `paso_cierre.py` (eso es F-034), ni
> `harness/features.json`, ni una línea del backend.

## 1 bis · Qué cambió, en una frase

El front **fuerza el guardado de lo escrito y sin guardar, y lo espera**, antes
de calcular la tanda y lanzar la primera petición de archivo. Si ese guardado no
sale bien, **la tanda no se lanza** y se dice por qué.

Ésta es la mitad que faltaba. `design.md` §1.3 es explícito: desplegar **solo**
el backend **empeora** el caso de la corrección reciente. Con las dos mitades,
quien corrija un código de obra y pulse «archivar y cerrar» dentro de los
1.500 ms del rebote ya no manda al backend un código que no está en la base:
se guarda primero, y el cotejo del Bloque 2 no tiene nada que rechazar.

## 2 bis · Ficheros tocados

### 2 bis.1 · Producción (2)

| Fichero | Qué |
|---|---|
| `services/postventa-front/js/autoguardado.js` | `vaciarPendientes()`, la constante `AVISO_SIN_GUARDAR`, el tope `RONDAS_DE_VACIADO`, la promesa del guardado en vuelo conservada (`promesaEnVuelo`), el registro `partesConPendiente` y la enmienda fechada del módulo |
| `services/postventa-front/js/app.js` | `confirmarArchivo` espera el vaciado **después** de `Confirmacion.resolver` y **antes** de `this.pendientes()`, y corta con `return` si no sale bien |

### 2 bis.2 · Tests nuevos (2)

- `services/postventa-front/tests_js/autoguardado_vaciado.test.js` — **12
  casos**: R18 (4), R20 (3), R21 (2), R22 (3). Nombre trazable `f031 RN: …`.
- `services/postventa-front/tests/test_f031_front.py` — **6 casos** sobre el
  texto fuente de `app.js`. Ver §6 bis.1: es una **adición** respecto a
  `tasks.md`.

### 2 bis.3 · Tests ya existentes

**Ninguno se ha tocado.** `autoguardado.test.js` (F-026), `confirmacion.test.js`
(F-025) y `circuito.test.js` siguen letra por letra como estaban, que es
exactamente lo que pedían las verificaciones de T9 y T10.

## 3 bis · Decisiones de diseño y por qué

1. **`vaciarPendientes()` vive en `js/autoguardado.js`, no en `app.js`.** Lo
   dice la cabecera del propio módulo y la regla de oro de `app.js`: lo que se
   puede probar con `node --test` no se deja en el fichero de Alpine. Lo que
   queda en `app.js` es **el orden de tres líneas**, y para eso está §6 bis.1.
2. **El módulo conserva ahora la promesa del guardado en vuelo.** F-026 solo
   necesitaba la bandera `enVuelo` («¿hay uno en el aire?»); F-031 necesita
   **esperarlo**, y una bandera no se espera. `promesaEnVuelo` se asigna fuera
   de la cadena, porque el último `.then` corre en una microtarea posterior:
   cuando `disparar` devuelve, la promesa ya está puesta.
3. **Registro `partesConPendiente`**, y es lo que hace cierto el «de cualquier
   parte» de R18. `pendientes` guarda **valores**, y para guardarlos hace falta
   el parte entero (`guardar` es `revalidarYGuardar`, que necesita sus bytes y
   su extracción). Hasta F-026 bastaba el parte que venía en la pulsación
   —siempre se guardaba el recién tecleado—; el vaciado tiene que poder guardar
   el de un parte cuyo guardado se cayó hace dos papeles. Se limpia en los dos
   sitios donde se limpia `pendientes`, para que no crezca sin fin.
4. **Tope de tres rondas** (`RONDAS_DE_VACIADO`). No es adorno: `disparar` se
   reprograma cuando encuentra otro guardado en vuelo, y un bucle sin tope no
   terminaría nunca con alguien tecleando delante (riesgo 4 de `design.md`
   §13). Pasadas las tres, `{ok:false}` y la tanda no se lanza, que es lo que
   hay que hacer de todas formas.
5. **El vaciado reutiliza `hayCambios` y `disparar` tal y como F-026 los
   dejó**, en vez de escribir un segundo criterio. De ahí salen gratis R21 (no
   toca `parte.ediciones`, porque el módulo nunca lo ha tocado) y R22 (sin
   cambios, ni una petición). Un segundo criterio de «hay cambios» habría
   divergido del primero, que es justo lo que este repositorio evita.
6. **`AVISO_SIN_GUARDAR` vive en el módulo**, no en `app.js`, por lo mismo que
   `AVISO_CADUCADA` vive en `js/confirmacion.js`: `app.js` es la única
   habitación de la casa sin tests, y un texto escrito ahí no lo comprueba
   nadie. Se **apoya** en el `MENSAJE_FALLO` de F-026 y solo añade lo que
   aquél no podía decir —que la tanda no ha salido—, para no dar dos
   explicaciones del mismo hecho.
7. **El vaciado va después de `Confirmacion.resolver`.** Si se colara antes, el
   tiempo del guardado contaría dentro de la ventana de la confirmación única
   de F-025 y una base lenta la caducaría sola. Y si el vaciado falla, la
   confirmación ya está consumida y hay que volver a confirmar: **correcto**,
   porque lo que se iba a archivar ha cambiado.
8. **El vaciado va antes de `this.pendientes()`** (R19). Guardar revalida
   (`revalidarYGuardar`, F-026 R50) y una corrección puede tumbar un veredicto:
   una tanda calculada antes archivaría un parte que acaba de dejar de ser
   archivable.

## 4 bis · Fase RED · las trazas reales

### 4 bis.1 · T8 · los doce casos del vaciado

Comando: `cd services/postventa-front && node --test "tests_js/*.test.js"`

```
✖ f031 R18: el vaciado no espera al rebote, fuerza el guardado y lo espera (3.3586ms)
✖ f031 R18: el vaciado retira el rebote en espera en vez de dejarlo vivo (0.5373ms)
✖ f031 R18: con un guardado en vuelo, el vaciado espera a que termine (2.2569ms)
✖ f031 R18: se vacía lo pendiente de CUALQUIER parte, no solo del abierto (1.2033ms)
✖ f031 R20: si el guardado se cae, el vaciado devuelve que NO (0.4689ms)
✖ f031 R20: el vaciado tiene tope de rondas y no se queda en bucle (0.496ms)
✖ f031 R20: el aviso dice que no se ha archivado nada y se apoya en el de F-026 (1.918ms)
✖ f031 R21: aunque el vaciado falle, lo que la persona escribió sigue ahí (0.4197ms)
✖ f031 R21: el vaciado correcto tampoco toca `ediciones` ni lo que leyó la IA (0.4298ms)
✖ f031 R22: sin nada escrito, el vaciado no dispara ni un guardado (0.6742ms)
✖ f031 R22: escribir y deshacer no deja nada que vaciar (0.4894ms)
✖ f031 R22: un segundo vaciado seguido no vuelve a escribir (0.3681ms)
ℹ tests 310
ℹ pass 298
ℹ fail 12
```

Con el motivo, el mismo en los doce:

```
test at tests_js\autoguardado_vaciado.test.js:168:1
✖ f031 R18: el vaciado no espera al rebote, fuerza el guardado y lo espera
  TypeError: montaje.auto.vaciarPendientes is not a function
      at TestContext.<anonymous> (...\tests_js\autoguardado_vaciado.test.js:177:38)
```

**Lo que dice ese rojo**: 298 casos ya existentes siguen pasando —F-026 entre
ellos— y los 12 nuevos caen porque el método no existe. Después de T9:
`ℹ tests 310 / ℹ pass 310 / ℹ fail 0`.

### 4 bis.2 · T10 · el orden de `confirmarArchivo`

El fichero de tests de `app.js` se escribió **después** del cambio, así que
para tener el rojo de verdad se revirtió `js/app.js` a su versión anterior
(`git checkout --`) y se ejecutó contra ella. Comando:
`cd services/postventa-front && python -m pytest tests/test_f031_front.py -q`

```
    def test_f031_r20_si_el_vaciado_falla_no_se_lanza_la_tanda(confirmar):
>       assert "if (!vaciado.ok)" in confirmar, (
            "`confirmarArchivo` no mira el resultado del vaciado (R20)"
        )
E       AssertionError: `confirmarArchivo` no mira el resultado del vaciado (R20)
E       assert 'if (!vaciado.ok)' in 'async confirmarArchivo() {\n      const decision = window.Confirmacion.resolver(\n ...

tests\test_f031_front.py:142: AssertionError
=========================== short test summary info ===========================
FAILED tests/test_f031_front.py::test_f031_r18_confirmar_archivo_espera_el_vaciado
FAILED tests/test_f031_front.py::test_f031_r19_la_tanda_se_calcula_despues_del_vaciado
FAILED tests/test_f031_front.py::test_f031_r19_el_vaciado_va_despues_de_resolver_la_confirmacion
FAILED tests/test_f031_front.py::test_f031_r20_si_el_vaciado_falla_no_se_lanza_la_tanda
FAILED tests/test_f031_front.py::test_f031_r20_el_aviso_es_el_del_modulo_y_no_uno_inventado_aqui
5 failed, 1 passed in 0.16s
```

**El que pasó, y por qué se declara**: `test_f031_r20_el_aviso_existe_de_verdad_en_el_modulo`
comprueba que `js/autoguardado.js` exporta `AVISO_SIN_GUARDAR`, y **T9 ya lo
había puesto**. Es un control de que el nombre que `app.js` pinta no es
huérfano, no un test del cambio de T10. Se deja dicho para que no cuente como
rojo lo que no lo fue.

Restaurado `app.js`: **6 passed**.

## 5 bis · Verificaciones de cada tarea, con su resultado real

| Tarea | Comando | Resultado |
|---|---|---|
| T8 | `node --test "tests_js/*.test.js"` | **rojo**: 310 tests, 298 passed, **12 failed** (los doce nuevos) — §4 bis.1 |
| T9 | `node --test "tests_js/*.test.js"` | **310 passed, 0 failed**, con `autoguardado.test.js` de F-026 **sin tocar** |
| T10 | `node --test "tests_js/*.test.js"` | **310 passed**, con `confirmacion.test.js` y `circuito.test.js` **sin tocar** |
| T10 | `pytest tests -q` (servicio `front`) | **256 passed in 4.71s** (250 antes + los 6 nuevos), incluido el puente `tests/test_f007_js.py` |
| Cierre | `bash harness/init.sh` | **VERDE** |

> **Nota sobre el comando de `tasks.md`.** T8, T9 y T10 lo escriben como
> `node --test tests_js`. Con Node 24 —el instalado: **v24.14.1**— un argumento
> que es un **directorio** se intenta cargar como módulo y la ejecución muere
> con `MODULE_NOT_FOUND` antes de descubrir ningún test. Se ha usado el
> **patrón** `tests_js/*.test.js`, que es exactamente lo que el puente
> `tests/test_f007_js.py` lleva usando desde F-007 y lo que tiene escrito en su
> docstring. No es una desviación de fondo: es el mismo comando bien escrito.

Salida del arnés al cerrar el bloque:

```
62 passed in 8.57s
[OK] pytest en verde (con medición de cobertura)
[OK] servicio api (services/postventa-api): pytest en verde (caché: árbol sin cambios desde el último verde)
256 passed in 5.32s
[OK] servicio front (services/postventa-front): pytest en verde
[OK] PUERTA COBERTURA: 100.0% de 28 líneas cambiadas cubiertas (28/28, umbral 80%, nivel critico)
[OK] Rama actual: feature/F-031-nombrado-persistido
ENTORNO LISTO. Puedes trabajar.
```

## 6 bis · Desviaciones respecto a la spec, declaradas

### 6 bis.1 · Un fichero de test de más: `tests/test_f031_front.py`

`tasks.md` T10 solo pedía los dos comandos en verde, y `design.md` §2.1 no
lista ningún fichero de test para `app.js`. **Se ha añadido igualmente**, con
seis casos, y el motivo es concreto: sin él, **R19 se quedaba sin ningún
test**. R19 es un requisito de `requirements.md` §1.3, la ficha es de rigor
`critico` y R28 exige «para cada requisito de §1.1 y §1.3, al menos un test».

R19 es además el requisito más frágil de los cuatro: es **un orden entre dos
líneas**, mover una no rompe nada visible, y lo que deja detrás es el defecto
exacto que R19 describe —archivar un parte que el guardado acaba de dejar
fuera del circuito—.

Se prueba sobre el **texto fuente** porque `js/app.js` no lo ejecuta ningún
test (su propia cabecera lo dice), y con el fuente **sin comentarios**: F-031
ha dejado ahí comentarios que citan R18, R19 y R20, y nombrar una cosa no es
hacerla. Mismo planteamiento y mismo motivo que `test_f009_front.py`,
`test_f012_front.py`, `test_f025_front.py` y `test_f026_front.py`, que ya
existen y hacen lo mismo con el HTML y con `app.js`.

### 6 bis.2 · El comando de `tasks.md` con Node 24

Ver la nota de §5 bis. `node --test tests_js` (directorio) no arranca con la
versión instalada; se usa el patrón, que es lo que hace el puente de F-007.

### 6 bis.3 · R24 no necesitó ni una línea

`requirements.md` R24 —«el 409 del backend se pinta tal cual en el parte, por
el camino que ya pinta los demás errores del circuito, sin tumbar la tanda»—
**ya se cumple sin tocar nada**: `ejecutarCircuito` nunca lanza (F-025 R20),
devuelve hasta dónde llegó, y `_aplicarResultado` pinta el motivo del error en
el parte. Se declara aquí para que no parezca un requisito olvidado: no se ha
implementado porque no hacía falta, y `tests_js/circuito.test.js` ya lo cubre.
Lo mismo con **R23**, que es F-019 R27 y F-028 R33 conservados: el selector de
la tanda sigue siendo `pendientesDeCircuito` y no se ha tocado.

## 7 bis · Lo que queda fuera de este encargo (y sigue pendiente)

- **Bloque 4 (T11–T13)**: `tests/test_f031_alcance_cerrado.py` (R29), la
  documentación (`docs/ARCHITECTURE.md`, las notas en las specs de F-006 y
  F-030, y dejar escrito que `azure-apps/postventa_incidencias.md` no cambia) y
  la anotación de H-1. **Sin empezar.**
- **Bloque 5 (T14–T16)**: V1 y V2 manuales y la campaña de mutación de la
  feature completa. **Sin empezar.**

Con el Bloque 3 cerrado, **la condición de despliegue de §7 del informe del
Bloque 2 queda satisfecha**: las dos mitades están hechas. Lo que falta para
cerrar la feature es el alcance escrito (Bloque 4) y las puertas de rigor
(Bloque 5), no funcionalidad.

## 8 bis · Verificaciones `MANUAL (humano)` pendientes

Las dos siguen siendo del Bloque 5 y **no se han recorrido**. Lo que cambia con
este bloque es que **T14 / V1 ya es ejercitable entera**: hasta ahora su primera
mitad —«se espera **no ver** el 409, porque el vaciado lo evita»— no se podía
comprobar porque el vaciado no existía. Ahora sí.

- **T14 / V1** · `func start` en `services/postventa-api` y `python
  dev_server.py` en `services/postventa-front`: corregir el código de obra de
  un parte y pulsar «archivar y cerrar» **antes de 1,5 s**. Se espera **no ver
  el 409**. Y forzándolo desde la consola (`api.archivar` con un código
  distinto) se espera el 409 de R3 pintado en el parte. **No sube nada**:
  `ARCHIVO_HABILITADO` está apagado en local.
- **T15 / V2** · en el entorno desplegado y solo con un parte que el humano
  autorice. No procede hasta que la feature esté completa.

## 9 bis · Evidencias

Números **medidos**, no estimados. Salidas de esta misma sesión.

| Evidencia | Medida |
|---|---|
| **Tests ejecutados** y resultado | JavaScript: **310 passed, 0 failed** (`node --test "tests_js/*.test.js"`). Servicio `front`: **256 passed**. Servicio `api`: verde (caché, árbol sin cambios). Arnés: **62 passed** |
| **Tests nuevos** de este bloque | **18** — 12 en `tests_js/autoguardado_vaciado.test.js` (`f031 RN: …`) y 6 en `tests/test_f031_front.py` (`test_f031_rN_…`) |
| **Cobertura de las líneas cambiadas** | **100,0 %** — 28/28, umbral 80 %, nivel `critico`, línea `PUERTA COBERTURA` de `bash harness/init.sh`. **Ojo**: esas 28 líneas son las del Bloque 2; la puerta mide **solo Python** y **este bloque no ha cambiado ni una línea de Python de producción** (ver 9 bis.1) |
| **Tiempo de ejecución de la suite** | JavaScript: **~1,9 s** (`duration_ms` del propio runner). Servicio `front`: **5,32 s**. Arnés: 8,57 s |
| **Mutantes generados y supervivientes** | **No aplicable a este bloque** — ver 9 bis.1 |
| **Lint** | `python -m ruff check .`: **61 avisos, los mismos que antes del bloque** (deuda previa). `ruff check` sobre el fichero nuevo: `All checks passed!` |

### 9 bis.1 · Por qué no hay campaña de mutación en este bloque

**Medido**, no supuesto: `harness/alcance.py:134` filtra el alcance con
`if not normalizada.endswith(".py")`. El mutador **solo muerde Python**.

Lo que ha cambiado este bloque es:

- **dos ficheros JavaScript de producción** (`js/autoguardado.js`,
  `js/app.js`), que el mutador no ve;
- **un fichero JavaScript de tests** y **un fichero Python de tests**, que no
  son código de producción y nunca entran en una campaña.

O sea: **cero líneas de Python de producción**. Una campaña lanzada ahora
volvería a generar exactamente los 3 mutantes del Bloque 2, ya muertos los
tres. Por eso no se lanza aquí, y por eso la cobertura de líneas cambiadas que
imprime el arnés sigue siendo la del Bloque 2.

**No es una exención**: `tasks.md` **T16** —la campaña de la feature entera— es
del Bloque 5 y **sigue pendiente**. Y la mutación del JavaScript no está
disponible en este proyecto; se dice así, con el motivo, en vez de omitirlo.

Lo que sustituye a la mutación en el front es el planteamiento de los propios
tests, que es el que ya usa F-026: el temporizador entra **inyectado** y se
cuenta lo que se **cancela**, no solo lo que se guarda. Tres casos del fichero
nuevo son control negativo puro —cero guardados, cero temporizadores, cero
estados publicados—, que es lo que caza un vaciado que dispare de más.

## 10 bis · Commits del bloque

```
f89b00e F-031 T10: confirmarArchivo espera el vaciado antes de calcular la tanda
8ec692f F-031 T9: vaciarPendientes() fuerza lo escrito y espera, con tope de rondas
1b70b62 F-031 T8 (RED): los tests del vaciado del front, antes de tocar el modulo
```

Ningún `git push`, ningún PR, ningún commit fuera de la rama de la feature.
