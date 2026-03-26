from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any
from bson import ObjectId
from ..models.playlist import PlaylistCreate, PlaylistResponse, SaveSongRequest
from ..models.user import UserResponse
from ..services.db import PlaylistDB
from ..services.auth import get_current_user
from datetime import datetime

router = APIRouter(prefix="/playlists", tags=["playlists"])

db = PlaylistDB('mongodb://localhost:27017', 'music_playlists')

def serialize_playlist(playlist: Dict) -> Dict:
    """Convert MongoDB playlist document into API response shape"""
    serialized = dict(playlist)
    if "_id" in serialized:
        serialized["id"] = str(serialized.pop("_id"))
    return serialized

@router.post("/", response_model=PlaylistResponse)
async def create_playlist(playlist_data: PlaylistCreate, current_user: Dict = Depends(get_current_user)):
    """Save a new playlist"""
    try:
        # Add metadata
        data = playlist_data.dict()
        data["created_at"] = datetime.utcnow()
        data["updated_at"] = datetime.utcnow()

        data["user_id"] = current_user["user_id"]
        
        result = db.save_playlist(current_user["user_id"], data)
        saved_playlists = db.get_playlists(current_user["user_id"])
        saved_playlist = next(p for p in saved_playlists if str(p["_id"]) == str(result["_id"]))
        return PlaylistResponse(**serialize_playlist(saved_playlist))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@router.get("/", response_model=List[PlaylistResponse])
async def list_playlists(current_user: Dict = Depends(get_current_user)):
    """List user's playlists"""
    try:
        playlists = db.get_playlists(current_user["user_id"])
        return [PlaylistResponse(**serialize_playlist(p)) for p in playlists]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/save-song", response_model=PlaylistResponse)
async def save_song(request: SaveSongRequest, current_user: Dict = Depends(get_current_user)):
    """Save song to existing or new playlist"""
    try:
        if request.playlist_id:
            # Add to existing playlist
            updated_playlist = db.append_song_to_playlist(current_user["user_id"], request.playlist_id, request.song)
            if not updated_playlist:
                raise HTTPException(status_code=404, detail="Playlist not found")
            return PlaylistResponse(**serialize_playlist(updated_playlist))
        elif request.playlist_name:
            # Create new playlist with this song
            playlist_data = {
                "name": request.playlist_name,
                "songs": [request.song],
                "preferences": request.preferences.dict(exclude_unset=True) if request.preferences else {}
            }
            now = datetime.utcnow()
            playlist_data["created_at"] = now
            playlist_data["updated_at"] = now
            saved = db.save_playlist(current_user["user_id"], playlist_data)
            saved_playlists = db.get_playlists(current_user["user_id"])
            saved_playlist = next(p for p in saved_playlists if str(p["_id"]) == str(saved["_id"]))
            return PlaylistResponse(**serialize_playlist(saved_playlist))
        else:
            raise HTTPException(status_code=400, detail="Either playlist_id or playlist_name required")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{playlist_id}/songs")
async def add_song_to_playlist(
    playlist_id: str,
    song: Dict[str, Any],
    current_user: Dict = Depends(get_current_user)
):
    """Add a single song to existing playlist"""
    try:
        updated_playlist = db.append_song_to_playlist(current_user["user_id"], playlist_id, song)
        if not updated_playlist:
            raise HTTPException(status_code=404, detail="Playlist not found")
        return PlaylistResponse(**serialize_playlist(updated_playlist))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{playlist_id}")
async def get_playlist(playlist_id: str, current_user: Dict = Depends(get_current_user)):
    """Get single playlist with all songs"""
    try:
        playlist = db.playlists.find_one({
            "_id": ObjectId(playlist_id),
            "user_id": current_user["user_id"]
        })
        if not playlist:
            raise HTTPException(status_code=404, detail="Playlist not found")
        return PlaylistResponse(**serialize_playlist(playlist))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{playlist_id}")
async def delete_playlist(playlist_id: str, current_user: Dict = Depends(get_current_user)):
    """Delete a playlist"""
    try:
        success = db.delete_playlist(current_user["user_id"], playlist_id)
        if not success:
            raise HTTPException(status_code=404, detail="Playlist not found")
        return {"message": "Playlist deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

