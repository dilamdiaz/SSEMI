# app/auth/routes.py
from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from datetime import datetime, timedelta
from app.database import get_db
from app.auth.models import Usuario, RecuperacionContrasena
from app.auth.schemas import (
    LoginRequest, TokenResponse, UserCreate, UserOut,
    UserSelfUpdate, UserUpdate, PasswordRecoveryRequest,
    PasswordResetRequest, CambiarEstadoRequest, CambiarEstadoResponse,
    TwoFactorRequest, TwoFactorVerify, TwoFactorResponse
)
from app.auth.utils import hash_password, verify_password
from app.auth.jwt_handler import create_access_token, SECRET_KEY, ALGORITHM, ACCESS_KEY_ADMIN
from app.auth.email_utils import send_email
import secrets
import traceback
from app.bitacora.crud import log_action

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")
router = APIRouter(tags=["Auth"])

# =================================================================
# -------------------- Endpoint: Register -------------------------
# =================================================================
@router.post("/register", response_model=UserOut)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(Usuario).filter(
        (Usuario.correo == user.correo) |
        (Usuario.numero_documento == user.numero_documento)
    ).first()
    
    if existing_user:
        raise HTTPException(status_code=400, detail="El usuario ya existe")

    rol_protegido = user.rol_fk != 1
    if rol_protegido and user.clave_acceso != ACCESS_KEY_ADMIN:
        raise HTTPException(status_code=401, detail="Clave de acceso inválida para este rol")

    new_user = Usuario(
        primer_nombre=user.primer_nombre,
        segundo_nombre=user.segundo_nombre,
        primer_apellido=user.primer_apellido,
        segundo_apellido=user.segundo_apellido,
        tipo_documento=user.tipo_documento,
        numero_documento=user.numero_documento,
        correo=user.correo,
        rol_fk=user.rol_fk,
        contraseña=hash_password(user.contraseña),
        numero_contacto=user.numero_contacto,
        direccion=user.direccion,
        estado=True,

        # -------------------------
        # Nuevos campos
        # -------------------------
        grado=user.grado,
        regional=user.regional or "Distrito Capital"
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    # BITÁCORA: nuevo usuario (auto-registro)
    try:
        log_action(
            db=db,
            id_usuario=new_user.id_usuario,
            accion="CREAR_USUARIO",
            descripcion=f"Registró el usuario {new_user.correo}",
            tabla_afectada="usuarios",
            id_registro_afectado=new_user.id_usuario
        )
    except Exception:
        pass
    return new_user

# =================================================================
# -------------------- Endpoint: Login ----------------------------
# =================================================================
@router.post("/login", response_model=TwoFactorResponse)
def login_send_2fa(request: LoginRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    try:
        user = db.query(Usuario).filter(Usuario.correo == request.correo).first()
        if not user or not verify_password(request.contraseña, user.contraseña):
            raise HTTPException(status_code=401, detail="Credenciales incorrectas")

        if not user.estado:
            raise HTTPException(status_code=403, detail="Cuenta Desactivada. Contacte al Administrador.")

        # Generar código 2FA de 6 dígitos
        codigo = f"{secrets.randbelow(1000000):06d}"
        user.two_factor_code = codigo
        user.two_factor_expiration = datetime.utcnow() + timedelta(minutes=5)

        db.commit()
        db.refresh(user)

        # Enviar correo con código
        subject = "Código de verificación SSEMI"
        body = f"""
        <p>Hola {user.primer_nombre},</p>
        <p>Tu código de verificación es: <b>{codigo}</b></p>
        <p>Este código expirará en 5 minutos.</p>
        """
        # Enviar el correo en background para evitar bloquear la petición
        try:
            background_tasks.add_task(send_email, user.correo, subject, body)
        except Exception as e:
            print(f"⚠️ No se pudo programar background task de email: {e}")

        # Si está permitido para debug, devolver el código en la respuesta (solo para pruebas)
        from os import getenv
        allow_debug = getenv("ALLOW_2FA_CODE_IN_RESPONSE", "false").lower() == "true"
        if allow_debug:
            return {"mensaje": "Código de verificación (debug)", "codigo": codigo}

        return {"mensaje": "Código de verificación enviado correctamente"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error no capturado en /login: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

# =================================================================
# -------------------- Endpoint: Verificar 2FA --------------------
# =================================================================
@router.post("/2fa/verify", response_model=TokenResponse)
def verify_2fa_code(data: TwoFactorVerify, db: Session = Depends(get_db)):
    user = db.query(Usuario).filter(Usuario.correo == data.correo).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # Validar código y expiración
    if user.two_factor_code != data.codigo:
        raise HTTPException(status_code=400, detail="Código inválido")
    if not user.two_factor_expiration or datetime.utcnow() > user.two_factor_expiration:
        raise HTTPException(status_code=400, detail="Código expirado")

    # Limpiar código después de verificar
    user.two_factor_code = None
    user.two_factor_expiration = None
    db.commit()
    db.refresh(user)

    # Crear token JWT
    token = create_access_token({"sub": user.correo, "role": user.rol_fk})

    # BITÁCORA: inicio de sesión exitoso
    try:
        log_action(
            db=db,
            id_usuario=user.id_usuario,
            accion="INICIO_SESION",
            descripcion=f"Usuario inició sesión",
            tabla_afectada="usuarios",
            id_registro_afectado=user.id_usuario
        )
    except Exception:
        pass

    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user.id_usuario,
        "correo": user.correo,
        "rol": user.rol_fk
    }

# =================================================================
# -------------------- Función Auxiliar ---------------------------
# =================================================================
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        correo: str = payload.get("sub")
        if correo is None:
            raise HTTPException(status_code=401, detail="Token inválido")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")
    
    user = db.query(Usuario).filter(Usuario.correo == correo).first()
    if user is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user

# =================================================================
# -------------------- Endpoint: /me ------------------------------
# =================================================================
@router.get("/me", response_model=UserOut)
def read_users_me(current_user: Usuario = Depends(get_current_user)):
    return current_user

# =================================================================
# ---- Endpoint: Usuario actual actualiza su perfil ---------------
# =================================================================
@router.put("/me", response_model=UserOut)
def update_my_profile(
    update: UserSelfUpdate,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if update.numero_contacto is not None:
        current_user.numero_contacto = update.numero_contacto
    if update.direccion is not None:
        current_user.direccion = update.direccion

    db.commit()
    db.refresh(current_user)
    return current_user

# =================================================================
# ---- Solicitud de recuperación de contraseña --------------------
# =================================================================
@router.post("/password/forgot")
def password_recovery(
    data: PasswordRecoveryRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    user = db.query(Usuario).filter(Usuario.correo == data.correo).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    token = secrets.token_urlsafe(32)
    registro = RecuperacionContrasena(
        id_usuario_fk=user.id_usuario,
        token=token,
        fecha_creacion=datetime.utcnow(),
        usado=False
    )
    db.add(registro)
    db.commit()
    db.refresh(registro)

    reset_link = f"{request.base_url}reset_password?token={token}"
    subject = "Recuperación de contraseña - Proyecto SSEMI"
    body = f"""
    <p>Hola {user.primer_nombre},</p>
    <p>Hemos recibido una solicitud para restablecer tu contraseña.</p>
    <p>Haz clic en el siguiente enlace para continuar:</p>
    <p><a href="{reset_link}">{reset_link}</a></p>
    <p>Este enlace expirará en 1 hora.</p>
    <br>
    <p>Si no solicitaste este cambio, ignora este mensaje.</p>
    """
    try:
        # Enviar en background para no bloquear la petición
        background_tasks.add_task(send_email, user.correo, subject, body)
    except Exception as e:
        print(f"⚠️ No se pudo programar envío de correo de recuperación: {e}")
        traceback.print_exc()
        # not raising a 500 to avoid blocking the user action; log and continue

    return {"message": "Se ha enviado un enlace de recuperación a tu correo"}

# =================================================================
# ---- Restablecimiento de contraseña -----------------------------
# =================================================================
@router.post("/password/reset")
def reset_password(data: PasswordResetRequest, db: Session = Depends(get_db)):
    registro = db.query(RecuperacionContrasena).filter(
        RecuperacionContrasena.token == data.token,
        RecuperacionContrasena.usado == False
    ).first()

    if not registro:
        raise HTTPException(status_code=400, detail="Token inválido o ya usado")

    if registro.fecha_creacion + timedelta(hours=1) < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Token expirado")

    user = db.query(Usuario).filter(Usuario.id_usuario == registro.id_usuario_fk).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    user.contraseña = hash_password(data.nueva_contraseña)
    registro.usado = True
    db.commit()

    return {"message": "Contraseña restablecida correctamente"}

# =================================================================
# ---- Cambiar estado usuario -------------------------------------
# =================================================================
@router.put("/usuarios/{id_usuario}/estado", response_model=CambiarEstadoResponse)
def actualizar_estado_usuario(
    id_usuario: int,
    data: CambiarEstadoRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    if current_user.rol_fk != 2:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo un administrador puede cambiar el estado de usuarios."
        )

    usuario = db.query(Usuario).filter(Usuario.id_usuario == id_usuario).first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )

    usuario.estado = data.estado
    db.commit()
    db.refresh(usuario)

    # BITÁCORA: cambio estado por admin
    try:
        log_action(
            db=db,
            id_usuario=current_user.id_usuario,
            accion="ACTUALIZAR_ESTADO_USUARIO",
            descripcion=f"Actualizó estado usuario {usuario.id_usuario} a {usuario.estado}",
            tabla_afectada="usuarios",
            id_registro_afectado=usuario.id_usuario
        )
    except Exception:
        pass

    return CambiarEstadoResponse(
        id_usuario=usuario.id_usuario,
        estado_nuevo=usuario.estado,
        mensaje=f"El estado del usuario {usuario.id_usuario} fue actualizado correctamente."
    )

# =================================================================
# ---- Listar todos los usuarios (solo admin) ---------------------
# =================================================================
@router.get("/usuarios", response_model=list[UserOut])
def listar_usuarios(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    if current_user.rol_fk != 2:
        raise HTTPException(status_code=403, detail="Acceso restringido a administradores")
    return db.query(Usuario).all()

# =================================================================
# ---- Obtener usuario por ID (solo admin) -----------------------
# =================================================================
@router.get("/usuarios/{id_usuario}", response_model=UserOut)
def obtener_usuario(
    id_usuario: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    if current_user.rol_fk != 2:
        raise HTTPException(status_code=403, detail="Acceso restringido a administradores")

    usuario = db.query(Usuario).filter(Usuario.id_usuario == id_usuario).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return usuario

# =================================================================
# ---- Actualizar usuario por ID (solo admin) --------------------
# =================================================================
@router.put("/usuarios/{id_usuario}", response_model=UserOut)
def actualizar_usuario(
    id_usuario: int,
    data: UserUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    if current_user.rol_fk != 2:
        raise HTTPException(status_code=403, detail="Solo administradores pueden actualizar datos")

    usuario = db.query(Usuario).filter(Usuario.id_usuario == id_usuario).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    for field, value in data.dict(exclude_unset=True).items():
        setattr(usuario, field, value)

    db.commit()
    db.refresh(usuario)
    # BITÁCORA: admin editó usuario
    try:
        log_action(
            db=db,
            id_usuario=current_user.id_usuario,
            accion="EDITAR_USUARIO",
            descripcion=f"Editó usuario {usuario.id_usuario}",
            tabla_afectada="usuarios",
            id_registro_afectado=usuario.id_usuario
        )
    except Exception:
        pass
    return usuario


# =================================================================
# ---- Eliminar usuario por ID (solo admin) ----------------------
# =================================================================
@router.delete("/usuarios/{id_usuario}")
def eliminar_usuario(
    id_usuario: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    if current_user.rol_fk != 2:
        raise HTTPException(status_code=403, detail="Solo administradores pueden eliminar usuarios")

    usuario = db.query(Usuario).filter(Usuario.id_usuario == id_usuario).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    db.delete(usuario)
    db.commit()
    # BITÁCORA: admin eliminó usuario
    try:
        log_action(
            db=db,
            id_usuario=current_user.id_usuario,
            accion="ELIMINAR_USUARIO",
            descripcion=f"Eliminó usuario {id_usuario}",
            tabla_afectada="usuarios",
            id_registro_afectado=id_usuario
        )
    except Exception:
        pass
    return {"mensaje": f"Usuario {id_usuario} eliminado correctamente"}
