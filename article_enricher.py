"""文章正文抓取模块：多重兜底确保拿到原文

策略优先级：
1. jina.ai Reader（免费、无需 key、专为 LLM 设计、抗反爬）
2. trafilatura（本地解析，离线可用）
3. 直接 GET + 简单正则（最后兜底）
"""

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

MAX_BODY_CHARS = 5000  # 单篇抓取的正文上限


def enrich_articles(articles: list[dict]) -> list[dict]:
    """对每篇文章尝试抓全文并填充 full_body 字段；失败时保留原 summary"""
    print("📖 抓取文章正文...")
    for art in articles:
        link = art.get("link")
        if not link:
            continue

        # 顺序尝试三种方法，先成功的胜出
        body = (
            _fetch_via_jina(link)
            or _fetch_via_trafilatura(link)
            or _fetch_via_simple_get(link)
        )

        if body and len(body) > len(art.get("summary", "")):
            art["full_body"] = body[:MAX_BODY_CHARS]
            print(f"  ✓ {art['title'][:30]}: {len(body)} 字")
        else:
            art["full_body"] = art.get("summary", "")
            print(f"  · {art['title'][:30]}: 用 summary 兜底")
    return articles


def _fetch_via_jina(url: str) -> str:
    """jina.ai Reader：最稳定的方案，专为 LLM 抓取设计"""
    try:
        # jina.ai Reader 接口：https://r.jina.ai/<encoded_url>
        # 直接拼接即可，它会返回干净的 markdown
        proxy_url = f"https://r.jina.ai/{url}"
        with httpx.Client(timeout=20, follow_redirects=True) as client:
            resp = client.get(
                proxy_url,
                headers={"Accept": "text/plain", "X-Return-Format": "text"},
            )
            if resp.status_code == 200 and len(resp.text) > 200:
                # jina 返回包含 Title/URL Source/Markdown Content 等头部，提取正文
                text = resp.text
                # 去掉常见的元信息头部
                if "Markdown Content:" in text:
                    text = text.split("Markdown Content:", 1)[1]
                elif "\n\n" in text[:500]:
                    text = text.split("\n\n", 1)[1] if text.startswith("Title:") else text
                return text.strip()
    except Exception as e:
        pass
    return ""


def _fetch_via_trafilatura(url: str) -> str:
    """trafilatura：离线解析，速度快"""
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
    return ""


def _fetch_via_simple_get(url: str) -> str:
    """简单 GET + 正则提取 <article>/<p>"""
    try:
        with httpx.Client(headers=HEADERS, timeout=15, follow_redirects=True) as client:
            resp = client.get(url)
            if resp.status_code != 200:
                return ""
            html = resp.text
        article_match = re.search(r'<article[^>]*>(.*?)</article>', html, re.DOTALL | re.IGNORECASE)
        block = article_match.group(1) if article_match else html
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
    test = [
        {"title": "test1", "link": "https://www.qbitai.com", "summary": "abc"},
        {"title": "test2", "link": "https://techcrunch.com", "summary": "abc"},
    ]
    enrich_articles(test)
    for t in test:
        print(t["title"], "→", len(t.get("full_body", "")), "chars")
