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
    analyze_lyrics_structure
)
from util.env_config import OPENAI_API_KEY

def transcribe_audio_with_whisper(audio_file_path: str) -> str:
    """
    Transcribe audio using OpenAI Whisper
    
    Whisper processes the entire audio file in one call.
    Returns '♪♪♪' for sections with only music/no vocals.
    """
    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    
    print(f"Transcribing audio with Whisper: {audio_file_path}")
    
    # Check file size (Whisper has 25MB limit)
    file_size_mb = Path(audio_file_path).stat().st_size / (1024 * 1024)
    print(f"Audio file size: {file_size_mb:.2f} MB")
    
    if file_size_mb > 25:
        print("⚠️ Warning: File exceeds 25MB limit. Consider compressing the audio.")
        return "Error: File too large for Whisper API (max 25MB)"
    
    with open(audio_file_path, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="verbose_json",  # Get more details including timestamps
            language="en",  # Specify language for better accuracy (remove if not English)
            prompt="This is a song with vocals and music. Transcribe only the sung lyrics."  # Help guide the model
        )
        
        # Extract the text from verbose response
        transcribed_text = transcript.text
        
        print(f"\n(openai) -> Transcription Info:")
        print(f"  - Language detected: {transcript.language}")
        print(f"  - Duration: {transcript.duration}s")
        print(f"  - Text length: {len(transcribed_text)} characters")
        
        # Check if we got mostly music symbols
        if transcribed_text.count('♪') > len(transcribed_text) * 0.5:
            print("⚠️ Warning: Mostly instrumental audio detected. Limited vocals found.")
        
        return transcribed_text


def analyze_lyrics_with_claude(transcribed_text: str, audio_file_path: str):
    """Analyze transcribed lyrics with Claude"""
    
    bedrock_opus_model = BedrockModel(model_id="us.anthropic.claude-opus-4-6-v1")
    
    agent = Agent(
        model=bedrock_opus_model,
        tools=[
            format_lyrics,
            analyze_lyrics_structure
        ],
        description="""
You are an expert lyrics analysis assistant.
Your role is to analyze transcribed lyrics and provide detailed insights.

When given transcribed lyrics:
1. Format the lyrics properly with line breaks
2. Identify the song structure (verses, chorus, bridge, etc.)
3. Analyze patterns, themes, and meaning
4. Provide insights about the song's message

If the transcription contains mostly music symbols (♪), note that the audio
was primarily instrumental with limited vocals.

Always be thorough and accurate in your analysis.
"""
    )
    
    prompt = f"""
Here are the transcribed lyrics from the audio file: {audio_file_path}

LYRICS:
{transcribed_text}

Please:
1. Format these lyrics with proper line breaks and structure
2. Analyze the song structure (identify verses, chorus, bridge, etc.)
3. Identify any notable patterns, themes, or wordplay
4. Provide insights about the song's message and meaning
5. If mostly instrumental (♪ symbols), note the limited vocal content
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
    transcribed_text = transcribe_audio_with_whisper(mp3_file_path)
    print(f"\n✅ Transcription complete! ({len(transcribed_text)} characters)\n")
    
    # Step 3: Analyze with Claude
    print("🧠 Analyzing lyrics with Claude...")
    analysis = analyze_lyrics_with_claude(transcribed_text, mp3_file_path)
    
    print("\n" + "=" * 80)
    print("TRANSCRIPTION & ANALYSIS RESULTS:")
    print("=" * 80)
    print("\n📝 RAW TRANSCRIPTION:")
    print("-" * 80)
    print(transcribed_text)
    print("\n" + "-" * 80)
    print("\n🎵 ANALYSIS:")
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
