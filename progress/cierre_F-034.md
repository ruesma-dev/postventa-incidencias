<!-- progress/cierre_F-034.md -->
# Acta de cierre · F-034, adjuntar y cerrar leen de lo persistido · 2026-09-23

## Qué cambia

`/api/adjuntar` y `/api/cerrar` dejan de fiarse del cuerpo de la petición:

- **si el parte consta archivado** se lee de la traza guardada (`postventa.archivos`,
  vía la situación que trae F-033), con la puerta compartida `exigir_parte_archivado`;
- **el número de incidencia y el código de obra** salen de lo guardado; los del cuerpo
  solo se cotejan (normalizados, F-032), y si no cuadran es **409 antes de hablar con
  Sigrid y antes de dejar traza, también en dry-run**. Es lo que decide **qué
  reclamación se cierra en el ERP de producción**;
- un número guardado incompleto o sin tramos es **409 `CodigoNoConsta`** (H-4, decidido
  por el líder dentro de D-4);
- el botón «Reintentar el cierre» del front **vacía el autoguardado** antes de lanzar
  nada (H-2).

Contrato HTTP sin cambios; ninguna sentencia más contra la base; sin DDL.

## Qué respalda el cierre

- **Review 1 RECHAZADA** (`progress/review_F-034.md`): el código estaba bien, pero los
  tests de `/api/cerrar` no veían el login. **Review 2 APROBADA**
  (`progress/review2_F-034.md`) tras corregirlo solo con tests; la corrección destapó
  además que `/api/adjuntar` tenía el mismo agujero (M3), también tapado.
- `bash harness/init.sh` en verde, **3.246 tests**, cobertura **100 %** de 88 líneas;
  mutación **12/12**, reejecutada por el reviewer; y la regla nueva del reviewer
  (punto 7, puertas que protegen un orden): **23 de 24** mutaciones de orden en rojo, la
  restante sobre algo que no es un colaborador.

## Las dos verificaciones MANUAL

El humano, el 2026-09-23: **«dalo por cerrado»**.

- **V1 (T16)**: **cubierta por los tests**, opción que el reviewer respaldó en las dos
  reviews. La prueba del 409 por consola en el entorno desplegado no se ejecutó.
- **V2 (T17)**: **cerrada sin ejecutar**. No hay comparación de dry-runs antes/después
  del despliegue: no consta ninguna simulación contra el ERP para esta feature.

## Lo que queda

- **Desplegarla.** Hasta entonces sigue vivo el riesgo aceptado el 2026-09-23 (ventanas
  abiertas por defecto con adjuntar y cerrar fiándose del cuerpo). Al desplegar, el líder
  pone la nota «desde el despliegue de F-034» en `azure-apps/postventa_incidencias.md`
  (O-2 de la review 2).
- **H-5** (el cotejo no iguala `RS26.08 - 0123` con `RS26.08/0123`): lado seguro, sin 409
  falsos con los datos del circuito según el reviewer. No se toca.
- **H-6** (corregir un parte adjuntado esconde «Reintentar el cierre»): anterior a F-034,
  incómodo y no peligroso. Pendiente de decidir si merece ficha.
