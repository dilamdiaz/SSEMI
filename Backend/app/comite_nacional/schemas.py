from pydantic import BaseModel
from typing import Optional

class EvaluadorComite(BaseModel):
    id_usuario: int
    primer_nombre: str
    segundo_nombre: Optional[str] = None
    primer_apellido: str
    segundo_apellido: Optional[str] = None
    correo: str
    comite_nacional: bool

    class Config:
        orm_mode = True
