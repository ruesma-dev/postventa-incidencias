<!-- progress/cierre_F-013.md -->
# Acta de cierre · F-013, el archivo se muda a la biblioteca de Posventa · 2026-09-25

## Qué cambia

Con `SHAREPOINT_ESTRUCTURA=posventa`, el parte archivado va a la biblioteca de
Posventa con **su** estructura, `<carpeta de obra>/PARTES INCIDENCIAS/<UNIDAD>/PARTES FIRMADOS`:

- la obra se reconoce por su número (`677  MIRASIERRA` es la 0677) y la unidad por el
  suyo (`VILLA 05` es la villa 5 de Sigrid); la hoja acepta `PARTES FIRMADOS` o
  `PARTES FIRMADO` (VILLA 02);
- lo que falta se **crea**, un nivel por llamada y **después** de dejar la traza
  previa: la unidad como `VILLA NN`, la hoja como `PARTES FIRMADOS`;
- lo dudoso **no se archiva**: 409 con uno de 22 motivos y lo que tiene que hacer una
  persona (parecidas, ambiguas, dos obras con el mismo número, una carpeta de dos
  unidades…);
- un parte ya archivado —los 133 de IT incluidos— **no** lee Sigrid, ni lista, ni sube:
  200 con su traza y los avisos de F-033. En IT no se mueve, copia ni borra nada.

Para saber la obra y la unidad se hacen **dos lecturas** por `sql/read` a `sigrid-api`.
**Hasta el corte, lo desplegado sigue en `por_obra`** (biblioteca de IT).

## Qué respalda el cierre

- **Review APROBADA** (`progress/review_F-013.md`), sin rechazo previo; cuatro
  hallazgos bajos, resueltos al cerrar: H-1 (verificaciones del corte en
  `current.md`), H-2 (R24 en el nombre del test), H-3 y H-4 (riesgos 18 y 19 en
  `design.md` §10).
- `bash harness/init.sh` en verde: **4.284 tests**, cobertura **100 % de 551 líneas**.
- Mutación formal (`progress/mutacion_F-013.md`): **109 / 108 / 1** —`_Nivel`,
  equivalente aceptado por el humano el 2026-09-24—, más 18 a mano (18 muertos).
- Punto 7 del reviewer (orden): **14 de 14** mutaciones de orden en rojo, hechas por
  el propio reviewer; más las de los bloques 2, 4 y 5 del implementer.
- Equivalentes a mano P2, M19 y M20: **aceptados por el humano el 2026-09-25**.

## Decisiones tomadas por el camino

- **T10 bis** (humano, «la a»): el test de firma de F-033 gana `resolver_destino`.
- Fallar cerrado sin configuración de `sigrid-api`, incluso con un parte ya archivado
  (líder; documentado en «qué se rompe»).
- Excepción con nombre para `test_f006_repo_sin_identificadores.py` en T16 (líder).
- La regla del 23 se compila como `<regla_del_23>` en el test (líder, T21).

## Lo que queda: el corte (MANUAL, humano)

Runbook en `docs/DESPLIEGUE.md` §9 y `tasks.md` «Después del merge». En corto: relanzar
los scripts 24 y 23 (R31) → avisar a Posventa por escrito → cargar los IDs de Posventa
y desplegar con `posventa` → R33 y R42 el mismo día. Tres frenos: cerrar la ventana,
dejar de crear, volver a `por_obra`.

## Mejoras del arnés que salen de aquí (aprobadas por el humano el 2026-09-25)

- Punto 7 del reviewer (RM7 en `arnes-base`): si una mutación de orden la caza primero
  un test de otra feature, repetir solo con los de la feature revisada.
- `CHECKPOINTS.md` C4 bis: en `critico`, los equivalentes **a mano** también necesitan
  la aceptación escrita del humano.
