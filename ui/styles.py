"""Tema oscuro compacto inspirado en reproductores de biblioteca clásicos."""

from __future__ import annotations

import re


APP_STYLESHEET = """
QWidget {
    color: #e7edf7;
    font-family: "Segoe UI";
    font-size: 13px;
}

QMainWindow {
    background-color: transparent;
}

QMenuBar#classicMenuBar {
    background-color: #0d1729;
    border-bottom: 1px solid #263957;
    color: #dce7f7;
    spacing: 2px;
}

QMenuBar#classicMenuBar::item {
    background-color: transparent;
    color: #dce7f7;
    padding: 7px 10px;
}

QMenuBar#classicMenuBar::item:selected,
QMenuBar#classicMenuBar::item:pressed {
    background-color: #1a2a45;
    color: #ffffff;
}

QFrame#windowFrame,
QWidget#contentArea,
QStackedWidget {
    background-color: #0a1020;
}

QFrame#windowFrame {
    border: 1px solid #314766;
    border-radius: 0;
}

QPushButton[windowControl="true"] {
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: 14px;
    color: #a9bad1;
    font-size: 14px;
    min-height: 0;
    min-width: 0;
    padding: 0;
}

QPushButton[windowControl="true"]:hover {
    background-color: #1b2a43;
    border-color: #30496d;
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

/* Base obligatoria para cualquier botón nuevo: nunca heredar blanco de Windows. */
QPushButton {
    background-color: #17243a;
    border: 1px solid #304563;
    border-radius: 6px;
    color: #e7edf7;
    min-height: 30px;
    padding: 0 12px;
}

QPushButton:hover {
    background-color: #1e304d;
    border-color: #3b82f6;
    color: #ffffff;
}

QPushButton:pressed {
    background-color: #122039;
}

QPushButton:disabled {
    background-color: #111a2b;
    border-color: #263348;
    color: #5f6d82;
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

QDialog#exportProgressDialog {
    background-color: #10192b;
}

QDialog#exportProgressDialog QLabel#exportProgressDetail {
    color: #e7edf7;
    font-weight: 600;
}

QDialog#exportProgressDialog QProgressBar {
    background-color: #0b1424;
    border: 1px solid #304563;
    border-radius: 5px;
    color: #ffffff;
    min-height: 22px;
    text-align: center;
}

QDialog#exportProgressDialog QProgressBar::chunk {
    background-color: #176fe5;
    border-radius: 4px;
}

QMessageBox#initialLibraryDialog QPushButton#initialLibraryButton {
    border-radius: 5px;
    font-size: 11px;
    font-weight: 600;
    min-height: 27px;
    min-width: 0;
    padding: 0 9px;
}

QDialog QLineEdit,
QDialog QComboBox,
QDialog QSpinBox,
QDialog QDoubleSpinBox {
    background-color: #0b1424;
    border: 1px solid #304563;
    border-radius: 5px;
    color: #f4f7fc;
    min-height: 30px;
    padding: 0 8px;
    selection-background-color: #176fe5;
}

QDialog QComboBox QAbstractItemView {
    background-color: #111c30;
    border: 1px solid #304563;
    color: #f4f7fc;
    selection-background-color: #1b477c;
    selection-color: #ffffff;
}

QCheckBox {
    color: #dce7f7;
    spacing: 8px;
}

QCheckBox::indicator {
    background-color: #0b1424;
    border: 1px solid #3a5275;
    border-radius: 3px;
    height: 16px;
    width: 16px;
}

QCheckBox::indicator:checked {
    background-color: #176fe5;
    border-color: #4b9aff;
}

QListWidget#exportTrackList {
    background-color: #0b1424;
    border: 1px solid #304563;
    color: #e7edf7;
    outline: none;
}

QListWidget#exportTrackList::item {
    min-height: 32px;
    padding: 3px 7px;
}

QListWidget#exportTrackList::item:selected {
    background-color: #1b477c;
    color: #ffffff;
}

QListWidget#folderExplorer {
    background-color: transparent;
    border: none;
    color: #e7edf7;
    outline: none;
}

QListWidget#folderExplorer::item {
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: 8px;
    color: #e7edf7;
    margin: 4px;
    padding: 8px;
}

QListWidget#folderExplorer::item:hover {
    background-color: #17243b;
    border-color: #2d4669;
}

QListWidget#folderExplorer::item:selected {
    background-color: #1b477c;
    border-color: #438df5;
    color: #ffffff;
}

QTabWidget#donationTabs::pane,
QTabWidget#settingsTabs::pane {
    background-color: #0b1424;
    border: 1px solid #304563;
}

QTabWidget#donationTabs QTabBar::tab,
QTabWidget#settingsTabs QTabBar::tab {
    background-color: #111c30;
    border: 1px solid #304563;
    color: #aebed4;
    min-width: 105px;
    padding: 8px 10px;
}

QTabWidget#donationTabs QTabBar::tab:selected,
QTabWidget#settingsTabs QTabBar::tab:selected {
    background-color: #1b477c;
    color: #ffffff;
}

QLabel#donationQr {
    background-color: #ffffff;
    border: 1px solid #304563;
}

QLabel#donationMethodTitle {
    color: #ffffff;
    font-size: 17px;
    font-weight: 700;
    padding: 4px;
}

QLabel#donationData {
    background-color: #121d31;
    border: 1px solid #304563;
    color: #dce7f7;
    padding: 7px;
}

QLabel#donationWarning {
    background-color: #121d31;
    border: 1px solid #3b5478;
    color: #e7edf7;
    padding: 8px;
}

QLineEdit#donationAddress {
    background-color: #08101d;
    border: 1px solid #304563;
    color: #dce7f7;
    min-height: 34px;
    padding: 0 8px;
}

QDialog#donationDialog QPushButton#donationPrimaryButton,
QDialog#donationDialog QPushButton#donationSecondaryButton {
    border-radius: 6px;
    color: #ffffff;
    font-weight: 700;
    min-height: 40px;
    padding: 0 18px;
}

QDialog#donationDialog QPushButton#donationPrimaryButton {
    background-color: #176fe5;
    border: 1px solid #3b8cff;
}

QDialog#donationDialog QPushButton#donationPrimaryButton:hover {
    background-color: #237ff0;
    border-color: #69a8ff;
}

QDialog#donationDialog QPushButton#donationSecondaryButton {
    background-color: #17243a;
    border: 1px solid #3a5275;
}

QDialog#donationDialog QPushButton#donationSecondaryButton:hover {
    background-color: #20314d;
    border-color: #4b9aff;
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

QPushButton#aboutButton {
    background-color: transparent;
    border: 1px solid transparent;
    color: #8fa7c7;
    min-height: 28px;
    padding: 3px 7px;
    text-align: left;
}

QPushButton#aboutButton:hover {
    background-color: #14243d;
    border-color: #2d4669;
    color: #ffffff;
}

QPlainTextEdit#aboutLicenseText {
    background-color: #0a1222;
    border: 1px solid #304563;
    border-radius: 0;
    color: #e7edf7;
    selection-background-color: #176fe5;
    selection-color: #ffffff;
    padding: 8px;
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
    padding: 0;
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

QScrollArea#albumRowsScroll,
QWidget#albumRowsContainer {
    background-color: transparent;
    border: none;
}

QFrame#artistAlbumRow {
    background-color: #0f1829;
    border: 1px solid #263957;
    border-radius: 9px;
}

QLabel#artistAlbumCover {
    background-color: #111d31;
    border: 1px solid #304563;
    border-radius: 8px;
}

QLabel#artistAlbumTitle {
    color: #f4f7fc;
    font-size: 14px;
    font-weight: 700;
}

QTreeWidget#artistAlbumTracks {
    background-color: #0b1424;
    border-color: #263957;
}

QScrollBar:vertical {
    background-color: #0b1424;
    border: 1px solid #1c2d48;
    border-radius: 6px;
    margin: 2px;
    width: 12px;
}

QScrollBar::handle:vertical {
    background-color: #276fc9;
    border-radius: 5px;
    min-height: 36px;
}

QScrollBar::handle:vertical:hover,
QScrollBar::handle:vertical:pressed {
    background-color: #6f52d9;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0;
}

QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {
    background-color: transparent;
}

QScrollBar:horizontal {
    background-color: #0b1424;
    border: 1px solid #1c2d48;
    border-radius: 6px;
    height: 12px;
    margin: 2px;
}

QScrollBar::handle:horizontal {
    background-color: #276fc9;
    border-radius: 5px;
    min-width: 36px;
}

QScrollBar::handle:horizontal:hover,
QScrollBar::handle:horizontal:pressed {
    background-color: #6f52d9;
}

QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {
    width: 0;
}

QScrollBar::add-page:horizontal,
QScrollBar::sub-page:horizontal {
    background-color: transparent;
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
QLineEdit#collectionSearch,
QLineEdit#folderSearch {
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
QLineEdit#collectionSearch:focus,
QLineEdit#folderSearch:focus {
    border-color: #2583ff;
}

QLineEdit#trackSearch,
QLineEdit#collectionSearch {
    font-size: 12px;
    min-height: 32px;
}

QLineEdit#folderSearch QToolButton {
    background-color: transparent;
    border: none;
    color: #aebed4;
    margin: 0;
    padding: 0;
}

QLineEdit#folderSearch QToolButton:hover {
    background-color: #1b2a43;
    border: none;
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

QPushButton#playerButton:checked {
    background-color: #1b477c;
    border-color: #4b9aff;
    color: #ffffff;
}

QPushButton#modeButton {
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: 14px;
    min-height: 26px;
    max-height: 26px;
    min-width: 26px;
    max-width: 26px;
    padding: 0;
}

QPushButton#modeButton:hover {
    background-color: #17243a;
    border-color: #304563;
}

QPushButton#modeButton[modeActive="true"] {
    background-color: #17345b;
    border-color: #315f96;
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

QFrame#trackPanel:hover {
    background-color: #111f35;
    border-color: #3b82f6;
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


THEME_PALETTES = {
    "vinqelo": {},
    "clementine": {
        "#176fe5": "#d97706", "#3186f4": "#f59e0b", "#2583ff": "#f59e0b",
        "#0e5fcf": "#b45309", "#3b82f6": "#f59e0b", "#4b9aff": "#fbbf24",
        "#438df5": "#f59e0b", "#1b477c": "#704214",
        "#0a1020": "#12100d", "#10192b": "#1b1712", "#111c30": "#211b14",
    },
    "amarok": {
        "#176fe5": "#7c3aed", "#3186f4": "#9b6cff", "#2583ff": "#8b5cf6",
        "#0e5fcf": "#6d28d9", "#3b82f6": "#8b5cf6", "#4b9aff": "#a78bfa",
        "#438df5": "#9b6cff", "#1b477c": "#4c2d78",
        "#0a1020": "#100d18", "#10192b": "#171223", "#111c30": "#20172f",
    },
    "emerald": {
        "#176fe5": "#059669", "#3186f4": "#10b981", "#2583ff": "#10b981",
        "#0e5fcf": "#047857", "#3b82f6": "#10b981", "#4b9aff": "#34d399",
        "#438df5": "#10b981", "#1b477c": "#145c49",
    },
    "graphite": {
        "#176fe5": "#64748b", "#3186f4": "#94a3b8", "#2583ff": "#94a3b8",
        "#0e5fcf": "#475569", "#3b82f6": "#94a3b8", "#4b9aff": "#cbd5e1",
        "#438df5": "#94a3b8", "#1b477c": "#3b4b60",
    },
    "musicmatch": {
        "#176fe5": "#3f709d", "#3186f4": "#5d89b0", "#2583ff": "#4d7da8",
        "#0e5fcf": "#315d87", "#3b82f6": "#4d7da8", "#4b9aff": "#7aa1c2",
        "#438df5": "#527fa8", "#1b477c": "#6687a5",
        "#0a1020": "#d7dfe7", "#10192b": "#506982", "#111c30": "#e4e9ee",
        "#0f1829": "#edf1f4", "#111d31": "#e5ebf0",
        "#15223a": "#c2ced9", "#0b1424": "#f3f6f8",
        "#08101d": "#e8edf2", "#091322": "#f5f7f9", "#17243a": "#cbd6e0",
        "#263650": "#9aabba", "#263957": "#91a3b4", "#304563": "#8fa2b4",
        "#2a3d5c": "#91a3b4", "#e7edf7": "#21364a", "#dce7f7": "#2d4358",
        "#c8d8ed": "#40576d", "#b5c7df": "#536b82", "#8fa7c7": "#4f6982",
        "#8296b4": "#546b80", "#7890b0": "#597188",
        "#f4f7fc": "#1f3449", "#8195b1": "#587086",
    },
}


MUSICMATCH_STYLESHEET = """
QDialog {
    background-color: #d7dfe7;
}

QDialog#aboutDialog,
QDialog#donationDialog,
QDialog#exportProgressDialog {
    background-color: #d7dfe7;
    color: #23384c;
}

QDialog#exportProgressDialog QLabel#exportProgressDetail {
    color: #23384c;
}

QDialog#exportProgressDialog QProgressBar {
    background-color: #f3f6f8;
    border-color: #8fa2b4;
    color: #23384c;
}

QDialog#exportProgressDialog QProgressBar::chunk {
    background-color: #3f709d;
}

QDialog#aboutDialog QLabel,
QDialog#donationDialog QLabel {
    color: #23384c;
}

QDialog#aboutDialog QLabel#pageSubtitle,
QDialog#donationDialog QLabel#pageSubtitle {
    color: #40576d;
}

QDialog#aboutDialog QLabel#aboutDetails {
    color: #23384c;
}

QDialog#aboutDialog QPlainTextEdit#aboutLicenseText {
    background-color: #f3f6f8;
    border: 1px solid #8fa2b4;
    color: #23384c;
    selection-background-color: #4d7da8;
    selection-color: #ffffff;
}

QDialog#aboutDialog QPushButton#secondaryButton {
    background-color: #c7d3de;
    border-color: #8da2b5;
    color: #243b50;
}

QDialog#aboutDialog QPushButton#secondaryButton:hover {
    background-color: #b5c6d5;
    border-color: #5d89b0;
    color: #1f3449;
}

QDialog#aboutDialog QPushButton#secondaryButton:pressed {
    background-color: #4d7da8;
    border-color: #315d87;
    color: #ffffff;
}

QDialog#donationDialog QTabWidget#donationTabs::pane {
    background-color: #f3f6f8;
    border: 1px solid #8fa2b4;
}

QDialog#donationDialog QTabWidget#donationTabs QTabBar::tab {
    background-color: #dbe3ea;
    border: 1px solid #9aabba;
    color: #2d4358;
}

QDialog#donationDialog QTabWidget#donationTabs QTabBar::tab:hover {
    background-color: #c7d5e1;
    border-color: #6f8da8;
    color: #1f3449;
}

QDialog#donationDialog QTabWidget#donationTabs QTabBar::tab:selected {
    background-color: #3f709d;
    border-color: #315d87;
    color: #ffffff;
}

QDialog#donationDialog QLabel#donationMethodTitle {
    color: #1c3146;
}

QDialog#donationDialog QLabel#donationData,
QDialog#donationDialog QLabel#donationWarning {
    background-color: #e5ebf0;
    border: 1px solid #91a3b4;
    color: #23384c;
}

QDialog#donationDialog QLineEdit#donationAddress {
    background-color: #f6f8fa;
    border: 1px solid #8fa2b4;
    color: #20364a;
    selection-background-color: #4d7da8;
    selection-color: #ffffff;
}

QDialog#donationDialog QPushButton#donationPrimaryButton {
    background-color: #3f709d;
    border-color: #5d89b0;
    color: #ffffff;
}

QDialog#donationDialog QPushButton#donationPrimaryButton:hover {
    background-color: #315d87;
    border-color: #7aa1c2;
    color: #ffffff;
}

QDialog#donationDialog QPushButton#donationSecondaryButton {
    background-color: #c7d3de;
    border-color: #8da2b5;
    color: #243b50;
}

QDialog#donationDialog QPushButton#donationSecondaryButton:hover {
    background-color: #b5c6d5;
    border-color: #5d89b0;
    color: #1f3449;
}

QLabel#pageTitle,
QLabel#statValue,
QLabel#emptyTitle,
QLabel#donationMethodTitle,
QLabel#trackTitle {
    color: #1c3146;
}

QLabel#pageSubtitle,
QLabel#mutedLabel,
QLabel#trackArtist,
QLabel#trackAlbum,
QLabel#trackMeta {
    color: #536b82;
}

QFrame#sidebar QLabel#mutedLabel,
QFrame#playerBar QLabel#mutedLabel,
QFrame#playerBar QLabel#trackArtist,
QFrame#playerBar QLabel#trackAlbum,
QFrame#playerBar QLabel#trackMeta,
QFrame#playerBar QLabel#trackTitle {
    color: #dce7f7;
}

QFrame#sidebar QLabel#navGroup {
    color: #d0dce7;
}

QFrame#sidebar QFrame#brandBlock {
    background-color: #5f7890;
    border-color: #8fa4b7;
}

QFrame#sidebar QLabel#brandCaption {
    color: #e3ecf4;
    font-weight: 600;
}

QFrame#sidebar QPushButton#navButton {
    color: #e4ebf2;
}

QFrame#sidebar QPushButton#aboutButton {
    background-color: transparent;
    border-color: transparent;
    color: #e4ebf2;
}

QFrame#sidebar QPushButton#aboutButton:hover {
    background-color: #40576d;
    border-color: #8fa4b7;
    color: #ffffff;
}

QFrame#sidebar QPushButton#aboutButton:pressed {
    background-color: #315d87;
    border-color: #9bb0c2;
    color: #ffffff;
}

QTreeWidget,
QListWidget,
QTableWidget,
QPlainTextEdit,
QTextEdit {
    background-color: #f2f5f7;
    alternate-background-color: #e5ebf0;
    border-color: #97a9ba;
    color: #23384c;
}

QTreeWidget::item {
    color: #23384c;
}

QTreeWidget::item:selected {
    background-color: #4d7da8;
    color: #ffffff;
}

QHeaderView::section,
QFrame#tableHeader {
    background-color: #c2ced9;
    border-color: #91a3b4;
    color: #40576d;
}

QLineEdit,
QComboBox,
QSpinBox,
QDoubleSpinBox {
    background-color: #f6f8fa;
    border-color: #8fa2b4;
    color: #20364a;
}

QPushButton#toolbarIcon {
    background-color: #c7d3de;
    border-color: #8da2b5;
}

QPushButton#toolbarIcon:hover {
    background-color: #b5c6d5;
    border-color: #5d89b0;
}

QPushButton#secondaryButton {
    background-color: #c7d3de;
    border-color: #8da2b5;
    color: #243b50;
}

QPushButton#secondaryButton:hover {
    background-color: #b5c6d5;
    border-color: #5d89b0;
    color: #1f3449;
}

QPushButton#secondaryButton:pressed {
    background-color: #4d7da8;
    border-color: #315d87;
    color: #ffffff;
}

QFrame#libraryPanel,
QFrame#emptyCard,
QFrame#statCard {
    background-color: #edf1f4;
    border-color: #9aabba;
}

QFrame#playerBar {
    background-color: #526b82;
    border-top-color: #7f94a7;
}

QFrame#playerBar QFrame#trackPanel {
    background-color: #40576d;
    border-color: #7890a6;
}

QFrame#playerBar QFrame#trackPanel:hover {
    background-color: #48627a;
    border-color: #9bb0c2;
}

QFrame#playerBar QLabel#columnHeader,
QFrame#playerBar QLabel#trackQuality {
    color: #d7e2ec;
}

QFrame#playerBar QPushButton#playerButton,
QFrame#playerBar QPushButton#modeButton {
    background-color: transparent;
    border-color: transparent;
}

QFrame#playerBar QPushButton#playerButton:hover,
QFrame#playerBar QPushButton#modeButton:hover {
    background-color: #40576d;
    border-color: #8298ab;
}

QFrame#playerBar QSlider::groove:horizontal {
    background-color: #91a4b5;
}

QListWidget#artistGrid::item:selected,
QListWidget#albumGrid::item:selected,
QListWidget#visualAlbumGrid::item:selected {
    background-color: #4d7da8;
    color: #ffffff;
}

QListWidget#artistGrid::item:hover,
QListWidget#albumGrid::item:hover,
QListWidget#visualAlbumGrid::item:hover {
    background-color: #c5d3df;
    color: #1f3449;
}

QListWidget#artistGrid::item:selected:hover,
QListWidget#albumGrid::item:selected:hover,
QListWidget#visualAlbumGrid::item:selected:hover {
    background-color: #4d7da8;
    color: #ffffff;
}

QListWidget#listeningArtists::item {
    color: #23384c;
}

QListWidget#listeningArtists::item:hover {
    background-color: #c5d3df;
    color: #1f3449;
}

QListWidget#listeningArtists::item:selected,
QListWidget#listeningArtists::item:selected:hover {
    background-color: #4d7da8;
    color: #ffffff;
}

QScrollBar::handle:vertical,
QScrollBar::handle:horizontal {
    background-color: #587fa3;
}

QScrollBar::handle:vertical:hover,
QScrollBar::handle:vertical:pressed,
QScrollBar::handle:horizontal:hover,
QScrollBar::handle:horizontal:pressed {
    background-color: #3f6f9b;
}
"""


def build_stylesheet(theme: str = "vinqelo", font_size: int = 13) -> str:
    stylesheet = APP_STYLESHEET
    for source, target in THEME_PALETTES.get(theme, {}).items():
        stylesheet = stylesheet.replace(source, target)
    if theme == "musicmatch":
        stylesheet += MUSICMATCH_STYLESHEET
    delta = max(11, min(17, int(font_size))) - 13
    if delta:
        stylesheet = re.sub(
            r"font-size:\s*(\d+)px",
            lambda match: f"font-size: {max(8, int(match.group(1)) + delta)}px",
            stylesheet,
        )
    return stylesheet
