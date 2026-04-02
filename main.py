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
    format_text
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
    """Analyze transcribed audio with Claude — handles both songs and spoken content."""

    bedrock_opus_model = BedrockModel(model_id="us.anthropic.claude-opus-4-6-v1")

    agent = Agent(
        model=bedrock_opus_model,
        tools=[
            format_lyrics,
            analyze_lyrics_structure,
            format_text,
        ],
        description="""
You are an expert audio transcription analyst.

**Step 1 — Classify the content.**
Read the transcribed text carefully and decide whether it is:
  - A SONG: contains sung lyrics, repeating lines, verses/chorus patterns, or music symbols (♪).
  - SPOKEN: a speech, interview, podcast, lecture, or other plain spoken-word content.

**Step 2 — Process accordingly.**
- If SONG:
    1. Call `format_lyrics` to format the lyrics with proper line breaks.
    2. Call `analyze_lyrics_structure` to identify verses, chorus, bridge, etc.
    3. Share insights about patterns, themes, and the song's meaning.
    4. If mostly instrumental (♪ symbols), note the limited vocal content.
- If SPOKEN:
    1. Call `format_text` to clean up and paragraph the spoken text.
    2. Summarise the key points, topics, and overall message of the content.

Always state your classification decision before using any tool.
"""
    )

    prompt = f"""
Transcribed audio from: {audio_file_path}

TRANSCRIPTION:
{transcribed_text}

Follow the two-step process described in your instructions:
1. Classify whether this is a SONG or SPOKEN content.
2. Use the appropriate tool(s) and provide a thorough analysis.
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
    
    print("\n" + "=" * 80)
    print("TRANSCRIPTION & ANALYSIS RESULTS:")
    print("=" * 80)
    print("\n📝 RAW TRANSCRIPTION:")
    print("-" * 80)
    print(transcribed_text)
    print("\n" + "-" * 80)
    print("\n🔍 ANALYSIS:")
    print("-" * 80)
    print(analysis)
    print("\n" + "=" * 80)
    
    return {
        "transcription": transcribed_text,
        "analysis": analysis
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
