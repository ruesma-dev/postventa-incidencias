# services/postventa-api/tests/test_f006_paso_archivo.py
"""El paso de archivo: dónde vive **toda** la decisión de F-006 (R10–R18, R23, R24, R27).

El puerto solo tiene tres operaciones mecánicas —asegurar carpeta, buscar,
subir— y ninguna decide nada. Quien decide es este paso, que es código puro y
se prueba entero con dobles: sin red, sin token, sin biblioteca y sin subir
absolutamente nada.

Eso no es una comodidad de test: es lo que permite que la campaña de mutación
tenga superficie que morder donde importa. Si la decisión viviera dentro del
adaptador de Graph, no se podría cubrir ni mutar sin abrir una conexión, y la
regla dura de `CLAUDE.md` prohíbe abrirla.

**Ni un dato real.** Los códigos `0677` y `RS26.08/0123` son inventados y
salen del material de F-003; los bytes del «PDF» son `b"%PDF-1.4 de mentira"`.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime

import pytest
from application.pipelines.paso_archivo import (
    AVISO_REEMPLAZADO,
    AVISO_YA_ARCHIVADO,
    MIME_PDF,
    paso_archivo,
)
from domain.models.errores import ArchivoFallido, NombradoImposible, ParteNoApto
from domain.models.persistencia import EstadoArchivo, TrazaArchivo
from domain.models.validacion import Destino, Veredicto

from tests.utiles_sharepoint import (
    CARPETA_BASE,
    DRIVE_FALSO,
    RENOMBRAR,
    ArchivoPortFalso,
    BibliotecaFalsa,
    RepositorioFalso,
    contexto_apto,
    contexto_no_apto,
    preexistente,
)

#: Un instante fijo. El paso **no** consulta el reloj: la hora entra por
#: parámetro, que es lo que permite afirmar sobre la fecha de la traza.
AHORA = datetime(2026, 8, 20, 9, 30, tzinfo=UTC)

#: Lo que tiene que salir con el material de ejemplo. **Inventado.**
CARPETA_ESPERADA = "Postventa/0677"
NOMBRE_ESPERADO = "0677 - RS26.08 - 0123 PARTE FIRMADO.pdf"


def archivar(ctx, archivador, repositorio, **extra):
    """Atajo: el paso con la carpeta base y la hora de siempre."""
    return paso_archivo(
        ctx,
        archivador,
        repositorio,
        carpeta_base=CARPETA_BASE,
        ahora=AHORA,
        **extra,
    )


# --------------------------------------------------------------------------
# R10, R11, R12, R27 · La carpeta
# --------------------------------------------------------------------------


def test_f006_r10_la_carpeta_es_base_mas_codigo_de_obra():
    """R10 · `<carpeta base>/<código de obra>`, con los ceros dentro."""
    archivador, repositorio = ArchivoPortFalso(), RepositorioFalso()

    archivar(contexto_apto(), archivador, repositorio)

    assert repositorio.ultima_traza.carpeta == CARPETA_ESPERADA
    assert archivador.biblioteca.carpetas == {CARPETA_ESPERADA}


def test_f006_r11_la_carpeta_se_crea_si_no_existe():
    """R11 · la carpeta del código de obra se crea antes de subir el fichero.

    Y se comprueba también **el orden**: asegurar la carpeta va antes que
    subir. Al revés, la subida fallaría contra una carpeta inexistente.
    """
    archivador, repositorio = ArchivoPortFalso(), RepositorioFalso()

    assert archivador.biblioteca.creaciones_de_carpeta == 0

    archivar(contexto_apto(), archivador, repositorio)

    assert archivador.biblioteca.creaciones_de_carpeta == 1
    assert archivador.operaciones.index("asegurar_carpeta") < archivador.operaciones.index("subir")


def test_f006_r12_pedir_la_carpeta_dos_veces_deja_una_sola():
    """R12 · reprocesar el parte no crea una segunda carpeta de la misma obra.

    La biblioteca falsa cuenta **creaciones reales**, no llamadas: si el paso
    pidiera la carpeta dos veces y el adaptador no fuera idempotente, aquí
    saldría 2 y el archivo de Posventa acabaría con dos carpetas `0677`.
    """
    biblioteca = BibliotecaFalsa()
    repositorio = RepositorioFalso()

    archivar(contexto_apto(), ArchivoPortFalso(biblioteca), repositorio)
    archivar(contexto_apto(), ArchivoPortFalso(biblioteca), repositorio)

    assert biblioteca.creaciones_de_carpeta == 1
    assert biblioteca.carpetas == {CARPETA_ESPERADA}


def test_f006_r27_el_destino_sale_de_configuracion():
    """R27 · cambiar la carpeta base cambia el destino, sin tocar el paso.

    Es lo que hace que **F-013** —mudar el archivo a la biblioteca de
    Posventa— sea cambiar variables de entorno y no reescribir código.
    """
    archivador, repositorio = ArchivoPortFalso(), RepositorioFalso()

    paso_archivo(
        contexto_apto(),
        archivador,
        repositorio,
        carpeta_base="OtraBiblioteca/Posventa",
        ahora=AHORA,
    )

    assert repositorio.ultima_traza.carpeta == "OtraBiblioteca/Posventa/0677"


# --------------------------------------------------------------------------
# R13, R14 · La identidad del parte y la capa barata de idempotencia
# --------------------------------------------------------------------------


def test_f006_r13_la_identidad_del_parte_es_el_hash_de_f002():
    """R13 · «el mismo parte» es el mismo `hash`, y ningún criterio propio.

    Una traza archivada de **otro** parte no puede cortar este: dos escaneos
    distintos de la misma incidencia son dos partes, y F-006 no define un
    criterio de deduplicación por nombre, ni por incidencia, ni por bytes.
    """
    archivador, repositorio = ArchivoPortFalso(), RepositorioFalso()
    de_otro_parte = TrazaArchivo(
        hash_parte="hash-de-otro-parte",
        estado=EstadoArchivo.ARCHIVADO,
        nombre_fichero=NOMBRE_ESPERADO,
        carpeta=CARPETA_ESPERADA,
    )

    ctx = archivar(
        contexto_apto(), archivador, repositorio, traza_previa=de_otro_parte
    )

    assert "subir" in archivador.operaciones
    assert ctx.archivo.hash_parte == contexto_apto().parte.hash


def test_f006_r14_con_traza_archivada_no_se_vuelve_a_subir():
    """R14 · si ya consta archivado, no se llama al proveedor. En absoluto.

    Es la capa barata: ni token, ni red, ni bytes por el cable. El doble
    **no recibe ni una llamada**, y el resultado trae el aviso que lo dice.
    """
    archivador, repositorio = ArchivoPortFalso(), RepositorioFalso()
    ctx_entrada = contexto_apto()
    ya_archivada = TrazaArchivo(
        hash_parte=ctx_entrada.parte.hash,
        estado=EstadoArchivo.ARCHIVADO,
        nombre_fichero=NOMBRE_ESPERADO,
        carpeta=CARPETA_ESPERADA,
        drive_id=DRIVE_FALSO,
        item_id="item-0001",
    )

    ctx = archivar(ctx_entrada, archivador, repositorio, traza_previa=ya_archivada)

    assert archivador.llamadas == []
    assert archivador.biblioteca.subidas == 0
    assert ctx.archivo is ya_archivada
    assert AVISO_YA_ARCHIVADO in ctx.avisos


@pytest.mark.parametrize(
    "estado", (EstadoArchivo.PENDIENTE, EstadoArchivo.ERROR)
)
def test_f006_r14_una_traza_que_no_es_archivado_no_corta(estado):
    """R14 · solo `archivado` corta. `pendiente` y `error` dejan reintentar.

    Es lo que hace verdad a R24: un fallo anterior no puede dejar el parte
    atascado para siempre.
    """
    archivador, repositorio = ArchivoPortFalso(), RepositorioFalso()
    ctx_entrada = contexto_apto()
    previa = TrazaArchivo(hash_parte=ctx_entrada.parte.hash, estado=estado)

    ctx = archivar(ctx_entrada, archivador, repositorio, traza_previa=previa)

    assert archivador.biblioteca.subidas == 1
    assert ctx.archivo.estado == EstadoArchivo.ARCHIVADO


# --------------------------------------------------------------------------
# R15 · El test que más importa de la feature
# --------------------------------------------------------------------------


def test_f006_r15_subir_dos_veces_deja_un_solo_elemento():
    """R15 · el `acceptance` 3, escrito como comportamiento observable.

    Se archiva **dos veces el mismo parte**, sin traza previa, para que la
    capa barata (R14) no tape lo que aquí se comprueba: que la propia subida
    reemplaza en vez de renombrar.

    Al final, la biblioteca tiene **exactamente un** elemento y **ningún**
    nombre con `(1)`. Si alguien cambiara el comportamiento de conflicto a
    «renombrar», este test caería por lo que de verdad pasaría en producción,
    no por una aserción sobre una cadena.
    """
    biblioteca = BibliotecaFalsa()
    repositorio = RepositorioFalso()

    archivar(contexto_apto(), ArchivoPortFalso(biblioteca), repositorio)
    archivar(contexto_apto(), ArchivoPortFalso(biblioteca), repositorio)

    assert len(biblioteca.elementos) == 1
    assert biblioteca.nombres == [NOMBRE_ESPERADO]
    assert not any("(1)" in nombre for nombre in biblioteca.nombres)


def test_f006_r15_reemplazar_conserva_el_mismo_item_id():
    """R15 · para el servicio real es **el mismo elemento**, con otra versión.

    Es lo que la verificación manual T18 comprueba contra la biblioteca de
    verdad: la segunda llamada devuelve el mismo `item_id`.
    """
    biblioteca = BibliotecaFalsa()
    repositorio = RepositorioFalso()

    primera = archivar(contexto_apto(), ArchivoPortFalso(biblioteca), repositorio)
    segunda = archivar(contexto_apto(), ArchivoPortFalso(biblioteca), repositorio)

    assert primera.archivo.item_id == segunda.archivo.item_id


def test_f006_r15_nunca_se_pide_renombrar():
    """R15 · renombrar **no es expresable** desde este paso.

    El puerto no tiene ningún parámetro de comportamiento ante conflicto: la
    decisión está cerrada dentro del adaptador, y el paso no puede pedir un
    `(1).pdf` ni por error ni a propósito. Se comprueba sobre la firma real
    del puerto, que es el sitio donde esa puerta se abriría.
    """
    import inspect

    from domain.ports.archivo import ArchivoPort

    firma = inspect.signature(ArchivoPort.subir)

    assert set(firma.parameters) == {"self", "carpeta", "nombre", "contenido", "mime"}


def test_f006_r15_la_biblioteca_falsa_si_renombraria_el_control_negativo():
    """R15 · **control negativo**: la falsa sabe duplicar cuando se le pide.

    Sin este test, `test_f006_r15_subir_dos_veces_deja_un_solo_elemento`
    podría estar dando verde porque el doble **no sabe** producir duplicados,
    no porque el paso los evite. Aquí se construye a propósito un adaptador
    mal hecho —el que renombra— y se comprueba que aparece el `(1)` que el
    `acceptance` prohíbe.
    """
    biblioteca = BibliotecaFalsa()
    repositorio = RepositorioFalso()

    archivar(
        contexto_apto(),
        ArchivoPortFalso(biblioteca, conflicto=RENOMBRAR),
        repositorio,
    )
    archivar(
        contexto_apto(),
        ArchivoPortFalso(biblioteca, conflicto=RENOMBRAR),
        repositorio,
    )

    assert len(biblioteca.elementos) == 2
    assert any("(1)" in nombre for nombre in biblioteca.nombres)


# --------------------------------------------------------------------------
# R16 · Mismo nombre, otro parte
# --------------------------------------------------------------------------


def test_f006_r16_mismo_nombre_otro_hash_reemplaza_con_aviso():
    """R16 · el archivo se queda con la última versión, y consta que hubo otra.

    Dos escaneos distintos de la misma incidencia producen el mismo nombre y
    `hash` distinto. Posventa tiene que quedarse con el último conformado, y
    quien revise tiene que poder enterarse de que había uno anterior: si se
    reemplaza en silencio, la versión anterior desaparece sin rastro.
    """
    biblioteca = BibliotecaFalsa()
    archivador = ArchivoPortFalso(biblioteca)
    repositorio = RepositorioFalso()
    preexistente(
        biblioteca,
        carpeta=CARPETA_ESPERADA,
        nombre=NOMBRE_ESPERADO,
        contenido=b"%PDF-1.4 el escaneo anterior",
    )

    ctx = archivar(
        contexto_apto(hash_parte="hash-del-segundo-escaneo"),
        archivador,
        repositorio,
    )

    assert AVISO_REEMPLAZADO in ctx.avisos
    assert len(biblioteca.elementos_de(CARPETA_ESPERADA)) == 1
    assert biblioteca.buscar(CARPETA_ESPERADA, NOMBRE_ESPERADO).contenido == (
        b"%PDF-1.4 de mentira"
    )


def test_f006_r16_sin_homonimo_no_se_avisa_de_ningun_reemplazo():
    """R16 · un aviso que sale siempre es un aviso que nadie lee.

    Con la carpeta vacía no hay nada que reemplazar y el aviso **no** aparece.
    """
    archivador, repositorio = ArchivoPortFalso(), RepositorioFalso()

    ctx = archivar(contexto_apto(), archivador, repositorio)

    assert AVISO_REEMPLAZADO not in ctx.avisos
    assert ctx.avisos == []


# --------------------------------------------------------------------------
# R17, R18 · Solo se archiva lo apto
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("caso", "campos", "destino_esperado"),
    (
        (
            "con observaciones manuscritas, va a la cola humana",
            {"observaciones": "Se aprecia que se han hecho parcheados"},
            Destino.COLA_VALIDACION_HUMANA,
        ),
        (
            "sin código de obra legible, va a revisión manual",
            {"codigo_obra": None},
            Destino.REVISION_MANUAL,
        ),
        (
            "sin nº de incidencia legible, va a revisión manual",
            {"numero_incidencia": None},
            Destino.REVISION_MANUAL,
        ),
    ),
)
def test_f006_r17_un_parte_no_apto_no_se_archiva(caso, campos, destino_esperado):
    """R17 · el destino de F-004 manda, y no se reinterpreta aquí.

    Archivar «por si acaso» un parte que F-004 mandó a la cola de validación
    humana es exactamente lo que prohíbe `CHECKPOINTS.md` C3: alguien tenía
    que decidir sobre él y ya no va a poder.
    """
    archivador, repositorio = ArchivoPortFalso(), RepositorioFalso()
    ctx = contexto_no_apto(**campos)

    assert ctx.validacion.destino == destino_esperado, caso

    with pytest.raises(ParteNoApto):
        archivar(ctx, archivador, repositorio)

    assert archivador.llamadas == []


def test_f006_r17_un_parte_no_apto_no_crea_carpeta():
    """R17 · ni la carpeta. La puerta de aptitud va **antes** de nombrar.

    Una carpeta vacía en el archivo de Posventa es basura que alguien tendrá
    que mirar, y encima sugiere que hubo un parte que nunca existió.
    """
    biblioteca = BibliotecaFalsa()
    archivador = ArchivoPortFalso(biblioteca)

    with pytest.raises(ParteNoApto):
        archivar(
            contexto_no_apto(observaciones="algo escrito a mano"),
            archivador,
            RepositorioFalso(),
        )

    assert biblioteca.carpetas == set()
    assert biblioteca.creaciones_de_carpeta == 0


def test_f006_r17_un_parte_no_apto_tampoco_deja_traza_de_archivo():
    """R17 · no se ha intentado archivar nada: no hay nada que registrar.

    Una traza de error diría que el archivo falló, y no falló: es que ni
    siquiera se intentó, porque el parte no está listo.
    """
    repositorio = RepositorioFalso()

    with pytest.raises(ParteNoApto):
        archivar(
            contexto_no_apto(observaciones="algo"), ArchivoPortFalso(), repositorio
        )

    assert repositorio.archivos == []


def test_f006_r17_un_veredicto_apto_con_otro_destino_tampoco_se_archiva():
    """R17 · las dos condiciones se exigen, y hace falta **cada una**.

    Lo destapó la campaña de mutación (T20): cambiar el `or` de la puerta por
    un `and` no rompía ningún test, porque todos los casos no aptos fallaban
    **las dos** condiciones a la vez. Un parte marcado `apto` pero con destino
    distinto de archivo y cierre habría pasado la puerta.

    Y no es un caso de laboratorio: es exactamente lo que llegaría por
    `POST /api/archivar` si alguien compusiera el cuerpo a mano con
    `veredicto=apto` y el destino de la cola de validación humana.
    """
    archivador = ArchivoPortFalso()
    ctx = contexto_apto()
    ctx.validacion = replace(
        ctx.validacion, destino=Destino.COLA_VALIDACION_HUMANA
    )

    assert ctx.validacion.veredicto == Veredicto.APTO

    with pytest.raises(ParteNoApto):
        archivar(ctx, archivador, RepositorioFalso())

    assert archivador.llamadas == []


def test_f006_r17_un_destino_de_archivo_con_veredicto_no_apto_tampoco():
    """R17 · y al revés, que es la otra mitad del mismo `and`.

    El destino correcto no rescata un veredicto negativo: los dos campos
    tienen que decir que sí.
    """
    archivador = ArchivoPortFalso()
    ctx = contexto_apto()
    ctx.validacion = replace(ctx.validacion, veredicto=Veredicto.NO_APTO)

    assert ctx.validacion.destino == Destino.ARCHIVO_Y_CIERRE

    with pytest.raises(ParteNoApto):
        archivar(ctx, archivador, RepositorioFalso())

    assert archivador.llamadas == []


def test_f006_r18_sin_validacion_no_se_archiva():
    """R18 · sin resultado de validación, `ParteNoApto`.

    No consta que este parte haya pasado la validación. Archivarlo sería dar
    por bueno un veredicto que nadie emitió.
    """
    archivador = ArchivoPortFalso()
    ctx = contexto_apto()
    ctx.validacion = None

    with pytest.raises(ParteNoApto) as fallo:
        archivar(ctx, archivador, RepositorioFalso())

    assert "valida" in fallo.value.motivo.lower()
    assert archivador.llamadas == []


def test_f006_r18_el_motivo_de_sin_validacion_es_distinto_al_de_no_apto():
    """R18 · «no hay veredicto» y «el veredicto dice que no» son dos cosas.

    Quien lo lea tiene que saber si el parte hay que revalidarlo o si hay que
    volver al papel.
    """
    with pytest.raises(ParteNoApto) as sin_veredicto:
        ctx = contexto_apto()
        ctx.validacion = None
        archivar(ctx, ArchivoPortFalso(), RepositorioFalso())
    with pytest.raises(ParteNoApto) as veredicto_negativo:
        archivar(
            contexto_no_apto(observaciones="algo"),
            ArchivoPortFalso(),
            RepositorioFalso(),
        )

    assert sin_veredicto.value.motivo != veredicto_negativo.value.motivo


def test_f006_r6_el_nombrado_imposible_no_sube_nada():
    """R6 · un parte apto al que no se le puede componer el nombre no sube.

    Caso imposible en el camino normal —F-004 no declara apto un parte sin
    códigos—, así que se fuerza con un código de obra que trae un carácter
    prohibido: legible para F-004, imposible de nombrar para F-006.

    El error sale **sin haber tocado el puerto**: ni carpeta, ni búsqueda, ni
    subida.
    """
    biblioteca = BibliotecaFalsa()
    archivador = ArchivoPortFalso(biblioteca)

    with pytest.raises(NombradoImposible):
        archivar(contexto_apto(codigo_obra="06|77"), archivador, RepositorioFalso())

    assert archivador.llamadas == []
    assert biblioteca.carpetas == set()


# --------------------------------------------------------------------------
# R23, R24 · La traza
# --------------------------------------------------------------------------


def test_f006_r23_la_traza_de_exito_lleva_todo_lo_declarado():
    """R23 · estado, nombre, carpeta, biblioteca, elemento, URL y fecha UTC.

    Los siete, comprobados uno a uno: una traza a la que le falte el
    `item_id` o la `web_url` no sirve para lo que existe —volver sobre el
    fichero meses después sin buscarlo a mano en la biblioteca—.
    """
    archivador, repositorio = ArchivoPortFalso(), RepositorioFalso()

    ctx = archivar(contexto_apto(), archivador, repositorio)
    traza = repositorio.ultima_traza

    assert traza is ctx.archivo
    assert traza.hash_parte == contexto_apto().parte.hash
    assert traza.estado == EstadoArchivo.ARCHIVADO
    assert traza.nombre_fichero == NOMBRE_ESPERADO
    assert traza.carpeta == CARPETA_ESPERADA
    assert traza.drive_id == DRIVE_FALSO
    assert traza.item_id == "item-0001"
    assert traza.web_url.startswith("https://")
    assert traza.archivado_at_utc == AHORA
    assert traza.motivo is None


def test_f006_r23_el_parte_se_sube_como_pdf_y_con_sus_propios_bytes():
    """R23 · lo que se sube es **el contenido del parte troceado** de F-002.

    Ni la remesa entera, ni un fichero recompuesto: los bytes del parte, tal
    y como los dejó F-002, con el MIME de un PDF.
    """
    archivador, repositorio = ArchivoPortFalso(), RepositorioFalso()

    archivar(
        contexto_apto(contenido=b"%PDF-1.4 estos bytes exactos"),
        archivador,
        repositorio,
    )
    subida = dict(archivador.llamadas[-1][1])

    assert subida["mime"] == MIME_PDF
    assert MIME_PDF == "application/pdf"
    assert archivador.biblioteca.buscar(CARPETA_ESPERADA, NOMBRE_ESPERADO).contenido == (
        b"%PDF-1.4 estos bytes exactos"
    )


def test_f006_r24_un_fallo_deja_traza_de_error_y_permite_reintentar():
    """R24 · el fallo se registra, el parte **no** queda como archivado, y se reintenta.

    Tres cosas en un solo recorrido, porque son la misma historia: si el
    estado quedara en `archivado`, R14 cortaría el reintento y el parte se
    perdería sin que nadie lo notara.
    """
    biblioteca = BibliotecaFalsa()
    repositorio = RepositorioFalso()
    roto = ArchivoPortFalso(
        biblioteca, fallo=ArchivoFallido("el proveedor no respondió")
    )

    with pytest.raises(ArchivoFallido):
        archivar(contexto_apto(), roto, repositorio)

    fallida = repositorio.ultima_traza
    assert fallida.estado == EstadoArchivo.ERROR
    assert fallida.estado != EstadoArchivo.ARCHIVADO
    assert fallida.motivo
    assert fallida.archivado_at_utc is None
    assert fallida.nombre_fichero == NOMBRE_ESPERADO
    assert fallida.carpeta == CARPETA_ESPERADA
    assert biblioteca.elementos == {}

    # Y el reintento, con la traza de error como previa, funciona.
    ctx = archivar(
        contexto_apto(),
        ArchivoPortFalso(biblioteca),
        repositorio,
        traza_previa=fallida,
    )

    assert ctx.archivo.estado == EstadoArchivo.ARCHIVADO
    assert len(biblioteca.elementos) == 1


def test_f006_r24_un_fallo_al_asegurar_la_carpeta_tambien_deja_traza():
    """R24 · el fallo puede ser de la carpeta, no solo de la subida.

    Si solo se registrara el fallo de `subir`, un permiso mal dado sobre la
    biblioteca dejaría el parte sin traza ninguna: ni archivado, ni fallido,
    ni en ningún sitio.
    """
    repositorio = RepositorioFalso()
    roto = ArchivoPortFalso(
        fallo_al_asegurar=ArchivoFallido("no se pudo crear la carpeta")
    )

    with pytest.raises(ArchivoFallido):
        archivar(contexto_apto(), roto, repositorio)

    assert repositorio.ultima_traza.estado == EstadoArchivo.ERROR


def test_f006_r24_el_motivo_del_fallo_no_lleva_los_bytes_del_parte():
    """R24 + R26 · el motivo va a un log que sobrevive al parte.

    Los bytes llevan el DNI manuscrito y las observaciones del cliente. En la
    traza va **qué** falló, nunca **qué había dentro**.
    """
    repositorio = RepositorioFalso()
    secreto = b"%PDF-1.4 con un DNI dentro"
    roto = ArchivoPortFalso(fallo=ArchivoFallido("tiempo de espera agotado"))

    with pytest.raises(ArchivoFallido):
        archivar(contexto_apto(contenido=secreto), roto, repositorio)

    motivo = repositorio.ultima_traza.motivo
    assert "DNI" not in motivo
    assert secreto.decode() not in motivo
