from PySide6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout
from PySide6.QtCore import QTimer, Qt
import sys

class KeyPressLogger(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Logger des entrées clavier")

        # Configuration de l'affichage
        self.label = QLabel("Appuyez sur une touche pour voir son nom et son code.")
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)

        # Configurer le timer pour exécuter la fonction check_key_input toutes les 100ms
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_key_input)
        self.timer.start(100)  # Temps en millisecondes

    def check_key_input(self):
        # Exemple de code à exécuter en continu sans bloquer l'interface
        pass  # Vous pouvez ajouter des vérifications ici si nécessaire

    def keyPressEvent(self, event):
        # Capture et affiche la touche pressée
        key = event.key()
        print("key : ",key)
        # Utiliser une alternative pour obtenir le nom si disponible, sinon afficher Key_Unknown
        key_name = Qt.Key(key).name if key < 0x01000000 else "Key_Unknown"
        self.label.setText(f"Touche pressée : {key}, Nom de la touche : {key_name}")
        print(f"Touche pressée : {key}, Nom de la touche : {key_name}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = KeyPressLogger()
    window.show()
    sys.exit(app.exec())
