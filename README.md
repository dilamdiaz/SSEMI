
# SSEMI — Instrucciones rápidas para desarrolladores

Breve README orientado al desarrollador que va a levantar el proyecto en su máquina. Aquí encontrarás los comandos mínimos para crear el entorno virtual, instalar dependencias, configurar las variables de entorno y ejecutar el servidor (FastAPI / uvicorn).

Requisitos previos
- Python 3.10+ instalado y accesible desde la línea de comandos.
- MySQL o MariaDB corriendo localmente (o acceso a un servidor MySQL).

# 1 Clona el repositorio (si no lo tienes):

```powershell
git clone <tu-repo-url>
cd C:\Users\Dylam\Desktop\SSEMI_PROYECTO
```

# 2 Crear y activar entorno virtual (PowerShell)

```powershell
cd backend
# Estar dentro de Backend
python -m venv venv
# Ejecuta esto en PowerShell para activar
venv\Scripts\Activate
#instalar para scheduler
pip install apscheduler
```

# 3 Instalar dependencias del backend

```powershell
pip install -r requirements.txt
python.exe -m pip install --upgrade pip
```

# 4 Variables de entorno mínimas (.env)

Coloca un archivo `.env` en la carpeta `Backend/` con al menos lo siguiente:

```text
DB_USER=root
DB_PASSWORD=
DB_HOST=127.0.0.1
DB_NAME=ssemi
SECRET_KEY=tu_clave_secreta_segura
ACCESS_KEY_ADMIN=miclaveespecial123
```

Notas:
- `SECRET_KEY` es obligatorio para JWT. Usa una cadena larga y aleatoria.
- Si vas a usar envío de correos, mueve las credenciales del archivo `app/auth/email_utils.py` a variables de entorno y asegúrate de no subir `.env` al repo.


# 5 Iniciar la aplicación (uvicorn)

Desde la carpeta `Backend/` activa el venv si no está activo y ejecuta:

```powershell
venv\Scripts\Activate  # si no está activo
uvicorn app.main:app --reload

```

La app quedará disponible en http://127.0.0.1:8000

Comandos útiles / atajos
- Para reinstalar dependencias rápidamente:

```powershell
pip install -r requirements.txt --upgrade
```


Notas rápidas de seguridad y desarrollo
- No subas `.env` ni claves a Git.
- Reemplaza cualquier credencial hardcodeada en `app/auth/email_utils.py` por variables de entorno.
- En producción restringe CORS (en `app/main.py` actualmente está `allow_origins=["*"]`).
