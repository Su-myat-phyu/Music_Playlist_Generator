import React, { useState, useRef, useCallback, useEffect } from 'react';

import { GoogleOAuthProvider, googleLogout } from '@react-oauth/google';
import AuthShell from './components/AuthShell';
import Dashboard from './components/Dashboard';

import SaveSongModal from './components/SaveSongModal';
import SimilarSongsModal from './components/SimilarSongsModal';
import './App.css';

import { BrowserRouter, Routes, Route } from 'react-router-dom';

const GOOGLE_CLIENT_ID = '80369468349-jlbunn8ubumo4kutgl2aed9dqkv2rf97.apps.googleusercontent.com';

const genres = [
  { id: 'rock', name: 'Rock' },
  { id: 'pop', name: 'Pop' },
  { id: 'jazz', name: 'Jazz' },
  { id: 'classical', name: 'Classical' },
  { id: 'hip-hop', name: 'Hip-Hop' },
  { id: 'electronic', name: 'Electronic' },
  { id: 'indie', name: 'Indie' },
  { id: 'r&b', name: 'R&B' },
  { id: 'country', name: 'Country' },
  { id: 'metal', name: 'Metal' },
  { id: 'latin', name: 'Latin' },
  { id: 'folk', name: 'Folk' },
];

const moods = [
  { id: 'happy', name: 'Happy', emoji: '☀️' },
  { id: 'energetic', name: 'Energetic', emoji: '⚡' },
  { id: 'relaxing', name: 'Relaxing', emoji: '🌊' },
  { id: 'romantic', name: 'Romantic', emoji: '💖' },
  { id: 'sad', name: 'Sad', emoji: '🌧️' },
  { id: 'focus', name: 'Focus', emoji: '🎯' },
  { id: 'party', name: 'Party', emoji: '🎉' },
  { id: 'workout', name: 'Workout', emoji: '💪' },
  { id: 'chill', name: 'Chill', emoji: '😌' },
];

const parseJwtPayload = (tokenStr) => {
  try {
    const payload = tokenStr.split('.')[1];
    if (!payload) {
      throw new Error('Invalid token - no payload');
    }

    const normalized = payload.replace(/-/g, '+').replace(/_/g, '/');
    const padded = normalized.padEnd(Math.ceil(normalized.length / 4) * 4, '=');
    const decoded = JSON.parse(atob(padded));
    return decoded;
  } catch (err) {
    throw new Error('Invalid token format');
  }
};

function App() {
  // Auth state
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [user, setUser] = useState(null);
  const [token, setToken] = useState('');
  // Playlist generator state
  const [selectedGenre, setSelectedGenre] = useState('');
  const [selectedMood, setSelectedMood] = useState('');
  const [selectedArtist, setSelectedArtist] = useState('');
  const [songCount, setSongCount] = useState(10);
  const [playlist, setPlaylist] = useState([]);

  // User playlists state
  const [userPlaylists, setUserPlaylists] = useState([]);
  const [expandedPlaylists, setExpandedPlaylists] = useState({});

  // UI state
  const [loading, setLoading] = useState(false);
  const [songSaveLoading, setSongSaveLoading] = useState(false);
  const [similarSongsLoading, setSimilarSongsLoading] = useState(false);
  const [similarSongs, setSimilarSongs] = useState([]);
  const [selectedBaseSong, setSelectedBaseSong] = useState(null);
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [saveSongDialogOpen, setSaveSongDialogOpen] = useState(false);
  const [selectedSong, setSelectedSong] = useState(null);
  const [playlistTargetMode, setPlaylistTargetMode] = useState('existing');
  const [selectedExistingPlaylistId, setSelectedExistingPlaylistId] = useState('');
  const [newPlaylistName, setNewPlaylistName] = useState('');

  // Audio state
  const audioRef = useRef(null);
  const [currentSongId, setCurrentSongId] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);

  // Utils
  const isTokenExpired = useCallback((tokenStr) => {
    try {
      const payload = parseJwtPayload(tokenStr);
      return payload.exp * 1000 < Date.now();
    } catch {
      return true;
    }
  }, []);

  const clearToken = () => {
    setToken('');
    setIsLoggedIn(false);
    setUser(null);
    setSuccessMessage('');
    localStorage.removeItem('token');
  };
  const getAuthHeaders = () => {
    if (token && !isTokenExpired(token)) {
      return {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      };
    }
    clearToken();
    return {
      'Content-Type': 'application/json',
    };
  };

  // Auth handlers
  const handleLoginSuccess = async (credentialResponse) => {
    const nextToken = credentialResponse.credential;
    setToken(nextToken);
    localStorage.setItem('token', nextToken);

    try {
      const payload = parseJwtPayload(nextToken);
      setUser({
        name: payload.name || payload.sub || 'Admin User',
        email: payload.email || 'admin@system',
        picture: payload.picture || '',
        role: payload.role || 'user',
        sub: payload.sub,
      });
      setIsLoggedIn(true);
      setError('');
    } catch (err) {
      setError(`Token parse error: ${err.message}`);
    }
  };

  const handleLoginError = () => {
    setError('Login failed');
  };

  const handleLogout = () => {
    setIsLoggedIn(false);
    setUser(null);
    setToken('');
    setUserPlaylists([]);
    setExpandedPlaylists({});
    setPlaylist([]);
    setError('');
    setSuccessMessage('');
    closeSaveSongDialog();
    localStorage.removeItem('token');
    googleLogout();
  };

  // Effects
  useEffect(() => {
    const savedToken = localStorage.getItem('token');
    if (savedToken && !isTokenExpired(savedToken)) {
      setToken(savedToken);
      try {
        const payload = parseJwtPayload(savedToken);
        setUser({
          name: payload.name,
          email: payload.email,
          picture: payload.picture,
          role: payload.role || 'user',
        });
        setIsLoggedIn(true);
      } catch (err) {
        clearToken();
      }
    } else {
      if (savedToken) clearToken();
    }
  }, [isTokenExpired]);
  useEffect(() => {
    if (isLoggedIn && token) {
      loadUserPlaylists();
    }
  }, [isLoggedIn, token]);

  useEffect(() => {
    return () => {
      if (audioRef.current) {
        audioRef.current.pause();
      }
    };
  }, []);

  // Playlist handlers
  const loadUserPlaylists = async () => {
    if (!token || isTokenExpired(token)) return;

    try {
      const response = await fetch(`/playlists/`, {
        headers: getAuthHeaders(),
      });

      if (!response.ok) {
        if (response.status === 401) {
          setUserPlaylists([]);
          return;
        }
        throw new Error('Failed to load playlists');
      }

      const data = await response.json();
      setUserPlaylists(data);
    } catch (err) {
      console.error('Failed to load playlists', err);
    }
  };

  const toggleSavedPlaylist = (playlistId) => {
    setExpandedPlaylists((prev) => ({
      ...prev,
      [playlistId]: !prev[playlistId],
    }));
  };

  const deletePlaylist = async (playlistId) => {
    if (!token || isTokenExpired(token) || !confirm('Delete this playlist? This cannot be undone.')) return;

    try {
      const response = await fetch(`/playlists/${playlistId}`, {
        method: 'DELETE',
        headers: getAuthHeaders(),
      });

      if (!response.ok) {
        if (response.status === 401) {
          clearToken();
          return;
        }
        throw new Error('Failed to delete playlist');
      }

      setUserPlaylists(prev => prev.filter(p => p.id !== playlistId));
      setExpandedPlaylists(prev => {
        const newState = { ...prev };
        delete newState[playlistId];
        return newState;
      });
    } catch (err) {
      console.error('Delete failed:', err);
    }
  };

  // Song handlers
  const togglePlayPause = useCallback((songId, previewUrl) => {
    if (!previewUrl) return;

    if (currentSongId === songId && isPlaying) {
      audioRef.current.pause();
      setIsPlaying(false);
    } else {
      if (audioRef.current) {
        audioRef.current.pause();
      }

      const audio = new Audio(previewUrl);
      audioRef.current = audio;
      audio.play().catch((e) => console.error('Audio play failed:', e));

      setCurrentSongId(songId);
      setIsPlaying(true);

      audio.onended = () => {
        setIsPlaying(false);
        setCurrentSongId(null);
      };
    }
  }, [currentSongId, isPlaying]);

  const openSaveSongDialog = (song) => {
    if (!token || isTokenExpired(token)) {
      setError('Session expired. Please log in again.');
      clearToken();
      return;
    }

    setSelectedSong(song);
    setPlaylistTargetMode(userPlaylists.length > 0 ? 'existing' : 'new');
    setSelectedExistingPlaylistId(userPlaylists[0]?.id || '');
    setNewPlaylistName('');
    setSaveSongDialogOpen(true);
    setError('');
  };

  const closeSaveSongDialog = () => {
    setSaveSongDialogOpen(false);
    setSelectedSong(null);
    setPlaylistTargetMode(userPlaylists.length > 0 ? 'existing' : 'new');
    setSelectedExistingPlaylistId('');
    setNewPlaylistName('');
  };



  const handleSaveSong = async () => {
    if (!selectedSong) return;

    if (playlistTargetMode === 'existing' && !selectedExistingPlaylistId) {
      setError('Please select an existing playlist');
      return;
    }

    if (playlistTargetMode === 'new' && !newPlaylistName.trim()) {
      setError('Please enter a new playlist name');
      return;
    }

    try {
      setSongSaveLoading(true);
      setError('');

      const payload = {
        song: selectedSong,
        preferences: {
          genre: selectedGenre,
          mood: selectedMood,
          artist: selectedArtist,
        },
      };

      if (playlistTargetMode === 'existing') {
        payload.playlist_id = selectedExistingPlaylistId;
      } else {
        payload.playlist_name = newPlaylistName.trim();
      }

      const response = await fetch(`/playlists/save-song`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        if (response.status === 401) {
          clearToken();
          setError('Session expired. Please log in again.');
          return;
        }
        const errorData = await response.json().catch(() => null);
        throw new Error(errorData?.detail || 'Failed to save song');
      }

      const savedPlaylist = await response.json();
      await loadUserPlaylists();

      if (savedPlaylist?.id) {
        setExpandedPlaylists((prev) => ({
          ...prev,
          [savedPlaylist.id]: true,
        }));
      }

      closeSaveSongDialog();
      setSuccessMessage('Song saved successfully.');
    } catch (err) {
      setError(err.message || 'Failed to save song');
    } finally {
      setSongSaveLoading(false);
    }
  };

  const handleFindSimilarSongs = async (song) => {
    try {
      setSimilarSongsLoading(true);
      setError('');
      setSelectedBaseSong(song);
      setSimilarSongs([]);

      const params = new URLSearchParams({
        title: song.title || '',
        artist: song.artist || '',
        genre: song.genre || '',
        limit: '6',
      });

      const response = await fetch(`/similar-songs?${params.toString()}`, {
        headers: getAuthHeaders(),
      });

      if (!response.ok) {
        if (response.status === 401) {
          clearToken();
          setError('Session expired. Please log in again.');
          return;
        }
        throw new Error('Failed to load similar songs');
      }

      const data = await response.json();
      setSimilarSongs(data.similar_songs || []);
    } catch (err) {
      setError(err.message || 'Failed to load similar songs');
    } finally {
      setSimilarSongsLoading(false);
    }
  };

  // Generator handlers
  const handleGenerate = async (e) => {
    e.preventDefault();

    if (audioRef.current) {
      audioRef.current.pause();
      setCurrentSongId(null);
      setIsPlaying(false);
    }

    setLoading(true);
    setError('');
    setSuccessMessage('');
    setPlaylist([]);
    setSimilarSongs([]);
    setSelectedBaseSong(null);

    try {
      const params = new URLSearchParams();
      if (selectedGenre) params.append('genre', selectedGenre);
      if (selectedMood) params.append('mood', selectedMood);
      if (selectedArtist) params.append('artist', selectedArtist);
      params.append('limit', songCount);

      const response = await fetch(`/custom?${params}`, {
        headers: getAuthHeaders(),
      });

      if (!response.ok) {
        if (response.status === 401) {
          clearToken();
          setError('Session expired. Please log in again.');
          return;
        }
        throw new Error(`API error: ${response.status}`);
      }

      const data = await response.json();
      setPlaylist(data.playlist || []);
    } catch (err) {
      setError(err.message || 'Failed to generate playlist. Is backend running?');
    } finally {
      setLoading(false);
    }
  };

  const savePlaylist = async (currentPlaylist) => {
    if (!token || isTokenExpired(token)) {
      setError('Session expired. Please log in again.');
      clearToken();
      return;
    }

    try {
      setLoading(true);
      setError('');

      const playlistData = {
        name: `My ${selectedGenre || 'Perfect'} Playlist`,
        songs: currentPlaylist,
        preferences: {
          genre: selectedGenre,
          mood: selectedMood,
          artist: selectedArtist,
        },
      };

      const response = await fetch(`/playlists/`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify(playlistData),
      });

      if (!response.ok) {
        if (response.status === 401) {
          clearToken();
          setError('Session expired. Please log in again.');
          return;
        }
        const errorData = await response.json().catch(() => null);
        throw new Error(errorData?.detail || 'Failed to save playlist');
      }

      setSuccessMessage('Playlist saved successfully.');
      loadUserPlaylists();
    } catch (err) {
      setError(err.message || 'Failed to save playlist');
    } finally {
      setLoading(false);
    }
  };

  const preferenceSummary = [
    selectedGenre && `Genre: ${selectedGenre}`,
    selectedMood && `Mood: ${selectedMood}`,
    selectedArtist && `Artist: ${selectedArtist}`,
  ].filter(Boolean);

  const clearGeneratorFilters = () => {
    setSelectedGenre('');
    setSelectedMood('');
    setSelectedArtist('');
    setSongCount(10);
    setError('');
    setSuccessMessage('');
  };

  return (
    <BrowserRouter>
      <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
        <Routes>
          <Route path="/" element={!isLoggedIn ? (
            <AuthShell 
              error={error}
              onLoginSuccess={handleLoginSuccess}
              onLoginError={handleLoginError}
            />
          ) : (
            <div>
              <Dashboard
                user={user}
                userPlaylists={userPlaylists}
                expandedPlaylists={expandedPlaylists}
                playlist={playlist}
                preferenceSummary={preferenceSummary}
                genres={genres}
                moods={moods}
                selectedGenre={selectedGenre}
                selectedMood={selectedMood}
                selectedArtist={selectedArtist}
                songCount={songCount}
                loading={loading}
                currentSongId={currentSongId}
                isPlaying={isPlaying}
                similarSongsLoading={similarSongsLoading}
                selectedBaseSong={selectedBaseSong}
                onLogout={handleLogout}
                onRefreshPlaylists={loadUserPlaylists}
                onTogglePlaylist={toggleSavedPlaylist}
                onDeletePlaylist={deletePlaylist}
                onPlaySong={togglePlayPause}
                onGenreChange={setSelectedGenre}
                onMoodChange={setSelectedMood}
                onArtistChange={setSelectedArtist}
                onSongCountChange={setSongCount}
                onGenerate={handleGenerate}
                onClearFilters={clearGeneratorFilters}
                onSavePlaylist={savePlaylist}
                onSimilarSongs={handleFindSimilarSongs}
                onSaveSong={openSaveSongDialog}
                error={error}
                successMessage={successMessage}
                onClearSuccess={() => setSuccessMessage('')}
                togglePlayPause={togglePlayPause}
              />
              {similarSongs.length > 0 && selectedBaseSong && (
                <SimilarSongsModal
                  similarSongs={similarSongs}
                  selectedBaseSong={selectedBaseSong}
                  currentSongId={currentSongId}
                  isPlaying={isPlaying}
                  onClose={() => {
                    setSimilarSongs([]);
                    setSelectedBaseSong(null);
                  }}
                  onPlay={togglePlayPause}
                  onSave={openSaveSongDialog}
                />
              )}
              <SaveSongModal
                isOpen={saveSongDialogOpen}
                song={selectedSong}
                userPlaylists={userPlaylists}
                playlistTargetMode={playlistTargetMode}
                selectedExistingPlaylistId={selectedExistingPlaylistId}
                newPlaylistName={newPlaylistName}
                songSaveLoading={songSaveLoading}
                onClose={closeSaveSongDialog}
                onModeChange={setPlaylistTargetMode}
                onPlaylistIdChange={setSelectedExistingPlaylistId}
                onNewPlaylistNameChange={setNewPlaylistName}
                onSave={handleSaveSong}
              />
            </div>
          )} />

        </Routes>
      </GoogleOAuthProvider>
    </BrowserRouter>
  );
}

export default App;


