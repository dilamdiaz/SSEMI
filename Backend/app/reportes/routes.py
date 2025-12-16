# app/reportes/routes.py
import os
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import List
from app.auth.routes import get_current_user
from app.database import get_db
from app.reportes.models import ReporteSSEMI
from app.reportes.schemas import ReporteCreate, ReporteSchema
from app.auth.models import Usuario
from app.evidencias.models import Evidencia
from app.evaluador.models import Calificacion
from app.solicitudes.models import SolicitudCorreccion

from openpyxl import Workbook
from app.bitacora.crud import log_action

try:
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except Exception:
    REPORTLAB_AVAILABLE = False

router = APIRouter(prefix="/reportes", tags=["Reportes"])
EXPORT_DIR = "exports"
os.makedirs(EXPORT_DIR, exist_ok=True)

# -----------------------
# CRUD
# -----------------------
@router.post("/", response_model=ReporteSchema)
def crear_reporte(reporte: ReporteCreate, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    nuevo = ReporteSSEMI(
        titulo=reporte.titulo,
        descripcion=reporte.descripcion,
        tipo_reporte=reporte.tipo_reporte,
        fecha_generacion=date.today(),
        id_usuario_accion=current_user.id_usuario

    )
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    # BITÁCORA: creación de reporte
    try:
        log_action(
            db=db,
            id_usuario=current_user.id_usuario,
            accion="CREAR_REPORTE",
            descripcion=f"Creó reporte {nuevo.titulo}",
            tabla_afectada="reportes",
            id_registro_afectado=nuevo.id_reporte
        )
    except Exception:
        pass
    return nuevo

@router.get("/", response_model=List[ReporteSchema])
def listar_reportes(db: Session = Depends(get_db)):
    return db.query(ReporteSSEMI).order_by(ReporteSSEMI.fecha_generacion.desc()).all()

@router.get("/{id_reporte}", response_model=ReporteSchema)
def obtener_reporte(id_reporte: int, db: Session = Depends(get_db)):
    rpt = db.query(ReporteSSEMI).filter(ReporteSSEMI.id_reporte == id_reporte).first()
    if not rpt:
        raise HTTPException(status_code=404, detail="Reporte no encontrado")
    return rpt

# -----------------------
# DATOS POR TIPO
# -----------------------
@router.get("/datos/usuarios")
def datos_usuarios(nombre: str = Query(None), regional: str = Query(None), db: Session = Depends(get_db)):
    q = db.query(
        Usuario.id_usuario,
        func.concat(
            Usuario.primer_nombre, ' ',
            func.coalesce(Usuario.segundo_nombre,''), ' ',
            Usuario.primer_apellido, ' ',
            Usuario.segundo_apellido
        ).label("nombre_completo"),
        Usuario.numero_documento,
        Usuario.regional,
        Usuario.estado
    )
    if nombre:
        like = f"%{nombre}%"
        q = q.filter(or_(
            Usuario.primer_nombre.ilike(like),
            Usuario.segundo_nombre.ilike(like),
            Usuario.primer_apellido.ilike(like),
            Usuario.segundo_apellido.ilike(like)
        ))
    if regional:
        q = q.filter(Usuario.regional.ilike(f"%{regional}%"))
    rows = q.all()
    return [dict(r._mapping) for r in rows]

@router.get("/datos/evidencias")
def datos_evidencias(instructor: str = Query(None), db: Session = Depends(get_db)):
    q = db.query(
        Evidencia.id_evidencia,
        Evidencia.titulo,
        Evidencia.fecha_evidencia,
        Evidencia.estado_evidencia,
        func.concat(
            Usuario.primer_nombre, ' ',
            func.coalesce(Usuario.segundo_nombre,''), ' ',
            Usuario.primer_apellido, ' ',
            Usuario.segundo_apellido
        ).label("instructor")
    ).join(Usuario, Usuario.id_usuario == Evidencia.id_usuario_fk)
    if instructor:
        like = f"%{instructor}%"
        q = q.filter(or_(
            Usuario.primer_nombre.ilike(like),
            Usuario.primer_apellido.ilike(like)
        ))
    rows = q.all()
    return [dict(r._mapping) for r in rows]

@router.get("/datos/evaluaciones")
def datos_evaluaciones(instructor: str = Query(None), db: Session = Depends(get_db)):
    q = db.query(
        Calificacion.id_calificacion,
        Calificacion.id_usuario_fk.label("id_usuario_fk"),
        func.concat(
            Usuario.primer_nombre, ' ',
            func.coalesce(Usuario.segundo_nombre,''), ' ',
            Usuario.primer_apellido, ' ',
            Usuario.segundo_apellido
        ).label("instructor"),
        Calificacion.puntaje_total,
        Calificacion.estado,
        Calificacion.fecha_calificacion
    ).join(Usuario, Usuario.id_usuario == Calificacion.id_usuario_fk)
    if instructor:
        like = f"%{instructor}%"
        q = q.filter(or_(
            Usuario.primer_nombre.ilike(like),
            Usuario.primer_apellido.ilike(like)
        ))
    rows = q.all()
    return [dict(r._mapping) for r in rows]

@router.get("/datos/solicitudes_correccion")
def datos_solicitudes(instructor: str = Query(None), db: Session = Depends(get_db)):
    q = db.query(
        SolicitudCorreccion.id_solicitud,
        func.concat(
            Usuario.primer_nombre, ' ',
            func.coalesce(Usuario.segundo_nombre,''), ' ',
            Usuario.primer_apellido, ' ',
            Usuario.segundo_apellido
        ).label("instructor"),
        SolicitudCorreccion.campo_a_modificar,
        SolicitudCorreccion.motivo,
        SolicitudCorreccion.estado_solicitud,
        SolicitudCorreccion.fecha_solicitud
    ).join(Usuario, Usuario.id_usuario == SolicitudCorreccion.id_usuario_fk)
    if instructor:
        like = f"%{instructor}%"
        q = q.filter(or_(
            Usuario.primer_nombre.ilike(like),
            Usuario.primer_apellido.ilike(like)
        ))
    rows = q.all()
    return [dict(r._mapping) for r in rows]

@router.get("/datos/actividad_general")
def datos_actividad_general(db: Session = Depends(get_db)):
    return {
        "total_usuarios": db.query(func.count(Usuario.id_usuario)).scalar(),
        "total_evidencias": db.query(func.count(Evidencia.id_evidencia)).scalar(),
        "total_calificaciones": db.query(func.count(Calificacion.id_calificacion)).scalar(),
        "total_solicitudes": db.query(func.count(SolicitudCorreccion.id_solicitud)).scalar()
    }

# -----------------------
# UTIL: obtener dataset simple
# -----------------------
def obtener_dataset_simple(reporte: ReporteSSEMI, db: Session):
    t = reporte.tipo_reporte
    if t == "usuarios":
        return datos_usuarios(nombre=None, regional=None, db=db)
    if t == "evidencias":
        return datos_evidencias(instructor=None, db=db)
    if t == "evaluaciones":
        return datos_evaluaciones(instructor=None, db=db)
    if t == "solicitudes_correccion":
        return datos_solicitudes(instructor=None, db=db)
    if t == "actividad_general":
        return [datos_actividad_general(db=db)]
    return []

# -----------------------
# EXPORT EXCEL
# -----------------------
@router.get("/{id_reporte}/export/excel")
def exportar_excel(id_reporte: int, db: Session = Depends(get_db)):
    reporte = db.query(ReporteSSEMI).filter(ReporteSSEMI.id_reporte == id_reporte).first()
    if not reporte:
        raise HTTPException(status_code=404, detail="Reporte no encontrado")
    dataset = obtener_dataset_simple(reporte, db)
    path = f"{EXPORT_DIR}/reporte_{id_reporte}.xlsx"

    wb = Workbook()
    ws = wb.active
    ws.title = "Reporte SSEMI"

    if dataset:
        headers = list(dataset[0].keys())
        ws.append(headers)
        for row in dataset:
            ws.append([row.get(h, "") for h in headers])
    else:
        ws.append(["No hay datos disponibles"])

    wb.save(path)
    # BITÁCORA: exportar reporte excel
    try:
        # intentar obtener usuario si está autenticado (no obligatorio)
        # Si quieres forzar auth, añade current_user: Usuario = Depends(get_current_user)
        log_action(db=db, id_usuario=None, accion="EXPORTAR_REPORTE_EXCEL", descripcion=f"Exportó reporte {id_reporte} (Excel)", tabla_afectada="reportes", id_registro_afectado=id_reporte)
    except Exception:
        pass

    return FileResponse(
        path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=f"reporte_{id_reporte}.xlsx"
    )

# -----------------------
# EXPORT PDF (versión mejorada con diseño SSEMI)
# -----------------------
@router.get("/{id_reporte}/export/pdf")
def exportar_pdf(id_reporte: int, db: Session = Depends(get_db)):
    reporte = db.query(ReporteSSEMI).filter(ReporteSSEMI.id_reporte == id_reporte).first()
    if not reporte:
        raise HTTPException(status_code=404, detail="Reporte no encontrado")

    dataset = obtener_dataset_simple(reporte, db)
    path = f"{EXPORT_DIR}/reporte_{id_reporte}.pdf"

    if not REPORTLAB_AVAILABLE:
        raise HTTPException(status_code=500, detail="ReportLab no está instalado")

    # Colores SSEMI
    COLOR_PRIMARIO = colors.HexColor("#fc7e2b")
    COLOR_SECUNDARIO = colors.HexColor("#f6d9c6")
    COLOR_TEXTO_HEADER = colors.white

    # Documento
    doc = SimpleDocTemplate(
        path,
        pagesize=letter,
        leftMargin=25,
        rightMargin=25,
        topMargin=40,
        bottomMargin=25
    )

    styles = getSampleStyleSheet()
    styles["Normal"].fontSize = 9

    elements = []

    # Logo
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
    logo_path = os.path.join(BASE_DIR, "frontend", "static", "images", "logo3.png")

    if os.path.exists(logo_path):
        elements.append(Image(logo_path, width=140, height=70))
        elements.append(Spacer(1, 10))

    # Header
    header_table = Table([[f"REPORTE SSEMI #{id_reporte}"]], colWidths=[480])
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), COLOR_PRIMARIO),
        ("TEXTCOLOR", (0, 0), (-1, -1), COLOR_TEXTO_HEADER),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTSIZE", (0, 0), (-1, -1), 14),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 10))

    # ----------- INFORMACIÓN SUPERIOR (alineada correctamente) ------------
    info_table = Table([
        ["Título:", reporte.titulo],
        ["Tipo:", reporte.tipo_reporte],
        ["Fecha de generación:", str(reporte.fecha_generacion)]
    ], colWidths=[120, 350])

    info_table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))

    elements.append(info_table)
    elements.append(Spacer(1, 10))


    # ---------------------- CONVERSIÓN DE ESTADO -------------------------
    if dataset:
        # Convertir True/False → Activo/Inactivo
        for fila in dataset:
            for k, v in fila.items():
                if isinstance(v, bool):
                    fila[k] = "Activo" if v else "Inactivo"

        headers = list(dataset[0].keys())
        table_data = [headers]

        for row in dataset:
            table_data.append([
                Paragraph(str(row.get(h, "")), styles["Normal"]) for h in headers
            ])

        col_widths = [480 / len(headers)] * len(headers)

        table = Table(table_data, colWidths=col_widths, repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), COLOR_PRIMARIO),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.3, colors.black),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 3),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ]))

        elements.append(table)
    else:
        elements.append(Paragraph("No hay datos disponibles", styles["Normal"]))

    doc.build(elements)
    # BITÁCORA: exportar reporte pdf
    try:
        log_action(db=db, id_usuario=None, accion="EXPORTAR_REPORTE_PDF", descripcion=f"Exportó reporte {id_reporte} (PDF)", tabla_afectada="reportes", id_registro_afectado=id_reporte)
    except Exception:
        pass

    return FileResponse(path, media_type="application/pdf", filename=f"reporte_{id_reporte}.pdf")
