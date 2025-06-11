# playlist_table.py
import sys
from pathlib import Path
from time import sleep

import yaml
# from networkx import config
from yaml import safe_load
from PySide6.QtWidgets import QTableView, QHeaderView, QAbstractItemView, QProxyStyle, QStyleOptionHeader, QStyle
from PySide6.QtCore import QAbstractTableModel, Qt, QModelIndex
from PySide6.QtGui import QColor, QBrush, QFont
from .config_loader import config_instance
from app.mpd.mpd_client import MPDClientWrapper
from app.mpd.music_state_manager import MusicStateManager


class CustomHeaderView(QHeaderView):
    def __init__(self, orientation, header, background_color, header_background, text_color,
                 selected_playlist, selected_text, colonne_text_colors, font, parent=None):
        super().__init__(orientation, parent)
        self.setSectionsClickable(False)  # Permet de cliquer sur les en-têtes si nécessaire

        self.background_color = background_color
        self.text_color = text_color
        self.colonne_text_colors = colonne_text_colors
        self.font = font

    def paintSection(self, painter, rect, logicalIndex):
        painter.save()

        # Utiliser la couleur de fond définie dans la configuration
        background_color = QColor(self.background_color)
        text_color = QColor(self.colonne_text_colors.get(
            self.model().headerData(logicalIndex, self.orientation(), Qt.DisplayRole).lower(),
            self.text_color  # Couleur par défaut si absente
        ))

        # Appliquer la couleur de fond
        painter.fillRect(rect, background_color)

        # Définir la police et la couleur du texte
        fontz = QFont(self.font)
        fontz.setBold(True)
        painter.setFont(fontz)
        painter.setPen(text_color)

        # Dessiner le texte de l'en-tête
        header_text = self.model().headerData(logicalIndex, self.orientation(), Qt.DisplayRole)
        if header_text == "Time":
            painter.drawText(rect, Qt.AlignCenter ,str(header_text))
        else:
            painter.drawText(rect, str(header_text))

        # Dessiner la bordure inférieure
        painter.setPen(QColor("#c9cb28"))
        painter.drawLine(rect.bottomLeft(), rect.bottomRight())

        painter.restore()


class PlaylistTableModel(QAbstractTableModel):
    def __init__(self, playlist_data, headers,  background_color, header_background,
                                        text_color,selected_playlist, selected_text,
                                        colonne_text_colors,playlist_header_line, font, playlist_current_song):
        super().__init__()
        self.headers = headers
        self.playlist_data = self.transform_data(playlist_data, headers)  # Transformation des données
        self.font = font
        self.text_color = text_color
        self.colonne_text_colors = colonne_text_colors
        self.mpd_client = MPDClientWrapper()
        print(self.mpd_client.get_status().get("song"))

        self.current_track = self._fetch_current_index()  # Position ou ID du morceau joué
        self.playlist_current_song = playlist_current_song


    def _fetch_current_index(self) -> int:
        song = self.mpd_client.get_status().get("song")
        return int(song)
        # try:
        #     return int(song)
        # except (TypeError, ValueError):
        #     return -1


    def transform_data(self, playlist_data, headers):
        """Transforme playlist_data pour ne conserver que les colonnes spécifiées dans headers."""
        transformed_data = []
        for item in playlist_data:
            transformed_item = {header.lower().replace(" ", "_"): item.get(header.lower().replace(" ", "_"), "N/A")
                                for header in headers}
            transformed_data.append(transformed_item)
        # print("transformed_data : ", transformed_data)
        return transformed_data

    def rowCount(self, parent=QModelIndex()):
        return len(self.playlist_data)

    def columnCount(self, parent=QModelIndex()):
        return len(self.headers)

    def data(self, index, role=Qt.DisplayRole):

        if not index.isValid():
            return None

        row = index.row()
        col = index.column()
        # Vérifie que l'index de colonne est dans la plage de headers
        if col >= len(self.headers):
            return None
        column_key = self.headers[col].lower().replace(" ", "_")  # Convertir l'en-tête en clé
        track = self.playlist_data[row]

        # print(f"Traitement de la cellule - Ligne: {row}, Colonne: {col}, Clé: {column_key}")



        # Texte de chaque cellule
        if role == Qt.DisplayRole:
            value = track.get(column_key, "N/A")  # "N/A" si la clé est absente
            if column_key == "time":
                if value == "Durée inconnue": #TODO: corection en amont du problème , comme enlevé la piste
                    value = 0
                # print(" value : ",value)
                seconds = int(value)
                minutes = seconds // 60  # Calculate minutes
                remaining_seconds = seconds % 60  # Calculate remaining seconds
                value =  f"{minutes}:{remaining_seconds:02d}"

            # print(f"Valeur affichée: {value}")
            return value

        # # Style personnalisé pour la piste en cours
        # if role == Qt.BackgroundRole and row == self.current_track:
        #     value = track.get(column_key, "N/A")
        #     print("row + role: ", value)
        #     return QBrush(QColor("#FFD700"))  # Jaune doré


        # Personnalisation des couleurs par colonne
        if role == Qt.ForegroundRole:
            if row == self.current_track:
                color = self.playlist_current_song
            else:
                # Obtenez le titre de la colonne en fonction de l'index de la colonne
                column_title = self.headers[col].lower()
                # Récupérez la couleur associée à ce titre dans `colonne_text_colors`
                color = self.colonne_text_colors.get(column_title, self.text_color)  # Couleur par défaut noire si absente
            return QBrush(QColor(color))

        # Fond alterné pour les lignes, mais avec une couleur de fond par défaut cohérente
        # if role == Qt.BackgroundRole:
        #     return QBrush(QColor(self.background_color)) if row % 2 == 0 else QBrush(QColor("#282828"))

        # Alignement centré
        if role == Qt.TextAlignmentRole:
            if column_key == "time":
                return Qt.AlignCenter
            elif column_key == "track":
                return Qt.AlignCenter

        # Police personnalisée
        if role == Qt.FontRole:
            fontz = QFont(self.font)
            return fontz

        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.headers[section]
        return None

    def update_current_song(self):
        new_idx = self._fetch_current_index()
        if new_idx == self.current_track:
            return
        old_idx = self.current_track
        self.current_track = new_idx
        # On émet un dataChanged sur l’ancienne et la nouvelle ligne seulement
        top_left_old = self.index(old_idx, 0)
        bot_right_old = self.index(old_idx, self.columnCount() - 1)
        top_left_new = self.index(new_idx, 0)
        bot_right_new = self.index(new_idx, self.columnCount() - 1)
        self.dataChanged.emit(top_left_old, bot_right_old, [Qt.ForegroundRole])
        self.dataChanged.emit(top_left_new, bot_right_new, [Qt.ForegroundRole])


    def update_playlist(self, new_playlist_data):
        """Mise à jour du modèle avec de nouvelles données."""
        self.beginResetModel()
        self.playlist_data = new_playlist_data
        self.endResetModel()

class StyledPlaylistTableView(QTableView):
    def __init__(self, playlist_data, header=None, column_widths=None, column_modes=None):
        super().__init__()
        print()
        playlist_mode = config_instance.data["playlist_mode"]
        header_choix = {"classic":[["Pos", "Title", "Time"], [30, 150, 60], ["fixed", "stretch", "fixed"]],
                        "mini":[["Title", "Time"],[150, 60], ["stretch", "fixed"]],
                        "kle":[["Artist", "Title", "Time"],[50, 150, 60], ["ResizeToContents", "stretch", "fixed"]],
                        "max":[["Artist", "Album", "Title", "Time"],[50,50,150,60], ["ResizeToContents", "ResizeToContents", "stretch", "fixed"]]}
        header = header_choix.get(playlist_mode)[0]

        column_widths = header_choix.get(playlist_mode)[1]

        column_modes = header_choix.get(playlist_mode)[2]

        background_color = config_instance.data["colors"]["background"]
        header_background = config_instance.data["colors"]["header_background"]
        text_color = config_instance.data["colors"]["text_primary"]
        colonne_text_colors = config_instance.data["colors"]["colonne_text_colors"]
        selected_playlist = config_instance.data["colors"]["selected_playlist"]
        selected_text = config_instance.data["colors"]["selected_text_playlist"]
        playlist_header_line = config_instance.data["colors"]["playlist_header_line"]
        playlist_current_song = config_instance.data["colors"]["playlist_current_song"]
        font = config_instance.data["font"]["family"]

        self.mpd_client = MPDClientWrapper()
        # Init le changement de music


        # Appliquer les styles avec les couleurs du fichier de configuration
        self.setStyleSheet(f"""
            /* Fond uniforme pour toutes les cellules */
            QTableView {{
                background-color: transparent;
                gridline-color: transparent;
                selection-background-color: {selected_playlist};
                selection-color: {selected_text};
                
                border: none;
            }}

            /* Fond et bordure pour les en-têtes */
            QHeaderView::section {{
                background-color: {background_color};
                color: {selected_text};
                
                border-bottom: 1px solid {playlist_header_line};
            }}
            QScrollBar:vertical {{
               border: none;
               background: transparent;
               width: 8px;
               margin: 0px 0px 0px 0px;
            }}
            QScrollBar::handle:vertical {{
               background: #cb28cb;
               min-height: 20px;
               border-radius: 4px;
            }}
            /* Masquer les lignes des cellules */
            QTableView::item {{
                border: none;
                border-right: none;
            }}
        """)
        # Initialisation du modèle de données
        self.model = PlaylistTableModel(playlist_data, header, background_color, header_background,
                                        text_color,selected_playlist, selected_text,
                                        colonne_text_colors,playlist_header_line, font,playlist_current_song)
        self.setModel(self.model)

        # Configuration des en-têtes
        # Utiliser CustomHeaderView pour l'en-tête horizontal
        self.setHorizontalHeader(CustomHeaderView(Qt.Horizontal, header, background_color, header_background, text_color,
                 selected_playlist, selected_text, colonne_text_colors, font, self))

        self.verticalHeader().setVisible(False)  # Cacher les en-têtes de lignes
        # fixer la hauteur de toutes les lignes à 32 pixels
        self.verticalHeader().setDefaultSectionSize(20)

        # Désactiver l'édition
        self.setEditTriggers(QTableView.NoEditTriggers)

        # Sélection de la ligne entière
        self.setSelectionBehavior(QTableView.SelectRows)

        # Définir les largeurs et les modes de redimensionnement des colonnes si fournis
        if column_widths:
            self.set_column_widths(column_widths)
        if column_modes:
            self.set_column_modes(column_modes)

        # self.horizontalHeader().setStyle(CustomHeaderStyle())



    def set_column_widths(self, column_widths):
        """Définit les largeurs de colonne en fonction d'un dictionnaire de largeurs."""
        for col, width in enumerate(column_widths):
            self.setColumnWidth(col, width)

    def set_column_modes(self, column_modes):
        """Définit le mode de redimensionnement de chaque colonne en fonction d'une liste de modes."""
        for col, mode in enumerate(column_modes):
            if mode == "stretch":
                self.horizontalHeader().setSectionResizeMode(col, QHeaderView.Stretch)
            elif mode == "fixed":
                self.horizontalHeader().setSectionResizeMode(col, QHeaderView.Fixed)
            elif mode == "ResizeToContents":
                self.horizontalHeader().setSectionResizeMode(col, QHeaderView.ResizeToContents)
            elif mode == "Custom":
                self.horizontalHeader().setSectionResizeMode(col, QHeaderView.Custom)
            elif mode == "Interactive":
                self.horizontalHeader().setSectionResizeMode(col, QHeaderView.Interactive)

    def update_playlist_view(self, new_playlist_data):
        """Met à jour la vue avec de nouvelles données de playlist."""
        self.model.update_playlist(new_playlist_data)

    def update_current_song_view(self):
        self.model.update_current_song()
        sid = int(self.mpd_client.get_status().get("song"))
        # Recentrer la piste courante au milieu du viewport (sans modifier la sélection)
        current_index = self.model.index(sid, 0)
        self.scrollTo(current_index, QAbstractItemView.PositionAtCenter)
