// ------------------- CONFIG -------------------
if (typeof apiFetch === 'undefined') console.warn('apiFetch not loaded. Ensure /js/api.js is included before this script.');
const API_BASE = API_URL;
const token = localStorage.getItem("ssemi_token");

let usuarioEditarId = null;
let solicitudSeleccionadaId = null;

// ------------------- VERIFICAR TOKEN -------------------
if (!token) {
    alert("Debe iniciar sesión");
    window.location.href = "/login";
}

// ------------------- SECCIONES -------------------
const usuariosSection = document.getElementById("usuariosSection");
const solicitudesSection = document.getElementById("solicitudesSection");
const reportesSection = document.getElementById("reportesSection");
const bitacoraSection = document.getElementById("bitacoraSection");

function mostrarUsuariosPanel() {
    usuariosSection.style.display = "block";
    solicitudesSection.style.display = "none";
    reportesSection.style.display = "none";
    mostrarUsuarios();
}
function mostrarSolicitudesPanel() {
    usuariosSection.style.display = "none";
    solicitudesSection.style.display = "block";
    reportesSection.style.display = "none";
    mostrarSolicitudes();
}

function mostrarBitacoraPanel() {
    usuariosSection.style.display = "none";
    solicitudesSection.style.display = "none";
    reportesSection.style.display = "none";
    if (bitacoraSection) bitacoraSection.style.display = "block";
    mostrarBitacora();
}

// ------------------- USUARIOS -------------------
const busqueda = document.getElementById("busquedaUsuarios");
const filtroRol = document.getElementById("filtroRol");
const filtroEstado = document.getElementById("filtroEstado");
const filtroGrado = document.getElementById("filtroGrado");
const filtroRegional = document.getElementById("filtroRegional");

busqueda.addEventListener("input", mostrarUsuarios);
filtroRol.addEventListener("change", mostrarUsuarios);
filtroEstado.addEventListener("change", mostrarUsuarios);
filtroGrado.addEventListener("change", mostrarUsuarios);
filtroRegional.addEventListener("change", mostrarUsuarios);

async function mostrarUsuarios() {
    try {
        let usuarios = await apiFetch('/usuarios');

        const term = busqueda.value.toLowerCase();
        if (term) {
            usuarios = usuarios.filter(u =>
                `${u.primer_nombre} ${u.segundo_nombre||''} ${u.primer_apellido} ${u.segundo_apellido||''}`.toLowerCase().includes(term) ||
                u.correo.toLowerCase().includes(term) ||
                u.numero_documento.toString().includes(term) ||
                (u.numero_contacto ? u.numero_contacto.toString().includes(term) : false) ||
                (u.grado ? u.grado.toLowerCase().includes(term) : false) ||
                (u.regional ? u.regional.toLowerCase().includes(term) : false)
            );
        }

        if (filtroRol.value) usuarios = usuarios.filter(u => u.rol_fk.toString() === filtroRol.value);
        if (filtroEstado.value) usuarios = usuarios.filter(u => u.estado.toString() === filtroEstado.value);
        if (filtroGrado.value) usuarios = usuarios.filter(u => u.grado === filtroGrado.value);
        if (filtroRegional.value) usuarios = usuarios.filter(u => u.regional === filtroRegional.value);

        const tbody = document.querySelector("#usuariosTable tbody");
        tbody.innerHTML = "";

        usuarios.forEach(u => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td>${u.id_usuario}</td>
                <td>${u.primer_nombre} ${u.segundo_nombre||''} ${u.primer_apellido} ${u.segundo_apellido||''}</td>
                <td>${u.correo}</td>
                <td>${u.tipo_documento} ${u.numero_documento}</td>
                <td>${u.rol_fk===1?'Instructor':u.rol_fk===2?'Administrador':'Evaluador'}</td>
                <td>${u.grado || ''}</td>
                <td>${u.regional || ''}</td>
                <td>${u.estado?'Activo':'Inactivo'}</td>
                <td>
                    <button class="btn btn-primary btn-sm me-1" onclick='abrirEditar(${JSON.stringify(u)})'>✏️ Editar</button>
                    <button class="btn btn-success btn-sm" onclick='cambiarEstado(${u.id_usuario}, ${u.estado})'>🔄 Cambiar Estado</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch(e) {
        console.error("Error al cargar usuarios:", e);
        alert("No se pudo cargar la lista de usuarios");
    }
}

// ------------------- MODAL EDITAR USUARIO -------------------
const modalEditar = new bootstrap.Modal(document.getElementById("modalEditar"), { backdrop: "static" });

function abrirEditar(u) {
    usuarioEditarId = u.id_usuario;
    document.getElementById("editPrimerNombre").value = u.primer_nombre;
    document.getElementById("editSegundoNombre").value = u.segundo_nombre || '';
    document.getElementById("editPrimerApellido").value = u.primer_apellido;
    document.getElementById("editSegundoApellido").value = u.segundo_apellido || '';
    document.getElementById("editTipoDoc").value = u.tipo_documento;
    document.getElementById("editNumDoc").value = u.numero_documento;
    document.getElementById("editCorreo").value = u.correo;
    document.getElementById("editContacto").value = u.numero_contacto || '';
    document.getElementById("editDireccion").value = u.direccion || '';
    document.getElementById("editRol").value = u.rol_fk;
    document.getElementById("editEstado").value = u.estado;
    // NUEVOS CAMPOS
    document.getElementById("editGrado").value = u.grado || '';
    document.getElementById("editRegional").value = u.regional || '';
    modalEditar.show();
}

document.getElementById("guardarCambios").addEventListener("click", async () => {
    try {
        const data = {
            primer_nombre: document.getElementById("editPrimerNombre").value,
            segundo_nombre: document.getElementById("editSegundoNombre").value,
            primer_apellido: document.getElementById("editPrimerApellido").value,
            segundo_apellido: document.getElementById("editSegundoApellido").value,
            tipo_documento: document.getElementById("editTipoDoc").value,
            numero_documento: parseInt(document.getElementById("editNumDoc").value),
            correo: document.getElementById("editCorreo").value,
            numero_contacto: parseInt(document.getElementById("editContacto").value),
            direccion: document.getElementById("editDireccion").value,
            rol_fk: parseInt(document.getElementById("editRol").value),
            estado: document.getElementById("editEstado").value === "true",
            // NUEVOS CAMPOS
            grado: document.getElementById("editGrado").value,
            regional: document.getElementById("editRegional").value
        };

        await apiFetch(`/usuarios/${usuarioEditarId}`, 'PUT', data);
        alert("Usuario actualizado correctamente");
        modalEditar.hide();
        mostrarUsuarios();
    } catch (e) {
        console.error("Error al actualizar usuario:", e);
        alert("No se pudo actualizar el usuario");
    }
});

async function cambiarEstado(id, estadoActual) {
    try {
        const data = { estado: !estadoActual };
        await apiFetch(`/usuarios/${id}/estado`, 'PUT', data);
        mostrarUsuarios();
    } catch (e) {
        console.error("Error al cambiar estado:", e);
        alert("No se pudo cambiar el estado");
    }
}

// ------------------- SOLICITUDES -------------------
const modalSolicitudBootstrap = new bootstrap.Modal(document.getElementById("modalSolicitud"), {backdrop:"static"});
const modalRechazoBootstrap = new bootstrap.Modal(document.getElementById("modalRechazo"), {backdrop:"static"});
const modalPerfil = new bootstrap.Modal(document.getElementById("modalPerfil"), {backdrop:"static"});

const traducciones = {
    primer_nombre: "Primer Nombre",
    segundo_nombre: "Segundo Nombre",
    primer_apellido: "Primer Apellido",
    segundo_apellido: "Segundo Apellido",
    numero_documento: "Número de Documento",
    tipo_documento: "Tipo de Documento",
    correo: "Correo Electrónico",
    numero_contacto: "Número de Contacto",
    direccion: "Dirección",
    grado: "Grado",
    regional: "Regional"
};

const busquedaSolicitudes = document.getElementById("busquedaSolicitudes");
const filtroCampoSolicitud = document.getElementById("filtroCampoSolicitud");
const filtroEstadoSolicitud = document.getElementById("filtroEstadoSolicitud");

busquedaSolicitudes.addEventListener("input", mostrarSolicitudes);
filtroCampoSolicitud.addEventListener("change", mostrarSolicitudes);
filtroEstadoSolicitud.addEventListener("change", mostrarSolicitudes);

let solicitudesCache = [];

async function mostrarSolicitudes(){
    try {
        if(solicitudesCache.length === 0){
            solicitudesCache = await apiFetch('/solicitudes-correccion/');
        }

        const term = busquedaSolicitudes.value.toLowerCase();
        const campoFiltro = filtroCampoSolicitud.value;
        const estadoFiltro = filtroEstadoSolicitud.value.toLowerCase();

        const filtradas = solicitudesCache.filter(s => {
            const nombre = s.usuario ? `${s.usuario.primer_nombre} ${s.usuario.segundo_nombre||''} ${s.usuario.primer_apellido} ${s.usuario.segundo_apellido||''}`.toLowerCase() : '';
            const campo = (s.campo_a_modificar || '').toLowerCase();
            const estado = (s.estado_solicitud || '').toLowerCase();
            const motivo = (s.motivo || '').toLowerCase();

            const busquedaMatch = nombre.includes(term) || campo.includes(term) || motivo.includes(term);
            const campoMatch = campoFiltro ? campo === campoFiltro.toLowerCase() : true;
            const estadoMatch = estadoFiltro ? estado === estadoFiltro : true;

            return busquedaMatch && campoMatch && estadoMatch;
        });

        const tbody = document.querySelector("#solicitudesTable tbody");
        tbody.innerHTML = "";

        filtradas.forEach(s=>{
            const nombreCompleto = s.usuario
                ? `${s.usuario.primer_nombre} ${s.usuario.segundo_nombre||''} ${s.usuario.primer_apellido} ${s.usuario.segundo_apellido||''}`
                : '';
            const campoTraducido = traducciones[s.campo_a_modificar] || s.campo_a_modificar;
            const tr = document.createElement("tr");
            const sEsc = JSON.stringify(s).replace(/'/g,"\\'").replace(/\n/g,"\\n");
            tr.innerHTML = `
                <td>${s.id_solicitud}</td>
                <td>${nombreCompleto}</td>
                <td>${campoTraducido}</td>
                <td>${s.valor_actual || ''}</td>
                <td>${s.nuevo_valor || ''}</td>
                <td>${s.motivo}</td>
                <td>${s.estado_solicitud}</td>
                <td class="text-center">
                    <button class="btn btn-primary btn-sm" onclick='abrirSolicitud(${sEsc})'>Ver</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch(e){
        console.error("Error al cargar solicitudes:", e); 
        alert("Error al cargar solicitudes");
    }
}

function abrirSolicitud(s){
    solicitudSeleccionadaId = s.id_solicitud;
    const nombreCompleto = s.usuario
        ? `${s.usuario.primer_nombre} ${s.usuario.segundo_nombre||''} ${s.usuario.primer_apellido} ${s.usuario.segundo_apellido||''}`
        : '';
    const campoTraducido = traducciones[s.campo_a_modificar] || s.campo_a_modificar;

    document.getElementById("solUsuario").innerText = nombreCompleto;
    document.getElementById("solCampo").innerText = campoTraducido;
    document.getElementById("solValorActual").innerText = s.valor_actual || '';
    document.getElementById("solNuevoValor").innerText = s.nuevo_valor || '';
    document.getElementById("solMotivo").innerText = s.motivo;
    document.getElementById("solEstado").innerText = s.estado_solicitud;
    modalSolicitudBootstrap.show();
}

// --- BOTONES DEL MODAL SOLICITUD ---
document.getElementById("aprobarSolicitud").addEventListener("click", async () => {
    if (!solicitudSeleccionadaId) {
        alert("Selecciona una solicitud primero");
        return;
    }

    try {
        await apiFetch(`/solicitudes-correccion/${solicitudSeleccionadaId}/aprobar`, 'PUT');

        alert("✅ Solicitud aprobada correctamente");
        modalSolicitudBootstrap.hide();
        solicitudSeleccionadaId = null;
        solicitudesCache = []; // refresca cache
        mostrarSolicitudes();
        mostrarUsuarios();

    } catch (e) {
        console.error("Error al aprobar solicitud:", e);
        alert("❌ Error al aprobar la solicitud: " + e.message);
    }
});


document.getElementById("rechazarSolicitud").addEventListener("click", ()=>{
    if(!solicitudSeleccionadaId){ alert("Selecciona una solicitud primero"); return; }
    modalSolicitudBootstrap.hide();
    modalRechazoBootstrap.show();
});

document.getElementById("confirmarRechazo").addEventListener("click", async ()=>{
    const motivo = document.getElementById("motivoRechazo").value.trim();
    if(!motivo){ alert("Debe ingresar un motivo de rechazo"); return; }

    try{
        await apiFetch(`/solicitudes-correccion/${solicitudSeleccionadaId}/rechazar`, 'PUT', { motivo_respuesta: motivo });
        alert("Solicitud rechazada");
        modalRechazoBootstrap.hide();
        document.getElementById("motivoRechazo").value = '';
        solicitudSeleccionadaId = null;
        solicitudesCache = []; // refresca cache
        mostrarSolicitudes();
        mostrarUsuarios();
    } catch(e){ console.error("Error al rechazar solicitud:", e); alert("Error al rechazar solicitud"); }
});


// ------------------- PERFIL ADMIN -------------------
document.getElementById("btnPerfil").addEventListener("click", async () => {
    try {
        const data = await apiFetch('/me');

        // Guardamos el ID del usuario para la actualización
        usuarioEditarId = data.id_usuario;

        // Cargar datos en el modal
        document.getElementById("perfilPrimerNombre").value = data.primer_nombre;
        document.getElementById("perfilSegundoNombre").value = data.segundo_nombre || '';
        document.getElementById("perfilPrimerApellido").value = data.primer_apellido;
        document.getElementById("perfilSegundoApellido").value = data.segundo_apellido || '';
        document.getElementById("perfilTipoDoc").value = data.tipo_documento;
        document.getElementById("perfilNumDoc").value = data.numero_documento;
        document.getElementById("perfilCorreo").value = data.correo;
        document.getElementById("perfilContacto").value = data.numero_contacto || '';
        document.getElementById("perfilDireccion").value = data.direccion || '';
        document.getElementById("perfilRol").value = data.rol_fk;
        document.getElementById("perfilGrado").value = data.grado || '';
        document.getElementById("perfilRegional").value = data.regional || '';
        // Mostrar estado legible
        document.getElementById("perfilEstado").value = data.estado ? 'Activo' : 'Inactivo';

        modalPerfil.show();
    } catch (e) {
        console.error("No se pudo cargar perfil admin:", e);
        alert("No se pudo cargar perfil");
    }
});

document.getElementById("guardarPerfil").addEventListener("click", async () => {
    try {
        const data = {
            primer_nombre: document.getElementById("perfilPrimerNombre").value,
            segundo_nombre: document.getElementById("perfilSegundoNombre").value,
            primer_apellido: document.getElementById("perfilPrimerApellido").value,
            segundo_apellido: document.getElementById("perfilSegundoApellido").value,
            tipo_documento: document.getElementById("perfilTipoDoc").value,
            numero_documento: parseInt(document.getElementById("perfilNumDoc").value),
            correo: document.getElementById("perfilCorreo").value,
            numero_contacto: parseInt(document.getElementById("perfilContacto").value),
            direccion: document.getElementById("perfilDireccion").value,
            rol_fk: parseInt(document.getElementById("perfilRol").value),
            // Convertimos el estado de "Activo"/"Inactivo" a true/false
            estado: document.getElementById("perfilEstado").value === "Activo",
            grado: document.getElementById("perfilGrado").value,
            regional: document.getElementById("perfilRegional").value
        };

        await apiFetch(`/usuarios/${usuarioEditarId}`, 'PUT', data);
        alert("Perfil actualizado correctamente");
        modalPerfil.hide();
        mostrarUsuarios();
    } catch (e) {
        console.error("No se pudo actualizar perfil admin:", e);
        alert("No se pudo actualizar perfil");
    }
});

// ------------------- LOGOUT -------------------
function logout(){ localStorage.removeItem("ssemi_token"); window.location.href="/login"; }

// ------------------- INICIAL -------------------
mostrarUsuarios();
// exportar función global para el onclick desde la plantilla
window.mostrarBitacoraPanel = mostrarBitacoraPanel;

document.getElementById("btnRefrescarBitacora")?.addEventListener("click", mostrarBitacora);

async function mostrarBitacora(){
    if(!bitacoraSection) return;
    try{
        const rows = await apiFetch('/bitacora/');
        const tbody = document.querySelector("#bitacoraTable tbody");
        tbody.innerHTML = "";
        rows.forEach(r=>{
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td>${r.id_bitacora}</td>
                <td>${new Date(r.fecha_accion).toLocaleString()}</td>
                <td>${r.usuario_nombre || r.id_usuario_fk}</td>
                <td>${r.accion}</td>
                <td>${r.descripcion || ''}</td>
                <td>${r.tabla_afectada}</td>
                <td>${r.id_registro_afectado || ''}</td>
            `;
            tbody.appendChild(tr);
        });
    }catch(e){
        console.error("Error al cargar bitacora:", e);
        alert("No se pudo cargar la bitácora");
    }
}
