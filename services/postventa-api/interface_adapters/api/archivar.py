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

## El veredicto ya no llega en el cuerpo: se lee de donde está guardado

**Enmienda del 2026-09-16 (F-030).** Hasta hoy este endpoint reconstruía un
`ResultadoValidacion` con el `veredicto` y el `destino` del formulario y
valores fijos para todo lo demás —sin motivos, firma `humana`, sin
observaciones, con los dos campos decisivos vacíos— y la puerta del paso
derivaba el estado de **ese** objeto. Rompía el circuito por los dos lados:

- la huella recomputada sobre el stub no dependía del parte —era una de tres
  constantes—, así que lo que una persona hubiera decidido sobre ese parte no
  coincidía nunca con la suya y el parte volvía a `pendiente`. La incidencia
  RS26.09/0178 se quedó así, decidida por una persona y sin archivar;
- y al revés, un cuerpo que dijera `veredicto=apto` pasaba la puerta sin que
  nadie hubiera mirado el parte. Lo único que lo impedía era que el front
  mandara la verdad.

Desde F-030 el contexto sale de aquí **sin veredicto**, y la puerta lo lee de
`postventa.validaciones` dentro de la consulta de situación que ya hacía
(`F-030 design.md` §5.4). Aquella decisión D4 de F-006 —«no se lee de la base
porque exige un método nuevo en el puerto, y eso es de F-005»— queda atendida
**sin método nuevo**: el veredicto viaja dentro de `SituacionParte`.

`veredicto` y `destino` **siguen siendo obligatorios en el cuerpo y siguen
validándose** contra las enumeraciones de F-004: el contrato HTTP no cambia y
un valor desconocido sigue siendo un 400 (R19, D6 de F-030). Lo que ya no
hacen es decidir nada.

## L1 sale de la situación que lee la puerta (F-033, 2026-09-18)

Este endpoint **no** pasa ninguna traza de archivo al paso: L1 la lee de la
situación que ya consulta la puerta de estado, del almacén. Lo único que añade
es la biblioteca vigente (`SHAREPOINT_DRIVE_ID`), para que el paso pueda avisar
si lo archivado está en otra; no sale en la respuesta ni en ningún log.

## Los dos códigos dejan de nombrar y pasan a cotejar (F-031, 2026-09-22)

**Enmienda del 2026-09-22.** Hasta hoy este handler metía `codigo_obra` y
`numero_incidencia` dentro de la `ExtraccionParte` de pega y el paso nombraba
el fichero con ellos. Es decir: desde F-030 la puerta de estado dejaba pasar
mirando los códigos **guardados**, y el PDF se nombraba con los
**declarados**. Coincidían porque
el front manda lo que leyó —una costumbre, no una garantía—, y la ventana
real del defecto son los 1.500 ms de rebote del autoguardado: quien corrige
un código y pulsa «archivar y cerrar» sin esperar manda uno que no está en la
base.

Desde F-031:

- los dos códigos viajan al paso **explícitos**, en `codigos_declarados`, y
  sirven solo para **cotejarlos** contra lo guardado. Si no cuadran, sale un
  **409** y no se archiva nada (F-031 R3, R5; decisiones D-2 y D-3);
- `_como_contexto` **deja de rellenarlos**: los nueve campos de la extracción
  van vacíos, y ese objeto deja de ser una fuente de datos;
- `CAMPOS_OBLIGATORIOS` **no cambia** (R10): los cinco siguen siendo
  obligatorios y un cuerpo incompleto sigue siendo un 400 (R6). Lo que cambia
  es para qué sirven dos de ellos. Retirarlos del contrato habría perdido la
  detección: sin lo declarado no hay con qué cotejar (D-4).
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

# F-034 · la pieza compartida con el gráfico y el cierre (D-2); ni una regla
# de este endpoint cambia (R26).
from application.pipelines.codigos_del_parte import CodigosDelParte
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
from domain.models.remesa import ModoDeteccion, ParteTroceado
from domain.models.validacion import Destino, Veredicto
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

    Levanta `CuerpoDeArchivoInvalido` (→ 400), `ParteNoApto`,
    `CodigosNoCoinciden` y `NombradoImposible` (→ 409), `ArchivoDeshabilitado`,
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
        _como_contexto(contenido, hash_parte=hash),
        archivador if archivador is not None else construir_archivador(ajustes),
        repositorio
        if repositorio is not None
        else construir_repositorio(ajustes),
        carpeta_base=ajustes.sharepoint_carpeta_base,
        ahora=ahora if ahora is not None else datetime.now(UTC),
        drive_id_vigente=ajustes.sharepoint_drive_id,
        # F-031 · lo que **afirma** el cuerpo. Solo sirve para cotejarlo
        # contra lo guardado (R3); no nombra nada y no decide nada (R11).
        codigos_declarados=CodigosDelParte(
            codigo_obra=codigo_obra, numero_incidencia=numero_incidencia
        ),
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


def _como_contexto(contenido: bytes, *, hash_parte: str) -> ContextoParte:
    """Reconstruye el contexto mínimo que necesita el paso de archivo.

    Al endpoint le llega un parte ya troceado y **suelto**, igual que a
    `/api/extraer`: quien conoce su origen es el front, que lo tiene de la
    respuesta de `/api/split`.

    Los **nueve** campos de la extracción van vacíos y a cero. Siete lo iban
    ya, a propósito: este endpoint no los necesita, y pedirlos obligaría al
    front a reenviar el DNI y las observaciones manuscritas del cliente en
    cada archivo, que es exactamente el dato que no debe viajar de más.

    Y **el veredicto se va sin rellenar** (F-030): este endpoint no recibe la
    extracción, así que no puede emitirlo, y fabricarlo con lo poco que tiene
    es lo que rompió el circuito. Lo lee la puerta del paso, de la base.

    > **Enmienda del 2026-09-22 (F-031).** Los otros dos —`codigo_obra` y
    > `numero_incidencia`— **dejan de rellenarse aquí**, y con eso este objeto
    > deja de ser una fuente de datos y pasa a ser lo que F-030 decía que era:
    > un contexto mínimo con el `hash` y los bytes. Rellenarlos afirmaba «esto
    > leyó la IA» sobre lo que había escrito un formulario, y esa confusión es
    > la que dejó el defecto: el fichero acababa nombrado con lo declarado
    > mientras la puerta de estado miraba lo guardado. Los dos siguen llegando al
    > endpoint y siguen siendo obligatorios (R10), pero viajan **explícitos**,
    > en `codigos_declarados`, y solo para cotejar.
    """
    campos = {nombre: CampoExtraido(valor=None, confianza_pct=0) for nombre in CAMPOS_DEL_PARTE}
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
        validacion=None,
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
