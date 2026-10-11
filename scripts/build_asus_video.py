#!/usr/bin/env python3
"""Build the ASUS UGen AI League Stage I demo video: NINE CIRCLES (2:48, 1920x1080).

Usage:
    python3 build_asus_video.py abstract    # circle_abstract_1..9.jpg
    python3 build_asus_video.py lissajous   # lissajous_<circle>.jpg
Output:
    ~/workspace/goals/hackathon-submission-pipeline/files/asus_nine_circles_<set>.mp4

Timeline: 8s title card, 9 x 17s circles with captions, 7s outro = 168s total.
"""
import os
import subprocess
import sys
import tempfile

BASE = os.path.expanduser("~/workspace/your_files")
OUTDIR = os.path.expanduser("~/workspace/goals/hackathon-submission-pipeline/files")
FPS = 24
SEG = 17  # seconds per circle
FRAMES = FPS * SEG
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

CIRCLES = ["limbo", "lust", "gluttony", "greed", "wrath",
           "heresy", "violence", "fraud", "treachery"]
ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX"]

SETS = {
    "abstract": [os.path.join(BASE, f"circle_abstract_{i}.jpg") for i in range(1, 10)],
    "lissajous": [os.path.join(BASE, f"lissajous_{c}.jpg") for c in CIRCLES],
}


def run(cmd):
    print("+", " ".join(cmd))
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr[-3000:])
        raise SystemExit(f"ffmpeg failed: {' '.join(cmd[:4])}")
    return r


def card(tmp, name, lines, seconds):
    """Black title/outro card."""
    out = os.path.join(tmp, name)
    texts = "".join(
        f"drawtext=fontfile={FONT}:text='{l}':fontcolor=white:fontsize={sz}:"
        f"x=(w-text_w)/2:y={y}:,"
        for l, sz, y in lines
    )
    run(["ffmpeg", "-y", "-f", "lavfi", "-i",
         f"color=black:s=1920x1080:d={seconds}:r={FPS}",
         "-vf", texts.rstrip(","), "-c:v", "libx264", "-pix_fmt", "yuv420p",
         "-r", str(FPS), out])
    return out


def segment(tmp, img, caption, idx):
    out = os.path.join(tmp, f"seg{idx:02d}.mp4")
    vf = (
        "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,setsar=1,"
        f"zoompan=z='min(1+0.15*on/{FRAMES},1.15)':d={FRAMES}:"
        "x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1920x1080:fps=24,"
        f"drawtext=fontfile={FONT}:text='{caption}':fontcolor=white:fontsize=64:"
        "x=(w-text_w)/2:y=h-140:box=1:boxcolor=0x000000AA:boxborderw=24"
    )
    run(["ffmpeg", "-y", "-loop", "1", "-i", img, "-vf", vf,
         "-c:v", "libx264", "-pix_fmt", "yuv420p", "-t", str(SEG), out])
    return out


def main():
    which = sys.argv[1] if len(sys.argv) > 1 else "abstract"
    if which not in SETS:
        raise SystemExit(f"unknown set {which!r}; choose one of {list(SETS)}")
    images = SETS[which]
    for p in images:
        if not os.path.isfile(p):
            raise SystemExit(f"missing image: {p}")
    if not os.path.isfile(FONT):
        raise SystemExit(f"missing font: {FONT}")
    os.makedirs(OUTDIR, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        parts = [card(tmp, "title.mp4", [
            ("NINE CIRCLES", 96, "(h-text_h)/2-70"),
            ("an original descent in nine movements", 44, "(h-text_h)/2+60"),
        ], 8)]
        for i, (img, c, r) in enumerate(zip(images, CIRCLES, ROMAN)):
            parts.append(segment(tmp, img, f"{r} \\u00b7 {c.upper()}", i))
        parts.append(card(tmp, "outro.mp4", [
            ("Original artwork", 64, "(h-text_h)/2-50"),
            ("created for the ASUS UGen AI League \\u00b7 Creator AI", 36, "(h-text_h)/2+40"),
        ], 7))
        lst = os.path.join(tmp, "parts.txt")
        with open(lst, "w") as f:
            for p in parts:
                f.write(f"file '{p}'\n")
        out = os.path.join(OUTDIR, f"asus_nine_circles_{which}.mp4")
        run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst,
             "-c", "copy", out])
        dur = run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                   "-of", "csv=p=0", out]).stdout.strip()
        print(f"DONE: {out} ({float(dur):.1f}s, {os.path.getsize(out)/1e6:.1f} MB)")


if __name__ == "__main__":
    main()
