<!-- progress/impl_F-013.md -->
# F-013 · Informe del implementer

> Rama `feature/F-013-archivo-posventa`. Rigor **`critico`**. Encargos por
> bloques: este informe crece bloque a bloque.

---

## Bloque 0 · T1 (2026-09-24)

**Alcance del encargo: solo T1.** T2 y T3 son del humano (MANUAL) y T4 es una
parada del líder. `harness/features.json` sin tocar. **No se ha ejecutado nada
contra Azure, Graph, Key Vault ni Sigrid**: los ensayos de abajo son locales,
con las llamadas de red sustituidas por datos inventados.

Commit: `553ce39` (`F-013 T1: scripts de solo lectura 23 … y 24 …`), más el de
este informe.

### 1 · Qué cambió

| Fichero | Qué |
|---|---|
| `infra/23_destino_posventa.ps1` (nuevo) | Medición T2 (R27, R28). URL → sitio y biblioteca, roles del token y, con `-CodigoObra`, el árbol **solo de carpetas** obra → `PARTES INCIDENCIAS` → unidades → `PARTES FIRMADOS`. Solo `GET` en Graph + el `POST` del token |
| `infra/24_ubicacion_sigrid.ps1` (nuevo) | Medición T3 (R32). Unidades de posventa de una obra (`upv` → `upv.obride`) con `con.cod`, `con.res` y nº de reclamaciones. Solo `sql/read`, vía `08_lectura_sigrid_comun.ps1` |
| `services/postventa-api/tests/test_f013_scripts_infra.py` (nuevo) | 44 tests del contrato de los dos scripts |
| `specs/F-013-archivo-posventa/tasks.md` | T1 marcada `[x]` |

`08_lectura_sigrid_comun.ps1` **no se ha tocado** (es de F-009 y lo cargan otros
nueve scripts): los dos nuevos lo cargan por punto y usan su veredicto, sus
códigos de salida, su TLS 1.2 y `Invoke-SigridLectura`.

### 2 · Cómo son los dos scripts

**`23_destino_posventa.ps1`**

- Parámetros: `-UrlSitio` (obligatorio salvo con `-WhatIf`),
  `-NombreBiblioteca` («Documentos compartidos»), `-CodigoObra`,
  `-CarpetaBase` (`""` = raíz, D-1), `-CarpetaIncidencias` («PARTES
  INCIDENCIAS»), `-CarpetaFirmados` («PARTES FIRMADOS»),
  `-MostrarIdentificadores`, `-WhatIf`. **Añadidos a lo que pedía el
  `design.md` §7.1**, y por qué, en §3: `-MostrarNombres`, `-DesdeKeyVault`,
  `-CarpetaObra`, `-MaxCarpetasObra`.
- Pasos: 1/4 token y roles (avisa de los amplios, F-018); 2/4 sitio por ruta
  (`GET /sites/{host}:/sites/<x>`) y bibliotecas (`/drives` y `/drive`); 3/4
  carpetas y ficheros de la base; 4/4 con `-CodigoObra`, el árbol. En cada
  nivel dice qué carpetas **casan** y cuáles son **parecidas** (§4.1, §4.2,
  §4.5), recorre también las parecidas (para que T2 vea qué hay dentro), cuenta
  los ficheros de cada hoja **sin nombrarlos**, marca las unidades **sin
  cifras** (riesgo 11: `VILLA CINCO`) y los **números de unidad repetidos**
  (D-6: saldrían ambiguas), y mira las versiones de **un** fichero para saber
  si hay versionado.
- Veredicto con el formato del 08: `PASA` si la aplicación ve el sitio,
  encuentra la biblioteca, tiene permiso de escritura en sitios, existe la base
  y —con `-CodigoObra`— hay **exactamente una** carpeta de obra que casa y
  **una** `PARTES INCIDENCIAS` que casa. Lo demás son datos (`(dato)`).
- Códigos de salida: 0 pasa, 3 parámetro, 5 `-CarpetaObra` inexistente, 6 no
  pasa, 7 credenciales o token, 8 Graph rechaza una lectura (403 lo explica
  como F-018), 9 sitio inexistente, 10 biblioteca no encontrada o ambigua.

**`24_ubicacion_sigrid.ps1`**

- Una consulta parametrizada que parte de `dbo.upv` (y no de `rcp`) para traer
  también las unidades **sin** reclamaciones, con el mismo camino que usará el
  adaptador (`design.md` §6.2): `upv.ide = con.ide` de la unidad,
  `upv.obride = con.ide` de la obra, y un `COUNT(*)` de reclamaciones de
  `tip = ?` por unidad.
- Pregunta el código **en sus dos formas** (`0677` y `677`) y dice si el que
  guarda Sigrid es **literalmente** el pedido: R10 compara literal.
- Dos obras con el mismo código (la 0677 tiene dos filas en el maestro) se
  rotulan «obra 1 / obra 2»: el `ide` del ERP no se imprime.
- Veredicto: al menos una obra y al menos una unidad; datos: nº de obras,
  código literal sí/no, unidades, unidades sin reclamaciones, reclamaciones,
  unidades cuyo `con.cod` no lleva cifras, unidades con **texto no reconocido**
  (posible nombre de persona → descarta `SHAREPOINT_NOMBRE_UNIDAD=nombre`, §4.6).

### 3 · Decisiones de diseño (y las añadidas a la spec)

1. **Nombres enmascarados por defecto (`-MostrarNombres` para el literal).** El
   encargo pide «ningún nombre de cliente en la salida por defecto», y el propio
   `design.md` §4.3 pone de ejemplo una carpeta `VILLA 05 - GARCÍA`.
   `ConvertTo-FormaSinNombres` conserva las palabras con cifras, las letras
   sueltas y un vocabulario de estructura (VILLA, BLOQUE, PORTAL, CHALET,
   PARTES, INCIDENCIAS, FIRMADOS…); el resto sale `<txt>`: `VILLA 05 - GARCIA`
   → `VILLA 05 - <txt>`, `0677 MIRASIERRA` → `0677 <txt>`. Es generosa a
   propósito. **Consecuencia**: para anotar en T2 el literal de la carpeta de
   obra (R36) hace falta `-MostrarNombres`, y por eso las líneas de §7 lo
   llevan.
2. **La máscara está copiada en los dos scripts**, no en el 08 (que es de F-009).
   `test_f013_t1_la_mascara_es_la_misma_en_los_dos` exige que las dos copias
   sean idénticas carácter a carácter.
3. **`-DesdeKeyVault` en el 23.** Las `GRAPH_*` salen de la sesión; con el
   interruptor, las que falten se leen con `az keyvault secret show` del vault
   de `00_vars_postventa.ps1` (nombres del mapa `$PostventaAppSettingsSecretas`,
   ninguno escrito en el script), capturadas en memoria. Si aun así falta
   alguna, se pide por consola (el secreto, como `SecureString`). Motivo: una
   línea `$env:GRAPH_CLIENT_SECRET = "..."` tecleada **queda en disco**, en el
   historial de PSReadLine.
4. **Reglas de casado provisionales en PowerShell.** Para medir antes de que
   exista el dominio (bloque 0) el 23 lleva una traducción directa de §4.1
   (obra: literal o código + blanco), §4.2 (tramo: igualdad de clave) y §4.5
   (parecidas). Lo dice en su cabecera y en su salida. **T14 las sustituye**
   por las del dominio vía `Invoke-PythonDelServicio`.
5. **`-CarpetaObra` y `-MaxCarpetasObra`.** Si la regla no encuentra la carpeta
   de la obra (o Posventa usa otra grafía), T2 puede forzar el literal y medir
   igual. Se recorren como mucho 5 carpetas de obra (casan + parecidas).
6. **La biblioteca se casa por URL** (`webUrl`), luego por nombre, y si pide la
   de por omisión y no casa ninguna, **la biblioteca por defecto del sitio**
   (`/sites/{id}/drive`). Si se pega la URL de la biblioteca
   (`…/Shared%20Documents/Forms/AllItems.aspx`) o un enlace de compartir
   (`/:f:/r/sites/…`), se entiende. Dice siempre por qué regla la eligió.
7. **Versionado**: Graph v1.0 no expone el ajuste de la biblioteca; se mira
   `/items/{id}/versions` de un fichero de una hoja: >1 versión → «sí»; 1 →
   «no concluyente».
8. **Del host del inquilino solo se imprime la ruta**; ni el `nextLink` (lleva
   el ID de la biblioteca) ni la URL de ninguna llamada fallida.

### 4 · Desviación respecto a la spec: **sin BOM**

T1 (`tasks.md:26-27`) y `design.md` §11 (`:701`) piden «UTF-8 con BOM y CRLF».
Los scripts salen **ASCII puro, CRLF y sin BOM**, como los otros 25 de
`infra/`. Motivo, **medido**: con BOM, `bash harness/init.sh` cayó en rojo
porque `tests/test_f010_prompt_keys_infra.py:77` lee **todos** los `.ps1` de
`infra/` con `encoding="ascii"` y la suite no llegaba ni a recolectar
(`UnicodeDecodeError: 'ascii' codec can't decode byte 0xef in position 0`).
`docs/CONVENTIONS.md` admite «excepciones documentadas», y `infra/` lo es de
hecho: ninguno de sus 25 scripts lleva BOM. Un fichero ASCII ya es UTF-8
válido y PowerShell 5.1 lo lee igual con o sin BOM.

No se ha tocado el test de F-010 (es de otra feature). **Para el líder**: si
se quiere BOM en `infra/`, el cambio es `encoding="utf-8-sig"` en ese test (y
revisar los demás que leen `.ps1` como `ascii`: `test_f006_scripts_infra.py`,
`test_f010_scripts_infra.py`), y probablemente enmendar T1/§11. El test de F-013
lo deja escrito con nombre: `test_f013_t1_sin_bom_como_el_resto_de_infra`.

Nota sobre el CRLF: el índice de git guarda LF en **todo** `infra/` y el CRLF
lo pone `core.autocrlf=true` al hacer checkout (`git ls-files --eol`:
`i/lf w/crlf`). El test de CRLF mira el árbol de trabajo, así que depende de esa
configuración, igual que el resto de `infra/`. Un `.gitattributes` con
`*.ps1 text eol=crlf` lo fijaría en cualquier máquina; no se ha añadido
(fuera de T1, afecta a todos los scripts; candidato también para `arnes-base`).

### 5 · Verificación

**Fase RED** — test escrito antes que los scripts. Comando exacto:

```
cd services/postventa-api && .venv/Scripts/python.exe -m pytest tests/test_f013_scripts_infra.py -q -p no:cacheprovider
```

Salida real (resumen y una traza; las 40 fallan por lo mismo):

```
E       FileNotFoundError: [Errno 2] No such file or directory: 'C:\\Users\\pgris\\PycharmProjects\\postventa-incidencias\\infra\\24_ubicacion_sigrid.ps1'
..\..\..\..\AppData\Local\Programs\Python\Python312\Lib\pathlib.py:1013: FileNotFoundError
=========================== short test summary info ===========================
FAILED tests/test_f013_scripts_infra.py::test_f013_t1_los_dos_scripts_existen[23_destino_posventa.ps1]
FAILED tests/test_f013_scripts_infra.py::test_f013_t1_los_dos_scripts_existen[24_ubicacion_sigrid.ps1]
FAILED tests/test_f013_scripts_infra.py::test_f013_t1_utf8_con_bom[23_destino_posventa.ps1]
[...]
FAILED tests/test_f013_scripts_infra.py::test_f013_r27_el_de_graph_solo_hace_get_mas_el_token
FAILED tests/test_f013_scripts_infra.py::test_f013_r27_el_de_graph_no_nombra_nada_que_suba_o_cree
FAILED tests/test_f013_scripts_infra.py::test_f013_r27_az_solo_para_leer_del_key_vault
[...]
FAILED tests/test_f013_scripts_infra.py::test_f013_r32_el_de_sigrid_solo_lee_por_sql_read
FAILED tests/test_f013_scripts_infra.py::test_f013_r32_la_consulta_va_parametrizada
FAILED tests/test_f013_scripts_infra.py::test_f013_r32_la_consulta_recorre_upv_hasta_la_obra
FAILED tests/test_f013_scripts_infra.py::test_f013_r32_la_cabecera_avisa_del_texto_libre
40 failed, 4 passed in 1.69s
```

Los 4 que pasaban en RED son los **controles negativos** de los patrones
(host, verbos, SQL), que no dependen de los scripts. `test_f013_t1_utf8_con_bom`
se renombró después a `…_sin_bom_como_el_resto_de_infra` (§4).

**GREEN** — el mismo comando: `44 passed in 0.29s`.

**Mutantes a mano** (la campaña del arnés no muta PowerShell). Inyectados en los
ficheros reales, uno a uno, con el test lanzado y el fichero restaurado byte a
byte (`cmp`) después:

| # | Mutante | Resultado |
|---|---|---|
| M1 | un `Invoke-RestMethod -Method Post` en `Get-Hijos` (crear carpeta) | **muere**: 2 failed |
| M2 | guardar el nombre de los ficheros en la lista de carpetas | **muere**: 1 failed |
| M3 | un `UPDATE dbo.con` en la consulta del 24 | **muere**: 1 failed |
| M4 | `Write-Identificadores` sin el `if ($MostrarIdentificadores)` | **muere**: 1 failed |
| M5 | el 24 con BOM | **muere**: 2 failed |

**PowerShell 5.1 real** (`5.1.26100.9549`), sin red:

- `Parser::ParseFile` de los dos: **0 errores de sintaxis**.
- `-WhatIf` de los dos, lanzados **desde `%TEMP%`** (comprueba el `chdir`):
  salida 0, «no se ha llamado a nada». El 23 descompone bien la URL de una
  biblioteca (`/sites/Postventa` + `Shared Documents`) y no imprime el host.
- **Ensayo completo con datos inventados**: una copia de los dos scripts en el
  scratchpad, con un `08` de mentira que carga el real y sustituye **solo**
  `Invoke-RestMethod`, `Invoke-SigridLectura`, `Get-SigridDestino` y
  `Get-SigridClave` (el falso `Invoke-RestMethod` lanza una excepción ante
  cualquier verbo que no sea `GET` o el token). Resultado del 23 (salida 0,
  `PASA`): paginación seguida (dos páginas), 18 llamadas, **todas `GET`** salvo
  el token; `0677 MIRASIERRA` casa, `0677-ANEXO` y `LISTADO 677` salen
  parecidas, `06770 NO` y `0680 OTRA` no; `PARTES DE INCIDENCIAS` parecida;
  unidades: `VILLA 05` con hoja y 3 ficheros **contados**, `VILLA 05 - <txt>`
  con hoja parecida, `VILLA 07` sin hoja, `VILLA <txt>` sin cifras y con hoja
  ambigua; número repetido `5`; versionado «sí (4 versiones)». Con
  `-MostrarIdentificadores` sale el bloque de IDs con el aviso de Key Vault;
  con `-MostrarNombres`, los literales. Resultado del 24 (salida 0, `PASA`):
  parámetros enviados `708 | 0677 | 677`; la unidad con un nombre inventado en
  `con.res` sale `Villa 7 - <txt> <txt>` y cuenta como «texto no reconocido»;
  `con.res` nulo → `(nulo)`; la segunda obra, guardada como `677 `, sale con
  «literal: NO».

**`bash harness/init.sh`**: en verde — **3.283 passed, 35 skipped en 110,48 s**;
PUERTA COBERTURA N/A (sin líneas Python de producción).

### 6 · Qué queda fuera y qué falta

- **Fuera de T1, a propósito**: la columna «resolvería / crearía (nombre) /
  bloquearía» (R28 completa) es **T14**, con la regla del dominio; hoy el 23 dice
  casan / parecidas / ambigua con reglas provisionales y, si no hay nada, «el
  sistema crearía la carpeta de obra (nombre: T14)».
- El 24 **no** tiene `-DesdeKeyVault`: usa el mecanismo del 08 (sesión o
  parámetro, y la clave por consola), el mismo con el que se lanzaron el 15, el
  16 y el 20.
- **Pendiente**: T2 y T3 (humano, §7) y la parada T4.

### 7 · Para el humano: T2 y T3 (MANUAL)

Las dos se lanzan **desde la raíz del repositorio**
(`C:\Users\pgris\PycharmProjects\postventa-incidencias`), en PowerShell. Ninguna
escribe nada. Se puede probar antes cada una añadiendo `-WhatIf` al final: no
llama a nada y dice qué variables faltan.

**T2 · qué necesita la sesión.** Las tres `GRAPH_*`: `GRAPH_TENANT_ID`,
`GRAPH_CLIENT_ID` y `GRAPH_CLIENT_SECRET`. **No hay que ponerlas a mano**: con
`-DesdeKeyVault` el script las lee del Key Vault del proyecto
(`graph-tenant-id`, `graph-client-id`, `graph-client-secret`) con la CLI de
Azure, en memoria, sin imprimirlas ni escribirlas. Requisitos: `az login` hecho
en esa consola y permiso para **leer secretos** de ese vault. Si no lo hay, el
script pide lo que falte por consola (el secreto, oculto). Lo que **no** hay que
hacer es teclear `$env:GRAPH_CLIENT_SECRET = "..."`: esa línea se guarda en disco,
en el historial de PSReadLine.

```
powershell -ExecutionPolicy Bypass -File infra\23_destino_posventa.ps1 -UrlSitio "<URL del sitio Postventa>" -CodigoObra 0677 -DesdeKeyVault -MostrarNombres
```

**T3 · qué necesita la sesión.** La raíz de la pasarela en
`$env:SIGRID_API_BASE_URL` (como en los guiones de F-009 y F-012); la clave de
`sigrid-api` la pide el script, oculta, si no está en `$env:SIGRID_API_KEY`. La
base va en la línea.

```
$env:SIGRID_API_BASE_URL = "<la raiz de la pasarela>"
```

```
powershell -ExecutionPolicy Bypass -File infra\24_ubicacion_sigrid.ps1 -CodigoObra 0677 -SigridBaseDatos ruesma -MostrarNombres
```

`-MostrarNombres` va en las dos porque T2 tiene que anotar el **literal** de la
carpeta de obra (R36) y T3 tiene que ver si `con.res` lleva nombres de persona
(§4.6). Lo que se anote en `progress/explore_F-013.md` va **sin identificadores
y sin nombres de cliente**; sin `-MostrarNombres`, la salida ya sale
enmascarada y se puede pegar tal cual. Con `-MostrarIdentificadores` el 23
imprime los ID del sitio y de la biblioteca **solo** para cargarlos en Key
Vault con `cargar_secretos_postventa.ps1 -Solo`.

### 8 · Para el líder: lo que ha quedado desfasado en la spec (no se ha tocado)

Desde que se escribió la spec se cerraron y desplegaron F-031, F-033 y F-034, y
el 2026-09-23 `desplegar_backend.ps1` pasó a dejar **abiertas por defecto** las
dos ventanas de escritura. Repaso con fichero y línea, **sin arreglar nada**:

1. **El corte, con las ventanas abiertas por defecto (lo más serio).**
   `design.md:487-496` (§7.3, pasos 4–6) y `tasks.md:192-205` (corte, pasos 4,
   5 y 5 bis) dan por hecho que, tras desplegar con
   `$EstructuraArchivo = "posventa"`, `ARCHIVO_HABILITADO` está cerrada y se
   abre «solo para el parte autorizado» (R33, `requirements.md:471`; R42,
   `:477`). Hoy `desplegar_backend.ps1:179-189` y `:489-496` la dejan
   **abierta**, y el comentario dice que Posventa ya usa el servicio en real:
   el primer archivado en la biblioteca de Posventa sería **el de cualquier
   usuario**, no el autorizado, y con `SHAREPOINT_CREAR_CARPETAS` encendido por
   omisión (D-4) podría **crear carpetas** antes de R42. El runbook tiene que
   decir cómo: `-VentanasCerradas` (cierra también la del ERP, que Posventa usa),
   cerrar solo la de archivo con `22_ventana_archivo.ps1` justo después, o
   desplegar primero con `SHAREPOINT_CREAR_CARPETAS=false`. Decisión del humano.
2. **Línea citada vieja.** `design.md:116` apunta a
   `infra/desplegar_backend.ps1:430`; `SHAREPOINT_CARPETA_BASE=Postventa` está
   hoy en **`:497`**.
3. **El orden del paso de archivo.** `design.md:370-378` (§5, tabla): la fila 3
   dice «L1 … **inerte** hoy; F-033», y ya no lo es; y falta el paso **1 bis**
   de F-031 (cotejo de códigos declarados). El orden real, en
   `application/pipelines/paso_archivo.py:222-248` y `:273-294`, es: puerta →
   cotejo → nombrado desde lo guardado → L1 → traza previa → carpeta → buscar →
   subir → traza final. El resolutor tiene que ir **después de L1** (si no, un
   parte ya archivado llamaría a Sigrid y listaría carpetas, contra lo que T15
   comprueba para R25) y **antes de la traza previa** (R22).
4. **De dónde salen los códigos.** `design.md:524-532` (§8.2) dice que F-013 usa
   `codigo_obra` y `numero_incidencia` «tal y como llegan al paso
   (`ctx.extraccion`)». Desde F-031 el paso los toma de `codigos_guardados(ctx)`
   (`paso_archivo.py:276`), y `tests/test_f031_alcance_cerrado.py:540-571`
   (R29, **se comprueba siempre**, sin git) **prohíbe** cualquier acceso a
   `.extraccion` en `paso_archivo.py`. El resolutor tiene que recibir los
   códigos **guardados**. El riesgo residual de §8.2 («un cuerpo que mienta en
   los dos») lo cerró F-031, y la recomendación de orden de `:534-538` ya se
   cumplió. El título `design.md:501` («F-033 (L1 inerte)») también se ha
   quedado viejo (la nota de `:510-514` lo matiza, el título no).
5. **Los tests que T10 tiene que mantener en verde.** `tasks.md:85-89` nombra
   `test_f006_*` y `test_f019_*`. Faltan los de F-031, F-033 y F-034, que fijan
   `paso_archivo.py`: F-031 R29 (arriba); F-033
   `NOMBRES_NUEVOS_Y_DONDE_VIVEN` (`tests/test_f033_alcance_cerrado.py:294-302`:
   `drive_id_vigente` solo puede vivir en `paso_archivo.py` y `archivar.py`; si
   el resolutor lo necesitara en `destino_archivo.py`, rompe); y F-034 R26
   (`tests/test_f034_alcance_cerrado.py:638`, compara `paso_archivo.py` con la
   base de **su** rama; debería saltarse fuera de ella, pero conviene
   comprobarlo al primer cambio del bloque 2).
6. **T15 y la precondición del bloque 5 ya se cumplen.** `tasks.md:121-126`
   («rebasar sobre `dev` con F-033… si F-033 no está mergeada, `blocked`») y
   `tasks.md:14-15`: F-033 está en `dev` y la rama sale de `dev` (`fadb678`).
   El rebase es trivial; T15 se puede hacer cuando toque sin esperar a nada.
7. **H-3 de F-034, sin sitio en la spec.** `progress/current.md:104-109`:
   `exigir_parte_archivado` (`application/pipelines/puerta_de_estado.py:185`)
   mira el **estado** de la traza pero no su **biblioteca**; un parte archivado
   en IT pasa la puerta del gráfico y del cierre igual que uno de Posventa. Con
   §9 bis (lo de IT se olvida) seguramente es lo querido, pero la spec de F-013
   no lo dice en ningún sitio. Decisión del humano, o una línea en §9 bis.
8. **Añadidos al 23 que la spec no nombra** (`design.md:439-464`, §7.1):
   `-MostrarNombres`, `-DesdeKeyVault`, `-CarpetaObra`, `-MaxCarpetasObra` y los
   tres parámetros de tramos/base. Y el **sin BOM** de §4 frente a
   `tasks.md:26-27` y `design.md:701`. Si el líder los acepta, conviene reflejarlos
   en §7.1 y §11 antes del bloque 6 (T17 documenta los dos scripts).

### Evidencias

| Evidencia | Valor |
|---|---|
| Tests de T1 | `test_f013_scripts_infra.py`: **44 passed** en 0,29 s (RED: 40 failed, 4 passed) |
| Suite del proyecto (`bash harness/init.sh`) | **3.283 passed, 35 skipped** en **110,48 s** (api); front en verde (caché); arnés 62 passed en 6,17 s |
| Cobertura de las líneas cambiadas | **N/A**: `PUERTA COBERTURA: N/A (F-013 no cambia líneas Python de producción frente a dev)`. T1 solo añade PowerShell y un test |
| Mutación (arnés) | `python -m harness.mutacion --feature F-013` (informe al scratchpad, para no adelantar el de T20): **0 ficheros, 0 líneas de producción, 0 mutantes**. El arnés solo muta `.py` de producción; la campaña de la feature es T20 |
| Mutación (a mano, PowerShell) | **5 mutantes inyectados, 5 muertos, 0 supervivientes** (§5) |
| Sintaxis PowerShell 5.1 | `Parser::ParseFile`: 0 errores en los dos |

---

## Bloque 1 · T5–T7 · Configuración y dominio puro (2026-09-24)

**Alcance del encargo: solo el Bloque 1.** No incluye nada del Bloque 2 (puertos,
resolutor, paso). Sin DDL, sin escrituras contra ningún sistema,
`harness/features.json` sin tocar. Ningún test toca la red.

Commits: `77c62dd` (T5), `4d86c99` (T6, en rojo, con la traza en el mensaje),
`cd00118` (estilo de T5: ruff), `a941acf` (T7), `0783c54` (T7: cierre de los
supervivientes de la mutación, §5), más el de este informe.

### 1 · Qué cambió

| Fichero | Qué |
|---|---|
| `services/postventa-api/config/settings.py` | Cinco campos: `sharepoint_estructura` (`"por_obra"`), `sharepoint_carpeta_incidencias` (`"PARTES INCIDENCIAS"`), `sharepoint_carpeta_firmados` (`"PARTES FIRMADOS"`), `sharepoint_carpeta_firmados_alternativa` (`"PARTES FIRMADO"`) y `sharepoint_crear_carpetas` (`True`). **Ninguno** llamado `sharepoint_nombre_unidad`. Descripción de `sharepoint_carpeta_base` actualizada (vacía = raíz, solo en `posventa`) y una nota fechada en el comentario de F-006 que decía que F-013 sería «cambiar tres variables» |
| `services/postventa-api/infrastructure/sharepoint/fabrica.py` | `_problemas_de_estructura`: una estrategia que no sea **exactamente** `por_obra`/`posventa` (R3) y una base vacía —o de solo blancos o barras— en `por_obra` (R17) → `ConfiguracionSharePointIncompleta`. Va dentro de la puerta 3 (configuración), **antes** de construir el adaptador, y en el mismo mensaje que las variables que falten. El orden entorno → interruptor → configuración no cambia |
| `services/postventa-api/domain/models/destino_posventa.py` (nuevo) | El dominio de `design.md` §2.1 y §4 (lista abajo). Solo biblioteca estándar y `nombrado.py` |
| `services/postventa-api/domain/models/errores.py` | `DestinoNoResuelto(motivo, detalle, candidatas=())`, con `candidatas` convertida en tupla; un párrafo en la docstring del módulo (familia 409) |
| `services/postventa-api/tests/test_f013_fabricas.py` (nuevo) | 37 tests: R1, R3, R17, R49 |
| `services/postventa-api/tests/test_f013_destino_dominio.py` (nuevo) | 246 tests: las tablas de `design.md` §4.1, §4.2, §4.3, §4.5, §4.6 y §4.7 enteras, fila a fila, más R9, R13/R14, R17, R18/R19, R35 (los cuatro obligatorios y los del recuadro), R36–R39, R44, R46 y R50 |
| `specs/F-013-archivo-posventa/tasks.md` | T5, T6 y T7 marcadas `[x]` |

**Lo que expone `destino_posventa.py`**: `EstructuraArchivo`, `MotivoDestino`
(los 22 códigos de R18, lista cerrada), `UbicacionReclamacion`, `UnidadDeObra`,
`PATRON_CODIGO_UNIDAD`, `clave_de_unidad`, `numero_de_obra`, `carpetas_de_obra`,
`parecidas_de_obra`, `carpeta_con_nombre`, `parecidas_de_tramo`,
`carpetas_de_unidad`, `parecidas_de_unidad`, `nombre_de_obra_nueva`,
`nombre_derivado_de_unidad`, `nombre_de_carpeta_admisible`,
`obras_del_mismo_numero`, `unidades_que_casan` y `unir_ruta`.

**Los controles de alcance de F-031, F-033 y F-034, sin tocarlos**: en verde
(28 passed; los 15 skipped son los controles del diff, que viven en las ramas de
esas features). El módulo nuevo no nombra ninguno de los identificadores
vigilados de `design.md` §2.3: R44 compara con `normalizar_codigo` y
`numero_de_obra`, nunca con `es_el_mismo_codigo`. Nada de este bloque ha chocado
con ellos.

### 2 · Decisiones de diseño (y lo que la spec no fijaba)

1. **`EstructuraArchivo` nace en T5**, sola, en `destino_posventa.py`: la
   fábrica la necesita para validar (R3), y la spec la coloca en ese módulo
   (§3.1). La lista de valores no se duplica en la fábrica. Por eso la fase RED
   de T6 es un `ImportError` del **resto** de nombres, no del módulo.
2. **La estrategia en `settings.py` es `str`, no el enum**: si fuera un tipo
   cerrado, un valor mal escrito tumbaría `/health` al leer los ajustes. Quien
   la valida es la fábrica, como con el resto de lo de SharePoint. Y la
   comparación es **exacta**: ni blancos ni mayúsculas se «arreglan»
   (`" posventa"` y `"POSVENTA"` → error). Falla cerrado.
3. **Dos funciones que la lista de §2.1 no nombra**, y que R36 y R38 necesitan
   en el dominio (T6 pide sus tests aquí): `nombre_de_obra_nueva(codigo,
   con_res)` —`<código normalizado> <con.res colapsado>`— y
   `nombre_de_carpeta_admisible`, que **delega** en `nombrado.nombre_admisible`
   (importada, no copiada: `design.md` §4.6). Sin `con.res`, el nombre de la
   obra acaba en blanco y R38 lo rechaza con `nombre_carpeta_imposible`, en vez
   de inventar un nombre.
4. **`parecidas_de_tramo` recibe también `alternativa`**. La firma de §4.5 es
   anterior a R49. Sin ella, la partición se rompería en la hoja:
   `PARTES FIRMADO` casaría **y** sería parecida. Solo sirve para excluir.
5. **`obra_ref` fuera del `repr` de `UnidadDeObra`** (`field(repr=False)`),
   con test: §3.3 y R23 dicen que no se loguea. Así, un `log.info("%s", fila)`
   descuidado no lo saca.
6. **Parecida de obra con código no numérico**: la spec dice «igualdad de
   token literal». Aquí es «las palabras del código aparecen seguidas entre las
   del nombre», sin mayúsculas ni tildes. Con un código de una palabra es
   exactamente la igualdad de token; con uno con guion (`AD-01`) es la
   generalización natural. Es generosa, como pide §4.5: su error cuesta un 409.
7. **Las secuencias de cifras de las reglas amplias se buscan tras NFKD**: una
   cifra de ancho completo (`６７７ MIRASIERRA`) no casa por la estricta (solo
   cifras ASCII, como exige §4.1), pero **sí** es parecida. Es más generoso que
   el `re.findall` literal de §4.5, nunca menos.
8. **Números de la unidad para la regla amplia**: si el `con.cod` cumple el
   patrón de R37 (solo el patrón, sin exigir que su obra sea la del parte), se
   toma su `<n>`; si no, los números de su clave, como antes. En los dos casos
   se añaden los del `con.res`.
9. **`numero_de_obra` normaliza** el código (`normalizar_codigo`, idempotente):
   `" 06 77 "` → 677, coherente con F-032 (un blanco no forma parte del código).
10. **Un código de obra vacío no casa con nada ni se parece a nada, y un tramo
    configurado vacío tampoco**: guardas explícitas, con test. El resolutor no
    debería llegar ahí (el nombrado falla antes), pero una clave vacía casaría
    con carpetas como `---`.
11. **Tramos: igualdad por `clave_de_unidad`**, tal cual dice §4.2. Un efecto
    que conviene saber: la puntuación también separa, así que
    `PARTES-INCIDENCIAS` **casa** con `PARTES INCIDENCIAS` (tienen la misma
    clave). Es la regla escrita y no se ha restringido; si el líder la quiere
    más estricta, es una enmienda.

### 3 · Fase RED (traza real)

**T5**. Comando exacto, desde `services/postventa-api`:

```
.venv/Scripts/python.exe -m pytest tests/test_f013_fabricas.py -q -p no:cacheprovider --tb=line
```

Salida real (extracto; líneas `E` y de fallo agrupadas):

```
E   KeyError: 'sharepoint_estructura'
E   KeyError: 'sharepoint_carpeta_firmados_alternativa'
E   AttributeError: 'Ajustes' object has no attribute 'sharepoint_crear_carpetas'
E   AttributeError: 'Ajustes' object has no attribute 'sharepoint_carpeta_firmados'. Did you mean: 'sharepoint_carpeta_base'?
tests\test_f013_fabricas.py:190: Failed: DID NOT RAISE ConfiguracionSharePointIncompleta      (x6, R3)
tests\test_f013_fabricas.py:289: Failed: DID NOT RAISE ConfiguracionSharePointIncompleta      (x5, R17)
tests\test_f013_fabricas.py:340: AssertionError: assert 'SHAREPOINT_ESTRUCTURA' in 'faltan variables para archivar en SharePoint: SHAREPOINT_DRIVE_ID. Se dicen los nombres y nunca los valores: uno de ellos es una credencial'
FAILED tests/test_f013_fabricas.py::test_f013_r3_estrategia_desconocida_falla_antes_de_construir_el_adaptador[otra]
FAILED tests/test_f013_fabricas.py::test_f013_r17_base_vacia_en_por_obra_es_error_de_configuracion[]
FAILED tests/test_f013_fabricas.py::test_f013_r49_la_alternativa_por_omision_es_la_de_villa_02
[...]
27 failed, 10 passed in 0.29s
```

Los 10 que ya pasaban en RED son los **controles positivos** (las dos
estrategias y la base con nombre construyen; la puerta del entorno sigue yendo
antes; la variable retirada no existe), que ya eran ciertos antes del cambio.
GREEN: **37 passed**.

**T6**. Comando exacto:

```
.venv/Scripts/python.exe -m pytest tests/test_f013_destino_dominio.py -q -p no:cacheprovider
```

Salida real, completa:

```
_____________ ERROR collecting tests/test_f013_destino_dominio.py _____________
ImportError while importing test module '...\tests\test_f013_destino_dominio.py'.
tests\test_f013_destino_dominio.py:31: in <module>
    from domain.models.destino_posventa import (
E   ImportError: cannot import name 'PATRON_CODIGO_UNIDAD' from 'domain.models.destino_posventa' (...\domain\models\destino_posventa.py)
=========================== short test summary info ===========================
ERROR tests/test_f013_destino_dominio.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.51s
```

Commiteado así (`4d86c99`, con la traza en el mensaje). GREEN tras T7:
**238 passed** (246 tras los tests que añadió la mutación, §5). Que las aserciones muerden —y no solo el import— lo demuestra
la campaña de mutación de §5.

### 4 · Verificación

| Comando (desde `services/postventa-api`) | Resultado |
|---|---|
| `pytest tests/test_f013_fabricas.py` | **37 passed** |
| `pytest tests/test_f013_destino_dominio.py` | **246 passed** |
| `pytest tests/test_f031_alcance_cerrado.py tests/test_f033_alcance_cerrado.py tests/test_f034_alcance_cerrado.py -rs` | **28 passed, 15 skipped** (controles del diff de sus ramas), sin tocarlos |
| `pytest tests/test_f006_fabrica.py tests/test_f025_sin_dry_run_previo.py tests/test_f005_ajustes.py` (los vecinos de la fábrica y de los ajustes) | en verde (93 passed junto con el de T5) |
| `python -m ruff check` sobre los seis ficheros tocados | All checks passed (el aviso global de 61 es deuda previa) |
| `bash harness/init.sh` (estado final, tras `0783c54`) | **ENTORNO LISTO**: api **3.566 passed, 35 skipped en 146,37 s**; PUERTA COBERTURA **100,0 % de 178 líneas cambiadas** (178/178, umbral 80 %, nivel `critico`). La pasada anterior, tras `a941acf`: 3.558 passed en 108,20 s, 182/182 |

### 5 · Mutación

La campaña formal de la feature es **T20** (bloque 7), y su informe,
`progress/mutacion_F-013.md`. Aquí se ha lanzado la del arnés sobre lo que
lleva la rama, **con el informe en el scratchpad** para no adelantar el de T20
(el mismo criterio que en T1). Alcance recalculado por la herramienta: rama
`fadb678..feature/F-013-archivo-posventa`, 4 ficheros de producción
(`settings.py`, `destino_posventa.py`, `errores.py`, `fabrica.py`).

**Primera pasada** (`python -m harness.mutacion --feature F-013`, 8 workers,
sobre `a941acf`): **56 mutantes, 47 muertos, 9 supervivientes**, 0 timeouts,
1.862,4 s. Análisis, uno a uno:

| # | Línea y mutación | Análisis | Qué se hizo |
|---|---|---|---|
| 1 | `destino_posventa.py:240` `len(recortado) > len(codigo)` → `>=` | **Equivalente**: se evalúa solo si `recortado != codigo` y empieza por `codigo`, así que ya es más largo. La guarda era redundante | Se quita la guarda (con un comentario de por qué el índice existe) |
| 2 | `:275` `range(len - largo + 1)` → `range(len + largo + 1)` | **Equivalente**: las ventanas de más dan cortes más cortos, que no pueden ser iguales a `buscadas` (no vacía) | `_contiene_seguidas` pasa a ser una búsqueda de texto con las palabras unidas por un blanco (las palabras no llevan blancos): sin aritmética |
| 3 | `:275` `… + 1` → `… + 2` | **Equivalente**, por lo mismo | Íd. |
| 4 | `:354` `endswith("S") and len > 1` → `or` | **Hueco real**: ningún test tenía una palabra de tramo **sin** `S` final (`FIRMADOS` e `INCIDENCIAS` acaban en `S`) | Test nuevo, `test_f013_r35_la_palabra_del_tramo_sin_su_s_final` (`ARCHIVO`: se usa entera) |
| 5 | `:354` `len > 1` → `>= 1` | **Hueco real** en la guarda del prefijo vacío (palabra que es solo `S`) | Íd. (`PARTES S`) |
| 6 | `:354` `len > 1` → `> 2` | **Hueco real**, una palabra de dos letras acabada en `S` | Íd. (`HOJA OS`) |
| 7 | `:355` `[:-1]` → `[:-2]` | **Hueco real**: se quita exactamente una `S` | Íd. (`CLASES` → `CLASE`, y `CLAS` no es parecida) |
| 8 | `:381` `not clave or not any(…)` → `and` | **Hueco real**: ningún test tenía una carpeta **sin número** que casara por la regla 1 o fuera sufijo del nombre. `not clave` era redundante (una clave vacía no tiene números) | Test nuevo `test_f013_r11_sin_numero_no_casa_aunque_sea_sufijo_del_nombre` y se quita `not clave` |
| 9 | `:386` `len(clave) <= len(nombre)` → `<` | **Hueco real**: ningún caso con la carpeta igual al `con.res` entero (el sufijo trivial de R39). La guarda de longitud era redundante (un corte más largo que el nombre da el nombre entero, distinto de la clave) | Tests nuevos `…_la_carpeta_con_el_nombre_entero_de_la_unidad_casa` y `…_una_carpeta_mas_larga_que_el_nombre_no_casa`, y se quita la guarda |

Las 4–7 se cierran además reescribiendo la línea como
`clave_buscada[-1].removesuffix("S") or clave_buscada[-1]`, sin enteros ni
comparaciones. **Comprobado a mano antes de simplificar**: cada superviviente
del 4 al 9, reinyectado en el fichero real (y el fichero restaurado byte a byte
después, `cmp`), lo mata al menos uno de los tests nuevos. El 6 sobrevivía a
la primera versión de esos tests y hubo que añadirle la fila `HOJA OS`.
Commit `0783c54`: sin cambio de comportamiento, 246 tests del dominio en verde.

**Segunda pasada** (misma orden, 8 workers, sobre `0783c54`, con el árbol
limpio): **43 mutantes, 43 muertos, 0 supervivientes, 0 timeouts**, 3.511,9 s.
Los 40 timeouts de la pasada paralela se repasaron en serie y los 40 salieron
muertos (el repaso mide el mutante y no la carga de la máquina). Informe
generado: en el scratchpad, `mutacion_F-013_bloque1_v2.md`; **no** se ha
escrito `progress/mutacion_F-013.md`, que es de T20.

### 6 · Qué queda fuera y qué falta

- **Fuera, a propósito (Bloque 2 en adelante)**: los puertos
  `ExploradorBibliotecaPort` y `UbicacionPort`, los dobles y el árbol medido
  como dato compartido (T8); el resolutor, que es quien convierte lo que
  devuelve este dominio en los 409 de `MotivoDestino`, y el caso de conjunto de
  las 15 unidades (T9); el paso (T10). Nada de este bloque se usa todavía
  desde producción: `destino_posventa.py` solo lo importa la fábrica (por
  `EstructuraArchivo`) y `SHAREPOINT_ESTRUCTURA` sigue valiendo `por_obra` por
  omisión, así que el comportamiento desplegable no cambia.
- **No se ha tocado** `.env.example` ni `local.settings.json.example` con las
  variables nuevas: la spec no lo pide en T5 y T17 es la tarea de
  documentación. Si el líder quiere que figuren, es una línea por variable.
- **Para el líder, sin bloquear**: la decisión 11 de §2 (`PARTES-INCIDENCIAS`
  casa por la clave de §4.2) y la 6 (parecida de un código no numérico con
  varias palabras). Las dos siguen lo escrito, o su generalización más
  directa; si se quieren de otra forma, es una enmienda con test.
- **Verificaciones MANUAL**: ninguna en este bloque.

### Evidencias

| Evidencia | Valor |
|---|---|
| Tests del bloque | `test_f013_fabricas.py` **37 passed** (RED: 27 failed, 10 passed); `test_f013_destino_dominio.py` **246 passed** (RED: `ImportError` en la recogida) |
| Controles de alcance de F-031, F-033 y F-034 | **28 passed, 15 skipped** (los del diff, fuera de sus ramas), sin tocarlos |
| Suite del proyecto (`bash harness/init.sh`, estado final) | api **3.566 passed, 35 skipped en 146,37 s**; front en verde (caché); arnés 62 passed en 5,54 s |
| Cobertura de las líneas cambiadas | **`PUERTA COBERTURA: 100.0% de 178 líneas cambiadas cubiertas (178/178, umbral 80%, nivel critico)`** |
| Mutación, primera pasada (8 workers) | 56 generados, 47 muertos, **9 supervivientes**, 0 timeouts, 1.862,4 s; los 9 analizados arriba |
| Mutación, segunda pasada (8 workers) | **43 generados, 43 muertos, 0 supervivientes**, 0 timeouts (40 repasados en serie, todos muertos), 3.511,9 s |
| Mutantes a mano | supervivientes 4–9 reinyectados contra los tests nuevos: todos mueren (el 6, tras añadir la fila `HOJA OS`) |
| ruff sobre los ficheros tocados | All checks passed |
