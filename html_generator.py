"""HTML 网页生成模块：生成类似小宇宙风格的播客详情页"""

import sys
import os
import shutil
import json
from datetime import datetime

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} - {date_str}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  :root {{
    --bg-page: #faf6ee;
    --bg-card: #ffffff;
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
  /* 期刊头：杂志专栏感 */
  .header {{
    background: transparent;
    color: var(--ink);
    padding: 32px 4px 28px;
    margin-bottom: 28px;
    border-top: 2px solid var(--ink);
    border-bottom: 1px solid var(--line);
  }}
  .masthead {{
    display: flex;
    align-items: center;
    gap: 14px;
    margin-bottom: 22px;
  }}
  .mascot-avatar {{
    width: 52px;
    height: 52px;
    border-radius: 50%;
    background: var(--bg-card);
    border: 1px solid var(--line);
    object-fit: cover;
    object-position: center top;
    padding: 2px;
    flex-shrink: 0;
  }}
  .masthead-meta {{
    flex: 1;
    line-height: 1.4;
  }}
  .masthead-by {{
    font-family: var(--serif);
    font-size: 13px;
    color: var(--ink);
    letter-spacing: 1px;
  }}
  .masthead-channel {{
    font-family: var(--serif);
    font-size: 11.5px;
    color: var(--ink-mute);
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-top: 2px;
  }}
  .title {{
    font-family: var(--serif);
    font-size: 28px;
    font-weight: 600;
    color: var(--ink);
    line-height: 1.5;
    margin-bottom: 14px;
    letter-spacing: 0.5px;
  }}
  .meta {{
    font-size: 12px;
    color: var(--ink-mute);
    letter-spacing: 1px;
  }}
  .player {{
    background: var(--bg-card);
    padding: 20px;
    border-radius: 14px;
    margin-bottom: 24px;
    border: 1px solid var(--line);
    box-shadow: 0 1px 3px rgba(60,40,10,0.04);
  }}
  audio {{
    width: 100%;
    height: 44px;
  }}
  .toc {{
    background: var(--bg-card);
    padding: 18px 22px;
    border-radius: 14px;
    margin-bottom: 28px;
    border: 1px solid var(--line);
    box-shadow: 0 1px 3px rgba(60,40,10,0.04);
  }}
  .toc-title {{
    font-family: var(--serif);
    font-size: 12px;
    color: var(--ink-soft);
    margin-bottom: 14px;
    letter-spacing: 3px;
    text-transform: uppercase;
    font-weight: 600;
  }}
  .toc-item {{
    display: flex;
    align-items: flex-start;
    padding: 10px 0;
    cursor: pointer;
    border-bottom: 1px solid #f5efe1;
    transition: background 0.15s;
  }}
  .toc-item:last-child {{ border-bottom: none; }}
  .toc-item:hover {{ background: #fdfaf1; }}
  .toc-time {{
    color: var(--accent);
    font-size: 12.5px;
    font-family: "SF Mono", Consolas, monospace;
    min-width: 52px;
    margin-right: 12px;
    margin-top: 2px;
    letter-spacing: 0.5px;
  }}
  .toc-text {{
    flex: 1;
    font-size: 14.5px;
    color: var(--ink);
  }}
  .segment {{
    background: var(--bg-card);
    border-radius: 14px;
    margin-bottom: 18px;
    overflow: hidden;
    border: 1px solid var(--line);
    box-shadow: 0 1px 3px rgba(60,40,10,0.04);
  }}
  .segment-image {{
    width: 100%;
    aspect-ratio: 16 / 9;
    object-fit: cover;
    background: #eee;
    display: block;
  }}
  .segment-body {{
    padding: 20px 22px 22px;
  }}
  .segment-time {{
    display: inline-block;
    color: var(--accent);
    font-size: 12px;
    font-weight: 600;
    background: #fdf2e0;
    padding: 4px 10px;
    border-radius: 999px;
    cursor: pointer;
    margin-bottom: 12px;
    font-family: "SF Mono", Consolas, monospace;
    letter-spacing: 0.5px;
  }}
  .segment-time:hover {{ background: #f9e6c3; }}
  .segment-title {{
    font-family: var(--serif);
    font-size: 19px;
    font-weight: 600;
    margin-bottom: 12px;
    color: var(--ink);
    line-height: 1.5;
  }}
  .segment-summary {{
    font-size: 14.5px;
    color: var(--ink-soft);
    margin-bottom: 14px;
    line-height: 1.85;
  }}
  .golden-quote {{
    font-family: var(--serif);
    font-size: 15px;
    font-weight: 500;
    color: var(--ink);
    background: #fdf8ed;
    border-left: 2px solid var(--accent);
    padding: 12px 16px;
    margin: 14px 0;
    line-height: 1.75;
    font-style: italic;
  }}
  .golden-quote::before {{
    content: '"';
    font-family: var(--serif);
    font-size: 26px;
    color: var(--accent);
    margin-right: 6px;
    font-weight: 700;
    line-height: 0;
    vertical-align: -8px;
  }}
  .segment-meta {{
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    font-size: 12px;
    color: var(--ink-mute);
    align-items: center;
  }}
  .tag {{
    background: #f5efe1;
    padding: 3px 10px;
    border-radius: 999px;
    color: var(--ink-soft);
    font-size: 11.5px;
  }}
  .source-link {{
    color: var(--accent);
    text-decoration: none;
    font-weight: 500;
    margin-left: auto;
  }}
  .source-link:hover {{ text-decoration: underline; }}
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
  <div class="header">
    <div class="masthead">
      <img class="mascot-avatar" src="mascot.png?v={cache_bust}" alt="AstraX">
      <div class="masthead-meta">
        <div class="masthead-by">主笔 · 伊恩</div>
        <div class="masthead-channel">AstraX · AI 雷达</div>
      </div>
    </div>
    <div class="title">{title}</div>
    <div class="meta">{date_str} · 共 {segment_count} 条 · 时长约 {duration_label}</div>
  </div>

  <div class="player">
    <audio id="player" controls preload="metadata">
      <source src="full.mp3?v={cache_bust}" type="audio/mpeg">
      你的浏览器不支持音频播放。
    </audio>
  </div>

  <div class="toc">
    <div class="toc-title">📑 章节</div>
    {toc_items}
  </div>

  {segments_html}

  <div class="footer">
    Powered by Claude Code · {generated_at}
  </div>
</div>

<script>
  const player = document.getElementById('player');
  document.querySelectorAll('[data-seek]').forEach(el => {{
    el.addEventListener('click', () => {{
      const t = parseFloat(el.getAttribute('data-seek'));
      player.currentTime = t;
      player.play();
      window.scrollTo({{ top: 0, behavior: 'smooth' }});
    }});
  }});
</script>
</body>
</html>"""


def generate_html(
    script: dict,
    chapters: list[dict],
    image_paths: dict,
    audio_full_path: str,
    output_dir: str,
    date_str: str,
) -> str:
    """生成播客详情页 HTML，并把音频/图片复制到同一目录"""

    # 缓存破坏戳：每次生成用一个新的版本号，强制浏览器重新加载资源
    cache_bust = datetime.now().strftime("%Y%m%d%H%M%S")

    page_dir = os.path.join(output_dir, f"site_{date_str}")
    os.makedirs(page_dir, exist_ok=True)

    # 复制音频
    if os.path.exists(audio_full_path):
        shutil.copy(audio_full_path, os.path.join(page_dir, "full.mp3"))

    # 复制 mascot 形象图
    if os.path.exists("mascot.png"):
        shutil.copy("mascot.png", os.path.join(page_dir, "mascot.png"))

    # 复制图片
    for idx, img_path in image_paths.items():
        if img_path and os.path.exists(img_path):
            ext = os.path.splitext(img_path)[1] or ".jpg"
            dst = os.path.join(page_dir, f"image_{idx:02d}{ext}")
            shutil.copy(img_path, dst)

    # 渲染章节列表（仅资讯章节，不含开场结尾）
    segment_chapters = [c for c in chapters if c["key"].startswith("segment_")]

    toc_items = []
    for c in segment_chapters:
        toc_items.append(
            f'<div class="toc-item" data-seek="{c["start_seconds"]}">'
            f'  <span class="toc-time">{c["label"]}</span>'
            f'  <span class="toc-text">{_escape(c["title"])}</span>'
            f'</div>'
        )

    # 渲染每条资讯卡片
    segments_html = []
    for i, seg in enumerate(script.get("segments", []), 1):
        chapter = segment_chapters[i - 1] if i - 1 < len(segment_chapters) else None
        time_label = chapter["label"] if chapter else "00:00"
        seek_seconds = chapter["start_seconds"] if chapter else 0

        # 找对应图片
        img_filename = None
        for ext in (".jpg", ".png", ".webp", ".gif"):
            candidate = f"image_{i:02d}{ext}"
            if os.path.exists(os.path.join(page_dir, candidate)):
                img_filename = candidate
                break

        img_html = (
            f'<img class="segment-image" src="{img_filename}?v={cache_bust}" alt="{_escape(seg["news_title"])}">'
            if img_filename else
            '<div class="segment-image"></div>'
        )

        keywords_html = " ".join(
            f'<span class="tag">{_escape(k)}</span>' for k in seg.get("keywords", [])
        )

        source_link = seg.get("source_link", "")
        source_name = seg.get("source", "")
        source_html = (
            f'<a class="source-link" href="{_escape(source_link)}" target="_blank">原文 →</a>'
            if source_link else ""
        )

        summary = seg.get("summary") or seg.get("script", "")[:200]
        golden_quote = seg.get("golden_quote", "")
        quote_html = (
            f'<div class="golden-quote">{_escape(golden_quote)}</div>'
            if golden_quote else ""
        )

        segments_html.append(f"""
  <div class="segment">
    {img_html}
    <div class="segment-body">
      <span class="segment-time" data-seek="{seek_seconds}">▶ {time_label}</span>
      <div class="segment-title">{i}. {_escape(seg["news_title"])}</div>
      {quote_html}
      <div class="segment-summary">{_escape(summary)}</div>
      <div class="segment-meta">
        {keywords_html}
        <span class="tag">来源: {_escape(source_name)}</span>
        {source_html}
      </div>
    </div>
  </div>""")

    total_seconds = chapters[-1]["start_seconds"] if chapters else 0
    duration_label = f"{int(total_seconds // 60)}分{int(total_seconds % 60)}秒"

    # 把期号 2026-04-28-1647 格式化为友好显示 "2026-04-28 16:47"
    parts = date_str.split("-")
    if len(parts) >= 4 and len(parts[3]) == 4:
        display_date = f"{'-'.join(parts[:3])} {parts[3][:2]}:{parts[3][2:]}"
    else:
        display_date = date_str

    html = HTML_TEMPLATE.format(
        title=_escape(script.get("title", "每日AI资讯")),
        date_str=display_date,
        segment_count=len(script.get("segments", [])),
        duration_label=duration_label,
        toc_items="\n    ".join(toc_items),
        segments_html="\n".join(segments_html),
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
        cache_bust=cache_bust,
    )

    page_path = os.path.join(page_dir, "index.html")
    with open(page_path, "w", encoding="utf-8") as f:
        f.write(html)

    return page_path


def _escape(text: str) -> str:
    """简单的 HTML 转义"""
    if not text:
        return ""
    return (
        text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
    )


if __name__ == "__main__":
    from glob import glob
    from config import OUTPUT_DIR

    files = sorted(glob(os.path.join(OUTPUT_DIR, "script_*.json")))
    if not files:
        print("未找到文案文件")
    else:
        latest = files[-1]
        date_str = os.path.basename(latest).replace("script_", "").replace(".json", "")
        with open(latest, "r", encoding="utf-8") as f:
            script = json.load(f)
        audio_dir = os.path.join(OUTPUT_DIR, f"audio_{date_str}")
        chapters_path = os.path.join(audio_dir, "chapters.json")
        chapters = []
        if os.path.exists(chapters_path):
            with open(chapters_path, "r", encoding="utf-8") as f:
                chapters = json.load(f)
        image_dir = os.path.join(OUTPUT_DIR, f"images_{date_str}")
        image_paths = {}
        if os.path.exists(image_dir):
            for fname in os.listdir(image_dir):
                try:
                    idx = int(fname.split(".")[0])
                    image_paths[idx] = os.path.join(image_dir, fname)
                except ValueError:
                    pass
        full_mp3 = os.path.join(audio_dir, "full.mp3")
        path = generate_html(script, chapters, image_paths, full_mp3, OUTPUT_DIR, date_str)
        print(f"网页已生成: {path}")
