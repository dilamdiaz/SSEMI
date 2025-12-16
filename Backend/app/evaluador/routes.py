# Backend/app/evaluador/routes.py
from fastapi import File, UploadFile
from fastapi import APIRouter, Depends, HTTPException, Request, Form, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import date
import traceback  # ✅ para imprimir errores en consola
from app.evaluador import models, schemas
from app.database import get_db
from app.evidencias.models import Evidencia, EstadoEvidenciaEnum
from app.auth.models import Usuario
from app.evaluador.models import Calificacion, DetalleCalificacion, Evidencia, Usuario
from app.auth.routes import get_current_user
from typing import List, Optional
from sqlalchemy import func
from app.evaluador.schemas import ResultadoSchema
import json
from app.bitacora.crud import log_action

router = APIRouter(prefix="/evaluador", tags=["Evaluador"])
templates = Jinja2Templates(directory="frontend/templates")


# ---------------- PANEL PRINCIPAL ----------------
@router.get("/", response_class=HTMLResponse)
async def panel_evaluador(request: Request):
    return templates.TemplateResponse("evaluador/evaluador.html", {"request": request})

@router.get("/resultados")
def resultados(
    instructor_id: int = None,
    fecha_desde: date = None,
    fecha_hasta: date = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if current_user.rol_fk != 3:
        raise HTTPException(status_code=403, detail="Acceso restringido a evaluadores")

    query = db.query(DetalleCalificacion).join(Calificacion).join(Evidencia)
    query = query.filter(Calificacion.id_usuario_fk == current_user.id_usuario)

    if instructor_id:
        query = query.filter(Evidencia.id_usuario_fk == instructor_id)
    if fecha_desde:
        query = query.filter(Calificacion.fecha_calificacion >= fecha_desde)
    if fecha_hasta:
        query = query.filter(Calificacion.fecha_calificacion <= fecha_hasta)


    resultados = []
    for det in query.all():
        resultados.append({
            "id_calificacion": det.id_calificacion_fk,
            "evidencia": det.evidencia.titulo,
            "instructor": det.evidencia.usuario.primer_nombre + " " + det.evidencia.usuario.primer_apellido,
            "evaluador": det.calificacion.usuario.primer_nombre + " " + det.calificacion.usuario.primer_apellido,
            "puntaje": float(det.puntaje),
            "observaciones": det.observaciones or "",
            "fecha": det.calificacion.fecha_calificacion.isoformat() if det.calificacion.fecha_calificacion else ""
        })
    return resultados


# ---------------- API: LISTAR EVIDENCIAS ----------------
@router.get("/data/evidencias")
async def listar_evidencias(db: Session = Depends(get_db)):
    evidencias = db.query(Evidencia).filter(
        Evidencia.estado_evidencia.in_([
            EstadoEvidenciaEnum.Cargada,
            EstadoEvidenciaEnum.Borrador
        ])
    ).all()

    result = []
    for e in evidencias:

        # Convertir archivos JSON string → lista
        archivos_lista = []
        if e.archivos:
            try:
                archivos_lista = json.loads(e.archivos)
            except:
                archivos_lista = []

        # Convertir formulario JSON string → dict
        formulario_dict = None
        if e.formulario:
            try:
                formulario_dict = json.loads(e.formulario)
            except:
                formulario_dict = None

        result.append({
            "id": e.id_evidencia,
            "titulo": e.titulo,
            "descripcion": e.descripcion,
            "archivos": archivos_lista,
            "formulario": formulario_dict,  # 🔥 AGREGADO
            "fecha": e.fecha_evidencia.strftime("%Y-%m-%d") if e.fecha_evidencia else "",
            "estado": e.estado_evidencia.value if e.estado_evidencia else "",
            "id_usuario_fk": e.id_usuario_fk
        })

    return JSONResponse(result)



# ---------------- API: HISTORIAL DE CALIFICACIONES ----------------
@router.get("/data/historial")
async def historial_calificaciones(db: Session = Depends(get_db)):
    try:
        calificaciones = db.query(Calificacion).order_by(
            Calificacion.fecha_calificacion.desc()
        ).all()

        print(f"[DEBUG] /evaluador/data/historial found {len(calificaciones)} calificaciones")

        result = []
        for c in calificaciones:
            result.append({
                "id": c.id_calificacion,
                "puntaje": float(c.puntaje_total or 0),
                "fecha": c.fecha_calificacion.strftime("%Y-%m-%d") if c.fecha_calificacion else "",
                "estado": c.estado
            })
        return JSONResponse(result)
    except Exception as e:
        print(f"[ERROR] Error al obtener historial de calificaciones: {e}")
        return JSONResponse([])

#----------------- API: GUARDAR AVANCE -----------------
@router.post("/evidencia/{id_evidencia}/parcial")
def guardar_avance_parcial(
    id_evidencia: int,
    puntaje: float = Form(...),
    observacion: str = Form(""),
    db: Session = Depends(get_db),
):
    evidencia = db.query(Evidencia).filter(Evidencia.id_evidencia == id_evidencia).first()
    if not evidencia:
        raise HTTPException(status_code=404, detail="Evidencia no encontrada")

    # Buscar calificación existente con estado avance
    calificacion = (
        db.query(Calificacion)
        .filter(
            Calificacion.id_usuario_fk == evidencia.id_usuario_fk,
            Calificacion.estado == "en_progreso"
        )
        .first()
    )

    # Si no existe, crearla
    if not calificacion:
        calificacion = Calificacion(
            id_usuario_fk=evidencia.id_usuario_fk,
            puntaje_total=0,
            fecha_calificacion=date.today(),
            estado="en_progreso"
        )
        db.add(calificacion)
        db.commit()
        db.refresh(calificacion)

    # Buscar si ya había detalle para esta evidencia
    detalle = (
        db.query(DetalleCalificacion)
        .filter(
            DetalleCalificacion.id_calificacion_fk == calificacion.id_calificacion,
            DetalleCalificacion.id_evidencia_fk == id_evidencia
        )
        .first()
    )

    if detalle:
        detalle.puntaje = puntaje
        detalle.observaciones = observacion
    else:
        detalle = DetalleCalificacion(
            id_calificacion_fk=calificacion.id_calificacion,
            id_evidencia_fk=id_evidencia,
            puntaje=puntaje,
            observaciones=observacion
        )
        db.add(detalle)

    db.commit()

    return {"message": "Avance parcial guardado correctamente."}

# --------------------------------------------------------------
# CARGAR AVANCE PARCIAL (REANUDAR)
# --------------------------------------------------------------
@router.get("/evidencia/{id_evidencia}/avance")
def cargar_avance_parcial(id_evidencia: int, db: Session = Depends(get_db)):
    detalle = (
        db.query(DetalleCalificacion)
        .join(Calificacion)
        .filter(
            DetalleCalificacion.id_evidencia_fk == id_evidencia,
            Calificacion.estado == "en_progreso"
        )
        .first()
    )

    if not detalle:
        return None

    return {
        "puntaje": float(detalle.puntaje),
        "observacion": detalle.observaciones
    }

# ---------------- API: CALIFICAR EVIDENCIA ----------------
@router.post("/evidencia/{id_evidencia}")
async def calificar_evidencia(
    id_evidencia: int,
    puntaje: float = Form(...),
    observacion: str = Form(None),
    files: list[UploadFile] = File(None),   # 👈 Acepta archivos si los envías
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    evidencia = db.query(Evidencia).filter(Evidencia.id_evidencia == id_evidencia).first()
    if not evidencia:
        raise HTTPException(status_code=404, detail="Evidencia no encontrada")

    try:
        total = puntaje
        estado = "aprobado" if total >= 50 else "rechazado"

        # Guardar archivos si llegan
        saved_files_paths = []
        if files:
            for f in files:
                file_path = f"uploads/evaluacion/{id_evidencia}_{f.filename}"
                with open(file_path, "wb") as buffer:
                    buffer.write(await f.read())
                saved_files_paths.append(file_path)

        # Crear calificación
        calificacion = Calificacion(
            id_usuario_fk=evidencia.id_usuario_fk,
            puntaje_total=total,
            fecha_calificacion=date.today(),
            estado=estado,
        )
        db.add(calificacion)
        db.flush()

        # Crear detalle
        detalle = DetalleCalificacion(
            id_calificacion_fk=calificacion.id_calificacion,
            id_evidencia_fk=id_evidencia,
            puntaje=puntaje,
            observaciones=observacion,
        )
        db.add(detalle)

        # Estado evidencia
        evidencia.estado_evidencia = EstadoEvidenciaEnum.Evaluada
        db.flush()

        db.commit()

        # BITÁCORA: registro de calificación
        try:
            log_action(
                db=db,
                id_usuario=current_user.id_usuario,
                accion="CALIFICAR_EVIDENCIA",
                descripcion=f"Calificó evidencia {id_evidencia} con puntaje {total}",
                tabla_afectada="calificaciones",
                id_registro_afectado=calificacion.id_calificacion
            )
        except Exception:
            pass
        return {
            "message": "✅ Evidencia evaluada correctamente",
            "estado": estado,
            "archivos_guardados": saved_files_paths
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al calificar: {e}")

# --- Schema para resultados ---

class ResultadoSchema(BaseModel):
    id_detalle: int
    evidencia: str
    instructor: str
    evaluador_id: int
    puntaje: float
    observaciones: Optional[str]
    fecha: date

# --- Endpoint para obtener instructores ---
@router.get("/evaluador/instructores")
def get_instructores(db: Session = Depends(get_db)):
    return db.query(Usuario).filter(Usuario.rol_fk == 1).all()  # supongamos rol 2 = instructor

# --- Endpoint resultados con filtros opcionales ---
@router.get("/evaluador/resultados", response_model=List[ResultadoSchema])
def obtener_resultados(
    instructor_id: Optional[int] = Query(None),
    fecha_desde: Optional[date] = Query(None),
    fecha_hasta: Optional[date] = Query(None),
    puntaje: Optional[float] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(
        DetalleCalificacion.id_detalle,
        Evidencia.titulo.label("evidencia"),
        (Usuario.primer_nombre + " " + Usuario.primer_apellido).label("instructor"),
        Calificacion.id_usuario_fk.label("evaluador_id"),
        DetalleCalificacion.puntaje,
        DetalleCalificacion.observaciones,
        Calificacion.fecha_calificacion.label("fecha")
    ).join(
        Calificacion, DetalleCalificacion.id_calificacion_fk == Calificacion.id_calificacion
    ).join(
        Evidencia, DetalleCalificacion.id_evidencia_fk == Evidencia.id_evidencia
    ).join(
        Usuario, Evidencia.id_usuario_fk == Usuario.id_usuario
    )

    # --- Aplicar filtros opcionales ---
    if instructor_id:
        query = query.filter(Usuario.id_usuario == instructor_id)
    if fecha_desde:
        query = query.filter(Calificacion.fecha_calificacion >= fecha_desde)
    if fecha_hasta:
        query = query.filter(Calificacion.fecha_calificacion <= fecha_hasta)
    if puntaje is not None:
        query = query.filter(DetalleCalificacion.puntaje == puntaje)

    resultados = query.order_by(Calificacion.fecha_calificacion.desc()).all()
    return resultados