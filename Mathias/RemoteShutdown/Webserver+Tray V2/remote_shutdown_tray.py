import sys
import os
import socket
import time
import threading
import webbrowser
import logging

from PySide6.QtCore import QTimer, Qt, Signal, QObject
from PySide6.QtGui import QIcon, QAction
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu

import faulthandler


# =========================================
# =========== F U N C T I O N S ===========
# =========================================

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip

def abs_path(relative_path: str) -> str:
    return os.path.join(BASE_DIR, relative_path)

def load_icon(path: str, size: int = None) -> QIcon:
    full = abs_path(path)
    if not os.path.exists(full):
        return QIcon()
    icon = QIcon(full)
    if size:
        pixmap = icon.pixmap(size, size)
        icon = QIcon(pixmap)
    return icon

def is_port_open(port: int) -> bool:
    sock = socket.socket()
    sock.settimeout(0.15)
    try:
        sock.connect(("127.0.0.1", port))
        return True
    except Exception:
        return False
    finally:
        sock.close()


# =========================================
# =========== V A R I A B L E S ===========
# =========================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JELLYSEER_DIR = r"D:\Scripts\Mathias\Jellyseerr"
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
os.environ["QT_SCALE_FACTOR"] = "1.5"

SERVER_IP = get_local_ip()

PORT_MAPPING = {
    "sonarr": 8989,
    "radarr": 7878,
    "bazarr": 6767,
    "tdarr": 8265,
    "sabnzbd": 6969,
    "jellyfin": 8096,
    "plex": 32400,
    "jellyseerr": 5055
}

status_cache = {}
status_lock = threading.Lock()
ICON_SIZE = 32  # using pre-scaled 32px icons


# =========================================
# ============ T R A Y   A P P ============
# =========================================

class StatusUpdater(QObject):
    status_updated = Signal(dict)

    def __init__(self):
        super().__init__()

    def start_loop(self):
        while True:
            new_status = {name: is_port_open(port) for name, port in PORT_MAPPING.items()}
            self.status_updated.emit(new_status)
            time.sleep(1)


class TrayApp(QObject):
    def __init__(self):
        super().__init__()

        # System Tray
        self.tray = QSystemTrayIcon()
        self.tray.setToolTip("Remote Shutdown / Services")
        self.tray.setIcon(load_icon("static/img/32px/tray_icon_32px.png", ICON_SIZE))
        self.tray.activated.connect(self.on_tray_activated)

        # Menu
        self.menu = QMenu()
        font = self.menu.font()
        font.setPointSize(font.pointSize())
        self.menu.setFont(font)
        self.tray.setContextMenu(self.menu)

        # Status Updater
        self.status_updater = StatusUpdater()
        self.status_updater.status_updated.connect(self.on_status_update)
        threading.Thread(target=self.status_updater.start_loop, daemon=True).start()

        # Timer
        self.timer = QTimer()
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.refresh_ui)
        self.timer.start()

        self.refresh_ui()
        self.tray.show()


    # Services
    def build_services_menu(self, menu: QMenu):
        with status_lock:
            snapshot = dict(status_cache)

        for name, port in PORT_MAPPING.items():
            running = snapshot.get(name, False)
            status_emoji = "🟢" if running else "🔴"
            label = f"{status_emoji} {name.capitalize()}"
            act = QAction(load_icon(f"static/img/32px/{name}_32px.png", ICON_SIZE), label, menu)
            act.triggered.connect(lambda checked=False, p=port: webbrowser.open(f"http://localhost:{p}"))
            menu.addAction(act)


    # Jellyseerr Controls
    def build_jellyseerr_controls(self, menu: QMenu):
        with status_lock:
            snapshot = dict(status_cache)

        running = snapshot.get("jellyseerr", False)
        status_emoji = "⏹️" if running else "▶️"
        status_text = "Stop" if running else "Start"
        label = f"{status_emoji} {status_text} Jellyseerr"

        act = QAction(load_icon("static/img/32px/jellyseerr_32px.png", ICON_SIZE), label, menu)
        if running:
            act.triggered.connect(lambda: self.stop_jellyseerr())
        else:
            act.triggered.connect(lambda: self.start_jellyseerr())

        menu.addAction(act)


    # System Controls
    def build_system_controls(self, menu: QMenu):
        menu.addSeparator()
        
        shutdown_menu = QMenu("Shutdown PC", menu)
        shutdown_menu.setIcon(load_icon("static/img/32px/shutdown_white_32px.png"))
        confirm_act = QAction("✅ Yes, Shutdown Now", shutdown_menu)
        cancel_act = QAction("❌ No, Cancel", shutdown_menu)
        confirm_act.triggered.connect(self.execute_shutdown)
        cancel_act.triggered.connect(lambda: None)
        shutdown_menu.addAction(confirm_act)
        shutdown_menu.addAction(cancel_act)
        
        shutdown_action = QAction(load_icon("static/img/32px/shutdown_white_32px.png"), "Shutdown PC", menu)
        shutdown_action.setMenu(shutdown_menu)
        menu.addAction(shutdown_action)
        
        quit_act = QAction(load_icon("static/img/32px/quit_white_32px.png"), "Quit", menu)
        quit_act.triggered.connect(self.quit_app)
        menu.addAction(quit_act)


    def rebuild_menu(self):
        self.menu.clear()
        self.build_services_menu(self.menu)
        self.build_jellyseerr_controls(self.menu)
        self.build_system_controls(self.menu)


    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            webbrowser.open("http://localhost:5000")


    def start_jellyseerr(self):
        vbs = os.path.join(JELLYSEER_DIR, "start_jellyseerr.vbs")
        os.system(f'start "" wscript "{vbs}"')

    def stop_jellyseerr(self):
        vbs = os.path.join(JELLYSEER_DIR, "stop_jellyseerr.vbs")
        os.system(f'start "" wscript "{vbs}"')

    def execute_shutdown(self):
        os.system("shutdown /s /f /t 1")

    def quit_app(self):
        QApplication.quit()

    def on_status_update(self, new_status):
        with status_lock:
            global status_cache
            status_cache = new_status
        self.refresh_ui()

    def refresh_ui(self):
        menu = self.tray.contextMenu()
        if menu and menu.isVisible():
            return
        
        self.rebuild_menu()

        with status_lock:
            snapshot = dict(status_cache)

        if snapshot and all(snapshot.values()):
            self.tray.setIcon(load_icon("static/img/32px/tray_icon_ok_32px.png", ICON_SIZE) 
                              if os.path.exists(abs_path("static/img/32px/tray_icon_ok_32px.png")) 
                              else load_icon("static/img/32px/tray_icon_32px.png", ICON_SIZE))
            self.tray.setToolTip("All services running")
        else:
            self.tray.setIcon(load_icon("static/img/32px/tray_icon_warn_32px.png", ICON_SIZE) 
                              if os.path.exists(abs_path("static/img/32px/tray_icon_warn_32px.png")) 
                              else load_icon("static/img/32px/tray_icon_32px.png", ICON_SIZE))
            down = [k for k, v in snapshot.items() if not v]
            hint = "Down: " + ", ".join(down) if down else "Checking..."
            self.tray.setToolTip(hint)


# =========================================
# ================ M A I N ================
# =========================================

if __name__ == "__main__":
    if sys.stderr:
        faulthandler.enable(file=sys.stderr, all_threads=True)
    app = QApplication(sys.argv)
    tray_app = TrayApp()
    sys.exit(app.exec())




# ===========================================================================================================================
# ================================================== O L D   V E R S I O N ==================================================
# ===========================================================================================================================

# import wx
# import wx.adv
# import webbrowser
# import os
# import ctypes
# import logging
# import socket
# import time
# import threading

# # =========================================
# # =========== F U N C T I O N S ===========
# # =========================================

# # ===== Determine local IP =====
# def get_local_ip():
#     s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#     try:
#         s.connect(("8.8.8.8", 80))
#         ip = s.getsockname()[0]
#     except Exception:
#         ip = "127.0.0.1"
#     finally:
#         s.close()
#     return ip

# # ===== Rel Path to Abs Path for EXE =====
# def abs_path(relative_path):
#     return os.path.join(BASE_DIR, relative_path)

# # ===== Load Bitmap =====
# def load_bitmap(path, size):
#     full_path = abs_path(path)
#     if not os.path.exists(full_path):
#         logging.warning(f"Icon not found: {full_path}")
#         return wx.Bitmap(size[0], size[1])
#     img = wx.Image(full_path, wx.BITMAP_TYPE_PNG)
#     if not img.IsOk():
#         logging.warning(f"Failed to load image: {full_path}")
#         return wx.Bitmap(size[0], size[1])
#     img = img.Rescale(size[0], size[1], wx.IMAGE_QUALITY_HIGH)
#     return wx.Bitmap(img)

# # ===== Check if Service is listening on Port (Running/Not running) =====
# def is_port_open(port):
#     sock = socket.socket()
#     sock.settimeout(0.1)
#     try:
#         sock.connect(("127.0.0.1", port))
#         return True
#     except:
#         return False
#     finally:
#         sock.close()

# # ===== Update Service Status =====
# def update_status_cache():
#     global status_cache
#     while True:
#         status_cache = {name: is_port_open(port) for name, port in PORT_MAPPING.items()}
#         time.sleep(1)




# # =========================================
# # =========== V A R I A B L E S ===========
# # =========================================

# SERVER_IP = get_local_ip()
# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# JELLYSEER_DIR = r"D:\Scripts\Mathias\Jellyseerr"
# PORT_MAPPING = {
#     "sonarr": 8989,
#     "radarr": 7878,
#     "sabnzbd": 6969,
#     "jellyfin": 8096,
#     "jellyseerr": 5055,
#     "plex": 32400,
#     "bazarr": 6767,
#     "tdarr": 8265
# }

# # ===== Threading =====
# status_cache = {}
# status_thread = threading.Thread(target=update_status_cache, daemon=True)
# status_thread.start()



# # =========================================
# # ============= T A S K B A R =============
# # =========================================

# class TaskBarIcon(wx.adv.TaskBarIcon):
#     ICON_SIZE = (20, 20)

#     def __init__(self):
#         super().__init__()
#         self.set_icon()
#         self.Bind(wx.adv.EVT_TASKBAR_LEFT_DOWN, self.on_left_click)

#     def CreatePopupMenu(self):
#         menu = wx.Menu()
#         for name, port in PORT_MAPPING.items():
#             status = "🟢" if status_cache.get(name, False) else "🔴"
#             label = f"{status} {name.capitalize()}"
#             url = f"http://localhost:{port}"
#             bmp = load_bitmap(f"static/img/{name}.png", self.ICON_SIZE)
#             item = wx.MenuItem(menu, wx.ID_ANY, label)
#             item.SetBitmap(bmp)
#             menu.Append(item)
#             menu.Bind(wx.EVT_MENU, lambda e, url=url: webbrowser.open(url), item)
#         # Add other fixed items like Start/Stop/Shutdown
#         menu.AppendSeparator()
#         menu.Append(wx.ID_EXIT, "Quit")
#         menu.Bind(wx.EVT_MENU, lambda e: wx.CallAfter(wx.GetApp().ExitMainLoop), id=wx.ID_EXIT)
#         return menu


#     def set_icon(self):
#         bmp = load_bitmap("static/img/tray_icon.png", self.ICON_SIZE)
#         icon = wx.Icon()
#         icon.CopyFromBitmap(bmp)
#         self.SetIcon(icon, "Remote Shutdown")

#     def on_left_click(self, event):
#         webbrowser.open("http://localhost:5000")

#     def confirm_shutdown(self, event):
#         result = ctypes.windll.user32.MessageBoxW(None,
#             "Are you sure you want to shut down this PC?",
#             "Confirm Shutdown", 4)
#         if result == 6:  # Yes
#             os.system("shutdown /s /f /t 1")

# if __name__ == "__main__":
#     wx_app = wx.App(False)
#     TaskBarIcon()
#     wx_app.MainLoop()

