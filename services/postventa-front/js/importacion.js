// services/postventa-front/js/importacion.js
// F-036 R50, R52, R65 · La página de importación (`importar.html`).
//
// Dos mitades, como el resto del front:
//
// - **Lógica pura** (se prueba con `node --test`, `tests_js/importacion.test.js`):
//   el nombre de `Content-Disposition`, el base64 del Excel de errores, los
//   textos de cada estado, el resumen, los errores ordenados y las marcas de
//   la bandeja (duplicadas y oficios ambiguos).
// - **El componente Alpine** `appImportacion`, construido por
//   `crearAppImportacion({api, guardar})` para que los tests le pongan un `api`
//   doble. Solo mueve estado y llama a `js/api.js` y a la lógica de arriba.
//
// Lo que NO hay aquí, a propósito: ningún botón ni método que edite, descarte
// o apruebe una incidencia de la bandeja. Eso es F-038 (`design.md` §9).
// Tampoco se reintenta nada por su cuenta (R52): si una importación falla, lo
// que se enseña es el motivo del backend y la decisión es de quien importa.
//
// La forma de las respuestas es la de los handlers (`progress/impl_F-036.md`,
// B6-7): `total_errores` junto a `errores`, `duplicada_de_fila` y
// `existente_id` siempre presentes, y la bandeja como `{obra, total,
// incidencias}`.

(function () {
  "use strict";

  const TIPO_XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet";

  /** La frase que acompaña al botón del Excel de errores (`design.md` §9). */
  const FRASE_EXCEL_ERRORES = "Corrígelo y súbelo otra vez; lo que ya entró no se duplica.";

  /** La marca de un oficio que tiene varios códigos en Sigrid (R93, D-19). */
  const MARCA_OFICIO_AMBIGUO = "varios códigos en Sigrid: se elige en la revisión";

  const TEXTO_ESTADO_FILA = {
    nueva: "Nueva",
    ya_en_bandeja: "Ya estaba en la bandeja",
    con_error: "Con error: no ha entrado",
  };

  // --- Descargas --------------------------------------------------------------

  /** El último tramo de una ruta: un nombre con `../` no sale de la carpeta. */
  function sinRuta(nombre) {
    const trozos = String(nombre).split(/[\\/]/);
    return trozos[trozos.length - 1].trim();
  }

  /**
   * El nombre del fichero de una cabecera `Content-Disposition`.
   *
   * `filename*` (RFC 6266, codificado) manda sobre `filename`. Sin nombre, o
   * con uno vacío, `porDefecto`.
   */
  function nombreDeDisposicion(cabecera, porDefecto) {
    const texto = String(cabecera || "");
    const extendido = /filename\*\s*=\s*([^']*)''([^;]+)/i.exec(texto);
    if (extendido) {
      try {
        const nombre = sinRuta(decodeURIComponent(extendido[2].trim()));
        if (nombre) {
          return nombre;
        }
      } catch (error) {
        // Mal codificado: se prueba con `filename`.
      }
    }
    const simple = /filename\s*=\s*(?:"([^"]*)"|([^;]+))/i.exec(texto);
    if (simple) {
      const nombre = sinRuta(simple[1] !== undefined ? simple[1] : simple[2]);
      if (nombre) {
        return nombre;
      }
    }
    return porDefecto;
  }

  /** El nombre de la plantilla si el backend no lo dice. */
  function nombrePorDefectoDePlantilla(obra) {
    return "plantilla_incidencias_" + obra + ".xlsx";
  }

  /** Los bytes de un texto en base64 (R65: el Excel de errores viaja así). */
  function bytesDeBase64(texto) {
    const binario = atob(String(texto || ""));
    const bytes = new Uint8Array(binario.length);
    for (let i = 0; i < binario.length; i += 1) {
      bytes[i] = binario.charCodeAt(i);
    }
    return bytes;
  }

  /** `{nombre, blob}` del Excel de errores de una respuesta, o `null` si no lo hay (R69). */
  function excelDeErrores(respuesta) {
    const excel = respuesta && respuesta.excel_errores;
    if (!excel) {
      return null;
    }
    return {
      nombre: excel.nombre,
      blob: new Blob([bytesDeBase64(excel.contenido_b64)], { type: TIPO_XLSX }),
    };
  }

  /**
   * Guarda un `Blob` en el disco del usuario: un enlace con `download`, un
   * clic y la URL liberada. `entorno` es inyectable para probarlo sin DOM.
   */
  function guardarBlob(blob, nombre, entorno) {
    const ajustes = entorno || { documento: document, URL: URL };
    const url = ajustes.URL.createObjectURL(blob);
    const enlace = ajustes.documento.createElement("a");
    enlace.href = url;
    enlace.download = nombre;
    ajustes.documento.body.appendChild(enlace);
    try {
      enlace.click();
    } finally {
      ajustes.documento.body.removeChild(enlace);
      ajustes.URL.revokeObjectURL(url);
    }
  }

  // --- El resultado de una importación (R43) ----------------------------------

  function textoDeFila(fila) {
    if (fila.estado === "duplicada_en_fichero") {
      return "Duplicada de la fila " + fila.duplicada_de_fila + " del mismo fichero";
    }
    return TEXTO_ESTADO_FILA[fila.estado] || String(fila.estado);
  }

  function textoDelEstado(respuesta) {
    if (respuesta.ya_importado) {
      return "Este fichero ya se había importado: no se ha añadido nada a la bandeja.";
    }
    if (respuesta.estado === "parcial") {
      return (
        "Importación parcial: han entrado las filas buenas; las que tienen " +
        "errores, no."
      );
    }
    return "Importación completa: ninguna fila tiene errores.";
  }

  function plural(n, singular, varios) {
    return n + " " + (n === 1 ? singular : varios);
  }

  function resumenLegible(resumen) {
    return [
      plural(resumen.leidas, "fila leída", "filas leídas"),
      plural(resumen.nuevas, "nueva", "nuevas"),
      plural(resumen.duplicadas_en_fichero, "duplicada en el fichero", "duplicadas en el fichero"),
      resumen.ya_en_bandeja + " ya en la bandeja",
      resumen.con_error + " con error",
    ].join(" · ");
  }

  /** Los errores por número de fila; dentro de la fila, en el orden del backend. */
  function erroresOrdenados(errores) {
    return (errores || [])
      .map(function (error, posicion) {
        return { error: error, posicion: posicion };
      })
      .sort(function (a, b) {
        return a.error.fila - b.error.fila || a.posicion - b.posicion;
      })
      .map(function (par) {
        return par.error;
      });
  }

  function textoDelError(error) {
    return "Fila " + error.fila + " · columna " + error.columna + " · " + error.problema;
  }

  /** R33 · si la lista viene cortada, cuántos hay y dónde están todos. */
  function avisoDeErroresRecortados(respuesta) {
    const lista = (respuesta && respuesta.errores) || [];
    const total = (respuesta && respuesta.total_errores) || 0;
    if (total <= lista.length) {
      return "";
    }
    return (
      "Se enseñan los primeros " + lista.length + " errores de " + total +
      ": el Excel de errores los trae todos."
    );
  }

  /** Todo lo que pinta el bloque «Importar» a partir de la respuesta 200. */
  function presentarImportacion(respuesta) {
    return {
      obra: respuesta.obra,
      estado: respuesta.estado,
      yaImportado: Boolean(respuesta.ya_importado),
      estadoTexto: textoDelEstado(respuesta),
      resumenTexto: resumenLegible(respuesta.resumen),
      filas: (respuesta.filas || []).map(function (fila) {
        return {
          fila: fila.fila,
          estado: fila.estado,
          texto: textoDeFila(fila),
          avisos: fila.avisos || [],
        };
      }),
      errores: erroresOrdenados(respuesta.errores).map(textoDelError),
      avisoRecorte: avisoDeErroresRecortados(respuesta),
      hayExcelDeErrores: Boolean(respuesta.excel_errores),
      crudo: respuesta,
    };
  }

  // --- La bandeja (R45, R50, R93, R99) ----------------------------------------

  function conCodigo(nombre, codigo) {
    if (!nombre && !codigo) {
      return "—";
    }
    if (!codigo) {
      return nombre;
    }
    return (nombre || "") + " (" + codigo + ")";
  }

  function marcaDeDuplicada(incidencia, porId) {
    const original = porId[incidencia.duplicada_de];
    if (!original) {
      return "duplicada de una incidencia anterior";
    }
    if (original.importacion_id !== incidencia.importacion_id) {
      return "duplicada de la fila " + original.fila_origen + " de otra importación";
    }
    return "duplicada de la fila " + original.fila_origen;
  }

  /** Las filas de `GET /api/bandeja` con sus marcas y sus textos de oficio y proveedor. */
  function filasDeBandeja(incidencias) {
    const lista = incidencias || [];
    const porId = {};
    lista.forEach(function (incidencia) {
      porId[incidencia.incidencia_id] = incidencia;
    });
    return lista.map(function (incidencia) {
      const marcas = [];
      if (incidencia.duplicada_de) {
        marcas.push(marcaDeDuplicada(incidencia, porId));
      }
      if (incidencia.oficio_ambiguo) {
        marcas.push(MARCA_OFICIO_AMBIGUO);
      }
      return Object.assign({}, incidencia, {
        marcas: marcas,
        oficioTexto: conCodigo(incidencia.oficio_nombre, incidencia.oficio_codigo),
        proveedorTexto: conCodigo(incidencia.proveedor_nombre, incidencia.proveedor_codigo),
      });
    });
  }

  /** R52 · el texto que se enseña de un error: el del backend si lo trae. */
  function mensajeDeError(error) {
    if (!error) {
      return "Error desconocido.";
    }
    return error.mensaje || error.message || String(error);
  }

  // --- El componente Alpine ---------------------------------------------------

  /**
   * El estado de `importar.html`. `dependencias.api` es el cliente de
   * `js/api.js` (o un doble); `dependencias.guardar(blob, nombre)`, la descarga
   * al disco.
   */
  function crearAppImportacion(dependencias) {
    const api = dependencias.api;
    const guardar = dependencias.guardar;

    return {
      usuario: { usuarioOid: "", correo: "" },

      // 1 · Plantilla
      obra: "",
      descargandoPlantilla: false,
      errorPlantilla: "",

      // 2 · Importar
      fichero: null,
      importando: false,
      resultado: null,
      errorImportacion: "",
      fraseExcelErrores: FRASE_EXCEL_ERRORES,

      // 3 · Bandeja
      bandeja: [],
      bandejaObra: "",
      bandejaCargada: false,
      cargandoBandeja: false,
      errorBandeja: "",

      async iniciar() {
        this.usuario = await api.identidad();
      },

      obraEscrita() {
        return String(this.obra || "").trim();
      },

      puedeDescargarPlantilla() {
        return Boolean(this.obraEscrita()) && !this.descargandoPlantilla;
      },

      async descargarPlantilla() {
        if (!this.puedeDescargarPlantilla()) {
          return;
        }
        const obra = this.obraEscrita();
        this.descargandoPlantilla = true;
        this.errorPlantilla = "";
        try {
          const descarga = await api.descargarPlantilla(obra);
          guardar(
            descarga.blob,
            nombreDeDisposicion(descarga.disposicion, nombrePorDefectoDePlantilla(obra)),
          );
        } catch (error) {
          this.errorPlantilla = mensajeDeError(error);
        } finally {
          this.descargandoPlantilla = false;
        }
      },

      alElegirFichero(evento) {
        const ficheros = (evento && evento.target && evento.target.files) || [];
        this.fichero = ficheros[0] || null;
        this.resultado = null;
        this.errorImportacion = "";
      },

      motivoSinImportar() {
        if (!this.usuario.usuarioOid) {
          return (
            "No hay sesión identificada: sin saber quién importa, el servicio " +
            "no acepta el fichero. Entra por el portal."
          );
        }
        if (!this.fichero) {
          return "Elige primero el fichero .xlsx.";
        }
        return "";
      },

      puedeImportar() {
        return !this.motivoSinImportar() && !this.importando;
      },

      async importar() {
        if (!this.puedeImportar()) {
          return;
        }
        this.importando = true;
        this.errorImportacion = "";
        this.resultado = null;
        try {
          // R52 · UNA petición. Si falla, se enseña el motivo y ya.
          const respuesta = await api.importarExcel(this.fichero, this.usuario.usuarioOid);
          this.resultado = presentarImportacion(respuesta);
          this.obra = respuesta.obra;
        } catch (error) {
          this.errorImportacion = mensajeDeError(error);
        } finally {
          this.importando = false;
        }
        if (this.resultado) {
          await this.cargarBandeja();
        }
      },

      descargarExcelDeErrores() {
        const excel = this.resultado && excelDeErrores(this.resultado.crudo);
        if (excel) {
          guardar(excel.blob, excel.nombre);
        }
      },

      async cargarBandeja() {
        const obra = this.obraEscrita();
        if (!obra || this.cargandoBandeja) {
          return;
        }
        this.cargandoBandeja = true;
        this.errorBandeja = "";
        try {
          const respuesta = await api.bandeja(obra);
          this.bandeja = filasDeBandeja(respuesta.incidencias);
          this.bandejaObra = respuesta.obra;
          this.bandejaCargada = true;
        } catch (error) {
          this.bandeja = [];
          this.bandejaCargada = false;
          this.errorBandeja = mensajeDeError(error);
        } finally {
          this.cargandoBandeja = false;
        }
      },
    };
  }

  /** El `x-data` de `importar.html`: el componente con el `api` de verdad. */
  function appImportacion() {
    const config = window.CONFIG_POSTVENTA;
    const api = window.Api.crearApi({ baseApi: config.baseApi, config: config });
    return crearAppImportacion({
      api: api,
      guardar: function (blob, nombre) {
        guardarBlob(blob, nombre);
      },
    });
  }

  const Importacion = {
    TIPO_XLSX: TIPO_XLSX,
    FRASE_EXCEL_ERRORES: FRASE_EXCEL_ERRORES,
    MARCA_OFICIO_AMBIGUO: MARCA_OFICIO_AMBIGUO,
    nombreDeDisposicion: nombreDeDisposicion,
    nombrePorDefectoDePlantilla: nombrePorDefectoDePlantilla,
    bytesDeBase64: bytesDeBase64,
    excelDeErrores: excelDeErrores,
    guardarBlob: guardarBlob,
    textoDeFila: textoDeFila,
    textoDelEstado: textoDelEstado,
    resumenLegible: resumenLegible,
    erroresOrdenados: erroresOrdenados,
    textoDelError: textoDelError,
    avisoDeErroresRecortados: avisoDeErroresRecortados,
    presentarImportacion: presentarImportacion,
    filasDeBandeja: filasDeBandeja,
    mensajeDeError: mensajeDeError,
    crearAppImportacion: crearAppImportacion,
  };

  if (typeof window !== "undefined") {
    window.Importacion = Importacion;
    window.appImportacion = appImportacion;
  }
  if (typeof module !== "undefined" && module.exports) {
    module.exports = Importacion;
  }
})();
