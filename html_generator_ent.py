"""娱乐深度谈 — 故事书风格网页生成器"""

import sys, os, json, re, subprocess, shutil
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from tts import _resolve_ffmpeg_bin

HTML_ENT = r"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{title} - 伊恩娱乐深度谈</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;500;600;700;900&family=Noto+Sans+SC:wght@400;500;700&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
:root{{
  --bg: #fef9f0;
  --card: #fffaf5;
  --ink: #2c2416;
  --ink-soft: #5c4a3a;
  --ink-mute: #9a8a7a;
  --line: #e8dcc8;
  --accent: #c8782a;
  --accent-soft: #e8a84a;
  --warm: #f5e6d0;
  --serif: "Noto Serif SC", "Source Han Serif SC", serif;
  --sans: "Noto Sans SC", -apple-system, "PingFang SC", sans-serif;
}}
body{{font-family:var(--serif);background:var(--bg);color:var(--ink);line-height:1.85;-webkit-font-smoothing:antialiased}}
.container{{max-width:720px;margin:0 auto;padding:32px 24px 80px}}

/* 顶部：第 X 夜 */
.issue-tag{{text-align:center;margin-bottom:8px}}
.issue-tag span{{display:inline-block;font-family:var(--sans);font-size:12px;letter-spacing:3px;color:var(--accent);background:var(--warm);padding:4px 16px;border-radius:999px;font-weight:600}}

/* 封面图 */
.cover{{margin:20px 0 28px;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,.06)}}
.cover img{{width:100%;aspect-ratio:16/10;object-fit:cover;display:block}}

/* 标题 */
.title{{font-family:var(--serif);font-size:30px;font-weight:900;color:var(--ink);text-align:center;line-height:1.45;margin-bottom:20px;letter-spacing:.5px}}

/* 元信息 */
.meta{{text-align:center;font-family:var(--sans);font-size:13px;color:var(--ink-mute);margin-bottom:8px}}
.meta span{{margin:0 10px}}

/* 播放器 */
.player{{background:var(--card);padding:24px;border-radius:14px;margin:24px 0;border:1px solid var(--line)}}
.player-label{{font-family:var(--sans);font-size:11px;letter-spacing:3px;color:var(--ink-mute);text-transform:uppercase;margin-bottom:10px;text-align:center}}
audio{{width:100%;height:44px;border-radius:8px}}

/* 章节 */
.chapters{{margin:28px 0}}
.chapter-item{{display:flex;align-items:center;padding:12px 16px;margin-bottom:6px;background:var(--card);border-radius:12px;border:1px solid var(--line);cursor:pointer;transition:all .15s}}
.chapter-item:hover{{border-color:var(--accent-soft);background:var(--warm)}}
.chapter-num{{font-family:var(--sans);font-size:12px;font-weight:700;color:var(--accent);min-width:32px}}
.chapter-title{{flex:1;font-family:var(--serif);font-size:15px;color:var(--ink)}}
.chapter-time{{font-family:var(--sans);font-size:12px;color:var(--ink-mute)}}

/* 故事正文区 */
.story{{background:var(--card);border-radius:14px;padding:28px 24px;margin:28px 0;border:1px solid var(--line);line-height:2}}
.story h3{{font-family:var(--serif);font-size:19px;color:var(--accent);margin:24px 0 12px;font-weight:700}}
.story h3:first-child{{margin-top:0}}
.story p{{font-size:15px;color:var(--ink-soft);margin-bottom:16px}}
.story .highlight{{font-family:var(--serif);font-size:17px;color:var(--ink);font-weight:600;font-style:italic;padding:16px 0;border-left:3px solid var(--accent-soft);padding-left:16px;margin:16px 0}}

/* 来源 */
.source-bar{{display:flex;align-items:center;gap:10px;font-family:var(--sans);font-size:12px;color:var(--ink-mute);margin-top:24px;padding-top:20px;border-top:1px solid var(--line)}}
.source-bar a{{color:var(--accent);text-decoration:none}}
.source-bar a:hover{{text-decoration:underline}}

/* 底栏 */
.footer{{text-align:center;font-family:var(--sans);font-size:11px;color:var(--ink-mute);margin-top:48px;letter-spacing:.5px}}

@media(max-width:600px){{
  .container{{padding:20px 16px 64px}}
  .title{{font-size:24px}}
  .story h3{{font-size:17px}}
}}
</style></head>
<body><div class="container">
  <div class="issue-tag"><span>第 {issue_no} 夜</span></div>
  {cover_html}
  <h1 class="title">{title}</h1>
  <div class="meta"><span>{date_str}</span><span>{duration_label}</span><span>伊恩 讲述</span></div>
  <div class="player"><div class="player-label">🎧 收听本期故事</div>
    <audio id="player" controls preload="metadata"><source src="full.mp3?v={cache_bust}" type="audio/mpeg"></audio>
  </div>
  {chapters_html}
  <div class="story">{story_html}</div>
  <div class="source-bar">{source_html}<a href="{source_link}" target="_blank" rel="noopener">🔗 原文</a></div>
  <div class="footer">伊恩娱乐深度谈 · 每日一个故事 · {generated_at}</div>
</div>
<script>
const player=document.getElementById('player');
document.querySelectorAll('[data-seek]').forEach(el=>{{el.addEventListener('click',()=>{{player.currentTime=parseFloat(el.getAttribute('data-seek'));player.play();window.scrollTo({{top:0,behavior:'smooth'}})}})}});
</script>
</body></html>"""


def generate_ent_html(script: dict, audio_path: str, image_path: str | None,
                       output_dir: str, date_str: str) -> str:
    """生成娱乐栏目故事书页面"""
    cache_bust = datetime.now().strftime("%Y%m%d%H%M%S")

    # 计算「第几夜」
    episodes_root = os.path.join(".", "episodes_ent")
    existing = 0
    if os.path.isdir(episodes_root):
        existing = sum(1 for n in os.listdir(episodes_root)
                       if os.path.isdir(os.path.join(episodes_root, n)) and n != date_str)
    issue_no = existing + 1

    page_dir = os.path.join(output_dir, f"site_ent_{date_str}")
    os.makedirs(page_dir, exist_ok=True)

    # 音频
    if audio_path and os.path.exists(audio_path):
        shutil.copy(audio_path, os.path.join(page_dir, "full.mp3"))

    # 封面图
    cover_html = ""
    if image_path and os.path.exists(image_path):
        ext = os.path.splitext(image_path)[1] or ".jpg"
        dst = os.path.join(page_dir, f"cover{ext}")
        shutil.copy(image_path, dst)
        cover_html = f'<div class="cover"><img src="cover{ext}?v={cache_bust}" alt=""></div>'
    else:
        # 生成一个占位封面
        cover_html = '<div class="cover"><div style="background:linear-gradient(135deg,#f5e6d0,#e8c88a);height:300px;display:flex;align-items:center;justify-content:center;font-size:48px;color:#c8782a">📖</div></div>'

    # 章节
    chapters = script.get("chapters", [])
    chapters_html = ""
    if chapters:
        items = []
        for i, ch in enumerate(chapters):
            items.append(
                f'<div class="chapter-item"><span class="chapter-num">0{i + 1}</span>'
                f'<span class="chapter-title">{_esc(ch)}</span></div>'
            )
        chapters_html = f'<div class="chapters">{"".join(items)}</div>'

    # 故事正文 —— 把脚本按自然段落格式化
    script_text = script.get("script", "")
    paragraphs = _format_story_paragraphs(script_text, chapters)
    story_html = "\n".join(f"<p>{_esc(p)}</p>" for p in paragraphs)

    # 时长
    total_sec = _duration(audio_path) if audio_path else 0
    mins, secs = int(total_sec // 60), int(total_sec % 60)
    duration_label = f"{mins}分{secs:02d}秒"

    parts = date_str.split("-")
    display_date = f"{'-'.join(parts[:3])} 午间" if len(parts) >= 3 else date_str

    html = HTML_ENT.format(
        title=_esc(script.get("title", "")),
        date_str=display_date,
        issue_no=f"{issue_no:03d}",
        duration_label=duration_label,
        cover_html=cover_html,
        chapters_html=chapters_html,
        story_html=story_html,
        source_html=f"来源：{_esc(script.get('source', ''))} · ",
        source_link=_esc(script.get("source_link", "#")),
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
        cache_bust=cache_bust,
    )

    page_path = os.path.join(page_dir, "index.html")
    with open(page_path, "w", encoding="utf-8") as f:
        f.write(html)
    return page_path


def _format_story_paragraphs(text: str, chapters: list[str]) -> list[str]:
    """将长脚本按章节标题和自然段落拆分"""
    paras = []
    for line in [l.strip() for l in text.split("\n") if l.strip()]:
        # 看是否匹配章节标题
        is_chapter = False
        for ch in chapters:
            if ch in line and len(line) < 30:
                paras.append(f"【{ch}】")
                is_chapter = True
                break
        if not is_chapter:
            # 按句号断成自然段
            for sent in re.split(r"(?<=[。！？])", line):
                sent = sent.strip()
                if sent and len(sent) > 4:
                    paras.append(sent)
    return paras


def _duration(filepath: str) -> float:
    if not filepath or not os.path.exists(filepath):
        return 0
    try:
        r = subprocess.run([_resolve_ffmpeg_bin("ffprobe"), "-v", "error",
                            "-show_entries", "format=duration",
                            "-of", "default=noprint_wrappers=1:nokey=1", filepath],
                           capture_output=True, text=True)
        return float(r.stdout.strip())
    except Exception:
        return 0


def _esc(text: str) -> str:
    if not text: return ""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
