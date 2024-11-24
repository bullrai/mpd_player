# app/ui/custom_title_bar.py
from PyQt5.QtCore import QSize
from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton
from future.standard_library import import_

from PySide6.QtGui import QFontDatabase, QFont
from PySide6.QtCore import Qt, QPoint
from app.utils.config_loader import config_instance

def setup_button_style(buttons, color1, color2, size=QSize(32,32)):
    """Applique le style de base aux boutons."""

    sizeb = size

    for button in buttons:
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {color1};
                border: none;
                font-size: 20px;
                font-family: Untitled1;
                width: 20px;   /* Largeur fixe du bouton */
                height: 20px;   /* Hauteur fixe du bouton */
            }}
            QPushButton:hover {{
                color: {color2};

            }}
        """)
        # button.setFixedSize(30,20)
        # button.setFixedWidth(20)

class CustomTitleBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # self.setFixedHeight(32)  # Hauteur de la barre d'en-tête
        # self.setStyleSheet("background-color: #6A0DAD;")  # Couleur de fond de la barre
        QFontDatabase.addApplicationFont("app/assets/images/Untitled1.ttf")

        font_player = QFont("Untitled1", 24)  # Nom de votre police
        font = config_instance.data["font"]["family"]
        text_secondary = config_instance.data["colors"]["text_secondary"]
        text_primary = config_instance.data["colors"]["text_primary"]

        # Création du layout principal
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        # layout.setSpacing(10)
        # self.setFixedHeight(32)


        # Boutons de gauche
        self.left_button_1 = QPushButton("Left 1")
        self.left_button_2 = QPushButton("Left 2")
        self.left_button_3 = QPushButton("Left 3")
        setup_button_style([self.left_button_1, self.left_button_2, self.left_button_3], text_primary, text_secondary, QSize(50,32))

        # Ajouter les boutons de gauche au layout
        layout.addWidget(self.left_button_1)
        layout.addWidget(self.left_button_2)
        layout.addWidget(self.left_button_3)

        # Ajouter un espace extensible au centre pour séparer les boutons de gauche et de droite
        layout.addStretch()

        # Boutons de droite (fermer, minimiser, maximiser)
        self.minimize_button = QPushButton("\u0049")
        self.maximize_button = QPushButton("\u004a")
        self.close_button = QPushButton("\u004b")
        setup_button_style([self.minimize_button, self.maximize_button, self.close_button], text_primary, text_secondary, QSize(32,32))

        # Ajouter les boutons de droite au layout
        layout.addWidget(self.minimize_button)
        layout.addWidget(self.maximize_button)
        layout.addWidget(self.close_button)

        # Connecter les boutons aux actions de la fenêtre principale
        self.close_button.clicked.connect(parent.close)
        self.minimize_button.clicked.connect(parent.showMinimized)
        self.maximize_button.clicked.connect(parent.showMaximized)

        # Variables pour le déplacement de la fenêtre
        self.old_pos = None

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.old_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if self.old_pos:
            delta = event.globalPosition().toPoint() - self.old_pos
            self.window().move(self.window().x() + delta.x(), self.window().y() + delta.y())
            self.old_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.old_pos = None
