"""
app/api/v1/endpoints/auth.py
Authentication endpoints for ZeroWaste Grocer staff.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.models import User
from app.schemas.api_schemas import LoginRequest, LoginResponse, UserResponse
from app.core.security import create_access_token, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="Staff authentication"
)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    if not request.email or not request.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email and password are required"
        )

    email_clean = request.email.strip()
    user = (
        db.query(User)
        .filter((User.email == email_clean) | (User.username == email_clean))
        .first()
    )

    if user:
        if not verify_password(request.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )
        user_id = str(user.id)
        name = user.full_name
        role = user.role
        store_id = user.store_id
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    token_payload = {
        "sub": user_id,
        "id": user_id,
        "name": name,
        "role": role,
        "email": email_clean,
        "store_id": store_id
    }
    token = create_access_token(data=token_payload)

    return LoginResponse(
        token=token,
        user=UserResponse(
            id=user_id,
            name=name,
            role=role,
            store_id=store_id
        )
    )
