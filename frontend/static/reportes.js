// frontend/static/reportes.js
(() => {
  const API_BASE = "http://127.0.0.1:8000/reportes";
  const token = localStorage.getItem("ssemi_token");

  if (!token) {
    console.warn("No token encontrado, redirigiendo a login");
    // window.location.href = "/login"; // opcional
  }

  // ----------------------
  // Toast notifications
  // ----------------------
  function toast(msg, type = "info") {
    const container = document.getElementById("toastContainer");
    if (!container) return console.log(msg);
    const div = document.createElement("div");
    div.className = `toast align-items-center text-bg-${type} border-0 show m-2`;
    div.innerHTML = `<div class="d-flex"><div class="toast-body">${msg}</div></div>`;
    container.appendChild(div);
    setTimeout(() => div.remove(), 3000);
  }

  // ----------------------
  // Cargar historial de reportes
  // ----------------------
  async function cargarHistorial() {
    try {
      const res = await fetch(`${API_BASE}/`, {
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (!res.ok) throw new Error("Error cargando historial de reportes");

      const data = await res.json();
      const tbody = document.querySelector("#tablaReportes tbody");
      tbody.innerHTML = "";

      data.forEach(r => {
        const id = r.id_reporte ?? r.id ?? "";
        const titulo = r.titulo ?? "";
        let tipo = r.tipo_reporte ?? r.tipo ?? "";
        // Normalizar el tipo para mostrarlo bonito
        if (tipo === "usuarios") tipo = "Usuarios";
        if (tipo === "evidencias") tipo = "Evidencias";
        if (tipo === "evaluaciones") tipo = "Evaluaciones";
        if (tipo === "solicitudes_correccion") tipo = "Solicitudes de Corrección";
        if (tipo === "actividad_general") tipo = "Actividad General";

        const fecha = r.fecha_generacion ?? "";

        tbody.innerHTML += `
          <tr>
            <td>${id}</td>
            <td>${titulo}</td>
            <td>${tipo}</td>
            <td>${fecha}</td>
            <td class="text-center">
              <button class="btn btn-sm btn-success" data-id="${id}" data-type="excel">Excel</button>
              <button class="btn btn-sm btn-danger" data-id="${id}" data-type="pdf">PDF</button>
            </td>
          </tr>
        `;
      });
    } catch (err) {
      console.error(err);
      toast("No se pudo cargar el historial", "danger");
    }
  }

  // ----------------------
  // Exportar Excel / PDF
  // ----------------------
  document.addEventListener("click", (e) => {
    const btn = e.target.closest("button[data-id]");
    if (!btn) return;

    const id = btn.getAttribute("data-id");
    const type = btn.getAttribute("data-type");
    if (!id) return;

    const url = `${API_BASE}/${id}/export/${type === "excel" ? "excel" : "pdf"}`;
    window.open(url, "_blank");
  });

  // ----------------------
  // Generar nuevo reporte
  // ----------------------
  async function generarReporte() {
    const tipo = document.getElementById("selectTipoReporte").value;
    const titulo = document.getElementById("inputTitulo").value.trim();

    if (!tipo || !titulo) {
      toast("Seleccione tipo de reporte y título", "warning");
      return;
    }

    // Convertir a minúsculas para que coincida con el backend
    const tipoBackend = tipo.toLowerCase().replace(/\s+/g, "_");

    try {
      const resp = await fetch(`${API_BASE}/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({ titulo, descripcion: "", tipo_reporte: tipoBackend })
      });

      if (!resp.ok) {
        const txt = await resp.text();
        console.error("Error creando reporte", resp.status, txt);
        toast("Error creando reporte", "danger");
        return;
      }

      const data = await resp.json();
      toast("Reporte creado correctamente", "success");
      cargarHistorial();
    } catch (err) {
      console.error(err);
      toast("Error de conexión", "danger");
    }
  }

  // ----------------------
  // Inicialización al cargar la página
  // ----------------------
  document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("btnGenerarReporte")?.addEventListener("click", generarReporte);
    document.getElementById("btnExportExcel")?.addEventListener("click", () => toast("Use los botones del historial para descargar", "info"));
    document.getElementById("btnExportPDF")?.addEventListener("click", () => toast("Use los botones del historial para descargar", "info"));
    cargarHistorial();
  });

  // ----------------------
  // Exponer funciones globalmente para debug o pruebas
  // ----------------------
  window.cargarHistorialReportes = cargarHistorial;
  window.generarReporteFrontend = generarReporte;
})();
