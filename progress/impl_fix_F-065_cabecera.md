# Informe · fix F-065: tests de cabecera tras el cierre de F-038

Encargo pequeño fuera del backlog (no toca `harness/features.json` ni
`progress/current.md`). Rama `fix/F-065-test-cabecera-f038`, creada desde
`dev` `e9b9d23` en la copia `postventa-merge`.

## Qué cambió

Solo `services/postventa-api/tests/test_f065_documentacion.py` (7 líneas
añadidas, 3 quitadas; finales CRLF del fichero conservados):

- `test_f065_a7_la_cabecera_dice_que_f065_esta_desplegada`: exige
  «publicada el 2026-10-21, verificada en producción el 2026-11-09» en la
  cabecera de `docs/INTEGRACION.md` y que **no** vuelva «implementada en su
  rama; se publica con su T6». Docstring actualizado (F-038 ya publicada y
  cerrada, merge `a7400a1`).
- `test_f065_r30_la_copia_de_azure_apps_dice_lo_que_cambia`: exige
  «F-038 publicada el 2026-10-21, verificada en producción el 2026-11-09» en
  la cabecera de la copia de azure-apps y que **no** vuelva «F-038 mergeada y
  sin publicar todavía» (comentario con la referencia a `402b082`).

Los fragmentos elegidos no llevan backticks ni asteriscos y van en una sola
línea del documento, así que sobreviven a `_normal`.

No se tocó `docs/` ni `azure-apps` (solo lectura).

## Verificación (real)

Antes del cambio (`git stash`), desde `services/postventa-api`:

```
./.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider tests/test_f065_documentacion.py
FAILED tests/test_f065_documentacion.py::test_f065_a7_la_cabecera_dice_que_f065_esta_desplegada
FAILED tests/test_f065_documentacion.py::test_f065_r30_la_copia_de_azure_apps_dice_lo_que_cambia
2 failed, 63 passed in 3.22s
```

Después del cambio, mismo comando:

```
65 passed in 0.72s
```

## Fuera del alcance / pendiente

- `bash harness/init.sh` no se ha ejecutado (lo hace el líder).
- Sin push ni merge.
