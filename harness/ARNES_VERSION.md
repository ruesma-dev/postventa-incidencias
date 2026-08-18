<!-- harness/ARNES_VERSION.md -->
# Version del arnes instalada en este repositorio

Lo escribe `instalar_arnes.ps1`. **No lo edites a mano.**

| Dato | Valor |
|---|---|
| Version del arnes | `1.5.0` |
| Fecha de la version | 2026-08-18 |
| Instalado/actualizado el | 2026-08-18 |
| Modo | instalar (1.4.0) + actualizacion manual a 1.4.1 y a 1.5.0 |
| Origen | `arnes-base` |

La 1.4.1 y la 1.5.0 se aplicaron a mano, por el mismo motivo: el modo
actualizar del instalador es interactivo y los unicos ficheros que habria
tocado en este repositorio son los adaptados (`CLAUDE.md`, `CHECKPOINTS.md`,
`docs/ARCHITECTURE.md`, `harness/features.json`, `harness/init.sh`), que hay
que conservar. Lo que aporta cada version se copio literal:

- **1.4.1**: el parrafo de documentacion compartida en `CLAUDE.md`, la seccion
  del puntero en `docs/referencia/README.md` y `harness/VERSION`.
- **1.5.0**: `harness/backlog.py` y `tests/test_backlog_md.py` (copia literal),
  la seccion `3 bis` de `harness/init.sh` (que genera `BACKLOG.md`) y los dos
  parrafos de `CLAUDE.md` sobre delegar en subagentes como via normal, mas la
  entrada de `BACKLOG.md` en el mapa del repositorio.

Comprobado tras aplicarla: `harness/init.sh` solo difiere del payload 1.5.0 en
las tres lineas de adaptacion de este proyecto (`REQUIERE_ENV=0` y las dos
cabeceras de adaptacion ya resueltas). El resto del arnes generico
—`.claude/agents/*`, `specs/SPECS.md`, `harness/*.py`— es identico al payload.

Para actualizar a una version posterior, desde el repositorio `arnes-base`:

```powershell
.\instalar_arnes.ps1 -Destino "C:\Users\pgris\PycharmProjects\postventa-incidencias" -Modo actualizar
```

Antes de aceptar cambios, lee `GUIA_INSTALACION.md` en `arnes-base`: los
ficheros con marcas de adaptacion llevan contenido propio de este proyecto y
casi siempre hay que conservarlos, no sobrescribirlos.
