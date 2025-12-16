# SSEMI  Sistema de Seguimiento y Evaluación de Méritos de Instructores

SSEMI es una aplicación web desarrollada para el **SENA** que permite la **gestión, carga, revisión y evaluación de evidencias** de los instructores en procesos de ascenso y seguimiento institucional.

El sistema centraliza las evidencias, automatiza el cálculo de puntajes por criterios y mantiene una **bitácora de acciones**, garantizando trazabilidad, seguridad y transparencia en el proceso de evaluación.

---

##  Funcionalidades principales

- Registro y autenticación de usuarios con JWT
- Gestión de roles:
  - Instructor
  - Evaluador
  - Administrador
- Carga y revisión de evidencias
- Evaluación por criterios y cálculo automático de puntajes
- Solicitudes de corrección de datos
- Bitácora de acciones del sistema
- Notificaciones y seguimiento de estados
- Control de acceso por rol

---

##  Arquitectura del proyecto

- **Backend**: FastAPI (Python)
- **Frontend**: HTML5 + Bootstrap 5
- **Base de datos**: MySQL
- **Autenticación**: JWT
- **ORM**: SQLAlchemy

---

##  Estructura del proyecto

```
SSEMI/

 Backend/
    app/
       auth/
       admin/
       evaluador/
       instructor/
       comite_nacional/
       evidencias/
       solicitudes/
       bitacora/
       reportes/
       mensajes/
       main.py
    requirements.txt
    .env (NO versionado)

 frontend/
    static/
    |   images/
    |   archivos .css y .js
    templates/
        archivos .html
 tests/

 README.md
```

---

##  Requisitos previos

- Python 3.10 o superior
- MySQL o MariaDB
- Git
- Navegador web moderno

---

##  Instalación y ejecución (Backend)

### 1 Clonar el repositorio

```bash
git clone https://github.com/dilamdiaz/SSEMI.git
cd SSEMI
```

### 2 Crear y activar entorno virtual (Windows)

Abre PowerShell y ejecuta:

```powershell
cd Backend
python -m venv venv
venv\Scripts\Activate
```

### 3 Instalar dependencias

```powershell
pip install --upgrade pip
pip install -r requirements.txt
pip install apscheduler
```

###  Variables de entorno (.env)

Crea un archivo `.env` dentro de la carpeta `Backend/` con el siguiente contenido mínimo:

```env
DB_USER=root
DB_PASSWORD=
DB_HOST=127.0.0.1
DB_NAME=ssemi

SECRET_KEY=tu_clave_secreta_segura
ACCESS_KEY_ADMIN=miclaveespecial123
```

Notas:
- El archivo `.env` NO debe subirse al repositorio.
- `SECRET_KEY` es obligatorio para JWT.
- En producción, todas las credenciales deben manejarse mediante variables de entorno o un gestor de secretos.

###  Ejecutar la aplicación

Desde la carpeta `Backend/` con el entorno virtual activo:

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

La API quedará disponible en:

```
http://127.0.0.1:8000
```

Documentación automática (Swagger):

```
http://127.0.0.1:8000/docs
```

---

##  Frontend

El frontend está desarrollado con HTML puro y Bootstrap, sin frameworks como React o Vue.

Para utilizarlo:

1. Inicia el backend.
2. Abre los archivos `.html` ubicados en la carpeta `frontend/` (por ejemplo `frontend/templates/admin.html`) en tu navegador o sirve las plantillas desde el backend si está configurado.
3. El frontend consume la API mediante peticiones HTTP (`fetch`).

---

##  Buenas prácticas y seguridad

- No subir archivos `.env` ni credenciales al repositorio.
- Restringir CORS en producción.
- No dejar claves o tokens hardcodeados.
- Usar HTTPS en despliegue.

---

##  Estado del proyecto

-  Proyecto finalizado
-  Listo para despliegue
-  Proyecto académico  SENA

##  Licencia

Proyecto de uso académico y educativo.

---

