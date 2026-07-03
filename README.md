# GitHub Desktop 中文汉化安装器

一键安装 GitHub Desktop 中文汉化补丁的工具。

## 功能

- 自动下载最新的 GitHub Desktop 汉化补丁
- 一键应用汉化到本地 GitHub Desktop 安装
- 支持 Windows 和 macOS
- 备份原始文件以便恢复

## 快速开始

### Windows 用户

1. 确保已安装 GitHub Desktop（https://desktop.github.com/）
2. 下载本仓库
3. 右键点击 `install-chinese.ps1`，选择"用 PowerShell 运行"
4. 或在 PowerShell 中执行：
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process -Force
   .\install-chinese.ps1
   ```

### macOS 用户

1. 确保已安装 GitHub Desktop
2. 打开终端，执行：
   ```bash
   bash install-chinese.sh
   ```

## 使用说明

脚本会自动：
1. 检测 GitHub Desktop 安装路径
2. 备份原始的 `app.asar` 文件
3. 下载汉化资源
4. 应用汉化补丁
5. 重启 GitHub Desktop

## 恢复原始版本

- **Windows**: 运行 `restore-original.ps1`
- **macOS**: 运行 `bash restore-original.sh`

## 常见问题

**Q: 脚本运行出错怎么办？**
A: 检查是否有管理员权限，或查看 `logs/` 目录中的错误日志。

**Q: 每次更新 GitHub Desktop 后都需要重新汉化吗？**
A: 是的，建议在 GitHub Desktop 更新后再次运行汉化脚本。

**Q: 是否安全？**
A: 脚本会备份原始文件，如遇到问题可以快速恢复。

## 许可

MIT License