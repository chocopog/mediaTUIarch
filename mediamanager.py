import subprocess

PLAYER = "spotify"

def pc(*args):
    r = subprocess.run(["playerctl","-p",PLAYER, *args], capture_output=True, text=True)
    return r.stdout.strip()

def minuteconverter(seconds):
    minutes = seconds // 60
    remaining_seconds = seconds % 60
    return f"{minutes}:{remaining_seconds:02d}"


title = pc("metadata", "title")
artist = pc("metadata", "artist")
album = pc("metadata","album")
cover = pc("metadata","mpris:artUrl")
length = minuteconverter(int(pc("metadata", "mpris:length"))/1_000_000)
status = pc("status")
position = minuteconverter(int(pc("position"))/1_000_000)
print(f"{title} - {artist} - {album} - {cover} - {length} - {status} - {position}")