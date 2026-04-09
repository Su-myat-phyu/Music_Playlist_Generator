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

    def _build_user_profile(self, preferences: Dict[str, Any]) -> Dict[str, Any]:
        "Build user preference vector"
        genre = preferences.get('genre', '').lower()
        mood = preferences.get('mood', '').lower()
        artist = preferences.get('artist', '').lower()
        
        # Mood genres to vector
        mood_genres = MOOD_GENRE_MAP.get(mood, [])
        profile_genres = list(set([genre] + mood_genres)) if genre or mood else []
        
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

        # Genre similarity (60%)
        if np.any(user_profile['genre_vec']):
            genre_sim = cosine_similarity([user_profile['genre_vec']], [song_feat['genre_vec']])[0][0]
            score += genre_sim * 0.6

            matching_genres = [
                ALL_GENRES[i]
                for i in range(len(song_feat['genre_vec']))
                if song_feat['genre_vec'][i] > 0 and user_profile['genre_vec'][i] > 0
            ]

            if selected_genre and selected_genre in song_genre:
                explanation_reasons.append(f"it matches your selected genre ({selected_genre})")
            elif matching_genres:
                explanation_reasons.append(f"its genre is similar to your preferences ({', '.join(matching_genres)})")
            elif genre_sim > 0.2:
                explanation_reasons.append("its genre profile is close to your selected preferences")

        # Text/style similarity (30%)
        text_sim = cosine_similarity([user_profile['text_vec']], [song_feat['text_vec']])[0][0]
        score += text_sim * 0.3

        mood_genres = MOOD_GENRE_MAP.get(selected_mood, [])
        mood_match = selected_mood and any(genre_term in song_genre for genre_term in mood_genres)

        if mood_match:
            explanation_reasons.append(f"it fits the {selected_mood} mood through its musical style")
        elif selected_mood and text_sim > 0.15:
            explanation_reasons.append(f"its style is similar to songs that match a {selected_mood} mood")

        # Artist match (10%)
        artist_match = 1.0 if user_profile['target_artist'] and user_profile['target_artist'] in song_feat['artist'] else 0.0
        score += artist_match * 0.1
        if artist_match:
            explanation_reasons.append(f"it matches your selected artist ({song.get('artist', '')})")
        elif selected_artist and text_sim > 0.2:
            explanation_reasons.append(f"it has a style related to your interest in {selected_artist}")

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
            scored_songs.append((song, score, explanation))
        
        # Sort by score desc
        scored_songs.sort(key=lambda x: x[1], reverse=True)
        
        recommendations = []
        for song, score, explanation in scored_songs[:limit]:
            song_copy = song.copy()
            song_copy['recommendation_score'] = round(score, 3)
            song_copy['explanation'] = explanation
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
            recommendations.append(song_copy)

        return recommendations

# Global instance
recommendation_engine = RecommendationEngine()

