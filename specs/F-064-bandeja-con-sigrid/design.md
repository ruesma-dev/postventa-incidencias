<!-- specs/F-064-bandeja-con-sigrid/design.md -->
# F-064 · La bandeja enseña también las incidencias que ya están en Sigrid y los conflictos con lo importado — Diseño

> **La página** de la spec conjunta (Q-1, aprobada por el humano el
> 2026-10-21). El backend, sus criterios, el volumen, los datos personales y
> todas las decisiones (Q-1 a Q-10 y N-1 a N-3, **aprobadas por el humano el
> 2026-10-21**)
> están en **`specs/F-065-revision-sigrid-backend/design.md`**: no se
> repiten aquí. Este documento solo cubre `services/postventa-front`.
>
> Base: la de F-038 en `done` y F-065 mergeada. Documentos: `docs/ARCHITECTURE.md`
> («La página de revisión (F-038)» y el portal), `docs/CONVENTIONS.md`,
> `specs/F-038-bandeja-revision/`.

## 1 · Encaje

`bandeja.html` + `js/revision.js` (`appRevision`, F-038) + un módulo **puro
nuevo**, `js/sigrid_bandeja.js`, con su test de `node --test`. Una función
nueva en `js/api.js`. `revision.js` ya mide ≈ 1.450 líneas: la lógica nueva
va al módulo propio y el componente solo la orquesta. `cuerpoDeAccion` **no
cambia** (la única pieza que compone la confirmación de una acción).

## 2 · Cómo se ve (Q-7, aprobada el 2026-10-21)

```
┌ Resumen de la obra (F-038) ─────────────────────────────────────────────┐
├ Sigrid ─────────────────────────────────────────────────────────────────┤
│ 1.276 reclamaciones de la obra (SAT 40 · PTE 18 · TER 130 · CER 1.050…) │
│ 7 incidencias de la bandeja chocan con Sigrid · 12 con avisos           │
│ Leído a las 10:42 · [Volver a mirar Sigrid]  (o «Leyendo…», o el error) │
├ Ver: (•) Bandeja  ( ) Ya en Sigrid (1.276)  ( ) Conflictos (7) ─────────┤
│ Bandeja: las tarjetas de F-038, y en las que chocan:                    │
│   ⚠ Choca con RS26.09/0123 (Pendiente): misma unidad, oficio y …        │
│   · Ya hubo una igual, cerrada: RS26.03/0456 (Cerrada, mayo de 2026)    │
│   [Aprobar] → [Aprobar a pesar del conflicto]                           │
│ Ya en Sigrid: filtros (estado, fechas, unidad, oficio, tipo, persona,   │
│   teléfono, correo, texto, volcadas desde el portal, con hallazgo)      │
│   · «N de M» · lista de 100 en 100 · [Ficha] despliega lo que ya llegó  │
│ Conflictos: conflictos / avisos / todos · pares incidencia ↔ reclamación│
└─────────────────────────────────────────────────────────────────────────┘
```

- **Los filtros** (Q-2) se aplican en el navegador sobre las reclamaciones ya
  leídas (F-065 N-1: llegan todas en una respuesta); no piden nada. El texto,
  las personas y los correos se comparan plegados (sin tildes ni mayúsculas),
  como `plegar` del backend; los teléfonos, **solo por sus cifras**. Por
  omisión, todos los estados: el humano pidió verlas todas.
- **La ficha** (Q-6, N-3) **no se pide**: los datos personales llegan con cada
  reclamación (es lo que permite buscar por propietario o teléfono), y el botón
  solo despliega lo que ya está en memoria, con el aviso de datos personales.
- **El segundo clic** (Q-4): el estado `aprobarPendiente` guarda el
  `incidencia_id` del primer clic; cualquier otra cosa (otra fila, otra vista,
  recargar, cerrar el detalle) lo borra.

## 3 · Ficheros

| Ruta | Qué |
|---|---|
| **crear** `services/postventa-front/js/sigrid_bandeja.js` | Puro (R63): `presentarSigrid(respuesta, catalogo)`, `filtrarReclamaciones(lista, filtros)`, `filtrosVacios()`, `soloCifras(texto)`, `lineaDeHallazgo(hallazgo, reclamacionesPorCod)`, `etiquetaEstadoSigrid`, `textoDelPanel(estado, error)`, `necesitaSegundoClic(incidenciaId, hallazgosDeLaFila, pendiente)`, `paginaDeSigrid(lista, n)`, `paresDeConflicto(presentado, cargadas, severidad)`, `camposDeFicha(ficha)` |
| **crear** `services/postventa-front/tests_js/sigrid_bandeja.test.js` | R53–R61, R63, R67 |
| **crear** `services/postventa-front/tests/test_f064_front.py` | Guardas estáticas: el `<script>` del módulo, las vistas, ninguna ruta de escritura nueva, nada a `console` ni al almacenamiento, ningún `x-html` (R62, R65, R66, R67) |
| modificar `js/api.js` | `sigridDeLaBandeja(obra)` (R64) |
| modificar `js/revision.js` | En `appRevision`: estado `sigrid`, `vista`, `filtrosSigrid`, `aprobarPendiente`, `ficha`; `mirarSigrid()` lanzado a la vez que la primera página (R50); el paso por `necesitaSegundoClic` antes de aprobar (R58); la marca tras una acción (R59); desplegar la ficha de lo ya cargado (R60) y descartarlo todo al cambiar de obra (R61) |
| modificar `bandeja.html` | El panel, el selector, las vistas, los filtros, la ficha y las líneas por tarjeta, todo con `x-text` |
| modificar `tests_js/revision.test.js`, `tests_js/api.test.js` | R50–R52, R58, R59, R61, R64 |
| modificar `README.md` del front, `docs/ARCHITECTURE.md` (sección de F-038), `azure-apps/postventa_incidencias.md` | R68 |

**No se toca**: `importar.html`, `oficios.html`, `index.html`, `partes.html`,
`js/portal.js` (`Portal.SECCIONES` y `PAGINAS` no cambian), el backend,
`cuerpoDeAccion`.

## 4 · Riesgos

- **Datos personales en pantalla** (decisión del humano, Q-6): la página no
  los guarda ni los manda a la consola y los pinta como texto. Llegan con la
  lista entera de la obra (N-3): el riesgo de que estén a la vista de todo
  `posventa-usuarios` está anotado en F-065 §12 y lo asume el humano.
- **≈ 1.276 filas con sus fichas en el navegador**: filtrar y paginar en
  memoria es inmediato con ese tamaño; se pinta de 100 en 100. El peso de la
  respuesta lo mide T-A0 de F-065.
- **Mutantes del segundo clic**: es la pieza que protege la aprobación; tiene
  su familia propia en la campaña (T6).

## 5 · Lo que no hace

No escribe nada nuevo (las acciones son las de F-038); no bloquea la
aprobación (Q-4); no calcula conflictos (es F-065); no guarda nada en el
navegador; no toca el volcado (F-040).

## 6 · Decisiones

Todas en `specs/F-065-revision-sigrid-backend/design.md` §14: Q-1 a Q-10 y
N-1 a N-3, **aprobadas por el humano el 2026-10-21**.
Las que afectan a esta página: Q-2 (filtros en pantalla, R55), Q-4 (segundo
clic, R58), Q-6 (ficha con datos personales, R60–R62), Q-7 (vistas, R53–R57),
Q-8 (no releer tras una acción, R59), N-1 (todas de una vez, filtros en
memoria) y N-3 (los datos personales en la lista: filtros por persona,
teléfono y correo, R55; ficha sin petición, R60).
