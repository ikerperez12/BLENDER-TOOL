# Theme configuration and stylesheet for IP Blender Tool

DARK_THEME_STYLE = """
/* Global styling */
QWidget {
    background-color: #121214;
    color: #e4e4e7;
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, Helvetica, Arial, sans-serif;
    font-size: 13px;
}

/* Main window background */
QMainWindow {
    background-color: #121214;
}

/* Cards / Section Frames */
QFrame#sectionFrame {
    background-color: #1e1e24;
    border: 1px solid #2d2d34;
    border-radius: 8px;
    padding: 10px;
}

/* Titles and Headers */
QLabel#headerTitle {
    font-size: 18px;
    font-weight: bold;
    color: #ffffff;
}

QLabel#subtitle {
    font-size: 12px;
    color: #71717a;
}

QLabel#sectionTitle {
    font-size: 14px;
    font-weight: bold;
    color: #0da2ff;
    margin-bottom: 5px;
}

/* Inputs and Line Edits */
QLineEdit {
    background-color: #18181b;
    border: 1px solid #3f3f46;
    border-radius: 4px;
    padding: 6px 10px;
    color: #f4f4f5;
}

QLineEdit:focus {
    border: 1px solid #0da2ff;
    background-color: #1f1f23;
}

/* Dropdowns and Combo Boxes */
QComboBox {
    background-color: #18181b;
    border: 1px solid #3f3f46;
    border-radius: 4px;
    padding: 5px 10px;
    color: #f4f4f5;
    combobox-popup: 0;
}

QComboBox:focus {
    border: 1px solid #0da2ff;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 25px;
    border-left: none;
}

/* Buttons */
QPushButton {
    background-color: #27272a;
    border: 1px solid #3f3f46;
    border-radius: 4px;
    padding: 6px 12px;
    color: #f4f4f5;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #3f3f46;
    border-color: #52525b;
}

QPushButton:pressed {
    background-color: #18181b;
}

/* Accent Buttons (Primary action) */
QPushButton#primaryButton {
    background-color: #007acc;
    border: 1px solid #0da2ff;
    color: #ffffff;
}

QPushButton#primaryButton:hover {
    background-color: #0da2ff;
}

QPushButton#primaryButton:pressed {
    background-color: #005999;
}

/* Stop/Cancel Buttons */
QPushButton#dangerButton {
    background-color: #7f1d1d;
    border: 1px solid #b91c1c;
    color: #fecaca;
}

QPushButton#dangerButton:hover {
    background-color: #b91c1c;
}

QPushButton#dangerButton:pressed {
    background-color: #450a0a;
}

/* Checkboxes */
QCheckBox {
    spacing: 8px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 1px solid #3f3f46;
    border-radius: 3px;
    background-color: #18181b;
}

QCheckBox::indicator:hover {
    border-color: #0da2ff;
}

QCheckBox::indicator:checked {
    background-color: #007acc;
    border-color: #0da2ff;
    image: url(data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>);
}

/* Table styling */
QTableWidget {
    background-color: #18181b;
    border: 1px solid #2d2d34;
    border-radius: 6px;
    gridline-color: #27272a;
}

QHeaderView::section {
    background-color: #1e1e24;
    color: #a1a1aa;
    padding: 5px;
    border: none;
    border-bottom: 1px solid #2d2d34;
    font-weight: bold;
}

QTableWidget::item {
    padding: 5px;
}

QTableWidget::item:selected {
    background-color: #27272a;
    color: #ffffff;
}

/* Progress bar */
QProgressBar {
    border: 1px solid #2d2d34;
    border-radius: 4px;
    text-align: center;
    background-color: #18181b;
    color: #ffffff;
    font-weight: bold;
}

QProgressBar::chunk {
    background-color: #007acc;
    border-radius: 3px;
}

/* Scrollbars */
QScrollBar:vertical {
    background-color: #121214;
    width: 10px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background-color: #27272a;
    min-height: 20px;
    border-radius: 5px;
}

QScrollBar::handle:vertical:hover {
    background-color: #3f3f46;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* Text Edit / Console */
QTextEdit#consoleBox {
    background-color: #0b0b0c;
    border: 1px solid #1f1f23;
    border-radius: 6px;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 12px;
    color: #a1a1aa;
    padding: 8px;
}
"""

STATUS_STYLES = {
    "Pending": "color: #a1a1aa; font-weight: bold;",
    "Running": "color: #3b82f6; font-weight: bold;",
    "Completed": "color: #10b981; font-weight: bold;",
    "Failed": "color: #ef4444; font-weight: bold;",
    "Cancelled": "color: #f59e0b; font-weight: bold;",
}
