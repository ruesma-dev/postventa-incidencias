<!-- progress/spec_F-064.md -->
# Spec de F-064 (y F-065) · informe del spec-author (2026-10-21)

Worktree `postventa-f064`, rama `feature/F-064-bandeja-con-sigrid`, base `dev`
`383bfd5`. No se ha ejecutado nada contra Sigrid ni contra la base, ni
`init.sh` ni pytest (P-4). No se ha tocado `harness/features.json` ni
`progress/current.md` (este último lo edita el árbol principal con F-038 en
curso: el líder anota allí la spec al recogerla).

## Dónde está

| Ficha | Carpeta | Requisitos |
|---|---|---|
| **F-065** · backend (tramo A) | `specs/F-065-revision-sigrid-backend/` | R1–R40 (R7 retirado) |
| **F-064** · la página (tramo B) | `specs/F-064-bandeja-con-sigrid/` | R50–R69 |

Orden: F-038 → F-065 → F-064 → F-040. Todas las decisiones, en
`specs/F-065-revision-sigrid-backend/design.md` §14.

## Primera versión (2026-10-21, mañana)

Spec conjunta con las Q-1 a Q-10 como propuestas (commit `1b2d839`). La
sustituye la versión de abajo.

## Decisiones del humano · 2026-10-21

Todas marcadas en la spec «Aprobada por el humano el 2026-10-21».

| Q | Decisión | Qué cambió en la spec |
|---|---|---|
| Q-1 | Partición como se recomendaba: backend **F-065** (`revision-sigrid-backend`), página **F-064** | Tramo A movido a `specs/F-065-revision-sigrid-backend/` conservando R1–R31; referencias cruzadas |
| Q-2 | **Todas** las reclamaciones de la obra, cualquier estado y fecha, con **filtros en pantalla**; la 0677 tiene ≈ 1.276, el techo de 1.000 no vale | R5 sin filtro de estado ni fecha; R7 retirado (sin fecha de corte); R8 con techo 20.000 (N-1); reincidencias de cualquier fecha; F-064 R54–R55 con los filtros (estado, fechas, unidad, oficio, tipo, texto, volcadas, con hallazgo); script 29 mide filas, bytes y segundos |
| Q-3 | Los dos del humano + **misma unidad y descripción parecida**; `PVI-` y avisos de coherencia como se proponían | R15 pasa de «misma descripción» a «descripción parecida» con la regla de R36 (N-2); ejemplos E2b–E2d |
| Q-4 | No bloquea: aviso + segundo clic | Sin cambios (R26, F-064 R58) |
| Q-5, Q-7, Q-8, Q-9, Q-10 | Como se recomendaban | Sin cambios |
| Q-6 | Los datos personales **sí** se enseñan en la página; nunca en logs ni trazas, ni en el repositorio/specs/progress/tests con valores reales, ni en nuestra base | Ruta nueva de **ficha** (R32–R35) con lista cerrada de campos; R37–R40 (no se guardan, no van a logs, datos de prueba inventados, errores sin filas); `Cache-Control: no-store`; F-064 R60–R62, R66–R67; riesgo anotado en F-065 §12 como decisión del humano |

## Propuestas nuevas que derivan de esas decisiones (tal como se enseñaron)

Las tres son de diseño y el humano no las ha visto: la PARADA 1 cubre lo
enseñado, así que quedan marcadas «pendiente de OK» en la spec
(`specs/F-065-revision-sigrid-backend/design.md` §14.2). No bloquean el Bloque
A1 (el script de medición), sí el A2.

- **N-1 · Volumen.** Una sola lectura con **techo propio de 20.000** filas,
  sin cursor en la ruta: el cruce necesita todas las reclamaciones de la obra a
  la vez, y un cursor obligaría a releer Sigrid entera por página o a una
  caché. ≈ 1.276 filas de columnas cortas son del orden de 300 KB. Paginar la
  lectura con `OFFSET … FETCH` solo si T-A0 mide más de ≈ 10 s. Descartado
  usar el tope de la pasarela (500.000) a pelo: el proxy de 45 s caería antes
  que un 409 claro.
- **N-2 · «Descripción parecida».** Jaccard sobre palabras significativas
  (plegadas, sin vacías ni de < 3 letras, plural simple), **umbral 50 y al
  menos 2 palabras en común**; constante del dominio, ajustable con T-A0 (que
  cuenta pares con 40/50/60 dentro de Sigrid).
- **N-3 · Ficha bajo demanda.** Los datos personales y textos largos no van en
  el listado sino en `GET /api/revision/sigrid/reclamacion`, que la página pide
  al pulsar «Ver ficha de Sigrid», con una **lista cerrada** de campos que deja
  fuera DNI, credenciales de i-Sigrid (`per.esiglog`/`esigpas`/`clamai`, que
  existen en la tabla `per`), direcciones y observaciones de la persona.

## Respuestas del humano a N-1 a N-3 · 2026-10-21

Marcadas en `specs/F-065-revision-sigrid-backend/design.md` §14.2 «Aprobado por
el humano el 2026-10-21». **La spec de F-065 y la de F-064 quedan aprobadas.**

| N | Decisión | Qué cambió |
|---|---|---|
| N-1 | Una sola lectura **con el techo de la pasarela, 500.000** (no 20.000), comprobando `truncated` y el corte de 230 s; si T-A0 mide más de ≈ 10 s, por trozos | R8 y R20 (`tope: 500000`); el adaptador compone su propia lectura (un `truncated` es 409, no el 503 de F-036); T-A0 mide segundos y bytes |
| N-2 | Aprobada como se proponía (Jaccard, umbral 50, ≥ 2 en común), ajustable con T-A0 | Ninguno |
| N-3 | **Todo en el listado, una sola ruta**; la ficha bajo demanda desaparece | R6, R20 y R33: los campos personales de la lista cerrada viajan en cada reclamación (`ficha`); R32 y R34 retirados; una sola consulta de 31 columnas; siguen fuera el DNI y las credenciales de i-Sigrid. F-064: filtros por **persona, teléfono (solo cifras) y correo** y texto también en la descripción larga (R55); la ficha se despliega sin petición (R60); una sola función en `api.js` (R64). T-A0 mide los bytes de la 0677 con esos campos. Riesgo (la agenda de la obra entera en cada carga, visible a `posventa-usuarios`) anotado en F-065 §12 como decisión del humano |

## Lo que queda para el líder

- Dar de alta F-065 en `features.json` (rigor `critico`, bloquea a F-064).
- Anotar en `progress/current.md` la spec aprobada y T-A0.
- T-A0 (Bloque A1 de F-065, solo lectura) puede mover el umbral de N-2, la
  columna de fecha o activar la lectura por trozos de N-1: si lo hace, se
  enmienda la spec antes del Bloque A2.
