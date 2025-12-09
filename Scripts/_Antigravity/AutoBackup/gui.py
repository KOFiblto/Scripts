import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
import datetime
import os

# Set theme
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

class BackupApp(ctk.CTk):
    def __init__(self, config_manager, backup_engine, usb_monitor, autostart_module):
        super().__init__()
        
        self.config_manager = config_manager
        self.backup_engine = backup_engine
        self.usb_monitor = usb_monitor
        self.autostart_module = autostart_module
        
        # Window setup
        self.title("AutoBackup Utility")
        self.geometry("750x700")
        
        # Colors (Modern "Glass" Dark Theme)
        self.c_bg = "#09090b"          # Almost black
        self.c_card = "#18181b"        # Zinc 900
        self.c_card_border = "#27272a" # Zinc 800
        self.c_primary = "#6366f1"     # Indigo 500
        self.c_primary_hover = "#4f46e5" # Indigo 600
        self.c_accent = "#22d3ee"      # Cyan 400
        self.c_text_main = "#f4f4f5"   # Zinc 100
        self.c_text_sub = "#a1a1aa"    # Zinc 400
        self.c_success = "#10b981"     # Emerald 500
        self.c_danger = "#ef4444"      # Red 500
        
        self.configure(fg_color=self.c_bg)

        # Main Scrollable Container
        self.main_frame = ctk.CTkScrollableFrame(
            self, 
            fg_color="transparent", 
            corner_radius=0
        )
        self.main_frame.pack(fill="both", expand=True)
        
        self._init_ui()
        self._load_settings()
        
        # Start monitor if enabled
        if self.config_manager.get("auto_backup_enabled"):
            self.usb_monitor.start()

    def _init_ui(self):
        # --- Header ---
        self.header_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=30, pady=(40, 20))
        
        self.label_title = ctk.CTkLabel(
            self.header_frame, 
            text="AutoBackup", 
            font=("Segoe UI Display", 36, "bold"),
            text_color=self.c_text_main
        )
        self.label_title.pack(side="left")
        
        self.badge = ctk.CTkLabel(
            self.header_frame,
            text=" PRO ",
            fg_color=self.c_primary,
            text_color="white",
            corner_radius=6,
            font=("Segoe UI", 10, "bold")
        )
        self.badge.pack(side="left", padx=10, pady=(10, 0))

        # --- Card: Source ---
        self._create_card_label("BACKUP SOURCES")
        
        self.card_source = ctk.CTkFrame(
            self.main_frame, 
            fg_color=self.c_card, 
            border_width=1, 
            border_color=self.c_card_border,
            corner_radius=16
        )
        self.card_source.pack(fill="x", padx=30, pady=(0, 20))
        
        self.listbox_sources = ctk.CTkTextbox(
            self.card_source, 
            height=100, 
            fg_color="#000000", # Darker inner well
            text_color=self.c_text_main,
            corner_radius=8,
            border_width=0,
            font=("Consolas", 12)
        )
        self.listbox_sources.pack(fill="x", padx=20, pady=(20, 10))
        self.listbox_sources.configure(state="disabled")

        self.btn_frame_source = ctk.CTkFrame(self.card_source, fg_color="transparent")
        self.btn_frame_source.pack(fill="x", padx=20, pady=(0, 20))

        self.btn_add_source = ctk.CTkButton(
            self.btn_frame_source, 
            text="+ Add Folder", 
            command=self.add_source_folder, 
            fg_color=self.c_card_border, 
            hover_color=self.c_primary,
            text_color=self.c_text_main,
            width=120,
            height=32,
            corner_radius=8
        )
        self.btn_add_source.pack(side="left")

        self.btn_clear_sources = ctk.CTkButton(
            self.btn_frame_source, 
            text="Clear", 
            command=self.clear_sources, 
            fg_color="transparent", 
            text_color=self.c_danger, 
            hover_color=self.c_card_border,
            width=60,
            height=32,
            corner_radius=8
        )
        self.btn_clear_sources.pack(side="right")

        # --- Card: Destination ---
        self._create_card_label("DESTINATION DRIVE")
        
        self.card_dest = ctk.CTkFrame(
            self.main_frame, 
            fg_color=self.c_card, 
            border_width=1, 
            border_color=self.c_card_border,
            corner_radius=16
        )
        self.card_dest.pack(fill="x", padx=30, pady=(0, 20))

        self.dest_inner = ctk.CTkFrame(self.card_dest, fg_color="transparent")
        self.dest_inner.pack(fill="x", padx=20, pady=20)

        self.entry_dest = ctk.CTkEntry(
            self.dest_inner, 
            placeholder_text="No destination selected...", 
            fg_color="#000000",
            text_color=self.c_text_main,
            border_width=0,
            height=40,
            corner_radius=8
        )
        self.entry_dest.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.entry_dest.configure(state="readonly")

        self.btn_select_dest = ctk.CTkButton(
            self.dest_inner, 
            text="Browse", 
            command=self.select_destination, 
            fg_color=self.c_primary, 
            hover_color=self.c_primary_hover,
            width=100,
            height=40,
            corner_radius=8
        )
        self.btn_select_dest.pack(side="right")

        # --- Card: Automation ---
        self._create_card_label("AUTOMATION")
        
        self.card_auto = ctk.CTkFrame(
            self.main_frame, 
            fg_color=self.c_card, 
            border_width=1, 
            border_color=self.c_card_border,
            corner_radius=16
        )
        self.card_auto.pack(fill="x", padx=30, pady=(0, 20))

        self.check_autostart = ctk.CTkSwitch(
            self.card_auto, 
            text="Start with Windows", 
            command=self.toggle_autostart,
            progress_color=self.c_success,
            button_color="white",
            button_hover_color="#e4e4e7",
            font=("Segoe UI", 13),
            text_color=self.c_text_main
        )
        self.check_autostart.pack(anchor="w", padx=20, pady=(20, 10))
        
        self.check_autobackup = ctk.CTkSwitch(
            self.card_auto, 
            text="Auto-Backup on USB Insert", 
            command=self.toggle_auto_backup,
            progress_color=self.c_accent,
            button_color="white",
            button_hover_color="#e4e4e7",
            font=("Segoe UI", 13),
            text_color=self.c_text_main
        )
        self.check_autobackup.pack(anchor="w", padx=20, pady=(0, 20))

        # --- Footer / Action ---
        self.footer_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.footer_frame.pack(fill="x", padx=30, pady=(10, 40))

        self.label_status = ctk.CTkLabel(self.footer_frame, text="Ready", text_color=self.c_text_sub, font=("Segoe UI", 12))
        self.label_status.pack(anchor="w")
        
        self.label_last_run = ctk.CTkLabel(self.footer_frame, text="Last Backup: Never", text_color=self.c_text_sub, font=("Segoe UI", 12))
        self.label_last_run.pack(anchor="w", pady=(0, 10))

        self.btn_backup_now = ctk.CTkButton(
            self.footer_frame, 
            text="RUN BACKUP NOW", 
            command=self.perform_manual_backup, 
            height=55, 
            font=("Segoe UI", 15, "bold"),
            fg_color=self.c_primary,
            hover_color=self.c_primary_hover,
            text_color="white",
            corner_radius=12
        )
        self.btn_backup_now.pack(fill="x")

    def _create_card_label(self, text):
        label = ctk.CTkLabel(
            self.main_frame, 
            text=text, 
            font=("Segoe UI", 11, "bold"), 
            text_color=self.c_text_sub
        )
        label.pack(anchor="w", padx=35, pady=(0, 5))

    def _load_settings(self):
        # Sources
        sources = self.config_manager.get("source_paths", [])
        self._update_sources_list(sources)
        
        # Dest
        dest = self.config_manager.get("destination_path", "")
        self.entry_dest.configure(state="normal")
        self.entry_dest.delete(0, "end")
        self.entry_dest.insert(0, dest)
        self.entry_dest.configure(state="readonly")
        
        # Toggles
        if self.config_manager.get("auto_backup_enabled"):
            self.check_autobackup.select()
        else:
            self.check_autobackup.deselect()
            
        if self.autostart_module.is_autostart_enabled():
            self.check_autostart.select()
        else:
            self.check_autostart.deselect()
            
        # Last Run
        last_run = self.config_manager.get("last_backup_timestamp")
        if last_run:
            self.label_last_run.configure(text=f"Last Backup: {last_run}")

    def _update_sources_list(self, sources):
        self.listbox_sources.configure(state="normal")
        self.listbox_sources.delete("0.0", "end")
        for s in sources:
            self.listbox_sources.insert("end", f" {s}\n")
        self.listbox_sources.configure(state="disabled")

    def add_source_folder(self):
        path = filedialog.askdirectory()
        if path:
            sources = self.config_manager.get("source_paths", [])
            if path not in sources:
                sources.append(path)
                self.config_manager.set("source_paths", sources)
                self._update_sources_list(sources)

    def clear_sources(self):
        self.config_manager.set("source_paths", [])
        self._update_sources_list([])

    def select_destination(self):
        path = filedialog.askdirectory()
        if path:
            self.config_manager.set("destination_path", path)
            self.entry_dest.configure(state="normal")
            self.entry_dest.delete(0, "end")
            self.entry_dest.insert(0, path)
            self.entry_dest.configure(state="readonly")

    def toggle_autostart(self):
        enabled = self.check_autostart.get()
        success = self.autostart_module.set_autostart(enabled)
        if not success:
            if enabled: self.check_autostart.deselect()
            else: self.check_autostart.select()
            messagebox.showerror("Error", "Failed to change autostart settings.")

    def toggle_auto_backup(self):
        enabled = self.check_autobackup.get()
        self.config_manager.set("auto_backup_enabled", enabled)
        if enabled:
            self.usb_monitor.start()

    def perform_manual_backup(self):
        self.btn_backup_now.configure(state="disabled", text="BACKING UP...", fg_color=self.c_card_border)
        self.label_status.configure(text="Status: Backing up...", text_color=self.c_accent)
        
        threading.Thread(target=self._backup_thread, daemon=True).start()

    def trigger_auto_backup(self):
        self.after(0, self.perform_manual_backup)

    def _backup_thread(self):
        sources = self.config_manager.get("source_paths")
        dest = self.config_manager.get("destination_path")
        
        success, msg = self.backup_engine.perform_backup(sources, dest)
        
        self.after(0, lambda: self._backup_finished(success, msg))

    def _backup_finished(self, success, msg):
        self.btn_backup_now.configure(state="normal", text="RUN BACKUP NOW", fg_color=self.c_primary)
        if success:
            self.label_status.configure(text=f"Status: Success - {msg}", text_color=self.c_success)
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.config_manager.set("last_backup_timestamp", timestamp)
            self.label_last_run.configure(text=f"Last Backup: {timestamp}")
        else:
            self.label_status.configure(text=f"Status: Failed - {msg}", text_color=self.c_danger)
            messagebox.showerror("Backup Failed", msg)
