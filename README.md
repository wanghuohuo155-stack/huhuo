# 入世（rushi-skill）

自验证、可进化、面向真实效果的 Agent Skill 生产系统。

仓颉解决"把知识变成 skill"；入世解决更难的三件事：
**让 skill 自证可信（证据链）、可测效果（A/B 评测）、随真实使用而进化（遥测闭环）**。

## 项目结构

```text
rushi-skill/
├── PLAN.md                     # 终极目标、行动与落地方案（Fellow 视角）
├── rushi-skill/                # 「入世」skill 本体（自包含，可安装）
│   ├── SKILL.md                # meta-skill 定义（触发条件 + 工作流）
│   ├── agents/openai.yaml      # UI 元数据
│   ├── scripts/rushi-cli.py    # CLI 入口
│   ├── scripts/rushi/          # 引擎（Python 3.11+，stdlib-only）
│   │   ├── pipeline.py         # S0–S10 流水线状态机
│   │   ├── verifier.py         # S3 忠实度校验（引文定位 + 数字出处）
│   │   ├── builder.py          # S5 RIA++ 六段校验
│   │   ├── linker.py           # S6 关系链接 + INDEX
│   │   ├── evaluator.py        # S7 触发评测
│   │   ├── packager.py         # S8 打包 / S9 闸门
│   │   ├── installer.py        # Claude / Cursor / Codex 适配器
│   │   ├── evolve.py           # S10 遥测 -> 进化提案
│   │   └── prompts/            # LLM 阶段提示词（8 份）
│   ├── references/             # 流水线 / Schema / 评测 / 遥测文档
│   └── assets/templates/       # SKILL.md / pack.json / trigger.json 等模板
├── tests/                      # 125 个单元测试（unittest）
├── examples/                   # 演示包 + 示例遥测
└── .github/workflows/ci.yml    # 单测 + 端到端冒烟 + 发布闸门
```

## 环境要求

- Python 3.11+（仅标准库，无第三方依赖）

## 配置 LLM 钥匙

入世的 S1/S2/S4/S5 等阶段需要调用大模型，先配好钥匙（二选一）：

**方式 A：OpenAI**

```powershell
$env:OPENAI_API_KEY='你的钥匙'   # PowerShell
```

```bash
export OPENAI_API_KEY='你的钥匙'  # Linux / macOS
```

**方式 B：DeepSeek（国内用户推荐）**

```powershell
$env:DEEPSEEK_API_KEY='你的钥匙'
$env:RUSHI_BASE_URL='https://api.deepseek.com'
$env:RUSHI_MODEL='deepseek-chat'
$env:RUSHI_API_KEY_ENV='DEEPSEEK_API_KEY'
$env:RUSHI_JSON_MODE='1'
```

```bash
export DEEPSEEK_API_KEY='你的钥匙'                    # Linux / macOS
export RUSHI_BASE_URL='https://api.deepseek.com'
export RUSHI_MODEL='deepseek-chat'
export RUSHI_API_KEY_ENV='DEEPSEEK_API_KEY'
export RUSHI_JSON_MODE='1'
```

## 快速开始

```bash
# 1. 环境自检
python rushi-skill/scripts/rushi-cli.py doctor

# 2. 端到端演示（examples/demo-pack）
python rushi-skill/scripts/rushi-cli.py verify  --build examples/demo-pack --project .
python rushi-skill/scripts/rushi-cli.py check   --build examples/demo-pack --project .
python rushi-skill/scripts/rushi-cli.py link    --build examples/demo-pack --project . --title "慢园丁手记" --author "入世示例"
python rushi-skill/scripts/rushi-cli.py test    --build examples/demo-pack --project . --mode mock
python rushi-skill/scripts/rushi-cli.py package --build examples/demo-pack --project . --name demo-pack
python rushi-skill/scripts/rushi-cli.py gate    --pack packs/demo-pack

# 3. 进化闭环演示
python rushi-skill/scripts/rushi-cli.py evolve --project . --pack packs/demo-pack --telemetry examples/telemetry.jsonl
```

## 使用说明（小人书式图文版）

- [使用说明-花拳绣腿.html](docs/使用说明-花拳绣腿.html)（当前版本，浏览器直接打开即可阅读）
- [使用说明.html](docs/使用说明.html)（《你的名字》日式动漫版）
- 在线渲染版（GitHub Pages）：<https://wanghuohuo155-stack.github.io/huhuo/使用说明-花拳绣腿.html>

## 与仓颉的关键差异

| 维度 | 仓颉（cangjie-skill） | 入世（rushi-skill） |
|---|---|---|
| 引文溯源 | 标签式（只标章节） | 机器可验证（span 定位 + 哈希） |
| 数字事实 | 无强制出处 | 必须出现在引文或 source_note |
| 验证主体 | 同一模型自证 | 确定性校验器 + 外部三角验证 + 人工抽样 |
| 测试 | 测"会不会触发" | 触发评测 + 效果评测 + 生产遥测 |
| 发布 | 自检清单 | CI 自动化发布闸门（缺证据即失败） |
| 安装 | 单 skill 复制 | pack 级安装，GLOSSARY 随包嵌入防断链 |
| 生命周期 | 静态文件 | semver + freshness + 遥测进化闭环 |

## 测试

```bash
PYTHONPATH=rushi-skill/scripts python -m unittest discover -s tests -v
```

## 安装为 Codex skill（可选）

```bash
python rushi-skill/scripts/rushi-cli.py install --pack packs/demo-pack --host codex --scope user
```

或把 `rushi-skill/` 整个目录复制到 `$CODEX_HOME/skills/`（Windows 默认
`C:\Users\<you>\.codex\skills`）。

## 许可证

AGPL-3.0，详见 [LICENSE](LICENSE)。
