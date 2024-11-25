from PySide6.QtCore import QObject, Signal, QTimer

class MusicStateManager(QObject):
    song_changed = Signal(dict)  # Signal émis quand la chanson change, transmet un dictionnaire avec les infos de la chanson

    def __init__(self, mpd_client, poll_interval=1000):
        """
        Initialise le gestionnaire d'état musical.
        :param mpd_client: Instance de MPDClientWrapper.
        :param poll_interval: Intervalle (en ms) pour vérifier les changements de musique.
        """
        super().__init__()
        self.mpd_client = mpd_client
        self.current_song = {}
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_song_state)
        self.poll_interval = poll_interval

    def start_monitoring(self):
        """Démarre le timer pour surveiller les changements de musique."""
        self.timer.start(self.poll_interval)

    def stop_monitoring(self):
        """Arrête le timer."""
        self.timer.stop()

    def update_song_state(self):
        """Vérifie si la chanson a changé et émet un signal si c'est le cas."""
        try:
            new_song = self.mpd_client.get_current_song()  # Récupère les infos de la chanson actuelle
            if new_song.get("title") != self.current_song.get("title"):
                self.current_song = new_song
                self.song_changed.emit(self.current_song)  # Émet le signal avec les infos de la chanson
        except Exception as e:
            print(f"Erreur lors de la mise à jour de l'état musical : {e}")
