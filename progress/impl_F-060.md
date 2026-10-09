<!-- progress/impl_F-060.md -->
# F-060 · Normalizar las ubicaciones de la bandeja al texto exacto de Sigrid — Informe del implementer

Rama `feature/F-060-normalizar-ubicaciones`. Rigor **`critico`**.
Spec: `specs/F-060-normalizar-ubicaciones/` (aprobada por el humano el 2026-10-09: D-1 a D-10 tal cual;
Q-1, las normalizadas pasan de `nueva` a `editada`).

**Base fija: `33d8938`** (`dev` en `704cfca` más el commit del backlog; fijada en `tasks.md` y por el líder el
2026-10-09). Las guardias de alcance y la mutación del Bloque 1 usan esa.

## Bloque 1 · La regla y el plan (dominio puro) · T1, T2, T3 · 2026-10-09

### T1 · Fase RED

`tests/test_f060_normalizacion_dominio.py` (80 casos) contra un **esqueleto neutro** de
`domain/models/normalizacion.py` con los nombres de `design.md` §6 y cuerpos que no deciden nada:
`clave_de_ubicacion` devuelve el texto tal cual, `ubicacion_de_sigrid` siempre `sin_coincidencia`,
`revision_de_normalizacion` devuelve los vigentes sin cambiar y con huella vacía, `planificar_normalizacion` un
plan vacío con el recuento a cero, `TEXTO_SISTEMA` y `QUIEN_SISTEMA` vacíos, `ESTADOS_NORMALIZABLES` vacío y los
tres tipos sin `frozen`. Así cada test falla por **aserción** y no por la importación.

Comando, desde `services/postventa-api`:

```
.venv/Scripts/python.exe -m pytest tests/test_f060_normalizacion_dominio.py -q -p no:cacheprovider --tb=line -rf
```

Salida real (una línea por fallo con `--tb=line`, la lista de `FAILED` y el total; solo se ha recortado el prefijo
absoluto de la ruta):

```
tests\test_f060_normalizacion_dominio.py:208: AssertionError: assert 'Sala Ejemplo' == 'sala ejemplo'
tests\test_f060_normalizacion_dominio.py:208: AssertionError: assert 'SALA EJEMPLO' == 'sala ejemplo'
tests\test_f060_normalizacion_dominio.py:208: AssertionError: assert '  Sala Ejemplo\t' == 'sala ejemplo'
tests\test_f060_normalizacion_dominio.py:208: AssertionError: assert '\nPATIO Ficticio  ' == 'patio ficticio'
tests\test_f060_normalizacion_dominio.py:208: AssertionError: assert '   ' == ''
tests\test_f060_normalizacion_dominio.py:215: AssertionError: assert 'Straße Ejemplo' == 'strasse ejemplo'
tests\test_f060_normalizacion_dominio.py:223: AssertionError: assert 'Ban\u0303o Ejemplo' == 'Ba\xf1o Ejemplo'
tests\test_f060_normalizacion_dominio.py:238: AssertionError: assert 'Sala  Ejemplo' == 'sala  ejemplo'
tests\test_f060_normalizacion_dominio.py:238: AssertionError: assert 'Sála Ejemplo' == 'sála ejemplo'
tests\test_f060_normalizacion_dominio.py:238: AssertionError: assert 'Pingüino Ejemplo' == 'pingüino ejemplo'
tests\test_f060_normalizacion_dominio.py:238: AssertionError: assert 'Sala Ejemplo.' == 'sala ejemplo.'
tests\test_f060_normalizacion_dominio.py:238: AssertionError: assert 'Sala-Ejemplo' == 'sala-ejemplo'
tests\test_f060_normalizacion_dominio.py:276: AssertionError: assert UbicacionDeSi...>, texto=None) == UbicacionDeSi...>, texto=None)
tests\test_f060_normalizacion_dominio.py:276: AssertionError: assert UbicacionDeSi...>, texto=None) == UbicacionDeSi...>, texto=None)
tests\test_f060_normalizacion_dominio.py:276: AssertionError: assert UbicacionDeSi...>, texto=None) == UbicacionDeSi...Sala Ejemplo')
tests\test_f060_normalizacion_dominio.py:276: AssertionError: assert UbicacionDeSi...>, texto=None) == UbicacionDeSi...tio ficticio')
tests\test_f060_normalizacion_dominio.py:276: AssertionError: assert UbicacionDeSi...>, texto=None) == UbicacionDeSi...Sala Ejemplo')
tests\test_f060_normalizacion_dominio.py:276: AssertionError: assert UbicacionDeSi...>, texto=None) == UbicacionDeSi...Sala Ejemplo')
tests\test_f060_normalizacion_dominio.py:276: AssertionError: assert UbicacionDeSi...>, texto=None) == UbicacionDeSi...tio ficticio')
tests\test_f060_normalizacion_dominio.py:276: AssertionError: assert UbicacionDeSi...>, texto=None) == UbicacionDeSi...tio ficticio')
tests\test_f060_normalizacion_dominio.py:276: AssertionError: assert UbicacionDeSi...>, texto=None) == UbicacionDeSi...>, texto=None)
tests\test_f060_normalizacion_dominio.py:276: AssertionError: assert UbicacionDeSi...>, texto=None) == UbicacionDeSi...>, texto=None)
tests\test_f060_normalizacion_dominio.py:282: AssertionError: assert UbicacionDeSi...>, texto=None) == UbicacionDeSi...>, texto=None)
tests\test_f060_normalizacion_dominio.py:291: AssertionError: assert UbicacionDeSi...>, texto=None) == UbicacionDeSi...tio Ficticio')
tests\test_f060_normalizacion_dominio.py:301: AssertionError: assert UbicacionDeSi...>, texto=None) == UbicacionDeSi...>, texto=None)
tests\test_f060_normalizacion_dominio.py:309: AssertionError: assert UbicacionDeSi...>, texto=None) == UbicacionDeSi...>, texto=None)
tests\test_f060_normalizacion_dominio.py:316: AssertionError: assert UbicacionDeSi...>, texto=None) == UbicacionDeSi...Sala Ejemplo')
tests\test_f060_normalizacion_dominio.py:322: AssertionError: assert UbicacionDeSi...>, texto=None) == UbicacionDeSi...Baño Ejemplo')
tests\test_f060_normalizacion_dominio.py:331: AssertionError: assert UbicacionDeSi...>, texto=None) == UbicacionDeSi...raße Ejemplo')
tests\test_f060_normalizacion_dominio.py:365: AssertionError: assert <Coincidencia.SIN_COINCIDENCIA: 'sin_coincidencia'> is <Coincidencia.NORMALIZABLE: 'normalizable'>
tests\test_f060_normalizacion_dominio.py:373: AssertionError: assert <Coincidencia.SIN_COINCIDENCIA: 'sin_coincidencia'> is <Coincidencia.NORMALIZABLE: 'normalizable'>
tests\test_f060_normalizacion_dominio.py:384: AssertionError: assert '' == 'sistema:normalizar_ubicacion'
tests\test_f060_normalizacion_dominio.py:393: AssertionError: assert frozenset() == frozenset({<E...VA: 'nueva'>})
tests\test_f060_normalizacion_dominio.py:402: Failed: DID NOT RAISE FrozenInstanceError
tests\test_f060_normalizacion_dominio.py:422: AssertionError: assert '' == 'sistema:normalizar_ubicacion'
tests\test_f060_normalizacion_dominio.py:422: AssertionError: assert '' == 'sistema:normalizar_ubicacion'
tests\test_f060_normalizacion_dominio.py:422: AssertionError: assert '' == 'sistema:normalizar_ubicacion'
tests\test_f060_normalizacion_dominio.py:447: AssertionError: assert 'SALA EJEMPLO' == 'Sala Ejemplo'
tests\test_f060_normalizacion_dominio.py:476: AssertionError: assert () == (RevisionNuev...mezone.utc)),)
tests\test_f060_normalizacion_dominio.py:511: AssertionError: assert [] == [UUID('000000...00000000001')]
tests\test_f060_normalizacion_dominio.py:526: AssertionError: assert [] == [UUID('000000...00000000002')]
tests\test_f060_normalizacion_dominio.py:535: AssertionError: assert RecuentoNorma...o_editables=0) == RecuentoNorma...o_editables=0)
tests\test_f060_normalizacion_dominio.py:543: AssertionError: assert RecuentoNorma...o_editables=0) == RecuentoNorma...o_editables=0)
tests\test_f060_normalizacion_dominio.py:543: AssertionError: assert RecuentoNorma...o_editables=0) == RecuentoNorma...o_editables=0)
tests\test_f060_normalizacion_dominio.py:552: AssertionError: assert RecuentoNorma...o_editables=0) == RecuentoNorma...o_editables=0)
tests\test_f060_normalizacion_dominio.py:559: AssertionError: assert RecuentoNorma...o_editables=0) == RecuentoNorma...o_editables=0)
tests\test_f060_normalizacion_dominio.py:574: AssertionError: assert [] == [UUID('000000...00000000003')]
tests\test_f060_normalizacion_dominio.py:589: AssertionError: assert RecuentoNorma...o_editables=0) == RecuentoNorma...o_editables=1)
tests\test_f060_normalizacion_dominio.py:589: AssertionError: assert RecuentoNorma...o_editables=0) == RecuentoNorma...o_editables=1)
tests\test_f060_normalizacion_dominio.py:599: AssertionError: assert RecuentoNorma...o_editables=0) == RecuentoNorma...o_editables=0)
tests\test_f060_normalizacion_dominio.py:599: AssertionError: assert RecuentoNorma...o_editables=0) == RecuentoNorma...o_editables=0)
tests\test_f060_normalizacion_dominio.py:607: assert 0 == 1
tests\test_f060_normalizacion_dominio.py:627: AssertionError: assert {} == {UUID('000000...0000003'): 91}
tests\test_f060_normalizacion_dominio.py:642: AssertionError: assert [] == [UUID('000000...0000000001e')]
tests\test_f060_normalizacion_dominio.py:671: AssertionError: assert RecuentoNorma...o_editables=0) == RecuentoNorma...o_editables=2)
tests\test_f060_normalizacion_dominio.py:698: AssertionError: assert RecuentoNorma...o_editables=0) == RecuentoNorma...o_editables=0)
tests\test_f060_normalizacion_dominio.py:741: AssertionError: assert <EstadoRevision.NUEVA: 'nueva'> is <EstadoRevision.EDITADA: 'editada'>
tests\test_f060_normalizacion_dominio.py:772: assert 0 == 2
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r1_la_clave_recorta_y_pliega_mayusculas[Sala Ejemplo-sala ejemplo]
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r1_la_clave_recorta_y_pliega_mayusculas[SALA EJEMPLO-sala ejemplo]
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r1_la_clave_recorta_y_pliega_mayusculas[  Sala Ejemplo\t-sala ejemplo]
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r1_la_clave_recorta_y_pliega_mayusculas[\nPATIO Ficticio  -patio ficticio]
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r1_la_clave_recorta_y_pliega_mayusculas[   -]
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r1_casefold_y_no_lower
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r1_nfc_frente_a_nfd
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r1_la_clave_no_toca_nada_mas[Sala  Ejemplo-sala  ejemplo]
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r1_la_clave_no_toca_nada_mas[S\xe1la Ejemplo-s\xe1la ejemplo]
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r1_la_clave_no_toca_nada_mas[Ping\xfcino Ejemplo-ping\xfcino ejemplo]
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r1_la_clave_no_toca_nada_mas[Sala Ejemplo.-sala ejemplo.]
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r1_la_clave_no_toca_nada_mas[Sala-Ejemplo-sala-ejemplo]
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r2_cada_fila_de_la_tabla[Sala Ejemplo-lista0-exacta-None]
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r2_cada_fila_de_la_tabla[patio ficticio-lista1-exacta-None]
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r2_cada_fila_de_la_tabla[ Sala Ejemplo -lista2-normalizable-Sala Ejemplo]
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r2_cada_fila_de_la_tabla[\tpatio ficticio\n-lista3-normalizable-patio ficticio]
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r2_cada_fila_de_la_tabla[SALA EJEMPLO-lista4-normalizable-Sala Ejemplo]
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r2_cada_fila_de_la_tabla[sala ejemplo-lista5-normalizable-Sala Ejemplo]
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r2_cada_fila_de_la_tabla[Patio Ficticio-lista6-normalizable-patio ficticio]
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r2_cada_fila_de_la_tabla[  PATIO FICTICIO -lista7-normalizable-patio ficticio]
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r2_cada_fila_de_la_tabla[PATIO FICTICIO-lista8-ambigua-None]
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r2_cada_fila_de_la_tabla[Patio ficticio-lista9-ambigua-None]
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r2_el_exacto_gana_aunque_otro_tenga_la_misma_clave
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r2_el_exacto_tras_recortar_gana_a_la_ambiguedad
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r2_ambigua_con_tres_candidatos
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r2_ambigua_por_la_forma_unicode_de_la_lista
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r2_un_valor_repetido_tal_cual_no_es_ambiguo
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r2_nfd_frente_a_nfc
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r2_casefold_en_la_clasificacion
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r5_el_resultado_es_el_valor_de_la_lista_caracter_a_caracter
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r5_el_resultado_conserva_la_forma_unicode_de_la_lista
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r8_la_identidad_del_sistema
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r7_estados_normalizables_son_nueva_y_editada
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_los_tipos_son_inmutables
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r11_validar_quien_rechaza_el_correo_del_sistema[-]
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r11_validar_quien_rechaza_el_correo_del_sistema[oid-de-prueba-f060-]
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r11_validar_quien_rechaza_el_correo_del_sistema[oid-de-prueba-f060-    ]
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r8_la_revision_cambia_solo_la_ubicacion_de_los_vigentes
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r6_una_normalizable_da_una_revision
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r6_mira_la_unidad_vigente_y_no_la_importada
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r6_mira_la_ubicacion_vigente_y_no_la_importada
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r6_una_ubicacion_de_otra_unidad_no_vale
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r6_una_unidad_sin_lista_no_normaliza[9901.03VILLA 3.]
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r6_una_unidad_sin_lista_no_normaliza[9901.03VILLA 9.]
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r6_sin_ubicacion_o_exacta_se_examina_y_no_cuenta
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r6_ambigua_no_se_normaliza
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r7_nueva_y_editada_se_normalizan
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r7_aprobada_y_descartada_son_no_editables[aprobar]
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r7_aprobada_y_descartada_son_no_editables[descartar]
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r7_no_editable_solo_cuenta_las_normalizables[aprobar]
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r7_no_editable_solo_cuenta_las_normalizables[descartar]
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r8_la_revision_del_plan_es_la_de_normalizacion
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r9_la_esperada_es_la_ultima_revision_leida
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r9_las_revisiones_van_en_orden_de_incidencia_id
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r10_el_recuento_de_una_obra_y_su_suma
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r10_el_plan_acepta_un_iterable_de_una_pasada
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r22_la_normalizada_queda_editada_y_sin_el_motivo
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r21_una_segunda_pasada_no_tiene_nada_que_normalizar
58 failed, 22 passed in 0.53s
```

**58 fallan, todos por aserción** (57 `AssertionError` y un `Failed: DID NOT RAISE FrozenInstanceError`); ninguno
por `ImportError`, `TypeError` ni `ValueError`. Los **22 que pasan en RED** son controles cuya respuesta correcta
coincide con la neutra, y tienen que seguir en verde:

| Tests que pasan en RED | Por qué |
|---|---|
| `test_f060_r2_cada_fila_de_la_tabla` (las 4 filas `sin_coincidencia`), `test_f060_r3_lista_vacia` (×5), `test_f060_r4_lo_que_no_es_la_misma_palabra_no_coincide` (×10) | `sin_coincidencia` es justo lo que devuelve el esqueleto: son el control negativo de R2–R4 (lo que **no** se puede normalizar). Su contraparte positiva sí falla |
| `test_f060_r1_la_clave_recorta_y_pliega_mayusculas[-]` | La clave de `""` es `""`, también sin hacer nada |
| `test_f060_r6_sin_situaciones_el_plan_esta_vacio` | Sin incidencias, el plan vacío es la respuesta correcta y la neutra |
| `test_f060_r23_ambigua_y_sin_coincidencia_siguen_fuera_de_lista` | Guarda: lo que no se normaliza no recibe revisión y sigue con el motivo de F-056 |

R11 (`validar_quien` rechaza el correo del sistema) **ya se cumple con el código de F-056** (el literal no tiene
`@`): en RED falla por la comprobación del literal (`'' == 'sistema:normalizar_ubicacion'`), que es lo que F-060
añade; el rechazo en sí es una guarda que no se puede ver fallar sin tocar `revision.py`, que no se toca.
