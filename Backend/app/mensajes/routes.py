# app/mensajes/routes.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List
from app.database import get_db
from app.auth.models import Usuario
from app.auth.routes import get_current_user
from app.mensajes import models, schemas

router = APIRouter(
    prefix="/mensajes",
    tags=["Mensajes"]
)

# ------------------------------------------------------
# ENVIAR MENSAJE (por rol o respuesta directa)
# ------------------------------------------------------
@router.post("/", response_model=schemas.MensajeOut)
def enviar_mensaje(
    datos: schemas.MensajeCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if datos.respuesta_a_id:
        # Es una respuesta directa a un mensaje existente
        mensaje_padre = db.query(models.Mensaje).filter_by(id=datos.respuesta_a_id).first()
        if not mensaje_padre:
            raise HTTPException(status_code=404, detail="Mensaje padre no encontrado")
        mensaje = models.Mensaje(
            remitente_id=current_user.id_usuario,
            destino_id=mensaje_padre.remitente_id,
            destino_rol=0,  # valor dummy para backend
            asunto=datos.asunto,
            contenido=datos.contenido,
            respuesta_a_id=datos.respuesta_a_id
        )
    else:
        # Mensaje nuevo a rol
        if datos.destino_rol not in [2, 3]:
            raise HTTPException(status_code=400, detail="Rol destino no permitido")
        if datos.destino_rol == current_user.rol_fk:
            raise HTTPException(status_code=400, detail="No puedes enviarte un mensaje a tu propio rol")
        mensaje = models.Mensaje(
            remitente_id=current_user.id_usuario,
            destino_rol=datos.destino_rol,
            asunto=datos.asunto,
            contenido=datos.contenido
        )

    db.add(mensaje)
    db.commit()
    db.refresh(mensaje)
    mensaje.remitente_nombre = f"{current_user.primer_nombre} {current_user.primer_apellido}"
    return mensaje

# ------------------------------------------------------
# BANDEJA DE ENTRADA (recibidos por rol o destino directo)
# ------------------------------------------------------
@router.get("/recibidos", response_model=List[schemas.MensajeOut])
def mensajes_recibidos(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    mensajes = (
        db.query(models.Mensaje)
        .filter(
            or_(
                models.Mensaje.destino_rol == current_user.rol_fk,
                models.Mensaje.destino_id == current_user.id_usuario
            )
        )
        .order_by(models.Mensaje.fecha_envio.desc())
        .all()
    )

    updated = False
    for m in mensajes:
        remitente = db.query(Usuario).filter(Usuario.id_usuario == m.remitente_id).first()
        m.remitente_nombre = f"{remitente.primer_nombre} {remitente.primer_apellido}" if remitente else None

        # Marcar como leído solo si es mensaje por rol y no se ha leído
        if m.destino_rol == current_user.rol_fk and not m.leido:
            m.leido = True
            updated = True

    if updated:
        db.commit()
    return mensajes

# ------------------------------------------------------
# ENVIADOS (por usuario)
# ------------------------------------------------------
@router.get("/enviados", response_model=List[schemas.MensajeOut])
def mensajes_enviados(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    mensajes = (
        db.query(models.Mensaje)
        .filter(models.Mensaje.remitente_id == current_user.id_usuario)
        .order_by(models.Mensaje.fecha_envio.desc())
        .all()
    )

    for m in mensajes:
        m.remitente_nombre = f"{current_user.primer_nombre} {current_user.primer_apellido}"
    return mensajes

# ------------------------------------------------------
# VER MENSAJE Y MARCAR LEÍDO
# ------------------------------------------------------
@router.get("/{mensaje_id}", response_model=schemas.MensajeOut)
def ver_mensaje(
    mensaje_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    mensaje = db.query(models.Mensaje).filter_by(id=mensaje_id).first()
    if not mensaje:
        raise HTTPException(status_code=404, detail="Mensaje no encontrado")

    # Permisos: remitente o rol destino o destino directo
    if mensaje.remitente_id != current_user.id_usuario and \
       mensaje.destino_rol != current_user.rol_fk and \
       mensaje.destino_id != current_user.id_usuario:
        raise HTTPException(status_code=403, detail="No tiene permiso para ver este mensaje")

    # Marcar como leído si corresponde
    if (mensaje.destino_rol == current_user.rol_fk or mensaje.destino_id == current_user.id_usuario) and not mensaje.leido:
        mensaje.leido = True
        db.commit()

    remitente = db.query(Usuario).filter(Usuario.id_usuario == mensaje.remitente_id).first()
    mensaje.remitente_nombre = f"{remitente.primer_nombre} {remitente.primer_apellido}" if remitente else None

    return mensaje

# ------------------------------------------------------
# ELIMINAR MENSAJE (solo remitente)
# ------------------------------------------------------
@router.delete("/{mensaje_id}")
def eliminar_mensaje(
    mensaje_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    mensaje = db.query(models.Mensaje).filter_by(id=mensaje_id).first()
    if not mensaje:
        raise HTTPException(status_code=404, detail="Mensaje no encontrado")
    if mensaje.remitente_id != current_user.id_usuario:
        raise HTTPException(status_code=403, detail="Solo el remitente puede eliminar este mensaje")
    db.delete(mensaje)
    db.commit()
    return {"message": "Mensaje eliminado"}
