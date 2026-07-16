"""Tema visual oscuro de la aplicacion."""

APP_STYLESHEET = """
QWidget {
    color: #f1f3f5;
    font-family: "Segoe UI";
    font-size: 14px;
}

QMainWindow {
    background-color: #111318;
}

QWidget#appRoot,
QWidget#contentArea,
QStackedWidget {
    background-color: #111318;
}

QLabel {
    background-color: transparent;
}

QFrame#sidebar {
    background-color: #171a21;
    border-right: 1px solid #292d36;
}

QLabel#brandName {
    color: #ffffff;
    font-size: 21px;
    font-weight: 700;
}

QLabel#brandCaption,
QLabel#mutedLabel,
QLabel#pageSubtitle,
QLabel#trackArtist {
    color: #9097a6;
}

QPushButton#navButton {
    background-color: transparent;
    border: none;
    border-radius: 8px;
    color: #aab0bd;
    min-height: 42px;
    padding: 0 14px;
    text-align: left;
}

QPushButton#navButton:hover {
    background-color: #222630;
    color: #ffffff;
}

QPushButton#navButton[active="true"] {
    background-color: #2b3040;
    color: #ffffff;
    font-weight: 600;
}

QLabel#pageTitle {
    color: #ffffff;
    font-size: 28px;
    font-weight: 700;
}

QFrame#statCard,
QFrame#emptyCard {
    background-color: #191c23;
    border: 1px solid #2a2e38;
    border-radius: 12px;
}

QLabel#statValue {
    color: #ffffff;
    font-size: 24px;
    font-weight: 700;
}

QLabel#statLabel {
    color: #9097a6;
    font-size: 12px;
}

QPushButton#primaryButton {
    background-color: #7c5cff;
    border: none;
    border-radius: 8px;
    color: #ffffff;
    font-weight: 600;
    min-height: 40px;
    padding: 0 18px;
}

QPushButton#primaryButton:hover {
    background-color: #8b6dff;
}

QPushButton#secondaryButton {
    background-color: #252a34;
    border: 1px solid #363c49;
    border-radius: 7px;
    color: #f1f3f5;
    min-height: 28px;
    padding: 0 10px;
}

QPushButton#secondaryButton:hover {
    background-color: #303643;
    border-color: #7c5cff;
}

QPushButton#secondaryButton:disabled {
    color: #666d7b;
    border-color: #292e38;
}

QPushButton#playerButton {
    background-color: transparent;
    border: none;
    border-radius: 17px;
    color: #d9dce3;
    font-size: 17px;
    min-height: 34px;
    min-width: 34px;
}

QPushButton#playerButton:hover {
    background-color: #2b2f38;
}

QPushButton#playerButton:disabled {
    color: #606571;
}

QFrame#playerBar {
    background-color: #181b21;
    border-top: 1px solid #2a2e38;
}

QSlider::groove:horizontal {
    background: #333843;
    border-radius: 2px;
    height: 4px;
}

QSlider::sub-page:horizontal {
    background: #7c5cff;
    border-radius: 2px;
}

QSlider::handle:horizontal {
    background: #f4f5f7;
    border: none;
    border-radius: 6px;
    height: 12px;
    margin: -4px 0;
    width: 12px;
}
"""
