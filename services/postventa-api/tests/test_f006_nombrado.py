# services/postventa-api/tests/test_f006_nombrado.py
"""El nombrado del parte: el corazón de F-006 (R1–R9).

**Dominio puro.** Aquí no hay red, ni SharePoint, ni configuración, ni reloj:
dos cadenas entran y un nombre de fichero sale. Por eso estos tests son los
más baratos de la feature y los que más protegen: el nombre es lo que Posventa
va a ver en la carpeta durante años, y equivocarlo no revienta nada — solo
archiva el parte donde nadie lo encuentra.

**Ni un dato real.** `0677` y `RS26.08/0123` son **inventados** y así lo dice
la spec. Los partes de verdad llevan DNI y observaciones manuscritas de
clientes: no entran ni en un test.

Las tres trampas que vigilan estos tests, y que son tres bugs distintos:

1. La **barra** del código de incidencia (`RS26.08/0123`) es un separador de
   ruta. Dejarla caer en el nombre parte el fichero en dos carpetas.
2. Los **ceros a la izquierda** del código de obra. `int("0677")` es un bug,
   no una normalización: `677` es otra obra.
3. Un **nombre imposible** se convierte en error, nunca en un saneo
   silencioso. Un fichero con un nombre que nadie pidió, en un archivo que se
   consulta a mano, es peor que un error ruidoso.
"""

from __future__ import annotations

import inspect

import pytest
from domain.models.errores import NombradoImposible
from domain.models.nombrado import (
    CARACTERES_PROHIBIDOS,
    EXTENSION,
    GUIONES_EQUIVALENTES,
    SEPARADOR,
    SUFIJO,
    DestinoArchivo,
    carpeta_de_archivo,
    componer_destino,
    nombre_admisible,
    nombre_de_archivo,
    normalizar_codigo,
)

#: Los dos códigos de ejemplo de la spec. **Inventados**: no son de nadie.
OBRA = "0677"
INCIDENCIA = "RS26.08/0123"

#: El nombre que tienen que producir. Escrito **literal**, no compuesto a
#: partir de las constantes del módulo: un test que se construye con las
#: mismas piezas que vigila da verde aunque las piezas cambien.
NOMBRE_ESPERADO = "0677 - RS26.08 - 0123 PARTE FIRMADO.pdf"

#: La carpeta base del destino de dev. Es **configuración**, no una constante
#: del dominio: aquí se pasa como argumento, que es justo lo que hace posible
#: F-013 sin tocar el dominio.
CARPETA_BASE = "Postventa"


# --------------------------------------------------------------------------
# R1 · La convención de Posventa, tal cual
# --------------------------------------------------------------------------


def test_f006_r1_el_nombre_sigue_la_convencion_de_posventa():
    """R1 · obra `0677` + incidencia `RS26.08/0123` → el nombre de la spec.

    Igualdad exacta contra una cadena literal. Ni `in`, ni `startswith`, ni
    una comparación normalizando espacios: lo que se archiva es esta cadena y
    ninguna parecida.
    """
    assert (
        nombre_de_archivo(codigo_obra=OBRA, numero_incidencia=INCIDENCIA)
        == NOMBRE_ESPERADO
    )


def test_f006_r1_el_separador_es_espacio_guion_normal_espacio():
    """R1 · el separador es ` - `, con el guion **normal** `U+002D`.

    Se comprueba sobre la constante y sobre el nombre producido: un guion
    largo aquí sería invisible al ojo y visible en la carpeta de Posventa.
    """
    assert SEPARADOR == " - "

    nombre = nombre_de_archivo(codigo_obra=OBRA, numero_incidencia=INCIDENCIA)

    assert "–" not in nombre
    assert "—" not in nombre
    assert nombre.count(" - ") == 2


# --------------------------------------------------------------------------
# R2 · La barra nunca llega al nombre
# --------------------------------------------------------------------------


def test_f006_r2_la_barra_del_numero_de_incidencia_pasa_a_guion():
    """R2 · `RS26.08/0123` se nombra `RS26.08 - 0123`.

    La barra es un separador de ruta: si sobrevive, el fichero cae en una
    subcarpeta que nadie pidió o la subida revienta.
    """
    nombre = nombre_de_archivo(codigo_obra=OBRA, numero_incidencia=INCIDENCIA)

    assert "/" not in nombre
    assert "RS26.08 - 0123" in nombre


def test_f006_r2_varias_barras_se_sustituyen_todas():
    """R2 · sustituir **la primera** barra no es sustituir la barra.

    Caso inventado y poco probable, pero el fallo sería silencioso: quedaría
    una barra viva en mitad del nombre.
    """
    nombre = nombre_de_archivo(codigo_obra=OBRA, numero_incidencia="A/B/C")

    assert "/" not in nombre
    assert nombre == f"0677 - A - B - C{SUFIJO}{EXTENSION}"


# --------------------------------------------------------------------------
# R3 · Los guiones que no son el guion normal
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("nombre_del_guion", "guion"),
    (
        ("guion U+2010", "‐"),
        ("guion sin salto U+2011", "‑"),
        ("guion de cifras U+2012", "‒"),
        ("guion largo U+2013", "–"),
        ("raya U+2014", "—"),
        ("barra horizontal U+2015", "―"),
        ("signo menos U+2212", "−"),
    ),
)
def test_f006_r3_los_guiones_no_normales_se_normalizan(nombre_del_guion, guion):
    """R3 · siete caracteres que hacen de guion y **no** son `U+002D`.

    Los siete se escriben aquí **uno a uno y a mano**, no iterando sobre
    `GUIONES_EQUIVALENTES`: un test que recorre la constante que vigila da
    verde aunque alguien vacíe la constante.

    Los tres del ejemplo de la spec (`–`, `—`, `−`) tienen que producir el
    **mismo** nombre que la versión con barra: es lo que garantiza que dos
    lecturas del mismo parte no acaben en dos ficheros distintos.
    """
    con_guion_raro = f"RS26.08 {guion} 0123"

    assert nombre_de_archivo(
        codigo_obra=OBRA, numero_incidencia=con_guion_raro
    ) == nombre_de_archivo(codigo_obra=OBRA, numero_incidencia=INCIDENCIA), (
        f"el {nombre_del_guion} no se ha normalizado a guion normal"
    )


def test_f006_r3_el_guion_raro_del_codigo_de_obra_tambien_se_normaliza():
    """R3 · «cualquiera de los códigos», dice el requisito. También la obra."""
    assert (
        nombre_de_archivo(codigo_obra="06–77", numero_incidencia=INCIDENCIA)
        == f"06-77{SEPARADOR}RS26.08 - 0123{SUFIJO}{EXTENSION}"
    )


def test_f006_r3_la_barra_se_sustituye_despues_de_normalizar_los_guiones():
    """R3 + R2 · el **orden** de las dos sustituciones importa.

    Si la barra se sustituyera **antes** de normalizar los guiones, un
    `RS26.08 – 0123` con guion largo saldría distinto que `RS26.08/0123`, y
    los dos son el mismo parte leído dos veces.
    """
    con_barra = nombre_de_archivo(codigo_obra=OBRA, numero_incidencia="RS26.08/0123")
    con_raya = nombre_de_archivo(
        codigo_obra=OBRA, numero_incidencia="RS26.08 — 0123"
    )

    assert con_barra == con_raya == NOMBRE_ESPERADO


def test_f006_r3_la_constante_declara_los_siete_guiones():
    """R3 · `GUIONES_EQUIVALENTES` no puede quedarse corta.

    Se comprueba pertenencia carácter a carácter, con los siete escritos a
    mano. Y que el guion **normal** no esté dentro: sustituirlo por sí mismo
    es inofensivo, pero declararlo aquí delata que alguien no entendió qué
    normaliza esta constante.
    """
    for guion in ("‐", "‑", "‒", "–", "—", "―", "−"):
        assert guion in GUIONES_EQUIVALENTES

    assert "-" not in GUIONES_EQUIVALENTES


# --------------------------------------------------------------------------
# R4 · Los ceros a la izquierda
# --------------------------------------------------------------------------


def test_f006_r4_los_ceros_a_la_izquierda_del_codigo_de_obra_se_conservan():
    """R4 · `0677` se archiva como `0677`. **Nunca** como `677`.

    El bug clásico: alguien normaliza el código a `int` para compararlo y
    devuelve la cadena ya sin ceros. `677` es otra obra, y el parte acaba en
    la carpeta de otra promoción.
    """
    nombre = nombre_de_archivo(codigo_obra="0677", numero_incidencia=INCIDENCIA)

    assert nombre.startswith("0677 ")
    assert not nombre.startswith("677")


@pytest.mark.parametrize("obra", ("0677", "0000677", "007", "0"))
def test_f006_r4_ningun_codigo_de_obra_pierde_sus_ceros(obra):
    """R4 · varias formas del mismo bug, incluida la obra `0`.

    `"0"` es el caso que rompe la comprobación perezosa `if not int(obra)`.
    """
    assert nombre_de_archivo(
        codigo_obra=obra, numero_incidencia=INCIDENCIA
    ).startswith(f"{obra}{SEPARADOR}")


def test_f006_r4_la_carpeta_conserva_los_ceros():
    """R4 · y en la **carpeta** también, que es donde más duele.

    Un nombre con los ceros dentro de una carpeta sin ellos deja el parte
    archivado en la promoción equivocada.
    """
    assert (
        carpeta_de_archivo(carpeta_base=CARPETA_BASE, codigo_obra="0677")
        == "Postventa/0677"
    )


def test_f006_r4_el_codigo_de_obra_no_se_convierte_a_numero():
    """R4 · un código de obra que **no** es un número tiene que pasar igual.

    Si en algún punto del recorrido hubiera un `int()`, esto reventaría con
    un `ValueError` en vez de nombrar el parte.
    """
    assert nombre_de_archivo(
        codigo_obra="0677-BIS", numero_incidencia=INCIDENCIA
    ).startswith("0677-BIS ")


# --------------------------------------------------------------------------
# R5 · El sufijo y la extensión, literales
# --------------------------------------------------------------------------


def test_f006_r5_el_sufijo_y_la_extension_van_literales():
    """R5 · ` PARTE FIRMADO` en mayúsculas y `.pdf`, sin acortar.

    Es el sufijo que ya usa Posventa y lo que distingue el parte conformado
    de cualquier otro documento de la misma incidencia. Se comprueban las dos
    constantes **literales** y el nombre producido.
    """
    assert SUFIJO == " PARTE FIRMADO"
    assert EXTENSION == ".pdf"

    nombre = nombre_de_archivo(codigo_obra=OBRA, numero_incidencia=INCIDENCIA)

    assert nombre.endswith(" PARTE FIRMADO.pdf")


def test_f006_r5_el_sufijo_no_se_pone_en_minusculas_ni_se_acorta():
    """R5 · ni `parte firmado`, ni `PF`, ni `.PDF`."""
    nombre = nombre_de_archivo(codigo_obra=OBRA, numero_incidencia=INCIDENCIA)

    assert "parte firmado" not in nombre
    assert ".PDF" not in nombre
    assert nombre.count("PARTE FIRMADO") == 1


# --------------------------------------------------------------------------
# R6 · Sin códigos no hay nombre: se levanta, no se inventa
# --------------------------------------------------------------------------


@pytest.mark.parametrize("ausente", (None, "", "   ", "\t", "\n  \t "))
def test_f006_r6_sin_codigo_de_obra_no_se_nombra(ausente):
    """R6 · ausente, vacío o solo espacios: `NombradoImposible`.

    Y el motivo **nombra cuál falta**: quien lee el error tiene que saber qué
    campo volver a mirar en el papel sin abrir el código fuente.
    """
    with pytest.raises(NombradoImposible) as fallo:
        nombre_de_archivo(codigo_obra=ausente, numero_incidencia=INCIDENCIA)

    assert "obra" in fallo.value.motivo.lower()


@pytest.mark.parametrize("ausente", (None, "", "   ", "\t", "\n  \t "))
def test_f006_r6_sin_numero_de_incidencia_no_se_nombra(ausente):
    """R6 · ídem con el nº de incidencia, y el motivo lo dice."""
    with pytest.raises(NombradoImposible) as fallo:
        nombre_de_archivo(codigo_obra=OBRA, numero_incidencia=ausente)

    assert "incidencia" in fallo.value.motivo.lower()


def test_f006_r6_el_motivo_distingue_cual_de_los_dos_falta():
    """R6 · dos motivos distintos, no uno genérico.

    «faltan datos» obliga a mirar el papel entero. «falta el código de obra»
    dice dónde mirar.
    """
    with pytest.raises(NombradoImposible) as sin_obra:
        nombre_de_archivo(codigo_obra=None, numero_incidencia=INCIDENCIA)
    with pytest.raises(NombradoImposible) as sin_incidencia:
        nombre_de_archivo(codigo_obra=OBRA, numero_incidencia=None)

    assert sin_obra.value.motivo != sin_incidencia.value.motivo


def test_f006_r6_no_se_inventa_ni_se_deduce_el_dato_que_falta():
    """R6 · nada de `SIN_INCIDENCIA`, ni de deducirlo de la obra.

    Un parte archivado con un nº de incidencia inventado es peor que un parte
    sin archivar: el segundo lo ve alguien, el primero no.
    """
    with pytest.raises(NombradoImposible):
        nombre_de_archivo(codigo_obra=OBRA, numero_incidencia="")


def test_f006_r6_sin_codigo_de_obra_tampoco_hay_carpeta():
    """R6 · la carpeta también se niega: `<base>/` sería la base entera."""
    with pytest.raises(NombradoImposible) as fallo:
        carpeta_de_archivo(carpeta_base=CARPETA_BASE, codigo_obra=None)

    assert "obra" in fallo.value.motivo.lower()


# --------------------------------------------------------------------------
# R7 · Un nombre imposible no se sanea en silencio
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "prohibido", ('"', "*", ":", "<", ">", "?", "/", "\\", "|")
)
def test_f006_r7_un_caracter_prohibido_no_se_sanea_en_silencio(prohibido):
    """R7 · los nueve caracteres que SharePoint no admite, uno a uno.

    Escritos **a mano**, no iterando `CARACTERES_PROHIBIDOS`: un test que
    recorre la constante que vigila da verde aunque alguien la vacíe.

    Se inyectan en el **código de obra** porque la barra del nº de incidencia
    ya se sustituye antes (R2) y no llegaría nunca a esta comprobación.

    La alternativa —cambiarlo por `_`— archivaría en Posventa un fichero con
    un nombre que nadie pidió, y **nadie se enteraría**.
    """
    with pytest.raises(NombradoImposible) as fallo:
        nombre_de_archivo(
            codigo_obra=f"06{prohibido}77", numero_incidencia=INCIDENCIA
        )

    assert "_" not in fallo.value.motivo


def test_f006_r7_la_constante_declara_los_nueve_caracteres():
    """R7 · `CARACTERES_PROHIBIDOS` no puede quedarse corta."""
    for prohibido in ('"', "*", ":", "<", ">", "?", "/", "\\", "|"):
        assert prohibido in CARACTERES_PROHIBIDOS


@pytest.mark.parametrize(
    ("nombre", "admisible"),
    (
        ("0677 - RS26.08 - 0123 PARTE FIRMADO.pdf", True),
        ("06|77 PARTE FIRMADO.pdf", False),
        ("06:77 PARTE FIRMADO.pdf", False),
        (" 0677 PARTE FIRMADO.pdf", False),
        ("0677 PARTE FIRMADO.pdf ", False),
        ("0677 PARTE FIRMADO.", False),
        ("", False),
    ),
)
def test_f006_r7_el_predicado_de_admisibilidad_juzga_cada_caso(nombre, admisible):
    """R7 · el predicado, probado directamente y en sus tres motivos.

    Existe como función pública **a propósito**: las ramas «empieza en
    espacio», «acaba en espacio» y «acaba en punto» no se pueden alcanzar
    desde `nombre_de_archivo`, porque los códigos ya vienen recortados y el
    nombre siempre acaba en `.pdf`. Una guardia que nadie puede ejercitar es
    una guardia que nadie sabe si funciona.
    """
    assert nombre_admisible(nombre) is admisible


def test_f006_r7_el_nombre_no_se_recorta_ni_se_sustituye_nada():
    """R7 · el error llega **en vez** del nombre, no además del nombre."""
    with pytest.raises(NombradoImposible):
        componer_destino(
            carpeta_base=CARPETA_BASE,
            codigo_obra="06?77",
            numero_incidencia=INCIDENCIA,
        )


# --------------------------------------------------------------------------
# R8 · Los espacios redundantes colapsan
# --------------------------------------------------------------------------


def test_f006_r8_los_espacios_redundantes_colapsan():
    """R8 · `0677  -  RS26.08` y `0677 - RS26.08` son el mismo parte.

    Dos lecturas del mismo papel que solo difieran en espacios tienen que
    producir **el mismo** nombre, o el archivo acaba con dos ficheros que a
    ojo son idénticos.
    """
    assert (
        nombre_de_archivo(
            codigo_obra="  0677 ", numero_incidencia="  RS26.08  /  0123  "
        )
        == NOMBRE_ESPERADO
    )


@pytest.mark.parametrize(
    "bruto", ("0677", " 0677", "0677 ", "  0677  ", "\t0677\n")
)
def test_f006_r8_los_extremos_se_recortan(bruto):
    """R8 · lo de los extremos se recorta, venga como venga."""
    assert normalizar_codigo(bruto) == "0677"


def test_f006_r8_los_espacios_interiores_se_colapsan_a_uno():
    """R8 · varios espacios seguidos dentro del código pasan a ser uno."""
    assert normalizar_codigo("RS26.08   -    0123") == "RS26.08 - 0123"


def test_f006_r8_el_colapso_ocurre_tambien_despues_de_sustituir_la_barra():
    """R8 · `RS26.08 / 0123` (barra con espacios) no deja espacios dobles.

    Si el colapso pasara **antes** de sustituir la barra, ` / ` se
    convertiría en `  -  ` y el nombre saldría con espacios dobles.
    """
    assert (
        nombre_de_archivo(codigo_obra=OBRA, numero_incidencia="RS26.08 / 0123")
        == NOMBRE_ESPERADO
    )


def test_f006_r8_normalizar_un_codigo_ausente_devuelve_la_cadena_vacia():
    """R8 · `None` normaliza a `""`, que es lo que luego detecta R6."""
    assert normalizar_codigo(None) == ""
    assert normalizar_codigo("   ") == ""


# --------------------------------------------------------------------------
# R9 · El nombrado es puro y determinista
# --------------------------------------------------------------------------


def test_f006_r9_el_nombrado_es_puro_y_deterministico():
    """R9 · mil llamadas con las mismas entradas, el mismo resultado.

    Sin reloj, sin azar y sin estado: es lo que permite volver a nombrar un
    parte meses después —cuando alguien corrija un campo en F-007— y obtener
    exactamente el mismo fichero.
    """
    nombres = {
        nombre_de_archivo(codigo_obra=OBRA, numero_incidencia=INCIDENCIA)
        for _ in range(1000)
    }

    assert nombres == {NOMBRE_ESPERADO}


@pytest.mark.parametrize(
    ("funcion", "parametros"),
    (
        (nombre_de_archivo, {"codigo_obra", "numero_incidencia"}),
        (carpeta_de_archivo, {"carpeta_base", "codigo_obra"}),
        (
            componer_destino,
            {"carpeta_base", "codigo_obra", "numero_incidencia"},
        ),
    ),
)
def test_f006_r9_las_funciones_no_reciben_configuracion_ni_reloj(
    funcion, parametros
):
    """R9 · la firma **es** la prueba de la pureza.

    Ni `ajustes`, ni `ahora`, ni `cliente`. Y todos los parámetros son de solo
    palabra clave, que es lo que impide que alguien invierta obra e incidencia
    en la llamada y archive el parte con el nombre del revés.
    """
    firma = inspect.signature(funcion)

    assert set(firma.parameters) == parametros
    for parametro in firma.parameters.values():
        assert parametro.kind is inspect.Parameter.KEYWORD_ONLY


def test_f006_r9_el_dominio_del_nombrado_no_importa_nada_de_fuera():
    """R9 · el módulo es puro también en sus importaciones.

    Ni `httpx`, ni `msal`, ni `requests`, ni `infrastructure`, ni
    `config.settings`: si mañana el nombrado necesitara configuración, dejaría
    de ser reproducible y F-013 dejaría de salir gratis.
    """
    import domain.models.nombrado as modulo

    codigo = inspect.getsource(modulo)

    for prohibido in ("httpx", "msal", "requests", "infrastructure", "config"):
        assert f"import {prohibido}" not in codigo


# --------------------------------------------------------------------------
# El destino compuesto: carpeta + nombre, en una pieza
# --------------------------------------------------------------------------


def test_f006_componer_destino_junta_la_carpeta_y_el_nombre():
    """`componer_destino` es lo que consume el paso de archivo (R10)."""
    destino = componer_destino(
        carpeta_base=CARPETA_BASE,
        codigo_obra=OBRA,
        numero_incidencia=INCIDENCIA,
    )

    assert isinstance(destino, DestinoArchivo)
    assert destino.carpeta == "Postventa/0677"
    assert destino.nombre_fichero == NOMBRE_ESPERADO
    assert destino.ruta_relativa == f"Postventa/0677/{NOMBRE_ESPERADO}"


def test_f006_el_destino_es_inmutable():
    """Un destino que se puede reescribir después de comprobarlo no vale.

    Entre componerlo y subir hay varias llamadas; si alguien pudiera cambiar
    el nombre por el camino, la comprobación de R7 no protegería nada.
    """
    destino = componer_destino(
        carpeta_base=CARPETA_BASE,
        codigo_obra=OBRA,
        numero_incidencia=INCIDENCIA,
    )

    with pytest.raises(Exception):
        destino.nombre_fichero = "otro.pdf"  # type: ignore[misc]


def test_f006_la_carpeta_base_se_recorta_por_los_extremos():
    """`Postventa/` y `Postventa` son la misma carpeta base.

    Una barra de más produciría `Postventa//0677`, que en Graph es otra ruta.
    """
    assert (
        carpeta_de_archivo(carpeta_base="  Postventa/  ", codigo_obra=OBRA)
        == "Postventa/0677"
    )


def test_f006_el_item_archivado_tambien_es_inmutable():
    """Lo que devuelve el puerto se copia a la traza: no puede cambiar por el camino.

    Lo destapó la campaña de mutación (T20): `ItemArchivado` estaba declarado
    `frozen=True` y ningún test lo comprobaba, así que quitarlo no rompía
    nada. Entre que el adaptador lo devuelve y el paso lo escribe en la traza
    hay código de por medio, y un `item_id` reescrito ahí dejaría la traza
    apuntando a un fichero que no es.
    """
    from domain.ports.archivo import ItemArchivado

    item = ItemArchivado(
        drive_id="drive-de-mentira",
        item_id="item-0001",
        web_url="https://ejemplo.invalido/x.pdf",
        nombre=NOMBRE_ESPERADO,
        carpeta="Postventa/0677",
    )

    with pytest.raises(Exception):
        item.item_id = "otro"  # type: ignore[misc]
