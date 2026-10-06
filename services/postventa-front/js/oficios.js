// services/postventa-front/js/oficios.js
// F-036 R80-R82, R86, R88, R89, R98 · Oficios repetidos en Sigrid (`oficios.html`).
// F-035 R75 · «Decididos como distintos»: la clave `distintos` de
// `presentarPropuestas` (bloque 13). Ni una llamada nueva: su botón usa `decidir()`.
//
// `design.md` §15.6 con la quinta enmienda: un solo catálogo, `oficio`. Nada de
// proveedores (F-050) ni de actividades (F-039).
//
// - **Lógica pura** (`tests_js/oficios.test.js`): motivos legibles, las
//   propuestas, los grupos vigentes y los avisos listos para pintar, los pares
//   de un grupo, el cuerpo de una decisión y el JSON de grupos vigentes de R98.
// - **El componente Alpine** `appOficios`, construido por
//   `crearAppOficios({api, guardar})`.
//
// **Nada se decide sin pulsar (R80, R89).** Cargar las propuestas solo lee; la
// única salida hacia `POST /api/catalogos/decisiones` es `decidir()`, que el
// HTML solo llama desde un `@click`, y el único sitio donde se escribe
// `confirmado: true` es `cuerpoDeDecision`. Mientras una decisión se guarda no
// sale otra: un doble clic no produce dos.
//
// La forma de las respuestas es la de los handlers (`progress/impl_F-036.md`,
// B6-18): `{obra, oficio: {oficios: [{codigo, nombre, grupo}], grupos:
// [{etiqueta, codigos}], propuestas: [{codigos, por_pares, motivos, pares}],
// avisos: [{codigos}]}}`. La tabla de §8 todavía escribe una clave
// `proveedor`, que el backend ya no manda. `oficio.distintos: [{codigo_a,
// codigo_b}]` (R75) llegará con F-053; hasta entonces no viene.
//
// Usa `window.Importacion` (`js/importacion.js`) para guardar ficheros y para
// el texto de los errores: `oficios.html` lo carga antes que este.

(function () {
  "use strict";

  const ImportacionModulo =
    (typeof window !== "undefined" && window.Importacion) ||
    (typeof require !== "undefined" ? require("./importacion.js") : null);

  /** El único catálogo de F-036 (quinta enmienda). */
  const CATALOGO = "oficio";

  /** Un código del grupo sin nombre en esta obra (R84: el grupo vale para todas). */
  const SIN_NOMBRE = "(sin nombre en esta obra)";

  /** Los motivos de `design.md` §15.6, para alguien sin formación. */
  const TEXTO_MOTIVO = {
    mismo_nombre: "mismo nombre salvo mayúsculas, tildes o puntuación",
    plural: "plural",
    errata: "posible errata",
    incluido: "uno contiene al otro",
  };

  const DECISIONES = ["mismo", "distinto"];

  function motivosLegibles(motivos) {
    return (motivos || []).map(function (motivo) {
      return TEXTO_MOTIVO[motivo] || String(motivo);
    });
  }

  /** Los códigos ordenados, sin repetir. */
  function ordenados(codigos) {
    return Array.from(new Set(codigos || [])).sort();
  }

  /** Todos los pares de un grupo, en orden: los que «Separar» puede elegir. */
  function paresDe(codigos) {
    const lista = ordenados(codigos);
    const pares = [];
    for (let i = 0; i < lista.length; i += 1) {
      for (let j = i + 1; j < lista.length; j += 1) {
        pares.push([lista[i], lista[j]]);
      }
    }
    return pares;
  }

  /** `{codigo: nombre}` de los oficios de la obra que tienen nombre. */
  function nombresPorCodigo(oficios) {
    const nombres = {};
    (oficios || []).forEach(function (oficio) {
      if (oficio.nombre) {
        nombres[oficio.codigo] = oficio.nombre;
      }
    });
    return nombres;
  }

  function miembros(codigos, nombres) {
    return ordenados(codigos).map(function (codigo) {
      return { codigo: codigo, nombre: nombres[codigo] || SIN_NOMBRE };
    });
  }

  function par(codigoA, codigoB, motivos, nombres) {
    return {
      codigo_a: codigoA,
      codigo_b: codigoB,
      nombre_a: nombres[codigoA] || SIN_NOMBRE,
      nombre_b: nombres[codigoB] || SIN_NOMBRE,
      motivos: motivosLegibles(motivos),
    };
  }

  /** Un código de oficio que se puede pintar y decidir: un texto no vacío. */
  function esCodigo(valor) {
    return typeof valor === "string" && valor.trim() !== "";
  }

  /**
   * F-035 R75 · Los pares de `oficio.distintos` (su última decisión es
   * «distinto»), listos para «Decididos como distintos». El dato lo añade al
   * backend una ficha aparte (R76, F-053), así que el consumo es tolerante: sin
   * el campo, o si no es una lista, no hay ninguno; una entrada que no son dos
   * códigos distintos se descarta. Cada par sale ordenado, una sola vez y en
   * orden, con el mismo `par()` de siempre y su clave.
   */
  function paresDistintos(distintos, nombres) {
    const porClave = {};
    (Array.isArray(distintos) ? distintos : []).forEach(function (entrada) {
      if (!entrada || !esCodigo(entrada.codigo_a) || !esCodigo(entrada.codigo_b)) {
        return;
      }
      const codigos = ordenados([entrada.codigo_a, entrada.codigo_b]);
      if (codigos.length !== 2) {
        return;
      }
      const clave = codigos.join("-");
      porClave[clave] = Object.assign({ clave: clave }, par(codigos[0], codigos[1], [], nombres));
    });
    return Object.keys(porClave)
      .sort()
      .map(function (clave) {
        return porClave[clave];
      });
  }

  /** Todo lo que pinta la pantalla a partir de `GET /api/catalogos/propuestas`. */
  function presentarPropuestas(respuesta) {
    const oficio = (respuesta && respuesta.oficio) || {};
    const nombres = nombresPorCodigo(oficio.oficios);

    const propuestas = (oficio.propuestas || []).map(function (propuesta) {
      const codigos = ordenados(propuesta.codigos);
      return {
        clave: codigos.join("-"),
        codigos: codigos,
        miembros: miembros(codigos, nombres),
        motivos: motivosLegibles(propuesta.motivos),
        porPares: Boolean(propuesta.por_pares),
        // §15.3 · un clique se confirma entero; lo que viene por pares
        // (R79), par a par.
        confirmarEntero: !propuesta.por_pares,
        pares: (propuesta.pares || []).map(function (p) {
          return par(p.codigo_a, p.codigo_b, p.motivos, nombres);
        }),
      };
    });

    const grupos = (oficio.grupos || [])
      .filter(function (grupo) {
        return (grupo.codigos || []).length > 1;
      })
      .map(function (grupo) {
        const codigos = ordenados(grupo.codigos);
        return {
          clave: codigos.join("-"),
          etiqueta: grupo.etiqueta,
          codigos: codigos,
          miembros: miembros(codigos, nombres),
          pares: paresDe(codigos).map(function (p) {
            return par(p[0], p[1], [], nombres);
          }),
        };
      });

    const avisos = (oficio.avisos || []).map(function (aviso) {
      const codigos = ordenados(aviso.codigos);
      return {
        clave: codigos.join("-"),
        codigos: codigos,
        miembros: miembros(codigos, nombres),
        texto:
          "Estos oficios no se agrupan: alguien dijo que dos de ellos son " +
          "distintos, así que el grupo no se aplica y cada uno sale por su lado.",
      };
    });

    const distintos = paresDistintos(oficio.distintos, nombres);

    return {
      obra: respuesta && respuesta.obra,
      propuestas: propuestas,
      grupos: grupos,
      avisos: avisos,
      distintos: distintos,
      gruposVigentes: oficio.grupos || [],
      sinNada: !propuestas.length && !grupos.length && !avisos.length && !distintos.length,
    };
  }

  /**
   * El cuerpo de `POST /api/catalogos/decisiones` (R88): `confirmado: true`
   * booleano y `catalogo: "oficio"`. Solo lo llama `decidir()`.
   */
  function cuerpoDeDecision(obra, usuarioOid, codigos, decision) {
    if (DECISIONES.indexOf(decision) === -1) {
      throw new Error("una decisión es «mismo» o «distinto»");
    }
    const lista = ordenados(codigos);
    if (lista.length < 2) {
      throw new Error("una decisión necesita al menos dos códigos");
    }
    if (decision === "distinto" && lista.length !== 2) {
      throw new Error("«distinto» se decide de dos en dos");
    }
    return {
      obra: obra,
      usuario_oid: usuarioOid,
      confirmado: true,
      decisiones: [{ catalogo: CATALOGO, codigos: lista, decision: decision }],
    };
  }

  /** R98 · `{obra, oficio: [[cod, cod], …]}`: solo códigos, solo grupos de más de uno. */
  function gruposParaDescargar(obra, grupos) {
    const oficio = (grupos || [])
      .map(function (grupo) {
        return ordenados(grupo.codigos);
      })
      .filter(function (codigos) {
        return codigos.length > 1;
      })
      .sort(function (a, b) {
        return a[0] < b[0] ? -1 : a[0] > b[0] ? 1 : 0;
      });
    return { obra: obra, oficio: oficio };
  }

  /** El fichero JSON de R98, listo para guardar. */
  function ficheroDeGrupos(obra, grupos) {
    const texto = JSON.stringify(gruposParaDescargar(obra, grupos), null, 2) + "\n";
    return {
      nombre: "grupos_vigentes_oficio_" + obra + ".json",
      blob: new Blob([texto], { type: "application/json" }),
    };
  }

  // --- El componente Alpine ---------------------------------------------------

  function crearAppOficios(dependencias) {
    const api = dependencias.api;
    const guardar = dependencias.guardar;
    const mensajeDeError = ImportacionModulo.mensajeDeError;

    return {
      usuario: { usuarioOid: "", correo: "" },
      obra: "",
      cargando: false,
      errorCarga: "",
      vista: null,
      decidiendo: false,
      errorDecision: "",

      async iniciar() {
        this.usuario = await api.identidad();
      },

      async cargar(obraCargada) {
        const obra = String(obraCargada || this.obra || "").trim();
        if (!obra) {
          return;
        }
        this.cargando = true;
        this.errorCarga = "";
        try {
          this.vista = presentarPropuestas(await api.propuestasCatalogos(obra));
        } catch (error) {
          this.vista = null;
          this.errorCarga = mensajeDeError(error);
        } finally {
          this.cargando = false;
        }
      },

      motivoSinDecidir() {
        if (!this.usuario.usuarioOid) {
          return (
            "No hay sesión identificada: sin saber quién decide, el servicio no " +
            "guarda la decisión. Entra por el portal."
          );
        }
        return "";
      },

      puedeDecidir() {
        return Boolean(this.vista) && !this.motivoSinDecidir() && !this.decidiendo;
      },

      /** La ÚNICA salida hacia `POST /api/catalogos/decisiones`: un botón pulsado. */
      async decidir(codigos, decision) {
        if (!this.puedeDecidir()) {
          return;
        }
        // La obra es la de las propuestas que se están viendo, no lo que haya
        // en el campo de texto ahora.
        const obra = this.vista.obra;
        this.decidiendo = true;
        this.errorDecision = "";
        let guardada = false;
        try {
          await api.decidirCatalogos(
            cuerpoDeDecision(obra, this.usuario.usuarioOid, codigos, decision),
          );
          guardada = true;
        } catch (error) {
          this.errorDecision = mensajeDeError(error);
        } finally {
          this.decidiendo = false;
        }
        if (guardada) {
          await this.cargar(obra);
        }
      },

      descargarGrupos() {
        if (!this.vista) {
          return;
        }
        const fichero = ficheroDeGrupos(this.vista.obra, this.vista.gruposVigentes);
        guardar(fichero.blob, fichero.nombre);
      },
    };
  }

  /** El `x-data` de `oficios.html`: el componente con el `api` de verdad. */
  function appOficios() {
    const config = window.CONFIG_POSTVENTA;
    const api = window.Api.crearApi({ baseApi: config.baseApi, config: config });
    return crearAppOficios({
      api: api,
      guardar: function (blob, nombre) {
        ImportacionModulo.guardarBlob(blob, nombre);
      },
    });
  }

  const Oficios = {
    CATALOGO: CATALOGO,
    SIN_NOMBRE: SIN_NOMBRE,
    TEXTO_MOTIVO: TEXTO_MOTIVO,
    motivosLegibles: motivosLegibles,
    paresDe: paresDe,
    nombresPorCodigo: nombresPorCodigo,
    presentarPropuestas: presentarPropuestas,
    cuerpoDeDecision: cuerpoDeDecision,
    gruposParaDescargar: gruposParaDescargar,
    ficheroDeGrupos: ficheroDeGrupos,
    crearAppOficios: crearAppOficios,
  };

  if (typeof window !== "undefined") {
    window.Oficios = Oficios;
    window.appOficios = appOficios;
  }
  if (typeof module !== "undefined" && module.exports) {
    module.exports = Oficios;
  }
})();
