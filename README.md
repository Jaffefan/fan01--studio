# 伊恩 AI 小报

每日自动生成的 AI 资讯音频播客，由 DeepSeek 写稿、edge-tts 合成语音，发布到 GitHub Pages。

**[全部期刊 →](https://jaffefan.github.io/fan01--studio/)**

## 怎么工作

1. 每日 9:00（北京时间）从 RSS（机器之心、量子位、HN、TechCrunch、The Verge）+ aiHot + Reddit/HN 抓取 AI 资讯
2. DeepSeek 筛选 5 条最重磅的，逐条写 700-900 字深度口播稿（含原文细节、网友评论、主播洞察）
3. edge-tts（晓伊音色）合成语音，ffmpeg 合并为完整 mp3 + 章节时间戳
4. 生成报纸风网页，发布到 GitHub Pages
5. 飞书群推送通知

## 本地运行

```bash
# 安装依赖
pip install -r requirements.txt

# 安装 ffmpeg（Windows 请在 config.py 配置 FFMPEG_DIR 路径）
# macOS: brew install ffmpeg
# Linux: sudo apt install ffmpeg

# 运行
python main.py
```

输出在 `output/` 目录：文案 JSON、分段时间戳、分段 mp3、合并完整音频、配图、网页。

## 环境变量

| 变量 | 必填 | 说明 |
|------|------|------|
| `DEEPSEEK_API_KEY` | 是 | DeepSeek API key |
| `SILICONFLOW_API_KEY` | 否 | AI 图片生成 |
| `FEISHU_WEBHOOK` | 否 | 飞书推送 webhook |
| `TTS_PROVIDER` | 否 | `edge`（默认）或 `siliconflow` |

本地开发时可直接修改 `config.py` 里的默认值。CI 上通过 GitHub Secrets 注入。

## 项目结构

```
main.py              # 主流程
fetcher.py           # RSS + aiHot 抓取
fetcher_social.py    # Reddit/HN/GitHub 抓取
script_generator.py  # DeepSeek 二阶段生成
article_enricher.py  # 全文抓取（jina.ai → trafilatura → GET）
tts.py               # TTS 语音合成 + ffmpeg 合并
html_generator.py    # 单期页面
archive_generator.py # 全部期刊首页
image_fetcher.py     # 配图
publisher.py         # Git 发布
feishu.py            # 飞书推送
config.py            # 配置
cloudflare-worker.js # Cloudflare Workers 定时触发器
```

## 技术栈

Python 3.12 · DeepSeek API · edge-tts · ffmpeg · GitHub Actions · GitHub Pages · Cloudflare Workers

## 链接

- 归档首页：https://jaffefan.github.io/fan01--studio/
- 手动触发：https://github.com/Jaffefan/fan01--studio/actions/workflows/daily.yml
