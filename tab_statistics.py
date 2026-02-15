import customtkinter as ctk
from tkinter import Canvas
import pandas as pd
import datetime
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import numpy as np

class StatisticsTab(ctk.CTkFrame):
    def __init__(self, master, data_manager, theme_manager):
        super().__init__(master)
        self.data = data_manager
        self.theme = theme_manager
        
        # Theme colors
        self.col_bg = self.theme.get("card_bg")
        self.col_card = self.theme.get("card_bg")
        self.col_accent = self.theme.get("accent")
        self.col_text_sub = self.theme.get("text_sub")

        # Time Filters
        self.filter_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.filter_frame.pack(fill="x", padx=20, pady=10)
        
        self.seg_filter = ctk.CTkSegmentedButton(self.filter_frame, 
                                                 values=["All Time", "This Year", "This Month", "This Week"],
                                                 command=self.update_stats,
                                                 selected_color=self.col_accent,
                                                 selected_hover_color="#7c3fe6")
        self.seg_filter.pack(side="right")
        self.seg_filter.set("All Time")

        ctk.CTkLabel(self.filter_frame, text="Your Statistics", font=("SF Pro Display", 20, "bold")).pack(side="left")

        # Scrollable Content
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=10, pady=5)

        # 1. Totals Section
        self.hero_frame = ctk.CTkFrame(self.scroll, fg_color=self.col_card, corner_radius=15)
        self.hero_frame.pack(fill="x", padx=10, pady=10)
        self.hero_frame.columnconfigure((0,1,2), weight=1)
        
        self.lbl_minutes = self.create_metric_label(self.hero_frame, "Minutes Played", "0", 0)
        self.lbl_plays = self.create_metric_label(self.hero_frame, "Total Plays", "0", 1)
        self.lbl_avg = self.create_metric_label(self.hero_frame, "Avg Daily Plays", "0", 2)

        # 2. Top 5 Cards
        self.top_container = ctk.CTkFrame(self.scroll, fg_color="transparent")
        self.top_container.pack(fill="x", pady=10)
        self.top_container.columnconfigure((0,1,2), weight=1, uniform="group1")

        self.card_artist = self.create_top_5_card(self.top_container, "Top Artists", 0)
        self.card_album = self.create_top_5_card(self.top_container, "Top Albums", 1)
        self.card_track = self.create_top_5_card(self.top_container, "Top Tracks", 2)

        # 3. Charts Section
        self.charts_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        self.charts_frame.pack(fill="x", padx=10, pady=10)
        self.charts_frame.columnconfigure((0,1), weight=1, uniform="group2")

        # Listening Clock
        self.clock_frame = ctk.CTkFrame(self.charts_frame, fg_color=self.col_card)
        self.clock_frame.grid(row=0, column=0, padx=5, sticky="nsew")
        
        header_clock = ctk.CTkFrame(self.clock_frame, fg_color="transparent")
        header_clock.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(header_clock, text="Listening Clock", font=("Arial", 12, "bold")).pack(anchor="w")
        self.lbl_busiest_hour = ctk.CTkLabel(header_clock, text="-", font=("SF Pro Display", 13), text_color=self.col_accent)
        self.lbl_busiest_hour.pack(anchor="w")

        self.clock_canvas_area = ctk.CTkFrame(self.clock_frame, fg_color="transparent")
        self.clock_canvas_area.pack(fill="both", expand=True, padx=5, pady=5)

        # Weekly Activity
        self.weekly_frame = ctk.CTkFrame(self.charts_frame, fg_color=self.col_card)
        self.weekly_frame.grid(row=0, column=1, padx=5, sticky="nsew")
        
        header_week = ctk.CTkFrame(self.weekly_frame, fg_color="transparent")
        header_week.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(header_week, text="Weekly Activity", font=("Arial", 12, "bold")).pack(anchor="w")
        self.lbl_busiest_day = ctk.CTkLabel(header_week, text="-", font=("SF Pro Display", 13), text_color=self.col_accent)
        self.lbl_busiest_day.pack(anchor="w")

        self.weekly_canvas_area = ctk.CTkFrame(self.weekly_frame, fg_color="transparent")
        self.weekly_canvas_area.pack(fill="both", expand=True, padx=5, pady=5)

    def create_metric_label(self, parent, title, value, col):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=0, column=col, pady=20)
        val_lbl = ctk.CTkLabel(frame, text=value, font=("SF Pro Display", 32, "bold"), text_color=self.col_accent)
        val_lbl.pack()
        ctk.CTkLabel(frame, text=title, font=("Arial", 12), text_color="gray").pack()
        return val_lbl

    def create_top_5_card(self, parent, title, col):
        """Creates the layout for a Top 5 ranking card."""
        card = ctk.CTkFrame(parent, fg_color=self.col_card, corner_radius=10)
        card.grid(row=0, column=col, sticky="nsew", padx=5)
        
        header = ctk.CTkFrame(card, height=30, fg_color=self.col_accent, corner_radius=10)
        header.pack(fill="x")
        ctk.CTkLabel(header, text=title, font=("Arial", 12, "bold"), text_color="white").place(relx=0.5, rely=0.5, anchor="center")

        # Rank #1
        rank1_frame = ctk.CTkFrame(card, fg_color="transparent")
        rank1_frame.pack(fill="x", pady=(15, 10))
        
        img_lbl = ctk.CTkLabel(rank1_frame, text="💿", font=("Arial", 40))
        img_lbl.pack()
        
        name_lbl = ctk.CTkLabel(rank1_frame, text="-", font=("SF Pro Display", 16, "bold"), wraplength=180)
        name_lbl.pack(padx=10)
        count_lbl = ctk.CTkLabel(rank1_frame, text="-", font=("Arial", 12), text_color="gray")
        count_lbl.pack()

        ctk.CTkFrame(card, height=1, fg_color="#333").pack(fill="x", padx=20, pady=5)

        # Ranks #2-5
        list_frame = ctk.CTkFrame(card, fg_color="transparent")
        list_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        return {
            "img": img_lbl,
            "name": name_lbl,
            "count": count_lbl,
            "list_container": list_frame
        }

    def update_stats(self, filter_val):
        if self.data.df.empty:
            self.data.parse_log()
            if self.data.df.empty: return

        df = self.data.df.copy()
        now = pd.Timestamp.now()

        if filter_val == "This Year":
            df = df[df['dt'].dt.year == now.year]
        elif filter_val == "This Month":
            df = df[(df['dt'].dt.year == now.year) & (df['dt'].dt.month == now.month)]
        elif filter_val == "This Week":
            start_date = now - pd.Timedelta(days=7)
            df = df[df['dt'] >= start_date]

        if df.empty: 
            self.lbl_minutes.configure(text="0")
            self.lbl_plays.configure(text="0")
            return 

        total_ms = df['play_ms'].sum()
        total_minutes = int(total_ms / 1000 / 60)
        
        valid_df = df[df['valid_play'] == True]
        total_plays = len(valid_df)
        
        days_range = (df['dt'].max() - df['dt'].min()).days
        days_range = max(1, days_range)
        avg_plays = int(total_plays / days_range)

        self.lbl_minutes.configure(text=f"{total_minutes:,}")
        self.lbl_plays.configure(text=f"{total_plays:,}")
        self.lbl_avg.configure(text=str(avg_plays))

        if not valid_df.empty:
            self.update_top_5_ui(self.card_artist, valid_df, 'artist')
            self.update_top_5_ui(self.card_album, valid_df, 'album')
            self.update_top_5_ui(self.card_track, valid_df, 'title')
        
        self.draw_listening_clock(valid_df)
        self.draw_weekly_activity(valid_df)

    def update_top_5_ui(self, ui_refs, df, col_name):
        top_data = df[col_name].value_counts().head(5)
        if top_data.empty: return
        
        top_name = top_data.index[0]
        top_count = top_data.iloc[0]
        
        ui_refs['name'].configure(text=top_name)
        ui_refs['count'].configure(text=f"{top_count} plays")
        
        sample_row = df[df[col_name] == top_name].iloc[0]
        rockbox_path = sample_row['original_path']
        pil_img = self.data.get_album_art(rockbox_path)
        
        if pil_img:
            ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(100, 100))
            ui_refs['img'].configure(image=ctk_img, text="")
        else:
            ui_refs['img'].configure(image=None, text="🎵")

        for widget in ui_refs['list_container'].winfo_children():
            widget.destroy()
            
        for i, (name, count) in enumerate(top_data.iloc[1:].items(), start=2):
            row = ctk.CTkFrame(ui_refs['list_container'], fg_color="transparent")
            row.pack(fill="x", pady=2)
            
            display_name = (name[:22] + '..') if len(name) > 22 else name
            
            ctk.CTkLabel(row, text=f"{i}. {display_name}", font=("Arial", 11), anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=f"{count}", font=("Arial", 11, "bold"), text_color="gray").pack(side="right")

    def draw_listening_clock(self, df):
        for widget in self.clock_canvas_area.winfo_children(): widget.destroy()
        if df.empty: 
            self.lbl_busiest_hour.configure(text="-")
            return

        hours = df['dt'].dt.hour
        hour_counts = hours.value_counts().sort_index()
        
        if not hour_counts.empty:
            busiest_h = hour_counts.idxmax()
            busiest_count = hour_counts.max()
            time_str = datetime.time(busiest_h, 0).strftime("%I:00 %p")
            self.lbl_busiest_hour.configure(text=f"Peak hour: {time_str} ({busiest_count} plays)")
        else:
            self.lbl_busiest_hour.configure(text="-")

        all_hours = range(24)
        counts = [hour_counts.get(h, 0) for h in all_hours]

        fig = Figure(figsize=(4, 2.5), dpi=100, facecolor=self.col_card)
        ax = fig.add_subplot(111, polar=True)
        ax.set_facecolor(self.col_card)
        
        theta = np.linspace(0.0, 2 * np.pi, 24, endpoint=False)
        width = (2*np.pi) / 24
        
        ax.bar(theta, counts, width=width, bottom=0.0, color=self.col_accent, alpha=0.8)
        
        ax.set_theta_zero_location("N")
        ax.set_theta_direction(-1)
        ax.set_xticks(np.linspace(0, 2*np.pi, 4, endpoint=False))
        ax.set_xticklabels(['00', '06', '12', '18'], color="white", fontsize=8)
        ax.set_yticklabels([])
        ax.grid(False)
        ax.spines['polar'].set_visible(False)

        canvas = FigureCanvasTkAgg(fig, master=self.clock_canvas_area)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def draw_weekly_activity(self, df):
        for widget in self.weekly_canvas_area.winfo_children(): widget.destroy()
        if df.empty: 
            self.lbl_busiest_day.configure(text="-")
            return

        days = df['dt'].dt.dayofweek
        day_counts = days.value_counts().sort_index()
        labels_full = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        labels_short = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        
        if not day_counts.empty:
            busiest_d_idx = day_counts.idxmax()
            busiest_d_count = day_counts.max()
            day_name = labels_full[busiest_d_idx]
            self.lbl_busiest_day.configure(text=f"Favorite day: {day_name} ({busiest_d_count} plays)")
        else:
            self.lbl_busiest_day.configure(text="-")

        all_days = range(7)
        counts = [day_counts.get(d, 0) for d in all_days]

        fig = Figure(figsize=(4, 2.5), dpi=100, facecolor=self.col_card)
        ax = fig.add_subplot(111)
        ax.set_facecolor(self.col_card)
        
        ax.bar(labels_short, counts, color=self.col_accent, alpha=0.8)
        
        ax.tick_params(axis='x', colors='white', labelsize=9)
        ax.tick_params(axis='y', colors='gray', labelsize=8)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.spines['bottom'].set_color('#444')
        
        canvas = FigureCanvasTkAgg(fig, master=self.weekly_canvas_area)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)