from pydantic import BaseModel
from datetime import datetime

class MensajeBase(BaseModel):
    destino_rol: int
    destino_id: int | None = None  # Usuario específico (opcional)
    asunto: str
    contenido: str
    respuesta_a_id: int | None = None  # Para mensajes de respuesta

class MensajeCreate(MensajeBase):
    pass

class MensajeOut(BaseModel):
    id: int
    asunto: str
    contenido: str
    remitente_id: int
    remitente_nombre: str | None = None
    destino_rol: int
    destino_id: int | None = None
    leido: bool
    fecha_envio: datetime
    respuesta_a_id: int | None = None

    class Config:
        from_attributes = True
