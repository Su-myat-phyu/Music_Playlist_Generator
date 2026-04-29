from typing import List, Dict, Any, Tuple, Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MultiLabelBinarizer
import re

# Replicate mappings from main.py
GENRE_MAP = {
    "rock": "rock", "pop": "pop", "jazz": "jazz", "classical": "classical",
    "hip-hop": "hip hop", "rap": "rap", "country": "country", "electronic": "electronic",
    "r&b": "r&b", "latin": "latin", "metal": "metal", "indie": "indie",
    "folk": "folk", "blues": "blues", "reggae": "reggae"
}

# Genre to proxy audio features: [energy, danceability, valence] (0-1 scale heuristics)
GENRE_AUDIO_MAP = {
    "rock": [0.85, 0.45, 0.55],
    "pop": [0.65, 0.80, 0.75],
    "jazz": [0.40, 0.35, 0.50],
    "classical": [0.25, 0.15, 0.40],
    "hip hop": [0.75, 0.70, 0.60],
    "rap": [0.70, 0.65, 0.50],
    "country": [0.60, 0.50, 0.65],
    "electronic": [0.80, 0.85, 0.60],
    "r&b": [0.55, 0.75, 0.70],
    "latin": [0.70, 0.85, 0.80],
    "metal": [0.95, 0.30, 0.45],
    "indie": [0.50, 0.55, 0.60],
    "folk": [0.45, 0.40, 0.65],
    "blues": [0.55, 0.45, 0.50],
    "reggae": [0.60, 0.75, 0.70]
}

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

ALL_GENRES = list(GENRE_MAP.keys())

GENRE_ALIASES = {
    "hip-hop": ["hip hop", "hip-hop"],
    "r&b": ["r&b", "rnb", "r b", "soul"],
}

MOOD_TEXT_MAP = {
    "happy": ["uplifting", "bright", "joyful"],
    "sad": ["melancholy", "emotional", "slow", "minor key"],
    "energetic": ["energetic", "upbeat", "driving"],
    "relaxing": ["calm", "peaceful", "soft"],
    "romantic": ["romantic", "love", "warm"],
    "focus": ["instrumental", "study", "focused"],
    "party": ["party", "dance", "upbeat"],
    "workout": ["workout", "high energy", "driving"],
    "chill": ["chill", "mellow", "laid back"],
}

MOOD_AUDIO_TARGETS = {
    "happy": [0.65, 0.75, 0.85],
    "sad": [0.35, 0.30, 0.20],
    "energetic": [0.90, 0.70, 0.65],
    "relaxing": [0.25, 0.25, 0.55],
    "romantic": [0.45, 0.55, 0.75],
    "focus": [0.25, 0.20, 0.50],
    "party": [0.85, 0.90, 0.80],
    "workout": [0.95, 0.70, 0.60],
    "chill": [0.35, 0.45, 0.60],
}

class RecommendationEngine:
    def __init__(self):
        self.tfidf = TfidfVectorizer(max_features=50, lowercase=True)
        self.genre_mlb = MultiLabelBinarizer(classes=ALL_GENRES)
        self._fit_transformers()

    def _fit_transformers(self):
        # Fit TF-IDF on richer vocab (genres + sample song terms)
        sample_vocab = [' '.join(ALL_GENRES) + ' song music artist album rock pop love heart dance night love']
        self.tfidf.fit(sample_vocab)
        self.genre_mlb.fit([ALL_GENRES])

    def _extract_song_features(self, song: Dict[str, Any], user_preferences: Dict[str, Any]) -> Dict[str, Any]:
        "Extract rich ML features: TF-IDF text + genre + audio proxies + duration"
        # Rich text: title + artist + album
        text_input = f"{song.get('title', '')} {song.get('artist', '')} {song.get('album', '')}".lower()
        
        # Genre multi-hot
        genre = song.get('genre', '').lower()
        genres = [g for g in ALL_GENRES if g in genre]
        genre_vec = self.genre_mlb.transform([genres]).flatten()
        
        # TF-IDF text embedding (style/semantic)
        text_vec = self.tfidf.transform([text_input]).toarray().flatten()
        
        # Duration normalized (0-1, assume max 10min song = 600000ms)
        duration = song.get('duration', 0) or 0
        duration_norm = min(duration / 600000.0, 1.0)
        
        # Audio proxy from genre [energy, dance, valence]
        audio_proxy = GENRE_AUDIO_MAP.get(genre.split()[0], [0.5, 0.5, 0.5])
        
        # Combined numerical features
        num_features = np.array([duration_norm, *audio_proxy])
        
        features = {
            'text_vec': text_vec,
            'genre_vec': genre_vec,
            'num_features': num_features,
            'full_vector': np.concatenate([text_vec, genre_vec, num_features]).astype(float),
            'artist': song.get('artist', '').lower(),
        }
        return features

    def _genre_terms(self, genre: str) -> List[str]:
        genre = (genre or "").strip().lower()
        canonical = GENRE_MAP.get(genre, genre)
        return [canonical, *GENRE_ALIASES.get(genre, [])]

    def _profile_genre_key(self, genre: str) -> Optional[str]:
        genre = (genre or "").strip().lower()
        if genre in ALL_GENRES:
            return genre
        for key, value in GENRE_MAP.items():
            if genre == value:
                return key
        return None

    def _matches_selected_genre(self, song: Dict[str, Any], selected_genre: str) -> bool:
        return self._genre_match_score(song, selected_genre) > 0

    def _genre_match_score(self, song: Dict[str, Any], selected_genre: str) -> float:
        if not selected_genre:
            return 0.0

        song_genre = (song.get('genre') or '').lower()
        genre_terms = self._genre_terms(selected_genre)

        if any(term and term in song_genre for term in genre_terms):
            return 1.0

        searchable_text = " ".join([
            str(song.get('title') or '').lower(),
            str(song.get('album') or '').lower(),
        ])
        if any(term and term in searchable_text for term in genre_terms):
            return 0.55

        return 0.0

    def _matches_exclusion_terms(self, song: Dict[str, Any]) -> bool:
        title_album_artist = " ".join([
            str(song.get('title') or '').lower(),
            str(song.get('album') or '').lower(),
            str(song.get('artist') or '').lower(),
        ])

        # These are common iTunes search drifts that should not override a selected genre.
        off_topic_terms = [
            "baby", "babies", "lullaby", "lullabies", "sleeping baby",
            "white noise", "waterfall sounds", "dog music", "music for pets",
            "meditation music", "nature sounds",
        ]

        return any(term in title_album_artist for term in off_topic_terms)

    def _mood_match_score(self, song: Dict[str, Any], song_feat: Dict[str, Any], selected_mood: str) -> float:
        if not selected_mood:
            return 0.0

        mood_terms = MOOD_TEXT_MAP.get(selected_mood, [])
        song_genre = str(song.get('genre') or '').lower()
        song_text = " ".join([
            str(song.get('title') or '').lower(),
            str(song.get('artist') or '').lower(),
            str(song.get('album') or '').lower(),
            song_genre,
        ])

        text_score = 1.0 if any(term in song_text for term in mood_terms) else 0.0

        target_audio = MOOD_AUDIO_TARGETS.get(selected_mood)
        if target_audio is None:
            return text_score

        audio_proxy = song_feat['num_features'][1:4]
        distance = np.linalg.norm(audio_proxy - np.array(target_audio))
        audio_score = max(0.0, 1.0 - (distance / np.sqrt(3)))

        return min(1.0, (audio_score * 0.7) + (text_score * 0.3))

    def _artist_match_score(self, song: Dict[str, Any], selected_artist: str) -> float:
        if not selected_artist:
            return 0.0

        song_artist = str(song.get('artist') or '').lower()
        song_text = " ".join([
            song_artist,
            str(song.get('title') or '').lower(),
            str(song.get('album') or '').lower(),
        ])

        if selected_artist in song_artist:
            return 1.0
        if selected_artist in song_text:
            return 0.6
        return 0.0

    def _active_filter_weights(self, selected_genre: str, selected_mood: str, selected_artist: str) -> Dict[str, float]:
        base_weights = {
            "genre": 0.40 if selected_genre else 0.0,
            "mood": 0.35 if selected_mood else 0.0,
            "artist": 0.25 if selected_artist else 0.0,
        }
        total = sum(base_weights.values())
        if total == 0:
            return {"genre": 0.0, "mood": 0.0, "artist": 0.0}
        return {key: value / total for key, value in base_weights.items()}

    def _format_duration(self, duration_ms: Optional[int]) -> str:
        if not duration_ms:
            return ""

        total_seconds = max(0, int(duration_ms / 1000))
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes}:{seconds:02d}"

    def describe_song(self, song: Dict[str, Any], preferences: Dict[str, Any]) -> str:
        "Create a short, display-friendly description for a recommended song."
        artist = song.get("artist") or "this artist"
        album = song.get("album") or ""
        genre = song.get("genre") or preferences.get("genre") or "music"
        selected_mood = (preferences.get("mood") or "").strip().lower()
        duration = self._format_duration(song.get("duration"))

        parts = [f"A {genre} track by {artist}"]

        if album:
            parts.append(f"from {album}")

        description = " ".join(parts)

        if selected_mood:
            description += f", chosen for a {selected_mood} listening vibe"
        else:
            description += ", chosen for your current music preferences"

        if duration:
            description += f" ({duration})"

        return description + "."

    def _build_user_profile(self, preferences: Dict[str, Any]) -> Dict[str, Any]:
        "Build user preference vector"
        genre = preferences.get('genre', '').lower()
        mood = preferences.get('mood', '').lower()
        artist = preferences.get('artist', '').lower()
        
        # Mood genres to vector
        mood_genres = MOOD_GENRE_MAP.get(mood, [])
        profile_genres = [
            mapped_genre
            for mapped_genre in {self._profile_genre_key(item) for item in [genre] + mood_genres}
            if mapped_genre
        ] if genre or mood else []
        
        genre_vec = self.genre_mlb.transform([profile_genres]).flatten()
        text_terms = [artist] if artist else []
        if mood: text_terms.append(mood)
        if genre: text_terms.append(genre)
        text_vec = self.tfidf.transform([' '.join(text_terms)]).toarray().flatten()
        
        return {
            'genre_vec': genre_vec,
            'text_vec': text_vec,
            'target_artist': artist
        }

    def score_song(self, song: Dict[str, Any], user_profile: Dict[str, Any], preferences: Dict[str, Any]) -> Tuple[float, str]:
        "Score song against user profile, return score + explanation"
        song_feat = self._extract_song_features(song, user_profile)
        score = 0.0

        selected_genre = preferences.get('genre', '').strip().lower()
        selected_mood = preferences.get('mood', '').strip().lower()
        selected_artist = preferences.get('artist', '').strip().lower()
        song_genre = song.get('genre', '').lower()

        explanation_reasons = []

        if self._matches_exclusion_terms(song):
            return -1.0, "Skipped because it appears to be background, sleep, or novelty audio."

        filter_weights = self._active_filter_weights(selected_genre, selected_mood, selected_artist)

        genre_match = self._genre_match_score(song, selected_genre)
        mood_match = self._mood_match_score(song, song_feat, selected_mood)
        artist_match = self._artist_match_score(song, selected_artist)

        score += genre_match * filter_weights["genre"]
        score += mood_match * filter_weights["mood"]
        score += artist_match * filter_weights["artist"]

        text_sim = cosine_similarity([user_profile['text_vec']], [song_feat['text_vec']])[0][0]
        score += text_sim * 0.08

        if selected_genre and genre_match >= 1.0:
            explanation_reasons.append(f"it matches your selected genre ({selected_genre})")
        elif selected_genre and genre_match > 0:
            explanation_reasons.append(f"it is related to your selected genre ({selected_genre})")

        if selected_mood and mood_match >= 0.55:
            explanation_reasons.append(f"it fits the {selected_mood} mood through its musical style")

        if selected_artist and artist_match >= 1.0:
            explanation_reasons.append(f"it matches your selected artist ({song.get('artist', '')})")
        elif selected_artist and artist_match > 0:
            explanation_reasons.append(f"it is related to your selected artist ({selected_artist})")

        if not explanation_reasons:
            explanation_reasons.append("it is a strong overall match based on your listening preferences")

        if len(explanation_reasons) == 1:
            explanation = f"Recommended because {explanation_reasons[0]}."
        else:
            explanation = f"Recommended because {', '.join(explanation_reasons[:-1])}, and {explanation_reasons[-1]}."

        return score, explanation

    def recommend(self, candidate_songs: List[Dict[str, Any]], preferences: Dict[str, Any], limit: int = 10) -> List[Dict[str, Any]]:
        "Recommend top songs with explanations"
        user_profile = self._build_user_profile(preferences)
        scored_songs = []
        
        for song in candidate_songs:
            score, explanation = self.score_song(song, user_profile, preferences)
            if score >= 0:
                scored_songs.append((song, score, explanation))
        
        # Sort by score desc
        scored_songs.sort(key=lambda x: x[1], reverse=True)
        
        recommendations = []
        for song, score, explanation in scored_songs[:limit]:
            song_copy = song.copy()
            song_copy['recommendation_score'] = round(float(score), 3)
            song_copy['explanation'] = explanation
            song_copy['description'] = self.describe_song(song_copy, preferences)
            recommendations.append(song_copy)
        
        return recommendations

    def recommend_similar_songs(
        self,
        selected_song: Dict[str, Any],
        candidate_songs: List[Dict[str, Any]],
        limit: int = 6
    ) -> List[Dict[str, Any]]:
        "Recommend songs similar to a selected track using cosine similarity"
        selected_features = self._extract_song_features(selected_song, {})
        selected_vector = selected_features['full_vector']

        ranked_songs = []
        selected_title = selected_song.get('title', '').strip().lower()
        selected_artist = selected_song.get('artist', '').strip().lower()
        selected_genre = selected_song.get('genre', '').strip().lower()

        for song in candidate_songs:
            song_title = song.get('title', '').strip().lower()
            song_artist = song.get('artist', '').strip().lower()

            if song_title == selected_title and song_artist == selected_artist:
                continue

            song_features = self._extract_song_features(song, {})
            song_vector = song_features['full_vector']

            similarity = cosine_similarity([selected_vector], [song_vector])[0][0]

            if not np.isfinite(similarity):
                similarity = 0.0

            candidate_genre = song.get('genre', '').strip().lower()
            reasons = []

            if selected_genre and candidate_genre and (
                selected_genre in candidate_genre or candidate_genre in selected_genre
            ):
                reasons.append("it shares a similar genre")

            if selected_artist and selected_artist == song_artist:
                reasons.append("it is by the same artist")

            if similarity > 0.15:
                reasons.append("its title, artist, and genre features are close to the selected track")

            if not reasons:
                reasons.append("it has a related musical profile based on cosine similarity")

            if len(reasons) == 1:
                explanation = (
                    f"Recommended because {reasons[0]} to "
                    f"{selected_song.get('title', 'the selected song')} by {selected_song.get('artist', 'this artist')}."
                )
            else:
                explanation = (
                    f"Recommended because {', '.join(reasons[:-1])}, and {reasons[-1]} to "
                    f"{selected_song.get('title', 'the selected song')} by {selected_song.get('artist', 'this artist')}."
                )

            ranked_songs.append((song, similarity, explanation))

        ranked_songs.sort(key=lambda item: item[1], reverse=True)

        recommendations = []
        for song, similarity, explanation in ranked_songs[:limit]:
            song_copy = song.copy()
            song_copy['explanation'] = explanation
            song_copy['similarity_score'] = round(float(similarity), 3)
            song_copy['description'] = self.describe_song(song_copy, {
                "genre": selected_song.get("genre", ""),
                "artist": selected_song.get("artist", ""),
                "mood": "",
            })
            recommendations.append(song_copy)

        return recommendations

# Global instance
recommendation_engine = RecommendationEngine()

