import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const root = path.resolve(process.cwd());
const source = String.raw`C:\Users\IRQV8\Downloads\listingData-9NDKG3757R44-1152921505701453856.csv`;
const importFolderName = "VinqeloStoreImport";
const outputDir = path.join(root, "dist", importFolderName);
const reviewDir = path.join(root, "outputs", "store-listing-localizations");
const csvName = "listingData-9NDKG3757R44-multidioma.csv";
const locales = ["es", "en", "it", "pt", "fr", "de"];

const descriptions = {
  es: `**Vinqelo Player** es un reproductor y organizador de música local para Windows, diseñado para quienes desean conservar el control total de su colección musical.

Importa una carpeta y Vinqelo Player respetará la forma en que has organizado tu música. Los artistas, álbumes y compilaciones se generan a partir de la estructura de carpetas, evitando que metadatos incompletos o etiquetas incorrectas fragmenten la biblioteca. También puedes navegar directamente por tus carpetas, buscar en toda la colección y localizar rápidamente la pista que se está reproduciendo.

Explora tus artistas mediante imágenes y collages creados con las carátulas de sus discos. Consulta álbumes con sus portadas, organiza canciones sueltas dentro de compilaciones y mantén cada elemento en el lugar que le corresponde. Vinqelo Player también puede leer metadatos, localizar carátulas, editar títulos y mantener ordenados los nombres de archivo.

Crea listas de reproducción, añade canciones a una cola editable y utiliza listas inteligentes basadas en el tiempo real de escucha. Los controles incluyen pista anterior, reproducir o pausar, pista siguiente, detener, repetición y reproducción aleatoria dentro de la colección seleccionada.

Vinqelo Player es compatible con MP3, FLAC, WAV, OGG, M4A y AAC. Durante la reproducción muestra duración, progreso, formato, frecuencia de muestreo, tasa de bits y canales. También incorpora preamplificador, ecualizador de seis bandas, volumen persistente y compatibilidad con las teclas multimedia de Windows.

Tus archivos de audio, biblioteca, estadísticas y preferencias permanecen almacenados localmente. Las consultas en Internet para buscar carátulas o completar metadatos son opcionales y nunca envían tus archivos de audio.`,
  en: `**Vinqelo Player** is a local music player and organizer for Windows, designed for listeners who want full control over their own music collection.

Import a folder and Vinqelo Player will respect the way your music is organized. Artists, albums, and compilations are created from the folder structure, preventing incomplete metadata or incorrect tags from fragmenting the library. You can also browse folders directly, search the entire collection, and quickly locate the track currently playing.

Explore artists through images and collages made from their album artwork. Browse albums with their covers, keep loose songs organized inside compilations, and preserve everything in its proper place. Vinqelo Player can also read metadata, locate artwork, edit titles, and keep file names organized.

Create playlists, add songs to an editable queue, and use smart playlists based on actual listening time. Playback controls include previous track, play or pause, next track, stop, repeat, and shuffle within the selected collection.

Vinqelo Player supports MP3, FLAC, WAV, OGG, M4A, and AAC. During playback it displays duration, progress, format, sample rate, bitrate, and channels. It also includes a preamplifier, six-band equalizer, persistent volume, and support for Windows media keys.

Your audio files, library, statistics, and preferences remain stored locally. Optional Internet requests for artwork or metadata never upload your audio files.`,
  it: `**Vinqelo Player** è un lettore e organizzatore di musica locale per Windows, pensato per chi desidera mantenere il pieno controllo della propria raccolta musicale.

Importa una cartella e Vinqelo Player rispetterà il modo in cui hai organizzato la musica. Artisti, album e compilation vengono creati dalla struttura delle cartelle, evitando che metadati incompleti o tag errati frammentino la libreria. Puoi anche esplorare direttamente le cartelle, cercare nell'intera raccolta e individuare rapidamente il brano in riproduzione.

Esplora gli artisti tramite immagini e collage creati dalle copertine dei loro album. Consulta gli album con le rispettive copertine, organizza i brani singoli nelle compilation e conserva ogni elemento al posto giusto. Vinqelo Player può inoltre leggere i metadati, trovare copertine, modificare i titoli e mantenere ordinati i nomi dei file.

Crea playlist, aggiungi brani a una coda modificabile e usa playlist intelligenti basate sul tempo di ascolto effettivo. I controlli includono brano precedente, riproduzione o pausa, brano successivo, arresto, ripetizione e riproduzione casuale nella raccolta selezionata.

Vinqelo Player supporta MP3, FLAC, WAV, OGG, M4A e AAC. Durante la riproduzione mostra durata, avanzamento, formato, frequenza di campionamento, bitrate e canali. Include inoltre preamplificatore, equalizzatore a sei bande, volume persistente e supporto per i tasti multimediali di Windows.

I file audio, la libreria, le statistiche e le preferenze restano archiviati localmente. Le ricerche facoltative su Internet per copertine o metadati non inviano mai i file audio.`,
  pt: `**Vinqelo Player** é um reprodutor e organizador de música local para Windows, criado para quem deseja manter controle total sobre a própria coleção musical.

Importe uma pasta e o Vinqelo Player respeitará a forma como sua música está organizada. Artistas, álbuns e coletâneas são criados a partir da estrutura de pastas, evitando que metadados incompletos ou etiquetas incorretas fragmentem a biblioteca. Você também pode navegar diretamente pelas pastas, pesquisar em toda a coleção e localizar rapidamente a faixa que está tocando.

Explore artistas por meio de imagens e colagens criadas com as capas de seus álbuns. Consulte álbuns com suas capas, organize músicas avulsas dentro de coletâneas e mantenha cada item no lugar correto. O Vinqelo Player também pode ler metadados, localizar capas, editar títulos e manter os nomes dos arquivos organizados.

Crie playlists, adicione músicas a uma fila editável e use playlists inteligentes baseadas no tempo real de audição. Os controles incluem faixa anterior, reproduzir ou pausar, próxima faixa, parar, repetir e reprodução aleatória dentro da coleção selecionada.

O Vinqelo Player é compatível com MP3, FLAC, WAV, OGG, M4A e AAC. Durante a reprodução, mostra duração, progresso, formato, taxa de amostragem, taxa de bits e canais. Também inclui pré-amplificador, equalizador de seis bandas, volume persistente e suporte às teclas multimídia do Windows.

Seus arquivos de áudio, biblioteca, estatísticas e preferências permanecem armazenados localmente. As consultas opcionais na Internet para capas ou metadados nunca enviam seus arquivos de áudio.`,
  fr: `**Vinqelo Player** est un lecteur et un gestionnaire de musique locale pour Windows, conçu pour les personnes qui souhaitent garder le contrôle total de leur collection musicale.

Importez un dossier et Vinqelo Player respectera l'organisation de votre musique. Les artistes, albums et compilations sont créés à partir de la structure des dossiers, afin d'éviter que des métadonnées incomplètes ou des balises incorrectes fragmentent la bibliothèque. Vous pouvez également parcourir directement les dossiers, rechercher dans toute la collection et retrouver rapidement le morceau en cours de lecture.

Explorez les artistes grâce à des images et des mosaïques créées à partir des pochettes de leurs albums. Consultez les albums avec leurs pochettes, organisez les morceaux isolés dans des compilations et conservez chaque élément à sa place. Vinqelo Player peut aussi lire les métadonnées, rechercher des pochettes, modifier les titres et maintenir les noms de fichiers en ordre.

Créez des listes de lecture, ajoutez des morceaux à une file modifiable et utilisez des listes intelligentes basées sur le temps d'écoute réel. Les commandes comprennent piste précédente, lecture ou pause, piste suivante, arrêt, répétition et lecture aléatoire dans la collection sélectionnée.

Vinqelo Player prend en charge MP3, FLAC, WAV, OGG, M4A et AAC. Pendant la lecture, il affiche la durée, la progression, le format, la fréquence d'échantillonnage, le débit et les canaux. Il comprend également un préamplificateur, un égaliseur à six bandes, un volume persistant et la prise en charge des touches multimédias de Windows.

Vos fichiers audio, votre bibliothèque, vos statistiques et vos préférences restent stockés localement. Les recherches facultatives sur Internet pour les pochettes ou les métadonnées n'envoient jamais vos fichiers audio.`,
  de: `**Vinqelo Player** ist ein lokaler Musikplayer und Musikverwalter für Windows. Er richtet sich an alle, die die vollständige Kontrolle über ihre eigene Musiksammlung behalten möchten.

Importieren Sie einen Ordner und Vinqelo Player übernimmt die vorhandene Organisation Ihrer Musik. Künstler, Alben und Kompilationen werden aus der Ordnerstruktur erstellt. Dadurch verhindern unvollständige Metadaten oder fehlerhafte Tags eine saubere Bibliothek nicht. Sie können außerdem direkt durch Ordner navigieren, die gesamte Sammlung durchsuchen und den aktuell wiedergegebenen Titel schnell finden.

Entdecken Sie Künstler anhand von Bildern und Collagen aus ihren Albumcovern. Durchsuchen Sie Alben mit Coverdarstellung, ordnen Sie einzelne Titel in Kompilationen ein und bewahren Sie alles am richtigen Ort auf. Vinqelo Player kann Metadaten lesen, Cover suchen, Titel bearbeiten und Dateinamen ordentlich halten.

Erstellen Sie Wiedergabelisten, fügen Sie Titel zu einer bearbeitbaren Warteschlange hinzu und verwenden Sie intelligente Wiedergabelisten auf Grundlage der tatsächlichen Hörzeit. Die Steuerung umfasst vorheriger Titel, Wiedergabe oder Pause, nächster Titel, Stopp, Wiederholung und Zufallswiedergabe innerhalb der ausgewählten Sammlung.

Vinqelo Player unterstützt MP3, FLAC, WAV, OGG, M4A und AAC. Während der Wiedergabe werden Dauer, Fortschritt, Format, Abtastrate, Bitrate und Kanäle angezeigt. Enthalten sind außerdem ein Vorverstärker, ein Sechsband-Equalizer, eine dauerhafte Lautstärkeeinstellung und Unterstützung für Windows-Medientasten.

Ihre Audiodateien, Bibliothek, Statistiken und Einstellungen bleiben lokal gespeichert. Optionale Internetabfragen nach Covern oder Metadaten übertragen niemals Ihre Audiodateien.`,
};

const shortDescriptions = {
  es: "Organiza y reproduce tu música local por artistas, álbumes, compilaciones y carpetas, con búsqueda, listas, cola, carátulas y controles de audio.",
  en: "Organize and play local music by artist, album, compilation, and folder, with search, playlists, queue, artwork, and audio controls.",
  it: "Organizza e riproduci la musica locale per artista, album, compilation e cartella, con ricerca, playlist, coda, copertine e controlli audio.",
  pt: "Organize e reproduza músicas locais por artista, álbum, coletânea e pasta, com pesquisa, playlists, fila, capas e controles de áudio.",
  fr: "Organisez et écoutez votre musique locale par artiste, album, compilation et dossier, avec recherche, listes, file, pochettes et commandes audio.",
  de: "Lokale Musik nach Künstler, Album, Kompilation und Ordner organisieren und abspielen – mit Suche, Listen, Warteschlange, Covern und Audiosteuerung.",
};

const captions = {
  es: ["Toda tu biblioteca y actividad de escucha en una sola vista.", "Explora tu colección por artistas mediante imágenes y collages de sus álbumes.", "Encuentra cada disco por su carátula, artista, cantidad de pistas y duración.", "Navega por tu música mediante una estructura de carpetas familiar."],
  en: ["Your complete library and listening activity in one view.", "Browse your collection by artist with images and album collages.", "Find every album by its artwork, artist, track count, and duration.", "Browse your music using a familiar folder structure."],
  it: ["Tutta la libreria e l'attività di ascolto in un'unica vista.", "Esplora la raccolta per artista con immagini e collage degli album.", "Trova ogni album tramite copertina, artista, numero di brani e durata.", "Esplora la musica con una struttura di cartelle familiare."],
  pt: ["Toda a sua biblioteca e atividade de audição em uma única tela.", "Explore a coleção por artista com imagens e colagens dos álbuns.", "Encontre cada álbum pela capa, artista, quantidade de faixas e duração.", "Navegue pela música usando uma estrutura de pastas familiar."],
  fr: ["Toute votre bibliothèque et votre activité d'écoute dans une seule vue.", "Explorez votre collection par artiste avec des images et des mosaïques d'albums.", "Retrouvez chaque album par sa pochette, son artiste, son nombre de pistes et sa durée.", "Parcourez votre musique avec une structure de dossiers familière."],
  de: ["Ihre gesamte Bibliothek und Höraktivität in einer einzigen Ansicht.", "Sammlung nach Künstlern mit Bildern und Albumcollagen durchsuchen.", "Jedes Album nach Cover, Künstler, Titelanzahl und Dauer finden.", "Musik in einer vertrauten Ordnerstruktur durchsuchen."],
};

const features = {
  es: ["Organización por artistas, álbumes, compilaciones y carpetas", "Importación y actualización de bibliotecas musicales completas", "Reproducción de MP3, FLAC, WAV, OGG, M4A y AAC", "Búsqueda rápida de canciones, artistas y álbumes", "Carátulas locales y búsqueda opcional de imágenes en Internet", "Listas de reproducción manuales e inteligentes", "Cola de reproducción editable", "Repetición y reproducción aleatoria de la colección actual", "Preamplificador y ecualizador de seis bandas", "Información de formato, calidad y canales de audio", "Edición de títulos y nombres de archivos", "Exportación seleccionable de listas de reproducción", "Compatibilidad con las teclas multimedia de Windows", "Interfaz oscura adaptable con varios temas e idiomas", "Estadísticas por tiempo acumulado de reproducción"],
  en: ["Organization by artist, album, compilation, and folder", "Import and update complete music libraries", "Playback of MP3, FLAC, WAV, OGG, M4A, and AAC", "Fast search across songs, artists, and albums", "Local artwork and optional online image search", "Manual and smart playlists", "Editable playback queue", "Repeat and shuffle within the current collection", "Preamplifier and six-band equalizer", "Audio format, quality, and channel information", "Edit titles and file names", "Selectable playlist export", "Windows media-key support", "Adaptive dark interface with multiple themes and languages", "Statistics based on accumulated listening time"],
  it: ["Organizzazione per artista, album, compilation e cartella", "Importazione e aggiornamento di intere librerie musicali", "Riproduzione di MP3, FLAC, WAV, OGG, M4A e AAC", "Ricerca rapida di brani, artisti e album", "Copertine locali e ricerca facoltativa di immagini online", "Playlist manuali e intelligenti", "Coda di riproduzione modificabile", "Ripetizione e riproduzione casuale nella raccolta corrente", "Preamplificatore ed equalizzatore a sei bande", "Informazioni su formato, qualità e canali audio", "Modifica di titoli e nomi dei file", "Esportazione selezionabile delle playlist", "Supporto per i tasti multimediali di Windows", "Interfaccia scura adattabile con più temi e lingue", "Statistiche basate sul tempo di ascolto accumulato"],
  pt: ["Organização por artista, álbum, coletânea e pasta", "Importação e atualização de bibliotecas musicais completas", "Reprodução de MP3, FLAC, WAV, OGG, M4A e AAC", "Pesquisa rápida de músicas, artistas e álbuns", "Capas locais e pesquisa opcional de imagens na Internet", "Playlists manuais e inteligentes", "Fila de reprodução editável", "Repetição e reprodução aleatória na coleção atual", "Pré-amplificador e equalizador de seis bandas", "Informações de formato, qualidade e canais de áudio", "Edição de títulos e nomes de arquivos", "Exportação selecionável de playlists", "Suporte às teclas multimídia do Windows", "Interface escura adaptável com vários temas e idiomas", "Estatísticas por tempo acumulado de audição"],
  fr: ["Organisation par artiste, album, compilation et dossier", "Importation et mise à jour de bibliothèques musicales complètes", "Lecture des formats MP3, FLAC, WAV, OGG, M4A et AAC", "Recherche rapide de morceaux, d'artistes et d'albums", "Pochettes locales et recherche facultative d'images en ligne", "Listes de lecture manuelles et intelligentes", "File de lecture modifiable", "Répétition et lecture aléatoire dans la collection actuelle", "Préamplificateur et égaliseur à six bandes", "Informations sur le format, la qualité et les canaux audio", "Modification des titres et des noms de fichiers", "Exportation sélective des listes de lecture", "Prise en charge des touches multimédias de Windows", "Interface sombre adaptable avec plusieurs thèmes et langues", "Statistiques basées sur le temps d'écoute cumulé"],
  de: ["Organisation nach Künstler, Album, Kompilation und Ordner", "Import und Aktualisierung vollständiger Musikbibliotheken", "Wiedergabe von MP3, FLAC, WAV, OGG, M4A und AAC", "Schnelle Suche nach Titeln, Künstlern und Alben", "Lokale Cover und optionale Online-Bildersuche", "Manuelle und intelligente Wiedergabelisten", "Bearbeitbare Wiedergabewarteschlange", "Wiederholung und Zufallswiedergabe der aktuellen Sammlung", "Vorverstärker und Sechsband-Equalizer", "Informationen zu Audioformat, Qualität und Kanälen", "Titel und Dateinamen bearbeiten", "Ausgewählte Wiedergabelisten exportieren", "Unterstützung für Windows-Medientasten", "Anpassbare dunkle Oberfläche mit mehreren Designs und Sprachen", "Statistiken nach kumulierter Hörzeit"],
};

const terms = {
  es: ["reproductor de música", "mp3", "flac", "biblioteca musical", "música local", "listas de reproducción", "ecualizador"],
  en: ["music player", "mp3 player", "flac player", "music library", "local music", "playlists", "equalizer"],
  it: ["lettore musicale", "lettore mp3", "flac", "libreria musicale", "musica locale", "playlist", "equalizzatore"],
  pt: ["reprodutor de música", "reprodutor mp3", "flac", "biblioteca musical", "música local", "playlists", "equalizador"],
  fr: ["lecteur de musique", "lecteur mp3", "flac", "bibliothèque musicale", "musique locale", "listes de lecture", "égaliseur"],
  de: ["Musikplayer", "MP3 Player", "FLAC Player", "Musikbibliothek", "lokale Musik", "Wiedergabelisten", "Equalizer"],
};

const licenses = {
  es: "Vinqelo Player se distribuye bajo la Licencia Pública General GNU, versión 3. El texto completo de la licencia está incluido con la aplicación.",
  en: "Vinqelo Player is distributed under the GNU General Public License, version 3. The complete license text is included with the application.",
  it: "Vinqelo Player è distribuito secondo i termini della GNU General Public License, versione 3. Il testo completo della licenza è incluso nell'applicazione.",
  pt: "O Vinqelo Player é distribuído sob a Licença Pública Geral GNU, versão 3. O texto completo da licença está incluído no aplicativo.",
  fr: "Vinqelo Player est distribué sous la Licence publique générale GNU, version 3. Le texte complet de la licence est inclus avec l'application.",
  de: "Vinqelo Player wird unter der GNU General Public License, Version 3, vertrieben. Der vollständige Lizenztext ist in der Anwendung enthalten.",
};

const csvText = await fs.readFile(source, "utf8");
const workbook = await Workbook.fromCSV(csvText.replace(/^\uFEFF/, ""), { sheetName: "Listing" });
const sheet = workbook.worksheets.getItem("Listing");
const used = sheet.getUsedRange();
const matrix = used.values.map(row => row.map(value => value == null ? "" : String(value)));
const headers = matrix[0];
const index = Object.fromEntries(headers.map((name, position) => [name, position]));
const rows = new Map(matrix.slice(1).filter(row => row[0]).map(row => [row[0], row]));

function setField(field, values) {
  const row = rows.get(field);
  if (!row) throw new Error(`No se encontró el campo ${field}`);
  for (const locale of locales) row[index[locale]] = values[locale] ?? "";
}

setField("Description", descriptions);
for (const field of ["Title", "ShortTitle", "SortTitle"]) {
  setField(field, Object.fromEntries(locales.map(locale => [locale, "Vinqelo Player"])));
}
setField("ShortDescription", shortDescriptions);
setField("DevStudio", Object.fromEntries(locales.map(locale => [locale, "Irán Quintero"])));
setField("CopyrightTrademarkInformation", Object.fromEntries(locales.map(locale => [locale, "Vinqelo Player © 2026 Irán Quintero."])));
setField("AdditionalLicenseTerms", licenses);

const assetFiles = {
  DesktopScreenshot1: "01-biblioteca.png",
  DesktopScreenshot2: "02-artistas.png",
  DesktopScreenshot3: "03-albumes.png",
  DesktopScreenshot4: "04-carpetas.png",
  StoreLogo720x1080: "poster-store-9x16-1440x2160.png",
  StoreLogo1080x1080: "caja-store-1x1-2160x2160.png",
  StoreLogo300x300: "icono-tienda-300x300.png",
  PromoImage1920x1080: "hero-1920x1080.png",
};
const sharedAssets = Object.fromEntries(
  Object.entries(assetFiles).map(([field, filename]) => [
    field,
    `${importFolderName}/images/${filename}`,
  ]),
);
for (const [field, filename] of Object.entries(sharedAssets)) {
  setField(field, Object.fromEntries(locales.map(locale => [locale, filename])));
}
setField("OverrideLogosForWin10", Object.fromEntries(locales.map(locale => [locale, "True"])));

for (let position = 0; position < 4; position++) {
  setField(`DesktopScreenshotCaption${position + 1}`, Object.fromEntries(locales.map(locale => [locale, captions[locale][position]])));
}
for (let position = 0; position < 15; position++) {
  setField(`Feature${position + 1}`, Object.fromEntries(locales.map(locale => [locale, features[locale][position]])));
}
for (let position = 0; position < 7; position++) {
  setField(`SearchTerm${position + 1}`, Object.fromEntries(locales.map(locale => [locale, terms[locale][position]])));
}

sheet.getRangeByIndexes(0, 0, matrix.length, headers.length).values = matrix;
sheet.getRange("A1:J1").format = { fill: "#123A78", font: { bold: true, color: "#FFFFFF" } };
sheet.getRange("A1:J14").format.wrapText = true;
sheet.getRange("A:A").format.columnWidth = 34;
sheet.getRange("B:C").format.columnWidth = 18;
sheet.getRange("D:D").format.columnWidth = 12;
sheet.getRange("E:J").format.columnWidth = 42;
sheet.freezePanes.freezeRows(1);

const preview = await workbook.render({ sheetName: "Listing", range: "A1:J14", scale: 0.8, format: "png" });
await fs.mkdir(reviewDir, { recursive: true });
await fs.writeFile(path.join(reviewDir, "vista-previa.png"), new Uint8Array(await preview.arrayBuffer()));
const xlsx = await SpreadsheetFile.exportXlsx(workbook);
await xlsx.save(path.join(reviewDir, "Vinqelo-Store-Listing-Multidioma.xlsx"));

function csvCell(value) {
  const text = String(value ?? "");
  return /[",\r\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
}
const outputCsv = "\uFEFF" + matrix.map(row => row.map(csvCell).join(",")).join("\r\n") + "\r\n";
await fs.mkdir(outputDir, { recursive: true });
await fs.writeFile(path.join(outputDir, csvName), outputCsv, "utf8");

const assetSource = path.join(root, "store-assets", "es-ES");
const imageDir = path.join(outputDir, "images");
await fs.mkdir(imageDir, { recursive: true });
for (const filename of new Set(Object.values(assetFiles))) {
  await fs.copyFile(path.join(assetSource, filename), path.join(imageDir, filename));
}

const verification = await workbook.inspect({
  kind: "table",
  range: "Listing!A1:J14",
  include: "values",
  tableMaxRows: 14,
  tableMaxCols: 10,
  tableMaxCellChars: 100,
  maxChars: 5000,
});
console.log(verification.ndjson);
const formulaErrors = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
  options: { useRegex: true, maxResults: 100 },
  summary: "comprobación final de errores",
});
console.log(formulaErrors.ndjson);
console.log(JSON.stringify({ outputDir, csv: path.join(outputDir, csvName), rows: matrix.length - 1, locales }, null, 2));
