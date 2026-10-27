const STATUS_CLASSES = {
  "Disponible": "status-available",
  "Prestado": "status-loaned",
  "En revisión": "status-review",
  "Baja": "status-neutral"
};

let equipoDetalleActual = null;

// ==========================================
// NOTIFICACIONES GLOBALES (TOAST)
// ==========================================
function mostrarMensajeEquipos(mensaje, tipo = "success") {
  let toastContainer = document.getElementById("toast-container");
  
  if (!toastContainer) {
    toastContainer = document.createElement("div");
    toastContainer.id = "toast-container";
    document.body.appendChild(toastContainer);
  }

  const alertaContenedor = document.createElement("div");
  alertaContenedor.className = "ui-alert-container";
  const alerta = document.createElement("div");
  alerta.className = `ui-alert ui-alert-${tipo}`;
  alerta.setAttribute("role", tipo === "danger" ? "alert" : "status");
  alerta.textContent = mensaje;
  alertaContenedor.appendChild(alerta);

  toastContainer.appendChild(alertaContenedor);

  setTimeout(() => {
    if (alertaContenedor.parentNode) {
      alertaContenedor.remove();
    }
  }, 4000);
}

// ==========================================
// REGISTRO DE EQUIPOS
// ==========================================
const CAMPOS_REGISTRO = {
  codigo: { input: "input-equipo-codigo", error: "err-codigo" },
  tipo: { input: "input-equipo-tipo", error: "err-tipo" },
  numero_inventario: { input: "input-equipo-inventario", error: "err-inventario" },
};

function errorCampo(campo, mensaje) {
  const { input, error } = CAMPOS_REGISTRO[campo];
  const inputEl = document.getElementById(input);
  const errorEl = document.getElementById(error);
  errorEl.textContent = mensaje || "";
  errorEl.hidden = !mensaje;
  if (mensaje) {
    inputEl.setAttribute("aria-invalid", "true");
  } else {
    inputEl.removeAttribute("aria-invalid");
  }
}

function limpiarErroresRegistro() {
  Object.keys(CAMPOS_REGISTRO).forEach((c) => errorCampo(c, ""));
  const banner = document.getElementById("equipo-form-error");
  banner.hidden = true;
  banner.textContent = "";
}

async function cargarTiposEquipo() {
  try {
    const tipos = await peticionAPI("/tipos-equipo");
    inventario.tipos = tipos.map((t) => t.nombre);
    document.getElementById("lista-tipos").innerHTML =
      inventario.tipos.map((t) => `<option value="${esc(t)}"></option>`).join("");
    poblarFiltroTipos();
  } catch (error) {
    // El catálogo es una ayuda: sin él se puede escribir el tipo a mano.
    console.warn("No se pudo cargar el catálogo de tipos:", error);
  }
}

function prepararRegistroEquipo() {
  document.getElementById("equipo-form").reset();
  document.getElementById("equipo-form").hidden = false;
  document.getElementById("equipo-exito").hidden = true;
  limpiarErroresRegistro();
  const boton = document.getElementById("equipo-guardar");
  boton.disabled = false;
  boton.textContent = "Guardar equipo";
  setTimeout(() => document.getElementById("input-equipo-codigo").focus(), 50);
}

function abrirRegistroEquipo() {
  prepararRegistroEquipo();
  cargarTiposEquipo();
  openModal("equipo-modal");
}

function validarRegistro(datos) {
  limpiarErroresRegistro();
  let valido = true;
  if (!datos.codigo) {
    errorCampo("codigo", "Indica el código del laboratorio.");
    valido = false;
  } else if (datos.codigo.length > 50) {
    errorCampo("codigo", "Máximo 50 caracteres.");
    valido = false;
  }
  if (!datos.tipo) {
    errorCampo("tipo", "Indica el tipo de equipo.");
    valido = false;
  }
  if (datos.numero_inventario && datos.numero_inventario === datos.codigo) {
    errorCampo(
      "numero_inventario",
      "El número de inventario debe ser distinto del código del laboratorio."
    );
    valido = false;
  }
  if (!valido) {
    const primero = document.querySelector("#equipo-form [aria-invalid='true']");
    if (primero) primero.focus();
  }
  return valido;
}

async function guardarEquipo(evento) {
  if (evento) evento.preventDefault();

  const valor = (id) => document.getElementById(id).value.trim();
  const datos = {
    codigo: valor("input-equipo-codigo"),
    tipo: valor("input-equipo-tipo"),
    numero_inventario: valor("input-equipo-inventario") || null,
    marca: valor("input-equipo-marca") || null,
    modelo: valor("input-equipo-modelo") || null,
  };

  if (!validarRegistro(datos)) return;

  const boton = document.getElementById("equipo-guardar");
  boton.disabled = true;
  boton.textContent = "Guardando…";

  try {
    const creado = await peticionAPI("/equipos", "POST", datos);

    // Solo se confirma lo que la API aceptó.
    document.getElementById("equipo-form").hidden = true;
    document.getElementById("equipo-exito").hidden = false;
    document.getElementById("equipo-exito-texto").textContent =
      `Equipo ${creado.codigo} registrado correctamente.`;
    document.getElementById("equipo-exito-qr").innerHTML = creado.qr_base64
      ? `<img src="${creado.qr_base64}" alt="Código QR de ${esc(creado.codigo)}" style="width:180px;height:180px;object-fit:contain">`
      : "";
    mostrarMensajeEquipos(`El equipo ${creado.codigo} fue registrado.`, "success");
    cargarEquiposDesdeAPI();
  } catch (error) {
    boton.disabled = false;
    boton.textContent = "Guardar equipo";
    const mensaje = mensajeError(error, "No se pudo registrar el equipo.");

    if (error.status === 409 && /inventario/i.test(mensaje)) {
      errorCampo("numero_inventario", mensaje);
      document.getElementById("input-equipo-inventario").focus();
    } else if (error.status === 409) {
      errorCampo("codigo", mensaje);
      document.getElementById("input-equipo-codigo").focus();
    } else {
      const banner = document.getElementById("equipo-form-error");
      banner.textContent = mensaje;
      banner.hidden = false;
    }
  }
}

// ==========================================
// INVENTARIO: estado, filtros, orden y paginación
// ==========================================
const inventario = {
  datos: [],
  tipos: [],
  cargando: true,
  error: null,
  busqueda: "",
  estado: "",
  tipo: "",
  orden: { campo: "codigo", dir: "asc" },
  pagina: 1,
  porPagina: 25,
};

const COLLATOR = new Intl.Collator("es", { numeric: true, sensitivity: "base" });

function normalizar(texto) {
  return String(texto ?? "")
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .toLowerCase();
}

function claseEstado(estado) {
  return STATUS_CLASSES[estado] || "status-neutral";
}

function badgeEstado(estado) {
  return `<span class="status ${claseEstado(estado)}"><span class="status-dot"></span>${esc(estado)}</span>`;
}

function poblarFiltroTipos() {
  const select = document.getElementById("inv-tipo");
  if (!select) return;
  const delInventario = inventario.datos.map((e) => e.tipo);
  const todos = [...new Set([...inventario.tipos, ...delInventario])].sort(COLLATOR.compare);
  select.innerHTML =
    `<option value="">Todos los tipos</option>` +
    todos.map((t) => `<option value="${esc(t)}">${esc(t)}</option>`).join("");
  select.value = inventario.tipo;
}

function equiposFiltrados() {
  const q = normalizar(inventario.busqueda.trim());
  const lista = inventario.datos.filter((e) => {
    if (inventario.estado && e.estado !== inventario.estado) return false;
    if (inventario.tipo && e.tipo !== inventario.tipo) return false;
    if (!q) return true;
    return normalizar(
      [e.codigo, e.numero_inventario, e.marca, e.modelo, e.tipo].join(" ")
    ).includes(q);
  });

  const { campo, dir } = inventario.orden;
  const factor = dir === "asc" ? 1 : -1;
  return lista.sort((a, b) => {
    const va = a[campo];
    const vb = b[campo];
    // Los vacíos siempre al final, sea cual sea el sentido.
    if (!va && !vb) return COLLATOR.compare(a.codigo, b.codigo);
    if (!va) return 1;
    if (!vb) return -1;
    return factor * COLLATOR.compare(va, vb) || COLLATOR.compare(a.codigo, b.codigo);
  });
}

function sincronizarHash() {
  const params = new URLSearchParams();
  if (inventario.estado) params.set("estado", inventario.estado);
  if (inventario.tipo) params.set("tipo", inventario.tipo);
  if (inventario.busqueda.trim()) params.set("q", inventario.busqueda.trim());
  const consulta = params.toString();
  const hash = `#/equipos${consulta ? "?" + consulta : ""}`;
  // replaceState no dispara hashchange: la URL queda compartible sin reiniciar la vista.
  if (location.hash !== hash && obtenerVistaActiva() === "equipos") {
    history.replaceState(null, "", hash);
  }
}

function hayFiltros() {
  return Boolean(inventario.estado || inventario.tipo || inventario.busqueda.trim());
}

function mostrarEstadoVista(html) {
  const caja = document.getElementById("inv-estado-vista");
  caja.hidden = !html;
  caja.innerHTML = html || "";
}

function renderInventario() {
  const tbody = document.getElementById("equipment-table");
  if (!tbody) return;

  if (typeof sincronizarVistaEquipos === "function") sincronizarVistaEquipos();
  document.getElementById("inv-limpiar").hidden = !hayFiltros();
  document.querySelectorAll(".th-sort").forEach((boton) => {
    const th = boton.closest("th");
    const activo = boton.dataset.campo === inventario.orden.campo;
    th.setAttribute(
      "aria-sort",
      activo ? (inventario.orden.dir === "asc" ? "ascending" : "descending") : "none"
    );
  });

  const resumen = document.getElementById("inv-resumen");
  const paginacion = document.getElementById("inv-paginacion");

  if (inventario.cargando) {
    resumen.textContent = "Cargando inventario…";
    paginacion.hidden = true;
    tbody.innerHTML = Array.from({ length: 8 }, () => `<div class="skeleton-card"></div>`).join("");
    mostrarEstadoVista("");
    return;
  }

  if (inventario.error) {
    resumen.textContent = "Sin datos por el momento.";
    tbody.innerHTML = "";
    paginacion.hidden = true;
    mostrarEstadoVista(htmlErrorConexion("cargarEquiposDesdeAPI()", esc(inventario.error)));
    return;
  }

  if (inventario.datos.length === 0) {
    resumen.textContent = "Sin equipos registrados.";
    tbody.innerHTML = "";
    paginacion.hidden = true;
    mostrarEstadoVista(`
      <p class="state-title">Aún no hay equipos registrados</p>
      <p class="state-text">Registra uno manualmente o carga el inventario completo desde un archivo.</p>
      <div class="state-actions">
        <button class="button button-primary" type="button" onclick="abrirRegistroEquipo()">Registrar equipo</button>
        <button class="button button-secondary" type="button" onclick="location.hash='#/importar'">Importar inventario</button>
      </div>`);
    return;
  }

  const lista = equiposFiltrados();
  const paginas = Math.max(1, Math.ceil(lista.length / inventario.porPagina));
  inventario.pagina = Math.min(inventario.pagina, paginas);
  const desde = (inventario.pagina - 1) * inventario.porPagina;
  const visibles = lista.slice(desde, desde + inventario.porPagina);

  if (lista.length === 0) {
    resumen.textContent = `0 de ${inventario.datos.length} equipos`;
    tbody.innerHTML = "";
    paginacion.hidden = true;
    mostrarEstadoVista(`
      <p class="state-title">Ningún equipo coincide con los filtros</p>
      <p class="state-text">Prueba con otra búsqueda o quita los filtros.</p>
      <button class="button button-secondary" type="button" onclick="limpiarFiltrosInventario()">Limpiar filtros</button>`);
    return;
  }

  mostrarEstadoVista("");
  resumen.textContent =
    `Mostrando ${desde + 1}–${desde + visibles.length} de ${lista.length}` +
    (lista.length !== inventario.datos.length ? ` (${inventario.datos.length} en total)` : " equipos");

  tbody.innerHTML = visibles.map((e, i) => {
    const marcaModelo = [e.marca, e.modelo].filter(Boolean).join(" ");
    const sub = marcaModelo || (e.numero_inventario ? `Inv. ${e.numero_inventario}` : "");
    return `
      <button type="button" class="equipo-card" style="--i:${Math.min(i, 14)}"
              data-codigo="${esc(e.codigo)}" aria-label="Ver detalle del equipo ${esc(e.codigo)}">
        <div class="eq-art">${iconoEquipo(e.tipo)}</div>
        ${badgeEstado(e.estado)}
        <div class="eq-code">${esc(e.codigo)}</div>
        <div class="eq-type">${esc(e.tipo)}</div>
        <div class="eq-sub">${esc(sub)}</div>
      </button>`;
  }).join("");

  paginacion.hidden = paginas <= 1;
  document.getElementById("inv-pagina").textContent = `Página ${inventario.pagina} de ${paginas}`;
  document.getElementById("inv-anterior").disabled = inventario.pagina <= 1;
  document.getElementById("inv-siguiente").disabled = inventario.pagina >= paginas;
}

async function cargarEquiposDesdeAPI() {
  // Solo se muestra el esqueleto en la primera carga; las actualizaciones en
  // vivo reemplazan los datos sin parpadeo.
  if (inventario.datos.length === 0) {
    inventario.cargando = true;
    renderInventario();
  }
  try {
    inventario.datos = await peticionAPI("/equipos");
    inventario.error = null;
    poblarFiltroTipos();
  } catch (error) {
    inventario.error = mensajeError(error, "No se pudo consultar el servidor.");
    console.error("Error cargando el inventario:", error);
  }
  inventario.cargando = false;
  renderInventario();
  // Avisa a la vista de panel para que pinte las categorías.
  document.dispatchEvent(new Event("labtrack:inventario"));
}

function aplicarFiltrosInventario(params) {
  inventario.estado = params.get("estado") || "";
  inventario.tipo = params.get("tipo") || "";
  inventario.busqueda = params.get("q") || "";
  inventario.pagina = 1;
  document.getElementById("inv-estado").value = inventario.estado;
  document.getElementById("inv-tipo").value = inventario.tipo;
  document.getElementById("inv-busqueda").value = inventario.busqueda;
  renderInventario();
}

function limpiarFiltrosInventario() {
  aplicarFiltrosInventario(new URLSearchParams());
  sincronizarHash();
  document.getElementById("inv-busqueda").focus();
}

function iniciarInventario() {
  const busqueda = document.getElementById("inv-busqueda");
  const cambiar = () => {
    inventario.busqueda = busqueda.value;
    inventario.estado = document.getElementById("inv-estado").value;
    inventario.tipo = document.getElementById("inv-tipo").value;
    inventario.pagina = 1;
    sincronizarHash();
    renderInventario();
  };

  let espera = null;
  busqueda.addEventListener("input", () => {
    clearTimeout(espera);
    espera = setTimeout(cambiar, 150);
  });
  document.getElementById("inv-estado").addEventListener("change", cambiar);
  document.getElementById("inv-tipo").addEventListener("change", cambiar);
  document.getElementById("inv-limpiar").addEventListener("click", limpiarFiltrosInventario);

  document.getElementById("inv-por-pagina").addEventListener("change", (e) => {
    inventario.porPagina = Number(e.target.value);
    inventario.pagina = 1;
    renderInventario();
  });
  document.getElementById("inv-anterior").addEventListener("click", () => {
    inventario.pagina -= 1;
    renderInventario();
  });
  document.getElementById("inv-siguiente").addEventListener("click", () => {
    inventario.pagina += 1;
    renderInventario();
  });

  document.querySelectorAll(".th-sort").forEach((boton) => {
    boton.addEventListener("click", () => {
      const campo = boton.dataset.campo;
      inventario.orden = {
        campo,
        dir: inventario.orden.campo === campo && inventario.orden.dir === "asc" ? "desc" : "asc",
      };
      inventario.pagina = 1;
      renderInventario();
    });
  });

  document.getElementById("equipment-table").addEventListener("click", (e) => {
    const boton = e.target.closest("button[data-codigo]");
    if (boton) showEquipment(boton.dataset.codigo);
  });

  document.getElementById("equipo-form").addEventListener("submit", guardarEquipo);
}

// ==========================================
// DETALLES DEL EQUIPO
// ==========================================
async function showEquipment(codigo) {
  try {
    const data = await peticionAPI(`/equipos/${codigo}`);
    equipoDetalleActual = data;

    document.getElementById("detalle-ilustracion").innerHTML = iconoEquipo(data.tipo);
    document.getElementById("detalle-codigo").textContent = data.codigo;
    document.getElementById("detalle-tipo").textContent = data.tipo;
    document.getElementById("detalle-inventario").textContent =
      data.numero_inventario || "—";
    document.getElementById("detalle-marca-modelo").textContent =
      [data.marca, data.modelo].filter(Boolean).join(" ") || "—";

    const statusClass = STATUS_CLASSES[data.estado] || "status-available";

    document.getElementById("detalle-estado").innerHTML = `
      <span class="status ${statusClass}">
        <span class="status-dot"></span>
        ${esc(data.estado)}
      </span>
    `;

    const qrContainer = document.getElementById("detalle-qr-container");

    if (data.qr_base64) {
      qrContainer.innerHTML = `
        <img
          src="${data.qr_base64}"
          alt="Código QR de ${data.codigo}"
          style="width: 220px; height: 220px; object-fit: contain;"
        >
      `;
    } else {
      qrContainer.innerHTML = `<p class="card-subtitle">Este equipo no tiene un código QR disponible.</p>`;
    }

    const contenedorFallas = document.getElementById("detalle-fallas");
    if (data.fallas && data.fallas.length > 0) {
      contenedorFallas.innerHTML = data.fallas.map(falla => `
      <div style="margin-bottom: 8px; padding: 10px; background: var(--bg-secondary, #f8fafc); border-radius: 6px; border: 1px solid var(--border-color, #e2e8f0);">
      <div style="font-size: 14px; color: var(--text);"><strong>Falla:</strong> ${esc(falla.descripcion || "Sin descripción")}</div>
      <div style="font-size: 12px; color: var(--muted); margin-top: 4px;">Estado: ${esc(falla.estado || "Pendiente")}</div>
    </div>
  `).join('');
    } else {
      contenedorFallas.innerHTML = `<p class="card-subtitle">No hay fallas registradas para este equipo.</p>`;
    }

const contenedorPrestamo = document.getElementById("detalle-prestamo");

const prestamo =
  data.prestamo_activo ||
  data.prestamo_actual ||
  data.prestamo ||
  null;

if (prestamo) {
  const estudiante = prestamo.estudiante || null;

  const nombreEstudiante =
    (estudiante && estudiante.nombre) ||
    prestamo.estudiante_nombre ||
    prestamo.nombre ||
    "Desconocido";

  const matriculaEstudiante =
    (estudiante && estudiante.matricula) ||
    prestamo.matricula ||
    "N/A";

  const fechaPrestamo = prestamo.fecha_prestamo || null;

  contenedorPrestamo.innerHTML = `
    <div style="padding: 10px; background: var(--bg-secondary, #f8fafc); border-radius: 6px; border: 1px solid var(--border-color, #e2e8f0);">
      <div style="font-size: 14px; color: var(--text);"><strong>Estudiante:</strong> ${esc(nombreEstudiante)}</div>
      <div style="font-size: 14px; color: var(--text); margin-top: 4px;"><strong>Matrícula:</strong> ${esc(matriculaEstudiante)}</div>
      <div style="font-size: 12px; color: var(--muted); margin-top: 4px;">Prestado desde: ${fechaPrestamo ? new Date(fechaPrestamo).toLocaleString() : "N/A"}</div>
    </div>
  `;
} else if (data.estado === "Prestado") {
  // El equipo figura como prestado pero no vino información del préstamo:
  // ayuda a diagnosticar en consola sin romper la interfaz.
  console.warn("Equipo marcado como 'Prestado' pero sin datos de préstamo en la respuesta:", data);
  contenedorPrestamo.innerHTML = `<p class="card-subtitle">El equipo está prestado, pero no se recibió la información del préstamo desde el servidor.</p>`;
} else {
  contenedorPrestamo.innerHTML = `<p class="card-subtitle">El equipo se encuentra en el laboratorio (no está prestado).</p>`;
}

    const modalFooter = document.querySelector("#detalle-equipo-modal .modal-footer");
    
    let footerHTML = `
      <button class="button" style="margin-right: auto; background-color: var(--danger, #ef4444); color: white; border: none;" onclick="eliminarEquipo('${data.codigo}')">Eliminar equipo</button>
      <button class="button button-secondary" onclick="closeModal('detalle-equipo-modal')">Cerrar</button>
    `;
    
    if (data.estado === "En revisión") {
      footerHTML += `<button class="button button-primary" onclick="resolverProblema('${data.codigo}')">Resolver problema</button>`;
    }
    modalFooter.innerHTML = footerHTML;

    openModal("detalle-equipo-modal");

  } catch (error) {
    console.error("Error obteniendo detalles del equipo:", error);
    document.getElementById("detalle-qr-container").innerHTML = `<p class="card-subtitle">No se pudo cargar la información del equipo.</p>`;
    document.getElementById("detalle-fallas").innerHTML = `<p class="card-subtitle">Error cargando fallas.</p>`;
    document.getElementById("detalle-prestamo").innerHTML = `<p class="card-subtitle">Error cargando préstamo.</p>`;
  }
}

// ==========================================
// RESOLUCIÓN DE FALLAS
// ==========================================
function resolverProblema(codigo) {
  const fallaPendiente = (equipoDetalleActual?.fallas || []).find(f => f.estado !== "Resuelta");

  if (!fallaPendiente) {
    alert("No se encontró una falla pendiente para este equipo.");
    return;
  }

  document.getElementById("resolver-codigo-label").textContent = codigo;
  document.getElementById("input-resolver-codigo").value = codigo;
  document.getElementById("input-resolver-falla-id").value = fallaPendiente.id;
  document.getElementById("input-resolver-detalle").value = "";

  closeModal("detalle-equipo-modal");
  openModal("resolver-problema-modal");

  setTimeout(() => document.getElementById("input-resolver-detalle").focus(), 100);
}

async function confirmarResolucionProblema() {
  const codigo = document.getElementById("input-resolver-codigo").value;
  const fallaId = document.getElementById("input-resolver-falla-id").value;
  const detalleResolucion = document.getElementById("input-resolver-detalle").value;

  if (!detalleResolucion.trim()) {
    alert("Por favor, ingresa los detalles de cómo se resolvió la falla.");
    return;
  }

  try {
    await peticionAPI(`/fallas/${fallaId}/resolver`, "PATCH", {
      observacion_resolucion: detalleResolucion,
    });

    closeModal("resolver-problema-modal");
    mostrarMensajeEquipos(`El problema del equipo ${codigo} se ha marcado como resuelto.`, "success");
    cargarEquiposDesdeAPI();
  } catch (error) {
    closeModal("resolver-problema-modal");
    mostrarMensajeEquipos("No se pudo resolver el problema: " + (error.detail || "Error del servidor"), "danger");
  }
}

// ==========================================
// BAJA DE EQUIPOS
// ==========================================
function eliminarEquipo(codigo) {
  document.getElementById("eliminar-codigo-label").textContent = codigo;
  document.getElementById("input-eliminar-codigo").value = codigo;
  
  closeModal("detalle-equipo-modal"); 
  openModal("eliminar-equipo-modal");
}

async function confirmarEliminarEquipo() {
  const codigo = document.getElementById("input-eliminar-codigo").value;
  
  try {
    await peticionAPI(`/equipos/${codigo}/baja`, "PATCH");

    closeModal("eliminar-equipo-modal");
    cargarEquiposDesdeAPI();
    mostrarMensajeEquipos(`El equipo ${codigo} ha sido dado de baja exitosamente.`, "success");
  } catch (error) {
    closeModal("eliminar-equipo-modal");
    mostrarMensajeEquipos("No se pudo eliminar el equipo: " + (error.detail || "Error del servidor"), "danger");
  }
}

// ==========================================
// INICIALIZACIÓN
// ==========================================
document.addEventListener("DOMContentLoaded", () => {
  if (document.getElementById("equipment-table")) {
    iniciarInventario();
    cargarEquiposDesdeAPI();
    cargarTiposEquipo();
  }
});

// Avisos en vivo del servidor: se vuelven a pedir los datos.
document.addEventListener("labtrack:cambio", () => {
  cargarEquiposDesdeAPI();
  cargarTiposEquipo();
});