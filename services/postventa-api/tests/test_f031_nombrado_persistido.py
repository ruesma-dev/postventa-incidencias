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

from dataclasses import replace
from datetime import UTC, datetime

import pytest
from application.pipelines.paso_archivo import (
    CodigosDelParte,
    _codigos_guardados,
    paso_archivo,
)
from domain.models.errores import NombradoImposible
from domain.models.estado import SituacionParte
from domain.models.nombrado import es_el_mismo_codigo

from tests.utiles_sharepoint import (
    CARPETA_BASE,
    ArchivoPortFalso,
    BibliotecaFalsa,
    RepositorioFalso,
    contexto_apto,
    parte_de_prueba,
)
from tests.utiles_validacion import HASH_DE_PRUEBA, veredicto_apto

#: Un instante fijo. El paso **no** consulta el reloj: la hora entra por
#: parámetro, igual que en F-006.
AHORA = datetime(2026, 9, 22, 10, 0, tzinfo=UTC)

HASH = HASH_DE_PRUEBA

#: Lo que consta **guardado** en `postventa.partes` para este parte, que es de
#: donde F-031 toma la carpeta y el nombre. Inventado.
OBRA_GUARDADA = "0677"
INCIDENCIA_GUARDADA = "RS26.08/0123"
NOMBRE_GUARDADO = "0677 - RS26.08 - 0123 PARTE FIRMADO.pdf"
CARPETA_GUARDADA = "Postventa/0677"

#: Lo que trae **el cuerpo** en los casos que separan las dos fuentes. Es otra
#: obra y otra incidencia a propósito: si el nombrado volviera a salir de aquí,
#: el PDF acabaría en `Postventa/0999` y estos tests lo verían.
OBRA_DEL_CUERPO = "0999"
INCIDENCIA_DEL_CUERPO = "RS26.09/0999"
CARPETA_DEL_CUERPO = "Postventa/0999"


class RepositorioQueCuenta(RepositorioFalso):
    """`RepositorioFalso` que además **cuenta las consultas de situación**.

    Es lo único con lo que se puede afirmar R2 —los dos códigos guardados no
    cuestan ninguna sentencia propia—, porque ese requisito no es sobre lo que
    devuelve el doble, sino sobre **cuántas veces se le pregunta**. Es el mismo
    doble que usó F-033 para su R8.
    """

    def __init__(self, **extra) -> None:
        super().__init__(**extra)
        self.consultas: list[str] = []

    def consultar_situacion(self, *, hash_parte: str) -> SituacionParte:
        self.consultas.append(hash_parte)
        return super().consultar_situacion(hash_parte=hash_parte)


def situacion_guardada(
    codigo_obra: str = OBRA_GUARDADA, numero_incidencia: str = INCIDENCIA_GUARDADA
) -> SituacionParte:
    """La situación que devolvería la base: el veredicto apto **con esos códigos**.

    Se construye con `veredicto_apto` —que sale de `validar_parte`, la función
    de verdad de F-004— y después se pisan los dos códigos con `replace`. El
    rodeo tiene motivo: un código **vacío** no es legible y F-004 no declararía
    apto ese parte, así que los casos de R7 no se podrían montar de otra forma
    sin quedarse parados en la puerta por un motivo que no es el suyo. Es el
    mismo recurso que usa `test_f030_veredicto_persistido.py`.
    """
    return SituacionParte(
        validacion=replace(
            veredicto_apto(hash_parte=HASH),
            codigo_obra=codigo_obra,
            numero_incidencia=numero_incidencia,
        )
    )


def contexto_del_cuerpo(
    codigo_obra: str = OBRA_DEL_CUERPO, numero_incidencia: str = INCIDENCIA_DEL_CUERPO
):
    """El contexto con **otros** códigos que los guardados.

    Es la mitad que hace que estos tests demuestren algo: si las dos fuentes
    dijeran lo mismo, pasarían igual antes y después de la feature.
    """
    return contexto_apto(
        hash_parte=HASH,
        codigo_obra=codigo_obra,
        numero_incidencia=numero_incidencia,
    )


def archivar(archivador, repositorio, *, ctx=None, declarados=None, **extra):
    """El paso con la carpeta base y la hora de siempre.

    `declarados` va explícito y por defecto a `None`: el camino **sin cotejo**
    es el que tiene que seguir nombrando con lo guardado (R11), y dejarlo por
    omisión obliga a cada caso a decir si está hablando del cotejo o no.
    """
    return paso_archivo(
        ctx if ctx is not None else contexto_del_cuerpo(),
        archivador,
        repositorio,
        carpeta_base=CARPETA_BASE,
        ahora=AHORA,
        codigos_declarados=declarados,
        **extra,
    )


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


# --------------------------------------------------------------------------
# R1, R11 · el nombre y la carpeta salen de lo guardado
# --------------------------------------------------------------------------


def test_f031_r1_el_nombre_y_la_carpeta_salen_de_lo_guardado_y_no_del_cuerpo():
    """R1 · el defecto que cierra la feature, visto en una sola aserción.

    El contexto dice `0999` / `RS26.09/0999`; la base dice `0677` /
    `RS26.08/0123`. Hasta F-031 el fichero se habría llamado con lo primero,
    porque el nombrado leía `ctx.extraccion`. Desde F-031 el PDF acaba
    **donde dice la base**, que es lo mismo que acaba de aprobar la puerta.
    """
    biblioteca = BibliotecaFalsa()
    archivador = ArchivoPortFalso(biblioteca)
    repositorio = RepositorioFalso(situacion=situacion_guardada())

    archivar(archivador, repositorio)

    assert repositorio.ultima_traza.nombre_fichero == NOMBRE_GUARDADO
    assert repositorio.ultima_traza.carpeta == CARPETA_GUARDADA
    assert biblioteca.nombres == [NOMBRE_GUARDADO]
    assert biblioteca.carpetas == {CARPETA_GUARDADA}
    # Y del cuerpo no queda ni rastro en la biblioteca.
    assert CARPETA_DEL_CUERPO not in biblioteca.carpetas
    assert not any(OBRA_DEL_CUERPO in nombre for nombre in biblioteca.nombres)


@pytest.mark.parametrize(
    ("caso", "obra_del_cuerpo", "incidencia_del_cuerpo"),
    (
        ("otra obra", "0999", INCIDENCIA_GUARDADA),
        ("otra incidencia", OBRA_GUARDADA, "RS26.09/0999"),
        ("las dos", "0999", "RS26.09/0999"),
        ("la obra sin sus ceros", "677", INCIDENCIA_GUARDADA),
    ),
)
def test_f031_r11_sin_cotejo_lo_declarado_tampoco_mueve_el_pdf(
    caso, obra_del_cuerpo, incidencia_del_cuerpo
):
    """R11 · el camino **sin** `codigos_declarados` tampoco archiva en otro sitio.

    Es la mitad silenciosa del requisito. El cotejo es lo que **cierra** la
    puerta ante una divergencia; lo que impide que el cuerpo la **abra** es
    que el nombrado ya no lo mira. Si mañana alguien llamara al paso sin pasar
    lo declarado —un script, un pipeline nuevo—, el destino tiene que seguir
    siendo el de la base.
    """
    biblioteca = BibliotecaFalsa()
    repositorio = RepositorioFalso(situacion=situacion_guardada())

    archivar(
        ArchivoPortFalso(biblioteca),
        repositorio,
        ctx=contexto_del_cuerpo(obra_del_cuerpo, incidencia_del_cuerpo),
    )

    assert repositorio.ultima_traza.carpeta == CARPETA_GUARDADA, caso
    assert repositorio.ultima_traza.nombre_fichero == NOMBRE_GUARDADO, caso
    assert biblioteca.carpetas == {CARPETA_GUARDADA}, caso


def test_f031_r1_el_paso_ya_no_lee_la_extraccion_del_contexto():
    """R1 · el parte se archiva aunque **no haya extracción ninguna**.

    Es la comprobación de que la segunda fuente está cerrada de verdad y no
    solo ignorada en el camino feliz: `_campo` era el único consumidor de
    `ctx.extraccion` en este paso, y dejarlo vivo habría dejado viva la fuente
    que la feature viene a cerrar (es la misma decisión que tomó F-033 con
    `traza_previa`).
    """
    from application.pipelines.contexto_parte import ContextoParte

    biblioteca = BibliotecaFalsa()
    repositorio = RepositorioFalso(situacion=situacion_guardada())
    ctx = ContextoParte(parte=parte_de_prueba(hash_parte=HASH))

    archivar(ArchivoPortFalso(biblioteca), repositorio, ctx=ctx)

    assert ctx.extraccion is None
    assert biblioteca.nombres == [NOMBRE_GUARDADO]


# --------------------------------------------------------------------------
# R2 · sin una sentencia más
# --------------------------------------------------------------------------


def test_f031_r2_los_codigos_guardados_no_cuestan_ninguna_consulta():
    """R2 · una consulta de situación por petición, la que ya hacía la puerta.

    Los dos códigos viajan desde F-030 dentro de `select_veredicto_y_cierre`,
    así que traerlos **no cuesta nada**. Es lo que abarata esta feature frente
    a F-033, y lo que hace que no haya que tocar `RepositorioPartesPort`, ni
    el SQL, ni `postventa`. Contra un PostgreSQL compartido con albaranes, una
    consulta más por parte y paso no es gratis.
    """
    repositorio = RepositorioQueCuenta(situacion=situacion_guardada())

    archivar(ArchivoPortFalso(), repositorio)

    assert repositorio.consultas == [HASH]


def test_f031_r2_los_codigos_salen_del_mismo_objeto_que_aprobo_la_puerta():
    """R2, R1 · se leen de `ctx.situacion.validacion`, no de un camino propio.

    Es la propiedad que ningún otro origen da gratis: el fichero se nombra,
    byte por byte, con los dos valores que **acaban de entrar en la huella
    del veredicto** que la puerta aprobó. Si mañana alguien los sacara de un
    campo nuevo de `SituacionParte`, habría dos representaciones del mismo
    dato y este caso diría cuándo divergieron.
    """
    from application.pipelines.contexto_parte import ContextoParte

    ctx = ContextoParte(parte=parte_de_prueba(hash_parte=HASH))
    ctx.situacion = situacion_guardada("0626", "RS26.09/0178")

    assert _codigos_guardados(ctx) == CodigosDelParte(
        codigo_obra="0626", numero_incidencia="RS26.09/0178"
    )


@pytest.mark.parametrize(
    ("caso", "situacion"),
    (
        ("no se ha preguntado todavía", None),
        ("no consta nada del parte", SituacionParte()),
    ),
)
def test_f031_r7_sin_veredicto_guardado_los_codigos_son_dos_vacios(caso, situacion):
    """R7 · sin `validacion` no hay códigos, y **no se inventa ninguno**.

    No se añade aquí una guardia que levante: quien decide que eso es un error
    es el nombrado, un paso más allá, y lo dice nombrando **cuál** falta. Es el
    mismo razonamiento que `nombre_admisible` tiene escrito en su docstring, y
    el camino es de hecho inalcanzable desde el endpoint —la puerta levanta
    `ParteNoApto` antes—, así que se prueba directamente sobre la función.
    """
    from application.pipelines.contexto_parte import ContextoParte

    ctx = ContextoParte(parte=parte_de_prueba(hash_parte=HASH))
    ctx.situacion = situacion

    assert _codigos_guardados(ctx) == CodigosDelParte(
        codigo_obra="", numero_incidencia=""
    ), caso


# --------------------------------------------------------------------------
# R7 · lo guardado vacío es un error, y no se rellena con el cuerpo
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("caso", "obra", "incidencia", "que_falta"),
    (
        ("sin código de obra", "", INCIDENCIA_GUARDADA, "código de obra"),
        ("obra de solo blancos", "   ", INCIDENCIA_GUARDADA, "código de obra"),
        ("sin nº de incidencia", OBRA_GUARDADA, "", "nº de incidencia"),
        ("incidencia de solo blancos", OBRA_GUARDADA, "  ", "nº de incidencia"),
    ),
)
def test_f031_r7_lo_guardado_vacio_no_se_sustituye_por_lo_del_cuerpo(
    caso, obra, incidencia, que_falta
):
    """R7 · el nombrado se niega diciendo **cuál** falta, con el cuerpo lleno.

    El contexto trae los dos códigos completos y aun así no se archiva nada.
    Es lo correcto y coincide con la regla de F-026: un código ilegible **no
    se aprueba, se teclea** — y teclearlo significa guardarlo, no mandarlo en
    la petición de archivo.
    """
    biblioteca = BibliotecaFalsa()
    repositorio = RepositorioFalso(situacion=situacion_guardada(obra, incidencia))

    with pytest.raises(NombradoImposible) as fallo:
        archivar(
            ArchivoPortFalso(biblioteca),
            repositorio,
            ctx=contexto_del_cuerpo(OBRA_GUARDADA, INCIDENCIA_GUARDADA),
        )

    assert que_falta in fallo.value.motivo, caso
    assert biblioteca.subidas == 0
    assert biblioteca.carpetas == set()
    assert repositorio.llamadas_guardar_archivo == 0


# --------------------------------------------------------------------------
# R8 · un nombre imposible **desde lo guardado** sigue siendo un error
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("caso", "obra", "incidencia"),
    (
        ("carácter prohibido en la obra", "06|77", INCIDENCIA_GUARDADA),
        ("carácter prohibido en la incidencia", OBRA_GUARDADA, "RS26.08:0123"),
        ("incidencia de solo separadores", OBRA_GUARDADA, "//-/"),
    ),
)
def test_f031_r8_un_nombre_imposible_desde_lo_guardado_no_se_sanea(
    caso, obra, incidencia
):
    """R8 · el camino de F-006 R7 sigue vivo, y ahora se alcanza desde la base.

    `normalizar_codigo` quita blancos, pero **no** quita lo que SharePoint no
    admite, así que un código guardado con una barra vertical sigue produciendo
    un nombre imposible. Y se sigue tratando igual: error ruidoso, nunca un
    saneo silencioso que archivaría en Posventa un fichero con un nombre que
    nadie pidió.

    Los dos códigos declarados son **los mismos** que los guardados, así que el
    cotejo pasa y lo que falla es el nombrado. Sin eso, el caso probaría R3.
    """
    biblioteca = BibliotecaFalsa()
    repositorio = RepositorioFalso(situacion=situacion_guardada(obra, incidencia))

    with pytest.raises(NombradoImposible):
        archivar(
            ArchivoPortFalso(biblioteca),
            repositorio,
            ctx=contexto_del_cuerpo(obra, incidencia),
            declarados=CodigosDelParte(
                codigo_obra=obra, numero_incidencia=incidencia
            ),
        )

    assert biblioteca.subidas == 0
    assert biblioteca.nombres == [], caso
    assert repositorio.llamadas_guardar_archivo == 0


# --------------------------------------------------------------------------
# R12 · las cuatro reglas del nombrado, intactas
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("caso", "obra", "incidencia", "carpeta", "nombre"),
    (
        (
            "los ceros a la izquierda se conservan",
            "0626",
            "RS26.09/0178",
            "Postventa/0626",
            "0626 - RS26.09 - 0178 PARTE FIRMADO.pdf",
        ),
        (
            "la barra de Sigrid pasa a guion",
            "0677",
            "RS26.08/0123",
            "Postventa/0677",
            "0677 - RS26.08 - 0123 PARTE FIRMADO.pdf",
        ),
        (
            "el guion largo del escaneo acaba en el mismo sitio",
            "0626",
            "RS26.09 – 0178",
            "Postventa/0626",
            "0626 - RS26.09 - 0178 PARTE FIRMADO.pdf",
        ),
        (
            "el código de obra no se parte por su guion",
            "06-77",
            "RS26.08/0123",
            "Postventa/06-77",
            "06-77 - RS26.08 - 0123 PARTE FIRMADO.pdf",
        ),
    ),
)
def test_f031_r12_las_reglas_del_nombrado_no_cambian_al_cambiar_la_fuente(
    caso, obra, incidencia, carpeta, nombre
):
    """R12 · la feature cambia **de dónde salen las entradas**, no qué se hace.

    El sufijo sigue literal y en mayúsculas, la extensión en minúsculas, los
    ceros dentro y la barra convertida en guion. El último caso es el que más
    fácil se rompe: `06-77` es **una** obra, no dos tramos, y partirlo
    archivaría el parte en una subcarpeta que no existe.
    """
    biblioteca = BibliotecaFalsa()
    repositorio = RepositorioFalso(situacion=situacion_guardada(obra, incidencia))

    archivar(ArchivoPortFalso(biblioteca), repositorio)

    assert repositorio.ultima_traza.carpeta == carpeta, caso
    assert repositorio.ultima_traza.nombre_fichero == nombre, caso
    assert biblioteca.nombres == [nombre], caso
    assert nombre.endswith(" PARTE FIRMADO.pdf"), caso
