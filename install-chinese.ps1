# GitHub Desktop Chinese Installation Script for Windows
# Usage: Right-click this file and select "Run with PowerShell"
# Or execute: Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process -Force; .\install-chinese.ps1

$ErrorActionPreference = "Stop"
$WarningPreference = "SilentlyContinue"

# Colors
$Green = "Green"
$Red = "Red"
$Yellow = "Yellow"
$Cyan = "Cyan"

function Log-Message($msg) {
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Add-Content -Path "logs/install.log" -Value "[$ts] $msg"
}

if (-not (Test-Path "logs")) {
    New-Item -ItemType Directory -Path "logs" -Force | Out-Null
}

Write-Host ""
Write-Host "========================================"  -ForegroundColor $Cyan
Write-Host "  GitHub Desktop Chinese Installer"  -ForegroundColor $Cyan
Write-Host "========================================"  -ForegroundColor $Cyan
Write-Host ""

Log-Message "Installation started"

# Check admin rights
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "WARNING: This script requires administrator privileges" -ForegroundColor $Yellow
    Write-Host "Please run PowerShell as Administrator" -ForegroundColor $Yellow
    Log-Message "ERROR: Administrator privileges required"
    Read-Host "Press Enter to exit"
    exit 1
}

# Detect GitHub Desktop installation path
Write-Host "Detecting GitHub Desktop installation path..." -ForegroundColor $Cyan
Log-Message "Detecting GitHub Desktop installation path"

$paths = @(
    "$env:LOCALAPPDATA\GitHubDesktop\app-*\resources",
    "$env:ProgramFiles\GitHub Desktop\resources",
    "C:\Users\$env:USERNAME\AppData\Local\GitHubDesktop\app-*\resources"
)

$foundPath = $null
foreach ($pattern in $paths) {
    $results = Get-Item -Path $pattern -ErrorAction SilentlyContinue
    if ($results) {
        $foundPath = $results[0].FullName
        break
    }
}

if (-not $foundPath) {
    Write-Host "ERROR: GitHub Desktop installation not found" -ForegroundColor $Red
    Write-Host "Please install GitHub Desktop from https://desktop.github.com/" -ForegroundColor $Red
    Log-Message "ERROR: GitHub Desktop installation not found"
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Found GitHub Desktop: $foundPath" -ForegroundColor $Green
Log-Message "Found GitHub Desktop: $foundPath"

# Check for app folder (new unpacked format) or app.asar (old packed format)
$appPath = Join-Path $foundPath "app"
$appAsarPath = Join-Path $foundPath "app.asar"
$appAsarBackup = Join-Path $foundPath "app.asar.backup"

$isUnpacked = Test-Path $appPath -PathType Container
$isPacked = Test-Path $appAsarPath -PathType Leaf

if (-not $isUnpacked -and -not $isPacked) {
    Write-Host "ERROR: GitHub Desktop app not found (neither app folder nor app.asar)" -ForegroundColor $Red
    Log-Message "ERROR: GitHub Desktop app not found"
    Read-Host "Press Enter to exit"
    exit 1
}

if ($isPacked) {
    Write-Host "Found packed app.asar format" -ForegroundColor $Green
}
else {
    Write-Host "Found unpacked app folder format" -ForegroundColor $Green
}

# Backup for packed format
if ($isPacked) {
    Write-Host ""
    Write-Host "Backing up original file..." -ForegroundColor $Cyan
    Log-Message "Backing up original file"

    if (Test-Path $appAsarBackup) {
        Write-Host "Backup already exists, skipping" -ForegroundColor $Yellow
    }
    else {
        Copy-Item -Path $appAsarPath -Destination $appAsarBackup -Force
        Write-Host "Backup completed: $appAsarBackup" -ForegroundColor $Green
        Log-Message "Backup completed: $appAsarBackup"
    }
}

# Download patch
Write-Host ""
Write-Host "Downloading Chinese localization patch..." -ForegroundColor $Cyan
Log-Message "Downloading Chinese localization patch"

$repoUrl = "https://github.com/SkymAu/github-desktop-chinese"
$downloadUrl = "https://github.com/SkymAu/github-desktop-chinese/archive/refs/heads/main.zip"
$zipPath = "github-desktop-chinese.zip"
$extractPath = "github-desktop-chinese-main"

Write-Host "Downloading from $repoUrl..." -ForegroundColor $Cyan

[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$client = New-Object System.Net.WebClient
$client.DownloadFile($downloadUrl, $zipPath)

Write-Host "Download completed" -ForegroundColor $Green
Log-Message "Download completed"

# Extract files
Write-Host ""
Write-Host "Extracting files..." -ForegroundColor $Cyan
Log-Message "Extracting files"

Add-Type -AssemblyName System.IO.Compression.FileSystem
[System.IO.Compression.ZipFile]::ExtractToDirectory($zipPath, ".", $true)

Write-Host "Extraction completed" -ForegroundColor $Green
Log-Message "Extraction completed"

# Apply localization
Write-Host ""
Write-Host "Applying Chinese localization..." -ForegroundColor $Cyan
Log-Message "Applying Chinese localization"

$patchScript = Join-Path $extractPath "patch.ps1"
$langPath = Join-Path $extractPath "app\resources\language"

if ($isPacked -and (Test-Path $patchScript)) {
    & $patchScript -AppAsarPath $appAsarPath
    Write-Host "Localization applied successfully" -ForegroundColor $Green
    Log-Message "Localization applied successfully"
}
elseif ($isUnpacked -and (Test-Path $langPath)) {
    # For unpacked format, copy language files directly
    $targetLangPath = Join-Path $appPath "resources\language"
    
    # Remove old language folder if exists
    if (Test-Path $targetLangPath) {
        Remove-Item -Path $targetLangPath -Recurse -Force -ErrorAction SilentlyContinue
    }
    
    Copy-Item -Path $langPath -Destination $targetLangPath -Recurse -Force
    Write-Host "Localization files copied successfully" -ForegroundColor $Green
    Log-Message "Localization files copied successfully"
}
elseif (Test-Path $langPath) {
    # Fallback: try to copy language resources
    $targetPath = Join-Path $foundPath "language"
    if (Test-Path $targetPath) {
        Remove-Item -Path $targetPath -Recurse -Force -ErrorAction SilentlyContinue
    }
    Copy-Item -Path $langPath -Destination $targetPath -Recurse -Force
    Write-Host "Localization resources applied (fallback method)" -ForegroundColor $Green
    Log-Message "Localization resources applied (fallback method)"
}
else {
    Write-Host "WARNING: Localization resources not found" -ForegroundColor $Yellow
    Write-Host "Please visit: $repoUrl" -ForegroundColor $Yellow
    Log-Message "WARNING: Localization resources not found"
}

# Cleanup
Write-Host ""
Write-Host "Cleaning up temporary files..." -ForegroundColor $Cyan
Log-Message "Cleaning up temporary files"

Remove-Item -Path $zipPath -Force -ErrorAction SilentlyContinue
Remove-Item -Path $extractPath -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "Cleanup completed" -ForegroundColor $Green
Log-Message "Cleanup completed"

# Complete
Write-Host ""
Write-Host "========================================"  -ForegroundColor $Green
Write-Host "Installation completed successfully!"  -ForegroundColor $Green
Write-Host "========================================"  -ForegroundColor $Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor $Cyan
Write-Host "1. Close GitHub Desktop completely"  -ForegroundColor $Cyan
Write-Host "2. Restart GitHub Desktop"  -ForegroundColor $Cyan
Write-Host "3. Verify that the interface is now in Chinese"  -ForegroundColor $Cyan
Write-Host ""
Write-Host "To restore original version: Run restore-original.ps1" -ForegroundColor $Yellow
Write-Host ""

Log-Message "Installation process completed"
Write-Host "Log saved to: logs/install.log" -ForegroundColor $Cyan

Read-Host "Press Enter to finish"
