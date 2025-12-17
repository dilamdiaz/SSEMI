from pydantic import BaseModel, EmailStr
from typing import Optional
from enum import Enum
from datetime import datetime

# Enum igual que en la base de datos
class TipoDocumentoEnum(str, Enum):
    CC = "CC"
    CE = "CE"

# -------------------------
# Esquemas para REGISTRO
# -------------------------

class UserCreate(BaseModel):
    primer_nombre: str
    segundo_nombre: Optional[str] = None
    primer_apellido: str
    segundo_apellido: str
    tipo_documento: TipoDocumentoEnum
    numero_documento: int
    correo: EmailStr
    contraseña: str
    numero_contacto: Optional[int] = None
    direccion: Optional[str] = None
    rol_fk: int
    clave_acceso: Optional[str] = None

    # NUEVOS CAMPOS
    grado: Optional[str] = None
    regional: Optional[str] = "Distrito Capital"


class UserOut(BaseModel):
    id_usuario: int
    primer_nombre: str
    segundo_nombre: Optional[str] = None
    primer_apellido: str
    segundo_apellido: Optional[str] = None
    tipo_documento: TipoDocumentoEnum
    numero_documento: int
    correo: EmailStr
    rol_fk: int
    numero_contacto: Optional[int] = None
    direccion: Optional[str] = None
    estado: bool

    # NUEVOS CAMPOS
    grado: Optional[str] = None
    regional: str

    class Config:
        from_attributes = True


# -------------------------
# Esquemas para LOGIN
# -------------------------

class LoginRequest(BaseModel):
    correo: EmailStr
    contraseña: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    correo: str
    rol: int


class UserSelfUpdate(BaseModel):
    numero_contacto: Optional[int] = None
    direccion: Optional[str] = None


# para administradores
class UserUpdate(BaseModel):
    primer_nombre: Optional[str] = None
    segundo_nombre: Optional[str] = None
    primer_apellido: Optional[str] = None
    segundo_apellido: Optional[str] = None
    tipo_documento: Optional[str] = None
    numero_documento: Optional[int] = None
    correo: Optional[EmailStr] = None
    numero_contacto: Optional[int] = None
    direccion: Optional[str] = None
    rol_fk: Optional[int] = None
    clave_acceso: Optional[str] = None
    grado: Optional[str] = None
    regional: Optional[str] = None


class PasswordRecoveryRequest(BaseModel):
    correo: EmailStr


class PasswordResetRequest(BaseModel):
    token: str
    nueva_contraseña: str


class CambiarEstadoRequest(BaseModel):
    estado: bool
    motivo: str | None = None


class CambiarEstadoResponse(BaseModel):
    id_usuario: int
    estado_nuevo: bool
    mensaje: str


# -------------------------
# Esquemas para 2FA
# -------------------------

class TwoFactorRequest(BaseModel):
    correo: EmailStr


class TwoFactorVerify(BaseModel):
    correo: EmailStr
    codigo: str


class TwoFactorResponse(BaseModel):
    mensaje: str
    codigo: str = None  # Solo presente en debug mode
