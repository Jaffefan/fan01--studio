"""飞书机器人推送模块：将每日 AI 资讯简报推送到飞书群"""

import sys
import httpx
from datetime import datetime

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from config import FEISHU_WEBHOOK


def push_to_feishu(script: dict, date_str: str, podcast_url: str | None = None):
    """将口播文案以富文本卡片形式推送到飞书群"""

    title = script.get("title", "每日AI资讯")
    segments = script.get("segments", [])

    # 期号 2026-04-28-1647 → 显示成 "2026-04-28 16:47"
    parts = date_str.split("-")
    if len(parts) >= 4 and len(parts[3]) == 4:
        display_date = f"{'-'.join(parts[:3])} {parts[3][:2]}:{parts[3][2:]}"
    else:
        display_date = date_str

    # 构建资讯列表（用快读摘要而非口播稿）
    news_lines = []
    for i, seg in enumerate(segments, 1):
        keywords = "、".join(seg.get("keywords", [])[:3])
        news_lines.append(f"**{i}. {seg['news_title']}**")
        news_lines.append(f"`{seg.get('source', '')}` · {keywords}")
        summary = (seg.get("summary") or seg.get("script", ""))[:120].replace("\n", " ")
        news_lines.append(f"{summary}...")
        news_lines.append("")

    content = "\n".join(news_lines)

    # 底部链接区
    footer_lines = []
    if podcast_url:
        footer_lines.append(f"🎧 **[点击收听完整播客 →]({podcast_url})**")
        footer_lines.append("")
    footer_lines.append(f"📅 期号: {display_date}")

    elements = [
        {
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": f"**📅 {display_date}**\n\n{content}",
            },
        },
        {"tag": "hr"},
        {
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": "\n".join(footer_lines),
            },
        },
    ]

    if podcast_url:
        elements.append({
            "tag": "action",
            "actions": [
                {
                    "tag": "button",
                    "text": {"tag": "plain_text", "content": "🎧 立即收听"},
                    "url": podcast_url,
                    "type": "primary",
                }
            ],
        })

    card = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {"tag": "plain_text", "content": f"📡 {title}"},
                "template": "blue",
            },
            "elements": elements,
        },
    }

    try:
        resp = httpx.post(FEISHU_WEBHOOK, json=card, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") == 0:
            print("  ✅ 飞书推送成功！")
        else:
            print(f"  ⚠️ 飞书返回异常: {data}")
    except Exception as e:
        print(f"  ⚠️ 飞书推送失败: {e}")


if __name__ == "__main__":
    import json
    import os
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
        print(f"推送 {date_str} 的资讯到飞书...\n")
        push_to_feishu(script, date_str)
