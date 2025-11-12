#!/bin/bash

# Script to download FFmpeg static build for Linux x64
# This is required for deployment on Render.com

set -e

echo "Downloading FFmpeg static build for Linux x64..."

# Download FFmpeg static build
wget -q --show-progress https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz

echo "Extracting FFmpeg..."
tar -xf ffmpeg-release-amd64-static.tar.xz

echo "Copying binaries..."
cp ffmpeg-*-amd64-static/ffmpeg ./ffmpeg
cp ffmpeg-*-amd64-static/ffprobe ./ffprobe

echo "Setting executable permissions..."
chmod +x ./ffmpeg ./ffprobe

echo "Cleaning up..."
rm -rf ffmpeg-*-amd64-static*

echo "FFmpeg installation complete!"
echo "FFmpeg version:"
./ffmpeg -version | head -n 1
