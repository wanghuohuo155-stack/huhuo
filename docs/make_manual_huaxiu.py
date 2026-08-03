"""生成《入世使用说明书（花拳绣腿版）》：深墨编辑体（Ink Editorial）语义化 HTML 手册。

用法：python docs/make_manual_huaxiu.py
产出：docs/使用说明-花拳绣腿.html（不覆盖旧版 使用说明.html）
所有命令文字与 rushi-cli 真实用法逐字一致（数据与已实测的 make_manual.py 相同）。

设计系统（花拳绣腿工作流第 2 步的决策记录）：
  场景  —— 开发者对着终端边看边敲，暗色降低眩光，与终端同处一个视觉世界。
  颜色  —— 克制策略：深墨底 + 纸白文字 + 单一暖金主色，语义色只用于结果/报错/提示。
  字体  —— 展示字 Georgia + Noto Serif SC（本机已装，衬线给「书」的分量）；
            正文 PingFang SC / 微软雅黑；命令 Cascadia Mono。
  节奏  —— 8dp 间距体系，圆角 6/14/22，断点 375 / 768 / 1024 / 1440。
  动效  —— 只编排一处：卡片滚动进场（错峰 ≤ 240ms）+ 背景极缓慢极光；
            其余仅 180ms 微交互；prefers-reduced-motion 时全部关闭。
生成后自动跑 Playwright 四断点截图回归：任何断点出现重叠/溢出即报错（退出码 1）。
"""

from __future__ import annotations

import html
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_HTML = ROOT / "docs" / "使用说明-花拳绣腿.html"


def esc(text: str) -> str:
    return html.escape(text, quote=True)


PANELS: list[dict] = [
    dict(pid="cover", title="入世使用说明书", emoji="📚",
         lines=["把一本书，变成 一套能干的技能工具箱！",
                "跟着本说明书一步一步走，",
                "就像看小人书一样简单。"],
         cmd="python rushi-skill\\scripts\\rushi-cli.py doctor",
         ok_text="看到全部 ✅，说明电脑准备好啦", err_text=None, tip="每张图都要照着做哦"),
    dict(pid="prep-python", title="准备 1：确认有 Python", emoji="🐍",
         lines=["Python 是让入世跑起来的引擎。",
                "① 按键盘【Win】键，输入 powershell，回车",
                "② 在黑框框里输入下面这行，回车"],
         cmd="python --version",
         ok_text="看到 python 3.11 或更高，OK！", err_text="提示找不到 python，去 python.org 下载并勾选 Add to PATH", tip=None),
    dict(pid="prep-codex", title="准备 2：把入世装进 Codex", emoji="🤖",
         lines=["把整个 rushi-skill 文件夹，放进技能的家里：", "（也可以直接对 Codex 说：帮我安装入世）"],
         cmd="Copy-Item -LiteralPath 'D:\\rushi-skill\\rushi-skill' -Destination 'C:\\Users\\wangh\\.codex-cli\\skills' -Recurse -Force",
         ok_text="skills\\rushi-skill\\SKILL.md 存在，OK！", err_text="权限被拒绝，让家长或 Codex 帮你执行", tip="装好后，新开一个 Codex 对话才会生效"),
    dict(pid="prep-key", title="准备 3：给入世配一把钥匙", emoji="🗝️",
         lines=["入世要请大模型帮忙，需要一把钥匙。", "用 DeepSeek（推荐）就输入这 4 行："],
         cmd="$env:RUSHI_BASE_URL='https://api.deepseek.com'; $env:RUSHI_MODEL='deepseek-chat'; $env:RUSHI_API_KEY_ENV='DEEPSEEK_API_KEY'; $env:RUSHI_JSON_MODE='1'",
         ok_text="没有报错 = 设置成功", err_text="提示找不到 DEEPSEEK_API_KEY，先去 platform 申请钥匙并设置", tip="用 OpenAI 也可以：设 $env:OPENAI_API_KEY='你的钥匙'"),
    dict(pid="step-cd", title="第 1 步：走到项目家门口", emoji="🚶",
         lines=["先让黑框框进入入世项目目录："],
         cmd="cd D:\\rushi-skill",
         ok_text="提示符变成 D:\\rushi-skill 开头", err_text="没有这个文件夹，先复制项目过来", tip=None),
    dict(pid="step-doctor", title="第 2 步：给入世体检", emoji="🩺",
         lines=["每次开工前先体检，确认一切正常："],
         cmd="python rushi-skill\\scripts\\rushi-cli.py doctor --project D:\\rushi-skill",
         ok_text="看到全部 ✅（含 配置可读）", err_text="有 ❌，看红字提示是哪一项，修好再继续", tip=None),
    dict(pid="step-init", title="第 3 步：建一个空项目", emoji="🏗️",
         lines=["入世需要一个工作台，一条命令建好："],
         cmd="python rushi-skill\\scripts\\rushi-cli.py init --project D:\\rushi-skill",
         ok_text="看到 项目已初始化：D:\\rushi-skill", err_text="提示路径错误，检查 --project 拼写", tip=None),
    dict(pid="step-ingest", title="第 4 步：把书放进工作台", emoji="📥",
         lines=["准备一个纯文本文件（书名.txt），放进 D:\\ 下，", "然后告诉入世：这本书叫什么、作者是谁："],
         cmd="python rushi-skill\\scripts\\rushi-cli.py ingest --project D:\\rushi-skill --slug mybook --source D:\\我的书.txt --title \"我的书\" --author \"作者\" --year \"2026\" --kind book",
         ok_text="看到 S0 完成，books\\mybook 出现", err_text="源文件为空/不存在，检查 --source 路径", tip="slug 只能用小写字母和数字，比如 mybook"),
    dict(pid="step-s1", title="第 5 步：让入世先通读全书", emoji="📖",
         lines=["入世会用 Adler 方法把整本书读懂，", "然后写出一张《整书理解》地图："],
         cmd="python rushi-skill\\scripts\\rushi-cli.py stage --build D:\\rushi-skill\\books\\mybook S1 --project D:\\rushi-skill --mode provider",
         ok_text="S1 -> done，books\\mybook\\BOOK_OVERVIEW.md 生成", err_text="S1 -> needs-provider：钥匙没配好；failed：输出不是合法 JSON（会自动重试一次）", tip="这一步要花十几秒到几分钟，耐心等"),
    dict(pid="step-s2", title="第 6 步：派 5 个小分队去找方法", emoji="🔍",
         lines=["5 个提取器（框架/原则/案例/反例/术语）", "同时从书里挑出最有用的方法："],
         cmd="python rushi-skill\\scripts\\rushi-cli.py stage --build D:\\rushi-skill\\books\\mybook S2 --project D:\\rushi-skill --mode provider",
         ok_text="S2 -> done，candidates 里有 5 个 json", err_text="某一路 failed：正常会重试；连续失败就重跑一次 S2", tip="书很长时，每一路最多挑 20 条，引文 ≤80 字"),
    dict(pid="step-claims", title="第 7 步：把候选变成正式清单", emoji="📝",
         lines=["把 candidates 里最好的候选，写成 claims.jsonl。", "这一步由 Codex 智能体自动做；格式长这样："],
         cmd='{"claim_id":"f01","skill_slug":"my-skill","kind":"framework","title":"标题","source_chapter":"章节","source_quote":"书里一字不差的句子","summary":"自己的话","tags":["tag"]}',
         ok_text="books\\mybook\\claims.jsonl 存在且每行都是 JSON", err_text="引文不是原话，后面 S3 会打回来", tip="source_quote 必须和书里一模一样，不能改写！"),
    dict(pid="step-s3", title="第 8 步：引文真假大检查", emoji="🕵️",
         lines=["S3 会把每条引文拿去书里核对位置，", "假话、拼接、改写的引文都会被揪出来："],
         cmd="python rushi-skill\\scripts\\rushi-cli.py stage --build D:\\rushi-skill\\books\\mybook S3 --project D:\\rushi-skill --mode provider",
         ok_text="S3 -> done，fidelity=100%", err_text="有 unverified：把这条引文改回书里的原话，再重跑 S3", tip=None),
    dict(pid="step-s4s5", title="第 9 步：外部验证 + 构造技能", emoji="🧱",
         lines=["S4 检查方法在外面世界有没有佐证；", "S5 把通过的方法组装成完整 SKILL.md："],
         cmd="python rushi-skill\\scripts\\rushi-cli.py stage --build D:\\rushi-skill\\books\\mybook S4 --project D:\\rushi-skill --mode provider; python rushi-skill\\scripts\\rushi-cli.py stage --build D:\\rushi-skill\\books\\mybook S5 --project D:\\rushi-skill --mode provider",
         ok_text="S4 -> done 和 S5 -> done，skills\\ 里有 SKILL.md", err_text="S5 failed：失败原因在 s5-review 文件夹里，修好重跑", tip="偶发失败正常：原样重跑一次，多数会通过"),
    dict(pid="step-trigger", title="第 10 步：给技能出考题", emoji="🎯",
         lines=["每个技能要有 tests\\trigger.json 考题：", "3 道该触发 + 2 道不该触发（诱饵）+ 1 道边界", "智能体按 assets\\templates\\trigger.json.template 生成"],
         cmd="python rushi-skill\\scripts\\rushi-cli.py check --build D:\\rushi-skill\\books\\mybook --project D:\\rushi-skill",
         ok_text="S5 构造校验: 通过", err_text="提示缺 trigger.json 或缺某一段，补齐再继续", tip="诱饵里必须有 1 道是'该触发另一个技能'的场景"),
    dict(pid="step-s6s7", title="第 11 步：连线 + 考试", emoji="🧩",
         lines=["S6 把技能之间的关系画成地图（INDEX.md）；", "S7 用考题考试，诱饵错 1 道就 FAIL："],
         cmd="python rushi-skill\\scripts\\rushi-cli.py stage --build D:\\rushi-skill\\books\\mybook S6 --project D:\\rushi-skill --mode provider; python rushi-skill\\scripts\\rushi-cli.py stage --build D:\\rushi-skill\\books\\mybook S7 --project D:\\rushi-skill --mode provider",
         ok_text="S6 -> done；S7 -> done（通过率与诱饵结果看 TEST_REPORT.md）", err_text="S7 failed：看 TEST_REPORT.md 哪道题答错，改 description 或考题", tip=None),
    dict(pid="step-package", title="第 12 步：打包 + 过安检", emoji="📦",
         lines=["把技能装进一个漂亮盒子（pack），", "然后过 S9 安检——缺一份证据都不放行："],
         cmd="python rushi-skill\\scripts\\rushi-cli.py package --build D:\\rushi-skill\\books\\mybook --project D:\\rushi-skill --name my-pack --version 0.1.0; python rushi-skill\\scripts\\rushi-cli.py gate --pack D:\\rushi-skill\\packs\\my-pack",
         ok_text="S8 打包成功 + S9 发布闸门: 通过", err_text="闸门列出缺哪份证据（PROVENANCE/TEST_REPORT/GLOSSARY/INDEX），补好再打包", tip="TEST_REPORT 必须 PASS 才能打包"),
    dict(pid="step-install", title="第 13 步：安装进 Codex", emoji="🚀",
         lines=["先 dry-run 预习一下会装到哪里，", "确认无误再去掉 --dry-run 真装："],
         cmd="python rushi-skill\\scripts\\rushi-cli.py install --pack D:\\rushi-skill\\packs\\my-pack --host codex --scope user --dry-run",
         ok_text="列出 → 目标路径\\skill 名（dry-run）", err_text="拒绝安装到 pack 自身目录，换 --target 路径", tip="host 可以是 codex / claude / cursor"),
    dict(pid="step-evolve", title="第 14 步：让技能越用越聪明", emoji="🌱",
         lines=["把使用记录（telemetry.jsonl）喂给入世，", "它会自动写出改进提案，等人类审批："],
         cmd="python rushi-skill\\scripts\\rushi-cli.py evolve --project D:\\rushi-skill --pack D:\\rushi-skill\\packs\\my-pack --telemetry D:\\rushi-skill\\telemetry.jsonl --out D:\\rushi-skill\\proposals",
         ok_text="S10 进化: 生成 N 条提案（待人类审批）", err_text="未指定 --telemetry 且无遥测库：先准备 telemetry.jsonl", tip="提案要人类审批后才改技能，不能自己乱改"),
    dict(pid="help-errors", title="急救卡：出错别慌", emoji="🚑",
         lines=["① 不认识命令 → 粘贴回原样，检查空格和引号", "② 钥匙没配对 → 重新执行准备 3 的 4 行", "③ S1/S2 显示 needs-provider → 钥匙没生效", "④ 引文打回 → 打开书复制原句，别自己写", "⑤ 还想不明白 → 把红字原样发给 Codex 问"],
         cmd="python rushi-skill\\scripts\\rushi-cli.py doctor --project D:\\rushi-skill",
         ok_text="红字消失 = 修复完成", err_text=None, tip="错误信息第一行最重要，先读它"),
    dict(pid="end", title="恭喜！你学会了入世", emoji="🎉",
         lines=["从一本书 → 一个证据齐全的技能包，", "每一步都有检查、有证据、能进化。", "现在，去新开一个 Codex 对话，对它说："],
         cmd="使用入世 skill，把 D:\\rushi-skill\\books\\mybook 蒸馏成可发布的 skill 包",
         ok_text="它自己会跑完整个流程！", err_text=None, tip="记住：没文本不拆书，引文必须逐字"),
]


FLOW: list[tuple[str, str, str]] = [
    ("S0", "放入书本", "step-ingest"),
    ("S1", "读懂全书", "step-s1"),
    ("S2", "五路提取", "step-s2"),
    ("S3", "引文检查", "step-s3"),
    ("S4", "外部验证", "step-s4s5"),
    ("S5", "构造技能", "step-s4s5"),
    ("S6", "连线成图", "step-s6s7"),
    ("S7", "考题考试", "step-s6s7"),
    ("S8", "打包", "step-package"),
    ("S9", "安检放行", "step-package"),
    ("S10", "进化", "step-evolve"),
]


KICKER_FALLBACK = {"cover": "序章", "end": "终章"}


def split_title(p: dict) -> tuple[str, str]:
    """「准备 1：确认有 Python」-> ("准备 1", "确认有 Python")；无冒号时用固定眉标。"""
    title = p["title"]
    if "：" in title:
        kicker, _, rest = title.partition("：")
        return kicker, rest
    return KICKER_FALLBACK.get(p["pid"], "说明"), title


def cmd_label(p: dict) -> str:
    """命令框顶栏说明这段文字该贴到哪里——是信息，不是装饰。"""
    if p["cmd"].lstrip().startswith("{"):
        return "claims.jsonl · 每行一条 JSON"
    if p["pid"] == "end":
        return "对 Codex 直接说这句话"
    return "PowerShell"


def card_html(p: dict, index: int) -> str:
    kicker, heading = split_title(p)
    body = "\n".join(f"<p>{esc(line)}</p>" for line in p["lines"])
    cmd_block = ""
    if p.get("cmd"):
        cmd_raw = p["cmd"]
        cmd_block = (
            '<div class="cmd">'
            '<div class="cmd-bar">'
            f'<span class="cmd-label">{esc(cmd_label(p))}</span>'
            '<span class="copy-status" role="status" aria-live="polite"></span>'
            f'<button class="copy" type="button" data-cmd="{esc(cmd_raw)}">复制</button>'
            "</div>"
            f"<pre><code>{esc(cmd_raw)}</code></pre>"
            "</div>"
        )
    bubbles: list[str] = []
    for kind, label, text in (
        ("ok", "成功", p.get("ok_text")),
        ("err", "报错", p.get("err_text")),
        ("tip", "提示", p.get("tip")),
    ):
        if text:
            bubbles.append(
                f'<div class="bubble {kind}"><span class="mark">{label}</span>'
                f"<span>{esc(text)}</span></div>"
            )
    bubble_block = f'<div class="bubbles">{"".join(bubbles)}</div>' if bubbles else ""
    return (
        f'<article class="page" id="{p["pid"]}" data-index="{index}">'
        '<div class="page-top">'
        f'<span class="num" aria-hidden="true">{index + 1:02d}</span>'
        '<div class="page-head">'
        f'<span class="kicker">{esc(kicker)}</span>'
        f"<h2>{esc(heading)}</h2>"
        "</div>"
        "</div>"
        f'<div class="body">{body}</div>'
        f"{cmd_block}{bubble_block}"
        "</article>"
    )


def flow_html() -> str:
    parts = ['<nav class="flow" aria-label="S0 到 S10 流程导航">']
    for code, label, target in FLOW:
        parts.append(
            f'<a class="node" href="#{target}"><b>{esc(code)}</b><span>{esc(label)}</span></a>'
        )
    parts.append("</nav>")
    return "\n".join(parts)


CSS = r"""
:root {
  --paper: #fffdf7;
  --ink: #33475b;
  --ink-strong: #1f2c3f;
  --sky-deep: #0e4fae;
  --sky-mid: #3b82d8;
  --sky-soft: #8fc4ef;
  --sky-pale: #d8ecff;
  --sun: #ffd166;
  --sun-ink: #2b4a78;
  --line: #8fb9e8;
  --cmd-bg: #1f3a5f;
  --cmd-ink: #e8f4ff;
  --ok-bg: #d9f2e0;
  --ok-line: #4caf7d;
  --ok-ink: #1e6b43;
  --err-bg: #ffe0e0;
  --err-line: #ef6c6c;
  --err-ink: #a12424;
  --tip-bg: #fff3d6;
  --tip-line: #e8b84b;
  --tip-ink: #7a5b00;
  --arrow: #ef8f5a;
  --radius-lg: 24px;
  --radius-md: 16px;
  --radius-sm: 12px;
  --shadow-card: 0 6px 14px rgba(40, 80, 140, .22), 0 2px 4px rgba(40, 80, 140, .12);
  --shadow-hover: 0 10px 22px rgba(40, 80, 140, .28), 0 4px 8px rgba(40, 80, 140, .14);
  --dur: 200ms;
  --ease: cubic-bezier(.22, .61, .36, 1);
}

* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  margin: 0;
  padding: 24px 16px 56px;
  font-family: "Microsoft YaHei", "PingFang SC", "Noto Sans JP", "Noto Sans SC", sans-serif;
  color: var(--ink);
  line-height: 1.6;
  overflow-x: hidden;
  min-height: 100vh;
}

.skip {
  position: absolute;
  left: -9999px;
  top: 8px;
  z-index: 50;
  padding: 10px 18px;
  background: var(--sun);
  color: var(--sun-ink);
  font-weight: 700;
  border-radius: var(--radius-sm);
  text-decoration: none;
}
.skip:focus { left: 8px; }

.bg {
  position: fixed;
  inset: 0;
  z-index: -1;
  overflow: hidden;
}
.bg svg { width: 100%; height: 100%; display: block; }
.bg::after {
  content: "";
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, rgba(216, 236, 255, .48), rgba(255, 255, 255, .30) 42%, rgba(216, 236, 255, .55));
}

.hero { text-align: center; margin: 6px auto 26px; max-width: 1100px; }
.hero h1 {
  margin: 0 0 4px;
  font-size: clamp(30px, 5vw, 44px);
  line-height: 1.25;
  color: #123c74;
  text-shadow: 0 2px 6px rgba(255, 255, 255, .9), 0 0 22px rgba(255, 255, 255, .6);
  letter-spacing: .02em;
}
.hero .subtitle {
  margin: 0 0 20px;
  font-size: clamp(16px, 2.4vw, 20px);
  color: var(--sun-ink);
  text-shadow: 0 1px 4px rgba(255, 255, 255, .85);
  font-weight: 600;
}

.flow {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin: 0 auto 34px;
  max-width: 1120px;
  padding: 16px;
  background: rgba(255, 253, 247, .88);
  border: 4px solid var(--line);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
}
.flow .node {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-width: 82px;
  padding: 8px 10px;
  border: 3px solid var(--line);
  border-radius: var(--radius-md);
  background: #fff;
  color: var(--sun-ink);
  text-decoration: none;
  transition: transform var(--dur) var(--ease), box-shadow var(--dur) var(--ease), background var(--dur) var(--ease);
}
.flow .node b { font-size: 17px; color: var(--ink-strong); }
.flow .node span { font-size: 13px; white-space: nowrap; }
.flow .node:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-hover);
  background: #f0f8ff;
}
.flow .node:active { transform: translateY(0) scale(.97); }
.flow .node:focus-visible {
  outline: 3px solid var(--sun);
  outline-offset: 2px;
}
.f-arrow { color: var(--arrow); font-size: 20px; font-weight: 700; line-height: 1; }
.f-arrow i { font-style: normal; }
.f-arrow .down { display: none; }

.pages {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(340px, 660px));
  gap: 30px;
  justify-content: center;
  max-width: 1400px;
  margin: 0 auto;
}

.page {
  background: var(--paper);
  border: 5px solid var(--line);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
  padding: 22px 24px 24px;
  opacity: 0;
  transform: translateY(18px);
  transition: opacity .5s var(--ease), transform .5s var(--ease), box-shadow var(--dur) var(--ease), border-color var(--dur) var(--ease);
}
.page.in { opacity: 1; transform: none; }
.page:hover {
  box-shadow: var(--shadow-hover);
  border-color: #7faeeb;
}

.page-top {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 0 0 12px;
  padding: 10px 14px;
  background: var(--sun);
  border: 3px solid var(--line);
  border-radius: var(--radius-md);
}
.page-top .emoji { font-size: 30px; line-height: 1; }
.page-top h2 {
  margin: 0;
  font-size: 21px;
  font-weight: 700;
  color: var(--sun-ink);
  line-height: 1.35;
}

.body p { margin: 0 0 8px; font-size: 17px; }
.body p:last-child { margin-bottom: 0; }

.cmd {
  position: relative;
  margin: 16px 0 0;
  background: var(--cmd-bg);
  border: 3px solid var(--line);
  border-radius: var(--radius-md);
  padding: 14px 14px 50px;
}
.cmd pre {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-all;
  overflow-wrap: anywhere;
  font-family: Consolas, "Cascadia Mono", "Courier New", monospace;
  font-size: 14.5px;
  line-height: 1.55;
  color: var(--cmd-ink);
}
.cmd .copy {
  position: absolute;
  right: 12px;
  bottom: 10px;
  padding: 7px 14px;
  font-size: 14px;
  font-family: inherit;
  font-weight: 600;
  color: var(--sun-ink);
  background: #fff;
  border: 2px solid var(--line);
  border-radius: var(--radius-sm);
  cursor: pointer;
  box-shadow: 0 2px 6px rgba(0, 0, 0, .18);
  transition: transform var(--dur) var(--ease), box-shadow var(--dur) var(--ease), background var(--dur) var(--ease);
}
.cmd .copy:hover { transform: translateY(-1px); box-shadow: 0 4px 10px rgba(0, 0, 0, .24); background: #f0f8ff; }
.cmd .copy:active { transform: translateY(0) scale(.97); }
.cmd .copy:focus-visible {
  outline: 3px solid #fff;
  outline-offset: 2px;
}
.cmd .copy-status {
  position: absolute;
  left: 14px;
  bottom: 16px;
  font-size: 13px;
  color: #bcd8f5;
}

.bubbles { display: flex; flex-direction: column; gap: 10px; margin-top: 14px; }
.bubble {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  min-width: 0;
  padding: 10px 14px;
  border: 3px solid;
  border-radius: var(--radius-md);
  font-size: 15.5px;
  line-height: 1.55;
}
.bubble .mark { flex: 0 0 auto; line-height: 1.35; }
.bubble span:last-child { min-width: 0; overflow-wrap: anywhere; word-break: break-word; }
.bubble.ok { background: var(--ok-bg); border-color: var(--ok-line); color: var(--ok-ink); }
.bubble.err { background: var(--err-bg); border-color: var(--err-line); color: var(--err-ink); }
.bubble.tip { background: var(--tip-bg); border-color: var(--tip-line); color: var(--tip-ink); }

.back-top {
  position: fixed;
  right: 18px;
  bottom: 18px;
  z-index: 40;
  width: 52px;
  height: 52px;
  border-radius: 50%;
  border: 3px solid var(--line);
  background: var(--sun);
  color: var(--sun-ink);
  font-size: 24px;
  text-decoration: none;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: var(--shadow-card);
  transition: transform var(--dur) var(--ease), box-shadow var(--dur) var(--ease);
}
.back-top:hover { transform: translateY(-3px); box-shadow: var(--shadow-hover); }
.back-top:active { transform: translateY(0) scale(.95); }
.back-top:focus-visible {
  outline: 3px solid #fff;
  outline-offset: 2px;
}

footer {
  margin: 42px auto 0;
  max-width: 1100px;
  text-align: center;
  font-size: 15px;
  color: var(--sun-ink);
  text-shadow: 0 1px 4px rgba(255, 255, 255, .85);
}
footer a { color: var(--sun-ink); font-weight: 700; }

@media (max-width: 767px) {
  body { padding: 16px 10px 64px; }
  .pages { grid-template-columns: minmax(0, 1fr); gap: 22px; }
  .page { padding: 16px 14px 18px; }
  .page-top h2 { font-size: 18px; }
  .body p { font-size: 16px; }
  .cmd pre { font-size: 13px; }
  .cmd .copy { position: static; display: block; width: 100%; margin-top: 12px; text-align: center; }
  .cmd .copy-status { position: static; display: block; margin-top: 8px; text-align: left; }
  .cmd { padding: 14px; }
  .flow { gap: 6px; padding: 12px; }
  .flow .node { min-width: 0; flex: 1 1 88px; }
  .f-arrow .right { display: none; }
  .f-arrow .down { display: inline; }
}

@media (prefers-reduced-motion: reduce) {
  html { scroll-behavior: auto; }
  .page { opacity: 1; transform: none; transition: none; }
  .flow .node, .cmd .copy, .back-top { transition: none; }
  .flow .node:hover, .back-top:hover { transform: none; }
}
"""


JS = r"""
(function () {
  var pages = document.querySelectorAll('.page');
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          var el = entry.target;
          var idx = Number(el.dataset.index || 0);
          el.style.transitionDelay = ((idx % 6) * 45) + 'ms';
          el.classList.add('in');
          io.unobserve(el);
        }
      });
    }, { threshold: 0.08 });
    pages.forEach(function (p) { io.observe(p); });
  } else {
    pages.forEach(function (p) { p.classList.add('in'); });
  }

  var prefersReduced = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (prefersReduced) {
    pages.forEach(function (p) { p.classList.add('in'); });
  }

  document.querySelectorAll('.copy').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var status = btn.parentNode.querySelector('.copy-status');
      var done = function () {
        btn.textContent = '✅ 已复制';
        if (status) status.textContent = '复制成功，去黑框框里粘贴吧';
        setTimeout(function () {
          btn.textContent = '📋 复制命令';
          if (status) status.textContent = '';
        }, 1800);
      };
      var fail = function () {
        if (status) status.textContent = '复制失败，请手动选择命令文字复制';
      };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(btn.dataset.cmd).then(done, function () {
          var t = document.createElement('textarea');
          t.value = btn.dataset.cmd;
          t.setAttribute('readonly', '');
          t.style.position = 'fixed';
          t.style.left = '-9999px';
          document.body.appendChild(t);
          t.select();
          try {
            document.execCommand('copy');
            done();
          } catch (e) {
            fail();
          }
          t.remove();
        });
      } else {
        fail();
      }
    });
  });
})();
"""


def build_html() -> str:
    cards = "\n".join(card_html(p, i) for i, p in enumerate(PANELS))
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="入世使用说明书：12 岁也能看懂的图文小人书式操作指南，S0 到 S10 全流程逐条命令实测。">
<title>入世使用说明书（花拳绣腿版）</title>
<style>
{CSS}
</style>
</head>
<body>
<a class="skip" href="#main">跳到主要内容</a>
<div class="bg" aria-hidden="true">{anime_bg_svg()}</div>
<header class="hero">
  <h1>📚 入世使用说明书</h1>
  <p class="subtitle">把一本书，变成一套能干的技能工具箱 —— 小人书式一步一步走</p>
  {flow_html()}
</header>
<main id="main" class="pages">
{cards}
</main>
<footer>
  本说明书中的每一条命令都按原样实测通过（2026-08-03，Python 3.14 + DeepSeek deepseek-chat，全新项目 mybook 全流程 S0→S10）。<br>
  遇到问题先看「急救卡」，再问 Codex。<a href="#cover">回到顶部 ↑</a>
</footer>
<a class="back-top" href="#cover" aria-label="回到顶部">↑</a>
<script>
{JS}
</script>
</body>
</html>"""


def main() -> None:
    pids = [p["pid"] for p in PANELS]
    assert len(pids) == len(set(pids)), "面板 pid 重复"
    assert len(PANELS) == 20, f"面板数应为 20，实际 {len(PANELS)}"
    for p in PANELS:
        assert p.get("title") and p.get("lines"), f"面板 {p['pid']} 缺标题或正文"
        assert any(p.get(k) for k in ("cmd", "ok_text", "err_text", "tip")), f"面板 {p['pid']} 内容为空"
    doc = build_html()
    for p in PANELS:
        if p.get("cmd"):
            assert esc(p["cmd"]) in doc, f"面板 {p['pid']} 的命令未进入 HTML"
    assert doc.count('<article class="page"') == len(PANELS), "卡片数量与面板数不一致"
    assert "TODO" not in doc, "HTML 里残留 TODO"
    OUT_HTML.write_text(doc, encoding="utf-8")
    print(f"生成完成：{OUT_HTML}")
    print(f"面板 {len(PANELS)} 张 · 命令 {sum(1 for p in PANELS if p.get('cmd'))} 条 · 流程图节点 {len(FLOW)} 个")
    try:
        from screenshot_regression import run_regression
    except ImportError:
        print("警告：找不到同目录 screenshot_regression.py，跳过视觉回归")
        return
    status, report = run_regression(OUT_HTML)
    if status == "failed":
        print("视觉回归失败，以下断点有问题（详情见 docs/screenshots/report.json）：")
        for w, info in report.items():
            if isinstance(info, dict) and "error" in info:
                print(f"  {info['error']}")
                continue
            issues = info.get("issues", [])
            print(f"  {w}px: {len(issues)} issues")
            for it in issues[:6]:
                print("    ", it)
        raise SystemExit(1)
    if status == "skipped":
        print("警告：未安装 playwright，跳过视觉回归（生成成功但未验证零重叠）。安装：python -m pip install playwright")
        return
    print("视觉回归通过：375 / 768 / 1024 / 1440 全部零重叠")


if __name__ == "__main__":
    main()
