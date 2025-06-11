# app/mpd/mpd_client.py
import os
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

    def shuffle(self):
        """Passe en mode aléatoire."""
        try:
            self.client.shuffle()
        except Exception as e :
            print(f"Erreur en Shuffle : {e}")

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

    def get_duration(self):
        try:
            status = self.client.status()
            print("status : ",status)
            duration = int(status.get("time", "0:0").split(":")[1])  # Durée totale en secondes
            return duration
        except Exception as e:
            print(f"Erreur lors de la récupération de la durée : {e}")

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

    def set_progress(self, new_position):
        # Envoyer la position à MPD

        print("new_position : ",new_position)
        try:
            self.client.seekcur(new_position)
            print(f"Position de lecture mise à jour : {new_position}s")
        except Exception as e:
            print(f"Erreur lors de la mise à jour de la position de lecture : {e}")

    def get_current_song(self):
        """
        Récupère les informations de la chanson actuelle, avec gestion des titres vides.
        """
        try:
            song_info = self.client.currentsong()  # Utilise la commande currentsong de MPD
            title = resolve_song_title(song_info)  # Résout le titre final
            artist = song_info.get("artist", "Inconnu")
            album = song_info.get("album", "Inconnu")
            file_path = song_info.get("file", "")

            return {
                "title": title,
                "artist": artist,
                "album": album,
                "file": file_path
            }
        except Exception as e:
            print(f"Erreur lors de la récupération du morceau actuel : {e}")
            return {
                "title": "Inconnu",
                "artist": "Inconnu",
                "album": "Inconnu",
                "file": ""
            }

    def get_current_file(self):
        """
        Récupère le chemin complet du fichier audio en cours de lecture en utilisant MPD.

        Returns:
            str: Chemin complet du fichier audio en cours de lecture, ou None si le fichier n'est pas trouvé.
        """

        self.MUSIC_DIRECTORY = "/home/bull/Musique"
        try:
            # Utiliser MPD pour obtenir les informations de la chanson actuelle
            current_song = self.get_current_song()
            print("Informations de la chanson en cours :", current_song)

            # Récupérer le chemin relatif du fichier audio
            file_path = current_song.get("file")
            if file_path:
                # Construire le chemin complet en combinant avec le répertoire de musique
                full_path = os.path.join(self.MUSIC_DIRECTORY, file_path)
                print("Chemin complet du fichier audio :", full_path)
                return full_path
            else:
                print("Erreur : Chemin du fichier introuvable dans les informations de la chanson.")
                return None
        except Exception as e:
            print(f"Erreur lors de la récupération du fichier audio : {e}")
            return None

    def get_current_playlist(self):
        """
        Récupère la playlist active actuelle depuis MPD, avec gestion des titres vides.
        """
        try:
            playlist = self.client.playlistinfo()  # Récupère la playlist active
            print("playlist : ", playlist)
            formatted_playlist = []
            for song in playlist:
                title = resolve_song_title(song)  # Résout le titre pour chaque chanson
                formatted_playlist.append({
                    'track': song.get('track', ''),
                    'title': title,
                    'artist': song.get('artist', 'Artiste inconnu'),
                    'album': song.get('album', 'Album inconnu'),
                    'time': song.get('time', 'Durée inconnue'),
                    'pos': song.get('pos', 'Position inconnue'),
                    'id': song.get('id', 'ID inconnu')
                })
            print("formatted_playlist : ", formatted_playlist)
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

    def add_to_playlist_active(self, path):
        """Ajoute un fichier ou un dossier à la playlist active."""
        try:
            self.client.add(path)
        except Exception as e:
            print(f"Erreur lors de l'ajout à la playlist active : {e}")

    def clear_to_playlist_active(self):
        """Vide la playlist active """
        try:
            self.client.clear()
        except Exception as e:
            print(f"Erreur lors de la suppréssion de la playlist active : {e}")

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


def resolve_song_title(song_info):
    """
    Remplace les titres vides par le nom du fichier audio.
    :param song_info: Dictionnaire contenant les métadonnées de la chanson.
    :return: Le titre final (réel ou basé sur le nom du fichier).
    """
    # Récupérer les informations nécessaires
    title = song_info.get("title", "").strip()  # Peut être vide ou absent
    file_path = song_info.get("file", "")  # Chemin complet du fichier

    # Si le titre est vide, utiliser le nom du fichier
    if not title and file_path:
        title = os.path.basename(file_path)  # Extraire uniquement le nom du fichier
        title = os.path.splitext(title)[0]  # Retirer l'extension du fichier

    return title
