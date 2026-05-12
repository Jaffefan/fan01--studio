"""归档首页生成器：扫描 episodes/ 下所有期刊，生成时间线列表首页"""

import sys
import os
import json
from datetime import datetime

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


ARCHIVE_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>伊恩 AI 小报 | 全部期刊</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;500;600;700;900&family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  :root {{
    --bg-page: #faf6ee;
    --bg-card: #ffffff;
    --bg-stage: radial-gradient(ellipse at 50% 20%, #fdf8ed 0%, #f0e9d9 100%);
    --ink: #1d1d1f;
    --ink-soft: #6e6e73;
    --ink-mute: #a0a0a4;
    --line: #e8e2d2;
    --accent: #d4801b;
    --serif: "Noto Serif SC", "Source Han Serif SC", serif;
    --sans: "Inter", -apple-system, BlinkMacSystemFont, "PingFang SC", sans-serif;
  }}
  body {{
    font-family: var(--sans);
    background: var(--bg-page);
    color: var(--ink);
    line-height: 1.7;
    -webkit-font-smoothing: antialiased;
  }}

  /* ── Hero 舞台 ── */
  .hero {{
    background: var(--bg-stage);
    text-align: center;
    padding: 48px 24px 36px;
    border-radius: 28px;
    margin: 18px auto 0;
    max-width: 840px;
    position: relative;
  }}
  .hero::after {{
    content: '';
    position: absolute;
    left: 0; right: 0; bottom: 0;
    height: 60px;
    background: linear-gradient(to top, rgba(60,40,10,0.05), transparent);
    pointer-events: none;
    border-radius: 0 0 28px 28px;
  }}
  .hero-mascot {{
    height: 180px;
    margin: 0 auto 22px;
    display: block;
    position: relative;
    z-index: 2;
    filter:
      drop-shadow(0 28px 22px rgba(80,50,10,0.16))
      drop-shadow(0 10px 8px rgba(80,50,10,0.09));
  }}
  .hero-text {{ position: relative; z-index: 2; }}
  .logo {{
    font-family: var(--serif);
    font-size: 38px;
    font-weight: 900;
    letter-spacing: 6px;
    margin-bottom: 4px;
    position: relative;
  }}
  .logo::before, .logo::after {{
    content: '✦';
    color: var(--accent);
    font-size: 14px;
    margin: 0 18px;
    vertical-align: 10px;
    opacity: 0.65;
  }}
  .tagline {{
    font-size: 13.5px;
    color: var(--ink-soft);
    margin-bottom: 18px;
    letter-spacing: 1px;
  }}
  .stats {{
    display: inline-block;
    background: var(--bg-card);
    padding: 6px 22px;
    border-radius: 999px;
    font-size: 12.5px;
    color: var(--ink-soft);
    border: 1px solid var(--line);
    letter-spacing: 1px;
    font-weight: 500;
  }}

  /* ── Grid 容器 ── */
  .grid-container {{
    max-width: 880px;
    margin: 0 auto;
    padding: 28px 20px 80px;
  }}
  .section-title {{
    font-family: var(--serif);
    font-size: 12.5px;
    font-weight: 600;
    color: var(--ink-mute);
    margin: 8px 4px 18px;
    letter-spacing: 4px;
    text-transform: uppercase;
    border-bottom: 1px solid var(--line);
    padding-bottom: 12px;
  }}
  .episodes-grid {{
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 20px;
  }}
  @media (max-width: 640px) {{
    .episodes-grid {{ grid-template-columns: 1fr; }}
    .hero {{ margin: 10px 12px 0; padding: 36px 16px 28px; border-radius: 20px; }}
    .hero::after {{ border-radius: 0 0 20px 20px; }}
    .hero-mascot {{ height: 140px; }}
    .logo {{ font-size: 30px; letter-spacing: 4px; }}
    .logo::before, .logo::after {{ margin: 0 8px; }}
  }}

  /* ── 卡片 ── */
  .episode-card {{
    background: var(--bg-card);
    border-radius: 16px;
    overflow: hidden;
    cursor: pointer;
    transition: transform 0.25s, box-shadow 0.25s;
    text-decoration: none;
    color: inherit;
    display: flex;
    flex-direction: column;
    border: 1px solid var(--line);
    box-shadow: 0 2px 8px rgba(60,40,10,0.04);
    position: relative;
  }}
  .episode-card:hover {{
    transform: translateY(-4px);
    box-shadow: 0 8px 28px rgba(60,40,10,0.10);
  }}
  /* 5 种强调色循环，像不同封面的杂志 */
  .episode-card.card-accent-0 {{ border-top: 3px solid #d4801b; }}
  .episode-card.card-accent-1 {{ border-top: 3px solid #c75b4a; }}
  .episode-card.card-accent-2 {{ border-top: 3px solid #4a8c6f; }}
  .episode-card.card-accent-3 {{ border-top: 3px solid #5b6fb5; }}
  .episode-card.card-accent-4 {{ border-top: 3px solid #8b5e9e; }}

  .ep-cover {{
    width: 100%;
    aspect-ratio: 16 / 10;
    object-fit: cover;
    background: #eee;
    display: block;
  }}
  .ep-body {{
    padding: 16px 18px 18px;
    flex: 1;
    display: flex;
    flex-direction: column;
  }}
  .ep-issue-no {{
    font-family: var(--sans);
    font-size: 10.5px;
    font-weight: 700;
    color: var(--ink-mute);
    letter-spacing: 2px;
    margin-bottom: 8px;
  }}
  .ep-title {{
    font-family: var(--serif);
    font-size: 17px;
    font-weight: 700;
    color: var(--ink);
    line-height: 1.5;
    margin-bottom: 10px;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }}
  .ep-meta {{
    display: flex;
    gap: 14px;
    font-size: 11.5px;
    color: var(--ink-mute);
    margin-bottom: 12px;
    letter-spacing: 0.5px;
  }}
  .ep-meta-chip {{
    background: #f5efe1;
    padding: 2px 10px;
    border-radius: 999px;
    font-size: 11px;
    color: var(--ink-soft);
  }}
  .ep-quote {{
    font-family: var(--serif);
    font-size: 12.5px;
    color: var(--ink-soft);
    background: #fdf8ed;
    border-left: 2px solid var(--accent);
    padding: 8px 12px;
    margin-top: auto;
    line-height: 1.65;
    font-style: italic;
    border-radius: 0 6px 6px 0;
  }}
  .empty {{
    text-align: center;
    padding: 60px 20px;
    color: var(--ink-mute);
    font-family: var(--serif);
  }}
  .footer {{
    text-align: center;
    color: var(--ink-mute);
    font-size: 11.5px;
    margin-top: 48px;
    letter-spacing: 0.5px;
  }}
</style>
</head>
<body>
<div class="grid-container">
  <div class="hero">
    <img class="hero-mascot" src="mascot.png" alt="AstraX">
    <div class="hero-text">
      <div class="logo">伊恩 AI 小报</div>
      <div class="tagline">每日一份带音频的 AI 资讯简报 · 把全网最值得关注的大事讲给你听</div>
      <span class="stats">已发布 {episode_count} 期</span>
    </div>
  </div>

  <div class="section-title">历 期</div>

  <div class="episodes-grid">
    {episodes_html}
  </div>

  <div class="footer">
    Powered by Claude Code · Updated {generated_at}
  </div>
</div>
</body>
</html>"""


def build_archive(repo_dir: str) -> str:
    """扫描 repo_dir/episodes/ 下所有期刊，生成根目录 index.html"""
    import shutil

    episodes_dir = os.path.join(repo_dir, "episodes")
    if not os.path.exists(episodes_dir):
        os.makedirs(episodes_dir, exist_ok=True)

    # 确保 mascot 在仓库根目录（如果 repo_dir 不是当前目录则需要复制）
    src_mascot = "mascot.png"
    dst_mascot = os.path.join(repo_dir, "mascot.png")
    if os.path.exists(src_mascot) and os.path.abspath(src_mascot) != os.path.abspath(dst_mascot):
        shutil.copy(src_mascot, dst_mascot)

    # 收集所有期 metadata
    episodes = []
    for name in sorted(os.listdir(episodes_dir), reverse=True):
        meta_path = os.path.join(episodes_dir, name, "episode_meta.json")
        if not os.path.exists(meta_path):
            continue
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                episodes.append(json.load(f))
        except Exception:
            continue

    # 写一份 episodes-list.json 给 episode 页面 JS 用（实现上一期/下一期导航）
    nav_list = [
        {
            "episode_id": ep["episode_id"],
            "title": ep.get("title", ""),
            "published_at": ep.get("published_at", ""),
        }
        for ep in episodes
    ]
    with open(os.path.join(repo_dir, "episodes-list.json"), "w", encoding="utf-8") as f:
        json.dump(nav_list, f, ensure_ascii=False, indent=2)

    # 渲染卡片
    if not episodes:
        episodes_html = '<div class="empty">还没有节目，敬请期待</div>'
    else:
        cards = []
        for i, ep in enumerate(episodes):
            # 补 issue_no（反向计算：最新一期 = len）
            ep.setdefault("issue_no", f"VOL.{len(episodes) - i:03d}")
            cards.append(_render_episode_card(ep, i))
        episodes_html = "\n".join(cards)

    html = ARCHIVE_TEMPLATE.format(
        episode_count=len(episodes),
        episodes_html=episodes_html,
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
    )

    out_path = os.path.join(repo_dir, "index.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"  ✅ 归档首页已更新（共 {len(episodes)} 期）")
    return out_path


def _render_episode_card(ep: dict, index: int) -> str:
    """渲染一张期刊卡片（双列网格，每张不同强调色）"""
    episode_id = ep["episode_id"]
    title = _escape(ep.get("title", ""))
    published = _escape(_short_date(ep.get("published_at", "")))
    duration = _escape(ep.get("duration_label", ""))
    segment_count = ep.get("segment_count", 0)
    issue_no = ep.get("issue_no", "")
    cover = ep.get("cover_image", "image_01.jpg")
    cover_url = f"episodes/{episode_id}/{cover}"

    # 头条金句
    segments = ep.get("segments", [])
    top_quote = ""
    for seg in segments:
        if seg.get("golden_quote"):
            top_quote = seg["golden_quote"]
            break

    quote_html = (
        f'<div class="ep-quote">&ldquo;{_escape(top_quote)}&rdquo;</div>'
        if top_quote else ""
    )
    accent_class = f"card-accent-{index % 5}"

    return f'''<a class="episode-card {accent_class}" href="episodes/{episode_id}/">
  <img class="ep-cover" src="{cover_url}" alt="{title}">
  <div class="ep-body">
    <div class="ep-issue-no">{issue_no} · {published}</div>
    <div class="ep-title">{title}</div>
    <div class="ep-meta">
      <span class="ep-meta-chip">⏱ {duration}</span>
      <span class="ep-meta-chip">{segment_count} 条</span>
    </div>
    {quote_html}
  </div>
</a>'''


def _escape(text: str) -> str:
    if not text:
        return ""
    return (
        text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
    )


def _short_date(date_str: str) -> str:
    """2026-05-12 08:30 → 5/12"""
    try:
        parts = date_str.split(" ")[0].split("-")
        if len(parts) == 3:
            return f"{int(parts[1])}/{int(parts[2])}"
    except Exception:
        pass
    return date_str


if __name__ == "__main__":
    from config import LOCAL_REPO_DIR
    if os.path.exists(LOCAL_REPO_DIR):
        build_archive(LOCAL_REPO_DIR)
    else:
        print(f"未找到本地仓库 {LOCAL_REPO_DIR}")
