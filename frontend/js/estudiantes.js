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
  const url = esEdicion
    ? `${API_URL}/estudiantes/${estudianteEditandoId}`
    : `${API_URL}/estudiantes`;

  try {
    const response = await fetch(url, {
      method: esEdicion ? "PUT" : "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ nombre, matricula })
    });

    if (response.ok) {
      closeModal("student-modal");
      document.getElementById("input-estudiante-nombre").value = "";
      document.getElementById("input-estudiante-matricula").value = "";
      estudianteEditandoId = null;
      cargarEstudiantesDesdeAPI();
    } else {
      const error = await response.json().catch(() => ({}));
      alert("Error: " + (error.detail || "No se pudo guardar."));
    }
  } catch (e) {
    console.error("Error al guardar estudiante:", e);
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
    const response = await fetch(`${API_URL}/estudiantes`);
    if (!response.ok) throw new Error("Error al consultar API");

    const estudiantes = await response.json();
    estudiantesCache = estudiantes;

    const tbody = document.getElementById("student-table");
    tbody.innerHTML = "";

    // Consultamos en paralelo si cada estudiante tiene sesión activa
    const estados = await Promise.all(
      estudiantes.map(async (est) => {
        try {
          const r = await fetch(`${API_URL}/sesiones/activa?matricula=${encodeURIComponent(est.matricula)}`);
          return r.ok;
        } catch (e) {
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
    const response = await fetch(`${API_URL}/estudiantes/${id}/historial`);
    if (!response.ok) throw new Error("Error al consultar historial");

    const data = await response.json();
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
  const sesionActiva = sesiones.find(s => !s.fecha_cierre);

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
                  <div class="operation-student-data">${e.tipo}</div>
                </div>
              </div>
            `
          )
          .join("")
      : `<p class="card-subtitle">Sin equipos prestados actualmente.</p>`;
  }

  const historialEl = document.getElementById("detalle-estudiante-historial");
  if (historialEl) {
    if (sesiones.length === 0) {
      historialEl.innerHTML = `<p class="card-subtitle">Sin historial registrado.</p>`;
    } else {
      historialEl.innerHTML = sesiones
        .slice()
        .reverse()
        .map((s) => {
          const equiposTexto =
            (s.equipos || [])
              .map((e) => `${e.codigo} (${e.estado_prestamo})`)
              .join(", ") || "Sin equipos";

          return `
            <div class="history-item">
              <div class="info-item-label">
                Sesión #${s.sesion_id} — ${s.fecha_cierre ? "Cerrada" : "Activa"}
              </div>
              <div class="stat-description">${new Date(s.fecha_apertura).toLocaleString()}</div>
              <div class="stat-description">${equiposTexto}</div>
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
    const response = await fetch(`${API_URL}/estudiantes/${estudianteDetalleActual.id}`, {
      method: "DELETE",
    });

    if (response.status === 204) {
      closeModal("detalle-estudiante-modal");
      estudianteDetalleActual = null;
      cargarEstudiantesDesdeAPI();
      return;
    }

    if (response.status === 409) {
      alert("No se puede eliminar: el estudiante ya tiene historial de préstamos registrado.");
      return;
    }

    const error = await response.json().catch(() => ({}));
    alert("Error: " + (error.detail || "No se pudo eliminar al estudiante."));
  } catch (e) {
    console.error("Error al eliminar estudiante:", e);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  if (document.getElementById("student-table")) {
    cargarEstudiantesDesdeAPI();
  }
});