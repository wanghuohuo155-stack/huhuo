"""四断点截图回归：375 / 768 / 1024 / 1440 视觉零重叠检查。

用法：
  python docs/screenshot_regression.py [html路径]   # 独立运行，默认检查同目录说明书
  或由 make_manual_huaxiu.py 生成后自动调用 run_regression()
产出：screenshots/{375,768,1024,1440}px.png + screenshots/report.json
检查项：横向溢出、页面兄弟块重叠、气泡重叠、命令文字与复制按钮重叠、
        长命令横向滚动、流程导航溢出、内容逃逸卡片。
状态语义：run_regression 返回 (status, report)，status ∈ ok / failed / skipped。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


DEFAULT_HTML = Path(__file__).resolve().parent / "使用说明-花拳绣腿.html"
WIDTHS = [375, 768, 1024, 1440]


OVERLAP_JS = r"""
() => {
  const issues = [];
  const innerW = window.innerWidth;

  function box(el) {
    const r = el.getBoundingClientRect();
    return { x: r.x, y: r.y, w: r.width, h: r.height, right: r.right, bottom: r.bottom };
  }
  function area(b) { return b.w * b.h; }
  function intersect(a, b) {
    const x = Math.max(0, Math.min(a.right, b.right) - Math.max(a.x, b.x));
    const y = Math.max(0, Math.min(a.bottom, b.bottom) - Math.max(a.y, b.y));
    return x * y;
  }
  function checkPair(a, b, where, kind) {
    const ba = box(a), bb = box(b);
    if (ba.w <= 0 || ba.h <= 0 || bb.w <= 0 || bb.h <= 0) return;
    const inter = intersect(ba, bb);
    const minArea = Math.min(area(ba), area(bb));
    if (inter > 20 && inter > minArea * 0.02) {
      issues.push({
        where, kind,
        a: (a.className || a.tagName).toString(),
        b: (b.className || b.tagName).toString(),
        overlap: Math.round(inter)
      });
    }
  }

  // 1. 页面横向溢出
  const doc = document.documentElement;
  if (doc.scrollWidth > innerW + 1) {
    issues.push({ where: 'document', kind: 'h-scroll', scrollWidth: doc.scrollWidth, innerWidth: innerW });
  }

  // 2. 每张卡片：直接子块之间不允许重叠（page-top / body / cmd / bubbles）
  document.querySelectorAll('.page').forEach(page => {
    const kids = Array.from(page.children).filter(k => k.offsetParent !== null);
    for (let i = 0; i < kids.length; i++) {
      for (let j = i + 1; j < kids.length; j++) {
        checkPair(kids[i], kids[j], page.id, 'page-sibling');
      }
    }
    const pr = box(page);
    if (pr.right > innerW + 1 || pr.x < -1) {
      issues.push({ where: page.id, kind: 'page-clipped', x: Math.round(pr.x), right: Math.round(pr.right), innerWidth: innerW });
    }
  });

  // 3. 气泡之间、气泡内部（mark 与文字）不允许重叠
  document.querySelectorAll('.bubbles').forEach(bub => {
    const kids = Array.from(bub.children);
    for (let i = 0; i < kids.length; i++) {
      for (let j = i + 1; j < kids.length; j++) {
        checkPair(kids[i], kids[j], bub.closest('.page').id, 'bubble-sibling');
      }
    }
    kids.forEach(b => {
      const mark = b.querySelector('.mark');
      const txt = b.querySelector('span:last-child');
      if (mark && txt) checkPair(mark, txt, bub.closest('.page').id, 'bubble-inner');
    });
  });

  // 4. 命令文字与复制按钮 / 状态文字不允许重叠
  document.querySelectorAll('.cmd').forEach(cmd => {
    const pre = cmd.querySelector('pre');
    const btn = cmd.querySelector('.copy');
    const status = cmd.querySelector('.copy-status');
    const pid = cmd.closest('.page').id;
    if (pre && btn) checkPair(pre, btn, pid, 'cmd-button');
    if (pre && status) checkPair(pre, status, pid, 'cmd-status');
  });

  // 5. 长命令不允许出现容器内横向滚动
  document.querySelectorAll('pre').forEach(pre => {
    if (pre.scrollWidth > pre.clientWidth + 1) {
      issues.push({ where: pre.closest('.page').id, kind: 'pre-hscroll', scrollWidth: pre.scrollWidth, clientWidth: pre.clientWidth });
    }
  });

  // 6. 流程导航不允许溢出视口
  const flow = document.querySelector('.flow');
  if (flow) {
    const fb = box(flow);
    if (fb.right > innerW + 1 || fb.x < -1) {
      issues.push({ where: 'flow', kind: 'flow-clipped', x: Math.round(fb.x), right: Math.round(fb.right), innerWidth: innerW });
    }
  }

  // 7. 卡片内任何文本块超出其祖先 .page 底部（内容被裁切）
  document.querySelectorAll('.page').forEach(page => {
    const pb = box(page);
    page.querySelectorAll('p, pre, .bubble, .page-top').forEach(el => {
      const eb = box(el);
      if (eb.bottom > pb.bottom + 1 || eb.right > pb.right + 1) {
        issues.push({ where: page.id, kind: 'content-escapes', el: (el.className || el.tagName).toString() });
      }
    });
  });

  return issues;
}
"""


def run_regression(html_path: Path | str, shot_dir: Path | str | None = None) -> tuple[str, dict]:
    """对 html_path 跑四断点零重叠回归。

    返回 (status, report)：
      ok      —— 全部断点零问题，report 为 {宽: {issues, screenshot}}
      failed  —— 存在重叠/溢出/浏览器错误，report 同上
      skipped —— 未安装 playwright（外部依赖缺失，不阻塞生成）
    """
    target = Path(html_path)
    if not target.exists():
        return "failed", {"error": f"HTML 不存在: {target}"}
    out_dir = Path(shot_dir) if shot_dir else target.parent / "screenshots"
    out_dir.mkdir(parents=True, exist_ok=True)
    url = target.resolve().as_uri()
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return "skipped", {}
    report: dict = {}
    failed = False
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel="msedge", headless=True)
        for w in WIDTHS:
            page = browser.new_page(viewport={"width": w, "height": 900}, reduced_motion="reduce")
            try:
                page.goto(url, wait_until="load", timeout=30000)
                page.wait_for_timeout(400)
                issues = page.evaluate(OVERLAP_JS)
                shot = out_dir / f"{w}px.png"
                page.screenshot(path=str(shot), full_page=True)
                report[w] = {"issues": issues, "screenshot": str(shot)}
                if issues:
                    failed = True
            except Exception as exc:  # 外部失败路径：浏览器打不开页面时给出可读错误
                report[w] = {"issues": [{"where": "launch", "kind": "error", "message": str(exc)}], "screenshot": ""}
                failed = True
            finally:
                page.close()
        browser.close()
    (out_dir / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return ("failed" if failed else "ok"), report


def main() -> int:
    html = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_HTML
    status, report = run_regression(html)
    if status == "skipped":
        print("未安装 playwright，跳过视觉回归。安装：python -m pip install playwright")
        return 0
    for w in WIDTHS:
        info = report.get(w, {})
        issues = info.get("issues", [])
        print(f"{w}px: {len(issues)} issues -> {info.get('screenshot', '')}")
        for it in issues[:12]:
            print("   ", it)
    return 1 if status == "failed" else 0


if __name__ == "__main__":
    sys.exit(main())
