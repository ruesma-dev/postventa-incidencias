<!-- progress/cierre_F-031.md -->
# Acta de cierre · F-031, el nombrado sale de lo persistido · 2026-09-23

## Qué respalda el cierre

- **Review APROBADO** (`progress/review_F-031.md`), sin hallazgos bloqueantes.
- `bash harness/init.sh` en verde; **94 tests nuevos**; cobertura **100 %** de
  las 28 líneas de Python cambiadas; mutación **3/3 muertos**, con la línea base
  comprobada sin caché. El front (JavaScript) lo respaldan sus tests propios:
  310 en verde.
- **Mergeada en `dev`** (`bd8d577`) y **desplegada** el 2026-09-23: backend a
  las 11:01 UTC (despliegue `activo`, leído con `az`) y front con `-SoloFront`
  según el humano. `dev` y `main` publicadas e iguales.

## Las dos verificaciones MANUAL

Preguntado por V2 (archivar un parte normal y comprobar nombre y carpeta) y por
cómo cerrar V1 (recorrerla en local o dejarla como hueco), el humano respondió
el 2026-09-23: **«todo ok»**.

- **V2 (T15)**: dada por buena por el humano. **No consta** en el repositorio
  el nombre ni la carpeta obtenidos, ni el `hash` del parte usado. Una búsqueda
  de solo lectura en SharePoint, hecha antes de esa respuesta, no encontró
  ningún `PARTE FIRMADO` posterior al despliegue.
- **V1 (T14)**: dada por buena por el humano, sin detalle. Aviso para quien la
  repita: **el guion de `progress/impl_F-031.md` §8 ter tiene dos defectos**,
  detectados el 2026-09-23 por el líder:
  1. en local, `/api/archivar` responde 503 **antes** del cotejo
     (`archivar.py:151` construye el archivador como argumento), así que el
     409 de códigos no coincidentes **no se puede ver en local**;
  2. la línea de consola `api.archivar({ ...cuerpo, ... })` no funciona: `api`
     no es global (solo `window.Api`) y `cuerpo` no existe.
  Lo verificable en local es que, en la pestaña Red, el guardado termina
  **antes** de que salga `/api/archivar`.

## Lo que sigue

**F-034** (adjuntar y cerrar leen de lo persistido el estado de archivo y los
dos códigos), spec aprobada, y después **F-013**. Con las ventanas de escritura
abiertas por defecto desde el 2026-09-23, F-034 es la que cierra el riesgo
aceptado ese día.
