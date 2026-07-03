# 详细安装指南

## 📋 前置要求

1. 已安装 GitHub Desktop
   - Windows: https://desktop.github.com/
   - macOS: https://desktop.github.com/

2. 管理员权限（Windows 需要；macOS 会在需要时提示输入密码）

3. 互联网连接（用于下载汉化补丁）

## 🪟 Windows 安装步骤

### 方式一：图形界面（推荐新手）

1. **下载本仓库**
   ```
   git clone https://github.com/wanghuohuo155-stack/huhuo.git
   cd huhuo
   ```

2. **右键点击 `install-chinese.ps1`**
   - 选择"用 PowerShell 运行"

3. **等待安装完成**
   - 脚本会自动进行所有操作
   - 查看彩色输出了解进度

### 方式二：命令行

1. **打开 PowerShell（管理员）**
   - 按 `Win + X`，选择"Windows PowerShell (管理员)"

2. **允许执行脚本**
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process -Force
   ```

3. **运行安装脚本**
   ```powershell
   .\install-chinese.ps1
   ```

### 完成后

1. **完全关闭 GitHub Desktop**
   - 从任务栏关闭
   - 按 Ctrl+Shift+Esc 打开任务管理器，确保没有后台进程

2. **重新启动 GitHub Desktop**

3. **验证汉化**
   - 检查菜单和界面是否已变为中文

## 🍎 macOS 安装步骤

### 方式一：快速安装

1. **下载本仓库**
   ```bash
   git clone https://github.com/wanghuohuo155-stack/huhuo.git
   cd huhuo
   ```

2. **运行安装脚本**
   ```bash
   bash install-chinese.sh
   ```

3. **输入密码**
   - 系统会提示输入 Mac 密码
   - 这是修改应用所需的权限

### 方式二：手动逐步

1. **打开终端** (Command + Space，输入 "Terminal")

2. **给脚本添加执行权限**
   ```bash
   chmod +x install-chinese.sh
   ```

3. **运行脚本**
   ```bash
   ./install-chinese.sh
   ```

### 完成后

1. **完全关闭 GitHub Desktop**
   - Command + Q 关闭应用
   - 或从 Dock 右键点击 → 退出

2. **重新启动 GitHub Desktop**

3. **验证汉化**
   - 检查菜单和界面是否已变为中文

## 🔄 恢复原始版本

如果需要恢复英文版本或遇到问题：

### Windows

1. **右键点击 `restore-original.ps1`**
   - 选择"用 PowerShell 运行"

2. **或在 PowerShell (管理员) 中运行**
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process -Force
   .\restore-original.ps1
   ```

3. **输入 `yes` 确认恢复**

### macOS

```bash
bash restore-original.sh
```

输入 `yes` 确认恢复

## ❓ 常见问题

### Q1: 脚本无法执行 (Windows)

**错误信息**: "无法加载文件 install-chinese.ps1，因为在此系统上禁止执行脚本"

**解决方案**:
```powershell
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope CurrentUser
.\install-chinese.ps1
```

### Q2: 需要管理员权限 (Windows/macOS)

**错误信息**: "需要管理员权限来运行此脚本"

**解决方案**:
- Windows: 以管理员身份运行 PowerShell
- macOS: 终端会自动提示输入密码

### Q3: 找不到 GitHub Desktop

**错误信息**: "未找到 GitHub Desktop 安装路径"

**解决方案**:
1. 确保已安装 GitHub Desktop
2. 使用官方安装程序完全卸载后重新安装
3. 确保安装在默认位置

### Q4: 汉化后仍然是英文

**可能原因**:
1. GitHub Desktop 未完全重启
2. 汉化补丁版本与 GitHub Desktop 版本不兼容
3. 安装过程中出错

**解决方案**:
1. 完全关闭 GitHub Desktop（包括后台进程）
2. 等待 2-3 分钟
3. 重新启动 GitHub Desktop
4. 如仍未解决，运行 `restore-original.ps1` 或 `restore-original.sh` 恢复，然后重试

### Q5: GitHub Desktop 更新后汉化失效

**原因**: GitHub Desktop 每次更新都会重置文件

**解决方案**:
- GitHub Desktop 更新后，再次运行 `install-chinese.ps1` 或 `install-chinese.sh`

### Q6: 如何查看安装日志？

日志文件位于 `logs/install.log`

```powershell
# Windows
Get-Content logs/install.log

# macOS
cat logs/install.log
```

## 🆘 仍需帮助？

1. **查看日志文件** - `logs/install.log` 中通常包含错误详情
2. **检查社区项目** - https://github.com/SkymAu/github-desktop-chinese
3. **提交 Issue** - 在本仓库提交问题

## ⚙️ 技术细节

### 脚本做了什么？

1. **检测** - 找到 GitHub Desktop 安装位置
2. **备份** - 创建 `app.asar.backup` 作为恢复点
3. **下载** - 从 GitHub 获取最新汉化补丁
4. **应用** - 将汉化资源应用到 `app.asar`
5. **清理** - 删除临时下载文件
6. **日志** - 记录所有操作到 `logs/install.log`

### 文件位置

- **Windows**: `C:\Users\{用户名}\AppData\Local\GitHubDesktop\app-*\resources\`
- **macOS**: `/Applications/GitHub Desktop.app/Contents/Resources/`

### 什么是 `app.asar`？

`app.asar` 是一个打包的应用资源文件，包含 GitHub Desktop 的用户界面和资源。汉化通过修改其中的语言文件来实现。

## 📝 许可

MIT License - 详见 LICENSE 文件