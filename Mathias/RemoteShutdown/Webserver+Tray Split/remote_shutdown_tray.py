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

# ===== Determine Local IP =====
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

# ===== Convert Relative Path to Absolute Path =====
def abs_path(relative_path: str) -> str:
    return os.path.join(BASE_DIR, relative_path)

# ===== Load QIcon from File =====
def load_icon(path: str, size: int = None) -> QIcon:
    full = abs_path(path)
    if not os.path.exists(full):
        return QIcon()
    icon = QIcon(full)
    if size:
        pixmap = icon.pixmap(size, size)
        icon = QIcon(pixmap)
    return icon

# ===== Check if Local Port is Open =====
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

# ===== Paths & Scaling =====
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JELLYSEER_DIR = r"D:\Scripts\Mathias\Jellyseerr"
SCALE = 1.0
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
os.environ["QT_SCALE_FACTOR"] = "1.5"

# ===== Local Server Info =====
SERVER_IP = get_local_ip()

# ===== Port Mapping for Services =====
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

# ===== Service Status Cache (Threading) =====
status_cache = {}
status_lock = threading.Lock()


# =========================================
# ============ T R A Y   A P P ============
# =========================================

# ===== Status Updater Thread =====
class StatusUpdater(QObject):
    status_updated = Signal(dict)

    def __init__(self):
        super().__init__()

    def start_loop(self):
        while True:
            new_status = {name: is_port_open(port) for name, port in PORT_MAPPING.items()}
            self.status_updated.emit(new_status)
            time.sleep(1)


# ===== Main Tray Application =====
class TrayApp(QObject):
    def __init__(self):
        super().__init__()
        self.ICON_SIZE = int(20 * SCALE)
        
        # ===== System Tray Setup =====
        self.tray = QSystemTrayIcon()
        self.tray.setToolTip("Remote Shutdown / Services")
        self.tray.setIcon(load_icon("static/img/tray_icon.png", self.ICON_SIZE))
        self.tray.activated.connect(self.on_tray_activated)

        # ===== Context Menu Setup =====
        self.menu = QMenu()
        font = self.menu.font()
        font.setPointSize(int(font.pointSize() * SCALE))
        self.menu.setFont(font)
        self.tray.setContextMenu(self.menu)

        # ===== Status Updater =====
        self.status_updater = StatusUpdater()
        self.status_updater.status_updated.connect(self.on_status_update)
        threading.Thread(target=self.status_updater.start_loop, daemon=True).start()

        # ===== Timer to Refresh UI =====
        self.timer = QTimer()
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.refresh_ui)
        self.timer.start()

        self.refresh_ui()
        self.tray.show()


    # ===== Build Service Menu =====
    def build_services_menu(self, menu: QMenu):
        with status_lock:
            snapshot = dict(status_cache)

        for name, port in PORT_MAPPING.items():
            running = snapshot.get(name, False)
            status_emoji = "🟢" if running else "🔴"
            label = f"{status_emoji} {name.capitalize()}"

            act = QAction(load_icon(f"static/img/{name}.png", self.ICON_SIZE), label, menu)
            act.triggered.connect(lambda checked=False, p=port: webbrowser.open(f"http://localhost:{p}"))
            menu.addAction(act)


    # ===== Build Jellyseerr Controls =====
    def build_jellyseerr_controls(self, menu: QMenu):
        with status_lock:
            snapshot = dict(status_cache)

        running = snapshot.get("jellyseerr", False)
        status_emoji = "⏹️" if running else "▶️"
        status_Text = "Stop" if running else "Start"
        label = f"{status_emoji} {status_Text} Jellyseerr"

        act = QAction(load_icon("static/img/jellyseerr.png", self.ICON_SIZE), label, menu)
        if running:
            act.triggered.connect(lambda: self.stop_jellyseerr())
        else:
            act.triggered.connect(lambda: self.start_jellyseerr())

        menu.addAction(act)


    # ===== Build System Controls =====
    def build_system_controls(self, menu: QMenu):
        menu.addSeparator()
        
        # Shutdown submenu
        shutdown_menu = QMenu("Shutdown PC", menu)
        shutdown_menu.setIcon(load_icon("static/img/shutdown_white.png"))
        
        confirm_act = QAction("✅ Yes, Shutdown Now", shutdown_menu)
        cancel_act = QAction("❌ No, Cancel", shutdown_menu)
        confirm_act.triggered.connect(self.execute_shutdown)
        cancel_act.triggered.connect(lambda: None)
        shutdown_menu.addAction(confirm_act)
        shutdown_menu.addAction(cancel_act)
        
        shutdown_action = QAction(load_icon("static/img/shutdown_white.png"), "Shutdown PC", menu)
        shutdown_action.setMenu(shutdown_menu)
        menu.addAction(shutdown_action)
        
        # Quit
        quit_act = QAction(load_icon("static/img/quit_white.png"), "Quit", menu)
        quit_act.triggered.connect(self.quit_app)
        menu.addAction(quit_act)


    # ===== Rebuild Menu =====
    def rebuild_menu(self):
        self.menu.clear()
        self.build_services_menu(self.menu)
        self.build_jellyseerr_controls(self.menu)
        self.build_system_controls(self.menu)


    # ===== Tray Activation =====
    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            webbrowser.open("http://localhost:5000")


    # ===== Jellyseerr Actions =====
    def start_jellyseerr(self):
        vbs = os.path.join(JELLYSEER_DIR, "start_jellyseerr.vbs")
        os.system(f'start "" wscript "{vbs}"')


    def stop_jellyseerr(self):
        vbs = os.path.join(JELLYSEER_DIR, "stop_jellyseerr.vbs")
        os.system(f'start "" wscript "{vbs}"')


    # ===== Shutdown PC =====
    def execute_shutdown(self):
        os.system("shutdown /s /f /t 1")


    # ===== Quit App =====
    def quit_app(self):
        QApplication.quit()


    # ===== Status Update Handler =====
    def on_status_update(self, new_status):
        with status_lock:
            global status_cache
            status_cache = new_status
        self.refresh_ui()


    # ===== Refresh UI =====
    def refresh_ui(self):
        menu = self.tray.contextMenu()
        if menu and menu.isVisible():
            return
        
        self.rebuild_menu()

        with status_lock:
            snapshot = dict(status_cache)

        if snapshot and all(snapshot.values()):
            self.tray.setIcon(load_icon("static/img/tray_icon_ok.png", self.ICON_SIZE) 
                              if os.path.exists(abs_path("static/img/tray_icon_ok.png")) 
                              else load_icon("static/img/tray_icon.png", self.ICON_SIZE))
            self.tray.setToolTip("All services running")
        else:
            self.tray.setIcon(load_icon("static/img/tray_icon_warn.png", self.ICON_SIZE) 
                              if os.path.exists(abs_path("static/img/tray_icon_warn.png")) 
                              else load_icon("static/img/tray_icon.png", self.ICON_SIZE))
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

