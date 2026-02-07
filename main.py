"""
Strands Agents SDK Example: Transcribe Lyrics from MP3 using Gemini AI

This example demonstrates how to use the Strands Agents SDK with Google's Gemini AI
to transcribe and analyze lyrics from an MP3 audio file.

Requirements:
    pip install strands-agents google-genai pydub
    
You'll also need ffmpeg installed:
    - Mac: brew install ffmpeg
    - Ubuntu: sudo apt-get install ffmpeg
    - Windows: Download from ffmpeg.org
"""

import os
import base64
from pathlib import Path
from strands import Agent, tool
# from strands.models.gemini import GeminiModel
from strands.models.bedrock import BedrockModel
from typing import Optional
from pydub import AudioSegment
# ..custom
from util.tools import (
    get_youtube_audio_as_mp3,
    convert_mp3_to_wav,
    get_audio_info,
    encode_audio_to_base64,
    split_audio_into_chunks,
    format_lyrics,
    analyze_lyrics_structure
)
from util.env_config import GEMINI_API_KEY

# ==============================================================================
# Main Application
# ==============================================================================

def transcribe_mp3_lyrics(mp3_file_path: str, gemini_api_key: Optional[str] = None):
    """
    Main function to transcribe lyrics from an MP3 file using Gemini AI.
    
    Args:
        mp3_file_path: Path to the MP3 file containing the song
        gemini_api_key: Google Gemini API key (can also be set as GEMINI_API_KEY env var)
    """
    
    # Get API key from environment if not provided
    if not gemini_api_key:
        gemini_api_key: Optional[str] = os.environ.get('GEMINI_API_KEY') or None
    
    if not gemini_api_key:
        print("Error: Please provide GEMINI_API_KEY either as parameter or environment variable")
        return
    
    # Configure Gemini model with audio processing capabilities
    gemini_model = BedrockModel(model_id="us.anthropic.claude-opus-4-6-v1")    
    # Create agent with audio processing and lyrics analysis tools
    agent = Agent(
        model=gemini_model,
        tools=[
            get_youtube_audio_as_mp3,
            convert_mp3_to_wav,
            get_audio_info,
            encode_audio_to_base64,
            split_audio_into_chunks,
            format_lyrics,
            analyze_lyrics_structure
        ],
        description="""
You are an expert audio transcription and lyrics analysis assistant. 
Your role is to help transcribe lyrics from audio files and provide detailed analysis.

When given an audio file:
1. First, get information about the audio file
2. If needed, convert MP3 to WAV format for better compatibility
3. For long files, consider splitting into chunks
4. Transcribe the lyrics accurately, capturing every word
5. Format the lyrics properly with line breaks
6. Analyze the song structure and provide insights

Always be thorough and accurate in transcription.
"""
    )
    
    print("=" * 80)
    print("🎵 MP3 Lyrics Transcription with Gemini AI & Strands Agents")
    print("=" * 80)
    print(f"\nProcessing: {mp3_file_path}\n")
    
    # Create the transcription prompt
    prompt = f"""
Please transcribe the lyrics from the audio file: {mp3_file_path}

Follow these steps:
1. Get information about the audio file
2. Transcribe all the lyrics you can hear from the audio
3. Format the lyrics with proper line breaks
4. Analyze the song structure

Provide:
- Complete transcribed lyrics
- Song structure analysis (verses, chorus, etc.)
- Any notable patterns or themes in the lyrics
"""
    
    # Run the agent
    print("Agent is processing the audio file...")
    print("-" * 80)
    
    response = agent(prompt)
    
    print("\n" + "=" * 80)
    print("TRANSCRIPTION RESULTS:")
    print("=" * 80)
    print(response)
    print("\n" + "=" * 80)
    
    return response


# MAIN Application

if __name__ == "__main__":
    # transcribe youtube audio file
    link = input("Enter youtube video url: ")
    link = link.strip()
    print("Downloading youtube mp3...")
    mp3_file = get_youtube_audio_as_mp3(link=link)
    if not mp3_file:
        print("No MP3 file created")
        exit()
    print(f"MP3 file location: {mp3_file}")
    transcribe_mp3_lyrics(mp3_file_path=mp3_file, gemini_api_key=GEMINI_API_KEY)
