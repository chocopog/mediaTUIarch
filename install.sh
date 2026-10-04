#!/usr/bin/env bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "installing tool globally"

sudo cp "$DIR/mediaplayer.py" /usr/local/bin/mdplayer
sudo chmod +x /usr/local/bin/mdplayer

echo "Success its now installed my g, run mdplayer to Launch it"

