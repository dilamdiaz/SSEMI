# app/evaluador/models.py
from sqlalchemy import (
    Column, Integer, String, ForeignKey, Date, Text,
    DECIMAL, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
from app.database import Base
from app.auth.models import Usuario  # ✅ Modelo real de usuario
from app.evidencias.models import Evidencia  # ⚠️ Eliminamos Reporte porque no debe depender de él

# ==============================
# ENUMS Y CONSTANTES
# ==============================
ESTADO_CALIFICACION_CHOICES = ("aprobado", "rechazado", "pendiente","en_progreso")


# ==============================
# TABLA PRINCIPAL: CALIFICACIONES
# ==============================
class Calificacion(Base):
    __tablename__ = "calificaciones"

    id_calificacion = Column(Integer, primary_key=True, index=True)
    id_usuario_fk = Column(Integer, ForeignKey("usuario.id_usuario"), nullable=False)
    puntaje_total = Column(DECIMAL(6, 2), nullable=True)
    fecha_calificacion = Column(Date, nullable=True)
    estado = Column(SQLEnum(*ESTADO_CALIFICACION_CHOICES, name="estado_calificacion_enum"), nullable=True)

    # Si un reporte necesita calificaciones, se consulta con JOIN desde el módulo de reportes

    # Relaciones
    usuario = relationship("Usuario", backref="calificaciones")  # Acceso rápido desde el usuario
    detalles = relationship(
        "DetalleCalificacion",
        back_populates="calificacion",
        cascade="all, delete-orphan"
    )


# ==============================
# TABLA HIJA: DETALLE_CALIFICACIONES
# ==============================
class DetalleCalificacion(Base):
    __tablename__ = "detalle_calificaciones"

    id_detalle = Column(Integer, primary_key=True, index=True)
    id_calificacion_fk = Column(Integer, ForeignKey("calificaciones.id_calificacion"), nullable=False)
    id_evidencia_fk = Column(Integer, ForeignKey("evidencias.id_evidencia"), nullable=False)
    puntaje = Column(DECIMAL(5, 2), nullable=False)
    observaciones = Column(Text, nullable=True)

    # Relaciones
    calificacion = relationship("Calificacion", back_populates="detalles")
    evidencia = relationship("Evidencia")  # Acceso directo a la evidencia evaluada

