import os
import multiprocessing
from time import sleep

import numpy as np
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QPainter, QColor, QPen, QMouseEvent
# from networkx import config
from pydub import AudioSegment
from app.mpd.mpd_client import MPDClientWrapper
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
    def __init__(self, mpd_client:MPDClientWrapper, audio_file, duration, parent=None):
        super().__init__(parent)
        self.mpd_client = mpd_client
        self.audio_file = audio_file
        # self.queue = multiprocessing.Queue()
        self.name_play = None if not self.audio_file else self.mpd_client.get_current_song().get("title")
        dure = self.mpd_client.get_duration()
        self.duration = dure if dure else 0

        print("duration : ",self.duration)
        self.progress = 0
        self.progress_0 = 0
        self.num_bars = 80
        self.waveform_resized = []  # Stockage de l'onde générée
        self.previous_position = 0
        self.progress_bar_fond = config_instance.data["colors"]["progress_bar_fond"]
        self.progress_bar = config_instance.data["colors"]["progress_bar"]

        self.music_manager = MusicStateManager(self.mpd_client)
        self.music_manager.song_changed.connect(self.check_name)

        self.is_dragging = False  # Indique si la souris est maintenue enfoncée

        # Toujours initialiser la queue et les timers
        self.queue = None  # Queue sera créée dynamiquement lorsque nécessaire
        self.waveform_check_timer = QTimer(self)
        self.waveform_check_timer.timeout.connect(self.check_waveform_ready)
        self.waveform_check_timer.start(100)  # Vérification toutes les 100 ms

        self.progress_update_timer = QTimer(self)
        self.progress_update_timer.timeout.connect(self.update_progress)
        self.progress_update_timer.start(1000)  # Mise à jour chaque seconde

        # Gestion des changements de chanson
        self.music_manager = MusicStateManager(self.mpd_client)
        self.music_manager.song_changed.connect(self.check_name)
        self.music_manager.start_monitoring()

        # Si un fichier audio est valide, démarrez la génération
        if audio_file and os.path.exists(audio_file):
            self.start_waveform_generation()
        else:
            self.waveform_resized = np.linspace(0.01, 0.01, self.num_bars)


    def update_progress(self):
        """Met à jour la progression en fonction de la position actuelle du morceau."""

        progress = self.mpd_client.get_progress()  # Obtenir la progression de 0 à 1.

        self.set_progress(progress)

    def set_progress(self, position):
        """Met à jour la progression en fonction de la position du morceau."""
        # self.check_name()
        # print("status : ",self.mpd_client.get_status().get("state"))
        if self.progress != position: # TODO: vérifier le fonctionnement en détail
            stat = self.mpd_client.get_status().get("state")
            if stat == "play":
                # print("play")
                self.progress = position
                self.update()  # Redessiner la barre d'onde
            elif stat == 'stop':
                self.waveform_resized = np.linspace(0.0, 0.01, self.num_bars)
                # print('stop')
                self.update()

    def check_waveform_ready(self):
        """Vérifie si la forme d'onde est prête dans la queue."""
        if not self.queue:
            print("Queue non initialisée.")
            return

        if not self.queue.empty():
            self.waveform_resized = self.queue.get()
            self.update()
            self.process.join()      # Attend la fin du processus

    def start_waveform_generation(self):
        """Démarre le processus pour générer la forme d'onde."""
        if not self.audio_file or not os.path.exists(self.audio_file):
            print("Erreur : fichier audio non disponible.")
            self.waveform_resized = np.linspace(0.01, 0.01, self.num_bars)  # État neutre
            self.update()
            return

        # Arrêter tout processus en cours
        if hasattr(self, 'process') and self.process.is_alive():
            self.process.terminate()
            self.process.join()

        # Créer une nouvelle queue
        self.queue = multiprocessing.Queue()

        # Démarrer le processus pour générer la forme d'onde
        self.process = multiprocessing.Process(
            target=generate_waveform_process,
            args=(self.audio_file, self.num_bars, self.queue)
        )
        self.process.start()

    def check_name(self):
        """Vérifie si le morceau a changé et régénère l'onde si nécessaire."""
        current_song = self.mpd_client.get_current_song()
        current_name = current_song.get("title") if current_song else None

        if not current_name:
            print("Aucune chanson détectée.")
            self.audio_file = None
            self.waveform_resized = np.linspace(0.01, 0.01, self.num_bars)  # État par défaut
            self.update()
            return

        if self.name_play != current_name:
            print(f"Nouveau morceau détecté : {current_name}. Mise à jour de la forme d'onde.")
            self.name_play = current_name
            self.audio_file = self.mpd_client.get_current_file()

            # Redémarrer le processus de génération d'onde
            self.start_waveform_generation()

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


    # def mousePressEvent(self, event: QMouseEvent):
    #     """Gère le clic de la souris pour définir la position de lecture."""
    #     if event.button() == Qt.LeftButton:
    #         self.is_dragging = True  # Activer le suivi du clic
    #         self.update_position_from_mouse(event.x())
    #
    # def mouseMoveEvent(self, event: QMouseEvent):
    #     """Gère le déplacement de la souris tout en maintenant le clic."""
    #     if self.is_dragging:  # Si on est en train de cliquer
    #         self.update_position_from_mouse(event.x())

    def mouseReleaseEvent(self, event: QMouseEvent):
        """Arrête le suivi lorsque le clic est relâché."""
        if event.button() == Qt.LeftButton:
            self.update_position_from_mouse(event.x())
            self.is_dragging = False  # Désactiver le suivi du clic

    def update_position_from_mouse(self, x):
        """Met à jour la position de lecture en fonction de la position de la souris."""
        # Calculer la progression en fonction de la position de la souris
        relative_position = x / self.width()
        print("relative_position : ",self.duration)
        relative_position = max(0, min(1, relative_position))  # Limiter entre 0 et 1.
        print("relative_position111 : ", relative_position)
        new_position = float(relative_position * self.duration)  # Position en secondes
        print("new_position : ", relative_position)

        # Mettre à jour la progression
        self.set_progress(relative_position)

        # Envoyer la position à MPD
        try:
            self.mpd_client.pause()
            sleep(0.2) # TODO: trouver une autre solution
            self.mpd_client.set_progress(new_position)
            self.mpd_client.pause()
            print(f"Position de lecture mise à jour : {new_position}s")
        except Exception as e:
            print(f"Erreur lors de la mise à jour de la position de lecture : {e}")

