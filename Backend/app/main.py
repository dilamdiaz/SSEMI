# Backend/app/main.py

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
import os
from sqlalchemy.orm import Session
from fastapi.staticfiles import StaticFiles
from app.evidencias.routes import UPLOAD_DIR
# ======================================================
# Importaciones internas
# ======================================================
from app.database import Base, engine, get_db
from app.auth.models import Usuario
from app.auth.routes import router as auth_router, get_current_user
from app.auth.schemas import UserOut
from app.evidencias.routes import router as evidencias_router
from app.evaluador.routes import router as evaluador_router
from app.admin import routes as admin_routes
from app.instructor.routes import router as instructor_router
from app.solicitudes.routes import router as solicitudes_router
from app.comite_nacional.routes import router as comite_nacional_router
from app.mensajes.routes import router as mensajes_router
from app.mensajes.routes_admin import router as mensajes_admin_router
from app.mensajes import routes_comite
from app.reportes import routes as reportes_router 
from app.recordatorios.recordatorios_scheduler import iniciar_scheduler, scheduler
from app.bitacora.routes import router as bitacora_router

# ------------------------------------------------------
# IMPORTACIONES NUEVAS PARA RECORDATORIOS
# ------------------------------------------------------
from app.recordatorios.recordatorios_scheduler import iniciar_scheduler, scheduler
from app.recordatorios.recordatorios_routes import router as recordatorios_router 

# ======================================================
# Inicialización de la aplicación
# ======================================================
app = FastAPI(title="SSEMI API", version="1.0.0")

# Carpeta absoluta de 'app'
APP_DIR = os.path.abspath(os.path.dirname(__file__))

# Carpeta uploads dentro de 'app'
UPLOAD_DIR = os.path.join(APP_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ======================================================
# Eventos de Startup y Shutdown (NUEVO)
# ======================================================
@app.on_event("startup")
async def startup_event():
    # Crear todas las tablas en la base de datos si no existen
    Base.metadata.create_all(bind=engine)
    
    # Inicializa y arranca el scheduler al inicio de la aplicación
    iniciar_scheduler()
    scheduler.start()
    print("Servicio de Recordatorios Automaticos iniciado. ⏰")

@app.on_event("shutdown")
async def shutdown_event():
    # Asegura que el scheduler se detenga limpiamente al cerrar la aplicación
    if scheduler.running:
        scheduler.shutdown()
        print("Servicio de Recordatorios Automaticos detenido. 🛑")


# ======================================================
# Configuración CORS
# ======================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ======================================================
# Paths del frontend y carpetas
# ======================================================
base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../frontend"))
uploads_path = os.path.join(os.path.dirname(__file__), "uploads")
static_path = os.path.join(base_path, "static")
templates_path = os.path.join(base_path, "templates")

# ======================================================
# Crear carpeta uploads si NO existe (corrección del error)
# ======================================================
if not os.path.exists(uploads_path):
    os.makedirs(uploads_path, exist_ok=True)
    print(f"[INFO] Carpeta 'uploads' creada automáticamente en: {uploads_path}")

# ======================================================
# Montar archivos estáticos
# ======================================================
app.mount("/static", StaticFiles(directory=static_path), name="static")
# Montamos la carpeta para acceso público
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

templates = Jinja2Templates(directory=templates_path)

# ======================================================
# Rutas principales de la API
# ======================================================
app.include_router(reportes_router.router) 
app.include_router(recordatorios_router) # <--- REGISTRO DEL NUEVO ROUTER DE RECORDATORIOS
app.include_router(auth_router)
app.include_router(evidencias_router)
app.include_router(evaluador_router)
app.include_router(admin_routes.router)
app.include_router(instructor_router)
app.include_router(solicitudes_router)
app.include_router(comite_nacional_router)
app.include_router(mensajes_router)
app.include_router(mensajes_admin_router)
app.include_router(routes_comite.router)
app.include_router(bitacora_router)



# ======================================================
# Rutas HTML principales
# ======================================================
@app.get("/", response_class=HTMLResponse)
async def serve_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/dashboard/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    return templates.TemplateResponse("admin.html", {"request": request})

@app.get("/dashboard/instructor", response_class=HTMLResponse)
async def instructor_dashboard(request: Request):
    return templates.TemplateResponse("instructor.html", {"request": request})

@app.get("/dashboard/evaluador", response_class=HTMLResponse)
async def evaluador_dashboard(request: Request):
    return templates.TemplateResponse("evaluador/evaluador.html", {"request": request})

@app.get("/usuarios", response_class=HTMLResponse)
async def usuarios_page(request: Request):
    return templates.TemplateResponse("usuarios.html", {"request": request})

# ======================================================
# API protegida de usuarios
# ======================================================
@app.get("/api/usuarios", response_model=list[UserOut])
def listar_usuarios_api(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if current_user.rol_fk != 2:
        raise HTTPException(status_code=403, detail="Acceso restringido a administradores")
    return db.query(Usuario).all()

# ======================================================
# Favicon
# ======================================================
@app.get("/favicon.ico")
async def favicon():
    path = os.path.join(static_path, "favicon.ico")
    if os.path.exists(path):
        return FileResponse(path)
    return "", 204

# ======================================================
# Catch-all seguro para admin
# ======================================================
@app.get("/dashboard/{full_path:path}", response_class=HTMLResponse)
async def catch_all_dashboard(request: Request, full_path: str):
    return templates.TemplateResponse("admin.html", {"request": request})

# ======================================================
# Catch-all para otras páginas HTML
# ======================================================
@app.get("/{page_name}", response_class=HTMLResponse)
@app.get("/{page_name}/", response_class=HTMLResponse)
async def serve_page(request: Request, page_name: str):
    file_name = f"{page_name}.html"
    template_path = os.path.join(templates_path, file_name)
    if not os.path.exists(template_path):
        return HTMLResponse("Página no encontrada", status_code=404)
    return templates.TemplateResponse(file_name, {"request": request})