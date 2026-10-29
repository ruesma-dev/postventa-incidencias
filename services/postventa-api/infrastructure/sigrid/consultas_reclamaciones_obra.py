# services/postventa-api/infrastructure/sigrid/consultas_reclamaciones_obra.py
"""El SQL de las **reclamaciones de la obra**: texto, parámetros y mapeo (F-065).

Módulo **puro**, como `consultas_catalogo.py` (F-036) y
`consultas_ubicaciones_validas.py` (F-056), que no se tocan, y por el mismo
motivo: el SQL se comprueba carácter a carácter en un test unitario, no contra
el ERP de producción. Aquí no hay `httpx`, no hay red y no se escribe nada.

**Ningún valor se interpola en el texto**: el campo `RCPCLI`, el patrón
`PVI-%`, el tipo y la obra viajan como marcadores `?`
(`azure-apps/sigrid_api.md` §5.2; R5).

## La consulta (`specs/F-065-revision-sigrid-backend/design.md` §3)

`SQL_RECLAMACIONES_DE_LA_OBRA` — **todas** las reclamaciones del tipo pedido
cuya unidad de posventa es de una obra con ese código, de cualquier estado y
fecha (Q-2), con las columnas de R6 y la lista cerrada de R33: treinta y una.
Parte de `rcp` y sube a la obra por la UPV, con **el mismo filtro de obra**
que `SQL_UNIDADES_DE_LA_OBRA`. La referencia `PVI-`, con un `OUTER APPLY …
TOP 1` (un `LEFT JOIN` duplicaría la reclamación con dos `RCPCLI`). Es **el
mismo texto** que mide `infra/29_reclamaciones_obra_sigrid.ps1` (R29), y un
test lo compara con los dos.

La medición T-A0 (2026-10-28, solo recuentos): 1.345 filas y menos de 1 s en
la obra piloto, sin `truncated`; de ahí que no se lea por trozos (N-1).

## La consulta de la guarda del ensayo (§15.5, R44)

`SQL_RECLAMACIONES_DE_LAS_UNIDADES` — la misma lectura **solo de las unidades
de lo que se va a mandar** y **sin** la lista de R33: las doce primeras
columnas de R6, sin las cuatro uniones que solo sirven a R33 (`auxrcp`, el
cliente y las dos personas). Es una **plantilla**: `__MARCADORES__` se cambia
por tantos `?` como unidades (de 1 a 50, una sola vez cada una), y las
unidades viajan como parámetros, tal cual y en el orden recibido. La misma
plantilla la usa `infra/29_reclamaciones_obra_sigrid.ps1 -Unidades` (R70).

## El mapeo (§10.2, enmienda del 2026-10-28)

- `obra_ref` y `cod`, obligatorios; lo demás puede ser `NULL`.
- **Se recortan** `estado_codigo`, `cod`, `tipo_codigo` y `clase_codigo`: el
  dominio compara el estado con los cinco códigos (R17) y el `cod` con el
  guardado por F-059 (R12) sin blancos. Uno que queda vacío es `None`, salvo
  `cod`, que es error.
- **Tal cual** `unidad_codigo` y `oficio_codigo`: R14 los compara con los de
  la bandeja, que vienen del catálogo de F-036 sin recortar.
- Las fechas son enteros `YYYYMMDD` y `0` es `NULL` (§6.6 de la pasarela); una
  imposible es error.

Ningún mensaje de error lleva la fila ni un valor suyo (R40): puede traer
datos personales.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from datetime import date
from typing import Any

from domain.models.volcado import MAX_PARTES_POR_LLAMADA, PREFIJO_REFERENCIA
from domain.ports.reclamaciones_obra import FichaReclamacion, FilaReclamacionObra

__all__ = [
    "CAMPO_REFERENCIA",
    "COLUMNAS_DE_LAS_UNIDADES",
    "COLUMNAS_RECLAMACION",
    "MARCADORES",
    "MAX_UNIDADES",
    "PATRON_REFERENCIA",
    "SQL_RECLAMACIONES_DE_LAS_UNIDADES",
    "SQL_RECLAMACIONES_DE_LA_OBRA",
    "fila_a_reclamacion_de_las_unidades",
    "fila_a_reclamacion_obra",
    "select_reclamaciones_de_la_obra",
    "select_reclamaciones_de_las_unidades",
]

#: Las columnas de cada fila de `SQL_RECLAMACIONES_DE_LA_OBRA`.
COLUMNAS_RECLAMACION = 31

#: Las columnas de cada fila de `SQL_RECLAMACIONES_DE_LAS_UNIDADES`: las de R6.
COLUMNAS_DE_LAS_UNIDADES = 12

#: El hueco de la plantilla de la guarda donde van los `?` de las unidades.
MARCADORES = "__MARCADORES__"

#: Como mucho, una unidad por parte de la llamada del ensayo (`N` ≤ 50).
MAX_UNIDADES = MAX_PARTES_POR_LLAMADA

#: El campo de `conext` donde la pasarela guarda la referencia de F-059
#: (`azure-apps/sigrid_api.md` §8.9).
CAMPO_REFERENCIA = "RCPCLI"

#: Solo se lee una referencia que es nuestra: la de F-059, `PVI-…`.
PATRON_REFERENCIA = f"{PREFIJO_REFERENCIA}%"

#: Las reclamaciones de la obra con sus datos (§3).
SQL_RECLAMACIONES_DE_LA_OBRA = (
    "SELECT v.obride, c.cod, e.cod, c.fec, u.cod, a.cod, a.res, t.cod, t.res, r.resubi, c.res, p.valt,\n"
    "       CAST(r.tex AS nvarchar(max)), r.motrcp, r.texurg, r.rcptip, r.fecpre,\n"
    "       CAST(r.solrcp AS nvarchar(max)), k.cod, k.res,\n"
    "       CAST(r.tel AS nvarchar(max)), CAST(r.ele AS nvarchar(max)),\n"
    "       cl.res, pr.nom, pr.tel, pr.tel2, pr.ele, pc.nom, pc.tel, pc.tel2, pc.ele\n"
    "FROM dbo.rcp r\n"
    "JOIN dbo.con c ON c.ide = r.ide\n"
    "JOIN dbo.upv v ON v.ide = r.upvide\n"
    "JOIN dbo.con u ON u.ide = v.ide\n"
    "JOIN dbo.con o ON o.ide = v.obride\n"
    "LEFT JOIN dbo.conest e ON e.tip = c.tip AND e.est = c.est\n"
    "LEFT JOIN dbo.auxofc a ON a.ide = r.ofcide\n"
    "LEFT JOIN dbo.auxtrcp t ON t.ide = r.trcpide\n"
    "LEFT JOIN dbo.auxrcp k ON k.ide = r.rcpide\n"
    "LEFT JOIN dbo.con cl ON cl.ide = r.cliide\n"
    "LEFT JOIN dbo.per pr ON pr.ide = r.recide\n"
    "LEFT JOIN dbo.per pc ON pc.ide = r.cntide\n"
    "OUTER APPLY (SELECT TOP 1 x.valt FROM dbo.conext x\n"
    "             WHERE x.conide = c.ide AND x.cod = ? AND x.valt LIKE ?\n"
    "             ORDER BY x.ide) p\n"
    "WHERE c.tip = ? AND LTRIM(RTRIM(o.cod)) = ?\n"
    "ORDER BY c.cod"
)


#: Las reclamaciones de unas unidades de la obra, sin R33 (§15.5): la plantilla.
SQL_RECLAMACIONES_DE_LAS_UNIDADES = (
    "SELECT v.obride, c.cod, e.cod, c.fec, u.cod, a.cod, a.res, t.cod, t.res, r.resubi, c.res, p.valt\n"
    "FROM dbo.rcp r\n"
    "JOIN dbo.con c ON c.ide = r.ide\n"
    "JOIN dbo.upv v ON v.ide = r.upvide\n"
    "JOIN dbo.con u ON u.ide = v.ide\n"
    "JOIN dbo.con o ON o.ide = v.obride\n"
    "LEFT JOIN dbo.conest e ON e.tip = c.tip AND e.est = c.est\n"
    "LEFT JOIN dbo.auxofc a ON a.ide = r.ofcide\n"
    "LEFT JOIN dbo.auxtrcp t ON t.ide = r.trcpide\n"
    "OUTER APPLY (SELECT TOP 1 x.valt FROM dbo.conext x\n"
    "             WHERE x.conide = c.ide AND x.cod = ? AND x.valt LIKE ?\n"
    "             ORDER BY x.ide) p\n"
    f"WHERE c.tip = ? AND LTRIM(RTRIM(o.cod)) = ? AND u.cod IN ({MARCADORES})\n"
    "ORDER BY c.cod"
)


def select_reclamaciones_de_la_obra(*, codigo_obra: str, tip: int) -> tuple[str, tuple]:
    """La lectura: `RCPCLI`, `PVI-%`, el tipo y el código de obra **ya normalizado**."""
    return SQL_RECLAMACIONES_DE_LA_OBRA, (CAMPO_REFERENCIA, PATRON_REFERENCIA, tip, codigo_obra)


def select_reclamaciones_de_las_unidades(
    *, codigo_obra: str, tip: int, unidades: Sequence[str]
) -> tuple[str, tuple]:
    """La lectura de la guarda (R44): un `?` por unidad, de 1 a 50 y sin repetir.

    Las unidades van **tal cual** (R14: `u.cod` se compara sin recortar) y en
    el orden recibido. Fuera de eso es un error de programación —la guarda
    solo lee lo que va a mandar— y el mensaje no repite ninguna.
    """
    if not 1 <= len(unidades) <= MAX_UNIDADES:
        raise ValueError(f"la lectura de la guarda lleva de 1 a {MAX_UNIDADES} unidades")
    if len(set(unidades)) != len(unidades):
        raise ValueError("la lectura de la guarda lleva cada unidad una sola vez")
    sql = SQL_RECLAMACIONES_DE_LAS_UNIDADES.replace(MARCADORES, ", ".join(["?"] * len(unidades)))
    return sql, (CAMPO_REFERENCIA, PATRON_REFERENCIA, tip, codigo_obra, *unidades)


def fila_a_reclamacion_de_las_unidades(fila: Sequence[Any]) -> FilaReclamacionObra:
    """Una fila de la guarda (12 columnas) al puerto, **sin ficha** (§15.2), o
    `ValueError` sin la fila (R40). Los mismos recortes y obligatorios que
    `fila_a_reclamacion_obra`; una fila de 31 columnas también es error."""
    if not isinstance(fila, (list, tuple)) or len(fila) != COLUMNAS_DE_LAS_UNIDADES:
        raise ValueError(
            f"una fila de Sigrid sin las {COLUMNAS_DE_LAS_UNIDADES} columnas esperadas"
        )
    return _fila(fila, ficha=lambda: None)


def fila_a_reclamacion_obra(fila: Sequence[Any]) -> FilaReclamacionObra:
    """Una fila de §3 al puerto, o `ValueError` sin la fila (R40).

    Se exige una lista o una tupla de 31 columnas, que es lo que trae el JSON
    de la pasarela (`rows[][]`): un texto de 31 letras se desempaquetaría en
    31 «columnas».
    """
    if not isinstance(fila, (list, tuple)) or len(fila) != COLUMNAS_RECLAMACION:
        raise ValueError(
            f"una fila de Sigrid sin las {COLUMNAS_RECLAMACION} columnas esperadas"
        )
    # La ficha, después de los obligatorios (como siempre): primero el error de la fila.
    return _fila(fila[:COLUMNAS_DE_LAS_UNIDADES], ficha=lambda: _ficha(fila[COLUMNAS_DE_LAS_UNIDADES:]))


def _ficha(columnas: Sequence[Any]) -> FichaReclamacion:
    """Las diecinueve columnas de R33."""
    (
        tex, motrcp, texurg, rcptip, fecpre, solrcp, clase, clase_nombre, tel, ele,
        propietario, pr_nom, pr_tel, pr_tel2, pr_ele, pc_nom, pc_tel, pc_tel2, pc_ele,
    ) = columnas  # fmt: skip
    return FichaReclamacion(
        descripcion_larga=_texto(tex),
        motivo=_texto(motrcp),
        urgencia=_texto(texurg),
        forma_comunicacion=_entero(rcptip),
        fecha_prevista=_fecha(fecpre),
        solucion=_texto(solrcp),
        clase_codigo=_codigo(clase),
        clase_nombre=_texto(clase_nombre),
        telefonos_avisos=_texto(tel),
        correo_avisos=_texto(ele),
        propietario=_texto(propietario),
        reclama_nombre=_texto(pr_nom),
        reclama_telefono=_texto(pr_tel),
        reclama_telefono2=_texto(pr_tel2),
        reclama_correo=_texto(pr_ele),
        contacto_nombre=_texto(pc_nom),
        contacto_telefono=_texto(pc_tel),
        contacto_telefono2=_texto(pc_tel2),
        contacto_correo=_texto(pc_ele),
    )


def _fila(
    fila: Sequence[Any], *, ficha: Callable[[], FichaReclamacion | None]
) -> FilaReclamacionObra:
    """Las doce columnas de R6, comunes a las dos lecturas; la ficha, con lo que
    dé `ficha()` **después** de comprobar la obra y el código."""
    (
        obride, cod, estado, fec, unidad, oficio, oficio_nombre, tipo, tipo_nombre,
        ubicacion, descripcion, referencia,
    ) = fila  # fmt: skip

    obra_ref = _texto(obride)
    if not (obra_ref or "").strip():
        raise ValueError("una reclamación sin referencia de obra")
    codigo = _codigo(cod)
    if codigo is None:
        raise ValueError("una reclamación sin código")

    return FilaReclamacionObra(
        obra_ref=obra_ref,
        cod=codigo,
        estado_codigo=_codigo(estado),
        fecha=_fecha(fec),
        unidad_codigo=_texto(unidad),
        oficio_codigo=_texto(oficio),
        oficio_nombre=_texto(oficio_nombre),
        tipo_codigo=_codigo(tipo),
        tipo_nombre=_texto(tipo_nombre),
        ubicacion=_texto(ubicacion),
        descripcion=_texto(descripcion),
        referencia=_texto(referencia),
        ficha=ficha(),
    )


def _texto(valor: Any) -> str | None:
    """`None` se queda en `None`; lo demás, a texto tal cual (como F-036)."""
    return None if valor is None else str(valor)


def _codigo(valor: Any) -> str | None:
    """Un código recortado; vacío tras recortar, `None` (§10.2)."""
    texto = (_texto(valor) or "").strip()
    return texto or None


def _es_entero(valor: Any) -> bool:
    """Un entero del JSON: `True` y `False` también son `int` en Python, y no valen."""
    return isinstance(valor, int) and not isinstance(valor, bool)


def _entero(valor: Any) -> int | None:
    """Un entero de Sigrid tal cual (el `0` también), o `None`."""
    if valor is None:
        return None
    if not _es_entero(valor):
        raise ValueError("una forma de comunicación de Sigrid que no es un entero")
    return valor


def _fecha(valor: Any) -> date | None:
    """Un entero `YYYYMMDD` a fecha; `0` y `NULL` son `None`.

    Una fecha imposible es `ValueError` **sin el valor** y sin la causa: el
    mensaje de `date` tampoco lo lleva, pero así no hay nada que mirar.
    """
    if valor is None or (_es_entero(valor) and valor == 0):
        return None
    if not _es_entero(valor):
        raise ValueError(_FECHA_NO_VALIDA)
    anio, resto = divmod(valor, 10_000)
    mes, dia = divmod(resto, 100)
    try:
        return date(anio, mes, dia)
    except ValueError:
        raise ValueError(_FECHA_NO_VALIDA) from None


_FECHA_NO_VALIDA = "una fecha de Sigrid que no es un entero YYYYMMDD válido"
