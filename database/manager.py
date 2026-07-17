"""Conexión y operaciones de la biblioteca SQLite."""

from __future__ import annotations

import logging
import re
import sqlite3
from pathlib import Path
from typing import Any


class DatabaseManager:
    def __init__(self, database_path: Path) -> None:
        self.database_path = Path(database_path)
        self._logger = logging.getLogger(__name__)

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def initialize(self) -> None:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        schema = Path(__file__).with_name("schema.sql").read_text(encoding="utf-8")
        connection = self.connect()
        try:
            # Migración conservadora para bibliotecas creadas por la versión inicial.
            columns = {
                row["name"]
                for row in connection.execute("PRAGMA table_info(albums)").fetchall()
            }
            if columns and "artist_id" not in columns:
                connection.execute("ALTER TABLE albums ADD COLUMN artist_id INTEGER")
            connection.executescript(schema)
            track_columns = {
                row["name"]
                for row in connection.execute("PRAGMA table_info(tracks)").fetchall()
            }
            if "play_count" not in track_columns:
                connection.execute(
                    "ALTER TABLE tracks ADD COLUMN play_count INTEGER NOT NULL DEFAULT 0"
                )
            if "last_played" not in track_columns:
                connection.execute("ALTER TABLE tracks ADD COLUMN last_played TEXT")
            if "listen_seconds" not in track_columns:
                connection.execute(
                    "ALTER TABLE tracks ADD COLUMN listen_seconds INTEGER NOT NULL DEFAULT 0"
                )
            if "date_added" not in track_columns:
                connection.execute("ALTER TABLE tracks ADD COLUMN date_added TEXT")
                connection.execute(
                    """UPDATE tracks SET date_added=(
                       SELECT date_added FROM albums WHERE albums.id=tracks.album_id)
                       WHERE date_added IS NULL"""
                )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_albums_artist_id ON albums(artist_id)"
            )
            qualified_counter = connection.execute(
                "SELECT value FROM app_meta WHERE key='qualified_play_counter_v1'"
            ).fetchone()
            if qualified_counter is None:
                # Las versiones anteriores contaban al abrir la pista. Se reinicia
                # una sola vez para que el historial use exclusivamente escuchas
                # reales de al menos 30 segundos.
                connection.execute("UPDATE tracks SET play_count=0, last_played=NULL")
                connection.execute(
                    "INSERT INTO app_meta(key, value) VALUES ('qualified_play_counter_v1', '1')"
                )
            listening_counter = connection.execute(
                "SELECT value FROM app_meta WHERE key='listening_time_counter_v1'"
            ).fetchone()
            if listening_counter is None:
                # Los conteos anteriores no conservaban la duración escuchada.
                # Se reinician una sola vez para iniciar un ranking temporal fiable.
                connection.execute(
                    "UPDATE tracks SET play_count=0, listen_seconds=0, last_played=NULL"
                )
                connection.execute(
                    "INSERT INTO app_meta(key, value) VALUES ('listening_time_counter_v1', '1')"
                )
            connection.execute("PRAGMA journal_mode = WAL")
            connection.commit()
        finally:
            connection.close()
        self._logger.info("Base de datos preparada en %s", self.database_path)

    def import_library_scan(self, scan: object) -> dict[str, int]:
        """Guarda un escaneo Root/Artist/Album/Track en una sola transacción."""
        connection = self.connect()
        counts = {"artists": 0, "albums": 0, "tracks": 0}
        try:
            root_path = str(scan.root_path)
            connection.execute(
                "INSERT INTO library_roots(folder_path) VALUES (?) "
                "ON CONFLICT(folder_path) DO NOTHING",
                (root_path,),
            )
            root_id = int(
                connection.execute(
                    "SELECT id FROM library_roots WHERE folder_path = ?", (root_path,)
                ).fetchone()["id"]
            )
            for artist in scan.artists:
                connection.execute(
                    "INSERT INTO artists(root_id, name, folder_path) VALUES (?, ?, ?) "
                    "ON CONFLICT(folder_path) DO UPDATE SET root_id=excluded.root_id, name=excluded.name",
                    (root_id, artist.name, str(artist.folder_path)),
                )
                artist_id = int(
                    connection.execute(
                        "SELECT id FROM artists WHERE folder_path = ?", (str(artist.folder_path),)
                    ).fetchone()["id"]
                )
                counts["artists"] += 1
                for album in artist.albums:
                    connection.execute(
                        """INSERT INTO albums
                           (artist_id, title, album_artist, folder_path, cover_path, year, is_compilation)
                           VALUES (?, ?, ?, ?, ?, ?, ?)
                           ON CONFLICT(folder_path) DO UPDATE SET
                             artist_id=excluded.artist_id, title=excluded.title,
                             album_artist=excluded.album_artist, cover_path=excluded.cover_path,
                             year=excluded.year, is_compilation=excluded.is_compilation""",
                        (
                            artist_id,
                            album.title,
                            artist.name,
                            str(album.folder_path),
                            str(album.cover_path) if album.cover_path else None,
                            album.year,
                            int(album.is_compilation),
                        ),
                    )
                    album_id = int(
                        connection.execute(
                            "SELECT id FROM albums WHERE folder_path = ?", (str(album.folder_path),)
                        ).fetchone()["id"]
                    )
                    counts["albums"] += 1
                    for track in album.tracks:
                        connection.execute(
                            """INSERT INTO tracks
                               (album_id, title, track_artist, track_number, file_path, duration, file_format)
                               VALUES (?, ?, ?, ?, ?, ?, ?)
                               ON CONFLICT(file_path) DO UPDATE SET
                                 album_id=excluded.album_id, title=excluded.title,
                                 track_artist=excluded.track_artist, track_number=excluded.track_number,
                                 duration=excluded.duration, file_format=excluded.file_format""",
                            (
                                album_id,
                                track.title,
                                track.track_artist,
                                track.track_number,
                                str(track.file_path),
                                track.duration,
                                track.file_format,
                            ),
                        )
                        counts["tracks"] += 1
            connection.commit()
        except Exception:
            connection.rollback()
            self._logger.exception("No se pudo importar la biblioteca %s", scan.root_path)
            raise
        finally:
            connection.close()
        return counts

    def get_library_stats(self) -> dict[str, int]:
        connection = self.connect()
        try:
            album_row = connection.execute(
                """SELECT COUNT(*) AS total_albums,
                    COALESCE(SUM(CASE WHEN is_compilation = 0 THEN 1 ELSE 0 END), 0) AS albums,
                    COALESCE(SUM(CASE WHEN is_compilation = 1 THEN 1 ELSE 0 END), 0) AS compilations
                    FROM albums"""
            ).fetchone()
            tracks = connection.execute("SELECT COUNT(*) AS value FROM tracks").fetchone()["value"]
            artists = connection.execute(
                """SELECT COUNT(*) AS value FROM artists ar WHERE EXISTS (
                   SELECT 1 FROM albums al WHERE al.artist_id=ar.id AND al.is_compilation=0)"""
            ).fetchone()["value"]
            roots = connection.execute("SELECT COUNT(*) AS value FROM library_roots").fetchone()["value"]
        finally:
            connection.close()
        return {
            "total_albums": int(album_row["total_albums"]),
            "albums": int(album_row["albums"]),
            "compilations": int(album_row["compilations"]),
            "tracks": int(tracks),
            "artists": int(artists),
            "roots": int(roots),
        }

    def get_artists(self) -> list[sqlite3.Row]:
        return self.fetch_all(
            """SELECT ar.*,
               COUNT(DISTINCT CASE WHEN al.is_compilation=0 THEN al.id END) AS album_count,
               SUM(CASE WHEN al.is_compilation=0 THEN 1 ELSE 0 END) AS track_count,
               COALESCE(SUM(CASE WHEN al.is_compilation=0 THEN t.duration ELSE 0 END), 0) AS total_duration
               FROM artists ar LEFT JOIN albums al ON al.artist_id=ar.id
               LEFT JOIN tracks t ON t.album_id=al.id GROUP BY ar.id
               HAVING COUNT(DISTINCT CASE WHEN al.is_compilation=0 THEN al.id END) > 0
               ORDER BY ar.name COLLATE NOCASE"""
        )

    def get_albums(self, is_compilation: bool | None = None) -> list[sqlite3.Row]:
        where = "" if is_compilation is None else "WHERE al.is_compilation = ?"
        parameters: tuple[Any, ...] = () if is_compilation is None else (int(is_compilation),)
        return self.fetch_all(
            f"""SELECT al.*, ar.name AS artist_name, COUNT(t.id) AS track_count,
                COALESCE(SUM(t.duration), 0) AS total_duration
                FROM albums al LEFT JOIN artists ar ON ar.id=al.artist_id
                LEFT JOIN tracks t ON t.album_id=al.id {where}
                GROUP BY al.id ORDER BY al.title COLLATE NOCASE""",
            parameters,
        )

    def get_artists_for_root(self, root_id: int) -> list[sqlite3.Row]:
        return self.fetch_all(
            """SELECT ar.*, COUNT(DISTINCT al.id) AS album_count, COUNT(t.id) AS track_count,
               COALESCE(SUM(t.duration), 0) AS total_duration
               FROM artists ar LEFT JOIN albums al ON al.artist_id=ar.id
               LEFT JOIN tracks t ON t.album_id=al.id WHERE ar.root_id=?
               GROUP BY ar.id ORDER BY ar.folder_path COLLATE NOCASE""",
            (root_id,),
        )

    def get_roots(self) -> list[sqlite3.Row]:
        return self.fetch_all(
            """SELECT r.*, COUNT(DISTINCT ar.id) AS artist_count,
               COUNT(DISTINCT al.id) AS album_count, COUNT(t.id) AS track_count,
               COALESCE(SUM(t.duration), 0) AS total_duration
               FROM library_roots r LEFT JOIN artists ar ON ar.root_id=r.id
               LEFT JOIN albums al ON al.artist_id=ar.id LEFT JOIN tracks t ON t.album_id=al.id
               GROUP BY r.id ORDER BY r.folder_path COLLATE NOCASE"""
        )

    def get_tracks_for_album(self, album_id: int) -> list[sqlite3.Row]:
        return self.fetch_all(
            """SELECT t.*, al.title AS album_title, al.artist_id, al.is_compilation, ar.name AS artist_name
               FROM tracks t JOIN albums al ON al.id=t.album_id
               LEFT JOIN artists ar ON ar.id=al.artist_id WHERE t.album_id=?
               ORDER BY COALESCE(t.track_number, 999999), t.title COLLATE NOCASE""",
            (album_id,),
        )

    def get_album_by_id(self, album_id: int) -> sqlite3.Row | None:
        rows = self.fetch_all(
            """SELECT al.*, ar.name AS artist_name, COUNT(t.id) AS track_count,
               COALESCE(SUM(t.duration), 0) AS total_duration
               FROM albums al LEFT JOIN artists ar ON ar.id=al.artist_id
               LEFT JOIN tracks t ON t.album_id=al.id WHERE al.id=? GROUP BY al.id""",
            (album_id,),
        )
        return rows[0] if rows else None

    def update_track_title(self, file_path: str, title: str) -> str:
        clean_title = " ".join(title.split()).strip()
        if not clean_title:
            raise ValueError("El título no puede quedar vacío.")
        source = Path(file_path)
        safe_stem = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", clean_title).rstrip(" .")
        if not safe_stem:
            raise ValueError("El título no produce un nombre de archivo válido en Windows.")
        reserved = {
            "CON", "PRN", "AUX", "NUL",
            *(f"COM{number}" for number in range(1, 10)),
            *(f"LPT{number}" for number in range(1, 10)),
        }
        if safe_stem.upper() in reserved:
            safe_stem = f"_{safe_stem}"
        destination = source.with_name(f"{safe_stem}{source.suffix}")
        renamed = False
        if source.exists() and source != destination:
            if destination.exists():
                raise FileExistsError(
                    f"Ya existe un archivo llamado {destination.name} en esa carpeta."
                )
            source.rename(destination)
            renamed = True
        new_path = str(destination if renamed else source)
        connection = self.connect()
        try:
            cursor = connection.execute(
                "UPDATE tracks SET title=?, file_path=? WHERE file_path=?",
                (clean_title, new_path, file_path),
            )
            if not cursor.rowcount:
                raise ValueError("La pista no pertenece a la biblioteca.")
            connection.commit()
        except Exception:
            if renamed and destination.exists() and not source.exists():
                destination.rename(source)
            raise
        finally:
            connection.close()
        try:
            from mutagen import File

            audio = File(new_path, easy=True)
            if audio is not None:
                if audio.tags is None:
                    audio.add_tags()
                audio["title"] = [clean_title]
                audio.save()
        except Exception:
            # El cambio en la biblioteca sigue siendo válido aunque el formato,
            # el archivo de solo lectura o sus etiquetas no permitan escritura.
            self._logger.warning(
                "No se pudo guardar el título dentro del archivo %s", file_path,
                exc_info=True,
            )
        return new_path

    def get_albums_for_artist(self, artist_id: int) -> list[sqlite3.Row]:
        return self.fetch_all(
            """SELECT al.*, ar.name AS artist_name, COUNT(t.id) AS track_count,
               COALESCE(SUM(t.duration), 0) AS total_duration
               FROM albums al JOIN artists ar ON ar.id=al.artist_id
               LEFT JOIN tracks t ON t.album_id=al.id WHERE al.artist_id=?
               GROUP BY al.id ORDER BY al.title COLLATE NOCASE""",
            (artist_id,),
        )

    def get_tracks_for_artist(self, artist_id: int) -> list[sqlite3.Row]:
        return self.fetch_all(
            """SELECT t.*, al.title AS album_title, al.artist_id, al.is_compilation, ar.name AS artist_name
               FROM tracks t JOIN albums al ON al.id=t.album_id JOIN artists ar ON ar.id=al.artist_id
               WHERE ar.id=? ORDER BY al.title COLLATE NOCASE,
               COALESCE(t.track_number, 999999), t.title COLLATE NOCASE""",
            (artist_id,),
        )

    def get_tracks_for_root(self, root_id: int) -> list[sqlite3.Row]:
        return self.fetch_all(
            """SELECT t.*, al.title AS album_title, al.artist_id, al.is_compilation, ar.name AS artist_name
               FROM tracks t JOIN albums al ON al.id=t.album_id JOIN artists ar ON ar.id=al.artist_id
               WHERE ar.root_id=? ORDER BY ar.name COLLATE NOCASE, al.title COLLATE NOCASE,
               COALESCE(t.track_number, 999999), t.title COLLATE NOCASE""",
            (root_id,),
        )

    def get_track_context(self, file_path: str) -> sqlite3.Row | None:
        rows = self.fetch_all(
            """SELECT t.file_path, t.album_id, al.artist_id, al.is_compilation
               FROM tracks t JOIN albums al ON al.id=t.album_id
               WHERE t.file_path=?""",
            (file_path,),
        )
        return rows[0] if rows else None

    def record_track_play(self, file_path: str) -> None:
        connection = self.connect()
        try:
            connection.execute(
                """UPDATE tracks SET play_count=play_count+1,
                   last_played=CURRENT_TIMESTAMP WHERE file_path=?""",
                (file_path,),
            )
            connection.commit()
        finally:
            connection.close()

    def record_qualified_listen(self, file_path: str, seconds: int = 30) -> None:
        connection = self.connect()
        try:
            connection.execute(
                """UPDATE tracks SET play_count=play_count+1,
                   listen_seconds=listen_seconds+?, last_played=CURRENT_TIMESTAMP
                   WHERE file_path=?""",
                (max(0, int(seconds)), file_path),
            )
            connection.commit()
        finally:
            connection.close()

    def add_listen_time(self, file_path: str, seconds: int) -> None:
        increment = max(0, int(seconds))
        if not increment:
            return
        connection = self.connect()
        try:
            connection.execute(
                """UPDATE tracks SET listen_seconds=listen_seconds+?,
                   last_played=CURRENT_TIMESTAMP WHERE file_path=?""",
                (increment, file_path),
            )
            connection.commit()
        finally:
            connection.close()

    def get_top_artists(self, limit: int = 6) -> list[sqlite3.Row]:
        return self.fetch_all(
            """SELECT ar.id, ar.name, ar.folder_path,
               SUM(t.play_count) AS play_count,
               SUM(t.listen_seconds) AS listen_seconds
               FROM artists ar JOIN albums al ON al.artist_id=ar.id
               JOIN tracks t ON t.album_id=al.id
               WHERE al.is_compilation=0 AND t.play_count>0
               GROUP BY ar.id HAVING SUM(t.play_count) >= 3
               ORDER BY listen_seconds DESC, play_count DESC, ar.name COLLATE NOCASE
               LIMIT ?""",
            (limit,),
        )

    def get_top_tracks(self, limit: int = 10) -> list[sqlite3.Row]:
        return self.fetch_all(
            """SELECT t.*, al.title AS album_title, al.cover_path,
               al.artist_id, al.is_compilation, ar.name AS artist_name
               FROM tracks t JOIN albums al ON al.id=t.album_id
               LEFT JOIN artists ar ON ar.id=al.artist_id
               WHERE t.play_count>=3
               ORDER BY t.listen_seconds DESC, t.play_count DESC,
               t.last_played DESC, t.title COLLATE NOCASE
               LIMIT ?""",
            (limit,),
        )

    def search_tracks(self, text: str, limit: int = 200) -> list[sqlite3.Row]:
        words = [word for word in text.strip().split() if word]
        if not words:
            return []
        conditions = []
        parameters: list[Any] = []
        for word in words:
            conditions.append(
                "(t.title LIKE ? OR t.track_artist LIKE ? OR al.title LIKE ? OR ar.name LIKE ?)"
            )
            value = f"%{word}%"
            parameters.extend((value, value, value, value))
        parameters.append(limit)
        return self.fetch_all(
            f"""SELECT t.*, al.title AS album_title, al.cover_path, al.artist_id,
                al.is_compilation, ar.name AS artist_name
                FROM tracks t JOIN albums al ON al.id=t.album_id
                LEFT JOIN artists ar ON ar.id=al.artist_id
                WHERE {' AND '.join(conditions)}
                ORDER BY t.title COLLATE NOCASE LIMIT ?""",
            tuple(parameters),
        )

    def get_track_by_path(self, file_path: str) -> sqlite3.Row | None:
        rows = self.fetch_all(
            """SELECT t.*, al.title AS album_title, al.cover_path, al.artist_id,
               al.is_compilation, ar.name AS artist_name
               FROM tracks t JOIN albums al ON al.id=t.album_id
               LEFT JOIN artists ar ON ar.id=al.artist_id WHERE t.file_path=?""",
            (file_path,),
        )
        return rows[0] if rows else None

    def create_playlist(self, name: str) -> int:
        clean_name = " ".join(name.split()).strip()
        if not clean_name:
            raise ValueError("La lista necesita un nombre.")
        connection = self.connect()
        try:
            cursor = connection.execute(
                "INSERT INTO playlists(name) VALUES (?)", (clean_name,)
            )
            connection.commit()
            return int(cursor.lastrowid)
        finally:
            connection.close()

    def get_playlists(self) -> list[sqlite3.Row]:
        return self.fetch_all(
            """SELECT p.*, COUNT(pt.track_id) AS track_count,
               COALESCE(SUM(t.duration), 0) AS total_duration
               FROM playlists p LEFT JOIN playlist_tracks pt ON pt.playlist_id=p.id
               LEFT JOIN tracks t ON t.id=pt.track_id
               GROUP BY p.id ORDER BY p.name COLLATE NOCASE"""
        )

    def add_track_to_playlist(self, playlist_id: int, file_path: str) -> bool:
        connection = self.connect()
        try:
            track = connection.execute(
                "SELECT id FROM tracks WHERE file_path=?", (file_path,)
            ).fetchone()
            if track is None:
                raise ValueError("La pista no pertenece a la biblioteca.")
            position = int(
                connection.execute(
                    "SELECT COALESCE(MAX(position), 0) + 1 FROM playlist_tracks WHERE playlist_id=?",
                    (playlist_id,),
                ).fetchone()[0]
            )
            cursor = connection.execute(
                """INSERT OR IGNORE INTO playlist_tracks(playlist_id, track_id, position)
                   VALUES (?, ?, ?)""",
                (playlist_id, int(track["id"]), position),
            )
            if cursor.rowcount:
                connection.execute(
                    "UPDATE playlists SET date_modified=CURRENT_TIMESTAMP WHERE id=?",
                    (playlist_id,),
                )
            connection.commit()
            return bool(cursor.rowcount)
        finally:
            connection.close()

    def get_playlist_tracks(self, playlist_id: int) -> list[sqlite3.Row]:
        return self.fetch_all(
            """SELECT t.*, al.title AS album_title, al.artist_id, al.is_compilation,
               ar.name AS artist_name, pt.position
               FROM playlist_tracks pt JOIN tracks t ON t.id=pt.track_id
               JOIN albums al ON al.id=t.album_id
               LEFT JOIN artists ar ON ar.id=al.artist_id
               WHERE pt.playlist_id=? ORDER BY pt.position""",
            (playlist_id,),
        )

    def remove_track_from_playlist(self, playlist_id: int, file_path: str) -> None:
        connection = self.connect()
        try:
            connection.execute(
                """DELETE FROM playlist_tracks WHERE playlist_id=? AND track_id=(
                   SELECT id FROM tracks WHERE file_path=?)""",
                (playlist_id, file_path),
            )
            connection.execute(
                "UPDATE playlists SET date_modified=CURRENT_TIMESTAMP WHERE id=?",
                (playlist_id,),
            )
            connection.commit()
        finally:
            connection.close()

    def delete_playlist(self, playlist_id: int) -> None:
        connection = self.connect()
        try:
            connection.execute("DELETE FROM playlists WHERE id=?", (playlist_id,))
            connection.commit()
        finally:
            connection.close()

    def get_smart_playlist_artists(self) -> list[sqlite3.Row]:
        return self.fetch_all(
            """SELECT ar.id, ar.name, SUM(t.listen_seconds) AS listen_seconds,
               COUNT(t.id) AS track_count
               FROM artists ar JOIN albums al ON al.artist_id=ar.id
               JOIN tracks t ON t.album_id=al.id
               WHERE al.is_compilation=0 AND t.listen_seconds>0
               GROUP BY ar.id ORDER BY listen_seconds DESC, ar.name COLLATE NOCASE"""
        )

    def get_smart_tracks_global(self, limit: int = 500) -> list[sqlite3.Row]:
        return self._get_smart_tracks("t.listen_seconds>0", (), limit)

    def get_smart_tracks_new(self, limit: int = 500) -> list[sqlite3.Row]:
        return self._get_smart_tracks(
            "t.listen_seconds>0 AND t.date_added>=datetime('now', '-30 days')",
            (),
            limit,
        )

    def get_smart_tracks_for_artist(
        self, artist_id: int, limit: int = 500
    ) -> list[sqlite3.Row]:
        return self._get_smart_tracks(
            "t.listen_seconds>0 AND al.artist_id=? AND al.is_compilation=0",
            (artist_id,),
            limit,
        )

    def _get_smart_tracks(
        self, where: str, parameters: tuple[Any, ...], limit: int
    ) -> list[sqlite3.Row]:
        return self.fetch_all(
            f"""SELECT t.*, al.title AS album_title, al.artist_id,
                al.is_compilation, ar.name AS artist_name
                FROM tracks t JOIN albums al ON al.id=t.album_id
                LEFT JOIN artists ar ON ar.id=al.artist_id
                WHERE {where}
                ORDER BY t.listen_seconds DESC, t.play_count DESC,
                t.title COLLATE NOCASE LIMIT ?""",
            (*parameters, limit),
        )

    def fetch_all(self, query: str, parameters: tuple[Any, ...] = ()) -> list[sqlite3.Row]:
        connection = self.connect()
        try:
            return list(connection.execute(query, parameters).fetchall())
        finally:
            connection.close()
