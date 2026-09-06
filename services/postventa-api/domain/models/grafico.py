# services/postventa-api/domain/models/grafico.py
"""El vocabulario del gráfico: el parte firmado dentro de Sigrid (F-012, paso 7a).

**Dominio puro**: sin red, sin SQL, sin reloj y sin configuración. Entra una
reclamación leída del ERP más los bytes del parte, y sale **exactamente** lo que
viajará a la pasarela. Igual que `domain/models/cierre.py`, se puede probar
entero sin abrir una conexión contra el ERP de producción — que es lo que
permite cubrirlo y mutarlo.

Y una cosa que este módulo **no** hace, a propósito: no sabe **cómo se
codifica** el contenido para viajar por HTTP. El transporte es cosa del
adaptador, y `test_f012_arquitectura.py` lo fija con un control negativo que
busca esa palabra en todo `domain/` y `application/`. Aquí el contenido son
bytes.

## Las tres reglas que este módulo no negocia

1. **`conide` y `contip` salen de la reclamación leída, nunca de una
   constante** (R8). La configuración sirve para **buscar**; lo que se escribe
   sale de lo que el ERP devolvió. Es el mismo principio que R4 de F-009.
2. **Lo que no cabe en el ERP no se trunca: se rechaza** (R9, R10, R12). Un
   nombre truncado deja de cruzar con el fichero de SharePoint y un login
   truncado es otro login.
3. **«Colgado» es `ok and (committed or idempotente)`** (R26). Decidir por
   `committed` a solas daría por fallido un éxito idempotente, y ese es el
   aviso literal del contrato de la pasarela (`azure-apps/sigrid_api.md` §8.8).

## `hash` y `sha256` son dos cosas, y aquí no se confunden

`hash` es la **huella de páginas** del parte (F-002), estable entre
reserializaciones, y es la clave de todas las trazas. `sha256` es el hash de
**los bytes exactos** que se envían, y es lo único que la pasarela coteja y lo
que decide su idempotencia. Este módulo produce el segundo y no toca el
primero.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

from domain.models.cierre import Reclamacion
from domain.models.errores import (
    CuerpoDeGraficoInvalido,
    GraficoDemasiadoGrande,
    GraficoNoEsPdf,
)
from domain.models.nombrado import nombre_de_archivo
from domain.models.persistencia import EstadoGrafico, TrazaGrafico

__all__ = [
    "CODIGOS_PASARELA_PRECONDICION",
    "CODIGOS_PASARELA_RECHAZO",
    "CODIGOS_PASARELA_REINTENTABLES",
    "FILAS_ESPERADAS_GRAFICO",
    "FIRMA_PDF",
    "LONGITUD_MAXIMA_NOM",
    "LONGITUD_MAXIMA_RES",
    "LONGITUD_MAXIMA_USU",
    "RES_GRAFICO_PARTE",
    "PeticionGrafico",
    "PlanDeGrafico",
    "RespuestaGrafico",
    "ResultadoGrafico",
    "clasificar_codigo",
    "componer_peticion",
    "esta_colgado",
    "validar_fichero",
]

#: La descripción con la que el gráfico queda en la ficha de Sigrid (R10).
#:
#: Es literalmente lo que Posventa teclea: `PARTE FIRMADO` en **3.197 de los
#: 3.680** gráficos de esta clase **[MEDIDO]**. `res` es lo que la pantalla del
#: ERP enseña como «Descripción» a quien abre la reclamación, así que un texto
#: propio y rastreable ensuciaría cada ficha de un documento de trabajo ajeno.
#: La trazabilidad de «qué gráficos son nuestros» la da `postventa.graficos`.
RES_GRAFICO_PARTE = "PARTE FIRMADO"

#: La firma binaria de un PDF (R19). La misma que la pasarela exige en su
#: `SIGRID_DOCUMENT_ALLOWED_MAGIC`; se comprueba aquí para no mandar por el
#: proxy un fichero que ya se sabe que va a rechazar.
FIRMA_PDF = b"%PDF-"

#: `gra.res` es «Texto de 48 caracteres» **[MEDIDO en `sigrid_tablas.md`]**.
LONGITUD_MAXIMA_RES = 48

#: `gra.nom` es `varchar(255)` **[MEDIDO]**. `nom` se escribe también en
#: `nomori`, que es igual de largo.
LONGITUD_MAXIMA_NOM = 255

#: `usu.cod` es «Texto 24» **[MEDIDO]**, y es el tope que aplica la pasarela.
#: `gra.usu` es más ancho, pero el login tiene que existir en `dbo.usu`.
LONGITUD_MAXIMA_USU = 24

#: Lo que afecta un gráfico escrito de verdad: el binario en la documental,
#: los metadatos en la de negocio y el enlace. **Tres filas, dos bases** (R27).
#:
#: La pasarela ya lo comprueba —relee las tres antes del `COMMIT`— y aquí se
#: vuelve a comprobar, por lo mismo que en el cierre: dar por adjuntado lo que
#: no lo está deja una reclamación cerrada sin su parte, que es justo la
#: anomalía que esta feature elimina.
FILAS_ESPERADAS_GRAFICO = 3

#: `details.codigo` con los que **el ERP quedó sin cambios** y el reintento es
#: seguro (R31). Los tres revierten: la pasarela los levanta antes del `COMMIT`
#: o dentro de la transacción. → 502.
CODIGOS_PASARELA_REINTENTABLES: tuple[str, ...] = (
    "colision_de_clave",
    "sha256_no_coincide",
    "filas_afectadas_inesperadas",
)

#: `details.codigo` que dicen que falta una **precondición del dueño de
#: `sigrid-api`** (R32). No es un fallo de esta feature ni de quien llama: es
#: configuración de otro proyecto, declarada en `docs/INTEGRACION.md` §6. → 503.
CODIGOS_PASARELA_PRECONDICION: tuple[str, ...] = (
    "escritura_documental_deshabilitada",
    "base_de_datos_no_permitida",
)

#: `details.codigo` con los que la pasarela **rechaza la petición**, sin
#: escribir nada (R33). Los tres últimos no deberían llegar nunca: R18 y R19
#: los cortan antes. → 409.
CODIGOS_PASARELA_RECHAZO: tuple[str, ...] = (
    "concepto_no_encontrado",
    "tipo_de_concepto_no_coincide",
    "clase_de_grafico_no_permitida",
    "usuario_no_valido",
    "fichero_vacio",
    "tipo_de_fichero_no_permitido",
    "tamano_excedido",
)


@dataclass(frozen=True)
class PeticionGrafico:
    """Lo que viaja a `POST /api/sigrid/concepto-grafico`, campo a campo.

    Lo que **no** está aquí es tan importante como lo que está: ni la base
    documental, ni `cod`, ni `ide`, ni `vin`, ni `pos`, ni `emp` (R13). Todo
    eso lo decide la pasarela con constantes medidas contra el ERP, y mandarlo
    sería inventarse la mitad de un modelo de datos ajeno.

    `contenido` va con **`repr=False`** y no es cosmética: dentro de ese PDF
    está el DNI manuscrito del cliente, y un `repr` que lo volcara acabaría en
    un log, en la traza de una excepción o en un mensaje de error — tres sitios
    que sobreviven al parte (R53).
    """

    conide: int
    contip: int
    gratipide: int
    res: str
    nom: str
    usu: str
    sha256: str
    bytes: int
    #: **DATO PERSONAL directo**: el PDF del parte, con el DNI y las
    #: observaciones manuscritas dentro. Nunca al log, nunca a un mensaje.
    contenido: bytes = field(repr=False, default=b"")


@dataclass(frozen=True)
class PlanDeGrafico:
    """Lo que devuelve el dry-run: qué se adjuntaría, y si se puede.

    `ya_cerrada` es un campo propio y no un `motivo` más porque **no es un
    error** (R16), exactamente igual que en `PlanDeCierre`: la reclamación
    estaba cerrada antes de que llegáramos y no se le cuelga un segundo
    gráfico.

    `avisos_pasarela` se transporta **tal cual** (R21, R67): ahí van, entre
    otros, los gráficos huérfanos que la pasarela detecta y que esta feature no
    toca (H6). Reescribirlos aquí sería opinar sobre el ERP de otro.
    """

    reclamacion: Reclamacion
    login_sigrid: str
    peticion: PeticionGrafico
    cerrable: bool
    ya_cerrada: bool = False
    motivo: str | None = None
    #: El dry-run ya lo encontró colgado: el commit no escribirá nada (R22).
    idempotente_previsto: bool = False
    cod_previsto: str | None = None
    ide_negocio_previsto: int | None = None
    avisos_pasarela: tuple[str, ...] = ()


@dataclass(frozen=True)
class RespuestaGrafico:
    """Lo que el adaptador saca de la respuesta de la pasarela, y nada más.

    De las 29 columnas por fila que trae el preview (`fila_documental`,
    `fila_negocio`) **no se guarda ninguna**: el usuario no decide ninguna de
    ellas y sacarlas al front sería volcar el modelo de datos del ERP en un
    navegador.

    Tres campos llegan a `None` en la respuesta idempotente y **eso no es un
    error** **[MEDIDO en T21 de F-004]**: `ide_documental`, `pos` y, con ellos,
    `committed: false`. `esta_colgado` responde `True` igual.
    """

    ok: bool
    committed: bool
    idempotente: bool
    dry_run: bool
    filas_afectadas: int
    bytes: int
    sha256: str
    cod: str | None = None
    ide_negocio: int | None = None
    ide_documental: int | None = None
    ide_enlace: int | None = None
    pos: int | None = None
    avisos: tuple[str, ...] = ()


@dataclass(frozen=True)
class ResultadoGrafico:
    """Qué pasó al adjuntar: el estado, el plan y la respuesta de la pasarela.

    Lleva **el plan entero** y no solo el estado porque quien recibe la
    respuesta necesita ver el dry-run —nombre, clase, tamaño, `sha256`, avisos—
    antes de confirmar (R21). La traza que se guarda en la base es otra cosa y
    guarda menos: el `oid` y nunca el login (R44).

    `plan` es **anulable**, y eso no es laxitud: es R24. Cuando la traza local
    ya dice `adjuntado`, el paso responde **sin llamar a nadie** —ni dry-run, ni
    commit, ni bytes—, así que no hay reclamación leída con la que construir un
    plan. En ese caso lo que se devuelve es `traza`, que es de dónde salió la
    respuesta. Inventar un plan a partir de la traza sería fabricar un dry-run
    que nadie ha ejecutado.
    """

    estado: EstadoGrafico
    plan: PlanDeGrafico | None = None
    #: La traza local con la que se resolvió, cuando se resolvió con ella (R24).
    traza: TrazaGrafico | None = None
    respuesta: RespuestaGrafico | None = None
    motivo: str | None = None
    adjuntado_at_utc: datetime | None = None


def validar_fichero(contenido: bytes, *, tope_bytes: int) -> tuple[int, str]:
    """El tamaño y el `sha256` de los bytes, o el motivo por el que no valen.

    Es la puerta que hace que R18 y R19 se comprueben **antes de llamar a
    nadie**: mandar 13 MB codificados por el proxy para que los rechacen al
    otro lado gasta el presupuesto de 45 s en un rechazo que ya se sabía.

    El **tope va primero** y la firma después, y el orden está decidido a
    propósito: lo que no puede pasar es tener que mirar dentro de un fichero
    enorme para descubrir que además no era un PDF.

    El mensaje del tope dice **cuánto ocupa y cuál es el tope** —los dos
    números sin los cuales no se sabe qué corregir— y el de la firma **no lleva
    ni un byte del fichero**: si no es un PDF puede ser cualquier cosa (R53).
    """
    tamano = len(contenido)
    if tamano > tope_bytes:
        raise GraficoDemasiadoGrande(
            f"el parte ocupa {tamano} bytes y el tope de esta feature son "
            f"{tope_bytes}: no se manda a la pasarela un fichero que ya se "
            f"sabe que va a rechazar"
        )
    if not contenido.startswith(FIRMA_PDF):
        raise GraficoNoEsPdf(
            "el fichero no empieza por la firma de un PDF, así que no se "
            "adjunta a la reclamación: la pasarela solo admite PDF y el "
            "contenido no se registra para poder decir qué era"
        )
    return tamano, hashlib.sha256(contenido).hexdigest()


def componer_peticion(
    *,
    reclamacion: Reclamacion,
    login: str,
    codigo_obra: str | None,
    numero_incidencia: str | None,
    gratipide: int,
    contenido: bytes,
    bytes: int,
    sha256: str,
) -> PeticionGrafico:
    """La petición exacta que viajará a la pasarela (R8–R12).

    `nom` sale de `domain/models/nombrado.py`, que es **el mismo nombre con el
    que el parte está en SharePoint**: un documento, un nombre, dos sitios, y
    cruzarlos es comparar dos cadenas iguales. Levanta `NombradoImposible` si
    faltan los códigos, igual que al archivar.

    `res` es la constante del dominio, y `conide`/`contip` salen de la
    reclamación leída y no de la configuración (R8).

    Los tres topes del ERP se comprueban aquí y **no se trunca nada**: un
    nombre truncado deja de cruzar con SharePoint y un login truncado es otro
    login.
    """
    usu = (login or "").strip()
    if not usu:
        raise CuerpoDeGraficoInvalido(
            "no hay login de Sigrid con el que firmar el gráfico: sin él no se "
            "adjunta nada al ERP"
        )
    if len(usu) > LONGITUD_MAXIMA_USU:
        raise CuerpoDeGraficoInvalido(
            f"el login «{usu}» no cabe en el maestro de usuarios del ERP "
            f"({LONGITUD_MAXIMA_USU} caracteres) y no se trunca: un login "
            f"truncado es otro login"
        )

    nom = nombre_de_archivo(
        codigo_obra=codigo_obra, numero_incidencia=numero_incidencia
    )
    if len(nom) > LONGITUD_MAXIMA_NOM:
        raise CuerpoDeGraficoInvalido(
            f"el nombre del fichero ocupa {len(nom)} caracteres y en el ERP "
            f"caben {LONGITUD_MAXIMA_NOM}; no se trunca, porque un nombre "
            f"truncado deja de cruzar con el fichero archivado"
        )

    return PeticionGrafico(
        conide=reclamacion.ide,
        contip=reclamacion.tip,
        gratipide=gratipide,
        res=RES_GRAFICO_PARTE,
        nom=nom,
        usu=usu,
        sha256=sha256,
        bytes=bytes,
        contenido=contenido,
    )


def esta_colgado(respuesta: RespuestaGrafico) -> bool:
    """¿El documento está dentro de Sigrid? `ok and (committed or idempotente)`.

    Es una función de una línea **a propósito**: es la regla de R26 y tiene que
    tener nombre, test y mutantes propios. La propia pasarela avisa de que
    decidir por `committed` a solas ve `false` en un éxito, porque en el caso
    idempotente no se escribió ninguna fila y decir lo contrario sería mentir.
    """
    return respuesta.ok and (respuesta.committed or respuesta.idempotente)


def clasificar_codigo(
    codigo: str | None,
) -> Literal["reintentable", "precondicion", "rechazo", "desconocido"]:
    """A cuál de las tres familias pertenece un `details.codigo` (R31–R34).

    Lista **cerrada**: lo que no está declarado sale como `desconocido` y el
    borde lo trata como un 502. Tratarlo «como si fuera» un rechazo daría un
    409, que promete que el ERP quedó intacto — y eso, con un código que nadie
    ha declarado, no se sabe.
    """
    if codigo in CODIGOS_PASARELA_REINTENTABLES:
        return "reintentable"
    if codigo in CODIGOS_PASARELA_PRECONDICION:
        return "precondicion"
    if codigo in CODIGOS_PASARELA_RECHAZO:
        return "rechazo"
    return "desconocido"
