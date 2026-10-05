// services/postventa-front/js/maqueta_datos.js
// F-035 · R23-R26 y R38-R41 · Los datos de ejemplo de la maqueta del portal.
//
// SOLO DATOS (`design.md` §7). Todo lo que pinta el portal sale de aquí,
// agrupado en bloques; cada bloque declara con `ficha: "F-0NN"` la ficha que
// lo sustituirá por datos reales y que, en el mismo trabajo, lo borrará
// (`design.md` §7.3). La guardia de la raíz (`tests/test_f035_placeholders_vivos.py`)
// lee esas líneas como texto: por eso cada `ficha` va escrita literal.
//
// Todo es EVIDENTEMENTE FICTICIO (R24): obras 99NN con «EJEMPLO» en el nombre,
// partes RS99…, unidades 99NN.03VILLA N., propietarios 99NN_REF/NNNN,
// personas 99NN_PER/NNNN, proveedores EJNN, referencias PVI-EJEMPLO-NNNN y
// correos en el dominio reservado ejemplo.invalid. Ni un DNI, ni un teléfono,
// ni un texto de un parte escaneado.
//
// Lo que NO es ficticio, a propósito (decisión D-10): los catálogos generales
// de Sigrid —estados de conest, tipos de reclamación, formas de comunicación y
// oficios— van con sus códigos y resúmenes reales, porque no son datos de
// nadie y son lo que Posventa reconoce al validar la maqueta. Fuente:
// `docs/referencia/04_alta_incidencia_sigrid.md` y el contrato del alta en
// lote de `azure-apps/sigrid_api.md` §8.9.
//
// El objeto se congela entero (R23): la maqueta enseña, no cambia sus datos.

(function () {
  "use strict";

  // ── Piezas que se repiten (todas ficticias) ───────────────────────────────

  /** Proveedores de ejemplo, código EJNN. */
  const PRV = {
    EJ01: { cod: "EJ01", res: "Carpintería PVC Ejemplo, S.L." },
    EJ02: { cod: "EJ02", res: "Electricidad Ejemplo, S.L." },
    EJ03: { cod: "EJ03", res: "Impermeabilizaciones Ejemplo, S.L." },
    EJ04: { cod: "EJ04", res: "Jardinería Ejemplo, S.L." },
    EJ05: { cod: "EJ05", res: "Carpintería de Madera Ejemplo, S.L." },
    EJ06: { cod: "EJ06", res: "Carpintería Ejemplo Dos, S.L." },
    EJ07: { cod: "EJ07", res: "Electricidad Ejemplo Sur, S.L." },
  };

  /** Unidades de posventa: villas de las tres obras de ejemplo. */
  const UPV = {
    "9901-1": { cod: "9901.03VILLA 1.", res: "Villa 1 (ejemplo)" },
    "9901-2": { cod: "9901.03VILLA 2.", res: "Villa 2 (ejemplo)" },
    "9901-3": { cod: "9901.03VILLA 3.", res: "Villa 3 (ejemplo)" },
    "9901-4": { cod: "9901.03VILLA 4.", res: "Villa 4 (ejemplo)" },
    "9901-5": { cod: "9901.03VILLA 5.", res: "Villa 5 (ejemplo)" },
    "9901-6": { cod: "9901.03VILLA 6.", res: "Villa 6 (ejemplo)" },
    "9902-1": { cod: "9902.03VILLA 1.", res: "Villa 1 (ejemplo)" },
    "9902-2": { cod: "9902.03VILLA 2.", res: "Villa 2 (ejemplo)" },
    "9902-3": { cod: "9902.03VILLA 3.", res: "Villa 3 (ejemplo)" },
    "9902-4": { cod: "9902.03VILLA 4.", res: "Villa 4 (ejemplo)" },
    "9902-5": { cod: "9902.03VILLA 5.", res: "Villa 5 (ejemplo)" },
    "9902-6": { cod: "9902.03VILLA 6.", res: "Villa 6 (ejemplo)" },
    "9903-1": { cod: "9903.03VILLA 1.", res: "Villa 1 (ejemplo)" },
    "9903-2": { cod: "9903.03VILLA 2.", res: "Villa 2 (ejemplo)" },
    "9903-3": { cod: "9903.03VILLA 3.", res: "Villa 3 (ejemplo)" },
    "9903-4": { cod: "9903.03VILLA 4.", res: "Villa 4 (ejemplo)" },
  };

  /** Propietarios: los copia Sigrid de la unidad al crear el parte. */
  const REF = {
    "9901-1": { cod: "9901_REF/0001", res: "Propietario Ejemplo 1 (Norte)" },
    "9901-2": { cod: "9901_REF/0002", res: "Propietario Ejemplo 2 (Norte)" },
    "9901-3": { cod: "9901_REF/0003", res: "Propietario Ejemplo 3 (Norte)" },
    "9901-4": { cod: "9901_REF/0004", res: "Propietario Ejemplo 4 (Norte)" },
    "9901-5": { cod: "9901_REF/0005", res: "Propietario Ejemplo 5 (Norte)" },
    "9901-6": { cod: "9901_REF/0006", res: "Propietario Ejemplo 6 (Norte)" },
    "9902-1": { cod: "9902_REF/0001", res: "Propietario Ejemplo 1 (Sur)" },
    "9902-2": { cod: "9902_REF/0002", res: "Propietario Ejemplo 2 (Sur)" },
    "9902-3": { cod: "9902_REF/0003", res: "Propietario Ejemplo 3 (Sur)" },
    "9902-4": { cod: "9902_REF/0004", res: "Propietario Ejemplo 4 (Sur)" },
    "9902-5": { cod: "9902_REF/0005", res: "Propietario Ejemplo 5 (Sur)" },
    "9902-6": { cod: "9902_REF/0006", res: "Propietario Ejemplo 6 (Sur)" },
    "9903-1": { cod: "9903_REF/0001", res: "Propietario Ejemplo 1 (Este)" },
    "9903-2": { cod: "9903_REF/0002", res: "Propietario Ejemplo 2 (Este)" },
    "9903-3": { cod: "9903_REF/0003", res: "Propietario Ejemplo 3 (Este)" },
    "9903-4": { cod: "9903_REF/0004", res: "Propietario Ejemplo 4 (Este)" },
  };

  /** Personas que reclaman: también las copia Sigrid de la unidad. */
  const PER = {
    "9901-1": { cod: "9901_PER/0001", res: "Persona Ejemplo 1 (Norte)" },
    "9901-2": { cod: "9901_PER/0002", res: "Persona Ejemplo 2 (Norte)" },
    "9901-3": { cod: "9901_PER/0003", res: "Persona Ejemplo 3 (Norte)" },
    "9901-4": { cod: "9901_PER/0004", res: "Persona Ejemplo 4 (Norte)" },
    "9901-5": { cod: "9901_PER/0005", res: "Persona Ejemplo 5 (Norte)" },
    "9901-6": { cod: "9901_PER/0006", res: "Persona Ejemplo 6 (Norte)" },
    "9902-1": { cod: "9902_PER/0001", res: "Persona Ejemplo 1 (Sur)" },
    "9902-2": { cod: "9902_PER/0002", res: "Persona Ejemplo 2 (Sur)" },
    "9902-3": { cod: "9902_PER/0003", res: "Persona Ejemplo 3 (Sur)" },
    "9902-4": { cod: "9902_PER/0004", res: "Persona Ejemplo 4 (Sur)" },
    "9902-5": { cod: "9902_PER/0005", res: "Persona Ejemplo 5 (Sur)" },
    "9902-6": { cod: "9902_PER/0006", res: "Persona Ejemplo 6 (Sur)" },
    "9903-1": { cod: "9903_PER/0001", res: "Persona Ejemplo 1 (Este)" },
    "9903-2": { cod: "9903_PER/0002", res: "Persona Ejemplo 2 (Este)" },
    "9903-3": { cod: "9903_PER/0003", res: "Persona Ejemplo 3 (Este)" },
    "9903-4": { cod: "9903_PER/0004", res: "Persona Ejemplo 4 (Este)" },
  };

  // Formas de comunicación y tipos de reclamación, por código (catálogos de
  // `volcado.catalogos`). «1» es «Escrita», el defecto del contrato.
  const ESCRITA = "1";
  const PRIMER_LISTADO = "0002";

  // ── Los bloques ───────────────────────────────────────────────────────────

  const MaquetaDatos = {
    // Tres obras de ejemplo. Las usan la bandeja, las incidencias, el volcado
    // y el coste; las retira F-041, que es la primera que lee obras reales.
    obras: {
      ficha: "F-041",
      filas: [
        { cod: "9901", res: "PROMOCIÓN EJEMPLO NORTE" },
        { cod: "9902", res: "PROMOCIÓN EJEMPLO SUR" },
        { cod: "9903", res: "PROMOCIÓN EJEMPLO ESTE" },
      ],
    },

    // Importar el Excel de la propiedad ya no es maqueta: F-036 está done y
    // vive en `importar.html` (`design.md` §16.5). Su bloque `entrada` se
    // retiró en la enmienda del 2026-10-05 (§7.3).

    // La web de clientes es un proyecto independiente (`design.md` §5.2).
    web: {
      ficha: "F-037",
      origen: "Web",
      pendientes: [
        "Pendiente: contrato de entrada, bloqueado por la web de clientes y por la importación del Excel",
      ],
    },

    // Lo importado, ANTES de Sigrid (`design.md` §5.3). Vocabulario de
    // revisión propio, a cerrar en F-038; «duplicada» es una marca aparte.
    bandeja: {
      ficha: "F-038",
      origenes: ["Excel", "Web"],
      estadosRevision: ["nueva", "editada", "aprobada", "descartada", "volcada"],
      filas: [
        {
          id: "BJ-0001",
          origen: "Excel",
          estado: "nueva",
          duplicada: false,
          fecha: "2026-09-10",
          obra: "9901",
          unidad: UPV["9901-2"],
          descripcionCorta: "Humedad en el techo del baño (ejemplo)",
          descripcionLarga: "Mancha de humedad en el techo del baño principal, junto al extractor (ejemplo).",
          ubicacion: "baño principal",
          oficio: "0021",
          tipo: PRIMER_LISTADO,
          forma: ESCRITA,
          propietario: REF["9901-2"],
          persona: PER["9901-2"],
          intervinientes: [{ oficio: "0021", proveedor: PRV.EJ03, causante: true }],
          referenciaExterna: "PVI-EJEMPLO-0001",
          codSigrid: null,
        },
        {
          // La fila de Excel «sin completar»: ni ubicación ni oficio (R38), y
          // sin oficio no hay de dónde proponer industrial (F-039).
          id: "BJ-0002",
          origen: "Excel",
          estado: "nueva",
          duplicada: false,
          fecha: "2026-09-10",
          obra: "9901",
          unidad: UPV["9901-3"],
          descripcionCorta: "Enchufe del salón sin corriente (ejemplo)",
          descripcionLarga: "El enchufe junto a la ventana del salón no da corriente (ejemplo).",
          ubicacion: null,
          oficio: null,
          tipo: PRIMER_LISTADO,
          forma: ESCRITA,
          propietario: REF["9901-3"],
          persona: PER["9901-3"],
          intervinientes: null,
          referenciaExterna: "PVI-EJEMPLO-0002",
          codSigrid: null,
        },
        {
          // La ÚNICA fila con tipo 0003, para enseñar su pendiente (R39).
          id: "BJ-0003",
          origen: "Excel",
          estado: "editada",
          duplicada: false,
          fecha: "2026-09-10",
          obra: "9901",
          unidad: UPV["9901-4"],
          descripcionCorta: "Puerta de armario descuadrada (ejemplo)",
          descripcionLarga: "La hoja del armario del dormitorio roza el marco al cerrar (ejemplo).",
          ubicacion: "dormitorio 1",
          oficio: "0143",
          tipo: "0003",
          forma: ESCRITA,
          propietario: REF["9901-4"],
          persona: PER["9901-4"],
          intervinientes: [{ oficio: "0143", proveedor: PRV.EJ05, causante: true }],
          referenciaExterna: "PVI-EJEMPLO-0003",
          codSigrid: null,
        },
        {
          id: "BJ-0004",
          origen: "Excel",
          estado: "aprobada",
          duplicada: false,
          fecha: "2026-09-10",
          obra: "9901",
          unidad: UPV["9901-5"],
          descripcionCorta: "Ventana del dormitorio no cierra (ejemplo)",
          descripcionLarga: "La ventana del dormitorio 2 no ajusta al cerrar y entra aire (ejemplo).",
          ubicacion: "dormitorio 2",
          oficio: "0005",
          tipo: PRIMER_LISTADO,
          forma: ESCRITA,
          propietario: REF["9901-5"],
          persona: PER["9901-5"],
          intervinientes: [{ oficio: "0005", proveedor: PRV.EJ01, causante: true }],
          referenciaExterna: "PVI-EJEMPLO-0004",
          codSigrid: null,
        },
        {
          id: "BJ-0005",
          origen: "Excel",
          estado: "aprobada",
          duplicada: false,
          fecha: "2026-09-11",
          obra: "9902",
          unidad: UPV["9902-1"],
          descripcionCorta: "Riego automático del jardín no arranca (ejemplo)",
          descripcionLarga: "El programador del riego no arranca a la hora fijada (ejemplo).",
          ubicacion: "jardín",
          oficio: "0024",
          tipo: PRIMER_LISTADO,
          forma: ESCRITA,
          propietario: REF["9902-1"],
          persona: PER["9902-1"],
          intervinientes: [{ oficio: "0024", proveedor: PRV.EJ04, causante: true }],
          referenciaExterna: "PVI-EJEMPLO-0005",
          codSigrid: null,
        },
        {
          // Duplicada de BJ-0005 (F-036) y descartada al revisarla.
          id: "BJ-0006",
          origen: "Excel",
          estado: "descartada",
          duplicada: true,
          fecha: "2026-09-11",
          obra: "9902",
          unidad: UPV["9902-1"],
          descripcionCorta: "Riego del jardín sin funcionar (ejemplo)",
          descripcionLarga: "El riego del jardín no funciona desde hace una semana (ejemplo).",
          ubicacion: "jardín",
          oficio: "0024",
          tipo: PRIMER_LISTADO,
          forma: ESCRITA,
          propietario: REF["9902-1"],
          persona: PER["9902-1"],
          intervinientes: [{ oficio: "0024", proveedor: PRV.EJ04, causante: true }],
          referenciaExterna: "PVI-EJEMPLO-0006",
          codSigrid: null,
        },
        {
          id: "BJ-0007",
          origen: "Web",
          estado: "nueva",
          duplicada: false,
          fecha: "2026-09-12",
          obra: "9903",
          unidad: UPV["9903-2"],
          descripcionCorta: "Luz del porche parpadea (ejemplo)",
          descripcionLarga: "La luz del porche parpadea al encenderla por la noche (ejemplo).",
          ubicacion: "porche",
          oficio: "0011",
          tipo: PRIMER_LISTADO,
          forma: ESCRITA,
          propietario: REF["9903-2"],
          persona: PER["9903-2"],
          intervinientes: [{ oficio: "0011", proveedor: PRV.EJ02, causante: true }],
          referenciaExterna: "PVI-EJEMPLO-0007",
          codSigrid: null,
        },
        {
          // Ya volcada: su código de Sigrid es el «creado» del volcado hecho.
          id: "BJ-0008",
          origen: "Web",
          estado: "volcada",
          duplicada: false,
          fecha: "2026-09-12",
          obra: "9902",
          unidad: UPV["9902-4"],
          descripcionCorta: "Puerta de entrada roza el suelo (ejemplo)",
          descripcionLarga: "La puerta de entrada roza el suelo al abrirla del todo (ejemplo).",
          ubicacion: "entrada",
          oficio: "0143",
          tipo: PRIMER_LISTADO,
          forma: ESCRITA,
          propietario: REF["9902-4"],
          persona: PER["9902-4"],
          intervinientes: [{ oficio: "0143", proveedor: PRV.EJ05, causante: true }],
          referenciaExterna: "PVI-EJEMPLO-0008",
          codSigrid: "RS99.09/0004",
        },
      ],
      // Quién y cuándo (criterio de F-038).
      historial: [
        { fila: "BJ-0003", fecha: "2026-09-11 09:20", usuario: "Usuario Ejemplo", accion: "Editada: tipo de reclamación" },
        { fila: "BJ-0004", fecha: "2026-09-11 09:35", usuario: "Usuario Ejemplo", accion: "Aprobada" },
        { fila: "BJ-0005", fecha: "2026-09-11 10:05", usuario: "Usuario Ejemplo", accion: "Aprobada" },
        { fila: "BJ-0006", fecha: "2026-09-11 10:06", usuario: "Usuario Ejemplo", accion: "Descartada: duplicada de BJ-0005" },
        { fila: "BJ-0008", fecha: "2026-09-12 12:40", usuario: "Usuario Ejemplo", accion: "Volcada a Sigrid" },
      ],
    },

    // Propuesta de industrial (F-039) y los oficios de cada obra con su
    // proveedor (`obrofc`), que es de donde sale la propuesta y la tabla de
    // intervinientes (`04_alta_incidencia_sigrid.md` §5). Una fila sin
    // propuesta: «no se inventa» (criterio de F-039).
    propuestas: {
      ficha: "F-039",
      porFila: {
        "BJ-0001": { proveedor: PRV.EJ03, motivo: "3 trabajos de impermeabilización en esta obra (ejemplo)" },
        "BJ-0002": null,
        "BJ-0003": { proveedor: PRV.EJ05, motivo: "2 trabajos de carpintería de madera en esta obra (ejemplo)" },
        "BJ-0004": { proveedor: PRV.EJ01, motivo: "4 trabajos de carpintería PVC en esta obra (ejemplo)" },
        "BJ-0005": { proveedor: PRV.EJ04, motivo: "1 trabajo de jardinería en esta obra (ejemplo)" },
        "BJ-0006": { proveedor: PRV.EJ04, motivo: "1 trabajo de jardinería en esta obra (ejemplo)" },
        "BJ-0007": { proveedor: PRV.EJ02, motivo: "2 trabajos de electricidad en esta obra (ejemplo)" },
        "BJ-0008": { proveedor: PRV.EJ05, motivo: "3 trabajos de carpintería de madera en esta obra (ejemplo)" },
      },
      oficiosObra: {
        "9901": [
          { oficio: "0005", proveedor: PRV.EJ01, comentario: "Carpintería exterior (ejemplo)" },
          { oficio: "0011", proveedor: PRV.EJ02, comentario: "Instalación eléctrica (ejemplo)" },
          { oficio: "0021", proveedor: PRV.EJ03, comentario: "Cubiertas y terrazas (ejemplo)" },
          { oficio: "0143", proveedor: PRV.EJ05, comentario: "Carpintería interior (ejemplo)" },
        ],
        // Dos proveedores del mismo oficio: de ahí el «interviniente_ambiguo».
        "9902": [
          { oficio: "0005", proveedor: PRV.EJ01, comentario: "Carpintería exterior (ejemplo)" },
          { oficio: "0011", proveedor: PRV.EJ07, comentario: "Instalación eléctrica (ejemplo)" },
          { oficio: "0021", proveedor: PRV.EJ03, comentario: "Cubiertas y terrazas (ejemplo)" },
          { oficio: "0024", proveedor: PRV.EJ04, comentario: "Zonas verdes (ejemplo)" },
          { oficio: "0143", proveedor: PRV.EJ05, comentario: "Puertas de paso (ejemplo)" },
          { oficio: "0143", proveedor: PRV.EJ06, comentario: "Armarios y rodapiés (ejemplo)" },
        ],
        "9903": [
          { oficio: "0011", proveedor: PRV.EJ02, comentario: "Instalación eléctrica (ejemplo)" },
          { oficio: "0021", proveedor: PRV.EJ03, comentario: "Cubiertas y terrazas (ejemplo)" },
          { oficio: "0024", proveedor: PRV.EJ04, comentario: "Zonas verdes (ejemplo)" },
          { oficio: "0143", proveedor: PRV.EJ06, comentario: "Carpintería interior (ejemplo)" },
        ],
      },
    },

    // Incidencias YA en Sigrid (`design.md` §5.4 y §5.5): doce, repartidas
    // entre los cinco estados de conest, por código (R21). Las del parte
    // archivado dicen dónde, con la estructura de Posventa y sin fichero (R41).
    incidencias: {
      ficha: "F-041",
      filas: [
        {
          id: "EJ-0001",
          cod: "RS99.01/0001",
          estado: "PTE",
          fecha: "2026-01-14",
          hora: "10:41",
          obra: "9901",
          unidad: UPV["9901-1"],
          descripcionCorta: "Humedad en la terraza (ejemplo)",
          descripcionLarga: "Aparece humedad en el techo del salón bajo la terraza tras las lluvias (ejemplo).",
          ubicacion: "terraza",
          oficio: "0021",
          tipo: PRIMER_LISTADO,
          forma: ESCRITA,
          propietario: REF["9901-1"],
          persona: PER["9901-1"],
          intervinientes: [{ oficio: "0021", proveedor: PRV.EJ03, causante: true }],
          referenciaExterna: "PVI-EJEMPLO-0101",
          correoAvisos: "propietario1.norte@ejemplo.invalid",
          parte: { guardado: false, archivado: false, adjunto: false, cerrado: false },
        },
        {
          // Dos intervinientes del mismo oficio, como en el alta manual.
          id: "EJ-0002",
          cod: "RS99.01/0002",
          estado: "SAT",
          fecha: "2026-01-20",
          hora: "09:15",
          obra: "9902",
          unidad: UPV["9902-2"],
          descripcionCorta: "Puerta de armario descuadrada (ejemplo)",
          descripcionLarga: "La puerta del armario empotrado no cierra: la hoja roza el marco (ejemplo).",
          ubicacion: "dormitorio 1",
          oficio: "0143",
          tipo: PRIMER_LISTADO,
          forma: ESCRITA,
          propietario: REF["9902-2"],
          persona: PER["9902-2"],
          intervinientes: [
            { oficio: "0143", proveedor: PRV.EJ05, causante: true },
            { oficio: "0143", proveedor: PRV.EJ06, causante: false },
          ],
          referenciaExterna: "PVI-EJEMPLO-0102",
          correoAvisos: "propietario2.sur@ejemplo.invalid",
          parte: { guardado: false, archivado: false, adjunto: false, cerrado: false },
        },
        {
          id: "EJ-0003",
          cod: "RS99.02/0003",
          estado: "SAT",
          fecha: "2026-02-03",
          hora: "12:02",
          obra: "9901",
          unidad: UPV["9901-3"],
          descripcionCorta: "Enchufe de la cocina sin corriente (ejemplo)",
          descripcionLarga: "El enchufe de la encimera de la cocina no da corriente (ejemplo).",
          ubicacion: "cocina",
          oficio: "0011",
          tipo: PRIMER_LISTADO,
          forma: ESCRITA,
          propietario: REF["9901-3"],
          persona: PER["9901-3"],
          intervinientes: [{ oficio: "0011", proveedor: PRV.EJ02, causante: true }],
          referenciaExterna: "PVI-EJEMPLO-0103",
          correoAvisos: "propietario3.norte@ejemplo.invalid",
          parte: { guardado: false, archivado: false, adjunto: false, cerrado: false },
        },
        {
          id: "EJ-0004",
          cod: "RS99.02/0004",
          estado: "PTE",
          fecha: "2026-02-18",
          hora: "16:30",
          obra: "9903",
          unidad: UPV["9903-1"],
          descripcionCorta: "Filtración en la ventana del salón (ejemplo)",
          descripcionLarga: "Entra agua por el alféizar de la ventana del salón cuando llueve (ejemplo).",
          ubicacion: "salón",
          oficio: "0021",
          tipo: PRIMER_LISTADO,
          forma: ESCRITA,
          propietario: REF["9903-1"],
          persona: PER["9903-1"],
          intervinientes: [{ oficio: "0021", proveedor: PRV.EJ03, causante: true }],
          referenciaExterna: "PVI-EJEMPLO-0104",
          correoAvisos: "propietario1.este@ejemplo.invalid",
          parte: { guardado: false, archivado: false, adjunto: false, cerrado: false },
        },
        {
          id: "EJ-0005",
          cod: "RS99.03/0005",
          estado: "TER",
          fecha: "2026-03-05",
          hora: "11:10",
          obra: "9902",
          unidad: UPV["9902-3"],
          descripcionCorta: "Riego del jardín con fuga (ejemplo)",
          descripcionLarga: "Pierde agua una tubería del riego junto al seto (ejemplo).",
          ubicacion: "jardín",
          oficio: "0024",
          tipo: PRIMER_LISTADO,
          forma: ESCRITA,
          propietario: REF["9902-3"],
          persona: PER["9902-3"],
          intervinientes: [{ oficio: "0024", proveedor: PRV.EJ04, causante: true }],
          referenciaExterna: "PVI-EJEMPLO-0105",
          correoAvisos: "propietario3.sur@ejemplo.invalid",
          parte: { guardado: true, archivado: true, adjunto: true, cerrado: false },
          carpetaArchivo: "9902  EJEMPLO SUR/PARTES INCIDENCIAS/VILLA 003/PARTES FIRMADOS",
        },
        {
          id: "EJ-0006",
          cod: "RS99.03/0006",
          estado: "CER",
          fecha: "2026-03-12",
          hora: "08:55",
          obra: "9901",
          unidad: UPV["9901-4"],
          descripcionCorta: "Persiana del dormitorio atascada (ejemplo)",
          descripcionLarga: "La persiana del dormitorio 2 se queda atascada a media altura (ejemplo).",
          ubicacion: "dormitorio 2",
          oficio: "0005",
          tipo: PRIMER_LISTADO,
          forma: ESCRITA,
          propietario: REF["9901-4"],
          persona: PER["9901-4"],
          intervinientes: [{ oficio: "0005", proveedor: PRV.EJ01, causante: true }],
          referenciaExterna: "PVI-EJEMPLO-0106",
          correoAvisos: "propietario4.norte@ejemplo.invalid",
          parte: { guardado: true, archivado: true, adjunto: true, cerrado: true },
          carpetaArchivo: "9901  EJEMPLO NORTE/PARTES INCIDENCIAS/VILLA 004/PARTES FIRMADOS",
        },
        {
          id: "EJ-0007",
          cod: "RS99.04/0007",
          estado: "NPR",
          fecha: "2026-04-02",
          hora: "13:20",
          obra: "9903",
          unidad: UPV["9903-3"],
          descripcionCorta: "Mancha en la fachada por uso (ejemplo)",
          descripcionLarga: "Mancha oscura en la fachada junto a la barbacoa (ejemplo).",
          ubicacion: "fachada",
          oficio: "0021",
          tipo: PRIMER_LISTADO,
          forma: ESCRITA,
          propietario: REF["9903-3"],
          persona: PER["9903-3"],
          intervinientes: [{ oficio: "0021", proveedor: PRV.EJ03, causante: false }],
          referenciaExterna: "PVI-EJEMPLO-0107",
          correoAvisos: "propietario3.este@ejemplo.invalid",
          parte: { guardado: false, archivado: false, adjunto: false, cerrado: false },
        },
        {
          id: "EJ-0008",
          cod: "RS99.04/0008",
          estado: "CER",
          fecha: "2026-04-16",
          hora: "10:05",
          obra: "9902",
          unidad: UPV["9902-5"],
          descripcionCorta: "Rodapié despegado en el pasillo (ejemplo)",
          descripcionLarga: "Un tramo del rodapié del pasillo se ha despegado de la pared (ejemplo).",
          ubicacion: "pasillo",
          oficio: "0143",
          tipo: PRIMER_LISTADO,
          forma: ESCRITA,
          propietario: REF["9902-5"],
          persona: PER["9902-5"],
          intervinientes: [{ oficio: "0143", proveedor: PRV.EJ06, causante: true }],
          referenciaExterna: "PVI-EJEMPLO-0108",
          correoAvisos: "propietario5.sur@ejemplo.invalid",
          parte: { guardado: true, archivado: true, adjunto: true, cerrado: true },
          carpetaArchivo: "9902  EJEMPLO SUR/PARTES INCIDENCIAS/VILLA 005/PARTES FIRMADOS",
        },
        {
          id: "EJ-0009",
          cod: "RS99.05/0009",
          estado: "PTE",
          fecha: "2026-05-07",
          hora: "17:45",
          obra: "9901",
          unidad: UPV["9901-6"],
          descripcionCorta: "Interruptor del baño no funciona (ejemplo)",
          descripcionLarga: "El interruptor de la luz del baño no enciende el punto de luz (ejemplo).",
          ubicacion: "baño",
          oficio: "0011",
          tipo: PRIMER_LISTADO,
          forma: ESCRITA,
          propietario: REF["9901-6"],
          persona: PER["9901-6"],
          intervinientes: [{ oficio: "0011", proveedor: PRV.EJ02, causante: true }],
          referenciaExterna: "PVI-EJEMPLO-0109",
          correoAvisos: "propietario6.norte@ejemplo.invalid",
          parte: { guardado: false, archivado: false, adjunto: false, cerrado: false },
        },
        {
          id: "EJ-0010",
          cod: "RS99.05/0010",
          estado: "TER",
          fecha: "2026-05-21",
          hora: "09:30",
          obra: "9903",
          unidad: UPV["9903-4"],
          descripcionCorta: "Arqueta del jardín hundida (ejemplo)",
          descripcionLarga: "La tapa de la arqueta del jardín se ha hundido en el césped (ejemplo).",
          ubicacion: "jardín",
          oficio: "0024",
          tipo: PRIMER_LISTADO,
          forma: ESCRITA,
          propietario: REF["9903-4"],
          persona: PER["9903-4"],
          intervinientes: [{ oficio: "0024", proveedor: PRV.EJ04, causante: true }],
          referenciaExterna: "PVI-EJEMPLO-0110",
          correoAvisos: "propietario4.este@ejemplo.invalid",
          parte: { guardado: true, archivado: false, adjunto: false, cerrado: false },
        },
        {
          id: "EJ-0011",
          cod: "RS99.06/0011",
          estado: "NPR",
          fecha: "2026-06-09",
          hora: "12:15",
          obra: "9902",
          unidad: UPV["9902-6"],
          descripcionCorta: "Arañazo en el suelo tras la mudanza (ejemplo)",
          descripcionLarga: "Arañazo en la tarima del salón que el propietario atribuye a la obra (ejemplo).",
          ubicacion: "salón",
          oficio: "0143",
          tipo: PRIMER_LISTADO,
          forma: ESCRITA,
          propietario: REF["9902-6"],
          persona: PER["9902-6"],
          intervinientes: [{ oficio: "0143", proveedor: PRV.EJ05, causante: false }],
          referenciaExterna: "PVI-EJEMPLO-0111",
          correoAvisos: "propietario6.sur@ejemplo.invalid",
          parte: { guardado: false, archivado: false, adjunto: false, cerrado: false },
        },
        {
          id: "EJ-0012",
          cod: "RS99.06/0012",
          estado: "SAT",
          fecha: "2026-06-23",
          hora: "15:50",
          obra: "9901",
          unidad: UPV["9901-2"],
          descripcionCorta: "Humedad bajo el lavabo (ejemplo)",
          descripcionLarga: "Mancha de humedad en el mueble bajo el lavabo del baño (ejemplo).",
          ubicacion: "baño",
          oficio: "0021",
          tipo: PRIMER_LISTADO,
          forma: ESCRITA,
          propietario: REF["9901-2"],
          persona: PER["9901-2"],
          intervinientes: [{ oficio: "0021", proveedor: PRV.EJ03, causante: true }],
          referenciaExterna: "PVI-EJEMPLO-0112",
          correoAvisos: "propietario2.norte@ejemplo.invalid",
          parte: { guardado: false, archivado: false, adjunto: false, cerrado: false },
        },
      ],
      // Los campos de la pestaña «Datos», cada uno con su origen (R25), en los
      // bloques de la ficha del parte de Sigrid (`design.md` §5.5 y su
      // enmienda). `clave` es la propiedad de la fila que lo rellena; `null`
      // si la maqueta no tiene dato de ejemplo para ese campo.
      campos: [
        { bloque: "Identificación", etiqueta: "Código", origen: "con.cod", clave: "cod", nota: "Serie RS<año>.<mes>/ más un correlativo: lo pone Sigrid al crear" },
        { bloque: "Identificación", etiqueta: "Estado", origen: "conest.cod", clave: "estado", nota: "Por código, nunca por su número" },
        { bloque: "Identificación", etiqueta: "Obra", origen: "upv.obride", clave: "obra", nota: "" },
        { bloque: "Identificación", etiqueta: "Unidad de posventa", origen: "rcp.upvide", clave: "unidad", nota: "" },
        { bloque: "Identificación", etiqueta: "Tipo de reclamación", origen: "rcp.trcpide", clave: "tipo", nota: "Catálogo auxtrcp; 0002 es el defecto del alta en lote" },
        { bloque: "Identificación", etiqueta: "Ubicación", origen: "rcp.resubi", clave: "ubicacion", nota: "Hasta 48 caracteres; en Sigrid es un desplegable" },
        { bloque: "Identificación", etiqueta: "Propietario", origen: "rcp.cliide", clave: "propietario", nota: "Los copia Sigrid de la unidad al crear" },
        { bloque: "Identificación", etiqueta: "Persona que reclama", origen: "rcp.recide", clave: "persona", nota: "Los copia Sigrid de la unidad al crear" },
        { bloque: "Identificación", etiqueta: "Persona de contacto", origen: "rcp.cntide", clave: null, nota: "Sin datos de ejemplo" },
        { bloque: "Identificación", etiqueta: "Teléfonos de avisos", origen: "rcp.tel", clave: null, nota: "Sin datos de ejemplo" },
        { bloque: "Identificación", etiqueta: "Correo de avisos", origen: "rcp.ele", clave: "correoAvisos", nota: "Destino del correo de «no procede»" },
        { bloque: "Datos de la reclamación", etiqueta: "Fecha / Hora", origen: ["rcp.fec", "rcp.hor"], clave: "fecha", nota: "" },
        { bloque: "Datos de la reclamación", etiqueta: "Clase", origen: "rcp.rcpide", clave: null, nota: "Catálogo auxrcp; vacía en el alta manual" },
        { bloque: "Datos de la reclamación", etiqueta: "Oficio", origen: "rcp.ofcide", clave: "oficio", nota: "Catálogo general auxofc; además tiene que ser un oficio de la obra" },
        { bloque: "Datos de la reclamación", etiqueta: "Forma de comunicación", origen: "rcp.rcptip", clave: "forma", nota: "1 es «Escrita», el defecto; el 0 no está documentado" },
        { bloque: "Datos de la reclamación", etiqueta: "Urgencia", origen: "rcp.texurg", clave: null, nota: "Sin datos de ejemplo" },
        { bloque: "Datos de la reclamación", etiqueta: "Motivo", origen: "rcp.motrcp", clave: null, nota: "Sin datos de ejemplo" },
        { bloque: "Datos de la reclamación", etiqueta: "Fecha prevista nueva visita", origen: "rcp.fecpre", clave: null, nota: "Sin datos de ejemplo" },
        { bloque: "Datos de la reclamación", etiqueta: "Descripción corta", origen: "con.res", clave: "descripcionCorta", nota: "Hasta 128 caracteres" },
        { bloque: "Datos de la reclamación", etiqueta: "Descripción larga", origen: "rcp.tex", clave: "descripcionLarga", nota: "" },
        { bloque: "Datos de la reclamación", etiqueta: "Solución", origen: "rcp.solrcp", clave: null, nota: "Vacía en todas: nadie la rellena" },
        { bloque: "Intervinientes", etiqueta: "Intervinientes", origen: ["rcpint.obrofcide", "obrofc.ofcide", "obrofc.prvide"], clave: "intervinientes", nota: "Oficios de la obra con su proveedor" },
        { bloque: "Intervinientes", etiqueta: "Causante", origen: "rcpint.cauave", clave: null, nota: "Columna de la tabla de intervinientes" },
        { bloque: "Intervinientes", etiqueta: "Industrial", origen: "pendiente", clave: null, nota: "", motivo: "cuál de los intervinientes es «el industrial» cuando hay varios lo confirman F-039 y F-040" },
        { bloque: "Intervinientes", etiqueta: "Industrial propuesto y motivo", origen: "propio", clave: null, nota: "Lo propone F-039" },
        { bloque: "Volcado", etiqueta: "Referencia externa", origen: "conext[RCPCLI]", clave: "referenciaExterna", nota: "«Nº Referencia Externo» de la ficha de Sigrid; la forma exacta la fija F-040" },
        { bloque: "Unidad y garantías", etiqueta: "Fin de vicios y defectos", origen: "upv.fecfin1", clave: null, nota: "Sin datos de ejemplo" },
        { bloque: "Unidad y garantías", etiqueta: "Habitabilidad / instalaciones", origen: ["upv.fecini2", "upv.fecfin2"], clave: null, nota: "Sin datos de ejemplo" },
        { bloque: "Unidad y garantías", etiqueta: "Inicio estructura", origen: "upv.fecini3", clave: null, nota: "Sin datos de ejemplo" },
        { bloque: "Unidad y garantías", etiqueta: "Escrituración", origen: "upv.fecesc", clave: null, nota: "Sin datos de ejemplo" },
        { bloque: "Unidad y garantías", etiqueta: "Visita del técnico acordada", origen: "upv.fecvtec", clave: null, nota: "Sin datos de ejemplo" },
      ],
      // «Queda histórico de cada cambio» (criterio de F-041).
      historial: [
        { incidencia: "EJ-0001", fecha: "2026-01-15 09:02", usuario: "Usuario Ejemplo", campo: "Estado", antes: "SAT", despues: "PTE" },
        { incidencia: "EJ-0005", fecha: "2026-03-20 13:40", usuario: "Usuario Ejemplo", campo: "Estado", antes: "PTE", despues: "TER" },
        { incidencia: "EJ-0006", fecha: "2026-03-28 10:12", usuario: "Usuario Ejemplo", campo: "Estado", antes: "TER", despues: "CER" },
        { incidencia: "EJ-0007", fecha: "2026-04-03 11:25", usuario: "Usuario Ejemplo", campo: "Estado", antes: "SAT", despues: "NPR" },
        { incidencia: "EJ-0009", fecha: "2026-05-08 08:47", usuario: "Usuario Ejemplo", campo: "Ubicación", antes: "aseo", despues: "baño" },
      ],
    },

    // «No procede» con correo al cliente (F-042). El destinatario es el
    // correo de avisos de la incidencia (ejemplo.invalid). En pruebas nunca
    // sale un correo a un cliente real.
    noProcede: {
      ficha: "F-042",
      plantillaCorreo: {
        asunto: "Respuesta a su incidencia de posventa (ejemplo)",
        saludo: "Estimado/a propietario/a:",
        cuerpo: "Hemos revisado su incidencia y no procede por el siguiente motivo:",
        despedida: "Un saludo, el departamento de Posventa (ejemplo).",
      },
      pendientes: ["Pendiente: buzón de envío — por decidir"],
    },

    // Impresión en bloque (F-044). La plantilla existe pero nadie la ha mirado:
    // la maqueta no dibuja nada que la imite.
    impresion: {
      ficha: "F-044",
      plantilla: "Plantilla de posventa",
      pendientes: [
        "Pendiente: la plantilla de posventa existe y está sin revisar; se revisa, con permiso, y se convierte a docs/referencia en la spec de F-044",
      ],
    },

    // Coste por capítulo de POSTV2 (F-046): una venta sin enlazar (null) y un
    // cero de verdad, para que se vean distintos (R22).
    capitulos: {
      ficha: "F-046",
      filas: [
        { obra: "9901", nombre: "PROMOCIÓN EJEMPLO NORTE", incidencias: 5, coste: 1250, venta: 1500 },
        { obra: "9902", nombre: "PROMOCIÓN EJEMPLO SUR", incidencias: 4, coste: 980, venta: null },
        { obra: "9903", nombre: "PROMOCIÓN EJEMPLO ESTE", incidencias: 3, coste: 0, venta: 0 },
      ],
      pendientes: ["Pendiente: de qué tablas sale el coste del capítulo — lo decide F-046"],
    },

    // Incidencia ↔ proforma ↔ coste ↔ venta (F-047): una enlazada y otra no.
    vinculos: {
      ficha: "F-047",
      porIncidencia: {
        "EJ-0001": { proforma: "PF-EJEMPLO-0001", coste: 320, venta: 400 },
        "EJ-0002": { proforma: null, coste: 150, venta: null },
      },
      pendientes: [
        "Pendiente: en qué momento y con qué campo se relaciona la incidencia con la proforma — lo investiga F-047",
      ],
    },

    // Lo que cada fase publicará en el datamart (F-048).
    datamart: {
      ficha: "F-048",
      filas: [
        { fase: "Entrada y revisión", dato: "Entradas importadas y su revisión", fichas: ["F-036", "F-038"], estado: "pendiente" },
        { fase: "Propuesta de industrial", dato: "Industrial propuesto y su motivo", fichas: ["F-039"], estado: "pendiente" },
        { fase: "Volcado a Sigrid", dato: "Lotes volcados y resultado por parte", fichas: ["F-040"], estado: "pendiente" },
        { fase: "Gestión", dato: "Cambios de estado e historial", fichas: ["F-041"], estado: "pendiente" },
        { fase: "No procede", dato: "Justificaciones y correos enviados", fichas: ["F-042"], estado: "pendiente" },
        { fase: "Partes y cierre", dato: "Partes firmados, sin firma y cierres", fichas: ["F-045"], estado: "pendiente" },
        { fase: "Coste y venta", dato: "Coste por capítulo y vínculo con la venta", fichas: ["F-046", "F-047"], estado: "pendiente" },
      ],
    },

    // El volcado a Sigrid (F-040), con el vocabulario del contrato del alta
    // en lote de `sigrid-api` (`azure-apps/sigrid_api.md` §8.9): estados por
    // parte, códigos de motivo y resumen. Solo se ENSEÑA; no se llama a nada.
    // Los catálogos del alta viven aquí porque existen para el volcado; si
    // F-038 los necesita antes, se los lleva (`design.md` §7.1).
    volcado: {
      ficha: "F-040",
      catalogos: {
        tipos: [
          { cod: "0002", res: "PRIMER LISTADO POSTVENTA" },
          // Sale por defecto en el escritorio y nadie sabe qué es (R39).
          { cod: "0003", res: null },
        ],
        formas: [{ cod: "1", res: "Escrita" }],
        oficios: [
          { cod: "0005", res: "Carpintería PVC" },
          { cod: "0011", res: "Electricidad" },
          { cod: "0021", res: "Impermeabilizaciones" },
          { cod: "0024", res: "Jardinería" },
          { cod: "0143", res: "Carpintería de madera" },
        ],
        estados: [
          { cod: "previsto", etiqueta: "Se crearía" },
          { cod: "creado", etiqueta: "Creado en Sigrid" },
          { cod: "idempotente", etiqueta: "Ya estaba creado: no se duplica" },
          { cod: "rechazado", etiqueta: "No se crea: hay que corregirlo" },
          { cod: "no_procesado", etiqueta: "No se llegó a intentar: se puede reenviar" },
        ],
        motivos: [
          "referencia_no_permitida",
          "referencia_duplicada_en_lote",
          "referencia_en_conflicto",
          "unidad_postventa_no_encontrada",
          "tipo_no_valido",
          "clase_no_valida",
          "oficio_no_esta_en_la_obra",
          "interviniente_no_esta_en_la_obra",
          "interviniente_ambiguo",
          "interviniente_repetido",
          "numeracion_agotada",
          "colision_de_clave",
          "filas_afectadas_inesperadas",
          "error_de_escritura",
          "presupuesto_de_tiempo_agotado",
        ],
      },
      // Ensayo (dry-run) de la obra 9901: nada creado; los códigos de los
      // previstos son provisionales. El idempotente ya existía: su código es
      // el de verdad.
      dryRun: {
        obra: "9901",
        partes: [
          { referenciaExterna: "PVI-EJEMPLO-0201", unidad: UPV["9901-1"], estado: "previsto", cod: "RS99.09/0001", provisional: true, motivo: null },
          { referenciaExterna: "PVI-EJEMPLO-0202", unidad: UPV["9901-2"], estado: "previsto", cod: "RS99.09/0002", provisional: true, motivo: null },
          { referenciaExterna: "PVI-EJEMPLO-0203", unidad: UPV["9901-3"], estado: "previsto", cod: "RS99.09/0003", provisional: true, motivo: null },
          { referenciaExterna: "PVI-EJEMPLO-0204", unidad: UPV["9901-4"], estado: "idempotente", cod: "RS99.09/0041", provisional: false, motivo: null },
          {
            referenciaExterna: "PVI-EJEMPLO-0205",
            unidad: UPV["9901-5"],
            estado: "rechazado",
            cod: null,
            provisional: false,
            motivo: {
              codigo: "oficio_no_esta_en_la_obra",
              mensaje: "El oficio 0024 · Jardinería no está entre los oficios de la obra 9901 (ejemplo).",
            },
          },
        ],
      },
      // Volcado hecho de la obra 9902: ningún previsto; los cuatro resultados
      // reales. El primero es la fila BJ-0008 de la bandeja.
      hecho: {
        obra: "9902",
        partes: [
          { referenciaExterna: "PVI-EJEMPLO-0008", unidad: UPV["9902-4"], estado: "creado", cod: "RS99.09/0004", provisional: false, motivo: null },
          { referenciaExterna: "PVI-EJEMPLO-0301", unidad: UPV["9902-1"], estado: "creado", cod: "RS99.09/0005", provisional: false, motivo: null },
          { referenciaExterna: "PVI-EJEMPLO-0302", unidad: UPV["9902-2"], estado: "idempotente", cod: "RS99.09/0042", provisional: false, motivo: null },
          {
            referenciaExterna: "PVI-EJEMPLO-0303",
            unidad: UPV["9902-3"],
            estado: "rechazado",
            cod: null,
            provisional: false,
            motivo: {
              codigo: "interviniente_ambiguo",
              mensaje: "El oficio 0143 tiene dos proveedores en la obra 9902: hay que indicar cuál (ejemplo).",
            },
          },
          {
            referenciaExterna: "PVI-EJEMPLO-0304",
            unidad: UPV["9902-5"],
            estado: "no_procesado",
            cod: null,
            provisional: false,
            motivo: {
              codigo: "presupuesto_de_tiempo_agotado",
              mensaje: "No dio tiempo a intentarlo dentro del lote: se puede reenviar sin riesgo (ejemplo).",
            },
          },
        ],
      },
      pendientes: [
        "Pendiente: el volcado real espera a que sigrid-api despliegue el alta en lote",
        "Pendiente: qué es el tipo de reclamación 0003 y qué regla elige entre 0002 y 0003",
        "Pendiente: qué oficio lleva el parte si hay varios intervinientes y quién marca Causante",
        "Pendiente: en qué estado queda el parte recién creado (la captura de Posventa lo enseña en PTE; el alta en lote lo deja en el estado inicial de la serie, SAT)",
      ],
    },
  };

  /** `Object.freeze` profundo: la maqueta enseña sus datos, no los cambia. */
  function congelar(valor) {
    if (valor && typeof valor === "object" && !Object.isFrozen(valor)) {
      Object.freeze(valor);
      Object.keys(valor).forEach(function (clave) {
        congelar(valor[clave]);
      });
    }
    return valor;
  }

  congelar(MaquetaDatos);

  if (typeof window !== "undefined") {
    window.MaquetaDatos = MaquetaDatos;
  }
  if (typeof module !== "undefined" && module.exports) {
    module.exports = MaquetaDatos;
  }
})();
