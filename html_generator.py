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
<title>{title} - 伊恩 AI 小报</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;500;600;700;900&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  :root {{
    --bg-page: #fdfcf8;
    --bg-card: #ffffff;
    --ink: #1d1d1f;
    --ink-soft: #5a5a5e;
    --ink-mute: #999;
    --line: #e8e4db;
    --line-light: #f0ece3;
    --accent: #d4801b;
    --serif: "Noto Serif SC", "Source Han Serif SC", serif;
    --sans: "Inter", -apple-system, BlinkMacSystemFont, "PingFang SC", sans-serif;
  }}
  body {{
    font-family: var(--serif);
    background: var(--bg-page);
    color: var(--ink);
    line-height: 1.85;
    -webkit-font-smoothing: antialiased;
  }}
  .container {{
    max-width: 700px;
    margin: 0 auto;
    padding: 40px 24px 80px;
  }}

  /* ── 面包屑 ── */
  .breadcrumb {{
    display: flex;
    align-items: center;
    gap: 8px;
    font-family: var(--sans);
    font-size: 12px;
    color: var(--ink-mute);
    margin-bottom: 36px;
    letter-spacing: 0.5px;
  }}
  .breadcrumb a {{
    color: var(--ink-soft);
    text-decoration: none;
    transition: color 0.15s;
  }}
  .breadcrumb a:hover {{ color: var(--accent); }}
  .breadcrumb .sep {{ font-size: 9px; }}
  .breadcrumb .vol {{
    margin-left: auto;
    font-family: var(--sans);
    font-size: 11px;
    letter-spacing: 2px;
    color: var(--ink-mute);
  }}

  /* ── 报头 (Newspaper Masthead) ── */
  .masthead {{
    text-align: center;
    border-top: 1px solid var(--ink);
    border-bottom: 2px solid var(--ink);
    padding: 16px 0;
    margin-bottom: 32px;
  }}
  .masthead-show {{
    font-family: var(--serif);
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 5px;
    color: var(--ink);
    text-transform: uppercase;
  }}
  .masthead-info {{
    font-family: var(--sans);
    font-size: 11px;
    color: var(--ink-soft);
    margin-top: 4px;
    letter-spacing: 1px;
  }}
  .masthead-info span {{ margin: 0 10px; }}

  /* ── 标题 ── */
  .title {{
    font-family: var(--serif);
    font-size: 34px;
    font-weight: 900;
    color: var(--ink);
    line-height: 1.35;
    text-align: center;
    margin-bottom: 12px;
    letter-spacing: 1px;
  }}

  /* ── 播放器 ── */
  .player {{
    background: var(--bg-card);
    padding: 24px 28px;
    border-radius: 12px;
    margin: 28px 0;
    border: 1px solid var(--line);
  }}
  .player-label {{
    font-family: var(--sans);
    font-size: 11px;
    letter-spacing: 3px;
    color: var(--ink-mute);
    text-transform: uppercase;
    margin-bottom: 12px;
    text-align: center;
  }}
  audio {{
    width: 100%;
    height: 44px;
    border-radius: 8px;
  }}

  /* ── 章节目录 ── */
  .toc {{
    margin-bottom: 36px;
    padding: 0 4px;
  }}
  .toc-title {{
    font-family: var(--sans);
    font-size: 11px;
    color: var(--ink-mute);
    letter-spacing: 3px;
    text-transform: uppercase;
    margin-bottom: 14px;
    font-weight: 600;
  }}
  .toc-item {{
    display: flex;
    align-items: baseline;
    padding: 8px 0;
    cursor: pointer;
    border-bottom: 1px solid var(--line-light);
    transition: color 0.15s;
    font-family: var(--serif);
  }}
  .toc-item:last-child {{ border-bottom: none; }}
  .toc-item:hover {{ color: var(--accent); }}
  .toc-time {{
    font-family: var(--sans);
    font-size: 12px;
    color: var(--accent);
    min-width: 50px;
    margin-right: 16px;
    font-weight: 500;
  }}
  .toc-text {{
    flex: 1;
    font-size: 15px;
    color: var(--ink);
  }}

  /* ── 导读按语 (Editor's Note) ── */
  .opening-note {{
    font-family: var(--serif);
    font-size: 15.5px;
    color: var(--ink-soft);
    font-style: italic;
    line-height: 1.9;
    margin-bottom: 42px;
    padding: 0 4px;
  }}

  /* ── 资讯片段 ── */
  .segment {{
    margin-bottom: 44px;
  }}
  .segment-image {{
    width: 100%;
    aspect-ratio: 16 / 9;
    object-fit: cover;
    background: #eee;
    display: block;
    border-radius: 8px;
    margin-bottom: 18px;
  }}
  .segment-number {{
    font-family: var(--sans);
    font-size: 11px;
    font-weight: 600;
    color: var(--accent);
    letter-spacing: 3px;
    text-transform: uppercase;
    margin-bottom: 8px;
  }}
  .segment-title {{
    font-family: var(--serif);
    font-size: 21px;
    font-weight: 700;
    color: var(--ink);
    line-height: 1.45;
    margin-bottom: 12px;
  }}
  .segment-summary {{
    font-family: var(--serif);
    font-size: 15px;
    color: var(--ink-soft);
    line-height: 1.9;
    margin-bottom: 14px;
  }}

  /* ── 金句引用 ── */
  .golden-quote {{
    font-family: var(--serif);
    font-size: 18px;
    font-weight: 500;
    color: var(--ink);
    text-align: center;
    padding: 20px 32px;
    margin: 24px 0;
    position: relative;
    line-height: 1.7;
    font-style: italic;
  }}
  .golden-quote::before {{
    content: '\\201C';
    font-size: 56px;
    color: var(--accent);
    position: absolute;
    left: 0;
    top: 6px;
    font-weight: 700;
    line-height: 1;
    opacity: 0.4;
  }}

  /* ── 来源与标签 ── */
  .segment-meta {{
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    font-family: var(--sans);
    font-size: 11.5px;
    color: var(--ink-mute);
    align-items: center;
  }}
  .tag {{
    background: #f5f0e8;
    padding: 3px 10px;
    border-radius: 999px;
    color: var(--ink-soft);
    font-size: 11px;
  }}
  .source-link {{
    color: var(--accent);
    text-decoration: none;
    font-weight: 500;
    margin-left: auto;
  }}
  .source-link:hover {{ text-decoration: underline; }}

  /* ── 上下期导航 ── */
  .episode-nav {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
    margin-top: 56px;
    padding-top: 32px;
    border-top: 1px solid var(--line);
    font-family: var(--sans);
  }}
  .episode-nav a {{
    text-decoration: none;
    color: inherit;
    transition: color 0.15s;
    display: block;
  }}
  .episode-nav a:hover {{ color: var(--accent); }}
  .episode-nav-label {{
    font-size: 11px;
    color: var(--ink-mute);
    letter-spacing: 2px;
    margin-bottom: 6px;
    text-transform: uppercase;
  }}
  .episode-nav-title {{
    font-family: var(--serif);
    font-size: 14px;
    color: var(--ink);
    line-height: 1.5;
    overflow: hidden;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
  }}
  .episode-nav .next {{ text-align: right; }}
  .episode-nav .placeholder {{
    color: var(--ink-mute);
    cursor: default;
    opacity: 0.5;
  }}

  .footer {{
    text-align: center;
    font-family: var(--sans);
    font-size: 11px;
    color: var(--ink-mute);
    margin-top: 48px;
    letter-spacing: 0.5px;
  }}

  @media (max-width: 600px) {{
    .container {{ padding: 24px 16px 64px; }}
    .title {{ font-size: 26px; }}
    .segment-title {{ font-size: 18px; }}
    .golden-quote {{ font-size: 16px; padding: 16px 20px; }}
  }}
</style>
</head>
<body>
<div class="container">
  <div class="breadcrumb">
    <a href="../../index.html">← 全部期刊</a>
    <span class="sep">·</span>
    <span>伊恩 AI 小报</span>
    <span class="vol">第 {issue_no} 期</span>
  </div>

  <div class="masthead">
    <div class="masthead-show">伊恩 AI 小报</div>
    <div class="masthead-info">
      <span>{date_str}（北京时间）</span><span>·</span><span>{segment_count} 条深度报道</span><span>·</span><span>{duration_label}</span><span>·</span><span>主笔 伊恩</span>
    </div>
  </div>

  <h1 class="title">{title}</h1>

  <div class="player">
    <div class="player-label">收听本期</div>
    <audio id="player" controls preload="metadata">
      <source src="full.mp3?v={cache_bust}" type="audio/mpeg">
    </audio>
  </div>

  <div class="toc">
    <div class="toc-title">章节</div>
    {toc_items}
  </div>

  {segments_html}

  <div class="episode-nav" id="episode-nav"></div>

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

  // 上一期 / 下一期导航
  fetch('../../episodes-list.json')
    .then(r => r.json())
    .then(list => {{
      const m = window.location.pathname.match(/episodes\\/([^\\/]+)/);
      if (!m) return;
      const currentId = m[1];
      const idx = list.findIndex(e => e.episode_id === currentId);
      if (idx === -1) return;
      const newer = idx > 0 ? list[idx - 1] : null;
      const older = idx < list.length - 1 ? list[idx + 1] : null;
      const nav = document.getElementById('episode-nav');
      const olderHtml = older
        ? `<a href="../${{older.episode_id}}/" class="prev">
             <div class="episode-nav-label">← 上一期</div>
             <div class="episode-nav-title">${{older.title}}</div>
           </a>`
        : `<div class="placeholder prev">
             <div class="episode-nav-label">← 上一期</div>
             <div class="episode-nav-title">已经是最早一期了</div>
           </div>`;
      const newerHtml = newer
        ? `<a href="../${{newer.episode_id}}/" class="next">
             <div class="episode-nav-label">下一期 →</div>
             <div class="episode-nav-title">${{newer.title}}</div>
           </a>`
        : `<div class="placeholder next">
             <div class="episode-nav-label">下一期 →</div>
             <div class="episode-nav-title">这是最新一期</div>
           </div>`;
      nav.innerHTML = olderHtml + newerHtml;
    }})
    .catch(() => {{}});
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

    # 计算"第几期"：扫描 episodes/ 已有目录数 + 1（本期还没加入）
    episodes_root = os.path.join(".", "episodes")
    existing_count = 0
    if os.path.isdir(episodes_root):
        existing_count = sum(
            1 for name in os.listdir(episodes_root)
            if os.path.isdir(os.path.join(episodes_root, name))
            and name != date_str  # 重复发同一期不重复计数
        )
    issue_no = existing_count + 1

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

    # 渲染每条资讯片段（报纸式编排：大图 → 编号 → 标题 → 正文 → 引用）
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
            f'<img class="segment-image" src="{img_filename}?v={cache_bust}" alt="{_escape(seg["news_title"])}" data-seek="{seek_seconds}" style="cursor:pointer">'
            if img_filename else
            '<div class="segment-image"></div>'
        )

        keywords_html = " ".join(
            f'<span class="tag">{_escape(k)}</span>' for k in seg.get("keywords", [])
        )

        source_link = seg.get("source_link", "")
        source_name = seg.get("source", "")
        source_html = (
            f'<a class="source-link" href="{_escape(source_link)}" target="_blank" rel="noopener">原文 →</a>'
            if source_link else ""
        )

        summary = seg.get("summary") or ""
        golden_quote = seg.get("golden_quote", "")
        quote_html = (
            f'<div class="golden-quote">{_escape(golden_quote)}</div>'
            if golden_quote else ""
        )

        segments_html.append(f"""
  <div class="segment">
    {img_html}
    <div class="segment-number" data-seek="{seek_seconds}" style="cursor:pointer">第 {i} 条 · {time_label}</div>
    <h2 class="segment-title">{_escape(seg["news_title"])}</h2>
    <div class="segment-summary">{_escape(summary)}</div>
    {quote_html}
    <div class="segment-meta">
      {keywords_html}
      <span class="tag">来源: {_escape(source_name)}</span>
      {source_html}
    </div>
  </div>""")

    # 直接 ffprobe 测合并后 mp3 实际时长（最准）
    total_seconds = _get_audio_duration_safe(audio_full_path)
    if not total_seconds and chapters:
        total_seconds = chapters[-1]["start_seconds"]  # 兜底
    duration_label = f"{int(total_seconds // 60)}分{int(total_seconds % 60):02d}秒"

    # 把期号 2026-04-28-1647 格式化为友好显示 "2026-04-28 16:47"
    parts = date_str.split("-")
    if len(parts) >= 4 and len(parts[3]) == 4:
        display_date = f"{'-'.join(parts[:3])} {parts[3][:2]}:{parts[3][2:]}"
    else:
        display_date = date_str

    html = HTML_TEMPLATE.format(
        title=_escape(script.get("title", "每日AI资讯")),
        date_str=display_date,
        issue_no=f"{issue_no:03d}",  # 三位数补零，如 001 / 042
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


def _get_audio_duration_safe(filepath: str) -> float:
    """用 ffprobe 测时长，失败返回 0"""
    if not filepath or not os.path.exists(filepath):
        return 0.0
    try:
        from tts import _resolve_ffmpeg_bin
        import subprocess
        ffprobe = _resolve_ffmpeg_bin("ffprobe")
        result = subprocess.run(
            [ffprobe, "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", filepath],
            capture_output=True, text=True,
        )
        return float(result.stdout.strip())
    except Exception:
        return 0.0


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
