# main.py
"""
YouTube Lyrics Transcription with Whisper + Claude Analysis
"""

from strands import Agent
from strands.models.bedrock import BedrockModel
import openai
from pathlib import Path
# ..custom
from util.tools import (
    get_youtube_audio_as_mp3,
    get_audio_info,
    format_lyrics,
    analyze_lyrics_structure,
    format_text,
    parse_technical_content,
)
from util.env_config import OPENAI_API_KEY

def _compress_audio_for_whisper(audio_file_path: str) -> str:
    """
    Compress audio to fit within Whisper's 25MB limit.
    Returns path to the compressed file.
    """
    from pydub import AudioSegment
    import tempfile

    print("  Compressing audio to meet Whisper's 25MB limit...")
    audio = AudioSegment.from_file(audio_file_path)
    # Convert to mono and lower bitrate to reduce size
    audio = audio.set_channels(1).set_frame_rate(16000)
    compressed_path = tempfile.mktemp(suffix=".mp3")
    audio.export(compressed_path, format="mp3", bitrate="64k")
    compressed_size_mb = Path(compressed_path).stat().st_size / (1024 * 1024)
    print(f"  Compressed to {compressed_size_mb:.2f} MB")
    return compressed_path


def transcribe_audio_with_whisper(audio_file_path: str) -> str:
    """
    Transcribe audio using OpenAI Whisper.

    Whisper processes the entire audio file in one call.
    Returns '♪♪♪' for sections with only music/no vocals.
    Retries up to 3 times on transient errors with exponential backoff.
    """
    import time

    client = openai.OpenAI(api_key=OPENAI_API_KEY)

    print(f"Transcribing audio with Whisper: {audio_file_path}")

    # Check file size (Whisper has 25MB limit)
    file_size_mb = Path(audio_file_path).stat().st_size / (1024 * 1024)
    print(f"Audio file size: {file_size_mb:.2f} MB")

    file_to_transcribe = audio_file_path
    compressed_file = None

    if file_size_mb > 25:
        print("⚠️ File exceeds 25MB limit. Attempting compression...")
        compressed_file = _compress_audio_for_whisper(audio_file_path)
        compressed_size_mb = Path(compressed_file).stat().st_size / (1024 * 1024)
        if compressed_size_mb > 25:
            raise ValueError(
                f"Audio file is too large ({compressed_size_mb:.1f} MB) even after compression. "
                "Please trim the audio to a shorter segment."
            )
        file_to_transcribe = compressed_file

    max_attempts = 3
    last_error = None

    try:
        for attempt in range(1, max_attempts + 1):
            try:
                with open(file_to_transcribe, "rb") as audio_file:
                    transcript = client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        response_format="verbose_json",
                        language="en",
                        prompt="Transcribe the audio accurately, including all spoken words and sung lyrics."
                    )

                transcribed_text = transcript.text

                print(f"\n(openai) -> Transcription Info:")
                print(f"  - Language detected: {transcript.language}")
                print(f"  - Duration: {transcript.duration}s")
                print(f"  - Text length: {len(transcribed_text)} characters")

                if transcribed_text.count('♪') > len(transcribed_text) * 0.5:
                    print("⚠️ Warning: Mostly instrumental audio detected. Limited vocals found.")

                return transcribed_text

            except openai.RateLimitError as e:
                last_error = e
                wait = 2 ** attempt
                print(f"⚠️ Rate limit hit (attempt {attempt}/{max_attempts}). Retrying in {wait}s...")
                time.sleep(wait)
            except (openai.APIConnectionError, openai.APITimeoutError) as e:
                last_error = e
                wait = 2 ** attempt
                print(f"⚠️ Connection error (attempt {attempt}/{max_attempts}): {e}. Retrying in {wait}s...")
                time.sleep(wait)
            except openai.APIStatusError as e:
                # 5xx are transient; 4xx (other than 429) are not worth retrying
                if e.status_code >= 500:
                    last_error = e
                    wait = 2 ** attempt
                    print(f"⚠️ Server error {e.status_code} (attempt {attempt}/{max_attempts}). Retrying in {wait}s...")
                    time.sleep(wait)
                else:
                    raise
    finally:
        if compressed_file and Path(compressed_file).exists():
            Path(compressed_file).unlink(missing_ok=True)

    raise RuntimeError(
        f"Whisper transcription failed after {max_attempts} attempts. Last error: {last_error}"
    )


def analyze_with_claude(transcribed_text: str, audio_file_path: str):
    """Analyze transcribed audio with Claude — handles songs, technical, and general spoken content."""

    bedrock_opus_model = BedrockModel(model_id="us.anthropic.claude-opus-4-6-v1")

    agent = Agent(
        model=bedrock_opus_model,
        tools=[
            format_lyrics,
            analyze_lyrics_structure,
            parse_technical_content,
            format_text,
        ],
        description="""
You are an expert audio transcription analyst. You handle three types of video content.

**Step 1 — Classify the content into exactly one category.**

- SONG: contains sung lyrics, repeating lines, verse/chorus patterns, or music symbols (♪).
- TECHNICAL: a tutorial, coding demo, conference talk, product walkthrough, or any video
  where the primary subject is a technology, tool, framework, programming language, or
  software/hardware product. Clues include: code snippets mentioned, CLI commands, API names,
  version numbers, product names, technical jargon, step-by-step instructions.
- GENERAL: everything else — speeches, interviews, podcasts, vlogs, news, documentaries,
  lectures on non-technical topics.

Always state your classification and a one-sentence reason before calling any tool.

---

**Step 2 — Process according to category.**

SONG:
  1. Call `format_lyrics` → formatted lyrics.
  2. Call `analyze_lyrics_structure` → verse/chorus/bridge breakdown.
  3. Provide: themes, notable wordplay, and the song's overall message.

TECHNICAL:
  1. Call `parse_technical_content` → cleaned, segmented transcript.
  2. Using the cleaned text, produce a structured technical overview:
     - **Technology / Product**: name and version (if mentioned).
     - **Overview**: 2-3 sentence summary of what the video covers.
     - **Features & Capabilities**: bulleted list of every distinct feature,
       concept, or capability introduced.
     - **Feature Details**: for each feature bullet, a short paragraph explaining
       what was demonstrated or explained in the video.
     - **Key Takeaways**: 3-5 actionable insights a viewer should walk away with.

GENERAL:
  1. Call `format_text` → clean, paragraphed text.
  2. Provide: a summary of key points, topics covered, and the overall message.
""",
    )

    prompt = f"""
Transcribed audio from: {audio_file_path}

TRANSCRIPTION:
{transcribed_text}

Follow the two-step process in your instructions:
1. Classify the content (SONG / TECHNICAL / GENERAL) and state your reason.
2. Call the appropriate tool(s) and deliver a thorough analysis.

Structure your final response with these two clearly labeled sections:

FORMATTED TRANSCRIPT:
<paste the full output returned by the formatting tool here>

ANALYSIS:
<your full analysis here>
"""

    response = agent(prompt)
    return response


def transcribe_mp3_lyrics(mp3_file_path: str):
    """Main function to transcribe and analyze lyrics"""
    
    print("=" * 80)
    print("🎵 MP3 Lyrics Transcription & Analysis")
    print("=" * 80)
    print(f"\nProcessing: {mp3_file_path}\n")
    
    # Step 1: Get audio info
    print("📊 Getting audio information...")
    audio_info = get_audio_info(mp3_file_path)
    print(f"Audio info: {audio_info}\n")
    
    # Step 2: Transcribe with Whisper
    print("🎤 Transcribing audio with OpenAI Whisper...")
    print("   (Whisper processes the entire audio file in one API call)")
    try:
        transcribed_text = transcribe_audio_with_whisper(mp3_file_path)
    except Exception as e:
        print(f"\n❌ Transcription failed: {e}")
        return None
    print(f"\n✅ Transcription complete! ({len(transcribed_text)} characters)\n")
    
    # Step 3: Analyze with Claude
    print("🧠 Analyzing audio content with Claude...")
    analysis = analyze_with_claude(transcribed_text, mp3_file_path)
    
    # Split agent response into formatted transcript and analysis sections
    analysis_str = str(analysis)
    formatted_transcript = ""
    analysis_body = analysis_str

    if "FORMATTED TRANSCRIPT:" in analysis_str and "ANALYSIS:" in analysis_str:
        parts = analysis_str.split("ANALYSIS:", 1)
        formatted_transcript = parts[0].replace("FORMATTED TRANSCRIPT:", "").strip()
        analysis_body = parts[1].strip()

    print("\n" + "=" * 80)
    print("TRANSCRIPTION & ANALYSIS RESULTS:")
    print("=" * 80)

    print("\n📝 RAW TRANSCRIPTION:")
    print("-" * 80)
    print(transcribed_text)

    if formatted_transcript:
        print("\n" + "-" * 80)
        print("\n📄 FORMATTED TRANSCRIPT:")
        print("-" * 80)
        print(formatted_transcript)

    print("\n" + "-" * 80)
    print("\n🔍 ANALYSIS:")
    print("-" * 80)
    print(analysis_body if formatted_transcript else analysis_str)
    print("\n" + "=" * 80)

    return {
        "transcription": transcribed_text,
        "formatted_transcript": formatted_transcript,
        "analysis": analysis_body if formatted_transcript else analysis_str,
    }


if __name__ == "__main__":
    print("=" * 80)
    print("🎵 YouTube Lyrics AI - Transcription & Analysis")
    print("=" * 80)
    print("\nChoose your input option:")
    print("  1. I have an MP3 file")
    print("  2. I have a YouTube link")
    print("-" * 80)
    
    option = input("Enter your choice (1 or 2): ").strip()
    
    mp3_file = None
    
    if option == "1":
        # Option 1: User has existing MP3 file
        print("\n📁 MP3 File Mode")
        print("-" * 80)
        mp3_file_path = input("Enter the path to your MP3 file: ").strip()
        
        if not mp3_file_path:
            print("❌ Error: MP3 file path is required")
            exit(1)
        
        # Check if file exists
        if not Path(mp3_file_path).exists():
            print(f"❌ Error: File not found: {mp3_file_path}")
            exit(1)
        
        # Check if it's an MP3 file
        if not mp3_file_path.lower().endswith('.mp3'):
            print("⚠️ Warning: File doesn't have .mp3 extension, but will proceed anyway...")
        
        mp3_file = mp3_file_path
        print(f"✅ Using existing file: {mp3_file}\n")
        
    elif option == "2":
        # Option 2: Download from YouTube link (original flow)
        print("\n📺 YouTube Download Mode")
        print("-" * 80)
        link = input("Enter YouTube video URL: ").strip()
        filename = input("Enter the filename: ").strip()
        
        if not link or not filename:
            print("❌ Error: URL and filename are required")
            exit(1)
        
        print(f"\n📥 Downloading from: {link}")
        mp3_file = get_youtube_audio_as_mp3(link=link, file_name=filename)
        
        if not mp3_file:
            print("❌ Download failed")
            exit(1)
        
        print(f"✅ Downloaded to: {mp3_file}\n")
        
    else:
        print("❌ Error: Invalid option. Please enter 1 or 2")
        exit(1)
    
    # Transcribe and analyze
    results = transcribe_mp3_lyrics(mp3_file_path=mp3_file)
    if results is None:
        exit(1)
