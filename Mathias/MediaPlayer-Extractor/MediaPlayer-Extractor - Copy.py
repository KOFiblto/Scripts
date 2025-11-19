import sys
import os
import subprocess
from pathlib import Path
from datetime import timedelta

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFileDialog, QLabel, QPushButton,
    QLineEdit, QTextEdit, QVBoxLayout, QHBoxLayout, QCheckBox, QMessageBox,
    QStyle, QStatusBar, QSlider, QSizePolicy
)
from PySide6.QtCore import Qt, QUrl
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QGraphicsColorizeEffect

# ------------------ CONFIG ------------------
BASE_DIR = Path(r"D:\_other\Celebs\Celebs")
ILLEGAL_CHARS = ['\\', '/', ':', '*', '?', '"', '<', '>', '|']

# ------------------ HELPERS ------------------
def sanitize_filename(name: str) -> str:
    for ch in ILLEGAL_CHARS:
        name = name.replace(ch, '_')
    return name.strip()

def format_time(ms: int) -> str:
    td = timedelta(milliseconds=ms)
    hours, remainder = divmod(td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    millis = td.microseconds // 1000
    return f"{td.days * 24 + hours:02d}-{minutes:02d}-{seconds:02d}_{millis:03d}"

def build_output_path(celebrity: str) -> Path:
    celeb_path = BASE_DIR / celebrity
    if not celeb_path.exists():
        reply = QMessageBox.question(None, "Create Celebrity Folder",
                                     f"The folder for '{celebrity}' does not exist.\nCreate it?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            celeb_path.mkdir(parents=True, exist_ok=True)
        else:
            return None
    return celeb_path

def title_case_name(name: str) -> str:
    return " ".join(word.capitalize() for word in name.split())

def detect_media_name(input_file: Path) -> str:
    parts = input_file.parts
    if "_movies" in parts:
        return sanitize_filename(input_file.parent.name)
    elif "_series" in parts:
        return sanitize_filename(input_file.parent.parent.name)
    else:
        return sanitize_filename(input_file.stem)

# ------------------ MAIN APP ------------------
class VideoExtractor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Celebrity Video Extractor")
        self.resize(1600, 900)

        # Media player
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        self.video_widget = QVideoWidget()
        self.media_player.setVideoOutput(self.video_widget)
        self.video_widget.setMinimumSize(640, 360)

        # ----------------- BUTTONS -----------------
        self.open_button = QPushButton("Open File")
        self.open_button.clicked.connect(self.open_file)

        self.celebrity_input = QLineEdit()
        self.celebrity_input.setPlaceholderText("Celebrity Name")
        self.celebrity_input.setMinimumHeight(50)

        self.extract_image_button = QPushButton("Extract Image (I)")
        self.extract_image_button.clicked.connect(self.extract_image)

        # Longer toggle button text
        self.start_segment_button = QPushButton("Start / Stop Extract Segment (C)")
        self.start_segment_button.clicked.connect(self.toggle_segment)

        self.extract_segment_button = QPushButton("Extract Segment (E)")
        self.extract_segment_button.setEnabled(False)
        self.extract_segment_button.clicked.connect(self.extract_segment)

        self.accurate_checkbox = QCheckBox("Accurate (re-encode)")
        self.accurate_checkbox.setChecked(True)

        self.open_folder_button = QPushButton("Open Output Folder")
        self.open_folder_button.clicked.connect(self.open_output_folder)

        self.play_button = QPushButton()
        self.play_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
        self.play_button.clicked.connect(self.play_pause)

        # --- New reset brightness button ---
        self.reset_brightness_button = QPushButton("Reset Brightness")
        self.reset_brightness_button.clicked.connect(self.reset_brightness)

        # Make buttons taller
        for btn in [self.open_button, self.extract_image_button, self.start_segment_button,
                    self.extract_segment_button, self.play_button, self.open_folder_button,
                    self.reset_brightness_button]:
            btn.setMinimumHeight(80)

        # ----------------- SLIDERS -----------------
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, 0)
        self.slider.sliderMoved.connect(self.set_position)
        self.slider.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.time_label = QLabel("00:00:00.000")

        # Brightness slider
        self.brightness_slider = QSlider(Qt.Orientation.Vertical)
        self.brightness_slider.setRange(-100, 300)  # very dark to very bright
        self.brightness_slider.setValue(0)
        self.brightness_slider.valueChanged.connect(self.update_brightness)
        self.brightness_label = QLabel("Brightness")

        # ----------------- LOG -----------------
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)

        # ----------------- LAYOUT -----------------
        central_layout = QVBoxLayout()

        # Top bar
        top_bar = QHBoxLayout()
        top_bar.addWidget(self.open_button)
        top_bar.addWidget(self.celebrity_input)
        top_bar.addWidget(self.extract_image_button)
        top_bar.addWidget(self.start_segment_button)
        top_bar.addWidget(self.extract_segment_button)
        top_bar.addWidget(self.accurate_checkbox)
        top_bar.addWidget(self.play_button)
        top_bar.addWidget(self.open_folder_button)
        top_bar.addWidget(self.reset_brightness_button)
        central_layout.addLayout(top_bar)

        # Main area: video on left, log + brightness on right
        main_area = QHBoxLayout()
        video_area = QVBoxLayout()
        
        self.video_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        video_area.addWidget(self.video_widget, 1)
        
        slider_layout = QHBoxLayout()
        slider_layout.addWidget(self.slider)
        slider_layout.addWidget(self.time_label)
        video_area.addLayout(slider_layout)
        
        main_area.addLayout(video_area, 4)

        right_side = QHBoxLayout()
        
        self.log_area.setMaximumWidth(400)
        right_side.addWidget(self.log_area, 2)
        
        brightness_layout = QVBoxLayout()
        brightness_layout.addWidget(self.brightness_label)
        brightness_layout.addWidget(self.brightness_slider)
        brightness_layout.addStretch(1)
        right_side.addLayout(brightness_layout, 1)
        
        main_area.addLayout(right_side, 1)
        central_layout.addLayout(main_area, 1)

        container = QWidget()
        container.setLayout(central_layout)
        self.setCentralWidget(container)
        self.setStatusBar(QStatusBar())

        # ----------------- VARIABLES -----------------
        self.input_file = None
        self.media_name = None
        self.output_path = None
        self.start_time = None
        self.stop_time = None
        self.ffmpeg_brightness = 0.0

        # brightness effect for live preview
        self.brightness_effect = QGraphicsColorizeEffect()
        self.video_widget.setGraphicsEffect(self.brightness_effect)

        # Signals
        self.media_player.positionChanged.connect(self.update_position)
        self.media_player.durationChanged.connect(self.update_duration)

    # ----------------- FUNCTIONS -----------------
    def update_brightness(self, value: int):
        """Real-time brightness update for preview and ffmpeg"""
        self.ffmpeg_brightness = value / 200.0
        factor = max(min(value / 100.0, 3.0), -1.0)
        if factor >= 0:
            self.brightness_effect.setColor(Qt.GlobalColor.white)
            self.brightness_effect.setStrength(factor)
        else:
            self.brightness_effect.setColor(Qt.GlobalColor.black)
            self.brightness_effect.setStrength(-factor)

    def reset_brightness(self):
        """Reset brightness slider and video effect to default"""
        self.brightness_slider.setValue(0)
        self.update_brightness(0)
        self.log("Brightness reset to default")


    def open_file(self):
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        if file_dialog.exec():
            file_path = file_dialog.selectedFiles()[0]
            self.input_file = Path(file_path)
            self.media_player.setSource(QUrl.fromLocalFile(str(self.input_file)))
            self.log(f"Opened: {self.input_file.name}")
            self.media_name = detect_media_name(self.input_file)

    def play_pause(self):
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.pause()
            self.play_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
        else:
            self.media_player.play()
            self.play_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPause))

    def update_position(self, position: int):
        self.slider.setValue(position)
        td = timedelta(milliseconds=position)
        h, rem = divmod(td.seconds, 3600)
        m, s = divmod(rem, 60)
        millis = td.microseconds // 1000
        self.time_label.setText(f"{h:02d}:{m:02d}:{s:02d}.{millis:03d}")

    def update_duration(self, duration: int):
        self.slider.setRange(0, duration)

    def set_position(self, position: int):
        self.media_player.setPosition(position)

    def toggle_segment(self):
        if self.start_time is None:
            self.start_time = self.media_player.position()
            self.start_segment_button.setText("Stop extract Segment (C)")
            self.log(f"Segment start at {format_time(self.start_time)}")
        else:
            self.stop_time = self.media_player.position()
            self.start_segment_button.setText("Start extract Segment (C)")
            self.log(f"Segment stop at {format_time(self.stop_time)}")
            if self.stop_time > self.start_time:
                self.extract_segment_button.setEnabled(True)
            else:
                QMessageBox.warning(self, "Invalid Time", "Stop time must be after start time.")
                self.start_time = None
                self.stop_time = None

    def extract_image(self):
        if not self.input_file: return
        celeb = title_case_name(self.celebrity_input.text().strip())
        if not celeb:
            QMessageBox.warning(self, "Celebrity Missing", "Please enter a celebrity name.")
            return
        self.output_path = build_output_path(celeb)
        if not self.output_path: return

        timestamp = format_time(self.media_player.position())
        outfile = self.output_path / f"{self.media_name}_{timestamp}.jpg"
        position_seconds = self.media_player.position() / 1000.0
        
        cmd = [
            "ffmpeg", "-ss", str(position_seconds), "-i", str(self.input_file),
            "-frames:v", "1", "-q:v", "2", "-pix_fmt", "yuvj420p", "-vsync", "0"
        ]
        
        if self.ffmpeg_brightness != 0:
            cmd.extend(["-vf", f"eq=brightness={self.ffmpeg_brightness}"])
            self.log(f"Applying brightness: {self.ffmpeg_brightness:.2f}")

        cmd.extend(["-y", str(outfile)])
        
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.log(f"Extracted image: {outfile.name}")
        self.statusBar().showMessage(f"Saved {outfile.name}")

    def extract_segment(self):
        if not self.input_file or self.start_time is None or self.stop_time is None: return
        celeb = title_case_name(self.celebrity_input.text().strip())
        if not celeb:
            QMessageBox.warning(self, "Celebrity Missing", "Please enter a celebrity name.")
            return
        self.output_path = build_output_path(celeb)
        if not self.output_path: return

        start = self.start_time / 1000.0
        duration = (self.stop_time - self.start_time) / 1000.0
        timestamp = format_time(self.start_time)
        outfile = self.output_path / f"{self.media_name}_{timestamp}.mkv"

        force_reencode = self.accurate_checkbox.isChecked() or (self.ffmpeg_brightness != 0)

        if not force_reencode:
            self.log("Extracting segment (fast copy mode)...")
            cmd = [
                "ffmpeg", "-ss", str(start), "-i", str(self.input_file),
                "-t", str(duration), "-c", "copy",
                "-avoid_negative_ts", "make_zero", "-y", str(outfile)
            ]
        else:
            log_msg = "Extracting segment (re-encode mode)"
            if self.ffmpeg_brightness != 0:
                log_msg += f" with brightness {self.ffmpeg_brightness:.2f}"
            self.log(log_msg)

            cmd = [
                "ffmpeg", "-ss", str(start), "-i", str(self.input_file),
                "-t", str(duration), "-c:v", "libx264", "-c:a", "aac",
                "-avoid_negative_ts", "make_zero"
            ]

            if self.ffmpeg_brightness != 0:
                cmd.extend(["-vf", f"eq=brightness={self.ffmpeg_brightness}"])
            
            cmd.extend(["-y", str(outfile)])
        
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.log(f"Extracted segment: {outfile.name}")
        self.statusBar().showMessage(f"Saved {outfile.name}")

        self.start_time = None
        self.stop_time = None
        self.extract_segment_button.setEnabled(False)

    def open_output_folder(self):
        if self.output_path and self.output_path.exists():
            os.startfile(self.output_path)
        else:
            celeb = title_case_name(self.celebrity_input.text().strip())
            if celeb:
                path_to_check = build_output_path(celeb)
                if path_to_check and path_to_check.exists():
                    os.startfile(path_to_check)
                    return
            QMessageBox.warning(self, "No Folder", "No output folder exists yet. Extract a file first.")

    def log(self, message: str):
        self.log_area.append(message)

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()
        if key == Qt.Key.Key_Space:
            self.play_pause()
        elif key == Qt.Key.Key_S:
            self.media_player.setPosition(max(0, self.media_player.position() - 5000))
        elif key == Qt.Key.Key_F:
            self.media_player.setPosition(self.media_player.position() + 5000)
        elif key == Qt.Key.Key_Up:
            self.audio_output.setVolume(min(1.0, self.audio_output.volume() + 0.1))
        elif key == Qt.Key.Key_Down:
            self.audio_output.setVolume(max(0.0, self.audio_output.volume() - 0.1))
        elif key == Qt.Key.Key_M:
            self.audio_output.setMuted(not self.audio_output.isMuted())
        elif key == Qt.Key.Key_I:
            self.extract_image()
        elif key == Qt.Key.Key_E:
            if self.extract_segment_button.isEnabled():
                self.extract_segment()
        elif key == Qt.Key.Key_C:
             self.toggle_segment()
        else:
            super().keyPressEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VideoExtractor()
    window.show()
    sys.exit(app.exec())
            