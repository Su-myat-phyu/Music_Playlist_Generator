from datetime import timedelta
from typing import Dict, Any, List
import hmac
import os

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.services.auth import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES, get_current_admin
from app.services.db import PlaylistDB


router = APIRouter(prefix="/admin", tags=["admin"])
db = PlaylistDB("mongodb://localhost:27017", "music_playlists")

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")


class AdminLoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=128)
    password: str = Field(min_length=1, max_length=256)


class AdminLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int


@router.post("/login", response_model=AdminLoginResponse)
async def admin_login(payload: AdminLoginRequest):
    if ADMIN_PASSWORD == "other_password":
        raise HTTPException(
            status_code=500,
            detail="Admin credentials are not configured. Set ADMIN_USERNAME and ADMIN_PASSWORD.",
        )

    username_ok = hmac.compare_digest(payload.username, ADMIN_USERNAME)
    password_ok = hmac.compare_digest(payload.password, ADMIN_PASSWORD)
    if not username_ok or not password_ok:
        raise HTTPException(status_code=401, detail="Invalid admin username or password")

    token = create_access_token(
        data={"sub": "admin_local", "role": "admin", "username": ADMIN_USERNAME},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    db.record_activity("admin_local", "admin_login", {"username": ADMIN_USERNAME})
    return AdminLoginResponse(access_token=token, expires_in_minutes=ACCESS_TOKEN_EXPIRE_MINUTES)


@router.get("/dashboard")
async def get_admin_dashboard(_: Dict[str, Any] = Depends(get_current_admin)):
    stats = db.get_dashboard_stats()
    total_users = stats.get("total_users", 0)
    total_playlists = stats.get("total_playlists", 0)
    recent_active_users = stats.get("recent_active_users", 0)
    engagement_rate = round((recent_active_users / total_users) * 100, 2) if total_users else 0.0
    avg_playlists_per_user = round((total_playlists / total_users), 2) if total_users else 0.0

    return {
        "summary": {
            "total_users": total_users,
            "recent_active_users_30d": recent_active_users,
            "engagement_rate_percent": engagement_rate,
            "playlist_generation_count": total_playlists,
            "avg_playlists_per_user": avg_playlists_per_user,
        },
        "popular_moods": stats.get("top_moods", []),
        "popular_genres": stats.get("top_genres", []),
        "top_artists": stats.get("top_artists", []),
        "user_activity": stats.get("user_activity", {}),
        "ml_metrics": stats.get("ml_metrics", {}),
    }


@router.get("/users")
async def list_registered_users(_: Dict[str, Any] = Depends(get_current_admin)):
    users = db.get_all_users(active_only=False)
    output: List[Dict[str, Any]] = []
    for user in users:
        # Exclude admin accounts from the registered users list
        role = str(user.get("role", "user")).lower()
        email = str(user.get("email", "")).lower()
        if role == "admin" or email == "admin@playlistgen.com":
            continue

        output.append(
            {
                "id": str(user.get("_id")),
                "name": user.get("name", ""),
                "email": user.get("email", ""),
                "role": user.get("role", "user"),
                "is_active": user.get("is_active", True),
                "playlists_count": user.get("playlists_count", 0),
                "last_activity": user.get("last_activity"),
                "created_at": user.get("created_at"),
            }
        )
    return {"users": output}


@router.patch("/users/{user_id}/deactivate")
async def deactivate_registered_user(user_id: str, _: Dict[str, Any] = Depends(get_current_admin)):
    success = db.deactivate_user(user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found or already inactive")
    db.record_activity("admin_local", "user_deactivated", {"target_user_id": user_id})
    return {"message": "User deactivated successfully", "user_id": user_id}

@router.patch("/users/{user_id}/activate")
async def activate_registered_user(user_id: str, _: Dict[str, Any] = Depends(get_current_admin)):
    success = db.activate_user(user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found or already active")
    db.record_activity("admin_local", "user_activated", {"target_user_id": user_id})
    return {"message": "User activated successfully", "user_id": user_id}
