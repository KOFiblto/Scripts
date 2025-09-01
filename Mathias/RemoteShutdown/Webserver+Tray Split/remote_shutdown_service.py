## --- R E L E A S E   V E R S I O N  ----

# from waitress import serve
# from remote_shutdown_flask import app

# if __name__ == "__main__":
#    serve(app, host="0.0.0.0", port=5000, threads=2)




## --- D E V E L O P M E N T   V E R S I O N  ----

from remote_shutdown_flask import app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)




############# T O D O #############

# Status Dots right bound

# Start / Stop Jellyseer require password

# Status Dots on Tray

# Tray Upgrade (Like TranslucentTB)

#