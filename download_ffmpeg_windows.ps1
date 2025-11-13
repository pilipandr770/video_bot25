# Download FFmpeg for Windows
# This script downloads FFmpeg static build for Windows

$ffmpegUrl = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
$downloadPath = "ffmpeg-windows.zip"
$extractPath = "bin/ffmpeg"

Write-Host "🔽 Downloading FFmpeg for Windows..." -ForegroundColor Cyan

try {
    # Create bin/ffmpeg directory if it doesn't exist
    if (-not (Test-Path $extractPath)) {
        New-Item -ItemType Directory -Path $extractPath -Force | Out-Null
    }

    # Download FFmpeg
    Write-Host "Downloading from: $ffmpegUrl"
    Invoke-WebRequest -Uri $ffmpegUrl -OutFile $downloadPath -UseBasicParsing
    
    Write-Host "✅ Download complete!" -ForegroundColor Green
    Write-Host "📦 Extracting..." -ForegroundColor Cyan
    
    # Extract zip
    Expand-Archive -Path $downloadPath -DestinationPath "temp_ffmpeg" -Force
    
    # Find ffmpeg.exe and ffprobe.exe in extracted files
    $ffmpegExe = Get-ChildItem -Path "temp_ffmpeg" -Filter "ffmpeg.exe" -Recurse | Select-Object -First 1
    $ffprobeExe = Get-ChildItem -Path "temp_ffmpeg" -Filter "ffprobe.exe" -Recurse | Select-Object -First 1
    
    if ($ffmpegExe -and $ffprobeExe) {
        # Copy to bin/ffmpeg
        Copy-Item $ffmpegExe.FullName -Destination "$extractPath/ffmpeg.exe" -Force
        Copy-Item $ffprobeExe.FullName -Destination "$extractPath/ffprobe.exe" -Force
        
        Write-Host "✅ FFmpeg installed successfully!" -ForegroundColor Green
        Write-Host "📍 Location: $extractPath" -ForegroundColor Yellow
        
        # Test FFmpeg
        Write-Host "`n🧪 Testing FFmpeg..." -ForegroundColor Cyan
        & "$extractPath/ffmpeg.exe" -version | Select-Object -First 1
        
        Write-Host "`n✅ FFmpeg is ready to use!" -ForegroundColor Green
    } else {
        Write-Host "❌ Could not find ffmpeg.exe or ffprobe.exe in archive" -ForegroundColor Red
    }
    
    # Cleanup
    Write-Host "`n🧹 Cleaning up..." -ForegroundColor Cyan
    Remove-Item $downloadPath -Force
    Remove-Item "temp_ffmpeg" -Recurse -Force
    
    Write-Host "✅ Done!" -ForegroundColor Green
    
} catch {
    Write-Host "❌ Error: $_" -ForegroundColor Red
    exit 1
}
