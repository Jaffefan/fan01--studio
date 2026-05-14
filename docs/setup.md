# 部署与 CI 配置

## GitHub Actions（定时 + 手动触发）

Workflow: `.github/workflows/daily.yml`

- **触发**：schedule（UTC 0:30）+ workflow_dispatch（手动）
- **权限**：`contents: write`（允许 push 回 main 分支）
- **超时**：25 分钟
- **步骤**：checkout → Python 3.12 → ffmpeg → pip install → git config → `python main.py`

### Secrets（GitHub Settings → Secrets → Actions）

```
DEEPSEEK_API_KEY    # 必填
SILICONFLOW_API_KEY # 可选
FEISHU_WEBHOOK      # 可选
TTS_PROVIDER        # edge（默认），改 siliconflow 用付费音色
```

## Cloudflare Workers（精准 9:00 触发）

GitHub 自带 cron 经常延迟 2-4 小时。Cloudflare Worker 可以 ±1 分钟精度。

文件：`cloudflare-worker.js`

部署步骤：
1. dash.cloudflare.com → Workers & Pages → Create Worker
2. 粘贴 `cloudflare-worker.js` 内容 → Deploy
3. Settings → Variables → 添加 Secret `GITHUB_TOKEN`（GitHub Personal Access Token，workflow 权限）
4. Settings → Triggers → Cron: `0 1 * * *`（UTC 1:00 = 北京 9:00）

## GitHub Pages

- 仓库：`Jaffefan/fan01--studio`
- 分支：`main`，根目录
- 不要在 Settings 里改 Pages 源

## 本地 ffmpeg

- Windows：`winget install Gyan.FFmpeg`，路径配置在 `config.py` `FFMPEG_DIR`
- macOS：`brew install ffmpeg`（自动在 PATH 里）
- Linux CI：`sudo apt install ffmpeg`
