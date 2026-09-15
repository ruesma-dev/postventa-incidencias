<!-- BACKLOG.md -->
# Backlog

**Fichero generado por `harness/backlog.py` a partir de `harness/features.json`. No lo edites a mano**: edita el JSON y vuelve a generarlo (lo hace solo `bash harness/init.sh`).

Resumen: **27 features**, 14 abiertas, 13 terminadas.

Bloqueadas: **F-009**.

## Trabajo abierto

| # | Feature | Prioridad | Estado | Rigor | Rama |
|---|---|---|---|---|---|
| F-009 | Cierre de la incidencia en Sigrid (solo estado) | 10 | bloqueada | critico | `feature/F-009-cierre-sigrid` |
| F-024 | Datos del parte enlazados a Sigrid, para el datamart | 12 | spec lista | estandar | `feature/F-024-datos-parte-sigrid` |
| F-011 | Fase 2: ingesta desde buzón de correo | 13 | pendiente | estandar | `feature/F-011-buzon-correo` |
| F-013 | Futuro: mudar el archivo a la biblioteca de Posventa | 13 | pendiente | estandar | `feature/F-013-archivo-posventa` |
| F-014 | Reagrupar el parte de dos hojas con el 'Página 2' que lee la extracción | 14 | pendiente | critico | `feature/F-014-reagrupar-pagina-2` |
| F-015 | Evaluación del prompt de extracción contra partes reales | 15 | pendiente | critico | `feature/F-015-evaluacion-prompt` |
| F-016 | Interpretación automática de las observaciones manuscritas | 16 | pendiente | critico | `feature/F-016-interpretacion-observaciones` |
| F-017 | Mejoras de CHECKPOINTS: verificaciones manuales y cobertura no medida | 17 | pendiente | documental | `feature/F-017-checkpoints-manual` |
| F-018 | Mínimo privilegio en Graph: la app solo Sites.Selected | 18 | pendiente | documental | `feature/F-018-minimo-privilegio-graph` |
| F-020 | Ajustes de diseño del front: el PDF manda en la pantalla | 20 | pendiente | documental | `feature/F-020-diseno-front` |
| F-021 | Rehidratar la sesión del front al recargar el navegador | 21 | pendiente | estandar | `feature/F-021-rehidratar-sesion` |
| F-022 | Caché de contexto en las llamadas a Gemini: dejar de repetir el prompt en cada página | 22 | pendiente | estandar | `feature/F-022-cache-prompts-gemini` |
| F-027 | Acelerar la suite: cachear el barrido del repositorio en los tests de arquitectura | 23 | pendiente | estandar | `feature/F-027-suite-barrido-cacheado` |
| F-028 | Rechazar un parte aprobado a mano, y quitar los espacios de los codigos de incidencia | 28 | pendiente | estandar | `feature/F-028-rechazo-manual` |

## Terminadas

| # | Feature | Prioridad | Rigor |
|---|---|---|---|
| F-001 | Esqueleto del monorepo y /health | 1 | estandar |
| F-002 | Ingesta y troceado de la remesa en partes | 2 | critico |
| F-003 | Extracción multimodal del parte, manuscritos incluidos | 3 | critico |
| F-004 | Validación del parte y clasificación de la firma | 4 | critico |
| F-005 | Persistencia en el PostgreSQL compartido | 5 | critico |
| F-006 | Nombrado y archivo en SharePoint | 6 | critico |
| F-007 | Front de carga y revisión | 7 | estandar |
| F-010 | Despliegue en Azure y tarjeta en el portal | 8 | estandar |
| F-008 | Modelo de posventa en Sigrid: confirmar contra el ERP | 9 | documental |
| F-012 | Futuro: subir el parte a Sigrid como gráfico de la incidencia | 12 | critico |
| F-019 | Endpoints de persistencia: guardar la remesa y leer la cola | 19 | estandar |
| F-025 | Archivar y cerrar en una sola confirmacion | 25 | critico |
| F-026 | Aprobacion humana de los partes que van a revision | 26 | estandar |

## Detalle

### F-009 · Cierre de la incidencia en Sigrid (solo estado)

estado **bloqueada** · prioridad 10 · rigor `critico` · SDD sí · rama `feature/F-009-cierre-sigrid`

Mover con.est de la reclamación al estado CERRADA, resuelto contra conest y nunca hardcodeado. OJO: el proceso 'Cerrar parte' del ERP exige que la reclamación tenga un gráfico asociado; un UPDATE directo se saltaría esa comprobación. El alcance real de esta feature depende de lo que F-008 averigüe sobre ese proceso y sobre la opción 'Cerrar parte sin archivo (RPV)'. Dry-run primero, el usuario confirma en el front, y entonces commit. Con preferencia por usuario para pasarlo a automático.

### F-024 · Datos del parte enlazados a Sigrid, para el datamart

estado **spec lista** · prioridad 12 · rigor `estandar` · SDD sí · rama `feature/F-024-datos-parte-sigrid`

Conservar en nuestra base (schema postventa de psql-albaranes-rs9k2) la informacion del parte que hoy no llega a Sigrid, siempre enlazada con las claves del ERP para que el datamart (sigrid_dm, mismo servidor, otra base) pueda enriquecer con ella los partes de posventa cuando los incorpore. Decidido por el humano el 2026-09-06 tras revisar la guia de cierre de Posventa: el cierre en Sigrid solo registra el grafico y el estado, y todo lo demas del parte se perderia. TRES PIEZAS. (1) Extraccion: anadir al prompt y al schema los campos impresos que hoy no se extraen -oficio, empresa (el industrial que reparo), estancia- y los manuscritos hora_inicio y hora_fin, con su confianza y sin exigirlos (regla de F-003: no se exige lo que la realidad deja vacio); columnas nuevas en postventa.partes con ADD COLUMN IF NOT EXISTS, idempotente como el resto del DDL. (2) Claves del ERP: columna reclamacion_ide (con.ide de la reclamacion, que el dry-run de F-009 ya lee) en postventa.cierres; en postventa.graficos nace ya con ella desde F-012. (3) Una vista de lectura postventa.v_partes_sigrid en nuestro schema que junta parte, validacion, archivo, cierre y grafico por hash_parte y expone las claves de Sigrid (obra, numero de incidencia, reclamacion_ide, gra_cod), los campos extraidos con sus confianzas, la clasificacion de la firma, la URL de SharePoint y las fechas; SIN dni_cliente. PREGUNTA ABIERTA (la decide el humano al aprobar la spec): si la vista expone las observaciones manuscritas, el dato mas valioso para el datamart pero que puede llevar nombres; por defecto NO. FUERA DE ALCANCE: el acceso desde el datamart (su ETL tendria que conectarse a nuestra base con un rol de solo lectura propio, como hace con mcp_sigrid_dm_ro); se deja como peticion escrita al proyecto datamart-seg-anual y el contrato de la vista se documenta en azure-apps/postventa_incidencias.md §8. Va despues de F-012 y antes de F-011.

### F-011 · Fase 2: ingesta desde buzón de correo

estado **pendiente** · prioridad 13 · rigor `estandar` · SDD sí · rama `feature/F-011-buzon-correo`

Recoger automáticamente las remesas que lleguen a un buzón corporativo, reaprovechando el pipeline existente. Patrón de albaranes-email y partes-email.

### F-013 · Futuro: mudar el archivo a la biblioteca de Posventa

estado **pendiente** · prioridad 13 · rigor `estandar` · SDD sí · rama `feature/F-013-archivo-posventa`

Al pasar a producción, dejar de archivar en la biblioteca de IT y hacerlo en la de Posventa respetando la estructura que ya usan y tienen sincronizada por OneDrive: Postventa - Documentos / <cod> <OBRA> / PARTES INCIDENCIAS / <UNIDAD> / PARTES FIRMADOS.

### F-014 · Reagrupar el parte de dos hojas con el 'Página 2' que lee la extracción

estado **pendiente** · prioridad 14 · rigor `critico` · SDD sí · rama `feature/F-014-reagrupar-pagina-2`

Las remesas reales llegan escaneadas sin capa de texto (Mirasierra: 22 páginas, 0 caracteres), así que el troceado de F-002 no puede leer el pie y degrada a 'una página, un parte': un parte de dos hojas sale partido en dos. F-003 ya pasa cada página por un modelo multimodal, que sí ve el pie impreso. Esta feature aprovecha esa lectura: si la extracción devuelve 'Página 2' (o N mayor que 1), esa página se reagrupa como continuación del parte anterior en vez de quedarse como parte suelto. Es la reagrupación posterior al troceado, no un segundo troceador.

### F-015 · Evaluación del prompt de extracción contra partes reales

estado **pendiente** · prioridad 15 · rigor `critico` · SDD sí · rama `feature/F-015-evaluacion-prompt`

Ningún test unitario detecta que un cambio de redacción de config/prompts.yaml empeore la extracción: en la suite el modelo está simulado y todo seguiría verde con el prompt roto. Esta feature crea el evaluador que falta —juego de partes de prueba con su verdad esperada, llamada real con credencial, umbral de acierto por campo e informe con veredicto— y, solo cuando ese comando exista, declara harness/rutas_sensibles.json para que tocar el prompt obligue a presentar evidencia. OJO A LA REGLA DE PROPAGACIÓN: el evaluador es genérico (vale igual para partes y albaranes), así que el mecanismo se porta a arnes-base en el mismo trabajo; aquí se queda solo el juego de partes y el umbral, que sí son de este dominio. El borrador de la declaración está en specs/F-003-extraccion/design.md. ENCARGO AÑADIDO EL 2026-08-19 desde el cierre de F-004: falta el CONTROL NEGATIVO de la clasificación de firma. T14 midió las cuatro etiquetas sobre los 22 partes reales de Mirasierra y salió 22/22 'humana' con confianza media 98,2, cero 'ilegible', cero 'marca_simple' y cero 'casilla_vacia'. Eso confirmó la decisión D1 (la regla estricta no manda a revisión ningún parte real) pero NO demuestra el criterio de aceptación de F-004 'la clasificación distingue firma de aspa': en la remesa no había ni un aspa, así que un clasificador que respondiera 'humana' a todo habría dado la misma salida. Lo que falta es pasar por el clasificador partes SINTÉTICOS con aspa y con casilla vacía (tests/utiles_pdf.py sabe componerlos) y comprobar que no los etiqueta 'humana'. El humano decidió el 2026-08-19 cerrar F-004 sin ello y traerlo aquí, que es el sitio natural de la evaluación de prompts.

### F-016 · Interpretación automática de las observaciones manuscritas

estado **pendiente** · prioridad 16 · rigor `critico` · SDD sí · rama `feature/F-016-interpretacion-observaciones`

Hoy F-004 rechaza en bloque cualquier parte con observaciones manuscritas y lo manda entero a la cola de validación humana, dé lo mismo que ponga 'falta rematar el rodapié' o 'firmado a satisfacción'. Esta feature interpreta el texto que ya transcribe F-003 para distinguir la observación inocua —una nota, una aclaración, un comentario que no discute la reparación— de la que de verdad impide dar la reparación por buena, y así reducir la cola humana a lo que la merece. Mejora posterior, no bloqueante: el circuito funciona sin ella, solo con más trabajo manual. En la remesa real de Mirasierra la cola serían 2 de 22 partes (~9 %), así que el ahorro se mide antes de complicar el modelo. Ante la duda, a la cola: la clasificación nunca da por buena una reparación por su cuenta si no está segura.

### F-017 · Mejoras de CHECKPOINTS: verificaciones manuales y cobertura no medida

estado **pendiente** · prioridad 17 · rigor `documental` · SDD no · rama `feature/F-017-checkpoints-manual`

Dos propuestas que dejó la review de F-003, aparcadas por el humano el 2026-08-19 como baja prioridad. (P2) C5 exige hoy todas las tareas de tasks.md en [x], pero el nivel de rigor critico OBLIGA a tener verificaciones MANUAL (humano) que ningún agente puede ejecutar: el reviewer queda entre rechazar un trabajo impecable, marcar como hecho algo que nadie ejecutó, o aprobar saltándose la letra de C5. Pasó con F-003 y lo único que impidió cerrarla con T18 sin ejecutar fue una nota escrita a mano en progress/current.md. Se propone que C5 distinga la tarea de agente pendiente (trabajo incompleto, CHANGES_REQUESTED) de la tarea MANUAL (humano) pendiente (estado propio: aprobado pero no cerrable hasta que el humano la ejecute). (P3) Que C4 bis nombre explícitamente la comprobación de ficheros «no medidos» en la puerta de cobertura, que hoy se hace pero no está escrita. Las dos son GENÉRICAS: se portan a arnes-base en el mismo trabajo, según la regla de propagación de CLAUDE.md. AÑADIDO EL 2026-08-19 desde F-005 (decisión D5): el DDL contra el PostgreSQL compartido es candidato reconocido a ruta sensible del arnés, pero declararlo cambiaría el arnés para todas las features, así que la decisión se trae aquí. Hoy no existe harness/rutas_sensibles.json y C4 ter es N/A. AÑADIDO desde F-006 (decisión D3): el humano eligió cerrar F-006 con su verificación de subida real declarada y pendiente hasta que F-010 despliegue; ese cierre necesita autorización expresa ante C5 y es el segundo caso real que justifica P2.

### F-018 · Mínimo privilegio en Graph: la app solo Sites.Selected

estado **pendiente** · prioridad 18 · rigor `documental` · SDD no · rama `feature/F-018-minimo-privilegio-graph`

El app registration `postventa-incidencias` (verificado el 2026-08-20) tiene consentimiento de administrador para TRES permisos de aplicación de Microsoft Graph: Sites.Selected, Sites.ReadWrite.All y Sites.FullControl.All. Los dos últimos alcanzan a TODOS los sitios de SharePoint del tenant, no solo a la biblioteca de Posventa, y vuelven irrelevante al primero: con Sites.FullControl.All la aplicación puede escribir en el sitio de RRHH o de dirección igual que en el suyo. Es más amplio incluso que Files.ReadWrite.All, que la spec de F-006 ya descartó por excesivo. No es un fallo: es lo que pasa al configurar Sites.Selected, que exige el paso extra de asignar la biblioteca concreta por Graph, mientras que los amplios funcionan a la primera. EL HUMANO DECIDIÓ EL 2026-08-20 arrancar F-006 con los permisos actuales y recortar después, en esta feature, para no mezclar un cambio de configuración del tenant con una implementación. Mientras tanto el riesgo queda documentado en la spec de F-006. El recorte lo ejecuta el humano en Azure: un agente no toca permisos del tenant.

### F-020 · Ajustes de diseño del front: el PDF manda en la pantalla

estado **pendiente** · prioridad 20 · rigor `documental` · SDD no · rama `feature/F-020-diseno-front`

Tres observaciones del humano al probar el front por primera vez el 2026-08-20 (F-007, T14), con la remesa real delante. Ninguna es un fallo: el front funciona. Son de uso, y salen de mirar la pantalla de trabajo de quien va a revisar 22 partes seguidos. (1) **El campo de observaciones se queda pequeño**: es texto manuscrito transcrito, de longitud variable, y hay que poder leerlo y corregirlo entero sin pelearse con una caja de una línea. (2) **El PDF se ve pequeño**, que es el problema de fondo: el documento es lo que la persona está leyendo para decidir, y hoy es lo que menos sitio ocupa. (3) **La vista del PDF está partida en dos** —a la izquierda la previsualización de páginas, a la derecha la página— y el reparto está al revés: la tira de previsualización debe ser **muy estrecha**, lo justo para navegar, y cederle el espacio a la página. Criterio que ordena las tres: en una pantalla de revisión, el documento manda y todo lo demás le cede sitio.

### F-021 · Rehidratar la sesión del front al recargar el navegador

estado **pendiente** · prioridad 21 · rigor `estandar` · SDD sí · rama `feature/F-021-rehidratar-sesion`

Decisión **D4 de F-019**, tomada por el humano el 2026-08-26 y aplazada a propósito hasta ver el piloto. F-019 dejó la persistencia escribiendo: la remesa, los partes y el resultado de la validación quedan guardados en `postventa`, y la cola de validación humana sobrevive entre sesiones. Lo que NO sobrevive es el trabajo en curso: si quien está revisando una remesa de 22 partes recarga la pestaña, la pantalla vuelve a cero y hay que subir el PDF y volver a extraerlo entero, gastando otra vez cuota de IA. La pieza que falta es de LECTURA: volver a pintar una remesa con sus partes y sus veredictos exige un método nuevo en `RepositorioPartesPort` —hoy solo existe `cola_validacion_humana`—, y el encargo de F-019 prohibía expresamente tocar el puerto, por eso se sacó aparte. Alcance: el método de lectura, el endpoint que lo expone y el cableado del front que lo consume al arrancar. Sin DDL: las seis tablas de F-005 ya guardan todo lo necesario. OJO al dato personal: la lectura devuelve observaciones manuscritas de clientes, así que hereda de F-019 el tope duro de límite y la prohibición de escribir dato personal en el log.

### F-022 · Caché de contexto en las llamadas a Gemini: dejar de repetir el prompt en cada página

estado **pendiente** · prioridad 22 · rigor `estandar` · SDD sí · rama `feature/F-022-cache-prompts-gemini`

ORIGEN: un aviso de consumo que recibió el humano el 2026-08-26 estimando hasta un 67 % de ahorro cacheando contenido repetido. OJO, ese aviso es sobre la API de Anthropic y ESTE PROYECTO NO LA USA: `postventa-api` llama a Gemini (`google.genai`), así que el ahorro estimado no sale de aquí. Si el gasto directo de API de la organización viene de otro repositorio, la feature de caché va allí, no en este (límite de servicio). Lo que sí aplica aquí es la misma idea con el proveedor que sí usamos: hoy el `system_instruction` viaja ENTERO en cada llamada, y una remesa como la real de Mirasierra son 22 páginas por dos llamadas —extracción y clasificación de firma— es decir 44 envíos del mismo prompt. El SDK ya instalado trae soporte de caché de contexto. EL MATIZ QUE ORDENA LA FEATURE: `config/prompts.yaml` entero son 7.501 bytes, así que cada prompt suelto ronda el mínimo de tokens que Gemini exige para cachear y PUEDE QUE NO COMPENSE. Por eso la feature empieza midiendo y su primer entregable es un número, no un cambio de código: hoy nadie sabe lo que cuesta procesar una remesa. Cerrarla documentando que no compensa es un resultado válido. NO SE TOCA EL TEXTO DE LOS PROMPTS: eso es F-015, y cambiarlos sin su evaluador es justo lo que esa feature previene.

### F-027 · Acelerar la suite: cachear el barrido del repositorio en los tests de arquitectura

estado **pendiente** · prioridad 23 · rigor `estandar` · SDD sí · rama `feature/F-027-suite-barrido-cacheado`

El 55 % de los 38,7 s que tarda la suite del servicio api son 67 tests de cinco ficheros que recorren el árbol del repositorio fichero a fichero, y repiten el mismo barrido en cada test: test_f003_arquitectura.py cuesta 12,7 s él solo, un tercio de la suite entera. Leer el árbol UNA vez en una fixture de sesión y que cada test consulte el resultado dejaría la suite en torno a 20 s. Medido en progress/explore_F-009_timeouts.md (medición 10) el 2026-09-02, a propósito de los timeouts de la campaña de mutación de F-009: con la suite a 20 s la campaña paralela volvería a caber de sobra en el tope de 120 s por mutante. Beneficia además a cada init.sh de cada sesión. OJO: toca tests de F-003, F-005, F-006 y F-009, features ya cerradas, con el riesgo de aflojar sin querer una comprobación de arquitectura; por eso lleva spec propia y review, y no se mete dentro de otra feature. RENUMERADA el 2026-09-15: nacio como F-022 el 2026-09-02 en la rama de F-012, sin ver que dev ya tenia una F-022 distinta -la cache de contexto de Gemini, del 2026-08-26-. Al mergear la cadena a dev colisionaron los dos identificadores; conserva el numero la que se dio de alta antes.

### F-028 · Rechazar un parte aprobado a mano, y quitar los espacios de los codigos de incidencia

estado **pendiente** · prioridad 28 · rigor `estandar` · SDD sí · rama `feature/F-028-rechazo-manual`

Pedida por el humano el 2026-09-15, mientras verificaba F-026 en real: hace falta poder cambiar el estado de un parte de aprobado a rechazado a mano. HOY NO SE PUEDE. F-026 dejo la aprobacion humana, pero la unica revocacion que existe es AUTOMATICA: MotivoRevocacion.VEREDICTO_CAMBIADO, que salta cuando un reproceso lee el papel y sale otra cosa (R30). Quien aprueba por error no tiene forma de deshacerlo, y el parte se archiva y cierra una incidencia del ERP de produccion. LA MITAD DEL TRABAJO YA ESTA HECHA, y por eso esta feature es pequena: el dominio ya modela la revocacion -`Aprobacion` tiene `revocada_at_utc` y `revocada_motivo`, `esta_vigente` la respeta, y una aprobacion revocada NO se borra (R33)-, y `puede_archivarse` ya deja de dar permiso en cuanto la aprobacion deja de estar vigente. Falta el GESTO: un motivo de revocacion nuevo -retirada por una persona-, el endpoint que la registra con el oid de quien la retira, y el boton en la cola. MISMA REGLA QUE GOBIERNA F-026: se registra al lado, nunca encima (R11). El veredicto de la maquina y sus motivos siguen intactos, y un parte rechazado vuelve a ser lo que era -no apto, con sus motivos- y deja de poder archivarse en el acto. TRES PREGUNTAS ABIERTAS que decide el humano al aprobar la spec. (1) Un parte YA ARCHIVADO Y CERRADO: por defecto NO se puede rechazar, porque lo escrito en SharePoint y en el ERP no se deshace desde aqui y fingir que si es peor que no ofrecerlo. (2) Si el rechazo exige escribir un motivo en texto o basta el gesto: por defecto texto libre y opcional, guardado junto a la revocacion. (3) Quien puede rechazar: por defecto cualquiera que pueda aprobar, con su oid registrado, no solo quien aprobo. NO TOCA SIGRID: como F-026, todo ocurre en nuestra base. SEGUNDO ASUNTO, anadido por el humano el 2026-09-15 nada mas verificar F-026 en real: LOS ESPACIOS DE LOS CODIGOS DE INCIDENCIA. La IA leyo el numero del papel como 'RS26.09 / 0149', con un espacio a cada lado de la barra, y eso ROMPE EL CIERRE: `a_codigo_de_sigrid` se apoya en `normalizar_codigo`, que colapsa los espacios repetidos pero NO quita los que rodean a un separador, asi que el codigo llega al ERP con sus dos espacios y la busqueda -WHERE c.cod = ?, igualdad exacta- no encuentra la reclamacion. Reproducido el 2026-09-15: 'RS26.09 / 0149' sale de `a_codigo_de_sigrid` tal cual. LO QUE HACE EL DEFECTO DIFICIL DE VER es que EL NOMBRE DEL FICHERO SALE BIEN POR CASUALIDAD -la barra pasa a ' - ' y el colapso posterior se come el sobrante-, o sea que el parte se archiva con el nombre correcto y solo falla el cierre. Y no es solo la barra: 'RS26.09- 0149' produce el nombre '0626 - RS26.09- 0149 PARTE FIRMADO.pdf', distinto del canonico, y ese si se archivaria mal. EL ARREGLO VA EN EL DOMINIO, en `normalizar_codigo`, para que lo hereden las dos conversiones y no diverjan. OJO: al cambiar la normalizacion cambia tambien `huella_de_veredicto` de F-026, que normaliza los mismos campos; hay que comprobar que eso no revoca aprobaciones vigentes por nada. Va en esta feature por peticion expresa del humano, aunque es un defecto independiente del rechazo manual.

### F-001 · Esqueleto del monorepo y /health

estado **terminada** · prioridad 1 · rigor `estandar` · SDD no · rama `feature/F-001-esqueleto`

Crear services/postventa-api (Function App Python con settings, logging y un endpoint /health) y services/postventa-front vacío pero arrancable. Feature de calentamiento: valida el circuito completo del arnés antes de jugarse nada.

### F-002 · Ingesta y troceado de la remesa en partes

estado **terminada** · prioridad 2 · rigor `critico` · SDD sí · rama `feature/F-002-ingesta-troceado`

Normalizar la entrada (PDF suelto, ZIP, varios ficheros) a una lista de PDFs, y trocear cada remesa en documentos de UN parte detectando el comienzo por la plantilla impresa. Endpoint POST /split. Se diseña contra los partes reales de muestras/.

### F-003 · Extracción multimodal del parte, manuscritos incluidos

estado **terminada** · prioridad 3 · rigor `critico` · SDD sí · rama `feature/F-003-extraccion`

Adaptador de IA tras ExtractorPort, arrancando con gemini-3.7-flash (el modelo que usa Ruesma; azure-apps documenta el proveedor pero no fija version), configurable por GEMINI_MODEL. Extrae promoción, código de obra, unidad (el papel la imprime como 'Vivienda'), nº de incidencia, fecha de servicio, descripción y lo escrito a mano: DNI y observaciones. Lee además el 'Página N' del pie, que F-014 necesitará para reagrupar el parte de dos hojas. CERRADA el 2026-08-19: revisión APROBADA y última verificación manual completada (T18, barrido de los 22 partes reales de Mirasierra), con el modelo leyendo la letra manuscrita y cero falsos negativos.

### F-004 · Validación del parte y clasificación de la firma

estado **terminada** · prioridad 4 · rigor `critico` · SDD sí · rama `feature/F-004-validacion`

Reglas de validación sobre lo extraído y clasificación de la firma en: firma humana / marca simple (aspa, trazo geométrico) / casilla vacía / ilegible. Un parte solo es apto si tiene firma humana del cliente, código de obra y nº de incidencia legibles, y NO trae observaciones manuscritas: firmado no es lo mismo que conforme. DECISIONES DE DOMINIO DEL HUMANO (2026-08-19, mandan sobre el diseño): (1) un parte SIN DNI del cliente SÍ pasa como conforme, la ausencia de DNI no descalifica; (2) un parte CON observaciones manuscritas NO es conforme, y de momento ese es el ÚNICO motivo de rechazo; (3) el parte rechazado por observaciones no se descarta: va a una COLA DE VALIDACIÓN HUMANA que presenta las observaciones transcritas para que una persona decida. Dato real que respalda el dimensionado de esa cola: en la remesa real de Mirasierra 2 de 22 partes (~9 %) traen observaciones manuscritas, y solo 7 de 22 traen DNI.

### F-005 · Persistencia en el PostgreSQL compartido

estado **terminada** · prioridad 5 · rigor `critico` · SDD sí · rama `feature/F-005-persistencia`

Schema propio del proyecto en psql-albaranes-rs9k2: remesas, partes, resultado de validación, trazas de archivo y cierre, y preferencias por usuario (incluida la de auto-cierre). DDL idempotente al arranque, como hace sv3 en albaranes.

### F-006 · Nombrado y archivo en SharePoint

estado **terminada** · prioridad 6 · rigor `critico` · SDD sí · rama `feature/F-006-sharepoint`

Nombrar cada parte apto y archivarlo en SharePoint, en biblioteca propia dentro del sitio de IT mientras estemos en dev. El código de la incidencia (RS26.08 - 0123) y el de obra (0677) van impresos en el parte y son cosas distintas. El nombre conserva el sufijo ' PARTE FIRMADO' que usa Posventa.

### F-007 · Front de carga y revisión

estado **terminada** · prioridad 7 · rigor `estandar` · SDD sí · rama `feature/F-007-front`

Front estático (HTML + Tailwind CDN + Alpine.js + dev_server.py) siguiendo el patrón de front-nominas: arrastrar PDF/ZIP o elegir carpeta, progreso parte a parte, semáforo de validación, y revisión manual de lo dudoso antes de archivar. PUNTO DE PARTIDA: el esqueleto del front ya está escrito y verificado en la rama feature/F-007-front (se sacó de F-001 porque su dev_server.py hundía la puerta de cobertura). Recuperarlo con: git checkout feature/F-007-front -- services/postventa-front. Ya resuelto ahí: los scripts propios van SIN defer al final del body (con defer, Alpine arranca antes de que exista la función del x-data), Alpine con versión fija 3.14.1, el proxy apunta al puerto 7073, y el staticwebapp.config.json lleva <TENANT_ID> como marcador porque el ID de tenant no se versiona.

### F-010 · Despliegue en Azure y tarjeta en el portal

estado **terminada** · prioridad 8 · rigor `estandar` · SDD sí · rama `feature/F-010-despliegue`

Scripts re-ejecutables en infra/ para Function App y Static Web App con auth de Entra, grupo de seguridad de Posventa (hay que crearlo) y alta de la tarjeta en front-portal. La tarjeta se edita en ese repositorio, no en este. PRIORIDAD SUBIDA EL 2026-08-20 por el humano, por delante de F-008 y F-009 (las dos de Sigrid): quiere que **negocio pruebe el circuito completo desplegado sin tocar Sigrid todavía**. Encaja con lo que ya hay: F-002 a F-007 cubren entrada, extracción, validación, archivo y front, y el cierre en el ERP es justamente lo que queda fuera. Efecto lateral que importa: F-010 es quien **desbloquea T18 de F-006**, la verificación de subida real a SharePoint, que está diferida esperando un entorno desplegado.

### F-008 · Modelo de posventa en Sigrid: confirmar contra el ERP

estado **terminada** · prioridad 9 · rigor `documental` · SDD no · rama `feature/F-008-modelo-sigrid`

Confirmar contra el ERP lo que ya está documentado en azure-apps/sigrid_tablas.md, sigrid_api.md §9 y docs/referencia/01_cierre_incidencia_sigrid.md. Lo crítico: el proceso 'Cerrar parte' de Sigrid comprueba que la reclamación tenga un gráfico asociado, y existe una opción 6 'Cerrar parte sin archivo (RPV)'. Hay que averiguar qué escribe realmente cada uno de esos dos procesos antes de decidir el alcance del cierre. Además: el con.tip de la reclamación y el estado CERRADA en conest (el estado PENDIENTE es 3/PTE), en qué base vive gra, y si 'Asociar URL de Internet' permite referenciar el PDF de SharePoint en vez de incrustar el binario. Solo lecturas.

### F-012 · Futuro: subir el parte a Sigrid como gráfico de la incidencia

estado **terminada** · prioridad 12 · rigor `critico` · SDD sí · rama `feature/F-012-grafico-sigrid`

Replicar el 'importar desde archivo' que hace Posventa a mano: adjuntar el PDF del parte a la reclamación como gráfico (fila en gra, binario en ima de la base documental y enlace rcg en la de negocio), ANTES del cambio de estado de F-009, de modo que ninguna reclamación quede cerrada sin su parte. DESBLOQUEADA EL 2026-09-06: el endpoint de dominio existe. sigrid-api expone POST /api/sigrid/concepto-grafico (su F-004, mergeada en dev el 2026-09-06; contrato en azure-apps/sigrid_api.md §8.8): dry-run por defecto, idempotente por tamaño+sha256, transaccional entre las dos bases (misma instancia, sin MSDTC), solo PDF hasta SIGRID_DOCUMENT_MAX_BYTES, y única vía de escritura en la documental. La atomicidad entre dos llamadas HTTP (adjuntar y cerrar) no existe: se sustituye por orden más idempotencia, y un fallo tras adjuntar deja la reclamación abierta con su gráfico, que el reintento cierra. Parámetros de partida: contip 708, gratipide 35 (PV002 'POSTVENTA:Fotos Reparaciones', docs/referencia/03_modelo_posventa_sigrid.md), usu el login que F-009 ya resuelve por usuario, sha256 del PDF archivado. La configuración de sigrid-api en dev (SIGRID_DOMAIN_WRITE_ENABLED, SIGRID_DOCUMENT_WRITE_ENABLED, SIGRID_DOCUMENT_WRITE_DATABASE y las listas blancas de contip y gratipide) es del dueño de sigrid-api y es precondición, no se toca desde aquí. DECISION DEL RESPONSABLE DEL 2026-09-10, y cambia una premisa: la verificación contra el ERP se hace sobre la incidencia RS26.09/0150 (tipo 708) de la OBRA 0626, y sobre ninguna otra. La 0626 NO es una obra de pruebas: es una obra EN USO; se le planteó de forma explícita y lo reafirmó. Cae así la premisa anterior, que decía literalmente 'Toda verificación contra el ERP se hace sobre reclamaciones de la OBRA DE PRUEBA 404, con dry-run antes de cada commit y autorización expresa del humano por incidencia' (decisión del 2026-09-06). Implica que la incidencia de la comprobación y su cierre quedan en el histórico de una obra en uso, con el documento adjunto colgado de ella. La incidencia la da de alta el responsable en el ERP: este servicio no crea incidencias, y si no existe, la comprobación previa responde que no la localiza. Lo que NO cambia: comprobación previa (dry-run) antes de cada escritura, autorización expresa del responsable por incidencia concreta -que aquí gana peso, no lo pierde-, CIERRE_HABILITADO como interruptor único para el documento adjunto y para el cambio de estado, y ninguna escritura desde un puesto de trabajo. Constancia fechada en specs/F-012-grafico-sigrid/ (glosario de requirements.md, §15 de design.md, bloque 9 de tasks.md) y en progress/guion_bloque9_F-012.md. Historia previa (hallazgo 2026-08-26, base documental fuera de ALLOWED_WRITE_DATABASES; 2026-09-03, cae la premisa de la réplica): en progress/history.md y progress/current.md.

### F-019 · Endpoints de persistencia: guardar la remesa y leer la cola

estado **terminada** · prioridad 19 · rigor `estandar` · SDD sí · rama `feature/F-019-endpoints-persistencia`

F-005 dejó `RepositorioPartesPort` completo —`guardar_remesa`, `guardar_parte`, `guardar_validacion`, `cola_validacion_humana`— y sus seis tablas creadas en la base real, pero **el único endpoint que escribe hoy es `/api/archivar`**, y solo su traza. El puerto existe y nadie lo llama: la remesa, los partes extraídos y el resultado de la validación no se guardan en ningún sitio. Consecuencia visible, detectada al diseñar F-007 (decisión D4): recargar la pestaña del front pierde todo el trabajo de revisión, y la cola de validación humana que F-004 declara no puede sobrevivir entre sesiones porque nada la escribe ni la lee. EL HUMANO DECIDIÓ EL 2026-08-20 sacar F-007 sin persistencia de sesión y dar de alta esta feature aparte, en vez de bloquear el front: el piloto de Mirasierra no se retrasa y el front no carga con una responsabilidad que es de `postventa-api`. Alcance: los endpoints que faltan sobre los puertos que YA existen; no hay que diseñar esquema ni tocar el DDL. **PREREQUISITO DEL ARCHIVADO REAL, DEMOSTRADO CONTRA EL ENTORNO DESPLEGADO EL 2026-08-25** (defecto 15 de F-010, T18): la tabla `archivos` tiene una clave ajena contra `partes` —`archivos_hash_parte_fkey`— y hoy NADA inserta el parte, así que `POST /api/archivar` sube el fichero a SharePoint y después NO puede escribir su traza: `ForeignKeyViolation`, «Key (hash_parte)=(...) is not present in table "partes"». Pasa con parte sintético y con parte real. Consecuencia: **tal y como está desplegado, el archivado no puede completar nunca**, y el circuito completo del piloto no se puede dar por bueno hasta que exista esta feature. Mientras tanto el borde responde 500 diciendo que el fichero SÍ está subido y que lo que falta es la traza (defecto 14). Al implementar esta feature hay que comprobar el orden: el parte se guarda ANTES de archivarlo.

### F-025 · Archivar y cerrar en una sola confirmacion

estado **terminada** · prioridad 25 · rigor `critico` · SDD sí · rama `feature/F-025-confirmacion-unica`

Quitar el paso de vista previa del circuito. Hoy el front pide DOS confirmaciones para la misma decision: una para archivar y otra, tras ensenar el dry-run del grafico y del cierre, para escribir en el ERP. Al pulsar archivar sobre los partes aptos habra UNA sola confirmacion -la que ya existe- y al confirmarla se ejecutan los tres pasos seguidos: archivar en SharePoint, adjuntar el parte a la reclamacion y cerrarla. DECISION DEL HUMANO DEL 2026-09-11, tomada despues de verificar el circuito completo contra el ERP real: NO hace falta ensenar ningun resumen antes de confirmar; se le planteo que eso es lo que protege de cerrar la incidencia equivocada si la IA leyo mal el numero del papel, y lo reafirmo. OJO: esto DEROGA requisitos aprobados de F-009 y de F-012 que exigen dry-run mostrado al usuario antes de cada commit; se enmiendan con constancia fechada, citando la premisa original literal, NO se borran (mismo patron que R28 de F-010 el 2026-09-03). Las comprobaciones que el backend hace antes de escribir -que la reclamacion existe, en que estado esta, si el documento ya cuelga de ella- NO se tocan: lo que desaparece es la pantalla, no la verificacion. Los partes no aptos siguen sin archivarse.

### F-026 · Aprobacion humana de los partes que van a revision

estado **terminada** · prioridad 26 · rigor `estandar` · SDD sí · rama `feature/F-026-aprobacion-humana`

Hoy un parte que la validacion manda a revision humana se queda bloqueado para siempre: el front lo pinta en ambar, deja corregir sus campos y consultar la cola, pero NO existe ninguna forma de aprobarlo -ni boton, ni endpoint- y `esArchivable` solo mira el veredicto y el destino que puso la IA. Esta feature cierra ese circuito: cuando el humano corrige los campos o revisa el parte, este pasa a APROBADO y entra en el flujo normal de archivo y cierre. NO TOCA SIGRID: la puerta del ERP sigue siendo la misma y el cierre sigue exigiendo lo que exige. EL APROBADO SE GUARDA, no vive solo en el navegador (decision del humano del 2026-09-11): quien aprobo y cuando, en el esquema propio. El motivo no es completismo: un parte llega a revision porque la firma no parecia humana o porque trae observaciones manuscritas del cliente diciendo que la reparacion no esta bien, asi que aprobarlo es la decision de una persona que sobrescribe al sistema en una incidencia que acabara cerrada en el ERP, y esa decision tiene que quedar registrada.
