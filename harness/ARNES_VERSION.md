<!-- harness/ARNES_VERSION.md -->
# Version del arnes instalada en este repositorio

Lo escribe `instalar_arnes.ps1`. **No lo edites a mano.**

| Dato | Valor |
|---|---|
| Version del arnes | `1.5.2` + el parche de la 1.6.3 y tres piezas de la 1.7.8, aplicados a mano |
| Fecha de la version | 2026-08-18 (parche de la 1.6.3: 2026-08-20; piezas de la 1.7.8: 2026-09-02) |
| Instalado/actualizado el | 2026-08-20 (ultimo parche a mano: 2026-09-02) |
| Modo | instalar (1.4.0) + actualizacion manual a 1.4.1, 1.5.0, 1.5.1 y 1.5.2, mas el parche de la 1.6.3 y tres piezas de la 1.7.8 |
| Origen | `arnes-base` |

> **Este repositorio NO lleva la 1.6.x completa, y `harness/VERSION` sigue
> diciendo `1.5.2` a proposito.** De la rama 1.6 se ha traido UNICAMENTE el
> parche de la 1.6.3 (ver abajo). Las 1.6.0, 1.6.1 y 1.6.2 estan PENDIENTES, y
> la 1.6.0 no es un parche: rehace `harness/mutacion.py` entero -linea base de
> la suite, veredicto «base rota», mutacion de `is`/`is not`- y sus numeros no
> son comparables con los de antes. Poner aqui `1.6.3` daria a entender que ese
> trabajo esta hecho, y no lo esta.

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

- **Parche de la 1.6.3** (2026-08-20): la campana de mutacion deja de envenenar
  el arbol con bytecode. `EjecutorPytest` muta un `.py`, lanza la suite en un
  subproceso y restaura el original; ese subproceso escribia `__pycache__`, asi
  que quedaba en disco un `.pyc` compilado DESDE EL CODIGO MUTADO, y CPython lo
  seguia dando por bueno porque valida la cache por (tamano, mtime) del fuente
  y la restauracion deja los dos iguales. Desde ahi, la campana mide contra un
  codigo que ya no esta. Arreglo:
  `env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}` en el `subprocess.run`
  de `EjecutorPytest.ejecutar`, con `tests/test_mutacion_sin_bytecode.py`
  vigilando las dos mitades. Y en `CHECKPOINTS.md` C4 bis, la regla objetiva
  que lo habria cazado el primer dia: «Tiempo total» entre numero de mutantes
  por debajo de UN SEGUNDO es sospechoso por construccion y la campana se
  relanza con la cache limpia. **Esta mitad nacio aqui**, en la review de
  F-010, y se porto a `arnes-base` en el mismo trabajo (regla de propagacion),
  donde se sello como 1.6.3 sobre la 1.6.2 que alli ya existia. Aqui se ha
  aplicado a mano sobre el `mutacion.py` de la 1.5.1, que es el que lleva este
  repositorio: el de la 1.6.x tiene otra estructura -el metodo se llama
  `correr` y devuelve un `ResultadoSuite`- y traerlo entero seria hacer la
  1.6.0, no un parche.

- **Tres piezas de la 1.7.8** (2026-09-02): el veredicto `timeout` de una
  campana de mutacion no decia nada del mutante, decia que la maquina estaba
  saturada. La suite del servicio `api` tarda 38,7 s en solitario y 131,6 s
  ejecutada con los 16 workers que usaba la campana, por encima del tope de
  120 s por mutante; tres campanas del MISMO commit de F-009 dieron 15, 27 y 0
  timeouts, sobre mutantes distintos cada vez. Diagnostico con diez mediciones
  en `progress/explore_F-009_timeouts.md`. Lo aplicado aqui:
  1. `harness/alcance.py`: `harness` entra en `DIRECTORIOS_EXCLUIDOS`. Sin
     esto, tocar el arnes desde la rama de una feature metia el codigo del
     propio arnes en el alcance mutable y en la puerta de cobertura: la
     campana se mutaba a si misma.
  2. `harness/mutacion_paralela.py`: al terminar una campana paralela, los
     mutantes en `timeout` se repasan EN SERIE sobre un solo worktree y se
     sustituye su veredicto por el real (`reemplazar_timeouts`, `repasar`). Un
     `timeout` deja de ser un veredicto y pasa a ser un reintento; el que
     sobrevive al repaso si es senal de un cuelgue de verdad.
  3. `harness/mutacion.py`: el informe registra con cuantos workers se midio y
     cuantos timeouts se repasaron. Sin ese dato no se pudo reconstruir como
     se habia lanzado la campana del 2026-08-27, que es justo lo que costo el
     dia. Con ello, `harness/rigor.json` declara ya `mutacion.workers: 8`.
  Vigilan el cambio `tests/test_alcance_excluidos.py`,
  `tests/test_mutacion_repaso_timeouts.py` y
  `tests/test_mutacion_informe_workers.py` (39 tests nuevos: la suite del
  arnes pasa de 17 a 56). **Esta mejora nacio aqui**, cerrando la T28 de
  F-009, y se porto a `arnes-base` en el mismo trabajo (regla de
  propagacion), donde se sello como **1.7.8** sobre la 1.7.7. Alli hizo falta
  una adaptacion que aqui NO aplica: como en `arnes-base` el arnes ES el
  producto, la exclusion protege solo el alcance AUTOMATICO -el que sale del
  diff- y no el que declara una persona con `--ficheros`, bandera que llego en
  la 1.7.1 y que este repositorio no tiene. Detalle en
  `progress/impl_arnes_reintento_timeouts.md`.

  **Este repositorio sigue sin llevar la 1.6.x ni la 1.7.x completas**, y
  `harness/VERSION` sigue diciendo `1.5.2` por el mismo motivo de siempre: de
  esas ramas solo se han traido parches concretos, no el trabajo entero.

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
