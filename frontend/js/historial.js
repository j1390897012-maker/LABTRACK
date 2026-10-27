// ============================================================
// CARGA DEL HISTORIAL (MAPEO EXACTO DEL BACKEND)
// ============================================================

async function cargarHistorialDesdeAPI() {
  const contenedor = document.getElementById("history-list");
  
  if (!contenedor) return;

  contenedor.innerHTML = htmlCargando("Cargando historial…");

  try {
    const data = await peticionAPI("/historial");

    // Extraemos el arreglo real de la propiedad "items" dictada por el backend
    const registros = data.items || [];
    
    if (registros.length === 0) {
      contenedor.innerHTML = `<div class="state-box"><p class="state-title">Aún no hay operaciones</p><p class="state-text">Cuando se preste o devuelva un equipo aparecerá aquí.</p></div>`;
      return;
    }

    renderizarHistorial(registros, contenedor);

  } catch (error) {
    console.error("Fallo la consulta real al backend:", error);
    contenedor.innerHTML = htmlErrorConexion("cargarHistorialDesdeAPI()", mensajeError(error));
  }
}

function renderizarHistorial(registros, contenedor) {
  contenedor.innerHTML = registros.map((registro, i) => {
    // Asegurar que JavaScript interprete la hora como UTC y la convierta a hora local
    const fechaFija = registro.fecha.endsWith("Z") ? registro.fecha : registro.fecha + "Z";
    const fechaObj = new Date(fechaFija);
    const fechaFormat = fechaObj.toLocaleDateString("es-MX", { day: "numeric", month: "short", year: "numeric" });
    const horaFormat = fechaObj.toLocaleTimeString("es-MX", { hour: "2-digit", minute: "2-digit" });

    const tipoEvento = registro.tipo_evento
      ? registro.tipo_evento.charAt(0).toUpperCase() + registro.tipo_evento.slice(1).replace(/_/g, " ")
      : "Evento";

    const clase = ["prestamo", "falla", "devolucion"].includes(registro.tipo_evento)
      ? `tl-${registro.tipo_evento}` : "";

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
      <div class="tl-item ${clase}" style="--i:${Math.min(i, 14)}">
        <span class="tl-dot"></span>
        <div class="tl-card">
          <div class="tl-top">
            <div class="tl-main">${esc(tipoEvento)} de <strong>${esc(registro.codigo_equipo || "N/A")}</strong></div>
            <span class="tl-badge">${esc(tipoEvento)}</span>
          </div>
          <div class="tl-sub">${esc(infoUsuario)}</div>
          ${registro.detalle ? `<div class="tl-det">${esc(registro.detalle)}</div>` : ""}
          <time class="tl-time">${esc(fechaFormat)} · ${esc(horaFormat)}</time>
        </div>
      </div>`;
  }).join("");
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