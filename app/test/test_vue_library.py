# app/ui/browser_tab.py

from PySide6.QtWidgets import QTreeView, QVBoxLayout, QWidget
from PySide6.QtCore import QAbstractItemModel, QModelIndex, Qt


class FileNode:
    """Représente un nœud dans l'arborescence (fichier ou dossier)."""

    def __init__(self, name, path, is_directory, parent=None):
        self.name = name  # Nom affiché dans la vue
        self.path = path  # Chemin relatif pour MPD
        self.is_directory = is_directory  # True si c'est un dossier
        self.parent = parent  # Parent du nœud
        self.children = []  # Liste des enfants
        self.loaded = False  # Indique si les enfants ont été chargés

    def add_child(self, child):
        self.children.append(child)

    def child_count(self):
        return len(self.children)

    def child(self, row):
        return self.children[row] if 0 <= row < self.child_count() else None

    def row(self):
        if self.parent:
            return self.parent.children.index(self)
        return 0


class FileSystemModel(QAbstractItemModel):
    """Modèle hiérarchique pour QTreeView."""

    def __init__(self, root_path, mpd_client):
        super().__init__()
        self.mpd_client = mpd_client
        self.root_node = FileNode("Bibliothèque musicale", root_path, True)  # Racine de l'arbre

        # Charger les éléments racine
        self.load_children(self.root_node)

    def rowCount(self, parent):
        node = parent.internalPointer() if parent.isValid() else self.root_node
        return node.child_count()

    def columnCount(self, parent):
        return 1  # Une seule colonne (nom des fichiers/dossiers)

    def data(self, index, role):
        if not index.isValid():
            return None
        node = index.internalPointer()
        if role == Qt.DisplayRole:
            return node.name
        return None

    def index(self, row, column, parent):
        if not self.hasIndex(row, column, parent):
            return QModelIndex()
        parent_node = parent.internalPointer() if parent.isValid() else self.root_node
        child_node = parent_node.child(row)
        return self.createIndex(row, column, child_node) if child_node else QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return QModelIndex()
        node = index.internalPointer()
        parent_node = node.parent if node else None
        if parent_node == self.root_node or not parent_node:
            return QModelIndex()
        return self.createIndex(parent_node.row(), 0, parent_node)

    def hasChildren(self, parent):
        node = parent.internalPointer() if parent.isValid() else self.root_node
        return node.is_directory

    def load_children(self, parent_node):
        """Charge les enfants d'un nœud."""
        if not parent_node.is_directory or parent_node.loaded:
            return
        try:
            # Utiliser uniquement le chemin relatif pour MPD
            items = self.mpd_client.client.lsinfo(parent_node.path)
            for item in items:
                if 'directory' in item:
                    child_node = FileNode(
                        name=item['directory'].split("/")[-1],
                        path=item['directory'],  # Chemin relatif
                        is_directory=True,
                        parent=parent_node
                    )
                    parent_node.add_child(child_node)
                elif 'file' in item and self.is_audio_file(item['file']):
                    child_node = FileNode(
                        name=item['file'].split("/")[-1],
                        path=item['file'],  # Chemin relatif
                        is_directory=False,
                        parent=parent_node
                    )
                    parent_node.add_child(child_node)
            parent_node.loaded = True
        except Exception as e:
            print(f"Erreur lors du chargement des enfants : {e}")

    def canFetchMore(self, parent):
        """Indique si le nœud peut charger plus de données."""
        node = parent.internalPointer() if parent.isValid() else self.root_node
        return node.is_directory and not node.loaded

    def fetchMore(self, parent):
        """Charge plus de données pour un nœud."""
        node = parent.internalPointer() if parent.isValid() else self.root_node
        if node.is_directory and not node.loaded:
            self.beginInsertRows(parent, 0, len(node.children) - 1)
            self.load_children(node)
            self.endInsertRows()

    def is_audio_file(self, filename):
        """Vérifie si le fichier a une extension audio valide."""
        audio_extensions = {".mp3", ".flac", ".wav", ".aac", ".ogg"}
        return any(filename.lower().endswith(ext) for ext in audio_extensions)


class BrowserTab(QWidget):
    """Interface utilisateur pour afficher la bibliothèque."""

    def __init__(self, mpd_client):
        super().__init__()
        self.mpd_client = mpd_client
        self.root_path = ""  # Chemin racine relatif pour MPD (vide pour la racine)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Initialisation de la vue
        self.tree_view = QTreeView()
        self.model = FileSystemModel(self.root_path, self.mpd_client)
        self.tree_view.setModel(self.model)

        # Ajouter la vue au layout
        layout.addWidget(self.tree_view)
        self.setLayout(layout)

    # def is_audio_file(self, filename):
    #     """Vérifie si le fichier a une extension audio valide."""
    #     audio_extensions = {".mp3", ".flac", ".wav", ".aac", ".ogg"}
    #     return any(filename.lower().endswith(ext) for ext in audio_extensions)

    def open_directory_or_file(self, item):
        """Ouvre un dossier ou traite un fichier lorsqu'un élément est cliqué."""
        item_text = item.text()

        if item_text.startswith("[Dossier]"):
            # Si c'est un dossier, on charge son contenu
            directory_name = item_text[10:]  # Retire "[Dossier] " pour obtenir le nom réel
            new_path = f"{self.current_path}/{directory_name}" if self.current_path else directory_name
            self.load_library(new_path)
        else:
            # Ici, on peut gérer l'action pour un fichier audio si nécessaire
            print(f"Fichier audio sélectionné : {item_text}")

    def go_to_parent_directory(self):
        """Remonte d'un niveau dans le répertoire actuel."""
        if "/" in self.current_path:
            # Remonte d'un niveau en enlevant la dernière partie du chemin
            parent_path = "/".join(self.current_path.split("/")[:-1])
        else:
            # Si on est déjà à la racine, on définit le chemin vide
            parent_path = ""

        self.load_library(parent_path)

    def add_selected_to_playlist(self):
        """Ajoute l'élément sélectionné à la playlist active de MPD."""
        current_item = self.library_list.currentItem()
        if current_item:
            item_text = current_item.text()
            if item_text.startswith("[Dossier]"):
                directory_name = item_text[10:]  # Enlève "[Dossier] " pour obtenir le nom réel
                full_path = f"{self.current_path}/{directory_name}" if self.current_path else directory_name
                self.mpd_client.add_to_playlist_active(full_path)  # Ajoute le dossier complet à la playlist
                print(f"Dossier ajouté à la playlist : {full_path}")
            else:
                full_path = f"{self.current_path}/{item_text}" if self.current_path else item_text
                self.mpd_client.client.add(full_path)  # Ajoute le fichier audio à la playlist
                print(f"Fichier ajouté à la playlist : {full_path}")
            # Actualiser PlaylistAcTab après l'ajout
            if self.playlist_ac_tab:
                self.playlist_ac_tab.update_playlist()


# app/ui/browser_tab.py

from PySide6.QtWidgets import QWidget, QVBoxLayout, QTreeView
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut, QStandardItemModel, QStandardItem
from app.mpd.mpd_client import MPDClientWrapper
from app.utils.config_loader import config_instance


class BrowserTab(QWidget):
    def __init__(self, mpd_client: MPDClientWrapper, playlist_ac_tab):
        super().__init__()
        self.mpd_client = mpd_client
        self.playlist_ac_tab = playlist_ac_tab  # Référence à PlaylistAcTab
        self.current_path = ""  # Commence dans le dossier racine
        self.music_directory = "/home/user/Music"

        self.library_text = config_instance.data["colors"]["library_text"]
        self.library_selected = config_instance.data["colors"]["library_selected"]
        self.library_text_selected = config_instance.data["colors"]["library_text_selected"]
        self.font = config_instance.data["font"]["family"]

        self.setup_ui()
        # self.load_library()  # Charger la bibliothèque à la racine au démarrage
        self.setup_shortcuts()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Initialisation de la vue et du modèle
        self.tree_view = QTreeView()
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(["Bibliothèque musicale"])
        self.tree_view.setModel(self.model)
        self.tree_view.expanded.connect(self.on_item_expanded)  # Événement d'expansion

        # Ajouter la vue au layout
        layout.addWidget(self.tree_view)
        self.setLayout(layout)

        # Charger les dossiers racine
        self.load_library()

        # Appliquer les styles
        self.tree_view.setStyleSheet("""
                    /*QTreeView::branch:closed:has-children {
                        image: url('folder_closed.png');
                        margin: 0px;
                    }
                    QTreeView::branch:open:has-children {
                        image: url('folder_open.png');
                        margin: 0px;
                    }*/

                    QHeaderView::section {
                        background-color: #1E1E1E; /* Couleur de fond */
                        color: #1E1E1E;           /* Couleur du texte */
                        border: 1px ; /* Bordure autour des en-têtes */
                        padding: 0px;             /* Espacement interne */
                        height: 1px;
                    }

                    QScrollBar:vertical {
                       border: none;
                       background: transparent;
                       width: 8px;
                       margin: 0px 0px 0px 0px;
                    }
                    QScrollBar::handle:vertical {
                       background: #cb28cb;
                       min-height: 20px;
                       border-radius: 4px;
                    }
                    QTreeView {
                       font-family: "Arial";
                       font-size: 14px;
                       color: #ffffff;
                       background-color: transparent;
                       alternate-background-color: transparent;
                    }
               """)

    def load_library(self, path=""):
        """Charge les éléments à la racine."""
        try:
            items = self.mpd_client.client.lsinfo(path)
            for item in items:
                if 'directory' in item:
                    dir_item = QStandardItem(item['directory'].split("/")[-1])
                    dir_item.setData(item['directory'], Qt.UserRole)
                    dir_item.setEditable(False)
                    dir_item.appendRow(QStandardItem("Chargement..."))  # Indicateur temporaire
                    self.model.appendRow(dir_item)
                elif 'file' in item and self.is_audio_file(item['file']):
                    file_item = QStandardItem(item['file'].split("/")[-1])
                    file_item.setData(item['file'], Qt.UserRole)
                    file_item.setEditable(False)
                    self.model.appendRow(file_item)
        except Exception as e:
            print(f"Erreur lors du chargement de la bibliothèque : {e}")

    def on_item_expanded(self, index):
        """Gère l'expansion d'un dossier."""
        item = self.model.itemFromIndex(index)
        if item.rowCount() == 1 and item.child(0).text() == "Chargement...":
            # Supprime l'indicateur temporaire
            item.removeRow(0)
            # Charge les sous-dossiers et fichiers
            self.load_subdirectory(item, item.data(Qt.UserRole))

    def load_subdirectory(self, parent_item, path):
        """Charge les sous-dossiers d'un dossier spécifique."""
        try:
            items = self.mpd_client.client.lsinfo(path)
            for item in items:
                if 'directory' in item:
                    dir_item = QStandardItem(item['directory'].split("/")[-1])
                    dir_item.setData(item['directory'], Qt.UserRole)
                    dir_item.setEditable(False)
                    dir_item.appendRow(QStandardItem("Chargement..."))  # Indicateur temporaire
                    parent_item.appendRow(dir_item)
                elif 'file' in item and self.is_audio_file(item['file']):
                    file_item = QStandardItem(item['file'].split("/")[-1])
                    file_item.setData(item['file'], Qt.UserRole)
                    file_item.setEditable(False)
                    parent_item.appendRow(file_item)
        except Exception as e:
            print(f"Erreur lors du chargement des sous-dossiers : {e}")

    def is_audio_file(self, filename):
        """Vérifie si le fichier est un fichier audio."""
        audio_extensions = {".mp3", ".flac", ".wav", ".aac", ".ogg"}
        return any(filename.lower().endswith(ext) for ext in audio_extensions)

    def setup_shortcuts(self):
        """Configure les raccourcis pour la navigation clavier et l'ajout à la playlist."""
        # Raccourci pour ajouter à la playlist avec la touche '0'
        add_to_playlist_shortcut = QShortcut(QKeySequence("0"), self)
        add_to_playlist_shortcut.activated.connect(self.add_selected_to_playlist)

    #     # Navigation dans la liste avec les flèches et les touches Entrée/Retour Arrière
    #     self.setFocusPolicy(Qt.StrongFocus)
    #
    # def keyPressEvent(self, event):
    #     """Gère les événements de touches pour la navigation dans la liste."""
    #     if event.key() == Qt.Key_Down:
    #         # Flèche Bas : se déplacer vers le bas dans la liste
    #         next_row = (self.library_list.currentRow() + 1) % self.library_list.count()
    #         self.library_list.setCurrentRow(next_row)
    #     elif event.key() == Qt.Key_Up:
    #         # Flèche Haut : se déplacer vers le haut dans la liste
    #         previous_row = (self.library_list.currentRow() - 1) % self.library_list.count()
    #         self.library_list.setCurrentRow(previous_row)
    #     elif event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
    #         # Entrée : ouvrir le dossier ou sélectionner le fichier
    #         current_item = self.library_list.currentItem()
    #         if current_item:
    #             self.open_directory_or_file(current_item)
    #     elif event.key() == Qt.Key_Backspace:
    #         # Retour Arrière : revenir au dossier parent
    #         self.go_to_parent_directory()
    #     else:
    #         # Appel de la méthode parente pour les autres touches
    #         super().keyPressEvent(event)

    # def is_audio_file(self, filename):
    #     """Vérifie si le fichier a une extension audio valide."""
    #     audio_extensions = {".mp3", ".flac", ".wav", ".aac", ".ogg"}
    #     return any(filename.lower().endswith(ext) for ext in audio_extensions)

    def add_selected_to_playlist(self):
        """Ajoute l'élément sélectionné à la playlist active de MPD."""
        current_item = self.library_list.currentItem()
        if current_item:
            item_text = current_item.text()
            if item_text.startswith("[Dossier]"):
                directory_name = item_text[10:]  # Enlève "[Dossier] " pour obtenir le nom réel
                full_path = f"{self.current_path}/{directory_name}" if self.current_path else directory_name
                self.mpd_client.add_to_playlist_active(full_path)  # Ajoute le dossier complet à la playlist
                print(f"Dossier ajouté à la playlist : {full_path}")
            else:
                full_path = f"{self.current_path}/{item_text}" if self.current_path else item_text
                self.mpd_client.client.add(full_path)  # Ajoute le fichier audio à la playlist
                print(f"Fichier ajouté à la playlist : {full_path}")
            # Actualiser PlaylistAcTab après l'ajout
            if self.playlist_ac_tab:
                self.playlist_ac_tab.update_playlist()
