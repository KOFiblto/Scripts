import sys
import os
import subprocess
from pathlib import Path
from datetime import timedelta

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFileDialog, QLabel, QPushButton,
    QLineEdit, QTextEdit, QVBoxLayout, QHBoxLayout, QRadioButton,
    QButtonGroup, QCheckBox, QMessageBox, QStyle, QStatusBar, QSlider
)
from PySide6.QtCore import Qt, QUrl
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget

ROOT_FOLDER = r"C:\\Extractor"
ILLEGAL_CHARS = ['\\', '/', ':', '*', '?', '"', '<', '>', '|']


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


def build_output_path(input_file: Path, mode: str, media_name: str) -> Path:
    base = Path(ROOT_FOLDER) / media_name
    base.mkdir(parents=True, exist_ok=True)
    return base


class VideoExtractor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video Extractor")
        self.resize(1200, 800)

        # Media player
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)

        self.video_widget = QVideoWidget()
        self.media_player.setVideoOutput(self.video_widget)

        # Buttons
        self.open_button = QPushButton("Open File")
        self.open_button.clicked.connect(self.open_file)

        self.mode_movie = QRadioButton("Movie")
        self.mode_series = QRadioButton("Series")
        self.mode_movie.setChecked(True)
        self.mode_group = QButtonGroup()
        self.mode_group.addButton(self.mode_movie)
        self.mode_group.addButton(self.mode_series)

        self.scene_name_input = QLineEdit()
        self.scene_name_input.setPlaceholderText("Scene name")

        self.extract_image_button = QPushButton("Extract Image (I)")
        self.extract_image_button.clicked.connect(self.extract_image)

        self.start_segment_button = QPushButton("Start extract Segment (S)")
        self.start_segment_button.clicked.connect(self.toggle_segment)

        self.extract_segment_button = QPushButton("Extract Segment (E)")
        self.extract_segment_button.setEnabled(False)
        self.extract_segment_button.clicked.connect(self.extract_segment)

        self.accurate_checkbox = QCheckBox("Accurate (re-encode)")
        self.accurate_checkbox.setChecked(True)

        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)

        # Play/pause with icon
        self.play_button = QPushButton()
        self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.play_button.clicked.connect(self.play_pause)

        # Open folder
        self.open_folder_button = QPushButton("Open Output Folder")
        self.open_folder_button.clicked.connect(self.open_output_folder)

        # Timeline slider + label
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 0)
        self.slider.sliderMoved.connect(self.set_position)
        self.slider.setFocusPolicy(Qt.NoFocus)  # ✅ prevent arrow keys being stolen
        self.time_label = QLabel("00:00:00.000")

        # Make buttons bigger
        for btn in [self.open_button, self.extract_image_button, self.start_segment_button,
                    self.extract_segment_button, self.play_button, self.open_folder_button]:
            btn.setMinimumHeight(40)

        # Layouts
        left_layout = QVBoxLayout()
        left_layout.addWidget(self.video_widget)

        control_layout = QHBoxLayout()
        control_layout.addWidget(self.play_button)
        control_layout.addWidget(self.slider)
        control_layout.addWidget(self.time_label)

        left_layout.addLayout(control_layout)

        right_layout = QVBoxLayout()
        right_layout.addWidget(self.open_button)
        right_layout.addWidget(self.mode_movie)
        right_layout.addWidget(self.mode_series)
        right_layout.addWidget(self.scene_name_input)
        right_layout.addWidget(self.extract_image_button)
        right_layout.addWidget(self.start_segment_button)
        right_layout.addWidget(self.extract_segment_button)
        right_layout.addWidget(self.accurate_checkbox)
        right_layout.addWidget(self.open_folder_button)
        right_layout.addWidget(self.log_area)

        main_layout = QHBoxLayout()
        main_layout.addLayout(left_layout, 3)
        main_layout.addLayout(right_layout, 1)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        self.setStatusBar(QStatusBar())

        # Extraction variables
        self.input_file = None
        self.media_name = None
        self.output_path = None
        self.start_time = None
        self.stop_time = None

        # Connect player signals for timeline
        self.media_player.positionChanged.connect(self.update_position)
        self.media_player.durationChanged.connect(self.update_duration)

    def open_file(self):
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        if file_dialog.exec():
            file_path = file_dialog.selectedFiles()[0]
            self.input_file = Path(file_path)

            # ✅ FIXED: use QUrl.fromLocalFile
            self.media_player.setSource(QUrl.fromLocalFile(str(self.input_file)))
            self.log(f"Opened: {self.input_file.name}")

            # Compute media name
            if self.mode_movie.isChecked():
                self.media_name = sanitize_filename(self.input_file.parent.name)
            else:
                try:
                    self.media_name = sanitize_filename(self.input_file.parent.parent.name)
                except Exception:
                    self.media_name = sanitize_filename(self.input_file.parent.name)

            self.output_path = build_output_path(self.input_file, "mode", self.media_name)
            self.log(f"Output folder: {self.media_name}")

    def play_pause(self):
        if self.media_player.playbackState() == QMediaPlayer.PlayingState:
            self.media_player.pause()
            self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        else:
            self.media_player.play()
            self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))

    def update_position(self, position):
        self.slider.setValue(position)
        td = timedelta(milliseconds=position)
        h, rem = divmod(td.seconds, 3600)
        m, s = divmod(rem, 60)
        millis = td.microseconds // 1000
        self.time_label.setText(f"{h:02d}:{m:02d}:{s:02d}.{millis:03d}")

    def update_duration(self, duration):
        self.slider.setRange(0, duration)

    def set_position(self, position):
        self.media_player.setPosition(position)

    def toggle_segment(self):
        if self.start_time is None:
            self.start_time = self.media_player.position()
            self.start_segment_button.setText("Stop extract Segment (S)")
            self.log(f"Segment start at {format_time(self.start_time)}")
        else:
            self.stop_time = self.media_player.position()
            self.start_segment_button.setText("Start extract Segment (S)")
            self.log(f"Segment stop at {format_time(self.stop_time)}")
            if self.stop_time > self.start_time:
                self.extract_segment_button.setEnabled(True)
            else:
                QMessageBox.warning(self, "Invalid", "Stop time must be after start time")
                self.start_time = None
                self.stop_time = None

    def extract_image(self):
        if not self.input_file:
            return
        pos = self.media_player.position()
        timestamp = format_time(pos)
        scene = sanitize_filename(self.scene_name_input.text() or "Scene")
        movie = self.media_name
        outfile = self.output_path / f"{scene} - {movie}_{timestamp}.jpg"

        cmd = [
            "ffmpeg", "-ss", str(pos/1000), "-i", str(self.input_file),
            "-frames:v", "1", "-q:v", "2", "-pix_fmt", "yuvj420p", "-y", str(outfile)
        ]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.log(f"Extracted image: {outfile.name}")
        self.statusBar().showMessage(f"Saved {outfile.name}")

    def extract_segment(self):
        if not self.input_file or self.start_time is None or self.stop_time is None:
            return
        start = self.start_time / 1000
        stop = self.stop_time / 1000
        timestamp = format_time(self.start_time)
        scene = sanitize_filename(self.scene_name_input.text() or "Scene")
        movie = self.media_name
        outfile = self.output_path / f"{scene} - {movie}_{timestamp}.mkv"

        duration = stop - start

        if self.accurate_checkbox.isChecked():
            cmd = [
                "ffmpeg", "-ss", str(start),
                "-i", str(self.input_file),
                "-t", str(duration),
                "-c:v", "libx264", "-c:a", "aac",
                "-y", str(outfile)
            ]
        else:
            cmd = [
                "ffmpeg", "-ss", str(start),
                "-i", str(self.input_file),
                "-t", str(duration),
                "-c", "copy",
                "-avoid_negative_ts", "1",
                "-y", str(outfile)
            ]

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
            QMessageBox.warning(self, "No Folder", "No output folder exists yet.")

    def log(self, message: str):
        self.log_area.append(message)

    # Keyboard shortcuts
    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Space:  # Pause/Play
            self.play_pause()
        elif key == Qt.Key_Left:  # -10s
            self.media_player.setPosition(max(0, self.media_player.position() - 10000))
        elif key == Qt.Key_Right:  # +10s
            self.media_player.setPosition(self.media_player.position() + 10000)
        elif key == Qt.Key_Comma:  # prev frame (~40ms back)
            self.media_player.setPosition(max(0, self.media_player.position() - 40))
        elif key == Qt.Key_Period:  # next frame
            self.media_player.setPosition(self.media_player.position() + 40)
        elif key == Qt.Key_Up:  # volume up
            vol = self.audio_output.volume() + 0.1
            self.audio_output.setVolume(min(1.0, vol))
        elif key == Qt.Key_Down:  # volume down
            vol = self.audio_output.volume() - 0.1
            self.audio_output.setVolume(max(0.0, vol))
        elif key == Qt.Key_M:  # mute toggle
            self.audio_output.setMuted(not self.audio_output.isMuted())
        else:
            super().keyPressEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VideoExtractor()
    window.show()
    sys.exit(app.exec())
