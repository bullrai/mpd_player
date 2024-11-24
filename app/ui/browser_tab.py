# app/ui/browser_tab.py

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QListWidget, QPushButton
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut
from app.mpd.mpd_client import MPDClientWrapper
from app.utils.config_loader import config_instance

class BrowserTab(QWidget):
    def __init__(self, mpd_client: MPDClientWrapper, playlist_ac_tab):
        super().__init__()
        self.mpd_client = mpd_client
        self.playlist_ac_tab = playlist_ac_tab  # Référence à PlaylistAcTab
        self.current_path = ""  # Commence dans le dossier racine

        self.library_text = config_instance.data["colors"]["library_text"]
        self.library_selected = config_instance.data["colors"]["library_selected"]
        self.library_text_selected = config_instance.data["colors"]["library_text_selected"]
        self.font =  config_instance.data["font"]["family"]

        self.setup_ui()
        self.load_library()  # Charger la bibliothèque à la racine au démarrage
        self.setup_shortcuts()

    def setup_ui(self):
        # Layout principal
        layout = QVBoxLayout()

        # Bouton Retour
        self.back_button = QPushButton("Retour")
        self.back_button.setVisible(False)  # Masqué par défaut
        self.back_button.clicked.connect(self.go_to_parent_directory)
        layout.addWidget(self.back_button)

        # Titre de l'onglet
        layout.addWidget(QLabel("Navigateur de bibliothèque"))

        # Liste des dossiers/fichiers
        self.library_list = QListWidget()
        self.library_list.setStyleSheet(f"""
            QListWidget {{
                background-color: transparent;
                color: {self.library_text};
                font-family: {self.font};
            }}
            QListWidget::item:selected {{
                background-color: {self.library_selected};
                color: {self.library_text_selected};
            }}
        """)
        self.library_list.itemClicked.connect(self.open_directory_or_file)
        layout.addWidget(self.library_list)

        # Appliquer le layout à l'onglet
        self.setLayout(layout)

    def setup_shortcuts(self):
        """Configure les raccourcis pour la navigation clavier et l'ajout à la playlist."""
        # Raccourci pour ajouter à la playlist avec la touche '0'
        add_to_playlist_shortcut = QShortcut(QKeySequence("0"), self)
        add_to_playlist_shortcut.activated.connect(self.add_selected_to_playlist)

        # Navigation dans la liste avec les flèches et les touches Entrée/Retour Arrière
        self.setFocusPolicy(Qt.StrongFocus)

    def keyPressEvent(self, event):
        """Gère les événements de touches pour la navigation dans la liste."""
        if event.key() == Qt.Key_Down:
            # Flèche Bas : se déplacer vers le bas dans la liste
            next_row = (self.library_list.currentRow() + 1) % self.library_list.count()
            self.library_list.setCurrentRow(next_row)
        elif event.key() == Qt.Key_Up:
            # Flèche Haut : se déplacer vers le haut dans la liste
            previous_row = (self.library_list.currentRow() - 1) % self.library_list.count()
            self.library_list.setCurrentRow(previous_row)
        elif event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            # Entrée : ouvrir le dossier ou sélectionner le fichier
            current_item = self.library_list.currentItem()
            if current_item:
                self.open_directory_or_file(current_item)
        elif event.key() == Qt.Key_Backspace:
            # Retour Arrière : revenir au dossier parent
            self.go_to_parent_directory()
        else:
            # Appel de la méthode parente pour les autres touches
            super().keyPressEvent(event)

    def load_library(self, path=""):
        """Charge les dossiers et fichiers audio dans le chemin spécifié sans descendre dans les sous-dossiers."""
        self.library_list.clear()
        self.current_path = path
        self.back_button.setVisible(bool(path))  # Affiche le bouton Retour si on n'est pas à la racine

        try:
            # Récupère uniquement les dossiers et fichiers du chemin actuel
            items = self.mpd_client.client.lsinfo(path)

            for item in items:
                if 'directory' in item:
                    # Affiche les dossiers uniquement
                    self.library_list.addItem(f"[Dossier] {item['directory'].split('/')[-1]}")
                elif 'file' in item and self.is_audio_file(item['file']):
                    # Affiche uniquement les fichiers audio
                    self.library_list.addItem(item['file'].split('/')[-1])

            # Mettre le focus sur le premier élément s'il y a des éléments
            if self.library_list.count() > 0:
                self.library_list.setCurrentRow(0)

        except Exception as e:
            print(f"Erreur en chargeant la bibliothèque musicale : {e}")

    def is_audio_file(self, filename):
        """Vérifie si le fichier a une extension audio valide."""
        audio_extensions = {".mp3", ".flac", ".wav", ".aac", ".ogg"}
        return any(filename.lower().endswith(ext) for ext in audio_extensions)

    def open_directory_or_file(self, item):
        """Ouvre un dossier ou traite un fichier lorsqu'un élément est cliqué."""
        item_text = item.text()

        if item_text.startswith("[Dossier]"):
            # Si c'est un dossier, on charge son contenu
            directory_name = item_text[10:]  # Retire "[Dossier] " pour obtenir le nom réel
            new_path = f"{self.current_path}/{directory_name}" if self.current_path else directory_name
            self.load_library(new_path)
        else:
            # Ici, on peut gérer l'action pour un fichier audio si nécessaire
            print(f"Fichier audio sélectionné : {item_text}")

    def go_to_parent_directory(self):
        """Remonte d'un niveau dans le répertoire actuel."""
        if "/" in self.current_path:
            # Remonte d'un niveau en enlevant la dernière partie du chemin
            parent_path = "/".join(self.current_path.split("/")[:-1])
        else:
            # Si on est déjà à la racine, on définit le chemin vide
            parent_path = ""
        
        self.load_library(parent_path)

    def add_selected_to_playlist(self):
        """Ajoute l'élément sélectionné à la playlist active de MPD."""
        current_item = self.library_list.currentItem()
        if current_item:
            item_text = current_item.text()
            if item_text.startswith("[Dossier]"):
                directory_name = item_text[10:]  # Enlève "[Dossier] " pour obtenir le nom réel
                full_path = f"{self.current_path}/{directory_name}" if self.current_path else directory_name
                self.mpd_client.client.add(full_path)  # Ajoute le dossier complet à la playlist
                print(f"Dossier ajouté à la playlist : {full_path}")
            else:
                full_path = f"{self.current_path}/{item_text}" if self.current_path else item_text
                self.mpd_client.client.add(full_path)  # Ajoute le fichier audio à la playlist
                print(f"Fichier ajouté à la playlist : {full_path}")
            # Actualiser PlaylistAcTab après l'ajout
            if self.playlist_ac_tab:
                self.playlist_ac_tab.update_playlist()