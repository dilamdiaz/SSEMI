const API_BASE = "http://127.0.0.1:8000";

/* ========= UTILIDADES ========= */
function onlySoySena(email) { return /@soy\.sena\.edu\.co$/i.test(email); }

function showMessage(el, msg, isError = true) {
  if (!el) return;
  el.textContent = msg;
  el.classList.remove("success", "error", "info");
  el.style.display = "block";
  el.classList.add(isError ? "error" : "success");
}

function clearMessage(el) {
  if (!el) return;
  el.textContent = "";
  el.style.display = "none";
  el.classList.remove("success", "error", "info");
}

function parseError(data) {
  if (!data) return "Error desconocido";
  if (typeof data === "string") return data;
  if (data.detail) {
    if (Array.isArray(data.detail))
      return data.detail.map(d => d.msg || d.message || JSON.stringify(d)).join(", ");
    return String(data.detail);
  }
  if (data.message) return String(data.message);
  if (data.msg) return String(data.msg);
  if (Array.isArray(data)) return data.map(v => String(v)).join(", ");
  try { return Object.values(data).map(v => String(v)).join(", "); }
  catch { return "Error desconocido"; }
}

function showLoading() { document.getElementById("loadingOverlay")?.classList.add("active"); }
function hideLoading() { document.getElementById("loadingOverlay")?.classList.remove("active"); }
function setSubmitDisabled(form, disabled = true) {
  const submit = form?.querySelector('button[type="submit"]');
  if (!submit) return;
  submit.disabled = disabled;
  submit.classList.toggle("disabled", disabled);
}

function removeResidualBackdrop() {
  document.querySelectorAll('.modal-backdrop').forEach(el => el.remove());
}

/* ========= DOM READY ========= */
document.addEventListener("DOMContentLoaded", () => {

  // Animaciones globales, estas sí se pueden ejecutar siempre
  const title = document.querySelector('.card-title');
  if (title) {
    title.style.opacity = '0';
    setTimeout(() => {
      title.style.transition = 'opacity 0.5s ease';
      title.style.opacity = '1';
    }, 200);
  }

  document.querySelectorAll('.input-row input').forEach(input => {
    const parent = input.parentElement;
    input.addEventListener('focus', () => parent.style.transform = 'scale(1.02)');
    input.addEventListener('blur', () => parent.style.transform = 'scale(1)');
    input.addEventListener('input', () => {
      if (input.checkValidity() && input.value.trim() !== "")
        parent.classList.add('valid');
      else
        parent.classList.remove('valid');
    });
  });

  /* ====================================================
     TODO EL CÓDIGO DEL LOGIN/2FA SOLO SE EJECUTA EN /login
     ==================================================== */
  if (window.location.pathname === "/login") {

    const loginForm = document.getElementById("loginForm");
    const msgEl = document.getElementById("loginMessage");

    const modalEl = document.getElementById("modal2FA");
    const input2FA = document.getElementById("input2FACode");
    const message2FA = document.getElementById("message2FA");
    const btnVerify2FA = document.getElementById("btnVerify2FA");

    let modal2FA = null;
    if (modalEl) {
      modal2FA = new bootstrap.Modal(modalEl, {
        backdrop: 'static',
        keyboard: false
      });

      modalEl.addEventListener('shown.bs.modal', () => {
        input2FA?.focus();
      });
    }

    let pendingCorreo = null;

    async function verify2FACode(correo, codigo) {
      showLoading();
      try {
        const resp = await fetch(`${API_BASE}/2fa/verify`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ correo, codigo })
        });

        const data = await resp.json().catch(() => null);
        hideLoading();

        if (!resp.ok) {
          showMessage(message2FA, `❌ ${parseError(data)}`, true);
          return null;
        }

        if (data?.access_token) {
          localStorage.setItem("ssemi_token", data.access_token);
          localStorage.setItem("user_role", String(data.rol ?? ""));
          localStorage.setItem("user_id", String(data.user_id ?? ""));
        }

        return data;

      } catch {
        hideLoading();
        showMessage(message2FA, "❌ Error al conectar", true);
        return null;
      }
    }

    if (btnVerify2FA) {
      btnVerify2FA.addEventListener("click", async () => {
        clearMessage(message2FA);

        const code = input2FA?.value?.trim();
        if (!code || code.length !== 6)
          return showMessage(message2FA, "Ingrese el código de 6 dígitos");

        if (!pendingCorreo)
          return showMessage(message2FA, "Correo no disponible");

        setSubmitDisabled(loginForm, true);
        const result = await verify2FACode(pendingCorreo, code);
        setSubmitDisabled(loginForm, false);

        if (result?.access_token) {
          modal2FA?.hide();
          showMessage(msgEl, "✅ Verificación correcta, redirigiendo...", false);
          setTimeout(() => redirectByRole(), 800);
        }
      });
    }

    if (loginForm) {
      loginForm.addEventListener("submit", async (e) => {
        e.preventDefault();

        clearMessage(msgEl);

        const correo = document.getElementById("loginCorreo")?.value?.trim();
        const contraseña = document.getElementById("loginPassword")?.value;

        if (!onlySoySena(correo))
          return showMessage(msgEl, "⚠️ Use correo @soy.sena.edu.co");

        if ((contraseña || "").length < 6)
          return showMessage(msgEl, "⚠️ Contraseña mínima 6 caracteres");

        setSubmitDisabled(loginForm, true);
        showLoading();

        try {
          const resp = await fetch(`${API_BASE}/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ correo, contraseña })
          });

          const data = await resp.json().catch(() => null);
          hideLoading();
          setSubmitDisabled(loginForm, false);

          if (!resp.ok) {
            showMessage(msgEl, `❌ ${parseError(data)}`, true);
            return;
          }

          pendingCorreo = correo;

          if (data?.access_token) {
            localStorage.setItem("ssemi_token", data.access_token);
            localStorage.setItem("user_role", String(data.rol ?? ""));
            localStorage.setItem("user_id", String(data.user_id ?? ""));
            showMessage(msgEl, "Iniciando...", false);
            return setTimeout(() => redirectByRole(), 500);
          }

          input2FA.value = "";
          modal2FA?.show();
          removeResidualBackdrop();

        } catch {
          hideLoading();
          setSubmitDisabled(loginForm, false);
          showMessage(msgEl, "❌ Error al conectar");
        }
      });
    }

    function redirectByRole() {
      const role = parseInt(localStorage.getItem("user_role") || "0");
      if (role === 1) return location.href = "/instructor";
      if (role === 2) return location.href = "/admin";
      if (role === 3) return location.href = "/evaluador";
      location.href = "/dashboard";
    }

    modalEl?.addEventListener("hidden.bs.modal", () => {
      input2FA.value = "";
      clearMessage(message2FA);
    });

    input2FA?.addEventListener("keydown", e => {
      if (e.key === "Enter") {
        e.preventDefault();
        btnVerify2FA?.click();
      }
    });
  } // FIN DEL BLOQUE /login
});


/* ========= REGISTRO ========= */
async function registerUser(form) {
  const msgEl = document.getElementById("registerMessage");
  if (!form) return;

  const data = {
    primer_nombre: form.querySelector("#primerNombre")?.value.trim(),
    segundo_nombre: form.querySelector("#segundoNombre")?.value.trim(),
    primer_apellido: form.querySelector("#primerApellido")?.value.trim(),
    segundo_apellido: form.querySelector("#segundoApellido")?.value.trim(),
    tipo_documento: form.querySelector("#tipoDocumento")?.value,
    numero_documento: form.querySelector("#numeroDocumento")?.value.trim(),
    correo: form.querySelector("#correo")?.value.trim(),
    rol_fk: parseInt(form.querySelector("#rolFk")?.value),
    contrasena: form.querySelector("#contrasena")?.value,
    clave_acceso: form.querySelector("#claveAcceso")?.value
  };

  try {
    const resp = await fetch(`${API_BASE}/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data)
    });

    const out = await resp.json().catch(() => null);

    if (!resp.ok) return showMessage(msgEl, `❌ ${parseError(out)}`, true);

    showMessage(msgEl, "Registro exitoso, redirigiendo...", false);
    setTimeout(() => location.href = "/login", 1200);

  } catch {
    showMessage(msgEl, "❌ Error al conectar", true);
  }
}
