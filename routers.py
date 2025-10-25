from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from create_tables import get_db
from pydantic import BaseModel
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
import os

secret = 'e73ef6dda2ce3b52e1f0cdf7b6761076024f064c5a80f6c9551ebd2fd9eca3f7'
SECRET_KEY = os.getenv("SECRET_KEY", secret )
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 4

pwd_context = CryptContext(
    schemes=["bcrypt_sha256", "bcrypt"],
    default="bcrypt_sha256",
    deprecated="auto",
)


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

router = APIRouter(prefix="/api/auth", tags=["authentication"])


class UserRegister(BaseModel):
    username: str
    mail: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hashuje hasło"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Tworzy JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def authenticate_user(db: Session, username: str, password: str):
    """Autentykuje użytkownika"""
    from models import User
    
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return False
    if not verify_password(password, user.pass_):
        return False
    return user

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Pobiera aktualnego użytkownika z tokenu JWT"""
    from models import User
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.username == token_data.username).first()
    if user is None:
        raise credentials_exception
    return user

# Endpointy
@router.post("/register", response_model=dict)
async def register_user(user_data: UserRegister, db: Session = Depends(get_db)):
    """Rejestracja nowego użytkownika"""
    from models import User
    
    # Sprawdź czy użytkownik już istnieje
    existing_user = db.query(User).filter(
        (User.username == user_data.username) | (User.mail == user_data.mail)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Użytkownik z tym username lub emailem już istnieje"
        )
    
    # Hashuj hasło
    hashed_password = get_password_hash(user_data.password)
    
    # Utwórz nowego użytkownika
    new_user = User(
        username=user_data.username,
        mail=user_data.mail,
        pass_=hashed_password,
        total_spent=0.0
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {
        "message": "Użytkownik został pomyślnie zarejestrowany",
        "user_id": new_user.id,
        "username": new_user.username
    }

@router.post("/login", response_model=Token)
async def login_user(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nieprawidłowy username lub hasło",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.get("/me")
async def read_users_me(current_user = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "mail": current_user.mail,
        "total_spent": current_user.total_spent
    }
