#!/usr/bin/env bash
# Instala FFmpeg en el servidor de Render
apt-get update && apt-get install -y ffmpeg
pip install -r requirements.txt