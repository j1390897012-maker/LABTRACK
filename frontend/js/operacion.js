let sesionActual = null; // { sesion_id, matricula, nombre }

function mostrarResultadoOperacion(texto) {
  const el = document.getElementById("operacion-resultado");
  if (el) el.textContent = texto;
}

function mostrarPanelSesion(nombre, matricula) {
  const panel = document.getElementById("panel-sesion-activa");
  const texto = document.getElementById("sesion-activa-texto");
  if (texto) {
    texto.textContent = `${nombre} (${matricula}) — Siguiente paso: Escanear QR del equipo.`;
  }
  if (panel) panel.hidden = false;
}

async function simularRFID() {
  const uid = prompt("UID de la tarjeta RFID:");
  if (!uid) return;
  await procesarScan("rfid", uid);
}

async function simularQR() {
  const codigo = prompt("Código QR del equipo:");
  if (!codigo) return;
  await procesarScan("qr", codigo);
}

async function procesarScan(tipo, valor) {
  try {
    const data = await peticionAPI("/identificaciones/scan", "POST", { tipo, valor });

    if (tipo === "rfid") {
      if (data.estado === "no_registrado") {
        if (confirm("Tarjeta no registrada. ¿Enrolarla a un estudiante?")) {
          const matricula = prompt("Matrícula del estudiante:");
          if (matricula) await enrolarRFID(valor, matricula);
        }
        return;
      }

      // "registrado": el backend ya abrió o reutilizó la sesión
      // internamente (accion = "sesion_abierta" | "sesion_continuada").
      // El frontend solo refleja ese estado, no decide nada.
      sesionActual = {
        sesion_id: data.sesion_id,
        matricula: data.matricula,
        nombre: data.nombre,
      };
      mostrarPanelSesion(data.nombre, data.matricula);
      mostrarResultadoOperacion(`${data.nombre} (${data.matricula}) — ${data.mensaje}`);
      return;
    }

    if (tipo === "qr") {
      await manejarRespuestaQR(data);
    }
  } catch (error) {
    mostrarResultadoOperacion("Error: " + (error.detail || "no se pudo procesar."));
  }
}

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
    const esSesionActual =
      sesionActual && estudiantes.some((e) => e.matricula === sesionActual.matricula);

    if (esSesionActual) {
      await registrarPrestamo(sesionActual.sesion_id, data);
    } else {
      // No hay una sesión local que coincida (p. ej. se escaneó el QR
      // sin pasar antes por RFID). Se conserva el comportamiento actual:
      // solo informar, sin prestar automáticamente.
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

  // Si el estudiante de la sesión activa local ya está entre las
  // opciones, se usa directamente sin volver a preguntar.
  if (sesionActual && estudiantes.some((e) => e.matricula === sesionActual.matricula)) {
    await registrarPrestamo(sesionActual.sesion_id, data);
    return;
  }

  // Caso de excepción real: varias sesiones activas y ninguna coincide
  // con la identificada localmente. El encargado elige.
  const opciones = estudiantes
    .map((e, i) => `${i + 1}. ${e.nombre} (${e.matricula})`)
    .join("\n");
  const seleccion = prompt(`Varias sesiones activas. Elige el número del estudiante:\n${opciones}`);
  const elegido = estudiantes[Number(seleccion) - 1];

  if (!elegido) {
    mostrarResultadoOperacion("Selección inválida. No se registró el préstamo.");
    return;
  }

  try {
    const sesion = await peticionAPI(
      `/sesiones/activa?matricula=${encodeURIComponent(elegido.matricula)}`
    );
    await registrarPrestamo(sesion.sesion_id, data);
  } catch (error) {
    mostrarResultadoOperacion(
      "Error al consultar la sesión del estudiante seleccionado: " + (error.detail || "desconocido")
    );
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

    // La sesión sigue activa: se puede escanear otro equipo.
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
