# services/postventa-api/tests/test_f032_huella_intacta.py
"""La huella del veredicto no se ha movido con F-032 (R17–R21).

**El control que paga esta feature.** F-032 cambia `normalizar_codigo` para que
un código pierda **todos** sus blancos, y sanea los dos códigos al leerlos. La
huella del veredicto —la que decide si una decisión humana **sigue contando**—
normaliza también el código de obra y el número de incidencia, con **otra**
función (`aprobacion.py::_normalizar`). Si las dos se tocaran, este cambio
habría movido las huellas ya escritas y **habría revocado en silencio
decisiones que tomaron personas de verdad** sobre partes que nadie ha vuelto a
mirar. Eso es exactamente lo que el alcance de la feature prohíbe (R17, D1).

**Sin red, sin base de datos, sin IA y sin reloj**: todo lo que se prueba aquí
son funciones puras sobre datos inventados.

## Por qué existe este fichero si ya está el centinela de F-028

`test_f028_huella_intacta.py` sigue vivo, sin tocar ni un aserto, y sus siete
huellas se ejecutan en cada suite. Pero mide **las formas de F-028**: el
espacio que **flanquea** al separador —`RS26.09 / 0149`, `06 - 77`—, que es lo
que aquella feature aprendió a limpiar.

Las formas que toca F-032 son otras y **ninguna de las siete las cubre**: el
espacio **dentro de un tramo**, lejos de la barra (`RS 26.09/0178`, el caso
real del 2026-09-17) y el espacio dentro del código de obra (`06 26`). Apoyarse
en el centinela ajeno sería dar por medido lo que nadie midió: de ahí R19, y de
ahí este fichero. Los dos se leen juntos y vigilan lo mismo por casos
distintos.

Lo que **no** se duplica aquí es el control de acoplamiento de F-028 (R51)
—que `aprobacion.py` no importa `nombrado` ni nombra sus piezas—: sigue en su
fichero, se ejecuta en la misma suite y R21 lo da por cubierto sin copiarlo.

## De dónde salen los literales, para que se puedan auditar

No son una foto de lo que devuelve el código de hoy. Se midieron en T1
—`progress/impl_F-032.md`—, sobre el commit `fd4fc70` y con el árbol limpio,
**antes de editar una sola línea** de `normalizar_codigo`. Esa es la diferencia
entre una medición y una foto: una huella comparada consigo misma no prueba
absolutamente nada, y un test así pasaría igual de verde si el cambio hubiera
movido las huellas de todo el sistema.

Y hay un segundo cerrojo que no depende de aquella medición:
`test_f032_r19_la_huella_canonica_se_recalcula_a_mano` reconstruye las tres
cadenas canónicas con `hashlib` a pelo, sin importar ni una constante de
`aprobacion.py`, y salen los mismos tres literales. O sea que el literal es
correcto por dos caminos independientes.

## Lo que hay que ver en el control 2, y es lo contraintuitivo

`_normalizar("RS 26.09/0178")` vale **`rs 26.09/0178`**, con el espacio dentro,
y **eso es lo correcto**. La huella no identifica nada fuera: compara **dos
lecturas del mismo papel**. `normalizar_codigo` sí identifica algo fuera —una
reclamación en un ERP que busca por igualdad exacta y una carpeta de
SharePoint—, y por eso es la que tenía que cambiar. Son dos trabajos distintos
en dos funciones distintas, y que sigan distintas es lo que sostiene todo lo
demás de este fichero.
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime

import pytest
from domain.models.aprobacion import _normalizar, huella_de_veredicto
from domain.models.estado import (
    DecisionEstado,
    EstadoParte,
    decision_en_firme,
    estado_del_parte,
)
from domain.models.firma import ClasificacionFirma
from domain.models.nombrado import normalizar_codigo
from domain.models.validacion import (
    CodigoMotivo,
    Destino,
    Motivo,
    ResultadoValidacion,
    Veredicto,
)

AHORA = datetime(2026, 9, 17, 12, 0, tzinfo=UTC)
HASH = "hash-inventado-del-parte-f032"

#: El `oid` **opaco** de quien decidió. Inventado y sin forma de GUID:
#: `test_f006_repo_sin_identificadores.py` prohíbe que entre una cadena con
#: forma de identificador, aunque sea inventada, porque quien la lea no puede
#: distinguirla de una de verdad.
OID = "oid-opaco-inventado-para-este-test"

#: El número de incidencia **real del 2026-09-17**, tal y como lo leyó la IA.
#:
#: Va literal a propósito: es la forma que costó un `ReclamacionNoLocalizada` y
#: un rescate a mano, y un caso real que nadie escribe se vuelve a perder. Un
#: código no identifica a ninguna persona.
NUMERO_LEIDO = "RS 26.09/0178"

#: El mismo número, canónico.
NUMERO_LIMPIO = "RS26.09/0178"

#: El código de obra leído con el espacio dentro, y el mismo ya canónico.
OBRA_LEIDA = "06 26"
OBRA_LIMPIA = "0626"

#: Las observaciones del caso no apto. **Inventadas**: son las mismas que usa
#: `test_f028_huella_intacta.py`, para que los dos ficheros se lean juntos.
OBSERVACIONES = "Se aprecian parcheados. No se reparo la totalidad."

#: Lo que separa los campos de la cadena canónica de la huella.
#:
#: Se escribe aquí y **no se importa** de `aprobacion.py`: el test que recalcula
#: la huella a mano tiene que ser una segunda opinión, y una segunda opinión que
#: reutiliza las constantes de la primera ya no lo es.
SALTO = "\n"

MOTIVO_OBS = Motivo(
    codigo=CodigoMotivo.OBSERVACIONES_MANUSCRITAS,
    texto="El cliente ha escrito algo en observaciones.",
)


def _veredicto(**campos) -> ResultadoValidacion:
    """Un `ResultadoValidacion` **montado a mano**, y es deliberado.

    Igual que en el centinela de F-028, y por su mismo motivo: lo que se mide
    aquí es que un valor **no** ha cambiado, con las esperadas escritas
    literales. Si el veredicto lo compusiera `validar_parte`, un cambio suyo en
    el reparto movería los tres literales y este fichero se pondría rojo
    anunciando que se han revocado decisiones **sin que sea verdad**. Un
    control negativo que grita en falso acaba borrado.

    Los seis campos que entran en la huella se escriben enteros; el resto son
    relleno.
    """
    base = {
        "hash_parte": "9f2b0011aabb",
        "veredicto": Veredicto.APTO,
        "destino": Destino.ARCHIVO_Y_CIERRE,
        "motivos": (),
        "clasificacion_firma": ClasificacionFirma.HUMANA,
        "observaciones": None,
        "confianza_observaciones": 0,
        "codigo_obra": OBRA_LIMPIA,
        "numero_incidencia": NUMERO_LIMPIO,
    }
    base.update(campos)
    return ResultadoValidacion(**base)


#: El veredicto (a): apto, con el **número** leído con el espacio dentro.
VEREDICTO_A = _veredicto(numero_incidencia=NUMERO_LEIDO)

#: El veredicto (b): apto, con la **obra** leída con el espacio dentro.
VEREDICTO_B = _veredicto(codigo_obra=OBRA_LEIDA)

#: El veredicto (c): **no apto**, en la cola por observaciones manuscritas, con
#: el número leído con el espacio dentro. Es el que tiene una decisión humana
#: detrás en el control 3, porque es el que una persona mira de verdad.
VEREDICTO_C = _veredicto(
    veredicto=Veredicto.NO_APTO,
    destino=Destino.COLA_VALIDACION_HUMANA,
    motivos=(MOTIVO_OBS,),
    observaciones=OBSERVACIONES,
    confianza_observaciones=88,
    numero_incidencia=NUMERO_LEIDO,
)

#: Las tres huellas **medidas en T1**, antes de tocar `normalizar_codigo`.
#: Commit `fd4fc700b7692e74018546565833396759137626`, árbol limpio. La traza de
#: aquella ejecución está en `progress/impl_F-032.md`.
HUELLA_A = "49ab7cc6aae5026b98a27208c78c5199a6c962b57d4006c150752121fb7c508a"
HUELLA_B = "3aa32ce8733a127291fb9c7d9b09854f893dfaeec5bb927d3020536af3e0b626"
HUELLA_C = "4fb437b10fd5635172f29bb1127aa5f23859fc492b68397d46c6eba819b66652"

#: Los tres casos del control, con su huella medida al lado y las seis piezas
#: de su cadena canónica escritas a mano para el segundo camino.
#:
#: Los seis campos van **con su nombre delante** y no como una tupla suelta: si
#: mañana alguien añade un campo a la cadena o le cambia el orden, el fallo dice
#: cuál en vez de enseñar solo un hexadecimal distinto.
CASOS: tuple[tuple[str, ResultadoValidacion, str, dict[str, str]], ...] = (
    (
        "a · apto, con el número leído «RS 26.09/0178»",
        VEREDICTO_A,
        HUELLA_A,
        {
            "destino": "archivo_y_cierre",
            "motivos_ordenados": "",
            "clasificacion_firma": "humana",
            "observaciones": "",
            "codigo_obra": "0626",
            "numero_incidencia": "rs 26.09/0178",
        },
    ),
    (
        "b · apto, con la obra leída «06 26»",
        VEREDICTO_B,
        HUELLA_B,
        {
            "destino": "archivo_y_cierre",
            "motivos_ordenados": "",
            "clasificacion_firma": "humana",
            "observaciones": "",
            "codigo_obra": "06 26",
            "numero_incidencia": "rs26.09/0178",
        },
    ),
    (
        "c · no apto, en cola por observaciones, número «RS 26.09/0178»",
        VEREDICTO_C,
        HUELLA_C,
        {
            "destino": "cola_validacion_humana",
            "motivos_ordenados": "observaciones_manuscritas",
            "clasificacion_firma": "humana",
            "observaciones": "se aprecian parcheados. no se reparo la totalidad.",
            "codigo_obra": "0626",
            "numero_incidencia": "rs 26.09/0178",
        },
    ),
)


# --------------------------------------------------------------------------
# Control 1 · R19 · el valor de la huella no se ha movido
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("titulo", "validacion", "esperada", "canonica"),
    CASOS,
    ids=[caso[0] for caso in CASOS],
)
def test_f032_r19_la_huella_sigue_valiendo_lo_que_valia(
    titulo: str,
    validacion: ResultadoValidacion,
    esperada: str,
    canonica: dict[str, str],
):
    """R19 · la huella de cada veredicto vale **exactamente** lo de antes.

    Las tres esperadas se midieron en T1, sobre el árbol anterior al cambio, y
    están escritas aquí literales. Si alguna se mueve, la decisión humana que se
    tomó sobre ese veredicto deja de contar sola —sin que nadie lo haya
    decidido y sin que nadie se entere—: el parte vuelve a `pendiente` y el
    trabajo de revisión se ha perdido.
    """
    assert huella_de_veredicto(validacion) == esperada, (
        f"la huella de «{titulo}» ha cambiado: hay decisiones humanas vigentes "
        "que dejan de contar"
    )


# --------------------------------------------------------------------------
# Control 2 · R19 · el mismo valor por un segundo camino independiente
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("titulo", "validacion", "esperada", "canonica"),
    CASOS,
    ids=[caso[0] for caso in CASOS],
)
def test_f032_r19_la_huella_canonica_se_recalcula_a_mano(
    titulo: str,
    validacion: ResultadoValidacion,
    esperada: str,
    canonica: dict[str, str],
):
    """R19 · el literal es correcto **por un segundo camino independiente**.

    El control de arriba compara contra una medición; este compara contra la
    definición. Se reconstruye la cadena canónica de `huella_de_veredicto`
    —destino, motivos ordenados, clasificación de la firma, observaciones,
    código de obra y número, separados por saltos de línea y en minúsculas— y se
    le pasa `hashlib` a pelo, sin importar ni una constante de `aprobacion.py`.

    Sirve para dos cosas: confirma que el literal no es la foto de un código que
    ya estuviera mal, y **fija el formato**. Si mañana alguien añade un campo a
    la cadena o le cambia el orden, este test lo dice con todas las letras.
    """
    a_mano = hashlib.sha256(SALTO.join(canonica.values()).encode("utf-8")).hexdigest()

    assert a_mano == esperada, f"la cadena canónica de «{titulo}» ya no es esa"
    assert a_mano == huella_de_veredicto(validacion)


def test_f032_r17_la_huella_conserva_el_espacio_de_dentro_del_tramo():
    """R17 · `_normalizar` **no** ha seguido a `normalizar_codigo`, y está bien.

    Es lo contraintuitivo del cambio, y por eso va escrito con todas las letras:
    después de F-032, `_normalizar("RS 26.09/0178")` sigue valiendo
    `rs 26.09/0178`, **con el espacio dentro**. No es un olvido.

    Las dos funciones preparan un código para trabajos distintos:

    - `normalizar_codigo` lo prepara para **identificar algo fuera**: la
      reclamación que el ERP busca por igualdad exacta y la carpeta de
      SharePoint donde acaba un PDF con el DNI manuscrito de un cliente. Ahí un
      espacio de más es un cierre muerto, y por eso desaparece;
    - `_normalizar` lo prepara para **comparar dos lecturas del mismo papel**.
      Es deliberadamente tonta —recorta, colapsa y baja a minúsculas—, porque lo
      único que no puede hacer es cambiar de valor cuando se toque el nombrado.

    Alinearlas cambiaría todas las huellas escritas y revocaría decisiones
    vivas. Eso es una feature con migración, no un arreglo de paso (D1).
    """
    assert _normalizar(NUMERO_LEIDO) == "rs 26.09/0178"
    assert _normalizar(OBRA_LEIDA) == "06 26"

    assert normalizar_codigo(NUMERO_LEIDO) == NUMERO_LIMPIO
    assert normalizar_codigo(OBRA_LEIDA) == OBRA_LIMPIA

    assert _normalizar(NUMERO_LEIDO) != normalizar_codigo(NUMERO_LEIDO)
    assert _normalizar(OBRA_LEIDA) != normalizar_codigo(OBRA_LEIDA)


# --------------------------------------------------------------------------
# Control 3 · R20 · el efecto: la decisión de una persona sigue en pie
# --------------------------------------------------------------------------


def _aprobacion(huella: str) -> DecisionEstado:
    """La fila del histórico que dejó una persona al aprobar un parte.

    La huella se le pasa **escrita**, como vendría de la base: es una decisión
    tomada **antes** del cambio, y lo que hay que comprobar es que el cambio no
    la ha invalidado.
    """
    return DecisionEstado(
        hash_parte=HASH,
        estado=EstadoParte.APROBADO,
        decidido_at_utc=AHORA,
        estado_anterior=EstadoParte.PENDIENTE,
        decidido_por=OID,
        motivo="Los parcheados son de otra incidencia ya cerrada.",
        huella_veredicto=huella,
    )


def test_f032_r20_un_parte_no_apto_aprobado_antes_del_cambio_sigue_aprobado():
    """R20 · el control del **efecto**, que es el que le importa a Posventa.

    El caso exacto del riesgo: un parte cuyo número se leyó `RS 26.09/0178`
    —con el espacio dentro del tramo, la forma que esta feature toca— fue a la
    cola por observaciones manuscritas, alguien lo miró, decidió que valía y su
    decisión quedó guardada con la huella de aquel veredicto. Después llega
    F-032.

    El parte tiene que seguir `aprobado`. Si volviera a `pendiente`, ese trabajo
    de revisión se habría perdido sin que nadie lo decidiera, y el parte se
    quedaría fuera del circuito hasta que alguien volviera a mirarlo.
    """
    estado = estado_del_parte(VEREDICTO_C, _aprobacion(HUELLA_C), None)

    assert estado is EstadoParte.APROBADO


def test_f032_r20_y_la_pantalla_sigue_diciendo_que_lo_aprobo_una_persona():
    """R20, F-028 R43 · no basta con el estado: la autoría también sigue.

    `decision_en_firme` es lo que distingue en pantalla «aprobado por una
    persona · <fecha>» de «lo dio por bueno la máquina». Sin este caso, un
    cambio que moviera la huella de un parte **apto** pasaría de largo por el
    test anterior: seguiría `aprobado`, pero por la máquina, y la pantalla
    dejaría de decir que alguien lo miró.
    """
    decision = _aprobacion(HUELLA_C)

    en_firme = decision_en_firme(VEREDICTO_C, decision, None)

    assert en_firme is decision
    assert en_firme.por_persona


def test_f032_r20_tambien_sigue_en_pie_el_parte_cuya_obra_se_leyo_con_espacio():
    """R20 · el segundo caso propio, por el otro campo.

    El de arriba va por el número de incidencia, que es el que decide **sobre
    qué reclamación se escribe el cierre**. Este va por el código de obra, que
    decide **en qué carpeta se archiva el PDF**. Los dos entran en la huella
    desde la enmienda H-1 de F-026, y los dos los toca esta feature, así que los
    dos necesitan su medición del efecto.
    """
    assert estado_del_parte(VEREDICTO_B, _aprobacion(HUELLA_B), None) is (
        EstadoParte.APROBADO
    )
    assert decision_en_firme(VEREDICTO_B, _aprobacion(HUELLA_B), None) is not None
