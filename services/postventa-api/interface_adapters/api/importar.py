# services/postventa-api/interface_adapters/api/importar.py
"""Handler de `POST /api/importaciones`: un Excel de incidencias a la bandeja (F-036).

`specs/F-036-importar-excel/design.md` §7.3 y §8. Aquí se **compone la
importación** —los seis pasos de `application/pipelines/paso_importacion.py`,
en su orden, con sus adaptadores— y se serializa el resultado (R43), como
manda `docs/CONVENTIONS.md`: la composición vive en el punto de entrada y
nunca dentro de un paso. Los puertos inyectables son la costura de test.

## Lo que se mira antes de abrir nada

1. **`usuario_oid`** (R22): un texto no vacío de hasta 128 caracteres; si no,
   `PeticionDeImportacionInvalida` (→ 400) sin mirar el fichero.
2. **Exactamente un fichero** (R14): ninguno o dos son 400.
3. **El tamaño** (R15): más de 2 MiB es `FicheroDemasiadoGrande` (→ 413) sin
   abrirlo y sin construir ningún adaptador.

## Qué se construye y cuándo

La bandeja, siempre (el paso 1 busca los bytes en ella). El lector, el
**aislado** (`LectorPlantillaAislado`, R118): la biblioteca de Excel lee el
fichero en un proceso hijo con tope de tiempo y de memoria. El catálogo de Sigrid
y las decisiones de equivalencia, **solo** si el fichero no estaba ya
importado y se ha reconocido como la plantilla: un fichero que no lo es se
rechaza sin llegar a Sigrid (R21), y el atajo de R39 no lee Sigrid.

## La respuesta (R43)

`importacion_id`, `obra`, `ya_importado`, `estado`, `resumen`, `filas` (las
válidas con su estado y avisos y las que tienen error, en orden de fila),
`errores` —hasta 200, R33— con `total_errores`, y `excel_errores {nombre,
contenido_b64}` **solo** si hay filas con error (R65, R69). El Excel de
errores no se guarda en ningún sitio (R68).

Escribe en el esquema propio y nada en Sigrid (R46); no depende de ninguna
ventana de escritura del servicio.

## Datos personales (R47)

El nombre del fichero y el `oid` se guardan (R42) pero no salen de aquí a
ningún log; el nombre se recorta a 255 caracteres. Los mensajes de rechazo no
repiten el `oid`.
"""

from __future__ import annotations

import base64
import uuid
from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from application.pipelines.contexto_importacion import ContextoImportacion
from application.pipelines.paso_importacion import (
    paso_catalogo,
    paso_excel_errores,
    paso_huella,
    paso_reconocimiento,
    paso_registro,
    paso_validacion,
)
from config.settings import obtener_ajustes
from domain.models.errores import (
    FicheroDemasiadoGrande,
    PeticionDeImportacionInvalida,
)
from domain.models.importacion import EstadoFilaImportada
from domain.models.plantilla_incidencias import MAX_BYTES_FICHERO
from domain.ports.bandeja import BandejaPort
from domain.ports.catalogo_obra import CatalogoObraPort
from domain.ports.equivalencias import EquivalenciasPort
from domain.ports.hoja_calculo import GeneradorPlantillaPort, LectorPlantillaPort
from infrastructure.documentos.excel_openpyxl import GeneradorPlantillaOpenpyxl
from infrastructure.documentos.lector_aislado import LectorPlantillaAislado
from infrastructure.documentos.plantilla_yaml import ConfiguracionPlantilla
from infrastructure.persistencia.fabrica import (
    construir_bandeja,
    construir_equivalencias,
)
from infrastructure.sigrid.fabrica import construir_catalogo_obra

from interface_adapters.api.plantilla import configuracion_de_la_plantilla

__all__ = [
    "MAX_ERRORES_EN_RESPUESTA",
    "MAX_NOMBRE_FICHERO",
    "MAX_USUARIO_OID",
    "importar_excel",
    "serializar_importacion",
]

#: Errores que viajan en la lista de la respuesta; el total va aparte (R33).
MAX_ERRORES_EN_RESPUESTA = 200

#: El nombre del fichero se guarda recortado (§8).
MAX_NOMBRE_FICHERO = 255

#: El `oid` de Entra, como mucho (R22).
MAX_USUARIO_OID = 128


def _usuario_oid(crudo: Any) -> str:
    """El `oid` de quien sube, recortado, o 400 sin repetirlo (R22, R47)."""
    oid = crudo.strip() if isinstance(crudo, str) else ""
    if not oid or len(oid) > MAX_USUARIO_OID:
        raise PeticionDeImportacionInvalida(
            f"falta 'usuario_oid' o no es un texto de 1 a {MAX_USUARIO_OID} "
            "caracteres: hace falta saber quién importa"
        )
    return oid


def _un_fichero(ficheros: Sequence[tuple[str, bytes]]) -> tuple[str, bytes]:
    """El único fichero de la petición (R14)."""
    if len(ficheros) != 1:
        raise PeticionDeImportacionInvalida(
            f"la petición tiene que traer exactamente un fichero y trae {len(ficheros)}"
        )
    nombre, contenido = ficheros[0]
    if len(contenido) > MAX_BYTES_FICHERO:
        raise FicheroDemasiadoGrande(
            f"El fichero pasa de {MAX_BYTES_FICHERO // (1024 * 1024)} MiB: no se ha "
            "abierto. Pártelo en varios ficheros."
        )
    return nombre[:MAX_NOMBRE_FICHERO], contenido


def importar_excel(
    ficheros: Sequence[tuple[str, bytes]],
    usuario_oid: Any,
    *,
    bandeja: BandejaPort | None = None,
    lector: LectorPlantillaPort | None = None,
    catalogo_obra: CatalogoObraPort | None = None,
    equivalencias: EquivalenciasPort | None = None,
    generador: GeneradorPlantillaPort | None = None,
    configuracion: ConfiguracionPlantilla | None = None,
    ahora: datetime | None = None,
    nuevo_id: Callable[[], UUID] = uuid.uuid4,
) -> dict[str, Any]:
    """Importa el fichero y devuelve la respuesta de R43.

    Levanta, sin traducir: `PeticionDeImportacionInvalida` y
    `FicheroNoEsPlantilla` (→ 400), `FicheroDemasiadoGrande` (→ 413),
    `ObraSinUnidades`, `ObraAmbigua` y `CatalogoSinVerificar` (→ 409), los
    fallos de Sigrid y de la base (→ 503), y los de la lectura aislada,
    `LectorSinAislamiento` y `LecturaOcupada` (→ 503, R119, R120).
    """
    oid = _usuario_oid(usuario_oid)
    nombre, contenido = _un_fichero(ficheros)

    contexto = ContextoImportacion(
        contenido=contenido,
        nombre_fichero=nombre,
        usuario_oid=oid,
        ahora=ahora if ahora is not None else datetime.now(UTC),
    )
    if bandeja is None:
        bandeja = construir_bandeja(obtener_ajustes())
    contexto = paso_huella(contexto, bandeja)
    if lector is None:
        # El fichero subido lo lee la biblioteca en un proceso hijo (R118).
        lector = LectorPlantillaAislado(entorno=obtener_ajustes().entorno)
    contexto = paso_reconocimiento(contexto, lector)
    if not contexto.ya_importado:
        if catalogo_obra is None:
            catalogo_obra = construir_catalogo_obra(obtener_ajustes())
        if equivalencias is None:
            equivalencias = construir_equivalencias(obtener_ajustes())
        config = (
            configuracion
            if configuracion is not None
            else configuracion_de_la_plantilla()
        )
        contexto = paso_catalogo(contexto, catalogo_obra, equivalencias)
        contexto = paso_validacion(contexto, config.listas)
        contexto = paso_registro(contexto, bandeja, nuevo_id=nuevo_id)
        contexto = paso_excel_errores(
            contexto,
            generador if generador is not None else GeneradorPlantillaOpenpyxl(),
            config.listas,
            config.textos,
        )
    return serializar_importacion(contexto)


def serializar_importacion(contexto: ContextoImportacion) -> dict[str, Any]:
    """La respuesta 200 de R43, a partir del contexto ya registrado.

    Las filas válidas llevan lo que dijo la bandeja (`FilaImportada`) y sus
    avisos (R34); las que tienen error, `con_error` y ningún identificador. Las
    dos claves `duplicada_de_fila` y `existente_id` van siempre, a `null` si no
    aplican.
    """
    resultado = contexto.resultado
    assert resultado is not None, "no se serializa una importación sin registrar"
    con_error = contexto.con_error or ()
    avisos = {v.fila: list(v.avisos) for v in contexto.validas or ()}
    filas = [
        {
            "fila": f.fila,
            "estado": f.estado.value,
            "incidencia_id": _texto(f.incidencia_id),
            "duplicada_de_fila": f.duplicada_de_fila,
            "existente_id": _texto(f.existente_id),
            "avisos": avisos.get(f.fila, []),
        }
        for f in resultado.filas
    ] + [
        {
            "fila": f.fila.numero,
            "estado": EstadoFilaImportada.CON_ERROR.value,
            "incidencia_id": None,
            "duplicada_de_fila": None,
            "existente_id": None,
            "avisos": [],
        }
        for f in con_error
    ]
    errores = [
        {"fila": e.fila, "columna": e.columna, "problema": e.problema}
        for f in con_error
        for e in f.errores
    ]
    cuerpo: dict[str, Any] = {
        "importacion_id": str(resultado.importacion.importacion_id),
        "obra": resultado.importacion.obra_codigo,
        "ya_importado": resultado.ya_importado,
        "estado": resultado.estado.value,
        "resumen": {
            "leidas": resultado.importacion.filas_leidas,
            "nuevas": resultado.nuevas,
            "duplicadas_en_fichero": resultado.duplicadas_en_fichero,
            "ya_en_bandeja": resultado.ya_en_bandeja,
            "con_error": resultado.con_error,
        },
        "filas": sorted(filas, key=lambda f: f["fila"]),
        "errores": errores[:MAX_ERRORES_EN_RESPUESTA],
        "total_errores": len(errores),
    }
    if contexto.excel_errores is not None:
        cuerpo["excel_errores"] = {
            "nombre": contexto.excel_errores.nombre,
            "contenido_b64": base64.b64encode(contexto.excel_errores.contenido).decode(
                "ascii"
            ),
        }
    return cuerpo


def _texto(valor: UUID | None) -> str | None:
    return None if valor is None else str(valor)
