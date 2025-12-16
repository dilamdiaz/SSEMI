from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Bitacora(Base):
    __tablename__ = "bitacora"

    id_bitacora = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_usuario_fk = Column(Integer, ForeignKey("usuario.id_usuario"), nullable=False)

    accion = Column(String(100), nullable=False)
    descripcion = Column(Text, nullable=True)
    tabla_afectada = Column(String(100), nullable=False)
    id_registro_afectado = Column(Integer, nullable=True)
    fecha_accion = Column(DateTime(timezone=True), server_default=func.now())

    usuario = relationship("Usuario")
