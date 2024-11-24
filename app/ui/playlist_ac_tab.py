# app/ui/player_tab.py

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QListWidget
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QKeyEvent
from app.mpd.mpd_client import MPDClientWrapper
from app.utils.playlist_table_view import StyledPlaylistTableView
import sys


class PlaylistAcTab(QWidget):
    def __init__(self, mpd_client: MPDClientWrapper):
        super().__init__()
        self.mpd_client = mpd_client


        # Configuration de la mise en page
        self.layout = QVBoxLayout()


        # Liste de la playlist
        self.playlist_view = StyledPlaylistTableView(self.init_playlist())
        self.layout.addWidget(self.playlist_view)


        # Connecter le signal de double-clic à la méthode de lecture
        self.playlist_view.doubleClicked.connect(self.play_selected_song)


        self.setLayout(self.layout)

    def init_playlist(self):
        """Met à jour la playlist active depuis MPD."""
        self.playlist_data = []
        # self.playlist_view.clear()
        try:
            self.playlist_data = self.mpd_client.get_current_playlist()  # Méthode à définir dans MPDClient

            return self.playlist_data
            # for song in playlist:
            #     self.playlist_list_widget.addItem(f"{song['artist']} - {song['title']}")
        except Exception as e:
            print(f"Erreur lors de la récupération de la playlist : {e}", file=sys.stderr)
            self.playlist_data("Erreur lors de la récupération de la playlist.")

    def update_playlist(self):
        # self.playlist_view.clear()
        self.playlist_data = self.mpd_client.get_current_playlist()
        self.playlist_view.update_playlist_view(self.playlist_data)

    def play_selected_song(self, index):
        """Joue la chanson sélectionnée."""
        if index.isValid():
            song_position = index.row()  # Récupère la position dans la playlist
            try:
                self.mpd_client.client.play(song_position)
                print(f"Lecture de la chanson à la position : {song_position}")
            except Exception as e:
                print(f"Erreur lors de la lecture de la chanson : {e}")

    def keyPressEvent(self, event: QKeyEvent):
        """Détecte la touche Entrée et joue la chanson sélectionnée."""
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            current_index = self.playlist_view.selectionModel().currentIndex()
            if current_index.isValid():
                self.play_selected_song(current_index)
        else:
            super().keyPressEvent(event)