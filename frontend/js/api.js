// Reemplaza con la URL pública que te dio Render
const API_URL = "https://labtrack-api-pvuh.onrender.com/api";

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

    // Respuestas sin contenido (204) o sin body no se pueden parsear como JSON.
    if (respuesta.status === 204) {
      if (!respuesta.ok) {
        throw { status: respuesta.status, detail: "Error sin contenido en la respuesta." };
      }
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
      const error = data && typeof data === "object" ? data : {};
      error.status = respuesta.status;
      if (!error.detail) {
        error.detail = "Error desconocido.";
      }
      throw error;
    }

    return data;
  } catch (error) {
    console.error("Fallo de conexión con Render:", error);
    throw error;
  }
}