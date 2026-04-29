import React, { useEffect, useMemo, useState } from 'react';
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
  nlpSearchQuery,
  nlpSearchSummary,
  loading,
  currentSongId,
  isPlaying,
  similarSongsLoading,
  selectedBaseSong,
  onLogout,
  onRefreshPlaylists,
  onTogglePlaylist,
  onDeletePlaylist,
  onDeleteSongFromPlaylist,
  onPlaySong,
  onGenreChange,
  onMoodChange,
  onArtistChange,
  onSongCountChange,
  onGenerate,
  onNlpSearch,
  onNlpSearchQueryChange,
  onClearFilters,
  onSavePlaylist,
  onSimilarSongs,
  onSaveSong,
  error,
  successMessage,
  onClearSuccess,
  togglePlayPause
}) => {
  const [isMobileNavOpen, setIsMobileNavOpen] = useState(false);
  const [activeSection, setActiveSection] = useState('home');
  const [showBackToTop, setShowBackToTop] = useState(false);
  const hasActiveFilters = Boolean(selectedGenre || selectedMood || selectedArtist);

  const navItems = useMemo(
    () => [
      { id: 'home', label: 'Home' },
      { id: 'generator', label: 'Generator' },
      { id: 'library', label: 'Library' },
      { id: 'results', label: 'Results' },
    ],
    []
  );

  useEffect(() => {
    const sectionIds = navItems.map((item) => item.id);
    const sectionElements = sectionIds
      .map((id) => document.getElementById(id))
      .filter(Boolean);

    if (sectionElements.length === 0) return undefined;

    const observer = new IntersectionObserver(
      (entries) => {
        const visibleEntries = entries
          .filter((entry) => entry.isIntersecting)
          .sort((a, b) => b.intersectionRatio - a.intersectionRatio);

        if (visibleEntries.length > 0) {
          setActiveSection(visibleEntries[0].target.id);
        }
      },
      {
        rootMargin: '-30% 0px -50% 0px',
        threshold: [0.2, 0.4, 0.6, 0.8],
      }
    );

    sectionElements.forEach((element) => observer.observe(element));

    return () => {
      sectionElements.forEach((element) => observer.unobserve(element));
      observer.disconnect();
    };
  }, [navItems]);

  useEffect(() => {
    const handleScroll = () => {
      setShowBackToTop(window.scrollY > 680);
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const scrollToSection = (sectionId) => {
    const section = document.getElementById(sectionId);
    if (section) {
      section.scrollIntoView({ behavior: 'smooth', block: 'start' });
      setIsMobileNavOpen(false);
    }
  };

  return (
    <div className="app-shell">
      <div className="bg-orb bg-orb--one" />
      <div className="bg-orb bg-orb--two" />
      <div className="bg-grid" />

      <main className="dashboard">
        <header className="top-nav glass-panel" id="home">
          <div className="top-nav__brand">
            <p className="top-nav__title">Music Playlist Generator</p>
            <p className="top-nav__subtitle">Create, preview, and organize faster</p>
          </div>

          <button
            type="button"
            className="btn btn-ghost btn-small top-nav__toggle"
            onClick={() => setIsMobileNavOpen((prev) => !prev)}
            aria-expanded={isMobileNavOpen}
            aria-controls="dashboard-nav"
          >
            Menu
          </button>

          <nav
            id="dashboard-nav"
            className={`top-nav__links ${isMobileNavOpen ? 'is-open' : ''}`}
            aria-label="Dashboard sections"
          >
            {navItems.map((item) => (
              <button
                key={item.id}
                type="button"
                className={`top-nav__link ${activeSection === item.id ? 'is-active' : ''}`}
                onClick={() => scrollToSection(item.id)}
              >
                {item.label}
              </button>
            ))}
            <button onClick={onLogout} className="btn btn-secondary btn-small top-nav__logout">
              Logout
            </button>
          </nav>
        </header>

        <section className="hero-panel glass-panel">
          <div className="hero-panel__content">
            <div className="hero-panel__top">
              <span className="eyebrow">Your music workspace</span>
              <div className="hero-panel__quick-actions">
                <button type="button" onClick={() => scrollToSection('generator')} className="btn btn-ghost btn-small">
                  New mix
                </button>
                <button type="button" onClick={() => scrollToSection('results')} className="btn btn-ghost btn-small">
                  View results
                </button>
              </div>
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
        {successMessage && (
          <div className="status-banner status-banner--success">
            <span>{successMessage}</span>
            <button type="button" className="btn btn-ghost btn-small" onClick={onClearSuccess}>
              Dismiss
            </button>
          </div>
        )}

        <section className="dashboard-grid">
          <aside className="dashboard-sidebar" id="generator">
            <div className="glass-panel panel-section section-anchor">
              <div className="panel-header">
                <div>
                  <span className="eyebrow">Generator</span>
                  <h2>Playlist settings</h2>
                </div>
              </div>

              <form onSubmit={onNlpSearch} className="nlp-search-form">
                <label htmlFor="nlp-search">Search with natural language</label>
                <div className="nlp-search-row">
                  <input
                    id="nlp-search"
                    type="search"
                    value={nlpSearchQuery}
                    onChange={(e) => onNlpSearchQueryChange(e.target.value)}
                    placeholder="sad classical songs by Adele"
                  />
                  <button type="submit" disabled={loading || !nlpSearchQuery.trim()} className="btn btn-primary">
                    Search
                  </button>
                </div>
                {nlpSearchSummary && (
                  <div className="nlp-search-summary">
                    {nlpSearchSummary.genre && <span>Genre: {nlpSearchSummary.genre}</span>}
                    {nlpSearchSummary.mood && <span>Mood: {nlpSearchSummary.mood}</span>}
                    {nlpSearchSummary.artist && <span>Artist: {nlpSearchSummary.artist}</span>}
                  </div>
                )}
              </form>

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
                      min="1"
                      max="50"
                      step="1"
                      value={songCount}
                      onChange={(e) => onSongCountChange(Number(e.target.value))}
                    />
                    <div className="range-value">{songCount}</div>
                  </div>
                  <p className="form-helper-copy">Tip: 1 song is great for testing; 10-20 songs is best for playlist exploration.</p>
                </div>

                <div className="generator-actions">
                  <button type="submit" disabled={loading} className="btn btn-primary btn-block">
                    {loading ? 'Generating playlist...' : `Generate playlist (${songCount} songs)`}
                  </button>
                  <button
                    type="button"
                    className="btn btn-ghost btn-block"
                    onClick={onClearFilters}
                    disabled={loading || !hasActiveFilters}
                  >
                    Reset filters
                  </button>
                </div>
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
            <div className="glass-panel panel-section section-anchor" id="library">
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
                      currentSongId={currentSongId}
                      isPlaying={isPlaying}
                      onToggle={onTogglePlaylist}
                      onDelete={onDeletePlaylist}
                      onDeleteSong={onDeleteSongFromPlaylist}
                      onPlay={togglePlayPause}
                    />
                  ))}
                </div>
              )}
            </div>

            <div className="glass-panel panel-section section-anchor" id="results">
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

              {playlist.length > 0 && (
                <div className="results-toolbar">
                  <div className="results-toolbar__count">
                    <strong>{playlist.length}</strong>
                    <span>tracks generated</span>
                  </div>
                  <div className="results-toolbar__meta">
                    {hasActiveFilters ? (
                      <span>Based on your selected filters</span>
                    ) : (
                      <span>Based on a broad discovery mix</span>
                    )}
                  </div>
                  <button
                    type="button"
                    className="btn btn-ghost btn-small"
                    onClick={() => scrollToSection('generator')}
                  >
                    Refine filters
                  </button>
                </div>
              )}

              {playlist.length === 0 ? (
                <div className="empty-state empty-state--large">
                  <div className="empty-state__icon">✨</div>
                  <h3>Your next mix starts here</h3>
                  <p>
                    Choose a mood or genre, generate recommendations, then preview and save
                    the tracks you love.
                  </p>
                  <button
                    type="button"
                    className="btn btn-primary"
                    onClick={() => scrollToSection('generator')}
                  >
                    Start generating
                  </button>
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

        {showBackToTop && (
          <button
            type="button"
            className="back-to-top"
            onClick={() => scrollToSection('home')}
            aria-label="Back to top"
          >
            Top
          </button>
        )}
      </main>
    </div>
  );
};

export default Dashboard;

