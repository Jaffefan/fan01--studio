"""微信推送模块：通过 Server酱 将播客简报推送到个人微信"""

import httpx
from config import SERVERCHAN_SENDKEY


def push_to_wechat(script: dict, date_str: str, podcast_url: str | None = None):
    """推送播客简报到微信（Server酱）"""

    title = script.get("title", "每日AI资讯")
    segments = script.get("segments", [])

    news_lines = [f"## {title}\n"]
    for i, seg in enumerate(segments, 1):
        news_lines.append(f"**{i}. {seg['news_title']}**")
        summary = (seg.get("summary") or seg.get("script", ""))[:100]
        news_lines.append(f"> {summary}...")
        news_lines.append("")

    if podcast_url:
        news_lines.append(f"[🎧 收听完整播客]({podcast_url})")
        news_lines.append("")

    parts = date_str.split("-")
    display_date = f"{'-'.join(parts[:3])} {parts[3][:2]}:{parts[3][2:]}" if len(parts) >= 4 and len(parts[3]) == 4 else date_str
    news_lines.append(f"---\n📅 {display_date} · 伊恩 AI 小报")

    body = "\n".join(news_lines)

    try:
        resp = httpx.post(
            f"https://sctapi.ftqq.com/{SERVERCHAN_SENDKEY}.send",
            data={"title": f"伊恩 AI 小报 · {display_date}", "desp": body},
            timeout=15,
        )
        data = resp.json()
        if data.get("code") == 0:
            print("  ✅ 微信推送成功！")
        else:
            print(f"  ⚠️ Server酱返回异常: {data}")
    except Exception as e:
        print(f"  ⚠️ 微信推送失败: {e}")
