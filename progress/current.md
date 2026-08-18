<!-- progress/current.md -->
# Sesión activa

**F-002 · Ingesta y troceado de la remesa en partes** — estado `spec_ready`,
rama `feature/F-002-ingesta-troceado` (creada desde `dev` con el arnés 1.5.0
ya mergeado).

**Esperando aprobación humana de la spec.** Nadie implementa hasta que el
humano la apruebe y la feature pase a `in_progress`.

- Spec: `specs/F-002-ingesta-troceado/` (19 requisitos EARS con test trazable,
  diseño por capas, 16 tareas con RED antes que implementación).
- Decisiones y dudas del spec-author: `progress/spec_F-002.md`.

## Lo que el humano tiene que decidir antes de implementar

1. **El parte de dos hojas no se detectará en producción mientras las remesas
   lleguen sin OCR.** Comprobado en solo lectura sobre la remesa real de
   Mirasierra: 22 páginas, **0 caracteres de capa de texto**, una imagen por
   página. La regla del pie («Página 2») solo dispara con PDFs que traigan
   texto. La spec asume aceptar la degradación en v1, declarándola en el campo
   `modo_deteccion` de cada parte; la alternativa buena es reagrupar en F-003,
   que ya pasa cada página por un modelo multimodal.
2. **El criterio `acceptance` 2 de F-002 se contradice con
   `docs/referencia/02_parte_de_trabajo.md`**: dice «22 páginas = 22 partes,
   con su parte de dos hojas», pero en Mirasierra las 22 páginas numeran
   «Página 1» y no hay ningún parte de dos hojas. La spec lo resuelve con
   recuento MANUAL sobre Mirasierra (T15) y el parte de dos hojas cubierto por
   tests sintéticos (T9). Si la intención era otra, hay que decirlo antes.
3. **`/split` devuelve cada parte en base64** (no hay persistencia hasta
   F-005): +33 % de tamaño de respuesta. Aceptable para el piloto, conviene
   confirmarlo.

## Compromiso heredado de F-001 (sigue vigente)

F-002 empieza por los tests, con la traza en rojo pegada en el informe de
implementación. El rigor declarado es `critico`: cobertura, campaña de
mutación y cero supervivientes sin justificación aceptada.

## Contexto de la sesión

- Sesión con los agentes del arnés (`spec-author`, `implementer`, `reviewer`)
  **cargados y disponibles**: la spec la redactó el subagente `spec-author`,
  no el líder.
- Arnés actualizado a **1.5.0** en esta misma sesión (merge `f5328f2` en
  `dev`): `BACKLOG.md` se genera desde `features.json` y `init.sh` lo regenera
  en cada arranque.
- Hallazgos de dominio que mandan sobre el diseño, en `docs/ARCHITECTURE.md` y
  `docs/referencia/`: «Cerrar parte» de Sigrid **exige documento adjunto**, y
  un parte firmado con observaciones manuscritas **no** es un parte conforme.
