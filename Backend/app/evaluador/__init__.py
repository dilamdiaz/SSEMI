from fastapi import APIRouter

router = APIRouter(
    prefix="/evaluador",
    tags=["Evaluador"]
)

# Aquí importas las rutas
from app.evaluador import routes
