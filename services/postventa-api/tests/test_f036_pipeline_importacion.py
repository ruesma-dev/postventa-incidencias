# services/postventa-api/tests/test_f036_pipeline_importacion.py
"""La aplicación de la plantilla y de la importación (F-036 T17).

`specs/F-036-importar-excel/design.md` §7.2 y §7.3:

- `application/pipelines/plantilla.py`: la plantilla de una obra, con los
  grupos vigentes de oficio aplicados, y su nombre de fichero;
- `application/pipelines/contexto_importacion.py` y `paso_importacion.py`: los
  seis pasos de la importación —huella, reconocimiento, catálogo, validación,
  registro y Excel de errores—, **en ese orden**.

Lo que se fija aquí, con dobles de los puertos (`tests/utiles_importacion.py`)
y el lector y el generador de verdad sobre libros en memoria:

- el orden de los pasos, y que un paso fuera de orden revienta;
- el atajo de R39, **solo** con una importación completa;
- R21: un fichero que no es la plantilla no llega ni a Sigrid ni a la base;
- la importación parcial, con el Excel de errores **después** del registro
  (R40: si la base falla, no hay Excel de una importación que no consta);
- cero válidas (R70), sin errores (R69), R67 y R68;
- los grupos de oficio aplicados en la validación y en la plantilla;
- R47: nada de la fila, del fichero ni de quien sube en los logs.

Ni un dato real: la obra, las unidades, los proveedores y los textos son
inventados. Ningún GUID literal (F-006 R26): `UUID(int=n)`.
"""

from __future__ import annotations

import ast
import dataclasses
import hashlib
import itertools
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID

import pytest
from application.pipelines import paso_importacion, plantilla
from application.pipelines.contexto_importacion import (
    ContextoImportacion,
    ExcelDeErrores,
)
from application.pipelines.paso_importacion import (
    fila_del_excel_de_errores,
    nombre_del_excel_de_errores,
    paso_catalogo,
    paso_excel_errores,
    paso_huella,
    paso_reconocimiento,
    paso_registro,
    paso_validacion,
)
from application.pipelines.plantilla import (
    generar_plantilla,
    nombre_de_la_plantilla,
    opciones_de_la_obra,
)
from domain.models.equivalencias import DISTINTO, Catalogo, DecisionPar
from domain.models.errores import (
    CatalogoNoDisponible,
    CodigoDeObraInvalido,
    FicheroDemasiadoGrande,
    FicheroNoEsPlantilla,
    ObraSinUnidades,
    PersistenciaNoDisponible,
)
from domain.models.importacion import (
    FALTA_DESCRIPCION,
    UNIDAD_FUERA_DE_LISTA,
    CeldaLeida,
    ErrorDeFila,
    EstadoFilaImportada,
    EstadoImportacion,
    FilaConError,
    FilaLeida,
    LibroLeido,
)
from domain.models.plantilla_incidencias import (
    CABECERA,
    COLUMNA_ERRORES,
    IDENTIFICADOR_PLANTILLA,
    OficioObra,
    ProveedorEnObra,
)
from domain.ports.catalogo_obra import FilaOficioCatalogo
from infrastructure.documentos.excel_openpyxl import HOJA_INCIDENCIAS
from infrastructure.documentos.plantilla_yaml import cargar_plantilla_yaml

from tests.utiles_importacion import (
    AHORA,
    OBRA_REF,
    VILLA_1,
    VILLA_2,
    BandejaEnMemoria,
    CatalogoEnMemoria,
    EquivalenciasEnMemoria,
    GeneradorQueAnota,
    LectorQueAnota,
    fichero,
    fila,
    filas_de_oficios,
)
from tests.utiles_plantilla import abrir, catalogo, mismo

SERVICIO = Path(__file__).resolve().parents[1]
CONFIG = cargar_plantilla_yaml()

#: Lo que no puede salir en un log (R47): todo inventado.
NOMBRE_FICHERO = "incidencias de Fulanita de Tal.xlsx"
OID = "oid-inventado-de-quien-sube"
DESCRIPCION = "Grieta en el tabique del salón"
DETALLE = "Llamar a Fulanita de Tal antes de ir"

#: Las filas de ejemplo: una buena y una con la unidad tecleada en minúsculas.
BUENA = fila(
    unidad=VILLA_1, ubicacion="Almacén", descripcion=DESCRIPCION, detalle=DETALLE
)
MALA = fila(unidad="viviendas bloque villa 2", descripcion="Puerta que no cierra")

#: Los pasos, por el nombre de la llamada que hace cada uno.
ORDEN_COMPLETO = [
    "bandeja.importacion_completa_por_hash",
    "lector.leer",
    "catalogo.leer_unidades",
    "catalogo.leer_oficios",
    "equivalencias.ultimas_decisiones",
    "bandeja.registrar",
    "generador.generar",
]


@dataclass
class Mundo:
    """Los dobles de una prueba, anotando en la misma lista."""

    decisiones: tuple[DecisionPar, ...] = ()
    llamadas: list[str] = field(default_factory=list)
    ids: itertools.count = field(default_factory=lambda: itertools.count(1))

    def __post_init__(self) -> None:
        self.bandeja = BandejaEnMemoria(self.llamadas)
        self.lector = LectorQueAnota(self.llamadas)
        self.catalogo = CatalogoEnMemoria(self.llamadas)
        self.equivalencias = EquivalenciasEnMemoria(self.llamadas, self.decisiones)
        self.generador = GeneradorQueAnota(self.llamadas)

    def nuevo_id(self) -> UUID:
        return UUID(int=next(self.ids))

    def importar(
        self,
        contenido: bytes,
        *,
        ahora: datetime = AHORA,
        nombre: str = NOMBRE_FICHERO,
    ) -> ContextoImportacion:
        """Los seis pasos, compuestos como los compondrá el handler (T18)."""
        contexto = ContextoImportacion(
            contenido=contenido, nombre_fichero=nombre, usuario_oid=OID, ahora=ahora
        )
        contexto = paso_huella(contexto, self.bandeja)
        contexto = paso_reconocimiento(contexto, self.lector)
        contexto = paso_catalogo(contexto, self.catalogo, self.equivalencias)
        contexto = paso_validacion(contexto, CONFIG.listas)
        contexto = paso_registro(contexto, self.bandeja, nuevo_id=self.nuevo_id)
        return paso_excel_errores(
            contexto, self.generador, CONFIG.listas, CONFIG.textos
        )


def _incidencias(contenido: bytes) -> list[tuple]:
    """Las filas de datos de «Incidencias» del Excel de errores, hasta la última con algo."""
    hoja = abrir(contenido)[HOJA_INCIDENCIAS]
    filas = [
        tuple(c.value for c in fila_)
        for fila_ in hoja.iter_rows(min_row=2, max_col=len(CABECERA))
    ]
    while filas and not any(filas[-1]):
        filas.pop()
    return filas


# --------------------------------------------------------------------------
# el orden de los pasos
# --------------------------------------------------------------------------


def test_f036_t17_los_seis_pasos_llaman_a_los_puertos_en_su_orden():
    mundo = Mundo()

    contexto = mundo.importar(fichero(BUENA, MALA))

    assert mundo.llamadas == ORDEN_COMPLETO
    assert contexto.excel_errores is not None


def test_f036_t17_sin_filas_con_error_no_se_llama_al_generador():
    mundo = Mundo()

    mundo.importar(fichero(BUENA))

    assert mundo.llamadas == ORDEN_COMPLETO[:-1]


def _contexto(**campos) -> ContextoImportacion:
    return ContextoImportacion(
        contenido=b"PK", nombre_fichero="f.xlsx", usuario_oid=OID, ahora=AHORA, **campos
    )


def test_f036_t17_reconocer_sin_huella_es_un_paso_fuera_de_orden():
    with pytest.raises(ValueError, match="fuera de orden"):
        paso_reconocimiento(_contexto(), LectorQueAnota([]))


def test_f036_t17_leer_el_catalogo_sin_reconocer_es_un_paso_fuera_de_orden():
    llamadas: list[str] = []
    with pytest.raises(ValueError, match="fuera de orden"):
        paso_catalogo(
            _contexto(hash="h"),
            CatalogoEnMemoria(llamadas),
            EquivalenciasEnMemoria(llamadas),
        )
    assert llamadas == []


def test_f036_t17_validar_sin_catalogo_es_un_paso_fuera_de_orden():
    libro = LectorQueAnota([]).leer(contenido=fichero(BUENA))
    with pytest.raises(ValueError, match="fuera de orden"):
        paso_validacion(
            _contexto(hash="h", libro=libro, obra_codigo="0677"), CONFIG.listas
        )


def test_f036_t17_registrar_sin_validar_es_un_paso_fuera_de_orden():
    llamadas: list[str] = []
    libro = LectorQueAnota([]).leer(contenido=fichero(BUENA))
    contexto = _contexto(hash="h", libro=libro, obra_codigo="0677", catalogo=catalogo())
    with pytest.raises(ValueError, match="fuera de orden"):
        paso_registro(contexto, BandejaEnMemoria(llamadas))
    assert llamadas == []


def test_f036_t17_el_excel_de_errores_antes_del_registro_es_un_paso_fuera_de_orden():
    """Va **después** del registro: sin `resultado`, ni se intenta."""
    llamadas: list[str] = []
    con_error = (FilaConError(FilaLeida(2, {}), (ErrorDeFila(2, "Unidad", "x"),)),)
    contexto = _contexto(hash="h", obra_codigo="0677", validas=(), con_error=con_error)
    with pytest.raises(ValueError, match="fuera de orden"):
        paso_excel_errores(
            contexto, GeneradorQueAnota(llamadas), CONFIG.listas, CONFIG.textos
        )
    assert llamadas == []


def test_f036_t17_el_excel_de_errores_sin_validar_es_un_paso_fuera_de_orden():
    with pytest.raises(ValueError, match="fuera de orden"):
        paso_excel_errores(
            _contexto(hash="h"), GeneradorQueAnota([]), CONFIG.listas, CONFIG.textos
        )


def test_f036_t17_el_contexto_exige_hora_con_zona():
    with pytest.raises(ValueError, match="zona horaria"):
        ContextoImportacion(
            contenido=b"",
            nombre_fichero="f",
            usuario_oid=OID,
            ahora=datetime(2026, 9, 30, 8),  # noqa: DTZ001 - sin zona a propósito
        )


def test_f036_t17_el_contexto_empieza_sin_validar():
    contexto = _contexto()
    assert contexto.validas is None
    assert contexto.con_error is None
    assert contexto.resultado is None
    assert contexto.excel_errores is None
    assert contexto.ya_importado is False


# --------------------------------------------------------------------------
# paso 1 · la huella y el atajo (R39)
# --------------------------------------------------------------------------


def test_f036_t17_la_huella_es_el_sha256_de_los_bytes():
    mundo = Mundo()
    contenido = fichero(BUENA)

    contexto = mundo.importar(contenido)

    esperado = hashlib.sha256(contenido).hexdigest()
    assert contexto.hash == esperado
    assert mundo.bandeja.hashes_pedidos == [esperado]
    assert mundo.bandeja.registradas[0][0].hash_fichero == esperado


def test_f036_r39_los_mismos_bytes_de_una_completa_no_leen_ni_escriben_nada():
    mundo = Mundo()
    contenido = fichero(BUENA)
    primera = mundo.importar(contenido)
    mundo.llamadas.clear()

    segunda = mundo.importar(contenido)

    assert mundo.llamadas == ["bandeja.importacion_completa_por_hash"]
    assert segunda.ya_importado is True
    assert segunda.resultado.importacion == primera.resultado.importacion
    assert segunda.resultado.filas == ()
    assert segunda.obra_codigo == "0677"
    assert segunda.excel_errores is None
    assert segunda.libro is None
    assert segunda.catalogo is None
    assert segunda.validas is None
    assert len(mundo.bandeja.registradas) == 1


def test_f036_r39_el_atajo_no_se_fia_de_la_obra_que_no_ha_leido():
    """La obra del atajo es la de la importación de entonces."""
    mundo = Mundo()
    contenido = fichero(BUENA)
    mundo.importar(contenido)

    contexto = paso_huella(
        ContextoImportacion(
            contenido=contenido, nombre_fichero="x", usuario_oid=OID, ahora=AHORA
        ),
        mundo.bandeja,
    )

    assert contexto.ya_importado
    assert contexto.obra_codigo == "0677"


def test_f036_r39_sin_atajo_la_huella_no_rellena_nada_mas():
    contexto = paso_huella(_contexto(), BandejaEnMemoria([]))

    assert contexto.hash == hashlib.sha256(b"PK").hexdigest()
    assert contexto.resultado is None
    assert contexto.obra_codigo is None
    assert contexto.ya_importado is False


@pytest.mark.parametrize(
    "paso",
    ["reconocimiento", "catalogo", "validacion", "registro", "excel_errores"],
)
def test_f036_r39_con_el_atajo_cada_paso_siguiente_no_hace_nada(paso):
    mundo = Mundo()
    contenido = fichero(BUENA)
    mundo.importar(contenido)
    contexto = paso_huella(
        ContextoImportacion(
            contenido=contenido, nombre_fichero="x", usuario_oid=OID, ahora=AHORA
        ),
        mundo.bandeja,
    )
    mundo.llamadas.clear()
    antes = contexto.resultado

    llamadas = {
        "reconocimiento": lambda c: paso_reconocimiento(c, mundo.lector),
        "catalogo": lambda c: paso_catalogo(c, mundo.catalogo, mundo.equivalencias),
        "validacion": lambda c: paso_validacion(c, CONFIG.listas),
        "registro": lambda c: paso_registro(c, mundo.bandeja, nuevo_id=mundo.nuevo_id),
        "excel_errores": lambda c: paso_excel_errores(
            c, mundo.generador, CONFIG.listas, CONFIG.textos
        ),
    }
    despues = llamadas[paso](contexto)

    assert despues is contexto
    assert mundo.llamadas == []
    assert contexto.resultado is antes
    assert contexto.excel_errores is None


def test_f036_r39_los_mismos_bytes_de_una_parcial_se_procesan_otra_vez():
    """R39, R67, R68: la buena sale `ya_en_bandeja` y el Excel se regenera."""
    mundo = Mundo()
    contenido = fichero(BUENA, MALA)
    primera = mundo.importar(contenido)
    mundo.llamadas.clear()

    segunda = mundo.importar(contenido)

    assert mundo.llamadas == ORDEN_COMPLETO
    assert segunda.ya_importado is False
    assert segunda.resultado.estado is EstadoImportacion.PARCIAL
    assert (
        segunda.resultado.importacion.importacion_id
        != primera.resultado.importacion.importacion_id
    )
    (buena,) = segunda.resultado.filas
    assert buena.estado is EstadoFilaImportada.YA_EN_BANDEJA
    assert buena.existente_id == primera.resultado.filas[0].incidencia_id
    assert segunda.excel_errores is not None
    assert _incidencias(segunda.excel_errores.contenido) == _incidencias(
        primera.excel_errores.contenido
    )


# --------------------------------------------------------------------------
# paso 2 · reconocer sin Sigrid ni base (R21)
# --------------------------------------------------------------------------


def _libro(**campos) -> LibroLeido:
    base = {
        "identificador": IDENTIFICADOR_PLANTILLA,
        "version": 1,
        "obra_codigo": "0677",
        "cabecera": CABECERA,
        "filas": (),
        "parece_formato_antiguo": False,
    }
    base.update(campos)
    return LibroLeido(**base)


@pytest.mark.parametrize(
    ("libro", "codigo"),
    [
        (_libro(identificador=None), "no_es_la_plantilla"),
        (_libro(identificador=None, parece_formato_antiguo=True), "formato_antiguo"),
        (_libro(version=2), "version_no_soportada"),
        (_libro(cabecera=CABECERA[1:]), "cabecera_distinta"),
        (_libro(obra_codigo="06 77/"), "obra_invalida"),
    ],
)
def test_f036_r21_un_fichero_que_no_es_la_plantilla_no_llega_a_sigrid_ni_a_la_base(
    libro, codigo
):
    mundo = Mundo()
    mundo.lector = LectorQueAnota(mundo.llamadas, libro)

    with pytest.raises(FicheroNoEsPlantilla) as rechazo:
        mundo.importar(b"PK\x03\x04 cualquier cosa")

    assert rechazo.value.codigo == codigo
    assert mundo.llamadas == ["bandeja.importacion_completa_por_hash", "lector.leer"]
    assert mundo.bandeja.registradas == []


def test_f036_r20_demasiadas_filas_tampoco_llega_a_sigrid():
    mundo = Mundo()
    filas = tuple(FilaLeida(n, {}) for n in range(2, 1003))
    mundo.lector = LectorQueAnota(mundo.llamadas, _libro(filas=filas))

    with pytest.raises(FicheroNoEsPlantilla, match="demasiadas_filas"):
        mundo.importar(b"PK")

    assert "catalogo.leer_unidades" not in mundo.llamadas


@pytest.mark.parametrize(
    ("contenido", "error"),
    [
        (b"esto no es un zip", FicheroNoEsPlantilla),
        (b"PK\x03\x04" + b"0" * (2 * 1024 * 1024), FicheroDemasiadoGrande),
    ],
    ids=["no_es_zip", "demasiado_grande"],
)
def test_f036_r21_lo_que_rechaza_el_lector_sube_tal_cual(contenido, error):
    mundo = Mundo()

    with pytest.raises(error):
        mundo.importar(contenido)

    assert mundo.llamadas == ["bandeja.importacion_completa_por_hash", "lector.leer"]


def test_f036_t17_el_reconocimiento_deja_el_libro_y_la_obra_normalizada():
    llamadas: list[str] = []
    libro = _libro(obra_codigo=" 0677 ")

    contexto = paso_reconocimiento(_contexto(hash="h"), LectorQueAnota(llamadas, libro))

    assert contexto.libro is libro
    assert contexto.obra_codigo == "0677"
    assert contexto.catalogo is None


# --------------------------------------------------------------------------
# paso 3 · el catálogo, con la obra de los metadatos y sus grupos
# --------------------------------------------------------------------------


def test_f036_t17_el_catalogo_se_lee_con_la_obra_de_los_metadatos():
    mundo = Mundo()

    contexto = mundo.importar(fichero(BUENA))

    assert mundo.catalogo.codigos_pedidos == ["0677"]
    assert contexto.catalogo == catalogo()
    assert mundo.equivalencias.pedidas == [
        (Catalogo.OFICIO, frozenset({"0046", "0085", "0133", "0166"}))
    ]


@pytest.mark.parametrize(
    "fallo",
    [
        ObraSinUnidades("sin unidades"),
        CatalogoNoDisponible("sin pasarela"),
    ],
)
def test_f036_t17_si_el_catalogo_falla_no_se_escribe_nada(fallo):
    mundo = Mundo()
    mundo.catalogo = CatalogoEnMemoria(mundo.llamadas, fallo=fallo)

    with pytest.raises(type(fallo)):
        mundo.importar(fichero(BUENA))

    assert mundo.bandeja.registradas == []
    assert "generador.generar" not in mundo.llamadas


def test_f036_t17_si_la_base_no_da_los_grupos_no_se_escribe_nada():
    mundo = Mundo()
    mundo.equivalencias = EquivalenciasEnMemoria(
        mundo.llamadas, fallo=PersistenciaNoDisponible("sin base")
    )

    with pytest.raises(PersistenciaNoDisponible):
        mundo.importar(fichero(BUENA))

    assert mundo.bandeja.registradas == []


def test_f036_t17_el_paso_de_catalogo_deja_grupos_y_opciones():
    mundo = Mundo(decisiones=(mismo("0085", "0166"),))

    contexto = mundo.importar(fichero(BUENA))

    assert contexto.grupos_oficio.catalogo is Catalogo.OFICIO
    assert contexto.grupos_proveedor.catalogo is Catalogo.PROVEEDOR
    assert [o.etiqueta for o in contexto.opciones_oficio] == [
        "Carpintería de madera",
        "Mamparas",
        "Albañilería",
    ]
    assert [p.etiqueta for p in contexto.opciones_proveedor] == [
        "Carpintería de madera · Carpinterías Ejemplo S.L.",
        "Carpintería de madera · Juan Ejemplo Ejemplo",
        "Mamparas · Mamparas Ejemplo S.A.",
    ]


# --------------------------------------------------------------------------
# los grupos de oficio, aplicados
# --------------------------------------------------------------------------


def test_f036_r92_con_el_grupo_confirmado_el_oficio_del_grupo_entra_ambiguo():
    """D-19 = (a): dos códigos en la obra y sin proveedor → `oficio_ambiguo`."""
    mundo = Mundo(decisiones=(mismo("0085", "0166"),))
    con_grupo = fila(unidad=VILLA_1, descripcion="Mampara rota", oficio="Mamparas")

    contexto = mundo.importar(fichero(con_grupo, decisiones=mundo.decisiones))

    (valida,) = contexto.validas
    assert valida.oficio.ambiguo is True
    assert valida.oficio.codigo is None
    assert valida.oficio.etiqueta == "Mamparas"
    assert contexto.con_error == ()


def test_f036_r94_con_el_grupo_confirmado_el_par_resuelve_el_proveedor():
    mundo = Mundo(decisiones=(mismo("0085", "0166"),))
    con_par = fila(
        unidad=VILLA_1,
        descripcion="Mampara rota",
        proveedor="Mamparas · Mamparas Ejemplo S.A.",
    )

    contexto = mundo.importar(fichero(con_par, decisiones=mundo.decisiones))

    (valida,) = contexto.validas
    assert valida.oficio.ambiguo is True
    assert valida.proveedor.codigo == "P002"


def test_f036_r92_con_el_grupo_confirmado_el_nombre_suelto_ya_no_vale():
    """Sin la decisión «Mampara» (0166) es una opción; con ella, un error de fila."""
    sin_grupo = Mundo()
    con_grupo = Mundo(decisiones=(mismo("0085", "0166"),))
    suelta = fila(unidad=VILLA_1, descripcion="Mampara rota", oficio="Mampara")

    antes = sin_grupo.importar(fichero(suelta))
    despues = con_grupo.importar(fichero(suelta))

    assert antes.validas[0].oficio.codigo == "0166"
    assert despues.validas == ()
    (error,) = despues.con_error[0].errores
    assert error.columna == "Oficio"


def test_f036_r82_una_decision_distinto_anula_la_componente_entera():
    """0046–0085 y 0085–0166 «mismo», pero 0046–0166 «distinto»: no se aplica."""
    distinto = DecisionPar(
        catalogo=Catalogo.OFICIO,
        codigo_a="0046",
        codigo_b="0166",
        decision=DISTINTO,
        motivos=frozenset(),
        obra_codigo="0677",
        decidido_por="oid-de-prueba",
        decidido_at_utc=AHORA,
    )
    mundo = Mundo(decisiones=(mismo("0046", "0085"), mismo("0085", "0166"), distinto))

    contexto = mundo.importar(fichero(BUENA))

    assert [o.etiqueta for o in contexto.opciones_oficio] == [
        "Carpintería de madera",
        "Mamparas",
        "Albañilería",
        "Mampara",
    ]
    assert contexto.grupos_oficio.no_aplicados == (frozenset({"0046", "0085", "0166"}),)


def test_f036_r86_la_etiqueta_del_grupo_es_la_del_oficio_con_mas_filas_en_obrofc():
    """Empate: el de código menor (0085, «Mamparas»); con más filas, 0166 manda."""
    llamadas: list[str] = []
    equivalencias = EquivalenciasEnMemoria(llamadas, (mismo("0085", "0166"),))
    mas_filas_0166 = catalogo(
        filas=(
            ProveedorEnObra("0085", "P002", "Mamparas Ejemplo S.A."),
            ProveedorEnObra("0166", "P002", "Mamparas Ejemplo S.A."),
            ProveedorEnObra("0166", "P004", "Cristales Ejemplo S.L."),
        )
    )

    empate = opciones_de_la_obra(catalogo(), equivalencias)
    desempate = opciones_de_la_obra(mas_filas_0166, equivalencias)

    assert "Mamparas" in [o.etiqueta for o in empate.oficios]
    assert "Mampara" in [o.etiqueta for o in desempate.oficios]
    assert "Mamparas" not in [o.etiqueta for o in desempate.oficios]


def test_f036_t17_las_opciones_de_la_obra_piden_solo_decisiones_de_oficio_de_la_obra():
    llamadas: list[str] = []
    equivalencias = EquivalenciasEnMemoria(llamadas)

    opciones = opciones_de_la_obra(catalogo(), equivalencias)

    assert equivalencias.pedidas == [
        (Catalogo.OFICIO, frozenset({"0046", "0085", "0133", "0166"}))
    ]
    assert [o.codigos_en_obra for o in opciones.oficios] == [
        ("0046",),
        ("0085",),
        ("0133",),
        ("0166",),
    ]
    assert opciones.grupos_proveedor.catalogo is Catalogo.PROVEEDOR
    assert sorted(c for g in opciones.grupos_proveedor.grupos for c in g.codigos) == [
        "P001",
        "P002",
        "P003",
    ]
    assert [p.filas_en_obra for p in opciones.proveedores] == [
        (("0046", "P001"),),
        (("0046", "P003"),),
        (("0085", "P002"),),
        (("0166", "P002"),),
    ]


def test_f036_r12_una_obra_sin_oficios_da_opciones_vacias():
    sin_oficios = catalogo(oficios=(), filas=())

    opciones = opciones_de_la_obra(sin_oficios, EquivalenciasEnMemoria([]))

    assert opciones.oficios == ()
    assert opciones.proveedores == ()


# --------------------------------------------------------------------------
# pasos 4 a 6 · validación, registro y Excel de errores
# --------------------------------------------------------------------------


def test_f036_r33_la_importacion_parcial_registra_las_buenas_y_devuelve_las_malas():
    mundo = Mundo()

    contexto = mundo.importar(fichero(BUENA, MALA))

    ((registro, grupos),) = mundo.bandeja.registradas
    assert registro.filas_leidas == 2
    assert registro.filas_con_error == 1
    assert registro.estado is EstadoImportacion.PARCIAL
    assert [v.fila for g in grupos for v in g.filas] == [2]
    assert contexto.resultado.estado is EstadoImportacion.PARCIAL
    assert contexto.resultado.nuevas == 1
    assert contexto.resultado.con_error == 1
    assert [f.fila.numero for f in contexto.con_error] == [3]
    assert contexto.agrupadas == grupos


def test_f036_r42_el_registro_lleva_quien_cuando_que_fichero_y_que_plantilla():
    mundo = Mundo()
    contenido = fichero(BUENA)

    mundo.importar(contenido, nombre="mi fichero.xlsx")

    ((registro, _),) = mundo.bandeja.registradas
    assert registro.importacion_id == UUID(int=1)
    assert registro.hash_fichero == hashlib.sha256(contenido).hexdigest()
    assert registro.nombre_fichero == "mi fichero.xlsx"
    assert registro.obra_codigo == "0677"
    assert registro.plantilla_version == 1
    assert registro.importado_por == OID
    assert registro.importado_at_utc == AHORA
    assert registro.estado is EstadoImportacion.COMPLETA


def test_f036_r37_las_repetidas_del_fichero_van_en_el_mismo_grupo():
    mundo = Mundo()
    otra_igual = fila(
        unidad=VILLA_1, ubicacion="Almacén", descripcion=DESCRIPCION + "."
    )

    contexto = mundo.importar(fichero(BUENA, otra_igual))

    (grupo,) = contexto.agrupadas
    assert [v.fila for v in grupo.filas] == [2, 3]
    assert [f.estado for f in contexto.resultado.filas] == [
        EstadoFilaImportada.NUEVA,
        EstadoFilaImportada.DUPLICADA_EN_FICHERO,
    ]


def test_f036_r40_si_la_base_falla_no_hay_excel_de_errores():
    mundo = Mundo()
    mundo.bandeja = BandejaEnMemoria(
        mundo.llamadas, fallo_al_registrar=PersistenciaNoDisponible("sin base")
    )
    contexto = ContextoImportacion(
        contenido=fichero(BUENA, MALA), nombre_fichero="f", usuario_oid=OID, ahora=AHORA
    )
    contexto = paso_huella(contexto, mundo.bandeja)
    contexto = paso_reconocimiento(contexto, mundo.lector)
    contexto = paso_catalogo(contexto, mundo.catalogo, mundo.equivalencias)
    contexto = paso_validacion(contexto, CONFIG.listas)

    with pytest.raises(PersistenciaNoDisponible):
        paso_registro(contexto, mundo.bandeja, nuevo_id=mundo.nuevo_id)

    assert contexto.resultado is None
    assert "generador.generar" not in mundo.llamadas
    with pytest.raises(ValueError, match="fuera de orden"):
        paso_excel_errores(contexto, mundo.generador, CONFIG.listas, CONFIG.textos)


def test_f036_r40_si_la_base_falla_en_la_huella_no_se_lee_nada_mas():
    mundo = Mundo()
    mundo.bandeja = BandejaEnMemoria(
        mundo.llamadas, fallo_al_buscar=PersistenciaNoDisponible("sin base")
    )

    with pytest.raises(PersistenciaNoDisponible):
        mundo.importar(fichero(BUENA))

    assert mundo.llamadas == ["bandeja.importacion_completa_por_hash"]


def test_f036_r62_el_excel_de_errores_lleva_solo_las_filas_con_error_tal_como_llegaron():
    mundo = Mundo()
    otra_mala = fila(unidad=VILLA_2, descripcion=None, oficio="Fontanería")

    contexto = mundo.importar(fichero(MALA, BUENA, otra_mala))

    filas = _incidencias(contexto.excel_errores.contenido)
    assert [f[0] for f in filas] == ["viviendas bloque villa 2", VILLA_2]
    assert filas[0][2] == "Puerta que no cierra"
    assert filas[1][4] == "Fontanería"
    assert filas[0][CABECERA.index(COLUMNA_ERRORES)] == (
        f"Fila 2 del fichero subido · Unidad: {UNIDAD_FUERA_DE_LISTA}"
    )
    assert filas[1][CABECERA.index(COLUMNA_ERRORES)].startswith(
        f"Fila 4 del fichero subido · Descripción corta: {FALTA_DESCRIPCION} · Oficio: "
    )


def test_f036_r62_el_excel_de_errores_usa_el_mismo_catalogo_y_opciones():
    mundo = Mundo(decisiones=(mismo("0085", "0166"),))

    contexto = mundo.importar(fichero(BUENA, MALA, decisiones=mundo.decisiones))

    (argumentos,) = mundo.generador.argumentos
    assert argumentos["catalogo"] is contexto.catalogo
    assert argumentos["opciones_oficio"] is contexto.opciones_oficio
    assert argumentos["opciones_proveedor"] is contexto.opciones_proveedor
    assert argumentos["listas"] is CONFIG.listas
    assert argumentos["textos"] is CONFIG.textos
    assert argumentos["generada_at"] == AHORA
    assert (
        argumentos["importacion_origen"]
        == contexto.resultado.importacion.importacion_id
    )
    assert len(argumentos["filas"]) == 1


def test_f036_r65_el_excel_de_errores_se_llama_con_la_obra_y_la_hora_utc():
    mundo = Mundo()
    en_madrid = datetime(2026, 9, 30, 1, 30, tzinfo=timezone(timedelta(hours=2)))

    contexto = mundo.importar(fichero(MALA), ahora=en_madrid)

    assert (
        contexto.excel_errores.nombre == "incidencias_0677_errores_20260929-2330.xlsx"
    )
    assert isinstance(contexto.excel_errores, ExcelDeErrores)


def test_f036_r65_el_nombre_del_excel_de_errores():
    assert (
        nombre_del_excel_de_errores("0677", AHORA)
        == "incidencias_0677_errores_20260930-0815.xlsx"
    )
    assert (
        nombre_del_excel_de_errores("A-1", datetime(2026, 1, 2, 3, 4, tzinfo=UTC))
        == "incidencias_A-1_errores_20260102-0304.xlsx"
    )


def test_f036_r63_la_fila_del_excel_de_errores_lleva_los_valores_tal_como_llegaron():
    celdas = {
        "Unidad": CeldaLeida("villa 1", False, False, "villa 1"),
        "Descripción corta": CeldaLeida("=A1", True, False, "=A1"),
        "Detalle": CeldaLeida(12.0, False, False, "12"),
        "Urgencia": CeldaLeida(True, False, True, "VERDADERO"),
        COLUMNA_ERRORES: CeldaLeida("lo de antes", False, False, "lo de antes"),
    }
    errores = (
        ErrorDeFila(7, "Unidad", "no está"),
        ErrorDeFila(7, "Descripción corta", "fórmula"),
        ErrorDeFila(7, "Urgencia", "fecha"),
    )

    resultado = fila_del_excel_de_errores(FilaConError(FilaLeida(7, celdas), errores))

    assert dict(resultado.valores) == {
        "Unidad": "villa 1",
        "Ubicación": None,
        "Descripción corta": "=A1",
        "Detalle": "12",
        "Oficio": None,
        "Proveedor": None,
        "Urgencia": "VERDADERO",
        "Listado": None,
    }
    assert dict(resultado.errores) == {
        "Unidad": "no está",
        "Descripción corta": "fórmula",
        "Urgencia": "fecha",
    }
    assert resultado.texto_errores == (
        "Fila 7 del fichero subido · Unidad: no está · Descripción corta: fórmula"
        " · Urgencia: fecha"
    )


def test_f036_r64_dos_errores_en_la_misma_columna_se_juntan():
    errores = (ErrorDeFila(3, "Unidad", "uno"), ErrorDeFila(3, "Unidad", "dos"))

    resultado = fila_del_excel_de_errores(FilaConError(FilaLeida(3, {}), errores))

    assert dict(resultado.errores) == {"Unidad": "uno · dos"}
    assert (
        resultado.texto_errores
        == "Fila 3 del fichero subido · Unidad: uno · Unidad: dos"
    )


def test_f036_r70_con_todas_las_filas_mal_consta_parcial_con_cero_nuevas():
    mundo = Mundo()
    otra_mala = fila(unidad="Villa 9", descripcion="Otra cosa")

    contexto = mundo.importar(fichero(MALA, otra_mala))

    ((registro, grupos),) = mundo.bandeja.registradas
    assert grupos == ()
    assert registro.filas_leidas == 2
    assert registro.filas_con_error == 2
    assert contexto.resultado.estado is EstadoImportacion.PARCIAL
    assert contexto.resultado.nuevas == 0
    assert len(_incidencias(contexto.excel_errores.contenido)) == 2


def test_f036_r69_sin_filas_con_error_no_hay_excel_y_consta_completa():
    mundo = Mundo()

    contexto = mundo.importar(fichero(BUENA))

    assert contexto.con_error == ()
    assert contexto.excel_errores is None
    assert contexto.resultado.estado is EstadoImportacion.COMPLETA
    assert mundo.generador.argumentos == []


def test_f036_t17_una_plantilla_sin_filas_consta_completa_con_cero_leidas():
    mundo = Mundo()

    contexto = mundo.importar(fichero())

    ((registro, grupos),) = mundo.bandeja.registradas
    assert (registro.filas_leidas, registro.filas_con_error, grupos) == (0, 0, ())
    assert contexto.resultado.estado is EstadoImportacion.COMPLETA
    assert contexto.excel_errores is None


def test_f036_r67_el_excel_de_errores_corregido_no_duplica_lo_que_ya_entro():
    """Se corrige la fila mala en el Excel de errores y se sube: entra solo ella."""
    mundo = Mundo()
    primera = mundo.importar(fichero(BUENA, MALA))
    corregida = fila(unidad=VILLA_2, descripcion="Puerta que no cierra")

    segunda = mundo.importar(fichero(corregida, BUENA))

    assert [(f.fila, f.estado) for f in segunda.resultado.filas] == [
        (2, EstadoFilaImportada.NUEVA),
        (3, EstadoFilaImportada.YA_EN_BANDEJA),
    ]
    assert (
        segunda.resultado.filas[1].existente_id
        == primera.resultado.filas[0].incidencia_id
    )
    assert segunda.resultado.estado is EstadoImportacion.COMPLETA
    assert segunda.excel_errores is None


def test_f036_r67_el_excel_de_errores_generado_se_puede_volver_a_subir():
    """Ida y vuelta: el Excel de errores, tal cual, se reconoce y vuelve a fallar igual."""
    mundo = Mundo()
    primera = mundo.importar(fichero(BUENA, MALA))

    segunda = mundo.importar(primera.excel_errores.contenido)

    assert segunda.obra_codigo == "0677"
    assert segunda.validas == ()
    assert [e.problema for f in segunda.con_error for e in f.errores] == [
        UNIDAD_FUERA_DE_LISTA
    ]


def test_f036_r68_nada_del_excel_de_errores_ni_de_las_filas_malas_llega_a_la_bandeja():
    mundo = Mundo()

    mundo.importar(fichero(BUENA, MALA))

    ((registro, grupos),) = mundo.bandeja.registradas
    assert not any(isinstance(v, bytes) for v in vars(registro).values())
    textos = repr([v.descripcion for g in grupos for v in g.filas])
    assert "Puerta que no cierra" not in textos


# --------------------------------------------------------------------------
# R47 · los logs
# --------------------------------------------------------------------------


def test_f036_r47_la_importacion_no_registra_textos_nombres_fichero_ni_oid(caplog):
    caplog.set_level(logging.DEBUG)
    mundo = Mundo(decisiones=(mismo("0085", "0166"),))
    con_proveedor = fila(
        unidad=VILLA_1,
        descripcion="Mampara rota",
        proveedor="Carpintería de madera · Juan Ejemplo Ejemplo",
    )

    mundo.importar(fichero(BUENA, MALA, con_proveedor, decisiones=mundo.decisiones))

    registrado = caplog.text
    assert "0677" in registrado
    for prohibido in (
        NOMBRE_FICHERO,
        "Fulanita",
        OID,
        DESCRIPCION,
        "Puerta que no cierra",
        "Viviendas Bloque",
        "villa",
        "Ejemplo",
        "P001",
        "P002",
        "P003",
        OBRA_REF,
    ):
        assert prohibido not in registrado


def test_f036_r47_el_contexto_no_ensena_bytes_ni_quien_ni_que_fichero():
    mundo = Mundo()

    contexto = mundo.importar(fichero(BUENA, MALA))

    texto = repr(contexto)
    assert NOMBRE_FICHERO not in texto
    assert OID not in texto
    assert DESCRIPCION not in texto
    assert "Viviendas Bloque" not in texto
    assert "PK" not in texto
    assert "0677" in texto
    assert "incidencias_0677_errores_" in texto


# --------------------------------------------------------------------------
# §7.2 · la plantilla
# --------------------------------------------------------------------------


def _plantilla(mundo: Mundo, codigo: object = "0677", ahora: datetime = AHORA):
    return generar_plantilla(
        codigo,
        catalogo_obra=mundo.catalogo,
        equivalencias=mundo.equivalencias,
        generador=mundo.generador,
        listas=CONFIG.listas,
        textos=CONFIG.textos,
        ahora=ahora,
    )


def test_f036_r1_la_plantilla_lee_el_catalogo_los_grupos_y_genera():
    mundo = Mundo()

    nombre, contenido = _plantilla(mundo)

    assert mundo.llamadas == [
        "catalogo.leer_unidades",
        "catalogo.leer_oficios",
        "equivalencias.ultimas_decisiones",
        "generador.generar",
    ]
    assert nombre == "plantilla_incidencias_0677_20260930.xlsx"
    assert contenido.startswith(b"PK\x03\x04")
    (argumentos,) = mundo.generador.argumentos
    assert argumentos["catalogo"] == catalogo()
    assert argumentos["filas"] == ()
    assert argumentos["importacion_origen"] is None
    assert argumentos["generada_at"] == AHORA
    assert argumentos["listas"] is CONFIG.listas
    assert argumentos["textos"] is CONFIG.textos


def test_f036_r92_la_plantilla_ofrece_un_oficio_por_grupo_confirmado():
    mundo = Mundo(decisiones=(mismo("0085", "0166"),))

    _, contenido = _plantilla(mundo)

    (argumentos,) = mundo.generador.argumentos
    assert [o.etiqueta for o in argumentos["opciones_oficio"]] == [
        "Carpintería de madera",
        "Mamparas",
        "Albañilería",
    ]
    assert [p.etiqueta for p in argumentos["opciones_proveedor"]][-1] == (
        "Mamparas · Mamparas Ejemplo S.A."
    )
    # La plantilla generada se importa con esas mismas opciones.
    importada = Mundo(decisiones=mundo.decisiones)
    fila_ = fila(unidad=VILLA_1, descripcion="Mampara rota", oficio="Mamparas")
    assert importada.importar(contenido).obra_codigo == "0677"
    assert importada.importar(fichero(fila_, decisiones=mundo.decisiones)).validas


def test_f036_r1_el_nombre_de_la_plantilla_lleva_la_fecha_en_utc():
    en_madrid = datetime(2026, 9, 30, 1, 30, tzinfo=timezone(timedelta(hours=2)))

    nombre, _ = _plantilla(Mundo(), ahora=en_madrid)

    assert nombre == "plantilla_incidencias_0677_20260929.xlsx"
    assert nombre_de_la_plantilla("B.7", datetime(2027, 1, 5, 23, 59, tzinfo=UTC)) == (
        "plantilla_incidencias_B.7_20270105.xlsx"
    )


def test_f036_r9_la_plantilla_normaliza_el_codigo_de_obra():
    mundo = Mundo()

    nombre, _ = _plantilla(mundo, codigo=" 06 77 ")

    assert mundo.catalogo.codigos_pedidos == ["0677"]
    assert nombre.startswith("plantilla_incidencias_0677_")


@pytest.mark.parametrize("codigo", [None, "", "   ", "06/77", "x" * 25])
def test_f036_r9_un_codigo_inadmisible_no_llama_a_sigrid_ni_a_la_base(codigo):
    mundo = Mundo()

    with pytest.raises(CodigoDeObraInvalido):
        _plantilla(mundo, codigo=codigo)

    assert mundo.llamadas == []


@pytest.mark.parametrize(
    ("donde", "fallo"),
    [
        ("catalogo", ObraSinUnidades("sin unidades")),
        ("catalogo", CatalogoNoDisponible("sin pasarela")),
        ("equivalencias", PersistenciaNoDisponible("sin base")),
    ],
)
def test_f036_r10_r11_si_algo_falla_no_hay_plantilla(donde, fallo):
    mundo = Mundo()
    if donde == "catalogo":
        mundo.catalogo = CatalogoEnMemoria(mundo.llamadas, fallo=fallo)
    else:
        mundo.equivalencias = EquivalenciasEnMemoria(mundo.llamadas, fallo=fallo)

    with pytest.raises(type(fallo)):
        _plantilla(mundo)

    assert "generador.generar" not in mundo.llamadas


def test_f036_r12_la_plantilla_de_una_obra_sin_oficios_se_genera_igual():
    mundo = Mundo()
    mundo.catalogo = CatalogoEnMemoria(mundo.llamadas, oficios=())

    _nombre, contenido = _plantilla(mundo)

    (argumentos,) = mundo.generador.argumentos
    assert argumentos["opciones_oficio"] == ()
    assert argumentos["opciones_proveedor"] == ()
    assert contenido.startswith(b"PK")


def test_f036_r47_la_plantilla_no_registra_nombres(caplog):
    caplog.set_level(logging.DEBUG)

    _plantilla(Mundo())

    assert "0677" in caplog.text
    for prohibido in ("Viviendas Bloque", "Ejemplo", "P001", OBRA_REF):
        assert prohibido not in caplog.text


# --------------------------------------------------------------------------
# arquitectura: la aplicación no conoce adaptadores
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "modulo",
    ["plantilla.py", "contexto_importacion.py", "paso_importacion.py"],
)
def test_f036_t17_la_aplicacion_solo_importa_dominio_y_aplicacion(modulo):
    ruta = SERVICIO / "application" / "pipelines" / modulo
    arbol = ast.parse(ruta.read_text(encoding="utf-8"))
    raices = set()
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.ImportFrom) and nodo.module:
            raices.add(nodo.module.split(".")[0])
        elif isinstance(nodo, ast.Import):
            raices.update(a.name.split(".")[0] for a in nodo.names)
    assert raices <= {
        "__future__",
        "application",
        "domain",
        "collections",
        "dataclasses",
        "datetime",
        "hashlib",
        "logging",
        "typing",
        "uuid",
    }


def test_f036_t17_los_modulos_nombran_su_ruta_en_la_primera_linea():
    for modulo in (plantilla, paso_importacion):
        primera = Path(modulo.__file__).read_text(encoding="utf-8").splitlines()[0]
        assert primera == (
            "# services/postventa-api/application/pipelines/"
            + Path(modulo.__file__).name
        )


def test_f036_t17_el_catalogo_de_filas_de_oficio_de_prueba_es_el_de_la_plantilla():
    """Control de los dobles: el catálogo en memoria da el de `utiles_plantilla`."""
    assert {f.oficio_codigo for f in filas_de_oficios()} == {
        o.codigo for o in catalogo().oficios
    }
    assert isinstance(filas_de_oficios()[0], FilaOficioCatalogo)
    assert OficioObra("0046", "Carpintería de madera") in catalogo().oficios


# --------------------------------------------------------------------------
# lo que destapó la mutación: cada guarda por separado, `frozen` y `repr`
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "campos",
    [
        {"hash": "h", "libro": "libro"},
        {"hash": "h", "obra_codigo": "0677"},
    ],
    ids=["sin_obra", "sin_libro"],
)
def test_f036_t17_el_catalogo_exige_libro_y_obra_a_la_vez(campos):
    llamadas: list[str] = []
    if campos.get("libro") == "libro":
        campos = {**campos, "libro": _libro()}

    with pytest.raises(ValueError, match="fuera de orden"):
        paso_catalogo(
            _contexto(**campos),
            CatalogoEnMemoria(llamadas),
            EquivalenciasEnMemoria(llamadas),
        )
    assert llamadas == []


def test_f036_t17_validar_sin_libro_es_un_paso_fuera_de_orden():
    with pytest.raises(ValueError, match="fuera de orden"):
        paso_validacion(
            _contexto(hash="h", obra_codigo="0677", catalogo=catalogo()), CONFIG.listas
        )


@pytest.mark.parametrize(
    "falta", ["validas", "con_error", "libro", "obra_codigo", "hash"]
)
def test_f036_t17_registrar_exige_cada_cosa_de_los_pasos_anteriores(falta):
    llamadas: list[str] = []
    campos = {
        "hash": "h",
        "libro": _libro(),
        "obra_codigo": "0677",
        "catalogo": catalogo(),
        "validas": (),
        "con_error": (),
    }
    campos[falta] = None

    with pytest.raises(ValueError, match="fuera de orden"):
        paso_registro(_contexto(**campos), BandejaEnMemoria(llamadas))
    assert llamadas == []


def test_f036_t17_el_excel_de_errores_exige_tambien_el_catalogo():
    llamadas: list[str] = []
    mundo = Mundo()
    hecho = mundo.importar(fichero(MALA))
    contexto = _contexto(
        hash="h",
        obra_codigo="0677",
        validas=(),
        con_error=hecho.con_error,
        resultado=hecho.resultado,
    )

    with pytest.raises(ValueError, match="fuera de orden"):
        paso_excel_errores(
            contexto, GeneradorQueAnota(llamadas), CONFIG.listas, CONFIG.textos
        )
    assert llamadas == []


def test_f036_r47_el_repr_del_contexto_solo_lleva_codigos_hora_y_nombre_del_excel():
    """Lo demás lleva texto de la propiedad, nombres o bytes: fuera del `repr`."""
    mundo = Mundo(decisiones=(mismo("0085", "0166"),))
    contexto = mundo.importar(fichero(BUENA, MALA, decisiones=mundo.decisiones))

    visibles = {c.name for c in dataclasses.fields(contexto) if c.repr}

    assert visibles == {"ahora", "hash", "obra_codigo", "excel_errores"}
    texto = repr(contexto)
    for campo in dataclasses.fields(contexto):
        assert (f"{campo.name}=" in texto) == (campo.name in visibles)
    assert "Ejemplo" not in texto
    assert "Mamparas" not in texto


def test_f036_t17_el_excel_de_errores_y_las_opciones_no_se_pueden_cambiar():
    excel = ExcelDeErrores("x.xlsx", b"PK")
    opciones = opciones_de_la_obra(catalogo(), EquivalenciasEnMemoria([]))

    with pytest.raises(dataclasses.FrozenInstanceError):
        excel.nombre = "otro.xlsx"  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        opciones.oficios = ()  # type: ignore[misc]
    assert "PK" not in repr(excel)
