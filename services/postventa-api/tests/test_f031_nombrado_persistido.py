# services/postventa-api/tests/test_f031_nombrado_persistido.py
"""El nombrado sale de lo **guardado**, no del cuerpo (F-031 R1, R2, R4, R7, R8, R11, R12).

Todo se prueba sobre `paso_archivo` con dobles: **sin red, sin BBDD y sin IA**
(R28). Ningún test de este fichero construye un adaptador capaz de llegar a
Graph ni abre una conexión, y la guarda de sesión de `tests/conftest.py` lo
hace además imposible.

## Qué hace falta para que un test de aquí demuestre algo

Que **las dos fuentes digan cosas distintas**. Hasta F-031 el nombre del
fichero salía de `ctx.extraccion` —lo que declaraba el cuerpo— y la puerta
aprobaba lo que constaba en `ctx.situacion.validacion` —lo guardado—; hoy
coinciden siempre porque el front manda lo que leyó, y por eso un test que
prepare las dos con el mismo valor **pasaría igual antes y después de esta
feature**. Es la misma lección que dejó escrita F-030 en
`tests/utiles_pg.py::con_el_veredicto_guardado`: los casos que vigilan de
dónde sale un dato separan las dos fuentes a mano, a propósito.

De ahí que aquí no se use ese atajo: cada caso monta el contexto con unos
códigos y la situación del doble con **otros**.

**Ni un dato real.** `0677`, `0626`, `RS26.08/0123` y `RS26.09/0178` son
inventados y salen del material de F-003; los bytes del «PDF» son
`b"%PDF-1.4 de mentira"`.
"""

from __future__ import annotations

import pytest
from domain.models.nombrado import es_el_mismo_codigo

# --------------------------------------------------------------------------
# R4 · «el mismo código escrito de dos maneras», en el dominio
# --------------------------------------------------------------------------
#
# La función vive en `domain/models/nombrado.py` y no en el paso por lo que ese
# módulo ya tiene escrito: **el dueño de «qué es el mismo código» es quien lo
# normaliza** (F-028 R47, F-032). `normalizar_codigo` ya cambió una vez —el
# 2026-09-17— y el día que vuelva a cambiar, el cotejo se mueve con ella.


@pytest.mark.parametrize(
    ("caso", "uno", "otro"),
    (
        # Los tres casos que F-032 declaró explícitamente **el mismo código**.
        ("el espacio dentro del primer tramo", "RS 26.09/0178", "RS26.09/0178"),
        ("el espacio dentro del código de obra", "06 26", "0626"),
        ("el guion largo del separador", "RS26.09 – 0178", "RS26.09-0178"),
        # Y los blancos que `str.split()` se lleva sin lista que mantener.
        ("el espacio no separable", "06 26", "0626"),
        ("los extremos recortados", "  0677  ", "0677"),
        # Los dos vacíos: **sí** son el mismo (§3.1). Quien opina sobre el
        # vacío es R7, un paso más adelante, y con otro error.
        ("los dos vacíos", "", ""),
        ("los dos ausentes", None, None),
        ("ausente contra vacío", None, ""),
        ("ausente contra solo blancos", None, "   "),
    ),
)
def test_f031_r4_dos_formas_de_escribir_el_mismo_codigo_son_el_mismo(caso, uno, otro):
    """R4 · lo que F-032 declaró el mismo código **no** puede dar un 409.

    Es el caso que costó un cierre a mano el 2026-09-17: el front manda lo que
    `valorDeCampo` devuelve, que solo hace `trim()`, y la base guarda lo que
    F-032 saneó al leerlo. Un cotejo literal convertiría en error justo lo que
    la feature anterior declaró equivalente.
    """
    assert es_el_mismo_codigo(uno, otro) is True
    assert es_el_mismo_codigo(otro, uno) is True, f"no es simétrico: {caso}"


@pytest.mark.parametrize(
    ("caso", "uno", "otro"),
    (
        ("otra obra", "0677", "0626"),
        ("otra incidencia", "RS26.08/0123", "RS26.09/0178"),
        ("los ceros a la izquierda cuentan", "0677", "677"),
        ("un código contra el vacío", "0677", ""),
        ("un código contra el ausente", "0677", None),
        ("otro tramo", "RS26.09/0178", "RS26.09/0179"),
    ),
)
def test_f031_r4_dos_codigos_distintos_no_son_el_mismo(caso, uno, otro):
    """R4 · y lo que de verdad es distinto tiene que seguir siéndolo.

    El tercer caso es la regla que `nombrado.py` no negocia: `int("0677")` es
    un bug, no una normalización, y `677` es otra obra.
    """
    assert es_el_mismo_codigo(uno, otro) is False, caso
    assert es_el_mismo_codigo(otro, uno) is False, f"no es simétrico: {caso}"


def test_f031_r4_la_funcion_se_exporta_en_el_modulo():
    """R4 · `es_el_mismo_codigo` es parte de la interfaz pública del dominio.

    Quien la va a llamar es el paso de archivo, desde la capa de aplicación:
    si no está en `__all__` es una función privada que alguien usa de fuera.
    """
    from domain.models import nombrado

    assert "es_el_mismo_codigo" in nombrado.__all__


def test_f031_r4_el_cotejo_se_apoya_en_normalizar_codigo_y_no_en_una_copia():
    """R4 · un criterio, no dos (F-028 R47).

    No se afirma sobre el texto de la función: se afirma sobre la propiedad
    que importa. Si mañana alguien reescribiera el cotejo con su propio saneo,
    este caso —un blanco que solo `normalizar_codigo` sabe quitar— es el que
    se pondría rojo.
    """
    from domain.models.nombrado import normalizar_codigo

    bruto = "RS26.09\t–\n0178"
    assert normalizar_codigo(bruto) == "RS26.09-0178"
    assert es_el_mismo_codigo(bruto, "RS26.09-0178") is True
