// Base del backend. Cuando el panel lo sirve la propia API (lo normal, también
// en Render) se usa el mismo origen; si se abre el archivo directamente
// (file://) se usa Render. Para apuntar a otro servidor durante el desarrollo:
//   localStorage.setItem("labtrack_api_base", "http://192.168.1.10:8000")
const RENDER_BASE = "https://labtrack-api-pvuh.onrender.com";

function resolverBaseAPI() {
  try {
    const manual = localStorage.getItem("labtrack_api_base");
    if (manual) return manual.replace(/\/+$/, "");
  } catch (e) { /* almacenamiento no disponible */ }
  return location.protocol.startsWith("http") ? location.origin : RENDER_BASE;
}

const API_BASE = resolverBaseAPI();
const API_URL = `${API_BASE}/api`;
const WS_URL = `${API_BASE.replace(/^http/, "ws")}/ws`;

async function leerRespuesta(respuesta) {
  // Respuestas sin contenido (204) o sin body no se pueden parsear como JSON.
  if (respuesta.status === 204) {
    return null;
  }

  const textoBruto = await respuesta.text();
  let data = null;

  if (textoBruto) {
    try {
      data = JSON.parse(textoBruto);
    } catch (parseError) {
      // El servidor no devolvió JSON válido; se conserva el texto crudo
      // para no perder información útil en el mensaje de error.
      data = { detail: textoBruto };
    }
  }

  if (!respuesta.ok) {
    console.error(`Error ${respuesta.status}:`, data);
    const error = data && typeof data === "object" && !Array.isArray(data) ? data : {};
    error.status = respuesta.status;
    if (!error.detail) {
      error.detail = "Error desconocido.";
    }
    throw error;
  }

  return data;
}

async function peticionAPI(endpoint, metodo = "GET", body = null) {
  const opciones = {
    method: metodo,
    headers: {
      "Content-Type": "application/json"
    }
  };

  if (body) {
    opciones.body = JSON.stringify(body);
  }

  try {
    const respuesta = await fetch(`${API_URL}${endpoint}`, opciones);
    return await leerRespuesta(respuesta);
  } catch (error) {
    if (error instanceof TypeError) {
      // fetch lanza TypeError cuando no hay conexión con el servidor.
      throw { status: 0, detail: "No se pudo conectar con el servidor." };
    }
    throw error;
  }
}

// Subida de archivos (multipart). No se fija Content-Type: el navegador
// agrega el boundary correcto.
async function subirArchivoAPI(endpoint, archivo, params = {}) {
  const form = new FormData();
  form.append("archivo", archivo);
  const query = new URLSearchParams(params).toString();
  try {
    const respuesta = await fetch(
      `${API_URL}${endpoint}${query ? "?" + query : ""}`,
      { method: "POST", body: form }
    );
    return await leerRespuesta(respuesta);
  } catch (error) {
    if (error instanceof TypeError) {
      throw { status: 0, detail: "No se pudo conectar con el servidor." };
    }
    throw error;
  }
}

// Convierte cualquier error de la API en un texto legible. FastAPI devuelve
// `detail` como texto, o como lista de {loc, msg} en errores de validación (422).
function mensajeError(error, porDefecto = "Ocurrió un error inesperado.") {
  if (!error) return porDefecto;
  const d = error.detail;
  if (Array.isArray(d)) {
    return d.map((e) => {
      const campo = Array.isArray(e.loc) ? e.loc[e.loc.length - 1] : "";
      return campo ? `${campo}: ${e.msg}` : e.msg;
    }).join(" · ");
  }
  return (typeof d === "string" && d) || error.message || porDefecto;
}

// Escapa texto antes de insertarlo con innerHTML (los datos pueden venir de
// archivos Excel o de formularios).
function esc(valor) {
  return String(valor ?? "").replace(/[&<>"']/g, (c) => (
    { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]
  ));
}