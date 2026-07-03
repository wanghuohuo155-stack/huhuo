#!/bin/bash

# GitHub Desktop 中文汉化安装脚本 (macOS)
# 使用方法: bash install-chinese.sh

set -e

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 日志函数
log_message() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" >> "logs/install.log"
}

# 创建日志目录
mkdir -p logs

echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}   GitHub Desktop 中文汉化安装器${NC}"
echo -e "${CYAN}========================================${NC}\n"

log_message "开始安装过程"

# 检测 GitHub Desktop 安装路径
echo -e "${CYAN}🔍 检测 GitHub Desktop 安装路径...${NC}"
log_message "正在检测 GitHub Desktop 安装路径"

# macOS 标准安装路径
GITHUB_DESKTOP_PATH="/Applications/GitHub Desktop.app/Contents/Resources"

if [ ! -d "$GITHUB_DESKTOP_PATH" ]; then
    echo -e "${RED}❌ 未找到 GitHub Desktop 安装路径${NC}"
    echo -e "${RED}请确保已安装 GitHub Desktop: https://desktop.github.com/${NC}"
    log_message "错误: 未找到 GitHub Desktop 安装路径"
    exit 1
fi

echo -e "${GREEN}✅ 找到 GitHub Desktop: $GITHUB_DESKTOP_PATH${NC}"
log_message "找到 GitHub Desktop: $GITHUB_DESKTOP_PATH"

APP_ASAR_PATH="$GITHUB_DESKTOP_PATH/app.asar"
APP_ASAR_BACKUP="$GITHUB_DESKTOP_PATH/app.asar.backup"

# 检查 app.asar 文件
if [ ! -f "$APP_ASAR_PATH" ]; then
    echo -e "${RED}❌ 未找到 app.asar 文件${NC}"
    log_message "错误: 未找到 app.asar 文件"
    exit 1
fi

echo -e "${GREEN}✅ 找到 app.asar 文件${NC}"

# 检查权限
if [ ! -w "$GITHUB_DESKTOP_PATH" ]; then
    echo -e "${YELLOW}⚠️  需要 sudo 权限来修改 GitHub Desktop${NC}"
    echo -e "${CYAN}请输入密码:${NC}"
    sudo -v
fi

# 备份原始文件
echo -e "\n${CYAN}💾 备份原始文件...${NC}"
log_message "正在备份原始文件"

if [ -f "$APP_ASAR_BACKUP" ]; then
    echo -e "${YELLOW}ℹ️  原始备份文件已存在，跳过备份${NC}"
else
    if sudo cp "$APP_ASAR_PATH" "$APP_ASAR_BACKUP"; then
        echo -e "${GREEN}✅ 备份完成: $APP_ASAR_BACKUP${NC}"
        log_message "备份完成: $APP_ASAR_BACKUP"
    else
        echo -e "${RED}❌ 备份失败${NC}"
        log_message "错误: 备份失败"
        exit 1
    fi
fi

# 下载汉化补丁
echo -e "\n${CYAN}⬇️  下载汉化补丁...${NC}"
log_message "正在下载汉化补丁"

REPO_URL="https://github.com/SkymAu/github-desktop-chinese"
DOWNLOAD_URL="https://github.com/SkymAu/github-desktop-chinese/archive/refs/heads/main.zip"
ZIP_PATH="github-desktop-chinese.zip"
EXTRACT_PATH="github-desktop-chinese-main"

if ! command -v curl &> /dev/null; then
    echo -e "${RED}❌ 缺少 curl 命令${NC}"
    log_message "错误: 缺少 curl 命令"
    exit 1
fi

echo -e "${CYAN}正在从 $REPO_URL 下载...${NC}"

if curl -L -o "$ZIP_PATH" "$DOWNLOAD_URL"; then
    echo -e "${GREEN}✅ 下载完成${NC}"
    log_message "下载完成"
else
    echo -e "${RED}❌ 下载失败${NC}"
    echo -e "${YELLOW}请手动访问: $REPO_URL${NC}"
    log_message "错误: 下载失败"
    exit 1
fi

# 解压文件
echo -e "\n${CYAN}📦 解压文件...${NC}"
log_message "正在解压文件"

if unzip -q "$ZIP_PATH" -d .; then
    echo -e "${GREEN}✅ 解压完成${NC}"
    log_message "解压完成"
else
    echo -e "${RED}❌ 解压失败${NC}"
    log_message "错误: 解压失败"
    exit 1
fi

# 应用汉化
echo -e "\n${CYAN}🔧 应用汉化补丁...${NC}"
log_message "正在应用汉化补丁"

# 检查是否有汉化脚本
if [ -f "$EXTRACT_PATH/patch.sh" ]; then
    if bash "$EXTRACT_PATH/patch.sh" "$APP_ASAR_PATH"; then
        echo -e "${GREEN}✅ 汉化应用完成${NC}"
        log_message "汉化应用完成"
    else
        echo -e "${RED}❌ 汉化应用失败${NC}"
        echo -e "${YELLOW}正在恢复原始文件...${NC}"
        sudo cp "$APP_ASAR_BACKUP" "$APP_ASAR_PATH"
        log_message "错误: 汉化应用失败，已恢复原始文件"
        exit 1
    fi
else
    # 备用方案：手动替换资源
    echo -e "${YELLOW}⚠️  未找到 patch.sh，尝试备用方案...${NC}"
    
    LANG_PATH="$EXTRACT_PATH/app/resources/language"
    if [ -d "$LANG_PATH" ]; then
        if sudo cp -r "$LANG_PATH" "$GITHUB_DESKTOP_PATH/language"; then
            echo -e "${GREEN}✅ 汉化资源已应用${NC}"
            log_message "汉化资源已应用（备用方案）"
        else
            echo -e "${RED}❌ 应用资源失败${NC}"
            log_message "错误: 应用资源失败"
            exit 1
        fi
    else
        echo -e "${YELLOW}⚠️  未找到汉化资源，请手动访问: $REPO_URL${NC}"
        log_message "警告: 未找到汉化资源"
    fi
fi

# 清理下载文件
echo -e "\n${CYAN}🧹 清理临时文件...${NC}"
log_message "正在清理临时文件"

rm -f "$ZIP_PATH"
rm -rf "$EXTRACT_PATH"
echo -e "${GREEN}✅ 清理完成${NC}"
log_message "清理完成"

# 完成
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}✅ 汉化安装完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "\n${CYAN}💡 下一步:${NC}"
echo -e "${CYAN}1. 完全关闭 GitHub Desktop（包括后台进程）${NC}"
echo -e "${CYAN}2. 重新启动 GitHub Desktop${NC}"
echo -e "${CYAN}3. 检查界面是否已变为中文${NC}"
echo -e "\n${YELLOW}恢复原始版本: bash restore-original.sh\n${NC}"

log_message "安装过程完成"
echo -e "${CYAN}日志已保存到: logs/install.log${NC}"