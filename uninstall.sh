#!usr/bin/env bash
set -e

echo "Removing mdplayer, sad to see u go u pos"

if [ -f /usr/local/bin/mdplayer ]; then
	sudo rm /usr/local/bin/mdplayer
	echo "its done. now u also go scram, skedaddle"
else
	echo "its not even installed, or its an unknown error"
	echo "whatever it may be, goodluck to u in figuring it out"
fi
