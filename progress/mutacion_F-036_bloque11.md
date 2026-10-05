<!-- progress/mutacion_F-036_bloque11.md -->
# F-036 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-036 --base c58e3b4 --workers 2` el 2026-10-01 22:44.

## Alcance

Origen del diff: **rama** (`c58e3b45d976f36f92f10c23e69f1e9e4777179b` .. `feature/F-036-importar-excel`).

| Fichero | Líneas en alcance |
|---|---|
| `services/postventa-api/infrastructure/documentos/ejecutor_aislado.py` | 48 |
| **Total** | **48** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 2 |
| Mutantes evaluados | 2 |
| Muertos | 2 |
| Supervivientes | 0 |
| Timeouts | 0 |
| Timeouts repasados en serie | 0: ningún mutante agotó el reloj |
| Tiempo total | 318.6 s |
| Workers | 2 |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.

## Notas del implementer (T49, 2026-10-01)

- **La orden y lo que corrió.** Se lanzó
  `python -m harness.mutacion --feature F-036 --base c58e3b4 --workers 6 --timeout 900 --salida progress/mutacion_F-036_bloque11.md`
  desde la raíz. Se pidieron 6 workers y la herramienta usó **2** (uno por
  mutante: solo generó dos), que es lo que dice su tabla de arriba.
- **Una primera tanda, sin `--timeout`** (la orden literal de `tasks.md`, con
  el tope por defecto de 120 s de `harness/rigor.json`), dio **2 timeouts y
  ningún veredicto**, también en el repaso en serie (362,4 s): la suite del
  `api` tarda más de 120 s en llegar a los tests que matan. No es un cuelgue
  de los mutantes. Se repitió con `--timeout 900`, como todas las campañas de
  F-036, y es el informe de arriba: **2 generados, 2 muertos**.
- **Supervivientes: ninguno.** No hay nada que analizar ni equivalentes.
- **Lo que la herramienta no genera.** Sus operadores solo sacan dos mutantes
  de las 48 líneas (el resto son comentarios, *docstring* y llamadas). Las
  mutaciones que pide T49 (quitar el `setrlimit`, cambiar `RLIMIT_CPU` por
  otro, quitar o cambiar el margen, quitar el redondeo, ponerlo después del
  byte del canal) y otras del mismo corte se aplicaron **a mano**, una a una,
  sobre una copia de `git archive HEAD`, pasando los tests `r119` de
  `tests/test_f036_lector_aislado.py` en Windows y en un contenedor Linux sin
  red: **14 de 14 caen en Windows**, por los tests con `setrlimit` doblado;
  **ninguna cae solo en Linux**. La tabla, en `progress/impl_F-036.md`,
  «Bloque 11 (T45–T49)».
