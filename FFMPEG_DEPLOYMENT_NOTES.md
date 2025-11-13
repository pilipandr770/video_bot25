# FFmpeg Deployment Notes

## Overview

This project requires FFmpeg binaries for video processing. The setup differs between local development (Windows) and production deployment (Linux).

## Current Status

✅ **Windows binaries**: Already installed and verified
- Location: `bin/ffmpeg/ffmpeg.exe` and `bin/ffmpeg/ffprobe.exe`
- Version: FFmpeg 8.0 (essentials build)
- Status: Working correctly

⚠️ **Linux binaries**: Not included in repository (by design)
- Must be downloaded during Render.com deployment
- Script available: `bin/ffmpeg/download_ffmpeg.sh`

## Deployment Process for Render.com

### Option 1: Build Command (Recommended)

Add FFmpeg download to your Render.com build command in `render.yaml`:

```yaml
services:
  - type: web
    name: ai-video-bot
    buildCommand: |
      pip install -r requirements.txt
      cd bin/ffmpeg && bash download_ffmpeg.sh && cd ../..
```

### Option 2: Dockerfile

If using Docker deployment, add to your Dockerfile:

```dockerfile
# Copy FFmpeg download script
COPY bin/ffmpeg/download_ffmpeg.sh /app/bin/ffmpeg/

# Download and install FFmpeg
RUN cd /app/bin/ffmpeg && bash download_ffmpeg.sh

# Ensure executable permissions
RUN chmod +x /app/bin/ffmpeg/ffmpeg /app/bin/ffmpeg/ffprobe
```

### Option 3: Manual Setup

After first deployment, SSH into your Render instance and run:

```bash
cd /app/bin/ffmpeg
bash download_ffmpeg.sh
```

## Why Not Include Linux Binaries in Git?

1. **Size**: FFmpeg binaries are ~70-80 MB, which bloats the repository
2. **Platform-specific**: Windows and Linux binaries are different
3. **Updates**: Easier to download latest version during deployment
4. **Git LFS**: Would require Git Large File Storage setup

## Verification After Deployment

After deploying to Render.com, verify FFmpeg is working:

```bash
# Check if binaries exist
ls -lh /app/bin/ffmpeg/

# Test FFmpeg
/app/bin/ffmpeg/ffmpeg -version

# Test FFprobe
/app/bin/ffmpeg/ffprobe -version
```

## Application Configuration

The application automatically detects FFmpeg location:

```python
# app/utils/ffmpeg.py
class FFmpegUtil:
    def __init__(self, ffmpeg_path: str = None):
        self.ffmpeg_path = ffmpeg_path or self._get_ffmpeg_path()
        
    @staticmethod
    def _get_ffmpeg_path() -> str:
        base_dir = os.path.dirname(os.path.dirname(__file__))
        # On Windows: bin/ffmpeg/ffmpeg.exe
        # On Linux: bin/ffmpeg/ffmpeg
        return os.path.join(base_dir, 'bin', 'ffmpeg', 'ffmpeg')
```

## Troubleshooting

### Issue: FFmpeg not found after deployment

**Solution**: Ensure the download script ran during build:
```bash
cd bin/ffmpeg && bash download_ffmpeg.sh
```

### Issue: Permission denied

**Solution**: Set executable permissions:
```bash
chmod +x bin/ffmpeg/ffmpeg bin/ffmpeg/ffprobe
```

### Issue: Download script fails

**Solution**: Check if wget is available:
```bash
which wget
# If not available, install: apt-get install wget
```

## Local Development vs Production

| Aspect | Windows (Local) | Linux (Render.com) |
|--------|----------------|-------------------|
| Binary names | `ffmpeg.exe`, `ffprobe.exe` | `ffmpeg`, `ffprobe` |
| Installation | Pre-installed | Download during build |
| Script | `download_ffmpeg_windows.ps1` | `download_ffmpeg.sh` |
| Permissions | Not required | `chmod +x` required |
| Size | ~120 MB | ~70 MB (static build) |

## Next Steps

Before deploying to Render.com:

1. ✅ Verify Windows binaries work locally (DONE)
2. ✅ Update render.yaml with FFmpeg download in buildCommand
3. ✅ Test Dockerfile if using Docker deployment
4. ⏳ Deploy to Render.com
5. ⏳ Verify FFmpeg works in production environment

## References

- FFmpeg Static Builds: https://johnvansickle.com/ffmpeg/
- Windows Builds: https://www.gyan.dev/ffmpeg/builds/
- FFmpeg Documentation: https://ffmpeg.org/documentation.html
