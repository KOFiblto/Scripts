## --- R E L E A S E   V E R S I O N  ----

from waitress import serve # type: ignore
from remote_shutdown_flask import app

if __name__ == "__main__":
   serve(app, host="0.0.0.0", port=5000, threads=2)




## --- D E V E L O P M E N T   V E R S I O N  ----

# from remote_shutdown_flask import app

# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=5000, debug=True)





########################## PY -> EXE ##########################

# -- Tray
# pyinstaller --onefile --add-data "static;static" --windowed --manifest admin.manifest --icon "D:\Scripts\Mathias\_Icons\tray_icon.ico"  "remote_shutdown_tray.py"

# -- Webserver
# pyinstaller --onefile --add-data "static;static" --windowed --manifest admin.manifest --icon "D:\Scripts\Mathias\_Icons\RemoteShutdown.ico" --add-data "templates;templates" "remote_shutdown_service.py"
