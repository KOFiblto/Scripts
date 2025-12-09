import os
import sys
import json
import shutil
import subprocess
import threading
import time
from datetime import datetime

from PySide6.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QLabel,
    QDialog, QFileDialog, QMessageBox, QListWidget, QLineEdit, QSpinBox, QFormLayout
)
from PySide6.QtCore import Qt, QTimer

CONFIG_FILE = "backup_config.json"
LAST_BACKUP_FILE = "last_backup.json"
LOG_FILE = "backup_errors.log"

# ---------- Helper Functions ----------
def log_error(message: str):
    with open(LOG_FILE, "a") as f:
        f.write(f"[{datetime.now().isoformat()}] {message}\n")

def load_config():
    if not os.path.exists(CONFIG_FILE):
        default_config = {"jobs": []}  # each job: {"source":"", "backup":"", "interval":60, "remote":""}
        save_config(default_config)
        return default_config
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        log_error(f"Error loading config: {e}")
        return {"jobs": []}

def save_config(config):
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        log_error(f"Error saving config: {e}")

def load_last_backup_times():
    if not os.path.exists(LAST_BACKUP_FILE):
        return {}
    try:
        with open(LAST_BACKUP_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        log_error(f"Error reading last backup file: {e}")
        return {}

def save_last_backup_time(job_name):
    last_times = load_last_backup_times()
    last_times[job_name] = datetime.now().isoformat()
    try:
        with open(LAST_BACKUP_FILE, "w") as f:
            json.dump(last_times, f)
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

def perform_backup_job(job):
    source = job.get("source")
    backup = job.get("backup")
    remote = job.get("remote")
    name = f"{source} -> {backup}"

    if not source or not backup:
        log_error(f"Job {name}: Source or backup folder not set.")
        return False
    if not os.path.exists(source):
        log_error(f"Job {name}: Source folder does not exist.")
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
        log_error(f"Job {name}: Error copying files: {e}")
        return False

    try:
        subprocess.run(["git", "add", "."], cwd=backup, check=True)
        commit_message = f"Auto backup {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        subprocess.run(["git", "commit", "-m", commit_message], cwd=backup, check=True)
        if remote:
            subprocess.run(["git", "push", "-u", "origin", "master"], cwd=backup, check=True)
        save_last_backup_time(name)
        return True
    except subprocess.CalledProcessError as e:
        log_error(f"Job {name}: Git error: {e}")
        return False

# ---------- Settings Dialog ----------
class JobSettingsDialog(QDialog):
    def __init__(self, config):
        super().__init__()
        self.setWindowTitle("Backup Jobs Settings")
        self.config = config
        self.setMinimumSize(700, 400)

        self.layout = QVBoxLayout()
        self.job_list = QListWidget()
        for job in config.get("jobs", []):
            self.job_list.addItem(f"{job['source']} -> {job['backup']}")
        self.layout.addWidget(QLabel("Backup Jobs:"))
        self.layout.addWidget(self.job_list)

        btn_layout = QHBoxLayout()
        add_btn = QPushButton("Add Job")
        add_btn.clicked.connect(self.add_job)
        remove_btn = QPushButton("Remove Selected Job")
        remove_btn.clicked.connect(self.remove_job)
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(remove_btn)
        self.layout.addLayout(btn_layout)

        save_btn = QPushButton("Save and Close")
        save_btn.clicked.connect(self.save_and_close)
        self.layout.addWidget(save_btn)

        self.setLayout(self.layout)

    def add_job(self):
        dlg = SingleJobDialog()
        if dlg.exec():
            job = dlg.get_job()
            self.config["jobs"].append(job)
            self.job_list.addItem(f"{job['source']} -> {job['backup']}")

    def remove_job(self):
        idx = self.job_list.currentRow()
        if idx >= 0:
            self.job_list.takeItem(idx)
            del self.config["jobs"][idx]

    def save_and_close(self):
        save_config(self.config)
        QMessageBox.information(self, "Saved", "Backup jobs saved successfully!")
        self.accept()

class SingleJobDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("New Backup Job")
        self.setMinimumSize(500, 300)
        self.layout = QFormLayout()

        self.src_edit = QLineEdit()
        src_btn = QPushButton("Browse")
        src_btn.clicked.connect(lambda: self.browse_folder(self.src_edit))
        self.layout.addRow("Source Folder:", self._with_button(self.src_edit, src_btn))

        self.dst_edit = QLineEdit()
        dst_btn = QPushButton("Browse")
        dst_btn.clicked.connect(lambda: self.browse_folder(self.dst_edit))
        self.layout.addRow("Backup Folder:", self._with_button(self.dst_edit, dst_btn))

        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1, 1440)
        self.interval_spin.setValue(60)
        self.layout.addRow("Interval (minutes):", self.interval_spin)

        self.remote_edit = QLineEdit()
        self.layout.addRow("Remote Git Repo (optional):", self.remote_edit)

        save_btn = QPushButton("Add Job")
        save_btn.clicked.connect(self.accept)
        self.layout.addRow(save_btn)
        self.setLayout(self.layout)

    def _with_button(self, widget, button):
        container = QWidget()
        hbox = QHBoxLayout()
        hbox.setContentsMargins(0, 0, 0, 0)
        hbox.addWidget(widget)
        hbox.addWidget(button)
        container.setLayout(hbox)
        return container

    def browse_folder(self, line_edit):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            line_edit.setText(folder)

    def get_job(self):
        return {
            "source": self.src_edit.text(),
            "backup": self.dst_edit.text(),
            "interval": self.interval_spin.value(),
            "remote": self.remote_edit.text()
        }

# ---------- Main Application ----------
class BackupApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Auto Backup")
        self.setMinimumSize(600, 400)
        self.config = load_config()
        self.layout = QVBoxLayout()

        self.backup_btn = QPushButton("BACKUP NOW")
        self.backup_btn.setMinimumHeight(100)
        self.backup_btn.setStyleSheet("font-size: 30px;")
        self.backup_btn.clicked.connect(self.backup_now)
        self.layout.addWidget(self.backup_btn)

        self.settings_btn = QPushButton("Settings")
        self.settings_btn.setMinimumHeight(70)
        self.settings_btn.setStyleSheet("font-size: 24px;")
        self.settings_btn.clicked.connect(self.open_settings)
        self.layout.addWidget(self.settings_btn)

        self.exit_btn = QPushButton("Exit")
        self.exit_btn.setMinimumHeight(70)
        self.exit_btn.setStyleSheet("font-size: 24px;")
        self.exit_btn.clicked.connect(self.close)
        self.layout.addWidget(self.exit_btn)

        self.setLayout(self.layout)

        self.start_backup_timer()

    def backup_now(self):
        if not self.config.get("jobs"):
            QMessageBox.warning(self, "No Jobs", "No backup jobs configured!")
            return
        success_count = 0
        for job in self.config["jobs"]:
            if perform_backup_job(job):
                success_count += 1
        QMessageBox.information(self, "Backup Complete", f"{success_count}/{len(self.config['jobs'])} jobs backed up successfully.")

    def open_settings(self):
        dialog = JobSettingsDialog(self.config)
        dialog.exec()
        self.config = load_config()  # reload updated jobs

    def start_backup_timer(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.auto_backup)
        self.timer.start(60 * 1000)  # every 60 sec

    def auto_backup(self):
        last_times = load_last_backup_times()
        now = datetime.now()
        for job in self.config.get("jobs", []):
            name = f"{job['source']} -> {job['backup']}"
            interval = job.get("interval", 60)
            last_time_str = last_times.get(name)
            last_time = datetime.fromisoformat(last_time_str) if last_time_str else None
            if not last_time or (now - last_time).total_seconds() >= interval * 60:
                perform_backup_job(job)

# ---------- Run ----------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BackupApp()
    window.show()
    sys.exit(app.exec())
