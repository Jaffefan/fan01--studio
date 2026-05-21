"""伊恩娱乐深度谈 — 主程序（每日午间发布）"""

import sys, json, os, shutil
from datetime import datetime, timezone, timedelta

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BJT = timezone(timedelta(hours=8))
from config import ENT_OUTPUT_DIR, ENT_TTS_VOICE, ENT_TTS_RATE, ENT_TARGET_DURATION
from fetcher_ent import fetch_entertainment
from script_generator_ent import generate_ent_script
from image_fetcher import fetch_images
from tts import generate_audio, clean_text_for_tts
from html_generator_ent import generate_ent_html
from publisher import publish


def _push_ent_feishu(script, date_str, podcast_url):
    """推送娱乐栏目到专属飞书群"""
    import httpx
    from config import ENT_FEISHU_WEBHOOK

    title = script.get("title", "")
    parts = date_str.split("-")
    display_date = f"{'-'.join(parts[:3])} 午间" if len(parts) >= 3 else date_str

    card = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {"tag": "plain_text", "content": f"🎬 {title}"},
                "template": "blue",
            },
            "elements": [
                {"tag": "div", "text": {"tag": "lark_md",
                                        "content": f"**📖 {display_date}**　　伊恩娱乐深度谈 · 每日一个故事\n\n{script.get('summary', '')[:200]}..."}},
                {"tag": "hr"},
                {"tag": "div", "text": {"tag": "lark_md",
                                        "content": f"🎧 [**收听完整故事 →**]({podcast_url})" if podcast_url else "🎧 本期已发布"}},
            ],
        },
    }

    try:
        resp = httpx.post(ENT_FEISHU_WEBHOOK, json=card, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") == 0:
            print("  ✅ 飞书娱乐群推送成功！")
        else:
            print(f"  ⚠️ 飞书返回异常: {data}")
    except Exception as e:
        print(f"  ⚠️ 娱乐群飞书推送失败: {e}")


def main():
    now = datetime.now(BJT)
    episode_id = now.strftime("%Y-%m-%d-%H%M")
    today = now.strftime("%Y-%m-%d")

    print(f"{'=' * 50}")
    print(f"  伊恩娱乐深度谈")
    print(f"  第 {episode_id} 夜")
    print(f"{'=' * 50}\n")

    # ── 1. 抓取 ──
    print("🎬 第一步：抓取娱乐资讯...\n")
    articles = fetch_entertainment()
    if not articles:
        print("未抓取到娱乐资讯，跳过。")
        return

    # ── 2. 生成脚本 ──
    print(f"\n📖 第二步：生成故事化深度稿...\n")
    script = generate_ent_script(articles)

    os.makedirs(ENT_OUTPUT_DIR, exist_ok=True)
    json_path = os.path.join(ENT_OUTPUT_DIR, f"script_ent_{episode_id}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(script, f, ensure_ascii=False, indent=2)

    title = script.get("title", "")[:50]
    print(f"  📖 {title}")

    # ── 3. 配图 ──
    print(f"\n🖼️ 第三步：抓取配图...\n")
    # Wrap into list format for fetch_images
    fake_script = {"segments": [{
        "news_title": script.get("title", ""),
        "image_url": script.get("image_url"),
        "source_link": script.get("source_link", ""),
        "keywords": script.get("keywords", []),
    }]}
    image_paths = fetch_images(fake_script, ENT_OUTPUT_DIR, episode_id)
    cover_image = image_paths.get(1)

    # ── 4. TTS ──
    print(f"\n🎙️ 第四步：语音合成...\n")
    # Override voice for entertainment (more relaxed)
    import tts as tts_mod
    orig_voice, orig_rate = tts_mod.VOICE, tts_mod.RATE
    tts_mod.VOICE = ENT_TTS_VOICE
    tts_mod.RATE = ENT_TTS_RATE

    audio_script = {
        "opening": script.get("opening", ""),
        "segments": [{"news_title": script.get("title", ""), "script": script.get("script", "")}],
        "ending": script.get("ending", "感谢收听，我们下期再见。"),
    }
    audio_files = tts_mod.generate_audio(audio_script, ENT_OUTPUT_DIR, episode_id)
    tts_mod.VOICE, tts_mod.RATE = orig_voice, orig_rate

    chapters_path = audio_files.get("chapters")
    full_mp3 = audio_files.get("full")

    # ── 5. HTML ──
    print(f"\n🌐 第五步：生成故事书页面...\n")
    site_path = generate_ent_html(script, full_mp3, cover_image, ENT_OUTPUT_DIR, episode_id)
    site_dir = os.path.dirname(site_path)
    print(f"  ✅ 本地: {site_path}")

    # ── 6. 发布 ──
    print(f"\n🚀 第六步：发布到 GitHub Pages...\n")
    # Reuse publisher but push to episodes_ent/
    podcast_url = None
    try:
        podcast_url = _publish_ent(site_dir, episode_id, script)
    except Exception as e:
        print(f"  ⚠️ 发布失败: {e}")

    # ── 7. 飞书娱乐群 ──
    print(f"\n📨 第七步：推送到飞书娱乐群...\n")
    try:
        _push_ent_feishu(script, episode_id, podcast_url)
    except Exception as e:
        print(f"  ⚠️ 飞书推送失败: {e}")

    # ── 汇总 ──
    print(f"\n{'=' * 50}")
    print(f"  完成！")
    print(f"{'=' * 50}")
    print(f"  📖 {title}")
    if podcast_url:
        print(f"  🔗 {podcast_url}")


def _publish_ent(site_dir, episode_id, script):
    """发布娱乐栏目到 episodes_ent/ 目录"""
    repo_dir = "."
    ep_dir = os.path.join(repo_dir, "episodes_ent", episode_id)
    if os.path.exists(ep_dir):
        shutil.rmtree(ep_dir)
    shutil.copytree(site_dir, ep_dir)

    # metadata
    meta = {
        "episode_id": episode_id,
        "title": script.get("title", ""),
        "published_at": _fmt_date(episode_id),
        "source": script.get("source", ""),
        "source_link": script.get("source_link", ""),
        "keywords": script.get("keywords", []),
    }
    meta_path = os.path.join(ep_dir, "episode_meta.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    # git ops
    import subprocess as sp
    paths = [f"episodes_ent/{episode_id}", ".nojekyll"]
    for p in paths:
        if os.path.exists(p):
            sp.run(["git", "add", p], capture_output=True, text=True)

    sp.run(["git", "commit", "-m", f"ent episode: {episode_id}"],
           capture_output=True, text=True)
    sp.run(["git", "pull", "--rebase", "origin", "main"],
           capture_output=True, text=True)
    result = sp.run(["git", "push", "origin", "HEAD:main"],
                    capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ⚠️ push failed: {result.stderr[:200]}")

    from config import GITHUB_PAGES_URL
    url = f"{GITHUB_PAGES_URL}/episodes_ent/{episode_id}/"
    print(f"  ✅ 发布成功: {url}")
    return url


def _fmt_date(episode_id):
    parts = episode_id.split("-")
    if len(parts) >= 4 and len(parts[3]) == 4:
        return f"{'-'.join(parts[:3])} {parts[3][:2]}:{parts[3][2:]}"
    return episode_id


if __name__ == "__main__":
    main()
