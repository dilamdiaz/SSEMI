# app/mensajes/routes_admin.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.auth.routes import get_current_user
from app.auth.models import Usuario
from app.mensajes import models, schemas

router = APIRouter(
    prefix="/admin/mensajes",
    tags=["Mensajes - Admin"]
)

# ------------------------------------------------------
# Validar que solo admin acceda
# ------------------------------------------------------
def verificar_admin(user: Usuario):
    if user.rol_fk != 2:  # 2 = Administrador
        raise HTTPException(status_code=403, detail="Acceso restringido a administradores")

# ------------------------------------------------------
# Obtener mensajes según bandeja
# ------------------------------------------------------
@router.get("/", response_model=List[schemas.MensajeOut])
def obtener_mensajes(
    bandeja: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    verificar_admin(current_user)

    if bandeja == "recibidos":
        # Mensajes dirigidos al rol admin o directamente al usuario admin
        mensajes = db.query(models.Mensaje).filter(
            (models.Mensaje.destino_rol == 2) | 
            (models.Mensaje.destino_id == current_user.id_usuario)
        ).order_by(models.Mensaje.fecha_envio.desc()).all()

    elif bandeja == "enviados":
        mensajes = db.query(models.Mensaje).filter(
            models.Mensaje.remitente_id == current_user.id_usuario
        ).order_by(models.Mensaje.fecha_envio.desc()).all()

    else:
        raise HTTPException(status_code=400, detail="Bandeja inválida")

    # Construir remitente_nombre completo
    for m in mensajes:
        remitente = db.query(Usuario).filter(Usuario.id_usuario == m.remitente_id).first()
        m.remitente_nombre = f"{remitente.primer_nombre} {remitente.primer_apellido}" if remitente else None

    return mensajes

# ------------------------------------------------------
# Ver mensaje por ID
# ------------------------------------------------------
@router.get("/{mensaje_id}", response_model=schemas.MensajeOut)
def obtener_mensaje(
    mensaje_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    verificar_admin(current_user)

    mensaje = db.query(models.Mensaje).filter(models.Mensaje.id == mensaje_id).first()
    if not mensaje:
        raise HTTPException(status_code=404, detail="Mensaje no encontrado")

    # Permiso: admin como destinatario (rol o usuario) o remitente
    if mensaje.remitente_id != current_user.id_usuario and \
       mensaje.destino_rol != 2 and mensaje.destino_id != current_user.id_usuario:
        raise HTTPException(status_code=403, detail="No tiene permiso para ver este mensaje")

    # Marcar como leído si es recibido
    if (mensaje.destino_rol == 2 or mensaje.destino_id == current_user.id_usuario) and not mensaje.leido:
        mensaje.leido = True
        db.commit()

    remitente = db.query(Usuario).filter(Usuario.id_usuario == mensaje.remitente_id).first()
    mensaje.remitente_nombre = f"{remitente.primer_nombre} {remitente.primer_apellido}" if remitente else None

    return mensaje

# ------------------------------------------------------
# Enviar mensaje
# ------------------------------------------------------
@router.post("/", response_model=schemas.MensajeOut)
def enviar_mensaje(
    data: schemas.MensajeCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    verificar_admin(current_user)

    # Validaciones
    if not data.destino_rol and not data.destino_id:
        raise HTTPException(status_code=400, detail="Debe especificar rol o usuario destino")

    # Evitar enviarse mensaje a sí mismo
    if data.destino_id == current_user.id_usuario:
        raise HTTPException(status_code=400, detail="No puedes enviarte un mensaje a ti mismo")

    mensaje = models.Mensaje(
        remitente_id=current_user.id_usuario,
        destino_rol=data.destino_rol if data.destino_rol else 0,
        destino_id=data.destino_id,
        asunto=data.asunto,
        contenido=data.contenido,
        respuesta_a_id=data.respuesta_a_id
    )

    db.add(mensaje)
    db.commit()
    db.refresh(mensaje)

    # Agregar remitente_nombre completo
    mensaje.remitente_nombre = f"{current_user.primer_nombre} {current_user.primer_apellido}"

    return mensaje

# ------------------------------------------------------
# Eliminar mensaje (solo remitente)
# ------------------------------------------------------
@router.delete("/{mensaje_id}")
def eliminar_mensaje(
    mensaje_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    verificar_admin(current_user)

    mensaje = db.query(models.Mensaje).filter(models.Mensaje.id == mensaje_id).first()
    if not mensaje:
        raise HTTPException(status_code=404, detail="Mensaje no encontrado")

    if mensaje.remitente_id != current_user.id_usuario:
        raise HTTPException(status_code=403, detail="Solo el remitente puede eliminar este mensaje")

    db.delete(mensaje)
    db.commit()
    return {"message": "Mensaje eliminado"}
