import React from 'react';

const SongCard = ({
  song,
  index,
  currentSongId,
  isPlaying,
  onPlay,
  onSimilar,
  onSave,
  similarSongsLoading,
  selectedBaseSong,
  hideSimilar = false,
  saveButtonClass = 'btn btn-ghost btn-small'
}) => {
  const defaultArtwork = 'https://via.placeholder.com/1200x1200/0f172a/e2e8f0?text=Music';
  
  const togglePreview = (e) => {
    e.stopPropagation();
    onPlay(index, song.preview_url);
  };

  const isLoadingSimilar = similarSongsLoading && 
    selectedBaseSong?.title === song.title && 
    selectedBaseSong?.artist === song.artist;

  return (
    <article className="song-card">
      <div className="song-card__artwork-wrap">
        <img
          src={song.artwork || defaultArtwork}
          alt={song.title}
          className="song-card__artwork"
        />
        <button
          type="button"
          className="play-button"
          onClick={togglePreview}
          title="Preview this song"
          disabled={!song.preview_url}
        >
          {currentSongId === index && isPlaying ? '⏸' : '▶'}
        </button>
      </div>

      <div className="song-card__body">
        <div className="song-card__content">
          <div>
            <h3 className="line-clamp-1">{song.title}</h3>
            <p className="song-card__artist">{song.artist}</p>
            <p className="song-card__album line-clamp-1">{song.album}</p>
          </div>

          {song.explanation && (
            <div className="song-card__insights">
              <p className="song-card__explanation">{song.explanation}</p>
            </div>
          )}
        </div>

        <div className="song-card__footer">
          <span className="song-tag">
            {song.mood || song.genre || 'Curated'}
          </span>
          <div className="song-card__actions">
            {!hideSimilar && onSimilar && (
              <button
                type="button"
                className="btn btn-ghost btn-small"
                onClick={(e) => {
                  e.stopPropagation();
                  onSimilar(song);
                }}
                disabled={isLoadingSimilar}
              >
                {isLoadingSimilar ? '🔍 Loading...' : '🔍 Similar'}
              </button>
            )}
            <button
              type="button"
              className={saveButtonClass}
              onClick={(e) => {
                e.stopPropagation();
                onSave(song);
              }}
            >
              💾 Save
            </button>
          </div>
        </div>
      </div>
    </article>
  );
};

export default SongCard;

