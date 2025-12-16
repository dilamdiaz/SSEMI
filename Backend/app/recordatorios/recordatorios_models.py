# Backend/app/recordatorios/recordatorios_models.py

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, func
from app.database import Base # Importación asumida desde tu main.py

class Notificacion(Base):
    """Modelo de la tabla 'notificacion' para almacenar recordatorios."""
    
    __tablename__ = "notificacion"

    id_notificacion = Column(Integer, primary_key=True, index=True)
    # Asume que existe una tabla 'usuario' con primary key 'id_usuario'
    id_usuario_fk = Column(Integer, ForeignKey('usuario.id_usuario'), nullable=False) 
    mensaje = Column(String(1000), nullable=False)
    fecha_envio = Column(DateTime, default=func.now())
    leida = Column(Boolean, default=False)
    # Relación a una tarea (si no existe el modelo 'tarea' en este proyecto,
    # evitamos crear una FK para no romper `create_all`).
    # Si tu proyecto tiene un modelo `tarea`, reemplaza por ForeignKey('tarea.id_tarea').
    tarea_id_tarea = Column(Integer, nullable=True)