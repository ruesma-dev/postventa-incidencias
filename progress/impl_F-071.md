<!-- progress/impl_F-071.md -->
# F-071 · informe de implementación

## T0 · Prueba de los prototipos de F-058, Excel de escritorio (líder, 2026-11-05)

A petición del humano, el líder hizo la parte de **Excel de escritorio** por
automatización (COM de Excel 16) sobre **copias** de
`prototipo_f058_a1.xlsx` y `prototipo_f058_a2.xlsx` (datos ficticios), sin
desproteger la hoja. Para cada caso se escribe la unidad y cada una de las
103 ubicaciones ficticias en la celda de `Ubicación` y se pregunta a Excel si
la validación la da por buena (`Validation.Value`). Las copias se borraron.

| Punto | Escritorio · a1 | Escritorio · a2 |
|---|---|---|
| 1 · Vivienda 1 acepta solo la lista A | sí | no (acepta cualquier cosa) |
| 1 · Orden y número de la lista | no medible por COM | sí (31, en orden) |
| 2 · Vivienda 6 → solo B; Vivienda 11 → solo C | sí | no |
| 3 · Unidad vacía rechaza lo tecleado | **no** (lo acepta) | no |
| 4 · Vivienda 15 (sin ubicaciones) rechaza | sí | no |
| 5 · Acepta otra mayúscula | sí (esperado) | sí |
| 6 · Fila 1001 igual que la 2 | sí | no |
| 7 · Funciona con la hoja protegida | sí | sí |
| 8 · Sigue tras guardar, cerrar y reabrir | sí | no |
| 9 · Sin espera apreciable | sí (abre en ~5 s con el arranque de Excel) | sí |

Lectura:
- **a2 no sirve**: su validación acepta cualquier valor.
- **a1 cumple** salvo el punto 3: con la `Unidad` vacía, Excel acepta lo que
  se teclee en `Ubicación` (el riesgo «lista vacía + omitir blancos» que ya
  avisó T0 de F-058). La importación lo rechaza igual (fila sin unidad).
- Sin medir por COM: lo que **se ve** en el desplegable (orden en a1) y
  **Excel web**. Quedan para el humano.

D-1: pendiente de la decisión del humano (recomendación del líder: **a1**).
