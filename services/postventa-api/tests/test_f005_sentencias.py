# services/postventa-api/tests/test_f005_sentencias.py
"""El SQL de cada operación (F-005, T14): R14, R17, R22, R25.

Dos familias de comprobación, y las dos importan:

- **Que el SQL diga lo que tiene que decir**: `ON CONFLICT` donde toca, la
  fecha de primera vez sin pisar, el contador de reprocesos, el `WHERE` que
  protege un cierre terminal, y el `JOIN` que evita duplicar la transcripción.
- **Que ningún valor se interpole en el texto**. Es lo que separa un
  parámetro de una inyección, y aquí hay texto manuscrito de clientes.

Todo el material es inventado.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from domain.models.errores import DdlInseguro
from domain.models.firma import ClasificacionFirma
from domain.models.persistencia import (
    EstadoArchivo,
    EstadoCierre,
    PreferenciasUsuario,
    RegistroRemesa,
    TrazaArchivo,
    TrazaCierre,
    nuevo_id,
)
from domain.models.remesa import ModoDeteccion, ParteTroceado
from domain.models.validacion import validar_parte

from infrastructure.persistencia.sentencias import (
    LIMITE_MAXIMO_COLA,
    select_cola,
    select_preferencias,
    upsert_archivo,
    upsert_cierre,
    upsert_parte,
    upsert_preferencias,
    upsert_remesa,
    upsert_validacion,
)
from tests.utiles_validacion import extraccion_de_ejemplo, lectura_de_firma

ESQUEMA = "postventa"
AHORA_INVENTADO = datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC)

#: Un parte troceado inventado. Sus «bytes» son un texto reconocible: si
#: acabaran en el SQL o en los parámetros, el test lo vería.
CONTENIDO_INVENTADO = b"%PDF-inventado-que-no-debe-guardarse"


def _parte() -> ParteTroceado:
    return ParteTroceado(
        hash="hash-inventado-0001",
        origen="remesa_inventada.pdf",
        paginas_origen=(3, 4),
        modo_deteccion=ModoDeteccion.POR_PIE_DE_PAGINA,
        contenido=CONTENIDO_INVENTADO,
    )


# --- partes: reprocesar actualiza, no duplica (R14, R15) --------------------


def test_f005_r14_el_parte_se_guarda_con_on_conflict_por_hash():
    """R14 · la deduplicación la hace la clave primaria, no el código."""
    sql, _ = upsert_parte(
        esquema=ESQUEMA,
        parte=_parte(),
        extraccion=extraccion_de_ejemplo(),
        remesa_id=nuevo_id(),
        ahora=AHORA_INVENTADO,
    )

    assert "INSERT INTO postventa.partes" in sql
    assert "ON CONFLICT (hash_parte) DO UPDATE SET" in sql


def test_f005_r15_al_reprocesar_no_se_pisa_la_fecha_de_primera_vez():
    """R15 · saber que un parte se subió tres veces desde marzo es el dato.

    `primera_vez_at_utc` **no** puede estar en el `DO UPDATE SET`: si
    estuviera, cada reproceso borraría cuándo llegó por primera vez.
    """
    sql, _ = upsert_parte(
        esquema=ESQUEMA,
        parte=_parte(),
        extraccion=extraccion_de_ejemplo(),
        remesa_id=nuevo_id(),
        ahora=AHORA_INVENTADO,
    )

    asignaciones = sql.split("ON CONFLICT")[1]

    assert "primera_vez_at_utc = EXCLUDED" not in asignaciones
    assert "actualizado_at_utc = EXCLUDED.actualizado_at_utc" in asignaciones
    assert "reprocesos = postventa.partes.reprocesos + 1" in asignaciones


def test_f005_r12_los_bytes_del_pdf_no_entran_en_la_base():
    """R12, R40 · el PDF con el DNI manuscrito vive en SharePoint.

    Ni en el texto del SQL ni entre los parámetros: si el contenido apareciera,
    estaríamos escribiendo un documento con datos personales en el disco
    compartido de otros tres proyectos.
    """
    sql, parametros = upsert_parte(
        esquema=ESQUEMA,
        parte=_parte(),
        extraccion=extraccion_de_ejemplo(),
        remesa_id=nuevo_id(),
        ahora=AHORA_INVENTADO,
    )

    assert CONTENIDO_INVENTADO not in sql.encode("utf-8")
    assert CONTENIDO_INVENTADO not in parametros
    assert not any(isinstance(valor, bytes | bytearray) for valor in parametros)


def test_f005_r18_hay_un_marcador_por_columna_y_ningun_valor_pegado():
    """Ningún valor se interpola: tantos `%s` como columnas, y nada más.

    Los valores del parte son texto leído de un papel escrito a mano por un
    cliente. Pegarlos al SQL sería una inyección con su nombre y su DNI dentro.
    """
    extraccion = extraccion_de_ejemplo(
        observaciones="'; DROP TABLE postventa.partes; --"
    )

    sql, parametros = upsert_parte(
        esquema=ESQUEMA,
        parte=_parte(),
        extraccion=extraccion,
        remesa_id=nuevo_id(),
        ahora=AHORA_INVENTADO,
    )
    linea_valores = [
        linea for linea in sql.splitlines() if linea.startswith("VALUES (")
    ][0]

    assert "DROP TABLE" not in sql
    assert "'; DROP TABLE postventa.partes; --" in parametros
    assert linea_valores.count("%s") == len(parametros)


def test_f005_r18_el_unico_marcador_con_cast_a_jsonb_es_el_de_los_avisos():
    """El `::jsonb` va en `avisos_extraccion`, y en ninguna otra columna.

    Contar `%s` no basta y buscar `"%s::jsonb" in sql` tampoco: las dos
    comprobaciones siguen pasando si el cast se le pone a **todas** las
    columnas menos a la que lo necesita, que es justo lo que sobrevivió a la
    campaña de mutación de T23. Aquí se emparejan la lista de columnas y la de
    marcadores y se mira cuál lleva el cast: `avisos_extraccion` recibe un
    texto JSON y Postgres necesita que se lo digan, mientras que ponérselo a
    una columna `text` o `timestamptz` reventaría el `INSERT` en la primera
    escritura real, ya en el entorno desplegado.
    """
    sql, parametros = upsert_parte(
        esquema=ESQUEMA,
        parte=_parte(),
        extraccion=extraccion_de_ejemplo(),
        remesa_id=nuevo_id(),
        ahora=AHORA_INVENTADO,
    )

    columnas = [
        columna.strip()
        for columna in sql.split("INSERT INTO postventa.partes (")[1]
        .split(")")[0]
        .split(",")
    ]
    linea_valores = next(
        linea for linea in sql.splitlines() if linea.startswith("VALUES (")
    )
    marcadores = [
        marcador.strip()
        for marcador in linea_valores.removeprefix("VALUES (")
        .removesuffix(")")
        .split(",")
    ]

    assert len(columnas) == len(marcadores) == len(parametros)

    con_cast = [
        columna
        for columna, marcador in zip(columnas, marcadores, strict=True)
        if marcador == "%s::jsonb"
    ]

    assert con_cast == ["avisos_extraccion"]
    assert marcadores.count("%s::jsonb") == 1
    assert set(marcadores) == {"%s", "%s::jsonb"}


def test_f005_r19_la_traza_de_ia_esta_entre_las_columnas():
    """R19 · quién leyó el parte se guarda con el parte."""
    sql, _ = upsert_parte(
        esquema=ESQUEMA,
        parte=_parte(),
        extraccion=extraccion_de_ejemplo(),
        remesa_id=nuevo_id(),
        ahora=AHORA_INVENTADO,
    )

    for columna in (
        "ia_proveedor",
        "ia_modelo",
        "prompt_key",
        "prompt_version",
        "prompt_huella",
    ):
        assert columna in sql


def test_f005_r14_el_upsert_dice_si_creo_o_actualizo():
    """`(xmax = 0)` distingue insertado de actualizado sin otra consulta."""
    sql, _ = upsert_parte(
        esquema=ESQUEMA,
        parte=_parte(),
        extraccion=extraccion_de_ejemplo(),
        remesa_id=nuevo_id(),
        ahora=AHORA_INVENTADO,
    )

    assert sql.rstrip().endswith("RETURNING (xmax = 0) AS creado")


# --- validaciones: sustituir, no acumular (R17) -----------------------------


def test_f005_r17_la_validacion_sustituye_y_no_acumula():
    """R17 · revalidar un parte no puede dejar dos veredictos."""
    resultado = validar_parte(
        extraccion_de_ejemplo(), lectura_de_firma(ClasificacionFirma.HUMANA)
    )

    sql, _ = upsert_validacion(
        esquema=ESQUEMA, resultado=resultado, ahora=AHORA_INVENTADO
    )

    assert "INSERT INTO postventa.validaciones" in sql
    assert "ON CONFLICT (hash_parte) DO UPDATE SET" in sql
    assert "veredicto = EXCLUDED.veredicto" in sql
    assert "destino = EXCLUDED.destino" in sql


def test_f005_r21_la_validacion_no_escribe_la_columna_de_observaciones():
    """R21, R39 · aquí no hay columna de observaciones, y no debe haberla."""
    resultado = validar_parte(
        extraccion_de_ejemplo(observaciones="texto manuscrito inventado"),
        lectura_de_firma(ClasificacionFirma.HUMANA),
    )

    sql, parametros = upsert_validacion(
        esquema=ESQUEMA, resultado=resultado, ahora=AHORA_INVENTADO
    )

    assert "observaciones" not in sql
    assert not any("texto manuscrito inventado" in str(valor) for valor in parametros)


# --- cierres: un cierre terminal no se pisa (R25, R26) ----------------------


def test_f005_r25_un_cierre_terminal_no_se_pisa():
    """R25 · el `WHERE` del `DO UPDATE` protege una escritura real en el ERP.

    Y `'cerrado'` viaja como **parámetro**, no pegado al texto: es un valor.
    """
    traza = TrazaCierre(
        hash_parte="hash-inventado-0001",
        numero_incidencia="XX00.00 - 0000",
        estado=EstadoCierre.CERRADO,
        cerrado_at_utc=AHORA_INVENTADO,
    )

    sql, parametros = upsert_cierre(esquema=ESQUEMA, traza=traza)

    assert "WHERE postventa.cierres.estado <> %s" in sql
    assert parametros[-1] == "cerrado"
    assert "'cerrado'" not in sql


def test_f005_r26_un_cierre_fallido_acumula_intentos_y_guarda_el_motivo():
    """R26 · cinco cierres fallidos se ven en la fila, no en un log."""
    traza = TrazaCierre(
        hash_parte="hash-inventado-0001",
        numero_incidencia="XX00.00 - 0000",
        estado=EstadoCierre.ERROR,
        motivo="motivo inventado del fallo",
    )

    sql, parametros = upsert_cierre(esquema=ESQUEMA, traza=traza)

    assert "intentos = postventa.cierres.intentos + 1" in sql
    assert "motivo = EXCLUDED.motivo" in sql
    assert "motivo inventado del fallo" in parametros


# --- archivos (R23) ---------------------------------------------------------


def test_f005_r23_el_archivo_deja_una_sola_fila_por_parte():
    """R23 · subir dos veces el mismo parte no genera un duplicado."""
    traza = TrazaArchivo(
        hash_parte="hash-inventado-0001",
        estado=EstadoArchivo.ARCHIVADO,
        nombre_fichero="0000 - XX00.00 - 0000 PARTE FIRMADO.pdf",
        item_id="item-inventado",
    )

    sql, parametros = upsert_archivo(esquema=ESQUEMA, traza=traza)

    assert "INSERT INTO postventa.archivos" in sql
    assert "ON CONFLICT (hash_parte) DO UPDATE SET" in sql
    assert "intentos = postventa.archivos.intentos + 1" in sql
    assert "item-inventado" in parametros


# --- la cola (R22) ----------------------------------------------------------


def test_f005_r22_la_cola_solo_trae_los_de_validacion_humana():
    """R22 · un parte al que le faltan los mínimos va a revisión, no a la cola.

    Meterlo aquí haría que alguien decidiera sobre una reparación que el
    cliente ni siquiera dio por recibida.
    """
    sql, parametros = select_cola(esquema=ESQUEMA, limite=50)

    assert "WHERE v.destino = %s" in sql
    assert parametros[0] == "cola_validacion_humana"
    assert "'cola_validacion_humana'" not in sql


def test_f005_r21_la_cola_trae_las_observaciones_con_un_join_a_partes():
    """R21, R39 · la transcripción se recupera, no se copia."""
    sql, _ = select_cola(esquema=ESQUEMA, limite=50)

    assert "JOIN postventa.partes AS p ON p.hash_parte = v.hash_parte" in sql
    assert "p.observaciones" in sql
    assert "p.observaciones_confianza_pct" in sql


def test_f005_r22_la_cola_sale_en_orden_de_llegada():
    """El que lleva más tiempo esperando se atiende primero."""
    sql, _ = select_cola(esquema=ESQUEMA, limite=50)

    assert "ORDER BY v.validado_at_utc ASC" in sql


def test_f005_r22_el_limite_de_la_cola_esta_acotado():
    """Un `Standard_B1ms` compartido no puede servir una lectura sin techo."""
    _, muchos = select_cola(esquema=ESQUEMA, limite=1_000_000)
    _, ninguno = select_cola(esquema=ESQUEMA, limite=0)
    _, negativo = select_cola(esquema=ESQUEMA, limite=-5)

    assert muchos[1] == LIMITE_MAXIMO_COLA
    assert LIMITE_MAXIMO_COLA == 500
    assert ninguno[1] == 1
    assert negativo[1] == 1


# --- remesas y preferencias -------------------------------------------------


def test_f005_r13_la_remesa_se_actualiza_por_su_id():
    """Volver a guardar la misma remesa la actualiza."""
    remesa = RegistroRemesa(
        id=nuevo_id(),
        nombre_origen="remesa_inventada.pdf",
        recibida_at_utc=AHORA_INVENTADO,
        num_partes=22,
        avisos=("aviso inventado",),
    )

    sql, parametros = upsert_remesa(esquema=ESQUEMA, remesa=remesa)

    assert "INSERT INTO postventa.remesas" in sql
    assert "ON CONFLICT (id) DO UPDATE SET" in sql
    assert "%s::jsonb" in sql
    assert '["aviso inventado"]' in parametros


def test_f005_r27_las_preferencias_dejan_una_fila_por_usuario():
    """R27 · la clave es el `oid` opaco de Entra ID, y no hay dos filas."""
    preferencias = PreferenciasUsuario(
        usuario_oid="oid-inventado-0000",
        auto_cierre=True,
        actualizado_at_utc=AHORA_INVENTADO,
    )

    sql, parametros = upsert_preferencias(esquema=ESQUEMA, preferencias=preferencias)

    assert "INSERT INTO postventa.preferencias_usuario" in sql
    assert "ON CONFLICT (usuario_oid) DO UPDATE SET" in sql
    assert "auto_cierre = EXCLUDED.auto_cierre" in sql
    assert parametros == ("oid-inventado-0000", True, AHORA_INVENTADO)


def test_f005_r27_la_consulta_de_preferencias_va_por_oid():
    """Se busca por `oid`, nunca por correo ni por nombre."""
    sql, parametros = select_preferencias(
        esquema=ESQUEMA, usuario_oid="oid-inventado-0000"
    )

    assert "WHERE usuario_oid = %s" in sql
    assert parametros == ("oid-inventado-0000",)
    assert "correo" not in sql
    assert "email" not in sql


# --- el esquema (R5, R8) ----------------------------------------------------


def test_f005_r8_todas_las_sentencias_van_cualificadas_con_el_esquema():
    """Nada sin cualificar: con `search_path` acotado, además, no arrancaría."""
    sql, _ = select_cola(esquema="otro_inventado", limite=10)

    assert "otro_inventado.validaciones" in sql
    assert "otro_inventado.partes" in sql
    assert "postventa." not in sql


def test_f005_r5_un_esquema_hostil_no_llega_al_sql():
    """El nombre del esquema es lo único que se pega al texto: se valida."""
    with pytest.raises(DdlInseguro):
        select_cola(esquema="postventa; DROP SCHEMA public", limite=10)

    with pytest.raises(DdlInseguro):
        upsert_preferencias(
            esquema="",
            preferencias=PreferenciasUsuario(
                usuario_oid="oid-inventado-0000",
                auto_cierre=False,
                actualizado_at_utc=AHORA_INVENTADO,
            ),
        )
