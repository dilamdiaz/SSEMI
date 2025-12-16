from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Mensaje(Base):
    __tablename__ = "mensajes"

    id = Column(Integer, primary_key=True, index=True)

    # Remitente
    remitente_id = Column(Integer, ForeignKey("usuario.id_usuario"), nullable=False)
    remitente = relationship(
        "Usuario",
        back_populates="mensajes_enviados",
        primaryjoin="Usuario.id_usuario==Mensaje.remitente_id"
    )

    # Destino específico de usuario (opcional)
    destino_id = Column(Integer, ForeignKey("usuario.id_usuario"), nullable=True)
    destino = relationship(
        "Usuario",
        foreign_keys=[destino_id]
    )

    # Destino por rol (para mensajes generales)
    destino_rol = Column(Integer, nullable=False)

    # Mensajes de respuesta
    respuesta_a_id = Column(Integer, ForeignKey("mensajes.id"), nullable=True)
    respuestas = relationship(
        "Mensaje",
        backref="mensaje_padre",
        remote_side=[id]
    )

    # Contenido
    asunto = Column(String(200), nullable=False)
    contenido = Column(Text, nullable=False)

    # Metadata
    fecha_envio = Column(DateTime, default=datetime.utcnow)
    leido = Column(Boolean, default=False)
