# app/main.py

import sys
from pathlib import Path
# Ajouter le répertoire parent au PYTHONPATH
sys.path.append(str(Path(__file__).resolve().parent.parent))
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont

from app.ui.main_window import MainWindow
from app.utils.config_loader import config_instance

def main():

    app = QApplication(sys.argv)
    font_family = config_instance.data["font"]["family"]
    font_size = config_instance.data["font"]["size"]
    global_font = QFont(font_family,font_size)
    app.setFont(global_font)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
