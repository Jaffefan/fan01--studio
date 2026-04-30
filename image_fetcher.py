"""配图模块：优先抓取原文章封面，失败时用 SiliconFlow AI 生成新闻风格图片"""

import sys
import os
import re
import httpx
from urllib.parse import urlparse

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from config import SILICONFLOW_API_KEY, SILICONFLOW_IMAGE_MODEL

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
HEADERS = {"User-Agent": USER_AGENT}


def fetch_images(script: dict, output_dir: str, date_str: str) -> dict:
    """为口播脚本中每条资讯抓取/生成配图，返回 {segment_index: local_image_path}"""
    image_dir = os.path.join(output_dir, f"images_{date_str}")
    os.makedirs(image_dir, exist_ok=True)

    image_paths = {}
    for i, seg in enumerate(script.get("segments", []), 1):
        print(f"  🖼️ 第{i}条配图: {seg['news_title'][:30]}")

        local_path = os.path.join(image_dir, f"{i:02d}.jpg")

        # 1. 优先用 RSS/Reddit 自带的图片
        original_url = seg.get("image_url")
        if original_url and _download_image(original_url, local_path):
            print(f"     ✓ 使用原文配图")
            image_paths[i] = local_path
            continue

        # 2. 尝试抓原文页面的 og:image
        page_url = seg.get("source_link")
        if page_url:
            og_image = _extract_og_image(page_url)
            if og_image and _download_image(og_image, local_path):
                print(f"     ✓ 使用原文 og:image")
                image_paths[i] = local_path
                continue

        # 3. AI 生成兜底
        keywords = seg.get("keywords", [])
        title = seg.get("news_title", "")
        prompt = _build_image_prompt(title, keywords)
        if _generate_ai_image(prompt, local_path):
            print(f"     ✓ AI 生成配图")
            image_paths[i] = local_path
            continue

        print(f"     ✗ 配图获取失败")

    return image_paths


def _download_image(url: str, save_path: str) -> bool:
    """下载图片，成功返回 True"""
    if not url:
        return False
    try:
        # 处理协议相对路径
        if url.startswith("//"):
            url = "https:" + url
        with httpx.Client(headers=HEADERS, timeout=15, follow_redirects=True) as client:
            resp = client.get(url)
            if resp.status_code != 200:
                return False
            content = resp.content
            # 简单校验是图片
            if len(content) < 1024 or not _looks_like_image(content):
                return False
            with open(save_path, "wb") as f:
                f.write(content)
            return True
    except Exception:
        return False


def _looks_like_image(data: bytes) -> bool:
    """通过文件头判断是否为图片"""
    return (
        data.startswith(b"\xff\xd8\xff")  # JPEG
        or data.startswith(b"\x89PNG")  # PNG
        or data.startswith(b"GIF8")  # GIF
        or data.startswith(b"RIFF") and b"WEBP" in data[:12]  # WebP
    )


def _extract_og_image(page_url: str) -> str | None:
    """从网页中提取 og:image meta 标签"""
    try:
        with httpx.Client(headers=HEADERS, timeout=15, follow_redirects=True) as client:
            resp = client.get(page_url)
            if resp.status_code != 200:
                return None
            html = resp.text[:50000]  # 只看前 50KB（meta 都在 head 里）

        patterns = [
            r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
            r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']',
            r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)["\']',
        ]
        for pat in patterns:
            match = re.search(pat, html, re.IGNORECASE)
            if match:
                img_url = match.group(1)
                # 处理相对路径
                if img_url.startswith("/"):
                    parsed = urlparse(page_url)
                    img_url = f"{parsed.scheme}://{parsed.netloc}{img_url}"
                return img_url
    except Exception:
        return None
    return None


def _build_image_prompt(title: str, keywords: list[str]) -> str:
    """构造给 AI 模型的图像生成 prompt"""
    kw = "、".join(keywords[:3]) if keywords else ""
    return (
        f"新闻摄影风格，主题：{title}。关键元素：{kw}。"
        f"科技感、专业、高质量、写实、横幅构图、现代简约。"
        f"无文字、无水印。"
    )


def _generate_ai_image(prompt: str, save_path: str) -> bool:
    """调用 SiliconFlow 生成图片并下载到本地"""
    try:
        with httpx.Client(timeout=90) as client:
            resp = client.post(
                "https://api.siliconflow.cn/v1/images/generations",
                headers={"Authorization": f"Bearer {SILICONFLOW_API_KEY}"},
                json={
                    "model": SILICONFLOW_IMAGE_MODEL,
                    "prompt": prompt,
                    "image_size": "1024x576",
                },
            )
            if resp.status_code != 200:
                print(f"     SiliconFlow 错误: {resp.text[:200]}")
                return False
            data = resp.json()
            image_url = data["images"][0]["url"]
        return _download_image(image_url, save_path)
    except Exception as e:
        print(f"     AI 生成异常: {e}")
        return False


if __name__ == "__main__":
    import json
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
        print(f"为 {date_str} 抓取配图...\n")
        fetch_images(script, OUTPUT_DIR, date_str)
