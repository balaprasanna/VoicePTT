import rumps
import whisper
import sounddevice as sd
import numpy as np
import pyperclip
import tempfile
import wave
import os
import subprocess
import threading
import time
from pynput import keyboard
from datetime import datetime
import json
import logging

SAMPLE_RATE = 16000
CHANNELS = 1
os.environ["PATH"] += os.pathsep + "/opt/homebrew/bin"



class EnhancedVoicePTTApp(rumps.App):
    # ================================
    # INITIALIZATION & CORE SETUP
    # ================================
    
    def __init__(self):
        super(EnhancedVoicePTTApp, self).__init__("🎙️", quit_button=None)
        
        # Setup logging
        self.setup_logging()
        
        # Initialize settings
        self.settings = self.load_settings()
        self.mode = self.settings.get("mode", "copy")
        self.hotkey = self.settings.get("hotkey", "cmd_r")
        self.model_size = self.settings.get("model_size", "small")
        self.audio_device = self.settings.get("audio_device", 1)
        
        # State management
        self.model = None
        self.is_recording = False
        self.recording_start_time = 0
        self.audio_buffer = []
        self.stream = None
        self.lock = threading.Lock()
        self.transcription_history = []
        
        # Load transcription history from log file
        self.load_transcription_history()
        
        # Setup components
        self.setup_menu()
        self.setup_keyboard_listener()
        
        # Load model in background
        threading.Thread(target=self.load_model, daemon=True).start()

    def setup_logging(self):
        """Setup simple logging for general app logs"""
        logging.basicConfig(
            filename='voiceptt.log',
            level=logging.INFO,
            format='%(asctime)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        self.logger = logging.getLogger(__name__)
        
        self.logger.info("VoicePTT app starting up")
    
    def save_transcription(self, text):
        """Save transcription to dedicated clean file"""
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            with open('voiceptt_transcriptions.txt', 'a', encoding='utf-8') as f:
                f.write(f"{timestamp} | {text}\n")
        except Exception as e:
            self.logger.error(f"Failed to save transcription: {e}")

    def load_transcription_history(self):
        """Load recent transcriptions from dedicated transcription file"""
        try:
            if os.path.exists('voiceptt_transcriptions.txt'):
                with open('voiceptt_transcriptions.txt', 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    # Get last 10 transcriptions
                    for line in lines[-10:]:
                        line = line.strip()
                        if not line:
                            continue
                        if '|' in line:
                            parts = line.split(' | ', 1)
                            if len(parts) == 2:
                                timestamp_str, text = parts
                                try:
                                    # Parse timestamp
                                    timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                                    self.transcription_history.append({
                                        "text": text,
                                        "timestamp": timestamp.strftime("%H:%M:%S"),
                                        "date": timestamp.isoformat()
                                    })
                                except ValueError:
                                    continue
                self.logger.info(f"Loaded {len(self.transcription_history)} transcriptions from history")
        except Exception as e:
            self.logger.error(f"Error loading transcription history: {e}")

    def load_model(self):
        """Load the Whisper AI model in background"""
        try:
            self.logger.info(f"Loading Whisper model: {self.model_size}")
            self.update_status("Loading AI model...")
            self.model = whisper.load_model(self.model_size)
            self.update_status(f"Ready • Hold {self.hotkey.replace('_', '+').upper()} to speak")
            self.logger.info(f"Model {self.model_size} loaded successfully")
        except Exception as e:
            self.logger.error(f"Error loading model: {str(e)}")
            self.update_status(f"Error loading model: {str(e)}")

    # ================================
    # SETTINGS MANAGEMENT
    # ================================
    
    def load_settings(self):
        """Load settings from JSON file"""
        try:
            with open("voiceptt_settings.json", "r") as f:
                return json.load(f)
        except:
            return {}
    
    def save_settings(self):
        """Save current settings to JSON file"""
        settings = {
            "mode": self.mode,
            "hotkey": self.hotkey,
            "model_size": self.model_size,
            "audio_device": self.audio_device
        }
        with open("voiceptt_settings.json", "w") as f:
            json.dump(settings, f, indent=2)

    def change_model(self, size):
        """Change Whisper model size"""
        if size != self.model_size:
            self.logger.info(f"Changing model from {self.model_size} to {size}")
            self.model_size = size
            self.save_settings()
            self.update_status(f"Loading {size} model...")
            threading.Thread(target=self.load_model, daemon=True).start()
            self.refresh_settings_menu()

    def change_audio_device(self, device_id):
        """Change audio input device"""
        self.audio_device = device_id
        self.save_settings()
        device_name = sd.query_devices()[device_id]['name']
        subprocess.run(["osascript", "-e", 
                      f'display notification "Audio device: {device_name}" with title "VoicePTT"'])
        self.refresh_settings_menu()

    def change_hotkey(self, key):
        """Change push-to-talk hotkey"""
        self.hotkey = key
        self.save_settings()
        if hasattr(self, 'keyboard_listener'):
            self.keyboard_listener.stop()
        self.setup_keyboard_listener()
        display_key = key.replace("_", "+").upper()
        self.update_status(f"Ready • Hold {display_key} to speak")
        subprocess.run(["osascript", "-e", 
                      f'display notification "Hotkey: {display_key}" with title "VoicePTT"'])
        self.refresh_settings_menu()

    # ================================
    # MENU MANAGEMENT
    # ================================
    
    def setup_menu(self):
        """Create the main application menu"""
        # Create settings menu with preferences as submenu
        settings_menu = rumps.MenuItem("⚙️ Settings")
        settings_menu.add(self.create_settings_submenu())
        
        self.menu = [
            rumps.MenuItem("📊 Status: Ready", callback=None),
            rumps.separator,
            # rumps.MenuItem("🎯 Push-to-Talk Mode", callback=self.toggle_ptt_mode),
            rumps.MenuItem(f"📋 Output: {self.mode.upper()}", callback=self.toggle_output_mode),
            rumps.separator,
            rumps.MenuItem("📝 Recent Transcriptions", callback=None),
            self.create_history_submenu(),
            rumps.separator,
            settings_menu,
            rumps.separator,
            rumps.MenuItem("ℹ️ Help & Info", callback=self.show_help),            
            rumps.MenuItem("❌ Quit", callback=self.quit_app)
        ]
        
    def create_history_submenu(self):
        """Create transcription history submenu"""
        submenu = rumps.MenuItem("📄 View History")
        
        if not self.transcription_history:
            submenu.add(rumps.MenuItem("(No transcriptions yet)", callback=None))
        else:
            # Add recent transcriptions
            for i, entry in enumerate(self.transcription_history[-5:]):  # Last 5
                timestamp = entry['timestamp']
                text_preview = entry['text'][:50] + "..." if len(entry['text']) > 50 else entry['text']
                item = rumps.MenuItem(f"{timestamp}: {text_preview}", callback=lambda sender, idx=i: self.copy_from_history(idx))
                submenu.add(item)
            
            # Add separator and clear option
            submenu.add(rumps.separator)
            submenu.add(rumps.MenuItem("🗑️ Clear History", callback=self.clear_history))
        
        return submenu
    
    def create_settings_submenu(self):
        """Create settings/preferences submenu"""
        submenu = rumps.MenuItem("🔧 Preferences")
        
        # Model size submenu
        model_submenu = rumps.MenuItem("🤖 Whisper Model")
        for size in ["tiny", "base", "small", "medium", "large"]:
            checked = "✓ " if size == self.model_size else ""
            item = rumps.MenuItem(f"{checked}{size.title()}", callback=lambda sender, s=size: self.change_model(s))
            model_submenu.add(item)
        submenu.add(model_submenu)
        
        # Audio device submenu
        audio_submenu = rumps.MenuItem("🎤 Audio Device")
        try:
            devices = sd.query_devices()
            for i, device in enumerate(devices):
                if device['max_input_channels'] > 0:  # Input devices only
                    checked = "✓ " if i == self.audio_device else ""
                    name = device['name'][:30] + "..." if len(device['name']) > 30 else device['name']
                    item = rumps.MenuItem(f"{checked}{name}", callback=lambda sender, idx=i: self.change_audio_device(idx))
                    audio_submenu.add(item)
        except:
            audio_submenu.add(rumps.MenuItem("Error loading devices", callback=None))
        submenu.add(audio_submenu)
        
        # Hotkey submenu
        hotkey_submenu = rumps.MenuItem("⌨️ Hotkey")
        for key in ["cmd_r", "cmd_l", "alt_r", "alt_l", "ctrl_r", "ctrl_l"]:
            checked = "✓ " if key == self.hotkey else ""
            display_name = key.replace("_", " ").title().replace("Cmd", "⌘").replace("Alt", "⌥").replace("Ctrl", "⌃")
            item = rumps.MenuItem(f"{checked}{display_name}", callback=lambda sender, k=key: self.change_hotkey(k))
            hotkey_submenu.add(item)
        submenu.add(hotkey_submenu)
        
        return submenu
    
    def refresh_settings_menu(self):
        """Force menu refresh by completely rebuilding it"""
        # Store current status
        current_status = "Ready"
        for item in self.menu:
            if "Status:" in str(item.title):
                current_status = str(item.title).replace("📊 Status: ", "")
                break
        
        # Force complete menu refresh
        self.menu.clear()
        self.setup_menu()
        
        # Restore the current status
        self.update_status(current_status)
    
    def refresh_history_menu(self):
        """Force complete menu refresh to update history (same approach as settings)"""
        # Store current status
        current_status = "Ready"
        for item in self.menu:
            if "Status:" in str(item.title):
                current_status = str(item.title).replace("📊 Status: ", "")
                break
        
        # Force complete menu refresh (same as settings refresh)
        self.menu.clear()
        self.setup_menu()
        
        # Restore the current status
        self.update_status(current_status)
    
    def create_history_callback(self, index):
        """Create a callback function for history menu items"""
        def callback(sender):
            self.copy_from_history(index)
        return callback
    
    def update_status(self, status):
        """Update the status message in the menu"""
        for item in self.menu:
            if "Status:" in str(item.title):
                item.title = f"📊 Status: {status}"
                break

    # ================================
    # AUDIO & RECORDING FUNCTIONALITY
    # ================================
    
    def start_recording(self):
        """Start audio recording"""
        if self.is_recording:
            return
            
        self.is_recording = True
        self.audio_buffer = []
        self.title = "🔴"
        self.update_status("Recording... (hold key)")
        
        def callback(indata, frames, time_info, status):
            if self.is_recording:
                with self.lock:
                    self.audio_buffer.append(indata.copy())
        
        try:
            sd.default.device = (self.audio_device, None)
            self.stream = sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=CHANNELS,
                dtype='int16',
                callback=callback
            )
            self.stream.start()
            time.sleep(0.1)  # Brief warm-up
        except Exception as e:
            self.cancel_recording(f"Audio error: {str(e)}")
    
    def stop_recording(self):
        """Stop audio recording and start transcription"""
        if not self.is_recording:
            return
            
        self.is_recording = False
        self.title = "⏳"
        self.update_status("Processing audio...")
        
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        
        threading.Thread(target=self.transcribe_audio, daemon=True).start()
    
    def cancel_recording(self, reason):
        """Cancel recording with error message"""
        self.is_recording = False
        self.title = "🎙️"
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        self.update_status(f"Cancelled: {reason}")
        subprocess.run(["afplay", "/System/Library/Sounds/Sosumi.aiff"])
    
    def transcribe_audio(self):
        """Process recorded audio and convert to text"""
        try:
            if not self.audio_buffer:
                self.cancel_recording("No audio captured")
                return
            
            # Process audio
            audio_data = np.concatenate(self.audio_buffer, axis=0)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
                with wave.open(f.name, 'wb') as wf:
                    wf.setnchannels(CHANNELS)
                    wf.setsampwidth(2)
                    wf.setframerate(SAMPLE_RATE)
                    wf.writeframes(audio_data.tobytes())
                
                # Transcribe
                self.update_status("Transcribing with AI...")
                result = self.model.transcribe(f.name, language="en")
                text = result["text"].strip()
                
                if text:
                    # Log to general log for debugging
                    self.logger.info(f"Transcription successful: {len(text)} characters")
                    
                    # Save transcription to dedicated file
                    self.save_transcription(text)
                    
                    # Store in history
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    history_entry = {
                        "text": text,
                        "timestamp": timestamp,
                        "date": datetime.now().isoformat()
                    }
                    self.transcription_history.append(history_entry)
                    
                    # Keep only last 10 items in memory
                    if len(self.transcription_history) > 10:
                        self.transcription_history = self.transcription_history[-10:]
                    
                    # Update menu to refresh history
                    self.refresh_history_menu()
                    
                    # Output text
                    pyperclip.copy(text)
                    if self.mode == "paste":
                        time.sleep(0.2)  # Brief delay
                        subprocess.run(["osascript", "-e", 
                                      'tell application "System Events" to keystroke "v" using command down'])
                    
                    # Success feedback
                    self.title = "✅"
                    self.update_status(f"✅ Transcribed • {len(text)} chars • {self.mode}")
                    subprocess.run(["afplay", "-v", "0.3", "/System/Library/Sounds/Blow.aiff"])
                    
                    # Show notification with preview
                    preview = text[:50] + "..." if len(text) > 50 else text
                    subprocess.run(["osascript", "-e", 
                                  f'display notification "{preview}" with title "VoicePTT" subtitle "{self.mode.title()}d to clipboard"'])
                    
                    # Reset after delay
                    threading.Timer(3.0, self.reset_to_ready).start()
                else:
                    self.cancel_recording("No speech detected")
                    
        except Exception as e:
            self.logger.error(f"Transcription failed: {str(e)}")
            self.cancel_recording(f"Transcription error: {str(e)}")
    
    def reset_to_ready(self):
        """Reset app to ready state"""
        self.title = "🎙️"
        self.update_status(f"Ready • Hold {self.hotkey.replace('_', '+').upper()} to speak")

    # ================================
    # KEYBOARD HANDLING
    # ================================
    
    def setup_keyboard_listener(self):
        """Setup keyboard listener for push-to-talk functionality"""
        def get_key_from_string(key_str):
            key_map = {
                "cmd_r": keyboard.Key.cmd_r,
                "cmd_l": keyboard.Key.cmd_l, 
                "alt_r": keyboard.Key.alt_r,
                "alt_l": keyboard.Key.alt_l,
                "ctrl_r": keyboard.Key.ctrl_r,
                "ctrl_l": keyboard.Key.ctrl_l
            }
            return key_map.get(key_str, keyboard.Key.cmd_r)
        
        def on_press(key):
            target_key = get_key_from_string(self.hotkey)
            if key == target_key and not self.is_recording and self.model:
                self.recording_start_time = time.time()
                self.start_recording()
        
        def on_release(key):
            target_key = get_key_from_string(self.hotkey)
            if key == target_key and self.is_recording:
                if time.time() - self.recording_start_time >= 0.1:
                    self.stop_recording()
                else:
                    self.cancel_recording("Key press too short")
        
        self.keyboard_listener = keyboard.Listener(on_press=on_press, on_release=on_release)
        self.keyboard_listener.start()

    # ================================
    # UI ACTIONS & CALLBACKS
    # ================================
    
    # def toggle_ptt_mode(self, sender):
    #     """Show push-to-talk info"""
    #     rumps.alert("Push-to-talk is always active!", 
    #                "Hold your configured hotkey to record, release to transcribe.", 
    #                ok="Got it!")
    
    def toggle_output_mode(self, sender):
        """Toggle between copy and paste output modes"""
        self.mode = "paste" if self.mode == "copy" else "copy"
        sender.title = f"📋 Output: {self.mode.upper()}"
        self.save_settings()
        subprocess.run(["osascript", "-e", 
                      f'display notification "Output mode: {self.mode.upper()}" with title "VoicePTT"'])
    
    def copy_from_history(self, index):
        """Copy text from transcription history"""
        try:
            # Get the last 5 items and use the provided index
            recent_items = self.transcription_history[-5:]
            if 0 <= index < len(recent_items):
                text = recent_items[index]["text"]
                pyperclip.copy(text)
                subprocess.run(["osascript", "-e", 
                              'display notification "Copied from history!" with title "VoicePTT"'])
        except (IndexError, KeyError):
            subprocess.run(["osascript", "-e", 
                          'display notification "Error copying from history" with title "VoicePTT"'])
    
    def clear_history(self, sender):
        """Clear all transcription history with confirmation"""
        # Show confirmation dialog
        response = rumps.alert(
            "Clear Transcription History",
            "Are you sure you want to clear all transcription history?\n\nThis will:\n• Remove all items from the menu\n• Clear the transcription file\n\nThis action cannot be undone.",
            ok="Clear History",
            cancel="Cancel"
        )
        
        if response == 1:  # User clicked "Clear History"
            try:
                # Clear in-memory history
                self.transcription_history.clear()
                self.logger.info("Cleared in-memory transcription history")
                
                # Clear the transcription file
                with open('voiceptt_transcriptions.txt', 'w', encoding='utf-8') as f:
                    f.write("")  # Empty the file
                self.logger.info("Cleared transcription file")
                
                # Refresh menu to show empty state
                self.refresh_history_menu()
                
                # Show success notification
                subprocess.run(["osascript", "-e", 
                              'display notification "Transcription history cleared!" with title "VoicePTT"'])
                
            except Exception as e:
                self.logger.error(f"Error clearing history: {e}")
                subprocess.run(["osascript", "-e", 
                              'display notification "Error clearing history!" with title "VoicePTT"'])
    
    def show_help(self, sender):
        """Show help dialog"""
        help_text = f"""🎙️ VoicePTT - Voice to Text

🔥 QUICK START:
• Hold {self.hotkey.replace('_', '+').upper()} key to record
• Release to transcribe
• Text goes to clipboard (or auto-pastes)

⚙️ FEATURES:
• Push-to-talk recording
• AI transcription (Whisper)
• Copy or auto-paste modes  
• Transcription history
• Customizable hotkeys
• Multiple audio devices
• Various AI model sizes

🎯 CURRENT SETTINGS:
• Hotkey: {self.hotkey.replace('_', '+').upper()}
• Output: {self.mode.upper()}
• Model: {self.model_size.title()}
• Device: {sd.query_devices()[self.audio_device]['name'][:30]}

💡 TIP: Use Settings menu to customize everything!"""
        
        rumps.alert("Voice PTT Help", help_text, ok="Close")
        
    def quit_app(self, sender):
        """Quit the application"""
        if hasattr(self, 'keyboard_listener'):
            self.keyboard_listener.stop()
        rumps.quit_application()

if __name__ == "__main__":
    EnhancedVoicePTTApp().run()