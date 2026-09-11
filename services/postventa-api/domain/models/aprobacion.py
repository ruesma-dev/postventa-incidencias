# services/postventa-api/domain/models/aprobacion.py
"""La aprobación humana de un parte que la validación mandó a revisión (F-026).

**Dominio puro.** Ni red, ni base de datos, ni IA, ni `psycopg`: aquí solo hay
reglas y una función de huella de la biblioteca estándar. Eso es lo que permite
probar entera la pieza que decide si un parte que la máquina rechazó puede
acabar cerrando una incidencia en el ERP de producción.

## La regla que gobierna el módulo entero

**La aprobación se registra al lado del veredicto, nunca encima** (R11). Nada
de lo que hay aquí modifica un `ResultadoValidacion`: lo que dijo F-004 —el
veredicto, el destino y los motivos— se conserva intacto, y lo que se añade es
una segunda cosa, con su propio autor y su propia fecha. Escribir `apto` donde
la máquina dijo `no_apto` borraría el hecho de que hubo un motivo, y con él la
razón por la que alguien tuvo que decidir.

## Se aprueba por **motivo**, no por color

Los dos destinos no aptos de F-004 llegan ahí por razones distintas:
`cola_validacion_humana` es «hay algo que **decidir**» y `revision_manual` es
«hay algo que **arreglar**». Pero la línea de lo aprobable no es el destino,
es el motivo (R6–R9):

| Motivo | ¿Aprobable? | Por qué |
|---|---|---|
| `observaciones_manuscritas` | **Sí** | Es el juicio que la cola espera: una persona lee la transcripción y resuelve |
| `firma_no_humana` | **Sí** | F-004 clasifica `ilegible` ante cualquier duda; una persona con el PDF delante puede ver que sí era una firma |
| `codigo_obra_no_legible` | **No** | Sin código de obra no hay carpeta de archivo |
| `numero_incidencia_no_legible` | **No** | Sin nº de incidencia no hay reclamación que cerrar ni fichero que nombrar |

Los dos últimos no son una política: **no hay nada que decidir, hay algo que
teclear**, y teclearlo ya funciona desde F-011 sin aprobar nada. Aprobar un
parte al que le falta un dato decisivo sería aprobar algo que va a fallar.

## Por qué una huella y no una marca de tiempo

Una aprobación vale para **el veredicto que se aprobó**, no para el parte en
abstracto: quien mira una firma dudosa y dice «vale» está diciendo «vale
**esta** firma». Si el sistema vuelve a leer el papel y sale otra cosa, esa
persona no ha opinado sobre lo nuevo, y la aprobación se revoca (R30).

La comparación se hace por **huella** y no por fecha porque recuperar el
trabajo tras recargar la pantalla exige volver a subir la remesa, y eso
reprocesa cada parte: caducar por tiempo invalidaría todas las aprobaciones en
el único gesto con el que se recuperan (P5). Con la huella, un reproceso que
lea lo mismo **no revoca nada** (R32).

Y la huella no lleva dentro ni una letra del texto manuscrito (R15): es un
`sha256` en hexadecimal, de `hashlib`, o sea **cero dependencias nuevas**
(R45).
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from domain.models.validacion import (
    CodigoMotivo,
    Destino,
    ResultadoValidacion,
    Veredicto,
)

__all__ = [
    "MOTIVOS_APROBABLES",
    "Aprobacion",
    "MotivoRevocacion",
    "admite_circuito",
    "es_aprobable",
    "esta_vigente",
    "huella_de_veredicto",
]

#: Los dos motivos de F-004 sobre los que una persona **decide** (R6).
#:
#: La lista es cerrada a propósito y no se deduce del destino: es lo que
#: separa «esto lo puede resolver quien mire el papel» de «a este parte le
#: falta un dato y no hay nada que resolver». Ampliarla ensancha la única
#: puerta por la que un parte rechazado llega al ERP de producción, así que
#: ampliarla es cambiar la spec.
MOTIVOS_APROBABLES: tuple[CodigoMotivo, ...] = (
    CodigoMotivo.OBSERVACIONES_MANUSCRITAS,
    CodigoMotivo.FIRMA_NO_HUMANA,
)

#: Separador de los campos de la cadena canónica de la huella.
#:
#: Vale un salto de línea porque el único campo que puede traer saltos —el
#: texto de las observaciones— entra **ya normalizado**, con los espacios
#: colapsados, y va el último.
_SEPARADOR_CANONICO = "\n"

#: Separador de los códigos de motivo dentro de su campo.
_SEPARADOR_MOTIVOS = ","


class MotivoRevocacion(str, Enum):
    """Por qué una aprobación dejó de valer.

    Es una **etiqueta corta y cerrada** (R34), y solo hay una: el veredicto
    cambió. Nunca el texto que lo provocó —que sería la observación manuscrita
    del cliente, copiada a una segunda tabla— y nunca un mensaje libre, que
    acabaría siendo un sitio donde alguien vuelca lo que no cabe en ningún
    otro.
    """

    VEREDICTO_CAMBIADO = "veredicto_cambiado"


@dataclass(frozen=True)
class Aprobacion:
    """La decisión de una persona sobre un parte concreto, con su traza.

    `aprobado_por` es el `oid` **opaco** de Entra ID y nada más (R13): nunca
    el correo, nunca el nombre, nunca el login de Sigrid. Es el mismo
    tratamiento que ya reciben `cierres.confirmado_por` y
    `graficos.confirmado_por`, y por el mismo motivo: para saber que alguien
    decidió no hace falta saber quién es.

    `destino_aprobado` es **de dónde se rescató** el parte, y es lo único que
    las puertas del backend pueden comparar: el cuerpo de `/api/archivar` no
    trae ni los motivos ni las observaciones, así que ahí no se puede
    recomputar la huella. La vigencia no se resuelve al leer, se resuelve al
    escribir (R30).

    `motivos_aprobados` guarda **códigos**, no textos: el texto de un motivo
    es redacción para Posventa y puede cambiar; el código es contrato de
    F-004.

    `huella_aprobada` es sobre **qué veredicto exacto** se decidió, sin copiar
    la transcripción de las observaciones (R14, R15).

    `validado_at_utc` es traza, no criterio: quién decide la vigencia es la
    huella.

    Una aprobación revocada **no se borra** (R33): la decisión se tomó, y
    quién la tomó y cuándo sigue siendo información.
    """

    hash_parte: str
    aprobado_por: str
    aprobado_at_utc: datetime
    destino_aprobado: Destino
    motivos_aprobados: tuple[CodigoMotivo, ...]
    huella_aprobada: str
    validado_at_utc: datetime
    revocada_at_utc: datetime | None = None
    revocada_motivo: str | None = None

    @property
    def vigente(self) -> bool:
        """¿Sigue en pie esta decisión? Lo mismo que `esta_vigente`."""
        return self.revocada_at_utc is None


def es_aprobable(validacion: ResultadoValidacion | None) -> bool:
    """¿Puede una persona aprobar este parte? (R6–R10).

    Tres condiciones, y las tres hacen falta:

    1. Hay veredicto. Sin él no hay nada sobre lo que decidir, y eso se
       arregla revalidando el parte, no aprobándolo.
    2. **No es apto.** Un parte que la máquina ya dio por bueno no tiene nada
       que aprobar (R10).
    3. Tiene motivos y **todos** están en `MOTIVOS_APROBABLES` (R8, R9). Basta
       uno fuera de la lista para que no se pueda: el parte que trae
       observaciones **y** además ha perdido el código de obra no se aprueba,
       porque archivarlo lo metería en una carpeta inventada.

    No modifica nada de lo que recibe: el veredicto de F-004 se conserva
    entero (R11).
    """
    if validacion is None or validacion.veredicto == Veredicto.APTO:
        return False
    if not validacion.motivos:
        return False
    return all(motivo.codigo in MOTIVOS_APROBABLES for motivo in validacion.motivos)


def huella_de_veredicto(validacion: ResultadoValidacion) -> str:
    """La huella del veredicto sobre el que se decide (R14, R30).

    Función **pura**: mismas entradas, misma salida, y sin ninguna consulta.
    Por eso se puede calcular en cualquier punto donde exista un veredicto, que
    es lo que permite resolver la revocación en la escritura.

    La cadena canónica lleva cuatro cosas, en este orden fijo:

    1. el destino;
    2. los códigos de los motivos, **ordenados** —el orden en que F-004 los
       emite es un detalle suyo, y revocar por eso sería revocar por nada—;
    3. la clasificación efectiva de la firma, porque aprobar «esta firma
       dudosa» no es aprobar «no hay firma»;
    4. las observaciones **normalizadas**, o la cadena vacía.

    Por qué entra el texto de las observaciones: F-004 no lo interpreta
    —cualquier texto no vacío produce el mismo `observaciones_manuscritas`, y
    juzgarlo es F-016—, así que sin él «todo correcto» y «no se reparó nada»
    darían la misma huella y una aprobación sobre la primera valdría para la
    segunda (P4).

    Por qué **no** entran los valores de los campos: el nombrado cambia si
    cambia el código de obra, pero eso no es lo que se aprobó; y los campos
    decisivos ilegibles no son aprobables, así que su cambio ya sale reflejado
    en los motivos.

    Lo que sale es un `sha256` en hexadecimal, así que **no lleva dentro ni
    una letra del texto manuscrito** (R15).
    """
    codigos = sorted(motivo.codigo.value for motivo in validacion.motivos)
    canonica = _SEPARADOR_CANONICO.join(
        (
            validacion.destino.value,
            _SEPARADOR_MOTIVOS.join(codigos),
            validacion.clasificacion_firma.value,
            _normalizar(validacion.observaciones),
        )
    )
    return hashlib.sha256(canonica.encode("utf-8")).hexdigest()


def esta_vigente(aprobacion: Aprobacion | None) -> bool:
    """¿Hay una decisión de una persona que siga en pie? (R31).

    `None` **no es un error**: es que a ese parte no lo ha aprobado nadie. Y
    una aprobación revocada tampoco vale: mientras lo esté, vuelve a hacer
    falta que alguien mire el parte.
    """
    return aprobacion is not None and aprobacion.revocada_at_utc is None


def admite_circuito(
    validacion: ResultadoValidacion | None,
    aprobacion: Aprobacion | None,
) -> bool:
    """¿Entra este parte en el circuito de archivo, gráfico y cierre? (R23).

    Dos caminos, y solo dos:

    - **el de siempre**: apto con destino `archivo_y_cierre`, sin que nadie
      tenga que aprobar nada;
    - **el que abre F-026**: hay aprobación, está vigente, y su
      `destino_aprobado` es el que declara la validación de esta petición.

    Que el destino tenga que coincidir es lo que hace que la puerta sirva de
    algo sin poder recomputar la huella: si el parte pasó de la cola ámbar a
    revisión manual, la aprobación de la cola no dice nada de lo nuevo.

    `admite_circuito(None, …)` es **falso** pase lo que pase: «no hay
    veredicto» sigue siendo un motivo propio y distinto de «el veredicto dice
    que no», como ya distinguían los tres pasos del backend antes de F-026.

    Y esto es lo **único** que F-026 relaja. Siguen en pie el archivo previo,
    el gráfico antes del cierre, el dry-run dentro de la misma llamada que
    escribe, el login verificado contra el ERP y el estado de origen en el
    `WHERE` (R26).
    """
    if validacion is None:
        return False
    if (
        validacion.veredicto == Veredicto.APTO
        and validacion.destino == Destino.ARCHIVO_Y_CIERRE
    ):
        return True
    return esta_vigente(aprobacion) and aprobacion.destino_aprobado == validacion.destino


def _normalizar(texto: str | None) -> str:
    """El texto listo para la huella: recortado, colapsado y en minúsculas.

    La normalización no es cosmética: la lectura del modelo **no es
    determinista en el espaciado**, y sin esto una relectura del mismo papel
    con dos espacios donde antes había uno revocaría la aprobación de una
    persona que había juzgado exactamente lo mismo.

    `None` y «solo espacios» dan lo mismo —la cadena vacía—, que es la misma
    equivalencia que ya aplica F-004 al decidir si hay observaciones.
    """
    if texto is None:
        return ""
    return " ".join(texto.split()).lower()
