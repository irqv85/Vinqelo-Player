# Vinqelo Player

Primera base ejecutable del reproductor de musica local para Windows.

## Requisitos

- Python 3.12 de 64 bits.
- VLC Media Player de 64 bits (se utilizara en el bloque de reproduccion).

## Preparar el entorno en Visual Studio Code

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

En Visual Studio Code, seleccione `.venv` como interprete de Python.

## Ejecutar

```powershell
python main.py
```

También puede iniciar la aplicación sin abrir Visual Studio Code haciendo doble
clic en `Iniciar Vinqelo Player.bat`. El archivo utiliza `pythonw.exe` para abrir
la interfaz sin dejar una consola visible.

En desarrollo, la biblioteca se crea en `database/library.sqlite3` y los errores
se guardan en `logs/vinqelo_player.log`. En una futura version empaquetada, esos
archivos se ubicaran en la carpeta de datos local del usuario de Windows.

## Alcance de esta version

- Ventana principal oscura y adaptable.
- Interfaz compacta de biblioteca inspirada en reproductores clásicos como Clementine.
- Identidad visual propia con el icono V azul.
- Ventana sin barra nativa, con esquinas redondeadas y controles propios.
- Metadatos completos de álbum y calidad técnica de la pista actual.
- Carátulas incrustadas, locales o recuperadas mediante MusicBrainz y Cover Art Archive.
- Navegacion entre Biblioteca, Buscar, Artistas, Albumes, Compilaciones y Carpetas.
- Cuadricula visual de albumes con caratula, titulo y artista.
- Busqueda global por cancion, artista o album.
- Barra inferior preparada para los controles del reproductor.
- Apertura y reproducción de MP3, FLAC, WAV, OGG, M4A y AAC mediante VLC.
- Pausa, detencion, pista anterior/siguiente, progreso y volumen.
- Cola real con la pista actual, la siguiente y las pendientes.
- Menu contextual **Anadir a la cola** sobre las listas de pistas.
- Importacion SQLite de bibliotecas completas con cola reproducible.
- El volumen se conserva entre ejecuciones.

## Organizar e importar la biblioteca

La jerarquia es fisica e inalterable. Organice la carpeta seleccionada asi:

```text
Mi biblioteca/
  Carlos Vives/
    Clasicos/
      01 - Cancion.mp3
      02 - Otra cancion.flac
```

`Carlos Vives` sera siempre el artista y `Clasicos` sera siempre el album,
independientemente de lo que indiquen las etiquetas internas del archivo. Para
compilaciones use, por ejemplo, `Mi biblioteca/Varios artistas/Romanticas 2026/`.

Si una carpeta de artista contiene pistas directamente, Vinqelo las conserva en
un album virtual llamado `Pistas sueltas`. Las carpetas con nombres de coleccion
como `Vallenatos Sueltos Spotify`, `Salsa nueva`, `Merengues`, `Gaitas`,
`Champetas`, `Playlist` o `Mix` aparecen directamente en **Compilaciones** como
`Varios artistas` y mantienen el artista individual de cada pista.

En **Artistas** se muestran tarjetas circulares construidas como un collage de
hasta cuatro portadas originales del propio artista. Vinqelo descarta resultados
marcados como recopilatorios y guarda las portadas en cache. `Pistas sueltas`
reutiliza ese mismo collage como caratula general. Al abrir un artista se muestran
sus albumes con caratula y debajo la lista de pistas.

Las portadas faltantes se buscan progresivamente al iniciar. La clave de cache
depende del artista y del titulo exacto del album; por ello no se vuelve a bajar
una imagen sin cambios. Nombres organizativos como
`Luis Miguel - 2001 - Mis Romances` se conservan en la biblioteca, pero se limpian
temporalmente a `Mis Romances` para localizar su lanzamiento original.

Al reproducir una pista desde un album o carpeta se carga la lista completa y se
comienza en la pista elegida. **Reproduccion en curso** vuelve al artista, album y
pista actual aunque la reproduccion haya avanzado automaticamente.

La portada de **Biblioteca** funciona como panel de actividad: muestra artistas y
canciones mas escuchados con sus collages o caratulas. Una escucha se registra
solamente despues de 30 segundos reales de reproduccion; el tiempo en pausa no
cuenta. Los rankings muestran un artista o una cancion al alcanzar tres escuchas
validas y se ordenan por el tiempo total acumulado, no por la cantidad de inicios.
El resaltado avanza a la pista siguiente junto con VLC.

Con clic derecho sobre un artista, album o compilacion se puede buscar una imagen
en internet y elegirla entre varias miniaturas en una ventana emergente. Las fotos
de artistas y las caratulas manuales provienen del catalogo musical de Deezer. La
busqueda automatica de respaldo conserva MusicBrainz/Cover Art Archive. La imagen
elegida queda fija y no es reemplazada automaticamente.

**Smart Playlist** crea listas dinámicas usando el tiempo escuchado: una lista
global mezclada, una lista de canciones agregadas durante los ultimos 30 dias y
una lista individual por cada artista. Todas se reordenan automaticamente y se
pueden reproducir completas desde cualquier pista.

Pulse el icono de carpeta de la parte superior, seleccione `Mi biblioteca` y
espere a que termine el analisis. Luego haga doble clic en una raiz, artista,
album o pista para reproducir su cola completa.

## Reproducir un archivo

1. Ejecute `python main.py`.
2. Pulse el icono de archivo en la parte superior de Biblioteca.
3. Seleccione un archivo de audio compatible.
4. Use los controles inferiores para pausar, detener, avanzar o retroceder.
