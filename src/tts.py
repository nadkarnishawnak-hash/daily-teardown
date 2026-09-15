"""Text-to-speech with a free default (Microsoft Edge neural voices) and optional paid upgrades.

Provider order for TTS_PROVIDER=auto: elevenlabs -> openai -> google -> edge (first one with a key wins).
"""
import asyncio
import base64
import re
import sys
from pathlib import Path

import requests

from .config import Config

DEFAULT_VOICES = {
    "edge": "en-US-AndrewMultilingualNeural",   # free; also good: en-US-AvaMultilingualNeural, en-US-BrianMultilingualNeural
    "google": "en-US-Neural2-D",                # 1M chars/mo free (billing must be enabled)
    "openai": "ash",                            # gpt-4o-mini-tts
    "elevenlabs": "JBFqnCBsd6RMkjVDRZzb",       # "George", a stock ElevenLabs voice
}


def pick_provider(cfg: Config) -> str:
    if cfg.tts_provider != "auto":
        return cfg.tts_provider
    if cfg.elevenlabs_key:
        return "elevenlabs"
    if cfg.openai_key:
        return "openai"
    if cfg.google_tts_key:
        return "google"
    return "edge"


def _chunks(text: str, limit: int) -> list[str]:
    """Split on sentence boundaries so no request exceeds the provider's character limit."""
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    out, cur = [], ""
    for s in sentences:
        if len(cur) + len(s) + 1 > limit and cur:
            out.append(cur.strip())
            cur = s
        else:
            cur = f"{cur} {s}".strip()
    if cur:
        out.append(cur)
    return out


def _edge(text: str, voice: str, out: Path) -> None:
    import edge_tts

    async def run():
        await edge_tts.Communicate(text, voice, rate="+4%").save(str(out))

    asyncio.run(run())


def _google(text: str, voice: str, key: str) -> bytes:
    audio = b""
    for chunk in _chunks(text, 4500):  # API limit is 5,000 bytes per request
        r = requests.post(
            "https://texttospeech.googleapis.com/v1/text:synthesize",
            params={"key": key},
            json={"input": {"text": chunk},
                  "voice": {"languageCode": "-".join(voice.split("-")[:2]), "name": voice},
                  "audioConfig": {"audioEncoding": "MP3", "speakingRate": 1.03}},
            timeout=120,
        )
        r.raise_for_status()
        audio += base64.b64decode(r.json()["audioContent"])
    return audio


def _openai(text: str, voice: str, key: str) -> bytes:
    audio = b""
    for chunk in _chunks(text, 3800):  # API limit is 4,096 chars per request
        r = requests.post(
            "https://api.openai.com/v1/audio/speech",
            headers={"Authorization": f"Bearer {key}"},
            json={"model": "gpt-4o-mini-tts", "voice": voice, "input": chunk, "response_format": "mp3",
                  "instructions": "Warm, conversational podcast host. Natural pacing, light energy, clear on numbers."},
            timeout=180,
        )
        r.raise_for_status()
        audio += r.content
    return audio


def _elevenlabs(text: str, voice_id: str, key: str) -> bytes:
    audio = b""
    for chunk in _chunks(text, 4500):
        r = requests.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
            params={"output_format": "mp3_44100_128"},
            headers={"xi-api-key": key, "Content-Type": "application/json"},
            json={"text": chunk, "model_id": "eleven_turbo_v2_5",
                  "voice_settings": {"stability": 0.45, "similarity_boost": 0.8, "style": 0.2}},
            timeout=300,
        )
        r.raise_for_status()
        audio += r.content
    return audio


def synthesize(cfg: Config, text: str, out: Path) -> dict:
    """Write an MP3 to `out`. Returns {"provider", "voice", "duration_sec", "bytes"}."""
    provider = pick_provider(cfg)
    voice = cfg.tts_voice or DEFAULT_VOICES[provider]
    out.parent.mkdir(parents=True, exist_ok=True)
    print(f"[tts] provider={provider} voice={voice} chars={len(text)}", file=sys.stderr)

    if provider == "edge":
        _edge(text, voice, out)
    elif provider == "google":
        out.write_bytes(_google(text, voice, cfg.google_tts_key))
    elif provider == "openai":
        out.write_bytes(_openai(text, voice, cfg.openai_key))
    elif provider == "elevenlabs":
        out.write_bytes(_elevenlabs(text, voice, cfg.elevenlabs_key))
    else:
        raise ValueError(f"unknown TTS_PROVIDER {provider!r}")

    size = out.stat().st_size
    if size < 10_000:
        raise RuntimeError(f"TTS produced a suspiciously small file ({size} bytes)")
    return {"provider": provider, "voice": voice, "duration_sec": _duration(out, text), "bytes": size}


def _duration(path: Path, text: str) -> int:
    try:
        from mutagen.mp3 import MP3
        length = MP3(str(path)).info.length
        if length and length > 5:
            return int(round(length))
    except Exception as e:  # fall back to a words-per-minute estimate
        print(f"[tts] could not read duration ({e}); estimating", file=sys.stderr)
    return int(len(text.split()) / 2.6)


def fmt_duration(seconds: int) -> str:
    m, s = divmod(int(seconds), 60)
    return f"{m}:{s:02d}"
