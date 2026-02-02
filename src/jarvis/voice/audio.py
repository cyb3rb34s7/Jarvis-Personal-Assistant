"""JARVIS - Audio I/O and hotkey handling."""

import threading
from typing import Callable, Optional

from pynput import keyboard


class HotkeyListener:
    """Listen for hotkey to trigger voice input."""

    def __init__(self, hotkey: str = "<ctrl>+<space>", on_press: Optional[Callable] = None, on_release: Optional[Callable] = None):
        """Initialize hotkey listener.

        Args:
            hotkey: Hotkey combination (default Ctrl+Space)
            on_press: Callback when hotkey is pressed
            on_release: Callback when hotkey is released
        """
        self.hotkey = hotkey
        self.on_press = on_press
        self.on_release = on_release
        self._listener: Optional[keyboard.GlobalHotKeys] = None
        self._is_pressed = False
        self._keyboard_listener: Optional[keyboard.Listener] = None

    def _handle_press(self):
        """Handle hotkey press."""
        if not self._is_pressed:
            self._is_pressed = True
            if self.on_press:
                self.on_press()

    def _handle_release(self, key):
        """Handle key release to detect hotkey release."""
        # Check if it's the space key being released
        if self._is_pressed:
            try:
                if key == keyboard.Key.space:
                    self._is_pressed = False
                    if self.on_release:
                        self.on_release()
            except AttributeError:
                pass

    def start(self):
        """Start listening for hotkey."""
        # Use GlobalHotKeys for press detection
        self._listener = keyboard.GlobalHotKeys({
            self.hotkey: self._handle_press
        })
        self._listener.start()

        # Use regular listener for release detection
        self._keyboard_listener = keyboard.Listener(on_release=self._handle_release)
        self._keyboard_listener.start()

    def stop(self):
        """Stop listening."""
        if self._listener:
            self._listener.stop()
            self._listener = None
        if self._keyboard_listener:
            self._keyboard_listener.stop()
            self._keyboard_listener = None


class PushToTalk:
    """Push-to-talk voice input handler."""

    def __init__(self, on_speech: Callable[[str], None], hotkey: str = "<ctrl>+<space>"):
        """Initialize push-to-talk.

        Args:
            on_speech: Callback with transcribed text
            hotkey: Hotkey combination
        """
        self.on_speech = on_speech
        self.hotkey = hotkey
        self._hotkey_listener: Optional[HotkeyListener] = None
        self._is_recording = False
        self._stop_event = threading.Event()

    def _on_hotkey_press(self):
        """Handle hotkey press - start recording."""
        if not self._is_recording:
            self._is_recording = True
            self._stop_event.clear()
            print("\n[*] Listening... (release Ctrl+Space to stop)")

            # Start recording in background thread
            threading.Thread(target=self._record_and_transcribe, daemon=True).start()

    def _on_hotkey_release(self):
        """Handle hotkey release - stop recording."""
        if self._is_recording:
            self._stop_event.set()

    def _record_and_transcribe(self):
        """Record audio and transcribe."""
        from .stt import get_recognizer

        try:
            recognizer = get_recognizer()
            text = recognizer.listen_once(timeout=30.0, silence_timeout=1.5)

            if text:
                print(f"[>] You said: {text}")
                self.on_speech(text)
            else:
                print("[!] No speech detected")

        except Exception as e:
            print(f"[!] Error: {e}")
        finally:
            self._is_recording = False

    def start(self):
        """Start push-to-talk listener."""
        self._hotkey_listener = HotkeyListener(
            hotkey=self.hotkey,
            on_press=self._on_hotkey_press,
            on_release=self._on_hotkey_release
        )
        self._hotkey_listener.start()
        print(f"[Mic] Voice mode active. Press {self.hotkey.replace('<', '').replace('>', '')} to speak.")

    def stop(self):
        """Stop push-to-talk listener."""
        if self._hotkey_listener:
            self._hotkey_listener.stop()
            self._hotkey_listener = None
