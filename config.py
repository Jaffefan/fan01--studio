"""项目配置：本地与 GitHub Actions 共用，敏感 key 优先从环境变量读取"""

import os

# AI 资讯 RSS 源配置
RSS_FEEDS = [
    {
        "name": "机器之心",
        "url": "https://www.jiqizhixin.com/rss",
        "lang": "zh",
    },
    {
        "name": "量子位",
        "url": "https://www.qbitai.com/feed",
        "lang": "zh",
    },
    {
        "name": "Hacker News - AI",
        "url": "https://hnrss.org/newest?q=AI+OR+LLM+OR+GPT+OR+Claude+OR+artificial+intelligence",
        "lang": "en",
    },
    {
        "name": "TechCrunch AI",
        "url": "https://techcrunch.com/category/artificial-intelligence/feed/",
        "lang": "en",
    },
    {
        "name": "The Verge AI",
        "url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
        "lang": "en",
    },
]

# 每个源最多抓取的文章数
MAX_ARTICLES_PER_FEED = 10

# 最终筛选出的资讯条数（只取当天 Top5）
TOP_NEWS_COUNT = 5

# 口播视频目标时长（秒），10 分钟
TARGET_DURATION_SECONDS = 600

# 输出目录
OUTPUT_DIR = "output"


# ============== 敏感配置：优先环境变量，本地 fallback ==============
# DeepSeek API
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "sk-ebe09535551545589945f3a9db554159")
DEEPSEEK_BASE_URL = "https://api.deepseek.com"

# SiliconFlow API
SILICONFLOW_API_KEY = os.environ.get(
    "SILICONFLOW_API_KEY",
    "sk-usvrsaipyzmpmcrmbwektpmroazprwckaywhpbdrkabnmpcm"
)
SILICONFLOW_IMAGE_MODEL = "Kwai-Kolors/Kolors"

# TTS 引擎选择
TTS_PROVIDER = os.environ.get("TTS_PROVIDER", "edge")
SILICONFLOW_TTS_MODEL = "FunAudioLLM/CosyVoice2-0.5B"
SILICONFLOW_TTS_VOICE = "FunAudioLLM/CosyVoice2-0.5B:diana"

# Pexels API（备用）
PEXELS_API_KEY = os.environ.get(
    "PEXELS_API_KEY",
    "aG8pDuxHeTblKGcl5b2MH0TU7zvHHVshwu0AYENpg2ophskn8ce0DfHs"
)

# 飞书机器人 webhook
FEISHU_WEBHOOK = os.environ.get(
    "FEISHU_WEBHOOK",
    "https://open.feishu.cn/open-apis/bot/v2/hook/df9a7177-66c0-459a-968c-a21517a6330b"
)


# ============== 运行环境判断 ==============
# 是在 GitHub Actions 还是本地
IS_CI = os.environ.get("GITHUB_ACTIONS") == "true"

# ffmpeg 路径（CI 上通过 apt 装的可以直接用 'ffmpeg'）
if IS_CI:
    FFMPEG_DIR = ""  # 直接调用 ffmpeg/ffprobe（在 PATH 里）
else:
    FFMPEG_DIR = r"C:\Users\LTSZ\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1-full_build\bin"


# ============== GitHub Pages 发布配置 ==============
GITHUB_USERNAME = "Jaffefan"
GITHUB_REPO = "fan01--studio"
GITHUB_PAGES_URL = f"https://{GITHUB_USERNAME.lower()}.github.io/{GITHUB_REPO}"
# CI 上代码就在仓库里，不需要 clone；本地保留兼容路径
LOCAL_REPO_DIR = "." if IS_CI else "podcast_site"
