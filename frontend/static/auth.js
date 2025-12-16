// Verificar estado de autenticación
if (typeof apiFetch === 'undefined') console.warn('apiFetch not loaded. Ensure /js/api.js is included before this script.');
console.log('Verificando sesión activa...');

async function verificarAuth() {
  const token = localStorage.getItem('ssemi_token');
  if (!token) {
    console.log('No se encontró una sesión activa');
    mostrarMensajeError('Por favor inicie sesión nuevamente');
    setTimeout(() => window.location.href = '/login', 1500);
    return false;
  }

    try {
    console.log('Verificando permisos de usuario...');
    const user = await apiFetch('/auth/me');
    console.log('Sesión verificada correctamente:', {
      usuario: user.primer_nombre + ' ' + user.primer_apellido,
      rol: user.rol_fk === 1 ? 'Instructor' : user.rol_fk === 2 ? 'Administrador' : 'Evaluador'
    });
    return true;
  } catch (error) {
    console.error('Error durante la verificación de sesión:', error);
    localStorage.removeItem('ssemi_token');
    mostrarMensajeError('Ocurrió un error al verificar su sesión. Por favor inicie sesión nuevamente.');
    setTimeout(() => window.location.href = '/login', 1500);
    return false;
  }
}

// Función auxiliar para mostrar mensajes de error
function mostrarMensajeError(mensaje) {
  const div = document.createElement('div');
  div.style.cssText = `
    position: fixed;
    top: 20px;
    left: 50%;
    transform: translateX(-50%);
    background-color: #ffe6e6;
    color: #b10000;
    padding: 15px 30px;
    border-radius: 6px;
    box-shadow: 0 2px 6px rgba(0,0,0,0.2);
    z-index: 1000;
    text-align: center;
  `;
  div.textContent = mensaje;
  document.body.appendChild(div);
  setTimeout(() => div.remove(), 3000);
}

// Al cargar la página
document.addEventListener('DOMContentLoaded', async () => {
  console.log('Iniciando verificación de sesión...');
  if (await verificarAuth()) {
    console.log('Sesión verificada, cargando interfaz de usuario...');
    await mostrarUsuarios();
  }
});