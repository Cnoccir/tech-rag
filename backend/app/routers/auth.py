# app/routers/auth.py
from typing import Annotated, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session  # Added this import
from uuid import uuid4

from backend.app.auth.auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    authenticate_user,
    verify_token
)
from backend.app.config import get_settings
from backend.app.database.database import get_db
from backend.app.database.models import User
from backend.app.schemas import Token, UserCreate, User as UserSchema

router = APIRouter(prefix="/auth", tags=["authentication"])
settings = get_settings()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Session = Depends(get_db)
) -> User:
    """Dependency to get current authenticated user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = verify_token(token, credentials_exception)
    user = db.query(User).filter(User.username == payload.get("sub")).first()
    if user is None:
        raise credentials_exception
    return user

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Login endpoint that returns a JWT token"""
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserSchema)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current authenticated user information"""
    return UserSchema.from_orm(current_user)

@router.post("/register", response_model=UserSchema)
async def register(
    username: str = Body(...),
    password: str = Body(...),
    is_admin: bool = Body(False),
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Register a new user. Only admin users can create other admin users."""
    # Check admin privileges for admin user creation
    if is_admin and (not current_user or not current_user.is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can create other admin users"
        )

    # Check username uniqueness
    if db.query(User).filter(User.username == username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    # Create new user
    user = User(
        id=str(uuid4()),
        username=username,
        password=get_password_hash(password),
        is_admin=is_admin
    )
    db.add(user)
    try:
        db.commit()
        db.refresh(user)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating user: {str(e)}"
        )

    return UserSchema.from_orm(user)
