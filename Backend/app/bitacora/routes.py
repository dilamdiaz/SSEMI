from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.bitacora.models import Bitacora
from app.bitacora.schemas import BitacoraResponse
from typing import List

router = APIRouter(prefix="/bitacora", tags=["Bitacora"])


@router.get("/", response_model=List[BitacoraResponse])
def obtener_bitacora(db: Session = Depends(get_db)):
    # Traer registros con relación a usuario y construir campo "usuario_nombre"
    registros = db.query(Bitacora).order_by(Bitacora.fecha_accion.desc()).all()
    resultado = []
    for r in registros:
        nombre = None
        try:
            if getattr(r, 'usuario', None):
                u = r.usuario
                parts = [u.primer_nombre or '', u.segundo_nombre or '', u.primer_apellido or '', u.segundo_apellido or '']
                # unir y limpiar espacios redundantes
                nombre = ' '.join([p for p in parts if p]).strip()
        except Exception:
            nombre = None

        resultado.append({
            'id_bitacora': r.id_bitacora,
            'id_usuario_fk': r.id_usuario_fk,
            'usuario_nombre': nombre,
            'accion': r.accion,
            'descripcion': r.descripcion,
            'tabla_afectada': r.tabla_afectada,
            'id_registro_afectado': r.id_registro_afectado,
            'fecha_accion': r.fecha_accion
        })

    return resultado
