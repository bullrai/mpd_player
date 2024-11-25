from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QTabWidget, QMessageBox, QHBoxLayout, QInputDialog
)
from PySide6.QtCore import Qt
from app.mpd.playlist_manager import PlaylistManager
from app.utils.playlist_table_view import StyledPlaylistTableView


class PlaylistTab(QWidget):
    def __init__(self, mpd_client):
        super().__init__()
        self.playlist_manager = PlaylistManager(mpd_client)
        self.mpd_client = mpd_client
        # Configuration principale
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # Onglets pour chaque playlist
        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)

        # Boutons pour gestion des playlists
        button_layout = QHBoxLayout()
        save_button = QPushButton("Enregistrer les modifications")
        save_button.clicked.connect(self.save_current_playlist)

        refresh_button = QPushButton("Actualiser les playlists")
        refresh_button.clicked.connect(self.refresh_playlists)

        new_playlist_button = QPushButton("+")
        new_playlist_button.setToolTip("Enregistrer la playlist active sous un nouveau nom")
        new_playlist_button.clicked.connect(self.save_active_playlist_as_new)

        button_layout.addWidget(save_button)
        button_layout.addWidget(refresh_button)
        button_layout.addWidget(new_playlist_button)
        self.layout.addLayout(button_layout)

        # Charger les playlists existantes
        # self.refresh_playlists()

    def refresh_playlists(self):
        """Recharge toutes les playlists dans les onglets."""
        self.tabs.clear()
        playlists = self.playlist_manager.list_playlists()
        for playlist in playlists:
            playlist_name = playlist["playlist"]
            self.add_playlist_tab(playlist_name)

    def add_playlist_tab(self, playlist_name):
        """Ajoute un onglet pour une playlist donnée."""
        songs = self.get_playlist_songs(playlist_name)

        # Crée une vue tabulaire stylisée pour afficher les morceaux
        playlist_view = StyledPlaylistTableView(songs)

        # Ajout à l'onglet
        tab = QWidget()
        tab_layout = QVBoxLayout()
        tab_layout.addWidget(playlist_view)
        tab.setLayout(tab_layout)
        self.tabs.addTab(tab, playlist_name)

        # Connecter les événements pour la navigation et l'ordre
        playlist_view.keyPressEvent = lambda event: self.handle_key_event(event, playlist_view)

    def get_playlist_songs(self, playlist_name):
        """Récupère les morceaux d'une playlist donnée."""
        try:

            self.mpd_client.load_playlist(playlist_name)

            return self.mpd_client.get_current_playlist()
        except Exception as e:
            print(f"Erreur lors du chargement de la playlist {playlist_name} : {e}")
            return []

    def handle_key_event(self, event, playlist_view):
        """Gère les touches pour naviguer et modifier l'ordre."""
        current_index = playlist_view.selectionModel().currentIndex()
        if not current_index.isValid():
            return

        # Vérifie si 'Ctrl' est enfoncé pour le déplacement
        if event.modifiers() == Qt.ControlModifier:
            if event.key() == Qt.Key_Up:
                # Déplacer la ligne vers le haut avec Ctrl+Up
                self.move_row(playlist_view, current_index.row(), -1)
                return
            elif event.key() == Qt.Key_Down:
                # Déplacer la ligne vers le bas avec Ctrl+Down
                self.move_row(playlist_view, current_index.row(), 1)
                return
            self.move_row(playlist_view, current_index.row(), 1)
        elif event.key() in (Qt.Key_Return, Qt.Key_Enter):
            # Jouer la chanson
            self.play_song(current_index.row())
        else:
            # Appeler l'événement par défaut
            super(StyledPlaylistTableView, playlist_view).keyPressEvent(event)

    def move_row(self, playlist_view, current_row, direction):
        """Déplace une ligne vers le haut ou le bas dans la vue."""
        model = playlist_view.model()
        new_row = current_row + direction
        if 0 <= new_row < model.rowCount():
            model.moveRow(current_row, new_row)
            playlist_view.selectRow(new_row)  # Sélectionner la nouvelle ligne

    def play_song(self, row):
        """Joue une chanson à partir de la playlist active."""
        try:
            self.mpd_client.play_song_at(row)

            QMessageBox.information(self, "Lecture", f"Lecture de la chanson à la position {row}.")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de lire la chanson : {e}")

    def save_current_playlist(self):
        """Sauvegarde les modifications dans la playlist active."""
        current_tab_index = self.tabs.currentIndex()
        if current_tab_index == -1:
            QMessageBox.warning(self, "Erreur", "Aucune playlist sélectionnée.")
            return

        playlist_name = self.tabs.tabText(current_tab_index)
        table_view = self.tabs.currentWidget().layout().itemAt(0).widget()
        model = table_view.model()

        try:
            # Efface et sauvegarde la playlist avec l'ordre mis à jour
            # self.mpd_client.client.clear()
            for song in model.playlist_data:
                self.mpd_client.add_to_playlist(song.get("file"))

            self.playlist_manager.save_playlist(playlist_name)
            QMessageBox.information(self, "Succès", f"Playlist '{playlist_name}' enregistrée.")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de sauvegarder la playlist : {e}")

    def save_active_playlist_as_new(self):
        """Demande un nouveau nom et sauvegarde la playlist active."""
        current_tab_index = self.tabs.currentIndex()
        if current_tab_index == -1:
            QMessageBox.warning(self, "Erreur", "Aucune playlist active.")
            return

        # Demander un nom pour la nouvelle playlist
        new_playlist_name, ok = QInputDialog.getText(
            self, "Nouvelle Playlist", "Entrez le nom de la nouvelle playlist :"
        )

        if ok and new_playlist_name.strip():
            playlist_name = self.tabs.tabText(current_tab_index)
            table_view = self.tabs.currentWidget().layout().itemAt(0).widget()
            model = table_view.model  # Correction ici : pas d'appel, c'est un attribut

            try:
                # Efface et sauvegarde la nouvelle playlist
                self.mpd_client.client.clear()
                for song in model.playlist_data:
                    self.mpd_client.client.add(song.get("file"))
                self.playlist_manager.save_playlist(new_playlist_name)
                QMessageBox.information(self, "Succès", f"Playlist '{new_playlist_name}' enregistrée.")
                self.refresh_playlists()
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Impossible de sauvegarder la nouvelle playlist : {e}")
        elif ok:
            QMessageBox.warning(self, "Erreur", "Le nom de la playlist ne peut pas être vide.")

