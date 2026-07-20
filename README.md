# Vinqelo Player

Vinqelo Player es un reproductor de música local para Windows. Organiza la
colección según las carpetas reales del usuario y ofrece una interfaz oscura,
rápida y adaptable.

## Funciones incluidas

### Reproducción

- Reproducción de MP3, FLAC, WAV, OGG, M4A y AAC.
- Reproducir, pausar, detener, pista anterior y pista siguiente.
- Barra de progreso, duración, búsqueda dentro de la pista y volumen persistente.
- Reproducción consecutiva de carpetas, álbumes, compilaciones y listas.
- Cola real con pista actual, siguiente y pistas pendientes.
- Clic derecho para añadir cualquier pista a la cola.
- Resaltado automático de la pista que está sonando sin mover el scroll del usuario.
- Panel inferior con carátula, título, artista, álbum, año, formato y calidad.

### Biblioteca basada en carpetas

Vinqelo respeta esta jerarquía física:

```text
Mi biblioteca/
  Artista/
    Álbum/
      01 - Canción.mp3
      02 - Otra canción.flac
```

- La carpeta de primer nivel define al artista.
- La carpeta interior define el álbum.
- Las etiquetas internas nunca cambian automáticamente ese artista o álbum.
- Las pistas colocadas directamente dentro del artista se reúnen en
  `Pistas sueltas`.
- Carpetas como `Vallenatos varios`, `Mix`, `Playlist` o similares
  pueden clasificarse como compilaciones de `Varios artistas`.
- Carpetas, artistas, álbumes y listas muestran cantidad de pistas y duración total.
- La sección Carpetas permite navegar por toda la estructura importada.

### Artistas, álbumes y compilaciones

- Artistas representados mediante una imagen circular o collage de sus álbumes.
- Vista de álbumes con carátula, título, artista, pistas y duración.
- Lista de pistas al abrir un álbum o artista.
- Opción para reproducir consecutivamente todos los álbumes de un artista.
- Sección independiente para compilaciones.
- Búsqueda dentro de Artistas, Álbumes, Compilaciones y listas de pistas.

### Carátulas e imágenes

- Prioridad para `cover.jpg`, `cover.png`, `folder.jpg`, `folder.png`,
  `front.jpg` y `front.png`.
- Carátula genérica cuando no hay una imagen disponible.
- Búsqueda de carátulas musicales en internet.
- Ventana con varias opciones antes de escoger una imagen de internet.
- Selección manual de imágenes guardadas en el equipo.
- Clic derecho sobre artistas y álbumes para fijar una imagen permanente.
- Caché local: las imágenes no se descargan nuevamente si la colección no cambió.
- La reproducción inferior conserva la carátula propia del álbum o pista actual.

### Búsqueda

- Buscador global de canciones, artistas y álbumes.
- Espera breve al escribir para no consultar SQLite con cada tecla.
- Buscadores locales en artistas, álbumes, compilaciones y pistas.
- Doble clic en un resultado para reproducir su álbum desde esa canción.

### Listas de reproducción

- Creación de listas personales persistentes en SQLite.
- Clic derecho sobre una canción → **Añadir a lista de reproducción…**.
- Creación de una lista nueva durante el mismo proceso.
- Reproducción completa desde cualquier pista.
- Eliminación de canciones y listas.
- Prevención de duplicados dentro de una misma lista.
- Cantidad de canciones y duración total visibles.

### Smart Playlist y estadísticas

- **Global:** canciones más escuchadas de toda la biblioteca.
- **New:** canciones agregadas durante los últimos 30 días que más se escuchan.
- **Por artista:** lista independiente con las canciones más escuchadas de cada artista.
- Cantidad de pistas y duración total en cada Smart Playlist.
- Rankings de artistas y canciones según tiempo real acumulado.
- Una reproducción sólo se valida después de 30 segundos escuchados.
- Los rankings principales comienzan a mostrar resultados después de tres escuchas válidas.
- El tiempo pausado no aumenta las estadísticas.

### Edición de títulos y datos oficiales

Desde la sección Carpetas:

- Clic derecho en una pista → **Editar título de la pista…**.
- Se actualizan SQLite y la etiqueta de audio cuando el formato permite escritura.
- El archivo físico también se renombra conservando su extensión:

  ```text
  track 01.mp3 → Nombre de la pista.mp3
  ```

- Se filtran caracteres que Windows no admite en nombres de archivo.
- Nunca se sobrescribe silenciosamente un archivo existente.
- La cola activa se actualiza aunque la canción esté reproduciéndose.
- Clic derecho en un álbum → **Buscar datos del álbum en internet…**.
- El catálogo musical en línea muestra diferentes ediciones y sus listas de pistas.
- Tabla comparativa editable antes de aplicar títulos manual o masivamente.
- Este proceso no cambia el artista ni el álbum definidos por las carpetas.

### Consola de sonido

- Botón de efectos situado junto a Stop.
- Preamplificador de −20 a +20 dB.
- Punto de resistencia en +6 dB: hay que soltar y volver a mover el fader para
  superar el nivel recomendado.
- Ecualizador configurable de seis bandas.
- Ganancia independiente de −20 a +20 dB por banda.
- Selector de frecuencia debajo de cada banda, expresado en Hz o kHz.
- Frecuencias disponibles desde 31,25 Hz
  hasta 16 kHz.
- Medidor VU LED vertical y dinámico junto al Preamp.
- Configuración de sonido guardada entre ejecuciones.
- No se incluye ajuste de tempo, porque fue retirado para preservar la calidad.

### Interfaz

- Tema oscuro, limpio y adaptable a diferentes tamaños de ventana.
- Ventana sin barra nativa, con bordes redondeados y controles propios.
- Barra lateral para Biblioteca, Buscar, Artistas, Álbumes, Compilaciones,
  Carpetas, Smart Playlist, listas personales, reproducción actual y cola.
- Identidad visual propia con el icono azul de Vinqelo.
- Menús y ventanas emergentes adaptados al tema oscuro.
- Se mantiene el scroll del usuario al avanzar automáticamente de pista.

## Ejecutar desde el código fuente

### Requisitos

- Windows de 64 bits.
- Python 3.12 de 64 bits.

### Preparar el entorno

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Después puede ejecutar:

```powershell
python main.py
```

También puede hacer doble clic en:

```text
Iniciar Vinqelo Player.bat
```

En desarrollo, SQLite se guarda en `database/library.sqlite3` y los errores en
`logs/vinqelo_player.log`.

## Versión portable para Windows

El portable actual se encuentra en:

```text
dist/Vinqelo Player Portable.exe
```

Incluye todos los componentes necesarios, por lo que no requiere instalaciones
adicionales. Al iniciarlo crea junto al ejecutable:

```text
Vinqelo Player Portable.exe
Vinqelo Player Data/
  library.sqlite3
  cover_cache/
  logs/
```

Para conservar biblioteca, listas, carátulas e historial al trasladarlo, copie
juntos el `.exe` y `Vinqelo Player Data`. Los archivos musicales no se copian:
deben seguir disponibles en la otra PC. Mantener las mismas rutas o la misma
letra del disco externo evita tener que importar la colección nuevamente.

Windows SmartScreen puede advertir sobre el ejecutable porque esta compilación
no está firmada con un certificado comercial.

## Instalador para Windows

El asistente de instalación se encuentra en:

```text
dist/Vinqelo Player Setup 0.7.0.exe
```

El instalador trabaja por usuario y no solicita permisos de administrador.
Al comenzar permite elegir entre español, inglés, portugués, francés, alemán
e italiano. Puede crear un acceso directo y registrar Vinqelo para abrir MP3,
FLAC, WAV, OGG, M4A y AAC. Cada formato tiene un icono Vinqelo identificable.

En la primera ejecución de una instalación nueva se confirma la carpeta Música
detectada por Windows. También puede elegirse otra carpeta o completar esta
configuración después. La biblioteca, las carátulas, las listas y el historial
se guardan en `Vinqelo Player Data` junto a la instalación y se conservan al
actualizar el programa.

## Manejo de errores

- Validación de carpetas inexistentes.
- Archivos dañados o metadatos faltantes no detienen el resto de la importación.
- Mensajes claros cuando un archivo no puede reproducirse.
- Registro técnico en `logs/vinqelo_player.log` o en la carpeta de datos portable.
- Rutas completas únicas en SQLite para evitar canciones duplicadas.

## Fuera del alcance actual

Todavía no se incluyen:

- Android.
- Sincronización entre equipos.
- Streaming o vídeo.
- Conversión automática a OGG.
- Búsqueda o descarga de archivos musicales.
- Firma comercial del ejecutable portable.

## Pruebas

La suite automatizada se ejecuta con:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Actualmente cubre base de datos, escaneo de bibliotecas, formatos, reproducción,
carátulas, búsqueda, metadatos, historial y listas de reproducción.
