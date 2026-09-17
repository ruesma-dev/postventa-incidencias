# services/postventa-api/tests/test_f032_espacios_en_los_codigos.py
"""Ningún espacio forma parte de un código (F-032, R1–R10 y R28).

Esto tampoco lo pidió un diseño: lo pidió el responsable **el día que volvió a
ver fallar el circuito en real**, el 2026-09-17, verificando F-030 contra
producción. La IA leyó el número del papel como `RS 26.09/0178` —con el espacio
**dentro del primer tramo**, no pegado a la barra— y el cierre murió en
`ReclamacionNoLocalizada` hasta que una persona editó el código a mano.

## Por qué hacía falta un segundo fichero y no bastaba el de F-028

`test_f028_espacios_codigos.py` fijó **seis formas**, y las seis tenían el
espacio **flanqueando al separador** (`RS26.09 / 0149`). La premisa de aquella
feature era que el espacio problemático siempre tocaba al separador, y no era
cierta. `normalizar_codigo` **colapsaba** los espacios interiores a uno en vez
de eliminarlos, así que un espacio que no tocaba la barra sobrevivía entero.

Ese fichero no se toca: sus asertos son el control que esta feature tiene que
pasar, no ajustar. Este amplía la tabla con las formas que aquel no cubría
(`design.md` §5) y con el **caso real escrito literal**, porque un caso real
que nadie escribe se vuelve a perder.

## Las tres salidas, y por qué se recorren las tres

Las tres cuelgan de `normalizar_codigo` y ninguna tiene saneo propio (F-028
R47), así que una sola línea las arregla, pero el daño de cada una es distinto
y por eso se afirman por separado:

- **el código del ERP** · Sigrid busca la reclamación por **igualdad exacta**:
  un espacio de más no devuelve «casi» la reclamación, devuelve **cero filas**;
- **el nombre del fichero** · dos lecturas del mismo parte producirían dos
  nombres que a ojo son el mismo fichero, y el archivo de Posventa se consulta
  a mano;
- **la carpeta** · la decide el código de obra. `06 26` archivaría el PDF en
  `Postventa/06 26`, que no es `Postventa/0626`. Ese daño **no se ve**, que es
  lo que lo hace peor que un cierre fallido.

**Dominio puro.** Sin red, sin base de datos, sin IA y sin reloj: dos cadenas
entran y una cadena sale.

**Ni un dato personal.** `0626` y `RS26.09/0149` son los inventados de la tabla
de F-028; `RS 26.09/0178` es el número real del 2026-09-17, y un código de
incidencia no identifica a nadie.

## Los blancos raros van escritos con su escape, a propósito

`\\u00a0` (espacio no separable) y `\\u202f` (espacio fino no separable) se
escriben con la secuencia de escape y no con el carácter: pegados en el fichero
son **indistinguibles de un espacio normal**, y un día alguien los «arreglaría»
sin saber que acaba de borrar el caso que el test prueba.
"""

from __future__ import annotations

import pytest
from domain.models.cierre import a_codigo_de_sigrid
from domain.models.nombrado import (
    carpeta_de_archivo,
    nombre_de_archivo,
    normalizar_codigo,
)

#: El código de obra de la tabla. **Inventado**, con la forma de los reales.
OBRA = "0626"

#: La carpeta base del archivo. Entra como argumento: el dominio no la lee.
BASE = "Postventa"

#: Los dos números canónicos. `0149` es el inventado que venía de F-028;
#: `0178` es **el real del 2026-09-17**, el que costó el rescate a mano.
CANONICO_0149 = "RS26.09/0149"
CANONICO_0178 = "RS26.09/0178"

#: Los dos nombres de fichero, **escritos literales**.
#:
#: No se componen con `SEPARADOR`, `SUFIJO` y `EXTENSION`: un test que se
#: construye con las mismas piezas que vigila da verde aunque las piezas
#: cambien, y lo que aquí se afirma es que todas las formas producen **esta**
#: cadena y ninguna parecida.
NOMBRE_0149 = "0626 - RS26.09 - 0149 PARTE FIRMADO.pdf"
NOMBRE_0178 = "0626 - RS26.09 - 0178 PARTE FIRMADO.pdf"

#: La tabla del **número de incidencia** de `design.md` §5, fila a fila.
#:
#: Cada fila es `(etiqueta, entrada, código del ERP, nombre del fichero)`. Las
#: seis primeras son las de F-028 y ya estaban verdes; de la 7 a la 13 son las
#: que esta feature arregla. El orden es el de la spec para que un fallo se
#: pueda leer contra ella sin traducir nada.
FORMAS_DEL_NUMERO: tuple[tuple[str, str, str, str], ...] = (
    ("1 · barra pegada (la canónica)", "RS26.09/0149", CANONICO_0149, NOMBRE_0149),
    ("2 · barra con espacio a los dos lados", "RS26.09 / 0149", CANONICO_0149, NOMBRE_0149),
    ("3 · barra con espacio solo delante", "RS26.09 /0149", CANONICO_0149, NOMBRE_0149),
    ("4 · guion normal con espacio a los dos lados", "RS26.09 - 0149", CANONICO_0149, NOMBRE_0149),
    ("5 · guion pegado delante, espacio detrás", "RS26.09- 0149", CANONICO_0149, NOMBRE_0149),
    ("6 · guion largo con espacio a los dos lados", "RS26.09 – 0149", CANONICO_0149, NOMBRE_0149),
    # El caso real del 2026-09-17, escrito tal cual se leyó del papel.
    ("7 · espacio dentro del primer tramo (EL CASO REAL)", "RS 26.09/0178", CANONICO_0178, NOMBRE_0178),
    ("8 · espacio dentro del segundo tramo", "RS26.09/01 49", CANONICO_0149, NOMBRE_0149),
    ("9 · varios espacios dentro del tramo", "RS  26.09/0149", CANONICO_0149, NOMBRE_0149),
    ("10 · espacio interior y alrededor del separador", "RS 26.09 / 0149", CANONICO_0149, NOMBRE_0149),
    ("11 · tabulador dentro del tramo", "RS\t26.09/0149", CANONICO_0149, NOMBRE_0149),
    ("12 · espacio no separable dentro del tramo", "RS\u00a026.09/0149", CANONICO_0149, NOMBRE_0149),
    ("13 · extremos con blancos y espacio interior", "  RS 26.09/0149  ", CANONICO_0149, NOMBRE_0149),
)

#: La tabla del **código de obra**, que es la que decide la carpeta.
#:
#: Cada fila es `(etiqueta, entrada, normalizado, carpeta)`. La fila E es la que
#: impide que este arreglo se pase de listo: el código de obra **no se parte por
#: sus guiones** (F-028 R48), y lo único que desaparece son los blancos.
FORMAS_DE_LA_OBRA: tuple[tuple[str, str, str, str], ...] = (
    ("A · la canónica", "0626", "0626", "Postventa/0626"),
    ("B · espacio dentro del código", "06 26", "0626", "Postventa/0626"),
    ("C · dos espacios dentro del código", "06  26", "0626", "Postventa/0626"),
    ("D · espacio no separable dentro del código", "06\u00a026", "0626", "Postventa/0626"),
    ("E · obra con guion (NO se parte)", "06-77", "06-77", "Postventa/06-77"),
    ("F · obra con guion y espacios", "06 - 77", "06-77", "Postventa/06-77"),
    ("G · obra con guion largo", "06–77", "06-77", "Postventa/06-77"),
    ("H · ceros a la izquierda", "0000626", "0000626", "Postventa/0000626"),
)

#: Atajos para parametrizar sin arrastrar la etiqueta.
ENTRADAS_DEL_NUMERO = tuple(fila[1] for fila in FORMAS_DEL_NUMERO)
ENTRADAS_DE_LA_OBRA = tuple(fila[1] for fila in FORMAS_DE_LA_OBRA)

#: El caso real, aparte y con nombre, porque es el que paga esta feature.
LEIDO_EL_17 = "RS 26.09/0178"


# --------------------------------------------------------------------------
# R1, R2 · `normalizar_codigo` elimina **todos** los blancos
# --------------------------------------------------------------------------


def test_f032_r1_normalizar_elimina_todos_los_espacios():
    """R1 · el caso real del 2026-09-17, y el de la obra, escritos a mano.

    Hasta hoy `normalizar_codigo` **colapsaba**: `" ".join(bruto.split())`
    dejaba un espacio donde había varios, y solo se eliminaban los que
    flanqueaban a un separador. Por eso `RS 26.09/0178` salía intacto y el ERP
    devolvía cero filas.

    Estos dos asertos son la feature entera en dos líneas: un espacio **no
    forma parte del código**, esté donde esté.
    """
    assert normalizar_codigo(LEIDO_EL_17) == "RS26.09/0178"
    assert normalizar_codigo("06 26") == "0626"


@pytest.mark.parametrize(
    ("etiqueta", "entrada"),
    (
        ("espacio normal", "RS 26.09/0149"),
        ("dos espacios seguidos", "RS  26.09/0149"),
        ("tabulador", "RS\t26.09/0149"),
        ("salto de línea", "RS\n26.09/0149"),
        ("espacio no separable (U+00A0)", "RS\u00a026.09/0149"),
        ("espacio fino no separable (U+202F)", "RS\u202f26.09/0149"),
    ),
)
def test_f032_r2_los_blancos_raros_tambien(etiqueta: str, entrada: str):
    """R2 · cualquier blanco Unicode, no solo el espacio de la barra espaciadora.

    Los tres últimos salen de los escaneos y de Word, y a ojo son
    **indistinguibles** de un espacio normal: quien mirara el parte en pantalla
    no vería nada raro y el ERP seguiría sin encontrar la reclamación.

    No hay lista de caracteres que mantener: `str.split()` sin argumentos ya
    parte por cualquier blanco Unicode, así que R2 sale del mismo cambio que R1.
    """
    assert normalizar_codigo(entrada) == CANONICO_0149, (
        f"el blanco «{etiqueta}» sobrevive al saneo"
    )


def test_f032_d3_el_espacio_de_ancho_cero_sigue_pasando_y_se_declara():
    """D3 · lo que esta feature **no** arregla, escrito para que se vea.

    `U+200B` (espacio de ancho cero) no es blanco para Python —`'a\\u200bb'.split()`
    devuelve `['a\\u200bb']`—, así que sobrevive al saneo y produciría un nombre
    de fichero con un carácter invisible que `nombre_admisible` acepta.

    **No se arregla aquí y se declara** (`requirements.md` §8, D3): no se ha
    visto nunca, y ampliar el criterio a «todo lo que no se ve» es otra
    discusión, porque hay caracteres invisibles que sí significan algo. Este
    test no bendice el defecto: lo **fija** para que el día que alguien decida
    arreglarlo se tropiece con él aquí y lea el porqué.
    """
    assert normalizar_codigo("06\u200b26") == "06\u200b26"


# --------------------------------------------------------------------------
# R3, R4, R5 · Lo que el arreglo NO puede tocar
# --------------------------------------------------------------------------


@pytest.mark.parametrize("obra", ("0626", "0000626", "007", "0", "06 26", "00 07"))
def test_f032_r3_los_ceros_a_la_izquierda_siguen_intactos(obra: str):
    """R3 · `0626` nunca es `626`, y quitar espacios no es la puerta trasera.

    Es la garantía más cara de romper de todas: un cero perdido archiva el PDF
    en la carpeta de otra promoción, y ahí no lo busca nadie. Los dos últimos
    casos son el de esta feature —un código con espacio— y comprueban que el
    saneo **elimina el blanco sin convertir el código en número**.
    """
    normalizado = normalizar_codigo(obra)

    assert isinstance(normalizado, str)
    assert normalizado == obra.replace(" ", "")
    assert normalizado.startswith("0")


@pytest.mark.parametrize("ausente", (None, "", "   ", "\t", "\n  \t ", "\u00a0"))
def test_f032_r4_un_codigo_vacio_sigue_dando_cadena_vacia(ausente: str | None):
    """R4 · un código ausente o de solo blancos sale como cadena vacía.

    Y **no se levanta nada aquí** (F-006 R6, F-028 R49, sin cambios): quien
    decide que eso es un error es quien va a nombrar el fichero. El saneo nuevo
    no puede convertir esto en una excepción, porque este mismo camino lo usa
    también la carpeta.
    """
    assert normalizar_codigo(ausente) == ""


@pytest.mark.parametrize(
    ("entrada", "esperado"),
    (("06-77", "06-77"), ("06 - 77", "06-77"), ("06–77", "06-77"), ("06 -77", "06-77")),
)
def test_f032_r5_el_codigo_de_obra_no_se_parte_por_sus_guiones(
    entrada: str, esperado: str
):
    """R5 · `06-77` es **una** obra, no dos tramos (F-028 R48, sin cambios).

    El guion se conserva: lo único que desaparece son los blancos. Si el saneo
    se pasara de listo y tratara el guion como separador, la carpeta se partiría
    en una subcarpeta que nadie pidió y el parte se archivaría donde no es.
    """
    assert normalizar_codigo(entrada) == esperado
    assert carpeta_de_archivo(carpeta_base=BASE, codigo_obra=entrada) == (
        f"{BASE}/{esperado}"
    )


# --------------------------------------------------------------------------
# R6 · El saneo vive en `normalizar_codigo` y en ningún otro sitio
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("etiqueta", "entrada"),
    [(fila[0], fila[1]) for fila in FORMAS_DEL_NUMERO + FORMAS_DE_LA_OBRA],
    ids=[fila[0] for fila in FORMAS_DEL_NUMERO + FORMAS_DE_LA_OBRA],
)
def test_f032_r6_el_saneo_vive_en_normalizar_codigo(etiqueta: str, entrada: str):
    """R6 · al salir de aquí no queda **ni un blanco** que limpiar después.

    Se afirma sobre `normalizar_codigo` directamente porque es donde el
    requisito dice que vive el arreglo: de ahí heredan las dos conversiones y
    la carpeta. Comprobarlo solo por sus resultados dejaría pasar un saneo
    local en una de las puntas, que es exactamente lo que F-028 R47 prohíbe
    —dos criterios del mismo concepto divergen siempre—.

    Y tiene una consecuencia que conviene ver: si aquí no queda ningún blanco,
    ninguna punta **puede** necesitar quitarlo.
    """
    normalizado = normalizar_codigo(entrada)

    assert not any(caracter.isspace() for caracter in normalizado), (
        f"la forma «{etiqueta}» conserva un blanco: «{normalizado}»"
    )


# --------------------------------------------------------------------------
# R7, R28 · Todas las formas mandan al ERP el mismo código
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("etiqueta", "entrada", "esperado"),
    [(fila[0], fila[1], fila[2]) for fila in FORMAS_DEL_NUMERO],
    ids=[fila[0] for fila in FORMAS_DEL_NUMERO],
)
def test_f032_r7_todas_las_formas_dan_el_mismo_codigo_para_el_erp(
    etiqueta: str, entrada: str, esperado: str
):
    """R7, R28 · la tabla de `design.md` §5, columna del ERP.

    Igualdad exacta contra la cadena literal, porque **la búsqueda en Sigrid es
    por igualdad exacta** (`WHERE c.tip = ? AND c.cod = ?`, sin `LIKE`, sin
    `REPLACE` y sin `TRIM`): un código con un espacio de más no devuelve «casi»
    la reclamación, devuelve **cero filas**, y el parte se queda sin cerrar.

    La fila 7 es la del 2026-09-17, y es la que hay que mirar cuando este test
    se ponga rojo.
    """
    assert a_codigo_de_sigrid(entrada) == esperado, (
        f"la forma «{etiqueta}» no llega al ERP como la canónica"
    )


def test_f032_r28_la_tabla_entera_produce_un_unico_codigo_por_incidencia():
    """R28 · la propiedad entera, que el caso a caso no afirma.

    Trece resultados podrían ser todos distintos del esperado y aun así iguales
    entre sí, o al revés. Aquí se afirma de una vez: las trece formas son **dos
    incidencias** y no trece.
    """
    codigos = {a_codigo_de_sigrid(entrada) for entrada in ENTRADAS_DEL_NUMERO}

    assert codigos == {CANONICO_0149, CANONICO_0178}


# --------------------------------------------------------------------------
# R8, R28 · Todas las formas se archivan con el mismo nombre canónico
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("etiqueta", "entrada", "esperado"),
    [(fila[0], fila[1], fila[3]) for fila in FORMAS_DEL_NUMERO],
    ids=[fila[0] for fila in FORMAS_DEL_NUMERO],
)
def test_f032_r8_todas_las_formas_dan_el_mismo_nombre_de_fichero(
    etiqueta: str, entrada: str, esperado: str
):
    """R8, R28 · la tabla de `design.md` §5, columna del nombre del fichero.

    El daño de esta columna es **silencioso**: `nombre_admisible` acepta un
    nombre con un espacio interior —no lleva carácter prohibido, no empieza ni
    acaba en espacio y no acaba en punto—, así que el mismo parte puede acabar
    en SharePoint con dos nombres distintos, uno por cada lectura, y a ojo son
    el mismo fichero.
    """
    assert (
        nombre_de_archivo(codigo_obra=OBRA, numero_incidencia=entrada) == esperado
    ), f"la forma «{etiqueta}» se archivaría con otro nombre"


def test_f032_r28_la_tabla_entera_produce_un_unico_nombre_por_incidencia():
    """R28 · un solo nombre canónico para todas las formas de leer el número.

    Es lo que impide que la carpeta de Posventa acumule duplicados del mismo
    parte, cada uno con el DNI manuscrito de un cliente dentro.
    """
    nombres = {
        nombre_de_archivo(codigo_obra=OBRA, numero_incidencia=entrada)
        for entrada in ENTRADAS_DEL_NUMERO
    }

    assert nombres == {NOMBRE_0149, NOMBRE_0178}


@pytest.mark.parametrize("entrada", ENTRADAS_DEL_NUMERO, ids=ENTRADAS_DEL_NUMERO)
def test_f032_r8_el_nombre_no_lleva_ni_barra_ni_ningun_blanco_de_mas(entrada: str):
    """R8 · las dos formas de estropear el nombre, comprobadas aparte.

    Una barra viva partiría el fichero en dos carpetas (F-006 R2). Un espacio de
    más no rompe nada técnicamente, pero SharePoint lo conserva y el fichero
    deja de encontrarse buscando el nombre que la gente escribe. El único
    espacio doble admisible sería ninguno: el separador es ` - ` y el sufijo va
    pegado.
    """
    nombre = nombre_de_archivo(codigo_obra=OBRA, numero_incidencia=entrada)

    assert "/" not in nombre
    assert "  " not in nombre
    assert nombre.endswith(" PARTE FIRMADO.pdf")


# --------------------------------------------------------------------------
# R9, R28 · El código de obra decide la carpeta
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("etiqueta", "entrada", "normalizado", "carpeta"),
    FORMAS_DE_LA_OBRA,
    ids=[fila[0] for fila in FORMAS_DE_LA_OBRA],
)
def test_f032_r9_el_codigo_de_obra_con_espacios_no_cambia_la_carpeta(
    etiqueta: str, entrada: str, normalizado: str, carpeta: str
):
    """R9, R28 · la tabla de la obra de `design.md` §5, entera.

    Este es el daño que **no se ve**. Un cierre fallido salta a la vista: el
    parte se queda abierto y alguien lo mira. Un PDF con el DNI manuscrito de
    un cliente archivado en `Postventa/06 26` —que para Graph es otra carpeta
    distinta de `Postventa/0626`— no se lo encuentra nadie y nadie lo echa en
    falta.

    Se afirma la carpeta **y** el primer tramo del nombre, porque el mismo
    código de obra decide los dos.
    """
    assert normalizar_codigo(entrada) == normalizado
    assert carpeta_de_archivo(carpeta_base=BASE, codigo_obra=entrada) == carpeta, (
        f"la forma «{etiqueta}» archivaría en otra carpeta"
    )
    assert nombre_de_archivo(
        codigo_obra=entrada, numero_incidencia=CANONICO_0178
    ).startswith(f"{normalizado} - ")


def test_f032_r28_las_formas_de_la_misma_obra_dan_una_unica_carpeta():
    """R28 · las cuatro formas de `0626` son **una** carpeta, no cuatro."""
    carpetas = {
        carpeta_de_archivo(carpeta_base=BASE, codigo_obra=entrada)
        for entrada in ("0626", "06 26", "06  26", "06\u00a026")
    }

    assert carpetas == {"Postventa/0626"}


# --------------------------------------------------------------------------
# R10 · Las dos conversiones siguen siendo idempotentes
# --------------------------------------------------------------------------


@pytest.mark.parametrize("entrada", ENTRADAS_DEL_NUMERO, ids=ENTRADAS_DEL_NUMERO)
def test_f032_r10_las_dos_conversiones_siguen_siendo_idempotentes(entrada: str):
    """R10 · aplicarlas dos veces sobre su propio resultado da lo mismo (F-009 R6).

    Si dejaran de serlo, lo que se manda al ERP dependería de **cuántas veces**
    ha pasado el parte por el pipeline, que es un bug que solo aparece cuando
    alguien reprocesa un parte y que nadie relaciona con su causa.
    """
    una_vez = a_codigo_de_sigrid(entrada)
    assert a_codigo_de_sigrid(una_vez) == una_vez

    normalizado = normalizar_codigo(entrada)
    assert normalizar_codigo(normalizado) == normalizado

    nombre = nombre_de_archivo(codigo_obra=OBRA, numero_incidencia=entrada)
    tramo = nombre.removeprefix(f"{OBRA} - ").removesuffix(" PARTE FIRMADO.pdf")
    assert a_codigo_de_sigrid(tramo) == una_vez
