from datetime import datetime, timedelta
from typing import Annotated, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from app.auth.auth import get_password_hash, verify_password, create_access_token, authenticate_user as auth_authenticate_user
from app.config import get_settings
from app.database.database import get_db
from app.database.models import User
from app.schemas import Token, UserCreate, User as UserSchema
from uuid import uuid4

router = APIRouter(prefix="/auth", tags=["authentication"])
settings = get_settings()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: Any = Depends(get_db)) -> Any:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Any = Depends(get_db)):
    """Login endpoint that returns a JWT token."""
    user = auth_authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register", response_model=UserSchema)
def register(
    username: str = Body(...),
    password: str = Body(...),
    is_admin: bool = Body(False),
    current_user: Optional[User] = Depends(get_current_user),
    db: Any = Depends(get_db)
):
    """Register a new user. Only admin users can create other admin users."""
    # Check if the user is trying to create an admin user
    if is_admin and (not current_user or not current_user.is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can create other admin users"
        )
    
    # Check if username already exists
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
    db.commit()
    db.refresh(user)
    
    return UserSchema.from_orm(user)
