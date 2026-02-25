<div align="center">
  <img src="lain_computer.png" width="400" alt="CABLE Hero Art">
  <h1>CABLE // Intelligent Folder Organizer</h1>
  
  <p><i>"Meow Meow Meow?"</i></p>

  <a href="https://www.python.org/">
    <img src="https://img.shields.io/badge/python-3.10%2B-blueviolet?style=for-the-badge&logo=python&logoColor=white" alt="Python Version">
  </a>
  <a href="https://opensource.org/licenses/MIT">
    <img src="https://img.shields.io/badge/license-MIT-green?style=for-the-badge" alt="License">
  </a>
  <img src="https://img.shields.io/badge/OS-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey?style=for-the-badge" alt="OS Support">

  <p><b>Automatically sort any directory into clean, categorized subfolders — once or continuously in the background.</b></p>
</div>

---

## ⚡ Features

- **Dual Modes**: Choose between a one-time **Sort Once** or a persistent **Watcher Daemon**.
- **Categorization**: Group files by type (Images, Video, Code, etc.) with customizable icons and colors.
- **Library Integration**: Automatically route files to your OS library folders (Pictures, Videos, Documents).
- **Date Subfolders**: Organize media into `YYYY/MM` structures automatically.
- **Undo System**: Regret a sort? Restore your files to their original state with one command.
- **Full Customization**: Every folder name, extension, and color is defined in a human-readable `cable.json`.

---

## 🚀 Quick Start

1. **Install Python, you dummy!**
   
2. **Install Dependencies**:
   ```bash
   pip install rich watchdog pystray Pillow tomli
   ```

3. **Run CABLE**:
   ```bash
   python cable.py
   ```

4. **Choose Your Source**:
   A native folder picker will appear. Select the directory you want to clean up.

5. **Follow the Prompts**:
   Pick your sorting mode, destination, and options. CABLE handles the rest.

6. **Guide**:
   If this .md is not enough check Cable.html, which is a better version of this. Hehe...

---

## ⚙️ Configuration

On first run, CABLE generates a `cable.json` file in the same directory. You can edit this to completely redefine how the system behaves.

```jsonc
{
  "categories": [
    {
      "key": "🖼️  Images",
      "folder": "Media/Images",
      "extensions": [".jpg", ".png", ".webp"]
    }
    // ... add your own!
  ]
}
```

---

## 🛠️ Requirements

- **Python 3.10+**
- **Rich**: For the beautiful terminal UI.
- **Watchdog**: For background file monitoring.
- **Pystray/Pillow**: For the system tray icon in watcher mode.

---

<div align="center">
  <img src="lain_smile.png" width="120" alt="Why is this blue? :3">
  <p><small><i>I love Cables so much...</i></small></p>
</div>
