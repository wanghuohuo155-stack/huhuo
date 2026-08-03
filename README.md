<h1 align="center">入世 · rushi-skill</h1>

<p align="center">
  <b>把一本书、一门课、一段长内容，蒸馏成可验证、可测试、可进化的 Agent Skill。</b>
</p>

<p align="center">
  <a href="https://github.com/wanghuohuo155-stack/rushi-skill/actions"><img src="https://img.shields.io/github/actions/workflow/status/wanghuohuo155-stack/rushi-skill/ci.yml?branch=main&label=CI" alt="CI"></a>
  <img src="https://img.shields.io/badge/Python-3.11%2B-3776AB" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/Tests-125%20passed-2ea44f" alt="125 tests passed">
  <img src="https://img.shields.io/badge/Coverage-90%25-2ea44f" alt="coverage 90%">
  <img src="https://img.shields.io/badge/License-AGPL--3.0-orange" alt="AGPL-3.0">
</p>

---

仓颉解决「把知识变成 skill」；入世解决更难的三件事：

1. **自证可信** —— 每条方法都有机器可验证的引文证据链，假引文过不了闸门
2. **可测效果** —— 触发评测 + 效果 A/B 基线，不是"看起来能用"
3. **随使用进化** —— 遥测闭环驱动版本迭代，提案经人类审批后落地

## 快速开始

### 0. 环境要求

- Python 3.11+（仅标准库，无第三方依赖）

### 1. 配置 LLM 钥匙

入世的 S1/S2/S4/S5 等阶段需要调用大模型，二选一：

**OpenAI**

```powershell
$env:OPENAI_API_KEY='你的钥匙'   # PowerShell
```

```bash
export OPENAI_API_KEY='你的钥匙'  # Linux / macOS
```

**DeepSeek（国内用户推荐）**

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

### 2. 克隆并自检

```bash
git clone https://github.com/wanghuohuo155-stack/rushi-skill.git
cd rushi-skill
python rushi-skill/scripts/rushi-cli.py doctor   # 全部 ✅ 即环境就绪
```

### 3. 端到端演示（约 1 分钟）

```bash
python rushi-skill/scripts/rushi-cli.py verify  --build examples/demo-pack --project .
python rushi-skill/scripts/rushi-cli.py check   --build examples/demo-pack --project .
python rushi-skill/scripts/rushi-cli.py link    --build examples/demo-pack --project . --title "慢园丁手记" --author "入世示例"
python rushi-skill/scripts/rushi-cli.py test    --build examples/demo-pack --project . --mode mock
python rushi-skill/scripts/rushi-cli.py package --build examples/demo-pack --project . --name demo-pack
python rushi-skill/scripts/rushi-cli.py gate    --pack packs/demo-pack
```

### 4. 进化闭环演示

```bash
python rushi-skill/scripts/rushi-cli.py evolve --project . --pack packs/demo-pack --telemetry examples/telemetry.jsonl
```

### 5. 安装为 Codex skill（可选）

```bash
python rushi-skill/scripts/rushi-cli.py install --pack packs/demo-pack --host codex --scope user
```

或把 `rushi-skill/` 整个目录复制到 `$CODEX_HOME/skills/`（Windows 默认
`C:\Users\<you>\.codex\skills`），然后新开一个 Codex 对话即可触发。

## 流水线：S0 → S10

| 阶段 | 做什么 | 关键产物 | 闸门 |
|---|---|---|---|
| S0 | 放入书本 | `books/<slug>/source.txt` + 清单 | 源文件非空、元数据完整 |
| S1 | 读懂全书（Adler 方法） | `BOOK_OVERVIEW.md` | 整书理解地图 |
| S2 | 五路提取 | `candidates/*.json`（框架/原则/案例/反例/术语） | 每路 ≤20 条，引文 ≤150 字 |
| S3 | 引文真伪检查 | `claims.jsonl` | 引文逐字定位，fidelity 达标 |
| S4 | 外部验证 | `s4/*.json` 三角佐证 | 无佐证方法标记为低置信 |
| S5 | 构造技能 | `skills/*/SKILL.md` | RIA++ 六段结构校验 |
| S6 | 连线成图 | `INDEX.md` | 关系问题 0 |
| S7 | 考题考试 | `TEST_REPORT.md` | 诱饵 0 容忍，通过率 ≥80% |
| S8 | 打包 | `packs/<name>/pack.json` | 证据四件套齐全 |
| S9 | 安检放行 | 发布闸门 | TEST_REPORT 必须 PASS |
| S10 | 进化 | `proposals/*.md` | 人类审批后才落地 |

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

## 文档

- 📖 [使用说明-花拳绣腿.html](docs/使用说明-花拳绣腿.html)（小人书式图文教程，浏览器直接打开）
- 🎨 [使用说明.html](docs/使用说明.html)（《你的名字》日式动漫版）
- 🌐 [在线渲染版](https://wanghuohuo155-stack.github.io/rushi-skill/)（GitHub Pages）
- 📐 [PLAN.md](docs/PLAN.md)（终极目标、行动与落地方案）
- 📝 [CHANGELOG.md](CHANGELOG.md)（版本变更记录）

## 测试与验证

- 125 个单元测试（unittest）：`PYTHONPATH=rushi-skill/scripts python -m unittest discover -s tests -v`
- 最小可运行检查：`python check.py`
- 覆盖率 ≥80% 门禁（当前 90%）
- CI 矩阵：Python 3.11 / 3.12（GitHub Actions）
- 说明书四断点截图回归：375 / 768 / 1024 / 1440 零重叠

## 项目结构

```text
rushi-skill/
├── README.md                  # 本文件
├── CHANGELOG.md               # 版本变更
├── LICENSE                    # AGPL-3.0
├── rushi.json                 # 引擎配置（可移植，无本机路径）
├── check.py                   # 最小可运行检查
├── rushi-skill/               # 「入世」skill 本体（自包含，可安装）
│   ├── SKILL.md               # meta-skill 定义（触发条件 + 工作流）
│   ├── agents/openai.yaml     # UI 元数据
│   ├── scripts/rushi-cli.py   # CLI 入口
│   ├── scripts/rushi/         # 引擎（纯标准库）
│   ├── references/            # 流水线 / Schema / 评测 / 遥测文档
│   ├── assets/templates/      # SKILL.md / pack.json / trigger.json 模板
│   └── prompts/               # LLM 阶段提示词（8 份）
├── docs/                      # 使用说明（HTML + 生成器 + PLAN）
├── examples/                  # 演示包、评测数据、示例遥测
├── tests/                     # 125 个单元测试
└── .github/workflows/ci.yml   # CI：单测 + 冒烟 + 发布闸门
```

## 许可证

[AGPL-3.0](LICENSE)
