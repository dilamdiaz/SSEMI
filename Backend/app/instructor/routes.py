from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth.models import Usuario
from app.auth.routes import get_current_user
from app.evaluador.models import Calificacion, DetalleCalificacion
from app.evidencias.models import Evidencia

router = APIRouter(prefix="/instructor")

@router.get("/calificaciones")
def ver_calificaciones_instructor(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    # Solo instructores pueden acceder
    if current_user.rol_fk != 1:
        raise HTTPException(status_code=403, detail="Acceso denegado")

    # Traer evidencias subidas por este instructor
    evidencias = db.query(Evidencia).filter(Evidencia.id_usuario_fk == current_user.id_usuario).all()
    evidencia_ids = [e.id_evidencia for e in evidencias]

    if not evidencia_ids:
        return []

    # Traer calificaciones relacionadas a esas evidencias
    detalles = db.query(DetalleCalificacion).join(Calificacion).filter(
        DetalleCalificacion.id_evidencia_fk.in_(evidencia_ids)
    ).all()

    # Formatear para frontend
    resultados = []
    for d in detalles:
        resultados.append({
            "id_calificacion": d.id_calificacion_fk,
            "evaluador": d.calificacion.usuario.primer_nombre + " " + (d.calificacion.usuario.segundo_nombre or ''),
            "evidencia": d.evidencia.titulo,
            "puntaje": float(d.puntaje),
            "observaciones": d.observaciones or "",
            "fecha": str(d.calificacion.fecha_calificacion),
            "estado": d.calificacion.estado
        })

    return resultados
