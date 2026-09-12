<!-- progress/mutacion_F-026.md -->
# F-026 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-026 --base feature/F-025-confirmacion-unica --workers 8` el 2026-09-12 12:40.

## Alcance

Origen del diff: **rama** (`bb84d8601dc46708991f250cc70d59dbb7b3ff9f` .. `feature/F-026-aprobacion-humana`).

| Fichero | Líneas en alcance |
|---|---|
| `services/postventa-api/application/pipelines/contexto_parte.py` | 15 |
| `services/postventa-api/application/pipelines/paso_archivo.py` | 35 |
| `services/postventa-api/application/pipelines/paso_cierre.py` | 23 |
| `services/postventa-api/application/pipelines/paso_grafico.py` | 23 |
| `services/postventa-api/domain/models/aprobacion.py` | 285 |
| `services/postventa-api/domain/models/errores.py` | 31 |
| `services/postventa-api/domain/models/persistencia.py` | 6 |
| `services/postventa-api/domain/ports/persistencia.py` | 40 |
| `services/postventa-api/function_app.py` | 88 |
| `services/postventa-api/infrastructure/persistencia/mapeo.py` | 85 |
| `services/postventa-api/infrastructure/persistencia/repositorio_pg.py` | 81 |
| `services/postventa-api/infrastructure/persistencia/sentencias.py` | 164 |
| `services/postventa-api/interface_adapters/api/aprobacion_serializada.py` | 61 |
| `services/postventa-api/interface_adapters/api/aprobar.py` | 231 |
| `services/postventa-api/interface_adapters/api/cuerpos.py` | 117 |
| `services/postventa-api/interface_adapters/api/parte.py` | 30 |
| **Total** | **1315** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 35 |
| Mutantes evaluados | 35 |
| Muertos | 34 |
| Supervivientes | 1 |
| Timeouts | 0 |
| Timeouts repasados en serie | 0: ningún mutante agotó el reloj |
| Tiempo total | 401.5 s |
| Workers | 8 |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/postventa-api/infrastructure/persistencia/mapeo.py:182` [booleano]

- Original: `return json.dumps([codigo.value for codigo in codigos], ensure_ascii=False)`
- Mutado:   `return json.dumps([codigo.value for codigo in codigos], ensure_ascii=True)`

**ANÁLISIS (líder, 2026-09-12): EQUIVALENTE, y está medido.**

`ensure_ascii` solo cambia la salida cuando hay algún carácter fuera de ASCII
que escapar. Los cuatro valores que puede tomar `CodigoMotivo` son
`codigo_obra_no_legible`, `numero_incidencia_no_legible`, `firma_no_humana` y
`observaciones_manuscritas`: **los cuatro son ASCII puro**, comprobado
ejecutando el enum. Con ese universo de entradas las dos formas producen
**exactamente el mismo texto**, así que ningún test puede distinguirlas y
ninguno debería intentarlo.

Y si algún día se añadiera un código con acentos, tampoco rompería nada: las
dos salidas seguirían siendo JSON válido y `json.loads` devolvería la misma
cadena. La diferencia sería de legibilidad al mirar la columna a ojo, no de
comportamiento.

**No se añade test.** Un test que fijara `ensure_ascii=False` estaría fijando
una preferencia de formato, no una propiedad del sistema.

#### Análisis

**EQUIVALENTE (inobservable), justificado.** `json_de_codigos_de_motivo` recibe
`CodigoMotivo` y nada más, y los cuatro valores del `Enum`
—`codigo_obra_no_legible`, `numero_incidencia_no_legible`, `firma_no_humana`,
`observaciones_manuscritas`— son **ASCII puro**. `ensure_ascii` solo cambia la
salida cuando hay un carácter fuera de ASCII, así que sobre este dominio
cerrado las dos opciones producen exactamente la misma cadena: **ningún test
puede distinguirlas sin inventar un código de motivo que no existe**.

Se deja `ensure_ascii=False` a propósito y no se cambia: es lo que hacen
`json_de_motivos` y `json_de_avisos` del mismo módulo, donde sí importa
—ahí entran textos con tildes—, y tener dos criterios distintos en tres
funciones vecinas invita a copiar la equivocada.

Lo que mataría a este mutante es un `CodigoMotivo` con un carácter no ASCII. El
día que F-004 añada uno, este superviviente se convierte en un hueco real y hay
que volver aquí.

> _Análisis traído de la campaña anterior de esta feature: el mutante volvió a sobrevivir con el mismo operador y el mismo texto. Reléelo si el código de alrededor ha cambiado._

