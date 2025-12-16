# app/reportes/schemas.py
from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import date

TIPOS_REPORTE = [
    'usuarios',
    'evidencias',
    'evaluaciones',
    'solicitudes_correccion',
    'actividad_general'
]

class ReporteBase(BaseModel):
    titulo: str
    descripcion: Optional[str] = None
    tipo_reporte: str

    @field_validator('tipo_reporte')
    def validar_tipo_reporte(cls, v):
        if v not in TIPOS_REPORTE:
            raise ValueError(f"tipo_reporte debe ser uno de {TIPOS_REPORTE}")
        return v

class ReporteCreate(ReporteBase):
    pass

class ReporteSchema(ReporteBase):
    id_reporte: int
    fecha_generacion: Optional[date]

    model_config = {"from_attributes": True}
