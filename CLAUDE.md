# 伊恩 AI 小报 — 项目约定

## 项目概览

每日自动 AI 资讯播客生成器。从 RSS + aiHot + 社交平台抓取 AI 资讯，DeepSeek 生成口播稿，edge-tts 合成语音，发布到 GitHub Pages + 飞书推送。

- 节目名：伊恩 AI 小报
- 主持人：伊恩（IP 形象：AstraX 黄色小星星）
- 发布时间：每日北京时间 9:00（UTC 1:00）
- 目标时长：15 分钟（5 条 × 700-900 字 + 开场结尾）

## 关键文件

| 文件 | 角色 |
|------|------|
| `main.py` | 主流程编排，北京时间时区 `BJT = timezone(timedelta(hours=8))` |
| `fetcher.py` | RSS + aiHot Daily API 抓取，返回 `(articles, aihot_data)` |
| `fetcher_social.py` | Reddit/HN/GitHub 抓取（用 last30days skill） |
| `script_generator.py` | 二阶段 DeepSeek：筛选 Top 5 → 深度写稿 |
| `article_enricher.py` | 三级兜底抓全文：jina.ai → trafilatura → 简单 GET |
| `tts.py` | edge-tts 语音合成 + ffmpeg 合并，清洗元标签 |
| `html_generator.py` | 报纸风单期页面（纯白 #fdfcf8，衬线体） |
| `archive_generator.py` | 全部期刊首页（双列网格，5 色交替卡片） |
| `image_fetcher.py` | 配图：原文 og:image 优先 → AI 生成兜底 |
| `publisher.py` | git add → commit → pull --rebase → push origin main |
| `feishu.py` | 飞书机器人富文本卡片推送 |
| `config.py` | 所有配置（RSS 源、API key、路径） |

## 硬规则（违反必出事）

- **时间**：所有 timestamp 必须北京时间（UTC+8）。期号 `datetime.now(BJT).strftime("%Y-%m-%d-%H%M")`
- **日期过滤**：RSS 文章的 `date_str` 必须用 `_to_beijing_date()` 转北京时间再取日期，否则凌晨文章被误杀
- **JSON 安全**：DeepSeek 长文本输出必须经 `_parse_json_response()`，内部有 `json_repair` 兜底。Prompt 里禁止英文双引号 `"`，强制用 `「」`
- **git push 前必须 pull --rebase**：避免并发 workflow 冲突
- **`fetch_all()` 返回 tuple**：`(articles, aihot_data)`，不要只解构一个
- **TTS 文本清洗**：`clean_text_for_tts()` 会过滤 "金句"、"总结一下" 等元标签——prompt 生成时已经在源头禁止，但 TTS 层也做兜底

## 环境变量（CI 用 Secrets，本地用 config.py 默认值）

| 变量 | 用途 |
|------|------|
| `DEEPSEEK_API_KEY` | DeepSeek API |
| `SILICONFLOW_API_KEY` | AI 图片生成 + CosyVoice2 TTS |
| `FEISHU_WEBHOOK` | 飞书群机器人 webhook |
| `TTS_PROVIDER` | `edge`（默认）或 `siliconflow` |
| `GITHUB_ACTIONS` | CI 检测（`true` 时 FFMPEG 走 PATH） |

## 已知陷阱

- **GitHub cron 延迟**：schedule 事件经常拖 2-4 小时，Cloudflare Worker（`cloudflare-worker.js`）可精准触发
- **aiHot 日报可能为空**：每日 08:00 北京生成，08:30 可能还没好，空响应已处理
- **机器之心/量子位 RSS 偶尔空**：网站可能改版或反爬，观察频率
- **edge-tts 音色稳定性**：免费但偶有波动，SiliconFlow CosyVoice2 是备选（需充值）
- **DeepSeek JSON 偶尔破损**：长文本含未转义字符，`json_repair` 兜底 + prompt 禁止英文双引号

## 本地运行

```bash
pip install -r requirements.txt
python main.py
# 输出在 output/ 目录下
```

## 深入文档

项目架构和数据流详见 `docs/architecture.md`，部署和 CI 配置详见 `docs/setup.md`。
