# app/solicitudes/models.py

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class SolicitudCorreccion(Base):
    __tablename__ = "solicitudes_correccion"

    id_solicitud = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_usuario_fk = Column(Integer, ForeignKey("usuario.id_usuario", ondelete="CASCADE"), nullable=False)
    
    campo_a_modificar = Column(String(100), nullable=False)
    valor_actual = Column(String(255), nullable=True)
    nuevo_valor = Column(String(255), nullable=True)
    motivo = Column(String(500), nullable=False)  # Motivo de la solicitud original
    motivo_respuesta = Column(String(500), nullable=True)  # Motivo de rechazo si aplica
    estado_solicitud = Column(String(50), default="Pendiente")
    fecha_solicitud = Column(DateTime(timezone=True), server_default=func.now())

    usuario = relationship("Usuario", back_populates="solicitudes_correccion")
