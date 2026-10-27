// ============================================================
// CAPA VISUAL (solo presentación: no toca la lógica de negocio)
// - Intro animada
// - Menú hamburguesa
// - Íconos / ilustraciones SVG por tipo de equipo
// - Pestañas de operación manual, chips de filtro, contadores animados
// ============================================================

// ---------- Intro animada ----------
(function () {
  const splash = document.getElementById("splash");
  if (!splash) return;

  const reducir = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  let terminada = false;

  function terminar() {
    if (terminada) return;
    terminada = true;
    splash.classList.add("out");
    document.body.classList.remove("intro");
    document.body.classList.add("ready");
    setTimeout(() => splash.remove(), 1000);
  }

  splash.addEventListener("click", terminar);
  setTimeout(terminar, reducir ? 0 : 3600);
})();

// ---------- Menú hamburguesa ----------
(function () {
  const burger = document.getElementById("burger");
  const overlay = document.getElementById("drawer-overlay");
  if (!burger) return;

  function abrir(abierto) {
    document.body.classList.toggle("drawer-open", abierto);
    burger.setAttribute("aria-expanded", String(abierto));
    burger.setAttribute("aria-label", abierto ? "Cerrar menú" : "Abrir menú");
  }

  burger.addEventListener("click", () =>
    abrir(!document.body.classList.contains("drawer-open"))
  );
  overlay.addEventListener("click", () => abrir(false));
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") abrir(false);
  });
  // Al elegir una sección el menú se cierra solo.
  document.querySelectorAll(".nav-button").forEach((b) =>
    b.addEventListener("click", () => abrir(false))
  );
  window.addEventListener("hashchange", () => abrir(false));
})();

// ---------- Ilustraciones de equipos (SVG en línea) ----------
const SVG_EQUIPOS = {
  osciloscopio: `
    <rect x="5" y="9" width="54" height="40" rx="6" class="f"/>
    <rect x="10" y="14" width="33" height="27" rx="3" class="s"/>
    <path d="M10 27.5h33M26.5 14v27" class="g"/>
    <path d="M11 28c3-9 5-9 8 0s5 9 8 0 5-9 8 0 3 5 7 2" class="a"/>
    <circle cx="51" cy="21" r="3.2" class="s"/><circle cx="51" cy="32" r="3.2" class="s"/>
    <path d="M47 41h8" class="s"/><path d="M16 54h32" class="s"/>`,
  generador: `
    <rect x="5" y="13" width="54" height="36" rx="6" class="f"/>
    <rect x="10" y="18" width="25" height="13" rx="2.5" class="s"/>
    <path d="M12 25c2-6 4-6 6 0s4 6 6 0 4-6 6 0" class="a"/>
    <circle cx="47" cy="25" r="7.5" class="s"/><path d="M47 25l3.5-4" class="a"/>
    <circle cx="14" cy="41" r="2.6" class="s"/><circle cx="23" cy="41" r="2.6" class="s"/>
    <circle cx="32" cy="41" r="2.6" class="s"/><circle cx="49" cy="41" r="3.4" class="s"/>`,
  multimetro: `
    <rect x="17" y="5" width="30" height="54" rx="6" class="f"/>
    <rect x="22" y="10" width="20" height="13" rx="2.5" class="s"/>
    <path d="M26 19v-5h4v5M34 14h4v5h-4z" class="a"/>
    <circle cx="32" cy="38" r="9" class="s"/><path d="M32 38l5-5" class="a"/>
    <circle cx="24" cy="53" r="2.2" class="s"/><circle cx="32" cy="53" r="2.2" class="s"/><circle cx="40" cy="53" r="2.2" class="s"/>`,
  fuente: `
    <rect x="5" y="14" width="54" height="36" rx="6" class="f"/>
    <rect x="10" y="19" width="19" height="10" rx="2" class="s"/><rect x="33" y="19" width="19" height="10" rx="2" class="s"/>
    <path d="M13 26v-4h4v4M36 26v-4h4v4" class="a"/>
    <circle cx="18" cy="40" r="4.2" class="s"/><circle cx="35" cy="40" r="4.2" class="s"/>
    <circle cx="50" cy="38" r="2.6" class="r"/><circle cx="50" cy="45" r="2.6" class="s"/>`,
  cautin: `
    <g transform="rotate(-35 32 32)">
      <rect x="4" y="27" width="26" height="10" rx="5" class="f"/>
      <path d="M11 29.5v5M16 29.5v5M21 29.5v5" class="s"/>
      <rect x="30" y="29" width="5" height="6" rx="1" class="s"/>
      <rect x="35" y="30" width="14" height="4" rx="2" class="s"/>
      <path d="M49 30l9 2-9 2z" class="a"/>
    </g>
    <path d="M57 8c-2 3 2 4 0 7M51 5c-2 3 2 4 0 7" class="a"/>
    <path d="M8 56h24" class="s"/>`,
  generico: `
    <rect x="17" y="17" width="30" height="30" rx="5" class="f"/>
    <rect x="25" y="25" width="14" height="14" rx="2" class="a"/>
    <path d="M24 17v-7M32 17v-7M40 17v-7M24 54v-7M32 54v-7M40 54v-7M17 24h-7M17 32h-7M17 40h-7M54 24h-7M54 32h-7M54 40h-7" class="s"/>`,
};

function claveIcono(tipo) {
  const t = String(tipo || "")
    .normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
  if (t.includes("osciloscop")) return "osciloscopio";
  if (t.includes("generador")) return "generador";
  if (t.includes("multimetro")) return "multimetro";
  if (t.includes("fuente")) return "fuente";
  if (t.includes("cautin") || t.includes("soldad")) return "cautin";
  return "generico";
}

// Devuelve el SVG del equipo. Si existe una foto real en
// assets/equipos/<clave>.png se puede sustituir cambiando esta función.
function iconoEquipo(tipo, clase = "") {
  const clave = claveIcono(tipo);
  return `<svg class="eq-svg eq-${clave} ${clase}" viewBox="0 0 64 64" aria-hidden="true">${SVG_EQUIPOS[clave]}</svg>`;
}

// ---------- Contadores animados ----------
function animarNumero(el, destino) {
  if (!el) return;
  const fin = Number(destino) || 0;
  const reducir = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const inicio = Number(el.dataset.actual || 0);
  el.dataset.actual = fin;
  if (reducir || inicio === fin) { el.textContent = fin; return; }
  const dur = 900;
  const t0 = performance.now();
  (function paso(t) {
    const p = Math.min(1, (t - t0) / dur);
    const e = 1 - Math.pow(1 - p, 3);
    el.textContent = Math.round(inicio + (fin - inicio) * e);
    if (p < 1) requestAnimationFrame(paso);
  })(t0);
}

// ---------- Pestañas: operación manual ----------
document.addEventListener("click", (e) => {
  const btn = e.target.closest(".seg-btn");
  if (!btn) return;
  const cont = btn.closest(".manual");
  cont.querySelectorAll(".seg-btn").forEach((b) => b.classList.toggle("active", b === btn));
  cont.querySelectorAll(".manual-panel").forEach((p) =>
    p.classList.toggle("active", p.dataset.panel === btn.dataset.tab)
  );
});

// ---------- Chips de estado (sincronizan con el <select> oculto) ----------
document.addEventListener("click", (e) => {
  const chip = e.target.closest("#inv-chips .chip");
  if (!chip) return;
  const select = document.getElementById("inv-estado");
  select.value = chip.dataset.estado;
  select.dispatchEvent(new Event("change"));
});

// Lo llama renderInventario() para mantener chips y título al día.
function sincronizarVistaEquipos() {
  if (typeof inventario === "undefined") return;
  document.querySelectorAll("#inv-chips .chip").forEach((c) =>
    c.classList.toggle("active", c.dataset.estado === inventario.estado)
  );
  const titulo = document.getElementById("equipos-titulo");
  const volver = document.getElementById("equipos-volver");
  if (titulo) titulo.textContent = inventario.tipo || "Equipos";
  if (volver) volver.hidden = !inventario.tipo;
}

// Con equipos por prestar, el botón final pasa a decir «Prestar equipos (N)».
function etiquetarBotonOperacion(pendientes) {
  const b = document.getElementById("btn-terminar-operacion");
  if (!b) return;
  b.textContent = pendientes > 0 ? `Prestar equipos (${pendientes})` : "Terminar operación";
  b.classList.toggle("pulse-btn", pendientes > 0);
}


// ============================================================
// ESTADOS DE CARGA, ERROR Y CONEXIÓN
// ============================================================

// Pantalla de carga con la marca (para listas que aún no llegan).
function htmlCargando(texto = "Cargando…") {
  return `
    <div class="loader" role="status" aria-live="polite">
      <div class="loader-mark"><span class="loader-ring"></span><b>L</b></div>
      <p>${texto}</p>
    </div>`;
}

// Estado de error amable con botón de reintentar. `reintentar` es el nombre
// de una función global, p. ej. "cargarEquiposDesdeAPI()".
function htmlErrorConexion(reintentar, mensaje) {
  return `
    <div class="state-box state-error" role="alert">
      <div class="state-ico">
        <svg viewBox="0 0 24 24"><path d="M3 3l18 18"/><path d="M9.5 5.6A7 7 0 0 1 19 12h.5a3.5 3.5 0 0 1 1.9 6.4M6 18a4 4 0 0 1-.6-7.9"/></svg>
      </div>
      <p class="state-title">No pudimos cargar la información</p>
      <p class="state-text">${mensaje || "Revisa tu conexión e inténtalo de nuevo."} Tus datos están a salvo.</p>
      <button class="button button-primary" type="button" onclick="${reintentar}">Reintentar</button>
    </div>`;
}

(function () {
  let activas = 0;
  let tLento = null;
  let tMuyLento = null;
  let reintento = null;
  let caida = false;

  // Elementos flotantes: aviso de carga lenta y banner de conexión.
  const pill = document.createElement("div");
  pill.id = "net-pill";
  pill.setAttribute("role", "status");
  pill.innerHTML = `<span class="loader-mark mini"><span class="loader-ring"></span><b>L</b></span><span class="net-text">Conectando con el servidor…</span>`;
  const banner = document.createElement("div");
  banner.id = "net-banner";
  banner.setAttribute("role", "alert");
  banner.innerHTML = `<span class="net-msg">Problemas de conexión. Reintentando automáticamente…</span><button type="button" class="button button-small">Reintentar ahora</button>`;
  document.addEventListener("DOMContentLoaded", () => {
    document.body.append(pill, banner);
    banner.querySelector("button").addEventListener("click", () =>
      document.dispatchEvent(new CustomEvent("labtrack:cambio", { detail: { origen: "manual" } }))
    );
  });

  const texto = pill.querySelector(".net-text");

  // Una petición empezó: si tarda, se avisa (sin bloquear la pantalla).
  window.redInicio = function () {
    activas += 1;
    if (activas === 1) {
      tLento = setTimeout(() => {
        texto.textContent = "Conectando con el servidor…";
        pill.classList.add("show");
      }, 1800);
      tMuyLento = setTimeout(() => {
        texto.textContent = "El servidor está tardando más de lo normal. Seguimos intentando…";
      }, 7000);
    }
  };

  window.redFin = function () {
    activas = Math.max(0, activas - 1);
    if (activas === 0) {
      clearTimeout(tLento);
      clearTimeout(tMuyLento);
      pill.classList.remove("show");
    }
  };

  // ok = false cuando no hay red o el servidor falla (5xx).
  window.redEstado = function (ok) {
    if (ok === !caida) return;
    caida = !ok;
    document.body.classList.toggle("net-down", caida);
    clearInterval(reintento);
    if (caida) {
      // Reintenta solo cada 8 s; las vistas ya escuchan este evento.
      reintento = setInterval(() =>
        document.dispatchEvent(new CustomEvent("labtrack:cambio", { detail: { origen: "reintento" } })), 8000);
    }
  };

  window.addEventListener("offline", () => {
    banner.querySelector(".net-msg").textContent = "Sin conexión a internet. Se reanudará al volver la red.";
    window.redEstado(false);
  });
  window.addEventListener("online", () => {
    banner.querySelector(".net-msg").textContent = "Problemas de conexión. Reintentando automáticamente…";
    document.dispatchEvent(new CustomEvent("labtrack:cambio", { detail: { origen: "online" } }));
  });
})();