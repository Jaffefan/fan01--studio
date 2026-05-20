"""每日 AI 资讯播客生成器 - 主程序"""

import sys
import json
import os
from datetime import datetime, timezone, timedelta

# 北京时间
BJT = timezone(timedelta(hours=8))

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from config import OUTPUT_DIR
from fetcher import fetch_all
from script_generator import generate_script
from image_fetcher import fetch_images
from tts import generate_audio
from html_generator import generate_html
from publisher import publish
from feishu import push_to_feishu
from wechat_push import push_to_wechat


def _today_already_published(today: str) -> bool:
    """检查 episodes/ 下是否已有今天的播客"""
    episodes_dir = os.path.join(".", "episodes")
    if not os.path.isdir(episodes_dir):
        return False
    for name in os.listdir(episodes_dir):
        if name.startswith(today) and os.path.isdir(os.path.join(episodes_dir, name)):
            return True
    return False


def main():
    # 期号 = 唯一 ID，北京时间，含时分钟
    now = datetime.now(BJT)
    episode_id = now.strftime("%Y-%m-%d-%H%M")
    today = now.strftime("%Y-%m-%d")
    print(f"{'='*50}")
    print(f"  每日 AI 资讯播客生成器")
    print(f"  期号: {episode_id}")
    print(f"{'='*50}\n")

    # 防重复：如果今天已有发布，跳过（为兜底 cron 提供安全的幂等性）
    if _today_already_published(today):
        print(f"✅ {today} 已有播客发布，跳过。")
        return

    # ========== 1. 抓取资讯 ==========
    print("📡 第一步：抓取 AI 资讯...\n")
    articles, aihot_data = fetch_all()
    if not articles:
        print("未抓取到任何资讯，请检查网络连接或 RSS 源配置。")
        return

    # ========== 2. AI 生成深度口播 ==========
    print(f"\n🤖 第二步：生成深度口播文案...\n")
    script = generate_script(articles)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    json_path = os.path.join(OUTPUT_DIR, f"script_{episode_id}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(script, f, ensure_ascii=False, indent=2)

    txt_path = os.path.join(OUTPUT_DIR, f"script_{episode_id}.txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(f"# {script.get('title', '每日AI资讯')}\n")
        f.write(f"# 日期: {episode_id}\n\n")
        f.write(f"【开场】\n{script['opening']}\n\n")
        for i, seg in enumerate(script["segments"], 1):
            f.write(f"【第{i}条 - {seg['news_title']}】\n")
            f.write(f"{seg['script']}\n")
            f.write(f"（关键词: {', '.join(seg['keywords'])}）\n")
            f.write(f"（来源: {seg['source']}）\n\n")
        f.write(f"【结尾】\n{script['ending']}\n")

    print(f"  标题: {script.get('title', '')}")
    for i, seg in enumerate(script["segments"], 1):
        print(f"  第{i}条: {seg['news_title']}")

    # ========== 3. 抓配图（原图优先，AI 兜底） ==========
    print(f"\n🖼️ 第三步：抓取/生成配图...\n")
    image_paths = fetch_images(script, OUTPUT_DIR, episode_id)

    # ========== 4. TTS 语音合成 + 章节时间戳 ==========
    print(f"\n🎙️ 第四步：TTS 语音合成...\n")
    audio_files = generate_audio(script, OUTPUT_DIR, episode_id)

    # 加载章节信息
    chapters_path = audio_files.get("chapters")
    chapters = []
    if chapters_path and os.path.exists(chapters_path):
        with open(chapters_path, "r", encoding="utf-8") as f:
            chapters = json.load(f)

    # ========== 5. 生成网页 ==========
    print(f"\n🌐 第五步：生成播客网页...\n")
    full_mp3 = audio_files["full"]
    site_path = generate_html(script, chapters, image_paths, full_mp3, OUTPUT_DIR, episode_id)
    site_dir = os.path.dirname(site_path)
    print(f"  ✅ 本地预览: {site_path}")

    # ========== 6. 发布到 GitHub Pages ==========
    print(f"\n🚀 第六步：发布到 GitHub Pages...\n")
    podcast_url = None
    try:
        podcast_url = publish(site_dir, episode_id, script=script, chapters=chapters)
    except Exception as e:
        print(f"  ⚠️ 发布失败（跳过）: {e}")

    # ========== 7. 推送飞书 ==========
    print(f"\n📨 第七步：推送到飞书...\n")
    try:
        push_to_feishu(script, episode_id, podcast_url=podcast_url)
    except Exception as e:
        print(f"  ⚠️ 飞书推送失败（不影响发布）: {e}")

    # ========== 8. 推送微信 ==========
    print(f"\n💬 第八步：推送到微信...\n")
    try:
        push_to_wechat(script, episode_id, podcast_url=podcast_url)
    except Exception as e:
        print(f"  ⚠️ 微信推送失败（不影响发布）: {e}")

    # ========== 完成汇总 ==========
    print(f"\n{'='*50}")
    print(f"  完成！")
    print(f"{'='*50}")
    print(f"  📄 文案: {txt_path}")
    print(f"  🌐 网页: {site_path}")
    if podcast_url:
        print(f"  🔗 在线: {podcast_url}")


if __name__ == "__main__":
    main()
