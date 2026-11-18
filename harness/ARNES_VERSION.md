<!-- harness/ARNES_VERSION.md -->
# Version del arnes instalada en este repositorio

Lo escribe `instalar_arnes.ps1`. **No lo edites a mano.**

| Dato | Valor |
|---|---|
| Version del arnes | `1.10.0` |
| Fecha de la version | 2026-11-12 |
| Instalado/actualizado el | 2026-11-12 19:37 |
| Modo | actualizar |
| Origen | `arnes-base` |

Para actualizar a una version posterior, desde el repositorio `arnes-base`:

```powershell
.\instalar_arnes.ps1 -Destino "C:\Users\pgris\PycharmProjects\postventa-incidencias" -Modo actualizar
```

Que hace el instalador por su cuenta al actualizar, sin que tengas que
vigilarlo fichero a fichero:

- **No toca el estado de este proyecto**: `harness/features.json`,
  `docs/ARCHITECTURE.md`, `progress/`, `specs/`, `docs/referencia/`,
  `BACKLOG.md` y la configuracion local. Ni con `-Forzar`.
- **Aplica sin preguntar** los ficheros genericos del arnes (los agentes,
  `harness/*.py`, `specs/SPECS.md`...), guardando antes una copia de la
  version que tenias.
- **Pregunta solo** por los que mezclan lo generico con lo tuyo (`CLAUDE.md`,
  `CHECKPOINTS.md`, `harness/init.sh`, `docs/CONVENTIONS.md`,
  `.claude/settings.json`), y la opcion por defecto es CONSERVAR el tuyo.

La clasificacion completa vive en `politica_ficheros.json`, en `arnes-base`.
Detalle en `GUIA_INSTALACION.md`.

## Lo que se hizo a mano tras el instalador (2026-11-12)

El instalador se lanzo contra el worktree `postventa-arnes` (rama
`feature/arnes-1.10`); el destino de las proximas actualizaciones es
`postventa-incidencias`, como dice el comando de arriba. Venia de la `1.5.2`
con el parche de la 1.6.3 y tres piezas de la 1.7.8 (historia completa en
este mismo fichero en `dev`, antes del merge). Detalle en
`progress/arnes_1.10.md`.

- **Capa local de rigor** (`harness/rigor.local.json`): `nivel_por_defecto`
  `critico` y `mutacion.workers` 8, los dos ajustes propios que llevaba
  `harness/rigor.json` y que la actualizacion piso. Se versiona y el
  instalador no la toca.
- **Los 6 mixtos se conservaron en el instalador y se fusionaron a mano**:
  `CLAUDE.md`, `CHECKPOINTS.md`, `harness/init.sh`, `docs/CONVENTIONS.md` y
  `.claude/settings.json` llevan lo generico de la 1.10.0 mas lo propio;
  `docs/referencia/README.md` no cambia en la 1.10.0 y se conserva.
- **`CHECKPOINTS.md` lleva dos reglas de C4 bis que la 1.10.0 no trae**
  (mutantes a mano cazados por la propia feature; guarda por definiciones que
  ve tambien las sentencias de modulo), nacidas aqui en F-060 y pendientes en
  `arnes-base` como
  `ENCARGO_pendiente_mutantes_a_mano_de_la_propia_feature_y_guarda_de_modulo.md`.
  Al actualizar, conservalas mientras el payload no las traiga.
- **`tests/test_f063_textos.py` lleva un arreglo local** (el test r2 se salta
  fuera del taller): sin el, la capa local pone la suite en rojo. Pendiente en
  `arnes-base` como
  `ENCARGO_pendiente_test_f063_r2_rojo_en_proyectos_con_capa_local.md`; si la
  version siguiente no lo trae, el instalador lo pisara y hay que reaplicarlo.