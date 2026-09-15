// ============================================================
// CARGA DEL HISTORIAL (MAPEO EXACTO DEL BACKEND)
// ============================================================

async function cargarHistorialDesdeAPI() {
  const contenedor = document.getElementById("history-list");
  
  if (!contenedor) return;

  contenedor.innerHTML = `<p class="card-subtitle">Cargando historial de operaciones...</p>`;

  try {
    const response = await fetch(`${API_URL}/historial`);
    
    if (!response.ok) {
      throw new Error(`Error HTTP: ${response.status}`);
    }

    const data = await response.json();
    
    // Extraemos el arreglo real de la propiedad "items" dictada por el backend
    const registros = data.items || [];
    
    if (registros.length === 0) {
      contenedor.innerHTML = `<p class="card-subtitle">Aún no hay operaciones registradas en el laboratorio.</p>`;
      return;
    }

    renderizarHistorial(registros, contenedor);

  } catch (error) {
    console.error("Fallo la consulta real al backend:", error);
    contenedor.innerHTML = `
      <p class="card-subtitle text-danger">
        No se pudo cargar el historial. Revisa la consola para más detalles.
      </p>
    `;
  }
}

function renderizarHistorial(registros, contenedor) {
  contenedor.innerHTML = registros.map(registro => {
    // Asegurar que JavaScript interprete la hora como UTC y la convierta a hora local
    const fechaFija = registro.fecha.endsWith("Z") ? registro.fecha : registro.fecha + "Z";
    const fechaObj = new Date(fechaFija);
    const fechaFormat = fechaObj.toLocaleDateString('es-MX', { month: 'short', day: 'numeric' });
    const horaFormat = fechaObj.toLocaleTimeString('es-MX', { hour: '2-digit', minute: '2-digit' });
    
    // Capitalizar la primera letra del evento
    const tipoEvento = registro.tipo_evento ? registro.tipo_evento.charAt(0).toUpperCase() + registro.tipo_evento.slice(1) : "Evento";
    
    // Determinar la clase de color del badge
    let badgeClass = "badge-success";
    if (registro.tipo_evento === "prestamo") {
      badgeClass = "badge-warning";
    } else if (registro.tipo_evento === "falla") {
      badgeClass = "badge-danger";
    }

    // Manejo inteligente de datos nulos para fallas
    const nombre = registro.estudiante_nombre;
    const matricula = registro.matricula;
    
    let infoUsuario = "";
    if (nombre || matricula) {
      infoUsuario = `${nombre || "Desconocido"} · ${matricula || "Sin matrícula"}`;
    } else if (registro.tipo_evento === "falla" || registro.tipo_evento === "resolucion_falla") {
      infoUsuario = "Reportado por encargado / Revisión";
    } else {
      infoUsuario = "Operación de sistema";
    }

    // Aprovechamos la clase global .history-item que ya tienes en tu CSS principal
    return `
      <div class="history-item">
        <div class="history-date-col">
          ${fechaFormat}<br>
          <span class="history-time">${horaFormat}</span>
        </div>
        
        <div>
          <div class="history-title">
            ${tipoEvento} de <strong>${registro.codigo_equipo || "N/A"}</strong>
          </div>
          <div class="history-subtitle">
            ${infoUsuario}
          </div>
          ${registro.detalle ? `<div class="history-detail-pill">${registro.detalle}</div>` : ''}
        </div>
        
        <span class="history-badge ${badgeClass}">
          ${tipoEvento}
        </span>
      </div>
    `;
  }).join('');
}

// Inicializar la carga al interactuar con el DOM
document.addEventListener("DOMContentLoaded", () => {
  if (document.getElementById("view-historial")) {
    cargarHistorialDesdeAPI();
  }
  
  const navHistorial = document.querySelector('button[data-view="historial"]');
  if(navHistorial) {
    navHistorial.addEventListener("click", () => {
      cargarHistorialDesdeAPI();
    });
  }
});