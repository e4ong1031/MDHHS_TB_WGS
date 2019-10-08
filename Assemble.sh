#!/bin/bash

sudo docker run --rm -v $1:$1 -v $2:$2 e4ong1031/mdhhs_assemble:latest python3.6 Assemble.py -i $1 -o $2
