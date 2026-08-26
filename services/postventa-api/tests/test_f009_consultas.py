# services/postventa-api/tests/test_f009_consultas.py
"""El SQL de lectura del cierre, comprobado carácter a carácter (F-009).

Que `consultas.py` sea un constructor **puro** de SQL es la decisión que hace
testeable la feature entera sin red (`design.md` §3). Es el mismo patrón que
`infrastructure/persistencia/sentencias.py`, y por el mismo motivo: el SQL más
delicado del servicio se comprueba aquí, en un test unitario, y no contra el
ERP de producción.

Lo que fija:

- **R1, R4** · el estado de destino se resuelve contra `conest` por su
  **código**, y el `tip` con el que se une sale de la propia reclamación.
- **R5** · la búsqueda se acota **siempre** por `tip`: la unicidad de `con.cod`
  está medida dentro del tipo 708, no en toda la tabla.
- **R6** · el código del parte vuelve al formato con barra de Sigrid, y esa
  conversión es la **inversa exacta** de la que aplica el nombrado de F-006.
- **R20** · control negativo: el SQL de lectura no menciona las tablas de
  gráficos. No hay ningún `COUNT` sobre ellas y es deliberado.
- **R2, R7** · los dos casos de aborto sin escribir, sobre el mapeo de filas.
- **Parametrización** · ni un valor pegado al texto (`sigrid_api.md` §5.2).
"""

from __future__ import annotations

import re

import pytest
from domain.models.cierre import CODIGO_ESTADO_CIERRE, Reclamacion, a_codigo_de_sigrid
from domain.models.errores import (
    EstadoDeCierreNoResoluble,
    ReclamacionNoLocalizada,
)
from domain.models.nombrado import nombre_de_archivo
from infrastructure.sigrid.consultas import (
    COLUMNAS_RECLAMACION,
    fila_a_reclamacion,
    reclamacion_unica,
    select_reclamacion,
    select_usuario,
)

#: Las dos tablas de gráficos del ERP, que este SQL no puede mencionar (R20).
PATRON_TABLAS_DE_GRAFICOS = re.compile(r"\b(rcg|gra)\b", re.IGNORECASE)

#: Una fila de la consulta del dry-run, inventada. Los números no son los de
#: la instalación: el ERP los da, aquí nadie los conoce.
FILA = (111_222, 1, 708, 3, "RS26.08/0123", "REPARACION", "PTE", "PENDIENTE", 90, "CER", "CERRADA")


# --------------------------------------------------------------------------
# La consulta del dry-run
# --------------------------------------------------------------------------


def test_f009_r1_el_estado_de_destino_se_resuelve_contra_conest_por_codigo():
    """R1 · `conest` se une por `tip` y se filtra por `cod`, nunca por número.

    Es el checkpoint C3 escrito en SQL: el número del estado de cierre lo dice
    el ERP en ejecución, y por eso lo que viaja es el **código**.
    """
    sql, parametros = select_reclamacion(
        tip=708, codigo="RS26.08/0123", codigo_estado_cierre=CODIGO_ESTADO_CIERRE
    )

    assert "LEFT JOIN dbo.conest ed ON ed.tip = c.tip AND ed.cod = ?" in sql
    assert parametros[0] == CODIGO_ESTADO_CIERRE


def test_f009_r1_tambien_trae_el_estado_de_origen_legible():
    """R1, R9 · el de origen se resuelve en la misma consulta.

    Una segunda llamada para traducir un número a `PTE / PENDIENTE` sería otro
    viaje al ERP por cada dry-run, y F-008 §6.4.6 recomendó exactamente esto.
    """
    sql, _ = select_reclamacion(
        tip=708, codigo="RS26.08/0123", codigo_estado_cierre=CODIGO_ESTADO_CIERRE
    )

    assert "LEFT JOIN dbo.conest eo ON eo.tip = c.tip AND eo.est = c.est" in sql


def test_f009_r5_la_busqueda_se_acota_siempre_por_tip():
    """R5 · `cod` es único **dentro del tipo**, no en toda la tabla.

    Está medido: 23.063 códigos distintos en 23.063 conceptos de tipo 708. Que
    no pueda repetirse en otro tipo de concepto **no se ha comprobado**, así
    que el filtro va siempre.
    """
    sql, parametros = select_reclamacion(
        tip=708, codigo="RS26.08/0123", codigo_estado_cierre=CODIGO_ESTADO_CIERRE
    )

    assert "WHERE c.tip = ? AND c.cod = ?" in sql
    assert parametros == (CODIGO_ESTADO_CIERRE, 708, "RS26.08/0123")


def test_f009_r4_el_tip_entra_por_parametro_y_no_esta_pegado_al_sql():
    """R4 · el tipo de concepto es configuración, como el estado.

    Cambiar de instalación no puede exigir tocar el SQL.
    """
    sql, parametros = select_reclamacion(
        tip=999, codigo="X", codigo_estado_cierre=CODIGO_ESTADO_CIERRE
    )

    assert "999" not in sql
    assert 999 in parametros


def test_f009_la_consulta_del_dry_run_no_escribe_nada():
    """R8 · el dry-run **lee**. Ni un verbo de escritura en el texto."""
    sql, _ = select_reclamacion(
        tip=708, codigo="RS26.08/0123", codigo_estado_cierre=CODIGO_ESTADO_CIERRE
    )

    en_mayusculas = sql.upper()
    for verbo in ("UPDATE", "INSERT", "DELETE", "MERGE", "DROP", "EXEC"):
        assert verbo not in en_mayusculas


def test_f009_r5_ningun_valor_va_pegado_al_texto_del_sql():
    """`sigrid_api.md` §5.2 · siempre marcadores `?`, nunca concatenación.

    No es solo higiene: la pasarela rechaza lo que no le guste, pero antes que
    eso, un código concatenado sería una inyección contra el ERP.
    """
    sql, parametros = select_reclamacion(
        tip=708, codigo="RS26.08/0123'; DROP TABLE con--", codigo_estado_cierre="CER"
    )

    assert "DROP" not in sql.upper()
    assert sql.count("?") == len(parametros)


# --------------------------------------------------------------------------
# R20 · control negativo: nada de gráficos en el SQL de lectura
# --------------------------------------------------------------------------


def test_f009_r20_el_sql_de_lectura_no_menciona_las_tablas_de_graficos():
    """R20 · no hay ningún `COUNT` sobre gráficos, y es **deliberado**.

    Tras la decisión del humano del 2026-08-26, el gráfico no condiciona el
    cierre: la precondición es propia —parte apto y archivado— y ninguna otra.
    Un `COUNT` aquí habría dejado a F-009 sin poder cerrar prácticamente nada:
    el 98,7 % de las reclamaciones abiertas no tiene gráfico.
    """
    sql, _ = select_reclamacion(
        tip=708, codigo="RS26.08/0123", codigo_estado_cierre=CODIGO_ESTADO_CIERRE
    )

    assert PATRON_TABLAS_DE_GRAFICOS.findall(sql) == []


def test_f009_r20_el_barrido_del_sql_caza_una_tabla_de_graficos_inyectada():
    """R20 · control negativo del control: el patrón salta de verdad."""
    sospechoso = "SELECT COUNT(*) FROM dbo.rcg WHERE con = ?"

    assert PATRON_TABLAS_DE_GRAFICOS.findall(sospechoso) != []


# --------------------------------------------------------------------------
# La verificación del login (R30)
# --------------------------------------------------------------------------


def test_f009_r30_la_verificacion_del_login_es_una_lectura_aparte():
    """R30 · va aparte porque su fallo tiene motivo propio y mensaje propio.

    Quien lo recibe tiene que saber que lo que toca es dar de alta la
    correspondencia a mano, no reintentar.
    """
    sql, parametros = select_usuario(login="fulanito")

    assert sql == "SELECT COUNT(*) FROM dbo.usu WHERE cod = ?"
    assert parametros == ("fulanito",)


# --------------------------------------------------------------------------
# R2 y R7 · los dos abortos, sobre el recuento de filas
# --------------------------------------------------------------------------


def test_f009_r7_una_sola_fila_devuelve_la_reclamacion():
    """R7 · el camino normal: exactamente una."""
    reclamacion = reclamacion_unica([FILA], codigo="RS26.08/0123")

    assert isinstance(reclamacion, Reclamacion)
    assert reclamacion.ide == 111_222
    assert reclamacion.estado_destino_cod == CODIGO_ESTADO_CIERRE


def test_f009_r7_sin_filas_no_hay_reclamacion_y_no_es_un_error():
    """R7 · cero filas es `None`: ese código no está en el ERP.

    No se levanta aquí porque quien decide qué hacer con «no está» es el paso,
    y el mensaje que necesita el usuario lo compone el borde.
    """
    assert reclamacion_unica([], codigo="RS26.08/0123") is None


def test_f009_r7_varias_reclamaciones_abortan_y_dicen_cuantas():
    """R7 · dos códigos iguales en el mismo tipo: **no se cierra ninguna**.

    Está medido que no pasa (23.063 de 23.063), así que esto es una red de
    seguridad. Elegir una de las dos sería cerrar la incidencia equivocada en
    el ERP de producción.
    """
    otra = (999, 1, 708, 3, "RS26.08/0123", "OTRA", "PTE", "PENDIENTE", 90, "CER", "CERRADA")

    with pytest.raises(ReclamacionNoLocalizada) as fallo:
        reclamacion_unica([FILA, otra], codigo="RS26.08/0123")

    assert "2" in fallo.value.motivo


def test_f009_r2_conest_duplicado_aborta_sin_escribir_nada():
    """R2 · el mismo `ide` dos veces es `conest` devolviendo dos filas.

    El `LEFT JOIN` multiplica: si el maestro de estados tuviera dos filas con
    el código de cierre, la consulta devolvería la misma reclamación duplicada.
    Suponer cuál vale sería escribir un estado que nadie eligió.
    """
    duplicada = (111_222, 1, 708, 3, "RS26.08/0123", "REPARACION", "PTE", "PENDIENTE", 91, "CER", "CERRADA")

    with pytest.raises(EstadoDeCierreNoResoluble):
        reclamacion_unica([FILA, duplicada], codigo="RS26.08/0123")


def test_f009_r2_sin_estado_de_cierre_en_conest_tampoco_se_cierra():
    """R2 · el `LEFT JOIN` no casó: `conest` no tiene el código de cierre.

    Es el caso que protege C3 por el otro lado: el número no está en el código
    **a propósito**, así que si el ERP no lo dice, no se supone.
    """
    sin_destino = (111_222, 1, 708, 3, "RS26.08/0123", "REPARACION", "PTE", "PENDIENTE", None, None, None)

    with pytest.raises(EstadoDeCierreNoResoluble) as fallo:
        reclamacion_unica([sin_destino], codigo="RS26.08/0123")

    assert CODIGO_ESTADO_CIERRE in fallo.value.motivo


def test_f009_r2_el_motivo_del_aborto_nombra_la_reclamacion():
    """R2 · «no se pudo» sin decir de cuál obliga a adivinar."""
    sin_destino = (111_222, 1, 708, 3, "RS26.08/0123", "REPARACION", "PTE", "PENDIENTE", None, "CER", "CERRADA")

    with pytest.raises(EstadoDeCierreNoResoluble) as fallo:
        reclamacion_unica([sin_destino], codigo="RS26.08/0123")

    assert "RS26.08/0123" in fallo.value.motivo


# --------------------------------------------------------------------------
# El mapeo de la fila
# --------------------------------------------------------------------------


def test_f009_el_mapeo_respeta_el_orden_declarado_de_columnas():
    """Las columnas del `SELECT` y las del mapeo son la **misma** lista.

    Dos listas del mismo concepto divergen siempre, y aquí divergir significa
    leer el estado de origen donde está la empresa.
    """
    sql, _ = select_reclamacion(tip=708, codigo="X", codigo_estado_cierre="CER")

    assert len(COLUMNAS_RECLAMACION) == len(FILA)
    for columna in COLUMNAS_RECLAMACION:
        assert columna in sql


def test_f009_el_mapeo_no_convierte_los_codigos_a_numero():
    """El código de la reclamación es texto y sigue siéndolo.

    Misma regla que el código de obra en F-006: `int()` sobre un código es un
    bug, no una normalización.
    """
    reclamacion = fila_a_reclamacion(FILA)

    assert isinstance(reclamacion.codigo, str)
    assert reclamacion.codigo == "RS26.08/0123"


def test_f009_el_mapeo_tolera_un_estado_de_origen_sin_traducir():
    """El `LEFT JOIN` del origen puede no casar, y eso no revienta el mapeo.

    Quien decide qué hacer con un estado ilegible es el dominio (R19), no el
    adaptador: aquí solo se convierte el `NULL` en cadena vacía.
    """
    sin_origen = (111_222, 1, 708, 3, "RS26.08/0123", "REPARACION", None, None, 90, "CER", "CERRADA")

    reclamacion = fila_a_reclamacion(sin_origen)

    assert reclamacion.estado_origen_cod == ""
    assert reclamacion.estado_origen_res == ""


# --------------------------------------------------------------------------
# R6 · el código del parte, al formato de Sigrid, y de vuelta
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "bruto",
    ["RS26.08/0123", "RS26.08 - 0123", "RS26.08 – 0123", "  RS26.08/0123  "],
)
def test_f009_r6_todas_las_formas_del_codigo_acaban_en_la_de_sigrid(bruto):
    """R6 · barra, guion normal, guion largo y espacios sobrantes.

    Los guiones raros salen de los escaneos, de los correos y de Word, que
    sustituye guiones por rayas sin avisar. Dos lecturas del mismo parte tienen
    que localizar la **misma** reclamación en el ERP.
    """
    assert a_codigo_de_sigrid(bruto) == "RS26.08/0123"


def test_f009_r6_es_la_inversa_exacta_del_nombrado_de_f006():
    """R6 · ida y vuelta contra `domain/models/nombrado.py`, sin copias.

    Se compone el nombre del fichero como lo hace F-006 y se recupera de él el
    código tal y como lo escribe Sigrid. Si alguien cambiara el separador de
    uno de los dos lados, este test se cae: es la única forma de que las dos
    conversiones no diverjan.
    """
    nombre = nombre_de_archivo(codigo_obra="0677", numero_incidencia="RS26.08/0123")
    tramo_de_la_incidencia = nombre.removeprefix("0677 - ").removesuffix(
        " PARTE FIRMADO.pdf"
    )

    assert tramo_de_la_incidencia == "RS26.08 - 0123"
    assert a_codigo_de_sigrid(tramo_de_la_incidencia) == "RS26.08/0123"


def test_f009_r6_un_codigo_ausente_sale_vacio_y_no_revienta():
    """R6 · sin código no hay conversión, y quien decide qué hacer es el paso.

    Levantar aquí obligaría a este módulo a saber por qué se pide el código, y
    no lo sabe.
    """
    assert a_codigo_de_sigrid(None) == ""
    assert a_codigo_de_sigrid("   ") == ""


def test_f009_r6_la_conversion_es_idempotente():
    """R6 · aplicarla dos veces da lo mismo que aplicarla una."""
    una = a_codigo_de_sigrid("RS26.08 - 0123")

    assert a_codigo_de_sigrid(una) == una
