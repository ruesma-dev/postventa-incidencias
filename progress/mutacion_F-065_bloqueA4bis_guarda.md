<!-- progress/mutacion_F-065_bloqueA4bis_guarda.md -->
# F-065 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-065 --base e623caf --workers 1` el 2026-10-30 01:15.

## Alcance

Origen del diff: **rama** (`e623caf083e4cd7e92475a24903999426b827430` .. `feature/F-065-revision-sigrid-backend`).

| Fichero | Líneas en alcance |
|---|---|
| `services/postventa-api/application/pipelines/guarda_sigrid.py` | 223 |
| `services/postventa-api/application/pipelines/sigrid_bandeja.py` | 21 |
| `services/postventa-api/application/pipelines/volcado.py` | 71 |
| `services/postventa-api/domain/models/sigrid_bandeja.py` | 3 |
| `services/postventa-api/domain/models/volcado.py` | 8 |
| `services/postventa-api/domain/ports/reclamaciones_obra.py` | 11 |
| `services/postventa-api/function_app.py` | 18 |
| `services/postventa-api/infrastructure/sigrid/consultas_reclamaciones_obra.py` | 113 |
| `services/postventa-api/infrastructure/sigrid/reclamaciones_obra.py` | 28 |
| `services/postventa-api/interface_adapters/api/volcado.py` | 113 |
| **Total** | **609** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 51 |
| Mutantes evaluados | 51 |
| Muertos | 51 |
| Supervivientes | 0 |
| Timeouts | 0 |
| Timeouts repasados en serie | 0: ningún mutante agotó el reloj |
| Tiempo total | 24996.2 s |
| Workers | 1 |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.

## Nota del implementer (Bloque A4 bis · T15–T17, la guarda del ensayo)

- **Dónde se lanzó.** En un `git worktree` desechable de la rama, separado
  (`--detach`) en `f461380`, con el árbol limpio antes y después. La ejecuta
  `harness.mutacion.main(...)` con el mismo alcance y el mismo informe
  (`--feature F-065 --base e623caf --workers 1 --timeout 900 --salida
  progress/mutacion_F-065_bloqueA4bis_guarda.md`), pero con un
  `EjecutorPytest` cuya suite son los ficheros que importan lo mutado o lo
  ejercitan, con `-x`.
- **La suite reducida (16 ficheros)**:
  - de F-065: `guarda_ensayo`, `consulta`, `adaptador`, `aplicacion`, `http`,
    `datos_personales`, `veredicto`, `dominio` y `scripts_infra`;
  - de F-059: `volcado_dominio`, `pipeline_volcado`, `volcado_http`,
    `repositorio_volcado`, `ddl`, `documentacion` y `scripts_infra`.
- **Cómo se eligió.** Busqué en `tests/` quién importa los diez módulos
  mutados (`guarda_sigrid`, los pipelines `sigrid_bandeja` y `volcado`, el
  borde `volcado`, `function_app`, el modelo `volcado`, el modelo
  `sigrid_bandeja`, el puerto, la consulta y el adaptador), directamente o por
  `tests/utiles_volcado.py`. Quedan fuera:
  - las guardas de alcance (`test_f059_alcance_cerrado.py`,
    `test_f065_alcance_cerrado.py`), que leen el código **como texto** y el
    diff de la rama, así que un mutante sin commit no las cambia;
  - `tests_bbdd/` de F-059, que necesita una base y no se lanza en local.
- **1.ª ronda, sobre `2c1e366`**: 51 evaluados, 48 muertos, **3
  supervivientes**, 0 timeouts, en 2097,5 s:
  - `guarda_sigrid.py:62` y `:76` (`frozen=True` → `False`): hueco real,
    nada comprobaba que el resultado de la guarda fuera inmutable;
  - `interface_adapters/api/volcado.py:496` (`<=` → `<` en el tope de 50
    códigos): hueco real, solo se probaba el 51.

  Los matan, en `f461380`,
  `test_f065_r47_lo_que_deja_la_guarda_no_se_puede_cambiar` y
  `test_f065_r43_cincuenta_codigos_distintos_es_el_maximo_que_se_admite`. Lo
  comprobé también a mano (HT1 a HT3 de `progress/impl_F-065.md`).
- **2.ª ronda, sobre `f461380`**: es la de arriba, 51 de 51 muertos. Su tiempo (24996,2 s) no es comparable con el de la 1.ª ronda: corrió a la vez que las guardas de alcance y con el equipo suspendido una parte de la noche.
