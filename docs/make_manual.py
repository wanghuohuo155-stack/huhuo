"""生成《入世使用说明书》：SVG 小人书面板 + 自包含 HTML（宫崎骏/新海诚日式动漫风）。

用法：python docs/make_manual.py
产出：docs/使用说明.html（主文档）、docs/images/panel-*.svg
所有命令文字与 rushi-cli 真实用法逐字一致（经实测验证）。
布局：文本自动换行，面板高度按内容自适应，杜绝文字重叠。
"""

from __future__ import annotations

import html
import random
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_HTML = ROOT / "docs" / "使用说明.html"
IMG_DIR = ROOT / "docs" / "images"

W = 660
BG = "#eaf6ff"      # 面板外底色（浅天空蓝）
PANEL = "#ffffff"   # 卡片白
TEXT = "#33475b"    # 正文深蓝灰
TITLE_TEXT = "#2b4a78"
LINE = "#8fb9e8"    # 柔和蓝描边
TITLE_FILL = "#ffd166"  # 暖黄标题条
CMD_BG = "#1f3a5f"
CMD_TEXT = "#e8f4ff"
OK_FILL, OK_STROKE, OK_TEXT = "#d9f2e0", "#4caf7d", "#1e6b43"
ERR_FILL, ERR_STROKE, ERR_TEXT = "#ffe0e0", "#ef6c6c", "#a12424"
TIP_FILL, TIP_STROKE, TIP_TEXT = "#fff3d6", "#e8b84b", "#7a5b00"
ARROW = "#ef8f5a"


def esc(text: str) -> str:
    return html.escape(text, quote=True)


def wrap(text: str, font_size: int, max_width: int, mono: bool = False) -> list[str]:
    """按估算字符宽度换行，保证单行不溢出面板。"""
    unit = font_size * (0.62 if mono else 1.0)
    per_line = max(1, int(max_width // unit))
    out: list[str] = []
    for raw in text.split("\n"):
        cur = ""
        for ch in raw:
            if len(cur) >= per_line:
                out.append(cur)
                cur = ""
            cur += ch
        out.append(cur)
    return out or [""]


def svg_panel(
    pid: str,
    title: str,
    emoji: str,
    lines: list[str],
    cmd: str | None,
    ok_text: str | None,
    err_text: str | None,
    tip: str | None,
) -> str:
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="PLACEHOLDER" viewBox="0 0 {W} PLACEHOLDER">',
        f'<rect x="6" y="6" width="{W-12}" height="PLACEHOLDER-12" rx="26" fill="{BG}" stroke="{LINE}" stroke-width="5"/>',
    ]
    cursor = 26
    # 标题栏
    parts.append(
        f'<rect x="24" y="{cursor}" width="{W-48}" height="56" rx="16" fill="{TITLE_FILL}" stroke="{LINE}" stroke-width="4"/>'
        f'<text x="40" y="{cursor+37}" font-size="30" font-weight="bold" fill="{TITLE_TEXT}">{esc(title)}</text>'
        f'<text x="{W-56}" y="{cursor+40}" font-size="38">{emoji}</text>'
    )
    cursor += 68
    # 正文（自动换行）
    for line in lines:
        for wl in wrap(line, 22, 560):
            parts.append(f'<text x="40" y="{cursor+24}" font-size="22" fill="{TEXT}">{esc(wl)}</text>')
            cursor += 31
    cursor += 6
    # 命令框（自动换行 + 动态高度）
    if cmd:
        cmd_lines = wrap(cmd, 19, 540, mono=True)
        box_h = 18 + len(cmd_lines) * 27
        parts.append(
            f'<rect x="40" y="{cursor}" width="{W-80}" height="{box_h}" rx="12" fill="{CMD_BG}" stroke="{LINE}" stroke-width="3"/>'
        )
        for i, wl in enumerate(cmd_lines):
            parts.append(
                f'<text x="56" y="{cursor+27+i*27}" font-size="19" fill="{CMD_TEXT}" font-family="Consolas,monospace">{esc(wl)}</text>'
            )
        cursor += box_h + 10
    # 结果气泡（自动换行 + 动态高度）
    for text, fill, stroke, color in (
        (ok_text, OK_FILL, OK_STROKE, OK_TEXT),
        (err_text, ERR_FILL, ERR_STROKE, ERR_TEXT),
        (tip, TIP_FILL, TIP_STROKE, TIP_TEXT),
    ):
        if not text:
            continue
        bubbles = wrap(text, 18, 540)
        bubble_h = 16 + len(bubbles) * 25
        parts.append(
            f'<rect x="40" y="{cursor}" width="{W-80}" height="{bubble_h}" rx="18" fill="{fill}" stroke="{stroke}" stroke-width="3"/>'
        )
        for i, wl in enumerate(bubbles):
            parts.append(f'<text x="58" y="{cursor+25+i*25}" font-size="18" fill="{color}">{esc(wl)}</text>')
        cursor += bubble_h + 10
    height = cursor + 14
    return "\n".join(parts).replace("PLACEHOLDER", str(height))


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


def flow_svg() -> str:
    nodes = [("S0", "放入书本"), ("S1", "读懂全书"), ("S2", "五路提取"), ("S3", "引文检查"),
             ("S4", "外部验证"), ("S5", "构造技能"), ("S6", "连线成图"), ("S7", "考题考试"),
             ("S8", "打包"), ("S9", "安检放行"), ("S10", "进化")]
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="1120" height="220" viewBox="0 0 1120 220">',
        f'<rect x="4" y="4" width="1112" height="212" rx="20" fill="{BG}" stroke="{LINE}" stroke-width="5"/>',
        '<defs><marker id="ar" markerWidth="9" markerHeight="9" refX="8" refY="3" '
        'orient="auto" markerUnits="userSpaceOnUse" viewBox="0 0 9 9">'
        '<path d="M0,0 L8,3.5 L0,7 Z" fill="%s"/></marker></defs>' % ARROW,
    ]
    for i, (code, label) in enumerate(nodes):
        x = 18 + i * 100
        parts.append(
            f'<rect x="{x}" y="60" width="88" height="56" rx="14" fill="{PANEL}" stroke="{LINE}" stroke-width="3"/>'
            f'<text x="{x+44}" y="86" font-size="16" font-weight="bold" text-anchor="middle" fill="{TITLE_TEXT}">{esc(code)}</text>'
            f'<text x="{x+44}" y="106" font-size="14" text-anchor="middle" fill="{TEXT}">{esc(label)}</text>'
        )
        if i < len(nodes) - 1:
            parts.append(
                f'<line x1="{x+89}" y1="88" x2="{x+98}" y2="88" stroke="{ARROW}" stroke-width="3" marker-end="url(#ar)"/>'
            )
    parts.append("</svg>")
    return "\n".join(parts)


def anime_bg_svg() -> str:
    """《你的名字》式日式动漫场景：澄蓝天空、积云、远山、城市、丘陵、池塘、鸟居。"""
    rng = random.Random(20260803)
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1440" height="900" viewBox="0 0 1440 900" preserveAspectRatio="xMidYMid slice">',
        "<defs>",
        '<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">',
        '<stop offset="0" stop-color="#0e4fae"/>',
        '<stop offset=".45" stop-color="#3b82d8"/>',
        '<stop offset=".78" stop-color="#8fc4ef"/>',
        '<stop offset="1" stop-color="#d8ecff"/>',
        "</linearGradient>",
        '<filter id="soft"><feGaussianBlur stdDeviation="3"/></filter>',
        '<filter id="soft2"><feGaussianBlur stdDeviation="9"/></filter>',
        "</defs>",
        '<rect x="0" y="0" width="1440" height="900" fill="url(#sky)"/>',
        # 太阳光晕
        '<circle cx="1110" cy="150" r="130" fill="#fff7d6" opacity=".5" filter="url(#soft2)"/>',
        '<circle cx="1110" cy="150" r="64" fill="#fffbe8" opacity=".85"/>',
    ]
    # 高空细云
    for _ in range(9):
        x = rng.uniform(0, 1440)
        y = rng.uniform(70, 300)
        length = rng.uniform(90, 260)
        parts.append(
            f'<line x1="{x:.0f}" y1="{y:.0f}" x2="{x+length:.0f}" y2="{y+18:.0f}" '
            f'stroke="#ffffff" stroke-width="{rng.uniform(2,5):.1f}" stroke-linecap="round" opacity="{rng.uniform(.35,.6):.2f}"/>'
        )
    # 大团积云（多层椭圆，底部淡蓝阴影）
    for _ in range(7):
        cx = rng.uniform(120, 1320)
        cy = rng.uniform(180, 470)
        s = rng.uniform(0.8, 1.5)
        parts.append(f'<ellipse cx="{cx:.0f}" cy="{cy+8:.0f}" rx="{95*s:.0f}" ry="{26*s:.0f}" fill="#ffffff" opacity=".95" filter="url(#soft)"/>')
        puffs = []
        for _ in range(rng.randint(5, 7)):
            px = cx + rng.uniform(-70, 70) * s
            py = cy + rng.uniform(-26, 10) * s
            rx = rng.uniform(32, 60) * s
            ry = rng.uniform(20, 32) * s
            puffs.append((px, py, rx, ry))
            parts.append(f'<ellipse cx="{px:.0f}" cy="{py:.0f}" rx="{rx:.0f}" ry="{ry:.0f}" fill="#ffffff" opacity=".98" filter="url(#soft)"/>')
        for px, py, rx, ry in puffs[1:4]:
            parts.append(
                f'<ellipse cx="{px:.0f}" cy="{py+ry*0.55:.0f}" rx="{rx*0.9:.0f}" ry="{ry*0.5:.0f}" '
                f'fill="#cfe6ff" opacity=".85" filter="url(#soft)"/>'
            )
    # 远山（两层，大气透视）
    parts.append(
        '<path d="M0,500 Q180,442 360,500 T720,470 T1080,500 T1440,470 L1440,560 L0,560 Z" fill="#9db8dc" opacity=".9"/>'
        '<path d="M0,560 Q240,500 520,560 T1000,530 T1440,560 L1440,660 L0,660 Z" fill="#6f8fc0" opacity=".95"/>'
    )
    # 城市天际线（东京式：塔楼+天线）
    x = -10
    while x < 1450:
        w = rng.randint(42, 82)
        h = rng.randint(120, 250)
        parts.append(f'<rect x="{x}" y="{660-h}" width="{w}" height="{h}" fill="#5d7090"/>')
        for _ in range(int(w * h / 700)):
            wx = x + rng.randint(4, w - 8)
            wy = 660 - h + rng.randint(4, h - 10)
            color = rng.choice(["#ffd9a0", "#cfe8ff", "#ffe9c9"])
            parts.append(f'<rect x="{wx}" y="{wy}" width="3" height="5" fill="{color}" opacity="{rng.uniform(.35,.75):.2f}"/>')
        x += w + rng.randint(0, 6)
    parts.append(
        '<rect x="380" y="360" width="42" height="300" fill="#57688c"/>'
        '<rect x="1018" y="330" width="54" height="330" fill="#54668c"/>'
        '<line x1="1045" y1="330" x2="1045" y2="280" stroke="#54668c" stroke-width="4"/>'
        '<line x1="1045" y1="280" x2="1062" y2="260" stroke="#54668c" stroke-width="4"/>'
        '<rect x="730" y="420" width="34" height="240" fill="#5a6c92"/>'
    )
    # 地平线薄雾
    parts.append('<rect x="0" y="588" width="1440" height="86" fill="#d8ecff" opacity=".55"/>')
    # 前景丘陵
    parts.append(
        '<path d="M0,760 Q300,690 640,760 T1440,730 L1440,900 L0,900 Z" fill="#8fce8f"/>'
        '<path d="M0,820 Q360,740 760,820 T1440,800 L1440,900 L0,900 Z" fill="#6db96f"/>'
        '<path d="M0,900 Q500,820 1000,900 L1440,900 Z" fill="#4e9a5a"/>'
    )
    # 池塘与天空倒影
    parts.append('<ellipse cx="240" cy="856" rx="150" ry="26" fill="#5da263"/>')
    parts.append('<ellipse cx="240" cy="850" rx="170" ry="34" fill="#8fc4ef" opacity=".97"/>')
    for _ in range(6):
        bx = rng.uniform(110, 370)
        parts.append(f'<ellipse cx="{bx:.0f}" cy="{rng.uniform(838,860):.0f}" rx="{rng.uniform(10,26):.0f}" ry="4" fill="#ffffff" opacity=".55"/>')
    # 树木
    for tx, ty, s in ((90, 760, 1.1), (700, 780, 1.0), (1010, 800, 0.9), (1340, 770, 1.15), (470, 800, 0.85)):
        parts.append(f'<rect x="{tx:.0f}" y="{ty:.0f}" width="8" height="24" fill="#6b4a2f"/>')
        parts.append(f'<circle cx="{tx+4:.0f}" cy="{ty-16:.0f}" r="{34*s:.0f}" fill="#3f7f52"/>')
        parts.append(f'<circle cx="{tx-14:.0f}" cy="{ty-6:.0f}" r="{22*s:.0f}" fill="#356e46"/>')
        parts.append(f'<circle cx="{tx+22:.0f}" cy="{ty-8:.0f}" r="{20*s:.0f}" fill="#4a8f5c"/>')
    # 红色鸟居
    parts.append(
        '<rect x="1176" y="782" width="16" height="76" rx="4" fill="#d8452f"/>'
        '<rect x="1242" y="782" width="16" height="76" rx="4" fill="#d8452f"/>'
        '<rect x="1164" y="770" width="106" height="14" rx="6" fill="#d8452f"/>'
        '<rect x="1172" y="792" width="90" height="9" rx="4" fill="#d8452f"/>'
        '<rect x="1204" y="780" width="26" height="14" rx="3" fill="#d8452f"/>'
    )
    # 飞鸟
    for _ in range(5):
        bx = rng.uniform(180, 900)
        by = rng.uniform(200, 330)
        parts.append(
            f'<path d="M{bx:.0f},{by:.0f} q6,-5 12,0 q6,-5 12,0" stroke="#33475b" stroke-width="2.5" fill="none" opacity=".8"/>'
        )
    parts.append("</svg>")
    return "\n".join(parts)


def build_html() -> str:
    cards = []
    for p in PANELS:
        svg = svg_panel(**p)
        copy_html = (
            f'<button class="copy" data-cmd="{esc(p["cmd"])}">📋 复制命令</button>'
            if p.get("cmd")
            else ""
        )
        cards.append(f'<section class="page" id="{p["pid"]}">{svg}{copy_html}</section>')
    body = "\n".join(cards)
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>入世使用说明书（日式动漫小人书版）</title>
<style>
  body {{
    margin:0; padding:28px;
    font-family:"Microsoft YaHei","PingFang SC",sans-serif;
    color:{TEXT};
    background-color:#bfe0ff;
  }}
  .bg {{ position:fixed; top:0; left:0; width:100vw; height:100vh; z-index:-1; overflow:hidden; }}
  .bg svg {{ width:100%; height:100%; display:block; }}
  h1, .flow, .pages, footer {{ position:relative; z-index:1; }}
  h1 {{
    text-align:center; font-size:40px; margin:8px 0 22px 0; color:#123c74;
    text-shadow:0 2px 6px rgba(255,255,255,.85), 0 0 22px rgba(255,255,255,.55);
  }}
  .flow {{ display:block; margin:0 auto 30px auto; max-width:1120px;
           filter:drop-shadow(0 6px 14px rgba(40,80,140,.22)); }}
  .pages {{ max-width:1400px; margin:0 auto; display:flex; flex-wrap:wrap; gap:30px; justify-content:center; }}
  .page {{ flex:0 1 680px; }}
  .page svg {{ width:100%; height:auto; display:block;
               filter:drop-shadow(0 6px 14px rgba(40,80,140,.22)); }}
  .copy {{
    display:block; margin:10px auto 0 auto; padding:8px 18px;
    font-size:16px; font-family:inherit; cursor:pointer;
    color:{TITLE_TEXT}; background:#ffffff;
    border:2px solid {LINE}; border-radius:12px;
    box-shadow:0 3px 8px rgba(40,80,140,.18);
  }}
  .copy:hover {{ background:#f0f8ff; }}
  footer {{ text-align:center; color:{TITLE_TEXT}; margin-top:36px; font-size:16px;
            text-shadow:0 1px 4px rgba(255,255,255,.8); }}
</style>
</head>
<body>
<div class="bg">{anime_bg_svg()}</div>
<h1>📚 入世使用说明书（日式动漫小人书版）</h1>
<div class="flow">{flow_svg()}</div>
<div class="pages">
{body}
</div>
<footer>本说明书中的每一条命令都按原样实测通过（2026-08-03，Python 3.14 + DeepSeek deepseek-chat，全新项目 mybook 全流程 S0→S10）。遇到问题先看「急救卡」，再问 Codex。</footer>
<script>
document.querySelectorAll('.copy').forEach(function(btn){{
  btn.addEventListener('click', function(){{
    var done = function(){{ btn.textContent = '✅ 已复制'; setTimeout(function(){{ btn.textContent = '📋 复制命令'; }}, 1500); }};
    if (navigator.clipboard && navigator.clipboard.writeText) {{
      navigator.clipboard.writeText(btn.dataset.cmd).then(done, function(){{
        var t = document.createElement('textarea');
        t.value = btn.dataset.cmd; document.body.appendChild(t); t.select();
        document.execCommand('copy'); t.remove(); done();
      }});
    }}
  }});
}});
</script>
</body>
</html>"""


def main() -> None:
    IMG_DIR.mkdir(parents=True, exist_ok=True)
    for p in PANELS:
        svg = svg_panel(**p)
        height = int(svg.split('height="')[1].split('"')[0])
        assert height >= 260, f"面板 {p['pid']} 高度异常: {height}"
        (IMG_DIR / f"panel-{p['pid']}.svg").write_text(svg, encoding="utf-8")
    (IMG_DIR / "flow.svg").write_text(flow_svg(), encoding="utf-8")
    OUT_HTML.write_text(build_html(), encoding="utf-8")
    print(f"生成 {len(PANELS)} 幅面板（日式动漫风，自适应高度）+ 流程图 + HTML: {OUT_HTML}")


if __name__ == "__main__":
    main()
