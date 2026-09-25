<!-- progress/review2_F-049.md -->
# F-049 · Las villas que crea el archivo, siempre con tres cifras — Segunda review

- **Veredicto:** APPROVED (APROBADO), a falta de un paso que no es del
  implementer: la aceptación escrita de M7 y M8 por el humano (§4)
- **Rama:** `feature/F-049-villa-tres-cifras`, `4dce6cd` (la primera review
  fue sobre `993dcbe`, acta en `cf93243`)
- **Fecha:** 2026-09-25 · reviewer

Los dos cambios de §6 de `progress/review_F-049.md` están hechos y bien
hechos. El commit de corrección solo toca tres ficheros de `progress/`: ni
código, ni tests, ni specs, ni docs. Todo lo que se aprobó en la primera
review sigue en pie (checkpoints, fase RED, cobertura, mutación reejecutada,
tabla requisito → test) y no lo repito aquí.

## 1 · Nivel de rigor

`critico`, declarado en `harness/features.json` y válido según `init.sh`.
Exige lo mismo que en la primera review: fase RED con traza real, cobertura
≥ 80 % de lo cambiado, mutación con totales comprobados por mí, cero
supervivientes salvo equivalentes aceptados por escrito por el humano, y las
MANUAL en `progress/current.md` con su comando exacto.

## 2 · Verificaciones que he hecho yo

| Qué | Resultado |
|---|---|
| `bash harness/init.sh` (tal cual) | **ENTORNO LISTO**. Raíz: 62 passed; api y front en verde **desde la caché** («árbol sin cambios desde el último verde»): es legítimo, porque desde el verde de la primera review solo han cambiado ficheros de `progress/`. `PUERTA COBERTURA: 100.0% de 1 líneas cambiadas cubiertas (1/1, umbral 80%, nivel critico)`. ruff, 61 avisos: la deuda previa |
| `git diff --stat cf93243 4dce6cd` | 3 ficheros: `progress/current.md` (+21 −3), `progress/impl_F-049.md` (+16 −0), `progress/mutacion_F-049.md` (+16 −7). Nada más |
| Código, tests, specs, docs, infra y harness sin tocar | `git diff --stat 884a0ee cf93243` y `884a0ee 4dce6cd` restringidos a `services infra docs specs tests harness`: **idénticos** (16 ficheros, +865 −74) |
| Líneas borradas en la corrección | solo la viñeta MANUAL antigua de F-049 (la que pedí sustituir), la viñeta de M8 (su frase falsa queda **citada literal** en un recuadro fechado) y la frase «Comprobado numéricamente … `0 … 199999`», reescrita con el rango ampliado |
| Comandos del paso 2 | los dos del bloque de F-049 son **carácter a carácter** los del bloque de F-013 (`current.md` 26/28 frente a 52/54) y coinciden con `docs/DESPLIEGUE.md` 752/756 salvo «repositorio» → «repo» en el marcador de la ruta, que ya era así en F-013 |
| Salida esperada nueva frente a `docs/DESPLIEGUE.md` §9 (recuadro F-049, 780–801) | compatible: obra y `PARTES INCIDENCIAS` «resolvería»; 1–7, 12 y 13 en su carpeta de tres cifras (DESPLIEGUE admite «resolvería» o «crearía `PARTES FIRMADOS`» según la hoja; `current.md` concreta 001–007 «resolvería» y 012, 013 «crearía `PARTES FIRMADOS`»); 8–11, 14, 15 «crearía `VILLA 008`» …; ninguna «bloquearía»; `DESTINO DE POSVENTA : PASA` |
| Nota fechada en el bloque de F-013 | presente («Sustituida el 2026-09-25 por F-049 …»), remite al bloque de arriba y **conserva** la salida antigua |
| M8, motivo nuevo | `format(-5,'0=3d')`, `format(-5,'03d')` y `format(-5,'03')` dan los tres `-05`; `format(n,'03') == format(n,'03d') == format(n,'0=3d')` para `n` en −200000…199999: **True**. El motivo nuevo («el `0` delante del ancho ya pone relleno `0` y alineación `=`») es el que da la documentación de Python |
| Árbol limpio al terminar | `git status` sin cambios salvo este informe |

## 3 · Checkpoints

Todos como en la primera review, con los dos `[ ]` resueltos:

### C1 — El arnés está completo y en verde
- [x] `init.sh` exit 0. · [x] Ficheros base.

### C2 — El estado es coherente
- [x] Una sola `in_progress` (F-049). · [x] Rama correcta.
- [x] `progress/current.md` coherente (bloque de F-049 arriba, bloques de
      F-013 debajo con su nota fechada).
- [x] `history.md`: F-049 aún no es `done`.

### C3 — Arquitectura y convenciones
- [x] Sin cambios desde la primera review (el commit nuevo es solo
      `progress/`). Los N/A de C3 siguen justificados en `review_F-049.md` §3.

### C3 bis — Documentos que entran de fuera
- N/A · F-049 no toca `docs/referencia/`.

### C4 — La verificación es real
- [x] Cada requisito con su `test_f049_rN_*`, en verde (tabla en
      `review_F-049.md` §5, sin cambios).
- [x] Sin red ni BBDD.
- [x] **MANUAL listadas con su comando exacto** (antes `[ ]`, cambio 1): el
      bloque de F-049 trae los dos comandos del paso 2, la salida esperada
      nueva y «Cualquier diferencia: no se despliega»; el bloque de F-013
      lleva su nota fechada que remite al nuevo.

### C4 bis — El rigor declarado se cumple
- [x] `critico` declarado. · [x] Fase RED (reproducida en la primera
      review). · [x] Cobertura `[OK]` 100 %.
- [x] Mutación: 0 del arnés (con prueba de control) y 9 a mano, todo
      reejecutado por mí en la primera review; el commit nuevo no cambia ni
      el código ni los tests, así que esos resultados siguen valiendo.
- N/A · Coste por mutante: 0 mutantes del arnés, la fórmula divide por cero
  (justificado en `review_F-049.md` §3; nada nuevo).
- [x] **Análisis de supervivientes** (antes `[ ]`, cambio 2): el motivo de M8
      ahora es cierto y está comprobado por mí. M7 y M8 son equivalentes.
- **Pendiente, fuera del implementer:** la **aceptación escrita del
  humano** de M7 y M8, que exige `critico`. La gestiona el líder y no cuenta
  como fallo de esta review, pero **F-049 no puede pasar a `done` sin ella**.
  Mi recomendación sigue siendo aceptar los dos, ahora sobre el texto
  corregido de `progress/mutacion_F-049.md`.
- [x] Evidencias con los cuatro números.
- N/A · Punto 7 (orden): el requisito central es un valor (el ancho), no un
  orden entre colaboradores (justificado en `review_F-049.md` §3).

### C4 ter — Rutas sensibles
- N/A · No existe `harness/rutas_sensibles.json`.

### C5 — Cierre de sesión
- [x] `tasks.md` T1–T7 `[x]` con sus commits `F-049 Tn:`; el de corrección
      (`4dce6cd`) es posterior a la review y lleva el prefijo `F-049:`.
- [x] Sin ficheros sin trackear del implementer.
- [x] `features.json`: `in_progress`.

## 4 · Para el líder

1. **Aceptación de M7 y M8.** Pendiente del humano, por escrito. El texto que
   acepta es el de `progress/mutacion_F-049.md`, viñetas M7 y M8 y el
   recuadro de corrección.
2. **La línea «Hecho el 2026-09-25 (humano)»** de `progress/current.md`
   (líneas 35–39) no la pedí yo: el implementer anota que el humano ya
   ejecutó el paso 2 contra la red real y salió lo esperado, «recibido por el
   líder». **No puedo verificarlo** (es una ejecución contra SharePoint y
   Sigrid que no está en el repositorio ni debe estarlo). Si el humano no lo
   dijo así, esa línea hay que quitarla antes del cierre. Relacionado: la
   salida esperada del bloque de F-049 es más concreta que la de
   `DESPLIEGUE.md` §9 (dice qué villas reorganizadas tienen hoja) porque sale
   de esa ejecución; si el paso 2 se repite otro día y Posventa ha tocado las
   hojas, manda la regla general de `DESPLIEGUE.md`.
3. Las observaciones no bloqueantes y las tres propuestas de automejora de
   `review_F-049.md` §7 y §8 siguen abiertas para el humano.
4. Este informe no está commiteado; queda para el líder, como el de la
   primera review.

## 5 · Cambios requeridos

Ninguno.
