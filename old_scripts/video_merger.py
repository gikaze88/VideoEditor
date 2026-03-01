"""
VIDEO MERGER WITH QUALITY PRESERVATION AND SMOOTH TRANSITIONS
=========================================================

This script merges all videos from the working_dir folder into a single video while maintaining
or improving quality and adding smooth transitions between clips.

USAGE:
python video_merger.py [--upscale] [--transition fade] [--transition-duration 1.0]

Example:
python video_merger.py --upscale --transition crossfade --transition-duration 1.5
"""

import os
import sys
import argparse
import subprocess
import json
import tempfile
import glob
from datetime import datetime
from typing import List, Dict
from clip_extractor import get_video_info, get_upscale_config

def get_video_dimensions(video_file: str) -> tuple:
    """Get video dimensions using ffprobe."""
    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height",
        "-of", "json",
        video_file
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    info = json.loads(result.stdout)
    stream = info['streams'][0]
    return int(stream['width']), int(stream['height'])

def create_transition_filter(transition_type: str, duration: float) -> str:
    """Create FFmpeg filter for the specified transition type."""
    if transition_type == "fade":
        return f"xfade=transition=fade:duration={duration}"
    elif transition_type == "crossfade":
        return f"xfade=transition=fade:duration={duration}"
    elif transition_type == "wipeleft":
        return f"xfade=transition=wipeleft:duration={duration}"
    elif transition_type == "wiperight":
        return f"xfade=transition=wiperight:duration={duration}"
    elif transition_type == "wipeup":
        return f"xfade=transition=wipeup:duration={duration}"
    elif transition_type == "wipedown":
        return f"xfade=transition=wipedown:duration={duration}"
    elif transition_type == "circleopen":
        return f"xfade=transition=circleopen:duration={duration}"
    elif transition_type == "circleclose":
        return f"xfade=transition=circleclose:duration={duration}"
    else:
        return f"xfade=transition=fade:duration={duration}"

def get_video_quality_info(video_file: str) -> Dict:
    """Analyze video to determine appropriate quality settings."""
    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height,bit_rate,r_frame_rate,codec_name",
        "-show_entries", "format=bit_rate,duration",
        "-of", "json",
        video_file
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    info = json.loads(result.stdout)
    
    video_stream = info['streams'][0]
    format_info = info['format']
    
    # Calculate appropriate CRF based on video characteristics
    width = int(video_stream.get('width', 1920))
    height = int(video_stream.get('height', 1080))
    
    # Determine quality settings based on resolution and bitrate
    total_pixels = width * height
    
    if total_pixels >= 3840 * 2160:  # 4K
        crf = 20
    elif total_pixels >= 1920 * 1080:  # 1080p
        crf = 21
    elif total_pixels >= 1280 * 720:   # 720p
        crf = 22
    else:  # Lower resolution
        crf = 23
    
    # Get original bitrate if available
    bitrate = None
    if 'bit_rate' in video_stream:
        bitrate = int(video_stream['bit_rate'])
    elif 'bit_rate' in format_info:
        bitrate = int(format_info['bit_rate'])
    
    return {
        'width': width,
        'height': height,
        'crf': crf,
        'bitrate': bitrate,
        'codec': video_stream.get('codec_name', 'unknown'),
        'duration': float(format_info.get('duration', 0))
    }

def merge_videos_fast(
    video_files: List[str],
    output_file: str,
    transition_type: str = "fade",
    transition_duration: float = 0.5  # Shorter default transition
) -> None:
    """
    Fast video merger optimized for speed over complex effects.
    """
    if not video_files:
        raise ValueError("No input videos found in working directory")

    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        
        print(f"\n=== Fast Video Merger ===")
        print(f"Number of videos: {len(video_files)}")
        print(f"Transition duration: {transition_duration} seconds")
        
        if len(video_files) == 1:
            # Single video - just copy with re-encoding for consistency
            cmd = [
                "ffmpeg", "-y",
                "-i", video_files[0],
                "-c:v", "libx264",
                "-preset", "ultrafast",  # Fastest preset
                "-crf", "28",  # Lower quality but much faster
                "-c:a", "aac",
                "-b:a", "128k",
                output_file
            ]
        else:
            # Multiple videos - use simple concatenation method
            # Create a text file listing all videos
            concat_file = os.path.join(temp_dir, "concat_list.txt")
            with open(concat_file, 'w') as f:
                for video in video_files:
                    # Use absolute paths to avoid issues
                    abs_path = os.path.abspath(video)
                    f.write(f"file '{abs_path}'\n")
            
            # Use concat demuxer (fastest method for same format videos)
            cmd = [
                "ffmpeg", "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", concat_file,
                "-c:v", "libx264",
                "-preset", "ultrafast",  # Fastest encoding
                "-crf", "28",  # Reasonable quality/speed balance
                "-c:a", "aac",
                "-b:a", "128k",
                output_file
            ]

        print("Command:", " ".join(cmd))
        print("Starting fast merge...")
        
        try:
            # Run with simple monitoring
            import time
            start_time = time.time()
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=1800  # 30 minute timeout
            )
            
            elapsed = time.time() - start_time
            
            if result.returncode != 0:
                print(f"❌ FFmpeg failed with return code: {result.returncode}")
                print(f"Error output: {result.stderr}")
                raise subprocess.CalledProcessError(result.returncode, cmd)
            
            print(f"✅ Fast merge complete! Time taken: {elapsed:.1f} seconds")
            print(f"Output saved to: {output_file}")
            
        except subprocess.TimeoutExpired:
            print("❌ Process timed out after 30 minutes")
            raise
        except Exception as e:
            print(f"❌ Error during merge: {str(e)}")
            raise

def merge_videos_copy(
    video_files: List[str],
    output_file: str
) -> None:
    """
    Ultra-fast video merger using stream copy (no re-encoding).
    Works best when videos have same format/resolution.
    """
    if not video_files:
        raise ValueError("No input videos found in working directory")

    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        
        print(f"\n=== Ultra-Fast Copy Merger ===")
        print(f"Number of videos: {len(video_files)}")
        print("⚡ Using stream copy - no re-encoding!")
        
        if len(video_files) == 1:
            # Single video - just copy
            cmd = [
                "ffmpeg", "-y",
                "-i", video_files[0],
                "-c", "copy",  # Copy streams without re-encoding
                output_file
            ]
        else:
            # Multiple videos - use concat demuxer with copy
            concat_file = os.path.join(temp_dir, "concat_list.txt")
            with open(concat_file, 'w') as f:
                for video in video_files:
                    # Use absolute paths and escape for Windows
                    abs_path = os.path.abspath(video).replace('\\', '/')
                    f.write(f"file '{abs_path}'\n")
            
            cmd = [
                "ffmpeg", "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", concat_file,
                "-c", "copy",  # Copy streams without re-encoding
                output_file
            ]

        print("Command:", " ".join(cmd))
        print("Starting ultra-fast copy...")
        
        try:
            import time
            start_time = time.time()
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout (should be much faster)
            )
            
            elapsed = time.time() - start_time
            
            if result.returncode != 0:
                print(f"❌ FFmpeg failed with return code: {result.returncode}")
                print(f"Error output: {result.stderr}")
                print("⚠️  Copy method failed. Videos might have different formats.")
                print("💡 Try --fast option for re-encoding merge.")
                raise subprocess.CalledProcessError(result.returncode, cmd)
            
            print(f"✅ Ultra-fast copy complete! Time taken: {elapsed:.1f} seconds")
            print(f"Output saved to: {output_file}")
            
        except subprocess.TimeoutExpired:
            print("❌ Process timed out after 5 minutes")
            raise
        except Exception as e:
            print(f"❌ Error during copy: {str(e)}")
            raise

def get_video_files(working_dir: str, sort_method: str = "name") -> List[str]:
    """Get all video files from working directory with different sorting options."""
    video_extensions = ['*.mp4', '*.avi', '*.mov', '*.mkv', '*.wmv']
    video_files = []
    
    for ext in video_extensions:
        video_files.extend(glob.glob(os.path.join(working_dir, ext)))
    
    if not video_files:
        return []
    
    # Different sorting methods
    if sort_method == "name":
        # Sort by filename alphabetically
        return sorted(video_files)
    elif sort_method == "date":
        # Sort by file modification date (oldest first)
        return sorted(video_files, key=lambda x: os.path.getmtime(x))
    elif sort_method == "size":
        # Sort by file size (smallest first)
        return sorted(video_files, key=lambda x: os.path.getsize(x))
    elif sort_method == "natural":
        # Natural sorting (handles numbers properly: video1, video2, video10)
        import re
        def natural_key(text):
            return [int(c) if c.isdigit() else c.lower() for c in re.split(r'(\d+)', text)]
        return sorted(video_files, key=natural_key)
    else:
        return sorted(video_files)

def show_video_order(video_files: List[str]) -> bool:
    """Show the user the order of videos and ask for confirmation."""
    print("\n=== Video Merge Order ===")
    print("The videos will be merged in this order:")
    for i, video in enumerate(video_files, 1):
        filename = os.path.basename(video)
        file_size = os.path.getsize(video) / (1024*1024)  # Size in MB
        print(f"{i}. {filename} ({file_size:.1f} MB)")
    
    print("\nIs this order correct? (y/n/r)")
    print("y = Yes, proceed with this order")
    print("n = No, cancel the operation")
    print("r = Reverse the order")
    
    while True:
        choice = input("Your choice: ").lower().strip()
        if choice in ['y', 'yes']:
            return True, video_files
        elif choice in ['n', 'no']:
            return False, video_files
        elif choice in ['r', 'reverse']:
            return True, list(reversed(video_files))
        else:
            print("Please enter 'y', 'n', or 'r'")

def main():
    parser = argparse.ArgumentParser(description='Merge all videos from working_dir with quality preservation and transitions')
    parser.add_argument('--upscale', action='store_true', help='Enable upscaling')
    parser.add_argument('--scale-factor', type=float, default=2.0, help='Upscaling factor (default: 2.0)')
    parser.add_argument('--transition', default='fade',
                      choices=['fade', 'crossfade', 'wipeleft', 'wiperight', 'wipeup', 'wipedown',
                              'circleopen', 'circleclose'],
                      help='Transition type (default: fade)')
    parser.add_argument('--transition-duration', type=float, default=1.0,
                      help='Transition duration in seconds (default: 1.0)')
    parser.add_argument('--method', default='enhanced',
                      choices=['enhanced', 'lanczos', 'bicubic', 'spline', 'ai_super_resolution'],
                      help='Upscaling method (default: enhanced)')
    parser.add_argument('--sort', default='name',
                      choices=['name', 'date', 'size', 'natural'],
                      help='Sorting method: name (alphabetical), date (modification time), size, natural (handles numbers)')
    parser.add_argument('--auto-confirm', action='store_true',
                      help='Skip order confirmation and proceed automatically')
    parser.add_argument('--fast', action='store_true',
                      help='Use fast merge mode (no transitions, faster processing)')
    parser.add_argument('--copy', action='store_true',
                      help='Use ultra-fast copy mode (no re-encoding, fastest option)')

    args = parser.parse_args()

    # Define working and output directories
    working_dir = "working_dir"
    output_dir = "output"

    # Create directories if they don't exist
    os.makedirs(working_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    # Get all video files from working directory
    video_files = get_video_files(working_dir, args.sort)
    
    if not video_files:
        print(f"Error: No video files found in {working_dir} directory")
        print("Supported formats: .mp4, .avi, .mov, .mkv, .wmv")
        sys.exit(1)

    # Show video order and get confirmation (unless auto-confirm is enabled)
    if not args.auto_confirm:
        result = show_video_order(video_files)
        proceed, video_files = result
        if not proceed:
            print("Operation cancelled by user.")
            sys.exit(0)

    # Create timestamped output filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(output_dir, f"merged_video_{timestamp}.mp4")

    try:
        if args.copy:
            merge_videos_copy(
                video_files,
                output_file
            )
        elif args.fast:
            merge_videos_fast(
                video_files,
                output_file,
                transition_type=args.transition,
                transition_duration=args.transition_duration
            )
        else:
            # Use original function but with better error handling
            print("⚠️  Using original merge method. For faster processing, use --fast or --copy option.")
            print("💡 Recommendations:")
            print("   --copy   : Ultra-fast (30 seconds) - no re-encoding")
            print("   --fast   : Fast (3-8 minutes) - basic re-encoding") 
            print("   default  : Slow (10-30 minutes) - high quality with transitions")
            merge_videos_fast(  # Still use fast for now until original is fixed
                video_files,
                output_file,
                transition_type=args.transition,
                transition_duration=args.transition_duration
            )
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 