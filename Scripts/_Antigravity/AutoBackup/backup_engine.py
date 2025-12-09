import os
import datetime
import logging
import zipfile

class BackupEngine:
    def __init__(self):
        self.logger = logging.getLogger("BackupEngine")
        logging.basicConfig(level=logging.INFO)

    def perform_backup(self, source_paths, destination_path):
        if not source_paths or not destination_path:
            return False, "Missing source or destination."

        if not os.path.exists(destination_path):
            return False, f"Destination path does not exist: {destination_path}"

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        zip_name = f"Backup_{timestamp}.zip"
        zip_full_path = os.path.join(destination_path, zip_name)

        try:
            with zipfile.ZipFile(zip_full_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                files_added = False
                for source in source_paths:
                    if os.path.exists(source):
                        if os.path.isdir(source):
                            # Walk the directory
                            parent_folder = os.path.dirname(source)
                            for root, dirs, files in os.walk(source):
                                for file in files:
                                    abs_path = os.path.join(root, file)
                                    # Arcname should be relative to the source's parent so we keep the folder structure
                                    # e.g. C:/Users/Docs -> Docs/file.txt
                                    rel_path = os.path.relpath(abs_path, parent_folder)
                                    zipf.write(abs_path, rel_path)
                                    files_added = True
                        else:
                            # It's a file
                            zipf.write(source, os.path.basename(source))
                            files_added = True
                
                if not files_added:
                     return False, "No valid files found to backup."

            return True, f"Backup saved as {zip_name}"

        except Exception as e:
            self.logger.error(f"Backup failed: {e}")
            return False, str(e)
