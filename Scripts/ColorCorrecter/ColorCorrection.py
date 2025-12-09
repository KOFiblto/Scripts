#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mini Color Corrector ("mini DaVinci") – single-file PyQt5 app

Features
- Load any video via OpenCV (cv2.VideoCapture)
- Scrub to pick a reference frame for live preview
- Real-time sliders: Brightness, Contrast, Saturation, Gamma, R/G/B gains
- Toggle GPU acceleration (NVENC) for export if available
- Export with ffmpeg filters; keeps GUI responsive (QProcess in separate thread)
- Auto-incremented output filename: original_filename_color-corrected_XXXX.ext
"""

import os
import re
import sys
import shlex
import math
import pathlib
import subprocess
from dataclasses import dataclass

# Qt import: prefer PyQt5, fallback to PySide6 if needed
try:
    from PyQt5 import QtCore, QtGui, QtWidgets
    Signal = QtCore.pyqtSignal
except ImportError:
    from PySide6 import QtCore, QtGui, QtWidgets
    Signal = QtCore.Signal

import cv2
import numpy as np

# -----------------------------
# Utility: slider model & mapping
# -----------------------------

@dataclass
class Controls:
    brightness: float = 0.0   # ffmpeg eq: -1..1 (0 neutral)
    contrast: float   = 1.0   # eq: 0..2 (1 neutral)
    saturation: float = 1.0   # eq: 0..3 (1 neutral)
    gamma: float      = 1.0   # eq: 0.1..10 (1 neutral)
    r_gain: float     = 1.0   # colorchannelmixer rr
    g_gain: float     = 1.0   # colorchannelmixer gg
    b_gain: float     = 1.0   # colorchannelmixer bb

# -----------------------------
# Color correction (preview path)
# -----------------------------

def apply_preview_cc(bgr_img: np.ndarray, c: Controls) -> np.ndarray:
    """
    Approximate ffmpeg filter chain for preview:
      colorchannelmixer -> eq(contrast, brightness, saturation, gamma)
    Implemented using OpenCV/NumPy in float32 [0,1] domain.
    """
    if bgr_img is None:
        return None
    img = bgr_img.astype(np.float32) / 255.0  # BGR in [0,1]

    # 1) Per-channel gains (B,G,R order in OpenCV)
    gains = np.array([c.b_gain, c.g_gain, c.r_gain], dtype=np.float32).reshape(1,1,3)
    img = img * gains

    # 2) Gamma (eq gamma: 1.0 neutral; >1 brightens midtones; apply as y = x ** (1/gamma))
    if c.gamma > 0:
        inv_gamma = 1.0 / c.gamma
        img = np.clip(img, 0.0, 1.0) ** inv_gamma

    # 3) Contrast & Brightness (approximate eq):
    #    eq contrast applies around 0.5. brightness is additive (-1..1) on [0,1] scale ~ /2
    img = (img - 0.5) * c.contrast + 0.5
    img = img + (c.brightness * 0.5)  # map -1..1 -> -0.5..0.5

    img = np.clip(img, 0.0, 1.0)

    # 4) Saturation in HSV
    hsv = cv2.cvtColor((img * 255).astype(np.uint8), cv2.COLOR_BGR2HSV).astype(np.float32)
    hsv[...,1] *= c.saturation
    hsv[...,1] = np.clip(hsv[...,1], 0, 255)
    img = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR).astype(np.float32) / 255.0

    out = np.clip(img * 255.0, 0, 255).astype(np.uint8)
    return out

# -----------------------------
# FFmpeg command generation
# -----------------------------

def build_ffmpeg_filters(c: Controls) -> str:
    """
    Construct ffmpeg filter graph string reflecting the UI controls.
    Order: colorchannelmixer -> eq
    """
    # colorchannelmixer with diagonal gains only (no cross-channel mixing)
    ccm = f"colorchannelmixer=rr={c.r_gain:.6f}:gg={c.g_gain:.6f}:bb={c.b_gain:.6f}"

    # eq
    # Clamp to valid ranges expected by ffmpeg eq to avoid runtime errors
    br = max(-1.0, min(1.0, c.brightness))
    ct = max(0.0, min(2.0, c.contrast))
    st = max(0.0, min(3.0, c.saturation))
    gm = max(0.1, min(10.0, c.gamma))
    eq = f"eq=contrast={ct:.6f}:brightness={br:.6f}:saturation={st:.6f}:gamma={gm:.6f}"

    return f"{ccm},{eq}"

def detect_nvenc_encoder(ext: str) -> str:
    """
    Pick a sane NVENC encoder based on typical container.
    """
    ext = ext.lower()
    if ext in [".mp4", ".mov", ".m4v", ".mts", ".m2ts"]:
        return "h264_nvenc"
    # default to h264 for wide compatibility (mkv will be fine with h264 as well)
    return "h264_nvenc"

def detect_cpu_encoder(ext: str) -> str:
    ext = ext.lower()
    if ext in [".mp4", ".mov", ".m4v", ".mts", ".m2ts"]:
        return "libx264"
    return "libx264"

def next_output_path(src: str) -> str:
    """
    Compute auto-incrementing path:
      original_filename_color-corrected_XXXX.ext, starting at 0001 in same dir.
    """
    p = pathlib.Path(src)
    stem, ext = p.stem, p.suffix
    pattern = re.compile(re.escape(stem) + r"_color\-corrected_(\d{4})" + re.escape(ext) + r"$")
    dirp = p.parent
    max_n = 0
    for child in dirp.glob(f"{stem}_color-corrected_*.{ext.lstrip('.') }"):
        m = pattern.match(child.name)
        if m:
            try:
                n = int(m.group(1))
                max_n = max(max_n, n)
            except:
                pass
    nxt = max_n + 1
    return str(dirp / f"{stem}_color-corrected_{nxt:04d}{ext}")

# -----------------------------
# Export Worker (QProcess)
# -----------------------------

class ExportWorker(QtCore.QObject):
    """
    Runs ffmpeg export without blocking the GUI.
    """
    started = Signal()
    progress = Signal(float, str)  # percent, status text
    finished = Signal(int, str)    # exitCode, outputPath
    error = Signal(str)

    def __init__(self, src_path: str, out_path: str, c: Controls, use_gpu: bool, est_duration_sec: float):
        super().__init__()
        self.src_path = src_path
        self.out_path = out_path
        self.controls = c
        self.use_gpu = use_gpu
        self.est_duration = max(0.01, est_duration_sec)
        self.proc = QtCore.QProcess()
        self.proc.setProcessChannelMode(QtCore.QProcess.ProcessChannelMode.MergedChannels)
        self.proc.readyReadStandardError.connect(self._on_stderr)  # merged
        self.proc.readyReadStandardOutput.connect(self._on_stdout)
        self.proc.finished.connect(self._on_finished)
        self._time_regex = re.compile(r"time=(\d+):(\d+):(\d+)\.(\d+)")
        self._buffer = bytearray()

    def start(self):
        self.started.emit()
        filters = build_ffmpeg_filters(self.controls)
        src = self.src_path
        out = self.out_path
        ext = pathlib.Path(out).suffix.lower()

        if self.use_gpu:
            vencoder = detect_nvenc_encoder(ext)
            cmd = [
                "ffmpeg", "-y", "-hide_banner",
                "-hwaccel", "cuda",
                "-i", src,
                "-vf", filters,
                "-c:v", vencoder,
                "-preset", "p4",           # balanced NVENC preset
                "-cq", "20",               # constant quality target
                "-c:a", "copy",
                out
            ]
        else:
            vencoder = detect_cpu_encoder(ext)
            cmd = [
                "ffmpeg", "-y", "-hide_banner",
                "-i", src,
                "-vf", filters,
                "-c:v", vencoder,
                "-preset", "medium",
                "-crf", "20",
                "-c:a", "copy",
                out
            ]

        # Use native start; no shell
        self.proc.start(cmd[0], cmd[1:])
        if not self.proc.waitForStarted(3000):
            self.error.emit("Failed to start ffmpeg process. Is ffmpeg installed and on PATH?")
            return

    def _on_stdout(self):
        # Not used; we merged channels
        pass

    def _parse_time_to_sec(self, h: str, m: str, s: str, ms: str) -> float:
        return int(h)*3600 + int(m)*60 + int(s) + int(ms)/100.0

    def _on_stderr(self):
        data = self.proc.readAllStandardError()
        if not data:
            return
        try:
            text = bytes(data).decode(errors="ignore")
        except Exception:
            return
        # Parse time=HH:MM:SS.xx for progress
        for m in self._time_regex.finditer(text):
            tsec = self._parse_time_to_sec(m.group(1), m.group(2), m.group(3), m.group(4))
            pct = max(0.0, min(100.0, (tsec / self.est_duration) * 100.0))
            self.progress.emit(pct, f"Encoding… {pct:.1f}%")
        # Also emit last line occasionally
        lines = [ln for ln in text.strip().splitlines() if ln.strip()]
        if lines:
            self.progress.emit(None if self.est_duration <= 0 else 0.0, lines[-1])

    def _on_finished(self, exitCode, exitStatus):
        self.finished.emit(int(exitCode), self.out_path)

# -----------------------------
# Main Window
# -----------------------------

class MiniColorCorrector(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mini Color Corrector")
        self.setMinimumSize(1100, 680)

        self.video_path = None
        self.cap = None
        self.total_frames = 0
        self.fps = 0.0
        self.duration_sec = 0.0
        self.current_frame_idx = 0
        self.reference_frame = None  # np.ndarray (BGR)
        self.controls = Controls()
        self.export_thread = None
        self.export_worker = None

        self._build_ui()
        self._connect_signals()
        self._set_controls_defaults()

    # UI
    def _build_ui(self):
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        main = QtWidgets.QHBoxLayout(central)

        # Left: preview
        left = QtWidgets.QVBoxLayout()
        self.preview_label = QtWidgets.QLabel("Open a video to begin…")
        self.preview_label.setAlignment(QtCore.Qt.AlignCenter)
        self.preview_label.setStyleSheet("background:#111; color:#bbb;")
        self.preview_label.setMinimumSize(640, 360)
        self.preview_label.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        # Frame scrubber
        self.frame_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.frame_slider.setMinimum(0)
        self.frame_slider.setMaximum(0)
        self.frame_slider.setEnabled(False)
        self.frame_pos_label = QtWidgets.QLabel("--:-- / --:--")
        self.frame_pos_label.setStyleSheet("color:#888;")

        scrub_layout = QtWidgets.QHBoxLayout()
        scrub_layout.addWidget(self.frame_slider)
        scrub_layout.addWidget(self.frame_pos_label)

        # File open + Export + GPU toggle
        topbar = QtWidgets.QHBoxLayout()
        self.open_btn = QtWidgets.QPushButton("Open Video…")
        self.export_btn = QtWidgets.QPushButton("Export")
        self.export_btn.setEnabled(False)
        self.gpu_chk = QtWidgets.QCheckBox("Use GPU (NVENC if available)")
        self.gpu_chk.setChecked(True)
        self.status_lbl = QtWidgets.QLabel("")
        self.status_lbl.setStyleSheet("color:#8ab4f8;")
        topbar.addWidget(self.open_btn)
        topbar.addWidget(self.export_btn)
        topbar.addWidget(self.gpu_chk)
        topbar.addStretch(1)
        topbar.addWidget(self.status_lbl)

        left.addLayout(topbar)
        left.addWidget(self.preview_label, 1)
        left.addLayout(scrub_layout)

        # Right: controls (sliders)
        right = QtWidgets.QVBoxLayout()
        right.setContentsMargins(8,8,8,8)
        right.addWidget(self._group_controls(), 1)

        # Progress bar
        self.progress = QtWidgets.QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(True)
        self.progress.setVisible(False)

        # Put together
        main.addLayout(left, 2)
        main.addLayout(right, 1)
        main.setStretch(0,2)
        main.setStretch(1,1)

        # Bottom status/progress
        bott = QtWidgets.QVBoxLayout()
        bott.addWidget(self.progress)
        main.addLayout(bott)

    def _group_controls(self):
        w = QtWidgets.QGroupBox("Color Controls")
        lay = QtWidgets.QVBoxLayout(w)

        # Helper to create a slider + spinbox row
        def slider_row(label_text, minv, maxv, init, step, map_to_label=lambda v: str(v)):
            row = QtWidgets.QHBoxLayout()
            lbl = QtWidgets.QLabel(label_text)
            sld = QtWidgets.QSlider(QtCore.Qt.Horizontal)
            sld.setMinimum(minv)
            sld.setMaximum(maxv)
            sld.setSingleStep(step)
            sld.setValue(init)
            val_lbl = QtWidgets.QLabel(map_to_label(init))
            val_lbl.setFixedWidth(80)
            row.addWidget(lbl)
            row.addWidget(sld, 1)
            row.addWidget(val_lbl)
            return row, sld, val_lbl

        # Brightness: -100..100 (maps to -1..1 for ffmpeg)
        br_row, self.sld_brightness, self.lbl_brightness = slider_row(
            "Brightness", -100, 100, 0, 1, lambda v: f"{v/100:+.2f}"
        )
        # Contrast: 0..200 (maps to 0..2)
        ct_row, self.sld_contrast, self.lbl_contrast = slider_row(
            "Contrast", 0, 200, 100, 1, lambda v: f"{v/100:.2f}"
        )
        # Saturation: 0..300 (maps to 0..3)
        st_row, self.sld_saturation, self.lbl_saturation = slider_row(
            "Saturation", 0, 300, 100, 1, lambda v: f"{v/100:.2f}"
        )
        # Gamma: 10..300 (maps to 0.1..3.0; default 1.0)
        gm_row, self.sld_gamma, self.lbl_gamma = slider_row(
            "Gamma", 10, 300, 100, 1, lambda v: f"{v/100:.2f}"
        )
        # RGB gains: 0..300 (maps to 0..3)
        r_row, self.sld_r, self.lbl_r = slider_row("Red Gain",   0, 300, 100, 1, lambda v: f"{v/100:.2f}")
        g_row, self.sld_g, self.lbl_g = slider_row("Green Gain", 0, 300, 100, 1, lambda v: f"{v/100:.2f}")
        b_row, self.sld_b, self.lbl_b = slider_row("Blue Gain",  0, 300, 100, 1, lambda v: f"{v/100:.2f}")

        # Reset button
        self.reset_btn = QtWidgets.QPushButton("Reset Controls")

        for row in [br_row, ct_row, st_row, gm_row, r_row, g_row, b_row]:
            lay.addLayout(row)
        lay.addWidget(self.reset_btn)
        lay.addStretch(1)

        return w

    def _connect_signals(self):
        self.open_btn.clicked.connect(self.on_open)
        self.export_btn.clicked.connect(self.on_export)
        self.reset_btn.clicked.connect(self.on_reset_controls)
        self.frame_slider.valueChanged.connect(self.on_seek_frame)

        # Sliders update preview
        self.sld_brightness.valueChanged.connect(self.on_controls_changed)
        self.sld_contrast.valueChanged.connect(self.on_controls_changed)
        self.sld_saturation.valueChanged.connect(self.on_controls_changed)
        self.sld_gamma.valueChanged.connect(self.on_controls_changed)
        self.sld_r.valueChanged.connect(self.on_controls_changed)
        self.sld_g.valueChanged.connect(self.on_controls_changed)
        self.sld_b.valueChanged.connect(self.on_controls_changed)

    def _set_controls_defaults(self):
        self.controls = Controls()
        self._sync_controls_to_labels()

    def _sync_controls_to_labels(self):
        # Map sliders -> Controls
        self.controls.brightness = self.sld_brightness.value() / 100.0
        self.controls.contrast   = self.sld_contrast.value() / 100.0
        self.controls.saturation = self.sld_saturation.value() / 100.0
        self.controls.gamma      = self.sld_gamma.value() / 100.0
        self.controls.r_gain     = self.sld_r.value() / 100.0
        self.controls.g_gain     = self.sld_g.value() / 100.0
        self.controls.b_gain     = self.sld_b.value() / 100.0

        # Labels
        self.lbl_brightness.setText(f"{self.controls.brightness:+.2f}")
        self.lbl_contrast.setText(f"{self.controls.contrast:.2f}")
        self.lbl_saturation.setText(f"{self.controls.saturation:.2f}")
        self.lbl_gamma.setText(f"{self.controls.gamma:.2f}")
        self.lbl_r.setText(f"{self.controls.r_gain:.2f}")
        self.lbl_g.setText(f"{self.controls.g_gain:.2f}")
        self.lbl_b.setText(f"{self.controls.b_gain:.2f}")

    # -----------------------------
    # Video handling
    # -----------------------------

    def on_open(self):
        filters = "Video Files (*.mp4 *.mov *.mkv *.avi *.m4v *.webm *.mts *.m2ts);;All Files (*)"
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Open Video", "", filters)
        if not path:
            return
        self.load_video(path)

    def load_video(self, path: str):
        self.cleanup_capture()
        self.video_path = path
        self.cap = cv2.VideoCapture(path)
        if not self.cap.isOpened():
            self.status_lbl.setText("Failed to open video.")
            return

        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        self.fps = float(self.cap.get(cv2.CAP_PROP_FPS) or 0.0)
        if self.fps <= 0:
            # attempt fallback via duration
            self.duration_sec = float(self.cap.get(cv2.CAP_PROP_POS_MSEC) or 0.0) / 1000.0
        else:
            self.duration_sec = self.total_frames / self.fps if self.total_frames > 0 else 0.0

        self.frame_slider.setEnabled(self.total_frames > 0)
        self.frame_slider.setMaximum(max(0, self.total_frames - 1))
        self.frame_slider.setValue(0)
        self.current_frame_idx = 0
        self.read_and_show_frame(0)
        self.export_btn.setEnabled(True)
        self.status_lbl.setText(os.path.basename(path))

    def cleanup_capture(self):
        if self.cap is not None:
            try:
                self.cap.release()
            except:
                pass
        self.cap = None
        self.reference_frame = None

    def on_seek_frame(self, idx: int):
        self.current_frame_idx = idx
        self.read_and_show_frame(idx)

    def read_and_show_frame(self, idx: int):
        if not self.cap:
            return
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ok, frame = self.cap.read()
        if not ok or frame is None:
            return
        self.reference_frame = frame
        self.update_preview()

        # time label
        if self.fps > 0:
            sec = idx / self.fps
        else:
            sec = 0.0
        self.frame_pos_label.setText(f"{self._sec_to_hms(sec)} / {self._sec_to_hms(self.duration_sec)}")

    def _sec_to_hms(self, s: float) -> str:
        s = int(round(s))
        h = s // 3600
        m = (s % 3600) // 60
        s2 = s % 60
        if h > 0:
            return f"{h:02d}:{m:02d}:{s2:02d}"
        else:
            return f"{m:02d}:{s2:02d}"

    # -----------------------------
    # Preview updates
    # -----------------------------

    def on_controls_changed(self, *_):
        self._sync_controls_to_labels()
        self.update_preview()

    def on_reset_controls(self):
        self.sld_brightness.setValue(0)
        self.sld_contrast.setValue(100)
        self.sld_saturation.setValue(100)
        self.sld_gamma.setValue(100)
        self.sld_r.setValue(100)
        self.sld_g.setValue(100)
        self.sld_b.setValue(100)
        self._sync_controls_to_labels()
        self.update_preview()

    def update_preview(self):
        if self.reference_frame is None:
            return
        out = apply_preview_cc(self.reference_frame, self.controls)
        self._show_image(out)

    def _show_image(self, bgr: np.ndarray):
        if bgr is None:
            return
        # Fit into preview label while keeping aspect ratio
        h, w, _ = bgr.shape
        qimg = QtGui.QImage(bgr.data, w, h, bgr.strides[0], QtGui.QImage.Format.Format_BGR888 if hasattr(QtGui.QImage.Format, 'Format_BGR888') else QtGui.QImage.Format_BGR888)
        pix = QtGui.QPixmap.fromImage(qimg)
        scaled = pix.scaled(self.preview_label.size(), QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
        self.preview_label.setPixmap(scaled)

    def resizeEvent(self, event: QtGui.QResizeEvent):
        super().resizeEvent(event)
        if self.reference_frame is not None:
            self.update_preview()

    # -----------------------------
    # Export
    # -----------------------------

    def on_export(self):
        if not self.video_path:
            return
        out_path = next_output_path(self.video_path)

        # Ensure output dir writable
        try:
            pathlib.Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Export Error", f"Cannot create output directory:\n{e}")
            return

        # Prepare worker
        self.progress.setVisible(True)
        self.progress.setValue(0)
        self.status_lbl.setText("Starting export…")
        self.export_btn.setEnabled(False)
        self.open_btn.setEnabled(False)
        self.frame_slider.setEnabled(False)

        # Fresh snapshot of controls (clamp a bit)
        c = Controls(
            brightness=float(max(-1.0, min(1.0, self.controls.brightness))),
            contrast=float(max(0.0, min(2.0, self.controls.contrast))),
            saturation=float(max(0.0, min(3.0, self.controls.saturation))),
            gamma=float(max(0.1, min(10.0, self.controls.gamma))),
            r_gain=float(max(0.0, min(3.0, self.controls.r_gain))),
            g_gain=float(max(0.0, min(3.0, self.controls.g_gain))),
            b_gain=float(max(0.0, min(3.0, self.controls.b_gain))),
        )

        use_gpu = self.gpu_chk.isChecked()
        est = self.duration_sec if self.duration_sec > 0 else 1.0

        self.export_thread = QtCore.QThread(self)
        self.export_worker = ExportWorker(self.video_path, out_path, c, use_gpu, est)
        self.export_worker.moveToThread(self.export_thread)

        # Wire signals
        self.export_thread.started.connect(self.export_worker.start)
        self.export_worker.started.connect(lambda: self.status_lbl.setText("Exporting…"))
        self.export_worker.progress.connect(self.on_export_progress)
        self.export_worker.finished.connect(self.on_export_finished)
        self.export_worker.error.connect(self.on_export_error)
        self.export_worker.finished.connect(lambda *_: self._cleanup_export())
        self.export_worker.error.connect(lambda *_: self._cleanup_export())

        self.export_thread.start()

    def _cleanup_export(self):
        self.open_btn.setEnabled(True)
        self.export_btn.setEnabled(True if self.video_path else False)
        self.frame_slider.setEnabled(True if self.cap and self.total_frames > 0 else False)
        if self.export_thread:
            self.export_thread.quit()
            self.export_thread.wait()
        self.export_thread = None
        self.export_worker = None

    def on_export_progress(self, pct: float, text: str):
        if pct is not None:
            self.progress.setValue(int(pct))
        if text:
            self.progress.setFormat(text)

    def on_export_finished(self, exitCode: int, out_path: str):
        self.progress.setValue(100)
        if exitCode == 0 and os.path.exists(out_path):
            self.status_lbl.setText(f"Done: {os.path.basename(out_path)}")
            QtWidgets.QMessageBox.information(
                self, "Export Complete", f"Export finished:\n{out_path}"
            )
        else:
            self.status_lbl.setText("Export failed.")
            QtWidgets.QMessageBox.critical(
                self, "Export Error", "ffmpeg finished with an error. Check console."
            )

    def on_export_error(self, msg: str):
        self.status_lbl.setText("Export error.")
        QtWidgets.QMessageBox.critical(self, "Export Error", msg)

# -----------------------------
# Main entry
# -----------------------------

def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName("Mini Color Corrector")

    # Dark-ish palette for nicer visuals
    pal = app.palette()
    pal.setColor(QtGui.QPalette.Window, QtGui.QColor("#202124"))
    pal.setColor(QtGui.QPalette.WindowText, QtCore.Qt.white)
    pal.setColor(QtGui.QPalette.Base, QtGui.QColor("#121212"))
    pal.setColor(QtGui.QPalette.AlternateBase, QtGui.QColor("#1E1E1E"))
    pal.setColor(QtGui.QPalette.ToolTipBase, QtCore.Qt.white)
    pal.setColor(QtGui.QPalette.ToolTipText, QtCore.Qt.white)
    pal.setColor(QtGui.QPalette.Text, QtCore.Qt.white)
    pal.setColor(QtGui.QPalette.Button, QtGui.QColor("#303134"))
    pal.setColor(QtGui.QPalette.ButtonText, QtCore.Qt.white)
    pal.setColor(QtGui.QPalette.BrightText, QtCore.Qt.red)
    pal.setColor(QtGui.QPalette.Highlight, QtGui.QColor("#8ab4f8"))
    pal.setColor(QtGui.QPalette.HighlightedText, QtCore.Qt.black)
    app.setPalette(pal)

    win = MiniColorCorrector()
    win.show()
    sys.exit(app.exec_() if hasattr(app, 'exec_') else app.exec())

if __name__ == "__main__":
    main()
