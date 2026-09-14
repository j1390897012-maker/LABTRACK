// ============================================================
// NAVEGACIÓN ENTRE VISTAS
// ============================================================

const navButtons = document.querySelectorAll(".nav-button");
const views = document.querySelectorAll(".view");
const breadcrumb = document.getElementById("breadcrumb");

const viewNames = {
  equipos: "Equipos",
  operacion: "Operación",
  estudiantes: "Estudiantes",
  historial: "Historial",
};

let vistaAnterior = "equipos";


// Navegación normal desde el sidebar
navButtons.forEach((button) => {

  button.addEventListener("click", () => {

    const view = button.dataset.view;

    if (!view) {
      return;
    }

    mostrarVista(view, viewNames[view] || view);

  });

});


// ============================================================
// MOSTRAR UNA VISTA NORMAL
// ============================================================

function mostrarVista(nombre, nombreBreadcrumb = null) {

  // Si estamos abandonando una vista normal,
  // la guardamos para poder regresar posteriormente.
  const vistaActual = obtenerVistaActiva();

  if (
    vistaActual &&
    vistaActual !== "prestamo-rfid" &&
    vistaActual !== nombre
  ) {
    vistaAnterior = vistaActual;
  }

  views.forEach((section) => {
    section.classList.remove("active");
  });

  const vista = document.getElementById(`view-${nombre}`);

  if (!vista) {
    console.error(`No existe la vista: view-${nombre}`);
    return;
  }

  vista.classList.add("active");

  navButtons.forEach((item) => {
    item.classList.toggle(
      "active",
      item.dataset.view === nombre
    );
  });

  if (breadcrumb) {
    breadcrumb.textContent =
      nombreBreadcrumb || viewNames[nombre] || nombre;
  }

}


// ============================================================
// OBTENER VISTA ACTIVA
// ============================================================

function obtenerVistaActiva() {

  const activa = document.querySelector(".view.active");

  if (!activa) {
    return null;
  }

  return activa.id.replace("view-", "");

}


// ============================================================
// ABRIR VISTA INTERNA DE PRÉSTAMO RFID
// ============================================================

function abrirVistaPrestamoRFID() {

  const vistaActual = obtenerVistaActiva();

  if (
    vistaActual &&
    vistaActual !== "prestamo-rfid"
  ) {
    vistaAnterior = vistaActual;
  }

  views.forEach((section) => {
    section.classList.remove("active");
  });

  const vista = document.getElementById(
    "view-prestamo-rfid"
  );

  if (!vista) {
    console.error(
      "No existe la vista view-prestamo-rfid"
    );
    return;
  }

  vista.classList.add("active");

  // Ningún botón del sidebar debe quedar seleccionado
  navButtons.forEach((item) => {
    item.classList.remove("active");
  });

  if (breadcrumb) {
    breadcrumb.textContent = "Préstamo RFID";
  }

}


// ============================================================
// REGRESAR DESDE EL FLUJO RFID
// ============================================================

function regresarDesdePrestamoRFID() {

  const destino = vistaAnterior || "equipos";

  mostrarVista(
    destino,
    viewNames[destino] || destino
  );

}


// ============================================================
// MODALES
// ============================================================

function openModal(id) {

  const modal = document.getElementById(id);

  if (!modal) {
    console.error(`No existe el modal: ${id}`);
    return;
  }

  modal.classList.add("open");

}


function closeModal(id) {

  const modal = document.getElementById(id);

  if (!modal) {
    return;
  }

  modal.classList.remove("open");

}


// Cerrar modal haciendo click en el fondo
document.querySelectorAll(".modal-backdrop").forEach((modal) => {

  modal.addEventListener("click", (event) => {

    if (event.target === modal) {
      modal.classList.remove("open");
    }

  });

});