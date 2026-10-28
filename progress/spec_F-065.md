<!-- progress/spec_F-065.md -->
# Spec de F-065 · informe del spec-author

Worktree `postventa-f065`, rama `feature/F-065-revision-sigrid-backend`, desde
`dev` `f7f63da` (commit `6eb23fa`). La spec aprobada el 2026-10-21 (con N-1 a
N-3) viene de `e38f01b`; su historia hasta esa aprobación está en
`progress/spec_F-064.md`. No se ha consultado Sigrid, ni la base, ni
SharePoint. No se han tocado `harness/features.json`, `BACKLOG.md` ni
`progress/current.md`.

## Conciliación 2026-10-28

Encargo del líder: conciliar requirements, design y tasks con el código real
de `dev` (F-059 tal como se cerró, F-060 y su API de revisión, el cliente de
`sigrid-api` con su límite de filas y `truncated`) y **añadir la guarda del
ensayo** por la decisión del humano del 2026-10-28 (C-4 de F-040: el botón
«Registrar» sincroniza con Sigrid antes de registrar, con la filosofía de
`azure-apps/dedicacion.md`).

### Qué cambió (ajustes a la realidad del código; ninguna decisión aprobada se mueve)

| Dónde | Qué decía | Qué dice ahora | Por qué |
|---|---|---|---|
| `design.md` cabecera, `tasks.md` cabecera | Base `dev` `383bfd5` | Conciliado con `dev` `f7f63da`, rama desde `6eb23fa` | La rama nueva |
| `requirements.md` R24, `design.md` §10.4, `tasks.md` T7 | La línea `F-065 sigrid de la bandeja` «con el cronómetro de F-060 sin cambiarlo», con `proceso_nuevo` y los tramos `construir.sigrid`…`serializar` | La línea la compone el borde con `tramos()`, `total()` y `calculo()`; la lista gana el tramo **`aplicacion`**; `proceso_nuevo` sale de un indicador **propio**, nunca de `es_primera_peticion()`; y lleva `segundos_de_proceso`. Un test fija que esta ruta no cambia el `proceso_nuevo` del siguiente listado | `Cronometro.linea()` escribe literal `F-060 tiempos del listado`; `calculo()` se mide contra el tramo `aplicacion`; `es_primera_peticion()` es **un** indicador por proceso y la ruta se lo comería al listado (eso sería cambiar sus logs, contra R26). `tiempos.py` no se toca |
| `requirements.md` R8 | 500.000 = `MAX_ALLOWED_ROWS` «de la instancia desplegada (§4.1)» | Precisado: es la App Setting de `func-sigridapi-dev-huyke` (la que usa todo el ecosistema; defecto del código 1.000); §4.1 avisa que paginar sigue siendo obligatorio; y la política de reintentos (35 s × 3) corta antes de 230 s pero **no** antes de los 45 s del proxy | Lo que dice `azure-apps/sigrid_api.md` §4.1; lo del proxy ya pasa con F-036 y F-056 |
| `design.md` §2 | El adaptador compone su `_leer` con `_un_intento`, `_mapear`, «la política de `tenacity`», `_cabeceras`, `_cliente_http` | Los cuatro métodos se heredan; la política **no es una pieza** (está dentro de `_leer` del catálogo), se compone igual con `es_transitorio` de `cliente.py`; `_fallo` es privada del módulo del catálogo, así que el adaptador tiene la suya | `infrastructure/sigrid/catalogo_obra.py` |
| `design.md` §5.1 | «Ensayar **y volcar** de nuevo la deja `volcada`» | Basta **ensayar**: un `idempotente` del ensayo ya la deja `volcada` (R13 de F-059); y la idempotencia exige la misma UPV (si no, `referencia_en_conflicto`) | R13 de F-059 y `azure-apps/sigrid_api.md` §8.9 |
| `design.md` §9.3 | No se toca `sql/` | `infrastructure/persistencia/sql/` (el último es `16_volcados_sigrid.sql`) | Esa ruta no existe en el servicio |

Comprobado y **sin cambio**: `exigir_entorno_con_catalogo` + `_exigir_configuracion`
(las dos puertas de R2); `TOPE_LECTURA_OBRA` 10.000 y `RevisionPort.listar(tope=)`;
`estado_de`, `valores_vigentes`, `es_candidata`, `SituacionDeRevision.volcado`;
`clave_de_ubicacion` (F-060), `plegar`, `normalizar_para_clave` y
`normalizar_codigo_obra` (F-036); `PREFIJO_REFERENCIA` y `referencia_de` (la
referencia sale en minúsculas; R10 compara sin distinguir mayúsculas, como la
pasarela); `ObraAmbigua`, `BandejaDemasiadoGrande` y `CatalogoNoDisponible`
existen; `SIGRID_TIMEOUT_S` 35, `SIGRID_REINTENTOS` 3,
`SIGRID_TIP_RECLAMACION` 708; el número 29 de `infra/` está libre; la fila de
consumidores de `sigrid_api.md` es su §10.

Observaciones que **no** se arreglan aquí (no son de esta ficha):

- `catalogo_obra.py`, `MAX_FILAS_CATALOGO`: su comentario dice que 1.000 es «el
  máximo que sirve `sigrid-api` en `pro`», ya falso (500.000). D-9 impide
  tocarlo; si se quiere corregir, es un ajuste de F-036.
- `docs/ARCHITECTURE.md`, sección de F-059: sigue diciendo «no está desplegada
  todavía», y `sigrid_api.md` §10 la da por publicada el 2026-10-17. Lo
  corrige T10 de esta ficha si toca esa sección (con S-1) o el dueño de F-059.

### Qué es nuevo (PENDIENTE DE OK del humano)

La **sincronización antes de registrar** y la **guarda del ensayo**:
`requirements.md` §12 (R41–R49, R70–R71), `design.md` §15 y §16, y en
`tasks.md` T2 bis, T-A0 bis, el **Bloque A4 bis** (T13–T17), una línea en T10
y T-A17–T-A18.

- **El veredicto** (R41), una función pura del dominio usada por la ruta y por
  el ensayo, sobre **todos** los pares de cada candidata: `se_enlaza`
  (emparejada por `PVI-`: la pasarela no puede crear otro parte), `ya_existe`
  (los dos criterios con una abierta), `choca` (otro conflicto), `va` (lo
  demás, también con avisos de reincidencia).
- **El contrato para F-040**:
  - sincronizar = la ruta de F-065 **tal cual**, `GET /api/revision/sigrid?obra=`,
    con un bloque aditivo `volcado` (candidatas, por veredicto, **por unidad**
    y la lista de veredictos con sus códigos) (R42);
  - el ensayo gana una clave **opcional** `conflictos_confirmados`
    (`[{incidencia_id, sigrid_cods}]`), por incidencia **y con los códigos**:
    si aparece una reclamación que choca después de confirmar, hay que
    confirmarla también (R43, R45);
  - el ensayo excluye `duplicada_en_sigrid` (`ya_existe`) y
    `conflicto_sin_confirmar` (`choca` sin todos sus códigos confirmados), con
    las `excluidas` de siempre, y añade un bloque `sigrid` a la respuesta (R45,
    R47);
  - `volcar` y el panel **no cambian**: lo excluido no tiene `previsto` y no
    se puede volcar (R49).
- **Si Sigrid falla o viene `truncated`**: no se ensaya —503
  `sigrid_no_disponible`, 409 `reclamaciones_sin_verificar` u `obra_ambigua`—,
  sin login, sin lote, sin nada guardado y sin interruptor (R46).
- **El coste**: con el troceo de F-059 (`N` = 5), 285 incidencias son 57
  ensayos. La propuesta es que la guarda lea **solo las unidades de lo que se
  manda** y **sin** los campos personales de R33 (`design.md` §15.5), porque
  los criterios exigen la misma unidad; un test fija que el veredicto es el
  mismo que con la obra entera (R49). Se mide **antes**, MANUAL y de solo
  lectura (T-A0 bis: el script 29 con `-Unidades`, la obra entera y una y
  cinco unidades de la 0677, tres veces cada una por los picos de F-061), y
  después en producción (T-A18, la duración del ensayo). Umbrales para volver
  al humano: obra > ≈ 10 s, guarda > ≈ 3 s.
- Sin DDL, sin variables nuevas, sin dependencias, sin caché. Las exclusiones
  no se guardan (el `CHECK` de `16_volcados_sigrid.sql` no las ve).

### Qué preguntas quedan (para el humano; todas con recomendación)

Numeradas **S-1 a S-9** (`design.md` §16; «S» para no confundirlas con la P-4
del arnés que cita `tasks.md`). La spec está escrita con la recomendación.

| # | Qué choca o qué hay que decidir | Recomendación |
|---|---|---|
| **S-1** | La guarda cambia el ensayo de F-059: choca con R26, R27 y §13 de F-065 (aprobados: «el volcado sin cambios», «el ensayo no mira los conflictos») y con R9 (cuerpo con exactamente cuatro claves) y R11 (cinco motivos) de F-059 | Enmendarlos: el ensayo gana una clave opcional, una lectura, dos motivos y un bloque aditivo; panel y `volcar` sin cambios. R26 y R27 llevan una nota y **no se han cambiado** |
| **S-2** | El encargo excluye «cualquier hallazgo de los criterios»; sin salida, es lo que Q-4 descartó para aprobar (un falso positivo de Jaccard ≥ 50 no se podría volcar nunca) | Solo `ya_existe` (los dos criterios y abierta) se excluye sin salida; `choca` se confirma; las cerradas solo avisan. Alternativas: todo conflicto excluido, o nada excluido |
| **S-3** | El encargo excluye lo emparejado por `PVI-`; F-059 resuelve una `en_duda` **reenviándola** (R27) y el `idempotente` la deja `volcada` (R13): excluirla la deja en duda para siempre | No excluirla (`se_enlaza`): la pasarela no puede crear otro parte con esa referencia |
| **S-4** | Cómo viaja la confirmación | `conflictos_confirmados` por incidencia con los códigos; descartados el booleano por lote y un `sincronizacion_id` guardado |
| **S-5** | Qué lee el ensayo (coste) | Solo las unidades de lo que se manda, sin datos personales, medido antes en T-A0 bis |
| **S-6** | ¿`volcar` relee Sigrid, como `dedicacion` antes de escribir? Cambiaría R15 de F-059 | No por ahora (ensayo ≤ 30 min); riesgo anotado |
| **S-7** | ¿Se guarda en la base quién confirmó un conflicto? | No (sería DDL); consta en el log de R48 |
| **S-8** | Sigrid caída o `truncated` en el ensayo | No se ensaya, sin interruptor |
| **S-9** | La ruta de sincronizar | La de F-065 tal cual con el bloque `volcado`; si T-A0 mide una respuesta pesada, un `vista=volcado` sin `ficha` (cambiaría R1) |

### Para el líder

- Los Bloques A1–A4, A5–A7 aprobados el 2026-10-21 se pueden ejecutar ya; lo
  nuevo (T2 bis, T-A0 bis, A4 bis, T-A17, T-A18 y la línea de T10) espera al
  OK de S-1 a S-9. Si el humano no aprueba S-1, el bloque nuevo sale de la
  ficha entera y F-040 tendría que garantizar la regla en el front.
- T-A0 bis conviene lanzarlo junto con T-A0 (mismo script, misma sesión del
  humano), en cuanto esté T2 bis.
- La spec de F-040 (otro worktree) tiene que usar este contrato (§15.3 de
  `design.md`): no se ha tocado desde aquí.
- **`bash harness/init.sh` al final (2026-10-28), en ROJO** por un test de
  tiempo ajeno a este trabajo: `1 failed, 5310 passed, 49 skipped in 667.53s`;
  el que falla es
  `tests/test_f036_excel_lector.py::test_f036_r115_celda_con_estilo_en_xfd1_es_barata_y_no_cambia_la_cabecera`
  (`assert 1.0106… < 1.0`, el tope de un segundo). Este trabajo solo cambia
  Markdown de `specs/` y `progress/`. La ejecución coincidió con la del líder
  en el mismo worktree (dos suites a la vez en el mismo equipo), que es lo
  más probable detrás de 0,01 s de más. No se ha reintentado ni tocado el
  test: lo decide el líder.

### Aprobación del humano (2026-10-28)

El humano aprueba S-1 a S-9 con las recomendaciones («si paruebo», tras el resumen del líder). Lo nuevo de la
conciliación (T2 bis, T-A0 bis, Bloque A4 bis, T-A17, T-A18 y la línea de T10) deja de esperar y entra en la ficha.
R26 y R27 de F-065 y R9, R11 y §13 de F-059 quedan enmendados en el sentido de S-1: la enmienda se escribe al
implementar el Bloque A4 bis, con su nota fechada en cada spec.

## Enmiendas tras la review del Bloque A2 (2026-10-28)

Encargo del líder: llevar a la spec las decisiones que tomó el humano el
2026-10-28 sobre las lecturas 1, 2, 3, 4 y 9 de `progress/review_F-065.md`
(«Review del Bloque A2», tabla «Las diez lecturas»), la del líder sobre la
lectura 6, y una tarea de corrección del Bloque A2. Solo spec: no se ha tocado
código, ni `features.json`, ni `BACKLOG.md`, ni `current.md`. No se ha
consultado Sigrid, ni la base, ni SharePoint.

### Qué cambió

| # | Decisión | Dónde | Qué dice ahora |
|---|---|---|---|
| 1 | Humano, lectura 1 | R12 (nota), R20, `design.md` §5.1 y §10.1 (`Hallazgo` y la tabla «Los códigos de cada hallazgo») | `Hallazgo` gana **`guardado_cod`**, el código de nuestra base, solo en `volcada_no_encontrada` y `codigo_distinto` (`null` en los demás). `sigrid_cods` son **siempre** códigos de Sigrid y solo no está vacío en `varias_en_sigrid`. `sigrid_cod`, si no es `null`, es siempre el `cod` de una reclamación de `reclamaciones`; por eso en `volcada_no_encontrada` pasa a `null`. Contrato con F-064 |
| 2 | Humano, lectura 2 | R12 (nota), §5.1 | `codigo_distinto` no se da si el guardado está entre las emparejadas; si no está, se da con la de código mayor en `sigrid_cod`. `anulada_en_sigrid` mira **solo** la de código mayor (es lo que pide C-A2-1) |
| 3 | Humano, lectura 3 | R13 (nota), §5.1 | **Ninguna** de las que llevan la referencia de una incidencia se cruza por criterios con ella; frente a las demás, todas |
| 4 | Humano, lectura 9 | R21 (nota), §10.1 («El orden de `Cruce.hallazgos`») | Tipo en el orden del enumerado, `incidencia_id` ascendente (`null` delante); los `coincide` de una incidencia en el **orden de R18** (fecha descendente, sin fecha al final, código descendente); los demás tipos por `sigrid_cod` ascendente. Filtrar `hallazgos` por incidencia y `coincide` da el orden de R18: F-064 toma los primeros sin reordenar. `Hallazgo` no gana la fecha |
| 5 | Humano, **enmienda a S-3**, lectura 4 | R41 (nota), R45 (nota), §15.2 (regla 0 de la tabla, ejemplos y párrafo), §16 S-3 | Una candidata cuya emparejada (la de código mayor) está en `NPR` da **`choca`**, no `se_enlaza`, con **solo** el código de la emparejada, y exige confirmación explícita en el ensayo (R45: sin ella, `conflicto_sin_confirmar` con ese código). Va antes de `se_enlaza` en la precedencia (también gana a un `ya_existe`). Que la menor de dos esté en `NPR` no cambia nada |
| 6 | Líder, lectura 6 | T5, `design.md` §10.2 | El mapeo del adaptador recorta `estado_codigo`, `cod`, `tipo_codigo` y `clase_codigo` (vacío tras recortar → `None`; `cod` vacío → error sin la fila), con su test. **`unidad_codigo` y `oficio_codigo`, PENDIENTE** (abajo) |
| — | Corrección del Bloque A2 | `tasks.md`, **T4 bis** (Bloque A2, antes de su «Parar. Review») | Lo que cambia el implementer en el dominio por 1–4 (5 no toca el dominio de A2: es de T13/T14), más C-A2-1 (fijar que `anulada_en_sigrid` mira solo la mayor, matar M12) y C-A2-2 (regenerar el informe de mutación desde un árbol confirmado). Y en cascada: T7 (la forma de R20 con `guardado_cod`), T13 (los casos de la enmienda a S-3) y T15 (la exclusión de la `choca` por `NPR`) |

Cabeceras de `requirements.md` y `design.md` con una nota que remite a estas
enmiendas; cada una marcada «*Enmienda del 2026-10-28*» en su sitio.

### Lecturas del spec-author (para que el líder las valide)

Ninguna cambia una decisión; concretan lo que las decisiones no dicen:

- **`sigrid_cod` = `null` en `volcada_no_encontrada`** (decisión 1). La
  decisión habla de `sigrid_cods`; he extendido la misma regla a `sigrid_cod`
  («solo códigos de reclamaciones que están en la respuesta»), porque es lo que
  señalaba la review (F-064 no encontraría ese código en `reclamaciones`) y con
  `guardado_cod` el guardado ya no se pierde.
- **Los códigos del veredicto `choca` por `NPR`** (decisión 5): solo el de la
  emparejada, no los de los `coincide` de conflicto, porque la pasarela no
  puede crear otro parte con esa referencia y lo que se confirma es «enlázala
  con el parte anulado». Y precedencia por delante de `se_enlaza` y de
  `ya_existe`.
- **El orden de los demás tipos** (decisión 4): por `sigrid_cod` ascendente,
  que es lo que ya hace T4.

### Decisión abierta: `unidad_codigo` y `oficio_codigo` en el recorte (decisión 6)

La decisión 6 dice «recorta `estado` y `cod` (y el resto de códigos que lleguen
de Sigrid)». Para `estado`, `cod`, `tipo_codigo` y `clase_codigo` no choca con
nada y está escrito. Para **`unidad_codigo` y `oficio_codigo` choca con partes
aprobadas** y no lo he resuelto:

- R14 (aprobado el 2026-10-21) los compara **por código exacto** con los de la
  bandeja.
- Los de la bandeja vienen del catálogo de F-036, que los lee **tal cual** de
  **las mismas columnas** (`SQL_UNIDADES_DE_LA_OBRA` lee `u.cod` de `con`;
  `SQL_OFICIOS_DE_LA_OBRA`, `a.cod` de `auxofc`; `_texto` no recorta) y que
  F-065 no puede tocar (D-9, §9.3).
- Si Sigrid rellenara esos códigos con blancos, recortarlos **solo** de este
  lado haría que ninguna unidad casara: **cero pares sin error**, justo lo que
  la decisión quiere evitar. Sin relleno, recortar no cambia nada.

Opciones: (a) dejarlos **tal cual**, como F-036, para que R14 compare lo mismo
con lo mismo (recomendación del spec-author: cumple la intención de la decisión
y no toca nada aprobado); (b) recortarlos y además comparar recortado en los
dos lados en el dominio (cambia R14 y el dominio ya revisado); (c) recortarlos
solo aquí, aceptando el riesgo. Está marcado **PENDIENTE** en T5 y en
`design.md` §10.2; no bloquea T4 bis ni el resto del Bloque A2, sí el T5 del
Bloque A3.

### Para el líder

- **F-064**: su spec (otro worktree, no tocada) tiene que recoger
  `guardado_cod` (y que `sigrid_cod` puede ser `null` en
  `volcada_no_encontrada`) y que los `coincide` de cada incidencia ya vienen
  en el orden de R18, para su R56 («las 3 primeras y N más») sin reordenar.
- **F-040**: la enmienda a S-3 cambia lo que verá en el bloque `volcado`: una
  candidata emparejada con una `NPR` sale `choca`, con un código, y hay que
  confirmarla.
- `requirements.md` §12 y la cabecera de `tasks.md` siguen diciendo
  «PENDIENTE DE OK» / «esperan al OK del humano a S-1–S-9», aunque el humano lo
  aprobó (sección anterior). No lo he tocado: no es de este encargo, y la
  sección anterior dice que la enmienda se escribe al implementar el Bloque A4
  bis.
