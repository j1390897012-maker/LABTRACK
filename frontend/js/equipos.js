const STATUS_CLASSES = {
  "Disponible": "status-available",
  "Prestado": "status-loaned",
  "En revisión": "status-review"
};

async function cargarEquiposDesdeAPI() {
  try {
    // 1. Obtener datos reales de Render
    const equipos = await peticionAPI("/equipos");
    
    // 2. Limpiar la tabla actual
    const tbody = document.getElementById("equipment-table");
    tbody.innerHTML = ""; 

    let total = equipos.length;
    let disponibles = 0;
    let prestados = 0;
    let revision = 0;

    // 3. Crear las filas dinámicamente
    equipos.forEach(eq => {
      if (eq.estado === "Disponible") disponibles++;
      if (eq.estado === "Prestado") prestados++;
      if (eq.estado === "En revisión") revision++;

      const tr = document.createElement("tr");
      tr.dataset.code = eq.codigo;
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

    // 4. Actualizar las tarjetas de estadísticas
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
    const code = row.dataset.code.toLowerCase();
    const rowStatus = row.dataset.status;
    const matchesCode = code.includes(search);
    const matchesStatus = !status || rowStatus === status;
    row.style.display = matchesCode && matchesStatus ? "" : "none";
  });
}

function showEquipment(codigo) {
  alert(`Se abrirá el detalle de ${codigo}. Luego usaremos peticionAPI('/equipos/${codigo}')`);
}

// 5. Ejecutar automáticamente al cargar la página
document.addEventListener("DOMContentLoaded", () => {
  cargarEquiposDesdeAPI();
});