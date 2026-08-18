<!-- harness/ARNES_VERSION.md -->
# Version del arnes instalada en este repositorio

Lo escribe `instalar_arnes.ps1`. **No lo edites a mano.**

| Dato | Valor |
|---|---|
| Version del arnes | `1.5.2` |
| Fecha de la version | 2026-08-18 |
| Instalado/actualizado el | 2026-08-18 |
| Modo | instalar (1.4.0) + actualizacion manual a 1.4.1, 1.5.0, 1.5.1 y 1.5.2 |
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
- **1.5.1** (2026-08-18): repetir una campana de mutacion ya no borra el
  analisis de los supervivientes que hubiera escrito el implementer. Copia
  literal de `harness/mutacion.py` y `tests/test_mutacion_informe.py` desde
  `arnes-base`; comprobado antes de copiar que este repositorio no tenia
  ninguna adaptacion local en `mutacion.py` (era byte a byte el de la 1.5.0).
- **1.5.2** (2026-08-18): el reviewer reejecuta la campana de mutacion cuando
  el «Tiempo total» del informe baja de 5 minutos, en vez de limitarse a
  recontar mutantes. Toca `.claude/agents/reviewer.md` (punto 4) y el bloque
  `C4 bis` de `CHECKPOINTS.md`. **Esta mitad nacio aqui**, en la review de
  F-002, y se porto a `arnes-base` por la regla de propagacion; alli se
  numero primero dentro de la 1.5.1 y despues se separo en su propia 1.5.2,
  para que un mismo numero de version no describiera dos contenidos distintos
  segun el repositorio.

Comprobado tras aplicarla: `harness/init.sh` solo difiere del payload 1.5.0 en
las tres lineas de adaptacion de este proyecto (`REQUIERE_ENV=0` y las dos
cabeceras de adaptacion ya resueltas). El resto del arnes generico
—`.claude/agents/*`, `specs/SPECS.md`, `harness/*.py`— es identico al payload.

Al sellar la 1.5.2 se hizo el **barrido completo del payload**, fichero a
fichero e ignorando finales de linea (este repositorio usa CRLF y el payload
LF): 32 ficheros comparados —los 33 del payload menos `harness/gitignore.arnes`,
que el instalador no copia—, 20 identicos, 1 ausente
(`tests/test_mutacion_informe.py`) y 11 distintos. De esos 11, nueve lo son por
adaptacion de este proyecto (`CLAUDE.md`, `CHECKPOINTS.md`,
`docs/ARCHITECTURE.md`, `docs/CONVENTIONS.md`, `docs/referencia/README.md`,
`harness/features.json`, `harness/init.sh`, `progress/current.md`,
`progress/history.md`), uno era `harness/mutacion.py` sin la 1.5.1 y el ultimo,
este propio sello. Ninguna divergencia inesperada: el arnes de este repositorio
no estaba trabajando sobre codigo viejo mas alla de la 1.5.1 que faltaba.
Verificado ademas que la campana de mutacion sigue operativa tras el cambio
(F-002, 45 mutantes, 45 muertos, 0 supervivientes, 14,5 s, con el arbol limpio
al terminar).

Para actualizar a una version posterior, desde el repositorio `arnes-base`:

```powershell
.\instalar_arnes.ps1 -Destino "C:\Users\pgris\PycharmProjects\postventa-incidencias" -Modo actualizar
```

Antes de aceptar cambios, lee `GUIA_INSTALACION.md` en `arnes-base`: los
ficheros con marcas de adaptacion llevan contenido propio de este proyecto y
casi siempre hay que conservarlos, no sobrescribirlos.
