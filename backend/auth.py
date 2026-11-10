import os
from datetime import datetime, timedelta
from typing import Optional, List
import jwt
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import User, Tenant, UserRole

SECRET_KEY = os.getenv("JWT_SECRET", "super-secret-plascencia-aluminio-vidrio-key-2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 horas

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token", auto_error=False)

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: Optional[str] = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> Optional[User]:
    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            return None
    except Exception:
        return None

    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    return user

def require_authenticated_user(current_user: Optional[User] = Depends(get_current_user)) -> User:
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autenticación requerida. Token no proporcionado o inválido.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user

def require_roles(allowed_roles: List[str]):
    """
    Control de Acceso Basado en Roles (RBAC):
    - Administrador: Configuración global de costos, tarifas de instalación y reportes.
    - Vendedor: Cotizaciones rápidas, proyectos y despieces para clientes.
    - Operario: Planos técnicos y hojas de corte exclusivamente.
    """
    def role_checker(current_user: User = Depends(require_authenticated_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permiso denegado. El rol '{current_user.role}' no tiene acceso a este recurso. Roles permitidos: {', '.join(allowed_roles)}"
            )
        return current_user
    return role_checker
