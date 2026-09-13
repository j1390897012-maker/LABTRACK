let sesionActual = null; // { sesion_id, matricula, nombre }

function mostrarResultadoOperacion(texto) {
  const el = document.getElementById("operacion-resultado");
  if (el) {
    el.innerHTML = `
      <div class="card stat-card" style="border-left: 4px solid var(--primary); margin-top: 20px;">
        <div class="stat-description" style="color: var(--text); font-size: 14px;">
          ${texto}
        </div>
      </div>
    `;
  }
}

function mostrarPanelSesion(nombre, matricula) {
  const panel = document.getElementById("panel-sesion-activa");
  const texto = document.getElementById("sesion-activa-texto");
  if (texto) {
    texto.textContent = `${nombre} (${matricula}) — Siguiente paso: Escanear QR del equipo.`;
  }
  if (panel) panel.hidden = false;
}

// Conexión con los Modales de UI
function simularRFID() {
  openModal('rfid-modal');
  setTimeout(() => document.getElementById("input-rfid-simulado").focus(), 100);
}

function simularQR() {
  openModal('qr-modal');
  setTimeout(() => document.getElementById("input-qr-simulado").focus(), 100);
}

async function procesarRFID() {
  const uid = document.getElementById("input-rfid-simulado").value.trim();
  if (!uid) return;
  closeModal('rfid-modal');
  document.getElementById("input-rfid-simulado").value = "";
  await procesarScan("rfid", uid);
}

async function procesarQR() {
  const codigo = document.getElementById("input-qr-simulado").value.trim();
  if (!codigo) return;
  closeModal('qr-modal');
  document.getElementById("input-qr-simulado").value = "";
  await procesarScan("qr", codigo);
}

// Tu lógica de negocio original
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
    mostrarResultadoOperacion("Error: " + (error.detail || "no se pudo procesar."));
  }
}

async function manejarRespuestaRFID(valor, data) {
  if (data.estado === "no_registrado") {
    const matricula = prompt("Tarjeta no registrada. Ingresa la matrícula para enrolarla:");
    if (matricula) await enrolarRFID(valor, matricula);
    return;
  }

  sesionActual = {
    sesion_id: data.sesion_id,
    matricula: data.matricula,
    nombre: data.nombre,
  };
  mostrarPanelSesion(data.nombre, data.matricula);
  mostrarResultadoOperacion(`${data.nombre} (${data.matricula}) — ${data.mensaje}`);
}

// --- Detectar escaneos que lleguen desde la app móvil (o Swagger) ---
let ultimoScanVisto = null;

async function revisarUltimoScan() {
  try {
    const evento = await peticionAPI("/identificaciones/ultimo-scan");
    if (!evento.timestamp || evento.timestamp === ultimoScanVisto) return;

    ultimoScanVisto = evento.timestamp;

    if (evento.tipo === "rfid") {
      await manejarRespuestaRFID(evento.datos.uid_rfid, evento.datos);
    } else if (evento.tipo === "qr") {
      await manejarRespuestaQR(evento.datos);
    }
  } catch (error) {
    // Silencioso: un fallo puntual de polling no debe interrumpir la interfaz.
  }
}

setInterval(revisarUltimoScan, 2500);

async function manejarRespuestaQR(data) {
  if (data.accion === "revisar_fallas") {
    const fallas = (data.fallas || []).map(f => f.descripcion).join("; ");
    mostrarResultadoOperacion(`${data.codigo} EN REVISIÓN — Fallas: ${fallas}`);
    return;
  }

  if (data.accion === "iniciar_devolucion") {
    mostrarResultadoOperacion(`${data.codigo}: préstamo activo de ${data.prestamo.estudiante.nombre}`);
    return;
  }

  if (data.accion === "confirmar_prestamo") {
    const estudiantes = data.estudiantes || [];
    const esSesionActual = sesionActual && estudiantes.some((e) => e.matricula === sesionActual.matricula);

    if (esSesionActual) {
      await registrarPrestamo(sesionActual.sesion_id, data);
    } else {
      mostrarResultadoOperacion(`${data.codigo}: ${data.mensaje}`);
    }
    return;
  }

  if (data.accion === "seleccionar_estudiante") {
    await seleccionarEstudianteYPrestar(data);
    return;
  }

  mostrarResultadoOperacion(`${data.codigo}: ${data.mensaje}`);
}

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
    mostrarResultadoOperacion("Selección inválida. No se registró el préstamo.");
    return;
  }

  try {
    const sesion = await peticionAPI(`/sesiones/activa?matricula=${encodeURIComponent(elegido.matricula)}`);
    await registrarPrestamo(sesion.sesion_id, data);
  } catch (error) {
    mostrarResultadoOperacion("Error al consultar la sesión: " + (error.detail || "desconocido"));
  }
}

async function registrarPrestamo(sesionId, dataEquipo) {
  try {
    const resultado = await peticionAPI("/equipos/prestar", "POST", {
      sesion_id: sesionId,
      equipo_id: dataEquipo.equipo_id,
      accesorios: [],
    });
    mostrarResultadoOperacion(`Préstamo registrado: ${resultado.codigo_equipo}. ${resultado.mensaje}`);

    if (sesionActual) {
      mostrarPanelSesion(sesionActual.nombre, sesionActual.matricula);
    }
  } catch (error) {
    mostrarResultadoOperacion("Error al registrar el préstamo: " + (error.detail || "no se pudo procesar."));
  }
}

async function enrolarRFID(uid, matricula) {
  try {
    const data = await peticionAPI("/identificaciones/enrolar", "POST", { tipo: "rfid", valor: uid, matricula });
    mostrarResultadoOperacion(`RFID enrolado a ${data.nombre} (${data.matricula}).`);
  } catch (error) {
    mostrarResultadoOperacion("Error al enrolar: " + (error.detail || "desconocido"));
  }
}