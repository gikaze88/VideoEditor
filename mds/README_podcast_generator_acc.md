# Video Generator Podcast (Accelerated Version)

This script generates videos by looping a background video with an **accelerated audio track** (1.5x speed) from either an audio file or extracted from a video file.

## 🚀 Key Feature

**Audio is automatically accelerated by 1.5x**, reducing video duration by 33% while maintaining audio quality.

## Requirements

- Python 3.x
- FFmpeg installed and available in PATH
- FFprobe (comes with FFmpeg)

## Directory Structure

```
Clip_Extractor/
├── video_generator_podcast_acc.py      # Main script (accelerated version)
├── working_dir_podcast/                # Input directory
│   ├── background_video.mp4           # Background video to loop (REQUIRED)
│   └── [your_audio_or_video_file]     # Your podcast audio/video (REQUIRED)
└── video_generator_podcast_output/    # Output directory
```

## How to Use

### Step 1: Prepare Your Files

Place the following files in the `working_dir_podcast` folder:

1. **background_video.mp4** - A short video that will be looped
2. **Your audio or video file** - Can be any of these formats:
   - Audio: `.mp3`, `.wav`, `.aac`, `.m4a`, `.flac`, `.ogg`, `.wma`
   - Video: `.mp4`, `.avi`, `.mov`, `.mkv`, `.flv`, `.wmv`, `.webm`

### Step 2: Run the Accelerated Script

```bash
python video_generator_podcast_acc.py
```

### Step 3: Get Your Output

The final video will be generated in the `video_generator_podcast_output` folder with a filename like:
```
[input_name]_Acc.mp4
```

## What the Script Does

1. **Detects input type**: Automatically determines if your input is audio or video
2. **Extracts audio**: If input is video, it extracts the audio track
3. **⚡ Accelerates audio by 1.5x**: Uses FFmpeg's `atempo` filter to speed up the audio
4. **Loops background video**: Calculates loops needed for the **accelerated** (shorter) duration
5. **Combines**: Merges the looped background video with your accelerated audio

## Example Workflow

```
# 1. Place files
working_dir_podcast/
├── background_video.mp4        # 10 seconds loop
└── podcast_episode_01.mp3      # 30 minutes (1800 seconds)

# 2. Run accelerated script
python video_generator_podcast_acc.py

# 3. Get output
video_generator_podcast_output/
└── podcast_episode_01_Acc.mp4  # 20 minutes (1200 seconds = 1800 / 1.5)
```

## Speed Comparison

| Original Duration | Accelerated Duration (1.5x) | Time Saved |
|-------------------|----------------------------|------------|
| 30 minutes        | 20 minutes                 | 10 minutes |
| 45 minutes        | 30 minutes                 | 15 minutes |
| 60 minutes        | 40 minutes                 | 20 minutes |
| 90 minutes        | 60 minutes                 | 30 minutes |

## Output Naming Convention

**Accelerated version**: `{input_filename}_Acc.mp4`

Examples:
- Input: `podcast_episode_01.mp3` → Output: `podcast_episode_01_Acc.mp4`
- Input: `interview_john_doe.mp4` → Output: `interview_john_doe_Acc.mp4`

Compare with normal version:
- **Normal**: `podcast_video_{filename}_{timestamp}.mp4`
- **Accelerated**: `{filename}_Acc.mp4` (cleaner, matches your example files)

## Technical Details

### Audio Acceleration
- Uses FFmpeg's `atempo` filter
- Speed factor: **1.5x** (configurable in the script via `SPEED_FACTOR` constant)
- Maintains pitch and audio quality
- Range supported: 0.5x to 2.0x

### Video Quality
- Video codec: H.264
- Video quality: CRF 23
- Audio codec: AAC
- Audio bitrate: 192k

## Customizing Speed Factor

To change the acceleration factor, edit line 11 in the script:

```python
# Change from 1.5x to your desired speed (between 0.5 and 2.0)
SPEED_FACTOR = 1.5  # Example: 1.25 for 25% faster, 1.75 for 75% faster
```

## Differences from Normal Version

| Feature | Normal (`video_generator_podcast.py`) | Accelerated (`video_generator_podcast_acc.py`) |
|---------|--------------------------------------|-----------------------------------------------|
| Audio speed | Original | 1.5x faster |
| Video duration | Same as audio | 33% shorter |
| Output name | `podcast_video_{name}_{timestamp}.mp4` | `{name}_Acc.mp4` |
| Use case | Standard playback | Quick consumption, time-saving |

## Troubleshooting

**Error: "Le facteur de vitesse X n'est pas supporté"**
- The speed factor must be between 0.5 and 2.0
- Edit `SPEED_FACTOR` in the script to a valid value

**Audio sounds distorted**
- Very high speed factors (>1.75) may affect quality
- Try a lower speed factor (e.g., 1.25 or 1.5)

**Video and audio out of sync**
- This shouldn't happen as the background video is looped to match the accelerated audio
- Verify the output file duration matches expectations

## When to Use This Version

✅ **Use accelerated version when:**
- You want to consume content faster
- Time is limited
- Creating preview/summary videos
- Audience prefers faster-paced content

❌ **Use normal version when:**
- Audio timing is critical (music, meditation, etc.)
- Natural pacing is important
- Transcription accuracy matters

