# Backend/app/recordatorios/recordatorios_scheduler.py

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.database import SessionLocal 
from .recordatorios_service import generar_recordatorios_pendientes

# Instancia global del scheduler
scheduler = AsyncIOScheduler()

def job_wrapper():
    """Wrapper para manejar la sesión de DB dentro de la tarea programada."""
    db = SessionLocal()
    try:
        generar_recordatorios_pendientes(db)
    finally:
        db.close() # Cierra la sesión después de cada ejecución

def iniciar_scheduler():
    """
    Configura el job periódico. Llamado en el evento 'startup' de main.py.
    """
    # Ejecuta la tarea cada 30 minutos (AJUSTA ESTO SEGÚN TU NECESIDAD)
    scheduler.add_job(
        job_wrapper, 
        'interval', 
        minutes=30,
        id='recordatorios_automaticos',
        max_instances=1 
    )