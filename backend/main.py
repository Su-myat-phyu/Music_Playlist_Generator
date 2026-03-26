from fastapi import FastAPI, Query, Depends
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from app.models.playlist import PlaylistCreate
from app.routers.playlists import router as playlists_router
from app.routers.auth import router as auth_router
from app.services.db import PlaylistDB
from app.services.auth import get_current_user
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

# Genre to iTunes term mapping
GENRE_MAP = {
    "rock": "rock",
    "pop": "pop",
    "jazz": "jazz",
    "classical": "classical",
    "hip-hop": "hip hop",
    "rap": "rap",
    "country": "country",
    "electronic": "electronic",
    "r&b": "r&b",
    "latin": "latin",
    "metal": "metal",
    "indie": "indie",
    "folk": "folk",
    "blues": "blues",
    "reggae": "reggae"
}

# Mood to genre mapping (for mood-based recommendations)
MOOD_GENRE_MAP = {
    "happy": ["pop", "dance", "happy"],
    "sad": ["ballad", "soul", "r&b"],
    "energetic": ["rock", "metal", "hip hop"],
    "relaxing": ["classical", "jazz", "ambient"],
    "romantic": ["r&b", "soul", "ballad"],
    "focus": ["classical", "instrumental", "piano"],
    "party": ["dance", "hip hop", "pop"],
    "workout": ["rock", "electronic", "hip hop"],
    "chill": ["indie", "jazz", "lo-fi"]
}

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

def get_mood_genres(mood):
    """Get genre terms for a mood"""
    return MOOD_GENRE_MAP.get(mood.lower(), ["pop", "rock"])

app.include_router(playlists_router)
app.include_router(auth_router)

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
    """Generate playlist based on mood"""
    mood_lower = mood.lower()
    genres = get_mood_genres(mood_lower)
    
    all_songs = []
    
    # Search for each genre related to the mood
    for genre in genres:
        results = search_itunes(genre, limit=limit)
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
    
    # Shuffle and limit
    random.shuffle(all_songs)
    final_playlist = all_songs[:limit]
    
    return {
        "mood": mood_lower,
        "genres_used": genres,
        "playlist": final_playlist,
        "count": len(final_playlist)
    }

@app.get("/by-genre")
def playlist_by_genre(
    genre: str = Query(..., description="Genre name"),
    limit: int = Query(default=10, description="Number of songs")
):
    """Generate playlist based on genre"""
    genre_lower = genre.lower()
    search_term = GENRE_MAP.get(genre_lower, genre_lower)
    
    results = search_itunes(search_term, limit=limit * 2)  # Get more to filter
    
    songs = []
    if results and "results" in results:
        for track in results["results"]:
            # Filter to ensure genre relevance
            track_genre = track.get("primaryGenreName", "").lower()
            if genre_lower in track_genre or track_genre in GENRE_MAP:
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
        "genre": genre_lower,
        "playlist": final_playlist,
        "count": len(final_playlist)
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
    """Custom playlist with multiple preferences"""
    all_songs = []
    
    # If artist is specified, search by artist
    if artist:
        results = search_itunes(artist, limit=limit)
        if results and "results" in results:
            for track in results["results"]:
                all_songs.append({
                    "title": track.get("trackName"),
                    "artist": track.get("artistName"),
                    "album": track.get("collectionName"),
                    "preview_url": track.get("previewUrl"),
                    "artwork": track.get("artworkUrl100"),
                    "genre": track.get("primaryGenreName"),
                    "duration": track.get("trackTimeMillis")
                })
    
    # If genre is specified, add genre songs
    if genre:
        genre_lower = genre.lower()
        search_term = GENRE_MAP.get(genre_lower, genre_lower)
        results = search_itunes(search_term, limit=limit)
        if results and "results" in results:
            for track in results["results"]:
                all_songs.append({
                    "title": track.get("trackName"),
                    "artist": track.get("artistName"),
                    "album": track.get("collectionName"),
                    "preview_url": track.get("previewUrl"),
                    "artwork": track.get("artworkUrl100"),
                    "genre": track.get("primaryGenreName"),
                    "duration": track.get("trackTimeMillis")
                })
    
    # If mood is specified, add mood-based songs
    if mood:
        genres = get_mood_genres(mood)
        for g in genres:
            results = search_itunes(g, limit=limit // 2)
            if results and "results" in results:
                for track in results["results"]:
                    all_songs.append({
                        "title": track.get("trackName"),
                        "artist": track.get("artistName"),
                        "album": track.get("collectionName"),
                        "preview_url": track.get("previewUrl"),
                        "artwork": track.get("artworkUrl100"),
                        "genre": track.get("primaryGenreName"),
                        "mood": mood,
                        "duration": track.get("trackTimeMillis")
                    })
    
    # Remove duplicates and shuffle
    seen = set()
    unique_songs = []
    for song in all_songs:
        key = (song.get("title"), song.get("artist"))
        if key not in seen:
            seen.add(key)
            unique_songs.append(song)
    
    random.shuffle(unique_songs)
    final_playlist = unique_songs[:limit]
    
    return {
        "preferences": {
            "genre": genre,
            "mood": mood,
            "artist": artist
        },
        "playlist": final_playlist,
        "count": len(final_playlist)
    }

