# YouTube Lyrics AI 🎵

Generate gospel song lyrics using YouTube API and Strands SDK with Google Gemini AI / Bedrock Models.

## Overview

This project automatically transcribes and analyzes lyrics from YouTube videos using advanced AI. It downloads audio from YouTube, processes it through multiple tools, and uses Google's Gemini AI to accurately transcribe lyrics and provide detailed song structure analysis.

## Features

- ✅ **YouTube Audio Download** - Automatically download audio from any YouTube video
- ✅ **Audio Format Conversion** - Convert MP3 to WAV for better compatibility
- ✅ **Smart Audio Processing** - Split long audio files into manageable chunks
- ✅ **AI-Powered Transcription** - Use Google Gemini AI for accurate lyrics transcription
- ✅ **Structure Analysis** - Automatically identify verses, choruses, and song patterns
- ✅ **Formatted Output** - Get properly formatted lyrics with line breaks
- ✅ **Audio Metadata** - Extract duration, bitrate, and other audio information

## Requirements

- Python 3.14+
- FFmpeg (for audio processing)
- AWS cli


## Pre-requisites

**Solution:** Install FFmpeg (see Installation section above)

### Poor Transcription Quality

**Tips for better results:**
- Use clear audio with minimal background noise
- Ensure vocals are prominent in the mix
- For very long songs, the system automatically splits into chunks
- Try `gemini-1.5-pro-latest` for better accuracy (costs more)

## API Costs

Google Gemini API pricing (as of 2024):
- **gemini-1.5-flash:** Very low cost, fast
- **gemini-1.5-pro:** Higher quality, moderate cost

See [Google AI Pricing](https://ai.google.dev/pricing) for current rates.

## Limitations

- Audio quality affects transcription accuracy
- Very heavy background music may interfere with lyrics detection
- Non-English lyrics may have varying accuracy
- YouTube download depends on video availability and restrictions

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

[Add your license here]

## Acknowledgments

- [Strands SDK](https://github.com/strands-ai/strands) - AI agent framework
- [Google Gemini AI](https://ai.google.dev/) - AI model for transcription
- [PyTubeFix](https://github.com/JuanBindez/pytubefix) - YouTube audio download
- [Pydub](https://github.com/jiaaro/pydub) - Audio processing

## Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Check existing issues for solutions
- Review the Troubleshooting section above

---

**Made with ❤️ for gospel music transcription**
