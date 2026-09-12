/* =========================================================
   ESTUDIANTES — FILTRO VISUAL (MOCK)
   ========================================================= */

function filterStudents() {
  const search = document
    .getElementById("student-search")
    .value
    .toLowerCase();

  const rows = document.querySelectorAll("#student-table tr");

  rows.forEach(row => {
    // Busca en el atributo data-student que pusiste en el HTML
    const student = row.dataset.student.toLowerCase();

    row.style.display = student.includes(search) ? "" : "none";
  });
}


/* =========================================================
   INTEGRACIÓN FUTURA CON LA API (RENDER)
   ========================================================= */

// Ejemplo de cómo usarás api.js más adelante para cargar la lista real
async function cargarEstudiantesDesdeAPI() {
  try {
    const estudiantes = await peticionAPI("/estudiantes");
    console.log("Estudiantes recibidos de Render:", estudiantes);
    
    // Aquí iría la lógica para limpiar el <tbody> y crear los <tr> 
    // dinámicamente con los datos de la base de datos.
  } catch (error) {
    console.error("Error al cargar los estudiantes", error);
  }
}

// Ejemplo para registrar un estudiante nuevo desde el modal
async function registrarEstudiante(nombre, matricula) {
  try {
    const nuevoEstudiante = await peticionAPI("/estudiantes", "POST", {
      nombre: nombre,
      matricula: matricula
    });
    console.log("Estudiante registrado exitosamente", nuevoEstudiante);
    closeModal('student-modal');
    // cargarEstudiantesDesdeAPI(); // Recargar la tabla
  } catch (error) {
    alert("Hubo un error al registrar el estudiante");
  }
}