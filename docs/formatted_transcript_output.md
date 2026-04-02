# Formatted Transcript in Final Output

## Overview

The final output now includes a **FORMATTED TRANSCRIPT** section between the raw
transcription and the analysis. This lets you follow along the cleaned text while
watching the video.

## Changes

| File | Change |
|------|--------|
| `main.py` | Updated agent prompt to require a `FORMATTED TRANSCRIPT:` / `ANALYSIS:` structure in the response; added output parsing and a dedicated `FORMATTED TRANSCRIPT` print section |

## Output Structure

```
RAW TRANSCRIPTION
-----------------
<verbatim Whisper output>

FORMATTED TRANSCRIPT
--------------------
<tool-cleaned version — filler words removed, paragraphed/line-broken>

ANALYSIS
--------
<category-specific analysis>
```

The `formatted_transcript` key is also included in the dict returned by
`transcribe_mp3_lyrics` for programmatic use.
