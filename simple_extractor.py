#!/usr/bin/env python3
"""
Simple Video Extractor
======================
Just extract a segment from a video in working_dir_extractor folder - no fuss, no complexity.
Output goes to simple_extractor_output folder with format: simple_extractor_file_timestamp.mp4
"""

import os
import glob
import subprocess
import time
from datetime import datetime

def get_video_file(working_dir="working_dir_extractor"):
    """Get the first video file from working directory."""
    video_extensions = ['*.mp4', '*.avi', '*.mov', '*.mkv', '*.wmv']
    video_files = []
    
    for ext in video_extensions:
        video_files.extend(glob.glob(os.path.join(working_dir, ext)))
    
    return sorted(video_files)[0] if video_files else None

def parse_time(time_str):
    """Convert time string (HH:MM:SS or MM:SS or seconds) to seconds."""
    if ':' in time_str:
        parts = time_str.split(':')
        if len(parts) == 2:  # MM:SS
            return int(parts[0]) * 60 + int(parts[1])
        elif len(parts) == 3:  # HH:MM:SS
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    else:
        return int(time_str)  # Just seconds

def simple_extract(video_file, start_time, end_time, output_file):
    """Simple video extraction using FFmpeg with stream copy."""
    
    # Calculate duration
    start_seconds = parse_time(start_time)
    end_seconds = parse_time(end_time)
    duration = end_seconds - start_seconds
    
    # Use stream copy for fastest extraction (no re-encoding)
    cmd = [
        "ffmpeg", "-y",
        "-ss", str(start_seconds),  # Start time
        "-i", video_file,           # Input file  
        "-t", str(duration),        # Duration
        "-c", "copy",               # Stream copy (no re-encoding)
        output_file
    ]
    
    print("Running:", " ".join(cmd))
    start = time.time()
    
    # ✅ CORRIGÉ: Utiliser encoding='utf-8' pour gérer les caractères spéciaux
    result = subprocess.run(
        cmd, 
        capture_output=True, 
        text=True,
        encoding='utf-8',
        errors='replace'  # Remplace les caractères non-décodables par '?'
    )
    elapsed = time.time() - start
    
    if result.returncode != 0:
        print(f"❌ Error: {result.stderr}")
        return False
    
    print(f"✅ Done in {elapsed:.1f} seconds!")
    return True

def format_time(seconds):
    """Convert seconds to HH:MM:SS format."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"

def main():
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python simple_extractor.py START_TIME END_TIME")
        print("Examples:")
        print("  python simple_extractor.py 01:30 02:45    # From 1:30 to 2:45")
        print("  python simple_extractor.py 00:01:30 00:02:45  # HH:MM:SS format")
        print("  python simple_extractor.py 90 165         # In seconds")
        return
    
    start_time = sys.argv[1]
    end_time = sys.argv[2]
    
    # Get video file
    video_file = get_video_file()
    if not video_file:
        print("❌ No videos found in working_dir_extractor/")
        return
    
    # Show what we found
    file_size = os.path.getsize(video_file) / (1024*1024)
    print(f"📁 Video: {os.path.basename(video_file)} ({file_size:.1f} MB)")
    
    # Parse times
    try:
        start_seconds = parse_time(start_time)
        end_seconds = parse_time(end_time)
        duration_seconds = end_seconds - start_seconds
        
        if duration_seconds <= 0:
            print("❌ End time must be after start time")
            return
            
        print(f"⏰ Extract from {format_time(start_seconds)} to {format_time(end_seconds)}")
        print(f"⏱️  Duration: {format_time(duration_seconds)}")
        
    except ValueError:
        print("❌ Invalid time format. Use HH:MM:SS, MM:SS, or seconds")
        return
    
    # Create output filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs("simple_extractor_output", exist_ok=True)
    output_file = f"simple_extractor_output/simple_extractor_file_{timestamp}.mp4"
    
    print(f"\n🚀 Extracting to: {output_file}")
    
    # Do the extraction
    if simple_extract(video_file, start_time, end_time, output_file):
        output_size = os.path.getsize(output_file) / (1024*1024)
        print(f"📁 Output: {output_file} ({output_size:.1f} MB)")
    else:
        print("❌ Failed to extract video segment")

if __name__ == "__main__":
    main()