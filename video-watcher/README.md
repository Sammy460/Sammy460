# Video Watcher

Lets Claude watch a video. Give it a video file or link and ask "watch this", "summarize this reel" or "what exercises are in this video".

## How it works
1. Downloads the link with `yt-dlp` (or uses your local file).
2. Pulls keyframes at scene changes with `ffmpeg`.
3. Transcribes speech with Whisper.
4. Claude looks at the frames, reads the transcript, and answers.

## Requirements
- `ffmpeg` (required)
- `yt-dlp` for links: `pip install yt-dlp`
- `faster-whisper` for transcripts: `pip install faster-whisper`

Instagram and some other sites need a login to download. If a link fails, download the video yourself and give Claude the file.

## Install (Claude Code)
```
/plugin marketplace add Sammy460/Sammy460
/plugin install video-watcher@sammy460
```
