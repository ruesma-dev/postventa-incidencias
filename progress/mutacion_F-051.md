<!-- progress/mutacion_F-051.md -->
# F-051 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-051 --workers 3` el 2026-10-01 17:33.

## Alcance

Origen del diff: **rama** (`a468367f31f1c552556c45f5cea2cfdebb2e5c03` .. `feature/F-051-carpeta-base-raiz`).

| Fichero | Líneas en alcance |
|---|---|
| `services/postventa-api/config/settings.py` | 16 |
| `services/postventa-api/infrastructure/sharepoint/fabrica.py` | 62 |
| `services/postventa-api/interface_adapters/api/archivar.py` | 8 |
| **Total** | **86** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 3 |
| Mutantes evaluados | 3 |
| Muertos | 3 |
| Supervivientes | 0 |
| Timeouts | 0 |
| Timeouts repasados en serie | 0: ningún mutante agotó el reloj |
| Tiempo total | 57.0 s |
| Workers | 3 |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.


## Complemento: mutantes a mano (implementer, 2026-10-01)

El operador del arnés generó solo 3 mutantes para 86 líneas: no muta
`return`, ternarias, argumentos ni defectos de campo. Se aplicaron a mano 9
más sobre la copia de trabajo, con los tests de F-051 y los de F-013 de la
fábrica y del borde (`test_f013_fabricas.py`, `test_f013_archivar_http.py`), y
se restauró cada fichero en bytes tras cada uno (`git status` limpio al acabar).

| Mutante | Resultado |
|---|---|
| `carpeta_base_efectiva`: ausente en `posventa` → `Postventa` (el incidente) | muerto |
| `carpeta_base_efectiva`: ausente en `por_obra` → raíz | muerto |
| `carpeta_base_efectiva`: ignora un valor puesto | muerto |
| traza: ternaria al revés (`raíz` ↔ nombre) | muerto |
| traza: sin recortar la base (`/` saldría `«/»`) | muerto |
| traza: eliminada | muerto |
| `archivar.py`, resolutor: `base=ajustes.sharepoint_carpeta_base or "Postventa"` | muerto |
| `settings.py`: el defecto `Postventa` de vuelta en el campo | muerto |
| `archivar.py`, paso: `carpeta_base=ajustes.sharepoint_carpeta_base or "Postventa"` | **superviviente** |

**Análisis del superviviente: equivalente en producción.** En `paso_archivo`,
`carpeta_base` solo se usa con `por_obra` (`componer_destino`); en `posventa`
manda el resolutor, que recibe `base=` (ese mutante sí muere). En `por_obra`,
ausente da `Postventa` con el mutante y sin él. Solo difieren con `por_obra` y
la base puesta a `""`, y ese caso **no llega al paso** en producción: lo
rechaza `construir_archivador` (F-013 R17, `test_f051_a3_..._se_rechazan_en_por_obra`).
Cazarlo exigiría un test con el archivador inyectado que afirmara la ruta
`/0677`, es decir, fijar como correcto el comportamiento que R17 prohíbe. No se
escribe.
