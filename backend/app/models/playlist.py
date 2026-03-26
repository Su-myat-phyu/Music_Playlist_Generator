from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, model_validator


class PlaylistPreferences(BaseModel):
    genre: Optional[str] = None
    mood: Optional[str] = None
    artist: Optional[str] = None


class PlaylistCreate(BaseModel):
    name: str
    songs: List[Dict[str, Any]] = Field(default_factory=list)
    preferences: PlaylistPreferences = Field(default_factory=PlaylistPreferences)


class PlaylistResponse(BaseModel):
    id: str
    name: str
    songs: List[Dict[str, Any]]
    preferences: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


class SaveSongRequest(BaseModel):
    song: Dict[str, Any]
    playlist_id: Optional[str] = None
    playlist_name: Optional[str] = None
    preferences: Optional[PlaylistPreferences] = None

    @model_validator(mode='before')
    @classmethod
    def validate_playlist_target(cls, v):
        if isinstance(v, dict):
            playlist_id = v.get("playlist_id")
            playlist_name = v.get("playlist_name")

            if not playlist_id and not playlist_name:
                raise ValueError("Either playlist_id or playlist_name is required")

            if playlist_id and playlist_name:
                raise ValueError("Provide either playlist_id or playlist_name, not both")

        return v

