from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    google_id: str

class UserDB(BaseModel):
    id: str
    name: str
    email: EmailStr
    google_id: Optional[str] = None
    role: str = "user"  # "user" or "admin"
    is_active: bool = True
    playlists: List[str] = []  # List of playlist ObjectIds as strings
    playlists_count: int = 0
    last_activity: datetime
    total_accuracy: float = 0.0
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True  # For ORM/Pydantic v2 compatibility

class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    role: str
    is_active: bool
    playlists_count: int = 0
    last_activity: datetime
    total_accuracy: float = 0.0
    created_at: datetime

    class Config:
        from_attributes = True

