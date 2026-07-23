# Vinqelo Player

**Current version: 0.7.3**

Vinqelo Player is a local music player and library manager for Windows. It
organizes music according to the user's real folder structure, keeps the
collection in a local SQLite database, and provides a clean interface designed
for large libraries.

The application is available through Microsoft Store and is licensed under the
GNU General Public License v3.0.

## What's new in 0.7.3

- Single-instance operation: launching Vinqelo again restores the application
  that is already running instead of opening a duplicate window.
- Opening one or several associated audio files from Windows reuses the active
  player and creates a temporary queue without importing those files.
- Background playback and export progress are available from the Windows
  system tray.
- Library export now respects the exact artist, album, folder, subfolder, or
  playlist selection instead of exporting unrelated music.
- Conversion processes remain hidden and run with low priority.
- Microsoft Store, Start menu, search, taskbar, tray, and audio-file icons use
  the corrected transparent artwork and dedicated size variants.

## Main features

### Local playback

- Supports MP3, FLAC, WAV, OGG, M4A, and AAC.
- Play, pause, stop, previous track, and next track controls.
- Seekable progress bar with elapsed time and total duration.
- Persistent volume between sessions.
- Continuous playback of folders, albums, compilations, playlists, and queues.
- Repeat current track or repeat the active folder, album, or playlist.
- Shuffle the current playback context.
- A single click selects a track; a double click starts playback.
- Opening an associated audio file from Windows loads it and starts playback.
- Opening several associated files creates a temporary queue without importing
  them into the library.
- Windows multimedia keys and system media controls are supported.
- Closing the main window keeps Vinqelo available in the Windows system tray.
  Its compact menu provides previous, play/pause, stop, next, restore, and exit.
- Vinqelo runs as a single instance. Opening the application or an associated
  audio file again reuses the existing window and playback engine.
- The current track can be located and centered again from the sidebar or the
  lower playback panel.
- The last loaded track is restored when the application starts and remains
  ready to play.

### Folder-based library

Vinqelo treats the physical folder hierarchy as the source of truth:

```text
Music library/
  Artist/
    Album/
      01 - Song.mp3
      02 - Another song.flac
```

- The first-level folder defines the artist.
- The folder inside the artist defines the album.
- Embedded tags cannot automatically replace those folder-defined values.
- Tracks stored directly inside an artist folder are grouped as loose tracks.
- Collections containing different performers can be classified as
  compilations under Various Artists.
- Artists and compilations can be reclassified manually.
- Manual classifications and chosen artist images remain fixed after library
  refreshes.
- Missing files are removed from the library and moved files can be recognized
  during a manual refresh.
- Library updates show progress and run without blocking normal interface use.
- Albums, artists, folders, playlists, and track lists display their track
  count and total duration.

### Artists, albums, compilations, and folders

- Circular artist images generated from a selected image or an album collage.
- Album artwork has priority in album views.
- Horizontal artist view with each album and its track list.
- Option to play all albums belonging to one artist.
- Dedicated album and compilation views.
- Folder browser inspired by the Windows file explorer.
- Global and local search fields with a short delay while typing.
- Clear button inside search fields.
- Double click is required to open artists, albums, folders, and tracks.

### Artwork and metadata

- Local artwork is searched first using names such as `cover`, `folder`, and
  `front` in JPG or PNG format.
- Embedded artwork can be reused and cached.
- Missing artwork may be searched online when internet access is enabled.
- Search results are presented before an image is selected.
- Artist and album artwork can be chosen manually and kept permanently.
- Cached artwork is reused instead of being downloaded again on every playback
  or library refresh.
- Online access can be disabled completely from Settings. In local mode,
  Vinqelo uses folder artwork, manually selected images, and embedded metadata.

### Search and track editing

- Global search across tracks, artists, and albums.
- Search inside artist, album, compilation, playlist, and folder views.
- Track titles can be edited from the folder browser.
- When a title changes, the physical audio file is renamed while preserving its
  extension.
- Unsupported Windows filename characters are removed safely.
- Existing files are never overwritten silently.
- Writable audio tags and the SQLite library are updated together.
- Album track lists can be compared with online catalog results before applying
  titles manually or in bulk.
- Folder-defined artists and albums are never replaced during that process.

### Queue and playlists

- The queue displays the current track and all upcoming tracks.
- Tracks can be added to the queue from their context menu.
- Personal playlists are stored persistently in SQLite.
- Tracks can be added to an existing playlist or to a newly created playlist.
- Duplicate entries inside the same playlist are prevented.
- Playlists can be reordered, played from any track, or deleted.
- Playlist export allows all tracks or only selected tracks to be included.

### Smart Playlists and listening statistics

- **Global:** most-listened tracks across the complete library.
- **New:** most-listened tracks added during the last 30 days.
- **By artist:** an individual ranking for every artist.
- Rankings use accumulated listening time.
- A listening session qualifies after at least 30 seconds.
- Main rankings begin showing a track after three qualified listening sessions.
- Paused time is not counted.
- Library dashboard with total artists, albums, compilations, tracks, duration,
  file formats, track counts, and average bitrate by format.
- Most-listened artists and tracks can be opened directly from the dashboard.

### Library export and external-drive synchronization

- Export complete libraries or selected folders, albums, playlists, and Smart
  Playlists.
- Removable drives are detected and offered as destinations.
- A normal directory can also be selected manually.
- Library tracks are organized as `Artist / Album / Track`.
- Compilations and playlists are placed in their own organized directories.
- Synchronization copies only new or modified files on later runs.
- Output can be converted to MP3 up to 128 kbps or WMA up to 160 kbps.
- Optional safe peak normalization raises volume without intentional clipping.
- Conversion uses one worker thread with low process priority to reduce its
  impact on playback and system responsiveness.
- Export can be cancelled without leaving incomplete final files.
- Export progress can be minimized to the system tray, restored or cancelled
  from its menu, and Windows displays a notification when it finishes.

### Sound console

- Preamplifier from −20 to +20 dB.
- Safety resistance point at +6 dB before entering the extended range.
- Configurable six-band equalizer.
- Independent gain from −20 to +20 dB per band.
- Selectable frequencies from 31.25 Hz to 16 kHz.
- Compact vertical VU meter.
- Sound settings are preserved between sessions.

### Interface and accessibility

- Six coordinated themes: Vinqelo, Clementine, Amarok, Emerald, Graphite, and
  MusicMatch Classic.
- Dark themes and a gray-blue light theme.
- Square application frame with custom window controls.
- Adjustable interface font size.
- Optional classic application menu.
- Interface languages: English, Spanish, Portuguese, French, German, and
  Italian.
- Translated startup and library-refresh screens.
- Consistent button, menu, dialog, selection, hover, and scrollbar colors.
- Sidebar sections for Library, Search, Artists, Albums, Compilations, Folders,
  Smart Playlists, Playlists, Now Playing, and Play Queue.
- Now Playing is displayed only while a playback context exists.
- Startup banner provides immediate feedback while the application is opening.
- Transparent, size-specific Windows icons are included for Microsoft Store,
  Start, search, taskbar, and the system tray.
- Associated audio files use their own Vinqelo document icon.

### Privacy and reliability

- Music files and library data remain on the user's computer.
- Internet access for artwork and catalog metadata can be disabled.
- SQLite prevents duplicate tracks by using their complete file paths.
- Damaged files and missing metadata do not stop the rest of a library scan.
- Missing folders and playback failures produce clear messages.
- Technical errors are recorded in a local log.
- Microsoft Store updates preserve the library and settings in the application's
  persistent Windows data directory.

## Running from source

### Requirements

- 64-bit Windows.
- 64-bit Python 3.12.

### Setup

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python main.py
```

During development, the SQLite library is stored in
`database/library.sqlite3`, cached images in `cover_cache`, and technical logs
in `logs/vinqelo_player.log`.

## Project structure

```text
main.py                 Application entry point
config.py               Shared paths and application information
database/               SQLite schema and data access
library/                Scanning, metadata, artwork, and export services
models/                 Album and track data models
player/                 Playback and Windows media integration
ui/                     Dialogs, pages, widgets, themes, and translations
assets/                 Logos, generic artwork, file icons, and local resources
tests/                  Automated test suite
tools/                  Store assets and packaging utilities
packaging/              Microsoft Store manifest and package configuration
logs/                   Development logs
```

## Tests

Run the complete automated suite with:

```powershell
python -m unittest discover -s tests -v
```

The 48-test suite covers database operations, library scanning, file moves,
manual classifications, audio formats, playback helpers, artwork caching,
metadata, listening history, playlists, library export selection,
single-instance activation, hidden conversion processes, and Store assets.

## License and contact

- License: GNU General Public License v3.0
- Source code: https://github.com/irqv85/Vinqelo-Player
- Contact: `vinqeloapp@gmail.com`

---

# Vinqelo Player — Español

**Versión actual: 0.7.3**

Vinqelo Player es un reproductor y administrador de música local para Windows.
Organiza la música según la estructura real de carpetas del usuario, conserva
la colección en una base SQLite local y ofrece una interfaz preparada para
bibliotecas grandes.

La aplicación está disponible mediante Microsoft Store y se distribuye bajo la
licencia GNU General Public License v3.0.

## Novedades de la versión 0.7.3

- Funcionamiento con una sola instancia: volver a iniciar Vinqelo restaura la
  aplicación que ya está abierta en lugar de crear otra ventana.
- Abrir desde Windows uno o varios archivos asociados reutiliza el reproductor
  activo y crea una cola temporal sin importarlos a la biblioteca.
- La reproducción en segundo plano y el progreso de las exportaciones están
  disponibles desde la bandeja de Windows.
- La exportación de biblioteca respeta exactamente el artista, álbum, carpeta,
  subcarpeta o lista seleccionados, sin copiar música ajena a la selección.
- Los procesos de conversión permanecen ocultos y trabajan con prioridad baja.
- Los iconos de Microsoft Store, Inicio, búsqueda, barra de tareas, bandeja y
  archivos de audio utilizan los recursos transparentes y tamaños corregidos.

## Funciones principales

### Reproducción local

- Reproduce MP3, FLAC, WAV, OGG, M4A y AAC.
- Controles de reproducir, pausar, detener, pista anterior y pista siguiente.
- Barra de progreso interactiva con tiempo transcurrido y duración total.
- Volumen persistente entre sesiones.
- Reproducción consecutiva de carpetas, álbumes, compilaciones, listas y colas.
- Repetición de una pista o del contexto actual.
- Modo aleatorio limitado a la carpeta, álbum, lista o cola en curso.
- Un clic selecciona una pista; el doble clic inicia la reproducción.
- Al abrir desde Windows un archivo asociado, Vinqelo lo carga y comienza a
  reproducirlo.
- Al abrir varios archivos asociados, se crea una cola temporal sin agregarlos
  a la biblioteca.
- Compatibilidad con teclas multimedia y controles multimedia de Windows.
- Al cerrar la ventana principal, Vinqelo permanece en la bandeja de Windows.
  El menú compacto ofrece anterior, reproducir/pausar, detener, siguiente,
  restaurar y salir.
- Vinqelo utiliza una sola instancia. Volver a abrir la aplicación o un archivo
  asociado reutiliza la ventana y el reproductor que ya están activos.
- Reproducción en curso permite regresar y centrar la pista actual desde la
  barra lateral o desde el panel inferior.
- La última pista cargada se restaura al iniciar y queda preparada para
  reproducirse.

### Biblioteca basada en carpetas

Vinqelo utiliza la jerarquía física como fuente principal:

```text
Biblioteca musical/
  Artista/
    Álbum/
      01 - Canción.mp3
      02 - Otra canción.flac
```

- La carpeta de primer nivel define al artista.
- La carpeta interior define al álbum.
- Las etiquetas internas no sustituyen automáticamente esos valores.
- Las canciones colocadas directamente dentro del artista se agrupan como
  pistas sueltas.
- Las colecciones con distintos intérpretes pueden clasificarse como
  compilaciones de Varios artistas.
- Artistas y compilaciones pueden reclasificarse manualmente.
- Las clasificaciones manuales y las imágenes elegidas permanecen fijas después
  de actualizar la biblioteca.
- Los archivos eliminados desaparecen de la biblioteca y los archivos movidos
  pueden reconocerse durante una actualización manual.
- La actualización muestra progreso y se ejecuta sin bloquear la interfaz.
- Álbumes, artistas, carpetas y listas muestran cantidad de pistas y duración.

### Artistas, álbumes, compilaciones y carpetas

- Imágenes circulares de artista creadas con una foto elegida o un collage de
  sus álbumes.
- La carátula del álbum tiene prioridad en las vistas de álbumes.
- Vista horizontal de artista con cada álbum y su lista de temas.
- Opción para reproducir todos los discos de un artista.
- Secciones independientes de álbumes y compilaciones.
- Navegador de carpetas inspirado en el explorador de Windows.
- Buscadores globales y locales con una espera breve mientras se escribe.
- Botón para borrar rápidamente cada búsqueda.
- Artistas, álbumes, carpetas y pistas se abren o reproducen con doble clic.

### Carátulas y metadatos

- Primero busca carátulas locales llamadas `cover`, `folder` o `front` en JPG
  o PNG.
- Puede reutilizar y almacenar carátulas incrustadas.
- Si falta una imagen, puede buscarla en internet cuando el acceso esté
  habilitado.
- Los resultados se muestran antes de elegir una imagen.
- Las imágenes de artistas y álbumes pueden seleccionarse manualmente y fijarse.
- La caché evita volver a descargar carátulas durante cada reproducción o
  actualización.
- Desde Configuración puede desactivarse completamente el acceso a internet. En
  modo local se utilizan imágenes de las carpetas, imágenes manuales y
  metadatos incrustados.

### Búsqueda y edición

- Búsqueda global de pistas, artistas y álbumes.
- Búsqueda dentro de artistas, álbumes, compilaciones, listas y carpetas.
- Edición del título de una pista desde el navegador de carpetas.
- Al cambiar el título también se renombra el archivo físico, conservando su
  extensión.
- Se eliminan de forma segura los caracteres no admitidos por Windows.
- Nunca se sobrescribe silenciosamente un archivo existente.
- Las etiquetas editables y SQLite se actualizan juntas.
- Las pistas de un álbum pueden compararse con resultados de un catálogo en
  línea antes de aplicar cambios manuales o masivos.
- El artista y el álbum definidos por las carpetas nunca se sustituyen durante
  ese proceso.

### Cola y listas de reproducción

- La cola muestra la pista actual y todo lo que sonará después.
- El menú contextual permite añadir pistas a la cola.
- Las listas personales se guardan permanentemente en SQLite.
- Es posible añadir una pista a una lista existente o crear una nueva.
- Se evitan duplicados dentro de una misma lista.
- Las listas pueden ordenarse, reproducirse desde cualquier pista o eliminarse.
- La exportación permite incluir todas las canciones o solo una selección.

### Listas inteligentes y estadísticas

- **Global:** canciones más escuchadas de toda la biblioteca.
- **New:** canciones más escuchadas agregadas durante los últimos 30 días.
- **Por artista:** clasificación independiente para cada artista.
- Las clasificaciones utilizan el tiempo acumulado de escucha.
- Una escucha se valida después de al menos 30 segundos.
- Las clasificaciones principales muestran una pista después de tres escuchas
  válidas.
- El tiempo en pausa no se contabiliza.
- Panel principal con artistas, álbumes, compilaciones, pistas, duración,
  formatos, cantidad y bitrate promedio por formato.
- Los artistas y canciones más escuchados se pueden abrir directamente.

### Exportación y sincronización con unidades externas

- Exportación de toda la biblioteca o de carpetas, álbumes, listas y listas
  inteligentes seleccionadas.
- Detección de unidades extraíbles como destinos sugeridos.
- También puede elegirse cualquier directorio.
- La biblioteca se organiza como `Artista / Álbum / Pista`.
- Las compilaciones y listas se guardan en directorios organizados.
- La sincronización copia solamente archivos nuevos o modificados.
- Conversión a MP3 de hasta 128 kbps o WMA de hasta 160 kbps.
- Normalización opcional a un pico seguro sin recorte intencional.
- La conversión utiliza un solo hilo y prioridad baja para reducir su impacto
  sobre la reproducción y el equipo.
- La exportación puede cancelarse sin dejar archivos finales incompletos.
- El progreso puede minimizarse a la bandeja, restaurarse o cancelarse desde su
  menú, y Windows muestra una notificación al terminar.

### Consola de sonido

- Preamplificador de −20 a +20 dB.
- Punto de resistencia de seguridad en +6 dB antes del rango ampliado.
- Ecualizador configurable de seis bandas.
- Ganancia independiente de −20 a +20 dB por banda.
- Frecuencias seleccionables desde 31,25 Hz hasta 16 kHz.
- Medidor VU vertical compacto.
- La configuración de sonido se conserva entre sesiones.

### Interfaz y accesibilidad

- Seis temas coordinados: Vinqelo, Clementine, Amarok, Esmeralda, Grafito y
  MusicMatch clásico.
- Temas oscuros y un tema claro gris azulado.
- Ventana cuadrada con controles propios.
- Tamaño de letra ajustable.
- Barra de menú clásica opcional.
- Idiomas: inglés, español, portugués, francés, alemán e italiano.
- Pantallas de inicio y actualización traducidas.
- Colores coherentes en botones, menús, ventanas, selecciones, estados hover y
  barras de desplazamiento.
- Barra lateral con Biblioteca, Buscar, Artistas, Álbumes, Compilaciones,
  Carpetas, Listas inteligentes, Listas, Reproducción en curso y Cola.
- Reproducción en curso solo aparece cuando existe un contexto activo.
- El banner de inicio informa inmediatamente que la aplicación está abriendo.
- Incluye iconos transparentes adaptados a cada tamaño de Microsoft Store,
  Inicio, búsqueda, barra de tareas y bandeja.
- Los archivos de audio asociados utilizan su propio icono de documento
  Vinqelo.

### Privacidad y estabilidad

- Los archivos de música y los datos de biblioteca permanecen en el equipo.
- El acceso a internet para carátulas y metadatos puede desactivarse.
- SQLite evita pistas duplicadas mediante su ruta completa.
- Los archivos dañados y metadatos faltantes no detienen el resto del escaneo.
- Las carpetas inexistentes y errores de reproducción producen mensajes claros.
- Los errores técnicos se registran localmente.
- Las actualizaciones de Microsoft Store conservan la biblioteca y la
  configuración en el directorio persistente de Windows.

## Ejecutar desde el código fuente

### Requisitos

- Windows de 64 bits.
- Python 3.12 de 64 bits.

### Preparación

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python main.py
```

Durante el desarrollo, SQLite se guarda en `database/library.sqlite3`, las
imágenes en `cover_cache` y los registros técnicos en
`logs/vinqelo_player.log`.

## Estructura del proyecto

```text
main.py                 Punto de entrada
config.py               Rutas e información compartida
database/               Esquema SQLite y acceso a datos
library/                Escaneo, metadatos, carátulas y exportación
models/                 Modelos de álbum y pista
player/                 Reproducción e integración multimedia de Windows
ui/                     Ventanas, páginas, controles, temas y traducciones
assets/                 Logos, carátulas genéricas, iconos y recursos
tests/                  Pruebas automatizadas
tools/                  Recursos y utilidades de Microsoft Store
packaging/              Manifiesto y configuración del paquete Store
logs/                   Registros de desarrollo
```

## Pruebas

La suite completa se ejecuta con:

```powershell
python -m unittest discover -s tests -v
```

Las 48 pruebas cubren base de datos, escaneo, movimientos de archivos,
clasificaciones manuales, formatos de audio, reproducción, caché de carátulas,
metadatos, historial, listas, selección de exportaciones, instancia única,
procesos de conversión ocultos y recursos de Microsoft Store.

## Licencia y contacto

- Licencia: GNU General Public License v3.0
- Código fuente: https://github.com/irqv85/Vinqelo-Player
- Contacto: `vinqeloapp@gmail.com`
