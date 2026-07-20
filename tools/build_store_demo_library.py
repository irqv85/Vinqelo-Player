"""Construye una biblioteca ficticia aislada para las capturas de Microsoft Store."""

from __future__ import annotations

import argparse
import hashlib
import shutil
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = PROJECT_ROOT / "database" / "schema.sql"
DEFAULT_DATA_DIR = PROJECT_ROOT / "store-assets" / "demo-library" / "data"
DEFAULT_COVERS_DIR = PROJECT_ROOT / "store-assets" / "demo-library" / "covers"


ARTISTS = (
    (
        "Aurora Vectorial",
        (
            ("Horizonte de Cristal", "horizonte-cristal.png", 2026,
             ("Primer Destello", "Horizonte", "Pulso Azul", "Cristal en Movimiento", "Señales")),
            ("Señales de Luz", "ciudad-magnetica.png", 2025,
             ("Frecuencia Inicial", "Luz de Medianoche", "Circuito Abierto", "Ecos Digitales")),
        ),
    ),
    (
        "Mar Abierto",
        (
            ("Mareas de Luz", "mareas-luz.png", 2026,
             ("Marea Serena", "Océano Interior", "Brisa Eléctrica", "Azul Profundo", "Regreso al Mar")),
            ("Corrientes", "horizonte-cristal.png", 2024,
             ("Corriente Norte", "Isla de Calma", "Línea del Agua", "Noche Marina")),
        ),
    ),
    (
        "Prisma Nocturno",
        (
            ("Ciudad Magnética", "ciudad-magnetica.png", 2025,
             ("Entrada a la Ciudad", "Neón Silencioso", "Avenida Magnética", "Último Tren", "Cielo Violeta")),
            ("Pulso Urbano", "mareas-luz.png", 2023,
             ("Pulso Urbano", "Líneas Paralelas", "Después de Medianoche", "Ruta Interior")),
        ),
    ),
    (
        "Ruta Solar",
        (
            ("Camino al Amanecer", "ruta-solar.png", 2026,
             ("Ruta Solar", "Kilómetro Cero", "Amanecer", "Viento Dorado", "Destino Azul")),
            ("Estaciones", "ciudad-magnetica.png", 2024,
             ("Primavera Digital", "Verano Lento", "Lluvia de Octubre", "Invierno Claro")),
        ),
    ),
)

COMPILATION = (
    "Noches de Vinqelo",
    "ciudad-magnetica.png",
    2026,
    (
        ("Aurora Vectorial", "Constelación"),
        ("Mar Abierto", "Marea Nocturna"),
        ("Prisma Nocturno", "Luces Lejanas"),
        ("Ruta Solar", "Camino de Estrellas"),
        ("Nube Modular", "Atmósfera"),
        ("Órbita Central", "Gravedad Azul"),
    ),
)


def _manual_artist_path(data_dir: Path, artist: str) -> Path:
    digest = hashlib.sha256(artist.casefold().encode("utf-8")).hexdigest()
    return data_dir / "cover_cache" / "manual_artists" / f"{digest}.img"


def build(data_dir: Path, covers_dir: Path) -> Path:
    data_dir.mkdir(parents=True, exist_ok=True)
    database_path = data_dir / "library.sqlite3"
    if database_path.exists():
        database_path.unlink()

    cover_paths = {path.name: path.resolve() for path in covers_dir.glob("*.png")}
    required = {album[1] for _, albums in ARTISTS for album in albums} | {COMPILATION[1]}
    missing = sorted(required.difference(cover_paths))
    if missing:
        raise FileNotFoundError(f"Faltan carátulas de demostración: {', '.join(missing)}")

    connection = sqlite3.connect(database_path)
    connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    root_path = r"C:\Música de demostración"
    root_id = connection.execute(
        "INSERT INTO library_roots(folder_path, date_added) VALUES (?, ?)",
        (root_path, "2026-07-01 09:30:00"),
    ).lastrowid

    track_serial = 0
    artist_ids: dict[str, int] = {}
    for artist_index, (artist, albums) in enumerate(ARTISTS, start=1):
        artist_folder = rf"{root_path}\{artist}"
        artist_id = connection.execute(
            "INSERT INTO artists(root_id, name, folder_path, date_added) VALUES (?, ?, ?, ?)",
            (root_id, artist, artist_folder, f"2026-07-{artist_index:02d} 10:00:00"),
        ).lastrowid
        artist_ids[artist] = int(artist_id)
        shutil.copyfile(cover_paths[albums[0][1]], _prepare_parent(_manual_artist_path(data_dir, artist)))

        for album_index, (album, cover, year, tracks) in enumerate(albums, start=1):
            album_folder = rf"{artist_folder}\{album}"
            album_id = connection.execute(
                """INSERT INTO albums(
                       artist_id, title, album_artist, folder_path, cover_path,
                       year, is_compilation, date_added
                   ) VALUES (?, ?, ?, ?, ?, ?, 0, ?)""",
                (
                    artist_id, album, artist, album_folder, str(cover_paths[cover]), year,
                    f"2026-07-{artist_index + album_index:02d} 11:15:00",
                ),
            ).lastrowid
            for number, title in enumerate(tracks, start=1):
                track_serial += 1
                duration = 178 + ((track_serial * 19) % 105)
                plays = max(3, 14 - track_serial // 3)
                listened = duration * plays - (track_serial % 4) * 21
                _insert_track(
                    connection, album_id, title, artist, number,
                    rf"{album_folder}\{number:02d} - {title}.flac",
                    duration, "FLAC", plays, listened, track_serial,
                )

    compilation_title, compilation_cover, year, compilation_tracks = COMPILATION
    compilation_artist = "Selección Vinqelo"
    compilation_folder = rf"{root_path}\{compilation_title}"
    compilation_artist_id = connection.execute(
        "INSERT INTO artists(root_id, name, folder_path, date_added) VALUES (?, ?, ?, ?)",
        (root_id, compilation_artist, compilation_folder, "2026-07-09 12:00:00"),
    ).lastrowid
    compilation_id = connection.execute(
        """INSERT INTO albums(
               artist_id, title, album_artist, folder_path, cover_path,
               year, is_compilation, date_added
           ) VALUES (?, ?, 'Varios artistas', ?, ?, ?, 1, ?)""",
        (
            compilation_artist_id, compilation_title, compilation_folder,
            str(cover_paths[compilation_cover]), year, "2026-07-09 12:05:00",
        ),
    ).lastrowid
    for number, (track_artist, title) in enumerate(compilation_tracks, start=1):
        track_serial += 1
        duration = 190 + ((number * 23) % 92)
        plays = max(3, 9 - number // 2)
        _insert_track(
            connection, compilation_id, title, track_artist, number,
            rf"{compilation_folder}\{number:02d} - {track_artist} - {title}.mp3",
            duration, "MP3", plays, duration * plays - number * 13, track_serial,
        )

    playlist_id = connection.execute(
        "INSERT INTO playlists(name, date_created, date_modified) VALUES (?, ?, ?)",
        ("Favoritas instrumentales", "2026-07-10 18:30:00", "2026-07-18 20:00:00"),
    ).lastrowid
    favorite_ids = [row[0] for row in connection.execute(
        "SELECT id FROM tracks ORDER BY listen_seconds DESC LIMIT 10"
    )]
    connection.executemany(
        "INSERT INTO playlist_tracks(playlist_id, track_id, position) VALUES (?, ?, ?)",
        ((playlist_id, track_id, position) for position, track_id in enumerate(favorite_ids, start=1)),
    )
    connection.execute(
        "INSERT OR REPLACE INTO app_meta(key, value) VALUES ('store_demo', '1')"
    )
    connection.execute(
        "INSERT OR REPLACE INTO app_meta(key, value) VALUES ('qualified_play_counter_v1', '1')"
    )
    connection.execute(
        "INSERT OR REPLACE INTO app_meta(key, value) VALUES ('listening_time_counter_v1', '1')"
    )
    connection.commit()
    connection.close()
    return database_path


def _prepare_parent(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _insert_track(
    connection: sqlite3.Connection,
    album_id: int,
    title: str,
    artist: str,
    number: int,
    file_path: str,
    duration: int,
    file_format: str,
    plays: int,
    listened: int,
    serial: int,
) -> None:
    last_played = datetime(2026, 7, 19, 21, 30) - timedelta(hours=serial * 3)
    connection.execute(
        """INSERT INTO tracks(
               album_id, title, track_artist, track_number, file_path, duration,
               file_format, file_size, modified_ns, file_signature, play_count,
               listen_seconds, last_played, date_added
           ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            album_id, title, artist, number, file_path, duration, file_format,
            25_000_000 + serial * 731_000, 1_720_000_000_000_000_000 + serial,
            f"demo-{serial:04d}", plays, listened,
            last_played.strftime("%Y-%m-%d %H:%M:%S"),
            (datetime(2026, 6, 25) + timedelta(days=serial % 24)).strftime("%Y-%m-%d %H:%M:%S"),
        ),
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--covers-dir", type=Path, default=DEFAULT_COVERS_DIR)
    args = parser.parse_args()
    print(build(args.data_dir.resolve(), args.covers_dir.resolve()))


if __name__ == "__main__":
    main()
