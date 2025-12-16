#backend/app/evidencias/routes.py
import os
import shutil
import uuid
from datetime import date
from typing import List
import json
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.responses import FileResponse
from app.database import get_db
from app.evidencias import models, schemas
from app.auth.models import Usuario  # ✅ usamos el modelo real
from app.evidencias.models import Evidencia
from app.auth.routes import get_current_user
from app.bitacora.crud import log_action


APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Carpeta uploads dentro de 'app'
UPLOAD_DIR = os.path.join(APP_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Montar carpeta uploads como estática en FastAPI
# Esto debe hacerse en el main.py donde creas FastAPI, ejemplo:
# app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

router = APIRouter(prefix="/evidencias", tags=["Evidencias"])

# ==============================
# FUNCIONES AUXILIARES
# ==============================
def save_upload_file(upload_file: UploadFile) -> str:
    """Guarda un archivo dentro de uploads y devuelve solo el nombre."""
    filename = f"{uuid.uuid4()}_{upload_file.filename}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)
    return f"uploads/{filename}"  # Guardamos solo el nombre

# =============================
# RF007 - Subir evidencia única
# =============================
@router.post("/", response_model=schemas.EvidenciaResponse)
def subir_evidencia(
    titulo: str = Form(...),
    descripcion: str = Form(None),
    id_categoria_fk: int = Form(...),
    id_usuario_fk: int = Form(...),
    reportes_id_reporte: int = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    usuario = db.get(Usuario, id_usuario_fk)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    categoria = db.get(models.Categoria, id_categoria_fk)
    if not categoria:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")

    if reportes_id_reporte:
        reporte = db.get(models.Reporte, reportes_id_reporte)
        if not reporte:
            raise HTTPException(status_code=404, detail="Reporte no encontrado")

    # Guardar archivo
    file_path = save_upload_file(file)

    evidencia = models.Evidencia(
        titulo=titulo,
        descripcion=descripcion,
        id_categoria_fk=id_categoria_fk,
        id_usuario_fk=id_usuario_fk,
        reportes_id_reporte=reportes_id_reporte,
        archivos=file_path,
        fecha_evidencia=date.today(),
        estado_evidencia=models.EstadoEvidenciaEnum.Cargada
    )

    db.add(evidencia)
    db.commit()
    db.refresh(evidencia)

    historial = models.HistorialCarga(
        id_evidencia=evidencia.id_evidencia,
        id_instructor=id_usuario_fk,
        fecha_carga=date.today()
    )
    db.add(historial)
    db.commit()

    # BITÁCORA
    try:
        log_action(
            db=db,
            id_usuario=evidencia.id_usuario_fk,
            accion="CREAR_EVIDENCIA",
            descripcion=f"Creó evidencia {evidencia.titulo}",
            tabla_afectada="evidencias",
            id_registro_afectado=evidencia.id_evidencia
        )
    except Exception:
        pass

    return schemas.EvidenciaResponse.from_orm(evidencia)


# ====================================
# RF008 - Subir múltiples evidencias
# ====================================
@router.post("/multiple", response_model=schemas.EvidenciaResponse)
def subir_multiples(
    titulo: str = Form(...),
    descripcion: str = Form(None),
    id_categoria_fk: int = Form(...),
    id_usuario_fk: int = Form(...),
    formulario_json: str = Form(...),  # 🔥 JSON del formulario
    reportes_id_reporte: int = Form(None),
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    # ------------ VALIDACIONES ----------------
    usuario = db.get(Usuario, id_usuario_fk)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    categoria = db.get(models.Categoria, id_categoria_fk)
    if not categoria:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")

    if reportes_id_reporte:
        reporte = db.get(models.Reporte, reportes_id_reporte)
        if not reporte:
            raise HTTPException(status_code=404, detail="Reporte no encontrado")

    if not files or len(files) == 0:
        raise HTTPException(status_code=400, detail="Debe subir al menos 1 archivo")

    # ------------ GUARDAR ARCHIVOS ----------------
    rutas_archivos = []
    for file in files:
        file_path = save_upload_file(file)
        rutas_archivos.append(file_path)

    files = rutas_archivos

    # ------------ CONVERTIR FORMULARIO JSON ----------------
    try:
        formulario_dict = json.loads(formulario_json)
    except:
        raise HTTPException(
            status_code=400,
            detail="El campo 'formulario_json' no contiene un JSON válido"
        )

    # Lo guardamos como JSON str en la DB
    formulario_guardar = formulario_dict   # guardar como dict real

    # ------------ CREAR LA EVIDENCIA ----------------
    evidencia = models.Evidencia(
        titulo=titulo,
        descripcion=descripcion,
        id_categoria_fk=id_categoria_fk,
        id_usuario_fk=id_usuario_fk,
        reportes_id_reporte=reportes_id_reporte,
        archivos=rutas_archivos,
        formulario=formulario_dict,     # 🔥🔥 FORMULARIO COMPLETO AQUÍ
        fecha_evidencia=date.today(),
        estado_evidencia=models.EstadoEvidenciaEnum.Cargada
    )

    db.add(evidencia)
    db.commit()
    db.refresh(evidencia)

    # ------------ HISTORIAL ----------------
    historial = models.HistorialCarga(
        id_evidencia=evidencia.id_evidencia,
        id_instructor=id_usuario_fk,
        fecha_carga=date.today()
    )
    db.add(historial)
    db.commit()

    # BITÁCORA
    try:
        log_action(
            db=db,
            id_usuario=evidencia.id_usuario_fk,
            accion="CREAR_EVIDENCIA_MULTIPLE",
            descripcion=f"Creó múltiples evidencias {evidencia.titulo}",
            tabla_afectada="evidencias",
            id_registro_afectado=evidencia.id_evidencia
        )
    except Exception:
        pass

    return evidencia

# ==========================
# RF009 - Editar evidencia
# ==========================
@router.put("/{evidencia_id}", response_model=schemas.EvidenciaResponse)
def editar_evidencia(
    evidencia_id: int,
    titulo: str = Form(None),
    descripcion: str = Form(None),
    id_categoria_fk: int = Form(None),
    files: List[UploadFile] = File(None),   # 🔥 ahora permite múltiples archivos
    db: Session = Depends(get_db)
):
    evidencia = db.get(models.Evidencia, evidencia_id)
    if not evidencia:
        raise HTTPException(status_code=404, detail="Evidencia no encontrada")

    # 🔥 1. BLOQUEAR EDICIÓN SI YA FUE EVALUADA
    if evidencia.estado_evidencia == "Evaluada":
        raise HTTPException(status_code=400, detail="No se puede editar una evidencia evaluada")

    # 🔥 2. Actualizar campos normales
    if titulo:
        evidencia.titulo = titulo
    if descripcion:
        evidencia.descripcion = descripcion
    if id_categoria_fk:
        evidencia.id_categoria_fk = id_categoria_fk

    # 🔥 3. Reemplazar archivos COMPLETAMENTE si llegan nuevos
    if files and len(files) > 0:

        # --- Eliminar archivos antiguos del disco ---
        if evidencia.archivos:
            from pathlib import Path
            for old_file in evidencia.archivos:
                abs_path = Path("app/uploads") / Path(old_file).name
                if abs_path.exists():
                    try:
                        abs_path.unlink()
                    except:
                        pass

        # --- Guardar nuevos archivos ---
        nuevos_paths = []
        for f in files:
            path = save_upload_file(f)
            nuevos_paths.append(path)

        evidencia.archivos = nuevos_paths  # 🔥 solo archivos nuevos

    db.commit()
    db.refresh(evidencia)

    # 🔥 4. Registrar historial
    historial = models.HistorialCarga(
        id_evidencia=evidencia.id_evidencia,
        id_instructor=evidencia.id_usuario_fk,
        fecha_carga=date.today()
    )
    db.add(historial)
    db.commit()

    # BITÁCORA
    try:
        log_action(
            db=db,
            id_usuario=evidencia.id_usuario_fk,
            accion="EDITAR_EVIDENCIA",
            descripcion=f"Editó evidencia {evidencia.id_evidencia}",
            tabla_afectada="evidencias",
            id_registro_afectado=evidencia.id_evidencia
        )
    except Exception:
        pass

    return schemas.EvidenciaResponse.from_orm(evidencia)

# ==========================
# RF010 - Eliminar evidencia
# ==========================
@router.delete("/{evidencia_id}")
def eliminar_evidencia(evidencia_id: int, db: Session = Depends(get_db)):
    evidencia = db.get(models.Evidencia, evidencia_id)
    if not evidencia:
        raise HTTPException(status_code=404, detail="Evidencia no encontrada")

    # Eliminar historial asociado
    db.query(models.HistorialCarga).filter(
        models.HistorialCarga.id_evidencia == evidencia_id
    ).delete()

    # Eliminar archivos físicos si existen
    if evidencia.archivos:
        for archivo in evidencia.archivos:  # asumir que es una lista de rutas
            file_path = os.path.join("app", archivo)  # ajustar según tu estructura
            if os.path.exists(file_path):
                os.remove(file_path)

    db.delete(evidencia)
    db.commit()

    # BITÁCORA
    try:
        log_action(
            db=db,
            id_usuario=evidencia.id_usuario_fk,
            accion="ELIMINAR_EVIDENCIA",
            descripcion=f"Eliminó evidencia {evidencia.id_evidencia}",
            tabla_afectada="evidencias",
            id_registro_afectado=evidencia.id_evidencia
        )
    except Exception:
        pass

    return {"message": "Evidencia eliminada correctamente"}

# ==========================
# RF011 - Listar evidencias (versión final corregida)
# ==========================
@router.get("/", response_model=List[dict])
def listar_evidencias(
    id_usuario_fk: int = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.Evidencia)
    if id_usuario_fk:
        query = query.filter(models.Evidencia.id_usuario_fk == id_usuario_fk)

    evidencias = query.all()

    resultado = []
    for e in evidencias:
        db.refresh(e)  # 🔁 fuerza sincronización con la base de datos
        estado = (
            e.estado_evidencia.value
            if hasattr(e, "estado_evidencia") and e.estado_evidencia
            else "Desconocido"
        )
        resultado.append({
            "id": e.id_evidencia,
            "titulo": e.titulo,
            "descripcion": e.descripcion,
            "fecha": e.fecha_evidencia.isoformat() if e.fecha_evidencia else None,
            "url": f"http://127.0.0.1:8000/{e.archivos}" if e.archivos else None,
            "estado": estado,  # 🔹 valor real de la BD
            "calificado": estado == models.EstadoEvidenciaEnum.Evaluada.value
        })
    return resultado

# ==============================
# RF012 - Historial de evidencias
# ==============================

@router.get("/historial")
def historial(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    resultados = (
        db.query(
            models.HistorialCarga.id,             
            models.HistorialCarga.id_evidencia,
            models.Evidencia.titulo,
            models.Evidencia.descripcion,
            models.Evidencia.archivos,
            models.Evidencia.estado_evidencia,
            models.HistorialCarga.fecha_carga
        )
        .join(models.Evidencia, models.Evidencia.id_evidencia == models.HistorialCarga.id_evidencia)
        .filter(models.HistorialCarga.id_instructor == current_user.id_usuario)   # 🔥 FILTRO POR USUARIO
        .all()
    )

    response = []
    for r in resultados:

        archivos_lista = []

        if r.archivos:
            raw = r.archivos

            if isinstance(raw, str):
                try:
                    archivos_lista = json.loads(raw)
                except:
                    archivos_lista = [raw]
            elif isinstance(raw, list):
                archivos_lista = raw

        estado = (
            r.estado_evidencia.value
            if r.estado_evidencia
            else "Pendiente"
        )

        response.append({
            "id": r.id,
            "id_evidencia": r.id_evidencia,
            "titulo": r.titulo,
            "descripcion": r.descripcion,
            "fecha": r.fecha_carga.isoformat() if r.fecha_carga else None,
            "estado": estado,
            "archivos": archivos_lista
        })

    return response

@router.get("/descargar/{filename}")
async def descargar_archivo(filename: str):
    filepath = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(404, "Archivo no encontrado")
    return FileResponse(filepath, filename=filename)

@router.get("/detalle/{id_evidencia}")
def obtener_evidencia_detalle(id_evidencia: int, db: Session = Depends(get_db)):
    evidencia = db.query(Evidencia).filter(Evidencia.id_evidencia == id_evidencia).first()
    if not evidencia:
        raise HTTPException(status_code=404, detail="Evidencia no encontrada")

    # -------------------------
    # Archivos
    # -------------------------
    archivos_list = []
    if evidencia.archivos:
        import os, json
        if isinstance(evidencia.archivos, str):
            try:
                archivos_raw = json.loads(evidencia.archivos)
            except:
                # fallback: string separado por comas
                archivos_raw = evidencia.archivos.split(",")
        elif isinstance(evidencia.archivos, list):
            archivos_raw = evidencia.archivos
        else:
            archivos_raw = []

        for f in archivos_raw:
            f = f.strip()
            if f:
                archivos_list.append({
                    "nombre": os.path.basename(f).split("_",1)[-1],  # nombre real
                    "url": f"http://127.0.0.1:8000/" + f.replace("\\","/")  # URL descargable
                })

    # -------------------------
    # Formulario
    # -------------------------
    formulario_data = None
    if evidencia.formulario:
        raw = evidencia.formulario
        if isinstance(raw, dict):
            formulario_data = raw
        else:
            import json
            try:
                formulario_data = json.loads(raw)
            except:
                formulario_data = None

    return {
        "id": evidencia.id_evidencia,
        "titulo": evidencia.titulo,
        "descripcion": evidencia.descripcion,
        "categoria": evidencia.categoria.nombre_categoria if evidencia.categoria else None,
        "fecha_evidencia": evidencia.fecha_evidencia.isoformat() if evidencia.fecha_evidencia else None,
        "estado": evidencia.estado_evidencia.value if evidencia.estado_evidencia else None,
        "usuario": evidencia.usuario.primer_nombre if evidencia.usuario else None,
        "formulario": formulario_data,
        "archivos": archivos_list
    }