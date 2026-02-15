import json
import os

class ThemeManager:
    def __init__(self):
        self.config_file = "theme_config.json"
        
        # Default palette (Sober and elegant, "Dark Modern" style)
        self.defaults = {
            "accent": "#3B8ED0",       # CTk standard blue
            "accent_hover": "#36719F",
            "card_bg": "#242424",      # Card/Panel background
            "text_main": "#FFFFFF",
            "text_sub": "#A0A0A0",     # Secondary gray text
            "success": "#2CC985",
            "error": "#E04F5F",
            "warning": "#E5B04D"
        }
        
        self.colors = self.load_theme()

    def load_theme(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    # Merge with defaults in case new keys are missing
                    return {**self.defaults, **data}
            except:
                pass
        return self.defaults.copy()

    def save_theme(self, new_colors):
        self.colors = new_colors
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.colors, f, indent=4)
        except Exception as e:
            print(f"Error saving theme: {e}")

    def get(self, key):
        return self.colors.get(key, self.defaults.get(key, "#FFFFFF"))