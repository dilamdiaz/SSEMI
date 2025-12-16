# app/evaluador/schemas.py
from datetime import date
from typing import List, Optional
from pydantic import BaseModel

class DetalleCalificacionBase(BaseModel):
    id_evidencia_fk: int
    puntaje: float
    observaciones: Optional[str] = None


class DetalleCalificacionCreate(DetalleCalificacionBase):
    pass


class DetalleCalificacionResponse(DetalleCalificacionBase):
    id_detalle: int

    class Config:
        orm_mode = True


class CalificacionBase(BaseModel):
    id_usuario_fk: int
    puntaje_total: Optional[float] = None
    fecha_calificacion: Optional[date] = None
    estado: Optional[str] = None

class CalificacionCreate(CalificacionBase):
    id_usuario_fk: int
    detalles: List[DetalleCalificacionCreate]= []


class CalificacionResponse(CalificacionBase):
    id_calificacion: int
    fecha_calificacion: Optional[date]
    fecha_ultimo_guardado: Optional[date]
    detalles: List[DetalleCalificacionResponse] = []

    class Config:
        orm_mode = True

class ResultadoSchema(BaseModel):
    id_detalle: int
    evidencia: str
    instructor: str
    evaluador_id: int
    puntaje: float
    observaciones: Optional[str] = None
    fecha: date

    class Config:
        orm_mode = True