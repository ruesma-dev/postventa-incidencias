<!-- progress/review_F-051.md -->
# F-051 · La carpeta base vacía no llega a la Function · Review 1

- **Veredicto:** CHANGES_REQUESTED
- **Resumen en una línea:** el **código es correcto y no hay que tocarlo**
  (incidente reproducido y arreglado desde el handler; F-006 y F-013 intactos;
  traza limpia y emitida solo con el destino aceptado; guarda del despliegue
  sana). Lo que falta es documental y de verificación, y es justo la familia
  de fallo del incidente: **el paso que comprueba el despliegue no está
  demostrado que pueda ver la traza**, y las verificaciones MANUAL no constan
  en `progress/current.md` con su comando. Tres cambios, todos de texto
  (§5); con ellos, una review 2 corta.
- Rama `feature/F-051-carpeta-base-raiz` en `e41d655`, frente a `dev`
  (`a468367`). azure-apps: commit local `59e9a8f`.

## 1 · Nivel de rigor

`critico`, declarado en `harness/features.json`. Exige: C1–C5 y C3 bis;
tests trazables; **fase RED** con salida real; **cobertura** de lo cambiado;
**mutación** verificada de forma independiente, **cero supervivientes** sin
aceptación **escrita** del humano (también los mutantes a mano); mutaciones
de **orden** a mano (regla 7) donde el requisito central es un orden; y
verificaciones MANUAL con su comando exacto.

## 2 · Lo que he verificado yo (no copiado del informe)

| Comprobación | Resultado |
|---|---|
| `bash harness/init.sh` | exit 0, `ENTORNO LISTO`; `PUERTA COBERTURA: 100.0% de 14 líneas cambiadas (14/14, umbral 80%, nivel critico)`. El servicio api salió por caché («árbol sin cambios»), así que lancé la suite aparte |
| Suite del servicio api, sin caché | **4415 passed, 52 skipped**, 73 s |
| F-051 + vecinas (`test_f051_*`, `test_f013_fabricas`, `test_f013_documentacion`, `test_f006_fabrica`, `test_f033_archivar_http`) | 236 passed, **0 skipped** (los tests que ejecutan PowerShell corren de verdad) |
| Tests de F-051 | 17 + 10 + 21 + 11 = 59, como dice el informe |
| **Reproducción del incidente desde el handler** (test propio en el scratchpad: `archivar_parte` **sin** archivador inyectado, la fábrica de verdad con el adaptador de Graph cambiado por un doble explorador) | **En `dev`** (worktree desechable): `posventa` sin la variable → `ArchivoFallido: la carpeta «Postventa» no existe en la biblioteca…`, el mismo texto de los 502. **En la rama**: `posventa` con la variable ausente, `/`, vacía y ` / ` → primer listado `""`, archivado en `<obra>/PARTES INCIDENCIAS/VILLA 05/PARTES FIRMADOS`, traza `… estructura posventa, carpeta base raíz`. `por_obra` sin variable → `Postventa/0677`, traza `«Postventa»`. `por_obra` con `/`, vacía, blancos y ` / ` → `ConfiguracionSharePointIncompleta`, adaptador no construido, **sin traza**. Ventana de archivo cerrada → sin traza. 10/10 |
| La mitigación de producción (`/`) con el código de `dev` | en `dev`, `posventa` + `/` **sí** archiva en la raíz (solo le falta la traza): la mitigación es correcta también en código |
| Otros lectores de `sharepoint_carpeta_base` (el campo pasa a `str \| None`) | solo `fabrica.py` (vía `carpeta_base_efectiva`) y `archivar.py` (ídem, dos sitios). Ningún `.strip()` sobre `None` posible. `paso_archivo` solo usa `carpeta_base` en `componer_destino` (`por_obra`) |
| Mutación: recálculo puro | `harness.alcance`: 3 ficheros, **86** líneas, rama `a468367..feature/F-051`; `generar_mutantes`: **3** (fabrica.py:122 `comparacion`, :218 `logico`, :218 `not`). Coinciden con el informe |
| Mutación: campaña reejecutada (57 s < 5 min) | `python -m harness.mutacion --feature F-051 --workers 3 --salida <scratchpad>`: **3 generados, 3 muertos, 0 supervivientes, 0 timeouts, 80,0 s**. Coinciden. Coste por mutante 80 × 3 / 3 = 80 s, del orden de la suite (73 s): sana |
| Control del «generador roto» | no aplica (no es cero), pero lo hice igual: sobre los ficheros enteros salen 35 |
| **Regla 7 · mutaciones de orden de la traza** (a mano, worktree desechable, solo tests de F-051) | traza movida **antes de la puerta de entorno**, **antes del interruptor** y **antes de `_exigir_configuracion`**: las tres caen (1 failed, `test_f051_t2_si_la_fabrica_se_niega_no_hay_traza`) |
| Mutaciones a mano de `desplegar_backend.ps1` (worktree desechable) | guarda **después** de `appsettings set` → cae; `Carpeta-Base-Para-Azure` devuelve tal cual → cae (2); la guarda con `IsNullOrEmpty` en vez de `IsNullOrWhiteSpace` → cae (2); la guarda que nunca aborta → cae; `SHAREPOINT_CARPETA_BASE=$CarpetaBaseArchivo` → cae (2). 5/5 |
| PowerShell 5.1 (5.1.26100.9549), ejecución real de las dos funciones extraídas del script (`-File`) | `$null`, `""`, `"   "`, `"/"` → `/`; `" / "` → `" / "` (el servicio la recorta); `Postventa` → `Postventa`. `App-Settings-Vacias` sobre `CREAR=`, `X=  `, `"KV="`, `SINIGUAL` y una referencia de Key Vault entre comillas → las cuatro primeras, no la referencia; sobre `A=1, B=/` → ninguna |
| Superviviente a mano del implementer (`archivar.py`, `carpeta_base=… or "Postventa"` en el paso) | **equivalente en producción**, confirmado leyendo `paso_archivo.py:354-359`: `carpeta_base` solo entra en `componer_destino` (`por_obra`), y `por_obra` con base puesta a vacía no llega al paso (R17 en la fábrica; lo he visto caer en mi reproducción). Falta la aceptación **escrita** del humano (§4) |
| `ruff` desde la raíz (como `init.sh`) sobre los 9 `.py` tocados | `All checks passed!` (desde `services/postventa-api` salen 6 `I001` por la detección de first-party; en `dev` salen igual: no es de F-051) |
| Barrido de identificadores en el diff y en `59e9a8f` | GUID, correos, IPv4, `print(`, `TODO`, `password`, `sig=`: **0** en lo añadido (los aciertos fueron `@pytest…` y un `"secreto-inventado"` de test). Ningún GUID en los documentos (lo fija además `test_f051_t4_ningun_documento_lleva_un_guid`) |
| Ficheros añadidos en la rama (`git log --diff-filter=A dev..HEAD`) | 4 tests y 2 informes de `progress/`. Ningún PDF ni parte |

## 3 · Respuestas a lo que pedía el líder

**El incidente.** Reproducido desde el handler con la fábrica real (tabla de
§2). Sin la variable y con `posventa`, la ruta listada es la raíz; con
`por_obra` sin variable, `Postventa`; `/` y vacía: raíz en `posventa`,
rechazo en `por_obra`. Y en `dev` el mismo test da el error literal de
producción.

**Que no cambie nada más de F-006/F-013.**
- `carpeta_base_efectiva` solo decide la **ausencia**; un valor puesto pasa
  tal cual y el recorte sigue en `unir_ruta`/`carpeta_de_archivo`. R17 se
  evalúa sobre la base efectiva: ausente en `por_obra` pasa (`Postventa`),
  puesta a vacía o `/` se rechaza, como antes. R3 (estrategia desconocida) va
  antes y no cambia. D-1 (la raíz en `posventa`) se mantiene.
- Tests de otras features ajustados (§4 del informe), **sin relajar**:
  `test_f013_r1_la_estrategia_por_omision_es_la_de_hoy` pasa de afirmar el
  campo (`== "Postventa"`, que era el mecanismo del incidente) a afirmar la
  base efectiva en `por_obra` (`== "Postventa"`): protege lo mismo, R1/R2.
  Los cuatro de `test_f013_documentacion.py` cambian `""` → `"/"` y
  `$CarpetaBaseArchivo` → `$carpetaBaseAppSetting` con la **misma** fuerza
  (presencia exacta en `$ajustes`, dos líneas «Destino del archivo»).
  `test_f051_scripts_infra` añade además que la variable cruda **no** se
  escribe ni se enseña. `test_f006_fabrica` y `test_f033_archivar_http` no
  se tocaron y pasan (siguen poniendo `Postventa` explícita).

**La traza.** `F-051 destino efectivo del archivo: estructura <e>, carpeta
base raíz|«<nombre>»`. Sin drive, sitio, tenant, cliente ni secreto (test que
lo recorre en DEBUG). Se emite **después** de las tres puertas y justo antes
de construir el adaptador: lo he comprobado moviéndola por encima de cada
puerta (regla 7, las tres caen) y en mi reproducción (rechazo y ventana
cerrada: sin traza). El paso 6 busca exactamente esa línea:
`test_f051_t4_el_paso_6_busca_la_traza_que_emite_la_fabrica` genera la traza
con la configuración del corte y exige que el texto del paso la contenga
literalmente; la KQL filtra por `has "F-051 destino efectivo del archivo"`.

**`desplegar_backend.ps1` y la decisión 4.** Nunca escribe la base vacía:
`Carpeta-Base-Para-Azure` convierte vacía o en blanco en `/`, y eso es lo
que va a `$ajustes` y lo que enseñan las dos líneas «Destino del archivo».
Sobre la guarda genérica `App-Settings-Vacias`: he repasado **todo** lo que
escribe el script. Es una sola llamada `az functionapp config appsettings
set` con `$ajustes`: 13 literales con valor fijo; `$TIEMPO_*_S` (35);
`$ventanaArchivo`/`$ventanaCierre` (`"true"`/`"false"`, nunca vacías);
`$EstructuraArchivo`, `$carpetaBaseAppSetting` y `$CrearCarpetasArchivo` de
`00_vars_postventa.ps1`; `$identidadCliente` (de `az identity show`); y las
once referencias a Key Vault, que nunca salen vacías (llevan el prefijo
`@Microsoft.KeyVault(`). **Ninguna App Setting se escribe vacía a propósito
hoy**, así que la guarda no rompe ningún despliegue legítimo. Los dos casos
en que saltaría son justo los que hay que parar: un `00_vars_postventa.local.ps1`
que deje vacía `$EstructuraArchivo` o `$CrearCarpetasArchivo` (Azure la
descartaría y el código usaría `por_obra` o su defecto en silencio, el mismo
incidente con otro nombre), o un `$identidadCliente` vacío (la identidad no
resolvería el Key Vault). Va antes de fijar nada, con `Salir-Con` y
`$SALIDA_FALLO`. **De acuerdo con la decisión 4.** Fuera de su alcance, y no
es regresión: `19_ventana_escritura.ps1` y `22_ventana_archivo.ps1` escriben
`true`/`false`, y `desplegar_front.ps1` escribe las de la Static Web App.

**PowerShell 5.1 (F-029).** F-051 no pasa ningún programa ni ninguna comilla
doble embebida a un ejecutable nativo: `/` va sin comillas en `--settings`;
las referencias de Key Vault siguen con su entrecomillado de antes, y la
guarda las desnuda solo para mirar el valor. La KQL se lanza en el portal y
no por `az monitor app-insights query`, precisamente por F-029 (decisión 6):
correcto. Los tres `.ps1`, ASCII + CRLF + sin BOM (test) y las funciones
ejecutadas de verdad en 5.1 (por el implementer y por mí).

**Documentación y azure-apps.** `INTEGRACION.md` y `azure-apps/postventa_incidencias.md`
(`59e9a8f`) llevan los mismos cambios y coinciden con el código: fila
«Carpeta base» con `SHAREPOINT_CARPETA_BASE=/` (o ausente) y «nunca vacía»;
el recuadro de §3 describe exactamente la regla de `carpeta_base_efectiva` y
el rechazo de R17; la fila de riesgos, actualizada; enmienda tras la de F-013
de §4. `DESPLIEGUE.md` §9: paso 5 con `"/"` y «carpeta base '/'» (lo que
imprime el script con `"/"`), paso 6 reescrito. `.env.example` y el
comentario de `00_vars` coherentes. El árbol de `azure-apps` está limpio y
`59e9a8f` es local (sin push, como debe).

## 4 · Checkpoints

### C1 — El arnés está completo y en verde
- [x] `bash harness/init.sh` exit 0.
- [x] Existen los siete ficheros base.

### C2 — El estado es coherente
- [x] Una sola feature `in_progress` (F-051).
- [x] Rama `feature/F-051-carpeta-base-raiz`.
- [x] `progress/current.md` empieza por el bloque del incidente y de F-051
      (los bloques de abajo son la historia que este repo conserva ahí, como
      en las reviews anteriores).
- [x] Toda feature `done` con resumen en `history.md` (sin cambios aquí).

### C3 — Arquitectura y convenciones
- [x] Hexagonal: la regla vive en `infrastructure/sharepoint/fabrica.py` (la
      fábrica decide estrategias, el dominio no sabe de ellas, `design.md`
      §2.3 de F-013); el borde (`interface_adapters`) la consume. Dominio sin
      tocar.
- [x] Primera línea con la ruta en los 12 ficheros de código tocados.
- [x] Sin `print()`, sin TODOs, sin secretos, sin dependencias nuevas.
- [x] La unidad es el parte (no cambia).
- [x] Nada se archiva sin las validaciones: la fábrica sigue rechazando antes
      de construir; ninguna escritura en Sigrid.
- [x] Lo manuscrito / firmado no es conforme / reprocesar no duplica /
      `conest`: N/A **justificado**: F-051 no toca extracción, validación,
      deduplicación ni cierre.
- [x] Ningún parte ni PDF en git (`git log --diff-filter=A dev..HEAD`).

### C3 bis — Documentos de fuera
- N/A **justificado**: F-051 no añade ni modifica nada en `docs/referencia/`.

### C4 — La verificación es real
- [x] Cada `acceptance` con ≥ 1 test trazable y en verde (tabla de §6).
- [x] Sin red ni BBDD: dobles y `monkeypatch`; los de PowerShell ejecutan
      funciones extraídas en un `.ps1` temporal, sin `az`.
- [ ] **Las verificaciones MANUAL (humano) no están en `progress/current.md`
      con su comando exacto.** El bloque de F-051 (líneas 14-19) dice «el paso
      6 de DESPLIEGUE §9 la busca en Application Insights (KQL)», sin el
      comando de despliegue, sin la consulta y sin la salida esperada. Están
      en `progress/impl_F-051.md` §8 y en `DESPLIEGUE.md`, pero el checkpoint
      pide `current.md`, que es lo que se tiene delante el día del
      despliegue. Cambio 1.

### C4 bis — El rigor declarado se cumple
- [x] `rigor: critico` declarado.
- [x] Fase RED con salida real en T1 (el mismo `ArchivoFallido` de
      producción), T2 y T3. T4 (documentación) sin RED estricta, declarado
      en §4 del informe: aceptable, no es requisito central y sus tests los
      he hecho caer yo con las mutaciones de `desplegar_backend.ps1`.
- [x] Cobertura `[OK]` 100 % (14/14).
- [x] `progress/mutacion_F-051.md` generado por la herramienta; totales
      recalculados (86 líneas, 3 mutantes) y coincidentes.
- [x] Campaña reejecutada por mí (57 s < 5 min): 3/3/0/0, coincide.
- [x] Coste por mutante 57 × 3 / 3 = 57 s (el mío, 80 s), del orden de la
      suite: no sospechosa.
- [ ] **Cero supervivientes salvo aceptación escrita del humano.** La campaña
      del arnés, 0. Pero el complemento a mano trae **1 superviviente
      declarado equivalente** (`archivar.py`, el `carpeta_base=` del paso). Lo
      he comprobado y **estoy de acuerdo en que es equivalente** (§2), pero en
      `critico` hace falta la aceptación **escrita** del humano. No es trabajo
      del implementer: §5, punto 4.
- [ ] **«Evidencias» sin el número de workers.** La fila de mutación dice
      `--base dev --max-mutantes 40` y 57,0 s, pero no con cuántos workers; y
      ese comando **no es** el que figura en la cabecera del informe generado
      (`--workers 3`). El dato está en `mutacion_F-051.md` (3), pero el
      checkpoint lo pide en «Evidencias». Cambio 2.
- [x] Ningún N/A sin motivo en este bloque.

### C4 ter — Rutas sensibles
- N/A **justificado**: no existe `harness/rutas_sensibles.json` (solo el
  `.ejemplo`), así que no hay declaración y `init.sh` no señala nada.

### C5 — Cierre
- [x] `tasks.md`: N/A **justificado**, `sdd=false`; commits `F-051 T1..T4:`
      más alta e informe, uno por tarea.
- [x] Sin temporales ni artefactos sin trackear (`git status` limpio; mis
      worktrees y salidas, en el scratchpad y retirados).
- [x] `features.json`: `in_progress`, que es el estado real.

## 5 · Cambios requeridos

Ninguno toca código de producción ni tests de producción.

1. **`progress/current.md`, bloque de F-051 (líneas 14-19): las MANUAL con su
   comando exacto y su salida esperada**, en este orden:
   - **(nuevo, ANTES de desplegar, solo lectura)** probar que una línea
     `INFO` de este logger llega a `traces`. La de F-006 sale del **mismo**
     logger (`infrastructure.sharepoint.fabrica`), al **mismo** nivel y en el
     **mismo** sitio desde F-006, y el 2026-10-01 tuvo que salir en cada una
     de las 90 peticiones (la fábrica pasaba: `posventa` con base
     `Postventa` no salta R17). En el portal, `appi-postventa-dev` →
     Registros:
     `traces | where timestamp > ago(3d) | where message has "F-006 archivador de SharePoint construido" | summarize n = count() by bin(timestamp, 1h)`.
     Tiene que salir algo el 2026-10-01. **Si no sale nada, el paso 6 no
     puede funcionar** como está escrito (la traza no llegaría aunque F-051
     estuviera desplegada) y hay que decirlo antes de desplegar, no después.
   - el despliegue (`infra\desplegar_backend.ps1`) y la línea «Destino del
     archivo: estructura 'posventa', carpeta base '/', crear carpetas 'true'»;
   - la KQL del paso 6 y su salida esperada (`… estructura posventa, carpeta
     base raíz`), con el freno 1 si dice un nombre;
   - con Posventa: el parte en su carpeta y el cierre en Sigrid.
2. **`progress/impl_F-051.md` §9 «Evidencias»**: el número de workers (3) y
   el comando con que **de verdad** se generó `mutacion_F-051.md`
   (`--workers 3`, según su cabecera), o explicar la diferencia con el que
   figura ahora (`--base dev --max-mutantes 40`).
3. **`docs/DESPLIEGUE.md` §9, paso 6, rama «si no sale ninguna línea»**
   (≈ línea 893): hoy da dos causas (la versión no lleva F-051, o el
   muestreo). Falta la tercera, que es la que confundiría al humano: **que
   las trazas `INFO` de la aplicación no lleguen a `traces`**. Añadirla, con
   la comprobación del punto 1 (la línea de F-006) como forma de
   distinguirla, y qué hacer entonces: la verificación pasa a ser el
   resultado (un `200` de `archivar` en `requests` y el parte en su carpeta
   con Posventa), no se da el corte por bueno sin ninguna de las dos. Es la
   misma lección del incidente: un paso de verificación que no puede ver lo
   que dice verificar. Opcional en el mismo cambio: si la consulta no
   devuelve nada, repetirla con `contains "destino efectivo del archivo"`
   antes de concluir (descarta cualquier sorpresa del `has` con el guion de
   `F-051`).
4. **(Humano, no implementer)** aceptación **escrita** del superviviente a
   mano equivalente de `progress/mutacion_F-051.md` (`archivar.py`, el
   `carpeta_base=` del paso). Mi análisis coincide con el del implementer.

Hallazgos bajos, **no bloquean**:
- H-1. `specs/F-013-archivo-posventa/` (requirements D-1, design §7.3 y
  D-1, tasks paso 5) sigue diciendo `SHAREPOINT_CARPETA_BASE=""` /
  `$CarpetaBaseArchivo = ""` sin recuadro que remita a F-051. F-049 sí dejó
  recuadros fechados en F-013. Quien relea la spec para un corte nuevo
  pondría `""`; hoy el script lo convierte en `/`, así que no hay daño, pero
  conviene un recuadro de una línea.
- H-2. `verificar_destino_sharepoint.ps1` con `por_obra` y la raíz da un
  aviso en rojo pero no cambia el RESULTADO ni el código de salida. Está bien
  así (solo lee), pero no es una puerta.

## 6 · Cobertura: acceptance → tests

| Acceptance | Tests |
|---|---|
| 1 · `posventa` sin la variable = raíz | `test_f051_a1_posventa_sin_la_variable_lista_la_raiz_y_archiva` (handler), `test_f051_a1_la_fabrica_construye_con_posventa_y_sin_la_variable`, `test_f051_la_base_efectiva_por_estrategia[posventa-ausente-raiz]`, `test_f051_la_base_ausente_se_lee_como_ausente` |
| 2 · `por_obra` sin la variable = `Postventa` | `test_f051_a2_por_obra_sin_la_variable_sigue_en_postventa` (handler), `test_f051_a2_la_fabrica_construye_con_por_obra_y_sin_la_variable`, `…[por_obra-ausente-postventa]`, `test_f013_r1_la_estrategia_por_omision_es_la_de_hoy` |
| 3 · `/` y vacía: raíz en `posventa`, rechazo en `por_obra` | `test_f051_a3_barra_y_vacia_son_la_raiz_en_posventa[barra,vacia]`, `test_f051_a3_barra_y_vacia_se_rechazan_en_por_obra[barra,vacia]`, más los de R17 de `test_f013_fabricas.py` |
| 4 · el despliegue no escribe la base vacía | `test_f051_t3_el_despliegue_escribe_la_base_ya_resuelta`, `…_la_base_vacia_se_escribe_como_barra`, `…_el_despliegue_ensena_lo_que_escribe`, `…_ninguna_app_setting_vacia_llega_a_azure`, `…_la_guarda_mira_el_valor_y_no_el_nombre`, `…_las_dos_funciones_se_ejecutan_en_powershell`, `…_las_variables_declaran_la_raiz_como_barra` |
| 5 · traza del destino efectivo y el guion la verifica | `test_f051_t2_la_fabrica_traza_el_destino_efectivo[7 casos]`, `…_el_incidente_se_habria_visto_en_la_traza`, `…_la_traza_no_lleva_ningun_identificador`, `…_si_la_fabrica_se_niega_no_hay_traza`; `test_f051_t4_el_paso_6_busca_la_traza_que_emite_la_fabrica`, `…_la_consulta_kql_es_de_solo_lectura_y_busca_la_traza`, `…_el_paso_6_dice_que_la_configuracion_no_basta`. **Que la traza llegue a Application Insights no lo cubre ningún test**: es el cambio 1 (MANUAL previa) |
| 6 · documentación y azure-apps | `test_f051_t4_el_paso_5_declara_la_raiz_como_barra`, `…_la_fila_de_la_carpeta_base_dice_barra[INTEGRACION, azure-apps]`, `…_hay_dos_recuadros_fechados_del_incidente`, `…_ningun_documento_lleva_un_guid`; los cuatro ajustados de `test_f013_documentacion.py`; lectura mía de `59e9a8f` |
| 7 · `init.sh` en verde | ejecutado: exit 0 |

## 7 · Lo que debe mirar el humano al desplegar

1. **Antes**: la consulta de la línea de F-006 (cambio 1). Si el
   2026-10-01 no aparece, no se puede confiar en el paso 6: parar y avisar.
2. Lanzar el despliegue **desde la rama mergeada** y comprobar, antes de
   escribir `DESPLEGAR`, «carpeta base '/'». Si el script se para con «App
   Settings sin valor: …», no forzarlo: es la guarda nueva, y el nombre que
   cite es el que va vacío en `00_vars_postventa(.local).ps1`.
3. La App Setting ya está en `/` por la mitigación: el despliegue la deja
   igual. Lo que cambia es el código (la ausencia ya sería la raíz) y la
   traza.
4. Tras el primer archivado, la KQL del paso 6: tiene que decir
   `estructura posventa, carpeta base raíz`. Cualquier nombre entre «»:
   freno 1 (`infra\22_ventana_archivo.ps1 -Cerrar`).
5. Los ~20 partes del 2026-10-01: se vuelven a archivar desde la aplicación;
   no se escribió nada a medias y el cierre va detrás del archivo.
6. Aceptar por escrito (o no) el superviviente equivalente (cambio 4).

## 8 · Propuesta de automejora (no aplicada)

A `CHECKPOINTS.md`, C4, para las features cuya verificación MANUAL dependa
de que **una traza llegue a un sistema de observabilidad**: exigir una
comprobación previa de que una traza **del mismo logger y nivel**, ya
existente, llega hoy a ese sistema. Un test puede fijar el texto de la
línea, pero no que el canal la transporte; sin esa prueba, el paso de
verificación puede volver a ser «mirar algo que no puede ver», que es
exactamente el incidente que arregla F-051. Vale para cualquier proyecto con
Application Insights: candidata a `arnes-base` si el humano la aprueba.
