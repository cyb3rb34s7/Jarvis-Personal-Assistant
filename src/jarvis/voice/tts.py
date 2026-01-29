"""JARVIS - Text to Speech using Kokoro."""

import sounddevice as sd
import numpy as np
from pathlib import Path
from typing import Optional
from kokoro_onnx import Kokoro

# Model paths (from kokoro-onnx GitHub releases)
MODELS_DIR = Path(__file__).parent.parent.parent.parent / "models" / "kokoro"
MODEL_PATH = MODELS_DIR / "kokoro-v1.0.onnx"
VOICES_PATH = MODELS_DIR / "voices-v1.0.bin"

# Default voice settings
DEFAULT_VOICE = "af_heart"  # American female, warm voice
DEFAULT_SPEED = 1.0
SAMPLE_RATE = 24000


class TextToSpeech:
    """Kokoro-based text to speech."""

    def __init__(self, voice: str = DEFAULT_VOICE, speed: float = DEFAULT_SPEED):
        """Initialize TTS.

        Args:
            voice: Voice ID to use (e.g., 'af_heart', 'af_bella', 'am_adam')
            speed: Speech speed (1.0 = normal)
        """
        self.voice = voice
        self.speed = speed
        self._kokoro: Optional[Kokoro] = None

    def _ensure_loaded(self):
        """Lazy load the Kokoro model."""
        if self._kokoro is None:
            if not MODEL_PATH.exists():
                raise FileNotFoundError(
                    f"Kokoro model not found at {MODEL_PATH}. "
                    "Download from: https://github.com/thewh1teagle/kokoro-onnx/releases"
                )

            if not VOICES_PATH.exists():
                raise FileNotFoundError(
                    f"Voices file not found at {VOICES_PATH}. "
                    "Download from: https://github.com/thewh1teagle/kokoro-onnx/releases"
                )

            print("Loading Kokoro TTS model...")
            self._kokoro = Kokoro(str(MODEL_PATH), str(VOICES_PATH))
            print("TTS model loaded!")

    def speak(self, text: str, block: bool = True) -> None:
        """Speak the given text.

        Args:
            text: Text to speak
            block: If True, wait for speech to finish
        """
        if not text.strip():
            return

        self._ensure_loaded()

        try:
            # Split long text into sentences to avoid phoneme limit
            import re
            sentences = re.split(r'(?<=[.!?])\s+', text)

            for sentence in sentences:
                if not sentence.strip():
                    continue

                # Truncate very long sentences (Kokoro limit ~500 chars)
                if len(sentence) > 400:
                    sentence = sentence[:400] + "..."

                # Generate audio
                audio, sample_rate = self._kokoro.create(
                    sentence,
                    voice=self.voice,
                    speed=self.speed
                )

                # Play audio
                sd.play(audio, sample_rate)
                if block:
                    sd.wait()

        except Exception as e:
            print(f"TTS Error: {e}")
            # Fallback: just print the text
            print(f"[Could not speak: {text[:100]}...]")

    def speak_streamed(self, text: str) -> None:
        """Speak text with sentence-level streaming for lower latency.

        Args:
            text: Text to speak (can contain multiple sentences)
        """
        if not text.strip():
            return

        self._ensure_loaded()

        # Split into sentences for streaming
        import re
        sentences = re.split(r'(?<=[.!?])\s+', text)

        for sentence in sentences:
            if sentence.strip():
                self.speak(sentence.strip(), block=True)

    def stop(self) -> None:
        """Stop any ongoing speech."""
        sd.stop()


# Global instance
_tts: Optional[TextToSpeech] = None


def get_tts() -> TextToSpeech:
    """Get or create the global TTS instance."""
    global _tts
    if _tts is None:
        _tts = TextToSpeech()
    return _tts


def speak(text: str, block: bool = True) -> None:
    """Convenience function to speak text.

    Args:
        text: Text to speak
        block: If True, wait for speech to finish
    """
    get_tts().speak(text, block=block)
