import os
import multiprocessing
from time import sleep

import numpy as np
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import QTimer, Qt, QThread, Signal, Slot
from PySide6.QtGui import QPainter, QColor, QPen, QMouseEvent
# from networkx import config
from pydub import AudioSegment
from app.mpd.mpd_client import MPDClientWrapper
from app.mpd.volume import VolumeControl
from app.utils.config_loader import config_instance
from app.mpd.music_state_manager import MusicStateManager

timer = QTimer
# TODO : verifié quand il n'y as pas de music, si sa mouline dans le vent.
class WaveformWorker(QThread):
    """Worker QThread qui calcule la forme d'onde et l'émet via un signal."""
    waveformReady = Signal(object)  # émetera un array numpy (ou liste)

    def __init__(self, audio_file: str, num_bars: int, parent=None):
        super().__init__(parent)
        self.audio_file = audio_file
        self.num_bars = num_bars

    def run(self):
        try:
            audio = AudioSegment.from_file(self.audio_file)
            audio = audio.set_frame_rate(audio.frame_rate // 8)
            if audio.channels > 1:
                audio = audio.set_channels(1)

            y = np.array(audio.get_array_of_samples(), dtype=np.float32)
            hop_length = 512
            y2 = y ** 2
            cs = np.cumsum(y2, dtype=np.float32)
            rms = np.sqrt((cs[hop_length:] - cs[:-hop_length]) / hop_length)
            rms = np.nan_to_num(rms, nan=0.0, posinf=0.0, neginf=0.0)
            if rms.max() > 0:
                rms /= rms.max()

            waveform_resized = np.interp(
                np.linspace(0, len(rms) - 1, self.num_bars),
                np.arange(len(rms)),
                rms
            )
            self.waveformReady.emit(waveform_resized)
        except Exception as e:
            print(f"Erreur lors de WaveformWorker: {e}")
            self.waveformReady.emit(np.zeros(self.num_bars, dtype=np.float32))


class WaveformProgressBar(QWidget):
    def __init__(self, mpd_client:MPDClientWrapper, audio_file, parent=None):
        super().__init__(parent)

        self.is_dragging = False

        self.mpd_client = mpd_client
        self.volume = VolumeControl(self.mpd_client)
        self.audio_file = audio_file
        self.name_play = self.mpd_client.get_current_song().get("title")
        self.progress = 0
        self.progress_0 = 0
        self.num_bars = 80
        self.waveform_resized = []  # Stockage de l'onde générée
        self.previous_position = 0
        self.progress_bar_fond = config_instance.data["colors"]["progress_bar_fond"]
        self.progress_bar = config_instance.data["colors"]["progress_bar"]

        self.music_manager = MusicStateManager(self.mpd_client)
        self.music_manager.song_changed.connect(self.check_name)

        # Démarrer la surveillance
        self.music_manager.start_monitoring()

        if audio_file and os.path.exists(audio_file):
            # Initialisation de la forme
            self.waveform_resized = np.linspace(0.01, 0.01, self.num_bars)
            self.worker = None

            # Timer pour mettre à jour la progression de la lecture
            self.progress_update_timer = QTimer(self)
            self.progress_update_timer.timeout.connect(self.update_progress)
            self.progress_update_timer.start(500)  # Mise à jour chaque seconde

            # Lancer le calcul de waveform dans un QThread
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
        if self.progress != position:# TODO: vérivier le fonctionnement en détail
            print("position : ", position, "progress : ", self.progress)
            self.progress = position
            self.update()  # Redessiner la barre d'onde

    @ Slot(object)
    def on_waveform_ready(self, waveform):
        """Slot appelé quand WaveformWorker a fini de calculer."""

        self.waveform_resized = np.array(waveform, dtype=np.float32)
        self.update()

    def start_waveform_generation(self):
        # Si un worker tournait déjà, on l'arrête proprement
        if hasattr(self, 'worker') and self.worker is not None:
            if self.worker.isRunning():
                self.worker.quit()
                self.worker.wait()

        # Réinitialisation visuelle
        self.waveform_resized = np.linspace(0.01, 0.01, self.num_bars)

        # Création et lancement du QThread
        self.worker = WaveformWorker(self.audio_file, self.num_bars)
        self.worker.waveformReady.connect(self.on_waveform_ready)
        self.worker.start()

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
        duration = self.mpd_client.get_duration()
        relative_position = x / self.width()
        print("relative_position : ",relative_position)
        relative_position = max(0, min(1, relative_position))  # Limiter entre 0 et 1.
        print("relative_position111 : ", relative_position)
        print("duration : ", duration)

        new_position = float(relative_position * duration)  # Position en secondes
        print("new_position : ", relative_position)

        # # Mettre à jour la progression
        # self.set_progress(relative_position)

        # Envoyer la position à MPD
        try:

            self.volume.fade_in_set_progress()
            # Appliquer seekcur directement
            self.mpd_client.set_progress(new_position)
            self.volume.fade_out_set_progress()

            print(f"Position de lecture mise à jour : {new_position}s")
        except Exception as e:
            print(f"Erreur lors de la mise à jour de la position de lecture : {e}")

