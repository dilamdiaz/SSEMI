# Backend/app/auth/utils.py

from passlib.context import CryptContext

# Configuración del contexto de encriptación
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """
    Hashea una contraseña usando bcrypt, asegurando compatibilidad con el límite de 72 bytes.
    """
    if not isinstance(password, str):
        raise ValueError(f"❌ Se esperaba un string, pero se recibió: {type(password)}")

    # Limpieza básica
    password = password.strip()

    # Recorte seguro basado en bytes (no solo caracteres)
    password = password.encode("utf-8")[:72].decode("utf-8", errors="ignore")

    # (Opcional) logs para depuración — puedes quitarlos en producción
    print("👉 Password recibido:", repr(password))
    print("📏 Longitud en bytes:", len(password.encode('utf-8')))

    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica una contraseña plana contra un hash almacenado.
    """
    if not isinstance(plain_password, str):
        raise ValueError(f"❌ Se esperaba un string, pero se recibió: {type(plain_password)}")

    # Recorte seguro basado en bytes
    plain_password = plain_password.encode("utf-8")[:72].decode("utf-8", errors="ignore")

    return pwd_context.verify(plain_password, hashed_password)
