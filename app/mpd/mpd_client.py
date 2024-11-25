# app/mpd/mpd_client.py

from mpd import MPDClient

class MPDClientWrapper:
    def __init__(self, host="localhost", port=6600):
        self.client = MPDClient()
        self.host = host
        self.port = port
        self.connect()

    def connect(self):
        """Connecte au serveur MPD."""
        try:
            self.client.connect(self.host, self.port)
        except Exception as e:
            print(f"Erreur de connexion à MPD : {e}")

    def disconnect(self):
        """Déconnecte du serveur MPD."""
        try:
            self.client.close()
            self.client.disconnect()
        except Exception as e:
            print(f"Erreur de déconnexion de MPD : {e}")

    # Fonctions de lecture de base
    def play(self):
        """Démarre la lecture."""
        try:
            self.client.play()
        except Exception as e:
            print(f"Erreur en lecture : {e}")

    def pause(self):
        """Met en pause la lecture."""
        try:
            self.client.pause()
        except Exception as e:
            print(f"Erreur en pause : {e}")

    def stop(self):
        """Arrête la lecture."""
        try:
            self.client.stop()
        except Exception as e:
            print(f"Erreur en stop : {e}")

    def next_track(self):
        """Passe à la piste suivante."""
        try:
            self.client.next()
        except Exception as e:
            print(f"Erreur en passant à la piste suivante : {e}")

    def previous_track(self):
        """Revient à la piste précédente."""
        try:
            self.client.previous()
        except Exception as e:
            print(f"Erreur en revenant à la piste précédente : {e}")

    def set_volume(self, volume):
        """Définit le volume en fonction d'une valeur entre 0 et 100."""
        try:
            self.client.setvol(volume)
        except Exception as e:
            print(f"Erreur de réglage du volume : {e}")

    def get_status(self):
        """Récupère le statut actuel de MPD."""
        try:
            return self.client.status()
        except Exception as e:
            print(f"Erreur de récupération du statut : {e}")
            return {}

    def get_elapsed(self):
        status = self.client.status()
        elapsed = float(status.get("elapsed", 0))
        return elapsed

    def get_progress(self):
        """
        Récupère la progression actuelle du morceau en cours de lecture.

        Returns:
            float: Valeur de la progression entre 0 et 1, représentant le pourcentage de lecture du morceau.
        """
        try:
            status = self.client.status()
            elapsed = float(status.get("elapsed", 0))  # Temps écoulé en secondes
            duration = float(status.get("duration", status["time"].split(":")[1]))  # Durée totale en secondes

            # Calcul de la progression en fraction (0 à 1)
            progress = elapsed / duration if duration > 0 else 0
            return progress
        except Exception as e:
            print(f"Erreur lors de la récupération de la progression : {e}")
            return 0.0

    def get_current_song(self):
        """Récupère les informations du morceau en cours de lecture."""
        try:
            song_info = self.client.currentsong()  # Utilise la commande currentsong de MPD
            # print(song_info)
            title = song_info.get("title", "Inconnu")
            artist = song_info.get("artist", "Inconnu")
            album = song_info.get("album", "Inconnu")
            return song_info
        except Exception as e:
            print(f"Erreur lors de la récupération du morceau actuel : {e}")
            return {"title": "Inconnu", "artist": "Inconnu", "album": "Inconnu"}

    def get_current_playlist(self):
        """Récupère la playlist active actuelle depuis MPD."""
        try:


            # Récupère la playlist active
            playlist = self.client.playlistinfo()
            # Structure la playlist en une liste de dictionnaires
            formatted_playlist = []
            for song in playlist:
                formatted_playlist.append({
                    'track': song.get('track', ''),
                    'title': song.get('title', 'Titre inconnu'),
                    'artist': song.get('artist', 'Artiste inconnu'),
                    'album': song.get('album', 'album inconnu'),
                    'time': song.get('time', 'time inconnu'),
                    'pos': song.get('pos', 'pos inconnu'),
                    'id': song.get('id', 'id inconnu')
                })
            print("playlist active : ",formatted_playlist)
            return formatted_playlist

        except Exception as e:
            print(f"Erreur lors de la récupération de la playlist : {e}")
            return []

    def list_info(self, path=""):
        """Liste les dossiers et fichiers audio dans le chemin spécifié."""
        try:
            return self.client.lsinfo(path)
        except Exception as e:
            print(f"Erreur lors de la récupération des informations de {path}: {e}")
            return []

    def add_to_playlist(self, path):
        """Ajoute un fichier ou un dossier à la playlist active."""
        try:
            self.client.add(path)
        except Exception as e:
            print(f"Erreur lors de l'ajout à la playlist : {e}")

    def play_song_at(self, position):
        """Joue la chanson à une position donnée dans la playlist."""
        try:
            self.client.play(position)
        except Exception as e:
            print(f"Erreur lors de la lecture de la chanson à la position {position}: {e}")

    def load_playlist(self, playlist_name):
        """Charge une playlist MPD."""
        try:
            self.client.load(playlist_name)
        except Exception as e:
            print(f"Erreur lors du chargement de la playlist {playlist_name}: {e}")


