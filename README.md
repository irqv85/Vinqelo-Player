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

En desarrollo, la biblioteca se crea en `database/library.sqlite3` y los errores
se guardan en `logs/vinqelo_player.log`. En una futura version empaquetada, esos
archivos se ubicaran en la carpeta de datos local del usuario de Windows.

## Alcance de esta version

- Ventana principal oscura y adaptable.
- Navegacion entre Biblioteca, Albumes, Compilaciones y Carpetas.
- Barra inferior preparada para los controles del reproductor.
- Apertura y reproducción de MP3, FLAC, WAV, OGG, M4A y AAC mediante VLC.
- Pausa, detención, saltos de 10 segundos, progreso y volumen.
- Esquema SQLite inicial y conteos de biblioteca.
- Seleccion preliminar de una carpeta, sin importarla aun.

## Reproducir un archivo

1. Ejecute `python main.py`.
2. Pulse **Abrir archivo** en la barra inferior.
3. Seleccione un archivo de audio compatible.
4. Use los controles inferiores para pausar, detener, avanzar o retroceder.
