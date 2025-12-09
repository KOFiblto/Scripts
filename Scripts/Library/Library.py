#!/usr/bin/env python3
"""
library_reader_win11.py

Windows 11 Fluent Design Library Reader:
 - Acrylic/frosted glass effects with transparency
 - Rounded corners throughout
 - Subtle gradients and shadows
 - Modern color palette with light/dark theming
 - Smooth hover animations
 - All original functionality preserved
"""

import sys
import json
from pathlib import Path
from functools import partial

from PySide6.QtCore import (
    Qt,
    QSize,
    QUrl,
    Signal,
    QObject,
    QRunnable,
    QThreadPool,
    QPoint,
    QPropertyAnimation,
    QEasingCurve,
    Property,
)
from PySide6.QtGui import (
    QPixmap,
    QImage,
    QImageReader,
    QCursor,
    QIcon,
    QPainter,
    QPolygon,
    QColor,
    QFont,
    QPalette,
    QLinearGradient,
    QPen,
)
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTreeView,
    QFileSystemModel,
    QSplitter,
    QListWidget,
    QListWidgetItem,
    QFileDialog,
    QMessageBox,
    QToolBar,
    QPushButton,
    QScrollArea,
    QGridLayout,
    QSizePolicy,
    QFrame,
    QStyle,
    QSlider,
    QGraphicsOpacityEffect,
)

# Multimedia
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget

# ----------------------------
# Config & utilities
# ----------------------------
APP_DIR = Path(__file__).parent
CONFIG_PATH = APP_DIR / "config.json"
DEFAULT_CONFIG = {"roots": []}

TILE_SIZE = 200
THUMB_SIZE = QSize(TILE_SIZE, TILE_SIZE)

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp", ".tiff", ".tif"}
VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".avi", ".webm", ".wmv"}


def load_config():
    if CONFIG_PATH.exists():
        try:
            return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    save_config(DEFAULT_CONFIG)
    return DEFAULT_CONFIG


def save_config(cfg):
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2), encoding="utf-8")


def list_subdirs(path: Path):
    try:
        return sorted([p for p in path.iterdir() if p.is_dir()], key=lambda p: p.name.lower())
    except Exception:
        return []


def list_media_files(path: Path):
    try:
        files = [p for p in path.iterdir() if p.is_file() and (is_image(p) or is_video(p))]
        return sorted(files, key=lambda p: p.name.lower())
    except Exception:
        return []


def is_image(p: Path):
    return p.suffix.lower() in IMAGE_EXTS


def is_video(p: Path):
    return p.suffix.lower() in VIDEO_EXTS


# ----------------------------
# Asynchronous thumbnail loader
# ----------------------------
class ThumbnailSignal(QObject):
    ready = Signal(str, object, bool)


class ThumbnailWorker(QRunnable):
    def __init__(self, path: Path, size: QSize, sig: ThumbnailSignal):
        super().__init__()
        self.path = Path(path)
        self.size = size
        self.sig = sig

    def run(self):
        p = self.path
        if is_image(p):
            reader = QImageReader(str(p))
            reader.setAutoTransform(True)
            try:
                reader.setScaledSize(self.size)
            except Exception:
                pass
            img = reader.read()
            self.sig.ready.emit(str(p), img if (img is not None and not img.isNull()) else None, False)
            return
        if is_video(p):
            self.sig.ready.emit(str(p), None, True)
            return
        self.sig.ready.emit(str(p), None, False)


# ----------------------------
# Modern Windows 11 Button
# ----------------------------
class ModernButton(QPushButton):
    def __init__(self, text="", icon_name=None, parent=None):
        super().__init__(text, parent)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setStyleSheet(self._style())
        
    def _style(self):
        return """
        QPushButton {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(255, 255, 255, 0.08),
                stop:1 rgba(255, 255, 255, 0.04));
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 6px;
            padding: 8px 16px;
            color: #FFFFFF;
            font-size: 10pt;
            font-weight: 500;
            min-height: 32px;
        }
        QPushButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(255, 255, 255, 0.12),
                stop:1 rgba(255, 255, 255, 0.08));
            border: 1px solid rgba(255, 255, 255, 0.18);
        }
        QPushButton:pressed {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(255, 255, 255, 0.04),
                stop:1 rgba(255, 255, 255, 0.02));
            border: 1px solid rgba(255, 255, 255, 0.08);
        }
        """


# ----------------------------
# Sidebar
# ----------------------------
class Sidebar(QWidget):
    folder_selected = Signal(Path)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.cfg = load_config()
        root_v = QVBoxLayout(self)
        root_v.setContentsMargins(16, 16, 16, 16)
        root_v.setSpacing(12)
        self.setFixedWidth(320)
        self.setStyleSheet(self._style())

        # Title
        title = QLabel("Library")
        title.setStyleSheet("""
            font-size: 18pt;
            font-weight: 600;
            color: #FFFFFF;
            padding: 8px 0px;
        """)
        root_v.addWidget(title)

        # Control buttons
        ctrl_row = QHBoxLayout()
        ctrl_row.setSpacing(8)
        self.back_btn = ModernButton("← Back")
        self.add_btn = ModernButton("+ Add")
        self.rem_btn = ModernButton("− Remove")
        ctrl_row.addWidget(self.back_btn)
        ctrl_row.addWidget(self.add_btn)
        ctrl_row.addWidget(self.rem_btn)
        root_v.addLayout(ctrl_row)

        # Roots section
        roots_label = QLabel("ROOT FOLDERS")
        roots_label.setStyleSheet("""
            font-size: 9pt;
            font-weight: 600;
            color: rgba(255, 255, 255, 0.6);
            letter-spacing: 0.5px;
            padding: 12px 0px 4px 0px;
        """)
        root_v.addWidget(roots_label)

        self.root_list = QListWidget()
        self.root_list.setFixedHeight(120)
        self.root_list.setStyleSheet("""
            QListWidget {
                background: rgba(255, 255, 255, 0.03);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 8px;
                padding: 8px;
                font-size: 10pt;
                color: #FFFFFF;
            }
            QListWidget::item {
                padding: 8px;
                border-radius: 4px;
                margin: 2px 0px;
            }
            QListWidget::item:hover {
                background: rgba(255, 255, 255, 0.08);
            }
            QListWidget::item:selected {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(0, 120, 215, 0.8),
                    stop:1 rgba(0, 103, 192, 0.8));
                border: none;
            }
        """)
        self.root_list.itemClicked.connect(self.on_root_clicked)
        root_v.addWidget(self.root_list)

        # File tree section
        tree_label = QLabel("NAVIGATION")
        tree_label.setStyleSheet("""
            font-size: 9pt;
            font-weight: 600;
            color: rgba(255, 255, 255, 0.6);
            letter-spacing: 0.5px;
            padding: 12px 0px 4px 0px;
        """)
        root_v.addWidget(tree_label)

        self.tree = QTreeView()
        self.tree.setHeaderHidden(True)
        self.tree.setStyleSheet("""
            QTreeView {
                background: rgba(255, 255, 255, 0.03);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 8px;
                padding: 8px;
                font-size: 10pt;
                color: #FFFFFF;
            }
            QTreeView::item {
                padding: 6px;
                border-radius: 4px;
            }
            QTreeView::item:hover {
                background: rgba(255, 255, 255, 0.08);
            }
            QTreeView::item:selected {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(0, 120, 215, 0.8),
                    stop:1 rgba(0, 103, 192, 0.8));
            }
            QTreeView::branch {
                background: transparent;
            }
        """)
        self.model = QFileSystemModel(self.tree)
        self.model.setReadOnly(True)
        root_v.addWidget(self.tree)

        self.add_btn.clicked.connect(self.add_root)
        self.rem_btn.clicked.connect(self.remove_root)
        self.populate_roots()
        self.tree.clicked.connect(self.on_tree_clicked)
        self.back_btn.clicked.connect(self.on_back_clicked)

    def _style(self):
        return """
        QWidget {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(20, 28, 45, 0.95),
                stop:1 rgba(12, 18, 32, 0.98));
            border-right: 1px solid rgba(255, 255, 255, 0.08);
        }
        """

    def populate_roots(self):
        self.root_list.clear()
        for r in self.cfg.get("roots", []):
            item = QListWidgetItem(str(r))
            self.root_list.addItem(item)

    def add_root(self):
        folder = QFileDialog.getExistingDirectory(self, "Select root folder", str(Path.home()))
        if folder:
            p = Path(folder)
            if str(p) in self.cfg["roots"]:
                QMessageBox.information(self, "Already added", f"{p} is already a root.")
                return
            self.cfg["roots"].append(str(p))
            save_config(self.cfg)
            self.populate_roots()

    def remove_root(self):
        cur = self.root_list.currentItem()
        if not cur:
            QMessageBox.information(self, "Select root", "Choose a root to remove.")
            return
        path = cur.text()
        if QMessageBox.question(self, "Remove root", f"Remove root {path}?") == QMessageBox.Yes:
            self.cfg["roots"] = [r for r in self.cfg["roots"] if r != path]
            save_config(self.cfg)
            self.populate_roots()
            self.tree.setModel(None)

    def apply_root(self, path: Path):
        self.model.setRootPath(str(path))
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(str(path)))
        for col in range(1, self.model.columnCount()):
            self.tree.hideColumn(col)
        self.tree.expand(self.model.index(str(path)))

    def on_root_clicked(self, item: QListWidgetItem):
        self.apply_root(Path(item.text()))

    def on_tree_clicked(self, idx):
        p = Path(self.model.filePath(idx))
        self.folder_selected.emit(p)

    def on_back_clicked(self):
        self.folder_selected.emit(Path(""))


# ----------------------------
# Modern Tile Widgets
# ----------------------------
class ThumbnailTile(QFrame):
    clicked = Signal()

    def __init__(self, path: Path, fixed_size: int = TILE_SIZE, parent=None):
        super().__init__(parent)
        self.path = Path(path)
        self.setFixedSize(fixed_size, fixed_size + 50)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setStyleSheet(self._style())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Thumbnail container with rounded corners
        thumb_container = QFrame()
        thumb_container.setStyleSheet("""
            QFrame {
                background: rgba(0, 0, 0, 0.2);
                border-radius: 12px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
        """)
        thumb_layout = QVBoxLayout(thumb_container)
        thumb_layout.setContentsMargins(0, 0, 0, 0)
        
        self.thumb_label = QLabel()
        inner = fixed_size - 32
        self.thumb_label.setFixedSize(inner, inner)
        self.thumb_label.setAlignment(Qt.AlignCenter)
        self.thumb_label.setScaledContents(False)
        thumb_layout.addWidget(self.thumb_label, alignment=Qt.AlignCenter)
        
        layout.addWidget(thumb_container)

        self.title = QLabel(self.path.name)
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setWordWrap(True)
        self.title.setFixedHeight(40)
        self.title.setStyleSheet("""
            font-size: 9pt;
            font-weight: 500;
            color: rgba(255, 255, 255, 0.9);
        """)
        layout.addWidget(self.title)

    def mouseReleaseEvent(self, ev):
        if ev.button() == Qt.LeftButton:
            self.clicked.emit()

    def set_thumbnail(self, pixmap: QPixmap):
        if pixmap is None or pixmap.isNull():
            icon = QApplication.style().standardIcon(QStyle.SP_FileIcon)
            fallback = icon.pixmap(THUMB_SIZE)
            self._set_pixmap_centered(fallback)
            return
        self._set_pixmap_centered(pixmap)

    def _set_pixmap_centered(self, pixmap: QPixmap):
        label_size = self.thumb_label.size()
        pm = pixmap.scaled(label_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.thumb_label.setPixmap(pm)

    def _style(self):
        return """
        QFrame {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(255, 255, 255, 0.05),
                stop:1 rgba(255, 255, 255, 0.02));
            border-radius: 16px;
            border: 1px solid rgba(255, 255, 255, 0.08);
        }
        QFrame:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(255, 255, 255, 0.08),
                stop:1 rgba(255, 255, 255, 0.04));
            border: 1px solid rgba(255, 255, 255, 0.15);
        }
        """


class FolderTile(QPushButton):
    clicked = Signal()

    def __init__(self, path: Path, has_media: bool = False, fixed_size: int = TILE_SIZE, parent=None):
        super().__init__(parent)
        self.path = Path(path)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setFixedSize(fixed_size, fixed_size + 50)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setStyleSheet(self._style())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        thumb_container = QFrame()
        thumb_container.setStyleSheet("""
            QFrame {
                background: rgba(0, 120, 215, 0.15);
                border-radius: 12px;
                border: 1px solid rgba(0, 120, 215, 0.3);
            }
        """)
        thumb_layout = QVBoxLayout(thumb_container)
        thumb_layout.setContentsMargins(0, 0, 0, 0)

        self.thumb_label = QLabel()
        inner = fixed_size - 32
        self.thumb_label.setFixedSize(inner, inner)
        self.thumb_label.setAlignment(Qt.AlignCenter)
        self.thumb_label.setScaledContents(False)
        thumb_layout.addWidget(self.thumb_label, alignment=Qt.AlignCenter)
        
        layout.addWidget(thumb_container)

        self.title = QLabel(self.path.name)
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setWordWrap(True)
        self.title.setFixedHeight(40)
        self.title.setStyleSheet("""
            font-size: 9pt;
            font-weight: 500;
            color: rgba(255, 255, 255, 0.9);
        """)
        layout.addWidget(self.title)

        if not has_media:
            icon = QApplication.style().standardIcon(QStyle.SP_DirIcon)
            icon_pix = icon.pixmap(THUMB_SIZE)
            self.set_thumbnail(icon_pix)

    def set_thumbnail(self, pixmap: QPixmap):
        if pixmap is None or pixmap.isNull():
            icon = QApplication.style().standardIcon(QStyle.SP_DirIcon)
            fallback = icon.pixmap(THUMB_SIZE)
            self._set_pixmap_centered(fallback)
            return
        self._set_pixmap_centered(pixmap)

    def _set_pixmap_centered(self, pixmap: QPixmap):
        label_size = self.thumb_label.size()
        pm = pixmap.scaled(label_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.thumb_label.setPixmap(pm)

    def _style(self):
        return """
        QPushButton {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(255, 255, 255, 0.05),
                stop:1 rgba(255, 255, 255, 0.02));
            border-radius: 16px;
            border: 1px solid rgba(255, 255, 255, 0.08);
            text-align: center;
        }
        QPushButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(0, 120, 215, 0.2),
                stop:1 rgba(0, 103, 192, 0.15));
            border: 1px solid rgba(0, 120, 215, 0.4);
        }
        """


# ----------------------------
# Gallery
# ----------------------------
class Gallery(QWidget):
    folder_open_requested = Signal(Path)
    media_open_requested = Signal(list, int)

    def __init__(self, thumb_signal: ThumbnailSignal, parent=None):
        super().__init__(parent)
        self.thumb_signal = thumb_signal
        self.thumb_signal.ready.connect(self.on_thumb_ready)
        self.threadpool = QThreadPool.globalInstance()
        self.thumb_cache = {}
        self.waiting_widgets = {}
        self._submitted = set()

        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 24, 24, 24)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: rgba(255, 255, 255, 0.03);
                width: 12px;
                border-radius: 6px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 0.15);
                border-radius: 6px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(255, 255, 255, 0.25);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        self.container = QWidget()
        self.grid = QGridLayout(self.container)
        self.grid.setContentsMargins(8, 8, 8, 8)
        self.grid.setSpacing(18)
        self.container.setLayout(self.grid)
        self.scroll.setWidget(self.container)

        outer.addWidget(self.scroll)
        self.current_path = None

    def clear_grid(self):
        while self.grid.count():
            it = self.grid.takeAt(0)
            w = it.widget()
            if w:
                w.deleteLater()

    def show_roots(self, roots):
        self.clear_grid()
        cols = 4
        row = col = 0
        for root in roots:
            p = Path(root)
            tile = FolderTile(p, has_media=False)
            tile.clicked.connect(lambda checked=False, rp=p: self.folder_open_requested.emit(rp))
            self.grid.addWidget(tile, row, col)
            col += 1
            if col >= cols:
                col = 0
                row += 1

    def show_folder_contents(self, path: Path):
        self.current_path = path
        subdirs = list_subdirs(path)
        media = list_media_files(path)
        self.clear_grid()
        row = col = 0
        cols = 4
        
        if subdirs:
            for d in subdirs:
                sub_media = list_media_files(d)
                has_media_direct = len(sub_media) > 0
                tile = FolderTile(d, has_media=has_media_direct)
                tile.clicked.connect(lambda checked=False, p=d: self.folder_open_requested.emit(p))
                if has_media_direct:
                    first_media = sub_media[0]
                    self.request_thumbnail_for_path(first_media, tile)
                self.grid.addWidget(tile, row, col)
                col += 1
                if col >= cols:
                    col = 0
                    row += 1
                    
        if media:
            if subdirs and col != 0:
                row += 1
                col = 0
            for idx, m in enumerate(media):
                tile = ThumbnailTile(m)
                tile.clicked.connect(partial(self._on_media_clicked, media, idx))
                self.request_thumbnail_for_path(m, tile)
                self.grid.addWidget(tile, row, col)
                col += 1
                if col >= cols:
                    col = 0
                    row += 1

        if not subdirs and not media:
            lbl = QLabel("Empty folder")
            lbl.setStyleSheet("font-size: 12pt; color: rgba(255, 255, 255, 0.5);")
            self.grid.addWidget(lbl, 0, 0)

    def _on_media_clicked(self, media_list, idx):
        self.media_open_requested.emit(media_list, idx)

    def request_thumbnail_for_path(self, path: Path, widget):
        key = str(path)
        if key in self.thumb_cache:
            widget.set_thumbnail(self.thumb_cache[key])
            return
        self.waiting_widgets.setdefault(key, []).append(widget)
        if key in self._submitted:
            return
        self._submitted.add(key)
        worker = ThumbnailWorker(path, THUMB_SIZE, self.thumb_signal)
        self.threadpool.start(worker)

    def on_thumb_ready(self, path_str: str, qimage_obj, is_video: bool):
        key = path_str
        pix = None
        if qimage_obj and isinstance(qimage_obj, QImage) and not qimage_obj.isNull():
            pix = QPixmap.fromImage(qimage_obj)
        else:
            if is_video:
                icon = QApplication.style().standardIcon(QStyle.SP_FileIcon)
                base = icon.pixmap(THUMB_SIZE)
                p = QPixmap(base)
                painter = QPainter()
                try:
                    painter.begin(p)
                    painter.setRenderHint(QPainter.Antialiasing)
                    size = min(p.width(), p.height())
                    tri_size = int(size * 0.26)
                    cx = p.width() // 2
                    cy = p.height() // 2
                    poly = QPolygon()
                    poly.append(QPoint(cx - tri_size // 2, cy - tri_size))
                    poly.append(QPoint(cx - tri_size // 2, cy + tri_size))
                    poly.append(QPoint(cx + tri_size, cy))
                    painter.setBrush(QColor(255, 255, 255, 220))
                    painter.setPen(Qt.NoPen)
                    painter.drawPolygon(poly)
                except Exception:
                    pass
                finally:
                    painter.end()
                pix = p
            else:
                icon = QApplication.style().standardIcon(QStyle.SP_FileIcon)
                pix = icon.pixmap(THUMB_SIZE)
        self.thumb_cache[key] = pix
        widgets = self.waiting_widgets.pop(key, [])
        for w in widgets:
            try:
                w.set_thumbnail(pix)
            except Exception:
                pass


# ----------------------------
# Viewer Widget
# ----------------------------
class ViewerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(self._style())

        v = QVBoxLayout(self)
        v.setContentsMargins(24, 24, 24, 24)
        v.setSpacing(12)

        # Top control bar with modern styling
        top_bar = QFrame()
        top_bar.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255, 255, 255, 0.08),
                    stop:1 rgba(255, 255, 255, 0.04));
                border-radius: 12px;
                border: 1px solid rgba(255, 255, 255, 0.1);
                padding: 8px;
            }
        """)
        top = QHBoxLayout(top_bar)
        top.setContentsMargins(8, 8, 8, 8)
        top.setSpacing(8)
        
        self.prev_btn = ModernButton("◀ Previous")
        self.next_btn = ModernButton("Next ▶")
        self.close_btn = ModernButton("✕ Close")
        self.close_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(232, 17, 35, 0.8),
                    stop:1 rgba(194, 14, 29, 0.8));
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 6px;
                padding: 8px 16px;
                color: #FFFFFF;
                font-size: 10pt;
                font-weight: 500;
                min-height: 32px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(250, 40, 55, 0.9),
                    stop:1 rgba(210, 20, 35, 0.9));
            }
        """)
        
        top.addWidget(self.prev_btn)
        top.addWidget(self.next_btn)
        top.addStretch()
        top.addWidget(self.close_btn)
        v.addWidget(top_bar)

        # Viewer area
        self.viewer_area = QWidget()
        self.viewer_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.viewer_area.setStyleSheet("""
            QWidget {
                background: rgba(0, 0, 0, 0.3);
                border-radius: 12px;
                border: 1px solid rgba(255, 255, 255, 0.08);
            }
        """)
        self.viewer_area_layout = QVBoxLayout(self.viewer_area)
        self.viewer_area_layout.setContentsMargins(0, 0, 0, 0)
        self.viewer_area_layout.setSpacing(0)
        v.addWidget(self.viewer_area)

        # Image viewer
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
        """)
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setScaledContents(False)
        self.scroll.setWidget(self.image_label)

        # Video
        self.video_widget = QVideoWidget()
        self.player = QMediaPlayer(self)
        self.audio = QAudioOutput(self)
        self.player.setAudioOutput(self.audio)
        self.player.setVideoOutput(self.video_widget)
        
        self.video_controls = QHBoxLayout()
        self.play_btn = ModernButton("▶ Play")
        self.play_btn.clicked.connect(self.toggle_play)
        self.video_slider = QSlider(Qt.Horizontal)
        self.video_slider.setRange(0, 1000)
        self.video_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                background: rgba(255, 255, 255, 0.1);
                height: 6px;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(0, 120, 215, 1),
                    stop:1 rgba(0, 103, 192, 1));
                width: 16px;
                height: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }
            QSlider::sub-page:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(0, 120, 215, 0.8),
                    stop:1 rgba(0, 103, 192, 0.8));
                border-radius: 3px;
            }
        """)
        self.video_controls.addWidget(self.play_btn)
        self.video_controls.addWidget(self.video_slider)
        self.player.positionChanged.connect(self._on_pos_changed)
        self.player.durationChanged.connect(self._on_dur_changed)
        self.video_slider.sliderMoved.connect(self._on_slider_moved)

        # State
        self.media_list = []
        self.index = 0
        self.current_pixmap_original = None
        self.current_media_is_image = False
        self.zoom = 1.0

        self.prev_btn.clicked.connect(self.prev_item)
        self.next_btn.clicked.connect(self.next_item)
        self.close_btn.clicked.connect(self.on_close)

    def _style(self):
        return """
        QWidget {
            background: transparent;
            color: #FFFFFF;
        }
        """

    def open_media_list(self, media_list, start_index=0):
        self.media_list = media_list[:]
        self.index = int(start_index) % max(1, len(self.media_list))
        self.zoom = 1.0
        self.show_current_media()

    def show_current_media(self):
        while self.viewer_area_layout.count():
            it = self.viewer_area_layout.takeAt(0)
            w = it.widget()
            if w:
                w.setParent(None)

        if not self.media_list:
            lbl = QLabel("No media")
            lbl.setStyleSheet("color: rgba(255, 255, 255, 0.5); font-size: 12pt;")
            self.viewer_area_layout.addWidget(lbl)
            return

        path = Path(self.media_list[self.index])
        if is_image(path):
            try:
                if self.player.playbackState() == QMediaPlayer.PlayingState:
                    self.player.stop()
                    self.play_btn.setText("▶ Play")
            except Exception:
                pass
            pix = QPixmap(str(path))
            if pix.isNull():
                lbl = QLabel("Failed to load image")
                lbl.setStyleSheet("color: rgba(255, 255, 255, 0.5); font-size: 12pt;")
                self.viewer_area_layout.addWidget(lbl)
                return
            self.current_pixmap_original = pix
            self.current_media_is_image = True
            self._update_image_display(fit=True)
            self.viewer_area_layout.addWidget(self.scroll)
        elif is_video(path):
            self.current_media_is_image = False
            try:
                self.player.setSource(QUrl.fromLocalFile(str(path)))
            except Exception:
                try:
                    self.player.setSource(QUrl.fromLocalFile(str(path)))
                except Exception:
                    pass
            self.player.pause()
            self.play_btn.setText("▶ Play")
            self.video_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            self.viewer_area_layout.addWidget(self.video_widget, stretch=1)
            controls_container = QWidget()
            controls_container.setStyleSheet("""
                QWidget {
                    background: rgba(0, 0, 0, 0.5);
                    border-radius: 8px;
                    padding: 8px;
                }
            """)
            controls_layout = QHBoxLayout(controls_container)
            controls_layout.setContentsMargins(8, 8, 8, 8)
            controls_layout.addWidget(self.play_btn)
            controls_layout.addWidget(self.video_slider)
            self.viewer_area_layout.addWidget(controls_container)
        else:
            lbl = QLabel("Unsupported media type")
            lbl.setStyleSheet("color: rgba(255, 255, 255, 0.5); font-size: 12pt;")
            self.viewer_area_layout.addWidget(lbl)

    def _update_image_display(self, fit=False):
        if not self.current_pixmap_original or self.current_pixmap_original.isNull():
            return
        avail = self.viewer_area.size()
        avail_w = max(10, avail.width())
        avail_h = max(10, avail.height())
        if fit:
            scaled = self.current_pixmap_original.scaled(avail_w, avail_h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.zoom = 1.0
            self.image_label.setPixmap(scaled)
        else:
            base = self.current_pixmap_original.scaled(avail_w, avail_h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            target_w = max(1, int(base.width() * self.zoom))
            target_h = max(1, int(base.height() * self.zoom))
            scaled = base.scaled(target_w, target_h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.image_label.setPixmap(scaled)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.current_media_is_image and self.current_pixmap_original:
            if abs(self.zoom - 1.0) < 1e-6:
                self._update_image_display(fit=True)
            else:
                self._update_image_display(fit=False)

    def toggle_play(self):
        st = self.player.playbackState()
        if st == QMediaPlayer.PlayingState:
            self.player.pause()
            self.play_btn.setText("▶ Play")
        else:
            self.player.play()
            self.play_btn.setText("⏸ Pause")

    def _on_pos_changed(self, pos):
        dur = self.player.duration()
        if dur > 0:
            v = int(pos * 1000 / dur)
            self.video_slider.blockSignals(True)
            self.video_slider.setValue(v)
            self.video_slider.blockSignals(False)

    def _on_dur_changed(self, dur):
        pass

    def _on_slider_moved(self, value):
        dur = self.player.duration()
        if dur > 0:
            pos = int(value / 1000 * dur)
            self.player.setPosition(pos)

    def next_item(self):
        if not self.media_list:
            return
        self.index = (self.index + 1) % len(self.media_list)
        self.zoom = 1.0
        self.show_current_media()

    def prev_item(self):
        if not self.media_list:
            return
        self.index = (self.index - 1) % len(self.media_list)
        self.zoom = 1.0
        self.show_current_media()

    def on_close(self):
        self.setVisible(False)

    def key_press(self, event):
        if event.key() == Qt.Key_Escape:
            self.on_close()
        elif event.key() in (Qt.Key_Right, Qt.Key_D):
            self.next_item()
        elif event.key() in (Qt.Key_Left, Qt.Key_A):
            self.prev_item()

    def wheelEvent(self, event):
        modifiers = QApplication.keyboardModifiers()
        if self.current_media_is_image and (modifiers & Qt.ControlModifier):
            delta = event.angleDelta().y()
            if delta > 0:
                factor = 1.15
            else:
                factor = 1 / 1.15
            self.zoom = max(0.1, min(10.0, self.zoom * factor))
            self._update_image_display(fit=False)
            event.accept()
        else:
            super().wheelEvent(event)


# ----------------------------
# Main Window
# ----------------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Library Reader")
        self.setMinimumSize(1200, 800)
        
        # Windows 11 style window with acrylic background
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(10, 18, 35, 1),
                    stop:0.5 rgba(15, 25, 45, 1),
                    stop:1 rgba(10, 18, 35, 1));
            }
            QMessageBox {
                background: rgba(32, 32, 32, 0.95);
                color: #FFFFFF;
            }
            QMessageBox QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(0, 120, 215, 0.8),
                    stop:1 rgba(0, 103, 192, 0.8));
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 6px;
                padding: 8px 16px;
                color: #FFFFFF;
                min-width: 80px;
            }
        """)

        central = QWidget()
        self.setCentralWidget(central)
        h = QHBoxLayout(central)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(0)

        self.sidebar = Sidebar()
        h.addWidget(self.sidebar)

        right_container = QWidget()
        right_container.setStyleSheet("""
            QWidget {
                background: transparent;
            }
        """)
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        h.addWidget(right_container, stretch=1)

        self.thumb_signal = ThumbnailSignal()
        self.gallery = Gallery(self.thumb_signal)
        right_layout.addWidget(self.gallery)

        self.viewer = ViewerWidget()
        self.viewer.setVisible(False)
        right_layout.addWidget(self.viewer)

        self.sidebar.folder_selected.connect(self.on_sidebar_folder_selected)
        self.gallery.folder_open_requested.connect(self.on_folder_selected)
        self.gallery.media_open_requested.connect(self.open_viewer)
        self.viewer.close_btn.clicked.connect(self.close_viewer)

        self.history = []
        self.current = None

        cfg = load_config()
        self.show_roots_view(cfg.get("roots", []))

        self.sidebar.add_btn.clicked.connect(self.sidebar.add_root)
        self.sidebar.rem_btn.clicked.connect(self.sidebar.remove_root)
        self.sidebar.back_btn.clicked.connect(self.go_back_top)

    def show_roots_view(self, roots):
        self.gallery.setVisible(True)
        self.viewer.setVisible(False)
        self.gallery.show_roots(roots)
        self.history.clear()
        self.current = None
        self.sidebar.tree.setModel(None)
        self.sidebar.populate_roots()

    def on_sidebar_folder_selected(self, path: Path):
        if not path or str(path) == "":
            self.go_back_top()
            return
        self.on_folder_selected(path)

    def on_folder_selected(self, path: Path):
        if self.current:
            self.history.append(self.current)
        self.current = path
        cfg = load_config()
        applied = False
        for r in cfg.get("roots", []):
            rp = Path(r)
            try:
                if rp in path.parents or rp == path:
                    self.sidebar.apply_root(rp)
                    applied = True
                    break
            except Exception:
                continue
        self.viewer.setVisible(False)
        self.gallery.setVisible(True)
        self.gallery.show_folder_contents(path)

    def go_back_top(self):
        cfg = load_config()
        self.show_roots_view(cfg.get("roots", []))

    def open_viewer(self, media_list, index):
        self.viewer.open_media_list([str(m) for m in media_list], index)
        self.viewer.setVisible(True)
        self.gallery.setVisible(False)

    def close_viewer(self):
        self.viewer.setVisible(False)
        self.gallery.setVisible(True)

    def keyPressEvent(self, event):
        if self.viewer.isVisible():
            self.viewer.key_press(event)
        else:
            super().keyPressEvent(event)


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # Set Windows 11 dark palette
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(32, 32, 32))
    palette.setColor(QPalette.WindowText, QColor(255, 255, 255))
    palette.setColor(QPalette.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.AlternateBase, QColor(45, 45, 45))
    palette.setColor(QPalette.Text, QColor(255, 255, 255))
    palette.setColor(QPalette.Button, QColor(45, 45, 45))
    palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))
    palette.setColor(QPalette.Highlight, QColor(0, 120, 215))
    palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
    app.setPalette(palette)
    
    mw = MainWindow()
    mw.show()
    
    cfg = load_config()
    if not cfg.get("roots"):
        msg = QMessageBox(mw)
        msg.setWindowTitle("Welcome")
        msg.setText("No root folders configured.\n\nUse the '+ Add' button in the sidebar to add folders.")
        msg.setIcon(QMessageBox.Information)
        msg.exec()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()