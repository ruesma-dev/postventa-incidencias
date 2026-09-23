# services/postventa-api/tests/test_f034_codigos_en_el_erp.py
"""Los dos códigos con los que se escribe en el ERP salen de lo guardado (F-034).

Este fichero crece por bloques (`tasks.md`):

- **Bloque 1**: las piezas compartidas. El error nuevo,
  `CodigoNoConsta` (R15, R28), y en qué se diferencia de sus tres hermanas
  de 409; y el módulo `application/pipelines/codigos_del_parte.py`, con el
  cotejo normalizado (R12), su variante de solo la incidencia (R16), la
  exigencia de lo guardado completo (R15) y la prueba de que el mensaje de
  `POST /api/archivar` no ha cambiado ni un byte al moverlo (R26).
- **Bloque 2**: `POST /api/adjuntar` y `paso_grafico` con los cinco puertos
  inyectados (R8, R11–R17, R19, R20, R24, R27, R34, R35). El mundo —lo
  guardado y lo declarado, escritos aparte— sale de `tests/utiles_circuito.py`.
- **Bloque 3**: `POST /api/cerrar` y `paso_cierre` con los cuatro puertos
  inyectados (R9, R11–R17, R19, R20, R27, R34, R35; R16 con solo la
  incidencia), y **H-4**: un nº de incidencia guardado sin ningún tramo es lo
  guardado incompleto → 409 `CodigoNoConsta` en gráfico y cierre, con archivar
  intacto (decisión del líder del 2026-09-23 dentro de D-4).

**Sin red, sin base de datos, sin IA y sin tocar el ERP** (R37).
"""

from __future__ import annotations

import json
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime

import pytest
from application.pipelines import codigos_del_parte as modulo_codigos_del_parte
from application.pipelines import paso_archivo as modulo_paso_archivo
from application.pipelines.codigos_del_parte import (
    CodigosDelParte,
    codigos_guardados,
    exigir_codigos_completos,
    exigir_codigos_declarados,
)
from application.pipelines.contexto_parte import ContextoParte
from application.pipelines.paso_archivo import paso_archivo
from domain.models.errores import (
    CodigoNoConsta,
    CodigosNoCoinciden,
    CuerpoDeCierreInvalido,
    CuerpoDeGraficoInvalido,
    NombradoImposible,
    ParteNoApto,
    ParteNoArchivado,
)
from domain.models.estado import SituacionParte
from domain.models.persistencia import EstadoArchivo
from interface_adapters.api import archivar as modulo_archivar

from tests.utiles_circuito import (
    AHORA,
    CORREO,
    OID,
    PDF,
    MundoDelAdjuntar,
    MundoDelCierre,
    cuerpo_de_cierre,
    formulario,
    situacion_guardada,
)
from tests.utiles_sharepoint import (
    CARPETA_BASE,
    ArchivoPortFalso,
    BibliotecaFalsa,
    RepositorioFalso,
    contexto_apto,
    parte_de_prueba,
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


def test_f034_r11_codigos_si_las_dos_listas_no_casan_falla_en_vez_de_cotejar_a_medias(
    monkeypatch,
):
    """El cotejo nunca se da por bueno mirando **menos** códigos de los que toca.

    `exigir_codigos_declarados` empareja lo declarado con lo guardado con un
    `zip(..., strict=True)` sobre dos llamadas a `_a_mirar`. Hoy las dos listas
    salen siempre del mismo largo, así que el `strict` no se nota; está para el
    día en que alguien toque `_a_mirar` —o empareje otra cosa— y las dos dejen
    de casar. Sin él, `zip` se callaría en la más corta y el código que se
    quedara fuera **no se cotejaría**: un nº de incidencia distinto pasaría el
    1 bis y se escribiría con lo guardado sin haber avisado a nadie de que el
    cuerpo no cuadraba (R11). Con él, revienta.

    Se fuerza la asimetría sustituyendo `_a_mirar` por uno que, para lo
    declarado, devuelve solo la obra; la incidencia declarada es otra. Lo que
    se exige es que **no pase en silencio**. Mata el mutante `strict=False` de
    la campaña de T15 (`progress/mutacion_F-034.md`).
    """
    declarados = _guardados(incidencia="RS26.09/0999")
    guardados = _guardados()
    original = modulo_codigos_del_parte._a_mirar

    def asimetrico(codigos, *, solo_incidencia):
        pares = original(codigos, solo_incidencia=solo_incidencia)
        return pares[:1] if codigos is declarados else pares

    monkeypatch.setattr(modulo_codigos_del_parte, "_a_mirar", asimetrico)

    with pytest.raises(ValueError, match="zip"):
        exigir_codigos_declarados(declarados, guardados, y_por_eso=Y_POR_ESO)


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


# ==========================================================================
# Bloque 2 · T4 · `POST /api/adjuntar` con los puertos inyectados (R8–R19)
# ==========================================================================
#
# Todos los casos de abajo recorren el **handler de verdad**
# (`adjuntar_grafico`) o la **ruta de verdad** (`function_app.adjuntar`) con
# los cinco puertos inyectados, así que la puerta de entorno no se evalúa y el
# 503 no puede tapar el 409 que se quiere ver (D-6 de `requirements.md`). Cada
# caso negativo tiene su control positivo con el mismo mundo.

#: Un número de incidencia que **no** es el guardado: otra reclamación.
OTRA_INCIDENCIA = "RS26.09/0999"
#: El DNI del parte de ejemplo (inventado): si sale en un motivo, R34 falla.
DNI_INVENTADO = "00000000T"


def _mundo_del_adjuntar(
    obra: str = OBRA_GUARDADA,
    incidencia: str = INCIDENCIA_GUARDADA,
    *,
    estado_archivo: EstadoArchivo | None = EstadoArchivo.ARCHIVADO,
) -> MundoDelAdjuntar:
    """Parte apto y archivado **según la base**, con esos códigos guardados."""
    return MundoDelAdjuntar(
        situacion_guardada(
            hash_parte=HASH,
            codigo_obra=obra,
            numero_incidencia=incidencia,
            estado_archivo=estado_archivo,
        )
    )


def _declarado(
    obra: str = OBRA_GUARDADA, incidencia: str = INCIDENCIA_GUARDADA, **cambios: str
) -> dict[str, str]:
    """El cuerpo de la petición: **lo declarado**, escrito aparte a propósito."""
    return formulario(
        hash_parte=HASH, codigo_obra=obra, numero_incidencia=incidencia, **cambios
    )


def test_f034_r11_control_positivo_mismos_codigos_si_adjunta():
    """El control de todo el bloque: mismos códigos, mismo mundo → se adjunta.

    Si esto no pasara, los 409 de abajo no demostrarían nada: podrían salir de
    cualquier otra cosa del mundo.
    """
    mundo = _mundo_del_adjuntar()

    respuesta = mundo.adjuntar(_declarado(commit="true", confirmado="true"))

    assert respuesta["estado"] == "adjuntado"
    assert mundo.erp.lecturas == [INCIDENCIA_GUARDADA]
    assert mundo.graficos.orden == [False, True]


@pytest.mark.parametrize("commit", ["", "true"], ids=["dry_run", "commit"])
def test_f034_r11_adjuntar_otra_incidencia_en_el_cuerpo_no_toca_el_erp(commit):
    """R8, R11, R13, R14 · **caso central**: el cuerpo nombra otra reclamación.

    Guardado `RS26.08/0123`, cuerpo `RS26.09/0999` → 409 y **cero** llamadas:
    ni se resuelve el login, ni se lee ninguna reclamación, ni se llama a la
    pasarela, ni se escribe ni se consulta la traza del gráfico. **También en
    dry-run** (R14): enseñar la reclamación que nombra un cuerpo que miente es
    enseñar otra cosa.
    """
    mundo = _mundo_del_adjuntar()

    with pytest.raises(CodigosNoCoinciden) as fallo:
        mundo.adjuntar(
            _declarado(incidencia=OTRA_INCIDENCIA, commit=commit, confirmado="true")
        )

    motivo = fallo.value.motivo
    assert motivo.startswith("el nº de incidencia de la petición")
    assert f"«{OTRA_INCIDENCIA}»" in motivo
    assert f"«{INCIDENCIA_GUARDADA}»" in motivo
    assert "no se ha adjuntado nada" in motivo
    assert "POST /api/parte" in motivo
    assert mundo.nada_ha_tocado_el_erp()


def test_f034_r16_adjuntar_otra_obra_en_el_cuerpo_tampoco_pasa():
    """R11, R16 · en `/adjuntar` se cotejan **los dos**: la obra también.

    La obra decide el nombre con el que el parte cuelga de la reclamación, y
    ese nombre es el que cruza con SharePoint.
    """
    mundo = _mundo_del_adjuntar()

    with pytest.raises(CodigosNoCoinciden) as fallo:
        mundo.adjuntar(_declarado(obra="0999"))

    assert fallo.value.motivo.startswith("el código de obra de la petición")
    assert "«0999»" in fallo.value.motivo
    assert mundo.nada_ha_tocado_el_erp()


@pytest.mark.parametrize(
    ("obra", "incidencia"),
    [("06 26", INCIDENCIA_GUARDADA), (OBRA_GUARDADA, "RS 26.08/0123")],
    ids=["obra con espacio", "incidencia con espacio"],
)
def test_f034_r12_adjuntar_el_cotejo_normaliza_y_no_da_409(obra, incidencia):
    """R12 · `06 26` ≡ `0626` y `RS 26.08/0123` ≡ `RS26.08/0123`.

    El front manda lo que devuelve `valorDeCampo`, que solo hace `trim()`, y la
    base guarda lo que F-032 saneó. Con un cotejo literal, el caso que costó un
    cierre a mano el 2026-09-17 sería un 409 diario.
    """
    mundo = _mundo_del_adjuntar()

    respuesta = mundo.adjuntar(_declarado(obra=obra, incidencia=incidencia))

    assert respuesta["estado"] == "dry_run_ok"
    assert mundo.erp.lecturas == [INCIDENCIA_GUARDADA]


@pytest.mark.parametrize(
    ("obra", "incidencia", "etiqueta"),
    [
        (OBRA_GUARDADA, "", "el nº de incidencia"),
        ("", INCIDENCIA_GUARDADA, "el código de obra"),
    ],
    ids=["sin incidencia guardada", "sin obra guardada"],
)
def test_f034_r15_adjuntar_sin_codigo_guardado_es_409_y_no_usa_el_del_cuerpo(
    obra, incidencia, etiqueta
):
    """R15 · lo guardado está incompleto: 409 diciendo **cuál** falta.

    El cuerpo trae los dos códigos, y **no** se usan para rellenar el hueco:
    eso volvería a dejar decidir al cuerpo (R19). Tampoco es un 400: la
    petición está bien formada, lo que está incompleto es lo guardado.

    Y sale `CodigoNoConsta`, no `CodigosNoCoinciden`, aunque lo declarado y lo
    guardado difieran: lo que hay que hacer es teclear el código que falta, y
    eso es lo que el mensaje tiene que decir (por eso en 1 bis la exigencia de
    lo completo va antes que el cotejo).
    """
    mundo = _mundo_del_adjuntar(obra, incidencia)

    with pytest.raises(CodigoNoConsta) as fallo:
        mundo.adjuntar(_declarado())

    assert fallo.value.motivo.startswith(f"no consta guardado {etiqueta}")
    assert "no se ha adjuntado nada" in fallo.value.motivo
    assert "POST /api/parte" in fallo.value.motivo
    assert mundo.nada_ha_tocado_el_erp()


@pytest.mark.parametrize(
    "declarados",
    [None, CodigosDelParte(codigo_obra=OBRA_GUARDADA, numero_incidencia="")],
    ids=["sin declarados", "declarado vacío"],
)
def test_f034_r15_grafico_sin_incidencia_guardada_no_llega_al_login(declarados):
    """R15 · vacío guardado y vacío (o nada) declarado, y aun así no pasa.

    Desde el borde no se llega aquí —un campo vacío es el 400 de R17—, pero el
    paso no puede fiarse de eso. El cotejo da por iguales dos vacíos
    (`es_el_mismo_codigo`), así que lo que tiene que cortar es la exigencia de
    lo guardado completo. Sin ella, el paso llegaría hasta el
    `CuerpoDeCierreInvalido` de `_codigo_de_incidencia` —un 400 que manda a
    mirar el cuerpo— **después** de haber resuelto el login contra el ERP.
    """
    from application.pipelines.paso_grafico import paso_grafico

    mundo = _mundo_del_adjuntar(OBRA_GUARDADA, "")
    ctx = ContextoParte(parte=parte_de_prueba(hash_parte=HASH, contenido=PDF))

    with pytest.raises(CodigoNoConsta):
        paso_grafico(
            ctx,
            mundo.erp,
            mundo.graficos,
            mundo.repositorio,
            mundo.usuarios,
            mundo.preferencias,
            commit=False,
            confirmado=False,
            usuario_oid=OID,
            correo=CORREO,
            codigos_declarados=declarados,
            gratipide=35,
            tope_bytes=10 * 1024 * 1024,
            ahora=AHORA,
        )

    assert mundo.nada_ha_tocado_el_erp()


def test_f034_r13_adjuntar_el_cotejo_va_antes_que_la_puerta_de_archivo():
    """R13, `design.md` §4.1 · 1 bis antes que 2: primero **sobre qué** parte.

    Con los códigos cruzados **y** sin archivo guardado, el error es el de los
    códigos: resolver primero la identidad y después el estado, como hace
    `paso_archivo` desde F-031.
    """
    mundo = _mundo_del_adjuntar(estado_archivo=None)

    with pytest.raises(CodigosNoCoinciden):
        mundo.adjuntar(_declarado(incidencia=OTRA_INCIDENCIA))

    assert mundo.nada_ha_tocado_el_erp()


def test_f034_r13_adjuntar_el_cotejo_va_antes_que_mirar_el_fichero():
    """R13 · el cotejo va antes que el tope y la firma del PDF (punto 3)."""
    mundo = _mundo_del_adjuntar()

    with pytest.raises(CodigosNoCoinciden):
        mundo.adjuntar(
            _declarado(incidencia=OTRA_INCIDENCIA), contenido=b"PK\x03\x04 un zip"
        )

    assert mundo.nada_ha_tocado_el_erp()


def test_f034_r20_adjuntar_la_puerta_de_aptitud_sigue_yendo_la_primera():
    """R20, R21 · la aptitud va antes que el cotejo: sin ella no hay situación.

    Un parte sin veredicto guardado y con los códigos cruzados sale por
    `ParteNoApto`, como antes de F-034: el cotejo se intercala **después**.
    """
    mundo = MundoDelAdjuntar(SituacionParte())

    with pytest.raises(ParteNoApto):
        mundo.adjuntar(_declarado(incidencia=OTRA_INCIDENCIA))

    assert mundo.nada_ha_tocado_el_erp()


def test_f034_r17_adjuntar_un_cuerpo_sin_codigo_sigue_siendo_400():
    """R17 · una petición mal formada no es un conflicto de estado."""
    mundo = _mundo_del_adjuntar()

    with pytest.raises(CuerpoDeGraficoInvalido) as fallo:
        mundo.adjuntar(_declarado(incidencia=""))

    assert "numero_incidencia" in fallo.value.motivo
    assert mundo.nada_ha_tocado_el_erp()


def test_f034_r24_adjuntar_un_codigo_guardado_imposible_es_nombrado_imposible():
    """R24 · `NombradoImposible` sigue alcanzable, ahora con lo **guardado**.

    Un código guardado con un carácter que SharePoint no admite no se sanea:
    no se adjunta y se dice por qué. Y no llega a la pasarela.
    """
    mundo = _mundo_del_adjuntar(obra="06*26")

    with pytest.raises(NombradoImposible):
        mundo.adjuntar(_declarado(obra="06*26"))

    assert mundo.graficos.llamadas == []


def test_f034_r8_adjuntar_el_handler_pasa_lo_declarado_solo_para_cotejar(
    monkeypatch,
):
    """R8, R19, D-7 · el borde entrega los dos códigos **como declarados**.

    Ni `numero_incidencia` ni `codigo_obra` llegan ya al paso como parámetros
    sueltos: van juntos en `codigos_declarados`, tal y como vinieron, y solo
    sirven para cotejar.
    """
    from interface_adapters.api import adjuntar as modulo_adjuntar

    opciones: list[dict] = []

    def espia(_ctx, *_puertos, **recibidas):
        opciones.append(recibidas)
        raise CodigosNoCoinciden("parado por el espía del test")

    monkeypatch.setattr(modulo_adjuntar, "paso_grafico", espia)

    with pytest.raises(CodigosNoCoinciden):
        _mundo_del_adjuntar().adjuntar(_declarado(obra="06 26"))

    assert opciones[0]["codigos_declarados"] == CodigosDelParte(
        codigo_obra="06 26", numero_incidencia=INCIDENCIA_GUARDADA
    )
    assert "numero_incidencia" not in opciones[0]
    assert "codigo_obra" not in opciones[0]


def test_f034_r19_paso_grafico_ya_no_acepta_los_codigos_sueltos():
    """R19, D-7 · la firma **declara** la asimetría: lo declarado entra por un
    sitio y lo guardado sale de `ctx`.

    Mientras existieran dos parámetros llamados `numero_incidencia` y
    `codigo_obra`, el cuerpo de la función podría volver a usarlos para nombrar
    o para buscar, y el defecto volvería sin que nadie lo notara.
    """
    import inspect

    from application.pipelines.paso_grafico import paso_grafico

    parametros = inspect.signature(paso_grafico).parameters

    assert "numero_incidencia" not in parametros
    assert "codigo_obra" not in parametros
    assert parametros["codigos_declarados"].default is None


def test_f034_r19_sin_declarados_el_grafico_escribe_con_lo_guardado():
    """R8, R19 · el camino sin cotejo **no** puede escribir en otra reclamación.

    Sin `codigos_declarados` no hay nada que cotejar, y el paso lee la
    reclamación y compone el nombre con los códigos **guardados**, los mismos
    que la puerta de aptitud acaba de aprobar.
    """
    from application.pipelines.paso_grafico import paso_grafico
    from domain.models.nombrado import nombre_de_archivo

    mundo = _mundo_del_adjuntar()
    ctx = ContextoParte(parte=parte_de_prueba(hash_parte=HASH, contenido=PDF))

    paso_grafico(
        ctx,
        mundo.erp,
        mundo.graficos,
        mundo.repositorio,
        mundo.usuarios,
        mundo.preferencias,
        commit=False,
        confirmado=False,
        usuario_oid=OID,
        correo=CORREO,
        gratipide=35,
        tope_bytes=10 * 1024 * 1024,
        ahora=AHORA,
    )

    assert mundo.erp.lecturas == [INCIDENCIA_GUARDADA]
    assert mundo.graficos.ultima().nom == nombre_de_archivo(
        codigo_obra=OBRA_GUARDADA, numero_incidencia=INCIDENCIA_GUARDADA
    )


@pytest.mark.parametrize(
    ("guardados", "declarados", "error"),
    [
        (
            (OBRA_GUARDADA, INCIDENCIA_GUARDADA),
            (OBRA_GUARDADA, OTRA_INCIDENCIA),
            "CodigosNoCoinciden",
        ),
        ((OBRA_GUARDADA, ""), (OBRA_GUARDADA, INCIDENCIA_GUARDADA), "CodigoNoConsta"),
    ],
    ids=["CodigosNoCoinciden", "CodigoNoConsta"],
)
def test_f034_r27_adjuntar_por_la_ruta_los_dos_errores_nuevos_son_409(
    monkeypatch, caplog, guardados, declarados, error
):
    """R27, R35, R36 · 409 con `{"error": <motivo>}` y nada más; al log, el tipo.

    Por la ruta de verdad y con el handler de verdad: el código sale del
    `except` real. El motivo nombra los códigos y **no** va al log tal cual
    —el `except` es compartido con errores que nombran el correo—: al log va
    el tipo del error (F-012 R54).
    """
    mundo = _mundo_del_adjuntar(*guardados)

    with caplog.at_level("DEBUG"):
        respuesta = mundo.por_la_ruta(monkeypatch, _declarado(*declarados))

    assert respuesta.status_code == 409
    cuerpo = json.loads(respuesta.get_body())
    assert set(cuerpo) == {"error"}
    assert cuerpo["error"]
    assert cuerpo["error"] not in caplog.text
    assert error in caplog.text
    assert mundo.nada_ha_tocado_el_erp()


def test_f034_r34_adjuntar_el_motivo_no_lleva_nada_del_papel_salvo_los_codigos():
    """R34 · el motivo nombra obra e incidencia y **nada más** del parte.

    Ni el DNI ni la descripción del parte de ejemplo —inventados, pero con la
    forma de los de verdad— ni el correo de quien llama pueden aparecer en un
    409 de códigos.
    """
    mundo = _mundo_del_adjuntar()

    with pytest.raises(CodigosNoCoinciden) as fallo:
        mundo.adjuntar(_declarado(incidencia=OTRA_INCIDENCIA))

    assert DNI_INVENTADO not in fallo.value.motivo
    assert "Sellado" not in fallo.value.motivo
    assert CORREO not in fallo.value.motivo


def test_f034_r35_adjuntar_la_respuesta_sigue_teniendo_las_ocho_claves():
    """R35 · ni una clave más en la respuesta de `POST /api/adjuntar`."""
    respuesta = _mundo_del_adjuntar().adjuntar(_declarado())

    assert set(respuesta) == {
        "hash_parte",
        "numero_incidencia",
        "estado",
        "idempotente",
        "filas_afectadas",
        "motivo",
        "dry_run",
        "avisos",
    }


# ==========================================================================
# Bloque 3 · T8 · `POST /api/cerrar` con los puertos inyectados (R9–R19)
# ==========================================================================
#
# **Lo más grave de la feature**: aquí el número de incidencia decide **qué
# reclamación se cierra** en el ERP de producción, y un cierre en Sigrid no se
# deshace desde este circuito. Mismo patrón que el Bloque 2: handler o ruta de
# verdad con los cuatro puertos inyectados —la puerta de entorno no se evalúa y
# el 503 no puede tapar el 409—, y cada negativo con su control positivo.


def _mundo_del_cierre(
    obra: str = OBRA_GUARDADA,
    incidencia: str = INCIDENCIA_GUARDADA,
    *,
    estado_archivo: EstadoArchivo | None = EstadoArchivo.ARCHIVADO,
) -> MundoDelCierre:
    """Parte apto y archivado **según la base**, con esos códigos guardados."""
    return MundoDelCierre(
        situacion_guardada(
            hash_parte=HASH,
            codigo_obra=obra,
            numero_incidencia=incidencia,
            estado_archivo=estado_archivo,
        )
    )


def _declarado_al_cerrar(incidencia: str = INCIDENCIA_GUARDADA, **cambios) -> dict:
    """El cuerpo de `/cerrar`: **lo declarado**, sin `codigo_obra` (R16)."""
    return cuerpo_de_cierre(hash_parte=HASH, numero_incidencia=incidencia, **cambios)


def _paso_cierre_directo(mundo: MundoDelCierre, **opciones):
    """`paso_cierre` a pelo, con los puertos del mundo y un contexto mínimo."""
    from application.pipelines.paso_cierre import paso_cierre

    ctx = ContextoParte(parte=parte_de_prueba(hash_parte=HASH, contenido=b""))
    return paso_cierre(
        ctx,
        mundo.erp,
        mundo.repositorio,
        mundo.usuarios,
        mundo.preferencias,
        commit=False,
        confirmado=False,
        usuario_oid=OID,
        correo=CORREO,
        ahora=AHORA,
        **opciones,
    )


def test_f034_r9_control_positivo_mismo_numero_si_cierra():
    """El control de todo el bloque: mismo número, mismo mundo → se cierra.

    Y se cierra **la guardada**: la única lectura del ERP es la de su código.
    """
    mundo = _mundo_del_cierre()

    respuesta = mundo.cerrar(_declarado_al_cerrar(commit=True, confirmado=True))

    assert respuesta["estado"] == "cerrado"
    assert mundo.erp.lecturas == [INCIDENCIA_GUARDADA]
    assert len(mundo.erp.cierres) == 1


@pytest.mark.parametrize("commit", [False, True], ids=["dry_run", "commit"])
def test_f034_r9_cerrar_otra_incidencia_en_el_cuerpo_no_toca_el_erp(commit):
    """R9, R11, R13, R14 · **caso central de la feature**.

    Guardado `RS26.08/0123`, cuerpo `RS26.09/0999` → 409 y **cero** llamadas:
    ni se resuelve el login, ni se lee ninguna reclamación, ni se cierra nada,
    ni se escribe ninguna traza de cierre ni fila del histórico. **También en
    dry-run** (R14): enseñar el cierre de la reclamación que nombra un cuerpo
    que miente es enseñar otra cosa.
    """
    mundo = _mundo_del_cierre()

    with pytest.raises(CodigosNoCoinciden) as fallo:
        mundo.cerrar(
            _declarado_al_cerrar(OTRA_INCIDENCIA, commit=commit, confirmado=True)
        )

    motivo = fallo.value.motivo
    assert motivo.startswith("el nº de incidencia de la petición")
    assert f"«{OTRA_INCIDENCIA}»" in motivo
    assert f"«{INCIDENCIA_GUARDADA}»" in motivo
    assert "no se ha cerrado nada" in motivo
    assert "POST /api/parte" in motivo
    assert mundo.nada_ha_tocado_el_erp()


def test_f034_r12_cerrar_el_cotejo_normaliza_y_no_da_409():
    """R12 · `RS 26.08/0123` ≡ `RS26.08/0123`: el caso del 2026-09-17 no es un 409."""
    mundo = _mundo_del_cierre()

    respuesta = mundo.cerrar(_declarado_al_cerrar("RS 26.08/0123"))

    assert respuesta["estado"] == "dry_run_ok"
    assert mundo.erp.lecturas == [INCIDENCIA_GUARDADA]


@pytest.mark.parametrize("obra", ["", "0999"], ids=["sin obra guardada", "otra obra"])
def test_f034_r16_cerrar_no_coteja_ni_exige_la_obra(obra):
    """R16 · el cuerpo de `/cerrar` no trae `codigo_obra` y el cotejo no lo exige.

    Con la obra guardada vacía —o cualquiera— el cierre sigue: allí la obra no
    decide nada. Exigirla daría un 409 sin ninguna escritura que evitar.
    """
    mundo = _mundo_del_cierre(obra=obra)

    respuesta = mundo.cerrar(_declarado_al_cerrar())

    assert "codigo_obra" not in _declarado_al_cerrar()
    assert respuesta["estado"] == "dry_run_ok"
    assert mundo.erp.lecturas == [INCIDENCIA_GUARDADA]


def test_f034_r15_cerrar_sin_incidencia_guardada_es_409_y_no_usa_la_del_cuerpo():
    """R15 · lo guardado está incompleto: 409 diciendo cuál falta, sin rellenarlo.

    El cuerpo trae un número bien formado y **no** se usa para tapar el hueco:
    eso volvería a dejar que el cuerpo eligiera qué reclamación se cierra.
    """
    mundo = _mundo_del_cierre(incidencia="")

    with pytest.raises(CodigoNoConsta) as fallo:
        mundo.cerrar(_declarado_al_cerrar(commit=True, confirmado=True))

    assert fallo.value.motivo.startswith("no consta guardado el nº de incidencia")
    assert "no se ha cerrado nada" in fallo.value.motivo
    assert "POST /api/parte" in fallo.value.motivo
    assert mundo.nada_ha_tocado_el_erp()


@pytest.mark.parametrize(
    "declarados",
    [None, CodigosDelParte(codigo_obra="", numero_incidencia="")],
    ids=["sin declarados", "declarado vacío"],
)
def test_f034_r15_paso_cierre_sin_incidencia_guardada_no_llega_al_login(declarados):
    """R15 · vacío guardado y vacío (o nada) declarado: `CodigoNoConsta`, no un 400.

    El cotejo da por iguales dos vacíos, así que lo que corta es la exigencia
    de lo guardado completo, antes del login contra el ERP.
    """
    mundo = _mundo_del_cierre(incidencia="")

    with pytest.raises(CodigoNoConsta):
        _paso_cierre_directo(mundo, codigos_declarados=declarados)

    assert mundo.nada_ha_tocado_el_erp()


def test_f034_r13_cerrar_el_cotejo_va_antes_que_la_puerta_de_archivo():
    """R13, `design.md` §5 · 1 bis antes que 2: primero **qué** reclamación."""
    mundo = _mundo_del_cierre(estado_archivo=None)

    with pytest.raises(CodigosNoCoinciden):
        mundo.cerrar(_declarado_al_cerrar(OTRA_INCIDENCIA))

    assert mundo.nada_ha_tocado_el_erp()


def test_f034_r20_cerrar_la_puerta_de_aptitud_sigue_yendo_la_primera():
    """R20, R21 · sin veredicto guardado sale `ParteNoApto`, como antes de F-034."""
    mundo = MundoDelCierre(SituacionParte())

    with pytest.raises(ParteNoApto):
        mundo.cerrar(_declarado_al_cerrar(OTRA_INCIDENCIA))

    assert mundo.nada_ha_tocado_el_erp()


def test_f034_r17_cerrar_un_cuerpo_sin_numero_sigue_siendo_400():
    """R17 · una petición mal formada no es un conflicto de estado."""
    mundo = _mundo_del_cierre()

    with pytest.raises(CuerpoDeCierreInvalido) as fallo:
        mundo.cerrar(_declarado_al_cerrar(""))

    assert "numero_incidencia" in fallo.value.motivo
    assert mundo.nada_ha_tocado_el_erp()


def test_f034_r9_cerrar_el_handler_pasa_lo_declarado_solo_para_cotejar(monkeypatch):
    """R9, R19, D-7 · el borde entrega el número **como declarado**, tal cual vino.

    Ni un `numero_incidencia` suelto: va dentro de `codigos_declarados`, y
    solo sirve para cotejar.
    """
    from interface_adapters.api import cerrar as modulo_cerrar

    opciones: list[dict] = []

    def espia(_ctx, *_puertos, **recibidas):
        opciones.append(recibidas)
        raise CodigosNoCoinciden("parado por el espía del test")

    monkeypatch.setattr(modulo_cerrar, "paso_cierre", espia)

    with pytest.raises(CodigosNoCoinciden):
        _mundo_del_cierre().cerrar(_declarado_al_cerrar("RS 26.08/0123"))

    declarados = opciones[0]["codigos_declarados"]
    assert isinstance(declarados, CodigosDelParte)
    assert declarados.numero_incidencia == "RS 26.08/0123"
    assert "numero_incidencia" not in opciones[0]


def test_f034_r19_paso_cierre_ya_no_acepta_el_numero_suelto():
    """R19, D-7 · la firma del cierre **declara** la asimetría, como la del gráfico."""
    import inspect

    from application.pipelines.paso_cierre import paso_cierre

    parametros = inspect.signature(paso_cierre).parameters

    assert "numero_incidencia" not in parametros
    assert parametros["codigos_declarados"].default is None


def test_f034_r19_sin_declarados_el_cierre_lee_la_reclamacion_guardada():
    """R9, R19 · el camino sin cotejo **no** puede cerrar otra reclamación."""
    mundo = _mundo_del_cierre()

    ctx = _paso_cierre_directo(mundo)

    assert mundo.erp.lecturas == [INCIDENCIA_GUARDADA]
    assert ctx.cierre.estado.value == "dry_run_ok"


def test_f034_r16_paso_cierre_con_declarados_coteja_solo_la_incidencia():
    """R16 · desde el paso: la obra declarada no cuenta, la incidencia sí."""
    mundo = _mundo_del_cierre()

    _paso_cierre_directo(
        mundo,
        codigos_declarados=CodigosDelParte(
            codigo_obra="9999", numero_incidencia=INCIDENCIA_GUARDADA
        ),
    )
    assert mundo.erp.lecturas == [INCIDENCIA_GUARDADA]

    otro = _mundo_del_cierre()
    with pytest.raises(CodigosNoCoinciden):
        _paso_cierre_directo(
            otro,
            codigos_declarados=CodigosDelParte(
                codigo_obra=OBRA_GUARDADA, numero_incidencia=OTRA_INCIDENCIA
            ),
        )
    assert otro.nada_ha_tocado_el_erp()


@pytest.mark.parametrize(
    ("incidencia_guardada", "declarada", "error"),
    [
        (INCIDENCIA_GUARDADA, OTRA_INCIDENCIA, "CodigosNoCoinciden"),
        ("", INCIDENCIA_GUARDADA, "CodigoNoConsta"),
    ],
    ids=["CodigosNoCoinciden", "CodigoNoConsta"],
)
def test_f034_r27_cerrar_por_la_ruta_los_dos_errores_nuevos_son_409(
    monkeypatch, caplog, incidencia_guardada, declarada, error
):
    """R27, R35, R36 · 409 con `{"error": <motivo>}` y nada más; al log, el tipo."""
    mundo = _mundo_del_cierre(incidencia=incidencia_guardada)

    with caplog.at_level("DEBUG"):
        respuesta = mundo.por_la_ruta(monkeypatch, _declarado_al_cerrar(declarada))

    assert respuesta.status_code == 409
    cuerpo = json.loads(respuesta.get_body())
    assert set(cuerpo) == {"error"}
    assert cuerpo["error"]
    assert cuerpo["error"] not in caplog.text
    assert error in caplog.text
    assert mundo.nada_ha_tocado_el_erp()


def test_f034_r34_cerrar_el_motivo_no_lleva_nada_del_papel_salvo_el_codigo():
    """R34 · ni el DNI, ni la descripción, ni el correo en un 409 de códigos."""
    mundo = _mundo_del_cierre()

    with pytest.raises(CodigosNoCoinciden) as fallo:
        mundo.cerrar(_declarado_al_cerrar(OTRA_INCIDENCIA))

    assert DNI_INVENTADO not in fallo.value.motivo
    assert "Sellado" not in fallo.value.motivo
    assert CORREO not in fallo.value.motivo
    assert OID not in fallo.value.motivo


def test_f034_r35_cerrar_la_respuesta_sigue_teniendo_las_seis_claves():
    """R35 · ni una clave más en la respuesta de `POST /api/cerrar`."""
    respuesta = _mundo_del_cierre().cerrar(_declarado_al_cerrar())

    assert set(respuesta) == {
        "hash_parte",
        "numero_incidencia",
        "estado",
        "filas_afectadas",
        "dry_run",
        "avisos",
    }


# ==========================================================================
# H-4 · decisión del líder del 2026-09-23 (dentro de D-4, aprobada por el
# humano): un nº de incidencia **guardado** sin ningún tramo —solo
# separadores— es lo guardado incompleto → 409 `CodigoNoConsta` en gráfico y
# cierre; **archivar no cambia** (R26).
# ==========================================================================

#: Números guardados que no están vacíos pero no tienen ningún tramo:
#: `a_codigo_de_sigrid` los deja en cadena vacía. El último es un guion largo,
#: que `normalizar_codigo` traduce a guion normal.
SIN_TRAMOS = ["/", " / ", "-", "–"]


@pytest.mark.parametrize("incidencia", SIN_TRAMOS)
@pytest.mark.parametrize("solo_incidencia", [False, True])
def test_f034_h4_codigos_incidencia_sin_tramos_es_lo_guardado_incompleto(
    incidencia, solo_incidencia
):
    """H-4 · la pieza compartida: sin ningún tramo, el nº de incidencia **falta**.

    Con y sin `solo_incidencia`: los dos pasos que escriben en el ERP la
    llaman, y en los dos el número es lo que elige la reclamación. El mensaje
    es el mismo que el del número vacío, porque se arregla igual.
    """
    with pytest.raises(CodigoNoConsta) as fallo:
        exigir_codigos_completos(
            _guardados(incidencia=incidencia),
            solo_incidencia=solo_incidencia,
            y_por_eso=Y_POR_ESO,
        )

    assert fallo.value.motivo == (
        f"no consta guardado el nº de incidencia de este parte, así que "
        f"{Y_POR_ESO}: hay que teclearlo en el parte y guardarlo (POST "
        f"/api/parte) antes de volver a intentarlo"
    )


def test_f034_h4_codigos_una_obra_sin_tramos_no_es_codigo_no_consta():
    """H-4, R24 · la decisión es sobre el **nº de incidencia**, no sobre la obra.

    Una obra guardada `/` sigue su camino de siempre: en el gráfico acaba en
    `NombradoImposible` (un carácter que SharePoint no admite), que es su caso
    propio y tiene que seguir alcanzable.
    """
    exigir_codigos_completos(_guardados(obra="/"), y_por_eso=Y_POR_ESO)

    mundo = _mundo_del_adjuntar(obra="/")
    with pytest.raises(NombradoImposible):
        mundo.adjuntar(_declarado(obra="/"))
    assert mundo.graficos.llamadas == []


@pytest.mark.parametrize(
    "declarada", ["/", INCIDENCIA_GUARDADA], ids=["la misma", "una buena"]
)
def test_f034_h4_adjuntar_incidencia_guardada_sin_tramos_es_409_codigo_no_consta(
    monkeypatch, declarada
):
    """H-4 · `/api/adjuntar`: 409 `CodigoNoConsta`, no el 400 que mentía.

    Antes salía `CuerpoDeCierreInvalido` («la petición no trae el número de
    incidencia»): un 400 que mandaba a mirar el cuerpo cuando lo incompleto es
    lo guardado. Da igual lo que declare el cuerpo: lo completo va antes que el
    cotejo.
    """
    mundo = _mundo_del_adjuntar(incidencia="/")

    respuesta = mundo.por_la_ruta(monkeypatch, _declarado(incidencia=declarada))

    assert respuesta.status_code == 409
    motivo = json.loads(respuesta.get_body())["error"]
    assert motivo.startswith("no consta guardado el nº de incidencia")
    assert "no se ha adjuntado nada" in motivo
    assert mundo.nada_ha_tocado_el_erp()


@pytest.mark.parametrize(
    "declarada", ["/", INCIDENCIA_GUARDADA], ids=["la misma", "una buena"]
)
def test_f034_h4_cerrar_incidencia_guardada_sin_tramos_es_409_codigo_no_consta(
    monkeypatch, declarada
):
    """H-4 · `/api/cerrar`: lo mismo, y aquí es lo que elige qué se cierra."""
    mundo = _mundo_del_cierre(incidencia="/")

    respuesta = mundo.por_la_ruta(
        monkeypatch, _declarado_al_cerrar(declarada, commit=True, confirmado=True)
    )

    assert respuesta.status_code == 409
    motivo = json.loads(respuesta.get_body())["error"]
    assert motivo.startswith("no consta guardado el nº de incidencia")
    assert "no se ha cerrado nada" in motivo
    assert mundo.nada_ha_tocado_el_erp()


#: Lo que `POST /api/archivar` dice hoy de un nº guardado de solo separadores,
#: medido antes de H-4 (sonda del 2026-09-23 sobre `0837ef6`). Es un
#: `NombradoImposible` y tiene que seguir siéndolo, byte a byte (R26).
MENSAJE_DE_ARCHIVAR_SIN_TRAMOS = (
    "el nº de incidencia del parte es solo separadores («{normalizado}»): sin "
    "ningún tramo no hay nombre que componer"
)


@pytest.mark.parametrize(
    ("incidencia", "normalizado"), [("/", "/"), (" / ", "/"), ("-", "-")]
)
def test_f034_h4_r26_archivar_no_cambia_con_una_incidencia_sin_tramos(
    incidencia, normalizado
):
    """H-4, R26 · **archivar queda idéntico**: `NombradoImposible`, no `CodigoNoConsta`.

    Archivar no llama a `exigir_codigos_completos` (allí el hueco lo dice el
    nombrado, como desde F-006), así que H-4 no puede alcanzarlo; este test lo
    comprueba por comportamiento, con el mensaje literal de antes, y sin haber
    tocado la biblioteca ni la traza.
    """
    biblioteca = BibliotecaFalsa()
    archivador = ArchivoPortFalso(biblioteca)
    repositorio = RepositorioFalso(situacion=_situacion(incidencia=incidencia))

    with pytest.raises(NombradoImposible) as error:
        paso_archivo(
            contexto_apto(hash_parte=HASH),
            archivador,
            repositorio,
            carpeta_base=CARPETA_BASE,
            ahora=datetime(2026, 9, 23, 10, 0, tzinfo=UTC),
            codigos_declarados=_guardados(incidencia=incidencia),
        )

    assert error.value.motivo == MENSAJE_DE_ARCHIVAR_SIN_TRAMOS.format(
        normalizado=normalizado
    )
    assert archivador.llamadas == []
    assert repositorio.llamadas_guardar_archivo == 0


def test_f034_h4_r26_archivar_no_llama_a_la_exigencia_de_completos():
    """H-4, R26 · el camino por el que H-4 podría llegar a archivar no existe.

    Si algún día `paso_archivo` empezara a llamar a `exigir_codigos_completos`,
    el criterio de H-4 cambiaría su comportamiento en silencio; este control
    obliga a volver a decidirlo.
    """
    import inspect

    assert "exigir_codigos_completos(" not in inspect.getsource(modulo_paso_archivo)
