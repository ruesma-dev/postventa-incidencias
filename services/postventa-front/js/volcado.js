// services/postventa-front/js/volcado.js
// F-040 R50-R62 · El panel de volcado de `bandeja.html`.
//
// `specs/F-040-volcado-sigrid/design.md` §3, contra el contrato
// **implementado** de F-059 (`GET /api/volcado`, `POST /api/volcado/ensayo`,
// `POST /api/volcado/volcar`) y de F-065 (`GET /api/revision/sigrid` y la
// guarda del ensayo).
//
// - **Lógica pura** (`tests_js/volcado.test.js`): cómo queda cada candidata
//   tras la sincronización (va / ya existe / choca), qué se ensaya, el troceo,
//   los cuerpos del ensayo y del volcado, cuándo se puede volcar, qué se dice
//   al parar y el resultado acumulado.
// - **El panel en el componente** (`conPanel`): su estado vive bajo UNA clave,
//   `volcado`, del único `x-data="appRevision()"` de la página (la guardia R70
//   de F-035 no admite un segundo `x-data`), y sus métodos se mezclan en él
//   para que `this` sea el proxy de Alpine.
//
// **«Registrar» (R60).** Sincroniza con Sigrid (una lectura, una vez), enseña
// el resultado y espera; solo con otro clic se ensaya, y solo con la
// confirmación (segundo clic y el número de partes, D-12) se vuelca. **Nada
// sale sin un clic (R56)**: cargar la obra solo lee `GET /api/volcado`.
//
// **Nada se reintenta solo (R53).** Ni el panel ni `js/api.js` (el ensayo, el
// volcado y la sincronización van `sinReintentos`). «Volver a registrar» es el
// único reintento, y lo pulsa una persona.
//
// **R55.** Ni el correo ni el `oid` van a `console` ni al almacenamiento del
// navegador; de la sincronización (que trae datos personales de clientes en la
// `ficha` de cada reclamación) el panel guarda en memoria solo lo que enseña,
// sin la `ficha`.
//
// El único `confirmado: true` del panel es el de `cuerpoDeVolcado` (R52).

(function () {
  "use strict";

  const RevisionModulo =
    (typeof window !== "undefined" && window.Revision) ||
    (typeof require !== "undefined" ? require("./revision.js") : null);

  /** El texto de un código de parte o de lote de §8.9: lo traduce F-038, no se copia (R54). */
  function textoMotivoVolcado(codigo) {
    return RevisionModulo.textoMotivoVolcado(codigo);
  }

  function propio(tabla, clave) {
    return typeof clave === "string" && Object.prototype.hasOwnProperty.call(tabla, clave);
  }

  /** El texto de `tabla` para `codigo`; uno desconocido, tal cual; sin código, nada (R54). */
  function textoDe(tabla, codigo) {
    if (codigo === null || codigo === undefined || codigo === "") {
      return "";
    }
    return propio(tabla, codigo) ? tabla[codigo] : String(codigo);
  }

  // --- Los textos (R54, R61) ------------------------------------------------------------------

  /** Los motivos de exclusión de un ensayo o un volcado: los de F-059 y los dos de la guarda de F-065. */
  const MOTIVOS_DE_EXCLUSION = [
    "no_es_de_la_bandeja",
    "de_otra_obra",
    "no_es_candidata",
    "ya_volcada",
    "huella_no_coincide",
    "fuera_del_ensayo",
    "revision_desactualizada",
    "duplicada_en_sigrid",
    "conflicto_sin_confirmar",
  ];

  const TEXTO_EXCLUSION = {
    no_es_de_la_bandeja: "No está en la bandeja",
    de_otra_obra: "Es de otra obra",
    no_es_candidata: "Ya no está aprobada ni en duda: no se puede volcar",
    ya_volcada: "Ya está volcada",
    huella_no_coincide: "Ha cambiado desde el ensayo",
    fuera_del_ensayo: "No estaba en el ensayo",
    revision_desactualizada: "Alguien la ha revisado otra vez desde el ensayo",
    duplicada_en_sigrid: "Ya existe en Sigrid",
    conflicto_sin_confirmar: "Choca con una reclamación abierta de Sigrid y no se ha incluido",
  };

  /** Las causas de un 409 `ensayo_no_valido` del volcado. */
  const CAUSAS_ENSAYO_NO_VALIDO = ["no_existe", "de_otra_obra", "de_otra_persona", "caducado"];

  const TEXTO_ENSAYO_NO_VALIDO = {
    no_existe: "el ensayo no existe",
    de_otra_obra: "el ensayo es de otra obra",
    de_otra_persona: "el ensayo lo hizo otra persona",
    caducado: "el ensayo ha caducado",
  };

  /** Los `codigo` de error de las tres rutas del volcado (F-059 y la guarda de F-065) y de la sincronización. */
  const CODIGOS_DE_ERROR = [
    "peticion_invalida",
    "ensayo_no_valido",
    "usuario_sigrid_no_mapeado",
    "usuario_sigrid_inexistente",
    "volcado_rechazado_por_la_pasarela",
    "bandeja_demasiado_grande",
    "ensayo_sin_respuesta",
    "volcado_sin_respuesta",
    "volcado_sin_traza",
    "volcado_deshabilitado",
    "configuracion_de_volcado_invalida",
    "configuracion_sigrid_incompleta",
    "base_de_datos_no_disponible",
    "sigrid_no_disponible",
    "reclamaciones_sin_verificar",
    "obra_ambigua",
  ];

  const TEXTO_ERROR = {
    peticion_invalida: "La petición no es válida: es un error de la página. Recarga la página.",
    ensayo_no_valido: "El ensayo de este trozo ya no vale. No se ha escrito nada: vuelve a registrar lo que queda.",
    usuario_sigrid_no_mapeado:
      "No hay usuario de Sigrid para tu sesión: hay que dar de alta la correspondencia con infra/07_alta_usuario_sigrid.ps1. No se ha escrito nada.",
    usuario_sigrid_inexistente:
      "Tu usuario de Sigrid no está bien dado de alta en el ERP: hay que revisar la correspondencia con infra/07_alta_usuario_sigrid.ps1. No se ha escrito nada.",
    volcado_rechazado_por_la_pasarela: "La pasarela de Sigrid ha rechazado el envío entero. No se ha escrito nada.",
    bandeja_demasiado_grande: "La obra pasa del tope de la bandeja: no se puede volcar desde aquí.",
    ensayo_sin_respuesta: "Sigrid no respondió a tiempo. No se ha escrito nada: repetir es inocuo.",
    volcado_sin_respuesta:
      "Sigrid no respondió a tiempo mientras se volcaba: lo que no consta queda en duda. Volver a registrar y volcar es seguro: no duplica.",
    volcado_sin_traza:
      "Sigrid respondió, pero no se pudo guardar su respuesta: lo de este trozo queda en duda. Avisa a sistemas.",
    volcado_deshabilitado: "La ventana del volcado está cerrada. No se ha escrito nada.",
    configuracion_de_volcado_invalida: "La configuración del volcado no es válida. Avisa a sistemas. No se ha escrito nada.",
    configuracion_sigrid_incompleta: "Falta configuración de Sigrid en el servicio. Avisa a sistemas. No se ha escrito nada.",
    base_de_datos_no_disponible: "La base de datos no está disponible. Avisa a sistemas. No se ha escrito nada.",
    sigrid_no_disponible:
      "Sigrid no responde: no se ha ensayado ni guardado nada. Vuelve a registrar más tarde.",
    reclamaciones_sin_verificar:
      "Sigrid ha devuelto demasiadas reclamaciones de la obra, o cortadas: no se puede saber qué hay. Avisa a sistemas.",
    obra_ambigua: "Hay más de una obra con ese código en Sigrid: lo tiene que mirar una persona.",
  };

  /** Los veredictos de F-065 (`Veredicto`), en su orden. */
  const VEREDICTOS = ["va", "se_enlaza", "ya_existe", "choca"];

  const TEXTO_VEREDICTO = {
    va: "Va",
    se_enlaza: "Se enlaza con su parte de Sigrid",
    ya_existe: "Ya existe en Sigrid",
    choca: "Choca con Sigrid",
  };

  /** El grupo del panel de cada veredicto (P-1: `se_enlaza` va dentro de «va»). */
  const GRUPO_DE_VEREDICTO = { va: "va", se_enlaza: "va", ya_existe: "ya_existe", choca: "choca" };

  /** Los criterios de una coincidencia de F-065 (`Criterio`). */
  const TEXTO_CRITERIO = {
    misma_unidad_oficio_ubicacion: "misma unidad, oficio y ubicación",
    misma_unidad_descripcion_parecida: "misma unidad y descripción parecida",
  };

  /** Los estados de un parte del ensayo (F-059 `EstadoEvento`) y del volcado. */
  const ETIQUETA_PARTE = {
    previsto: "Se crearía",
    idempotente: "Ya estaba creado",
    rechazado: "No se crea",
    no_procesado: "No se llegó a intentar",
    creado: "Creado",
    sin_respuesta: "En duda",
  };

  const SIN_DATO = "—";

  const TEXTO_SIN_RESPUESTA_SINCRONIZACION =
    "No se ha podido mirar Sigrid (sin conexión o tardó demasiado). Volver a registrar es inocuo: solo lee.";
  const TEXTO_SIN_RESPUESTA_ENSAYO =
    "No se ha podido hablar con el servicio (sin conexión o tardó demasiado) y no se ha reintentado. Repetir es inocuo: vuelve a registrar.";
  const TEXTO_SIN_RESPUESTA_VOLCADO =
    "No se sabe qué ha pasado con este trozo (sin conexión o tardó demasiado): sus partes quedan en duda hasta volver a leer. Volver a registrar y volcar lo aclara sin duplicar.";
  /**
   * C-B1-2 (review del Bloque 1) · lo que `design.md` §1 y §3.2 documentan como
   * «nada escrito» en un volcado: el trozo queda «sin volcar». Lista blanca:
   * cualquier otro fallo (corte, `volcado_sin_traza`, sin `codigo`, un código
   * desconocido o de otra ruta) deja el trozo entero «en duda», y
   * `volcado_sin_respuesta`, solo sus `en_duda`.
   */
  const NADA_ESCRITO_EN_EL_VOLCADO = [
    "peticion_invalida",
    "ensayo_no_valido",
    "usuario_sigrid_no_mapeado",
    "usuario_sigrid_inexistente",
    "volcado_rechazado_por_la_pasarela",
    "ensayo_sin_respuesta",
    "volcado_deshabilitado",
    "configuracion_de_volcado_invalida",
    "configuracion_sigrid_incompleta",
    "base_de_datos_no_disponible",
  ];
  const TEXTO_CADUCADO =
    "El ensayo de este trozo ha caducado antes de mandarlo: no se ha mandado. Hay que volver a registrar lo que queda.";
  const TEXTO_POSTERIOR_SINCRONIZACION = "Puedes volver a registrar más tarde: no se ha escrito nada.";

  function textoExclusion(codigo) {
    return textoDe(TEXTO_EXCLUSION, codigo);
  }

  function textoEnsayoNoValido(causa) {
    return textoDe(TEXTO_ENSAYO_NO_VALIDO, causa);
  }

  function textoError(codigo) {
    return textoDe(TEXTO_ERROR, codigo);
  }

  function etiquetaParte(estado) {
    return textoDe(ETIQUETA_PARTE, estado);
  }

  function textoVeredicto(veredicto) {
    return textoDe(TEXTO_VEREDICTO, veredicto);
  }

  /** «a», «a y b», «a, b y c». */
  function listaConY(partes) {
    if (partes.length <= 1) {
      return partes.join("");
    }
    return partes.slice(0, -1).join(", ") + " y " + partes[partes.length - 1];
  }

  /**
   * R61 · por qué choca una incidencia con la reclamación `reclamacion`:
   * `porque` es `{tipo: "anulada"}` (es su propio parte, anulado o en un estado
   * desconocido), `{tipo: "criterios", criterios, parecido}` (su `coincide`), o
   * `null` (más de 10 coincidencias: el porqué no viajó, R18 de F-065).
   */
  function textoPorque(porque, reclamacion) {
    const r = reclamacion || {};
    if (porque && porque.tipo === "anulada") {
      if (r.estado === "NPR") {
        return "Su parte " + r.cod + " está anulado en Sigrid";
      }
      return "Su parte " + r.cod + " está en un estado de Sigrid que el panel no conoce (" + r.estado + ")";
    }
    if (porque && porque.tipo === "criterios") {
      const criterios = (porque.criterios || []).map(function (c) {
        return textoDe(TEXTO_CRITERIO, c);
      });
      const parecido = typeof porque.parecido === "number" ? " (parecido " + porque.parecido + " %)" : "";
      return "Coincide en " + listaConY(criterios) + parecido;
    }
    return "Coincide con esta reclamación abierta (el detalle de la coincidencia no ha llegado)";
  }

  /** R62 · el texto de la casilla de una que choca (el segundo clic). */
  function textoInclusion(fila) {
    if (fila && fila.anulada) {
      const anulada = (fila.reclamaciones || []).find(function (r) {
        return r.porque && r.porque.tipo === "anulada";
      });
      return (
        "Incluirla: la enlaza con su parte anulado " + (anulada ? anulada.cod : "") +
        " de Sigrid y no crea otro"
      );
    }
    return "Incluirla en el ensayo aunque choque con lo que hay en Sigrid";
  }

  // --- La sincronización (R61, R62) ------------------------------------------------------------

  function nombreDeUnidad(catalogo, codigo) {
    const unidades = (catalogo && Array.isArray(catalogo.unidades) && catalogo.unidades) || [];
    const unidad = unidades.find(function (u) {
      return u && u.codigo === codigo;
    });
    return (unidad && unidad.nombre) || codigo;
  }

  /** La reclamación tal como la guarda el panel: sin `ficha` (datos personales, R33 de F-065). */
  function reclamacionSinFicha(r, catalogo) {
    return {
      cod: r.cod,
      estado: r.estado === undefined ? null : r.estado,
      unidad_codigo: r.unidad_codigo === undefined ? null : r.unidad_codigo,
      unidadNombre: r.unidad_codigo ? nombreDeUnidad(catalogo, r.unidad_codigo) : null,
      ubicacion: r.ubicacion === undefined ? null : r.ubicacion,
      oficio_codigo: r.oficio_codigo === undefined ? null : r.oficio_codigo,
      oficio_nombre: r.oficio_nombre === undefined ? null : r.oficio_nombre,
      descripcion: r.descripcion === undefined ? null : r.descripcion,
      incidencia_id: r.incidencia_id === undefined ? null : r.incidencia_id,
    };
  }

  /**
   * R61, R51 · con `respuesta` el 200 de `GET /api/revision/sigrid` y
   * `candidatas` los `incidencia_id` de `GET /api/volcado`: cada veredicto en
   * su grupo, en el orden de la respuesta, con sus reclamaciones (sin `ficha`)
   * y, si choca, el porqué; el recuento por unidad de cada grupo (de
   * `volcado.por_unidad`); y `sinSincronizar`, las candidatas que los
   * veredictos no nombran. Un veredicto desconocido va a «choca» sin casilla.
   */
  function agruparSincronizacion(candidatas, respuesta, catalogo) {
    const datos = respuesta || {};
    const bloque = datos.volcado || {};
    const veredictos = Array.isArray(bloque.veredictos) ? bloque.veredictos : [];
    const porCod = {};
    (Array.isArray(datos.reclamaciones) ? datos.reclamaciones : []).forEach(function (r) {
      if (r && typeof r.cod === "string") {
        porCod[r.cod] = r;
      }
    });
    const coincidencias = {};
    (Array.isArray(datos.hallazgos) ? datos.hallazgos : []).forEach(function (h) {
      if (h && h.tipo === "coincide" && h.incidencia_id && h.sigrid_cod) {
        coincidencias[h.incidencia_id + "|" + h.sigrid_cod] = h;
      }
    });

    const deLaBandeja = datos.incidencias && typeof datos.incidencias === "object" ? datos.incidencias : {};
    const grupos = { va: [], ya_existe: [], choca: [], orden: [] };
    const nombradas = {};
    veredictos.forEach(function (v) {
      const conocido = propio(GRUPO_DE_VEREDICTO, v.veredicto);
      const grupo = conocido ? GRUPO_DE_VEREDICTO[v.veredicto] : "choca";
      const cods = Array.isArray(v.sigrid_cods) ? v.sigrid_cods.slice() : [];
      const reclamaciones = cods.map(function (cod) {
        const original = porCod[cod] || { cod: cod };
        const r = reclamacionSinFicha(original, catalogo);
        r.porque = null;
        if (grupo === "choca") {
          if (original.incidencia_id && original.incidencia_id === v.incidencia_id) {
            r.porque = { tipo: "anulada" };
          } else {
            const h = coincidencias[v.incidencia_id + "|" + cod];
            r.porque = h ? { tipo: "criterios", criterios: (h.criterios || []).slice(), parecido: h.parecido } : null;
          }
        }
        r.porqueTexto = grupo === "choca" ? textoPorque(r.porque, r) : "";
        return r;
      });
      const seEnlaza = v.veredicto === "se_enlaza";
      const vigente = propio(deLaBandeja, v.incidencia_id) ? deLaBandeja[v.incidencia_id] || {} : {};
      const fila = {
        incidencia_id: v.incidencia_id,
        unidad_codigo: v.unidad_codigo,
        unidadNombre: nombreDeUnidad(catalogo, v.unidad_codigo),
        estado: v.estado,
        descripcion: vigente.descripcion || null,
        ubicacion: vigente.ubicacion || null,
        veredicto: v.veredicto,
        grupo: grupo,
        sigrid_cods: cods,
        reclamaciones: reclamaciones,
        seEnlaza: seEnlaza,
        enlazaCon: seEnlaza && cods.length ? cods[0] : null,
        marca: seEnlaza && cods.length ? "se enlaza con " + cods[0] : "",
        incluible: grupo === "choca" && conocido,
        anulada: reclamaciones.some(function (r) {
          return Boolean(r.porque && r.porque.tipo === "anulada");
        }),
      };
      fila.textoInclusion = fila.incluible ? textoInclusion(fila) : "";
      grupos[grupo].push(fila);
      grupos.orden.push(fila);
      nombradas[v.incidencia_id] = true;
    });

    const recuento = { va: [], ya_existe: [], choca: [] };
    const porUnidad = bloque.por_unidad && typeof bloque.por_unidad === "object" ? bloque.por_unidad : {};
    Object.keys(porUnidad).forEach(function (codigo) {
      const c = porUnidad[codigo] || {};
      const cuentas = {
        va: (c.va || 0) + (c.se_enlaza || 0),
        ya_existe: c.ya_existe || 0,
        choca: c.choca || 0,
      };
      Object.keys(cuentas).forEach(function (grupo) {
        if (cuentas[grupo] > 0) {
          recuento[grupo].push({ unidad_codigo: codigo, nombre: nombreDeUnidad(catalogo, codigo), n: cuentas[grupo] });
        }
      });
    });
    grupos.recuento = recuento;
    grupos.totales = { va: grupos.va.length, ya_existe: grupos.ya_existe.length, choca: grupos.choca.length };
    grupos.sinSincronizar = (candidatas || []).filter(function (id) {
      return !nombradas[id];
    });
    return grupos;
  }

  /** ¿Está marcada la casilla de `id`? Solo el booleano `true` (o estar en una lista). */
  function estaIncluida(incluidas, id) {
    if (Array.isArray(incluidas)) {
      return incluidas.indexOf(id) !== -1;
    }
    return Boolean(incluidas) && incluidas[id] === true;
  }

  /**
   * R62, R51 · lo que se ensaya: lo que va y lo que choca con su casilla (y se
   * puede incluir), en el orden de la sincronización. Nunca lo que ya existe
   * ni lo que la sincronización no nombra.
   */
  function paraEnsayar(grupos, incluidas) {
    if (!grupos || !Array.isArray(grupos.orden)) {
      return [];
    }
    return grupos.orden
      .filter(function (fila) {
        if (fila.grupo === "va") {
          return true;
        }
        return fila.grupo === "choca" && fila.incluible && estaIncluida(incluidas, fila.incidencia_id);
      })
      .map(function (fila) {
        return fila.incidencia_id;
      });
  }

  /** R62 · `conflictos_confirmados` de un trozo: las incluidas de ESE trozo, con todos sus códigos. */
  function confirmadosDelTrozo(ids, grupos, incluidas) {
    const choca = (grupos && grupos.choca) || [];
    return (ids || [])
      .map(function (id) {
        return choca.find(function (fila) {
          return fila.incidencia_id === id;
        });
      })
      .filter(function (fila) {
        return Boolean(fila) && fila.incluible && estaIncluida(incluidas, fila.incidencia_id);
      })
      .map(function (fila) {
        return { incidencia_id: fila.incidencia_id, sigrid_cods: fila.sigrid_cods.slice() };
      });
  }

  /** R60, R56 · sincronización en 200, sin ensayar aún, algo que ensayar y nada en vuelo. */
  function puedeEnsayar(estado) {
    return (
      Boolean(estado) &&
      Boolean(estado.grupos) &&
      estado.fase === "sincronizado" &&
      !estado.enVuelo &&
      paraEnsayar(estado.grupos, estado.incluidas).length > 0
    );
  }

  /**
   * R63 · la etiqueta de un tipo de reclamación, de `catalogo.listados` (F-072
   * R20); sin ella (de baja, desconocido o sin catálogo), el código tal cual,
   * nunca un nombre inventado. Sin código, nada.
   */
  function nombreDeTipo(catalogo, codigo) {
    if (codigo === null || codigo === undefined || codigo === "") {
      return "";
    }
    const listados = (catalogo && Array.isArray(catalogo.listados) && catalogo.listados) || [];
    const tipo = listados.find(function (l) {
      return l && l.codigo === codigo;
    });
    return (tipo && tipo.etiqueta) || String(codigo);
  }

  /** R64 [D-2] · cuántas por tipo, en el orden de aparición, con su etiqueta (o el código). */
  function recuentoPorTipo(filas, catalogo) {
    const cuentas = [];
    const indice = {};
    (filas || []).forEach(function (fila) {
      const codigo = fila.tipo_codigo;
      if (!propio(indice, codigo)) {
        indice[codigo] = cuentas.length;
        cuentas.push({ tipo_codigo: codigo, etiqueta: nombreDeTipo(catalogo, codigo), n: 0 });
      }
      cuentas[indice[codigo]].n += 1;
    });
    return cuentas;
  }

  /** R64 [D-2] · el recuento por tipo del resumen del ensayo: solo con más de un tipo. */
  function textoPorTipo(porTipo) {
    const tipos = porTipo || [];
    if (tipos.length < 2) {
      return "";
    }
    return "Por tipo: " + listaConY(tipos.map(function (t) {
      return t.n + " " + t.etiqueta;
    }));
  }

  /** R61, R51, R52 · cuántas por unidad, en el orden de aparición, con su nombre (o el código). */
  function recuentoPorUnidad(filas, catalogo) {
    const cuentas = [];
    const indice = {};
    (filas || []).forEach(function (fila) {
      const codigo = fila.unidad_codigo;
      if (!propio(indice, codigo)) {
        indice[codigo] = cuentas.length;
        cuentas.push({ unidad_codigo: codigo, nombre: nombreDeUnidad(catalogo, codigo), n: 0 });
      }
      cuentas[indice[codigo]].n += 1;
    });
    return cuentas;
  }

  /** R51 · grupos de `n` en orden, sin perder ni repetir. `n` ha de ser un entero positivo. */
  function trocear(ids, n) {
    if (typeof n !== "number" || !Number.isInteger(n) || n < 1) {
      throw new RangeError("partes_por_llamada no es un entero positivo: " + String(n));
    }
    const trozos = [];
    for (let i = 0; i < ids.length; i += n) {
      trozos.push(ids.slice(i, i + n));
    }
    return trozos;
  }

  /** R51, R62 · el cuerpo de `POST /api/volcado/ensayo`: el de F-059 y, solo si hay, `conflictos_confirmados`. */
  function cuerpoDeEnsayo(obra, ids, identidad, confirmados) {
    const cuerpo = {
      obra: obra,
      usuario_oid: identidad.usuarioOid,
      usuario_correo: identidad.correo,
      incidencias: ids.slice(),
    };
    if (Array.isArray(confirmados) && confirmados.length > 0) {
      cuerpo.conflictos_confirmados = confirmados;
    }
    return cuerpo;
  }

  /**
   * R62 · las excluidas de la guarda de F-065 (`duplicada_en_sigrid`,
   * `conflicto_sin_confirmar`) de los ensayos, marcando «cambió desde la
   * sincronización» las que iban en «va» y las incluidas cuya `sigrid_cod` no
   * estaba entre sus códigos.
   */
  function excluidasDeLaGuarda(respuestas, grupos) {
    const porId = {};
    ((grupos && grupos.orden) || []).forEach(function (fila) {
      porId[fila.incidencia_id] = fila;
    });
    const excluidas = [];
    (respuestas || []).forEach(function (datos) {
      ((datos && datos.excluidas) || []).forEach(function (e) {
        if (e.motivo !== "duplicada_en_sigrid" && e.motivo !== "conflicto_sin_confirmar") {
          return;
        }
        const fila = porId[e.incidencia_id];
        const cambio =
          Boolean(fila) &&
          (fila.grupo === "va" || (fila.grupo === "choca" && fila.sigrid_cods.indexOf(e.sigrid_cod) === -1));
        excluidas.push({
          incidencia_id: e.incidencia_id,
          motivo: e.motivo,
          sigrid_cod: e.sigrid_cod,
          texto: textoExclusion(e.motivo),
          cambio: cambio,
        });
      });
    });
    return {
      excluidas: excluidas,
      hayCambios: excluidas.some(function (e) {
        return e.cambio;
      }),
    };
  }

  // --- El volcado (R52, R53) -------------------------------------------------------------------

  function previstosDe(datos) {
    return ((datos && datos.partes) || []).filter(function (p) {
      return p.estado === "previsto";
    });
  }

  /**
   * R52 · el cuerpo de `POST /api/volcado/volcar` de un ensayo: **el único
   * `confirmado: true` del panel**, con solo sus `previsto`, cada uno con la
   * `revision_id` de su parte del ensayo. `null` si no hay ninguno (ese trozo
   * no se manda: el backend rechaza una lista vacía).
   */
  function cuerpoDeVolcado(ensayo, identidad) {
    const previstos = previstosDe(ensayo);
    if (!ensayo || !ensayo.ensayo_id || previstos.length === 0) {
      return null;
    }
    return {
      obra: ensayo.obra,
      ensayo_id: ensayo.ensayo_id,
      usuario_oid: identidad.usuarioOid,
      usuario_correo: identidad.correo,
      confirmado: true,
      incidencias: previstos.map(function (p) {
        return { incidencia_id: p.incidencia_id, revision_id: p.revision_id };
      }),
    };
  }

  function nombreDeOficio(catalogo, codigo) {
    const oficios = (catalogo && Array.isArray(catalogo.oficios) && catalogo.oficios) || [];
    const oficio = oficios.find(function (o) {
      return o && o.codigo === codigo;
    });
    return (oficio && oficio.nombre) || codigo;
  }

  function nombreDeProveedor(catalogo, oficio, proveedor) {
    const pares = (catalogo && Array.isArray(catalogo.pares) && catalogo.pares) || [];
    const par = pares.find(function (p) {
      return p && p.oficio_codigo === oficio && p.proveedor_codigo === proveedor;
    });
    return (par && par.proveedor_nombre) || proveedor;
  }

  function filaDelEnsayo(parte, catalogo) {
    const envio = parte.envio || null;
    const interviniente = (envio && Array.isArray(envio.intervinientes) && envio.intervinientes[0]) || null;
    return {
      incidencia_id: parte.incidencia_id,
      unidad_codigo: envio ? envio.unidad_postventa : null,
      unidad: envio ? nombreDeUnidad(catalogo, envio.unidad_postventa) : SIN_DATO,
      oficio: envio ? nombreDeOficio(catalogo, envio.oficio) : SIN_DATO,
      proveedor: interviniente ? nombreDeProveedor(catalogo, interviniente.oficio, interviniente.proveedor) : SIN_DATO,
      ubicacion: (envio && envio.ubicacion) || SIN_DATO,
      descripcion: (envio && envio.descripcion) || SIN_DATO,
      tipo_codigo: envio && envio.tipo ? envio.tipo : null,
      tipo: envio ? nombreDeTipo(catalogo, envio.tipo) : SIN_DATO,
      estado: parte.estado,
      etiqueta: etiquetaParte(parte.estado),
      motivo: textoMotivoVolcado(parte.motivo),
      sigrid_cod: parte.sigrid_cod || null,
    };
  }

  /** La caducidad (ISO) más temprana de una lista de ensayos con `ensayo_id`, o `null`. */
  function caducidadMasTemprana(respuestas) {
    let mejor = null;
    (respuestas || []).forEach(function (datos) {
      if (!datos || !datos.ensayo_id || !datos.caduca_at_utc) {
        return;
      }
      if (mejor === null || Date.parse(datos.caduca_at_utc) < Date.parse(mejor)) {
        mejor = datos.caduca_at_utc;
      }
    });
    return mejor;
  }

  /**
   * R51, R52, R53.5 · los ensayos de la obra, juntos: una tabla con los
   * nombres del catálogo, las excluidas con su texto, el resumen, N (los
   * `previsto`), el recuento por unidad de lo que se crearía, la caducidad más
   * temprana y si hubo algún `idempotente`.
   */
  function juntarEnsayos(respuestas, catalogo) {
    const filas = [];
    const excluidas = [];
    const resumen = { previstos: 0, idempotentes: 0, rechazados: 0, no_procesados: 0, excluidas: 0 };
    (respuestas || []).forEach(function (datos) {
      ((datos && datos.partes) || []).forEach(function (parte) {
        filas.push(filaDelEnsayo(parte, catalogo));
      });
      ((datos && datos.excluidas) || []).forEach(function (e) {
        excluidas.push({ incidencia_id: e.incidencia_id, motivo: e.motivo, sigrid_cod: e.sigrid_cod || null, texto: textoExclusion(e.motivo) });
      });
    });
    filas.forEach(function (f) {
      if (f.estado === "previsto") resumen.previstos += 1;
      if (f.estado === "idempotente") resumen.idempotentes += 1;
      if (f.estado === "rechazado") resumen.rechazados += 1;
      if (f.estado === "no_procesado") resumen.no_procesados += 1;
    });
    resumen.excluidas = excluidas.length;
    const previstas = filas.filter(function (f) {
      return f.estado === "previsto";
    });
    return {
      filas: filas,
      excluidas: excluidas,
      resumen: resumen,
      n: previstas.length,
      porUnidad: recuentoPorUnidad(previstas, catalogo),
      porTipo: recuentoPorTipo(previstas, catalogo),
      caduca: caducidadMasTemprana(respuestas),
      hayIdempotente: resumen.idempotentes > 0,
    };
  }

  function instante(ahora) {
    return ahora instanceof Date ? ahora.getTime() : ahora;
  }

  /** R53.1 · el ensayo de un trozo ya no vale. Sin caducidad legible, tampoco. */
  function caducado(ensayo, ahora) {
    const limite = Date.parse((ensayo && ensayo.caduca_at_utc) || "");
    if (Number.isNaN(limite)) {
      return true;
    }
    return instante(ahora) >= limite;
  }

  /** R52 · la cuenta atrás hasta `caduca` («m:ss»), «caducado» o nada sin caducidad. */
  function cuentaAtras(caduca, ahora) {
    if (!caduca) {
      return "";
    }
    const quedan = Date.parse(caduca) - instante(ahora);
    if (!(quedan > 0)) {
      return "caducado";
    }
    const segundos = Math.floor(quedan / 1000);
    return Math.floor(segundos / 60) + ":" + String(segundos % 60).padStart(2, "0");
  }

  /** R52, R56 · ≥ 1 previsto, todos los ensayos en 200, sin caducar y sin petición en vuelo. */
  function puedeVolcar(estado, ahora) {
    if (!estado || estado.enVuelo) {
      return false;
    }
    const ensayos = estado.ensayos || [];
    if (ensayos.length === 0 || !ensayos.every(function (e) { return e.ok; })) {
      return false;
    }
    const datos = ensayos.map(function (e) {
      return e.datos;
    });
    const conPrevistos = datos.filter(function (d) {
      return previstosDe(d).length > 0;
    });
    if (conPrevistos.length === 0) {
      return false;
    }
    return !caducado({ caduca_at_utc: caducidadMasTemprana(conPrevistos) }, ahora);
  }

  /** R52, D-12 · el número exacto de partes, tecleado (sin espacios a los lados). */
  function confirmacionValida(tecleado, n) {
    if (tecleado === null || tecleado === undefined) {
      return false;
    }
    const texto = String(tecleado).trim();
    return /^[1-9]\d*$/.test(texto) && Number(texto) === n;
  }

  /**
   * R52, C-3 · el texto de la confirmación, con el recuento por unidad; R64
   * [D-2] · y por tipo, solo cuando hay más de uno (con uno, no cambia).
   */
  function textoConfirmacion(n, porUnidad, obra, porTipo) {
    const verbo = n === 1 ? "Se va a crear 1 parte" : "Se van a crear " + n + " partes";
    const unidades = (porUnidad || []).map(function (u) {
      return u.n + " de " + u.nombre;
    });
    const tipos = porTipo || [];
    const porTipos =
      tipos.length > 1
        ? "; por tipo, " + listaConY(tipos.map(function (t) {
            return t.n + " " + t.etiqueta;
          }))
        : "";
    return (
      verbo + " en el ERP de producción de la obra " + obra + ": " + listaConY(unidades) + porTipos +
      ". Escribe " + n + " para confirmar."
    );
  }

  /** §3.2 · lo que dice el panel cuando `error` para la `fase` (sincronizacion, ensayo, volcado). */
  function textoDeParada(fase, error) {
    const e = error || {};
    const detalle = (e.detalle && typeof e.detalle === "object" && e.detalle) || {};
    if (e.http === null || e.http === undefined) {
      if (fase === "volcado") return TEXTO_SIN_RESPUESTA_VOLCADO;
      if (fase === "ensayo") return TEXTO_SIN_RESPUESTA_ENSAYO;
      return TEXTO_SIN_RESPUESTA_SINCRONIZACION;
    }
    const codigo = e.codigo;
    if (
      fase === "volcado" &&
      NADA_ESCRITO_EN_EL_VOLCADO.indexOf(codigo) === -1 &&
      codigo !== "volcado_sin_respuesta" &&
      codigo !== "volcado_sin_traza"
    ) {
      // C-B1-2 · sin un código de «nada escrito», el panel no sabe si Sigrid escribió.
      return (
        "No se sabe qué ha pasado con este trozo (el servicio respondió " + e.http +
        (codigo ? ", " + codigo : "") + "): sus partes quedan en duda hasta volver a leer. " +
        "Volver a registrar y volcar lo aclara sin duplicar."
      );
    }
    if (!codigo) {
      if (fase === "sincronizacion" && e.http === 503) {
        return (e.mensajeServicio ? e.mensajeServicio + " " : "Sigrid o la base no están disponibles. ") + TEXTO_POSTERIOR_SINCRONIZACION;
      }
      if (fase === "sincronizacion") {
        return "No se ha podido mirar Sigrid (el servicio respondió " + e.http + "). Volver a registrar es inocuo: solo lee.";
      }
      return "El servicio respondió " + e.http + (e.mensajeServicio ? ": " + e.mensajeServicio : ".");
    }
    if (!propio(TEXTO_ERROR, codigo)) {
      return "El servicio respondió " + e.http + " (" + codigo + ")" + (e.mensajeServicio ? ": " + e.mensajeServicio : ".");
    }
    let texto = TEXTO_ERROR[codigo];
    if (codigo === "bandeja_demasiado_grande" && typeof detalle.total === "number") {
      texto = "La obra pasa del tope de la bandeja (" + detalle.total + " incidencias): no se puede volcar desde aquí.";
    } else if (codigo === "reclamaciones_sin_verificar" && typeof detalle.filas === "number") {
      texto =
        "Sigrid ha devuelto demasiadas reclamaciones de la obra (" + detalle.filas +
        " filas), o cortadas: no se puede saber qué hay. Avisa a sistemas.";
    } else if (codigo === "ensayo_no_valido" && detalle.motivo) {
      texto = "No se ha escrito nada: " + textoEnsayoNoValido(detalle.motivo) + ". Hay que volver a registrar lo que queda.";
    } else if (codigo === "volcado_rechazado_por_la_pasarela" && detalle.codigo_pasarela) {
      texto = "La pasarela de Sigrid ha rechazado el envío entero: " + textoMotivoVolcado(detalle.codigo_pasarela) + ". No se ha escrito nada.";
    } else if ((codigo === "usuario_sigrid_no_mapeado" || codigo === "usuario_sigrid_inexistente") && e.mensajeServicio) {
      texto = texto + " (El servicio dice: " + e.mensajeServicio + ".)";
    } else if (codigo === "ensayo_sin_respuesta" && fase === "volcado") {
      texto = "Sigrid no respondió a tiempo antes de escribir: no se ha escrito nada. Volver a registrar es inocuo.";
    }
    return texto;
  }

  /**
   * R51, R53 · seguir o parar tras una respuesta (`{fase, datos}` o `{fase,
   * error}`): para ante cualquier error (también sin respuesta del servicio) y
   * ante un volcado 200 con algún `sin_respuesta`.
   */
  function siguientePaso(resultado) {
    const r = resultado || {};
    if (r.error) {
      return { seguir: false, mensaje: textoDeParada(r.fase, r.error) };
    }
    const resumen = (r.datos && r.datos.resumen) || {};
    if (r.fase === "volcado" && resumen.sin_respuesta > 0) {
      return {
        seguir: false,
        mensaje:
          "Sigrid no confirmó " + resumen.sin_respuesta + " parte(s) de este trozo: quedan en duda. Volver a registrar y volcar lo aclara: no duplica.",
      };
    }
    return { seguir: true, mensaje: "" };
  }

  /**
   * R53.4 · el resultado acumulado de los volcados: creados (con su RS), ya
   * creados, rechazados y no procesados con su motivo, excluidas, en duda (los
   * `sin_respuesta`; del `fallo`, los de §3.2), sin volcar y los avisos.
   * `fallo` es `{error, ids}` (los del trozo que paró) o `null`; `sinMandar`,
   * los de los trozos que ya no se mandaron.
   */
  function juntarVolcados(respuestas, fallo, sinMandar) {
    const r = { creados: [], yaCreados: [], rechazados: [], noProcesados: [], excluidas: [], enDuda: [], sinMandar: [], avisos: [] };
    (respuestas || []).forEach(function (datos) {
      ((datos && datos.partes) || []).forEach(function (p) {
        if (p.estado === "creado") r.creados.push({ incidencia_id: p.incidencia_id, sigrid_cod: p.sigrid_cod });
        else if (p.estado === "idempotente") r.yaCreados.push({ incidencia_id: p.incidencia_id, sigrid_cod: p.sigrid_cod });
        else if (p.estado === "rechazado") r.rechazados.push({ incidencia_id: p.incidencia_id, motivo: p.motivo, texto: textoMotivoVolcado(p.motivo) });
        else if (p.estado === "no_procesado") r.noProcesados.push({ incidencia_id: p.incidencia_id, motivo: p.motivo, texto: textoMotivoVolcado(p.motivo) });
        else if (p.estado === "sin_respuesta") r.enDuda.push(p.incidencia_id);
      });
      ((datos && datos.excluidas) || []).forEach(function (e) {
        r.excluidas.push({ incidencia_id: e.incidencia_id, motivo: e.motivo, texto: textoExclusion(e.motivo) });
      });
      ((datos && datos.avisos) || []).forEach(function (a) {
        r.avisos.push(a);
      });
    });
    if (fallo) {
      const ids = fallo.ids || [];
      const error = fallo.error || {};
      // C-B1-2 · lista blanca: solo lo documentado como «nada escrito» queda
      // «sin volcar»; `volcado_sin_respuesta`, sus `en_duda`; lo demás (corte,
      // `volcado_sin_traza`, sin código, código desconocido), el trozo entero en duda.
      const sinRespuesta = error.http === null || error.http === undefined;
      let enDuda = [];
      if (!sinRespuesta && error.codigo === "volcado_sin_respuesta") {
        const lista = (error.detalle && Array.isArray(error.detalle.en_duda) && error.detalle.en_duda) || [];
        enDuda = ids.filter(function (id) {
          return lista.indexOf(id) !== -1;
        });
      } else if (sinRespuesta || NADA_ESCRITO_EN_EL_VOLCADO.indexOf(error.codigo) === -1) {
        enDuda = ids.slice();
      }
      enDuda.forEach(function (id) {
        r.enDuda.push(id);
      });
      ids.forEach(function (id) {
        if (enDuda.indexOf(id) === -1) {
          r.sinMandar.push(id);
        }
      });
    }
    (sinMandar || []).forEach(function (id) {
      r.sinMandar.push(id);
    });
    r.resumen = {
      creados: r.creados.length,
      idempotentes: r.yaCreados.length,
      rechazados: r.rechazados.length,
      no_procesados: r.noProcesados.length,
      en_duda: r.enDuda.length,
      excluidas: r.excluidas.length,
      sin_mandar: r.sinMandar.length,
    };
    return r;
  }

  /** R59 · el aviso de que lo creado queda en SAT y Posventa lo pasa a PTE a mano. */
  function avisoDePte(resumen) {
    const creados = (resumen && resumen.creados) || 0;
    if (!(creados > 0)) {
      return "";
    }
    const quien = creados === 1 ? "El parte creado queda" : "Los " + creados + " partes creados quedan";
    return (
      quien + " en SAT en Sigrid: Posventa tiene que pasarlos a PTE a mano, que es cuando Sigrid avisa al industrial."
    );
  }

  /** R55 · la guarda de salida: una serie de ensayos o de volcados en marcha. Ilegible, no pregunta. */
  function hayVolcadoEnMarcha(estado) {
    try {
      const fase = estado && estado.volcado && estado.volcado.fase;
      return fase === "ensayando" || fase === "volcando";
    } catch (error) {
      return false;
    }
  }

  /**
   * C-B1-1 · una petición del panel en vuelo o una serie en marcha
   * (sincronizando, ensayando, volcando). Más ancho que `hayVolcadoEnMarcha`,
   * que es la guarda de salida (R55: solo ensayos y volcados).
   */
  function volcadoOcupado(estado) {
    const v = estado && estado.volcado;
    if (!v) {
      return false;
    }
    return Boolean(v.enVuelo) || v.fase === "sincronizando" || hayVolcadoEnMarcha(estado);
  }

  /** R50 · los recuentos de `GET /api/volcado`. */
  function resumenDelPanel(datos) {
    const d = datos || {};
    const resumen = d.resumen || {};
    const n = Array.isArray(d.candidatas) ? d.candidatas.length : 0;
    const partes = d.partes_por_llamada;
    const trozos = n > 0 && partes > 0 ? Math.ceil(n / partes) : 0;
    let texto = "Ninguna candidata";
    if (n > 0) {
      texto =
        (n === 1 ? "1 candidata" : n + " candidatas") + ", en " +
        (trozos === 1 ? "1 trozo" : trozos + " trozos") + " de " + partes;
    }
    return {
      aprobadas: resumen.aprobadas || 0,
      enDuda: resumen.en_duda || 0,
      volcadas: resumen.volcadas || 0,
      candidatas: n,
      partesPorLlamada: partes,
      trozos: trozos,
      texto: texto,
    };
  }

  // --- El panel en el componente (design.md §3.3) -------------------------------------------------

  function estadoInicial(obra) {
    return {
      obra: obra || "",
      cargando: false,
      error: "",
      panel: null,
      candidatas: [],
      fase: "inicio",
      enVuelo: false,
      grupos: null,
      incluidas: {},
      ensayos: [],
      vistaEnsayo: null,
      guarda: null,
      progreso: { k: 0, m: 0 },
      parada: "",
      confirmando: false,
      tecleado: "",
      resultado: null,
      aviso: "",
      ahora: 0,
    };
  }

  function relojDelNavegador() {
    return {
      ahora: function () {
        return Date.now();
      },
      cadaSegundo: function (funcion) {
        const id = setInterval(funcion, 1000);
        return function () {
          clearInterval(id);
        };
      },
    };
  }

  /**
   * Mezcla el panel en el componente `app` (`appRevision`): el estado bajo
   * `volcado` y los métodos, para que `this` sea el proxy de Alpine y alcance
   * `obraCargada`, `usuario`, `catalogo`, `obra` y `cargar()`. Nada guarda en
   * un cierre el objeto crudo; el reloj de la cuenta atrás y su cancelación,
   * que no son estado que se pinte, sí (`dependencias.reloj`, inyectable).
   */
  function conPanel(app, dependencias) {
    const api = dependencias.api;
    const reloj = dependencias.reloj || relojDelNavegador();
    let pararReloj = null;

    function detenerReloj() {
      if (pararReloj) {
        pararReloj();
        pararReloj = null;
      }
    }

    const metodos = {
      volcado: estadoInicial(""),

      /** R50 · tras una carga buena de la bandeja: `GET /api/volcado` (solo lee). Otra obra, el panel a cero. */
      async volcadoAlCargar() {
        const obra = this.obraCargada;
        if (volcadoOcupado(this)) {
          // C-B1-1 · con una serie en marcha el panel no se toca: ni se reinicia
          // ni se relee. La serie sigue, la guarda de salida sigue preguntando
          // y su resultado se enseña al acabar. (El HTML ya no deja cargar.)
          return;
        }
        if (obra !== this.volcado.obra) {
          detenerReloj();
          this.volcado = estadoInicial(obra);
        }
        await this.volcadoLeerPanel();
      },

      async volcadoLeerPanel() {
        const estado = this.volcado;
        estado.cargando = true;
        estado.error = "";
        try {
          const datos = await api.volcadoPanel(estado.obra);
          estado.panel = resumenDelPanel(datos);
          estado.candidatas = (datos.candidatas || []).map(function (c) {
            return c.incidencia_id;
          });
        } catch (error) {
          estado.panel = null;
          estado.candidatas = [];
          estado.error = RevisionModulo.queHacerConElError(error, false).mensaje;
        } finally {
          estado.cargando = false;
        }
      },

      /** R53.5 · el panel y la primera página de la bandeja, otra vez (si la obra del campo es la del panel). */
      async volcadoReleer() {
        const estado = this.volcado;
        if (String(this.obra || "").trim() === estado.obra) {
          await this.cargar();
        } else {
          await this.volcadoLeerPanel();
        }
      },

      volcadoPuedeRegistrar() {
        const v = this.volcado;
        return Boolean(v.obra && v.panel) && !v.enVuelo && !v.cargando;
      },

      volcadoTextoRegistrar() {
        return this.volcado.fase === "inicio" ? "Registrar" : "Volver a registrar";
      },

      /** R60, R53.6 · «Registrar» (y «Volver a registrar»): la sincronización, una vez, y esperar. */
      async registrar() {
        if (!this.volcadoPuedeRegistrar()) {
          return;
        }
        detenerReloj();
        const estado = this.volcado;
        estado.grupos = null;
        estado.incluidas = {};
        estado.ensayos = [];
        estado.vistaEnsayo = null;
        estado.guarda = null;
        estado.resultado = null;
        estado.aviso = "";
        estado.parada = "";
        estado.confirmando = false;
        estado.tecleado = "";
        estado.progreso = { k: 0, m: 0 };
        estado.fase = "sincronizando";
        estado.enVuelo = true;
        try {
          const respuesta = await api.revisionSigrid(estado.obra);
          estado.grupos = agruparSincronizacion(estado.candidatas, respuesta, this.catalogo);
          estado.fase = "sincronizado";
        } catch (error) {
          estado.parada = siguientePaso({ fase: "sincronizacion", error: error }).mensaje;
          estado.fase = "parado";
        } finally {
          estado.enVuelo = false;
        }
      },

      volcadoPuedeEnsayar() {
        return puedeEnsayar(this.volcado) && RevisionModulo.puedeActuar(this.usuario, false);
      },

      /** R51, R62 · los ensayos, de uno en uno; la serie para en el primer fallo. */
      async ensayar() {
        if (!this.volcadoPuedeEnsayar()) {
          return;
        }
        const estado = this.volcado;
        const identidad = { usuarioOid: this.usuario.usuarioOid, correo: this.usuario.correo };
        const trozos = trocear(paraEnsayar(estado.grupos, estado.incluidas), estado.panel.partesPorLlamada);
        estado.fase = "ensayando";
        estado.enVuelo = true;
        estado.ensayos = [];
        estado.parada = "";
        estado.progreso = { k: 0, m: trozos.length };
        let paro = false;
        for (let i = 0; i < trozos.length; i += 1) {
          estado.progreso = { k: i + 1, m: trozos.length };
          const cuerpo = cuerpoDeEnsayo(estado.obra, trozos[i], identidad, confirmadosDelTrozo(trozos[i], estado.grupos, estado.incluidas));
          try {
            const datos = await api.volcadoEnsayo(cuerpo);
            estado.ensayos.push({ ok: true, ids: trozos[i].slice(), datos: datos });
          } catch (error) {
            estado.ensayos.push({ ok: false, ids: trozos[i].slice(), error: error });
            estado.parada = siguientePaso({ fase: "ensayo", error: error }).mensaje;
            paro = true;
            break;
          }
        }
        const buenos = estado.ensayos
          .filter(function (e) {
            return e.ok;
          })
          .map(function (e) {
            return e.datos;
          });
        estado.vistaEnsayo = juntarEnsayos(buenos, this.catalogo);
        estado.guarda = excluidasDeLaGuarda(buenos, estado.grupos);
        estado.enVuelo = false;
        estado.fase = paro ? "parado" : "ensayado";
        if (!paro) {
          this.volcadoArrancarReloj();
        }
        if (estado.vistaEnsayo.hayIdempotente) {
          await this.volcadoReleer();
        }
      },

      volcadoArrancarReloj() {
        detenerReloj();
        const estado = this.volcado;
        estado.ahora = reloj.ahora();
        pararReloj = reloj.cadaSegundo(function () {
          estado.ahora = reloj.ahora();
        });
      },

      volcadoCuentaAtras() {
        const vista = this.volcado.vistaEnsayo;
        return cuentaAtras(vista && vista.caduca, this.volcado.ahora);
      },

      volcadoPuedeVolcar() {
        return puedeVolcar(this.volcado, reloj.ahora()) && RevisionModulo.puedeActuar(this.usuario, false);
      },

      volcadoConfirmacion() {
        const vista = this.volcado.vistaEnsayo;
        return vista ? textoConfirmacion(vista.n, vista.porUnidad, this.volcado.obra, vista.porTipo) : "";
      },

      /** R64 · el recuento por tipo del resumen del ensayo (vacío con un solo tipo). */
      volcadoPorTipo() {
        const vista = this.volcado.vistaEnsayo;
        return vista ? textoPorTipo(vista.porTipo) : "";
      },

      volcadoConfirmacionValida() {
        const vista = this.volcado.vistaEnsayo;
        return Boolean(vista) && confirmacionValida(this.volcado.tecleado, vista.n);
      },

      /** R52 · el primer clic de «Volcar N partes»: solo abre la confirmación. */
      pedirVolcado() {
        if (!this.volcadoPuedeVolcar()) {
          return;
        }
        this.volcado.confirmando = true;
        this.volcado.tecleado = "";
      },

      cancelarVolcado() {
        this.volcado.confirmando = false;
        this.volcado.tecleado = "";
      },

      /** R52, R53 · el segundo clic: un volcado por ensayo con previstos, de uno en uno; para ante cualquier cosa. */
      async volcar() {
        const estado = this.volcado;
        if (!estado.confirmando || !this.volcadoConfirmacionValida() || !this.volcadoPuedeVolcar()) {
          return;
        }
        const identidad = { usuarioOid: this.usuario.usuarioOid, correo: this.usuario.correo };
        const pendientes = estado.ensayos
          .map(function (e) {
            return { datos: e.datos, cuerpo: cuerpoDeVolcado(e.datos, identidad) };
          })
          .filter(function (p) {
            return p.cuerpo !== null;
          });
        const idsDe = function (p) {
          return p.cuerpo.incidencias.map(function (i) {
            return i.incidencia_id;
          });
        };
        estado.confirmando = false;
        estado.tecleado = "";
        estado.fase = "volcando";
        estado.enVuelo = true;
        estado.parada = "";
        estado.progreso = { k: 0, m: pendientes.length };
        const respuestas = [];
        let fallo = null;
        let sinMandar = [];
        for (let i = 0; i < pendientes.length; i += 1) {
          const resto = function (desde) {
            return pendientes.slice(desde).reduce(function (lista, p) {
              return lista.concat(idsDe(p));
            }, []);
          };
          if (caducado(pendientes[i].datos, reloj.ahora())) {
            estado.parada = TEXTO_CADUCADO;
            sinMandar = resto(i);
            break;
          }
          estado.progreso = { k: i + 1, m: pendientes.length };
          try {
            const datos = await api.volcadoVolcar(pendientes[i].cuerpo);
            respuestas.push(datos);
            const paso = siguientePaso({ fase: "volcado", datos: datos });
            if (!paso.seguir) {
              estado.parada = paso.mensaje;
              sinMandar = resto(i + 1);
              break;
            }
          } catch (error) {
            fallo = { error: error, ids: idsDe(pendientes[i]) };
            estado.parada = siguientePaso({ fase: "volcado", error: error }).mensaje;
            sinMandar = resto(i + 1);
            break;
          }
        }
        detenerReloj();
        estado.resultado = juntarVolcados(respuestas, fallo, sinMandar);
        estado.aviso = avisoDePte(estado.resultado.resumen);
        estado.ensayos = [];
        estado.enVuelo = false;
        estado.fase = estado.parada ? "parado" : "terminado";
        await this.volcadoReleer();
      },

      hayVolcadoEnMarcha() {
        return hayVolcadoEnMarcha(this);
      },

      /** C-B1-1 · algo del panel en vuelo: la bandeja no deja cambiar de obra ni de filtro. */
      volcadoOcupado() {
        return volcadoOcupado(this);
      },

      /** Cómo nombrar una incidencia en el resultado: su descripción del ensayo, o su identificador. */
      volcadoNombre(incidenciaId) {
        const vista = this.volcado.vistaEnsayo;
        const fila = vista
          ? vista.filas.find(function (f) {
              return f.incidencia_id === incidenciaId;
            })
          : null;
        return fila && fila.descripcion !== SIN_DATO ? fila.unidad + " · " + fila.descripcion : String(incidenciaId);
      },
    };

    Object.keys(metodos).forEach(function (clave) {
      app[clave] = metodos[clave];
    });
    return app;
  }

  const Volcado = {
    MOTIVOS_DE_EXCLUSION: MOTIVOS_DE_EXCLUSION,
    CAUSAS_ENSAYO_NO_VALIDO: CAUSAS_ENSAYO_NO_VALIDO,
    CODIGOS_DE_ERROR: CODIGOS_DE_ERROR,
    VEREDICTOS: VEREDICTOS,
    agruparSincronizacion: agruparSincronizacion,
    paraEnsayar: paraEnsayar,
    confirmadosDelTrozo: confirmadosDelTrozo,
    puedeEnsayar: puedeEnsayar,
    recuentoPorUnidad: recuentoPorUnidad,
    recuentoPorTipo: recuentoPorTipo,
    textoPorTipo: textoPorTipo,
    trocear: trocear,
    cuerpoDeEnsayo: cuerpoDeEnsayo,
    excluidasDeLaGuarda: excluidasDeLaGuarda,
    cuerpoDeVolcado: cuerpoDeVolcado,
    juntarEnsayos: juntarEnsayos,
    puedeVolcar: puedeVolcar,
    confirmacionValida: confirmacionValida,
    textoConfirmacion: textoConfirmacion,
    caducado: caducado,
    cuentaAtras: cuentaAtras,
    siguientePaso: siguientePaso,
    textoDeParada: textoDeParada,
    juntarVolcados: juntarVolcados,
    avisoDePte: avisoDePte,
    textoExclusion: textoExclusion,
    textoEnsayoNoValido: textoEnsayoNoValido,
    textoError: textoError,
    etiquetaParte: etiquetaParte,
    textoVeredicto: textoVeredicto,
    textoPorque: textoPorque,
    textoInclusion: textoInclusion,
    hayVolcadoEnMarcha: hayVolcadoEnMarcha,
    volcadoOcupado: volcadoOcupado,
    NADA_ESCRITO_EN_EL_VOLCADO: NADA_ESCRITO_EN_EL_VOLCADO,
    resumenDelPanel: resumenDelPanel,
    estadoInicial: estadoInicial,
    conPanel: conPanel,
  };

  if (typeof window !== "undefined") {
    window.Volcado = Volcado;
  }
  if (typeof module !== "undefined" && module.exports) {
    module.exports = Volcado;
  }
})();
