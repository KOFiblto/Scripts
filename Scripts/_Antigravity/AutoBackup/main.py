from config_manager import ConfigManager
from backup_engine import BackupEngine
from usb_monitor import USBMonitor
import autostart
from gui import BackupApp
import sys

def main():
    config = ConfigManager()
    engine = BackupEngine()
    
    # Monitor needs a callback, but we need the app instance for the callback.
    # We will set it after app creation.
    monitor = USBMonitor(config, None) 
    
    app = BackupApp(config, engine, monitor, autostart)
    
    # Connect the callback
    monitor.backup_callback = app.trigger_auto_backup
    
    app.mainloop()
    
    # Cleanup
    monitor.stop()

if __name__ == "__main__":
    main()
