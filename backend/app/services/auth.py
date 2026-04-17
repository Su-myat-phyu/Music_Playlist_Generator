from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from dotenv import load_dotenv
from google.auth.transport import requests
from google.oauth2 import id_token
import os
from app.services.db import PlaylistDB

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "your-super-secret-key-change-in-production")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 * 24 * 60  # 30 days

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")
db = PlaylistDB("mongodb://localhost:27017", "music_playlists")

def normalize_bcrypt_secret(secret: str) -> str:
    """bcrypt only accepts first 72 bytes; enforce safely for unicode input."""
    if secret is None:
        return ""
    return secret.encode("utf-8")[:72].decode("utf-8", errors="ignore")

def verify_password(plain_password, hashed_password):
    """Not used for Google auth, but included for completeness"""
    return pwd_context.verify(normalize_bcrypt_secret(plain_password), hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if "role" not in to_encode:
        to_encode["role"] = "user"
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # First try Google ID token validation (frontend sends this directly)
        if GOOGLE_CLIENT_ID:
            google_payload = id_token.verify_oauth2_token(token, requests.Request(), GOOGLE_CLIENT_ID)
            google_user_id = google_payload.get("sub")
            if google_user_id:
                return {"user_id": f"google_{google_user_id}", "role": "user"}

        # Fallback to JWT
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        role: str = payload.get("role", "user")
        if user_id is None:
            raise credentials_exception

        user_doc = db.get_user(user_id)
        if user_doc and not user_doc.get("is_active", True):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive",
            )

        return {"user_id": user_id, "role": role}
    except (JWTError, ValueError):
        raise credentials_exception

def decode_token(token: str):
    """Utility to decode token without dependency"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

