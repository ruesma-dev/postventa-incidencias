<!-- BACKLOG.md -->
# Backlog

**Fichero generado por `harness/backlog.py` a partir de `harness/features.json`. No lo edites a mano**: edita el JSON y vuelve a generarlo (lo hace solo `bash harness/init.sh`).

Resumen: **20 features**, 10 abiertas, 10 terminadas.

## Trabajo abierto

| # | Feature | Prioridad | Estado | Rigor | Rama |
|---|---|---|---|---|---|
| F-009 | Cierre de la incidencia en Sigrid (solo estado) | 10 | pendiente | critico | `feature/F-009-cierre-sigrid` |
| F-011 | Fase 2: ingesta desde buzón de correo | 11 | pendiente | estandar | `feature/F-011-buzon-correo` |
| F-012 | Futuro: subir el parte a Sigrid como gráfico de la incidencia | 12 | pendiente | critico | `feature/F-012-grafico-sigrid` |
| F-013 | Futuro: mudar el archivo a la biblioteca de Posventa | 13 | pendiente | estandar | `feature/F-013-archivo-posventa` |
| F-014 | Reagrupar el parte de dos hojas con el 'Página 2' que lee la extracción | 14 | pendiente | critico | `feature/F-014-reagrupar-pagina-2` |
| F-015 | Evaluación del prompt de extracción contra partes reales | 15 | pendiente | critico | `feature/F-015-evaluacion-prompt` |
| F-016 | Interpretación automática de las observaciones manuscritas | 16 | pendiente | critico | `feature/F-016-interpretacion-observaciones` |
| F-017 | Mejoras de CHECKPOINTS: verificaciones manuales y cobertura no medida | 17 | pendiente | documental | `feature/F-017-checkpoints-manual` |
| F-018 | Mínimo privilegio en Graph: la app solo Sites.Selected | 18 | pendiente | documental | `feature/F-018-minimo-privilegio-graph` |
| F-020 | Ajustes de diseño del front: el PDF manda en la pantalla | 20 | pendiente | documental | `feature/F-020-diseno-front` |

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
| F-019 | Endpoints de persistencia: guardar la remesa y leer la cola | 19 | estandar |

## Detalle

### F-009 · Cierre de la incidencia en Sigrid (solo estado)

estado **pendiente** · prioridad 10 · rigor `critico` · SDD sí · rama `feature/F-009-cierre-sigrid`

Mover con.est de la reclamación al estado CERRADA, resuelto contra conest y nunca hardcodeado. OJO: el proceso 'Cerrar parte' del ERP exige que la reclamación tenga un gráfico asociado; un UPDATE directo se saltaría esa comprobación. El alcance real de esta feature depende de lo que F-008 averigüe sobre ese proceso y sobre la opción 'Cerrar parte sin archivo (RPV)'. Dry-run primero, el usuario confirma en el front, y entonces commit. Con preferencia por usuario para pasarlo a automático.

### F-011 · Fase 2: ingesta desde buzón de correo

estado **pendiente** · prioridad 11 · rigor `estandar` · SDD sí · rama `feature/F-011-buzon-correo`

Recoger automáticamente las remesas que lleguen a un buzón corporativo, reaprovechando el pipeline existente. Patrón de albaranes-email y partes-email.

### F-012 · Futuro: subir el parte a Sigrid como gráfico de la incidencia

estado **pendiente** · prioridad 12 · rigor `critico` · SDD sí · rama `feature/F-012-grafico-sigrid`

Replicar el 'importar desde archivo' que hace Posventa a mano: INSERT del PDF en gra (binario en ima) e INSERT en rcg para vincularlo al concepto de la reclamación, atómico con el cambio de estado. REQUIERE un endpoint de dominio nuevo en sigrid-api: hoy la pasarela lee documentos pero no los escribe, y sql/write ni reserva ide con applock ni está pensado para BLOBs. Ese endpoint se implementa en el repositorio sigrid-api, no aquí.

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

### F-019 · Endpoints de persistencia: guardar la remesa y leer la cola

estado **terminada** · prioridad 19 · rigor `estandar` · SDD sí · rama `feature/F-019-endpoints-persistencia`

F-005 dejó `RepositorioPartesPort` completo —`guardar_remesa`, `guardar_parte`, `guardar_validacion`, `cola_validacion_humana`— y sus seis tablas creadas en la base real, pero **el único endpoint que escribe hoy es `/api/archivar`**, y solo su traza. El puerto existe y nadie lo llama: la remesa, los partes extraídos y el resultado de la validación no se guardan en ningún sitio. Consecuencia visible, detectada al diseñar F-007 (decisión D4): recargar la pestaña del front pierde todo el trabajo de revisión, y la cola de validación humana que F-004 declara no puede sobrevivir entre sesiones porque nada la escribe ni la lee. EL HUMANO DECIDIÓ EL 2026-08-20 sacar F-007 sin persistencia de sesión y dar de alta esta feature aparte, en vez de bloquear el front: el piloto de Mirasierra no se retrasa y el front no carga con una responsabilidad que es de `postventa-api`. Alcance: los endpoints que faltan sobre los puertos que YA existen; no hay que diseñar esquema ni tocar el DDL. **PREREQUISITO DEL ARCHIVADO REAL, DEMOSTRADO CONTRA EL ENTORNO DESPLEGADO EL 2026-08-25** (defecto 15 de F-010, T18): la tabla `archivos` tiene una clave ajena contra `partes` —`archivos_hash_parte_fkey`— y hoy NADA inserta el parte, así que `POST /api/archivar` sube el fichero a SharePoint y después NO puede escribir su traza: `ForeignKeyViolation`, «Key (hash_parte)=(...) is not present in table "partes"». Pasa con parte sintético y con parte real. Consecuencia: **tal y como está desplegado, el archivado no puede completar nunca**, y el circuito completo del piloto no se puede dar por bueno hasta que exista esta feature. Mientras tanto el borde responde 500 diciendo que el fichero SÍ está subido y que lo que falta es la traza (defecto 14). Al implementar esta feature hay que comprobar el orden: el parte se guarda ANTES de archivarlo.
