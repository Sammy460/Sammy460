---
name: watch-video
description: >
  This skill should be used when the user shares a video file or video link and asks to
  "watch this video", "what happens in this video", "review this reel", "summarize this clip",
  "transcribe this video", "analyze this TikTok / Reel / Short", or wants exercises, steps or
  quotes pulled out of a video. Extracts keyframes and a transcript so Claude can see and hear the video.
metadata:
  version: "0.1.0"
---

# Watch Video

Turn a video into frames plus a transcript, look at them, then answer the user's question.

## 1. Get the video

- Local file: use the path as given.
- Link (Instagram, TikTok, YouTube, ...): the script downloads it with `yt-dlp` if installed.
  If the download fails (login wall, blocked host, missing `yt-dlp`), say so plainly and ask the user to download the video and share the file. Never invent what the video shows.

## 2. Extract

Run:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/watch-video/scripts/extract.py" "<file-or-url>" --out "<workdir>/video-watch"
```

Options: `--max-frames N` (default 24), `--interval SEC` (fixed spacing instead of scene detection), `--lang de` (force transcript language), `--model small` (Whisper model size).

The script prints a JSON summary with: duration, resolution, the frame list with timestamps, the transcript path, and warnings. Requires `ffmpeg`. Transcription uses `faster-whisper` or `openai-whisper` if installed; otherwise it skips the transcript and warns.

## 3. Watch

1. Read `transcript.txt` if present (timestamped lines).
2. Read the frame images with the Read tool, in time order. For long videos, view every frame's timestamp list first, then open the frames that matter.
3. Match frames to transcript lines by timestamp.

## 4. Answer

Default output when the user just says "watch this":
- **Summary**: 2-3 sentences.
- **Timeline**: `mm:ss` – what is shown / said, one line per scene.
- **Key takeaways**: what the viewer should remember (e.g. exercises with sets/reps, recipe steps, product claims).
- **Text on screen**: captions or overlays visible in frames.

For a reel review, add: hook (first 3 s), pacing, clarity of message, call to action, and 3 concrete improvements.

State what came from audio vs what came from frames. If something is unclear in the frames, say so instead of guessing.

## Hand-off to other plugins

If the video is a workout and the Fitness Buddy plugin is installed, offer to turn the exercises into a plan with its `workout-plan` skill.
