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

## 定时触发（密集 cron + 双兜底）

GitHub cron 已从 2 个时间点改为密集模式：`'7,22,37,52 0,1,2 * * *'`，每 15 分钟一次覆盖北京 8:45-11:00。`_today_already_published()` 确保只第一发生效。

额外兜底：
- **Windows Task Scheduler**：`trigger_podcast.bat`，每天 9:00 本地触发（需电脑开机）
- **Google Apps Script**：`trigger_podcast.gs`，云端日定时器（需部署到 script.google.com）

## GitHub Pages

- 仓库：`Jaffefan/fan01--studio`
- 分支：`main`，根目录
- 不要在 Settings 里改 Pages 源

## 本地 ffmpeg

- Windows：`winget install Gyan.FFmpeg`，路径配置在 `config.py` `FFMPEG_DIR`
- macOS：`brew install ffmpeg`（自动在 PATH 里）
- Linux CI：`sudo apt install ffmpeg`
