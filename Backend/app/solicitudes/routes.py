from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session, joinedload
from typing import List
from app.database import get_db
from app.auth.models import Usuario
from app.auth.routes import get_current_user
from app.bitacora.crud import log_action   # ✅ IMPORTANTE
from . import models, schemas

router = APIRouter(
    prefix="/solicitudes-correccion",
    tags=["Solicitudes de Corrección"]
)

# ======================================================
# Crear una nueva solicitud ✅ BITÁCORA
# ======================================================
@router.post("/", response_model=schemas.SolicitudResponse)
def crear_solicitud(
    solicitud: schemas.SolicitudCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    nueva_solicitud = models.SolicitudCorreccion(
        id_usuario_fk=current_user.id_usuario,
        campo_a_modificar=solicitud.campo_a_modificar,
        valor_actual=solicitud.valor_actual,
        nuevo_valor=solicitud.nuevo_valor,
        motivo=solicitud.motivo,
        estado_solicitud="Pendiente"
    )

    db.add(nueva_solicitud)
    db.commit()
    db.refresh(nueva_solicitud)

    # ✅ BITÁCORA
    log_action(
        db=db,
        id_usuario=current_user.id_usuario,
        accion="CREAR_SOLICITUD",
        descripcion=f"Creó solicitud de corrección para {solicitud.campo_a_modificar}",
        tabla_afectada="solicitudes_correccion",
        id_registro_afectado=nueva_solicitud.id_solicitud
    )

    return nueva_solicitud


# ======================================================
# Listar solicitudes
# ======================================================
@router.get("/", response_model=List[schemas.SolicitudResponse])
def listar_solicitudes(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    query = db.query(models.SolicitudCorreccion).options(joinedload(models.SolicitudCorreccion.usuario))

    if current_user.rol_fk not in [1, 2]:
        query = query.filter(models.SolicitudCorreccion.id_usuario_fk == current_user.id_usuario)

    return query.all()


# ======================================================
# Aprobar solicitud ✅ BITÁCORA
# ======================================================
@router.put("/{id_solicitud}/aprobar", response_model=schemas.SolicitudResponse)
def aprobar_solicitud(
    id_solicitud: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    solicitud = db.query(models.SolicitudCorreccion).filter(
        models.SolicitudCorreccion.id_solicitud == id_solicitud
    ).first()

    if not solicitud:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")

    if solicitud.estado_solicitud != "Pendiente":
        raise HTTPException(status_code=400, detail="Solicitud no pendiente")

    if current_user.rol_fk not in [1, 2]:
        raise HTTPException(status_code=403, detail="No autorizado")

    mapeo_campos = {
        "Primer Nombre": "primer_nombre",
        "Segundo Nombre": "segundo_nombre",
        "Primer Apellido": "primer_apellido",
        "Segundo Apellido": "segundo_apellido",
        "Número de Contacto": "numero_contacto",
        "Dirección": "direccion",
        "Correo": "correo",
        "Tipo de Documento": "tipo_documento",
        "Número Documento": "numero_documento",
        "Número de Documento": "numero_documento",
        "Grado": "grado",
        "Regional": "regional"
    }

    campo_real = mapeo_campos.get(solicitud.campo_a_modificar)
    if not campo_real:
        raise HTTPException(status_code=400, detail="Campo inválido")

    nuevo_valor = solicitud.nuevo_valor

    if campo_real in ["numero_documento", "numero_contacto"]:
        nuevo_valor = int(nuevo_valor)

    if campo_real == "tipo_documento" and nuevo_valor not in ["CC", "CE"]:
        raise HTTPException(status_code=400, detail="Tipo documento inválido")

    db.query(Usuario).filter(
        Usuario.id_usuario == solicitud.id_usuario_fk
    ).update({campo_real: nuevo_valor})

    solicitud.estado_solicitud = "Aprobada"
    db.commit()
    db.refresh(solicitud)

    # ✅ BITÁCORA
    log_action(
        db=db,
        id_usuario=current_user.id_usuario,
        accion="APROBAR_SOLICITUD",
        descripcion=f"Aprobó cambio de {solicitud.campo_a_modificar}",
        tabla_afectada="solicitudes_correccion",
        id_registro_afectado=solicitud.id_solicitud
    )

    return solicitud


# ======================================================
# Rechazar solicitud ✅ BITÁCORA
# ======================================================
@router.put("/{id_solicitud}/rechazar", response_model=schemas.SolicitudResponse)
def rechazar_solicitud(
    id_solicitud: int,
    motivo_respuesta: str = Body(..., embed=True),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    solicitud = db.query(models.SolicitudCorreccion).filter(
        models.SolicitudCorreccion.id_solicitud == id_solicitud
    ).first()

    if not solicitud:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")

    solicitud.estado_solicitud = "Rechazada"
    solicitud.motivo_respuesta = motivo_respuesta

    db.commit()
    db.refresh(solicitud)

    # ✅ BITÁCORA
    log_action(
        db=db,
        id_usuario=current_user.id_usuario,
        accion="RECHAZAR_SOLICITUD",
        descripcion=f"Rechazó solicitud: {solicitud.campo_a_modificar}",
        tabla_afectada="solicitudes_correccion",
        id_registro_afectado=solicitud.id_solicitud
    )

    return solicitud
