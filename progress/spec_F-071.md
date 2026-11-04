<!-- progress/spec_F-071.md -->
# Spec de F-071 · resumen del spec-author (2026-11-04)

Escrita en el worktree `postventa-f071`, rama
`feature/F-071-plantilla-desde-sigrid` (desde `feature/F-040-volcado-sigrid`
en `d50fe9d`). Carpeta: `specs/F-071-plantilla-desde-sigrid/`
(`requirements.md`, `design.md`, `tasks.md`). **Pendiente de aprobación del
humano.** F-071 dada de alta en `harness/features.json` (`spec_ready`,
prioridad 1, rigor `critico`) y `BACKLOG.md` regenerado. No se ha consultado
Sigrid ni escrito nada fuera del worktree.

## Qué propone, en corto

- **Unidad, Ubicación, Oficio y Proveedor salen de Sigrid** al descargar
  la plantilla; **Urgencia y Listado no pueden**: Sigrid no tiene catálogo de
  urgencias (`rcp.texurg` es texto libre) y el tipo de reclamación
  (`auxtrcp`) no lo usa la bandeja (el volcado manda siempre `0002`). Se
  quedan en el YAML (Q-2, Q-3).
- **Ubicación dependiente de la unidad de la fila** (desplegable con
  `INDIRECT` y rangos con nombre por lista; lo que diseñó F-058, que el humano
  ya aprobó y nunca se implementó). Fuera «General» y «Otra». Antes de escribir
  código, 15 minutos de prueba manual con los prototipos que F-058 dejó en
  `C:\Users\pgris\Downloads\f058_prototipos\` (Q-1).
- **Oficio: una entrada por código, sin grupos de equivalencia**, con la
  etiqueta `Nombre (código)`. **Proveedor: una entrada por fila de `obrofc`**,
  `Nombre oficio (código) · Nombre proveedor (código)`. Lo elegido entra en la
  bandeja con su código: **ninguna fila nueva sale `oficio_ambiguo`**.
- **La importación lee Sigrid en ese momento** (catálogo y ubicaciones), valida
  la ubicación contra la unidad de su fila, acepta lo tecleado con otra
  mayúscula si casa con una sola opción (regla de F-060) y devuelve lo que ya
  no está en Sigrid en el Excel de errores, que sale con las listas de hoy.
- **Versión 2**; una plantilla v1 se rechaza entera con un motivo claro.
- La plantilla deja de leer PostgreSQL. Ni DDL, ni consulta nueva, ni
  endpoint, ni cambios en el front, la revisión, el volcado ni `sigrid-api`.
- **47 requisitos**, **20 tareas** en 6 bloques (Bloque 0 manual; RED antes de
  GREEN; mutación por bloque; despliegue y verificación en la 0677 MANUAL).

## Preguntas para el humano (con la recomendación)

**Q-1 · La prueba del desplegable dependiente (D-1).** El de `Ubicación`
depende de una fórmula `INDIRECT` en la validación de datos. F-058 dejó dos
prototipos con datos ficticios en `C:\Users\pgris\Downloads\f058_prototipos\`
y su guía de 9 puntos; la prueba **nunca se hizo**. ¿La haces ahora en Excel
de escritorio y Excel web (unos 15 minutos)?
*Recomendación:* **sí, antes del Bloque 1.** Es la única pieza con riesgo
técnico; si falla con las dos variantes, la alternativa es la (c)
—desplegable con todas las ubicaciones de la obra y validación por unidad solo
al importar—, que no cumple del todo tu petición y te la volvería a enseñar.

**Q-2 · Urgencia.** En Sigrid no hay tabla de urgencias: `rcp.texurg` es un
texto libre de 32 caracteres, la pasarela no lo admite al crear el parte y el
volcado no lo manda (D-10 de F-059). ¿Aceptas que «Urgente» y «Peligro para
la seguridad» sigan en el YAML?
*Recomendación:* **sí.** Si quieres saber si Posventa escribe ahí unos valores
fijos, la medición de solo lectura es
`SELECT LTRIM(RTRIM(texurg)) AS urgencia, COUNT(*) AS n FROM dbo.rcp GROUP BY LTRIM(RTRIM(texurg)) ORDER BY n DESC`
(la lanzas tú; no la he ejecutado). Mandar la urgencia a Sigrid sería otra
ficha con un cambio en `sigrid-api`.

**Q-3 · Listado → tipo de reclamación.** En Sigrid sí hay tabla: `auxtrcp`
(«Tipos de reclamación»; `0002` es PRIMER LISTADO POSTVENTA). Pero hoy el
`listado` del Excel **no llega a Sigrid**: el volcado manda siempre `0002`
(tu Q-1 de F-059). Ofrecer `auxtrcp` en la plantilla solo tiene sentido si la
bandeja lo guarda por código y el volcado lo manda, y eso toca DDL, la
revisión, la página de la bandeja y F-040, que está a medias.
*Recomendación:* **ficha aparte** («El tipo de reclamación sale de `auxtrcp`
de punta a punta: plantilla, bandeja, revisión y volcado»), detrás de F-040;
F-071 deja `Listado` como está. Medición de solo lectura si quieres verla:
`SELECT cod, res, pos, fecbaj FROM dbo.auxtrcp ORDER BY pos, cod`.

**Q-4 · Plantillas v1 en la calle (D-4).** En F-058 decidiste aceptar solo
la versión nueva. Con F-071 hay un motivo más: las etiquetas de oficio de la
v1 («Pintura») no casan con las de la v2 («Pintura (0039)»). ¿Hay ahora mismo
alguna v1 de la 0677 u otra obra rellenándose?
*Recomendación:* **rechazar la v1** con el motivo «descarga una nueva y copia
tus filas». Si hay alguna a medio rellenar, avisar a quien la tenga en cuanto
se publique.

**Q-5 · Etiquetas con código (D-11, D-12).** ¿Oficio como `Nombre (código)`
siempre, y proveedor como `Nombre oficio (código) · Nombre proveedor
(código)`?
*Recomendación:* **sí, siempre con código.** Los oficios casi iguales de
Sigrid se ven los dos y se distinguen; la etiqueta no cambia si entra otro
oficio con el mismo nombre entre la descarga y la importación; y es lo que
Posventa ve en Sigrid. Coste: etiquetas largas en la celda.

**Q-6 · Las equivalencias de oficio (D-14).** La plantilla y la importación
dejan de agrupar oficios (R86 y R92 de F-036). La tabla de decisiones, la
página `oficios.html` y sus dos rutas **se quedan** sin cambios (la revisión
aún las usa para enseñar las filas viejas ambiguas).
*Recomendación:* **dejarlas** en esta ficha. Si ya no sirven para nada más,
retirarlas es otra ficha pequeña cuando las filas viejas ambiguas estén
resueltas.

**Q-7 · Mayúsculas en las demás columnas (D-17).** Excel acepta lo tecleado
sin mirar mayúsculas («vivienda 3» por «Vivienda 3»), y hoy la importación lo
rechaza (comparación exacta, decisión 7 de F-036). ¿Aplicamos a Unidad,
Oficio, Proveedor, Urgencia y Listado la misma regla que F-060 aplica a la
ubicación —si casa con **una sola** opción salvo mayúsculas, se toma esa, con
aviso—?
*Recomendación:* **sí**: es la misma regla, no una nueva, y evita devolver lo
que el Excel dio por bueno.

**Q-8 · Lo que no está en la tipología.** Sin «General» ni «Otra», si el sitio
real no está en la lista de la unidad (p. ej. «Escalera» en una villa cuya
tipología no la tiene), la ubicación va en blanco y se explica en «Detalle»;
la bandeja la pedirá al aprobar.
*Recomendación:* **así**, y que Posventa dé de alta en Sigrid (en su UI, nunca
desde este proyecto) las ubicaciones que falten en cada tipología; la
plantilla las ofrecerá en la siguiente descarga.

**Q-9 · El script de migración de F-036 (D-6).** Usa la lista del YAML y los
grupos que desaparecen.
*Recomendación:* **retirarlo** con sus tests (≈150), con constancia en
`docs/ARCHITECTURE.md`. Si alguna otra obra necesitará migrar un Excel
antiguo, dímelo y se congela en vez de borrarse.

**Q-10 · Verificación en producción (T16).** En F-058 autorizaste una
importación de prueba que solo escribía una fila en `postventa.importaciones`.
La de F-071 escribe además **una incidencia** de prueba («PRUEBA F-071 -
DESCARTAR») en la bandeja de la 0677, que luego descartas tú. Nada en Sigrid.
¿La autorizas?
*Recomendación:* **sí**: es la única forma de ver en producción que lo elegido
entra sin `oficio_ambiguo`. Alternativa: verificar solo la descarga (pasos 1 y
2 de T16).

**Q-11 · F-058 (D-20).** F-071 la absorbe entera.
*Recomendación:* **cerrarla como absorbida por F-071** (el líder cambia su
ficha) y retirar el worktree `postventa-f058` cuando F-071 esté aprobada; su
rama se conserva como archivo.

**Q-12 · Lo ya importado.** Las filas de la 0677 que ya están en la bandeja con
`oficio_ambiguo` o con ubicación fuera de lista **no cambian**: se resuelven
en la bandeja como hoy.
*Recomendación:* **así** (D-18). Si prefieres borrarlas y reimportarlas con la
plantilla nueva, es una decisión de datos tuya, fuera de esta ficha.

**Q-13 · Base de la rama y F-040 (para el líder y el humano).** La rama sale de
F-040 (`d50fe9d`), que está `in_progress`; F-071 no usa nada de F-040. Solo
puede haber una feature `in_progress`.
*Recomendación:* **aparcar F-040** (`blocked`, sin fallo) mientras dura F-071,
por la urgencia, y **llevar la rama de F-071 a `dev`** antes del Bloque 1 para
poder mergearla y publicarla sin arrastrar F-040 a medias.

## Para el líder

- La spec cita a F-058 por `git show` de su rama; no hace falta traer nada.
- `progress/impl_F-058.md` (rama de F-058) tiene la guía de la prueba de T0.
- `azure-apps/postventa_incidencias.md` es del líder al desplegar (T15).
- Si el humano aprueba Q-3 (ficha aparte), darla de alta; y anotar en F-058 que
  queda absorbida (Q-11).
