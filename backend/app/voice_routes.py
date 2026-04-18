"""
Voice transcription endpoint for MyMitra.
Uses faster-whisper (tiny model) for fully offline, privacy-first STT.
All audio stays on device — nothing ever leaves the user's machine.
"""

import os
import logging
import tempfile
from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)
router = APIRouter()

_whisper_model = None


def _get_whisper_model():
    global _whisper_model
    if _whisper_model is None:
        from faster_whisper import WhisperModel
        # tiny model: ~75 MB, <1 s for short clips on CPU
        _whisper_model = WhisperModel("tiny", device="cpu", compute_type="int8")
        logger.info("Whisper tiny model loaded (offline STT ready)")
    return _whisper_model


@router.post("/voice/transcribe")
async def transcribe_audio(audio: UploadFile = File(...)):
    """
    Transcribe an audio clip to text using the local Whisper tiny model.
    Audio is processed entirely on-device.
    """
    try:
        model = _get_whisper_model()
    except Exception as e:
        logger.error(f"Whisper load failed: {e}")
        raise HTTPException(status_code=503, detail="Speech recognition unavailable")

    try:
        audio_bytes = await audio.read()
        if len(audio_bytes) < 500:
            return JSONResponse({"text": "", "confidence": 0.0})

        suffix = ".webm"
        content_type = audio.content_type or ""
        if "wav" in content_type:
            suffix = ".wav"
        elif "ogg" in content_type:
            suffix = ".ogg"
        elif "mp4" in content_type or "m4a" in content_type:
            suffix = ".mp4"

        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        try:
            segments, info = model.transcribe(
                tmp_path,
                language=None,       # auto-detect language
                beam_size=1,         # fastest path
                vad_filter=True,     # skip silence
                vad_parameters={"min_silence_duration_ms": 400},
            )
            text = " ".join(seg.text.strip() for seg in segments).strip()
            return JSONResponse({
                "text": text,
                "language": info.language,
                "confidence": round(float(info.language_probability), 3),
            })
        finally:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

    except Exception as e:
        logger.error(f"Transcription error: {e}")
        raise HTTPException(status_code=500, detail="Transcription failed")
