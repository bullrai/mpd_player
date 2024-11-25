# app/ui/control_bar.py
from pathlib import Path
import threading
import psutil
from PyQt5.QtCore import QRect

from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QSlider, QPushButton, QMessageBox
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtGui import QPainter, QColor, QPen , QFontDatabase, QFont
from PySide6.QtCore import Qt, QSize, QPoint ,QTimer
# from scipy.special import title
import multiprocessing
from app.mpd.mpd_client import MPDClientWrapper
from app.mpd.volume import VolumeControl
from app.utils.config_loader import config_instance
from app.ui.waveform_widget import WaveformProgressBar
from app.mpd.music_state_manager import MusicStateManager

import numpy as np
from pydub import AudioSegment
import os

import glob
# Chemin global pour les images SVG
image_path = Path("app/assets/images")




def setup_button_style(buttons, font_player, size, color, hover_color ):
    """Applique le style de base aux boutons."""

    colorz = color
    colorz_hover = hover_color
    sizep = size

    for button in buttons:
        button.setStyleSheet(f"""
            QPushButton {{
                font-size: {sizep}px;  /* Taille de la police en pixels */
                font-family: Untitled1;
                
                color: {colorz};
                border: none;
                
                width: {sizep}px;   /* Largeur fixe du bouton */
                height: {sizep}px;   /* Hauteur fixe du bouton */
            }}
            QPushButton:hover {{
                color: {colorz_hover};

            }}
        """)
        button.setFixedSize(sizep,sizep)
        # button.setFont(font_player)
        # button.setFixedSize(sizep,sizep)
        if button == "play_button":
            print("play_button")
        # button.setFixedWidth(20)



class ControlBar(QWidget):

    def __init__(self, mpd_client: MPDClientWrapper):
        super().__init__()
        self.mpd_client = mpd_client
        self.volume_control = VolumeControl(self.mpd_client)

        # Dans MainWindow ou un autre composant principal
        self.music_manager = MusicStateManager(self.mpd_client)
        self.music_manager.song_changed.connect(self.update_song_title)

        # Démarrer la surveillance
        self.music_manager.start_monitoring()

        QFontDatabase.addApplicationFont("app/assets/images/Untitled1.ttf")

        font_player = QFont("Untitled1", 24)  # Nom de votre police
        font = config_instance.data["font"]["family"]
        button_play = config_instance.data["colors"]["player_button"]
        button_play_hover = config_instance.data["colors"]["player_button_hover"]
        song_tittle = config_instance.data["colors"]["song_tittle"]
        color_volume = config_instance.data["colors"]["volume"]

        # Récupérer le chemin complet du fichier audio en cours de lecture
        current_file = get_current_file(self)
        duration = get_current_duration(self)
        # print('duration : ',duration)
        # print(f"Chemin complet du fichier audio en cours : {current_file}")
        # Initialiser les attributs pour éviter les avertissements
        self.volume_popup = None
        self.volume_slider = None

        # Créer la disposition principale de la barre de contrôle
        main_layout = QVBoxLayout()
        # self.setFixedHeight(170)
        # main_layout.setSpacing(20)

        # Titre de la chanson actuellement en lecture
        song_layout = QHBoxLayout()

        self.song_title = QLabel("tite du son")  # TODO : améliorer
        self.song_title.setFixedSize(300, 20)
        self.song_title.setStyleSheet(f"""
                        QLabel {{
                            font-family: {font};
                            background-color: transparent;
                            color: {song_tittle};
                            border: none;
                        }}
                    """)

        song_layout.addWidget(self.song_title)
        main_layout.addLayout(song_layout)
        main_layout.addSpacing(10)
        # Layout de la barre de contrôle
        control_layout = QHBoxLayout()
        control_layout.setSpacing(10)  # Espacement entre les boutons
        # self.setFixedHeight(200)

        # Boutons de contrôle avec tailles spécifiques
        self.previous_button = QPushButton("\u0044")
        self.stop_button = QPushButton("\u0043")


        # Bouton Play plus grand
        self.play_button = QPushButton("\u0041")
        setup_button_style([self.play_button], font_player, 42, button_play, button_play_hover)

        self.pause_button = QPushButton("\u0042")
        self.next_button = QPushButton("\u0045")
        setup_button_style([self.previous_button, self.stop_button,
                            self.pause_button, self.next_button], font_player, 30, button_play, button_play_hover)




        # Connecter les boutons aux fonctions du client MPD
        # self.shuffle_button.clicked.connect(lambda: print("Mélanger"))
        self.previous_button.clicked.connect(mpd_client.previous_track)
        self.stop_button.clicked.connect(mpd_client.stop)
        self.play_button.clicked.connect(mpd_client.pause)
        self.pause_button.clicked.connect(mpd_client.pause)
        self.next_button.clicked.connect(mpd_client.next_track)
        # self.repeat_button.clicked.connect(lambda: print("Répéter"))

        # Ajouter les boutons au layout de contrôle
        # control_layout.addWidget(self.shuffle_button)
        control_layout.addWidget(self.previous_button)
        control_layout.addWidget(self.stop_button)
        control_layout.addWidget(self.play_button)  # Bouton Play plus grand
        control_layout.addWidget(self.pause_button)
        control_layout.addWidget(self.next_button)
        # control_layout.addWidget(self.repeat_button)
        # Ajouter la barre de contrôle au layout principal
        main_layout.addLayout(control_layout)
        main_layout.addSpacing(10)


        # # Initialiser la barre de progression d'onde avec le fichier audio et la durée

        # Créer et ajouter la barre de progression d'onde
        self.waveform_bar = WaveformProgressBar(mpd_client, current_file, duration=duration)
        self.waveform_bar.setFixedHeight(50)  # Hauteur ajustable pour assurer la visibilité
        main_layout.addWidget(self.waveform_bar)
        main_layout.addSpacing(5)
        # else:
        #     print("Erreur : fichier audio introuvable ou invalide.")

        # Créer la "volume_box" pour le titre de la chanson et le contrôle du volume
        self.volume_box = QHBoxLayout()

        self.playlist_button = QPushButton("\u0046")
        self.playlist_button.clicked.connect(mpd_client.next_track)
        self.shuffle_button = QPushButton("\u0048")
        self.shuffle_button.clicked.connect(mpd_client.next_track)
        self.repeat_button = QPushButton("\u0047")
        self.repeat_button.clicked.connect(mpd_client.next_track)
        setup_button_style([self.playlist_button, self.shuffle_button,
                            self.repeat_button], font_player, 30, button_play, button_play_hover)
        self.volume_box.addWidget(self.playlist_button)
        self.volume_box.addWidget(self.shuffle_button)
        self.volume_box.addWidget(self.repeat_button)

        # Bouton de volume # TODO: enlever le slider et le remplacer par un scroll
        self.volume_button = QPushButton(f"Volume: {self.volume_control.get_volume()}%")
        self.volume_button.setFixedSize(100, 30)
        self.volume_button.setStyleSheet(f"""
                QPushButton {{
                    color: {color_volume};
                    font-family: {font};
                    background-color: transparent;
                    border: none;
                }}
            """)
        self.volume_button.clicked.connect(self.show_volume_popup)
        self.volume_box.addWidget(self.volume_button)

        ## Bouton resize
        # self.button_resize = QPushButton("resize")
        # self.button_resize.setFixedSize(100, 30)
        # self.button_resize.clicked.connect(self.show_volume_popup)
        # self.button_resize.setStyleSheet(f"""
        #                  QPushButton {{
        #                      background-color: transparent;
        #                      color: {text_primary};
        #
        #                  }}
        #              """)
        # self.volume_box.addWidget(self.button_resize)
        # Ajouter la box de titre et de volume au layout principal
        main_layout.addLayout(self.volume_box)
        self.setLayout(main_layout)


        self.setStyleSheet(f"background-color: transparent;")
        # Initialiser le widget popup pour le slider de volume
        self.init_volume_popup()
        self.update_song_title()

    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        if 'python' in proc.info['name']:
            print(proc.info)

    # def update_progress(self):
    #     """Met à jour la progression de la barre d'onde en fonction de la position actuelle du morceau."""
    #     if hasattr(self, 'waveform_bar') and self.waveform_bar:
    #         progress = self.mpd_client.get_progress()  # Obtenir la progression de 0 à 1
    #         self.waveform_bar.set_progress(progress)


    def init_volume_popup(self):
        """Initialise le widget popup pour le contrôle de volume."""
        self.volume_popup = QWidget(self)
        self.volume_popup.setWindowFlags(Qt.WindowType.Popup)
        self.volume_popup.setFixedSize(30, 150)

        popup_layout = QVBoxLayout()
        self.volume_slider = QSlider(Qt.Orientation.Vertical)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(self.volume_control.get_volume())
        self.volume_slider.valueChanged.connect(self.update_volume)

        popup_layout.addWidget(self.volume_slider)
        self.volume_popup.setLayout(popup_layout)

    def show_volume_popup(self):
        """Affiche le popup de contrôle de volume sous le bouton de volume."""
        # Calculer la position pour afficher le popup sous le bouton
        button_pos = self.volume_button.mapToGlobal(QPoint(70, self.volume_button.height()))
        self.volume_popup.move(button_pos)
        self.volume_popup.show()

    def update_volume(self, value):
        """Met à jour le volume et l'étiquette du bouton de volume."""
        self.volume_control.set_volume(value)
        self.volume_button.setText(f"Volume: {value}%")

    def update_song_title(self):
        """Met à jour le titre de la chanson en lecture depuis MPD."""
        song_info = self.mpd_client.get_current_song()
        if song_info:
            title = song_info.get("title", "Titre inconnu")
            artist = song_info.get("artist", "Artiste inconnu")
            self.song_title.setText(f"{title}")
            return title
        else:
            self.song_title.setText("Aucune chanson en lecture")

def get_current_file(self):
    """
    Récupère le chemin complet du fichier audio en cours de lecture en utilisant MPD.

    Returns:
        str: Chemin complet du fichier audio en cours de lecture, ou None si le fichier n'est pas trouvé.
    """

    self.MUSIC_DIRECTORY = "/home/bull/Musique"
    try:
        # Utiliser MPD pour obtenir les informations de la chanson actuelle
        current_song = self.mpd_client.get_current_song()
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

def get_current_duration(self):
    """Récupère la durée du morceau en cours de lecture via mpd_client."""
    try:
        song_info = self.mpd_client.get_current_song()
        duration = song_info.get("duration")

        if duration:
            return float(duration)  # Convertir la durée en secondes
    except Exception as e:
        print(f"Erreur lors de la récupération de la durée : {e}")
    return None