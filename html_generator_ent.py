"""娱乐深度谈 — 故事书+新粗野主义风格网页"""

import sys, os, json, re, subprocess, shutil
from datetime import datetime

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from tts import _resolve_ffmpeg_bin


CSS_ENT = """
*{margin:0;padding:0;box-sizing:border-box}
:root{--bg:#FAF8F5;--ink:#1A1613;--pink:#FF3366;--green:#00E5A3;--gray:#9A9A9A;--light:#EFECE6;--card:#FFFFFF;--border:#E0DDD6;--sans:"Noto Sans SC",sans-serif;--art:"Playfair Display",serif}
body{font-family:var(--sans);background:var(--bg);color:var(--ink);-webkit-font-smoothing:antialiased;overflow-x:hidden}
html{scroll-behavior:smooth}
.bg-blob{position:fixed;border-radius:50%;filter:blur(120px);opacity:.55;pointer-events:none;z-index:0}
.bg-blob-1{top:-80px;right:-10%;width:500px;height:500px;background:linear-gradient(135deg,#FFEEF2,#E3FFF2)}
.bg-blob-2{top:40%;left:-10%;width:400px;height:400px;background:linear-gradient(135deg,#FFFCE3,#FFEEF2);opacity:.45}
header{max-width:1200px;margin:0 auto;padding:24px 24px 16px;display:flex;justify-content:space-between;align-items:center;position:relative;z-index:10;border-bottom:1px solid var(--border)}
.logo{display:flex;align-items:center;gap:10px}
.logo-badge{background:var(--ink);color:#fff;padding:2px 6px;border-radius:4px;font-size:11px;font-weight:900;letter-spacing:1px}
.logo-text{font-size:12px;font-weight:900;letter-spacing:3px;color:var(--gray)}
.issue-num{font-size:12px;font-family:monospace;color:var(--gray)}
main{max-width:1200px;margin:0 auto;padding:40px 24px 80px;display:grid;grid-template-columns:1fr 360px;gap:40px;position:relative;z-index:10}
@media(max-width:960px){main{grid-template-columns:1fr}}
.content{min-width:0}
.tag-pill{display:inline-flex;align-items:center;gap:6px;background:rgba(0,229,163,.12);color:#00A372;padding:3px 12px;border-radius:999px;font-size:11px;font-weight:900;margin-bottom:16px}
.ep-title{font-size:34px;font-weight:900;line-height:1.25;margin-bottom:24px;letter-spacing:-.5px}
.ep-title .hl{color:var(--pink)}
@media(max-width:600px){.ep-title{font-size:24px}}
.player{background:var(--card);border:2px solid var(--ink);padding:20px;border-radius:16px;box-shadow:6px 6px 0 0 var(--ink);margin-bottom:32px}
.player-row{display:flex;align-items:center;gap:14px}
.play-btn{width:56px;height:56px;border-radius:12px;background:var(--green);border:2px solid var(--ink);display:flex;align-items:center;justify-content:center;cursor:pointer;flex-shrink:0;transition:all .15s}
.play-btn:hover{background:var(--pink);color:#fff}
.play-btn svg{width:22px;height:22px;fill:currentColor;margin-left:2px}
.player-info{flex:1;min-width:0}
.player-status{font-size:11px;font-weight:900;color:var(--gray);text-transform:uppercase;letter-spacing:1px}
.player-time{font-size:11px;font-family:monospace;font-weight:700;color:var(--ink)}
.player-bar-row{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:6px}
.progress-bar{height:12px;background:var(--light);border-radius:999px;border:1px solid var(--border);overflow:hidden}
.progress-fill{height:100%;background:var(--pink);border-radius:999px;width:0;transition:width .3s}
.story{font-size:16px;line-height:1.9;color:#444}
.story p{margin-bottom:20px}
.section{padding-top:16px;scroll-margin-top:24px}
.section-header{display:flex;align-items:center;gap:10px;margin-bottom:14px}
.section-btn{display:flex;align-items:center;gap:4px;padding:4px 10px;background:var(--ink);color:var(--green);font-size:11px;font-family:monospace;font-weight:700;border-radius:8px;cursor:pointer;border:none;transition:all .15s}
.section-btn:hover{background:var(--pink);color:#fff}
.section-btn span{font-size:12px}
.section-title{font-size:22px;font-weight:900;color:var(--ink)}
@media(max-width:600px){.section-title{font-size:18px}}
.image-card{margin:32px 0;position:relative;display:flex;justify-content:center}
.image-card-inner{width:100%;aspect-ratio:16/9;background:var(--light);border-radius:24px;border:2px solid var(--ink);box-shadow:4px 4px 0 0 var(--ink);overflow:hidden}
.image-card-inner img{width:100%;height:100%;object-fit:cover;display:block}
.more{border-top:1px solid var(--border);padding-top:32px;margin-top:40px}
.more-label{font-size:11px;font-weight:900;color:var(--gray);letter-spacing:3px;font-family:monospace;margin-bottom:14px}
.more-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}
@media(max-width:600px){.more-grid{grid-template-columns:1fr}}
.more-card{background:var(--card);border-radius:12px;border:1px solid var(--border);padding:16px;text-decoration:none;transition:all .15s;display:block}
.more-card:hover{border-color:var(--pink)}
.more-card-label{font-size:11px;font-family:monospace;font-weight:700;color:var(--pink);margin-bottom:4px}
.more-card-title{font-size:14px;font-weight:700;color:var(--ink)}
.more-card:hover .more-card-title{color:var(--pink)}
.sidebar{position:sticky;top:24px;display:flex;flex-direction:column;gap:20px}
@media(max-width:960px){.sidebar{position:static}}
.host-card{background:var(--card);border:1px solid var(--border);border-radius:16px;padding:20px;text-align:center;position:relative;overflow:hidden}
.host-card::before{content:'';position:absolute;top:0;left:0;right:0;height:3px;background:linear-gradient(90deg,var(--green),var(--pink))}
.host-avatar{width:64px;height:64px;background:#FFFCE3;border-radius:50%;border:2px solid var(--ink);margin:0 auto 12px;display:flex;align-items:center;justify-content:center;font-size:28px}
.host-name{font-weight:900;font-size:14px}
.host-handle{font-size:10px;font-family:monospace;color:var(--pink);font-weight:700;margin:2px 0 8px}
.host-bio{font-size:12px;color:var(--gray);line-height:1.6;text-align:left;background:var(--bg);padding:12px;border-radius:10px}
.timeline{background:var(--card);border:2px solid var(--ink);border-radius:16px;padding:20px;box-shadow:4px 4px 0 0 var(--ink)}
.timeline-label{font-size:11px;font-weight:900;color:var(--gray);letter-spacing:3px;text-transform:uppercase;margin-bottom:12px}
.tl-item{display:flex;align-items:flex-start;gap:10px;padding:10px;border-radius:10px;cursor:pointer;border:1px solid transparent;transition:all .15s;margin-bottom:4px}
.tl-item:hover{background:#FFEEF2;border-color:rgba(255,51,102,.2)}
.tl-time{background:var(--ink);color:var(--green);font-family:monospace;font-size:11px;font-weight:700;padding:2px 6px;border-radius:6px;flex-shrink:0}
.tl-item:hover .tl-time{background:var(--pink);color:#fff}
.tl-title{font-size:12px;font-weight:700;color:var(--ink)}
footer{max-width:1200px;margin:0 auto;padding:0 24px 40px;text-align:center;position:relative;z-index:10}
.footer-quote{font-family:var(--art);font-style:italic;font-size:15px;color:var(--ink);margin-bottom:8px}
.footer-tag{font-size:11px;font-weight:700;color:var(--gray)}
"""

JS_ENT = """
const audio=document.getElementById('audio');
const playBtn=document.getElementById('play-btn');
const playIcon=document.getElementById('play-icon');
const pauseIcon=document.getElementById('pause-icon');
const progressFill=document.getElementById('progress-fill');
const currentTimeEl=document.getElementById('current-time');
const playerStatus=document.getElementById('player-status');

function fmt(t){var m=Math.floor(t/60),s=Math.floor(t%60);return (m<10?'0':'')+m+':'+(s<10?'0':'')+s}

function togglePlay(){if(audio.paused){audio.play()}else{audio.pause()}}
audio.onplay=function(){playIcon.style.display='none';pauseIcon.style.display='block';playerStatus.textContent='正在播放'}
audio.onpause=function(){playIcon.style.display='block';pauseIcon.style.display='none';playerStatus.textContent='已暂停'}
audio.ontimeupdate=function(){var p=audio.currentTime/audio.duration*100;progressFill.style.width=p+'%';currentTimeEl.textContent=fmt(audio.currentTime)}
audio.onended=function(){playIcon.style.display='block';pauseIcon.style.display='none';playerStatus.textContent='播放完毕';progressFill.style.width='0%';currentTimeEl.textContent='00:00'}

function seek(t,elId){audio.currentTime=t;if(audio.paused)audio.play();if(elId){var el=document.getElementById(elId);if(el)el.scrollIntoView({behavior:'smooth'})}}

fetch('../../episodes_ent_list.json').then(function(r){return r.json()}).then(function(list){
  var m=location.pathname.match(/episodes_ent\/([^\/]+)/);
  if(!m)return;
  var cur=m[1],idx=list.findIndex(function(e){return e.id===cur});
  if(idx===-1)return;
  var newer=idx>0?list[idx-1]:null,older=idx<list.length-1?list[idx+1]:null;
  if(newer){var cn=document.getElementById('card-next');cn.href='../'+newer.id+'/';cn.querySelector('.more-card-title').textContent=newer.title}
  if(older){var co=document.getElementById('card-prev');co.href='../'+older.id+'/';co.querySelector('.more-card-title').textContent=older.title}
}).catch(function(){});
"""

HTML_BODY = """<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{title} - 伊恩娱乐深度谈</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@500;700;900&family=Playfair+Display:ital,wght@1,900&display=swap" rel="stylesheet">
<style>{css}</style></head>
<body>
<div class="bg-blob bg-blob-1"></div>
<div class="bg-blob bg-blob-2"></div>

<header>
  <div class="logo">
    <span class="logo-badge">IAN</span>
    <span class="logo-text">伊恩娱乐深度谈</span>
  </div>
  <div class="issue-num">第 {issue_no} 夜 / {date_short}</div>
</header>

<main>
  <div class="content">
    <div class="tag-pill"><span>#</span> {category}</div>
    <h1 class="ep-title">{title_high}</h1>

    <div class="player">
      <div class="player-row">
        <button class="play-btn" id="play-btn" onclick="togglePlay()">
          <svg id="play-icon" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
          <svg id="pause-icon" viewBox="0 0 24 24" style="display:none"><path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/></svg>
        </button>
        <div class="player-info">
          <div class="player-bar-row">
            <span class="player-status" id="player-status">点击播放</span>
            <span class="player-time"><span id="current-time">00:00</span> / {total_time}</span>
          </div>
          <div class="progress-bar"><div class="progress-fill" id="progress-fill"></div></div>
        </div>
      </div>
    </div>

    <article class="story">
      {story_html}
    </article>

    <section class="more">
      <p class="more-label">更多故事 / MORE STORIES</p>
      <div class="more-grid" id="more-grid">
        <a href="#" class="more-card" id="card-next">
          <p class="more-card-label">NEXT →</p>
          <h4 class="more-card-title">敬请期待</h4>
        </a>
        <a href="#" class="more-card" id="card-prev">
          <p class="more-card-label">← PREVIOUS</p>
          <h4 class="more-card-title">敬请期待</h4>
        </a>
      </div>
    </section>
  </div>

  <aside class="sidebar">
    <div class="host-card">
      <div class="host-avatar">🧔🏻‍♂️</div>
      <div class="host-name">讲述者：伊恩 (Ian)</div>
      <div class="host-handle">@IAN_TALKSHOW</div>
      <div class="host-bio">AI影视行业编导。像窝在咖啡馆闲聊的朋友，把影视、动漫、游戏的来龙去脉聊得通透有趣。</div>
    </div>

    <div class="timeline">
      <div class="timeline-label">故事时间轴</div>
      {timeline_html}
    </div>
  </aside>
</main>

<footer>
  <p class="footer-quote">" 听完故事，咖啡刚好也凉了。 "</p>
  <p class="footer-tag">IAN ENTERTAINMENT IN-DEPTH TALK © 2026</p>
</footer>

<audio id="audio" preload="metadata"><source src="full.mp3?v={cache_bust}" type="audio/mpeg"></audio>
<script>{js}</script>
</body></html>"""


def generate_ent_html(script: dict, audio_path: str, image_path: str | None,
                       output_dir: str, date_str: str) -> str:
    """生成娱乐栏目页面"""
    cache_bust = datetime.now().strftime("%Y%m%d%H%M%S")

    episodes_root = os.path.join(".", "episodes_ent")
    existing = sum(1 for n in os.listdir(episodes_root)
                   if os.path.isdir(os.path.join(episodes_root, n))) if os.path.isdir(episodes_root) else 0
    issue_no = f"{existing + 1:03d}"

    page_dir = os.path.join(output_dir, f"site_ent_{date_str}")
    os.makedirs(page_dir, exist_ok=True)

    if audio_path and os.path.exists(audio_path):
        shutil.copy(audio_path, os.path.join(page_dir, "full.mp3"))
    total_sec = _duration(audio_path) if audio_path else 0
    total_time = _fmt(total_sec)

    raw_title = script.get("title", "")
    title_high = _highlight_title(raw_title)
    keywords = script.get("keywords", [])
    category = keywords[0] if keywords else "娱乐深度"

    parts = date_str.split("-")
    date_short = f"{'-'.join(parts[:3])}" if len(parts) >= 3 else date_str

    chapters = script.get("chapters", [])
    script_text = script.get("script", "")
    story_html, timeline_html, chapter_times = _build_story(script_text, chapters, total_sec)

    cover_file = None
    if image_path and os.path.exists(image_path):
        ext = os.path.splitext(image_path)[1] or ".jpg"
        cover_file = f"cover{ext}"
        shutil.copy(image_path, os.path.join(page_dir, cover_file))
    image_block = ""
    if cover_file:
        image_block = f"""<div class="image-card"><div class="image-card-inner"><img src="{cover_file}?v={cache_bust}" alt=""></div></div>"""

    body = HTML_BODY.format(
        css=CSS_ENT, js=JS_ENT,
        title=_esc(raw_title),
        title_high=title_high,
        issue_no=issue_no,
        date_short=date_short,
        category=_esc(category),
        total_time=total_time,
        story_html=image_block + "\n" + story_html,
        timeline_html=timeline_html,
        cache_bust=cache_bust,
    )

    page_path = os.path.join(page_dir, "index.html")
    with open(page_path, "w", encoding="utf-8") as f:
        f.write(body)

    _update_ent_list()
    return page_path


def _build_story(text: str, chapters: list[str], total_sec: float):
    story_parts = []
    timeline_items = []
    chapter_times = []

    if chapters:
        segments = _split_by_chapters(text, chapters)
    else:
        segments = _split_by_paragraphs(text)

    for sec_id, (label, content) in enumerate(segments, 1):
        sec_div_id = f"sec-{sec_id:04d}"
        start_sec = total_sec * (sec_id - 1) / max(len(segments), 1)
        time_label = _fmt(start_sec)

        if sec_id <= 5 and label:
            timeline_items.append(
                f'<div class="tl-item" onclick="seek({start_sec:.1f},\'{sec_div_id}\')">'
                f'<span class="tl-time">{time_label}</span>'
                f'<span class="tl-title">{_esc(label[:20])}</span></div>'
            )
            chapter_times.append((start_sec, label))

        section_title_html = ""
        if label and len(label) > 1:
            section_title_html = (
                f'<div class="section-header">'
                f'<button class="section-btn" onclick="seek({start_sec:.1f},\'{sec_div_id}\')">'
                f'<span>▶</span> {time_label}</button>'
                f'<h3 class="section-title">{_esc(label)}</h3>'
                f'</div>'
            )

        paras = [l.strip() for l in content.split("\n") if l.strip()]
        paras_html = "".join(f"<p>{_esc(p)}</p>" for p in paras if len(p) > 2)

        story_parts.append(
            f'<div class="section" id="{sec_div_id}">'
            f'{section_title_html}{paras_html}</div>'
        )

    return "\n".join(story_parts), "\n".join(timeline_items), chapter_times


def _split_by_chapters(text: str, chapters: list[str]):
    segments = []
    remaining = text
    for ch in chapters:
        idx = remaining.find(ch)
        if idx >= 0:
            if idx > 0:
                segments.append(("", remaining[:idx].strip()))
            segments.append((ch, ch))
            remaining = remaining[idx + len(ch):]
    if remaining.strip():
        segments.append(("", remaining.strip()))
    if len(segments) <= 1:
        return _split_by_paragraphs(text)
    return segments


def _split_by_paragraphs(text: str):
    paras = [p.strip() for p in re.split(r'\n{2,}', text) if p.strip()]
    result = []
    for p in paras:
        lines = p.split("\n")
        label = lines[0][:25] if lines else ""
        result.append((label, p))
    if len(result) > 6:
        merged, buf = [], ""
        for label, content in result:
            buf += content + "\n\n"
            if len(buf) > 600:
                merged.append((label, buf.strip()))
                buf = ""
        if buf:
            merged.append(("", buf.strip()))
        return merged
    return result


def _highlight_title(title: str) -> str:
    highlighted = re.sub(r'[「「](.+?)[」」]', r'<span class="hl">「\1」</span>', title)
    if highlighted != title:
        return highlighted
    half = len(title) // 2
    if half > 4:
        return title[:half] + '<span class="hl">' + title[half:] + '</span>'
    return title


def _update_ent_list():
    root = os.path.join(".", "episodes_ent")
    items = []
    if os.path.isdir(root):
        for name in sorted(os.listdir(root), reverse=True):
            mp = os.path.join(root, name, "episode_meta.json")
            if os.path.exists(mp):
                try:
                    with open(mp, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                    items.append({"id": meta["episode_id"], "title": meta.get("title", "")})
                except Exception:
                    continue
    with open("episodes_ent_list.json", "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False)


def _duration(fp: str) -> float:
    if not fp or not os.path.exists(fp):
        return 0
    try:
        r = subprocess.run([_resolve_ffmpeg_bin("ffprobe"), "-v", "error",
                            "-show_entries", "format=duration",
                            "-of", "default=noprint_wrappers=1:nokey=1", fp],
                           capture_output=True, text=True)
        return float(r.stdout.strip())
    except Exception:
        return 0


def _fmt(sec: float) -> str:
    m, s = int(sec // 60), int(sec % 60)
    return f"{m:02d}:{s:02d}"


def _esc(text: str) -> str:
    if not text:
        return ""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
