# Arreglo · tests de configuración ausente aislados de `os.environ`

Sin spec (opción (a), aprobada por el humano el 2026-11-15). Rama
`fix/tests-configuracion-sin-entorno`, sacada de `dev` 6994cb0. Solo se tocan tests:
ni código de producción ni arnés.

## Hecho

Los tests que comprueban que una fábrica **nombra la configuración que falta** se
aislaban del `.env` (`_env_file=None`), pero no de `os.environ`. Si el proceso traía
esas variables (alguien las exporta en su terminal, o `volcar_variables` del arnés 1.10
vuelca el `.env` a los workers de la mutación paralela), lo que tenía que faltar estaba
y el test se ponía rojo.

## Ficheros

- `services/postventa-api/tests/conftest.py`: el fixture autouse `entorno_de_test`
  quita, antes de cada test, toda variable que lee `Ajustes` (`monkeypatch.delenv(...,
  raising=False)`, las dos grafías, mayúsculas y minúsculas) y después fija `ENTORNO=test`
  como antes. Los nombres salen del propio modelo (`variables_de_configuracion()`: el
  alias de cada campo, o el nombre en mayúsculas si no tiene alias), así que un campo
  nuevo queda cubierto sin tocar ninguna lista. El test que necesite una variable la pone
  él con `monkeypatch.setenv`, que corre después.
- `services/postventa-api/tests/test_f059_volcado_http.py`: los dos `parametrize` de
  `test_f059_r10_r30_…` y `test_f059_r16_r37_r42_…` construían `Ajustes` **al recoger los
  tests**, antes de cualquier fixture, y el fixture no llegaba a aislarlos. Ahora cada
  parámetro es una `lambda` que el test llama al empezar (`ajustes =
  construir_ajustes()`). Mismos casos, mismos ids y mismas aserciones.

No se ha debilitado ni quitado ninguna aserción. EOL CRLF de los dos ficheros
conservado. No se tocó ningún otro fichero.

## Reproducción ANTES

Variables exportadas con valores **ficticios** (script en el scratchpad de la sesión:
`GEMINI_API_KEY`, `PG_HOST`, `PG_USER`, `PG_PASSWORD`, `SHAREPOINT_SITE_ID`,
`SHAREPOINT_DRIVE_ID`, `SHAREPOINT_CARPETA_BASE`, `GRAPH_TENANT_ID`, `GRAPH_CLIENT_ID`,
`GRAPH_CLIENT_SECRET`, `SIGRID_API_BASE_URL`, `SIGRID_API_KEY`, `SIGRID_BASE_DATOS`,
`VOLCADO_PARTES_POR_LLAMADA`). No se ha leído ni abierto el `.env`.

`.venv/Scripts/python.exe -m pytest -q` sobre los 8 ficheros del encargo:

```
13 failed, 624 passed in 5.49s
```

Los 13 son exactamente los del encargo. Traza corta de dos de ellos:

```
tests/test_f056_ubicaciones.py:503: AssertionError: assert 'SIGRID_API_BASE_URL' in 'faltan variables
  para hablar con sigrid-api: SIGRID_BASE_DATOS. Se dicen los nombres y nunca los valores: ...'
tests/test_f059_fabrica.py:171: Failed: DID NOT RAISE ConfiguracionSigridIncompleta
```

Con solo el fixture arreglado seguían rojos 2 (los `[sin-configuracion]` de
`test_f059_volcado_http.py`), por el `parametrize` que construye en la recogida. Arreglados
con las `lambda`.

## Barrido (otros tests con el mismo patrón)

Suite unitaria entera de `api` con las variables ficticias exportadas y **sin** el arreglo:
24 fallos, los 13 del encargo más **11 nuevos**, que dependían de `SHAREPOINT_CARPETA_BASE`
en el entorno (comprobado exportando solo esa: siguen saliendo los 11):

- `tests/test_f006_archivar_http.py::test_f006_r30_archivar_devuelve_200_con_el_contrato`
- `tests/test_f013_fabricas.py::test_f013_r1_la_estrategia_por_omision_es_la_de_hoy`
- `tests/test_f031_cotejo_de_codigos.py::test_f031_r10_el_camino_bueno_sigue_devolviendo_las_seis_claves`
- `tests/test_f031_cotejo_de_codigos.py::test_f031_r4_el_mismo_codigo_escrito_de_dos_maneras_archiva` (sus 4 casos)
- `tests/test_f051_carpeta_base.py::test_f051_la_base_ausente_se_lee_como_ausente`
- `tests/test_f051_carpeta_base.py::test_f051_la_base_efectiva_por_estrategia` (`desconocida-ausente-postventa`, `por_obra-ausente-postventa`, `posventa-ausente-raiz`)

Los cubre el mismo fixture de `conftest.py`, sin tocar sus ficheros. Nota: esa pasada se
lanzó con `-p no:logging` por error y 273 tests que usan `caplog` dieron error de fixture
y no se evaluaron; por eso cuenta la pasada «después» (abajo), que corre la suite entera
sin ese flag.

## Verificación DESPUÉS

| Pasada | Resultado |
|---|---|
| 8 ficheros del encargo, sin variables | 637 passed in 5.39 s |
| 8 ficheros del encargo, con las ficticias | 637 passed in 5.73 s |
| 14 ficheros (encargo + barrido + `test_health`, `test_f003_fabrica`), sin variables | 745 passed in 7.83 s |
| los mismos 14, con las ficticias y el arreglo retirado (`git stash`) | 24 failed, 721 passed |
| los mismos 14, con las ficticias y el arreglo | 745 passed in 9.17 s |
| **suite unitaria entera de `api`, con las ficticias** | **9932 passed, 353 skipped in 855.25 s** |

La suite entera sin variables no se ha relanzado aquí: la mide `bash harness/init.sh`, que
corre el líder (encargo: no lo ejecuto yo).

## Pendiente

- `bash harness/init.sh` (líder).
- Reintentar la campaña de mutación de F-072 (T3) cuando esto llegue a `dev`.
