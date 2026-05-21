"""娱乐资讯抓取：影视 + 游戏 + 动漫 RSS"""

import sys, re, feedparser, httpx
from datetime import datetime, timezone, timedelta
from config import ENT_RSS_FEEDS, ENT_MAX_ARTICLES_PER_FEED

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BJT = timezone(timedelta(hours=8))
AIHOT_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 aihot-skill/0.2.0"
)


def fetch_entertainment(only_today: bool = True) -> list[dict]:
    """从娱乐 RSS 源抓取文章"""
    all_articles = []

    print("🎬 抓取娱乐资讯...\n")
    for feed_cfg in ENT_RSS_FEEDS:
        try:
            items = _fetch_feed(feed_cfg)
            all_articles.extend(items)
            print(f"  ✓ {feed_cfg['name']}: {len(items)} 篇")
        except Exception as e:
            print(f"  ✗ {feed_cfg['name']}: {e}")

    if only_today:
        today = datetime.now(BJT).strftime("%Y-%m-%d")
        before = len(all_articles)
        all_articles = [a for a in all_articles if a["date"] == today]
        print(f"\n📅 过滤当天: {before} → {len(all_articles)} 篇")

    # 去重 + 排序
    all_articles = _dedup(all_articles)
    all_articles.sort(key=lambda x: x["published"], reverse=True)
    print(f"📋 共 {len(all_articles)} 篇娱乐资讯\n")
    return all_articles


def _fetch_feed(cfg: dict) -> list[dict]:
    feed = feedparser.parse(cfg["url"])
    articles = []
    for entry in feed.entries[:ENT_MAX_ARTICLES_PER_FEED]:
        published_iso = _parse_time(entry)
        date_str = _to_beijing_date(published_iso)
        summary_html = entry.get("summary", "") or entry.get("description", "")
        summary = _strip_html(summary_html)
        image_url = _extract_image(entry, summary_html)
        articles.append({
            "title": entry.get("title", "无标题"),
            "summary": summary[:500],
            "link": entry.get("link", ""),
            "published": published_iso,
            "date": date_str,
            "source": cfg["name"],
            "lang": cfg["lang"],
            "image_url": image_url,
        })
    return articles


def _parse_time(entry) -> str:
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        dt = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
        return dt.isoformat()
    return datetime.now(timezone.utc).isoformat()


def _to_beijing_date(iso_str: str) -> str:
    try:
        s = iso_str.replace("Z", "+00:00")
        dt = datetime.fromisoformat(s).astimezone(BJT)
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return iso_str[:10]


def _strip_html(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", text)).strip()


def _extract_image(entry, summary_html: str) -> str | None:
    if hasattr(entry, "media_thumbnail") and entry.media_thumbnail:
        url = entry.media_thumbnail[0].get("url")
        if url: return url
    if summary_html:
        m = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', summary_html)
        if m: return m.group(1)
    return None


def _dedup(articles: list[dict]) -> list[dict]:
    seen, unique = set(), []
    for a in articles:
        key = re.sub(r"\s+", "", a["title"])[:15]
        if key not in seen:
            seen.add(key); unique.append(a)
    return unique
