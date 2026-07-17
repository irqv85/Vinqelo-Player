"""Tema oscuro compacto inspirado en reproductores de biblioteca clásicos."""

APP_STYLESHEET = """
QWidget {
    color: #e7edf7;
    font-family: "Segoe UI";
    font-size: 13px;
}

QMainWindow {
    background-color: transparent;
}

QFrame#windowFrame,
QWidget#contentArea,
QStackedWidget {
    background-color: #0a1020;
}

QFrame#windowFrame {
    border: 1px solid #314766;
    border-radius: 14px;
}

QPushButton[windowControl="true"] {
    background-color: rgba(18, 31, 51, 210);
    border: 1px solid #2a3d59;
    border-radius: 7px;
    color: #a9bad1;
    font-size: 14px;
}

QPushButton[windowControl="true"]:hover {
    background-color: #213554;
    color: #ffffff;
}

QPushButton[closeControl="true"]:hover {
    background-color: #d94a55;
    border-color: #ef6670;
}

QLabel {
    background-color: transparent;
}

QToolTip {
    background-color: #1a2740;
    border: 1px solid #34517d;
    color: #ffffff;
    padding: 5px 7px;
}

QDialog,
QMessageBox,
QProgressDialog {
    background-color: #10192b;
}

QMessageBox QLabel,
QProgressDialog QLabel {
    background-color: transparent;
    color: #e7edf7;
}

QMessageBox QPushButton,
QProgressDialog QPushButton {
    background-color: #176fe5;
    border: 1px solid #3186f4;
    border-radius: 6px;
    color: #ffffff;
    min-height: 30px;
    min-width: 82px;
    padding: 0 12px;
}

QFrame#sidebar {
    background-color: #10192b;
    border-right: 1px solid #24334d;
}

QFrame#brandBlock {
    background-color: #0c1527;
    border: 1px solid #223656;
    border-radius: 10px;
}

QLabel#brandName {
    color: #ffffff;
    font-size: 18px;
    font-weight: 700;
}

QLabel#brandCaption,
QLabel#mutedLabel,
QLabel#pageSubtitle,
QLabel#trackArtist {
    color: #8fa1bb;
}

QLabel#navGroup {
    color: #5f7698;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1px;
    padding: 12px 10px 4px 10px;
}

QLabel#engineReady {
    color: #65d69e;
    font-size: 11px;
}

QLabel#engineUnavailable {
    color: #ff8e8e;
    font-size: 11px;
}

QPushButton#navButton {
    background-color: transparent;
    border: none;
    border-left: 3px solid transparent;
    border-radius: 5px;
    color: #b8c5d8;
    min-height: 36px;
    padding: 0 12px;
    text-align: left;
}

QPushButton#navButton:hover {
    background-color: #17243b;
    color: #ffffff;
}

QPushButton#navButton[active="true"] {
    background-color: #1b2c49;
    border-left: 3px solid #2583ff;
    color: #ffffff;
    font-weight: 600;
}

QLabel#pageEyebrow {
    color: #438df5;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1px;
}

QLabel#pageTitle {
    color: #ffffff;
    font-size: 25px;
    font-weight: 700;
}

QFrame#statCard {
    background-color: #111c30;
    border: 1px solid #263957;
    border-radius: 7px;
}

QLabel#statValue {
    color: #ffffff;
    font-size: 21px;
    font-weight: 700;
}

QLabel#statLabel {
    color: #8396b2;
    font-size: 11px;
}

QFrame#libraryPanel,
QFrame#emptyCard {
    background-color: #0f1829;
    border: 1px solid #263650;
    border-radius: 8px;
}

QFrame#tableHeader {
    background-color: #15223a;
    border: none;
    border-bottom: 1px solid #2a3d5c;
    border-top-left-radius: 7px;
    border-top-right-radius: 7px;
}

QLabel#columnHeader {
    color: #8296b4;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1px;
}

QLabel#emptyTitle {
    color: #dce7f7;
    font-size: 17px;
    font-weight: 600;
}

QPushButton#primaryButton {
    background-color: #176fe5;
    border: 1px solid #3186f4;
    border-radius: 6px;
    color: #ffffff;
    font-weight: 600;
    min-height: 36px;
    padding: 0 16px;
}

QPushButton#primaryButton:hover {
    background-color: #2583ff;
}

QPushButton#primaryButton:pressed {
    background-color: #0e5fcf;
}

QPushButton#secondaryButton {
    background-color: #17243a;
    border: 1px solid #304563;
    border-radius: 6px;
    color: #dce7f7;
    min-height: 30px;
    padding: 0 11px;
}

QPushButton#secondaryButton:hover {
    background-color: #1e304d;
    border-color: #3b82f6;
}

QPushButton#secondaryButton:disabled {
    color: #5f6d82;
    border-color: #263348;
}

QPushButton#toolbarIcon,
QPushButton#toolbarIconPrimary {
    background-color: #17243a;
    border: 1px solid #304563;
    border-radius: 8px;
    padding: 7px;
}

QPushButton#toolbarIconPrimary {
    background-color: #176fe5;
    border-color: #3186f4;
}

QPushButton#toolbarIcon:hover,
QPushButton#toolbarIconPrimary:hover {
    background-color: #2583ff;
    border-color: #58a0ff;
}

QTreeWidget {
    background-color: #0f1829;
    alternate-background-color: #111d31;
    border: 1px solid #263650;
    border-radius: 8px;
    color: #dce7f7;
    outline: none;
}

QTreeWidget::item {
    color: #dce7f7;
    min-height: 30px;
    padding: 3px 6px;
}

QTreeWidget::item:selected {
    background-color: #2583ff;
    color: #ffffff;
    font-weight: 600;
}

QListWidget#artistGrid,
QListWidget#albumGrid,
QListWidget#visualAlbumGrid {
    background-color: transparent;
    border: none;
    outline: none;
}

QListWidget#artistGrid::item,
QListWidget#albumGrid::item,
QListWidget#visualAlbumGrid::item {
    border-radius: 9px;
    color: #e7edf7;
    padding: 8px;
}

QListWidget#visualAlbumGrid::item {
    padding: 0;
}

QListWidget#artistGrid::item:hover,
QListWidget#albumGrid::item:hover,
QListWidget#visualAlbumGrid::item:hover {
    background-color: #17243b;
}

QListWidget#artistGrid::item:selected,
QListWidget#albumGrid::item:selected,
QListWidget#visualAlbumGrid::item:selected {
    background-color: #1b477c;
}

QFrame#albumCard {
    background-color: transparent;
    border: none;
}

QLabel#albumCardCover {
    background-color: #16233a;
    border: 1px solid #304564;
    border-radius: 7px;
}

QLabel#albumCardTitle {
    color: #f4f7fc;
    font-size: 12px;
    font-weight: 600;
}

QLabel#albumCardArtist {
    color: #8195b1;
    font-size: 10px;
}

QLineEdit#librarySearch,
QLineEdit#trackSearch,
QLineEdit#collectionSearch {
    background-color: #111c30;
    border: 1px solid #304563;
    border-radius: 9px;
    color: #f4f7fc;
    font-size: 14px;
    min-height: 40px;
    padding: 0 12px;
    selection-background-color: #176fe5;
}

QLineEdit#librarySearch:focus,
QLineEdit#trackSearch:focus,
QLineEdit#collectionSearch:focus {
    border-color: #2583ff;
}

QLineEdit#trackSearch,
QLineEdit#collectionSearch {
    font-size: 12px;
    min-height: 32px;
}

QMenu {
    background-color: #111c30;
    border: 1px solid #304563;
    border-radius: 7px;
    color: #f4f7fc;
    padding: 5px;
}

QMenu::item {
    background-color: transparent;
    border-radius: 5px;
    color: #f4f7fc;
    padding: 7px 28px 7px 10px;
}

QMenu::item:selected {
    background-color: #1b477c;
    color: #ffffff;
}

QMenu::item:disabled {
    color: #687a94;
}

QMenu::separator {
    background-color: #304563;
    height: 1px;
    margin: 4px 7px;
}

QDialog#artworkPreviewDialog {
    background-color: #0b1424;
}

QLabel#artworkPreview {
    background-color: #08101d;
    border: 1px solid #304563;
    border-radius: 10px;
}

QDialogButtonBox QPushButton {
    background-color: #176fe5;
    border: 1px solid #3186f4;
    border-radius: 6px;
    color: #ffffff;
    min-height: 32px;
    padding: 0 14px;
}

QDialogButtonBox QPushButton:hover {
    background-color: #2583ff;
}

QListWidget#listeningArtists {
    background-color: transparent;
    border: none;
    outline: none;
}

QListWidget#onlineArtworkGrid {
    background-color: #08101d;
    border: 1px solid #263650;
    border-radius: 8px;
    color: #dce7f7;
    outline: none;
}

QListWidget#onlineArtworkGrid::item {
    border-radius: 8px;
    padding: 6px;
}

QListWidget#onlineArtworkGrid::item:selected {
    background-color: #2583ff;
    color: #ffffff;
}

QListWidget#smartPlaylistList {
    background-color: #0b1424;
    border: 1px solid #263650;
    border-radius: 8px;
    color: #dce7f7;
    outline: none;
}

QListWidget#smartPlaylistList::item {
    border-radius: 6px;
    padding: 7px 10px;
}

QListWidget#smartPlaylistList::item:selected {
    background-color: #2583ff;
    color: #ffffff;
    font-weight: 600;
}

QListWidget#listeningArtists::item {
    border-radius: 8px;
    color: #dce7f7;
    padding: 5px;
}

QListWidget#listeningArtists::item:hover,
QListWidget#listeningArtists::item:selected {
    background-color: #172d4b;
}

QTreeWidget#listeningTracks::item {
    min-height: 54px;
}

QHeaderView::section {
    background-color: #15223a;
    border: none;
    border-bottom: 1px solid #2a3d5c;
    color: #8296b4;
    font-size: 10px;
    font-weight: 700;
    padding: 8px;
}

QFrame#playerBar {
    background-color: #101a2c;
    border-top: 1px solid #2b3d59;
}

QFrame#trackPanel {
    background-color: #0c1525;
    border: 1px solid #243653;
    border-radius: 7px;
}

QFrame#effectSection {
    background-color: #0c1525;
    border: 1px solid #2a3d5c;
    border-radius: 9px;
}

QFrame#mixerConsole {
    background-color: #091220;
    border: 1px solid #293d5a;
    border-radius: 10px;
}

QFrame#mixerChannel,
QFrame#mixerPreamp,
QFrame#vuChannel {
    background-color: #0d1829;
    border: 1px solid #273b58;
    border-radius: 7px;
}

QFrame#mixerPreamp {
    border-color: #365a86;
}

QFrame#mixerSeparator {
    color: #2a3e5a;
}

QLabel#mixerScale,
QLabel#mixerFooter {
    color: #7187a6;
    font-size: 9px;
}

QSlider#mixerFader::groove:vertical {
    background-color: #263a56;
    border-radius: 3px;
    width: 6px;
}

QSlider#mixerFader::sub-page:vertical {
    background-color: #263a56;
    border-radius: 3px;
}

QSlider#mixerFader::add-page:vertical {
    background-color: #2583ff;
    border-radius: 3px;
}

QSlider#mixerFader::handle:vertical {
    background-color: #dce5f0;
    border: 2px solid #3186f4;
    border-radius: 3px;
    height: 12px;
    margin: 0 -12px;
    width: 30px;
}

QDoubleSpinBox#mixerValue,
QComboBox#frequencySelector {
    background-color: #091322;
    border: 1px solid #304766;
    border-radius: 4px;
    color: #dce7f7;
    min-height: 26px;
    padding: 0 5px;
    selection-background-color: #176fe5;
}

QDoubleSpinBox#mixerValue:focus,
QComboBox#frequencySelector:focus {
    border-color: #3186f4;
}

QComboBox#frequencySelector QAbstractItemView {
    background-color: #0d1829;
    border: 1px solid #304766;
    color: #dce7f7;
    selection-background-color: #176fe5;
    selection-color: #ffffff;
}

QComboBox#frequencySelector::drop-down,
QDoubleSpinBox#mixerValue::up-button,
QDoubleSpinBox#mixerValue::down-button {
    background-color: #17263e;
    border: none;
    width: 17px;
}

QFrame#effectFader {
    background-color: #0c1525;
    border: 1px solid #2a3d5c;
    border-radius: 9px;
}

QSlider#toneFader::groove:vertical {
    background-color: #243650;
    border-radius: 3px;
    width: 6px;
}

QSlider#toneFader::sub-page:vertical {
    background-color: #2583ff;
    border-radius: 3px;
}

QSlider#toneFader::handle:vertical {
    background-color: #f5f8fc;
    border: 2px solid #2583ff;
    border-radius: 7px;
    height: 14px;
    margin: 0 -5px;
    width: 14px;
}

QPushButton#effectsButton {
    background-color: #17263e;
    border: 1px solid #36537a;
    border-radius: 8px;
}

QPushButton#effectsButton:hover {
    background-color: #1f3960;
    border-color: #4b9aff;
}

QPushButton#effectSecondaryButton {
    background-color: #15233a;
    border: 1px solid #36506f;
    border-radius: 6px;
    color: #dce7f7;
    min-height: 32px;
    padding: 0 14px;
}

QPushButton#effectSecondaryButton:hover {
    background-color: #1d3454;
    border-color: #4b9aff;
    color: #ffffff;
}

QDoubleSpinBox#effectValueSpin {
    background-color: #091322;
    border: 1px solid #304766;
    border-radius: 5px;
    color: #e6eef9;
    min-height: 28px;
    min-width: 86px;
    padding: 0 6px;
    selection-background-color: #176fe5;
    selection-color: #ffffff;
}

QDoubleSpinBox#effectValueSpin:focus {
    border-color: #3186f4;
}

QCheckBox#autoPreampCheck {
    color: #c6d5e9;
    spacing: 8px;
}

QCheckBox#autoPreampCheck::indicator {
    background-color: #091322;
    border: 1px solid #3a5375;
    border-radius: 4px;
    height: 16px;
    width: 16px;
}

QCheckBox#autoPreampCheck::indicator:checked {
    background-color: #2583ff;
    border-color: #58a4ff;
}

QDoubleSpinBox#effectValueSpin::up-button,
QDoubleSpinBox#effectValueSpin::down-button {
    background-color: #17263e;
    border: none;
    width: 17px;
}

QDoubleSpinBox#effectValueSpin::up-button:hover,
QDoubleSpinBox#effectValueSpin::down-button:hover {
    background-color: #25466f;
}

QLabel#coverThumb {
    background-color: #16233a;
    border: 1px solid #304564;
    border-radius: 5px;
}

QLabel#trackTitle {
    color: #ffffff;
    font-size: 14px;
    font-weight: 600;
}

QLabel#trackAlbum {
    color: #b5c7df;
    font-size: 11px;
}

QLabel#trackMeta {
    color: #7890b0;
    font-size: 10px;
}

QLabel#trackQuality {
    color: #56a1ff;
    font-size: 10px;
    font-weight: 600;
}

QPushButton#playerButton {
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: 17px;
    color: #c8d4e5;
    font-size: 14px;
    min-height: 34px;
    min-width: 34px;
}

QPushButton#playerButton:hover {
    background-color: #1b2a43;
    border-color: #30496d;
    color: #ffffff;
}

QPushButton#playerButton:disabled {
    color: #536177;
}

QPushButton#playButton {
    background-color: #176fe5;
    border: 1px solid #3b8fff;
    border-radius: 21px;
    color: #ffffff;
    font-size: 16px;
    font-weight: 700;
    min-height: 42px;
    min-width: 42px;
}

QPushButton#playButton:hover {
    background-color: #2583ff;
}

QPushButton#playButton:disabled {
    background-color: #24344d;
    border-color: #30415b;
    color: #697991;
}

QSlider::groove:horizontal {
    background: #2a3a54;
    border-radius: 2px;
    height: 4px;
}

QSlider::sub-page:horizontal {
    background: #2583ff;
    border-radius: 2px;
}

QSlider::handle:horizontal {
    background: #f5f8fc;
    border: 2px solid #2583ff;
    border-radius: 6px;
    height: 12px;
    margin: -5px 0;
    width: 12px;
}
"""
