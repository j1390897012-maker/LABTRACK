async function guardarEstudiante() {
  const nombre = document.getElementById("input-estudiante-nombre").value;
  const matricula = document.getElementById("input-estudiante-matricula").value;

  if (!nombre || !matricula) return alert("Completa todos los campos.");

  try {
    const response = await fetch(`${API_URL}/estudiantes`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ nombre, matricula })
    });
    
    if (response.ok) {
      closeModal("student-modal");
      document.getElementById("input-estudiante-nombre").value = "";
      document.getElementById("input-estudiante-matricula").value = "";
      cargarEstudiantesDesdeAPI();
    } else {
      const error = await response.json();
      alert("Error: " + error.detail);
    }
  } catch (e) {
    console.error("Error al guardar estudiante:", e);
  }
}

async function cargarEstudiantesDesdeAPI() {
  try {
    const response = await fetch(`${API_URL}/estudiantes`);
    if (!response.ok) throw new Error("Error al consultar API");
    
    const estudiantes = await response.json();
    const tbody = document.getElementById("student-table");
    tbody.innerHTML = ""; 

    estudiantes.forEach(est => {
      const tr = document.createElement("tr");
      // Guardamos nombre y matrícula en minúsculas para facilitar el filtro
      tr.dataset.student = `${est.nombre} ${est.matricula}`.toLowerCase();

      const rfidBadge = est.uid_rfid 
        ? `<span class="rfid-badge">RFID registrado</span>`
        : `<span class="rfid-badge rfid-missing" style="background: var(--warning-soft); color: var(--warning);">Sin RFID</span>`;

      // Iniciales para el avatar
      const iniciales = est.nombre.substring(0, 2).toUpperCase();

      tr.innerHTML = `
        <td>
          <div class="student-card">
            <div class="avatar">${iniciales}</div>
            <div><div class="student-name">${est.nombre}</div></div>
          </div>
        </td>
        <td class="code">${est.matricula}</td>
        <td>${rfidBadge}</td>
        <td><span class="status status-available"><span class="status-dot"></span>Inactiva</span></td>
        <td><button class="button button-secondary button-small">Ver estudiante</button></td>
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

document.addEventListener("DOMContentLoaded", () => {
  // Asegurarnos de que cargue la lista al abrir la página
  if (document.getElementById("student-table")) {
    cargarEstudiantesDesdeAPI();
  }
});