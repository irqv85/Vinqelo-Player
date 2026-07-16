PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS albums (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    album_artist TEXT NOT NULL,
    folder_path TEXT NOT NULL UNIQUE,
    cover_path TEXT,
    year INTEGER,
    is_compilation INTEGER NOT NULL DEFAULT 0 CHECK (is_compilation IN (0, 1)),
    date_added TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tracks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    album_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    track_artist TEXT,
    track_number INTEGER,
    file_path TEXT NOT NULL UNIQUE,
    duration REAL NOT NULL DEFAULT 0,
    file_format TEXT NOT NULL,
    FOREIGN KEY (album_id) REFERENCES albums(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_albums_title ON albums(title COLLATE NOCASE);
CREATE INDEX IF NOT EXISTS idx_albums_compilation ON albums(is_compilation);
CREATE INDEX IF NOT EXISTS idx_tracks_album_id ON tracks(album_id);
CREATE INDEX IF NOT EXISTS idx_tracks_track_number ON tracks(album_id, track_number);

