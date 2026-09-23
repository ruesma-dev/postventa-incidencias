# services/postventa-api/tests/test_f034_codigos_en_el_erp.py
"""Los dos códigos con los que se escribe en el ERP salen de lo guardado (F-034).

Este fichero crece por bloques (`tasks.md`):

- **Bloque 1** (este): las piezas compartidas. El error nuevo,
  `CodigoNoConsta` (R15, R28), y en qué se diferencia de sus tres hermanas
  de 409; y el módulo `application/pipelines/codigos_del_parte.py`, con el
  cotejo normalizado (R12), su variante de solo la incidencia (R16), la
  exigencia de lo guardado completo (R15) y la prueba de que el mensaje de
  `POST /api/archivar` no ha cambiado ni un byte al moverlo (R26).
- **Bloques 2 y 3**: `POST /api/adjuntar` y `POST /api/cerrar` con los puertos
  inyectados (R8–R19, R24, R27).

**Sin red, sin base de datos, sin IA y sin tocar el ERP** (R37).
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime

import pytest
from application.pipelines import paso_archivo as modulo_paso_archivo
from application.pipelines.codigos_del_parte import (
    CodigosDelParte,
    codigos_guardados,
    exigir_codigos_completos,
    exigir_codigos_declarados,
)
from application.pipelines.paso_archivo import paso_archivo
from domain.models.errores import (
    CodigoNoConsta,
    CodigosNoCoinciden,
    NombradoImposible,
    ParteNoApto,
    ParteNoArchivado,
)
from domain.models.estado import SituacionParte
from interface_adapters.api import archivar as modulo_archivar

from tests.utiles_sharepoint import (
    CARPETA_BASE,
    ArchivoPortFalso,
    BibliotecaFalsa,
    RepositorioFalso,
    contexto_apto,
)
from tests.utiles_validacion import veredicto_apto

HASH = "f034aa0011bb"

#: Lo que consta **guardado** del parte de estos casos. Inventado.
OBRA_GUARDADA = "0626"
INCIDENCIA_GUARDADA = "RS26.08/0123"

#: Una cola de `y_por_eso` cualquiera, para ver que el mensaje la lleva.
Y_POR_ESO = "no se ha tocado nada del ERP"

# --------------------------------------------------------------------------
# R15, R28 · el error nuevo, y por qué es un error propio
# --------------------------------------------------------------------------

#: Las hermanas de 409 de las que `CodigoNoConsta` tiene que distinguirse
#: (`design.md` §3.2). Cada una manda a quien la lee a un sitio distinto.
HERMANAS_DE_409 = (CodigosNoCoinciden, ParteNoArchivado, NombradoImposible)


def test_f034_r15_errores_codigo_no_consta_lleva_su_motivo():
    """R15 · el `motivo` viaja en el objeto, como en sus hermanas.

    El borde lo lee para componer el cuerpo del 409 (`{"error": <motivo>}`,
    R27). Sin él, el error saldría mudo y quien lo recibiera no sabría **cuál**
    de los dos códigos falta.
    """
    error = CodigoNoConsta("no consta guardado el nº de incidencia de este parte")

    assert isinstance(error, Exception)
    assert error.motivo == "no consta guardado el nº de incidencia de este parte"
    assert str(error) == error.motivo


@pytest.mark.parametrize("hermana", HERMANAS_DE_409 + (ParteNoApto,))
def test_f034_r28_errores_codigo_no_consta_no_es_ninguna_hermana(hermana):
    """R28 · tres hechos, tres errores; la distinción **no es cosmética**.

    Si `CodigoNoConsta` heredara de cualquiera de ellas —o al revés—, un
    `except` del borde se la tragaría y a la persona le llegaría el mensaje de
    otro hecho, que se arregla de otra forma: guardar una corrección no sirve
    de nada si lo que falta es teclear el código.
    """
    assert not issubclass(CodigoNoConsta, hermana)
    assert not issubclass(hermana, CodigoNoConsta)


def test_f034_r28_errores_el_docstring_dice_en_que_se_diferencia():
    """R28 · el porqué vive al lado del error, no solo en la spec.

    Quien se encuentre este error dentro de seis meses lee el módulo, no
    `specs/F-034-archivo-persistido-en-erp/design.md`. Nombra las tres
    hermanas de las que se distingue y la ficha que lo introduce.
    """
    documentacion = CodigoNoConsta.__doc__ or ""

    for hermana in HERMANAS_DE_409:
        assert hermana.__name__ in documentacion
    assert "F-034" in documentacion


def test_f034_r28_errores_el_modulo_lo_cuenta_entre_los_409():
    """R28 · la cabecera de `errores.py` reparte cada error en su familia.

    Es el mapa que lee quien llega al módulo: si `CodigoNoConsta` no aparece
    ahí, el reparto 400/409/503 que el borde respeta queda incompleto.
    """
    from domain.models import errores

    assert "CodigoNoConsta" in (errores.__doc__ or "")


# --------------------------------------------------------------------------
# Bloque 1 · T3 · `codigos_del_parte.py`, la pieza compartida
# --------------------------------------------------------------------------


def _guardados(
    obra: str = OBRA_GUARDADA, incidencia: str = INCIDENCIA_GUARDADA
) -> CodigosDelParte:
    return CodigosDelParte(codigo_obra=obra, numero_incidencia=incidencia)


def _situacion(
    obra: str = OBRA_GUARDADA, incidencia: str = INCIDENCIA_GUARDADA
) -> SituacionParte:
    """La situación que devolvería la base: veredicto apto con **esos** códigos."""
    return SituacionParte(
        validacion=replace(
            veredicto_apto(hash_parte=HASH),
            codigo_obra=obra,
            numero_incidencia=incidencia,
        )
    )


def test_f034_codigos_del_parte_es_inmutable():
    """`CodigosDelParte` no se puede retocar por el camino (F-031 R11, conservado)."""
    codigos = _guardados()

    with pytest.raises(FrozenInstanceError):
        codigos.numero_incidencia = "RS26.09/0999"  # type: ignore[misc]


def test_f034_r10_codigos_guardados_salen_de_la_situacion_ya_leida():
    """R8, R10 · los dos códigos guardados, de `ctx.situacion.validacion`.

    `codigos_guardados` solo recibe el contexto: no tiene con qué hacer una
    consulta más, que es la mitad de R10 que se puede ver en la firma.
    """
    ctx = contexto_apto(hash_parte=HASH)
    ctx.situacion = _situacion(obra="0677", incidencia="RS26.09/0178")

    assert codigos_guardados(ctx) == CodigosDelParte(
        codigo_obra="0677", numero_incidencia="RS26.09/0178"
    )


@pytest.mark.parametrize(
    "situacion",
    (None, SituacionParte()),
    ids=("sin situacion", "situacion sin veredicto"),
)
def test_f034_r15_codigos_guardados_sin_veredicto_son_dos_vacios(situacion):
    """Sin `validacion`, dos cadenas vacías y **ningún** error aquí (F-031 R7).

    Quien decide que eso es un error es quien los va a usar: el nombrado en
    archivo, `exigir_codigos_completos` en el gráfico y el cierre.
    """
    ctx = contexto_apto(hash_parte=HASH)
    ctx.situacion = situacion

    assert codigos_guardados(ctx) == CodigosDelParte(
        codigo_obra="", numero_incidencia=""
    )


@pytest.mark.parametrize(
    ("guardados", "declarados"),
    (
        (
            _guardados(incidencia="RS26.09/0178"),
            _guardados(incidencia="RS 26.09/0178"),
        ),
        (_guardados(obra="0626"), _guardados(obra="06 26")),
        (_guardados(obra="06 26"), _guardados(obra="0626")),
    ),
    ids=(
        "incidencia con espacio",
        "obra con espacio declarada",
        "obra con espacio guardada",
    ),
)
def test_f034_r12_codigos_el_cotejo_normaliza_los_dos_lados(guardados, declarados):
    """R12 · `RS 26.09/0178` ≡ `RS26.09/0178` y `06 26` ≡ `0626`: no hay 409."""
    exigir_codigos_declarados(declarados, guardados, y_por_eso=Y_POR_ESO)
    exigir_codigos_declarados(
        declarados, guardados, solo_incidencia=True, y_por_eso=Y_POR_ESO
    )


@pytest.mark.parametrize(
    ("declarados", "etiqueta", "declarado", "guardado"),
    (
        (_guardados(obra="0999"), "el código de obra", "0999", OBRA_GUARDADA),
        (
            _guardados(incidencia="RS26.09/0999"),
            "el nº de incidencia",
            "RS26.09/0999",
            INCIDENCIA_GUARDADA,
        ),
    ),
    ids=("otra obra", "otra incidencia"),
)
def test_f034_r11_codigos_divergentes_dicen_cual_y_llevan_la_cola(
    declarados, etiqueta, declarado, guardado
):
    """R11 · lo declarado no es lo guardado: `CodigosNoCoinciden`, diciendo cuál.

    El mensaje es la parte fija —qué campo, con los dos valores— seguida de
    `y_por_eso`, que es lo que cada endpoint pone de su cosecha (§2.5 del
    informe del implementer, aprobado por el humano el 2026-09-23).
    """
    with pytest.raises(CodigosNoCoinciden) as error:
        exigir_codigos_declarados(declarados, _guardados(), y_por_eso=Y_POR_ESO)

    assert error.value.motivo == (
        f"{etiqueta} de la petición («{declarado}») no es el que consta "
        f"guardado para este parte («{guardado}»), así que {Y_POR_ESO}"
    )


def test_f034_r11_codigos_si_fallan_los_dos_se_nombra_primero_la_obra():
    """El orden de F-031 se conserva: obra primero, incidencia después."""
    with pytest.raises(CodigosNoCoinciden) as error:
        exigir_codigos_declarados(
            _guardados(obra="0999", incidencia="RS26.09/0999"),
            _guardados(),
            y_por_eso=Y_POR_ESO,
        )

    assert error.value.motivo.startswith("el código de obra de la petición")


def test_f034_r19_codigos_sin_declarados_no_hay_nada_que_cotejar():
    """R19 · sin cuerpo no hay cotejo, y eso no abre nada: se usa lo guardado."""
    exigir_codigos_declarados(None, _guardados(), y_por_eso=Y_POR_ESO)
    exigir_codigos_declarados(
        None, _guardados(), solo_incidencia=True, y_por_eso=Y_POR_ESO
    )


def test_f034_r16_codigos_solo_incidencia_no_coteja_la_obra():
    """R16 · el cuerpo de `/api/cerrar` no trae `codigo_obra`: no se le exige."""
    exigir_codigos_declarados(
        _guardados(obra=""), _guardados(), solo_incidencia=True, y_por_eso=Y_POR_ESO
    )


def test_f034_r16_codigos_solo_incidencia_si_coteja_la_incidencia():
    """R16 · con `solo_incidencia`, la incidencia se sigue cotejando entera."""
    with pytest.raises(CodigosNoCoinciden) as error:
        exigir_codigos_declarados(
            _guardados(obra="", incidencia="RS26.09/0999"),
            _guardados(),
            solo_incidencia=True,
            y_por_eso=Y_POR_ESO,
        )

    assert error.value.motivo.startswith("el nº de incidencia de la petición")


def test_f034_r16_codigos_por_defecto_se_cotejan_los_dos():
    """R16 · sin `solo_incidencia`, una obra declarada vacía **no** pasa.

    Es el valor por defecto el que protege `/api/adjuntar` y `/api/archivar`:
    si por defecto se saltara la obra, un cuerpo sin obra abriría la puerta.
    """
    with pytest.raises(CodigosNoCoinciden):
        exigir_codigos_declarados(
            _guardados(obra=""), _guardados(), y_por_eso=Y_POR_ESO
        )


@pytest.mark.parametrize(
    ("guardados", "etiqueta"),
    (
        (_guardados(obra=""), "el código de obra"),
        (_guardados(obra="  "), "el código de obra"),
        (_guardados(incidencia=""), "el nº de incidencia"),
        (_guardados(incidencia=" \t"), "el nº de incidencia"),
        (_guardados(obra="", incidencia=""), "el código de obra"),
    ),
    ids=(
        "obra vacia",
        "obra en blanco",
        "incidencia vacia",
        "incidencia en blanco",
        "las dos",
    ),
)
def test_f034_r15_codigos_incompletos_dicen_cual_falta(guardados, etiqueta):
    """R15 · lo guardado incompleto: `CodigoNoConsta`, diciendo **cuál** falta.

    «Vacío» es lo que `normalizar_codigo` deja vacío —el mismo criterio que el
    nombrado—, así que un código de solo blancos también falta. El mensaje dice
    qué hay que hacer —teclearlo y guardarlo— sea cual sea el endpoint, y lleva
    la cola del que llama.
    """
    with pytest.raises(CodigoNoConsta) as error:
        exigir_codigos_completos(guardados, y_por_eso=Y_POR_ESO)

    assert error.value.motivo == (
        f"no consta guardado {etiqueta} de este parte, así que {Y_POR_ESO}: "
        f"hay que teclearlo en el parte y guardarlo (POST /api/parte) antes de "
        f"volver a intentarlo"
    )


def test_f034_r15_codigos_completos_no_levanta():
    """R15 · con los dos códigos guardados no hay nada que decir."""
    exigir_codigos_completos(_guardados(), y_por_eso=Y_POR_ESO)


def test_f034_r16_codigos_completos_solo_incidencia_no_exige_la_obra():
    """R16 · en el cierre la obra no decide nada, y no se exige."""
    exigir_codigos_completos(
        _guardados(obra=""), solo_incidencia=True, y_por_eso=Y_POR_ESO
    )

    with pytest.raises(CodigoNoConsta) as error:
        exigir_codigos_completos(
            _guardados(obra="", incidencia=""),
            solo_incidencia=True,
            y_por_eso=Y_POR_ESO,
        )
    assert "el nº de incidencia" in error.value.motivo


# --------------------------------------------------------------------------
# R26 · archivar no cambia ni una regla ni un byte al usar la pieza compartida
# --------------------------------------------------------------------------

#: El mensaje de `POST /api/archivar` **tal y como lo dejó F-031**, copiado a
#: mano de `paso_archivo.py` antes de F-034 (commit `633a8fb`). Si alguien lo
#: retoca al compartir la pieza, este test lo ve.
MENSAJE_DE_ARCHIVAR_DE_F031 = (
    "{etiqueta} de la petición («{declarado}») no es el que consta "
    "guardado para este parte («{guardado}»), así que **no se ha "
    "archivado nada**: el nombre y la carpeta salen de lo guardado. "
    "Hay que guardar la corrección con POST /api/parte y volver a "
    "archivar"
)


@pytest.mark.parametrize(
    ("declarados", "etiqueta", "declarado", "guardado"),
    (
        (_guardados(obra="0999"), "el código de obra", "0999", OBRA_GUARDADA),
        (
            _guardados(incidencia="RS26.09/0999"),
            "el nº de incidencia",
            "RS26.09/0999",
            INCIDENCIA_GUARDADA,
        ),
    ),
    ids=("otra obra", "otra incidencia"),
)
def test_f034_r26_codigos_el_mensaje_de_archivar_es_byte_a_byte_el_de_f031(
    declarados, etiqueta, declarado, guardado
):
    """R26 · desde `paso_archivo`, el 409 dice exactamente lo mismo que ayer.

    Se ejercita el paso entero, no la pieza suelta: lo que se afirma es que
    **archivar** sigue diciendo lo mismo, y de paso que no llega a tocar nada.
    """
    biblioteca = BibliotecaFalsa()
    archivador = ArchivoPortFalso(biblioteca)
    repositorio = RepositorioFalso(situacion=_situacion())

    with pytest.raises(CodigosNoCoinciden) as error:
        paso_archivo(
            contexto_apto(hash_parte=HASH),
            archivador,
            repositorio,
            carpeta_base=CARPETA_BASE,
            ahora=datetime(2026, 9, 23, 10, 0, tzinfo=UTC),
            codigos_declarados=declarados,
        )

    assert error.value.motivo == MENSAJE_DE_ARCHIVAR_DE_F031.format(
        etiqueta=etiqueta, declarado=declarado, guardado=guardado
    )
    assert archivador.llamadas == []
    assert repositorio.llamadas_guardar_archivo == 0


def test_f034_r26_codigos_archivo_y_su_endpoint_usan_la_pieza_compartida():
    """R26, D-2 · una sola `CodigosDelParte`, no una copia por paso.

    El paso de archivo y su endpoint tienen que usar **la misma** clase que el
    módulo compartido: dos clases con el mismo nombre no se comparan iguales, y
    el cotejo se rompería en silencio el día que alguien mezclara una y otra.
    Y los dos privados de F-031 ya no existen: la regla vive en un solo sitio.
    """
    assert modulo_paso_archivo.CodigosDelParte is CodigosDelParte
    assert modulo_archivar.CodigosDelParte is CodigosDelParte
    assert not hasattr(modulo_paso_archivo, "_codigos_guardados")
    assert not hasattr(modulo_paso_archivo, "_exigir_codigos_declarados")
