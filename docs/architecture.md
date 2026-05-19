# 架构说明

## 数据流

```
RSS 5源  aiHot API  last30days(social)
   │         │           │
   └────┬────┴─────┬─────┘
        ▼          ▼
   fetcher.py  fetcher_social.py
        │          │
        └────┬─────┘
             ▼
       all_articles (list[dict])
       + aihot_data (日报 JSON)
             │
             ▼
    script_generator.py
    ┌─────────────────┐
    │ 阶段1: 筛选 Top 5 │  ← DeepSeek (SELECTION_PROMPT)
    │ 阶段1.5: 抓全文    │  ← article_enricher.py (jina → trafilatura → GET)
    │ 阶段2: 深度写稿    │  ← DeepSeek (DEEP_SCRIPT_PROMPT)
    └─────────────────┘
             │
             ▼
         script dict
    ┌──────┼──────┬──────┐
    ▼      ▼      ▼      ▼
 配图   TTS合成  HTML   飞书
(og:image (edge-tts  (报纸风  (webhook
 →AI生成) +ffmpeg)   页面)   卡片)
    │      │      │      │
    └──────┴──────┴──────┘
             ▼
      publisher.py
      (git add/commit/push)
             │
             ▼
      GitHub Pages 部署
```

## Article dict 字段

```python
{
    "title": str,        # 标题
    "summary": str,      # 摘要（前 300-500 字）
    "link": str,         # 原文 URL
    "published": str,    # ISO 8601 北京时间
    "date": str,         # YYYY-MM-DD 北京时间
    "source": str,       # 来源名
    "lang": str,         # zh / en
    "image_url": str|None,  # RSS 自带配图
    "category": str|None,   # aiHot 分类（ai-models/products/industry/paper/tip）
    "full_body": str,    # 抓取的全文（enrich_articles 填充）
    "top_comments": list[str],  # 网友评论（social 源填充）
}
```

## Script dict 结构

```python
{
    "title": "本期标题（爆款风格 15-28 字）",
    "opening": "开场白（30秒）",
    "segments": [
        {
            "news_title": "本条标题",
            "script": "完整口播稿（700-900字，无元标签）",
            "golden_quote": "金句（20字内，仅网页展示）",
            "summary": "快读摘要（250-350字）",
            "keywords": ["关键词"],
            "source": "来源名",
            "source_link": "URL"
        }
    ],
    "ending": "结尾（30秒）",
    "total_word_count": int  # 必须 ≥ 4000
}
```

## 外部依赖

| 服务 | 用途 | 费用 |
|------|------|------|
| DeepSeek API | 筛选 + 写稿 | ~¥2/期 |
| edge-tts | 语音合成 | 免费 |
| jina.ai Reader | 全文抓取 | 免费 |
| aiHot API | AI 日报 | 免费 |
| Pexels API | 免费图库搜图（配图第 3 级兜底） | 免费 |
| SiliconFlow | AI 图片（第 4 级兜底） | ~¥0.1/张 |
| GitHub Pages | 网页托管 | 免费 |
| Cloudflare Workers | 定时触发 | 免费 |
| 飞书 Webhook | 推送通知 | 免费 |

## 错误恢复策略

| 失败点 | 降级方案 |
|--------|----------|
| DeepSeek 筛选失败 | 取前 5 条兜底 |
| 全文抓取失败 | 用 RSS summary 代替 |
| jina.ai 不可用 | → trafilatura → 简单 GET |
| TTS 失败 | edge-tts 重试 → SiliconFlow 备选 |
| 飞书推送失败 | 不影响发布，静默跳过 |
| git push 被拒 | pull --rebase 后重推 |
