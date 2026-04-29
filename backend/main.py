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
import re

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

MOOD_SEARCH_PHRASES = {
    "happy": ["uplifting", "joyful", "bright"],
    "sad": ["melancholy", "emotional", "slow"],
    "energetic": ["energetic", "upbeat", "driving"],
    "relaxing": ["calm", "peaceful", "soft"],
    "romantic": ["romantic", "love", "warm"],
    "focus": ["instrumental", "study", "focused"],
    "party": ["party", "dance", "upbeat"],
    "workout": ["workout", "high energy", "driving"],
    "chill": ["chill", "mellow", "laid back"],
}

NLP_FILLER_WORDS = {
    "find", "search", "show", "give", "me", "songs", "song", "tracks", "track",
    "music", "playlist", "recommend", "recommendations", "for", "that", "are",
    "is", "with", "some", "please", "to", "listen", "listening", "by", "from",
    "artist", "singer", "band",
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

def high_quality_artwork_url(artwork_url):
    """Return a larger iTunes artwork URL when the API provides a thumbnail URL."""
    if not artwork_url:
        return artwork_url
    return artwork_url.replace("100x100bb", "1200x1200bb")

def serialize_itunes_track(track, extra_fields=None):
    """Convert an iTunes API result to the song shape used by the app."""
    song = {
        "title": track.get("trackName"),
        "artist": track.get("artistName"),
        "album": track.get("collectionName"),
        "preview_url": track.get("previewUrl"),
        "artwork": high_quality_artwork_url(track.get("artworkUrl100")),
        "genre": track.get("primaryGenreName"),
        "duration": track.get("trackTimeMillis")
    }
    if extra_fields:
        song.update(extra_fields)
    return song

def build_custom_search_terms(genre="", mood="", artist=""):
    """Build focused iTunes search terms from the combined user intent."""
    genre = (genre or "").strip().lower()
    mood = (mood or "").strip().lower()
    artist = (artist or "").strip()

    genre_phrase = GENRE_DESCRIPTIONS.get(genre, f"{genre} music" if genre else "")
    mood_phrases = MOOD_SEARCH_PHRASES.get(mood, [mood] if mood else [])
    terms = []

    if artist and genre_phrase and mood_phrases:
        terms.append(f"{artist} {mood_phrases[0]} {genre_phrase}")
    if artist and mood_phrases:
        terms.append(f"{artist} {mood_phrases[0]} music")
    if artist and genre_phrase:
        terms.append(f"{artist} {genre_phrase}")
    if genre_phrase and mood_phrases:
        terms.extend(f"{phrase} {genre_phrase}" for phrase in mood_phrases[:3])
    if genre_phrase:
        terms.append(genre_phrase)
    if artist:
        terms.append(artist)
    if not genre_phrase and mood_phrases:
        terms.extend(f"{phrase} music" for phrase in mood_phrases[:3])

    seen = set()
    unique_terms = []
    for term in terms:
        normalized = term.strip().lower()
        if normalized and normalized not in seen:
            seen.add(normalized)
            unique_terms.append(term.strip())

    return unique_terms

def parse_nlp_music_query(query=""):
    """Extract genre, mood, and artist hints from a natural-language music query."""
    raw_query = (query or "").strip()
    normalized = re.sub(r"\s+", " ", raw_query.lower())

    detected_genre = ""
    for genre_key, genre_phrase in GENRE_DESCRIPTIONS.items():
        genre_terms = {genre_key, genre_phrase.replace(" music", "")}
        if genre_key == "hip-hop":
            genre_terms.update({"hip hop", "hiphop"})
        if genre_key == "r&b":
            genre_terms.update({"rnb", "r b", "rhythm and blues"})
        if any(re.search(rf"\b{re.escape(term)}\b", normalized) for term in genre_terms):
            detected_genre = genre_key
            break

    detected_mood = ""
    for mood_key, mood_terms in MOOD_SEARCH_PHRASES.items():
        all_mood_terms = {mood_key, *mood_terms}
        if mood_key == "sad":
            all_mood_terms.update({"depressing", "heartbreak", "heartbroken", "emotional"})
        if mood_key == "happy":
            all_mood_terms.update({"cheerful", "feel good", "feel-good"})
        if mood_key == "relaxing":
            all_mood_terms.update({"relaxed", "peaceful", "calming"})
        if any(re.search(rf"\b{re.escape(term)}\b", normalized) for term in all_mood_terms):
            detected_mood = mood_key
            break

    detected_artist = ""
    artist_match = re.search(
        r"\b(?:by|from|artist|singer|band)\s+(.+?)(?:\s+(?:genre|mood|songs|tracks|music|playlist)\b|$)",
        raw_query,
        flags=re.IGNORECASE,
    )
    if artist_match:
        detected_artist = artist_match.group(1).strip(" .,!?:;")

    remaining_text = normalized
    for value in [detected_genre, detected_mood]:
        if value:
            remaining_text = re.sub(rf"\b{re.escape(value)}\b", " ", remaining_text)
    if detected_genre:
        remaining_text = remaining_text.replace(GENRE_DESCRIPTIONS[detected_genre].replace(" music", ""), " ")
    for phrase in MOOD_SEARCH_PHRASES.get(detected_mood, []):
        remaining_text = re.sub(rf"\b{re.escape(phrase)}\b", " ", remaining_text)
    if detected_artist:
        remaining_text = remaining_text.replace(detected_artist.lower(), " ")

    tokens = [
        token for token in re.findall(r"[a-z0-9&'-]+", remaining_text)
        if token not in NLP_FILLER_WORDS and len(token) > 1
    ]
    free_text = " ".join(tokens).strip()

    return {
        "query": raw_query,
        "genre": detected_genre,
        "mood": detected_mood,
        "artist": detected_artist,
        "free_text": free_text,
    }

def collect_ranked_recommendations(preferences, limit=10, extra_terms=None):
    all_songs = []
    search_terms = build_custom_search_terms(
        preferences.get("genre", ""),
        preferences.get("mood", ""),
        preferences.get("artist", "")
    )

    if extra_terms:
        search_terms = [*extra_terms, *search_terms]

    if not search_terms:
        search_terms = ["pop music"]

    seen_terms = set()
    for term in search_terms:
        normalized_term = term.strip().lower()
        if not normalized_term or normalized_term in seen_terms:
            continue
        seen_terms.add(normalized_term)

        results = search_itunes(term, limit=max(limit * 4, 20))
        if results and "results" in results:
            for track in results["results"]:
                all_songs.append(serialize_itunes_track(track))

    if not all_songs:
        fallback_term = GENRE_DESCRIPTIONS.get(
            preferences.get("genre", "").lower(),
            f"{preferences.get('genre')} music" if preferences.get("genre") else "pop"
        )
        fallback_results = search_itunes(fallback_term, limit=max(limit * 4, 20))
        if fallback_results and "results" in fallback_results:
            for track in fallback_results["results"]:
                all_songs.append(serialize_itunes_track(track))

    seen = set()
    unique_songs = []
    for song in all_songs:
        key = (song.get("title"), song.get("artist"))
        if key not in seen:
            seen.add(key)
            unique_songs.append(song)

    return recommendation_engine.recommend(unique_songs, preferences, limit)

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
    limit: int = Query(default=10, ge=1, le=50, description="Number of results")
):
    """Search for songs"""
    results = search_itunes(q, limit)
    
    if results and "results" in results:
        songs = []
        for track in results["results"]:
            songs.append(serialize_itunes_track(track))
        return {"results": songs, "count": len(songs)}
    
    return {"error": "No results found"}

@app.get("/by-mood")
def playlist_by_mood(
    mood: str = Query(..., description="Mood (happy, sad, energetic, relaxing, etc.)"),
    limit: int = Query(default=10, ge=1, le=50, description="Number of songs")
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
                all_songs.append(serialize_itunes_track(track, {"mood": mood_lower}))
    
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
    limit: int = Query(default=10, ge=1, le=50, description="Number of songs")
):
    """Generate explainable playlist based on genre using ML"""
    genre_lower = genre.lower()
    preferences = {"genre": genre_lower}
    
    # Fetch candidates from genre + similar
    base_results = search_itunes(genre_lower, limit=limit*3)
    all_songs = []
    if base_results and "results" in base_results:
        for track in base_results["results"]:
            all_songs.append(serialize_itunes_track(track))
    
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
    limit: int = Query(default=10, ge=1, le=50, description="Number of songs")
):
    """Generate playlist based on favorite artist"""
    results = search_itunes(artist, limit=limit * 2)
    
    songs = []
    if results and "results" in results:
        for track in results["results"]:
            songs.append(serialize_itunes_track(track))
    
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
    limit: int = Query(default=10, ge=1, le=50, description="Number of songs")
):
    """Custom explainable playlist using ML"""
    preferences = {
        "genre": genre,
        "mood": mood,
        "artist": artist
    }
    
    recommendations = collect_ranked_recommendations(preferences, limit)
    
    return {
        "preferences": preferences,
        "method": "ML cosine similarity",
        "playlist": recommendations,
        "count": len(recommendations)
    }

@app.get("/nlp-search")
def nlp_search_songs(
    q: str = Query(..., min_length=2, description="Natural-language song search"),
    limit: int = Query(default=10, ge=1, le=50, description="Number of songs")
):
    """Find songs from a natural-language request using parsed genre, mood, and artist hints."""
    parsed = parse_nlp_music_query(q)
    preferences = {
        "genre": parsed["genre"],
        "mood": parsed["mood"],
        "artist": parsed["artist"],
    }

    extra_terms = [q]
    if parsed["free_text"]:
        extra_terms.append(parsed["free_text"])

    recommendations = collect_ranked_recommendations(
        preferences,
        limit,
        extra_terms=extra_terms
    )

    return {
        "query": q,
        "parsed": parsed,
        "preferences": preferences,
        "method": "NLP parsed search + ML ranking",
        "playlist": recommendations,
        "count": len(recommendations)
    }

@app.get("/similar-songs")
def similar_songs(
    title: str = Query(..., description="Selected song title"),
    artist: str = Query(..., description="Selected song artist"),
    genre: str = Query(default="", description="Selected song genre"),
    limit: int = Query(default=6, ge=1, le=50, description="Number of similar songs")
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
                candidate_songs.append(serialize_itunes_track(track))

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
