import React from 'react';
import SongCard from './SongCard';

const SimilarSongsModal = ({
  similarSongs,
  selectedBaseSong,
  currentSongId,
  isPlaying,
  onClose,
  onPlay,
  onSave
}) => {
  if (!similarSongs || similarSongs.length === 0) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        className="similar-songs-modal glass-panel"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-labelledby="similar-songs-title"
      >
        <div className="similar-songs-modal__header">
          <div>
            <span className="eyebrow">Song Similarity</span>
            <h3 id="similar-songs-title">Similar to "{selectedBaseSong?.title}"</h3>
            <p className="similar-songs-modal__subtitle">Recommended because title, artist, and genre match the selected track.</p>
          </div>

          <button
            type="button"
            className="btn btn-ghost btn-small modal-close"
            onClick={onClose}
            aria-label="Close similar songs modal"
          >
            ✕
          </button>
        </div>

        <div className="similar-songs-modal__body">
          <div className="similar-songs-grid">
            {similarSongs.map((song, index) => (
              <SongCard
                key={`similar-${index}`}
                song={song}
                index={`similar-${index}`}
                currentSongId={currentSongId}
                isPlaying={isPlaying}
                onPlay={onPlay}
                onSave={onSave}
                similarSongsLoading={false}
                selectedBaseSong={null}
                hideSimilar
                saveButtonClass="btn btn-primary btn-small"
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default SimilarSongsModal;

