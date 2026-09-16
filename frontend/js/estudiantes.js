let estudiantesCache = [];
let estudianteEditandoId = null;
let estudianteDetalleActual = null;

// ============================================================
// GUARDAR (crear o editar, según estudianteEditandoId)
// ============================================================

async function guardarEstudiante() {
  const nombre = document.getElementById("input-estudiante-nombre").value;
  const matricula = document.getElementById("input-estudiante-matricula").value;

  if (!nombre || !matricula) return alert("Completa todos los campos.");

  const esEdicion = estudianteEditandoId !== null;
  const endpoint = esEdicion
    ? `/estudiantes/${estudianteEditandoId}`
    : `/estudiantes`;

  try {
    await peticionAPI(endpoint, esEdicion ? "PUT" : "POST", { nombre, matricula });

    closeModal("student-modal");
    document.getElementById("input-estudiante-nombre").value = "";
    document.getElementById("input-estudiante-matricula").value = "";
    estudianteEditandoId = null;
    cargarEstudiantesDesdeAPI();
  } catch (error) {
    alert("Error: " + (error.detail || "No se pudo guardar."));
  }
}

// ============================================================
// ABRIR MODAL DE REGISTRO / EDICIÓN
// ============================================================

function abrirModalNuevoEstudiante() {
  estudianteEditandoId = null;
  document.getElementById("input-estudiante-nombre").value = "";
  document.getElementById("input-estudiante-matricula").value = "";

  const header = document.querySelector("#student-modal .modal-header h2");
  if (header) header.textContent = "Registrar estudiante";

  openModal("student-modal");
}

function abrirModalEditarEstudiante() {
  if (!estudianteDetalleActual) return;

  estudianteEditandoId = estudianteDetalleActual.id;
  document.getElementById("input-estudiante-nombre").value = estudianteDetalleActual.nombre;
  document.getElementById("input-estudiante-matricula").value = estudianteDetalleActual.matricula;

  const header = document.querySelector("#student-modal .modal-header h2");
  if (header) header.textContent = "Editar estudiante";

  closeModal("detalle-estudiante-modal");
  openModal("student-modal");
}

// ============================================================
// LISTADO
// ============================================================

async function cargarEstudiantesDesdeAPI() {
  try {
    const estudiantes = await peticionAPI("/estudiantes");
    estudiantesCache = estudiantes;

    const tbody = document.getElementById("student-table");
    tbody.innerHTML = "";

    // Consultamos en paralelo si cada estudiante tiene sesión activa
    const estados = await Promise.all(
      estudiantes.map(async (est) => {
        try {
          await peticionAPI(`/sesiones/activa?matricula=${encodeURIComponent(est.matricula)}`);
          return true;
        } catch (e) {
          // 404 = no tiene sesión activa; se trata como "Inactiva".
          return false;
        }
      })
    );

    estudiantes.forEach((est, i) => {
      const tr = document.createElement("tr");
      tr.dataset.student = `${est.nombre} ${est.matricula}`.toLowerCase();

      const rfidBadge = est.uid_rfid
        ? `<span class="rfid-badge">RFID registrado</span>`
        : `<span class="rfid-badge rfid-missing" style="background: var(--warning-soft); color: var(--warning);">Sin RFID</span>`;

      const iniciales = est.nombre.substring(0, 2).toUpperCase();

      const tieneSesionActiva = estados[i];
      const sesionBadge = tieneSesionActiva
        ? `<span class="status status-available"><span class="status-dot"></span>Activa</span>`
        : `<span class="status" style="background: var(--bg-secondary, #f1f5f9); color: var(--muted, #64748b);"><span class="status-dot" style="background: var(--muted, #64748b);"></span>Inactiva</span>`;

      tr.innerHTML = `
        <td>
          <div class="student-card">
            <div class="avatar">${iniciales}</div>
            <div><div class="student-name">${est.nombre}</div></div>
          </div>
        </td>
        <td class="code">${est.matricula}</td>
        <td>${rfidBadge}</td>
        <td>${sesionBadge}</td>
        <td><button class="button button-secondary button-small" onclick="abrirDetalleEstudiante(${est.id})">Ver estudiante</button></td>
      `;
      tbody.appendChild(tr);
    });
  } catch (error) {
    console.error("Error cargando estudiantes:", error);
  }
}

function filterStudents() {
  const search = document.getElementById("student-search").value.toLowerCase();
  const rows = document.querySelectorAll("#student-table tr");

  rows.forEach(row => {
    const studentData = row.dataset.student || "";
    row.style.display = studentData.includes(search) ? "" : "none";
  });
}

// ============================================================
// DETALLE DEL ESTUDIANTE (RFID/matrícula + historial)
// ============================================================

async function abrirDetalleEstudiante(id) {
  const estudiante = estudiantesCache.find(e => e.id === id);

  if (!estudiante) {
    alert("No se encontró la información del estudiante.");
    return;
  }

  estudianteDetalleActual = estudiante;

  document.getElementById("detalle-estudiante-nombre").textContent = estudiante.nombre;
  document.getElementById("detalle-estudiante-matricula").textContent = estudiante.matricula;
  document.getElementById("detalle-estudiante-rfid").textContent = estudiante.uid_rfid || "Sin RFID registrado";
  document.getElementById("detalle-estudiante-sesion").textContent = "Cargando...";
  document.getElementById("detalle-estudiante-equipos").innerHTML = `<p class="card-subtitle">Cargando equipos...</p>`;
  document.getElementById("detalle-estudiante-historial").innerHTML = `<p class="card-subtitle">Cargando historial...</p>`;

  openModal("detalle-estudiante-modal");

  try {
    const data = await peticionAPI(`/estudiantes/${id}/historial`);
    pintarDetalleEstudiante(data);
  } catch (error) {
    console.error("Error al cargar historial del estudiante:", error);
    document.getElementById("detalle-estudiante-sesion").textContent = "Sin sesión activa";
    document.getElementById("detalle-estudiante-equipos").innerHTML = `<p class="card-subtitle">No se pudo cargar la información.</p>`;
    document.getElementById("detalle-estudiante-historial").innerHTML = `<p class="card-subtitle">No se pudo cargar el historial.</p>`;
  }
}

function pintarDetalleEstudiante(data) {
  const sesiones = data.sesiones || [];
  const sesionActiva = sesiones.find((s) => {
  if (typeof s.estado === "string") {
    return s.estado !== "Cerrada";
  }
  return !s.fecha_cierre;
});

  const sesionEl = document.getElementById("detalle-estudiante-sesion");
  if (sesionEl) {
    sesionEl.textContent = sesionActiva
      ? `Sesión #${sesionActiva.sesion_id} (activa)`
      : "Sin sesión activa";
  }

  const equiposEl = document.getElementById("detalle-estudiante-equipos");
  if (equiposEl) {
    const equiposActuales = sesionActiva
      ? (sesionActiva.equipos || []).filter(e => !e.fecha_devolucion)
      : [];

    equiposEl.innerHTML = equiposActuales.length
      ? equiposActuales
          .map(
            (e) => `
              <div class="equipo-operacion-row">
                <div>
                  <div class="info-item-label">Equipo</div>
                  <div class="operation-student-name">${e.codigo}</div>
                </div>
                <div>
                  <div class="info-item-label">Tipo</div>
                  <div class="operation-student-data">${e.tipo || "—"}</div>
                </div>
              </div>
            `
          )
          .join("")
      : `<p class="card-subtitle">Sin equipos prestados actualmente.</p>`;
  }

  // ============================================================
  // NUEVA LÓGICA DE RENDERIZADO DEL HISTORIAL VERTICAL
  // ============================================================
  const historialEl = document.getElementById("detalle-estudiante-historial");
  if (historialEl) {
    if (sesiones.length === 0) {
      historialEl.innerHTML = `<p class="card-subtitle">Sin historial registrado.</p>`;
    } else {
      historialEl.innerHTML = sesiones
        .slice()
        .reverse()
        .map((s) => {
          // Formateo correcto de fecha UTC a hora local (igual que en historial.js)
          const fechaFija = s.fecha_apertura.endsWith("Z") ? s.fecha_apertura : s.fecha_apertura + "Z";
          const fechaObj = new Date(fechaFija);
          const fechaFormat = fechaObj.toLocaleDateString('es-MX', { month: 'short', day: 'numeric' });
          const horaFormat = fechaObj.toLocaleTimeString('es-MX', { hour: '2-digit', minute: '2-digit' });
          
          const estadoSesion = s.fecha_cierre ? "Cerrada" : "Activa";
          const colorEstadoSesion = s.fecha_cierre ? "var(--muted)" : "var(--primary, #3b82f6)";

          // Iterar los equipos de esta sesión en formato de lista vertical
          let equiposHTML = "";
          if (s.equipos && s.equipos.length > 0) {
            equiposHTML = s.equipos.map(e => {
              const esDevuelto = e.estado_prestamo === "Devuelto";
              const tipoEvento = esDevuelto ? "Devolución" : "Préstamo";
              
              // Colores de los badges
              const badgeColor = esDevuelto ? "var(--success)" : "var(--warning)";
              const colorBg = esDevuelto ? "var(--success-light, #d1fae5)" : "var(--warning-light, #fef3c7)";

              return `
                <div class="history-item" style="display: flex; align-items: flex-start; gap: 16px; padding: 12px 0; border-bottom: 1px solid var(--border-color, #e2e8f0); margin-left: 12px;">
                  <div style="flex: 1;">
                    <div class="history-main" style="color: var(--text); font-weight: 500; font-size: 14px;">
                      ${tipoEvento} de <strong>${e.codigo}</strong>
                    </div>
                    <div class="history-secondary" style="color: var(--muted); font-size: 12px; margin-top: 4px;">
                      Tipo: ${e.tipo || "No especificado"}
                    </div>
                  </div>
                  <span class="history-type" style="background-color: ${colorBg}; color: ${badgeColor}; padding: 4px 8px; border-radius: 99px; font-size: 11px; font-weight: 600;">
                    ${e.estado_prestamo}
                  </span>
                </div>
              `;
            }).join("");
          } else {
            equiposHTML = `<div style="font-size: 13px; color: var(--muted); padding: 12px;">Sin operaciones en esta sesión.</div>`;
          }

          // Envoltura de la sesión agrupando sus equipos
          return `
            <div style="margin-bottom: 24px;">
              <div style="display: flex; align-items: center; gap: 16px; padding-bottom: 12px; border-bottom: 2px solid var(--border-color, #e2e8f0);">
                <div class="history-date" style="min-width: 60px; text-align: center; color: var(--muted); font-size: 13px; font-weight: 600;">
                  ${fechaFormat}<br>
                  <span style="font-weight: 400; font-size: 11px;">${horaFormat}</span>
                </div>
                <div style="flex: 1;">
                  <div style="font-weight: 600; font-size: 15px; color: var(--text);">Sesión #${s.sesion_id}</div>
                  <div style="font-size: 12px; color: ${colorEstadoSesion}; font-weight: 500;">${estadoSesion}</div>
                </div>
              </div>
              <div class="sesion-equipos-lista">
                ${equiposHTML}
              </div>
            </div>
          `;
        })
        .join("");
    }
  }
}

// ============================================================
// ELIMINAR
// ============================================================

async function eliminarEstudianteDesdeDetalle() {
  if (!estudianteDetalleActual) return;

  const confirmar = await mostrarConfirmacion(
    `¿Deseas eliminar a ${estudianteDetalleActual.nombre} (${estudianteDetalleActual.matricula})?\n\nEsta acción no se puede deshacer.`,
    { titulo: "Eliminar estudiante", textoAceptar: "Eliminar", peligro: true }
  );

  if (!confirmar) return;

  try {
    await peticionAPI(`/estudiantes/${estudianteDetalleActual.id}`, "DELETE");

    closeModal("detalle-estudiante-modal");
    estudianteDetalleActual = null;
    cargarEstudiantesDesdeAPI();
  } catch (error) {
    if (error.status === 409) {
      alert("No se puede eliminar: el estudiante ya tiene historial de préstamos registrado.");
      return;
    }

    alert("Error: " + (error.detail || "No se pudo eliminar al estudiante."));
  }
}

document.addEventListener("DOMContentLoaded", () => {
  if (document.getElementById("student-table")) {
    cargarEstudiantesDesdeAPI();
  }
});