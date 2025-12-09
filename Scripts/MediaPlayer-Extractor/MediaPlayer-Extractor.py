import sys
import os
import subprocess
import shlex
from pathlib import Path
from datetime import timedelta

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFileDialog, QLabel, QPushButton,
    QLineEdit, QTextEdit, QVBoxLayout, QHBoxLayout, QSlider, QRadioButton,
    QButtonGroup, QCheckBox, QMessageBox, QStyle, QStatusBar
)
from PySide6.QtCore import Qt, QUrl, QTimer
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget

ROOT_FOLDER = r"C:\\_other\\Celebs\\MediaPlayer-Extractor"
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

        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)

        self.video_widget = QVideoWidget()
        self.media_player.setVideoOutput(self.video_widget)

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

        self.play_button = QPushButton()
        self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.play_button.clicked.connect(self.play_pause)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 0)
        self.slider.sliderMoved.connect(self.set_position)

        self.time_label = QLabel("00:00:00.000")

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Layouts
        left_layout = QVBoxLayout()
        left_layout.addWidget(self.video_widget)
        control_layout = QHBoxLayout()
        control_layout.addWidget(self.play_button)
        control_layout.addWidget(self.slider)
        control_layout.addWidget(self.time_label)
        left_layout.addLayout(control_layout)

        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("Scene name:"))
        right_layout.addWidget(self.scene_name_input)
        right_layout.addWidget(self.extract_image_button)
        right_layout.addWidget(self.start_segment_button)
        right_layout.addWidget(self.extract_segment_button)
        right_layout.addWidget(self.accurate_checkbox)
        right_layout.addWidget(QLabel("Log:"))
        right_layout.addWidget(self.log_area)

        top_layout = QHBoxLayout()
        top_layout.addWidget(self.open_button)
        top_layout.addWidget(self.mode_movie)
        top_layout.addWidget(self.mode_series)

        main_layout = QHBoxLayout()
        main_layout.addLayout(left_layout, 3)
        main_layout.addLayout(right_layout, 1)

        wrapper = QVBoxLayout()
        wrapper.addLayout(top_layout)
        wrapper.addLayout(main_layout)

        container = QWidget()
        container.setLayout(wrapper)
        self.setCentralWidget(container)

        # State
        self.input_file = None
        self.media_name = None
        self.output_folder = None
        self.segment_start = None
        self.segment_stop = None

        # Signals
        self.media_player.positionChanged.connect(self.update_position)
        self.media_player.durationChanged.connect(self.update_duration)

    def log(self, msg: str):
        self.log_area.append(msg)
        self.status_bar.showMessage(msg)

    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Video File")
        if not file_path:
            return
        self.input_file = Path(file_path)
        mode = "Movie" if self.mode_movie.isChecked() else "Series"
        if mode == "Movie":
            self.media_name = self.input_file.parent.name
        else:
            try:
                self.media_name = self.input_file.parent.parent.name
            except Exception:
                self.media_name = self.input_file.parent.name
        self.media_name = sanitize_filename(self.media_name)
        self.output_folder = build_output_path(self.input_file, mode, self.media_name)
        self.media_player.setSource(QUrl.fromLocalFile(str(self.input_file)))
        self.log(f"Opened file: {self.input_file}")
        self.log(f"Media name: {self.media_name}")
        self.log(f"Output folder: {self.output_folder}")

    def play_pause(self):
        if self.media_player.playbackState() == QMediaPlayer.PlayingState:
            self.media_player.pause()
            self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        else:
            self.media_player.play()
            self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))

    def update_position(self, position):
        self.slider.setValue(position)
        ms = position
        td = timedelta(milliseconds=ms)
        h, rem = divmod(td.seconds, 3600)
        m, s = divmod(rem, 60)
        millis = td.microseconds // 1000
        self.time_label.setText(f"{h:02d}:{m:02d}:{s:02d}.{millis:03d}")

    def update_duration(self, duration):
        self.slider.setRange(0, duration)

    def set_position(self, position):
        self.media_player.setPosition(position)

    def current_time_str(self):
        return self.time_label.text()

    def current_time_for_filename(self):
        return format_time(self.media_player.position())

    def extract_image(self):
        if not self.input_file:
            return
        scene_name = sanitize_filename(self.scene_name_input.text() or "Scene")
        timestamp = self.current_time_for_filename()
        outfile = self.output_folder / f"{scene_name}_{timestamp}.jpg"
        cmd = f'ffmpeg -ss {self.current_time_str()} -i "{self.input_file}" -frames:v 1 -q:v 2 -y "{outfile}"'
        self.run_ffmpeg(cmd, outfile)

    def toggle_segment(self):
        if self.segment_start is None:
            self.segment_start = self.media_player.position()
            self.start_segment_button.setText("Stop extract Segment (S)")
            self.log(f"Segment start: {self.current_time_str()}")
        else:
            self.segment_stop = self.media_player.position()
            if self.segment_stop <= self.segment_start:
                QMessageBox.warning(self, "Error", "Stop time must be greater than start time")
                return
            self.start_segment_button.setText("Start extract Segment (S)")
            self.extract_segment_button.setEnabled(True)
            self.log(f"Segment stop: {self.current_time_str()}")

    def extract_segment(self):
        if not (self.segment_start and self.segment_stop):
            return
        scene_name = sanitize_filename(self.scene_name_input.text() or "Scene")
        start_str = format_time(self.segment_start)
        stop_str = format_time(self.segment_stop)
        outfile = self.output_folder / f"{scene_name}_{start_str}.mkv"
        start_tc = self.ms_to_ffmpeg_time(self.segment_start)
        stop_tc = self.ms_to_ffmpeg_time(self.segment_stop)
        if self.accurate_checkbox.isChecked():
            cmd = f'ffmpeg -ss {start_tc} -i "{self.input_file}" -to {stop_tc} -c:v libx264 -crf 18 -preset veryfast -c:a aac -b:a 192k -y "{outfile}"'
        else:
            cmd = f'ffmpeg -ss {start_tc} -to {stop_tc} -i "{self.input_file}" -c copy -avoid_negative_ts 1 -y "{outfile}"'
        self.run_ffmpeg(cmd, outfile)
        self.segment_start = None
        self.segment_stop = None
        self.extract_segment_button.setEnabled(False)

    def ms_to_ffmpeg_time(self, ms: int) -> str:
        td = timedelta(milliseconds=ms)
        h, rem = divmod(td.seconds, 3600)
        m, s = divmod(rem, 60)
        millis = td.microseconds // 1000
        return f"{h:02d}:{m:02d}:{s:02d}.{millis:03d}"

    def run_ffmpeg(self, cmd, outfile):
        self.log(f"Running: {cmd}")
        try:
            subprocess.run(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            self.log(f"Saved: {outfile}")
        except subprocess.CalledProcessError as e:
            self.log(f"Error: {e.stderr.decode(errors='ignore')}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = VideoExtractor()
    win.show()
    sys.exit(app.exec())
