<!-- progress/review_fix_ajustes_sin_secretos_en_repr.md -->
# Revisión · Arreglo `Ajustes` sin secretos en su `repr` (reviewer, 2026-11-19)

Revisión completa (pasada 1), diff `ed9318e...HEAD` (HEAD 8d68ddf), worktree
`postventa-fix-secretos`, rama `fix/ajustes-sin-secretos-en-repr`.

## Veredicto: RECHAZADO

Motivo único: **`bash harness/init.sh` en rojo**, y no se aprueba sobre un
portero en rojo. El rojo **no viene del arreglo**: el código está bien, y
cumple la propuesta, las convenciones y los puntos pedidos (ver abajo). En
cuanto el portero salga verde, el arreglo se puede aprobar sin más cambios.

## 1. `bash harness/init.sh` (raíz del worktree, tal cual): ROJO

- Suite raíz: 2202 passed, 48 skipped. Servicio `api`: verde (servido de caché
  del verde de 2026-11-19 01:05, mismo árbol, más 38 rutas `ejecutar_siempre`
  en verde). PUERTAS COBERTURA, CARRIL, TAMAÑO y CAPA E2E: N/A porque la rama no
  es de una feature declarada (lo imprime el portero).
- **KO: `servicio front (services/postventa-front): pytest en rojo`**. Falla
  `tests/test_f007_dev_front_ps1.py::test_f007_r36_el_script_existe_y_va_en_utf8_con_bom_y_crlf`:
  `dev_front.ps1 tiene que ir con finales de línea CRLF` (76 `\n`, 0 `\r\n`).
- **Causa**: es un efecto de volver a sacar `services/postventa-front` entero en
  LF. `git ls-files --eol` da `i/lf w/lf` para `dev_front.ps1` en el worktree,
  frente a `i/lf w/crlf` en la carpeta principal: ese script se guarda en LF y
  **necesita** el CRLF que pone `core.autocrlf=true` al sacarlo. Al arreglar los
  16 tests JS de F-038 (que quieren LF) se rompió este (que quiere CRLF).
- Comprobación aparte, sin tocar el árbol: la suite del front con ese único test
  deseleccionado da **910 passed, 7 skipped, 1 deselected**. Los 16 tests JS
  de F-038 ya pasan. No hay ningún otro rojo.

## 2. Revisión del diff contra la propuesta

Ficheros: `services/postventa-api/config/settings.py` (+8: `repr=False` y un
comentario de una línea en los cuatro `Field`),
`services/postventa-api/tests/test_fix_ajustes_sin_secretos_en_repr.py`
(nuevo), `progress/current.md` y el informe del implementer. Nada más: ni
`SecretStr` ni otros campos tocados. **Se ajusta a la propuesta.**

- [x] **El test falla de verdad sin el arreglo.** Lo he reproducido yo: copia
  del `settings.py` de `ed9318e` en el scratchpad y el test nuevo sin cambios
  → `4 failed, 5 passed`, un fallo por secreto (`gemini_api_key`,
  `graph_client_secret`, `pg_password`, `sigrid_api_key aparece en
  repr(Ajustes)`). Con el arreglo: `9 passed`. Va parametrizado por campo, así
  que quitar `repr=False` de uno solo de los cuatro lo pone en rojo.
- [x] **Valores de prueba falsos evidentes**: `FALSO-gemini-clave-0001`,
  `FALSO-pg-contrasena-0002`, `FALSO-graph-secreto-0003`,
  `FALSO-sigrid-clave-0004`, distintos entre sí. El fixture aísla del `.env`
  y del entorno (`delenv` de las cuatro variables, `chdir` a `tmp_path`,
  `_env_file=None`).
- [x] **Ningún secreto real entra en el repo**: el diff solo trae los valores
  `FALSO-*`. El escaneo de patrones de clave sobre el diff no da nada, `.env`
  no aparece en él, y el informe del implementer no trae valores (filtra
  hasta los falsos).
- [x] **Ningún adaptador se rompe.** `repr=False` solo cambia `__repr__`/`__str__`:
  ni la validación, ni `model_dump`, ni el acceso por atributo. Los usos en
  `infrastructure/{llm,persistencia,sharepoint,sigrid}/fabrica.py` leen el
  atributo (`ajustes.gemini_api_key`, `ajustes.pg_password`,
  `str(ajustes.graph_client_secret)`, `str(ajustes.sigrid_api_key)`), y ningún
  código depende del `repr` de `Ajustes`. Lo cubre el test
  `test_fix_el_secreto_sigue_legible_como_atributo`, y `test_f003_fabrica.py`
  y `test_f013_fabricas.py` pasan junto al nuevo (54 passed). La suite del API
  sale verde en `init.sh`.
- [x] **Convenciones**: primera línea con la ruta, todo en español, sin prints
  de debug, sin secretos. RED (36a6b3f) y GREEN (ad3c963) en commits separados,
  y la salida real del RED está en el informe.
- N/A cobertura, mutación, capa e2e y trazabilidad de requisitos: es un arreglo
  sin spec ni entrada en `features.json` (el portero las declara N/A por ese
  motivo).

## Cambios requeridos

1. **Entorno, no código**: volver a sacar en el worktree
   `services/postventa-front/dev_front.ps1` con CRLF (con `core.autocrlf=true`
   basta con borrarlo y hacer `git checkout -- services/postventa-front/dev_front.ps1`),
   **dejando en LF el resto del front**, y relanzar `bash harness/init.sh`. Si
   sale verde, el arreglo queda aprobable tal cual. No lo he hecho yo: el
   reviewer no toca el árbol.

## Observaciones (no bloquean)

- El conflicto LF/CRLF va a volver en cada worktree o clon nuevo con
  `core.autocrlf=true`. El arreglo duradero, como cambio aparte, es fijarlo en
  `.gitattributes`: `services/postventa-front/** text eol=lf` y, después,
  `services/postventa-front/dev_front.ps1 text eol=crlf`. El implementer ya lo
  propone. Como vale para cualquier repositorio con `.ps1` y controles de texto
  multilínea, hay que valorar si va a `arnes-base`.
- Tal como dice el implementer, `graph_tenant_id` y `graph_client_id` siguen en
  el `repr`. No son credenciales y quedan fuera de la propuesta aprobada. Es
  decisión del humano.
- El portero sirvió de caché la suite del API (mismo árbol que el verde del
  implementer, que dio 10374 passed). Se pidió `init.sh` sin `ARNES_SIN_CACHE`
  y así se ha ejecutado.
