import customtkinter as ctk
from tkinter import messagebox, simpledialog
import requests
import threading
import pandas as pd
import webbrowser
import json
import os
import hashlib
import time
from PIL import Image
from io import BytesIO

class DiscoveryTab(ctk.CTkFrame):
    def __init__(self, master, data_manager, theme_manager):
        super().__init__(master)
        self.data = data_manager
        self.theme = theme_manager
        self.config_file = "config.json"
        
        # Session variables
        self.api_key = ""
        self.shared_secret = ""
        self.session_key = ""
        self.last_scrobble_time = 0

        # UI Header
        info_lbl = ctk.CTkLabel(self, text="Last.fm: Discovery & Scrobbling\nSync your iPod with your profile and discover new music.",
                                font=("Arial", 12), text_color="gray")
        info_lbl.pack(pady=(10, 5))

        # Credentials Section
        cred_frame = ctk.CTkFrame(self, fg_color="transparent")
        cred_frame.pack(fill="x", padx=20, pady=5)
        
        cred_frame.columnconfigure(1, weight=1)
        
        ctk.CTkLabel(cred_frame, text="API Key:").grid(row=0, column=0, sticky="w", padx=5)
        self.entry_apikey = ctk.CTkEntry(cred_frame, placeholder_text="Your API Key")
        self.entry_apikey.grid(row=0, column=1, sticky="ew", padx=5, pady=2)

        ctk.CTkLabel(cred_frame, text="Shared Secret:").grid(row=1, column=0, sticky="w", padx=5)
        self.entry_secret = ctk.CTkEntry(cred_frame, placeholder_text="Your Shared Secret (required for scrobbling)", show="*")
        self.entry_secret.grid(row=1, column=1, sticky="ew", padx=5, pady=2)

        # Login Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=5)
        
        self.btn_login = ctk.CTkButton(btn_frame, text="🔑 Connect with Last.fm", command=self.auth_process, 
                                       width=150, fg_color=self.theme.get("accent"), hover_color=self.theme.get("accent_hover"))
        self.btn_login.pack(side="left", padx=5)

        self.lbl_user_status = ctk.CTkLabel(btn_frame, text="Not connected", text_color="gray")
        self.lbl_user_status.pack(side="left", padx=10)

        self.load_config()

        # Separator
        ctk.CTkFrame(self, height=2, fg_color="#333").pack(fill="x", padx=20, pady=10)

        # Scrobbling Section
        scrobble_frame = ctk.CTkFrame(self, fg_color="#2B2B2B")
        scrobble_frame.pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(scrobble_frame, text="Synchronization (Scrobbling)", font=("SF Pro Display", 14, "bold")).pack(pady=5)
        
        self.lbl_scrobble_info = ctk.CTkLabel(scrobble_frame, text="Analyze your log to submit past playbacks.")
        self.lbl_scrobble_info.pack(pady=2)

        self.btn_scrobble = ctk.CTkButton(scrobble_frame, text="🚀 Submit Scrobbling to Profile", 
                                          command=self.start_scrobble_thread,
                                          fg_color=self.theme.get("error"), hover_color=self.theme.get("error"), state="disabled")
        self.btn_scrobble.pack(pady=10, fill="x", padx=40)

        # Discovery Section
        ctk.CTkLabel(self, text="Discovery (Based on History)", font=("SF Pro Display", 14, "bold")).pack(pady=(20, 5))
        
        self.btn_discover = ctk.CTkButton(self, text="🔎 Get Recommendations", command=self.start_discovery_thread)
        self.btn_discover.pack(pady=5, padx=40, fill="x")

        self.results_frame = ctk.CTkScrollableFrame(self, label_text="Recommendations")
        self.results_frame.pack(pady=10, padx=20, fill="both", expand=True)

    def load_config(self):
        """Loads credentials and last scrobble state from config file."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.api_key = config.get("api_key", "")
                    self.shared_secret = config.get("shared_secret", "")
                    self.session_key = config.get("session_key", "")
                    self.last_scrobble_time = config.get("last_scrobble_time", 0)

                    self.entry_apikey.insert(0, self.api_key)
                    self.entry_secret.insert(0, self.shared_secret)

                    if self.session_key:
                        self.lbl_user_status.configure(text="✅ Connected", text_color="#1DB954")
                        self.btn_scrobble.configure(state="normal")
                        self.btn_login.configure(state="disabled", text="Session Active")
            except: pass

    def save_config(self):
        """Saves session and credentials to local JSON."""
        data = {}
        if os.path.exists(self.config_file):
            try: 
                with open(self.config_file, 'r') as f: data = json.load(f)
            except: pass
        
        data["api_key"] = self.api_key
        data["shared_secret"] = self.shared_secret
        data["session_key"] = self.session_key
        data["last_scrobble_time"] = self.last_scrobble_time
        
        try:
            with open(self.config_file, 'w') as f: json.dump(data, f, indent=4)
        except: pass

    def auth_process(self):
        """Initializes the authentication flow."""
        self.api_key = self.entry_apikey.get().strip()
        self.shared_secret = self.entry_secret.get().strip()
        
        if not self.api_key or not self.shared_secret:
            messagebox.showwarning("Missing data", "API Key and Shared Secret are required to connect.")
            return

        threading.Thread(target=self.run_auth, daemon=True).start()

    def run_auth(self):
        """Requests auth token and opens browser for user authorization."""
        try:
            sig = self.sign_request({'method': 'auth.getToken', 'api_key': self.api_key})
            url = f"http://ws.audioscrobbler.com/2.0/?method=auth.getToken&api_key={self.api_key}&api_sig={sig}&format=json"
            resp = requests.get(url).json()
            token = resp['token']

            auth_url = f"http://www.last.fm/api/auth/?api_key={self.api_key}&token={token}"
            webbrowser.open(auth_url)
            
            self.after(0, lambda: self.confirm_session(token))
            
        except Exception as e:
            messagebox.showerror("Error", f"Connection error: {e}")

    def confirm_session(self, token):
        msg = "Your browser has been opened.\n\n1. Click 'Yes, Allow Access' on the website.\n2. Return here and click 'Yes'.\n\nHave you authorized the app?"
        ans = messagebox.askyesno("Confirm Authorization", msg)
        if ans:
            self.get_session(token)

    def get_session(self, token):
        """Retrieves the permanent session key from Last.fm."""
        try:
            params = {'method': 'auth.getSession', 'api_key': self.api_key, 'token': token}
            params['api_sig'] = self.sign_request(params)
            params['format'] = 'json'
            
            resp = requests.get("http://ws.audioscrobbler.com/2.0/", params=params).json()
            
            if 'session' in resp:
                self.session_key = resp['session']['key']
                user = resp['session']['name']
                self.save_config()
                self.lbl_user_status.configure(text=f"✅ {user}", text_color="#1DB954")
                self.btn_scrobble.configure(state="normal")
                self.btn_login.configure(state="disabled")
                messagebox.showinfo("Success", f"Connected as {user}. Scrobbling is now enabled.")
            else:
                messagebox.showerror("Error", "Could not obtain session. Please try again.")
        except Exception as e:
            messagebox.showerror("Error", f"Session retrieval failed: {e}")

    def sign_request(self, params):
        """Generates MD5 signature required by Last.fm for write operations."""
        keys = sorted(params.keys())
        sig_str = "".join(f"{k}{params[k]}" for k in keys) + self.shared_secret
        return hashlib.md5(sig_str.encode('utf-8')).hexdigest()

    def start_scrobble_thread(self):
        if not self.session_key: return
        if not self.data.drive_path:
            messagebox.showwarning("Error", "Please select your iPod drive first.")
            return
            
        self.btn_scrobble.configure(state="disabled", text="Processing...")
        threading.Thread(target=self.run_scrobble, daemon=True).start()

    def run_scrobble(self):
        """Processes the playback log and sends new tracks to Last.fm."""
        if not self.data.parse_log() or self.data.df.empty:
            self.reset_scrobble_btn()
            return

        df = self.data.df
        pending = df[
            (df['valid_play'] == True) & 
            (df['timestamp'] > self.last_scrobble_time)
        ].copy() 

        if pending.empty:
            self.after(0, lambda: messagebox.showinfo("Info", "No new songs to submit."))
            self.reset_scrobble_btn()
            return

        total = len(pending)
        sent_count = 0
        batch_size = 50
        chunks = [pending[i:i + batch_size] for i in range(0, pending.shape[0], batch_size)]

        self.update_info(f"Sending {total} songs in {len(chunks)} batches...")

        for chunk in chunks:
            payload = {
                'method': 'track.scrobble',
                'api_key': self.api_key,
                'sk': self.session_key
            }
            
            idx = 0
            max_ts_in_chunk = 0
            
            for _, row in chunk.iterrows():
                # Rockbox logs the end time. Last.fm expects start time.
                start_ts = int(row['timestamp'] - (row['play_ms'] / 1000))
                
                payload[f'artist[{idx}]'] = row['artist']
                payload[f'track[{idx}]'] = row['title']
                payload[f'album[{idx}]'] = row['album']
                payload[f'timestamp[{idx}]'] = start_ts
                
                if row['timestamp'] > max_ts_in_chunk:
                    max_ts_in_chunk = row['timestamp']
                idx += 1
            
            payload['api_sig'] = self.sign_request(payload)
            payload['format'] = 'json'

            try:
                resp = requests.post("http://ws.audioscrobbler.com/2.0/", data=payload)
                if resp.status_code == 200:
                    sent_count += idx
                    self.last_scrobble_time = max_ts_in_chunk 
                    self.save_config() 
                    self.update_info(f"Sent: {sent_count}/{total}")
                else:
                    print(f"Last.fm Error: {resp.text}")
            except Exception as e:
                print(f"Network error: {e}")
            
            time.sleep(0.5) 

        self.reset_scrobble_btn()
        self.after(0, lambda: messagebox.showinfo("Scrobbling Finished", f"{sent_count} tracks were successfully sent to Last.fm."))

    def update_info(self, text):
        self.after(0, lambda: self.lbl_scrobble_info.configure(text=text))

    def reset_scrobble_btn(self):
        self.after(0, lambda: self.btn_scrobble.configure(state="normal", text="🚀 Submit Scrobbling to Profile"))

    def start_discovery_thread(self):
        key = self.api_key if self.api_key else self.entry_apikey.get()
        if not key:
             messagebox.showwarning("Error", "Missing API Key")
             return
        
        for widget in self.results_frame.winfo_children(): widget.destroy()
        ctk.CTkLabel(self.results_frame, text="⏳ Searching...").pack()
        threading.Thread(target=self.run_discovery, args=(key,), daemon=True).start()

    def run_discovery(self, api_key):
        """Fetches similar artists based on recent listening history."""
        if not self.data.parse_log() or self.data.df.empty: return
        self.data.scan_library_artists()
        df = self.data.df
        df = df[df['valid_play'] == True].copy()
        
        last_date = df['dt'].max()
        df['days_ago'] = (last_date - df['dt']).dt.days.clip(lower=0)
        df['score'] = 0.95 ** df['days_ago']
        top_artists = df.groupby('artist')['score'].sum().sort_values(ascending=False).head(5).index.tolist()

        recommendations = []
        seen_recs = set()
        session = requests.Session()

        for source in top_artists:
            clean_source = self.data.normalize_text(source)
            if source == "Unknown": continue
            
            try:
                url = "http://ws.audioscrobbler.com/2.0/"
                params = {'method': 'artist.getsimilar', 'artist': source, 'api_key': api_key, 'format': 'json', 'limit': 8, 'autocorrect': 1}
                data = session.get(url, params=params, timeout=5).json()
                
                if 'similarartists' in data:
                    count = 0
                    for sim in data['similarartists']['artist']:
                        rec_name = sim['name']
                        clean_rec = self.data.normalize_text(rec_name)
                        if rec_name not in seen_recs and clean_rec not in self.data.library_artists and clean_rec != clean_source:
                            
                            img_url = ""
                            if 'image' in sim:
                                for img in sim['image']:
                                    if img['size'] == 'extralarge': img_url = img['#text']
                            
                            img_data = None
                            if img_url:
                                try:
                                    r = session.get(img_url, timeout=3)
                                    if r.status_code == 200: img_data = BytesIO(r.content)
                                except: pass

                            recommendations.append({'name': rec_name, 'reason': source, 'url': sim.get('url',''), 'img_bytes': img_data})
                            seen_recs.add(rec_name)
                            count += 1
                            if count >= 2: break
            except: pass
            if len(recommendations) >= 10: break

        self.after(0, lambda: self.show_results(recommendations, top_artists))

    def show_results(self, recs, sources):
        for widget in self.results_frame.winfo_children(): widget.destroy()
        ctk.CTkLabel(self.results_frame, text=f"Based on: {', '.join(sources)}", text_color="gray").pack(pady=(0,10))
        
        if not recs:
            ctk.CTkLabel(self.results_frame, text="No results found.").pack()
            return

        for item in recs:
            card = ctk.CTkFrame(self.results_frame, fg_color="#2B2B2B")
            card.pack(pady=5, padx=5, fill="x")
            
            try:
                if item['img_bytes']:
                    pil = Image.open(item['img_bytes'])
                    ctk_img = ctk.CTkImage(pil, size=(60,60))
                    ctk.CTkLabel(card, text="", image=ctk_img).pack(side="left", padx=10, pady=5)
            except: 
                ctk.CTkLabel(card, text="🎵", font=("Arial", 25)).pack(side="left", padx=15)

            ctk.CTkLabel(card, text=item['name'], font=("Arial", 14, "bold")).pack(anchor="w", pady=(10,0))
            ctk.CTkLabel(card, text=f"Because you listen to {item['reason']}", font=("Arial", 11), text_color="gray").pack(anchor="w")
            ctk.CTkButton(card, text="View", width=50, height=25, command=lambda u=item['url']: webbrowser.open(u)).pack(side="right", padx=10)