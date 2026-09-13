const STATUS_CLASSES = {
  "Disponible": "status-available",
  "Prestado": "status-loaned",
  "En revisión": "status-review",
  "Baja": "status-review" 
};

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
    } else {
      const error = await response.json();
      alert("Error: " + error.detail);
    }
  } catch (e) {
    console.error("Error al guardar equipo:", e);
  }
}

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

async function showEquipment(codigo) {
  try {
    const response = await fetch(`${API_URL}/equipos/${codigo}`);
    const data = await response.json();
    
    if (response.ok) {
      // Por ahora usamos un alert para confirmar que la API responde.
      // En el futuro, esto puede abrir un modal estructurado.
      alert(`Detalles del Equipo:\nCódigo: ${data.codigo}\nTipo: ${data.tipo}\nEstado: ${data.estado}`);
    } else {
      alert("Error: " + data.detail);
    }
  } catch (error) {
    console.error("Error obteniendo detalles:", error);
    alert("No se pudo conectar con el servidor.");
  }
}

document.addEventListener("DOMContentLoaded", () => {
  if (document.getElementById("equipment-table")) {
    cargarEquiposDesdeAPI();
  }
});