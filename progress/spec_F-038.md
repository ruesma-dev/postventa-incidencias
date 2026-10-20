<!-- progress/spec_F-038.md -->
# F-038 · Informe del spec-author

## Conciliación con dev · 2026-10-20

**Encargo del líder (2026-10-20):** poner al día con `dev` la spec aprobada
de F-038 (`specs/F-038-bandeja-revision/`, del 2026-10-06), sin reescribirla.
Rama `feature/F-038-bandeja-revision`, nacida de `dev` **`87a03f3`** (base
fija). Solo lectura y redacción: ni `init.sh` ni pytest (P-4), ni `.env`.

**Resultado.** Ninguna decisión aprobada (D-1, D-2, D-4, D-8, D-11, D-12,
D-13, Q-2, Q-3, Q-4) cambia. La conciliación **no** necesita tocar
`services/postventa-api`: no hay bloqueo. Hay **cinco decisiones nuevas**
(Q-6 a Q-10) que la spec no contemplaba, redactadas con la recomendación y
**pendientes de aprobación del humano**; T1 no empieza hasta que las
resuelva. *(Resueltas el 2026-10-20: sección final.)*

Cómo se ha hecho: lo conciliado está **en su sitio** en los tres ficheros,
con la marca «Conciliado 2026-10-20» y su fuente; numeración intacta
(R1–R19, T1–T11); lo nuevo, al final (R20–R26; `design.md` §10). Cabeceras
con la fecha y la base `87a03f3`.

### 1 · Qué cambió y por qué (con su fuente)

#### 1.1 · F-059 (volcado; `done` 2026-10-20)

| Cambio en la spec | Fuente |
|---|---|
| Seis estados: `volcada` y `en_duda` además de los cuatro (R4 (c), R5) | F-059 R1; `EstadoRevision` en `domain/models/revision.py` |
| Desde `volcada` y `en_duda`, ninguna acción; 409 `accion_no_permitida` con `estado` y `acciones: []` (R11, R12, R21) | F-059 R2, design §4.2; `_PERMITIDAS`; `_error_de_revision` |
| `activas` = todo menos `descartada` **y `volcada`** (R6) | F-059 R4 (d), D-7 de F-059; `_FUERA_DE_ACTIVAS`, `_pasa` |
| Filtros `volcada` y `en_duda` (R6, R21: en F-040 salvo Q-6 (a')) | F-059 R4 (c); `FiltroEstado`, `_filtro` |
| Seis claves en `resumen.por_estado` (R5) | F-059 R4 (b); handler `listar_revision` |
| Objeto `volcado` en cada incidencia y en la respuesta de la acción; F-038 lo ignora (R4 (e), R21) | F-059 R4 (a), F-2 (a); `volcado_de` en `interface_adapters/api/volcado.py` |
| Riesgo y verificación: no dejar aprobada la fila de prueba (candidata al volcado); comprobar la `volcada` de la 0626 en solo lectura (T7) | F-059 R3; `progress/history.md` (F-059: `RS26.10/0074` sigue `volcada` en la bandeja) |
| La primera lectura de Sigrid tras un rato puede pasar de 35 s (riesgo 7, T7 paso 2) | Lo aprendido en F-059 (`progress/history.md`) |

**Encaje con F-040.** F-059 design §16 y la spec aprobada de F-040 (rama
`feature/F-040-volcado-sigrid`, design §3: «En `js/revision.js` (de F-038), las
etiquetas de `volcada` y `en_duda`, la línea "Volcada como RS…" y los filtros
nuevos (R54)») dan a F-040 la presentación del volcado. Pero F-038 se publica
antes y, con `activas` por defecto, una `en_duda` sale en su lista: Q-6.

#### 1.2 · F-060 (normalizar ubicaciones; `done`)

| Cambio en la spec | Fuente |
|---|---|
| Revisiones del sistema: `revisado_por`/`correo` = `sistema:normalizar_ubicacion`, que no es un correo (R4 (d), R8, R22) | F-060 R22, definición de «Identidad del sistema»; design §10.1 («mejora opcional» para F-038) |
| La normalización corre sola tras cada importación; existe `POST /api/revision/normalizar` (R15, R23) | F-060 R26–R31; `revision_normalizar` en `function_app.py` |
| Las 38 ubicaciones de la 0677 que siguen fuera de lista: qué hace el formulario (R24) | F-060 V1 y `progress/history.md` (110 normalizadas, 148 → 38) |
| T7 paso 2: el resumen ya no es el de la T19 de F-056; se compara con un `GET` del momento | Ídem |
| Ninguna clave nueva en las tres rutas | F-060 R36 |

#### 1.3 · F-056 tal como quedó (el contrato de verdad)

| Cambio en la spec | Fuente |
|---|---|
| Proveedores de un oficio desde **`catalogo.pares`** (R9 (a)) | F-056 R28; `_pares` del handler |
| «Grupo de la fila» de un ambiguo = oficios con `grupo.etiqueta` igual al `oficio_nombre` vigente (R9 (b)) | `_oficios` del handler |
| Con el ambiguo sin elegir, proveedor solo el vigente o ninguno; `oficio_codigo: null` (R9 (c)) | F-056 R15 |
| Marcas `oficio_ambiguo` y `proveedor_ambiguo` en `importados`/`vigentes` (design §1) | `_valores_de` |
| Los nueve motivos, en su orden (R4 (a)) | `MotivoNoAprobable`; F-056 R21, design §3.5 |
| Ubicación vacía = `null`; `""` es 400 (R9 (d)) | F-056 design §8 y §3.5 (precisión del 2026-10-07) |
| `hayCambios` con la normalización del backend, para no provocar 400 `sin_cambios` (R9 (e)) | F-056 R13, R16 |
| Tabla completa de errores: `peticion_invalida`, `valores_no_validos` (`errores`), `sin_cambios`, `incidencia_no_encontrada`, `obra_sin_unidades`, `accion_no_permitida` (`estado`, `acciones`), `revision_desactualizada`, `incidencia_no_aprobable` (`motivos`), `bandeja_demasiado_grande` (`total`), `obra_ambigua`, `catalogo_sin_verificar`, 500 y 503 sin `codigo`; y la acción sin respuesta (R12) | `CODIGOS_DE_REVISION`, `_error_de_revision`, `_rechazo_de_obra`, rutas `revision`, `revision_historial`, `revision_acciones` |
| Cuerpo con exactamente las claves de cada acción; la acción no se reintenta (R10) | `_peticion`, `_COMUNES`, `_PROPIAS` |
| `duplicada_de` es un UUID: «fila N» solo si la original está cargada (R4 (b)) | `_fila` |
| Cursor base64url opaco; tamaño 100/200; la página no manda `tamano` (R7) | `cursor_de`, `clave_de_cursor`, `TAMANO_POR_DEFECTO`, `TAMANO_MAXIMO` |
| El resumen cuenta motivos también de las descartadas; `ajustarResumen` con `null` solo mueve estados; deriva conocida del `duplicada` de otra fila (design §2.3, riesgo 8) | `resumen` en `domain/models/revision.py`; F-056 R8, R22 |
| Acciones por estado: `aprobada` no ofrece «Aprobar» (R11) | F-056 design §3.3; `_PERMITIDAS` |

#### 1.4 · El front de hoy

| Cambio en la spec | Fuente |
|---|---|
| `js/api.js`: `clasificar` no conserva lo propio del cuerpo de un error → se añade, aditivo (R26, design §2.1) | `clasificar`/`ErrorApi` de `js/api.js` |
| Las tres funciones con `mensajeDelServicio: true` (sin él, un 503 dice el texto de archivar) | `clasificarSinDetalle`, `TEXTO_ENTORNO_NO_ARCHIVA` |
| `api.test.js` cuenta 17 endpoints y los lista: se amplía | `tests_js/api.test.js` (`LOS_ENDPOINTS`) |
| `js/importacion.js` no exporta su fecha (y es solo día): `js/revision.js` lleva la suya | `Importacion` exportado |
| El pie de una página real es de su sección; sin subnavegación (R1) | `importar.html`, `oficios.html`, `PIE_PAGINAS_REALES` |
| La guardia de la tira no admite el paso 03 en `bandeja.html` (R85 frente a R86): Q-10 | `problemasDelRecorrido` en `tests_js/portal.test.js` |
| R14: enlace fuera de la `<table>` y como `<a>` | `test_f036_r50_la_bandeja_es_de_solo_lectura`, `botones_prohibidos` |

#### 1.5 · Guardias del portal (F-035), recontadas sobre `87a03f3`

- `Portal.PAGINAS` tiene dos páginas; `bandeja` en `construccion` con F-038,
  F-039, F-040 y F-043; `pasoDeSeccion("bandeja")` = `"02"`. Como decía la
  spec.
- Restos (escáner de `tests/test_f035_placeholders_vivos.py`): **F-038, 7**
  (3 en `index.html`, 3 en `PLACEHOLDERS`, 1 en `MaquetaDatos`), más su
  título en `TITULOS_FICHAS`; F-039, 5; F-040, 7; F-043, 6; F-044, 9. Tras el
  cierre, F-039 y F-043 conservan restos fuera de `#/bandeja` y F-040 en su
  envoltorio de bloque: R18 se cumple.
- R28 ya usa F-044 en su control; el de R62 usa F-038 y pasa a F-044 (como
  decía la spec).
- **Nuevo:** otros **dos** controles miran la sección `bandeja` y se romperían
  en el cierre: `test_f035_r62_control_el_lector_de_estados_lee_el_texto`
  (sustituye `bandeja` → `parcial`; con `bandeja` ya en `parcial`, la copia
  no cambia) y «f035 R66: control: quitar data-construccion de una pestaña de
  partes.html salta». Se mudan a `impresion` en T1 bis (Bloque 1 bis).
- **Nuevo:** en el cierre, también `bandeja.reintentarVolcado` (F-040) es
  `enBloque: true` sobre la selección de la bandeja, y
  `MaquetaDatos.propuestas.porFila` (F-039) apunta a las filas `BJ-…` de la
  bandeja (design §3.2).
- Inventario de listas de páginas (design §3.1), con las cuatro de `entrada`
  que **no** se amplían.

#### 1.6 · Dependencia, publicación y verificación

- D-1 cumplida: sin merge previo; base fija `87a03f3` (design §1, tasks
  cabecera, T5 `--base 87a03f3`).
- T6/T10: `infra/desplegar_front.ps1 -SoloFront` existe con ese parámetro y
  deduce la raíz con `$PSScriptRoot`: los comandos desde el worktree limpio
  valen tal cual. Se añade que el líder hace el merge desde un worktree
  aparte y pone al día `azure-apps` (R20).
- T7: `infra/24_ubicacion_sigrid.ps1 -CodigoObra` existe; pasos 2 y 3
  ajustados; pasos 3 bis y 3 ter nuevos (solo lectura).
- `init.sh` lo ejecuta el líder mientras P-4 siga abierto (tasks cabecera,
  T5, T9).

#### 1.7 · Reglas del repositorio

- **R20**: la página nueva es algo que el proyecto expone →
  `docs/ARCHITECTURE.md` (implementer, T3 y T8) y
  `azure-apps/postventa_incidencias.md` (el líder, en su repositorio, T6 y
  T10). La spec del 2026-10-06 solo pedía el README.

#### 1.8 · Solapes con fichas que vienen detrás

- **F-057** (`pending`; spec en `feature/F-057-tabla-bandeja-paso1`): rehace la
  tabla de `importar.html`, conserva el enlace de R14 (su R27) y añade a
  `bandeja.html` el enlace profundo `?incidencia=` (su R21–R25). Va después de
  F-038; su T1 ya prevé comprobar que lo construido encaja.
- **F-040** (`spec_ready`; spec en `feature/F-040-volcado-sigrid`): pone su
  panel en `bandeja.html`. *(Actualizado tras la decisión Q-6 del humano,
  2026-10-20.)* **F-040 ya no trae la presentación del volcado**: su R54
  (etiquetas de `volcada` y `en_duda`, la línea «Volcada como RS…», los
  textos de los códigos de parte de §8.9 y los filtros) es ahora R21 de
  F-038. Queda para **la conciliación de F-040** quitar R54 de su spec (y la
  frase de su design §3 sobre `js/revision.js`), conservando solo los textos
  propios del panel (exclusiones de un ensayo, ensayo no válido) y apoyándose
  en `lineaDeVolcado` / `textoMotivoVolcado` de `js/revision.js`.

### 2 · Preguntas para el humano (con recomendación) — resueltas el 2026-10-20, ver «Decisiones del humano · 2026-10-20»

Detalle y alternativas en `specs/F-038-bandeja-revision/design.md` §10.4.

- **Q-6 · `volcada` y `en_duda` en F-038.** Recomiendo **(a)**: etiqueta, «Ya
  no se revisa aquí» y ningún botón ni formulario; lo demás del volcado
  (línea con el código de Sigrid, motivos de rechazo, filtros) se queda en
  F-040 R54, como está aprobado. Alternativas: (a') también los dos filtros
  ya; (b) todo R54 de F-040 aquí; (c) nada (descartada: ofrecería acciones
  que dan 409).
- **Q-7 · Revisión del sistema.** Recomiendo «el sistema (ubicación puesta en
  el texto exacto de Sigrid)» en lugar del literal
  `sistema:normalizar_ubicacion`. Alternativa: el literal tal cual.
- **Q-8 · Normalizar desde la página.** Recomiendo **no**: ya corre sola tras
  cada importación y lo de la 0677 está normalizado; R15 se queda en tres
  rutas. Alternativa: un botón con ensayo y confirmación (cuarta ruta).
- **Q-9 · Valores fuera del catálogo en el formulario.** Recomiendo
  **conservarlos** como opción marcada «no está en la lista de Sigrid de
  hoy»; el backend los rechaza junto al campo si se guardan así.
  Alternativa: vaciarlos con aviso al abrir (riesgo de quitar la ubicación
  sin darse cuenta al corregir otra cosa).
- **Q-10 · El paso 03 de la tira en `bandeja.html`.** Recomiendo `<span>` sin
  `href` ni `aria-current` y ajustar la guardia de R85; y el 02 (actual) con
  `data-construccion` y `aria-label`, como la pestaña de R2 y como ya exige
  la guardia, aunque contradice la última frase de R87 de F-035 (un caso que
  hasta hoy no se había dado). Alternativas: 03 como enlace a `./#/bandeja`;
  o seguir la letra de R87 en el 02 y ajustar también esa parte de la
  guardia.

### 3 · Lo que queda fuera

- `services/postventa-api`: nada (ni hace falta). Si al implementar
  apareciera algo, bloqueo.
- Las specs de F-040 y F-057 no se tocan aquí: sus encajes quedan en §1.8.
- Lo del volcado más allá de Q-6, la normalización bajo demanda (Q-8) y el
  enlace profundo `?incidencia=` (F-057).
- `docs/INTEGRACION.md`: F-038 no añade rutas.
- P-4 (que la suite no lea el `.env`): sigue siendo un encargo aparte.

### 4 · Ficheros

- `specs/F-038-bandeja-revision/requirements.md`
- `specs/F-038-bandeja-revision/design.md` (§10, la conciliación)
- `specs/F-038-bandeja-revision/tasks.md`
- este informe; y una entrada en `progress/current.md`.

## Decisiones del humano · 2026-10-20

Recibidas por el líder el mismo día; aplicadas a la spec y **conciliación
cerrada**. En `design.md` §9 (tabla «Aprobadas por el humano el
2026-10-20») y §10.4.

| Id | Decidido | Dónde queda |
|---|---|---|
| **Q-6** | **(b) ampliada** (no la (a) recomendada): `volcada` y `en_duda` se ven en F-038 **con todo** —estado, «Volcada como <sigrid_cod> por <quien> el <fecha>» en hora de Madrid, el motivo de una `en_duda` si lo hay, y los filtros `volcada` y `en_duda`—; la presentación del volcado de R54 de F-040 pasa aquí. **Sin ninguna acción ni formulario** sobre ellas. Motivo del humano: «la idea es gestionar toda la postventa en el portal» | R4 (e), R6, **R21.1–R21.7** (incluye el último intento `rechazado`/`no_procesado` de una aprobada y los textos de los quince códigos de parte de `sigrid_api.md` §8.9, porque son lo que trae `volcado.motivo`); `design.md` §2.2, §2.4 (`lineaDeVolcado`, `textoMotivoVolcado`), §5, §6.9, §8; `tasks.md` **Bloque 1 ter** (T4 bis, T4 ter), T5 y T7 paso 5 |
| — | Editar o anular una incidencia ya volcada **no es de F-038**: ficha nueva que abre el líder aparte (backend y escritura en Sigrid); F-038 no espera por ella | `requirements.md` §3 («Ficha nueva (editar o anular partes ya volcados)», sin número); `design.md` §8 |
| **Q-7** | «el sistema (ubicación puesta en el texto exacto de Sigrid)» | R22 |
| **Q-8** | No se ofrece normalizar; R15 con tres rutas más `/.auth/me` | R15, R23 |
| **Q-9** | El valor fuera del catálogo de hoy se conserva como opción «no está en la lista de Sigrid de hoy»; el backend lo rechaza junto al campo | R24 |
| **Q-10** | Paso 03 `<span>` sin `href` ni `aria-current`; el 02 actual con `data-construccion` y `aria-label`; la guardia de R85 y la precisión de R87 se ajustan **como cambio a propósito de F-035**, declarado | R25; `tasks.md` T1 bis |

Lo que **no** se ha tomado de R54 de F-040: los textos de los motivos propios
del panel de F-059 (exclusiones de un ensayo, `MotivoExclusion`; ensayo no
válido, `MotivoEnsayoNoValido`), porque no salen en el objeto `volcado` de
`GET /api/revision` sino en las respuestas del panel: siguen en F-040.

**Reparto de `tasks.md` revisado.** El Bloque 1 de la spec del 2026-10-06
(T1–T5, todo de una vez) se parte, sin renumerar, en:

- **Bloque 1** · lo puro y la API (T1 RED, T2);
- **Bloque 1 bis** · la página y las guardias del portal (T1 bis RED, T3, T4);
- **Bloque 1 ter** · la presentación del volcado, Q-6 (T4 bis RED, T4 ter);
- **Bloque 1 quater** · mutación y `init.sh` por el líder (T5);

cada uno con su review y parada. Bloques 2 (publicar), 3 (verificar en
producción: diez pasos, con el 4 y el 5 nuevos) y 4 (cierre) como estaban.

**Queda abierto, fuera de F-038**: la conciliación de F-040 (soltar su R54);
la ficha nueva de editar o anular partes ya volcados (la abre el líder); P-4.
