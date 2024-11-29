# app/mpd/volume.py
import time
from .mpd_client import MPDClientWrapper

class VolumeControl:
    def __init__(self, mpd_client: MPDClientWrapper):
        self.mpd_client = mpd_client
        self.volume_cache = 0

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

    def fade_in_set_progress(self):
        fade_duration = 0.5  # Durée totale du fade-in en secondes
        steps = 10  # Nombre d'étapes dans le fade
        # Faire un fade-in pour remonter au volume initial
        # for volume in range(0, current_volume + 1, int(current_volume / steps)):
        self.volume_cache = self.get_volume()
        self.set_volume(0)
            # time.sleep(fade_duration / steps)


    def fade_out_set_progress(self):
        fade_duration = 0.1  # Durée totale du fade-in en secondes
        steps = 20  # Nombre d'étapes dans le fade
        print("volume ac : ",self.volume_cache)
        for volume in range(self.volume_cache+1):
            print(volume)
            self.set_volume(volume)
            time.sleep(fade_duration / steps)