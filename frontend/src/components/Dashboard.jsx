import React from 'react';
import PlaylistCard from './PlaylistCard';
import SongCard from './SongCard';

const Dashboard = ({
  user,
  userPlaylists,
  expandedPlaylists,
  playlist,
  preferenceSummary,
  genres,
  moods,
  selectedGenre,
  selectedMood,
  selectedArtist,
  songCount,
  loading,
  currentSongId,
  isPlaying,
  similarSongsLoading,
  selectedBaseSong,
  onLogout,
  onRefreshPlaylists,
  onTogglePlaylist,
  onDeletePlaylist,
  onPlaySong,
  onGenreChange,
  onMoodChange,
  onArtistChange,
  onSongCountChange,
  onGenerate,
  onSavePlaylist,
  onSimilarSongs,
  onSaveSong,
  error,
  togglePlayPause
}) => {
  const defaultArtwork = 'https://via.placeholder.com/1200x1200/0f172a/e2e8f0?text=Music';

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
              <button onClick={onLogout} className="btn btn-secondary">
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

              <form onSubmit={onGenerate} className="generator-form">
                <div className="form-group">
                  <label>Genre</label>
                  <select
                    value={selectedGenre}
                    onChange={(e) => onGenreChange(e.target.value)}
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
                    onChange={(e) => onMoodChange(e.target.value)}
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
                    onChange={(e) => onArtistChange(e.target.value)}
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
                      onChange={(e) => onSongCountChange(Number(e.target.value))}
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
                <button onClick={onRefreshPlaylists} className="btn btn-ghost">
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
                  {userPlaylists.map((savedPlaylist) => (
                    <PlaylistCard
                      key={savedPlaylist.id}
                      playlist={savedPlaylist}
                      isExpanded={!!expandedPlaylists[savedPlaylist.id]}
                      onToggle={onTogglePlaylist}
                      onDelete={onDeletePlaylist}
                      onPlay={togglePlayPause}
                    />
                  ))}
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
                  <button onClick={() => onSavePlaylist(playlist)} className="btn btn-primary">
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
                    <SongCard
                      key={`${song.id}-${index}`}
                      song={song}
                      index={index}
                      currentSongId={currentSongId}
                      isPlaying={isPlaying}
                      onPlay={togglePlayPause}
                      onSimilar={onSimilarSongs}
                      onSave={onSaveSong}
                      similarSongsLoading={similarSongsLoading}
                      selectedBaseSong={selectedBaseSong}
                    />
                  ))}
                </div>
              )}
            </div>
          </section>
        </section>
      </main>
    </div>
  );
};

export default Dashboard;

