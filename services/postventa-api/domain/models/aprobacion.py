# services/postventa-api/domain/models/aprobacion.py
"""La huella del veredicto sobre el que alguien decidió (F-026, lo que queda).

**Dominio puro.** Ni red, ni base de datos, ni IA, ni `psycopg`: aquí solo hay
una función de huella de la biblioteca estándar y su normalizador. Eso es lo
que permite probar entera la pieza que decide si una decisión humana sigue
valiendo para el veredicto de ahora.

## Qué era este módulo, y qué queda de él

> **Enmienda del 2026-09-16 · F-028 T15 (`design.md` §8.2).** Hasta hoy este
> módulo era **el dominio entero de la decisión humana**: `Aprobacion`,
> `MOTIVOS_APROBABLES`, `es_aprobable`, `MotivoRevocacion`, `esta_vigente` y
> `admite_circuito`, que era el criterio con el que las tres puertas del
> backend dejaban pasar un parte al circuito de archivo y cierre.
>
> La premisa que lo gobernaba **sigue siendo cierta y no se borra**; decía,
> literal: *«La aprobación se registra al lado del veredicto, nunca encima
> (R11). Nada de lo que hay aquí modifica un `ResultadoValidacion`: lo que dijo
> F-004 —el veredicto, el destino y los motivos— se conserva intacto, y lo que
> se añade es una segunda cosa, con su propio autor y su propia fecha.»*
>
> Lo que cambia es **dónde vive esa segunda cosa**. F-028 la mudó a
> `domain/models/estado.py`, que no la guarda como «aprobado / no aprobado»
> sino como un **estado del parte** con cuatro valores y un histórico
> append-only detrás (`postventa.historico_estado`). Dos motivos, y ninguno es
> de estilo:
>
> 1. lo que F-026 no podía hacer era **rechazar un parte que la máquina había
>    dado por bueno**, porque su única operación era aprobar lo rechazado;
> 2. `postventa.aprobaciones` tiene **una fila por parte** y cada decisión
>    nueva sustituye a la anterior, así que un ciclo aprobar → rechazar →
>    aprobar no dejaba rastro del rechazo. El histórico de F-028 es
>    append-only y los deja los tres.
>
> Quien quiera saber hoy si un parte entra en el circuito pregunta
> `estado_del_parte(...) is EstadoParte.APROBADO`, y esa es la **única**
> respuesta que hay. Lo demás se retiró en T15.
>
> **La tabla `postventa.aprobaciones` no se ha borrado** (regla dura 3 de
> `specs/F-028-estado-del-parte/tasks.md`): guarda decisiones que tomaron
> personas de verdad, y el DDL del histórico la **siembra** en cada arranque
> para que esas decisiones sigan contando. Lo que se retiró es el código que la
> escribía y la leía, no el dato.

## Por qué sobrevive la huella, y por qué sobrevive **aquí**

Una decisión vale para **el veredicto que se decidió**, no para el parte en
abstracto: quien mira una firma dudosa y dice «vale» está diciendo «vale
**esta** firma». Si el sistema vuelve a leer el papel y sale otra cosa, esa
persona no ha opinado sobre lo nuevo, y su decisión deja de contar
(F-026 R30, F-028 R19).

La comparación se hace por **huella** y no por fecha porque recuperar el
trabajo tras recargar la pantalla exige volver a subir la remesa, y eso
reprocesa cada parte: caducar por tiempo invalidaría todas las decisiones en el
único gesto con el que se recuperan (P5). Con la huella, un reproceso que lea
lo mismo **no caduca nada** (R32).

Lo que cambió con F-028 es **cuándo se compara**. F-026 la resolvía al escribir
—`revocar_aprobacion_si_cambio` viajaba pegado al guardado del veredicto— y
dejaba la fila marcada como revocada. F-028 la resuelve al **derivar**:
`estado.py::_aprueba_lo_que_hay` compara la huella apuntada en el histórico con
la del veredicto de ahora, cada vez que hace falta el estado. Nada que revocar,
nada que reescribir, y el histórico no pierde la fila.

Y la huella no lleva dentro ni una letra del texto manuscrito (R15): es un
`sha256` en hexadecimal, de `hashlib`, o sea **cero dependencias nuevas** (R45).
"""

from __future__ import annotations

import hashlib

from domain.models.validacion import ResultadoValidacion

__all__ = ["huella_de_veredicto"]

#: Separador de los campos de la cadena canónica de la huella.
#:
#: Vale un salto de línea porque el único campo que puede traer saltos —el
#: texto de las observaciones— entra **ya normalizado**, con los espacios
#: colapsados, y va el último.
_SEPARADOR_CANONICO = "\n"

#: Separador de los códigos de motivo dentro de su campo.
_SEPARADOR_MOTIVOS = ","


def huella_de_veredicto(validacion: ResultadoValidacion) -> str:
    """La huella del veredicto sobre el que se decide (R14, R30; F-028 R19).

    Función **pura**: mismas entradas, misma salida, y sin ninguna consulta.
    Por eso se puede calcular en cualquier punto donde exista un veredicto, que
    es lo que permite resolver la caducidad al derivar el estado.

    La cadena canónica lleva seis cosas, en este orden fijo:

    1. el destino;
    2. los códigos de los motivos, **ordenados** —el orden en que F-004 los
       emite es un detalle suyo, y caducar por eso sería caducar por nada—;
    3. la clasificación efectiva de la firma, porque aprobar «esta firma
       dudosa» no es aprobar «no hay firma»;
    4. las observaciones **normalizadas**, o la cadena vacía;
    5. el **código de obra**, normalizado;
    6. el **número de incidencia**, normalizado.

    Los dos van por el mismo `_normalizar` que las observaciones: un número
    con un espacio de más o en otra caja es **el mismo número**, y caducar por
    eso sería caducar por nada, igual que pasaría con el orden de los motivos.

    Por qué entra el texto de las observaciones: F-004 no lo interpreta
    —cualquier texto no vacío produce el mismo `observaciones_manuscritas`, y
    juzgarlo es F-016—, así que sin él «todo correcto» y «no se reparó nada»
    darían la misma huella y una decisión sobre la primera valdría para la
    segunda (P4).

    **Los dos campos decisivos SÍ entran** (5 y 6), y esto es una enmienda:

    > **Enmienda del 2026-09-12 · H-1 de `progress/review_F-026.md`.** Hasta
    > hoy esta función decía, literal: *«Por qué **no** entran los valores de
    > los campos: el nombrado cambia si cambia el código de obra, pero eso no
    > es lo que se aprobó; y los campos decisivos ilegibles no son aprobables,
    > así que su cambio ya sale reflejado en los motivos.»*
    >
    > Ese razonamiento examinaba el **código de obra** y **no llegó a examinar
    > el número de incidencia**, que es el que decide **sobre qué reclamación
    > del ERP de producción se escribe el cierre**. El camino que dejaba
    > abierto: un parte va a la cola por observaciones, alguien lo aprueba
    > mirando el papel, otra persona corrige el número a uno distinto —también
    > legible, así que ningún motivo cambia—, revalida, y la aprobación
    > sobrevive y acaba cerrando **otra** reclamación.
    >
    > Entra también el **código de obra**, por su propio motivo: decide la
    > carpeta y el nombre del fichero, y lo que se archiva es un PDF con el DNI
    > manuscrito de un cliente. Una aprobación que sobreviviera a cambiarlo
    > estaría avalando que ese documento se guarde en la carpeta de otra obra.
    >
    > Lo decidió el responsable del proyecto el **2026-09-12**, tras leer el
    > hallazgo. **Este era el momento**: tocar la huella invalida las
    > aprobaciones existentes, y no había ninguna porque la feature todavía no
    > se había desplegado.

    Sigue siendo cierto que **un campo decisivo ilegible no es aprobable**, así
    que lo que estos dos añaden no es la legibilidad —que ya sale en los
    motivos— sino **la identidad de lo que se aprobó**.

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
            _normalizar(validacion.codigo_obra),
            _normalizar(validacion.numero_incidencia),
        )
    )
    return hashlib.sha256(canonica.encode("utf-8")).hexdigest()


def _normalizar(texto: str | None) -> str:
    """El texto listo para la huella: recortado, colapsado y en minúsculas.

    La normalización no es cosmética: la lectura del modelo **no es
    determinista en el espaciado**, y sin esto una relectura del mismo papel
    con dos espacios donde antes había uno caducaría la decisión de una
    persona que había juzgado exactamente lo mismo.

    `None` y «solo espacios» dan lo mismo —la cadena vacía—, que es la misma
    equivalencia que ya aplica F-004 al decidir si hay observaciones.
    """
    if texto is None:
        return ""
    return " ".join(texto.split()).lower()
