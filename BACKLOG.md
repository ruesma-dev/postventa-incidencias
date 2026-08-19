<!-- BACKLOG.md -->
# Backlog

**Fichero generado por `harness/backlog.py` a partir de `harness/features.json`. No lo edites a mano**: edita el JSON y vuelve a generarlo (lo hace solo `bash harness/init.sh`).

Resumen: **17 features**, 14 abiertas, 3 terminadas.

En curso: **F-004**.

## Trabajo abierto

| # | Feature | Prioridad | Estado | Rigor | Rama |
|---|---|---|---|---|---|
| F-004 | Validación del parte y clasificación de la firma | 4 | en curso | critico | `feature/F-004-validacion` |
| F-005 | Persistencia en el PostgreSQL compartido | 5 | pendiente | critico | `feature/F-005-persistencia` |
| F-006 | Nombrado y archivo en SharePoint | 6 | pendiente | critico | `feature/F-006-sharepoint` |
| F-007 | Front de carga y revisión | 7 | pendiente | estandar | `feature/F-007-front` |
| F-008 | Modelo de posventa en Sigrid: confirmar contra el ERP | 8 | pendiente | documental | `feature/F-008-modelo-sigrid` |
| F-009 | Cierre de la incidencia en Sigrid (solo estado) | 9 | pendiente | critico | `feature/F-009-cierre-sigrid` |
| F-010 | Despliegue en Azure y tarjeta en el portal | 10 | pendiente | estandar | `feature/F-010-despliegue` |
| F-011 | Fase 2: ingesta desde buzón de correo | 11 | pendiente | estandar | `feature/F-011-buzon-correo` |
| F-012 | Futuro: subir el parte a Sigrid como gráfico de la incidencia | 12 | pendiente | critico | `feature/F-012-grafico-sigrid` |
| F-013 | Futuro: mudar el archivo a la biblioteca de Posventa | 13 | pendiente | estandar | `feature/F-013-archivo-posventa` |
| F-014 | Reagrupar el parte de dos hojas con el 'Página 2' que lee la extracción | 14 | pendiente | critico | `feature/F-014-reagrupar-pagina-2` |
| F-015 | Evaluación del prompt de extracción contra partes reales | 15 | pendiente | critico | `feature/F-015-evaluacion-prompt` |
| F-016 | Interpretación automática de las observaciones manuscritas | 16 | pendiente | critico | `feature/F-016-interpretacion-observaciones` |
| F-017 | Mejoras de CHECKPOINTS: verificaciones manuales y cobertura no medida | 17 | pendiente | documental | `feature/F-017-checkpoints-manual` |

## Terminadas

| # | Feature | Prioridad | Rigor |
|---|---|---|---|
| F-001 | Esqueleto del monorepo y /health | 1 | estandar |
| F-002 | Ingesta y troceado de la remesa en partes | 2 | critico |
| F-003 | Extracción multimodal del parte, manuscritos incluidos | 3 | critico |

## Detalle

### F-004 · Validación del parte y clasificación de la firma

estado **en curso** · prioridad 4 · rigor `critico` · SDD sí · rama `feature/F-004-validacion`

Reglas de validación sobre lo extraído y clasificación de la firma en: firma humana / marca simple (aspa, trazo geométrico) / casilla vacía / ilegible. Un parte solo es apto si tiene firma humana del cliente, código de obra y nº de incidencia legibles, y NO trae observaciones manuscritas: firmado no es lo mismo que conforme. DECISIONES DE DOMINIO DEL HUMANO (2026-08-19, mandan sobre el diseño): (1) un parte SIN DNI del cliente SÍ pasa como conforme, la ausencia de DNI no descalifica; (2) un parte CON observaciones manuscritas NO es conforme, y de momento ese es el ÚNICO motivo de rechazo; (3) el parte rechazado por observaciones no se descarta: va a una COLA DE VALIDACIÓN HUMANA que presenta las observaciones transcritas para que una persona decida. Dato real que respalda el dimensionado de esa cola: en la remesa real de Mirasierra 2 de 22 partes (~9 %) traen observaciones manuscritas, y solo 7 de 22 traen DNI.

### F-005 · Persistencia en el PostgreSQL compartido

estado **pendiente** · prioridad 5 · rigor `critico` · SDD sí · rama `feature/F-005-persistencia`

Schema propio del proyecto en psql-albaranes-rs9k2: remesas, partes, resultado de validación, trazas de archivo y cierre, y preferencias por usuario (incluida la de auto-cierre). DDL idempotente al arranque, como hace sv3 en albaranes.

### F-006 · Nombrado y archivo en SharePoint

estado **pendiente** · prioridad 6 · rigor `critico` · SDD sí · rama `feature/F-006-sharepoint`

Nombrar cada parte apto y archivarlo en SharePoint, en biblioteca propia dentro del sitio de IT mientras estemos en dev. El código de la incidencia (RS26.08 - 0123) y el de obra (0677) van impresos en el parte y son cosas distintas. El nombre conserva el sufijo ' PARTE FIRMADO' que usa Posventa.

### F-007 · Front de carga y revisión

estado **pendiente** · prioridad 7 · rigor `estandar` · SDD sí · rama `feature/F-007-front`

Front estático (HTML + Tailwind CDN + Alpine.js + dev_server.py) siguiendo el patrón de front-nominas: arrastrar PDF/ZIP o elegir carpeta, progreso parte a parte, semáforo de validación, y revisión manual de lo dudoso antes de archivar. PUNTO DE PARTIDA: el esqueleto del front ya está escrito y verificado en la rama feature/F-007-front (se sacó de F-001 porque su dev_server.py hundía la puerta de cobertura). Recuperarlo con: git checkout feature/F-007-front -- services/postventa-front. Ya resuelto ahí: los scripts propios van SIN defer al final del body (con defer, Alpine arranca antes de que exista la función del x-data), Alpine con versión fija 3.14.1, el proxy apunta al puerto 7073, y el staticwebapp.config.json lleva <TENANT_ID> como marcador porque el ID de tenant no se versiona.

### F-008 · Modelo de posventa en Sigrid: confirmar contra el ERP

estado **pendiente** · prioridad 8 · rigor `documental` · SDD no · rama `feature/F-008-modelo-sigrid`

Confirmar contra el ERP lo que ya está documentado en azure-apps/sigrid_tablas.md, sigrid_api.md §9 y docs/referencia/01_cierre_incidencia_sigrid.md. Lo crítico: el proceso 'Cerrar parte' de Sigrid comprueba que la reclamación tenga un gráfico asociado, y existe una opción 6 'Cerrar parte sin archivo (RPV)'. Hay que averiguar qué escribe realmente cada uno de esos dos procesos antes de decidir el alcance del cierre. Además: el con.tip de la reclamación y el estado CERRADA en conest (el estado PENDIENTE es 3/PTE), en qué base vive gra, y si 'Asociar URL de Internet' permite referenciar el PDF de SharePoint en vez de incrustar el binario. Solo lecturas.

### F-009 · Cierre de la incidencia en Sigrid (solo estado)

estado **pendiente** · prioridad 9 · rigor `critico` · SDD sí · rama `feature/F-009-cierre-sigrid`

Mover con.est de la reclamación al estado CERRADA, resuelto contra conest y nunca hardcodeado. OJO: el proceso 'Cerrar parte' del ERP exige que la reclamación tenga un gráfico asociado; un UPDATE directo se saltaría esa comprobación. El alcance real de esta feature depende de lo que F-008 averigüe sobre ese proceso y sobre la opción 'Cerrar parte sin archivo (RPV)'. Dry-run primero, el usuario confirma en el front, y entonces commit. Con preferencia por usuario para pasarlo a automático.

### F-010 · Despliegue en Azure y tarjeta en el portal

estado **pendiente** · prioridad 10 · rigor `estandar` · SDD sí · rama `feature/F-010-despliegue`

Scripts re-ejecutables en infra/ para Function App y Static Web App con auth de Entra, grupo de seguridad de Posventa (hay que crearlo) y alta de la tarjeta en front-portal. La tarjeta se edita en ese repositorio, no en este.

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

Ningún test unitario detecta que un cambio de redacción de config/prompts.yaml empeore la extracción: en la suite el modelo está simulado y todo seguiría verde con el prompt roto. Esta feature crea el evaluador que falta —juego de partes de prueba con su verdad esperada, llamada real con credencial, umbral de acierto por campo e informe con veredicto— y, solo cuando ese comando exista, declara harness/rutas_sensibles.json para que tocar el prompt obligue a presentar evidencia. OJO A LA REGLA DE PROPAGACIÓN: el evaluador es genérico (vale igual para partes y albaranes), así que el mecanismo se porta a arnes-base en el mismo trabajo; aquí se queda solo el juego de partes y el umbral, que sí son de este dominio. El borrador de la declaración está en specs/F-003-extraccion/design.md.

### F-016 · Interpretación automática de las observaciones manuscritas

estado **pendiente** · prioridad 16 · rigor `critico` · SDD sí · rama `feature/F-016-interpretacion-observaciones`

Hoy F-004 rechaza en bloque cualquier parte con observaciones manuscritas y lo manda entero a la cola de validación humana, dé lo mismo que ponga 'falta rematar el rodapié' o 'firmado a satisfacción'. Esta feature interpreta el texto que ya transcribe F-003 para distinguir la observación inocua —una nota, una aclaración, un comentario que no discute la reparación— de la que de verdad impide dar la reparación por buena, y así reducir la cola humana a lo que la merece. Mejora posterior, no bloqueante: el circuito funciona sin ella, solo con más trabajo manual. En la remesa real de Mirasierra la cola serían 2 de 22 partes (~9 %), así que el ahorro se mide antes de complicar el modelo. Ante la duda, a la cola: la clasificación nunca da por buena una reparación por su cuenta si no está segura.

### F-017 · Mejoras de CHECKPOINTS: verificaciones manuales y cobertura no medida

estado **pendiente** · prioridad 17 · rigor `documental` · SDD no · rama `feature/F-017-checkpoints-manual`

Dos propuestas que dejó la review de F-003, aparcadas por el humano el 2026-08-19 como baja prioridad. (P2) C5 exige hoy todas las tareas de tasks.md en [x], pero el nivel de rigor critico OBLIGA a tener verificaciones MANUAL (humano) que ningún agente puede ejecutar: el reviewer queda entre rechazar un trabajo impecable, marcar como hecho algo que nadie ejecutó, o aprobar saltándose la letra de C5. Pasó con F-003 y lo único que impidió cerrarla con T18 sin ejecutar fue una nota escrita a mano en progress/current.md. Se propone que C5 distinga la tarea de agente pendiente (trabajo incompleto, CHANGES_REQUESTED) de la tarea MANUAL (humano) pendiente (estado propio: aprobado pero no cerrable hasta que el humano la ejecute). (P3) Que C4 bis nombre explícitamente la comprobación de ficheros «no medidos» en la puerta de cobertura, que hoy se hace pero no está escrita. Las dos son GENÉRICAS: se portan a arnes-base en el mismo trabajo, según la regla de propagación de CLAUDE.md.

### F-001 · Esqueleto del monorepo y /health

estado **terminada** · prioridad 1 · rigor `estandar` · SDD no · rama `feature/F-001-esqueleto`

Crear services/postventa-api (Function App Python con settings, logging y un endpoint /health) y services/postventa-front vacío pero arrancable. Feature de calentamiento: valida el circuito completo del arnés antes de jugarse nada.

### F-002 · Ingesta y troceado de la remesa en partes

estado **terminada** · prioridad 2 · rigor `critico` · SDD sí · rama `feature/F-002-ingesta-troceado`

Normalizar la entrada (PDF suelto, ZIP, varios ficheros) a una lista de PDFs, y trocear cada remesa en documentos de UN parte detectando el comienzo por la plantilla impresa. Endpoint POST /split. Se diseña contra los partes reales de muestras/.

### F-003 · Extracción multimodal del parte, manuscritos incluidos

estado **terminada** · prioridad 3 · rigor `critico` · SDD sí · rama `feature/F-003-extraccion`

Adaptador de IA tras ExtractorPort, arrancando con gemini-3.7-flash (el modelo que usa Ruesma; azure-apps documenta el proveedor pero no fija version), configurable por GEMINI_MODEL. Extrae promoción, código de obra, unidad (el papel la imprime como 'Vivienda'), nº de incidencia, fecha de servicio, descripción y lo escrito a mano: DNI y observaciones. Lee además el 'Página N' del pie, que F-014 necesitará para reagrupar el parte de dos hojas. CERRADA el 2026-08-19: revisión APROBADA y última verificación manual completada (T18, barrido de los 22 partes reales de Mirasierra), con el modelo leyendo la letra manuscrita y cero falsos negativos.
