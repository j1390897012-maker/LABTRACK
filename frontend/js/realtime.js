// Conexión en tiempo real con el backend (WebSocket /ws).
//
// El servidor avisa cuando algo cambió (préstamo, devolución, registro,
// importación...). Aquí solo se retransmite como el evento "labtrack:cambio"
// y cada vista vuelve a pedir sus datos. Si el socket se cae, se reintenta
// con espera creciente y mientras tanto se actualiza cada 30 s.
(function () {
  const estadoEl = document.getElementById("rt-status");
  const textoEl = estadoEl ? estadoEl.querySelector(".rt-text") : null;
  let socket = null;
  let intentos = 0;
  let reintento = null;
  let latido = null;
  let esperaPong = null;
  let respaldo = null;
  let debounce = null;

  function mostrar(estado, texto) {
    if (!estadoEl) return;
    estadoEl.dataset.estado = estado;
    textoEl.textContent = texto;
    estadoEl.title = {
      vivo: "Los cambios se reflejan al instante.",
      conectando: "Conectando con el servidor…",
      caido: "Reconectando con el servidor. Mientras tanto los datos se actualizan cada 30 segundos.",
    }[estado];
  }

  function notificar(detalle) {
    // Agrupa ráfagas de avisos (p. ej. una importación) en una sola actualización.
    clearTimeout(debounce);
    debounce = setTimeout(() => {
      document.dispatchEvent(new CustomEvent("labtrack:cambio", { detail: detalle }));
    }, 250);
  }

  function iniciarRespaldo() {
    if (respaldo) return;
    respaldo = setInterval(() => notificar({ origen: "sondeo" }), 30000);
  }

  function detenerRespaldo() {
    clearInterval(respaldo);
    respaldo = null;
  }

  function detenerLatido() {
    clearInterval(latido);
    clearTimeout(esperaPong);
  }

  function conectar() {
    clearTimeout(reintento);
    mostrar("conectando", "Conectando…");
    try {
      socket = new WebSocket(WS_URL);
    } catch (e) {
      programarReintento();
      return;
    }

    socket.onopen = () => {
      const eraReconexion = intentos > 0;
      intentos = 0;
      detenerRespaldo();
      mostrar("vivo", "En vivo");
      // Tras reconectar pudo haber cambios que no llegaron.
      if (eraReconexion) notificar({ origen: "reconexion" });
      detenerLatido();
      latido = setInterval(() => {
        if (socket.readyState !== WebSocket.OPEN) return;
        socket.send("ping");
        esperaPong = setTimeout(() => socket.close(), 10000);
      }, 25000);
    };

    socket.onmessage = (evento) => {
      if (evento.data === "pong") {
        clearTimeout(esperaPong);
        return;
      }
      try {
        const mensaje = JSON.parse(evento.data);
        if (mensaje.evento === "cambio") notificar(mensaje);
      } catch (e) { /* mensaje no reconocido: se ignora */ }
    };

    socket.onclose = () => {
      detenerLatido();
      programarReintento();
    };
    socket.onerror = () => socket.close();
  }

  function programarReintento() {
    mostrar("caido", "Reconectando…");
    iniciarRespaldo();
    intentos += 1;
    const espera = Math.min(30000, 1000 * 2 ** Math.min(intentos, 5));
    reintento = setTimeout(conectar, espera);
  }

  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "visible") notificar({ origen: "visible" });
  });

  conectar();
})();