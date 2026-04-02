# Abstract Content Routing (Song vs Spoken)

## Overview

The agent now classifies transcribed audio before processing it, routing to the
appropriate tools depending on whether the content is a **song** or **spoken-word**
material (speech, podcast, interview, lecture, etc.).

## Changes

| File | Change |
|------|--------|
| `util/tools.py` | Added `format_text` tool — formats plain spoken transcriptions into clean paragraphs |
| `main.py` | Renamed `analyze_lyrics_with_claude` → `analyze_with_claude`; added `format_text` to the agent's tool list; updated agent system prompt with explicit two-step classify-then-act instructions; made the Whisper transcription prompt content-neutral |

## Agent Behaviour

**Step 1 — Classify**
Claude reads the raw transcription and decides:
- **SONG** — contains sung lyrics, repeating structures, verse/chorus patterns, or music symbols (♪)
- **SPOKEN** — speech, interview, podcast, lecture, or other plain spoken-word content

**Step 2 — Route**

| Content type | Tools used |
|---|---|
| SONG | `format_lyrics` → `analyze_lyrics_structure` → thematic analysis |
| SPOKEN | `format_text` → key-points summary |

Claude always states its classification decision before calling any tool.
