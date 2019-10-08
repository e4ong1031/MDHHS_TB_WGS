#!/bin/bash

sudo docker run --rm -v $1:$1 -v $2:$2 -e DISPLAY={$DISPLAY} -v /tmp/.X11-unix:/tmp/.X11-unix:ro -e USERID=$UID -e USER=$USER -v $HOME/.Xauthority:/home/developer/.Xauthority e4ong1031/mdhhs_assemble:latest python3.6 Assemble.py -i $1 -o $2
