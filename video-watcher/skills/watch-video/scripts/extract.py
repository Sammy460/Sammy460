#!/usr/bin/env python3
"""Extract keyframes and a transcript from a video file or URL.

Usage: extract.py <file-or-url> --out DIR [--max-frames N] [--interval SEC] [--lang CODE] [--model NAME]
Prints a JSON summary to stdout.
"""
import argparse, json, os, re, shutil, subprocess, sys


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def fmt(t):
    t = int(t)
    return f"{t // 60:02d}:{t % 60:02d}"


def download(url, out, warnings):
    if not shutil.which("yt-dlp"):
        sys.exit(json.dumps({"error": "yt-dlp is not installed; download the video manually and pass the file path."}))
    tpl = os.path.join(out, "source.%(ext)s")
    r = run(["yt-dlp", "-f", "mp4/best", "-o", tpl, "--no-playlist", url])
    files = [f for f in os.listdir(out) if f.startswith("source.")]
    if r.returncode != 0 or not files:
        sys.exit(json.dumps({"error": "download failed", "detail": (r.stderr or r.stdout).strip().splitlines()[-3:]}))
    return os.path.join(out, files[0])


def probe(path):
    r = run(["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", path])
    if r.returncode != 0:
        sys.exit(json.dumps({"error": "ffprobe failed", "detail": r.stderr.strip()}))
    info = json.loads(r.stdout)
    dur = float(info["format"].get("duration", 0))
    v = next((s for s in info["streams"] if s["codec_type"] == "video"), None)
    has_audio = any(s["codec_type"] == "audio" for s in info["streams"])
    res = f'{v["width"]}x{v["height"]}' if v else None
    return dur, res, has_audio


def scene_times(path, threshold=0.3):
    r = run(["ffmpeg", "-hide_banner", "-i", path, "-vf", f"select='gt(scene,{threshold})',showinfo", "-f", "null", "-"])
    return [float(m) for m in re.findall(r"pts_time:([0-9.]+)", r.stderr)]


def pick_times(path, dur, max_frames, interval):
    if interval:
        times = [t for t in frange(0, dur, interval)]
    else:
        times = [0.0] + scene_times(path)
        # fill gaps so no stretch longer than dur/max_frames*2 has no frame
        gap = max(dur / max_frames * 2, 1.0)
        filled = []
        for a, b in zip(times, times[1:] + [dur]):
            filled.append(a)
            t = a + gap
            while t < b - gap / 2:
                filled.append(t)
                t += gap
        times = filled
    times = sorted(set(round(t, 2) for t in times if t < dur))
    if len(times) > max_frames:  # evenly thin out
        step = len(times) / max_frames
        times = [times[int(i * step)] for i in range(max_frames)]
    return times


def frange(a, b, s):
    while a < b:
        yield a
        a += s


def grab(path, times, out):
    frames = []
    for i, t in enumerate(times):
        f = os.path.join(out, f"frame_{i:03d}_{fmt(t).replace(':', 'm')}s.jpg")
        run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", str(t), "-i", path,
             "-frames:v", "1", "-vf", "scale='min(768,iw)':-2", "-q:v", "3", f])
        if os.path.exists(f):
            frames.append({"time": fmt(t), "seconds": t, "file": f})
    return frames


def transcribe(path, out, lang, model, warnings):
    wav = os.path.join(out, "audio.wav")
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", path, "-vn", "-ac", "1", "-ar", "16000", wav])
    if not os.path.exists(wav):
        warnings.append("audio extraction failed")
        return None
    segs = None
    try:
        from faster_whisper import WhisperModel
        m = WhisperModel(model, device="cpu", compute_type="int8")
        it, _ = m.transcribe(wav, language=lang)
        segs = [(s.start, s.text.strip()) for s in it]
    except ImportError:
        try:
            import whisper
            res = whisper.load_model(model).transcribe(wav, language=lang)
            segs = [(s["start"], s["text"].strip()) for s in res["segments"]]
        except ImportError:
            warnings.append("no Whisper installed (pip install faster-whisper); transcript skipped, audio saved as audio.wav")
            return None
    txt = os.path.join(out, "transcript.txt")
    with open(txt, "w") as fh:
        for start, text in segs:
            fh.write(f"[{fmt(start)}] {text}\n")
    return txt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source")
    ap.add_argument("--out", required=True)
    ap.add_argument("--max-frames", type=int, default=24)
    ap.add_argument("--interval", type=float)
    ap.add_argument("--lang")
    ap.add_argument("--model", default="small")
    a = ap.parse_args()

    if not shutil.which("ffmpeg"):
        sys.exit(json.dumps({"error": "ffmpeg is not installed"}))
    os.makedirs(a.out, exist_ok=True)
    warnings = []
    path = download(a.source, a.out, warnings) if re.match(r"https?://", a.source) else a.source
    if not os.path.exists(path):
        sys.exit(json.dumps({"error": f"file not found: {path}"}))

    dur, res, has_audio = probe(path)
    frames = grab(path, pick_times(path, dur, a.max_frames, a.interval), a.out)
    transcript = transcribe(path, a.out, a.lang, a.model, warnings) if has_audio else None
    if not has_audio:
        warnings.append("video has no audio track")

    print(json.dumps({"source": path, "duration": fmt(dur), "resolution": res,
                      "frames": frames, "transcript": transcript, "warnings": warnings}, indent=2))


if __name__ == "__main__":
    main()
