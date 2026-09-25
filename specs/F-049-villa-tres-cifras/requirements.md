<!-- specs/F-049-villa-tres-cifras/requirements.md -->
# F-049 · Las villas que crea el archivo, siempre con tres cifras — Requisitos

> Notación EARS (`specs/SPECS.md`). Cada requisito se traduce a **al menos un
> test trazable** `test_f049_rN_*`. Rigor **`critico`**, el de F-013, de la que
> esta feature es una enmienda: fase RED obligatoria, cobertura del 100 % de
> lo cambiado y campaña de mutación con cada superviviente explicado.
>
> Es una feature **de una regla**. El detalle vive en las enmiendas fechadas
> del 2026-09-25 de `specs/F-013-archivo-posventa/` (`requirements.md` R37,
> T4-1, T4-5, el vocabulario, R31 y R42; `design.md` §1, §4.5, §4.6, §7.1 y
> §7.3; `tasks.md`, «Después del merge»). Aquí solo se fija qué cambia y
> cómo se comprueba.

## Por qué

En el **paso 2 del corte de F-013** (2026-09-25), el script 23 contra la
biblioteca real mostró que Posventa ha **reorganizado** sus carpetas de unidad
de la obra piloto: ya no son `VILLA 01` … `VILLA 07` (lo medido en T2 el
2026-09-24), sino **`VILLA 001` … `VILLA 007`, `VILLA 012` y `VILLA 013`**.
F-013 R37 crea la unidad que falta con **al menos dos cifras** (`VILLA 08`),
así que las carpetas que creara el sistema no se parecerían a las de Posventa.

**Decisión del humano (2026-09-25)**: «**Siempre con tres cifras**». `VILLA
008`, `VILLA 013`, en todas las obras; con 1.000 o más, tal cual (`VILLA
1000`).

## Alcance

**Entra**: el ancho del número en el **nombre que se crea**
(`domain/models/destino_posventa.py::nombre_derivado_de_unidad`) y la
documentación que lo describe.

**No entra**, a propósito:

- **Cómo se casa.** La regla estricta y la amplia de la unidad (F-013 §4.3 y
  §4.5) comparan **números enteros**: `VILLA 001`, `VILLA 01` y `VILLA 1` son
  la misma villa 1 desde F-013. No se toca ni una línea de ellas.
- **El patrón del `con.cod`** (`PATRON_CODIGO_UNIDAD`), la obra (R36), los
  tramos fijos y la hoja alternativa (R49).
- **Las carpetas que ya existen.** Ni se renombran ni se mueven (F-013 R43).
- **`infra/00_vars_postventa.ps1`**: el corte lo prepara el líder aparte.

## Requisitos

**R1.** El nombre derivado de una unidad (F-013 R37) debe ser `VILLA `
seguido de `<n>` como entero con **al menos tres cifras**: `0677.03VILLA 8.`
→ `VILLA 008`; `0677.03VILLA 13.` → `VILLA 013`; `0677.03VILLA 100.` →
`VILLA 100`; `0677.03VILLA 1000.` → `VILLA 1000`. Los ceros a la izquierda de
`<n>` en el `con.cod` no cuentan (`0677.03VILLA 008.` → `VILLA 008`). Lo que
no cumple el patrón sigue siendo `None` (F-013 R37, sin cambios).

**R2.** El casado **no cambia**: `VILLA 001`, `VILLA 01` y `VILLA 1` casan con
la villa 1 de Sigrid, y con ninguna otra (ni la 10 ni la 100). Con la
biblioteca reorganizada que midió el script 23 el 2026-09-25 (`VILLA 001` …
`VILLA 007`, `VILLA 012`, `VILLA 013`), las unidades 1–7, 12 y 13 **casan**
con su carpeta existente y las 8–11, 14 y 15 **se crean** con tres cifras,
sin ninguna parecida que lo impida. SI conviven `VILLA 01` y `VILLA 001`,
ENTONCES la unidad 1 es `unidad_ambigua` (409, F-013 R14): el sistema no
elige.

**R3.** Lo creado con tres cifras **casa consigo mismo y solo con su unidad**
(F-013 R39, R46 y R50): para cada una de las 15 unidades de la 0677, la
carpeta `VILLA 0NN` casa con esa unidad y con ninguna otra, no es parecida de
ella, pasa F-013 R38, y una segunda resolución la encuentra sin crear nada.

**R4.** La documentación que decía «dos cifras» lleva un **recuadro fechado
el 2026-09-25 (F-049)** que **cita literal** la premisa enmendada, sin
borrarla: F-013 `requirements.md` (R37, T4-1, T4-5, el vocabulario, R31 y
R42), `design.md` (§4.6 con el código, §4.5 y §7.3), `tasks.md` («Después del
merge», paso 2), `docs/INTEGRACION.md` §3 y `docs/DESPLIEGUE.md` §9, donde la
salida esperada de R31 pasa a ser «crearía `VILLA 008` …».
