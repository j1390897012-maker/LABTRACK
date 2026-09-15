const STATUS_CLASSES = {
  "Disponible": "status-available",
  "Prestado": "status-loaned",
  "En revisión": "status-review",
  "Baja": "status-review" 
};

let equipoDetalleActual = null;

// ==========================================
// NOTIFICACIONES GLOBALES (TOAST)
// ==========================================
function mostrarMensajeEquipos(mensaje, tipo = "success") {
  let toastContainer = document.getElementById("toast-container");
  
  if (!toastContainer) {
    toastContainer = document.createElement("div");
    toastContainer.id = "toast-container";
    document.body.appendChild(toastContainer);
  }

  const alertaContenedor = document.createElement("div");
  alertaContenedor.className = "ui-alert-container";
  alertaContenedor.innerHTML = `
    <div class="ui-alert ui-alert-${tipo}">
      ${mensaje}
    </div>
  `;

  toastContainer.appendChild(alertaContenedor);

  setTimeout(() => {
    if (alertaContenedor.parentNode) {
      alertaContenedor.remove();
    }
  }, 4000);
}

// ==========================================
// REGISTRO DE EQUIPOS
// ==========================================
async function guardarEquipo() {
  const codigo = document.getElementById("input-equipo-codigo").value;
  const tipo = document.getElementById("input-equipo-tipo").value;

  if (!codigo || !tipo) return alert("Completa todos los campos.");

  try {
    const response = await fetch(`${API_URL}/equipos`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ codigo, tipo })
    });
    
    if (response.ok) {
      closeModal("equipo-modal");
      document.getElementById("input-equipo-codigo").value = "";
      document.getElementById("input-equipo-tipo").value = "";
      cargarEquiposDesdeAPI();
      mostrarMensajeEquipos(`El equipo ${codigo} fue registrado exitosamente.`, "success");
    } else {
      const error = await response.json();
      closeModal("equipo-modal");
      mostrarMensajeEquipos("Error: " + (error.detail || "No se pudo registrar el equipo"), "danger");
    }
  } catch (e) {
    console.error("Error al guardar equipo:", e);
    closeModal("equipo-modal");
    mostrarMensajeEquipos("Ocurrió un error en la conexión con el servidor.", "danger");
  }
}

// ==========================================
// CARGA Y RENDERIZADO DE INVENTARIO
// ==========================================
async function cargarEquiposDesdeAPI() {
  try {
    const response = await fetch(`${API_URL}/equipos`);
    if (!response.ok) throw new Error("Error al consultar API");
    
    const equipos = await response.json();
    const tbody = document.getElementById("equipment-table");
    tbody.innerHTML = ""; 

    let total = equipos.length;
    let disponibles = 0;
    let prestados = 0;
    let revision = 0;

    equipos.forEach(eq => {
      if (eq.estado === "Disponible") disponibles++;
      if (eq.estado === "Prestado") prestados++;
      if (eq.estado === "En revisión") revision++;

      const tr = document.createElement("tr");
      tr.dataset.code = eq.codigo.toLowerCase();
      tr.dataset.status = eq.estado;

      const statusClass = STATUS_CLASSES[eq.estado] || "status-available";

      tr.innerHTML = `
        <td class="code">${eq.codigo}</td>
        <td>${eq.tipo}</td>
        <td>
          <span class="status ${statusClass}">
            <span class="status-dot"></span>
            ${eq.estado}
          </span>
        </td>
        <td>
          <button class="button button-secondary button-small" onclick="showEquipment('${eq.codigo}')">
            Ver detalles
          </button>
        </td>
      `;
      tbody.appendChild(tr);
    });

    const statValues = document.querySelectorAll(".stat-card .stat-value");
    if (statValues.length >= 4) {
      statValues[0].textContent = total;
      statValues[1].textContent = disponibles;
      statValues[2].textContent = prestados;
      statValues[3].textContent = revision;
    }
  } catch (error) {
    console.error("Error cargando el inventario:", error);
  }
}

function filterEquipment() {
  const search = document.getElementById("equipment-search").value.toLowerCase();
  const status = document.getElementById("equipment-status").value;
  const rows = document.querySelectorAll("#equipment-table tr");

  rows.forEach(row => {
    const code = row.dataset.code || "";
    const rowStatus = row.dataset.status;
    const matchesCode = code.includes(search);
    const matchesStatus = !status || rowStatus === status;
    row.style.display = matchesCode && matchesStatus ? "" : "none";
  });
}

// ==========================================
// DETALLES DEL EQUIPO
// ==========================================
async function showEquipment(codigo) {
  try {
    const response = await fetch(`${API_URL}/equipos/${codigo}`);
    const data = await response.json();

    if (!response.ok) {
      console.error("Error al obtener equipo:", data.detail);
      return;
    }
    equipoDetalleActual = data;

    document.getElementById("detalle-codigo").textContent = data.codigo;
    document.getElementById("detalle-tipo").textContent = data.tipo;

    const statusClass = STATUS_CLASSES[data.estado] || "status-available";

    document.getElementById("detalle-estado").innerHTML = `
      <span class="status ${statusClass}">
        <span class="status-dot"></span>
        ${data.estado}
      </span>
    `;

    const qrContainer = document.getElementById("detalle-qr-container");

    if (data.qr_base64) {
      qrContainer.innerHTML = `
        <img
          src="${data.qr_base64}"
          alt="Código QR de ${data.codigo}"
          style="width: 220px; height: 220px; object-fit: contain;"
        >
      `;
    } else {
      qrContainer.innerHTML = `<p class="card-subtitle">Este equipo no tiene un código QR disponible.</p>`;
    }

    const contenedorFallas = document.getElementById("detalle-fallas");
    if (data.fallas && data.fallas.length > 0) {
      contenedorFallas.innerHTML = data.fallas.map(falla => `
      <div style="margin-bottom: 8px; padding: 10px; background: var(--bg-secondary, #f8fafc); border-radius: 6px; border: 1px solid var(--border-color, #e2e8f0);">
      <div style="font-size: 14px; color: var(--text);"><strong>Falla:</strong> ${falla.descripcion || "Sin descripción"}</div>
      <div style="font-size: 12px; color: var(--muted); margin-top: 4px;">Estado: ${falla.estado || "Pendiente"}</div>
    </div>
  `).join('');
    } else {
      contenedorFallas.innerHTML = `<p class="card-subtitle">No hay fallas registradas para este equipo.</p>`;
    }

const contenedorPrestamo = document.getElementById("detalle-prestamo");

const prestamo =
  data.prestamo_activo ||
  data.prestamo_actual ||
  data.prestamo ||
  null;

if (prestamo) {
  const estudiante = prestamo.estudiante || null;

  const nombreEstudiante =
    (estudiante && estudiante.nombre) ||
    prestamo.estudiante_nombre ||
    prestamo.nombre ||
    "Desconocido";

  const matriculaEstudiante =
    (estudiante && estudiante.matricula) ||
    prestamo.matricula ||
    "N/A";

  const fechaPrestamo = prestamo.fecha_prestamo || null;

  contenedorPrestamo.innerHTML = `
    <div style="padding: 10px; background: var(--bg-secondary, #f8fafc); border-radius: 6px; border: 1px solid var(--border-color, #e2e8f0);">
      <div style="font-size: 14px; color: var(--text);"><strong>Estudiante:</strong> ${nombreEstudiante}</div>
      <div style="font-size: 14px; color: var(--text); margin-top: 4px;"><strong>Matrícula:</strong> ${matriculaEstudiante}</div>
      <div style="font-size: 12px; color: var(--muted); margin-top: 4px;">Prestado desde: ${fechaPrestamo ? new Date(fechaPrestamo).toLocaleString() : "N/A"}</div>
    </div>
  `;
} else if (data.estado === "Prestado") {
  // El equipo figura como prestado pero no vino información del préstamo:
  // ayuda a diagnosticar en consola sin romper la interfaz.
  console.warn("Equipo marcado como 'Prestado' pero sin datos de préstamo en la respuesta:", data);
  contenedorPrestamo.innerHTML = `<p class="card-subtitle">El equipo está prestado, pero no se recibió la información del préstamo desde el servidor.</p>`;
} else {
  contenedorPrestamo.innerHTML = `<p class="card-subtitle">El equipo se encuentra en el laboratorio (no está prestado).</p>`;
}

    const modalFooter = document.querySelector("#detalle-equipo-modal .modal-footer");
    
    let footerHTML = `
      <button class="button" style="margin-right: auto; background-color: var(--danger, #ef4444); color: white; border: none;" onclick="eliminarEquipo('${data.codigo}')">Eliminar equipo</button>
      <button class="button button-secondary" onclick="closeModal('detalle-equipo-modal')">Cerrar</button>
    `;
    
    if (data.estado === "En revisión") {
      footerHTML += `<button class="button button-primary" onclick="resolverProblema('${data.codigo}')">Resolver problema</button>`;
    }
    modalFooter.innerHTML = footerHTML;

    openModal("detalle-equipo-modal");

  } catch (error) {
    console.error("Error obteniendo detalles del equipo:", error);
    document.getElementById("detalle-qr-container").innerHTML = `<p class="card-subtitle">No se pudo cargar la información del equipo.</p>`;
    document.getElementById("detalle-fallas").innerHTML = `<p class="card-subtitle">Error cargando fallas.</p>`;
    document.getElementById("detalle-prestamo").innerHTML = `<p class="card-subtitle">Error cargando préstamo.</p>`;
  }
}

// ==========================================
// RESOLUCIÓN DE FALLAS
// ==========================================
function resolverProblema(codigo) {
  const fallaPendiente = (equipoDetalleActual?.fallas || []).find(f => f.estado !== "Resuelta");

  if (!fallaPendiente) {
    alert("No se encontró una falla pendiente para este equipo.");
    return;
  }

  document.getElementById("resolver-codigo-label").textContent = codigo;
  document.getElementById("input-resolver-codigo").value = codigo;
  document.getElementById("input-resolver-falla-id").value = fallaPendiente.id;
  document.getElementById("input-resolver-detalle").value = "";

  closeModal("detalle-equipo-modal");
  openModal("resolver-problema-modal");

  setTimeout(() => document.getElementById("input-resolver-detalle").focus(), 100);
}

async function confirmarResolucionProblema() {
  const codigo = document.getElementById("input-resolver-codigo").value;
  const fallaId = document.getElementById("input-resolver-falla-id").value;
  const detalleResolucion = document.getElementById("input-resolver-detalle").value;

  if (!detalleResolucion.trim()) {
    alert("Por favor, ingresa los detalles de cómo se resolvió la falla.");
    return;
  }

  try {
    const response = await fetch(`${API_URL}/fallas/${fallaId}/resolver`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ observacion_resolucion: detalleResolucion })
    });

    if (response.ok) {
      closeModal("resolver-problema-modal");
      mostrarMensajeEquipos(`El problema del equipo ${codigo} se ha marcado como resuelto.`, "success");
      cargarEquiposDesdeAPI();
    } else {
      closeModal("resolver-problema-modal");
      const error = await response.json();
      mostrarMensajeEquipos("No se pudo resolver el problema: " + (error.detail || "Error del servidor"), "danger");
    }
  } catch (error) {
    console.error("Error al resolver el problema:", error);
    closeModal("resolver-problema-modal");
    mostrarMensajeEquipos("Ocurrió un error de conexión con el servidor.", "danger");
  }
}

// ==========================================
// BAJA DE EQUIPOS
// ==========================================
function eliminarEquipo(codigo) {
  document.getElementById("eliminar-codigo-label").textContent = codigo;
  document.getElementById("input-eliminar-codigo").value = codigo;
  
  closeModal("detalle-equipo-modal"); 
  openModal("eliminar-equipo-modal");
}

async function confirmarEliminarEquipo() {
  const codigo = document.getElementById("input-eliminar-codigo").value;
  
  try {
    const response = await fetch(`${API_URL}/equipos/${codigo}/baja`, {
      method: "PATCH", 
      headers: { "Content-Type": "application/json" }
    });

    if (response.ok) {
      closeModal("eliminar-equipo-modal");
      cargarEquiposDesdeAPI(); 
      mostrarMensajeEquipos(`El equipo ${codigo} ha sido dado de baja exitosamente.`, "success");
    } else {
      closeModal("eliminar-equipo-modal");
      const error = await response.json();
      mostrarMensajeEquipos("No se pudo eliminar el equipo: " + (error.detail || "Error del servidor"), "danger");
    }
  } catch (error) {
    console.error("Error al eliminar equipo:", error);
    closeModal("eliminar-equipo-modal");
    mostrarMensajeEquipos("Ocurrió un error en la conexión con el servidor.", "danger");
  }
}

// ==========================================
// INICIALIZACIÓN
// ==========================================
document.addEventListener("DOMContentLoaded", () => {
  if (document.getElementById("equipment-table")) {
    cargarEquiposDesdeAPI();
  }
});