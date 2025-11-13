# FFmpeg Setup

This directory contains FFmpeg binaries required for video processing.

## Installation

### For Windows (Local Development)

**Option 1: Use existing binaries (Recommended)**

FFmpeg binaries for Windows are already included in this directory:
- `ffmpeg.exe` - FFmpeg version 8.0
- `ffprobe.exe` - FFprobe version 8.0

Verify they work:
```powershell
.\bin\ffmpeg\ffmpeg.exe -version
.\bin\ffmpeg\ffprobe.exe -version
```

**Option 2: Download fresh binaries**

Run the PowerShell download script from the project root:
```powershell
.\download_ffmpeg_windows.ps1
```

This will automatically download and install the latest FFmpeg build for Windows.

### For Linux x64 (Render.com Deployment)

**Important:** Linux binaries are NOT included in the repository. They must be downloaded during deployment.

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

**Manual Installation (Linux):**

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

### Windows
```powershell
.\bin\ffmpeg\ffmpeg.exe -version
.\bin\ffmpeg\ffprobe.exe -version
```

### Linux
```bash
./bin/ffmpeg/ffmpeg -version
./bin/ffmpeg/ffprobe -version
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
