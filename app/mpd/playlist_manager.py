# app/mpd/playlist_manager.py

from .mpd_client import MPDClientWrapper


class PlaylistManager:
    def __init__(self, mpd_client: MPDClientWrapper):
        self.mpd_client = mpd_client
        print("list_playlists : ",self.list_playlists())

    def list_playlists(self):
        """Liste toutes les playlists enregistrées."""
        try:
            return self.mpd_client.client.listplaylists()

        except Exception as e:
            print(f"Erreur en listant les playlists : {e}")
            return []

    def load_playlist(self, playlist_name):
        """Charge une playlist existante dans la playlist actuelle."""
        try:
            self.mpd_client.client.clear()  # Efface la playlist actuelle
            self.mpd_client.client.load(playlist_name)
        except Exception as e:
            print(f"Erreur en chargeant la playlist {playlist_name} : {e}")

    def save_playlist(self, playlist_name):
        """Enregistre la playlist actuelle sous le nom donné."""
        try:
            self.mpd_client.client.save(playlist_name)
        except Exception as e:
            print(f"Erreur en sauvegardant la playlist {playlist_name} : {e}")

    def delete_playlist(self, playlist_name):
        """Supprime une playlist existante."""
        try:
            self.mpd_client.client.rm(playlist_name)
        except Exception as e:
            print(f"Erreur en supprimant la playlist {playlist_name} : {e}")
