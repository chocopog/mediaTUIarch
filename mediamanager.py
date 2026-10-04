#!/usr/bin/env python3
"""mediamanager a terminal now-playing controller with album art.

Reads track info and sends controls through playerctl (MPRIS), and draws the
album cover with chafa. Works with Spotify.
Keys:  space play/pause   n next   p previous   <- -> seek 5s
       up/down (or +/-) volume   s shuffle   q quit
"""

import argparse
import hashlib
import os
import select
import shutil
import subprocess
import sys
import termios
import time
import tty
import urllib.request

CACHE = os.path.expanduser("~/.cache/mediamanager")
PLAYER = "spotify"
CHAFA_FORMAT = "auto"

ESC = "\x1b"

#playerctl

def pc(*args):
    try:
        r = subprocess.run(
            ["playerctl", "-p", PLAYER, *args],
            capture_output=True, text=True, timeout=2,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return r.stdout.strip()


def to_float(text, default=0.0):
    try:
        return float(text)
    except ValueError:
        return default


def get_metadata():
    """Return a fresh dict describing the current track, or None if nothing plays."""
    title = pc("metadata", "title")
    if not title:
        return None

    return {
        "title": title,
        "artist": pc("metadata", "artist"),
        "album": pc("metadata", "album"),
        "cover": pc("metadata", "mpris:artUrl"),
        "length": to_float(pc("metadata", "mpris:length")) / 1_000_000,
        "status": pc("status"),
        "position": to_float(pc("position")),
        "volume": to_float(pc("volume"), default=-1.0),
        "shuffle": pc("shuffle"),
    }


#album cover

def get_art(cover_url):
    """Return a local file path for the cover, downloading and caching it."""
    if not cover_url:
        return None
    if cover_url.startswith("file://"):
        path = cover_url[len("file://"):]
        return path if os.path.exists(path) else None

    os.makedirs(CACHE, exist_ok=True)
    name = hashlib.sha1(cover_url.encode()).hexdigest()
    path = os.path.join(CACHE, name)

    if not os.path.exists(path):
        try:
            with urllib.request.urlopen(cover_url, timeout=5) as resp:
                data = resp.read()
            with open(path, "wb") as f:
                f.write(data)
        except Exception:
            return None
    return path


def render_art(path, width, height):
    """Return chafa's rendering of the image, or '' if chafa/the file is unavailable."""
    if not path or not shutil.which("chafa"):
        return ""
    try:
        r = subprocess.run(
            ["chafa", "--size", f"{width}x{height}", "--animate=off",
             "--format", CHAFA_FORMAT, path],
            capture_output=True, text=True, timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return r.stdout if r.returncode == 0 else ""


# ------------------------------------------------------------------ drawing -- ai made

def fmt_time(seconds):
    seconds = int(max(seconds, 0))
    return f"{seconds // 60}:{seconds % 60:02d}"


def clip(text, width):
    return text if len(text) <= width else text[: max(width - 1, 0)] + "…"


def write(text):
    sys.stdout.write(text)


def move(row, col=1):
    return f"{ESC}[{row};{col}H"


def layout(size):
    """Work out how big the art can be for this terminal size."""
    text_rows = 7
    art_h = max(size.lines - text_rows - 1, 4)
    art_w = min(size.columns, art_h * 2)
    return art_w, art_h, art_h + 2  # width, height, first text row


def draw_idle(size):
    write(f"{ESC}[2J")
    mid = max(size.lines // 2, 1)
    msg = "No track is playing"
    write(move(mid, max((size.columns - len(msg)) // 2, 1)) + msg)
    hint = "waiting for the player...   q to quit"
    write(move(mid + 2, max((size.columns - len(hint)) // 2, 1)) + hint)
    sys.stdout.flush()


def draw_art(art, size):
    write(f"{ESC}[2J" + move(1))
    if art:
        write(art)
    else:
        write("(no cover art)")


def draw_text(track, size):
    _, _, row = layout(size)
    cols = size.columns

    length = track["length"]
    position = min(track["position"], length) if length else track["position"]
    bar_w = max(cols - 16, 10)
    filled = int(bar_w * position / length) if length else 0
    bar = "█" * filled + "░" * (bar_w - filled)

    icon = {"Playing": "▶", "Paused": "⏸"}.get(track["status"], "■")
    if track["volume"] >= 0:
        vol = f"vol {int(round(track['volume'] * 100))}%"
    else:
        vol = "vol --"
    shuffle = "shuffle on" if track["shuffle"].lower() == "on" else "shuffle off"

    byline = track["artist"]
    if track["album"]:
        byline = f"{byline} — {track['album']}" if byline else track["album"]

    lines = [
        f"{ESC}[1m{clip(track['title'], cols)}{ESC}[0m",
        clip(byline, cols),
        "",
        f"{bar} {fmt_time(position)}/{fmt_time(length)}",
        f"{icon} {track['status']}   {vol}   {shuffle}",
        "",
        clip("space play/pause  n next  p prev  ←/→ seek  ↑/↓ volume  s shuffle  q quit", cols),
    ]
    for i, line in enumerate(lines):
        write(move(row + i) + line + f"{ESC}[K")
    sys.stdout.flush()

#keyboard inputs

def read_key(timeout):
    ready, _, _ = select.select([sys.stdin], [], [], timeout)
    if not ready:
        return None
    ch = os.read(sys.stdin.fileno(), 1).decode(errors="ignore")
    if ch != ESC:
        return ch
    # Possible arrow-key escape sequence: ESC [ A/B/C/D
    seq = ""
    while len(seq) < 2 and select.select([sys.stdin], [], [], 0.02)[0]:
        seq += os.read(sys.stdin.fileno(), 1).decode(errors="ignore")
    return {"[A": "up", "[B": "down", "[C": "right", "[D": "left"}.get(seq)


def handle_key(key):
    if key in ("q", "Q"):
        return False
    if key == " ":
        pc("play-pause")
    elif key == "n":
        pc("next")
    elif key == "p":
        pc("previous")
    elif key == "right":
        pc("position", "5+")
    elif key == "left":
        pc("position", "5-")
    elif key in ("up", "+", "="):
        pc("volume", "0.05+")
    elif key in ("down", "-", "_"):
        pc("volume", "0.05-")
    elif key == "s":
        pc("shuffle", "Toggle")
    return True


#main

def run():
    last_title = None
    last_cover = None
    last_size = None
    art_path = None
    art = ""
    idle_drawn = False

    while True:
        track = get_metadata()
        size = shutil.get_terminal_size()

        if track is None:
            # forger song
            last_title = last_cover = None
            art_path = None
            art = ""
            if not idle_drawn or size != last_size:
                draw_idle(size)
                idle_drawn = True
        else:
            idle_drawn = False
            song_changed = track["title"] != last_title or track["cover"] != last_cover
            resized = size != last_size

            if song_changed or resized:
                if song_changed:
                    art_path = get_art(track["cover"])
                    last_title, last_cover = track["title"], track["cover"]
                art_w, art_h, _ = layout(size)
                art = render_art(art_path, art_w, art_h)
                draw_art(art, size)
            draw_text(track, size)

        last_size = size

        key = read_key(1.0)  
        if key is not None:
            if not handle_key(key):
                return
            continue

#idk what this AI made
def main():
    global PLAYER, CHAFA_FORMAT

    parser = argparse.ArgumentParser(description="Terminal now-playing controller with album art.")
    parser.add_argument("-p", "--player", default=PLAYER,
                        help="playerctl player name (default: spotify; see `playerctl -l`)")
    parser.add_argument("--format", default=CHAFA_FORMAT,
                        help="chafa output format: auto, kitty, sixels, symbols, ... (default: auto)")
    args = parser.parse_args()
    PLAYER = args.player
    CHAFA_FORMAT = args.format

    if not sys.stdin.isatty() or not sys.stdout.isatty():
        sys.exit("nowplaying needs to run in an interactive terminal.")
    if not shutil.which("playerctl"):
        sys.exit("playerctl not found. Install it first (e.g. sudo pacman -S playerctl).")

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)
        write(f"{ESC}[?1049h{ESC}[?25l")  # alternate screen, hide cursor
        sys.stdout.flush()
        run()
    except KeyboardInterrupt:
        pass
    finally:
        write(f"{ESC}[?25h{ESC}[?1049l")  # show cursor, leave alternate screen
        sys.stdout.flush()
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


if __name__ == "__main__":
    main()