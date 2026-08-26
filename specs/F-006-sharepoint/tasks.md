<!-- specs/F-006-sharepoint/tasks.md -->
# F-006 · Nombrado y archivo en SharePoint — Tareas

> Rigor **`critico`**: los tests se escriben **antes** que el código y la
> **traza real en rojo** de cada tarea RED se pega en `progress/impl_F-006.md`.
> Un «se hizo TDD» sin traza es un checkbox vacío (`CHECKPOINTS.md` C4 bis).
>
> Una tarea = un commit `F-006 Tn: ...`. Rama `feature/F-006-sharepoint`.
>
> La suite del servicio se ejecuta así (desde la raíz del repositorio):
> `cd services/postventa-api && .venv/Scripts/python.exe -m pytest -q`
>
> **21 tareas, 6 de ellas con fase RED**: T2, T4, T6, T9 y T11 en rojo por
> código que aún no existe, y **T13 en rojo por rotura deliberada** (el
> entregable de esa tarea es el propio test). **Tres son `MANUAL (humano)`**:
> T17, T18 y T19.
>
> **PRECONDICIÓN DURA**: F-004 y F-005 mergeadas en `dev`, en ese orden (ver
> `design.md` §1). Es **T1**, y si no se cumple la feature se marca `blocked`.
>
> **REGLA QUE ATRAVIESA TODAS LAS TAREAS**: ninguna tarea, ni un comando de
> verificación, ni una prueba «solo por ver si va», sube nada a SharePoint
> desde una máquina de desarrollo. La única subida real permitida es **T18**,
> desde el entorno desplegado y contra el destino de dev.
>
> **El humano trabaja en PowerShell**: no admite `&&` y parte los comandos
> largos al pegarlos. Por eso **cada verificación manual se entrega como un
> script** más **una línea corta** para invocarlo.

---

## Fase 0 · Precondición

- [x] **T1**: Comprobar que `dev` trae ya F-004 y F-005, y **rebasar** esta
      rama sobre `dev`. F-006 consume `ResultadoValidacion`, `Veredicto`,
      `Destino` (F-004) y `TrazaArchivo`, `EstadoArchivo`,
      `RepositorioPartesPort.guardar_archivo`, la tabla `postventa.archivos` y
      `docs/INTEGRACION.md` (F-005).
      **Verificación**: desde la raíz,
      `git log --oneline dev | head -20` muestra los merges de F-004 y F-005;
      `cd services/postventa-api && .venv/Scripts/python.exe -c "from domain.models.validacion import Destino; from domain.models.persistencia import TrazaArchivo, EstadoArchivo; print('ok')"`
      imprime `ok`, y `bash harness/init.sh` sigue en verde.
      **Si falta cualquiera de las dos: `blocked`.** No se inventa un modelo
      gemelo para poder empezar antes (`design.md` §1).

---

## Fase 1 · El nombrado (dominio puro)

- [x] **T2 · RED**: Escribir `tests/test_f006_nombrado.py` (R1–R9), con
      **ejemplos inventados y marcados como tales**:
      - `test_f006_r1_el_nombre_sigue_la_convencion_de_posventa`: obra `0677` e
        incidencia `RS26.08/0123` → `0677 - RS26.08 - 0123 PARTE FIRMADO.pdf`.
      - `test_f006_r2_la_barra_del_numero_de_incidencia_pasa_a_guion`: la barra
        **no aparece** en el nombre resultante.
      - `test_f006_r3_los_guiones_no_normales_se_normalizan`: `RS26.08 – 0123`
        (guion largo `U+2013`), `RS26.08 — 0123` y `RS26.08 − 0123` producen
        **el mismo** nombre que la versión con barra.
      - `test_f006_r4_los_ceros_a_la_izquierda_del_codigo_de_obra_se_conservan`
        y `test_f006_r4_la_carpeta_conserva_los_ceros`: nunca `677`.
      - `test_f006_r5_el_sufijo_y_la_extension_van_literales`.
      - `test_f006_r6_sin_codigo_de_obra_no_se_nombra` y
        `test_f006_r6_sin_numero_de_incidencia_no_se_nombra`: `None`, `""` y
        `"   "` levantan `NombradoImposible` **nombrando cuál falta**.
      - `test_f006_r7_un_caracter_prohibido_no_se_sanea_en_silencio`.
      - `test_f006_r8_los_espacios_redundantes_colapsan`.
      - `test_f006_r9_el_nombrado_es_puro_y_deterministico`: mil llamadas con
        las mismas entradas dan el mismo resultado; la función no recibe
        configuración ni reloj.
      **Verificación**: rojo por `ModuleNotFoundError`; **traza pegada** en
      `progress/impl_F-006.md`.

- [x] **T3**: Implementar `domain/models/nombrado.py` (`design.md` §4.2) y
      añadir `NombradoImposible` a `domain/models/errores.py`.
      **Verificación**: `.venv/Scripts/python.exe -m pytest tests/test_f006_nombrado.py -q`
      en verde, y la suite completa sin regresiones.

---

## Fase 2 · El puerto, el paso y la idempotencia

- [x] **T4 · RED**: Escribir `tests/utiles_sharepoint.py` con **`BibliotecaFalsa`**
      (`design.md` §6.4: un diccionario `ruta -> elemento` que **imita** el
      comportamiento real — reemplazar pisa y conserva `item_id`, renombrar
      crea `nombre (1).pdf`, `asegurar_carpeta` es idempotente y cuenta
      creaciones), más `ArchivoPortFalso` y `RepositorioFalso`. Y escribir
      `tests/test_f006_paso_archivo.py` (R10–R18, R23, R24, R27):
      - `test_f006_r10_la_carpeta_es_base_mas_codigo_de_obra`.
      - `test_f006_r11_la_carpeta_se_crea_si_no_existe` y
        `test_f006_r12_pedir_la_carpeta_dos_veces_deja_una_sola` (la falsa
        cuenta **una** creación).
      - `test_f006_r13_la_identidad_del_parte_es_el_hash_de_f002`.
      - `test_f006_r14_con_traza_archivada_no_se_vuelve_a_subir`: el doble
        **no recibe ninguna llamada** y el resultado trae el aviso.
      - `test_f006_r15_subir_dos_veces_deja_un_solo_elemento`: **la biblioteca
        falsa acaba con exactamente un elemento y ningún nombre con `(1)`**.
      - `test_f006_r15_nunca_se_pide_renombrar`.
      - `test_f006_r16_mismo_nombre_otro_hash_reemplaza_con_aviso`.
      - `test_f006_r17_un_parte_no_apto_no_se_archiva` y
        `test_f006_r17_un_parte_no_apto_no_crea_carpeta`: con
        `Destino.COLA_VALIDACION_HUMANA` y con `Destino.REVISION_MANUAL`, sale
        `ParteNoApto` y el doble **no recibe ni una llamada**.
      - `test_f006_r18_sin_validacion_no_se_archiva`.
      - `test_f006_r23_la_traza_de_exito_lleva_todo_lo_declarado`.
      - `test_f006_r24_un_fallo_deja_traza_de_error_y_permite_reintentar`.
      - `test_f006_r27_el_destino_sale_de_configuracion`: cambiar
        `carpeta_base` cambia la carpeta sin tocar el paso.
      **Verificación**: rojo; **traza pegada** en `progress/impl_F-006.md`.

      > `test_f006_r15_subir_dos_veces_deja_un_solo_elemento` es **el test que
      > más importa de la feature**: es el `acceptance` 3 escrito como
      > comportamiento observable, no como aserción sobre una constante.

- [x] **T5**: Implementar `domain/ports/archivo.py` (`ItemArchivado`,
      `ArchivoPort`), `application/pipelines/paso_archivo.py` (`design.md` §6.2,
      los ocho pasos **en ese orden**), añadir `ParteNoApto` y `ArchivoFallido`
      a `domain/models/errores.py` y `archivo: TrazaArchivo | None` a
      `application/pipelines/contexto_parte.py`.
      **Verificación**: `.venv/Scripts/python.exe -m pytest tests/test_f006_paso_archivo.py -q`
      en verde, y la suite completa también.

---

## Fase 3 · La puerta que impide subir desde local

- [x] **T6 · RED**: Escribir `tests/test_f006_fabrica.py` (R19, R20, R28):
      - `test_f006_r19_en_entorno_local_la_fabrica_no_construye_el_adaptador`:
        con `ENTORNO=local` (y con `test`) sale `ArchivoDeshabilitado`.
      - `test_f006_r19_el_constructor_del_adaptador_tambien_muerde`: construir
        `AdaptadorSharePointGraph` **a mano**, saltándose la fábrica, también
        levanta `ArchivoDeshabilitado`. Es el único test de la suite que
        nombra la clase real, y lo hace para comprobar que **no** se deja
        construir.
      - `test_f006_r20_por_defecto_el_archivo_esta_deshabilitado`: sin
        `ARCHIVO_HABILITADO`, `ajustes.archivo_habilitado is False` y la
        fábrica se niega.
      - `test_f006_r28_configuracion_incompleta_falla_nombrando_la_variable`:
        con `ENTORNO=dev` y `ARCHIVO_HABILITADO=1` pero sin
        `SHAREPOINT_DRIVE_ID`, sale `ConfiguracionSharePointIncompleta`
        nombrando la variable, y **el valor de `GRAPH_CLIENT_SECRET` no
        aparece en el mensaje** ni entero ni en fragmentos.
      **Verificación**: rojo; **traza pegada** en `progress/impl_F-006.md`.

- [x] **T7**: Ampliar `config/settings.py` con los ajustes de `design.md` §7
      (todos **opcionales en el modelo**, `archivo_habilitado` por defecto
      `False`), actualizar `.env.example` y `local.settings.json.example` con
      **placeholders y ningún valor**, y escribir
      `infrastructure/sharepoint/fabrica.py` (`construir_archivador`,
      `ENTORNOS_CON_ARCHIVO`) más `ConfiguracionSharePointIncompleta` y
      `ArchivoDeshabilitado` en `domain/models/errores.py`.
      **Verificación**: los tests de T6 en verde. `.env` **no se toca** y
      `git status` no lo muestra.

---

## Fase 4 · El adaptador de Graph

- [x] **T8**: ~~Declarar `msal>=1.28,<2.0` y `requests>=2.31,<3.0`~~ →
      **DECISIÓN DEL HUMANO DEL 2026-08-20**: se declara **`httpx`**, no `msal`
      ni `requests`. El servicio no tenía cliente HTTP y `partes` ya resuelve
      esto en producción con `httpx`; se cierra así la decisión abierta **D1**
      de `design.md` §10. Declarado `httpx>=0.27,<1.0` en
      `services/postventa-api/requirements.txt` e instalarlos en el venv del
      servicio. **Si la decisión abierta D1 dice que el ecosistema usa otra
      librería, se cambia aquí y solo aquí**: el puerto aísla al resto.
      **Verificación**:
      `cd services/postventa-api && .venv/Scripts/python.exe -m pip install -r requirements-dev.txt`
      termina bien, `.venv/Scripts/python.exe -c "import msal, requests; print('ok')"`
      imprime `ok`, y la suite sigue en verde.

- [x] **T9 · RED**: Escribir `tests/test_f006_adaptador_graph.py` (R11, R12,
      R15, R16, R25, R26) contra `ClienteGraphFalso` y con
      `espera_inicial_s=0`, **con `ENTORNO=dev` forzado solo en ese fichero**
      (es lo que hace construible el adaptador; la red la sigue impidiendo la
      guardia de F-003):
      - la carpeta se crea si el `GET` da `404`, y un `409 nameAlreadyExists`
        se trata como éxito (R12);
      - la subida manda **siempre** el comportamiento de conflicto
        «reemplazar»; ningún camino manda «renombrar» (R15);
      - `buscar` devuelve `None` ante un `404` y el elemento ante un `200`;
      - un `429` y un `503` se reintentan y la siguiente respuesta vale (R25);
      - un `403` y un `404` **no** se reintentan: el doble registra **una**
        llamada (R25);
      - agotados los reintentos sale `ArchivoFallido`;
      - `test_f006_r26_el_error_no_lleva_contenido_ni_datos_personales`: el
        mensaje no contiene los bytes del parte, ni un DNI inventado, ni el
        texto de unas observaciones inventadas;
      - `test_f006_r26_el_log_no_lleva_la_credencial`: se captura el logger y
        se comprueba que ni el token simulado ni el secreto simulado aparecen.
      **Verificación**: rojo; **traza pegada** en `progress/impl_F-006.md`.

- [x] **T10**: Implementar `infrastructure/sharepoint/graph.py`
      (`design.md` §8.1), **con la puerta de entorno en el propio
      constructor** (§5, puerta 1).
      **Verificación**: los tests de T9 en verde. Ningún test abre red (la
      guardia de F-003 lo garantiza) y ninguno sube nada.

---

## Fase 5 · El borde HTTP

- [x] **T11 · RED**: Escribir `tests/test_f006_archivar_http.py` (R30, R31)
      con **los cinco caminos**, uno por test, todos con dobles inyectados:
      200 con el contrato exacto de `design.md` §8.2; 400 sin fichero; 409 con
      parte no apto; 409 con nombre imposible; 503 con archivo deshabilitado;
      502 con fallo del proveedor. En los cuatro caminos de error, el doble
      **no recibe ninguna llamada de subida** y la respuesta **no lleva el
      contenido del parte**.
      **Verificación**: rojo; **traza pegada** en `progress/impl_F-006.md`.

- [x] **T12**: Implementar `interface_adapters/api/archivar.py` (handler +
      composición, con los dos puertos inyectables como costura de test) y
      añadir la ruta `archivar` en `function_app.py` con el mapeo a
      400 / 409 / 502 / 503.
      **Verificación**: los tests de T11 en verde y la suite completa también.

---

## Fase 6 · Arquitectura y datos personales

- [x] **T13 · RED (por rotura deliberada)**: Escribir
      `tests/test_f006_arquitectura.py` (R21, R22, R26, R29, R32):
      - `test_f006_r21_la_suite_no_puede_abrir_conexiones` con un
        `ArchivoPort` delante: la guardia de F-003 sigue mordiendo.
      - `test_f006_r21_ningun_test_construye_el_adaptador_real`: barrido de
        `tests/*.py` buscando `AdaptadorSharePointGraph(`; el **único**
        fichero autorizado es `test_f006_fabrica.py` (T6), que lo construye
        precisamente para comprobar que se niega.
      - `test_f006_r22_dominio_y_aplicacion_no_conocen_graph`: recorrido con
        `ast` de `domain/` y `application/` — ni `msal`, ni `requests`, ni
        `httpx`, ni `infrastructure`.
      - `test_f006_r22_solo_infrastructure_sharepoint_importa_graph`.
      - `test_f006_r26_ningun_fichero_del_servicio_incrusta_un_identificador`:
        barrido de `services/postventa-api/**` buscando patrones de GUID; solo
        pueden aparecer nombres de variable.
      - `test_f006_r29_los_ejemplos_de_entorno_no_traen_valores`: en
        `.env.example` y `local.settings.json.example`, cada variable nueva
        tiene placeholder y ningún GUID ni secreto.
      - `test_f006_r32_integracion_declara_el_consumo_de_sharepoint`: existe
        `docs/INTEGRACION.md`, tiene sección de SharePoint, nombra las
        variables y **no** contiene ningún GUID.
      **Verificación**: como el entregable **es** el test, la fase RED se
      demuestra **rompiendo deliberadamente lo que vigilan, en una copia
      aislada del árbol, nunca en el árbol real** (`CHECKPOINTS.md` C4 bis):
      añadir `import requests` a un módulo de `domain/` copiado y pegar la
      traza del fallo en `progress/impl_F-006.md`.

---

## Fase 7 · Documentación (parte del trabajo, no un «luego»)

- [x] **T14**: Actualizar `docs/ARCHITECTURE.md`: `infrastructure/sharepoint/`
      en el árbol; paso 5 con la regla de la barra, la de los ceros y la del
      sufijo; paso 6 con las tres capas de idempotencia; y en la tabla de
      sistemas externos, la fila de SharePoint con las variables de destino y
      **la puerta de entorno** (`ENTORNO` + `ARCHIVO_HABILITADO`) que impide
      subir desde local.
      **Verificación**: el diff del documento lo refleja y `bash harness/init.sh`
      sigue en verde.

- [x] **T15**: Añadir a **`docs/INTEGRACION.md`** (el documento que crea F-005,
      **no se crea otro**) la sección «SharePoint (Microsoft Graph)»: qué sitio
      y qué biblioteca **por nombre de variable**, qué identidad (app-only), qué
      permisos, qué carpeta base, qué volumen se espera (una remesa real son 22
      partes), y **qué se rompe si alguien cambia la biblioteca o revoca el
      permiso**. Cabecera con origen y fecha, según la regla 2 de
      `azure-apps/README.md`.
      **Verificación**: `test_f006_r32_integracion_declara_el_consumo_de_sharepoint`
      en verde, y **ni un GUID, ni un secreto, ni un tenant** en el documento
      (lo comprueba el mismo test).

- [x] **T16**: Escribir los dos scripts de verificación manual en `infra/`,
      **sin un solo valor dentro**: leen todo de variables de entorno de la
      sesión del humano y **no imprimen nunca el token ni el secreto**.
      - `infra/verificar_destino_sharepoint.ps1` — **solo lectura**: pide token
        app-only, resuelve el sitio y la biblioteca, lista la raíz y dice si la
        carpeta base existe. **No sube nada.**
      - `infra/verificar_archivo_dev.ps1` — llama **dos veces** a
        `POST /api/archivar` **del servicio desplegado** (parámetro `-BaseUrl`)
        con un PDF sintético, y comprueba que el `item_id` es el mismo las dos
        veces y que en la carpeta hay **un solo** elemento.
      **Verificación**: `powershell -File infra\verificar_destino_sharepoint.ps1 -WhatIf`
      imprime la ayuda y las variables que necesita, **sin llamar a nada**; y
      un barrido de los dos ficheros no encuentra ningún GUID ni credencial.

---

## Fase 8 · Verificaciones MANUAL (humano)

> Las tres se ejecutan **en PowerShell**. Se entregan como **script + una línea
> corta**, porque los comandos largos se parten al pegarlos y PowerShell no
> admite `&&`.
>
> **T17 depende de una decisión abierta del humano** (D6 de `design.md` §10).
> Si no está resuelta, queda **PENDIENTE DEL HUMANO** y se anota así en
> `progress/current.md`: no se sustituye por una prueba local.
>
> **T18 · EJECUTADA EL 2026-08-25** dentro del trabajo de F-010 y con
> autorización expresa ante C5. Lo que sigue describe por qué estuvo diferida
> hasta ese día; el resultado real está en la propia tarea, abajo.
>
> **T18 ya no depende de una decisión abierta: está DIFERIDA.** El humano
> resolvió **D3** el **2026-08-19** por la opción **(a)** (`design.md` §10):
> F-006 se implementa y se cierra con **T18 declarada y PENDIENTE**, y esa
> verificación se ejecuta **cuando F-010 despliegue el entorno**. No está
> olvidada ni pendiente de decidir: está **aplazada por decisión del humano,
> con fecha**. Sigue firme que subir desde local «solo para probar» **no** es
> una opción.

- [ ] **T17 · MANUAL (humano) · LISTA PARA EJECUTAR** — *(**D6 RESUELTA el
      2026-08-20**: la biblioteca de dev, el app registration y los permisos ya
      existen, así que esta tarea **ya no está bloqueada**)*. Confirmar que el
      destino de dev existe y que la identidad tiene permiso, **solo con
      lecturas**. El script no sube, no crea y no borra nada, y hay un test que
      lo comprueba (`test_f006_t17_el_script_del_destino_no_escribe_nada`).

      **Paso 1** — en la sesión de PowerShell, fijar las cinco variables. Los
      valores los tiene el humano; **no se pegan en ningún informe, en ningún
      commit y en ningún chat**:

      ```
      $env:GRAPH_TENANT_ID     = "<tenant>"
      $env:GRAPH_CLIENT_ID     = "<aplicacion>"
      $env:GRAPH_CLIENT_SECRET = "<secreto>"
      $env:SHAREPOINT_SITE_ID  = "<sitio>"
      $env:SHAREPOINT_DRIVE_ID = "<biblioteca>"
      ```

      **Paso 2** — copiar el script fuera del repositorio y ejecutarlo:

      ```
      copy infra\verificar_destino_sharepoint.ps1 $HOME\
      ```

      Línea de invocación:

      ```
      powershell -ExecutionPolicy Bypass -File $HOME\verificar_destino_sharepoint.ps1
      ```

      Para ver antes qué va a hacer, **sin llamar a nada**:

      ```
      powershell -ExecutionPolicy Bypass -File $HOME\verificar_destino_sharepoint.ps1 -WhatIf
      ```

      **Resultado esperado**: imprime el nombre del sitio y de la biblioteca,
      la lista de permisos concedidos a la aplicación, y las tres líneas
      finales `biblioteca_localizada`, `carpeta_base_existe` y
      `permiso_escritura: True`. **No sube nada.**

      **Se espera además un aviso en amarillo** sobre `Sites.ReadWrite.All` y
      `Sites.FullControl.All`: es el **riesgo aceptado** del 2026-08-20
      (`design.md` §9, riesgo 7), y lo recorta **F-018**. Que salga es lo
      correcto; que **no** salga significaría que los permisos ya se
      recortaron.

      El resultado real se anota en `progress/current.md` **sin
      identificadores**: solo «biblioteca localizada: sí/no», «carpeta base:
      existe/no existe», «permiso de escritura: sí/no» y «permisos amplios
      presentes: sí/no».

- [x] **T18 · MANUAL (humano) · DIFERIDA A F-010 · EJECUTADA EL 2026-08-25** — *(D3 resuelta el
      **2026-08-19**, opción **(a)**)*. **La única subida real de toda la
      feature**, y **la única tarea de F-006 que queda sin ejecutar al
      cerrarla**. Se ejecuta **contra el servicio desplegado** y **sobre el
      destino de dev**, nunca desde local:

      **Cuándo**: cuando **F-010** haya desplegado el entorno de dev y exista
      una URL de despliegue. Antes de eso **no se puede ejecutar y no se
      sustituye por nada**. Al cerrar F-006, esta casilla queda `[ ]` y así
      debe quedar: es una verificación **aplazada**, no olvidada.

      **Comando previsto** (el script `infra/verificar_archivo_dev.ps1` sí se
      entrega dentro de F-006, en T16; lo que se difiere es *ejecutarlo*):

      ```
      copy infra\verificar_archivo_dev.ps1 $HOME\
      ```

      Línea de invocación (sustituyendo la URL del despliegue de dev):

      ```
      powershell -File $HOME\verificar_archivo_dev.ps1 -BaseUrl <url-de-dev>
      ```

      **Criterio de verificación** — qué se comprueba y contra qué destino:
      se comprueba que **el nombrado y la idempotencia funcionan de verdad
      contra una biblioteca real**, no contra el doble de test. El destino es
      la **biblioteca de dev dentro del sitio de IT** (la de D6), a través del
      **servicio desplegado por F-010**; nunca el archivo real de Posventa y
      nunca desde una máquina de desarrollo. La tarea se da por verificada si
      y solo si se cumplen los tres puntos siguientes **con resultado real
      anotado**, y hasta entonces sigue `[ ]`.

      **Resultado esperado**, con un parte **sintético** (obra `0677`,
      incidencia `RS26.08/0001`, ambos inventados):
      - primera llamada: `200`, `nombre_fichero = 0677 - RS26.08 - 0001 PARTE
        FIRMADO.pdf`, `carpeta = Postventa/0677`, `estado = archivado`;
      - segunda llamada: `200`, **el mismo `item_id`**, aviso de «ya estaba
        archivado»;
      - listado de la carpeta: **un solo elemento**, y **ningún** nombre con
        `(1)`.

      **Si aparece un `(1)`, es una parada**: se habla con el humano antes de
      seguir. Ese es exactamente el fallo que el `acceptance` prohíbe, y no se
      arregla con más tests.

      El resultado real se anota en `progress/current.md` **el día que se
      ejecute, dentro del trabajo de F-010**, y solo entonces se marca esta
      casilla. **No se pega la URL del despliegue, ni el `item_id`, ni ningún
      identificador.**

      > **EJECUTADA POR EL HUMANO EL 2026-08-25, DENTRO DEL TRABAJO DE F-010, Y
      > CON AUTORIZACIÓN EXPRESA.** Esta casilla llevaba `[ ]` desde el cierre
      > de F-006 el 2026-08-19 por la opción (a) de D3, esperando el entorno
      > desplegado. Ya no espera a nada.
      >
      > **La autorización que exigía el cierre**: el humano autorizó el
      > **2026-08-25** con la fórmula literal «**autorizo T18 ante
      > `CHECKPOINTS.md` C5**». Es la autorización expresa, nombrando C5 y
      > dejada por escrito, que pide la sección «El cierre de F-006 necesita
      > autorización expresa del humano (C5)» de este mismo documento.
      >
      > **Cómo se ejecutó**: **no** con `verificar_archivo_dev.ps1 -BaseUrl`,
      > que es lo que preveía el «comando previsto» de arriba y que **ya no
      > puede funcionar**. Desde que la Function App es backend enlazado de la
      > Static Web App, la plataforma le activa Easy Auth y su host desnudo
      > responde `400 Login not supported for provider azureStaticWebApps` a
      > todo (es el **defecto 13** de F-010). La vía real fue **la consola del
      > navegador en el front, con sesión iniciada**, que va al mismo origen y
      > pasa por el proxy que autentica. El fragmento está en
      > `docs/DESPLIEGUE.md` §5 bis y el detalle en
      > `specs/F-010-despliegue/tasks.md`, T18.
      >
      > **Los tres puntos del «Resultado esperado», contra el resultado real**:
      >
      > | Lo que pedía | Lo que pasó |
      > |---|---|
      > | 1.ª llamada `200`, `0677 - RS26.08 - 0001 PARTE FIRMADO.pdf`, `Postventa/0677`, `estado = archivado` | **Cumplido** al tercer intento. Los dos primeros no llegaron: `400` por el host desnudo (defecto 13) y `500` por el `ForeignKeyViolation` del defecto 15, este último **con el PDF ya subido y bien nombrado** |
      > | 2.ª llamada `200`, **el mismo destino**, aviso de que ya estaba | **Cumplido**: `200`, mismo destino, y el aviso «ya había un fichero con este nombre y se ha reemplazado». Eso es **R16** |
      > | Listado de la carpeta: **un solo elemento**, ninguno con `(1)` | **Cumplido**, y verificado por el humano **en la biblioteca**. **No hubo parada** |
      >
      > El tercer punto es el `acceptance` de esta feature, y es el que
      > obligaba a hablar con el humano antes de seguir si aparecía un `(1)`.
      > **No apareció.**
      >
      > Sin URL, sin `item_id` y sin ningún identificador, como manda el
      > párrafo de arriba. El nombre del fichero y la carpeta sí: son
      > sintéticos y ya estaban escritos en esta misma tarea.

- [x] **T19 · N/A · DECISIÓN DEL HUMANO DEL 2026-08-20** — ~~Copiar la
      sección nueva de `docs/INTEGRACION.md` a
      `azure-apps/postventa_incidencias.md`~~.

      **El humano decidió el 2026-08-20 que no hace commits en `azure-apps`.**
      Esta tarea, por tanto, **no está pendiente: ya no aplica**. No se queda
      `[ ]` esperando a nadie ni se apunta como deuda, porque no lo es.

      **Lo que sí se ha hecho, y cubre el fondo del asunto**: la sección de
      SharePoint está escrita en **`docs/INTEGRACION.md`** (T15), que vive en
      **este** repositorio y es la fuente de verdad declarada de lo que
      consumimos —sitio y biblioteca por nombre de variable, identidad,
      permisos, volumen y qué se rompe si alguien lo toca—. Lo que decae es
      **la copia** a otro repositorio, no la obligación de documentarlo.

      **Consecuencia que conviene no perder de vista**: mientras esa copia no
      exista, quien lea solo `azure-apps/` **no se enterará** de que este
      proyecto es un inquilino nuevo del sitio de IT con permiso de escritura.
      Si algún día se quiere cerrar ese hueco, el material está listo para
      copiar y pegar.

---

## Fase 9 · Cierre

- [x] **T20**: Campaña de mutación y análisis de supervivientes.
      **Verificación**: `python -m harness.mutacion --feature F-006` genera
      `progress/mutacion_F-006.md` con **cero supervivientes** (nivel
      `critico`), o cada superviviente con su análisis escrito y aceptado por
      el humano. Atención especial a los mutantes de `nombrado.py` (los
      separadores, el sufijo y el orden de las sustituciones) y a los de la
      puerta de entorno de §5: si alguno sobrevive, es que la regla dura no
      está probada de verdad.

- [x] **T21**: Ejecutar `bash harness/init.sh` en verde.
      **Verificación**: exit code 0, con la puerta de cobertura de las líneas
      cambiadas en `[OK]` (umbral 80 %).

### El cierre de F-006 necesita autorización expresa del humano (C5)

> **CERRADO EL 2026-08-25.** Esta sección describe una situación que **ya no
> existe**: T18 se ejecutó ese día con la autorización expresa que aquí se
> exigía —«autorizo T18 ante `CHECKPOINTS.md` C5», del humano, con fecha— y su
> casilla está `[x]` con el resultado real anotado. **F-006 ya no tiene ninguna
> verificación manual pendiente.** Lo que sigue se conserva porque es el
> razonamiento que sostuvo el cierre del 2026-08-19 y el que motiva **F-017**;
> no es una condición viva.

Dicho sin rodeos, porque es justo donde esto se pierde: con la opción (a) de
**D3**, F-006 llega al `reviewer` con **una verificación manual sin resultado
real** —**T18**—, y el rigor `critico` de esta feature **la exige**.
`CHECKPOINTS.md` **C5** pide `tasks.md` con **todas** las tareas `[x]`, y T18
va a quedar `[ ]`.

Por tanto: **ese cierre lo autoriza el humano, no el arnés.** El `reviewer`
no puede dar por cumplido C5 por su cuenta ni relajar el criterio; necesita la
autorización expresa del humano, dejada por escrito en `progress/`, para
aprobar F-006 con T18 pendiente. Sin esa autorización, el veredicto correcto
es `CHANGES_REQUESTED`.

**Este caso es exactamente el que motiva F-017**: la propuesta de que C5
distinga la **tarea de agente pendiente** (que nunca debe pasar) de la
**verificación `MANUAL (humano)` pendiente por una dependencia declarada**
(que puede pasar con autorización y fecha). Quien lea esto y quiera el hilo
completo, el identificador es **F-017**.

---

## Resumen de dependencias externas

| Tarea | Depende de | Estado |
|---|---|---|
| T1 | F-004 y F-005 mergeadas en `dev` | fuera de esta rama |
| T8 | **D1** (qué librería de Graph reutilizar) | **RESUELTA 2026-08-20**: `httpx` |
| T17 | **D6** (biblioteca de dev y app registration creados) | **RESUELTA 2026-08-20**: ya existen. T17 lista para que la ejecute el humano |
| T18 | **F-010** (entorno desplegado) + D6 | **EJECUTADA el 2026-08-25**, dentro de F-010 y con autorización expresa ante C5. Estuvo **DIFERIDA** desde el 2026-08-19 por D3 (a); la dependencia ya no existe |
| T19 | ~~T15 hecha~~ | **N/A 2026-08-20**: el humano no commitea en `azure-apps` |
