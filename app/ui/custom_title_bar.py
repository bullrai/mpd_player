# app/ui/custom_title_bar.py
from PySide6.QtCore import QSize
from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton


from PySide6.QtGui import QFontDatabase, QFont
from PySide6.QtCore import Qt, QPoint
from app.utils.config_loader import config_instance

def setup_button_style(button, color1, color2, font, font_size, size=[32,32]):
    """Applique le style de base aux boutons."""

    width = size[0]
    height = size[1]
    height_button = height -12
    QSize()
    button.setStyleSheet(f"""
        QPushButton {{
            background-color: transparent;
            color: {color1};
            border: none;
            font-size: {font_size}px;
            font-family: {font};
            width: {width}px;   /* Largeur fixe du bouton */
            height: {height}px;   /* Hauteur fixe du bouton */
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

        font_player = "Untitled1"  # Nom de votre police
        font = config_instance.data["font"]["family"]
        font_size = config_instance.data["font"]["size"]
        text_secondary = config_instance.data["colors"]["text_secondary"]
        text_primary = config_instance.data["colors"]["text_primary"]
        button_close = config_instance.data["colors"]["button_close"]
        button_close_hove = config_instance.data["colors"]["button_close_hove"]
        button_maximize = config_instance.data["colors"]["button_close"]
        button_maximize_hove = config_instance.data["colors"]["button_close_hove"]
        button_minimize = config_instance.data["colors"]["button_close"]
        button_minimize_hove = config_instance.data["colors"]["button_close_hove"]

        # Création du layout principal
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        # layout.setSpacing(10)
        # self.setFixedHeight(32)


        # Boutons de gauche #TODO: menu(mpd,réglage...)
        self.left_button_1 = QPushButton("PyMPDM")
        setup_button_style(self.left_button_1, text_primary, text_secondary, font, 14,  [90,32])
        layout.addWidget(self.left_button_1)
        # self.left_button_2 = QPushButton("Left 2")
        # setup_button_style(self.left_button_2, text_primary, text_secondary, font, font_size, [50,32])
        # layout.addWidget(self.left_button_2)
        # self.left_button_3 = QPushButton("Left 3")
        # setup_button_style(self.left_button_3, text_primary, text_secondary, font, font_size, [50,32])
        # layout.addWidget(self.left_button_3)



        # Ajouter un espace extensible au centre pour séparer les boutons de gauche et de droite
        layout.addStretch()

        # Boutons de droite (fermer, minimiser, maximiser)
        self.minimize_button = QPushButton("\u0049")
        setup_button_style(self.minimize_button, button_minimize, button_minimize_hove, font_player, 20, [32,32])
        self.maximize_button = QPushButton("\u004a")
        setup_button_style(self.maximize_button, button_maximize, button_maximize_hove, font_player, 20, [32,32])
        self.close_button = QPushButton("\u004b")
        setup_button_style(self.close_button, button_close, button_close_hove, font_player, 20, [32,32])

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
