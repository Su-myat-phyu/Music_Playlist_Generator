from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import RedirectResponse, JSONResponse
import google.auth.transport.requests
# import google.oauth2.google_auth  # Removed unused
from google.auth.transport.requests import Request
from google.oauth2 import id_token
from urllib.parse import urlencode, parse_qs
from app.models.user import UserCreate, UserResponse, UserDB
from app.services.db import PlaylistDB
from app.services.auth import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from typing import Optional
from datetime import timedelta, datetime
from dotenv import load_dotenv
import os
import httpx

load_dotenv()

router = APIRouter(prefix="/auth/google", tags=["auth"])

db = PlaylistDB('mongodb://localhost:27017', 'music_playlists')
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = "http://127.0.0.1:8000/auth/google/callback"
FRONTEND_URL = "http://localhost:3000"
SCOPE = "https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/userinfo.profile openid"

@router.get("/login")
async def google_login():
    """Redirect to Google login"""
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(500, "Google Client ID not configured")
    
    google_login_url = (
        "https://accounts.google.com/o/oauth2/auth?"
        f"client_id={GOOGLE_CLIENT_ID}&"
        f"redirect_uri={REDIRECT_URI}&"
        f"scope={SCOPE}&"
        f"response_type=code&"
        "access_type=offline"
    )
    return {"login_url": google_login_url}

@router.get("/callback")
async def google_callback(code: str):
    """Handle Google callback, exchange code for user info and JWT"""
    if not code:
        raise HTTPException(400, "No code provided")
    
    try:
        # Exchange code for tokens
        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": REDIRECT_URI,
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(token_url, data=token_data)
            token_info = response.json()
        
        if "access_token" not in token_info:
            raise HTTPException(400, "Failed to get Google access token")
        
        # Get user info
        userinfo_url = "https://www.googleapis.com/oauth2/v3/userinfo"
        headers = {"Authorization": f"Bearer {token_info['access_token']}"}
        
        async with httpx.AsyncClient() as client:
            user_response = await client.get(userinfo_url, headers=headers)
            user_data = user_response.json()
        
        google_id = user_data["sub"]
        email = user_data["email"]
        name = user_data["name"]
        
        # Check if user exists
        users = db.get_users()
        user = next((u for u in users if u.get("google_id") == google_id), None)
        
        if user:
            # Update existing user
            db.update_user(
                str(user["_id"]),
                {
                    "name": name,
                    "email": email,
                    "last_activity": datetime.utcnow(),
                },
            )
            user_id = str(user["_id"])
        else:
            # Create new user
            new_user = {
                "name": name,
                "email": email,
                "google_id": google_id,
                "role": "user",
                "is_active": True,
                "playlists": [],
                "playlists_count": 0,
                "last_activity": datetime.utcnow(),
                "total_accuracy": 0.0,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            saved_user = db.save_user(new_user)
            user_id = str(saved_user["_id"])
        
        if not user_id:
            raise HTTPException(500, "Failed to save user")

        db.record_activity(user_id, "login", {"provider": "google_oauth"})
        
        # Create JWT
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user_id}, expires_delta=access_token_expires
        )
        
        # Fetch full user for response
        users = db.get_users()
        current_user = next((u for u in users if str(u["_id"]) == user_id), None)
        
        return JSONResponse(content={
            "access_token": access_token,
            "token_type": "bearer",
            "user": UserResponse(**current_user) if current_user else None
        })
    
    except Exception as e:
        raise HTTPException(500, f"Auth error: {str(e)}")

