# GitHub Desktop 中文汉化安装脚本 (Windows)
# 使用方法: 右键点击此文件选择"用 PowerShell 运行"
# 或在 PowerShell 中执行: Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process -Force; .\install-chinese.ps1

param()

$ErrorActionPreference = "Stop"
$WarningPreference = "SilentlyContinue"

# 颜色定义
$Green = [System.ConsoleColor]::Green
$Red = [System.ConsoleColor]::Red
$Yellow = [System.ConsoleColor]::Yellow
$Cyan = [System.ConsoleColor]::Cyan

function Write-ColorOutput($Message, $Color = "White") {
    Write-Host $Message -ForegroundColor $Color
}

function Log-Message($Message) {
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Add-Content -Path "logs/install.log" -Value "[$timestamp] $Message"
}

if (-not (Test-Path "logs")) {
    New-Item -ItemType Directory -Path "logs" -Force | Out-Null
}

Write-ColorOutput "`n========================================" $Cyan
Write-ColorOutput "   GitHub Desktop 中文汉化安装器" $Cyan
Write-ColorOutput "========================================`n" $Cyan

Log-Message "开始安装过程"

# 检查管理员权限
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-ColorOutput "⚠️  需要管理员权限来运行此脚本" $Yellow
    Write-ColorOutput "请以管理员身份运行 PowerShell 后重试" $Yellow
    Log-Message "错误: 缺少管理员权限"
    Read-Host "按 Enter 退出"
    exit 1
}

# 检测 GitHub Desktop 安装路径
Write-ColorOutput "🔍 检测 GitHub Desktop 安装路径..." $Cyan
Log-Message "正在检测 GitHub Desktop 安装路径"

$githubDesktopPaths = @(
    "$env:LOCALAPPDATA\GitHubDesktop\app-*\resources",
    "$env:ProgramFiles\GitHub Desktop\resources",
    "C:\Users\$env:USERNAME\AppData\Local\GitHubDesktop\app-*\resources"
)

$foundPath = $null
foreach ($pattern in $githubDesktopPaths) {
    $paths = Get-Item -Path $pattern -ErrorAction SilentlyContinue
    if ($paths) {
        $foundPath = $paths[0].FullName
        break
    }
}

if (-not $foundPath) {
    Write-ColorOutput "❌ 未找到 GitHub Desktop 安装路径" $Red
    Write-ColorOutput "请确保已安装 GitHub Desktop: https://desktop.github.com/" $Red
    Log-Message "错误: 未找到 GitHub Desktop 安装路径"
    Read-Host "按 Enter 退出"
    exit 1
}

Write-ColorOutput "✅ 找到 GitHub Desktop: $foundPath" $Green
Log-Message "找到 GitHub Desktop: $foundPath"

$appAsarPath = Join-Path $foundPath "app.asar"
$appAsarBackup = Join-Path $foundPath "app.asar.backup"

if (-not (Test-Path $appAsarPath)) {
    Write-ColorOutput "❌ 未找到 app.asar 文件" $Red
    Log-Message "错误: 未找到 app.asar 文件"
    Read-Host "按 Enter 退出"
    exit 1
}

Write-ColorOutput "✅ 找到 app.asar 文件" $Green

# 备份原始文件
Write-ColorOutput "`n💾 备份原始文件..." $Cyan
Log-Message "正在备份原始文件"

if (Test-Path $appAsarBackup) {
    Write-ColorOutput "ℹ️  原始备份文件已存在，跳过备份" $Yellow
}
else {
    Copy-Item -Path $appAsarPath -Destination $appAsarBackup -Force
    Write-ColorOutput "✅ 备份完成: $appAsarBackup" $Green
    Log-Message "备份完成: $appAsarBackup"
}

# 下载汉化补丁
Write-ColorOutput "`n⬇️  下载汉化补丁..." $Cyan
Log-Message "正在下载汉化补丁"

$repoUrl = "https://github.com/SkymAu/github-desktop-chinese"
$downloadUrl = "https://github.com/SkymAu/github-desktop-chinese/archive/refs/heads/main.zip"
$zipPath = "github-desktop-chinese.zip"
$extractPath = "github-desktop-chinese-main"

Write-ColorOutput "正在从 $repoUrl 下载..." $Cyan

[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$client = New-Object System.Net.WebClient
$client.DownloadFile($downloadUrl, $zipPath)

Write-ColorOutput "✅ 下载完成" $Green
Log-Message "下载完成"

# 解压文件
Write-ColorOutput "`n📦 解压文件..." $Cyan
Log-Message "正在解压文件"

Add-Type -AssemblyName System.IO.Compression.FileSystem
[System.IO.Compression.ZipFile]::ExtractToDirectory($zipPath, ".", $true)

Write-ColorOutput "✅ 解压完成" $Green
Log-Message "解压完成"

# 应用汉化
Write-ColorOutput "`n🔧 应用汉化补丁..." $Cyan
Log-Message "正在应用汉化补丁"

$patchScript = Join-Path $extractPath "patch.ps1"
$langPath = Join-Path $extractPath "app\resources\language"

if (Test-Path $patchScript) {
    & $patchScript -AppAsarPath $appAsarPath
    Write-ColorOutput "✅ 汉化应用完成" $Green
    Log-Message "汉化应用完成"
}
elseif (Test-Path $langPath) {
    Copy-Item -Path $langPath -Destination (Join-Path $foundPath "language") -Recurse -Force
    Write-ColorOutput "✅ 汉化资源已应用" $Green
    Log-Message "汉化资源已应用（备用方案）"
}
else {
    Write-ColorOutput "⚠️  未找到汉化资源，请手动访问: $repoUrl" $Yellow
    Log-Message "警告: 未找到汉化资源"
}

# 清理下载文件
Write-ColorOutput "`n🧹 清理临时文件..." $Cyan
Log-Message "正在清理临时文件"

Remove-Item -Path $zipPath -Force -ErrorAction SilentlyContinue
Remove-Item -Path $extractPath -Recurse -Force -ErrorAction SilentlyContinue

Write-ColorOutput "✅ 清理完成" $Green
Log-Message "清理完成"

# 完成
Write-ColorOutput "`n========================================" $Green
Write-ColorOutput "✅ 汉化安装完成！" $Green
Write-ColorOutput "========================================" $Green
Write-ColorOutput "`n💡 下一步:" $Cyan
Write-ColorOutput "1. 完全关闭 GitHub Desktop（包括后台进程）" $Cyan
Write-ColorOutput "2. 重新启动 GitHub Desktop" $Cyan
Write-ColorOutput "3. 检查界面是否已变为中文" $Cyan
Write-ColorOutput "`n恢复原始版本: 运行 restore-original.ps1`n" $Yellow

Log-Message "安装过程完成"
Write-ColorOutput "日志已保存到: logs/install.log" $Cyan

Read-Host "按 Enter 完成"
