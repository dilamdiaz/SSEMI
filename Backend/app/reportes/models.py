# app/reportes/models.py
from sqlalchemy import Column, Integer, String, Text, Date, Enum, ForeignKey
from app.database import Base

class ReporteSSEMI(Base):
    __tablename__ = "reportes_ssemi"
    __table_args__ = {"extend_existing": True}

    id_reporte = Column(Integer, primary_key=True, autoincrement=True)
    titulo = Column(String(150), nullable=False)
    descripcion = Column(Text, nullable=True)
    id_usuario_accion = Column(Integer, ForeignKey("usuario.id_usuario"), nullable=True)
    fecha_generacion = Column(Date, nullable=True)
    tipo_reporte = Column(
        Enum(
            'usuarios',
            'evidencias',
            'evaluaciones',
            'solicitudes_correccion',
            'actividad_general',
            name="tipo_reporte_enum"
        ),
        nullable=False
    )
