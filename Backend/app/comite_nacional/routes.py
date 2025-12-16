# Backend/app/comite_nacional/routes.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.auth.models import Usuario
from app.auth.routes import get_current_user
from app.comite_nacional import schemas  
from app.auth.email_utils import send_email

router = APIRouter(
    prefix="/comite-nacional",
    tags=["Comité Nacional"]
)

# -------------------------------
# Listar evaluadores y estado Comité Nacional
# -------------------------------
@router.get("/", response_model=List[schemas.EvaluadorComite])
def listar_evaluadores_comite(db: Session = Depends(get_db),
                              current_user: Usuario = Depends(get_current_user)):
    if current_user.rol_fk != 2:  # Solo admin
        raise HTTPException(status_code=403, detail="Acceso no autorizado")

    # Rol 3 = evaluadores
    evaluadores = db.query(Usuario).filter(Usuario.rol_fk == 3).all()
    return evaluadores

# -------------------------------
# Activar evaluador en Comité Nacional
# -------------------------------
@router.put("/{id_usuario}/activar")
def activar_evaluador_comite(id_usuario: int,
                             db: Session = Depends(get_db),
                             current_user: Usuario = Depends(get_current_user)):
    if current_user.rol_fk != 2:
        raise HTTPException(status_code=403, detail="Acceso no autorizado")

    evaluador = db.query(Usuario).filter(
        Usuario.id_usuario == id_usuario, 
        Usuario.rol_fk == 3
    ).first()
    
    if not evaluador:
        raise HTTPException(status_code=404, detail="Evaluador no encontrado")

    # Verificar límite de 5 evaluadores activos
    activos_count = db.query(Usuario).filter(
        Usuario.rol_fk == 3, 
        Usuario.comite_nacional == True
    ).count()

    if activos_count >= 5:
        raise HTTPException(
            status_code=400, 
            detail="Ya hay 5 evaluadores activos en el Comité Nacional"
        )

    evaluador.comite_nacional = True
    db.commit()
    db.refresh(evaluador)

    # Enviar correo
    subject = "✅ Has sido seleccionado como evaluador del Comité Nacional"
    body = f"""
    <p>Hola {evaluador.primer_nombre},</p>
    <p>Has sido activado como miembro del Comité Nacional de evaluadores.</p>
    <p>Saludos,</p>
    <p>Equipo SSEMI</p>
    """
    try:
        send_email(evaluador.correo, subject, body)
    except Exception as e:
        print(f"❌ Error al enviar correo de activación: {e}")

    return {"message": f"{evaluador.primer_nombre} {evaluador.primer_apellido} activado en Comité Nacional"}

# -------------------------------
# Desactivar evaluador en Comité Nacional
# -------------------------------
@router.put("/{id_usuario}/desactivar")
def desactivar_evaluador_comite(id_usuario: int,
                                db: Session = Depends(get_db),
                                current_user: Usuario = Depends(get_current_user)):
    if current_user.rol_fk != 2:
        raise HTTPException(status_code=403, detail="Acceso no autorizado")

    evaluador = db.query(Usuario).filter(
        Usuario.id_usuario == id_usuario, 
        Usuario.rol_fk == 3
    ).first()
    if not evaluador:
        raise HTTPException(status_code=404, detail="Evaluador no encontrado")

    evaluador.comite_nacional = False
    db.commit()
    db.refresh(evaluador)

    # Enviar correo
    subject = "⚠️ Has sido desactivado del Comité Nacional"
    body = f"""
    <p>Hola {evaluador.primer_nombre},</p>
    <p>Tu estado en el Comité Nacional ha sido desactivado.</p>
    <p>Saludos,</p>
    <p>Equipo SSEMI</p>
    """
    try:
        send_email(evaluador.correo, subject, body)
    except Exception as e:
        print(f"❌ Error al enviar correo de desactivación: {e}")

    return {"message": f"{evaluador.primer_nombre} {evaluador.primer_apellido} desactivado en Comité Nacional"}
