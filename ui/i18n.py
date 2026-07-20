"""Traducción dinámica de la interfaz de Vinqelo Player.

Los nombres de artistas, álbumes y pistas nunca se traducen: el catálogo solo
contiene textos propios de la aplicación.
"""

from __future__ import annotations

import re

from PySide6.QtCore import QEvent, QLocale, QObject
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QAbstractButton,
    QApplication,
    QComboBox,
    QDoubleSpinBox,
    QLabel,
    QLineEdit,
    QListWidget,
    QMenu,
    QSpinBox,
    QTabWidget,
    QTreeWidget,
    QWidget,
)


# Español es el texto fuente. Mantener frases completas evita modificar datos
# musicales que casualmente contengan una palabra común.
T: dict[str, dict[str, str]] = {
    "Configurar biblioteca de música": {"en": "Set up music library", "pt": "Configurar biblioteca de música", "fr": "Configurer la bibliothèque musicale", "de": "Musikbibliothek einrichten", "it": "Configura la libreria musicale"},
    "Windows indicó esta carpeta para tu música:\n\n{path}\n\n¿Quieres usarla como biblioteca principal?": {"en": "Windows selected this folder for your music:\n\n{path}\n\nWould you like to use it as your main library?", "pt": "O Windows indicou esta pasta para suas músicas:\n\n{path}\n\nDeseja usá-la como biblioteca principal?", "fr": "Windows a indiqué ce dossier pour votre musique :\n\n{path}\n\nVoulez-vous l’utiliser comme bibliothèque principale ?", "de": "Windows hat diesen Ordner für deine Musik angegeben:\n\n{path}\n\nMöchtest du ihn als Hauptbibliothek verwenden?", "it": "Windows ha indicato questa cartella per la tua musica:\n\n{path}\n\nVuoi usarla come libreria principale?"},
    "Usar esta carpeta": {"en": "Use this folder", "pt": "Usar esta pasta", "fr": "Utiliser ce dossier", "de": "Diesen Ordner verwenden", "it": "Usa questa cartella"},
    "Elegir otra carpeta": {"en": "Choose another folder", "pt": "Escolher outra pasta", "fr": "Choisir un autre dossier", "de": "Anderen Ordner wählen", "it": "Scegli un’altra cartella"},
    "Configurar después": {"en": "Set up later", "pt": "Configurar depois", "fr": "Configurer plus tard", "de": "Später einrichten", "it": "Configura più tardi"},
    "Pista": {"en": "Track", "pt": "Faixa", "fr": "Piste", "de": "Titel", "it": "Brano"},
    "Disco": {"en": "Disc", "pt": "Disco", "fr": "Disque", "de": "Disc", "it": "Disco"},
    "bits": {"en": "bits", "pt": "bits", "fr": "bits", "de": "Bit", "it": "bit"},
    "Mono": {"en": "Mono", "pt": "Mono", "fr": "Mono", "de": "Mono", "it": "Mono"},
    "Estéreo": {"en": "Stereo", "pt": "Estéreo", "fr": "Stéréo", "de": "Stereo", "it": "Stereo"},
    "canales": {"en": "channels", "pt": "canais", "fr": "canaux", "de": "Kanäle", "it": "canali"},
    "Título": {"en": "Title", "pt": "Título", "fr": "Titre", "de": "Titel", "it": "Titolo"},
    "Álbum": {"en": "Album", "pt": "Álbum", "fr": "Album", "de": "Album", "it": "Album"},
    "Artista del álbum": {"en": "Album artist", "pt": "Artista do álbum", "fr": "Artiste de l’album", "de": "Albumkünstler", "it": "Artista dell’album"},
    "Año": {"en": "Year", "pt": "Ano", "fr": "Année", "de": "Jahr", "it": "Anno"},
    "Género": {"en": "Genre", "pt": "Gênero", "fr": "Genre", "de": "Genre", "it": "Genere"},
    "Calidad": {"en": "Quality", "pt": "Qualidade", "fr": "Qualité", "de": "Qualität", "it": "Qualità"},
    "Tamaño": {"en": "Size", "pt": "Tamanho", "fr": "Taille", "de": "Größe", "it": "Dimensione"},
    "Archivo local": {"en": "Local file", "pt": "Arquivo local", "fr": "Fichier local", "de": "Lokale Datei", "it": "File locale"},
    "Carátula incrustada": {"en": "Embedded cover", "pt": "Capa incorporada", "fr": "Pochette intégrée", "de": "Eingebettetes Cover", "it": "Copertina incorporata"},
    "Carátula elegida manualmente": {"en": "Manually selected cover", "pt": "Capa escolhida manualmente", "fr": "Pochette choisie manuellement", "de": "Manuell ausgewähltes Cover", "it": "Copertina scelta manualmente"},
    "Carátula oficial de la biblioteca": {"en": "Official library cover", "pt": "Capa oficial da biblioteca", "fr": "Pochette officielle de la bibliothèque", "de": "Offizielles Bibliothekscover", "it": "Copertina ufficiale della libreria"},
    "Caché local de MusicBrainz": {"en": "Local MusicBrainz cache", "pt": "Cache local do MusicBrainz", "fr": "Cache MusicBrainz local", "de": "Lokaler MusicBrainz-Cache", "it": "Cache locale di MusicBrainz"},
    "Configuración": {"en": "Settings", "pt": "Configurações", "fr": "Paramètres", "de": "Einstellungen", "it": "Impostazioni"},
    "Reproducción": {"en": "Playback", "pt": "Reprodução", "fr": "Lecture", "de": "Wiedergabe", "it": "Riproduzione"},
    "Apariencia": {"en": "Appearance", "pt": "Aparência", "fr": "Apparence", "de": "Darstellung", "it": "Aspetto"},
    "Idioma": {"en": "Language", "pt": "Idioma", "fr": "Langue", "de": "Sprache", "it": "Lingua"},
    "Guardar": {"en": "Save", "pt": "Salvar", "fr": "Enregistrer", "de": "Speichern", "it": "Salva"},
    "Cancelar": {"en": "Cancel", "pt": "Cancelar", "fr": "Annuler", "de": "Abbrechen", "it": "Annulla"},
    "Cerrar": {"en": "Close", "pt": "Fechar", "fr": "Fermer", "de": "Schließen", "it": "Chiudi"},
    "Minimizar": {"en": "Minimize", "pt": "Minimizar", "fr": "Réduire", "de": "Minimieren", "it": "Riduci"},
    "Maximizar": {"en": "Maximize", "pt": "Maximizar", "fr": "Agrandir", "de": "Maximieren", "it": "Ingrandisci"},
    "Biblioteca": {"en": "Library", "pt": "Biblioteca", "fr": "Bibliothèque", "de": "Bibliothek", "it": "Libreria"},
    "Buscar": {"en": "Search", "pt": "Pesquisar", "fr": "Rechercher", "de": "Suchen", "it": "Cerca"},
    "Artistas": {"en": "Artists", "pt": "Artistas", "fr": "Artistes", "de": "Künstler", "it": "Artisti"},
    "Álbumes": {"en": "Albums", "pt": "Álbuns", "fr": "Albums", "de": "Alben", "it": "Album"},
    "Compilaciones": {"en": "Compilations", "pt": "Compilações", "fr": "Compilations", "de": "Kompilationen", "it": "Raccolte"},
    "Carpetas": {"en": "Folders", "pt": "Pastas", "fr": "Dossiers", "de": "Ordner", "it": "Cartelle"},
    "Pistas": {"en": "Tracks", "pt": "Faixas", "fr": "Pistes", "de": "Titel", "it": "Brani"},
    "Listas de reproducción": {"en": "Playlists", "pt": "Playlists", "fr": "Listes de lecture", "de": "Wiedergabelisten", "it": "Playlist"},
    "Reproducción en curso": {"en": "Now playing", "pt": "Reproduzindo agora", "fr": "Lecture en cours", "de": "Aktuelle Wiedergabe", "it": "In riproduzione"},
    "Cola de reproducción": {"en": "Play queue", "pt": "Fila de reprodução", "fr": "File de lecture", "de": "Warteschlange", "it": "Coda di riproduzione"},
    "Acerca de": {"en": "About", "pt": "Sobre", "fr": "À propos", "de": "Über", "it": "Informazioni"},
    "TU MÚSICA": {"en": "YOUR MUSIC", "pt": "SUA MÚSICA", "fr": "VOTRE MUSIQUE", "de": "DEINE MUSIK", "it": "LA TUA MUSICA"},
    "REPRODUCCIÓN": {"en": "PLAYBACK", "pt": "REPRODUÇÃO", "fr": "LECTURE", "de": "WIEDERGABE", "it": "RIPRODUZIONE"},
    "PLAYER LOCAL": {"en": "LOCAL PLAYER", "pt": "PLAYER LOCAL", "fr": "LECTEUR LOCAL", "de": "LOKALER PLAYER", "it": "LETTORE LOCALE"},
    "COLECCIÓN LOCAL": {"en": "LOCAL COLLECTION", "pt": "COLEÇÃO LOCAL", "fr": "COLLECTION LOCALE", "de": "LOKALE SAMMLUNG", "it": "COLLEZIONE LOCALE"},
    "BIBLIOTECA": {"en": "LIBRARY", "pt": "BIBLIOTECA", "fr": "BIBLIOTHÈQUE", "de": "BIBLIOTHEK", "it": "LIBRERIA"},
    "Reproducir": {"en": "Play", "pt": "Reproduzir", "fr": "Lire", "de": "Wiedergeben", "it": "Riproduci"},
    "Pausar": {"en": "Pause", "pt": "Pausar", "fr": "Pause", "de": "Pause", "it": "Pausa"},
    "Detener": {"en": "Stop", "pt": "Parar", "fr": "Arrêter", "de": "Stopp", "it": "Ferma"},
    "Anterior": {"en": "Previous", "pt": "Anterior", "fr": "Précédent", "de": "Zurück", "it": "Precedente"},
    "Siguiente": {"en": "Next", "pt": "Próxima", "fr": "Suivant", "de": "Weiter", "it": "Successivo"},
    "Atrás": {"en": "Back", "pt": "Voltar", "fr": "Retour", "de": "Zurück", "it": "Indietro"},
    "Volver": {"en": "Back", "pt": "Voltar", "fr": "Retour", "de": "Zurück", "it": "Indietro"},
    "Exportar": {"en": "Export", "pt": "Exportar", "fr": "Exporter", "de": "Exportieren", "it": "Esporta"},
    "Exportación": {"en": "Export", "pt": "Exportação", "fr": "Exportation", "de": "Export", "it": "Esportazione"},
    "Exportar playlist": {"en": "Export playlist", "pt": "Exportar playlist", "fr": "Exporter la liste", "de": "Wiedergabeliste exportieren", "it": "Esporta playlist"},
    "Formato de salida:": {"en": "Output format:", "pt": "Formato de saída:", "fr": "Format de sortie :", "de": "Ausgabeformat:", "it": "Formato di uscita:"},
    "Selecciona el directorio de destino": {"en": "Select the destination folder", "pt": "Selecione a pasta de destino", "fr": "Sélectionnez le dossier de destination", "de": "Zielordner auswählen", "it": "Seleziona la cartella di destinazione"},
    "MP3 · 128 kbps": {"en": "MP3 · 128 kbps", "pt": "MP3 · 128 kbps", "fr": "MP3 · 128 kbps", "de": "MP3 · 128 kbit/s", "it": "MP3 · 128 kbps"},
    "OGG · 128 kbps equivalente": {"en": "OGG · 128 kbps equivalent", "pt": "OGG · equivalente a 128 kbps", "fr": "OGG · équivalent 128 kbps", "de": "OGG · entspricht 128 kbit/s", "it": "OGG · equivalente a 128 kbps"},
    "WMA · 128 kbps": {"en": "WMA · 128 kbps", "pt": "WMA · 128 kbps", "fr": "WMA · 128 kbps", "de": "WMA · 128 kbit/s", "it": "WMA · 128 kbps"},
    "Preparando exportación…": {"en": "Preparing export…", "pt": "Preparando exportação…", "fr": "Préparation de l’exportation…", "de": "Export wird vorbereitet…", "it": "Preparazione esportazione…"},
    "Ya hay una exportación en curso.": {"en": "An export is already in progress.", "pt": "Já há uma exportação em andamento.", "fr": "Une exportation est déjà en cours.", "de": "Ein Export wird bereits ausgeführt.", "it": "È già in corso un’esportazione."},
    "La lista no contiene pistas.": {"en": "The playlist contains no tracks.", "pt": "A playlist não contém faixas.", "fr": "La liste ne contient aucune piste.", "de": "Die Wiedergabeliste enthält keine Titel.", "it": "La playlist non contiene brani."},
    "Exportación cancelada.": {"en": "Export cancelled.", "pt": "Exportação cancelada.", "fr": "Exportation annulée.", "de": "Export abgebrochen.", "it": "Esportazione annullata."},
    "Se copiaron": {"en": "Copied", "pt": "Foram copiadas", "fr": "Copié", "de": "Kopiert:", "it": "Copiati"},
    "en:": {"en": "to:", "pt": "em:", "fr": "vers :", "de": "nach:", "it": "in:"},
    "Playlist exportada como compilación.": {"en": "Playlist exported as a compilation.", "pt": "Playlist exportada como compilação.", "fr": "Liste exportée comme compilation.", "de": "Wiedergabeliste als Kompilation exportiert.", "it": "Playlist esportata come raccolta."},
    "No se pudieron exportar": {"en": "Could not export", "pt": "Não foi possível exportar", "fr": "Impossible d’exporter", "de": "Export nicht möglich für", "it": "Impossibile esportare"},
    "Exportación terminada": {"en": "Export complete", "pt": "Exportação concluída", "fr": "Exportation terminée", "de": "Export abgeschlossen", "it": "Esportazione completata"},
    "No se pudo exportar": {"en": "Could not export", "pt": "Não foi possível exportar", "fr": "Échec de l’exportation", "de": "Export fehlgeschlagen", "it": "Esportazione non riuscita"},
    "Nueva lista": {"en": "New playlist", "pt": "Nova playlist", "fr": "Nouvelle liste", "de": "Neue Wiedergabeliste", "it": "Nuova playlist"},
    "Apoyar Vinqelo": {"en": "Support Vinqelo", "pt": "Apoiar Vinqelo", "fr": "Soutenir Vinqelo", "de": "Vinqelo unterstützen", "it": "Sostieni Vinqelo"},
    "Estilo:": {"en": "Style:", "pt": "Estilo:", "fr": "Style :", "de": "Stil:", "it": "Stile:"},
    "Tamaño de la tipografía:": {"en": "Font size:", "pt": "Tamanho da fonte:", "fr": "Taille de police :", "de": "Schriftgröße:", "it": "Dimensione carattere:"},
    "Idioma de la interfaz:": {"en": "Interface language:", "pt": "Idioma da interface:", "fr": "Langue de l’interface :", "de": "Oberflächensprache:", "it": "Lingua dell’interfaccia:"},
    "Duración del crossfade:": {"en": "Crossfade duration:", "pt": "Duração do crossfade:", "fr": "Durée du fondu :", "de": "Crossfade-Dauer:", "it": "Durata crossfade:"},
    "Superponer el final y el inicio de las pistas": {"en": "Overlap the end and start of tracks", "pt": "Sobrepor o final e o início das faixas", "fr": "Superposer la fin et le début des pistes", "de": "Titelenden und -anfänge überblenden", "it": "Sovrapponi fine e inizio dei brani"},
    "Se aplica al cambio automático entre pistas de la cola.": {"en": "Applies to automatic track changes in the queue.", "pt": "Aplica-se à mudança automática entre faixas da fila.", "fr": "S’applique au passage automatique entre les pistes de la file.", "de": "Gilt für automatische Titelwechsel in der Warteschlange.", "it": "Si applica al cambio automatico tra i brani in coda."},
    "Tu música y actividad de reproducción en un solo lugar.": {"en": "Your music and listening activity in one place.", "pt": "Sua música e atividade de reprodução em um só lugar.", "fr": "Votre musique et votre activité d’écoute au même endroit.", "de": "Deine Musik und Höraktivität an einem Ort.", "it": "La tua musica e l’attività di ascolto in un unico posto."},
    "Abrir un archivo": {"en": "Open a file", "pt": "Abrir um arquivo", "fr": "Ouvrir un fichier", "de": "Datei öffnen", "it": "Apri un file"},
    "Actualizar biblioteca": {"en": "Update library", "pt": "Atualizar biblioteca", "fr": "Actualiser la bibliothèque", "de": "Bibliothek aktualisieren", "it": "Aggiorna libreria"},
    "Agregar raíz de biblioteca": {"en": "Add library root", "pt": "Adicionar raiz da biblioteca", "fr": "Ajouter un dossier racine", "de": "Bibliotheksstamm hinzufügen", "it": "Aggiungi cartella principale"},
    "ARTISTAS MÁS ESCUCHADOS": {"en": "MOST LISTENED ARTISTS", "pt": "ARTISTAS MAIS OUVIDOS", "fr": "ARTISTES LES PLUS ÉCOUTÉS", "de": "MEISTGEHÖRTE KÜNSTLER", "it": "ARTISTI PIÙ ASCOLTATI"},
    "CANCIONES MÁS ESCUCHADAS": {"en": "MOST LISTENED TRACKS", "pt": "MÚSICAS MAIS OUVIDAS", "fr": "TITRES LES PLUS ÉCOUTÉS", "de": "MEISTGEHÖRTE TITEL", "it": "BRANI PIÙ ASCOLTATI"},
    "CANCIÓN": {"en": "TRACK", "pt": "MÚSICA", "fr": "TITRE", "de": "TITEL", "it": "BRANO"},
    "TÍTULO": {"en": "TITLE", "pt": "TÍTULO", "fr": "TITRE", "de": "TITEL", "it": "TITOLO"},
    "ARTISTA": {"en": "ARTIST", "pt": "ARTISTA", "fr": "ARTISTE", "de": "KÜNSTLER", "it": "ARTISTA"},
    "ÁLBUM": {"en": "ALBUM", "pt": "ÁLBUM", "fr": "ALBUM", "de": "ALBUM", "it": "ALBUM"},
    "DURACIÓN": {"en": "DURATION", "pt": "DURAÇÃO", "fr": "DURÉE", "de": "DAUER", "it": "DURATA"},
    "TIPO": {"en": "TYPE", "pt": "TIPO", "fr": "TYPE", "de": "TYP", "it": "TIPO"},
    "TIEMPO": {"en": "TIME", "pt": "TEMPO", "fr": "TEMPS", "de": "ZEIT", "it": "TEMPO"},
    "TIEMPO ESCUCHADO": {"en": "LISTENING TIME", "pt": "TEMPO OUVIDO", "fr": "TEMPS D’ÉCOUTE", "de": "HÖRZEIT", "it": "TEMPO DI ASCOLTO"},
    "ESTADO": {"en": "STATUS", "pt": "ESTADO", "fr": "ÉTAT", "de": "STATUS", "it": "STATO"},
    "PISTAS": {"en": "TRACKS", "pt": "FAIXAS", "fr": "PISTES", "de": "TITEL", "it": "BRANI"},
    "LISTA DE TEMAS": {"en": "TRACK LIST", "pt": "LISTA DE FAIXAS", "fr": "LISTE DES TITRES", "de": "TITELLISTE", "it": "ELENCO BRANI"},
    "ÁLBUMES Y PISTAS": {"en": "ALBUMS AND TRACKS", "pt": "ÁLBUNS E FAIXAS", "fr": "ALBUMS ET PISTES", "de": "ALBEN UND TITEL", "it": "ALBUM E BRANI"},
    "Artistas definidos por las carpetas de tu biblioteca.": {"en": "Artists defined by your library folders.", "pt": "Artistas definidos pelas pastas da sua biblioteca.", "fr": "Artistes définis par les dossiers de votre bibliothèque.", "de": "Künstler, die durch deine Bibliotheksordner definiert sind.", "it": "Artisti definiti dalle cartelle della libreria."},
    "Portadas organizadas por las carpetas de tu biblioteca.": {"en": "Covers organized by your library folders.", "pt": "Capas organizadas pelas pastas da sua biblioteca.", "fr": "Pochettes organisées selon les dossiers de votre bibliothèque.", "de": "Cover nach deinen Bibliotheksordnern sortiert.", "it": "Copertine organizzate per cartelle della libreria."},
    "Navega como en el Explorador y abre las carpetas con doble clic.": {"en": "Browse like File Explorer and open folders with a double-click.", "pt": "Navegue como no Explorador e abra pastas com duplo clique.", "fr": "Parcourez comme dans l’Explorateur et ouvrez les dossiers par double-clic.", "de": "Wie im Explorer navigieren und Ordner per Doppelklick öffnen.", "it": "Naviga come in Esplora file e apri le cartelle con un doppio clic."},
    "La pista actual y todo lo que sonará después.": {"en": "The current track and everything that will play next.", "pt": "A faixa atual e tudo o que tocará depois.", "fr": "La piste actuelle et tout ce qui sera lu ensuite.", "de": "Der aktuelle Titel und alles, was danach abgespielt wird.", "it": "Il brano attuale e tutto ciò che verrà riprodotto dopo."},
    "Encuentra una canción, artista o álbum en toda la biblioteca.": {"en": "Find a track, artist, or album in the entire library.", "pt": "Encontre uma música, artista ou álbum em toda a biblioteca.", "fr": "Trouvez un titre, un artiste ou un album dans toute la bibliothèque.", "de": "Titel, Künstler oder Album in der gesamten Bibliothek finden.", "it": "Trova un brano, artista o album in tutta la libreria."},
    "Listas automáticas ordenadas por tiempo acumulado de reproducción.": {"en": "Automatic playlists sorted by accumulated listening time.", "pt": "Playlists automáticas ordenadas pelo tempo acumulado de reprodução.", "fr": "Listes automatiques triées par temps d’écoute cumulé.", "de": "Automatische Wiedergabelisten nach gesamter Hörzeit sortiert.", "it": "Playlist automatiche ordinate per tempo di ascolto accumulato."},
    "Crea tus propias listas y conserva el orden de reproducción.": {"en": "Create your own playlists and preserve playback order.", "pt": "Crie suas próprias playlists e preserve a ordem de reprodução.", "fr": "Créez vos listes et conservez l’ordre de lecture.", "de": "Eigene Wiedergabelisten erstellen und Reihenfolge beibehalten.", "it": "Crea le tue playlist e conserva l’ordine di riproduzione."},
    "Buscar artistas…": {"en": "Search artists…", "pt": "Pesquisar artistas…", "fr": "Rechercher des artistes…", "de": "Künstler suchen…", "it": "Cerca artisti…"},
    "Buscar álbum o pista de este artista…": {"en": "Search this artist's albums or tracks…", "pt": "Pesquisar álbum ou faixa deste artista…", "fr": "Rechercher un album ou une piste de cet artiste…", "de": "Album oder Titel dieses Künstlers suchen…", "it": "Cerca album o brano di questo artista…"},
    "Buscar dentro de este álbum…": {"en": "Search within this album…", "pt": "Pesquisar neste álbum…", "fr": "Rechercher dans cet album…", "de": "In diesem Album suchen…", "it": "Cerca in questo album…"},
    "Buscar en esta carpeta": {"en": "Search this folder", "pt": "Pesquisar nesta pasta", "fr": "Rechercher dans ce dossier", "de": "Diesen Ordner durchsuchen", "it": "Cerca in questa cartella"},
    "Buscar canción, artista o álbum…": {"en": "Search track, artist, or album…", "pt": "Pesquisar música, artista ou álbum…", "fr": "Rechercher un titre, un artiste ou un album…", "de": "Titel, Künstler oder Album suchen…", "it": "Cerca brano, artista o album…"},
    "Reproducir artista": {"en": "Play artist", "pt": "Reproduzir artista", "fr": "Lire l’artiste", "de": "Künstler wiedergeben", "it": "Riproduci artista"},
    "Reproducir álbum": {"en": "Play album", "pt": "Reproduzir álbum", "fr": "Lire l’album", "de": "Album wiedergeben", "it": "Riproduci album"},
    "Reproducir carpeta completa": {"en": "Play entire folder", "pt": "Reproduzir pasta inteira", "fr": "Lire tout le dossier", "de": "Ganzen Ordner wiedergeben", "it": "Riproduci intera cartella"},
    "Añadir a la cola": {"en": "Add to queue", "pt": "Adicionar à fila", "fr": "Ajouter à la file", "de": "Zur Warteschlange hinzufügen", "it": "Aggiungi alla coda"},
    "Añadir a lista de reproducción…": {"en": "Add to playlist…", "pt": "Adicionar à playlist…", "fr": "Ajouter à une liste…", "de": "Zur Wiedergabeliste hinzufügen…", "it": "Aggiungi alla playlist…"},
    "Quitar de esta lista": {"en": "Remove from this playlist", "pt": "Remover desta playlist", "fr": "Retirer de cette liste", "de": "Aus dieser Wiedergabeliste entfernen", "it": "Rimuovi da questa playlist"},
    "Eliminar lista": {"en": "Delete playlist", "pt": "Excluir playlist", "fr": "Supprimer la liste", "de": "Wiedergabeliste löschen", "it": "Elimina playlist"},
    "Marcar como compilación": {"en": "Mark as compilation", "pt": "Marcar como compilação", "fr": "Marquer comme compilation", "de": "Als Kompilation markieren", "it": "Segna come raccolta"},
    "Reproducir todos los álbumes": {"en": "Play all albums", "pt": "Reproduzir todos os álbuns", "fr": "Lire tous les albums", "de": "Alle Alben wiedergeben", "it": "Riproduci tutti gli album"},
    "Buscar foto en internet…": {"en": "Search for photo online…", "pt": "Buscar foto na internet…", "fr": "Rechercher une photo en ligne…", "de": "Foto im Internet suchen…", "it": "Cerca foto online…"},
    "Buscar una foto en el equipo…": {"en": "Choose a photo from this computer…", "pt": "Escolher uma foto no computador…", "fr": "Choisir une photo sur l’ordinateur…", "de": "Foto auf dem Computer auswählen…", "it": "Scegli una foto dal computer…"},
    "Buscar carátula en internet…": {"en": "Search for cover online…", "pt": "Buscar capa na internet…", "fr": "Rechercher une pochette en ligne…", "de": "Cover im Internet suchen…", "it": "Cerca copertina online…"},
    "Buscar una carátula en el equipo…": {"en": "Choose a cover from this computer…", "pt": "Escolher uma capa no computador…", "fr": "Choisir une pochette sur l’ordinateur…", "de": "Cover auf dem Computer auswählen…", "it": "Scegli una copertina dal computer…"},
    "Ver foto en grande": {"en": "View large photo", "pt": "Ver foto ampliada", "fr": "Afficher la photo en grand", "de": "Großes Foto anzeigen", "it": "Visualizza foto grande"},
    "Ver carátula en grande": {"en": "View large cover", "pt": "Ver capa ampliada", "fr": "Afficher la pochette en grand", "de": "Großes Cover anzeigen", "it": "Visualizza copertina grande"},
    "Editar título de la pista…": {"en": "Edit track title…", "pt": "Editar título da faixa…", "fr": "Modifier le titre de la piste…", "de": "Titelnamen bearbeiten…", "it": "Modifica titolo del brano…"},
    "Buscar datos del álbum en internet…": {"en": "Search for album data online…", "pt": "Buscar dados do álbum na internet…", "fr": "Rechercher les données de l’album en ligne…", "de": "Albumdaten im Internet suchen…", "it": "Cerca dati album online…"},
    "Selecciona o crea una lista": {"en": "Select or create a playlist", "pt": "Selecione ou crie uma playlist", "fr": "Sélectionnez ou créez une liste", "de": "Wiedergabeliste auswählen oder erstellen", "it": "Seleziona o crea una playlist"},
    "Ninguna pista seleccionada": {"en": "No track selected", "pt": "Nenhuma faixa selecionada", "fr": "Aucune piste sélectionnée", "de": "Kein Titel ausgewählt", "it": "Nessun brano selezionato"},
    "Abre un archivo para comenzar": {"en": "Open a file to begin", "pt": "Abra um arquivo para começar", "fr": "Ouvrez un fichier pour commencer", "de": "Zum Starten eine Datei öffnen", "it": "Apri un file per iniziare"},
    "Álbum desconocido": {"en": "Unknown album", "pt": "Álbum desconhecido", "fr": "Album inconnu", "de": "Unbekanntes Album", "it": "Album sconosciuto"},
    "TIPO Y CALIDAD DEL ARCHIVO": {"en": "FILE TYPE AND QUALITY", "pt": "TIPO E QUALIDADE DO ARQUIVO", "fr": "TYPE ET QUALITÉ DU FICHIER", "de": "DATEITYP UND QUALITÄT", "it": "TIPO E QUALITÀ DEL FILE"},
    "VOLUMEN": {"en": "VOLUME", "pt": "VOLUME", "fr": "VOLUME", "de": "LAUTSTÄRKE", "it": "VOLUME"},
    "Ir a la pista en reproducción": {"en": "Go to the playing track", "pt": "Ir para a faixa em reprodução", "fr": "Aller à la piste en cours", "de": "Zum laufenden Titel", "it": "Vai al brano in riproduzione"},
    "Carátula del álbum": {"en": "Album cover", "pt": "Capa do álbum", "fr": "Pochette de l’album", "de": "Albumcover", "it": "Copertina album"},
    "Buscando carátula oficial…": {"en": "Searching for official cover…", "pt": "Buscando capa oficial…", "fr": "Recherche de la pochette officielle…", "de": "Offizielles Cover wird gesucht…", "it": "Ricerca della copertina ufficiale…"},
    "No se encontró una carátula para este álbum": {"en": "No cover was found for this album", "pt": "Nenhuma capa foi encontrada para este álbum", "fr": "Aucune pochette trouvée pour cet album", "de": "Für dieses Album wurde kein Cover gefunden", "it": "Nessuna copertina trovata per questo album"},
    "Pista anterior": {"en": "Previous track", "pt": "Faixa anterior", "fr": "Piste précédente", "de": "Vorheriger Titel", "it": "Brano precedente"},
    "Pista siguiente": {"en": "Next track", "pt": "Próxima faixa", "fr": "Piste suivante", "de": "Nächster Titel", "it": "Brano successivo"},
    "Reproducir o pausar": {"en": "Play or pause", "pt": "Reproduzir ou pausar", "fr": "Lire ou mettre en pause", "de": "Wiedergeben oder pausieren", "it": "Riproduci o pausa"},
    "Repetir una pista": {"en": "Repeat one track", "pt": "Repetir uma faixa", "fr": "Répéter une piste", "de": "Einen Titel wiederholen", "it": "Ripeti un brano"},
    "Repetir carpeta o lista": {"en": "Repeat folder or playlist", "pt": "Repetir pasta ou playlist", "fr": "Répéter le dossier ou la liste", "de": "Ordner oder Liste wiederholen", "it": "Ripeti cartella o playlist"},
    "Reproducción aleatoria": {"en": "Shuffle", "pt": "Reprodução aleatória", "fr": "Lecture aléatoire", "de": "Zufallswiedergabe", "it": "Riproduzione casuale"},
    "Repetición desactivada": {"en": "Repeat off", "pt": "Repetição desativada", "fr": "Répétition désactivée", "de": "Wiederholung aus", "it": "Ripetizione disattivata"},
    "Repetir carpeta o álbum": {"en": "Repeat folder or album", "pt": "Repetir pasta ou álbum", "fr": "Répéter le dossier ou l’album", "de": "Ordner oder Album wiederholen", "it": "Ripeti cartella o album"},
    "Repetir artista": {"en": "Repeat artist", "pt": "Repetir artista", "fr": "Répéter l’artiste", "de": "Künstler wiederholen", "it": "Ripeti artista"},
    "Aleatorio desactivado": {"en": "Shuffle off", "pt": "Aleatório desativado", "fr": "Lecture aléatoire désactivée", "de": "Zufallswiedergabe aus", "it": "Riproduzione casuale disattivata"},
    "Aleatorio en carpeta o álbum": {"en": "Shuffle folder or album", "pt": "Aleatório na pasta ou álbum", "fr": "Lecture aléatoire du dossier ou de l’album", "de": "Ordner oder Album zufällig", "it": "Casuale nella cartella o album"},
    "Aleatorio por artista": {"en": "Shuffle artist", "pt": "Aleatório por artista", "fr": "Lecture aléatoire par artiste", "de": "Künstler zufällig", "it": "Casuale per artista"},
    "Aleatorio global": {"en": "Global shuffle", "pt": "Aleatório global", "fr": "Lecture aléatoire globale", "de": "Globale Zufallswiedergabe", "it": "Casuale globale"},
    "Reproducida": {"en": "Played", "pt": "Reproduzida", "fr": "Lue", "de": "Abgespielt", "it": "Riprodotta"},
    "▶  Sonando": {"en": "▶  Playing", "pt": "▶  Tocando", "fr": "▶  En cours", "de": "▶  Wiedergabe", "it": "▶  In riproduzione"},
    "En cola": {"en": "Queued", "pt": "Na fila", "fr": "En file", "de": "In Warteschlange", "it": "In coda"},
    "Desactivado": {"en": "Off", "pt": "Desativado", "fr": "Désactivé", "de": "Aus", "it": "Disattivato"},
    "Una pista": {"en": "One track", "pt": "Uma faixa", "fr": "Une piste", "de": "Ein Titel", "it": "Un brano"},
    "Carpeta o álbum": {"en": "Folder or album", "pt": "Pasta ou álbum", "fr": "Dossier ou album", "de": "Ordner oder Album", "it": "Cartella o album"},
    "Artista": {"en": "Artist", "pt": "Artista", "fr": "Artiste", "de": "Künstler", "it": "Artista"},
    "Biblioteca global": {"en": "Entire library", "pt": "Biblioteca inteira", "fr": "Bibliothèque entière", "de": "Gesamte Bibliothek", "it": "Intera libreria"},
    "Carpeta o lista actual": {"en": "Current folder or playlist", "pt": "Pasta ou playlist atual", "fr": "Dossier ou liste actuelle", "de": "Aktueller Ordner oder Wiedergabeliste", "it": "Cartella o playlist attuale"},
    "Repetir carpeta o lista actual": {"en": "Repeat current folder or playlist", "pt": "Repetir pasta ou playlist atual", "fr": "Répéter le dossier ou la liste actuelle", "de": "Aktuellen Ordner oder Wiedergabeliste wiederholen", "it": "Ripeti cartella o playlist attuale"},
    "Aleatorio en carpeta o lista actual": {"en": "Shuffle current folder or playlist", "pt": "Aleatório na pasta ou playlist atual", "fr": "Lecture aléatoire du dossier ou de la liste actuelle", "de": "Aktuellen Ordner oder Wiedergabeliste zufällig wiedergeben", "it": "Casuale nella cartella o playlist attuale"},
    "Aún no hay reproducciones. Tu actividad aparecerá aquí.": {"en": "No plays yet. Your activity will appear here.", "pt": "Ainda não há reproduções. Sua atividade aparecerá aqui.", "fr": "Aucune lecture pour le moment. Votre activité apparaîtra ici.", "de": "Noch keine Wiedergaben. Deine Aktivität erscheint hier.", "it": "Ancora nessuna riproduzione. La tua attività apparirà qui."},
    "Apoyar el desarrollo de Vinqelo": {"en": "Support Vinqelo development", "pt": "Apoiar o desenvolvimento do Vinqelo", "fr": "Soutenir le développement de Vinqelo", "de": "Die Entwicklung von Vinqelo unterstützen", "it": "Sostieni lo sviluppo di Vinqelo"},
    "Las contribuciones son voluntarias y ayudan a mantener el proyecto. No desbloquean funciones adicionales.": {"en": "Contributions are voluntary and help maintain the project. They do not unlock additional features.", "pt": "As contribuições são voluntárias e ajudam a manter o projeto. Não desbloqueiam recursos adicionais.", "fr": "Les contributions sont volontaires et aident à maintenir le projet. Elles ne débloquent aucune fonction supplémentaire.", "de": "Beiträge sind freiwillig und helfen, das Projekt zu pflegen. Sie schalten keine zusätzlichen Funktionen frei.", "it": "I contributi sono volontari e aiutano a mantenere il progetto. Non sbloccano funzioni aggiuntive."},
    "Escanea desde la aplicación de Binance": {"en": "Scan with the Binance app", "pt": "Escaneie com o aplicativo Binance", "fr": "Scannez avec l’application Binance", "de": "Mit der Binance-App scannen", "it": "Scansiona con l’app Binance"},
    "Copiar dirección": {"en": "Copy address", "pt": "Copiar endereço", "fr": "Copier l’adresse", "de": "Adresse kopieren", "it": "Copia indirizzo"},
    "Dirección copiada": {"en": "Address copied", "pt": "Endereço copiado", "fr": "Adresse copiée", "de": "Adresse kopiert", "it": "Indirizzo copiato"},
    "Apoyar mediante Ko-fi": {"en": "Support via Ko-fi", "pt": "Apoiar pelo Ko-fi", "fr": "Soutenir via Ko-fi", "de": "Über Ko-fi unterstützen", "it": "Sostieni tramite Ko-fi"},
    "Abre la página oficial de Vinqelo en Ko-fi para realizar un aporte.": {"en": "Open Vinqelo's official Ko-fi page to make a contribution.", "pt": "Abra a página oficial do Vinqelo no Ko-fi para contribuir.", "fr": "Ouvrez la page Ko-fi officielle de Vinqelo pour contribuer.", "de": "Öffne die offizielle Ko-fi-Seite von Vinqelo, um beizutragen.", "it": "Apri la pagina Ko-fi ufficiale di Vinqelo per contribuire."},
    "Abrir Ko-fi": {"en": "Open Ko-fi", "pt": "Abrir Ko-fi", "fr": "Ouvrir Ko-fi", "de": "Ko-fi öffnen", "it": "Apri Ko-fi"},
    "QR no disponible": {"en": "QR unavailable", "pt": "QR indisponível", "fr": "QR indisponible", "de": "QR nicht verfügbar", "it": "QR non disponibile"},
    "Aplicar títulos": {"en": "Apply titles", "pt": "Aplicar títulos", "fr": "Appliquer les titres", "de": "Titel anwenden", "it": "Applica titoli"},
    "Buscando ediciones musicales…": {"en": "Searching music releases…", "pt": "Buscando edições musicais…", "fr": "Recherche des éditions musicales…", "de": "Musikveröffentlichungen werden gesucht…", "it": "Ricerca delle edizioni musicali…"},
    "Buscando opciones…": {"en": "Searching options…", "pt": "Buscando opções…", "fr": "Recherche d’options…", "de": "Optionen werden gesucht…", "it": "Ricerca opzioni…"},
    "Buscar datos oficiales del álbum": {"en": "Search official album data", "pt": "Buscar dados oficiais do álbum", "fr": "Rechercher les données officielles de l’album", "de": "Offizielle Albumdaten suchen", "it": "Cerca dati ufficiali dell’album"},
    "Buscar de nuevo": {"en": "Search again", "pt": "Buscar novamente", "fr": "Rechercher à nouveau", "de": "Erneut suchen", "it": "Cerca di nuovo"},
    "Buscar imagen en internet": {"en": "Search image online", "pt": "Buscar imagem na internet", "fr": "Rechercher une image en ligne", "de": "Bild im Internet suchen", "it": "Cerca immagine online"},
    "Cargando lista oficial de pistas…": {"en": "Loading official track list…", "pt": "Carregando lista oficial de faixas…", "fr": "Chargement de la liste officielle des pistes…", "de": "Offizielle Titelliste wird geladen…", "it": "Caricamento elenco ufficiale dei brani…"},
    "Consola de sonido": {"en": "Sound console", "pt": "Console de som", "fr": "Console audio", "de": "Audiokonsole", "it": "Console audio"},
    "Continuar": {"en": "Continue", "pt": "Continuar", "fr": "Continuer", "de": "Weiter", "it": "Continua"},
    "Efectos · Vinqelo Player": {"en": "Effects · Vinqelo Player", "pt": "Efeitos · Vinqelo Player", "fr": "Effets · Vinqelo Player", "de": "Effekte · Vinqelo Player", "it": "Effetti · Vinqelo Player"},
    "Efectos: preamplificador y ecualizador": {"en": "Effects: preamp and equalizer", "pt": "Efeitos: pré-amplificador e equalizador", "fr": "Effets : préampli et égaliseur", "de": "Effekte: Vorverstärker und Equalizer", "it": "Effetti: preamplificatore ed equalizzatore"},
    "Elige una imagen": {"en": "Choose an image", "pt": "Escolha uma imagem", "fr": "Choisissez une image", "de": "Bild auswählen", "it": "Scegli un’immagine"},
    "Exportando playlist": {"en": "Exporting playlist", "pt": "Exportando playlist", "fr": "Exportation de la liste", "de": "Wiedergabeliste wird exportiert", "it": "Esportazione playlist"},
    "Exportar como compilacion...": {"en": "Export as compilation…", "pt": "Exportar como compilação…", "fr": "Exporter comme compilation…", "de": "Als Kompilation exportieren…", "it": "Esporta come raccolta…"},
    "No se encontraron imágenes. Prueba otra búsqueda.": {"en": "No images found. Try another search.", "pt": "Nenhuma imagem encontrada. Tente outra busca.", "fr": "Aucune image trouvée. Essayez une autre recherche.", "de": "Keine Bilder gefunden. Versuche eine andere Suche.", "it": "Nessuna immagine trovata. Prova un’altra ricerca."},
    "Perfil: IrQv8": {"en": "Profile: IrQv8", "pt": "Perfil: IrQv8", "fr": "Profil : IrQv8", "de": "Profil: IrQv8", "it": "Profilo: IrQv8"},
    "Preamplificador y ecualizador configurable de 6 bandas sobre VLC.": {"en": "Configurable preamp and 6-band equalizer powered by VLC.", "pt": "Pré-amplificador e equalizador configurável de 6 bandas com VLC.", "fr": "Préampli et égaliseur 6 bandes configurables avec VLC.", "de": "Konfigurierbarer Vorverstärker und 6-Band-Equalizer mit VLC.", "it": "Preamplificatore ed equalizzatore configurabile a 6 bande con VLC."},
    "El Preamp ofrece −20 a +20 dB y se detiene primero en +6 dB. Suelta y vuelve a moverlo para superar ese punto.": {"en": "The preamp ranges from −20 to +20 dB and pauses first at +6 dB. Release and drag again to go beyond that point.", "pt": "O pré-amplificador vai de −20 a +20 dB e para primeiro em +6 dB. Solte e arraste novamente para ultrapassar esse ponto.", "fr": "Le préampli va de −20 à +20 dB et s’arrête d’abord à +6 dB. Relâchez puis faites glisser à nouveau pour dépasser ce seuil.", "de": "Der Vorverstärker reicht von −20 bis +20 dB und stoppt zunächst bei +6 dB. Loslassen und erneut ziehen, um diesen Punkt zu überschreiten.", "it": "Il preamplificatore va da −20 a +20 dB e si ferma prima a +6 dB. Rilascia e trascina di nuovo per superare quel punto."},
    "Preparando el reproductor…": {"en": "Preparing the player…", "pt": "Preparando o player…", "fr": "Préparation du lecteur…", "de": "Player wird vorbereitet…", "it": "Preparazione del lettore…"},
    "Organizando tu música…": {"en": "Organizing your music…", "pt": "Organizando sua música…", "fr": "Organisation de votre musique…", "de": "Deine Musik wird organisiert…", "it": "Organizzazione della tua musica…"},
    "Casi listo…": {"en": "Almost ready…", "pt": "Quase pronto…", "fr": "Presque prêt…", "de": "Fast fertig…", "it": "Quasi pronto…"},
    "Validando cambios en la biblioteca…": {"en": "Checking library changes…", "pt": "Verificando alterações na biblioteca…", "fr": "Vérification des changements de la bibliothèque…", "de": "Bibliotheksänderungen werden geprüft…", "it": "Verifica delle modifiche alla libreria…"},
    "Actualizando la colección…": {"en": "Updating the collection…", "pt": "Atualizando a coleção…", "fr": "Mise à jour de la collection…", "de": "Sammlung wird aktualisiert…", "it": "Aggiornamento della collezione…"},
    "Organizando los cambios detectados…": {"en": "Organizing detected changes…", "pt": "Organizando as alterações detectadas…", "fr": "Organisation des changements détectés…", "de": "Erkannte Änderungen werden organisiert…", "it": "Organizzazione delle modifiche rilevate…"},
    "Preparando la colección…": {"en": "Preparing the collection…", "pt": "Preparando a coleção…", "fr": "Préparation de la collection…", "de": "Sammlung wird vorbereitet…", "it": "Preparazione della collezione…"},
    "Organizando la información…": {"en": "Organizing information…", "pt": "Organizando as informações…", "fr": "Organisation des informations…", "de": "Informationen werden organisiert…", "it": "Organizzazione delle informazioni…"},
    "Restablecer consola": {"en": "Reset console", "pt": "Redefinir console", "fr": "Réinitialiser la console", "de": "Konsole zurücksetzen", "it": "Reimposta console"},
    "Seleccionar canciones": {"en": "Select tracks", "pt": "Selecionar músicas", "fr": "Sélectionner les pistes", "de": "Titel auswählen", "it": "Seleziona brani"},
    "Seleccionar todas": {"en": "Select all", "pt": "Selecionar todas", "fr": "Tout sélectionner", "de": "Alle auswählen", "it": "Seleziona tutto"},
    "Listas inteligentes": {"en": "Smart Playlists", "pt": "Playlists inteligentes", "fr": "Listes intelligentes", "de": "Intelligente Wiedergabelisten", "it": "Playlist intelligenti"},
    "Global · Más escuchadas": {"en": "Global · Most listened", "pt": "Global · Mais ouvidas", "fr": "Global · Les plus écoutées", "de": "Global · Meistgehört", "it": "Globale · Più ascoltate"},
    "New · Últimos 30 días": {"en": "New · Last 30 days", "pt": "Novas · Últimos 30 dias", "fr": "Nouveautés · 30 derniers jours", "de": "Neu · Letzte 30 Tage", "it": "Novità · Ultimi 30 giorni"},
    "POR ARTISTA": {"en": "BY ARTIST", "pt": "POR ARTISTA", "fr": "PAR ARTISTE", "de": "NACH KÜNSTLER", "it": "PER ARTISTA"},
    "Aún no hay escuchas suficientes para esta lista.": {"en": "There is not enough listening activity for this playlist yet.", "pt": "Ainda não há reproduções suficientes para esta playlist.", "fr": "Il n’y a pas encore assez d’écoutes pour cette liste.", "de": "Für diese Wiedergabeliste gibt es noch nicht genügend Höraktivität.", "it": "Non ci sono ancora abbastanza ascolti per questa playlist."},
    "TU MÚSICA, A TU MANERA": {"en": "YOUR MUSIC, YOUR WAY", "pt": "SUA MÚSICA, DO SEU JEITO", "fr": "VOTRE MUSIQUE, À VOTRE FAÇON", "de": "DEINE MUSIK, DEIN STIL", "it": "LA TUA MUSICA, A MODO TUO"},
    "Usar esta imagen": {"en": "Use this image", "pt": "Usar esta imagem", "fr": "Utiliser cette image", "de": "Dieses Bild verwenden", "it": "Usa questa immagine"},
    "Validar títulos con MusicBrainz": {"en": "Validate titles with MusicBrainz", "pt": "Validar títulos com MusicBrainz", "fr": "Valider les titres avec MusicBrainz", "de": "Titel mit MusicBrainz prüfen", "it": "Convalida titoli con MusicBrainz"},
    "Ver licencia completa": {"en": "View full license", "pt": "Ver licença completa", "fr": "Voir la licence complète", "de": "Vollständige Lizenz anzeigen", "it": "Visualizza licenza completa"},
    "Ocultar licencia": {"en": "Hide license", "pt": "Ocultar licença", "fr": "Masquer la licence", "de": "Lizenz ausblenden", "it": "Nascondi licenza"},
    "Versión": {"en": "Version", "pt": "Versão", "fr": "Version", "de": "Version", "it": "Versione"},
    "Desarrollado por": {"en": "Developed by", "pt": "Desenvolvido por", "fr": "Développé par", "de": "Entwickelt von", "it": "Sviluppato da"},
    "Licencia": {"en": "License", "pt": "Licença", "fr": "Licence", "de": "Lizenz", "it": "Licenza"},
    "Software libre, distribuido sin garantía, conforme a los términos de la licencia.": {"en": "Free software, distributed without warranty under the license terms.", "pt": "Software livre, distribuído sem garantia, conforme os termos da licença.", "fr": "Logiciel libre, distribué sans garantie conformément aux termes de la licence.", "de": "Freie Software, ohne Gewährleistung gemäß den Lizenzbedingungen verbreitet.", "it": "Software libero, distribuito senza garanzia secondo i termini della licenza."},
    "GNU General Public License, versión 3.0.": {"en": "GNU General Public License, version 3.0.", "pt": "GNU General Public License, versão 3.0.", "fr": "Licence publique générale GNU, version 3.0.", "de": "GNU General Public License, Version 3.0.", "it": "GNU General Public License, versione 3.0."},
    "CARPETA / PISTA": {"en": "FOLDER / TRACK", "pt": "PASTA / FAIXA", "fr": "DOSSIER / PISTE", "de": "ORDNER / TITEL", "it": "CARTELLA / BRANO"},
    "RUTA / ARTISTA": {"en": "PATH / ARTIST", "pt": "CAMINHO / ARTISTA", "fr": "CHEMIN / ARTISTE", "de": "PFAD / KÜNSTLER", "it": "PERCORSO / ARTISTA"},
    "ÁLBUM / PISTA": {"en": "ALBUM / TRACK", "pt": "ÁLBUM / FAIXA", "fr": "ALBUM / PISTE", "de": "ALBUM / TITEL", "it": "ALBUM / BRANO"},
    "Vinqelo · Azul": {"en": "Vinqelo · Blue", "pt": "Vinqelo · Azul", "fr": "Vinqelo · Bleu", "de": "Vinqelo · Blau", "it": "Vinqelo · Blu"},
    "Clementine · Naranja": {"en": "Clementine · Orange", "pt": "Clementine · Laranja", "fr": "Clementine · Orange", "de": "Clementine · Orange", "it": "Clementine · Arancione"},
    "Amarok · Morado": {"en": "Amarok · Purple", "pt": "Amarok · Roxo", "fr": "Amarok · Violet", "de": "Amarok · Violett", "it": "Amarok · Viola"},
    "Esmeralda": {"en": "Emerald", "pt": "Esmeralda", "fr": "Émeraude", "de": "Smaragd", "it": "Smeraldo"},
    "Grafito": {"en": "Graphite", "pt": "Grafite", "fr": "Graphite", "de": "Graphit", "it": "Grafite"},
    "USDT: Envía solamente USDT mediante BNB Smart Chain (BEP20).": {"en": "USDT: Send USDT only through BNB Smart Chain (BEP20).", "pt": "USDT: Envie somente USDT pela BNB Smart Chain (BEP20).", "fr": "USDT : envoyez uniquement des USDT via BNB Smart Chain (BEP20).", "de": "USDT: Nur USDT über BNB Smart Chain (BEP20) senden.", "it": "USDT: invia solo USDT tramite BNB Smart Chain (BEP20)."},
    "BTC: Este depósito acepta BTC mediante BNB Smart Chain (BEP20), no Bitcoin por su red nativa.": {"en": "BTC: This deposit accepts BTC through BNB Smart Chain (BEP20), not native Bitcoin.", "pt": "BTC: Este depósito aceita BTC pela BNB Smart Chain (BEP20), não pela rede nativa do Bitcoin.", "fr": "BTC : ce dépôt accepte le BTC via BNB Smart Chain (BEP20), pas via le réseau Bitcoin natif.", "de": "BTC: Diese Einzahlung akzeptiert BTC über BNB Smart Chain (BEP20), nicht über das native Bitcoin-Netzwerk.", "it": "BTC: questo deposito accetta BTC tramite BNB Smart Chain (BEP20), non tramite la rete Bitcoin nativa."},
}

REVERSE = {translated: source for source, values in T.items() for translated in values.values()}
LANGUAGES = {"es", "en", "pt", "fr", "de", "it"}
DECORATED_PREFIXES = ("←  ", "▶  ", "+  ")


class TranslationManager(QObject):
    def __init__(self, application: QApplication, language: str = "es") -> None:
        super().__init__(application)
        self.application = application
        self.language = language if language in LANGUAGES else "es"
        application.installEventFilter(self)

    def set_language(self, language: str) -> None:
        self.language = language if language in LANGUAGES else "es"
        for widget in self.application.allWidgets():
            self.apply(widget)

    def _exact(self, text: str) -> str:
        source = REVERSE.get(text, text)
        return source if self.language == "es" else T.get(source, {}).get(self.language, text)

    def translate(self, text: str) -> str:
        if not text:
            return text
        exact = self._exact(text)
        if exact != text or text in T or text in REVERSE:
            return exact

        for prefix in DECORATED_PREFIXES:
            if text.startswith(prefix):
                return prefix + self.translate(text[len(prefix):])

        title_prefix = "Vinqelo Player — "
        if text.startswith(title_prefix):
            return title_prefix + self.translate(text[len(title_prefix):])

        for smart_title in ("Global · Más escuchadas", "New · Últimos 30 días"):
            if text.startswith(smart_title + " ·"):
                translated_title = self._exact(smart_title)
                return translated_title + self.translate(text[len(smart_title):])

        # Frases de conteo generadas por las páginas. Solo se sustituyen cuando
        # contienen números, para no tocar nombres reales de música.
        if re.search(r"\d", text):
            words = {
                "en": {"álbumes": "albums", "álbum": "album", "pistas": "tracks", "pista": "track", "canciones seleccionadas": "songs selected", "de": "of"},
                "pt": {"álbumes": "álbuns", "álbum": "álbum", "pistas": "faixas", "pista": "faixa", "canciones seleccionadas": "músicas selecionadas", "de": "de"},
                "fr": {"álbumes": "albums", "álbum": "album", "pistas": "pistes", "pista": "piste", "canciones seleccionadas": "chansons sélectionnées", "de": "sur"},
                "de": {"álbumes": "Alben", "álbum": "Album", "pistas": "Titel", "pista": "Titel", "canciones seleccionadas": "Titel ausgewählt", "de": "von"},
                "it": {"álbumes": "album", "álbum": "album", "pistas": "brani", "pista": "brano", "canciones seleccionadas": "brani selezionati", "de": "di"},
            }.get(self.language)
            if words:
                result = text
                for source in ("canciones seleccionadas", "álbumes", "álbum", "pistas", "pista"):
                    result = re.sub(rf"\b{re.escape(source)}\b", words[source], result, flags=re.IGNORECASE)
                if re.fullmatch(r"\d+ de \d+ .+", text):
                    result = result.replace(" de ", f" {words['de']} ", 1)
                listened = {"en": "listened", "pt": "ouvidos", "fr": "écoutées", "de": "gehört", "it": "ascoltati"}[self.language]
                if result.endswith(" escuchados"):
                    result = result[:-11] + " " + listened
                return result
        return text

    @staticmethod
    def _source_text(owner: QObject, property_name: str, current: str) -> str:
        """Conserva el español original para cambios de idioma reversibles.

        Es necesario porque varias traducciones válidas coinciden (por ejemplo,
        ``Atrás`` y ``Volver`` son ``Back`` en inglés).
        """
        stored = owner.property(property_name)
        if isinstance(stored, str):
            variants = {stored, *T.get(stored, {}).values()}
            decorated = {prefix + value for prefix in DECORATED_PREFIXES for value in variants}
            titled = {"Vinqelo Player — " + value for value in variants}
            if current in variants | decorated | titled:
                return stored
        source = REVERSE.get(current, current)
        owner.setProperty(property_name, source)
        return source

    def apply(self, widget: QWidget) -> None:
        if isinstance(widget, (QLabel, QAbstractButton)):
            source = self._source_text(widget, "vinqeloSourceText", widget.text())
            widget.setText(self.translate(source))
        if isinstance(widget, QLineEdit):
            source = self._source_text(widget, "vinqeloSourcePlaceholder", widget.placeholderText())
            widget.setPlaceholderText(self.translate(source))
        if isinstance(widget, (QSpinBox, QDoubleSpinBox)) and widget.suffix().strip() == "segundos":
            suffixes = {"es": " segundos", "en": " seconds", "pt": " segundos", "fr": " secondes", "de": " Sekunden", "it": " secondi"}
            widget.setSuffix(suffixes[self.language])
        if isinstance(widget, QComboBox):
            sources = widget.property("vinqeloComboSources")
            if not isinstance(sources, list) or len(sources) != widget.count():
                sources = [REVERSE.get(widget.itemText(index), widget.itemText(index)) for index in range(widget.count())]
                widget.setProperty("vinqeloComboSources", sources)
            for index in range(widget.count()):
                widget.setItemText(index, self.translate(sources[index]))
        if widget.toolTip():
            source = self._source_text(widget, "vinqeloSourceToolTip", widget.toolTip())
            widget.setToolTip(self.translate(source))
        if widget.windowTitle():
            source = self._source_text(widget, "vinqeloSourceWindowTitle", widget.windowTitle())
            widget.setWindowTitle(self.translate(source))
        if isinstance(widget, QTabWidget):
            sources = widget.property("vinqeloTabSources")
            if not isinstance(sources, list) or len(sources) != widget.count():
                sources = [REVERSE.get(widget.tabText(index), widget.tabText(index)) for index in range(widget.count())]
                widget.setProperty("vinqeloTabSources", sources)
            for index in range(widget.count()):
                widget.setTabText(index, self.translate(sources[index]))
        if isinstance(widget, QMenu):
            for action in widget.actions():
                source = self._source_text(action, "vinqeloSourceText", action.text())
                action.setText(self.translate(source))
        if isinstance(widget, QTreeWidget) and widget.headerItem() is not None:
            header = widget.headerItem()
            sources = widget.property("vinqeloHeaderSources")
            if not isinstance(sources, list) or len(sources) != widget.columnCount():
                sources = [REVERSE.get(header.text(column), header.text(column)) for column in range(widget.columnCount())]
                widget.setProperty("vinqeloHeaderSources", sources)
            for column in range(widget.columnCount()):
                header.setText(column, self.translate(sources[column]))
        if isinstance(widget, QListWidget):
            for index in range(widget.count()):
                item = widget.item(index)
                item.setText(self.translate(item.text()))

    def eventFilter(self, watched: object, event: QEvent) -> bool:
        if event.type() in (QEvent.Type.Polish, QEvent.Type.Show) and isinstance(watched, QWidget):
            self.apply(watched)
        if event.type() == QEvent.Type.ActionAdded and isinstance(watched, QWidget):
            action = event.action()
            if isinstance(action, QAction):
                source = self._source_text(action, "vinqeloSourceText", action.text())
                action.setText(self.translate(source))
        return super().eventFilter(watched, event)


def enable_translation(application: QApplication, language: str) -> TranslationManager:
    return TranslationManager(application, language)


def detect_system_language() -> str:
    """Devuelve uno de los idiomas disponibles a partir del idioma de Windows."""
    language = QLocale.system().name().split("_", 1)[0].lower()
    return language if language in LANGUAGES else "en"


def translate_text(text: str) -> str:
    """Traduce contenido dinámico creado después de mostrar una página."""
    application = QApplication.instance()
    manager = getattr(application, "_vinqelo_translation_manager", None)
    return manager.translate(text) if manager is not None else text
