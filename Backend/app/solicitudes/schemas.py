from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# ======================================================
# 📥 Crear una nueva solicitud
# ======================================================
class SolicitudCreate(BaseModel):
    campo_a_modificar: str
    valor_actual: Optional[str] = None
    nuevo_valor: Optional[str] = None
    motivo: str


# ======================================================
# 🔄 Actualizar estado (aprobar o rechazar)
# ======================================================
class SolicitudUpdate(BaseModel):
    estado_solicitud: str
    motivo_respuesta: Optional[str] = None  # Solo se usa al rechazar


# ======================================================
# ❌ Esquema para rechazo (solo motivo)
# ======================================================
class SolicitudRechazo(BaseModel):
    motivo_respuesta: str


# ======================================================
# 👤 Usuario relacionado a la solicitud
# ======================================================
class UsuarioResponse(BaseModel):
    id_usuario: int
    primer_nombre: str
    segundo_nombre: Optional[str]
    primer_apellido: str
    segundo_apellido: Optional[str]
    correo: str

    class Config:
        orm_mode = True


# ======================================================
# 📤 Respuesta completa de solicitud
# ======================================================
class SolicitudResponse(BaseModel):
    id_solicitud: int
    id_usuario_fk: int
    usuario: Optional[UsuarioResponse] = None
    campo_a_modificar: str
    valor_actual: Optional[str]
    nuevo_valor: Optional[str]
    motivo: str
    motivo_respuesta: Optional[str] = None
    estado_solicitud: str
    fecha_solicitud: datetime

    class Config:
        orm_mode = True
