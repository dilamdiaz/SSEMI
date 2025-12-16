// frontend/static/evaluador.js


// ======================================================
//  CONFIGURACIÓN GENERAL
// ======================================================
const API_BASE = "/evaluador";
let evidenciaSeleccionada = null;
let evaluacionModificada = false;
let historialGlobal = [];


// ======================================================
//  UTILIDADES
// ======================================================
function mostrarSeccion(id) {
    document.querySelectorAll("section").forEach(s => s.classList.add("hidden"));
    document.getElementById(id).classList.remove("hidden");
}

function cerrarSesion() {
    window.location.href = "/login";
}

async function safeFetch(url, options = {}) {
    try {
        // Añadir Authorization si existe token
        const token = localStorage.getItem("ssemi_token");
            options.headers = options.headers || {};
            if (token && !options.headers["Authorization"]) {
                options.headers["Authorization"] = `Bearer ${token}`;
            }

        const res = await fetch(url, options);
        if (!res.ok) throw new Error(`Error ${res.status}`);
        return await res.json();
    } catch (err) {
        console.error(err);
        alert("❌ No se pudo conectar con el servidor.");
        return [];
    }
}


// ======================================================
//  CARGAR EVIDENCIAS
// ======================================================
async function cargarEvidencias() {
    const evidencias = await safeFetch(`${API_BASE}/data/evidencias`);
    const tbody = document.querySelector("#tablaEvidencias tbody");
    tbody.innerHTML = "";

    if (evidencias.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" class="text-center">No hay evidencias pendientes.</td></tr>`;
        return;
    }

    evidencias.forEach(e => {
        const tr = document.createElement("tr");
        tr.setAttribute("data-id", e.id);

        tr.innerHTML = `
            <td>${e.id}</td>
            <td>${e.titulo}</td>
            <td>${e.fecha}</td>
            <td><span class="estado ${e.estado.toLowerCase()}">${e.estado}</span></td>
            <td><button class="btn btn-sm btn-primary btnEvaluar">Evaluar</button></td>
        `;

        // click en toda la fila
        tr.addEventListener("click", (ev) => {
            // evitar doble ejecución por el botón
            if (ev.target.classList.contains("btnEvaluar")) {
                ev.stopPropagation();
            }
            abrirEvaluacion(e.id);
        });

        tbody.appendChild(tr);
    });
}


// ======================================================
//  ABRIR EVALUACIÓN
// ======================================================
async function abrirEvaluacion(id) {
    evidenciaSeleccionada = id;
    mostrarSeccion("evaluar");

    const data = await safeFetch(`${API_BASE}/evidencia/${id}/avance`);

    document.getElementById("puntaje").value = data?.puntaje || "";
    document.getElementById("observacion").value = data?.observacion || "";

    if (data?.puntaje || data?.observacion) {
        alert("ℹ️ Se cargó un avance parcial anterior.");
    }

    await cargarEvidenciaDetalle(id);
}


// ======================================================
//  CARGAR DATOS DE LA EVIDENCIA COMPLETA
// ======================================================
async function cargarEvidenciaDetalle(id) {
    try {
        const resp = await fetch(`/evidencias/detalle/${id}`);
        if (!resp.ok) throw new Error("Evidencia no encontrada");
        const data = await resp.json();

        // Limpiar contenedores
        const camposContainer = document.getElementById("camposUsuario");
        const archivosContainer = document.getElementById("archivosUsuario");
        camposContainer.innerHTML = "";
        archivosContainer.innerHTML = "";

        // Mostrar formulario si existe
        if (data.formulario) {
            for (const [key, value] of Object.entries(data.formulario)) {
                const div = document.createElement("div");
                div.className = "mb-2";
                div.innerHTML = `<strong>${key}:</strong> ${value}`;
                camposContainer.appendChild(div);
            }
        } else {
            camposContainer.innerHTML = "<em>No hay formulario enviado por el instructor.</em>";
        }

        // Mostrar archivos
        if (data.archivos && data.archivos.length > 0) {
            data.archivos.forEach(f => {
                const li = document.createElement("li");
                li.className = "list-group-item";
                li.innerHTML = `<a href="${f.url}" target="_blank">${f.nombre}</a>`;
                archivosContainer.appendChild(li);
            });
        } else {
            archivosContainer.innerHTML = "<li class='list-group-item'><em>No hay archivos subidos.</em></li>";
        }

    } catch (error) {
        console.error("Error cargando detalle de evidencia:", error);
    }
}



// ======================================================
//  GUARDAR EVALUACIÓN
// ======================================================
document.getElementById("formEvaluacion")?.addEventListener("submit", async e => {
    e.preventDefault();

    const formData = new FormData(e.target);

    const token = localStorage.getItem("ssemi_token");
    if (!token) return alert("❌ No autenticado. Inicia sesión para calificar evidencias.");

    const res = await fetch(`${API_BASE}/evidencia/${evidenciaSeleccionada}`, {
        method: "POST",
        body: formData,
        headers: {
            "Authorization": `Bearer ${token}`
        }
    });

    if (!res.ok) {
        const errorText = await res.text();
        alert(`❌ Error al enviar: ${errorText}`);
        return;
    }

    const data = await res.json();
    alert(data.message);

    mostrarSeccion("panel");
    cargarEvidencias();
});



// ======================================================
//  GUARDAR AVANCE PARCIAL
// ======================================================
async function guardarAvanceParcial() {
    const formData = new FormData(document.getElementById("formEvaluacion"));

    const token = localStorage.getItem("ssemi_token");
    if (!token) return alert("❌ No autenticado. Inicia sesión para guardar avances.");

    const res = await fetch(`${API_BASE}/evidencia/${evidenciaSeleccionada}/parcial`, {
        method: "POST",
        body: formData,
        headers: {
            "Authorization": `Bearer ${token}`
        }
    });

    if (!res.ok) return alert("❌ Error guardando avance parcial.");

    const data = await res.json();
    alert(data.message);
    evaluacionModificada = false;
}


// ======================================================
//  HISTORIAL
// ======================================================
async function cargarHistorial() {
    historialGlobal = await safeFetch(`${API_BASE}/data/historial`);
    renderizarHistorial(historialGlobal);
}

// Función para renderizar cualquier array de historial en la tabla
function renderizarHistorial(data) {
    const tbody = document.querySelector("#tablaHistorial tbody");
    tbody.innerHTML = "";

    if (data.length === 0) {
        tbody.innerHTML = `<tr><td colspan="4" class="text-center">No hay calificaciones registradas</td></tr>`;
        return;
    }

    data.forEach(c => {
        tbody.innerHTML += `
            <tr>
                <td>${c.id}</td>
                <td>${c.puntaje}</td>
                <td>${c.fecha}</td>
                <td>${c.estado}</td>
            </tr>
        `;
    });
}

// Función que aplica los filtros seleccionados en frontend
function aplicarFiltrosHistorial() {
    const idFiltro = document.getElementById("filtroHistID").value.trim();
    const puntajeFiltro = document.getElementById("filtroHistPuntaje").value.trim();
    const fechaFiltro = document.getElementById("filtroHistFecha").value.trim();
    const estadoFiltro = document.getElementById("filtroHistEstado").value;

    // Mapear estados de la BD a los valores del select
    const estadoMap = {
        "evaluada": "aprobado",
        "borrador": "rechazado",
        "cargada": "en_progreso"
    };

    let filtrado = historialGlobal;

    if (idFiltro) {
        filtrado = filtrado.filter(c => c.id.toString().includes(idFiltro));
    }

    if (puntajeFiltro) {
        filtrado = filtrado.filter(c => c.puntaje == parseFloat(puntajeFiltro));
    }

    if (fechaFiltro) {
        filtrado = filtrado.filter(c => c.fecha.startsWith(fechaFiltro));
    }

    if (estadoFiltro) {
    filtrado = filtrado.filter(c => c.estado === estadoFiltro);
}

    renderizarHistorial(filtrado);
}

// =======================================
// FILTROS AUTOMÁTICOS
// =======================================
document.getElementById("filtroHistID").addEventListener("input", aplicarFiltrosHistorial);
document.getElementById("filtroHistPuntaje").addEventListener("input", aplicarFiltrosHistorial);
document.getElementById("filtroHistFecha").addEventListener("change", aplicarFiltrosHistorial);
document.getElementById("filtroHistEstado").addEventListener("change", aplicarFiltrosHistorial);


// ======================================================
//  CARGAR INSTRUCTORES
// ======================================================
async function cargarInstructores() {
    const instructores = await safeFetch(`${API_BASE}/evaluador/instructores`);
    const select = document.getElementById("filtroInstructor");

    select.innerHTML = '<option value="">Todos</option>';

    instructores.forEach(i => {
        if (i.rol_fk === 1) {
            const opt = document.createElement("option");
            opt.value = i.id_usuario;
            opt.textContent = `${i.primer_nombre} ${i.primer_apellido}`;
            select.appendChild(opt);
        }
    });
}


// ======================================================
//  RESULTADOS FILTRADOS
// ======================================================
async function generarResultados() {
    const instructor = document.getElementById("filtroInstructor").value;
    const fecha = document.getElementById("fechaFiltro").value;
    const puntaje = document.getElementById("puntajeFiltro").value;

    const params = new URLSearchParams();
    if (instructor) params.append("instructor_id", instructor);
    if (fecha) params.append("fecha_desde", fecha);
    if (puntaje) params.append("puntaje", puntaje);

    const resultados = await safeFetch(`${API_BASE}/evaluador/resultados?${params.toString()}`);
    const tbody = document.querySelector("#tablaResultados tbody");
    tbody.innerHTML = "";

    if (resultados.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6" class="text-center">No hay resultados</td></tr>`;
        return;
    }

    resultados.forEach(r => {
        tbody.innerHTML += `
            <tr>
                <td>${r.evidencia}</td>
                <td>${r.instructor}</td>
                <td>${r.evaluador_id}</td>
                <td>${r.puntaje}</td>
                <td>${r.observaciones || ""}</td>
                <td>${r.fecha}</td>
            </tr>
        `;
    });
}


// ======================================================
//  EXPORTACIONES
// ======================================================
function exportarExcel() {
    const table = document.getElementById("tablaResultados");
    const wb = XLSX.utils.table_to_book(table, { sheet: "Resultados" });
    XLSX.writeFile(wb, "resultados.xlsx");
}

function exportarPDF() {
    const { jsPDF } = window.jspdf;
    const doc = new jsPDF();
    doc.autoTable({ html: "#tablaResultados" });
    doc.save("resultados.pdf");
}



// ======================================================
//  INICIALIZACIÓN
// ======================================================
cargarEvidencias();
cargarHistorial();
cargarInstructores();
mostrarSeccion("panel");
