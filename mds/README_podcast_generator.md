# Video Generator Podcast

This script generates videos by looping a background video with an audio track from either an audio file or extracted from a video file.

## Requirements

- Python 3.x
- FFmpeg installed and available in PATH
- FFprobe (comes with FFmpeg)

## Directory Structure

```
Clip_Extractor/
├── video_generator_podcast.py          # Main script
├── working_dir_podcast/                # Input directory
│   ├── background_video.mp4           # Background video to loop (REQUIRED)
│   └── [your_audio_or_video_file]     # Your podcast audio/video (REQUIRED)
└── video_generator_podcast_output/    # Output directory
```

## How to Use

### Step 1: Prepare Your Files

Place the following files in the `working_dir_podcast` folder:

1. **background_video.mp4** - A short video that will be looped to match your audio duration
2. **Your audio or video file** - Can be any of these formats:
   - Audio: `.mp3`, `.wav`, `.aac`, `.m4a`, `.flac`, `.ogg`, `.wma`
   - Video: `.mp4`, `.avi`, `.mov`, `.mkv`, `.flv`, `.wmv`, `.webm`

### Step 2: Run the Script

```bash
python video_generator_podcast.py
```

### Step 3: Get Your Output

The final video will be generated in the `video_generator_podcast_output` folder with a filename like:
```
podcast_video_[input_name]_[timestamp].mp4
```

## What the Script Does

1. **Detects input type**: Automatically determines if your input is audio or video
2. **Extracts audio**: If input is video, it extracts the audio track
3. **Loops background video**: Calculates how many times to loop `background_video.mp4` to match the audio duration
4. **Combines**: Merges the looped background video with your audio

## Example Workflow

```
# 1. Place files
working_dir_podcast/
├── background_video.mp4        # 10 seconds loop
└── podcast_episode_01.mp3      # 30 minutes

# 2. Run script
python video_generator_podcast.py

# 3. Get output (background video looped 180 times)
video_generator_podcast_output/
└── podcast_video_podcast_episode_01_20251127_142030.mp4
```

## Differences from video_generator_v1.py

This simplified version:
- ✅ Does NOT require ElevenLabs API
- ✅ Does NOT generate subtitles/SRT files
- ✅ Does NOT require Whisper
- ✅ Automatically detects audio vs video input
- ✅ Simple workflow: just place files and run
- ✅ No configuration needed

## Troubleshooting

**Error: "background_video.mp4 not found"**
- Make sure the file is named exactly `background_video.mp4` (case-insensitive)
- Ensure it's in the `working_dir_podcast` folder

**Error: "No audio or video file found"**
- Place at least one audio or video file in `working_dir_podcast`
- Make sure the file extension is supported (see list above)

**Error: "ffmpeg not found"**
- Install FFmpeg: https://ffmpeg.org/download.html
- Add FFmpeg to your system PATH

## Output Quality

- Video codec: H.264
- Video quality: CRF 23 (good balance between quality and file size)
- Audio codec: AAC
- Audio bitrate: 192k

