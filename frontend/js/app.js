// Navegación entre vistas
const navButtons = document.querySelectorAll(".nav-button");
const views = document.querySelectorAll(".view");
const breadcrumb = document.getElementById("breadcrumb");

const viewNames = {
  equipos: "Equipos",
  operacion: "Operación",
  estudiantes: "Estudiantes",
  historial: "Historial"
};

navButtons.forEach(button => {
  button.addEventListener("click", () => {
    const view = button.dataset.view;

    navButtons.forEach(item => item.classList.remove("active"));
    views.forEach(section => section.classList.remove("active"));

    button.classList.add("active");
    document.getElementById(`view-${view}`).classList.add("active");
    breadcrumb.textContent = viewNames[view];
  });
});

// Control de modales
function openModal(id) {
  document.getElementById(id).classList.add("open");
}

function closeModal(id) {
  document.getElementById(id).classList.remove("open");
}

document.querySelectorAll(".modal-backdrop").forEach(modal => {
  modal.addEventListener("click", event => {
    if (event.target === modal) {
      modal.classList.remove("open");
    }
  });
});