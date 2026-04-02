# Three-Category Content Routing

## Overview

The agent now classifies transcribed audio into one of three categories and routes
each to its own processing path:

| Category | Description | Tools used |
|---|---|---|
| **SONG** | Sung lyrics, verse/chorus patterns, music symbols | `format_lyrics` → `analyze_lyrics_structure` |
| **TECHNICAL** | Tutorial, demo, conference talk, product walkthrough | `parse_technical_content` → structured technical overview |
| **GENERAL** | Speech, interview, podcast, vlog, non-technical lecture | `format_text` → key-points summary |

## Changes

| File | Change |
|------|--------|
| `util/tools.py` | Added `parse_technical_content` tool — removes filler words, segments transcript into logical blocks for downstream technical analysis |
| `main.py` | Added `parse_technical_content` to agent tool list; updated agent system prompt with three-category classify-then-act instructions |

## Technical Video Output Format

When the agent classifies content as TECHNICAL it produces:

- **Technology / Product** — name and version if mentioned
- **Overview** — 2-3 sentence description of what the video covers
- **Features & Capabilities** — bulleted list of every distinct feature or concept introduced
- **Feature Details** — a paragraph per feature explaining what was demonstrated
- **Key Takeaways** — 3-5 actionable insights the viewer should walk away with
