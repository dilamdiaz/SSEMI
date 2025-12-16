// frontend/static/comite.js

// ------------------- COMITÉ NACIONAL -------------------
if (typeof apiFetch === 'undefined') console.warn('apiFetch not loaded. Ensure /js/api.js is included before this script.');
const busquedaComite = document.getElementById("busquedaComite");
const filtroComiteEstado = document.getElementById("filtroComiteEstado");
let evaluadoresCache = [];

// Escucha los filtros
busquedaComite.addEventListener("input", mostrarEvaluadoresComite);
filtroComiteEstado.addEventListener("change", mostrarEvaluadoresComite);

// Función para cargar evaluadores desde la API
async function cargarEvaluadoresComite() {
    try {
        evaluadoresCache = await apiFetch('/comite-nacional/');
        mostrarEvaluadoresComite();
    } catch (e) {
        console.error("Error al cargar evaluadores:", e);
        alert("Error al cargar evaluadores del Comité Nacional");
    }
}

// Función para mostrar la tabla filtrada
function mostrarEvaluadoresComite() {
    const term = busquedaComite.value.toLowerCase();
    const estadoFiltro = filtroComiteEstado.value;

    const filtrados = evaluadoresCache.filter(e => {
        const nombreCompleto = `${e.primer_nombre} ${e.segundo_nombre || ''} ${e.primer_apellido} ${e.segundo_apellido || ''}`.toLowerCase();
        const correo = e.correo.toLowerCase();
        const estado = e.comite_nacional.toString();

        const busquedaMatch = nombreCompleto.includes(term) || correo.includes(term);
        const estadoMatch = estadoFiltro ? estado === estadoFiltro : true;

        return busquedaMatch && estadoMatch;
    });

    const tbody = document.querySelector("#comiteTable tbody");
    tbody.innerHTML = "";

    filtrados.forEach(e => {
        const nombreCompleto = `${e.primer_nombre} ${e.segundo_nombre || ''} ${e.primer_apellido} ${e.segundo_apellido || ''}`;
        const estadoComite = e.comite_nacional ? "Sí" : "No";

        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td>${e.id_usuario}</td>
            <td>${nombreCompleto}</td>
            <td>${e.correo}</td>
            <td>${estadoComite}</td>
            <td class="text-center">
                ${e.comite_nacional 
                    ? `<button class="btn btn-sm btn-danger" onclick="desactivarEvaluador(${e.id_usuario})">Desactivar</button>` 
                    : `<button class="btn btn-sm btn-success" onclick="activarEvaluador(${e.id_usuario})">Activar</button>`}
            </td>
        `;
        tbody.appendChild(tr);
    });
}

// Función para activar evaluador
async function activarEvaluador(id_usuario) {
    try {
        await apiFetch(`/comite-nacional/${id_usuario}/activar`, 'PUT');
        alert("✅ Evaluador activado en Comité Nacional");
        cargarEvaluadoresComite();
    } catch (e) {
        console.error("Error al activar evaluador:", e);
        alert("❌ Error al activar evaluador");
    }
}

// Función para desactivar evaluador
async function desactivarEvaluador(id_usuario) {
    try {
        await apiFetch(`/comite-nacional/${id_usuario}/desactivar`, 'PUT');
        alert("✅ Evaluador desactivado en Comité Nacional");
        cargarEvaluadoresComite();
    } catch (e) {
        console.error("Error al desactivar evaluador:", e);
        alert("❌ Error al desactivar evaluador");
    }
}

document.addEventListener('DOMContentLoaded', () => {
    cargarEvaluadoresComite(); // tu función de comite.js
});
