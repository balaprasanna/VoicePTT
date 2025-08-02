# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Virtual Environment Setup
```bash
# Create virtual environment (if not exists)
python3 -m venv whisper_env

# Activate virtual environment
source whisper_env/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Running the Application
```bash
# Quick launch via command script
./ptt.command

# Or manually run
source whisper_env/bin/activate
python run_ptt.py

# Background launch (detached from terminal)
nohup python run_ptt.py > /dev/null 2>&1 &
```

### Permission Setup
On macOS, the application requires:
- **Microphone access** - Required for voice recording
- **Accessibility access** - Required for global hotkey detection

## Architecture Overview

### Core Application Structure
- **Main App Class**: `EnhancedVoicePTTApp` - Inherits from `rumps.App` for macOS menu bar integration
- **Threading Model**: Uses background threads for model loading and audio transcription to keep UI responsive
- **State Management**: Manages recording state, audio buffers, and transcription history in memory
- **Settings Persistence**: JSON file (`voiceptt_settings.json`) stores user preferences

### Key Components

#### Audio Pipeline
1. **Recording**: `sounddevice` captures audio from selected input device at 16kHz mono
2. **Buffering**: Audio data collected in `audio_buffer` list during recording
3. **Processing**: Temporary WAV file created for Whisper model input
4. **Transcription**: OpenAI Whisper model processes audio offline

#### Menu System
- **Dynamic Menu Generation**: Menu items are rebuilt completely for updates (settings, history)
- **Nested Submenus**: Settings organized in hierarchical structure
- **Real-time Updates**: Status and history reflect current app state

#### Hotkey System
- **Global Listener**: `pynput.keyboard` monitors system-wide key events
- **Push-to-Talk Logic**: Recording starts on key press, stops on release
- **Configurable Keys**: Supports Cmd/Alt/Ctrl + Left/Right variants

### File Structure
- `run_ptt.py` - Main application with all functionality
- `ptt.command` - Bash launcher script
- `voiceptt_settings.json` - User settings (auto-created)
- `voiceptt.log` - General application logs
- `voiceptt_transcriptions.txt` - Clean transcription history
- `whisper_env/` - Python virtual environment
- `archive/` - Old/experimental scripts

### Critical Dependencies
- `rumps` - macOS menu bar app framework
- `openai-whisper` - AI transcription engine (offline)
- `sounddevice` - Audio recording interface
- `pynput` - Global hotkey detection
- `pyperclip` - Clipboard management

### Key Behaviors
- **Model Loading**: Whisper models loaded asynchronously on startup/change
- **History Management**: Last 10 transcriptions kept in memory, all saved to file
- **Error Handling**: Audio/transcription errors trigger sound alerts and status updates
- **Output Modes**: Copy to clipboard or auto-paste via System Events
- **Logging Strategy**: Dual logging - general app events + clean transcription file

## Development Notes

### Modifying Audio Settings
Audio device changes take effect immediately. Device list is populated from `sounddevice.query_devices()` filtering for input-capable devices.

### Menu Refresh Pattern
Due to rumps limitations, menu updates require complete menu reconstruction via `menu.clear()` and `setup_menu()`.

### Threading Considerations
- Model loading and transcription run in daemon threads
- Audio recording uses callback-based streaming
- UI updates must happen on main thread

### Platform-Specific Code
- Uses `osascript` for notifications and auto-paste functionality
- Relies on macOS sound files for audio feedback
- Requires macOS accessibility permissions for global hotkeys