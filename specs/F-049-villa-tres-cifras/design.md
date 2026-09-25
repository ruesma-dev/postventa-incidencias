<!-- specs/F-049-villa-tres-cifras/design.md -->
# F-049 · Las villas que crea el archivo, siempre con tres cifras — Diseño

> Feature de una regla. El diseño de fondo es el de F-013 (`design.md` §4.6),
> enmendado el 2026-09-25; aquí va solo lo que cambia.

## 1 · Ficheros

### 1.1 A crear

| Fichero | Qué |
|---|---|
| `specs/F-049-villa-tres-cifras/{requirements,design,tasks}.md` | esta spec |
| `services/postventa-api/tests/test_f049_villa_tres_cifras.py` | R1–R4 |

### 1.2 A modificar

| Fichero | Qué cambia |
|---|---|
| `services/postventa-api/domain/models/destino_posventa.py` | `nombre_derivado_de_unidad`: `:02d` → `:03d`, y sus docstrings |
| `services/postventa-api/infrastructure/sharepoint/graph.py`, `domain/ports/biblioteca.py`, `application/pipelines/destino_archivo.py`, `config/settings.py` | **solo** si algún comentario fija el ancho del nombre creado |
| Tests de F-013 que **fijan el ancho** del nombre creado | la expectativa pasa a tres cifras; la lista exacta va al informe (`progress/impl_F-049.md`) |
| `specs/F-013-archivo-posventa/{requirements,design,tasks}.md` | recuadros fechados (R4) |
| `docs/INTEGRACION.md` §3, `docs/DESPLIEGUE.md` §9 | recuadros fechados (R4) |
| `azure-apps/postventa_incidencias.md` (repositorio aparte) | el gemelo de INTEGRACION §3, commit local allí |

### 1.3 Lo que NO se toca

- `_casa_con_la_unidad`, `parecidas_de_unidad`, `clave_de_unidad`,
  `PATRON_CODIGO_UNIDAD`: el casado por número entero ya reconoce `VILLA 001`.
- Los **datos medidos** de los tests de F-013 (`UNIDADES_EN_POSVENTA`,
  `HOJAS_EN_POSVENTA`, `arbol_0677`…): son la foto de T2 del 2026-09-24, con
  dos cifras porque así estaban entonces. La biblioteca reorganizada entra
  como dato **nuevo** en los tests de F-049.
- `infra/00_vars_postventa.ps1` y el resto de `infra/`: el script 23 ejecuta
  la regla del dominio (F-013 T14), así que dice «crearía `VILLA 008`» sin
  tocarlo.
- Los tests de F-006, F-019, F-031…F-034.

## 2 · La regla

```python
def nombre_derivado_de_unidad(unidad_codigo, *, codigo_obra) -> str | None:
    ...
    return f"VILLA {int(encaje['n']):03d}"
```

`:03d` rellena hasta tres cifras y deja intacto lo que ya tiene más: `1` →
`001`, `100` → `100`, `1000` → `1000`. El `int()` quita los ceros que traiga
el `con.cod`.

## 3 · Por qué el casado no cambia

`clave_de_unidad` pasa cada token numérico por `str(int(t))`: la clave de
`VILLA 008` es `(VILLA, 8)`, igual que la de `VILLA 08` y la del `con.res`
`Viviendas Bloque Villa 8`. La regla estricta (sufijo de la clave del nombre,
F-013 §4.3) y la amplia (números enteros, §4.5) no ven la diferencia.
Consecuencia, y es la correcta: `VILLA 01` y `VILLA 001` en la misma carpeta
son **dos** candidatas de la villa 1 → `unidad_ambigua`.

## 4 · Riesgos y alternativas descartadas

- **Rellenar según las hermanas** («el ancho que usen las demás carpetas de
  la obra»): queda fuera al elegir el humano «siempre con tres cifras».
  Además dependería del listado, y una obra sin unidades no tendría ancho.
- **Seguir con dos cifras**: queda fuera por lo mismo; la biblioteca real de
  la obra piloto ya está en tres.
- **Riesgo**: otra obra de Posventa que siga con dos cifras recibiría `VILLA
  008` junto a `VILLA 07`. No bloquea (números distintos) y es la decisión del
  humano: «siempre con tres cifras». Lo vería Posventa en la comprobación de
  F-013 R42.
