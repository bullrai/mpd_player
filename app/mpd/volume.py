# app/mpd/volume.py

from .mpd_client import MPDClientWrapper

class VolumeControl:
    def __init__(self, mpd_client: MPDClientWrapper):
        self.mpd_client = mpd_client

    def set_volume(self, volume):
        """Définit le volume en fonction d'une valeur entre 0 et 100."""
        try:
            self.mpd_client.client.setvol(volume)
        except Exception as e:
            print(f"Erreur de réglage du volume : {e}")

    def get_volume(self):
        """Récupère le volume actuel."""
        try:
            status = self.mpd_client.client.status()
            return int(status.get("volume", 0))
        except Exception as e:
            print(f"Erreur en récupérant le volume : {e}")
            return 0
