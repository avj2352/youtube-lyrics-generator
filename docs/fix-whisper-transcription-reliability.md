# Fix: OpenAI Whisper Transcription Reliability

## Summary

Improved the robustness of the Whisper transcription step which would previously fail
with no recovery on transient API errors or large audio files.

## Changes

| File | Change |
|------|--------|
| `main.py` | Added `_compress_audio_for_whisper()` helper to compress files that exceed Whisper's 25MB limit using pydub (mono, 16kHz, 64k bitrate) |
| `main.py` | `transcribe_audio_with_whisper()` now retries up to 3 times with exponential backoff on rate limit errors, connection errors, timeouts, and 5xx server errors |
| `main.py` | `transcribe_audio_with_whisper()` now raises exceptions instead of returning error strings, preventing error text from being silently passed to Claude as lyrics |
| `main.py` | `transcribe_mp3_lyrics()` wraps the transcription call in try/except and returns `None` on failure instead of crashing |
| `main.py` | `__main__` block exits with code 1 when `transcribe_mp3_lyrics` returns `None` |

## Root Causes Fixed

1. **No retry on transient errors** — Rate limits, network blips, and OpenAI 5xx errors caused immediate hard failures.
2. **Silent error propagation** — The old `>25MB` code path returned an error *string*, which flowed into Claude as if it were real lyrics.
3. **Large file crashes** — Files over 25MB had no recovery path; now they are compressed with pydub before upload.
4. **Compressed temp file cleanup bug** — Cleanup was placed in a `finally` inside the retry loop, deleting the temp file before retries could use it; moved to a wrapping `try/finally`.
