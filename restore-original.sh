#!/bin/bash

# GitHub Desktop 恢复原始版本脚本 (macOS)
# 使用方法: bash restore-original.sh

set -e

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}   GitHub Desktop 版本恢复工具${NC}"
echo -e "${CYAN}========================================${NC}\n"

# 检测 GitHub Desktop 安装路径
echo -e "${CYAN}🔍 检测 GitHub Desktop 安装路径...${NC}"

GITHUB_DESKTOP_PATH="/Applications/GitHub Desktop.app/Contents/Resources"

if [ ! -d "$GITHUB_DESKTOP_PATH" ]; then
    echo -e "${RED}❌ 未找到 GitHub Desktop 安装路径${NC}"
    exit 1
fi

echo -e "${GREEN}✅ 找到 GitHub Desktop: $GITHUB_DESKTOP_PATH${NC}"

APP_ASAR_PATH="$GITHUB_DESKTOP_PATH/app.asar"
APP_ASAR_BACKUP="$GITHUB_DESKTOP_PATH/app.asar.backup"

# 检查备份文件
if [ ! -f "$APP_ASAR_BACKUP" ]; then
    echo -e "${RED}❌ 未找到备份文件: $APP_ASAR_BACKUP${NC}"
    echo -e "${RED}无法恢复原始版本${NC}"
    exit 1
fi

echo -e "${GREEN}✅ 找到备份文件${NC}"

# 确认恢复
echo -e "\n${YELLOW}⚠️  确认要恢复原始版本吗?${NC}"
read -p "请输入 'yes' 确认: " confirmation

if [ "$confirmation" != "yes" ]; then
    echo -e "${RED}❌ 恢复已取消${NC}"
    exit 0
fi

# 恢复文件
echo -e "\n${CYAN}🔄 正在恢复原始文件...${NC}"

if sudo cp "$APP_ASAR_BACKUP" "$APP_ASAR_PATH"; then
    echo -e "${GREEN}✅ 恢复完成${NC}"
    echo -e "\n${YELLOW}💡 请完全关闭 GitHub Desktop 并重新启动${NC}"
else
    echo -e "${RED}❌ 恢复失败${NC}"
    exit 1
fi

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}✅ 恢复完成！${NC}"
echo -e "${GREEN}========================================${NC}\n"