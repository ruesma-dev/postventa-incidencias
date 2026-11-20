<!-- specs/F-040-volcado-sigrid/requirements.md -->
# F-040 · Volcar a Sigrid las incidencias aprobadas (el panel de volcado) — Requisitos

> Aprobada el 2026-10-07 (D-1..D-14, Q-1..Q-8); conciliada con `dev` el 2026-10-27 (C-1..C-6, respuestas del
> 2026-10-28) y con F-065 el 2026-10-31 (P-1..P-3, respondidas). Rigor **`critico`**. Solo el front; backend, F-059.
> **Puesta al día del 2026-11-18** (tras el merge de `dev` `4b1eb21`: F-038, F-071 y F-072 `done`): **condensada**
> para la puerta TAMAÑO sin quitar ni cambiar de sentido ningún requisito salvo las enmiendas **[E-1118]** (el
> texto íntegro anterior, con fichero y línea de cada contrato y las tablas de conciliación de sus §4–§6:
> `git show 4b1eb21:specs/F-040-volcado-sigrid/requirements.md`); **R63–R69 nuevos** (tipo de F-072, textos de su
> Q-11, decisiones del humano del 2026-11-05). **[D-n]** = decisión abierta de `design.md` §12, escrita con la
> opción recomendada. Lo hecho (Bloque 1, T4, T5.1, T5.2, T6a) no se rehace.

## 0 · De dónde sale

Lo aprobado en la bandeja se crea en Sigrid con **ensayo previo y confirmación**, en lote, su número vuelve a la
bandeja y **reintentar no duplica**. F-059 da las rutas (`GET /api/volcado`, `POST /api/volcado/ensayo` y
`/volcar`); F-065, la sincronización y la guarda del ensayo (C-4: **sincronizar antes de registrar**). Volumen
real: la VILLA 15 de la 0677, ~285 incidencias = 57 trozos de 5; su volcado es del humano, no de la ficha (C-2).
**[E-1118]** Desde F-072 (en producción el 2026-11-18) cada incidencia lleva su **tipo de reclamación** (código de
`dbo.auxtrcp`); el backend pone el **tipo efectivo** en el `envio` de cada parte y lo manda; el panel no lo calcula.

## 0.1 · Glosario

Los de F-059 (candidata, referencia, ensayo, volcado, llamada, en duda), más:
- **Trozo**: como mucho `partes_por_llamada` incidencias (hoy 5). **Sincronización**: `GET /api/revision/sigrid`.
- **Va / ya existe / choca**: los grupos del veredicto de F-065. **Va** = `va` + `se_enlaza` (marcada «se enlaza
  con RS…», P-1); **ya existe** = `ya_existe`; **choca** = `choca` (criterios, o su parte `PVI-` en `NPR`).
- **Sin respuesta del servicio**: `ErrorApi` con `http` nulo (red o corte de 40 s); en un volcado **no** dice que
  no se haya escrito.
- **[E-1118] Tipo efectivo**: `tipo_reclamacion`, o `0002` si es nulo (F-072 R19). **Su etiqueta**: la de
  `catalogo.listados` de `GET /api/revision` (`<res> (<cod>)`, F-072 R20), que la página ya tiene.

## 1 · El panel (D-2)

- **R50.** `bandeja.html` debe tener un panel «Volcado a Sigrid» con su lógica en `js/volcado.js`, montado dentro
  del **único** `x-data="appRevision()"` (R70 de F-035). CUANDO la bandeja carga una obra, el panel debe pedir
  `GET /api/volcado` y enseñar aprobadas, en duda y volcadas, cuántas candidatas y en cuántos trozos, y que el
  ensayo no crea nada. Su único botón de entrada es **«Registrar»** (R60). (capa: unit)
- **R60.** CUANDO se pulsa «Registrar», el panel debe, en este orden: (1) pedir la sincronización **una vez**,
  `sinReintentos`; (2) enseñar el resultado (R61) y esperar; (3) solo con otro clic, ensayar y volcar (R51–R53).
  SI la sincronización no responde 200 o queda sin respuesta, ENTONCES debe parar sin ensayar ni dejar ensayar y
  decirlo según el error (`design.md` §3.2: 400, los tres 409, el 503 **sin `codigo`**). (capa: unit)
- **R61.** Tras la sincronización, el panel debe enseñar cada fila de `volcado.veredictos` en su grupo —va (con
  `se_enlaza` marcado y su código), ya existe (con sus `sigrid_cods`), choca (cada reclamación con su estado,
  unidad, ubicación, oficio y descripción, y por qué choca: «su parte está anulado en Sigrid» si es la emparejada,
  o los `criterios` y el `parecido` de su `coincide`)— y el **recuento por unidad** de cada grupo, de
  `volcado.por_unidad`, con el nombre del `catalogo` (sin nombre, el código). No enseña la `ficha` (datos
  personales) ni guarda la respuesta fuera de la memoria de la página. (capa: unit)
- **R62.** Lo que **ya existe** no se ensaya ni se vuelca, y ningún botón lo incluye. Lo que **choca** solo se
  ensaya con un **segundo clic por incidencia** (casilla, sin «todas las de la unidad», P-2) y viaja en
  `conflictos_confirmados` con todos sus `sigrid_cods`, solo las del trozo; en una que choca por `NPR`, el texto
  dice que incluirla **la enlaza con el parte anulado**. SI el ensayo excluye una con `duplicada_en_sigrid` o
  `conflicto_sin_confirmar` (Sigrid cambió desde la sincronización), ENTONCES el panel debe enseñarla en las
  excluidas con su texto y ofrecer «Volver a registrar». (capa: unit)

### 1.1 · Ensayo y volcado

- **R51.** CUANDO se pide el ensayo, el panel debe partir **lo que nombra la sincronización** (va y las que chocan
  incluidas; una candidata aprobada después de sincronizar se cuenta aparte y pide «Volver a registrar») en trozos
  de `partes_por_llamada`, pedir los ensayos **de uno en uno** con «trozo k de M» y enseñar juntos cada parte con
  unidad, oficio y proveedor (nombres del `catalogo`; sin nombre, el código del `envio`), ubicación, descripción,
  **tipo (R63) [E-1118]** y estado (`previsto` «Se crearía», `idempotente` «Ya estaba creado», `rechazado` «No se
  crea» y `no_procesado` «No se llegó a intentar», con el texto de su motivo), las excluidas con su motivo y el
  recuento por unidad de lo que se crearía. Un 200 sin `ensayo_id` es un trozo sin previstos, no un fallo. SI un
  ensayo no responde 200 o queda sin respuesta, ENTONCES la serie para, lo dice y no habilita el volcado. (capa: unit)
- **R52.** «Volcar N partes a Sigrid» (N = los `previsto` de todos los ensayos) solo se habilita con ≥ 1 previsto,
  todos los ensayos en 200, la caducidad más temprana sin alcanzar (cuenta atrás visible) y nada en vuelo, y tras
  una **confirmación explícita** (D-12: segundo clic y teclear N) cuyo texto dice el recuento por unidad (y por
  tipo, R64). Manda un volcado por ensayo con algún `previsto`, con su `ensayo_id` y solo sus `previsto` con su
  `revision_id`. `confirmado: true` aparece en **una sola** función de `js/volcado.js`. (capa: unit)
- **R53.** Los volcados van **de uno en uno**, en el orden de los ensayos, y: (1) SI el ensayo de un trozo ya
  caducó, ENTONCES no se manda y se pide volver a registrar lo que queda; (2) SI un volcado no responde 200, queda
  sin respuesta o trae algún `sin_respuesta`, ENTONCES el panel **para**, enseña qué quedó creado, en duda y sin
  mandar, y **no reintenta solo** (ensayo y volcado van `sinReintentos`); (3) el texto de la parada sale del
  `codigo` (`design.md` §3.2: 503 `volcado_deshabilitado` = ventana cerrada; 502 `volcado_sin_respuesta` = en
  duda, repetir es seguro; sin respuesta = no se sabe hasta releer); (4) el resultado enseña creados (con su
  `RS…`), ya creados, rechazados, no procesados y excluidas con su motivo, en duda, sin mandar y los **avisos** de
  posible duplicado; (5) al terminar o parar, y tras ensayos con algún `idempotente`, relee `GET /api/volcado` y
  la primera página de la bandeja; (6) **«Volver a registrar»** es el único reintento: repite R60 desde la
  sincronización y es como se reanuda un volcado parado. (capa: unit)
- **R54.** La presentación de `volcada` y `en_duda` en la lista es de F-038 R21. El panel debe tener texto en
  castellano para **cada** motivo de exclusión de F-059 y de F-065, cada causa de `ensayo_no_valido`, cada
  `codigo` de error de las tres rutas, de la guarda y de la sincronización, y el 503 sin `codigo`; los de §8.9, por
  `Revision.textoMotivoVolcado`, sin copiar su tabla. Un código desconocido sale tal cual. (capa: unit)
- **R55.** Ni correo ni `oid` van a `console` ni al almacenamiento del navegador, ni nada de la respuesta de la
  sincronización (`no-store`, datos personales). MIENTRAS haya una serie en marcha, salir de la página debe
  preguntar, con la **misma** guarda de salida de `bandeja.html` (F-038 R13), ampliada. (capa: unit)
- **R56.** Nada sale sin un clic: cargar solo lee; sincronizar, ensayar y volcar solo desde `@click`; con una
  petición en vuelo, ningún botón de «Registrar», ensayo ni volcado. (capa: unit)
- **R59.** Tras un volcado con algún `creado`, el panel debe decir que quedan **en SAT** y que Posventa los pasa
  **a PTE a mano** (Q-3), que es cuando Sigrid avisa al industrial. (capa: unit)

### 1.2 · El tipo de reclamación y los textos de Q-11 de F-072 [E-1118]

- **R63.** La columna «Tipo» del ensayo debe enseñar el `envio.tipo` de cada parte con su etiqueta de
  `catalogo.listados`; SI el código no está en la lista (de baja o desconocido), ENTONCES el código tal cual. La
  tabla fija `TEXTO_TIPO` («siempre `0002`», Q-1 de 2026-10-07) desaparece. (capa: unit)
- **R64.** [D-2] CUANDO los `previsto` llevan más de un tipo, el resumen del ensayo y el texto de la confirmación
  (R52) deben decir además el recuento por tipo, con su etiqueta; con uno solo, el texto no cambia. (capa: unit)
- **R65.** CUANDO un parte del ensayo vuelve `rechazado` con `tipo_no_valido` (tipo dado de baja entre aprobar y
  volcar; el volcado no relee `auxtrcp`, F-072 R29), el panel debe enseñarlo «No se crea» con un texto que diga qué
  hacer [D-1]: «El tipo de reclamación no existe o está de baja en Sigrid: cambia el tipo en la revisión y vuelve
  a aprobarla». No cuenta en N. El texto vive en `TEXTO_MOTIVO_VOLCADO` de `js/revision.js`. (capa: unit)
- **R66.** La revisión de `bandeja.html` debe reconocer el motivo `tipo_fuera_de_sigrid` (F-072 R24): en
  `MOTIVOS` de `js/revision.js` entre `proveedor_ambiguo` y `duplicada`, con el texto [D-1] «El tipo de reclamación
  ya no está vigente en Sigrid: elige otro», y el resumen cuenta diez motivos. Una incidencia con ese motivo no se
  puede aprobar, así que nunca es candidata nueva al volcado. (capa: unit)
- **R67.** El campo «Listado» del formulario de la revisión debe rotularse [D-1] «Listado (tipo de reclamación)» y
  ofrecer los tipos de `catalogo.listados`; [D-3] sin la opción en blanco «Sin listado» (el backend nunca devuelve
  nulo: el blanco ya es `0002`), y SI el tipo de la incidencia no está entre los vigentes, ENTONCES una opción más
  con su código y «(ya no vigente en Sigrid)», para guardar sin cambiarlo (F-072 R21). En el historial, el campo
  `listado` sale con su etiqueta o su código, nunca «sin listado». (capa: unit)

### 1.3 · Decisiones del humano del 2026-11-05 [E-1118]

- **R68.** La miga de pan de `bandeja.html` debe ser «Portal de posventa › Bandeja de revisión», con «Bandeja de
  revisión» como **texto sin enlace** (`<span aria-current="page">`), no un enlace a `./#/bandeja`. (capa: unit)
- La **tarjeta 02 del inicio a «En producción»** ya la hizo F-038 (T8, 2026-11-12); T6 solo lo comprueba.

### 1.4 · La primera escritura real [E-1118]

- **R69.** El primer volcado real con el panel debe hacerse **desde el entorno desplegado**, en la obra 0626 (Q-4,
  C-6), con un ensayo previo en la página, la ventana `VOLCADO_HABILITADO` abierta solo para ese volcado y la
  **autorización expresa del humano en el chat** para esa escritura (`tasks.md` T5.4). Ningún test ni script local
  debe llamar a `/api/volcado/volcar` ni a Sigrid. (capa: integración; MANUAL)

## 2 · El cierre de la ficha en el portal

- **R57.** En **un solo commit** que también pone F-040 en `done` (como D-11 de F-038): fuera los restos de F-040
  de la maqueta (`design.md` §4: el bloque `data-en-construccion="F-040"` de `index.html#/bandeja`, lo de
  `MaquetaDatos.volcado` que solo le servía, las tres entradas `bandeja.*Volcado`/`bandeja.volcar` de
  `PLACEHOLDERS` y sus funciones), con los catálogos `tipos`, `formas` y `oficios` **mudados**, no borrados. [D-4]
  [E-1118] El enlace a `bandeja.html` ya lo puso F-038 (tarjeta «Revisar la bandeja»): no se añade otro, y su
  texto y el de la tarjeta 02 del inicio dicen también que lo aprobado se vuelca a Sigrid. Las guardias de F-035
  siguen en verde; F-039 y F-043 conservan sus restos. (capa: unit)
- **R58.** `services/postventa-front/README.md` y `docs/ARCHITECTURE.md` deben contar el panel (hecho en T2;
  [E-1118] fuera el «sin publicar todavía» de `ARCHITECTURE.md`, publicado el 2026-11-02, y el tipo de R63);
  [E-1118] `docs/INTEGRACION.md` y su copia `azure-apps/postventa_incidencias.md` dejan de hablar de F-040 en
  futuro («volcará», «sin la página de F-040, solo llamando a las rutas»). (capa: unit)

## 3 · Fuera de alcance

| Qué | Dónde |
|---|---|
| Ensayo, volcado, ventana, tipo efectivo; sincronización y guarda; `volcada`/`en_duda` en la lista | **F-059**, **F-072**; **F-065**; **F-038 R21** |
| Pasar a PTE (Q-3); abrir o cerrar la ventana; el volcado de la VILLA 15 (C-2) | Posventa a mano; `infra/27_…`; el humano |
| Industrial propuesto; aprobar en bloque (C-5); conflictos en la lista; `N` (Q-8); recrear un anulado (Q-5) | F-039; F-043; F-064; más adelante; nadie |
| [E-1118] Leer `auxtrcp` desde el front o elegir el tipo en el panel | Nadie: el tipo se elige en la revisión (F-072) |
| [E-1118] Restos de F-072 en `docs/INTEGRACION.md` («sin desplegar», «DDL al arrancar»; los fija `test_f072_documentacion.py`) | El líder, aparte (`progress/history.md`, F-072) |
