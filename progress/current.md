<!-- progress/current.md -->
# Sesión activa

**F-003 · Extracción multimodal del parte, manuscritos incluidos** — estado
`in_progress`, rama `feature/F-003-extraccion`, rigor `critico`.

**Implementación TERMINADA y revisión APROBADA** (2026-08-18):
`progress/impl_F-003.md` y `progress/review_F-003.md`. 207 tests del servicio
(112 de F-003), cobertura de lo cambiado 100 % (631/631), mutación 127
generados y 127 muertos con **cero supervivientes**, portero en verde.

El reviewer verificó por su cuenta y estrenó la exigencia del arnés 1.5.2:
**reejecutó la campaña de mutación entera** (101,0 s, mismos cuatro totales,
salida fuera de `progress/`, árbol limpio después). Los muertos están
comprobados, no solo contados.

**Pendiente para cerrar: solo las dos verificaciones MANUAL del humano** (T17
y T18, abajo). La feature **no se marca `done`** hasta que se ejecuten y se
anote aquí su resultado real. Nada depende ya del implementer.

## Cadena de ramas (importante para el merge, que es del humano)

`dev` → `feature/F-002-ingesta-troceado` (F-002 cerrada) →
`chore/postreview-F-002` (tres decisiones de la review + arnés 1.5.2) →
`feature/F-003-extraccion` (esta).

Cada una sale de la anterior porque depende de su código. Se mergean **en ese
orden**, o se mergea directamente la última cuando todo esté cerrado.

## Lo que decidió el humano sobre F-003

- **`numero_pagina`** entra en el contrato: F-003 lo lee y lo devuelve; **no
  reagrupa nada** (eso es F-014, y hay un test que lo vigila).
- El endpoint **`POST /api/extraer`** entra en F-003.
- Los campos se llaman **`unidad`** y **`fecha_servicio`**. El papel imprime
  «Vivienda», el backlog decía «chalet». `docs/ARCHITECTURE.md` quedó alineado
  en T19 (commit `81a1a90`), comprobado por el reviewer.
- El modelo por defecto es **`gemini-3.7-flash`**. `azure-apps` documenta el
  proveedor pero **no fija versión**, así que ninguna afirmación de la spec
  puede decir qué versión corre en otro proyecto.
- La ruta sensible de `config/prompts.yaml` no se declara aún: hace falta antes
  el evaluador, que es **F-015**.

## Lo que hay que vigilar en esta feature

1. **La verificación contra un parte real se ejecuta pronto**, en cuanto el
   adaptador y el endpoint estén hechos: es el momento de la verdad del
   proyecto. Si el modelo no lee estos manuscritos, no falla F-003 —su
   contrato se cumpliría igual—, falla la premisa. Si sale mal, ahorra la
   campaña de mutación entera.
2. **Confirmar el identificador exacto del modelo contra la API** antes de la
   primera llamada real: un ID mal escrito no falla en los tests (el modelo
   está simulado) sino en ejecución.
3. **Datos personales**: prohibido volcar el contenido del parte, la respuesta
   cruda o los valores extraídos en logs o mensajes de error. El parte lleva
   DNI.
4. **La guardia de red del `conftest`** es la tarea delicada: si choca con
   pytest o con la cobertura, la spec deja una variante B ya aprobada. Una
   tercera vía es `blocked`, no improvisación.

## Verificaciones MANUAL (humano) de F-003 — PENDIENTES, con su comando

Las dos tareas **T17** y **T18** de `specs/F-003-extraccion/tasks.md` están
**preparadas y sin ejecutar**: piden credencial de IA y el parte real, y
ninguna de las dos cosas puede tocar un agente. El resto de la feature está
implementada y en verde sin ellas.

**Antes de nada**: no hay `.env` en `services/postventa-api/`. Hay que crearlo
copiando `.env.example` y poniendo la clave real en `GEMINI_API_KEY`. Ese
fichero **no se versiona** y ningún agente lo toca.

### 0 · Confirmar el identificador del modelo (primer paso de T17)

Va **antes** de gastar una sola llamada de extracción. Un ID mal escrito **no
lo caza ningún test** —ahí el modelo está simulado— y revienta en ejecución
con un 404 del proveedor, fácil de confundir con un problema de credencial.

```bash
cd services/postventa-api && .venv/Scripts/python.exe -c "
from config.settings import obtener_ajustes
from google import genai
ajustes = obtener_ajustes()
cliente = genai.Client(api_key=ajustes.gemini_api_key)
nombres = [m.name for m in cliente.models.list()]
print('GEMINI_MODEL =', ajustes.gemini_model)
print('reconocido:', any(ajustes.gemini_model in n for n in nombres))
"
```

Si sale `reconocido: False` **es una parada**: se decide el identificador
correcto y se pone en `GEMINI_MODEL`. No se sustituye por otro modelo por
iniciativa de nadie que no sea el humano.

### 1 · T17 · Humo con un parte **sintético** (sin ningún dato personal)

```bash
cd services/postventa-api && .venv/Scripts/python.exe -c "
from tests.utiles_pdf import remesa_sintetica
from interface_adapters.api.extraer import extraer_parte
pdf = remesa_sintetica([1])
res = extraer_parte(pdf, hash_parte='humo')
print('traza:', res['traza'])
for nombre, campo in res['campos'].items():
    print(f'{nombre}: valor={campo[\"valor\"]!r} confianza={campo[\"confianza_pct\"]}')
print('avisos:', res['avisos'])
"
```

**Esperado**: las nueve claves, `proveedor=gemini`, el modelo configurado,
`codigo_obra = 0677`, `numero_incidencia = RS26.08/0123` y
`numero_pagina = "1"`. Aquí **sí** se pueden imprimir los valores: son
inventados por el generador.

### 2 · T18 · Acierto sobre un parte **real** de Mirasierra

Es **el momento de la verdad del proyecto**: lo que se comprueba no es el
contrato de F-003 —eso ya lo demuestra la suite— sino si el modelo **lee de
verdad estos manuscritos y estos escaneos**. El PDF
`docs/referencia/doc02871320260817093833.pdf` está en el árbol y **no se
versiona**.

```bash
cd services/postventa-api && .venv/Scripts/python.exe -c "
from pathlib import Path
from domain.models.remesa import DocumentoEntrada
from interface_adapters.api.split import trocear_remesa
from interface_adapters.api.extraer import extraer_parte
import base64
ruta = Path('../../docs/referencia/doc02871320260817093833.pdf')
partes = trocear_remesa([DocumentoEntrada(nombre=ruta.name, contenido=ruta.read_bytes())])['partes']
p = partes[0]
res = extraer_parte(base64.b64decode(p['contenido_b64']), hash_parte=p['hash'])
print('traza:', res['traza'])
for nombre, campo in res['campos'].items():
    visible = campo['valor'] if nombre == 'numero_pagina' else (campo['valor'] is not None)
    print(f'{nombre}: {visible} confianza={campo[\"confianza_pct\"]}')
print('avisos:', res['avisos'])
"
```

**Esperado**: las nueve claves; `codigo_obra` y `numero_incidencia` en `True`
con confianza alta; `numero_pagina` con valor `"1"` —único cuyo valor se
imprime: un número de página no es dato personal—; y los campos que el papel
deja en blanco en `False` con confianza 0, que es **lo normal** en esta
remesa, no un fallo.

Se anotan aquí **los booleanos y las confianzas, nunca los valores**: el parte
lleva DNI.

**Si el resultado es malo, se para y se habla antes de tocar nada más.** Un
acierto pobre no se arregla con más tests ni con más mutación: se arregla
tocando el prompt (`config/prompts.yaml`) o cambiando de modelo.

## Pendiente del humano
- **Aprobar tres dependencias nuevas**: `google-genai>=0.3`, `pyyaml>=6.0`,
  `tenacity>=8.2,<10.0`.
- **Merge de la cadena de ramas** a `dev`.
- **Decisión suelta**: si la regla de `docs/CONVENTIONS.md` sobre ReportLab
  frente a PyMuPDF debe subir a `arnes-base` en su propia versión. Es el único
  fichero donde este repositorio adelanta al arnés genérico.

## Contexto del proyecto

- Arnés **1.5.2**, verificado contra el payload fichero a fichero: no hay
  código viejo. La campaña de mutación conserva ahora el análisis de
  supervivientes al repetirse, y el reviewer la reejecuta cuando es barata.
- Agentes del arnés cargados: se delega, el líder no implementa.
- **Lección vigente**: dos agentes a la vez en la misma rama se pisan en el
  índice de git. Si se paraleliza, el segundo no toca git y commitea el líder.
- Hallazgos de dominio que mandan sobre el diseño, en `docs/ARCHITECTURE.md` y
  `docs/referencia/`: «Cerrar parte» de Sigrid **exige documento adjunto**, y
  un parte firmado con observaciones manuscritas **no** es un parte conforme.

## Propuestas de automejora del arnés que dejó la review de F-003

Ninguna aplicada; las tres necesitan decisión del humano y **dos son
genéricas**, así que irían a `arnes-base` por la regla de propagación.

- **P1 · La campaña de mutación debería usar la base real de la rama.**
  `harness/alcance.py` resuelve el origen del diff con una ref que en cadenas
  de ramas no es la base de la feature: en F-003 el alcance arrastró 27
  ficheros y 1912 líneas (incluido `harness/mutacion.py`, que aportó 32 de los
  127 mutantes) mientras la cobertura, que usa `--base dev` explícito, medía
  631 líneas. No es un defecto —el alcance es más ancho, nunca más estrecho, y
  los 127 murieron— pero los números no son comparables entre features.
  Propuesta: campo `base` en `harness/features.json`, con `dev` por defecto,
  usado por `harness.cobertura` y `harness.mutacion`.
- **P2 · `CHECKPOINTS.md` C5 no contempla las tareas `MANUAL (humano)`.** Hoy
  exige todas las tareas `[x]`, y una feature `critico` está obligada a tener
  verificaciones que ningún agente puede ejecutar. El reviewer tuvo que
  improvisar. Propuesta: una tarea `MANUAL` pendiente no vacía el checkpoint
  pero impide el paso a `done`, y el reviewer la lista con su comando.
- **P3 · C4 bis debería nombrar la comprobación de «no medido»** en la
  cobertura: un 100 % sobre ficheros que no aparecen en el informe de
  `coverage` sería falso. El mecanismo existe en `harness/cobertura.py`; lo que
  falta es que el checkpoint obligue al reviewer a verificarlo.
