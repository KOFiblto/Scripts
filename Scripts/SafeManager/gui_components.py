import customtkinter as ctk
from tkinter import filedialog
import string

class PasswordDialog(ctk.CTkToplevel):
    def __init__(self, *args, title="Enter Password", **kwargs):
        super().__init__(*args, **kwargs)
        self.geometry("400x200")
        self.title(title)
        self.password = None
        self.grab_set()

        self.label = ctk.CTkLabel(self, text="Please enter your VHDX password:", font=ctk.CTkFont(size=14))
        self.label.pack(pady=(20, 10))

        self.entry = ctk.CTkEntry(self, show="*", width=300)
        self.entry.pack(pady=10)
        self.entry.focus()
        self.entry.bind("<Return>", lambda e: self.on_submit())

        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.pack(pady=(10, 20))

        self.submit_btn = ctk.CTkButton(self.btn_frame, text="Submit", command=self.on_submit)
        self.submit_btn.pack(side="left", padx=10)

        self.cancel_btn = ctk.CTkButton(self.btn_frame, text="Cancel", command=self.on_cancel, fg_color="gray")
        self.cancel_btn.pack(side="left", padx=10)

    def on_submit(self):
        self.password = self.entry.get()
        self.destroy()

    def on_cancel(self):
        self.destroy()

    def get_input(self):
        self.wait_window()
        return self.password

class ConfirmDialog(ctk.CTkToplevel):
    def __init__(self, *args, title="Confirm", message="", **kwargs):
        super().__init__(*args, **kwargs)
        self.geometry("400x200")
        self.title(title)
        self.result = False
        self.grab_set()

        lbl = ctk.CTkLabel(self, text=message, wraplength=350, font=ctk.CTkFont(size=14))
        lbl.pack(pady=30, padx=20, fill="both", expand=True)

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=(0, 20))

        yes_btn = ctk.CTkButton(btn_frame, text="Yes", command=self.on_yes, fg_color="#c0392b", hover_color="#e74c3c", width=100)
        yes_btn.pack(side="left", padx=10)
        
        no_btn = ctk.CTkButton(btn_frame, text="No", command=self.on_no, width=100)
        no_btn.pack(side="left", padx=10)

    def on_yes(self):
        self.result = True
        self.destroy()
        
    def on_no(self):
        self.destroy()

    def get_result(self):
        self.wait_window()
        return self.result

class SafeDialog(ctk.CTkToplevel):
    def __init__(self, *args, safe=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.safe = safe
        self.title("Edit Safe" if safe else "Add Safe")
        self.geometry("500x350")
        self.result = None
        self.grab_set()

        self.name_var = ctk.StringVar(value=safe['name'] if safe else "")
        self.path_var = ctk.StringVar(value=safe['path'] if safe else "")
        self.type_var = ctk.StringVar(value=safe['type'] if safe else "VeraCrypt")
        self.letter_var = ctk.StringVar(value=safe['preferred_letter'] if safe and safe.get('preferred_letter') else "None")

        self.create_widgets()

    def create_widgets(self):
        self.grid_columnconfigure(1, weight=1)

        name_lbl = ctk.CTkLabel(self, text="Name:")
        name_lbl.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="e")
        name_entry = ctk.CTkEntry(self, textvariable=self.name_var)
        name_entry.grid(row=0, column=1, padx=(0, 20), pady=(20, 10), sticky="ew")

        path_lbl = ctk.CTkLabel(self, text="File Path:")
        path_lbl.grid(row=1, column=0, padx=20, pady=10, sticky="e")
        
        path_frame = ctk.CTkFrame(self, fg_color="transparent")
        path_frame.grid(row=1, column=1, padx=(0, 20), pady=10, sticky="ew")
        path_frame.grid_columnconfigure(0, weight=1)
        
        path_entry = ctk.CTkEntry(path_frame, textvariable=self.path_var)
        path_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        
        browse_btn = ctk.CTkButton(path_frame, text="Browse", width=60, command=self.browse_path)
        browse_btn.grid(row=0, column=1)

        type_lbl = ctk.CTkLabel(self, text="Type:")
        type_lbl.grid(row=2, column=0, padx=20, pady=10, sticky="e")
        type_menu = ctk.CTkOptionMenu(self, variable=self.type_var, values=["VeraCrypt", "VHDX"])
        type_menu.grid(row=2, column=1, padx=(0, 20), pady=10, sticky="w")

        letter_lbl = ctk.CTkLabel(self, text="Preferred Letter:")
        letter_lbl.grid(row=3, column=0, padx=20, pady=10, sticky="e")
        letters = ["None"] + list(string.ascii_uppercase[2:])
        letter_menu = ctk.CTkOptionMenu(self, variable=self.letter_var, values=letters)
        letter_menu.grid(row=3, column=1, padx=(0, 20), pady=10, sticky="w")

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=4, column=0, columnspan=2, pady=(30, 20))

        save_btn = ctk.CTkButton(btn_frame, text="Save", command=self.on_save)
        save_btn.pack(side="left", padx=5)

        if self.safe:
            del_btn = ctk.CTkButton(btn_frame, text="Delete", fg_color="#c0392b", hover_color="#e74c3c", command=self.on_delete)
            del_btn.pack(side="left", padx=5)

        cancel_btn = ctk.CTkButton(btn_frame, text="Cancel", fg_color="gray", command=self.destroy)
        cancel_btn.pack(side="left", padx=5)

    def browse_path(self):
        filename = filedialog.askopenfilename()
        if filename:
            filename = filename.replace("/", "\\")
            self.path_var.set(filename)

    def on_delete(self):
        confirm = ConfirmDialog(self, title="Confirm Delete", message="Are you sure you want to delete this Safe?")
        if confirm.get_result():
            self.result = {'action': 'delete', 'id': self.safe['id']}
            self.destroy()

    def on_save(self):
        name = self.name_var.get().strip()
        path = self.path_var.get().strip()
        
        if not name or not path:
            return
            
        letter = self.letter_var.get()
        if letter == "None":
            letter = ""

        self.result = {
            'action': 'save',
            'name': name,
            'path': path,
            'type': self.type_var.get(),
            'preferred_letter': letter
        }
        self.destroy()

    def get_result(self):
        self.wait_window()
        return self.result

class ErrorDialog(ctk.CTkToplevel):
    def __init__(self, *args, title="Error", message="", **kwargs):
        super().__init__(*args, **kwargs)
        self.title(title)
        self.geometry("400x200")
        self.grab_set()

        lbl = ctk.CTkLabel(self, text=message, wraplength=350, font=ctk.CTkFont(size=14))
        lbl.pack(pady=30, padx=20, fill="both", expand=True)

        btn = ctk.CTkButton(self, text="OK", command=self.destroy, width=100)
        btn.pack(pady=(0, 20))

class InfoDialog(ctk.CTkToplevel):
    def __init__(self, *args, title="Information", message="", **kwargs):
        super().__init__(*args, **kwargs)
        self.title(title)
        self.geometry("400x200")
        self.grab_set()

        lbl = ctk.CTkLabel(self, text=message, wraplength=350, font=ctk.CTkFont(size=14))
        lbl.pack(pady=30, padx=20, fill="both", expand=True)

        btn = ctk.CTkButton(self, text="OK", command=self.destroy, width=100)
        btn.pack(pady=(0, 20))
