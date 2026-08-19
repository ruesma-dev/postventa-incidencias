# services/postventa-api/tests/test_f005_ddl_troceado.py
"""El troceador del DDL, en sus bordes (F-005, T23).

`ddl.sentencias` es un **escáner escrito a mano** sobre el texto de los `.sql`
que se van a aplicar contra un servidor compartido con la producción de
albaranes, partes y el datamart. Que corte por el `;` equivocado no es un
detalle de estilo: es aplicar **fragmentos sueltos** de DDL contra la base de
otros.

`test_f005_ddl_seguro.py` comprueba que el escáner acierta en el caso normal.
Este fichero comprueba sus **bordes**, que es donde la campaña de mutación
demostró que nadie miraba: comentarios pegados a la sentencia, comentarios
vacíos, comentarios sin cerrar, literales vacíos, comillas dobladas, cuerpos
`$$…$$` sin cerrar y sentencias pegadas sin separador.

Cada test de aquí fija el resultado **completo y exacto** del troceado, no un
`in`: la lección de la campaña es que una comprobación parcial deja pasar un
escáner que se come una letra, arrastra un `*/` o pierde el corte.

Todo el SQL es **inventado**: ninguna de estas sentencias se ha ejecutado
nunca contra nada.
"""

from __future__ import annotations

from infrastructure.persistencia.ddl import _fin_de_literal, sentencias

#: Una sentencia legítima corta, para usarla como testigo: si el escáner se
#: come una letra o pierde un corte, este texto deja de salir entero.
TESTIGO = "CREATE SCHEMA IF NOT EXISTS postventa"


# --- comentarios de bloque --------------------------------------------------


def test_f005_r1_un_comentario_de_bloque_al_principio_no_se_traga_el_ddl():
    """Un `.sql` que **empieza** por su cabecera `/* … */` conserva el DDL.

    Es la forma de todos los ficheros de `infrastructure/persistencia/sql/`:
    la explicación arriba y la sentencia debajo. Si el escáner buscara el
    cierre del comentario **antes** de donde empieza, no lo encontraría y se
    comería el fichero entero sin que nadie se enterase.
    """
    troceadas = sentencias(f"/* cabecera inventada */\n{TESTIGO}")

    assert troceadas == (TESTIGO,)


def test_f005_r1_un_comentario_de_bloque_vacio_no_desplaza_el_corte():
    """`/**/` cierra en el carácter siguiente a su apertura, no más allá."""
    troceadas = sentencias(f"/**/{TESTIGO}")

    assert troceadas == (TESTIGO,)


def test_f005_r1_un_comentario_pegado_a_la_sentencia_no_se_come_letras():
    """Sin espacio entre `*/` y el `CREATE`, la sentencia sale entera.

    Dos fallos distintos aparecen aquí y los dos son silenciosos: reanudar
    **un carácter después** del cierre deja `REATE SCHEMA…`, y reanudar
    **antes** del cierre arrastra el `*/` dentro del SQL. Ninguno de los dos
    se ve con un `assert "CREATE SCHEMA" in troceadas[0]`.
    """
    troceadas = sentencias(f"/* nota inventada */{TESTIGO}")

    assert troceadas == (TESTIGO,)
    assert "*/" not in troceadas[0]


def test_f005_r1_un_comentario_de_bloque_sin_cerrar_no_corta_por_su_punto_coma():
    """Un `/*` sin cerrar se come el resto, y **no** parte por el `;` de dentro.

    Es texto comentado: lo que hay ahí no es SQL, y trocearlo produciría
    fragmentos que nadie escribió. El fichero se queda sin sentencias, y sin
    sentencias no se aplica nada, que es el resultado seguro.
    """
    assert sentencias("/* comentario inventado sin cerrar; con punto y coma") == ()


# --- comentarios de línea ---------------------------------------------------


def test_f005_r1_un_comentario_de_linea_final_sin_salto_no_pierde_la_sentencia():
    """Un `.sql` cuya última línea es un `--` sin salto final sigue entero.

    No todos los editores dejan salto de línea al final del fichero. Si el
    escáner tratara el «no hay salto» como una posición del texto en vez de
    como su final, la sentencia anterior se perdería.
    """
    troceadas = sentencias(f"{TESTIGO};\n-- comentario final inventado sin salto")

    assert troceadas == (TESTIGO,)


# --- literales --------------------------------------------------------------


def test_f005_r1_un_literal_vacio_no_se_traga_la_sentencia_siguiente():
    """`DEFAULT ''` es un literal de dos comillas seguidas, y termina ahí.

    Si el escáner se saltara el primer carácter del literal, la comilla de
    cierre pasaría por la de apertura y el literal seguiría abierto hasta el
    final del fichero: la sentencia siguiente desaparecería.
    """
    troceadas = sentencias(
        f"CREATE TABLE IF NOT EXISTS postventa.inventada (n text DEFAULT '');\n"
        f"{TESTIGO}"
    )

    assert len(troceadas) == 2
    assert troceadas[0].endswith("DEFAULT '')")
    assert troceadas[1] == TESTIGO


def test_f005_r1_un_literal_sin_cerrar_no_revienta_el_troceado():
    """Una comilla sin cerrar devuelve la sentencia entera, no una excepción.

    El escáner llega al final del texto y para. Si en vez de parar leyera un
    carácter más, el arranque se caería con un `IndexError` a secas: quien lo
    viera no sabría ni qué fichero ni qué sentencia mirar, que es justo lo
    que los mensajes de `DdlInseguro` existen para decir.
    """
    texto = "CREATE TABLE IF NOT EXISTS postventa.inventada (n text DEFAULT 'sin cerrar"

    assert sentencias(texto) == (texto,)


def test_f005_r1_una_comilla_doblada_no_termina_el_literal():
    """`'d''Artagnan; S.L.'` es **un** literal, con su `;` dentro.

    Un apellido con apóstrofo es lo más normal del mundo en un dato de obra.
    Si el escáner diera el literal por terminado en la comilla doblada, el
    `;` de dentro cortaría la sentencia y se aplicarían dos fragmentos.
    """
    troceadas = sentencias(
        f"CREATE TABLE IF NOT EXISTS postventa.inventada "
        f"(n text DEFAULT 'd''Artagnan; S.L.');\n{TESTIGO}"
    )

    assert len(troceadas) == 2
    assert "'d''Artagnan; S.L.'" in troceadas[0]
    assert troceadas[1] == TESTIGO


def test_f005_r1_un_literal_que_solo_contiene_una_comilla_termina_donde_debe():
    """`''''` es el literal cuyo valor es **una comilla**, y acaba en la cuarta.

    Es el caso que separa «salto la comilla doblada» de «salto dos caracteres
    a ojo»: aquí el carácter siguiente a la pareja es **otra comilla**, así
    que contar mal deja el literal abierto y se traga el resto del fichero.
    """
    troceadas = sentencias(
        f"CREATE TABLE IF NOT EXISTS postventa.inventada "
        f"(n text DEFAULT '''');\n{TESTIGO}"
    )

    assert len(troceadas) == 2
    assert troceadas[0].endswith("DEFAULT '''')")
    assert troceadas[1] == TESTIGO


def test_f005_r1_un_literal_seguido_de_punto_y_coma_no_pierde_el_corte():
    """El `;` pegado a la comilla de cierre sigue cortando la sentencia."""
    troceadas = sentencias(
        f"CREATE OR REPLACE VIEW postventa.v_inventada AS SELECT 'uno';\n{TESTIGO}"
    )

    assert len(troceadas) == 2
    assert troceadas[0].endswith("SELECT 'uno'")
    assert troceadas[1] == TESTIGO


# --- cuerpos con dólares ----------------------------------------------------


def test_f005_r1_un_cuerpo_con_dolares_no_se_traga_la_sentencia_siguiente():
    """Tras `$$…$$` el escáner sigue troceando: el cuerpo termina en su cierre.

    Si el cierre no se reconociera, todo lo que viene detrás quedaría dentro
    del cuerpo y el fichero entero se aplicaría como **una** sentencia.
    """
    troceadas = sentencias(
        f"CREATE OR REPLACE VIEW postventa.v_inventada AS "
        f"SELECT $$uno; dos$$ AS t;\n{TESTIGO}"
    )

    assert len(troceadas) == 2
    assert troceadas[0].endswith("SELECT $$uno; dos$$ AS t")
    assert troceadas[1] == TESTIGO


def test_f005_r1_un_cuerpo_con_dolares_sin_cerrar_no_corta_por_dentro():
    """Un `$$` sin cerrar llega hasta el final, sin partir por su `;` interno.

    Igual que con el literal sin cerrar: lo que sale es **una** sentencia
    inválida que la guarda rechaza, no dos fragmentos que alguien aplicaría.
    """
    troceadas = sentencias("$$uno; dos")

    assert troceadas == ("$$uno; dos",)


# --- el punto y coma --------------------------------------------------------


def test_f005_r1_dos_sentencias_pegadas_por_el_punto_y_coma_salen_enteras():
    """Sin espacio tras el `;`, la segunda sentencia no pierde su primera letra.

    Reanudar dos caracteres después del `;` se lleva por delante la `C` de
    `CREATE`, y el error que produce eso en el arranque no dice ni de lejos
    lo que ha pasado.
    """
    tabla = "CREATE TABLE IF NOT EXISTS postventa.inventada (id text)"

    troceadas = sentencias(f"{TESTIGO};{tabla}")

    assert troceadas == (TESTIGO, tabla)


# --- el contrato de `_fin_de_literal`, por debajo del troceado --------------


def test_f005_r1_un_literal_sin_cerrar_que_acaba_en_comilla_doblada_llega_al_final():
    """`_fin_de_literal` devuelve el final del texto, no un carácter antes.

    Este test baja al ayudante privado **a propósito**, y es el único del
    fichero que lo hace. Por encima, en `sentencias`, la diferencia es
    invisible: si el ayudante se quedara corto, el bucle volvería a entrar por
    la comilla que dejó suelta, la trataría como un literal nuevo y pegaría el
    mismo texto en dos trozos consecutivos, con lo que la sentencia resultante
    saldría idéntica. La campaña de mutación de T23 lo demostró dejando vivo
    el `posicion + 1 < fin` de la línea 177 con la suite entera en verde.

    Que hoy se compense no lo hace inofensivo: el contrato documentado del
    ayudante es «la posición justo detrás de la comilla que cierra el
    literal», y en un literal sin cerrar esa posición es el final del texto.
    Quien lo reutilice mañana —para señalar dónde empieza y acaba un literal
    en el dry-run de la primera aplicación, por ejemplo— se comería el último
    carácter sin que ningún test se quejara.
    """
    #: `SELECT 'a''` — un literal abierto en la posición 7 que termina con una
    #: comilla doblada pegada al final del texto, sin cerrar nunca.
    texto = "SELECT 'a''"

    assert texto[7] == "'"
    assert _fin_de_literal(texto, 7) == len(texto)
    assert _fin_de_literal(texto, 7) == 11

    # Y, en efecto, por encima no se nota: el troceado sale igual de bien.
    assert sentencias(texto) == (texto,)
