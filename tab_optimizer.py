import customtkinter as ctk
from tkinter import filedialog, messagebox, Toplevel
import os
import io
import threading
import requests
from PIL import Image, ImageTk
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, error as ID3Error
from mutagen.mp4 import MP4, MP4Cover
from mutagen.flac import FLAC, Picture

class OptimizerTab(ctk.CTkFrame):
    def __init__(self, master, data_manager, theme_manager):
        super().__init__(master)
        self.data = data_manager
        self.theme = theme_manager
        
        self.selected_path = ctk.StringVar()
        self.stop_event = threading.Event()
        self.is_running = False

        # --- UI LAYOUT ---
        sel_frame = ctk.CTkFrame(self)
        sel_frame.pack(fill="x", padx=20, pady=20)

        ctk.CTkLabel(sel_frame, text="Target:", font=("Arial", 12, "bold")).pack(side="left", padx=10)
        self.entry_path = ctk.CTkEntry(sel_frame, textvariable=self.selected_path, width=400, placeholder_text="Select Artist or Album folder...")
        self.entry_path.pack(side="left", padx=10)
        ctk.CTkButton(sel_frame, text="📂", width=40, command=self.select_folder).pack(side="left", padx=5)

        opt_frame = ctk.CTkFrame(self, fg_color="transparent")
        opt_frame.pack(fill="x", padx=20, pady=5)
        
        self.chk_force = ctk.CTkCheckBox(opt_frame, text="Force replace (Even if image exists)", font=("Arial", 12))
        self.chk_force.pack(side="left", padx=10)

        self.chk_singles = ctk.CTkCheckBox(opt_frame, text="Singles Mode (Search art for individual tracks)", font=("Arial", 12))
        self.chk_singles.pack(side="left", padx=10)

        self.btn_run = ctk.CTkButton(self, text="🛠 Optimize for Rockbox & PictureFlow", 
                                     command=self.start_optimization, 
                                     fg_color=self.theme.get("accent"), hover_color=self.theme.get("accent_hover"), height=40)
        self.btn_run.pack(fill="x", padx=40, pady=20)

        self.log_box = ctk.CTkTextbox(self, width=600, height=350, font=("Consolas", 11))
        self.log_box.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        self.log_box.configure(state="disabled")

    def select_folder(self):
        initial = self.data.music_path if self.data.music_path else "/"
        folder = filedialog.askdirectory(initialdir=initial)
        if folder:
            self.selected_path.set(folder)

    def log(self, message):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", message + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def start_optimization(self):
        path = self.selected_path.get()
        if not path or not os.path.exists(path):
            messagebox.showerror("Error", "Please select a valid folder.")
            return

        self.btn_run.configure(state="disabled", text="Processing... (Check log)")
        self.log_box.configure(state="normal")
        self.log_box.delete("0.0", "end")
        self.log_box.configure(state="disabled")
        
        self.is_running = True
        threading.Thread(target=self.run_process, args=(path,), daemon=True).start()

    def run_process(self, root_path):
        """Main optimization loop."""
        self.log(f"Starting optimization in: {root_path}\n{'='*50}")
        
        force_replace = self.chk_force.get()
        singles_mode = self.chk_singles.get()
        
        for root, dirs, files in os.walk(root_path):
            audio_files = [f for f in files if f.lower().endswith(('.mp3', '.m4a', '.flac'))]
            
            if not audio_files:
                continue

            # --- SINGLES MODE ---
            if singles_mode:
                self.log(f"📂 Folder: {os.path.basename(root)} (SINGLES MODE)")
                
                for f in audio_files:
                    full_p = os.path.join(root, f)
                    meta = self.get_metadata(full_p)
                    artist = meta.get('artist', 'Unknown')
                    title = meta.get('title', f)
                    
                    header_msg = f"   🎵 {title} ({artist})"
                    current_art = self.extract_art(full_p)
                    
                    if current_art and not force_replace:
                        self.log(f"{header_msg} -> OK (Already has an image)")
                        continue
                    
                    self.log(f"{header_msg} -> Searching...")
                    options = self.search_internet_covers(artist, "", title=title)
                    
                    final_image_data = None
                    if options:
                        self.selected_cover_data = None
                        self.waiting_selection = True
                        
                        self.after(0, lambda a=artist, t=title, o=options: self.show_selection_dialog(f"{a} - {t}", "", o))
                        
                        while self.waiting_selection:
                            import time; time.sleep(0.1)
                            
                        if self.selected_cover_data:
                            final_image_data = self.process_image(self.selected_cover_data)
                            self.embed_art(full_p, final_image_data)
                            self.log(f"      ✅ Image embedded.")
                        else:
                            self.log(f"      ❌ Selection canceled.")
                    else:
                        self.log(f"      ⚠ Not found online.")

            # --- ALBUM MODE ---
            else:
                first_file = os.path.join(root, audio_files[0])
                meta = self.get_metadata(first_file)
                artist = meta.get('artist', 'Unknown')
                album = meta.get('album', 'Unknown')
                
                header_msg = f"💿 {artist} – {album}"
                current_art_data = self.extract_art(first_file)
                final_image_data = None
                status_msg = ""

                if current_art_data and not force_replace:
                    if self.needs_optimization(current_art_data):
                        final_image_data = self.process_image(current_art_data)
                        status_msg = "Optimized (Re-compressed .jpg)."
                    else:
                        bmp_path = os.path.join(root, "cover.bmp")
                        if not os.path.exists(bmp_path):
                            final_image_data = self.process_image(current_art_data)
                            status_msg = "Image OK, generating missing .bmp."
                        else:
                            status_msg = "Everything OK."
                            final_image_data = None 

                if not current_art_data or force_replace:
                    self.log(f"{header_msg} -> Searching for covers...")
                    options = self.search_internet_covers(artist, album, "")
                    
                    if options:
                        self.selected_cover_data = None
                        self.waiting_selection = True
                        self.after(0, lambda: self.show_selection_dialog(artist, album, options))
                        
                        while self.waiting_selection:
                            import time; time.sleep(0.1)
                        
                        if self.selected_cover_data:
                            final_image_data = self.process_image(self.selected_cover_data)
                            status_msg = "New image applied."
                        else:
                             status_msg = "Canceled."
                    else:
                        status_msg = "Not found."

                if final_image_data:
                    try:
                        with open(os.path.join(root, "cover.jpg"), "wb") as f:
                            f.write(final_image_data)
                        
                        img = Image.open(io.BytesIO(final_image_data))
                        img.save(os.path.join(root, "cover.bmp"))
                    except Exception as e:
                        self.log(f"Error writing local files: {e}")

                    for f in audio_files:
                        full_p = os.path.join(root, f)
                        self.embed_art(full_p, final_image_data)
                
                self.log(f"{header_msg}\nResult: {status_msg}\n{'-'*30}")

        self.log("\nProcess Finished.")
        self.btn_run.configure(state="normal", text="🛠 Optimize for Rockbox")
        self.is_running = False

    def needs_optimization(self, img_data):
        """Checks if image meets Rockbox criteria (Max 500x500, non-progressive)."""
        try:
            img = Image.open(io.BytesIO(img_data))
            if img.width > 500 or img.height > 500: return True
            if 'progressive' in img.info: return True
            if img.mode != 'RGB': return True
            return False
        except: return True

    def process_image(self, img_data):
        """Standardizes image: 500x500, RGB, baseline JPEG."""
        try:
            img = Image.open(io.BytesIO(img_data))
            if img.mode != 'RGB': img = img.convert('RGB')
            img = img.resize((500, 500), Image.Resampling.LANCZOS)
            out_io = io.BytesIO()
            img.save(out_io, format='JPEG', quality=85, progressive=False, optimize=True)
            return out_io.getvalue()
        except Exception as e:
            self.log(f"Error processing image: {e}")
            return None

    def get_metadata(self, path):
        meta = {'artist': 'Unknown', 'album': 'Unknown', 'title': ''}
        try:
            if path.endswith('.mp3'):
                audio = ID3(path)
                meta['artist'] = str(audio.get('TPE1', 'Unknown'))
                meta['album'] = str(audio.get('TALB', 'Unknown'))
                meta['title'] = str(audio.get('TIT2', ''))
            elif path.endswith('.m4a'):
                audio = MP4(path)
                meta['artist'] = audio.tags.get('\xa9ART', ['Unknown'])[0]
                meta['album'] = audio.tags.get('\xa9alb', ['Unknown'])[0]
                meta['title'] = audio.tags.get('\xa9nam', [''])[0]
            elif path.endswith('.flac'):
                audio = FLAC(path)
                meta['artist'] = audio.get('artist', ['Unknown'])[0]
                meta['album'] = audio.get('album', ['Unknown'])[0]
                meta['title'] = audio.get('title', [''])[0]
        except: pass
        return meta

    def extract_art(self, path):
        try:
            if path.endswith('.mp3'):
                audio = ID3(path)
                for key in audio.keys():
                    if key.startswith('APIC'):
                        return audio[key].data
            elif path.endswith('.m4a'):
                audio = MP4(path)
                if 'covr' in audio.tags:
                    return audio.tags['covr'][0]
            elif path.endswith('.flac'):
                audio = FLAC(path)
                if audio.pictures:
                    return audio.pictures[0].data
        except: pass
        return None

    def embed_art(self, path, img_data):
        try:
            if path.endswith('.mp3'):
                audio = MP3(path, ID3=ID3)
                try: audio.add_tags()
                except ID3Error: pass
                audio.tags.delall("APIC")
                audio.tags.add(
                    APIC(encoding=3, mime='image/jpeg', type=3, desc=u'Cover', data=img_data)
                )
                audio.save()
            elif path.endswith('.m4a'):
                audio = MP4(path)
                audio.tags['covr'] = [img_data]
                audio.save()
            elif path.endswith('.flac'):
                audio = FLAC(path)
                audio.clear_pictures()
                pic = Picture()
                pic.type = 3
                pic.mime = "image/jpeg"
                pic.desc = "Cover"
                pic.data = img_data
                audio.add_picture(pic)
                audio.save()
        except Exception as e:
            self.log(f"Error embedding in {os.path.basename(path)}: {e}")

    def search_internet_covers(self, artist, album, title=""):
        """Fetches cover art from iTunes and Deezer APIs."""
        urls = []
        term = f"{artist} {title}" if title else f"{artist} {album}"
        
        try:
            res = requests.get("https://itunes.apple.com/search", 
                               params={"term": term, "media": "music", "limit": 4}, timeout=5).json()
            urls += [item['artworkUrl100'].replace('100x100bb', '600x600bb') for item in res.get('results', [])]
        except: pass
        
        try:
            q = f'artist:"{artist}" track:"{title}"' if title else f'artist:"{artist}" album:"{album}"'
            res = requests.get(f"https://api.deezer.com/search?q={q}&limit=2", timeout=5).json()
            if 'data' in res:
                urls += [item['album']['cover_xl'] for item in res.get('data', [])]
        except: pass

        imgs = []
        unique_urls = list(dict.fromkeys(urls))
        for url in unique_urls:
            if len(imgs) >= 5: break
            try:
                r = requests.get(url, timeout=5)
                if r.status_code == 200:
                    imgs.append(r.content)
            except: pass
        return imgs

    def show_selection_dialog(self, title_display, subtitle, img_list):
        """Opens a dialog for the user to choose between found covers."""
        dialog = ctk.CTkToplevel(self)
        dialog.title(f"Select: {title_display}")
        dialog.geometry("850x330")
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()
        
        label_text = f"Cover art for: {title_display}"
        if subtitle: label_text += f"\n({subtitle})"
        
        ctk.CTkLabel(dialog, text=label_text, font=("Arial", 14, "bold")).pack(pady=10)

        frame = ctk.CTkScrollableFrame(dialog, orientation="horizontal", height=200)
        frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.dialog_images = []

        def select(idx):
            self.selected_cover_data = img_list[idx]
            self.waiting_selection = False
            dialog.destroy()

        def cancel():
            self.selected_cover_data = None
            self.waiting_selection = False
            dialog.destroy()
            
        ctk.CTkButton(dialog, text="Skip / Cancel", command=cancel, fg_color=self.theme.get("warning")).pack(pady=5)

        for i, img_data in enumerate(img_list):
            try:
                pil_img = Image.open(io.BytesIO(img_data)).resize((150, 150))
                ctk_img = ctk.CTkImage(pil_img, size=(150, 150))
                self.dialog_images.append(ctk_img)
                
                btn = ctk.CTkButton(frame, text="", image=ctk_img, width=160, height=160,
                                    command=lambda idx=i: select(idx), fg_color="transparent", border_width=2)
                btn.pack(side="left", padx=10)
            except: pass

        dialog.protocol("WM_DELETE_WINDOW", cancel)