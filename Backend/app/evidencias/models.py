#backend/app/evidencias/models.py
from sqlalchemy import Column, Integer, String, Date, Enum, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
import enum
import os
from app.database import Base
from app.auth.models import Usuario  # ✅ Importar modelo real para evitar duplicación
from datetime import date

# ==============================
# ENUMS
# ==============================
class EstadoEvidenciaEnum(enum.Enum):
    Cargada = "Cargada"
    Borrador = "Borrador"
    Evaluada = "Evaluada"


# ==============================
# TABLAS Y RELACIONES
# ==============================
class Categoria(Base):
    __tablename__ = "categoria"

    id_categoria = Column(Integer, primary_key=True, autoincrement=True)
    nombre_categoria = Column(String(100), nullable=False)
    descripcion = Column(String(200))

    evidencias = relationship("Evidencia", back_populates="categoria")


class Reporte(Base):
    __tablename__ = "reportes"

    id_reporte = Column(Integer, primary_key=True, index=True)
    titulo = Column(String(150), nullable=False)
    descripcion = Column(Text, nullable=True)
    fecha_creacion = Column(Date, nullable=True)
    estado = Column(Enum("Pendiente", "Aprobado", "Rechazado"), default="Pendiente")

    evidencias = relationship("Evidencia", back_populates="reporte")
    # 🔸 Eliminamos relación directa con Calificación (para evitar dependencias circulares)


class Evidencia(Base):
    __tablename__ = "evidencias"

    id_evidencia = Column(Integer, primary_key=True, autoincrement=True)
    titulo = Column(String(150), nullable=False)
    descripcion = Column(String(200))
    id_categoria_fk = Column(Integer, ForeignKey("categoria.id_categoria", ondelete="SET NULL", onupdate="CASCADE"))
    archivos = Column(JSON, nullable=True)
    fecha_evidencia = Column(Date, nullable=False)
    formulario = Column(JSON, nullable=True)
    estado_evidencia = Column(Enum(EstadoEvidenciaEnum), default=EstadoEvidenciaEnum.Cargada)
    id_usuario_fk = Column(Integer, ForeignKey("usuario.id_usuario", ondelete="CASCADE", onupdate="CASCADE"))
    reportes_id_reporte = Column(Integer, ForeignKey("reportes.id_reporte", ondelete="SET NULL", onupdate="CASCADE"))

    categoria = relationship("Categoria", back_populates="evidencias")
    usuario = relationship("Usuario")  # ✅ usa modelo importado de app.auth.models
    reporte = relationship("Reporte", back_populates="evidencias")
    historial = relationship("HistorialCarga", back_populates="evidencia", cascade="all, delete-orphan")
    
    @property
    def id(self):
        return self.id_evidencia

    @property
    def filepath(self):
        return self.archivos
    
    @property
    def filename(self):
        if isinstance(self.archivos, list):
            return [os.path.basename(r) for r in self.archivos]
        return None
    
    @property
    def uploaded_at(self):
        return self.fecha_evidencia


class HistorialCarga(Base):
    __tablename__ = "historial_carga"

    id = Column(Integer, primary_key=True, autoincrement=True)
    id_evidencia = Column(Integer, ForeignKey("evidencias.id_evidencia", ondelete="CASCADE", onupdate="CASCADE"))
    id_instructor = Column(Integer, ForeignKey("usuario.id_usuario", ondelete="CASCADE", onupdate="CASCADE"))
    fecha_carga = Column(Date)

    evidencia = relationship("Evidencia", back_populates="historial")
    usuario = relationship("Usuario")  # ✅ también usa el modelo real

    @property
    def evidencia_fk(self):
        return self.id_evidencia

    @property
    def instructor_fk(self):
        return self.id_instructor
