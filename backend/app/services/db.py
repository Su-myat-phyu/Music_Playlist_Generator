from datetime import datetime
from typing import Any, Dict, List, Optional

from bson import ObjectId
from pymongo import MongoClient


class PlaylistDB:
    def __init__(self, mongo_uri: str, db_name: str):
        self.client = MongoClient(mongo_uri)
        self.db = self.client[db_name]
        self.playlists = self.db["playlists"]
        self.users = self.db["users"]

    def save_playlist(self, user_id: str, playlist_data: Dict[str, Any]) -> Dict[str, Any]:
        now = datetime.utcnow()
        document = {
            "user_id": user_id,
            "name": playlist_data["name"],
            "songs": playlist_data.get("songs", []),
            "preferences": playlist_data.get("preferences", {}),
            "created_at": now,
            "updated_at": now,
        }
        result = self.playlists.insert_one(document)
        document["_id"] = result.inserted_id
        return document

    def get_playlists(self, user_id: str) -> List[Dict[str, Any]]:
        return list(self.playlists.find({"user_id": user_id}).sort("created_at", -1))

    def delete_playlist(self, user_id: str, playlist_id: str) -> bool:
        result = self.playlists.delete_one(
            {"_id": ObjectId(playlist_id), "user_id": user_id}
        )
        return result.deleted_count > 0

    def get_playlist(self, user_id: str, playlist_id: str) -> Optional[Dict[str, Any]]:
        return self.playlists.find_one(
            {"_id": ObjectId(playlist_id), "user_id": user_id}
        )

    def append_song_to_playlist(
        self, user_id: str, playlist_id: str, song: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        playlist = self.get_playlist(user_id, playlist_id)
        if not playlist:
            return None

        existing_songs = playlist.get("songs", [])
        song_id = song.get("id")
        song_title = song.get("title")

        duplicate_exists = any(
            existing_song.get("id") == song_id and existing_song.get("title") == song_title
            for existing_song in existing_songs
        )

        if duplicate_exists:
            return playlist

        updated_songs = existing_songs + [song]
        updated_at = datetime.utcnow()

        self.playlists.update_one(
            {"_id": playlist["_id"], "user_id": user_id},
            {"$set": {"songs": updated_songs, "updated_at": updated_at}},
        )

        playlist["songs"] = updated_songs
        playlist["updated_at"] = updated_at
        return playlist

    def save_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        existing_user = self.users.find_one({"email": user_data["email"]})
        now = datetime.utcnow()

        if existing_user:
            self.users.update_one(
                {"_id": existing_user["_id"]},
                {"$set": {**user_data, "updated_at": now}},
            )
            existing_user.update(user_data)
            existing_user["updated_at"] = now
            return existing_user

        document = {**user_data, "created_at": now, "updated_at": now}
        result = self.users.insert_one(document)
        document["_id"] = result.inserted_id
        return document

    def get_users(self) -> List[Dict[str, Any]]:
        return list(self.users.find().sort("created_at", -1))

    def get_user(self, email: str) -> Optional[Dict[str, Any]]:
        return self.users.find_one({"email": email})

    def update_user(self, email: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        user = self.get_user(email)
        if not user:
            return None

        updated_at = datetime.utcnow()
        self.users.update_one(
            {"_id": user["_id"]},
            {"$set": {**update_data, "updated_at": updated_at}},
        )
        user.update(update_data)
        user["updated_at"] = updated_at
        return user