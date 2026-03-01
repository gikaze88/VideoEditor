"""
VIDEO EXTRACTOR WITH QUALITY PRESERVATION/UPSCALING
================================================

This script extracts a specific portion of a video while maintaining or improving its quality.
It uses the upscaling functionality from clip_extractor.py.

USAGE:
python video_extractor.py start_time end_time [--upscale] [--scale-factor 2.0] [--method enhanced]

Example:
python video_extractor.py 00:01:30 00:02:45 --upscale --scale-factor 2.0 --method enhanced
"""

import os
import sys
import argparse
import glob
from datetime import datetime
from clip_extractor import (
    get_video_info,
    seconds_to_hhmmss,
    extract_segment,
    get_upscale_config,
    get_video_quality_info
)
import subprocess

def parse_time_to_seconds(time_str):
    """Convert time string (HH:MM:SS) to seconds."""
    try:
        h, m, s = time_str.split(':')
        return int(h) * 3600 + int(m) * 60 + int(s)
    except ValueError:
        raise ValueError("Time must be in format HH:MM:SS")

def get_video_file(working_dir: str) -> str:
    """Get the first video file from working directory."""
    video_extensions = ['*.mp4', '*.avi', '*.mov', '*.mkv', '*.wmv']
    video_files = []
    
    for ext in video_extensions:
        video_files.extend(glob.glob(os.path.join(working_dir, ext)))
    
    if not video_files:
        return None
    return sorted(video_files)[0]  # Return the first video file alphabetically

def main():
    parser = argparse.ArgumentParser(description='Extract a portion of video with quality preservation/upscaling')
    parser.add_argument('start_time', help='Start time in format HH:MM:SS')
    parser.add_argument('end_time', help='End time in format HH:MM:SS')
    parser.add_argument('--upscale', action='store_true', help='Enable upscaling')
    parser.add_argument('--scale-factor', type=float, default=2.0, help='Upscaling factor (default: 2.0)')
    parser.add_argument('--method', default='enhanced', 
                      choices=['enhanced', 'lanczos', 'bicubic', 'spline', 'ai_super_resolution'],
                      help='Upscaling method (default: enhanced)')
    
    args = parser.parse_args()

    # Define working and output directories
    working_dir = "working_dir"
    output_dir = "output"

    # Create directories if they don't exist
    os.makedirs(working_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    # Get video file from working directory
    video_file = get_video_file(working_dir)
    if not video_file:
        print(f"Error: No video files found in {working_dir} directory")
        print("Supported formats: .mp4, .avi, .mov, .mkv, .wmv")
        sys.exit(1)

    # Convert times to seconds
    try:
        start_seconds = parse_time_to_seconds(args.start_time)
        end_seconds = parse_time_to_seconds(args.end_time)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    # Validate times
    if end_seconds <= start_seconds:
        print("Error: End time must be greater than start time.")
        sys.exit(1)

    # Calculate duration
    duration = end_seconds - start_seconds

    # Get video info
    video_info = get_video_info(video_file)
    if not video_info:
        print("Error: Could not analyze video file.")
        sys.exit(1)

    # Analyze video quality for optimization info
    quality_info = get_video_quality_info(video_file)

    # Validate times against video duration
    if end_seconds > video_info['duration']:
        print(f"Error: End time exceeds video duration ({seconds_to_hhmmss(video_info['duration'])})")
        sys.exit(1)

    # Configure upscaling if enabled
    upscale_config = get_upscale_config(
        video_info,
        enable_upscale=args.upscale,
        scale_factor=args.scale_factor,
        method=args.method
    )

    # Create timestamped output filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(output_dir, f"video_extractor_{timestamp}.mp4")

    # Print extraction info
    print("\n=== Video Extraction Configuration ===")
    print(f"Input file: {os.path.basename(video_file)}")
    print(f"Start time: {args.start_time}")
    print(f"End time: {args.end_time}")
    print(f"Duration: {seconds_to_hhmmss(duration)}")
    print(f"Original resolution: {quality_info['width']}x{quality_info['height']}")
    
    if upscale_config:
        orig_w, orig_h = upscale_config['original_resolution']
        new_w, new_h = upscale_config['resolution']
        upscale_crf = max(18, quality_info['crf'] - 2)
        preset = "fast" if duration > 300 else "medium"
        
        print("\n=== Upscaling Configuration ===")
        print(f"Original resolution: {orig_w}x{orig_h}")
        print(f"New resolution: {new_w}x{new_h}")
        print(f"Scale factor: x{upscale_config['scale_factor']}")
        print(f"Method: {upscale_config['method']}")
        print(f"Quality (CRF): {upscale_crf} (optimized for upscaling)")
        print(f"Encoding preset: {preset} (optimized for speed)")
        improvement = (new_w * new_h) / (orig_w * orig_h)
        print(f"Quality improvement: +{improvement:.1f}x pixels")
    else:
        print(f"Quality (CRF): {quality_info['crf']} (matching original)")
        print("Mode: Original quality preservation (optimized)")
        print("Upscaling: Disabled")
    
    print("=====================================")

    # Extract the segment
    print("\nExtracting video segment with optimized settings...")
    try:
        extract_segment(video_file, start_seconds, duration, output_file, upscale_config)
        print(f"\nExtraction complete! Output saved to: {output_file}")
    except subprocess.CalledProcessError as e:
        print(f"Error during extraction: {e}")
        print("This might be due to:")
        print("- Invalid time range")
        print("- Corrupted video file")
        print("- FFmpeg configuration issues")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 