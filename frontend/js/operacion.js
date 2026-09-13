// ============================================================
// ESTADO DEL FLUJO RFID / QR
// ============================================================

let sesionActual = null;

let equiposOperacion = [];

let ultimoScanVisto = null;

let uidPendienteEnrolar = null;


// ============================================================
// OPERACIÓN MANUAL
// ============================================================

async function prestarEquipoManual() {

  const matricula = document
    .getElementById("manual-prestamo-matricula")
    .value
    .trim();

  const codigo = document
    .getElementById("manual-prestamo-codigo")
    .value
    .trim();

  const resultado = document.getElementById(
    "manual-prestamo-resultado"
  );

  if (!matricula || !codigo) {

    resultado.innerHTML = `
      <div class="card stat-card"
           style="border-left: 4px solid var(--danger);">
        <div class="stat-description"
             style="color: var(--text);">
          Debes proporcionar la matrícula y el código
          del equipo.
        </div>
      </div>
    `;

    return;
  }

  try {

    // Primero buscamos la sesión activa del estudiante.
    const sesion = await peticionAPI(
      `/sesiones/activa?matricula=${encodeURIComponent(matricula)}`
    );

    // Después buscamos el equipo por código.
    const equipo = await peticionAPI(
      `/equipos/${encodeURIComponent(codigo)}`
    );

    const respuesta = await peticionAPI(
      `/sesiones/${sesion.sesion_id}/equipos`,
      "POST",
      {
        equipo_id: equipo.id,
        accesorios: [],
      }
    );

    resultado.innerHTML = `
      <div class="card stat-card"
           style="border-left: 4px solid var(--success);">

        <div class="stat-label">
          Préstamo registrado
        </div>

        <div class="stat-description"
             style="color: var(--text);">

          ${respuesta.mensaje || "Préstamo registrado correctamente."}

        </div>

      </div>
    `;

    document.getElementById(
      "manual-prestamo-matricula"
    ).value = "";

    document.getElementById(
      "manual-prestamo-codigo"
    ).value = "";

  } catch (error) {

    resultado.innerHTML = `
      <div class="card stat-card"
           style="border-left: 4px solid var(--danger);">

        <div class="stat-label">
          No se pudo registrar el préstamo
        </div>

        <div class="stat-description"
             style="color: var(--text);">

          ${error.detail || "Ocurrió un error."}

        </div>

      </div>
    `;

  }

}


async function devolverEquipoManual() {

  const codigo = document
    .getElementById("manual-devolucion-codigo")
    .value
    .trim();

  const resultado = document.getElementById(
    "manual-devolucion-resultado"
  );

  if (!codigo) {

    resultado.innerHTML = `
      <div class="card stat-card"
           style="border-left: 4px solid var(--danger);">

        <div class="stat-description"
             style="color: var(--text);">

          Debes proporcionar el código del equipo.

        </div>

      </div>
    `;

    return;
  }

  try {

    const respuesta = await peticionAPI(
      "/devoluciones",
      "POST",
      {
        codigo_equipo: codigo,
      }
    );

    resultado.innerHTML = `
      <div class="card stat-card"
           style="border-left: 4px solid var(--success);">

        <div class="stat-label">
          Devolución iniciada
        </div>

        <div class="stat-description"
             style="color: var(--text);">

          ${respuesta.mensaje || "Devolución iniciada correctamente."}

        </div>

      </div>
    `;

    document.getElementById(
      "manual-devolucion-codigo"
    ).value = "";

  } catch (error) {

    resultado.innerHTML = `
      <div class="card stat-card"
           style="border-left: 4px solid var(--danger);">

        <div class="stat-label">
          No se pudo iniciar la devolución
        </div>

        <div class="stat-description"
             style="color: var(--text);">

          ${error.detail || "Ocurrió un error."}

        </div>

      </div>
    `;

  }

}


// ============================================================
// MODAL DE SIMULACIÓN (RFID)
// ============================================================

function simularRFID() {

  openModal("rfid-modal");

  setTimeout(() => {

    const input = document.getElementById(
      "input-rfid-simulado"
    );

    if (input) {
      input.focus();
    }

  }, 100);

}


async function procesarRFID() {

  const input = document.getElementById(
    "input-rfid-simulado"
  );

  const uid = input.value.trim();

  if (!uid) {
    return;
  }

  closeModal("rfid-modal");

  input.value = "";

  await procesarScan("rfid", uid);

}


// ============================================================
// PROCESAMIENTO DE SCAN
// ============================================================

async function procesarScan(tipo, valor) {

  try {

    const data = await peticionAPI(
      "/identificaciones/scan",
      "POST",
      {
        tipo,
        valor,
      }
    );

    if (tipo === "rfid") {

      await manejarRespuestaRFID(
        valor,
        data
      );

      return;
    }

    if (tipo === "qr") {

      await manejarRespuestaQR(data);

    }

  } catch (error) {

    mostrarResultadoRFID(
      "Error: " +
      (error.detail || "No se pudo procesar el escaneo.")
    );

  }

}


// ============================================================
// RFID
// ============================================================

async function manejarRespuestaRFID(valor, data) {

  if (data.estado === "no_registrado") {

    // Tarjeta no registrada: se abre el modal de
    // enrolamiento en vez del prompt() nativo.

    abrirEnrolamientoRFID(valor);

    return;
  }


  // Guardar sesión actual

  sesionActual = {

    sesion_id: data.sesion_id,

    matricula: data.matricula,

    nombre: data.nombre,

  };


  // Reiniciar equipos de la operación

  equiposOperacion = [];


  // Abrir automáticamente la vista RFID

  abrirVistaPrestamoRFID();


  // Mostrar estudiante

  mostrarEstudianteRFID(data);


  // Estado

  actualizarEstadoRFID(
    "RFID detectada",
    "Listo para prestar equipos."
  );


  // Mostrar pantalla esperando QR

  const esperandoQR = document.getElementById(
    "rfid-flow-esperando-qr"
  );

  if (esperandoQR) {
    esperandoQR.hidden = false;
  }


  mostrarResultadoRFID(
    `${data.nombre} (${data.matricula}) — ${data.mensaje || "Estudiante identificado correctamente."}`
  );

}


// ============================================================
// MOSTRAR ESTUDIANTE
// ============================================================

function mostrarEstudianteRFID(data) {

  const contenedor = document.getElementById(
    "rfid-flow-estudiante"
  );

  if (!contenedor) {
    return;
  }

  contenedor.hidden = false;


  const nombre = document.getElementById(
    "rfid-flow-nombre"
  );

  const matricula = document.getElementById(
    "rfid-flow-matricula"
  );

  const sesion = document.getElementById(
    "rfid-flow-sesion"
  );


  if (nombre) {
    nombre.textContent =
      data.nombre || "—";
  }

  if (matricula) {
    matricula.textContent =
      data.matricula || "—";
  }

  if (sesion) {
    sesion.textContent =
      data.sesion_id
        ? `Sesión #${data.sesion_id}`
        : "Sin sesión";
  }

}


// ============================================================
// ESTADO DE LA VISTA RFID
// ============================================================

function actualizarEstadoRFID(
  estado,
  subtitulo
) {

  const badge = document.getElementById(
    "rfid-flow-badge"
  );

  const status = document.getElementById(
    "rfid-flow-status"
  );

  const subtitle = document.getElementById(
    "rfid-flow-subtitle"
  );


  if (badge) {

    badge.innerHTML = `
      <span class="status-dot"></span>
      ${estado}
    `;

  }

  if (status) {
    status.textContent = subtitulo;
  }

  if (subtitle) {
    subtitle.textContent = subtitulo;
  }

}


// ============================================================
// RESULTADO DEL FLUJO RFID
// ============================================================

function mostrarResultadoRFID(texto) {

  const el = document.getElementById(
    "rfid-flow-resultado"
  );

  if (!el) {
    return;
  }

  el.innerHTML = `
    <div class="card stat-card"
         style="
           border-left: 4px solid var(--primary);
           margin-top: 20px;
         ">

      <div class="stat-description"
           style="
             color: var(--text);
             font-size: 14px;
           ">

        ${texto}

      </div>

    </div>
  `;

}


// ============================================================
// QR
// ============================================================

async function manejarRespuestaQR(data) {

  // Si todavía no existe una sesión,
  // el QR no puede iniciar el flujo normal.
  if (!sesionActual) {

    mostrarResultadoRFID(
      "Se detectó un QR, pero primero debes identificar al estudiante mediante RFID."
    );

    return;
  }


  // ----------------------------------------------------------
  // EQUIPO EN REVISIÓN
  // ----------------------------------------------------------

  if (data.accion === "revisar_fallas") {

    const fallas = (data.fallas || [])
      .map((f) => f.descripcion)
      .join("; ");


    agregarEquipoOperacion({
      codigo: data.codigo,
      tipo: data.tipo,
      estado: "En revisión",
      accion: "revisar_fallas",
    });


    mostrarResultadoRFID(
      `${data.codigo} está EN REVISIÓN. Fallas registradas: ${fallas || "sin descripción"}`
    );

    actualizarEstadoRFID(
      "Equipo en revisión",
      "El encargado debe decidir si desea prestar el equipo."
    );

    return;
  }


  // ----------------------------------------------------------
  // DEVOLUCIÓN
  // ----------------------------------------------------------

  if (data.accion === "iniciar_devolucion") {

    agregarEquipoOperacion({
      codigo: data.codigo,
      tipo: data.tipo,
      estado: data.estado || "Prestado",
      accion: "iniciar_devolucion",
    });


    mostrarResultadoRFID(
      `${data.codigo}: préstamo activo de ${data.prestamo?.estudiante?.nombre || "un estudiante"}.`
    );

    actualizarEstadoRFID(
      "Devolución",
      "El equipo corresponde a una devolución."
    );

    return;
  }


  // ----------------------------------------------------------
  // CONFIRMAR PRÉSTAMO
  // ----------------------------------------------------------

  if (data.accion === "confirmar_prestamo") {

    const estudiantes =
      data.estudiantes || [];


    const esSesionActual =
      sesionActual &&
      estudiantes.some(
        (e) =>
          e.matricula === sesionActual.matricula
      );


    agregarEquipoOperacion({
      codigo: data.codigo,
      tipo: data.tipo,
      estado: data.estado || "Disponible",
      equipo_id: data.equipo_id,
      accion: "confirmar_prestamo",
    });


    if (esSesionActual) {

      await registrarPrestamo(
        sesionActual.sesion_id,
        data
      );

      return;
    }


    mostrarResultadoRFID(
      `${data.codigo}: ${data.mensaje || "Equipo listo para préstamo."}`
    );

    return;
  }


  // ----------------------------------------------------------
  // SELECCIONAR ESTUDIANTE
  // ----------------------------------------------------------

  if (data.accion === "seleccionar_estudiante") {

    await seleccionarEstudianteYPrestar(
      data
    );

    return;
  }


  // ----------------------------------------------------------
  // RESPUESTA GENÉRICA
  // ----------------------------------------------------------

  agregarEquipoOperacion({
    codigo: data.codigo,
    tipo: data.tipo,
    estado: data.estado,
    equipo_id: data.equipo_id,
    accion: data.accion,
  });


  mostrarResultadoRFID(
    `${data.codigo || "Equipo"}: ${
      data.mensaje || "Operación procesada."
    }`
  );

}


// ============================================================
// AGREGAR EQUIPO A LA VISTA
// ============================================================

function agregarEquipoOperacion(data) {

  equiposOperacion.push(data);


  const contenedor = document.getElementById(
    "rfid-flow-equipos"
  );

  const lista = document.getElementById(
    "rfid-flow-equipo-list"
  );


  if (!contenedor || !lista) {
    return;
  }


  contenedor.hidden = false;


  lista.innerHTML = equiposOperacion
    .map((equipo, index) => {

      return `
        <div
          class="operation-context"
          style="margin-bottom: 12px;"
        >

          <div class="operation-context-header">

            <div>

              <div class="info-item-label">
                Equipo
              </div>

              <div class="operation-student-name">
                ${equipo.codigo || "—"}
              </div>

            </div>


            <div>

              <div class="info-item-label">
                Tipo
              </div>

              <div class="operation-student-data">
                ${equipo.tipo || "—"}
              </div>

            </div>


            <div>

              <div class="info-item-label">
                Estado
              </div>

              <div>
                ${equipo.estado || "—"}
              </div>

            </div>

          </div>

        </div>
      `;

    })
    .join("");

}


// ============================================================
// SELECCIÓN DE ESTUDIANTE
// ============================================================

async function seleccionarEstudianteYPrestar(data) {

  const estudiantes =
    data.estudiantes || [];


  if (
    sesionActual &&
    estudiantes.some(
      (e) =>
        e.matricula === sesionActual.matricula
    )
  ) {

    await registrarPrestamo(
      sesionActual.sesion_id,
      data
    );

    return;
  }


  const opciones = estudiantes
    .map(
      (e, i) =>
        `${i + 1}. ${e.nombre} (${e.matricula})`
    )
    .join("\n");


  const seleccion = prompt(
    `Varias sesiones activas. Elige el número del estudiante:\n${opciones}`
  );


  const elegido =
    estudiantes[Number(seleccion) - 1];


  if (!elegido) {

    mostrarResultadoRFID(
      "Selección inválida. No se registró el préstamo."
    );

    return;
  }


  try {

    const sesion = await peticionAPI(
      `/sesiones/activa?matricula=${encodeURIComponent(
        elegido.matricula
      )}`
    );


    await registrarPrestamo(
      sesion.sesion_id,
      data
    );

  } catch (error) {

    mostrarResultadoRFID(
      "Error al consultar la sesión: " +
      (error.detail || "desconocido")
    );

  }

}


// ============================================================
// REGISTRAR PRÉSTAMO
// ============================================================

async function registrarPrestamo(
  sesionId,
  dataEquipo
) {

  try {

    const resultado = await peticionAPI(
      "/equipos/prestar",
      "POST",
      {
        sesion_id: sesionId,

        equipo_id: dataEquipo.equipo_id,

        accesorios: [],
      }
    );


    mostrarResultadoRFID(
      `Préstamo registrado: ${
        resultado.codigo_equipo
      }. ${
        resultado.mensaje ||
        "Préstamo registrado correctamente."
      }`
    );


    actualizarEstadoRFID(
      "Préstamo registrado",
      "El equipo fue agregado a la sesión."
    );


    if (sesionActual) {

      // El equipo ya quedó registrado.
      // No borramos el estudiante ni la sesión
      // porque pueden agregarse más equipos.

    }

  } catch (error) {

    mostrarResultadoRFID(
      "Error al registrar el préstamo: " +
      (
        error.detail ||
        "No se pudo procesar."
      )
    );

  }

}


// ============================================================
// CANCELAR FLUJO RFID
// ============================================================

function cancelarFlujoRFID() {

  const confirmar = confirm(
    "¿Deseas cancelar la operación RFID actual?"
  );

  if (!confirmar) {
    return;
  }


  sesionActual = null;

  equiposOperacion = [];


  // Limpiar vista

  const estudiante =
    document.getElementById(
      "rfid-flow-estudiante"
    );

  const esperando =
    document.getElementById(
      "rfid-flow-esperando-qr"
    );

  const equipos =
    document.getElementById(
      "rfid-flow-equipos"
    );

  const resultado =
    document.getElementById(
      "rfid-flow-resultado"
    );


  if (estudiante) {
    estudiante.hidden = true;
  }

  if (esperando) {
    esperando.hidden = true;
  }

  if (equipos) {
    equipos.hidden = true;
  }

  if (resultado) {
    resultado.innerHTML = "";
  }


  const lista =
    document.getElementById(
      "rfid-flow-equipo-list"
    );

  if (lista) {
    lista.innerHTML = "";
  }


  regresarDesdePrestamoRFID();

}


// ============================================================
// ENROLAMIENTO RFID (modal — tarjeta no registrada)
// ============================================================

function abrirEnrolamientoRFID(uid) {

  uidPendienteEnrolar = uid;


  const inputUid = document.getElementById(
    "enrolar-rfid-uid"
  );

  const inputMatricula = document.getElementById(
    "input-enrolar-matricula"
  );

  const resultado = document.getElementById(
    "enrolar-rfid-resultado"
  );


  if (inputUid) {
    inputUid.value = uid;
  }

  if (inputMatricula) {
    inputMatricula.value = "";
  }

  if (resultado) {
    resultado.innerHTML = "";
  }


  openModal("enrolar-rfid-modal");


  setTimeout(() => {

    if (inputMatricula) {
      inputMatricula.focus();
    }

  }, 100);

}


async function confirmarEnrolamientoRFID() {

  const matricula = document
    .getElementById("input-enrolar-matricula")
    .value
    .trim();

  const resultado = document.getElementById(
    "enrolar-rfid-resultado"
  );

  if (!matricula) {

    if (resultado) {
      resultado.textContent =
        "Ingresa la matrícula del estudiante.";
    }

    return;
  }

  await enrolarRFID(
    uidPendienteEnrolar,
    matricula
  );

  closeModal("enrolar-rfid-modal");

}


// ============================================================
// ENROLAR RFID
// ============================================================

async function enrolarRFID(
  uid,
  matricula
) {

  try {

    const data = await peticionAPI(
      "/identificaciones/enrolar",
      "POST",
      {
        tipo: "rfid",
        valor: uid,
        matricula,
      }
    );


    // Después de enrolar no iniciamos
    // automáticamente un préstamo.
    // Mostramos el resultado.

    const vistaActual =
      obtenerVistaActiva();


    if (vistaActual !== "prestamo-rfid") {
      abrirVistaPrestamoRFID();
    }


    mostrarResultadoRFID(
      `RFID enrolado a ${data.nombre} (${data.matricula}).`
    );

  } catch (error) {

    mostrarResultadoRFID(
      "Error al enrolar: " +
      (error.detail || "desconocido")
    );

  }

}


// ============================================================
// POLLING DE ESCANEOS EN VIVO
// ============================================================

async function revisarUltimoScan() {

  try {

    const evento = await peticionAPI(
      "/identificaciones/ultimo-scan"
    );


    if (
      !evento.timestamp ||
      evento.timestamp === ultimoScanVisto
    ) {
      return;
    }


    ultimoScanVisto =
      evento.timestamp;


    if (evento.tipo === "rfid") {

      await manejarRespuestaRFID(
        evento.datos.uid_rfid,
        evento.datos
      );

    } else if (evento.tipo === "qr") {

      await manejarRespuestaQR(
        evento.datos
      );

    }

  } catch (error) {

    // El polling debe ser silencioso.
    // Si Render tarda o falla una petición,
    // no se interrumpe la interfaz.

  }

}


// ============================================================
// INICIAR POLLING
// ============================================================

setInterval(
  revisarUltimoScan,
  2500
);