# Arreglo · `Ajustes` sin secretos en su `repr` (implementer, 2026-11-18/19)

Arreglo sin spec, aprobado por el humano el 2026-11-18. Rama
`fix/ajustes-sin-secretos-en-repr` (desde `dev` ed9318e), worktree
`postventa-fix-secretos`.

## Qué y por qué
`services/postventa-api/config/settings.py` declaraba cuatro secretos como
`str | None` corrientes, así que el `repr` de `Ajustes` (y su `str`) los
imprimía en claro. Un traceback de pytest llegó a enseñar parte de la clave de
Gemini. Arreglo mínimo acordado: `repr=False` en el `Field` de
`gemini_api_key`, `pg_password`, `graph_client_secret` y `sigrid_api_key`.
No se ha migrado a `SecretStr` (se descartó en la propuesta): los campos siguen
siendo `str` y los adaptadores los leen igual que antes.

## Ficheros
- `services/postventa-api/config/settings.py`: `repr=False` (más un comentario
  de una línea) en los cuatro `Field`. +8 líneas, ninguna borrada.
- `services/postventa-api/tests/test_fix_ajustes_sin_secretos_en_repr.py`
  (nuevo): construye `Ajustes(entorno="test", _env_file=None, ...)` con cuatro
  valores FALSOS evidentes, tras `delenv` de las cuatro variables y `chdir` a
  `tmp_path` (el mismo aislamiento que `test_f005_*` y `test_f003_fabrica.py`).
  Comprueba: (a) ni `repr` ni `str` contienen ninguno de los valores; (b) cada
  campo sigue devolviendo su valor tal cual; (c) el `repr` sigue mostrando
  campos que no son secretos (`entorno='test'`).

## Fase RED -> GREEN
Comando, desde `services/postventa-api`:
`.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider tests/test_fix_ajustes_sin_secretos_en_repr.py`

RED, antes del arreglo (commit 36a6b3f). Los valores falsos van sustituidos por `<falso>`
al filtrar la salida, aunque no sean secretos:
```
E       AssertionError: gemini_api_key aparece en repr(Ajustes)
E       AssertionError: graph_client_secret aparece en repr(Ajustes)
E       AssertionError: pg_password aparece en repr(Ajustes)
E       AssertionError: sigrid_api_key aparece en repr(Ajustes)
4 failed, 5 passed in 1.29s
```
GREEN, después del arreglo (commit ad3c963): `9 passed in 1.09s`.

## Suite del servicio
`.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider` desde
`services/postventa-api`: **10374 passed, 485 skipped in 1608.22s**.

## `bash harness/init.sh` (raíz del worktree): EN ROJO, no por este cambio
- La suite de `postventa-api` dentro de `init.sh` sale verde: 2202 passed, 48 skipped
  (primer bloque) y 10374 passed, 485 skipped.
- `PUERTA COBERTURA`, `PUERTA CARRIL`, `CAPA E2E`: N/A (la rama no es una
  feature declarada). `PUERTA TAMAÑO`: aviso N/A.
- **KO: `servicio front (services/postventa-front): pytest en rojo`**, porque
  falla `tests/test_f007_js.py::test_f007_r32_la_suite_de_javascript_esta_en_verde`:
  16 tests de `node --test`, todos controles de mutación de F-038
  (`revision.test.js`, mutantes PR8, AC14, Q4, GS6, N10, E7, BN12, RX14-RX24).
  Mensaje tipo: `el control no encuentra una sola vez: !v.proveedor_ambiguo && ... 1 !== 2`.
- **Diagnóstico** (no he tocado el front): el diff de la rama contra ed9318e
  solo contiene los dos ficheros de arriba. El worktree se sacó con
  `core.autocrlf=true`, así que todo `services/postventa-front` está en **CRLF**,
  mientras que en la carpeta principal está en LF (comprobado con `file`, solo
  leyendo). Los controles de F-038 buscan fragmentos de varias líneas con `\n`
  y no los encuentran con CRLF. Es el mismo problema que `.gitattributes` ya
  resuelve para los SVG (F-035 R52), pero aquí afecta a los `.html`/`.js`
  del front. Es un fallo del entorno de un worktree nuevo, no de este arreglo.
- No he aplicado ningún apaño (reescribir el worktree en LF, tocar
  `.gitattributes`): la regla es no improvisar. Propuesta para el líder y el
  humano: (1) volver a sacar el front del worktree en LF
  (`git -c core.autocrlf=false checkout -- services/postventa-front` con el árbol limpio)
  y relanzar `init.sh`; o (2) como arreglo duradero, aparte, añadir a
  `.gitattributes` `services/postventa-front/** text eol=lf` (o que los
  controles de F-038 normalicen `\r\n`). La (2) es un cambio del arnés del
  proyecto y hay que decidir si va a `arnes-base`.

## Otros campos que podrían ser sensibles (sin cambiar, como se pidió)
Ninguno es una contraseña, una clave o una cadena de conexión con credenciales.
Para valorar:
- `graph_tenant_id` y `graph_client_id`: según el `CLAUDE.md` transversal, un
  ID de tenant no se versiona; no es una credencial, pero sale en el `repr`.
- `sigrid_api_base_url`: URL de la pasarela. Solo lleva credenciales si
  alguien metiera la clave en la query; el campo dice que la clave nunca va
  en la URL.
- `pg_host`, `pg_usuario`, `sharepoint_site_id`, `sharepoint_drive_id`:
  identificadores de infraestructura, no secretos.

## Pendiente
- Que `init.sh` salga verde en este worktree (ver propuesta arriba). Si no, el
  merge a `dev` y el `init.sh` de `dev` lo confirmarán desde una copia en LF.
- Nada de push: la rama queda con dos commits locales (36a6b3f RED,
  ad3c963 GREEN) más el de este informe.
