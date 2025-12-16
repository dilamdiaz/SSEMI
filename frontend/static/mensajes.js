// ---------------- CONFIG ----------------
const API_BASE = "http://127.0.0.1:8000/mensajes";
const token = localStorage.getItem("ssemi_token");

// ---------------- STATE ----------------
let bandejaActual = "recibidos";
let mensajesCache = [];

// ---------------- INIT ----------------
document.addEventListener("DOMContentLoaded", () => {
    if (!token) {
        alert("Debe iniciar sesión");
        window.location.href = "/login";
        return;
    }

    cargarMensajes(bandejaActual);

    // Enviar mensaje
    document.getElementById("btnEnviarMensaje")
        .addEventListener("click", enviarMensaje);

    // Escuchar cambio de pestañas
    window.addEventListener("cambiarTab", (e) => {
        bandejaActual = e.detail;
        cargarMensajes(bandejaActual);
    });
});

// ---------------- CARGAR MENSAJES ----------------
async function cargarMensajes(tipo) {
    const lista = document.getElementById("listaMensajes");
    lista.innerHTML = `<div class="text-center text-muted py-3">Cargando mensajes...</div>`;

    const endpoint = tipo === "recibidos"
        ? `${API_BASE}/recibidos`
        : `${API_BASE}/enviados`;

    try {
        const resp = await fetch(endpoint, {
            headers: { "Authorization": `Bearer ${token}` }
        });

        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);

        mensajesCache = await resp.json();

        if (mensajesCache.length === 0) {
            lista.innerHTML = `
                <div class="empty-state d-flex flex-column align-items-center w-100 py-5">
                    <i class="bi bi-envelope-x-fill mb-3" style="font-size: 3rem; color: #ccc;"></i>
                    <p class="text-muted">No hay mensajes ${tipo}.</p>
                </div>
            `;
            return;
        }

        lista.innerHTML = "";
        mensajesCache.forEach(m => lista.appendChild(crearItemMensaje(m)));

    } catch (error) {
        console.error(error);
        lista.innerHTML = `<div class="text-danger text-center py-3">Error cargando datos</div>`;
    }
}

// ---------------- ITEM MENSAJE ----------------
function crearItemMensaje(m) {
    const div = document.createElement("div");
    div.classList.add("card", "mb-3", "shadow-sm");

    const leidoClass = (!m.leido && bandejaActual === "recibidos") ? "bg-light fw-bold" : "";

    div.innerHTML = `
        <div class="card-body ${leidoClass}">
            <div class="fw-bold">${m.asunto}</div>
            <div class="small text-muted">De: ${m.remitente_nombre || "Desconocido"}</div>
            <div class="small text-muted">${new Date(m.fecha_envio).toLocaleString()}</div>
        </div>
    `;

    div.addEventListener("click", () => abrirMensaje(m.id));
    return div;
}

// ---------------- ABRIR MENSAJE ----------------
async function abrirMensaje(id) {
    try {
        const resp = await fetch(`${API_BASE}/${id}`, {
            headers: { "Authorization": `Bearer ${token}` }
        });

        if (!resp.ok) throw new Error("Error al abrir mensaje");

        const m = await resp.json();

        document.getElementById("modalAsunto").innerText = m.asunto;
        document.getElementById("modalRemitente").innerText = m.remitente_nombre;
        document.getElementById("modalFecha").innerText = new Date(m.fecha_envio).toLocaleString();
        document.getElementById("modalContenido").innerText = m.contenido;

        // Mostrar modal
        window.modalLeerMensaje.show();

        // Recargar recibidos si corresponde
        if (bandejaActual === "recibidos") cargarMensajes("recibidos");

    } catch (err) {
        console.error(err);
        alert("Error al cargar mensaje");
    }
}

// ---------------- ENVIAR MENSAJE ----------------
async function enviarMensaje() {
    const destino_rol = document.getElementById("destinoRol").value;
    const asunto = document.getElementById("nuevoAsunto").value.trim();
    const contenido = document.getElementById("nuevoContenido").value.trim();

    if (!destino_rol || !asunto || !contenido) {
        alert("Todos los campos son obligatorios");
        return;
    }

    const payload = { destino_rol: Number(destino_rol), asunto, contenido };

    try {
        const resp = await fetch(API_BASE + "/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${token}`
            },
            body: JSON.stringify(payload)
        });

        if (!resp.ok) {
            const errorData = await resp.json();
            alert(errorData.detail || "Error enviando mensaje");
            return;
        }

        // Cerrar modal y limpiar campos
        window.modalRedactar.hide();
        document.getElementById("nuevoAsunto").value = "";
        document.getElementById("nuevoContenido").value = "";

        // Recargar enviados
        cargarMensajes("enviados");

    } catch (error) {
        console.error(error);
        alert("No se pudo enviar el mensaje");
    }
}
