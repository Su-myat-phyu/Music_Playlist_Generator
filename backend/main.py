from fastapi import FastAPI, Query, Depends
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from app.models.playlist import PlaylistCreate
from app.routers.playlists import router as playlists_router
from app.routers.auth import router as auth_router
from app.routers.admin import router as admin_router

from app.services.db import PlaylistDB
from app.services.auth import get_current_user
from app.services.recommendation import recommendation_engine, GENRE_MAP, MOOD_GENRE_MAP
import requests
import random

load_dotenv()
app = FastAPI()
db = PlaylistDB('mongodb://localhost:27017', 'music_playlists')

# Add CORS middleware to allow frontend to call API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# iTunes API base URL
ITUNES_SEARCH_URL = "https://itunes.apple.com/search"

# Mappings moved to recommendation.py

# Genre descriptions for better search
GENRE_DESCRIPTIONS = {
    "rock": "rock music",
    "pop": "pop music",
    "jazz": "jazz music",
    "classical": "classical music",
    "hip-hop": "hip hop music",
    "rap": "rap music",
    "country": "country music",
    "electronic": "electronic music",
    "r&b": "r&b music",
    "latin": "latin music",
    "metal": "metal music",
    "indie": "indie music",
    "folk": "folk music",
    "blues": "blues music",
    "reggae": "reggae music"
}

def search_itunes(term, limit=10):
    """Search iTunes API"""
    params = {
        "term": term,
        "limit": limit,
        "media": "music",
        "entity": "song"
    }
    try:
        response = requests.get(ITUNES_SEARCH_URL, params=params)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        return None

# get_mood_genres moved to recommendation.py

app.include_router(playlists_router)
app.include_router(auth_router)
app.include_router(admin_router)


@app.get("/")
def home():
    return {
        "message": "Music Playlist Generator API running",
        "description": "Generate playlists based on mood, genre, and favorite artists",
        "endpoints": {
            "/genres": "List available genres",
            "/moods": "List available moods",
            "/auth/google/login": "Google OAuth login",
            "/auth/google/callback": "Google OAuth callback",
            "/search": "Search by genre/mood/artist",
            "/custom": "Custom playlist",
            "/playlists": "GET user's playlists (requires auth)",
            "/playlists/": "POST new playlist (requires auth)",
            "/playlists/{id}": "DELETE playlist (requires auth)"
        }
    }

@app.get("/genres")
def list_genres():
    """List all available genres"""
    return {
        "genres": list(GENRE_MAP.keys())
    }

@app.get("/moods")
def list_moods():
    """List all available moods"""
    return {
        "moods": list(MOOD_GENRE_MAP.keys())
    }

@app.get("/search")
def search_songs(
    q: str = Query(default="Taylor Swift", description="Search query"),
    limit: int = Query(default=10, description="Number of results")
):
    """Search for songs"""
    results = search_itunes(q, limit)
    
    if results and "results" in results:
        songs = []
        for track in results["results"]:
            songs.append({
                "title": track.get("trackName"),
                "artist": track.get("artistName"),
                "album": track.get("collectionName"),
                "preview_url": track.get("previewUrl"),
                "artwork": track.get("artworkUrl100"),
                "genre": track.get("primaryGenreName"),
                "duration": track.get("trackTimeMillis")
            })
        return {"results": songs, "count": len(songs)}
    
    return {"error": "No results found"}

@app.get("/by-mood")
def playlist_by_mood(
    mood: str = Query(..., description="Mood (happy, sad, energetic, relaxing, etc.)"),
    limit: int = Query(default=10, description="Number of songs")
):
    """Generate explainable playlist based on mood using ML"""
    mood_lower = mood.lower()
    preferences = {"mood": mood_lower}
    
    # Fetch broader candidates
    genres = ["pop", "rock", "jazz", "hip-hop", "electronic"]  # Broad search
    all_songs = []
    for genre in genres:
        results = search_itunes(genre, limit=limit*3)
        if results and "results" in results:
            for track in results["results"]:
                all_songs.append({
                    "title": track.get("trackName"),
                    "artist": track.get("artistName"),
                    "album": track.get("collectionName"),
                    "preview_url": track.get("previewUrl"),
                    "artwork": track.get("artworkUrl100"),
                    "genre": track.get("primaryGenreName"),
                    "mood": mood_lower,
                    "duration": track.get("trackTimeMillis")
                })
    
    # ML ranking + explanations
    recommendations = recommendation_engine.recommend(all_songs, preferences, limit)
    
    return {
        "mood": mood_lower,
        "method": "ML cosine similarity",
        "playlist": recommendations,
        "count": len(recommendations)
    }

@app.get("/by-genre")
def playlist_by_genre(
    genre: str = Query(..., description="Genre name"),
    limit: int = Query(default=10, description="Number of songs")
):
    """Generate explainable playlist based on genre using ML"""
    genre_lower = genre.lower()
    preferences = {"genre": genre_lower}
    
    # Fetch candidates from genre + similar
    base_results = search_itunes(genre_lower, limit=limit*3)
    all_songs = []
    if base_results and "results" in base_results:
        for track in base_results["results"]:
            all_songs.append({
                "title": track.get("trackName"),
                "artist": track.get("artistName"),
                "album": track.get("collectionName"),
                "preview_url": track.get("previewUrl"),
                "artwork": track.get("artworkUrl100"),
                "genre": track.get("primaryGenreName"),
                "duration": track.get("trackTimeMillis")
            })
    
    # ML ranking + explanations
    recommendations = recommendation_engine.recommend(all_songs, preferences, limit)
    
    return {
        "genre": genre_lower,
        "method": "ML cosine similarity",
        "playlist": recommendations,
        "count": len(recommendations)
    }

@app.get("/by-artist")
def playlist_by_artist(
    artist: str = Query(..., description="Favorite artist name"),
    limit: int = Query(default=10, description="Number of songs")
):
    """Generate playlist based on favorite artist"""
    results = search_itunes(artist, limit=limit * 2)
    
    songs = []
    if results and "results" in results:
        for track in results["results"]:
            songs.append({
                "title": track.get("trackName"),
                "artist": track.get("artistName"),
                "album": track.get("collectionName"),
                "preview_url": track.get("previewUrl"),
                "artwork": track.get("artworkUrl100"),
                "genre": track.get("primaryGenreName"),
                "duration": track.get("trackTimeMillis")
            })
    
    # Shuffle and limit
    random.shuffle(songs)
    final_playlist = songs[:limit]
    
    return {
        "based_on_artist": artist,
        "playlist": final_playlist,
        "count": len(final_playlist)
    }

@app.get("/custom")
def custom_playlist(
    genre: str = Query(default="", description="Genre preference"),
    mood: str = Query(default="", description="Mood preference"),
    artist: str = Query(default="", description="Favorite artist"),
    limit: int = Query(default=10, description="Number of songs")
):
    """Custom explainable playlist using ML"""
    preferences = {
        "genre": genre,
        "mood": mood,
        "artist": artist
    }
    
    # Fetch broad candidates
    all_songs = []
    search_terms = [genre or "", mood or "", artist or ""]
    for term in search_terms:
        if term:
            results = search_itunes(term, limit=limit*2)
            if results and "results" in results:
                for track in results["results"]:
                    song = {
                        "title": track.get("trackName"),
                        "artist": track.get("artistName"),
                        "album": track.get("collectionName"),
                        "preview_url": track.get("previewUrl"),
                        "artwork": track.get("artworkUrl100"),
                        "genre": track.get("primaryGenreName"),
                        "duration": track.get("trackTimeMillis")
                    }
                    all_songs.append(song)
    
    if not all_songs:
        fallback_results = search_itunes("pop", limit=20)
        if fallback_results and "results" in fallback_results:
            for track in fallback_results["results"]:
                all_songs.append({
                    "title": track.get("trackName"),
                    "artist": track.get("artistName"),
                    "album": track.get("collectionName"),
                    "preview_url": track.get("previewUrl"),
                    "artwork": track.get("artworkUrl100"),
                    "genre": track.get("primaryGenreName"),
                    "duration": track.get("trackTimeMillis")
                })
    
    # Dedup + ML ranking
    seen = set()
    unique_songs = []
    for song in all_songs:
        key = (song.get("title"), song.get("artist"))
        if key not in seen:
            seen.add(key)
            unique_songs.append(song)
    
    recommendations = recommendation_engine.recommend(unique_songs, preferences, limit)
    
    return {
        "preferences": preferences,
        "method": "ML cosine similarity",
        "playlist": recommendations,
        "count": len(recommendations)
    }

@app.get("/similar-songs")
def similar_songs(
    title: str = Query(..., description="Selected song title"),
    artist: str = Query(..., description="Selected song artist"),
    genre: str = Query(default="", description="Selected song genre"),
    limit: int = Query(default=6, description="Number of similar songs")
):
    """Recommend songs similar to a selected track using ML cosine similarity"""
    selected_song = {
        "title": title,
        "artist": artist,
        "genre": genre
    }

    candidate_terms = [f"{title} {artist}", artist, genre]
    candidate_songs = []

    for term in candidate_terms:
        if not term:
            continue

        results = search_itunes(term, limit=max(limit * 4, 12))
        if results and "results" in results:
            for track in results["results"]:
                candidate_songs.append({
                    "title": track.get("trackName"),
                    "artist": track.get("artistName"),
                    "album": track.get("collectionName"),
                    "preview_url": track.get("previewUrl"),
                    "artwork": track.get("artworkUrl100"),
                    "genre": track.get("primaryGenreName"),
                    "duration": track.get("trackTimeMillis")
                })

    seen = set()
    unique_candidates = []
    for song in candidate_songs:
        key = (song.get("title"), song.get("artist"))
        if key not in seen:
            seen.add(key)
            unique_candidates.append(song)

    recommendations = recommendation_engine.recommend_similar_songs(
        selected_song,
        unique_candidates,
        limit
    )

    return {
        "selected_song": selected_song,
        "method": "ML cosine similarity for song-to-song recommendations",
        "similar_songs": recommendations,
        "count": len(recommendations)
    }
