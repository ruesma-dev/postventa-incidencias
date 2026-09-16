# services/postventa-api/tests/test_f028_espacios_codigos.py
"""Los espacios de los códigos: todas las formas del mismo número (F-028, R44–R46).

Esto no lo pidió un diseño. Lo pidió el responsable **el mismo día que vio
fallar el circuito en real**, el 2026-09-15: la IA leyó el número del papel como
`RS26.09 / 0149` —con un espacio a cada lado de la barra— y el cierre en el ERP
no encontró la reclamación, porque la búsqueda es **por igualdad exacta**.

Lo que hace este defecto difícil de ver a ojo, y por lo que merece un fichero
propio en vez de un caso suelto:

1. **El nombre del fichero sale bien por casualidad.** La barra se convierte en
   `" - "` y el colapso de espacios posterior se come el sobrante. Así que el
   parte se archiva con el nombre correcto **y solo falla el cierre**: medio
   circuito en verde tapando la mitad rota.
2. **Salvo una forma, que rompe las dos.** `RS26.09- 0149` —guion pegado por
   delante, espacio por detrás— produce además un nombre **distinto** del
   canónico, y ese sí deja dos ficheros que a ojo son el mismo parte.

Por eso la tabla de `design.md` §9.3 se recorre **entera y para las dos
conversiones**, fila a fila: cualquiera de las seis formas tiene que dar el
mismo código para el ERP (R45) y el mismo nombre de fichero (R46), y el saneo
vive donde lo dice R44 —en `normalizar_codigo`—, no en una de las dos puntas.

**Dominio puro.** Sin red, sin base de datos, sin IA y sin reloj: dos cadenas
entran y una cadena sale. El defecto que cuesta un cierre fallido en producción
se prueba entero en memoria, y eso es justamente lo que lo hace barato de fijar
para siempre.

**Ni un dato real.** `0626` y `RS26.09/0149` son los de la tabla de `design.md`
§9.3, y son **inventados**: un parte de verdad lleva DNI y observaciones
manuscritas de un cliente, y eso no entra en un test.
"""

from __future__ import annotations

import pytest
from domain.models.cierre import a_codigo_de_sigrid
from domain.models.errores import NombradoImposible
from domain.models.nombrado import (
    SEPARADORES_DE_CODIGO,
    carpeta_de_archivo,
    nombre_de_archivo,
    normalizar_codigo,
    tramos_de_codigo,
)

#: El código de obra de la tabla. **Inventado**: no es de nadie.
OBRA = "0626"

#: Cómo lo escribe Sigrid, que es la forma canónica del número de incidencia.
CODIGO_DE_SIGRID = "RS26.09/0149"

#: El nombre del fichero que tiene que salir, **escrito literal**.
#:
#: No se compone a partir de `SEPARADOR`, `SUFIJO` y `EXTENSION` a propósito: un
#: test que se construye con las mismas piezas que vigila da verde aunque las
#: piezas cambien, y aquí lo que se afirma es que las seis formas producen
#: **esta** cadena y ninguna parecida.
NOMBRE_DE_ARCHIVO = "0626 - RS26.09 - 0149 PARTE FIRMADO.pdf"

#: La tabla de `design.md` §9.3, fila a fila, con la etiqueta de cada forma.
#:
#: Las seis son **el mismo número de incidencia** leído del mismo papel por la
#: IA, y las seis tienen que acabar en el mismo sitio. El orden es el de la
#: spec para que un fallo se pueda leer contra ella sin traducir nada.
FORMAS_EQUIVALENTES = (
    ("barra pegada (la canónica)", "RS26.09/0149"),
    ("barra con espacio a los dos lados", "RS26.09 / 0149"),
    ("barra con espacio solo delante", "RS26.09 /0149"),
    ("guion normal con espacio a los dos lados", "RS26.09 - 0149"),
    ("guion normal pegado delante y con espacio detrás", "RS26.09- 0149"),
    ("guion largo con espacio a los dos lados", "RS26.09 – 0149"),
)

#: Solo las entradas, para parametrizar sin arrastrar la etiqueta.
ENTRADAS = tuple(entrada for _, entrada in FORMAS_EQUIVALENTES)


# --------------------------------------------------------------------------
# R44 · El saneo vive en `normalizar_codigo`, y quita los espacios del separador
# --------------------------------------------------------------------------


@pytest.mark.parametrize(("etiqueta", "entrada"), FORMAS_EQUIVALENTES)
def test_f028_r44_normalizar_quita_los_espacios_que_rodean_al_separador(
    etiqueta, entrada
):
    """R44 · las seis formas normalizan a **un solo** código, sin espacios.

    Se afirma sobre `normalizar_codigo` directamente porque es **donde el
    requisito dice que vive el arreglo**: de ahí heredan las dos conversiones
    (`design.md` §9.1). Comprobarlo solo por sus resultados dejaría pasar un
    saneo local en una de las dos puntas, que es exactamente lo que R47
    prohíbe.

    El código normalizado lleva el separador que traía —barra o guion—, pero
    **nunca** un espacio pegado a él.
    """
    normalizado = normalizar_codigo(entrada)

    assert normalizado in ("RS26.09/0149", "RS26.09-0149"), (
        f"la forma «{etiqueta}» normaliza a «{normalizado}»"
    )
    assert " " not in normalizado, (
        f"la forma «{etiqueta}» conserva un espacio: «{normalizado}»"
    )


def test_f028_r44_el_espacio_se_quita_por_los_dos_lados_del_separador():
    """R44 · «los espacios que rodean», dice el requisito: delante y detrás.

    Los tres casos se escriben aparte porque son **tres bugs distintos**: un
    arreglo que solo mire hacia atrás deja vivo `RS26.09 /0149`, y uno que solo
    mire hacia delante deja vivo `RS26.09- 0149`, que es justo la forma que
    además estropea el nombre del fichero.
    """
    assert normalizar_codigo("RS26.09 /0149") == "RS26.09/0149"
    assert normalizar_codigo("RS26.09/ 0149") == "RS26.09/0149"
    assert normalizar_codigo("RS26.09 / 0149") == "RS26.09/0149"


def test_f028_r44_tambien_con_varios_espacios_seguidos():
    """R44 · el colapso de R8 y este saneo tienen que componerse, no pelearse.

    Un escaneo no trae un espacio: trae los que el OCR quiera. Si el saneo
    solo supiera quitar **uno**, `RS26.09   /   0149` seguiría roto.
    """
    assert normalizar_codigo("RS26.09   /   0149") == "RS26.09/0149"
    assert normalizar_codigo("  RS26.09  -  0149  ") == "RS26.09-0149"


# --------------------------------------------------------------------------
# R45 · Todas las formas mandan al ERP el mismo código
# --------------------------------------------------------------------------


@pytest.mark.parametrize(("etiqueta", "entrada"), FORMAS_EQUIVALENTES)
def test_f028_r45_todas_las_formas_dan_el_mismo_codigo_para_el_erp(
    etiqueta, entrada
):
    """R45 · la tabla de `design.md` §9.3, columna `a_codigo_de_sigrid`.

    Igualdad exacta contra la cadena literal, porque **la búsqueda de la
    reclamación en Sigrid es por igualdad exacta**: un código con un espacio de
    más no devuelve «casi» la reclamación, no devuelve ninguna, y el parte se
    queda sin cerrar sin que nadie se entere hasta que alguien lo mire a mano.
    """
    assert a_codigo_de_sigrid(entrada) == CODIGO_DE_SIGRID, (
        f"la forma «{etiqueta}» no llega al ERP como la canónica"
    )


def test_f028_r45_las_seis_formas_producen_un_unico_codigo():
    """R45 · dicho de otra manera: el conjunto de resultados tiene **un** valor.

    Es la afirmación que el caso a caso no hace: seis resultados podrían ser
    todos distintos del esperado y aun así iguales entre sí, o al revés. Aquí
    se afirma la propiedad entera de una vez.
    """
    assert {a_codigo_de_sigrid(entrada) for entrada in ENTRADAS} == {
        CODIGO_DE_SIGRID
    }


def test_f028_r45_el_codigo_ya_saneado_no_se_vuelve_a_mover():
    """R45 · la conversión sigue siendo idempotente (F-009 R6).

    Si el arreglo hiciera que aplicarla dos veces diera algo distinto, el
    código que se manda al ERP dependería de cuántas veces ha pasado por el
    pipeline, que es un bug que solo aparece cuando alguien reprocesa un parte.
    """
    for entrada in ENTRADAS:
        una_vez = a_codigo_de_sigrid(entrada)

        assert a_codigo_de_sigrid(una_vez) == una_vez


# --------------------------------------------------------------------------
# R46 · Todas las formas se archivan con el mismo nombre canónico
# --------------------------------------------------------------------------


@pytest.mark.parametrize(("etiqueta", "entrada"), FORMAS_EQUIVALENTES)
def test_f028_r46_todas_las_formas_dan_el_mismo_nombre_de_fichero(
    etiqueta, entrada
):
    """R46 · la tabla de `design.md` §9.3, columna `nombre_de_archivo`.

    Cinco de las seis formas ya salían bien **por casualidad** —la barra pasa a
    `" - "` y el colapso posterior se come el sobrante—, y por eso el defecto
    llevaba tiempo sin verse. La sexta, `RS26.09- 0149`, no: produce un nombre
    distinto, y dos nombres distintos del mismo parte son dos ficheros en la
    carpeta de Posventa que a ojo son el mismo.
    """
    assert (
        nombre_de_archivo(codigo_obra=OBRA, numero_incidencia=entrada)
        == NOMBRE_DE_ARCHIVO
    ), f"la forma «{etiqueta}» se archivaría con otro nombre"


def test_f028_r46_las_seis_formas_producen_un_unico_nombre():
    """R46 · la propiedad entera: un solo nombre para las seis lecturas.

    Es lo que impide que el archivo de Posventa acumule duplicados: el mismo
    parte leído dos veces por la IA, con el espacio en distinto sitio, tiene
    que sobrescribir el mismo fichero y no crear uno nuevo.
    """
    nombres = {
        nombre_de_archivo(codigo_obra=OBRA, numero_incidencia=entrada)
        for entrada in ENTRADAS
    }

    assert nombres == {NOMBRE_DE_ARCHIVO}


def test_f028_r46_el_nombre_no_lleva_ni_barra_ni_espacios_dobles():
    """R46 · las dos formas de estropear el nombre, comprobadas aparte.

    Una barra viva partiría el fichero en dos carpetas (F-006 R2). Un espacio
    doble no rompe nada técnicamente, pero SharePoint lo conserva y el fichero
    deja de encontrarse buscando el nombre que la gente escribe.
    """
    for entrada in ENTRADAS:
        nombre = nombre_de_archivo(codigo_obra=OBRA, numero_incidencia=entrada)

        assert "/" not in nombre
        assert "  " not in nombre


# --------------------------------------------------------------------------
# R45 + R46 · Las dos conversiones son la ida y la vuelta del mismo camino
# --------------------------------------------------------------------------


@pytest.mark.parametrize("entrada", ENTRADAS)
def test_f028_r45_r46_el_nombre_del_fichero_devuelve_el_codigo_del_erp(entrada):
    """Ida y vuelta: del papel al nombre, y del nombre al ERP.

    Es el circuito real de un parte: F-006 lo archiva con ese nombre y F-009
    saca de ahí el código con el que busca la reclamación. Si las dos
    conversiones dejaran de ser inversas exactas (R47), el parte quedaría
    archivado bien y sin cerrar, que es el fallo del 2026-09-15.
    """
    nombre = nombre_de_archivo(codigo_obra=OBRA, numero_incidencia=entrada)
    tramo_de_la_incidencia = nombre.removeprefix(f"{OBRA} - ").removesuffix(
        " PARTE FIRMADO.pdf"
    )

    assert a_codigo_de_sigrid(tramo_de_la_incidencia) == CODIGO_DE_SIGRID


# --------------------------------------------------------------------------
# Los tramos · la pieza que hace inversas exactas a las dos conversiones (R47)
# --------------------------------------------------------------------------


def test_f028_los_dos_separadores_estan_declarados():
    """`SEPARADORES_DE_CODIGO` son la barra y el guion, y **solo** esos dos.

    Se escriben **a mano**, no iterando la constante: un test que recorre lo
    que vigila da verde aunque alguien la vacíe. Y se afirma que no hay un
    tercero: meter aquí el punto partiría `RS26.09` por la mitad.
    """
    assert "/" in SEPARADORES_DE_CODIGO
    assert "-" in SEPARADORES_DE_CODIGO
    assert set(SEPARADORES_DE_CODIGO) == {"/", "-"}


@pytest.mark.parametrize(
    "codigo", ("RS26.09/0149", "RS26.09-0149")
)
def test_f028_r47_la_barra_y_el_guion_dan_los_mismos_tramos(codigo):
    """R47 · es **esto** lo que hace que las dos conversiones no diverjan.

    Escrito con barra o con guion, el código son los mismos dos tramos. A
    partir de ahí, una conversión los une con ` - ` y la otra con `/`, y
    ninguna de las dos tiene que saber cómo venía escrito el papel.
    """
    assert tramos_de_codigo(codigo) == ("RS26.09", "0149")


def test_f028_un_codigo_sin_separador_es_un_solo_tramo():
    """Un código que no lleva separador no se parte en nada.

    Es el caso corriente del código de obra si alguien lo pasara por aquí, y
    el de un número de incidencia que Sigrid emitiera sin barra.
    """
    assert tramos_de_codigo("RS26090149") == ("RS26090149",)


@pytest.mark.parametrize(
    ("codigo", "tramos"),
    (
        ("", ()),
        ("/", ()),
        ("-", ()),
        ("//-", ()),
        ("/0149", ("0149",)),
        ("RS26.09/", ("RS26.09",)),
        ("A/B/C", ("A", "B", "C")),
    ),
)
def test_f028_los_tramos_vacios_se_descartan(codigo, tramos):
    """Un separador suelto no produce un tramo vacío.

    Si los tramos vacíos sobrevivieran, `/0149` se uniría como ` - 0149` y el
    nombre del fichero saldría con un espacio doble donde no hay nada que
    separar. Descartarlos aquí es lo que permite que quien nombra el fichero
    pueda distinguir «no hay ningún tramo» y negarse (R49).
    """
    assert tramos_de_codigo(codigo) == tramos


# --------------------------------------------------------------------------
# R48 · Lo que el arreglo NO puede tocar de F-006
# --------------------------------------------------------------------------


@pytest.mark.parametrize("obra", ("0626", "0000626", "007", "0"))
def test_f028_r48_los_ceros_a_la_izquierda_siguen_intactos(obra):
    """R48 · F-006 R4 sigue en pie: `0626` nunca es `626`.

    Es la garantía más cara de romper de las tres: un cero perdido archiva el
    parte en la carpeta de otra promoción, y ahí no lo busca nadie.
    """
    assert nombre_de_archivo(
        codigo_obra=obra, numero_incidencia=CODIGO_DE_SIGRID
    ).startswith(f"{obra} - ")


def test_f028_r48_el_codigo_de_obra_no_se_parte_en_tramos():
    """R48 · la obra **no** pasa por los tramos, y es deliberado.

    `06-77` es **una** obra escrita con guion, no dos tramos. Si la obra se
    compusiera por tramos, el guion pasaría a ` - ` y —peor— la carpeta se
    partiría en una subcarpeta que nadie pidió. La obra solo se normaliza.
    """
    assert nombre_de_archivo(
        codigo_obra="06-77", numero_incidencia=CODIGO_DE_SIGRID
    ) == "06-77 - RS26.09 - 0149 PARTE FIRMADO.pdf"

    assert (
        carpeta_de_archivo(carpeta_base="Postventa", codigo_obra="06-77")
        == "Postventa/06-77"
    )


def test_f028_r48_el_guion_raro_del_codigo_de_obra_sigue_normalizando():
    """R48 · F-006 R3 sigue en pie también para la obra, y sin partirla.

    El guion largo de `06–77` pasa a guion normal —dos lecturas del mismo
    papel tienen que dar la misma carpeta— pero el código sigue siendo uno.
    """
    assert normalizar_codigo("06–77") == "06-77"


def test_f028_r48_el_sufijo_y_la_extension_siguen_literales():
    """R48 · F-006 R5 sigue en pie: ` PARTE FIRMADO` y `.pdf`, sin tocar."""
    nombre = nombre_de_archivo(
        codigo_obra=OBRA, numero_incidencia="RS26.09 / 0149"
    )

    assert nombre.endswith(" PARTE FIRMADO.pdf")
    assert nombre.count("PARTE FIRMADO") == 1


def test_f028_r48_un_caracter_prohibido_sigue_sin_sanearse_en_silencio():
    """R48 · F-006 R7 sigue en pie: error ruidoso, nunca un `_` por lo bajo.

    Se inyecta en la **obra** porque la barra del nº de incidencia ya no llega
    nunca a la comprobación: ahora es un separador de tramos.
    """
    with pytest.raises(NombradoImposible) as fallo:
        nombre_de_archivo(codigo_obra="06|77", numero_incidencia=CODIGO_DE_SIGRID)

    assert "_" not in fallo.value.motivo


# --------------------------------------------------------------------------
# R49 · Un código que se queda sin nada sigue siendo un error
# --------------------------------------------------------------------------


@pytest.mark.parametrize("ausente", (None, "", "   ", "\t", "\n  \t "))
def test_f028_r49_un_codigo_vacio_sigue_siendo_nombrado_imposible(ausente):
    """R49 · F-006 R6 **sin cambios**: sin nº de incidencia no se archiva.

    El arreglo de los espacios no puede convertir un código ausente en un
    nombre con un hueco: un parte archivado con un número inventado es peor
    que un parte sin archivar, porque el segundo lo ve alguien.
    """
    with pytest.raises(NombradoImposible) as fallo:
        nombre_de_archivo(codigo_obra=OBRA, numero_incidencia=ausente)

    assert "incidencia" in fallo.value.motivo.lower()


@pytest.mark.parametrize("solo_separadores", ("/", "-", " / ", "//", " - - "))
def test_f028_r49_un_codigo_de_solo_separadores_tampoco_se_archiva(
    solo_separadores,
):
    """R49 · el hueco que abre componer por tramos, tapado en el mismo sitio.

    `"/"` **no** normaliza a la cadena vacía —es un carácter—, así que la
    guardia de R6 lo deja pasar. Pero no tiene ni un tramo, y unir cero tramos
    daría `0626 -  PARTE FIRMADO.pdf`, con un espacio doble y sin número:
    un nombre que `nombre_admisible` acepta —no lleva carácter prohibido, ni
    empieza ni acaba en espacio— y que en la carpeta de Posventa no significa
    nada. Se niega, como manda R7: error ruidoso, no saneo silencioso.
    """
    with pytest.raises(NombradoImposible) as fallo:
        nombre_de_archivo(
            codigo_obra=OBRA, numero_incidencia=solo_separadores
        )

    assert "incidencia" in fallo.value.motivo.lower()
