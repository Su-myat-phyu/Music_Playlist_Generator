import React from 'react';

  const PlaylistCard = ({
  playlist,
  isExpanded,
  onToggle,
  onDelete,
  onPlay
}) => {
  return (
    <article className="saved-playlist-card saved-playlist-card--expandable">
      <button
        type="button"
        className="saved-playlist-toggle"
        onClick={() => onToggle(playlist.id)}
      >
        <div className="saved-playlist-card__top">
          <span className="saved-playlist-card__badge">Saved</span>
          <span className="saved-playlist-card__count">
            {playlist.songs.length} songs
          </span>
        </div>

        <div className="saved-playlist-card__header">
          <div>
            <h3>{playlist.name}</h3>
            <div className="chip-list">
              <span className="chip">
                {playlist.preferences?.genre || 'Mixed genre'}
              </span>
              <span className="chip">
                {playlist.preferences?.mood || 'Any mood'}
              </span>
            </div>
          </div>

          <div className="saved-playlist-actions">
            <button
              type="button"
              className="btn btn-ghost btn-small"
              onClick={(e) => {
                e.stopPropagation();
                onToggle(playlist.id);
              }}
              title="Toggle playlist"
            >
              {isExpanded ? 'Collapse' : 'Expand'}
            </button>
            <button
              type="button"
              className="btn btn-danger btn-small"
              onClick={(e) => {
                e.stopPropagation();
                onDelete(playlist.id);
              }}
              title="Delete playlist"
            >
              Delete
            </button>
          </div>
        </div>
      </button>

      {isExpanded && (
        <div className="saved-playlist-songs">
          {playlist.songs.length === 0 ? (
            <p className="muted-copy">No songs saved in this playlist yet.</p>
          ) : (
            playlist.songs.map((song, index) => {
              const savedSongKey = `saved-${playlist.id}-${index}`;
              return (
                <div key={savedSongKey} className="saved-song-row">
                  <div className="saved-song-row__info">
                    <img
                      src={song.artwork || 'https://via.placeholder.com/1200x1200/0f172a/e2e8f0?text=Music'}
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
              onClick={() => onPlay(savedSongKey, song.preview_url)}
              disabled={!song.preview_url}
            >
              {!song.preview_url
                ? 'No preview'
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
};

export default PlaylistCard;

