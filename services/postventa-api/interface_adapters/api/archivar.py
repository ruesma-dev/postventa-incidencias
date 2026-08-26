# services/postventa-api/interface_adapters/api/archivar.py
"""Handler de `POST /api/archivar`, sin nada de Azure dentro.

Aquí se **compone el paso** —archivador y repositorio, con sus adaptadores— y
se serializa el resultado, como manda `docs/CONVENTIONS.md`: la composición
vive en el punto de entrada y nunca dentro de un paso.

Los dos puertos inyectables son **la costura de test** del endpoint: con
ellos, la suite prueba el borde entero sin que SharePoint aparezca por ninguna
parte. Sin ellos, el handler construye lo de verdad, y es ahí —y solo ahí—
donde se topa con la puerta de entorno. Por eso, llamado desde un puesto de
trabajo, este endpoint responde **503** y no sube nada.

Una llamada = **un parte**, como `/api/extraer`: la Function corta a los 230 s.

## Por qué existe este endpoint y no solo el paso del pipeline

Porque sin él **no hay ninguna forma legítima de ejercitar la subida real**.
La única vía permitida es el entorno desplegado (`design.md` §5), y algo tiene
que haber ahí que se pueda invocar. Este endpoint es lo que hace posible la
verificación manual **T18**.

## El veredicto llega en el cuerpo, y se vuelve a comprobar

Decisión **D4** de `design.md` §10. Leerlo de la base sería más fuerte, pero
exige un método nuevo en `RepositorioPartesPort`, que es de F-005, y F-006 no
cambia specs ajenas. Lo que sí se hace es **no fiarse**: el veredicto que
llega se reconstruye como `ResultadoValidacion` y `paso_archivo` lo vuelve a
comprobar contra el destino, igual que si viniera de dentro.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from application.pipelines.contexto_parte import ContextoParte
from application.pipelines.paso_archivo import paso_archivo
from config.settings import obtener_ajustes
from domain.models.errores import CuerpoDeArchivoInvalido
from domain.models.extraccion import (
    CAMPOS_DEL_PARTE,
    CampoExtraido,
    ExtraccionParte,
    TrazaExtraccion,
)
from domain.models.firma import ClasificacionFirma
from domain.models.remesa import ModoDeteccion, ParteTroceado
from domain.models.validacion import Destino, ResultadoValidacion, Veredicto
from domain.ports.archivo import ArchivoPort
from domain.ports.persistencia import RepositorioPartesPort
from infrastructure.persistencia.fabrica import construir_repositorio
from infrastructure.sharepoint.fabrica import construir_archivador

#: Lo que el cuerpo tiene que traer, además del fichero.
CAMPOS_OBLIGATORIOS = (
    "hash",
    "codigo_obra",
    "numero_incidencia",
    "veredicto",
    "destino",
)


def archivar_parte(
    contenido: bytes,
    *,
    hash: str = "",
    codigo_obra: str = "",
    numero_incidencia: str = "",
    veredicto: str = "",
    destino: str = "",
    archivador: ArchivoPort | None = None,
    repositorio: RepositorioPartesPort | None = None,
    ahora: datetime | None = None,
) -> dict[str, Any]:
    """Archiva **un** parte apto y devuelve el cuerpo de la respuesta.

    Levanta `CuerpoDeArchivoInvalido` (→ 400), `ParteNoApto` y
    `NombradoImposible` (→ 409), `ArchivoDeshabilitado`,
    `ConfiguracionSharePointIncompleta`, `ConfiguracionPgIncompleta` y
    `PersistenciaNoDisponible` (→ 503), `ArchivoFallido` (→ 502) y
    `ArchivoSinTraza` (→ 500) **sin traducirlas**: convertir eso en códigos
    HTTP es trabajo del borde.

    Las tres últimas vienen de la persistencia y no de SharePoint, y la
    diferencia entre ellas es **si el fichero llegó a subirse**: solo
    `ArchivoSinTraza` significa que sí. Lo demás —incluido lo que levanta
    `construir_repositorio` aquí abajo, que corre **antes** de que se suba
    nada— deja la biblioteca de Posventa intacta.
    """
    _exigir_cuerpo(
        hash=hash,
        codigo_obra=codigo_obra,
        numero_incidencia=numero_incidencia,
        veredicto=veredicto,
        destino=destino,
    )
    ajustes = obtener_ajustes()
    contexto = paso_archivo(
        _como_contexto(
            contenido,
            hash_parte=hash,
            codigo_obra=codigo_obra,
            numero_incidencia=numero_incidencia,
            veredicto=veredicto,
            destino=destino,
        ),
        archivador if archivador is not None else construir_archivador(ajustes),
        repositorio
        if repositorio is not None
        else construir_repositorio(ajustes),
        carpeta_base=ajustes.sharepoint_carpeta_base,
        ahora=ahora if ahora is not None else datetime.now(UTC),
    )
    return _serializar(contexto)


def _exigir_cuerpo(**campos: str) -> None:
    """El cuerpo, comprobado; o el 400 diciendo **qué** le falta.

    Un 400 que no lo dice obliga a leer el código del servidor para arreglar
    una petición que manda otro equipo.

    El veredicto y el destino se comprueban contra las enumeraciones de F-004:
    un valor que no existe no puede convertirse en «no apto» por descuido —eso
    sería un 409 donde hay una petición mal formada— ni, mucho peor, en apto.
    """
    faltan = [nombre for nombre, valor in campos.items() if not (valor or "").strip()]
    if faltan:
        raise CuerpoDeArchivoInvalido(
            f"la petición no trae: {', '.join(sorted(faltan))}"
        )

    _exigir_valor_conocido(Veredicto, campos["veredicto"], "veredicto")
    _exigir_valor_conocido(Destino, campos["destino"], "destino")


def _exigir_valor_conocido(enumeracion, valor: str, nombre: str) -> None:
    """El valor tiene que ser uno de los que declara el dominio."""
    admitidos = [miembro.value for miembro in enumeracion]
    if valor not in admitidos:
        raise CuerpoDeArchivoInvalido(
            f"'{nombre}' no es uno de los valores admitidos "
            f"({', '.join(admitidos)})"
        )


def _como_contexto(
    contenido: bytes,
    *,
    hash_parte: str,
    codigo_obra: str,
    numero_incidencia: str,
    veredicto: str,
    destino: str,
) -> ContextoParte:
    """Reconstruye el contexto mínimo que necesita el paso de archivo.

    Al endpoint le llega un parte ya troceado y **suelto**, igual que a
    `/api/extraer`: quien conoce su origen es el front, que lo tiene de la
    respuesta de `/api/split`.

    De la extracción solo se reconstruyen los dos campos que deciden el
    nombre. Los otros siete van vacíos **a propósito**: este endpoint no los
    necesita, y pedirlos obligaría al front a reenviar el DNI y las
    observaciones manuscritas del cliente en cada archivo, que es exactamente
    el dato que no debe viajar de más.
    """
    campos = {nombre: CampoExtraido(valor=None, confianza_pct=0) for nombre in CAMPOS_DEL_PARTE}
    campos["codigo_obra"] = CampoExtraido(valor=codigo_obra, confianza_pct=100)
    campos["numero_incidencia"] = CampoExtraido(
        valor=numero_incidencia, confianza_pct=100
    )
    return ContextoParte(
        parte=ParteTroceado(
            hash=hash_parte,
            origen="",
            paginas_origen=(),
            modo_deteccion=ModoDeteccion.UNA_PAGINA_POR_PARTE,
            contenido=contenido,
        ),
        extraccion=ExtraccionParte(
            hash_parte=hash_parte,
            campos=campos,
            traza=TrazaExtraccion(
                proveedor="", modelo="", prompt_key="", version_prompt="", huella_prompt=""
            ),
        ),
        validacion=ResultadoValidacion(
            hash_parte=hash_parte,
            veredicto=Veredicto(veredicto),
            destino=Destino(destino),
            motivos=(),
            clasificacion_firma=ClasificacionFirma.HUMANA,
            observaciones=None,
            confianza_observaciones=0,
        ),
    )


def _serializar(contexto: ContextoParte) -> dict[str, Any]:
    """Pasa el resultado a JSON. **Ni una clave más que las de R30.**

    Ni el contenido del PDF, ni ningún campo manuscrito, ni la configuración
    del destino: esta respuesta la recibe un navegador.
    """
    traza = contexto.archivo
    return {
        "hash_parte": traza.hash_parte,
        "nombre_fichero": traza.nombre_fichero,
        "carpeta": traza.carpeta,
        "estado": traza.estado.value,
        "web_url": traza.web_url,
        "avisos": list(contexto.avisos),
    }
