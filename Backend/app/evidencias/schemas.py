from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional,List

class EvidenciaResponse(BaseModel):
    id_evidencia: int
    titulo: str
    descripcion: Optional[str]
    archivos: Optional[List[str]] = []
    formulario: Optional[dict]
    id_categoria_fk: int
    id_usuario_fk: int
    fecha_evidencia: Optional[date]
    estado_evidencia: Optional[str]

    class Config:
        from_attributes = True


class HistorialResponse(BaseModel):
    id: int
    evidencia_id: int
    titulo: str
    descripcion: Optional[str]
    accion: str
    fecha: datetime   # 👈 asegúrate de que esté aquí también

    class Config:
        from_attributes = True