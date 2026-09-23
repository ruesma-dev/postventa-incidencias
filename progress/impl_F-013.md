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
