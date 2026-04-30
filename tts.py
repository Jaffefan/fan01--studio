"""TTS 语音合成模块：将口播文案转为语音文件（使用 edge-tts，免费）"""

import sys
import asyncio
import os
import re
import json
import edge_tts

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# 音色选择（伊恩 主持人 - 可爱年轻女声）：
#   zh-CN-XiaoyiNeural   女声，年轻活泼俏皮（推荐 - 伊恩 人设）
#   zh-CN-XiaoxiaoNeural 女声，自然甜美
#   zh-CN-XiaoshuangNeural 童声，更小更可爱（可能太稚嫩）
#   zh-CN-YunjianNeural  男声，激情叙述
VOICE = "zh-CN-XiaoyiNeural"

# 语速（晓伊 本身节奏轻快，正常即可）
RATE = "+5%"

# 音量
VOLUME = "+0%"


def clean_text_for_tts(text: str) -> str:
    """
    清洗文案中不适合 TTS 朗读的内容：
    - 去除 markdown 加粗/斜体标记（** * __）
    - 去除 markdown 标题标记（#）
    - 将【对比分析】【技术科普】等标签转为自然过渡语
    - 去除多余空行
    """
    # 去除 ** 加粗标记
    text = re.sub(r'\*{1,3}', '', text)
    # 去除 __ 下划线强调
    text = re.sub(r'_{1,2}', '', text)
    # 去除 markdown 标题 #
    text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)
    # 去除反引号
    text = re.sub(r'`+', '', text)

    # 将结构标签转为口播过渡语，让朗读更自然
    text = text.replace('【对比分析】', '我们来横向对比一下。')
    text = text.replace('【技术科普】', '简单科普一下背后的技术。')
    text = text.replace('【颠覆认知】', '这件事真正颠覆的是——')
    text = text.replace('【实际影响】', '对我们普通人来说，')

    # 清理多余空白行
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = text.strip()

    return text


def generate_audio(script: dict, output_dir: str, date_str: str) -> dict:
    """
    将口播文案合成为语音文件。
    分段合成（开场 + 每条资讯 + 结尾），方便剪映逐段导入。
    """
    audio_dir = os.path.join(output_dir, f"audio_{date_str}")
    os.makedirs(audio_dir, exist_ok=True)

    audio_files = {}

    # 合成开场白
    print("  🎙️ 合成开场白...")
    opening_path = os.path.join(audio_dir, "00_opening.mp3")
    asyncio.run(_synthesize(clean_text_for_tts(script["opening"]), opening_path))
    audio_files["opening"] = opening_path

    # 合成每条资讯
    for i, seg in enumerate(script["segments"], 1):
        print(f"  🎙️ 合成第{i}条：{seg['news_title']}...")
        seg_path = os.path.join(audio_dir, f"{i:02d}_segment_{i}.mp3")
        asyncio.run(_synthesize(clean_text_for_tts(seg["script"]), seg_path))
        audio_files[f"segment_{i}"] = seg_path

    # 合成结尾
    print("  🎙️ 合成结尾...")
    ending_path = os.path.join(audio_dir, "99_ending.mp3")
    asyncio.run(_synthesize(clean_text_for_tts(script["ending"]), ending_path))
    audio_files["ending"] = ending_path

    # 保存音频清单
    manifest_path = os.path.join(audio_dir, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(audio_files, f, ensure_ascii=False, indent=2)

    # 合并所有分段为一个完整文件，并生成章节时间戳
    print("  🎙️ 合并为完整音频...")
    full_path = os.path.join(audio_dir, "full.mp3")
    chapters = _merge_audio(audio_files, full_path, script)
    audio_files["full"] = full_path

    # 保存章节信息
    chapters_path = os.path.join(audio_dir, "chapters.json")
    with open(chapters_path, "w", encoding="utf-8") as f:
        json.dump(chapters, f, ensure_ascii=False, indent=2)
    audio_files["chapters"] = chapters_path

    print(f"\n  ✅ 所有音频已保存到: {audio_dir}")
    return audio_files


def _get_audio_duration(filepath: str) -> float:
    """用 ffprobe 获取音频时长（秒）"""
    import subprocess
    try:
        from config import FFMPEG_DIR
        ffprobe = os.path.join(FFMPEG_DIR, "ffprobe.exe")
    except ImportError:
        ffprobe = "ffprobe"
    result = subprocess.run(
        [ffprobe, "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", filepath],
        capture_output=True, text=True,
    )
    try:
        return float(result.stdout.strip())
    except ValueError:
        return 0.0


def _merge_audio(audio_files: dict, output_path: str, script: dict | None = None) -> list[dict]:
    """
    将所有分段音频按顺序合并为一个完整文件（使用 ffmpeg）。
    返回章节时间戳列表 [{"title", "start_seconds", "label"}, ...]
    """
    import subprocess

    try:
        from config import FFMPEG_DIR
        ffmpeg = os.path.join(FFMPEG_DIR, "ffmpeg.exe")
    except ImportError:
        ffmpeg = "ffmpeg"

    # 按顺序排列：开场 → 各段资讯 → 结尾
    order = ["opening"]
    order += [k for k in sorted(audio_files.keys()) if k.startswith("segment_")]
    order.append("ending")

    # 生成 0.8 秒静音文件用于段落间停顿
    silence_path = os.path.join(os.path.dirname(output_path), "_silence.mp3")
    subprocess.run(
        [ffmpeg, "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono",
         "-t", "0.8", "-q:a", "9", silence_path],
        capture_output=True,
    )
    silence_duration = 0.8

    # 拿每个分段的时长，计算章节起始时间
    chapters = []
    cumulative = 0.0

    segment_titles = []
    if script:
        segment_titles = [seg.get("news_title", f"第{i+1}条")
                          for i, seg in enumerate(script.get("segments", []))]

    # 创建 ffmpeg concat 文件列表（使用绝对路径，正斜杠）
    list_path = os.path.join(os.path.dirname(output_path), "_filelist.txt")
    with open(list_path, "w", encoding="utf-8") as f:
        first = True
        for idx, key in enumerate(order):
            filepath = audio_files.get(key)
            if not (filepath and os.path.exists(filepath)):
                continue
            abs_path = os.path.abspath(filepath).replace("\\", "/")
            sil_path = os.path.abspath(silence_path).replace("\\", "/")
            if not first:
                f.write(f"file '{sil_path}'\n")
                cumulative += silence_duration
            f.write(f"file '{abs_path}'\n")
            first = False

            # 记录章节
            if key == "opening":
                title = "开场"
            elif key == "ending":
                title = "结尾"
            elif key.startswith("segment_"):
                seg_idx = int(key.split("_")[1]) - 1
                title = segment_titles[seg_idx] if seg_idx < len(segment_titles) else key
            else:
                title = key
            chapters.append({
                "key": key,
                "title": title,
                "start_seconds": round(cumulative, 2),
                "label": _format_timestamp(cumulative),
            })
            cumulative += _get_audio_duration(filepath)

    # 合并
    subprocess.run(
        [ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", list_path,
         "-b:a", "192k", output_path],
        capture_output=True,
    )

    # 清理临时文件
    for tmp in [silence_path, list_path]:
        if os.path.exists(tmp):
            os.remove(tmp)

    return chapters


def _format_timestamp(seconds: float) -> str:
    """秒数转 mm:ss 格式"""
    m = int(seconds // 60)
    s = int(seconds % 60)
    return f"{m:02d}:{s:02d}"


async def _synthesize(text: str, output_path: str):
    """合成单段语音 - 根据 TTS_PROVIDER 路由到不同引擎"""
    try:
        from config import TTS_PROVIDER
    except ImportError:
        TTS_PROVIDER = "edge"

    if TTS_PROVIDER == "siliconflow":
        if _synthesize_siliconflow(text, output_path):
            return
        # SiliconFlow 失败时回退到 edge-tts
        print(f"     ⚠️ SiliconFlow 失败，回退到 edge-tts")

    communicate = edge_tts.Communicate(text, VOICE, rate=RATE, volume=VOLUME)
    await communicate.save(output_path)


def _synthesize_siliconflow(text: str, output_path: str) -> bool:
    """调用 SiliconFlow CosyVoice2 合成（更自然的音色），成功返回 True"""
    import httpx
    try:
        from config import SILICONFLOW_API_KEY, SILICONFLOW_TTS_MODEL, SILICONFLOW_TTS_VOICE
    except ImportError:
        return False

    try:
        with httpx.Client(timeout=120) as client:
            resp = client.post(
                "https://api.siliconflow.cn/v1/audio/speech",
                headers={"Authorization": f"Bearer {SILICONFLOW_API_KEY}"},
                json={
                    "model": SILICONFLOW_TTS_MODEL,
                    "input": text,
                    "voice": SILICONFLOW_TTS_VOICE,
                    "response_format": "mp3",
                },
            )
            if resp.status_code != 200:
                print(f"     SiliconFlow TTS 错误: {resp.text[:200]}")
                return False
            with open(output_path, "wb") as f:
                f.write(resp.content)
            return True
    except Exception as e:
        print(f"     SiliconFlow TTS 异常: {e}")
        return False


if __name__ == "__main__":
    import sys
    from glob import glob
    from config import OUTPUT_DIR

    files = sorted(glob(os.path.join(OUTPUT_DIR, "script_*.json")))
    if not files:
        print("未找到文案文件，请先运行 main.py")
    else:
        latest = files[-1]
        date_str = os.path.basename(latest).replace("script_", "").replace(".json", "")
        print(f"正在为 {date_str} 的文案重新生成语音...\n")
        with open(latest, "r", encoding="utf-8") as f:
            script = json.load(f)
        generate_audio(script, OUTPUT_DIR, date_str)
