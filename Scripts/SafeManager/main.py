import customtkinter as ctk
import database
import drive_allocator
import mounter
from gui_components import SafeDialog, PasswordDialog, ErrorDialog, InfoDialog
import os
import hashlib
import threading
import time

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

def get_safe_color(safe_id):
    # Generates a visually distinct, dark theme friendly background color reliably using the Safe ID.
    colors = [
        "#1B4F72", "#78281F", "#145A32", "#4A235A", 
        "#7E5109", "#154360", "#4D5656", "#0E6251", 
        "#641E16", "#117864"
    ]
    idx = int(hashlib.md5(safe_id.encode()).hexdigest(), 16) % len(colors)
    return colors[idx]

class SafeManagerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("SafeManager")
        self.geometry("750x550")
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        self.title_lbl = ctk.CTkLabel(self, text="Encrypted Drives Manager", font=ctk.CTkFont(size=20, weight="bold"))
        self.title_lbl.grid(row=0, column=0, padx=20, pady=20, sticky="w")
        
        self.scrollable_frame = ctk.CTkScrollableFrame(self)
        self.scrollable_frame.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")
        self.scrollable_frame.grid_columnconfigure(0, weight=1)
        
        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.grid(row=2, column=0, padx=20, pady=(0, 20), sticky="ew")
        
        self.add_btn = ctk.CTkButton(self.btn_frame, text="Add Safe", command=self.add_safe)
        self.add_btn.pack(side="left", padx=5)

        self.dismount_all_btn = ctk.CTkButton(self.btn_frame, text="Dismount All", fg_color="#d35400", hover_color="#e67e22", command=self.dismount_all)
        self.dismount_all_btn.pack(side="left", padx=5)
        
        self.safe_widgets = []
        self.polling = True
        
        self.refresh_safes_list()
        
        # Start the background thread for continuous non-blocking polling
        self.polling_thread = threading.Thread(target=self.poll_mount_states, daemon=True)
        self.polling_thread.start()

    def poll_mount_states(self):
        while self.polling:
            widgets = list(self.safe_widgets)
            for w in widgets:
                try:
                    is_mnt = mounter.is_mounted(w['safe'])
                    if is_mnt != w['mounted_state']:
                        w['mounted_state'] = is_mnt
                        # Safely trigger a UI update on the main Tk thread
                        self.after(0, self.update_single_widget, w)
                except:
                    pass
            time.sleep(1)

    def update_single_widget(self, w):
        try:
            if not w['btns_frame'].winfo_exists():
                return
                
            for child in w['btns_frame'].winfo_children():
                child.pack_forget()
                
            if w['mounted_state']:
                w['mnt_lbl'].pack(side="left", padx=5)
                w['dismount_btn'].pack(side="left", padx=5)
            else:
                w['mnt_btn'].pack(side="left", padx=5)
                
            w['edit_btn'].pack(side="left", padx=5)
        except Exception:
            pass

    def refresh_safes_list(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
            
        self.safe_widgets = []
        safes = database.load_safes()
        
        if not safes:
            lbl = ctk.CTkLabel(self.scrollable_frame, text="No Safes found. Click 'Add Safe' to begin.", text_color="gray")
            lbl.grid(row=0, column=0, pady=20)
            return

        for i, safe in enumerate(safes):
            bg_color = get_safe_color(safe['id'])
            frame = ctk.CTkFrame(self.scrollable_frame, fg_color=bg_color, corner_radius=8)
            frame.grid(row=i, column=0, padx=5, pady=10, sticky="ew")
            frame.grid_columnconfigure(1, weight=1)
            
            # Badge text to visually distinguish without emojis
            badge_text = "[ VC ]" if safe['type'] == "VeraCrypt" else "[ VHDX ]"
            badge_color = "#85C1E9" if safe['type'] == "VeraCrypt" else "#D7BDE2"
            badge = ctk.CTkLabel(frame, text=badge_text, font=ctk.CTkFont(size=14, weight="bold"), text_color=badge_color)
            badge.grid(row=0, column=0, padx=(15, 5), pady=(15, 0), sticky="w")
            
            name_lbl = ctk.CTkLabel(frame, text=safe['name'], font=ctk.CTkFont(size=18, weight="bold"))
            name_lbl.grid(row=0, column=1, padx=5, pady=(15, 0), sticky="w")
            
            info_text = f"Path: {safe['path']}  |  Letter: {safe.get('preferred_letter') or 'Auto'}"
            lbl = ctk.CTkLabel(frame, text=info_text, justify="left", anchor="w", text_color="lightgray")
            lbl.grid(row=1, column=0, columnspan=2, padx=15, pady=(5, 15), sticky="w")
            
            btns_frame = ctk.CTkFrame(frame, fg_color="transparent")
            btns_frame.grid(row=0, column=2, rowspan=2, padx=15, pady=10, sticky="e")
            
            mnt_btn = ctk.CTkButton(btns_frame, text="Mount", width=80, command=lambda s=safe: self.mount_safe(s))
            mnt_lbl = ctk.CTkButton(btns_frame, text="Mounted", width=80, state="disabled", fg_color="gray")
            dismount_btn = ctk.CTkButton(btns_frame, text="Dismount", width=80, fg_color="#d35400", hover_color="#e67e22", command=lambda s=safe: self.dismount_safe(s))
            
            edit_btn = ctk.CTkButton(btns_frame, text="Edit", width=80, command=lambda s=safe: self.edit_safe(s))
            
            w_dict = {
                'safe': safe, 
                'btns_frame': btns_frame,
                'mnt_btn': mnt_btn,
                'mnt_lbl': mnt_lbl,
                'dismount_btn': dismount_btn,
                'edit_btn': edit_btn,
                'mounted_state': None
            }
            self.safe_widgets.append(w_dict)
            
            # Initial setup of buttons, polling thread will override almost instantly if needed
            mnt_btn.pack(side="left", padx=5)
            edit_btn.pack(side="left", padx=5)

    def add_safe(self):
        dialog = SafeDialog(self)
        result = dialog.get_result()
        if result and result.get('action') == 'save':
            database.add_safe(result['name'], result['path'], result['type'], result['preferred_letter'])
            self.refresh_safes_list()

    def edit_safe(self, safe):
        dialog = SafeDialog(self, safe=safe)
        result = dialog.get_result()
        if result:
            if result.get('action') == 'delete':
                database.delete_safe(result['id'])
            elif result.get('action') == 'save':
                database.edit_safe(safe['id'], result['name'], result['path'], result['type'], result['preferred_letter'])
            self.refresh_safes_list()

    def mount_safe(self, safe):
        if not os.path.exists(safe['path']):
            ErrorDialog(self, message=f"File not found:\n{safe['path']}")
            return

        all_safes = database.load_safes()
        try:
            drive_letter = drive_allocator.allocate_drive_letter(safe, all_safes)
        except Exception as e:
            ErrorDialog(self, message=str(e))
            return

        if safe['type'] == "VeraCrypt":
            try:
                mounter.mount_veracrypt(safe['path'], drive_letter)
                InfoDialog(self, message=f"VeraCrypt launched.\nTarget Drive Letter: {drive_letter}:")
            except Exception as e:
                ErrorDialog(self, message=str(e))
        
        elif safe['type'] == "VHDX":
            if not mounter.is_admin():
                ErrorDialog(self, message="Administrator privileges are required to mount VHDX files.\nRestart the application as Administrator.")
                return
                
            pwd_dialog = PasswordDialog(self)
            password = pwd_dialog.get_input()
            if password:
                try:
                    mounter.mount_vhdx(safe['path'], password, drive_letter)
                    InfoDialog(self, message=f"VHDX successfully mounted to {drive_letter}:")
                except Exception as e:
                    ErrorDialog(self, message=str(e))
                    
    def dismount_safe(self, safe):
        try:
            mounter.dismount_safe(safe)
            InfoDialog(self, message=f"Dismount command sent for {safe['name']}.")
        except Exception as e:
            ErrorDialog(self, message=str(e))
            
    def dismount_all(self):
        try:
            mounter.dismount_all()
            InfoDialog(self, message="Dismount All command executed.")
        except Exception as e:
            ErrorDialog(self, message=str(e))

if __name__ == "__main__":
    app = SafeManagerApp()
    app.mainloop()
