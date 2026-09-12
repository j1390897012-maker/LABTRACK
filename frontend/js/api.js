// Reemplaza con la URL pública que te dio Render
const API_URL = "https://labtrack-loef.onrender.com/api";

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
    const data = await respuesta.json();
    
    if (!respuesta.ok) {
      console.error(`Error ${respuesta.status}:`, data);
      throw data; // Lanza el error para que el archivo JS específico lo maneje
    }
    
    return data;
  } catch (error) {
    console.error("Fallo de conexión con Render:", error);
    throw error;
  }
}