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
<title>AstraX · AI 雷达 | 主播伊恩</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;500;600;700&display=swap" rel="stylesheet">
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
    --serif: "Noto Serif SC", "Source Han Serif SC", "Songti SC", serif;
    --sans: -apple-system, BlinkMacSystemFont, "PingFang SC", "Microsoft YaHei", sans-serif;
  }}
  body {{
    font-family: var(--sans);
    background: var(--bg-page);
    color: var(--ink);
    line-height: 1.75;
    -webkit-font-smoothing: antialiased;
  }}
  .container {{
    max-width: 720px;
    margin: 0 auto;
    padding: 24px 20px 80px;
  }}
  .hero {{
    position: relative;
    background: var(--bg-stage);
    color: var(--ink);
    padding: 56px 28px 44px;
    border-radius: 24px;
    margin-bottom: 32px;
    text-align: center;
    overflow: hidden;
  }}
  /* 模拟舞台底部柔光阴影 */
  .hero::after {{
    content: '';
    position: absolute;
    left: 0; right: 0; bottom: 0;
    height: 60px;
    background: linear-gradient(to top, rgba(60,40,10,0.06), transparent);
    pointer-events: none;
  }}
  .hero-mascot {{
    height: 200px;
    margin: 0 auto 28px;
    display: block;
    position: relative;
    z-index: 2;
    /* 多层阴影模拟真实物体落在台面上 */
    filter:
      drop-shadow(0 30px 25px rgba(80,50,10,0.18))
      drop-shadow(0 12px 10px rgba(80,50,10,0.10));
  }}
  .hero-text {{
    position: relative;
    z-index: 2;
  }}
  .logo {{
    font-family: var(--serif);
    font-size: 32px;
    font-weight: 600;
    color: var(--ink);
    letter-spacing: 2px;
    margin-bottom: 10px;
  }}
  .tagline {{
    font-family: var(--serif);
    font-size: 14.5px;
    color: var(--ink-soft);
    margin-bottom: 22px;
    line-height: 1.8;
    letter-spacing: 0.5px;
  }}
  .stats {{
    display: inline-block;
    background: var(--bg-card);
    padding: 7px 20px;
    border-radius: 999px;
    font-size: 12.5px;
    color: var(--ink-soft);
    border: 1px solid var(--line);
    letter-spacing: 1px;
  }}
  .section-title {{
    font-family: var(--serif);
    font-size: 13px;
    font-weight: 600;
    color: var(--ink-soft);
    margin: 12px 4px 16px;
    letter-spacing: 3px;
    text-transform: uppercase;
    border-bottom: 1px solid var(--line);
    padding-bottom: 12px;
  }}
  .episode-card {{
    background: var(--bg-card);
    border-radius: 14px;
    overflow: hidden;
    margin-bottom: 16px;
    box-shadow: 0 1px 3px rgba(60,40,10,0.04), 0 4px 16px rgba(60,40,10,0.04);
    cursor: pointer;
    transition: transform 0.2s, box-shadow 0.2s;
    text-decoration: none;
    color: inherit;
    display: block;
    border: 1px solid var(--line);
  }}
  .episode-card:hover {{
    transform: translateY(-2px);
    box-shadow: 0 6px 24px rgba(60,40,10,0.08);
  }}
  .ep-cover {{
    width: 100%;
    aspect-ratio: 16 / 9;
    object-fit: cover;
    background: #eee;
    display: block;
  }}
  .ep-body {{
    padding: 18px 20px 20px;
  }}
  .ep-meta-top {{
    display: flex;
    justify-content: space-between;
    font-size: 11.5px;
    color: var(--ink-mute);
    margin-bottom: 10px;
    letter-spacing: 0.5px;
  }}
  .ep-title {{
    font-family: var(--serif);
    font-size: 18px;
    font-weight: 600;
    color: var(--ink);
    line-height: 1.5;
    margin-bottom: 14px;
  }}
  .ep-quote {{
    font-family: var(--serif);
    font-size: 13.5px;
    color: var(--ink);
    background: #fdf8ed;
    border-left: 2px solid var(--accent);
    padding: 10px 14px;
    margin-bottom: 12px;
    line-height: 1.7;
    font-style: italic;
  }}
  .ep-segments {{
    font-size: 12.5px;
    color: var(--ink-soft);
    line-height: 1.7;
  }}
  .empty {{
    text-align: center;
    padding: 60px 20px;
    color: var(--ink-mute);
  }}
  .footer {{
    text-align: center;
    color: var(--ink-mute);
    font-size: 11.5px;
    margin-top: 50px;
    letter-spacing: 0.5px;
  }}
</style>
</head>
<body>
<div class="container">
  <div class="hero">
    <img class="hero-mascot" src="mascot.png" alt="AstraX">
    <div class="hero-text">
      <div class="logo">AstraX · AI 雷达</div>
      <div class="tagline">主播伊恩 · 每日 10 分钟<br>把全网最炸的 AI 大事讲给你听</div>
      <span class="stats">已发布 {episode_count} 期</span>
    </div>
  </div>

  <div class="section-title">All Issues · 历期</div>

  {episodes_html}

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

    # 渲染卡片
    if not episodes:
        episodes_html = '<div class="empty">还没有节目，敬请期待 🎙️</div>'
    else:
        cards = []
        for ep in episodes:
            cards.append(_render_episode_card(ep))
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


def _render_episode_card(ep: dict) -> str:
    """渲染一张期刊卡片"""
    episode_id = ep["episode_id"]
    title = _escape(ep.get("title", ""))
    published = _escape(ep.get("published_at", ""))
    duration = _escape(ep.get("duration_label", ""))
    segment_count = ep.get("segment_count", 0)
    cover = ep.get("cover_image", "image_01.jpg")
    cover_url = f"episodes/{episode_id}/{cover}"

    # 头条金句
    segments = ep.get("segments", [])
    top_quote = ""
    for seg in segments:
        if seg.get("golden_quote"):
            top_quote = seg["golden_quote"]
            break

    # 各段标题列表
    seg_titles = " · ".join(
        _escape((s.get("title") or "")[:18]) for s in segments[:5]
    )

    quote_html = (
        f'<div class="ep-quote">"{_escape(top_quote)}"</div>'
        if top_quote else ""
    )

    return f'''<a class="episode-card" href="episodes/{episode_id}/">
  <img class="ep-cover" src="{cover_url}" alt="{title}">
  <div class="ep-body">
    <div class="ep-meta-top">
      <span>📅 {published}</span>
      <span>⏱ {duration} · {segment_count} 条</span>
    </div>
    <div class="ep-title">{title}</div>
    {quote_html}
    <div class="ep-segments">{seg_titles}</div>
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


if __name__ == "__main__":
    from config import LOCAL_REPO_DIR
    if os.path.exists(LOCAL_REPO_DIR):
        build_archive(LOCAL_REPO_DIR)
    else:
        print(f"未找到本地仓库 {LOCAL_REPO_DIR}")
