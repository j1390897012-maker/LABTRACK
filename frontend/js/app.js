// ============================================================
// NAVEGACIÓN ENTRE VISTAS
// ============================================================

const navButtons = document.querySelectorAll(".nav-button");
const views = document.querySelectorAll(".view");
const breadcrumb = document.getElementById("breadcrumb");

const viewNames = {
  panel: "Panel",
  equipos: "Equipos",
  operacion: "Operación",
  estudiantes: "Estudiantes",
  historial: "Historial",
  importar: "Importar",
};

let vistaAnterior = "panel";


// Navegación normal desde el sidebar
navButtons.forEach((button) => {

  button.addEventListener("click", () => {

    const view = button.dataset.view;

    if (!view) {
      return;
    }

    // La URL es la fuente de verdad (#/equipos?estado=Prestado), así los
    // indicadores, el botón "atrás" y los enlaces compartidos coinciden.
    const destino = `#/${view}`;
    if (location.hash === destino) {
      navegarDesdeHash();
    } else {
      location.hash = destino;
    }

  });

});


// ============================================================
// RUTAS POR HASH
// ============================================================

function leerHash() {
  const texto = location.hash.replace(/^#\/?/, "");
  const [vista, consulta] = texto.split("?");
  return { vista: vista || "panel", params: new URLSearchParams(consulta || "") };
}

function navegarDesdeHash() {
  let { vista, params } = leerHash();

  if (!viewNames[vista]) {
    vista = "panel";
    params = new URLSearchParams();
  }

  mostrarVista(vista, viewNames[vista]);

  if (vista === "equipos" && typeof aplicarFiltrosInventario === "function") {
    aplicarFiltrosInventario(params);
  }
}

window.addEventListener("hashchange", navegarDesdeHash);
document.addEventListener("DOMContentLoaded", navegarDesdeHash);


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
    const activo = item.dataset.view === nombre;
    item.classList.toggle("active", activo);
    if (activo) {
      item.setAttribute("aria-current", "page");
    } else {
      item.removeAttribute("aria-current");
    }
  });

  document.title = `${viewNames[nombre] || nombre} · LABTRACK`;

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

  const destino = vistaAnterior || "panel";

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