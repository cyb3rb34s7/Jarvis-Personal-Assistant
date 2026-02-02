"""JARVIS - Speech to Text using faster-whisper."""

import os
import queue
import sys
import numpy as np
from pathlib import Path
from typing import Optional, Callable

# Add CUDA libraries from pip packages to PATH (needed for Windows)
def _setup_cuda_path():
    """Add pip-installed CUDA libraries to PATH."""
    site_packages = Path(__file__).parent.parent.parent.parent / ".venv" / "Lib" / "site-packages"
    cuda_paths = [
        site_packages / "nvidia" / "cublas" / "bin",
        site_packages / "nvidia" / "cudnn" / "bin",
        site_packages / "nvidia" / "cuda_runtime" / "bin",
    ]
    for cuda_path in cuda_paths:
        if cuda_path.exists():
            os.environ["PATH"] = str(cuda_path) + os.pathsep + os.environ.get("PATH", "")

_setup_cuda_path()

import sounddevice as sd
from faster_whisper import WhisperModel


class SpeechRecognizer:
    """Whisper-based speech recognizer optimized for Hinglish."""

    def __init__(
        self,
        model_size: str = "large-v3-turbo",
        device: str = "cuda",
        compute_type: str = "float16",
        language: str = "hi",  # Hindi - works better for Hinglish
        sample_rate: int = 16000
    ):
        """Initialize the speech recognizer.

        Args:
            model_size: Whisper model size (large-v3-turbo recommended for Hinglish)
            device: Device to use (cuda or cpu)
            compute_type: Compute type (float16 for GPU, int8 for CPU)
            language: Language code (hi for Hindi/Hinglish)
            sample_rate: Audio sample rate
        """
        self.sample_rate = sample_rate
        self.language = language
        self.audio_queue: queue.Queue = queue.Queue()
        self._is_listening = False

        print(f"Loading Whisper {model_size} model on {device}...")
        self.model = WhisperModel(
            model_size,
            device=device,
            compute_type=compute_type
        )
        print("Model loaded!")

    def _audio_callback(self, indata, frames, time, status):
        """Callback for audio stream."""
        if status:
            print(f"Audio status: {status}", file=sys.stderr)
        self.audio_queue.put(indata.copy())

    def listen_once(self, timeout: float = 10.0, silence_timeout: float = 2.0) -> str:
        """Listen for speech and return transcription.

        Args:
            timeout: Maximum time to listen (seconds)
            silence_timeout: Stop after this much silence (seconds)

        Returns:
            Transcribed text
        """
        audio_chunks = []

        with sd.InputStream(
            samplerate=self.sample_rate,
            blocksize=int(self.sample_rate * 0.1),  # 100ms blocks
            dtype="float32",
            channels=1,
            callback=self._audio_callback
        ):
            import time
            start_time = time.time()
            last_audio_time = start_time
            got_audio = False

            # Simple energy-based voice activity detection
            silence_threshold = 0.01

            while True:
                elapsed = time.time() - start_time
                if elapsed > timeout:
                    break

                try:
                    data = self.audio_queue.get(timeout=0.1)
                    audio_chunks.append(data)

                    # Check if there's audio activity
                    energy = np.sqrt(np.mean(data ** 2))
                    if energy > silence_threshold:
                        got_audio = True
                        last_audio_time = time.time()

                except queue.Empty:
                    continue

                # Check for silence timeout after getting some audio
                if got_audio and (time.time() - last_audio_time) > silence_timeout:
                    break

        if not audio_chunks:
            return ""

        # Combine audio chunks
        audio = np.concatenate(audio_chunks, axis=0).flatten()

        # Transcribe
        segments, info = self.model.transcribe(
            audio,
            language=self.language,
            beam_size=5,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500)
        )

        # Combine all segments
        text = " ".join(segment.text for segment in segments).strip()
        return text

    def transcribe_file(self, file_path: str, language: str = None) -> str:
        """Transcribe audio from a file.

        Args:
            file_path: Path to audio file (WAV, MP3, WEBM, etc.)
            language: Language code (uses instance default if None)

        Returns:
            Transcribed text
        """
        import librosa

        language = language or self.language

        # Load audio file and resample to expected rate
        audio, _ = librosa.load(file_path, sr=self.sample_rate, mono=True)

        # Transcribe
        segments, info = self.model.transcribe(
            audio,
            language=language,
            beam_size=5,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500)
        )

        # Combine all segments
        text = " ".join(segment.text for segment in segments).strip()
        return text


# Global instance for convenience
_recognizer: Optional[SpeechRecognizer] = None


def get_recognizer() -> SpeechRecognizer:
    """Get or create the global speech recognizer."""
    global _recognizer
    if _recognizer is None:
        _recognizer = SpeechRecognizer()
    return _recognizer


def get_stt() -> SpeechRecognizer:
    """Get or create the global speech recognizer.

    Alias for get_recognizer() for API consistency.
    """
    return get_recognizer()


def preload_stt() -> SpeechRecognizer:
    """Pre-load the STT model and return the recognizer.

    Call this at startup to avoid loading delay on first transcription.
    """
    return get_recognizer()


def transcribe(timeout: float = 10.0) -> str:
    """Convenience function to transcribe speech.

    Args:
        timeout: Maximum time to listen

    Returns:
        Transcribed text
    """
    return get_recognizer().listen_once(timeout=timeout)
