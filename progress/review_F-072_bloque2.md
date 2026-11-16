<!-- progress/review_F-072_bloque2.md -->
Revisión incremental desde 7caa1d0 (pasada 2): delta `7caa1d0..4cb3727`. La pasada 1 revisó `c8c357e..7caa1d0`.

# F-072 · Review del Bloque 2 (dominio de la revisión: R21–R25)

- **Veredicto: APROBADO** (APPROVED) en `4cb3727`, condicionado a que el `init.sh` del líder
  salga verde (no lo he ejecutado: lo lanza el líder, por su encargo). Pasada 1: APROBADO en
  `7caa1d0`, con el caso borde del `listado` heredado como observación; el humano eligió (a) (Q-12).

## Pasada 2 · el ajuste del heredado (Q-12, opción (a))

- **Código** (`639245a`, `revision.py:509-511`): `_mismos_valores` compara las dos fotos con
  `listado=None`, además del tipo efectivo. Es el cambio mínimo y no toca nada más. La huella no
  pasa por ahí (R26 intacta: los tests de R26 siguen en verde dentro de los dirigidos). Estado,
  `sin_cambios` y `campos_cambiados` ya miran lo mismo, solo el tipo efectivo, y se cierra la
  incoherencia `editada` con `cambios == ()` de la pasada 1.
- **Tests** (`3ebcd15`, `d33d2ad`): `r25_el_listado_heredado_no_cuenta_para_el_estado`, parametrizado
  en los dos sentidos y en el cambio (`primero→None`, `None→segundo`, `primero→segundo`), con el
  contraste `9001` → `editada`; y `..._para_sin_cambios`. RED pegado con la salida real (`EDITADA is
  NUEVA`). Que el de `sin_cambios` pasara ya en rojo está explicado (editar copia el heredado, R23):
  es un test de coherencia y está bien que quede.
- **Mutación**: el generador solo da `!=` en la línea 511. Los dos mutantes que importan, quitar
  `listado=None` de cada lado, son manuales. Los he **reproducido** sobre una copia de `4cb3727` en el
  scratchpad (base `658 passed`): M1, lado `a`, `2 failed` (`[None-segundo]`, `[primero-segundo]`);
  M2, lado `b`, `2 failed` (`[primero-None]`, `[primero-segundo]`). Mismos tests que la tabla del
  implementer (M1 sobrevivía sin parametrizar; lo cazó él). T22 volverá a medir estas líneas.
- **Spec** (`4cb3727`): R25 ahora cubre `cambios`, el historial, el estado (R1 de F-056) y
  `sin_cambios` (R16), por tipo efectivo y sin el heredado; `design.md` §4.2 lo dice con la salvedad
  de la huella; Q-12 consta como decidida (humano, 2026-11-16). Coincide con el código. Los otros
  dos retoques de `design.md` (§1 y §9) solo condensan el texto, sin cambiar el sentido.
- **Tests en el árbol de trabajo**: F-072 de dominio y volcado, F-059 de dominio, F-060 y
  `tests/test_f056_*.py`: `1474 passed, 9 skipped`. Árbol limpio salvo este informe.
- Detalles menores, no bloquean: (1) antes de la `def` parametrizada nueva
  (`test_f072_revision_dominio.py:~602`) hay una sola línea en blanco, y PEP 8 pide dos; (2)
  `impl_F-072.md` aún dice «Specs sin tocar… encargo del spec-author», y `4cb3727` ya lo hizo.

## Pasada 1
- **Nivel de rigor:** `critico` (declarado en `harness/features.json`). Exige RED con traza, cobertura
  (90 %, la mide el `init.sh` del líder) y mutación con cero supervivientes; RM1–RM7.

## Checkpoints del bloque

- [x] **C1 tests**: dirigidos en el árbol de trabajo (dominio F-072/F-056/F-059/F-060, HTTP, paginación,
  documentación y pipeline de F-056): `1205 passed in 9.20s`. Suite entera: la del implementer
  (`10045 passed, 353 skipped`) y el `init.sh` del líder. Árbol limpio (solo los dos `.json` de campaña sin versionar, como en el Bloque 1).
- [x] **C2 trazabilidad**: R21–R25 con su test (tabla abajo). R27 es del Bloque 6 (HTTP).
- [x] **C3 diseño y hexagonal**: solo `domain/models/revision.py` en producción, como pide §4.2; puro.
- [x] **C3 bis / quater**: sin frontera nueva en este bloque; `azure-apps` va en T25.
- [x] **C4 RED**: traza real de T4 pegada (ImportError de `TIPO_NO_VALIDO` y, con la constante
  inyectada, `49 failed, 21 passed`). Los 21 verdes, explicados (la copia de R23 era estructural).
- [x] **C4 bis mutación**: ver abajo. Cero supervivientes; RM1–RM7 recorridas.
- [x] **C5 convenciones y secretos**: cabecera con ruta, español, sin prints, sin secretos ni datos
  reales (obra `9901`, tipos `9001`/`9002`/`9009`, «TIPO FICTICIO N», `@ejemplo.invalid`).

## Puntos que pidió mirar el líder

**1 · Aserciones de F-056/F-060: ninguna debilitada más allá de R22/R24/R25.** Las 7 de
`test_f056_revision_dominio.py` siguen siendo igualdades completas (foto y huella), solo con
`tipo_reclamacion="0002"` (R22), el décimo motivo en su sitio (R24) o el campo `listado` movido al
tipo (R25). La única aserción que desaparece es `isinstance(v.listado, Listado)` en
`r13_urgencia_y_listado_validos`, y la sustituye la igualdad de la terna `(urgencia, tipo, listado
heredado None)`, más fuerte. Paginación r27: diccionario completo con el motivo a 0; documentación:
9 → 10. **Los 3 HTTP (o2, r10, r42)**: el único cambio es `valores=_valores(listado="primero")` en
el `editar`, con comentario R22/R24 y aviso del Bloque 6; nada más del test cambia. Son el mínimo
de (b). r29: añade `tipo_reclamacion="9001"` y conserva `listado=SEGUNDO`; mínimo para R25.

**2 · `_mismos_valores` en `estado_de` y `sin_cambios`: coherente, no rompe la huella.**
- Es R25 («pasar de nulo a `0002` no es un cambio») aplicada a los otros dos sitios que comparan
  fotos. Sin ella, R22 haría que guardar sin tocar nada en una incidencia anterior a F-072 escribiera
  una revisión vacía y le quitara la aprobación a una aprobada (R2 de F-056 permite editar desde
  `aprobada`): con ella, `SinCambios` y la aprobación sigue. Tests: `r25_editar_una_foto_sin_tipo_*`
  (`None` y `"0002"`) y `r25_volver_a_lo_importado_*`.
- La huella no pasa por `_mismos_valores`: `huella_de_valores` sigue distinguiendo nulo y `0002`
  (R26, aprobado en el Bloque 1). Aprobar copia la foto tal cual, así que una aprobada anterior a
  F-072 conserva su huella; y como `sin_cambios` impide la revisión vacía, ninguna huella cambia
  sin un cambio real. Coherente con R26.
- **Caso borde de la pasada 1 (resuelto en la pasada 2, Q-12 (a)):** el heredado contaba para el
  estado y no para `cambios`, así que salía `editada` con `cambios == ()`. Pedí que constara en la
  spec, y ya consta en `4cb3727`.

**3 · R24 y R21.** Enum: `PROVEEDOR_AMBIGUO`, `TIPO_FUERA_DE_SIGRID`, `DUPLICADA`, y en
`motivos_no_aprobable` la comprobación va justo entre las dos (test con los cuatro motivos a la
vez). Aprobar con el motivo → `IncidenciaNoAprobable` (409); los códigos salen de `listas.listados`,
los mismos con que valida editar. Tipo nulo nunca es motivo; lista vacía sí se mira (`tipos is not
None`, el superviviente que mató `85d3c36`); sin `tipos` no se calcula. R21: `TIPO_NO_VALIDO` es una
constante y el test con `9999-RARO-F072` comprueba que no aparece ni en el mensaje ni en los errores.
`isinstance(pedido, str)` antes del `in` evita el `TypeError` con una lista (caso del test).

**4 · Mutación: suficiente para `critico`.**
- **Recálculo independiente** (`alcance_de_feature("F-072", base="6994cb0", rama="9b22088")` +
  `generar_mutantes`): 64/109/16 líneas, 4/20/0 mutantes, **24**. Coincide.
- **Control de `volcado.py` (0 mutantes)**: el fichero entero da 139; el cero es legítimo (docstrings,
  import, alias y la llamada a `tipo_efectivo`), con el control a mano del Bloque 1.
- **Uno por línea**: 16 líneas distintas; los 16 evaluados del `.json` y los 8 descartados de la
  tabla son exactamente el reparto que da el generador por línea. Sin muestreo (16 ≤ 100).
- **Los 8 descartados a mano**: reproduje tres al pie de la letra sobre una copia de `7caa1d0`
  (`aplicar_mutante`, `pytest -x`): `858 not in → in`, `757 or → and` y `857 is not None →
  veracidad`. Mueren con **el mismo primer test** que la tabla. Los otros cinco no los he repetido.
- **RM1**: medido en `9b22088`; `9b22088..7caa1d0` solo toca `progress/`. **RM2**: líneas base
  1670–1858 s; media 340,7 s = 5450,4 / 16; media con suite entera 958,9 s; con 8 workers y `-x`
  cuadra. Campaña no reejecutada: 91 min según el informe. **RM3**: ninguno de los 16 muertos es
  equivalente (`frozen=False`, `25`, `or` en 755: todos cambian comportamiento observable).
  **RM5**: sin equivalentes declarados. **RM6**: no se quitó ninguna guarda; se añadió una.
  **RM7**: N/A en este bloque. R24 es un orden dentro de una lista, no entre llamadas a colaboradores;
  los órdenes de lectura (R1, R11, R27) son de los Bloques 3, 5 y 6.
- El superviviente real que encontró el implementer antes de la campaña (`856 tipos`, lista vacía,
  R7) es un hallazgo de verdad: con cero tipos leídos se habría aprobado cualquier tipo. Bien cazado.

**5 · Alcance (R31/R32) y secretos.** `c8c357e..HEAD` toca solo `revision.py`, el test nuevo, los
4 tests de F-056 citados, `docs/ARCHITECTURE.md` (el motivo, adelantado por la opción (b)) y
`progress/`/`tasks.md`. Nada de §3.3: ni front, ni `infrastructure/`, ni `application/`, ni SQL,
ni `config/`, ni `.env`/`.xlsx`; `rigor.local.json` sin tocar. Sin escrituras en Sigrid (dominio puro).

## Cobertura requisito → test (`tests/test_f072_revision_dominio.py`)

| R | Tests |
|---|---|
| R21 | `r21_un_codigo_vigente_exacto_se_guarda`, `_el_tipo_que_ya_tiene_se_conserva_aunque_este_de_baja`, `_una_foto_sin_tipo_conserva_su_efectivo_0002_*`, `_otro_valor_es_error_en_listado` (10 casos), `_el_error_no_repite_lo_recibido`, `_por_decidir_*` |
| R22 | `r22_listado_nulo_guarda_0002_sin_mirar_la_lista` (nulo, vigente, de baja), `r22_por_decidir_nulo_guarda_0002` |
| R23 | `r23_editar_copia_el_listado_heredado`, `_descartar_`, `_recuperar_`, `_aprobar_copia_el_tipo_y_el_heredado`, `_la_revision_del_sistema_*` (tipo no nulo) |
| R24 | `r24_el_motivo_va_detras_*`, `_un_tipo_guardado_que_no_esta_vigente_es_motivo`, `_sin_tipo_guardado_*`, `_sin_ningun_tipo_vigente_*`, `_sin_los_tipos_leidos_*`, `_en_su_sitio_entre_los_demas`, `_no_se_puede_aprobar`, `_la_fila_y_el_resumen_lo_llevan` |
| R25 | `r25_mismo_tipo_efectivo_no_es_cambio`, `_otro_tipo_efectivo_es_cambio_de_listado`, `_el_listado_heredado_no_es_cambio`, `_editar_una_foto_sin_tipo_*`, `_volver_a_lo_importado_*` |

## Observaciones (no bloquean)

La 1 (spec del caso borde) y la 3 (`.json` de campaña sin versionar) de la pasada 1, resueltas.

2. **Estado transitorio de la rama, hasta el Bloque 6**: editar con `listado` nulo guarda `0002`, y
   aprobar lo compara con los listados del YAML, así que se bloquea; `listar_para_revisar`
   (`application/pipelines/revision.py:267`) y la respuesta de `aplicar_accion` (`:337`) llaman sin
   `tipos` y no enseñan el motivo. Es lo aceptado en (b); la rama no puede ir a `dev` antes de T23.
   En T19, pasar `tipos` en esas dos llamadas y volver a tocar o2/r10/r42.

## Automejora (propuesta, no aplicada)

Para `CHECKPOINTS.md` C4 bis: cuando la reducción «uno por línea» deja descartados por debajo del
suelo del nivel, que el informe de campaña los liste con su texto original → mutado y su resultado a
mano. Este bloque y el anterior lo han hecho por iniciativa propia, y el paso a mano sobre todos
los generados cazó huecos las dos veces (2 descartados vivos en el Bloque 1, `856 tipos` aquí,
antes de lanzar la campaña).
