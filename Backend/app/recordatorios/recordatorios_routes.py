# Backend/app/recordatorios/recordatorios_routes.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from .recordatorios_models import Notificacion
# Puedes crear un esquema Pydantic si lo necesitas, pero por simplicidad
# devolveremos un diccionario para esta función.

router = APIRouter(
    prefix="/api/recordatorios",
    tags=["Recordatorios"]
)

@router.get("/notificaciones/pendientes/{user_id}")
def get_notificaciones_pendientes(user_id: int, db: Session = Depends(get_db)):
    """
    [GET] Consulta todas las notificaciones no leídas para un usuario.
    """
    
    notificaciones_raw = db.query(Notificacion).filter(
        Notificacion.id_usuario_fk == user_id,
        Notificacion.leida == False
    ).order_by(Notificacion.fecha_envio.desc()).all()
    
    notificaciones = []
    for noti in notificaciones_raw:
        # Extraer el enlace directo (|URL:{ruta})
        mensaje_completo = noti.mensaje
        if "|URL:" in mensaje_completo:
            mensaje_texto, url_path = mensaje_completo.split("|URL:")
        else:
            mensaje_texto, url_path = mensaje_completo, "#"

        notificaciones.append({
            "id": noti.id_notificacion,
            "mensaje": mensaje_texto,
            "fecha_envio": noti.fecha_envio.strftime("%Y-%m-%d %H:%M:%S"),
            "enlace_directo": url_path 
        })
        
    return notificaciones

@router.post("/notificaciones/marcar_leida/{id_notificacion}", status_code=status.HTTP_200_OK)
def marcar_como_leida(id_notificacion: int, db: Session = Depends(get_db)):
    """
    [POST] Marca una notificación como leída.
    """
    notificacion = db.query(Notificacion).filter(Notificacion.id_notificacion == id_notificacion).first()
    
    if not notificacion:
        raise HTTPException(status_code=404, detail="Notificación no encontrada")
        
    notificacion.leida = True
    db.commit()
    return {"status": "ok", "message": "Notificación marcada como leída"}