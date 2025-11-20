import time
import os
import threading
import logging
import datetime

class USBMonitor:
    def __init__(self, config_manager, backup_callback):
        self.config_manager = config_manager
        self.backup_callback = backup_callback
        self.running = False
        self.thread = None
        self.logger = logging.getLogger("USBMonitor")

    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)

    def _monitor_loop(self):
        self.logger.info("USB Monitor started.")
        
        while self.running:
            if self.config_manager.get("auto_backup_enabled"):
                dest_path = self.config_manager.get("destination_path")
                
                if dest_path and os.path.exists(dest_path):
                    # Check if we should backup
                    last_timestamp_str = self.config_manager.get("last_backup_timestamp")
                    should_backup = False
                    
                    if not last_timestamp_str:
                        should_backup = True
                    else:
                        # Parse timestamp and check delta
                        # Format: 2023-11-19 18:00:00
                        try:
                            last_run = datetime.datetime.strptime(last_timestamp_str, "%Y-%m-%d %H:%M:%S")
                            # Backup if more than 12 hours have passed
                            if (datetime.datetime.now() - last_run).total_seconds() > 3600 * 12: 
                                should_backup = True
                        except ValueError:
                            should_backup = True # Invalid timestamp, run anyway

                    if should_backup:
                        self.logger.info("Triggering auto-backup...")
                        self.backup_callback()
                        # Wait a bit to prevent double triggering
                        time.sleep(60) 
            
            time.sleep(5) # Check every 5 seconds
