// Carga masiva desde archivo. Flujo: elegir archivo → Validar (no guarda)
// → Importar (guarda todo o nada).
const IMPORTACIONES = {
  equipos: { endpoint: "/equipos/importar", etiqueta: "equipos" },
  estudiantes: { endpoint: "/estudiantes/importar", etiqueta: "estudiantes" },
};
const MAX_ERRORES_VISIBLES = 100;

function iniciarImportacion(tarjeta) {
  const tipo = tarjeta.dataset.importacion;
  const { endpoint, etiqueta } = IMPORTACIONES[tipo];
  const entrada = tarjeta.querySelector("input[type=file]");
  const botonValidar = tarjeta.querySelector("[data-accion=validar]");
  const botonImportar = tarjeta.querySelector("[data-accion=importar]");
  const resultado = tarjeta.querySelector(".import-resultado");
  let validado = false; // el archivo actual ya pasó la validación sin errores

  function mostrar(html, clase = "") {
    resultado.className = `import-resultado ${clase}`.trim();
    resultado.innerHTML = html;
  }

  function ocupado(enCurso, textoBoton) {
    botonValidar.disabled = enCurso || !entrada.files[0];
    botonImportar.disabled = enCurso || !validado;
    if (enCurso) mostrar(`<p class="import-estado">${esc(textoBoton)}</p>`);
  }

  function resumen(r, conservar) {
    const partes = [
      `${r.total_filas} fila${r.total_filas === 1 ? "" : "s"} leída${r.total_filas === 1 ? "" : "s"}`,
      `${r.creados} nuevo${r.creados === 1 ? "" : "s"}`,
      `${r.actualizados} por actualizar`,
    ];
    if (r.fallas_creadas) partes.push(`${r.fallas_creadas} falla${r.fallas_creadas === 1 ? "" : "s"} pendiente${r.fallas_creadas === 1 ? "" : "s"}`);
    return `<p class="import-estado"><strong>${esc(conservar)}</strong> ${esc(partes.join(" · "))}.</p>`;
  }

  function tablaErrores(errores) {
    const visibles = errores.slice(0, MAX_ERRORES_VISIBLES);
    return `
      <div class="table-wrapper">
        <table class="table-inv">
          <thead><tr><th>Fila</th><th>Valor</th><th>Problema</th></tr></thead>
          <tbody>${visibles.map((e) => `
            <tr><td data-label="Fila">${e.fila}</td><td data-label="Valor">${esc(e.valor ?? "—")}</td><td data-label="Problema">${esc(e.motivo)}</td></tr>`).join("")}
          </tbody>
        </table>
      </div>
      ${errores.length > visibles.length ? `<p class="kpi-note">Y ${errores.length - visibles.length} errores más.</p>` : ""}`;
  }

  async function ejecutar(dryRun) {
    const archivo = entrada.files[0];
    if (!archivo) return;
    ocupado(true, dryRun ? "Validando archivo…" : "Importando…");
    try {
      const r = await subirArchivoAPI(endpoint, archivo, { dry_run: dryRun });
      if (r.errores.length) {
        validado = false;
        mostrar(
          `<p class="import-estado"><strong>No se guardó nada.</strong> Corrige ${r.errores.length} fila${r.errores.length === 1 ? "" : "s"} del archivo y vuelve a validarlo.</p>${tablaErrores(r.errores)}`,
          "import-error"
        );
      } else if (dryRun) {
        validado = true;
        mostrar(`${resumen(r, "Archivo válido.")}<p class="field-help">Revisa las cifras y pulsa «Importar» para guardar.</p>`, "import-ok");
      } else {
        validado = false;
        mostrar(resumen(r, `Importación completada de ${etiqueta}.`), "import-ok");
        entrada.value = "";
        mostrarMensajeEquipos(`Importación de ${etiqueta} completada.`, "success");
      }
    } catch (e) {
      validado = false;
      mostrar(`<p class="import-estado"><strong>No se pudo procesar el archivo.</strong> ${esc(mensajeError(e))}</p>`, "import-error");
    }
    ocupado(false);
  }

  entrada.addEventListener("change", () => {
    validado = false;
    resultado.innerHTML = "";
    resultado.className = "import-resultado";
    botonValidar.disabled = !entrada.files[0];
    botonImportar.disabled = true;
  });
  botonValidar.addEventListener("click", () => ejecutar(true));
  botonImportar.addEventListener("click", () => ejecutar(false));
}

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".import-card").forEach(iniciarImportacion);
});
