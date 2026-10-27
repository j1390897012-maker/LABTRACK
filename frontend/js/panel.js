// Panel principal: indicadores con contador animado y bloques por categoría.
// Los datos siguen viniendo de la API (/equipos/resumen y el inventario).
const KPI_CLAVES = ["total", "disponibles", "prestados", "en_revision"];

async function cargarPanel() {
  const error = document.getElementById("panel-error");
  try {
    const resumen = await peticionAPI("/equipos/resumen");
    error.hidden = true;

    KPI_CLAVES.forEach((clave) => {
      const kpi = document.querySelector(`.kpi[data-kpi="${clave}"]`);
      animarNumero(kpi.querySelector("[data-valor]"), resumen[clave]);
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
      partes.push(`<a href="#/equipos?estado=Baja">${resumen.baja} de baja</a>`);
    }
    if (resumen.otros) partes.push(`${resumen.otros} con otro estado`);
    nota.hidden = partes.length === 0;
    nota.innerHTML = partes.length ? `El total incluye ${partes.join(" y ")}.` : "";
  } catch (e) {
    error.hidden = false;
    error.textContent = `No pudimos actualizar los indicadores. ${mensajeError(e)}`;
  }
}

// Una tarjeta por tipo de equipo; al tocarla se listan solo esos equipos.
function renderCategorias() {
  const cont = document.getElementById("panel-categorias");
  if (!cont || typeof inventario === "undefined") return;

  // Primera carga o error sin datos: pantalla de carga / error amable.
  if (inventario.datos.length === 0) {
    cont.innerHTML = inventario.error
      ? htmlErrorConexion("cargarEquiposDesdeAPI()", inventario.error)
      : htmlCargando("Cargando equipos…");
    return;
  }

  const grupos = {};
  inventario.datos.forEach((e) => {
    if (e.estado === "Baja") return;
    const g = (grupos[e.tipo] = grupos[e.tipo] || { total: 0, libres: 0, prestados: 0, revision: 0 });
    g.total += 1;
    if (e.estado === "Disponible") g.libres += 1;
    else if (e.estado === "Prestado") g.prestados += 1;
    else if (e.estado === "En revisión") g.revision += 1;
  });

  const tipos = Object.keys(grupos).sort((a, b) => grupos[b].total - grupos[a].total);
  const flecha = `<span class="cat-go"><svg viewBox="0 0 24 24"><path d="M5 12h14M13 6l6 6-6 6"/></svg></span>`;

  const todas = `
    <a class="cat-card cat-all" href="#/equipos" style="--i:0">
      ${flecha}
      <div class="cat-art">${iconoEquipo("generico")}</div>
      <div class="cat-name">Todo el inventario</div>
      <div class="cat-meta">${inventario.datos.length} equipos</div>
    </a>`;

  cont.innerHTML = todas + tipos.map((tipo, i) => {
    const g = grupos[tipo];
    // En lugar de una barra, cifras con el mismo color que sus estados.
    const etiquetas = [
      `<span class="tag tag-ok">${g.libres} disponibles</span>`,
      g.prestados ? `<span class="tag tag-use">${g.prestados} prestados</span>` : "",
      g.revision ? `<span class="tag tag-rev">${g.revision} en revisión</span>` : "",
    ].join("");
    return `
      <a class="cat-card" href="#/equipos?tipo=${encodeURIComponent(tipo)}" style="--i:${Math.min(i + 1, 14)}">
        ${flecha}
        <div class="cat-art">${iconoEquipo(tipo)}</div>
        <div class="cat-name">${esc(tipo)}</div>
        <div class="cat-meta">${g.total} equipos</div>
        <div class="cat-tags">${etiquetas}</div>
      </a>`;
  }).join("");
}

document.addEventListener("DOMContentLoaded", () => {
  renderCategorias(); // muestra "Cargando equipos…" hasta que lleguen los datos
  cargarPanel();
});
document.addEventListener("labtrack:inventario", renderCategorias);
document.addEventListener("labtrack:cambio", cargarPanel);