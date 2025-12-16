// frontend/static/register.js

document.addEventListener("DOMContentLoaded", () => {

  const form = document.getElementById("registerForm");
  const msgEl = document.getElementById("registerMessage");

  const rolSelect = document.getElementById("rol_fk");
  const gradoRow = document.getElementById("grado_row");
  const claveRow = document.getElementById("clave_access_row");

  const API_BASE = API_URL;
  const LOGIN_URL = "/login";

  function showMessage(msg, isError = true) {
    msgEl.textContent = msg;
    msgEl.style.color = isError ? "red" : "green";
  }

  // ────────────────────────────────────────────────
  // MOSTRAR U OCULTAR CAMPOS SEGÚN EL ROL
  // ────────────────────────────────────────────────
  rolSelect.addEventListener("change", () => {

    const rol = parseInt(rolSelect.value);

    // Si es Instructor → mostrar GRADO
    if (rol === 1) {
      gradoRow.style.display = "block";
    } else {
      gradoRow.style.display = "none";
      document.getElementById("grado").value = ""; // limpiar
    }

    // Si no es Instructor → mostrar clave de acceso
    if (rol !== 1) {
      claveRow.style.display = "block";
    } else {
      claveRow.style.display = "none";
      document.getElementById("clave_acceso").value = ""; // limpiar
    }
  });

  // ────────────────────────────────────────────────
  // ENVÍO DEL FORMULARIO
  // ────────────────────────────────────────────────
  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    // Validación de contraseña confirmada
    const pass = document.getElementById("contraseña").value;
    const passConfirm = document.getElementById("confirmar_contraseña").value;

    if (pass !== passConfirm) {
      showMessage("❌ Las contraseñas no coinciden");
      return;
    }

    const rol = parseInt(rolSelect.value);

    const data = {
      primer_nombre: document.getElementById("primer_nombre").value.trim(),
      segundo_nombre: document.getElementById("segundo_nombre").value.trim() || null,
      primer_apellido: document.getElementById("primer_apellido").value.trim(),
      segundo_apellido: document.getElementById("segundo_apellido").value.trim(),
      tipo_documento: document.getElementById("tipo_documento").value,
      numero_documento: parseInt(document.getElementById("numero_documento").value),
      correo: document.getElementById("correo").value.trim(),
      rol_fk: rol,
      contraseña: pass,
      numero_contacto: null,
      direccion: null,
      clave_acceso: rol !== 1
        ? (document.getElementById("clave_acceso").value.trim() || null)
        : null,
      grado: rol === 1
        ? document.getElementById("grado").value || null
        : null,
      regional: document.getElementById("regional").value || null
    };

    // Validación mínima
    if (!data.primer_nombre ||
        !data.primer_apellido ||
        !data.segundo_apellido ||
        !data.tipo_documento ||
        !data.numero_documento ||
        !data.correo ||
        !data.rol_fk ||
        !data.contraseña) {

      showMessage("⚠️ Complete todos los campos obligatorios");
      return;
    }

    try {
      const resp = await fetch(`${API_BASE}/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data)
      });

      const result = await resp.json();

      if (!resp.ok) {
        const detail = Array.isArray(result.detail)
          ? result.detail.map(d => d.msg || d.message).join(", ")
          : result.detail || result.message || "Error al registrar";
        showMessage(`❌ ${detail}`);
        return;
      }

      showMessage("✅ Usuario registrado correctamente", false);
      form.reset();

      // Mostrar modal de éxito si existe
      const modalEl = document.getElementById('registroExitoso');
      if (modalEl) {
        const modal = new bootstrap.Modal(modalEl);
        modal.show();

        setTimeout(() => {
          modal.hide();
          window.location.href = LOGIN_URL;
        }, 2500);

      } else {
        setTimeout(() => window.location.href = LOGIN_URL, 1500);
      }

    } catch (err) {
      console.error(err);
      showMessage("❌ Error de conexión con el servidor");
    }
  });
});
