<!-- progress/current.md -->
# Sesión activa

**F-002 · Ingesta y troceado de la remesa en partes** — estado `in_progress`,
rama `feature/F-002-ingesta-troceado`, rigor `critico`.

**Implementación TERMINADA.** Las 16 tareas de
`specs/F-002-ingesta-troceado/tasks.md` están marcadas (T15 es del humano) y
`bash harness/init.sh` termina en verde, exit 0. Informe completo con las
trazas de la fase RED y las evidencias: **`progress/impl_F-002.md`**.

**Revisión APROBADA** (2026-08-18): `progress/review_F-002.md`. El reviewer
recorrió `CHECKPOINTS.md` entero y verificó por su cuenta —sin fiarse del
informe— el portero, las dos suites, la cobertura recalculada a mano, el
alcance y el número de mutantes, y **reejecutó la campaña de mutación completa**
(44 evaluados, 44 muertos, 0 supervivientes en 29,7 s). Comprobó también contra
el historial de git que en los commits RED estaba el test y **no** el módulo de
producción.

Pendiente para cerrar: **solo la verificación MANUAL de abajo (T15)**, que es
del humano. La feature **no se marca `done`** hasta que se ejecute y se anote
aquí su resultado real. Nada depende ya del implementer.

## Números de esta implementación

- 104 tests en verde (94 del servicio —87 de F-002— y 10 del arnés).
- Cobertura de las líneas cambiadas: **100 %** (273/273, umbral 80 %).
- Mutación: **44 mutantes, 44 muertos, 0 supervivientes**
  (`progress/mutacion_F-002.md`).
- `ruff`: 32 avisos, la deuda previa exacta. Cero avisos nuevos.

## Lo que el humano decidió al aprobar (respetado)

1. **Degradación aceptada.** Las remesas reales llegan escaneadas sin capa de
   texto, así que la regla del pie no se dispara y el troceado es «una página,
   un parte». Queda declarado en el campo `modo_deteccion` de cada parte.
2. **Recuperación planificada: `F-014`** (prioridad 14, `blocked_by` F-003).
3. **F-002 no prepara F-014**: no se ha dejado ni un gancho, ni una bandera,
   ni código muerto. Solo `origen` y `paginas_origen` con precisión suficiente
   —qué fichero y qué páginas suyas— para reagrupar después sin reabrir la
   remesa.

## Riesgo 4 del diseño: comprobado y descartado

`design.md` §7 mandaba parar si `extraer_paginas` no conservara el contenido
de la página. **No pasa**: la página extraída da la misma huella que en la
remesa de origen, con capa de texto y escaneada. R14 se cumple. No hubo que
bloquear nada.

## PENDIENTE · verificación MANUAL (humano)

`tasks.md` T15 — acierto del troceado sobre la **remesa real de Mirasierra**
(criterio `acceptance` 2). No se puede automatizar: el PDF
`docs/referencia/doc02871320260817093833.pdf` no se versiona (datos
personales) y tiene que estar en el árbol de quien lo ejecute.

```bash
cd services/postventa-api && .venv/Scripts/python.exe -c "
from pathlib import Path
from domain.models.remesa import DocumentoEntrada
from interface_adapters.api.split import trocear_remesa
ruta = Path('../../docs/referencia/doc02871320260817093833.pdf')
res = trocear_remesa([DocumentoEntrada(nombre=ruta.name, contenido=ruta.read_bytes())])
print('partes:', res['total_partes'])
print('modos:', sorted({p['modo_deteccion'] for p in res['partes']}))
print('hashes distintos:', len({p['hash'] for p in res['partes']}))
print('paginas por parte:', [len(p['paginas_origen']) for p in res['partes']])
print('avisos:', res['avisos'])
"
```

**Esperado**: `partes: 22`, `modos: ['una_pagina_por_parte']`,
`hashes distintos: 22`, `paginas por parte: [1] * 22`, `avisos: []`.
Solo imprime recuentos: ningún dato personal sale por pantalla y no escribe
nada en disco. **Resultado real: PENDIENTE de ejecutar por el humano** — se
anota aquí cuando se ejecute.

## AVISO · trabajo de otra sesión colado en esta rama

El commit `3211984` («F-002 T11: …») arrastró, además de sus tests, ficheros
que no son de F-002: `specs/F-003-extraccion/` (los tres documentos),
`progress/spec_F-003.md`, `BACKLOG.md` y el estado de F-003 en
`harness/features.json`. Otra sesión los tenía preparados en el índice de git
y el commit se los llevó por delante.

**No se han tocado**: sacarlos de la rama podría destruir ese trabajo, y esa
decisión es del líder o del humano. No afecta a nada de lo verificado en
F-002.

## Contexto de la sesión

- Agentes del arnés (`spec-author`, `implementer`, `reviewer`) **cargados**.
- Arnés **1.5.0**.
- Hallazgos de dominio que mandan sobre el diseño, en `docs/ARCHITECTURE.md` y
  `docs/referencia/`: «Cerrar parte» de Sigrid **exige documento adjunto**, y
  un parte firmado con observaciones manuscritas **no** es un parte conforme.
