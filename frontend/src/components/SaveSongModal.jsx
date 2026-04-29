import React from 'react';
import { getHighQualityArtwork } from '../utils/artwork';

const SaveSongModal = ({
  isOpen,
  song,
  userPlaylists,
  playlistTargetMode,
  selectedExistingPlaylistId,
  newPlaylistName,
  songSaveLoading,
  onClose,
  onModeChange,
  onPlaylistIdChange,
  onNewPlaylistNameChange,
  onSave
}) => {
  if (!isOpen || !song) return null;

  const defaultArtwork = 'https://via.placeholder.com/1200x1200/0f172a/e2e8f0?text=Music';
  const artwork = getHighQualityArtwork(song.artwork) || defaultArtwork;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        className="save-song-modal cyber-save-modal"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-labelledby="save-song-title"
      >
        <div className="cyber-save-header">
          <div className="cyber-save-icon">💾</div>
          <div>
            <span className="eyebrow cyber-label">Quick Save</span>
            <h3 id="save-song-title">Add to Collection</h3>
            <p>
              Save <strong>{song.title}</strong> by {song.artist}
            </p>
          </div>
          <button
            type="button"
            className="btn btn-ghost btn-small cyber-close"
            onClick={onClose}
            aria-label="Close save dialog"
          >
            ✕
          </button>
        </div>

        <div className="cyber-save-song-preview">
          <div className="song-artwork-large">
            <img
              src={artwork}
              alt={`${song.title} artwork`}
              className="song-artwork-circle"
              decoding="async"
            />
          </div>
          <div className="cyber-song-meta">
            <h4>{song.title}</h4>
            <p className="artist-name">{song.artist}</p>
            <span className="cyber-tag gradient-text">
              {song.mood || song.genre || 'Recommended'}
            </span>
          </div>
        </div>

        <div className="cyber-save-modes">
          <button
            type="button"
            className={`mode-pill ${playlistTargetMode === 'existing' ? 'active-glow' : ''}`}
            onClick={() => onModeChange('existing')}
            disabled={userPlaylists.length === 0}
            aria-pressed={playlistTargetMode === 'existing'}
          >
            <span>📂</span> Existing Playlist
            {userPlaylists.length > 0 && <span>({userPlaylists.length})</span>}
          </button>
          <button
            type="button"
            className={`mode-pill ${playlistTargetMode === 'new' ? 'active-glow' : ''}`}
            onClick={() => onModeChange('new')}
            aria-pressed={playlistTargetMode === 'new'}
          >
            <span>➕</span> New Playlist
          </button>
        </div>

        {playlistTargetMode === 'existing' ? (
          <div className="cyber-form-group">
            <label>Choose Playlist</label>
            <div className="playlist-select-wrapper">
              <select
                value={selectedExistingPlaylistId}
                onChange={(e) => onPlaylistIdChange(e.target.value)}
                disabled={userPlaylists.length === 0}
                aria-label="Select existing playlist"
              >
                {userPlaylists.length === 0 ? (
                  <option value="">No playlists yet</option>
                ) : (
                  userPlaylists.map((playlist) => (
                    <option key={playlist.id} value={playlist.id}>
                      {playlist.name} ({playlist.songs?.length || 0} songs)
                    </option>
                  ))
                )}
              </select>
            </div>
          </div>
        ) : (
          <div className="cyber-form-group">
            <label>New Playlist Name</label>
            <input
              type="text"
              value={newPlaylistName}
              onChange={(e) => onNewPlaylistNameChange(e.target.value)}
              placeholder="My Chill Vibes Mix"
              maxLength={50}
            />
          </div>
        )}

        <div className="cyber-save-actions">
          <button 
            type="button" 
            className="btn btn-secondary cyber-btn" 
            onClick={onClose}
          >
            Cancel
          </button>
          <button
            type="button"
            className="btn btn-primary cyber-save-btn gradient-btn"
            onClick={onSave}
            disabled={songSaveLoading || (playlistTargetMode === 'existing' && !selectedExistingPlaylistId) || (playlistTargetMode === 'new' && !newPlaylistName.trim())}
          >
            {songSaveLoading ? (
              <>
                <span className="loading-spinner"></span>
                Saving...
              </>
            ) : (
              'Save Track ✨'
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default SaveSongModal;

