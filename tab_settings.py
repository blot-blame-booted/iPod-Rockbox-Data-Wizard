import customtkinter as ctk
from tkinter import messagebox

class SettingsTab(ctk.CTkFrame):
    def __init__(self, master, theme_manager):
        super().__init__(master)
        self.theme_manager = theme_manager
        self.entries = {}

        # Title and Instructions
        ctk.CTkLabel(self, text="🎨 Appearance Settings", 
                     font=("SF Pro Display", 20, "bold")).pack(pady=(20, 15))

        ctk.CTkLabel(self, text="Modify HEX color codes to unify the style.\nRestart the application to apply all changes.",
                     text_color="gray").pack(pady=(0, 20))

        # Settings Container
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=20, pady=10)

        # Generate inputs dynamically
        self.create_color_row("Accent Color (Buttons)", "accent")
        self.create_color_row("Hover Color (Mouse over)", "accent_hover")
        self.create_color_row("Card Background", "card_bg")
        self.create_color_row("Secondary Text", "text_sub")
        self.create_color_row("Success Color", "success")
        self.create_color_row("Error / Danger Color", "error")

        # Action Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=40, pady=20)

        ctk.CTkButton(btn_frame, text="Restore Defaults", 
                      command=self.reset_defaults, fg_color="#555").pack(side="left", expand=True, padx=10)
        
        ctk.CTkButton(btn_frame, text="💾 Save Changes", 
                      command=self.save_changes, 
                      fg_color=self.theme_manager.get("success")).pack(side="left", expand=True, padx=10)

    def create_color_row(self, label_text, key):
        """Creates a UI row for a specific color setting."""
        row = ctk.CTkFrame(self.scroll, fg_color="transparent")
        row.pack(fill="x", pady=5)
        
        ctk.CTkLabel(row, text=label_text, width=200, anchor="w").pack(side="left", padx=10)
        
        # Color preview square
        current_color = self.theme_manager.get(key)
        preview = ctk.CTkFrame(row, width=30, height=30, fg_color=current_color, corner_radius=5)
        preview.pack(side="right", padx=10)
        
        entry = ctk.CTkEntry(row, width=100)
        entry.insert(0, current_color)
        entry.pack(side="right")
        
        # Store references for later retrieval
        self.entries[key] = (entry, preview)

        # Update preview color in real-time as user types
        entry.bind("<KeyRelease>", lambda event, p=preview, e=entry: self.update_preview(p, e))

    def update_preview(self, preview_frame, entry_widget):
        """Updates the preview frame color if a valid HEX code is entered."""
        color = entry_widget.get()
        if len(color) == 7 and color.startswith("#"):
            try:
                preview_frame.configure(fg_color=color)
            except: pass

    def save_changes(self):
        """Persists the new color settings to the theme configuration."""
        new_colors = self.theme_manager.colors.copy()
        for key, (entry, _) in self.entries.items():
            new_colors[key] = entry.get()
        
        self.theme_manager.save_theme(new_colors)
        messagebox.showinfo("Saved", "Settings saved.\nPlease restart the application to apply all changes.")

    def reset_defaults(self):
        """Reverts the theme to the hardcoded default values."""
        self.theme_manager.colors = self.theme_manager.defaults.copy()
        self.theme_manager.save_theme(self.theme_manager.colors)
        
        # Refresh UI elements
        for key, (entry, preview) in self.entries.items():
            val = self.theme_manager.get(key)
            entry.delete(0, "end")
            entry.insert(0, val)
            preview.configure(fg_color=val)