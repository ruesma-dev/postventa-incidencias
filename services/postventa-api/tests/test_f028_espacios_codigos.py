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
from domain.models.nombrado import nombre_de_archivo, normalizar_codigo

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
