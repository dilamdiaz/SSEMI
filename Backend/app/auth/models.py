# app/auth/models.py

from sqlalchemy import Column, Integer, String, BigInteger, Enum, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
import enum

# Enum para tipo_documento
class TipoDocumentoEnum(str, enum.Enum):
    CC = "CC"
    CE = "CE"

class Rol(Base):
    __tablename__ = "rol"

    id_rol = Column(Integer, primary_key=True, index=True)
    nombre_rol = Column(String(50), unique=True, nullable=False)

    usuarios = relationship("Usuario", back_populates="rol")
    

class Usuario(Base):
    __tablename__ = "usuario"

    id_usuario = Column(Integer, primary_key=True, index=True)
    primer_nombre = Column(String(50), nullable=False)
    segundo_nombre = Column(String(50))
    primer_apellido = Column(String(50), nullable=False)
    segundo_apellido = Column(String(50), nullable=False)
    tipo_documento = Column(Enum(TipoDocumentoEnum), nullable=False)
    numero_documento = Column(BigInteger, unique=True, nullable=False)
    correo = Column(String(100), unique=True, nullable=False)
    rol_fk = Column(Integer, ForeignKey("rol.id_rol"), nullable=False)
    contraseña = Column(String(255), nullable=False)
    numero_contacto = Column(BigInteger, unique=True)
    direccion = Column(String(150))
    estado = Column(Boolean, default=True)

    # -------------------------------
    # Campos para verificación 2FA
    # -------------------------------
    two_factor_code = Column(String(6), nullable=True)
    two_factor_expiration = Column(DateTime, nullable=True)

    # -------------------------------
    # NUEVOS CAMPOS
    # -------------------------------
    grado = Column(String(20), nullable=True)  # algunos roles no requieren grado
    regional = Column(String(100), nullable=False, default="Distrito Capital")
    comite_nacional = Column(Boolean, default=False)  # indica si pertenece al Comité Nacional

    rol = relationship("Rol", back_populates="usuarios")
    solicitudes_correccion = relationship("SolicitudCorreccion", back_populates="usuario")
    
    # -------------------------------
    # Relación con mensajes
    # -------------------------------
    # Mensajes enviados por este usuario
    mensajes_enviados = relationship(
        "Mensaje",
        back_populates="remitente",
        foreign_keys="Mensaje.remitente_id"
    )

    # Mensajes recibidos directamente (destino_id)
    mensajes_recibidos = relationship(
        "Mensaje",
        back_populates="destino",
        foreign_keys="Mensaje.destino_id"
    )

class RecuperacionContrasena(Base):
    __tablename__ = "recuperacion_contrasena"

    id_recuperacion = Column(Integer, primary_key=True, index=True)
    id_usuario_fk = Column(Integer, ForeignKey("usuario.id_usuario"), nullable=False)
    token = Column(String(255), unique=True, nullable=False)
    fecha_creacion = Column(DateTime, nullable=False, default=datetime.utcnow)
    usado = Column(Boolean, default=False)

    usuario = relationship("Usuario")
