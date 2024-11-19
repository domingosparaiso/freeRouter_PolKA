#!/bin/bash
src=10.0.17.2
dst=10.160.0.20
ping -i 5 -D ${dst} | sed -u -r "s/\[([0-9]*\.[0-9]*)\].*time=([0-9]*\.[0-9]*) ms$/\1 \2/g" | python latency.py ${src} ${dst}
