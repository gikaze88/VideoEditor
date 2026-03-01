#!/usr/bin/env python3
"""
FFmpeg Process Monitor
Monitors running FFmpeg processes and output file growth
"""

import os
import time
import subprocess
import glob
from pathlib import Path

def get_ffmpeg_processes():
    """Get running FFmpeg processes."""
    try:
        result = subprocess.run(['tasklist', '/fi', 'imagename eq ffmpeg.exe', '/fo', 'csv'], 
                              capture_output=True, text=True, shell=True)
        lines = result.stdout.strip().split('\n')
        processes = []
        for line in lines[1:]:  # Skip header
            if 'ffmpeg.exe' in line:
                parts = line.replace('"', '').split(',')
                if len(parts) >= 5:
                    processes.append({
                        'name': parts[0],
                        'pid': parts[1],
                        'memory': parts[4]
                    })
        return processes
    except:
        return []

def get_output_files():
    """Get output files and their info."""
    output_dir = Path("output")
    if not output_dir.exists():
        return []
    
    files = []
    for file_path in output_dir.glob("*.mp4"):
        if file_path.is_file():
            stat = file_path.stat()
            files.append({
                'name': file_path.name,
                'size_mb': stat.st_size / (1024 * 1024),
                'modified': time.ctime(stat.st_mtime)
            })
    return sorted(files, key=lambda x: x['name'])

def monitor_progress():
    """Monitor FFmpeg progress."""
    print("🔍 FFmpeg Process Monitor")
    print("=" * 50)
    print("Press Ctrl+C to stop monitoring\n")
    
    last_sizes = {}
    
    try:
        while True:
            # Check FFmpeg processes
            processes = get_ffmpeg_processes()
            print(f"⏰ {time.strftime('%H:%M:%S')}")
            
            if processes:
                print(f"🚀 FFmpeg Processes Running: {len(processes)}")
                for proc in processes:
                    print(f"   PID: {proc['pid']} | Memory: {proc['memory']}")
            else:
                print("❌ No FFmpeg processes found")
            
            # Check output files
            output_files = get_output_files()
            if output_files:
                print(f"📁 Output Files:")
                for file_info in output_files:
                    current_size = file_info['size_mb']
                    last_size = last_sizes.get(file_info['name'], 0)
                    growth = current_size - last_size
                    
                    status = "📈 Growing" if growth > 0.1 else "⏸️  Stable"
                    print(f"   {file_info['name']}: {current_size:.1f} MB {status}")
                    
                    last_sizes[file_info['name']] = current_size
            else:
                print("📁 No output files found yet")
            
            print("-" * 50)
            time.sleep(10)  # Update every 10 seconds
            
    except KeyboardInterrupt:
        print("\n✅ Monitor stopped by user")

if __name__ == "__main__":
    monitor_progress() 