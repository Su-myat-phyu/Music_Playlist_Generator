from datetime import datetime
from typing import Any, Dict, List, Optional

from bson import ObjectId
from pymongo import MongoClient


class PlaylistDB:
    def __init__(self, mongo_uri: str, db_name: str):
        # Fail fast when Mongo is unavailable so API endpoints don't hang for ~30s.
        self.client = MongoClient(
            mongo_uri,
            serverSelectionTimeoutMS=3000,
            connectTimeoutMS=3000,
            socketTimeoutMS=5000,
        )
        self.db = self.client[db_name]
        self.playlists = self.db["playlists"]
        self.users = self.db["users"]
        self.activity_logs = self.db["activity_logs"]

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
        self.record_activity(
            user_id,
            "playlist_created",
            {
                "playlist_id": str(result.inserted_id),
                "songs_count": len(document.get("songs", [])),
            },
        )
        return document

    def get_playlists(self, user_id: str) -> List[Dict[str, Any]]:
        return list(self.playlists.find({"user_id": user_id}).sort("created_at", -1))

    def delete_playlist(self, user_id: str, playlist_id: str) -> bool:
        result = self.playlists.delete_one(
            {"_id": ObjectId(playlist_id), "user_id": user_id}
        )
        if result.deleted_count > 0:
            self.record_activity(user_id, "playlist_deleted", {"playlist_id": playlist_id})
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
        self.record_activity(
            user_id,
            "song_saved_to_playlist",
            {"playlist_id": str(playlist["_id"]), "song_title": song.get("title")},
        )
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

    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        try:
            from bson import ObjectId
            return self.users.find_one({"_id": ObjectId(user_id)})
        except:
            # For Google users with string IDs, search by user_id directly
            return self.users.find_one({"_id": user_id})

    def update_user(self, user_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            from bson import ObjectId
            user = self.users.find_one({"_id": ObjectId(user_id)})
            if not user:
                return None

            updated_at = datetime.utcnow()
            self.users.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {**update_data, "updated_at": updated_at}},
            )
            if user:
                user.update(update_data)
                user["updated_at"] = updated_at
            return user
        except:
            # For Google users with string IDs
            user = self.users.find_one({"_id": user_id})
            if not user:
                return None

            updated_at = datetime.utcnow()
            self.users.update_one(
                {"_id": user_id},
                {"$set": {**update_data, "updated_at": updated_at}},
            )
            if user:
                user.update(update_data)
                user["updated_at"] = updated_at
            return user

    def deactivate_user(self, user_id: str) -> bool:
        """Deactivate a user (set is_active=False)"""
        try:
            from bson import ObjectId
            query = {"_id": ObjectId(user_id)}
        except:
            query = {"_id": user_id}

        result = self.users.update_one(
            query,
            {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
        )
        return result.modified_count > 0

    def get_all_users(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """Get all users, optionally filter active only"""
        query = {} if not active_only else {"is_active": True}
        return list(self.users.find(query).sort("created_at", -1))

    def record_activity(self, user_id: str, action: str, metadata: Optional[Dict[str, Any]] = None):
        now = datetime.utcnow()
        self.activity_logs.insert_one(
            {
                "user_id": user_id,
                "action": action,
                "metadata": metadata or {},
                "created_at": now,
            }
        )
        self.update_user(user_id, {"last_activity": now})

    def get_user_activity_metrics(self, days: int = 30) -> Dict[str, Any]:
        from datetime import timedelta

        since = datetime.utcnow() - timedelta(days=days)
        base_match = {"created_at": {"$gte": since}}

        actions_pipeline = [
            {"$match": base_match},
            {"$group": {"_id": "$action", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
        ]
        actions = list(self.activity_logs.aggregate(actions_pipeline))

        login_pipeline = [
            {"$match": {"created_at": {"$gte": since}, "action": {"$in": ["login", "admin_login"]}}},
            {
                "$group": {
                    "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}},
                    "count": {"$sum": 1},
                }
            },
            {"$sort": {"_id": 1}},
        ]
        logins = list(self.activity_logs.aggregate(login_pipeline))

        top_users_pipeline = [
            {"$match": base_match},
            {"$group": {"_id": "$user_id", "actions_count": {"$sum": 1}}},
            {"$sort": {"actions_count": -1}},
            {"$limit": 10},
        ]
        top_users_raw = list(self.activity_logs.aggregate(top_users_pipeline))

        top_users = []
        for row in top_users_raw:
            user_doc = self.get_user(row["_id"])
            if not user_doc:
                continue
            top_users.append(
                {
                    "user_id": row["_id"],
                    "name": user_doc.get("name", "Unknown"),
                    "email": user_doc.get("email", "unknown@email"),
                    "actions_count": row["actions_count"],
                }
            )

        return {
            "actions_breakdown": [{"action": x["_id"], "count": x["count"]} for x in actions],
            "login_frequency": [{"date": x["_id"], "count": x["count"]} for x in logins],
            "top_active_users": top_users,
        }

    def get_ml_metrics(self) -> Dict[str, Any]:
        # Uses recommendation_score values saved for songs in generated playlists.
        pipeline = [
            {"$unwind": "$songs"},
            {"$match": {"songs.recommendation_score": {"$exists": True, "$ne": None}}},
            {
                "$group": {
                    "_id": None,
                    "avg_score": {"$avg": "$songs.recommendation_score"},
                    "max_score": {"$max": "$songs.recommendation_score"},
                    "min_score": {"$min": "$songs.recommendation_score"},
                    "total_samples": {"$sum": 1},
                    "high_confidence": {
                        "$sum": {"$cond": [{"$gte": ["$songs.recommendation_score", 0.7]}, 1, 0]}
                    },
                }
            },
        ]
        summary = list(self.playlists.aggregate(pipeline))
        if not summary:
            return {
                "accuracy": 0.0,
                "precision": None,
                "recall": None,
                "f1_score": None,
                "evaluated_samples": 0,
                "note": "No recommendation_score data available yet.",
            }

        aggregate = summary[0]
        total_samples = aggregate["total_samples"] or 1
        accuracy = round(float(aggregate["avg_score"]), 4)
        precision_proxy = round(float(aggregate["high_confidence"]) / float(total_samples), 4)

        return {
            "accuracy": accuracy,
            "precision": None,
            "recall": None,
            "f1_score": None,
            "precision_proxy": precision_proxy,
            "evaluated_samples": aggregate["total_samples"],
            "score_range": {
                "min": round(float(aggregate["min_score"]), 4),
                "max": round(float(aggregate["max_score"]), 4),
            },
            "note": (
                "Precision/recall require labeled ground truth. "
                "Proxy precision is ratio of recommendation_score >= 0.7."
            ),
        }

    def get_dashboard_stats(self) -> Dict[str, Any]:
        """Get admin dashboard stats with usage and ML monitoring data."""
        # Total users and playlists
        total_users = self.users.count_documents({})
        total_playlists = self.playlists.count_documents({})

        # Popular moods/genres (top 5)
        mood_pipeline = [
            {"$match": {"preferences.mood": {"$ne": None}}},
            {"$group": {"_id": "$preferences.mood", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 5}
        ]
        moods = list(self.playlists.aggregate(mood_pipeline))

        genre_pipeline = [
            {"$match": {"preferences.genre": {"$ne": None}}},
            {"$group": {"_id": "$preferences.genre", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 5}
        ]
        genres = list(self.playlists.aggregate(genre_pipeline))

        # Avg ML accuracy across all playlists (uses recommendation_score)
        accuracy_pipeline = [
            {"$unwind": "$songs"},
            {"$match": {"songs.recommendation_score": {"$exists": True, "$ne": None}}},
            {"$group": {"_id": None, "avg_accuracy": {"$avg": "$songs.recommendation_score"}}}
        ]
        accuracy_result = list(self.playlists.aggregate(accuracy_pipeline))
        avg_accuracy = accuracy_result[0]["avg_accuracy"] if accuracy_result else 0.0

        # Recent activity (users active last 30 days)
        from datetime import timedelta
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_users = self.users.count_documents({"last_activity": {"$gte": thirty_days_ago}})
        activity_metrics = self.get_user_activity_metrics(days=30)
        ml_metrics = self.get_ml_metrics()

        return {
            "total_users": total_users,
            "total_playlists": total_playlists,
            "recent_active_users": recent_users,
            "avg_accuracy": round(avg_accuracy, 4),
            "top_moods": [{"name": m["_id"], "count": m["count"]} for m in moods],
            "top_genres": [{"name": g["_id"], "count": g["count"]} for g in genres],
            "user_activity": activity_metrics,
            "ml_metrics": ml_metrics,
        }

    def update_user_stats(self, user_id: str, new_playlist_id: str, song_scores: List[float]):
        """Update user stats after new playlist: playlists_count++, total_accuracy avg, last_activity"""
        try:
            from bson import ObjectId
            now = datetime.utcnow()
            avg_new_accuracy = sum(song_scores) / len(song_scores) if song_scores else 0.0

            # Update playlists list and stats
            self.users.update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$push": {"playlists": new_playlist_id},
                    "$inc": {"playlists_count": 1},
                    "$set": {
                        "last_activity": now,
                        "total_accuracy": avg_new_accuracy  # Simple avg; could be weighted later
                    }
                }
            )
            self.record_activity(
                user_id,
                "playlist_saved",
                {"playlist_id": new_playlist_id, "songs_count": len(song_scores)},
            )
        except:
            # Fallback for Google string IDs
            now = datetime.utcnow()
            avg_new_accuracy = sum(song_scores) / len(song_scores) if song_scores else 0.0
            self.users.update_one(
                {"_id": user_id},
                {
                    "$push": {"playlists": new_playlist_id},
                    "$inc": {"playlists_count": 1},
                    "$set": {
                        "last_activity": now,
                        "total_accuracy": avg_new_accuracy
                    }
                }
            )
            self.record_activity(
                user_id,
                "playlist_saved",
                {"playlist_id": new_playlist_id, "songs_count": len(song_scores)},
            )
