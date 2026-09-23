<!-- progress/impl_despliegue_ventanas_abiertas.md -->
# Despliegue con las ventanas de escritura abiertas por defecto

> **Veredicto: hecho y en verde.** `desplegar_backend.ps1` publica
> `ARCHIVO_HABILITADO` y `CIERRE_HABILITADO` **abiertas** por defecto y las
> **dos cerradas** con `-VentanasCerradas`. `bash harness/init.sh` →
> **ENTORNO LISTO** (api: 3066 passed, 28 skipped). Rama
> `chore/despliegue-ventanas-abiertas`, fusionada en `dev` con `--no-ff`.
> **Ningún script ejecutado contra Azure**, ninguna escritura en ningún sistema,
> ni una línea de `services/*/` que no sea test, `features.json` sin tocar.
>
> **Dos cosas para el humano, abajo en §4:** `verificar_despliegue.ps1` ya no
> puede salir en verde tras un despliegue por defecto (pendiente de decisión),
> y hay docstrings de `function_app.py` que siguen diciendo «se despliega
> apagada» y no se han tocado porque el encargo prohíbe el código de `services/`.

Decisión del humano, 2026-09-23, literal: *«vamos a desplegar, pero quiero que
por defecto publique abierto, no cerrado»*; a la pregunta de qué ventanas,
*«Las dos»*.

## 1 · Qué cambió

| Fichero | Qué |
|---|---|
| `infra/desplegar_backend.ps1` | `[switch]$VentanasCerradas`. `$ventanaArchivo` y `$ventanaCierre` nacen en `"true"` y pasan a `"false"` solo dentro de `if ($VentanasCerradas)`. `$ajustes` lleva `"ARCHIVO_HABILITADO=$ventanaArchivo"` y `"CIERRE_HABILITADO=$ventanaCierre"`. Cabecera (decisión, fecha, riesgo aceptado, **que el defecto del código no cambia**), `.PARAMETER`, ejemplo, el resumen previo, la línea del RESULTADO (sale de las variables, no escrita a mano) y el paso 3 de la lista de después (ya decía «503» contra el host desnudo, cosa que no es cierta desde el 2026-08-25: ahora dice el 400 de Easy Auth) |
| `infra/90_push_dev_main.ps1` | `git log` → `git --no-pager log`. Una línea |
| `infra/22_ventana_archivo.ps1` | Cabecera «cada despliegue la vuelve a CERRAR» → «a ABRIR», con lo de antes conservado como historia; y el mensaje final `RECUERDA` |
| `infra/19_ventana_escritura.ps1` | Párrafo nuevo en la cabecera: el despliegue la deja abierta, el defecto del código no cambia, riesgo aceptado |
| `infra/14_paso0_sigrid.ps1` | Su cabecera decía «el interruptor del cierre, que nace apagado» (invoca `desplegar_backend.ps1 -SinPublicar`, así que **también abre las dos ventanas**). Una línea corregida |
| `services/postventa-api/tests/test_f010_scripts_infra.py` | Los tres sitios que fijaban `false` (R33, H2, T18 de F-012) reescritos. Helper `problemas_de_ventana` + test parametrizado por las dos variables + **control negativo** (cerrada por defecto, sin interruptor, valor escrito a mano: los tres tienen que dar problemas). H2 exige ahora que las dos vayan **dentro de `$ajustes`**. El resumen del RESULTADO no puede llevar `CERRADA`/`ABIERTA` literal |
| `services/postventa-api/tests/test_f010_tarjeta_portal.py` | R34: `Se cierra **siempre** al terminar` → `-VentanasCerradas` y «El siguiente despliegue la vuelve a abrir». Test nuevo: el runbook dice la fecha, `config/settings.py`, «Riesgo aceptado», «sin una puerta manual» y F-034 |
| `specs/F-010-despliegue/requirements.md` | **Recuadro fechado bajo R33** (patrón de R28): premisa literal sin borrar, más la de H2; qué la invalida; quién lo decidió; qué NO cambia (defecto del código, razón de H2, R34); riesgo aceptado; consecuencia sobre R27. Fila R33 de la trazabilidad con «Premisa enmendada el 2026-09-23» |
| `specs/F-006-sharepoint/requirements.md` (R20), `specs/F-009-cierre-sigrid/requirements.md` (R37), `specs/F-012-grafico-sigrid/requirements.md` (R39) | **Nota fechada, no enmienda**: esos tres fijan el defecto **del código**, que no cambia. Remiten al recuadro de R33 |
| `docs/DESPLIEGUE.md` | §2 (fila del script 2), §4 (recuadro de la decisión, abrir/cerrar con el script 22 o `az`, «El siguiente despliegue la vuelve a abrir»), §4 bis (mecanismo, script 19, subsección **«Riesgo aceptado con la ventana del ERP abierta por defecto»**, secuencia de un cierre, fila de la tabla), §5 (nota sobre `verificar_despliegue.ps1`), §5 bis (la consola del front) |
| `docs/INTEGRACION.md` | «La puerta que impide subir desde un puesto de trabajo»: el cierre 2 dice «apagado por defecto **en el código**» y un recuadro explica que ya no vale para el despliegue. §3 bis «Las puertas», punto 2, con el riesgo. Las dos filas de la tabla de variables |
| `docs/ARCHITECTURE.md` | La frase «que se despliega apagado» de la sección de `ANONYMOUS` |

**El defecto del código, comprobado leyendo**: `services/postventa-api/config/settings.py:228-230`
(`archivo_habilitado: bool = Field(default=False, validation_alias="ARCHIVO_HABILITADO", …)`) y
`:312-314` (`cierre_habilitado: bool = Field(default=False, validation_alias="CIERRE_HABILITADO", …)`).
Sin cambios; lo siguen fijando `test_f006_fabrica.py:133` y `test_f009_fabrica.py:96`.

## 2 · Verificación

- **Fase RED** (tests escritos antes de tocar el script):

  ```
  services/postventa-api> .venv/Scripts/python.exe -m pytest "tests/test_f010_scripts_infra.py::test_despliegue_ventanas_abiertas_por_defecto_y_cerradas_con_el_switch" -q -p no:cacheprovider --tb=line
        Left contains 4 more items, first extra item: 'falta [switch]$VentanasCerradas en param(...)'
  ...\tests\test_f010_scripts_infra.py:551: AssertionError: assert ['falta [swit... veces, no 2'] == []
  FAILED tests/test_f010_scripts_infra.py::test_despliegue_ventanas_abiertas_por_defecto_y_cerradas_con_el_switch[ARCHIVO_HABILITADO-ventanaArchivo]
  FAILED tests/test_f010_scripts_infra.py::test_despliegue_ventanas_abiertas_por_defecto_y_cerradas_con_el_switch[CIERRE_HABILITADO-ventanaCierre]
  2 failed in 0.11s
  ```

  Con el filtro `-k "ventana or h2 or r33 or t18"`: **8 failed, 13 passed**
  (los dos parametrizados, el control negativo, el de la cabecera, los dos de
  H2 y los dos de T18). Tras el cambio: `test_f010_scripts_infra.py`,
  `test_f012_scripts_infra.py` y `test_f010_prompt_keys_infra.py` → **244
  passed, 3 skipped**.
- El test del runbook (`test_despliegue_ventanas_el_runbook_dice_la_decision_y_el_riesgo`)
  se escribió **después** del texto: es documental, sin traza RED.
- **Parser de PowerShell 5.1** (`5.1.26100.9549`, `Parser::ParseFile`) sobre
  `desplegar_backend.ps1`, 19, 22, 14 y 90: **0 errores** en los cinco.
- **La lógica del interruptor, ejecutada en local** (el trozo del script
  aislado en un `scriptblock`, sin Azure):
  ```
  VentanasCerradas=False -> ARCHIVO_HABILITADO=true CIERRE_HABILITADO=true (ABIERTA/ABIERTA)
  VentanasCerradas=True -> ARCHIVO_HABILITADO=false CIERRE_HABILITADO=false (CERRADA/CERRADA)
  ```
- `bash harness/init.sh` → **ENTORNO LISTO**; api **3066 passed, 28 skipped
  en 171,67 s**; raíz 62 passed; front, caché en verde.
- **Un tropiezo, corregido**: al reescribir 19, 22, 14 y dos docs con Python
  su copia de trabajo quedó en LF y `test_f012_utillaje_cada_script_va_en_crlf[19_ventana_escritura.ps1]`
  falló. El commit `55d6347` no lleva el fallo (el índice está en LF por
  `core.autocrlf=true`, igual que antes); se devolvió la copia de trabajo a
  CRLF y el test pasa.

## 3 · Evidencias

| Evidencia | Valor |
|---|---|
| Tests ejecutados | api 3066 passed, 28 skipped; raíz 62 passed |
| Cobertura de líneas cambiadas | **N/A**: no se cambia Python de producción (`PUERTA COBERTURA: N/A`); lo cambiado es PowerShell y Markdown, que `harness/alcance.py` no mide |
| Mutación | **N/A**: tarea `chore` sin feature ni nivel de rigor; no hay Python de producción que mutar |
| Tiempo de la suite | 171,67 s (api) |

## 4 · Lo que queda fuera, y lo que el humano tiene que saber

1. **`verificar_despliegue.ps1` no sale en verde tras un despliegue por
   defecto.** Su comprobación 2 solo llama a `/api/archivar` si la ventana de
   archivo está **cerrada** (con ella abierta subiría un PDF), y su veredicto
   exige `$ventana -eq "false"`. **No se ha tocado**: la guarda es correcta y
   aflojarla es una decisión de seguridad, no un ajuste de texto. Además, desde
   el 2026-08-25 esa comprobación tampoco se podía hacer por el host desnudo
   (§5 bis). Anotado en el recuadro de R33 y en `DESPLIEGUE.md` §5 como
   **pendiente de decisión**.
2. **Docstrings de `services/postventa-api/function_app.py` desfasados**, no
   tocados porque el encargo prohíbe el código de `services/` salvo tests:
   `:59` («el entorno se despliega con la **ventana de escritura
   cerrada**»), `:97` («`CIERRE_HABILITADO` se despliega **apagada**»),
   `:161` y `:169-170` (las dos «se despliega apagad…») y `:167`
   («cuando el archivado está cerrado, que es como se despliega»).
   `test_f010_endpoints_protegidos.py:229` fija la frase «ventana de escritura
   cerrada», así que tocarlos exige tocar también ese test. **Sin decidir.**
   También `test_f010_integracion_expuesto.py:13-15` dice en su docstring que
   la ventana del cierre «se despliega APAGADA» (texto de 2026-08, no aserción).
3. **`14_paso0_sigrid.ps1` abre también las dos ventanas**: llama a
   `desplegar_backend.ps1 -SinPublicar` sin `-VentanasCerradas`. Coherente con
   la decisión («por defecto, abierto»); corregida su cabecera, nada más.
4. **`azure-apps/postventa_incidencias.md` SÍ habla de las ventanas, y queda
   desfasado** (no se ha tocado ese repositorio, como pedía el encargo):
   `:86` («las ventanas de escritura se despliegan **apagadas**»),
   `:400-401` («`CIERRE_HABILITADO` se despliega apagado y cada despliegue lo
   devuelve a `false`»), `:783-785` («se despliegan **apagadas**, se abren para
   la prueba y se…»), y las filas de la tabla de variables `:521` y `:535`
   (correctas para el código, sin decir lo del despliegue). Por la regla de
   mantenimiento de `azure-apps/`, su actualización toca **en el mismo trabajo**:
   la decide el líder.
5. `INTEGRACION.md` §8, fila «Que Posventa lo use de verdad» («Posventa todavía
   no ha cerrado ninguna incidencia con esto»): el encargo dice que ya lo usa en
   real. No se ha tocado —no habla de las ventanas—, pero probablemente está
   desfasada.
6. **El riesgo aceptado** queda escrito en la cabecera del script, en el
   recuadro de R33, en `DESPLIEGUE.md` §4 bis y en `INTEGRACION.md` §3 bis:
   con la ventana del ERP abierta por defecto, cualquier versión desplegada
   escribe en Sigrid de producción sin puerta manual, y mientras F-034 no esté
   desplegada `/api/adjuntar` y `/api/cerrar` toman el número de incidencia del
   cuerpo.

## 5 · Commits

- `cb4eb74` 90_push_dev_main usa `git --no-pager log`.
- `52da909` desplegar_backend publica las dos ventanas abiertas; `-VentanasCerradas` las cierra (script + tests).
- `a45855f` enmienda bajo R33 de F-010 y notas en F-006 R20, F-009 R37, F-012 R39.
- `55d6347` documentación y cabeceras de 22, 19 y 14.
- (este informe y `current.md`) + merge `--no-ff` en `dev`.
