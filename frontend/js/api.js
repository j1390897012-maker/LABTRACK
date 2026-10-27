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

// Mensajes que sí se muestran al usuario. El detalle técnico solo va a la consola.
const MSG_CONEXION = "No se pudo conectar con el servidor. Revisa tu conexión e inténtalo de nuevo.";
const MSG_SERVIDOR = "Algo salió mal de nuestro lado. Inténtalo de nuevo en unos momentos.";
const MSG_DATOS = "Revisa los datos ingresados e inténtalo de nuevo.";
const MSG_GENERICO = "No se pudo completar la acción. Inténtalo de nuevo.";

function esTextoTecnico(texto) {
  return texto.length > 220 ||
    /traceback|exception|sqlalchemy|psycopg|asyncpg|operationalerror|<html|<!doctype|internal server error|errno|stack|connection (refused|reset)|timed? ?out|\bat 0x/i.test(texto);
}

// Convierte la respuesta de error del backend en un texto apto para el usuario.
function detalleAmigable(status, detail) {
  if (status >= 500) return MSG_SERVIDOR;
  if (Array.isArray(detail)) return MSG_DATOS;
  if (typeof detail === "string" && detail.trim()) {
    return esTextoTecnico(detail) ? MSG_SERVIDOR : detail;
  }
  return MSG_GENERICO;
}

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
    // El detalle técnico queda solo en la consola (para quien desarrolla).
    console.error(`Error ${respuesta.status}:`, data);
    const error = data && typeof data === "object" && !Array.isArray(data) ? data : {};
    error.status = respuesta.status;
    error.detalle_tecnico = error.detail;
    error.detail = detalleAmigable(respuesta.status, error.detail);
    throw error;
  }

  return data;
}

async function peticionCruda(endpoint, metodo = "GET", body = null) {
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
      throw { status: 0, detail: MSG_CONEXION };
    }
    throw error;
  }
}

// Subida de archivos (multipart). No se fija Content-Type: el navegador
// agrega el boundary correcto.
async function subirCruda(endpoint, archivo, params = {}) {
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
      throw { status: 0, detail: MSG_CONEXION };
    }
    throw error;
  }
}

// Seguimiento de red: avisa a la interfaz si una petición tarda o si se cayó la conexión.
// (redInicio / redFin / redEstado viven en ui.js)
async function conSeguimiento(endpoint, tarea) {
  const silenciosa = /ultimo-scan/.test(endpoint); // el sondeo de escaneos no debe distraer
  if (!silenciosa && typeof redInicio === "function") redInicio();
  try {
    const resultado = await tarea();
    // Solo las peticiones "normales" confirman que hay conexión (el sondeo silencioso no).
    if (!silenciosa && typeof redEstado === "function") redEstado(true);
    return resultado;
  } catch (error) {
    if (typeof redEstado === "function") {
      redEstado(!(error && (error.status === 0 || error.status >= 500)));
    }
    throw error;
  } finally {
    if (!silenciosa && typeof redFin === "function") redFin();
  }
}

function peticionAPI(endpoint, metodo = "GET", body = null) {
  return conSeguimiento(endpoint, () => peticionCruda(endpoint, metodo, body));
}

function subirArchivoAPI(endpoint, archivo, params = {}) {
  return conSeguimiento(endpoint, () => subirCruda(endpoint, archivo, params));
}

// Convierte cualquier error de la API en un texto legible. FastAPI devuelve
// `detail` como texto, o como lista de {loc, msg} en errores de validación (422).
function mensajeError(error, porDefecto = "Ocurrió un error inesperado.") {
  if (!error) return porDefecto;
  const d = error.detail;
  if (Array.isArray(d)) return MSG_DATOS;
  if (typeof d === "string" && d) return esTextoTecnico(d) ? MSG_SERVIDOR : d;
  return porDefecto;
}

// Escapa texto antes de insertarlo con innerHTML (los datos pueden venir de
// archivos Excel o de formularios).
function esc(valor) {
  return String(valor ?? "").replace(/[&<>"']/g, (c) => (
    { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]
  ));
}