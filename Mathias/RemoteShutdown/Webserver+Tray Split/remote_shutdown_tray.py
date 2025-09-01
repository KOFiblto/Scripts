import wx
import wx.adv
import webbrowser
import os
import ctypes
import logging

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JELLYSEER_DIR = r"D:\Scripts\Jellyseerr"

def abs_path(relative_path):
    return os.path.join(BASE_DIR, relative_path)

def load_bitmap(path, size):
    full_path = abs_path(path)
    if not os.path.exists(full_path):
        logging.warning(f"Icon not found: {full_path}")
        return wx.Bitmap(size[0], size[1])
    img = wx.Image(full_path, wx.BITMAP_TYPE_PNG)
    if not img.IsOk():
        logging.warning(f"Failed to load image: {full_path}")
        return wx.Bitmap(size[0], size[1])
    img = img.Rescale(size[0], size[1], wx.IMAGE_QUALITY_HIGH)
    return wx.Bitmap(img)

class TaskBarIcon(wx.adv.TaskBarIcon):
    ICON_SIZE = (20, 20)

    def __init__(self):
        super().__init__()
        self.set_icon()
        self.Bind(wx.adv.EVT_TASKBAR_LEFT_DOWN, self.on_left_click)

    def CreatePopupMenu(self):
        menu = wx.Menu()
        items = [
            ("Sonarr", "static/img/sonarr.png", lambda e: webbrowser.open("http://localhost:8989")),
            ("Radarr", "static/img/radarr.png", lambda e: webbrowser.open("http://localhost:7878")),
            ("Jellyfin", "static/img/jellyfin.png", lambda e: webbrowser.open("http://localhost:8096")),
            ("Jellyseerr", "static/img/jellyseerr.png", lambda e: webbrowser.open("http://localhost:5055")),
            ("Plex", "static/img/plex.png", lambda e: webbrowser.open("http://localhost:32400")),
            ("Start Jellyseerr", "static/img/jellyseerr.png", lambda e: os.system(f'start "" wscript "{os.path.join(JELLYSEER_DIR, "start_jellyseerr.vbs")}"')),
            ("Stop Jellyseerr", "static/img/jellyseerr.png", lambda e: os.system(f'start "" wscript "{os.path.join(JELLYSEER_DIR, "stop_jellyseerr.vbs")}"')),
            ("Shutdown PC", "static/img/shutdown.png", self.confirm_shutdown),
            ("Quit", "static/img/quit.png", lambda e: wx.CallAfter(wx.GetApp().ExitMainLoop))
        ]
        for label, path, handler in items:
            bmp = load_bitmap(path, self.ICON_SIZE)
            item = wx.MenuItem(menu, wx.ID_ANY, label)
            item.SetBitmap(bmp)
            menu.Append(item)
            menu.Bind(wx.EVT_MENU, handler, item)
        return menu

    def set_icon(self):
        bmp = load_bitmap("static/img/tray_icon.png", self.ICON_SIZE)
        icon = wx.Icon()
        icon.CopyFromBitmap(bmp)
        self.SetIcon(icon, "Remote Shutdown")

    def on_left_click(self, event):
        webbrowser.open("http://localhost:5000")

    def confirm_shutdown(self, event):
        result = ctypes.windll.user32.MessageBoxW(None,
            "Are you sure you want to shut down this PC?",
            "Confirm Shutdown", 4)
        if result == 6:  # Yes
            os.system("shutdown /s /f /t 1")

if __name__ == "__main__":
    wx_app = wx.App(False)
    TaskBarIcon()
    wx_app.MainLoop()