import React, { useState, useRef, useCallback, useEffect } from 'react';
import { GoogleOAuthProvider, GoogleLogin, googleLogout } from '@react-oauth/google';
import './App.css';

const API_BASE = 'http://127.0.0.1:8000';
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
  { id: 'romantic', name: 'Romantic', emoji: '💜' },
  { id: 'sad', name: 'Sad', emoji: '🌧️' },
  { id: 'focus', name: 'Focus', emoji: '🎯' },
  { id: 'party', name: 'Party', emoji: '🎉' },
  { id: 'workout', name: 'Workout', emoji: '💪' },
  { id: 'chill', name: 'Chill', emoji: '😌' },
];

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [user, setUser] = useState(null);
  const [token, setToken] = useState('');
  const [selectedGenre, setSelectedGenre] = useState('');
  const [selectedMood, setSelectedMood] = useState('');
  const [selectedArtist, setSelectedArtist] = useState('');
  const [songCount, setSongCount] = useState(10);
  const [playlist, setPlaylist] = useState([]);
  const [userPlaylists, setUserPlaylists] = useState([]);
  const [expandedPlaylists, setExpandedPlaylists] = useState({});
  const [loading, setLoading] = useState(false);
  const [songSaveLoading, setSongSaveLoading] = useState(false);
  const [error, setError] = useState('');
  const [saveSongDialogOpen, setSaveSongDialogOpen] = useState(false);
  const [selectedSong, setSelectedSong] = useState(null);
  const [playlistTargetMode, setPlaylistTargetMode] = useState('existing');
  const [selectedExistingPlaylistId, setSelectedExistingPlaylistId] = useState('');
  const [newPlaylistName, setNewPlaylistName] = useState('');

  const audioRef = useRef(null);
  const [currentSongId, setCurrentSongId] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);

  // Check if token is expired
  const isTokenExpired = (tokenStr) => {
    try {
      const payload = JSON.parse(atob(tokenStr.split('.')[1]));
      return payload.exp * 1000 < Date.now();
    } catch {
      return true;
    }
  };

  // Clear invalid token
  const clearToken = () => {
    setToken('');
    setIsLoggedIn(false);
    setUser(null);
    localStorage.removeItem('token');
  };

  useEffect(() => {
    const savedToken = localStorage.getItem('token');
    if (savedToken && !isTokenExpired(savedToken)) {
      setToken(savedToken);
      try {
        const payload = JSON.parse(atob(savedToken.split('.')[1]));
        setUser({
          name: payload.name,
          email: payload.email,
          picture: payload.picture,
        });
        setIsLoggedIn(true);
      } catch (err) {
        clearToken();
      }
    } else {
      if (savedToken) clearToken();
    }
  }, []);

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

  const handleLoginSuccess = async (credentialResponse) => {
    const nextToken = credentialResponse.credential;
    setToken(nextToken);
    localStorage.setItem('token', nextToken);

    try {
      const payload = JSON.parse(atob(nextToken.split('.')[1]));
      setUser({
        name: payload.name,
        email: payload.email,
        picture: payload.picture,
      });
      setIsLoggedIn(true);
      setError('');
    } catch (err) {
      setError('Login failed');
    }
  };

  const handleLoginError = () => {
    setError('Login failed');
  };

  const closeSaveSongDialog = () => {
    setSaveSongDialogOpen(false);
    setSelectedSong(null);
    setPlaylistTargetMode(userPlaylists.length > 0 ? 'existing' : 'new');
    setSelectedExistingPlaylistId('');
    setNewPlaylistName('');
  };

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

  const toggleSavedPlaylist = (playlistId) => {
    setExpandedPlaylists((prev) => ({
      ...prev,
      [playlistId]: !prev[playlistId],
    }));
  };

  const handleLogout = () => {
    setIsLoggedIn(false);
    setUser(null);
    setToken('');
    setUserPlaylists([]);
    setExpandedPlaylists({});
    setPlaylist([]);
    setError('');
    closeSaveSongDialog();
    localStorage.removeItem('token');
    googleLogout();
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

  const handleGenerate = async (e) => {
    e.preventDefault();

    if (audioRef.current) {
      audioRef.current.pause();
      setCurrentSongId(null);
      setIsPlaying(false);
    }

    setLoading(true);
    setError('');
    setPlaylist([]);

    try {
      const params = new URLSearchParams();
      if (selectedGenre) params.append('genre', selectedGenre);
      if (selectedMood) params.append('mood', selectedMood);
      if (selectedArtist) params.append('artist', selectedArtist);
      params.append('limit', songCount);

      const response = await fetch(`${API_BASE}/custom?${params}`, {
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

      const response = await fetch(`${API_BASE}/playlists/`, {
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

      alert('Playlist saved successfully!');
      loadUserPlaylists();
    } catch (err) {
      setError(err.message || 'Failed to save playlist');
    } finally {
      setLoading(false);
    }
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

      const response = await fetch(`${API_BASE}/playlists/save-song`, {
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
    } catch (err) {
      setError(err.message || 'Failed to save song');
    } finally {
      setSongSaveLoading(false);
    }
  };

  const loadUserPlaylists = async () => {
    if (!token || isTokenExpired(token)) {
      clearToken();
      return;
    }

    try {
      const response = await fetch(`${API_BASE}/playlists`, {
        headers: getAuthHeaders(),
      });

      if (!response.ok) {
        if (response.status === 401) {
          clearToken();
          return;
        }
        throw new Error('Failed to load playlists');
      }

      const data = await response.json();
      setUserPlaylists(data);
    } catch (err) {
      console.error('Failed to load playlists');
    }
  };

  const deletePlaylist = async (playlistId) => {
    if (!token || isTokenExpired(token) || !confirm('Delete this playlist? This cannot be undone.')) return;

    try {
      const response = await fetch(`${API_BASE}/playlists/${playlistId}`, {
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

  const defaultArtwork = 'https://via.placeholder.com/1200x1200/0f172a/e2e8f0?text=Music';
  const preferenceSummary = [
    selectedGenre && `Genre: ${selectedGenre}`,
    selectedMood && `Mood: ${selectedMood}`,
    selectedArtist && `Artist: ${selectedArtist}`,
  ].filter(Boolean);

  if (!isLoggedIn) {
    return (
      <div className="app-shell auth-shell">
        <div className="bg-orb bg-orb--one" />
        <div className="bg-orb bg-orb--two" />
        <div className="bg-grid" />

        <main className="auth-layout">
          <section className="auth-copy">
            <span className="eyebrow">AI music curation</span>
            <h1>Build beautiful playlists in seconds.</h1>
            <p>
              Discover tracks by mood, genre, and favorite artist, then save your
              playlists in one polished workspace.
            </p>

            <div className="hero-metrics">
              <div className="metric-card">
                <strong>12+</strong>
                <span>Genres</span>
              </div>
              <div className="metric-card">
                <strong>9</strong>
                <span>Moods</span>
              </div>
              <div className="metric-card">
                <strong>50</strong>
                <span>Tracks max</span>
              </div>
            </div>
          </section>

          <section className="auth-card">
            <div className="auth-card__icon">🎧</div>
            <span className="eyebrow">Welcome back</span>
            <h2>Sign in to your music space</h2>
            <p>
              Save playlists, refresh your collection, and keep your perfect mixes
              organized in one place.
            </p>

            <div className="auth-card__login">
              <GoogleLogin
                onSuccess={handleLoginSuccess}
                onError={handleLoginError}
                theme="filled_blue"
                size="large"
                text="signin_with"
                shape="pill"
                width="320"
              />
            </div>

            {error && <div className="status-banner status-banner--error">{error}</div>}

            <div className="auth-card__features">
              <div>✨ Smart recommendations</div>
              <div>💾 Saved playlists</div>
              <div>▶️ Instant previews</div>
            </div>
          </section>
        </main>
      </div>
    );
  }

  return (
    <div className="app-shell">
      <div className="bg-orb bg-orb--one" />
      <div className="bg-orb bg-orb--two" />
      <div className="bg-grid" />

      <main className="dashboard">
        <section className="hero-panel glass-panel">
          <div className="hero-panel__content">
            <div className="hero-panel__top">
              <span className="eyebrow">Your music workspace</span>
              <button onClick={handleLogout} className="btn btn-secondary">
                Logout
              </button>
            </div>

            <div className="hero-panel__headline">
              <div className="hero-user">
                <img src={user.picture} alt={user.name} className="hero-user__avatar" />
                <div>
                  <p className="hero-user__name">{user.name}</p>
                  <p className="hero-user__email">{user.email}</p>
                </div>
              </div>

              <div>
                <h1>Create a playlist that matches your vibe.</h1>
                <p>
                  Fine-tune your next mix with genre, mood, artist, and track count.
                  Preview songs instantly and save the best results to your collection.
                </p>
              </div>
            </div>

            <div className="hero-stats">
              <div className="stat-card">
                <span className="stat-card__label">Saved playlists</span>
                <strong>{userPlaylists.length}</strong>
              </div>
              <div className="stat-card">
                <span className="stat-card__label">Current result</span>
                <strong>{playlist.length} songs</strong>
              </div>
              <div className="stat-card">
                <span className="stat-card__label">Selected mood</span>
                <strong>{selectedMood || 'Any'}</strong>
              </div>
            </div>
          </div>
        </section>

        {error && <div className="status-banner status-banner--error">{error}</div>}

        <section className="dashboard-grid">
          <aside className="dashboard-sidebar">
            <div className="glass-panel panel-section">
              <div className="panel-header">
                <div>
                  <span className="eyebrow">Generator</span>
                  <h2>Playlist settings</h2>
                </div>
              </div>

              <form onSubmit={handleGenerate} className="generator-form">
                <div className="form-group">
                  <label>Genre</label>
                  <select
                    value={selectedGenre}
                    onChange={(e) => setSelectedGenre(e.target.value)}
                  >
                    <option value="">Any Genre</option>
                    {genres.map((genre) => (
                      <option key={genre.id} value={genre.id}>
                        {genre.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="form-group">
                  <label>Mood</label>
                  <select
                    value={selectedMood}
                    onChange={(e) => setSelectedMood(e.target.value)}
                  >
                    <option value="">Any Mood</option>
                    {moods.map((mood) => (
                      <option key={mood.id} value={mood.id}>
                        {mood.emoji} {mood.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="form-group">
                  <label>Artist</label>
                  <input
                    type="text"
                    value={selectedArtist}
                    onChange={(e) => setSelectedArtist(e.target.value)}
                    placeholder="Taylor Swift, Drake..."
                  />
                </div>

                <div className="form-group">
                  <label>Number of songs</label>
                  <div className="range-wrap">
                    <input
                      type="range"
                      min="5"
                      max="50"
                      step="5"
                      value={songCount}
                      onChange={(e) => setSongCount(Number(e.target.value))}
                    />
                    <div className="range-value">{songCount}</div>
                  </div>
                </div>

                <button type="submit" disabled={loading} className="btn btn-primary btn-block">
                  {loading ? 'Generating playlist...' : `Generate playlist (${songCount} songs)`}
                </button>
              </form>
            </div>

            <div className="glass-panel panel-section">
              <div className="panel-header">
                <div>
                  <span className="eyebrow">Overview</span>
                  <h2>Current filters</h2>
                </div>
              </div>

              {preferenceSummary.length > 0 ? (
                <div className="chip-list">
                  {preferenceSummary.map((item) => (
                    <span key={item} className="chip">
                      {item}
                    </span>
                  ))}
                </div>
              ) : (
                <p className="muted-copy">
                  No filters selected yet. Choose any combination and generate a new mix.
                </p>
              )}
            </div>
          </aside>

          <section className="dashboard-main">
            <div className="glass-panel panel-section">
              <div className="panel-header panel-header--split">
                <div>
                  <span className="eyebrow">Library</span>
                  <h2>Your playlists</h2>
                </div>
                <button onClick={loadUserPlaylists} className="btn btn-ghost">
                  Refresh
                </button>
              </div>

              {userPlaylists.length === 0 ? (
                <div className="empty-state">
                  <div className="empty-state__icon">📚</div>
                  <h3>No saved playlists yet</h3>
                  <p>Generate a playlist and save it to build your personal collection.</p>
                </div>
              ) : (
                <div className="saved-playlists saved-playlists--stacked">
                  {userPlaylists.map((savedPlaylist) => {
                    const isExpanded = !!expandedPlaylists[savedPlaylist.id];

                    return (
                      <article key={savedPlaylist.id} className="saved-playlist-card saved-playlist-card--expandable">
                        <button
                          type="button"
                          className="saved-playlist-toggle"
                          onClick={() => toggleSavedPlaylist(savedPlaylist.id)}
                        >
                          <div className="saved-playlist-card__top">
                            <span className="saved-playlist-card__badge">Saved</span>
                            <span className="saved-playlist-card__count">
                              {savedPlaylist.songs.length} songs
                            </span>
                          </div>

                          <div className="saved-playlist-card__header">
                            <div>
                              <h3>{savedPlaylist.name}</h3>
                              <div className="chip-list">
                                <span className="chip">
                                  {savedPlaylist.preferences?.genre || 'Mixed genre'}
                                </span>
                                <span className="chip">
                                  {savedPlaylist.preferences?.mood || 'Any mood'}
                                </span>
                              </div>
                            </div>

                            <div className="saved-playlist-actions">
                              <button
                                type="button"
                                className="btn btn-ghost btn-small"
                                onClick={() => toggleSavedPlaylist(savedPlaylist.id)}
                                title="Toggle playlist"
                              >
                                {isExpanded ? 'Collapse' : 'Expand'}
                              </button>
                              <button
                                type="button"
                                className="btn btn-danger btn-small"
                                onClick={() => deletePlaylist(savedPlaylist.id)}
                                title="Delete playlist"
                              >
                                Delete
                              </button>
                            </div>
                          </div>

                        </button>

                        {isExpanded && (
                          <div className="saved-playlist-songs">
                            {savedPlaylist.songs.length === 0 ? (
                              <p className="muted-copy">No songs saved in this playlist yet.</p>
                            ) : (
                              savedPlaylist.songs.map((song, index) => {
                                const savedSongKey = `saved-${savedPlaylist.id}-${index}`;

                                return (
                                  <div key={savedSongKey} className="saved-song-row">
                                    <div className="saved-song-row__info">
                                      <img
                                        src={song.artwork || defaultArtwork}
                                        alt={song.title}
                                        className="saved-song-row__artwork"
                                      />
                                      <div>
                                        <h4 className="line-clamp-1">{song.title}</h4>
                                        <p className="saved-song-row__artist">{song.artist}</p>
                                        <p className="saved-song-row__album line-clamp-1">
                                          {song.album}
                                        </p>
                                      </div>
                                    </div>

                                    <button
                                      type="button"
                                      className="btn btn-ghost btn-small saved-song-row__play"
                                      onClick={() => togglePlayPause(savedSongKey, song.preview_url)}
                                      disabled={!song.preview_url}
                                    >
                                      {!song.preview_url
                                        ? 'No preview'
                                        : currentSongId === savedSongKey && isPlaying
                                          ? 'Pause'
                                          : 'Play'}
                                    </button>
                                  </div>
                                );
                              })
                            )}
                          </div>
                        )}
                      </article>
                    );
                  })}
                </div>
              )}
            </div>

            <div className="glass-panel panel-section">
              <div className="panel-header panel-header--split">
                <div>
                  <span className="eyebrow">Generated playlist</span>
                  <h2>Recommended tracks</h2>
                </div>
                {playlist.length > 0 && (
                  <button onClick={() => savePlaylist(playlist)} className="btn btn-primary">
                    Save to my playlist
                  </button>
                )}
              </div>

              {playlist.length === 0 ? (
                <div className="empty-state empty-state--large">
                  <div className="empty-state__icon">✨</div>
                  <h3>Your next mix starts here</h3>
                  <p>
                    Choose a mood or genre, generate recommendations, then preview and save
                    the tracks you love.
                  </p>
                </div>
              ) : (
                <div className="song-grid">
                  {playlist.map((song, index) => (
                    <article key={`${song.id}-${index}`} className="song-card">
                      <div className="song-card__artwork-wrap">
                        <img
                          src={song.artwork || defaultArtwork}
                          alt={song.title}
                          className="song-card__artwork"
                        />
                        <button
                          type="button"
                          className="play-button"
                          onClick={(e) => {
                            e.stopPropagation();
                            togglePlayPause(index, song.preview_url);
                          }}
                          title="Preview this song"
                        >
                          {currentSongId === index && isPlaying ? '⏸' : '▶'}
                        </button>
                      </div>

                      <div className="song-card__body">
                        <div>
                          <h3 className="line-clamp-1">{song.title}</h3>
                          <p className="song-card__artist">{song.artist}</p>
                          <p className="song-card__album line-clamp-1">{song.album}</p>
                        </div>

                        <div className="song-card__footer">
                          <span className="song-tag">
                            {selectedMood || selectedGenre || 'Curated'}
                          </span>
                          <button
                            type="button"
                            className="btn btn-ghost btn-small"
                            onClick={() => openSaveSongDialog(song)}
                          >
                            Save
                          </button>
                        </div>
                      </div>
                    </article>
                  ))}
                </div>
              )}
            </div>
          </section>
        </section>
      </main>

      {saveSongDialogOpen && selectedSong && (
        <div className="modal-overlay" onClick={closeSaveSongDialog}>
          <div
            className="save-song-modal glass-panel"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="save-song-modal__header">
              <div>
                <span className="eyebrow">Save track</span>
                <h3>Add this song to your collection</h3>
                <p>
                  Choose an existing playlist or create a new one for
                  <strong> {selectedSong.title}</strong>.
                </p>
              </div>

              <button
                type="button"
                className="btn btn-ghost btn-small modal-close"
                onClick={closeSaveSongDialog}
              >
                ✕
              </button>
            </div>

            <div className="save-song-modal__song">
              <img
                src={selectedSong.artwork || defaultArtwork}
                alt={selectedSong.title}
                className="save-song-modal__artwork"
              />
              <div>
                <h4>{selectedSong.title}</h4>
                <p>{selectedSong.artist}</p>
                <span className="song-tag">
                  {selectedMood || selectedGenre || 'Curated track'}
                </span>
              </div>
            </div>

            <div className="save-song-modal__modes">
              <button
                type="button"
                className={`mode-chip ${playlistTargetMode === 'existing' ? 'is-active' : ''}`}
                onClick={() => setPlaylistTargetMode('existing')}
                disabled={userPlaylists.length === 0}
              >
                Existing playlist
              </button>
              <button
                type="button"
                className={`mode-chip ${playlistTargetMode === 'new' ? 'is-active' : ''}`}
                onClick={() => setPlaylistTargetMode('new')}
              >
                New playlist
              </button>
            </div>

            {playlistTargetMode === 'existing' ? (
              <div className="form-group">
                <label>Select playlist</label>
                <select
                  value={selectedExistingPlaylistId}
                  onChange={(e) => setSelectedExistingPlaylistId(e.target.value)}
                  disabled={userPlaylists.length === 0}
                >
                  {userPlaylists.length === 0 ? (
                    <option value="">No playlists available</option>
                  ) : (
                    userPlaylists.map((savedPlaylist) => (
                      <option key={savedPlaylist.id} value={savedPlaylist.id}>
                        {savedPlaylist.name} ({savedPlaylist.songs.length} songs)
                      </option>
                    ))
                  )}
                </select>
              </div>
            ) : (
              <div className="form-group">
                <label>New playlist name</label>
                <input
                  type="text"
                  value={newPlaylistName}
                  onChange={(e) => setNewPlaylistName(e.target.value)}
                  placeholder="Late Night Favorites"
                />
              </div>
            )}

            <div className="save-song-modal__actions">
              <button type="button" className="btn btn-secondary" onClick={closeSaveSongDialog}>
                Cancel
              </button>
              <button
                type="button"
                className="btn btn-primary"
                onClick={handleSaveSong}
                disabled={songSaveLoading || (playlistTargetMode === 'existing' && userPlaylists.length === 0)}
              >
                {songSaveLoading ? 'Saving...' : 'Save song'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function Root() {
  return (
    <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
      <App />
    </GoogleOAuthProvider>
  );
}

export default Root;
