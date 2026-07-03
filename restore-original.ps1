# GitHub Desktop 恢复原始版本脚本 (Windows)
# 使用方法: 右键点击此文件选择"用 PowerShell 运行"

$ErrorActionPreference = "Stop"

# 颜色定义
$Green = [System.ConsoleColor]::Green
$Red = [System.ConsoleColor]::Red
$Yellow = [System.ConsoleColor]::Yellow
$Cyan = [System.ConsoleColor]::Cyan

function Write-ColorOutput {
    param(
        [string]$Message,
        [System.ConsoleColor]$Color = [System.ConsoleColor]::White
    )
    Write-Host $Message -ForegroundColor $Color
}

Write-ColorOutput "`n========================================" $Cyan
Write-ColorOutput "   GitHub Desktop 版本恢复工具" $Cyan
Write-ColorOutput "========================================`n" $Cyan

# 检查管理员权限
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-ColorOutput "⚠️  需要管理员权限来运行此脚本" $Yellow
    Write-ColorOutput "请以管理员身份运行 PowerShell 后重试" $Yellow
    exit 1
}

# 检测 GitHub Desktop 安装路径
Write-ColorOutput "🔍 检测 GitHub Desktop 安装路径..." $Cyan

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
    exit 1
}

Write-ColorOutput "✅ 找到 GitHub Desktop: $foundPath" $Green

$appAsarPath = Join-Path $foundPath "app.asar"
$appAsarBackup = Join-Path $foundPath "app.asar.backup"

# 检查备份文件
if (-not (Test-Path $appAsarBackup)) {
    Write-ColorOutput "❌ 未找到备份文件: $appAsarBackup" $Red
    Write-ColorOutput "无法恢复原始版本" $Red
    exit 1
}

Write-ColorOutput "✅ 找到备份文件" $Green

# 确认恢复
Write-ColorOutput "`n⚠️  确认要恢复原始版本吗?" $Yellow
$confirmation = Read-Host "请输入 'yes' 确认"

if ($confirmation -ne "yes") {
    Write-ColorOutput "❌ 恢复已取消" $Red
    exit 0
}

# 恢复文件
Write-ColorOutput "`n🔄 正在恢复原始文件..." $Cyan

try {
    Copy-Item -Path $appAsarBackup -Destination $appAsarPath -Force
    Write-ColorOutput "✅ 恢复完成" $Green
    
    Write-ColorOutput "`n💡 请完全关闭 GitHub Desktop 并重新启动" $Yellow
} catch {
    Write-ColorOutput "❌ 恢复失败: $_" $Red
    exit 1
}

Write-ColorOutput "`n========================================" $Green
Write-ColorOutput "✅ 恢复完成！" $Green
Write-ColorOutput "========================================`n" $Green