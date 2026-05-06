"""文章正文抓取模块：尝试拉取原文全文，配合社交平台评论增强 DeepSeek 输入"""

import sys
import re
import httpx

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
)
HEADERS = {"User-Agent": USER_AGENT, "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"}

MAX_BODY_CHARS = 4000  # 单篇抓取的正文上限


def enrich_articles(articles: list[dict]) -> list[dict]:
    """对每篇文章尝试抓全文并填充 full_body 字段；失败时保留原 summary"""
    print("📖 抓取文章正文...")
    for art in articles:
        link = art.get("link")
        if not link:
            continue
        body = _fetch_full_text(link)
        if body and len(body) > len(art.get("summary", "")):
            art["full_body"] = body[:MAX_BODY_CHARS]
            print(f"  ✓ {art['title'][:30]}: {len(body)} 字")
        else:
            art["full_body"] = art.get("summary", "")
            print(f"  · {art['title'][:30]}: 用 summary 兜底")
    return articles


def _fetch_full_text(url: str) -> str:
    """尝试用 trafilatura（如有）抓正文，否则降级为 BeautifulSoup-style 正则"""
    # 优先用 trafilatura（语义抽取最准）
    try:
        import trafilatura
        downloaded = trafilatura.fetch_url(url, no_ssl=True)
        if downloaded:
            text = trafilatura.extract(
                downloaded,
                include_comments=False,
                include_tables=False,
                favor_recall=True,
            )
            if text:
                return text.strip()
    except ImportError:
        pass
    except Exception:
        pass

    # 降级：直接 GET + 简单提取 <article> 或 <p> 文本
    try:
        with httpx.Client(headers=HEADERS, timeout=15, follow_redirects=True) as client:
            resp = client.get(url)
            if resp.status_code != 200:
                return ""
            html = resp.text
        # 优先 <article>
        article_match = re.search(r'<article[^>]*>(.*?)</article>', html, re.DOTALL | re.IGNORECASE)
        block = article_match.group(1) if article_match else html
        # 提取所有 <p>
        paragraphs = re.findall(r'<p[^>]*>(.*?)</p>', block, re.DOTALL | re.IGNORECASE)
        text = "\n\n".join(_strip_html(p) for p in paragraphs)
        return text.strip()
    except Exception:
        return ""


def _strip_html(html: str) -> str:
    text = re.sub(r"<[^>]+>", "", html)
    text = re.sub(r"\s+", " ", text).strip()
    return text


if __name__ == "__main__":
    test = [{"title": "test", "link": "https://www.qbitai.com", "summary": "abc"}]
    enrich_articles(test)
    print(test[0].get("full_body", "")[:300])
