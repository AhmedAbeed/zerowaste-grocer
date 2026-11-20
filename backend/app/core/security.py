"""
app/core/security.py
JWT token creation, validation, and authentication dependencies for ZeroWaste Grocer.
"""
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Set
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.hash import pbkdf2_sha256

SECRET_KEY = os.getenv("SECRET_KEY", "zerowaste-secret-key-change-in-production-2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

ROLE_ALIASES = {
    "clerk": "clerk",
    "inventoryclerk": "clerk",
    "auditor": "auditor",
    "inventoryauditor": "auditor",
    "manager": "manager",
    "storemanager": "manager",
    "admin": "admin",
    "systemadmin": "admin",
    "enterpriseadmin": "admin",
}

def normalize_role(role: str) -> str:
    cleaned = str(role or '').strip().lower().replace('_', '').replace(' ', '')
    return ROLE_ALIASES.get(cleaned, cleaned)

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    auto_error=False
)

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Dict[str, Any]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_current_user(token: Optional[str] = Depends(oauth2_scheme)) -> Dict[str, Any]:
    """
    FastAPI dependency for user authentication.
    Validates and decodes the JWT Bearer token.
    Raises HTTP 401 if missing, invalid, or expired.
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return verify_token(token)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return pbkdf2_sha256.verify(plain_password, hashed_password)
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    return pbkdf2_sha256.hash(password)

def require_roles(*allowed_roles: str):
    """
    FastAPI dependency factory enforcing role-based access control.
    Supports canonical roles ('clerk', 'auditor', 'manager', 'admin')
    as well as backward-compatible aliases ('storeManager', etc.).
    """
    canonical_allowed = {normalize_role(r) for r in allowed_roles}

    def role_checker(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        raw_role = current_user.get("role_id") or current_user.get("role", "")
        user_role = normalize_role(str(raw_role))
        if user_role not in canonical_allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operation not permitted for current role"
            )
        return current_user

    return role_checker

def get_user_branch_id(current_user: Dict[str, Any]) -> Optional[int]:
    """
    Extracts the branch_id from JWT claims.
    Returns None for Enterprise Admin (who has global branch oversight).
    """
    raw_role = current_user.get("role_id") or current_user.get("role", "")
    if normalize_role(str(raw_role)) == "admin":
        return None
    val = current_user.get("branch_id")
    if val is None:
        val = current_user.get("store_id")
    if val is not None:
        try:
            return int(val)
        except (ValueError, TypeError):
            pass
    return None

def verify_branch_access(
    current_user: Dict[str, Any],
    requested_store_id: Optional[int] = None,
    require_for_admin: bool = False
) -> int:
    """
    Enforces strict branch isolation:
    - For clerk, auditor, and manager: branch_id MUST come from the JWT.
      If a requested_store_id is passed and differs from their JWT branch_id, raises HTTP 403.
      Returns the user's JWT branch_id.
    - For admin (branch_id = None): global access is allowed. Returns requested_store_id.
      If require_for_admin is True and requested_store_id is None, raises HTTP 400.
      Otherwise falls back to 1.
    """
    raw_role = current_user.get("role_id") or current_user.get("role", "")
    is_admin = (normalize_role(str(raw_role)) == "admin")

    if is_admin:
        if requested_store_id is None:
            if require_for_admin:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Explicit store_id query parameter is required for admin user."
                )
            return 1
        return requested_store_id

    branch_id = get_user_branch_id(current_user)
    if branch_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User has no branch assignment."
        )

    if requested_store_id is not None and requested_store_id != branch_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied: User is assigned to branch {branch_id}, cannot access branch {requested_store_id}."
        )

    return branch_id
