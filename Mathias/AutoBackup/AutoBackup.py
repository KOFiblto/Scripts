import os
import sys
import json
import shutil
import subprocess
import threading
import time
from datetime import datetime

from PySide6.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QFileDialog,
    QLineEdit, QLabel, QDialog, QFormLayout, QMessageBox, QSpinBox
)
from PySide6.QtCore import Qt, QTimer

# ---------- Constants ----------
CONFIG_FILE = "backup_config.json"
LAST_BACKUP_FILE = "last_backup.txt"
LOG_FILE = "backup_errors.log"

# ---------- Helper Functions ----------
def log_error(message: str):
    with open(LOG_FILE, "a") as f:
        f.write(f"[{datetime.now().isoformat()}] {message}\n")

def load_config():
    if not os.path.exists(CONFIG_FILE):
        default_config = {
            "source_folder": "",
            "backup_folder": "",
            "interval_minutes": 60,
            "remote_repo": ""
        }
        save_config(default_config)
        return default_config
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        log_error(f"Error loading config: {e}")
        return None

def save_config(config: dict):
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        log_error(f"Error saving config: {e}")

def load_last_backup_time():
    if not os.path.exists(LAST_BACKUP_FILE):
        return None
    try:
        with open(LAST_BACKUP_FILE, "r") as f:
            ts = f.read().strip()
            return datetime.fromisoformat(ts)
    except Exception as e:
        log_error(f"Error reading last backup time: {e}")
        return None

def save_last_backup_time():
    try:
        with open(LAST_BACKUP_FILE, "w") as f:
            f.write(datetime.now().isoformat())
    except Exception as e:
        log_error(f"Error saving last backup time: {e}")

def init_git_repo(backup_folder: str, remote_repo: str = None):
    if not os.path.exists(os.path.join(backup_folder, ".git")):
        try:
            subprocess.run(["git", "init"], cwd=backup_folder, check=True)
            subprocess.run(["git", "lfs", "install"], cwd=backup_folder, check=True)
            if remote_repo:
                subprocess.run(["git", "remote", "add", "origin", remote_repo], cwd=backup_folder, check=True)
        except Exception as e:
            log_error(f"Error initializing Git repo: {e}")

def perform_backup(config: dict):
    source = config.get("source_folder")
    backup = config.get("backup_folder")
    remote = config.get("remote_repo")

    if not source or not backup:
        log_error("Source or backup folder not set.")
        return False

    if not os.path.exists(source):
        log_error(f"Source folder does not exist: {source}")
        return False

    os.makedirs(backup, exist_ok=True)
    init_git_repo(backup, remote)

    try:
        for item in os.listdir(source):
            s_path = os.path.join(source, item)
            d_path = os.path.join(backup, item)
            if os.path.isdir(s_path):
                shutil.copytree(s_path, d_path, dirs_exist_ok=True)
            else:
                shutil.copy2(s_path, d_path)
    except Exception as e:
        log_error(f"Error copying files: {e}")
        return False

    try:
        subprocess.run(["git", "add", "."], cwd=backup, check=True)
        commit_message = f"Auto backup {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        subprocess.run(["git", "commit", "-m", commit_message], cwd=backup, check=True)
        if remote:
            subprocess.run(["git", "push", "-u", "origin", "master"], cwd=backup, check=True)
        save_last_backup_time()
        return True
    except subprocess.CalledProcessError as e:
        log_error(f"Git error: {e}")
        return False

# ---------- Settings Dialog ----------
class SettingsDialog(QDialog):
    def __init__(self, config):
        super().__init__()
        self.setWindowTitle("Backup Settings")
        self.config = config
        layout = QFormLayout()

        self.src_edit = QLineEdit(config.get("source_folder", ""))
        src_btn = QPushButton("Browse")
        src_btn.clicked.connect(lambda: self.browse_folder(self.src_edit))
        layout.addRow("Source Folder:", self._with_button(self.src_edit, src_btn))

        self.dst_edit = QLineEdit(config.get("backup_folder", ""))
        dst_btn = QPushButton("Browse")
        dst_btn.clicked.connect(lambda: self.browse_folder(self.dst_edit))
        layout.addRow("Backup Folder:", self._with_button(self.dst_edit, dst_btn))

        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1, 1440)
        self.interval_spin.setValue(config.get("interval_minutes", 60))
        layout.addRow("Backup Interval (minutes):", self.interval_spin)

        self.remote_edit = QLineEdit(config.get("remote_repo", ""))
        layout.addRow("Remote Git Repo (optional):", self.remote_edit)

        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_settings)
        layout.addRow(save_btn)

        self.setLayout(layout)

    def _with_button(self, widget, button):
        container = QWidget()
        hbox = QVBoxLayout() if False else QVBoxLayout()
        hbox.setContentsMargins(0, 0, 0, 0)
        hbox.addWidget(widget)
        hbox.addWidget(button)
        container.setLayout(hbox)
        return container

    def browse_folder(self, line_edit):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            line_edit.setText(folder)

    def save_settings(self):
        self.config["source_folder"] = self.src_edit.text()
        self.config["backup_folder"] = self.dst_edit.text()
        self.config["interval_minutes"] = self.interval_spin.value()
        self.config["remote_repo"] = self.remote_edit.text()
        save_config(self.config)
        QMessageBox.information(self, "Settings Saved", "Configuration saved successfully!")
        self.accept()

# ---------- Main Application ----------
class BackupApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Auto Backup")
        self.setFixedSize(300, 200)
        self.config = load_config()
        self.layout = QVBoxLayout()

        self.backup_btn = QPushButton("Backup Now")
        self.backup_btn.clicked.connect(self.backup_now)
        self.layout.addWidget(self.backup_btn)

        self.settings_btn = QPushButton("Settings")
        self.settings_btn.clicked.connect(self.open_settings)
        self.layout.addWidget(self.settings_btn)

        self.exit_btn = QPushButton("Exit")
        self.exit_btn.clicked.connect(self.close)
        self.layout.addWidget(self.exit_btn)

        self.setLayout(self.layout)

        self.start_backup_timer()

    def backup_now(self):
        success = perform_backup(self.config)
        if success:
            QMessageBox.information(self, "Backup Complete", f"Backup completed successfully at {datetime.now().strftime('%H:%M:%S')}")
        else:
            QMessageBox.warning(self, "Backup Failed", "Backup failed. Check the log file.")

    def open_settings(self):
        dialog = SettingsDialog(self.config)
        dialog.exec()
        self.config = load_config()  # reload updated settings

    def start_backup_timer(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.auto_backup)
        self.timer.start(60 * 1000)  # check every 60 seconds

    def auto_backup(self):
        last_backup = load_last_backup_time()
        interval = self.config.get("interval_minutes", 60)
        now = datetime.now()
        if not last_backup or (now - last_backup).total_seconds() >= interval * 60:
            perform_backup(self.config)

# ---------- Run ----------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BackupApp()
    window.show()
    sys.exit(app.exec())
