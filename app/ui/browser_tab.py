# app/ui/browser_tab.py
from PySide6.QtWidgets import QTreeView, QVBoxLayout, QWidget, QMenu
from PySide6.QtCore import QAbstractItemModel, QModelIndex, Qt
from PySide6.QtGui import QKeySequence, QShortcut
from app.mpd.mpd_client import MPDClientWrapper


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

    def __init__(self, mpd_client:MPDClientWrapper, playlist_ac_tab):
        super().__init__()
        self.mpd_client = mpd_client
        self.root_path = ""  # Chemin racine relatif pour MPD (vide pour la racine)
        self.playlist_ac_tab = playlist_ac_tab  # Référence à PlaylistAcTab
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Initialisation de la vue
        self.tree_view = QTreeView()
        self.model = FileSystemModel(self.root_path, self.mpd_client)
        self.tree_view.setModel(self.model)
        self.tree_view.setUniformRowHeights(True)
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
                            QTreeView::item {
                                padding: 4px;  /* Ajoute un espacement vertical et horizontal */
                            }
                            QTreeView {
                               
                               /*font-size: 14px;*/
                               color: #ffffff;
                               background-color: transparent;
                               alternate-background-color: transparent;
                            }
                       """)

        self.tree_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree_view.customContextMenuRequested.connect(self.open_context_menu)

        # Ajouter la vue au layout
        layout.addWidget(self.tree_view)
        self.setLayout(layout)


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

    def open_context_menu(self, position):
        """Affiche le menu contextuel."""
        # Créer le menu
        menu = QMenu(self)

        # Ajouter les options au menu
        add_action = menu.addAction("Add to playlist AC")
        replace_action = menu.addAction("Replace playlist AC")

        # Connecter les actions aux fonctions
        add_action.triggered.connect(self.add_selected_to_playlist)
        replace_action.triggered.connect(self.replace_playlist_with_selected)

        # Afficher le menu à la position du clic
        menu.exec(self.tree_view.viewport().mapToGlobal(position))

    def add_selected_to_playlist(self):
        """
        Ajoute les éléments sélectionnés (fichiers et dossiers) à la playlist.
        """
        selected_indexes = self.tree_view.selectionModel().selectedIndexes()

        if not isinstance(self.tree_view.model(), FileSystemModel):
            print("Le modèle actuel n'est pas un FileSystemModel.")
            return

        def add_files_recursively(node: FileNode):
            """Ajoute tous les fichiers audio d’un nœud (récursivement)."""
            if not node:
                return

            if node.is_directory:
                # Charger les enfants s’ils ne sont pas encore chargés
                if not node.loaded:
                    self.tree_view.model().load_children(node)

                for child in node.children:
                    add_files_recursively(child)
            else:
                # C’est un fichier : on l’ajoute
                try:
                    self.mpd_client.add_to_playlist_active(node.path)
                    print(f"Ajouté à la playlist : {node.path}")
                except Exception as e:
                    print(f"Erreur lors de l'ajout à la playlist : {e}")

        for index in selected_indexes:
            node = index.internalPointer()
            add_files_recursively(node)

        self.playlist_ac_tab.update_playlist()

    def replace_playlist_with_selected(self):
        """Remplace la playlist active avec les éléments sélectionnés."""
        print("replace playlist début")
        try:
            print(self.mpd_client.get_current_playlist())
            self.mpd_client.clear_to_playlist_active()  # Vider la playlist active
            print("Playlist active effacée.")
            self.add_selected_to_playlist()  # Ajouter les nouveaux fichiers
        except Exception as e:
            print(f"Erreur lors du remplacement de la playlist : {e}")




    def setup_shortcuts(self):
        """Configure les raccourcis pour la navigation clavier et l'ajout à la playlist."""
        # Raccourci pour ajouter à la playlist avec la touche '0'
        add_to_playlist_shortcut = QShortcut(QKeySequence("0"), self)
        add_to_playlist_shortcut.activated.connect(self.add_selected_to_playlist)

        # Navigation dans la liste avec les flèches et les touches Entrée/Retour Arrière
        self.setFocusPolicy(Qt.StrongFocus)

    def keyPressEvent(self, event):
        """Gère les événements de touches pour la navigation dans la liste."""
        if event.key() == Qt.Key_Down:
            # Flèche Bas : se déplacer vers le bas dans la liste
            next_row = (self.library_list.currentRow() + 1) % self.library_list.count()
            self.library_list.setCurrentRow(next_row)
        elif event.key() == Qt.Key_Up:
            # Flèche Haut : se déplacer vers le haut dans la liste
            previous_row = (self.library_list.currentRow() - 1) % self.library_list.count()
            self.library_list.setCurrentRow(previous_row)
        elif event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            # Entrée : ouvrir le dossier ou sélectionner le fichier
            current_item = self.library_list.currentItem()
            if current_item:
                self.open_directory_or_file(current_item)
        elif event.key() == Qt.Key_Backspace:
            # Retour Arrière : revenir au dossier parent
            self.go_to_parent_directory()
        else:
            # Appel de la méthode parente pour les autres touches
            super().keyPressEvent(event)



    # def is_audio_file(self, filename):
    #     """Vérifie si le fichier a une extension audio valide."""
    #     audio_extensions = {".mp3", ".flac", ".wav", ".aac", ".ogg"}
    #     return any(filename.lower().endswith(ext) for ext in audio_extensions)



