const ITUNES_ARTWORK_SIZE_PATTERN = /\/\d+x\d+bb\.(jpg|jpeg|png|webp)(\?.*)?$/i;

export const getHighQualityArtwork = (artworkUrl, size = 1200) => {
  if (!artworkUrl) {
    return artworkUrl;
  }

  return artworkUrl.replace(
    ITUNES_ARTWORK_SIZE_PATTERN,
    `/${size}x${size}bb.$1$2`
  );
};

