import os
import multiprocessing
import numpy as np
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QPainter, QColor, QPen
# from networkx import config
from pydub import AudioSegment
from app.utils.config_loader import config_instance
from app.mpd.music_state_manager import MusicStateManager

timer = QTimer

def generate_waveform_process(audio_file, num_bars, queue):
    """Fonction de processus pour générer la forme d'onde avec scipy et numpy, avec gestion des NaN."""
    try:
        # Charger le fichier audio avec pydub pour supporter plusieurs formats
        audio = AudioSegment.from_file(audio_file)

        # Convertir en mono si nécessaire
        if audio.channels > 1:
            audio = audio.set_channels(1)

        # Obtenir les données audio sous forme d'onde
        y = np.array(audio.get_array_of_samples(), dtype=np.float32)

        # Calcul RMS avec gestion des NaN
        hop_length = 512
        rms = np.sqrt(np.convolve(y ** 2, np.ones(hop_length) / hop_length, mode='valid'))

        # Remplacer les NaN éventuels par 0 ou une petite valeur par défaut
        rms = np.nan_to_num(rms, nan=0.0, posinf=0.0, neginf=0.0)

        # Normaliser et redimensionner l'onde
        if np.max(rms) > 0:
            rms /= np.max(rms)  # Normaliser entre 0 et 1

        waveform_resized = np.interp(
            np.linspace(0, len(rms) - 1, num_bars),
            np.arange(len(rms)),
            rms
        )
        queue.put(waveform_resized)  # Met le résultat dans la queue
    except Exception as e:
        print(f"Erreur lors de la génération de la forme d'onde : {e}")
        queue.put([])  # Retourne une liste vide en cas d'erreur


class WaveformProgressBar(QWidget):
    def __init__(self, mpd_client, audio_file, duration, parent=None):
        super().__init__(parent)
        self.mpd_client = mpd_client
        self.audio_file = audio_file
        self.name_play = self.mpd_client.get_current_song().get("title")
        self.duration = duration
        self.progress = 0
        self.progress_0 = 0
        self.num_bars = 80
        self.waveform_resized = []  # Stockage de l'onde générée
        self.previous_position = 0
        self.progress_bar_fond = config_instance.data["colors"]["progress_bar_fond"]
        self.progress_bar = config_instance.data["colors"]["progress_bar"]

        self.music_manager = MusicStateManager(self.mpd_client)
        self.music_manager.song_changed.connect(self.start_waveform_generation)

        # Démarrer la surveillance
        self.music_manager.start_monitoring()

        if audio_file and os.path.exists(audio_file):
            # Queue pour récupérer la forme d'onde depuis le processus
            self.queue = multiprocessing.Queue()
            self.waveform_resized = np.linspace(0.01, 0.01, self.num_bars)
            # Timer pour surveiller la fin de la génération de l'onde
            self.waveform_check_timer = QTimer(self)
            self.waveform_check_timer.timeout.connect(self.check_waveform_ready)
            self.waveform_check_timer.start(100)  # Vérifie toutes les 100 ms

            # Timer pour mettre à jour la progression de la lecture
            self.progress_update_timer = QTimer(self)
            self.progress_update_timer.timeout.connect(self.update_progress)
            self.progress_update_timer.start(1000)  # Mise à jour chaque seconde

            # Démarrer le processus de génération de la forme d'onde
            self.start_waveform_generation()
        else:
            self.waveform_resized = np.linspace(0.01, 0.01, self.num_bars)


    def update_progress(self):
        """Met à jour la progression en fonction de la position actuelle du morceau."""

        progress = self.mpd_client.get_progress()  # Obtenir la progression de 0 à 1

        self.set_progress(progress)

    def set_progress(self, position):
        """Met à jour la progression en fonction de la position du morceau."""
        # self.check_name()
        if self.progress != position: # TODO: vérivier le fonctionnement en détail
            # print(position,self.progress)
            self.progress = position
            self.update()  # Redessiner la barre d'onde

    def check_waveform_ready(self):
        """Vérifie si la forme d'onde est prête dans la queue."""
        if not self.queue.empty():
            self.waveform_resized = self.queue.get()  # Récupère la forme d'onde
            self.update()  # Redessine la barre d'onde

            self.process.join()  # Attend la fin du processus

    def start_waveform_generation(self):
        """Démarre le processus pour générer la forme d'onde."""

        self.waveform_resized = np.linspace(0.01, 0.01, self.num_bars)
        self.process = multiprocessing.Process(
            target=generate_waveform_process,
            args=(self.audio_file, self.num_bars, self.queue)
        )
        self.process.start()



    def check_name(self):
        """Vérifie si le morceau a changé et regénère l'onde si nécessaire."""
        current_name = self.mpd_client.get_current_song().get("title")
        if self.name_play != current_name:
            print("Nouveau morceau détecté. Mise à jour de la forme d'onde.")
            self.name_play = current_name
            self.audio_file = self.mpd_client.get_current_file()  # Met à jour le fichier audio actuel
            self.start_waveform_generation()  # Recalcule l'onde pour le nouveau fichier

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        width = self.width()
        height = self.height() // 2

        if len(self.waveform_resized) == 0:
            painter.drawText(self.rect(), Qt.AlignCenter, "Forme d'onde non disponible")
            return

        bar_width = 2
        space_between_bars = (width - (self.num_bars * bar_width)) / (self.num_bars - 1)

        for i, value in enumerate(self.waveform_resized):
            x = int(i * (bar_width + space_between_bars))
            bar_height = int(value * height)
            color = QColor(self.progress_bar) if i / self.num_bars <= self.progress else QColor(self.progress_bar_fond)
            pen = QPen(color)
            pen.setWidth(bar_width)
            painter.setPen(pen)

            painter.drawLine(x, height, x, height - bar_height)
            painter.drawLine(x, height, x, height + bar_height)

        painter.end()


