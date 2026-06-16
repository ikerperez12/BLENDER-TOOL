import sys
import os

# Add the parent directory of 'app' to sys.path to resolve imports correctly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set environment variables for High DPI scaling to ensure crisp windows on Windows OS
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"

from PySide6.QtWidgets import QApplication
from app.core.db import init_db
from app.ui.main_window import MainWindow

def main():
    # 1. Initialize SQLite Database and Settings
    init_db()
    
    # 2. Start PySide6 Application
    app = QApplication(sys.argv)
    
    # Configure high-DPI font rendering
    font = app.font()
    font.setPointSize(10)
    app.setFont(font)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
