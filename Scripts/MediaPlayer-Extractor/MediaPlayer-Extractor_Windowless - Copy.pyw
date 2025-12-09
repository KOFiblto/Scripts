import sys
import os
import subprocess
import datetime
import re
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout,
    QLabel, QFileDialog, QSlider, QTextEdit, QLineEdit, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer, QUrl
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget

# ---- Config ----
BASE_DIR = Path(r"D:\_other\Celebs\Celebs")
SEGMENT_MODES = ["fast", "accurate"]

# ---- Helpers ----
def sanitize_filename(name):
    return re.sub(r'[\\/:*?"<>|]', "_", name)

def format_timestamp(ms):
    seconds, ms = divmod(ms, 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{int(hours):02d}-{int(minutes):02d}-{int(seconds):02d}_{int(ms):03d}"

# ---- Main App ----
class MediaTagger(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Celebrity Media Tagger")
        self.resize(1200, 700)

        # Media player setup
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.video_widget = QVideoWidget()
        self.player.setVideoOutput(self.video_widget)

        # State
        self.current_file = None
        self.celebrity_name = ""
        self.start_time = None
        self.stop_time = None
        self.brightness = 0.0  # default 0
        self.segment_mode = "accurate"

        # Layouts
        self.init_ui()
        self.init_timers()
        self.init_shortcuts()

    def init_ui(self):
        # Top buttons
        top_layout = QHBoxLayout()
        self.open_btn = QPushButton("Open File")
        self.celebrity_input = QLineEdit()
        self.celebrity_input.setPlaceholderText("Enter celebrity name")
        self.extract_img_btn = QPushButton("Extract Image")
        self.start_stop_seg_btn = QPushButton("Start/Stop Segment")
        self.extract_seg_btn = QPushButton("Extract Segment")
        self.toggle_bright_btn = QPushButton("Toggle Brightness Preview")
        self.play_pause_btn = QPushButton("Play/Pause")
        self.open_folder_btn = QPushButton("Open Output Folder")
        self.reset_bright_btn = QPushButton("Reset Brightness")

        top_layout.addWidget(self.open_btn)
        top_layout.addWidget(self.celebrity_input)
        top_layout.addWidget(self.extract_img_btn)
        top_layout.addWidget(self.start_stop_seg_btn)
        top_layout.addWidget(self.extract_seg_btn)
        top_layout.addWidget(self.toggle_bright_btn)
        top_layout.addWidget(self.play_pause_btn)
        top_layout.addWidget(self.open_folder_btn)
        top_layout.addWidget(self.reset_bright_btn)

        # Video + right panel
        main_layout = QHBoxLayout()
        right_panel = QVBoxLayout()
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.brightness_slider = QSlider(Qt.Orientation.Vertical)
        self.brightness_slider.setRange(-100, 100)
        self.brightness_slider.setValue(0)
        self.brightness_slider.setTickInterval(10)

        right_panel.addWidget(QLabel("Log"))
        right_panel.addWidget(self.log_area)
        right_panel.addWidget(QLabel("Brightness"))
        right_panel.addWidget(self.brightness_slider)

        main_layout.addWidget(self.video_widget, 4)
        main_layout.addLayout(right_panel, 1)

        # Bottom slider
        bottom_layout = QHBoxLayout()
        self.position_slider = QSlider(Qt.Orientation.Horizontal)
        bottom_layout.addWidget(self.position_slider)

        # Combine layouts
        layout = QVBoxLayout()
        layout.addLayout(top_layout)
        layout.addLayout(main_layout)
        layout.addLayout(bottom_layout)
        self.setLayout(layout)

        # Connect buttons
        self.open_btn.clicked.connect(self.open_file)
        self.extract_img_btn.clicked.connect(self.extract_image)
        self.start_stop_seg_btn.clicked.connect(self.start_stop_segment)
        self.extract_seg_btn.clicked.connect(self.extract_segment)
        self.play_pause_btn.clicked.connect(self.toggle_play)
        self.open_folder_btn.clicked.connect(self.open_output_folder)
        self.reset_bright_btn.clicked.connect(self.reset_brightness)
        self.brightness_slider.valueChanged.connect(self.update_brightness)
        self.position_slider.sliderReleased.connect(self.seek_position)

    def init_timers(self):
        self.timer = QTimer()
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.update_position)
        self.timer.start()

    def init_shortcuts(self):
        self.key_map = {
            Qt.Key.Key_Space: self.toggle_play,
            Qt.Key.Key_S: lambda: self.skip_seconds(-5),
            Qt.Key.Key_F: lambda: self.skip_seconds(5),
            Qt.Key.Key_Up: lambda: self.adjust_volume(5),
            Qt.Key.Key_Down: lambda: self.adjust_volume(-5),
            Qt.Key.Key_M: self.mute_toggle,
            Qt.Key.Key_I: self.extract_image,
            Qt.Key.Key_C: self.start_stop_segment,
            Qt.Key.Key_E: self.extract_segment
        }

    # ---- Actions ----
    def keyPressEvent(self, event):
        func = self.key_map.get(event.key())
        if func:
            func()

    def open_file(self):
        file, _ = QFileDialog.getOpenFileName(self, "Open Media", "", "Videos (*.mp4 *.mkv *.avi *.mov)")
        if file:
            self.current_file = Path(file)
            self.player.setSource(QUrl.fromLocalFile(file))
            self.log(f"Opened file: {file}")

    def toggle_play(self):
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
        else:
            self.player.play()

    def skip_seconds(self, seconds):
        self.player.setPosition(self.player.position() + seconds * 1000)

    def adjust_volume(self, delta):
        vol = max(0, min(100, self.audio_output.volume()*100 + delta))
        self.audio_output.setVolume(vol / 100)

    def mute_toggle(self):
        self.audio_output.setMuted(not self.audio_output.isMuted())

    def update_position(self):
        if self.player.duration() > 0:
            self.position_slider.setValue(int(self.player.position() / self.player.duration() * 100))
        # update log with time if desired

    def seek_position(self):
        if self.player.duration() > 0:
            pos = self.position_slider.value() / 100 * self.player.duration()
            self.player.setPosition(int(pos))

    def update_brightness(self):
        self.brightness = self.brightness_slider.value() / 100
        # Could implement real-time preview if desired
        self.log(f"Brightness set to {self.brightness:.2f}")

    def reset_brightness(self):
        self.brightness_slider.setValue(0)
        self.brightness = 0
        self.log("Brightness reset")

    def start_stop_segment(self):
        pos = self.player.position()
        if not self.start_time:
            self.start_time = pos
            self.log(f"Segment start set at {format_timestamp(pos)}")
        else:
            self.stop_time = pos
            self.log(f"Segment stop set at {format_timestamp(pos)}")

    def extract_image(self):
        if not self.current_file:
            self.log("No file open")
            return
        celeb = self.get_celebrity_folder()
        if not celeb:
            return
        timestamp = format_timestamp(self.player.position())
        media_name = sanitize_filename(self.current_file.stem)
        output_file = celeb / f"{media_name}_{timestamp}.jpg"
        cmd = [
            "ffmpeg", "-y", "-i", str(self.current_file),
            "-ss", str(self.player.position()/1000),
            "-vframes", "1"
        ]
        if self.brightness != 0:
            cmd += ["-vf", f"eq=brightness={self.brightness}"]
        cmd.append(str(output_file))
        self.run_ffmpeg(cmd, f"Image saved: {output_file}")

    def extract_segment(self):
        if not self.current_file or not self.start_time or not self.stop_time or self.stop_time <= self.start_time:
            self.log("Invalid segment")
            return
        celeb = self.get_celebrity_folder()
        if not celeb:
            return
        timestamp = f"{format_timestamp(self.start_time)}_{format_timestamp(self.stop_time)}"
        media_name = sanitize_filename(self.current_file.stem)
        output_file = celeb / f"{media_name}_{timestamp}.mkv"
        if self.segment_mode == "fast":
            cmd = [
                "ffmpeg", "-y", "-i", str(self.current_file),
                "-ss", str(self.start_time/1000),
                "-to", str(self.stop_time/1000),
                "-c", "copy",
                str(output_file)
            ]
        else:
            cmd = [
                "ffmpeg", "-y", "-i", str(self.current_file),
                "-ss", str(self.start_time/1000),
                "-to", str(self.stop_time/1000)
            ]
            if self.brightness != 0:
                cmd += ["-vf", f"eq=brightness={self.brightness}"]
            cmd.append(str(output_file))
        self.run_ffmpeg(cmd, f"Segment saved: {output_file}")
        self.start_time = None
        self.stop_time = None

    def run_ffmpeg(self, cmd, success_msg):
        self.log(f"Running: {' '.join(cmd)}")
        try:
            subprocess.run(cmd, check=True)
            self.log(success_msg)
        except subprocess.CalledProcessError:
            self.log("Error during ffmpeg execution")

    def get_celebrity_folder(self):
        name = self.celebrity_input.text().strip()
        if not name:
            self.log("Enter celebrity name")
            return None
        folder = BASE_DIR / sanitize_filename(name)
        if not folder.exists():
            reply = QMessageBox.question(self, "Create Folder?", f"Folder {folder} does not exist. Create it?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                folder.mkdir(parents=True)
                self.log(f"Created folder: {folder}")
            else:
                return None
        return folder

    def open_output_folder(self):
        celeb = self.get_celebrity_folder()
        if celeb:
            os.startfile(celeb)

    def log(self, message):
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        self.log_area.append(f"[{ts}] {message}")

# ---- Run App ----
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MediaTagger()
    window.show()
    sys.exit(app.exec())
