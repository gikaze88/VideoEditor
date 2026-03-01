#!/usr/bin/env python3
"""
Simple Video Concatenator
=========================
Just concatenate all videos from working_dir_merger folder - no fuss, no complexity.
Output goes to simple_merger_output folder with format: simple_merger_file_timestamp.mp4
"""

import os
import glob
import subprocess
import tempfile
import time
from datetime import datetime

def get_video_files(working_dir="working_dir_merger"):
    """Get all video files from working directory."""
    video_extensions = ['*.mp4', '*.avi', '*.mov', '*.mkv', '*.wmv']
    video_files = []
    
    for ext in video_extensions:
        video_files.extend(glob.glob(os.path.join(working_dir, ext)))
    
    return sorted(video_files) if video_files else []

def simple_concat(video_files, output_file):
    """Simple video concatenation using FFmpeg."""
    
    if len(video_files) == 1:
        # Single video - just copy
        cmd = ["ffmpeg", "-y", "-i", video_files[0], "-c", "copy", output_file]
    else:
        # Multiple videos - create concat list and merge
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            for video in video_files:
                abs_path = os.path.abspath(video).replace('\\', '/')
                f.write(f"file '{abs_path}'\n")
            concat_file = f.name
        
        try:
            cmd = [
                "ffmpeg", "-y",
                "-f", "concat",
                "-safe", "0", 
                "-i", concat_file,
                "-c", "copy",
                output_file
            ]
        except:
            os.unlink(concat_file)
            raise
    
    print("Running:", " ".join(cmd))
    start = time.time()
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if len(video_files) > 1:
        os.unlink(concat_file)
    
    elapsed = time.time() - start
    
    if result.returncode != 0:
        print(f"❌ Error: {result.stderr}")
        return False
    
    print(f"✅ Done in {elapsed:.1f} seconds!")
    return True

def confirm_video_order(video_files):
    """Show video order and ask for confirmation."""
    print(f"\n📁 Found {len(video_files)} videos:")
    print("=== Video Merge Order ===")
    total_size = 0
    for i, video in enumerate(video_files, 1):
        size_mb = os.path.getsize(video) / (1024*1024)
        total_size += size_mb
        print(f"  {i}. {os.path.basename(video)} ({size_mb:.1f} MB)")
    
    print(f"\nTotal size: {total_size:.1f} MB")
    print("\nThe videos will be merged in this order.")
    print("\nOptions:")
    print("  y = Yes, proceed with this order")
    print("  r = Reverse the order")
    print("  n = No, cancel the operation")
    
    while True:
        choice = input("\nYour choice (y/r/n): ").lower().strip()
        if choice in ['y', 'yes']:
            return video_files
        elif choice in ['r', 'reverse']:
            reversed_files = list(reversed(video_files))
            print("\n🔄 Reversed order:")
            for i, video in enumerate(reversed_files, 1):
                print(f"  {i}. {os.path.basename(video)}")
            return reversed_files
        elif choice in ['n', 'no']:
            return None
        else:
            print("❌ Please enter 'y' (yes), 'r' (reverse), or 'n' (no)")

def main():
    import sys
    
    # Check for auto-confirm flag
    auto_confirm = "--auto-confirm" in sys.argv
    
    # Get videos
    video_files = get_video_files()
    
    if not video_files:
        print("❌ No videos found in working_dir_merger/")
        return
    
    # Confirm order with user (unless auto-confirm is enabled)
    if auto_confirm:
        print(f"\n📁 Found {len(video_files)} videos (auto-confirm mode):")
        for i, video in enumerate(video_files, 1):
            size_mb = os.path.getsize(video) / (1024*1024)
            print(f"  {i}. {os.path.basename(video)} ({size_mb:.1f} MB)")
        print("✅ Proceeding with alphabetical order...")
        confirmed_files = video_files
    else:
        confirmed_files = confirm_video_order(video_files)
        if not confirmed_files:
            print("🚫 Operation cancelled by user.")
            return
    
    # Create output filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs("simple_merger_output", exist_ok=True)
    output_file = f"simple_merger_output/simple_merger_file_{timestamp}.mp4"
    
    print(f"\n🚀 Concatenating to: {output_file}")
    
    # Do the merge
    if simple_concat(confirmed_files, output_file):
        file_size = os.path.getsize(output_file) / (1024*1024)
        print(f"✅ Success! Output: {output_file} ({file_size:.1f} MB)")
    else:
        print("❌ Failed to merge videos")

if __name__ == "__main__":
    main() 