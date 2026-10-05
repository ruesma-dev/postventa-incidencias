# services/postventa-api/application/pipelines/paso_importacion.py
"""Los seis pasos de la importación de un Excel de incidencias (F-036).

`specs/F-036-importar-excel/design.md` §7.3. Cada paso recibe el
`ContextoImportacion`, lo enriquece y lo devuelve; la composición vive en el
punto de entrada (`interface_adapters/api/importar.py`), no aquí.

1. **`paso_huella`** — `sha256` de los bytes; si ya constan en una
   importación **completa**, el contexto queda `ya_importado` con el resumen
   de entonces y los demás pasos no hacen nada (R39: sin Sigrid ni escritura).
2. **`paso_reconocimiento`** — el lector y `reconocer_plantilla` (R16–R20). Un
   fichero que no es la plantilla se rechaza **entero** aquí: ni Sigrid, ni
   base, ni Excel de errores (R21).
3. **`paso_catalogo`** — el catálogo de la obra de los metadatos, leído de
   Sigrid en este momento, y los grupos vigentes y opciones de la obra (§7.2).
4. **`paso_validacion`** — `validar_filas`: válidas y con error (R33).
5. **`paso_registro`** — `agrupar_por_clave` sobre las válidas y
   `BandejaPort.registrar`, también con cero válidas (R70).
6. **`paso_excel_errores`** — si hay filas con error, el **mismo** generador
   de la plantilla con el mismo catálogo y opciones (R62–R65). Va **después**
   del registro: si la base falla, no se entrega un Excel de errores de una
   importación que no consta (R40).

## Un paso fuera de orden revienta

Cada paso exige lo que deja el anterior y, si falta, levanta `ValueError`
(«paso fuera de orden») **antes** de llamar a ningún puerto. Es un error de
programación, no de la petición: así nadie puede, por ejemplo, generar un
Excel de errores sin haber registrado la importación.

## Logs (R47)

Código de obra, recuentos e `importacion_id`. Nunca el nombre del fichero, el
`oid`, los textos de las filas, los nombres de unidad o de proveedor, ni el
`sha256` (identifica el fichero de una persona).
"""

from __future__ import annotations

import hashlib
import logging
import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from uuid import UUID

from domain.models.importacion import (
    FilaConError,
    agrupar_por_clave,
    reconocer_plantilla,
    validar_filas,
)
from domain.models.plantilla_incidencias import (
    CABECERA,
    COLUMNA_ERRORES,
    ListasCerradas,
    TextosPlantilla,
)
from domain.ports.bandeja import BandejaPort, RegistroImportacion
from domain.ports.catalogo_obra import CatalogoObraPort
from domain.ports.equivalencias import EquivalenciasPort
from domain.ports.hoja_calculo import (
    FilaPlantilla,
    GeneradorPlantillaPort,
    LectorPlantillaPort,
)

from application.pipelines.catalogo_obra import leer_catalogo
from application.pipelines.contexto_importacion import (
    ContextoImportacion,
    ExcelDeErrores,
)
from application.pipelines.plantilla import opciones_de_la_obra

__all__ = [
    "fila_del_excel_de_errores",
    "nombre_del_excel_de_errores",
    "paso_catalogo",
    "paso_excel_errores",
    "paso_huella",
    "paso_reconocimiento",
    "paso_registro",
    "paso_validacion",
]

log = logging.getLogger(__name__)

#: Las columnas de datos de la plantilla: todas menos la de errores.
COLUMNAS_DE_DATOS: tuple[str, ...] = tuple(c for c in CABECERA if c != COLUMNA_ERRORES)

#: Entre las partes del texto de la columna de errores (R63).
SEPARADOR_ERRORES = " · "


def _fuera_de_orden(paso: str, falta: str) -> ValueError:
    return ValueError(f"paso fuera de orden: {paso} sin {falta}")


# --------------------------------------------------------------------------
# el Excel de errores, puro
# --------------------------------------------------------------------------


def nombre_del_excel_de_errores(obra_codigo: str, instante: datetime) -> str:
    """`incidencias_<obra>_errores_<AAAAMMDD-HHMM>.xlsx`, en UTC (R65)."""
    return (
        f"incidencias_{obra_codigo}_errores_{instante.astimezone(UTC):%Y%m%d-%H%M}.xlsx"
    )


def fila_del_excel_de_errores(fila: FilaConError) -> FilaPlantilla:
    """Una fila con error, como se reescribe en el Excel de errores (R63, R64).

    Los valores van **tal como llegaron** (`texto_original`: una fórmula, como
    su texto); la columna de errores del fichero subido no se copia, se
    rellena de nuevo. Cada columna con error se marca con su problema y la
    columna de errores dice «Fila N del fichero subido · Columna: problema · …».
    """
    celdas = fila.fila.celdas
    valores = {
        columna: celdas[columna].texto_original if columna in celdas else None
        for columna in COLUMNAS_DE_DATOS
    }
    marcas: dict[str, list[str]] = {}
    for error in fila.errores:
        marcas.setdefault(error.columna, []).append(error.problema)
    texto = SEPARADOR_ERRORES.join(
        [f"Fila {fila.fila.numero} del fichero subido"]
        + [f"{error.columna}: {error.problema}" for error in fila.errores]
    )
    return FilaPlantilla(
        valores=valores,
        errores={c: SEPARADOR_ERRORES.join(p) for c, p in marcas.items()},
        texto_errores=texto,
    )


# --------------------------------------------------------------------------
# los seis pasos
# --------------------------------------------------------------------------


def paso_huella(
    contexto: ContextoImportacion, bandeja: BandejaPort
) -> ContextoImportacion:
    """Paso 1: el `sha256` y el atajo de R39, solo con una importación completa."""
    contexto.hash = hashlib.sha256(contexto.contenido).hexdigest()
    previa = bandeja.importacion_completa_por_hash(hash_fichero=contexto.hash)
    if previa is not None:
        contexto.resultado = previa
        contexto.obra_codigo = previa.importacion.obra_codigo
        log.info(
            "F-036 importación ya hecha, no se escribe nada: importacion=%s obra=%s",
            previa.importacion.importacion_id,
            previa.importacion.obra_codigo,
        )
    return contexto


def paso_reconocimiento(
    contexto: ContextoImportacion, lector: LectorPlantillaPort
) -> ContextoImportacion:
    """Paso 2: leer el libro y reconocer la plantilla (R16–R21)."""
    if contexto.ya_importado:
        return contexto
    if contexto.hash is None:
        raise _fuera_de_orden("reconocimiento", "huella")
    libro = lector.leer(contenido=contexto.contenido)
    contexto.obra_codigo = reconocer_plantilla(libro)
    contexto.libro = libro
    log.info(
        "F-036 plantilla reconocida: obra=%s filas=%d",
        contexto.obra_codigo,
        len(libro.filas),
    )
    return contexto


def paso_catalogo(
    contexto: ContextoImportacion,
    catalogo_obra: CatalogoObraPort,
    equivalencias: EquivalenciasPort,
) -> ContextoImportacion:
    """Paso 3: el catálogo de la obra de los metadatos y sus opciones (§7.1, §7.2)."""
    if contexto.ya_importado:
        return contexto
    if contexto.libro is None or contexto.obra_codigo is None:
        raise _fuera_de_orden("catálogo", "reconocimiento")
    catalogo = leer_catalogo(catalogo_obra, contexto.obra_codigo)
    opciones = opciones_de_la_obra(catalogo, equivalencias)
    contexto.catalogo = catalogo
    contexto.grupos_oficio = opciones.grupos_oficio
    contexto.grupos_proveedor = opciones.grupos_proveedor
    contexto.opciones_oficio = opciones.oficios
    contexto.opciones_proveedor = opciones.proveedores
    return contexto


def paso_validacion(
    contexto: ContextoImportacion, listas: ListasCerradas
) -> ContextoImportacion:
    """Paso 4: válidas y con error, sin que una fila mala pare a las demás (R33)."""
    if contexto.ya_importado:
        return contexto
    if contexto.libro is None or contexto.catalogo is None:
        raise _fuera_de_orden("validación", "catálogo")
    contexto.validas, contexto.con_error = validar_filas(
        contexto.libro.filas,
        catalogo=contexto.catalogo,
        opciones_oficio=contexto.opciones_oficio,
        opciones_proveedor=contexto.opciones_proveedor,
        listas=listas,
    )
    log.info(
        "F-036 filas validadas: obra=%s validas=%d con_error=%d",
        contexto.obra_codigo,
        len(contexto.validas),
        len(contexto.con_error),
    )
    return contexto


def paso_registro(
    contexto: ContextoImportacion,
    bandeja: BandejaPort,
    *,
    nuevo_id: Callable[[], UUID] = uuid.uuid4,
) -> ContextoImportacion:
    """Paso 5: la importación y sus filas válidas, en una transacción (R37–R42, R70).

    Con cero válidas se registra igual: la importación consta, parcial y con
    cero nuevas. Si la base falla, el error sube y el contexto queda sin
    `resultado`: no hay Excel de errores de una importación que no consta.
    """
    if contexto.ya_importado:
        return contexto
    if (
        contexto.validas is None
        or contexto.con_error is None
        or contexto.libro is None
        or contexto.obra_codigo is None
        or contexto.hash is None
    ):
        raise _fuera_de_orden("registro", "validación")
    contexto.agrupadas = agrupar_por_clave(
        contexto.validas, obra_codigo=contexto.obra_codigo
    )
    registro = RegistroImportacion(
        importacion_id=nuevo_id(),
        hash_fichero=contexto.hash,
        nombre_fichero=contexto.nombre_fichero,
        obra_codigo=contexto.obra_codigo,
        plantilla_version=contexto.libro.version,  # type: ignore[arg-type]
        importado_por=contexto.usuario_oid,
        importado_at_utc=contexto.ahora,
        filas_leidas=len(contexto.validas) + len(contexto.con_error),
        filas_con_error=len(contexto.con_error),
    )
    contexto.resultado = bandeja.registrar(
        importacion=registro, grupos=contexto.agrupadas
    )
    return contexto


def paso_excel_errores(
    contexto: ContextoImportacion,
    generador: GeneradorPlantillaPort,
    listas: ListasCerradas,
    textos: TextosPlantilla,
) -> ContextoImportacion:
    """Paso 6: el Excel de errores, solo si hay filas con error (R62–R65, R69).

    No se guarda en ningún sitio (R68): se queda en el contexto y viaja en la
    respuesta.
    """
    if contexto.ya_importado:
        return contexto
    if contexto.con_error is None:
        raise _fuera_de_orden("Excel de errores", "validación")
    if not contexto.con_error:
        return contexto
    if contexto.resultado is None or contexto.catalogo is None:
        raise _fuera_de_orden("Excel de errores", "registro")
    importacion_id = contexto.resultado.importacion.importacion_id
    contenido = generador.generar(
        catalogo=contexto.catalogo,
        opciones_oficio=contexto.opciones_oficio,
        opciones_proveedor=contexto.opciones_proveedor,
        listas=listas,
        textos=textos,
        generada_at=contexto.ahora,
        filas=tuple(fila_del_excel_de_errores(f) for f in contexto.con_error),
        importacion_origen=importacion_id,
    )
    contexto.excel_errores = ExcelDeErrores(
        nombre=nombre_del_excel_de_errores(
            contexto.catalogo.obra_codigo, contexto.ahora
        ),
        contenido=contenido,
    )
    log.info(
        "F-036 Excel de errores generado: importacion=%s obra=%s filas=%d bytes=%d",
        importacion_id,
        contexto.catalogo.obra_codigo,
        len(contexto.con_error),
        len(contenido),
    )
    return contexto
