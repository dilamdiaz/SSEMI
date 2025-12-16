(() => {

    // ======================================================
    // CONFIG
    // ======================================================
    const API_MENSAJES = `${API_URL}/admin/mensajes`;
    const getToken = () => localStorage.getItem("ssemi_token");

    let bandejaActual = "recibidos";
    let respuestaAId = null; // ID del mensaje al que se responde
    let mensajeActual = null; // Mensaje abierto en el modal

    // ======================================================
    // FORMAT DATE (robusto)
    // ======================================================
    function formatDate(dateStr) {
        if (!dateStr) return "—";
        const d = new Date(dateStr);
        if (!isNaN(d)) return d.toLocaleString("es-CO", { timeZone: "America/Bogota" });
        return String(dateStr);
    }

    // ======================================================
    // MOSTRAR TOAST (éxito o error)
    // ======================================================
    function mostrarToast(mensaje, tipo = "success") {
        const container = document.getElementById("toastContainer");
        if (!container) return;

        const toastEl = document.createElement("div");
        toastEl.className = `toast align-items-center text-white bg-${tipo} border-0`;
        toastEl.role = "alert";
        toastEl.ariaLive = "assertive";
        toastEl.ariaAtomic = "true";

        toastEl.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">${mensaje}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Cerrar"></button>
            </div>
        `;

        container.appendChild(toastEl);

        const bsToast = new bootstrap.Toast(toastEl, { delay: 4000 });
        bsToast.show();

        toastEl.addEventListener("hidden.bs.toast", () => toastEl.remove());
    }

    // ======================================================
    // INIT
    // ======================================================
    document.addEventListener("DOMContentLoaded", () => {

        if (!document.getElementById("mensajesSection")) return;

        const token = getToken();
        if (!token) {
            alert("Debe iniciar sesión");
            window.location.href = "/login";
            return;
        }

        cargarMensajes("recibidos");

        document.getElementById("tabRecibidos")
            ?.addEventListener("click", () => cambiarBandeja("recibidos"));

        document.getElementById("tabEnviados")
            ?.addEventListener("click", () => cambiarBandeja("enviados"));

        document.getElementById("btnRedactar")
            ?.addEventListener("click", () => abrirModalRedactar());

        document.getElementById("btnEnviarMensaje")
            ?.addEventListener("click", enviarMensaje);

        document.getElementById("btnResponderModal")
            ?.addEventListener("click", () => abrirModalRedactar(mensajeActual.id));
    });

    // ======================================================
    // CAMBIAR BANDEJA
    // ======================================================
    function cambiarBandeja(bandeja) {
        bandejaActual = bandeja;

        document.querySelectorAll("#tabsMensajes .nav-link")
            .forEach(tab => tab.classList.remove("active"));

        document.getElementById(bandeja === "recibidos" ? "tabRecibidos" : "tabEnviados")
            ?.classList.add("active");

        cargarMensajes(bandeja);
    }

    // ======================================================
    // CARGAR MENSAJES
    // ======================================================
    async function cargarMensajes(bandeja) {
        const lista = document.getElementById("listaMensajes");
        if (!lista) return;

        lista.innerHTML = `<div class="text-center py-3">Cargando mensajes...</div>`;

        try {
            const res = await fetch(`${API_MENSAJES}?bandeja=${bandeja}`, {
                headers: { "Authorization": `Bearer ${getToken()}` }
            });

            if (!res.ok) throw new Error("Error al cargar mensajes");

            let mensajes = await res.json();

            if (mensajes.length === 0) {
                lista.innerHTML = `<p class="text-center text-muted py-3">No hay mensajes en esta bandeja.</p>`;
                return;
            }

            mensajes.sort((a, b) => new Date(b.fecha_envio) - new Date(a.fecha_envio));

            lista.innerHTML = mensajes.map(m => `
                <div class="list-group-item d-flex justify-content-between align-items-start ${!m.leido ? "no-leido" : ""}">
                    <div class="mensaje-info" style="cursor:pointer;" onclick="window.__leerMensaje(${m.id})">
                        <div><strong>${m.asunto}</strong></div>
                        <div><small>De: ${m.remitente_nombre}</small></div>
                        <div><small>${formatDate(m.fecha_envio)}</small></div>
                    </div>
                </div>
            `).join("");

        } catch (err) {
            console.error(err);
            lista.innerHTML = `<p class="text-danger text-center">Error cargando mensajes.</p>`;
            mostrarToast("Error cargando mensajes", "danger");
        }
    }

    // ======================================================
    // VER MENSAJE
    // ======================================================
    async function verMensaje(id) {
        try {
            const res = await fetch(`${API_MENSAJES}/${id}`, {
                headers: { "Authorization": `Bearer ${getToken()}` }
            });

            if (!res.ok) throw new Error("No se pudo cargar el mensaje");

            const m = await res.json();
            mensajeActual = m;

            document.getElementById("modalAsunto").innerText = m.asunto;
            document.getElementById("modalRemitente").innerText = m.remitente_nombre;
            document.getElementById("modalFecha").innerText = formatDate(m.fecha_envio);
            document.getElementById("modalContenido").innerText = m.contenido;

            const btnResp = document.getElementById("btnResponderModal");
            if (m.remitente_id !== obtenerMiId()) {
                btnResp.style.display = "inline-block";
            } else {
                btnResp.style.display = "none";
            }

            new bootstrap.Modal(document.getElementById("modalLeerMensaje")).show();
            cargarMensajes(bandejaActual);

        } catch (err) {
            console.error(err);
            mostrarToast("Error mostrando mensaje", "danger");
        }
    }

    window.__leerMensaje = verMensaje;

    // ======================================================
    // ABRIR MODAL REDACTAR
    // ======================================================
    function abrirModalRedactar(respuestaId = null) {
        respuestaAId = respuestaId || null;

        document.getElementById("nuevoAsunto").value = respuestaAId ? `RE: ${mensajeActual.asunto}` : "";
        document.getElementById("nuevoContenido").value = "";

        const divDestino = document.getElementById("divDestino");
        if (respuestaAId) {
            divDestino.style.display = "none";
        } else {
            divDestino.style.display = "block";
        }

        new bootstrap.Modal(document.getElementById("modalRedactar")).show();
    }

    // ======================================================
    // ENVIAR MENSAJE
    // ======================================================
    async function enviarMensaje() {
        const asunto = document.getElementById("nuevoAsunto").value.trim();
        const contenido = document.getElementById("nuevoContenido").value.trim();

        if (!asunto || !contenido) {
            mostrarToast("Debe completar asunto y contenido", "danger");
            return;
        }

        let body = { asunto, contenido };

        if (respuestaAId) {
            body.respuesta_a_id = parseInt(respuestaAId);
            body.destino_id = mensajeActual.remitente_id; 
            body.destino_rol = 0; // valor dummy para backend
        } else {
            const destinoRol = document.getElementById("destinoRol").value;
            body.destino_rol = parseInt(destinoRol);
        }

        try {
            const res = await fetch(API_MENSAJES, {
                method: "POST",
                headers: {
                    "Authorization": `Bearer ${getToken()}`,
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(body)
            });

            if (!res.ok) {
                const errText = await res.text();
                mostrarToast("Error al enviar mensaje: " + errText, "danger");
                throw new Error(errText);
            }

            bootstrap.Modal.getInstance(document.getElementById("modalRedactar")).hide();
            cambiarBandeja("enviados");
            mostrarToast("Mensaje enviado correctamente ✅", "success");

        } catch (err) {
            console.error(err);
            mostrarToast("Error enviando mensaje", "danger");
        }
    }

    // ======================================================
    // OBTENER MI ID
    // ======================================================
    function obtenerMiId() {
        return parseInt(localStorage.getItem("ssemi_user_id"));
    }

})();
