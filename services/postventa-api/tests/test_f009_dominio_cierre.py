# services/postventa-api/tests/test_f009_dominio_cierre.py
"""El dominio del cierre: decidir sin tocar nada (F-009, R18, R19, R20, R21).

`evaluar` es la única pieza de F-009 que **decide** si una reclamación se
cierra, y es dominio puro: sin red, sin SQL, sin reloj. Por eso se prueba
entera con fixtures y por eso puede exigírsele cobertura y mutación sin abrir
una conexión.

Cuatro requisitos, y el cuarto es el que más fácil se cae solo:

- **R18** · una reclamación ya cerrada se registra como `ya_cerrada` y **no es
  un error**.
- **R19** · un estado que no admite cierre automático aborta **nombrando el
  estado**, `NPR` (NO PROCEDE) incluido: alguien decidió que esa reclamación no
  procede y cerrarla la daría por resuelta.
- **R20** · control negativo: el dominio **no sabe qué es un gráfico**.
  `Reclamacion` no tiene ese campo y el módulo no menciona `rcg` ni `gra`. Es
  la forma más barata de que la decisión del humano del 2026-08-26 —validar →
  cerrar → subir el PDF— no se pueda incumplir por descuido.
- **R21** · el plan trae **siempre** el aviso de que la reclamación quedará
  cerrada sin el parte dentro de Sigrid. Un aviso que sale a veces es un aviso
  que nadie lee.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from domain.models.cierre import (
    AVISO_SIN_GRAFICO,
    CODIGO_ESTADO_CIERRE,
    CODIGOS_ESTADO_CERRABLE,
    LONGITUD_MAXIMA_LOGIN,
    TEXTO_LOG_CIERRE,
    TEXTO_PROCESO_ERP,
    EstadoSigrid,
    PlanDeCierre,
    Reclamacion,
    a_codigo_de_sigrid,
    evaluar,
)

#: Raíz del servicio (este fichero vive en `<servicio>/tests/`).
SERVICIO = Path(__file__).resolve().parent.parent

#: El módulo que este test vigila.
MODULO_DOMINIO = SERVICIO / "domain" / "models" / "cierre.py"

#: Las dos tablas de gráficos de Sigrid, que el dominio no puede nombrar (R20).
#:
#: Como palabras completas: `gra` aparece dentro de «gráfico», y el aviso de
#: R21 **tiene** que hablar del gráfico para que quien confirma sepa lo que
#: está aceptando. Lo que se prohíbe es la **tabla**, no la palabra.
PATRON_TABLAS_DE_GRAFICOS = re.compile(r"\b(rcg|gra)\b")


def _reclamacion(*, est: int, cod_origen: str) -> Reclamacion:
    """Una reclamación inventada, en el estado que pida el test.

    Los números son inventados y **no** son los de la instalación: lo que se
    prueba es que el dominio decide con lo que le den, sin conocer ninguno.
    """
    return Reclamacion(
        ide=111_222,
        emp=1,
        tip=708,
        est=est,
        codigo="RS26.08/0123",
        descripcion="REPARACION DE INCIDENCIA",
        estado_origen_cod=cod_origen,
        estado_origen_res=f"ESTADO {cod_origen}",
        estado_destino_est=90,
        estado_destino_cod=CODIGO_ESTADO_CIERRE,
        estado_destino_res="CERRADA",
    )


# --------------------------------------------------------------------------
# R18 · ya cerrada no es un error
# --------------------------------------------------------------------------


def test_f009_r18_una_reclamacion_ya_cerrada_no_se_vuelve_a_cerrar():
    """R18 · si ya está en el estado de cierre, `ya_cerrada` y sin escribir.

    Se compara **contra el estado de destino leído del ERP**, no contra ningún
    número: los dos lados de la comparación salen de la misma consulta.
    """
    plan = evaluar(
        _reclamacion(est=90, cod_origen=CODIGO_ESTADO_CIERRE),
        login_sigrid="unlogin",
    )

    assert plan.ya_cerrada is True
    assert plan.cerrable is False
    assert plan.motivo is not None


def test_f009_r18_ya_cerrada_se_detecta_aunque_el_codigo_no_acompanie():
    """R18 · basta con que el `est` sea el de destino.

    Un `conest` con el código en otro sitio no puede hacer que se vuelva a
    cerrar algo que ya está cerrado.
    """
    plan = evaluar(_reclamacion(est=90, cod_origen="PTE"), login_sigrid="unlogin")

    assert plan.ya_cerrada is True
    assert plan.cerrable is False


def test_f009_r18_ya_cerrada_se_detecta_tambien_por_el_codigo():
    """R18 · y con que el código de origen sea el de cierre, también."""
    plan = evaluar(_reclamacion(est=7, cod_origen=CODIGO_ESTADO_CIERRE), login_sigrid="x")

    assert plan.ya_cerrada is True


# --------------------------------------------------------------------------
# R19 · un estado que no admite cierre aborta, y dice cuál es
# --------------------------------------------------------------------------


@pytest.mark.parametrize("cerrable", CODIGOS_ESTADO_CERRABLE)
def test_f009_r19_los_estados_declarados_cerrables_si_se_cierran(cerrable):
    """R19 · `SAT`, `PTE` y `TER` sí. Son los tres que Posventa cierra."""
    plan = evaluar(_reclamacion(est=3, cod_origen=cerrable), login_sigrid="unlogin")

    assert plan.cerrable is True
    assert plan.ya_cerrada is False
    assert plan.motivo is None


def test_f009_r19_npr_no_se_cierra_y_el_motivo_lo_nombra():
    """R19 · `NPR` (NO PROCEDE) queda fuera **a propósito**.

    Alguien decidió que esa reclamación no procede. Cerrarla la daría por
    resuelta, que es exactamente lo contrario de lo que se decidió.
    """
    plan = evaluar(_reclamacion(est=7, cod_origen="NPR"), login_sigrid="unlogin")

    assert plan.cerrable is False
    assert plan.ya_cerrada is False
    assert "NPR" in (plan.motivo or "")


def test_f009_r19_un_estado_desconocido_tampoco_se_cierra():
    """R19 · lo que no está declarado cerrable, no se cierra.

    Lista blanca y no lista negra: un estado nuevo en el ERP no puede empezar a
    cerrarse solo porque nadie se acordó de prohibirlo.
    """
    plan = evaluar(_reclamacion(est=42, cod_origen="XXX"), login_sigrid="unlogin")

    assert plan.cerrable is False
    assert "XXX" in (plan.motivo or "")


def test_f009_r19_sin_estado_de_origen_legible_no_se_cierra():
    """R19 · si `conest` no dio el estado de origen, no se decide a ciegas."""
    plan = evaluar(_reclamacion(est=3, cod_origen=""), login_sigrid="unlogin")

    assert plan.cerrable is False
    assert plan.motivo is not None


# --------------------------------------------------------------------------
# R21 · el aviso va siempre
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "cod_origen", [*CODIGOS_ESTADO_CERRABLE, "NPR", CODIGO_ESTADO_CIERRE, ""]
)
def test_f009_r21_el_plan_siempre_trae_el_aviso_de_que_quedara_sin_grafico(cod_origen):
    """R21 · salga cerrable o no, el aviso está.

    Es el riesgo aceptado de `design.md` §2 puesto delante de quien confirma:
    este servicio va a producir reclamaciones `CER` sin ninguna fila en `rcg`,
    algo que no ha ocurrido en los 2.365 cierres de «Cerrar parte» desde 2023.
    """
    plan = evaluar(_reclamacion(est=3, cod_origen=cod_origen), login_sigrid="unlogin")

    assert plan.aviso_sin_grafico == AVISO_SIN_GRAFICO
    assert plan.aviso_sin_grafico.strip() != ""


def test_f009_r21_el_aviso_dice_las_dos_cosas_que_hay_que_saber():
    """R21 · que quedará **cerrada** y que será **sin el parte dentro de Sigrid**.

    Un aviso genérico («revisa antes de confirmar») no informa de nada.
    """
    minusculas = AVISO_SIN_GRAFICO.lower()

    assert "sigrid" in minusculas
    assert "gráfico" in minusculas or "grafico" in minusculas


# --------------------------------------------------------------------------
# R20 · control negativo: el dominio no sabe qué es un gráfico
# --------------------------------------------------------------------------


def test_f009_r20_la_reclamacion_no_tiene_ningun_campo_de_graficos():
    """R20 · `Reclamacion` ni siquiera puede transportar ese dato.

    `design.md` §6: la forma más barata de que R20 no se incumpla por descuido
    es que el dato no exista en el modelo. Si mañana alguien añade
    `tiene_grafico`, este test se cae antes de que nadie lo consulte.
    """
    campos = set(Reclamacion.__dataclass_fields__)

    assert not [campo for campo in campos if "graf" in campo or "rcg" in campo]


def test_f009_r20_el_dominio_no_menciona_las_tablas_de_graficos():
    """R20 · ni `rcg` ni `gra` aparecen como tabla en el módulo del dominio.

    El control es sobre las **tablas**: la palabra «gráfico» sí aparece, y
    tiene que aparecer, porque el aviso de R21 habla justamente de eso.
    """
    texto = MODULO_DOMINIO.read_text(encoding="utf-8")

    assert PATRON_TABLAS_DE_GRAFICOS.findall(texto) == []


def test_f009_r20_el_barrido_de_tablas_de_graficos_caza_una_inyectada():
    """R20 · control negativo del propio control: el patrón salta.

    Un barrido que nunca se ha visto saltar no protege de nada.
    """
    sospechoso = "SELECT COUNT(*) FROM dbo.rcg WHERE con = ?"

    assert PATRON_TABLAS_DE_GRAFICOS.findall(sospechoso) == ["rcg"]


# --------------------------------------------------------------------------
# Las constantes: códigos, nunca números (C3)
# --------------------------------------------------------------------------


def test_f009_r3_el_estado_de_cierre_es_un_codigo_y_no_un_numero():
    """C3 · `CER` es un **código**; el número lo pone el ERP en ejecución."""
    assert isinstance(CODIGO_ESTADO_CIERRE, str)
    assert CODIGO_ESTADO_CIERRE == "CER"


def test_f009_r3_los_estados_cerrables_tambien_son_codigos():
    """C3 · y los tres de la lista blanca, igual."""
    assert all(isinstance(codigo, str) for codigo in CODIGOS_ESTADO_CERRABLE)
    assert CODIGO_ESTADO_CIERRE not in CODIGOS_ESTADO_CERRABLE


def test_f009_r25_el_texto_del_log_empieza_por_el_del_proceso_del_erp():
    """R25 · sigue apareciendo en los informes de Posventa, y se distingue.

    `tex LIKE 'Cerrar parte%'` es el filtro con el que F-008 midió toda la
    población. Un texto que empezara distinto nos borraría de esos informes; y
    un texto idéntico haría nuestros cierres indistinguibles de los manuales
    justo en la feature donde más falta hace poder distinguirlos.
    """
    assert TEXTO_LOG_CIERRE.startswith(TEXTO_PROCESO_ERP)
    assert TEXTO_LOG_CIERRE != TEXTO_PROCESO_ERP
    assert "postventa-incidencias" in TEXTO_LOG_CIERRE


def test_f009_r35_la_longitud_del_login_es_la_del_campo_del_erp():
    """R35 · `dbo.log.usu` es «Texto de 48 caracteres» (`sigrid_tablas.md`)."""
    assert LONGITUD_MAXIMA_LOGIN == 48


# --------------------------------------------------------------------------
# El estado legible, que es lo que enseña el dry-run (R9)
# --------------------------------------------------------------------------


def test_f009_r9_la_reclamacion_expone_los_dos_estados_legibles():
    """R9 · código y descripción de origen y destino, para el dry-run."""
    reclamacion = _reclamacion(est=3, cod_origen="PTE")

    assert reclamacion.estado_origen == EstadoSigrid(est=3, cod="PTE", res="ESTADO PTE")
    assert reclamacion.estado_destino == EstadoSigrid(
        est=90, cod=CODIGO_ESTADO_CIERRE, res="CERRADA"
    )


def test_f009_r9_el_plan_lleva_el_login_con_el_que_se_firmaria():
    """R9 · quien confirma tiene que ver con qué login se va a firmar."""
    plan = evaluar(_reclamacion(est=3, cod_origen="PTE"), login_sigrid="mengano")

    assert isinstance(plan, PlanDeCierre)
    assert plan.login_sigrid == "mengano"


# --------------------------------------------------------------------------
# R6 · el código del parte, al formato de Sigrid
# --------------------------------------------------------------------------


def test_f009_r6_el_codigo_del_parte_vuelve_al_formato_con_barra():
    """R6 · en el fichero va con guion; en Sigrid, con barra."""
    assert a_codigo_de_sigrid("RS26.08 - 0123") == "RS26.08/0123"


def test_f009_r6_un_codigo_que_ya_viene_con_barra_no_se_toca():
    """R6 · el parte puede traerlo ya como lo escribe Sigrid."""
    assert a_codigo_de_sigrid("RS26.08/0123") == "RS26.08/0123"
