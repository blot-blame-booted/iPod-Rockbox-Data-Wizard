import customtkinter as ctk
from tkinter import filedialog
import os
import threading 
from data_manager import RockboxData
from tab_playlists import PlaylistTab
from tab_discovery import DiscoveryTab
from tab_statistics import StatisticsTab
from tab_optimizer import OptimizerTab
from theme_manager import ThemeManager
from tab_settings import SettingsTab

class RockboxManagerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.theme = ThemeManager()
        ctk.set_appearance_mode("Dark")

        self.title("Rockbox Data Wizard - Ultimate Edition")
        self.geometry("1100x850") 
        
        self.data_manager = RockboxData()

        ctk.CTkLabel(self, text="iPod Data Wizard", font=("SF Pro Display", 24, "bold")).pack(pady=(20, 10))

        self.path_frame = ctk.CTkFrame(self)
        self.path_frame.pack(pady=5, padx=20, fill="x")
        
        self.btn_select_drive = ctk.CTkButton(self.path_frame, text="Select iPod Drive", command=self.select_drive)
        self.btn_select_drive.pack(side="left", padx=10, pady=10)
        
        self.lbl_status = ctk.CTkLabel(self.path_frame, text="Not connected", text_color="gray")
        self.lbl_status.pack(side="left", padx=10)

        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(pady=10, padx=20, fill="both", expand=True)

        self.tab_stats = self.tabview.add("Statistics")
        self.tab_playlists = self.tabview.add("Playlists")
        self.tab_discovery = self.tabview.add("Discovery Lastfm")
        self.tab_opt = self.tabview.add("Art Optimizer")
        self.tab_settings = self.tabview.add("Settings")
        
        self.stats_ui = StatisticsTab(self.tab_stats, self.data_manager, self.theme)
        self.stats_ui.pack(fill="both", expand=True)

        self.opt_ui = OptimizerTab(self.tab_opt, self.data_manager, self.theme)
        self.opt_ui.pack(fill="both", expand=True)

        self.playlist_ui = PlaylistTab(self.tab_playlists, self.data_manager, self.theme)
        self.playlist_ui.pack(fill="both", expand=True)

        self.discovery_ui = DiscoveryTab(self.tab_discovery, self.data_manager, self.theme)
        self.discovery_ui.pack(fill="both", expand=True)

        self.settings_ui = SettingsTab(self.tab_settings, self.theme)
        self.settings_ui.pack(fill="both", expand=True)

    def select_drive(self):
        directory = filedialog.askdirectory(title="Select iPod Root Directory")
        if directory:
            # Run the loading process in a separate thread to prevent UI freezing
            threading.Thread(target=self.load_data_thread, args=(directory,), daemon=True).start()

    def load_data_thread(self, directory):
        """Background loading process."""
        
        # Update UI to indicate loading state
        self.btn_select_drive.configure(state="disabled", text="⏳ Loading data...")
        self.lbl_status.configure(text="Analyzing log and metadata...", text_color="orange")
        
        log_found = self.data_manager.set_paths(directory)
        
        # Populate DataFrame. Initial run uses disk; subsequent runs use JSON cache.
        if log_found:
             self.data_manager.parse_log()

        # Update UI upon completion (using .after for thread safety in tkinter)
        self.after(0, lambda: self.finish_loading(directory, log_found))

    def finish_loading(self, directory, log_found):
        self.btn_select_drive.configure(state="normal", text=f"Drive: {os.path.basename(directory)}")
        
        possible_music_path = os.path.join(directory, "Music")
        self.opt_ui.selected_path.set(possible_music_path)
        
        if log_found:
            self.lbl_status.configure(text=f"Connected: {directory} ✅", text_color="#1DB954")
            self.stats_ui.update_stats("All Time")
        else:
            self.lbl_status.configure(text=f"⚠ Log not found in {directory}", text_color="red")

if __name__ == "__main__":
    app = RockboxManagerApp()
    app.mainloop()