'''
Download youtube videos as mp3
https://www.geeksforgeeks.org/download-video-in-mp3-format-using-pytube/
'''
from strands import tool
import os
import base64
from pydub import AudioSegment
from pathlib import Path
from pytubefix import YouTube
from pytubefix.cli import on_progress
from typing import Optional

@tool
def get_youtube_audio_as_mp3(link: str) -> Optional[str]:
    """download youtube video as mp3 file"""
    # print(f"Downloading youtube URL: {link}...")
    youtubeObject = YouTube(link, on_progress_callback=on_progress, use_oauth=True, allow_oauth_cache=True)
    # extract audio
    video = youtubeObject.streams.filter(only_audio=True).first()        
    try:
        if video is None:
            raise ValueError(f"Unable to obtain videa instance from Youtube")
        # download the file
        audio_file = video.download(output_path="./download")
        if audio_file is None:
            raise ValueError("no data when trying to download video")
        base, _ = os.path.splitext(audio_file)
        mp3_file = base + '.mp3'
        os.rename(audio_file, mp3_file)
        print(f"Audio downloaded: {video.title}")
        return mp3_file
    except Exception as e:
        print(f"Error occured: {e.__class__}: \n {format(e)}")
        return None


# ==============================================================================
# Audio Processing Tools
# ==============================================================================

@tool
def convert_mp3_to_wav(mp3_file_path: str) -> str:
    """
    Convert an MP3 file to WAV format for better compatibility.
    
    Args:
        mp3_file_path: Path to the MP3 file to convert
        
    Returns:
        Path to the converted WAV file
    """
    try:
        mp3_path = Path(mp3_file_path)
        if not mp3_path.exists():
            return f"Error: File {mp3_file_path} not found"
        
        # Load MP3 file
        audio = AudioSegment.from_mp3(mp3_file_path)
        
        # Convert to WAV
        wav_path = mp3_path.with_suffix('.wav')
        audio.export(wav_path, format='wav')
        
        return str(wav_path)
    except Exception as e:
        return f"Error converting MP3 to WAV: {str(e)}"


@tool
def get_audio_info(audio_file_path: str) -> str:
    """
    Get information about an audio file (duration, sample rate, channels).
    
    Args:
        audio_file_path: Path to the audio file
        
    Returns:
        Audio file information as a formatted string
    """
    try:
        audio = AudioSegment.from_file(audio_file_path)
        
        duration_seconds = len(audio) / 1000.0
        minutes = int(duration_seconds // 60)
        seconds = int(duration_seconds % 60)
        
        info = f"""
Audio File Information:
- Duration: {minutes}m {seconds}s ({duration_seconds:.2f} seconds)
- Sample Rate: {audio.frame_rate} Hz
- Channels: {audio.channels} ({'stereo' if audio.channels == 2 else 'mono'})
- Sample Width: {audio.sample_width} bytes
- Frame Width: {audio.frame_width} bytes
"""
        return info
    except Exception as e:
        return f"Error reading audio file: {str(e)}"


@tool
def encode_audio_to_base64(audio_file_path: str) -> str:
    """
    Encode audio file to base64 string for API transmission.
    
    Args:
        audio_file_path: Path to the audio file
        
    Returns:
        Base64 encoded string of the audio file
    """
    try:
        with open(audio_file_path, 'rb') as audio_file:
            audio_data = audio_file.read()
            encoded = base64.b64encode(audio_data).decode('utf-8')
            return encoded
    except Exception as e:
        return f"Error encoding audio: {str(e)}"


@tool
def split_audio_into_chunks(audio_file_path: str, chunk_duration_ms: int = 60000) -> str:
    """
    Split audio file into smaller chunks for processing.
    
    Args:
        audio_file_path: Path to the audio file
        chunk_duration_ms: Duration of each chunk in milliseconds (default: 60000ms = 1 minute)
        
    Returns:
        List of paths to the audio chunks as a string
    """
    try:
        audio = AudioSegment.from_file(audio_file_path)
        audio_path = Path(audio_file_path)
        
        chunks = []
        for i, start_ms in enumerate(range(0, len(audio), chunk_duration_ms)):
            end_ms = min(start_ms + chunk_duration_ms, len(audio))
            chunk = audio[start_ms:end_ms]
            
            chunk_path = audio_path.parent / f"{audio_path.stem}_chunk_{i+1}{audio_path.suffix}"
            chunk.export(chunk_path, format=audio_path.suffix[1:])
            chunks.append(str(chunk_path))
        
        return f"Created {len(chunks)} chunks: " + ", ".join(chunks)
    except Exception as e:
        return f"Error splitting audio: {str(e)}"


# ==============================================================================
# Lyrics Analysis Tools
# ==============================================================================

@tool
def format_lyrics(raw_lyrics: str) -> str:
    """
    Format and clean up transcribed lyrics.
    
    Args:
        raw_lyrics: The raw transcribed lyrics text
        
    Returns:
        Formatted lyrics with proper line breaks and structure
    """
    # Split by common punctuation and format
    lines = raw_lyrics.replace('. ', '.\n').replace('? ', '?\n').replace('! ', '!\n')
    return lines.strip()


@tool
def analyze_lyrics_structure(lyrics: str) -> str:
    """
    Analyze the structure of song lyrics (verses, chorus, bridge, etc.).
    
    Args:
        lyrics: The transcribed lyrics to analyze
        
    Returns:
        Analysis of the song structure
    """
    lines = [line.strip() for line in lyrics.split('\n') if line.strip()]
    word_count = len(lyrics.split())
    line_count = len(lines)
    
    analysis = f"""
Lyrics Structure Analysis:
- Total Lines: {line_count}
- Total Words: {word_count}
- Average Words per Line: {word_count/line_count:.1f}
- Estimated Song Sections: {line_count // 4} (based on typical 4-line sections)

Common Song Structure Patterns:
- Verse-Chorus-Verse-Chorus-Bridge-Chorus
- Intro-Verse-Pre-Chorus-Chorus-Verse-Pre-Chorus-Chorus-Bridge-Chorus-Outro
"""
    return analysis
