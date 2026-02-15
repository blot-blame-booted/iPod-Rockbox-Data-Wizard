import customtkinter as ctk
from tkinter import messagebox
import os
import datetime
import json
import pandas as pd

class PlaylistTab(ctk.CTkFrame):
    def __init__(self, master, data_manager, theme_manager):
        super().__init__(master)
        self.data = data_manager
        self.theme = theme_manager
        
        # --- UI Components ---
        ctk.CTkLabel(self, text="Smart Playlist Generator", font=("SF Pro Display", 20, "bold")).pack(pady=(20, 15))

        self.options_container = ctk.CTkFrame(self, fg_color="transparent")
        self.options_container.pack(fill="x", padx=20)

        # Initialize option rows
        self.chk_on_repeat, self.ent_on_repeat = self.create_option_row("On Repeat (Decay)", 25)
        self.chk_on_repeat.select()

        self.chk_forgotten, self.ent_forgotten = self.create_option_row("Forgotten Favorites", 25)

        self.chk_second_chance, self.ent_second = self.create_option_row("Second Chance", 25)

        self.chk_time_travel, self.ent_time_travel = self.create_option_row("Time Travel (By Year)", 50)
        self.chk_time_travel.select()

        self.chk_flashback, self.ent_flashback = self.create_option_row("Flashback: This month in history", 50)
        self.chk_flashback.select()

        ctk.CTkFrame(self, height=2, fg_color="#333").pack(fill="x", padx=40, pady=15)

        ctk.CTkLabel(self, text="Database", font=("Arial", 14, "bold")).pack(pady=5)
        self.chk_metrics = ctk.CTkSwitch(self, text="Generate metrics.json and scan Playlists")
        self.chk_metrics.pack(pady=5)
        self.chk_metrics.select()

        self.btn_process = ctk.CTkButton(self, text="Generate Playlists", command=self.process_playlists, 
                                         height=45, font=("Arial", 14, "bold"),
                                         fg_color=self.theme.get("accent"), hover_color=self.theme.get("accent_hover"))
        self.btn_process.pack(pady=30, padx=40, fill="x")

        self.prog_bar = ctk.CTkProgressBar(self)
        self.prog_bar.pack(pady=10, padx=40, fill="x")
        self.prog_bar.set(0)

    def create_option_row(self, text, default_val):
        """Creates a row with a Checkbox on the left and a numerical Entry on the right."""
        row = ctk.CTkFrame(self.options_container, fg_color="transparent")
        row.pack(pady=5, fill="x", padx=20)

        chk = ctk.CTkCheckBox(row, text=text, font=("Arial", 13))
        chk.pack(side="left")

        ent = ctk.CTkEntry(row, width=50, justify="center")
        ent.insert(0, str(default_val))
        ent.pack(side="right", padx=(5, 0))

        lbl = ctk.CTkLabel(row, text="Qty:", text_color="gray", font=("Arial", 11))
        lbl.pack(side="right")

        return chk, ent

    def get_limit(self, entry_widget, default=25):
        try:
            val = int(entry_widget.get())
            return max(1, val)
        except ValueError:
            return default

    def process_playlists(self):
        if not self.data.drive_path:
            messagebox.showwarning("Error", "Please select the iPod drive first.")
            return
            
        self.prog_bar.start()
        
        if not self.data.parse_log() or self.data.df.empty:
            self.prog_bar.stop()
            messagebox.showinfo("Info", "Log is empty or not found.")
            return

        df = self.data.df 
        # Filter only valid plays to ensure playlist quality
        df = df[df['valid_play'] == True].copy()

        # --- 1. On Repeat ---
        if self.chk_on_repeat.get():
            limit = self.get_limit(self.ent_on_repeat, 25)
            
            last = df['dt'].max()
            df['days_ago'] = (last - df['dt']).dt.days.clip(lower=0)
            df['score'] = 0.95 ** df['days_ago']
            
            top = df.groupby('original_path').agg({
                'score':'sum', 'artist':'first', 'title':'first', 'total_ms':'first'
            }).sort_values('score', ascending=False).head(limit)
            
            self.generate_m3u8(top.reset_index(), "(Dynamic) On Repeat.m3u8")

        # --- 2. Forgotten Favorites ---
        if self.chk_forgotten.get():
            limit = self.get_limit(self.ent_forgotten, 25)
            
            last_date = df['dt'].max()
            cutoff = last_date - datetime.timedelta(days=180)
            
            stats = df.groupby('original_path').agg(
                last_played=('dt', 'max'), 
                play_count=('timestamp', 'count'), 
                artist=('artist', 'first'), 
                title=('title', 'first'), 
                total_ms=('total_ms', 'first')
            )
            
            forgotten = stats[
                (stats['play_count'] >= 3) & 
                (stats['last_played'] < cutoff)
            ].sort_values('play_count', ascending=False).head(limit)
            
            self.generate_m3u8(forgotten.reset_index(), "(Dynamic) Forgotten Favorites.m3u8")

        # --- 3. Second Chance ---
        if self.chk_second_chance.get():
            limit = self.get_limit(self.ent_second, 25)
            
            stats = df.groupby('original_path').agg(
                play_count=('timestamp', 'count'), 
                artist=('artist', 'first'), 
                title=('title', 'first'), 
                total_ms=('total_ms', 'first')
            )
            chance = stats[
                (stats['play_count'] >= 1) & 
                (stats['play_count'] <= 2)
            ].sample(frac=1).head(limit)
            
            self.generate_m3u8(chance.reset_index(), "(Dynamic) Second Chance.m3u8")

        # --- 4. Time Travel (By Year) ---
        if self.chk_time_travel.get():
            limit = self.get_limit(self.ent_time_travel, 50)
            
            df['year'] = df['dt'].dt.year
            for year in df['year'].unique():
                year_df = df[df['year'] == year]
                
                top_year = year_df.groupby('original_path').agg({
                    'timestamp': 'count', 
                    'artist': 'first', 
                    'title': 'first', 
                    'total_ms': 'first'
                }).sort_values('timestamp', ascending=False).head(limit)
                
                self.generate_m3u8(top_year.reset_index(), f"(Dynamic) Time Travel {year}.m3u8")

        # --- 5. Flashback ---
        if self.chk_flashback.get():
            limit = self.get_limit(self.ent_flashback, 50)
            now = datetime.datetime.now()
            
            flashback_df = df[
                (df['dt'].dt.month == now.month) & 
                (df['dt'].dt.year < now.year)
            ]
            
            if not flashback_df.empty:
                top_flashback = flashback_df.groupby('original_path').agg({
                    'timestamp': 'count',
                    'total_ms': 'sum',
                    'artist': 'first',
                    'title': 'first'
                }).sort_values(
                    by=['timestamp', 'total_ms'], 
                    ascending=False
                ).head(limit)
                
                month_name = now.strftime("%B")
                self.generate_m3u8(top_flashback.reset_index(), f"(Dynamic) Flashback - {month_name}.m3u8")

        # --- 6. Metrics ---
        if self.chk_metrics.get():
            self.data.scan_existing_playlists()
            self.generate_metrics_db()

        self.prog_bar.stop()
        self.prog_bar.set(1)
        messagebox.showinfo("Success", "Playlists generated successfully.")

    def generate_m3u8(self, df_subset, filename):
        """Writes the M3U8 playlist file to the iPod drive."""
        if df_subset.empty:
            return
                    
        if not os.path.exists(self.data.playlist_path): os.makedirs(self.data.playlist_path)
        path = os.path.join(self.data.playlist_path, filename)
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write("#EXTM3U\n")
                for _, row in df_subset.iterrows():
                    ms = row.get('total_ms', 0)
                    sec = ms // 1000 if ms > 0 else -1
                    
                    title = row.get('title', 'Unknown Title')
                    artist = row.get('artist', 'Unknown Artist')
                    original_path = row['original_path']
                    
                    f.write(f"#EXTINF:{sec},{title} - {artist}\n{original_path}\n")
        except Exception as e:
            print(f"Error writing playlist {filename}: {e}")

    def generate_metrics_db(self):
        """Generates a JSON database with track usage metrics."""
        metrics_data = []
        df = self.data.df
        grouped = df.groupby('original_path')
        last_log_date = df['dt'].max()

        for path, group in grouped:
            play_count = len(group)
            last_played = group['dt'].max()
            first_played = group['dt'].min()
            days_since = (last_log_date - last_played).days
            recent_score = round(max(0, 1 - (days_since / 365)), 2)
            days_known = (last_log_date - first_played).days
            novelty_score = 0.9 if days_known < 30 else 0.1
            cooccur = round(play_count / (days_known + 1), 3)
            on_playlist = path in self.data.existing_playlist_songs

            metrics_data.append({
                "track_id": path, "play_count": play_count, "last_played_ts": int(last_played.timestamp()),
                "recent_score": recent_score, "novelty_score": novelty_score, 
                "cooccur_score": cooccur, "is_on_playlist": on_playlist 
            })

        json_path = os.path.join(self.data.drive_path, ".rockbox", "user_metrics.json")
        try:
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(metrics_data, f, indent=2)
        except Exception: pass