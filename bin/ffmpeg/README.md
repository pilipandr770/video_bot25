# FFmpeg Setup

This directory contains FFmpeg binaries required for video processing.

## Installation

### For Linux x64 (Render.com deployment)

Run the download script to automatically download and install FFmpeg:

```bash
cd bin/ffmpeg
bash download_ffmpeg.sh
```

This will:
1. Download the latest FFmpeg static build for Linux x64
2. Extract the binaries
3. Copy `ffmpeg` and `ffprobe` to this directory
4. Set executable permissions
5. Clean up temporary files

### Manual Installation

If you prefer to install manually:

```bash
# Download FFmpeg static build
wget https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz

# Extract
tar -xf ffmpeg-release-amd64-static.tar.xz

# Copy binaries
cp ffmpeg-*-amd64-static/ffmpeg bin/ffmpeg/
cp ffmpeg-*-amd64-static/ffprobe bin/ffmpeg/

# Set permissions
chmod +x bin/ffmpeg/ffmpeg bin/ffmpeg/ffprobe

# Clean up
rm -rf ffmpeg-*-amd64-static*
```

## Verification

After installation, verify FFmpeg is working:

```bash
./ffmpeg -version
./ffprobe -version
```

## Usage in Application

The application automatically detects FFmpeg binaries in this directory. The `FFmpegUtil` class in `app/utils/ffmpeg.py` handles all FFmpeg operations.

## Requirements

- Linux x64 system (for Render.com deployment)
- wget (for download script)
- tar (for extraction)

## Notes

- FFmpeg binaries are platform-specific. The download script is configured for Linux x64.
- For local development on Windows or macOS, you may need to install FFmpeg separately or use platform-specific binaries.
- The static build includes all necessary codecs and doesn't require additional dependencies.
- Total size: approximately 70-80 MB for both binaries.

## Troubleshooting

### Permission Denied

If you get permission errors when running FFmpeg:

```bash
chmod +x bin/ffmpeg/ffmpeg bin/ffmpeg/ffprobe
```

### Command Not Found

Ensure you're using the full path to the binary:

```bash
./bin/ffmpeg/ffmpeg -version
```

Or add to PATH (not recommended for production):

```bash
export PATH=$PATH:$(pwd)/bin/ffmpeg
```
