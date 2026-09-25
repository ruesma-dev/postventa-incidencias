<!-- progress/explore_F-013.md -->
# F-013 · Medición del bloque 0 (T2 y T3) · 2026-09-24

Ejecutadas por el humano el 2026-09-24 con los scripts de solo lectura de T1
(`infra/23_destino_posventa.ps1` e `infra/24_ubicacion_sigrid.ps1`). **Nada se
creó, se subió ni se borró.** Aquí van sin identificadores (ni de sitio, ni de
biblioteca, ni de tenant) y sin nombres de persona: los nombres de carpeta y de
unidad que aparecen son de obra y de villa.

## T2 · La biblioteca de Posventa (obra piloto 0677)

| Qué | Medido |
|---|---|
| La aplicación ve el sitio `Postventa` | sí |
| Bibliotecas del sitio | **1**, «Documentos» (`/sites/Postventa/Documentos compartidos`), la de por defecto |
| Permisos del token | `Mail.ReadWrite` y `Sites.ReadWrite.All` (el amplio: F-018 tendrá que conceder este sitio) |
| Raíz de la biblioteca (D-1) | **52 carpetas** y 7 ficheros sueltos |
| Carpeta de obra que **casa** con la regla provisional | **0** |
| Carpeta de obra **parecida** | **1: `677  MIRASIERRA`** — **sin el cero** del código y con **dos espacios** |
| Dentro de la obra | 4 subcarpetas (`PARTES INCIDENCIAS` y otras tres de trabajo interno) y 2 ficheros sueltos |
| `PARTES INCIDENCIAS` | **existe y casa** |
| Unidades bajo `PARTES INCIDENCIAS` | **7: `VILLA 01` … `VILLA 07`** (siempre dos cifras) |
| `PARTES FIRMADOS` en cada unidad | **sí** en 01, 03, 05, 06 y 07 (con 0, 4, 2, 2 y 3 ficheros) |
| **VILLA 02** | tiene **una carpeta PARECIDA** a `PARTES FIRMADOS`, no igual (el script no la nombra; pendiente de que el humano diga su literal) |
| **VILLA 04** | **sin subcarpetas y 142 ficheros sueltos**: ahí los partes se guardan directamente en la unidad |
| Versionado de la biblioteca | no concluyente (el fichero mirado tiene 1 versión) |

**Defecto del script 23, a corregir al tocarlo**: la tabla resumen cuenta solo lo
que cuelga de una obra que **case**; como la 0677 solo era parecida, el resumen
sale con ceros (unidades 0, `PARTES INCIDENCIAS` 0…) aunque el árbol de arriba
muestra los datos. La medición es buena; el resumen engaña.

## T3 · Sigrid (obra 0677)

| Qué | Medido |
|---|---|
| Obras con ese código | **1**; código guardado `0677`, literal igual al pedido |
| `con.res` de la obra | `15 VIVIENDAS UNIFAMILIARES EN MIRASIERRA(MADRID)` |
| Unidades de posventa | **15**: `con.cod` `0677.03VILLA N.` y `con.res` `Viviendas Bloque Villa N`, con N = 1 … 15 **sin cero** |
| Nombres de persona en las unidades | **ninguno** |
| Reclamaciones en esas unidades | 1.197; **6 unidades sin ninguna** (8, 9, 10, 11, 14, 15) |

## Lo que la medición desmiente o precisa de `design.md` §4

1. **La obra no casa por el literal `<cod> <OBRA>`.** La carpeta real es
   `677  MIRASIERRA`: el código **sin cero** y un nombre corto que **no** es el
   `con.res` de Sigrid. La regla provisional la da por «parecida» → 409: con ella,
   **ningún parte de la 0677 se archivaría**.
2. **Las unidades casan por número**: Sigrid `Villa 5` ↔ Posventa `VILLA 05`. La
   regla de D-6 (números como enteros) se sostiene con los 7 casos.
3. **Faltan carpetas para 8 de las 15 villas** (8 a 15). Cinco no tienen
   reclamaciones, pero **VILLA 12 tiene 9 y VILLA 13 tiene 213**: sus partes
   obligarían a **crear** la unidad y su hoja.
4. **Dos grafías que la regla de parecidas pararía** (409, R35): la hoja parecida
   de VILLA 02 y la práctica de VILLA 04 (ficheros sueltos en la unidad).
5. **Nombre al crear**: ni el `con.res` de la obra ni el de la unidad se parecen
   a cómo nombra Posventa sus carpetas (`677  MIRASIERRA`, `VILLA 05`).

Estos cinco puntos van a la **parada T4**: los decide el humano.
