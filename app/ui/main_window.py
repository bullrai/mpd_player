# app/ui/main_window.py
import sys
from pathlib import Path

from PyQt5.QtWidgets import QBoxLayout

# Ajouter le répertoire parent au PYTHONPATH
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
print("Chemin ajouté au PYTHONPATH :", Path(__file__).resolve().parent.parent.parent)

import yaml
from PySide6.QtWidgets import (QApplication, QMainWindow, QTabWidget, QWidget,
                               QVBoxLayout, QHBoxLayout, QPushButton,QStackedWidget
                               )
from PySide6.QtGui import QScreen, QKeySequence, QShortcut, QIcon, QFontDatabase, QFont
from PySide6.QtCore import QSize, Qt
from app.mpd.mpd_client import MPDClientWrapper
# from app.ui.player_tab import PlayerTab
from app.ui.playlist_tab import PlaylistTab
from app.ui.browser_tab import BrowserTab
from app.ui.control_bar import ControlBar
from app.ui.playlist_ac_tab import PlaylistAcTab
from app.utils.config_loader import config_instance
# app/ui/main_window.py

from app.ui.custom_title_bar import CustomTitleBar  # Importer la barre d'en-tête personnalisée




class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.mpd_client = MPDClientWrapper()

        QFontDatabase.addApplicationFont("app/assets/images/Untitled1.ttf")
        background_color = config_instance.data["colors"]["background"]
        border_window = config_instance.data["colors"]["border_window"]
        font = config_instance.data["font"]["family"]
        font_player = QFont("Untitled1", 24)
        player_button = config_instance.data["colors"]["player_button"]
        player_button_hover = config_instance.data["colors"]["player_button_hover"]

        # Configuration de la fenêtre principale
        self.setWindowTitle("Lecteur Audio MPD")
        self.resize(350, 600)
        #
        # self.adjustSize()
        self.setWindowFlags(Qt.FramelessWindowHint)  # Supprimer les bordures de la fenêtre
        self.setAttribute(Qt.WA_TranslucentBackground)
        # self.setStyleSheet(f"""
        #             QMainWindow {{
        #                 background-color: {background_color};
        #                 border-radius: 5px;  /* Ajustez le rayon des coins */
        #             }}
        #         """)

        # Layout principal vertical
        main_widget = QWidget()
        main_widget.setObjectName("Container")
        main_widget.setStyleSheet(f"""
                    #Container {{
                        background-color: {background_color};
                        border: 1px solid {border_window};
                        border-radius: 10px;  /* Ajustez le rayon des coins */
                        
                    }}
                """)
        # main_widget.setContentsMargins(1,1,1,1)
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(2,2,2,2)
        # main_layout.setSpacing(0)

        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        # Ajouter la barre d'en-tête personnalisée
        title_bar = CustomTitleBar(self)
        main_layout.addWidget(title_bar)

        # Initialiser et ajouter la barre de contrôle
        control_bar = ControlBar(self.mpd_client)
        main_layout.addWidget(control_bar)

        # Bouton toggle



        # Conteneur horizontal pour les boutons de navigation et le contenu
        self.content_layout = QVBoxLayout()
        button_box = QHBoxLayout()

        self.toggle_button = QPushButton("\u0046")
        self.toggle_button.setStyleSheet(f"background-color: transparent;")
        self.toggle_button.clicked.connect(self.toggle_content_layout)

        self.playlistac_button = QPushButton("Playlist Active")
        self.playlistac_button.setStyleSheet(f"background-color: transparent;")
        self.playlistac_button.clicked.connect(self.show_playlistac)

        # self.playlist_button = QPushButton("Playlists")
        # self.playlist_button.setStyleSheet(f"font-family: transparent;")
        # self.playlist_button.clicked.connect(self.show_playlist)

        self.browser_button = QPushButton("Navigateur")
        self.browser_button.setStyleSheet(f"background-color: transparent;")
        self.browser_button.clicked.connect(self.show_browser)



        button_box.addWidget(self.toggle_button)
        button_box.addWidget(self.playlistac_button)
        button_box.addWidget(self.browser_button)

        # button_box.addWidget(self.playlist_button)


        self.content_layout.addLayout(button_box)

        self.content_area = QStackedWidget()
        self.playlistac_tab = PlaylistAcTab(self.mpd_client)
        # self.playlist_tab = PlaylistTab(self.mpd_client)
        self.browser_tab = BrowserTab(self.mpd_client, self.playlistac_tab)

        self.content_area.addWidget(self.playlistac_tab)
        # self.content_area.addWidget(self.playlist_tab)
        self.content_area.addWidget(self.browser_tab)
        self.content_layout.addWidget(self.content_area)

        main_layout.addLayout(self.content_layout)
        main_layout.addStretch()

        # Affichage initial
        # self.hide_content_layout()

        # Variable pour suivre l'état
        self.is_content_hidden = False
        self.resize(350, 500)

        # Raccourcis globaux
        self.setup_shortcuts()

    def toggle_content_layout(self):
        """Bascule entre cacher et afficher le content_layout."""
        self.is_content_hidden = not self.is_content_hidden  # Inverse l'état

        # Cacher ou afficher les widgets dans le layout
        for i in range(self.content_layout.count()):
            widget = self.content_layout.itemAt(i).widget()
            if widget:
                widget.setVisible(not self.is_content_hidden)


        # Met à jour le texte du bouton
        if self.is_content_hidden:
            self.toggle_button.setText("Afficher Contenu")
            print("change size")
            self.setFixedSize(350, 280)
        else:
            self.toggle_button.setText("Cacher Contenu")
            self.setFixedSize(350, 500)
            print("change size")
        # Ajuste la taille de la fenêtre
        # self.adjustSize()


    def show_playlistac(self):
        """Affiche la section Playlist active dans la zone de contenu."""
        self.content_area.setCurrentWidget(self.playlistac_tab)

    def show_playlist(self):
        """Affiche la section Gestion de Playlists dans la zone de contenu."""
        self.content_area.setCurrentWidget(self.playlist_tab)

    def show_browser(self):
        """Affiche la section Navigateur dans la zone de contenu."""
        self.content_area.setCurrentWidget(self.browser_tab)

    def showEvent(self, event):
        """Déplace la fenêtre vers l'écran spécifié par screen_index."""
        super().showEvent(event)

        # Récupère la géométrie de l'écran principal
        screen = QApplication.primaryScreen()
        screen_geometry = screen.geometry()

        # Utiliser frameGeometry après show pour un calcul précis
        # frame_geometry = self.frameGeometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.move(screen_geometry.x() + x, screen_geometry.y() + y)

    def load_shortcuts(self):
        """Charge les raccourcis depuis un fichier YAML."""
        config_path = Path("config/shortcuts.yaml")
        # print("config_path : ",config_path)
        try:
            with open(config_path, "r") as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            print("Fichier de configuration des raccourcis non trouvé.")
            return {}
        except yaml.YAMLError:
            print("Erreur de lecture du fichier YAML des raccourcis.")
            return {}

    def setup_shortcuts(self):
        """Configure les raccourcis clavier globaux pour l'application en utilisant le fichier de configuration."""
        shortcuts = self.load_shortcuts()
        # print("bzkbz : ",shortcuts)
        # Raccourcis globaux
        global_shortcuts = shortcuts.get("globalz", {})
        # print("global_shortcuts : ",shortcuts)
        # print(global_shortcuts.get("play_pause"))
        QShortcut(QKeySequence(global_shortcuts.get("play_pause")), self).activated.connect(self.toggle_play_pause)
        QShortcut(QKeySequence(global_shortcuts.get("next_track")), self).activated.connect(self.next_track)
        QShortcut(QKeySequence(global_shortcuts.get("previous_track")), self).activated.connect(self.previous_track)
        QShortcut(QKeySequence(global_shortcuts.get("volume_up")), self).activated.connect(self.volume_up)
        QShortcut(QKeySequence(global_shortcuts.get("volume_down")), self).activated.connect(self.volume_down)
        QShortcut(QKeySequence(global_shortcuts.get("playlist")), self).activated.connect(self.show_playlistac)
        QShortcut(QKeySequence(global_shortcuts.get("library")), self).activated.connect(self.show_browser)

        # Vous pouvez ajouter d'autres raccourcis spécifiques aux onglets ici

    # Actions des raccourcis (inchangées)
    def toggle_play_pause(self):
        """Active/désactive la lecture."""
        status = self.mpd_client.get_status()
        if status.get("state") == "play":
            self.mpd_client.pause()
        else:
            self.mpd_client.play()

    def next_track(self):
        """Passe à la piste suivante."""
        self.mpd_client.next_track()

    def previous_track(self):
        """Revient à la piste précédente."""
        self.mpd_client.previous_track()

    def volume_up(self):
        """Augmente le volume."""
        volume = int(self.mpd_client.get_status().get("volume", 0))
        self.mpd_client.set_volume(min(volume + 10, 100))


    def volume_down(self):
        """Diminue le volume."""
        volume = int(self.mpd_client.get_status().get("volume", 0))
        self.mpd_client.set_volume(max(volume - 10, 0))

    def next_tab(self):
        """Passe à l'onglet suivant."""
        self.show_playlistac()

    def previous_tab(self):
        """Revient à l'onglet précédent."""
        self.show_browser()


