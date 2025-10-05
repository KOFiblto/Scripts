#!/usr/bin/env python3
"""
library_reader_final.py

Modernized Library Reader:
 - Sidebar-only layout (Back / Add Root / Remove Root + file tree)
 - Cleaner styles, larger text, slightly smaller thumbs
 - Thumbnails preserve aspect ratio inside square tiles (no stretching)
 - Folder tiles show first direct media as thumbnail (or folder icon)
 - Embedded viewer maximizes content and supports Ctrl + mouse wheel zoom
 - Fixed QPolygon/QPainter usage for video-placeholder drawing
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

# Make tiles slightly smaller than before, as requested
TILE_SIZE = 200  # square tile size (visual region)
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
    # path_str, qimage (or None), is_video (bool)
    ready = Signal(str, object, bool)


class ThumbnailWorker(QRunnable):
    """Background worker that loads/scales a QImage (safe to create in worker thread)."""

    def __init__(self, path: Path, size: QSize, sig: ThumbnailSignal):
        super().__init__()
        self.path = Path(path)
        self.size = size
        self.sig = sig

    def run(self):
        p = self.path
        # If image: load and scale as QImage
        if is_image(p):
            reader = QImageReader(str(p))
            reader.setAutoTransform(True)
            # request scaled size (reader may ignore if not supported)
            try:
                reader.setScaledSize(self.size)
            except Exception:
                pass
            img = reader.read()
            # emit image (possibly null QImage)
            self.sig.ready.emit(str(p), img if (img is not None and not img.isNull()) else None, False)
            return
        # If video: cannot extract frame here (no ffmpeg frame extraction in worker); signal video placeholder
        if is_video(p):
            self.sig.ready.emit(str(p), None, True)
            return
        # fallback: generic
        self.sig.ready.emit(str(p), None, False)


# ----------------------------
# Sidebar
# ----------------------------
class Sidebar(QWidget):
    folder_selected = Signal(Path)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.cfg = load_config()
        root_v = QVBoxLayout(self)
        root_v.setContentsMargins(10, 10, 10, 10)
        root_v.setSpacing(10)
        self.setFixedWidth(300)
        self.setStyleSheet(self._style())

        # top controls: Back / Add / Remove
        ctrl_row = QHBoxLayout()
        self.back_btn = QPushButton("Back")
        self.back_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.add_btn = QPushButton("Add Root")
        self.add_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.rem_btn = QPushButton("Remove Root")
        self.rem_btn.setCursor(QCursor(Qt.PointingHandCursor))
        ctrl_row.addWidget(self.back_btn)
        ctrl_row.addWidget(self.add_btn)
        ctrl_row.addWidget(self.rem_btn)
        root_v.addLayout(ctrl_row)

        # configured roots list (compact)
        self.root_list = QListWidget()
        self.root_list.setFixedHeight(100)
        self.root_list.setStyleSheet("QListWidget { font-size: 12pt; }")
        self.root_list.itemClicked.connect(self.on_root_clicked)
        root_v.addWidget(self.root_list)

        # file tree
        self.tree = QTreeView()
        self.tree.setHeaderHidden(True)
        self.model = QFileSystemModel(self.tree)
        self.model.setReadOnly(True)
        root_v.addWidget(self.tree)

        # hookups
        self.add_btn.clicked.connect(self.add_root)
        self.rem_btn.clicked.connect(self.remove_root)
        self.populate_roots()
        self.tree.clicked.connect(self.on_tree_clicked)
        self.back_btn.clicked.connect(self.on_back_clicked)

    def _style(self):
        return """
        QWidget { background: #071126; color: #e6eef8; }
        QPushButton {
            background: rgba(255,255,255,0.03);
            padding: 6px 8px;
            border-radius: 8px;
            font-weight: 600;
        }
        QPushButton:hover { background: rgba(255,255,255,0.05); }
        QLabel { font-size: 10pt; }
        """

    def populate_roots(self):
        self.root_list.clear()
        for r in self.cfg.get("roots", []):
            self.root_list.addItem(QListWidgetItem(str(r)))

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
        # emit special Path() ? We'll let main window bind the sidebar back button directly.
        self.folder_selected.emit(Path(""))


# ----------------------------
# Gallery (async thumbs, fixed square tiles)
# ----------------------------
class ThumbnailTile(QFrame):
    clicked = Signal()

    def __init__(self, path: Path, fixed_size: int = TILE_SIZE, parent=None):
        super().__init__(parent)
        self.path = Path(path)
        # total tile: fixed_size (square) + label area
        self.setFixedSize(fixed_size, fixed_size + 44)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setStyleSheet(self._style())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # thumbnail region: square area slightly smaller than tile to provide margins
        self.thumb_label = QLabel()
        inner = fixed_size - 24  # padding
        self.thumb_label.setFixedSize(inner, inner)
        self.thumb_label.setAlignment(Qt.AlignCenter)
        # DO NOT stretch pixmap to the label size; we manually scale keeping aspect.
        self.thumb_label.setScaledContents(False)
        layout.addWidget(self.thumb_label, alignment=Qt.AlignCenter)

        # larger title font
        self.title = QLabel(self.path.name)
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setWordWrap(True)
        self.title.setFixedHeight(44)
        font = QFont()
        font.setPointSize(10)
        font.setBold(True)
        self.title.setFont(font)
        layout.addWidget(self.title)

    def mouseReleaseEvent(self, ev):
        if ev.button() == Qt.LeftButton:
            self.clicked.emit()

    def set_thumbnail(self, pixmap: QPixmap):
        if pixmap is None or pixmap.isNull():
            # folder/file icon fallback
            icon = QApplication.style().standardIcon(QStyle.SP_FileIcon)
            fallback = icon.pixmap(THUMB_SIZE)
            self._set_pixmap_centered(fallback)
            return
        self._set_pixmap_centered(pixmap)

    def _set_pixmap_centered(self, pixmap: QPixmap):
        label_size = self.thumb_label.size()
        # scale preserving aspect ratio but not exceed label_size
        pm = pixmap.scaled(label_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.thumb_label.setPixmap(pm)

    def _style(self):
        return """
        QFrame {
            background: rgba(255,255,255,0.01);
            border-radius: 12px;
            border: 1px solid rgba(255,255,255,0.03);
        }
        QFrame:hover { background: rgba(255,255,255,0.03); }
        """


class FolderTile(QPushButton):
    """Folder tile with optional media thumbnail (has_media is optional)."""

    clicked = Signal()

    def __init__(self, path: Path, has_media: bool = False, fixed_size: int = TILE_SIZE, parent=None):
        super().__init__(parent)
        self.path = Path(path)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setFixedSize(fixed_size, fixed_size + 44)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setStyleSheet(self._style())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        self.thumb_label = QLabel()
        inner = fixed_size - 24
        self.thumb_label.setFixedSize(inner, inner)
        self.thumb_label.setAlignment(Qt.AlignCenter)
        self.thumb_label.setScaledContents(False)
        layout.addWidget(self.thumb_label, alignment=Qt.AlignCenter)

        self.title = QLabel(self.path.name)
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setWordWrap(True)
        self.title.setFixedHeight(44)
        font = QFont()
        font.setPointSize(10)
        font.setBold(True)
        self.title.setFont(font)
        layout.addWidget(self.title)

        # default placeholder (folder icon) — if has_media we'll request an actual thumbnail elsewhere
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
            background: rgba(255,255,255,0.01);
            border-radius: 12px;
            border: 1px solid rgba(255,255,255,0.03);
            text-align: center;
        }
        QPushButton:hover { background: rgba(255,255,255,0.03); }
        """


class Gallery(QWidget):
    folder_open_requested = Signal(Path)
    media_open_requested = Signal(list, int)

    def __init__(self, thumb_signal: ThumbnailSignal, parent=None):
        super().__init__(parent)
        self.thumb_signal = thumb_signal
        self.thumb_signal.ready.connect(self.on_thumb_ready)
        self.threadpool = QThreadPool.globalInstance()
        self.thumb_cache = {}  # path_str -> QPixmap
        self.waiting_widgets = {}  # path_str -> [widget, ...]
        self._submitted = set()

        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 12, 12, 12)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.container = QWidget()
        self.grid = QGridLayout(self.container)
        self.grid.setContentsMargins(6, 6, 6, 6)
        self.grid.setSpacing(14)
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
        """Display top-level configured roots as folder tiles."""
        self.clear_grid()
        cols = 2
        row = col = 0
        for root in roots:
            p = Path(root)
            tile = FolderTile(p, has_media=False)
            tile.clicked.connect(lambda checked=False, rp=p: self.folder_open_requested.emit(rp))
            # show folder icon (no media)
            self.grid.addWidget(tile, row, col)
            col += 1
            if col >= cols:
                col = 0
                row += 1

    def show_folder_contents(self, path: Path):
        self.current_path = path
        subdirs = list_subdirs(path)
        media = list_media_files(path)
        # Always show subfolders first if present; any direct media also shown below
        self.clear_grid()
        row = col = 0
        cols = 4
        if subdirs:
            for d in subdirs:
                sub_media = list_media_files(d)
                has_media_direct = len(sub_media) > 0
                tile = FolderTile(d, has_media=has_media_direct)
                tile.clicked.connect(lambda checked=False, p=d: self.folder_open_requested.emit(p))
                # if folder has direct media, request thumbnail for first media file
                if has_media_direct:
                    first_media = sub_media[0]
                    self.request_thumbnail_for_path(first_media, tile)
                self.grid.addWidget(tile, row, col)
                col += 1
                if col >= cols:
                    col = 0
                    row += 1
        # Add media from current folder (direct files) below subfolders
        if media:
            # if we already placed subfolders, start a new row
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
            lbl = QLabel("Folder is empty")
            lbl.setStyleSheet("font-size: 12pt; color: #bcd3ff;")
            self.grid.addWidget(lbl, 0, 0)

    def _on_media_clicked(self, media_list, idx):
        self.media_open_requested.emit(media_list, idx)

    def request_thumbnail_for_path(self, path: Path, widget):
        key = str(path)
        # if cached, apply immediately
        if key in self.thumb_cache:
            widget.set_thumbnail(self.thumb_cache[key])
            return
        # register waiting widget
        self.waiting_widgets.setdefault(key, []).append(widget)
        # submit worker once per path
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
                # video placeholder: file icon + triangle overlay
                icon = QApplication.style().standardIcon(QStyle.SP_FileIcon)
                base = icon.pixmap(THUMB_SIZE)
                # create a copy to paint on
                p = QPixmap(base)
                painter = QPainter()
                try:
                    # Ensure painter begins; using try/finally to guarantee end
                    painter.begin(p)
                    painter.setRenderHint(QPainter.Antialiasing)
                    size = min(p.width(), p.height())
                    tri_size = int(size * 0.26)
                    cx = p.width() // 2
                    cy = p.height() // 2
                    # Build polygon safely using QPoint and QPolygon.append
                    poly = QPolygon()
                    poly.append(QPoint(cx - tri_size // 2, cy - tri_size))
                    poly.append(QPoint(cx - tri_size // 2, cy + tri_size))
                    poly.append(QPoint(cx + tri_size, cy))
                    painter.setBrush(QColor(255, 255, 255, 220))
                    painter.setPen(Qt.NoPen)
                    painter.drawPolygon(poly)
                except Exception:
                    # in case painting fails, we'll just fallback to base icon
                    pass
                finally:
                    painter.end()
                pix = p
            else:
                icon = QApplication.style().standardIcon(QStyle.SP_FileIcon)
                pix = icon.pixmap(THUMB_SIZE)
        # cache and apply
        self.thumb_cache[key] = pix
        widgets = self.waiting_widgets.pop(key, [])
        for w in widgets:
            try:
                w.set_thumbnail(pix)
            except Exception:
                pass


# ----------------------------
# Viewer embedded in main window (improved sizing + zoom)
# ----------------------------
class ViewerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(self._style())

        v = QVBoxLayout(self)
        v.setContentsMargins(8, 8, 8, 8)
        v.setSpacing(6)

        # top controls area (kept simple)
        top = QHBoxLayout()
        self.prev_btn = QPushButton("◀")
        self.next_btn = QPushButton("▶")
        self.close_btn = QPushButton("Close")
        top.addWidget(self.prev_btn)
        top.addWidget(self.next_btn)
        top.addStretch()
        top.addWidget(self.close_btn)
        v.addLayout(top)

        # viewer_area fills remaining space; we use it to compute available area for media
        self.viewer_area = QWidget()
        self.viewer_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.viewer_area_layout = QVBoxLayout(self.viewer_area)
        self.viewer_area_layout.setContentsMargins(0, 0, 0, 0)
        self.viewer_area_layout.setSpacing(0)
        v.addWidget(self.viewer_area)

        # image scroll area (will be added/removed into viewer_area_layout)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setScaledContents(False)
        self.scroll.setWidget(self.image_label)

        # video
        self.video_widget = QVideoWidget()
        self.player = QMediaPlayer(self)
        self.audio = QAudioOutput(self)
        self.player.setAudioOutput(self.audio)
        self.player.setVideoOutput(self.video_widget)
        self.video_controls = QHBoxLayout()
        self.play_btn = QPushButton("Play")
        self.play_btn.clicked.connect(self.toggle_play)
        self.video_slider = QSlider(Qt.Horizontal)
        self.video_slider.setRange(0, 1000)
        self.video_controls.addWidget(self.play_btn)
        self.video_controls.addWidget(self.video_slider)
        self.player.positionChanged.connect(self._on_pos_changed)
        self.player.durationChanged.connect(self._on_dur_changed)
        self.video_slider.sliderMoved.connect(self._on_slider_moved)

        # state
        self.media_list = []
        self.index = 0
        self.current_pixmap_original = None  # store original pixmap for crisp scaling
        self.current_media_is_image = False
        self.zoom = 1.0  # zoom factor (1.0 = fit-to-window on open)

        # connect nav
        self.prev_btn.clicked.connect(self.prev_item)
        self.next_btn.clicked.connect(self.next_item)
        self.close_btn.clicked.connect(self.on_close)

    def _style(self):
        return """
        QWidget { background: #071126; color: #e6eef8; border-radius: 10px; }
        QPushButton {
            background: rgba(255,255,255,0.03);
            padding: 6px 10px;
            border-radius: 8px;
            font-weight: 600;
        }
        QPushButton:hover { background: rgba(255,255,255,0.05); }
        """

    def open_media_list(self, media_list, start_index=0):
        self.media_list = media_list[:]
        self.index = int(start_index) % max(1, len(self.media_list))
        self.zoom = 1.0
        self.show_current_media()

    def show_current_media(self):
        # clear viewer_area_layout
        while self.viewer_area_layout.count():
            it = self.viewer_area_layout.takeAt(0)
            w = it.widget()
            if w:
                w.setParent(None)

        if not self.media_list:
            lbl = QLabel("No media")
            self.viewer_area_layout.addWidget(lbl)
            return

        path = Path(self.media_list[self.index])
        if is_image(path):
            # stop video if playing
            try:
                if self.player.playbackState() == QMediaPlayer.PlayingState:
                    self.player.stop()
                    self.play_btn.setText("Play")
            except Exception:
                pass
            # load full-res pixmap once and store
            pix = QPixmap(str(path))
            if pix.isNull():
                lbl = QLabel("Failed to load image")
                self.viewer_area_layout.addWidget(lbl)
                return
            self.current_pixmap_original = pix
            self.current_media_is_image = True
            # fit to viewer_area size initially
            self._update_image_display(fit=True)
            self.viewer_area_layout.addWidget(self.scroll)
        elif is_video(path):
            self.current_media_is_image = False
            # setup and add video widget + controls
            try:
                self.player.setSource(QUrl.fromLocalFile(str(path)))
            except Exception:
                # fallback: try older API
                try:
                    self.player.setSource(QUrl.fromLocalFile(str(path)))
                except Exception:
                    pass
            self.player.pause()
            self.play_btn.setText("Play")
            # make video_widget expand to fill viewer_area
            self.video_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            self.viewer_area_layout.addWidget(self.video_widget, stretch=1)
            # add controls below
            controls_container = QWidget()
            controls_layout = QHBoxLayout(controls_container)
            controls_layout.setContentsMargins(0, 0, 0, 0)
            controls_layout.addWidget(self.play_btn)
            controls_layout.addWidget(self.video_slider)
            self.viewer_area_layout.addWidget(controls_container)
        else:
            lbl = QLabel("Unsupported media type")
            self.viewer_area_layout.addWidget(lbl)

    def _update_image_display(self, fit=False):
        """Scale original pixmap according to current zoom and viewer_area size."""
        if not self.current_pixmap_original or self.current_pixmap_original.isNull():
            return
        avail = self.viewer_area.size()
        avail_w = max(10, avail.width())
        avail_h = max(10, avail.height())
        if fit:
            # compute scale to fit while preserving aspect
            scaled = self.current_pixmap_original.scaled(avail_w, avail_h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.zoom = 1.0  # reset zoom baseline as 'fit'
            self.image_label.setPixmap(scaled)
        else:
            # apply zoom relative to original or relative to fit baseline:
            # We'll interpret zoom as multiplier where 1.0 is fit size; compute target by first fitting then scaling.
            base = self.current_pixmap_original.scaled(avail_w, avail_h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            target_w = max(1, int(base.width() * self.zoom))
            target_h = max(1, int(base.height() * self.zoom))
            scaled = base.scaled(target_w, target_h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.image_label.setPixmap(scaled)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # if current media is image, rescale appropriately
        if self.current_media_is_image and self.current_pixmap_original:
            # adjust display; keep current zoom factor but if zoom == 1.0 treat as fit
            if abs(self.zoom - 1.0) < 1e-6:
                self._update_image_display(fit=True)
            else:
                self._update_image_display(fit=False)

    def toggle_play(self):
        st = self.player.playbackState()
        if st == QMediaPlayer.PlayingState:
            self.player.pause()
            self.play_btn.setText("Play")
        else:
            self.player.play()
            self.play_btn.setText("Pause")

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
        # hide self and let parent restore gallery
        self.setVisible(False)

    def key_press(self, event):
        if event.key() == Qt.Key_Escape:
            self.on_close()
        elif event.key() in (Qt.Key_Right, Qt.Key_D):
            self.next_item()
        elif event.key() in (Qt.Key_Left, Qt.Key_A):
            self.prev_item()

    def wheelEvent(self, event):
        """Support Ctrl + mouse wheel for zoom in/out on images."""
        modifiers = QApplication.keyboardModifiers()
        if self.current_media_is_image and (modifiers & Qt.ControlModifier):
            # delta in Qt6 is angleDelta; event.angleDelta().y() gives steps (multiples of 120)
            delta = event.angleDelta().y()
            if delta > 0:
                factor = 1.15
            else:
                factor = 1 / 1.15
            # If zoom was at baseline 1.0 (fit), we will set zoom to 1.0 * small > 1.0
            self.zoom = max(0.1, min(10.0, self.zoom * factor))
            # After changing zoom, update display
            self._update_image_display(fit=False)
            event.accept()
        else:
            super().wheelEvent(event)


# ----------------------------
# Main window & wiring
# ----------------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Library Reader — Modern")
        self.setMinimumSize(1100, 700)
        self.setStyleSheet(self._global_style())

        # central widget
        central = QWidget()
        self.setCentralWidget(central)
        h = QHBoxLayout(central)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(0)

        # create sidebar (left) and right content area
        self.sidebar = Sidebar()
        h.addWidget(self.sidebar)

        # right: stacked area (gallery OR viewer)
        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        h.addWidget(right_container, stretch=1)

        # Create thumbnail signal and pass to gallery
        self.thumb_signal = ThumbnailSignal()
        self.gallery = Gallery(self.thumb_signal)
        right_layout.addWidget(self.gallery)

        # Embedded viewer (hidden by default)
        self.viewer = ViewerWidget()
        self.viewer.setVisible(False)
        right_layout.addWidget(self.viewer)

        # connections
        self.sidebar.folder_selected.connect(self.on_sidebar_folder_selected)
        self.gallery.folder_open_requested.connect(self.on_folder_selected)
        self.gallery.media_open_requested.connect(self.open_viewer)
        self.viewer.close_btn.clicked.connect(self.close_viewer)

        # navigation history
        self.history = []
        self.current = None

        # show roots view at startup
        cfg = load_config()
        self.show_roots_view(cfg.get("roots", []))

        # connect sidebar add/remove/back to main actions
        self.sidebar.add_btn.clicked.connect(self.sidebar.add_root)
        self.sidebar.rem_btn.clicked.connect(self.sidebar.remove_root)
        self.sidebar.back_btn.clicked.connect(self.go_back_top)

    def _global_style(self):
        return """
        QMainWindow { background: #041023; color: #e6eef8; }
        QLabel { color: #dbe9ff; }
        """

    def show_roots_view(self, roots):
        """Show the configured root folders as the top-level UI."""
        self.gallery.setVisible(True)
        self.viewer.setVisible(False)
        self.gallery.show_roots(roots)
        # also clear navigation history
        self.history.clear()
        self.current = None
        # clear sidebar file tree model so user must pick a root or add
        self.sidebar.tree.setModel(None)
        # refresh roots list
        self.sidebar.populate_roots()

    def on_sidebar_folder_selected(self, path: Path):
        # Sidebar emits Path("") for back; treat that as top-level request
        if not path or str(path) == "":
            self.go_back_top()
            return
        self.on_folder_selected(path)

    def on_folder_selected(self, path: Path):
        # when a folder is selected, record current and show contents
        if self.current:
            self.history.append(self.current)
        self.current = path
        # ensure sidebar shows appropriate tree root for navigation
        # find which configured root contains this path (if any) and set tree accordingly
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
        # show gallery contents
        self.viewer.setVisible(False)
        self.gallery.setVisible(True)
        self.gallery.show_folder_contents(path)

    def go_back_top(self):
        """Back button returns to top-level roots view (not just previous folder)."""
        cfg = load_config()
        self.show_roots_view(cfg.get("roots", []))

    def open_viewer(self, media_list, index):
        # show viewer embedded, provide media list
        # media_list contains Path objects; convert to list of str for stability
        self.viewer.open_media_list([str(m) for m in media_list], index)
        self.viewer.setVisible(True)
        self.gallery.setVisible(False)

    def close_viewer(self):
        self.viewer.setVisible(False)
        self.gallery.setVisible(True)

    def keyPressEvent(self, event):
        # forward to viewer if visible
        if self.viewer.isVisible():
            self.viewer.key_press(event)
        else:
            super().keyPressEvent(event)


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    mw = MainWindow()
    mw.show()
    # if no roots configured, prompt quick hint
    cfg = load_config()
    if not cfg.get("roots"):
        QMessageBox.information(
            mw,
            "No roots",
            "No root folders configured. Use Add Root in the left sidebar to add roots."
        )
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
