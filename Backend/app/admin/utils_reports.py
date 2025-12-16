# app/admin/utils_reports.py
from sqlalchemy.orm import Session
from app.evaluador.models import Calificacion, DetalleCalificacion
from app.auth.models import Usuario
from datetime import date

def generar_reporte(db: Session, filtros: dict):
    """
    Genera reporte consolidado según filtros:
    - programa: string
    - instructor: string
    """
    query = db.query(Calificacion)

    # Filtrar por fecha
    if "fecha_inicio" in filtros and "fecha_fin" in filtros:
        query = query.filter(Calificacion.fecha_calificacion.between(
            filtros["fecha_inicio"], filtros["fecha_fin"]
        ))

    # Filtrar por instructor
    if "instructor" in filtros:
        query = query.join(Usuario).filter(Usuario.nombre.like(f"%{filtros['instructor']}%"))

    calificaciones = query.all()

    # Resumen
    total_evaluaciones = len(calificaciones)
    promedio_puntaje = (
        sum([float(c.puntaje_total or 0) for c in calificaciones]) / total_evaluaciones
        if total_evaluaciones else 0
    )

    estados = {"pendiente":0, "en_progreso":0, "finalizada":0, "aprobado":0}
    observaciones = []

    for c in calificaciones:
        if c.estado in estados:
            estados[c.estado] += 1
        for d in c.detalles:
            if d.observaciones:
                observaciones.append(d.observaciones)

    reporte = {
        "total_evaluaciones": total_evaluaciones,
        "promedio_puntaje": round(promedio_puntaje,2),
        "estados": estados,
        "observaciones": observaciones[:5]  # Top 5 observaciones
    }

    return reporte

