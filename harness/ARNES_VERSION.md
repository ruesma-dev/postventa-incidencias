<!-- harness/ARNES_VERSION.md -->
# Version del arnes instalada en este repositorio

Lo escribe `instalar_arnes.ps1`. **No lo edites a mano.**

| Dato | Valor |
|---|---|
| Version del arnes | `1.4.1` |
| Fecha de la version | 2026-08-18 |
| Instalado/actualizado el | 2026-08-18 |
| Modo | instalar (1.4.0) + actualizacion manual a 1.4.1 |
| Origen | `arnes-base` |

La 1.4.1 se aplico a mano (sus tres cambios: el parrafo de documentacion
compartida en `CLAUDE.md`, la seccion del puntero en
`docs/referencia/README.md` y `harness/VERSION`) porque el modo actualizar del
instalador habria pisado las adaptaciones de este proyecto, escritas una hora
antes de que se publicara la version.

Para actualizar a una version posterior, desde el repositorio `arnes-base`:

```powershell
.\instalar_arnes.ps1 -Destino "C:\Users\pgris\PycharmProjects\postventa-incidencias" -Modo actualizar
```

Antes de aceptar cambios, lee `GUIA_INSTALACION.md` en `arnes-base`: los
ficheros con marcas de adaptacion llevan contenido propio de este proyecto y
casi siempre hay que conservarlos, no sobrescribirlos.