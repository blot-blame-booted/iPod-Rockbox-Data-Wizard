import pandas as pd
import os
import datetime
import re
import glob
import json
from mutagen import File 
from mutagen.easyid3 import EasyID3
from mutagen.flac import FLAC
from mutagen.mp4 import MP4
from io import BytesIO
from PIL import Image

class RockboxData:
    def __init__(self):
        self.drive_path = ""
        self.log_path = ""
        self.music_path = ""
        self.playlist_path = ""
        self.df = pd.DataFrame()
        self.existing_playlist_songs = set()
        self.library_artists = set()
        self.cache_file = "metadata_cache.json"
        self.tag_cache = self.load_cache()

    def load_cache(self):
        """Loads metadata cache from a local JSON file."""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading cache: {e}")
        return {}

    def save_cache(self):
        """Saves current memory cache to a JSON file."""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.tag_cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving cache: {e}")

    def set_paths(self, drive_path):
        self.drive_path = drive_path
        self.log_path = os.path.join(drive_path, ".rockbox", "playback.log")
        self.music_path = os.path.join(drive_path, "Music")
        self.playlist_path = os.path.join(drive_path, "Playlists")

        if not os.path.exists(self.log_path):
            alt = os.path.join(drive_path, "playback.log")
            if os.path.exists(alt):
                self.log_path = alt
                return False 
        return os.path.exists(self.log_path)

    def parse_log(self):
        """Reads the log and extracts real metadata from files."""
        if not self.log_path or not os.path.exists(self.log_path): return False
        
        data = []
        cache_updated = False

        try:
            with open(self.log_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()

            for line in lines:
                if line.startswith('#') or not line.strip(): continue
                parts = line.strip().split(':')
                
                if len(parts) >= 4:
                    try:
                        timestamp = int(parts[0])
                        play_ms = int(parts[1])
                        total_ms = int(parts[2])
                        
                        is_valid = False
                        if total_ms > 0:
                            ratio = play_ms / total_ms
                            if ratio >= 0.45 or play_ms >= 120000:
                                is_valid = True
                        
                        original_path = ":".join(parts[3:]) 
                        
                        artist, album, title, found_new = self.get_metadata(original_path)
                        if found_new:
                            cache_updated = True
                        
                        data.append({
                            'timestamp': timestamp,
                            'dt': datetime.datetime.fromtimestamp(timestamp),
                            'play_ms': play_ms,
                            'total_ms': total_ms,
                            'valid_play': is_valid,
                            'original_path': original_path,
                            'artist': artist,
                            'album': album,
                            'title': title
                        })
                    except ValueError: continue
            
            self.df = pd.DataFrame(data)
            
            if cache_updated:
                self.save_cache()
                
            return True
        except Exception as e:
            print(f"Error parsing log: {e}")
            return False

    def get_metadata(self, rockbox_path):
        """Returns: artist, album, title, is_new(bool)"""
        if rockbox_path in self.tag_cache:
            val = self.tag_cache[rockbox_path]
            return val[0], val[1], val[2], False

        rel_path = rockbox_path.replace("/<HDD0>/", "").replace("/", os.sep)
        full_path = os.path.join(self.drive_path, rel_path)

        artist, album, title = "Unknown", "Unknown Album", "Unknown Title"
        found_tags = False

        if os.path.exists(full_path):
            try:
                audio = File(full_path, easy=True) 
                if audio:
                    if 'artist' in audio: artist = audio['artist'][0]
                    if 'album' in audio: album = audio['album'][0]
                    if 'title' in audio: title = audio['title'][0]
                    found_tags = True
                
                if not found_tags and full_path.lower().endswith('.m4a'):
                    m4a = MP4(full_path)
                    if '\xa9ART' in m4a: artist = m4a['\xa9ART'][0]
                    if '\xa9alb' in m4a: album = m4a['\xa9alb'][0]
                    if '\xa9nam' in m4a: title = m4a['\xa9nam'][0]
                    found_tags = True
            except Exception:
                pass 

        if not found_tags or artist == "Unknown":
            path_parts = rockbox_path.replace("\\", "/").split("/")
            if len(path_parts) > 3:
                if "music" in path_parts[2].lower(): 
                    artist = path_parts[3]
                    if len(path_parts) > 4:
                        album = path_parts[4]
                filename = path_parts[-1]
                title = re.sub(r'^\d+[\.\s-]*', '', os.path.splitext(filename)[0])
            else:
                title = os.path.basename(rockbox_path)

        self.tag_cache[rockbox_path] = [artist, album, title]
        return artist, album, title, True

    def get_album_art(self, rockbox_path):
        rel_path = rockbox_path.replace("/<HDD0>/", "").replace("/", os.sep)
        full_path = os.path.join(self.drive_path, rel_path)

        if not os.path.exists(full_path):
            return None

        try:
            file = File(full_path)
            artwork_data = None
            if file.tags:
                if hasattr(file.tags, 'getall'): 
                    for tag in file.tags.keys():
                        if tag.startswith('APIC'): 
                            artwork_data = file.tags[tag].data
                            break
                if 'covr' in file.tags:
                    artwork_data = file.tags['covr'][0]
            if not artwork_data and hasattr(file, 'pictures') and file.pictures:
                artwork_data = file.pictures[0].data

            if artwork_data:
                return Image.open(BytesIO(artwork_data))
        except Exception:
            pass
        return None

    def scan_existing_playlists(self):
        self.existing_playlist_songs = set()
        if not os.path.exists(self.playlist_path): return

        for pl_file in glob.glob(os.path.join(self.playlist_path, "*.m3u8")):
            try:
                with open(pl_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if not line.startswith('#') and line.strip():
                            self.existing_playlist_songs.add(line.strip())
            except: pass

    def scan_library_artists(self):
        self.library_artists = set()
        if not os.path.exists(self.music_path): return
        try:
            for item in os.listdir(self.music_path):
                if os.path.isdir(os.path.join(self.music_path, item)):
                    self.library_artists.add(self.normalize_text(item))
        except: pass

    def normalize_text(self, text):
        text = str(text).lower()
        text = re.sub(r'[^\w\s]', '', text)
        return text.strip()