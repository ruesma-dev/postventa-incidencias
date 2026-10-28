<!-- progress/mutacion_F-065_bloqueA2.md -->
# F-065 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-065 --base 16453b5 --workers 1` el 2026-10-28 20:59.

> **Nota del implementer (no la escribe la herramienta).** Esta campaña **no**
> es el comando tal cual: es `harness.mutacion.main(...)` con el mismo alcance,
> los mismos mutantes y el mismo informe, pero con un `EjecutorPytest` cuya
> suite es **solo** `tests/test_f065_dominio.py` (en serie, `--timeout 300`).
> Motivo: la máquina estaba cargada con las campañas de mutación de otros
> repositorios (`partes`, `facturas`, `albaranes`) y la suite entera del
> servicio tardó **25 min 33 s** (1.533 s), así que con el timeout de 120 s
> por mutante todos habrían salido `timeout`. Es equivalente para matar o
> sobrevivir: **ningún otro módulo importa `domain/models/sigrid_bandeja.py`**
> (búsqueda en `services/`: solo él y su test), así que ningún otro test puede
> cazar un mutante suyo. El comando oficial, para cuando la máquina esté
> libre: `python -m harness.mutacion --feature F-065 --base 16453b5 --salida
> progress/mutacion_F-065_bloqueA2.md`. Envoltorio usado (fuera del repo):
> `EjecutorPytest(raiz=services/postventa-api, argumentos=["-x", "-q",
> "--tb=no", "-p", "no:cacheprovider", "tests/test_f065_dominio.py"],
> ejecutable=services/postventa-api/.venv/Scripts/python.exe)`.
>
> Primera pasada (antes de `718a633`): 52 generados, 47 muertos, **5
> supervivientes**, todos `@dataclass(frozen=True) -> frozen=False` (líneas
> 151, 173, 192, 213 y 221: `ReclamacionSigrid`, `Hallazgo`, `Cruce`,
> `_Texto`, `_Candidata`). Ningún test comprobaba la inmutabilidad: hueco
> real, no equivalente. Se cierra con
> `test_f065_r19_los_tipos_del_cruce_son_inmutables` (los tres públicos) y
> pasando los dos privados a `NamedTuple` (inmutables por construcción, sin
> bandera que mutar). Esta es la segunda pasada.

## Alcance

Origen del diff: **rama** (`16453b58e6f28a3c1dd17444feff0b9a3e50c3d8` .. `feature/F-065-revision-sigrid-backend`).

| Fichero | Líneas en alcance |
|---|---|
| `services/postventa-api/domain/models/sigrid_bandeja.py` | 528 |
| **Total** | **528** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 50 |
| Mutantes evaluados | 50 |
| Muertos | 50 |
| Supervivientes | 0 |
| Timeouts | 0 |
| Timeouts repasados en serie | 0: ningún mutante agotó el reloj |
| Tiempo total | 193.5 s |
| Workers | 1 |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.

