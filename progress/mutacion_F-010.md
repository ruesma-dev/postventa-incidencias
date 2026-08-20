<!-- progress/mutacion_F-010.md -->
# F-010 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-010` el 2026-08-20 15:17.

## Alcance

Origen del diff: **rama** (`0705d881d4a1c329006db5fe970c45bcb93c2e75` .. `feature/F-010-despliegue`).

| Fichero | Líneas en alcance |
|---|---|
| `services/postventa-api/function_app.py` | 55 |
| `services/postventa-front/dev_server.py` | 188 |
| **Total** | **243** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 20 |
| Mutantes evaluados | 20 |
| Muertos | 20 |
| Supervivientes | 0 |
| Timeouts | 0 |
| Tiempo total | 17.6 s |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.

## Nota de alcance de esta campaña (F-010)

Los dos ficheros del alcance entran por el punto de partida del diff de rama,
no porque F-010 los haya reescrito:

- **`function_app.py`**: F-010 solo le ha tocado **la cabecera del módulo**
  (R32). El `auth_level` no cambia, y no hay ni una línea de comportamiento
  nueva: por eso no ha generado ningún mutante.
- **`dev_server.py`**: F-010 **no lo toca**. Aparece porque el punto de
  partida del diff de rama es anterior a que se cerrara F-007.

Lo que F-010 entrega de verdad —cinco scripts de PowerShell, un cambio en JS y
documentación— **queda fuera de lo que la campaña sabe mutar**: la herramienta
solo muta `.py`. La disciplina de esa parte la sostienen los tests de contrato
de la fase 1 (`test_f010_scripts_infra.py`), `test_f010_tarjeta_portal.py`,
`test_f010_endpoints_protegidos.py`, `test_config_timeout.test.js` y la fase
RED de T5, cuya traza está en `progress/impl_F-010.md`.

## Las dos campañas de esta feature, y por qué los números no coinciden

Esta feature ha lanzado la campaña **dos veces**, y conviene dejar escrito lo
que salió en cada una en vez de enseñar solo la última:

| Cuándo | Resultado |
|---|---|
| Antes de T5 y T9 (con la feature parada en D2) | 20 mutantes, 17 muertos, **3 supervivientes** |
| Con la feature terminada (esta) | 20 mutantes, **20 muertos, 0 supervivientes** |

Los tres supervivientes de la primera eran **el mismo caso**: el ancho del
separador decorativo del banner de arranque de `dev_server.py`
(`log.info("=" * 60)` → `"=" * 61`). En la campaña final los tres mueren.

**No se ha añadido ningún test para matarlos**, así que la diferencia no la
explica un cambio nuestro sobre esas líneas: entre una campaña y otra solo
entraron `desplegar_backend.ps1`, sus tests, `config.js` y su test de JS, y
ninguno toca `dev_server.py`. El resultado de 0 supervivientes se ha
**reproducido dos veces**, en modo paralelo y con `--workers 1`, que es
determinista. Se deja constancia de la discrepancia en vez de justificarla con
una causa que no se ha comprobado.

En cualquiera de las dos lecturas la conclusión práctica es la misma: esas
tres mutaciones no alteran ningún comportamiento observable —solo la anchura
de una línea decorativa en el log de arranque del servidor de desarrollo
local, que además ni siquiera se despliega, porque `desplegar_front.ps1` lo
excluye de la copia que sube.
