# 🎙️ VoicePTT - Voice Push-to-Talk Transcription

A macOS menu bar application that converts speech to text using AI transcription. Hold a hotkey to record, release to transcribe, and get your text instantly copied to clipboard or auto-pasted.

![VoicePTT Demo](https://img.shields.io/badge/macOS-Compatible-brightgreen) ![Python](https://img.shields.io/badge/Python-3.8+-blue) ![License](https://img.shields.io/badge/License-MIT-yellow)

## ✨ Features

- **🎯 Push-to-Talk Recording** - Hold configurable hotkey (⌘R, ⌘L, ⌥R, etc.)
- **🤖 AI Transcription** - Powered by OpenAI Whisper (offline)
- **📋 Smart Output** - Copy to clipboard or auto-paste mode
- **📝 Transcription History** - View and copy from recent transcriptions
- **⚙️ Customizable Settings** - Change model size, audio device, hotkeys
- **🔄 Real-time Updates** - Menu updates instantly with new transcriptions
- **🗂️ Dual Logging** - General app logs + clean transcription file
- **🧹 History Management** - Clear history with confirmation dialog

## 🖥️ Requirements

- **macOS** (tested on macOS 13+)
- **Python 3.8 or later**
- **Microphone access** (will prompt for permissions)
- **Accessibility permissions** (for global hotkeys)

## 🚀 Installation

### 1. Clone or Download
```bash
git clone <repository-url>
cd macapps
```

### 2. Create Virtual Environment
```bash
python3 -m venv whisper_env
source whisper_env/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Set Executable Permissions
```bash
chmod +x ptt.command
```

### 5. First Launch
Double-click `ptt.command` to start the app. 

**Note:** On first launch, macOS will prompt for:
- **Microphone access** - Required for voice recording
- **Accessibility access** - Required for global hotkey detection

### 6. Create Desktop App (Optional)
For easier access, create a native-looking app icon:

#### Option A: Automator App (Recommended)
1. Open **Automator** (Applications → Automator)
2. Choose **Application** template
3. Search for "**Run Shell Script**" and drag it to workflow
4. Set Shell to: `/bin/bash`
5. Paste this script (update path to your project location):
   ```bash
   cd /path/to/your/macapps
   source whisper_env/bin/activate
   nohup python run_ptt.py > /dev/null 2>&1 &
   ```
   **Replace `/path/to/your/macapps` with your actual project path**
   
   *Tip: To find your project path, open Terminal, navigate to your project folder, and run `pwd`*
6. **File** → **Save** as "VoicePTT" to Desktop/Applications
7. Right-click saved app → **Get Info** → drag a custom icon to the icon area (optional)

#### Option B: Desktop Alias
1. Right-click `ptt.command` → **Make Alias**
2. Drag alias to Desktop
3. Rename to "VoicePTT"
4. Right-click → **Get Info** → change icon (optional)

Now you can launch VoicePTT by double-clicking the desktop icon!

## 🎮 Usage

### Starting the App
**Method 1:** Double-click `ptt.command` in the project folder
**Method 2:** Double-click your desktop shortcut/app (if created)

1. Launch using either method above
2. Look for 🎙️ icon in your menu bar
3. Wait for "Ready" status (Whisper model loading)

### Recording & Transcription
1. **Hold** your configured hotkey (default: Right ⌘)
2. **Speak** your message
3. **Release** the key to stop recording
4. Text automatically **copied to clipboard** (or auto-pasted)

### Menu Navigation
- **Status** - Shows current app state
- **Output** - Toggle between COPY/PASTE modes
- **Recent Transcriptions** → **View History** - See recent transcriptions
- **Settings** → **Preferences** - Customize everything
- **Help & Info** - Quick reference guide

## ⚙️ Configuration

### Hotkey Options
- **⌘ R** (Right Command) - Default
- **⌘ L** (Left Command)
- **⌥ R** (Right Option/Alt)
- **⌥ L** (Left Option/Alt)
- **⌃ R** (Right Control)
- **⌃ L** (Left Control)

### Whisper Models
- **Tiny** - Fastest, less accurate (~39 MB)
- **Base** - Good balance (~74 MB)
- **Small** - Better accuracy (~244 MB) - **Default**
- **Medium** - High accuracy (~769 MB)
- **Large** - Best accuracy (~1550 MB)

### Output Modes
- **COPY** - Text copied to clipboard (default)
- **PASTE** - Text automatically pasted where cursor is

## 📁 File Structure

```
macapps/
├── run_ptt.py                    # Main application
├── ptt.command                   # Launch script (double-click this)
├── requirements.txt              # Python dependencies
├── voiceptt_settings.json        # App settings (auto-created)
├── voiceptt.log                  # General app logs
├── voiceptt_transcriptions.txt   # Clean transcription history
├── whisper_env/                  # Python virtual environment
└── archive/                      # Archived files
```

## 🔧 Troubleshooting

### App Won't Start
1. **Check permissions**: System Preferences → Privacy & Security
   - Microphone: Enable for Terminal/Python
   - Accessibility: Enable for Terminal/Python
2. **Verify Python**: `python3 --version` should be 3.8+
3. **Check virtual environment**: Ensure `whisper_env` exists and has packages

### Hotkey Not Working
1. **Check Accessibility permissions** (most common issue)
2. **Try different hotkey** in Settings → Preferences → Hotkey
3. **Restart the app** after permission changes

### Poor Transcription Quality
1. **Use larger model**: Settings → Preferences → Whisper Model
2. **Check microphone**: Try speaking closer/louder
3. **Test audio device**: Settings → Preferences → Audio Device
4. **Check for background noise**

### App Performance Issues
1. **Use smaller model** if experiencing slowness
2. **Check available disk space** (models need storage)
3. **Close other intensive applications**

## 🗂️ Logs & History

### View Logs
- **General logs**: `voiceptt.log` (app events, errors, debug info)
- **Transcriptions**: `voiceptt_transcriptions.txt` (clean text only)

### Clear History
- Menu: Recent Transcriptions → View History → 🗑️ Clear History
- Requires confirmation, clears both memory and file

## 🔄 Updates & Maintenance

### Update Whisper
```bash
source whisper_env/bin/activate
pip install --upgrade openai-whisper
```

### Reset Settings
Delete `voiceptt_settings.json` to restore defaults.

### Clean Logs
```bash
rm voiceptt.log voiceptt_transcriptions.txt
```

## 🛡️ Privacy & Security

- **100% Offline** - No internet required after setup
- **Local Processing** - All transcription happens on your Mac
- **No Data Sharing** - Your voice never leaves your device
- **Secure Storage** - Settings and history stored locally only

## 📋 Dependencies

Key packages installed via `requirements.txt`:
- `openai-whisper` - AI transcription engine
- `rumps` - macOS menu bar framework
- `sounddevice` - Audio recording
- `pyperclip` - Clipboard management
- `pynput` - Global hotkey detection
- `numpy` - Audio processing

## 🤝 Contributing

Found a bug or want to add features? 
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- [OpenAI Whisper](https://github.com/openai/whisper) - Amazing speech recognition
- [rumps](https://github.com/jaredks/rumps) - Simple macOS menu bar apps
- The Python community for excellent libraries

---

**Made with ❤️ for productivity enthusiasts**

*Turn your voice into text with just a keystroke!*