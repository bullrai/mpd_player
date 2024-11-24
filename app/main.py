# app/main.py

import sys
from pathlib import Path
# Ajouter le répertoire parent au PYTHONPATH
sys.path.append(str(Path(__file__).resolve().parent.parent))
from PySide6.QtWidgets import QApplication
from app.ui.main_window import MainWindow

def main():

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
