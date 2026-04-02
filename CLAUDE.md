# Youtube Lyrics AI

An AI powered Youtube Lyrics generator. A Command Line application.

## Architecture

### Build tool

This project uses `UV` build tool. The following are commands from UV:

```bash
# install a new package
uv add <package-name>

# remove a package
uv remove <package-name>

# to run application
uv run main.py

# to see dependency tree
uv tree -d 1
```

### Strands Agents SDK

The`youtube_lyrics_ai` is built using Strands Agents SDK. A downloaded version of `strands-agents` python
SDK is available under `downloaded_site`.


### OpenAI SDK

The project also uses `openai` package for `speech-to-text`, transcribing Audio files to Text

## Documentation

For every enhancement, change or bug fix, create a documentation (Markdown file) under `docs`.
- List all the files that were created / changed - with a single line summary of the change


