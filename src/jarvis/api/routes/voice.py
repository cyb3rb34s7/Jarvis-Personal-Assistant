"""JARVIS API - Voice endpoints (STT/TTS)."""

import base64
import io
import tempfile
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import Response
from pydantic import BaseModel

from ..auth import verify_token

router = APIRouter()


class TranscribeResponse(BaseModel):
    text: str
    language: Optional[str] = None
    confidence: Optional[float] = None


class SynthesizeRequest(BaseModel):
    text: str
    voice: str = "af_heart"
    speed: float = 1.0


@router.post("/voice/transcribe", response_model=TranscribeResponse)
async def transcribe_audio(
    file: UploadFile = File(...),
    language: str = "hi",
    _: None = Depends(verify_token),
):
    """Transcribe audio to text using Whisper.

    Args:
        file: Audio file (WAV, MP3, WEBM, etc.)
        language: Language hint (default: hi for Hindi/Hinglish)

    Returns:
        Transcribed text
    """
    try:
        from ...voice.stt import get_stt
    except ImportError:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Voice dependencies not installed. Run: pip install jarvis[voice]",
        )

    # Read uploaded file
    content = await file.read()

    # Save to temp file (Whisper needs file path)
    suffix = Path(file.filename).suffix if file.filename else ".wav"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        # Transcribe
        stt = get_stt()
        text = stt.transcribe_file(tmp_path, language=language)

        return TranscribeResponse(
            text=text,
            language=language,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Transcription failed: {str(e)}",
        )
    finally:
        # Clean up temp file
        Path(tmp_path).unlink(missing_ok=True)


@router.post("/voice/synthesize")
async def synthesize_speech(
    data: SynthesizeRequest,
    _: None = Depends(verify_token),
):
    """Synthesize text to speech using Kokoro.

    Args:
        data: Text to synthesize and voice settings

    Returns:
        Audio file (WAV format)
    """
    try:
        from ...voice.tts import get_tts
    except ImportError:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Voice dependencies not installed. Run: pip install jarvis[voice]",
        )

    if not data.text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Text cannot be empty",
        )

    try:
        tts = get_tts()

        # Generate audio
        audio_data = tts.synthesize(data.text, voice=data.voice, speed=data.speed)

        if audio_data is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="TTS returned no audio data",
            )

        # Return as WAV
        return Response(
            content=audio_data,
            media_type="audio/wav",
            headers={
                "Content-Disposition": f'attachment; filename="speech.wav"',
            },
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Synthesis failed: {str(e)}",
        )


@router.post("/voice/synthesize/base64")
async def synthesize_speech_base64(
    data: SynthesizeRequest,
    _: None = Depends(verify_token),
):
    """Synthesize text to speech, returning base64-encoded audio.

    Useful for WebSocket or JSON responses.

    Args:
        data: Text to synthesize and voice settings

    Returns:
        Base64-encoded audio data
    """
    try:
        from ...voice.tts import get_tts
    except ImportError:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Voice dependencies not installed. Run: pip install jarvis[voice]",
        )

    if not data.text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Text cannot be empty",
        )

    try:
        tts = get_tts()

        # Generate audio
        audio_data = tts.synthesize(data.text, voice=data.voice, speed=data.speed)

        if audio_data is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="TTS returned no audio data",
            )

        # Encode as base64
        audio_b64 = base64.b64encode(audio_data).decode("utf-8")

        return {
            "audio": audio_b64,
            "format": "wav",
            "text": data.text,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Synthesis failed: {str(e)}",
        )
