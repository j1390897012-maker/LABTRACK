// ============================================================
// ESTADO DEL FLUJO RFID / QR
// ============================================================

let sesionActual = null;
let equiposOperacion = [];
let ultimoScanVisto = null;
let uidPendienteEnrolar = null;

// Información de la devolución actualmente en curso.
let devolucionActual = null;

// Desde dónde se abrió el modal de devolución: "manual" o "qr".
let origenDevolucion = null;

// Indica si ya sincronizamos el último scan existente al cargar.
let pollingInicializado = false;

const STORAGE_ULTIMO_SCAN = "labtrack_ultimo_scan";

// Timestamp del RFID que inició la operación actual.
let inicioOperacionRFID = null;

// Resolutores pendientes de los modales de confirmación / selección.
let resolverConfirmacion = null;
let resolverSeleccionEstudiante = null;

// ============================================================
// CONFIRMACIÓN EN INTERFAZ (reemplaza confirm() nativo)
// ============================================================

function mostrarConfirmacion(mensaje, opciones = {}) {
  const {
    titulo = "Confirmar acción",
    textoAceptar = "Confirmar",
    textoCancelar = "Cancelar",
    peligro = false,
  } = opciones;

  const tituloEl = document.getElementById("confirm-modal-titulo");
  const mensajeEl = document.getElementById("confirm-modal-mensaje");
  const aceptarBtn = document.getElementById("confirm-modal-aceptar");
  const cancelarBtn = document.getElementById("confirm-modal-cancelar");

  if (tituloEl) tituloEl.textContent = titulo;
  if (mensajeEl) mensajeEl.textContent = mensaje;

  if (aceptarBtn) {
    aceptarBtn.textContent = textoAceptar;
    aceptarBtn.className = peligro ? "button button-danger" : "button button-primary";
  }

  if (cancelarBtn) {
    cancelarBtn.textContent = textoCancelar;
  }

  openModal("confirm-modal");

  return new Promise((resolve) => {
    resolverConfirmacion = resolve;
  });
}

function responderConfirmacion(valor) {
  closeModal("confirm-modal");

  if (resolverConfirmacion) {
    const resolve = resolverConfirmacion;
    resolverConfirmacion = null;
    resolve(valor);
  }
}

// ============================================================
// SELECCIÓN DE ESTUDIANTE EN INTERFAZ (reemplaza prompt() nativo)
// ============================================================

function mostrarSeleccionEstudiante(estudiantes) {
  const lista = document.getElementById("seleccionar-estudiante-lista");

  if (lista) {
    lista.innerHTML = estudiantes
      .map(
        (e, i) => `
          <button
            type="button"
            class="student-option"
            onclick="elegirEstudianteSesion(${i})"
          >
            <span>${e.nombre}</span>
            <span class="code">${e.matricula}</span>
          </button>
        `
      )
      .join("");
  }

  openModal("seleccionar-estudiante-modal");

  return new Promise((resolve) => {
    resolverSeleccionEstudiante = { resolve, estudiantes };
  });
}

function elegirEstudianteSesion(indice) {
  const contexto = resolverSeleccionEstudiante;
  closeModal("seleccionar-estudiante-modal");

  if (contexto) {
    resolverSeleccionEstudiante = null;
    contexto.resolve(contexto.estudiantes[indice]);
  }
}

function cerrarSeleccionEstudiante() {
  const contexto = resolverSeleccionEstudiante;
  closeModal("seleccionar-estudiante-modal");

  if (contexto) {
    resolverSeleccionEstudiante = null;
    contexto.resolve(null);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const confirmModal = document.getElementById("confirm-modal");
  if (confirmModal) {
    confirmModal.addEventListener("click", (event) => {
      if (event.target === confirmModal) {
        responderConfirmacion(false);
      }
    });
  }

  const seleccionModal = document.getElementById("seleccionar-estudiante-modal");
  if (seleccionModal) {
    seleccionModal.addEventListener("click", (event) => {
      if (event.target === seleccionModal) {
        cerrarSeleccionEstudiante();
      }
    });
  }
});

// ============================================================
// OPERACIÓN MANUAL — PRÉSTAMO
// ============================================================

async function prestarEquipoManual() {
  const matricula = document.getElementById("manual-prestamo-matricula").value.trim();
  const codigo = document.getElementById("manual-prestamo-codigo").value.trim();
  const resultado = document.getElementById("manual-prestamo-resultado");

  if (!matricula || !codigo) {
    resultado.innerHTML = `
      <div class="card stat-card" style="border-left: 4px solid var(--danger);">
        <div class="stat-description" style="color: var(--text);">
          Debes proporcionar la matrícula y el código del equipo.
        </div>
      </div>
    `;
    return;
  }

  try {
    const sesion = await peticionAPI(`/sesiones/activa?matricula=${encodeURIComponent(matricula)}`);
    const equipo = await peticionAPI(`/equipos/${encodeURIComponent(codigo)}`);

    const respuesta = await peticionAPI("/equipos/prestar", "POST", {
      sesion_id: sesion.sesion_id,
      equipo_id: equipo.id,
      accesorios: [],
    });

    resultado.innerHTML = `
      <div class="card stat-card" style="border-left: 4px solid var(--success);">
        <div class="stat-label">Préstamo registrado</div>
        <div class="stat-description" style="color: var(--text);">
          ${respuesta.mensaje || "Préstamo registrado correctamente."}
        </div>
      </div>
    `;

    document.getElementById("manual-prestamo-matricula").value = "";
    document.getElementById("manual-prestamo-codigo").value = "";

    await cargarEquiposDesdeAPI();
  } catch (error) {
    resultado.innerHTML = `
      <div class="card stat-card" style="border-left: 4px solid var(--danger);">
        <div class="stat-label">No se pudo registrar el préstamo</div>
        <div class="stat-description" style="color: var(--text);">
          ${error.detail || "Ocurrió un error."}
        </div>
      </div>
    `;
  }
}

// ============================================================
// OPERACIÓN MANUAL — DEVOLUCIÓN
// ============================================================

async function devolverEquipoManual() {
  const codigo = document.getElementById("manual-devolucion-codigo").value.trim();
  const resultado = document.getElementById("manual-devolucion-resultado");

  if (!codigo) {
    resultado.innerHTML = `
      <div class="card stat-card" style="border-left: 4px solid var(--danger);">
        <div class="stat-description" style="color: var(--text);">
          Debes proporcionar el código del equipo.
        </div>
      </div>
    `;
    return;
  }

  try {
    const respuesta = await peticionAPI("/devoluciones", "POST", {
      codigo_equipo: codigo,
    });

    resultado.innerHTML = "";
    document.getElementById("manual-devolucion-codigo").value = "";

    abrirModalDevolucion(respuesta, "manual");
  } catch (error) {
    resultado.innerHTML = `
      <div class="card stat-card" style="border-left: 4px solid var(--danger);">
        <div class="stat-label">No se pudo iniciar la devolución</div>
        <div class="stat-description" style="color: var(--text);">
          ${error.detail || "Ocurrió un error."}
        </div>
      </div>
    `;
  }
}

// ============================================================
// MODAL DE DEVOLUCIÓN (compartido por manual y QR)
// ============================================================

function abrirModalDevolucion(datosDevolucion, origen) {
  devolucionActual = datosDevolucion;
  origenDevolucion = origen;

  const codigoLabel = document.getElementById("devolucion-codigo-label");
  const codigoInput = document.getElementById("input-devolucion-codigo");
  const estadoInput = document.getElementById("input-devolucion-estado");
  const fallaInput = document.getElementById("input-devolucion-falla");
  const grupoFalla = document.getElementById("grupo-devolucion-falla");
  const resultado = document.getElementById("devolucion-modal-resultado");

  if (codigoLabel) codigoLabel.textContent = datosDevolucion.codigo_equipo;
  if (codigoInput) codigoInput.value = datosDevolucion.codigo_equipo;
  if (estadoInput) estadoInput.value = "Disponible";
  if (fallaInput) fallaInput.value = "";
  if (grupoFalla) grupoFalla.style.display = "none";
  if (resultado) resultado.innerHTML = "";

  poblarAccesoriosDevolucion(datosDevolucion.accesorios);

  openModal("devolucion-modal");
}

function poblarAccesoriosDevolucion(accesorios) {
  const grupo = document.getElementById("grupo-devolucion-accesorios");
  const lista = document.getElementById("devolucion-accesorios-lista");

  if (!grupo || !lista) {
    return;
  }

  if (!accesorios || accesorios.length === 0) {
    grupo.hidden = true;
    lista.innerHTML = "";
    return;
  }

  grupo.hidden = false;

  lista.innerHTML = accesorios
    .map(
      (a) => `
        <div class="accesorio-row">
          <div>
            <div class="accesorio-nombre">${a.nombre}</div>
            <div class="accesorio-meta">Prestados: ${a.cantidad_prestada}</div>
          </div>
          <input
            type="number"
            class="input"
            id="accesorio-cantidad-${a.tipo_accesorio_id}"
            value="${a.cantidad_prestada}"
            min="0"
            max="${a.cantidad_prestada}"
          >
        </div>
      `
    )
    .join("");
}

function leerAccesoriosDevolucionDesdeFormulario() {
  if (!devolucionActual || !devolucionActual.accesorios || devolucionActual.accesorios.length === 0) {
    return [];
  }

  const accesorios = [];

  for (const accesorio of devolucionActual.accesorios) {
    const input = document.getElementById(`accesorio-cantidad-${accesorio.tipo_accesorio_id}`);
    const cantidad = input ? Number(input.value) : NaN;

    if (
      !Number.isInteger(cantidad) ||
      cantidad < 0 ||
      cantidad > accesorio.cantidad_prestada
    ) {
      mostrarErrorDevolucionModal(
        `Cantidad inválida para ${accesorio.nombre}. Debe estar entre 0 y ${accesorio.cantidad_prestada}.`
      );
      return null;
    }

    accesorios.push({
      tipo_accesorio_id: accesorio.tipo_accesorio_id,
      cantidad_devuelta: cantidad,
    });
  }

  return accesorios;
}

function mostrarErrorDevolucionModal(texto) {
  const el = document.getElementById("devolucion-modal-resultado");

  if (el) {
    el.innerHTML = `
      <div class="card stat-card" style="border-left: 4px solid var(--danger);">
        <div class="stat-description" style="color: var(--text);">${texto}</div>
      </div>
    `;
  }
}

function toggleFallaDevolucion() {
  const estado = document.getElementById("input-devolucion-estado").value;
  const grupo = document.getElementById("grupo-devolucion-falla");

  if (grupo) {
    grupo.style.display = estado === "En revisión" ? "block" : "none";
  }
}

async function completarDevolucion(datosDevolucion, estado, descripcionFalla, accesoriosDevueltos) {
  const sesionEquipoId = datosDevolucion.sesion_equipo_id;

  if (!sesionEquipoId) {
    throw { detail: "La respuesta de devolución no contiene sesion_equipo_id." };
  }

  await peticionAPI("/devoluciones/accesorios", "POST", {
    sesion_id: sesionEquipoId, // O sesion_equipo_id según tu API
    sesion_equipo_id: sesionEquipoId,
    accesorios: accesoriosDevueltos,
  });

  const huboFalla = estado === "En revisión";

  const resultadoFalla = await peticionAPI(
    `/devoluciones/${sesionEquipoId}/falla`,
    "PATCH",
    {
      hubo_falla: huboFalla,
      descripcion: huboFalla ? descripcionFalla : null,
    }
  );

  return resultadoFalla;
}

async function confirmarDevolucion() {
  if (!devolucionActual) {
    mostrarErrorDevolucionModal("No existe una devolución activa.");
    return;
  }

  const estado = document.getElementById("input-devolucion-estado").value;
  const falla = document.getElementById("input-devolucion-falla").value.trim();

  if (estado === "En revisión" && !falla) {
    mostrarErrorDevolucionModal(
      "Debes describir la falla o incidencia del equipo para ponerlo en revisión."
    );
    return;
  }

  const accesorios = leerAccesoriosDevolucionDesdeFormulario();

  if (accesorios === null) {
    return;
  }

  try {
    const resultadoFalla = await completarDevolucion(
      devolucionActual,
      estado,
      falla || null,
      accesorios
    );

    const codigo = devolucionActual.codigo_equipo;
    const equipoId = devolucionActual.equipo_id;
    const origen = origenDevolucion;

    closeModal("devolucion-modal");
    devolucionActual = null;
    origenDevolucion = null;

    const mensaje = resultadoFalla.mensaje || `Devolución de ${codigo} procesada.`;

    if (origen === "qr") {
      agregarEquipoOperacion({
        codigo,
        tipo: "Devuelto",
        estado: resultadoFalla.equipo_estado,
        equipo_id: equipoId,
        accion: "devolucion_completada",
      });

      mostrarResultadoRFID(mensaje);

      actualizarEstadoRFID(
        estado === "En revisión" ? "Equipo en revisión" : "Devolución registrada",
        estado === "En revisión" ? "El equipo quedó marcado para revisión." : "El equipo quedó disponible."
      );

      finalizarVistaSiNoHaySesion();
    } else {
      const resultado = document.getElementById("manual-devolucion-resultado");

      if (resultado) {
        resultado.innerHTML = `
          <div class="card stat-card" style="border-left: 4px solid var(--success);">
            <div class="stat-label">Devolución procesada</div>
            <div class="stat-description" style="color: var(--text);">${mensaje}</div>
          </div>
        `;
      }
    }

    await cargarEquiposDesdeAPI();
  } catch (error) {
    mostrarErrorDevolucionModal(error.detail || "Error desconocido al procesar la devolución.");
  }
}

function cancelarDevolucion() {
  const origen = origenDevolucion;

  closeModal("devolucion-modal");
  devolucionActual = null;
  origenDevolucion = null;

  if (origen === "qr" && !sesionActual) {
    mostrarResultadoRFID("Devolución cancelada. No se realizó ningún cambio.");
    finalizarVistaSiNoHaySesion();
  }
}

// ============================================================
// MODAL DE SIMULACIÓN RFID
// ============================================================

function simularRFID() {
  openModal("rfid-modal");

  setTimeout(() => {
    const input = document.getElementById("input-rfid-simulado");
    if (input) {
      input.focus();
    }
  }, 100);
}

async function procesarRFID() {
  const input = document.getElementById("input-rfid-simulado");
  const uid = input.value.trim();

  if (!uid) {
    return;
  }

  closeModal("rfid-modal");
  input.value = "";

  await procesarScan("rfid", uid);
}

// ============================================================
// PROCESAMIENTO DE SCAN
// ============================================================

async function procesarScan(tipo, valor) {
  try {
    const data = await peticionAPI("/identificaciones/scan", "POST", {
      tipo,
      valor,
    });

    if (tipo === "rfid") {
      await manejarRespuestaRFID(valor, data);
      return;
    }

    if (tipo === "qr") {
      await manejarRespuestaQR(data);
    }
  } catch (error) {
    mostrarResultadoRFID(
      "Error: " + (error.detail || "No se pudo procesar el escaneo.")
    );
  }
}

// ============================================================
// RFID
// ============================================================

async function manejarRespuestaRFID(valor, data) {
  if (data.estado === "no_registrado") {
    const confirmar = await mostrarConfirmacion(
      `La tarjeta RFID (${valor}) no está registrada.\n\n¿Deseas enrolarla a un estudiante?`,
      { titulo: "Tarjeta no registrada", textoAceptar: "Enrolar tarjeta" }
    );

    if (!confirmar) {
      return;
    }

    abrirEnrolamientoRFID(valor);
    return;
  }

  inicioOperacionRFID = new Date().toISOString();
  equiposOperacion = [];

  const lista = document.getElementById("rfid-flow-equipo-list");
  const equipos = document.getElementById("rfid-flow-equipos");

  if (lista) {
    lista.innerHTML = "";
  }

  if (equipos) {
    equipos.hidden = true;
  }

  sesionActual = {
    sesion_id: data.sesion_id,
    matricula: data.matricula,
    nombre: data.nombre,
  };

  abrirVistaPrestamoRFID();
  mostrarEstudianteRFID(data);

  actualizarEstadoRFID(
    "RFID detectada",
    "Listo para escanear un equipo."
  );

  const esperandoQR = document.getElementById("rfid-flow-esperando-qr");

  if (esperandoQR) {
    esperandoQR.hidden = false;
  }

  const botonTerminar = document.getElementById("btn-terminar-operacion");

  if (botonTerminar) {
    botonTerminar.style.display = "block";
  }
}

// ============================================================
// MOSTRAR ESTUDIANTE
// ============================================================

function mostrarEstudianteRFID(data) {
  const contenedor = document.getElementById("rfid-flow-estudiante");

  if (!contenedor) {
    return;
  }

  contenedor.hidden = false;

  const nombre = document.getElementById("rfid-flow-nombre");
  const matricula = document.getElementById("rfid-flow-matricula");
  const sesion = document.getElementById("rfid-flow-sesion");

  if (nombre) {
    nombre.textContent = data.nombre || "—";
  }

  if (matricula) {
    matricula.textContent = data.matricula || "—";
  }

  if (sesion) {
    sesion.textContent = data.sesion_id
      ? `Sesión #${data.sesion_id}`
      : "Sin sesión";
  }
}

// ============================================================
// ESTADO DE LA VISTA RFID
// ============================================================

function actualizarEstadoRFID(estado, subtitulo) {
  const badge = document.getElementById("rfid-flow-badge");
  const status = document.getElementById("rfid-flow-status");
  const subtitle = document.getElementById("rfid-flow-subtitle");

  if (badge) {
    badge.innerHTML = `<span class="status-dot"></span> ${estado}`;
  }

  if (status) {
    status.textContent = subtitulo;
  }

  if (subtitle) {
    subtitle.textContent = subtitulo;
  }
}

// ============================================================
// RESULTADO DEL FLUJO RFID (Logs ocultos por petición)
// ============================================================

function mostrarResultadoRFID(texto) {
  const el = document.getElementById("rfid-flow-resultado");
  if (el) {
    el.innerHTML = ""; // Se deja vacío para eliminar la caja de logs
  }
}

// ============================================================
// QR
// ============================================================

async function manejarRespuestaQR(data) {
  const candidatos = data.estudiantes || (data.estudiante ? [data.estudiante] : []);

  // ----------------------------------------------------------
  // NO HAY SESIÓN EN EL FRONTEND, PERO EL EQUIPO SE PUEDE PRESTAR
  // ----------------------------------------------------------
  if (!sesionActual && (data.accion === "confirmar_prestamo" || data.accion === "seleccionar_estudiante")) {
    if (candidatos.length === 0) {
      mostrarResultadoRFID(
        "Se detectó un QR de un equipo libre, pero primero debes identificar al estudiante mediante RFID o tener una sesión activa."
      );
      return;
    }

    if (candidatos.length === 1) {
      await confirmarAsignacionAEstudiante(candidatos[0], data);
    } else {
      const elegido = await mostrarSeleccionEstudiante(candidatos);

      if (!elegido) {
        mostrarResultadoRFID("No se seleccionó ningún estudiante. No se registró el préstamo.");
        return;
      }

      await confirmarAsignacionAEstudiante(elegido, data);
    }

    return;
  }

  // ----------------------------------------------------------
  // EQUIPO EN REVISIÓN
  // ----------------------------------------------------------
  if (data.accion === "revisar_fallas") {
    const fallas = (data.fallas || []).map((f) => f.descripcion).join("; ");
    agregarEquipoOperacion({
      codigo: data.codigo,
      tipo: data.tipo,
      estado: "En revisión",
      accion: "revisar_fallas",
    });

    mostrarResultadoRFID(`${data.codigo} está EN REVISIÓN. Fallas registradas: ${fallas || "sin descripción"}`);
    actualizarEstadoRFID("Equipo en revisión", "El encargado debe decidir si desea prestar el equipo.");
    return;
  }

  // ----------------------------------------------------------
  // DEVOLUCIÓN
  // ----------------------------------------------------------
  if (data.accion === "iniciar_devolucion") {
    await manejarDevolucionQR(data);
    return;
  }

  // ----------------------------------------------------------
  // CONFIRMAR PRÉSTAMO (con sesión ya activa en el frontend)
  // ----------------------------------------------------------
  if (data.accion === "confirmar_prestamo") {
    const estudiantes = data.estudiantes || [];

    const esSesionActual = sesionActual && (
      estudiantes.some((e) => e.matricula === sesionActual.matricula) ||
      (data.estudiante && data.estudiante.matricula === sesionActual.matricula)
    );

    agregarEquipoOperacion({
      codigo: data.codigo,
      tipo: data.tipo,
      estado: data.estado || "Disponible",
      equipo_id: data.equipo_id,
      accion: "confirmar_prestamo",
    });

    if (esSesionActual) {
      await registrarPrestamo(sesionActual.sesion_id, data);
      return;
    }

    mostrarResultadoRFID(`${data.codigo}: ${data.mensaje || "Equipo listo para préstamo."}`);
    return;
  }

  // ----------------------------------------------------------
  // SELECCIONAR ESTUDIANTE (con sesión ya activa en el frontend)
  // ----------------------------------------------------------
  if (data.accion === "seleccionar_estudiante") {
    await seleccionarEstudianteYPrestar(data);
    return;
  }

  // ----------------------------------------------------------
  // RESPUESTA GENÉRICA
  // ----------------------------------------------------------
  agregarEquipoOperacion({
    codigo: data.codigo,
    tipo: data.tipo,
    estado: data.estado,
    equipo_id: data.equipo_id,
    accion: data.accion,
  });

  mostrarResultadoRFID(`${data.codigo || "Equipo"}: ${data.mensaje || "Operación procesada."}`);
}

// ============================================================
// RECONECTAR SESIÓN EXISTENTE Y CONFIRMAR ASIGNACIÓN
// ============================================================

async function confirmarAsignacionAEstudiante(estudiante, dataEquipo) {
  let sesionId = estudiante.sesion_id || dataEquipo.sesion_id;
  let equiposActuales = [];

  try {
    const sesionDetalle = await peticionAPI(
      `/sesiones/activa?matricula=${encodeURIComponent(estudiante.matricula)}`
    );
    sesionId = sesionDetalle.sesion_id || sesionId;
    equiposActuales = sesionDetalle.equipos || [];
  } catch (error) {
    // Si falla la consulta, seguimos sin la lista previa
  }

  const listaEquipos = equiposActuales.length
    ? equiposActuales.map((e) => `• ${e.codigo} (${e.tipo || "—"})`).join("\n")
    : "Sin equipos prestados por ahora.";

  const confirmar = await mostrarConfirmacion(
    `Sesión activa de ${estudiante.nombre} (${estudiante.matricula})\n\n` +
    `Equipos actuales en su sesión:\n${listaEquipos}\n\n` +
    `¿Deseas agregar el equipo ${dataEquipo.codigo} a esta sesión?`,
    { titulo: "Asignar equipo", textoAceptar: "Sí, asignar" }
  );

  if (!confirmar) {
    mostrarResultadoRFID(`Operación cancelada para el equipo ${dataEquipo.codigo}.`);
    return;
  }

  sesionActual = {
    sesion_id: sesionId,
    matricula: estudiante.matricula,
    nombre: estudiante.nombre,
  };

  equiposOperacion = [];
  inicioOperacionRFID = new Date().toISOString();

  abrirVistaPrestamoRFID();
  mostrarEstudianteRFID({
    nombre: sesionActual.nombre,
    matricula: sesionActual.matricula,
    sesion_id: sesionActual.sesion_id,
  });

  equiposActuales.forEach((e) =>
    agregarEquipoOperacion({
      codigo: e.codigo,
      tipo: e.tipo,
      estado: "Prestado",
      accion: "ya_en_sesion",
    })
  );

  const btnTerminar = document.getElementById("btn-terminar-operacion");
  if (btnTerminar) btnTerminar.style.display = "block";

  const esperandoQR = document.getElementById("rfid-flow-esperando-qr");
  if (esperandoQR) esperandoQR.hidden = false;

  actualizarEstadoRFID("Sesión recuperada", "Procesando préstamo...");

  await registrarPrestamo(sesionActual.sesion_id, dataEquipo);
}

// ============================================================
// DEVOLUCIÓN INICIADA DESDE QR (sin necesidad de RFID previo)
// ============================================================

async function manejarDevolucionQR(data) {
  const yaPrestadoEnEstaOperacion =
    sesionActual &&
    equiposOperacion.some(
      (e) => e.codigo === data.codigo && e.accion === "prestamo_confirmado"
    );

  if (yaPrestadoEnEstaOperacion) {
    mostrarResultadoRFID(
      `${data.codigo} ya fue agregado al préstamo de esta operación.`
    );
    return;
  }

  const estudiante = data.prestamo ? data.prestamo.estudiante : null;

  abrirVistaPrestamoRFID();

  const esperandoQR = document.getElementById("rfid-flow-esperando-qr");
  if (esperandoQR) {
    esperandoQR.hidden = true;
  }

  if (estudiante) {
    let sesionId = null;

    try {
      const sesion = await peticionAPI(
        `/sesiones/activa?matricula=${encodeURIComponent(estudiante.matricula)}`
      );
      sesionId = sesion.sesion_id;
    } catch (error) {
      // Ignorar error de sesión
    }

    mostrarEstudianteRFID({
      nombre: estudiante.nombre,
      matricula: estudiante.matricula,
      sesion_id: sesionId,
    });
  }

  const nombreEstudiante = estudiante ? estudiante.nombre : "un estudiante";

  mostrarResultadoRFID(
    `${data.codigo} está actualmente prestado a ${nombreEstudiante}.`
  );

  actualizarEstadoRFID(
    "Equipo prestado",
    "El equipo está prestado. Confirma si deseas iniciar su devolución."
  );

  const confirmar = await mostrarConfirmacion(
    `El equipo ${data.codigo} está actualmente prestado a ${nombreEstudiante}.\n\n` +
    `¿Deseas recibir la devolución?`,
    { titulo: "Recibir devolución", textoAceptar: "Recibir equipo" }
  );

  if (!confirmar) {
    mostrarResultadoRFID(
      `Devolución cancelada. El equipo ${data.codigo} permanece prestado.`
    );

    actualizarEstadoRFID(
      "Devolución cancelada",
      "No se realizó ningún cambio en el equipo."
    );

    finalizarVistaSiNoHaySesion();
    return;
  }

  try {
    const devolucion = await peticionAPI("/devoluciones", "POST", {
      codigo_equipo: data.codigo,
    });

    abrirModalDevolucion(devolucion, "qr");

    actualizarEstadoRFID(
      "Devolución iniciada",
      "Confirma los accesorios y el estado en que se entrega el equipo."
    );
  } catch (error) {
    mostrarResultadoRFID(
      "No se pudo iniciar la devolución: " + (error.detail || "Error desconocido.")
    );

    actualizarEstadoRFID(
      "Error",
      "No se pudo iniciar la devolución."
    );

    finalizarVistaSiNoHaySesion();
  }
}

// ============================================================
// AGREGAR EQUIPO A LA VISTA
// ============================================================

function agregarEquipoOperacion(data) {
  equiposOperacion.push(data);

  const contenedor = document.getElementById("rfid-flow-equipos");
  const lista = document.getElementById("rfid-flow-equipo-list");

  if (!contenedor || !lista) {
    return;
  }

  contenedor.hidden = false;

  const STATUS_CLASSES_LOCAL = {
    Disponible: "status-available",
    Prestado: "status-loaned",
    "En revisión": "status-review",
  };

  lista.innerHTML = equiposOperacion
    .map((equipo) => {
      const statusClass = STATUS_CLASSES_LOCAL[equipo.estado] || "status-available";

      return `
        <div class="equipo-operacion-row">
          <div>
            <div class="info-item-label">Equipo</div>
            <div class="operation-student-name">${equipo.codigo || "—"}</div>
          </div>
          <div>
            <div class="info-item-label">Tipo</div>
            <div class="operation-student-data">${equipo.tipo || "—"}</div>
          </div>
          <div>
            <span class="status ${statusClass}">
              <span class="status-dot"></span>
              ${equipo.estado || "—"}
            </span>
          </div>
        </div>
      `;
    })
    .join("");
}

// ============================================================
// SELECCIÓN DE ESTUDIANTE
// ============================================================

async function seleccionarEstudianteYPrestar(data) {
  const estudiantes = data.estudiantes || [];

  if (
    sesionActual &&
    estudiantes.some(
      (e) => e.matricula === sesionActual.matricula
    )
  ) {
    const confirmar = await mostrarConfirmacion(
      `El equipo ${data.codigo} está disponible.\n\n` +
      `¿Deseas prestarlo a ${sesionActual.nombre} (${sesionActual.matricula})?`,
      { titulo: "Confirmar préstamo", textoAceptar: "Prestar equipo" }
    );

    if (!confirmar) {
      mostrarResultadoRFID("Préstamo cancelado. No se realizó ningún cambio.");
      return;
    }

    await registrarPrestamo(sesionActual.sesion_id, data);
    return;
  }

  const elegido = await mostrarSeleccionEstudiante(estudiantes);

  if (!elegido) {
    mostrarResultadoRFID("No se seleccionó ningún estudiante. No se registró el préstamo.");
    return;
  }

  const confirmar = await mostrarConfirmacion(
    `Equipo: ${data.codigo}\n` +
    `Estudiante: ${elegido.nombre}\n` +
    `Matrícula: ${elegido.matricula}\n\n` +
    `¿Deseas registrar el préstamo?`,
    { titulo: "Confirmar préstamo", textoAceptar: "Registrar préstamo" }
  );

  if (!confirmar) {
    mostrarResultadoRFID("Préstamo cancelado. No se realizó ningún cambio.");
    return;
  }

  try {
    const sesion = await peticionAPI(
      `/sesiones/activa?matricula=${encodeURIComponent(elegido.matricula)}`
    );

    await registrarPrestamo(sesion.sesion_id, data);
  } catch (error) {
    mostrarResultadoRFID(
      "Error al consultar la sesión: " + (error.detail || "desconocido")
    );
  }
}

// ============================================================
// REGISTRAR PRÉSTAMO
// ============================================================

async function registrarPrestamo(sesionId, dataEquipo) {
  try {
    const resultado = await peticionAPI("/equipos/prestar", "POST", {
      sesion_id: sesionId,
      equipo_id: dataEquipo.equipo_id,
      accesorios: [],
    });

    agregarEquipoOperacion({
      codigo: resultado.codigo_equipo || dataEquipo.codigo,
      tipo: dataEquipo.tipo,
      estado: "Prestado",
      equipo_id: dataEquipo.equipo_id,
      accion: "prestamo_confirmado",
    });

    mostrarResultadoRFID(
      `Préstamo registrado: ${resultado.codigo_equipo}. ` +
      `${resultado.mensaje || "Préstamo registrado correctamente."}`
    );

    actualizarEstadoRFID(
      "Préstamo registrado",
      "El equipo fue agregado a la sesión."
    );

    await cargarEquiposDesdeAPI();
  } catch (error) {
    mostrarResultadoRFID(
      "Error al registrar el préstamo: " + (error.detail || "No se pudo procesar.")
    );
  }
}

// ============================================================
// CANCELAR FLUJO RFID
// ============================================================

async function cancelarFlujoRFID() {
  const confirmar = await mostrarConfirmacion(
    "¿Deseas cancelar la operación RFID actual?",
    { titulo: "Cancelar operación", textoAceptar: "Sí, cancelar", peligro: true }
  );

  if (!confirmar) {
    return;
  }

  sesionActual = null;
  equiposOperacion = [];
  devolucionActual = null;
  inicioOperacionRFID = null;

  const estudiante = document.getElementById("rfid-flow-estudiante");
  const esperando = document.getElementById("rfid-flow-esperando-qr");
  const equipos = document.getElementById("rfid-flow-equipos");
  const resultado = document.getElementById("rfid-flow-resultado");
  const lista = document.getElementById("rfid-flow-equipo-list");
  const botonTerminar = document.getElementById("btn-terminar-operacion");

  if (estudiante) estudiante.hidden = true;
  if (esperando) esperando.hidden = true;
  if (equipos) equipos.hidden = true;
  if (resultado) resultado.innerHTML = "";
  if (lista) lista.innerHTML = "";
  if (botonTerminar) botonTerminar.style.display = "none";

  regresarDesdePrestamoRFID();
}

// ============================================================
// LIMPIAR VISTA CUANDO NO HAY SESIÓN DE PRÉSTAMO ACTIVA
// ============================================================

function finalizarVistaSiNoHaySesion() {
  if (sesionActual) {
    return;
  }

  setTimeout(() => {
    inicioOperacionRFID = null;

    const estudiante = document.getElementById("rfid-flow-estudiante");
    const esperando = document.getElementById("rfid-flow-esperando-qr");
    const equipos = document.getElementById("rfid-flow-equipos");
    const resultado = document.getElementById("rfid-flow-resultado");
    const lista = document.getElementById("rfid-flow-equipo-list");
    const botonTerminar = document.getElementById("btn-terminar-operacion");

    if (estudiante) estudiante.hidden = true;
    if (esperando) esperando.hidden = true;
    if (equipos) equipos.hidden = true;
    if (resultado) resultado.innerHTML = "";
    if (lista) lista.innerHTML = "";
    if (botonTerminar) botonTerminar.style.display = "none";

    regresarDesdePrestamoRFID();
  }, 1800);
}

// ============================================================
// ENROLAMIENTO RFID
// ============================================================

function abrirEnrolamientoRFID(uid) {
  uidPendienteEnrolar = uid;

  const inputUid = document.getElementById("enrolar-rfid-uid");
  const inputMatricula = document.getElementById("input-enrolar-matricula");
  const resultado = document.getElementById("enrolar-rfid-resultado");

  if (inputUid) inputUid.value = uid;
  if (inputMatricula) inputMatricula.value = "";
  if (resultado) resultado.innerHTML = "";

  openModal("enrolar-rfid-modal");

  setTimeout(() => {
    if (inputMatricula) inputMatricula.focus();
  }, 100);
}

async function confirmarEnrolamientoRFID() {
  const matricula = document.getElementById("input-enrolar-matricula").value.trim();
  const resultado = document.getElementById("enrolar-rfid-resultado");

  if (!matricula) {
    if (resultado) {
      resultado.textContent = "Ingresa la matrícula del estudiante.";
    }
    return;
  }

  await enrolarRFID(uidPendienteEnrolar, matricula);
  closeModal("enrolar-rfid-modal");
}

// ============================================================
// ENROLAR RFID
// ============================================================

async function enrolarRFID(uid, matricula) {
  try {
    const data = await peticionAPI("/identificaciones/enrolar", "POST", {
      tipo: "rfid",
      valor: uid,
      matricula,
    });

    const vistaActual = obtenerVistaActiva();

    if (vistaActual !== "prestamo-rfid") {
      abrirVistaPrestamoRFID();
    }

    mostrarResultadoRFID(`RFID enrolado a ${data.nombre} (${data.matricula}).`);
  } catch (error) {
    mostrarResultadoRFID("Error al enrolar: " + (error.detail || "desconocido"));
  }
}

// ============================================================
// INICIALIZAR ESTADO DEL ÚLTIMO SCAN
// ============================================================

async function inicializarPollingScan() {
  try {
    const evento = await peticionAPI("/identificaciones/ultimo-scan");

    if (evento.timestamp) {
      ultimoScanVisto = evento.timestamp;
      localStorage.setItem(STORAGE_ULTIMO_SCAN, evento.timestamp);
    }

    pollingInicializado = true;
  } catch (error) {
    pollingInicializado = true;
  }
}

// ============================================================
// POLLING DE ESCANEOS EN VIVO
// ============================================================

async function revisarUltimoScan() {
  try {
    const evento = await peticionAPI("/identificaciones/ultimo-scan");

    if (!evento.timestamp) {
      return;
    }

    if (!ultimoScanVisto) {
      ultimoScanVisto = localStorage.getItem(STORAGE_ULTIMO_SCAN);
    }

    if (!pollingInicializado) {
      ultimoScanVisto = evento.timestamp;
      localStorage.setItem(STORAGE_ULTIMO_SCAN, evento.timestamp);
      pollingInicializado = true;
      return;
    }

    if (evento.timestamp === ultimoScanVisto) {
      return;
    }

    ultimoScanVisto = evento.timestamp;
    localStorage.setItem(STORAGE_ULTIMO_SCAN, evento.timestamp);

    if (evento.tipo === "rfid") {
      await manejarRespuestaRFID(evento.datos.uid_rfid, evento.datos);
      return;
    }

    if (evento.tipo === "qr") {
      if (!inicioOperacionRFID) {
        await manejarRespuestaQR(evento.datos);
        return;
      }

      const timestampQR = new Date(evento.timestamp).getTime();
      const timestampRFID = new Date(inicioOperacionRFID).getTime();

      if (!Number.isNaN(timestampQR) && !Number.isNaN(timestampRFID) && timestampQR > timestampRFID) {
        await manejarRespuestaQR(evento.datos);
      }
    }
  } catch (error) {
    // El polling debe ser silencioso.
  }
}

// ============================================================
// TERMINAR OPERACIÓN
// ============================================================

async function terminarOperacion() {
  const confirmar = await mostrarConfirmacion(
    "¿Deseas dar por terminada la operación? Se cerrará la sesión activa de la interfaz.",
    { titulo: "Terminar operación", textoAceptar: "Terminar" }
  );

  if (!confirmar) {
    return;
  }

  mostrarResultadoRFID("Operación terminada con éxito. Se puede retirar la credencial.");
  actualizarEstadoRFID("Finalizado", "Listo para el siguiente estudiante.");

  const botonTerminar = document.getElementById("btn-terminar-operacion");

  if (botonTerminar) {
    botonTerminar.style.display = "none";
  }

  setTimeout(() => {
    sesionActual = null;
    equiposOperacion = [];
    devolucionActual = null;
    inicioOperacionRFID = null;

    const estudiante = document.getElementById("rfid-flow-estudiante");
    const esperando = document.getElementById("rfid-flow-esperando-qr");
    const equipos = document.getElementById("rfid-flow-equipos");
    const resultado = document.getElementById("rfid-flow-resultado");
    const lista = document.getElementById("rfid-flow-equipo-list");

    if (estudiante) estudiante.hidden = true;
    if (esperando) esperando.hidden = true;
    if (equipos) equipos.hidden = true;
    if (resultado) resultado.innerHTML = "";
    if (lista) lista.innerHTML = "";

    regresarDesdePrestamoRFID();
  }, 2000);
}

// ============================================================
// INICIAR POLLING
// ============================================================

inicializarPollingScan();
setInterval(revisarUltimoScan, 2500);