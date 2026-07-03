# 🚀 快速开始指南

## 第一步：克隆仓库到本地

### Windows 用户

1. **打开 PowerShell (管理员)**
   - 按 `Win + X`，选择 "Windows PowerShell (管理员)"

2. **执行以下命令克隆仓库**
   ```powershell
   # 进入 D 盘（或其他你想放的位置）
   cd D:\
   
   # 克隆仓库
   git clone https://github.com/wanghuohuo155-stack/huhuo.git
   
   # 进入项目目录
   cd huhuo
   ```

3. **允许 PowerShell 执行脚本**
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process -Force
   ```

4. **运行安装脚本**
   ```powershell
   .\install-chinese.ps1
   ```

### macOS 用户

1. **打开终端**
   - Command + Space，输入 "Terminal"

2. **执行以下命令克隆仓库**
   ```bash
   # 克隆仓库
   git clone https://github.com/wanghuohuo155-stack/huhuo.git
   
   # 进入项目目录
   cd huhuo
   ```

3. **运行安装脚本**
   ```bash
   bash install-chinese.sh
   ```

---

## 第二步：等待安装完成

脚本会自动进行以下操作：
- 🔍 检测 GitHub Desktop 安装位置
- 💾 备份原始文件
- ⬇️ 下载汉化补丁
- 🔧 应用汉化
- 🧹 清理临时文件

看到 ✅ 绿色的 "汉化安装完成!" 提示时，说明成功了。

---

## 第三步：重启 GitHub Desktop

1. **完全关闭 GitHub Desktop**
   - 从任务栏/Dock 关闭
   - 或按 `Cmd + Q` (Mac) / `Alt + F4` (Windows)

2. **重新启动 GitHub Desktop**

3. **验证汉化是否成功**
   - 检查菜单是否已变为中文

---

## ⚠️ 如果脚本无法找到

**问题**: `.\install-chinese.ps1 is not recognized...`

**原因**: 你还没有进入包含脚本的目录

**解决方案**:
```powershell
# 确保你在正确的目录
cd D:\huhuo

# 确认脚本存在
ls *.ps1

# 然后运行
.\install-chinese.ps1
```

---

## 🔄 如何恢复原始版本？

如果需要恢复英文版本：

### Windows
```powershell
.\restore-original.ps1
```

### macOS
```bash
bash restore-original.sh
```

---

## 🛠️ 常用命令速查

| 命令 | 说明 |
|------|------|
| `cd huhuo` | 进入项目目录 |
| `ls` 或 `dir` | 查看文件列表 |
| `.\install-chinese.ps1` | 运行安装脚本 (Windows) |
| `bash install-chinese.sh` | 运行安装脚本 (macOS) |
| `Get-Content logs/install.log` | 查看安装日志 (Windows) |
| `cat logs/install.log` | 查看安装日志 (macOS) |

---

## 需要更多帮助？

- 📖 详细说明：查看 [INSTALLATION.md](./INSTALLATION.md)
- 📋 项目介绍：查看 [README.md](./README.md)
- 🐛 提交问题：https://github.com/wanghuohuo155-stack/huhuo/issues
