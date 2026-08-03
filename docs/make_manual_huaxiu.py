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
  /* 深墨编辑体：单一暖金主色 + 语义三色，其余全部靠明度层级 */
  --ink-900: #070A0F;
  --surface: #131A24;
  --surface-2: #0A0E15;
  --hair: rgba(255, 255, 255, .09);
  --hair-strong: rgba(255, 255, 255, .16);
  --text: #E9EEF5;
  --text-2: #C3CDDA;
  --text-3: #8D9BAC;
  --gold: #E7B341;
  --gold-2: #F2CE7A;
  --jade: #6FDCAB;
  --jade-ink: #ADEBCE;
  --coral: #FF8E7E;
  --coral-ink: #FFC0B6;
  --r-sm: 6px;
  --r-md: 14px;
  --r-lg: 22px;
  --dur: 180ms;
  --ease: cubic-bezier(.2, .7, .3, 1);
  --shell: 1320px;
}

* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  margin: 0;
  padding: 0 0 72px;
  background: var(--ink-900);
  color: var(--text-2);
  font-family: "PingFang SC", "Microsoft YaHei", "Noto Sans SC", system-ui, sans-serif;
  font-size: 16px;
  line-height: 1.7;
  overflow-x: hidden;
  min-height: 100vh;
  -webkit-font-smoothing: antialiased;
}

/* ——— 背景：极缓慢的极光 + 细网格，唯一的环境动效 ——— */
.bg { position: fixed; inset: 0; z-index: -1; overflow: hidden; background: var(--ink-900); }
.bg i {
  position: absolute;
  display: block;
  border-radius: 50%;
  filter: blur(88px);
  opacity: .62;
}
.bg .b1 { width: 780px; height: 780px; top: -280px; left: -160px; background: radial-gradient(circle, rgba(231,179,65,.28), transparent 68%); animation: drift1 46s ease-in-out infinite; }
.bg .b2 { width: 720px; height: 720px; top: 12%; right: -240px; background: radial-gradient(circle, rgba(90,140,255,.26), transparent 68%); animation: drift2 58s ease-in-out infinite; }
.bg .b3 { width: 640px; height: 640px; bottom: -220px; left: 28%; background: radial-gradient(circle, rgba(80,210,160,.18), transparent 70%); animation: drift3 66s ease-in-out infinite; }
.bg .grid {
  position: absolute;
  inset: 0;
  background-image: linear-gradient(var(--hair) 1px, transparent 1px), linear-gradient(90deg, var(--hair) 1px, transparent 1px);
  background-size: 96px 96px;
  opacity: .35;
  -webkit-mask-image: radial-gradient(ellipse 90% 60% at 50% 0%, #000 20%, transparent 78%);
  mask-image: radial-gradient(ellipse 90% 60% at 50% 0%, #000 20%, transparent 78%);
}
.bg .veil { position: absolute; inset: 0; background: linear-gradient(180deg, rgba(7,10,15,.42), rgba(7,10,15,.8) 60%, var(--ink-900)); }

@keyframes drift1 { 50% { transform: translate3d(90px, 60px, 0) scale(1.12); } }
@keyframes drift2 { 50% { transform: translate3d(-110px, 70px, 0) scale(1.08); } }
@keyframes drift3 { 50% { transform: translate3d(70px, -60px, 0) scale(1.14); } }

.progress {
  position: fixed;
  top: 0; left: 0;
  height: 2px;
  width: 0;
  z-index: 60;
  background: linear-gradient(90deg, var(--gold), var(--gold-2));
  box-shadow: 0 0 12px rgba(231, 179, 65, .55);
}

.skip {
  position: absolute;
  left: -9999px;
  top: 12px;
  z-index: 70;
  padding: 10px 18px;
  background: var(--gold);
  color: #17202B;
  font-weight: 700;
  border-radius: var(--r-sm);
  text-decoration: none;
}
.skip:focus { left: 16px; }

.shell { max-width: var(--shell); margin: 0 auto; padding: 0 32px; }

/* ——— Hero ——— */
.hero { padding: 96px 0 56px; }
.eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  font-family: "Cascadia Mono", Consolas, monospace;
  font-size: 12px;
  letter-spacing: .22em;
  color: var(--gold);
  margin: 0 0 22px;
}
.eyebrow::before {
  content: "";
  width: 34px;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--gold));
}
.hero h1 {
  margin: 0;
  font-family: Georgia, "Noto Serif SC", "Source Han Serif SC", "Songti SC", serif;
  font-size: clamp(36px, 6vw, 68px);
  line-height: 1.18;
  letter-spacing: .005em;
  font-weight: 600;
  color: var(--text);
}
.hero h1 em { font-style: normal; color: var(--gold); }
.hero .lead {
  margin: 24px 0 0;
  max-width: 40em;
  font-size: clamp(15.5px, 1.4vw, 18px);
  color: var(--text-2);
}
.meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px 28px;
  margin: 34px 0 0;
  padding: 20px 0 0;
  border-top: 1px solid var(--hair);
  font-family: "Cascadia Mono", Consolas, monospace;
  font-size: 12.5px;
  color: var(--text-3);
  letter-spacing: .04em;
}
.meta b { color: var(--text); font-weight: 600; }

/* ——— S0→S10 流程条 ——— */
.flow {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 40px 0 0;
}
.flow .node {
  display: inline-flex;
  align-items: baseline;
  gap: 8px;
  padding: 8px 14px;
  border: 1px solid var(--hair);
  border-radius: 999px;
  background: rgba(255, 255, 255, .028);
  color: var(--text-2);
  text-decoration: none;
  transition: border-color var(--dur) var(--ease), background var(--dur) var(--ease), transform var(--dur) var(--ease);
}
.flow .node b {
  font-family: "Cascadia Mono", Consolas, monospace;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: .06em;
  color: var(--gold);
}
.flow .node span { font-size: 13.5px; white-space: nowrap; }
.flow .node:hover { border-color: var(--gold); background: rgba(231, 179, 65, .09); transform: translateY(-2px); }
.flow .node:active { transform: translateY(0); }
.flow .node:focus-visible { outline: 2px solid var(--gold); outline-offset: 3px; }

/* ——— 卡片 ——— */
.pages {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(440px, 1fr));
  gap: 26px;
  padding: 56px 0 0;
}

.page {
  position: relative;
  padding: 28px 30px 30px;
  background: linear-gradient(160deg, rgba(255, 255, 255, .045), rgba(255, 255, 255, .012) 42%), var(--surface);
  border: 1px solid var(--hair);
  border-radius: var(--r-lg);
  box-shadow: 0 22px 50px rgba(0, 0, 0, .42);
  opacity: 0;
  transform: translateY(22px);
  transition: opacity .62s var(--ease), transform .62s var(--ease),
              border-color var(--dur) var(--ease), box-shadow var(--dur) var(--ease);
}
.page::before {
  content: "";
  position: absolute;
  left: 0;
  top: 30px;
  bottom: 30px;
  width: 2px;
  border-radius: 2px;
  background: linear-gradient(180deg, var(--gold), rgba(231, 179, 65, 0));
  opacity: .55;
  transition: opacity var(--dur) var(--ease);
}
.page.in { opacity: 1; transform: none; }
.page:hover {
  border-color: var(--hair-strong);
  box-shadow: 0 26px 60px rgba(0, 0, 0, .5);
}
.page:hover::before { opacity: 1; }

.page-top {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  align-items: start;
  gap: 16px;
  padding-bottom: 18px;
  margin-bottom: 20px;
  border-bottom: 1px solid var(--hair);
}
.page-top .num {
  font-family: Georgia, "Noto Serif SC", serif;
  font-size: 30px;
  line-height: 1;
  color: var(--gold);
  opacity: .82;
  font-variant-numeric: tabular-nums;
  padding-top: 4px;
}
.page-head { min-width: 0; }
.kicker {
  display: block;
  font-family: "Cascadia Mono", Consolas, monospace;
  font-size: 11.5px;
  letter-spacing: .18em;
  color: var(--text-3);
  margin-bottom: 6px;
}
.page-top h2 {
  margin: 0;
  font-family: Georgia, "Noto Serif SC", "Source Han Serif SC", "Songti SC", serif;
  font-size: 23px;
  font-weight: 600;
  line-height: 1.4;
  color: var(--text);
  letter-spacing: .01em;
}

.body p { margin: 0 0 5px; font-size: 16px; color: var(--text-2); }
.body p:last-child { margin-bottom: 0; }

/* ——— 命令窗 ——— */
.cmd {
  margin-top: 20px;
  background: var(--surface-2);
  border: 1px solid var(--hair);
  border-radius: var(--r-md);
  overflow: hidden;
}
.cmd-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px 12px;
  padding: 9px 12px;
  background: rgba(255, 255, 255, .035);
  border-bottom: 1px solid var(--hair);
}
.cmd-label {
  margin-right: auto;
  font-family: "Cascadia Mono", Consolas, monospace;
  font-size: 11.5px;
  letter-spacing: .1em;
  color: var(--text-3);
}
.copy-status { font-size: 12.5px; color: var(--gold-2); }
.cmd .copy {
  flex: 0 0 auto;
  padding: 5px 14px;
  font-family: "Cascadia Mono", Consolas, monospace;
  font-size: 12px;
  letter-spacing: .08em;
  color: var(--text);
  background: transparent;
  border: 1px solid var(--hair-strong);
  border-radius: var(--r-sm);
  cursor: pointer;
  transition: background var(--dur) var(--ease), color var(--dur) var(--ease), border-color var(--dur) var(--ease);
}
.cmd .copy:hover { background: var(--gold); border-color: var(--gold); color: #17202B; }
.cmd .copy:active { background: var(--gold-2); }
.cmd .copy:focus-visible { outline: 2px solid var(--gold); outline-offset: 2px; }
.cmd pre {
  margin: 0;
  padding: 15px 16px;
  white-space: pre-wrap;
  word-break: break-all;
  overflow-wrap: anywhere;
  font-family: "Cascadia Mono", Consolas, "Courier New", monospace;
  font-size: 13.5px;
  line-height: 1.72;
  color: #D6E2F2;
}

/* ——— 结果 / 报错 / 提示 ——— */
.bubbles { display: flex; flex-direction: column; gap: 8px; margin-top: 18px; }
.bubble {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  min-width: 0;
  padding: 10px 13px;
  border: 1px solid;
  border-radius: 12px;
  font-size: 14.5px;
  line-height: 1.65;
}
.bubble .mark {
  flex: 0 0 auto;
  padding: 1px 8px;
  border-radius: 999px;
  font-family: "Cascadia Mono", Consolas, monospace;
  font-size: 11px;
  letter-spacing: .1em;
  line-height: 1.75;
}
.bubble span:last-child { min-width: 0; overflow-wrap: anywhere; word-break: break-word; }
.bubble.ok { background: rgba(111, 220, 171, .07); border-color: rgba(111, 220, 171, .26); color: var(--jade-ink); }
.bubble.ok .mark { background: rgba(111, 220, 171, .16); color: var(--jade); }
.bubble.err { background: rgba(255, 142, 126, .07); border-color: rgba(255, 142, 126, .26); color: var(--coral-ink); }
.bubble.err .mark { background: rgba(255, 142, 126, .16); color: var(--coral); }
.bubble.tip { background: rgba(231, 179, 65, .07); border-color: rgba(231, 179, 65, .24); color: #EFD9A4; }
.bubble.tip .mark { background: rgba(231, 179, 65, .16); color: var(--gold-2); }

/* ——— 页脚与回顶 ——— */
footer {
  margin-top: 72px;
  padding-top: 28px;
  border-top: 1px solid var(--hair);
  font-size: 14px;
  color: var(--text-3);
}
footer p { margin: 0 0 8px; }
footer b { color: var(--text-2); font-weight: 600; }
footer a { color: var(--gold); text-decoration: none; border-bottom: 1px solid rgba(231, 179, 65, .4); }
footer a:hover { color: var(--gold-2); }
footer a:focus-visible { outline: 2px solid var(--gold); outline-offset: 3px; }

.back-top {
  position: fixed;
  right: 24px;
  bottom: 24px;
  z-index: 50;
  width: 46px;
  height: 46px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  border: 1px solid var(--hair-strong);
  background: var(--surface);
  color: var(--gold);
  font-size: 18px;
  text-decoration: none;
  box-shadow: 0 10px 30px rgba(0, 0, 0, .5);
  transition: transform var(--dur) var(--ease), border-color var(--dur) var(--ease), background var(--dur) var(--ease);
}
.back-top:hover { transform: translateY(-3px); border-color: var(--gold); background: rgba(231, 179, 65, .12); }
.back-top:active { transform: translateY(0); }
.back-top:focus-visible { outline: 2px solid var(--gold); outline-offset: 3px; }

@media (max-width: 1023px) {
  .shell { padding: 0 24px; }
  .pages { grid-template-columns: minmax(0, 1fr); gap: 22px; }
}

@media (max-width: 767px) {
  .shell { padding: 0 16px; }
  .hero { padding: 56px 0 36px; }
  .hero h1 { font-size: clamp(26px, 7.6vw, 34px); }
  .meta { gap: 8px 20px; }
  .pages { padding-top: 40px; }
  .page { padding: 22px 18px 22px 20px; border-radius: 18px; }
  .page-top { gap: 12px; padding-bottom: 14px; margin-bottom: 16px; }
  .page-top .num { font-size: 24px; }
  .page-top h2 { font-size: 19.5px; }
  .body p { font-size: 15.5px; }
  .cmd pre { font-size: 12.5px; padding: 13px 14px; }
  .bubble { font-size: 14px; }
  .flow .node { flex: 1 1 auto; justify-content: center; }
  .back-top { right: 14px; bottom: 14px; }
}

@media (prefers-reduced-motion: reduce) {
  html { scroll-behavior: auto; }
  .page { opacity: 1; transform: none; transition: none; }
  .bg i { animation: none; }
  .flow .node, .cmd .copy, .back-top, .page::before { transition: none; }
  .flow .node:hover, .back-top:hover { transform: none; }
}
"""


JS = r"""
(function () {
  var pages = document.querySelectorAll('.page');
  var prefersReduced = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  if (prefersReduced || !('IntersectionObserver' in window)) {
    pages.forEach(function (p) { p.classList.add('in'); });
  } else {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        var el = entry.target;
        var idx = Number(el.dataset.index || 0);
        el.style.transitionDelay = ((idx % 4) * 60) + 'ms';
        el.classList.add('in');
        io.unobserve(el);
      });
    }, { threshold: 0.06 });
    pages.forEach(function (p) { io.observe(p); });
  }

  var bar = document.querySelector('.progress');
  if (bar) {
    var tick = function () {
      var h = document.documentElement.scrollHeight - window.innerHeight;
      bar.style.width = (h > 0 ? Math.min(1, window.scrollY / h) * 100 : 0) + '%';
    };
    window.addEventListener('scroll', tick, { passive: true });
    window.addEventListener('resize', tick);
    tick();
  }

  document.querySelectorAll('.copy').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var status = btn.parentNode.querySelector('.copy-status');
      var done = function () {
        btn.textContent = '已复制';
        if (status) status.textContent = '去 PowerShell 里粘贴';
        setTimeout(function () {
          btn.textContent = '复制';
          if (status) status.textContent = '';
        }, 1800);
      };
      var fail = function () {
        if (status) status.textContent = '复制失败，请手动选中命令文字';
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
    cmd_count = sum(1 for p in PANELS if p.get("cmd"))
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="入世使用说明书：从一本书到一套可发布技能包，S0 到 S10 全流程逐条命令实测，照着敲就能跑通。">
<title>入世使用说明书 · 从一本书到一套技能</title>
<style>
{CSS}
</style>
</head>
<body>
<a class="skip" href="#main">跳到主要内容</a>
<div class="progress" aria-hidden="true"></div>
<div class="bg" aria-hidden="true">
  <i class="b1"></i><i class="b2"></i><i class="b3"></i>
  <div class="grid"></div><div class="veil"></div>
</div>
<div class="shell">
<header class="hero">
  <p class="eyebrow">RUSHI · 入世 · 操作手册</p>
  <h1>把一本书，<br>炼成一套<em>能干活的技能</em>。</h1>
  <p class="lead">从放进一本 txt，到产出一个证据齐全、通过安检的技能包。{len(PANELS)} 张卡片，一步一张，照着敲就行——每条命令都已实测跑通。</p>
  <p class="meta"><span><b>{len(PANELS)}</b> 张卡片</span><span><b>{cmd_count}</b> 条实测命令</span><span><b>S0 → S10</b> 全流程</span><span>最后实测 <b>2026-08-03</b></span></p>
  {flow_html()}
</header>
<main id="main" class="pages">
{cards}
</main>
<footer>
  <p>本手册每一条命令都按原样实测通过：<b>2026-08-03 · Python 3.14 · DeepSeek deepseek-chat</b>，全新项目 mybook 走完 S0→S10。</p>
  <p>卡壳了先翻「急救卡」，还不行就把红字原样发给 Codex。<a href="#cover">回到开头 ↑</a></p>
</footer>
</div>
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
