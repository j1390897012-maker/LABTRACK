// ============================================================
// ESTADO DEL FLUJO RFID / QR
// ============================================================

let sesionActual = null;
let equiposOperacion = [];
let ultimoScanVisto = null;
let uidPendienteEnrolar = null;

// Información de la devolución actualmente en curso.
let devolucionActual = null;

// Indica si ya sincronizamos el último scan existente al cargar.
let pollingInicializado = false;

const STORAGE_ULTIMO_SCAN = "labtrack_ultimo_scan";

// ============================================================
// OPERACIÓN MANUAL
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

    const respuesta = await peticionAPI(`/sesiones/${sesion.sesion_id}/equipos`, "POST", {
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
// INICIAR DEVOLUCIÓN MANUAL
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
    // IMPORTANTE: El encargado solamente proporciona codigo_equipo.
    // El backend resuelve internamente el equipo_id.
    const respuesta = await peticionAPI("/devoluciones", "POST", { codigo_equipo: codigo });

    devolucionActual = respuesta;

    // Procesar accesorios y posteriormente la falla/estado.
    await completarDevolucion(respuesta);

    document.getElementById("manual-devolucion-codigo").value = "";

    resultado.innerHTML = `
      <div class="card stat-card" style="border-left: 4px solid var(--success);">
        <div class="stat-label">Devolución procesada</div>
        <div class="stat-description" style="color: var(--text);">
          ${respuesta.mensaje || "La devolución fue procesada correctamente."}
        </div>
      </div>
    `;

    await cargarEquiposDesdeAPI();
    devolucionActual = null;

  } catch (error) {
    resultado.innerHTML = `
      <div class="card stat-card" style="border-left: 4px solid var(--danger);">
        <div class="stat-label">No se pudo procesar la devolución</div>
        <div class="stat-description" style="color: var(--text);">
          ${error.detail || "Ocurrió un error."}
        </div>
      </div>
    `;
  }
}

// ============================================================
// COMPLETAR DEVOLUCIÓN
// ============================================================

async function completarDevolucion(datosDevolucion) {
  const sesionEquipoId = datosDevolucion.sesion_equipo_id;
  const accesorios = datosDevolucion.accesorios || [];

  // 1. Registrar accesorios
  const accesoriosDevueltos = [];

  for (const accesorio of accesorios) {
    const cantidadTexto = prompt(
      `Devolución de accesorios\n\n${accesorio.nombre}\nCantidad prestada: ${accesorio.cantidad_prestada}\n\n¿Cuántas unidades se devuelven?`,
      String(accesorio.cantidad_prestada)
    );

    if (cantidadTexto === null) {
      throw { detail: "La devolución fue cancelada durante el registro de accesorios." };
    }

    const cantidad = Number(cantidadTexto);

    if (!Number.isInteger(cantidad) || cantidad < 0 || cantidad > accesorio.cantidad_prestada) {
      throw { detail: `Cantidad inválida para ${accesorio.nombre}. Debe estar entre 0 y ${accesorio.cantidad_prestada}.` };
    }

    accesoriosDevueltos.push({
      tipo_accesorio_id: accesorio.tipo_accesorio_id,
      cantidad_devuelta: cantidad,
    });
  }

  await peticionAPI("/devoluciones/accesorios", "POST", {
    sesion_equipo_id: sesionEquipoId,
    accesorios: accesoriosDevueltos,
  });

  // 2. Determinar si hubo falla
  const huboFalla = confirm(`¿Se detectó una falla o incidencia en ${datosDevolucion.codigo_equipo}?`);
  let descripcion = null;

  if (huboFalla) {
    descripcion = prompt("Describe la falla o incidencia detectada:");
    if (!descripcion || !descripcion.trim()) {
      throw { detail: "Debes proporcionar una descripción de la falla." };
    }
    descripcion = descripcion.trim();
  }

  // 3. Registrar resultado de la devolución
  const resultadoFalla = await peticionAPI(`/devoluciones/${sesionEquipoId}/falla`, "PATCH", {
    hubo_falla: huboFalla,
    descripcion: descripcion,
  });

  // Mostrar el resultado real informado por backend.
  mostrarResultadoRFID(resultadoFalla.mensaje || `Devolución de ${datosDevolucion.codigo_equipo} procesada.`);
  actualizarEstadoRFID(
    huboFalla ? "Equipo en revisión" : "Devolución registrada",
    huboFalla ? "El equipo quedó marcado para revisión." : "El equipo quedó disponible."
  );

  agregarEquipoOperacion({
    codigo: datosDevolucion.codigo_equipo,
    tipo: "Devuelto",
    estado: resultadoFalla.equipo_estado,
    equipo_id: datosDevolucion.equipo_id,
    accion: "devolucion_completada",
  });

  return resultadoFalla;
}

// ============================================================
// MODAL DE SIMULACIÓN RFID
// ============================================================

function simularRFID() {
  openModal("rfid-modal");
  setTimeout(() => {
    const input = document.getElementById("input-rfid-simulado");
    if (input) input.focus();
  }, 100);
}

async function procesarRFID() {
  const input = document.getElementById("input-rfid-simulado");
  const uid = input.value.trim();

  if (!uid) return;

  closeModal("rfid-modal");
  input.value = "";
  await procesarScan("rfid", uid);
}

// ============================================================
// PROCESAMIENTO DE SCAN
// ============================================================

async function procesarScan(tipo, valor) {
  try {
    const data = await peticionAPI("/identificaciones/scan", "POST", { tipo, valor });

    if (tipo === "rfid") {
      await manejarRespuestaRFID(valor, data);
      return;
    }

    if (tipo === "qr") {
      await manejarRespuestaQR(data);
    }
  } catch (error) {
    mostrarResultadoRFID("Error: " + (error.detail || "No se pudo procesar el escaneo."));
  }
}

// ============================================================
// RFID
// ============================================================

async function manejarRespuestaRFID(valor, data) {
  if (data.estado === "no_registrado") {
    abrirEnrolamientoRFID(valor);
    return;
  }

  sesionActual = {
    sesion_id: data.sesion_id,
    matricula: data.matricula,
    nombre: data.nombre,
  };

  equiposOperacion = [];

  abrirVistaPrestamoRFID();
  mostrarEstudianteRFID(data);
  actualizarEstadoRFID("RFID detectada", "Listo para prestar equipos.");

  const esperandoQR = document.getElementById("rfid-flow-esperando-qr");
  if (esperandoQR) esperandoQR.hidden = false;

  const botonTerminar = document.getElementById("btn-terminar-operacion");
  if (botonTerminar) botonTerminar.style.display = "block";

  mostrarResultadoRFID(`${data.nombre} (${data.matricula}) — ${data.mensaje || "Estudiante identificado correctamente."}`);
}

// ============================================================
// MOSTRAR ESTUDIANTE
// ============================================================

function mostrarEstudianteRFID(data) {
  const contenedor = document.getElementById("rfid-flow-estudiante");
  if (!contenedor) return;

  contenedor.hidden = false;

  const nombre = document.getElementById("rfid-flow-nombre");
  const matricula = document.getElementById("rfid-flow-matricula");
  const sesion = document.getElementById("rfid-flow-sesion");

  if (nombre) nombre.textContent = data.nombre || "—";
  if (matricula) matricula.textContent = data.matricula || "—";
  if (sesion) sesion.textContent = data.sesion_id ? `Sesión #${data.sesion_id}` : "Sin sesión";
}

// ============================================================
// ESTADO DE LA VISTA RFID
// ============================================================

function actualizarEstadoRFID(estado, subtitulo) {
  const badge = document.getElementById("rfid-flow-badge");
  const status = document.getElementById("rfid-flow-status");
  const subtitle = document.getElementById("rfid-flow-subtitle");

  if (badge) badge.innerHTML = `<span class="status-dot"></span> ${estado}`;
  if (status) status.textContent = subtitulo;
  if (subtitle) subtitle.textContent = subtitulo;
}

// ============================================================
// RESULTADO DEL FLUJO RFID
// ============================================================

function mostrarResultadoRFID(texto) {
  const el = document.getElementById("rfid-flow-resultado");
  if (!el) return;

  el.innerHTML = `
    <div class="card stat-card" style="border-left: 4px solid var(--primary); margin-top: 20px;">
      <div class="stat-description" style="color: var(--text); font-size: 14px;">
        ${texto}
      </div>
    </div>
  `;
}

// ============================================================
// QR
// ============================================================

async function manejarRespuestaQR(data) {
  // DEVOLUCIÓN
  if (data.accion === "iniciar_devolucion") {
    try {
      /*
       * El scan QR únicamente identifica/inicia el flujo.
       * Consultamos /devoluciones usando el código físico.
       * NO usamos equipo_id proporcionado por el usuario.
       */
      const devolucion = await peticionAPI("/devoluciones", "POST", { codigo_equipo: data.codigo });
      devolucionActual = devolucion;

      const codigoLabel = document.getElementById("devolucion-codigo-label");
      const codigoInput = document.getElementById("input-devolucion-codigo");
      const estadoInput = document.getElementById("input-devolucion-estado");
      const fallaInput = document.getElementById("input-devolucion-falla");
      const grupoFalla = document.getElementById("grupo-devolucion-falla");

      if (codigoLabel) codigoLabel.textContent = devolucion.codigo_equipo;
      if (codigoInput) codigoInput.value = devolucion.codigo_equipo;
      if (estadoInput) estadoInput.value = "Disponible";
      if (fallaInput) fallaInput.value = "";
      if (grupoFalla) grupoFalla.style.display = "none";

      openModal("devolucion-modal");
      actualizarEstadoRFID("Devolución detectada", "Confirma el estado en el que se entrega el equipo.");
    } catch (error) {
      mostrarResultadoRFID("No se pudo iniciar la devolución: " + (error.detail || "Error desconocido."));
    }
    return;
  }

  // EQUIPO EN REVISIÓN
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

  // CONFIRMAR PRÉSTAMO
  if (data.accion === "confirmar_prestamo") {
    const estudiantes = data.estudiantes || [];
    const esSesionActual = sesionActual && estudiantes.some((e) => e.matricula === sesionActual.matricula);

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

  // SELECCIONAR ESTUDIANTE
  if (data.accion === "seleccionar_estudiante") {
    await seleccionarEstudianteYPrestar(data);
    return;
  }

  // RESPUESTA GENÉRICA
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
// AGREGAR EQUIPO A LA VISTA
// ============================================================

function agregarEquipoOperacion(data) {
  equiposOperacion.push(data);

  const contenedor = document.getElementById("rfid-flow-equipos");
  const lista = document.getElementById("rfid-flow-equipo-list");

  if (!contenedor || !lista) return;

  contenedor.hidden = false;
  lista.innerHTML = equiposOperacion.map((equipo) => `
    <div class="operation-context" style="margin-bottom: 12px;">
      <div class="operation-context-header">
        <div>
          <div class="info-item-label">Equipo</div>
          <div class="operation-student-name">${equipo.codigo || "—"}</div>
        </div>
        <div>
          <div class="info-item-label">Tipo</div>
          <div class="operation-student-data">${equipo.tipo || "—"}</div>
        </div>
        <div>
          <div class="info-item-label">Estado</div>
          <div>${equipo.estado || "—"}</div>
        </div>
      </div>
    </div>
  `).join("");
}

// ============================================================
// SELECCIÓN DE ESTUDIANTE
// ============================================================

async function seleccionarEstudianteYPrestar(data) {
  const estudiantes = data.estudiantes || [];

  if (sesionActual && estudiantes.some((e) => e.matricula === sesionActual.matricula)) {
    await registrarPrestamo(sesionActual.sesion_id, data);
    return;
  }

  const opciones = estudiantes.map((e, i) => `${i + 1}. ${e.nombre} (${e.matricula})`).join("\n");
  const seleccion = prompt(`Varias sesiones activas. Elige el número del estudiante:\n${opciones}`);
  const elegido = estudiantes[Number(seleccion) - 1];

  if (!elegido) {
    mostrarResultadoRFID("Selección inválida. No se registró el préstamo.");
    return;
  }

  try {
    const sesion = await peticionAPI(`/sesiones/activa?matricula=${encodeURIComponent(elegido.matricula)}`);
    await registrarPrestamo(sesion.sesion_id, data);
  } catch (error) {
    mostrarResultadoRFID("Error al consultar la sesión: " + (error.detail || "desconocido"));
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

    mostrarResultadoRFID(`Préstamo registrado: ${resultado.codigo_equipo}. ${resultado.mensaje || "Préstamo registrado correctamente."}`);
    actualizarEstadoRFID("Préstamo registrado", "El equipo fue agregado a la sesión.");
    await cargarEquiposDesdeAPI();
  } catch (error) {
    mostrarResultadoRFID("Error al registrar el préstamo: " + (error.detail || "No se pudo procesar."));
  }
}

// ============================================================
// CANCELAR FLUJO RFID
// ============================================================

function cancelarFlujoRFID() {
  if (!confirm("¿Deseas cancelar la operación RFID actual?")) return;

  sesionActual = null;
  equiposOperacion = [];
  devolucionActual = null;

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
    if (resultado) resultado.textContent = "Ingresa la matrícula del estudiante.";
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
    const data = await peticionAPI("/identificaciones/enrolar", "POST", { tipo: "rfid", valor: uid, matricula });
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
    // El siguiente polling intentará nuevamente.
    pollingInicializado = true;
  }
}

// ============================================================
// POLLING DE ESCANEOS EN VIVO
// ============================================================

async function revisarUltimoScan() {
  try {
    const evento = await peticionAPI("/identificaciones/ultimo-scan");
    if (!evento.timestamp) return;
    
    if (!ultimoScanVisto) {
      ultimoScanVisto = localStorage.getItem(STORAGE_ULTIMO_SCAN);
    }

    // Primer ciclo: sincronizar el evento existente pero NO procesarlo.
    if (!pollingInicializado) {
      ultimoScanVisto = evento.timestamp;
      localStorage.setItem(STORAGE_ULTIMO_SCAN, evento.timestamp);
      pollingInicializado = true;
      return;
    }

    // Ya procesamos este scan.
    if (evento.timestamp === ultimoScanVisto) return;

    // Nuevo scan.
    ultimoScanVisto = evento.timestamp;
    localStorage.setItem(STORAGE_ULTIMO_SCAN, evento.timestamp);

    if (evento.tipo === "rfid") {
      await manejarRespuestaRFID(evento.datos.uid_rfid, evento.datos);
    } else if (evento.tipo === "qr") {
      await manejarRespuestaQR(evento.datos);
    }
  } catch (error) {
    // El polling debe ser silencioso.
  }
}

// ============================================================
// FUNCIONES DE DEVOLUCIÓN
// ============================================================

function toggleFallaDevolucion() {
  const estado = document.getElementById("input-devolucion-estado").value;
  const grupo = document.getElementById("grupo-devolucion-falla");
  
  if (grupo) {
    grupo.style.display = estado === "En revisión" ? "block" : "none";
  }
}

// ============================================================
// CONFIRMAR DEVOLUCIÓN DESDE MODAL QR
// ============================================================

async function confirmarDevolucion() {
  const codigo = document.getElementById("input-devolucion-codigo").value.trim();
  const estado = document.getElementById("input-devolucion-estado").value;
  const falla = document.getElementById("input-devolucion-falla").value.trim();

  if (!devolucionActual) {
    alert("No existe una devolución activa.");
    return;
  }

  if (estado === "En revisión" && !falla) {
    alert("Debes describir la falla o incidencia del equipo para ponerlo en revisión.");
    return;
  }

  try {
    // 1. Registrar accesorios
    const accesorios = devolucionActual.accesorios || [];
    const accesoriosDevueltos = [];

    for (const accesorio of accesorios) {
      const cantidadTexto = prompt(
        `Devolución de accesorios\n\n${accesorio.nombre}\nCantidad prestada: ${accesorio.cantidad_prestada}\n\n¿Cuántas unidades se devuelven?`,
        String(accesorio.cantidad_prestada)
      );

      if (cantidadTexto === null) return;

      const cantidad = Number(cantidadTexto);

      if (!Number.isInteger(cantidad) || cantidad < 0 || cantidad > accesorio.cantidad_prestada) {
        alert(`Cantidad inválida para ${accesorio.nombre}. Debe estar entre 0 y ${accesorio.cantidad_prestada}.`);
        return;
      }

      accesoriosDevueltos.push({
        tipo_accesorio_id: accesorio.tipo_accesorio_id,
        cantidad_devuelta: cantidad,
      });
    }

    await peticionAPI("/devoluciones/accesorios", "POST", {
      sesion_equipo_id: devolucionActual.sesion_equipo_id,
      accesorios: accesoriosDevueltos,
    });

    // 2. Registrar resultado de la falla
    const huboFalla = estado === "En revisión";
    const respuesta = await peticionAPI(`/devoluciones/${devolucionActual.sesion_equipo_id}/falla`, "PATCH", {
      hubo_falla: huboFalla,
      descripcion: huboFalla ? falla : null,
    });

    closeModal("devolucion-modal");

    agregarEquipoOperacion({
      codigo: devolucionActual.codigo_equipo || codigo,
      tipo: "Devuelto",
      estado: respuesta.equipo_estado,
      equipo_id: devolucionActual.equipo_id,
      accion: "devolucion_completada",
    });

    mostrarResultadoRFID(respuesta.mensaje || `Devolución de ${codigo} procesada correctamente.`);
    actualizarEstadoRFID(
      huboFalla ? "Equipo en revisión" : "Devolución registrada",
      huboFalla ? "El equipo quedó marcado para revisión." : "El equipo quedó disponible."
    );

    // Obtener el estado real del backend.
    await cargarEquiposDesdeAPI();
    devolucionActual = null;

  } catch (error) {
    alert("Error al procesar la devolución: " + (error.detail || "Error desconocido."));
  }
}

// ============================================================
// TERMINAR OPERACIÓN
// ============================================================

function terminarOperacion() {
  if (!confirm("¿Deseas dar por terminada la operación? Se cerrará la sesión activa de la interfaz.")) {
    return;
  }

  mostrarResultadoRFID("Operación terminada con éxito. Se puede retirar la credencial.");
  actualizarEstadoRFID("Finalizado", "Listo para el siguiente estudiante.");

  const botonTerminar = document.getElementById("btn-terminar-operacion");
  if (botonTerminar) botonTerminar.style.display = "none";

  setTimeout(() => {
    sesionActual = null;
    equiposOperacion = [];
    devolucionActual = null;

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

// Primero sincronizamos el último scan existente.
inicializarPollingScan();

// Después revisamos periódicamente si llegó un scan nuevo.
setInterval(revisarUltimoScan, 2500);