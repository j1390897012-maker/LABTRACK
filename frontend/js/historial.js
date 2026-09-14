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
      <p class="card-subtitle" style="color: var(--danger);">
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
    
    // Determinar colores del badge
    let badgeColor = "var(--success)";
    let colorBg = "var(--success-light, #d1fae5)";
    
    if (registro.tipo_evento === "prestamo") {
      badgeColor = "var(--warning)";
      colorBg = "var(--warning-light, #fef3c7)";
    } else if (registro.tipo_evento === "falla") {
      badgeColor = "var(--danger)";
      colorBg = "var(--danger-light, #fee2e2)";
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

    return `
      <div class="history-item" style="display: flex; align-items: flex-start; gap: 16px; padding: 12px 0; border-bottom: 1px solid var(--border-color, #e2e8f0);">
        <div class="history-date" style="min-width: 60px; text-align: center; color: var(--muted); font-size: 13px; font-weight: 600;">
          ${fechaFormat}<br>
          <span style="font-weight: 400; font-size: 11px;">${horaFormat}</span>
        </div>
        
        <div style="flex: 1;">
          <div class="history-main" style="color: var(--text); font-weight: 500; font-size: 15px;">
            ${tipoEvento} de <strong>${registro.codigo_equipo || "N/A"}</strong>
          </div>
          <div class="history-secondary" style="color: var(--muted); font-size: 13px; margin-top: 4px;">
            ${infoUsuario}
          </div>
          ${registro.detalle ? `<div style="font-size: 12px; color: var(--text); margin-top: 6px; padding: 4px 8px; background-color: var(--bg-secondary, #f1f5f9); border-radius: 4px; display: inline-block;">${registro.detalle}</div>` : ''}
        </div>
        
        <span class="history-type" style="background-color: ${colorBg}; color: ${badgeColor}; padding: 4px 8px; border-radius: 99px; font-size: 12px; font-weight: 600;">
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