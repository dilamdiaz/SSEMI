from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class BitacoraBase(BaseModel):
    accion: str
    descripcion: Optional[str] = None
    tabla_afectada: str
    id_registro_afectado: Optional[int] = None

class BitacoraCreate(BitacoraBase):
    id_usuario_fk: int

class BitacoraResponse(BitacoraBase):
    id_bitacora: int
    id_usuario_fk: int
    usuario_nombre: Optional[str] = None
    fecha_accion: datetime

    class Config:
        orm_mode = True
