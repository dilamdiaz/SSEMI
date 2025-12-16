# app/admin/routes.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from sqlalchemy import func, or_
from app.admin.utils_reports import generar_reporte
from app.evaluador.models import Calificacion, DetalleCalificacion
from app.auth.models import Usuario
from datetime import datetime
from fastapi.responses import StreamingResponse
import io, csv
from app.auth.routes import get_current_user
from app.bitacora.crud import log_action

router = APIRouter(prefix="/admin/reportes", tags=["Reportes"])

@router.post("/datos")
def obtener_datos_reportes(filtros: dict, db: Session = Depends(get_db)):
    """
    Endpoint para obtener los datos del reporte según filtros.
    """
    data = generar_reporte(db, filtros)
    return data


@router.post("/generar")
def generar_reporte(filtros: dict, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    """
    Genera reportes de evaluaciones según filtros:
    filtros: {
        "programa": str,
        "instructor": str
    }
    """
    query = db.query(Calificacion).join(Usuario).join(DetalleCalificacion)

    # Filtrar por instructor
    if filtros.get("instructor"):
        nombre_busqueda = f"%{filtros['instructor']}%"
        query = query.filter(
            func.concat(
                Usuario.primer_nombre, " ",
                func.coalesce(Usuario.segundo_nombre, ""), " ",
                Usuario.primer_apellido, " ",
                func.coalesce(Usuario.segundo_apellido, "")
            ).ilike(nombre_busqueda)
        )



    calificaciones = query.all()

    # Preparar datos de respuesta
    evaluaciones = []
    puntajes = []
    estados = {}
    for c in calificaciones:
        nombre_completo = " ".join(filter(None, [
            c.usuario.primer_nombre,
            c.usuario.segundo_nombre,
            c.usuario.primer_apellido,
            c.usuario.segundo_apellido
        ]))
        programa = ", ".join([d.criterio for d in c.detalles])
        observaciones = " | ".join([d.observaciones for d in c.detalles if d.observaciones])

        evaluaciones.append({
            "id_calificacion": c.id_calificacion,
            "usuario_nombre": nombre_completo,
            "programa": programa,
            "puntaje_total": float(c.puntaje_total or 0),
            "estado": c.estado,
            "observaciones": observaciones
        })

        if c.puntaje_total:
            puntajes.append(float(c.puntaje_total))
        estados[c.estado] = estados.get(c.estado, 0) + 1

    total = len(calificaciones)
    promedio = sum(puntajes)/len(puntajes) if puntajes else 0
    porcentaje_cumplimiento = (sum(puntajes)/(total*100))*100 if total else 0

    # Historial simulado (puedes guardarlo en la BD si quieres)
    historial = [{
        "id": i+1,
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "filtros": str(filtros)
    } for i in range(3)]

    return {
        "evaluaciones": evaluaciones,
        "total_evaluaciones": total,
        "promedio_puntaje": round(promedio, 2),
        "porcentaje_cumplimiento": round(porcentaje_cumplimiento, 2),
        "estados": estados,
        "historial": historial
    }
    # BITÁCORA: generación de reporte por admin
    try:
        log_action(db=db, id_usuario=current_user.id_usuario, accion="GENERAR_REPORTE_ADMIN", descripcion=f"Generó reporte admin con filtros {filtros}", tabla_afectada="reportes")
    except Exception:
        pass
    
@router.get("/descargar/{id}")
def descargar_reporte(id: int, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    # Aquí puedes volver a generar los datos según id o filtros (aquí un ejemplo simple)
    calificaciones = db.query(Calificacion).all()

    salida = io.StringIO()
    writer = csv.writer(salida)
    writer.writerow(["ID", "Instructor", "Programa", "Puntaje Total", "Estado", "Observaciones"])

    for c in calificaciones:
        nombre = " ".join(filter(None, [c.usuario.primer_nombre, c.usuario.segundo_nombre, c.usuario.primer_apellido, c.usuario.segundo_apellido]))
        programas = ", ".join([d.criterio for d in c.detalles])
        observaciones = " | ".join([d.observaciones for d in c.detalles if d.observaciones])
        writer.writerow([c.id_calificacion, nombre, programas, c.puntaje_total, c.estado, observaciones])

    salida.seek(0)
    # BITÁCORA: descargar reporte csv
    try:
        log_action(db=db, id_usuario=current_user.id_usuario, accion="DESCARGAR_REPORTE", descripcion=f"Descargó reporte {id}", tabla_afectada="reportes", id_registro_afectado=id)
    except Exception:
        pass
    return StreamingResponse(
        iter([salida.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=reporte_{id}.csv"}
    )