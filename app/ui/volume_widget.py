# app/ui/volume_widget.py

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtGui import QPainter, QMouseEvent, QWheelEvent, QColor
from PySide6.QtCore import Qt, QRectF
from app.mpd.mpd_client import MPDClientWrapper
from app.mpd.volume import VolumeControl


class VolumeWidget(QWidget):
    def __init__(self, mpd_client:MPDClientWrapper, parent=None):
        super().__init__(parent)
        self.mpd_client = mpd_client  # Client MPD pour gérer le volume
        self.volume_control = VolumeControl(self.mpd_client)
        self.volume = self.volume_control.get_volume() # Volume initial
        self.bar_count = 20  # Nombre de barres pour représenter le volume
        self.is_dragging = False  # Indique si la souris est maintenue enfoncée


        # self.setFixedHeight(30)
        self.setFixedWidth(100)

    def set_volume(self, volume):
        """Définit le volume et met à jour l'affichage."""
        self.volume = max(0, min(100, volume))  # Limiter entre 0 et 100
        if self.mpd_client:
            self.volume_control.set_volume(self.volume)  # Envoyer à MPD
        self.update()  # Redessiner le widget

    def paintEvent(self, event):
        """Dessine le widget."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Taille et position des barres
        bar_width = 5 # self.width() / self.bar_count
        spacing = 2
        base_height =  1#self.height() - 20  # Réserver de la place pour le texte
        active_bars = int(self.volume / 100 * self.bar_count)

        # Dessiner chaque barre
        for i in range(self.bar_count):
            x = i * bar_width
            y = 22
            height = base_height *i
            rect = QRectF(x + spacing, y, bar_width - spacing, -height)
            if i < active_bars:
                painter.setBrush(QColor("#cb28cb"))  # Barres actives
            else:
                painter.setBrush(QColor("#888888"))  # Barres inactives
            painter.setPen(Qt.NoPen)
            painter.drawRect(rect)



    def mousePressEvent(self, event: QMouseEvent):
        """Gère le clic de la souris pour définir le volume."""
        if event.button() == Qt.LeftButton:
            self.is_dragging = True  # Activer le suivi du clic
            self.update_volume_from_mouse(event.x())

    def mouseMoveEvent(self, event: QMouseEvent):
        """Gère le déplacement de la souris tout en maintenant le clic."""
        if self.is_dragging:  # Si on est en train de cliquer
            self.update_volume_from_mouse(event.x())

    def mouseReleaseEvent(self, event: QMouseEvent):
        """Arrête le suivi lorsque le clic est relâché."""
        if event.button() == Qt.LeftButton:
            self.is_dragging = False  # Désactiver le suivi du clic

    def update_volume_from_mouse(self, x):
        """Met à jour le volume en fonction de la position de la souris."""
        bar_width = self.width() / self.bar_count
        clicked_bar = int(x / bar_width)
        new_volume = int((clicked_bar + 1) / self.bar_count * 100)
        self.set_volume(new_volume)

    def wheelEvent(self, event: QWheelEvent):
        """Gère la molette de la souris pour ajuster le volume."""
        delta = 5 if event.angleDelta().y() > 0 else -5
        self.set_volume(self.volume + delta)

    # def wheelEvent(self, event: QWheelEvent):
    #     """Gère la molette de la souris pour ajuster le volume."""
    #     print("scroll")
    #     delta = 5 if event.angleDelta().y() > 0 else -5
    #     self.set_volume(self.volume + delta)