# services/postventa-api/tests/test_f032_saneo_en_la_extraccion.py
"""Los dos códigos nacen limpios, y **solo** ellos (F-032, R11–R16).

El bloque 1 de esta feature arregló las tres **salidas**: el código que se le
manda al ERP, el nombre del fichero y la carpeta de archivo. Con eso, un código
leído con un espacio de más ya no rompe el cierre ni manda el PDF a una carpeta
equivocada. Lo que sigue roto sin este fichero es la **entrada**: lo que se
escribe en `postventa.partes` todavía nace con el espacio que leyó el modelo, y
por eso el 2026-09-17 hubo que **editar un parte a mano** —`RS 26.09/0178`—
antes de que el circuito lo dejara pasar.

Este fichero fija la otra mitad: que lo que se guarda no lleve espacios, **sin
que nadie tenga que editar nada**.

## Por qué se prueban dos caminos y no uno

`design.md` §4 mide por dónde llega de verdad el valor a la base, que no es por
donde parece:

```
/api/extraer  →  paso_extraccion  →  ExtraccionParte  →  JSON al front
                                                            |
   (el front lo enseña, la persona puede corregirlo, y lo devuelve)
                                                            v
/api/parte · /api/validar · /api/estado  →  cuerpos.a_extraccion
                                                            |
                                       paso_persistencia → upsert_parte
```

`paso_extraccion` **no persiste nada**: su resultado viaja al front y vuelve en
el cuerpo. Quien construye el `ExtraccionParte` que acaba en la tabla es
`cuerpos.a_extraccion`. De ahí que hagan falta los dos sitios: sanear solo en el
pipeline dejaría la base sucia en cuanto una persona corrigiera un campo, y
sanear solo en el cuerpo dejaría al front enseñando un código que no es el que
se va a usar. Los dos caminos tienen su test aquí, y el de R13 los recorre
enteros de borde a borde.

## La mitad que más importa: lo que **no** se toca

Un saneo que se pasara de listo estropearía el dato que una persona lee para
decidir. Por eso la regla vive en el dominio y conoce **dos** campos, no
nueve: `codigo_obra` y `numero_incidencia`. Los otros siete se copian tal cual,
y el caso que lo demuestra es una **observación manuscrita con espacios dobles
y saltos de línea**, que tiene que salir letra por letra igual que entró. Un
código identifica una reclamación en un ERP que busca por igualdad exacta; una
observación es prosa de una persona, y quitarle los espacios la convierte en
otra cosa.

**Dobles en memoria**: sin red, sin base de datos y sin IA. La guarda de
`tests/conftest.py` hace lo primero imposible, no improbable.

**Ni un dato personal.** El DNI `00000000T` no es un número emitido, las
observaciones y la promoción están escritas para este fichero, y los códigos
—`06 26`, `0626`, `RS 26.09/0178`— no identifican a nadie.
"""

from __future__ import annotations

import json
import uuid
from typing import Any

import azure.functions as func
import pytest
from application.pipelines.contexto_parte import ContextoParte
from application.pipelines.paso_extraccion import paso_extraccion
from domain.models.extraccion import CAMPOS_DEL_PARTE, ExtraccionParte
from domain.models.nombrado import normalizar_codigo
from domain.models.remesa import ModoDeteccion, ParteTroceado
from infrastructure.persistencia import sentencias
from interface_adapters.api.cuerpos import (
    CLAVES_DE_LA_EXTRACCION,
    a_extraccion,
    bloque,
)

from tests.utiles_ia import prompt_de_prueba, respuesta_simulada
from tests.utiles_pg import RepositorioEnMemoria

# --------------------------------------------------------------------------
# El material: los dos códigos sucios y los siete textos que no se tocan
# --------------------------------------------------------------------------

#: El código de obra **tal y como lo leyó el modelo**, con el espacio dentro.
#: Es la forma que mandaba el PDF a `Postventa/06 26`, que no existe.
OBRA_LEIDA = "06 26"

#: El mismo código de obra, ya limpio: lo que tiene que acabar en la tabla.
OBRA_LIMPIA = "0626"

#: El número de incidencia **real del 2026-09-17**, escrito literal.
#:
#: Va literal a propósito: un caso real que nadie escribe se vuelve a perder, y
#: este costó un `ReclamacionNoLocalizada` y un rescate a mano.
NUMERO_LEIDO = "RS 26.09/0178"

#: El mismo número, ya limpio.
NUMERO_LIMPIO = "RS26.09/0178"

HASH = "9f2b0011aabb"

#: Generado en ejecución: `test_f006_repo_sin_identificadores.py` prohíbe que
#: entre en el repositorio una cadena con forma de GUID, aunque sea inventada.
REMESA_ID = str(uuid.uuid4())

TRAZA = {
    "proveedor": "gemini",
    "modelo": "modelo-inventado",
    "prompt_key": "parte_posventa_es",
    "version_prompt": "1",
    "huella_prompt": "0a1b2c3d4e5f",
}


#: Los siete campos que **no** son un código y se copian tal cual (R14).
CAMPOS_DE_TEXTO: tuple[str, ...] = (
    "promocion",
    "unidad",
    "fecha_servicio",
    "descripcion",
    "dni_cliente",
    "observaciones",
    "numero_pagina",
)

#: Una transcripción **inventada** de unas observaciones manuscritas.
#:
#: Lleva a propósito lo que un saneo mal dirigido destrozaría: **espacios
#: dobles** y **saltos de línea**. Es el caso que separa «sanear un código» de
#: «tocar el texto del cliente», y las observaciones son justo lo que lee una
#: persona para decidir si un parte vale.
OBSERVACIONES_INVENTADAS = (
    "Se aprecian  parcheados en el techo del porche.\n"
    "Falta rematar el rodapie  del salon.\n"
    "Pendiente  segunda visita."
)

#: Una promoción **inventada**, con dos espacios que también son legítimos.
PROMOCION_INVENTADA = "15  VIVIENDAS UNIFAMILIARES EN MIRASIERRA (inventada)"

#: DNI **inventado**: `00000000T` no es un número emitido.
DNI_INVENTADO = "00000000T"

#: Los siete textos de ejemplo, con sus espacios legítimos dentro.
TEXTOS_DE_EJEMPLO: dict[str, str] = {
    "promocion": PROMOCION_INVENTADA,
    "unidad": "Viviendas  Bloque Villa 5",
    "fecha_servicio": "05/08/26",
    "descripcion": "Sellado de encuentro  de falsos techos de porches",
    "dni_cliente": DNI_INVENTADO,
    "observaciones": OBSERVACIONES_INVENTADAS,
    "numero_pagina": "1",
}

#: Las formas del número que el bloque 1 dejó equivalentes, para comprobar que
#: la regla del saneo **es** la del nombrado y no una copia con su propia vida.
FORMAS_EQUIVALENTES: tuple[str, ...] = (
    "RS26.09/0178",
    "RS 26.09/0178",
    "RS26.09 / 0178",
    "RS26.09 - 0178",
    "RS\t26.09/0178",
    "  RS 26.09/0178  ",
)


# --------------------------------------------------------------------------
# La regla del dominio, importada **dentro** de cada test a propósito
# --------------------------------------------------------------------------


def _regla_del_dominio():
    """`sanear_valor_leido`, importada aquí dentro y no en la cabecera.

    No es descuido. En la **fase RED** de T6 esta función todavía no existe
    (la escribe T7), y un `import` en la cabecera tumbaría el fichero entero
    en la recogida: los doce tests de comportamiento —que son los que de
    verdad demuestran el defecto— no llegarían a ejecutarse y el rojo no
    diría nada. Con el import aquí, cada test falla por su propio motivo.
    """
    from domain.models.extraccion import sanear_valor_leido

    return sanear_valor_leido


def _campos_de_codigo() -> tuple[str, ...]:
    """`CAMPOS_DE_CODIGO`, importada dentro por el mismo motivo que la regla."""
    from domain.models.extraccion import CAMPOS_DE_CODIGO

    return CAMPOS_DE_CODIGO


# --------------------------------------------------------------------------
# El camino del pipeline: `paso_extraccion`
# --------------------------------------------------------------------------


class PromptsFalsos:
    """Doble de `RepositorioPromptsPort`: siempre el mismo prompt de mentira."""

    def __init__(self) -> None:
        self.prompt = prompt_de_prueba()

    def obtener(self, clave: str):
        return self.prompt


class ExtractorQueDevuelveLoQueSeLeDice:
    """Doble de `ExtractorPort`. Ni red, ni SDK, ni prompt de verdad."""

    def __init__(self, respuesta) -> None:
        self.respuesta = respuesta

    def extraer(self, *, documento: bytes, mime: str, prompt):
        return self.respuesta


def _parte() -> ParteTroceado:
    """Un parte troceado de mentira, con la forma que produce F-002."""
    return ParteTroceado(
        hash=HASH,
        origen="remesa-inventada.pdf",
        paginas_origen=(3,),
        modo_deteccion=ModoDeteccion.UNA_PAGINA_POR_PARTE,
        contenido=b"%PDF-1.4 parte de prueba",
    )


#: Marca para decirle a `_extraer` que el modelo **no devolvió** ese campo.
_AUSENTE = object()


def _extraer(**campos: Any) -> ContextoParte:
    """Ejecuta el paso de extracción con lo que el modelo haya «leído»."""
    leido = {**TEXTOS_DE_EJEMPLO, "codigo_obra": OBRA_LEIDA}
    leido["numero_incidencia"] = NUMERO_LEIDO
    leido.update(campos)
    omitir = tuple(nombre for nombre, valor in leido.items() if valor is _AUSENTE)
    for nombre in omitir:
        leido.pop(nombre)
    return paso_extraccion(
        ContextoParte(parte=_parte()),
        ExtractorQueDevuelveLoQueSeLeDice(
            respuesta_simulada(omitir=omitir, **leido)
        ),
        PromptsFalsos(),
        "parte_posventa_es",
    )


# --------------------------------------------------------------------------
# El camino del cuerpo HTTP: `cuerpos.a_extraccion`
# --------------------------------------------------------------------------

def _bloque_extraccion(**cambios: Any) -> dict[str, Any]:
    """El bloque `extraccion` tal y como lo devuelve `POST /api/extraer`."""
    valores = {
        **TEXTOS_DE_EJEMPLO,
        "codigo_obra": OBRA_LEIDA,
        "numero_incidencia": NUMERO_LEIDO,
    }
    valores.update(cambios)
    return {
        "hash_parte": HASH,
        "campos": {
            nombre: {"valor": valores[nombre], "confianza_pct": 90}
            for nombre in CAMPOS_DEL_PARTE
        },
        "traza": TRAZA,
        "avisos": [],
    }


def _desde_el_cuerpo(**cambios: Any) -> ExtraccionParte:
    """Lo que `cuerpos.a_extraccion` reconstruye a partir de ese bloque."""
    return a_extraccion(
        bloque(
            {"extraccion": _bloque_extraccion(**cambios)},
            "extraccion",
            CLAVES_DE_LA_EXTRACCION,
        )
    )


# --------------------------------------------------------------------------
# R14 · la regla del dominio conoce dos campos, no nueve
# --------------------------------------------------------------------------


def test_f032_r14_la_regla_del_dominio_solo_conoce_los_dos_codigos():
    """R14 · `CAMPOS_DE_CODIGO` son exactamente dos, y son los que son.

    Escritos literales y no derivados de nada: el día que alguien añada aquí
    `observaciones` «para que quede más limpio», este test tiene que ser lo
    que se ponga rojo. Y los dos tienen que ser campos del contrato de F-003,
    porque sanear una clave que no existe no saneaba nada.
    """
    campos_de_codigo = _campos_de_codigo()

    assert campos_de_codigo == ("codigo_obra", "numero_incidencia")
    assert all(nombre in CAMPOS_DEL_PARTE for nombre in campos_de_codigo)
    assert set(CAMPOS_DEL_PARTE) - set(campos_de_codigo) == set(CAMPOS_DE_TEXTO)


def test_f032_r11_la_regla_del_dominio_no_es_una_copia_de_normalizar_codigo():
    """R11 · el saneo **es** `normalizar_codigo`, no algo que se le parece.

    Dos criterios del mismo concepto divergen siempre, y a este proyecto ya le
    pasó: F-028 dejó dos ideas distintas de «espacio sobrante» y el
    2026-09-17 se cobró un cierre. Aquí se comprueba de dos formas
    independientes: que es **el mismo objeto función** —o sea, que
    `extraccion.py` la importa en vez de reescribirla— y que todas las formas
    equivalentes del número dan el mismo valor saneado.
    """
    from domain.models import extraccion as modulo_extraccion

    sanear_valor_leido = _regla_del_dominio()

    assert modulo_extraccion.normalizar_codigo is normalizar_codigo
    saneados = {
        sanear_valor_leido("numero_incidencia", forma) for forma in FORMAS_EQUIVALENTES
    }
    assert saneados == {NUMERO_LIMPIO}


@pytest.mark.parametrize("nombre", CAMPOS_DE_TEXTO)
def test_f032_r14_la_regla_del_dominio_copia_un_texto_letra_por_letra(nombre):
    """R14 · los siete campos de texto salen **idénticos**, sin excepción.

    El caso que importa es `observaciones`: espacios dobles y saltos de línea
    dentro. Si el saneo llegara ahí, la transcripción de lo que escribió una
    persona a mano quedaría convertida en otra cosa, y es exactamente el texto
    que otra persona lee para decidir si el parte vale.
    """
    sanear_valor_leido = _regla_del_dominio()
    texto = TEXTOS_DE_EJEMPLO[nombre]

    assert sanear_valor_leido(nombre, texto) == texto


def test_f032_r16_la_regla_del_dominio_deja_en_none_lo_que_llega_en_none():
    """R16 · un campo que el modelo no leyó no se convierte en uno leído.

    Para los nueve, códigos incluidos: `None` es «no consta», y devolver `""`
    lo convertiría en «el papel estaba en blanco», que es otra afirmación.
    """
    sanear_valor_leido = _regla_del_dominio()

    assert all(sanear_valor_leido(nombre, None) is None for nombre in CAMPOS_DEL_PARTE)


@pytest.mark.parametrize("blancos", ["   ", "\t", "\n", " \t\n "])
def test_f032_r16_la_regla_del_dominio_deja_un_codigo_de_solo_blancos_sin_leer(
    blancos,
):
    """R16 · un código que se queda vacío tras el saneo sale **no leído**.

    `None` y no `""`: un valor de solo blancos no dice nada que un `NULL` no
    diga, F-004 ya trata «solo espacios» como vacío y la huella del veredicto
    normaliza los dos al mismo sitio, así que esto **no mueve ninguna huella**.
    """
    sanear_valor_leido = _regla_del_dominio()

    assert sanear_valor_leido("codigo_obra", blancos) is None
    assert sanear_valor_leido("numero_incidencia", blancos) is None


def test_f032_r14_la_regla_del_dominio_no_vacia_un_texto_de_solo_blancos():
    """R14 · y al revés: un **texto** de solo blancos sale tal cual.

    La equivalencia «solo espacios es vacío» es de los códigos, que van a
    identificar algo. Un texto se copia sin juzgarlo, y quien decide que un
    campo está vacío es `CampoExtraido.esta_vacio`, que ya existía.
    """
    sanear_valor_leido = _regla_del_dominio()

    assert sanear_valor_leido("observaciones", "   ") == "   "


# --------------------------------------------------------------------------
# R11 · el camino del pipeline
# --------------------------------------------------------------------------


def test_f032_r11_la_extraccion_sanea_los_dos_codigos():
    """R11 · lo que sale de `paso_extraccion` ya viaja sin espacios.

    Es lo que ve el front y lo que la persona devuelve en el cuerpo: si aquí
    saliera sucio, la pantalla estaría enseñando un código que no es el que se
    va a usar para buscar la reclamación.
    """
    contexto = _extraer()

    assert contexto.extraccion.campo("codigo_obra").valor == OBRA_LIMPIA
    assert contexto.extraccion.campo("numero_incidencia").valor == NUMERO_LIMPIO


def test_f032_r14_el_pipeline_no_toca_los_otros_siete_campos():
    """R14 · los siete textos salen del paso **letra por letra** como entraron.

    Incluida la observación manuscrita con sus espacios dobles y sus saltos de
    línea. Este es el test que separa «sanear un código» de «tocar el texto
    del cliente».
    """
    contexto = _extraer()

    salidos = {
        nombre: contexto.extraccion.campo(nombre).valor for nombre in CAMPOS_DE_TEXTO
    }
    assert salidos == TEXTOS_DE_EJEMPLO
    assert salidos["observaciones"] == OBSERVACIONES_INVENTADAS


def test_f032_r11_el_pipeline_conserva_la_confianza_de_lo_que_sanea():
    """R11 · sanear el valor no toca la confianza con la que se leyó.

    Son dos cosas distintas: qué pone y cómo de seguro estaba el modelo de lo
    que ponía. Bajar la confianza porque el valor se haya limpiado sería
    inventarse una duda que nadie tuvo.
    """
    contexto = _extraer()

    assert contexto.extraccion.campo("codigo_obra").confianza_pct == 90
    assert contexto.extraccion.campo("numero_incidencia").confianza_pct == 90


# --------------------------------------------------------------------------
# R15 · el saneo no es silencioso
# --------------------------------------------------------------------------


def test_f032_r15_el_saneo_deja_aviso():
    """R15 · si el valor cambia, queda dicho **qué se leyó y qué se guardó**.

    Sin esto, el saneo taparía una lectura mala del modelo sin que nadie se
    entere: quien mire el parte vería un código correcto y no sabría que no es
    letra por letra el del papel. Los avisos ya se persisten
    (`partes.avisos_extraccion`) y ya se enseñan, así que no hace falta ningún
    mecanismo nuevo. Y no llevan dato personal: los dos códigos ya viven en
    claro en sus propias columnas.
    """
    contexto = _extraer()

    avisos = contexto.extraccion.avisos
    del_codigo = [aviso for aviso in avisos if aviso.startswith("codigo_obra:")]
    del_numero = [aviso for aviso in avisos if aviso.startswith("numero_incidencia:")]

    assert len(del_codigo) == 1
    assert OBRA_LEIDA in del_codigo[0] and OBRA_LIMPIA in del_codigo[0]
    assert len(del_numero) == 1
    assert NUMERO_LEIDO in del_numero[0] and NUMERO_LIMPIO in del_numero[0]
    #: Y llega también al contexto, que es de donde los recoge la respuesta.
    assert contexto.avisos == list(avisos)


def test_f032_r15_sin_cambio_no_hay_aviso():
    """R15 · un código que ya venía limpio **no** deja aviso.

    Si lo dejara, el aviso perdería todo su valor: avisar siempre es no avisar.
    """
    contexto = _extraer(codigo_obra=OBRA_LIMPIA, numero_incidencia=NUMERO_LIMPIO)

    assert not any("se ha guardado sin" in aviso for aviso in contexto.extraccion.avisos)


def test_f032_r15_los_siete_textos_no_generan_aviso_de_saneo():
    """R15 · ningún texto produce aviso de saneo, porque ninguno se sanea."""
    contexto = _extraer()

    for nombre in CAMPOS_DE_TEXTO:
        assert not any(
            aviso.startswith(f"{nombre}:") and "se ha guardado sin" in aviso
            for aviso in contexto.extraccion.avisos
        )


# --------------------------------------------------------------------------
# R16 · ausente sigue ausente, por el camino del pipeline
# --------------------------------------------------------------------------


def test_f032_r16_ausente_sigue_ausente():
    """R16 · un campo que el modelo no devolvió sigue sin valor tras el saneo.

    Y conserva su aviso de siempre —«el modelo no devolvió el campo»—, que es
    lo que distingue «el papel no lo traía» de «nadie lo miró».
    """
    contexto = _extraer(codigo_obra=_AUSENTE)

    campo = contexto.extraccion.campo("codigo_obra")

    assert campo.valor is None
    assert campo.confianza_pct == 0
    assert "codigo_obra: el modelo no devolvió el campo" in contexto.extraccion.avisos


def test_f032_r16_un_codigo_de_solo_blancos_llega_como_no_leido():
    """R16 · el modelo lee solo espacios y se guarda como **no leído**.

    Un `NULL` dice lo mismo que una cadena de espacios y no engaña a nadie que
    después consulte la tabla buscando partes sin código.
    """
    contexto = _extraer(codigo_obra="   ")

    assert contexto.extraccion.campo("codigo_obra").valor is None
    assert contexto.extraccion.campo("codigo_obra").esta_vacio is True


# --------------------------------------------------------------------------
# R12 · el camino del cuerpo HTTP (el que llega de verdad a la tabla)
# --------------------------------------------------------------------------


def test_f032_r12_el_cuerpo_http_sanea_los_dos_codigos():
    """R12 · el mismo saneo en `cuerpos.a_extraccion`.

    Es la puerta de `/api/parte`, `/api/validar` y `/api/estado`, y por tanto
    **la única** por la que el valor llega a `postventa.partes`. Sanear solo en
    el pipeline dejaría la base sucia en cuanto una persona corrigiera un
    campo en la pantalla, que es justo lo que pasó el 2026-09-17.
    """
    extraccion = _desde_el_cuerpo()

    assert extraccion.campo("codigo_obra").valor == OBRA_LIMPIA
    assert extraccion.campo("numero_incidencia").valor == NUMERO_LIMPIO


def test_f032_r14_el_cuerpo_http_no_toca_los_otros_siete_campos():
    """R14 · y por este camino tampoco se toca ningún texto.

    La misma regla en los dos sitios porque es **la misma función del
    dominio**: si aquí se sanearan ocho campos y allí dos, el valor guardado
    dependería de por qué endpoint entró.
    """
    extraccion = _desde_el_cuerpo()

    salidos = {nombre: extraccion.campo(nombre).valor for nombre in CAMPOS_DE_TEXTO}

    assert salidos == TEXTOS_DE_EJEMPLO
    assert salidos["observaciones"] == OBSERVACIONES_INVENTADAS


def test_f032_r15_el_cuerpo_http_no_fabrica_avisos():
    """R15 · el borde sanea **sin** emitir aviso, y es deliberado.

    `a_extraccion` construye la extracción con `avisos=()` por contrato: los
    avisos son de la **lectura**, no del transporte (F-019). Fabricarlos aquí
    los duplicaría en cada revalidación del mismo parte —y un parte se
    revalida cada vez que alguien corrige un campo—.
    """
    extraccion = _desde_el_cuerpo()

    assert extraccion.avisos == ()


def test_f032_r16_el_cuerpo_http_deja_ausente_lo_que_llega_ausente():
    """R16 · `None` sigue `None`, y un código de solo blancos sale no leído."""
    extraccion = _desde_el_cuerpo(codigo_obra=None, numero_incidencia="  \t ")

    assert extraccion.campo("codigo_obra").valor is None
    assert extraccion.campo("numero_incidencia").valor is None


# --------------------------------------------------------------------------
# R13 · de borde a borde: lo que acaba en `postventa.partes`
# --------------------------------------------------------------------------


class RepositorioQueEscribeComoLaBase(RepositorioEnMemoria):
    """El doble de siempre, que además **compone el SQL** de `upsert_parte`.

    Es lo que permite comprobar R13 sin base de datos: lo que se afirma no es
    un objeto en memoria, sino los **parámetros** que viajarían a la columna
    `partes.codigo_obra`. `RepositorioEnMemoria` guarda el objeto que se le
    dio, y eso, para esto, es ciego: el valor podría estar limpio en el objeto
    y sucio en la columna sin que el test se enterara.

    No es una base de datos: no valida tipos, no aplica `CHECK` y no abre
    ningún socket. Que el SQL sea PostgreSQL válido sigue siendo trabajo de
    `tests_bbdd/`.
    """

    #: El esquema es irrelevante para lo que aquí se mide; va explícito para
    #: no depender de la configuración del entorno.
    ESQUEMA = "postventa"

    def __init__(self) -> None:
        super().__init__()
        #: Las parejas `(sql, parametros)` de cada `upsert_parte`, en orden.
        self.sentencias_de_parte: list[tuple[str, tuple]] = []

    def guardar_parte(self, *, parte, extraccion, remesa_id, ahora):
        self.sentencias_de_parte.append(
            sentencias.upsert_parte(
                esquema=self.ESQUEMA,
                parte=parte,
                extraccion=extraccion,
                remesa_id=remesa_id,
                ahora=ahora,
            )
        )
        return super().guardar_parte(
            parte=parte, extraccion=extraccion, remesa_id=remesa_id, ahora=ahora
        )


def _fila_que_iria_a_la_tabla(sql: str, parametros: tuple) -> dict[str, Any]:
    """Empareja cada columna del `INSERT` con el parámetro que le toca.

    Las columnas se leen **del propio SQL** y no de una constante privada de
    `sentencias.py`: así el test no se ata a un orden que no es su asunto, y
    si alguien añadiera una columna sin su parámetro, `strict=True` lo diría.
    """
    columnas = sql.split("(", 1)[1].split(")", 1)[0].split(", ")
    return dict(zip(columnas, parametros, strict=True))


def _cuerpo_de_parte() -> dict[str, Any]:
    """El cuerpo completo de `POST /api/parte`, con los dos códigos sucios."""
    return {
        "remesa_id": REMESA_ID,
        "parte": {
            "hash": HASH,
            "origen": "remesa-inventada.pdf",
            "paginas_origen": [3],
            "modo_deteccion": "una_pagina_por_parte",
        },
        "extraccion": _bloque_extraccion(),
        "firma": {
            "hash_parte": HASH,
            "firma": {"clasificacion": "humana", "confianza_pct": 93},
            "traza": {**TRAZA, "prompt_key": "firma_parte_es"},
            "avisos": [],
        },
    }


def _responder(monkeypatch, repositorio, cuerpo: Any) -> func.HttpResponse:
    """Llama al handler de verdad con el repositorio inyectado por la costura."""
    import function_app
    from interface_adapters.api.parte import guardar_parte_http

    def envoltura(cuerpo_recibido, **datos):
        return guardar_parte_http(cuerpo_recibido, repositorio=repositorio, **datos)

    monkeypatch.setattr(function_app, "guardar_parte_http", envoltura)
    return function_app.parte(
        func.HttpRequest(
            method="POST",
            url="/api/parte",
            headers={"Content-Type": "application/json"},
            body=json.dumps(cuerpo, ensure_ascii=False).encode("utf-8"),
        )
    )


def test_f032_r13_lo_que_se_guarda_no_lleva_espacios(monkeypatch):
    """R13 · el criterio de aceptación entero, de borde a borde y con dobles.

    Un cuerpo de `POST /api/parte` cuyo `codigo_obra` sea `06 26` y cuyo
    `numero_incidencia` sea `RS 26.09/0178` —el caso real del 2026-09-17—
    tiene que acabar llamando a `sentencias.upsert_parte` con `0626` y
    `RS26.09/0178`. **Sin que nadie edite el parte a mano**, que es lo que hubo
    que hacer aquel día y lo único que esta feature viene a evitar.

    Recorre el camino completo: handler HTTP → `cuerpos.a_extraccion` →
    `paso_persistencia` → `upsert_parte`. Sin base de datos: se afirma sobre
    los parámetros de la sentencia, que es lo que viajaría a las columnas.
    """
    repositorio = RepositorioQueEscribeComoLaBase()

    respuesta = _responder(monkeypatch, repositorio, _cuerpo_de_parte())

    assert respuesta.status_code == 200
    assert len(repositorio.sentencias_de_parte) == 1
    sql, parametros = repositorio.sentencias_de_parte[0]
    fila = _fila_que_iria_a_la_tabla(sql, parametros)

    assert fila["codigo_obra"] == OBRA_LIMPIA
    assert fila["numero_incidencia"] == NUMERO_LIMPIO


def test_f032_r14_lo_que_se_guarda_conserva_el_texto_manuscrito(monkeypatch):
    """R14 · por ese mismo camino, la observación manuscrita llega intacta.

    Va aquí y no solo en el dominio porque es donde se puede perder de verdad:
    entre el cuerpo HTTP y la columna hay tres funciones, y lo que se guarda en
    `partes.observaciones` es lo que después lee una persona para decidir.
    """
    repositorio = RepositorioQueEscribeComoLaBase()

    _responder(monkeypatch, repositorio, _cuerpo_de_parte())

    sql, parametros = repositorio.sentencias_de_parte[0]
    fila = _fila_que_iria_a_la_tabla(sql, parametros)

    assert fila["observaciones"] == OBSERVACIONES_INVENTADAS
    assert fila["promocion"] == PROMOCION_INVENTADA
