# Media Manager
SO FAR ONLY TESTED ON ARCH

Was missing a specific style of terminal media player, either that or I didn't look far enough.
Whatever may be the case, it's a fun project for now.

Using Python to make a wrapper for playerctl to present data such as artist, song, album, and the album art. It shows the cover in your terminal, updates when the song changes, and lets you control playback from the keyboard.

## Dependencies (so far)
- playerctl
- chafa (optional, without it you just don't get the cover)
- python3

installation
```bash
bash install.sh
```s

uninstallation
```bash
bash uninstall.sh
```

no external library in python  
for installing dependancies on Arch:

```bash
sudo pacman -S playerctl chafa
```

## Usage

```bash
python3 nowplaying.py                  # controls Spotify
python3 nowplaying.py -p spotifyd      # another player (see `playerctl -l`)
python3 nowplaying.py --format symbols # force chafa's block-character output
```

The cover quality depends on your terminal. `--format auto` (the default) lets chafa pick: kitty is the only one ive tested on so far, and its pretty crisp. 
## Keys

| Key | Action |
|---|---|
| `space` | play / pause |
| `n` / `p` | next / previous |
| `←` / `→` | seek 5 seconds |
| `↑` / `↓` or `+` / `-` | volume |
| `s` | toggle shuffle |
| `q` | quit |

## How it works

A loop asks playerctl for the current track once a second and compares the title and cover URL with the previously played song.. Only when they change does it download the cover (cached in `~/.cache/nowplaying/`) and redraw it with chafa. The title, artist, progress bar, volume and shuffle state refresh every pass.

When nothing is playing it shows "No track is playing" and forgets the last song, so replaying the same one later still draws its cover.

By default it only talks to the player named `spotify`, so one needs the app for it. wont work on website.
### I guess these are important commands I should remember during the duration of our project in case I forget
`playerctl -l` (list the players that are running, the name goes after `-p`)

`playerctld daemon` (so playerctl detects the recently used media player; note `nowplaying.py` passes `-p spotify` itself, so this only matters for playerctl commands you run by hand)

`playerctl metadata --format '{{artist}} - {{title}}'` or something similar
Pick the player yourself

**Pick the player yourself**
```bash
playerctl -p spotify status           # target one player
playerctl -p spotify,firefox status   # first one that's running
playerctl -a pause                    # every player at once
```

**Read track info**
```bash
playerctl -p spotify metadata                                   # everything it knows
playerctl -p spotify metadata --format '{{artist}} - {{title}}' # just the fields you want
playerctl -p spotify metadata mpris:artUrl                      # the album art link
playerctl -p spotify metadata mpris:length                      # length, in microseconds
playerctl -p spotify position                                   # seconds into the song
playerctl -p spotify status                                     # Playing / Paused / Stopped
```

**Watch changes live** (prints a new line every time something changes, nice for seeing what playerctl reports)
```bash
playerctl -p spotify --follow metadata --format '{{artist}} - {{title}} [{{status}}]'
```

**Control playback**
```bash
playerctl -p spotify play-pause
playerctl -p spotify next
playerctl -p spotify previous
playerctl -p spotify position 30      # jump to 30 seconds
playerctl -p spotify position 5+      # forward 5 seconds (5- goes back)
playerctl -p spotify volume 0.5       # 50%
playerctl -p spotify volume 0.05+     # a bit louder (0.05- is quieter)
playerctl -p spotify shuffle Toggle   # or On / Off
playerctl -p spotify loop Playlist    # or None / Track
```

**Try chafa on its own** (any image, handy for testing how it looks in your terminal)
```bash
chafa --size 40x20 ~/.cache/nowplaying/<some-file>
chafa --format symbols image.jpg      # block characters, works anywhere
chafa --format kitty image.jpg        # crisp, kitty / Ghostty / WezTerm
chafa --format sixels image.jpg       # foot and other sixel terminals
```

**Poke at the code from Python** (check what `get_metadata()` returns without starting the UI)
```bash
python3 -c "import nowplaying; print(nowplaying.get_metadata())"
```

**Cover cache**
```bash
ls ~/.cache/nowplaying           # downloaded covers
rm -r ~/.cache/nowplaying        # clear it, they just get downloaded again
```

**Push to GitHub**
```bash
git init
git add nowplaying.py README.md .gitignore
git commit -m "Terminal now-playing controller with album art"
gh repo create nowplaying --public --source=. --push
```

## Notes

- If the cover is misplaced after resizing the terminal, it redraws on the next pass.

# HUGE THANKS TO THE MAKERS OF PLAYERCTL AND CHAFA