# -*- coding: utf-8 -*-
"""
Multi Project Canvas Plugin for QGIS v7
With i18n support (English/Italian)
"""

from qgis.PyQt.QtCore import (
    Qt, QTimer, pyqtSignal, QSize, QMimeData, QPoint, 
    QByteArray, QBuffer, QIODevice, QRectF, QTranslator,
    QCoreApplication, QLocale, QSettings
)
from qgis.PyQt.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QHBoxLayout, QListWidget, 
    QListWidgetItem, QToolButton, QMenu, QAction, QInputDialog, 
    QMessageBox, QFileDialog, QApplication, QSizePolicy, QLabel,
    QFrame, QAbstractItemView, QStyle, QStyledItemDelegate,
    QLineEdit, QScrollArea, QGroupBox, QSplitter, QTabWidget,
    QTreeWidget, QTreeWidgetItem, QDialog, QDialogButtonBox,
    QFormLayout, QComboBox, QSpinBox, QCheckBox, QWidgetAction
)
from qgis.PyQt.QtGui import (
    QIcon, QColor, QPixmap, QPainter, QFont, QBrush, QPen,
    QImage, QDrag, QPainterPath
)
from qgis.core import (
    QgsProject, QgsApplication, Qgis, QgsCoordinateReferenceSystem,
    QgsRectangle, QgsMapSettings, QgsMapRendererParallelJob,
    QgsMapRendererSequentialJob, QgsBookmarkManager, QgsBookmark,
    QgsReferencedRectangle
)
from qgis.gui import QgsMapCanvas
import os
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime


class Sketchy:
    """Translation system for the plugin"""
    
    _translations = {
        'it': {
            # General
            'Projects': 'Progetti',
            'PROJECTS': 'PROGETTI',
            'Project': 'Progetto',
            'Multi Project Panel': 'Pannello Multi Progetto',
            'Multi-Project Panel': 'Pannello Multi-Progetto',
            
            # Actions
            'New project': 'Nuovo progetto',
            'Open project': 'Apri progetto',
            'Save': 'Salva',
            'Save as': 'Salva come',
            'Save project': 'Salva progetto',
            'Duplicate': 'Duplica',
            'Duplicate project': 'Duplica progetto',
            'Close': 'Chiudi',
            'Close others': 'Chiudi altri',
            'Activate': 'Attiva',
            'Rename...': 'Rinomina...',
            'Rename': 'Rinomina',
            'Rename project': 'Rinomina progetto',
            'Move up': 'Sposta su',
            'Move down': 'Sposta giù',
            'Show in Explorer': 'Mostra in Esplora risorse',
            'Delete': 'Elimina',
            
            # Navigation
            'Back': 'Indietro',
            'Forward': 'Avanti',
            'Sync': 'Sincronizza',
            'Sync extent to all projects': 'Sincronizza estensione a tutti i progetti',
            'Extent synced to {0} projects': 'Estensione sincronizzata a {0} progetti',
            
            # Bookmarks
            'Bookmarks': 'Segnalibri',
            'Add bookmark': 'Aggiungi segnalibro',
            'Add bookmark from current extent': 'Aggiungi segnalibro dall\'estensione corrente',
            'New bookmark': 'Nuovo segnalibro',
            'Go to': 'Vai a',
            'bookmark': 'segnalibro',
            'bookmarks': 'segnalibri',
            
            # Thumbnails
            'Show/hide thumbnails': 'Mostra/nascondi anteprime',
            'Refresh thumbnail': 'Aggiorna anteprima',
            
            # Search
            'Search layers in all projects...': 'Cerca layer in tutti i progetti...',
            
            # Workspace
            'Save workspace...': 'Salva workspace...',
            'Load workspace...': 'Carica workspace...',
            'Save workspace': 'Salva workspace',
            'Load workspace': 'Carica workspace',
            'Workspace saved': 'Workspace salvato',
            'Workspace loaded': 'Workspace caricato',
            
            # Layer info
            'layer': 'layer',
            'layers': 'layer',
            'Not saved': 'Non salvato',
            
            # Messages
            'New': 'Nuovo',
            'Opened': 'Aperto',
            'Saved': 'Salvato',
            'Duplicated': 'Duplicato',
            'copy': 'copia',
            'Panel activated. Ctrl+T for new project.': 'Pannello attivato. Ctrl+T per nuovo progetto.',
            
            # Dialogs
            'Name:': 'Nome:',
            'Confirm': 'Conferma',
            'Warning': 'Attenzione',
            'Error': 'Errore',
            'Save changes': 'Salva modifiche',
            "'{0}' has been modified. Save?": "'{0}' è stato modificato. Salvare?",
            'Cannot close the last project': 'Impossibile chiudere l\'ultimo progetto',
            'Close all other projects?': 'Chiudere tutti gli altri progetti?',
            'There are unsaved projects. Close anyway?': 'Ci sono progetti non salvati. Chiudere comunque?',
            'Cannot open': 'Impossibile aprire',
            'Cannot load': 'Impossibile caricare',
        }
    }
    
    _current_locale = None
    
    @classmethod
    def get_locale(cls):
        if cls._current_locale is None:
            locale = QSettings().value('locale/userLocale', 'en_US')
            cls._current_locale = locale[0:2] if locale else 'en'
        return cls._current_locale
    
    @classmethod
    def translate(cls, message):
        locale = cls.get_locale()
        if locale in cls._translations and message in cls._translations[locale]:
            return cls._translations[locale][message]
        return message


def tr(message):
    """Translate a string using the current locale."""
    return Sketchy.translate(message)


class ThumbnailGenerator:
    """Generates project thumbnails"""
    
    @staticmethod
    def generate(project, canvas, size=QSize(180, 120)):
        image = QImage(size, QImage.Format_ARGB32)
        image.fill(QColor(255, 255, 255))
        
        settings = QgsMapSettings()
        settings.setOutputSize(size)
        settings.setDestinationCrs(canvas.mapSettings().destinationCrs())
        settings.setExtent(canvas.extent())
        settings.setLayers(canvas.layers())
        settings.setBackgroundColor(QColor(255, 255, 255))
        
        job = QgsMapRendererSequentialJob(settings)
        job.start()
        job.waitForFinished()
        
        return QPixmap.fromImage(job.renderedImage())


class ExtentHistory:
    """Manages extent history for back/forward navigation"""
    
    def __init__(self, max_size=50):
        self.history = []
        self.current_index = -1
        self.max_size = max_size
        self._updating = False
    
    def add(self, extent, crs):
        if self._updating:
            return
        
        if self.current_index < len(self.history) - 1:
            self.history = self.history[:self.current_index + 1]
        
        if self.history:
            last = self.history[-1]
            if (abs(last['extent'][0] - extent.xMinimum()) < 0.0001 and
                abs(last['extent'][1] - extent.yMinimum()) < 0.0001):
                return
        
        self.history.append({
            'extent': [extent.xMinimum(), extent.yMinimum(), 
                      extent.xMaximum(), extent.yMaximum()],
            'crs': crs.authid()
        })
        
        if len(self.history) > self.max_size:
            self.history.pop(0)
        
        self.current_index = len(self.history) - 1
    
    def can_go_back(self):
        return self.current_index > 0
    
    def can_go_forward(self):
        return self.current_index < len(self.history) - 1
    
    def go_back(self):
        if self.can_go_back():
            self.current_index -= 1
            return self.history[self.current_index]
        return None
    
    def go_forward(self):
        if self.can_go_forward():
            self.current_index += 1
            return self.history[self.current_index]
        return None
    
    def set_updating(self, updating):
        self._updating = updating


class ProjectBookmark:
    """A project bookmark"""
    def __init__(self, name, extent, crs):
        self.name = name
        self.extent = extent
        self.crs = crs
        self.created = datetime.now().isoformat()


class ProjectTab:
    """Represents a project with all its properties"""
    
    def __init__(self, name, temp_dir):
        self.name = name
        self.temp_dir = temp_dir
        self.temp_file = os.path.join(temp_dir, f"project_{id(self)}.qgz")
        self.saved_file = None
        self.is_modified = False
        self.extent = None
        self.crs = "EPSG:4326"
        self.layer_count = 0
        self.thumbnail = None
        self.bookmarks = []
        self.extent_history = ExtentHistory()
        self.notes = ""
        self.created = datetime.now().isoformat()
        self.last_modified = datetime.now().isoformat()
    
    def capture_state(self, project, canvas):
        self.extent = [
            canvas.extent().xMinimum(),
            canvas.extent().yMinimum(),
            canvas.extent().xMaximum(),
            canvas.extent().yMaximum()
        ]
        self.crs = canvas.mapSettings().destinationCrs().authid()
        self.layer_count = len(project.mapLayers())
        self.last_modified = datetime.now().isoformat()
        
        if self.layer_count > 0:
            self.thumbnail = ThumbnailGenerator.generate(project, canvas)
        
        self.extent_history.add(canvas.extent(), canvas.mapSettings().destinationCrs())
        
        return project.write(self.temp_file)
    
    def restore_state(self, project, canvas, iface):
        project.clear()
        
        if os.path.exists(self.temp_file):
            project.read(self.temp_file)
        
        if self.crs:
            crs = QgsCoordinateReferenceSystem(self.crs)
            if crs.isValid():
                canvas.setDestinationCrs(crs)
        
        if self.extent and self.extent[0] != self.extent[2]:
            canvas.setExtent(QgsRectangle(
                self.extent[0], self.extent[1],
                self.extent[2], self.extent[3]
            ))
        
        canvas.refresh()
        iface.layerTreeView().layerTreeModel().setRootGroup(project.layerTreeRoot())
        
        self.layer_count = len(project.mapLayers())
    
    def add_bookmark(self, name, extent, crs):
        bm = ProjectBookmark(name, extent, crs)
        self.bookmarks.append(bm)
        return bm
    
    def remove_bookmark(self, index):
        if 0 <= index < len(self.bookmarks):
            self.bookmarks.pop(index)
    
    def to_dict(self):
        return {
            'name': self.name,
            'saved_file': self.saved_file,
            'extent': self.extent,
            'crs': self.crs,
            'layer_count': self.layer_count,
            'notes': self.notes,
            'bookmarks': [
                {'name': b.name, 'extent': b.extent, 'crs': b.crs, 'created': b.created}
                for b in self.bookmarks
            ],
            'created': self.created,
            'last_modified': self.last_modified
        }
    
    def from_dict(self, data):
        self.name = data.get('name', self.name)
        self.saved_file = data.get('saved_file')
        self.extent = data.get('extent')
        self.crs = data.get('crs', 'EPSG:4326')
        self.layer_count = data.get('layer_count', 0)
        self.notes = data.get('notes', '')
        self.created = data.get('created', self.created)
        self.last_modified = data.get('last_modified', self.last_modified)
        
        self.bookmarks = []
        for bm_data in data.get('bookmarks', []):
            bm = ProjectBookmark(
                bm_data['name'],
                bm_data['extent'],
                bm_data['crs']
            )
            bm.created = bm_data.get('created', bm.created)
            self.bookmarks.append(bm)
    
    def cleanup(self):
        if os.path.exists(self.temp_file):
            try:
                os.remove(self.temp_file)
            except:
                pass


class ProjectItemDelegate(QStyledItemDelegate):
    """Delegate with thumbnail"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.show_thumbnails = True
    
    def sizeHint(self, option, index):
        if self.show_thumbnails:
            return QSize(220, 90)
        return QSize(220, 50)
    
    def paint(self, painter, option, index):
        painter.save()
        
        name = index.data(Qt.DisplayRole)
        is_active = index.data(Qt.UserRole + 1)
        is_modified = index.data(Qt.UserRole + 2)
        layer_count = index.data(Qt.UserRole + 3) or 0
        saved_file = index.data(Qt.UserRole + 4)
        thumbnail = index.data(Qt.UserRole + 5)
        bookmark_count = index.data(Qt.UserRole + 6) or 0
        
        # Background
        if option.state & QStyle.State_Selected:
            painter.fillRect(option.rect, QColor(51, 153, 255))
            text_color = QColor(255, 255, 255)
            secondary_color = QColor(220, 220, 220)
        elif is_active:
            painter.fillRect(option.rect, QColor(230, 242, 255))
            text_color = QColor(0, 0, 0)
            secondary_color = QColor(100, 100, 100)
        else:
            painter.fillRect(option.rect, QColor(255, 255, 255))
            text_color = QColor(0, 0, 0)
            secondary_color = QColor(128, 128, 128)
        
        if is_active:
            painter.setPen(QPen(QColor(51, 153, 255), 2))
            painter.drawRect(option.rect.adjusted(1, 1, -1, -1))
        
        rect = option.rect
        
        if self.show_thumbnails and thumbnail:
            thumb_rect = rect.adjusted(6, 6, -rect.width() + 76, -6)
            painter.fillRect(thumb_rect, QColor(240, 240, 240))
            scaled = thumbnail.scaled(thumb_rect.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            x_offset = (thumb_rect.width() - scaled.width()) // 2
            y_offset = (thumb_rect.height() - scaled.height()) // 2
            painter.drawPixmap(thumb_rect.x() + x_offset, thumb_rect.y() + y_offset, scaled)
            painter.setPen(QColor(200, 200, 200))
            painter.drawRect(thumb_rect)
            text_x = 82
        else:
            icon_rect = rect.adjusted(8, 8 if not self.show_thumbnails else 20, -rect.width() + 40, -8 if not self.show_thumbnails else -20)
            icon = QgsApplication.getThemeIcon("/mIconQgsProjectFile.svg")
            icon.paint(painter, icon_rect)
            text_x = 45
        
        if is_modified:
            painter.setBrush(QColor(255, 152, 0))
            painter.setPen(Qt.NoPen)
            mod_x = text_x - 10 if self.show_thumbnails else 35
            painter.drawEllipse(rect.x() + mod_x, rect.y() + 8, 8, 8)
        
        painter.setPen(text_color)
        name_font = QFont()
        name_font.setBold(is_active)
        name_font.setPointSize(10)
        painter.setFont(name_font)
        
        name_rect = rect.adjusted(text_x, 8, -8, -rect.height() + 28)
        display_name = name + (" •" if is_modified else "")
        elided = painter.fontMetrics().elidedText(display_name, Qt.ElideRight, name_rect.width())
        painter.drawText(name_rect, Qt.AlignLeft | Qt.AlignVCenter, elided)
        
        info_font = QFont()
        info_font.setPointSize(8)
        painter.setFont(info_font)
        painter.setPen(secondary_color)
        
        info_rect = rect.adjusted(text_x, 28, -8, -rect.height() + 44)
        
        # Translated layer/bookmark text
        layer_text = tr("layer") if layer_count == 1 else tr("layers")
        info_parts = [f"{layer_count} {layer_text}"]
        if bookmark_count > 0:
            bm_text = tr("bookmark") if bookmark_count == 1 else tr("bookmarks")
            info_parts.append(f"{bookmark_count} {bm_text}")
        info_text = " • ".join(info_parts)
        painter.drawText(info_rect, Qt.AlignLeft | Qt.AlignVCenter, info_text)
        
        if self.show_thumbnails:
            file_rect = rect.adjusted(text_x, 44, -8, -rect.height() + 60)
            if saved_file:
                file_text = Path(saved_file).name
            else:
                file_text = tr("Not saved")
            elided_file = painter.fontMetrics().elidedText(file_text, Qt.ElideMiddle, file_rect.width())
            painter.drawText(file_rect, Qt.AlignLeft | Qt.AlignVCenter, elided_file)
        
        painter.setPen(QColor(230, 230, 230))
        painter.drawLine(rect.bottomLeft(), rect.bottomRight())
        
        painter.restore()


class CollapsibleSection(QWidget):
    """A collapsible section widget with header and content"""
    
    collapsed_changed = pyqtSignal(bool)
    
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self._is_collapsed = False
        self._title = title
        self._content_widget = None
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header button
        self.header_btn = QToolButton()
        self.header_btn.setStyleSheet("""
            QToolButton {
                background: #e8e8e8;
                border: none;
                border-top: 1px solid #ccc;
                padding: 4px 8px;
                font-weight: bold;
                font-size: 10px;
                text-align: left;
            }
            QToolButton:hover {
                background: #ddd;
            }
        """)
        self.header_btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.header_btn.setArrowType(Qt.DownArrow)
        self.header_btn.setText(self._title)
        self.header_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.header_btn.setFixedHeight(24)
        self.header_btn.clicked.connect(self.toggle_collapsed)
        layout.addWidget(self.header_btn)
        
        # Content container
        self.content_area = QWidget()
        self.content_layout = QVBoxLayout(self.content_area)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)
        layout.addWidget(self.content_area)
    
    def set_content(self, widget):
        self._content_widget = widget
        self.content_layout.addWidget(widget)
    
    def toggle_collapsed(self):
        self._is_collapsed = not self._is_collapsed
        self.content_area.setVisible(not self._is_collapsed)
        self.header_btn.setArrowType(Qt.RightArrow if self._is_collapsed else Qt.DownArrow)
        self.collapsed_changed.emit(self._is_collapsed)
    
    def set_collapsed(self, collapsed):
        self._is_collapsed = collapsed
        self.content_area.setVisible(not collapsed)
        self.header_btn.setArrowType(Qt.RightArrow if collapsed else Qt.DownArrow)
    
    def is_collapsed(self):
        return self._is_collapsed
    
    def sizeHint(self):
        if self._is_collapsed:
            return QSize(200, 24)  # Just header height
        return super().sizeHint()
    
    def minimumSizeHint(self):
        return QSize(100, 24)  # Just header height minimum


class BookmarkWidget(QWidget):
    """Widget to manage bookmarks for the current project"""
    
    bookmark_activated = pyqtSignal(object)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.project_tab = None
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)
        
        # Header with add button
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        
        self.btn_add = QToolButton()
        self.btn_add.setIcon(QgsApplication.getThemeIcon("/mActionAdd.svg"))
        self.btn_add.setToolTip(tr("Add bookmark from current extent"))
        self.btn_add.clicked.connect(self.add_bookmark)
        header.addWidget(self.btn_add)
        
        header.addStretch()
        
        self.bookmark_count_label = QLabel("0")
        self.bookmark_count_label.setStyleSheet("color: #666; font-size: 10px;")
        header.addWidget(self.bookmark_count_label)
        
        layout.addLayout(header)
        
        # Bookmark list - compact by default
        self.bookmark_list = QListWidget()
        self.bookmark_list.setMinimumHeight(0)
        self.bookmark_list.setMaximumHeight(100)
        self.bookmark_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #ddd;
                border-radius: 3px;
                background: white;
            }
            QListWidget::item {
                padding: 2px 4px;
            }
            QListWidget::item:hover {
                background: #f0f0f0;
            }
        """)
        self.bookmark_list.itemDoubleClicked.connect(self._on_double_click)
        self.bookmark_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.bookmark_list.customContextMenuRequested.connect(self._show_menu)
        layout.addWidget(self.bookmark_list)
    
    def set_project(self, project_tab):
        self.project_tab = project_tab
        self.refresh()
    
    def refresh(self):
        self.bookmark_list.clear()
        if not self.project_tab:
            self.bookmark_count_label.setText("0")
            return
        
        count = len(self.project_tab.bookmarks)
        self.bookmark_count_label.setText(str(count))
        
        for i, bm in enumerate(self.project_tab.bookmarks):
            item = QListWidgetItem(QgsApplication.getThemeIcon("/mActionBookmarks.svg"), bm.name)
            item.setData(Qt.UserRole, i)
            self.bookmark_list.addItem(item)
        
        # Auto-adjust height based on content
        if count == 0:
            self.bookmark_list.setMaximumHeight(30)
        else:
            self.bookmark_list.setMaximumHeight(min(100, count * 24 + 10))
    
    def add_bookmark(self):
        if not self.project_tab:
            return
        self.bookmark_activated.emit(None)
    
    def do_add_bookmark(self, name, extent, crs):
        if self.project_tab:
            self.project_tab.add_bookmark(name, extent, crs)
            self.refresh()
    
    def _on_double_click(self, item):
        if not self.project_tab:
            return
        
        idx = item.data(Qt.UserRole)
        if 0 <= idx < len(self.project_tab.bookmarks):
            self.bookmark_activated.emit(self.project_tab.bookmarks[idx])
    
    def _show_menu(self, pos):
        item = self.bookmark_list.itemAt(pos)
        if not item:
            return
        
        idx = item.data(Qt.UserRole)
        
        menu = QMenu(self)
        
        action_goto = menu.addAction(tr("Go to"))
        action_goto.triggered.connect(lambda: self._on_double_click(item))
        
        action_rename = menu.addAction(tr("Rename"))
        action_rename.triggered.connect(lambda: self._rename(idx))
        
        menu.addSeparator()
        
        action_delete = menu.addAction(tr("Delete"))
        action_delete.triggered.connect(lambda: self._delete(idx))
        
        menu.exec_(self.bookmark_list.mapToGlobal(pos))
    
    def _rename(self, idx):
        if not self.project_tab or idx >= len(self.project_tab.bookmarks):
            return
        
        bm = self.project_tab.bookmarks[idx]
        name, ok = QInputDialog.getText(self, tr("Rename"), tr("Name:"), text=bm.name)
        if ok and name:
            bm.name = name
            self.refresh()
    
    def _delete(self, idx):
        if self.project_tab:
            self.project_tab.remove_bookmark(idx)
            self.refresh()


class SearchWidget(QWidget):
    """Widget to search across projects"""
    
    result_selected = pyqtSignal(int, str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.projects = []
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(tr("Search layers in all projects..."))
        self.search_input.textChanged.connect(self.do_search)
        search_layout.addWidget(self.search_input)
        
        self.btn_clear = QToolButton()
        self.btn_clear.setIcon(QgsApplication.getThemeIcon("/mActionRemove.svg"))
        self.btn_clear.clicked.connect(self.clear_search)
        self.btn_clear.setVisible(False)
        search_layout.addWidget(self.btn_clear)
        
        layout.addLayout(search_layout)
        
        self.results_tree = QTreeWidget()
        self.results_tree.setHeaderHidden(True)
        self.results_tree.setMaximumHeight(200)
        self.results_tree.itemDoubleClicked.connect(self._on_result_click)
        self.results_tree.setVisible(False)
        layout.addWidget(self.results_tree)
    
    def set_projects(self, projects):
        self.projects = projects
    
    def do_search(self, text):
        self.results_tree.clear()
        
        if len(text) < 2:
            self.results_tree.setVisible(False)
            self.btn_clear.setVisible(False)
            return
        
        self.btn_clear.setVisible(True)
        text_lower = text.lower()
        has_results = False
        
        for proj_idx, proj in enumerate(self.projects):
            proj_matches = text_lower in proj.name.lower()
            
            layer_matches = []
            if os.path.exists(proj.temp_file):
                temp_proj = QgsProject()
                temp_proj.read(proj.temp_file)
                for layer_id, layer in temp_proj.mapLayers().items():
                    if text_lower in layer.name().lower():
                        layer_matches.append((layer_id, layer.name()))
                temp_proj.clear()
            
            bookmark_matches = [bm.name for bm in proj.bookmarks if text_lower in bm.name.lower()]
            
            if proj_matches or layer_matches or bookmark_matches:
                has_results = True
                proj_item = QTreeWidgetItem([f"📁 {proj.name}"])
                proj_item.setData(0, Qt.UserRole, proj_idx)
                proj_item.setData(0, Qt.UserRole + 1, None)
                
                for layer_id, layer_name in layer_matches:
                    layer_item = QTreeWidgetItem([f"  📄 {layer_name}"])
                    layer_item.setData(0, Qt.UserRole, proj_idx)
                    layer_item.setData(0, Qt.UserRole + 1, layer_id)
                    proj_item.addChild(layer_item)
                
                for bm_name in bookmark_matches:
                    bm_item = QTreeWidgetItem([f"  🔖 {bm_name}"])
                    bm_item.setData(0, Qt.UserRole, proj_idx)
                    bm_item.setData(0, Qt.UserRole + 1, f"bookmark:{bm_name}")
                    proj_item.addChild(bm_item)
                
                self.results_tree.addTopLevelItem(proj_item)
                proj_item.setExpanded(True)
        
        self.results_tree.setVisible(has_results)
    
    def clear_search(self):
        self.search_input.clear()
        self.results_tree.clear()
        self.results_tree.setVisible(False)
        self.btn_clear.setVisible(False)
    
    def _on_result_click(self, item, column):
        proj_idx = item.data(0, Qt.UserRole)
        extra = item.data(0, Qt.UserRole + 1)
        self.result_selected.emit(proj_idx, extra or "")


class RenameDialog(QDialog):
    """Dialog to rename a project"""
    
    def __init__(self, current_name, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("Rename project"))
        self.setMinimumWidth(300)
        
        layout = QVBoxLayout(self)
        
        form = QFormLayout()
        self.name_input = QLineEdit(current_name)
        self.name_input.selectAll()
        form.addRow(tr("Name:"), self.name_input)
        layout.addLayout(form)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def get_name(self):
        return self.name_input.text()


class MultiProjectDock(QDockWidget):
    """Main dock widget v7 with i18n"""
    
    project_switched = pyqtSignal(int)
    
    def __init__(self, iface, parent=None):
        super().__init__(tr("Projects"), parent)
        self.iface = iface
        self.project = QgsProject.instance()
        self.canvas = iface.mapCanvas()
        
        self.temp_dir = tempfile.mkdtemp(prefix="qgis_mp_")
        self.projects = []
        self.current_index = -1
        self.tab_counter = 0
        self._switching = False
        self._tracking_extent = True
        
        self.setup_ui()
        self.setup_connections()
        
        QTimer.singleShot(200, self._init_first_project)
    
    def setup_ui(self):
        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.setMinimumWidth(260)
        
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # === HEADER ===
        header = QFrame()
        header.setStyleSheet("""
            QFrame { background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #4a90d9, stop:1 #357abd); }
            QLabel { color: white; font-weight: bold; font-size: 11px; }
            QToolButton { background: transparent; border: none; border-radius: 3px; padding: 4px; }
            QToolButton:hover { background: rgba(255,255,255,0.2); }
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(10, 8, 10, 8)
        
        header_layout.addWidget(QLabel(tr("PROJECTS")))
        header_layout.addStretch()
        
        self.btn_toggle_thumb = QToolButton()
        self.btn_toggle_thumb.setIcon(QgsApplication.getThemeIcon("/mActionShowAllLayers.svg"))
        self.btn_toggle_thumb.setToolTip(tr("Show/hide thumbnails"))
        self.btn_toggle_thumb.setCheckable(True)
        self.btn_toggle_thumb.setChecked(True)
        self.btn_toggle_thumb.setIconSize(QSize(16, 16))
        self.btn_toggle_thumb.clicked.connect(self._toggle_thumbnails)
        header_layout.addWidget(self.btn_toggle_thumb)
        
        self.btn_new = QToolButton()
        self.btn_new.setIcon(QgsApplication.getThemeIcon("/mActionAdd.svg"))
        self.btn_new.setToolTip(tr("New project") + " (Ctrl+T)")
        self.btn_new.setShortcut("Ctrl+T")
        self.btn_new.setIconSize(QSize(16, 16))
        self.btn_new.clicked.connect(self.new_project)
        header_layout.addWidget(self.btn_new)
        
        self.btn_open = QToolButton()
        self.btn_open.setIcon(QgsApplication.getThemeIcon("/mActionFileOpen.svg"))
        self.btn_open.setToolTip(tr("Open project") + " (Ctrl+Shift+O)")
        self.btn_open.setShortcut("Ctrl+Shift+O")
        self.btn_open.setIconSize(QSize(16, 16))
        self.btn_open.clicked.connect(self.open_project)
        header_layout.addWidget(self.btn_open)
        
        main_layout.addWidget(header)
        
        # === SEARCH ===
        self.search_widget = SearchWidget()
        self.search_widget.result_selected.connect(self._on_search_result)
        main_layout.addWidget(self.search_widget)
        
        # === SPLITTER FOR RESIZABLE SECTIONS ===
        self.splitter = QSplitter(Qt.Vertical)
        self.splitter.setHandleWidth(4)
        self.splitter.setStyleSheet("""
            QSplitter::handle {
                background: #ddd;
            }
            QSplitter::handle:hover {
                background: #4a90d9;
            }
        """)
        
        # === PROJECT LIST ===
        self.project_list = QListWidget()
        self.delegate = ProjectItemDelegate()
        self.project_list.setItemDelegate(self.delegate)
        self.project_list.setDragDropMode(QAbstractItemView.InternalMove)
        self.project_list.setDefaultDropAction(Qt.MoveAction)
        self.project_list.setStyleSheet("""
            QListWidget { border: none; background: #fafafa; }
            QListWidget::item { padding: 0; }
        """)
        self.project_list.itemClicked.connect(self._on_item_clicked)
        self.project_list.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.project_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.project_list.customContextMenuRequested.connect(self._show_context_menu)
        self.project_list.model().rowsMoved.connect(self._on_rows_moved)
        self.splitter.addWidget(self.project_list)
        
        # === BOOKMARKS SECTION (in splitter) ===
        self.bookmark_section = CollapsibleSection(tr("Bookmarks"))
        self.bookmark_widget = BookmarkWidget()
        self.bookmark_widget.bookmark_activated.connect(self._on_bookmark_activated)
        self.bookmark_section.set_content(self.bookmark_widget)
        self.bookmark_section.set_collapsed(True)  # Collapsed by default
        self.bookmark_section.collapsed_changed.connect(self._on_bookmark_collapsed_changed)
        self.splitter.addWidget(self.bookmark_section)
        
        # Set initial sizes (projects get all space when bookmarks collapsed)
        self.splitter.setSizes([500, 24])  # 24 is just the header height
        self.splitter.setStretchFactor(0, 10)  # Project list stretches much more
        self.splitter.setStretchFactor(1, 0)  # Bookmarks doesn't stretch when collapsed
        self.splitter.setCollapsible(0, False)  # Project list not collapsible
        self.splitter.setCollapsible(1, False)  # Prevent full collapse
        
        main_layout.addWidget(self.splitter, 1)
        
        # === NAVIGATION BAR ===
        nav_frame = QFrame()
        nav_frame.setStyleSheet("""
            QFrame { background: #f5f5f5; border-top: 1px solid #ddd; border-bottom: 1px solid #ddd; }
            QToolButton { background: transparent; border: none; padding: 4px 8px; }
            QToolButton:hover { background: #e0e0e0; }
            QToolButton:disabled { color: #aaa; }
        """)
        nav_layout = QHBoxLayout(nav_frame)
        nav_layout.setContentsMargins(8, 4, 8, 4)
        nav_layout.setSpacing(4)
        
        self.btn_back = QToolButton()
        self.btn_back.setIcon(QgsApplication.getThemeIcon("/mActionArrowLeft.svg"))
        self.btn_back.setToolTip(tr("Back") + " (Alt+←)")
        self.btn_back.clicked.connect(self.go_back)
        self.btn_back.setEnabled(False)
        nav_layout.addWidget(self.btn_back)
        
        self.btn_forward = QToolButton()
        self.btn_forward.setIcon(QgsApplication.getThemeIcon("/mActionArrowRight.svg"))
        self.btn_forward.setToolTip(tr("Forward") + " (Alt+→)")
        self.btn_forward.clicked.connect(self.go_forward)
        self.btn_forward.setEnabled(False)
        nav_layout.addWidget(self.btn_forward)
        
        nav_layout.addWidget(QLabel("|"))
        
        self.btn_sync_extent = QToolButton()
        self.btn_sync_extent.setText(tr("Sync"))
        self.btn_sync_extent.setToolTip(tr("Sync extent to all projects"))
        self.btn_sync_extent.clicked.connect(self.sync_extent_to_all)
        nav_layout.addWidget(self.btn_sync_extent)
        
        nav_layout.addStretch()
        
        self.btn_add_bookmark = QToolButton()
        self.btn_add_bookmark.setIcon(QgsApplication.getThemeIcon("/mActionNewBookmark.svg"))
        self.btn_add_bookmark.setToolTip(tr("Add bookmark"))
        self.btn_add_bookmark.clicked.connect(self._add_bookmark_current)
        nav_layout.addWidget(self.btn_add_bookmark)
        
        main_layout.addWidget(nav_frame)
        
        # === FOOTER ===
        footer = QFrame()
        footer.setStyleSheet("""
            QFrame { background: #f0f0f0; border-top: 1px solid #ddd; }
            QToolButton { background: transparent; border: 1px solid transparent;
                border-radius: 3px; padding: 6px 10px; font-size: 11px; }
            QToolButton:hover { background: #e0e0e0; border: 1px solid #ccc; }
        """)
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(8, 6, 8, 6)
        
        self.btn_save = QToolButton()
        self.btn_save.setText(tr("Save"))
        self.btn_save.setIcon(QgsApplication.getThemeIcon("/mActionFileSave.svg"))
        self.btn_save.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.btn_save.clicked.connect(self.save_current)
        footer_layout.addWidget(self.btn_save)
        
        self.btn_save_as = QToolButton()
        self.btn_save_as.setText(tr("Save as"))
        self.btn_save_as.setIcon(QgsApplication.getThemeIcon("/mActionFileSaveAs.svg"))
        self.btn_save_as.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.btn_save_as.clicked.connect(self.save_current_as)
        footer_layout.addWidget(self.btn_save_as)
        
        footer_layout.addStretch()
        
        self.btn_menu = QToolButton()
        self.btn_menu.setIcon(QgsApplication.getThemeIcon("/mActionOptions.svg"))
        self.btn_menu.setPopupMode(QToolButton.InstantPopup)
        self._setup_menu()
        footer_layout.addWidget(self.btn_menu)
        
        main_layout.addWidget(footer)
        
        self.setWidget(main_widget)
    
    def _setup_menu(self):
        menu = QMenu(self)
        
        action_dup = menu.addAction(QgsApplication.getThemeIcon("/mActionDuplicateLayer.svg"), tr("Duplicate project"))
        action_dup.triggered.connect(self.duplicate_current)
        
        action_refresh_thumb = menu.addAction(tr("Refresh thumbnail"))
        action_refresh_thumb.triggered.connect(self._refresh_current_thumbnail)
        
        menu.addSeparator()
        
        action_save_ws = menu.addAction(tr("Save workspace..."))
        action_save_ws.triggered.connect(self.save_workspace)
        
        action_load_ws = menu.addAction(tr("Load workspace..."))
        action_load_ws.triggered.connect(self.load_workspace)
        
        menu.addSeparator()
        
        action_close_others = menu.addAction(tr("Close others"))
        action_close_others.triggered.connect(self.close_others)
        
        self.btn_menu.setMenu(menu)
    
    def setup_connections(self):
        self.project.layersAdded.connect(self._on_modified)
        self.project.layersRemoved.connect(self._on_modified)
        self.canvas.extentsChanged.connect(self._on_extent_changed)
    
    def _init_first_project(self):
        current_file = self.project.fileName()
        if current_file:
            name = Path(current_file).stem
        else:
            self.tab_counter += 1
            name = f"{tr('Project')} {self.tab_counter}"
        
        proj = ProjectTab(name, self.temp_dir)
        if current_file:
            proj.saved_file = current_file
        
        proj.capture_state(self.project, self.canvas)
        self.projects.append(proj)
        self.current_index = 0
        
        self._refresh_list()
        self._update_nav_buttons()
        self.bookmark_widget.set_project(proj)
        self.search_widget.set_projects(self.projects)
    
    def _refresh_list(self):
        self.project_list.clear()
        
        for i, proj in enumerate(self.projects):
            item = QListWidgetItem()
            item.setData(Qt.DisplayRole, proj.name)
            item.setData(Qt.UserRole, i)
            item.setData(Qt.UserRole + 1, i == self.current_index)
            item.setData(Qt.UserRole + 2, proj.is_modified)
            item.setData(Qt.UserRole + 3, proj.layer_count)
            item.setData(Qt.UserRole + 4, proj.saved_file)
            item.setData(Qt.UserRole + 5, proj.thumbnail)
            item.setData(Qt.UserRole + 6, len(proj.bookmarks))
            self.project_list.addItem(item)
        
        if 0 <= self.current_index < self.project_list.count():
            self.project_list.setCurrentRow(self.current_index)
        
        self.search_widget.set_projects(self.projects)
    
    def _toggle_thumbnails(self, checked):
        self.delegate.show_thumbnails = checked
        self._refresh_list()
    
    def _on_bookmark_collapsed_changed(self, collapsed):
        """Adjust splitter sizes when bookmark section is expanded/collapsed"""
        if collapsed:
            # When collapsed, give minimal space to bookmarks
            self.splitter.setSizes([self.splitter.height() - 24, 24])
        else:
            # When expanded, give reasonable space to bookmarks
            total = self.splitter.height()
            bookmark_height = min(150, total // 3)  # Max 150px or 1/3 of total
            self.splitter.setSizes([total - bookmark_height, bookmark_height])
    
    def _on_item_clicked(self, item):
        index = item.data(Qt.UserRole)
        if index != self.current_index:
            self._switch_to(index)
    
    def _on_item_double_clicked(self, item):
        index = item.data(Qt.UserRole)
        self._rename_project(index)
    
    def _on_rows_moved(self, parent, start, end, dest, row):
        new_order = []
        for i in range(self.project_list.count()):
            item = self.project_list.item(i)
            old_idx = item.data(Qt.UserRole)
            new_order.append(self.projects[old_idx])
        
        current_proj = self.projects[self.current_index]
        
        self.projects = new_order
        self.current_index = self.projects.index(current_proj)
        
        self._refresh_list()
    
    def _switch_to(self, index):
        if self._switching or index == self.current_index:
            return
        
        if index < 0 or index >= len(self.projects):
            return
        
        self._switching = True
        self._tracking_extent = False
        
        if 0 <= self.current_index < len(self.projects):
            self.projects[self.current_index].capture_state(self.project, self.canvas)
        
        self.projects[index].restore_state(self.project, self.canvas, self.iface)
        self.current_index = index
        
        self._refresh_list()
        self._update_nav_buttons()
        self.bookmark_widget.set_project(self.projects[index])
        
        self._switching = False
        self._tracking_extent = True
        
        self.project_switched.emit(index)
    
    def _on_extent_changed(self):
        if not self._tracking_extent or self._switching:
            return
        
        if 0 <= self.current_index < len(self.projects):
            proj = self.projects[self.current_index]
            proj.extent_history.add(
                self.canvas.extent(),
                self.canvas.mapSettings().destinationCrs()
            )
            self._update_nav_buttons()
    
    def _update_nav_buttons(self):
        if 0 <= self.current_index < len(self.projects):
            proj = self.projects[self.current_index]
            self.btn_back.setEnabled(proj.extent_history.can_go_back())
            self.btn_forward.setEnabled(proj.extent_history.can_go_forward())
        else:
            self.btn_back.setEnabled(False)
            self.btn_forward.setEnabled(False)
    
    def go_back(self):
        if self.current_index < 0:
            return
        
        proj = self.projects[self.current_index]
        state = proj.extent_history.go_back()
        
        if state:
            self._tracking_extent = False
            proj.extent_history.set_updating(True)
            
            extent = QgsRectangle(state['extent'][0], state['extent'][1],
                                  state['extent'][2], state['extent'][3])
            self.canvas.setExtent(extent)
            self.canvas.refresh()
            
            proj.extent_history.set_updating(False)
            self._tracking_extent = True
            self._update_nav_buttons()
    
    def go_forward(self):
        if self.current_index < 0:
            return
        
        proj = self.projects[self.current_index]
        state = proj.extent_history.go_forward()
        
        if state:
            self._tracking_extent = False
            proj.extent_history.set_updating(True)
            
            extent = QgsRectangle(state['extent'][0], state['extent'][1],
                                  state['extent'][2], state['extent'][3])
            self.canvas.setExtent(extent)
            self.canvas.refresh()
            
            proj.extent_history.set_updating(False)
            self._tracking_extent = True
            self._update_nav_buttons()
    
    def sync_extent_to_all(self):
        if self.current_index < 0:
            return
        
        current_extent = self.canvas.extent()
        current_crs = self.canvas.mapSettings().destinationCrs().authid()
        
        extent_list = [
            current_extent.xMinimum(),
            current_extent.yMinimum(),
            current_extent.xMaximum(),
            current_extent.yMaximum()
        ]
        
        for i, proj in enumerate(self.projects):
            if i != self.current_index:
                proj.extent = extent_list
                proj.crs = current_crs
        
        count = len(self.projects) - 1
        self.iface.messageBar().pushMessage(
            "Multi Project",
            tr("Extent synced to {0} projects").format(count),
            Qgis.Info, 2
        )
    
    def _add_bookmark_current(self):
        if self.current_index < 0:
            return
        
        name, ok = QInputDialog.getText(self, tr("New bookmark"), tr("Name:"))
        if ok and name:
            extent = [
                self.canvas.extent().xMinimum(),
                self.canvas.extent().yMinimum(),
                self.canvas.extent().xMaximum(),
                self.canvas.extent().yMaximum()
            ]
            crs = self.canvas.mapSettings().destinationCrs().authid()
            
            self.projects[self.current_index].add_bookmark(name, extent, crs)
            self.bookmark_widget.refresh()
            self._refresh_list()
    
    def _on_bookmark_activated(self, bookmark):
        if bookmark is None:
            self._add_bookmark_current()
            return
        
        extent = QgsRectangle(bookmark.extent[0], bookmark.extent[1],
                              bookmark.extent[2], bookmark.extent[3])
        self.canvas.setExtent(extent)
        self.canvas.refresh()
    
    def _on_search_result(self, proj_idx, extra):
        if proj_idx != self.current_index:
            self._switch_to(proj_idx)
        
        if extra and not extra.startswith("bookmark:"):
            layer = self.project.mapLayer(extra)
            if layer:
                self.iface.setActiveLayer(layer)
        elif extra and extra.startswith("bookmark:"):
            bm_name = extra[9:]
            proj = self.projects[proj_idx]
            for bm in proj.bookmarks:
                if bm.name == bm_name:
                    self._on_bookmark_activated(bm)
                    break
    
    def new_project(self):
        self._save_current_state()
        
        self.tab_counter += 1
        name = f"{tr('Project')} {self.tab_counter}"
        
        proj = ProjectTab(name, self.temp_dir)
        
        self.project.clear()
        self.canvas.setDestinationCrs(QgsCoordinateReferenceSystem("EPSG:4326"))
        self.canvas.refresh()
        
        proj.capture_state(self.project, self.canvas)
        
        self.projects.append(proj)
        self.current_index = len(self.projects) - 1
        
        self._refresh_list()
        self._update_nav_buttons()
        self.bookmark_widget.set_project(proj)
        
        self.iface.messageBar().pushMessage("Multi Project", f"{tr('New')}: {name}", Qgis.Info, 2)
    
    def open_project(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, tr("Open project"), "",
            "QGIS Projects (*.qgs *.qgz);;All (*.*)"
        )
        
        if not file_path:
            return
        
        self._save_current_state()
        
        name = Path(file_path).stem
        proj = ProjectTab(name, self.temp_dir)
        proj.saved_file = file_path
        
        self.project.clear()
        if self.project.read(file_path):
            self.canvas.setDestinationCrs(self.project.crs())
            self.iface.zoomFull()
            
            proj.capture_state(self.project, self.canvas)
            
            self.projects.append(proj)
            self.current_index = len(self.projects) - 1
            
            self._refresh_list()
            self._update_nav_buttons()
            self.bookmark_widget.set_project(proj)
            
            self.iface.messageBar().pushMessage("Multi Project", f"{tr('Opened')}: {name}", Qgis.Info, 2)
        else:
            QMessageBox.warning(self, tr("Error"), f"{tr('Cannot open')}:\n{file_path}")
    
    def save_current(self):
        if self.current_index < 0:
            return
        
        proj = self.projects[self.current_index]
        
        if proj.saved_file:
            if self.project.write(proj.saved_file):
                proj.is_modified = False
                self._refresh_list()
                self.iface.messageBar().pushMessage(
                    "Multi Project", f"{tr('Saved')}: {proj.saved_file}", Qgis.Success, 2
                )
        else:
            self.save_current_as()
    
    def save_current_as(self):
        if self.current_index < 0:
            return
        
        proj = self.projects[self.current_index]
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, tr("Save project"),
            proj.name + ".qgz",
            "QGIS Project (*.qgz);;QGIS Project XML (*.qgs)"
        )
        
        if file_path:
            if self.project.write(file_path):
                proj.saved_file = file_path
                proj.name = Path(file_path).stem
                proj.is_modified = False
                self._refresh_list()
                self.iface.messageBar().pushMessage(
                    "Multi Project", f"{tr('Saved')}: {file_path}", Qgis.Success, 2
                )
    
    def _save_current_state(self):
        if 0 <= self.current_index < len(self.projects):
            self.projects[self.current_index].capture_state(self.project, self.canvas)
    
    def _on_modified(self, *args):
        if self._switching:
            return
        
        if 0 <= self.current_index < len(self.projects):
            proj = self.projects[self.current_index]
            proj.is_modified = True
            proj.layer_count = len(self.project.mapLayers())
            self._refresh_list()
    
    def _refresh_current_thumbnail(self):
        if 0 <= self.current_index < len(self.projects):
            proj = self.projects[self.current_index]
            proj.thumbnail = ThumbnailGenerator.generate(self.project, self.canvas)
            self._refresh_list()
    
    def _show_context_menu(self, pos):
        item = self.project_list.itemAt(pos)
        if not item:
            return
        
        index = item.data(Qt.UserRole)
        proj = self.projects[index]
        
        menu = QMenu(self)
        
        if index != self.current_index:
            action_switch = menu.addAction(tr("Activate"))
            action_switch.triggered.connect(lambda: self._switch_to(index))
            menu.addSeparator()
        
        action_rename = menu.addAction(QgsApplication.getThemeIcon("/mActionRename.svg"), tr("Rename..."))
        action_rename.triggered.connect(lambda: self._rename_project(index))
        
        action_duplicate = menu.addAction(QgsApplication.getThemeIcon("/mActionDuplicateLayer.svg"), tr("Duplicate"))
        action_duplicate.triggered.connect(lambda: self._duplicate_project(index))
        
        menu.addSeparator()
        
        action_move_up = menu.addAction(tr("Move up"))
        action_move_up.triggered.connect(lambda: self._move_project(index, -1))
        action_move_up.setEnabled(index > 0)
        
        action_move_down = menu.addAction(tr("Move down"))
        action_move_down.triggered.connect(lambda: self._move_project(index, 1))
        action_move_down.setEnabled(index < len(self.projects) - 1)
        
        menu.addSeparator()
        
        if proj.saved_file:
            action_show = menu.addAction(tr("Show in Explorer"))
            action_show.triggered.connect(lambda: self._show_in_explorer(proj.saved_file))
            menu.addSeparator()
        
        action_close = menu.addAction(QgsApplication.getThemeIcon("/mActionRemove.svg"), tr("Close"))
        action_close.triggered.connect(lambda: self._close_project(index))
        action_close.setEnabled(len(self.projects) > 1)
        
        menu.exec_(self.project_list.mapToGlobal(pos))
    
    def _rename_project(self, index):
        if index < 0 or index >= len(self.projects):
            return
        
        proj = self.projects[index]
        dialog = RenameDialog(proj.name, self)
        
        if dialog.exec_() == QDialog.Accepted:
            new_name = dialog.get_name()
            if new_name:
                proj.name = new_name
                self._refresh_list()
    
    def _duplicate_project(self, index):
        if index < 0 or index >= len(self.projects):
            return
        
        source = self.projects[index]
        
        if index == self.current_index:
            source.capture_state(self.project, self.canvas)
        
        new_name = f"{source.name} ({tr('copy')})"
        proj = ProjectTab(new_name, self.temp_dir)
        proj.extent = source.extent.copy() if source.extent else None
        proj.crs = source.crs
        proj.layer_count = source.layer_count
        proj.bookmarks = [
            ProjectBookmark(b.name, b.extent.copy(), b.crs) 
            for b in source.bookmarks
        ]
        
        if os.path.exists(source.temp_file):
            shutil.copy(source.temp_file, proj.temp_file)
        
        self.projects.insert(index + 1, proj)
        self._refresh_list()
        
        self.iface.messageBar().pushMessage("Multi Project", f"{tr('Duplicated')}: {new_name}", Qgis.Info, 2)
    
    def duplicate_current(self):
        self._duplicate_project(self.current_index)
    
    def _move_project(self, index, direction):
        new_index = index + direction
        if new_index < 0 or new_index >= len(self.projects):
            return
        
        self.projects[index], self.projects[new_index] = self.projects[new_index], self.projects[index]
        
        if index == self.current_index:
            self.current_index = new_index
        elif new_index == self.current_index:
            self.current_index = index
        
        self._refresh_list()
    
    def _close_project(self, index):
        if len(self.projects) <= 1:
            QMessageBox.warning(self, tr("Warning"), tr("Cannot close the last project"))
            return
        
        proj = self.projects[index]
        
        if proj.is_modified:
            reply = QMessageBox.question(
                self, tr("Save changes"),
                tr("'{0}' has been modified. Save?").format(proj.name),
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
            )
            if reply == QMessageBox.Save:
                if index == self.current_index:
                    self.save_current()
            elif reply == QMessageBox.Cancel:
                return
        
        proj.cleanup()
        self.projects.pop(index)
        
        if index < self.current_index:
            self.current_index -= 1
        elif index == self.current_index:
            self.current_index = min(self.current_index, len(self.projects) - 1)
            self._switching = True
            self.projects[self.current_index].restore_state(self.project, self.canvas, self.iface)
            self._switching = False
            self.bookmark_widget.set_project(self.projects[self.current_index])
        
        self._refresh_list()
        self._update_nav_buttons()
    
    def close_others(self):
        if len(self.projects) <= 1:
            return
        
        reply = QMessageBox.question(
            self, tr("Confirm"), tr("Close all other projects?"),
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        current = self.projects[self.current_index]
        
        for i, proj in enumerate(self.projects):
            if i != self.current_index:
                proj.cleanup()
        
        self.projects = [current]
        self.current_index = 0
        self._refresh_list()
    
    def _show_in_explorer(self, file_path):
        import subprocess
        import platform
        
        if platform.system() == "Windows":
            subprocess.run(["explorer", "/select,", file_path])
        elif platform.system() == "Darwin":
            subprocess.run(["open", "-R", file_path])
        else:
            subprocess.run(["xdg-open", os.path.dirname(file_path)])
    
    def save_workspace(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, tr("Save workspace"), "",
            "Multi Project Workspace (*.mpw)"
        )
        
        if not file_path:
            return
        
        self._save_current_state()
        
        ws_dir = Path(file_path).parent / (Path(file_path).stem + "_projects")
        ws_dir.mkdir(exist_ok=True)
        
        workspace = {
            'version': '7.0',
            'current': self.current_index,
            'projects': []
        }
        
        for i, proj in enumerate(self.projects):
            proj_file = ws_dir / f"{proj.name.replace(' ', '_')}_{i}.qgz"
            
            if i == self.current_index:
                self.project.write(str(proj_file))
            else:
                shutil.copy(proj.temp_file, str(proj_file))
            
            proj_data = proj.to_dict()
            proj_data['workspace_file'] = str(proj_file)
            workspace['projects'].append(proj_data)
        
        with open(file_path, 'w') as f:
            json.dump(workspace, f, indent=2)
        
        self.iface.messageBar().pushMessage(
            "Multi Project", f"{tr('Workspace saved')}: {file_path}", Qgis.Success, 3
        )
    
    def load_workspace(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, tr("Load workspace"), "",
            "Multi Project Workspace (*.mpw)"
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'r') as f:
                workspace = json.load(f)
        except Exception as e:
            QMessageBox.critical(self, tr("Error"), f"{tr('Cannot load')}:\n{e}")
            return
        
        for proj in self.projects:
            proj.cleanup()
        self.projects.clear()
        
        for proj_data in workspace.get('projects', []):
            name = proj_data.get('name', tr('Project'))
            proj = ProjectTab(name, self.temp_dir)
            proj.from_dict(proj_data)
            
            source = proj_data.get('workspace_file')
            if source and os.path.exists(source):
                shutil.copy(source, proj.temp_file)
            
            self.projects.append(proj)
        
        current = workspace.get('current', 0)
        if current >= len(self.projects):
            current = 0
        
        self.current_index = current
        self._switching = True
        if self.projects:
            self.projects[current].restore_state(self.project, self.canvas, self.iface)
            self.bookmark_widget.set_project(self.projects[current])
        self._switching = False
        
        self._refresh_list()
        self._update_nav_buttons()
        
        self.iface.messageBar().pushMessage(
            "Multi Project", f"{tr('Workspace loaded')}: {file_path}", Qgis.Success, 3
        )
    
    def cleanup(self):
        for proj in self.projects:
            proj.cleanup()
        
        try:
            shutil.rmtree(self.temp_dir)
        except:
            pass


class MultiProjectCanvasPlugin:
    """Main plugin class v7 with i18n"""
    
    def __init__(self, iface):
        self.iface = iface
        self.dock = None
        self.action = None
    
    def initGui(self):
        self.action = QAction(
            QgsApplication.getThemeIcon("/mActionNewMap.svg"),
            tr("Multi Project Panel"),
            self.iface.mainWindow()
        )
        self.action.setCheckable(True)
        self.action.setToolTip(tr("Multi-Project Panel") + " (Ctrl+Shift+P)")
        self.action.setShortcut("Ctrl+Shift+P")
        self.action.triggered.connect(self.toggle)
        
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu("Multi Project Canvas", self.action)
    
    def unload(self):
        if self.dock:
            self.deactivate()
        
        self.iface.removeToolBarIcon(self.action)
        self.iface.removePluginMenu("Multi Project Canvas", self.action)
    
    def toggle(self, checked):
        if checked:
            self.activate()
        else:
            self.deactivate()
    
    def activate(self):
        if self.dock:
            return
        
        self.dock = MultiProjectDock(self.iface, self.iface.mainWindow())
        self.dock.visibilityChanged.connect(self._on_visibility_changed)
        
        self.iface.addDockWidget(Qt.LeftDockWidgetArea, self.dock)
        
        self.iface.messageBar().pushMessage(
            "Multi Project",
            tr("Panel activated. Ctrl+T for new project."),
            Qgis.Info, 3
        )
    
    def deactivate(self):
        if not self.dock:
            return
        
        has_modified = any(p.is_modified for p in self.dock.projects)
        if has_modified:
            reply = QMessageBox.question(
                self.iface.mainWindow(),
                tr("Confirm"),
                tr("There are unsaved projects. Close anyway?"),
                QMessageBox.Yes | QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                self.action.setChecked(True)
                return
        
        self.dock.cleanup()
        self.iface.removeDockWidget(self.dock)
        self.dock.deleteLater()
        self.dock = None
    
    def _on_visibility_changed(self, visible):
        self.action.setChecked(visible)
