# 🧙‍♂️ iPod Rockbox Data Wizard

**iPod Rockbox Data Wizard** is a powerful, all-in-one desktop utility for iPods and digital media players running [Rockbox](https://www.rockbox.org/). It transforms your offline listening history into rich statistics, smart playlists, and Last.fm integrations, while providing tools to optimize your music library's metadata and album art.

---

## 🚀 Key Features

### 📊 Advanced Statistics
*   **Visual Insights:** View total minutes played, total plays, and average daily plays.
*   **Dynamic Rankings:** Top 5 Artists, Albums, and Tracks with album art visualization.
*   **Listening Clock:** A polar chart showing your peak listening hours.
*   **Weekly Activity:** A bar chart analyzing which days of the week you are most active.
*   **Time Filtering:** Filter all data by "All Time", "This Year", "This Month", or "This Week".

### 🎵 Smart Playlist Generator
*   **On Repeat:** Tracks you've been playing recently using a decay algorithm.
*   **Forgotten Favorites:** High-play tracks you haven't heard in over 6 months.
*   **Second Chance:** Randomly resurfaces tracks with very low play counts.
*   **Time Travel:** Automatically generates playlists based on specific years of activity.
*   **Flashback:** "This Month in History" – tracks played in the current month across previous years.

### 📡 Last.fm Discovery & Scrobbling
*   **Historical Scrobbling:** Sync your offline Rockbox playback log to your Last.fm profile.
*   **Smart Discovery:** Get artist recommendations based on your habits.
*   **Library Aware:** The recommendation engine filters out artists already present in your iPod's `Music` folder.

### 🖼️ Album Art Optimizer
*   **Rockbox Standardizer:** Resizes and optimizes covers to 500x500 Baseline JPEG for maximum compatibility with Rockbox and PictureFlow.
*   **Automated Search:** Fetches missing high-quality covers from iTunes and Deezer APIs.
*   **BMP Generation:** Automatically creates the `cover.bmp` files required by many Rockbox themes.
*   **Singles Mode:** Individually search and embed art for tracks that aren't part of a specific album.

---

## 🛠️ Requirements

The application requires **Python 3.10+** and the following dependencies:

*   `customtkinter`: Modern UI components.
*   `pandas`: Heavy-duty data processing and log analysis.
*   `mutagen`: Reading and writing audio metadata (MP3, M4A, FLAC).
*   `Pillow (PIL)`: Image processing and resizing.
*   `matplotlib`: Rendering statistics charts.
*   `requests`: API connections for Last.fm and cover art search.

---

## 📥 Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/iPod-Rockbox-Data-Wizard.git
    cd iPod-Rockbox-Data-Wizard
    ```

2.  **Install dependencies:**
    ```bash
    pip install customtkinter pandas mutagen Pillow matplotlib requests
    ```

3.  **Run the application:**
    ```bash
    python main.py
    ```

---

## 📖 How to Use

1.  **Enable Logging:** On your iPod, ensure Rockbox is recording your activity:
    *   *Settings -> Playback Settings -> Loggin -> Yes*
2.  **Listen to your music:** Play your favorite music so you can start creating logs to feed the app.
3.  **Select Drive:** Connect your iPod and select its root directory in the app.
4.  **Analyze:** The tool will automatically parse the `playback.log` and build a local metadata cache for high performance.
5.  **Manage:** Use the tabs to generate playlists, scrobble to Last.fm, or fix your album covers.

---

## 🎨 UI Customization
You can customize the application's appearance in the **Settings** tab. Change the HEX color codes for accents, backgrounds, and text to match your personal style or your iPod's theme.

---

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing
Contributions are welcome! If you have ideas for new smart playlists or statistical charts, feel free to open an issue or submit a pull request.

---
*Developed for the Rockbox community.* 🎸
