# app/bitacora/crud.py
from sqlalchemy.orm import Session
from .models import Bitacora

def log_action(
    db: Session,
    id_usuario: int,
    accion: str,
    descripcion: str,
    tabla_afectada: str,
    id_registro_afectado: int = None
):
    registro = Bitacora(
        id_usuario_fk=id_usuario,
        accion=accion,
        descripcion=descripcion,
        tabla_afectada=tabla_afectada,
        id_registro_afectado=id_registro_afectado
    )
    db.add(registro)
    db.commit()
