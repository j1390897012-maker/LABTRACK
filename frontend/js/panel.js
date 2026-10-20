// Panel principal: indicadores y fallas pendientes, siempre desde la API.
const KPI_CLAVES = ["total", "disponibles", "prestados", "en_revision"];

async function cargarPanel() {
  const error = document.getElementById("panel-error");
  try {
    const resumen = await peticionAPI("/equipos/resumen");
    error.hidden = true;

    KPI_CLAVES.forEach((clave) => {
      const kpi = document.querySelector(`.kpi[data-kpi="${clave}"]`);
      kpi.querySelector("[data-valor]").textContent = resumen[clave];
      // Texto accesible completo, p. ej. "Disponibles: 55. Ver en inventario."
      kpi.setAttribute(
        "aria-label",
        `${kpi.querySelector(".kpi-label").textContent}: ${resumen[clave]}. Ver en el inventario.`
      );
    });

    // Los cuatro indicadores no suman el total cuando hay equipos de baja:
    // se aclara para que las cifras cuadren.
    const nota = document.getElementById("panel-nota");
    const partes = [];
    if (resumen.baja) {
      partes.push(
        `<a href="#/equipos?estado=Baja">${resumen.baja} de baja</a>`
      );
    }
    if (resumen.otros) partes.push(`${resumen.otros} con otro estado`);
    nota.hidden = partes.length === 0;
    nota.innerHTML = partes.length
      ? `El total incluye ${partes.join(" y ")}.`
      : "";
  } catch (e) {
    error.hidden = false;
    error.textContent = `No se pudieron cargar los indicadores. ${mensajeError(e)}`;
  }
  cargarFallasPendientes();
}

async function cargarFallasPendientes() {
  const contenedor = document.getElementById("panel-fallas");
  try {
    const fallas = await peticionAPI("/fallas?estado=Pendiente");
    if (fallas.length === 0) {
      contenedor.innerHTML = `
        <div class="state-box">
          <p class="state-title">Sin fallas pendientes</p>
          <p class="state-text">Todos los reportes están resueltos.</p>
        </div>`;
      return;
    }
    const filas = fallas.slice(0, 8).map((f) => `
      <tr>
        <td data-label="Equipo"><span class="code">${esc(f.codigo_equipo)}</span></td>
        <td data-label="Tipo">${esc(f.tipo_equipo)}</td>
        <td data-label="Falla">${esc(f.descripcion)}</td>
        <td data-label="Reportada">${f.fecha ? esc(new Date(f.fecha).toLocaleDateString("es-MX")) : "—"}</td>
        <td class="td-actions">
          <button class="button button-secondary button-small" type="button"
                  data-codigo="${esc(f.codigo_equipo)}"
                  aria-label="Ver detalle del equipo ${esc(f.codigo_equipo)}">Detalle</button>
        </td>
      </tr>`).join("");
    const resto = fallas.length - 8;
    contenedor.innerHTML = `
      <div class="table-wrapper">
        <table class="table-inv">
          <thead><tr><th>Equipo</th><th>Tipo</th><th>Falla</th><th>Reportada</th><th><span class="sr-only">Acciones</span></th></tr></thead>
          <tbody>${filas}</tbody>
        </table>
      </div>
      ${resto > 0 ? `<p class="kpi-note table-foot">Y ${resto} más. Filtra el inventario por «En revisión» para verlas.</p>` : ""}`;
  } catch (e) {
    contenedor.innerHTML = `
      <div class="state-box">
        <p class="state-title">No se pudieron cargar las fallas</p>
        <p class="state-text">${esc(mensajeError(e))}</p>
        <button class="button button-secondary" type="button" onclick="cargarFallasPendientes()">Reintentar</button>
      </div>`;
  }
}

document.addEventListener("DOMContentLoaded", () => {
  cargarPanel();
  document.getElementById("panel-fallas").addEventListener("click", (e) => {
    const boton = e.target.closest("button[data-codigo]");
    if (boton) showEquipment(boton.dataset.codigo);
  });
});

document.addEventListener("labtrack:cambio", cargarPanel);
